"""真实窗口检查相机、完整时间轴与原生播放；按参数停留或退出。"""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import time
import traceback

import bpy

WORKSPACE = Path(__file__).resolve().parents[2]
sys.path.insert(0,str(WORKSPACE/'scripts'))
sys.dont_write_bytecode = True
import presentation
import project_io

parser = argparse.ArgumentParser()
parser.add_argument('--config',required=True)
parser.add_argument('--save-layout',action='store_true')
parser.add_argument('--leave-open',action='store_true')
parser.add_argument('--quick',action='store_true')
parser.add_argument('--reopen-check-only',action='store_true',help='只读确认重新打开后的布局，不保存或播放')
args = parser.parse_args(sys.argv[sys.argv.index('--')+1:])
config = json.loads(project_io.resolve(args.config).read_text(encoding='utf8'))
evidence = project_io.evidence_dir(config,config['presentation'].get('output_stage','stage-4.0'))
evidence.mkdir(parents=True,exist_ok=True)
work=WORKSPACE/config['presentation'].get('work_dir','.work/stage-4.0')
screen_path=work/'gui_layout_only.png' if config['presentation'].get('revision') in ('4.0-R1','4.0-R2') else evidence/'gui_layout_only.png'
screen_path.parent.mkdir(parents=True,exist_ok=True)
state = {'step':'reopen-check' if args.reopen_check_only else 'setup','samples':[]}
initial_open_state={'scene':bpy.context.scene.name,'frame':bpy.context.scene.frame_current}


