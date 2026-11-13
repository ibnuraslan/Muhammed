"""Render one graded still per Ch4-5 shot (plain house look) for the approval storyboard.
  python scenes/storyboard_ch45.py             all shots
  python scenes/storyboard_ch45.py interview hq warehouse    only these sets (smoke test)
Groups shots by (set, variant) so each set builds once. Renders 25%, low samples, look="plain".
Also renders a Ch3 reference frame (c3_01 capitol ch3_push) for a side-by-side look check.
"""
import os, sys, json, importlib
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "..", "edit"))
import bpy, kit, grade
from common import reset, camera
from chapter_shots_ch45 import CH

OUT = os.path.join(HERE, "..", "out", "ch45_sb")
os.makedirs(OUT, exist_ok=True)
PCT = int(os.environ.get("SB_PCT", 25))
SAMPLES = int(os.environ.get("SB_SAMPLES", 16))
only = set(sys.argv[1:])

# flat list of (chapter, idx, set, move, label, name)
shots = []
for c, lst in CH.items():
    for k, (st, mv, lab, anc) in enumerate(lst):
        shots.append((c, k, st, mv, lab, f"c{c}_{k+1:02d}_{st}_{mv}"))
# a Ch3 reference for the look check
ref = ("capitol", "ch3_push", "REF Ch3 c3_01 capitol ch3_push (look match)", "c3_ref_capitol_ch3_push")


def render_one(mod, st, mv, name, t=0.5, title_frame=None):
    exposure = getattr(mod, "EXPOSURE", 0.0)
    s = reset(res=kit.RES, samples=SAMPLES, exposure=exposure)
    s.render.resolution_percentage = PCT
    s.cycles.max_bounces = getattr(mod, "BOUNCES", 8)
    s.cycles.adaptive_threshold = 0.05
    variant = getattr(mod, "VARIANT_FOR", {}).get(mv, None)
    ctx = mod.build(variant)
    spec = mod.MOVES[mv]
    cam = camera((0, 0, 0), (0, 1, 0), lens=35, dof_dist=spec.get("dof", None) and 3.0, fstop=spec.get("dof", 2.8) or 2.8)
    if spec.get("dof"):
        cam.data.dof.use_dof = True
    ctx["cam"] = cam
    if spec.get("title") and title_frame is not None:   # inject the chapter card exactly as bake.py does
        import title_card
        small, big, f_in, f_out = spec["title"][:4]
        title_card.add_title(cam, small, big, f_in, f_out, scrim=spec["title"][4] if len(spec["title"]) > 4 else 0.36)
    s.frame_set(title_frame if title_frame is not None else 40)    # evaluate frame drivers (clock, lights, title fade)
    kit.apply_cam(cam, ctx, spec, t)
    grade.add_grade(s, look="plain")
    s.render.filepath = os.path.join(OUT, name + ".png")
    bpy.ops.render.render(write_still=True)
    print("[sb]", name, flush=True)


# group by set to build once per (set, variant); but reset() wipes the scene, so just build per shot (simpler, robust)
NAMES = [n for n in os.environ.get("SB_NAMES", "").split(",") if n]
TS = [float(x) for x in os.environ.get("SB_TS", "0.5").split(",")]
if NAMES:
    for (c, k, st, mv, lab, name) in shots:
        if name not in NAMES:
            continue
        mod = importlib.import_module("sc_" + st)
        for t in TS:
            try:
                render_one(mod, st, mv, f"{name}_t{int(t*100):03d}", t=t)
            except Exception as e:
                import traceback; traceback.print_exc(); print("[sb][ERR]", name, e, flush=True)
        if mod.MOVES[mv].get("title"):
            render_one(mod, st, mv, f"{name}_title", t=0.25, title_frame=66)
    print("[sb] done named", len(NAMES)); sys.exit(0)
todo = [sh for sh in shots if not only or sh[2] in only]
for (c, k, st, mv, lab, name) in todo:
    try:
        mod = importlib.import_module("sc_" + st)
        render_one(mod, st, mv, name)
    except Exception as e:
        import traceback; traceback.print_exc(); print("[sb][ERR]", name, e, flush=True)
if not only or "capitol" in only:
    mod = importlib.import_module("sc_capitol")
    render_one(mod, "capitol", "ch3_push", ref[3], t=0.5)
print("[sb] done", len(todo), "shots ->", OUT)
