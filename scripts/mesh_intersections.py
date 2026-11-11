"""展示碰撞筛查：真实三角网格BVH，源装配已有相交单列记录。"""
import itertools
from mathutils import Vector
from mathutils.bvhtree import BVHTree

import geometry_checks as geo


def scan(scene,frames):
    objects=sorted((o for o in scene.objects if o.get('source_object')),key=lambda o:o.name)
    local={};cache={}
    for obj in objects:
        mesh=obj.data;mesh.calc_loop_triangles()
        local[obj.name]=([v.co.copy() for v in mesh.vertices],[tuple(t.vertices) for t in mesh.loop_triangles])
    def state(obj):
        matrix=tuple(x for row in obj.matrix_world for x in row)
        prior=cache.get(obj.name)
        if prior and prior[0]==matrix:return prior[1]
        verts,triangles=local[obj.name]
        points=[obj.matrix_world @ v for v in verts]
        item=(geo.bounds(obj),BVHTree.FromPolygons(points,triangles,all_triangles=True,epsilon=0))
        cache[obj.name]=(matrix,item)
        return item
    def hits():
        result={};states={o.name:state(o) for o in objects}
        for a,b in itertools.combinations(objects,2):
            (lo,hi),tree=states[a.name];(lo2,hi2),other=states[b.name]
            # 面或边接触不作为体积穿透，先用1微米严格包围盒排除。
            if any(min(hi[i],hi2[i])-max(lo[i],lo2[i])<=1e-6 for i in range(3)):continue
            pairs=tree.overlap(other)
            if pairs:result[a['source_object']+' | '+b['source_object']]=len(pairs)
        return result
    scene.frame_set(1);baseline=hits();events=[]
    for index,frame in enumerate(frames):
        whole=int(frame);scene.frame_set(whole,subframe=frame-whole);current=hits()
        fresh={n:count for n,count in current.items() if n not in baseline}
        if fresh:events.append({'frame':frame,'new_pairs':fresh})
        if index%1000==0:print('INTERSECTION_SCAN',index,len(frames),frame,'events',len(events),flush=True)
    scene.frame_set(1)
    return {'method':'世界空间真实三角网格BVH相交；严格包围盒排除接触；源相交不作新穿插',
            'baseline_pairs':baseline,'frames_checked':len(frames),'new_intersection_events':events,
            'status':'REVIEW' if events else 'PASS'}


def adaptive_frames(scene,start=121,end=960,max_step=.001):
    """按实际网格包围盒角点位移细分到约1毫米，覆盖快速回装的子帧。"""
    import math
    objects=[o for o in scene.objects if o.get('source_object')]
    previous=None;frames=[]
    for frame in range(start,end+1):
        scene.frame_set(frame)
        points=[o.matrix_world @ Vector(v) for o in objects for v in o.bound_box]
        if previous is not None:
            distance=max((a-b).length for a,b in zip(points,previous))
            steps=max(1,math.ceil(distance/max_step*1.05))
            frames.extend(frame-1+i/steps for i in range(1,steps+1))
        else:frames.append(float(frame))
        previous=points
    scene.frame_set(1)
    return frames
