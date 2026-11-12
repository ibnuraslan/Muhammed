"""QA: render a still and crop every visible hand (wrist + 0.25 m) so twisted wrists / wrong-way palms show.
  PYTHONPATH=projects/killer-in-house/scenes:nvidia_doc/scenes python projects/killer-in-house/tools/hand_check.py <set> <move> <t> <outdir>
-> outdir/<set>_<move>/plate.png and hand_<rig>_<L|R>.png (only hands inside the frame and not hidden behind something)
"""
import os, sys, importlib
sys.path.insert(0, "/home/user/Muhammed/nvidia_doc/scenes")
import bpy
import kit
from common import reset, camera
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
st, mv, t, outd = sys.argv[1], sys.argv[2], float(sys.argv[3]), sys.argv[4]
OUT = os.path.join(outd, f"{st}_{mv}"); os.makedirs(OUT, exist_ok=True)
mod = importlib.import_module("sc_" + st)
s = reset(res=kit.RES, samples=8, exposure=getattr(mod, "EXPOSURE", 0.0)); s.render.resolution_percentage = 50
ctx = mod.build(getattr(mod, "VARIANT_FOR", {}).get(mv, None)); spec = mod.MOVES[mv]
cam = camera((0, 0, 0), (0, 1, 0), lens=35, dof_dist=3.0, fstop=spec.get("dof", 2.8) or 2.8); cam.data.dof.use_dof = False
ctx["cam"] = cam
kit.apply_cam(cam, ctx, spec, t)
p = os.path.join(OUT, "plate.png"); s.render.filepath = p; bpy.ops.render.render(write_still=True)
from PIL import Image
im = Image.open(p); W, Hh = im.size
dg = bpy.context.evaluated_depsgraph_get()
n = 0
for a in bpy.data.objects:
    if a.type != 'ARMATURE':
        continue
    for sd in ("L", "R"):
        b = a.pose.bones.get("wrist." + sd)
        if b is None:
            continue
        w = a.matrix_world @ b.tail
        v = world_to_camera_view(s, cam, w)
        if v.z <= 0 or not (0.02 < v.x < 0.98 and 0.02 < v.y < 0.98):
            continue
        d = (w - cam.matrix_world.translation)
        ok, loc, *_ = s.ray_cast(dg, cam.matrix_world.translation, d.normalized(), distance=d.length - 0.12)
        hidden = ok
        r = max(24, int(0.16 / max(v.z, 0.3) * cam.data.lens / 36 * W))
        x, y = int(v.x * W), int((1 - v.y) * Hh)
        crop = im.crop((max(0, x - r), max(0, y - r), min(W, x + r), min(Hh, y + r))).resize((240, 240))
        crop.save(os.path.join(OUT, f"hand_{a.name}_{sd}{'_hidden' if hidden else ''}.png")); n += 1
print("[hands]", st, mv, n, "crops", flush=True)
