"""真实 Blender 窗口播放与截图验收；不保存工程、不使用离线渲染。"""
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
from animation import kinematics as engine

parser=argparse.ArgumentParser();parser.add_argument('--config',required=True)
args=parser.parse_args(sys.argv[sys.argv.index('--')+1:])
config=json.loads(project_io.resolve(args.config).read_text(encoding='utf8'))
evidence=project_io.evidence_dir(config,'stage-2');evidence.mkdir(parents=True,exist_ok=True)
state={'step':'setup','samples':[],'index':0,'capture':False}


def timer():
    try:
        assert not bpy.app.background
        scene=bpy.context.scene;animation=config['animation']
        if state['step']=='setup':
            assert Path(bpy.data.filepath).resolve()==project_io.project(config).resolve()
            scene.frame_set(animation['frame_start'])
            animated=sorted(o.name for o in bpy.data.objects if o.animation_data)
            assert animated==sorted('JOINT::'+m['joint'] for m in animation['motions'])
            state['channels']={name:{'action':bpy.data.objects[name].animation_data.action.name,'curves':len(engine.fcurves(bpy.data.objects[name]))} for name in animated}
            # 保留底部 Timeline，右侧另显示 Dope Sheet；不改变场景对象。
            area=next(a for a in bpy.context.screen.areas if a.type=='PROPERTIES')
            area.type='DOPESHEET_EDITOR';area.ui_type='DOPESHEET'
            area.spaces.active.mode='DOPESHEET'
            area.spaces.active.dopesheet.show_only_selected=False
            area.spaces.active.dopesheet.show_hidden=True
            region=next(r for r in area.regions if r.type=='WINDOW')
            with bpy.context.temp_override(area=area,region=region):
                bpy.ops.action.view_all()
            state['started']=time.monotonic();state['step']='playing'
            # 与空格键相同的原生播放操作；随后只观察真实推进，不在播放期间设帧。
            bpy.ops.screen.animation_play()
            return 0.2
        if state['step']=='playing':
            assert bpy.context.screen.is_animation_playing
            frame=scene.frame_current
            state['samples'].append({'elapsed_s':time.monotonic()-state['started'],'frame':frame,
                                     'joint_quaternions':{name:list(bpy.data.objects[name].rotation_quaternion) for name in state['channels']}})
            elapsed=time.monotonic()-state['started']
            wrapped=any(b['frame']<a['frame'] for a,b in zip(state['samples'],state['samples'][1:]))
            if elapsed>6 and wrapped:
                bpy.ops.screen.screenshot(filepath=str(evidence/'gui_playback.png'))
                bpy.ops.screen.animation_cancel(restore_frame=False)
                assert not bpy.context.screen.is_animation_playing
                state['step']='screenshots'
                return 0.5
            if elapsed>45:
                raise RuntimeError('实际图形播放未在时限内覆盖一次完整循环')
            return 0.2
        if state['step']=='screenshots':
            sample=animation['gui_samples'][state['index']]
            if not state['capture']:
                scene.frame_set(sample['frame'])
                direction=Vector((1,-1,0.8) if state['index']==0 else (1,-1,-0.55))
                rotation=(-direction).to_track_quat('-Z','Y')
                for area in bpy.context.screen.areas:
                    if area.type=='VIEW_3D':
                        area.spaces.active.region_3d.view_rotation=rotation
                        area.tag_redraw()
                state['capture']=True
                return 2.0
            bpy.ops.screen.screenshot(filepath=str(evidence/('gui_'+sample['name']+'.png')))
            state['index']+=1;state['capture']=False
            if state['index']<len(animation['gui_samples']):
                return 0.3
            scene.frame_set(animation['frame_start'])
            for area in bpy.context.screen.areas:
                if area.type=='VIEW_3D':
                    area.spaces.active.region_3d.view_rotation=(-Vector((1,-1,0.8))).to_track_quat('-Z','Y')
                    area.tag_redraw()
            result={'status':'PASS','blender_version':bpy.app.version_string,'background':False,'project':str(project_io.project(config).relative_to(WORKSPACE)).replace('\\','/'),
                    'playback_operator':'screen.animation_play (Space equivalent)','actual_playback_observed':True,'full_cycle_observed':True,
                    'playback_samples':state['samples'],'channels':state['channels'],
                    'screenshots':['gui_playback.png']+['gui_'+s['name']+'.png' for s in animation['gui_samples']],
                    'stopped_at_frame':scene.frame_current,'file_saved_by_gui':False}
            (evidence/'gui_validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
            print('STAGE2_GUI_PLAYBACK_PASS',flush=True)
            return None
    except Exception as error:
        if bpy.context.screen.is_animation_playing:
            bpy.ops.screen.animation_cancel(restore_frame=False)
        (evidence/'gui_error.json').write_text(json.dumps({'status':'FAIL','error':str(error)},ensure_ascii=False),encoding='utf8')
        raise

bpy.app.timers.register(timer,first_interval=5.0)
