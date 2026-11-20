"""Small MASTER.blend for Part 3: the MASTER scene's Video Sequencer holds Scene strips LINKED from //shots/<id>.blend,
end to end at the VO timings. Rendering scene MASTER renders the whole part to //frames/.
    blender -b --factory-startup --python tools/build_master_linked.py -- <package dir>   (writes <package dir>/MASTER.blend)"""
import os, sys, json, re
import bpy
PKG = sys.argv[sys.argv.index("--") + 1]
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
order = re.findall(r'@shot\("(p3_[0-9a-z]+)"', open(os.path.join(HERE, "shots.py")).read())
tim = json.load(open(os.path.join(HERE, "vo", "vo_timings.json")))
out = os.path.join(PKG, "MASTER.blend")
bpy.ops.wm.save_as_mainfile(filepath=out)          # save first so the library paths can be relative (//shots/...)
master = bpy.context.scene; master.name = "MASTER"
master.sequence_editor_create(); strips = master.sequence_editor.strips
f = 1
for sid in order:
    lib = os.path.join(PKG, "shots", sid + ".blend")
    with bpy.data.libraries.load(lib, link=True, relative=True) as (src, dst):
        dst.scenes = [src.scenes[0]]
    sc = dst.scenes[0]
    n = int(round(tim[sid] * 24))
    st = strips.new_scene(name=sid, scene=sc, channel=1, frame_start=f)
    st.frame_final_duration = n
    st.scene_input = 'CAMERA'
    f += n
master.frame_start, master.frame_end = 1, f - 1
r = master.render
r.engine = 'CYCLES'; master.cycles.samples = 64; master.cycles.use_adaptive_sampling = True
master.cycles.adaptive_threshold = 0.03; master.cycles.use_denoising = True
r.resolution_x, r.resolution_y, r.resolution_percentage = 2560, 1440, 100
r.fps = 24; r.use_sequencer = True; r.use_compositing = False
r.image_settings.file_format = 'PNG'; r.image_settings.color_mode = 'RGB'; r.image_settings.color_depth = '16'
r.filepath = "//frames/mary_celeste_p3_"
r.use_overwrite = False; r.use_placeholder = True
for lib in bpy.data.libraries:
    lib.filepath = bpy.path.relpath(bpy.path.abspath(lib.filepath))
bpy.ops.wm.save_as_mainfile(filepath=out, compress=True, relative_remap=True)
print("MASTER", out, "frames", master.frame_start, master.frame_end, round(os.path.getsize(out) / 1e3, 1), "kB",
      [l.filepath for l in bpy.data.libraries][:2], flush=True)
