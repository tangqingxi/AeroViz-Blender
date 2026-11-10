"""命令行入口：配置驱动、显式适配器、验证后保存。"""
import argparse
import importlib
import json
from pathlib import Path
import sys
import traceback
import bpy

WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE/'scripts'))
sys.path.insert(0, str(WORKSPACE))
sys.dont_write_bytecode = True
from adapters import ADAPTERS
from scene_builder import build, setup_views
from validation import snapshot, audit, write_report

def workspace_path(value):
    p = (WORKSPACE/value).resolve()
    if not p.is_relative_to(WORKSPACE):
        raise ValueError(f"输出必须位于 Blender 工作区：{p}")
    return p

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', required=True)
    args = parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
    config_path = workspace_path(args.config)
    config = json.loads(config_path.read_text(encoding='utf8'))
    input_root = (WORKSPACE/config['input_root']).resolve()
    output = workspace_path(config['output_dir'])
    if output.is_relative_to(input_root) or input_root.is_relative_to(output):
        raise ValueError('输入和输出目录不能相互包含')
    for name in ('preview', 'reports'):
        (output/name).mkdir(parents=True,exist_ok=True)
    before = snapshot(input_root)
    inventory, geometry, duplicates = audit(input_root)
    if config['adapter'] not in ADAPTERS:
        raise ValueError('尚未注册该格式适配器')
    data = importlib.import_module(ADAPTERS[config['adapter']]).read(config, input_root)
    objects, records = build(config,data,input_root)
    bbox = setup_views(objects,output)
    write_report(output,config,data,records,bbox,inventory,geometry,duplicates,before,snapshot(input_root))
    target = workspace_path(str(Path(config['output_dir'])/config['blend_name']))
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(target))
    print('STAGE1_IMPORT_OK',str(target),flush=True)

if __name__ == '__main__':
    try:
        main()
    except Exception:
        traceback.print_exc()
        sys.exit(1)
