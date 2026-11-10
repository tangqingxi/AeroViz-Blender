"""验证优先级、透明度、颜色空间及多 Visual 歧义处理。"""
from pathlib import Path
import sys
import bpy
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from materials import resolve_definition,linear_rgb,match_visual
settings={'source_color_space':'linear','roughness':0.62}
library={'Gazebo/White':{'diffuse':[1,1,1,1],'specular':[0.1]*3+[1]}}
r={'key':'a/v','link':'a','mesh_uri':'model://m/part.STL','diffuse':[0.2,0.4,0.75,0.8],'ambient':None,'specular':None,'emissive':None,'transparency':0.25,'script_name':'Gazebo/White'}
d=resolve_definition(r,settings,library)
assert d['source']=='sdf_rgba' and abs(d['rgba'][3]-0.6)<1e-9
assert d['rgba'][:3]==[0.2,0.4,0.75]
r['diffuse']=None
assert resolve_definition(r,settings,library)['source']=='gazebo_named'
r['script_name']='__default__'
assert resolve_definition(r,settings,library) is None
assert abs(linear_rgb([0.5],'srgb')[0]-0.21404114048223255)<1e-9
assert linear_rgb([0.5],'linear')==[0.5]
obj=bpy.data.objects.new('material_mapping_test',None)
obj['source_file']='part.STL'
other=dict(r,key='b/v',link='b')
try:
    match_visual(obj,[r,other],{})
    raise AssertionError('歧义不应被静默接受')
except ValueError:
    pass
assert match_visual(obj,[r,other],{'object_visuals':{obj.name:'b/v'}})['link']=='b'
print('MATERIAL_MAPPING_TESTS_OK')
