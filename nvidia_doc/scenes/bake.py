"""Bake a scene move into a self-contained .blend for rendering elsewhere.

  python scenes/bake.py home behind --seconds 3.25 --out out/blend/intro
  -> out/blend/intro/home_behind.blend   (every frame keyed: camera, focus, lens, rig, phone, props)
     out/blend/intro/home_behind_ui/f0001.png ...   (phone screen image sequence, relative path)

Textures are packed into the .blend. Render settings are stored (Cycles, 1920x816, 24 fps, denoise, motion blur);
open the file and render the animation, or: blender -b home_behind.blend -a
"""
import os, sys, shutil, importlib
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bpy
import kit
from common import reset, camera

arg = lambda k, d: type(d)(sys.argv[sys.argv.index(k) + 1]) if k in sys.argv else d
scene_name, move = sys.argv[1], sys.argv[2]
FPS = 24
SECONDS = arg('--seconds', 3.0)
OUTDIR = os.path.abspath(arg('--out', os.path.join(HERE, "..", "out", "blend")))
SAMPLES = arg('--samples', 128)
os.makedirs(OUTDIR, exist_ok=True)
name = arg('--name', f"{scene_name}_{move}")

mod = importlib.import_module("sc_" + scene_name)
s = reset(res=kit.RES, samples=SAMPLES, exposure=getattr(mod, "EXPOSURE", 0.0))
s.cycles.max_bounces = getattr(mod, "BOUNCES", 8)
variant = getattr(mod, "VARIANT_FOR", {}).get(move, None)
ctx = mod.build(variant)
spec = mod.MOVES[move]
cam = camera((0, 0, 0), (0, 1, 0), lens=35, dof_dist=3.0, fstop=spec.get("dof", 2.8) or 2.8)
cam.data.dof.use_dof = bool(spec.get("dof"))
ctx["cam"] = cam
# every frame must pose the rigs from the SAME starting pose the build left them in: some anim functions rotate
# bones relative to their current pose (Human.rot), so without this each frame adds onto the last one and a
# 14-degree head tilt becomes a spinning head over the shot. A single still never shows it; a bake does.
_rest = {(a.name, pb.name): (pb.location.copy(), pb.rotation_quaternion.copy(), pb.rotation_euler.copy(), pb.scale.copy())
         for a in bpy.data.objects if a.type == 'ARMATURE' for pb in a.pose.bones}
def restore_pose():
    for a in bpy.data.objects:
        if a.type != 'ARMATURE':
            continue
        for pb in a.pose.bones:
            r = _rest.get((a.name, pb.name))
            if r:
                pb.location, pb.rotation_quaternion, pb.rotation_euler, pb.scale = r
    bpy.context.view_layer.update()
if spec.get("title"):                          # chapter title card inside the shot (fades by frame-driven driver)
    import title_card
    small, big, f_in, f_out = spec["title"][:4]
    title_card.add_title(cam, small, big, f_in, f_out, scrim=spec["title"][4] if len(spec["title"]) > 4 else 0.36)

n = int(round(SECONDS * FPS))
s.frame_start, s.frame_end = 1, n
s.render.fps = FPS
s.render.resolution_percentage = 100
s.cycles.use_denoising = True
s.render.use_motion_blur = True
s.render.motion_blur_shutter = 0.5
s.render.filepath = f"//render/{name}_"
s.render.image_settings.file_format = 'PNG'

# objects whose transforms we key every frame
movers = [o for o in bpy.data.objects if o.type in ('MESH', 'EMPTY', 'LIGHT', 'CURVE') and o.name != cam.name]
arms = [o for o in bpy.data.objects if o.type == 'ARMATURE']
ui_dir = os.path.join(OUTDIR, name + "_ui")
screen_tex = None
if "screen_mat" in ctx:
    screen_tex = ctx["screen_mat"].node_tree.nodes["UI"]
    os.makedirs(ui_dir, exist_ok=True)

def state(o):
    return (tuple(round(v, 6) for v in o.location), tuple(round(v, 6) for v in o.rotation_euler),
            tuple(round(v, 6) for v in o.rotation_quaternion), tuple(round(v, 6) for v in o.scale))
# find what moves: compare three sample times, then key only those objects every frame
snap = []
for t in [k / 8 for k in range(9)]:      # nine samples: catch motion that happens only mid-shot (doors)
    restore_pose(); kit.apply_cam(cam, ctx, spec, t); bpy.context.view_layer.update()
    snap.append({o.name: state(o) for o in movers})
