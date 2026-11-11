"""复用R2展示层，精简特写并同步四舵面退出，不改原装配。"""
import hashlib
import json
import math

import bpy
from mathutils import Vector

import presentation as p
import presentation_r1 as r1
import presentation_r2 as r2
from animation import kinematics as k


def appearance_state(scene):
    """锁定R2摄影棚和主灯，特写跟随灯仅允许按新镜头时段触发。"""
    scene.frame_set(1)
    def tree_state(tree):
        return {'nodes':[(n.name,n.type,getattr(n,'operation',None),getattr(n,'blend_type',None),
                    [(s.name,list(s.default_value) if hasattr(s.default_value,'__len__') else s.default_value)
                     for s in n.inputs if hasattr(s,'default_value')]) for n in tree.nodes],
                'links':[(l.from_node.name,l.from_socket.name,l.to_node.name,l.to_socket.name) for l in tree.links]}
    lights={}
    for obj in scene.objects:
        if obj.type!='LIGHT':continue
        lights[obj.name]={'matrix_basis':[list(row) for row in obj.matrix_basis],'parent':obj.parent.name if obj.parent else None,'type':obj.data.type,
                         'energy':None if obj.name=='S4::LIGHT_DETAIL' else obj.data.energy,'color':list(obj.data.color),'size':obj.data.size,
                         'curves':[(curve.data_path,curve.array_index,curve.extrapolation,
                            [(list(pt.co),list(pt.handle_left),list(pt.handle_right),pt.interpolation,pt.handle_left_type,pt.handle_right_type) for pt in curve.keyframe_points])
                                   for curve in (k.fcurves(obj.data) if obj.name!='S4::LIGHT_DETAIL' and obj.data.animation_data and obj.data.animation_data.action else [])]}
    ground=bpy.data.objects['S4::GROUND']
    state={'lights':lights,'world':tree_state(scene.world.node_tree),'ground':tree_state(ground.material_slots[0].material.node_tree),
           'ground_matrix':[list(row) for row in ground.matrix_world],
           'color':[scene.view_settings.view_transform,scene.view_settings.look,scene.view_settings.exposure,scene.view_settings.gamma]}
    return state


def appearance_signature(scene):
    return hashlib.sha256(json.dumps(appearance_state(scene),sort_keys=True).encode()).hexdigest()


def cameras(config,scene,intro):
    spec=config['presentation'];end=spec['frame_end'];objects=[o for o in scene.objects if o.get('source_object')]
    pairs={name:(bpy.data.objects['S4::CAMERA_'+name],bpy.data.objects['S4::CAMERA_'+name+'::TARGET']) for name in 'ABC'}
    rows=[(row['frame'],Vector(row['camera']),Vector(row['target'])) for row in intro]
    def fixed(start,stop,direction,target):
        distance=0;target=Vector(target)
        for frame in range(start,stop+1):
            scene.frame_set(frame);position,_=r1.fit(scene,pairs['A'][0],direction,target,objects,margin=.82)
            distance=max(distance,(position-target).length)
        position=target+Vector(direction).normalized()*distance
        rows.extend([(start,position,target),(stop,position,target)])
        return position,target
    fixed(91,200,(1,-1,.65),(0,0,-.19))
    fixed(306,335,(1,-1,.65),(0,-.05,-.18))
    position,target=fixed(506,700,(1,-1,.65),(0,0,-.17))
    final_direction=Vector((math.cos(math.radians(-35)),math.sin(math.radians(-35)),.8));radius=0
    for frame in range(spec['exploded_hold'][0],spec['reassembly_range'][1]+1):
        scene.frame_set(frame);pos,_=r1.fit(scene,pairs['A'][0],final_direction,target,objects,margin=.82)
        radius=max(radius,(pos-target).length/math.sqrt(1+.8*.8))
    offset=position-target;angle0=math.atan2(offset.y,offset.x);radius0=math.hypot(offset.x,offset.y)
    radius=max(radius*1.06,radius0*1.10)
    for frame in range(701,751):
        t=r1.smooth((frame-701)/38);angle=angle0+(math.radians(-35)-angle0)*t
        rad=radius0+(radius-radius0)*t;height=offset.z/radius0+(.8-offset.z/radius0)*t
        rows.append((frame,target+Vector((math.cos(angle)*rad,math.sin(angle)*rad,height*rad)),target))
    rows.append((870,rows[-1][1],target))
    scene.frame_set(1);last,focus=r1.fit(scene,pairs['A'][0],(.82,-.574,.34),(0,0,-.045),objects,margin=.82)
    rows.extend([(871,last,focus),(end,last,focus)]);p.camera_keys(pairs['A'],rows)
    r2.action_name(pairs['A'][0],'CAMERA_A',True);r2.action_name(pairs['A'][1],'CAMERA_A_TARGET',True)

    # 沿用R2偏转近景和退出全景，两段各自固定，退出时不切单件或环绕。
    b_rows=[];direction=Vector((.85,-.98,.80))
    for start,stop,target,prefixes in [(336,425,(0,0,-.14),('SURFACE',)),(426,505,(0,0,-.34),('SURFACE','SERVO'))]:
        focused=[bpy.data.objects['S4::INSTANCE::'+name] for m in spec['modules'] if m['id'].startswith(prefixes) for name in m['objects']]
        target=Vector(target);distance=0
        for frame in range(start,stop+1):
            scene.frame_set(frame);pos,_=r1.fit(scene,pairs['B'][0],direction,target,focused,margin=.80);distance=max(distance,(pos-target).length)
        position=target+direction.normalized()*distance
        if not b_rows:b_rows.append((1,position,target))
        b_rows.extend([(start,position,target),(stop,position,target)])
    b_rows.append((end,position,target));p.camera_keys(pairs['B'],b_rows)
    r2.action_name(pairs['B'][0],'CAMERA_B');r2.action_name(pairs['B'][1],'CAMERA_B_TARGET')
    for detail in spec['details']:
        focused=r2.focus_objects(detail);module=bpy.data.objects['S4::MODULE::'+detail['module']]
        scene.frame_set(1);local_focus=module.matrix_world.inverted() @ r2.center(focused)
        direction=Vector(detail['offset']).normalized();distance=Vector(detail['offset']).length
        for frame in range(detail['start'],detail['end']+1):
            scene.frame_set(frame);focus=module.matrix_world @ local_focus if detail['module']=='POWER' else r2.center(focused)
            pos,_=r1.fit(scene,pairs['C'][0],direction,focus,focused,margin=.80);distance=max(distance,(pos-focus).length)
        for frame in range(detail['start'],detail['end']+1):
            scene.frame_set(frame);focus=module.matrix_world @ local_focus if detail['module']=='POWER' else r2.center(focused)
            t=r1.smooth((frame-detail['start']-4)/max(1,detail['end']-detail['start']-9))
            p.camera_keys(pairs['C'],[(frame,focus+direction*distance*(1.06-.06*t),focus)])
    for name in 'ABC':
        for obj in pairs[name]:
            r2.action_name(obj,obj.name.removeprefix('S4::'),name in ('A','C'))
            if obj.animation_data.action.name.startswith('S4::R2::'):obj.animation_data.action.name=obj.animation_data.action.name.replace('S4::R2::','S4::R3::',1)
    scene.timeline_markers.clear()
    for shot in spec['shots']:
        marker=scene.timeline_markers.new(shot[0],frame=shot[2]);marker.camera=pairs[shot[4]][0]
    scene.camera=pairs['A'][0]