def timer():
    try:
        assert not bpy.app.background
        scene = bpy.data.scenes[config['presentation']['scene']]
        if state['step']=='reopen-check':
            observed={'scene':bpy.context.scene.name,'frame':scene.frame_current,
                      'is_playing':bpy.context.screen.is_animation_playing}
            # 原生启动事件或用户浏览可能推进画面；最终只调整会话，不保存工程。
            if bpy.context.screen.is_animation_playing:bpy.ops.screen.animation_cancel(restore_frame=False)
            if bpy.context.scene!=scene:bpy.context.window.scene=scene
            if scene.frame_current!=1:scene.frame_set(1)
            scene.camera=bpy.data.objects['S4::CAMERA_A']
            area=max(bpy.context.screen.areas,key=lambda a:a.width*a.height)
            assert area.type=='VIEW_3D' and area.spaces.active.region_3d.view_perspective=='CAMERA'
            timeline=next(a for a in bpy.context.screen.areas if a.type=='DOPESHEET_EDITOR' and a.ui_type=='TIMELINE')
            region=next(r for r in timeline.regions if r.type=='WINDOW')
            left=region.view2d.region_to_view(0,0)[0];right=region.view2d.region_to_view(region.width,0)[0]
            assert left<=1 and right>=scene.frame_end
            bpy.ops.screen.screenshot(filepath=str(work/'final_reopen.png'))
            result={'status':'PASS','background':False,'scene':scene.name,'camera':scene.camera.name,
                    'frame':scene.frame_current,'is_playing':False,'range':[scene.frame_start,scene.frame_end],
                    'timeline_visible_range':[left,right],'save_called':False,'left_open':True,
                    'initial_cli_state':initial_open_state,'observed_before_normalizing':observed,
                    'project_sha256':hashlib.sha256(project_io.project(config).read_bytes()).hexdigest()}
            (evidence/'final_reopen_validation.json').write_bytes((json.dumps(result,ensure_ascii=False,indent=2)+'\n').encode('utf8'))
            print('FINAL_REOPEN_PASS',flush=True);return None
        if state['step'] == 'setup':
            presentation.configure_layout(scene)
            scene.sync_mode = 'FRAME_DROP'
            main = max(bpy.context.screen.areas,key=lambda a:a.width*a.height)
            bottom = next(a for a in bpy.context.screen.areas if a.type == 'DOPESHEET_EDITOR' and a.y < main.y and a.width > main.width*.8)
            if bottom.height < 220:
                # 原生边界移动要求鼠标处于编辑区边界，先让窗口事件刷新该状态。
                state['edge'] = [main.x+main.width//2,main.y-1,220-bottom.height]
                bpy.context.window.cursor_warp(state['edge'][0],state['edge'][1])
                state['step'] = 'resize';return .6
            state['step'] = 'timeline';return .3
        if state['step'] == 'resize':
            with bpy.context.temp_override(window=bpy.context.window,screen=bpy.context.screen,area=None,region=None):
                bpy.ops.screen.area_move(x=state['edge'][0],y=state['edge'][1],delta=state['edge'][2])
            state['step'] = 'timeline';return .5
        if state['step'] == 'timeline':
            for area in bpy.context.screen.areas:
                if area.type == 'DOPESHEET_EDITOR' and area.ui_type == 'TIMELINE':
                    area.spaces.active.show_markers = True
                    region = next(r for r in area.regions if r.type == 'WINDOW')
                    with bpy.context.temp_override(area=area,region=region):
                        bpy.ops.action.view_all()
            scene.frame_set(1)
            main = max(bpy.context.screen.areas,key=lambda a:a.width*a.height)
            bpy.context.window.cursor_warp(main.x+main.width//2,main.y+main.height//2)
            state['step'] = 'ready'
            return 3.0
        if state['step'] == 'ready':
            area = max(bpy.context.screen.areas,key=lambda a:a.width*a.height)
            assert area.type == 'VIEW_3D' and area.spaces.active.region_3d.view_perspective == 'CAMERA'
            assert any(a.type == 'DOPESHEET_EDITOR' and a.ui_type == 'TIMELINE' for a in bpy.context.screen.areas)
            assert scene.camera.name == 'S4::CAMERA_A' and scene.frame_current == 1
            if args.save_layout: project_io.save_project(config)
            state['project_sha256'] = hashlib.sha256(project_io.project(config).read_bytes()).hexdigest()
            bpy.ops.screen.screenshot(filepath=str(screen_path))
            state['step'] = 'finish' if args.quick else 'play'
            if not args.quick:
                state['started'] = time.monotonic()
                region = next(r for r in area.regions if r.type == 'WINDOW')
                with bpy.context.temp_override(area=area,region=region):
                    state['play_operator'] = sorted(bpy.ops.screen.animation_play())
            return 1.0
        if state['step'] == 'play':
            if not bpy.context.screen.is_animation_playing:
                # 启动期窗口重绘可能中断播放，只允许一次有记录的重新启动。
                if state.get('restart_count',0) >= 1:
                    raise RuntimeError('原生播放在第二次启动后仍中断')
                state['restart_count'] = state.get('restart_count',0)+1
                area = next(a for a in bpy.context.screen.areas if a.type == 'VIEW_3D')
                region = next(r for r in area.regions if r.type == 'WINDOW')
                with bpy.context.temp_override(area=area,region=region): bpy.ops.screen.animation_play()
                return 1.0
            state['samples'].append({'elapsed_s':round(time.monotonic()-state['started'],3),
                                     'frame':scene.frame_current,'camera':scene.camera.name})
            if config['presentation'].get('revision') in ('4.0-R1','4.0-R2'):
                captured=state.setdefault('visual_sample_frames',{})
                samples=(75,235,350,412,453,625,821,913,975) if config['presentation'].get('revision')=='4.0-R2' else (80,248,412,453,612,807,855,930,975)
                for frame in samples:
                    if frame<=scene.frame_current<frame+25 and str(frame) not in captured:
                        bpy.ops.screen.screenshot(filepath=str(work/f'gui_live_{frame:03d}.png'))
                        captured[str(frame)]={'actual_frame':scene.frame_current,'camera':scene.camera.name}
            wrapped = any(b['frame'] < a['frame'] for a,b in zip(state['samples'],state['samples'][1:]))
            if wrapped:
                bpy.ops.screen.animation_cancel(restore_frame=False)
                if config['presentation'].get('revision') in ('4.0-R1','4.0-R2'):
                    state['check_frames']=[75,350,412,453,625,821,913,975] if config['presentation'].get('revision')=='4.0-R2' else [80,248,412,453,807,930,975]
                    state['check_index']=0;state['check_wait']=False;state['step']='checks';return .2
                scene.frame_set(1);scene.camera = bpy.data.objects['S4::CAMERA_A']
                state['step'] = 'finish';return 2.0
            if time.monotonic()-state['started'] > 85:
                raise RuntimeError('真实窗口未观察到完整播放循环')
            return .5
        if state['step']=='checks':
            frame=state['check_frames'][state['check_index']]
            if not state['check_wait']:
                scene.frame_set(frame);state['check_wait']=True;return 1.2
            bpy.ops.screen.screenshot(filepath=str(work/f'gui_exact_{frame:03d}.png'))
            state.setdefault('exact_visual_frames',[]).append(frame)
            state['check_index']+=1;state['check_wait']=False
            if state['check_index']<len(state['check_frames']):return .2
            scene.frame_set(1);scene.camera=bpy.data.objects['S4::CAMERA_A']
            state['step']='finish';return 2.0
        if state['step'] == 'finish':
            scene.frame_set(1);scene.camera = bpy.data.objects['S4::CAMERA_A']
            bpy.ops.screen.screenshot(filepath=str(screen_path))
            assert state['project_sha256'] == hashlib.sha256(project_io.project(config).read_bytes()).hexdigest()
            result = {'status':'PASS','background':False,'project_sha256':state['project_sha256'],
                      'blender_version':bpy.app.version_string,'camera':scene.camera.name,'frame':1,
                      'timeline_visible':True,'range':[scene.frame_start,scene.frame_end],
                      'markers':len(scene.timeline_markers),'layout_saved':args.save_layout,
                      'areas':[{'type':a.type,'ui_type':a.ui_type,'height':a.height,'width':a.width} for a in bpy.context.screen.areas],
                      'full_cycle_observed':not args.quick,'playback_samples':state['samples'],
                      'restart_count':state.get('restart_count',0),
                      'visual_sample_frames':state.get('visual_sample_frames',{}),
                      'exact_visual_frames':state.get('exact_visual_frames',[]),
                      'left_open':args.leave_open,
                      'note':'GUI截图仅证明窗口布局，不作为展示渲染素材；最终停留遵循用户最新补充要求。'}
            (evidence/'gui_validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
            print('STAGE4_GUI_PASS',flush=True)
            if not args.leave_open: bpy.ops.wm.quit_blender()
            return None
    except Exception:
        if bpy.context.screen.is_animation_playing: bpy.ops.screen.animation_cancel(restore_frame=False)
        (evidence/'gui_error.json').write_text(traceback.format_exc(),encoding='utf8')
        # 故障窗口自动退出，避免给用户留下无法处理的半成品状态。
        bpy.ops.wm.quit_blender()
        return None


bpy.app.timers.register(timer,first_interval=4.0)
