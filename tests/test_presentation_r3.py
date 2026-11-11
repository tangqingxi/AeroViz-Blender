"""R3副本验证、高密几何审批与正式保存后独立回归。"""
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
import project_io
import presentation
import presentation_r3


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--config',required=True);parser.add_argument('--phase',choices=['prepare','verify','apply'],required=True);parser.add_argument('--expected-sha256')
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:]);c=json.loads(project_io.resolve(args.config).read_text(encoding='utf8'));target=project_io.project(c);work=WORKSPACE/'.work/stage-4-r3'
    baseline=json.loads((project_io.evidence_dir(c,'stage-4.0')/'source_baseline.json').read_text(encoding='utf8'))
    if args.phase=='prepare':assert target.is_relative_to(work)
    if args.phase=='apply':
        assert args.expected_sha256 and hashlib.sha256(target.read_bytes()).hexdigest()==args.expected_sha256
        assert hashlib.sha256((work/'rollback/DF4.blend').read_bytes()).hexdigest()==args.expected_sha256
        approval=json.loads((work/'approval.json').read_text(encoding='utf8'));assert approval=={'status':'PASS','config':c['presentation']}
        scan=json.loads((work/'intersections.json').read_text(encoding='utf8'));assert scan['status']=='PASS'
        assert scan['candidate_sha256']==hashlib.sha256((work/'candidate.blend').read_bytes()).hexdigest()
        assert scan['config_sha256']==hashlib.sha256(json.dumps(c['presentation'],sort_keys=True).encode()).hexdigest()
    bpy.ops.wm.open_mainfile(filepath=str(target))
    if args.phase!='verify':presentation_r3.apply(c,baseline)
    result=presentation_r3.validate(c,baseline)
    (work/(args.phase+'_validation.json')).write_bytes((json.dumps(result,ensure_ascii=False,indent=2)+'\n').encode('utf8'))
    if args.phase!='verify':
        try:
            presentation.configure_layout(bpy.data.scenes[c['presentation']['scene']]);project_io.save_project(c)
            cmd=[bpy.app.binary_path,'--background','--factory-startup','--python-exit-code','1','--python',str(WORKSPACE/'tests/reverify_saved_project.py'),'--','--config',args.config,'--out',str(work/(args.phase+'_regression.json'))]
            proc=subprocess.run(cmd,cwd=WORKSPACE,capture_output=True,timeout=240);(work/(args.phase+'_saved_verify.log')).write_bytes(proc.stdout+proc.stderr)
            if proc.returncode:raise RuntimeError(proc.stdout.decode('utf8',errors='replace')[-2000:])
            if args.phase=='prepare':(work/'approval.json').write_bytes(json.dumps({'status':'PASS','config':c['presentation']},ensure_ascii=False).encode('utf8'))
        except Exception:
            if args.phase=='apply':shutil.copyfile(work/'rollback/DF4.blend',target);assert hashlib.sha256(target.read_bytes()).hexdigest()==args.expected_sha256
            raise
    print('R3_'+args.phase.upper()+'_PASS',result['reassembly_matrix_error'],result['synchronized_group_factor_error'])


if __name__=='__main__':main()
