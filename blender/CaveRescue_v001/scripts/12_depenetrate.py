"""v006d hand depenetration (director round 4): wherever clip_scan finds hand/finger skin inside a body, move that
hand's IK target off the surface along the surface normal (3-5 cm clearance), keeping the elbow pole unchanged.
blender -b in.blend --python 12_depenetrate.py -- out.blend"""
import bpy, sys, os
from mathutils import Vector as V
from mathutils.bvhtree import BVHTree
OUT = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene
ARM = ("hand", "finger", "metacarpal", "thumb", "palm")
SKIP = ("lowerarm", "wrist", "upperarm", "clavicle", "shoulder", "deltoid", "breast", "pectoral", "scapula")
SELF_T = ("head", "neck", "jaw", "spine", "pelvis", "upperleg", "lowerleg", "thigh", "calf", "foot", "toe", "root", "eye", "ear", "nose", "lip", "oris", "brow", "cheek", "temporal", "tongue", "levator", "risorius", "special", "orbicularis", "glute")
# (character, frame range) from clip_scan 40c131b on v006c; both hands are tested, only penetrating ones move
JOBS = [("Boy4", 232, 250), ("Boy2", 2128, 2146), ("DiverB", 2194, 2308), ("DiverA", 2326, 2350), ("DiverB", 2362, 2416), ("DiverB", 2548, 2566)]
CLEAR = 0.04
CH = {}; RESTORE = []
for r in bpy.data.objects:
    if r.type != 'ARMATURE' or "IK_hand.L" not in r.pose.bones: continue
    body = [c for c in r.children_recursive if c.type == 'MESH' and c.name.endswith(".body")]
    if not body: continue
    body = body[0]
    for m in body.modifiers:
        if m.type in ('MASK', 'SUBSURF', 'MULTIRES') and m.show_viewport: m.show_viewport = False; RESTORE.append(m)
    bones = {b.name for b in r.data.bones}; gi = {g.index: g.name for g in body.vertex_groups}
    helper = {i for i, n in gi.items() if n.lower().startswith(("helper", "joint"))}
    probe = {"L": [], "R": []}; selft = set(); skin = set()
    for v in body.data.vertices:
        if any(g.group in helper and g.weight > 0.5 for g in v.groups): continue
        skin.add(v.index)
        dg_ = [g for g in v.groups if gi.get(g.group) in bones]
        if not dg_: continue
        n = gi[max(dg_, key=lambda x: x.weight).group]; nl = n.lower()
        if any(k in nl for k in SKIP): continue
        if any(k in nl for k in ARM): probe[n[-1]].append(v.index) if n[-1] in "LR" else None
        elif any(k in nl for k in SELF_T): selft.add(v.index)
    CH[r.name] = (r, body, probe, selft, skin)
def mesh_state(name, dg):
    r, body, probe, selft, skin = CH[name]
    ev = body.evaluated_get(dg); me = ev.to_mesh(); mw = body.matrix_world
    verts = [mw @ v.co for v in me.vertices]
    polys = [tuple(p.vertices) for p in me.polygons]
    ev.to_mesh_clear()
    sb = BVHTree.FromPolygons(verts, [p for p in polys if all(i in selft for i in p)])
    kb = BVHTree.FromPolygons(verts, [p for p in polys if all(i in skin for i in p)])
    return verts, sb, kb
def push(p, bvh, depth=0.0):
    loc, nrm, _, d = bvh.find_nearest(p, 0.08)
    if loc is None or (p - loc).dot(nrm) >= 0: return None
    return (loc - p) + nrm * CLEAR
total = 0
for name, a, b in JOBS:
    r = CH[name][0]
    others = [o for o in CH if o != name]
    frames = list(range(a, b + 1, 3))
    for it in range(8):
        offs = {}
        for f in frames:
            sc.frame_set(f); dg = bpy.context.evaluated_depsgraph_get()
            verts, sb, _ = mesh_state(name, dg)
            near = []
            P0 = r.matrix_world @ r.pose.bones["root"].head
            for o in others:
                ro = CH[o][0]
                if CH[o][1].hide_render or (ro.matrix_world @ ro.pose.bones["root"].head - P0).length > 2.5: continue
                near.append(mesh_state(o, dg)[2])
            for s in "LR":
                best = None
                for i in CH[name][2][s]:
                    p = verts[i]
                    for bv in [sb] + near:
                        dv = push(p, bv)
                        if dv is not None and (best is None or dv.length > best.length): best = dv
                if best is not None: offs[(f, s)] = (r.matrix_world.inverted().to_3x3() @ best)
        if not offs: break
        print("DEPEN", name, a, b, "iter", it, "hands moved", len(offs), "max cm", round(max(v.length for v in offs.values()) * 100, 1))
        # sample current IK targets on all frames first, then key with the offset (zero where clean, so edges stay put)
        cur = {}
        for f in frames:
            sc.frame_set(f)
            for s in "LR": cur[(f, s)] = r.pose.bones["IK_hand." + s].matrix.copy()
        for f in frames:
            for s in "LR":
                pb = r.pose.bones["IK_hand." + s]; M = cur[(f, s)].copy()
                if (f, s) in offs: M.translation += offs[(f, s)]
                elif not any((g, s) in offs for g in frames): continue
                sc.frame_set(f); pb.matrix = M; bpy.context.view_layer.update()
                pb.keyframe_insert("location", frame=f, group="IK_hand." + s); total += 1
print("DEPEN_KEYS", total)
for m in RESTORE: m.show_viewport = True
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("DEPEN_OK")
