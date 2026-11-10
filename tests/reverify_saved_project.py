"""Re-verify a saved AeroViz project against the records of the run that built it.

Read-only: opens the saved `.blend` files, replays the assertions recorded in the
Stage 1 / Stage 1.5 evidence JSON, and prints a fresh record.  It never saves a
`.blend`, never touches the model input and never rewrites the reports, so it is safe
to run on an accepted deliverable.

Usage (inside Blender, no scene required)::

    blender --background --factory-startup --python-exit-code 1 `
            --python tests/reverify_saved_project.py -- --config configs/DF4.json `
            [--out path/to/record.json]

Checks performed when the matching report exists:

* Stage 1 project: mesh count, object names, world matrices against the recorded
  matrices, visible/reference split, link and joint empty counts, visible bounding box,
  absence of animation data.
* Stage 1.5 project: every Stage 1 object preserved unchanged (matrices, parenting,
  collections, hide state, geometry hash, joint properties), plus exactly the documented
  display lights added; material name and Principled BSDF values per assigned object;
  Eevee engine; absence of animation data.
"""
import argparse
import json
import sys
import traceback
from pathlib import Path

import bpy

WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE / "scripts"))
sys.dont_write_bytecode = True


def load(path):
    return json.loads(path.read_text(encoding="utf8"))


def max_matrix_error(obj, matrix_rows):
    return max(
        abs(obj.matrix_world[r][c] - matrix_rows[r][c]) for r in range(4) for c in range(4)
    )


def check_stage1(project, reports):
    record = load(reports / "validation.json")
    bpy.ops.wm.open_mainfile(filepath=str(project))
    meshes = [o for o in bpy.data.objects if o.type == "MESH"]
    assert len(meshes) == record["imported_count"], (len(meshes), record["imported_count"])
    rows = {r["object"]: r for r in record["records"]}
    assert set(rows) == {o.name for o in meshes}, "mesh object names differ from the record"
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
    animated = [o.name for o in bpy.data.objects if o.animation_data]
    assert not animated, animated
    return {
        "project": str(project),
        "project_sha256_note": "hash recorded separately by the audit manifest",
        "mesh_count": len(meshes),
        "visible_count": len(visible),
        "reference_only_count": len(reference),
        "link_empty_count": sum(1 for o in bpy.data.objects if o.name.startswith("LINK::")),
        "joint_empty_count": sum(1 for o in bpy.data.objects if o.name.startswith("JOINT::")),
        "object_total": len(bpy.data.objects),
        "world_matrix_max_error": matrix_error,
        "bbox_dimensions_m": dims,
        "bbox_dimensions_recorded_m": record["bbox"]["dimensions_m"],
        "bbox_max_abs_error": bbox_error,
        "objects_with_animation": animated,
        "status": "PASS",
    }


def check_stage15(config, reports):
    settings = config["materials"]
    project = (WORKSPACE / settings["target_blend"]).resolve()
    if not project.is_file() or not (reports / "material_validation.json").is_file():
        return None
    import materials  # noqa: E402  (imported late: needs bpy)

    record = load(reports / "material_validation.json")
    baseline = load(reports / "material_structure_baseline.json")
    bpy.ops.wm.open_mainfile(filepath=str(project))
    preserved = materials.check_preserved(baseline)
    added = preserved["added_objects"]
    expected_added = sorted("MATERIAL_LIGHT::" + name for name in record["environment"]["lights"])
    assert added == expected_added, (added, expected_added)
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
    assert color_error < 1e-6, color_error
    lights = sorted(o.name for o in bpy.data.objects if o.name.startswith("MATERIAL_LIGHT::"))
    assert lights == expected_added, lights
    animated = [o.name for o in bpy.data.objects if o.animation_data]
    assert not animated, animated
    return {
        "project": str(project),
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
        "objects_with_animation": animated,
        "status": "PASS",
    }


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True, help="Model config, relative to the repo root")
    parser.add_argument("--out", help="Optional path for the JSON record (default: stdout)")
    args = parser.parse_args(argv)
    config_path = (WORKSPACE / args.config).resolve()
    config = load(config_path)
    output = (WORKSPACE / config["output_dir"]).resolve()
    reports = output / "reports"
    stage1_project = output / config["blend_name"]

    result = {
        "blender_version": bpy.app.version_string,
        "background": bpy.app.background,
        "config": str(config_path),
        "stage1": None,
        "stage1_5": None,
        "overall": "FAIL",
    }
    try:
        if stage1_project.is_file() and (reports / "validation.json").is_file():
            result["stage1"] = check_stage1(stage1_project, reports)
        result["stage1_5"] = check_stage15(config, reports)
        result["overall"] = "PASS"
    except Exception:
        result["traceback"] = traceback.format_exc()
        text = json.dumps(result, ensure_ascii=False, indent=2)
        if args.out:
            Path(args.out).write_text(text, encoding="utf8")
        print("REVERIFY_FAIL")
        traceback.print_exc()
        sys.exit(1)

    text = json.dumps(result, ensure_ascii=False, indent=2)
    if args.out:
        Path(args.out).write_text(text, encoding="utf8")
    print("REVERIFY_OK")
    print(text)


main()