movers = [o for o in movers if len({sn[o.name] for sn in snap}) > 1]
print("[bake] moving objects:", [o.name for o in movers][:20], len(movers), flush=True)

prev_q, prev_e = {}, {}
# key every STEP frames (Blender interpolates between keys); per-frame UI image sequences need every frame
STEP = 1 if screen_tex is not None else int(os.environ.get("BAKE_STEP", arg('--step', 2)))
key_frames = list(range(1, n + 1, STEP))
if key_frames[-1] != n:
    key_frames.append(n)
for f in key_frames:
    t = (f - 1) / max(n - 1, 1)
    restore_pose(); kit.apply_cam(cam, ctx, spec, t)
    bpy.context.view_layer.update()
    if "__cam__" in prev_e:
        e = cam.rotation_euler.copy(); e.make_compatible(prev_e["__cam__"]); cam.rotation_euler = e
    prev_e["__cam__"] = cam.rotation_euler.copy()
    for prop in ("location", "rotation_euler"):
        cam.keyframe_insert(prop, frame=f)
    cam.data.keyframe_insert("lens", frame=f)
    cam.data.dof.keyframe_insert("focus_distance", frame=f)
    for a in arms:
        a.keyframe_insert("location", frame=f)
        for pb in a.pose.bones:
            if pb.rotation_mode == 'QUATERNION':          # keep q and -q from alternating between frames: the same pose,
                q = pb.rotation_quaternion            # but interpolating across the sign flip spins the bone through
                pq = prev_q.get((a.name, pb.name))    # wild angles on motion-blur subframes (ghost limbs)
                if pq is not None and pq.dot(q) < 0:
                    pb.rotation_quaternion = -q
                prev_q[(a.name, pb.name)] = pb.rotation_quaternion.copy()
            pb.keyframe_insert("location", frame=f)
            pb.keyframe_insert("rotation_quaternion" if pb.rotation_mode == 'QUATERNION' else "rotation_euler", frame=f)
    for o in movers:
        if o.rotation_mode == 'QUATERNION':
            pq = prev_q.get(o.name)
            if pq is not None and pq.dot(o.rotation_quaternion) < 0:
                o.rotation_quaternion = -o.rotation_quaternion
            prev_q[o.name] = o.rotation_quaternion.copy()
        else:
            pe = prev_e.get(o.name)
            if pe is not None:
                e = o.rotation_euler.copy(); e.make_compatible(pe); o.rotation_euler = e
            prev_e[o.name] = o.rotation_euler.copy()
        o.keyframe_insert("location", frame=f)
        o.keyframe_insert("rotation_quaternion" if o.rotation_mode == 'QUATERNION' else "rotation_euler", frame=f)
        o.keyframe_insert("scale", frame=f)                    # growing strokes / marks animate by scale
    if screen_tex is not None and screen_tex.image is not None and screen_tex.image.filepath:
        shutil.copyfile(bpy.path.abspath(screen_tex.image.filepath), os.path.join(ui_dir, f"f{f:04d}.png"))
    print(f"[bake] {name} frame {f}/{n}", flush=True)

for a in arms:                                # step between keys: no interpolation drift on baked poses
    if a.animation_data and a.animation_data.action:
        for fc in getattr(a.animation_data.action, "fcurves", []):
            for kp in fc.keyframe_points:
                kp.interpolation = 'LINEAR'

for im in bpy.data.images:                    # pack every still texture into the .blend
    if im.source == 'FILE' and im.packed_file is None and im.filepath and "ui_frames" not in im.filepath:
        try:
            im.pack()
        except Exception as e:
            print("[bake] could not pack", im.name, e)

if screen_tex is not None:                    # phone screen = image sequence next to the .blend
    img = bpy.data.images.load(os.path.join(ui_dir, "f0001.png"))
    img.source = 'SEQUENCE'; img.colorspace_settings.name = 'sRGB'
    img.filepath = "//" + os.path.relpath(os.path.join(ui_dir, "f0001.png"), OUTDIR)
    screen_tex.image = img
    screen_tex.image_user.frame_duration = n; screen_tex.image_user.frame_start = 1
    screen_tex.image_user.frame_offset = 0; screen_tex.image_user.use_auto_refresh = True
    for im in list(bpy.data.images):          # the per-frame UI stills used while baking are not needed
        if im is not img and "ui_frames" in im.filepath:
            bpy.data.images.remove(im)

s.frame_set(1)
path = os.path.join(OUTDIR, name + ".blend")
bpy.ops.wm.save_as_mainfile(filepath=path, compress=True, relative_remap=True)
print("[bake] saved", path, flush=True)
