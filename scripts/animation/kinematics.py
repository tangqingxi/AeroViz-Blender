"""配置驱动的关节四元数运动；不导入几何、不重建层级、不猜测轴向。"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import sys
import bpy
from mathutils import Matrix,Quaternion,Vector

WORKSPACE=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(WORKSPACE/'scripts'))
sys.dont_write_bytecode=True
import project_io
import materials


def matrix_error(a,b):
    return max(abs(a[r][c]-b[r][c]) for r in range(4) for c in range(4))


def rotation_only(matrix):
    """只接受正的均匀缩放与纯旋转；非均匀缩放/剪切不能静默近似。"""
    m=matrix.to_3x3()
    sizes=[m.col[i].length for i in range(3)]
    if min(sizes)<1e-10 or m.determinant()<=0 or max(sizes)-min(sizes)>1e-6:
        raise ValueError('旋转轴变换不支持零、负或非均匀缩放')
    r=m.to_quaternion().to_matrix()
    if max(abs(m[i][j]-r[i][j]*sizes[0]) for i in range(3) for j in range(3))>1e-6:
        raise ValueError('旋转轴变换存在剪切')
    return r


def quaternion_delta(axis, angle_deg):
    # 用双精度计算半角后再转 Blender 四元数，避免大角度单精度化造成转速误差。
    half=math.radians(angle_deg)/2
    sine=math.sin(half)
    return Quaternion((math.cos(half),*(sine*x for x in axis)))


def angle_at(motion,frame,animation):
    if motion['kind']=='spin':
        start=motion['start_frame'];end=motion['end_frame']
        return motion.get('initial_angle_deg',0)+motion['rate_deg_per_s']*(min(max(frame,start),end)-start)/animation['fps']
    if motion['kind']!='keyed_angles':
        raise ValueError('未支持的运动类型：'+motion['kind'])
    keys=motion['keys']
    if frame<=keys[0]['frame']:
        return keys[0]['angle_deg']
    for a,b in zip(keys,keys[1:]):
        if frame<=b['frame']:
            t=(frame-a['frame'])/(b['frame']-a['frame'])
            return a['angle_deg']*(1-t)+b['angle_deg']*t
    return keys[-1]['angle_deg']


def bindings(config):
    animation=config['animation']
    root=bpy.data.objects[animation.get('root_object',config['model_name']+'_ROOT')]
    root_rotation=rotation_only(root.matrix_world)
    result=[];seen=set()
    for motion in animation['motions']:
        name='JOINT::'+motion['joint']
        if name in seen:
            raise ValueError('重复关节配置：'+name)
        seen.add(name)
        obj=bpy.data.objects.get(name)
        if obj is None or obj.type!='EMPTY' or obj.get('type') not in ('revolute','continuous'):
            raise ValueError('不是现有关节：'+name)
        if obj.constraints or Vector(obj.delta_rotation_euler).length>1e-8 or abs(obj.delta_rotation_quaternion.w-1)>1e-8:
            raise ValueError('关节有约束或增量姿态，需明确适配：'+name)
        meshes=sorted(o.name for o in obj.children_recursive if o.type=='MESH')
        if not meshes:
            raise ValueError('禁止给无网格子代关节添加动画：'+name)
        if 'expected_meshes' in motion and meshes!=sorted(motion['expected_meshes']):
            raise ValueError('关节子网格与配置不一致：'+name)
        if 'expected_center_m' in motion:
            expected=root.matrix_world @ Vector(motion['expected_center_m'])
            if (obj.matrix_world.translation-expected).length>1e-6:
                raise ValueError('关节中心与配置不一致：'+name)
        axis_model=Vector(obj['axis_model'])
        if axis_model.length<1e-10:
            raise ValueError('关节轴为零：'+name)
        axis_model.normalize()
        if 'expected_axis_model' in motion and (axis_model-Vector(motion['expected_axis_model']).normalized()).length>1e-6:
            raise ValueError('轴方向与配置不一致，禁止自动反向：'+name)
        world_axis=(root_rotation @ axis_model).normalized()
        local_axis=(rotation_only(obj.matrix_world).inverted() @ world_axis).normalized()
        back=(rotation_only(obj.matrix_world) @ local_axis).normalized()
        if back.dot(world_axis)<1-1e-7:
            raise ValueError('轴反向变换不保持正方向：'+name)
        action=obj.animation_data.action if obj.animation_data else None
        if obj.animation_data and (not action or not action.get('aeroviz_owned') or obj.animation_data.drivers or obj.animation_data.nla_tracks):
            raise ValueError('不能覆盖外来动画或驱动：'+name)
        q0=Quaternion(action['base_quaternion']) if action else obj.matrix_basis.to_quaternion()
        base_mode=action.get('base_rotation_mode','QUATERNION') if action else obj.rotation_mode
        base_euler=list(obj.rotation_euler)
        lower=float(obj.get('lower','-inf'));upper=float(obj.get('upper','inf'))
        for frame in range(animation['frame_start'],animation['frame_end']+1):
            angle=math.radians(angle_at(motion,frame,animation))
            if not lower<=angle<=upper:
                raise ValueError(f'{name} 配置角度越界：{angle}，{lower}~{upper}')
        if abs(angle_at(motion,animation['frame_start'],animation))>1e-9:
            raise ValueError('起始帧必须为原始零位：'+name)
        result.append({'object':obj,'motion':motion,'q0':q0,'base_mode':base_mode,'base_euler':base_euler,
                       'axis_local':local_axis,'axis_world':world_axis,'axis_model':axis_model,'center':obj.matrix_world.translation.copy(),
                       'meshes':meshes,'lower':lower,'upper':upper,'axis_back_dot':back.dot(world_axis)})
    # 本版本只支持彼此独立的关节，不默默处理级联运动学。
    controlled={b['object'] for b in result}
    def ancestors(obj):
        parent=obj.parent
        while parent is not None:
            yield parent
            parent=parent.parent
    if any(any(a in controlled for a in ancestors(b['object'])) for b in result):
        raise ValueError('配置关节存在级联父子关系，需单独适配')
    return result


def set_angle(binding,angle):
    obj=binding['object']
    obj.rotation_mode='QUATERNION'
    obj.rotation_quaternion=binding['q0'] @ quaternion_delta(binding['axis_local'],angle)
    bpy.context.view_layer.update()


def fcurves(obj):
    action=obj.animation_data.action
    slot=obj.animation_data.action_slot
    curves=[]
    for layer in action.layers:
        for strip in layer.strips:
            if strip.type=='KEYFRAME':
                bag=strip.channelbag(slot)
                if bag:
                    curves.extend(bag.fcurves)
    return curves


def build(config, prepared=None):
    animation=config['animation'];scene=bpy.context.scene
    if animation['interpolation']!='LINEAR' or animation['fps']<=0:
        raise ValueError('此实现要求正 FPS 与 LINEAR 插值')
    scene.frame_set(animation['frame_start'])
    prepared=prepared or bindings(config)
    scene.render.fps=animation['fps'];scene.render.fps_base=1
    scene.frame_start=animation['frame_start'];scene.frame_end=animation['frame_end']
    scene.sync_mode='NONE'
    for binding in prepared:
        obj=binding['object'];motion=binding['motion']
        if obj.animation_data:
            old=obj.animation_data.action
            obj.animation_data_clear()
            if old.users==0:
                bpy.data.actions.remove(old)
        # 先按角度线性求样，再逐整数帧烘焙；四元数分量的线性插值并非严格角度线性。
        frames=range(scene.frame_start,scene.frame_end+1)
        previous=None
        for frame in frames:
            q=binding['q0'] @ quaternion_delta(binding['axis_local'],angle_at(motion,frame,animation))
            if previous is not None and previous.dot(q)<0:
                q.negate()
            obj.rotation_mode='QUATERNION';obj.rotation_quaternion=q
            obj.keyframe_insert(data_path='rotation_quaternion',frame=frame,group=motion['joint'])
            previous=q.copy()
        action=obj.animation_data.action
        action.name='AeroViz::'+config['model_name']+'::'+motion['joint']
        action['aeroviz_owned']=True
        action['base_quaternion']=list(binding['q0'])
        action['base_rotation_mode']=binding['base_mode']
        action['axis_local']=list(binding['axis_local'])
        for curve in fcurves(obj):
            curve.extrapolation='CONSTANT'
            for key in curve.keyframe_points:
                key.interpolation='LINEAR'
        for key in motion.get('keys',[]):
            if key.get('marker'):
                marker=scene.timeline_markers.get(key['marker']) or scene.timeline_markers.new(key['marker'])
                marker.frame=key['frame']
    scene['aeroviz_animation']=json.dumps({'version':1,'config_sha256':hashlib.sha256(json.dumps(animation,sort_keys=True).encode()).hexdigest()},sort_keys=True)
    scene.frame_set(scene.frame_start)
    bpy.context.view_layer.update()
    return prepared


def base_snapshot():
    """记录结构与材质，不包含网格顶点本体，便于归档与重新验证。"""
    return {'objects':materials.snapshot_objects(),
            'material_signatures':{m.name:m.get('sdf_material_signature') for m in bpy.data.materials},
            'slots':{o.name:[s.material.name if s.material else None for s in o.material_slots] for o in bpy.data.objects if o.type=='MESH'},
            'material_nodes':{m.name:json.dumps([(n.type,[(s.name,str(s.default_value[:]) if hasattr(s.default_value,'__len__') else str(s.default_value)) for s in n.inputs if hasattr(s,'default_value')]) for n in m.node_tree.nodes],sort_keys=True) for m in bpy.data.materials if m.use_nodes}}


def reference_rotation(axis, angle_deg):
    """独立 Rodrigues 参考矩阵，用双精度三角函数避免大角度先转单精度。"""
    x,y,z=axis.normalized();angle=math.radians(angle_deg)
    c=math.cos(angle);s=math.sin(angle);v=1-c
    return Matrix(((c+x*x*v,x*y*v-z*s,x*z*v+y*s,0),
                   (y*x*v+z*s,c+y*y*v,y*z*v-x*s,0),
                   (z*x*v-y*s,z*y*v+x*s,c+z*z*v,0),(0,0,0,1)))


def validate(config,baseline):
    scene=bpy.context.scene;animation=config['animation'];scene.frame_set(animation['frame_start'])
    prepared=bindings(config)
    expected_names=sorted(b['object'].name for b in prepared)
    assert sorted(o.name for o in bpy.data.objects if o.animation_data)==expected_names
    assert len(bpy.data.actions)==len(prepared)
    assert len(bpy.data.objects)==len(baseline['objects'])
    snapshot=base_snapshot()
    for key in ('material_signatures','slots','material_nodes'):
        assert snapshot[key]==baseline[key],key
    for name,old in baseline['objects'].items():
        current=snapshot['objects'][name]
        for key,value in old.items():
            if key=='has_animation':
                assert current[key]==(name in expected_names)
            elif key in ('matrix_world','matrix_basis','matrix_parent_inverse'):
                assert matrix_error(current[key],value)<1e-6,(name,key)
            else:
                assert current[key]==value,(name,key)
    assert scene.render.fps==animation['fps'] and scene.render.fps_base==1
    assert (scene.frame_start,scene.frame_end)==(animation['frame_start'],animation['frame_end'])
    before={n:Matrix(s['matrix_world']) for n,s in baseline['objects'].items()}
    rows=[];previous={};totals={};max_step_error=0.0
    for frame in range(scene.frame_start,scene.frame_end+1):
        scene.frame_set(frame);bpy.context.view_layer.update();depsgraph=bpy.context.evaluated_depsgraph_get()
        expected={name:m.copy() for name,m in before.items()};angles={};centers={};quaternions={}
        for b in prepared:
            obj=b['object'];name=obj.name;motion=b['motion'];angle=angle_at(motion,frame,animation)
            evaluated=obj.evaluated_get(depsgraph)
            center=evaluated.matrix_world.translation
            assert (center-b['center']).length<1e-6,name
            # 独立世界坐标参考：平移到原关节中心，按模型世界轴旋转，再平移回来。
            delta=Matrix.Translation(b['center']) @ reference_rotation(b['axis_world'],angle) @ Matrix.Translation(-b['center'])
            for descendant in (obj,*obj.children_recursive):
                expected[descendant.name]=delta @ before[descendant.name]
            actual_q=evaluated.rotation_quaternion.copy().normalized()
            relative=b['q0'].conjugated() @ actual_q
            measured=math.degrees(2*math.atan2(Vector((relative.x,relative.y,relative.z)).dot(b['axis_local']),relative.w))
            if motion['kind']=='keyed_angles':
                assert abs(measured-angle)<animation['tolerances']['angle_deg'],(frame,name,measured,angle)
            if motion['kind']=='spin':
                if name in previous:
                    qprev=previous[name]
                    assert qprev.dot(actual_q)>0
                    qstep=qprev.conjugated() @ actual_q
                    step=math.degrees(2*math.atan2(Vector((qstep.x,qstep.y,qstep.z)).dot(b['axis_local']),qstep.w))
                    expected_step=angle-angle_at(motion,frame-1,animation)
                    error=abs(step-expected_step);max_step_error=max(max_step_error,error)
                    assert error<animation['tolerances']['angle_deg'],(frame,name,step,error)
                    totals[name]=totals.get(name,0)+step
                previous[name]=actual_q
            angles[name]={'expected_deg':angle,'measured_principal_deg':measured}
            centers[name]=list(center);quaternions[name]=list(actual_q)
        errors={name:matrix_error(bpy.data.objects[name].evaluated_get(depsgraph).matrix_world,m) for name,m in expected.items()}
        assert max(errors.values())<animation['tolerances']['matrix'],(frame,max(errors.items(),key=lambda item:item[1]))
        rows.append({'frame':frame,'angles':angles,'joint_centers_m':centers,'quaternions':quaternions,'max_world_matrix_error':max(errors.values()),'non_target_max_error':max((error for name,error in errors.items() if all(name not in {x.name for x in (b['object'],*b['object'].children_recursive)} for b in prepared)),default=0)})
    channels={}
    for b in prepared:
        curves=fcurves(b['object'])
        assert len(curves)==4 and all(c.data_path=='rotation_quaternion' for c in curves)
        assert all(k.interpolation=='LINEAR' for c in curves for k in c.keyframe_points)
        channels[b['object'].name]={'action':b['object'].animation_data.action.name,'channel_count':len(curves),'keys_per_channel':[len(c.keyframe_points) for c in curves]}
        expected_total=angle_at(b['motion'],scene.frame_end,animation)-angle_at(b['motion'],scene.frame_start,animation)
        if b['motion']['kind']=='spin':
            assert abs(totals[b['object'].name]-expected_total)<animation['tolerances']['angle_deg']
    markers={k['marker']:k['frame'] for m in animation['motions'] for k in m.get('keys',[]) if k.get('marker')}
    assert all(scene.timeline_markers.get(name) and scene.timeline_markers[name].frame==frame for name,frame in markers.items())
    scene.frame_set(scene.frame_start)
    return {'status':'PASS','markers':markers,'frame_count':len(rows),'frames':rows,'rotor_accumulated_deg':totals,'max_increment_error_deg':max_step_error,
            'channels':channels,'object_count':len(bpy.data.objects),'mesh_count':sum(o.type=='MESH' for o in bpy.data.objects),'material_count':len(bpy.data.materials),'animated_objects':expected_names,
            'frame1_preserved':True,'geometry_materials_hierarchy_preserved':True}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--config',required=True)
    parser.add_argument('--expected-sha256',required=True)
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    config=json.loads(project_io.resolve(args.config).read_text(encoding='utf8'));target=project_io.project(config)
    assert hashlib.sha256(target.read_bytes()).hexdigest()==args.expected_sha256
    bpy.ops.wm.open_mainfile(filepath=str(target))
    bpy.context.scene.frame_set(config['animation']['frame_start'])
    baseline=base_snapshot();build(config);validate(config,baseline)
    project_io.save_project(config)
    print('KINEMATICS_SAVED',target.name)


if __name__=='__main__':
    main()
