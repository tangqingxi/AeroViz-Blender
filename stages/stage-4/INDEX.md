# Stage 4 索引

Stage 4 有四个镜头/拆解修订版和一次画质定标。2026-11-11 已把原先散在三个目录
（`stage-4.0/`、`stage-4.0-r1/`、`stage-4/`）的内容**全部合并到本目录**：报告平铺，
证据按版本分子目录，清单按版本改名。

## 当前有效版本

| 项目 | 值 |
|---|---|
| 当前正式版本 | **Stage 4.0-R3**（已验收基线） |
| 当前画质定标 | **Stage 4.1**（Cycles 参数与 8 帧测试，待用户画质验收） |
| 正式工程 | `<DEV>/output/DF4/DF4.blend` |
| 正式工程 SHA256 | `cfafc7c7245654409a378a7c16267251a3307863dfcfb6c288ac53c1674295a0` |
| 正式工程大小 | 5,519,908 B |
| 时间轴 | 30 FPS，1–900 帧，30 秒，10 个章节 |
| 阶段状态 | **STAGE 4.1: READY FOR USER QUALITY ACCEPTANCE** |

除 R3 与 4.1 之外的内容都是历史记录，不得当作当前状态引用。

## 文件布局

```text
stages/stage-4/
├── INDEX.md                              本文件
├── STAGE_4_0_REPORT.md                   4.0 主报告
├── STAGE_4_0_ACCEPTANCE.md                4.0 验收说明
├── STAGE_4_0_R1_REPORT.md                R1 主报告
├── STAGE_4_0_R2_REPORT.md                R2 主报告
├── STAGE_4_0_R3_REPORT.md                R3 主报告（当前基线）
├── STAGE_4_1_CYCLES_REPORT.md            4.1 画质定标报告
├── evidence-manifest-stage-4.0.json      4.0 证据清单
├── evidence-manifest-stage-4.0-r1.json   R1 证据清单
├── evidence-manifest-stage-4.0-r2.json   R2 证据清单
├── evidence-manifest-stage-4.0-r3.json   R3 证据清单
├── evidence-manifest-stage-4.1.json      4.1 证据清单
└── evidence/
    ├── stage-4.0/        4.0 的机器证据、总览图与低清预览 MP4
    ├── stage-4.0-r1/     R1 的机器证据
    ├── stage-4.0-r2/     R2 的机器证据与 STAGE_4_0_R2_OVERVIEW.png
    ├── stage-4.0-r3/     R3 的机器证据与 STAGE_4_0_R3_OVERVIEW.png
    └── stage-4.1/        4.1 的 Cycles 总览图与渲染记录
```

## 版本一览

| 版本 | 报告 | 证据 | 证据清单 | 工程 SHA256（当时） | 状态 |
|---|---|---|---|---|---|
| 4.0 | [`STAGE_4_0_REPORT.md`](STAGE_4_0_REPORT.md)、[`STAGE_4_0_ACCEPTANCE.md`](STAGE_4_0_ACCEPTANCE.md) | [`evidence/stage-4.0/`](evidence/stage-4.0/) | [`evidence-manifest-stage-4.0.json`](evidence-manifest-stage-4.0.json) | `489553c1…60d7` | 历史 |
| 4.0-R1 | [`STAGE_4_0_R1_REPORT.md`](STAGE_4_0_R1_REPORT.md) | [`evidence/stage-4.0-r1/`](evidence/stage-4.0-r1/) | [`evidence-manifest-stage-4.0-r1.json`](evidence-manifest-stage-4.0-r1.json) | `da631cf3…9287` | 历史 |
| 4.0-R2 | [`STAGE_4_0_R2_REPORT.md`](STAGE_4_0_R2_REPORT.md) | [`evidence/stage-4.0-r2/`](evidence/stage-4.0-r2/) | [`evidence-manifest-stage-4.0-r2.json`](evidence-manifest-stage-4.0-r2.json) | `766faf31…f197` | 历史 |
| **4.0-R3** | [`STAGE_4_0_R3_REPORT.md`](STAGE_4_0_R3_REPORT.md) | [`evidence/stage-4.0-r3/`](evidence/stage-4.0-r3/) | [`evidence-manifest-stage-4.0-r3.json`](evidence-manifest-stage-4.0-r3.json) | `cfafc7c7…295a0` | **当前基线，已验收** |
| **4.1** | [`STAGE_4_1_CYCLES_REPORT.md`](STAGE_4_1_CYCLES_REPORT.md) | [`evidence/stage-4.1/`](evidence/stage-4.1/) | [`evidence-manifest-stage-4.1.json`](evidence-manifest-stage-4.1.json) | 同上（只读使用，未改动） | **待用户画质验收** |

## 2026-11-11 合并说明

| 项目 | 变化 |
|---|---|
| 目录 | `stages/stage-4.0/`、`stages/stage-4.0-r1/` 的**全部内容**并入 `stages/stage-4/`，两个旧目录已删除 |
| 报告 | 4.0 与 R1 的报告移入本目录后，与 R2/R3/4.1 报告平铺共存 |
| 证据 | 原本混在 `evidence/` 顶层的 R2 文件移入 `evidence/stage-4.0-r2/`；`evidence/r3/` 改名 `evidence/stage-4.0-r3/`；`evidence/stage4_1/` 改名 `evidence/stage-4.1/`；R3 总览图移入 `evidence/stage-4.0-r3/` |
| 清单 | 五份清单统一改名为 `evidence-manifest-stage-<版本>.json`。原 `evidence-manifest.json`（内容是 R2）现为 `evidence-manifest-stage-4.0-r2.json` |
| 内容 | **只改了路径字面量**。报告的结论、工程 SHA256、网格/对象计数、清单里的证据哈希全部未变 |
| 证据文件 | `evidence/` 内的 JSON 是**当时**的记录，其内部写的旧路径（如 `stages/stage-4.0/...`）保持原样，未改写字节，因此清单哈希仍然有效 |

## 历史保护

- 四个修订版与 4.1 的报告、证据、清单全部保留；没有删除任何历史材料。
- 每份报告的结论只对当时那份工程字节成立，历史阶段的 PASS 不等于当前阶段的 PASS。
- 证据清单的 `status` 字段统一使用 schema v2 枚举，原始状态词保留在各清单的 `status_note` 中。

## 相关文档

- 证据与输入哈希汇总：[`../../manifests/ARTIFACT_MANIFEST.md`](../../manifests/ARTIFACT_MANIFEST.md)
- 当前状态与下一步：[`../../HANDOFF.md`](../../HANDOFF.md)
- 阶段总览：[`../../README.md`](../../README.md)
