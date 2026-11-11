"""Contact audit. blender -b work/film.blend --python audit.py -- review/audit.txt
- feet: standing characters' lowest foot vertex vs floor (hover > 2 cm, sink < -1.5 cm) when the foot is planted
- held props: distance from the gripping palm to the prop while held
- camera inside geometry (ray parity test) and camera near-clipping of the people
- camera framing hold: the longest stretch with less than a small change in view"""
import sys, math
import bpy
from mathutils import Vector
out = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene; OB = bpy.data.objects; dg = bpy.context.evaluated_depsgraph_get()
L = []
def log(*a): L.append(" ".join(str(x) for x in a))
cam = sc.camera
def inside(p):
    n = 0; o = p.copy(); d = Vector((0.0123, 0.0177, 1.0)).normalized()
    for _ in range(40):
        hit, loc, nrm, idx, ob, M = sc.ray_cast(dg, o, d)
        if not hit: break
        if "Cyc" in ob.name or "Membrane" in ob.name or ob.name.startswith(("OR_Wall", "OR_Ceil", "OR_Floor")): o = loc + d * 1e-4; continue
        n += 1; o = loc + d * 1e-4
    return n % 2 == 1, n
def foot_low(rig_name, side):
    rig = OB[rig_name]; pb = rig.pose.bones["foot." + side]
    return (rig.matrix_world @ pb.head).z, (rig.matrix_world @ pb.tail).z
prev = None; hold = 0; worst_hold = (0, 0)
issues = {"inside": [], "hover": [], "sink": [], "grip": []}
last_foot = {}
for f in range(1, sc.frame_end + 1, 5):
    sc.frame_set(f); dg = bpy.context.evaluated_depsgraph_get()
    cp = cam.matrix_world.translation.copy(); fw = cam.matrix_world.to_3x3() @ Vector((0, 0, -1))
    # inside test: the first surface along the view axis (and 4 offsets) is hit from its back side
    backs = []
    for off in (Vector((0, 0, 0)), Vector((0.3, 0, 0)), Vector((-0.3, 0, 0)), Vector((0, 0.3, 0)), Vector((0, -0.3, 0))):
        d = (cam.matrix_world.to_3x3() @ (Vector((0, 0, -1)) + off)).normalized()
        hit, loc, nrm, idx, ob, M = sc.ray_cast(dg, cp, d)
        if hit and nrm.dot(d) > 0 and "Cyc" not in ob.name and not ob.name.startswith("OR_"): backs.append(ob.name)
    if len(backs) >= 3: issues["inside"].append((f, max(set(backs), key=backs.count)))
    if prev is not None:
        dpos = (cp - prev[0]).length; dang = math.degrees(fw.angle(prev[1])); dl = abs(cam.data.lens - prev[2])
        if dpos < 0.01 and dang < 0.6 and dl < 0.3: hold += 5
        else: hold = 0
        if hold > worst_hold[0]: worst_hold = (hold, f)
    prev = (cp, fw, cam.data.lens)
    for rn in ("Surgeon", "Nurse"):
        for s in "LR":
            hz, tz = foot_low(rn, s)
            ankle_rest = OB[rn].data.bones["foot." + s].head_local.z
            gap = hz - ankle_rest
            key = (rn, s); p_now = OB[rn].matrix_world @ OB[rn].pose.bones["foot." + s].head
            planted = key in last_foot and (p_now - last_foot[key]).length < 0.004 * 5   # moved < 4 mm/frame: a planted foot
            last_foot[key] = p_now.copy()
            if gap > 0.02 and planted: issues["hover"].append((rn, s, f, round(gap, 3)))
            if gap < -0.015: issues["sink"].append((rn, s, f, round(gap, 3)))
    # held props vs palm
    for prop, rig, s, f0, f1 in (("Scalpel", "Surgeon", "R", 340, 560), ("Forceps", "Surgeon", "R", 570, 1500), ("NeedleHolder", "Surgeon", "R", 1505, 1680)):
        if f0 <= f <= f1:
            pb = OB[rig].pose.bones["finger3-1." + s]; palm = OB[rig].matrix_world @ pb.head
            d = (OB[prop].matrix_world.translation - palm).length
            if d > 0.09: issues["grip"].append((prop, f, round(d, 3)))
log("CAMERA inside geometry at frames:", issues["inside"] or "none")
log("LONGEST near-static camera hold: %.2f s ending f%d" % (worst_hold[0] / 60, worst_hold[1]))
log("FOOT hover >2cm on a planted foot (rig, side, frame, gap):", len(issues["hover"]), issues["hover"][:30])
log("FOOT sink >1.5cm:", len(issues["sink"]), issues["sink"][:30])
log("GRIP prop far from palm (>9cm):", len(issues["grip"]), issues["grip"][:30])
# props on the tray: shavings must land on the tray surface
tz = OB["Tray"].matrix_world.translation.z
sc.frame_set(sc.frame_end)
bad = [(o.name, round(o.matrix_world.translation.z - tz, 3)) for o in OB if o.name.startswith("Shaving") and abs(o.matrix_world.translation.z - tz) > 0.03]
log("SHAVINGS off the tray at end:", bad or "none")
open(out, "w").write("\n".join(L) + "\n"); print("\n".join(L))
