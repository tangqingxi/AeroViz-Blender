"""展示层副本测试、保存后回归与正式原子更新入口。"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

import bpy

WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(WORKSPACE/'scripts'))
sys.dont_write_bytecode = True
import presentation
import project_io


def write(path, value):
    Path(path).parent.mkdir(parents=True,exist_ok=True)
    Path(path).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf8')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config',required=True)
    parser.add_argument('--phase',choices=['prepare','verify','apply'],required=True)
    parser.add_argument('--expected-sha256')
    args = parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    config = json.loads(project_io.resolve(args.config).read_text(encoding='utf8'))
    target = project_io.project(config); work = WORKSPACE/'.work/stage-4.0'
    baseline_path = work/'source_baseline.json'
    bpy.ops.wm.open_mainfile(filepath=str(target))
    if args.phase == 'prepare':
        assert target.is_relative_to(work)
        baseline = presentation.capture_source(config); write(baseline_path,baseline)
    else:
        baseline = json.loads(baseline_path.read_text(encoding='utf8'))
    if args.phase == 'apply':
        assert args.expected_sha256 and hashlib.sha256(target.read_bytes()).hexdigest() == args.expected_sha256
        backup = work/'rollback/DF4.blend'
        assert hashlib.sha256(backup.read_bytes()).hexdigest() == args.expected_sha256
        approval = json.loads((work/'approval.json').read_text(encoding='utf8'))
        assert approval == {'status':'PASS','config':config['presentation']}
    if args.phase in ('prepare','apply'):
        presentation.build(config,baseline)
    result = presentation.validate(config,baseline)
    write(work/(args.phase+'_presentation.json'),result)
    if args.phase in ('prepare','apply'):
        try:
            presentation.configure_layout(bpy.data.scenes[config['presentation']['scene']])
            project_io.save_project(config)
            commands = [
                ('saved-verify',['--python',str(Path(__file__).resolve()),'--','--config',args.config,'--phase','verify']),
                ('saved-regression',['--python',str(WORKSPACE/'tests/reverify_saved_project.py'),'--','--config',args.config,'--out',str(work/(args.phase+'_regression.json'))])]
            for label, command in commands:
                process = subprocess.run([bpy.app.binary_path,'--background','--factory-startup','--python-exit-code','1',*command],cwd=WORKSPACE,capture_output=True,timeout=180)
                (work/(args.phase+'_'+label+'.log')).write_bytes(process.stdout+process.stderr)
                if process.returncode: raise RuntimeError(label+' failed: '+process.stdout.decode('utf8',errors='replace')[-1800:])
            if args.phase == 'prepare': write(work/'approval.json',{'status':'PASS','config':config['presentation']})
        except Exception:
            if args.phase == 'apply':
                shutil.copyfile(backup,target)
                assert hashlib.sha256(target.read_bytes()).hexdigest() == args.expected_sha256
            raise
    print('PRESENTATION_'+args.phase.upper()+'_PASS',json.dumps(result,ensure_ascii=False))


if __name__ == '__main__':
    main()
