"""R2定向修订：相机主导、完整动力组件、同步舵面与侧向电池。"""
import json
import math

import bpy
from mathutils import Matrix,Vector

import geometry_checks as geo
import presentation as p
import presentation_r1 as r1
from animation import kinematics as k


def action_name(block,label,sampled=False):
    if block.animation_data and block.animation_data.action:
        a=p.owned(block.animation_data.action);a.name='S4::R2::'+label
        if sampled:a['sampled_location']=True


def center(objects):
    points=[o.matrix_world @ Vector(v) for o in objects for v in o.bound_box]
    return Vector([(min(v[i] for v in points)+max(v[i] for v in points))/2 for i in range(3)])


def focus_objects(detail):
    return [bpy.data.objects['S4::INSTANCE::'+name] for name in detail['objects']]


def studio(config,scene):
    r1.studio(config,scene)
    spec=config['presentation'];scene.world['style']=spec['style']
    mat=bpy.data.objects['S4::GROUND'].material_slots[0].material;mat['style']=spec['style']
    thresholds=[n for n in mat.node_tree.nodes if n.type=='MATH' and n.operation=='LESS_THAN']
    for i,node in enumerate(thresholds):node.inputs[1].default_value=.0028 if i<2 else .0016
    for node in mat.node_tree.nodes:
        if node.type=='MATH' and node.operation=='MULTIPLY' and not node.inputs[1].is_linked:
            value=node.inputs[1].default_value
            if abs(value-.018)<1e-5:node.inputs[1].default_value=.45
            elif abs(value-.028)<1e-5:node.inputs[1].default_value=.85
    mat['grid_world_linewidth_m']=json.dumps({'minor':.0014,'major':.0032})
    scene.world['source_hex_is_srgb']=True
    # R1的柔光对象继续使用，延长开场揭示并提高前下方补光。
    for label,power,size in [('KEY',18,1.20),('FILL',18,1.10),('RIM',19,1.00),('RIM_RIGHT',15,1.00),('REVEAL',10,.9)]:
        obj=bpy.data.objects['S4::LIGHT_'+label];r1.clear_animation(obj.data);obj.data.energy=power;obj.data.size=size
        if label in ('KEY','REVEAL'):
            for frame,factor in ((1,.50),(8,.50),(75,1),(90,1),(990,1)):p.key(obj,frame,energy=power*factor)
            action_name(obj.data,'LIGHT_'+label)
    scene.view_settings.exposure=-.10


