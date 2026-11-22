"""MASTER.blend for one intro film: scene MASTER sequences the film's shots as Scene strips LINKED from
//shots/<film><shot>.blend, back to back from frame 1. Render MASTER.blend, scene MASTER, frames 1..N.
    blender -b --factory-startup -P tools/build_master.py -- <film f1..f4> <PKG root (has shots/)>"""
import os, sys, importlib
import bpy
a = sys.argv[sys.argv.index("--") + 1:]
FILM, ROOT = a[0], a[1]
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [os.path.join(HERE, "films"), os.path.join(HERE, "lib")]
MODS = {"f1": "f1_lamp", "f2": "f2_letters", "f3": "f3_locksmith", "f4": "f4_salvage"}
src_txt = open(os.path.join(HERE, "films", MODS[FILM] + ".py")).read()
ns = {}
exec(src_txt[src_txt.index("SHOTS = dict("):].split("\n")[0], ns)          # the film's SHOTS (no Blender build)
SHOTS = ns["SHOTS"]
OUT = os.path.join(ROOT, "MASTER.blend")
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.save_as_mainfile(filepath=OUT)
blank = bpy.context.scene
m = bpy.data.scenes.new("MASTER")
r = m.render
r.resolution_x, r.resolution_y, r.resolution_percentage = 2560, 1440, 100
r.fps = 24
m.render.engine = 'CYCLES'
m.cycles.samples = 64; m.cycles.use_adaptive_sampling = True; m.cycles.adaptive_threshold = 0.03; m.cycles.use_denoising = True
try:
    m.cycles.denoiser = 'OPENIMAGEDENOISE'
except Exception:
    pass
r.use_sequencer = True; r.use_compositing = False
r.image_settings.file_format = 'PNG'; r.image_settings.color_mode = 'RGB'; r.image_settings.color_depth = '16'
r.filepath = f"//frames/SELDOM_{FILM.upper()}_"
r.use_overwrite = False; r.use_placeholder = True
ed = m.sequence_editor_create(); strips = ed.strips if hasattr(ed, "strips") else ed.sequences
start = 1; first = None
for sh in sorted(SHOTS, key=lambda k: SHOTS[k][0]):
    sid = f"{FILM}{sh}"
    lib = os.path.join(ROOT, "shots", f"{sid}.blend")
    with bpy.data.libraries.load(lib, link=True, relative=True) as (src, dst):
        dst.scenes = [src.scenes[0]]
    sc = dst.scenes[0]; first = first or sc
    n = sc.frame_end - sc.frame_start + 1
    s = strips.new_scene(name=sid, scene=sc, channel=1, frame_start=start)
    s.scene_input = 'CAMERA'
    assert s.frame_final_start == start and s.frame_final_end == start + n, (sid, s.frame_final_start, s.frame_final_end)
    print("STRIP", sid, start, start + n - 1, flush=True)
    start += n
m.frame_start, m.frame_end = 1, start - 1
camd = bpy.data.cameras.new("MASTER_cam"); camo = bpy.data.objects.new("MASTER_cam", camd); m.collection.objects.link(camo); m.camera = camo
for k in ("view_transform", "look", "exposure", "gamma"):                      # colour management copied from the shots
    setattr(m.view_settings, k, getattr(first.view_settings, k))
m.display_settings.display_device = first.display_settings.display_device
m.sequencer_colorspace_settings.name = first.sequencer_colorspace_settings.name
bpy.data.scenes.remove(blank)
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True, relative_remap=True)
print("MASTER", OUT, "frames", m.frame_start, m.frame_end, m.view_settings.view_transform, m.view_settings.look, flush=True)
