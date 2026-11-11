"""只渲染展示场景，不保存工程；中间序列限定在.work。"""
import argparse
import json
from pathlib import Path
import sys
import time

import bpy

WORKSPACE = Path(__file__).resolve().parents[2]
sys.path.insert(0,str(WORKSPACE/'scripts'))
sys.dont_write_bytecode = True
import project_io
import presentation


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config',required=True)
    parser.add_argument('--mode',choices=['stills','video','benchmark'],required=True)
    parser.add_argument('--start',type=int,default=1)
    parser.add_argument('--end',type=int)
    args = parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    config = json.loads(project_io.resolve(args.config).read_text(encoding='utf8'))
    bpy.ops.wm.open_mainfile(filepath=str(project_io.project(config)))
    spec = config['presentation']; scene = bpy.data.scenes[spec['scene']]
    presentation.activate(scene)
    work = WORKSPACE/'.work/stage-4.0'
    evidence = project_io.evidence_dir(config,'stage-4.0')
    scene.render.image_settings.file_format = 'PNG'
    scene.render.resolution_x = spec['preview']['width'];scene.render.resolution_y = spec['preview']['height']
    scene.render.resolution_percentage = 100
    if args.mode == 'stills':
        scene.eevee.taa_render_samples = 32
        frames = [(name,frame) for name,frame in spec['stills'].items()]
        destination = evidence/'images'
    elif args.mode == 'benchmark':
        scene.eevee.taa_render_samples = 8
        frames = [('benchmark',60)];destination = work
    else:
        scene.eevee.taa_render_samples = spec['preview']['samples']
        frames = [(f'{frame:05d}',frame) for frame in range(args.start,args.end or spec['frame_end']+1,spec['preview']['frame_step'])]
        destination = work/'frames'
    destination.mkdir(parents=True,exist_ok=True)
    start = time.monotonic()
    for index,(name,frame) in enumerate(frames):
        scene.frame_set(frame)
        scene.render.filepath = str(destination/(name+'.png'))
        bpy.ops.render.render(write_still=True,scene=scene.name)
        print('S4_RENDER',index+1,len(frames),frame,round(time.monotonic()-start,2),flush=True)


if __name__ == '__main__':
    main()
