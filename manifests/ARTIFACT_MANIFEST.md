# 产物与输入清单（ARTIFACT MANIFEST）

> 本文件是 AeroViz-Blender 全部交付产物的哈希索引与来源记录。所有 SHA256 均由脚本对
> 实际文件计算，不是手工誊写。审计仓库内的证据文件为逐字节拷贝，哈希与开发工作区一致。

- 开发仓库：<https://github.com/tangqingxi/AeroViz-Blender>
- 开发提交：`f7cbd09837037480f5a7df4325a49b5a57b68440`（`main`）
- 审计仓库：<https://github.com/tangqingxi/AeroViz-Blender-Audit>
- 更新日期：2026-11-11

---

## 1. 文件管理边界

| 内容 | 是否入库 | 原因 |
|---|---|---|
| 33 个 STL、`ductedfan4.sdf.jinja` | 否 | 第三方几何，上游无许可证文件；体积 |
| 当前工程 `DF4.blend`（唯一，约 5.4 MB） | 否 | 体积大、含第三方几何 |
| 本地 `preview/`、`reports/`、`.blend1` | 否 | 已清理；预览与验证记录改为直接写入本仓库的证据目录 |
| 渲染与窗口截图、测量 JSON、阶段报告 | 是（本仓库） | 阶段验收证据 |
| 代码、配置、文档 | 是（主仓库） | 本项目编写，不含几何 |

主仓库 `.gitignore` 屏蔽 `*.stl`、`*.sdf`、`*.sdf.jinja`、`*.urdf`、`*.step`、`*.blend` 与 `/output/`，防止模型资产被误提交。需要在团队内共享工程文件时走 Git LFS 或 Release，不在仓库里放二进制。

## 2. 阶段报告

完整阶段索引见根 [`README.md`](../README.md)；Stage 4 的四个修订版 + 4.1 见 [`stages/stage-4/INDEX.md`](../stages/stage-4/INDEX.md)。

| 阶段 | 报告 | 证据清单 |
|---|---|---|
| Stage 1 | [`stages/stage-1/STAGE_1_REPORT.md`](../stages/stage-1/STAGE_1_REPORT.md) | [`stages/stage-1/evidence-manifest.json`](../stages/stage-1/evidence-manifest.json) |
| Stage 1.5 | [`stages/stage-1.5/STAGE_1_5_REPORT.md`](../stages/stage-1.5/STAGE_1_5_REPORT.md) | [`stages/stage-1.5/evidence-manifest.json`](../stages/stage-1.5/evidence-manifest.json) |
| Stage 2 | [`stages/stage-2/STAGE_2_REPORT.md`](../stages/stage-2/STAGE_2_REPORT.md) | [`stages/stage-2/evidence-manifest.json`](../stages/stage-2/evidence-manifest.json) |
| Stage 3 | [`stages/stage-3/STAGE_3_REPORT.md`](../stages/stage-3/STAGE_3_REPORT.md) | [`stages/stage-3/evidence-manifest.json`](../stages/stage-3/evidence-manifest.json) |
| Stage 4.0-R3（当前基线） | [`stages/stage-4/STAGE_4_0_R3_REPORT.md`](../stages/stage-4/STAGE_4_0_R3_REPORT.md) | [`stages/stage-4/evidence-manifest-stage-4.0-r3.json`](../stages/stage-4/evidence-manifest-stage-4.0-r3.json) |
| Stage 4.1（画质定标） | [`stages/stage-4/STAGE_4_1_CYCLES_REPORT.md`](../stages/stage-4/STAGE_4_1_CYCLES_REPORT.md) | [`stages/stage-4/evidence-manifest-stage-4.1.json`](../stages/stage-4/evidence-manifest-stage-4.1.json) |

## 3. 原始输入（34 个文件，只读，不发布）

来源目录：`../DF4_SolidWorks`（**未**上传到任何仓库）。

