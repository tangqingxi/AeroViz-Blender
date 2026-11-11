"""用本地FFmpeg编码低清预览；不下载工具，不保留中间序列。"""
import argparse
import json
import os
from pathlib import Path
import subprocess

WORKSPACE = Path(__file__).resolve().parents[2]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config',default='configs/DF4.json')
    parser.add_argument('--ffmpeg',required=True)
    parser.add_argument('--encoder',default='h264_nvenc')
    args = parser.parse_args()
    config = json.loads((WORKSPACE/args.config).read_text(encoding='utf8'))
    if config['presentation'].get('revision')=='4.0-R1':
        raise RuntimeError('本轮R1禁止制作MP4')
    spec = config['presentation']; work = WORKSPACE/'.work/stage-4.0'
    frames = work/'frames'; ordered = work/'encode_frames'; ordered.mkdir(exist_ok=True)
    for index,frame in enumerate(range(1,spec['frame_end']+1,spec['preview']['frame_step']),1):
        source = frames/f'{frame:05d}.png'; target = ordered/f'{index:05d}.png'
        if not source.is_file(): raise FileNotFoundError(source)
        if target.exists(): target.unlink()
        os.link(source,target)
    out = (WORKSPACE/config['audit_root']).resolve()/'stages/stage-4.0/evidence/video/DF4_Stage4_0_preview.mp4'
    out.parent.mkdir(parents=True,exist_ok=True)
    command = [args.ffmpeg,'-hide_banner','-y','-framerate',str(spec['fps']/spec['preview']['frame_step']),
               '-start_number','1','-i',str(ordered/'%05d.png'),'-c:v',args.encoder]
    if args.encoder == 'h264_nvenc': command += ['-preset','p4','-rc','vbr','-cq','23','-b:v','0']
    elif args.encoder == 'libx264': command += ['-preset','medium','-crf','22']
    command += ['-pix_fmt','yuv420p','-movflags','+faststart','-an',str(out)]
    process = subprocess.run(command,capture_output=True)
    (work/'encoding.log').write_bytes(process.stdout+process.stderr)
    if process.returncode: raise RuntimeError(process.stderr.decode('utf8',errors='replace')[-2000:])
    print(out)


if __name__ == '__main__':
    main()
