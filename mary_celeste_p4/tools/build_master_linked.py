"""Small MASTER.blend for the farm: its MASTER scene's sequencer holds every shot as a Scene strip whose scene is
LINKED from //shots/Sxx.blend (relative library paths), in VO order, frames 1..N. Render MASTER.blend, scene MASTER.
    blender -b --factory-startup --python tools/build_master_linked.py -- <PKG root (has shots/)>"""
import os, sys, json
import bpy
ROOT = sys.argv[sys.argv.index("--") + 1]
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "tools"))
from shots_vo import SHOTS
TIM = json.load(open(os.path.join(HERE, "vo", "vo_timings.json")))
OUT = os.path.join(ROOT, "MASTER.blend")
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.save_as_mainfile(filepath=OUT)                    # so relative library paths are taken from ROOT
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
r.filepath = "//frames/MC_P4_"
r.use_overwrite = False; r.use_placeholder = True
ed = m.sequence_editor_create(); strips = ed.strips if hasattr(ed, "strips") else ed.sequences
total = 0
for sid, _, _ in SHOTS:
    lib = os.path.join(ROOT, "shots", f"{sid}.blend")
    with bpy.data.libraries.load(lib, link=True, relative=True) as (src, dst):
        dst.scenes = [src.scenes[0]]
    sc = dst.scenes[0]
    t = TIM[sid]; n = t["frames"]
    assert (sc.frame_start, sc.frame_end) == (1, n), (sid, sc.frame_start, sc.frame_end, n)
    s = strips.new_scene(name=sid, scene=sc, channel=1, frame_start=1 + t["start"])
    s.scene_input = 'CAMERA'
    assert s.frame_final_start == 1 + t["start"] and s.frame_final_end == 1 + t["start"] + n
    total = max(total, t["start"] + n)
m.frame_start, m.frame_end = 1, total
m.view_settings.view_transform = 'AgX'; m.view_settings.look = 'AgX - Medium High Contrast'   # must match the shots
bpy.data.scenes.remove(blank)
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True, relative_remap=True)
print("MASTERLINKED", OUT, "frames", m.frame_start, m.frame_end, "libs", [l.filepath for l in bpy.data.libraries][:3], "...",
      len(bpy.data.libraries), round(os.path.getsize(OUT) / 1e6, 2), "MB", flush=True)
