"""在现有展示Scene上定向修订，不重建实例、原网格或原机械Action。"""
import json
import math
from pathlib import Path

import bpy
from mathutils import Matrix,Quaternion,Vector

import geometry_checks as geo
import presentation as p
from animation import kinematics as k


def smooth(t):
    t=max(0,min(1,t))
    return t*t*(3-2*t)


def angle_at(keys,frame):
    if frame <= keys[0][0]: return keys[0][1]
    for (a,x),(b,y) in zip(keys,keys[1:]):
        if frame<=b:return x+(y-x)*smooth((frame-a)/(b-a))
    return keys[-1][1]


def location_keys(module):
    return [(1,[0,0,0]),(module['start'],[0,0,0]),*module.get('waypoints',[]),
            (module['end'],module['delta']),(module['return_start'],module['delta']),
            *module.get('return_waypoints',[]),(module['return_end'],[0,0,0]),(990,[0,0,0])]


def location_at(module,frame):
    keys=location_keys(module)
    if frame<=keys[0][0]:return Vector(keys[0][1])
    for (a,x),(b,y) in zip(keys,keys[1:]):
        if frame<=b:return Vector(x)+(Vector(y)-Vector(x))*smooth((frame-a)/(b-a))
    return Vector(keys[-1][1])


def clear_animation(block):
    if block.animation_data:
        action=block.animation_data.action
        if action and not action.get(p.OWNER): raise ValueError('拒绝清理非展示动画：'+block.name)
        block.animation_data_clear()


def ease_owned():
    for action in bpy.data.actions:
        if not action.get(p.OWNER):continue
        for layer in action.layers:
            for strip in layer.strips:
                for bag in strip.channelbags:
                    for curve in bag.fcurves:
                        for point in curve.keyframe_points:
                            point.interpolation='LINEAR' if action.get('r1_sampled_rotation') or action.get('r1_sampled_location') else 'BEZIER'
                            point.handle_left_type=point.handle_right_type='AUTO_CLAMPED'


def name_action(block,label):
    if block.animation_data and block.animation_data.action:
        action=block.animation_data.action
        p.owned(action);action.name='S4::R1::'+label


