# Stage 4 展示层接口与修订记录

当前R2接口见文末；下列初始实现记录保留为历史。展示原型效果等待用户人工验收。未进入4.1精修、4.2高质量渲染或4.3剪辑交接。

## 单工程、两个Scene

`output/DF4/DF4.blend` 仍是唯一正式工程。原 `Scene` 的117个对象和1–301帧完整保留。新 `STAGE4_PRESENTATION` 为1–1650帧、30FPS展示时间轴，默认相机视角打开。新增67个对象均带 `aeroviz_stage4` 标识，集中在展示Collection的六个子Collection中。27个网格实例共享原33个网格中27个可见件的Mesh及原材质，不复制或重新导入STL；其余新增对象为23个模块Empty、5个NLA轴心Empty、3相机、3目标Empty、5灯和1地面。

展示模块只做平移。五个展示轴心复用原五个Action的原Action Slot，以独立NLA Strip改变播放时间，不复制、修改或重新制作原Action。旋翼开场为30°/s视觉演示；舵面保留±10°原运动片段。源场景的24个爆炸控制器及其Action不参与展示场景求值。

`configs/DF4.json` 的 `presentation` 块定义Scene、模块对象、起止帧、FLU米制位移、NLA片段、细节镜头目标、舵机/舵面展示对应、镜头清单、静帧和配色。展示位移不是实际维修行程。三脚架共用一个模块；飞控跟随上框、GPS固定平面跟随后侧板，仅继承原相对矩阵，不修正Gazebo现状。

## 入口与保护

- `scripts/presentation.py`：捕获源基线、建立展示Scene、验证共享几何/材质、逐帧顺序与主镜头包围盒留白。构建若遇已有展示Scene立即拒绝，不叠加重复实例。
- `tests/test_presentation.py`：prepare/verify/apply；先在`.work/stage-4.0/`副本测试，正式apply须匹配源哈希、字节备份和已测试配置。原子保存后独立进程复验，失败恢复字节备份。
- `tests/reverify_saved_project.py`：先验证新增层和全部源指纹，再仅在只读验证进程中移除已核对的新增层，原Stage1–3的全局计数断言保持原强度；不会保存该内存状态。
- `scripts/rendering/stage4_preview.py`：只读渲染benchmark/stills/video。stills模式把分散帧写到`.work/stage-4.0/stills/`，随后调用本机Python/Pillow排版总览图并清理输入帧；可用`--image-python`指定该Python。低清序列只写`.work/stage-4.0/frames/`。
- `scripts/rendering/encode_stage4.py --ffmpeg <本地可执行文件>`：以15FPS编码55秒MP4，保留时间长度。默认本地NVENC，也支持`--encoder libx264`；不下载依赖。
- `scripts/rendering/gui_stage4.py`：真实窗口相机/Timeline检查与完整原生播放；`--save-layout`显式保存布局，`--leave-open`按本轮用户补充要求停留。未提供leave-open时检查后退出。

`presentation.isolate_source_for_legacy_tests()`只允许在只读验证进程使用。撤销展示层时也须先通过相同的源指纹与新增所有权检查；正式保存属于独立任务，不在本轮自动执行。

背景四个色号按sRGB解码为线性值，原SDF材质仍保留原线性解释。地面弱混合网格、距离淡出、低金属度与高粗糙度只属于新展示地面材质，不覆盖原机体材质。AgX、照明与曝光会影响最终像素，色号不等同于每个像素输出值。

## 当前原型的限度

960×540、15FPS、Eevee 8采样用于节奏和拆解验收；静帧为32采样。只有主相机要求全机不裁切，细节与俯视镜头允许裁出画面之外的已拆部件。没有新增连杆、螺丝、HUD或标注几何。没有进行实际碰撞/拆装可行性验证；舵机对应按现有几何方位组织，不宣称完成实机传动测定。

用户验收步骤见 [Stage 4.0 验收说明](stage4-acceptance.md)。镜头清单、拆解方向、截图、视频和回归数据统一在Audit的Stage4.0主报告。

