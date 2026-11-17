"""Screen positions (0..1, origin bottom-left) of a character's head/chest, or a world point, for a move at times t.
  python tools/track2d.py <set> <move> <out.json> --cast p --n 30        (or --point x,y,z)
Used to pin 2D overlays (photo callouts) to the 3D shot."""
import os, sys, json, importlib
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path[:0] = [os.path.join(ROOT, "scenes"), os.path.join(ROOT, "..", "..", "nvidia_doc", "scenes")]
import bpy, kit
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
from common import reset, camera
argv = sys.argv[1:]
st, mv, out = argv[:3]
arg = lambda k, d: type(d)(argv[argv.index(k) + 1]) if k in argv else d
n = arg("--n", 30); cast = arg("--cast", ""); point = arg("--point", "")
mod = importlib.import_module("sc_" + st)
s = reset(res=kit.RES, samples=1)
ctx = mod.build(getattr(mod, "VARIANT_FOR", {}).get(mv))
spec = mod.MOVES[mv]
cam = camera((0, 0, 0), (0, 1, 0), lens=35); ctx["cam"] = cam
res = []
for i in range(n):
    t = i / max(n - 1, 1)
    kit.apply_cam(cam, ctx, spec, t); bpy.context.view_layer.update()
    pts = {}
    if cast:
        h = ctx["cast"][cast]
        for b in ("head", "spine03"):
            p = world_to_camera_view(s, cam, h.bone_head(b)); pts[b] = (p.x, p.y, p.z)
    if point:
        p = world_to_camera_view(s, cam, Vector([float(v) for v in point.split(",")])); pts["point"] = (p.x, p.y, p.z)
    res.append(dict(t=t, **pts))
json.dump(res, open(out, "w"), indent=0)
print("[track]", out, res[0], res[-1])
