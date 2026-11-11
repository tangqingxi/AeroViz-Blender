# 后续阶段的预留接口

**Stage 2与Stage 3已实现并验证；Stage 4未实现。** 当前工程保留五个机械关节动画，并增加独立爆炸/恢复位移层；没有相机运动或最终视频渲染。

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

## Stage 3 —— 已实现坐标冻结与爆炸/恢复

- `scripts/coordinate_frames.py`：读取 `coordinate_frames`，验证正交且det=+1的3x3旋转，转换向量，验证单位基与往返；不处理NED或CG推定。
- `scripts/animation/exploded_view.py`：读取 `exploded_view`，在既有JOINT上方增加独立偏移层，绝不调用Stage2机械build。
- `branches[]`：`joint`、`parent`、`child_link`、`meshes`是对原子树的约束；`group`只用于管理，不声称新的机械连接；`direction_flu`、`distance_m`、`displacement_flu_m`必须一致，并写 `reason`。
- 全局时间参数：`frame_start`、`mechanical_end`、`fully_exploded`、`hold_end`、`frame_end`；所有控制器只在这五个帧上写三轴Location。`coordinate_frame`、`root_object`、Collection名、控制器前缀及截图帧均可配置。
- 方向采用模型向量→世界向量→父级局部位移，不施加平移原点，支持不同模型层级。配置必须明确覆盖全部有网格JOINT，空子树/参考件拒绝；未知父级与原子树变化立即报错。
- 每个控制器初始单位姿态并归零，保持旧JOINT的matrix_basis和matrix_parent_inverse，原Action内存身份在构建前后不变，保存后按关键帧/插值/句柄/外推/自定义属性指纹复核。
- 爆炸回归逐整数帧检查机械末帧之后的刚体平移、非目标不动、保持段和最终恢复；原机械Action在121之后按原外推保持，不延长或重做。
- `tests/reverify_saved_project.py`保留旧检查，仅扩展配置白名单：声明的控制器、24个关节父级变更及总帧数；其余原对象字段仍逐项检查。完整动画工程需要Audit的Stage3结构与Action基线。

## Stage 4.0 —— 已实现的展示原型

当前实际入口、独立Scene/NLA契约、逐帧回归和原子保存见 [展示层接口](stage4-presentation.md)。用户操作见 [验收说明](stage4-acceptance.md)。本阶段的验收素材为干净Eevee渲染和低清MP4，GUI截图只证明布局和播放。

### 后续完整渲染接口草案（尚未授权）

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
- Stage4.0的最终展示证据使用干净渲染画面；真实窗口单独验证打开、布局与播放，不替代最终素材。

## 一以贯之的非目标

除非另行授权，以下始终不在范围内：物理仿真、碰撞/干涉分析、制造公差、运动规划，以及任何"视觉结果与 Gazebo 渲染数值等价"的声明。
