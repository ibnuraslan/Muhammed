"""One .blend for the whole of Part 3: every shot appended as its own scene (p3_01 ... p3_43), and a MASTER scene whose
Video Sequencer plays the shot scenes as Scene strips end to end at the VO timings. Rendering MASTER renders the part.
    blender -b --factory-startup --python tools/build_master.py -- <shots_dir> <out.blend>"""
import os, sys, json, re
import bpy
argv = sys.argv[sys.argv.index("--") + 1:]
SHOTS, OUT = argv[0], argv[1]
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
order = re.findall(r'@shot\("(p3_[0-9a-z]+)"', open(os.path.join(HERE, "shots.py")).read())
tim = json.load(open(os.path.join(HERE, "vo", "vo_timings.json")))
master = bpy.context.scene; master.name = "MASTER"
for sid in order:
    path = os.path.join(SHOTS, sid + ".blend")
    with bpy.data.libraries.load(path, link=False, relative=False) as (src, dst):
        dst.scenes = [n for n in src.scenes]
    sc = dst.scenes[0]; sc.name = sid
    n = int(round(tim[sid] * 24))
    sc.frame_start, sc.frame_end = 1, n
    print("appended", sid, n, flush=True)
# the edit
master.sequence_editor_create()
se = master.sequence_editor
strips = se.strips if hasattr(se, "strips") else se.sequences
f = 1
for i, sid in enumerate(order):
    sc = bpy.data.scenes[sid]
    st = strips.new_scene(name=sid, scene=sc, channel=1, frame_start=f)
    st.scene_input = 'CAMERA'
    st.scene_camera = sc.camera
    f += sc.frame_end
master.frame_start, master.frame_end = 1, f - 1
r = master.render
r.engine = 'CYCLES'; master.cycles.samples = 64; master.cycles.use_adaptive_sampling = True
master.cycles.adaptive_threshold = 0.03; master.cycles.use_denoising = True
r.resolution_x, r.resolution_y, r.resolution_percentage = 2560, 1440, 100
r.fps = 24; r.use_sequencer = True; r.use_compositing = False
r.image_settings.file_format = 'PNG'; r.image_settings.color_mode = 'RGB'; r.image_settings.color_depth = '16'
r.filepath = "//frames/mary_celeste_p3_"
r.use_overwrite = False; r.use_placeholder = True
for sid in order:                                    # every shot: same output size and sampling
    s = bpy.data.scenes[sid]
    s.render.resolution_x, s.render.resolution_y, s.render.resolution_percentage = 2560, 1440, 100
    s.cycles.samples = 64; s.cycles.use_adaptive_sampling = True; s.cycles.adaptive_threshold = 0.03; s.cycles.use_denoising = True
bpy.context.window.scene = master if bpy.context.window else None
# one copy of each image: shots appended from separate files bring their own copies of the shared textures
seen = {}
for img in list(bpy.data.images):
    if img.source != 'FILE' or not img.filepath:
        continue
    k = os.path.normpath(bpy.path.abspath(img.filepath, library=img.library))
    if k in seen:
        img.user_remap(seen[k]); bpy.data.images.remove(img)
    else:
        seen[k] = img
print("images after dedupe:", len(bpy.data.images), flush=True)
try:
    bpy.ops.file.pack_all()
except Exception as e:
    print("pack_all:", e)
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True, relative_remap=True)
print("MASTER", OUT, "frames", master.frame_start, master.frame_end, round(os.path.getsize(OUT) / 1e6, 1), "MB", flush=True)
