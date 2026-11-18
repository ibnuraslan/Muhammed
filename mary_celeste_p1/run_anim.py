"""Render one Part 1 shot as an animated sequence (final pass).

    blender -b --python run_anim.py -- S10 [--dur 1.0] [--start 1 --end 24]
Writes out/frames/<id>/f0001.png ... (raw, no card / caption: comp/assemble.py adds those).
Motion: people keyed live (p1/anim.py), the camera moves per MOVES, ships worked by the sea, the sea advances."""
import os, sys, math
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "p1")); sys.path.insert(0, HERE)
import bpy
from mathutils import Vector
import env as E
import shots, anim as A, ship

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
sid = argv[0]
opt = lambda k, d=None: argv[argv.index(k) + 1] if k in argv else d
sh = shots.SHOTS[sid]
dur = float(opt("--dur", sh["dur"]))

# per-shot camera moves: (move, handheld). Default by kind of shot (see default_move).
MOVES = {
    "S01": (("drift", (2.5, 0, 0)), 0), "S02": (("push", 0.08), 0.6), "S03": (("push", 0.12), 0.7), "S04": (("rise", 0.25), 0.3),
    "S05": (("push", 0.06), 0.5), "S06": (("push", 0.1), 0.3), "S07": (("push", 0.12), 0.4), "S08": (("drift", (0.15, 0, 0)), 0.6),
    "S09": (("hold",), 0.15), "S10": (("push", 0.07), 0.4), "S11": (("push", 0.1), 0.5), "S12": (("rise", 0.4), 0),
    "S13": (("drift", (1.5, 0, 0)), 0), "S14": (("drift", (0.4, 0, 0)), 0.5), "S15": (("pull", 0.08), 0), "S16": (("push", 0.05), 0),
    "S17": (("push", 0.1), 0), "S18": (("drift", (3.0, 0, 0)), 0), "S19": (("push", 0.06), 0.3), "S20": (("drift", (2.0, 0, 0)), 0),
    "S21": (("push", 0.08), 0.5), "S22": (("hold",), 0.8), "S23": (("push", 0.07), 0.5), "S24": (("drift", (0.2, 0, 0)), 0.6),
    "S25": (("drift", (3.0, 0, 0)), 0), "S26": (("push", 0.05), 0.6), "S27": (("hold",), 0.7), "S28": (("tilt", 6), 0.3),
    "S29": (("tilt", -4), 0.3), "S30": (("drift", (1.2, 0, 0)), 0), "S31": (("push", 0.1), 0.5), "S32": (("push", 0.12), 0.2),
    "S33": (("rise", 0.8), 0), "S34": (("push", 0.07), 0.5), "S35": (("drift", (0.12, 0, 0)), 0.2), "S36": (("push", 0.08), 0.5),
    "S37": (("push", 0.06), 0.5), "S38": (("drift", (0.25, 0, 0)), 0.2), "S39": (("drift", (2.5, 0, 0)), 0), "S40": (("tilt", 5), 0.3),
    "S41": (("drift", (2.0, 0, 0)), 0), "S42": (("push", 0.12), 0.3), "S43": (("push", 0.12), 0), "S44": (("push", 0.05), 0.5),
    "S45": (("push", 0.18), 0.2), "S46": (("push", 0.1), 0.2), "S47": (("push", 0.08), 0.1), "S48": (("push", 0.08), 0.3),
    "S49": (("drift", (0.05, 0, 0)), 0.1), "S50": (("drift", (0.05, 0, 0)), 0.1), "S51": (("push", 0.12), 0), "S52": (("pull", 0.15), 0),
    "S53": (("push", 0.06), 0),
}

# per-shot actions on top of the pose (actor index in creation order -> fn(dv, M, t)); each one is motivated by the
# script: searching, looking down at the hollow, eyes narrowing at the horizon, calling out, weighing the risk
import poses as P


def ease(u):
    u = min(max(u, 0.0), 1.0); return u * u * (3 - 2 * u)


def look_turn(yaw0, yaw1, pitch0=0.0, pitch1=0.0, t0=0.0, t1=None):
    def f(dv, M, t):
        e = ease((t - t0) / max((t1 or dur) - t0, 1e-3))
        P.head(dv.h, pitch=pitch0 + (pitch1 - pitch0) * e, yaw=yaw0 + (yaw1 - yaw0) * e)
    return f


def lean_in(deg, t0=0.0):
    def f(dv, M, t):
        e = ease((t - t0) / max(dur - t0, 1e-3))
        for b, k in (("spine04", 0.35), ("spine03", 0.35), ("spine02", 0.3)):
            dv.h.rot(b, (1, 0, 0), deg * k * e)
    return f


