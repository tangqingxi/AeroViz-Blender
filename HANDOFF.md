# Agent Handoff — Stage 3 坐标与爆炸视图完成

- Generated at: 2026-11-10T14:55:48Z
- DEV: <https://github.com/tangqingxi/AeroViz-Blender>，main，`6b2480bc6683de6a2d94fb23b20683c04f8bc17d`（已推送）。
- AUDIT: <https://github.com/tangqingxi/AeroViz-Blender-Audit>，main。当前Audit提交SHA见交付消息，不在本文件内嵌自身SHA。
- 两仓库保持Public；不上传完整.blend/STL/SDF，不force push、不创建Tag。

**Stage 3: COMPLETE**

**Stage 4: WAITING FOR AUTHORIZATION**

## 当前唯一工程

| 项目 | 当前值 |
|---|---|
| 路径 | `output/DF4/DF4.blend` |
| SHA256 | `392af12f14a6fbfb27b201d836b86752c90a97afbc024960fc00f03407726824` |
| 对象 / 网格 / 材质 / 分配 | 117 / 33 / 7 / 33 |
| 原对象 | 93全部保留；25个JOINT不重建 |
| 新控制器 | 24个EXPLODE_OFFSET Empty，唯一EXPLODED_RIG归属 |
| 动画对象 | 29：旧5个机械JOINT + 新24个偏移Empty |
| 时间轴 | 30FPS，1–301帧；机械1–121，展开121–181，保持181–241，恢复241–301 |
| GUI | 真实窗口完整播放和六状态截图PASS，按用户后续要求截图后退出，没有遗留窗口 |

用户不熟悉Blender，明确要求打开截图后退出。不要再默认留下Blender窗口；交付以报告和可直接查看截图为主。本轮GUI没有保存工程，正式文件保存于原装配检查帧，完整爆炸状态截图是Frame181。

## 基线与历史说明

- Stage2历史交付哈希：`c206c5daf61c182982101bdbe8bd797fe0ea47e52dd5855989f16c2f84d8873b`，旧报告和证据不改写。
- 本轮实际当前工程：`5e96e2af3f88d7f5bedc8b9041b6404b039c851c8c089517c995b675222b5943`，保存于Frame11；旧.blend1匹配历史交付并保存于Frame1。
- 用户明确接受当前字节作为新基线，不回退。完整语义比较覆盖对象层级、几何/法线/拓扑/材质索引、材质节点连接、关节属性、五个Action全部关键帧/句柄/插值/外推和1–121逐帧矩阵，全部一致，无Stage2实质差异。
- 当前字节已备份到.work/stage-3/rollback，比较确认后按授权删除.blend1；正式更新前再次核对接受哈希。保存后独立进程完整回归PASS，未触发字节恢复。

## 坐标系与新增结构

FLU正式冻结：+X前、+Y左、+Z上，右手系。DF4_ROOT和LINK::base_link保持单位世界矩阵，不旋转整机。原点是SDF模型原点，不能声称为实机CG。

FRD/FLU向量旋转diag(1,-1,-1)，det+1、正交、逆等于自身，三个单位基及往返误差均0。仅转换向量分量，不声明PX4与SDF原点平移相同，不处理NED地理坐标。Autopilot两处C++路径由任务提供，本轮未取得源码副本，不声称完成独立代码级复核。

24个有网格JOINT在插入前均直接以LINK::base_link为父。新增Empty父级为原LINK，初始局部单位变换，JOINT改为其子级并保留局部姿态/父逆矩阵。其余原始父子关系不变，原Collection、相机、灯光、网格、材质不变。

分组：DUCT4、TAIL3、ELECTRONICS2、MOTOR1、AIRFRAME5、SERVOS4、CONTROL_SURFACES4、ROTOR1。向量/距离/理由来自配置和实际包围盒，不是物理拆卸数据。controller2、X-tend、直接电池、参考件、无网格IMU不独立爆炸。

## 验证与证据

- 唯一主报告：`stages/stage-3/STAGE_3_REPORT.md`。
- 坐标、分支清单、控制器、121–301逐帧、装配恢复、Stage2回归和真实截图均在 `stages/stage-3/evidence/`。
- Stage3最大刚体平移矩阵误差2.980232e-8；Frame301对Frame121恢复误差0。
- 五个原Action指纹与内存身份保持；Stage2只检查1–121帧，累计转角4800.000025901°。装配/爆炸位置各5个机械独立测试共10项PASS。
- 181与241保持一致；最终展开AABB无新的正体积包围盒交叠。窗口检查无无法解决的明显穿插；这不是制造干涉验证。
- 真实窗口完整播放约10.125秒、50次观测跨过完整循环；六张状态图和播放图已查看。原生播放等效于空格，无computer-use，无离线渲染冒充截图。GUI随后自动退出。
- 坐标与爆炸模块不硬编码DF4名称/轴/距离/时间；语法、JSON、保存调用扫描和自有控制器复用测试PASS。
- 原93对象受控白名单：只允许24个指定JOINT父级变化和根坐标元数据；其他字段逐项检查。没有删除或弱化历史检查。

## 复验与边界

DEV：`scripts/coordinate_frames.py`、`scripts/animation/exploded_view.py`、`scripts/animation/gui_verify_exploded.py`；测试：`tests/test_coordinate_frames.py`、`tests/test_exploded_view.py`。规范见docs/coordinate-frames、architecture、interfaces。

```powershell
& $B --background --factory-startup --python-exit-code 1 `
  --python tests/reverify_saved_project.py -- --config configs/DF4.json
```

回归默认读取Audit Stage3爆炸基线及Stage2原结构基线。机械build在已有爆炸层时拒绝执行，防止重做旧Action。所有工程保存仍走project_io.save_project；测试失败必须用已核对字节恢复并停止。

本轮成功证据推送后清理.work，保持output/DF4只含DF4.blend且没有.blend1或阶段副本；最终核对两仓库clean和本地/远端HEAD一致。不得上传本地模型工程。

## 未解决问题与下一阶段

本阶段无未通过验收项。限制：未实测CG，未做动力学、气动或制造干涉；NED/完整实飞姿态不在范围；Autopilot源码未独立核对；原未描述电子设备连接与上游模型分发许可限制保持旧报告说明。爆炸向量只用于展示。

Stage4尚未授权，不做相机/灯光编排、最终视频或MP4。用户授权后再继续。不得重跑Stage1/1.5、重做Stage2Action或以重新导入掩盖结构问题。
