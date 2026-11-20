"""One .blend for the whole of Part 2: every exported shot appended as its own scene (SHOT_01 ... SHOT_45), and a MASTER
scene whose Video Sequencer holds them as Scene strips at their voice-over times. Rendering MASTER renders the part.

    blender -b --factory-startup --python tools/build_master.py -- <PKG dir (has shots/, textures/)> <out.blend>
Images are de-duplicated across shots (same texture file -> one image) and packed; the file is saved compressed."""
import os, sys, json
import bpy

argv = sys.argv[sys.argv.index("--") + 1:]
PKG, OUT = os.path.abspath(argv[0]), os.path.abspath(argv[1])
P2 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, P2)
import shots
T = json.load(open(os.path.join(P2, "vo", "vo_timings.json")))
TEX = os.path.join(PKG, "textures")

master = bpy.context.scene
master.name = "MASTER"
for o in list(bpy.data.objects):               # factory startup cube, light, camera
    bpy.data.objects.remove(o, do_unlink=True)
ed = master.sequence_editor_create()
strips = ed.strips

by_path = {}
for sid, *_ in shots.SHOTS:
    path = os.path.join(PKG, "shots", f"{sid}.blend")
    before = set(bpy.data.images)
    with bpy.data.libraries.load(path, link=False, relative=False) as (src, dst):
        dst.scenes = list(src.scenes)
    sc = dst.scenes[0]
    sc.name = f"SHOT_{sid}"
    # images: point at the shared texture file by absolute path; one image per file across all shots
    for im in [i for i in bpy.data.images if i not in before]:
        if im.source != 'FILE' or im.packed_file:
            continue
        p = os.path.join(TEX, os.path.basename(bpy.path.abspath(im.filepath, library=im.library)))
        if not os.path.exists(p):
            print("WARN missing", im.name, im.filepath); continue
        if p in by_path:
            im.user_remap(by_path[p]); bpy.data.images.remove(im)
        else:
            im.filepath = p; by_path[p] = im
    t = T[sid]
    st = strips.new_scene(name=f"SHOT_{sid}", scene=sc, channel=1, frame_start=t["start_frame"])
    st.scene_input = 'CAMERA'; st.scene_camera = sc.camera
    st.frame_final_duration = t["frames"]
    print("ADDED", sid, t["start_frame"], t["frames"], flush=True)

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
master.view_settings.view_transform = 'Standard'      # the strips arrive already graded by their own scenes
bpy.context.window.scene = master if bpy.context.window else None
bpy.ops.file.pack_all()
bpy.ops.outliner.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print("MASTER", OUT, round(os.path.getsize(OUT) / 1e6, 1), "MB", "frames 1 -", total, "images", len(bpy.data.images), flush=True)