def cameras(config,scene):
    spec=config['presentation'];objects=[o for o in scene.objects if o.get('source_object')]
    pairs={name:(bpy.data.objects['S4::CAMERA_'+name],bpy.data.objects['S4::CAMERA_'+name+'::TARGET']) for name in 'ABC'}
    rows=[];target=Vector((0,0,-.045));radius=0
    # 在静止机体外作20度圆弧推进，控制主体保持不动。
    for frame in range(1,91):
        t=r1.smooth((frame-1)/74);theta=math.radians(-55+20*t);height=.02+.30*t
        direction=Vector((math.cos(theta),math.sin(theta),height));scene.frame_set(frame)
        pos,_=r1.fit(scene,pairs['A'][0],direction,target,objects,margin=.82)
        radius=max(radius,(pos-target).length/math.sqrt(1+height*height))
    for frame in range(1,91):
        t=r1.smooth((frame-1)/74);theta=math.radians(-55+20*t);height=.02+.30*t;rad=radius*(1.22-.22*t)
        rows.append((frame,target+Vector((math.cos(theta)*rad,math.sin(theta)*rad,height*rad)),target))
    def fixed(start,end,samples,direction,target):
        distance=0;target=Vector(target)
        for f in samples:
            scene.frame_set(f);position,_=r1.fit(scene,pairs['A'][0],direction,target,objects,margin=.82)
            distance=max(distance,(position-target).length)
        position=target+Vector(direction).normalized()*distance
        rows.extend([(start,position,target),(end,position,target)])
        return position,target
    fixed(91,235,range(91,236,2),(1,-1,.65),(0,0,-.19))
    fixed(361,390,range(361,391),(1,-1,.65),(0,-.05,-.18))
    full_position,full_target=fixed(601,775,range(601,766,2),(1,-1,.65),(0,0,-.17))
    # 完整分解后的圆弧升高/后退，同一终态也包住回装的避让路径。
    final_direction=Vector((math.cos(math.radians(-35)),math.sin(math.radians(-35)),.8))
    end_radius=0
    for frame in range(766,946):
        scene.frame_set(frame);pos,_=r1.fit(scene,pairs['A'][0],final_direction,full_target,objects,margin=.82)
        end_radius=max(end_radius,(pos-full_target).length/math.sqrt(1+.8*.8))
    begin_offset=full_position-full_target;begin_angle=math.atan2(begin_offset.y,begin_offset.x)
    begin_rad=math.hypot(begin_offset.x,begin_offset.y);end_radius=max(end_radius*1.06,begin_rad*1.10)
    for frame in range(776,826):
        t=r1.smooth((frame-776)/38);angle=begin_angle+(math.radians(-35)-begin_angle)*t
        rad=begin_rad+(end_radius-begin_rad)*t;height=begin_offset.z/begin_rad+(.8-begin_offset.z/begin_rad)*t
        rows.append((frame,full_target+Vector((math.cos(angle)*rad,math.sin(angle)*rad,height*rad)),full_target))
    rows.append((945,rows[-1][1],full_target))
    scene.frame_set(1);end_pos,end_target=r1.fit(scene,pairs['A'][0],(.82,-.574,.34),(0,0,-.045),objects,margin=.82)
    rows.extend([(946,end_pos,end_target),(990,end_pos,end_target)])
    p.camera_keys(pairs['A'],rows);action_name(pairs['A'][0],'CAMERA_A',True);action_name(pairs['A'][1],'CAMERA_A_TARGET',True)
    # 功能演示与四象限布局各用一个稳定斜俯视构图，不逐零件切镜头。
    b_rows=[]
    for start,end,target,names in [(391,480,(0,0,-.14),['cs11','cs2','cs33','cs4']),
        (481,580,(0,0,-.34),['cs11','cs2','cs33','cs4']+['servo-KST-X08H-'+str(i) for i in range(1,5)])]:
        focused=[bpy.data.objects['S4::INSTANCE::'+n] for n in names];distance=0;direction=Vector((.85,-.98,.80))
        for frame in range(start,end+1):
            scene.frame_set(frame);pos,focus=r1.fit(scene,pairs['B'][0],direction,target,focused,margin=.80);distance=max(distance,(pos-focus).length)
        position=Vector(target)+direction.normalized()*distance
        if not b_rows:b_rows.append((1,position,target))
        b_rows.extend([(start,position,target),(end,position,target)])
    b_rows.append((990,b_rows[-1][1],b_rows[-1][2]));p.camera_keys(pairs['B'],b_rows)
    action_name(pairs['B'][0],'CAMERA_B');action_name(pairs['B'][1],'CAMERA_B_TARGET')
    for detail in spec['details']:
        focused=focus_objects(detail);module=bpy.data.objects['S4::MODULE::'+detail['module']]
        scene.frame_set(1);neutral_center=center(focused);local_focus=module.matrix_world.inverted() @ neutral_center
        direction=Vector(detail['offset']).normalized();distance=Vector(detail['offset']).length
        for frame in range(detail['start'],detail['end']+1):
            scene.frame_set(frame);focus=module.matrix_world @ local_focus if detail['module']=='POWER' else center(focused)
            pos,_=r1.fit(scene,pairs['C'][0],direction,focus,focused,margin=.80);distance=max(distance,(pos-focus).length)
        for frame in range(detail['start'],detail['end']+1):
            scene.frame_set(frame);focus=module.matrix_world @ local_focus if detail['module']=='POWER' else center(focused)
            t=r1.smooth((frame-detail['start']-4)/max(1,detail['end']-detail['start']-9))
            pos=focus+direction*distance*(1.06-.06*t);p.camera_keys(pairs['C'],[(frame,pos,focus)])
    action_name(pairs['C'][0],'CAMERA_C',True);action_name(pairs['C'][1],'CAMERA_C_TARGET',True)
    scene.timeline_markers.clear()
    for shot in spec['shots']:
        marker=scene.timeline_markers.new(shot[0],frame=shot[2]);marker.camera=pairs[shot[4]][0]
    scene.camera=pairs['A'][0]


