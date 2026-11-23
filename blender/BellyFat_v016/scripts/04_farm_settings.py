import bpy
sc = bpy.context.scene; cy = sc.cycles; r = sc.render
cy.max_bounces = 8; cy.diffuse_bounces = 3; cy.glossy_bounces = 3; cy.transmission_bounces = 8; cy.transparent_max_bounces = 8
cy.caustics_reflective = cy.caustics_refractive = False; r.use_persistent_data = True
cy.samples = 48; cy.adaptive_threshold = 0.05; cy.use_adaptive_sampling = True; cy.use_denoising = True; cy.denoiser = 'OPENIMAGEDENOISE'
r.use_motion_blur = False
r.image_settings.file_format = 'PNG'; r.image_settings.color_mode = 'RGB'; r.image_settings.color_depth = '8'; r.image_settings.compression = 15
sc.frame_start, sc.frame_end = 1, 1273
import os
sc.render.fps = 60; sc.render.fps_base = 1.0
if not sc.sequence_editor: sc.sequence_editor_create()
se = sc.sequence_editor
for s_ in list(getattr(se, "strips", getattr(se, "sequences", []))):
    if s_.type == "SOUND": (se.strips if hasattr(se, "strips") else se.sequences).remove(s_)
vo = os.path.join(os.path.dirname(os.path.abspath(bpy.data.filepath)), "BellyFat_v016_VO.mp3")
st = (se.strips if hasattr(se, "strips") else se.sequences).new_sound("VO", vo, 1, 1)
st.sound.pack(); print("VO strip", st.frame_final_duration)
import sys
bpy.ops.wm.save_as_mainfile(filepath=sys.argv[sys.argv.index("--") + 1])
