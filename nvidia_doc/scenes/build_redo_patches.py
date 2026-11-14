"""Bake the 14 redo shots and build one small farm-style patch .blend per shot, the same way as the c5_17 patch:
a factory master scene that plays the baked shot scene(s) as sequencer strips, so the colour/brightness path is
identical to the delivered nvidia_ch45.blend. Frame counts are exactly those of the shots they replace.
  python scenes/build_redo_patches.py [c4_03 c5_14 ...]   -> out/deliver/ch45_redo/<id>_patch.blend + patches.json
Bakes go to out/blend/redo/ (resumable: an existing baked part is reused unless --rebake)."""
import os, sys, json, subprocess, hashlib
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(ROOT, "edit"))
from redo_ch45 import table
PY = sys.executable
BAKED = os.path.join(ROOT, "out", "blend", "redo"); os.makedirs(BAKED, exist_ok=True)
OUT = os.path.join(ROOT, "out", "deliver", "ch45_redo"); os.makedirs(OUT, exist_ok=True)
only = [a for a in sys.argv[1:] if not a.startswith("--")]
rebake = "--rebake" in sys.argv

rows = [r for r in table() if not only or r["id"] in only]
for r in rows:                                   # 1. bake every part (one process each: clean scene, no stale caches)
    for st, mv, role in r["parts"]:
        name = f"{r['id']}_{st}_{mv}"
        path = os.path.join(BAKED, name + ".blend")
        if os.path.exists(path) and not rebake:
            continue
        cmd = [PY, os.path.join(HERE, "bake.py"), st, mv, "--seconds", f"{r['frames'] / 24:.6f}", "--out", BAKED,
               "--name", name, "--samples", "32", "--step", "2"]
        print("[redo] bake", name, r["frames"], "frames", flush=True)
        rc = subprocess.run(cmd, cwd=HERE).returncode
        if rc != 0:
            raise SystemExit(f"bake failed: {name}")

# 2. one patch per shot, built in a fresh Blender session each (a separate process per shot keeps them independent)
if "--patch-one" not in sys.argv:
    info = {}
    for r in rows:
        rc = subprocess.run([PY, __file__, r["id"], "--patch-one"], cwd=HERE).returncode
        if rc != 0:
            raise SystemExit(f"patch failed: {r['id']}")
        info[r["id"]] = json.load(open(os.path.join(OUT, f"{r['id']}_patch.json")))
    allinfo = {}
    pj = os.path.join(OUT, "patches.json")
    if os.path.exists(pj):
        allinfo = json.load(open(pj))
    allinfo.update(info)
    json.dump(allinfo, open(pj, "w"), indent=1)
    print("[redo] patches:", {k: (v["frames"], v["mb"]) for k, v in info.items()})
    sys.exit(0)

import bpy
import grade
r = rows[0]
bpy.ops.wm.read_factory_settings(use_empty=True)
m = bpy.context.scene; m.name = f"PATCH_{r['id'].upper()}"
scenes = []
for st, mv, role in r["parts"]:
    name = f"{r['id']}_{st}_{mv}"
    with bpy.data.libraries.load(os.path.join(BAKED, name + ".blend"), link=False) as (src, dst):
        dst.scenes = src.scenes[:1]
    sc = dst.scenes[0]; sc.name = name
    if role != "title":
        grade.add_grade(sc, look="plain")
    else:
        sc.render.film_transparent = True
    sc.cycles.samples = 32; sc.cycles.use_adaptive_sampling = True; sc.cycles.adaptive_threshold = 0.05; sc.cycles.use_denoising = True
    sc.render.use_motion_blur = False; sc.render.fps = 24
    sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1920, 816, 100
    if role in ("left", "right"):                  # render only the middle half: 960 px wide, half the sensor width
        sc.render.resolution_x = 960               # = the middle 960 px of the full 1920 frame, at half the cost
        sc.camera.data.sensor_fit = 'HORIZONTAL'; sc.camera.data.sensor_width *= 0.5
    n = sc.frame_end - sc.frame_start + 1
    assert n == r["frames"], (name, n, r["frames"])
    scenes.append((sc, role))
for lib in list(bpy.data.libraries):
    bpy.data.libraries.remove(lib)
se = m.sequence_editor_create(); strips = se.strips if hasattr(se, "strips") else se.sequences
for k, (sc, role) in enumerate(scenes):
    ch = {"full": 1, "left": 1, "right": 2, "title": 4}[role]
    st = strips.new_scene(name=sc.name[:60], scene=sc, channel=ch, frame_start=1)
    if hasattr(st, "scene_input"):
        st.scene_input = 'CAMERA'
    if role in ("left", "right"):                  # each 960 px half placed on its side, unscaled
        if hasattr(st, "fit_method"):
            st.fit_method = 'ORIGINAL'
        st.transform.scale_x = st.transform.scale_y = 1.0
        st.transform.offset_x = -480 if role == "left" else 480
        if role == "right":
            st.blend_type = 'ALPHA_OVER'
    if role == "title":
        st.blend_type = 'ALPHA_OVER'
if any(role == "right" for _, role in scenes):     # a thin dark divider between the halves
    try:
        div = strips.new_effect(name="Divider", type='COLOR', channel=3, frame_start=1, length=r["frames"])
    except TypeError:
        div = strips.new_effect(name="Divider", type='COLOR', channel=3, frame_start=1, frame_end=r["frames"] + 1)
    div.color = (0.0, 0.0, 0.0); div.blend_type = 'ALPHA_OVER'
    if hasattr(div, "fit_method"):
        div.fit_method = 'ORIGINAL'
    div.transform.scale_x = 4 / 1920             # a 4 px dark line down the middle
m.frame_start, m.frame_end = 1, r["frames"]
m.render.resolution_x, m.render.resolution_y, m.render.resolution_percentage = 1920, 816, 100
m.render.fps = 24; m.render.engine = 'CYCLES'
m.cycles.samples = 32; m.cycles.use_adaptive_sampling = True; m.cycles.adaptive_threshold = 0.05; m.cycles.use_denoising = True
m.render.use_sequencer = True; m.render.use_compositing = False; m.render.film_transparent = False
cam = bpy.data.objects.new("FilmCam", bpy.data.cameras.new("FilmCam")); m.collection.objects.link(cam); m.camera = cam
m.render.filepath = f"//render/{r['id']}_"; m.render.image_settings.file_format = 'PNG'
for im in bpy.data.images:
    if im.source == 'FILE' and im.packed_file is None:
        try: im.pack()
        except Exception as e: print("[redo] pack", im.name, e)
for fo in bpy.data.fonts:
    if fo.filepath and fo.filepath != "<builtin>" and not fo.packed_file:
        try: fo.pack()
        except Exception as e: print("[redo] font", fo.name, e)
out = os.path.join(OUT, f"{r['id']}_patch.blend")
bpy.context.window.scene = m if bpy.context.window else None
bpy.ops.wm.save_as_mainfile(filepath=out, compress=True)
inf = dict(id=r["id"], file=os.path.relpath(out, ROOT), scene=m.name, frames=r["frames"], master_in=r["master_in"],
           master_out=r["master_out"], replaces=r["old_name"], mb=round(os.path.getsize(out) / 1e6, 2),
           sha256=hashlib.sha256(open(out, "rb").read()).hexdigest(), libraries=len(bpy.data.libraries))
json.dump(inf, open(os.path.join(OUT, f"{r['id']}_patch.json"), "w"), indent=1)
print("[redo] saved", inf, flush=True)
