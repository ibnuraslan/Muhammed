"""Chat B preview still: like nvidia_doc/scenes/run.py --still --exr, plus hands.json (pixel positions of every
visible wrist, for the hand-crop strip on review sheets).
  python b_run.py <set> <move> --t 0.5 --pct 40 --samples 12 --out DIR
"""
import os, sys, json, importlib
HERE = os.path.dirname(os.path.abspath(__file__))
import bpy
import kit
from common import reset, camera
from bpy_extras.object_utils import world_to_camera_view

arg = lambda k, d: type(d)(sys.argv[sys.argv.index(k) + 1]) if k in sys.argv else d
scene_name, move = sys.argv[1], sys.argv[2]
OUT = arg('--out', "/tmp/b_run"); os.makedirs(OUT, exist_ok=True)
mod = importlib.import_module("sc_" + scene_name)
s = reset(res=kit.RES, samples=arg('--samples', 12), exposure=getattr(mod, "EXPOSURE", 0.0))
s.render.resolution_percentage = arg('--pct', 40)
s.cycles.max_bounces = getattr(mod, "BOUNCES", 8)
ctx = mod.build(getattr(mod, "VARIANT_FOR", {}).get(move, None))
spec = mod.MOVES[move]
cam = camera((0, 0, 0), (0, 1, 0), lens=35, dof_dist=3.0, fstop=spec.get("dof", 2.8) or 2.8)
cam.data.dof.use_dof = bool(spec.get("dof"))
ctx["cam"] = cam
t = arg('--t', 0.5)
s.frame_set(int(arg('--frame', 1 + round(t * 24 * getattr(mod, "DUR", {}).get(move, 5.0)))))
kit.apply_cam(cam, ctx, spec, t)
bpy.context.view_layer.update()
hands = []
for a in bpy.data.objects:
    if a.type != 'ARMATURE' or a.hide_render or "wrist.L" not in a.pose.bones:
        continue
    for sd in ("L", "R"):
        p = a.matrix_world @ a.pose.bones[f"wrist.{sd}"].tail
        v = world_to_camera_view(s, cam, p)
        if 0.02 < v.x < 0.98 and 0.02 < v.y < 0.98 and v.z > 0:
            hands.append(dict(who=a.name, side=sd, x=v.x, y=1 - v.y, dist=v.z))
json.dump(hands, open(os.path.join(OUT, "hands.json"), "w"))
s.render.image_settings.file_format = 'OPEN_EXR'; s.render.image_settings.color_depth = '32'
s.render.use_compositing = False
json.dump(dict(exposure=s.view_settings.exposure, cine=json.loads(s.get("look_cine", "{}"))), open(os.path.join(OUT, "plate.json"), "w"))
s.render.filepath = os.path.join(OUT, "plate.exr")
bpy.ops.render.render(write_still=True)
print("[b_run]", OUT, len(hands), "hands", flush=True)