| 输入文件 | 大小 (B) | SHA256 |
|---|---|---|
| `ductedfan4.sdf.jinja` | 46482 | `8567be57b6181812bc0f20c8bd065b02f89eeec0f6b3047ca02154786e5b52c4` |
| `meshes/X-tend.STL` | 30284 | `e7f833d938f25d9263ddefcc7dca1652e2ed1e5d8668f125f56a01717b45e3ff` |
| `meshes/base.STL` | 2660184 | `b459ad3a9e9207dc2317439cf9c1983bdcffbf5e01ea70184a3313fe49555f26` |
| `meshes/base_board_flyctrl.STL` | 96584 | `5733a2dca0c3fad377ed888a4c83d67fcb56dddd403ad38c3ffbfa7d3b2b9384` |
| `meshes/battery-4s-10000-2.STL` | 684 | `e0d6c87ce8fce37b8278e8a06a9e522a15424b60931b0058c4f65677b6ba7bce` |
| `meshes/bec-Hobbywing-Platinum.STL` | 684 | `40c760f56e46ed8542188ca3e0024f1529b1b942acdd25f54e3ad494d803a278` |
| `meshes/box_up.STL` | 139584 | `2859507769e03d03c1152f9c6a993ea968c2f565e355aef918f2dc3c08b10d1c` |
| `meshes/box_up2.STL` | 47684 | `1be6087d1f4a9a73298fe502d100249a1cd423e2b024e553dc6594c4e5d7322e` |
| `meshes/controller2.STL` | 30684 | `472610d149cb3382e5749814f02de3b99a2865e924fe39cf16f6cdc2ef3cf05b` |
| `meshes/cs11.STL` | 451984 | `cd7cc90e1a4d9ec20b2cc23df0f1b7729a9a9eec6e6f1cb8f4818574f3178bbc` |
| `meshes/cs2.STL` | 451984 | `8c5c49b51bbb59dae2b94c038291cb302b77e8374edf1bc1b5d1da2d028727ba` |
| `meshes/cs33.STL` | 451984 | `4bff5de0af83870a4778d17c8bda1aa089d5923ffea302602071ae41bb60a1b8` |
| `meshes/cs4.STL` | 451984 | `ee727ea57d4dae7b7f50d831816c331ca7858d92700609c46203db9e8fd039be` |
| `meshes/duct-in.STL` | 1379884 | `d1c7b99f055a820a832b1a71e247e4324f3e78e7eb13c937d43e8b12b5568881` |
| `meshes/duct-out-1.STL` | 183584 | `9839b6094cefb318b430ff4d0bfe1a73e7a21c9c88a9c9b3638385133ea51294` |
| `meshes/duct-out-2.STL` | 183584 | `55ef4263f8e4b029a886dc6bb4d7c401ba1a8845dcd8a86c7c791e947848dd2e` |
| `meshes/duct-out-3.STL` | 183584 | `bb5bf4b4b157cd28b794692b97b1e3cb823ba33a05b3362b09ce511afd132ac9` |
| `meshes/motor-Sunnysky-X2814III-1000KV.STL` | 19084 | `166e46509f9425f7ebd8eaf4a27df93504ffe6777769721607de0e1a1a0a2309` |
| `meshes/panel11.STL` | 58284 | `cf5c5b6c7ecdfb54bad5ea03e01e205d4423b587dd0bec511f003b4193aeb4fb` |
| `meshes/panel12.STL` | 58284 | `6413c9d979b6a40d89f3be335f1b6743fa324cf5dbdbd7d5cc79b5b36cff5f72` |
| `meshes/rotor-iFlight-9inch.STL` | 2538484 | `2fe5e5cc3e9573b31f3ec3b3e4275b725dd20e58d5a5a6b01c678c452a8d5935` |
| `meshes/rotor.STL` | 2538484 | `2fe5e5cc3e9573b31f3ec3b3e4275b725dd20e58d5a5a6b01c678c452a8d5935` |
| `meshes/servo-KST-X08H-1.STL` | 24284 | `e685562ec15ecbc77bf769a5b68b81f1bada9cc80458cb80ef46877ec77d2ea4` |
| `meshes/servo-KST-X08H-2.STL` | 24284 | `37a0bcc929836c091f607d9dc117381d9f4d5e8cfe9c93700f5df03bccaeb328` |
| `meshes/servo-KST-X08H-3.STL` | 24284 | `07d6ffa2c5905023093e2a2058b830e1a7c87c655c7f001f9381bb8fe6309e8d` |
| `meshes/servo-KST-X08H-4.STL` | 24284 | `98a720565b653a989823eb8a12c460438ce3946a9b667c4d3d7911bf5805275c` |
| `meshes/shelf1.STL` | 35284 | `fa1baa8ccf13150f3f908cec4a1f619edf2318914b81faa4782d6630ece2942c` |
| `meshes/surface-60-1.STL` | 451984 | `4bff5de0af83870a4778d17c8bda1aa089d5923ffea302602071ae41bb60a1b8` |
| `meshes/surface-60-2.STL` | 451984 | `8c5c49b51bbb59dae2b94c038291cb302b77e8374edf1bc1b5d1da2d028727ba` |
| `meshes/surface-60-3.STL` | 451984 | `cd7cc90e1a4d9ec20b2cc23df0f1b7729a9a9eec6e6f1cb8f4818574f3178bbc` |
| `meshes/surface-60-4.STL` | 451984 | `ee727ea57d4dae7b7f50d831816c331ca7858d92700609c46203db9e8fd039be` |
| `meshes/tail-1.STL` | 59284 | `b5f4043625b7cb286cb0556d5e47dc74e81ebbbd1df4d5762b3d6c66f8b4f096` |
| `meshes/tail-2.STL` | 59284 | `4ee0900bb9f0e82bec10c1739050cab4d13d9e926c0b8c3a5c5687cbb79bf0ad` |
| `meshes/tail-3.STL` | 59284 | `b6c1bed67516ed01c2ff1773679e27875eda0d683f2cfce7ebd5e8408995a238` |

