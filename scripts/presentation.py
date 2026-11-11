"""独立展示场景：共享源网格与材质，复用机械Action，不改动源装配。"""
import hashlib
import json
from pathlib import Path

import bpy
from mathutils import Matrix, Vector

from animation import exploded_view as ex
from animation import kinematics as k

OWNER = 'aeroviz_stage4'


def activate(scene):
    bpy.context.window.scene = scene
    scene.frame_set(scene.frame_current)
    bpy.context.view_layer.update()


def scene_state(scene):
    return {'objects': sorted(o.name for o in scene.objects),
            'range': [scene.frame_start, scene.frame_end, scene.render.fps],
            'camera': scene.camera.name if scene.camera else None,
            'markers': [(m.name, m.frame, m.camera.name if m.camera else None) for m in scene.timeline_markers],
            'world': scene.world.name if scene.world else None,
            'properties': {x: str(scene[x]) for x in scene.keys()}}


def capture_source(config):
    """只在源场景第一帧比较；几何和全部原Action另有完整指纹。"""
    scene = bpy.data.scenes[config['presentation']['source_scene']]
    activate(scene)
    scene.frame_set(1)
    result = k.base_snapshot()
    result.update(actions=ex.actions_snapshot(list(scene.objects)),
                  mesh_fingerprints=ex.mesh_fingerprints(), material_links=ex.material_links(),
                  scene=scene_state(scene),
                  collections={c.name: {'objects': sorted(o.name for o in c.objects),
                                       'children': sorted(x.name for x in c.children),
                                       'hide_render': c.hide_render, 'hide_viewport': c.hide_viewport}
                               for c in bpy.data.collections if not c.get(OWNER)})
    return result


def check_source(config, baseline):
    now = capture_source(config)
    for field, original in baseline.items():
        actual = now[field]
        if isinstance(original, dict):
            actual = {name: actual[name] for name in original}
        # 元组经JSON保存后是列表；统一规范化再比较。
        assert json.dumps(actual, sort_keys=True) == json.dumps(original, sort_keys=True), field
    return {'status': 'PASS', 'objects': len(baseline['objects']),
            'original_actions': len(baseline['actions']),
            'original_meshes': len(baseline['mesh_fingerprints']),
            'original_materials': len(baseline['material_signatures'])}


def owned(block):
    block[OWNER] = True
    return block


def empty(name, collection):
    obj = owned(bpy.data.objects.new(name, None))
    collection.objects.link(obj)
    obj.empty_display_size = .012
    return obj


def key(obj, frame, location=None, energy=None):
    if location is not None:
        obj.location = location
        obj.keyframe_insert(data_path='location', frame=frame)
    if energy is not None:
        obj.data.energy = energy
        obj.data.keyframe_insert(data_path='energy', frame=frame)


def hex_linear(value):
    rgb = [int(value[i:i+2], 16)/255 for i in (0, 2, 4)]
    return [v/12.92 if v <= .04045 else ((v+.055)/1.055)**2.4 for v in rgb]


