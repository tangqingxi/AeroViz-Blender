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

当前已实现并验证的能力（Stage 1、Stage 1.5、Stage 2 与 Stage 3）：

- **配置驱动导入**：每架飞机一份 JSON 配置，引擎不从代码里读取任何机型信息。
- **SDF（单模型）适配器**：`link` / `visual` / `joint` / `frame` 位姿、弧度 RPY、`expressed_in`、`relative_to`、`model://` URI 映射、外部 include 记账、多父/成环关节拒绝。
- **STL 适配器**：Blender 原生导入，按声明单位（`m` / `mm` / `cm`）缩放，保持源坐标、不居中。
- **装配重建**：按功能分组建立 Collection；`LINK::` / `JOINT::` 空对象保留真实关节中心、轴向与限位；父子层级按描述重建。
- **重复与合并件审计**：微米精度三角面比较；合并件与重复件**隐藏而不删除**，且其独特三角面必须被可见零件覆盖 100 %。
- **输入完整性**：构建前后逐文件 SHA-256 快照，任一字节变化即中止构建。
- **材质恢复**：SDF diffuse/specular/ambient/transparency/emissive 与 Gazebo 命名脚本材质；按内容签名确定性复用；二次执行幂等；任何手工覆盖必须写明 `reason`。
- **结构保护**：Stage 1.5 必须保持原有对象的矩阵、父子关系、Collection、隐藏状态、几何哈希与关节属性完全不变。
- **图形验收**：专用脚本在真实窗口中重开 `.blend`、断言状态并截图；后台渲染成功**不**算目视验收。

已新增配置驱动的机械运动与关键帧验证。Stage 3已实现配置驱动爆炸/恢复。尚未实现（不得假设存在）：镜头与灯光编排、视频渲染、多机型批处理。见 §7 路线图。

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
        └── output/<MODEL>/            唯一的当前工程（<blend_name>）

scripts/materials.py           Stage 1.5：SDF 材质 → Principled BSDF，
                               在当前唯一工程中更新材质
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
│   ├── animation/              机械运动、独立爆炸位移层与真实窗口验收
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
│   └── reverify_saved_project.py    当前工程的只读复验
└── output/                     只有一个当前工程，已被 git 忽略
```

`output/` 刻意不纳入版本管理，而且里面**只有一个文件**：当前工程 `output/DF4/DF4.blend`。

工程版本管理只有一条规则：**所有阶段直接在同一个工程上迭代**，不再生成 `DF4_Stage1.blend`、`DF4_Stage2.blend` 之类的阶段副本。保存时先写临时文件，确认落盘成功后再原子替换当前工程，因此保存中途失败不会破坏已有工程；所有程序化保存都把 `save_version` 置为 0，不产生 `.blend1`。

预览、渲染与验证记录不落本地：脚本直接写进审计仓库对应阶段的 `evidence/` 目录，运行期间的 `.work/` 临时目录在结束后删除。

## 6. 快速开始

环境要求：Blender **5.0.1**（5.x；代码针对 5.0 的 Python API），Windows。无需额外 Python 包，Blender 自带解释器即可。下文中 `$B` 指 Blender 可执行文件。

Stage 1 —— 导入与装配恢复（DF4）：

```powershell
& $B --background --factory-startup --python-exit-code 1 `
     --python '.\scripts\main.py' -- --config configs/DF4.json
```

Stage 1.5 —— 在当前唯一工程中恢复 SDF 材质：

```powershell
& $B --background --factory-startup --python-exit-code 1 `
     --python '.\scripts\materials.py' -- --config configs/DF4.json
```

图形验收（必须真实窗口，不能用 `--background`）：

```powershell
& $B -W '.\output\DF4\DF4.blend' --python '.\scripts\gui_verify.py'           -- --config configs/DF4.json
& $B -W '.\output\DF4\DF4.blend' --python '.\scripts\gui_verify_materials.py' -- --config configs/DF4.json
```

关节传递检查与映射单元检查：

```powershell
& $B --background --factory-startup --python-exit-code 1 `
     --python '.\scripts\check_joint_hierarchy.py' -- --config configs/DF4.json
& $B --background --factory-startup --python-exit-code 1 `
     --python '.\tests\test_material_mapping.py'
