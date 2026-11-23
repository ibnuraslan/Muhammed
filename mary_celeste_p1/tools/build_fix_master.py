"""MASTER.blend for a P1 FIX package: each fixed shot as a Scene strip linked from //shots/<id>.blend, placed at its
EXACT original Part 1 frame range (from the VO timings), so the rendered frames are numbered like the Part 1 master and
overlay 1:1. Scene camera set, colour management copied from the shots, 2560x1440 24 fps, Cycles 64 spp + OIDN.
Frames between the fixed shots hold no strip and render black (instantly); only the listed ranges are used.

    blender -b --factory-startup --python tools/build_fix_master.py -- <PKG_DIR> S11 S13 ...   (writes <PKG_DIR>/MASTER.blend)"""
import bpy, os, sys, json
a = sys.argv[sys.argv.index("--") + 1:]
pkg = os.path.abspath(a[0]); ids = a[1:]
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
tim = json.load(open(os.path.join(HERE, "vo", "vo_timings.json")))
rng = {}; f = 1
for sid, d in tim.items():
    n = int(round(d * 24)); rng[sid] = (f, f + n - 1); f += n
out = os.path.join(pkg, "MASTER.blend")
master = bpy.context.scene; master.name = "MASTER"
bpy.ops.wm.save_as_mainfile(filepath=out)
se = master.sequence_editor_create(); placed = []
for sid in ids:
    with bpy.data.libraries.load(os.path.join(pkg, "shots", f"{sid}.blend"), link=True, relative=True) as (src, dst):
        dst.scenes = ["Scene"]
    sc = dst.scenes[0]; s0, s1 = rng[sid]
    assert sc.frame_end - sc.frame_start + 1 == s1 - s0 + 1, (sid, sc.frame_end, s1 - s0 + 1)
    st = se.strips.new_scene(name=sid, scene=sc, channel=1, frame_start=s0); st.scene_input = 'CAMERA'
    placed.append((sid, s0, s1))
shot0 = [s for s in bpy.data.scenes if s.name != "MASTER"][0]
for k in ("view_transform", "look", "exposure", "gamma"):
    setattr(master.view_settings, k, getattr(shot0.view_settings, k))
master.display_settings.display_device = shot0.display_settings.display_device
master.sequencer_colorspace_settings.name = shot0.sequencer_colorspace_settings.name
r = master.render
master.frame_start, master.frame_end = min(p[1] for p in placed), max(p[2] for p in placed)
r.fps, r.fps_base = 24, 1.0
r.resolution_x, r.resolution_y, r.resolution_percentage = 2560, 1440, 100
r.engine = 'CYCLES'; master.cycles.samples = 64; master.cycles.use_adaptive_sampling = True
master.cycles.adaptive_threshold = 0.03; master.cycles.use_denoising = True
r.use_sequencer = True
r.image_settings.file_format = 'PNG'; r.image_settings.color_mode = 'RGB'; r.image_settings.color_depth = '16'
r.filepath = "//frames/P1_"; r.use_overwrite = False; r.use_placeholder = True
cd = bpy.data.cameras.new("MASTER_cam"); co = bpy.data.objects.new("MASTER_cam", cd)
master.collection.objects.link(co); co.location = (0, -10, 2); master.camera = co
bpy.ops.wm.save_as_mainfile(filepath=out, compress=True)
print("FIXMASTER", out, master.frame_start, master.frame_end, placed, master.view_settings.look, flush=True)