def apply(config,baseline):
    spec=config['presentation'];scene=bpy.data.scenes[spec['scene']]
    assert scene.get('stage4_r1') and not scene.get('stage4_r2')
    assert p.check_source(config,baseline)['status']=='PASS'
    p.activate(bpy.data.scenes[spec['source_scene']]);bpy.context.scene.frame_set(1)
    bindings={b['motion']['joint']:b for b in k.bindings(config)}
    p.activate(scene);scene.frame_set(1);retained=sorted(o.name for o in scene.objects)
    for obj in scene.objects:
        r1.clear_animation(obj)
        if obj.data and obj.data.get(p.OWNER):r1.clear_animation(obj.data)
    for action in list(bpy.data.actions):
        if action.get(p.OWNER) and action.users==0:bpy.data.actions.remove(action)
    root=bpy.data.objects[spec['pose']['root']];root.rotation_euler=(0,0,0);root.scale=(1,1,1)
    for obj in scene.objects:
        if obj.name.startswith('S4::MODULE::'):obj.matrix_basis=Matrix.Identity(4)
    power=p.empty('S4::MODULE::POWER',bpy.data.collections['S4::STAGE4_ACTIONS'])
    power.parent=root;power.matrix_parent_inverse=Matrix.Translation(-Vector(root['center_model_m']));power.matrix_basis=Matrix.Identity(4)
    power['source_objects']=json.dumps(['motor-Sunnysky-X2814III-1000KV','rotor'])
    for name in ('MOTOR','ROTOR'):
        obj=bpy.data.objects['S4::MODULE::'+name];obj.parent=power;obj.matrix_parent_inverse=Matrix.Identity(4);obj.matrix_basis=Matrix.Identity(4)
    for m in spec['modules']:
        ctrl=bpy.data.objects['S4::MODULE::'+m['id']]
        for frame in [1,*range(m['start'],m['end']+1),*range(m['return_start'],m['return_end']+1),990]:p.key(ctrl,frame,r1.location_at(m,frame))
        action_name(ctrl,'MODULE::'+m['id'],True)
    for reuse in spec['motion_reuse']:
        src=bpy.data.objects['JOINT::'+reuse['joint']];pivot=bpy.data.objects['S4::MOTION::'+reuse['joint']]
        pivot.rotation_quaternion=bindings[reuse['joint']]['q0'];track=pivot.animation_data_create().nla_tracks.new();track.name='S4::R2::ROTOR_SPIN'
        strip=track.strips.new(track.name,reuse['timeline'][0],src.animation_data.action);strip.action_slot=src.animation_data.action_slot
        strip.action_frame_start,strip.action_frame_end=reuse['source'];strip.frame_start,strip.frame_end=reuse['timeline'];strip.scale=40
        strip.blend_type='REPLACE';strip.extrapolation='HOLD'
    for joint in spec['surface_motion']['joints']:
        binding=bindings[joint];pivot=bpy.data.objects['S4::MOTION::'+joint];pivot.rotation_mode='QUATERNION'
        for frame in [1,*range(391,481),990]:
            pivot.rotation_quaternion=binding['q0'] @ k.quaternion_delta(binding['axis_local'],r1.angle_at(spec['surface_motion']['angle_keys'],frame))
            pivot.keyframe_insert(data_path='rotation_quaternion',frame=frame)
        action_name(pivot,joint+'::SYNC_20');pivot.animation_data.action['sampled_rotation']=True
    scene.frame_end=990;scene.frame_preview_end=990;scene.use_preview_range=False
    studio(config,scene);cameras(config,scene)
    for action in bpy.data.actions:
        if action.get(p.OWNER) and action.name.startswith('S4::R1::'):action.name=action.name.replace('S4::R1::','S4::R2::',1)
    r1.ease_owned();scene['stage4_r2']=True;scene['stage4_r2_retained_objects']=json.dumps(retained)
    scene['presentation_config_json']=json.dumps(spec,ensure_ascii=False,sort_keys=True)
    assert p.check_source(config,baseline)['status']=='PASS';p.configure_layout(scene)
    return scene


