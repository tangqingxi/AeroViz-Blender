# Stage 4.0 展示层接口

当前仅为镜头与渐进式拆解原型，效果等待用户人工验收。未进入4.1精修、4.2高质量渲染或4.3剪辑交接。

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
