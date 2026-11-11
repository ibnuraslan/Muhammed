"""Render a thumbnail still.
  PYTHONPATH=projects/thumbnails/nvidia/scenes:nvidia_doc/scenes \
    python projects/thumbnails/nvidia/scenes/thumb.py <name> [--variant V] [--pct 25] [--samples 32] [--out DIR] [--blend]

Writes <out>/<name>.png at 3840x2160 (x pct) and <out>/<name>_1280.png at 1280x720.
Full quality = --pct 100 --samples 256 (Cycles, adaptive, OpenImageDenoise).
"""
import os, sys, importlib
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bpy
from mathutils import Vector
from common import reset, camera
import grade
from thumbkit import THUMB_RES

arg = lambda k, d: type(d)(sys.argv[sys.argv.index(k) + 1]) if k in sys.argv else d
name = sys.argv[1]
OUT = arg('--out', os.path.join(HERE, "..", "out"))
os.makedirs(OUT, exist_ok=True)
SAMPLES = arg('--samples', 256)
PCT = arg('--pct', 100)
variant = arg('--variant', "")
tag = arg('--tag', name + (("_" + variant) if variant else ""))

mod = importlib.import_module("th_" + name)
s = reset(res=THUMB_RES, samples=SAMPLES, exposure=getattr(mod, "EXPOSURE", 0.0))
s.render.resolution_percentage = PCT
s.render.image_settings.color_depth = '8'
s.cycles.adaptive_threshold = 0.01 if SAMPLES >= 128 else 0.03
s.cycles.max_bounces = getattr(mod, "BOUNCES", 8)
s.view_settings.look = getattr(mod, "LOOK", 'AgX - High Contrast')
s.render.use_persistent_data = False
ctx = mod.build(variant or None)
loc, tgt, lens = ctx["cam"]
cam = camera(tuple(loc), tuple(tgt), lens=lens, dof_dist=1.0, fstop=ctx.get("fstop", 2.8))
cam.data.dof.focus_distance = (Vector(loc) - Vector(ctx["focus"])).length
if ctx.get("shift"):
    cam.data.shift_x, cam.data.shift_y = ctx["shift"]
for o in bpy.data.objects:          # light sources never show as shapes; practicals are emissive meshes
    if o.type == 'LIGHT':
        o.visible_camera = False
if "post" in ctx:
    ctx["post"](ctx, cam)
grade.add_grade(s, bloom=getattr(mod, "BLOOM", 0.45), vignette=getattr(mod, "VIGNETTE", 0.65))
if "--blend" in sys.argv:
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, tag + ".blend"))
p = os.path.join(OUT, tag + ".png")
s.render.filepath = p
bpy.ops.render.render(write_still=True)
from PIL import Image
Image.open(p).convert("RGB").resize((1280, 720), Image.LANCZOS).save(os.path.join(OUT, tag + "_1280.png"))
print("[thumb]", p, flush=True)