def studio(config,scene):
    spec=config['presentation'];palette=spec['palette']
    world=scene.world
    world.node_tree.nodes['Background'].inputs['Color'].default_value=(*p.hex_linear(palette['world']),1)
    world.node_tree.nodes['Background'].inputs['Strength'].default_value=1
    world['palette_srgb']=json.dumps(palette);world['style']='Neutral Tech Studio'
    mat=bpy.data.objects['S4::GROUND'].material_slots[0].material
    mat['palette_srgb']=json.dumps(palette);mat['style']='Neutral Tech Studio'
    mixes=[n for n in mat.node_tree.nodes if n.type=='MIX_RGB']
    mixes[0].inputs[1].default_value=(*p.hex_linear(palette['ground']),1)
    mixes[0].inputs[2].default_value=(*p.hex_linear(palette['minor_grid']),1)
    mixes[1].inputs[2].default_value=(*p.hex_linear(palette['major_grid']),1)
    for node in mat.node_tree.nodes:
        if node.type=='MATH' and node.operation=='DIVIDE':
            value=node.inputs[1].default_value
            if abs(value-.1)<1e-5:node.inputs[1].default_value=.25
            elif abs(value-.5)<1e-5:node.inputs[1].default_value=1
        if node.type=='MATH' and node.operation=='MULTIPLY' and not node.inputs[1].is_linked:
            value=node.inputs[1].default_value
            if abs(value-.10)<1e-5:node.inputs[1].default_value=.018
            elif abs(value-.16)<1e-5:node.inputs[1].default_value=.028
    shader=next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
    shader.inputs['Emission Strength'].default_value=.85
    shader.inputs['Metallic'].default_value=.025;shader.inputs['Roughness'].default_value=.80
    lights=[('KEY',(.35,-.50,1.25),19,1.05,(0,0,-.08)),
            ('FILL',(.30,-.85,-.10),14,.90,(0,0,-.15)),
            ('RIM',(-.65,.60,.50),19,.85,(0,0,-.15)),
            ('REVEAL',(.70,-.10,.75),10,.80,(0,0,-.08)),
            ('RIM_RIGHT',(.65,.70,.20),13,.85,(0,0,-.18))]
    collection=bpy.data.collections['S4::LIGHT_RIG']
    for label,position,power,size,target in lights:
        name='S4::LIGHT_'+label;obj=bpy.data.objects.get(name)
        if obj is None:
            data=p.owned(bpy.data.lights.new(name,'AREA'));obj=p.owned(bpy.data.objects.new(name,data));collection.objects.link(obj)
        obj.location=position;obj.data.energy=power;obj.data.size=size
        obj.rotation_euler=(Vector(target)-obj.location).to_track_quat('-Z','Y').to_euler()
        if label in ('KEY','REVEAL'):
            for frame,factor in ((1,.42),(8,.42),(47,1),(60,1),(990,1)):p.key(obj,frame,energy=power*factor)
            name_action(obj.data,'LIGHT_'+label)
        if label=='REVEAL':
            p.key(obj,1,(.8,.10,.75));p.key(obj,48,(.60,-.25,.75));p.key(obj,60,(.60,-.25,.75))
            name_action(obj,'REVEAL_TRACK')
    detail=bpy.data.objects['S4::LIGHT_DETAIL'];power={1:0,990:0}
    for d in spec['details']:
        power[d['start']-1]=0;power[d['start']]=6;power[d['end']]=6;power[d['end']+1]=0
    for frame,energy in sorted(power.items()):p.key(detail,frame,energy=energy)
    name_action(detail.data,'DETAIL_LIGHT')
    scene.view_settings.look='AgX - Medium High Contrast'
    scene.view_settings.exposure=-.1


def fit(scene,camera,direction,target,objects,margin=.84):
    target=Vector(target);direction=Vector(direction).normalized()
    rotation=(-direction).to_track_quat('-Z','Y').to_matrix()
    right,up=rotation.col[0],rotation.col[1]
    horizontal=camera.data.sensor_width/(2*camera.data.lens)
    vertical=horizontal*scene.render.resolution_y/scene.render.resolution_x
    distance=0
    for obj in objects:
        for corner in obj.bound_box:
            relative=obj.matrix_world @ Vector(corner)-target
            distance=max(distance,relative.dot(direction)+abs(relative.dot(right))/(horizontal*margin),
                         relative.dot(direction)+abs(relative.dot(up))/(vertical*margin))
    return target+direction*distance,target