def build_grid(scene, collection, spec):
    """颜色按sRGB色号解码到线性，地面线条弱混合并随距离淡出。"""
    palette = spec['palette']
    world = owned(bpy.data.worlds.new('S4::HAWKEYE_WORLD'))
    world.use_nodes = True
    world.node_tree.nodes['Background'].inputs['Color'].default_value = (*hex_linear(palette['world']), 1)
    world.node_tree.nodes['Background'].inputs['Strength'].default_value = .7
    world['palette_srgb'] = json.dumps(palette)
    scene.world = world
    mesh = owned(bpy.data.meshes.new('S4::GROUND_GEOMETRY'))
    z = spec['ground_z']
    mesh.from_pydata([(-100,-100,z),(100,-100,z),(100,100,z),(-100,100,z)], [], [(0,1,2,3)])
    ground = owned(bpy.data.objects.new('S4::GROUND', mesh))
    collection.objects.link(ground)
    mat = owned(bpy.data.materials.new('S4::HAWKEYE_GRID'))
    mat.use_nodes = True
    mat['palette_srgb'] = json.dumps(palette)
    nodes = mat.node_tree.nodes
    nodes.clear()
    links = mat.node_tree.links
    def node(kind): return nodes.new(kind)
    def math_node(op, a, b=None):
        n = node('ShaderNodeMath'); n.operation = op
        for i, value in enumerate((a,b)):
            if value is None: continue
            if isinstance(value, (int,float)): n.inputs[i].default_value = value
            else: links.new(value, n.inputs[i])
        return n.outputs[0]
    geom = node('ShaderNodeNewGeometry')
    separate = node('ShaderNodeSeparateXYZ'); links.new(geom.outputs['Position'], separate.inputs[0])
    masks = []
    for spacing, width in ((.1,.012),(.5,.004)):
        axes = []
        for axis in ('X','Y'):
            phase = math_node('FRACT', math_node('DIVIDE', separate.outputs[axis], spacing))
            distance = math_node('MINIMUM', phase, math_node('SUBTRACT', 1, phase))
            axes.append(math_node('LESS_THAN', distance, width))
        masks.append(math_node('MAXIMUM', *axes))
    radius = node('ShaderNodeVectorMath'); radius.operation = 'LENGTH'
    links.new(geom.outputs['Position'], radius.inputs[0])
    fade = math_node('MAXIMUM', math_node('SUBTRACT', 1, math_node('DIVIDE', radius.outputs['Value'], 4)), 0)
    color = (*hex_linear(palette['ground']),1)
    for mask, code, strength in zip(masks, ('minor_grid','major_grid'), (.10,.16)):
        mix = node('ShaderNodeMixRGB'); mix.blend_type = 'MIX'
        links.new(math_node('MULTIPLY', math_node('MULTIPLY', mask, strength), fade), mix.inputs[0])
        if isinstance(color, tuple): mix.inputs[1].default_value = color
        else: links.new(color, mix.inputs[1])
        mix.inputs[2].default_value = (*hex_linear(palette[code]),1)
        color = mix.outputs[0]
    shader = node('ShaderNodeBsdfPrincipled')
    links.new(color, shader.inputs['Base Color'])
    shader.inputs['Roughness'].default_value = .73
    shader.inputs['Metallic'].default_value = .06
    shader.inputs['Specular IOR Level'].default_value = .25
    links.new(color, shader.inputs['Emission Color'])
    shader.inputs['Emission Strength'].default_value = .65
    output = node('ShaderNodeOutputMaterial'); links.new(shader.outputs[0], output.inputs[0])
    mesh.materials.append(mat)


def camera(name, collection, helpers):
    data = owned(bpy.data.cameras.new(name))
    obj = owned(bpy.data.objects.new(name, data)); collection.objects.link(obj)
    data.lens = 48; data.clip_start = .005; data.clip_end = 250
    target = empty(name+'::TARGET', helpers)
    track = obj.constraints.new('TRACK_TO'); track.target = target
    track.track_axis = 'TRACK_NEGATIVE_Z'; track.up_axis = 'UP_Y'
    return obj, target


def camera_keys(pair, rows):
    for frame, position, target in rows:
        key(pair[0], frame, position); key(pair[1], frame, target)


def centroid(obj):
    return sum((obj.matrix_world @ Vector(p) for p in obj.bound_box), Vector())/8


def configure_layout(scene):
    """把最大编辑区设为相机视图，保留时间轴供用户直接播放。"""
    activate(scene)
    for screen in (bpy.context.screen,):
        areas = [a for a in screen.areas if a.type not in ('TOPBAR','STATUSBAR')]
        if not areas: continue
        largest = max(areas, key=lambda a: a.width*a.height)
        largest.type = 'VIEW_3D'
        space = largest.spaces.active
        if space.type != 'VIEW_3D':
            # 后台模式延迟创建编辑区；真实窗口打开后再次应用并验收布局。
            continue
        space.region_3d.view_perspective = 'CAMERA'
        space.region_3d.view_camera_zoom = 20
        space.overlay.show_overlays = False
        space.shading.type = 'MATERIAL'
        space.shading.use_scene_lights = True
        space.shading.use_scene_world = True
        space.show_region_ui = False
        for area in areas:
            if area == largest: continue
            if area.type == 'DOPESHEET_EDITOR':
                if area.width > largest.width*.8 and area.y < largest.y:
                    area.ui_type = 'TIMELINE'
                    area.spaces.active.show_markers = True
                else:
                    area.type = 'PROPERTIES'
    for marker in scene.timeline_markers:
        marker.name = marker.name.split(' | ')[0]
    # Blender会用相机名覆盖切换标记的显示文字，另加紧随其后的阶段标记供定位。
    if scene.get('presentation_config_json'):
        spec = json.loads(scene['presentation_config_json'])
        for shot in spec['shots']:
            cut = next(m for m in scene.timeline_markers if m.frame == shot[2] and m.camera)
            cut.name = 'CUT::'+shot[0];cut.select = False
            phase = scene.timeline_markers.get(shot[0]) or scene.timeline_markers.new(shot[0])
            phase.frame = shot[2]+1;phase.camera = None;phase.select = True
    scene.frame_set(1)


