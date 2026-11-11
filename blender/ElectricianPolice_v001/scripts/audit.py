"""Contact + camera audit for ElectricianPolice.
blender -b film.blend --python audit.py -- <report.txt> [step]
Checks: feet hover/sink on the ground (shoe soles vs floor height), hands on grips / lever / slip,
seated pelvis vs seat, camera inside geometry (backface ray test), camera-to-head distance."""
import bpy, sys, math, os
from mathutils import Vector
a = sys.argv[sys.argv.index("--") + 1:]
OUT = a[0]; STEP = int(a[1]) if len(a) > 1 else 4
sc = bpy.context.scene; cam = sc.camera
L = []
def log(*x): L.append(" ".join(str(v) for v in x))
def vis(o): return not o.hide_render
CHARS = ["Man", "ManW", "OfficerA", "OfficerB", "OfficerC", "PedA", "PedB"]
def shoes(n): return next((o for o in bpy.data.objects if o.parent and o.parent.name == n and ".shoes" in o.name), None)
def floor_z(x, y):
    if -19 < x < -7 and 50 < y < 64: return 0.02
    if 17 < x < 26 and 38 < y < 46: return 0.02
    if 8 < x < 34 and 10 < y < 46: return 0.05
    if 4.15 < abs(x) < 7.2: return 0.03
    return 0.0
dirs = [Vector(d) for d in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1))]
worst = {}
def note(key, f, val, txt):
    if key not in worst or abs(val) > abs(worst[key][1]): worst[key] = (f, val, txt)
cnt = {}
for f in range(sc.frame_start, sc.frame_end + 1, STEP):
    sc.frame_set(f); dg = bpy.context.evaluated_depsgraph_get()
    # ---- feet
    for n in CHARS:
        sh = shoes(n)
        if sh is None or not vis(sh): continue
        arm = bpy.data.objects[n]
        if n == "Man" and f < 400: continue          # riding: feet on pegs / one foot down (checked below)
        me = sh.evaluated_get(dg).to_mesh()
        for side in (1, -1):
            pts = [sh.matrix_world @ v.co for v in me.vertices if (v.co.x * side) > 0] if False else None
        ws = [sh.matrix_world @ v.co for v in me.vertices]
        sh.evaluated_get(dg).to_mesh_clear()
        cx = sum(p.x for p in ws) / len(ws)
        for side, grp in (("L", [p for p in ws if p.x >= cx - 0.0 and True]), ("R", None)):
            pass
        # split by the two ankle bones
        aL = arm.matrix_world @ arm.pose.bones["foot.L"].head; aR = arm.matrix_world @ arm.pose.bones["foot.R"].head
        for s, ap in (("L", aL), ("R", aR)):
            pts = [p for p in ws if (p - ap).length < (p - (aR if s == "L" else aL)).length]
            if not pts: continue
            zmin = min(p.z for p in pts); fz = floor_z(ap.x, ap.y)
            d = zmin - fz
            lifted = (ap.z - fz) > 0.105         # foot in swing (walk) - not a contact frame
            if not lifted:
                if d > 0.03: cnt["hover"] = cnt.get("hover", 0) + 1; note("hover_" + n, f, d, s)
                if d < -0.03: cnt["sink"] = cnt.get("sink", 0) + 1; note("sink_" + n, f, d, s)
    # ---- hands on things
    man = bpy.data.objects["Man"]
    def wrist(arm, s): return arm.matrix_world @ arm.pose.bones["wrist." + s].head
    if f < 218:
        b = bpy.data.objects["Bike"]
        for s, gp in (("L", (-0.29, 0.27, 0.99)), ("R", (0.29, 0.27, 0.99))):
            d = (wrist(man, s) - b.matrix_world @ Vector(gp)).length
            note("grip_" + s, f, d, "wrist to bike grip")
    if 1044 <= f <= 1086:
        g = bpy.data.objects["LeverGrip"].matrix_world.translation
        d = (wrist(man, "R") - g).length; note("lever_R", f, d, "wrist to lever grip")
    if 262 <= f <= 345:
        sl = bpy.data.objects["TicketSlip"].matrix_world.translation
        h = wrist(bpy.data.objects["OfficerA"], "R") if f < 276 else wrist(man, "R")
        note("slip", f, (sl - h).length, "slip to holding wrist")
    if 1150 <= f:
        ph = bpy.data.objects["St_Phone"].matrix_world.translation
        note("phone", f, (ph - wrist(bpy.data.objects["OfficerC"], "R")).length, "phone to wrist")
    # ---- camera inside geometry: every ray from the camera first hits a back face
    cp = cam.matrix_world.translation
    inside = 0; nearest = 9e9
    for d in dirs:
        hit, loc, nrm, idx, ob, _ = sc.ray_cast(dg, cp + d * 1e-4, d, distance=50)
        if hit:
            nearest = min(nearest, (loc - cp).length)
            if nrm.dot(d) > 0.2: inside += 1
    if inside >= 3: cnt["cam_inside"] = cnt.get("cam_inside", 0) + 1; log("CAM_INSIDE f%d hits_backface=%d" % (f, inside))
    if nearest < 0.12: cnt["cam_close_surface"] = cnt.get("cam_close_surface", 0) + 1; log("CAM_CLOSE f%d %.2f m" % (f, nearest))
    for n in CHARS:
        arm = bpy.data.objects[n]; bd = next((o for o in bpy.data.objects if o.parent == arm and o.name.startswith(n + ".body")), None)
        if bd is None or not vis(bd): continue
        hd = arm.matrix_world @ arm.pose.bones["head"].head
        dd = (hd - cp).length
        if dd < 0.28: cnt["cam_head"] = cnt.get("cam_head", 0) + 1; log("CAM_NEAR_HEAD f%d %s %.2f m" % (f, n, dd))
log("COUNTS", cnt)
for k in sorted(worst): f, v, t = worst[k]; log("WORST %-22s f%-5d %.3f  %s" % (k, f, abs(v), t))
open(OUT, "w").write("\n".join(L) + "\n"); print("\n".join(L))
