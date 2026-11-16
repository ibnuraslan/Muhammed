"""Straighten + rig the CC-BY '3d High-Poly Alligator' (SDPM Esare) as a crocodile.
blender -b --factory-startup -P 01_croc_rig.py -- assets/croc_hp.glb work/croc.blend
Result: mesh 'Croc_body' on armature 'Croc' (head toward -Y, belly on z=0, ~3.4 m long).
Bones: root > body > spine1 > spine2 > neck > head ; body > tail1..tail8 ; spine2 > FL_up>FL_lo, FR_up>FR_lo ; body > HL_up>HL_lo, HR_up>HR_lo"""
import bpy, sys, math
import numpy as np
from mathutils import Vector, Matrix
a = sys.argv[sys.argv.index("--") + 1:]; SRC, OUT = a
for o in list(bpy.data.objects): bpy.data.objects.remove(o)
bpy.ops.import_scene.gltf(filepath=SRC)
ob = [o for o in bpy.data.objects if o.type == 'MESH'][0]
mw = ob.matrix_world.copy(); ob.parent = None; ob.matrix_world = mw
for o in [o for o in bpy.data.objects if o is not ob]: bpy.data.objects.remove(o)
bpy.context.view_layer.objects.active = ob; ob.select_set(True)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
ob.name = "Croc_body"; me = ob.data
import bmesh
bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.002); bm.to_mesh(me); bm.free()
P = np.array([tuple(v.co) for v in me.vertices])
# hand-picked centre line (model units, top view), snout -> tail tip
SP = [(4.25,-3.85),(3.3,-2.65),(2.9,-2.1),(2.4,-1.5),(1.6,-0.85),(0.6,-0.2),(-0.4,0.0),(-1.4,0.1),
      (-2.4,0.05),(-3.1,-0.4),(-3.4,-1.2),(-3.4,-2.1),(-3.0,-3.0),(-2.45,-3.5)]
def zmid(x, y, r=0.35):
    d = np.hypot(P[:,0]-x, P[:,1]-y); m = d < r
    if m.sum() < 5: m = d < r*2
    return 0.5*(P[m,2].min()+P[m,2].max())
S3 = [np.array([x, y, zmid(x, y)]) for x, y in SP]
# segments (bone name, start, end) in curved space; front chain points forward from hips (index 5)
segs = [("spine1",5,4),("spine2",4,3),("neck",3,2),("head",2,0)] + [("tail%d"%(i-4),i,i+1) for i in range(5,13)]
LEGS = {"FL":((2.6,-1.35),(3.75,-1.3),"spine2"),"FR":((2.2,-1.8),(1.95,-2.8),"spine2"),
        "HL":((0.75,0.05),(1.0,0.42),"spine1"),"HR":((0.45,-0.55),(0.25,-1.85),"spine1")}
def footz(x,y):
    d = np.hypot(P[:,0]-x, P[:,1]-y); r = 0.3
    while (d < r).sum() < 5: r *= 1.5
    return P[d < r,2].min() + 0.08
legsegs = []
for k,(s,e,par) in LEGS.items():
    s3 = np.array([s[0],s[1],zmid(*s)]); e3 = np.array([e[0],e[1],footz(*e)])
    m3 = 0.5*(s3+e3) + np.array([0,0,0.12])
    legsegs += [(k+"_up", s3, m3, par), (k+"_lo", m3, e3, k+"_up")]
# --- straightening: lay the centre line straight along -Y (head) / +Y (tail), keep z
L = [np.linalg.norm(S3[i+1][:2]-S3[i][:2]) for i in range(len(S3)-1)]
ST = [None]*len(S3); ST[5] = np.array([0,0,S3[5][2]])
for i in range(4,-1,-1): ST[i] = ST[i+1] + np.array([0,-L[i],S3[i][2]-S3[i+1][2]])
for i in range(6,len(S3)): ST[i] = ST[i-1] + np.array([0,L[i-1],S3[i][2]-S3[i-1][2]])
def rigid(a0,a1,b0,b1):
    """rotation about z mapping dir a0->a1 to b0->b1, plus translation"""
    da = (a1-a0)[:2]; db = (b1-b0)[:2]
    ang = math.atan2(db[1],db[0]) - math.atan2(da[1],da[0])
    R = np.array([[math.cos(ang),-math.sin(ang),0],[math.sin(ang),math.cos(ang),0],[0,0,1]])
    return R, b0 - R@a0
T = {}
for n,i,j in segs: T[n] = rigid(S3[i],S3[j],ST[i],ST[j])
T["body"] = T["spine1"]
def segdist(p, a0, a1):
    ab = a1-a0; t = np.clip(((p-a0)@ab)/(ab@ab),0,1)
    return np.linalg.norm(p - (a0 + t[:,None]*ab), axis=1)