def narrow(amount):
    def f(dv, M, t):
        dv.lids(amount * ease(t / dur)); dv.brow_knit(amount * 0.8 * ease(t / dur))
    return f


def both(*fs):
    def f(dv, M, t):
        for g in fs:
            g(dv, M, t)
    return f


ACTIONS = {
    "S02": {0: look_turn(-10, 25, 0, -4)},
    "S03": {0: look_turn(-30, 30, 0, 4)},
    "S05": {0: lean_in(4)}, "S07": {0: both(lean_in(5), narrow(0.4))},
    "S08": {0: look_turn(10, -15)},
    "S10": {0: look_turn(0, 8, 0, 6)},
    "S14": {0: look_turn(-10, 10), 2: look_turn(-10, 15, 0, -6)},
    "S21": {0: both(narrow(0.6), look_turn(0, 6, 0, -3))},
    "S23": {0: lean_in(6)},
    "S26": {0: lean_in(5), 1: look_turn(0, -12)},
    "S31": {0: lean_in(4)},
    "S36": {0: look_turn(-12, 6, 0, 4)},
    "S42": {0: look_turn(0, 28, 0, 14, t0=0.8)},
    "S44": {0: look_turn(8, -10, 0, 6)},
    "S48": {0: look_turn(-4, 6, 0, 3)},
}

E.reset()
shots.ANIM.update(on=True, dur=dur, actors=[], actions=ACTIONS.get(sid, {}))
sh["fn"]()
sc = bpy.context.scene
cam = sc.camera
move, hh = MOVES.get(sid, (("push", 0.06), 0.3))

# ships and boats: the sea works them; whatever stands on them goes with them
roots = [o for o in bpy.data.objects if o.name.endswith("_root") and o.type == 'EMPTY' and not o.name.startswith("MCx")]
SHIPS = {"MC_root": dict(), "DG_root": dict(), "DGboat_root": dict(heave=0.12, roll=3.0, pitch=1.5, period=4.2),
         "ghostboat_root": None}


def inside(root, p, pad=1.2):
    q = root.matrix_world.inverted() @ Vector(p)
    big = root.name.startswith(("MC", "DG_")) and not root.name.startswith("DGboat")
    Lh, Bh = (ship.L / 2 + pad, ship.B / 2 + pad) if big else (3.0, 1.5)
    return abs(q.x) < Lh and abs(q.y) < Bh and -4 < q.z < 30


skip = {"Ocean", "FarSea", "Sun", "SeaHaze"}
bpy.context.view_layer.update()                       # matrix_world must be current before re-parenting
for r in roots:
    cfg = SHIPS.get(r.name, dict())
    if cfg is None:
        continue
    aboard = inside(r, cam.location)
    for o in list(bpy.data.objects):
        if o.parent is not None or o is r or o.name in skip or o.name.endswith("_root") or o.type in ('LIGHT',):
            continue
        if o is cam and not aboard:
            continue
        if o.type == 'CAMERA' or inside(r, o.matrix_world.to_translation(), pad=0.6):
            if o.name.startswith(("land", "mapsea", "floor", "meridian", "parallel")):
                continue
            mw = o.matrix_world.copy(); o.parent = r; o.matrix_world = mw
    bpy.context.view_layer.update()
    A.ship_motion(r, dur, seed=sum(map(ord, r.name)) % 97, **cfg)

A.ocean_time(dur)
bpy.context.view_layer.update()
if move[0] != "hold" or hh:
    A.camera_move(cam, move if move[0] != "hold" else ("push", 0.0), dur, handheld=hh)

sc.frame_start = int(opt("--start", 1)); sc.frame_end = int(opt("--end", int(round(dur * E.FPS))))
out = os.path.join(HERE, "out", "frames", sid); os.makedirs(out, exist_ok=True)
sc.render.filepath = os.path.join(out, "f")
sc.render.use_overwrite = False; sc.render.use_placeholder = True
import grade as G
k = dict(E.WARM); k.update(sh.get("cine") or {})
G.add_grade(sc, bloom=0.28, look="cinematic", cine=k, vignette=0.6)
# motion blur on the camera and people only (the FFT sea changes topology each frame and would cost 3x)
sc.render.use_motion_blur = os.environ.get("MBLUR", "1") == "1"; sc.render.motion_blur_shutter = 0.4
for o in bpy.data.objects:
    if o.name in ("Ocean", "FarSea") or o.name.endswith(("_hull", "_sail", "_deck")):
        o.cycles.use_motion_blur = False
sc.render.use_persistent_data = True
bpy.ops.render.render(animation=True)
print("RENDERED_ANIM", sid, sc.frame_start, sc.frame_end, flush=True)
