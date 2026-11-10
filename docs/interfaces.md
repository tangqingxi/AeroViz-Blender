# 后续阶段的预留接口

**Stage 2 已实现并验证；Stage 3/4 未实现。** 当前工程包含五个现有机械关节的运动，仍没有爆炸视图、镜头运动或视频渲染。

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

## Stage 2 —— 已实现的机械运动接口

入口 `scripts/animation/kinematics.py`，只打开现有工程、驱动已有 JOINT，不导入模型。`--config` 指定机型，`--expected-sha256` 指定写入前必须匹配的工程哈希，保存统一经 `project_io.save_project()`。

`animation` 契约：

- `root_object`：模型根对象名；`fps`、`frame_start`、`frame_end`、`interpolation=LINEAR`。
- `motions[]`：每项有描述文件关节名 `joint`，以及 `kind=spin` 或 `keyed_angles`。轴与限位从保存的关节属性读取，不配置替代轴。
- `spin`：`rate_deg_per_s`、`initial_angle_deg`、`start_frame`、`end_frame`。速度仅为演示配置。
- `keyed_angles`：按帧递增的 `keys[{frame,angle_deg,marker?}]`，对角度进行分段线性采样。起始帧必须零位，演示末尾需配置返回零位。
- `expected_axis_model`、`expected_center_m`、`expected_meshes`：对既有骨架的断言，任何不一致报错，不用于覆盖既有轴或中心。`test_angles_deg` 指定独立试验角度。
- `tolerances`：世界矩阵、轴、角度的验证阈值；`gui_samples`：需要截图的命名帧。

算法：先以根对象纯旋转将 `axis_model` 转世界，再以关节世界纯旋转的逆变换转局部并归一化，检查反向变换的有符号方向。保存 q0，以 `q0 × q_delta(local_axis,angle)` 驱动。根与关节允许正均匀缩放；零/负/非均匀缩放或剪切显式拒绝。当前版本也拒绝受控关节级联，防止把独立关节验证错误地推广到任意机械臂。

Blender 5.0.1 的 Action 经 `layers → strips → channelbag(action_slot) → fcurves` 操作，每个关节独立 Action、四个 Quaternion 通道。全部整数帧采样后写 LINEAR 关键帧，并保持相邻 Quaternion 符号连续；原始关键角度和 Timeline Markers 来自配置。帧间分量线性插值经归一化后不等同于严格匀角速，验收范围明确为全部整数帧及连续无反转的帧间姿态。

验证/更新顺序：

1. 原件哈希及 Stage 1/1.5 历史回归；字节备份到 `.work/stage-2/rollback/`。
2. 字节副本先做每个关节的独立正负/恢复试验，再生成组合动画。
3. 世界坐标 Rodrigues 参考与实际依赖图求值逐帧比较，包括全部对象、正轴方向、原点及累计转角；独立进程重开副本并回归。
4. 正式原件仍匹配哈希时，用同一引擎生成并验证，再原子保存；新进程重开与历史回归失败即恢复备份并停止。
5. 实际图形窗口使用原生播放命令，连续采样证明时间轴真实推进和循环，再截图六种状态。GUI 不保存。

`tests/reverify_saved_project.py` 保留历史几何、矩阵、包围盒、材质断言，在第1帧检查，只受控允许配置中五个 JOINT 的动画标志改变。其他字段仍严格比较；历史无动画工程仍按原规则检查。当前动画工程的完整逐帧回归基线在 Audit `stages/stage-2/evidence/structure_baseline.json`。

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

- 渲染只读当前工程；不修改几何或骨架状态。
- 帧序列写入工程之外的临时目录，只有最终视频与少量静帧保留；两者都不提交到本仓库。
- 渲染本身不算验收证据；同一状态仍需真实窗口截图进入审计记录。

## 一以贯之的非目标

除非另行授权，以下始终不在范围内：物理仿真、碰撞/干涉分析、制造公差、运动规划，以及任何"视觉结果与 Gazebo 渲染数值等价"的声明。
