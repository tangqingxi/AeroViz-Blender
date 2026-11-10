"""解析单模型 SDF；不执行 Jinja，不把惯性坐标用于几何放置。"""
from pathlib import Path
import xml.etree.ElementTree as ET
from mathutils import Matrix, Euler, Vector
from adapters.import_stl import UNIT_SCALE

def pose(element, unit=1.0):
    if element is None:
        return Matrix.Identity(4)
    if element.get("degrees") == "true" or element.get("rotation_format", "euler_rpy") != "euler_rpy":
        raise ValueError("暂不支持该旋转格式，请先转换为弧度 RPY")
    numbers = [float(x) for x in (element.text or "0 0 0 0 0 0").split()]
    if len(numbers) != 6:
        raise ValueError("pose 必须为六个数值，不能含未展开模板")
    return Matrix.Translation(Vector(numbers[:3])*unit) @ Euler(numbers[3:], 'XYZ').to_matrix().to_4x4()

def pose_values(values, unit=1.0):
    e = ET.Element("pose")
    e.text = " ".join(map(str, values))
    return pose(e, unit)

def reference(element, default):
    return (element.get("relative_to") or element.get("frame") or default) if element is not None else default

def read(config, input_root):
    unit = UNIT_SCALE[config.get("sdf_unit", "m")]
    root = ET.parse(input_root / config["description"]).getroot()
    models = root.findall("model")
    if len(models) != 1 or models[0].find("model") is not None:
        raise ValueError("目前只支持单模型；嵌套模型需要独立适配器")
    model = models[0]
    nodes = {"__model__": (None, Matrix.Identity(4))}
    links = {}
    for link in model.findall("link"):
        name = link.attrib["name"]
        p = link.find("pose")
        nodes[name] = (reference(p, "__model__"), pose(p, unit))
        links[name] = {"inertial_pose": link.findtext("inertial/pose", "0 0 0 0 0 0")}
    for frame in model.findall("frame"):
        p = frame.find("pose")
        nodes[frame.attrib["name"]] = (reference(p, frame.get("attached_to", "__model__")), pose(p, unit))
    cache = {"__model__": Matrix.Identity(4)}
    def resolve(name, stack=()):
        if name in cache:
            return cache[name]
        if name in stack or name not in nodes:
            raise ValueError(f"坐标系缺失或循环：{name}，路径：{stack}")
        ref, transform = nodes[name]
        cache[name] = resolve(ref, stack+(name,)) @ transform
        return cache[name]
    joints, ignored_joints = [], []
    includes = [{"name": i.findtext("name"), "uri": i.findtext("uri"), "pose": i.findtext("pose")} for i in model.findall("include")]
    for item in includes:
        if item["name"] not in config.get("ignored_includes", {}):
            raise ValueError(f"尚未解析外部 include，请在配置明确处理：{item}")
    for j in model.findall("joint"):
        child, parent = j.findtext("child"), j.findtext("parent")
        if child not in links or (parent not in links and parent != "world"):
            if any(child.startswith(i["name"]+"::") for i in includes):
                ignored_joints.append(j.attrib["name"])
                continue
            raise ValueError(f"关节引用未知 link：{j.attrib}")
        p = j.find("pose")
        nodes[j.attrib["name"]] = (reference(p, child), pose(p, unit))
        xyz = j.find("axis/xyz")
        if xyz is not None and xyz.get("expressed_in"):
            axis_frame = xyz.get("expressed_in")
        else:
            axis_frame = "__model__" if j.findtext("axis/use_parent_model_frame", "0") in ("1", "true") else j.attrib["name"]
        joints.append({"name": j.attrib["name"], "type": j.get("type"), "child": child, "parent": parent,
                       "axis": [float(x) for x in (j.findtext("axis/xyz") or "0 0 1").split()], "axis_frame": axis_frame,
                       "lower": j.findtext("axis/limit/lower"), "upper": j.findtext("axis/limit/upper")})
    for name in links:
        links[name]["matrix"] = resolve(name)
    for j in joints:
        j["matrix"] = resolve(j["name"])
        j["axis_model"] = list(resolve(j["axis_frame"]).to_3x3() @ Vector(j["axis"]))
    parts = []
    for link in model.findall("link"):
        for visual in link.findall("visual"):
            mesh = visual.find("geometry/mesh")
            if mesh is None:
                raise ValueError("此适配器只处理网格 visual，不能静默遗漏其他几何")
            uri = mesh.findtext("uri")
            if uri.startswith("model://"):
                model_id, relative = uri[8:].split("/", 1)
                if model_id not in config.get("uri_roots", {}):
                    raise ValueError(f"没有 URI 映射：{model_id}")
                file = input_root / config["uri_roots"][model_id] / relative
            elif uri.startswith("file://"):
                file = Path(uri[7:])
            else:
                file = input_root / uri
            p = visual.find("pose")
            parts.append({"file": str(file.resolve()), "link": link.attrib["name"], "visual": visual.get("name"),
                          "matrix": resolve(reference(p, link.attrib["name"])) @ pose(p, unit),
                          "scale": [float(x) for x in mesh.findtext("scale", "1 1 1").split()],
                          "reason": "SDF link × visual；保留网格原始坐标，不施加 inertial pose"})
    return {"parts": parts, "links": links, "joints": joints, "includes": includes,
            "ignored_joints": ignored_joints, "model_pose": pose(model.find("pose"), unit)}
