# AeroViz-Blender

AeroViz是通用航空器三维可视化平台，Blender是当前实现平台，DF4是首个完成装配、材质、机械运动、展示镜头与正式渲染的验证案例。

DF4可视化工作流已完成。本轮只整合审计仓库与收尾，不启动Stage5多机型适配或其他开发。

## 阶段状态

| 阶段 | 状态 |
|---|---|
| Stage 1 | 完成：模型导入与装配恢复 |
| Stage 1.5 | 完成：SDF材质恢复 |
| Stage 2 | 完成：机械运动骨架 |
| Stage 3 | 完成：FLU坐标与爆炸恢复 |
| Stage 4.0-R3 | 完成并验收：展示镜头和机械拆解 |
| Stage 4.1 | Cycles画质定标通过 |
| Stage 4.2 | 900帧PNG与MP4正式渲染完成 |
| DF4可视化工作流 | 已完成 |
| Stage 5 | 暂不启动 |

## 当前产物

- 唯一正式工程：`output/DF4/DF4.blend`，本地保留，不上传Git。
- SHA256：`cfafc7c7245654409a378a7c16267251a3307863dfcfb6c288ac53c1674295a0`。
- 正式渲染：仓库外`../DF4_Render/Stage4_2_Final/`，900张1920×1080 PNG及正式MP4；不迁移、不删除、不上传。
- 历史审计：[audit/DF4](audit/DF4/README.md)，已通过不使用squash的Git Subtree成为主仓库的一部分。
- [审计总入口](audit/README.md)、[迁移报告](audit/MIGRATION_REPORT.md)、[Stage4.2正式渲染报告](audit/DF4/stages/stage-4/STAGE_4_2_FINAL_RENDER_REPORT.md)。历史Stage4.0低清MP4仅作过程证据，不是正式成片。

## 代码与数据

| 目录 | 职责 |
|---|---|
| configs/ | 模型路径、单位、零件分组和展示配置 |
| adapters/ | SDF与STL格式适配 |
| scripts/ | 导入、场景、材质、运动、展示与渲染 |
| tests/ | 保存后完整回归与阶段专项验证 |
| assets/ | 通用展示资产 |
| docs/ | 架构、接口、来源与操作说明 |
| audit/DF4/ | 历史报告、截图、测量、证据清单和原Audit Git历史 |
| output/ | 唯一本地工程，Git忽略 |

模型输入位于仓库外`../DF4_gazebo/`，只读。配置与通用格式导入逻辑分离；展示阶段专用模块为DF4首个验证案例的实现，不表示其他机型已适配。原机械Action、网格几何和真实安装关系受回归保护。后续增加格式使用独立适配器，不引入不必要依赖。

## 检查与使用

Blender 5.0.1打开`output/DF4/DF4.blend`；展示Scene为STAGE4_PRESENTATION，30FPS、1–900帧。主画面或Timeline上按空格播放/暂停，数字小键盘0返回相机视角，无需修改对象。

证据验证的root是`audit/DF4`：

```powershell
python scripts/verify_evidence.py audit/DF4 audit/DF4/manifests/evidence-manifest.json
```

所有阶段清单和Stage4.1/4.2记录见[审计入口](audit/DF4/README.md)。[架构](docs/architecture.md)、[接口](docs/interfaces.md)、[模型来源](docs/asset-provenance.md)、[新机型配置说明](docs/model-onboarding.md)、[展示操作](docs/stage4-acceptance.md)。模型输入、Blend、900张正式PNG与正式MP4不纳入版本控制；只维护当前主仓库。
