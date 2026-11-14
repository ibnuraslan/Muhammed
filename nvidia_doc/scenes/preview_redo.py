"""Preview stills for the Ch4-5 redo shots, rendered through a master-style scene (a fresh scene playing the shot
scene as a sequencer strip), which is exactly how nvidia_ch45.blend and its patches render: the master's colour
management applies (AgX, no look, exposure 0), so the set's own EXPOSURE/look do NOT reach the final picture.

  python scenes/preview_redo.py <set> <move> <frames> <outname> [--ts 0,0.5,1] [--pct 25] [--samples 12] [--title]
-> out/ch45_redo_prev/<outname>_t000.png ...  (prints the mean luminance of each)
--title injects the move's chapter card exactly as bake.py does.
"""
import os, sys, importlib
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bpy, numpy as np
import kit, grade
from common import reset, camera

arg = lambda k, d: type(d)(sys.argv[sys.argv.index(k) + 1]) if k in sys.argv else d
st, mv, frames, outname = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4]
TS = [float(x) for x in arg("--ts", "0,0.5,1").split(",")]
PCT, SAMPLES = arg("--pct", 25), arg("--samples", 12)
OUT = os.path.join(HERE, "..", "out", "ch45_redo_prev"); os.makedirs(OUT, exist_ok=True)
mod = importlib.import_module("sc_" + st)
for t in TS:
    s = reset(res=kit.RES, samples=SAMPLES, exposure=getattr(mod, "EXPOSURE", 0.0))
    s.cycles.max_bounces = getattr(mod, "BOUNCES", 8); s.cycles.adaptive_threshold = 0.05
    s.render.resolution_percentage = PCT; s.render.use_motion_blur = False
    variant = getattr(mod, "VARIANT_FOR", {}).get(mv, None)
    ctx = mod.build(variant); spec = mod.MOVES[mv]
    cam = camera((0, 0, 0), (0, 1, 0), lens=35, dof_dist=spec.get("dof", None) and 3.0, fstop=spec.get("dof", 2.8) or 2.8)
    cam.data.dof.use_dof = bool(spec.get("dof")); ctx["cam"] = cam
    if "--title" in sys.argv and spec.get("title"):
        import title_card
        tt = spec["title"]
        title_card.add_title(cam, tt[0], tt[1], tt[2], tt[3], scrim=tt[4] if len(tt) > 4 else 0.36)
    f = 1 + int(round(t * (frames - 1)))
    s.frame_start, s.frame_end = 1, frames
    s.frame_set(f)
    kit.apply_cam(cam, ctx, spec, t)
    grade.add_grade(s, look="plain")
    M = bpy.data.scenes.new("PREVIEW_MASTER"); M.render.engine = 'CYCLES'
    M.render.resolution_x, M.render.resolution_y, M.render.resolution_percentage = 1920, 816, PCT
    se = M.sequence_editor_create(); strip = se.strips.new_scene(name="shot", scene=s, channel=1, frame_start=1)
    strip.scene_input = 'CAMERA'
    M.render.use_sequencer = True; M.render.use_compositing = False
    fc = bpy.data.objects.new("FC", bpy.data.cameras.new("FC")); M.collection.objects.link(fc); M.camera = fc
    M.frame_set(f)
    p = os.path.join(OUT, f"{outname}_t{int(t * 100):03d}.png"); M.render.filepath = p
    bpy.ops.render.render(write_still=True, scene=M.name)
    im = bpy.data.images.load(p); a = np.array(im.pixels[:]).reshape(-1, 4)[:, :3]
    print(f"[prev] {outname} t={t} frame {f} mean {a.mean():.3f}", flush=True)
