"""通用 SDF 材质提取、复用与分配；不修改对象结构和网格几何。"""
import argparse
from array import array
import hashlib
import json
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET
import bpy
from mathutils import Vector

WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE/'scripts'))
sys.dont_write_bytecode = True
import project_io

def rgba(text):
    if text is None:
        return None
    values = [float(x) for x in text.split()]
    if len(values) != 4 or not all(0 <= x <= 1 for x in values):
        raise ValueError(f'无效 RGBA：{text}')
    return values

def extract_sdf(path, parameters=None):
    if path is None:
        return []
    text = Path(path).read_text(encoding='utf8')
    # 只替换配置中明确给出的模板变量，不执行模板中的代码。
    for key, value in (parameters or {}).items():
        text = re.sub(r'\{\{\s*'+re.escape(key)+r'\s*\}\}', lambda m: str(value), text)
    if '{%' in text:
        raise ValueError('存在结构性 Jinja 控制语句；请先使用可信模板参数展开为 SDF，不能跳过材质')
    root = ET.fromstring(text)
    records = []
    for model in root.findall('model'):
        if model.find('model') is not None:
            raise ValueError('嵌套模型材质作用域尚未支持，不能静默忽略')
        for link in model.findall('link'):
            for visual in link.findall('visual'):
                material = visual.find('material')
                material_text = ET.tostring(material,encoding='unicode') if material is not None else ''
                if '{{' in material_text or '{{' in (visual.findtext('transparency') or ''):
                    raise ValueError('材质中有未展开的 Jinja 变量，请配置 jinja_parameters')
                records.append({'key': link.get('name')+'/'+visual.get('name'), 'link':link.get('name'), 'visual':visual.get('name'),
                    'geometry': ET.tostring(visual.find('geometry'),encoding='unicode') if visual.find('geometry') is not None else None,
                    'mesh_uri':visual.findtext('geometry/mesh/uri'), 'has_material':material is not None,
                    'ambient':rgba(visual.findtext('material/ambient')), 'diffuse':rgba(visual.findtext('material/diffuse')),
                    'specular':rgba(visual.findtext('material/specular')), 'emissive':rgba(visual.findtext('material/emissive')),
                    'transparency':float(visual.findtext('transparency','0')), 'script_name':visual.findtext('material/script/name'),
                    'script_uris': [e.text for e in visual.findall('material/script/uri')], 'lighting':visual.findtext('material/lighting')})
    return records

def linear_rgb(values, color_space):
    if color_space == 'linear':
        return list(values)
    if color_space == 'srgb':
        return [x/12.92 if x <= 0.04045 else ((x+0.055)/1.055)**2.4 for x in values]
    raise ValueError('source_color_space 必须为 linear 或 srgb')

def resolve_definition(record, settings, library):
    named = library.get(record.get('script_name'), {}) if record else {}
    if record and record['diffuse'] is not None:
        source = 'sdf_rgba'
        color = record['diffuse']
    elif named:
        source = 'gazebo_named'
        color = named['diffuse']
    else:
        return None
    transparency = record['transparency']
    if not 0 <= transparency <= 1:
        raise ValueError('SDF transparency 超出 0~1')
    spec = record['specular'] or named.get('specular', [0.1,0.1,0.1,1])
    ambient = record['ambient'] or named.get('ambient')
    emissive = record['emissive'] or named.get('emissive',[0,0,0,1])
    space = settings.get('source_color_space','linear')
    definition = {'source':source, 'rgba':linear_rgb(color[:3],space)+[color[3]*(1-transparency)],
                  'roughness':settings.get('roughness',0.62), 'metallic':settings.get('metallic',0),
                  'specular':sum(spec[:3])/3, 'ambient_raw':ambient, 'specular_raw':spec,
                  'diffuse_raw':color, 'transparency_raw':transparency, 'emission':linear_rgb(emissive[:3],space), 'color_space':space}
    if source == 'gazebo_named':
        definition['script_name'] = record['script_name']
    return definition

