# Agent Handoff — Stage 4.0-R1 就绪，待用户视觉验收

- DEV：<https://github.com/tangqingxi/AeroViz-Blender>，main，`33834c8ba51e0a400477c64d148a5eb87a51a880`（已推送）。
- AUDIT：<https://github.com/tangqingxi/AeroViz-Blender-Audit>，main，当前提交见交付消息/Git HEAD。
- 两仓库Public；不force push、不创建Tag、不上传.blend/STL/SDF或渲染序列。

**STAGE 4.0-R1: READY FOR USER VISUAL ACCEPTANCE**。用户尚未认可效果；不进入4.1精修、最终高质量渲染或Premiere交接。

## 当前工程

唯一正式工程：`<DEV>/output/DF4/DF4.blend`，SHA256 `da631cf33dfc6ecb8a4c0a1393b13831067967f79fb83886a1dee0bf18629287`。
Stage4.0基线489553c1…、Stage3历史392af12f…和Stage2历史c206c5da…保留在对应历史报告。R1没有改写任何Stage1–4.0阶段目录。

原Scene117对象/33网格/7材质/29原Action、25关节和24个爆炸控制器保持，1–301帧。FLU +X前/+Y左/+Z上，原点是SDF原点，不声称实机CG。

沿用STAGE4_PRESENTATION、原67展示对象及27共享Mesh/材质实例，仅增3脚架控制Empty、一个几何中心附近的展示姿态根、一盏轮廓灯。现72展示对象，整体189对象/8材质，没有新增Mesh几何。

## R1时间轴与语义

30FPS、1–990帧、33秒。1–120 Hero和轻微组合姿态，120前归零。脚架先同步径向让开盘面再下移并分散；外涵道三片同步。电机和旋翼分别展示，移至+X/-Y同侧；内涵道抬升/侧移/下放避让。四舵面391–480同步0→+20→0→-20→0，使用独立S4四元数Action，原Stage2 Action不动。原旋翼Action子片段通过显式scale40重定时，约30°/s、累计360°，回装矩阵恢复。

四舵面随后同步退出，四舵机再协调退出；展示对应1/cs11、2/cs2、4/cs33、3/cs4。电池沿-Y开口侧出380mm，±Y精确连续扫掠无穿透，±X被侧板阻挡。上框与飞控、后板与GPS平面保持原相对关系，不修正悬空或源装配现状。下框/电调使用避让折线，夹持片最后拆，未添加连杆/螺丝/完整盒体。

811–870完整分解停留2秒，871–960按15组逆序回装，961–990完整机型保持。最终世界矩阵误差约2.45e-16。中性灰科技摄影棚、6柔光/轮廓灯、极弱网格，原材质颜色不改。

## 证据与复核

R1主报告仅`stages/stage-4.0-r1/STAGE_4_0_R1_REPORT.md`。证据包括源/保存后回归、精确电池扫掠、GUI完整播放与关键帧检查、最终重新打开、14,647个约1mm自适应几何样本、正式/副本输入签名及源输入哈希。

原装配已有20对三角边界接触/相交单列保留。新动画未发现新增相交对；不声称制造公差或数学意义全机连续碰撞证明。末轮只修正镜头构图，最终副本与高密筛查副本的几何运动输入签名一致，详见framing_geometry_equivalence.json。548帧A镜头全机、442帧B/C关注部件均完整入画。

原Scene保护基线仍读Audit Stage4.0的source_baseline.json。reverify先验证完整展示及源指纹，再仅在只读进程移除已核对新增层，保持历史全局计数断言，不保存该内存状态。

## 用户交付与窗口

用户不熟悉Blender。本轮最终保持窗口打开，Camera A、Frame1、停止播放、Timeline完整1–990，用户按空格即可播放/暂停。已实际完整播放并检查80/248/412/453/807/930/975帧，最后重新打开确认。GUI截图仅临时检查，已清理。

本轮严格不生成MP4。旧Stage4.0的55秒MP4仅作历史资料，不代表R1。以后各阶段只交付一张本地总览图，本轮`STAGE_4_0_R1_OVERVIEW.png`在R1 evidence/images；全部18画面来自正式工程实际渲染，中文/帧号标注，images继续忽略，不上传Github。

.work/stage-4-r1在正式/GUI/输入校验完成后通过project_io受限清理接口删除，只有一个正式DF4.blend；详见delivery_checks.json。下一步仅等待用户视觉反馈与新授权。
