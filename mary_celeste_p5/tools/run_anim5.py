"""Part 5 final pass: build one shot's scene (as the storyboard did), animate it to its VO-timed length, check it for
clipping over the shot, then either render the frame sequence or export it to the RenderStreet package.

    blender -b --python tools/run_anim5.py -- S05 [--start 1 --end 24]
    env: TIMINGS=vo/vo_timings.json (VO-retimed durations), EXPORT=<package dir> (farm .blend instead of rendering)
"""
import os, sys, json, runpy
HERE = os.path.dirname(os.path.abspath(__file__)); P5 = os.path.dirname(HERE)
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
sid = argv[0]
opt = lambda k, d=None: argv[argv.index(k) + 1] if k in argv else d
sys.path[:0] = [P5, os.path.join(P5, "scenes")]
from shots import SHOTS
scene = {s[0]: s[1] for s in SHOTS}[sid]
tim = json.load(open(os.environ.get("TIMINGS", os.path.join(P5, "vo", "vo_timings.json"))))
dur = float(tim[sid])
# hair strand density by how close the people are (0.7 = the approved storyboard look; far boats need very little):
# keeps every farm .blend small
HAIRD = {"S01": 0.12, "S02": 0.7, "S03": 0.15, "S04": 0.05, "S05": 0.7, "S06": 0.03, "S07": 0.35, "S08": 0.03,
         "S11": 0.6, "S22": 0.7, "S23": 0.4, "S26": 0.7, "S27": 0.03}
os.environ.update(P5_ANIM="1", SHOT=sid, PREVIEW=os.environ.get("PREVIEW", "0"),
                  HAIR=os.environ.get("HAIR", str(HAIRD.get(sid, 0.5))))
os.environ.setdefault("OUT", os.path.join(P5, "out", "anim", sid, sid + ".png"))
runpy.run_path(os.path.join(P5, "scenes", scene + ".py"), run_name="__main__")

import bpy
import p5, anim5 as A
from mathutils import Vector
FPS = 24
sc = bpy.context.scene; cam = sc.camera
nf = int(round(dur * FPS))

# camera: (move, handheld) per shot, from the storyboard's camera notes
MOVES = {
    "S01": (("push", 0.08), 0.0), "S02": (("push", 0.03), 0.35), "S03": (("tilt", 5), 0.3), "S04": (("pull", 0.08), 0.0),
    "S05": (("hold",), 0.6), "S06": (("spin", 4.0), 0.0), "S07": (("push", 0.05), 0.4), "S08": (("drift", (2.0, 0, 0)), 0.0),
    "S09": (("drift", (0.25, 0, 0)), 0.0), "S10": (("push", 0.12), 0.0), "S11": (("push", 0.06), 0.3), "S12": (("push", 0.07), 0.5),
    "S13": (("drift", (0.25, 0, 0)), 0.0), "S14": (("drift", (0.05, 0, 0)), 0.2), "S15": (("push", 0.05), 0.0),
    "S16": (("push", 0.06), 0.0), "S17": (("push", 0.1), 0.0), "S18": (("push", 0.06), 0.0), "S19": (("drift", (0.05, 0, 0)), 0.0),
    "S20": (("push", 0.06), 0.0), "S21": (("push", 0.03), 0.0), "S22": (("hold",), 0.3), "S23": (("push", 0.05), 0.0),
    "S24": (("drift", (2.0, 0, 0)), 0.0), "S25": (("drift", (1.2, 0, 0)), 0.0), "S26": (("push", 0.08), 0.0),
    "S27": (("pull", 0.15), 0.0), "S28": (("hold",), 0.0),
}

# the sea, the boats on it, the ship
A.ocean_time(dur)
RIDERS = []                                         # (root, its matrix at build) for the grip allowance in the check
for rec in {r[1].name: r for r in p5.FLOATS}.values():     # one ride per boat (the last placement wins)
    root = rec[1]
    A.adopt(root)
    RIDERS.append((root, root.matrix_world.copy()))
    q = root.matrix_world.inverted() @ cam.matrix_world.to_translation()
    if abs(q.x) < 3.6 and abs(q.y) < 1.4 and q.z < 3.0:      # a camera aboard the boat rides with it
        cam.parent = root; cam.matrix_parent_inverse = root.matrix_world.inverted()
    A.ride(rec, dur)
