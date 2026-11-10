"""配置驱动的右手坐标变换，向量转换不引入地理坐标或重心假设。"""
import json
import math


def determinant(a):
    return a[0][0]*(a[1][1]*a[2][2]-a[1][2]*a[2][1])-a[0][1]*(a[1][0]*a[2][2]-a[1][2]*a[2][0])+a[0][2]*(a[1][0]*a[2][1]-a[1][1]*a[2][0])


def transpose(a):
    return [list(row) for row in zip(*a)]


def matvec(a,v):
    if len(v)!=3 or not all(math.isfinite(x) for x in v):
        raise ValueError('向量必须含三个有限数值')
    return [sum(row[i]*v[i] for i in range(3)) for row in a]


def validate_matrix(a):
    if len(a)!=3 or any(len(row)!=3 for row in a) or not all(math.isfinite(x) for row in a for x in row):
        raise ValueError('需要有限数值3x3矩阵')
    orth=max(abs(sum(a[k][i]*a[k][j] for k in range(3))-(1 if i==j else 0)) for i in range(3) for j in range(3))
    det=determinant(a)
    if abs(det-1)>1e-7 or orth>1e-7:
        raise ValueError('转换矩阵必须为正交的右手旋转')
    return {'determinant':det,'orthogonality_error':orth}


def definitions(config):
    d=config['coordinate_frames']
    if not d['right_handed'] or any(not f['right_handed'] for f in d['frames'].values()):
        raise ValueError('此模块只接受明确的右手坐标系')
    for transform in d['transforms'].values():
        if transform['source'] not in d['frames'] or transform['target'] not in d['frames']:
            raise ValueError('转换引用了未定义坐标系')
        validate_matrix(transform['matrix'])
    return d


def rotation(config,source,target):
    d=definitions(config)
    if source not in d['frames'] or target not in d['frames']:
        raise ValueError('未知坐标系')
    identity=[[1,0,0],[0,1,0],[0,0,1]]
    pending=[(source,identity)];seen=set()
    while pending:
        frame,acc=pending.pop(0)
        if frame==target:return acc
        if frame in seen:continue
        seen.add(frame)
        for tr in d['transforms'].values():
            edge=tr['matrix'] if tr['source']==frame else transpose(tr['matrix']) if tr['target']==frame else None
            if edge is not None:
                next_frame=tr['target'] if tr['source']==frame else tr['source']
                composed=[[sum(edge[i][k]*acc[k][j] for k in range(3)) for j in range(3)] for i in range(3)]
                pending.append((next_frame,composed))
    raise ValueError('坐标系之间没有已声明转换')


def convert(config,v,source,target):
    return matvec(rotation(config,source,target),v)


def validate(config):
    d=definitions(config);records={}
    for name,tr in d['transforms'].items():
        info=validate_matrix(tr['matrix']);back=rotation(config,tr['target'],tr['source'])
        errors=[]
        for v in ([1,0,0],[0,1,0],[0,0,1],[.13,-.21,.37]):
            result=matvec(back,matvec(tr['matrix'],v));errors.append(max(abs(a-b) for a,b in zip(v,result)))
        assert max(errors)<1e-7
        records[name]=dict(info,round_trip_error=max(errors),basis_vectors=[matvec(tr['matrix'],v) for v in ([1,0,0],[0,1,0],[0,0,1])])
    tests=[]
    for case in d.get('unit_basis_tests',[]):
        actual=convert(config,case['input'],case['source'],case['target'])
        error=max(abs(a-b) for a,b in zip(actual,case['expected']));assert error<1e-7
        tests.append(dict(case,actual=actual,error=error))
    return {'status':'PASS','definitions':d,'transforms':records,'basis_tests':tests}


def attach_metadata(config):
    import bpy
    d=definitions(config)
    for name in d['identity_objects']:
        matrix=bpy.data.objects[name].matrix_world
        if max(abs(matrix[i][j]-(1 if i==j else 0)) for i in range(4) for j in range(4))>1e-7:
            raise ValueError('声明的原点对象不是单位变换：'+name)
    root=bpy.data.objects[d['root_object']]
    root['aeroviz_coordinate_frames_json']=json.dumps(d,ensure_ascii=False,sort_keys=True)
    root['coordinate_system']=d['model_frame']
    root['coordinate_origin']=d['origin']
    root['right_handed']=d['right_handed']
    return validate(config)


def verify_scene(config):
    """只读验证元数据和原点，不用重新写入来掩盖缺失元数据。"""
    import bpy
    d=definitions(config)
    for name in d['identity_objects']:
        matrix=bpy.data.objects[name].matrix_world
        assert max(abs(matrix[i][j]-(1 if i==j else 0)) for i in range(4) for j in range(4))<1e-7
    root=bpy.data.objects[d['root_object']]
    assert json.loads(root['aeroviz_coordinate_frames_json'])==d
    assert root['coordinate_system']==d['model_frame'] and root['coordinate_origin']==d['origin'] and root['right_handed']
    return validate(config)
