"""(killer-in-house) The whole film in ONE file to render: intro + Seldom sting + Chapters 1-3, each part's
voiceover underneath. Farm-ready as the shared make_film.py (027e0aa): FilmCam, fonts packed, 32 samples,
adaptive 0.05, denoise, film_transparent off. Shot files stay in out/blend/<part>/ (linked, relative): keep the
out/blend folder together.
  python scenes/make_film_kih.py [--sting /path/to/seldom_sting.blend]   -> out/blend/film/killer_in_house.blend
Voiceovers: vo/intro.mp3, vo/ch1.mp3 ... (a part without one is laid in picture-only).
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path[:0] = [HERE, os.path.join(ROOT, "nvidia_doc", "scenes")]
import bpy
import grade
import shots

P = os.path.abspath(os.path.join(HERE, ".."))
BL = os.path.join(P, "out", "blend"); FPS = 24
SAMPLES = int(os.environ.get("FILM_SAMPLES", 32))
arg = lambda k, d: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
STING = arg("--sting", os.path.join(ROOT, "nvidia_doc", "out", "blend", "sting", "seldom_sting.blend"))
parts = [("intro", [(f"{s}_{m}", lab) for s, m, t, lab in shots.INTRO], os.path.join(P, "vo", "intro.mp3"), 2.5, BL)]
if os.path.exists(STING):
    parts.append(("sting", [("seldom_sting", "Seldom logo sting")], os.path.join(ROOT, "brand", "seldom_sting_sfx.wav"), 0.0, os.path.dirname(os.path.dirname(STING))))
else:
    print("[film] WARNING: no sting file at", STING, "- pass --sting; the film is built without it")
for c in ("ch1", "ch2", "ch3"):
    parts.append((c, [(f"{s}_{m}", lab) for s, m, t, lab in shots.CHAPTERS[c]], os.path.join(P, "vo", f"{c}.mp3"), 2.0, BL))

for folder, shot_list, _, _, base in parts:
    for name, _ in shot_list:
        path = os.path.join(base, folder, name + ".blend")
        bpy.ops.wm.open_mainfile(filepath=path)
        sc = bpy.context.scene
        if folder != "sting" and (sc.compositing_node_group is None or not sc.compositing_node_group.name.startswith("HouseGrade")):
            grade.add_grade(sc)
        sc.name = name
        sc.cycles.samples = SAMPLES; sc.cycles.use_adaptive_sampling = True; sc.cycles.adaptive_threshold = 0.05
        sc.cycles.use_denoising = True; sc.render.film_transparent = False
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
master = bpy.context.scene; master.name = "KILLER_IN_HOUSE"
master.render.resolution_x, master.render.resolution_y, master.render.resolution_percentage = 1920, 816, 100
master.render.fps = FPS
se = master.sequence_editor_create()
strips = se.strips if hasattr(se, "strips") else se.sequences
out_dir = os.path.join(BL, "film"); os.makedirs(out_dir, exist_ok=True)
frame = 1
for folder, shot_list, vo, lead, base in parts:
    start = frame
    master.timeline_markers.new(folder.upper(), frame=frame)
    for name, label in shot_list:
        path = os.path.join(base, folder, name + ".blend")
        with bpy.data.libraries.load(path, link=True, relative=True) as (src, dst):
            dst.scenes = [n for n in src.scenes if n == name] or src.scenes[:1]
        sc = dst.scenes[0]
        strips.new_scene(name=f"{folder[:3]} {label}"[:60], scene=sc, channel=1, frame_start=frame)
        frame += sc.frame_end - sc.frame_start + 1
    if os.path.exists(vo):
        snd = strips.new_sound(f"VO {folder}", vo, channel=2, frame_start=start + int(round(lead * FPS)))
        try:
            snd.sound.pack()
        except Exception as e:
            print("[film] could not pack", vo, e)
    else:
        print(f"[film] {folder}: no voiceover at {vo} (picture only)")
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
    return st
starts = {m.name: m.frame for m in master.timeline_markers}
if "STING" in starts:
    s_sting, s_ch1 = starts["STING"], starts["CH1"]
    black(s_sting - 24, s_sting, 0.0, 1.0); black(s_sting, s_sting + 12, 1.0, 0.0)
    black(s_ch1 - 36, s_ch1, 0.0, 1.0); black(s_ch1, s_ch1 + 24, 1.0, 0.0)
    for st in strips:
        if st.type == 'SOUND' and st.name == "VO intro":
            st.volume = 1.0; st.keyframe_insert("volume", frame=s_sting - 24)
            st.volume = 0.0; st.keyframe_insert("volume", frame=s_sting)
cam = bpy.data.objects.new("FilmCam", bpy.data.cameras.new("FilmCam"))
master.collection.objects.link(cam); master.camera = cam
master.render.engine = 'CYCLES'
master.cycles.samples = SAMPLES; master.cycles.adaptive_threshold = 0.05
master.render.film_transparent = False
master.render.use_sequencer = True
master.render.use_compositing = False
master.render.filepath = "//render/killer_in_house_"
master.render.image_settings.file_format = 'PNG'
out = os.path.join(out_dir, "killer_in_house.blend")
bpy.ops.wm.save_as_mainfile(filepath=out, compress=True, relative_remap=True)
print("[film] saved", out, "frames", master.frame_end, f"({(frame - 1) / FPS / 60:.1f} min)", flush=True)
