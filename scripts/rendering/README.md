# `scripts/rendering/` — reserved, not implemented

**Nothing in this directory is implemented.** No camera choreography, no lighting setup
for production and no video encoding exists in this repository yet.

This directory is the intended home for Stage 4 — camera, lighting and video rendering
(`render.py`), consuming a finished stage project without modifying geometry or rig state.

The parameter contract and the evidence rules (a render is not acceptance evidence on
its own) are specified in [`docs/interfaces.md`](../../docs/interfaces.md).

The four orthographic `VIEW::*` cameras and the four `MATERIAL_LIGHT::*` area lights
that already exist are *preview* assets produced by Stage 1 / Stage 1.5, not a rendering
pipeline.
