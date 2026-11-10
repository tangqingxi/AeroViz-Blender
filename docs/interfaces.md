# Reserved interfaces for later stages

> 中文摘要：本文件只描述**尚未实现**的后续阶段接口约定，用于保证 Stage 2/3/4 不需要
> 推翻现有结构。仓库中不存在相应的动画或渲染实现。

**Status: not implemented.** `scripts/animation/` and `scripts/rendering/` currently
contain only a README. Nothing in this repository creates keyframes, drivers, exploded
views, camera moves or video files. Stage 1 and Stage 1.5 end with a static, correctly
assembled, correctly shaded project.

These contracts exist so that later work attaches to the existing rig instead of
rewriting it.

## What already exists to build on

| Available | Meaning |
|---|---|
| `JOINT::<name>` empties | True joint frames in world space; each carries `type`, `child`, `parent`, `axis`, `axis_model`, `lower`, `upper` |
| Child meshes under a joint | Rotating a joint moves exactly the meshes it should; verified by `scripts/check_joint_hierarchy.py` |
| `LINK::<name>` empties | Description link frames, useful for frame-anchored effects |
| `SDF_MAT::*` materials | Deterministic, content-addressed, safe to reuse in renders |
| `PREVIEW_CAMERAS` | Four orthographic views already framed on the model |
| `MATERIAL_PREVIEW_LIGHTS` | Four area lights already positioned around the model |

## Stage 2 — mechanical motion skeleton

Intended entry point: `scripts/animation/kinematics.py`, invoked as
`--python scripts/animation/kinematics.py -- --config configs/<MODEL>.json`.

Proposed config block (additive; absent means "do nothing"):

```json
"animation": {
  "motions": [
    {"joint": "rotor_joint", "kind": "spin", "axis": "z",
     "rate_deg_per_s": 1200, "start": 0, "end": 240, "phase_deg": 0},
    {"joint": "cs1_joint", "kind": "sweep", "axis": "x",
     "amplitude_deg": 12, "period_s": 4, "phase_deg": 0},
    {"joint": "cs2_joint", "kind": "static", "value_deg": -8}
  ]
}
```

Contract:

- Motion is expressed per **joint name from the description**, never per mesh name.
- Limits: any commanded angle must stay inside `lower`/`upper` when those are finite;
  a violation raises instead of clipping silently.
- The script writes a **new** project version (e.g. `<MODEL>_Stage2.blend`) and never
  overwrites Stage 1 / 1.5.
- Verification must include an independent test that rotating one joint moves only its
  own descendants, and that no object gains `animation_data` it should not have.

## Stage 3 — exploded views and mechanical animation

Intended entry point: `scripts/animation/explode.py` (assignment only, no keyframes
here) plus composition in Stage 2's animation layer.

Proposed config block:

```json
"explode": {
  "grouping": "collection",
  "offset_m": 0.03,
  "gap_axis": "z",
  "order": ["REFERENCE_ONLY", "ELECTRONICS", "DUCT", "ROTOR", "TAIL", "CONTROL_SURFACES"],
  "keep_together": [["cs1", "cs11"], ["rotor", "motor"]]
}
```

Contract:

- Explosion is computed from the object's own bounds and group, and stored as a
  documented offset (keyframable later); no geometry is permanently moved.
- Hidden `REFERENCE_ONLY` parts stay excluded unless explicitly requested.
- Every explosion parameter must appear in the stage report with the resulting offsets.

## Stage 4 — camera, lighting and video rendering

Intended entry point: `scripts/rendering/render.py`.

Proposed config block:

```json
"render": {
  "engine": "BLENDER_EEVEE",
  "resolution": [1920, 1080],
  "fps": 30,
  "frame_start": 0,
  "frame_end": 240,
  "cameras": ["orbit", "front"],
  "output_dir": "output/<MODEL>/render",
  "output_format": "PNG_SEQUENCE",
  "encode_video": {"container": "mp4", "codec": "H264", "crf": 18}
}
```

Contract:

- Rendering reads a finished stage project; it never modifies geometry or rig state.
- Frames go to a git-ignored directory; only the final video and a few stills are ever
  delivered, and never committed to this repository.
- A render is not acceptance evidence on its own; a real-window screenshot of the
  same state still has to be captured for the audit record.

## Non-goals carried forward

These stay out of scope unless a later stage is explicitly authorised: physics
simulation, collision/interference analysis, manufacturing tolerances, motion planning,
and any claim that the visual result is numerically identical to Gazebo rendering.
