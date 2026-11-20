"""One .blend for the whole part: every shot .blend of the farm package appended as its own scene (named by shot),
plus a MASTER scene whose Video Sequencer holds the shot scenes as Scene strips, back to back on the VO timings.
Rendering MASTER renders the whole part in one job. Images are de-duplicated, packed, and the file is compressed.

    blender -b --factory-startup --python tools/build_master.py -- <PKG dir> <out.blend>"""
import os, sys, json
import bpy

a = sys.argv[sys.argv.index("--") + 1:]
PKG, OUT = a[0], a[1]
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "tools"))
from shots_vo import SHOTS
TIM = json.load(open(os.path.join(HERE, "vo", "vo_timings.json")))
FPS = 24

# start from an empty file saved next to the output, so relative paths resolve the same way
bpy.ops.wm.read_factory_settings(use_empty=True)
os.makedirs(os.path.dirname(OUT), exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=OUT)
blank = bpy.context.scene

scenes = {}
for sid, _, _ in SHOTS:
    path = os.path.join(PKG, "shots", f"{sid}.blend")
    with bpy.data.libraries.load(path, link=False, relative=True) as (src, dst):
        dst.scenes = list(src.scenes)
    sc = dst.scenes[0]
    sc.name = sid
    scenes[sid] = sc
    # the shot's images were relative to shots/: point them at the real files (absolute for now; packed below)
    for img in bpy.data.images:
        if img.filepath.startswith("//../textures/"):
            img.filepath = os.path.join(PKG, "textures", img.filepath[len("//../textures/"):])
    print("APPENDED", sid, sc.frame_start, sc.frame_end, flush=True)

# one image datablock per file (each appended shot brought its own copies)
first = {}
for img in list(bpy.data.images):
    if img.source != 'FILE':
        continue
    key = os.path.realpath(bpy.path.abspath(img.filepath))
    if key in first and first[key] is not img:
        img.user_remap(first[key]); bpy.data.images.remove(img)
    else:
        first[key] = img

# the MASTER scene: Scene strips in order, frame-exact to the VO timings
m = bpy.data.scenes.new("MASTER")
r = m.render
r.resolution_x, r.resolution_y, r.resolution_percentage = 2560, 1440, 100
r.fps = FPS
m.render.engine = 'CYCLES'
m.cycles.samples = 64; m.cycles.use_adaptive_sampling = True; m.cycles.adaptive_threshold = 0.03
m.cycles.use_denoising = True
try:
    m.cycles.denoiser = 'OPENIMAGEDENOISE'
except Exception:
    pass
r.use_sequencer = True; r.use_compositing = False
r.image_settings.file_format = 'PNG'; r.image_settings.color_mode = 'RGB'; r.image_settings.color_depth = '16'
r.filepath = "//frames/MC_P4_"
r.use_overwrite = False; r.use_placeholder = True
m.view_settings.view_transform = scenes[SHOTS[0][0]].view_settings.view_transform     # the strips carry their own look
m.view_settings.look = scenes[SHOTS[0][0]].view_settings.look
ed = m.sequence_editor_create()
strips = ed.strips if hasattr(ed, "strips") else ed.sequences
total = 0
for sid, _, _ in SHOTS:
    sc = scenes[sid]; t = TIM[sid]; n = t["frames"]
    sc.frame_start, sc.frame_end = 1, n
    sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 2560, 1440, 100
    sc.render.fps = FPS
    s = strips.new_scene(name=sid, scene=sc, channel=1, frame_start=1 + t["start"])
    s.scene_input = 'CAMERA'
    assert s.frame_final_start == 1 + t["start"] and s.frame_final_end == 1 + t["start"] + n, (sid, s.frame_final_start, s.frame_final_end)
    total = max(total, t["start"] + n)
m.frame_start, m.frame_end = 1, total
bpy.context.window.scene = m if bpy.context.window else None
for sc in bpy.data.scenes:
    if sc is blank:
        bpy.data.scenes.remove(blank); break

bpy.ops.file.pack_all()
for f in bpy.data.fonts:
    if f.filepath and f.filepath != "<builtin>" and not f.packed_file:
        try:
            f.pack()
        except Exception:
            pass
try:
    bpy.ops.outliner.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)
except Exception:
    pass
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
missing = [i.name for i in bpy.data.images if i.source == 'FILE' and not i.packed_file]
print("MASTER", OUT, "scenes", len(bpy.data.scenes), "frames", m.frame_start, m.frame_end, "unpacked", missing,
      round(os.path.getsize(OUT) / 1e6, 1), "MB", flush=True)
