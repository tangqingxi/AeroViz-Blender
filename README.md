# AeroViz-Blender — Audit Repository

本仓库是 **AeroViz-Blender** 的阶段报告、验收证据与交接记录，**不含源码、不含模型资产**。

- 开发仓库（代码、配置、文档）：<https://github.com/tangqingxi/AeroViz-Blender>
- 审计仓库（本仓库）：<https://github.com/tangqingxi/AeroViz-Blender-Audit>

两个仓库保持 Public。本仓库只放报告、截图与测量记录，不含原始 STL/SDF/`.blend`，也不放可执行源码。

## 当前状态

| 项目 | 值 |
|---|---|
| 当前正式工程 | `<DEV>/output/DF4/DF4.blend`，5,519,908 B |
| 工程 SHA256 | `cfafc7c7245654409a378a7c16267251a3307863dfcfb6c288ac53c1674295a0` |
| 当前有效阶段 | Stage 4.0-**R3**（已验收基线）+ Stage 4.1（Cycles 画质定标） |
| 阶段状态 | **STAGE 4.1: READY FOR USER QUALITY ACCEPTANCE** |
| 时间轴 | 30 FPS，1–900 帧，30 秒，10 个章节 |
| 下一步 | 用户确认画质 → 授权 Stage 4.2 正式渲染 900 帧 |

当前状态以 [`HANDOFF.md`](HANDOFF.md) 为准；本页只做导航。

## 阶段索引

| 阶段 | 内容 | 状态 | 报告 |
|---|---|---|---|
| Stage 1 | 通用模型导入与空间装配恢复 | 已完成 | [`STAGE_1_REPORT.md`](stages/stage-1/STAGE_1_REPORT.md) |
| Stage 1.5 | SDF 材质恢复 | 已完成 | [`STAGE_1_5_REPORT.md`](stages/stage-1.5/STAGE_1_5_REPORT.md) |
| Stage 2 | 机械运动骨架与独立运动测试 | COMPLETE / PASS | [`STAGE_2_REPORT.md`](stages/stage-2/STAGE_2_REPORT.md) |
| Stage 3 | FLU 定义与爆炸/恢复视图 | COMPLETE / PASS | [`STAGE_3_REPORT.md`](stages/stage-3/STAGE_3_REPORT.md) |
| Stage 4.0 | 展示镜头与渐进式拆解原型 | 历史（已被 R3 取代） | [`STAGE_4_0_REPORT.md`](stages/stage-4.0/STAGE_4_0_REPORT.md) |
| Stage 4.0-R1 | 中性摄影棚、姿态、同步拆解与逆序装配 | 历史（已被 R3 取代） | [`STAGE_4_0_R1_REPORT.md`](stages/stage-4.0-r1/STAGE_4_0_R1_REPORT.md) |
| Stage 4.0-R2 | 柔和灰摄影棚、相机叙事与完整动力拆解 | 历史（已被 R3 取代） | [`STAGE_4_0_R2_REPORT.md`](stages/stage-4/STAGE_4_0_R2_REPORT.md) |
| **Stage 4.0-R3** | 镜头精简与四舵面同步拆解 | **当前基线，已验收** | [`STAGE_4_0_R3_REPORT.md`](stages/stage-4/STAGE_4_0_R3_REPORT.md) |
| **Stage 4.1** | Cycles 正式画质定标（8 帧测试） | **待用户画质验收** | [`STAGE_4_1_CYCLES_REPORT.md`](stages/stage-4/STAGE_4_1_CYCLES_REPORT.md) |
| Stage 4.2 | 正式渲染 900 帧 + MP4 | 未授权 | — |
| Stage 5 | 多机型适配与工具完善 | 未执行 | — |

Stage 4 的四个修订版 + 4.1 分散在三个目录，**先读** [`stages/stage-4/INDEX.md`](stages/stage-4/INDEX.md)：它说明每个版本的报告、证据目录与清单的对应关系，以及 `evidence-manifest.json` 实际只覆盖 R2 这件事。

## 目录结构

