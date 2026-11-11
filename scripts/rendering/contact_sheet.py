"""将阶段渲染排版为一张本地验收合图，不改变原始渲染内容。"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys

from PIL import Image, ImageDraw, ImageFont

WORKSPACE = Path(__file__).resolve().parents[2]
sys.path.insert(0,str(WORKSPACE/'scripts'))
sys.dont_write_bytecode = True
import project_io


def compose(config, source_dir, font_path=None):
    spec = config['presentation']; source_dir = Path(source_dir).resolve()
    evidence = project_io.evidence_dir(config,spec.get('output_stage','stage-4.0'))
    destination = evidence/spec.get('overview_subdir','images')/spec.get('overview_name',f"{config['model_name']}_Stage4_0_overview.png")
    frames = sorted(spec['stills'].items(),key=lambda row:row[1])
    labels = {
        'stage_00_hero':'完整机型 · Hero',
        'stage_00_hero_reveal_start':'低角度登场 · 灯光揭示',
        'stage_01_legs_out':'三脚架整体拆出',
        'stage_01_leg_closeup':'单脚架细节',
        'stage_02_outer_duct_partial':'外涵道逐片分离',
        'stage_03_motor_closeup':'电机揭示与退出',
        'stage_03_power_system':'旋翼与动力系统',
        'stage_04_surface_deflection':'四舵面独立偏转',
        'stage_04_servo_pair_closeup':'舵机与舵面对应',
        'stage_04_controls_servos':'舵面 / 舵机依次退出',
        'stage_05_flight_controller_closeup':'上框与飞控共同移出',
        'stage_05_battery_frame':'电池框架拆解',
        'stage_06_esc_closeup':'电调与下部夹持结构',
        'stage_06_final_exploded':'最终完整分解',
    }
    labels.update(spec.get('still_labels',{}))
    font_path = font_path or Path(os.environ.get('WINDIR','C:/Windows'))/'Fonts/msyh.ttc'
    title_font = ImageFont.truetype(str(font_path),40)
    label_font = ImageFont.truetype(str(font_path),24)
    note_font = ImageFont.truetype(str(font_path),21)
    heroes = [name for name in ('stage_00_hero','stage_06_final_exploded') if name in spec['stills']]
    details = [name for name,frame in frames if name not in heroes]
    gap = 16; width = 1952; header = 106; hero_height = 584; cell_width = 468; cell_height = 310
    rows = (len(details)+3)//4
    height = header + hero_height + gap + rows*(cell_height+gap)+54
    sheet = Image.new('RGB',(width,height),(27,28,31)); draw = ImageDraw.Draw(sheet)
    draw.text((gap,18),config['model_name']+'  |  '+spec.get('overview_title','Stage 4.0 展示与渐进式拆解'),font=title_font,fill=(235,237,240))
    draw.text((gap,72),'按原渲染拼接 · 帧号对应 30 FPS 时间轴 · 本地视觉验收合图',font=note_font,fill=(156,164,175))
    sources = []
    def panel(name,x,y,target_width,target_height):
        path = source_dir/(name+'.png')
        with Image.open(path) as original:
            im = original.convert('RGB')
        image_height = target_height-44
        im.thumbnail((target_width,image_height),Image.Resampling.LANCZOS)
        sheet.paste(im,(x+(target_width-im.width)//2,y+(image_height-im.height)//2))
        frame = spec['stills'][name]
        draw.text((x+8,y+image_height+8),f"{labels.get(name,name)}  ·  F{frame:04d}",font=label_font,fill=(218,223,230))
        sources.append({'source':path.name,'frame':frame,'label':labels.get(name,name),
                        'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    for i,name in enumerate(heroes): panel(name,gap+i*(960+gap),header,960,hero_height)
    start_y = header+hero_height+gap
    for i,name in enumerate(details): panel(name,gap+(i%4)*(cell_width+gap),start_y+(i//4)*(cell_height+gap),cell_width,cell_height)
    draw.text((gap,height-40),'上排：完整机型 / 最终布局；下排：按时间顺序的阶段与细节。画面不代表实际拆装行程。',font=note_font,fill=(156,164,175))
    destination.parent.mkdir(parents=True,exist_ok=True)
    sheet.save(destination)
    record = {'local_only':spec.get('overview_local_only',True),'path':destination.relative_to(project_io.audit_root(config)).as_posix(),
              'width':width,'height':height,'source_frame_count':len(sources),'sources':sources,
              'sha256':hashlib.sha256(destination.read_bytes()).hexdigest(),'bytes':destination.stat().st_size}
    (evidence/'contact_sheet.json').write_bytes((json.dumps(record,ensure_ascii=False,indent=2)+'\n').encode('utf8'))
    return destination


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config',default='configs/DF4.json')
    parser.add_argument('--source-dir',required=True)
    parser.add_argument('--font')
    parser.add_argument('--clean-work-source',action='store_true')
    args = parser.parse_args()
    config = json.loads(project_io.resolve(args.config).read_text(encoding='utf8'))
    source = project_io.resolve(args.source_dir)
    destination = compose(config,source,args.font)
    if args.clean_work_source:
        cleanup = dict(config,work_dir=str(source))
        project_io.clear_work_dir(cleanup)
    print(destination)


if __name__ == '__main__':
    main()