def battery_verify(config):
    spec=config['presentation'];scene=bpy.data.scenes[spec['scene']]
    obstacles=['panel11','panel12','base_board_flyctrl','shelf1','controller2','X-tend','box_up','box_up2','bec-Hobbywing-Platinum']
    p.activate(bpy.data.scenes[spec['source_scene']]);bpy.context.scene.frame_set(1)
    result=geo.cardinal_sweep(bpy.data.objects['battery-4s-10000-2'],[bpy.data.objects[n] for n in obstacles])
    assert result['directions']['-Y']['swept_intersections']=={}
    module=next(m for m in spec['modules'] if m['id']=='BATTERY');assert module['delta']==[0,-.38,0]
    p.activate(scene);samples=[]
    for frame in [*range(module['start'],module['end']+1),*range(module['return_start'],module['return_end']+1)]:
        scene.frame_set(frame);obj=bpy.data.objects['S4::INSTANCE::battery-4s-10000-2'];lo,hi=geo.bounds(obj)
        for name in obstacles:
            other=bpy.data.objects['S4::INSTANCE::'+name];a,b=geo.bounds(other)
            if any(min(hi[i],b[i])-max(lo[i],a[i])<=1e-6 for i in range(3)):continue
            assert not geo.box_hits(lo,hi,geo.triangles(other)),(frame,name)
        samples.append({'frame':frame,'bounds':[lo,hi],'intersections':0})
    result.update(status='PASS',actual_vector=[0,-.38,0],samples=samples,method='实际长方体电池连续侧向扫掠SAT及动画逐帧三角检查')
    return result


