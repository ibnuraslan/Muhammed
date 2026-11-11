"""Contact + camera audit. blender -b work/film.blend --python scripts/04_audit.py -- audit.txt
Checks every 5 frames: shoe soles vs bedroom floor (hover/sink), grip (wrists on the box, fingertips not inside it),
box held against the chest (no gap, no penetration), camera inside or within 2 mm of a visible mesh."""
import sys, bpy
from mathutils import Vector as V
OUT = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene; FZ = 0.25
rig = bpy.data.objects["Gamer"]; shoes = bpy.data.objects["Gamer.shoes02"]; body = bpy.data.objects["Gamer.body"]
broot = bpy.data.objects["BoxRoot"]; cam = sc.camera
W2, H2, D2 = 0.15, 0.19, 0.07
lines = []; worst = {}; CAMMIN = (0, 9.0)
def note(k, f, v, bad):
    if k not in worst or abs(v) > abs(worst[k][1]): worst[k] = (f, v)
    if bad: lines.append("FAIL %-18s f%4d %.4f" % (k, f, v))
skip = ("Dust", "Grass_", "EnergyRing", "Bullet_trail", "Dust_motes", "Win_glass", "Curtain")
for f in sorted(set(list(range(1, sc.frame_end + 1, 5)) + list(range(160, 230)))):
    sc.frame_set(f); dg = bpy.context.evaluated_depsgraph_get()
    # soles: lowest shoe vertex per side
    me = shoes.evaluated_get(dg).to_mesh(); M = shoes.matrix_world
    for s, sgn in (("L", 1), ("R", -1)):
        zs = [(M @ v.co).z for v in me.vertices if sgn * (M @ v.co).x > 0]
        z = min(zs) - FZ; note("sole_" + s, f, z, z > 0.01 or z < -0.01)
    shoes.evaluated_get(dg).to_mesh_clear()
    Bi = broot.matrix_world.inverted()
    for s in "LR":
        pb = rig.pose.bones["finger3-3." + s]; tip = rig.matrix_world @ pb.tail
        l = Bi @ tip
        inside = abs(l.x) < W2 - 0.002 and abs(l.y) < D2 - 0.002 and abs(l.z) < H2 - 0.002
        note("fingertip_in_box_" + s, f, 1.0 if inside else 0.0, inside)
        wr = Bi @ (rig.matrix_world @ rig.pose.bones["wrist." + s].head)
        gap = abs(wr.x) - W2
        note("wrist_gap_" + s, f, gap, gap > 0.05 or gap < 0.0)
    # chest contact: box back face vs body surface along the box normal
    back = broot.matrix_world @ V((0, D2, 0.0)); nrm = (broot.matrix_world.to_3x3() @ V((0, 1, 0))).normalized()
    be = body.evaluated_get(dg); Bm = be.matrix_world.inverted()
    hit, loc, n_, i = be.closest_point_on_mesh(Bm @ back)
    if hit:
        d = ((be.matrix_world @ loc) - back).dot(nrm); note("box_chest_gap", f, d, (d > 0.06 or d < -0.03) and f < 1355)
    # camera near/inside geometry
    c = cam.matrix_world.translation; best = (9, "")
    for o in bpy.data.objects:
        if o.type != "MESH" or o.hide_render or o.name.startswith(skip): continue
        mw = o.matrix_world; bb = [mw @ V(p) for p in o.bound_box]
        lo = V([min(p[k] for p in bb) for k in range(3)]); hi = V([max(p[k] for p in bb) for k in range(3)])
        if any(c[k] < lo[k] - 0.3 or c[k] > hi[k] + 0.3 for k in range(3)): continue
        oe = o.evaluated_get(dg); mi = mw.inverted()
        if len(o.data.polygons) == 0: continue
        try: ok, p, n, _ = oe.closest_point_on_mesh(mi @ c)
        except RuntimeError: continue
        if not ok: continue
        d = (mw @ p - c).length; ins = (mi @ c - p).dot(n) < 0
        if ins and d < 0.05 and o.name.startswith(("Wall_", "Box_", "Room_", "Page_", "Artbook", "Gamer")) and not o.name.endswith("_xp"):
            d = -d
        if abs(d) < abs(best[0]): best = (d, o.name)
    note("camera_clearance", f, best[0], best[0] < 0.002)
    if best[0] < CAMMIN[1]: CAMMIN = (f, best[0])
    if best[0] < 0.002: lines[-1] += "  " + best[1]
rep = ["AUDIT GameBoxBullet  frames 1-%d step 5" % sc.frame_end, ""]
rep += ["worst %-22s f%4d  %+.4f" % (k, f, v) for k, (f, v) in sorted(worst.items()) if k != "camera_clearance"]
rep += ["min   camera_clearance       f%4d  %+.4f m" % CAMMIN]
rep += ["", "%d failures" % len(lines)] + lines[:200]
open(OUT, "w").write("\n".join(rep)); print("\n".join(rep[:40]))
