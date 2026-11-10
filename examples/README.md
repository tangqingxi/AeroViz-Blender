# Examples

> 中文摘要：新增机型从 `configs/template.json` 开始，不要直接改通用代码。
> 完整样例是 `configs/DF4.json`。

This project ships **no model assets**, so the examples are configuration shapes rather
than runnable datasets. The complete worked example is [`configs/DF4.json`](../configs/DF4.json)
(DF4, SDF 1.5, single model, 25 visual meshes + 2 extra + 6 reference-only).

## Starting point

```powershell
Copy-Item configs\template.json configs\SHC09.json
```

Then follow [docs/model-onboarding.md](../docs/model-onboarding.md).

## Minimal SDF model

The adapter only needs a single `<model>` with `link`/`visual`/`joint` elements:

```json
{
  "model_name": "MINI",
  "adapter": "sdf",
  "input_root": "../models/mini",
  "description": "mini.sdf",
  "mesh_unit": "m",
  "sdf_unit": "m",
  "output_dir": "output/MINI",
  "blend_name": "MINI_Stage1.blend",
  "apply_model_pose": false,
  "uri_roots": {"mini": "."},
  "groups": {"AIRFRAME": ["*.STL"], "ROTOR": ["rotor*.STL"]},
  "reference_only": {},
  "extra_meshes": [],
  "unit_evidence": "STL has no unit metadata; the SDF collision box of 0.4 m matches the mesh extent.",
  "coordinate_evidence": "All link/visual poses are identity; meshes already carry assembly coordinates."
}
```

Rules of thumb:

- Every STL under `input_root` must be referenced by the description, listed in
  `extra_meshes`, or listed in `reference_only` with a reason — otherwise the build stops.
- `expected_dimensions_m` is optional but recommended: it turns a silent unit mistake
  into a failed build.
- `extra_meshes` entries always need `reason`; they have no link in the description.

## Minimal STL part list (no description file)

```json
{
  "model_name": "PART_SET",
  "adapter": "stl",
  "input_root": "../models/part_set",
  "description": null,
  "mesh_unit": "mm",
  "output_dir": "output/PART_SET",
  "blend_name": "PART_SET_Stage1.blend",
  "groups": {"PARTS": ["*.stl"]},
  "parts": [
    {"path": "body.stl", "pose": [0, 0, 0, 0, 0, 0],
     "reason": "Assembly origin from the CAD export; verified against the drawing."}
  ]
}
```

The STL adapter refuses to guess: without an explicit `pose` and `reason` per part it
raises instead of placing geometry arbitrarily.
