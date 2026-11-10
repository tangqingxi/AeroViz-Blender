# AeroViz-Blender

**AeroViz** is a platform for aircraft 3D visualisation and animation toolchains.
**Blender** is the current implementation backend.
**DF4** (ducted-fan UAV) is the first validation case — the architecture is not bound to it.

AeroViz-Blender rebuilds a flyable-looking aircraft assembly inside Blender from the
model descriptions and mesh sets that already exist for simulation (SDF/URDF-style
descriptions plus STL geometry), restores assembly poses and joint frames, recovers
SDF materials, and will grow into kinematic motion, exploded views and rendered video.

> 平台名称是 AeroViz，Blender 是当前实现平台，DF4 只是第一个验证机型。后续机型
> （如 SHC09）通过新增配置接入，不需要修改通用代码。

---

## 1. Project Overview

Flight-simulation and CAD pipelines carry an aircraft as a machine description plus a
pile of meshes. That data is complete but not *presentable*: it is hard to inspect
visually, impossible to animate, and it cannot be turned into a video. AeroViz-Blender
closes that gap:

- **Import** a single-model description, resolve link/visual/joint frames explicitly,
  and place every mesh at its true assembly position.
- **Preserve** engineering truth: no auto-centring, no guessed units, no silent
  approximation. Every placement decision is recorded with its evidence.
- **Recover** materials from the description (diffuse/specular/transparency/scripted
  material names) into a glTF/Principled-style shader.
- **Verify** what was built by reopening the saved project in a real graphical Blender
  process, screenshotting it, and re-checking transforms and material bindings.
- **Extend** to kinematics, exploded views and rendered video in later stages.

The project separates three kinds of content that are usually tangled:

| Kind | Lives in | Rule |
|---|---|---|
| Generic automation | `scripts/`, `adapters/` | Must contain no aircraft name, part name or path |
| Aircraft-specific data | `configs/<MODEL>.json` | All naming, grouping, units, overrides and evidence |
| Verified evidence | separate audit repository | Reports, screenshots, hashes, acceptance records |

## 2. Core Capabilities

Implemented and verified today (Stage 1 and Stage 1.5):

- **Config-driven import.** One JSON config per aircraft; the engine reads nothing
  aircraft-specific from code.
- **SDF (single-model) adapter.** `link` / `visual` / `joint` / `frame` poses, radian
  RPY, `expressed_in`, `relative_to`, `model://` URI mapping, external-include
  accounting, multi-parent and cyclic-joint rejection.
- **STL adapter.** Blender-native import at true scale (`m` / `mm` / `cm`), source
  coordinates preserved, no re-centring.
- **Assembly reconstruction.** Collection layout by functional group, `LINK::` /
  `JOINT::` empties that keep true joint centres, axes and limits, parent/child
  hierarchy rebuilt from the description.
- **Duplicate and merge auditing.** Triangle-level geometry comparison at micrometre
  precision; merged or repeated reference meshes are hidden instead of deleted, and
  their triangle coverage by visible parts must reach 100 %.
- **Input integrity.** Per-file SHA-256 snapshot before and after; the build refuses to
  finish if any input byte changed.
- **Material recovery.** SDF diffuse/specular/ambient/transparency/emissive plus Gazebo
  named script materials, deterministic reuse by content signature, idempotent
  re-application, explicit `reason` required for any manual override.
- **Structural preservation check.** Stage 1.5 must leave every pre-existing object's
  matrices, parenting, collections, hide state, geometry hash and joint properties
  unchanged.
- **Graphical acceptance.** Dedicated scripts reopen the saved `.blend` in a real
  Blender window, assert the expected state and capture screenshots. Background
  rendering alone is explicitly not accepted as visual proof.

Not implemented yet (do not assume these exist): mechanical motion, keyframed
animation, exploded views, camera/light choreography, video rendering, multi-aircraft
batch processing. See the roadmap in §7.

## 3. Architecture

