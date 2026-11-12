"""v008b: lift hands out of the character's own legs/pelvis/belly (hand_fix.py only tests the torso).
blender -b in.blend --python leg_fix.py -- out.blend [rounds] [Boy,Man,...]
For each frame (step 2) where a hand vertex is >1.5 cm under the leg/pelvis/spine skin, the IK hand target is keyed
along the mean surface normal by the deepest depth + 0.8 cm. A prop held in that hand at that frame moves with it."""
import sys, bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index("--") + 1:]; OUT = a[0]; ROUNDS = int(a[1]) if len(a) > 1 else 4
sc = bpy.context.scene
HAND = ("hand", "finger", "metacarpal", "thumb"); TGT = ("upperleg", "lowerleg", "pelvis", "spine01", "spine02", "glute", "foot")
HELD = (("Brick_Big", "Boy", "R", 1, 131), ("Brick_Small", "Boy", "R", 336, 712), ("Prop_Tweezers", "Mom", "R", 960, 1145),
        ("Prop_Inhaler", "Man", "R", 1606, 1720), ("Prop_Tissue", "Man", "R", 1515, 1582), ("Prop_Gamepad", "Teen", "R", 1395, 1439), ("Prop_Phone", "Man", "R", 1440, 1469))
INFO = {}
for nm in (a[2].split(",") if len(a) > 2 else ("Boy", "Teen", "Man", "Mom")):
    arm = bpy.data.objects[nm]; body = bpy.data.objects[nm + "_Body"]
    bones = set(arm.data.bones.keys()); gi = {g.index: g.name for g in body.vertex_groups if g.name in bones}
    dom = []
    for v in body.data.vertices:
        g = max((g for g in v.groups if g.group in gi), key=lambda g: g.weight, default=None); dom.append(gi[g.group] if g else "")
    INFO[nm] = (arm, body, dom)
def push(arm, s, f, delta):
    n = "IK_hand." + s; pb = arm.pose.bones[n]
    d = arm.data.bones[n].matrix_local.to_3x3().inverted() @ (arm.matrix_world.to_3x3().inverted() @ delta)
    pb.location = pb.location + d; pb.keyframe_insert("location", frame=f, group=n)
    for pn, cn, cs, f0, f1 in HELD:
        if cn == arm.name and cs == s and f0 <= f <= f1 and pn in bpy.data.objects:
            o = bpy.data.objects[pn]; o.location = o.location + delta; o.keyframe_insert("location", frame=f)
for rnd in range(ROUNDS):
    n_hit = 0
    for f in range(sc.frame_start, sc.frame_end + 1, 2):
        sc.frame_set(f); dg = bpy.context.evaluated_depsgraph_get(); todo = []
        for nm, (arm, body, dom) in INFO.items():
            if arm.hide_render or body.hide_render: continue
            e = body.evaluated_get(dg); me = e.to_mesh()
            if len(me.vertices) != len(dom): e.to_mesh_clear(); continue
            Mw = e.matrix_world; V = [Mw @ v.co for v in me.vertices]
            polys = [tuple(p.vertices) for p in me.polygons if all(dom[i].startswith(TGT) for i in p.vertices)]
            e.to_mesh_clear()
            if not polys: continue
            T = BVHTree.FromPolygons(V, polys)
            for s in "LR":
                deep, nsum = 0.0, Vector()
                for i, n in enumerate(dom):
                    if not (n.startswith(HAND) and n.endswith("." + s)): continue
                    loc, nr, _, d = T.find_nearest(V[i], 0.3)
                    if loc is not None and d > 0.015 and (V[i] - loc).dot(nr) < 0: deep = max(deep, d); nsum += nr
                if deep > 0 and nsum.length > 1e-6: todo.append((arm, s, nsum.normalized() * (deep + 0.008)))
        for arm, s, dv in todo: push(arm, s, f, dv); n_hit += 1
    print("LEGFIX round", rnd, "hits", n_hit)
    if n_hit == 0: break
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print("LEGFIX saved", OUT)
