# `scripts/rendering/` —— Stage 4.0 低清展示原型

`stage4_preview.py`只读当前工程的展示Scene，输出一张本地总览图或临时低清序列；`encode_stage4.py`调用本地FFmpeg生成MP4；`gui_stage4.py`检查真实窗口相机、Timeline与完整播放，并可按用户指令保存布局、停留或退出。

展示Scene由上一级的`presentation.py`建立。原Scene、原几何/材质、Stage2五个Action和Stage3控制器保持原样。使用共享Mesh实例和NLA片段复用，不重新导入模型。

参数、流程与限制见 [展示层接口](../../docs/stage4-presentation.md)。本阶段最终视觉验收素材为干净渲染及MP4，GUI截图只证明布局和播放。

现有四个`VIEW::*`正交相机与四个`MATERIAL_LIGHT::*`灯仍属于源Scene；展示Scene使用独立的相机A/B/C与五灯。仅交付Stage4.0原型，不进行4.1精修、4.2高质量渲染或4.3剪辑交接。

后续图片默认只有一张总览图。stills结束后自动用本机Python/Pillow合图并清理临时帧；`--image-python`可覆盖Python路径。合图只保留本地，不上传GitHub。
