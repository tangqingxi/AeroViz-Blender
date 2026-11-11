"""米制包围盒与三角形分离轴检查，不以包围盒重叠冒充实体穿透。"""
from mathutils import Vector


def bounds(obj):
    points = [obj.matrix_world @ Vector(v) for v in obj.bound_box]
    return ([min(p[i] for p in points) for i in range(3)],
            [max(p[i] for p in points) for i in range(3)])


def triangle_box(triangle, lo, hi, tolerance=1e-6):
    """严格内部相交；1微米内的接触不计为明显穿透。"""
    center = Vector([(lo[i]+hi[i])/2 for i in range(3)])
    half = Vector([(hi[i]-lo[i])/2 for i in range(3)])
    p = [v-center for v in triangle]
    edges = [p[1]-p[0],p[2]-p[1],p[0]-p[2]]
    basis = [Vector((1,0,0)),Vector((0,1,0)),Vector((0,0,1))]
    axes = basis+[edges[0].cross(edges[1])]+[e.cross(a) for e in edges for a in basis]
    for axis in axes:
        length = axis.length
        if length < 1e-12: continue
        axis /= length
        r = sum(abs(axis[i])*half[i] for i in range(3))
        values = [v.dot(axis) for v in p]
        if min(values) >= r-tolerance or max(values) <= -r+tolerance: return False
    return True


def triangles(obj):
    mesh = obj.data; mesh.calc_loop_triangles()
    vertices = [obj.matrix_world @ v.co for v in mesh.vertices]
    return [(tri.index,[vertices[i] for i in tri.vertices]) for tri in mesh.loop_triangles]


def box_hits(lo,hi,mesh_triangles):
    return [index for index,triangle in mesh_triangles if triangle_box(triangle,lo,hi)]


def cardinal_sweep(battery, obstacles, distance=.38):
    """本模型电池是轴对齐长方体，沿坐标轴的完整扫掠体仍是长方体。"""
    lo,hi = bounds(battery)
    points = [battery.matrix_world @ v.co for v in battery.data.vertices]
    assert len(points) == 8 and all(all(min(abs(p[i]-lo[i]),abs(p[i]-hi[i]))<1e-7 for i in range(3)) for p in points)
    geometry = {o.name:triangles(o) for o in obstacles}
    result = {'battery_bounds':{'min':lo,'max':hi},'obstacle_bounds':{o.name:bounds(o) for o in obstacles},'directions':{}}
    for axis,sign,label in [(1,1,'+Y'),(1,-1,'-Y'),(0,1,'+X'),(0,-1,'-X')]:
        lower=list(lo);upper=list(hi)
        if sign>0:upper[axis] += distance
        else:lower[axis] -= distance
        # 新扫掠区域排除已被初始电池占据的体积，单列源装配已有重叠。
        fresh_lo=list(lower);fresh_hi=list(upper)
        if sign>0:fresh_lo[axis]=hi[axis]
        else:fresh_hi[axis]=lo[axis]
        initial={name:box_hits(lo,hi,ts) for name,ts in geometry.items()}
        swept={name:box_hits(lower,upper,ts) for name,ts in geometry.items()}
        fresh={name:box_hits(fresh_lo,fresh_hi,ts) for name,ts in geometry.items()}
        result['directions'][label]={'delta':[sign*distance if i==axis else 0 for i in range(3)],
            'initial_intersections':{n:len(v) for n,v in initial.items() if v},
            'swept_intersections':{n:len(v) for n,v in swept.items() if v},
            'new_swept_intersections':{n:len(v) for n,v in fresh.items() if v},
            'clear_of_new_penetration':not any(fresh.values())}
    return result
