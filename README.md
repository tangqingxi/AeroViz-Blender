# AeroViz-Blender

**AeroViz** 是航空器三维可视化与动画工具链的**平台名称**。
**Blender** 是当前的**实现平台**。
**DF4**（涵道风扇无人机）只是**第一个验证案例**，项目架构不绑定于它。

本仓库把仿真侧已有的机型描述（SDF/URDF 风格）与网格（STL）重建为 Blender 中的可视化装配：恢复真实装配位姿与关节坐标系、恢复 SDF 材质，并在此后扩展为机械运动、爆炸视图与渲染视频。

---

## 1. 项目概述

仿真与 CAD 流程里，一架航空器由"一份机器描述 + 一堆网格"构成。这份数据完整，但**不可展示**：难以目视检查、无法做动画、更无法产出视频。AeroViz-Blender 补上这一段：

- **导入**单模型描述，按显式语义求解 link/visual/joint 坐标系，把每个网格放在真实装配位置。
- **保真**：不自动居中、不猜单位、不静默近似；每个放置决策都记录其依据。
- **恢复材质**：把描述里的 diffuse/specular/transparency/脚本材质名映射到 Principled BSDF。
- **验证**：用真实图形进程重新打开工程、断言状态并截图，而不是以后台渲染成功代替目视验收。
- **扩展**：后续阶段接入运动学、爆炸视图与视频渲染。

项目把三类内容严格分开：

| 类别 | 位置 | 规则 |
|---|---|---|
| 通用自动化代码 | `scripts/`、`adapters/` | 不得出现任何机型名、零件名或机型路径 |
| 机型专属数据 | `configs/<MODEL>.json` | 命名、分组、单位、覆盖项与依据全部在此 |
| 验收证据 | 独立审计仓库 | 报告、截图、哈希、验收记录 |

## 2. 核心能力

当前已实现并验证的能力（Stage 1 与 Stage 1.5）：

- **配置驱动导入**：每架飞机一份 JSON 配置，引擎不从代码里读取任何机型信息。
- **SDF（单模型）适配器**：`link` / `visual` / `joint` / `frame` 位姿、弧度 RPY、`expressed_in`、`relative_to`、`model://` URI 映射、外部 include 记账、多父/成环关节拒绝。
- **STL 适配器**：Blender 原生导入，按声明单位（`m` / `mm` / `cm`）缩放，保持源坐标、不居中。
- **装配重建**：按功能分组建立 Collection；`LINK::` / `JOINT::` 空对象保留真实关节中心、轴向与限位；父子层级按描述重建。
- **重复与合并件审计**：微米精度三角面比较；合并件与重复件**隐藏而不删除**，且其独特三角面必须被可见零件覆盖 100 %。
- **输入完整性**：构建前后逐文件 SHA-256 快照，任一字节变化即中止构建。
- **材质恢复**：SDF diffuse/specular/ambient/transparency/emissive 与 Gazebo 命名脚本材质；按内容签名确定性复用；二次执行幂等；任何手工覆盖必须写明 `reason`。
- **结构保护**：Stage 1.5 必须保持原有对象的矩阵、父子关系、Collection、隐藏状态、几何哈希与关节属性完全不变。
- **图形验收**：专用脚本在真实窗口中重开 `.blend`、断言状态并截图；后台渲染成功**不**算目视验收。

尚未实现（不得假设存在）：机械运动、关键帧动画、爆炸视图、镜头与灯光编排、视频渲染、多机型批处理。见 §7 路线图。

## 3. 架构

```
configs/<MODEL>.json          机型专属：输入根目录、单位、分组、
        │                     参考件、覆盖项、依据说明
        ▼
scripts/main.py               入口：边界检查 → 选择适配器 → 构建 → 校验 → 保存
        │
        ├── adapters/         格式层：描述文件 → 中性场景数据
        │     import_sdf.py   单模型 SDF 1.5（关节、frame、URI）
        │     import_stl.py   显式零件清单（不推断装配关系）
        │
        ├── scripts/scene_builder.py   中性数据 → Collection、LINK::/JOINT:: 层级、
        │                              四向正交预览
        ├── scripts/validation.py      输入快照、几何清单、重复/覆盖率审计、报告生成
        │
        └── output/<MODEL>/            .blend 工程、preview/、reports/

scripts/materials.py           Stage 1.5：SDF 材质 → Principled BSDF，
                               在既有 Stage 1 工程上另存新版本
scripts/gui_verify*.py         图形进程重开 + 截图验收
scripts/check_joint_hierarchy.py   独立进程验证关节传递
tests/                         映射/优先级单元检查（在 Blender 内运行）
```

