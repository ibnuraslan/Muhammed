"""near-clip check by view depth: YOU's camera-visible geometry inside the frame with depth < LIM"""
import bpy, sys, math
from mathutils import Vector
a=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
f0,f1,st=(int(a[0]),int(a[1]),int(a[2])) if a else (1,4284,3)
sc=bpy.context.scene; cam=sc.camera; LIM=0.11
objs=[o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith("YOU.") and ("body" in o.name or "casualsuit" in o.name or "shoes" in o.name) and "headpart" not in o.name and "reveal" not in o.name]
print("LENS2 objs",[o.name for o in objs])
for f in range(f0,f1+1,st):
    sc.frame_set(f); dg=bpy.context.evaluated_depsgraph_get()
    cd=cam.data; fr=[cam.matrix_world @ v for v in cd.view_frame(scene=sc)]
    Mi=cam.matrix_world.inverted()
    # frame half-extents at depth 1
    vf=cd.view_frame(scene=sc); dz=-vf[0].z; xs=max(abs(v.x) for v in vf)/dz; ys=max(abs(v.y) for v in vf)/dz
    best=(9,None)
    for o in objs:
        ev=o.evaluated_get(dg); me=ev.to_mesh(); M=Mi@o.matrix_world
        for v in me.vertices:
            p=M@v.co; d=-p.z
            if 0<d<LIM and abs(p.x)<=xs*d+0.02 and abs(p.y)<=ys*d+0.02 and d<best[0]: best=(d,o.name)
        ev.to_mesh_clear()
    if best[1]: print("CLIPD",f,round((f-1)/60,2),round(best[0],3),best[1])