def build(config, baseline):
    spec = config['presentation']
    if bpy.data.scenes.get(spec['scene']):
        raise ValueError('展示层已存在；拒绝叠加。请先验证或使用明确的撤销入口。')
    assert check_source(config, baseline)['status'] == 'PASS'
    source = bpy.data.scenes[spec['source_scene']]
    source.frame_set(1)
    originals = {o.name:o for o in source.objects}
    world_matrices = {n:o.matrix_world.copy() for n,o in originals.items()}
    centers = {n:centroid(o) for n,o in originals.items() if o.type == 'MESH'}
    film = owned(bpy.data.scenes.new(spec['scene']))
    film.unit_settings.system = 'METRIC'; film.unit_settings.scale_length = 1
    film.frame_start = 1; film.frame_end = spec['frame_end']; film.render.fps = spec['fps']
    film.render.engine = 'BLENDER_EEVEE'
    film.render.resolution_x = spec['preview']['width']; film.render.resolution_y = spec['preview']['height']
    film.render.resolution_percentage = 100
    film.eevee.taa_render_samples = spec['preview']['samples']
    film.render.image_settings.file_format = 'PNG'; film.render.image_settings.color_mode = 'RGB'
    film.view_settings.view_transform = 'AgX'
    film.view_settings.look = 'AgX - Medium High Contrast'
    root = owned(bpy.data.collections.new(spec['scene'])); film.collection.children.link(root)
    cols = {}
    for name in ('CAMERA_RIG','LIGHT_RIG','BACKGROUND','STAGE4_ACTIONS','STAGE4_HELPERS','STAGE4_INSTANCES'):
        col = owned(bpy.data.collections.new('S4::'+name)); root.children.link(col); cols[name] = col
    activate(film)
    modules = {}; proxies = {}
    for module in spec['modules']:
        group = empty('S4::MODULE::'+module['id'], cols['STAGE4_ACTIONS']); modules[module['id']] = group
        group['source_objects'] = json.dumps(module['objects'])
        for frame, delta in ((1,[0,0,0]),(module['start'],[0,0,0]),(module['end'],module['delta']),(spec['frame_end'],module['delta'])):
            key(group, frame, delta)
        group.location = (0,0,0)
        for name in module['objects']:
            original = originals[name]
            assert original.type == 'MESH' and not original.get('reference_only')
            proxy = original.copy(); proxy.animation_data_clear()
            proxy.name = 'S4::INSTANCE::'+name; owned(proxy)
            proxy['source_object'] = name
            cols['STAGE4_INSTANCES'].objects.link(proxy)
            proxy.parent = group; proxy.matrix_parent_inverse = Matrix.Identity(4)
            proxy.matrix_basis = world_matrices[name]
            proxy.hide_render = False; proxy.hide_viewport = False
            proxies[name] = proxy
    expected = {n for n,o in originals.items() if o.type == 'MESH' and not o.get('reference_only')}
    assert set(proxies) == expected, (set(proxies),expected)
    for reuse in spec['motion_reuse']:
        original = originals['JOINT::'+reuse['joint']]
        proxy = proxies[reuse['object']]; module = proxy.parent
        pivot = empty('S4::MOTION::'+reuse['joint'], cols['STAGE4_HELPERS'])
        pivot.parent = module; pivot.matrix_basis = world_matrices[original.name]
        pivot.rotation_mode = 'QUATERNION'
        proxy.parent = pivot; proxy.matrix_basis = world_matrices[original.name].inverted() @ world_matrices[reuse['object']]
        animation = pivot.animation_data_create()
        track = animation.nla_tracks.new(); track.name = 'S4::REUSE::'+reuse['joint']
        strip = track.strips.new('S4::'+reuse['joint'], reuse['timeline'][0], original.animation_data.action)
        strip.action_slot = original.animation_data.action_slot
        strip.action_frame_start, strip.action_frame_end = reuse['source']
        strip.frame_start, strip.frame_end = reuse['timeline']
        strip.blend_type = 'REPLACE'; strip.extrapolation = 'HOLD'
        pivot['reused_action'] = original.animation_data.action.name
    build_grid(film, cols['BACKGROUND'], spec)
    cameras = {name:camera('S4::CAMERA_'+name,cols['CAMERA_RIG'],cols['STAGE4_HELPERS']) for name in 'ABC'}
    # 主镜头始终处在+X前方、-Y侧面，仅小幅环绕；扩展构图容纳已退出模块。
    main_rows = [
        (1,(.97,-1.02,-.015),(0,0,-.045)), (10,(.97,-1.02,-.015),(0,0,-.045)),
        (48,(.70,-.84,.22),(0,0,-.045)), (60,(.70,-.84,.22),(0,0,-.045)),
        (61,(.95,-1.15,.48),(0,0,-.22)), (140,(.95,-1.15,.48),(0,0,-.22)),
        (181,(1.12,-1.40,.63),(0,0,-.20)), (306,(1.23,-1.31,.69),(0,0,-.20)),
        (1036,(1.24,-1.43,.70),(0,0,-.10)), (1516,(1.24,-1.43,.70),(0,0,-.10)),
        (1530,(1.24,-1.43,.70),(0,0,-.10)),(1620,(1.55,-1.65,1.02),(0,0,-.10)),
        (1650,(1.55,-1.65,1.02),(0,0,-.10))]
    # 按每个关键时刻的真实包围盒约束构图，避免终态电池或脚架被裁切。
    fitted = []
    for frame, position, target in main_rows:
        target = Vector(target); direction = (Vector(position)-target).normalized()
        rotation = (-direction).to_track_quat('-Z','Y').to_matrix()
        right, up = rotation.col[0], rotation.col[1]
        tan_h = cameras['A'][0].data.sensor_width/(2*cameras['A'][0].data.lens)
        tan_v = tan_h*film.render.resolution_y/film.render.resolution_x
        required = 0
        for module in spec['modules']:
            t = max(0,min(1,(frame-module['start'])/(module['end']-module['start'])))
            t = t*t*(3-2*t)
            delta = Vector(module['delta'])*t
            for name in module['objects']:
                for corner in originals[name].bound_box:
                    relative = world_matrices[name] @ Vector(corner)+delta-target
                    required = max(required,relative.dot(direction)+abs(relative.dot(right))/(tan_h*.86),
                                   relative.dot(direction)+abs(relative.dot(up))/(tan_v*.86))
        # 首尾推进/拉远保留至少6%的动作幅度；静止节点不添加微漂移。
        distance = max((Vector(position)-target).length,required)
        if frame in (1,10): distance *= 1.10
        if frame in (1620,1650): distance *= 1.10
        fitted.append((frame,target+direction*distance,target))
    camera_keys(cameras['A'],fitted)
    camera_keys(cameras['B'], [(1,(.80,-.92,1.15),(0,0,-.20)),
                               (531,(.80,-.92,1.15),(0,0,-.20)),
                               (1035,(.80,-.92,1.15),(0,0,-.20)),
                               (1650,(.80,-.92,1.15),(0,0,-.20))])
    # 细节镜头只在相应剪切段生效；取源几何中心，不改原装配偏置。
    byid = {m['id']:m for m in spec['modules']}
    for detail in spec['details']:
        start,end,name,module_id,offset = (detail[x] for x in ('start','end','object','module','offset'))
        module = byid[module_id]; original_center = centers[name]
        for frame,scale in ((start,1.08),(start+6,1.08),(end-7,1),(end,1)):
            t = max(0,min(1,(frame-module['start'])/(module['end']-module['start'])))
            t = t*t*(3-2*t)
            target = original_center + Vector(module['delta'])*t
            camera_keys(cameras['C'],[(frame,target+Vector(offset)*scale,target)])
    for shot in spec['shots']:
        marker = film.timeline_markers.new(shot[0],frame=shot[2])
        marker.camera = cameras[shot[4]][0]
    film.camera = cameras['A'][0]
    for label, position, power, size, target in (
        ('KEY',(.35,-.40,1.20),22,.75,(0,0,-.1)),
        ('RIM',(-.55,.65,.55),20,.55,(0,0,-.1)),
        ('FILL',(.20,-.80,-.20),8,.65,(0,0,-.22)),
        ('REVEAL',(.80,.10,.60),12,.40,(0,0,-.04))):
        data = owned(bpy.data.lights.new('S4::LIGHT_'+label,'AREA'))
        data.energy = power; data.shape = 'DISK'; data.size = size
        obj = owned(bpy.data.objects.new(data.name,data)); cols['LIGHT_RIG'].objects.link(obj)
        obj.location = position
        obj.rotation_euler = (Vector(target)-obj.location).to_track_quat('-Z','Y').to_euler()
        if label in ('KEY','REVEAL'):
            for frame,energy in ((1,power*.20),(8,power*.20),(45,power),(60,power)):
                key(obj,frame,energy=energy)
        if label == 'REVEAL':
            key(obj,1,(.8,.1,.6));key(obj,48,(.55,-.25,.65));key(obj,60,(.55,-.25,.65))
    detail_data = owned(bpy.data.lights.new('S4::LIGHT_DETAIL','AREA'))
    detail_data.energy = 4; detail_data.shape = 'DISK'; detail_data.size = .5
    detail_light = owned(bpy.data.objects.new(detail_data.name,detail_data))
    cols['LIGHT_RIG'].objects.link(detail_light)
    follow = detail_light.constraints.new('COPY_LOCATION'); follow.target = cameras['C'][0]
    aim = detail_light.constraints.new('TRACK_TO'); aim.target = cameras['C'][1]
    aim.track_axis = 'TRACK_NEGATIVE_Z'; aim.up_axis = 'UP_Y'
    # 特写灯只在C镜头亮起，其余镜头不受切换中的灯位影响。
    powers = {1:0, spec['frame_end']:0}
    for detail in spec['details']:
        powers[detail['start']-1] = 0; powers[detail['start']] = 4
        powers[detail['end']] = 4; powers[detail['end']+1] = 0
    for frame,energy in sorted(powers.items()): key(detail_light,frame,energy=energy)
    for action in bpy.data.actions:
        if action.name not in {row['name'] for row in baseline['actions'].values()}:
            owned(action)
            if not action.name.startswith('S4::'): action.name = 'S4::'+action.name
            for layer in action.layers:
                for strip in layer.strips:
                    for bag in strip.channelbags:
                        for curve in bag.fcurves:
                            for point in curve.keyframe_points:
                                point.interpolation = 'BEZIER'
                                point.handle_left_type = 'AUTO_CLAMPED'; point.handle_right_type = 'AUTO_CLAMPED'
    film['source_baseline_sha256'] = hashlib.sha256(json.dumps(baseline,sort_keys=True).encode()).hexdigest()
    film['presentation_config_json'] = json.dumps(spec,ensure_ascii=False,sort_keys=True)
    assert check_source(config,baseline)['status'] == 'PASS'
    activate(film); film.frame_set(1)
    configure_layout(film)
    return film


