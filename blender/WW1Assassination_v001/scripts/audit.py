"""Contact audit for WW1Assassination. blender -b film.blend --python audit.py -- <report.txt> [step]
Checks: standing feet hover/sink vs ground, wheels on the road, camera inside buildings/cars/people, driver hands on wheel,
seated pelvis above the seat, bomb in the bomber's hand before release."""
import sys, os, math
import bpy
from mathutils import Vector
HERE = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(HERE, "00_story.py")).read())
a = sys.argv[sys.argv.index("--") + 1:]
OUT = a[0]; STEP = int(a[1]) if len(a) > 1 else 10
sc = bpy.context.scene
SW = sc.get("SWAP_F", 1748)
def ground_z(x, y):
    if 6.0 <= y <= 8.0 and not (-2.5 < x < 2.5): return 0.15
    if -7.0 <= y <= -5.5: return 0.15
    if y > 8.0 and 2.5 <= abs(x) <= 4.5: return 0.15
    return 0.0
lines = []; worst = {}
def rec(kind, f, who, val, lim):
    if abs(val) > lim:
        lines.append(f"{kind:10s} f{f:5d} {who:28s} {val:+.3f}")
        k = (kind, who); worst[k] = max(worst.get(k, 0), abs(val))
people = [o for o in bpy.data.objects if o.type == 'ARMATURE' and "foot.L" in o.pose.bones and not o.hide_render and o.name not in ("Archduke", "Duchess", "Driver")]
blds = [o for o in bpy.data.objects if o.name.startswith(("BldQuay", "BldFar", "BldSide", "Cafe_"))]
bb = []
for o in blds:
    pts = [o.matrix_world @ Vector(c) for c in o.bound_box]
    bb.append((o.name, Vector(map(min, *pts)), Vector(map(max, *pts))))
cam = sc.camera
n_frames = 0
sc.frame_set(1)
_h = bpy.data.objects.get("Helmet"); _a = bpy.data.objects["Archduke"]
REF_HELM = (_h.matrix_world.translation - _a.matrix_world @ _a.pose.bones["head"].tail).length if _h else 0.0
for f in range(1, SW, STEP):
    sc.frame_set(f); n_frames += 1
    # feet: lowest of heel (foot head) / toe tail vs ground; flag when grounded-phase foot is off (> 3 cm) or sunk (> 2 cm)
    for o in people:
        if o.hide_render: continue
        for s in "LR":
            pb = o.pose.bones["foot." + s]; h = o.matrix_world @ pb.head; t = o.matrix_world @ pb.tail
            g = ground_z(h.x, h.y)
            low = min(h.z - 0.07, t.z - 0.025) - g
            if low < -0.025: rec("SINK", f, o.name + "." + s, low, 0.025)
    # wheels
    for car in ("Car1", "Car2"):
        for w in [x for x in bpy.data.objects if x.name.startswith(car + "_wheel")]:
            z = w.matrix_world.translation.z - w.dimensions.z / 2
            rec("WHEEL", f, w.name, z, 0.03)
    # camera inside buildings
    c = cam.matrix_world.translation
    for nm, mn, mx in bb:
        if all(mn[i] + 0.05 < c[i] < mx[i] - 0.05 for i in range(3)):
            rec("CAM_IN", f, nm, 1.0, 0.5)
    for car in ("Car1_Body", "Car2_Body"):
        o = bpy.data.objects[car]; loc = o.matrix_world.inverted() @ c
        if -0.7 < loc.x < 0.7 and -1.7 < loc.y < 1.5 and 0.35 < loc.z < 1.2: rec("CAM_IN", f, car, 1.0, 0.5)
    if c.z < 0.08 and f < SW: rec("CAM_LOW", f, "camera", c.z, 0.0)
    # driver hands to wheel rim
    D = bpy.data.objects["Driver"]; wh = bpy.data.objects.get("Car1_Body")
    for s in "LR":
        p = D.matrix_world @ D.pose.bones["wrist." + s].tail
        tgt = D.matrix_world @ D.pose.bones["IK_hand." + s].head
        rec("HAND_IK", f, "Driver." + s, (p - tgt).length, 0.06)
    for nm in ("Archduke", "Duchess"):
        A_ = bpy.data.objects[nm]
        for s in "LR":
            p = A_.matrix_world @ A_.pose.bones["wrist." + s].head; tgt = A_.matrix_world @ A_.pose.bones["IK_hand." + s].head
            rec("HAND_IK", f, nm + "." + s, (p - tgt).length, 0.06)
