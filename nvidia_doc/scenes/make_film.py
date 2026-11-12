"""The whole film in ONE file to render: intro + Chapters 1-3 back to back, each chapter's voiceover underneath.

  python scenes/make_film.py           -> out/blend/film/nvidia_film.blend
The shot files stay in out/blend/intro and out/blend/chapter1..3 (linked, relative paths); keep the folder together.
"""
import os, sys, json
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bpy
import grade

ND = os.path.abspath(os.path.join(HERE, ".."))
BL = os.path.join(ND, "out", "blend")
FPS = 24
SAMPLES = int(os.environ.get("FILM_SAMPLES", 32))
INTRO = ["home_behind", "home_front", "invest_drawer", "invest_reveal", "street_bus_reveal", "street_walk_track",
         "cafe_title_push", "cafe_pull_back"]
tim = json.load(open(os.path.join(ND, "vo", "ch_timing.json")))
parts = [("intro", [(n, n) for n in INTRO], os.path.join(ND, "vo", "intro_vo.mp3"), 2.5)]
# the Seldom logo sting sits between the intro and Chapter 1 (its own sound design, no voiceover)
parts.append(("sting", [("seldom_sting", "Seldom logo sting")], os.path.join(ND, "..", "brand", "seldom_sting_sfx.wav"), 0.0))
for c in ("1", "2", "3"):
    parts.append((f"chapter{c}", [(s["name"], s["label"]) for s in tim[c]], os.path.join(ND, "vo", f"ch{c}_vo.mp3"), 2.0))

# make sure every shot file carries the house grade in its own scene
for folder, shots, _, _ in parts:
    for name, _ in shots:
        path = os.path.join(BL, folder, name + ".blend")
        bpy.ops.wm.open_mainfile(filepath=path)
        sc = bpy.context.scene
        if sc.compositing_node_group is None or not sc.compositing_node_group.name.startswith("HouseGrade"):
            grade.add_grade(sc)
        sc.name = name
        # fast final settings: denoised Cycles at low samples (the house look holds; ~4x faster than 128)
        sc.cycles.samples = SAMPLES
        sc.cycles.use_adaptive_sampling = True
        sc.cycles.adaptive_threshold = 0.05
        sc.cycles.use_denoising = True
        bpy.ops.wm.save_mainfile(filepath=path, compress=True)
        b1 = path + "1"
        if os.path.exists(b1):
            os.remove(b1)

bpy.ops.wm.read_factory_settings(use_empty=True)
master = bpy.context.scene; master.name = "NVIDIA_FILM"
master.render.resolution_x, master.render.resolution_y, master.render.resolution_percentage = 1920, 816, 100
master.render.fps = FPS
se = master.sequence_editor_create()
strips = se.strips if hasattr(se, "strips") else se.sequences
out_dir = os.path.join(BL, "film"); os.makedirs(out_dir, exist_ok=True)
frame = 1
for folder, shots, vo, lead in parts:
    start = frame
    master.timeline_markers.new(folder.upper(), frame=frame)
    for name, label in shots:
        path = os.path.join(BL, folder, name + ".blend")
        with bpy.data.libraries.load(path, link=True, relative=True) as (src, dst):
            dst.scenes = [n for n in src.scenes if n == name] or src.scenes[:1]
        sc = dst.scenes[0]
        st = strips.new_scene(name=f"{folder[:3]} {label}"[:60], scene=sc, channel=1, frame_start=frame)
        n = sc.frame_end - sc.frame_start + 1
        frame += n
    snd = strips.new_sound(f"VO {folder}", vo, channel=2, frame_start=start + int(round(lead * FPS)))
    try:
        snd.sound.pack()
    except Exception as e:
        print("[film] could not pack", vo, e)
    print(f"[film] {folder}: frames {start}-{frame - 1}", flush=True)
master.frame_start, master.frame_end = 1, frame - 1


# fades through black: intro fades out ~1 s after its last word, the sting fades in/out, Chapter 1 fades in
def black(f0, f1, a0, a1, ch=5):
    kw = dict(name="Fade", type='COLOR', channel=ch, frame_start=f0)
    try:
        st = strips.new_effect(frame_end=f1, **kw)
    except TypeError:
        st = strips.new_effect(length=f1 - f0, **kw)
    st.color = (0, 0, 0); st.blend_type = 'ALPHA_OVER'
    st.blend_alpha = a0; st.keyframe_insert("blend_alpha", frame=f0)
    st.blend_alpha = a1; st.keyframe_insert("blend_alpha", frame=f1 - 1)
    return st
starts = {m.name: m.frame for m in master.timeline_markers}
s_sting, s_ch1 = starts["STING"], starts["CHAPTER1"]
black(s_sting - 24, s_sting, 0.0, 1.0)          # intro -> black over 1 s
black(s_sting, s_sting + 12, 1.0, 0.0)          # sting fades up
black(s_ch1 - 36, s_ch1, 0.0, 1.0)              # sting -> black over 1.5 s
black(s_ch1, s_ch1 + 24, 1.0, 0.0)              # Chapter 1 fades in
# the intro's music/VO tail and the sting's sound both fade with the picture
for st in strips:
    if st.type == 'SOUND' and st.name == "VO intro":
        end = s_sting
        st.volume = 1.0; st.keyframe_insert("volume", frame=end - 24)
        st.volume = 0.0; st.keyframe_insert("volume", frame=end)
master.render.use_sequencer = True
master.render.use_compositing = False
master.render.filepath = "//render/nvidia_film_"
master.render.image_settings.file_format = 'PNG'
out = os.path.join(out_dir, "nvidia_film.blend")
bpy.ops.wm.save_as_mainfile(filepath=out, compress=True, relative_remap=True)
print("[film] saved", out, "frames", master.frame_end, f"({(frame - 1) / FPS / 60:.1f} min)", flush=True)
