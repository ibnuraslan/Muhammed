import bpy,numpy as np
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath="assets/toucan_b.glb")
o=[o for o in bpy.data.objects if o.type=='MESH'][0]
M=np.array(o.matrix_world); v=np.array([M[:3,:3]@np.array(x.co)+M[:3,3] for x in o.data.vertices])
h=v[v[:,2]>7]
for y in np.arange(-4,5.5,0.5):
    m=np.abs(h[:,1]-y)<0.25
    if m.sum(): print('y=%.1f n=%d xw=%.2f z=%.2f..%.2f'%(y,m.sum(),np.ptp(h[m,0]),h[m,2].min(),h[m,2].max()))
# feet
f=v[v[:,2]<-1]; print('low verts z<-1',len(f), f.min(0).round(2), f.max(0).round(2))
for z in np.arange(-5.5,2,0.5):
    m=np.abs(v[:,2]-z)<0.25; print('z=%.1f n=%d y=%.2f..%.2f x=%.2f..%.2f'%(z,m.sum(),v[m,1].min(),v[m,1].max(),v[m,0].min(),v[m,0].max()))
