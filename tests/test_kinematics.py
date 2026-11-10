"""独立关节试验及真实依赖图逐帧验证；测试字节仅放 .work/stage-2。"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import sys
import bpy
from mathutils import Matrix,Vector,Quaternion

WORKSPACE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(WORKSPACE));sys.path.insert(0,str(WORKSPACE/'scripts'))
sys.dont_write_bytecode=True
import project_io
from animation import kinematics as engine
from adapters import import_sdf


def write(path,value):
    Path(path).write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf8')


def independent(config):
    data=import_sdf.read(config,project_io.input_root(config))
    sdf_joints={j['name']:j for j in data['joints']}
    prepared=engine.bindings(config)
    before={o.name:o.matrix_world.copy() for o in bpy.data.objects}
    snapshot=engine.base_snapshot();results=[]
    root=bpy.data.objects[config['animation']['root_object']]
    for binding in prepared:
        obj=binding['object'];motion=binding['motion'];source=sdf_joints[motion['joint']]
        source_axis=Vector(source['axis_model']).normalized()
        assert (source_axis-binding['axis_model']).length<1e-6
        assert (root.matrix_world @ source['matrix'].translation-binding['center']).length<1e-6
        assert float(source['lower'])==binding['lower'] and float(source['upper'])==binding['upper']
        descendants={o.name for o in obj.children_recursive}|{obj.name}
        cases=[]
        for angle in motion['test_angles_deg']:
            engine.set_angle(binding,angle)
            depsgraph=bpy.context.evaluated_depsgraph_get()
            delta=Matrix.Translation(binding['center']) @ Matrix.Rotation(math.radians(angle),4,binding['axis_world']) @ Matrix.Translation(-binding['center'])
            actual={o.name:o.evaluated_get(depsgraph).matrix_world.copy() for o in bpy.data.objects}
            errors={name:engine.matrix_error(actual[name],delta@matrix if name in descendants else matrix) for name,matrix in before.items()}
            assert max(errors.values())<1e-6,(obj.name,angle,max(errors.values()))
            assert (actual[obj.name].translation-binding['center']).length<1e-6
            changed=[name for name in binding['meshes'] if engine.matrix_error(actual[name],before[name])>1e-5]
            assert bool(changed)==(angle!=0)
            cases.append({'angle_deg':angle,'changed_target_meshes':changed,'joint_center_m':list(actual[obj.name].translation),
                          'joint_local_quaternion':list(obj.rotation_quaternion),'max_expected_matrix_error':max(errors.values()),
                          'non_target_max_error':max((error for name,error in errors.items() if name not in descendants),default=0),
                          'mesh_world_matrices':{o.name:[list(r) for r in actual[o.name]] for o in bpy.data.objects if o.type=='MESH'}})
        engine.set_angle(binding,0)
        obj.rotation_mode=binding['base_mode'];obj.rotation_euler=binding['base_euler']
        bpy.context.view_layer.update()
        assert max(engine.matrix_error(o.matrix_world,before[o.name]) for o in bpy.data.objects)<1e-6
        assert engine.base_snapshot()==snapshot
        results.append({'joint':obj.name,'status':'PASS','sdf_matches_saved_properties':True,'axis_model':list(binding['axis_model']),
                        'axis_world':list(binding['axis_world']),'axis_local':list(binding['axis_local']),'axis_back_signed_dot':binding['axis_back_dot'],
                        'center_m':list(binding['center']),'sdf_limits_rad':[binding['lower'],binding['upper']],
                        'meshes':binding['meshes'],'cases':cases,'zero_restored':True})
    # 不创建场景对象的非单位初始姿态数学用例，验证右乘和正轴没有被单位姿态偶然掩盖。
    root_rotation=Matrix.Rotation(math.pi/2,4,'Z')
    joint_rotation=Matrix.Rotation(math.pi/2,4,'Y')
    world_axis=engine.rotation_only(root_rotation) @ Vector((1,0,0))
    local=engine.rotation_only(joint_rotation).inverted() @ world_axis
    q0=joint_rotation.to_quaternion()
    actual=(q0 @ engine.quaternion_delta(local,30)).to_matrix().to_4x4()
    expected=Matrix.Rotation(math.radians(30),4,world_axis) @ joint_rotation
    assert engine.matrix_error(actual,expected)<1e-6
    try:
        engine.rotation_only(Matrix.Diagonal((1,2,1,1)))
        raise AssertionError('必须拒绝非均匀缩放')
    except ValueError:
        pass
    return {'status':'PASS','joints':results,'nonidentity_quaternion_and_root_axis_test':'PASS','nonuniform_scale_rejected':True}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--config',required=True)
    parser.add_argument('--phase',choices=['prepare','apply','verify'],required=True)
    parser.add_argument('--expected-sha256')
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    config=json.loads(project_io.resolve(args.config).read_text(encoding='utf8'))
    target=project_io.project(config);work=WORKSPACE/'.work/stage-2'
    if args.expected_sha256:
        assert hashlib.sha256(target.read_bytes()).hexdigest()==args.expected_sha256
    bpy.ops.wm.open_mainfile(filepath=str(target));bpy.context.scene.frame_set(config['animation']['frame_start'])
    if args.phase=='prepare':
        assert target.is_relative_to(work)
        baseline=engine.base_snapshot();write(work/'structure_baseline.json',baseline)
        standalone=independent(config);write(work/'independent_motion.json',standalone)
        engine.build(config)
        result=engine.validate(config,baseline)
        write(work/'combined_animation.json',result)
        write(work/'rotor_continuity.json',{'status':'PASS','accumulated_deg':result['rotor_accumulated_deg'],'max_increment_error_deg':result['max_increment_error_deg'],'frame_count':result['frame_count'],'samples':[r for r in result['frames'] if r['frame'] in (1,31,61,91,121)]})
        project_io.save_project(config)
        write(work/'test_approval.json',{'status':'PASS','baseline_sha256':hashlib.sha256((work/'rollback'/target.name).read_bytes()).hexdigest(),'animation':config['animation']})
    else:
        baseline=json.loads((work/'structure_baseline.json').read_text(encoding='utf8'))
        if args.phase=='apply':
            assert args.expected_sha256,'正式更新必须指定原工程哈希'
            approval=json.loads((work/'test_approval.json').read_text(encoding='utf8'))
            assert approval['status']=='PASS' and approval['animation']==config['animation']
            assert engine.base_snapshot()==baseline
            engine.build(config)
        result=engine.validate(config,baseline)
        write(work/(args.phase+'_animation.json'),result)
        if args.phase=='apply':
            project_io.save_project(config)
        else:
            write(work/'structure_comparison.json',{'status':'PASS','object_total':result['object_count'],'mesh_count':result['mesh_count'],'material_count':result['material_count'],'frame1_preserved':True,'geometry_materials_hierarchy_preserved':True,'animated_objects':result['animated_objects']})
    print('KINEMATICS_'+args.phase.upper()+'_PASS',flush=True)


if __name__=='__main__':
    main()
