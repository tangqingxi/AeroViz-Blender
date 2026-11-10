"""只读复验当前唯一工程，对照审计仓库中已归档的验收记录。

打开 `output/<MODEL>/<blend_name>`，重放 Stage 1 与 Stage 1.5 记录过的断言，然后把
一份新的核验记录写回审计仓库的 `manifests/`。本脚本不保存任何 `.blend`，不写临时
工程，也不改动模型输入，因此可以安全地跑在交付物上。

用法::

    blender --background --factory-startup --python-exit-code 1 `
            --python tests/reverify_saved_project.py -- --config configs/DF4.json `
            [--out path/to/record.json]

期望值来源（均在审计仓库内，不依赖本地 output/reports）：

* ``stages/stage-1/evidence/validation.json``            网格数、世界矩阵、包围盒
* ``stages/stage-1.5/evidence/material_validation.json``  材质分配与 BSDF 数值
* ``stages/stage-1.5/evidence/material_structure_baseline.json``  89 个原有对象的状态
"""
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import sys
import traceback

import bpy

WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE / "scripts"))
sys.dont_write_bytecode = True
import project_io  # noqa: E402

REL = project_io  # 便于阅读：所有路径都经 project_io 解析


def load(path):
    return json.loads(Path(path).read_text(encoding="utf8"))


def rel(path):
    path = Path(path).resolve()
    try:
        return str(path.relative_to(WORKSPACE)).replace("\\", "/")
    except ValueError:
        return path.name


def max_matrix_error(obj, matrix_rows):
    return max(
        abs(obj.matrix_world[r][c] - matrix_rows[r][c]) for r in range(4) for c in range(4)
    )


def check_stage1(record, baseline):
    meshes = [o for o in bpy.data.objects if o.type == "MESH"]
    assert len(meshes) == record["imported_count"], (len(meshes), record["imported_count"])
    rows = {r["object"]: r for r in record["records"]}
    assert set(rows) == {o.name for o in meshes}, "网格对象名与 Stage 1 记录不一致"
    matrix_error = max(max_matrix_error(bpy.data.objects[n], r["world_matrix"]) for n, r in rows.items())
    assert matrix_error < 1e-6, matrix_error
    reference = [o for o in meshes if o.get("reference_only")]
    visible = [o for o in meshes if not o.get("reference_only")]
    assert len(visible) == record["visible_count"], (len(visible), record["visible_count"])
    assert len(reference) == len(meshes) - record["visible_count"], len(reference)
    points = [o.matrix_world @ v.co for o in visible for v in o.data.vertices]
    lo = [min(p[i] for p in points) for i in range(3)]
    hi = [max(p[i] for p in points) for i in range(3)]
    dims = [hi[i] - lo[i] for i in range(3)]
    bbox_error = max(abs(dims[i] - record["bbox"]["dimensions_m"][i]) for i in range(3))
    assert bbox_error < 1e-6, bbox_error
    links = sum(1 for o in bpy.data.objects if o.name.startswith("LINK::"))
    joints = sum(1 for o in bpy.data.objects if o.name.startswith("JOINT::"))
    assert links == sum(1 for k in baseline if k.startswith("LINK::")), links
    assert joints == sum(1 for k in baseline if k.startswith("JOINT::")), joints
    return {
        "mesh_count": len(meshes),
        "visible_count": len(visible),
        "reference_only_count": len(reference),
        "link_empty_count": links,
        "joint_empty_count": joints,
        "world_matrix_max_error": matrix_error,
        "bbox_dimensions_m": dims,
        "bbox_max_abs_error": bbox_error,
        "status": "PASS",
    }


