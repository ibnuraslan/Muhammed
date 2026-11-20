"""Small MASTER.blend for Part 1: scene MASTER whose Video Sequencer plays every shot as a Scene strip LINKED from
//shots/<id>.blend, in VO order, frames 1-3788, 2560x1440 24 fps, Cycles 64 spp + OIDN, output //frames/MASTER_####.png.

    blender -b --factory-startup --python tools/build_master_link.py -- <PKG_DIR>      (writes <PKG_DIR>/MASTER.blend)"""
import bpy, os, sys, json
pkg = os.path.abspath(sys.argv[sys.argv.index("--") + 1:][0])
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
order = list(json.load(open(os.path.join(HERE, "vo", "vo_timings.json"))))
out = os.path.join(pkg, "MASTER.blend")
master = bpy.context.scene; master.name = "MASTER"
bpy.ops.wm.save_as_mainfile(filepath=out)                     # saved first: library paths are stored relative (//shots/...)
se = master.sequence_editor_create(); f = 1
for sid in order:
    lib = os.path.join(pkg, "shots", f"{sid}.blend")
    with bpy.data.libraries.load(lib, link=True, relative=True) as (src, dst):
        dst.scenes = ["Scene"]
    sc = dst.scenes[0]
    n = sc.frame_end - sc.frame_start + 1
    st = se.strips.new_scene(name=sid, scene=sc, channel=1, frame_start=f); st.scene_input = 'CAMERA'
    f += n
r = master.render
master.frame_start, master.frame_end = 1, f - 1
r.fps, r.fps_base = 24, 1.0
r.resolution_x, r.resolution_y, r.resolution_percentage = 2560, 1440, 100
r.engine = 'CYCLES'; master.cycles.samples = 64; master.cycles.use_adaptive_sampling = True
master.cycles.adaptive_threshold = 0.03; master.cycles.use_denoising = True
r.use_sequencer = True
# colour management must match the shots, or the strips come out washed out (the sequencer output uses MASTER's view)
shot0 = [s for s in bpy.data.scenes if s.name != "MASTER"][0]
for k in ("view_transform", "look", "exposure", "gamma"):
    setattr(master.view_settings, k, getattr(shot0.view_settings, k))
master.display_settings.display_device = shot0.display_settings.display_device
master.sequencer_colorspace_settings.name = shot0.sequencer_colorspace_settings.name
r.image_settings.file_format = 'PNG'; r.image_settings.color_mode = 'RGB'; r.image_settings.color_depth = '16'
r.filepath = "//frames/MASTER_"; r.use_overwrite = False; r.use_placeholder = True
# a camera in MASTER: farms (RenderStreet) refuse a scene without one; the sequencer output ignores it
cd = bpy.data.cameras.new("MASTER_cam"); co = bpy.data.objects.new("MASTER_cam", cd)
master.collection.objects.link(co); co.location = (0, -10, 2); master.camera = co
bpy.ops.wm.save_as_mainfile(filepath=out, compress=True)
print("MASTERLINK", out, master.frame_end, [l.filepath for l in bpy.data.libraries][:2], len(bpy.data.libraries),
      round(os.path.getsize(out) / 1e3), "KB", flush=True)
