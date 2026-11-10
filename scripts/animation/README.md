# `scripts/animation/` — reserved, not implemented

**Nothing in this directory is implemented.** AeroViz-Blender currently stops at a
static, correctly assembled and correctly shaded project (Stage 1 and Stage 1.5).

This directory is the intended home for:

- Stage 2 — mechanical motion skeleton and independent motion tests
  (`kinematics.py`), driven by the existing `JOINT::` rig.
- Stage 3 — exploded views and mechanical animation (`explode.py`).

The parameter contract, invariants and verification requirements are specified in
[`docs/interfaces.md`](../../docs/interfaces.md). No keyframe, driver or animation data
is created by any script in this repository today.
