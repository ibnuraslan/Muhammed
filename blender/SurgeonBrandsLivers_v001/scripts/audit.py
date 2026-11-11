"""Contact audit for SurgeonBrandsLivers: foot hover/sink/slide, grasp distances, hands through desks, camera inside walls or bodies.
blender -b film.blend --python audit.py -- <report.txt> [step]"""
import sys, math
import bpy
from mathutils import Vector
a = sys.argv[sys.argv.index("--") + 1:]
OUT = a[0]; STEP = int(a[1]) if len(a) > 1 else 3
sc = bpy.context.scene
V = Vector
DAIS_H = 0.4
def ground(x, y):
    return DAIS_H if (-12.0 < x < -9.4 and -3.2 < y < 3.2) else 0.0
def visible(ob, f):
    return not ob.hide_render
STAND = {   # actor: frame ranges where it stands/sits on its feet (feet must be planted, not lying/carried)
    "Surgeon1": [(1, 600), (1200, 1710)], "Patient": [(605, 790)], "Surgeon2": [(850, 1300)], "Nurse": [(1, 600), (766, 1100)],
    "PanelA": [(1231, 1710)], "PanelB": [(1231, 1710)], "PanelC": [(1231, 1710)]}
GRASP = [  # (actor, side, prop object, local grip point, frame range)
    ("Surgeon1", "R", "ArgonPen_OR", V((0, 0, 0.07)), (1, 300)),
    ("Surgeon1", "R", "NeedleDriver", V((0, 0, 0.115)), (330, 440)),
    ("PanelA", "R", "Gavel", V((0, -0.16, 0)), (1480, 1710)),
    ("PanelB", "R", "Stamp", V((0, 0, 0.12)), (1560, 1625)),
    ("Patient", "L", "Mug", V((0, 0, 0.05)), (605, 660)),
    ("GloveHands", "R", "ArgonPen_Studio", V((0, 0, 0.08)), (150, 290)),
]
DESKS = [("lectern", (-7.4, -6.8, -0.35, 0.35), 1.12), ("panel desk", (-10.45, -9.55, -2.6, 2.6), DAIS_H + 0.785)]
TRANSIT = [(132, 152), (270, 294), (628, 650), (768, 790), (1052, 1080), (1178, 1196), (1244, 1260)]   # planned dives / wall fly-throughs
ROOMS = [("OR", -3.5, 3.5, -3.5, 3.5, 3.0), ("HOME", 3.8, 9.8, -3.0, 3.0, 2.7), ("HEAR", -12.0, -3.8, -3.5, 3.5, 3.2), ("COR", -0.2, 3.4, 3.6, 7.2, 2.8)]
STUDIO = (V((0, 0, -6.0)), 4.5)
rigs = {n: bpy.data.objects[n] for n in STAND}
rest_ankle = {n: {s: r.data.bones["foot." + s].head_local.z for s in "LR"} for n, r in rigs.items()}
rep = []; worst = {}
def note(kind, f, msg, val):
    rep.append("%5d %-10s %s" % (f, kind, msg))
    k = (kind, msg.split(":")[0]); worst[k] = max(worst.get(k, (0, 0)), (val, f))
prev = {}
cam = sc.camera
bodies = [r for r in bpy.data.objects if r.type == 'ARMATURE']
for f in range(1, sc.frame_end + 1, STEP):
    sc.frame_set(f)
    for n, r in rigs.items():
        body = bpy.data.objects.get(n + ".body")
        if not any(a_ <= f <= b_ for a_, b_ in STAND[n]) or (body is not None and body.hide_render):
            for s in "LR": prev.pop((n, s), None)
            continue
        for s in "LR":
            pb = r.pose.bones["foot." + s]; p = r.matrix_world @ pb.head
            g = ground(p.x, p.y); dz = p.z - g - rest_ankle[n][s]
            key = (n, s)
            if key in prev:
                pf, pp = prev[key]
                sp = (p - pp).to_2d().length / ((f - pf) / 60.0)
                if abs(dz) < 0.015 and abs(pp.z - p.z) < 0.003 and 0.08 < sp:
                    note("SLIDE", f, "%s foot.%s: %.2f m/s" % (n, s, sp), sp)
            prev[key] = (f, p.copy())
            if dz < -0.03:
                note("SINK", f, "%s foot.%s: %.3f m" % (n, s, dz), -dz)
            if 0.04 < dz and n not in ("Surgeon2", "Nurse", "Patient"):
                note("HOVER", f, "%s foot.%s: %.3f m" % (n, s, dz), dz)
    for n, s, prop, loc, (f0, f1) in GRASP:
        if not f0 <= f <= f1:
            continue
        r = bpy.data.objects[n]; po = bpy.data.objects[prop]
        hand = r.matrix_world @ r.pose.bones["finger3-1." + s].head
        d = (hand - po.matrix_world @ loc).length
        if d > 0.07:
            note("GRASP", f, "%s %s hand to %s: %.3f m" % (n, s, prop, d), d)
    for n in ("Surgeon1", "PanelA", "PanelB", "PanelC"):
        r = bpy.data.objects[n]
        for s in "LR":
            for bn in ("wrist.", "finger3-3."):
                p = r.matrix_world @ r.pose.bones[bn + s].head
                for dn, (x0, x1, y0, y1), top in DESKS:
                    if x0 < p.x < x1 and y0 < p.y < y1 and p.z < top - 0.015:
                        note("THROUGH", f, "%s %s%s into %s: %.3f m" % (n, bn, s, dn, top - p.z), top - p.z)
    c = cam.matrix_world.translation
    if not any(a_ <= f <= b_ for a_, b_ in TRANSIT):
        inside = any(x0 + 0.02 < c.x < x1 - 0.02 and y0 + 0.02 < c.y < y1 - 0.02 and 0.02 < c.z < h - 0.02 for _, x0, x1, y0, y1, h in ROOMS)
        in_studio = (c - STUDIO[0]).length < STUDIO[1] - 0.05
        if not (inside or in_studio):
            note("CAMERA", f, "camera outside every room (inside a wall/floor): %s" % (tuple(round(v, 2) for v in c),), 1)
        for r in bodies:
            if r.name == "GloveHands":
                continue
            for bn in ("head", "spine02", "spine04"):
                p = r.matrix_world @ r.pose.bones[bn].head
                if (c - p).length < 0.10 and any(not o.hide_render for o in r.children if o.type == 'MESH'):
                    note("CAMERA", f, "camera inside %s (%s): %.2f m" % (r.name, bn, (c - p).length), 1)
with open(OUT, "w") as fh:
    fh.write("SurgeonBrandsLivers contact audit, every %d frames\n\nWORST PER CHECK\n" % STEP)
    for (kind, what), (v, f) in sorted(worst.items()):
        fh.write("  %-8s %-45s worst %.3f at frame %d\n" % (kind, what, v, f))
    fh.write("\nCOUNT %d issues\n\nALL\n" % len(rep) + "\n".join(rep) + "\n")
print("AUDIT", len(rep), OUT)
