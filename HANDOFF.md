# Agent Handoff — Stage 4.0 展示原型完成，待人工效果验收

- DEV：<https://github.com/tangqingxi/AeroViz-Blender>，main，`51b04a79f5b9fd37c1ce6aed4740775b33714edc`（已推送）。
- AUDIT：<https://github.com/tangqingxi/AeroViz-Blender-Audit>，main，最终提交见交付消息/Git HEAD。
- 两仓库Public，不上传.blend/STL/SDF，不force push、不创建Tag。

**Stage 4.0：技术PASS，人工效果验收PENDING。4.1–4.3未授权。**

唯一当前工程：`<DEV>/output/DF4/DF4.blend`，SHA256 `489553c18fffb5c12cbce8efcc5c41ced7f6d1e507c7bda90988e684565c60d7`。
原Scene117对象/33网格/7材质/29原Action完整保留，1–301帧，Stage1–3完整回归PASS。FLU +X前/+Y左/+Z上，原点是SDF原点，非已测CG。历史Stage3哈希392af12f…和Stage2 c206c5da…保留在原报告，不改写。

新增STAGE4_PRESENTATION场景，67个带所有权标记的对象：27个共享Mesh/原材质的实例，23模块Empty、5个NLA轴心、3相机、3目标、5灯、1地面。整体184对象/8材质。五个原Action以NLA片段复用，不复制修改。17镜头、17相机切换标记与17可读S01–S17阶段标记。30FPS 1–1650帧。

冻结顺序：三脚架整体→外涵道三片逐个→电机揭示/退出→旋翼揭示/退出→内涵道→四舵面偏转/逐个退出→四舵机→电池→上框/飞控→两侧板/GPS固定平面→下框→电调→两片夹持件→终态全景。舵机展示对应1/cs11、2/cs2、4/cs33、3/cs4，依据几何方位，未虚构连杆。controller2悬空、X-tend相对位置保持Gazebo现状。

55秒960×540/15FPS MP4与一张本地总览图（14帧拼接，分散帧已清理）均在`stages/stage-4.0/evidence/`，主报告只有`STAGE_4_0_REPORT.md`一份；简短中文验收说明按用户明确要求单列。MP4全825帧解码PASS，预览副本与正式工程渲染输入签名一致，静帧从正式工程重新渲染。

## 用户最新窗口要求

用户本轮补充明确要求最终保持窗口，覆盖此前“截图后退出”偏好。已真实打开工程、完整播放循环、暂停回第1帧与相机A，保存主相机默认视图，底部Timeline约220像素且显示全范围/阶段标记。当前保留该窗口，用户只需空格播放/暂停。GUI截图只证明布局，不是最终展示素材。

## 复验与清理

`scripts/presentation.py`保留源快照/独立展示/NLA/1650逐帧/746主相机构图检查。`tests/reverify_saved_project.py`先检展示层与源指纹，再在只读进程内移除已验证的新增层，沿用历史全局计数断言，不保存该内存状态。源基线永久保存在Audit Stage4.0 evidence，不依赖.work。

正式工程原子更新前完成副本测试，更新后独立进程回归；布局保存后又重开验证。原输入34文件与Stage1归档逐字节哈希一致。临时备份/825帧序列已按project_io受限清理接口处理，详见delivery_checks.json。没有重做机械运动或修正装配。

下一步只等待用户观看MP4并验收节奏/镜头/拆解布局。不得自动进入4.1精修、4.2高质量渲染、4.3剪辑交接，也不得重导模型或改实机装配关系。


用户最新图片交付规范：以后各阶段只提供一张本地总览图，分散帧只作临时输入；images图片不上传GitHub。当前分支已移除14个图片文件并加入目录忽略规则，历史提交保留。公开清单与本地图片记录分列。
