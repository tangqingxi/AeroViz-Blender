"""独立的爆炸位移层：只增加配置声明的Empty和位移动画，保留原机械Action。"""
import argparse
from array import array
import hashlib
import json
from pathlib import Path
import sys
import bpy
from mathutils import Matrix,Vector

WORKSPACE=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(WORKSPACE/'scripts'));sys.dont_write_bytecode=True
import project_io
import coordinate_frames
from animation import kinematics as k


def controller_name(config,branch):
    return config['exploded_view']['controller_prefix']+branch['joint']


def contract(config):
    if not bpy.context.scene.get('aeroviz_exploded'):
        return {},set()
    spec=config['exploded_view']
    parents={'JOINT::'+b['joint']:(controller_name(config,b),b['parent']) for b in spec['branches']}
    return parents,{controller_name(config,b) for b in spec['branches']}


def actions_snapshot(objects=None):
    result={}
    for obj in objects if objects is not None else bpy.data.objects:
        if not obj.animation_data:continue
        action=obj.animation_data.action
        result[obj.name]={'name':action.name,'properties':{p:list(action[p]) if hasattr(action[p],'to_list') else action[p] for p in action.keys()},
                          'curves':[{'path':c.data_path,'index':c.array_index,'extrapolation':c.extrapolation,
                                     'keys':[{'co':list(p.co),'left':list(p.handle_left),'right':list(p.handle_right),'interpolation':p.interpolation,'easing':p.easing,'handles':[p.handle_left_type,p.handle_right_type]} for p in c.keyframe_points]} for c in k.fcurves(obj)]}
    return result


def mesh_fingerprints():
    result={}
    for obj in bpy.data.objects:
        if obj.type!='MESH':continue
        mesh=obj.data;digest=hashlib.sha256()
        for items,key,width,kind in [(mesh.vertices,'co',3,'f'),(mesh.vertices,'normal',3,'f'),(mesh.edges,'vertices',2,'i'),(mesh.loops,'vertex_index',1,'i'),(mesh.polygons,'material_index',1,'i'),(mesh.polygons,'use_smooth',1,'b')]:
            values=array(kind,[0])*(len(items)*width);items.foreach_get(key,values);digest.update(values.tobytes())
        result[obj.name]=digest.hexdigest()
    return result


def material_links():
    return {m.name:sorted([l.from_node.name,l.from_socket.identifier,l.to_node.name,l.to_socket.identifier] for l in m.node_tree.links) for m in bpy.data.materials}


def capture_baseline(config):
    scene=bpy.context.scene;scene.frame_set(config['animation']['frame_start'])
    baseline=k.base_snapshot()
    baseline['actions']=actions_snapshot()
    baseline['mesh_fingerprints']=mesh_fingerprints()
    baseline['material_links']=material_links()
    baseline['collections']={c.name:{'objects':sorted(o.name for o in c.objects),'children':sorted(x.name for x in c.children),'hide_viewport':c.hide_viewport,'hide_render':c.hide_render} for c in bpy.data.collections}
    baseline['subtrees']={o.name:sorted(x.name for x in o.children_recursive) for o in bpy.data.objects if o.name.startswith('JOINT::')}
    scene.frame_set(config['animation']['frame_end'])
    baseline['end_matrices']={o.name:[list(r) for r in o.matrix_world] for o in bpy.data.objects}
    scene.frame_set(config['animation']['frame_start'])
    return baseline


def factor(spec,frame):
    a,b,c,d=spec['mechanical_end'],spec['fully_exploded'],spec['hold_end'],spec['frame_end']
    if frame<=a:return 0.0
    if frame<b:return (frame-a)/(b-a)
    if frame<=c:return 1.0
    if frame<d:return (d-frame)/(d-c)
    return 0.0


def check_source(config,baseline):
    spec=config['exploded_view'];names=set()
    for branch in spec['branches']:
        name='JOINT::'+branch['joint'];joint=bpy.data.objects[name]
        if name in names:raise ValueError('重复爆炸分支：'+name)
        names.add(name)
        if joint.parent.name!=branch['parent'] or joint.children[0].name!=branch['child_link']:
            raise ValueError('关节直接父级或子LINK不符合配置：'+name)
        if sorted(o.name for o in joint.children_recursive)!=baseline['subtrees'][name]:
            raise ValueError('原始关节子树已改变：'+name)
        meshes=sorted(o.name for o in joint.children_recursive if o.type=='MESH')
        if not meshes or meshes!=sorted(branch['meshes']):raise ValueError('分支网格不符：'+name)
        for mesh in (bpy.data.objects[n] for n in meshes):
            if mesh.get('reference_only') or any(c.name==spec['exclude_collection'] for c in mesh.users_collection):raise ValueError('禁止爆炸参考网格')
        v=Vector(branch['direction_flu'])*branch['distance_m']
        if (v-Vector(branch['displacement_flu_m'])).length>1e-7:raise ValueError('方向距离与位移不一致')
    actual={o.name for o in bpy.data.objects if o.name.startswith('JOINT::') and any(x.type=='MESH' for x in o.children_recursive)}
    if names!=actual:raise ValueError('配置没有精确覆盖全部有网格的关节分支')
    if sum(o.name.startswith('JOINT::') for o in bpy.data.objects)!=spec['expected_joint_count']:raise ValueError('JOINT总数不符')
    if len(bpy.data.objects)!=spec['expected_original_objects']:raise ValueError('原始对象数量不符')


