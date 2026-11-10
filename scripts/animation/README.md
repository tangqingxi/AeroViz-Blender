# 机械运动与爆炸位移模块

- `kinematics.py`：Stage2，读取已有JOINT轴与限位，保留q0并生成独立Quaternion Action，严格验证1–121帧。已有爆炸层时禁止重建机械Action。
- `exploded_view.py`：Stage3，在配置的原LINK→JOINT间插入独立偏移Empty，只给其Location写关键帧；原机械Action不修改。支持自身控制器复用和分层分支位移叠加。
- `gui_verify.py`：Stage2原生窗口验收。
- `gui_verify_exploded.py`：Stage3实际播放与截图，最后按照用户要求退出Blender，不保存GUI状态。

模型名称、关节、子树、时间轴、向量与距离均来自配置。坐标模块位于上级 `coordinate_frames.py`，模型元数据不写在机械旋转层。原点不推定为CG；爆炸距离不是物理运动数据。

测试先在 `.work/` 字节副本运行；所有阶段使用唯一当前工程，保存统一经过project_io；报告和证据在独立Audit仓库。Stage4相机/灯光编排、最终视频尚未授权。