def validate(config, baseline):
    """完整源回归之外，验证展示实例身份、模块关系、动作顺序及NLA复用。"""
    source_result = check_source(config,baseline)
    spec = config['presentation']; film = bpy.data.scenes[spec['scene']]
    assert film.get(OWNER)
    assert set(bpy.data.objects.keys()) == set(baseline['objects']) | {o.name for o in film.objects}
    assert all(o.get(OWNER) for o in film.objects)
    assert not set(o.name for o in film.objects) & set(baseline['objects'])
    original_actions = {v['name'] for v in baseline['actions'].values()}
    assert all(a.name in original_actions or a.get(OWNER) for a in bpy.data.actions)
    activate(film); film.frame_set(1)
    matrix_error = 0.0
    for m in spec['modules']:
        ctrl = bpy.data.objects['S4::MODULE::'+m['id']]
        for name in m['objects']:
            a = bpy.data.objects['S4::INSTANCE::'+name]; b = bpy.data.objects[name]
            assert a.data == b.data
            assert [(s.link,s.material) for s in a.material_slots] == [(s.link,s.material) for s in b.material_slots]
            matrix_error = max(matrix_error,k.matrix_error(a.matrix_world,b.matrix_world))
            assert a.parent == ctrl or a.parent.parent == ctrl
    assert matrix_error < 1e-6, matrix_error
    assert {n for m in spec['modules'] for n in m['objects']} == {o.name for o in bpy.data.scenes[spec['source_scene']].objects if o.type == 'MESH' and not o.get('reference_only')}
    assert all(a['end'] < b['start'] for a,b in zip(spec['modules'],spec['modules'][1:])), '拆解时间重叠'
    assert [(m.frame,m.camera.name) for m in film.timeline_markers if m.camera] == [(s[2],'S4::CAMERA_'+s[4]) for s in spec['shots']]
    assert {(m.name,m.frame) for m in film.timeline_markers if not m.camera} == {(s[0],s[2]+1) for s in spec['shots']}
    endpoint_error = 0.0
    for module in spec['modules']:
        ctrl = bpy.data.objects['S4::MODULE::'+module['id']]
        film.frame_set(module['start']); assert ctrl.location.length < 1e-6
        film.frame_set(module['end'])
        endpoint_error = max(endpoint_error,(ctrl.location-Vector(module['delta'])).length)
    assert endpoint_error < 1e-6
    for reuse in spec['motion_reuse']:
        pivot = bpy.data.objects['S4::MOTION::'+reuse['joint']]
        original = bpy.data.objects['JOINT::'+reuse['joint']]
        strip = pivot.animation_data.nla_tracks[0].strips[0]
        assert strip.action == original.animation_data.action
        assert strip.action_slot == original.animation_data.action_slot
        assert [strip.frame_start,strip.frame_end] == reuse['timeline']
        assert [strip.action_frame_start,strip.action_frame_end] == reuse['source']
    relative_error = 0.0
    for module in spec['modules']:
        a = module['objects'][0]
        for b in module['objects'][1:]:
            source_relative = bpy.data.objects[a].matrix_world.inverted() @ bpy.data.objects[b].matrix_world
            for frame in (1,spec['frame_end'],module['end']):
                film.frame_set(frame)
                display_relative = bpy.data.objects['S4::INSTANCE::'+a].matrix_world.inverted() @ bpy.data.objects['S4::INSTANCE::'+b].matrix_world
                relative_error = max(relative_error,k.matrix_error(source_relative,display_relative))
    assert relative_error < 1e-6
    # 全时间轴逐帧检查模块运动：只允许声明的区间移动，平移单调且不旋转缩放。
    trajectory_error = 0.0; previous = {}; active_a_frames = 0; camera_margin = 1.0
    from bpy_extras.object_utils import world_to_camera_view
    for frame in range(1,spec['frame_end']+1):
        film.frame_set(frame)
        for module in spec['modules']:
            ctrl = bpy.data.objects['S4::MODULE::'+module['id']]
            delta = Vector(module['delta']); t = ctrl.location.dot(delta)/delta.length_squared
            assert -1e-6 <= t <= 1+1e-6
            assert t+1e-6 >= previous.get(module['id'],0)
            previous[module['id']] = t
            trajectory_error = max(trajectory_error,(ctrl.location-delta*t).length)
            if frame <= module['start']: assert ctrl.location.length < 1e-6
            if frame >= module['end']: assert (ctrl.location-delta).length < 1e-6
            assert Vector(ctrl.rotation_euler).length < 1e-7 and (ctrl.scale-Vector((1,1,1))).length < 1e-7
        if film.camera.name == 'S4::CAMERA_A':
            active_a_frames += 1
            for obj in film.objects:
                if not obj.get('source_object'): continue
                for corner in obj.bound_box:
                    projected = world_to_camera_view(film,film.camera,obj.matrix_world @ Vector(corner))
                    camera_margin = min(camera_margin,projected.x,projected.y,1-projected.x,1-projected.y)
    assert trajectory_error < 1e-6
    assert camera_margin > .02, camera_margin
    film.frame_set(1)
    return {'status':'PASS','source':source_result,'scene':film.name,
            'presentation_objects':len(film.objects),'global_objects':len(bpy.data.objects),
            'modules':len(spec['modules']),'linked_mesh_instances':sum(len(m['objects']) for m in spec['modules']),
            'reused_original_actions':len(spec['motion_reuse']),
            'initial_world_matrix_max_error':matrix_error,'endpoint_max_error':endpoint_error,
            'attached_parts_relative_matrix_max_error':relative_error,
            'trajectory_frames_verified':spec['frame_end'],'trajectory_axis_max_error':trajectory_error,
            'main_camera_frames_verified':active_a_frames,'main_camera_min_normalized_margin':camera_margin,
            'shots':len(spec['shots']),'range':[1,spec['frame_end']],
            'camera_cut_markers':len(spec['shots']),'readable_phase_markers':len(spec['shots']),
            'original_scene_unchanged':True}