names = [n for n,_,_ in segs]; D = np.stack([segdist(P,S3[i],S3[j]) for _,i,j in segs],1)
# leg verts: closer to a leg segment than to the spine
LD = np.stack([segdist(P,s,e) for _,s,e,_ in legsegs],1); lnames = [l[0] for l in legsegs]
W = {}
allD = np.concatenate([D, LD*1.25], 1); alln = names + lnames
Wm = (allD + 0.02) ** -5; Wm /= Wm.sum(1, keepdims=True)
for vi in range(len(P)):
    idx = np.argsort(-Wm[vi])[:4]; ww = Wm[vi, idx]; ww = ww/ww.sum()
    W[vi] = [(alln[i], float(w)) for i, w in zip(idx, ww) if w > 0.01]
# straighten vertices (legs ride with their parent spine bone)
def tf(n):
    while n not in T: n = dict((l[0],l[3]) for l in legsegs)[n]
    return T[n]
NP = np.zeros_like(P)
for vi in range(len(P)):
    acc = np.zeros(3)
    for n,w in W[vi]:
        R,t = tf(n); acc += w*(R@P[vi]+t)
    NP[vi] = acc
# scale to ~3.4 m, belly on z=0, head toward -Y
tot = sum(L); s = 3.4/tot
NP *= s; ST = [p*s for p in ST]
zb = NP[:,2].min(); NP[:,2] -= zb; ST = [p-np.array([0,0,zb]) for p in ST]
for v,c in zip(me.vertices, NP): v.co = c
me.update()
# legs in straight space
LS = []
for n,s3,e3,par in legsegs:
    R,t = tf(n); LS.append((n,(R@s3+t)*s-np.array([0,0,zb]),(R@e3+t)*s-np.array([0,0,zb]),par))
# armature
arm = bpy.data.armatures.new("Croc"); rig = bpy.data.objects.new("Croc", arm); bpy.context.scene.collection.objects.link(rig)
bpy.context.view_layer.objects.active = rig; bpy.ops.object.mode_set(mode='EDIT')
E = arm.edit_bones
def eb(n, h, t, par=None, conn=False):
    b = E.new(n); b.head = Vector(h); b.tail = Vector(t); b.roll = 0
    if par: b.parent = E[par]; b.use_connect = conn
    return b
eb("root",(0,0,0),(0,-0.4,0))
eb("body",ST[5],ST[5]+np.array([0,-0.15,0]),"root")
prev = "body"
for n,i,j in segs:
    if n.startswith("tail"): continue
    eb(n, ST[i], ST[j], prev if prev!="body" else "body", prev!="body"); prev = n
prev = "body"
for n,i,j in segs:
    if not n.startswith("tail"): continue
    eb(n, ST[i], ST[j], prev, prev!="body"); prev = n
for n,h,t,par in LS: eb(n,h,t,par, par.endswith("_up"))
bpy.ops.object.mode_set(mode='OBJECT')
for b in rig.pose.bones: b.rotation_mode = 'QUATERNION'
ob.parent = rig
for n in alln: ob.vertex_groups.new(name=n)
for vi,lst in W.items():
    for n,w in lst: ob.vertex_groups[n].add([vi], w, 'REPLACE')
md = ob.modifiers.new("Armature",'ARMATURE'); md.object = rig
sm = ob.modifiers.new("Smooth",'CORRECTIVE_SMOOTH'); sm.iterations = 6; sm.smooth_type = 'LENGTH_WEIGHTED'; sm.use_only_smooth = True
# material: softened, brighter olive (animated look)
for m in me.materials:
    nt = m.node_tree; b = [n for n in nt.nodes if n.type=='BSDF_PRINCIPLED'][0]
    b.inputs["Roughness"].default_value = 0.55
    for l in list(b.inputs["Base Color"].links):
        hsv = nt.nodes.new("ShaderNodeHueSaturation"); hsv.inputs["Saturation"].default_value = 1.15; hsv.inputs["Value"].default_value = 1.45
        nt.links.new(l.from_socket, hsv.inputs["Color"]); nt.links.new(hsv.outputs[0], b.inputs["Base Color"])
    nm = [n for n in nt.nodes if n.type=='NORMAL_MAP']
    for n in nm: n.inputs["Strength"].default_value = 0.35
print("BONES", [b.name for b in arm.bones], "LEN", NP[:,1].min(), NP[:,1].max(), "Z", NP[:,2].max())
bpy.ops.wm.save_as_mainfile(filepath=OUT)
