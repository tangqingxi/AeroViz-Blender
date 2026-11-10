"""在独立后台进程验证关节层级，不保存旋转、不创建动画。

读取当前唯一工程，对每个带网格子代的 revolute 关节做临时矩阵传递检查，
结果写入审计仓库的阶段证据目录。
"""
import argparse
import json
from pathlib import Path
import sys

import bpy
from mathutils import Matrix, Vector

WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE/'scripts'))
sys.dont_write_bytecode = True
import project_io

parser = argparse.ArgumentParser()
parser.add_argument('--config', required=True)
args = parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
config = json.loads(project_io.resolve(args.config).read_text(encoding='utf8'))
project = project_io.project(config)
if not project.is_file():
    raise FileNotFoundError(f'当前工程不存在：{project}')
bpy.ops.wm.open_mainfile(filepath=str(project))

results = []
for pivot in bpy.data.objects:
    if not pivot.name.startswith('JOINT::') or pivot.get('type') != 'revolute':
        continue
    meshes = [o for o in pivot.children_recursive if o.type == 'MESH']
    if not meshes:
        continue
    before = {o.name: o.matrix_world.copy() for o in bpy.data.objects if o.type == 'MESH'}
    original = pivot.matrix_basis.copy()
    center = pivot.matrix_world.translation.copy()
    world = pivot.matrix_world.copy()
    axis_local = world.to_3x3().inverted() @ Vector(pivot['axis_model'])
    rotation = Matrix.Rotation(0.1, 4, axis_local)
    delta = world @ rotation @ world.inverted()
    pivot.matrix_basis = original @ rotation
    bpy.context.view_layer.update()
    assert (pivot.matrix_world.translation-center).length < 1e-6
    names = {o.name for o in meshes}
    max_error = 0
    for name, old in before.items():
        expected = delta @ old if name in names else old
        actual = bpy.data.objects[name].matrix_world
        error = max(abs(actual[r][c]-expected[r][c]) for r in range(4) for c in range(4))
        assert error < 1e-6, (pivot.name, name, error)
        max_error = max(max_error, error)
    pivot.matrix_basis = original
    bpy.context.view_layer.update()
    results.append({'joint':pivot.name, 'meshes':list(names), 'center_m':list(center), 'max_error':max_error})
assert not any(o.animation_data for o in bpy.data.objects)

out = project_io.evidence_dir(config, 'stage-1')
out.mkdir(parents=True, exist_ok=True)
(out/'joint_checks.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf8')
print('JOINT_HIERARCHY_OK', len(results), str(out/'joint_checks.json'))