窗口边界操作的上下文限制与相机标记的显示行为按Blender 5.0.1源码核对：[screen_ops.cc](https://github.com/blender/blender/blob/v5.0.1/source/blender/editors/screen/screen_ops.cc)、[anim_markers.cc](https://github.com/blender/blender/blob/v5.0.1/source/blender/editors/animation/anim_markers.cc)。Timeline增加17个可读阶段标记；17个原相机切换标记仍各自绑定A/B/C，额外阶段标记不改变镜头切换。

后续各阶段只交付一张本地总览图。`scripts/rendering/contact_sheet.py`负责确定性拼接和中文阶段/帧号标签；原渲染内容不经生成式改写。Audit的images目录在Git忽略范围内，公开证据清单只记录图片元数据，不包含图片字节。


## 当前55秒镜头的导演描述

影片以两秒低机位侧前方推进开场，灯光由弱到强扫过机体，让白色涵道和脚架轮廓逐渐显现，旋翼缓慢转动，建立明星登场的仪式感。随后镜头拉开，三只脚架作为一个整体缓慢下沉，停稳后切到单只脚架近景，交代其支撑形态。回到侧前方主镜头，三片外涵道伴随小幅环绕逐片退开，每片到位后稍作停留，让内部结构依次显露。动力段切入斜侧特写，先展示电机再让电机退出，随后展示并拆出旋翼，最后移开内涵道。控制段采用稳定的斜俯视：四个舵面先依次偏转、回零，再逐个退出；穿插一组舵机与舵面的近景，随后四个舵机沿对应方位依次分离。中后段回到主三分之四视角，电池先向上退出，上框连同飞控移开，两块侧板分别退开，GPS固定平面保持原相对位置随侧板移动，最后下框退出；电调获得一次跟随特写后离场，两片脚架夹持件最后拆出。结尾以约四秒的全景揭示收束：所有部件保持分层布局，镜头缓慢升高、后退并小幅转向，最后停稳，留出整体观察和后期剪辑的余量。全段以“揭示—分离—停留”为节拍，用稳定主镜头交代关系，用短特写强调细节。


## R1定向修订接口

当前配置 `presentation.revision=4.0-R1`，复用原展示Scene、67个既有展示对象与27个共享Mesh实例。`presentation_r1.apply()`只更新展示Action、NLA、父级、灯光、背景和镜头；原Scene不变。姿态根在可见几何包围盒中心旋转，不标注实机CG。四舵面使用独立S4四元数Action，按原SDF轴向逐帧采样±20°，不改原Stage2 Action。旋翼NLA显式设置scale=40，原Action取1–10帧重定时到1–361帧，总360°，约30°/s，末态矩阵恢复。

模块 `waypoints` / `return_waypoints` 记录退出和回装的安全折线路径。Location逐整数帧采样smoothstep，分量LINEAR插值使子帧也落在分段路径上。脚架先同步径向让开盘面再下移；电机和旋翼先保持安装高度侧向脱离，再移向+X同侧区域；内涵道先+Z抬升70mm、侧移-Y 600mm，再轴向下放；下框先抬升15mm再侧移；电调先抬升40mm再侧移。逆序回装采用相反的折线路径。

`geometry_checks.py`对长方体电池执行±X/±Y连续扫掠体与实际三角形的分离轴检查；±Y清楚，±X被侧板阻挡，选-Y 380mm。另逐帧检查电池进出。`mesh_intersections.py`按实际网格角点位移约1mm自适应细分，记录世界空间BVH新增相交对，源装配20个既有接触/相交对单独保留，不作源几何修正；该检查不是制造公差或严格连续全机碰撞证明。

`tests/test_presentation_r1.py`提供prepare/verify/apply。正式apply必须匹配原文件SHA、字节备份、已通过的副本配置以及几何筛查对应的副本SHA/配置SHA；保存后新进程完整回归，失败恢复旧字节。R1的原Scene基线继续读取Audit Stage4.0 source_baseline.json，不改历史报告。

当前展示990帧、21镜头；811–870为分解停留，871–960逐组回装，961–990完整机型停留。`stage4_preview.py`只允许stills/benchmark，video与编码入口均对R1拒绝执行。总览图按配置 `output_stage/work_dir/overview_name/still_labels` 写入新R1证据目录，GUI截图只在.work内作检查，最终清理。

末轮镜头构图修正只刷新相机及目标Action，B镜头按关注部件的整段运动包围盒固定构图；全部442帧B/C关注部件和548帧主镜头均有边距约束。`mesh_intersections.geometry_signature()`锁定网格、父级、几何Action/NLA，与相机/灯光分离；构图副本和原14,647样本筛查副本的几何运动输入相同，正式`framing-apply`再次核对该签名并执行独立进程回归。


## R2定向修订接口

`presentation_r2.py`复用现有R1展示Scene与72对象，只新增POWER平移Empty。原MOTOR/ROTOR模块作为其静态子层，Rotor原局部关节/NLA留在下层；验证时把允许的局部自转因子分离，检查完整安装矩阵、相对位置和旋转轴。原117对象/33网格/7材质/29 Action保持，27展示实例仍共享原Mesh/材质。

禁用AIRCRAFT_POSE_ROOT动作，根保持中立；1–90帧全部非旋翼网格世界矩阵不动。主相机按圆弧推进约20°并升高，14章中只有4类C特写；飞控/电调由主镜头展示。地面黑色/深灰网格输入按sRGB解码，宽度次1.4mm/主3.2mm，屏幕像素宽度随透视变化，不能误称全画面恒定像素。

同步舵面20°角度沿用正确的独立展示动作，不改Stage2 Action。舵面随后依次退出；舵机协调退出。电池先读取R1 Blend实际曲线和世界包围盒轨迹，证实已为-Y 380mm；R2只重定时，不把更早Stage4.0的+Z记录误作当前R1。重新执行完整侧向扫掠和中间帧验证。

`tests/test_presentation_r2.py`提供prepare/verify/apply，源基线仍读取Audit Stage4.0的source_baseline.json；正式apply匹配R1实际SHA/备份、已通过配置、几何筛查对应副本SHA，保存后新进程回归失败恢复原字节。所有分散渲染、GUI检查和临时副本只在.work/stage-4-r2。

R2输出路径按本轮明确指定为Audit `stages/stage-4/evidence/STAGE_4_0_R2_OVERVIEW.png`；只保留这一张总览图。此前images目录内分散图片仍忽略；R2允许提交一张最终总览图，其余临时PNG不入库。渲染和编码入口在R2配置下拒绝视频。

## R3定向修订接口

`presentation_r3.py`在R2正式Scene上修改展示Action和相机，不增删展示对象，不改任何原网格、零件材质、父级或机械Action。复用R1缓动/路径函数及R2完整机械验证；R2验证器仅增加按修订选择的帧范围、同步组和两特写约束，原Stage1–3历史断言保持。另运行R2旧配置兼容回归。

保留开场1–90帧相机采样和脚架1–145帧轨迹，逐帧比较误差。摄影棚地面/世界节点、五个主灯与颜色管理通过签名保护；第六盏特写跟随补光沿用6W和原局部结构，仅按现存两段C镜头重新触发。Camera B偏转近景与退出全景各自固定，不在运动中环绕，不切单件。

900帧、30秒、10章节；四舵面336–425同步±20°，426–465同步退出，466–470保持；四舵机471–500退出，501–505保持。所有位移端点和避让路径向量继续匹配R2配置，只重定时。691–750分解保持，751–870逆序14组回装，同组舵面、舵机、涵道和脚架同步返回，871–900完整机型保持。

`tests/test_presentation_r3.py`延续prepare/verify/apply，正式更新核对R2实际SHA、字节备份、副本审批和几何筛查SHA，保存后独立进程完整回归失败则恢复旧字节。全片实际三角BVH自适应子帧检查重新运行；电池另检查连续-Y扫掠与实际进出帧，不能仅根据标签认定路径正确。

本轮唯一总览图为Audit `stages/stage-4/evidence/STAGE_4_0_R3_OVERVIEW.png`。机器记录通过`record_subdir=r3`单独存入evidence/r3，避免覆盖R2。主报告及R3证据清单另名，R1/R2历史字节保持。分散渲染/GUI截图/副本只在.work/stage-4-r3，最终受限清理；视频与编码入口对R3拒绝执行。
