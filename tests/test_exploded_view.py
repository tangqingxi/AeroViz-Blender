"""Stage3副本、正式更新及保存后完整回归；机械Action只读保留。"""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import subprocess
import shutil
import bpy

WORKSPACE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(WORKSPACE/'scripts'));sys.dont_write_bytecode=True
import project_io
from animation import exploded_view as ex
from animation import kinematics as k


def write(path,value):
    Path(path).write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf8')


def bbox_check(config):
    spec=config['exploded_view'];scene=bpy.context.scene;scene.frame_set(spec['fully_exploded'])
    objects=[o for o in bpy.data.objects if o.type=='MESH' and not o.get('reference_only')]
    boxes={}
    from mathutils import Vector
    for o in objects:
        points=[o.matrix_world @ Vector(v) for v in o.bound_box]
        boxes[o.name]=([min(p[i] for p in points) for i in range(3)],[max(p[i] for p in points) for i in range(3)])
    excluded=set(spec['excluded_objects']);overlap=[];gap_min=None
    for index,a in enumerate(objects):
        for b in objects[index+1:]:
            if a.name in excluded and b.name in excluded:continue
            lo1,hi1=boxes[a.name];lo2,hi2=boxes[b.name]
            intersection=[min(hi1[i],hi2[i])-max(lo1[i],lo2[i]) for i in range(3)]
            if min(intersection)>1e-5:overlap.append({'objects':[a.name,b.name],'intersection_m':intersection})
    scene.frame_set(spec['frame_start'])
    return {'status':'PASS' if not overlap else 'REVIEW','fully_exploded_aabb_overlaps':overlap,'boxes':boxes,'note':'包围盒为保守筛查，不能等同于制造干涉检查；最终结合实际窗口验收'}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--config',required=True);parser.add_argument('--phase',choices=['prepare','apply','verify','reuse'],required=True);parser.add_argument('--expected-sha256')
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:]);config=json.loads(project_io.resolve(args.config).read_text(encoding='utf8'));target=project_io.project(config);work=WORKSPACE/'.work/stage-3'
    if args.expected_sha256:assert hashlib.sha256(target.read_bytes()).hexdigest()==args.expected_sha256
    bpy.ops.wm.open_mainfile(filepath=str(target))
    if args.phase=='prepare':
        assert target.is_relative_to(work)
        baseline=ex.capture_baseline(config);write(work/'explosion_baseline.json',baseline)
        ex.build(config,baseline)
    else:
        baseline=json.loads((work/'explosion_baseline.json').read_text(encoding='utf8'))
        if args.phase=='reuse':
            prior_actions=ex.actions_snapshot();prior_objects=set(bpy.data.objects.keys())
            ex.build(config,baseline)
            assert ex.actions_snapshot()==prior_actions and set(bpy.data.objects.keys())==prior_objects
        if args.phase=='apply':
            assert args.expected_sha256
            assert ex.capture_baseline(config)==baseline
            approval=json.loads((work/'test_approval.json').read_text(encoding='utf8'))
            assert approval['status']=='PASS' and approval['config']==config['exploded_view']
            ex.build(config,baseline)
    result=ex.validate(config,baseline)
    mechanical=json.loads((project_io.evidence_dir(config,'stage-2')/'structure_baseline.json').read_text(encoding='utf8'))
    result['stage2']=k.validate(config,mechanical)
    result['bbox']=bbox_check(config)
    write(work/(args.phase+'_explosion.json'),result)
    if args.phase in ('prepare','apply'):
        if args.phase=='prepare':
            project_io.save_project(config)
            write(work/'test_approval.json',{'status':'PASS','config':config['exploded_view']})
        else:
            backup=work/'rollback'/target.name
            assert backup.is_file() and hashlib.sha256(backup.read_bytes()).hexdigest()==args.expected_sha256
            try:
                project_io.save_project(config)
                commands=[('saved-verify',['--python',str(Path(__file__).resolve()),'--','--config',args.config,'--phase','verify']),
                          ('saved-regression',['--python',str(WORKSPACE/'tests/reverify_saved_project.py'),'--','--config',args.config,'--out',str(work/'formal-regression.json'),'--explosion-baseline',str(work/'explosion_baseline.json')])]
                for label,command in commands:
                    process=subprocess.run([bpy.app.binary_path,'--background','--factory-startup','--python-exit-code','1',*command],cwd=WORKSPACE,capture_output=True,timeout=120)
                    (work/(label+'.log')).write_bytes(process.stdout+process.stderr)
                    if process.returncode:raise RuntimeError(label+' failed')
            except Exception:
                if hashlib.sha256(target.read_bytes()).hexdigest()!=args.expected_sha256:shutil.copyfile(backup,target)
                assert hashlib.sha256(target.read_bytes()).hexdigest()==args.expected_sha256
                raise
    print('EXPLOSION_'+args.phase.upper()+'_PASS',result['object_total'],result['animated_objects'],result['bbox']['status'])


if __name__=='__main__':main()