**适配器契约就是接缝。** 适配器返回一份中性字典（`parts`、`links`、`joints`、`includes`、`model_pose`），场景构建器只消费这份数据。新增格式 = 新增一个模块并在 `adapters/__init__.py` 注册；新增机型 = 新增一个配置文件。两者互不需要改对方。

代码**强制**而非文档声明的约束：

- 模型输入目录只读；构建前后比对输入哈希。
- 输出必须留在仓库工作区（`output/`）内，且不得落在输入目录里。
- 盘上每个 STL 必须被描述引用、列入 `extra_meshes`、或列入 `reference_only` 并给出理由；否则构建失败。
- 旋转必须是弧度 RPY；`degrees="true"`、四元数位姿、嵌套模型、成环/多父关节、非网格 visual 一律报错而不是近似。
- 参考件只有在可见零件覆盖其独特三角面 100 % 时才允许隐藏。

## 4. 支持的模型格式

| 格式 | 状态 | 说明 |
|---|---|---|
| SDF 1.5，单个 `<model>` | 已支持 | `adapter: "sdf"`；位姿遵循 SDFormat 1.5 坐标语义 |
| 含 `{% %}` 控制流的 SDFormat 模板 | 显式报错 | 先用可信参数展开为 SDF |
| 嵌套模型 / `include` 的外部模型 | 拒绝 | 仅在 `ignored_includes` 中显式说明时跳过 |
| STL 零件清单（无描述文件） | 已支持 | `adapter: "stl"`；每个零件必须给出位姿与依据 |
| 非网格 visual（box/sphere/cylinder） | 拒绝 | 不静默跳过 |
| URDF、STEP、OBJ、FBX、glTF | 未支持 | 新增适配器即可，由配置选择 |

单位靠**声明**而非推断：STL 支持 `m` / `mm` / `cm`，SDF 默认米。Blender 使用公制，`scale_length = 1`。

## 5. 项目结构

```text
AeroViz-Blender/
├── README.md
├── .gitignore                  排除构建输出与第三方模型资产
├── configs/
│   ├── DF4.json                审计运行所用的确切配置
│   └── template.json           新机型起步模板
├── adapters/
│   ├── __init__.py             适配器注册表（sdf、stl）
│   ├── import_sdf.py
│   └── import_stl.py
├── scripts/
│   ├── main.py                 Stage 1 入口
│   ├── materials.py            Stage 1.5 入口（也可作为模块导入）
│   ├── scene_builder.py        Collection、层级、预览
│   ├── validation.py           完整性与审计记录
│   ├── gui_verify.py           Stage 1 图形验收
│   ├── gui_verify_materials.py Stage 1.5 图形验收
│   ├── check_joint_hierarchy.py
│   ├── animation/              Stage 2/3 预留：只有接口说明，无实现
│   └── rendering/              Stage 4 预留：只有接口说明，无实现
├── assets/
│   └── materials/
│       └── gazebo_standard.json   Gazebo Classic 脚本材质数值摘要
├── docs/
│   ├── architecture.md         分层、数据契约、强制约束
│   ├── model-onboarding.md     如何接入 SHC09 或其他机型
│   ├── interfaces.md           后续阶段的预留接口
│   └── asset-provenance.md     模型来源与许可状态
├── examples/
│   └── README.md
├── tests/
│   ├── test_material_mapping.py     映射优先级 / 颜色空间 / 歧义处理
│   └── reverify_saved_project.py    交付工程的只读复验
└── output/                     生成物，已被 git 忽略（工程、预览、报告）
```

`output/` 刻意不纳入版本管理：其中是多兆字节的 `.blend` 工程、渲染帧与每次运行的报告。大型工程文件留在本地，共享时再约定 Git LFS 或 Release 策略。

## 6. 快速开始

环境要求：Blender **5.0.1**（5.x；代码针对 5.0 的 Python API），Windows。无需额外 Python 包，Blender 自带解释器即可。下文中 `$B` 指 Blender 可执行文件。

