"""The whole Radio Jingle film in ONE file to render (do not render it here):
Cold Open (2.5 s of picture before the first word) -> fade -> Seldom logo sting (bag, 6 s) -> fade -> Chapters 1-5
(3 s of picture under each chapter title before the voice). Shots are linked from out/blend/<part>/ (relative paths:
keep the out/blend folder together). Farm-ready: scene camera, fonts packed, 32 samples on every shot and the master.
  python make_film_rj.py        -> projects/radio-jingle/out/blend/film/radio_jingle_film.blend
Voiceovers: vo/cold.mp3, vo/ch1.mp3 ... vo/ch5.mp3 if present (until then the timeline uses the estimated cut)."""
import os, sys, json
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "nvidia_doc", "scenes"))
import bpy
import grade

BL = os.path.abspath(os.path.join(HERE, "..", "out", "blend"))
VO = os.path.abspath(os.path.join(HERE, "..", "vo"))
FPS = 24
SAMPLES = int(os.environ.get("FILM_SAMPLES", 32))
ORDER = [("cold", 2.5), ("sting", 0.0), ("ch1", 3.0), ("ch2", 3.0), ("ch3", 3.0), ("ch4", 3.0), ("ch5", 3.0)]
STING_SFX = os.path.join(ROOT, "brand", "seldom_sting_sfx.wav")

parts = []
for folder, lead in ORDER:
    f = os.path.join(BL, folder, "shots.json")
    if not os.path.exists(f):
        print("[film] missing part (not baked yet):", folder, flush=True); continue
    shots = json.load(open(f))
    vo = STING_SFX if folder == "sting" else os.path.join(VO, folder + ".mp3")
    parts.append((folder, shots, vo if os.path.exists(vo) else None, lead))

# every shot file: house grade (with its per-shot look settings), 32 samples, fonts packed, scene named after the shot
for folder, shots, _, _ in parts:
    for sh in shots:
        path = os.path.join(BL, folder, sh["name"] + ".blend")
        bpy.ops.wm.open_mainfile(filepath=path)
        sc = bpy.context.scene
        if sc.compositing_node_group is None or not sc.compositing_node_group.name.startswith("HouseGrade"):
            grade.add_grade(sc)
        sc.name = sh["name"]
        sc.cycles.samples = SAMPLES; sc.cycles.use_adaptive_sampling = True; sc.cycles.adaptive_threshold = 0.05
        sc.cycles.use_denoising = True
        for fo in bpy.data.fonts:
            if fo.filepath and not fo.packed_file and fo.filepath != "<builtin>":
                try:
                    fo.pack()
                except Exception as e:
                    print("[film] could not pack font", fo.filepath, e)
        bpy.ops.wm.save_mainfile(filepath=path, compress=True)
        if os.path.exists(path + "1"):
            os.remove(path + "1")

bpy.ops.wm.read_factory_settings(use_empty=True)
master = bpy.context.scene; master.name = "RADIO_JINGLE_FILM"
master.render.resolution_x, master.render.resolution_y, master.render.resolution_percentage = 1920, 816, 100
master.render.fps = FPS
se = master.sequence_editor_create()
strips = se.strips if hasattr(se, "strips") else se.sequences
frame = 1
for folder, shots, vo, lead in parts:
    start = frame
    master.timeline_markers.new(folder.upper(), frame=frame)
    for sh in shots:
        path = os.path.join(BL, folder, sh["name"] + ".blend")
        with bpy.data.libraries.load(path, link=True, relative=True) as (src, dst):
            dst.scenes = [n for n in src.scenes if n == sh["name"]] or src.scenes[:1]
        sc = dst.scenes[0]
        strips.new_scene(name=f"{folder[:4]} {sh['label']}"[:60], scene=sc, channel=1, frame_start=frame)
        frame += sc.frame_end - sc.frame_start + 1
    if vo:
        snd = strips.new_sound(f"VO {folder}", vo, channel=2, frame_start=start + int(round(lead * FPS)))
        try:
            snd.sound.pack()
        except Exception as e:
            print("[film] could not pack", vo, e)
    print(f"[film] {folder}: frames {start}-{frame - 1}", flush=True)
master.frame_start, master.frame_end = 1, frame - 1


def black(f0, f1, a0, a1, ch=5):
    kw = dict(name="Fade", type='COLOR', channel=ch, frame_start=f0)
    try:
        st = strips.new_effect(frame_end=f1, **kw)
    except TypeError:
        st = strips.new_effect(length=f1 - f0, **kw)
    st.color = (0, 0, 0); st.blend_type = 'ALPHA_OVER'
    st.blend_alpha = a0; st.keyframe_insert("blend_alpha", frame=f0)
    st.blend_alpha = a1; st.keyframe_insert("blend_alpha", frame=f1 - 1)


starts = {m.name: m.frame for m in master.timeline_markers}
if "STING" in starts and "CH1" in starts:
    s_sting, s_ch1 = starts["STING"], starts["CH1"]
    black(s_sting - 24, s_sting, 0.0, 1.0)          # cold open -> black over 1 s
    black(s_sting, s_sting + 12, 1.0, 0.0)          # sting fades up
    black(s_ch1 - 36, s_ch1, 0.0, 1.0)              # sting -> black over 1.5 s
    black(s_ch1, s_ch1 + 24, 1.0, 0.0)              # Chapter 1 fades in
cam = bpy.data.objects.new("FilmCam", bpy.data.cameras.new("FilmCam"))
master.collection.objects.link(cam); master.camera = cam
master.render.engine = 'CYCLES'
master.cycles.samples = SAMPLES; master.cycles.adaptive_threshold = 0.05
master.render.film_transparent = False
master.render.use_sequencer = True
master.render.use_compositing = False          # each shot scene applies its own grade
master.render.filepath = "//render/radio_jingle_"
master.render.image_settings.file_format = 'PNG'
out_dir = os.path.join(BL, "film"); os.makedirs(out_dir, exist_ok=True)
out = os.path.join(out_dir, "radio_jingle_film.blend")
bpy.ops.wm.save_as_mainfile(filepath=out, compress=True, relative_remap=True)
print("[film] saved", out, "frames", master.frame_end, f"({(frame - 1) / FPS / 60:.1f} min)", flush=True)
