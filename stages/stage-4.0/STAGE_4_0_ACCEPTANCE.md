# Stage 4.0 验收说明

双击本地 `AeroViz-Blender/output/DF4/DF4.blend`。工程默认打开 `STAGE4_PRESENTATION` 展示场景，停在第1帧、主相机A视角，下方保留 Timeline。无需修改参数、关键帧或对象位置。

如果误离开相机视角，把鼠标放在画面内按数字小键盘 **0**；也可以用菜单 **View → Cameras → Active Camera** 返回。

把鼠标放在画面或 Timeline 上，按 **空格** 播放，再按一次暂停。完整范围为 **1–1650帧（55秒）**。暂停后在 Timeline 点击定位，或在当前帧数字框输入帧号；无需移动对象。Timeline 上的 S01–S17 标记对应镜头阶段。

| 验收项目 | 定位帧 | PNG文件 |
|---|---:|---|
| 完整机型与Hero登场 | 60 | `stage_00_hero.png` |
| 三脚架整体拆出 | 140 | `stage_01_legs_out.png` |
| 单脚架细节 | 165 | `stage_01_leg_closeup.png` |
| 外涵道逐片分离 | 264 | `stage_02_outer_duct_partial.png` |
| 动力系统 | 475 | `stage_03_power_system.png` |
| 舵面偏转 | 545 | `stage_04_surface_deflection.png` |
| 舵面与舵机依次退出 | 1034 | `stage_04_controls_servos.png` |
| 电池框架拆解 | 1334 | `stage_05_battery_frame.png` |
| 最终完整分解布局 | 1648 | `stage_06_final_exploded.png` |

PNG 位于 Audit 仓库 `stages/stage-4.0/evidence/images/`。直接双击 `stages/stage-4.0/evidence/video/DF4_Stage4_0_preview.mp4` 可观看完整预览，无需进入 Blender。