def local_displacement(config,branch):
    spec=config['exploded_view'];root=bpy.data.objects[spec['root_object']]
    # 位移是向量，不加模型原点平移；父级完整3x3逆矩阵正确处理其尺度。
    model=coordinate_frames.convert(config,branch['displacement_flu_m'],spec['coordinate_frame'],config['coordinate_frames']['model_frame'])
    world=root.matrix_world.to_3x3() @ Vector(model)
    parent=bpy.data.objects[branch['parent']]
    return parent.matrix_world.to_3x3().inverted() @ world,world


def build(config,baseline):
    spec=config['exploded_view'];scene=bpy.context.scene;scene.frame_set(spec['frame_start'])
    old_actions={o.name:o.animation_data.action.as_pointer() for o in bpy.data.objects if o.animation_data and o.name in baseline['objects']}
    coordinate_frames.attach_metadata(config)
    existing=bool(scene.get('aeroviz_exploded'))
    if not existing:check_source(config,baseline)
    col=bpy.data.collections.get(spec['collection'])
    if col is None:
        col=bpy.data.collections.new(spec['collection']);scene.collection.children.link(col)
    for branch in spec['branches']:
        name=controller_name(config,branch);joint=bpy.data.objects['JOINT::'+branch['joint']];parent=bpy.data.objects[branch['parent']]
        obj=bpy.data.objects.get(name)
        if obj is None:
            world=joint.matrix_world.copy();basis=joint.matrix_basis.copy();inverse=joint.matrix_parent_inverse.copy()
            obj=bpy.data.objects.new(name,None);col.objects.link(obj);obj.parent=parent;obj.matrix_parent_inverse=Matrix.Identity(4);obj.matrix_basis=Matrix.Identity(4)
            bpy.context.view_layer.update();joint.parent=obj;joint.matrix_parent_inverse=inverse;joint.matrix_world=world;bpy.context.view_layer.update()
            assert k.matrix_error(joint.matrix_basis,basis)<1e-6
            assert k.matrix_error(joint.matrix_parent_inverse,inverse)<1e-6
            obj['aeroviz_explode_joint']=joint.name
            obj.empty_display_size=.01;obj.hide_set(True)
        elif obj.get('aeroviz_explode_joint')!=joint.name or joint.parent!=obj or obj.parent!=parent:
            raise ValueError('已有控制器不符合安全插入契约：'+name)
        if obj.animation_data:
            action=obj.animation_data.action
            if not action.get('aeroviz_explode_owned'):raise ValueError('不能覆盖外来爆炸动画')
            obj.animation_data_clear()
            if action.users==0:bpy.data.actions.remove(action)
        obj.rotation_mode='QUATERNION';obj.rotation_quaternion=(1,0,0,0);obj.scale=(1,1,1)
        local,world=local_displacement(config,branch)
        for frame in (spec['frame_start'],spec['mechanical_end'],spec['fully_exploded'],spec['hold_end'],spec['frame_end']):
            obj.location=local*factor(spec,frame);obj.keyframe_insert(data_path='location',frame=frame,group=branch['group'])
        action=obj.animation_data.action;action.name='Explode::'+config['model_name']+'::'+branch['joint'];action['aeroviz_explode_owned']=True
        for curve in k.fcurves(obj):
            curve.extrapolation='CONSTANT'
            for key in curve.keyframe_points:key.interpolation=spec['interpolation']
    for name,frame in spec['markers'].items():
        marker=scene.timeline_markers.get(name) or scene.timeline_markers.new(name);marker.frame=frame
    scene.frame_start=spec['frame_start'];scene.frame_end=spec['frame_end'];scene.render.fps=config['animation']['fps']
    scene['aeroviz_exploded']=json.dumps({'version':1,'branches':len(spec['branches'])})
    scene.frame_set(spec['frame_start']);bpy.context.view_layer.update()
    assert old_actions=={o.name:o.animation_data.action.as_pointer() for o in bpy.data.objects if o.name in old_actions}
    assert actions_snapshot([bpy.data.objects[n] for n in baseline['actions']])==baseline['actions']


