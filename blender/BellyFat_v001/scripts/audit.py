"""Contact / penetration / camera audit for BellyFat.
blender -b anim.blend --python audit.py -- <report.txt> [step]
REAL frames (store visible): shoe soles on the floor, planted-foot slide, fingertips inside her body, basket/cans on the floor,
                             shopper hands on the cart handle, camera inside a body or shelf.
MACRO frames (tissue visible): bullet overlapping lobules / fibres / intestines, camera inside the tissue block or lobules.
Camera (all frames): speed continuity (no jumps), framing holds longer than 1.5 s, visibility-swap frames."""
import sys, math, json
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
argv = sys.argv[sys.argv.index("--") + 1:]
OUT = argv[0]; STEP = int(argv[1]) if len(argv) > 1 else 4
sc = bpy.context.scene
SWAP_IN, SWAP_OUT = 154, 1225
issues = {}; stats = {}
def flag(k, f, m): issues.setdefault(k, []).append((f, m))
def stat(k, v): stats.setdefault(k, []).append(v)
root = bpy.data.objects["MacroRoot"]; cam = bpy.data.objects["CAM_Film"]; bul = bpy.data.objects["Bullet"]
W = bpy.data.objects["Woman"]
shoes = {"Woman": "Woman.shoes02", "ShopperA": "ShopperA.shoes03", "ShopperB": "ShopperB.shoes02"}
def ev_mesh_world(o, dg, every=1):
    e = o.evaluated_get(dg); me = e.to_mesh(); mw = o.matrix_world
    pts = [mw @ v.co for v in list(me.vertices)[::every]]; e.to_mesh_clear(); return pts
def bvh_world(o, dg):
    e = o.evaluated_get(dg); me = e.to_mesh(); mw = o.matrix_world
    verts = [mw @ v.co for v in me.vertices]; polys = [tuple(p.vertices) for p in me.polygons]
    e.to_mesh_clear(); return BVHTree.FromPolygons(verts, polys)
def inside(tree, p, d=None):
    """open MPFB meshes: inside = the nearest surface faces away from the point (and it is within 6 cm)"""
    loc, nrm, idx, dist = tree.find_nearest(p)
    return loc is not None and dist < 0.06 and (p - loc).dot(nrm) < 0
woman_foot_ref = {}
real_frames = [f for f in range(1, sc.frame_end + 1, STEP) if f < SWAP_IN or f >= SWAP_OUT]
macro_frames = [f for f in range(SWAP_IN, SWAP_OUT, STEP)]
shelves = [bpy.data.objects[n] for n in ("ShelfL", "ShelfR")]
for f in real_frames:
    sc.frame_set(f); dg = bpy.context.evaluated_depsgraph_get()
    for who, sn in shoes.items():
        pts = ev_mesh_world(bpy.data.objects[sn], dg, 3)
        for side, sel in (("L", lambda p, c: p), ):
            pass
        zmin = min(p.z for p in pts); stat("sole_z_" + who, zmin)
        if zmin > 0.015: flag("FOOT_HOVER", f, "%s lowest sole point %.1f cm above floor" % (who, zmin * 100))
        if zmin < -0.015: flag("FOOT_SINK", f, "%s sole %.1f cm below floor" % (who, -zmin * 100))
    # woman planted-foot slide (both feet planted all film)
    for s in "LR":
        p = W.matrix_world @ W.pose.bones["foot." + s].head
        if s not in woman_foot_ref: woman_foot_ref[s] = p.copy()
        dxy = (p - woman_foot_ref[s]).to_2d().length
        if dxy > 0.01: flag("FOOT_SLIDE", f, "Woman foot.%s moved %.1f cm" % (s, dxy * 100))
    # fingertips inside her body / tee
    body = bvh_world(bpy.data.objects["Woman.body"], dg)
    for s in "LR":
        for k in range(1, 6):
            bn = "finger%d-3.%s" % (k, s)
            if bn not in W.pose.bones: continue
            tip = W.matrix_world @ W.pose.bones[bn].tail
            if inside(body, tip):
                loc, nrm, idx, dist = body.find_nearest(tip)
                if dist > 0.008: flag("FINGER_IN_BODY", f, "Woman %s %.1f cm inside" % (bn, dist * 100))
    # camera inside her body or a shelf
    cp = cam.matrix_world.translation
    if inside(body, cp): flag("CAMERA_INSIDE", f, "camera inside Woman.body")
    for sh in shelves:
        t = bvh_world(sh, dg)
        loc, nrm, idx, dist = t.find_nearest(cp)
        if loc is not None and dist < 0.002: flag("CAMERA_NEAR_SHELF", f, "%.1f mm from %s" % (dist * 1000, sh.name))
    # basket + cans resting
    if f > 170:
        for n in ["Basket", "FallCan0", "FallCan1", "FallCan2"]:
            pts = ev_mesh_world(bpy.data.objects[n], dg)
            zmin = min(p.z for p in pts)
            if abs(zmin) > 0.012: flag("PROP_FLOAT" if zmin > 0 else "PROP_SINK", f, "%s lowest point %.1f cm" % (n, zmin * 100))
    # shopper A hands on the cart handle while pushing
    if f <= 160:
        A = bpy.data.objects["ShopperA"]; cart = bpy.data.objects["Cart"]
        for s, dy in (("L", 0.2), ("R", -0.2)):
            w = A.matrix_world @ A.pose.bones["wrist." + s].head
            hx = cart.matrix_world @ Vector((0.57, -dy, 1.05))
            d = (w - hx).length
            stat("cart_grip_cm", d * 100)
            if d > 0.12: flag("HAND_OFF_CART", f, "ShopperA wrist.%s %.0f cm from the handle" % (s, d * 100))