def check_stage15(record, baseline, animated_objects=(), parent_overrides=None, additional_objects=()):
    import materials  # 延迟导入：需要 bpy

    preserved = materials.check_preserved(baseline, animated_objects=animated_objects, parent_overrides=parent_overrides)
    added = preserved["added_objects"]
    expected_added = sorted("MATERIAL_LIGHT::" + name for name in record["environment"]["lights"])
    assert added == sorted(expected_added + list(additional_objects)), (added, expected_added)
    assert len(bpy.data.objects) == len(baseline) + len(added), len(bpy.data.objects)
    meshes = [o for o in bpy.data.objects if o.type == "MESH"]
    assert len(meshes) == 33, len(meshes)
    verified, color_error = 0, 0.0
    for row in record["assignments"]:
        obj = bpy.data.objects[row["object"]]
        if "material" not in row:
            continue
        assert obj.material_slots and all(
            slot.material and slot.material.name == row["material"] for slot in obj.material_slots
        ), row["object"]
        shader = next(
            n for n in obj.material_slots[0].material.node_tree.nodes if n.type == "BSDF_PRINCIPLED"
        )
        definition = row["definition"]
        for socket, value in (
            ("Base Color", definition["rgba"]),
            ("Alpha", definition["rgba"][3]),
            ("Roughness", definition["roughness"]),
            ("Metallic", definition["metallic"]),
            ("Specular IOR Level", definition["specular"]),
        ):
            actual = shader.inputs[socket].default_value
            if isinstance(actual, float):
                color_error = max(color_error, abs(actual - value))
            else:
                color_error = max(color_error, max(abs(a - b) for a, b in zip(actual, value)))
        verified += 1
    assert len(bpy.data.materials) == len(record["created_materials"])
    assert color_error < 1e-6, color_error
    lights = sorted(o.name for o in bpy.data.objects if o.name.startswith("MATERIAL_LIGHT::"))
    assert lights == expected_added, lights
    return {
        "object_total": len(bpy.data.objects),
        "baseline_object_count": len(baseline),
        "preserved_object_count": preserved["preserved_count"],
        "added_objects": added,
        "mesh_count": len(meshes),
        "material_count": len(bpy.data.materials),
        "materials": sorted(bpy.data.materials.keys()),
        "assignments_verified": verified,
        "assignment_color_max_error": color_error,
        "render_engine": bpy.context.scene.render.engine,
        "status": "PASS",
    }


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--out", help="记录路径，默认写入审计仓库 manifests/reverify-current.json")
    parser.add_argument("--animation-baseline", help="动画原始结构基线，默认读取 Stage 2 归档证据")
    parser.add_argument("--explosion-baseline", help="Stage3原始结构及Action基线")
    args = parser.parse_args(argv)

    config = load(project_io.resolve(args.config))
    project = project_io.project(config)
    stage1 = project_io.evidence_dir(config, "stage-1")
    stage15 = project_io.evidence_dir(config, "stage-1.5")
    out = Path(args.out) if args.out else project_io.reports_dir(config) / "reverify-current.json"

    result = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "blender_version": bpy.app.version_string,
        "background": bpy.app.background,
        "project": rel(project),
        "overall": "FAIL",
    }
    try:
        assert project.is_file(), f"当前工程不存在：{project}"
        result["project_sha256"] = hashlib.sha256(project.read_bytes()).hexdigest()
        bpy.ops.wm.open_mainfile(filepath=str(project))
        animated = sorted(o.name for o in bpy.data.objects if o.animation_data)
        stage2_active = bool(bpy.context.scene.get("aeroviz_animation"))
        allowed = sorted("JOINT::"+m["joint"] for m in config.get("animation",{}).get("motions",[])) if stage2_active else []
        from animation.exploded_view import contract
        parent_overrides, extra_controllers = contract(config)
        assert animated == sorted(set(allowed)|extra_controllers), (animated,allowed)
        if stage2_active:
            bpy.context.scene.frame_set(config["animation"]["frame_start"])
        baseline = load(stage15 / "material_structure_baseline.json")
        result["stage1"] = check_stage1(load(stage1 / "validation.json"), baseline)
        result["stage1_5"] = check_stage15(load(stage15 / "material_validation.json"), baseline, animated_objects=allowed, parent_overrides=parent_overrides, additional_objects=extra_controllers)
        if stage2_active:
            from animation import kinematics
            source = project_io.resolve(args.animation_baseline) if args.animation_baseline else project_io.evidence_dir(config,"stage-2")/"structure_baseline.json"
            result["stage2"] = kinematics.validate(config,load(source))
            assert len(animated)==len(config["animation"]["motions"])+len(extra_controllers)
            assert all(not o.animation_data for o in bpy.data.objects if o.type=="MESH")
        if extra_controllers:
            from animation import exploded_view
            source = project_io.evidence_dir(config,'stage-3')/'explosion_baseline.json'
            if args.explosion_baseline:
                source = project_io.resolve(args.explosion_baseline)
            result['stage3'] = exploded_view.validate(config,load(source))
        result["objects_with_animation"] = animated
        result["object_total"] = len(bpy.data.objects)
        result["overall"] = "PASS"
    except Exception:
        result["traceback"] = traceback.format_exc()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf8")
        print("REVERIFY_FAIL")
        traceback.print_exc()
        sys.exit(1)

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf8")
    print("REVERIFY_OK", result["project_sha256"][:12], result["object_total"])
    print(json.dumps({k: result[k] for k in ("project", "overall", "object_total", "objects_with_animation")},
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
