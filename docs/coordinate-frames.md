# 模型坐标系与机体系转换

DF4 模型坐标本阶段正式定义为 **FLU**：+X前方、+Y左侧、+Z上方，右手系。该语义按用户授权冻结；不是通过本阶段测量获得机头方向。Blender世界与模型坐标当前一致，DF4_ROOT和LINK::base_link世界矩阵均为单位阵，不为适应软件默认视角旋转整机。

原点是SDF模型坐标原点，当前与base_link初始原点重合。没有重心测量依据，不能标注为实机CG。

PX4 BODY_FRD 为+X前、+Y右、+Z下。按任务给定定义，向量转换为：

```text
v_FLU = diag(1,-1,-1) * v_FRD
v_FRD = diag(1,-1,-1) * v_FLU
```

这是绕X轴180°的旋转，行列式+1，正交、逆矩阵等于自身。FRD三个单位基分别映射到FLU +X、-Y、-Z。配置中的两个显式矩阵、逆向和往返均经测试，误差阈值1e-7。此处只转换三维向量分量，不声明PX4与SDF原点的平移相同，也不转换绝对位置；不处理NED地理参考系与完整飞行姿态。

所有模型专属定义在 `configs/DF4.json.coordinate_frames`；根对象保存完整JSON元数据与原点说明。通用 `scripts/coordinate_frames.py` 不包含DF4名称或特定矩阵常量，提供定义读取、旋转矩阵验证、图路径求解、向量转换与只读场景元数据检查。`attach_metadata()`只写属性，不写任何变换；`verify_scene()`只读检查，不以重写元数据掩盖错误。

任务引用的Autopilot转换实现路径为 `src/modules/simulation/gz_plugins/ductedfan/DuctedFanPlugin.cpp` 和 `src/modules/mavlink/mavlink_receiver.cpp`。当前可访问工作区未找到对应Autopilot源码，不能声称已独立核对这些文件的具体实现或提交；本轮矩阵依据是用户给定的冻结定义，并以数学及实际工程测试验证。未修改任何Autopilot仓库。

爆炸位移首先在配置声明的模型FLU中定义，然后用模型根3x3变换转世界向量，再用控制器父级3x3逆变换转局部位移；不叠加原点平移，不混入惯性位姿。方向和距离是人为展示参数，不是机械拆卸行程或物理仿真。