Stage 1 —— 导入与装配恢复（DF4）：

```powershell
& $B --background --factory-startup --python-exit-code 1 `
     --python '.\scripts\main.py' -- --config configs/DF4.json
```

Stage 1.5 —— 把 SDF 材质恢复到新版本工程：

```powershell
& $B --background --factory-startup --python-exit-code 1 `
     --python '.\scripts\materials.py' -- --config configs/DF4.json
```

图形验收（必须真实窗口，不能用 `--background`）：

```powershell
& $B -W '.\output\DF4\DF4_Stage1.blend'   --python '.\scripts\gui_verify.py'
& $B -W '.\output\DF4\DF4_Stage1_5.blend' --python '.\scripts\gui_verify_materials.py'
```

关节传递检查与映射单元检查：

```powershell
& $B --background --factory-startup --python-exit-code 1 `
     --python '.\scripts\check_joint_hierarchy.py'
& $B --background --factory-startup --python-exit-code 1 `
     --python '.\tests\test_material_mapping.py'
```

对已验收工程做只读复验（打开两个阶段的工程、重放全部记录断言、不保存任何文件）：

```powershell
& $B --background --factory-startup --python-exit-code 1 `
     --python '.\tests\reverify_saved_project.py' -- --config configs/DF4.json
```

期望依次看到 `STAGE1_IMPORT_OK`、`MATERIAL_STAGE_OK 7 33`、`JOINT_HIERARCHY_OK 5`、`MATERIAL_MAPPING_TESTS_OK`、`REVERIFY_OK`。所有输出路径相对仓库根目录解析；模型输入目录只被读取。

接入其他机型：复制 `configs/template.json`，按 [docs/model-onboarding.md](docs/model-onboarding.md) 填写。新增机型不需要改动通用代码。

## 7. 开发路线图

| 阶段 | 内容 | 状态 |
|---|---|---|
| Stage 1 | 通用模型导入与空间装配恢复 | 已完成 |
| Stage 1.5 | SDF 材质恢复 | 已完成 |
| Stage 2 | 机械运动骨架与独立运动测试 | 待执行 |
| Stage 3 | 爆炸视图与机械动画 | 待执行 |
| Stage 4 | 镜头、灯光与视频渲染 | 待执行 |
| Stage 5 | 多机型适配与工具完善 | 待执行 |

Stage 1 与 Stage 1.5 已针对 DF4 完成，验收证据在独立审计仓库。后续阶段均未开始：本仓库目前**不包含任何动画、爆炸视图或视频渲染能力**。

## 8. 当前状态

- 仅在 Blender 5.0.1 / Windows 上验证，目前唯一的机型是 DF4。
- **Stage 1**：33 个 STL 输入 → 33 个独立网格对象，27 可见 + 6 隐藏参考件；整机可见尺寸约 0.353 × 0.376 × 0.378 m；26 个 link 空对象与 25 个关节空对象；相对描述文件的世界矩阵误差为 0；输入哈希前后不变。
- **Stage 1.5**：提取 25 条 SDF visual 材质定义（25 条带显式定义），新建并复用 7 个 Blender 材质，为 33 个网格对象完成分配（13 个显式 RGBA、12 个 Gazebo 命名脚本、8 个展示默认），Stage 1 的 89 个对象全部保持不变，Eevee 与 Material Preview 均在真实窗口截图。
- **Stage 2（机械运动）尚未开始**，需要明确授权。

详细的阶段报告、截图与产物哈希位于配套审计仓库 `tangqingxi/AeroViz-Blender-Audit`，不在本仓库。

## 许可证与第三方资产

本仓库**不含**任何模型资产、`.blend` 工程或渲染帧。

DF4 几何来自一个**没有许可证文本**的上游仓库；该模型作者与本项目作者是同一实验室的同事，DF4 属团队共用资产，因此派生的报告与截图在配套审计仓库中公开发布。具体来源、与上游的字节差异，以及超出团队范围使用时的处理方式，见 [docs/asset-provenance.md](docs/asset-provenance.md)。

本项目自身的许可证**尚未确定**，因此没有放置 `LICENSE` 文件；在确定之前，默认适用"保留所有权利"。
