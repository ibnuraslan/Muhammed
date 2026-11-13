"""ONE self-contained farm master for Chapters 4-5: fade in, Ch4, Ch5, fade out.

  python scenes/make_master_ch45.py            -> out/blend/ch45/nvidia_ch45.blend

1. Each baked shot (out/blend/ch4|ch5/<name>.blend) is made farm-ready in place: original house grade
   (grade.add_grade look="plain", matching the farm-rendered Ch1-3), Cycles 32 samples / adaptive 0.05 / denoise,
   motion blur off, alpha off, fonts packed.
2. Every shot scene is APPENDED (not linked) into one master file, so the farm gets a single .blend.
3. Identical data is shared: images (by pixel hash), then materials (by node signature), then meshes (by geometry
   + materials). Images larger than 2K are scaled down. Everything is packed (images, fonts, sounds).
4. The master scene plays the shot scenes end to end on the sequencer with both voiceovers underneath, and a black
   colour strip fades the picture in (1 s) and out (1.5 s). FilmCam is the scene camera; 32 samples on the master.
"""
import os, sys, json, hashlib, re
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "..", "edit"))
import bpy
import grade
from chapter_shots_ch45 import LEAD

ROOT = os.path.abspath(os.path.join(HERE, ".."))
FPS = 24
SAMPLES = int(os.environ.get("FILM_SAMPLES", 32))
MAXTEX = 2048
OUT = os.path.join(ROOT, "out", "blend", "ch45"); os.makedirs(OUT, exist_ok=True)
tim = json.load(open(os.path.join(ROOT, "vo", "ch45_timing.json")))
SHOTS = [(c, sh["name"], sh["label"], sh["frames"]) for c in ("4", "5") for sh in tim[c]]
skip_prep = "--skip-prep" in sys.argv


def farm_ready(sc):
    sc.cycles.samples = SAMPLES
    sc.cycles.use_adaptive_sampling = True; sc.cycles.adaptive_threshold = 0.05
    sc.cycles.use_denoising = True
    sc.render.use_motion_blur = False
    sc.render.film_transparent = False
    sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1920, 816, 100
    sc.render.fps = FPS


# ---------------------------------------------------------------- 1. per-shot prep (grade, settings, fonts)
missing = [n for c, n, _, _ in SHOTS if not os.path.exists(os.path.join(ROOT, "out", "blend", f"ch{c}", n + ".blend"))]
if missing:
    raise SystemExit(f"[master45] missing baked shots: {missing}")
if not skip_prep:
    for c, name, label, frames in SHOTS:
        path = os.path.join(ROOT, "out", "blend", f"ch{c}", name + ".blend")
        bpy.ops.wm.open_mainfile(filepath=path)
        sc = bpy.context.scene
        if sc.compositing_node_group is None or not sc.compositing_node_group.name.startswith("HouseGrade"):
            grade.add_grade(sc, look="plain")
        sc.name = name
        farm_ready(sc)
        assert sc.frame_end - sc.frame_start + 1 == frames, (name, sc.frame_start, sc.frame_end, frames)
        for fo in bpy.data.fonts:
            if fo.filepath and fo.filepath != "<builtin>" and not fo.packed_file:
                try: fo.pack()
                except Exception as e: print("[master45] font", fo.filepath, e)
        bpy.ops.wm.save_mainfile(filepath=path, compress=True)
        print("[master45] prepped", name, frames, "frames", flush=True)

# ---------------------------------------------------------------- 2. append every shot scene into one file
bpy.ops.wm.read_factory_settings(use_empty=True)
master = bpy.context.scene; master.name = "NVIDIA_CH45"
scenes = []
for c, name, label, frames in SHOTS:
    path = os.path.join(ROOT, "out", "blend", f"ch{c}", name + ".blend")
    with bpy.data.libraries.load(path, link=False) as (src, dst):
        dst.scenes = [n for n in src.scenes if n == name] or src.scenes[:1]
    sc = dst.scenes[0]; sc.name = name
    scenes.append((sc, label, frames))
    print("[master45] appended", name, flush=True)
assert not bpy.data.libraries, "linked libraries left in the master"