# ------------------------------------------------------------------ macro
lobs = [o for o in bpy.data.objects if o.name.startswith("M_Lob")]
fibs = [o for o in bpy.data.objects if o.name.startswith("M_MuscleFib")]
guts = [o for o in bpy.data.objects if o.name.startswith("M_Gut") and "Bed" not in o.name]
blocks = [bpy.data.objects[n] for n in ("M_FatBed", "M_Fascia", "M_MuscleBed", "M_GutBed")]
BR = 0.18
layers = [bpy.data.objects[n] for n in ("M_Fabric", "M_Epidermis", "M_Dermis", "M_Fascia", "M_MuscleBed", "M_FatBed", "M_Peritoneum")]
for f in macro_frames:
    sc.frame_set(f); dg = bpy.context.evaluated_depsgraph_get()
    Mi = root.matrix_world.inverted()
    tipL = Mi @ (bul.matrix_world @ Vector((0.6, 0, 0))); baseL = Mi @ (bul.matrix_world @ Vector((0.0, 0, 0)))
    ax = tipL - baseL
    def seg_dist(c):
        t = max(0.0, min(1.0, (c - baseL).dot(ax) / ax.length_squared)); return (c - (baseL + ax * t)).length
    worst = 0.0; wn = None
    for o in lobs:
        c = o.location; r = max(o.scale) * 0.92
        ov = BR + r - seg_dist(c)
        if ov > worst: worst, wn = ov, o.name
    stat("lobule_overlap", worst)
    if worst > 0.12: flag("BULLET_IN_LOBULE", f, "%s overlaps the bullet by %.2f u (%.1f mm)" % (wn, worst, worst * 25))
    # fibres: the parted shape key moves the front rows aside; sample their evaluated verts near the axis
    for o in fibs:
        if abs(o.location.x - tipL.x) > 0.5: continue
        pts = [Mi @ p for p in ev_mesh_world(o, dg, 2)]
        dmin = min(seg_dist(p) for p in pts)
        if dmin < BR - 0.04: flag("BULLET_IN_FIBRE", f, "%s %.2f u inside" % (o.name, BR - dmin))
    for o in layers:
        pts = [Mi @ p for p in ev_mesh_world(o, dg, 1)]
        def inside_bullet(p):
            u = (p - baseL).dot(ax) / ax.length_squared
            if u < 0 or u > 1: return False
            rr = BR if u < 0.55 else BR * math.sqrt(max(0.0, 1 - ((u - 0.55) / 0.45) ** 2))
            return (p - (baseL + ax * u)).length < rr - 0.02
        n_in = sum(1 for p in pts if inside_bullet(p))
        if n_in: flag("BULLET_IN_LAYER", f, "%s: %d verts inside the bullet" % (o.name, n_in))
    for o in guts:
        pts = [Mi @ p for p in ev_mesh_world(o, dg, 4)]
        dmin = min(seg_dist(p) for p in pts)
        stat("gut_gap_mm", (dmin - BR) * 25)
        if dmin < BR: flag("BULLET_HITS_ORGAN", f, "%s %.2f u" % (o.name, dmin - BR))
    # camera inside tissue
    cl = Mi @ cam.matrix_world.translation
    if cl.y < 0.05 and -3.6 < cl.z < 3.6 and -0.1 < cl.x < 8.4: flag("CAMERA_INSIDE", f, "camera inside the tissue block (local %s)" % (tuple(round(v, 2) for v in cl),))
    for o in lobs:
        if (cl - o.location).length < max(o.scale) * 1.05: flag("CAMERA_INSIDE", f, "camera inside %s" % o.name)
    stat("cam_y_local", cl.y)