这 34 个哈希在校验前后各取一次并完全一致（Stage 1 的 `validation.json` 中 `input_unchanged: true`，Stage 1.5 的 `material_input_manifest.json` 独立复核）。逐件相同的几何可见于 `cs11 = surface-60-3`、`cs2 = surface-60-2`、`cs33 = surface-60-1`、`cs4 = surface-60-4`、`rotor = rotor-iFlight-9inch` 五对文件哈希完全相同。

## 4. 工程文件（唯一当前工程 + 历史字节）

| 文件 | 大小 (B) | SHA256 | 说明 |
|---|---|---|---|
| `DF4.blend` | 5422781 | `392af12f14a6fbfb27b201d836b86752c90a97afbc024960fc00f03407726824` | **当前唯一工程**：Stage3坐标元数据与24个独立爆炸位移层；原93对象和旧5个Action保留 |

历史字节（2026-11-10 本地清理时删除，仅保留哈希）：

| 文件 | 大小 (B) | SHA256 | 说明 |
|---|---|---|---|
| `DF4_Stage1.blend` | 5397145 | `10caf87e82d5072801f4cdf10c1a3690696a1b60d94012cfecbc12403048bc8d` | Stage 1 工程 |
| `DF4_Stage1.blend1` | 5389699 | `574c1b0071c923f0513e41430c7c7d7b6c6ea5b62c24ddb0cae04d2c87d9afeb` | 前一次保存；**Stage 1.5 实际派生自这一版** |
| `DF4_Stage1_5.blend` | 5403119 | `216ae8ab7de87cac17846a304dcd34110008ef4a71ce77f1829c9a8a37c0e474` | Stage 1.5 工程，即当前工程的前身 |
| `DF4_Stage1_5.blend1` | 5393663 | `fdce4368e07e7cc47034f0463a0d8f9ee29f09b702a0f701ad541e49d25deb01` | 前一次保存 |

当前工程只保留在本地 `output/DF4/`，原因见 §1；完整 `.blend` 不上传，共享时另行约定 Git LFS 或 Release 交付方式。

### 字节时间线（重要）

