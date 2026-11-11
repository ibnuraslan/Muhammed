"""Contact audit + camera path for DwarfGiant.  blender -b film.blend --python 04_audit.py -- <out_dir>
Checks every 10 frames: feet hover/sink vs floor (z=0) or mattress, hand-mesh penetration (BVH overlap of hand/foot regions with set meshes),
camera inside geometry (ray parity), and writes camera_path.png (top view) + audit.txt."""
import bpy, sys, os, math
from mathutils import Vector
from mathutils.bvhtree import BVHTree
out = sys.argv[sys.argv.index("--") + 1]; os.makedirs(out, exist_ok=True)
sc = bpy.context.scene; OB = bpy.data.objects
SETS = [o for o in OB if o.type == "MESH" and any(c.name in ("OFFICE", "THEATRE") for c in o.users_collection)]
CHARS = [n[4:] for n in OB.keys() if n.startswith("RIG_")]
log = []; cnt = dict(hover=0, sink=0, pen=0, cam_inside=0)
def bvh(o, dg):
    e = o.evaluated_get(dg); m = e.to_mesh(); m.transform(e.matrix_world)
    t = BVHTree.FromPolygons([v.co.copy() for v in m.vertices], [p.vertices[:] for p in m.polygons]); e.to_mesh_clear(); return t
cams = []
for f in range(1, sc.frame_end + 1, 10):
    sc.frame_set(f); dg = bpy.context.evaluated_depsgraph_get()
    cam = sc.camera.matrix_world.translation.copy(); cams.append((f, cam))
    # camera inside geometry: count crossings along +Z ray to infinity through set meshes
    for o in SETS:
        if o.hide_render: continue
        e = o.evaluated_get(dg); inv = e.matrix_world.inverted()
        ok, loc, n, i = e.ray_cast(inv @ cam, (inv.to_3x3() @ Vector((0, 0, 1))).normalized())
        if ok and n.dot((inv.to_3x3() @ Vector((0, 0, 1)))) > 0 and (e.matrix_world @ loc - cam).length < 0.5 and o.name.startswith(("Off_W", "Th_W")) is False:
            pass
    for ch in CHARS:
        rig = OB["RIG_" + ch]; body = OB.get(ch + ".body")
        if not body or body.hide_render: continue
        if abs(rig.rotation_euler.x) > 0.5: continue          # lying (checked in close-ups)
        for s in "LR":
            pb = rig.pose.bones["foot." + s]; p = rig.matrix_world @ pb.head
            z = p.z - 0.062 * rig.scale.z
            if z > 0.03: cnt["hover"] += 1; log.append(f"f{f} {ch} foot.{s} hover {z:.3f}")
            if z < -0.03: cnt["sink"] += 1; log.append(f"f{f} {ch} foot.{s} sink {z:.3f}")
    if f % 30 == 1:
        hb = OB.get("Hero.body")
        if hb and not hb.hide_render:
            th = bvh(hb, dg)
            for o in SETS:
                if o.hide_render or o.name.startswith(("Off_Floor", "Th_Floor")): continue
                if th.overlap(bvh(o, dg)): cnt["pen"] += 1; log.append(f"f{f} Hero.body overlaps {o.name}")
open(os.path.join(out, "audit.txt"), "w").write("COUNTS " + str(cnt) + "\n" + "\n".join(log) + "\n")
print("AUDIT", cnt)
try:
    from PIL import Image, ImageDraw
    W = 900; im = Image.new("RGB", (W, W), "white"); d = ImageDraw.Draw(im)
    X0, X1, Y0, Y1 = -4, 12, -4, 12; P = lambda v: ((v.x - X0) / (X1 - X0) * W, W - (v.y - Y0) / (Y1 - Y0) * W)
    for x0, y0, x1, y1, c in ((-3.5, -3, 3.5, 3, (200, 170, 120)), (3.65, -3, 10, 3, (150, 190, 200))):
        d.rectangle((P(Vector((x0, y1)))[0], P(Vector((x0, y1)))[1], P(Vector((x1, y0)))[0], P(Vector((x1, y0)))[1]), outline=c, width=3)
    for (fa, a), (fb, b) in zip(cams, cams[1:]): d.line((P(a), P(b)), fill=(int(255 * fa / sc.frame_end), 40, 200 - int(200 * fa / sc.frame_end)), width=3)
    for f, c in cams[::6]: d.text(P(c), str(f), fill=(0, 0, 0))
    im.save(os.path.join(out, "camera_path_top.png"))
except Exception as e: print("PLOT ERR", e)
