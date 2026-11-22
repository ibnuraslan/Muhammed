"""Seldom intros (films 1-4): animated pass for one shot -> a self-contained farm .blend (or a local render).

    blender -b --factory-startup -P run_anim.py -- f1 B          (env: EXPORT=<package dir>, else renders here)
Motion (nothing moves by itself):
  people  - live rigs (shared lib/anim.py, as Part 1/4): breathing, blinks; the shot's own action is the pose as a
            function of shot time (si.T), keyed every 0.25 s; feet/knees settled on the floor;
  props   - every prop a person moves follows the live hand (si.hand), keyed every frame; wipes, doors, lights keyed;
  camera  - the shot's move through t = 0, 0.5, 1 (smoothstep), keyed every frame.
"""
import os, sys, json, math, subprocess, runpy, importlib
HERE = os.path.dirname(os.path.abspath(__file__))
P4 = os.path.join(HERE, "..", "mary_celeste_p4")
sys.path[:0] = [os.path.join(HERE, "lib"), os.path.join(HERE, "films"), os.path.join(P4, "lib"), os.path.join(P4, "tools")]
argv = sys.argv[sys.argv.index("--") + 1:]
FILM, SHOT = argv[0], argv[1]
FPS = 24
MODS = {"f1": "f1_lamp", "f2": "f2_letters", "f3": "f3_locksmith", "f4": "f4_salvage"}
BL = os.environ.get("BLENDER", "/opt/blender/blender-5.2.2-linux-x64/blender")

