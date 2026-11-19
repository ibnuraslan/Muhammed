"""Part 4 animated pass (same process as Part 1): build one shot at its VO-retimed length, animate it, check clipping,
then either render it here or export a self-contained farm .blend.

    blender -b --python run_anim.py -- S05            (env: TIMINGS=vo/vo_timings.json, EXPORT=<package dir>)
Motion:
  camera  - the storyboard's own move: the shot's camera is evaluated at t = 0, 0.5 and 1 (shots/board.py) and keyed
            every frame through those three poses with the same smoothstep ease, plus a light handheld sway where the
            shot is handheld (interiors, people);
  people  - live rigs on the storyboard pose (lib/anim.py from Part 1): breathing, weight shift, blinks, clothes and hair
            ride the rig; boots settled on the planking;
  sea     - the FFT ocean advances with the shot clock; in the exterior wides the sea works the ship (heave/roll/pitch);
  graphics- map bands spread and fade, the drift line inks itself and the model ship sails it, the hold vapour thickens.
Nothing moves by itself."""
import os, sys, json, math, subprocess, runpy
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [os.path.join(HERE, "lib"), os.path.join(HERE, "tools"), os.path.join(HERE, "shots")]
argv = sys.argv[sys.argv.index("--") + 1:]
SID = argv[0]
FPS = 24
TIM = json.load(open(os.environ.get("TIMINGS", os.path.join(HERE, "vo", "vo_timings.json"))))
NF = int(TIM[SID]["frames"]); DUR = NF / FPS
from shots_vo import HANDHELD, SHIP_MOTION
B = bpy_bin = os.environ.get("BLENDER", "/opt/blender/blender-5.2.2-linux-x64/blender")