def apply(config,baseline):
    spec=config['presentation'];scene=bpy.data.scenes[spec['scene']]
    assert scene.get('stage4_r2') and not scene.get('stage4_r3')
    assert p.check_source(config,baseline)['status']=='PASS';p.activate(scene)
    previous=json.loads(scene['presentation_config_json']);frozen=appearance_signature(scene);retained=sorted(o.name for o in scene.objects)
    intro=[]
    for frame in range(1,91):
        scene.frame_set(frame);intro.append({'frame':frame,'camera':list(bpy.data.objects['S4::CAMERA_A'].location),'target':list(bpy.data.objects['S4::CAMERA_A::TARGET'].location)})
    for obj in scene.objects:
        if obj.name.startswith(('S4::MODULE::','S4::MOTION::','S4::CAMERA_')):r1.clear_animation(obj)
    for action in list(bpy.data.actions):
        if action.get(p.OWNER) and action.users==0:bpy.data.actions.remove(action)
    for m in spec['modules']:
        obj=bpy.data.objects['S4::MODULE::'+m['id']]
        for frame in [1,*range(m['start'],m['end']+1),*range(m['return_start'],m['return_end']+1),spec['frame_end']]:p.key(obj,frame,r1.location_at(m,frame))
        r2.action_name(obj,'MODULE::'+m['id'],True);obj.animation_data.action.name=obj.animation_data.action.name.replace('S4::R2::','S4::R3::',1)
    source=bpy.data.scenes[spec['source_scene']];p.activate(source);source.frame_set(1);bindings={b['motion']['joint']:b for b in k.bindings(config)}
    p.activate(scene)
    for reuse in spec['motion_reuse']:
        src=bpy.data.objects['JOINT::'+reuse['joint']];pivot=bpy.data.objects['S4::MOTION::'+reuse['joint']]
        pivot.rotation_quaternion=bindings[reuse['joint']]['q0'];track=pivot.animation_data_create().nla_tracks.new();track.name='S4::R3::ROTOR_SPIN'
        strip=track.strips.new(track.name,reuse['timeline'][0],src.animation_data.action);strip.action_slot=src.animation_data.action_slot
        strip.action_frame_start,strip.action_frame_end=reuse['source'];strip.frame_start,strip.frame_end=reuse['timeline'];strip.scale=40;strip.blend_type='REPLACE';strip.extrapolation='HOLD'
    for joint in spec['surface_motion']['joints']:
        binding=bindings[joint];obj=bpy.data.objects['S4::MOTION::'+joint];obj.rotation_mode='QUATERNION'
        for frame in [1,*range(spec['surface_demo'][0],spec['surface_demo'][1]+1),spec['frame_end']]:
            obj.rotation_quaternion=binding['q0'] @ k.quaternion_delta(binding['axis_local'],r1.angle_at(spec['surface_motion']['angle_keys'],frame));obj.keyframe_insert(data_path='rotation_quaternion',frame=frame)
        r2.action_name(obj,joint+'::SYNC_20');obj.animation_data.action.name=obj.animation_data.action.name.replace('S4::R2::','S4::R3::',1);obj.animation_data.action['sampled_rotation']=True
    scene.frame_end=spec['frame_end'];scene.frame_preview_end=spec['frame_end'];scene.use_preview_range=False
    detail=bpy.data.objects['S4::LIGHT_DETAIL'];r1.clear_animation(detail.data)
    cue_frames={1,spec['frame_end']}
    for d in spec['details']:cue_frames.update((d['start']-1,d['start'],d['end'],d['end']+1))
    for frame in sorted(cue_frames):p.key(detail,frame,energy=6 if any(d['start']<=frame<=d['end'] for d in spec['details']) else 0)
    r2.action_name(detail.data,'DETAIL_LIGHT');detail.data.animation_data.action.name='S4::R3::DETAIL_LIGHT'
    cameras(config,scene,intro)
    # 只调整本轮新建Action插值，保留主灯的原R2曲线和句柄。
    for action in bpy.data.actions:
        if action.name.startswith('S4::R3::'):
            sampled=action.get('sampled_rotation') or action.get('sampled_location') or action.name.endswith('DETAIL_LIGHT')
            for layer in action.layers:
                for strip in layer.strips:
                    for bag in strip.channelbags:
                        for curve in bag.fcurves:
                            for point in curve.keyframe_points:
                                point.interpolation='LINEAR' if sampled else 'BEZIER';point.handle_left_type=point.handle_right_type='AUTO_CLAMPED'
    scene['stage4_r3']=True;scene['stage4_r3_retained_objects']=json.dumps(retained)
    scene['stage4_r3_preserved_json']=json.dumps({'appearance':frozen,'intro':intro,'legs':[m for m in previous['modules'] if m['id'].startswith('LEG')]})
    scene['presentation_config_json']=json.dumps(spec,ensure_ascii=False,sort_keys=True)
    assert appearance_signature(scene)==frozen
    assert p.check_source(config,baseline)['status']=='PASS';p.configure_layout(scene)