def validate(config,baseline):
    spec=config['exploded_view'];scene=bpy.context.scene;scene.frame_set(spec['frame_start'])
    parents,controllers=contract(config);assert controllers
    assert set(bpy.data.objects.keys())==set(baseline['objects'])|controllers
    assert len(controllers)==len(spec['branches'])
    assert sorted(o.name for o in bpy.data.collections[spec['collection']].objects)==sorted(controllers)
    now=k.base_snapshot()
    assert mesh_fingerprints()==baseline['mesh_fingerprints']
    assert material_links()==baseline['material_links']
    for key in ('material_signatures','slots','material_nodes'):assert now[key]==baseline[key],key
    for name,before in baseline['objects'].items():
        after=now['objects'][name]
        if name in parents:
            new,old=parents[name];assert before['parent']==old and after['parent']==new
            after=dict(after,parent=old)
        assert after==before,('原始状态改变',name)
    for name,before in baseline['collections'].items():
        col=bpy.data.collections[name]
        assert sorted(o.name for o in col.objects)==before['objects']
        assert sorted(x.name for x in col.children)==before['children']
        assert (col.hide_viewport,col.hide_render)==(before['hide_viewport'],before['hide_render'])
    assert actions_snapshot([bpy.data.objects[n] for n in baseline['actions']])==baseline['actions']
    assert set(o.name for o in bpy.data.objects if o.animation_data)==set(baseline['actions'])|controllers
    controller_checks=[]
    for branch in spec['branches']:
        obj=bpy.data.objects[controller_name(config,branch)]
        assert obj.type=='EMPTY' and obj.parent.name==branch['parent']
        assert obj.get('aeroviz_explode_joint')=='JOINT::'+branch['joint']
        assert sorted(c.name for c in obj.users_collection)==[spec['collection']]
        assert k.matrix_error(obj.matrix_parent_inverse,Matrix.Identity(4))<1e-7
        assert obj.location.length<1e-7 and not obj.constraints and not obj.animation_data.drivers and not obj.animation_data.nla_tracks
        controller_checks.append({'controller':obj.name,'parent':obj.parent.name,'joint':'JOINT::'+branch['joint'],'child_link':branch['child_link'],'group':branch['group'],'frame1_location':list(obj.location),'rotation_quaternion':list(obj.rotation_quaternion),'scale':list(obj.scale),'parent_inverse_identity':True,'status':'PASS'})
    expected_end={n:Matrix(m) for n,m in baseline['end_matrices'].items()}
    frame_rows=[];max_error=0;return_error=0
    for frame in range(spec['mechanical_end'],spec['frame_end']+1):
        scene.frame_set(frame);bpy.context.view_layer.update();depsgraph=bpy.context.evaluated_depsgraph_get()
        expected={n:m.copy() for n,m in expected_end.items()};controller_rows={}
        for branch in spec['branches']:
            obj=bpy.data.objects[controller_name(config,branch)];joint=bpy.data.objects['JOINT::'+branch['joint']]
            assert obj.parent.name==branch['parent'] and joint.parent==obj
            assert sorted(x.name for x in joint.children_recursive if x.name in baseline['objects'])==baseline['subtrees'][joint.name]
            local,world=local_displacement(config,branch);f=factor(spec,frame)
            assert (obj.location-local*f).length<1e-6
            assert abs(obj.rotation_quaternion.w-1)<1e-6 and Vector((obj.rotation_quaternion.x,obj.rotation_quaternion.y,obj.rotation_quaternion.z)).length<1e-6 and (obj.scale-Vector((1,1,1))).length<1e-6
            for name in (joint.name,*baseline['subtrees'][joint.name]):expected[name]=Matrix.Translation(world*f) @ expected[name]
            controller_rows[obj.name]={'local_location':list(obj.location),'expected_world_offset':list(world*f)}
        errors={n:k.matrix_error(bpy.data.objects[n].evaluated_get(depsgraph).matrix_world,m) for n,m in expected.items()}
        maximum=max(errors.values());assert maximum<1e-6,(frame,maximum);max_error=max(max_error,maximum)
        if frame==spec['frame_end']:return_error=maximum
        frame_rows.append({'frame':frame,'factor':factor(spec,frame),'max_rigid_translation_error':maximum,'controllers':controller_rows})
    for name in controllers:
        curves=k.fcurves(bpy.data.objects[name]);assert len(curves)==3
        assert all(c.data_path=='location' and len(c.keyframe_points)==5 and all(p.interpolation=='LINEAR' for p in c.keyframe_points) for c in curves)
    assert all(scene.timeline_markers.get(n) and scene.timeline_markers[n].frame==f for n,f in spec['markers'].items())
    scene.frame_set(spec['frame_start'])
    coordinate=coordinate_frames.verify_scene(config)
    return {'status':'PASS','coordinate_tests':coordinate,'controllers':sorted(controllers),'controller_checks':controller_checks,'original_objects':len(baseline['objects']),'object_total':len(bpy.data.objects),'animated_objects':len(controllers)+len(baseline['actions']),
            'original_actions_unchanged':True,'original_geometry_materials_hierarchy_preserved_with_parent_whitelist':True,'max_matrix_error':max_error,'assembly_return_error':return_error,'frame_rows':frame_rows}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--config',required=True);parser.add_argument('--expected-sha256',required=True)
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:]);config=json.loads(project_io.resolve(args.config).read_text(encoding='utf8'));target=project_io.project(config)
    assert hashlib.sha256(target.read_bytes()).hexdigest()==args.expected_sha256
    bpy.ops.wm.open_mainfile(filepath=str(target));baseline=capture_baseline(config);build(config,baseline);validate(config,baseline);project_io.save_project(config)


if __name__=='__main__':main()
