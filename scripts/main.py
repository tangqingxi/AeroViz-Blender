"""Stage 1 入口：配置驱动导入、装配恢复、验证，并写入当前唯一工程。"""
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
import project_io
from adapters import ADAPTERS
from scene_builder import build, setup_views
from validation import snapshot, audit, write_report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', required=True)
    args = parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
    config = json.loads(project_io.resolve(args.config).read_text(encoding='utf8'))
    input_root = project_io.input_root(config)
    output = project_io.output_dir(config)
    target = project_io.project(config)
    if not output.is_relative_to(WORKSPACE):
        raise ValueError(f"输出必须位于 Blender 工作区：{output}")
    if output.is_relative_to(input_root) or input_root.is_relative_to(output):
        raise ValueError('输入和输出目录不能相互包含')

    # 预览与报告先落在临时目录，验收通过后再归档到审计仓库，本地不留副本。
    work = project_io.reset_dir(project_io.work_dir(config))
    work_reports = project_io.reset_dir(work/'reports')
    work_preview = project_io.reset_dir(work/'preview')
    evidence = project_io.evidence_dir(config, 'stage-1')

    before = snapshot(input_root)
    inventory, geometry, duplicates = audit(input_root)
    if config['adapter'] not in ADAPTERS:
        raise ValueError('尚未注册该格式适配器')
    data = importlib.import_module(ADAPTERS[config['adapter']]).read(config, input_root)
    objects, records = build(config, data, input_root)
    bbox = setup_views(objects, work_preview)
    write_report(work_reports, config, data, records, bbox, inventory, geometry, duplicates,
                 before, snapshot(input_root))

    copied = project_io.publish([work_reports/'validation.json', work_reports/'input_manifest.json',
                                 work_preview/'*.png'], evidence)
    target = project_io.save_project(config)
    project_io.clear_dir(work)
    print('STAGE1_IMPORT_OK', str(target), flush=True)
    print('STAGE1_EVIDENCE', ', '.join(p.name for p in copied), flush=True)


if __name__ == '__main__':
    try:
        main()
    except Exception:
        traceback.print_exc()
        sys.exit(1)