| 时间（2026-11-10） | 事件 |
|---|---|
| 17:57:33 | Stage 1 构建，写出 `DF4_Stage1.blend` 与四张离线预览 |
| 17:58:05 | 启动 Stage 1 图形进程 |
| 17:58:14–17:58:22 | 捕获四张 `gui_*.png` 窗口截图 |
| 17:59:35 | 关节传递检查通过（`JOINT_HIERARCHY_OK 5`） |
| 18:00:08 | 写出 `validation.json` / `gui_validation.json` / `IMPORT_REPORT.md` |
| 18:12:53 | Stage 1.5 构建，写出 `DF4_Stage1_5.blend` 与 `eevee_preview.png`；此时被保护的 Stage 1 工程哈希为 `574c1b00…` |
| 18:13:53 | 捕获 `material_preview*.png` |
| 18:14:30 | 写出 `material_validation.json` / `MATERIAL_REPORT.md` |
| 18:26:44–18:26:45 | 两个图形进程退出时 Blender 执行 `Saved "…blend"`，工程被重新保存（原字节成为 `.blend1`） |
| 19:1x | 归一化：`DF4_Stage1_5.blend` **字节不变**重命名为 `DF4.blend`；其余阶段工程与 `.blend1` 本地删除 |

历史结论：Stage 1/1.5 截图与报告对应的是 **18:26 之前**的工程字节；归一化后的静态 `DF4.blend` 是图形会话退出时的重新保存结果，与 `DF4_Stage1_5.blend` 完全同字节。Stage 2 当前字节已按本节最新表更新。Stage 1.5 派生的那一版 Stage 1 字节曾是 `DF4_Stage1.blend1`，现已删除、只留哈希。历史静态字节已复验，当前动画字节的只读复验见更新后的 §7。

## 5. 审计仓库内的证据文件

逐文件哈希见各阶段 `evidence-manifest.json`（由 `build_manifest.py` 生成，`verify_evidence.py` 校验通过）。

| 目录 | 内容 |
|---|---|
| `stages/stage-1/evidence/` | 4 张图形窗口截图、1 张离线等轴测预览、`validation.json`、`gui_validation.json`、`joint_checks.json`、`input_manifest.json` |
| `stages/stage-1.5/evidence/` | Material Preview 整窗/视口截图、Eevee 渲染、`material_validation.json`、`material_gui_validation.json`、`material_structure_baseline.json`、`material_input_manifest.json` |
| `stages/stage-2/evidence/` | 独立运动、121帧组合、连续转角、结构基线、正式回归、七张真实窗口截图与日志 |
| `stages/stage-3/evidence/` | 爆炸/恢复语义比较、坐标测试、六帧真实窗口截图、正式回归 |
| `stages/stage-4/evidence/stage-4.0/` | 4.0 原型：源基线、回归、GUI 布局、低清预览 MP4 |
| `stages/stage-4/evidence/stage-4.0-r1/` | R1：回归、电池路径、接触表、输入保全 |
| `stages/stage-4/evidence/`（顶层） | **R2** 机器证据与 `STAGE_4_0_R2_OVERVIEW.png` |
| `stages/stage-4/evidence/r3/` | **R3** 机器证据（当前基线的回归与重开验证） |
| `stages/stage-4/evidence/stage4_1/` | **4.1** Cycles 总览图与渲染记录 |
| `manifests/reverify-2026-11-10.json` | 归一化之前两个阶段工程的复验记录（历史） |

未复制到审计仓库的文件（体积大且可重生成）：`build.log`、`material_build.log`、`material_mapping_tests.log`、`joint_checks.log`、`gui_process.log`、`material_gui_process.log`、`*_pid.txt`、四张离线正交预览（`front/top/side/isometric`，等轴测已收）。

## 6. 上游来源与许可证核查

| 项目 | 结果 |
|---|---|
| 推定上游仓库 | <https://github.com/mengchaoheng/DF_gazebo>（描述："This is a flight simulator for Ducted Fan UAV"） |
| 上游默认分支 | `ductedfan` |
| 对应模型目录 | `models/ductedfan4/`（含 `ductedfan4.sdf.jinja`、`model.config`、`meshes/`） |
| 上游许可证字段 | GitHub API 返回 `"license": null` |
| 上游根目录许可证文件 | **不存在** `LICENSE` / `COPYING` / `NOTICE`（2026-11-10 核查） |
| 上游 README 许可证声明 | 未发现 |
| 本地描述文件 | 46 482 B，`8567be57…`（git blob `5755d40a…`） |
| 上游同名文件 | 38 859 B，git blob `62b55d92…` |

**判定：**

