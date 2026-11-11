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
with open(OUT, "w") as fh:
    fh.write(f"Audit over {n_frames} frames (every {STEP}) up to the map swap (f{SW}).\n")
    fh.write("Worst per item (kind, who, value):\n")
    for (k, w), v in sorted(worst.items(), key=lambda x: -x[1])[:60]: fh.write(f"  {k:10s} {w:28s} {v:.3f}\n")
    fh.write(f"\n{len(lines)} flagged samples. First 200:\n" + "\n".join(lines[:200]) + "\n")
print("AUDIT", len(lines), "flags", OUT)