```text
AeroViz-Blender-Audit/
├── README.md                        本文件：导航与阶段索引
├── HANDOFF.md                       只描述当前状态与下一步
├── manifests/
│   ├── ARTIFACT_MANIFEST.md         输入/产物哈希、来源、许可证核查
│   ├── evidence-manifest.json       全仓快照（某次提交时点有效，非阶段验收记录）
│   ├── reverify-2026-11-10.json     归一化前的历史复验记录
│   ├── refactor-check-2026-11-10.json
│   └── io-regression*.json|log      Stage 2 期 I/O 回归驱动记录
└── stages/
    ├── stage-1/        STAGE_1_REPORT.md + evidence-manifest.json + evidence/
    ├── stage-1.5/      STAGE_1_5_REPORT.md + evidence-manifest.json + evidence/
    ├── stage-2/        STAGE_2_REPORT.md + evidence-manifest.json + evidence/
    ├── stage-3/        STAGE_3_REPORT.md + evidence-manifest.json + evidence/
    ├── stage-4.0/      STAGE_4_0_REPORT.md + ACCEPTANCE + evidence-manifest.json + evidence/
    ├── stage-4.0-r1/   STAGE_4_0_R1_REPORT.md + evidence-manifest.json + evidence/
    └── stage-4/        Stage 4 的 R2 / R3 / 4.1
        ├── INDEX.md                   ← Stage 4 系列索引（先读这个）
        ├── STAGE_4_0_R2_REPORT.md
        ├── STAGE_4_0_R3_REPORT.md
        ├── STAGE_4_1_CYCLES_REPORT.md
        ├── evidence-manifest.json     ← 覆盖 R2（phase 字段：Stage4.0-R2）
        ├── evidence-manifest-r3.json  ← 覆盖 R3
        ├── evidence-manifest-s41.json ← 覆盖 4.1
        └── evidence/
            ├── …                     R2 的机器证据与 STAGE_4_0_R2_OVERVIEW.png
            ├── r3/                   R3 的机器证据与 STAGE_4_0_R3_OVERVIEW.png 同级文件
            └── stage4_1/             4.1 的总览图与渲染记录
```

## 证据校验

各阶段清单由 `build_manifest.py` 生成，记录相对路径与 SHA256：

```bash
python scripts/verify_evidence.py <audit-root> <audit-root>/stages/stage-1/evidence-manifest.json
python scripts/verify_evidence.py <audit-root> <audit-root>/stages/stage-2/evidence-manifest.json
python scripts/verify_evidence.py <audit-root> <audit-root>/stages/stage-3/evidence-manifest.json
python scripts/verify_evidence.py <audit-root> <audit-root>/stages/stage-4.0/evidence-manifest.json
python scripts/verify_evidence.py <audit-root> <audit-root>/stages/stage-4.0-r1/evidence-manifest.json
python scripts/verify_evidence.py <audit-root> <audit-root>/stages/stage-4/evidence-manifest.json        # R2
python scripts/verify_evidence.py <audit-root> <audit-root>/stages/stage-4/evidence-manifest-r3.json     # R3
python scripts/verify_evidence.py <audit-root> <audit-root>/stages/stage-4/evidence-manifest-s41.json    # 4.1
```

退出码 0 表示列出的文件本地字节与记录一致。该校验只证明本地文件完整性，不证明测试结论。

## 本轮治理（2026-11-11）

只做结构与状态收敛，不改写任何历史报告或历史 SHA256：

| 处理 | 对象 | 原因 |
|---|---|---|
| 新增 | `stages/stage-4/INDEX.md` | Stage 4 分三个目录、每版各有清单，缺一个统一切换点 |
| 重写 | `README.md`、`HANDOFF.md` | 原文同时描述 R2 与 R3，出现"当前状态见 R2 报告"这类与事实冲突的表述 |
| 修正 | `manifests/ARTIFACT_MANIFEST.md` | §5 把 R1 期的复验文件标成"当前工程复验"；§7 的工程哈希与对象数是 Stage 3 的旧值 |
| 删除 | `manifests/reverify-current.json` | 与 `stages/stage-4.0-r1/evidence/saved_project_regression.json` **逐字节相同**（`c48eec1c…`），内容是 R1 期数据，文件名却暗示"当前" |
| 重新生成 | `manifests/evidence-manifest.json` | 全仓快照；删除重复文件后必然失效，且其 phase 字段被标成 Stage4.0-R3，易被误读为阶段验收记录。重生成后标注为 `RepoSnapshot` |
| 保留 | R1/R2/R3 全部报告、证据、阶段清单 | 历史价值，且 R2 清单的文件名虽无版本后缀，内容是唯一的一份 R2 记录 |

删除前均核对过 SHA256 与引用关系；无法确定用途的文件一律保留（如 `manifests/io-regression*`）。

## 分工边界

本仓库只放报告、截图与测量记录，不含原始 STL/SDF/`.blend`。模型来源与文件取舍见 [`manifests/ARTIFACT_MANIFEST.md`](manifests/ARTIFACT_MANIFEST.md) §1、§6。

## 协作流程

1. ChatGPT 制定阶段任务。
2. Agent 在本地执行，代码提交主仓库。
3. Agent 将报告与验收证据提交本仓库。
4. 用户提供本仓库链接。
5. ChatGPT 阅读报告并复核；通过后授权下一阶段。

## 明确声明

- 各阶段报告只对当时那份工程字节成立；历史阶段的 PASS 不等于当前阶段的 PASS。
- 报告中的数据全部来自实际执行与工程文件，未将计划功能写成已实现功能。
- 未创建版本 Tag；本项目自身许可证尚未确定。
