# Agent Handoff

只记录当前状态。历史过程在 `stages/` 下各阶段报告中，不在此重复。

## 当前状态

| 项目 | 值 |
|---|---|
| 当前正式工程 | `<DEV>/output/DF4/DF4.blend` |
| 工程大小 / SHA256 | 5,519,908 B / `cfafc7c7245654409a378a7c16267251a3307863dfcfb6c288ac53c1674295a0` |
| 当前有效阶段 | Stage 4.0-**R3**（已验收基线）+ **Stage 4.1**（Cycles 画质定标） |
| 阶段状态 | **STAGE 4.1: READY FOR USER QUALITY ACCEPTANCE** |
| 时间轴 | 30 FPS，1–900 帧，30 秒，10 个章节 |
| 阻塞点 | 用户尚未给出画质验收结论；Stage 4.2 未授权 |

## 仓库与提交

| 仓库 | 分支 | HEAD | 状态 |
|---|---|---|---|
| <https://github.com/tangqingxi/AeroViz-Blender> | `main` | `f7cbd09837037480f5a7df4325a49b5a57b68440` | 已推送，工作区 clean |
| <https://github.com/tangqingxi/AeroViz-Blender-Audit> | `main` | 见本文件所在提交（SHA 在完成消息中给出） | 已推送，工作区 clean |

两个仓库保持 Public。不 force push、不创建 Tag、不上传 `.blend` / STL / SDF / 全分辨率测试帧 / 序列 / MP4。

## 本轮完成

1. **Audit 治理**：新增 `stages/stage-4/INDEX.md`；重写本文件与 `README.md`；修正 `manifests/ARTIFACT_MANIFEST.md` 中把 R1 期文件标成"当前"的段落；删除与 R1 证据逐字节相同的 `manifests/reverify-current.json`。详见 `README.md` 的「本轮治理」表。
2. **Stage 4.1 Cycles 定标**：8 帧 1920×1080 / 256 samples / OptiX / OIDN / AgX，平均 10.08 s/帧；900 帧约 2.52 小时、PNG 母版约 1.63 GB。报告见 `stages/stage-4/STAGE_4_1_CYCLES_REPORT.md`，总览图见 `stages/stage-4/evidence/stage-4.1/STAGE_4_1_CYCLES_QUALITY_OVERVIEW.png`。Stage 4 全部版本已合并到 `stages/stage-4/` 一处，索引见 `stages/stage-4/INDEX.md`。
3. **DEV 新增** `scripts/rendering/render_cycles.py`：只读正式工程的 Cycles 静帧渲染入口，带 `--skip-existing` 续跑检查。

## 待用户确认

1. 是否接受 256 samples / OptiX / OIDN 的画质（依据：8 帧总览图与 100% 裁切检查）。
2. 是否需要在正式渲染前补 512 samples 对照帧，或补拍过渡帧（F0426、F0506 等相机/动作切换点）。
3. 授权 Stage 4.2 后，MP4 是否按 CRF 17、Preset slow、BT.709、Fast Start 输出。

## 未解决问题

| 问题 | 影响 | 现状 |
|---|---|---|
| 定标只覆盖 8 帧 | 极端过渡帧的画质未单独验证 | 可在正式渲染前补 2–3 帧 |
| 长时间渲染可能降频 | 900 帧实际耗时可能高于 2.52 小时 | 正式渲染首批 100 帧后重新校准 |
| 项目自身许可证未定 | 主仓库无 `LICENSE` | 需项目所有者选择 |
| 上游 DF4 模型无许可证文件 | 几何本体不入库 | 权利人仅许可公开展示渲染证据 |

## 下一阶段（未授权）

Stage 4.2 —— 正式渲染 900 帧并交付 MP4：

- 目录：`DF4_Render/Stage4_2_Final/{PNG_Master,MP4,MANIFEST.md}`。
- PNG 母版：`DF4_000001.png` … `DF4_000900.png`，无损存档。
- MP4：H.264 High Profile、1920×1080、30 FPS、CRF 16–18、slow、yuv420p、BT.709、Fast Start、无音轨。
- 必须支持中断续跑：已通过校验的帧不得重复渲染或覆盖。
- 复用 `scripts/rendering/render_cycles.py` 的参数与 `--skip-existing` 语义。

## 启动核对

1. 读 `README.md`、本文件、`stages/stage-4/INDEX.md`。
2. 核对两仓库 HEAD 与远端一致、工作区 clean。
3. 跑 `verify_evidence.py` 校验各阶段 `evidence-manifest*.json`，退出码须为 0。
4. 确认 `output/DF4/` 只有一个 `DF4.blend`，且 SHA256 为 `cfafc7c7…295a0`。
5. 未获授权前不渲染 900 帧、不生成 MP4、不修改正式工程。
