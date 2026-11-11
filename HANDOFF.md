# Agent Handoff — Stage 4.0-R3 就绪，待用户视觉验收

DEV <https://github.com/tangqingxi/AeroViz-Blender> main `e38ecc3f646eaccdd16c13cf7cc6593fce02a870`，已推送。AUDIT <https://github.com/tangqingxi/AeroViz-Blender-Audit>，当前提交见Git HEAD。两仓库Public，不force push、不建Tag，不上传Blend/STL/SDF/视频/序列。

**STAGE 4.0-R3: READY FOR USER VISUAL ACCEPTANCE**，用户效果验收PENDING。停止等待，不进入最终高质量渲染或Premiere。

## 当前工程

唯一正式工程`<DEV>/output/DF4/DF4.blend`，SHA256 `cfafc7c7245654409a378a7c16267251a3307863dfcfb6c288ac53c1674295a0`。实际R2基线`766faf3114d05f2b3f0193ae8cc0ecd0aeb0e08f476afcc686e34d59be8af197`先完整回归/字节备份再在临时副本修改，未回退R1。原Scene117对象/33网格/7材质/29Action、五机械关节、24爆炸控制与FLU保持，历史断言源码不变；R2展示73对象、27共享实例和全局190对象保留，不改父级或几何。

## R3时间与镜头

30秒、30FPS、1–900帧，10章节，相机字母切换4次。删除脚架与舵机特写，C仅涵道201–230和完整动力231–305。原开场1–90相机、脚架1–145运动逐帧误差0，摄影棚/主灯签名保留，特写6W补光按新时段触发。B偏转近景336–425、退出全景426–505各自固定。

四舵面336–425同步±20°回零后426–465同步退出，471–500四舵机退出。POWER仍共同平移，Rotor局部原Action慢转保持。电池-Y380mm与所有模块的空间路径向量保留，只压缩时间；连续扫掠和43个进出帧无穿透。691–750完整分解停留2秒，751–870按14组逆序回装4秒，四舵面同步返回，871–900完整机型保持1秒。恢复误差2.45e-16。

## 证据与用户窗口

唯一主报告`stages/stage-4/STAGE_4_0_R3_REPORT.md`，机器证据`stages/stage-4/evidence/r3/`，新清单`stages/stage-4/evidence-manifest-r3.json`。R1/R2报告和证据字节不改写。完整保存后回归、R2验证兼容、源输入34哈希、同步/动力/电池/构图与恢复、13,981自适应实际网格子帧和真实GUI均PASS。原20对源接触/相交保留，不宣称制造级全机CCD。

本轮只交付一张`stages/stage-4/evidence/STAGE_4_0_R3_OVERVIEW.png`，16个正式工程实际渲染画面。无新MP4/分散PNG，.work/stage-4-r3通过project_io安全清理。Blender5.0.1实际完整播放和精确关键帧检查后重新打开，保持STAGE4_PRESENTATION、Camera A、第1帧、停止播放、Timeline完整1–900。用户直接按空格检查，无需修改参数；说明在DEV docs/stage4-acceptance.md。
