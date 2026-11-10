"""只读验证现有关节在装配和爆炸位置的独立旋转，不写入关键帧或工程。"""
import argparse
import json
from pathlib import Path
import sys
import bpy
from mathutils import Matrix,Vector
WORKSPACE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(WORKSPACE/'scripts'));sys.dont_write_bytecode=True
import project_io
from animation import kinematics as k
from animation import exploded_view as ex

parser=argparse.ArgumentParser();parser.add_argument('--config',required=True);parser.add_argument('--out')
args=parser.parse_args(sys.argv[sys.argv.index('--')+1:]);config=json.loads(project_io.resolve(args.config).read_text(encoding='utf8'))
bpy.ops.wm.open_mainfile(filepath=str(project_io.project(config)))
original_actions=ex.actions_snapshot();scene=bpy.context.scene
frames=[config.get('animation',{}).get('frame_start',1)]
if scene.get('aeroviz_exploded'):frames.append(config['exploded_view']['fully_exploded'])
results=[];root=bpy.data.objects[config.get('coordinate_frames',{}).get('root_object',config['model_name']+'_ROOT')]
for frame in frames:
    scene.frame_set(frame)
    for pivot in bpy.data.objects:
        if not pivot.name.startswith('JOINT::') or pivot.get('type')!='revolute':continue
        meshes=[o for o in pivot.children_recursive if o.type=='MESH']
        if not meshes:continue
        before={o.name:o.matrix_world.copy() for o in bpy.data.objects if o.type=='MESH'}
        basis=pivot.matrix_basis.copy();world=pivot.matrix_world.copy();center=world.translation.copy()
        axis_world=k.rotation_only(root.matrix_world) @ Vector(pivot['axis_model'])
        local=k.rotation_only(world).inverted() @ axis_world
        rotation=k.quaternion_delta(local,10).to_matrix().to_4x4()
        pivot.matrix_basis=basis @ rotation;bpy.context.view_layer.update()
        delta=Matrix.Translation(center) @ k.reference_rotation(axis_world,10) @ Matrix.Translation(-center)
        names={o.name for o in meshes};errors={n:k.matrix_error(bpy.data.objects[n].matrix_world,delta@m if n in names else m) for n,m in before.items()}
        assert max(errors.values())<1e-6
        assert (pivot.matrix_world.translation-center).length<1e-6
        assert any(k.matrix_error(bpy.data.objects[n].matrix_world,before[n])>1e-5 for n in names)
        pivot.matrix_basis=basis;bpy.context.view_layer.update()
        assert max(k.matrix_error(bpy.data.objects[n].matrix_world,m) for n,m in before.items())<1e-6
        results.append({'frame':frame,'joint':pivot.name,'meshes':sorted(names),'center_m':list(center),'max_error':max(errors.values()),'status':'PASS'})
scene.frame_set(frames[0]);assert ex.actions_snapshot()==original_actions
out=project_io.resolve(args.out) if args.out else project_io.evidence_dir(config,'stage-3' if scene.get('aeroviz_exploded') else 'stage-2' if scene.get('aeroviz_animation') else 'stage-1')/'independent_joint_checks.json'
out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps({'status':'PASS','checks':results,'actions_unchanged':True},ensure_ascii=False,indent=2),encoding='utf8')
print('JOINT_HIERARCHY_OK',len(results))
