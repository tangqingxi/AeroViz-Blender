"""通用 STL 适配器：只负责几何导入，不推测坐标或居中。"""
from pathlib import Path
import bpy

UNIT_SCALE = {"m": 1.0, "mm": 0.001, "cm": 0.01}

def load_mesh(path, unit):
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(path)
    if unit not in UNIT_SCALE:
        raise ValueError(f"不支持的网格单位：{unit}")
    before = set(bpy.data.objects)
    if hasattr(bpy.ops.wm, "stl_import"):
        bpy.ops.wm.stl_import(filepath=str(path), global_scale=UNIT_SCALE[unit], use_scene_unit=False, forward_axis='Y', up_axis='Z')
    else:
        bpy.ops.import_mesh.stl(filepath=str(path), global_scale=UNIT_SCALE[unit], use_scene_unit=False, axis_forward='Y', axis_up='Z')
    objects = list(set(bpy.data.objects) - before)
    if len(objects) != 1 or objects[0].type != 'MESH':
        raise RuntimeError(f"STL 导入未返回唯一网格：{path}")
    obj = objects[0]
    obj.name = path.stem
    obj["source_file"] = str(path)
    return obj

def read(config, input_root):
    # 无描述文件时必须显式指定每个零件，禁止猜测装配关系。
    parts = []
    for item in config.get("parts", []):
        if "pose" not in item or not item.get("reason"):
            raise ValueError("独立 STL 配置必须给出 pose 和坐标依据 reason")
        parts.append(dict(item, file=str(input_root / item["path"]), link=None, scale=[1, 1, 1]))
    if not parts:
        raise ValueError("独立 STL 适配器没有配置零件")
    return {"parts": parts, "links": {}, "joints": [], "includes": [], "model_pose": [0]*6}
