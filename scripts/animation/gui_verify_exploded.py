"""Stage3真实窗口播放与截图，视口适配不修改相机或灯光，不保存工程。"""
import argparse
import json
from pathlib import Path
import sys
import time
import bpy
from mathutils import Vector

WORKSPACE=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(WORKSPACE/'scripts'));sys.dont_write_bytecode=True
import project_io
parser=argparse.ArgumentParser();parser.add_argument('--config',required=True);parser.add_argument('--evidence-dir');parser.add_argument('--snapshot-only',action='store_true')
args=parser.parse_args(sys.argv[sys.argv.index('--')+1:]);config=json.loads(project_io.resolve(args.config).read_text(encoding='utf8'));spec=config['exploded_view']
evidence=project_io.resolve(args.evidence_dir) if args.evidence_dir else project_io.evidence_dir(config,'stage-3');evidence.mkdir(parents=True,exist_ok=True)
state={'step':'setup','samples':[],'index':0,'capture':False}


def fit_view():
    objects=[o for o in bpy.data.objects if o.type=='MESH' and not o.get('reference_only')]
    points=[o.matrix_world @ Vector(v) for o in objects for v in o.bound_box]
    lo=Vector([min(v[i] for v in points) for i in range(3)]);hi=Vector([max(v[i] for v in points) for i in range(3)])
    for area in bpy.context.screen.areas:
        if area.type=='VIEW_3D':
            space=area.spaces.active;rotation=(-Vector((1,-1,.8))).to_track_quat('-Z','Y')
            projected=[rotation.to_matrix().transposed() @ (p-(lo+hi)/2) for p in points]
            width=max(p.x for p in projected)-min(p.x for p in projected);height=max(p.y for p in projected)-min(p.y for p in projected)
            region=next(r for r in area.regions if r.type=='WINDOW');aspect=region.width/max(region.height,1)
            space.region_3d.view_location=(lo+hi)/2;space.region_3d.view_distance=max(width,height*aspect)*1.25
            space.region_3d.view_rotation=rotation;space.region_3d.view_perspective='ORTHO'
            space.overlay.show_extras=False;space.clip_start=.001;area.tag_redraw()


def timer():
    try:
        assert not bpy.app.background
        scene=bpy.context.scene
        if state['step']=='setup':
            bpy.context.preferences.filepaths.save_version=0
            assert len(bpy.data.objects)==config['exploded_view']['expected_original_objects']+len(spec['branches'])
            area=next((a for a in bpy.context.screen.areas if a.type=='PROPERTIES'),None) or next(a for a in bpy.context.screen.areas if a.type=='DOPESHEET_EDITOR' and a.ui_type!='TIMELINE')
            area.type='DOPESHEET_EDITOR';area.ui_type='DOPESHEET'
            area.spaces.active.dopesheet.show_hidden=True;area.spaces.active.dopesheet.show_only_selected=False
            region=next(r for r in area.regions if r.type=='WINDOW')
            with bpy.context.temp_override(area=area,region=region):bpy.ops.action.view_all()
            scene.frame_set(spec['fully_exploded']);fit_view();scene.frame_set(spec['frame_start'])
            state['started']=time.monotonic();state['step']='screenshots' if args.snapshot_only else 'play'
            if not args.snapshot_only:bpy.ops.screen.animation_play()
            return .2
        if state['step']=='play':
            assert bpy.context.screen.is_animation_playing
            state['samples'].append({'elapsed':time.monotonic()-state['started'],'frame':scene.frame_current,'locations':{o.name:list(o.location) for o in bpy.data.objects if o.name.startswith(spec['controller_prefix'])}})
            wrapped=any(b['frame']<a['frame'] for a,b in zip(state['samples'],state['samples'][1:]))
            if wrapped:
                bpy.ops.screen.screenshot(filepath=str(evidence/'gui_playback.png'));bpy.ops.screen.animation_cancel(restore_frame=False);state['step']='screenshots';return .5
            if time.monotonic()-state['started']>60:raise RuntimeError('实际窗口播放未完成完整循环')
            return .2
        if state['step']=='screenshots':
            frame=spec['gui_frames'][state['index']]
            if not state['capture']:
                scene.frame_set(frame);fit_view();state['capture']=True;return 2.0
            bpy.ops.screen.screenshot(filepath=str(evidence/f'gui_frame_{frame:03d}.png'));state['index']+=1;state['capture']=False
            if state['index']<len(spec['gui_frames']):return .2
            scene.frame_set(spec['fully_exploded']);fit_view()
            result={'status':'PASS','blender_version':bpy.app.version_string,'background':False,'full_cycle_observed':not args.snapshot_only,'physical_key_injection':False,
                    'method':'Blender native screen.animation_play, same operator as Space','playback_samples':state['samples'],'frames_captured':spec['gui_frames'],'final_frame':scene.frame_current,'gui_saved_project':False,'exit_after_capture':True}
            (evidence/'gui_validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8');print('EXPLODED_GUI_PASS',flush=True)
            # 用户要求截图验收后退出；执行退出命令，不调用保存接口。
            bpy.ops.wm.quit_blender()
            return None
    except Exception as error:
        if bpy.context.screen.is_animation_playing:bpy.ops.screen.animation_cancel(restore_frame=False)
        (evidence/'gui_error.json').write_text(json.dumps({'error':str(error)},ensure_ascii=False),encoding='utf8');raise

bpy.app.timers.register(timer,first_interval=4.0)
