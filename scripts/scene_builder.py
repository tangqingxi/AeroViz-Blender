"""按装配语义创建场景，并用关节空对象保留真实旋转中心。"""
from pathlib import Path
from fnmatch import fnmatchcase
import bpy
from mathutils import Matrix, Vector
from adapters.import_stl import load_mesh, UNIT_SCALE
from adapters.import_sdf import pose_values

def collection(name, parent):
    result = bpy.data.collections.new(name)
    parent.children.link(result)
    return result

def empty(name, col, parent=None, matrix=None):
    obj = bpy.data.objects.new(name, None)
    col.objects.link(obj)
    obj.empty_display_size = 0.012
    obj.parent = parent
    if matrix is not None:
        obj.matrix_world = matrix
    return obj

def attach(obj, parent, world):
    # 显式计算局部矩阵，避免父对象未求值时 matrix_world 赋值造成偏移。
    obj.parent = parent
    obj.matrix_parent_inverse = Matrix.Identity(4)
    obj.matrix_basis = parent.matrix_world.inverted() @ world if parent else world
    bpy.context.view_layer.update()

def build(config, data, input_root):
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    for col in list(bpy.data.collections):
        bpy.data.collections.remove(col)
    scene = bpy.context.scene
    scene.unit_settings.system = 'METRIC'
    scene.unit_settings.scale_length = 1
    root_col = collection(config["model_name"]+"_ROOT", scene.collection)
    groups = {name: collection(name, root_col) for name in config.get("groups", {})}
    groups["UNCLASSIFIED"] = collection("UNCLASSIFIED", root_col)
    reference_col = collection("REFERENCE_ONLY", root_col)
    rig_col = collection("LINKS_AND_JOINTS", root_col)
    root_matrix = data["model_pose"] if config.get("apply_model_pose") else Matrix.Identity(4)
    root_obj = empty(config["model_name"]+"_ROOT", rig_col, matrix=root_matrix)
    links = {name: empty("LINK::"+name, rig_col) for name in data["links"]}
    for name, obj in links.items():
        attach(obj, root_obj, root_matrix @ data["links"][name]["matrix"])
        obj["inertial_pose_not_applied"] = data["links"][name]["inertial_pose"]
    done = set()
    def parent_joint(j, visiting=()):
        if j["name"] in done:
            return
        if j["name"] in visiting:
            raise ValueError("关节父子链形成循环")
        for upstream in data["joints"]:
            if upstream["child"] == j["parent"]:
                parent_joint(upstream, visiting+(j["name"],))
        pivot = empty("JOINT::"+j["name"], rig_col)
        attach(pivot, links.get(j["parent"], root_obj), root_matrix @ j["matrix"])
        for key in ("type", "child", "parent", "axis", "axis_model", "lower", "upper"):
            if j[key] is not None:
                pivot[key] = j[key]
        attach(links[j["child"]], pivot, root_matrix @ data["links"][j["child"]]["matrix"])
        done.add(j["name"])
    children = [j["child"] for j in data["joints"]]
    if len(set(children)) != len(children):
        raise ValueError("不支持一个 link 有多个父关节")
    for j in data["joints"]:
        parent_joint(j)
    parts = list(data["parts"])
    parts.extend(dict(i, file=str(input_root/i["path"]), link=None, scale=[1]*3) for i in config.get("extra_meshes", []))
    referenced = {Path(i["file"]).resolve() for i in parts}
    for file in input_root.rglob('*'):
        if file.suffix.lower() == '.stl' and file.resolve() not in referenced:
            if file.name not in config.get("reference_only", {}):
                raise ValueError(f"发现未处理 STL，请配置其取舍：{file}")
            parts.append({"file": str(file), "link": None, "scale": [1]*3, "reason": config["reference_only"][file.name]})
    records, objects = [], []
    for part in parts:
        file = Path(part["file"])
        obj = load_mesh(file, config["mesh_unit"])
        # 网格比例只作用于顶点，不缩放关节与其子对象。
        scale = part["scale"]
        obj.data.transform(Matrix.Diagonal(Vector((*scale, 1))))
        local = part.get("matrix", pose_values(part.get("pose", [0]*6), UNIT_SCALE[config.get("sdf_unit", "m")]))
        expected = root_matrix @ local
        attach(obj, links.get(part["link"], root_obj), expected)
        is_ref = file.name in config.get("reference_only", {})
        group = next((name for name, patterns in config.get("groups", {}).items() if any(fnmatchcase(file.name.lower(), p.lower()) for p in patterns)), "UNCLASSIFIED")
        for old in list(obj.users_collection):
            old.objects.unlink(obj)
        (reference_col if is_ref else groups[group]).objects.link(obj)
        obj.hide_render = is_ref
        obj.hide_set(is_ref)
        obj["coordinate_reason"] = part["reason"]
        obj["reference_only"] = is_ref
        obj.color = (0.62, 0.65, 0.70, 1)
        bpy.context.view_layer.update()
        error = max(abs(obj.matrix_world[r][c]-expected[r][c]) for r in range(4) for c in range(4))
        if error > 1e-6:
            raise ValueError(f"父子变换检查失败：{file.name}，误差 {error}")
        records.append({"file": file.name, "object": obj.name, "link": part["link"], "group": group, "reference_only": is_ref,
                        "reason": part["reason"], "world_matrix": [list(row) for row in expected], "matrix_error": error})
        objects.append(obj)
    reference_col.hide_render = True
    reference_col.hide_viewport = True
    # 空对象保留层级，但默认不在视口绘制，避免遮挡几何。
    for obj in rig_col.objects:
        obj.hide_set(True)
    return objects, records

