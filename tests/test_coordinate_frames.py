"""在Blender内只读测试坐标定义、单位基向量、矩阵与场景根变换。"""
import argparse,json,sys
from pathlib import Path
import bpy
WORKSPACE=Path(__file__).resolve().parents[1];sys.path.insert(0,str(WORKSPACE/'scripts'));sys.dont_write_bytecode=True
import project_io,coordinate_frames as cf
parser=argparse.ArgumentParser();parser.add_argument('--config',required=True);parser.add_argument('--out',required=True)
args=parser.parse_args(sys.argv[sys.argv.index('--')+1:]);config=json.loads(project_io.resolve(args.config).read_text(encoding='utf8'))
bpy.ops.wm.open_mainfile(filepath=str(project_io.project(config)))
before={o.name:[list(r) for r in o.matrix_world] for o in bpy.data.objects}
result=cf.verify_scene(config)
try:
    cf.validate_matrix([[1,0,0],[0,-1,0],[0,0,1]])
    raise AssertionError('反射矩阵不能作为右手旋转')
except ValueError:
    result['reflection_rejected']=True
assert before=={o.name:[list(r) for r in o.matrix_world] for o in bpy.data.objects}
result['all_world_matrices_unchanged']=True
project_io.resolve(args.out).write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
print('COORDINATE_TESTS_PASS')
