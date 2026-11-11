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
args = parser.parse_args(sys.argv[sys.argv.index('--')+1:])
config = json.loads(project_io.resolve(args.config).read_text(encoding='utf8'))
evidence = project_io.evidence_dir(config,'stage-4.0')
evidence.mkdir(parents=True,exist_ok=True)
state = {'step':'setup','samples':[]}


def timer():
    try:
        assert not bpy.app.background
        scene = bpy.data.scenes[config['presentation']['scene']]
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
            bpy.ops.screen.screenshot(filepath=str(evidence/'gui_layout_only.png'))
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
            wrapped = any(b['frame'] < a['frame'] for a,b in zip(state['samples'],state['samples'][1:]))
            if wrapped:
                bpy.ops.screen.animation_cancel(restore_frame=False)
                scene.frame_set(1);scene.camera = bpy.data.objects['S4::CAMERA_A']
                state['step'] = 'finish';return 2.0
            if time.monotonic()-state['started'] > 85:
                raise RuntimeError('真实窗口未观察到完整播放循环')
            return .5
        if state['step'] == 'finish':
            scene.frame_set(1);scene.camera = bpy.data.objects['S4::CAMERA_A']
            bpy.ops.screen.screenshot(filepath=str(evidence/'gui_layout_only.png'))
            assert state['project_sha256'] == hashlib.sha256(project_io.project(config).read_bytes()).hexdigest()
            result = {'status':'PASS','background':False,'project_sha256':state['project_sha256'],
                      'blender_version':bpy.app.version_string,'camera':scene.camera.name,'frame':1,
                      'timeline_visible':True,'range':[scene.frame_start,scene.frame_end],
                      'markers':len(scene.timeline_markers),'layout_saved':args.save_layout,
                      'areas':[{'type':a.type,'ui_type':a.ui_type,'height':a.height,'width':a.width} for a in bpy.context.screen.areas],
                      'full_cycle_observed':not args.quick,'playback_samples':state['samples'],
                      'restart_count':state.get('restart_count',0),
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
