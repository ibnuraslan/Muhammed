"""Farm settings + VO strip. blender -b work/film_look.blend -P 04_finish.py -- <out.blend> <vo.mp3>"""
import bpy, sys, os
a = sys.argv[sys.argv.index("--") + 1:]; out, vo = a[0], a[1]
sc = bpy.context.scene
r = sc.render; r.resolution_x, r.resolution_y, r.resolution_percentage = 1080, 1920, 100; r.fps = 60; r.fps_base = 1.0
r.engine = 'CYCLES'; sc.cycles.samples = 48; sc.cycles.adaptive_threshold = 0.05; sc.cycles.use_adaptive_sampling = True
sc.cycles.use_denoising = True; sc.cycles.denoiser = 'OPENIMAGEDENOISE'; r.use_motion_blur = False
r.image_settings.file_format = 'PNG'; r.use_simplify = False
sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Punchy'
if not sc.sequence_editor: sc.sequence_editor_create()
se = sc.sequence_editor
strips = se.strips if hasattr(se, "strips") else se.sequences
for st in list(strips): strips.remove(st)
snd = strips.new_sound("VO", vo, channel=1, frame_start=1)
print("VO strip", snd.frame_final_start, snd.frame_final_end, "film", sc.frame_start, sc.frame_end)
bpy.ops.wm.save_as_mainfile(filepath=out, compress=True)