# ------------------------------------------------------------------ camera continuity and holds (all frames, every frame)
pos = []; fwd = []
for f in range(1, sc.frame_end + 1):
    sc.frame_set(f); M = cam.matrix_world; Mi = root.matrix_world.inverted()
    pos.append((Mi @ M.translation, M.translation * 40.0))
    fwd.append((M.to_3x3() @ Vector((0, 0, -1))).normalized())
# speed in the macro frame once the camera is within 30 cm of the hole, else world (x40 so both are in macro units)
sp = [((pos[i][0] - pos[i - 1][0]) if pos[i][0].length < 12 else (pos[i][1] - pos[i - 1][1])).length * 60 for i in range(1, len(pos))]
pos = [p[1] if p[0].length >= 12 else p[0] for p in pos]
for i in range(2, len(sp)):
    a, b = sp[i - 1], sp[i]
    if max(a, b) > 1.0 and max(a, b) / max(1e-6, min(a, b)) > 2.5 and abs(a - b) > 2.0:
        flag("CAMERA_SPEED_JUMP", i + 1, "%.1f -> %.1f u/s" % (a, b))
for i in range(0, len(fwd) - 90, 15):
    ang = max(math.degrees(fwd[i].angle(fwd[j])) for j in range(i, i + 90))
    mv = max((pos[j] - pos[i]).length for j in range(i, i + 90))
    if ang < 6 and mv < 0.5: flag("FRAMING_HOLD", i + 1, "1.5 s with < 6 deg turn and < 0.5 u travel")
with open(OUT, "w") as fh:
    fh.write("BellyFat audit, step %d, real frames %d, macro frames %d\n\n" % (STEP, len(real_frames), len(macro_frames)))
    for k in ("FOOT_HOVER", "FOOT_SINK", "FOOT_SLIDE", "FINGER_IN_BODY", "CAMERA_INSIDE", "CAMERA_NEAR_SHELF", "PROP_FLOAT", "PROP_SINK",
              "HAND_OFF_CART", "BULLET_IN_LOBULE", "BULLET_IN_FIBRE", "BULLET_IN_LAYER", "BULLET_HITS_ORGAN", "CAMERA_SPEED_JUMP", "FRAMING_HOLD"):
        v = issues.get(k, [])
        fh.write("%-18s %4d%s\n" % (k, len(v), ("   e.g. " + "; ".join("f%d %s" % x for x in v[:4])) if v else ""))
        if v: fh.write("%18s frames %s\n" % ("", sorted(set(x[0] for x in v))))
    fh.write("\nstats\n")
    for k, v in stats.items():
        fh.write("  %-16s min %.3f  max %.3f\n" % (k, min(v), max(v)))
print(open(OUT).read())