# 1. the camera at t = 0.5 and 1 (separate light runs: people are not built)
camdir = os.path.join(HERE, "out", "cams"); os.makedirs(camdir, exist_ok=True)
camfile = lambda t: os.path.join(camdir, f"{FILM}_{SHOT}_{t}.json")
for t in ("0.0", "0.5", "1.0"):
    if not os.path.exists(camfile(t)) or os.environ.get("RECAM"):
        env = dict(os.environ, CAMDUMP=camfile(t), PCT="10"); env.pop("ANIM", None); env.pop("EXPORT", None)
        subprocess.run([BL, "-b", "--factory-startup", "-P", os.path.join(HERE, "films", "run.py"), "--", FILM, SHOT, t, "/tmp/x.png"],
                       env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
cams = [json.load(open(camfile(t))) for t in ("0.0", "0.5", "1.0")]

# 2. the shot at t = 0, people live
os.environ["ANIM"] = "1"
import si
si.ANIM = "1"; si.T = 0.0
si.C.reset()
import bpy
from mathutils import Vector, Matrix
mod = importlib.import_module(MODS[FILM])
t0, t1 = mod.SHOTS[SHOT]
NF = int(round((t1 - t0) * FPS)); DUR = NF / FPS
mod.build(SHOT, 0.0, None)
import anim as A
sc = bpy.context.scene
ease = lambda u: u * u * (3 - 2 * u)


class TSet:
    pre = True
    def __call__(self, dv, M, t):
        si.T = min(1.0, max(0.0, t / DUR))


def lowest(dv, frames):
    dg = None; lo = 1e9
    for f in frames:
        sc.frame_set(f); dg = bpy.context.evaluated_depsgraph_get()
        for o in dv.objects:
            if o.type != 'MESH' or o.hide_render or o.name.endswith("_body"):
                continue
            oe = o.evaluated_get(dg); me = oe.to_mesh()
            for v in me.vertices:
                lo = min(lo, (oe.matrix_world @ v.co).z)
            oe.to_mesh_clear()
    return lo


# 3. people
for i, ac in enumerate(si.ACTORS):
    dv, M, pose = ac["dv"], ac["M"], ac["pose"]
    A.live(dv, M, lambda dv_, M_, pose=pose: pose(dv_.h, dv_, M_, M_.inverted()), ac["look"], DUR,
           density=0.75 * ac["hair"], seed=i, action=TSet())
    sc.frame_set(1); bpy.context.view_layer.update()
    for o in list(getattr(dv, "sea_boots", [])):            # procedural boots (women): ride the foot bones
        if o.parent is None and not any(m.type == 'ARMATURE' for m in o.modifiers):
            side = "L" if "bootL" in o.name else "R"
            mw = M @ o.matrix_world
            o.parent = dv.h.arm; o.parent_type = 'BONE'; o.parent_bone = f"foot.{side}"
            bpy.context.view_layer.update(); o.matrix_world = mw
    if ac.get("settle", True):
        lo = lowest(dv, sorted({1, max(1, NF // 2), NF}))
        dz = ac["floor_z"] + 0.002 - lo
        movers = [dv.h.arm] + [o for o in dv.objects if o.parent is None and not any(m.type == 'ARMATURE' for m in getattr(o, "modifiers", []))]
        for o in movers:
            o.location.z += dz
        print("SETTLE", ac["kind"], round(dz, 4), flush=True)
        bpy.context.view_layer.update()
    for o in dv.objects:
        o["person"] = ac["kind"]
    sc.frame_set(1)

# 4. props and anything else that moves with shot time, keyed every frame
for i in range(NF):
    f = 1 + i; sc.frame_set(f); bpy.context.view_layer.update()
    si.T = i / max(NF - 1, 1)
    si.run_dyn(si.T, f)

# 5. camera through t = 0, 0.5, 1
import env as EV
def lagr(a, b, c, s):
    return a * (2 * s - 1) * (s - 1) + b * 4 * s * (1 - s) + c * s * (2 * s - 1)
cam = sc.camera
L = [Vector(c["loc"]) for c in cams]; Tg = [Vector(c["tgt"]) for c in cams]
for i in range(NF):
    u = i / max(NF - 1, 1); s = u            # the shots' own moves already ease (E(t)) inside build
    EV.aim(cam, lagr(*L, s), lagr(*Tg, s), cams[0].get("roll", 0.0) or 0.0)
    cam.keyframe_insert("location", frame=1 + i); cam.keyframe_insert("rotation_quaternion", frame=1 + i)
    cam.data.lens = lagr(*(c["lens"] for c in cams), s); cam.data.keyframe_insert("lens", frame=1 + i)
    if cam.data.dof.use_dof:
        f0 = [c["focus"] if c["focus"] else (Vector(c["tgt"]) - Vector(c["loc"])).length for c in cams]
        cam.data.dof.focus_distance = max(0.05, lagr(*f0, s)); cam.data.dof.keyframe_insert("focus_distance", frame=1 + i)

# 6. grade, frame range, motion blur
import grade as G
gr = si.GRADE
G.add_grade(sc, bloom=gr.get("bloom", 0.3), look="cinematic", cine={"sat": gr.get("sat", 1.0), "exposure": gr.get("exposure", 0.0)})
sc.frame_start, sc.frame_end = 1, NF
sc.render.fps = FPS
sc.render.use_motion_blur = True; sc.render.motion_blur_shutter = 0.4
for o in bpy.data.objects:
    if o.name.startswith(("Ocean", "FarSea")):
        o.cycles.use_motion_blur = False

# 7. clipping on the first, middle and last frame (zero clips required)
SID = f"{FILM}{SHOT}"
if si.ACTORS:
    import clipcheck
    clipcheck.OUT = os.path.join(HERE, "out", "clip_anim")
    bad = 0
    for f in sorted({1, max(1, NF // 2), NF}):
        sc.frame_set(f)
        bad += len(clipcheck.check(f"{SID}_f{f:04d}", hand_ok=gr.get("clip_ok", ("floor",))))
    print(f"CLIPRESULT {SID} {bad}", flush=True)
    sc.frame_set(1)
    if bad and os.environ.get("CLIP_STRICT", "1") == "1":
        print("ABORT clipping", SID, flush=True); sys.exit(2)

if os.environ.get("EXPORT"):
    import farm_export
    farm_export.export(os.environ["EXPORT"], SID)
    sys.exit(0)
out = os.path.join(HERE, "out", "frames", SID); os.makedirs(out, exist_ok=True)
sc.render.filepath = os.path.join(out, "f")
if os.environ.get("PCT"):
    sc.render.resolution_percentage = int(os.environ["PCT"])
fr = os.environ.get("FRAMES")
if fr:
    for f in [int(x) for x in fr.split(",")]:
        sc.frame_set(f); sc.render.filepath = os.path.join(out, f"f{f:04d}.png"); bpy.ops.render.render(write_still=True)
else:
    bpy.ops.render.render(animation=True)
print("RENDERED_ANIM", SID, NF, flush=True)