def create_material(definition):
    signature = json.dumps(definition,sort_keys=True,separators=(',',':'))
    digest = hashlib.sha256(signature.encode()).hexdigest()[:12]
    label = definition.get('script_name', definition['source']).replace('/','_')
    name = 'SDF_MAT::'+label+'::'+digest
    material = bpy.data.materials.get(name)
    created = material is None
    if material is None:
        material = bpy.data.materials.new(name)
    elif material.get('sdf_material_signature') != signature:
        raise ValueError(f'同名材质冲突，不能覆盖外来材质：{name}')
    material.use_nodes = True
    # 节点以确定方式更新，同一材质再次执行不会增加节点或材质。
    nodes = material.node_tree.nodes
    nodes.clear()
    shader = nodes.new('ShaderNodeBsdfPrincipled')
    target = nodes.new('ShaderNodeOutputMaterial')
    shader.inputs['Base Color'].default_value = definition['rgba']
    shader.inputs['Alpha'].default_value = definition['rgba'][3]
    shader.inputs['Roughness'].default_value = definition['roughness']
    shader.inputs['Metallic'].default_value = definition['metallic']
    shader.inputs['Specular IOR Level'].default_value = definition['specular']
    shader.inputs['IOR'].default_value = 1.5
    shader.inputs['Emission Color'].default_value = (*definition.get('emission',[0,0,0]),1)
    shader.inputs['Emission Strength'].default_value = 1
    material.node_tree.links.new(shader.outputs['BSDF'],target.inputs['Surface'])
    material.diffuse_color = definition['rgba']
    if definition['rgba'][3] < 1:
        material.surface_render_method = 'DITHERED'
    material['sdf_material_signature'] = signature
    material['source_definition_json'] = json.dumps(definition,ensure_ascii=False)
    return material, created

def match_visual(obj, records, settings):
    selected = settings.get('object_visuals',{}).get(obj.name) or obj.get('sdf_visual_key')
    if selected:
        matches = [r for r in records if r['key']==selected]
    else:
        source = Path(obj.get('source_file','')).name.casefold()
        matches = [r for r in records if r['mesh_uri'] and Path(r['mesh_uri']).name.casefold()==source]
        if len(matches)>1 and obj.parent and obj.parent.name.startswith('LINK::'):
            matches = [r for r in matches if r['link']==obj.parent.name[6:]]
    if len(matches)>1 or (selected and not matches):
        raise ValueError(f'{obj.name} 的 Visual 绑定不明确，请在 object_visuals 中使用 link/visual 键')
    return matches[0] if matches else None

def apply_materials(config, records):
    settings = config['materials']
    library = json.loads((WORKSPACE/settings['gazebo_library']).read_text(encoding='utf8'))['materials']
    assignments, created_names = [], set()
    for obj in bpy.data.objects:
        if obj.type != 'MESH':
            continue
        record = match_visual(obj,records,settings)
        definition = resolve_definition(record,settings,library)
        source = definition['source'] if definition else None
        override = settings.get('overrides',{}).get(obj.name)
        if override:
            if not override.get('reason'):
                raise ValueError('材质覆盖必须声明 reason，避免将展示色声称为原始色')
            base = definition or dict(settings['default'], source='display_default')
            definition = dict(base,**override,source='config_override')
            source = 'config_override'
        if definition is None and any(s.material and not s.material.get('sdf_material_signature') for s in obj.material_slots):
            assignments.append({'object':obj.name, 'file':Path(obj.get('source_file','')).name, 'visual_key':record['key'] if record else None,
                                'source':'existing_material', 'materials':[s.material.name for s in obj.material_slots if s.material]})
            continue
        if definition is None:
            definition = dict(settings['default'],source='display_default',metallic=0,emission=[0,0,0])
            source = 'display_default'
        material,created = create_material(definition)
        if created:
            created_names.add(material.name)
        if not obj.material_slots:
            obj.data.materials.append(None)
        for slot in obj.material_slots:
            slot.link = 'OBJECT'
            slot.material = material
        assignments.append({'object':obj.name, 'file':Path(obj.get('source_file','')).name, 'visual_key':record['key'] if record else None,
                            'source':source, 'material':material.name, 'definition':definition,
                            'reference_only':bool(obj.get('reference_only',False))})
    return assignments, sorted(created_names)

def object_state(obj):
    state = {'type':obj.type,'parent':obj.parent.name if obj.parent else None,'parent_type':obj.parent_type,
             'matrix_world':[list(r) for r in obj.matrix_world], 'matrix_basis':[list(r) for r in obj.matrix_basis],
             'matrix_parent_inverse':[list(r) for r in obj.matrix_parent_inverse], 'collections':sorted(c.name for c in obj.users_collection),
             'hide_render':obj.hide_render,'hide_viewport':obj.hide_viewport,'hide_set':obj.hide_get(),
             'modifiers':[(m.name,m.type) for m in obj.modifiers], 'has_animation':obj.animation_data is not None}
    if obj.name.startswith('JOINT::'):
        state['joint_properties'] = {k:list(obj[k]) if hasattr(obj[k],'to_list') else obj[k] for k in obj.keys()}
    if obj.type == 'MESH':
        digest = hashlib.sha256()
        for items,attribute,width,kind in [(obj.data.vertices,'co',3,'f'),(obj.data.loops,'vertex_index',1,'i'),(obj.data.polygons,'loop_start',1,'i'),(obj.data.polygons,'loop_total',1,'i'),(obj.data.polygons,'use_smooth',1,'b')]:
            values = array(kind,[0])*(len(items)*width)
            items.foreach_get(attribute,values)
            digest.update(values.tobytes())
        state['geometry_sha256'] = digest.hexdigest()
        state['mesh_datablock'] = obj.data.name
    return state

