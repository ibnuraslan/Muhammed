"""Part 3 animated shot -> one keyframed .blend for the render farm (or a local animation render).

    TIMINGS=vo/vo_timings.json EXPORT=out/farm/mary_celeste_p3 blender -b --python anim_export.py -- p3_07

Every shot in shots.py is a function of t (0..1) that builds its set, people, props and camera. Here the shot is
built at probe times every KEYDT seconds with the people kept as live rigs ("probe"), and everything that changes is
recorded: each object's transform, every pose bone of every rig, camera lens and focus, light energies, the FFT sea's
clock, and the shape of meshes that bend (ropes, the lowering line, the pump water, the pencil route). The shot is then
built once more at t = 0 ("live": hair grown, corneas, eyes) and all of that is keyed onto it (Bezier between probes,
linear for the sea clock). Nothing is cached or simulated: the .blend renders its frame range as it stands.
Zero clips are required: lib/clipcheck runs on the first, middle and last frame before export."""
import os, sys, math, json, time
HERE = os.path.dirname(os.path.abspath(__file__))
SC = os.path.join(HERE, "..", "mary_celeste_3d", "scenes")
for p in (os.path.join(HERE, "lib"), SC, HERE, os.path.join(HERE, "tools")):
    if p not in sys.path:
        sys.path.insert(0, p)
import numpy as np
import common as C
import bpy
from mathutils import Matrix, Vector
import crew, shots as S

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
SID = argv[0]
FPS = 24
FAST = {"p3_03": 0.2, "p3_05": 0.25, "p3_07": 0.125, "p3_08": 0.25, "p3_11": 0.25, "p3_12": 0.25, "p3_22": 0.125, "p3_18": 0.25,
        "p3_20": 0.25, "p3_37": 0.25}          # shots with a quick repeated action (pumping, hammering, hauling, writing)
KEYDT = float(os.environ.get("KEYDT", FAST.get(SID, 0.5)))
dur = S.SHOTS[SID]["dur"]
if os.environ.get("TIMINGS"):
    dur = float(json.load(open(os.environ["TIMINGS"])).get(SID, dur))
NF = max(1, int(round(dur * FPS)))
times = sorted(set([min(k * KEYDT, dur) for k in range(int(dur / KEYDT) + 1)] + [dur]))
SHAPE_MAX = 40000           # meshes up to this many vertices may be keyed as shapes (ropes, lines, water)


def build(t, mode):
    C.reset()
    crew.MODE = mode
    info = S.build(SID, t / dur if dur > 0 else 0.0)
    bpy.context.view_layer.update()
    return info


def snapshot():
    snap = dict(obj={}, pose={}, cam={}, light={}, ocean={}, shape={})
    for o in bpy.data.objects:
        snap["obj"][o.name] = [list(r) for r in o.matrix_basis]
        if o.type == 'ARMATURE':
            snap["pose"][o.name] = {pb.name: [list(r) for r in pb.matrix_basis] for pb in o.pose.bones}
        elif o.type == 'CAMERA':
            snap["cam"][o.name] = (o.data.lens, o.data.dof.focus_distance)
        elif o.type == 'LIGHT':
            snap["light"][o.name] = o.data.energy
        elif o.type == 'MESH':
            md = o.modifiers.get("Ocean")
            if md is not None:
                snap["ocean"][o.name] = md.time
            if "person" not in o and (o.parent is None or o.parent.type != 'ARMATURE'):
                n = len(o.data.vertices)
                if 2 <= n <= SHAPE_MAX:
                    co = np.empty(n * 3, np.float32); o.data.vertices.foreach_get("co", co)
                    snap["shape"][o.name] = co
    return snap


def key_obj(o, Mb, f):
    o.matrix_basis = Matrix(Mb)
    o.keyframe_insert("location", frame=f)
    if o.rotation_mode == 'QUATERNION':
        o.keyframe_insert("rotation_quaternion", frame=f)
    else:
        o.keyframe_insert("rotation_euler", frame=f)
    o.keyframe_insert("scale", frame=f)


def differs(a, b, eps=1e-5):
    return np.abs(np.asarray(a, np.float64) - np.asarray(b, np.float64)).max() > eps


t0 = time.time()
probes = []
for tk in times:
    build(tk, "probe")
    probes.append((tk, snapshot()))
    print(f"PROBE {SID} t={tk:.2f}s  {time.time() - t0:.0f}s", flush=True)

info = build(0.0, "live")
sc = bpy.context.scene
base = probes[0][1]
try:
    bpy.context.preferences.edit.keyframe_new_interpolation_type = 'BEZIER'
except Exception:
    pass
frames = [1 + tk * FPS for tk, _ in probes]
nkeys = 0
# objects (local transforms), skipping anything that never moves
for name in base["obj"]:
    o = bpy.data.objects.get(name)
    if o is None:
        continue
    seq = [p["obj"].get(name) for _, p in probes]
    if any(s is None for s in seq) or not any(differs(s, seq[0]) for s in seq):
        continue
    if o.type == 'ARMATURE' or "person" not in o or o.parent is None:
        for f, Mb in zip(frames, seq):
            key_obj(o, Mb, f); nkeys += 1