```

对当前唯一工程做只读复验（第1帧重放历史断言，并验证已授权关节动画，不保存工程）：

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
| Stage 2 | 机械运动骨架与独立运动测试 | 已完成 |
| Stage 3 | 坐标系定义与爆炸/装配恢复 | 已完成 |
| Stage 4.0-R1 | 中性摄影棚、姿态、同步拆解与逆序装配 | 已实现，等待人工效果验收 |
| Stage 5 | 多机型适配与工具完善 | 待执行 |

Stage 1、1.5、2、3 已针对 DF4 完成。旋翼与四个舵面动画在当前工程，证据在独立审计仓库。Stage 3 已增加坐标定义与爆炸/恢复视图；Stage 4.0已授权并实现低清展示原型，等待人工效果验收；4.1–4.3未授权。

## 8. 当前状态

- 仅在 Blender 5.0.1 / Windows 上验证，目前唯一的机型是 DF4。
- **当前工程**：`output/DF4/DF4.blend`，190个对象、8个材质。原Scene的117对象（33网格、29动画对象）完整保留；独立STAGE4_PRESENTATION共73个展示对象，其中27个共享原网格与材质的展示实例，24个活动模块、3个保留的辅助模块、1个静态姿态根、5个运动轴心、3相机、3目标Empty、6灯和1地面。所有成果都在这一个工程里。
- **Stage 1**：33 个 STL 输入 → 33 个独立网格对象，27 可见 + 6 隐藏参考件；整机可见尺寸约 0.353 × 0.376 × 0.378 m；26 个 link 空对象与 25 个关节空对象；相对描述文件的世界矩阵误差为 0；输入哈希前后不变。
- **Stage 1.5**：提取 25 条 SDF visual 材质定义（25 条带显式定义），新建并复用 7 个 Blender 材质，为 33 个网格对象完成分配（13 个显式 RGBA、12 个 Gazebo 命名脚本、8 个展示默认），Stage 1 的 89 个对象全部保持不变，Eevee 与 Material Preview 均在真实窗口截图。
- **Stage 2 已完成**：30 FPS、1–121帧；旋翼演示 1200°/s、累计 4800°，四个舵面按 CS1→CS4 顺序独立完成 ±10° 并归零。动画对象恰好五个原有 JOINT。Stage 3 已完成；Stage 4.0展示原型见下文。

详细的阶段报告、截图与产物哈希位于配套审计仓库 `tangqingxi/AeroViz-Blender-Audit`，不在本仓库。

## 许可证与第三方资产

本仓库**不含**任何模型资产、`.blend` 工程或渲染帧。

DF4 几何来自第三方仓库 `mengchaoheng/DF_gazebo`，该仓库没有 `LICENSE` 文件，因此几何本体（STL/SDF）与由它生成的工程不在本仓库分发。来源、与上游的字节差异见 [docs/asset-provenance.md](docs/asset-provenance.md)。

本项目自身的许可证**尚未确定**，因此没有放置 `LICENSE` 文件；在确定之前，默认适用"保留所有权利"。


## 工程 I/O 安全回归

已有工程默认禁止 Stage 1 重建：入口在清理 `.work/`、导入和场景构建前报错。首次构建仍正常允许；只有明确授权重建时才添加 `--force-rebuild`。Stage 2 只打开并更新当前工程，不通过 Stage 1 重建。

`project_io.save_project()` 用 `save_as_mainfile(copy=True)` 写到目标同目录的唯一 `*.partial.blend`，校验非空且当前路径未变后用 `os.replace()` 原子替换。已打开当前工程时，`bpy.data.filepath` 始终保持原目标；首次构建在提交成功后用真正的 `open_mainfile()` 绑定目标。覆盖另一份尚未打开的既有工程默认报错，只有 Stage 1 在显式授权门后使用 `allow_rebind=True`。所有保存关闭 `.blend1` 备份，保存或替换故障都在 finally 清理本次临时文件。

临时目录只能为仓库 `.work/` 或其子目录。`validate_work_dir()` 只检查；`safe_reset_work_dir()` 与 `clear_work_dir()` 每次删除前都完整校验路径链、受保护目录的双向包含关系及整棵目录树的重解析点，不再提供任意路径递归删除接口。无效配置会在任何删除前报错。Windows 目录联接也按重解析点拒绝。

在 Blender 5.0.1 中执行回归（只保存正式工程的 `.work/io-regression/` 副本）：

```powershell
& $B --background --factory-startup --python-exit-code 1 `
     --python tests/test_project_io.py -- --config configs/DF4.json
```

