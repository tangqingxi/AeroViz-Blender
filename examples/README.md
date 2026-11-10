# 示例

本仓库不分发模型资产，因此示例是**配置的形状**，而不是可直接运行的数据集。完整样例是 [`configs/DF4.json`](../configs/DF4.json)（DF4：SDF 1.5 单模型，25 个 visual 网格 + 2 个补充 + 6 个参考件）。

## 起步方式

```powershell
Copy-Item configs\template.json configs\SHC09.json
```

然后按 [docs/model-onboarding.md](../docs/model-onboarding.md) 逐项填写。

## 最小 SDF 模型

适配器只需要一个 `<model>`，内含 `link`/`visual`/`joint`：

```json
{
  "model_name": "MINI",
  "adapter": "sdf",
  "input_root": "../models/mini",
  "description": "mini.sdf",
  "mesh_unit": "m",
  "sdf_unit": "m",
  "output_dir": "output/MINI",
  "blend_name": "MINI.blend",
  "apply_model_pose": false,
  "uri_roots": {"mini": "."},
  "groups": {"AIRFRAME": ["*.STL"], "ROTOR": ["rotor*.STL"]},
  "reference_only": {},
  "extra_meshes": [],
  "unit_evidence": "STL 无单位元数据；SDF 碰撞盒 0.4 m 与网格跨度一致，据此采用米。",
  "coordinate_evidence": "所有 link/visual 位姿均为单位阵；网格自带装配坐标。"
}
```

要点：

- `input_root` 下每个 STL 必须被描述引用、列入 `extra_meshes`、或列入 `reference_only` 并给出理由，否则构建中止。
- `expected_dimensions_m` 可选但建议填：它能把"单位搞错了"从静默错误变成构建失败。
- `extra_meshes` 每项都要 `reason`；它们在描述文件里没有对应 link。

## 最小 STL 零件清单（无描述文件）

```json
{
  "model_name": "PART_SET",
  "adapter": "stl",
  "input_root": "../models/part_set",
  "description": null,
  "mesh_unit": "mm",
  "output_dir": "output/PART_SET",
  "blend_name": "PART_SET.blend",
  "groups": {"PARTS": ["*.stl"]},
  "parts": [
    {"path": "body.stl", "pose": [0, 0, 0, 0, 0, 0],
     "reason": "装配原点取自 CAD 导出；已对照图纸核对。"}
  ]
}
```

STL 适配器拒绝猜测：缺少每个零件的 `pose` 与 `reason` 时它会报错，而不是随意摆放几何。
