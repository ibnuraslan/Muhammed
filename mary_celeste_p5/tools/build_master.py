"""One .blend for the whole part: every shot appended as its own scene, and a MASTER scene whose Video Sequencer holds
the shot scenes as Scene strips in order on the VO timing. Rendering MASTER renders the whole part in one job.

    blender -b --factory-startup --python tools/build_master.py -- <PKG dir with shots/ and textures/> <out .blend>
Images are de-duplicated across shots (same file -> one image) and packed; the file is saved compressed."""
import os, sys, json
import bpy

argv = sys.argv[sys.argv.index("--") + 1:]
PKG, OUT = os.path.abspath(argv[0]), os.path.abspath(argv[1])
P5 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, P5)
from shots import SHOTS
tim = json.load(open(os.path.join(P5, "vo", "vo_timings.json")))
FPS = 24
SHOTDIR = os.path.join(PKG, "shots")

# work from a file saved next to the shot files, so their //../textures/ paths resolve the same way
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(SHOTDIR, "_master_tmp.blend"))
master = bpy.context.scene; master.name = "MASTER"

scenes = []
for sid, *_ in SHOTS:
    path = os.path.join(SHOTDIR, f"{sid}.blend")
    with bpy.data.libraries.load(path, link=False) as (src, dst):
        dst.scenes = list(src.scenes)
    sc = dst.scenes[0]; sc.name = sid
    n = int(round(float(tim[sid]) * FPS))
    sc.frame_start, sc.frame_end = 1, n
    scenes.append((sid, sc, n))
    for lib in list(bpy.data.libraries):
        bpy.data.libraries.remove(lib)
    print("APPENDED", sid, n, "frames", flush=True)

# one image per file on disk (every shot carried its own copy of the shared textures)
by_path = {}
for img in list(bpy.data.images):
    if img.source != 'FILE' or img.packed_file:
        continue
    key = os.path.normpath(bpy.path.abspath(img.filepath))
    if key in by_path:
        img.user_remap(by_path[key]); bpy.data.images.remove(img)
    else:
        by_path[key] = img
print("IMAGES", len(by_path), "unique files", flush=True)

# the master edit
master.render.engine = 'CYCLES'
master.render.resolution_x, master.render.resolution_y, master.render.resolution_percentage = 2560, 1440, 100
master.render.fps = FPS
master.cycles.samples = 64; master.cycles.use_adaptive_sampling = True; master.cycles.adaptive_threshold = 0.03
master.cycles.use_denoising = True
try:
    master.cycles.denoiser = 'OPENIMAGEDENOISE'
except Exception:
    pass
master.render.image_settings.file_format = 'PNG'; master.render.image_settings.color_mode = 'RGB'
master.render.image_settings.color_depth = '16'
master.render.filepath = "//frames/MaryCeleste_P5_"
master.render.use_sequencer = True; master.render.use_compositing = False      # each shot scene carries its own grade
master.render.use_overwrite = False; master.render.use_placeholder = True
se = master.sequence_editor_create()
strips = getattr(se, "strips", None) or se.sequences
f = 1
for sid, sc, n in scenes:
    st = strips.new_scene(name=sid, scene=sc, channel=1, frame_start=f)
    st.scene_input = 'CAMERA'
    st.frame_final_duration = n
    f += n
master.frame_start, master.frame_end = 1, f - 1
print("MASTER", master.frame_start, master.frame_end, flush=True)

bpy.ops.file.pack_all()
try:
    bpy.ops.outliner.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)
except Exception:
    pass
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True, relative_remap=True)
os.remove(os.path.join(SHOTDIR, "_master_tmp.blend"))
print("SAVED", OUT, round(os.path.getsize(OUT) / 1e6, 1), "MB", flush=True)
