"""在实际 Blender 图形进程内验证当前工程的材质与结构，并截取 Material Preview。"""
import argparse
import json
from pathlib import Path
import sys

import bpy

WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE/'scripts'))
sys.dont_write_bytecode = True
import project_io
from materials import check_preserved

parser = argparse.ArgumentParser()
parser.add_argument('--config', required=True)
argv = sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
args = parser.parse_args(argv)
CONFIG = json.loads(project_io.resolve(args.config).read_text(encoding='utf8'))
EVIDENCE = project_io.evidence_dir(CONFIG, 'stage-1.5')
STATE = {'step': 0}


def step():
    try:
        assert not bpy.app.background
        if STATE['step']==0:
            baseline=json.loads((EVIDENCE/'material_structure_baseline.json').read_text(encoding='utf8'))
            result=check_preserved(baseline)
            expected=json.loads((EVIDENCE/'material_validation.json').read_text(encoding='utf8'))
            for row in expected['assignments']:
                obj=bpy.data.objects[row['object']]
                if 'material' in row:
                    assert all(s.material and s.material.name==row['material'] for s in obj.material_slots)
                    shader=next(n for n in obj.material_slots[0].material.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
                    assert max(abs(a-b) for a,b in zip(shader.inputs['Base Color'].default_value,row['definition']['rgba']))<1e-6
                    for key,field in [('Roughness','roughness'),('Metallic','metallic'),('Specular IOR Level','specular')]:
                        assert abs(shader.inputs[key].default_value-row['definition'][field])<1e-6
            assert bpy.context.scene.render.engine=='BLENDER_EEVEE'
            STATE['result']={'filepath':Path(bpy.data.filepath).name,'background':False,'preservation':result,'assigned_count':len(expected['assignments']), 'material_colors_verified':True}
            for area in bpy.context.screen.areas:
                if area.type=='VIEW_3D':
                    assert area.spaces.active.shading.type=='MATERIAL'
                    area.tag_redraw()
            STATE['step']=1
            return 15.0
        if STATE['step']==1:
            bpy.ops.screen.screenshot(filepath=str(EVIDENCE/'material_preview_window.png'))
            area=next(a for a in bpy.context.screen.areas if a.type=='VIEW_3D')
            with bpy.context.temp_override(area=area):
                bpy.ops.screen.screenshot_area(filepath=str(EVIDENCE/'material_preview.png'))
            STATE['result']['viewport_mode']=area.spaces.active.shading.type
            STATE['result']['studio_light']=area.spaces.active.shading.studio_light
            (EVIDENCE/'material_gui_validation.json').write_text(json.dumps(STATE['result'],ensure_ascii=False,indent=2),encoding='utf8')
            return None
    except Exception as error:
        (EVIDENCE/'material_gui_error.txt').write_text(repr(error),encoding='utf8')
        raise

bpy.app.timers.register(step,first_interval=6.0)
