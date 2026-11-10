# 后续阶段的预留接口

**状态：未实现。** `scripts/animation/` 与 `scripts/rendering/` 目前只有一份 README。本仓库中没有任何脚本创建关键帧、驱动器、爆炸视图、镜头运动或视频文件。Stage 1 与 Stage 1.5 结束时是一个静止的、装配正确、着色正确的工程。

本文存在的目的：让后续工作**挂在现有骨架上**，而不是推翻它重做。

## 现有可复用的东西

| 已有 | 含义 |
|---|---|
| `JOINT::<名称>` 空对象 | 世界坐标下的真实关节坐标系；每个携带 `type`、`child`、`parent`、`axis`、`axis_model`、`lower`、`upper` |
| 关节下的子网格 | 旋转关节时只有它该动的网格动；已由 `scripts/check_joint_hierarchy.py` 验证 |
| `LINK::<名称>` 空对象 | 描述文件 link 坐标系，可用于以坐标系为锚点的效果 |
| `SDF_MAT::*` 材质 | 确定性、按内容寻址，渲染时可安全复用 |
| `PREVIEW_CAMERAS` | 已对准模型的四个正交视角 |
| `MATERIAL_PREVIEW_LIGHTS` | 已布置在模型周围的四盏面积灯 |

## Stage 2 —— 机械运动骨架

预期入口：`scripts/animation/kinematics.py`，调用方式
`--python scripts/animation/kinematics.py -- --config configs/<MODEL>.json`。

建议的配置块（纯增量；缺省即"什么都不做"）：

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

契约：

- 运动按**描述文件中的关节名**表达，绝不按网格名。
- 限位：命令角度必须落在 `lower`/`upper`（有限时）之内；越界报错，不静默裁剪。
- 脚本写出**新的**工程版本（如 `<MODEL>_Stage2.blend`），绝不覆盖 Stage 1 / 1.5。
- 验证必须包含独立测试：旋转某个关节只移动它自己的后代，且没有对象凭空获得 `animation_data`。

## Stage 3 —— 爆炸视图与机械动画

预期入口：`scripts/animation/explode.py`（只负责分配，不在此键帧）加 Stage 2 的动画层组合。

建议的配置块：

```json
"explode": {
  "grouping": "collection",
  "offset_m": 0.03,
  "gap_axis": "z",
  "order": ["REFERENCE_ONLY", "ELECTRONICS", "DUCT", "ROTOR", "TAIL", "CONTROL_SURFACES"],
  "keep_together": [["cs1", "cs11"], ["rotor", "motor"]]
}
```

契约：

- 爆炸位移由对象自身包围盒与分组计算，并作为**有记录的偏移**保存（后续可键帧）；不永久移动几何。
- 隐藏的 `REFERENCE_ONLY` 件默认排除，除非显式要求。
- 每个爆炸参数都要连同产生的偏移量写进阶段报告。

## Stage 4 —— 镜头、灯光与视频渲染

预期入口：`scripts/rendering/render.py`。

建议的配置块：

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

契约：

- 渲染只读一个已完成的阶段工程；不修改几何或骨架状态。
- 帧序列写入被 git 忽略的目录；只交付最终视频与少量静帧，且不提交到本仓库。
- 渲染本身不算验收证据；同一状态仍需真实窗口截图进入审计记录。

## 一以贯之的非目标

除非另行授权，以下始终不在范围内：物理仿真、碰撞/干涉分析、制造公差、运动规划，以及任何"视觉结果与 Gazebo 渲染数值等价"的声明。
