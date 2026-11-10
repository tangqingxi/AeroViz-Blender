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
import stat
import tempfile
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


def _is_reparse(path):
    """同时识别符号链接、Windows 目录联接及其他重解析点。"""
    try:
        info = path.lstat()
    except FileNotFoundError:
        return False
    return stat.S_ISLNK(info.st_mode) or bool(getattr(info, "st_file_attributes", 0) & 0x400)


def _overlaps(a, b):
    return a.is_relative_to(b) or b.is_relative_to(a)


def validate_work_dir(config):
    """只做判断、不删除；配置与路径树均安全时才返回规范化目录。"""
    raw = Path(config.get("work_dir", ".work"))
    if ".." in raw.parts:
        raise ValueError(f"临时路径禁止父目录跳转：{raw}")
    lexical = raw if raw.is_absolute() else WORKSPACE / raw
    lexical = Path(os.path.abspath(lexical))
    allowed = WORKSPACE / ".work"
    if not lexical.is_relative_to(allowed):
        raise ValueError(f"临时目录只允许位于工作区 .work 内：{lexical}")
    # 先检查路径链，再解析真实路径，防止解析掩盖曾经过的联接。
    for candidate in (lexical, *lexical.parents):
        if _is_reparse(candidate):
            raise ValueError(f"临时目录路径包含符号链接或目录联接：{candidate}")
        if candidate == WORKSPACE:
            break
    path = lexical.resolve()
    if not path.is_relative_to(allowed.resolve()):
        raise ValueError(f"临时目录解析后越界：{path}")
    protected = [WORKSPACE / "output", output_dir(config), input_root(config), audit_root(config)]
    if path in (WORKSPACE, WORKSPACE.parent) or any(_overlaps(path, item.resolve()) for item in protected):
        raise ValueError(f"临时目录与受保护路径存在包含关系：{path}")
    # 删除前完整扫描树；不跟随任何重解析点，遇到一个即拒绝整次清理。
    pending = [path] if path.exists() else []
    while pending:
        current = pending.pop()
        if not current.is_dir():
            raise ValueError(f"临时路径不是目录：{current}")
        with os.scandir(current) as entries:
            for entry in entries:
                child = Path(entry.path)
                if _is_reparse(child):
                    raise ValueError(f"临时树包含符号链接或目录联接：{child}")
                if entry.is_dir(follow_symlinks=False):
                    pending.append(child)
    return path


def work_dir(config):
    return validate_work_dir(config)


def safe_reset_work_dir(config):
    """清理仅限经过完整安全校验的 .work 子树。"""
    path = validate_work_dir(config)
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def clear_work_dir(config):
    """结束时也重新校验，禁止复用任意路径递归删除接口。"""
    path = validate_work_dir(config)
    if path.exists():
        shutil.rmtree(path)


def ensure_parent(path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _write_copy(path):
    """Blender 5.0.1 的副本保存不会改变当前会话的工程路径。"""
    import bpy
    result = bpy.ops.wm.save_as_mainfile(filepath=str(path), copy=True)
    if "FINISHED" not in result:
        raise RuntimeError(f"Blender 未完成副本保存：{result}")


def save_project(config, *, allow_rebind=False):
    """同目录副本保存后原子替换；原有会话保持绑定，首次构建则重开绑定。"""
    import bpy

    target = project(config).resolve()
    if not target.is_relative_to(WORKSPACE) or target.suffix.lower() != ".blend":
        raise ValueError(f"工程必须位于工作区且为 .blend：{target}")
    if any(_overlaps(target, root) for root in (input_root(config), audit_root(config))):
        raise ValueError(f"工程路径涉及只读输入或 Audit：{target}")
    current = Path(bpy.data.filepath).resolve() if bpy.data.filepath else None
    if current != target and target.exists() and not allow_rebind:
        raise RuntimeError(f"当前会话未打开目标工程，拒绝覆盖：{target}")
    ensure_parent(target)
    # 临时文件与目标同目录，避免跨文件系统替换；独占命名避免碰到他人的残留。
    fd, name = tempfile.mkstemp(prefix=target.stem+".", suffix=".partial.blend", dir=target.parent)
    os.close(fd)
    temporary = Path(name)
    bpy.context.preferences.filepaths.save_version = 0
    phase = "临时文件保存"
    try:
        _write_copy(temporary)
        if not temporary.is_file() or temporary.stat().st_size == 0:
            raise RuntimeError(f"临时工程不存在或为空：{temporary.name}")
        if (Path(bpy.data.filepath).resolve() if bpy.data.filepath else None) != current:
            raise RuntimeError("副本保存意外改变当前工程路径，拒绝替换")
        phase = "原子替换"
        os.replace(temporary, target)
    except Exception as error:
        raise RuntimeError(f"{phase}失败，原目标未改动：{target}；{error}") from error
    finally:
        if temporary.exists():
            temporary.unlink()
    if current != target:
        # 仅首次构建或入口明确授权重建时需要绑定；使用真实重开而非修改字符串。
        result = bpy.ops.wm.open_mainfile(filepath=str(target))
        if "FINISHED" not in result:
            raise RuntimeError(f"保存已落盘，但重新绑定工程失败：{target}")
    if Path(bpy.data.filepath).resolve() != target:
        raise RuntimeError(f"保存已落盘，但当前工程路径校验失败：{bpy.data.filepath}")
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
