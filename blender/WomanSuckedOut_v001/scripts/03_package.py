"""Phase 2 package: VO sound strip from frame 1, render settings, all images packed, compressed save.
blender -b p1.blend --python 03_package.py -- <out.blend> <vo.mp3>"""
import bpy, sys
a = sys.argv[sys.argv.index("--") + 1:]; OUT, VO = a[0], a[1]
sc = bpy.context.scene
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1080, 1920, 100
sc.render.fps = 60; sc.frame_start = 1; sc.frame_end = 1651; sc.frame_step = 1
sc.cycles.samples = 48; sc.cycles.adaptive_threshold = 0.05; sc.cycles.use_denoising = True
sc.render.use_motion_blur = False
sc.render.image_settings.file_format = 'PNG'
sc.render.filepath = "####"
if not sc.sequence_editor: sc.sequence_editor_create()
se = sc.sequence_editor
strips = getattr(se, "strips", None) or se.sequences
for s in list(strips): strips.remove(s)
snd = strips.new_sound("VO", VO, channel=1, frame_start=1)
bpy.ops.outliner.orphans_purge(do_recursive=True)
bpy.ops.file.pack_all()
for snd_ in bpy.data.sounds:
    if not snd_.packed_file: snd_.pack()
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print("PACKED", OUT, sc.frame_start, sc.frame_end, len(bpy.data.images))