# rigs: every pose bone
for an, bones in base["pose"].items():
    arm = bpy.data.objects.get(an)
    if arm is None:
        continue
    for pb in arm.pose.bones:
        pb.rotation_mode = 'QUATERNION'
    for f, (_, p) in zip(frames, probes):
        pose = p["pose"].get(an, {})
        for pb in arm.pose.bones:
            if pb.name in pose:
                pb.matrix_basis = Matrix(pose[pb.name])
                pb.keyframe_insert("rotation_quaternion", frame=f); pb.keyframe_insert("location", frame=f)
                pb.keyframe_insert("scale", frame=f); nkeys += 1
# camera lens / focus, lights
for cn, v0 in base["cam"].items():
    cam = bpy.data.objects.get(cn)
    for f, (_, p) in zip(frames, probes):
        lens, foc = p["cam"].get(cn, v0)
        cam.data.lens = lens; cam.data.keyframe_insert("lens", frame=f)
        if cam.data.dof.use_dof:
            cam.data.dof.focus_distance = foc; cam.data.dof.keyframe_insert("focus_distance", frame=f)
for ln, e0 in base["light"].items():
    seq = [p["light"].get(ln, e0) for _, p in probes]
    if max(seq) - min(seq) > 1e-4:
        L = bpy.data.objects[ln].data
        for f, e in zip(frames, seq):
            L.energy = e; L.keyframe_insert("energy", frame=f)
# the sea's clock (linear)
for on, t_0 in base["ocean"].items():
    md = bpy.data.objects[on].modifiers["Ocean"]
    for f, (_, p) in zip(frames, probes):
        md.time = p["ocean"].get(on, t_0); md.keyframe_insert("time", frame=f)
    fc = bpy.data.objects[on].animation_data.action
    try:
        for cu in fc.fcurves:
            for kp in cu.keyframe_points:
                kp.interpolation = 'LINEAR'
    except Exception:
        pass
# meshes that bend: one shape key per probe, each at 1 on its own frame and 0 on the neighbours
nshape = 0
for mn, co0 in base["shape"].items():
    o = bpy.data.objects.get(mn)
    if o is None or o.type != 'MESH':
        continue
    seq = [p["shape"].get(mn) for _, p in probes]
    if any(s is None or len(s) != len(co0) for s in seq) or not any(differs(s, co0, 1e-4) for s in seq):
        continue
    if len(o.data.vertices) * 3 != len(co0):
        continue
    o.shape_key_add(name="Basis", from_mix=False)
    keys = []
    for i, s in enumerate(seq):
        k = o.shape_key_add(name=f"t{i}", from_mix=False); k.data.foreach_set("co", s); keys.append(k)
    for i, k in enumerate(keys):
        for j, f in enumerate(frames):
            k.value = 1.0 if i == j else 0.0
            k.keyframe_insert("value", frame=f)
    nshape += 1
print(f"KEYED {SID}: {nkeys} transform keys, {nshape} bending meshes, {len(frames)} probes, frames 1-{NF}", flush=True)

sc.frame_start, sc.frame_end = 1, NF
sc.render.fps = FPS
sc.frame_set(1)
def retag_hands():
    """The clip check forgives contacts at the hands (a grip): give it the wrists/knuckles at THIS frame."""
    bpy.context.view_layer.update()
    for arm in [o for o in bpy.data.objects if o.type == 'ARMATURE']:
        pts = []
        for sd in ("L", "R"):
            for b in (f"wrist.{sd}", f"finger3-1.{sd}"):
                pb = arm.pose.bones.get(b)
                if pb is not None:
                    pts += list(arm.matrix_world @ pb.head)
        name = arm.name[:-4] if arm.name.endswith("_rig") else arm.name
        for o in bpy.data.objects:
            if o.get("person") == name:
                o["hands"] = pts


# zero clips at the first, middle and last frame and at every probe
if any("person" in o for o in bpy.data.objects):
    import clipcheck
    clipcheck.OUT = os.path.join(HERE, "out", "clip")
    bad = 0
    for f in sorted({1, max(1, NF // 2), NF} | {int(round(fr)) for fr in frames if fr <= NF}):
        sc.frame_set(f); retag_hands(); bad += len(clipcheck.check(f"{SID}_anim_f{f:04d}"))
    print(f"CLIPRESULT {SID} {bad}", flush=True)
    sc.frame_set(1)
    if bad and os.environ.get("CLIP_STRICT", "1") == "1":
        print("ABORT: clipping in", SID, flush=True); sys.exit(2)
# the house grade in the compositor, motion blur on camera and people (not the FFT sea)
import grade as G
G.add_grade(sc, bloom=info.get("bloom", 0.3), look="cinematic", cine=info.get("cine"))
sc.render.use_motion_blur = os.environ.get("MBLUR", "1") == "1"; sc.render.motion_blur_shutter = 0.4
for o in bpy.data.objects:
    if o.name.startswith(("Ocean", "FarSea")) or o.name.endswith(("_hull", "_deck")):
        o.cycles.use_motion_blur = False
if os.environ.get("EXPORT"):
    import farm_export
    farm_export.export(os.environ["EXPORT"], SID)
    sys.exit(0)
out = os.path.join(HERE, "out", "frames", SID); os.makedirs(out, exist_ok=True)
sc.render.filepath = os.path.join(out, "f")
sc.render.use_overwrite = False; sc.render.use_placeholder = True
if os.environ.get("RENDER_FRAMES"):
    a, b = [int(x) for x in os.environ["RENDER_FRAMES"].split(":")]
    sc.frame_start, sc.frame_end = a, b
bpy.ops.render.render(animation=True)
print("RENDERED_ANIM", SID, sc.frame_start, sc.frame_end, flush=True)
