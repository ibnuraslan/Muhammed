"""Assemble a chapter into ONE file to render: every shot .blend is graded, then linked into a master scene whose
timeline plays the shots in order with the voiceover underneath.

  python scenes/make_master.py intro out/blend/intro vo/intro_vo.mp3
  -> out/blend/intro/intro.blend    (render this: Render > Render Animation, or blender -b intro.blend -a)
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bpy
import grade

CHAPTERS = {
    "intro": [("home_behind", "Set 1A  'I was unfaithful to my wife.'"),
              ("home_front", "Set 1B  'That's what Nvidia CEO ... November eighth.'"),
              ("invest_drawer", "Set 2A  'The same day, Nvidia opens an independent investigation'"),
              ("invest_reveal", "Set 2B  'into whether a foreign intelligence service targeted him.'"),
              ("street_bus_reveal", "Set 3A  'The woman at the center of the allegation is Alice Huang.'"),
              ("street_walk_track", "Set 3B  'She comes from the other side of Nvidia's business.'"),
              ("cafe_title_push", "Set 4A  'The company she helps build buys the kinds of chips'"),
              ("cafe_pull_back", "Set 4B  'Washington is trying to keep out of China.'")],
}

args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
chapter, folder, vo = args[:3]
if chapter not in CHAPTERS and chapter.startswith("chapter"):      # chapter1..3: shot list cut to the voiceover
    import json
    cnum = chapter[len("chapter"):]
    tfile = "ch45_timing.json" if cnum in ("4", "5") else "ch_timing.json"   # ch4/5 live in their own timing file
    tim = json.load(open(os.path.join(HERE, "..", "vo", tfile)))[cnum]
    CHAPTERS[chapter] = [(s["name"], s["label"]) for s in tim]
LEAD = float(args[3]) if len(args) > 3 else (2.5 if chapter == "intro" else 0.0)   # seconds of picture before the first word
# Ch4/5 match the farm-rendered Ch1-3, which used the ORIGINAL house grade -> look="plain" (no cinematic relook).
LOOK = os.environ.get("FILM_LOOK", "plain" if chapter in ("chapter4", "chapter5") else "cinematic")
folder = os.path.abspath(folder)
shots = CHAPTERS[chapter]

# 1. grade every shot file in place (compositor tree stored in its scene)
for name, _ in shots:
    path = os.path.join(folder, name + ".blend")
    bpy.ops.wm.open_mainfile(filepath=path)
    sc = bpy.context.scene
    if sc.compositing_node_group is None or sc.compositing_node_group.name.startswith("HouseGrade") is False:
        grade.add_grade(sc, look=LOOK)
    sc.name = name
    # farm-ready: denoised Cycles at 32 samples, fonts packed (else the farm swaps in Blender's default font)
    sc.cycles.samples = int(os.environ.get("FILM_SAMPLES", 32))
    sc.cycles.use_adaptive_sampling = True; sc.cycles.adaptive_threshold = 0.05; sc.cycles.use_denoising = True
    for fo in bpy.data.fonts:
        if fo.filepath and fo.filepath != "<builtin>" and not fo.packed_file:
            try:
                fo.pack()
            except Exception as e:
                print("[master] could not pack font", fo.filepath, e)
    bpy.ops.wm.save_mainfile(filepath=path, compress=True)
    print("[master] graded", name, sc.frame_end, "frames", flush=True)

# 2. the master file: link each shot's scene, lay them end to end on the timeline, voiceover underneath
bpy.ops.wm.read_factory_settings(use_empty=True)
master = bpy.context.scene; master.name = chapter.upper()
master.render.resolution_x, master.render.resolution_y, master.render.resolution_percentage = 1920, 816, 100
master.render.fps = 24
se = master.sequence_editor_create()
strips = se.strips if hasattr(se, "strips") else se.sequences
frame = 1
for k, (name, label) in enumerate(shots):
    path = os.path.join(folder, name + ".blend")
    with bpy.data.libraries.load(path, link=True, relative=True) as (src, dst):
        dst.scenes = [n for n in src.scenes if n == name] or src.scenes[:1]
    sc = dst.scenes[0]
    st = strips.new_scene(name=label[:60], scene=sc, channel=1, frame_start=frame)
    st.scene_input = 'CAMERA' if hasattr(st, "scene_input") else None
    n = sc.frame_end - sc.frame_start + 1
    print(f"[master] {name:20s} frames {frame}-{frame + n - 1}", flush=True)
    m = master.timeline_markers.new(label.split("  ")[0], frame=frame)
    frame += n
master.frame_start, master.frame_end = 1, frame - 1
# voiceover (packed into the master)
vo_path = os.path.abspath(vo)
snd = strips.new_sound("Voiceover", vo_path, channel=2, frame_start=1 + int(round(LEAD * 24)))
bpy.ops.file.pack_all() if False else None
try:
    snd.sound.pack()
except Exception as e:
    print("[master] could not pack sound:", e)
# render farms refuse a file without a scene camera, and read the sample count from the master scene
cam = bpy.data.objects.new("FilmCam", bpy.data.cameras.new("FilmCam"))
master.collection.objects.link(cam); master.camera = cam
master.render.engine = 'CYCLES'
master.cycles.samples = int(os.environ.get("FILM_SAMPLES", 32)); master.cycles.adaptive_threshold = 0.05
master.render.film_transparent = False
master.render.use_sequencer = True
master.render.use_compositing = False          # each shot scene applies its own grade
master.render.filepath = f"//render/{chapter}_"
master.render.image_settings.file_format = 'PNG'
out = os.path.join(folder, chapter + ".blend")
bpy.ops.wm.save_as_mainfile(filepath=out, compress=True, relative_remap=True)
print("[master] saved", out, "frames", master.frame_end, flush=True)
