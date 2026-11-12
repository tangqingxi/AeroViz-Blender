# Stage 4.2 — DF4 正式全片渲染（Cycles Final Render）

**STAGE 4.2: FINAL RENDER COMPLETE**

| 项目 | 值 |
|---|---|
| 阶段 | Stage 4.2（正式全片渲染） |
| 上游基线 | Stage 4.0-R3（镜头/动画，已验收）+ Stage 4.1（Cycles 画质定标，已验收） |
| 执行日期 | 2026-11-11 |
| 正式工程 | `<DEV>/output/DF4/DF4.blend` |
| 工程 SHA256（渲染前 / 渲染后） | `cfafc7c7245654409a378a7c16267251a3307863dfcfb6c288ac53c1674295a0`（一致） |
| 交付位置 | `<local>/DF4_Render/Stage4_2_Final/`（不在 Git 内） |
| 审计证据 | [`evidence/stage-4.2/`](evidence/stage-4.2/) |
| 证据清单 | [`evidence-manifest-stage-4.2.json`](evidence-manifest-stage-4.2.json) |

## 1. 任务目标

在已验收的 R3 工程上，用 4.1 定标通过的 Cycles 参数渲染完整 900 帧，输出 PNG 母版与一份 1080p30 H.264 成片，同时保证：

- 不改动画、镜头、拆解顺序、背景、材质、灯光；
- 正式工程字节不变；
- 渲染可中断续跑，不重复覆盖已通过的帧；
- 900 张 PNG 与 MP4 只留在本地，Audit 只收报告与少量证据。

## 2. 渲染参数（与 4.1 验收值一致，未改动）

| 项 | 值 |
|---|---|
| Engine / Device | Cycles / GPU **OptiX** |
| Blender | 5.0.1（build `a3db93c5b259`，内置 Python 3.11.13） |
| 分辨率 / 帧率 | 1920×1080（100%）/ 30 FPS |
| 帧范围 / 总帧数 | 1–900 / 900 |
| Samples | 256 |
| Adaptive Sampling | 开启，Threshold 0.01，最小采样 0 |
| Denoiser | OpenImageDenoise，Albedo + Normal，prefilter ACCURATE |
| Color Management | AgX，Look `AgX - Medium High Contrast`，Exposure −0.1，Gamma 1.0 |
| 输出 | PNG，RGB 8-bit，压缩 15 |
| 背景 / Motion Blur | 不透明 / 关闭 |
| 光线反弹 | `max_bounces = 12` |

## 3. 硬件

| 项目 | 值 |
|---|---|
| GPU | NVIDIA GeForce RTX 5060 Laptop GPU，8,151 MiB，驱动 591.91（Cycles 枚举为 OPTIX 设备，CPU 未参与渲染） |
| CPU | Intel Core i7-14650HX（16 核 / 24 线程） |
| 内存 | 15.6 GB |
| 操作系统 | Windows 11（10.0.26200） |
| 渲染前后 D: 剩余 | 77.2 GB → 75.3 GB（交付占用约 1.53 GB） |

## 4. 过渡帧补检（正式渲染前）

用与正式渲染完全相同的参数单独渲染 3 帧，仅作风险检查，未入 Git：

| 帧 | 内容 | 耗时 | 结果 |
|---|---|---:|---|
| F0426 | 四舵面开始同步退出 | 9.89 s | PASS |
| F0506 | 电池开始侧向退出 | 8.70 s | PASS |
| F0751 | 完整分解转入重新装配 | 8.89 s | PASS |

逐张目视检查：无穿模、无黑屏、无相机切换异常、无丢件、无异常模糊、无可见噪点。检查通过后才开始长跑。

## 5. PNG 母版

| 项目 | 值 |
|---|---|
| 数量 | **900 / 900** |
| 命名 | `DF4_000001.png` … `DF4_000900.png`，连续无缺号 |
| 总体积 | 1,631,175,874 B ≈ **1.52 GiB（1.63 GB）** |
| 平均单帧 | 1,812,418 B（最小 / 最大见 `check_all.json`） |
| 尺寸 | 900 张全部 1920×1080 |
| 完整性 | 0 个 0 字节文件；900 张全部可解码；无缺帧、无重复帧号 |

分段校验（每段渲染完成后立即执行）：

| 段 | 帧范围 | 帧数 | 校验 |
|---|---|---:|---|
| 1 | 1–300 | 300 | PASS |
| 2 | 301–600 | 300 | PASS |
| 3 | 601–900 | 300 | PASS |

## 6. 耗时

| 段 | 帧范围 | 渲染耗时 | 平均 |
|---|---|---:|---:|
| 1 | 1–300 | 3,872.06 s | 12.95 s/帧 |
| 2 | 301–600 | 3,928.61 s | 13.10 s/帧 |
| 3 | 601–900 | 3,328.21 s | 11.09 s/帧 |
| 首帧冒烟 | F0001 | 7.29 s | — |
| **合计** | **1–900** | **11,136.17 s = 3 小时 5 分 36 秒** | **12.37 s/帧** |

单帧耗时区间约 7.3–15.5 s：开场镜头较快，Camera C/B 段落（201–305、336–505）因可见几何更多而偏慢。长跑过程中未观察到持续降频到影响交付的程度，但比 4.1 的 8 帧短测（10.08 s/帧）慢约 23%，与 4.1 报告中"长跑可能低于短测"的提示一致。

