"""ONE self-contained film file for farms that refuse linked libraries:
  python edit/make_film_single.py  -> out/single/phone_banker_film.blend
Same timeline as edit/make_film.py (intro, fade, sting, fade, Ch1-3, VO strips, fades, FilmCam, farm settings), but
every shot scene is APPENDED (local data, no library links). Images appended from many shots that point at the same
shared texture are merged into one datablock, then every image is packed (fonts are already packed in the shots,
sounds are packed). Saved zstd-compressed."""
import os, sys, json
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, ".."))
import bpy
BL = os.path.join(ROOT, "out", "blend"); FPS = 24
T = json.load(open(os.path.join(ROOT, "vo", "timing.json")))
BRAND = os.path.abspath(os.path.join(ROOT, "..", "..", "brand"))
parts = [("intro", [r["name"] for r in T["intro"]["shots"]], os.path.join(ROOT, "vo", "intro_vo.mp3"), T["intro"]["vo_offset"])]
parts.append(("sting", ["seldom_sting"], os.path.join(BRAND, "seldom_sting_sfx.wav"), 0.0))
for c in ("ch1", "ch2", "ch3"):
    parts.append((c, [r["name"] for r in T[c]["shots"]], os.path.join(ROOT, "vo", f"{c}_vo.mp3"), T[c]["vo_offset"]))
LABEL = {r["name"]: r["label"] for p in ("intro", "ch1", "ch2", "ch3") for r in T[p]["shots"]}; LABEL["seldom_sting"] = "Seldom logo sting"

def farm(sc):
    sc.render.engine = 'CYCLES'; sc.cycles.samples = 32; sc.cycles.use_adaptive_sampling = True
    sc.cycles.adaptive_threshold = 0.05; sc.cycles.use_denoising = True; sc.render.film_transparent = False

OUT = os.path.join(ROOT, "out", "single"); os.makedirs(OUT, exist_ok=True)
out = os.path.join(OUT, "phone_banker_film.blend")
bpy.ops.wm.read_factory_settings(use_empty=True)
master = bpy.context.scene; master.name = "PHONE_BANKER_FILM"
master.render.resolution_x, master.render.resolution_y, master.render.resolution_percentage = 1920, 816, 100
master.render.fps = FPS
se = master.sequence_editor_create()
strips = se.strips if hasattr(se, "strips") else se.sequences
frame = 1
for folder, shots, vo, lead in parts:
    start = frame
    master.timeline_markers.new(folder.upper(), frame=frame)
    for name in shots:
        with bpy.data.libraries.load(os.path.join(BL, folder, name + ".blend"), link=False) as (src, dst):
            dst.scenes = [name]
        sc = dst.scenes[0]
        assert sc.name == name and sc.library is None, (name, sc.name)
        farm(sc)
        strips.new_scene(name=f"{folder} {LABEL[name]}"[:60], scene=sc, channel=1, frame_start=frame)
        frame += sc.frame_end - sc.frame_start + 1
        print(f"[single] appended {name}", flush=True)
    snd = strips.new_sound(f"VO {folder}", vo, channel=2, frame_start=start + int(round(lead * FPS)))
    snd.sound.pack()
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
mk = {m.name: m.frame for m in master.timeline_markers}
a, c1 = mk["STING"], mk["CH1"]
for f in ((a - 24, a, 0.0, 1.0), (a, a + 12, 1.0, 0.0), (c1 - 36, c1, 0.0, 1.0), (c1, c1 + 24, 1.0, 0.0)):
    black(*f)
for st in strips:
    if st.type == 'SOUND' and st.name == "VO intro":
        st.volume = 1.0; st.keyframe_insert("volume", frame=a - 24)
        st.volume = 0.0; st.keyframe_insert("volume", frame=a)
cam = bpy.data.objects.new("FilmCam", bpy.data.cameras.new("FilmCam"))
master.collection.objects.link(cam); master.camera = cam
farm(master); master.render.use_sequencer = True; master.render.use_compositing = False
master.render.filepath = "//render/phone_banker_film_"; master.render.image_settings.file_format = 'PNG'

# merge images that are the same file (each shot brought its own datablock for a shared texture), then pack all
bpy.ops.wm.save_as_mainfile(filepath=out)                    # a saved path first: image paths resolve against the shots' folders
first = {}; merged = 0
for im in list(bpy.data.images):
    if im.source != 'FILE' or not im.filepath or im.packed_file:
        continue
    key = (os.path.normpath(bpy.path.abspath(im.filepath, library=im.library)), im.colorspace_settings.name, im.alpha_mode)
    if key in first:
        im.user_remap(first[key]); bpy.data.images.remove(im); merged += 1
    else:
        first[key] = im
print(f"[single] merged {merged} duplicate images into {len(first)}", flush=True)
for p, im in first.items():
    im.filepath = p[0]                                       # absolute while packing, so pack() reads the real file
    im.pack()
unpacked = [im.name for im in bpy.data.images if im.source == 'FILE' and im.filepath and not im.packed_file]
fonts = [f.name for f in bpy.data.fonts if f.filepath and f.filepath != "<builtin>" and not f.packed_file]
print(f"[single] libraries {len(bpy.data.libraries)}, unpacked images {len(unpacked)}, unpacked fonts {len(fonts)}", flush=True)
bpy.ops.wm.save_as_mainfile(filepath=out, compress=True)
if os.path.exists(out + "1"):
    os.remove(out + "1")
print(f"[single] saved {out} {os.path.getsize(out)} bytes, frames {master.frame_end}", flush=True)
