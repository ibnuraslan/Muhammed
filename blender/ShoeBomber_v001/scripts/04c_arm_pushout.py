"""Arm-through-body pass (v006d, matches pipeline/limb_check.py ARMBODY minus the shoulder joint itself): every STEP frames,
for every arm the camera can see, points along upperarm02 / lowerarm01-02 / wrist that are > 3 cm inside the owner's torso or
inside any other body push the arm out: the elbow pole and (for forearm points) the IK hand target move by the push vector.
blender -b film.blend --python 04c_arm_pushout.py -- <out.blend> [f0] [f1] [step]"""
import bpy, sys
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from bpy_extras.object_utils import world_to_camera_view
a = sys.argv[sys.argv.index("--") + 1:]
OUT = a[0]; F0 = int(a[1]) if len(a) > 1 else 1; F1 = int(a[2]) if len(a) > 2 else bpy.context.scene.frame_end
STEP = int(a[3]) if len(a) > 3 else 2
sc = bpy.context.scene; cam = sc.camera; O = bpy.data.objects
saved = {}
for o in O:
    for m in getattr(o, "modifiers", []):
        if m.type in ("MASK", "SUBSURF", "MULTIRES"): saved[(o.name, m.name)] = m.show_viewport; m.show_viewport = False
RIGS = [o for o in O if o.type == 'ARMATURE' and "head" in o.pose.bones and "upperarm01.L" in o.pose.bones and "IK_hand.L" in o.pose.bones]
def body_of(r):
    m = [c for c in r.children_recursive if c.type == 'MESH' and "body" in c.name.lower()]
    return max(m, key=lambda c: len(c.data.vertices)) if m else None
BODY = {r.name: body_of(r) for r in RIGS}
TORSO_G = ("spine", "pelvis", "clavicle", "breast", "neck", "root", "shoulder")
CLS = {}
for r in RIGS:
    b = BODY[r.name]
    if b is None: continue
    gi = {g.index: g.name.lower() for g in b.vertex_groups}; bones = {bn.name.lower() for bn in r.data.bones}
    torso, skin = set(), set()
    for v in b.data.vertices:
        gs = [g for g in v.groups if g.weight > 0.05]
        if any(gi.get(g.group, "").startswith(("helper", "joint")) and g.weight > 0.5 for g in gs): continue
        skin.add(v.index); gs = [g for g in gs if gi.get(g.group, "") in bones]
        if not gs: continue
        dom = gi.get(max(gs, key=lambda g: g.weight).group, "")
        if any(dom.startswith(k) for k in TORSO_G): torso.add(v.index)
    CLS[r.name] = (torso, skin)
def bvh(vs, ps, keep):
    q = [p for p in ps if all(i in keep for i in p)]
    return BVHTree.FromPolygons(vs, q) if q else None
def W(r, b, tail=False):
    pb = r.pose.bones[b]; return r.matrix_world @ (pb.tail if tail else pb.head)
def seen(p):
    c = world_to_camera_view(sc, cam, p); return 0 <= c.x <= 1 and 0 <= c.y <= 1 and c.z > 0.05
ARM = ["upperarm02", "lowerarm01", "lowerarm02"]
def move(r, bone, off, f):
    pb = r.pose.bones[bone]; M = r.matrix_world @ pb.matrix; M.translation += off
    pb.matrix = r.matrix_world.inverted() @ M; bpy.context.view_layer.update()
    pb.keyframe_insert("location", frame=f, group=bone)
    if pb.rotation_mode == 'QUATERNION': pb.keyframe_insert("rotation_quaternion", frame=f, group=bone)
n = 0
for it in range(2):
    for f in range(F0, F1 + 1, STEP):
        if 1069 <= f < 1393: continue
        sc.frame_set(f); dg = bpy.context.evaluated_depsgraph_get()
        live = [r for r in RIGS if not r.hide_render and BODY.get(r.name) and not BODY[r.name].hide_render and r.name in CLS]
        T = {}
        for r in live:
            b = BODY[r.name]; e = b.evaluated_get(dg); me = e.to_mesh(); mw = e.matrix_world
            vs = [mw @ v.co for v in me.vertices]; ps = [tuple(p.vertices) for p in me.polygons]; e.to_mesh_clear()
            T[r.name] = (bvh(vs, ps, CLS[r.name][0]), bvh(vs, ps, CLS[r.name][1]))
        for r in live:
            for s in "LR":
                pts = []
                for bn in ARM:
                    h, t = W(r, bn + "." + s), W(r, bn + "." + s, True)
                    pts += [(h.lerp(t, k / 4), bn) for k in range(5)]
                pts.append((W(r, "wrist." + s, True), "wrist"))
                if not any(seen(p) for p, _ in pts): continue
                best = None
                for o in live:
                    tree = T[r.name][0] if o is r else T[o.name][1]
                    if tree is None: continue
                    for p, bn in pts:
                        loc, nrm, _, d = tree.find_nearest(p, 0.12)
                        if loc is None or d < 0.03 or (p - loc).dot(nrm) >= 0: continue
                        if best is None or d > best[0]: best = (d, loc - p + nrm * 0.02, bn)
                if best is None: continue
                d, off, bn = best
                move(r, "Pole_elbow." + s, off * 1.5, f)
                if bn != "upperarm02": move(r, "IK_hand." + s, off, f)
                n += 1
print("ARM_PUSHED", n)
for o in O:
    for m in getattr(o, "modifiers", []):
        if (o.name, m.name) in saved: m.show_viewport = saved[(o.name, m.name)]
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("ARM_SAVED", OUT)
