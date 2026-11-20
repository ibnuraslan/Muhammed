"""MASTER.blend for the farm: a small file whose MASTER scene's Video Sequencer holds Scene strips LINKED from
//shots/Sxx.blend (each shot packed on its own), in voice-over order at the VO times. Rendering MASTER renders Part 2.

    blender -b --factory-startup --python tools/build_master_linked.py -- <folder with shots/>"""
import os, sys, json
import bpy

ROOT = os.path.abspath(sys.argv[sys.argv.index("--") + 1:][0])
P2 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, P2)
import shots
T = json.load(open(os.path.join(P2, "vo", "vo_timings.json")))
OUT = os.path.join(ROOT, "MASTER.blend")

master = bpy.context.scene
master.name = "MASTER"
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)
bpy.ops.wm.save_as_mainfile(filepath=OUT)                 # saved first so library paths can be relative (//shots/...)
ed = master.sequence_editor_create()
for sid, *_ in shots.SHOTS:
    path = os.path.join(ROOT, "shots", f"S{sid}.blend")
    with bpy.data.libraries.load(path, link=True, relative=True) as (src, dst):
        dst.scenes = [src.scenes[0]]
    sc = dst.scenes[0]
    t = T[sid]
    st = ed.strips.new_scene(name=f"S{sid}", scene=sc, channel=1, frame_start=t["start_frame"])
    st.scene_input = 'CAMERA'; st.scene_camera = sc.camera
    st.frame_final_duration = t["frames"]
    print("LINKED", sid, sc.library.filepath, t["start_frame"], t["frames"], flush=True)

# farms (RenderStreet) refuse a scene without a camera even when the sequencer drives the render: give MASTER one
# (the sequencer output ignores it)
cd = bpy.data.cameras.new("MASTER_cam"); cam = bpy.data.objects.new("MASTER_cam", cd)
master.collection.objects.link(cam); master.camera = cam

total = max(T[s]["start_frame"] + T[s]["frames"] - 1 for s in T)
master.frame_start, master.frame_end = 1, total
r = master.render
r.engine = 'CYCLES'; r.resolution_x, r.resolution_y, r.resolution_percentage = 2560, 1440, 100
r.fps = 24; r.fps_base = 1.0
master.cycles.samples = 64; master.cycles.use_adaptive_sampling = True; master.cycles.adaptive_threshold = 0.03
master.cycles.use_denoising = True
try:
    master.cycles.denoiser = 'OPENIMAGEDENOISE'
except Exception:
    pass
r.use_sequencer = True; r.use_compositing = True
r.image_settings.file_format = 'PNG'; r.image_settings.color_mode = 'RGB'; r.image_settings.color_depth = '16'
r.filepath = "//frames/MaryCeleste_P2_"
r.use_overwrite = False; r.use_placeholder = True
# the sequencer shows each strip through MASTER's colour management: use the shots' own (all 42 are AgX, Medium High
# Contrast, exposure 0; their grade is in each shot's compositor, which the strips keep)
master.view_settings.view_transform = 'AgX'
master.view_settings.look = 'AgX - Medium High Contrast'
master.view_settings.exposure = 0.0
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True, relative_remap=True)
print("MASTER", OUT, round(os.path.getsize(OUT) / 1e6, 2), "MB frames 1 -", total, flush=True)
