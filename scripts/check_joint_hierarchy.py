"""在独立后台进程验证关节层级，不保存旋转、不创建动画。"""
import json
from pathlib import Path
import bpy
from mathutils import Matrix, Vector

output = Path(bpy.data.filepath).parent
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
        max_error = max(max_error,error)
    pivot.matrix_basis = original
    bpy.context.view_layer.update()
    results.append({'joint':pivot.name, 'meshes':list(names), 'center_m':list(center), 'max_error':max_error})
assert not any(o.animation_data for o in bpy.data.objects)
(output/'reports/joint_checks.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf8')
print('JOINT_HIERARCHY_OK',len(results))