def isolate_source_for_legacy_tests(config, baseline):
    """只读测试进程中移除已验证的新增层，运行历史全局计数断言；绝不保存。"""
    result = validate(config,baseline)
    source = bpy.data.scenes[spec_source := config['presentation']['source_scene']]
    activate(source)
    for obj in list(bpy.data.objects):
        if obj.get(OWNER): bpy.data.objects.remove(obj,do_unlink=True)
    for blocks in (bpy.data.scenes,bpy.data.collections,bpy.data.actions,bpy.data.meshes,
                   bpy.data.materials,bpy.data.cameras,bpy.data.lights,bpy.data.worlds):
        for block in list(blocks):
            if block.get(OWNER): blocks.remove(block,do_unlink=True)
    assert set(bpy.data.objects.keys()) == set(baseline['objects'])
    assert source.name == spec_source
    return result


def visual_signature(config):
    """忽略窗口布局与标记文字，比较副本预览与正式工程的渲染输入。"""
    scene = bpy.data.scenes[config['presentation']['scene']]
    activate(scene);scene.frame_set(1)
    data = {'objects':{},'actions':{},'materials':{},'world':[],
            'render':[scene.render.engine,scene.render.resolution_x,scene.render.resolution_y,
                      scene.view_settings.view_transform,scene.view_settings.look,scene.view_settings.exposure],
            'cuts':[(m.frame,m.camera.name) for m in scene.timeline_markers if m.camera]}
    import materials
    for obj in scene.objects:
        row = materials.object_state(obj)
        row['constraints'] = [(c.type,c.target.name if hasattr(c,'target') and c.target else None) for c in obj.constraints]
        row['material_slots'] = [(s.link,s.material.name if s.material else None) for s in obj.material_slots]
        if obj.type == 'CAMERA': row['camera'] = [obj.data.lens,obj.data.sensor_width,obj.data.clip_start,obj.data.clip_end]
        if obj.type == 'LIGHT': row['light'] = [obj.data.type,obj.data.energy,obj.data.size,list(obj.data.color)]
        if obj.animation_data:
            row['action'] = obj.animation_data.action.name if obj.animation_data.action else None
            row['nla'] = [(s.action.name,s.action_slot.identifier,s.frame_start,s.frame_end,s.action_frame_start,s.action_frame_end,s.blend_type,s.extrapolation)
                          for t in obj.animation_data.nla_tracks for s in t.strips]
        data['objects'][obj.name] = row
    for action in bpy.data.actions:
        if action.get(OWNER) or action.name in {o['name'] for o in ex.actions_snapshot(list(bpy.data.scenes[config['presentation']['source_scene']].objects)).values()}:
            data['actions'][action.name] = [(c.data_path,c.array_index,c.extrapolation,
                [(list(p.co),list(p.handle_left),list(p.handle_right),p.interpolation,p.handle_left_type,p.handle_right_type) for p in c.keyframe_points])
                for layer in action.layers for strip in layer.strips for bag in strip.channelbags for c in bag.fcurves]
    def nodes(tree):
        return [(n.name,n.type,[(s.name,list(s.default_value) if hasattr(s.default_value,'__len__') else s.default_value)
                 for s in n.inputs if hasattr(s,'default_value')]) for n in tree.nodes]
    for mat in bpy.data.materials:
        data['materials'][mat.name] = {'nodes':nodes(mat.node_tree),'links':ex.material_links()[mat.name]}
    data['world'] = nodes(scene.world.node_tree)
    return hashlib.sha256(json.dumps(data,sort_keys=True).encode()).hexdigest()
