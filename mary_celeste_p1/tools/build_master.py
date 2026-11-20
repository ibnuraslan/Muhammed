"""Build ONE farm .blend for Part 1: every shot appended as its own scene (named by shot id), plus a MASTER scene whose
Video Sequencer plays the shot scenes back to back as Scene strips (the VO timings: each shot's own frame range).
Rendering scene MASTER renders the whole part in one job. All images and fonts packed; saved compressed.

    blender -b --factory-startup --python tools/build_master.py -- <PKG_DIR> <OUT.blend>
PKG_DIR holds shots/<id>.blend (tools/build_package.sh)."""
import bpy, os, sys, re

a = sys.argv[sys.argv.index("--") + 1:]
pkg, out = os.path.abspath(a[0]), os.path.abspath(a[1])
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
import json
order = list(json.load(open(os.path.join(HERE, "vo", "vo_timings.json"))))     # shot order (S01 ... S53, S16b in place)

master = bpy.context.scene
master.name = "MASTER"
bpy.ops.wm.save_as_mainfile(filepath=out)                  # saved first, so appended paths resolve relative to it

for sid in order:
    path = os.path.join(pkg, "shots", f"{sid}.blend")
    with bpy.data.libraries.load(path, link=False) as (src, dst):
        dst.scenes = list(src.scenes)
    for sc in dst.scenes:
        sc.name = sid
    print("APPENDED", sid, flush=True)

# one copy of each shared image (every shot file brought its own)
seen = {}
for img in list(bpy.data.images):
    if img.source != 'FILE' or not img.filepath:
        continue
    key = os.path.normpath(bpy.path.abspath(img.filepath, library=img.library))
    if key in seen:
        img.user_remap(seen[key]); bpy.data.images.remove(img)
    else:
        seen[key] = img

# MASTER: sequencer of scene strips, back to back
se = master.sequence_editor_create()
coll = getattr(se, "strips", None) or se.sequences
f = 1
for sid in order:
    sc = bpy.data.scenes[sid]
    n = sc.frame_end - sc.frame_start + 1
    st = coll.new_scene(name=sid, scene=sc, channel=1, frame_start=f)
    st.scene_input = 'CAMERA'
    f += n
total = f - 1
r = master.render
master.frame_start, master.frame_end = 1, total
r.fps, r.fps_base = 24, 1.0
r.resolution_x, r.resolution_y, r.resolution_percentage = 2560, 1440, 100
r.engine = 'CYCLES'
master.cycles.samples = 64; master.cycles.use_adaptive_sampling = True; master.cycles.adaptive_threshold = 0.03
master.cycles.use_denoising = True
try:
    master.cycles.denoiser = 'OPENIMAGEDENOISE'
except Exception:
    pass
r.use_sequencer = True
try:
    r.use_compositing = False                                  # the grade lives in each shot scene's compositor
except Exception:
    pass
r.image_settings.file_format = 'PNG'; r.image_settings.color_mode = 'RGB'; r.image_settings.color_depth = '16'
r.filepath = "//frames/MASTER_"
r.use_overwrite = False; r.use_placeholder = True
for sid in order:                                              # each shot scene renders at the master's size
    s = bpy.data.scenes[sid].render
    s.resolution_x, s.resolution_y, s.resolution_percentage = 2560, 1440, 100

try:
    bpy.ops.outliner.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)
except Exception:
    pass
bpy.ops.file.pack_all()
for fnt in bpy.data.fonts:
    if fnt.filepath and fnt.filepath != "<builtin>" and not fnt.packed_file:
        fnt.pack()
missing = [i.name for i in bpy.data.images if i.source == 'FILE' and not i.packed_file]
print("UNPACKED", missing, flush=True)
bpy.ops.wm.save_as_mainfile(filepath=out, compress=True)
print("MASTER_DONE", out, total, "frames", round(os.path.getsize(out) / 1e6, 1), "MB", len(bpy.data.scenes), "scenes", flush=True)