def validate(config,baseline):
    result=r2.validate(config,baseline);spec=config['presentation'];scene=bpy.data.scenes[spec['scene']]
    preserved=json.loads(scene['stage4_r3_preserved_json']);assert appearance_signature(scene)==preserved['appearance']
    intro_error=0;leg_error=0;b_error=0
    for row in preserved['intro']:
        scene.frame_set(row['frame'])
        intro_error=max(intro_error,(bpy.data.objects['S4::CAMERA_A'].location-Vector(row['camera'])).length,(bpy.data.objects['S4::CAMERA_A::TARGET'].location-Vector(row['target'])).length)
    for frame in range(1,146):
        scene.frame_set(frame)
        for m in preserved['legs']:leg_error=max(leg_error,(bpy.data.objects['S4::MODULE::'+m['id']].location-r1.location_at(m,frame)).length)
    for start,stop in [(336,425),(426,505)]:
        scene.frame_set(start);b_initial=bpy.data.objects['S4::CAMERA_B'].matrix_world.copy()
        for frame in range(start,stop+1):
            scene.frame_set(frame);assert scene.camera.name=='S4::CAMERA_B';b_error=max(b_error,k.matrix_error(bpy.data.objects['S4::CAMERA_B'].matrix_world,b_initial))
    for frame in range(1,spec['frame_end']+1):
        scene.frame_set(frame);energy=6 if any(d['start']<=frame<=d['end'] for d in spec['details']) else 0
        assert abs(bpy.data.objects['S4::LIGHT_DETAIL'].data.energy-energy)<1e-6
    assert max(intro_error,leg_error,b_error)<1e-7
    surfaces=[m for m in spec['modules'] if m['id'].startswith('SURFACE')]
    assert len({(m['start'],m['end'],m['return_start'],m['return_end']) for m in surfaces})==1
    assert all(m['start']>spec['surface_demo'][1] for m in surfaces)
    assert all(not m.get('waypoints') and not m.get('return_waypoints') for m in surfaces)
    assert spec['frame_end']==900 and len(spec['shots'])==10
    scene.frame_set(1)
    result.update(appearance_preserved_from_r2=True,intro_preservation_error=intro_error,leg_motion_preservation_error=leg_error,control_camera_matrix_error=b_error,surface_translation_synchronized=True,surface_return_synchronized=True)
    return result
