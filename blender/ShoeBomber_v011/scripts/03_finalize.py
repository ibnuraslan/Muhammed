"""ShoeBomber v011 stage C: VO strip, farm render settings, purge. Then run pipeline/package_for_farm.py.
blender -b anim.blend --python 03_finalize.py -- <out.blend>"""
import bpy, sys
OUT = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene
VO = "/home/user/Muhammed/blender/ShoeBomber_v011/ShoeBomber_v011_VO.mp3"
if not sc.sequence_editor: sc.sequence_editor_create()
se = sc.sequence_editor
strips = se.strips if hasattr(se, "strips") else se.sequences
for s in list(strips): strips.remove(s)
snd = strips.new_sound("VO", VO, channel=1, frame_start=1)
snd.sound.pack()
r = sc.render; cy = sc.cycles
r.resolution_x, r.resolution_y, r.resolution_percentage = 1080, 1920, 100
r.fps, r.fps_base = 60, 1.0
sc.frame_start, sc.frame_end = 1, 1469
r.image_settings.file_format = 'PNG'; r.image_settings.color_mode = 'RGBA'
r.use_stamp = False
cy.samples = 64; cy.use_adaptive_sampling = True; cy.adaptive_threshold = 0.04
cy.use_denoising = True; cy.denoiser = 'OPENIMAGEDENOISE'
try:
    cy.denoising_input_passes = 'RGB_ALBEDO_NORMAL'
except Exception: pass
cy.max_bounces = 6; cy.diffuse_bounces = 3; cy.glossy_bounces = 3; cy.transmission_bounces = 6; cy.transparent_max_bounces = 16
cy.caustics_reflective = False; cy.caustics_refractive = False
r.use_persistent_data = True; r.use_simplify = True; r.simplify_subdivision_render = 2; cy.texture_limit_render = '2048'
r.use_motion_blur = False
cy.device = 'CPU'
for o in [o for o in bpy.data.objects if o.name in ("SeatSrc",)]:
    bpy.data.objects.remove(o, do_unlink=True)     # instanced seat source (hidden); the seats keep the mesh
# texture budget: 1K for everything, 2K for the hero sneakers (package < 80 MB). Image.pack() keeps alpha (LESSONS 3).
for im in bpy.data.images:
    if im.source != 'FILE' or im.size[0] == 0: continue
    lim = 2048 if any(k in im.name.lower() for k in ("image_0", "image_1")) and im.size[0] <= 1024 else 1024
    w, h = im.size
    if max(w, h) > lim:
        k = lim / max(w, h); im.scale(int(w * k), int(h * k)); im.pack()
        print("SHRINK", im.name, (w, h), "->", tuple(im.size))
bpy.ops.outliner.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print("FINAL_OK", OUT)
