"""在实际 Blender 图形进程内验证重新打开结果并保存窗口截图。"""
import json
from pathlib import Path
import bpy
from mathutils import Vector

WORKSPACE = Path(__file__).resolve().parents[1]
OUTPUT = Path(bpy.data.filepath).parent
REPORTS = OUTPUT/'reports'
RESULT = json.loads((REPORTS/'validation.json').read_text(encoding='utf8'))
QUEUE = ['isometric', 'front', 'top', 'side']
STATE = {'index': 0, 'capture': False, 'checks': {}}

def verify_loaded():
    if bpy.app.background:
        raise RuntimeError('必须在图形进程执行，后台不能作为截图验收')
    objects = [o for o in bpy.data.objects if o.type == 'MESH']
    assert len(objects) == RESULT['imported_count']
    checks = []
    for record in RESULT['records']:
        obj = bpy.data.objects[record['object']]
        error = max(abs(obj.matrix_world[r][c]-record['world_matrix'][r][c]) for r in range(4) for c in range(4))
        assert error < 1e-6, obj.name
        raw = RESULT['inventory'][record['file']]
        # 本次数据采用米及单位比例，检查导入器没有交换坐标轴或重新居中。
        if all(abs(record['world_matrix'][r][c]-(1 if r==c else 0)) < 1e-6 for r in range(4) for c in range(4)):
            actual_min = [min(v.co[i] for v in obj.data.vertices) for i in range(3)]
            actual_max = [max(v.co[i] for v in obj.data.vertices) for i in range(3)]
            for a,b in zip(actual_min+actual_max,raw['min']+raw['max']):
                assert abs(a-b) < 1e-6, obj.name
        checks.append({'object': obj.name, 'world_matrix_error': error})
    return {'background': bpy.app.background, 'filepath': bpy.data.filepath, 'mesh_count': len(objects), 'objects': checks,
            'joints': [{'name': o.name, 'center': list(o.matrix_world.translation), 'axis_model': list(o['axis_model'])} for o in bpy.data.objects if o.name.startswith('JOINT::')],
            'status': '实际图形进程重新打开，数据检查通过；窗口截图待人工/代理视觉检查'}

def step():
    try:
        if not STATE['checks']:
            STATE['checks'] = verify_loaded()
        name = QUEUE[STATE['index']]
        if not STATE['capture']:
            cam = bpy.data.objects['VIEW::'+name]
            for area in bpy.context.screen.areas:
                if area.type == 'VIEW_3D':
                    area.spaces.active.region_3d.view_rotation = cam.rotation_euler.to_quaternion()
                    area.spaces.active.region_3d.view_perspective = 'ORTHO'
                    area.tag_redraw()
            STATE['capture'] = True
            return 2.0
        bpy.ops.screen.screenshot(filepath=str(OUTPUT/'preview'/('gui_'+name+'.png')))
        STATE['index'] += 1
        STATE['capture'] = False
        if STATE['index'] < len(QUEUE):
            return 0.5
        STATE['checks']['screenshots'] = ['preview/gui_'+n+'.png' for n in QUEUE]
        (REPORTS/'gui_validation.json').write_text(json.dumps(STATE['checks'],ensure_ascii=False,indent=2),encoding='utf8')
        # 恢复等轴测供用户继续查看，验收脚本不重写工程。
        for area in bpy.context.screen.areas:
            if area.type == 'VIEW_3D':
                area.spaces.active.region_3d.view_rotation = bpy.data.objects['VIEW::isometric'].rotation_euler.to_quaternion()
                area.tag_redraw()
        return None
    except Exception as error:
        (REPORTS/'gui_error.txt').write_text(repr(error),encoding='utf8')
        raise

bpy.app.timers.register(step,first_interval=5.0)
