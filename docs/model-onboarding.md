# Onboarding a new aircraft (e.g. SHC09)

> 中文摘要：新增机型只改配置，不改通用代码。复制 `configs/template.json`，填写
> 输入根目录、单位依据、分组、参考件与额外零件，然后按顺序执行 Stage 1 / 1.5，
> 并用图形进程复验。

The engine has no aircraft-specific code. A new airframe is one JSON file plus a
verification run. DF4 (`configs/DF4.json`) is a complete worked example.

## 0. Prepare the input

- Keep the upstream model directory **outside** this repository and read-only.
- You need the machine description (SDF/URDF) and every mesh it references.
- Record where the data came from and its licence status in
  [asset-provenance.md](asset-provenance.md) before publishing anything.

## 1. Copy the template

```powershell
Copy-Item configs\template.json configs\SHC09.json
```

## 2. Fill the description-level fields

| Key | Meaning |
|---|---|
| `model_name` | Short airframe id; used for the root empty and output paths. No spaces |
| `adapter` | `"sdf"` for a single-model SDF, `"stl"` for an explicit part list |
| `input_root` | Absolute path, or a path relative to the repository root |
| `description` | Description file relative to `input_root` (`null` for the STL adapter) |
| `mesh_unit` | `"m"`, `"mm"` or `"cm"` — the unit the **mesh** coordinates are in |
| `sdf_unit` | Unit of the **description** pose values; SDFormat is metres |
| `output_dir`, `blend_name` | Output project location, relative to the repository root |
| `apply_model_pose` | `false` keeps the model origin (no simulated flight height baked in) |
| `uri_roots` | `model://<id>` → directory mapping under `input_root` |
| `ignored_includes` | External includes you deliberately do not model, **each with a reason** |
| `expected_dimensions_m` | Per-axis `[min, max]` sanitiser for the overall visible size |
| `coordinate_evidence`, `unit_evidence` | Short written justification copied into the report |

Units and coordinates are never inferred. If you cannot state the evidence, the correct
move is to stop and measure, not to guess.

## 3. Classify the parts

- `groups` maps functional groups to glob patterns (`"DUCT": ["duct-*.STL"]`). Unmatched
  files land in `UNCLASSIFIED` rather than disappearing.
- `reference_only` maps file name → reason. Use it for merged assemblies and exact
  duplicates. The build then *proves* that visible parts cover 100 % of their unique
  triangles before allowing them to be hidden.
- `extra_meshes` lists meshes that exist on disk but are not referenced by the
  description. Each needs `path`, `pose` and `reason`; they are attached to the model
  root because no link is known.

## 4. Fill the materials block

`materials.source_blend` and `target_blend` wire Stage 1.5 to the Stage 1 project.
Keep `source_color_space` explicit and justified: `"linear"` preserves raw values,
`"srgb"` applies the standard piecewise decode.

Rules the code enforces:

- `overrides` must carry a `reason`; an override is recorded as `config_override`, never
  presented as the original colour.
- `object_visuals` disambiguates a mesh reused by several visuals with different colours;
  an ambiguous match raises instead of picking arbitrarily.
- Unknown script materials keep an existing foreign material if one exists, otherwise
  fall back to the documented neutral display default.
- Add newly confirmed Gazebo script materials to `assets/materials/gazebo_standard.json`
  instead of hard-coding colours in the material engine.

## 5. Run and verify

```powershell
$B = '<blender.exe>'
& $B --background --factory-startup --python-exit-code 1 --python .\scripts\main.py -- --config configs\SHC09.json
& $B --background --factory-startup --python-exit-code 1 --python .\scripts\materials.py -- --config configs\SHC09.json
& $B -W .\output\SHC09\SHC09_Stage1.blend --python .\scripts\gui_verify.py
& $B -W .\output\SHC09\SHC09_Stage1_5.blend --python .\scripts\gui_verify_materials.py
```

Then look at the screenshots. A file existing is not visual acceptance.

## 6. Checklist before reporting the stage

- [ ] `expected_dimensions_m` matches the measured extent and the numbers are explained.
- [ ] Every hidden reference part has a reason and 100 % triangle coverage.
- [ ] Every `extra_meshes` entry states why the description does not define it.
- [ ] Input SHA-256 snapshot unchanged before/after (the build asserts this).
- [ ] Stage 1.5 reports 89/89-style preservation for *this* project (all prior objects).
- [ ] Materials: count of explicit RGBA / named script / display default objects known.
- [ ] Screenshots reviewed, not just produced.
- [ ] Reports and evidence go to the **audit** repository, never this one.

## 7. Expected data for a ducted-fan airframe

For reference, DF4 produced: 25 SDF visuals + 2 unreferenced extra meshes + 6 hidden
reference meshes = 33 mesh objects; 26 link empties; 25 joint empties (20 fixed,
5 with meshed children on revolute joints). A different airframe will differ — do not
copy those numbers as expectations.