# ---------------------------------------------------------------- 3. share identical data
def strip_suffix(n):
    return re.sub(r"\.\d{3}$", "", n)


def img_key(im):
    if im.packed_file is not None:
        return ("p", hashlib.sha1(im.packed_file.data).hexdigest())
    if im.source == 'FILE' and im.filepath:
        return ("f", bpy.path.abspath(im.filepath))
    return None


n_img = 0; keep = {}
for im in list(bpy.data.images):
    k = img_key(im)
    if k is None: continue
    if k in keep and keep[k] != im:
        im.user_remap(keep[k]); n_img += 1
    else:
        keep[k] = im
for im in [i for i in bpy.data.images if i.users == 0]:
    bpy.data.images.remove(im)


def rnd(v):
    try:
        return tuple(round(float(x), 5) for x in v)
    except TypeError:
        try: return round(float(v), 5)
        except Exception: return str(v)


def mat_sig(m):
    parts = [strip_suffix(m.name), m.blend_method if hasattr(m, "blend_method") else ""]
    if m.use_nodes and m.node_tree:
        for nd in sorted(m.node_tree.nodes, key=lambda x: x.name):
            row = [strip_suffix(nd.name), nd.bl_idname]
            for s in nd.inputs:
                if hasattr(s, "default_value"): row.append(rnd(s.default_value))
            if getattr(nd, "image", None) is not None: row.append(nd.image.name)
            for a in ("operation", "blend_type", "data_type", "feature", "extension"):
                if hasattr(nd, a): row.append(str(getattr(nd, a)))
            parts.append(tuple(row))
        for l in m.node_tree.links:
            parts.append((l.from_node.name, l.from_socket.identifier, l.to_node.name, l.to_socket.identifier))
        ad = m.node_tree.animation_data
        if ad:
            for fc in ad.drivers:
                d = fc.driver
                parts.append((fc.data_path, fc.array_index, d.expression,
                              tuple((v.name, v.targets[0].id.name if v.targets[0].id else "", v.targets[0].data_path) for v in d.variables)))
    else:
        parts.append(rnd(m.diffuse_color))
    return hashlib.sha1(repr(parts).encode()).hexdigest()


n_mat = 0; keep = {}
for m in list(bpy.data.materials):
    k = mat_sig(m)
    if k in keep and keep[k] != m:
        m.user_remap(keep[k]); n_mat += 1
    else:
        keep[k] = m
for m in [m for m in bpy.data.materials if m.users == 0]:
    bpy.data.materials.remove(m)

import numpy as np
def mesh_key(me):
    if me.shape_keys is not None or len(me.vertices) == 0:
        return None
    co = np.empty(len(me.vertices) * 3, np.float32); me.vertices.foreach_get("co", co)
    lv = np.empty(len(me.loops), np.int32); me.loops.foreach_get("vertex_index", lv)
    h = hashlib.sha1(np.round(co, 5).tobytes()); h.update(lv.tobytes())
    h.update(repr([m.name if m else "" for m in me.materials]).encode())
    if me.uv_layers:
        uv = np.empty(len(me.loops) * 2, np.float32); me.uv_layers[0].data.foreach_get("uv", uv); h.update(np.round(uv, 5).tobytes())
    return h.hexdigest()


n_mesh = 0; keep = {}
for me in list(bpy.data.meshes):
    k = mesh_key(me)
    if k is None: continue
    if k in keep and keep[k] != me:
        me.user_remap(keep[k]); n_mesh += 1
    else:
        keep[k] = me
for me in [m for m in bpy.data.meshes if m.users == 0]:
    bpy.data.meshes.remove(me)
print(f"[master45] shared: {n_img} images, {n_mat} materials, {n_mesh} meshes", flush=True)

# textures <= 2K, then pack everything
n_scaled = 0
for im in bpy.data.images:
    if im.source == 'FILE' and max(im.size[0], im.size[1]) > MAXTEX:
        w, h = im.size; s = MAXTEX / max(w, h)
        im.scale(max(1, int(w * s)), max(1, int(h * s))); n_scaled += 1
