# 架构设计

分层、数据契约与代码强制的约束。README 讲项目整体，本文讲**要改代码或加模块时**需要知道的细节。

## 分层

```
            +---------------------------------------------------+
            | configs/<MODEL>.json    机型专属数据              |
            +---------------------------------------------------+
                      |                          ^
                      v                          |
  +-----------------------------+     +------------------------------+
  | adapters/<格式>.py          |     | assets/materials/*.json      |
  | 描述文件 → 中性场景数据     |     | 已知脚本材质的数值摘要       |
  +-----------------------------+     +------------------------------+
                      |
                      v  中性数据契约
  +-----------------------------------------------------------------+
  | scripts/scene_builder.py   Collection、LINK::/JOINT::、预览     |
  +-----------------------------------------------------------------+
                      |
                      v
  +-----------------------------------------------------------------+
  | scripts/validation.py      完整性、重复审计、报告记录            |
  +-----------------------------------------------------------------+
                      |
                      v
  +-----------------------------------------------------------------+
  | output/<MODEL>/            .blend、preview/、reports/            |
  | scripts/materials.py       Stage 1.5 读取 Stage 1，另存新版本，  |
  |                            绝不覆盖旧工程                        |
  +-----------------------------------------------------------------+
```

## 模块职责

| 模块 | 负责 | 不得负责 |
|---|---|---|
| `scripts/main.py` | 命令行、工作区/输入边界检查、选择适配器、保存 | 解析格式、出现机型名称 |
| `adapters/import_sdf.py` | SDF 1.5 解析、位姿坐标系求解、URI 映射 | 改动 Blender 场景 |
| `adapters/import_stl.py` | 按声明单位导入 STL，一件零件一个对象 | 推断装配关系 |
| `adapters/__init__.py` | 格式注册表（`ADAPTERS`） | 解析逻辑 |
| `scripts/scene_builder.py` | Collection、父子层级、关节空对象、预览相机与渲染 | 读取描述文件 |
| `scripts/validation.py` | 输入快照、几何清单、重复与覆盖率审计、报告文本 | 决定机型语义 |
| `scripts/materials.py` | SDF 材质提取、Principled BSDF 构建、分配、结构保护 | 导入几何、创建动画 |
| `scripts/gui_verify*.py` | 图形进程重开、断言、截图 | 保存或修改工程 |
| `scripts/check_joint_hierarchy.py` | 独立验证关节传递 | 持久化任何旋转 |

## 适配器契约（中性场景数据）

每个适配器返回同一个字典，`scene_builder.build()` 只消费它：

```python
{
  "parts": [
    {"file": "<绝对路径>", "link": "link 名" | None,
     "scale": [sx, sy, sz],
     "matrix": Matrix(4x4) | None,     # 网格的世界放置矩阵
     "pose": [x, y, z, r, p, y],       # 与 matrix 二选一
     "reason": "<这个放置为什么成立>"}
  ],
  "links":  {"<名称>": {"matrix": Matrix, "inertial_pose": "..."}},
  "joints": [{"name", "type", "child", "parent", "axis", "axis_frame",
              "lower", "upper", "matrix", "axis_model"}],
  "includes": [...],          # 遇到的外部 include
  "ignored_joints": [...],    # include 内被显式跳过的关节
  "model_pose": Matrix,
}
```

`reason` 对任何"描述文件没有直接给出"的放置都是必填项；它会被写入对象的 `coordinate_reason` 自定义属性，并进入审计报告。

## 场景内命名约定

| 前缀 / Collection | 含义 |
|---|---|
| `<MODEL>_ROOT` | 装配体根空对象 |
| `LINK::<名称>` | 位于描述文件 link 坐标系上的空对象 |
| `JOINT::<名称>` | 位于关节坐标系上的空对象；携带 `type`、`child`、`parent`、`axis`、`axis_model`、`lower`、`upper` |
| `REFERENCE_ONLY` collection | 合并件/重复件，隐藏但保留，便于审计 |
| `LINKS_AND_JOINTS` collection | 骨架；默认隐藏，避免遮挡几何 |
| `PREVIEW_CAMERAS` collection | 正交视角相机（`VIEW::isometric`、`front`、`top`、`side`） |
| `MATERIAL_PREVIEW_LIGHTS` | Stage 1.5 新增的展示灯 |
| `SDF_MAT::<label>::<hash>` | 生成的材质，按内容签名命名以便确定性复用 |

## 代码强制的约束

1. **输入只读**：`validation.snapshot()` 在构建前后对每个输入文件求哈希，任一字节不同即中止。
2. **输出留在工作区**：解析到仓库根之外、或落在输入目录内的输出路径一律报错。
3. **不静默丢弃**：输入根下每个 STL 必须被描述引用、列入 `extra_meshes`、或列入 `reference_only` 并给出理由。
4. **隐藏件必须可证明冗余**：参考件只有在可见零件的并集覆盖其 100% 独特三角面（1e-6 精度）时才允许隐藏。
5. **不猜变换**：世界矩阵与描述目标逐元素比较到 1e-6；显式重置 `matrix_parent_inverse`，避免父子关系累积漂移。
6. **Stage 1.5 只做加法**：原有对象的世界矩阵/局部矩阵、父对象、父逆矩阵、Collection、隐藏状态、几何哈希、关节属性前后比对，唯一允许新增的是有记录的展示灯。
7. **材质幂等**：同一配置连续执行两次，材质集合与每个槽位绑定必须完全一致。

## 为什么不上框架

整个引擎只有几个模块、一份数据契约、一个注册表。没有插件系统、没有事件总线、没有场景抽象层——这些只会增加间接层，却无法替代真正的工作量：精确的坐标系数学与诚实的审计。

后续阶段（运动学、爆炸视图、渲染）预期**新增消费现有 `JOINT::` 骨架的模块**，而不是重构这条管线。
