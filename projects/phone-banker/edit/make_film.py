"""The whole phone-banker film in ONE file to render: intro -> Seldom sting -> Chapters 1-3, each part's voice under it.

  python edit/make_film.py      (after edit/bake_all.sh)  -> out/blend/film/phone_banker_film.blend + edit/film_edl.json
Shot files stay in out/blend/<part>/ and are linked with relative paths; keep the out/blend folder together.
Like nvidia_doc/scenes/make_film.py: every shot gets the house grade, 32 samples, adaptive 0.05, denoise, packed fonts,
alpha off; the master gets a FilmCam, the same render settings and fades through black around the sting.
"""
import os, sys, json
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, ".."))
ND = os.path.abspath(os.path.join(ROOT, "..", "..", "nvidia_doc", "scenes"))
sys.path.insert(0, ND)
import bpy
import grade

BL = os.path.join(ROOT, "out", "blend")
FPS = 24
SAMPLES = int(os.environ.get("FILM_SAMPLES", 32))
T = json.load(open(os.path.join(ROOT, "vo", "timing.json")))
BRAND = os.path.abspath(os.path.join(ROOT, "..", "..", "brand"))
parts = [("intro", [(r["name"], r["label"]) for r in T["intro"]["shots"]], os.path.join(ROOT, "vo", "intro_vo.mp3"), T["intro"]["vo_offset"])]
parts.append(("sting", [("seldom_sting", "Seldom logo sting")], os.path.join(BRAND, "seldom_sting_sfx.wav"), 0.0))
for c in ("ch1", "ch2", "ch3"):
    parts.append((c, [(r["name"], r["label"]) for r in T[c]["shots"]], os.path.join(ROOT, "vo", f"{c}_vo.mp3"), T[c]["vo_offset"]))


def farm_settings(sc):
    sc.cycles.samples = SAMPLES
    sc.cycles.use_adaptive_sampling = True
    sc.cycles.adaptive_threshold = 0.05
    sc.cycles.use_denoising = True
    sc.render.film_transparent = False


if os.environ.get("SKIP_SHOTS") != "1":
    for folder, shots, _, _ in parts:
        for name, _ in shots:
            path = os.path.join(BL, folder, name + ".blend")
            bpy.ops.wm.open_mainfile(filepath=path)
            sc = bpy.context.scene
            if sc.compositing_node_group is None or not sc.compositing_node_group.name.startswith("HouseGrade"):
                grade.add_grade(sc)
            sc.name = name
            farm_settings(sc)
            for fo in bpy.data.fonts:                  # the farm must not fall back to Blender's default font
                if fo.filepath and not fo.packed_file and fo.filepath != "<builtin>":
                    try:
                        fo.pack()
                    except Exception as e:
                        print("[film] could not pack font", fo.filepath, e)
            bpy.ops.wm.save_mainfile(filepath=path, compress=True)
            if os.path.exists(path + "1"):
                os.remove(path + "1")
            print("[film] prepared", name, flush=True)

# The master links each shot's scene. Linking loads the whole shot (about 0.4 GB each, ~28 GB for the film), more than
# this machine has, so the links are made against tiny placeholder files (an empty scene with the same name and frame
# range) and each library path is then pointed at the real shot file. Blender resolves the links by scene name when the
# farm opens the master, so it renders the real shots; nothing heavy is loaded here.
FRAMES = {r["name"]: r["frames"] for p in ("intro", "ch1", "ch2", "ch3") for r in T[p]["shots"]}; FRAMES["seldom_sting"] = 144
PH = os.path.join(BL, "_placeholders"); os.makedirs(PH, exist_ok=True)
for folder, shots, _, _ in parts:
    for name, _ in shots:
        bpy.ops.wm.read_factory_settings(use_empty=True)
        sc = bpy.context.scene; sc.name = name; sc.frame_start, sc.frame_end = 1, FRAMES[name]
        bpy.ops.wm.save_as_mainfile(filepath=os.path.join(PH, name + ".blend"))

bpy.ops.wm.read_factory_settings(use_empty=True)
master = bpy.context.scene; master.name = "PHONE_BANKER_FILM"
master.render.resolution_x, master.render.resolution_y, master.render.resolution_percentage = 1920, 816, 100
master.render.fps = FPS
se = master.sequence_editor_create()
strips = se.strips if hasattr(se, "strips") else se.sequences
out_dir = os.path.join(BL, "film"); os.makedirs(out_dir, exist_ok=True)
out = os.path.join(out_dir, "phone_banker_film.blend")
bpy.ops.wm.save_as_mainfile(filepath=out)                 # saved first, so relative library paths are relative to it
edl = dict(shots=[], vo=[])
frame = 1
for folder, shots, vo, lead in parts:
    start = frame
    master.timeline_markers.new(folder.upper(), frame=frame)
    for name, label in shots:
        with bpy.data.libraries.load(os.path.join(PH, name + ".blend"), link=True, relative=True) as (src, dst):
            dst.scenes = [name]
        sc = dst.scenes[0]
        strips.new_scene(name=f"{folder} {label}"[:60], scene=sc, channel=1, frame_start=frame)
        sc.library.filepath = "//" + os.path.relpath(os.path.join(BL, folder, name + ".blend"), out_dir)   # -> the real shot
        n = FRAMES[name]
        edl["shots"].append([frame, frame + n, name])
        frame += n
    f_vo = start + int(round(lead * FPS))
    snd = strips.new_sound(f"VO {folder}", vo, channel=2, frame_start=f_vo)
    try:
        snd.sound.pack()
    except Exception as e:
        print("[film] could not pack", vo, e)
    edl["vo"].append([f"VO {folder}", f_vo, frame])
    print(f"[film] {folder}: frames {start}-{frame - 1}", flush=True)
master.frame_start, master.frame_end = 1, frame - 1
edl["end"] = frame - 1


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
s_sting, s_ch1 = starts["STING"], starts["CH1"]
fades = [(s_sting - 24, s_sting, 0.0, 1.0), (s_sting, s_sting + 12, 1.0, 0.0), (s_ch1 - 36, s_ch1, 0.0, 1.0), (s_ch1, s_ch1 + 24, 1.0, 0.0)]
for f in fades:
    black(*f)
edl["fades"] = fades
edl["markers"] = starts
for st in strips:                                       # the intro's voice tail fades with the picture
    if st.type == 'SOUND' and st.name == "VO intro":
        st.volume = 1.0; st.keyframe_insert("volume", frame=s_sting - 24)
        st.volume = 0.0; st.keyframe_insert("volume", frame=s_sting)
cam = bpy.data.objects.new("FilmCam", bpy.data.cameras.new("FilmCam"))
master.collection.objects.link(cam); master.camera = cam
master.render.engine = 'CYCLES'
farm_settings(master)
master.render.use_sequencer = True
master.render.use_compositing = False
master.render.filepath = "//render/phone_banker_film_"
master.render.image_settings.file_format = 'PNG'
bpy.ops.wm.save_as_mainfile(filepath=out, compress=True, relative_remap=False)
json.dump(edl, open(os.path.join(HERE, "film_edl.json"), "w"), indent=1)
print("[film] saved", out, "frames", master.frame_end, f"({(frame - 1) / FPS / 60:.2f} min)", flush=True)
