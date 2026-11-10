# 产物与输入清单（ARTIFACT MANIFEST）

> 本文件是 AeroViz-Blender 全部交付产物的哈希索引与来源记录。所有 SHA256 均由脚本对
> 实际文件计算，不是手工誊写。审计仓库内的证据文件为逐字节拷贝，哈希与开发工作区一致。

- 开发仓库：<https://github.com/tangqingxi/AeroViz-Blender>
- 开发提交：`d956bec3d71b105d20f2bc9e192a940406d108f4`（`main`）
- 审计仓库：<https://github.com/tangqingxi/AeroViz-Blender-Audit>（Private）
- 生成日期：2026-11-10

---

## 1. 仓库可见性与发布决定

| 仓库 | 可见性 | 依据 |
|---|---|---|
| `AeroViz-Blender`（主仓库） | **Public** | 只含本项目编写的代码、配置与文档，不含任何第三方模型资产 |
| `AeroViz-Blender-Audit`（审计仓库） | **Private** | 含 DF4 模型的渲染与窗口截图，其再分发权未确立 |

任务要求"优先保持 Public"，但同一要求也规定："存在再分发权不明确的材料时，不得公开上传，先保留在本地或采用 Private 仓库并报告。" DF4 几何来自一个**没有任何许可证**的上游仓库（见 §6），因此截图与工程一律不公开，审计仓库设为私有。

**解除条件**：一旦确认 DF4 模型的再分发权（上游补充许可证，或权利人书面许可并记录在本文件），审计仓库可直接改为 Public，无需改动任何内容。

主仓库 `.gitignore` 同时屏蔽 `*.stl`、`*.sdf`、`*.sdf.jinja`、`*.urdf`、`*.step`、`*.blend` 与 `/output/`，从机制上防止模型资产被误提交。

## 2. 阶段报告

| 阶段 | 报告 | 证据清单 |
|---|---|---|
| Stage 1 | [`stages/stage-1/STAGE_1_REPORT.md`](../stages/stage-1/STAGE_1_REPORT.md) | [`stages/stage-1/evidence-manifest.json`](../stages/stage-1/evidence-manifest.json) |
| Stage 1.5 | [`stages/stage-1.5/STAGE_1_5_REPORT.md`](../stages/stage-1.5/STAGE_1_5_REPORT.md) | [`stages/stage-1.5/evidence-manifest.json`](../stages/stage-1.5/evidence-manifest.json) |

## 3. 原始输入（34 个文件，只读，不发布）

来源目录：`D:\01_科研\TIE\DF4_SolidWorks\DF4_SolidWorks`（**未**上传到任何仓库）。

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

## 4. 阶段工程文件（本地保留，不发布）

| 文件 | 大小 (B) | SHA256 | 说明 |
|---|---|---|---|
| `DF4_Stage1.blend` | 5397145 | `10caf87e82d5072801f4cdf10c1a3690696a1b60d94012cfecbc12403048bc8d` | 当前 Stage 1 工程 |
| `DF4_Stage1.blend1` | 5389699 | `574c1b0071c923f0513e41430c7c7d7b6c6ea5b62c24ddb0cae04d2c87d9afeb` | 前一次保存；**Stage 1.5 实际派生自这一版** |
| `DF4_Stage1_5.blend` | 5403119 | `216ae8ab7de87cac17846a304dcd34110008ef4a71ce77f1829c9a8a37c0e474` | 当前 Stage 1.5 工程 |
| `DF4_Stage1_5.blend1` | 5393663 | `fdce4368e07e7cc47034f0463a0d8f9ee29f09b702a0f701ad541e49d25deb01` | 前一次保存 |

这四个文件**只保留在本地工作区**（`output/DF4/`），原因见 §1。共享时另行约定 Git LFS 或 Release 交付方式；本轮不创建 Tag、不上传。

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

结论：截图与报告对应的是 **18:26 之前**的工程字节；磁盘上当前字节是图形会话退出时的重新保存。Stage 1.5 派生的那一版 Stage 1 字节被保留为 `DF4_Stage1.blend1`。为使"当前字节"也有依据，2026-11-10 又做了一次只读重开复验（§7）。

## 5. 审计仓库内的证据文件

逐文件哈希见两份 `evidence-manifest.json`（由 `build_manifest.py` 生成，`verify_evidence.py` 校验通过）。

| 目录 | 内容 |
|---|---|
| `stages/stage-1/evidence/` | 4 张图形窗口截图、1 张离线等轴测预览、`validation.json`、`gui_validation.json`、`joint_checks.json`、`input_manifest.json` |
| `stages/stage-1.5/evidence/` | Material Preview 整窗/视口截图、Eevee 渲染、`material_validation.json`、`material_gui_validation.json`、`material_structure_baseline.json`、`material_input_manifest.json` |
| `manifests/reverify-2026-11-10.json` | 只读重开复验记录（见 §7） |

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
3. 结论：DF4 的 STL、SDF、`.blend` 工程与一切渲染/截图**不得公开上传**。主仓库公开是安全的，因为它不含这些内容。

**待办**（需项目所有者决定，Agent 不得代选）：

- 本项目自身的许可证尚未确定，因此**没有放置 `LICENSE` 文件**，默认"保留所有权利"。若选 MIT / BSD-3-Clause / Apache-2.0，需同时补版权行。
- 若权利人确认可再分发 DF4 模型，请在上游补充许可证或在本文件记录书面许可，届时可将审计仓库改为 Public。

## 7. 只读重开复验记录（2026-11-10）

因工程在图形会话退出时被重新保存（§4 时间线），对**磁盘上当前字节**做了一次独立复核。使用的命令：

```powershell
& 'D:\app\Blender\blender.exe' --background --factory-startup --python-exit-code 1 `
  --python '.\tests\reverify_saved_project.py' -- --config configs/DF4.json
```

输出 `REVERIFY_OK`，记录见 [`reverify-2026-11-10.json`](reverify-2026-11-10.json)：

| 检查 | 结果 |
|---|---|
| Stage 1 网格数 / 可见 / 参考件 | 33 / 27 / 6 |
| Stage 1 `LINK::` / `JOINT::` | 26 / 25 |
| Stage 1 世界矩阵最大误差 | 0.0 |
| Stage 1 可见包围盒最大偏差 | 1.49e-08 m（记录方式差异，非尺寸变化） |
| Stage 1 对象总数 | 89 |
| Stage 1.5 基线对象保留 | 89 / 89 |
| Stage 1.5 新增对象 | 仅 4 个 `MATERIAL_LIGHT::*` |
| Stage 1.5 材质绑定与 BSDF 数值 | 33 个对象全部一致，最大误差 2.86e-08 |
| 材质数 / 引擎 | 7 / `BLENDER_EEVEE` |
| 两个工程的动画数据 | 0 个对象 |

该记录证明**当前字节**仍满足 Stage 1/1.5 记录的全部断言，但不能替代"截图时刻的原始字节"——本地没有更早的字节归档，这一点已在两份报告的"未解决问题"中列明。
