"""Blender 5.0.1 工程 I/O 回归；所有写入工程均为 .work 中的字节副本。"""
import argparse
import ast
import hashlib
import json
import os
from pathlib import Path
import runpy
import shutil
import subprocess
import sys
import traceback
from unittest.mock import patch
import bpy

WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE / "scripts"))
sys.path.insert(0, str(WORKSPACE))
sys.dont_write_bytecode = True
import project_io


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding="utf8"))


def write(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf8")


def worker(args):
    config = read(args.config)
    target = project_io.project(config)
    result = {"case": args.case, "status": "FAIL"}
    exit_code = 0
    try:
        if args.case in ("guard", "force_gate", "first_gate"):
            import scene_builder
            old_scene = sorted(bpy.data.objects.keys())
            counters = {"cleanup": 0, "build": 0}
            def stop_cleanup(*unused, **kwargs):
                counters["cleanup"] += 1
                raise RuntimeError("AUTHORIZED_BOUNDARY_NO_REBUILD")
            def stop_build(*unused, **kwargs):
                counters["build"] += 1
                raise AssertionError("不允许实际构建场景")
            argv = [str(WORKSPACE / "scripts/main.py"), "--", "--config", args.config]
            if args.case == "force_gate":
                argv.append("--force-rebuild")
            with patch.object(project_io, "safe_reset_work_dir", side_effect=stop_cleanup), patch.object(scene_builder, "build", side_effect=stop_build), patch.object(sys, "argv", argv):
                try:
                    runpy.run_path(str(WORKSPACE / "scripts/main.py"), run_name="__main__")
                    raise AssertionError("入口必须在拒绝或测试边界停止")
                except SystemExit as error:
                    exit_code = int(error.code)
            assert exit_code != 0 and counters["build"] == 0
            assert old_scene == sorted(bpy.data.objects.keys())
            assert counters["cleanup"] == (0 if args.case == "guard" else 1)
            result.update(counters=counters, entry_exit_code=exit_code, scene_unchanged=True)
        elif args.case == "reopen":
            bpy.ops.wm.open_mainfile(filepath=str(target))
            assert bool(bpy.context.scene.get("io_regression_marker")) == args.expect_marker
            result.update(reopened=True, marker_present=bool(bpy.context.scene.get("io_regression_marker")))
        else:
            bpy.ops.wm.open_mainfile(filepath=str(target))
            old_hash = digest(target)
            old_filepath = bpy.data.filepath
            bpy.context.scene["io_regression_marker"] = True
            observed_temporaries=[]
            def save_observed():
                current_write=project_io._write_copy
                def inspect_copy(path):
                    assert Path(path).parent.resolve()==target.parent.resolve()
                    observed_temporaries.append(Path(path).name)
                    previous=bpy.data.filepath
                    value=current_write(path)
                    assert bpy.data.filepath==previous
                    return value
                with patch.object(project_io,"_write_copy",side_effect=inspect_copy):
                    return project_io.save_project(config)
            if args.case == "success":
                save_observed()
            elif args.case == "new_target":
                config = dict(config, blend_name="new-target.blend")
                target = project_io.project(config)
                assert not target.exists()
                save_observed()
                assert bpy.context.scene.get("io_regression_marker")
            else:
                if args.case == "save_failure":
                    def fail_save(path):
                        Path(path).write_bytes(b"injected incomplete save")
                        raise OSError("INJECTED_TEMP_SAVE_FAILURE")
                    context = patch.object(project_io, "_write_copy", side_effect=fail_save)
                else:
                    context = patch.object(project_io.os, "replace", side_effect=PermissionError("INJECTED_REPLACE_FAILURE"))
                with context:
                    try:
                        save_observed()
                        raise AssertionError("故障必须明确报错")
                    except RuntimeError as error:
                        assert "失败" in str(error)
                        result["reported_error"] = str(error)
                assert digest(target) == old_hash
            assert Path(bpy.data.filepath).resolve() == target.resolve()
            if args.case != "new_target":
                assert bpy.data.filepath == old_filepath
            assert target.is_file() and target.stat().st_size > 0
            assert not list(target.parent.glob("*.partial.blend"))
            assert not list(target.parent.glob("*.blend1"))
            assert bpy.context.preferences.filepaths.save_version == 0
            result.update(filepath_correct=True, target_nonempty=True, partials_absent=True, backups_absent=True,
                          target_hash_unchanged=digest(target) == old_hash if args.case != "new_target" else None,
                          same_filesystem=bool(observed_temporaries), filepath_before=old_filepath, filepath_after=bpy.data.filepath)
            assert observed_temporaries
        result["status"] = "PASS"
    except Exception:
        result["traceback"] = traceback.format_exc()
        exit_code = 1
    write(args.result, result)
    print("IO_CASE", args.case, result["status"], flush=True)
    if exit_code:
        sys.exit(exit_code)


def run(args):
    config = read(project_io.resolve(args.config))
    formal = project_io.project(config)
    audit = project_io.audit_root(config)
    records = audit / "manifests"
    before = digest(formal)
    assert bpy.app.version_string == "5.0.1", bpy.app.version_string
    expected = args.expected_sha256
    if expected and before != expected:
        raise RuntimeError("正式工程哈希不匹配；停止，禁止通过重建修复")
    test_config = dict(config, work_dir=".work/io-regression")
    sandbox = project_io.safe_reset_work_dir(test_config)
    results, logs = {}, []
    def static_checks():
        syntax, json_files, scan = [], [], []
        for source in sorted(WORKSPACE.rglob("*.py")):
            if ".work" in source.parts or ".git" in source.parts:
                continue
            relative=source.relative_to(WORKSPACE).as_posix()
            tree=ast.parse(source.read_text(encoding="utf8"),filename=relative)
            syntax.append(relative)
            for node in ast.walk(tree):
                if isinstance(node,ast.Call):
                    function=ast.unparse(node.func)
                    if function in ("bpy.ops.wm.save_mainfile","bpy.ops.wm.save_as_mainfile","os.replace","shutil.rmtree"):
                        assert relative=="scripts/project_io.py", (relative,function)
                        scan.append({"file":relative,"line":node.lineno,"operation":function})
        for source in sorted((WORKSPACE/"configs").glob("*.json")):
            cfg=read(source)
            assert project_io.resolve(cfg["input_root"]).is_absolute()
            assert project_io.project(cfg).is_relative_to(WORKSPACE)
            json_files.append(source.relative_to(WORKSPACE).as_posix())
        assert sum(r["operation"]=="bpy.ops.wm.save_as_mainfile" for r in scan)==1
        return {"status":"PASS","python_syntax":syntax,"json_and_paths":json_files,"save_call_scan":scan}

    def portable(text):
        for path, label in [(str(audit), "<AUDIT>"), (str(project_io.input_root(config)), "<INPUT>"), (str(WORKSPACE), "<DEV>"), (str(Path(bpy.app.binary_path).parent), "<BLENDER>")]:
            text = text.replace(path, label).replace(path.replace("\\", "/"), label)
        return text
    def portable_value(value):
        if isinstance(value, dict):
            return {k:portable_value(v) for k,v in value.items()}
        if isinstance(value, list):
            return [portable_value(v) for v in value]
        return portable(value) if isinstance(value,str) else value
    def child(case, cfg_path, expected_marker=False, expected_exit=0, result_name=None):
        result_file = sandbox / ((result_name or case)+"-result.json")
        command = [bpy.app.binary_path, "--background", "--factory-startup", "--python-exit-code", "1", "--python", str(Path(__file__).resolve()),
                   "--", "--config", str(cfg_path), "--case", case, "--result", str(result_file)]
        if expected_marker:
            command.append("--expect-marker")
        proc = subprocess.run(command, cwd=WORKSPACE, capture_output=True, text=True, encoding="utf8", errors="replace", timeout=120)
        logs.append(f"CASE {case} EXIT {proc.returncode}\n"+proc.stdout+proc.stderr)
        assert proc.returncode == expected_exit, proc.stdout+proc.stderr
        data = read(result_file)
        assert data["status"] == "PASS", data
        print("PASS", result_name or case, flush=True)
        return data
    try:
        results["static_checks"]=static_checks()
        print("PASS static_checks",flush=True)
        path_results = {}
        candidates = {"work_root": ".work", "work_nested": ".work/io-regression", "repository_root":str(WORKSPACE),
                      "workspace_parent":str(WORKSPACE.parent), "output":str(project_io.output_dir(config)),
                      "input":str(project_io.input_root(config)), "audit":str(audit),
                      "outside":str(WORKSPACE.parent/"arbitrary-outside"), "prefix_collision":str(WORKSPACE/".work-unsafe"),
                      "parent_traversal":".work/../output", "contains_input":".work/io-regression"}
        for name, value in candidates.items():
            candidate_config = dict(config, work_dir=value)
            if name == "contains_input":
                candidate_config["input_root"] = str(sandbox)
                candidate_config["input_root_env"] = None
            allowed = name in ("work_root", "work_nested")
            try:
                project_io.validate_work_dir(candidate_config)
                assert allowed, name
                verdict = "ALLOW"
            except ValueError:
                assert not allowed, name
                verdict = "REJECT"
            path_results[name] = {"status":"PASS", "decision":verdict, "judgment_only":True}
        own_config = dict(config, work_dir=".work/io-regression/reset-fixture")
        own = project_io.safe_reset_work_dir(own_config)
        (own/"marker.txt").write_text("delete only this fixture",encoding="utf8")
        assert not list(project_io.safe_reset_work_dir(own_config).iterdir())
        project_io.clear_work_dir(own_config)
        path_results["safe_reset_and_clear"] = {"status":"PASS"}
        for kind in ("symlink", "junction"):
            link = sandbox/(kind+"-to-audit")
            created = False
            try:
                if kind == "symlink":
                    try:
                        link.symlink_to(audit, target_is_directory=True)
                        created = True
                    except OSError as error:
                        path_results[kind] = {"status":"SKIP", "reason":f"WinError {getattr(error, 'winerror', None)}: {error.strerror}"}
                else:
                    process = subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(audit)], capture_output=True, text=True, errors="replace")
                    created = process.returncode == 0
                    if not created:
                        path_results[kind] = {"status":"SKIP", "reason":process.stdout+process.stderr}
                if created:
                    for work in (str(link), ".work"):
                        try:
                            project_io.validate_work_dir(dict(config,work_dir=work))
                            raise AssertionError("未拒绝重解析点")
                        except ValueError:
                            pass
                    path_results[kind] = {"status":"PASS", "decision":"REJECT", "tree_scan_rejects":True}
            finally:
                if created:
                    assert project_io._is_reparse(link) and link.resolve() == audit.resolve()
                    # 仅移除经过核对的链接本身，不递归、不访问目标内容。
                    if kind == "symlink":
                        link.unlink()
                    else:
                        os.rmdir(link)
        assert any(path_results[k]["status"]=="PASS" for k in ("junction","symlink")), "没有实际验证重解析点保护"
        results["path_safety"] = path_results
        print("PASS path_safety", flush=True)
        for case in ("success", "save_failure", "replace_failure", "new_target", "guard", "force_gate", "first_gate"):
            folder = sandbox/case
            folder.mkdir()
            target = folder/config["blend_name"]
            if case != "first_gate":
                shutil.copyfile(formal,target)
                assert digest(target)==before
            cfg = dict(config,output_dir=str(folder.relative_to(WORKSPACE)),work_dir=".work/io-regression/stage-work")
            cfg_path=folder/"config.json"
            write(cfg_path,cfg)
            marker=sandbox/"stage-work/sentinel.txt"
            marker.parent.mkdir(exist_ok=True)
            marker.write_text("do not reset before the guard",encoding="utf8")
            results[case]=child(case,cfg_path,expected_exit=1 if case in ("guard","force_gate","first_gate") else 0)
            assert marker.read_text(encoding="utf8")=="do not reset before the guard"
            if case in ("success","save_failure","replace_failure"):
                results[case+"_reopen"]=child("reopen",cfg_path,case=="success",result_name=case+"_reopen")
                if case != "success":
                    assert digest(target)==before
            if case=="new_target":
                cfg["blend_name"]="new-target.blend"
                write(cfg_path,cfg)
                results[case+"_reopen"]=child("reopen",cfg_path,True,result_name=case+"_reopen")
            if case=="guard":
                assert digest(target)==before
                assert "--force-rebuild" in logs[-1] and "拒绝覆盖" in logs[-1]
        bpy.ops.wm.open_mainfile(filepath=str(formal))
        meshes=[o for o in bpy.data.objects if o.type=="MESH"]
        integrity={"object_total":len(bpy.data.objects),"mesh_count":len(meshes),"material_count":len(bpy.data.materials),
                   "assigned_objects":sum(any(s.material for s in o.material_slots) for o in meshes),
                   "animation_data":sum(o.animation_data is not None for o in bpy.data.objects)+sum(s.animation_data is not None for s in bpy.data.scenes),
                   "actions":len(bpy.data.actions),"open":"PASS"}
        assert integrity == {"object_total":93,"mesh_count":33,"material_count":7,"assigned_objects":33,"animation_data":0,"actions":0,"open":"PASS"},integrity
        results["formal_integrity"] = integrity
        assert list(formal.parent.iterdir())==[formal]
        assert not list(WORKSPACE.rglob("*.blend1"))
        results["overall"]="PASS"
    except Exception:
        results["overall"]="FAIL"
        results["traceback"]=traceback.format_exc()
        print(results["traceback"],flush=True)
    finally:
        project_io.clear_work_dir(test_config)
        root = WORKSPACE/".work"
        if root.exists() and not any(root.iterdir()):
            root.rmdir()
        after=digest(formal)
        results.update(blender_version=bpy.app.version_string,formal_before_sha256=before,formal_after_sha256=after,
                       formal_unchanged=before==after,work_absent_or_empty=not root.exists() or not any(root.iterdir()),
                       dev_commit=subprocess.check_output(["git","rev-parse","HEAD"],cwd=WORKSPACE,text=True).strip())
        if before!=after or not results["work_absent_or_empty"]:
            results["overall"]="FAIL"
        record=records/"io-regression.json"
        record.write_text(json.dumps(portable_value(results),ensure_ascii=False,indent=2),encoding="utf8")
        (records/"io-regression.log").write_text(portable("\n".join(logs)),encoding="utf8")
    print("IO_REGRESSION",results["overall"],flush=True)
    if results["overall"]!="PASS":
        sys.exit(1)


parser=argparse.ArgumentParser()
parser.add_argument("--config",required=True)
parser.add_argument("--case")
parser.add_argument("--result")
parser.add_argument("--expect-marker",action="store_true")
parser.add_argument("--expected-sha256")
args=parser.parse_args(sys.argv[sys.argv.index("--")+1:])
if args.case:
    worker(args)
else:
    run(args)
