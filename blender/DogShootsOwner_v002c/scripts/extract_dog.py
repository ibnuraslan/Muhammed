import bpy, bmesh, sys, math
from mathutils import Vector, Matrix
import numpy as np
a=sys.argv[sys.argv.index("--")+1:]; src,out,thr=a[0],a[1],float(a[2])
for o in list(bpy.data.objects): bpy.data.objects.remove(o)
bpy.ops.import_scene.gltf(filepath=src)
o=[o for o in bpy.data.objects if o.type=='MESH'][0]
mw=o.matrix_world.copy(); o.parent=None; o.matrix_world=mw
for x in [x for x in bpy.data.objects if x!=o]: bpy.data.objects.remove(x)
bpy.context.view_layer.objects.active=o; o.select_set(True); bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
me=o.data; P=np.array([v.co[:] for v in me.vertices])
# ground plane fit by RANSAC-ish least squares on lowest 70% in z after rough fit
A=np.c_[P[:,0],P[:,1],np.ones(len(P))]
for it in range(4):
    if it==0: m=np.ones(len(P),bool)
    coef,_,_,_=np.linalg.lstsq(A[m],P[m,2],rcond=None)
    res=P[:,2]-A@coef
    m=np.abs(res)<np.percentile(np.abs(res),60)
h=P[:,2]-A@coef
n=np.array([-coef[0],-coef[1],1.0]); n/=np.linalg.norm(n); h=h/np.sqrt(coef[0]**2+coef[1]**2+1)
high=h>0.06
c=P[high][:,:2]; cen=np.median(c,axis=0)
d=np.linalg.norm(P[:,:2]-cen,axis=1)
# dog cluster: high points within 1.2 m of the median
hc=high&(d<1.2)
lo=P[hc].min(0)-0.08; hi=P[hc].max(0)+0.08
print("EXT plane", coef, "dog bbox", lo, hi, "count", hc.sum())
keep=(P[:,0]>lo[0])&(P[:,0]<hi[0])&(P[:,1]>lo[1])&(P[:,1]<hi[1])&(h>thr)
bm=bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
bmesh.ops.delete(bm, geom=[bm.verts[i] for i in range(len(P)) if not keep[i]], context='VERTS')
bm.to_mesh(me); bm.free()
# level the ground plane to z=0: rotate so n -> +Z, then put the lowest point at 0
R=Vector(n).rotation_difference(Vector((0,0,1))).to_matrix().to_4x4()
me.transform(R); V=[v.co for v in me.vertices]
mn=Vector([min(v[i] for v in V) for i in range(3)]); mx=Vector([max(v[i] for v in V) for i in range(3)])
me.transform(Matrix.Translation(-Vector(((mn.x+mx.x)/2,(mn.y+mx.y)/2,mn.z)))); me.update()
o.name="SleepDog"; bpy.context.view_layer.update()
print("EXT dims", tuple(round(x,3) for x in o.dimensions), "verts", len(me.vertices))
bpy.ops.wm.save_as_mainfile(filepath=out)
sc=bpy.context.scene; sc.render.engine='CYCLES'; sc.cycles.samples=12; sc.render.resolution_x=sc.render.resolution_y=400
w=bpy.data.worlds.new("w"); sc.world=w; w.use_nodes=True; w.node_tree.nodes["Background"].inputs[1].default_value=1.2
cam=bpy.data.objects.new("c",bpy.data.cameras.new("c")); sc.collection.objects.link(cam); sc.camera=cam
D=max(o.dimensions)
for i,loc in enumerate([(D*1.2,-D*1.2,D*0.8),(-D*1.2,D*0.4,D*0.5),(0,0,D*2)]):
    cam.location=loc; cam.rotation_euler=(Vector((0,0,o.dimensions.z*0.4))-Vector(loc)).to_track_quat('-Z','Y').to_euler()
    sc.render.filepath=out.replace(".blend",f"_{i}.png"); bpy.ops.render.render(write_still=True)