1. 上游**未授予任何再分发许可**，公开仓库缺少许可证时默认"保留所有权利"。
2. 本地描述文件与上游**字节不同**（46 482 B vs 38 859 B），本地副本含 PX4/MAVLink 侧改造（例如 `<include>` 外部 `model://gps`、质量保持 1.56 kg 的注释）。因此本地数据是**修改派生版本**，且无法确定其对应的上游提交。
3. 结论：DF4 的 STL、SDF 与 `.blend` 工程不入库（与 §1 一致）；本仓库只保存报告、截图与测量记录。
4. 项目所有者已确认取得权利人许可，允许**公开展示**模型渲染图与相关可视化证据。该许可不自动扩大为原始 STL、SDF 或完整 `.blend` 工程的再分发许可。

**待办**：

- 本项目自身的许可证尚未确定，因此**没有放置 `LICENSE` 文件**，默认"保留所有权利"。若选 MIT / BSD-3-Clause / Apache-2.0，需同时补版权行。
- 上游无许可证文本；若将来需要把几何本体对外共享，先确认许可再执行。

## 7. 历史只读复验记录

### 7.1 Stage 3 基线（2026-11-10）

Stage3在用户批准的新字节基线上加入坐标元数据与24个独立位移层，对**磁盘上当前字节**执行历史断言、Stage2原121帧与Stage3至301帧的复核。新旧基线完整语义一致，记录见Stage3 semantic_comparison.json；历史Stage2交付哈希保持不变。命令：

```powershell
& '<blender.exe>' --background --factory-startup --python-exit-code 1 `
  --python '.\tests\reverify_saved_project.py' -- --config configs/DF4.json
