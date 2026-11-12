"""Hand contact pass (v006). Every STEP frames, for every cabin character, solve the pose and test the hand verts
(same classes as pipeline/clip_scan.py) against (a) every other character's body and (b) the character's own
head/neck/torso/legs. A hand that has sunk in gets its IK target pushed back out along the surface normal of the
deepest vertex (+ margin) and keyed there, so the hand rests ON the surface it touches instead of inside it.
blender -b anim.blend --python 03b_hand_pushout.py -- <out.blend> [f0] [f1] [step]"""
import sys, bpy
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index("--") + 1:]
OUT = a[0]; F0 = int(a[1]) if len(a) > 1 else 1; F1 = int(a[2]) if len(a) > 2 else 1068; STEP = int(a[3]) if len(a) > 3 else 3
sc = bpy.context.scene; O = bpy.data.objects
CAB = ["Bomber", "Attendant", "Steward", "PaxA", "PaxB", "PaxC", "PaxD"]
ARM = ("hand", "finger", "metacarpal", "thumb", "palm")
SKIP = ("lowerarm", "wrist", "upperarm", "clavicle", "shoulder", "deltoid", "breast", "pectoral", "scapula")
SELF_T = ("head", "neck", "jaw", "spine", "pelvis", "upperleg", "lowerleg", "thigh", "calf", "foot", "toe", "root", "eye", "ear", "nose", "lip", "oris", "brow", "cheek", "temporal", "tongue", "levator", "risorius", "special", "orbicularis", "glute")
DEPTH = 0.012; MARGIN = 0.018

def mod_off(body):
    for m in body.modifiers:
        if m.type in ('MASK', 'SUBSURF', 'MULTIRES') and not m.name.startswith("Hide"): m.show_viewport = False
cls = {}
for n in CAB:
    r = O[n]; body = O[n + ".body"]; mod_off(body)
    bones = {b.name for b in r.data.bones}; gi = {g.index: g.name for g in body.vertex_groups}
    helper = {i for i, nm in gi.items() if nm.lower().startswith(("helper", "joint")) or nm in ("HelperGeometry", "JointCubes")}
    probe = {"L": [], "R": []}; selft = set(); solid = set()
    for v in body.data.vertices:
        if any(g.group in helper and g.weight > 0.5 for g in v.groups): continue
        solid.add(v.index)
        dg_ = [g for g in v.groups if gi.get(g.group) in bones]
        if not dg_: continue
        nm = gi[max(dg_, key=lambda x: x.weight).group]; lo = nm.lower()
        if any(k in lo for k in SKIP): continue
        if any(k in lo for k in ARM): probe["R" if nm.endswith(".R") else "L"].append(v.index)
        elif any(k in lo for k in SELF_T): selft.add(v.index)
    cls[n] = (probe, selft, solid)

def bvh(body, dg, keep):
    ev = body.evaluated_get(dg); me = ev.to_mesh(); mw = body.matrix_world
    vs = [mw @ v.co for v in me.vertices]
    ps = [tuple(p.vertices) for p in me.polygons if all(i in keep for i in p.vertices)]
    ev.to_mesh_clear()
    return (BVHTree.FromPolygons(vs, ps) if ps else None), vs

def push(tree, pts):
    """deepest penetration -> world offset that brings that vertex MARGIN outside the surface"""
    best = None
    for p in pts:
        loc, nrm, _, d = tree.find_nearest(p, 0.4)
        if loc is None or d < DEPTH or (p - loc).dot(nrm) >= 0: continue
        if best is None or d > best[0]: best = (d, loc - p + nrm * MARGIN)
    return best

moved = 0
for it in range(3):
    for f in range(F0, F1 + 1, STEP):
        sc.frame_set(f); dg = bpy.context.evaluated_depsgraph_get()
        full, own, verts = {}, {}, {}
        for n in CAB:
            probe, selft, solid = cls[n]; body = O[n + ".body"]
            full[n], verts[n] = bvh(body, dg, solid)
            own[n], _ = bvh(body, dg, selft)
        for n in CAB:
            r = O[n]; probe = cls[n][0]
            for s in "LR":
                pts = [verts[n][i] for i in probe[s][::2]]
                tot = Vector()
                for m in CAB:
                    tree = own[n] if m == n else full[m]
                    if tree is None: continue
                    b = push(tree, [p + tot for p in pts])
                    if b: tot += b[1]
                if tot.length < 1e-4: continue
                pb = r.pose.bones["IK_hand." + s]
                Mw = r.matrix_world @ pb.matrix
                Mw.translation += tot
                pb.matrix = r.matrix_world.inverted() @ Mw
                bpy.context.view_layer.update()
                pb.keyframe_insert("location", frame=f, group="IK_hand." + s)
                pb.keyframe_insert("rotation_quaternion", frame=f, group="IK_hand." + s)
                moved += 1
                print("PUSH it%d f%d %s.%s %.3f" % (it, f, n, s, tot.length))
print("PUSHED", moved)
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("PUSHOUT_SAVED", OUT)