def validate(config,baseline):
    spec=config['presentation'];source_result=p.check_source(config,baseline)
    r3=spec.get('revision')=='4.0-R3';last=spec['frame_end'] if r3 else 990
    demo_start,demo_end=spec['surface_demo'] if r3 else (391,480)
    source=bpy.data.scenes[spec['source_scene']];p.activate(source);source.frame_set(1)
    bindings={b['motion']['joint']:b for b in k.bindings(config)}
    scene=bpy.data.scenes[spec['scene']];p.activate(scene);scene.frame_set(1)
    assert scene.get('stage4_r3' if r3 else 'stage4_r2') and scene.frame_end==last and scene.render.fps==30
    retained=json.loads(scene['stage4_r3_retained_objects' if r3 else 'stage4_r2_retained_objects']);assert len(retained)==(73 if r3 else 72) and set(retained)<=set(o.name for o in scene.objects)
    assert all(o.get(p.OWNER) for o in scene.objects)
    assert set(bpy.data.objects.keys())==set(baseline['objects'])|set(o.name for o in scene.objects)
    assert all(a.name in {v['name'] for v in baseline['actions'].values()} or a.get(p.OWNER) for a in bpy.data.actions)
    names=[n for m in spec['modules'] for n in m['objects']];assert len(set(names))==len(names)==27
    initial={};error=0
    for name in names:
        obj=bpy.data.objects['S4::INSTANCE::'+name];old=bpy.data.objects[name];initial[name]=obj.matrix_world.copy()
        assert obj.data==old.data and [(s.link,s.material) for s in obj.material_slots]==[(s.link,s.material) for s in old.material_slots]
        error=max(error,k.matrix_error(obj.matrix_world,old.matrix_world))
    assert error<1e-6
    root=bpy.data.objects[spec['pose']['root']];assert not root.animation_data and Vector(root.rotation_euler).length<1e-8
    root_initial=root.matrix_world.copy();power=bpy.data.objects['S4::MODULE::POWER']
    assert bpy.data.objects['S4::MODULE::MOTOR'].parent==power and bpy.data.objects['S4::MODULE::ROTOR'].parent==power
    assert not bpy.data.objects['S4::MODULE::MOTOR'].animation_data and not bpy.data.objects['S4::MODULE::ROTOR'].animation_data
    assert len(spec['details'])==(2 if r3 else 4) and {d['module'] for d in spec['details']}==({'DUCT1','POWER'} if r3 else {'LEG1','DUCT1','POWER','SERVO1'})
    assert [(m.frame,m.camera.name) for m in scene.timeline_markers if m.camera]==[(s[2],'S4::CAMERA_'+s[4]) for s in spec['shots']]
    controllers={m['id']:bpy.data.objects['S4::MODULE::'+m['id']] for m in spec['modules']}
    for ctrl in controllers.values():
        assert all(pt.interpolation=='LINEAR' for curve in k.fcurves(ctrl) for pt in curve.keyframe_points)
    surfaces=[m for m in spec['modules'] if m['id'].startswith('SURFACE')]
    if r3:assert len({(m['start'],m['end'],m['return_start'],m['return_end']) for m in surfaces})==1
    else:assert all(a['end']<b['start'] for a,b in zip(surfaces,surfaces[1:]))
    motor=bpy.data.objects['S4::INSTANCE::motor-Sunnysky-X2814III-1000KV'];rotor=bpy.data.objects['S4::INSTANCE::rotor']
    pivot=bpy.data.objects['S4::MOTION::rotor_joint'];pivot_initial=bpy.data.objects['JOINT::rotor_joint'].matrix_world.copy()
    binding=bindings['rotor_joint'];relative_initial=motor.matrix_world.inverted() @ rotor.matrix_world
    power_error=0;power_translation_error=0;axis_error=0;trajectory_error=0;sync_error=0;angle_error=0;relative_error=0
    camera_margin=1.;focus_margin=1.;opening_body_error=0;arc=[];opening_positions=[];previous_q=None;spin_total=0;speeds=[]
    from bpy_extras.object_utils import world_to_camera_view
    for frame in range(1,last+1):
        scene.frame_set(frame);assert k.matrix_error(root.matrix_world,root_initial)<1e-8
        if frame<=90:
            opening_body_error=max(opening_body_error,max(k.matrix_error(bpy.data.objects['S4::INSTANCE::'+n].matrix_world,initial[n]) for n in names if n!='rotor'))
            cam=bpy.data.objects['S4::CAMERA_A'];target=bpy.data.objects['S4::CAMERA_A::TARGET'];offset=cam.location-target.location
            arc.append(math.degrees(math.atan2(offset.y,offset.x)));opening_positions.append((offset.length,cam.location.z))
        factors={}
        for m in spec['modules']:
            ctrl=controllers[m['id']];delta=Vector(m['delta']);factors[m['id']]=ctrl.location.dot(delta)/delta.length_squared
            trajectory_error=max(trajectory_error,(ctrl.location-r1.location_at(m,frame)).length)
            if frame<=m['start'] or frame>=m['return_end']:assert ctrl.location.length<1e-6
            assert Vector(ctrl.rotation_euler).length<1e-7 and (ctrl.scale-Vector((1,1,1))).length<1e-7
        groups=[('LEG1','LEG2','LEG3'),('DUCT1','DUCT2','DUCT3'),tuple('SERVO'+str(i) for i in range(1,5))]
        if r3:groups.append(tuple('SURFACE'+str(i) for i in range(1,5)))
        for group in groups:
            sync_error=max(sync_error,max(factors[n] for n in group)-min(factors[n] for n in group))
        q=binding['q0'].inverted() @ pivot.rotation_quaternion.normalized()
        expected=power.matrix_world @ pivot_initial @ q.to_matrix().to_4x4() @ pivot_initial.inverted() @ initial['rotor']
        power_error=max(power_error,k.matrix_error(rotor.matrix_world,expected),k.matrix_error(motor.matrix_world,power.matrix_world @ initial['motor-Sunnysky-X2814III-1000KV']))
        relative=motor.matrix_world.inverted() @ rotor.matrix_world
        power_translation_error=max(power_translation_error,(relative.translation-relative_initial.translation).length)
        world_axis=(pivot.matrix_world.to_3x3() @ binding['axis_local']).normalized()
        axis_error=max(axis_error,(world_axis-binding['axis_world']).length)
        if frame<=361:
            current=pivot.rotation_quaternion.normalized()
            if previous_q is not None:
                dq=previous_q.inverted() @ current;step=math.degrees(2*math.atan2(dq.z,dq.w));spin_total+=step;speeds.append(step*30)
            previous_q=current.copy()
        angles=[]
        for joint in spec['surface_motion']['joints']:
            b=bindings[joint];obj=bpy.data.objects['S4::MOTION::'+joint];delta=b['q0'].inverted() @ obj.rotation_quaternion.normalized()
            theta=2*math.atan2(Vector((delta.x,delta.y,delta.z)).dot(b['axis_local']),delta.w)
            assert b['lower']-1e-8<=theta<=b['upper']+1e-8
            degrees=math.degrees(theta);angles.append(degrees);angle_error=max(angle_error,abs(degrees-r1.angle_at(spec['surface_motion']['angle_keys'],frame)))
        assert max(angles)-min(angles)<1e-4
        if scene.camera.name=='S4::CAMERA_A':focused=names
        elif scene.camera.name=='S4::CAMERA_B':focused=[n for m in spec['modules'] if m['id'].startswith(('SURFACE','SERVO')) for n in m['objects']]
        else:focused=next(d['objects'] for d in spec['details'] if d['start']<=frame<=d['end'])
        for name in focused:
            obj=bpy.data.objects['S4::INSTANCE::'+name]
            for corner in obj.bound_box:
                point=world_to_camera_view(scene,scene.camera,obj.matrix_world @ Vector(corner));margin=min(point.x,point.y,1-point.x,1-point.y)
                if scene.camera.name=='S4::CAMERA_A':camera_margin=min(camera_margin,margin)
                else:focus_margin=min(focus_margin,margin)
                assert margin>.015,(frame,scene.camera.name,name,margin)
        for m in spec['modules']:
            if m['id']=='POWER':continue
            a=m['objects'][0]
            for b in m['objects'][1:]:
                actual=bpy.data.objects['S4::INSTANCE::'+a].matrix_world.inverted() @ bpy.data.objects['S4::INSTANCE::'+b].matrix_world
                expected=initial[a].inverted() @ initial[b];relative_error=max(relative_error,k.matrix_error(actual,expected))
    assert max(power_error,power_translation_error,axis_error,trajectory_error,sync_error,relative_error,opening_body_error)<1e-6
    assert angle_error<1e-4 and abs(spin_total-360)<1e-3 and min(speeds)>28 and max(speeds)<32
    assert 15<=max(arc)-min(arc)<=25 and opening_positions[0][0]>opening_positions[-1][0] and opening_positions[-1][1]>opening_positions[0][1]
    recovery=max(k.matrix_error(bpy.data.objects['S4::INSTANCE::'+n].matrix_world,initial[n]) for n in names);assert recovery<1e-6
    scene.frame_set(spec['exploded_hold'][0] if r3 else 800);legs=[p.centroid(bpy.data.objects['S4::INSTANCE::tail-'+str(i)]) for i in (1,2,3)]
    leg_gap=min((a-b).length for i,a in enumerate(legs) for b in legs[i+1:]);assert leg_gap>.80
    # 分量线性插值与0.25帧实际求值共同约束四个舵面的限位。
    submax=0
    for quarter in range(demo_start*4,demo_end*4+1):
        scene.frame_set(quarter//4,subframe=quarter%4/4)
        for joint in spec['surface_motion']['joints']:
            b=bindings[joint];obj=bpy.data.objects['S4::MOTION::'+joint]
            assert all(pt.interpolation=='LINEAR' for curve in k.fcurves(obj) for pt in curve.keyframe_points)
            dq=b['q0'].inverted() @ obj.rotation_quaternion.normalized();theta=2*math.atan2(Vector((dq.x,dq.y,dq.z)).dot(b['axis_local']),dq.w)
            assert b['lower']-1e-8<=theta<=b['upper']+1e-8;submax=max(submax,abs(theta))
    battery=battery_verify(config);scene.frame_set(1)
    return {'status':'PASS','revision':spec['revision'],'source':source_result,'source_scene_objects':117,('retained_r2_objects' if r3 else 'retained_r1_objects'):len(retained),
            'presentation_objects':len(scene.objects),'global_objects':len(bpy.data.objects),'modules':len(spec['modules']),
            'frames':[1,last],'fps':30,'duration_s':last/30,'initial_matrix_error':error,'reassembly_matrix_error':recovery,
            'body_opening_matrix_error':opening_body_error,'aircraft_pose_root_disabled':True,'camera_intro_arc_degrees':max(arc)-min(arc),
            'power_installation_matrix_error':power_error,'power_relative_translation_error':power_translation_error,'rotor_axis_error':axis_error,
            'rotor_total_degrees':spin_total,'rotor_speed_range_degrees_per_s':[min(speeds),max(speeds)],
            'surface_angle_error_degrees':angle_error,'surface_subframe_max_radians':submax,'surface_limit_radians':.3491,
            'synchronized_group_factor_error':sync_error,'trajectory_error':trajectory_error,'group_relative_matrix_error':relative_error,
            'leg_centroid_min_distance_m':leg_gap,'main_camera_min_margin':camera_margin,'focused_parts_min_margin':focus_margin,
            'battery':battery,'shot_count':len(spec['shots']),'detail_count':len(spec['details']),'mp4_generated':False}