测试覆盖成功保存与独立进程重开、当前路径、临时写入/替换故障、目录保护、已有工程覆盖拦截及首次/显式授权门。不执行真正的 Stage 1/1.5 重建。记录与必要日志直接写入 Audit `manifests/io-regression.json` 和 `manifests/io-regression.log`，测试结束清理自己的临时目录。符号链接或联接创建若受环境限制，单独报告 SKIP，不冒充通过。首次绑定测试同样只使用副本，不创建阶段编号工程。

证据哈希校验器随代码提供：

```powershell
python scripts/verify_evidence.py ../AeroViz-Blender-Audit ../AeroViz-Blender-Audit/manifests/evidence-manifest.json
```

该回归不提供 Stage 2 执行授权。


## Stage 2 使用与验证

直接打开 `output/DF4/DF4.blend`，时间轴范围 1–121，按空格播放/暂停。四秒演示中旋翼持续转动，四个舵面分时偏转并回零；Timeline Markers 标明 CS1–CS4 正负偏转及 Return。1200°/s 不是实际电机测量值。

通用运动模块在 `scripts/animation/kinematics.py`，配置在 `configs/DF4.json` 的 `animation` 块。每个关节四个 Quaternion 通道、121 个采样点，LINEAR 插值与符号连续；不通过起终姿态的模360°结果冒充累计转数。重建动画会改工程，应先在 `.work/stage-2/` 字节副本完成测试，并匹配目标哈希。现有 Action 只有属于本引擎时才允许重建，不覆盖外来动画。

只读重新验证已保存工程：沿用 `tests/reverify_saved_project.py -- --config configs/DF4.json`，无需重跑导入或材质。真实窗口播放与截图：

```powershell
& $B -W '.\output\DF4\DF4.blend' --python scripts/animation/gui_verify.py -- --config configs/DF4.json
```

该脚本调用与空格相同的原生播放操作，记录真实帧推进和循环，显示 Dope Sheet 五个 Action，保存六种姿态和播放窗口截图；不保存工程。结果直写 Audit `stages/stage-2/evidence/`。受控回归接口为 `tests/test_kinematics.py -- --config <副本配置> --phase prepare`，随后独立进程 `--phase verify`；测试需要先准备 `.work/stage-2/rollback/` 原字节副本。正式更新的 `--phase apply --expected-sha256 <基线哈希>` 要求副本测试批准记录与动画配置一致，保存失败或回归失败必须恢复原字节并停止。

Pre-Stage 2 的 `test_project_io.py` 是静态工程基线专项记录，不用于断言 Stage 2 工程仍然无动画。当前工程的完整回归以更新后的 reverify 与运动验证为准。Stage 4.0仅授权展示原型。


## Stage 3 坐标与爆炸视图

DF4模型按用户定义冻结为FLU（前/左/上），原点为SDF模型原点，不声称为实机CG。根对象保持单位阵，FRD/FLU转换与说明见 [docs/coordinate-frames.md](docs/coordinate-frames.md)。

单工程现为117对象：原93对象保留，24个有网格的JOINT各增加一个独立 `EXPLODE_OFFSET` Empty。原五个机械Action不重建、不增键；只对配置声明的24个JOINT改变直接父级，其网格和子LINK关系不变。其余对象、33网格、7材质、相机和灯光保持。

时间轴30FPS、1–301帧：1–121保留机械运动，121–181展开，181–241保持，241–301恢复到121帧装配状态。控制器仅有Location动画（每轴5点、LINEAR），旋转和缩放不变。分支方向/距离/理由全部在 `exploded_view.branches` 配置；人为展示位移不是实际拆装行程。直接电池、controller2、X-tend、参考重复件、无网格IMU不单独爆炸。

`tests/test_exploded_view.py`提供prepare/apply/verify，先在 `.work/stage-3/` 的字节副本测试；apply保存后新启进程回归，失败恢复已核对的字节备份。只读复验仍使用 `tests/reverify_saved_project.py`，Stage2只验证1–121帧，Stage3继续验证121–301帧及原Action完整指纹。

实际窗口验收入口为 `scripts/animation/gui_verify_exploded.py -- --config configs/DF4.json`。使用原生播放，截取1/121/151/181/241/301帧，按用户最新要求截图后自动退出Blender，不保存GUI状态。无需用户操作Blender；结果与截图见Audit Stage3主报告。本阶段不输出MP4。


## Stage 4.0 初始展示原型（历史）