# 1. the camera at t = 0.5 and t = 1 (separate light runs: people are not built)
camfile = lambda t: os.path.join(HERE, "out", "cams", f"{SID}_{t}.json")
os.makedirs(os.path.join(HERE, "out", "cams"), exist_ok=True)
for t in ("0.5", "1.0"):
    if not os.path.exists(camfile(t)) or os.environ.get("RECAM"):
        env = dict(os.environ, CAMDUMP=camfile(t), PREVIEW="0.25"); env.pop("ANIM", None); env.pop("EXPORT", None)
        subprocess.run([bpy_bin, "-b", "--python", os.path.join(HERE, "shots", "board.py"), "--", SID, t], env=env,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
cams = [None, json.load(open(camfile("0.5"))), json.load(open(camfile("1.0")))]

# 2. the shot at t = 0, people live
os.environ["ANIM"] = "1"
sys.argv = [sys.argv[0], "--", SID, "0.0"]
g = runpy.run_path(os.path.join(HERE, "shots", "board.py"), run_name="board_anim")
import bpy
from mathutils import Vector, Matrix
import anim as A, ship, p4
cams[0] = g["CAMS"][0]
sc = bpy.context.scene
cam = sc.camera
ease = lambda u: u * u * (3 - 2 * u)


def lagr(a, b, c, s):                                  # through a (s=0), b (s=0.5), c (s=1)
    return a * (2 * s - 1) * (s - 1) + b * 4 * s * (1 - s) + c * s * (2 * s - 1)


# 3. people (live rigs on the storyboard pose)
for i, ac in enumerate(g["ACTORS"]):
    dv, M, pose = ac["dv"], ac["M"], ac["pose"]
    A.live(dv, M, lambda dv_, M_, pose=pose: pose(dv_.h, dv_, M_, M_.inverted()), ac["look"], DUR, density=0.75 * ac["hair"], seed=i)
    # procedural boots (built by live() on the first pose, in the rig's own frame, not skinned): place them with the
    # man and let them ride the foot bones, so they follow his weight shift
    sc.frame_set(1); bpy.context.view_layer.update()
    for o in list(getattr(dv, "sea_boots", [])):
        if o.parent is None:
            side = "L" if "bootL" in o.name else "R"
            mw = M @ o.matrix_world
            o.parent = dv.h.arm; o.parent_type = 'BONE'; o.parent_bone = f"foot.{side}"
            bpy.context.view_layer.update(); o.matrix_world = mw
    bpy.context.view_layer.update()
    # boots rest on the planking (checked on the first, middle and last frame); the whole rig lifts if needed
    import numpy as np
    Si = ac["SHIP"].inverted(); dg = bpy.context.evaluated_depsgraph_get(); worst = -1.0
    for f in (1, max(1, NF // 2), NF):
        sc.frame_set(f); dg = bpy.context.evaluated_depsgraph_get()
        for o in dv.objects:
            if o.type != 'MESH' or "boot" not in o.name.lower() or o.hide_render:
                continue
            oe = o.evaluated_get(dg); me = oe.to_mesh()
            for v in me.vertices:
                q = Si @ (oe.matrix_world @ v.co)
                s_ = (q.x - ship._ends(1.0)[0]) / (ship._ends(1.0)[1] - ship._ends(1.0)[0])
                hb = max(ship.half_breadth(min(max(s_, 0.0), 1.0), 1.0) - 0.1, 0.1)
                worst = max(worst, ship.zdeck(q.x) + 0.012 * (1 - min(1.0, (q.y / hb) ** 2)) - q.z)
            oe.to_mesh_clear()
    sc.frame_set(1)
    if worst > -0.002:
        up = ac["SHIP"].to_3x3() @ Vector((0, 0, worst + 0.002))
        movers = [dv.h.arm] + [o for o in dv.objects if o.parent is None and not any(m.type == 'ARMATURE' for m in getattr(o, "modifiers", []))]
        print("SETTLE", ac["kind"], round(worst, 4), "m", flush=True)
        if worst > 0.08:
            raise SystemExit(f"settle too large ({worst:.3f} m): something is not riding the rig")
        for o in movers:
            o.location += up
        bpy.context.view_layer.update()
        hd = [c + up[k % 3] for k, c in enumerate(dv.objects[0].get("hands", []))]
        for o in dv.objects:
            o["hands"] = hd
    for o in dv.objects:
        o["person"] = ac["kind"]

# 4. camera: the storyboard move through t = 0, 0.5, 1, eased, keyed every frame (+ handheld sway)
import numpy as np
hh = HANDHELD.get(SID, 0.0); rng = np.random.default_rng(7); ph = rng.uniform(0, 6.28, 4)
c0, c1, c2 = cams
V = lambda k: [Vector(c[k]) for c in (c0, c1, c2)]
L0, L1, L2 = V("loc"); T0, T1, T2 = V("tgt")
for i in range(NF):
    u = i / max(NF - 1, 1); s = ease(u); t = i / FPS
    loc = lagr(L0, L1, L2, s); tgt = lagr(T0, T1, T2, s); roll = c0.get("roll", 0.0) or 0.0
    if hh:
        fwd = (tgt - loc).normalized(); right = fwd.cross(Vector((0, 0, 1))).normalized(); up = right.cross(fwd)
        sway = right * math.sin(0.7 * 6.28 * t + ph[0]) + up * math.sin(0.53 * 6.28 * t + ph[1])
        tgt = tgt + sway * hh * (tgt - loc).length * 0.004
        roll += hh * 0.25 * math.sin(0.37 * 6.28 * t + ph[3])
    import env as EV
    EV.aim(cam, loc, tgt, roll)
    cam.data.lens = lagr(*(c["lens"] for c in cams), s); cam.data.keyframe_insert("lens", frame=1 + i)
    if cam.data.dof.use_dof:
        f0 = [c["focus"] if c["focus"] else (Vector(c["tgt"]) - Vector(c["loc"])).length for c in cams]
        cam.data.dof.focus_distance = max(0.05, lagr(*f0, s)); cam.data.dof.keyframe_insert("focus_distance", frame=1 + i)
    cam.keyframe_insert("location", frame=1 + i); cam.keyframe_insert("rotation_quaternion", frame=1 + i)

# 5. the sea, and the ship it works (exterior wides only: aboard, the camera rides with her)
A.ocean_time(DUR)
if SID in SHIP_MOTION:
    root = bpy.data.objects.get("MC_root")
    if root:
        bpy.context.view_layer.update()
        Ri = root.matrix_world.inverted()
        for o in list(bpy.data.objects):
            if o.parent is not None or o is root or o.type in ('LIGHT', 'CAMERA') or o.name.startswith(("Ocean", "FarSea", "SeaHaze", "SantaMaria")):
                continue
            q = Ri @ o.matrix_world.to_translation()
            if abs(q.x) < ship.L / 2 + 2 and abs(q.y) < ship.B / 2 + 1 and -4 < q.z < 35:
                mw = o.matrix_world.copy(); o.parent = root; o.matrix_world = mw
        A.ship_motion(root, DUR, seed=3)

# 6. graphics over the shot
if g["BANDS"]:
    for b in g["BANDS"]:
        o, fade, k, n = b["obj"], b["fade"], b["k"], b["n"]
        for i in range(NF):
            u = i / max(NF - 1, 1); phv = (u + k / n) % 1.0
            sc_ = (0.02 + 0.16 * phv) / 0.18; o.scale = (sc_, sc_, 1.0); o.keyframe_insert("scale", frame=1 + i)
            fade.inputs[1].default_value = 1 - phv; fade.inputs[1].keyframe_insert("default_value", frame=1 + i)
        # keys on every frame; at the wrap the band is fully faded (fade 0), so sub-frame blending there is invisible
if g["DRIFT"] and SID == "S27":
    d = g["DRIFT"]
    for i in range(NF):
        u = ease(i / max(NF - 1, 1)); p, dv_ = d["at"](u); ang = math.atan2(dv_.y, dv_.x); k = d["k"]
        d["root"].matrix_world = Matrix.Translation(p + Vector((0, 0, 0.0005))) @ Matrix.Rotation(ang, 4, 'Z') @ Matrix.Diagonal((k, k, k, 1))
        d["root"].keyframe_insert("location", frame=1 + i); d["root"].keyframe_insert("rotation_euler", frame=1 + i)
        for o, ud in d["dashes"]:
            o.hide_render = ud > max(u, 2 / 60) + 1e-6; o.keyframe_insert("hide_render", frame=1 + i)
vm = bpy.data.materials.get("vapor")
if vm and SID == "S05":
    mr = vm.node_tree.nodes.get("Map Range")
    for i, u in ((0, 0.0), (NF - 1, 1.0)):
        v = 0.4 + 0.6 * u
        mr.inputs['To Min'].default_value = 1.2 * v; mr.inputs['To Max'].default_value = 5.0 * v
        mr.inputs['To Min'].keyframe_insert("default_value", frame=1 + i); mr.inputs['To Max'].keyframe_insert("default_value", frame=1 + i)

# 7. grade, frame range, motion blur
import grade as G
gr = g["GRADE"]
G.add_grade(sc, bloom=gr.get("bloom", 0.3), look="cinematic", cine={"sat": gr.get("sat", 1.0), "exposure": gr.get("exposure", 0.0)})
sc.frame_start, sc.frame_end = 1, NF
sc.render.fps = FPS
sc.render.use_motion_blur = True; sc.render.motion_blur_shutter = 0.4
for o in bpy.data.objects:
    if o.name.startswith(("Ocean", "FarSea")) or o.name.endswith(("_hull", "_deck")) or "_sail" in o.name:
        o.cycles.use_motion_blur = False

# 8. clipping check on the first, middle and last frame (zero clips required)
if any("person" in o for o in bpy.data.objects):
    import clipcheck
    clipcheck.OUT = os.path.join(HERE, "out", "clip_anim")
    bad = 0
    for f in sorted({1, max(1, NF // 2), NF}):
        sc.frame_set(f)
        bad += len(clipcheck.check(f"{SID}_f{f:04d}", hand_ok=("rod", "spear", "pump", "brake", "rail", "cap", "bulwark", "lantern", "deck")))
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
bpy.ops.render.render(animation=True)
print("RENDERED_ANIM", SID, NF, flush=True)