```
configs/<MODEL>.json          aircraft-specific: input root, units, grouping,
        │                     reference parts, overrides, evidence text
        ▼
scripts/main.py               entry point: boundary checks, adapter selection,
        │                     build, validation, save
        ├── adapters/         format layer: description → neutral scene data
        │     import_sdf.py   single-model SDF 1.5  (joints, frames, URIs)
        │     import_stl.py   explicit part list    (no assembly guessing)
        │
        ├── scripts/scene_builder.py   neutral scene data → Blender collections,
        │                              LINK::/JOINT:: hierarchy, four-view previews
        ├── scripts/validation.py      input snapshot, geometry inventory,
        │                              duplicate/coverage audit, report writer
        │
        └── output/<MODEL>/            .blend project, preview/, reports/

scripts/materials.py          Stage 1.5: SDF materials → Principled BSDF, applied to
                              an existing Stage 1 project, saved as a new version
scripts/gui_verify*.py        graphical reopen + screenshot acceptance
scripts/check_joint_hierarchy.py   independent joint transmission check
tests/                        mapping/priority unit checks (run inside Blender)
```

**The adapter contract is the seam.** An adapter returns a neutral dict
(`parts`, `links`, `joints`, `includes`, `model_pose`) and the scene builder consumes
only that. Adding a description format means adding one module and one registry entry
in `adapters/__init__.py`; adding an aircraft means adding one config file. Neither
requires editing the other.

**Invariants** the code enforces rather than documents:

- Model input directories are read-only; input hashes are compared before and after.
- Outputs must stay inside the repository workspace (`output/`), never inside the input.
- Unreferenced meshes must be declared in `reference_only` with a reason, or the build
  fails — no mesh is ever dropped silently.
- Rotations must be radian RPY; `degrees="true"`, quaternion poses, nested models,
  loops/multi-parent joints and non-mesh visuals raise instead of approximating.
- A reference mesh may only be hidden if visible parts cover 100 % of its unique
  triangles.

## 4. Supported Model Formats

| Format | Status | Notes |
|---|---|---|
| SDF 1.5, single `<model>` | Supported | `adapter: "sdf"`; pose frame semantics per SDFormat 1.5 |
| SDFormat with `{% %}` Jinja control flow | Rejected with an error | Expand the template first with trusted parameters |
| Nested models / `include`d models | Rejected | Only accounted for when explicitly listed in `ignored_includes` |
| STL part list (no description) | Supported | `adapter: "stl"`; every part needs an explicit pose and reason |
| SDF with non-mesh visuals (box/sphere/cylinder) | Rejected | Not silently skipped |
| URDF, STEP, OBJ, FBX, glTF | Not yet | Add an adapter; config selects it |

Mesh units are declared, never inferred: STL supports `m` / `mm` / `cm`, SDF defaults
to metres. Blender runs metric with `scale_length = 1`.

## 5. Project Structure

```text
AeroViz-Blender/
├── README.md
├── .gitignore                  excludes build output and third-party model assets
├── configs/
│   ├── DF4.json                the exact config used for the audited Stage 1/1.5 runs
│   └── template.json           starting point for a new aircraft
├── adapters/
│   ├── __init__.py             adapter registry (sdf, stl)
│   ├── import_sdf.py
│   └── import_stl.py
├── scripts/
│   ├── main.py                 Stage 1 entry point
│   ├── materials.py            Stage 1.5 entry point (also importable as a module)
│   ├── scene_builder.py        collections, hierarchy, previews
│   ├── validation.py           integrity and audit records
│   ├── gui_verify.py           Stage 1 graphical acceptance
│   ├── gui_verify_materials.py Stage 1.5 graphical acceptance
│   ├── check_joint_hierarchy.py
│   ├── animation/              reserved for Stage 2/3 — interface only, no code
│   └── rendering/              reserved for Stage 4 — interface only, no code
├── assets/
│   └── materials/
│       └── gazebo_standard.json   Gazebo Classic script-material colour summary
├── docs/
│   ├── architecture.md
│   ├── model-onboarding.md     how to add SHC09 or any other airframe
│   ├── interfaces.md           reserved interfaces for later stages
│   └── asset-provenance.md     model provenance and licence status
├── examples/
│   └── README.md
├── tests/
│   ├── test_material_mapping.py     mapping priority / colour space / ambiguity
│   └── reverify_saved_project.py    read-only re-verification of a saved project
└── output/                     generated, git-ignored (projects, previews, reports)
```

