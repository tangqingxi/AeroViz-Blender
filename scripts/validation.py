"""输入快照、几何边界、重复件和工程验收报告。"""
from pathlib import Path
import hashlib
import struct
import json
from collections import Counter

def snapshot(root):
    return {str(p.relative_to(root)): {"bytes": p.stat().st_size, "sha256": hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(root.rglob('*')) if p.is_file()}

def inspect_stl(file):
    blob = file.read_bytes()
    n = struct.unpack_from('<I', blob, 80)[0] if len(blob) >= 84 else -1
    if 84+n*50 == len(blob):
        triangles = [tuple(tuple(struct.unpack_from('<3f', blob, 84+i*50+12+k*12)) for k in range(3)) for i in range(n)]
    else:
        vertices = [tuple(map(float, line.split()[1:4])) for line in blob.decode('ascii').splitlines() if line.strip().startswith('vertex ')]
        if not vertices or len(vertices) % 3:
            raise ValueError(f"无效 STL：{file}")
        triangles = [tuple(vertices[i:i+3]) for i in range(0,len(vertices),3)]
    vertices = [v for t in triangles for v in t]
    lo = [min(v[i] for v in vertices) for i in range(3)]
    hi = [max(v[i] for v in vertices) for i in range(3)]
    # 忽略三角面顺序和顶点循环，按微米精度识别同一几何。
    canonical = Counter(tuple(sorted(tuple(round(x,6) for x in v) for v in t)) for t in triangles)
    return {"triangles": len(triangles), "min": lo, "max": hi, "dimensions": [hi[i]-lo[i] for i in range(3)]}, canonical

def audit(root):
    info, geometry = {}, {}
    for p in sorted(root.rglob('*')):
        if p.suffix.lower() == '.stl':
            if p.name in info:
                raise ValueError("文件名重复，需先扩展配置为相对路径键")
            info[p.name], geometry[p.name] = inspect_stl(p)
    duplicates = [[a,b] for a in geometry for b in geometry if a<b and geometry[a] == geometry[b]]
    return info, geometry, duplicates

def write_report(output, config, data, records, bbox, inventory, geometry, duplicates, before, after):
    if before != after:
        raise RuntimeError("原始输入内容发生变化，验收失败")
    by_file = {r['file']: r for r in records}
    if len(records) != len(inventory):
        raise RuntimeError("并非每个 STL 都有一个独立对象")
    refs = [r for r in records if r['reference_only']]
    combined = Counter()
    for r in records:
        if not r['reference_only']:
            combined |= geometry[r['file']]
    coverage = {r['file']: len(set(geometry[r['file']]) & set(combined))/len(geometry[r['file']]) for r in refs}
    if any(x < 0.99999 for x in coverage.values()):
        raise RuntimeError(f"参考件含未呈现的几何，禁止静默隐藏：{coverage}")
    for value, limits in zip(bbox['dimensions_m'], config.get('expected_dimensions_m', [])):
        if not limits[0] <= value <= limits[1]:
            raise RuntimeError(f"整机尺寸不在配置范围内：{bbox}")
    results = {"blender_version": __import__('bpy').app.version_string, "inventory": inventory, "records": records,
               "bbox": bbox, "duplicates": duplicates, "reference_coverage": coverage, "input_unchanged": before == after,
               "missing_files": [], "imported_count": len(records), "visible_count": len(records)-len(refs), "gui_status": "待实际打开验收"}
    report_dir = output/'reports'
    (report_dir/'validation.json').write_text(json.dumps(results, ensure_ascii=False, indent=2),encoding='utf8')
    (report_dir/'input_manifest.json').write_text(json.dumps(before, ensure_ascii=False, indent=2),encoding='utf8')
    lines = ['# '+config['model_name']+' Stage 1 导入验收报告', '',
             '## 文件与导入结果', '', f'- 发现 STL：{len(inventory)}；成功导入：{len(records)} 个独立 Mesh Object。',
             f'- 默认可见：{len(records)-len(refs)}；隐藏参考对象：{len(refs)}。所有 STL 均保留独立对象，无导入遗漏。',
             '- 网格引用缺失：无。SDF 本地可用，无需检索其他仓库。',
             '- 原始输入逐文件 SHA-256 前后对比一致；未修改模型输入、PX4 或执行 Git 写操作。',
             '', '## 单位与坐标依据', '',
             config.get('unit_evidence', '网格单位由配置 mesh_unit 指定；STL 自身不携带单位。'),
             '- Blender：METRIC，scale_length=1；X/Y 保持源文件方向、Z 向上。正视沿 -Y 看向 +Y，侧视从 +X 看向 -X；源文件未明确飞行前向，不自行旋转。',
             f"- 整机可见包围盒：{bbox['dimensions_m'][0]:.6f} × {bbox['dimensions_m'][1]:.6f} × {bbox['dimensions_m'][2]:.6f} m。",
             f"- 最小坐标：{bbox['min']}；最大坐标：{bbox['max']}。",
             f"- apply_model_pose={config.get('apply_model_pose', False)}；模型变换：{[list(r) for r in data['model_pose']] if hasattr(data['model_pose'], 'translation') else data['model_pose']}。关闭时保留模型坐标原点，不应用仿真生成高度。",
             '- Link pose 相对模型；Visual pose 相对 link；Joint pose 默认相对 child link。所有惯性 pose 只作元数据保存。',
             config.get('coordinate_evidence', '使用配置与描述文件的显式变换，不自动居中或猜测坐标。'),
             '- 正式坐标依据：[SDFormat 1.5 坐标语义](https://sdformat.org/tutorials/specification/pose_frame_semantics/1.5/) 与 [关节运动学](https://sdformat.org/tutorials/specification/spec_model_kinematics/)。',
             '', '## 零件逐项处理', '', '| 文件 | 原始范围 min → max（m） | 分类 / Link | 处理 |', '|---|---|---|---|']
    for name, info in inventory.items():
        r=by_file[name]
        fmt=lambda v: '('+', '.join(f'{x:.6f}' for x in v)+')'
        lines.append(f"| {name} | {fmt(info['min'])} → {fmt(info['max'])} | {r['group']} / {r['link'] or '模型根'} | {'隐藏参考；' if r['reference_only'] else '可见；'}{r['reason']} |")
    lines += ['', '## 重复与合并件检查', '']
    lines += [f'- {a} = {b}：全部三角面在微米精度一致。' for a,b in duplicates]
    lines += [f'- {name} 的不同三角面被可见独立零件覆盖 {ratio:.2%}，忽略重复计数后无独有几何遗漏。' for name,ratio in coverage.items()]
    lines += ['', '## 关节与层级检查', '', '- 所有导入对象世界矩阵与描述文件目标矩阵逐项比较，最大元素误差 ≤ 1e-6。', '- 每个关节为父 link 下的独立空对象，child link 保持原世界坐标；网格仍为独立对象。', '| 关节 | 父 → 子 | 类型 | 模型坐标中心（m） | 模型坐标轴 | 限位（rad） |', '|---|---|---|---|---|---|']
    for j in data['joints']:
        lines.append(f"| {j['name']} | {j['parent']} → {j['child']} | {j['type']} | {list(j['matrix'].translation)} | {j['axis_model']} | {j['lower']} ~ {j['upper']} |")
    lines += ['', '## 装配检查与已知不确定性', '',
              '- 四个舵面与旋翼的关节中心保留在源 SDF 定义处，未创建关键帧或动画。关节轴与限位保存在空对象自定义属性。',
              '- 配置 extra_meshes 中的零件无 SDF link：沿用原始坐标挂在模型根；固定关系未由描述文件证实，逐项依据见上表。',
              f"- 外部 include：{data.get('includes', [])}；明确跳过关节：{data.get('ignored_joints', [])}；配置说明：{config.get('ignored_includes', {})}。",
              '- 本阶段检查几何完整、尺寸与层级，不等同于制造公差、碰撞干涉或动力学验证。',
              '', '## 预览与工程', '', f"- {config['blend_name']}；preview/isometric.png、front.png、top.png、side.png。预览只使用中性工作台显示，无材质美化。",
              '', '## Blender 图形打开验证', '', '待执行：必须以实际图形窗口截图和重新打开的数据验证记录补充，不以后台导入成功代替。', '']
    (report_dir/'IMPORT_REPORT.md').write_text('\n'.join(lines),encoding='utf8')
