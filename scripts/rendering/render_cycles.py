"""Cycles 静帧渲染：质量定标与后续正式序列共用。

特性：

* 只读使用正式工程：把 ``output/<MODEL>/<blend_name>`` 复制到 ``<out>/_work/`` 后
  才打开，任何渲染设置都写在副本上，**不保存、不覆盖正式工程**。
* ``--skip-existing`` 支持中断续跑：已有帧先核对尺寸与字节数，全部通过才跳过，
  避免重复渲染，也避免沿用坏帧。
* 逐帧记录耗时、相机、字节数与 SHA256，写入 ``<out>/render_<tag>.json``。

用法::

    blender --background --factory-startup --python-exit-code 1 `
      --python scripts/rendering/render_cycles.py -- `
      --config configs/DF4.json --frames 30,145,200 --tag quality
"""
import argparse
import hashlib
import json
import shutil
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import bpy

WORKSPACE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(WORKSPACE / "scripts"))
sys.dont_write_bytecode = True
import project_io  # noqa: E402

SCENE_NAME = "STAGE4_PRESENTATION"


def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--frames", required=True, help="逗号分隔帧号，或 start-end")
    parser.add_argument("--out", help="输出根目录，默认 <workspace>/../DF4_Render/Stage4_1_QualityTest")
    parser.add_argument("--tag", default="render")
    parser.add_argument("--samples", type=int, default=256)
    parser.add_argument("--threshold", type=float, default=0.01)
    parser.add_argument("--width", type=int, default=1920)
    parser.add_argument("--height", type=int, default=1080)
    parser.add_argument("--percent", type=int, default=100)
    parser.add_argument("--backend", default="OPTIX", choices=("OPTIX", "CUDA", "CPU"))
    parser.add_argument("--skip-existing", action="store_true")
    parser.add_argument("--frame-prefix", default="DF4_F")
    return parser.parse_args(argv)


def expand(frames):
    result = []
    for chunk in frames.split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        if "-" in chunk:
            start, end = chunk.split("-", 1)
            result.extend(range(int(start), int(end) + 1))
        else:
            result.append(int(chunk))
    return sorted(dict.fromkeys(result))


def enable_gpu(backend):
    if backend == "CPU":
        return []
    prefs = bpy.context.preferences.addons["cycles"].preferences
    prefs.compute_device_type = backend
    prefs.get_devices()
    used = []
    for device in prefs.devices:
        device.use = device.type == backend
        if device.use:
            used.append({"name": device.name, "type": device.type})
    if not used:
        raise RuntimeError(f"{backend} 没有可用设备；确认驱动后再回退 CPU")
    return used


def configure(scene, args):
    scene.render.engine = "CYCLES"
    scene.cycles.device = "GPU" if args.backend != "CPU" else "CPU"
    scene.cycles.samples = args.samples
    scene.cycles.use_adaptive_sampling = True
    scene.cycles.adaptive_threshold = args.threshold
    scene.cycles.use_denoising = True
    scene.cycles.denoiser = "OPENIMAGEDENOISE"
    scene.cycles.denoising_input_passes = "RGB_ALBEDO_NORMAL"
    scene.cycles.denoising_prefilter = "ACCURATE"
    scene.cycles.max_bounces = 12
    scene.render.resolution_x = args.width
    scene.render.resolution_y = args.height
    scene.render.resolution_percentage = args.percent
    scene.render.film_transparent = False
    scene.render.use_motion_blur = False
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"
    scene.render.image_settings.color_depth = "8"
    scene.render.image_settings.compression = 15


def existing_ok(path, width, height):
    """已有帧是否可以直接沿用：能被 Blender 读回且尺寸正确。"""
    if not path.is_file() or path.stat().st_size == 0:
        return False
    try:
        image = bpy.data.images.load(str(path), check_existing=False)
        try:
            return tuple(image.size) == (width, height)
        finally:
            bpy.data.images.remove(image)
    except Exception:  # noqa: BLE001
        return False


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main():
    args = parse_args()
    config = json.loads(project_io.resolve(args.config).read_text(encoding="utf8"))
    project = project_io.project(config)
    if not project.is_file():
        raise FileNotFoundError(f"正式工程不存在：{project}")

    out = Path(args.out) if args.out else project_io.resolve("../DF4_Render/Stage4_1_QualityTest")
    frames_dir = out / "frames"
    frames_dir.mkdir(parents=True, exist_ok=True)
    work = out / "_work"
    work.mkdir(parents=True, exist_ok=True)

    copy = work / "render_copy.blend"
    shutil.copy2(project, copy)
    bpy.ops.wm.open_mainfile(filepath=str(copy))
    scene = bpy.data.scenes.get(SCENE_NAME)
    if scene is None:
        raise RuntimeError(f"缺少场景 {SCENE_NAME}")

    used = enable_gpu(args.backend)
    configure(scene, args)

    frames = expand(args.frames)
    record = {
        "started_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "blender": bpy.app.version_string,
        "scene": scene.name,
        "project": str(project.relative_to(project_io.WORKSPACE)).replace("\\", "/"),
        "project_sha256": sha256(project),
        "backend": args.backend,
        "devices": used,
        "samples": scene.cycles.samples,
        "adaptive_threshold": scene.cycles.adaptive_threshold,
        "denoiser": scene.cycles.denoiser,
        "resolution": [scene.render.resolution_x, scene.render.resolution_y, scene.render.resolution_percentage],
        "frames": [],
        "skipped": [],
    }

    total = 0.0
    rendered = 0
    for number in frames:
        target = frames_dir / f"{args.frame_prefix}{number:04d}.png"
        if args.skip_existing and existing_ok(target, args.width, args.height):
            record["skipped"].append({"frame": number, "path": target.name})
            print(f"FRAME_SKIP {number}", flush=True)
            continue
        started = time.perf_counter()
        scene.frame_set(number)
        camera = scene.camera.name if scene.camera else None
        scene.render.filepath = str(target)
        bpy.ops.render.render(write_still=True, scene=scene.name)
        elapsed = time.perf_counter() - started
        total += elapsed
        rendered += 1
        record["frames"].append({
            "frame": number,
            "seconds": round(elapsed, 2),
            "png_bytes": target.stat().st_size if target.exists() else 0,
            "camera": camera,
            "sha256": sha256(target) if target.exists() else None,
        })
        print(f"FRAME_DONE {number} {elapsed:.2f}s {camera}", flush=True)

    record["finished_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    record["rendered_count"] = rendered
    record["total_seconds"] = round(total, 2)
    record["mean_seconds"] = round(total / rendered, 2) if rendered else None
    (out / f"render_{args.tag}.json").write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf8")
    print("RENDER_SET_DONE", json.dumps({"rendered": rendered, "skipped": len(record["skipped"]),
                                         "mean_s": record["mean_seconds"]}, ensure_ascii=False))


main()