## 7. MP4 编码

| 项目 | 值 |
|---|---|
| 工具 | FFmpeg 9.0.2 essentials build（libx264） |
| 命令 | `ffmpeg -framerate 30 -start_number 1 -i PNG_Master/DF4_%06d.png -c:v libx264 -profile:v high -level 4.1 -crf 17 -preset slow -pix_fmt yuv420p -color_primaries bt709 -color_trc bt709 -colorspace bt709 -x264-params colorprim=bt709:transfer=bt709:colormatrix=bt709 -movflags +faststart -an MP4/DF4_Final_1080p30.mp4` |
| 编码耗时 | 8.3 s（约 112 fps 编码速度） |
| 输出 | `MP4/DF4_Final_1080p30.mp4` |
| 大小 | 6,329,553 B（6.04 MB） |
| 时长 / 帧数 | 30.000 s / 900 |
| 编码 / Profile / Level | H.264 / High / 4.1 |
| 码率 | 1,684,810 bit/s |
| 像素格式 | yuv420p |
| 色彩 | BT.709（primaries / transfer / matrix 三个标记均写入，ffprobe 可读出） |
| 帧率 | 30/1 恒定 |
| 音频 | 无音轨 |
| 封装 | MP4，+faststart |

**解码保真抽检**：从 MP4 解码回 PNG 与母版逐像素比较，平均 |RGB| 差为 F0001 1.44/255、F0450 1.28/255、F0900 1.15/255，属于 yuv420p + CRF 17 的正常舍入范围，未见色偏或块状失真。

## 8. 结果目录

```text
DF4_Render/
├── _tools/                        FFmpeg（本地工具，不入库）
├── Stage4_1_QualityTest/          4.1 定标素材（保留）
└── Stage4_2_Final/                本轮交付
    ├── PNG_Master/                900 张 1920×1080 PNG（1.52 GiB）
    ├── MP4/
    │   └── DF4_Final_1080p30.mp4  6.04 MB / 30.000 s
    ├── preview/
    │   ├── cover_F0030.png        1280×720 封面候选
    │   └── contact_sheet.png      9 帧联系表
    ├── MANIFEST.md                交付清单
    ├── check_all.json / check_seg1-3.json
    └── render_seg1-3.json / render_smoke.json
```

## 9. 正式工程保护

- 渲染脚本先把 `DF4.blend` 复制到 `<Stage4_2_Final>/_work/` 再打开，所有渲染设置只作用于副本，脚本内不含保存操作。
- 渲染前 SHA256：`cfafc7c7…295a0`；渲染后复核：**相同**。
- `output/DF4/` 仍然只有 `DF4.blend` 一个文件。
- 未改动 117 个源对象、33 个原始网格、7 个原始材质、29 个 Action、24 个 Stage 3 爆炸控制器、73 个 Stage 4 展示对象、900 帧时间轴、相机与灯光。

## 10. 提交与仓库

| 仓库 | 分支 | HEAD | 说明 |
|---|---|---|---|
| AeroViz-Blender | `main` | `1e04052ace5decd448f7053e582c77e7cd7131b5` | 新增 `--frame-digits` / `--frames-subdir`，供 6 位帧号与 `PNG_Master` 使用 |
| AeroViz-Blender-Audit | `main` | 见本文件所在提交 | 本报告、证据与索引更新 |

两个仓库保持 Public；未 force push、未创建 Tag；900 张 PNG 与 MP4 **未**提交到任何仓库。

## 11. 未解决问题

1. **渲染耗时高于 4.1 预测**：12.37 s/帧 vs 短测 10.08 s/帧（+23%），总耗时 3.1 小时而非 2.5 小时。原因应为长跑热负载与相机 C/B 段几何更多；不影响交付，但后续如需重渲应预留 3.5 小时。
2. **FFmpeg 为本地下载工具**：仓库中无 FFmpeg，系统 PATH 也没有。本轮下载了 gyan.dev 的 9.0.2 essentials build 到 `DF4_Render/_tools/`（109.5 MB，不入库）。团队成员需自备 FFmpeg 才能重复编码。
3. **8-bit PNG 母版**：按 4.1 验收参数输出 8-bit，若后续需要更高调色空间（10-bit 或 EXR），需要重新渲染，本轮未做。
4. **MP4 只有 1.68 Mbps**：画面以大面积平滑灰为主，CRF 17 下体积很小，质量抽检正常；若剪辑侧希望更高码率，可用同一 PNG 序列重编，无需重渲。
5. **Stage 4.1 的测试帧目录仍保留**（`Stage4_1_QualityTest/`，约 14 MB），尚未清理；留给 4.3 一并处理。

## 12. 用户下一步建议

- 先看 `preview/contact_sheet.png` 与 `MP4/DF4_Final_1080p30.mp4`，确认成片可接受。
- 剪辑可直接导入 MP4；若需要更高画质的中转，用 `PNG_Master/` 序列。
- 封面候选：`preview/cover_F0030.png`（完整装配）。
- 下一阶段建议 **Stage 4.3 — 最终交付整理 / 剪辑交接**（目录清理、交付说明、剪映/Premiere 导入建议、封面帧确认），本轮不执行。
