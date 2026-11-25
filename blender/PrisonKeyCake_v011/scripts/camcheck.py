"""Camera audit: blender -b film.blend --python camcheck.py -- out.txt [step] [f0] [f1]
Per frame: a 7x12 ray grid from the camera. Reports the object covering most of the frame and how near it is,
which faces (eyes of Pris/Vis/Smith) are in frame AND unoccluded, and flags:
  NEAR   an object nearer than 0.25 m covers > 35 % of the frame (lens blocker / camera in a body)
  WALL   > 70 % of the frame is one wall/floor/ceiling (empty frame)
  NOFACE no face visible (fine on a planned macro; listed so the plan can be checked)"""
import bpy, sys
from mathutils import Vector
from collections import Counter
a = sys.argv[sys.argv.index("--") + 1:]
out = a[0]; step = int(a[1]) if len(a) > 1 else 5
sc = bpy.context.scene
f0 = int(a[2]) if len(a) > 2 else sc.frame_start; f1 = int(a[3]) if len(a) > 3 else sc.frame_end
cam = sc.camera; O = bpy.data.objects
CH = {"Pris": "Pris", "Vis": "Vis", "Smith": "Smith"}
def owner(o):
    n = o.name.split(".")[0]
    return n if n in CH else o.name
lines = []
for f in range(f0, f1 + 1, step):
    sc.frame_set(f); dg = bpy.context.evaluated_depsgraph_get()
    M = cam.matrix_world; cd = cam.data
    fr = cd.view_frame(scene=sc)                     # 4 corners in camera space
    xs = [v.x for v in fr]; ys = [v.y for v in fr]; z = fr[0].z
    o = M.translation
    hits = Counter(); near = Counter(); n = 0
    for i in range(7):
        for j in range(12):
            u = min(xs) + (max(xs) - min(xs)) * (i + 0.5) / 7; v = min(ys) + (max(ys) - min(ys)) * (j + 0.5) / 12
            d = (M.to_3x3() @ Vector((u, v, z))).normalized(); n += 1
            ok, loc, nr, idx, ob, mx = sc.ray_cast(dg, o, d, distance=200)
            if ok:
                k = owner(ob); hits[k] += 1
                if (loc - o).length < 0.25: near[k] += 1
            else:
                hits["<sky>"] += 1
    faces = []
    for r in ("Pris", "Vis", "Smith"):
        rig = O[r]
        if rig.get("hidden"): continue
        for e in ("eye.L", "eye.R"):
            p = rig.matrix_world @ rig.pose.bones[e].head
            pc = M.inverted() @ p
            if pc.z >= 0: continue
            sx = pc.x / -pc.z * -z; sy = pc.y / -pc.z * -z
            if not (min(xs) < sx < max(xs) and min(ys) < sy < max(ys)): continue
            d = p - o; ok, loc, nr, idx, ob, mx = sc.ray_cast(dg, o, d.normalized(), distance=d.length - 0.03)
            if (not ok) or owner(ob) == r:
                faces.append(r); break
    top, cnt = hits.most_common(1)[0]
    flags = []
    nt, nc = (near.most_common(1)[0] if near else ("", 0))
    if nc > 0.35 * n: flags.append("NEAR:%s" % nt)
    if cnt > 0.70 * n and any(k in top for k in ("Wall", "Floor", "Ceiling", "Ground", "<sky>", "Facade")): flags.append("WALL:%s" % top)
    if not faces: flags.append("NOFACE")
    lines.append("%4d lens %4.0f top %-22s %3d%%  faces %-18s %s" % (f, cd.lens, top[:22], 100 * cnt // n, ",".join(faces), " ".join(flags)))
open(out, "w").write("\n".join(lines)); print("CAMCHECK_DONE", out)
