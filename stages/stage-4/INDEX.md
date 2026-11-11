# Stage 4 索引

Stage 4 经过四次镜头/拆解迭代和一次画质定标，文件分散在三个目录里。本页是这些版本的唯一入口：先说清**哪个是当前有效版本**，再逐版列出报告、清单和证据的位置。

## 当前有效版本

| 项目 | 值 |
|---|---|
| 当前正式版本 | **Stage 4.0-R3**（已验收基线） |
| 当前画质定标 | **Stage 4.1**（Cycles 参数与 8 帧测试，待用户画质验收） |
| 正式工程 | `<DEV>/output/DF4/DF4.blend` |
| 正式工程 SHA256 | `cfafc7c7245654409a378a7c16267251a3307863dfcfb6c288ac53c1674295a0` |
| 正式工程大小 | 5,519,908 B |
| 镜头 / 时间轴 | 30 FPS，1–900 帧，30 秒，10 个章节 |
| 阶段状态 | Stage 4.1: READY FOR USER QUALITY ACCEPTANCE |

除 R3 与 4.1 之外的同目录文件都是历史记录，**不得当作当前状态引用**。

## 版本一览

| 版本 | 报告 | 机器证据 | 证据清单 | 工程 SHA256（当时） | 状态 |
|---|---|---|---|---|---|
| 4.0 原型 | [`../stage-4.0/STAGE_4_0_REPORT.md`](../stage-4.0/STAGE_4_0_REPORT.md) | [`../stage-4.0/evidence/`](../stage-4.0/evidence/) | [`../stage-4.0/evidence-manifest.json`](../stage-4.0/evidence-manifest.json) | `489553c1…60d7` | 历史（低清预览） |
| 4.0-R1 | [`../stage-4.0-r1/STAGE_4_0_R1_REPORT.md`](../stage-4.0-r1/STAGE_4_0_R1_REPORT.md) | [`../stage-4.0-r1/evidence/`](../stage-4.0-r1/evidence/) | [`../stage-4.0-r1/evidence-manifest.json`](../stage-4.0-r1/evidence-manifest.json) | `da631cf3…9287` | 历史（已被 R2 取代） |
| 4.0-R2 | [`STAGE_4_0_R2_REPORT.md`](STAGE_4_0_R2_REPORT.md) | [`evidence/`](evidence/)（顶层文件） | [`evidence-manifest.json`](evidence-manifest.json) | `766faf31…f197` | 历史（已被 R3 取代） |
| **4.0-R3** | [`STAGE_4_0_R3_REPORT.md`](STAGE_4_0_R3_REPORT.md) | [`evidence/r3/`](evidence/r3/) | [`evidence-manifest-r3.json`](evidence-manifest-r3.json) | `cfafc7c7…295a0` | **当前基线，已验收** |
| **4.1 画质定标** | [`STAGE_4_1_CYCLES_REPORT.md`](STAGE_4_1_CYCLES_REPORT.md) | [`evidence/stage4_1/`](evidence/stage4_1/) | [`evidence-manifest-s41.json`](evidence-manifest-s41.json) | 同上（只读使用，未改动） | **待用户画质验收** |

## 文件名与目录的对应关系（最容易混淆的部分）

1. `evidence-manifest.json` 的 `phase` 字段是 **`Stage4.0-R2`**，对应开发提交 `4b8dca8`。它的文件名没有版本后缀，但**它只覆盖 R2**，不是当前清单。
2. `evidence-manifest-r3.json` 的 `phase` 是 `Stage4.0-R3`，对应开发提交 `e38ecc3`，覆盖当前基线。
3. `evidence-manifest-s41.json` 覆盖本轮的 Cycles 定标材料。
4. R2 的机器证据放在 `evidence/` 顶层（`baseline_regression.json`、`battery_path.json`、`GUI` 记录等）；R3 的机器证据放在 `evidence/r3/` 子目录；4.1 的材料放在 `evidence/stage4_1/`。
5. 两张总览图并列在 `evidence/`：`STAGE_4_0_R2_OVERVIEW.png` 与 `STAGE_4_0_R3_OVERVIEW.png`，按文件名区分，不要按修改时间判断。
6. R2 清单保留原文件名与内容不变，作为历史；本轮**没有**覆盖或重写它。

## 历史保护

- R1 / R2 / R3 的报告、证据与清单保持原始字节，未改写其 SHA256。
- 删除或替换只发生在"完全重复、无引用、纯过期状态说明"三类文件上，且均记录在根 `README.md` 的治理说明中。
- 历史阶段的 PASS 记录不等于当前阶段的 PASS：每份报告的结论只对当时那份工程字节成立。

## 相关文档

- 证据与输入哈希的汇总：[`../../manifests/ARTIFACT_MANIFEST.md`](../../manifests/ARTIFACT_MANIFEST.md)
- 当前状态与下一步：[`../../HANDOFF.md`](../../HANDOFF.md)
- 阶段总览：[`../../README.md`](../../README.md)
