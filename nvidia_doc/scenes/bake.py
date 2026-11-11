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
name = f"{scene_name}_{move}"

mod = importlib.import_module("sc_" + scene_name)
s = reset(res=kit.RES, samples=SAMPLES, exposure=getattr(mod, "EXPOSURE", 0.0))
s.cycles.max_bounces = getattr(mod, "BOUNCES", 8)
variant = getattr(mod, "VARIANT_FOR", {}).get(move, None)
ctx = mod.build(variant)
spec = mod.MOVES[move]
cam = camera((0, 0, 0), (0, 1, 0), lens=35, dof_dist=3.0, fstop=spec.get("dof", 2.8) or 2.8)
cam.data.dof.use_dof = bool(spec.get("dof"))
ctx["cam"] = cam
if spec.get("title"):                          # chapter title card inside the shot (fades by frame-driven driver)
    import title_card
    small, big, f_in, f_out = spec["title"]
    title_card.add_title(cam, small, big, f_in, f_out)

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
            tuple(round(v, 6) for v in o.rotation_quaternion))
# find what moves: compare three sample times, then key only those objects every frame
snap = []
for t in (0.0, 0.5, 1.0):
    kit.apply_cam(cam, ctx, spec, t); bpy.context.view_layer.update()
    snap.append({o.name: state(o) for o in movers})
movers = [o for o in movers if len({sn[o.name] for sn in snap}) > 1]
print("[bake] moving objects:", [o.name for o in movers][:20], len(movers), flush=True)

for f in range(1, n + 1):
    t = (f - 1) / max(n - 1, 1)
    kit.apply_cam(cam, ctx, spec, t)
    bpy.context.view_layer.update()
    for prop in ("location", "rotation_euler"):
        cam.keyframe_insert(prop, frame=f)
    cam.data.keyframe_insert("lens", frame=f)
    cam.data.dof.keyframe_insert("focus_distance", frame=f)
    for a in arms:
        a.keyframe_insert("location", frame=f)
        for pb in a.pose.bones:
            pb.keyframe_insert("location", frame=f)
            pb.keyframe_insert("rotation_quaternion" if pb.rotation_mode == 'QUATERNION' else "rotation_euler", frame=f)
    for o in movers:
        o.keyframe_insert("location", frame=f)
        o.keyframe_insert("rotation_quaternion" if o.rotation_mode == 'QUATERNION' else "rotation_euler", frame=f)
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
