"""路径解析与工程安全保存：所有阶段共用一个当前工程。

约定（唯一权威定义，其他模块不得自行拼接路径）：

* 当前工程            ``output/<MODEL>/<blend_name>``，DF4 为 ``output/DF4/DF4.blend``
* 模型输入（只读）    ``config.input_root``，可用 ``config.input_root_env`` 指定的
                      环境变量整体覆盖，便于换机器而不改配置
* 审计证据            ``<audit_root>/stages/<stage>/evidence``，直接写入审计仓库，
                      本地 ``output/`` 不再持久保存 preview 与 reports
* 临时目录            ``config.work_dir``（默认 ``.work``），每次运行前清空，
                      验收结束后删除

保存一律走 :func:`save_project`：先写临时文件，确认落盘成功后再原子替换当前
工程，因此保存中途失败不会破坏已有的 ``DF4.blend``。
"""
import os
import shutil
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[1]


def resolve(value):
    """相对路径按仓库根解析；绝对路径原样使用。"""
    path = Path(value)
    return (path if path.is_absolute() else WORKSPACE / path).resolve()


def input_root(config):
    """模型输入目录。环境变量存在时优先，保持配置可移植。"""
    env = config.get("input_root_env")
    override = os.environ.get(env, "").strip() if env else ""
    path = resolve(override or config["input_root"])
    if not path.is_dir():
        raise FileNotFoundError(f"模型输入目录不存在：{path}")
    return path


def audit_root(config):
    """审计仓库根目录。环境变量 AEROVIZ_AUDIT_ROOT 可覆盖。"""
    override = os.environ.get("AEROVIZ_AUDIT_ROOT", "").strip()
    value = override or config.get("audit_root")
    if not value:
        raise ValueError("请在配置中提供 audit_root，或设置 AEROVIZ_AUDIT_ROOT")
    return resolve(value)


def output_dir(config):
    return resolve(config["output_dir"])


def project(config):
    """当前唯一工程文件。"""
    return output_dir(config) / config["blend_name"]


def evidence_dir(config, stage):
    """阶段证据目录（审计仓库内）。"""
    return audit_root(config) / "stages" / stage / "evidence"


def reports_dir(config):
    """审计仓库中的清单目录，用于放跨阶段的核验记录。"""
    return audit_root(config) / "manifests"


def work_dir(config):
    """本地临时目录，运行结束即清理。"""
    return resolve(config.get("work_dir", ".work"))


def reset_dir(path):
    """清空并重建目录，返回该目录。"""
    path = Path(path)
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def clear_dir(path):
    """删除临时目录；它不应留在本地。"""
    path = Path(path)
    if path.exists():
        shutil.rmtree(path)


def ensure_parent(path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def save_project(config):
    """把当前 Blender 会话保存为当前工程，失败时不动原文件。"""
    import bpy

    target = project(config)
    ensure_parent(target)
    temporary = target.with_name(target.stem + ".partial" + target.suffix)
    if temporary.exists():
        temporary.unlink()
    # 关闭自动备份，避免在 output/ 下产生 .blend1。
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(temporary))
    if not temporary.is_file() or temporary.stat().st_size == 0:
        raise RuntimeError(f"临时工程写入失败，原工程未改动：{temporary}")
    os.replace(temporary, target)
    if not target.is_file() or target.stat().st_size == 0:
        raise RuntimeError(f"工程替换后校验失败：{target}")
    return target


def publish(files, destination):
    """把临时目录里选定的文件/通配符复制到证据目录，返回实际复制的文件。"""
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    copied = []
    for item in files:
        item = Path(item)
        if any(ch in item.name for ch in "*?"):
            matches = sorted(item.parent.glob(item.name))
        else:
            matches = [item] if item.is_file() else []
        for match in matches:
            shutil.copy2(match, destination / match.name)
            copied.append(destination / match.name)
    return copied
