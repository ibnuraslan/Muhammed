"""Farm packaging, step 2: MASTER.blend at the root of the delivery folder - scene "MASTER" plays every shot (scene
strips linked from //shots/Sxx.blend) end to end in VO order. Colour management is copied from the shots, a scene
camera is set (RenderStreet refuses a file without one). FARM_DELIVERY_RULES.md 1, 4, 7, 8.

    blender -b --factory-startup --python tools/make_master.py -- P1 <PKG dir>
"""
import os, sys, json
import bpy

args = sys.argv[sys.argv.index("--") + 1:]
PART, PKG = args[0], os.path.abspath(args[1])
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
tim = json.load(open(os.path.join(ROOT, "vo", PART + "_timing.json")))
ONLY = set(filter(None, os.environ.get("ONLY", "").split(",")))      # test builds: only these strips, at their real frames
NAME = os.environ.get("MASTERNAME", "MASTER.blend")
bpy.ops.wm.read_factory_settings(use_empty=True)
master = bpy.context.scene
master.name = "MASTER"
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(PKG, NAME))     # so the library paths can be relative
se = master.sequence_editor_create()
strips = se.strips if hasattr(se, "strips") else se.sequences
frame = 1
first = None
for o in tim["shots"]:
    sid = o["shot"]
    if ONLY and sid not in ONLY:
        frame += o["frames"]; continue
    path = os.path.join(PKG, "shots", sid + ".blend")
    with bpy.data.libraries.load(path, link=True, relative=True) as (src, dst):
        dst.scenes = [n for n in src.scenes if n == sid] or src.scenes[:1]
    sc = dst.scenes[0]
    first = first or sc
    n = sc.frame_end - sc.frame_start + 1
    assert n == o["frames"], (sid, n, o["frames"])
    assert frame == o["start"], (sid, frame, o["start"])
    st = strips.new_scene(name=sid, scene=sc, channel=1, frame_start=frame)
    if hasattr(st, "scene_input"):
        st.scene_input = 'CAMERA'
    master.timeline_markers.new(sid, frame=frame)
    print(f"[master] {sid} frames {frame}-{frame + n - 1}", flush=True)
    frame += n
master.frame_start, master.frame_end = 1, frame - 1
assert master.frame_end == tim["frames_total"], (master.frame_end, tim["frames_total"])
# render settings (the farm reads these from the master scene)
r = master.render
r.resolution_x, r.resolution_y, r.resolution_percentage = 2560, 1440, 100
r.fps, r.fps_base = 24, 1.0
r.engine = 'CYCLES'
master.cycles.samples = 64; master.cycles.use_adaptive_sampling = True; master.cycles.use_denoising = True
master.cycles.denoiser = 'OPENIMAGEDENOISE'
r.use_motion_blur = True
r.use_sequencer = True
r.use_compositing = False                     # each shot scene applies its own grade
r.film_transparent = False
r.filepath = "//frames/"
r.image_settings.file_format = 'PNG'; r.image_settings.color_mode = 'RGB'; r.image_settings.color_depth = '8'
# colour management: exactly the shots'
vs, fvs = master.view_settings, first.view_settings
key = lambda s: (s.view_settings.view_transform, s.view_settings.look, round(s.view_settings.exposure, 4), round(s.view_settings.gamma, 4),
                 s.display_settings.display_device, s.sequencer_colorspace_settings.name)
for s_ in [st.scene for st in strips]:
    assert key(s_) == key(first), ("colour management differs between shots", s_.name, key(s_), key(first))
master.display_settings.display_device = first.display_settings.display_device
vs.view_transform = fvs.view_transform
vs.look = fvs.look
vs.exposure = fvs.exposure
vs.gamma = fvs.gamma
vs.use_curve_mapping = fvs.use_curve_mapping
master.sequencer_colorspace_settings.name = first.sequencer_colorspace_settings.name
# a scene camera (never used for the picture: the sequencer drives the render)
cam = bpy.data.objects.new("MasterCam", bpy.data.cameras.new("MasterCam"))
master.collection.objects.link(cam); master.camera = cam
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(PKG, NAME), compress=True, relative_remap=True)
print("[master] saved", os.path.join(PKG, NAME), "frames 1 -", master.frame_end,
      "| view", vs.view_transform, vs.look, vs.exposure, vs.gamma, master.display_settings.display_device,
      master.sequencer_colorspace_settings.name, flush=True)