`output/` is intentionally not versioned: it holds multi-megabyte `.blend` projects,
render frames and per-run reports. Large project files stay local until a Git LFS or
Release delivery policy is agreed.

## 6. Getting Started

Requirements: Blender **5.0.1** (5.x; the code targets the Blender Python API present in
5.0) on Windows. No extra Python packages — Blender's bundled interpreter is enough.
Set `$B` to the Blender executable in the snippets below.

Stage 1 — import and assembly recovery (DF4):

```powershell
& $B --background --factory-startup --python-exit-code 1 `
     --python '.\scripts\main.py' -- --config configs/DF4.json
```

Stage 1.5 — recover SDF materials into a new project version:

```powershell
& $B --background --factory-startup --python-exit-code 1 `
     --python '.\scripts\materials.py' -- --config configs/DF4.json
```

Graphical acceptance (must run with a real window, not `--background`):

```powershell
& $B -W '.\output\DF4\DF4_Stage1.blend'   --python '.\scripts\gui_verify.py'
& $B -W '.\output\DF4\DF4_Stage1_5.blend' --python '.\scripts\gui_verify_materials.py'
```

Independent joint-transmission check and mapping unit checks:

```powershell
& $B --background --factory-startup --python-exit-code 1 `
     --python '.\scripts\check_joint_hierarchy.py'
& $B --background --factory-startup --python-exit-code 1 `
     --python '.\tests\test_material_mapping.py'
```

Re-verify an accepted project against the records of the run that produced it
(read-only; opens both stages, replays every recorded assertion, saves nothing):

```powershell
& $B --background --factory-startup --python-exit-code 1 `
     --python '.\tests\reverify_saved_project.py' -- --config configs/DF4.json
```

Expect `STAGE1_IMPORT_OK`, `MATERIAL_STAGE_OK 7 33`, `JOINT_HIERARCHY_OK 5`,
`MATERIAL_MAPPING_TESTS_OK` and `REVERIFY_OK` respectively. All output paths resolve
relative to the repository root; the model input directory is only read.

To build a different aircraft, copy `configs/template.json` and follow
[docs/model-onboarding.md](docs/model-onboarding.md).

## 7. Development Roadmap

| Stage | Scope | Status |
|---|---|---|
| Stage 1 | Generic model import and spatial assembly recovery | Done |
| Stage 1.5 | SDF material recovery | Done |
| Stage 2 | Mechanical motion skeleton and independent motion tests | Pending |
| Stage 3 | Exploded views and mechanical animation | Pending |
| Stage 4 | Camera, lighting and video rendering | Pending |
| Stage 5 | Multi-aircraft adaptation and tooling polish | Pending |

Stage 1 and Stage 1.5 are complete for DF4 and were accepted against evidence in the
separate audit repository. No later stage has started; nothing in this repository
animates, explodes or renders video yet.

## 8. Current Status

- Validated on Blender 5.0.1, Windows, DF4 as the only airframe so far.
- Stage 1: 33 STL inputs → 33 independent mesh objects, 27 visible + 6 hidden
  reference parts, overall visible extent ≈ 0.353 × 0.376 × 0.378 m, 26 link empties and
  25 joint empties, world-matrix error 0 against the description, input hashes
  unchanged before/after.
- Stage 1.5: 25 SDF visual materials extracted (25 with explicit definitions),
  7 Blender materials created and reused by content signature, 33 mesh objects assigned
  (13 explicit RGBA, 12 Gazebo named script, 8 display default), all 89 pre-existing
  objects preserved unchanged, Eevee and Material Preview captures taken in a real
  window.
- Stage 2 (mechanical motion) has not started and requires explicit authorisation.

Detailed stage reports, screenshots and artefact hashes live in the companion audit
repository `tangqingxi/AeroViz-Blender-Audit`, not here.

## Licence and third-party assets

This repository contains **no** model assets, no `.blend` projects and no rendered
frames. The DF4 geometry is third-party material whose redistribution terms are not
established; see [docs/asset-provenance.md](docs/asset-provenance.md).

The project's own licence is **not yet chosen**, so no `LICENSE` file is included.
Until one is confirmed, the default of "all rights reserved" applies to this code.
