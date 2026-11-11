"""Contact audit for SpeakWithoutSight.
blender -b anim.blend --python audit.py -- <report.txt> [step]
Checks: feet hover/sink (shoe soles vs floor or footstool), fingertip contact gap/penetration in the touch beats,
BVH overlap counts (girl<->teacher bodies, hands<->armchair, hug), camera inside geometry / too close to a surface."""
import sys, math
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index("--") + 1:]
OUT = a[0]; STEP = int(a[1]) if len(a) > 1 else 10
sc = bpy.context.scene; STOOL = Vector(sc["stool"])
def gz(x, y):
    return STOOL.z if (abs(x - STOOL.x) < 0.2 and abs(y - STOOL.y) < 0.14) else 0.0
def bvh(o):
    dg = bpy.context.evaluated_depsgraph_get(); eo = o.evaluated_get(dg); me = eo.to_mesh()
    vs = [eo.matrix_world @ v.co for v in me.vertices]; ps = [tuple(p.vertices) for p in me.polygons]
    t = BVHTree.FromPolygons(vs, ps); eo.to_mesh_clear(); return t, vs
def bone(o, n, tail=False):
    pb = o.pose.bones[n]; return o.matrix_world @ (pb.tail if tail else pb.head)
G, T = bpy.data.objects["Girl"], bpy.data.objects["Teacher"]
CONTACT = [(530, 1062, "girl R middle tip -> teacher throat", G, "finger3-3.R", "Teacher.body"),
           (1110, 1722, "girl R middle tip -> teacher lips", G, "finger3-3.R", "Teacher.body"),
           (1490, 1600, "girl L middle tip -> own lips", G, "finger3-3.L", "Girl.body"),
           (1615, 1722, "girl L middle tip -> own throat", G, "finger3-3.L", "Girl.body"),
           (1843, 1900, "girl L middle tip -> own throat", G, "finger3-3.L", "Girl.body")]
lines = []; stats = {"foot_hover": 0, "foot_sink": 0, "tip_gap": 0, "tip_pen": 0, "body_overlap_frames": 0, "hand_chair": 0, "cam_close": 0}
cam = sc.camera
chair = bpy.data.objects["ArmChair_01"]
for f in range(sc.frame_start, sc.frame_end + 1, STEP):
    sc.frame_set(f)
    # feet: lowest shoe vertex per foot vs the surface below it (seated/kneeling poses only check the planted ones)
    for P in ("Girl", "Mother", "Father"):
        sh = bpy.data.objects.get(P + ".shoes01")
        if not sh: continue
        t_, vs = bvh(sh)
        for side in (1, -1):
            o = bpy.data.objects[P]; ax = bone(o, "foot.L" if side == 1 else "foot.R")
            mine = [v for v in vs if (v - ax).length < 0.2]
            if not mine: continue
            low = min(mine, key=lambda v: v.z); d = low.z - gz(low.x, low.y)
            if d > 0.02: stats["foot_hover"] += 1; lines.append("f%d %s foot%s hover %.3f" % (f, P, "L" if side == 1 else "R", d))
            if d < -0.015: stats["foot_sink"] += 1; lines.append("f%d %s foot%s sink %.3f" % (f, P, "L" if side == 1 else "R", d))
    # fingertip contact
    for f0, f1, nm, O, b, surf in CONTACT:
        if f0 <= f <= f1:
            tree, _ = bvh(bpy.data.objects[surf]); tip = bone(O, b, True)
            loc, nrm, idx, dist = tree.find_nearest(tip)
            inside = (tip - loc).dot(nrm) < 0
            sd = -dist if inside else dist
            # fingertip bone tail sits ~8 mm inside the pad; contact = signed distance in [-0.002, 0.015]
            if sd > 0.02: stats["tip_gap"] += 1; lines.append("f%d %s gap %.3f" % (f, nm, sd))
            if sd < -0.006: stats["tip_pen"] += 1; lines.append("f%d %s penetration %.3f" % (f, nm, sd))
    # bodies through each other (girl vs teacher), hands vs chair
    tg, _ = bvh(bpy.data.objects["Girl.body"]); tt, _ = bvh(bpy.data.objects["Teacher.body"]); tc, _ = bvh(chair)
    ov = len(tg.overlap(tt))
    if ov > 40: stats["body_overlap_frames"] += 1; lines.append("f%d girl/teacher body overlap pairs %d" % (f, ov))
    oc = len(tg.overlap(tc))
    if oc > 200: stats["hand_chair"] += 1; lines.append("f%d girl body/armchair overlap pairs %d" % (f, oc))
    # camera: nearest surface over all visible meshes
    cp = cam.matrix_world.translation; dg = bpy.context.evaluated_depsgraph_get()
    hit, loc, nrm, idx, ob, _ = sc.ray_cast(dg, cp, (bpy.data.objects["CAM_Film_Aim"].location - cp).normalized(), distance=0.04)
    if hit and ob.visible_camera and not ob.name.startswith(("ExplainerDome", "DarkBubble")):
        stats["cam_close"] += 1; lines.append("f%d camera within 4 cm of %s" % (f, ob.name))
open(OUT, "w").write("AUDIT step %d\n%s\n\n%s\n" % (STEP, stats, "\n".join(lines)))
print("AUDIT", stats)