def cameras(config,scene):
    spec=config['presentation'];proxies=[o for o in scene.objects if o.get('source_object')]
    pairs={name:(bpy.data.objects['S4::CAMERA_'+name],bpy.data.objects['S4::CAMERA_'+name+'::TARGET']) for name in 'ABC'}
    rows=[]
    for frame,sample,direction,target,extra in (
        (1,1,(.95,-1.05,-.04),(0,0,-.045),1.13),(10,1,(.95,-1.05,-.04),(0,0,-.045),1.13),
        (48,80,(.72,-.88,.28),(0,0,-.045),1.04),(60,80,(.72,-.88,.28),(0,0,-.045),1.04),
        (120,80,(.72,-.88,.28),(0,0,-.045),1.04),
        (121,248,(.95,-1.15,.65),(0,0,-.19),1),(180,248,(.95,-1.15,.65),(0,0,-.19),1),
        (211,248,(.95,-1.15,.65),(0,0,-.19),1),(270,248,(.95,-1.15,.65),(0,0,-.19),1),
        (571,807,(1.03,-1.25,.75),(0,0,-.17),1),(810,807,(1.03,-1.25,.75),(0,0,-.17),1),
        (811,807,(1.03,-1.25,.75),(0,0,-.17),1),(822,807,(1.03,-1.25,.75),(0,0,-.17),1),
        (855,807,(1.10,-1.20,.95),(0,0,-.17),1.06),(870,807,(1.10,-1.20,.95),(0,0,-.17),1.06),
        (960,807,(1.10,-1.20,.95),(0,0,-.17),1.06),
        (961,1,(.75,-.92,.32),(0,0,-.045),1.04),(990,1,(.75,-.92,.32),(0,0,-.045),1.04)):
        scene.frame_set(sample)
        position,focus=fit(scene,pairs['A'][0],direction,target,proxies)
        position=focus+(position-focus)*extra
        rows.append((frame,position,focus))
    p.camera_keys(pairs['A'],rows)
    p.camera_keys(pairs['B'],[(1,(.85,-.98,.60),(0,0,-.18)),(390,(.85,-.98,.60),(0,0,-.18)),
        (391,(.50,-.58,.35),(0,0,-.14)),(480,(.50,-.58,.35),(0,0,-.14)),
        (481,(.85,-.98,.60),(0,0,-.20)),(990,(.85,-.98,.60),(0,0,-.20))])
    modules={m['id']:m for m in spec['modules']}
    for detail in spec['details']:
        name=detail['object'];proxy=bpy.data.objects['S4::INSTANCE::'+name]
        for frame,scale in ((detail['start'],1.06),(detail['start']+4,1.06),(detail['end']-5,1),(detail['end'],1)):
            scene.frame_set(frame)
            focus=p.centroid(proxy)
            focused=[proxy]
            if detail['module']=='SERVO1':
                surface=bpy.data.objects['S4::INSTANCE::cs11'];focus=(focus+p.centroid(surface))/2;focused.append(surface)
            offset=Vector(detail['offset'])
            fitted,_=fit(scene,pairs['C'][0],offset,focus,focused,margin=.80)
            distance=max(offset.length,(fitted-focus).length)*scale
            p.camera_keys(pairs['C'],[(frame,focus+offset.normalized()*distance,focus)])
    for pair in pairs.values():
        name_action(pair[0],pair[0].name.replace('S4::',''))
        name_action(pair[1],pair[1].name.replace('S4::',''))
    scene.timeline_markers.clear()
    for shot in spec['shots']:
        marker=scene.timeline_markers.new(shot[0],frame=shot[2]);marker.camera=pairs[shot[4]][0]
    scene.camera=pairs['A'][0]


