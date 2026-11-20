"""Delivery layout (hub, final): <OUT>/MASTER.blend + <OUT>/shots/Sxx.blend.
Each shot file is self-contained (textures packed, compressed); MASTER.blend links the shot scenes from //shots/ and
holds them as Scene strips in VO order in its MASTER scene (render settings and //frames/ output as the master edit).

    blender -b --factory-startup --python tools/build_linked.py -- pack <PKG> <OUT>     (one shot per run: <SID>)
    blender -b --factory-startup --python tools/build_linked.py -- master <OUT>
"""
import os, sys, json
import bpy

argv = sys.argv[sys.argv.index("--") + 1:]
P5 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, P5)
from shots import SHOTS
FPS = 24

if argv[0] == "pack":
    PKG, OUT, sid = os.path.abspath(argv[1]), os.path.abspath(argv[2]), argv[3]
    bpy.ops.wm.open_mainfile(filepath=os.path.join(PKG, "shots", f"{sid}.blend"))
    sc = bpy.context.scene; sc.name = sid
    bpy.ops.file.pack_all()
    os.makedirs(os.path.join(OUT, "shots"), exist_ok=True)
    dst = os.path.join(OUT, "shots", f"{sid}.blend")
    sc.render.filepath = f"//../frames/{sid}/{sid}_"
    bpy.ops.wm.save_as_mainfile(filepath=dst, compress=True, relative_remap=True)
    print("PACKED", sid, round(os.path.getsize(dst) / 1e6, 1), "MB", flush=True)

elif argv[0] == "master":
    OUT = os.path.abspath(argv[1])
    tim = json.load(open(os.path.join(P5, "vo", "vo_timings.json")))
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "MASTER.blend"))     # so the library paths are //shots/
    m = bpy.context.scene; m.name = "MASTER"
    m.render.engine = 'CYCLES'
    m.render.resolution_x, m.render.resolution_y, m.render.resolution_percentage = 2560, 1440, 100
    m.render.fps = FPS
    m.cycles.samples = 64; m.cycles.use_adaptive_sampling = True; m.cycles.adaptive_threshold = 0.03; m.cycles.use_denoising = True
    try:
        m.cycles.denoiser = 'OPENIMAGEDENOISE'
    except Exception:
        pass
    m.render.image_settings.file_format = 'PNG'; m.render.image_settings.color_mode = 'RGB'; m.render.image_settings.color_depth = '16'
    m.render.filepath = "//frames/MaryCeleste_P5_"
    m.render.use_sequencer = True; m.render.use_compositing = False
    m.render.use_overwrite = False; m.render.use_placeholder = True
    se = m.sequence_editor_create()
    strips = se.strips if hasattr(se, "strips") else se.sequences
    f = 1
    for sid, *_ in SHOTS:
        path = f"//shots/{sid}.blend"
        with bpy.data.libraries.load(bpy.path.abspath(path), link=True, relative=True) as (src, dst):
            dst.scenes = [s for s in src.scenes if s == sid]
        sc = dst.scenes[0]
        n = int(round(float(tim[sid]) * FPS))
        st = strips.new_scene(name=sid, scene=sc, channel=1, frame_start=f)
        st.scene_input = 'CAMERA'; st.frame_final_duration = n
        f += n
    m.frame_start, m.frame_end = 1, f - 1
    for lib in bpy.data.libraries:
        lib.filepath = bpy.path.relpath(bpy.path.abspath(lib.filepath))
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "MASTER.blend"), compress=True, relative_remap=True)
    print("MASTER", m.frame_start, m.frame_end, [l.filepath for l in bpy.data.libraries][:3], flush=True)
