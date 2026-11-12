"""Run a scene move. Examples:
  python scenes/run.py office_door door_push --still --lowres --samples 16      # look-dev still
  python scenes/run.py office_door door_push --anim 72 --samples 64             # hero animation (12 fps)
  python scenes/run.py port crane_rise --plate                                   # plate + depth for 2.5D
  --plain : old bright lighting (look.py recipes become no-ops), for before/after sheets
  --exr   : still as scene-linear EXR (plate.exr + plate.json with the exposure), to grade with grade.grade_file
"""
import os, sys, importlib
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
if "--plain" in sys.argv:
    os.environ["HOUSE_LOOK"] = "plain"
import bpy
import kit
from common import reset, camera

arg = lambda k, d: type(d)(sys.argv[sys.argv.index(k) + 1]) if k in sys.argv else d
scene_name, move = sys.argv[1], sys.argv[2]
OUT = arg('--out', os.path.join(HERE, "..", "out", "plates", scene_name, move))
os.makedirs(OUT, exist_ok=True)
SAMPLES = arg('--samples', 96)

mod = importlib.import_module("sc_" + scene_name)
s = reset(res=kit.RES, samples=SAMPLES, exposure=getattr(mod, "EXPOSURE", 0.0))
if "--lowres" in sys.argv:
    s.render.resolution_percentage = 33
if "--pct" in sys.argv:
    s.render.resolution_percentage = arg('--pct', 100)
s.cycles.max_bounces = getattr(mod, "BOUNCES", 8)
variant = getattr(mod, "VARIANT_FOR", {}).get(move, None)
ctx = mod.build(variant)
spec = mod.MOVES[move]
cam = camera((0, 0, 0), (0, 1, 0), lens=35, dof_dist=spec.get("dof", None) and 3.0, fstop=spec.get("dof", 2.8) or 2.8)
if spec.get("dof"):
    cam.data.dof.use_dof = True
ctx["cam"] = cam

if "--anim" in sys.argv:
    n = arg('--anim', 72)
    if hasattr(mod, "screen_corners"):      # per-frame screen corners for pinning UI in post (cheap: no render)
        import json
        cs = []
        for i in range(n):
            kit.apply_cam(cam, ctx, spec, i / max(n - 1, 1)); cs.append(mod.screen_corners(ctx, s, cam))
        json.dump(dict(corners=cs[0], frames=cs), open(os.path.join(OUT, "screen.json"), "w"))
    for i in range(n):
        p = os.path.join(OUT, f"f{i:04d}.png")
        if os.path.exists(p):
            continue
        kit.apply_cam(cam, ctx, spec, i / max(n - 1, 1))
        s.render.filepath = p; bpy.ops.render.render(write_still=True)
        print("[anim]", p, flush=True)
else:
    t = 0.0 if spec.get("kind") == "anim" and "--still" in sys.argv and "--mid" not in sys.argv else 0.5
    t = arg('--t', t)
    kit.apply_cam(cam, ctx, spec, t)
    if "--exr" in sys.argv:
        import json
        s.render.image_settings.file_format = 'OPEN_EXR'; s.render.image_settings.color_depth = '32'
        s.render.use_compositing = False
        json.dump(dict(exposure=s.view_settings.exposure, look=s.view_settings.look, cine=json.loads(s.get("look_cine", "{}"))), open(os.path.join(OUT, "plate.json"), "w"))
        s.render.filepath = os.path.join(OUT, "plate.exr")
    else:
        s.render.filepath = os.path.join(OUT, "plate.png")
    bpy.ops.render.render(write_still=True)
    if "--plate" in sys.argv:
        kit.render_depth(os.path.join(OUT, "depth.png"), far=spec.get("far", 60.0))
    if hasattr(mod, "screen_corners"):
        import json
        json.dump(dict(corners=mod.screen_corners(ctx, s, cam)), open(os.path.join(OUT, "screen.json"), "w"))
    print("[plate]", OUT, flush=True)
