"""(killer-in-house) make_master for this project: the shot list comes from shots.py (names <set>_<move>);
the voiceover is optional until it arrives (the master is built picture-only, VO strip added later).
  python scenes/make_master_kih.py ch2 out/blend/ch2 [vo/ch2.mp3|-] [lead]
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.join(HERE, "..", "..", "..", "nvidia_doc", "scenes")]
import bpy
import grade
import shots

args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
chapter, folder = args[:2]
vo = args[2] if len(args) > 2 and args[2] != "-" else None
LEAD = float(args[3]) if len(args) > 3 else 2.5
folder = os.path.abspath(folder)
shot_list = [(f"{s}_{m}", lab) for s, m, t, lab in shots.CHAPTERS[chapter]]

for name, _ in shot_list:
    path = os.path.join(folder, name + ".blend")
    bpy.ops.wm.open_mainfile(filepath=path)
    sc = bpy.context.scene
    if sc.compositing_node_group is None or not sc.compositing_node_group.name.startswith("HouseGrade"):
        grade.add_grade(sc)
    sc.name = name
    # farm-ready (shared 027e0aa): denoised Cycles at 32 samples, adaptive 0.05, fonts packed, no transparent film
    sc.cycles.samples = int(os.environ.get("FILM_SAMPLES", 32))
    sc.cycles.use_adaptive_sampling = True; sc.cycles.adaptive_threshold = 0.05; sc.cycles.use_denoising = True
    sc.render.film_transparent = False
    for fo in bpy.data.fonts:
        if fo.filepath and fo.filepath != "<builtin>" and not fo.packed_file:
            try:
                fo.pack()
            except Exception as e:
                print("[master] could not pack font", fo.filepath, e)
    bpy.ops.wm.save_mainfile(filepath=path, compress=True)
    print("[master] graded", name, sc.frame_end, "frames", flush=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
master = bpy.context.scene; master.name = chapter.upper()
master.render.resolution_x, master.render.resolution_y, master.render.resolution_percentage = 1920, 816, 100
master.render.fps = 24
se = master.sequence_editor_create()
strips = se.strips if hasattr(se, "strips") else se.sequences
frame = 1
for name, label in shot_list:
    path = os.path.join(folder, name + ".blend")
    with bpy.data.libraries.load(path, link=True, relative=True) as (src, dst):
        dst.scenes = [n for n in src.scenes if n == name] or src.scenes[:1]
    sc = dst.scenes[0]
    st = strips.new_scene(name=label[:60], scene=sc, channel=1, frame_start=frame)
    if hasattr(st, "scene_input"):
        st.scene_input = 'CAMERA'
    n = sc.frame_end - sc.frame_start + 1
    print(f"[master] {name:28s} frames {frame}-{frame + n - 1}", flush=True)
    master.timeline_markers.new(label.split("  ")[0], frame=frame)
    frame += n
master.frame_start, master.frame_end = 1, frame - 1
if vo and os.path.exists(vo):
    snd = strips.new_sound("Voiceover", os.path.abspath(vo), channel=2, frame_start=1 + int(round(LEAD * 24)))
    try:
        snd.sound.pack()
    except Exception as e:
        print("[master] could not pack sound:", e)
else:
    print("[master] no voiceover yet: picture-only master (VO strip goes on channel 2 from frame", 1 + int(round(LEAD * 24)), ")")
cam = bpy.data.objects.new("FilmCam", bpy.data.cameras.new("FilmCam"))        # farms refuse a file without a scene camera
master.collection.objects.link(cam); master.camera = cam
master.render.engine = 'CYCLES'
master.cycles.samples = int(os.environ.get("FILM_SAMPLES", 32)); master.cycles.adaptive_threshold = 0.05
master.render.film_transparent = False
master.render.use_sequencer = True
master.render.use_compositing = False
master.render.filepath = f"//render/{chapter}_"
master.render.image_settings.file_format = 'PNG'
out = os.path.join(folder, chapter + ".blend")
bpy.ops.wm.save_as_mainfile(filepath=out, compress=True, relative_remap=True)
print("[master] saved", out, "frames", master.frame_end, flush=True)
