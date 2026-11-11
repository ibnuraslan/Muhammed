"""Contact / camera audit for DonationBin.
blender -b anim.blend --python audit.py -- <report.txt> [step]
Checks every <step> frames (default 2):
  feet   : ankle height above the surface below (asphalt or clothes pile) for standing/walking humans -> hover (> 3 cm) / sink (< -3 cm)
  hands  : finger tips inside the 12 mm bin walls, the flap plate or the cut panel (penetration)
  lying  : woman pelvis below the pile surface (sink into clothes)
  camera : camera inside steel (distance to the bin shell / flap / panel < 1.5 cm) or below the ground"""
import sys, math
import bpy
from mathutils import Vector
a = sys.argv[sys.argv.index("--") + 1:]
OUT = a[0]; STEP = int(a[1]) if len(a) > 1 else 2
sc = bpy.context.scene; dg = bpy.context.evaluated_depsgraph_get()
PILE = bpy.data.objects["Pile"]; FY = sc["bin_front_y"]
def gz(x, y):
    if -0.73 < x < 0.73 and -0.58 < y < 0.58:
        hit, loc, n, i = PILE.ray_cast(Vector((x, y, 3)), Vector((0, 0, -1)))
        if hit: return loc.z
    return 0.0
# windows where a character is meant to be off the ground (airborne, lying, crouched on the pile with body-relative feet)
FREE = {"Woman": [(156, 300), (290, 470), (640, 670), (1200, 1250), (1495, 2100), (2095, 2150)], "Shover": [], "Passerby": [], "FireA": [], "FireB": []}
PASS = [(268, 290), (520, 545), (955, 975), (1395, 1412), (1560, 1590), (1862, 1885), (2080, 2100)]   # planned camera pass-throughs
steel = [bpy.data.objects[n] for n in ("BinShell", "Flap", "CutPanel", "BinLiner")]
lines = []; worst = {}
def note(kind, f, msg, v):
    lines.append("%-7s f%4d %s %.3f" % (kind, f, msg, v))
    k = (kind, msg.split()[0]); worst[k] = max(worst.get(k, 0), abs(v))
def inside(o, f, p):
    return any(f0 <= f <= f1 for f0, f1 in FREE.get(o, []))
def hidden(o):
    return bpy.data.objects[o].hide_render
for f in range(1, sc.frame_end + 1, STEP):
    sc.frame_set(f)
    for nm in ("Woman", "Shover", "Passerby", "FireA", "FireB"):
        if hidden(nm): continue
        R = bpy.data.objects[nm]; P = R.pose.bones; M = R.matrix_world; B = R.data.bones
        if not inside(nm, f, None):
            for s in "LR":
                ank = M @ P["foot." + s].head; rest = B["foot." + s].head_local.z
                d = ank.z - gz(ank.x, ank.y) - rest
                if d > 0.03 and nm != "FireA": note("feet", f, "%s hover %s" % (nm, s), d)
                if d < -0.03: note("feet", f, "%s sink %s" % (nm, s), d)
        for s in "LR":
            for i in (2, 3, 4):
                tip = M @ P["finger%d-3.%s" % (i, s)].tail
                for o in steel:
                    if o.hide_render: continue
                    ev = o.evaluated_get(dg); inv = o.matrix_world.inverted()
                    ok, cp, n, idx = ev.closest_point_on_mesh(inv @ tip)
                    if ok:
                        d = (o.matrix_world @ cp - tip).length
                        if d < 0.004 and (inv @ tip - cp).dot(n) < 0:
                            note("hands", f, "%s %s tip%d in %s" % (nm, s, i, o.name), d)
        if nm == "Woman" and 290 <= f <= 2090:
            pel = M @ P["root"].head
            d = pel.z - gz(pel.x, pel.y)
            if d < 0.06: note("lying", f, "Woman pelvis_into_pile", d)
    cam = sc.camera; cp_ = cam.matrix_world.translation
    if cp_.z < 0.05: note("camera", f, "below_ground", cp_.z)
    if not any(f0 <= f <= f1 for f0, f1 in PASS):
        for o in steel:
            if o.hide_render: continue
            ev = o.evaluated_get(dg); inv = o.matrix_world.inverted()
            ok, cp, n, idx = ev.closest_point_on_mesh(inv @ cp_)
            if ok:
                d = (o.matrix_world @ cp - cp_).length
                if d < 0.015: note("camera", f, "in_steel %s" % o.name, d)
open(OUT, "w").write("AUDIT DonationBin (step %d)\nWORST: %s\nCOUNT %d\n" % (STEP, {"%s/%s" % k: round(v, 3) for k, v in worst.items()}, len(lines)) + "\n".join(lines) + "\n")
print("AUDIT", len(lines), worst)