```

输出 `REVERIFY_OK`。该脚本读取本仓库已归档的 Stage 1 / 1.5 期望值，不依赖本地 `output/reports`：

| 检查 | 结果 |
|---|---|
| 工程 SHA256 | `392af12f14a6fbfb27b201d836b86752c90a97afbc024960fc00f03407726824` |
| 对象总数 | 117（原93 + 24爆炸Empty） |
| Stage 1 网格数 / 可见 / 参考件 | 33 / 27 / 6 |
| Stage 1 `LINK::` / `JOINT::` | 26 / 25 |
| Stage 1 世界矩阵最大误差 | 0.0 |
| Stage 1 可见包围盒最大偏差 | 1.49e-08 m（记录方式差异，非尺寸变化） |
| Stage 1.5 基线对象保留 | 89 / 89；24个JOINT父级使用明确白名单 |
| 受控新增对象 | Stage1.5的4个灯 + Stage3配置24个偏移Empty |
| Stage 1.5 材质绑定与 BSDF 数值 | 33 个对象全部一致，最大误差 2.86e-08 |
| 材质数 / 引擎 | 7 / `BLENDER_EEVEE` |
| 动画数据 | 旧5个JOINT + 新24个偏移Empty；其他原对象无新增动画 |

归一化之前的记录 [`reverify-2026-11-10.json`](reverify-2026-11-10.json) 保留作为历史：它对应 `DF4_Stage1.blend` 与 `DF4_Stage1_5.blend` 两个文件，那两份字节已在本轮清理中删除。

### 7.2 当前字节（Stage 4.0-R3）

当前正式工程 `output/DF4/DF4.blend` 的完整回归与重开验证在 [`stages/stage-4/evidence/r3/`](../stages/stage-4/evidence/stage-4.0-r3/)（`saved_project_regression.json`、`final_reopen_validation.json`、`r2_compatibility_regression.json`），工程 SHA256 为 `cfafc7c7…295a0`。Stage 4 各版本的有效性以 [`stages/stage-4/INDEX.md`](../stages/stage-4/INDEX.md) 为准。

2026-11-11 删除的 `manifests/reverify-current.json` 与 `stages/stage-4/evidence/stage-4.0-r1/saved_project_regression.json` **逐字节相同**（`c48eec1c…`），内容是 R1 期数据，文件名却暗示"当前"。权威副本仍在 R1 证据目录中，删除不影响历史可追溯性。

## 8. 仓库整理时的一次性迁移校验（2026-11-10）

本轮把两个导入模块移入 `adapters/` 并引入注册表，需要证明"整理"没有改变解析行为。校验方式：在 Blender 后台导入新包结构，重新解析 DF4 描述文件，并与 Stage 1/1.5 已记录的基线逐项比对。记录见 [`refactor-check-2026-11-10.json`](refactor-check-2026-11-10.json)：

| 项目 | 结果 |
|---|---|
| 注册表映射 | `sdf → adapters.import_sdf`、`stl → adapters.import_stl`；未注册键抛错 |
| 重新解析的部件 / link / 关节 | 25 / 26 / 25 |
| 外部 include / 跳过关节 | 1 / 1 |
| 材质记录（带定义） | 25（25） |
| 预计网格对象数 | 33（与 `validation.json` 的 `imported_count` 一致） |
| STL 支持单位 | `m`、`mm`、`cm` |
| 结果 | `PASS` |

同时复跑了 `tests/test_material_mapping.py`（`MATERIAL_MAPPING_TESTS_OK`）。该迁移校验脚本为一次性使用、未纳入开发仓库；长期回归依赖开发仓库的 `tests/reverify_saved_project.py`。

### Stage 2 / Stage 3 阶段结束时的工程字节（历史）

Stage2历史交付为 `c206c5daf61c182982101bdbe8bd797fe0ea47e52dd5855989f16c2f84d8873b`。本轮当前文件为 `5e96e2af3f88d7f5bedc8b9041b6404b039c851c8c089517c995b675222b5943`，用户明确接受，不恢复旧备份；所要求机械语义完整比较一致。Stage3最终为 `392af12f14a6fbfb27b201d836b86752c90a97afbc024960fc00f03407726824`，保存后独立进程回归PASS，历史阶段报告和证据没有改写。证据位于 stages/stage-3/evidence，完整工程不上传。


## 9. Stage 4.0 历史交付

- 唯一正式工程：`<DEV>/output/DF4/DF4.blend`，5,466,403字节，SHA256 `489553c18fffb5c12cbce8efcc5c41ced7f6d1e507c7bda90988e684565c60d7`。
- 原Scene117对象/33网格/7材质/29动画对象保持；新增展示Scene67对象，整体184对象/8材质。
- 低清MP4：`stages/stage-4/evidence/stage-4.0/video/DF4_Stage4_0_preview.mp4`，55秒、960×540、15FPS、825帧。
- 一张本地总览图（14帧拼接，分散帧已清理）、GUI布局证据、主报告及验收说明均在Stage4.0目录；完整清单与哈希见该目录evidence-manifest.json。
- 技术回归PASS，等待人工效果验收；4.1–4.3未授权。本文既有Stage1–3哈希保留为历史，不替换历史交付记录。


用户最新图片交付规范：以后各阶段只提供一张本地总览图，分散帧只作临时输入；images图片不上传GitHub。当前分支已移除14个图片文件并加入目录忽略规则，历史提交保留。公开清单与本地图片记录分列。


## 10. Stage 4.0-R1 历史交付

- 唯一正式工程：`<DEV>/output/DF4/DF4.blend`，5,498,544字节，SHA256 `da631cf33dfc6ecb8a4c0a1393b13831067967f79fb83886a1dee0bf18629287`。
- 原117对象/33网格/7材质/29 Action全部保留；既有67展示对象保留，现72展示对象，整体189对象/8材质。
- 33秒、30FPS、1–990帧，811–870分解停留，871–960逆序回装，961–990完整机型保持。
- 本地只交付`stages/stage-4/evidence/stage-4.0-r1/images/STAGE_4_0_R1_OVERVIEW.png`。18个正式工程实际渲染画面拼接；无MP4，分散帧清理，images不上传GitHub。
- 源输入34文件哈希一致，全部源回归、姿态/同步±20°限位、侧向电池、回装/构图、14,647自适应几何样本及真实GUI通过。完整报告与哈希见R1目录。
- 状态为READY FOR USER VISUAL ACCEPTANCE，尚未获得用户效果认可。原Stage4.0及Stage1–3报告/哈希保持历史。


## 11. Stage 4.0-R2 历史交付

- 唯一正式工程：`<DEV>/output/DF4/DF4.blend`，5,518,390字节，SHA256 `766faf3114d05f2b3f0193ae8cc0ecd0aeb0e08f476afcc686e34d59be8af197`。
- DEV：`4b8dca8ef2e2810f2c40477f8c394ff8c4d49b21`。源117对象/33网格/7材质/29Action保持；R1展示72对象保留，只增POWER，展示73/全局190对象。
- 33秒、30FPS、1–990帧，14镜头；机体静止开场，完整动力组件共同退出，舵面同步±20°后依次退出，电池-Y380mm，完整分解后逆序回装。
- 唯一图片：`stages/stage-4/evidence/STAGE_4_0_R2_OVERVIEW.png`，18个正式工程渲染画面合图；按本轮明确路径提交一张总览图，历史images仍忽略。无新MP4或序列。
- Stage1–3/源输入34文件哈希/17,245几何样本/动力与舵面/电池连续扫掠/正式重开/真实GUI播放全部PASS。回装误差2.45e-16。历史阶段目录不改写，临时副本及PNG结束清理。
- 状态READY FOR USER VISUAL ACCEPTANCE，用户效果验收PENDING。Blender保持Camera A、Frame1、停止播放，等用户按空格检查。


## 12. Stage 4.0-R3 当前基线交付

- 唯一正式工程`<DEV>/output/DF4/DF4.blend`，5,519,908字节，SHA256 `cfafc7c7245654409a378a7c16267251a3307863dfcfb6c288ac53c1674295a0`，DEV `e38ecc3f646eaccdd16c13cf7cc6593fce02a870`。
- 实际R2基线766faf31…保留回归和字节备份记录，未回退R1。源117对象/33网格/7材质/29Action及展示73对象保持，不改原几何/父级/材质。
- 30秒、30FPS、1–900帧、10章节；C只保留涵道/完整动力，四舵面同步±20°后同步退出与同步返回，完整动力和-Y380mm电池保留。
- 691–750分解保持2秒，751–870逆序回装4秒，871–900完整机型1秒。恢复误差2.45e-16；13,981自适应网格子帧无新增相交对，源输入34哈希/完整回归/真实GUI通过。
- 唯一图片`stages/stage-4/evidence/STAGE_4_0_R3_OVERVIEW.png`，16画面由正式工程实际渲染。R3记录单独存evidence/r3，历史报告/清单保持，无新MP4或分散序列；.work/stage-4-r3清理。
- READY FOR USER VISUAL ACCEPTANCE，效果验收PENDING。Blender保持Camera A、第1帧、停止播放，等待用户检查。

> Stage 4 各版本的判定以 [`stages/stage-4/INDEX.md`](../stages/stage-4/INDEX.md) 为准；本节的"当前"指 R3 交付时点。

## 13. Stage 4.1 画质定标

- 只读使用 R3 工程，工程字节未变（`cfafc7c7…295a0`）。渲染在 `<out>/_work/` 的临时副本上进行，未把任何 Cycles 设置写回正式工程。
- 参数：Cycles GPU/OptiX、1920×1080 100%、30 FPS、256 samples、Adaptive 0.01、OpenImageDenoise（Albedo+Normal，prefilter ACCURATE）、AgX + `AgX - Medium High Contrast`、Exposure −0.1、PNG RGB 8-bit、背景不透明、Motion Blur 关闭。
- 8 帧实测：合计 80.64 s，平均 10.08 s/帧；900 帧推算约 2.52 小时、PNG 母版约 1.63 GB。
- 交付物：[`STAGE_4_1_CYCLES_REPORT.md`](../stages/stage-4/STAGE_4_1_CYCLES_REPORT.md)、总览图 [`stage4_1/STAGE_4_1_CYCLES_QUALITY_OVERVIEW.png`](../stages/stage-4/evidence/stage-4.1/STAGE_4_1_CYCLES_QUALITY_OVERVIEW.png)、渲染记录 [`stage4_1/stage4_1_render_record.json`](../stages/stage-4/evidence/stage-4.1/stage4_1_render_record.json)。
- 8 张全分辨率 PNG 仅存本地 `DF4_Render/Stage4_1_QualityTest/frames/`，不入库。
- 状态：**READY FOR USER QUALITY ACCEPTANCE**。Stage 4.2（900 帧 + MP4）未授权，正式工程不保存 Cycles 设置。
