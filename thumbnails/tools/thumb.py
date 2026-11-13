"""Render a thumbnail plate from a film's own Blender set, with a dedicated 16:9 camera.
  PYTHONPATH=<film scenes>:nvidia_doc/scenes python thumbnails/tools/thumb.py thumbnails/<film>/concepts.py <name> \
      [--pct 25] [--samples 32] [--out dir]
A concept (dict in CONCEPTS) holds:
  scene    set module name (sc_<scene>.py)          variant  build() variant (optional)
  move/t   optional MOVES entry + time, to pose the set's animation first
  cam      (loc, target, lens_mm)                    focus    point to focus on;  fstop  aperture
  exposure view exposure override                    setup(ctx)  extra lights / props / tweaks for the thumbnail
Full quality: 3840x2160, 256+ samples, OIDN denoise -> downscaled to 1920x1080 by the compositor."""
import os, sys, importlib.util, importlib
sys.argv = [a for a in sys.argv]
arg = lambda k, d: type(d)(sys.argv[sys.argv.index(k) + 1]) if k in sys.argv else d
cfg_path, name = sys.argv[1], sys.argv[2]
import bpy
from mathutils import Vector
import kit
from common import reset, camera, point_at

spec = importlib.util.spec_from_file_location("concepts", cfg_path)
cfgm = importlib.util.module_from_spec(spec); spec.loader.exec_module(cfgm)
C = cfgm.CONCEPTS[name]
mod = importlib.import_module("sc_" + C["scene"])
pct = arg('--pct', 100); samples = arg('--samples', 384)
s = reset(res=(3840, 2160), samples=samples, exposure=C.get("exposure", getattr(mod, "EXPOSURE", 0.0)))
s.render.resolution_percentage = pct
s.cycles.max_bounces = getattr(mod, "BOUNCES", 8)
s.cycles.adaptive_threshold = 0.01
ctx = mod.build(C.get("variant"))
if ctx is None: ctx = {}
cam = camera((0, 0, 0), (0, 1, 0), lens=35)
ctx["cam"] = cam
if C.get("move"):
    m = mod.MOVES[C["move"]]
    if m.get("anim"): m["anim"](ctx, C.get("t", 0.5))
if C.get("frame") is not None:
    s.frame_set(C["frame"])
loc, tgt, lens = C["cam"](ctx) if callable(C["cam"]) else C["cam"]
cam.location = Vector(loc); point_at(cam, tuple(tgt)); cam.data.lens = lens
if C.get("roll"):
    cam.rotation_euler.rotate_axis('Z', C["roll"])
if C.get("shift"):
    cam.data.shift_x, cam.data.shift_y = C["shift"]
if C.get("fstop"):
    cam.data.dof.use_dof = True
    f = C["focus"](ctx) if callable(C.get("focus")) else C.get("focus", tgt)
    cam.data.dof.focus_distance = (Vector(loc) - Vector(f)).length
    cam.data.dof.aperture_fstop = C["fstop"]
if C.get("setup"):
    C["setup"](ctx)
out = arg('--out', os.path.join(os.path.dirname(cfg_path), "plates"))
os.makedirs(out, exist_ok=True)
s.render.filepath = os.path.join(out, f"{name}.png")
s.render.image_settings.color_depth = '8'
bpy.ops.render.render(write_still=True)
print("[thumb]", s.render.filepath, flush=True)
if C.get("mask") and "--nomask" not in sys.argv:
    # a matte of the objects that stand in front of the word (alpha), so the text can sit behind them
    keep = set(C["mask"](ctx))
    for o in bpy.data.objects:
        if o.type in ('MESH', 'CURVE') and o not in keep:
            o.hide_render = True
    s.render.film_transparent = True; s.cycles.samples = 16; s.cycles.use_denoising = False
    s.render.image_settings.color_mode = 'RGBA'
    s.render.filepath = os.path.join(out, f"{name}_mask.png")
    bpy.ops.render.render(write_still=True)
    print("[mask]", s.render.filepath, flush=True)
