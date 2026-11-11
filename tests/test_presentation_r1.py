"""R1先改字节副本，全部通过后原子更新，保存后回归失败则恢复原字节。"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

import bpy

WORKSPACE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(WORKSPACE/'scripts'));sys.dont_write_bytecode=True
import presentation
import presentation_r1
import project_io


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--config',required=True)
    parser.add_argument('--phase',choices=['prepare','verify','apply'],required=True)
    parser.add_argument('--expected-sha256');args=parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    config=json.loads(project_io.resolve(args.config).read_text(encoding='utf8'))
    target=project_io.project(config);work=WORKSPACE/'.work/stage-4-r1'
    baseline=json.loads((project_io.evidence_dir(config,'stage-4.0')/'source_baseline.json').read_text(encoding='utf8'))
    if args.phase=='prepare':assert target.is_relative_to(work)
    if args.phase=='apply':
        assert args.expected_sha256 and hashlib.sha256(target.read_bytes()).hexdigest()==args.expected_sha256
        assert hashlib.sha256((work/'rollback/DF4.blend').read_bytes()).hexdigest()==args.expected_sha256
        approval=json.loads((work/'approval.json').read_text(encoding='utf8'))
        assert approval=={'status':'PASS','config':config['presentation']}
        sweep=json.loads((work/'intersection_probe.json').read_text(encoding='utf8'))
        assert sweep['status']=='PASS' and not sweep['new_intersection_events']
        assert sweep['presentation_config_sha256']==hashlib.sha256(json.dumps(config['presentation'],sort_keys=True).encode()).hexdigest()
        assert sweep['candidate_sha256']==hashlib.sha256((work/'candidate.blend').read_bytes()).hexdigest()
    bpy.ops.wm.open_mainfile(filepath=str(target))
    if args.phase!='verify':presentation_r1.apply(config,baseline)
    result=presentation_r1.validate(config,baseline)
    (work/(args.phase+'_validation.json')).write_bytes((json.dumps(result,ensure_ascii=False,indent=2)+'\n').encode('utf8'))
    if args.phase!='verify':
        try:
            presentation.configure_layout(bpy.data.scenes[config['presentation']['scene']]);project_io.save_project(config)
            for label,command in [('saved-reverify',['--python',str(WORKSPACE/'tests/reverify_saved_project.py'),'--','--config',args.config,'--out',str(work/(args.phase+'_regression.json'))])]:
                process=subprocess.run([bpy.app.binary_path,'--background','--factory-startup','--python-exit-code','1',*command],cwd=WORKSPACE,capture_output=True,timeout=240)
                (work/(args.phase+'_'+label+'.log')).write_bytes(process.stdout+process.stderr)
                if process.returncode:raise RuntimeError(process.stdout.decode('utf8',errors='replace')[-2000:])
            if args.phase=='prepare':(work/'approval.json').write_bytes(json.dumps({'status':'PASS','config':config['presentation']},ensure_ascii=False).encode('utf8'))
        except Exception:
            if args.phase=='apply':
                shutil.copyfile(work/'rollback/DF4.blend',target)
                assert hashlib.sha256(target.read_bytes()).hexdigest()==args.expected_sha256
            raise
    print('R1_'+args.phase.upper()+'_PASS',json.dumps(result,ensure_ascii=False))


if __name__=='__main__':main()