初始版本默认打开主相机和第1帧，Timeline为1–1650帧、17个镜头标记；当前已由R1替代。按空格播放/暂停。用户无需修改对象或参数；完整操作与截图对应见 [Stage 4.0 验收说明](docs/stage4-acceptance.md)。

55秒渐进式拆解按脚架→三片外涵道→电机/旋翼/内涵道→四舵面偏转并依次退出→四舵机退出→电池/上框/侧板/下框→电调/夹持片→最终揭示组织。采用Hawkeye Grid、三类相机和五灯，提供960×540、15FPS MP4和一张本地验收总览图。展示Scene共享原几何/材质，五个机械Action以NLA复用，原机械与爆炸控制不改写。

接口和可复现流程见 [展示层接口](docs/stage4-presentation.md)。报告、MP4、PNG与哈希位于Audit的 `stages/stage-4.0/`。技术回归完成后仍等待用户人工效果验收，不自动进入4.1–4.3。按用户本轮最新补充要求，最终窗口停留在主相机第1帧。


各阶段图片验收只交付一张总览图；分散渲染帧仅作临时输入，合图后清理。此前images目录中的图片不上传GitHub；R2按本轮明确指定路径提交一张最终总览图，其他图片继续仅作本地资料。


## Stage 4.0-R1（历史修订）

当前展示时间轴已修订为33秒、30FPS、1–990帧。中性科技摄影棚替代原Hawkeye Grid；开场姿态展示在拆解前归零。三脚架与三片外涵道分别同步展开，四舵面同步完成0→+20°→0→-20°→0；随后同步拆出舵面和舵机。电池沿实际无新穿插的-Y开口侧向退出，框架/电调/夹持件随后拆出，分解保持2秒后15组逆序返回，最后完整机型保持1秒。

原Scene117对象、原33网格、7材质及29个机械/爆炸Action保持。现有67个展示对象全部保留，仅新增3个脚架控制、姿态根和一盏轮廓灯；27个实例继续共享原Mesh/材质。正式工程仍只有 `output/DF4/DF4.blend`。

本轮明确不制作MP4，只提供本地 `STAGE_4_0_R1_OVERVIEW.png`。先前Stage4.0的55秒MP4为历史资料，不能用作当前R1预览。最终Blender保持Camera A、第1帧、停止播放，用户可按空格验收。详情见[当前验收说明](docs/stage4-acceptance.md)，审计报告位于Audit的 `stages/stage-4.0-r1/`。


## Stage 4.0-R2（历史修订）

当前为33秒、30FPS、1–990帧。柔和中性浅灰摄影棚、深色细网格；开场仅相机推进、升高与20°有限环绕，无整机倾斜。14个镜头章节替代R1的21章，只保留脚架、涵道、完整动力组件和一组舵机/舵面四类特写；飞控与电调独立特写取消。

电机和旋翼通过S4::MODULE::POWER共同平移，两个Mesh保留独立，旋翼原关节层仍缓慢自转。四舵面同步±20°展示后依次退出；电池经Blend实际曲线/世界坐标确认，保留-Y 380mm侧出，未用+Z。766–825分解停留，826–945逆序装配，946–990完整机型停留。原Stage1–3对象、网格、材质、Action及FLU保持。

只输出本轮正式工程与一张 `stages/stage-4/evidence/STAGE_4_0_R2_OVERVIEW.png`，不生成视频。最终Blender保持Camera A、第1帧、停止播放，用户直接按空格验收。[当前操作说明](docs/stage4-acceptance.md)。R1历史报告保留。

## 当前修订：Stage 4.0-R3

30秒、30FPS、1–900帧，10个镜头章节。删除单脚架及舵机/舵面独立特写，Camera C仅保留单片涵道和完整动力组件。四舵面先同步±20°回零，再于426–465同步退出，随后四舵机退出；Camera B在偏转和退出阶段各保持稳定构图。脚架91–145帧的原退出运动、完整动力组件、摄影棚、原始零件材质及-Y380mm电池路径保持。

691–750完整分解保持2秒，751–870分组逆序装配，四舵面同步返回，871–900完整机型停留。原Stage1–3与R2展示73对象保留；唯一工程仍为`output/DF4/DF4.blend`。本轮只交付Audit一张`STAGE_4_0_R3_OVERVIEW.png`，没有新视频或独立渲染序列。中间帧/GUI检查图限于`.work/stage-4-r3/`并清理。最终窗口保持Camera A、第1帧、停止播放；[中文验收说明](docs/stage4-acceptance.md)。R1/R2报告与证据不覆盖。