def setup_views(objects, output):
    visible = [o for o in objects if not o["reference_only"]]
    points = [o.matrix_world @ Vector(v) for o in visible for v in o.bound_box]
    lo = Vector([min(v[i] for v in points) for i in range(3)])
    hi = Vector([max(v[i] for v in points) for i in range(3)])
    center, span = (lo+hi)/2, max(hi-lo)
    scene = bpy.context.scene
    presentation = collection("PREVIEW_CAMERAS", scene.collection)
    scene.render.engine = 'BLENDER_WORKBENCH'
    scene.render.resolution_x = 1200
    scene.render.resolution_y = 1200
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    scene.display.shading.light = 'STUDIO'
    scene.display.shading.color_type = 'SINGLE'
    scene.display.shading.single_color = (0.66, 0.69, 0.74)
    scene.display.shading.show_shadows = True
    scene.display.shading.show_cavity = True
    scene.display.shading.cavity_type = 'BOTH'
    scene.display.shading.background_type = 'WORLD'
    scene.world.color = (0.055, 0.055, 0.055)
    directions = {"isometric": (1,-1,0.8), "front": (0,-1,0), "top": (0,0,1), "side": (1,0,0)}
    cameras = {}
    for name, direction in directions.items():
        cam = bpy.data.cameras.new(name)
        obj = bpy.data.objects.new("VIEW::"+name, cam)
        presentation.objects.link(obj)
        obj.location = center+Vector(direction).normalized()*span*3
        obj.rotation_euler = (center-obj.location).to_track_quat('-Z','Y').to_euler()
        cam.type = 'ORTHO'
        cam.ortho_scale = span*1.6
        cam.clip_start, cam.clip_end = 0.001, 100
        scene.camera = obj
        scene.render.filepath = str(output/'preview'/f'{name}.png')
        bpy.ops.render.render(write_still=True)
        obj.hide_set(True)
        cameras[name] = obj
    scene.camera = cameras['isometric']
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type == 'VIEW_3D':
                space = area.spaces.active
                space.overlay.show_extras = False
                space.clip_start = 0.001
                space.region_3d.view_location = center
                space.region_3d.view_rotation = cameras['isometric'].rotation_euler.to_quaternion()
                space.region_3d.view_distance = span*2.0
                space.region_3d.view_perspective = 'ORTHO'
    bpy.ops.object.select_all(action='DESELECT')
    return {"min": list(lo), "max": list(hi), "dimensions_m": list(hi-lo)}