mc = bpy.data.objects.get("MC_root")
if mc is not None:
    if sid in ("S04", "S05", "S06"):
        A.sail(mc, dur, speed=2.6)                   # she moves away on the wind
    elif sid in ("S24", "S25"):
        A.sway(mc, dur)                              # at anchor / alongside the quay
for o in bpy.data.objects:                           # other ships at anchor (S24)
    if o.type == 'EMPTY' and o.parent is None and "dutch_ship" in o.name.lower():
        A.sway(o, dur, heave=0.06, roll=0.6, seed=hash(o.name) % 50)
A.steam(dur); A.flicker(dur)
if bpy.data.objects.get("Ocean_galley_water"):      # S12: Part 1's galley water and what floats in it
    sys.path.append(os.path.join(p5.ROOT, "mary_celeste_p1", "p1"))
    import anim as P1A
    P1A.galley_water(dur, [o for o in bpy.data.objects if o.name.startswith(("float_", "wooden_bucket_02", "wooden_spoon"))])
move, hh = MOVES.get(sid, (("push", 0.05), 0.0))
if move[0] != "hold" or hh:
    A.camera_move(cam, move if move[0] != "hold" else ("push", 0.0), dur, handheld=hh)

# clipping over the shot: first, middle and last frame, zero clips required
if any("person" in o for o in bpy.data.objects):
    import clipcheck
    bad = 0
    from mathutils import Vector as _V
    hands0 = {o.name: list(o["hands"]) for o in bpy.data.objects if "hands" in o}
    for f in sorted({1, max(1, nf // 2), max(1, nf)}):
        sc.frame_set(f)
        # the grip allowance follows the hands: wrists of people riding a boat move with the boat
        for root, R0 in RIDERS:
            D = root.matrix_world @ R0.inverted()
            for o in bpy.data.objects:
                if o.name in hands0 and o.parent is root:
                    h = hands0[o.name]
                    o["hands"] = [c for k in range(0, len(h), 3) for c in (D @ _V(h[k:k + 3]))]
        bad += len(clipcheck.check(f"{sid}_f{f:04d}"))
    print(f"CLIPRESULT {sid} {bad}", flush=True)
    if bad and os.environ.get("CLIP_STRICT", "1") == "1":
        print("ABORT: clipping in", sid, flush=True); sys.exit(2)
    sc.frame_set(1)

sc.frame_start = int(opt("--start", 1)); sc.frame_end = int(opt("--end", nf))
sc.render.fps = FPS
sc.render.use_motion_blur = os.environ.get("MBLUR", "1") == "1"; sc.render.motion_blur_shutter = 0.4
for o in bpy.data.objects:
    if o.name.startswith(("Ocean", "FarSea")) or o.name.endswith(("_hull", "_sail", "_deck")):
        o.cycles.use_motion_blur = False
if os.environ.get("EXPORT"):
    sys.path.insert(0, os.path.join(p5.ROOT, "mary_celeste_p1", "tools"))
    import farm_export                                # Part 1's farm export, used as is
    farm_export.export(os.environ["EXPORT"], sid)
    sys.exit(0)
out = os.path.join(P5, "out", "anim", sid); os.makedirs(out, exist_ok=True)
if os.environ.get("STILLS"):                          # check frames only: STILLS=first,mid,last or a list of numbers
    fr = [1, max(1, nf // 2), nf] if os.environ["STILLS"] == "fml" else [int(x) for x in os.environ["STILLS"].split(",")]
    for f in fr:
        sc.frame_set(f); sc.render.filepath = os.path.join(out, f"s{f:04d}.png"); bpy.ops.render.render(write_still=True)
    print("STILLS", sid, fr, flush=True); sys.exit(0)
sc.render.filepath = os.path.join(out, "f")
sc.render.use_overwrite = False; sc.render.use_placeholder = True
bpy.ops.render.render(animation=True)
print("RENDERED_ANIM", sid, sc.frame_start, sc.frame_end, flush=True)