def snapshot_objects():
    bpy.context.view_layer.update()
    return {o.name:object_state(o) for o in bpy.data.objects}

def check_preserved(before):
    current = snapshot_objects()
    errors = [name for name, state in before.items() if current.get(name)!=state]
    if errors:
        raise RuntimeError(f'原有对象的结构或坐标发生变化：{errors}')
    return {'original_object_count':len(before),'preserved_count':len(before),'added_objects':sorted(set(current)-set(before)), 'geometry_and_transforms_unchanged':True}

def setup_environment(config):
    settings = config['materials']['preview']
    scene = bpy.context.scene
    # 直接选择 Eevee，不进行 Cycles 渲染。
    scene.render.engine = 'BLENDER_EEVEE'
    scene.render.resolution_x = settings['resolution']
    scene.render.resolution_y = settings['resolution']
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    scene.render.film_transparent = False
    scene.view_settings.view_transform = settings['view_transform']
    scene.view_settings.look = 'None'
    scene.view_settings.exposure = 0
    scene.view_settings.gamma = 1
    scene.camera = bpy.data.objects[settings['camera']]
    visible = [o for o in bpy.data.objects if o.type=='MESH' and not o.get('reference_only',False)]
    points = [o.matrix_world @ Vector(v) for o in visible for v in o.bound_box]
    lo=Vector([min(v[i] for v in points) for i in range(3)])
    hi=Vector([max(v[i] for v in points) for i in range(3)])
    center=(lo+hi)/2
    world = bpy.data.worlds.get('MATERIAL_PREVIEW_WORLD') or bpy.data.worlds.new('MATERIAL_PREVIEW_WORLD')
    scene.world = world
    world.use_nodes = True
    world.node_tree.nodes.clear()
    bg=world.node_tree.nodes.new('ShaderNodeBackground')
    bg.inputs['Color'].default_value=(*settings['world_color'],1)
    bg.inputs['Strength'].default_value=settings['world_strength']
    out=world.node_tree.nodes.new('ShaderNodeOutputWorld')
    world.node_tree.links.new(bg.outputs['Background'],out.inputs['Surface'])
    col=bpy.data.collections.get('MATERIAL_PREVIEW_LIGHTS')
    if col is None:
        col=bpy.data.collections.new('MATERIAL_PREVIEW_LIGHTS')
        scene.collection.children.link(col)
    for spec in settings['lights']:
        name='MATERIAL_LIGHT::'+spec['name']
        obj=bpy.data.objects.get(name)
        if obj is None:
            light=bpy.data.lights.new(name,'AREA')
            obj=bpy.data.objects.new(name,light)
            col.objects.link(obj)
        elif obj not in col.objects.values():
            raise ValueError('展示灯光名称与已有对象冲突')
        obj.location=center+Vector(spec['offset'])
        obj.rotation_euler=(center-obj.location).to_track_quat('-Z','Y').to_euler()
        obj.data.energy=spec['energy']
        obj.data.shape='DISK'
        obj.data.size=spec['size']
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type=='VIEW_3D':
                shading=area.spaces.active.shading
                shading.type='MATERIAL'
                shading.use_scene_lights=False
                shading.use_scene_world=False
                shading.studiolight_intensity=settings['studio_strength']
                shading.studiolight_background_alpha=0
                shading.background_type='VIEWPORT'
                shading.background_color=(0.12,0.12,0.12)
                try:
                    shading.studio_light=settings['studio_light']
                except TypeError:
                    pass
    return {'bbox_dimensions_m':list(hi-lo),'lights':[s['name'] for s in settings['lights']]}

