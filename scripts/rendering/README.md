# `scripts/rendering/` —— Stage 4 展示验收

当前Stage4.0-R3只渲染一张总览图，不制作MP4。视频/编码入口在R1/R2/R3配置下直接拒绝执行；编码模块保留供历史Stage4.0使用。

`stage4_preview.py`只读当前工程的展示Scene，输出一张本地总览图或临时低清序列；`encode_stage4.py`调用本地FFmpeg生成MP4；`gui_stage4.py`检查真实窗口相机、Timeline与完整播放，并可按用户指令保存布局、停留或退出。

展示Scene由上一级的`presentation.py`建立。原Scene、原几何/材质、Stage2五个Action和Stage3控制器保持原样。使用共享Mesh实例和NLA片段复用，不重新导入模型。

参数、流程与限制见 [展示层接口](../../docs/stage4-presentation.md)。当前R3视觉验收素材只有实际渲染合成的总览图；GUI截图只证明布局和播放，不作为最终渲染。

现有四个`VIEW::*`正交相机与四个`MATERIAL_LIGHT::*`灯仍属于源Scene；当前展示Scene使用独立的相机A/B/C与六灯。仅交付R3原型，不进行最终高质量渲染或剪辑交接。

图片只有一张总览图。stills结束后自动用本机Python/Pillow合图并清理临时帧；`--image-python`可覆盖Python路径。R3图片与报告存入Audit，机器证据使用record_subdir独立归档，避免覆盖R2；此前images目录仍忽略，其余临时图片不上传GitHub。

## Cycles 静帧渲染（Stage 4.1）

`render_cycles.py` 是写入正式画质的静帧入口：只读正式工程（先复制到 `<out>/_work/` 再打开），
固定 Cycles + GPU/OptiX + 256 samples + Adaptive 0.01 + OpenImageDenoise(Albedo+Normal) + AgX；
`--skip-existing` 先核对已有帧尺寸再跳过，供正式序列中断续跑。它不保存工程、不改动镜头与动画，
输出到 Git 之外的目录。参数、8 帧实测与画质结论见审计仓库
`stages/stage-4/STAGE_4_1_CYCLES_REPORT.md`。正式 900 帧序列与 MP4 编码尚未授权。