def apply(config,baseline):
    spec=config['presentation'];scene=bpy.data.scenes[spec['scene']]
    assert scene.get(p.OWNER) and not scene.get('stage4_r1')
    assert p.check_source(config,baseline)['status']=='PASS'
    source=bpy.data.scenes[spec['source_scene']];p.activate(source);source.frame_set(1)
    bindings={b['motion']['joint']:b for b in k.bindings(config)}
    world={o.name:o.matrix_world.copy() for o in source.objects}
    p.activate(scene);scene.frame_set(1)
    retained=sorted(o.name for o in scene.objects)
    for obj in list(scene.objects):
        assert obj.get(p.OWNER)
        clear_animation(obj)
        if obj.data and obj.data.get(p.OWNER):clear_animation(obj.data)
    for action in list(bpy.data.actions):
        if action.get(p.OWNER) and action.users==0:bpy.data.actions.remove(action)
    # 中立根使用几何包围盒中心，不声称是实机重心。
    points=[world[o.name] @ Vector(v) for o in source.objects if o.type=='MESH' and not o.get('reference_only') for v in o.bound_box]
    center=Vector([(min(v[i] for v in points)+max(v[i] for v in points))/2 for i in range(3)])
    root=p.empty(spec['pose']['root'],bpy.data.collections['S4::STAGE4_HELPERS']);root.location=center
    root['pivot_definition']=spec['pose']['note'];root['center_model_m']=list(center)
    for obj in scene.objects:
        if obj.name.startswith('S4::MODULE::'):
            obj.parent=root;obj.matrix_parent_inverse=Matrix.Translation(-center);obj.matrix_basis=Matrix.Identity(4)
    old_legs=bpy.data.objects['S4::MODULE::LEGS']
    for module in spec['modules']:
        name='S4::MODULE::'+module['id'];ctrl=bpy.data.objects.get(name)
        if ctrl is None:
            ctrl=p.empty(name,bpy.data.collections['S4::STAGE4_ACTIONS']);ctrl.parent=old_legs
            ctrl.matrix_parent_inverse=Matrix.Identity(4);ctrl.matrix_basis=Matrix.Identity(4)
        for name in module['objects']:
            proxy=bpy.data.objects['S4::INSTANCE::'+name]
            if module['id'].startswith('LEG'):
                proxy.parent=ctrl;proxy.matrix_parent_inverse=Matrix.Identity(4);proxy.matrix_basis=world[name]
        # 逐帧采样分段缓入缓出，分量线性插值使子帧也留在安全折线路径上。
        for frame in [1,*range(module['start'],module['end']+1),*range(module['return_start'],module['return_end']+1),990]:
            p.key(ctrl,frame,location_at(module,frame))
        name_action(ctrl,'MODULE::'+module['id'])
        ctrl.animation_data.action['r1_sampled_location']=True
    for frame,degrees in spec['pose']['keys']:
        root.rotation_euler=[math.radians(x) for x in degrees]
        root.keyframe_insert(data_path='rotation_euler',frame=frame)
    name_action(root,'AIRCRAFT_POSE')
    for reuse in spec['motion_reuse']:
        original=bpy.data.objects['JOINT::'+reuse['joint']];pivot=bpy.data.objects['S4::MOTION::'+reuse['joint']]
        pivot.rotation_quaternion=bindings[reuse['joint']]['q0'];anim=pivot.animation_data_create()
        track=anim.nla_tracks.new();track.name='S4::R1::REUSE_ROTOR'
        strip=track.strips.new('S4::R1::ROTOR_30_DPS',reuse['timeline'][0],original.animation_data.action)
        strip.action_slot=original.animation_data.action_slot
        strip.action_frame_start,strip.action_frame_end=reuse['source'];strip.frame_start,strip.frame_end=reuse['timeline']
        # 修改结束帧并不会自动改变NLA实际求值速度，必须显式设置时间缩放。
        strip.scale=(reuse['timeline'][1]-reuse['timeline'][0])/(reuse['source'][1]-reuse['source'][0])
        strip.blend_type='REPLACE';strip.extrapolation='HOLD'
    for joint in spec['surface_motion']['joints']:
        binding=bindings[joint];pivot=bpy.data.objects['S4::MOTION::'+joint];pivot.rotation_mode='QUATERNION'
        for frame in [1,*range(391,481),990]:
            angle=angle_at(spec['surface_motion']['angle_keys'],frame)
            pivot.rotation_quaternion=binding['q0'] @ k.quaternion_delta(binding['axis_local'],angle)
            pivot.keyframe_insert(data_path='rotation_quaternion',frame=frame)
        name_action(pivot,joint+'::SYNC_20_DEG');pivot.animation_data.action['r1_sampled_rotation']=True
    scene.frame_end=990;scene.render.fps=30;scene.frame_preview_end=990;scene.use_preview_range=False
    studio(config,scene);cameras(config,scene);ease_owned()
    scene['stage4_r1']=True;scene['stage4_r1_retained_objects']=json.dumps(retained)
    scene['presentation_config_json']=json.dumps(spec,ensure_ascii=False,sort_keys=True)
    assert p.check_source(config,baseline)['status']=='PASS'
    p.configure_layout(scene);scene.frame_set(1)
    return scene