for im in bpy.data.images:
    if im.source in ('FILE', 'GENERATED') and im.packed_file is None:
        try: im.pack()
        except Exception as e: print("[master45] could not pack image", im.name, e)
    elif n_scaled and im.packed_file is not None and im.is_dirty:
        try: im.pack()
        except Exception as e: print("[master45] could not repack", im.name, e)
for fo in bpy.data.fonts:
    if fo.filepath and fo.filepath != "<builtin>" and not fo.packed_file:
        try: fo.pack()
        except Exception as e: print("[master45] font", fo.name, e)
print(f"[master45] scaled {n_scaled} images to <= {MAXTEX}px", flush=True)

# ---------------------------------------------------------------- 4. the master timeline
master.render.resolution_x, master.render.resolution_y, master.render.resolution_percentage = 1920, 816, 100
master.render.fps = FPS
se = master.sequence_editor_create()
strips = se.strips if hasattr(se, "strips") else se.sequences
frame = 1; ch_start = {}
for (sc, label, frames), (c, name, _, _) in zip(scenes, SHOTS):
    ch_start.setdefault(c, frame)
    st = strips.new_scene(name=name[:60], scene=sc, channel=1, frame_start=frame)
    if hasattr(st, "scene_input"):
        st.scene_input = 'CAMERA'
    n = sc.frame_end - sc.frame_start + 1
    master.timeline_markers.new(f"{name[:5]} {label.split(' ')[0]}", frame=frame)
    frame += n
END = frame - 1
master.frame_start, master.frame_end = 1, END
for c, vo in (("4", "vo/ch4_vo.mp3"), ("5", "vo/ch5_vo.mp3")):
    snd = strips.new_sound(f"Voiceover Ch{c}", os.path.join(ROOT, vo), channel=2 + int(c) - 4, frame_start=ch_start[c] + int(round(LEAD * FPS)))
    snd.sound.pack()
# fade from / to black: a black colour strip over the picture, opacity keyed 1->0 (1 s) and 0->1 (1.5 s)
for nm, f0, f1, a0, a1 in (("FadeIn", 1, 1 + FPS, 1.0, 0.0), ("FadeOut", END - int(1.5 * FPS) + 1, END, 0.0, 1.0)):
    try:
        col = strips.new_effect(name=nm, type='COLOR', channel=5, frame_start=f0, length=f1 - f0 + 1)
    except TypeError:
        col = strips.new_effect(name=nm, type='COLOR', channel=5, frame_start=f0, frame_end=f1 + 1)
    col.color = (0, 0, 0); col.blend_type = 'ALPHA_OVER'
    col.blend_alpha = a0; col.keyframe_insert("blend_alpha", frame=f0)
    col.blend_alpha = a1; col.keyframe_insert("blend_alpha", frame=f1)
master.timeline_markers.new("CH4", frame=ch_start["4"]); master.timeline_markers.new("CH5", frame=ch_start["5"])
cam = bpy.data.objects.new("FilmCam", bpy.data.cameras.new("FilmCam"))
master.collection.objects.link(cam); master.camera = cam
master.render.engine = 'CYCLES'
farm_ready(master)
master.render.use_sequencer = True
master.render.use_compositing = False          # each shot scene applies its own (plain) grade
master.render.filepath = "//render/nvidia_ch45_"
master.render.image_settings.file_format = 'PNG'
outp = os.path.join(OUT, "nvidia_ch45.blend")
bpy.ops.wm.save_as_mainfile(filepath=outp, compress=True)
info = dict(file=outp, mb=round(os.path.getsize(outp) / 1e6, 1), frames=END, shots=len(SHOTS),
            ch4_start=ch_start["4"], ch5_start=ch_start["5"], images=len(bpy.data.images), meshes=len(bpy.data.meshes),
            materials=len(bpy.data.materials), shared=dict(images=n_img, materials=n_mat, meshes=n_mesh), scaled=n_scaled,
            libraries=len(bpy.data.libraries))
json.dump(info, open(os.path.join(OUT, "master_info.json"), "w"), indent=1)
print("[master45] saved", info, flush=True)