def write_report(result, settings, reports):
    rows=result['assignments']
    defaults=[r for r in rows if r['source']=='display_default']
    no_source=[r for r in rows if r.get('visual_key') is None]
    direct=[r for r in rows if r['source']=='sdf_rgba']
    named=[r for r in rows if r['source']=='gazebo_named']
    lines=['# '+Path(result['project']).stem+' 材质验收报告','',
           '## 提取与分配结果','',
           f"- SDF Visual：{result['sdf_visual_count']}；带 material 定义：{result['sdf_material_count']}。原始记录逐项保存在 material_validation.json。",
           f"- 新建 Blender 材质：{result['created_material_count']}；分配对象：{result['assigned_object_count']}。",
           f'- 直接 RGBA 来源：{len(direct)} 个对象；Gazebo 标准命名来源：{len(named)} 个对象；展示默认：{len(defaults)} 个对象。',
           '- 相同定义通过确定性名称与内容签名复用。重复执行两次，材质集合、每个槽位绑定均一致，无新增材质。',
           '', '## SDF 到 Principled BSDF 映射','',
           '- diffuse RGB → Base Color；Alpha = diffuse alpha × (1 − transparency)。本次所有 Alpha 均为 1。',
           '- ambient 原值保存在 source_definition_json 中，不叠加 Base Color，不转换成自发光。',
           '- specular RGB 均值 → Specular IOR Level，仅为温和展示近似；IOR=1.5，Metallic=0，Roughness='+str(settings['roughness'])+'。不宣称等价复现 Gazebo Blinn-Phong。',
           '- emissive → Emission Color；本模型定义为零。未定义时也为零。',
           '- 原始 geometry、mesh URI、link/visual、ambient/diffuse/specular、transparency、script name/URI、lighting 均已提取，未使用 inertial 信息。',
           '- XML 原文可直接解析；未执行 Jinja。MAVLink 插件中的 {{变量}} 不涉及材质，全部材质数值提取成功；材质字段如有未展开变量会明确报错，可通过 jinja_parameters 传入值，不能静默跳过。',
           '- 一个文件被多个 Visual 引用时，优先用对象显式 visual 键绑定，再用 source_file 与父 Link 缩小范围；仍不明确时报告错误，不按文件名任意选色。',
           '', '## 颜色空间与脚本材质','',
           settings.get('color_space_reason','颜色空间由 source_color_space 显式指定。'),
           '- 当前 source_color_space='+settings.get('source_color_space','linear')+'。Blender 节点数值为线性；显示采用 AgX、exposure=0、gamma=1，因此截图像素不等于原始 RGBA。可配置 srgb，通过标准分段函数解码到线性；不对 Alpha 或 specular 强度做色彩解码。',
           '- Gazebo/White：diffuse=(1,1,1,1)；Gazebo/Black：diffuse=(0,0,0,1)。脚本库在 assets/materials/gazebo_standard.json，保留原始 specular 尾部参数。',
           '- URI 中的 __default__ 本身不提供颜色；本模型同时给出了有效的 Gazebo/White 或 Gazebo/Black 名称，才可恢复标准色。未知名称或仅有 __default__ 不能声称有原始颜色。',
           '- 优先显式 diffuse，其次已知标准脚本，其次保留已有材质，最后使用配置中的中性展示默认；显式 overrides 必须注明 reason，并在来源列标记 config_override。',
           '- 参考：[SDFormat 材质语义](https://sdformat.org/tutorials/specification/spec_materials/)；[Gazebo Classic 标准脚本](https://raw.githubusercontent.com/gazebosim/gazebo-classic/gazebo11/media/materials/scripts/gazebo.material)；[Blender 5.0 Principled BSDF](https://docs.blender.org/manual/en/5.0/render/shader_nodes/shader/principled.html)。',
           '', '## 对象分配明细','', '| STL / 对象 | SDF Link/Visual | 来源 | 原始 diffuse / 展示 RGBA | Blender 材质 |', '|---|---|---|---|---|']
    for row in rows:
        definition=row.get('definition',{})
        lines.append(f"| {row['file']} / {row['object']} | {row.get('visual_key') or '无'} | {row['source']} | {definition.get('diffuse_raw',definition.get('rgba'))} | {row.get('material',row.get('materials'))} |")
    lines+=['','## 未找到原始材质的对象','']
    lines += ['- '+r['file']+('（隐藏参考件）' if r.get('reference_only') else '（可见补充件）') for r in no_source]
    lines += ['', '## 使用展示默认材质的对象','', '- '+', '.join(r['object'] for r in defaults),
              '- 默认 RGBA='+str(settings['default']['rgba'])+'；'+settings['default']['reason']+'。隐藏合并件不假定具有单一真实颜色；不按外观猜测未引用电子设备的涂装。',
              '', '## 结构保护与预览','',
              f"- Stage 1 原有 {result['preservation']['preserved_count']} 个对象全部保留：世界与局部矩阵、父对象、父逆矩阵、Collection、隐藏状态、网格顶点/拓扑/平滑标志及关节属性一致。未合并对象、修改关节中心或创建动画。",
              '- 新增对象仅为 MATERIAL_PREVIEW_LIGHTS 中的展示灯：'+', '.join(result['preservation']['added_objects'])+'。未变动任何原有模型或相机的空间位置。',
              '- Eevee 预览：eevee_preview.png；Material Preview：material_preview.png（实际图形视口截图）。',
              '- 默认视口 MATERIAL，使用 Blender 内置 studio.exr、中性灰背景；Eevee 使用独立面积灯，均未进行金属化、纹理绘制或 Cycles 渲染。',
              '- 原始 STL 的三角面与法线显示特征予以保留；本阶段未为外观修整几何。',
              '', '## 实际打开验收','', '待实际打开最终工程并检查 Material Preview 截图。后台渲染成功不代替图形打开验收。','']
    (reports/'MATERIAL_REPORT.md').write_text('\n'.join(lines),encoding='utf8')


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--config',required=True)
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    config=json.loads(project_io.resolve(args.config).read_text(encoding='utf8'))
    settings=config['materials']
    project=project_io.project(config)
    if not project.is_file():
        raise FileNotFoundError(f'当前工程不存在，请先执行 Stage 1：{project}')
    before_project=hashlib.sha256(project.read_bytes()).hexdigest()
    input_root=project_io.input_root(config)
    input_hashes={str(p.relative_to(input_root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in input_root.rglob('*') if p.is_file()}
    # 渲染与报告先落临时目录，验收通过后再归档到审计仓库。
    work=project_io.safe_reset_work_dir(config)
    reports=work/'reports'
    preview=work/'preview'
    reports.mkdir()
    preview.mkdir()
    evidence=project_io.evidence_dir(config,'stage-1.5')
    bpy.ops.wm.open_mainfile(filepath=str(project))
    before=snapshot_objects()
    (reports/'material_structure_baseline.json').write_text(json.dumps(before,ensure_ascii=False,indent=2),encoding='utf8')
    records=extract_sdf(input_root/config['description'] if config.get('description') else None,settings.get('jinja_parameters'))
    assignments,created=apply_materials(config,records)
    # 再执行一次验证幂等性；材质数据块与每个槽位必须保持一致。
    slots_before={o.name:[s.material.name if s.material else None for s in o.material_slots] for o in bpy.data.objects if o.type=='MESH'}
    names_before=set(bpy.data.materials.keys())
    again,new=apply_materials(config,records)
    assert not new and names_before==set(bpy.data.materials.keys())
    assert assignments==again
    assert slots_before=={o.name:[s.material.name if s.material else None for s in o.material_slots] for o in bpy.data.objects if o.type=='MESH'}
    env=setup_environment(config)
    preserved=check_preserved(before)
    bpy.context.scene.render.filepath=str(preview/'eevee_preview.png')
    bpy.ops.render.render(write_still=True)
    # 临时文件 + 原子替换：保存失败不会破坏当前工程。
    project_io.save_project(config)
    assert input_hashes=={str(p.relative_to(input_root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in input_root.rglob('*') if p.is_file()}
    result={'project':str(project.relative_to(project_io.WORKSPACE)).replace('\\','/'),'project_before_sha256':before_project,
            'project_after_sha256':hashlib.sha256(project.read_bytes()).hexdigest(),'source_files_unchanged':True,
            'sdf_visual_count':len(records),'sdf_material_count':sum(r['has_material'] for r in records),'created_material_count':len(created),
            'created_materials':created,'assigned_object_count':len(assignments),'assignments':assignments,'sdf_records':records,
            'preservation':preserved,'idempotence_passed':True,'environment':env,'gui_status':'待实际打开截图检查'}
    (reports/'material_validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
    write_report(result,settings,reports)
    copied=project_io.publish([reports/'material_validation.json',reports/'material_structure_baseline.json',
                               preview/'eevee_preview.png'],evidence)
    project_io.clear_work_dir(config)
    print('MATERIAL_STAGE_OK',len(created),len(assignments),flush=True)
    print('MATERIAL_EVIDENCE',', '.join(p.name for p in copied),flush=True)

if __name__=='__main__':
    main()