def validate(config,baseline):
    """保留源回归强度，逐帧验证同步、限位、姿态归零与最终恢复。"""
    spec=config['presentation'];source_result=p.check_source(config,baseline)
    source=bpy.data.scenes[spec['source_scene']];p.activate(source);source.frame_set(1)
    bindings={b['motion']['joint']:b for b in k.bindings(config)}
    scene=bpy.data.scenes[spec['scene']];p.activate(scene);scene.frame_set(1)
    assert scene.get('stage4_r1') and scene.frame_start==1 and scene.frame_end==990
    retained=json.loads(scene['stage4_r1_retained_objects'])
    assert len(retained)==67 and set(retained)<=set(o.name for o in scene.objects)
    assert all(o.get(p.OWNER) for o in scene.objects)
    assert set(bpy.data.objects.keys())==set(baseline['objects'])|set(o.name for o in scene.objects)
    assert all(a.name in {v['name'] for v in baseline['actions'].values()} or a.get(p.OWNER) for a in bpy.data.actions)
    initial={};initial_error=0
    names=[n for m in spec['modules'] for n in m['objects']]
    assert len(names)==27 and len(set(names))==27
    for name in names:
        obj=bpy.data.objects['S4::INSTANCE::'+name];original=bpy.data.objects[name]
        assert obj.data==original.data
        assert [(s.link,s.material) for s in obj.material_slots]==[(s.link,s.material) for s in original.material_slots]
        initial[name]=obj.matrix_world.copy()
        initial_error=max(initial_error,k.matrix_error(obj.matrix_world,original.matrix_world))
    assert initial_error<1e-6,initial_error
    root=bpy.data.objects[spec['pose']['root']]
    assert root.get(p.OWNER) and 'CG' in root['pivot_definition']
    assert [(m.frame,m.camera.name) for m in scene.timeline_markers if m.camera]==[(s[2],'S4::CAMERA_'+s[4]) for s in spec['shots']]
    controllers={m['id']:bpy.data.objects['S4::MODULE::'+m['id']] for m in spec['modules']}
    for ctrl in controllers.values():
        curves=k.fcurves(ctrl)
        assert len(curves)==3 and all(c.data_path=='location' and all(pt.interpolation=='LINEAR' for pt in c.keyframe_points) for c in curves)
    for joint in spec['surface_motion']['joints']:
        curves=k.fcurves(bpy.data.objects['S4::MOTION::'+joint])
        assert len(curves)==4 and all(c.data_path=='rotation_quaternion' and all(pt.interpolation=='LINEAR' for pt in c.keyframe_points) for c in curves)
    max_axis_error=0;sync_error=0;camera_margin=1.;camera_frames=0;max_angle_error=0;relative_error=0;pose_error=0
    rotor=bpy.data.objects['S4::MOTION::rotor_joint'];previous_rotor=None;spin_total=0;spin_steps=[]
    from bpy_extras.object_utils import world_to_camera_view
    for frame in range(1,991):
        scene.frame_set(frame)
        if frame>=120:assert Vector(root.rotation_euler).length<1e-7
        if frame<=120:
            pose_matrix=root.matrix_world @ Matrix.Translation(-Vector(root['center_model_m']))
            for name in names:
                if name=='rotor':continue
                pose_error=max(pose_error,k.matrix_error(bpy.data.objects['S4::INSTANCE::'+name].matrix_world,pose_matrix @ initial[name]))
        if frame<=361:
            q=rotor.rotation_quaternion.normalized()
            if previous_rotor is not None:
                difference=previous_rotor.inverted() @ q
                angle=math.degrees(2*math.atan2(difference.z,difference.w));spin_total+=angle;spin_steps.append(angle*30)
            previous_rotor=q.copy()
        factors={}
        for m in spec['modules']:
            ctrl=controllers[m['id']];delta=Vector(m['delta']);factor=ctrl.location.dot(delta)/delta.length_squared
            factors[m['id']]=factor
            if not m.get('waypoints'):assert -1e-6<=factor<=1+1e-6,(frame,m['id'],factor)
            max_axis_error=max(max_axis_error,(ctrl.location-location_at(m,frame)).length)
            if frame<=m['start'] or frame>=m['return_end']:assert ctrl.location.length<1e-6
            if m['end']<=frame<=m['return_start']:assert (ctrl.location-delta).length<1e-6
            assert Vector(ctrl.rotation_euler).length<1e-7 and (ctrl.scale-Vector((1,1,1))).length<1e-7
        for group in [('LEG1','LEG2','LEG3'),('DUCT1','DUCT2','DUCT3'),tuple('SURFACE'+str(i) for i in range(1,5)),tuple('SERVO'+str(i) for i in range(1,5))]:
            sync_error=max(sync_error,max(factors[n] for n in group)-min(factors[n] for n in group))
        angles=[]
        for joint in spec['surface_motion']['joints']:
            binding=bindings[joint];pivot=bpy.data.objects['S4::MOTION::'+joint]
            assert pivot.animation_data.action.get(p.OWNER) and not pivot.animation_data.nla_tracks
            delta=binding['q0'].inverted() @ pivot.rotation_quaternion.normalized()
            angle=2*math.atan2(Vector((delta.x,delta.y,delta.z)).dot(binding['axis_local']),delta.w)
            assert binding['lower']-1e-8<=angle<=binding['upper']+1e-8,(frame,joint,angle)
            expected=angle_at(spec['surface_motion']['angle_keys'],frame)
            max_angle_error=max(max_angle_error,abs(math.degrees(angle)-expected));angles.append(math.degrees(angle))
        assert max(angles)-min(angles)<1e-4
        if frame<=390 or frame>=480:assert max(abs(v) for v in angles)<1e-4
        if scene.camera.name=='S4::CAMERA_A':
            camera_frames+=1
            for name in names:
                obj=bpy.data.objects['S4::INSTANCE::'+name]
                for corner in obj.bound_box:
                    projected=world_to_camera_view(scene,scene.camera,obj.matrix_world @ Vector(corner))
                    camera_margin=min(camera_margin,projected.x,projected.y,1-projected.x,1-projected.y)
        for m in spec['modules']:
            a=m['objects'][0]
            for b in m['objects'][1:]:
                relative=bpy.data.objects['S4::INSTANCE::'+a].matrix_world.inverted() @ bpy.data.objects['S4::INSTANCE::'+b].matrix_world
                reference=bpy.data.objects[a].matrix_world.inverted() @ bpy.data.objects[b].matrix_world
                relative_error=max(relative_error,k.matrix_error(relative,reference))
    assert max_axis_error<1e-6 and sync_error<1e-6 and relative_error<1e-6
    assert max_angle_error<1e-4,max_angle_error
    assert pose_error<1e-6 and abs(spin_total-360)<1e-3
    assert min(spin_steps)>28 and max(spin_steps)<32,(min(spin_steps),max(spin_steps))
    assert camera_margin>.025,camera_margin
    recovery=max(k.matrix_error(bpy.data.objects['S4::INSTANCE::'+n].matrix_world,initial[n]) for n in names)
    assert recovery<1e-6,recovery
    # 用0.25帧步长复核极值附近的实际四元数求值，不仅检查关键帧。
    subframe_max=0
    for quarter in range(391*4,480*4+1):
        scene.frame_set(quarter//4,subframe=(quarter%4)/4)
        for joint in spec['surface_motion']['joints']:
            binding=bindings[joint];q=binding['q0'].inverted() @ bpy.data.objects['S4::MOTION::'+joint].rotation_quaternion.normalized()
            angle=2*math.atan2(Vector((q.x,q.y,q.z)).dot(binding['axis_local']),q.w)
            subframe_max=max(subframe_max,abs(angle));assert binding['lower']-1e-8<=angle<=binding['upper']+1e-8
    scene.frame_set(811)
    endpoints={m['id']:list(p.centroid(bpy.data.objects['S4::INSTANCE::'+m['objects'][0]])) for m in spec['modules']}
    legs=[Vector(endpoints['LEG'+str(i)]) for i in (1,2,3)]
    leg_gap=min((a-b).length for i,a in enumerate(legs) for b in legs[i+1:]);assert leg_gap>.5,leg_gap
    m=Vector(endpoints['MOTOR']);r=Vector(endpoints['ROTOR'])
    assert m.x>0 and r.x>0 and m.y<0 and r.y<0 and (m-r).length>.08
    battery=battery_validate(config)
    scene.frame_set(1)
    return {'status':'PASS','revision':'4.0-R1','source':source_result,'retained_presentation_objects':len(retained),
            'presentation_objects':len(scene.objects),'global_objects':len(bpy.data.objects),'modules':len(spec['modules']),
            'timeline':[1,990],'fps':30,'duration_s':33,'trajectory_frames_verified':990,
            'initial_world_matrix_max_error':initial_error,'reassembly_world_matrix_max_error':recovery,
            'trajectory_axis_max_error':max_axis_error,'synchronized_modules_factor_max_error':sync_error,
            'surface_angle_max_error_deg':max_angle_error,'surface_subframe_max_abs_radians':subframe_max,
            'surface_limit_radians':.3491,'surface_subframe_samples_per_joint':357,
            'group_relative_matrix_max_error':relative_error,'leg_endpoint_centroid_min_distance_m':leg_gap,
            'main_camera_frames_verified':camera_frames,'main_camera_min_normalized_margin':camera_margin,
            'pose_neutral_before_disassembly':True,'battery':battery,'shots':len(spec['shots']),
            'pose_rigid_matrix_max_error':pose_error,'rotor_actual_total_degrees':spin_total,
            'rotor_actual_speed_range_degrees_per_s':[min(spin_steps),max(spin_steps)],
            'mp4_generated':False}


def battery_validate(config):
    spec=config['presentation'];scene=bpy.data.scenes[spec['scene']]
    obstacle_names=['base_board_flyctrl','panel11','panel12','shelf1','controller2','X-tend','box_up','box_up2','bec-Hobbywing-Platinum']
    p.activate(bpy.data.scenes[spec['source_scene']]);bpy.context.scene.frame_set(1)
    result=geo.cardinal_sweep(bpy.data.objects['battery-4s-10000-2'],[bpy.data.objects[n] for n in obstacle_names])
    assert result['directions']['-Y']['clear_of_new_penetration']
    assert result['directions']['-Y']['swept_intersections']=={}
    assert not result['directions']['+X']['clear_of_new_penetration'] and not result['directions']['-X']['clear_of_new_penetration']
    p.activate(scene);samples=[]
    for frame in [*range(571,616),*range(913,919)]:
        scene.frame_set(frame);battery=bpy.data.objects['S4::INSTANCE::battery-4s-10000-2'];lo,hi=geo.bounds(battery)
        collisions={}
        for name in obstacle_names:
            obj=bpy.data.objects['S4::INSTANCE::'+name];a,b=geo.bounds(obj)
            if any(min(hi[i],b[i])-max(lo[i],a[i])<=1e-6 for i in range(3)):continue
            hits=geo.box_hits(lo,hi,geo.triangles(obj))
            if hits:collisions[name]=len(hits)
        assert not collisions,(frame,collisions)
        samples.append({'frame':frame,'battery_bounds':[lo,hi],'intersections':0})
    result.update(status='PASS',chosen_direction='-Y',chosen_displacement_m=[0,-.38,0],
                  method='轴对齐实心长方体连续扫掠体与周围实际三角网格SAT；并逐动画帧复核',
                  intermediate_frame_samples=samples,
                  note='X-tend包围盒与电池包围盒重叠，但本次精确三角检查没有发现实体穿透；不修正原始关系。')
    return result
