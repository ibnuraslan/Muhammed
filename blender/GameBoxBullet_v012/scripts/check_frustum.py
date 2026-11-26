"""Lens-blocker check (LESSONS, Nov 2026): on every sampled frame, cast a 9x16 grid of rays through the camera frustum and
report frames where near geometry (closer than NEAR m, not the intended macro subject) covers more than MAXFRAC of the frame.
blender -b film.blend --python check_frustum.py -- out.json [step=2] [near=0.06] [maxfrac=0.25]"""
import bpy, sys, json
from mathutils import Vector
a = sys.argv[sys.argv.index("--") + 1:]
out = a[0]; step = int(a[1]) if len(a) > 1 else 2; NEAR = float(a[2]) if len(a) > 2 else 0.06; MAXF = float(a[3]) if len(a) > 3 else 0.25
sc = bpy.context.scene; cam = sc.camera
SUBJECT = ("Bullet",)                    # the macro subject itself may fill the frame
bad = []; worst = []
for f in range(sc.frame_start, sc.frame_end + 1, step):
    sc.frame_set(f); dg = bpy.context.evaluated_depsgraph_get()
    M = cam.matrix_world; o = M.translation
    fr = cam.data.view_frame(scene=sc)            # 4 corners in camera space
    xs = [v.x for v in fr]; ys = [v.y for v in fr]; z = fr[0].z
    n = 0; near = 0; who = {}
    for i in range(9):
        for j in range(16):
            p = Vector((min(xs) + (max(xs) - min(xs)) * (i + 0.5) / 9, min(ys) + (max(ys) - min(ys)) * (j + 0.5) / 16, z))
            d = (M.to_3x3() @ p).normalized()
            hit, loc, nrm, idx, ob, _ = sc.ray_cast(dg, o + d * cam.data.clip_start, d, distance=NEAR)
            n += 1
            if hit and not ob.name.startswith(SUBJECT):
                near += 1; who[ob.name] = who.get(ob.name, 0) + 1
    frac = near / n
    worst.append((round(frac, 3), f))
    if frac > MAXF:
        bad.append({"frame": f, "frac": round(frac, 3), "objects": sorted(who.items(), key=lambda x: -x[1])[:3]})
json.dump({"near_m": NEAR, "max_frac": MAXF, "bad": bad, "worst": sorted(worst)[-10:]}, open(out, "w"), indent=1)
print("FRUSTUM bad frames:", len(bad), [b["frame"] for b in bad][:40])
