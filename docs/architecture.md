# Architecture

> 中文摘要：配置驱动 + 适配器分层。适配器把机型描述文件转成中性场景数据，场景构建器
> 只消费这份数据；机型差异全部收敛在 `configs/<MODEL>.json`。

## Layers

```
            +---------------------------------------------------+
            | configs/<MODEL>.json    aircraft-specific data     |
            +---------------------------------------------------+
                      |                          ^
                      v                          |
  +-----------------------------+     +------------------------------+
  | adapters/<format>.py        |     | assets/materials/*.json      |
  | description -> neutral data |     | known script-material colours|
  +-----------------------------+     +------------------------------+
                      |
                      v  neutral data contract
  +-----------------------------------------------------------------+
  | scripts/scene_builder.py   collections, LINK::/JOINT::, previews |
  +-----------------------------------------------------------------+
                      |
                      v
  +-----------------------------------------------------------------+
  | scripts/validation.py      integrity, duplicate audit, records   |
  +-----------------------------------------------------------------+
                      |
                      v
  +-----------------------------------------------------------------+
  | output/<MODEL>/            .blend, preview/, reports/            |
  | scripts/materials.py       Stage 1.5 reads Stage 1, writes a new |
  |                            project version, never overwrites it  |
  +-----------------------------------------------------------------+
```

## Module responsibilities

| Module | Owns | Must not own |
|---|---|---|
| `scripts/main.py` | CLI, workspace/input boundary checks, adapter selection, save | Format parsing, aircraft names |
| `adapters/import_sdf.py` | SDF 1.5 parsing, pose-frame resolution, URI mapping | Blender scene mutation |
| `adapters/import_stl.py` | STL import at declared scale, one object per part | Assembly inference |
| `adapters/__init__.py` | Format registry (`ADAPTERS`) | Parsing logic |
| `scripts/scene_builder.py` | Collections, parenting, joint empties, preview cameras/renders | Reading description files |
| `scripts/validation.py` | Input snapshots, geometry inventory, duplicate/coverage audit, report text | Deciding aircraft semantics |
| `scripts/materials.py` | SDF material extraction, Principled BSDF construction, assignment, preservation checks | Importing geometry, creating animation |
| `scripts/gui_verify*.py` | Graphical reopen, assertions, screenshots | Saving or modifying the project |
| `scripts/check_joint_hierarchy.py` | Independent joint transmission proof | Persisting any rotation |

## The neutral data contract

Every adapter returns the same dict; `scene_builder.build()` consumes only this:

```python
{
  "parts": [
    {"file": "<abs path>", "link": "link_name" | None,
     "scale": [sx, sy, sz],
     "matrix": Matrix(4x4) | None,     # world placement of the mesh
     "pose": [x, y, z, r, p, y],       # alternative to matrix
     "reason": "<why this placement is justified>"}
  ],
  "links":  {"<name>": {"matrix": Matrix, "inertial_pose": "..."}},
  "joints": [{"name", "type", "child", "parent", "axis", "axis_frame",
              "lower", "upper", "matrix", "axis_model"}],
  "includes": [...],          # external includes encountered
  "ignored_joints": [...],    # joints inside includes, explicitly skipped
  "model_pose": Matrix,
}
```

`reason` is mandatory for any part whose placement is not directly given by the
description; it is copied into the object's `coordinate_reason` custom property and
into the audit report.

## Naming conventions inside the scene

| Prefix / collection | Meaning |
|---|---|
| `<MODEL>_ROOT` | Root empty for the assembly |
| `LINK::<name>` | Empty at a description link frame |
| `JOINT::<name>` | Empty at a joint frame; carries `type`, `child`, `parent`, `axis`, `axis_model`, `lower`, `upper` |
| `REFERENCE_ONLY` collection | Hidden merged/duplicate meshes kept for auditability |
| `LINKS_AND_JOINTS` collection | The rig; hidden by default so it never occludes geometry |
| `PREVIEW_CAMERAS` collection | Orthographic view cameras (`VIEW::isometric`, `front`, `top`, `side`) |
| `MATERIAL_PREVIEW_LIGHTS` | Display lights added by Stage 1.5 only |
| `SDF_MAT::<label>::<hash>` | Generated material, named by content signature for deterministic reuse |

## Enforced invariants

1. **Inputs are read-only.** `validation.snapshot()` hashes every input file before and
   after; a single byte difference aborts the run.
2. **Outputs stay in the workspace.** Any output path resolving outside the repository
   root, or inside the input root, raises.
3. **No silent drops.** Every STL found under the input root must be either referenced
   by the description, listed in `extra_meshes`, or listed in `reference_only` with a
   reason.
4. **Hidden references must be provably redundant.** A reference mesh is only allowed
   if the union of visible parts covers 100 % of its unique triangles at 1e-6 precision.
5. **No guessed transforms.** Matrices are compared against the description targets to
   1e-6; `matrix_parent_inverse` is reset explicitly so parenting cannot accumulate drift.
6. **Stage 1.5 is additive.** Every pre-existing object's world/local matrices, parent,
   parent-inverse, collections, hide state, geometry hash and joint properties are
   compared before and after; only documented display lights may be added.
7. **Idempotent materials.** Applying materials twice must produce the same material
   set and the same slot bindings.

## Why no framework

The whole engine is a handful of modules with one data contract and a registry. There is
no plugin system, no event bus and no scene abstraction layer: those would add
indirection without removing any of the real work, which is exact frame math and honest
auditing. Later stages (kinematics, exploded views, rendering) are expected to add
modules that consume the existing `JOINT::` rig rather than restructure the pipeline.
