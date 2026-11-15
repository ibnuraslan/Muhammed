"""v009: third-person camera rules (director): people in frame >= 1.5 m from the lens (passengers >= 1.0 m),
no shot longer than 2.5 s. The final face close-up (55.72 s on) is exempt by direction.
blender -b film.blend --python cam_dist_check.py -- out.json [step=3]"""
import bpy, sys, json
from bpy_extras.object_utils import world_to_camera_view
a = sys.argv[sys.argv.index("--") + 1:]; OUT = a[0]; STEP = int(a[1]) if len(a) > 1 else 3
sc = bpy.context.scene; cam = sc.camera; FPS = sc.render.fps
EXEMPT0 = 1 + round(55.72 * FPS)
BONES = ("head", "neck01", "spine02", "spine05", "wrist.L", "wrist.R", "hand.L", "hand.R", "lowerarm01.L", "lowerarm01.R",
         "upperleg01.L", "upperleg01.R", "lowerleg01.L", "lowerleg01.R", "foot.L", "foot.R")
MAIN = {"YOU", "CAPT", "FO"}
rigs = [o for o in bpy.data.objects if o.type == 'ARMATURE' and "head" in o.pose.bones]
res = {"flags": [], "shots": []}
prev = None; cut = sc.frame_start
for f in range(sc.frame_start, sc.frame_end + 1):
    sc.frame_set(f); M = cam.matrix_world.copy()
    if prev is not None and ((M.translation - prev.translation).length > 0.05 or (M.to_3x3() - prev.to_3x3()).median_scale > 0 and max(abs(x) for r in (M.to_3x3() - prev.to_3x3()) for x in r) > 0.08):
        res["shots"].append([cut, f - 1, round((f - cut) / FPS, 2)]); cut = f
    prev = M
    if (f - sc.frame_start) % STEP or f >= EXEMPT0: continue
    cp = M.translation
    for r in rigs:
        lim = 1.5 if r.name in MAIN else 1.0
        for b in BONES:
            if b not in r.pose.bones: continue
            p = r.matrix_world @ r.pose.bones[b].head
            d = (p - cp).length
            if d >= lim: continue
            c = world_to_camera_view(sc, cam, p)
            if -0.05 <= c.x <= 1.05 and -0.05 <= c.y <= 1.05 and c.z > 0:
                res["flags"].append([f, round(f / FPS, 2), r.name, b, round(d, 2)])
res["shots"].append([cut, sc.frame_end, round((sc.frame_end + 1 - cut) / FPS, 2)])
long_ = [s for s in res["shots"] if s[2] > 2.5]
res["long_shots"] = long_
json.dump(res, open(OUT, "w"), indent=1)
byrig = {}
for fl in res["flags"]: byrig.setdefault(fl[2], []).append(fl[1])
print("CAMDIST shots", len(res["shots"]), "long", long_, "flags", {k: (len(v), min(v), max(v)) for k, v in byrig.items()})