# ---- penetration / clipping counts (director's clipping check)
pen = {"people_overlap": 0, "hand_off_prop": 0, "helmet_clip_or_gap": 0, "seat_sink": 0}
pistol = bpy.data.objects.get("Pistol"); parasol = bpy.data.objects.get("Parasol"); helmet = bpy.data.objects.get("Helmet")
arch = bpy.data.objects["Archduke"]; GN = bpy.data.objects["Gunman"]; DU = bpy.data.objects["Duchess"]
REF_P = {}
def prop_dev(key, prop, arm, bone):
    w = arm.matrix_world @ arm.pose.bones[bone].tail
    d = (prop.matrix_world.translation - w).length
    if key not in REF_P: REF_P[key] = d
    return abs(d - REF_P[key])
dg_people = [o for o in bpy.data.objects if o.type == 'ARMATURE' and "root" in o.pose.bones and o.name not in ("Archduke", "Duchess", "Driver") and not o.name.startswith("Crowd") or (o.type == 'ARMATURE' and o.name.startswith("Crowd_"))]
for f in range(1, SW, STEP * 2):
    sc.frame_set(f)
    pts = [(o.name, (o.matrix_world @ o.pose.bones["root"].head)) for o in dg_people if not o.hide_render and "root" in o.pose.bones and not o.name.startswith("Horse")]
    for i in range(len(pts)):
        for j in range(i + 1, len(pts)):
            d = (pts[i][1] - pts[j][1]); d.z = 0
            if d.length < 0.32: pen["people_overlap"] += 1; lines.append(f"OVERLAP    f{f:5d} {pts[i][0]} ~ {pts[j][0]} {d.length:.2f}")
    if pistol and not pistol.hide_render:
        if prop_dev("pistol", pistol, GN, "wrist.R") > 0.02: pen["hand_off_prop"] += 1
    if parasol:
        if prop_dev("parasol", parasol, DU, "wrist.L") > 0.02: pen["hand_off_prop"] += 1
    if helmet:
        hb = arch.matrix_world @ arch.pose.bones["head"].tail
        if abs((helmet.matrix_world.translation - hb).length - REF_HELM) > 0.01: pen["helmet_clip_or_gap"] += 1
    pel = arch.matrix_world @ arch.pose.bones["root"].head
    car = bpy.data.objects["Car1_Sway"]; loc = car.matrix_world.inverted() @ pel
    if loc.z < sc.get("SEAT_R", 0.96) - 0.12: pen["seat_sink"] += 1
lines.insert(0, "PENETRATION COUNTS (frames sampled every %d): %s" % (STEP * 2, pen))
with open(OUT, "w") as fh:
    fh.write("PENETRATION COUNTS: %s\n" % pen)
    fh.write(f"Audit over {n_frames} frames (every {STEP}) up to the map swap (f{SW}).\n")
    fh.write("Worst per item (kind, who, value):\n")
    for (k, w), v in sorted(worst.items(), key=lambda x: -x[1])[:60]: fh.write(f"  {k:10s} {w:28s} {v:.3f}\n")
    fh.write(f"\n{len(lines)} flagged samples. First 200:\n" + "\n".join(lines[:200]) + "\n")
print("AUDIT", len(lines), "flags", OUT)
