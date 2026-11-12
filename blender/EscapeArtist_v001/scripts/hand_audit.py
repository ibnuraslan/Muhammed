"""Hand audit (Hands rule, Nov 11 23:00). blender -b film.blend --python hand_audit.py -- [step]
Bone-volume test (robust against MPFB's masked helper geometry):
 - head: sphere around the head bone (r = 0.105 m, scaled by character height)
 - torso: capsule from the root bone head to neck01 (r = 0.115 m, scaled)
For every visible character, every <step> frames, the hand vertices (wrist/finger/metacarpal groups) are tested for:
 self  : inside own head sphere or own torso capsule
 hand  : left and right hand vertices closer than 8 mm (hands merging)
 other : inside another visible character's head sphere / torso capsule
A flag needs more than 6 sampled hand vertices. Prints flagged frames and a total."""
import sys, bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree
a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
STEP = int(a[0]) if a else 10
sc = bpy.context.scene
CAST = ["Prisoner", "PrisonerOld", "Boy", "Father", "Stepmother", "Guard", "Guard2", "Judge", "Protester1", "Protester2"]
HAND = ("wrist", "finger", "metacarpal")
for o in bpy.data.objects:
    for m in o.modifiers:
        if m.type == "SUBSURF": m.show_viewport = False
def seg_dist(p, a, b):
    ab = b - a; t = max(0.0, min(1.0, (p - a).dot(ab) / max(ab.length_squared, 1e-9)))
    return (p - (a + ab * t)).length
total = 0; flagged = {}
for f in range(0, sc.frame_end + 1, STEP):
    sc.frame_set(f); dg = bpy.context.evaluated_depsgraph_get()
    vols, hands = {}, {}
    for n in CAST:
        body = bpy.data.objects.get(n + ".body")
        if body is None or body.hide_render: continue
        arm = bpy.data.objects[n]; M = arm.matrix_world; PB = arm.pose.bones
        hgt = (arm.data.bones["head"].tail_local.z) / 1.8
        hd = PB["head"]; hc = M @ (hd.head + (hd.tail - hd.head) * 0.45)
        vols[n] = (hc, 0.105 * hgt, M @ PB["spine04"].head, M @ PB["neck01"].head, 0.115 * hgt)
        e = body.evaluated_get(dg); me = e.to_mesh(); MW = body.matrix_world
        vg = {g.index: g.name for g in body.vertex_groups}
        hs = {"L": [], "R": []}
        for v in list(me.vertices)[::2]:
            for g in v.groups:
                nm = vg.get(g.group, "")
                if g.weight > 0.5 and nm.startswith(HAND) and nm[-2:] in (".L", ".R"):
                    hs[nm[-1]].append(MW @ v.co); break
        e.to_mesh_clear(); hands[n] = hs
    for n, hs in hands.items():
        hc, hr, t0, t1, tr = vols[n]
        for s in "LR":
            pts = hs[s]
            k_self = sum(1 for p in pts if (p - hc).length < hr or seg_dist(p, t0, t1) < tr)
            kd = KDTree(len(hs["R" if s == "L" else "L"]))
            for i, q in enumerate(hs["R" if s == "L" else "L"]): kd.insert(q, i)
            kd.balance()
            k_hand = sum(1 for p in pts if kd.find(p)[2] is not None and kd.find(p)[2] < 0.008) if s == "L" else 0
            k_other = 0
            for m, (hc2, hr2, a2, b2, tr2) in vols.items():
                if m != n: k_other += sum(1 for p in pts if (p - hc2).length < hr2 or seg_dist(p, a2, b2) < tr2)
            for kind, k in (("self", k_self), ("hand", k_hand), ("other", k_other)):
                if k > 6:
                    total += 1; flagged.setdefault((n, kind), []).append(f)
                    print("HANDFLAG", f, n, s, kind, k)
print("HAND_AUDIT_TOTAL", total)
for k, v in flagged.items(): print("HANDFLAG_SUMMARY", k, len(v), v[:20])
