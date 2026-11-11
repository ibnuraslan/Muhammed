import bpy,numpy as np
bpy.ops.wm.read_factory_settings(use_empty=True)
for f in ("toucan_scan","toucan_b"):
    for o in list(bpy.data.objects): bpy.data.objects.remove(o)
    bpy.ops.import_scene.gltf(filepath=f"assets/{f}.glb")
    for o in [o for o in bpy.data.objects if o.type=='MESH']:
        M=np.array(o.matrix_world); v=np.array([M[:3,:3]@np.array(x.co)+M[:3,3] for x in o.data.vertices])
        c=v.mean(0); u,s,vt=np.linalg.svd(v-c,full_matrices=False)
        print(f,o.name,'mean',c.round(3),'axes',vt.round(2).tolist(),'sd',s.round(2))
        p=(v-c)@vt[0]; print(' extent along ax0',p.min().round(3),p.max().round(3))
        # uv-based colour: sample texture at a few points along axis
        img=[i for i in bpy.data.images][0]; px=np.array(img.pixels[:]).reshape(img.size[1],img.size[0],4)
        uvl=o.data.uv_layers.active.data; vuv=np.zeros((len(v),2))
        for l in o.data.loops: vuv[l.vertex_index]=uvl[l.index].uv
        for t in np.linspace(p.min(),p.max(),12):
            m=np.abs(p-t)<(p.max()-p.min())/24
            uv=vuv[m]; cols=px[(uv[:,1].clip(0,.999)*img.size[1]).astype(int),(uv[:,0].clip(0,.999)*img.size[0]).astype(int),:3]
            print('  t=%.3f n=%d col=%s ext1=%.3f ext2=%.3f'%(t,m.sum(),cols.mean(0).round(2),np.ptp((v[m]-c)@vt[1]),np.ptp((v[m]-c)@vt[2])))
        break
