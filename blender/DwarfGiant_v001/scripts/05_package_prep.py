"""Shrink for a <95 MB normal-git package, set farm settings, then hand off to pipeline/package_for_farm.py.
blender -b film.blend --python 05_package_prep.py -- <out.blend>"""
import bpy, sys, os
out = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene
bpy.data.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)
HERO_2K = ("young_lightskinned_male_diffuse", "sss")   # hero face close-ups keep 2K skin
for im in bpy.data.images:
    if im.source != "FILE" or not im.has_data and not os.path.exists(bpy.path.abspath(im.filepath)): continue
    try:
        w, h = im.size
        lim = 2048 if any(k in im.name for k in HERO_2K) else (512 if any(k in im.name.lower() for k in ("_ao", "rough", "metal", "spec")) else 1024)
        if max(w, h) > lim:
            f = lim / max(w, h); im.scale(max(1, int(w * f)), max(1, int(h * f)))
            im.pack()
    except Exception as e:
        print("IMG ERR", im.name, e)
# farm render settings
r, cy = sc.render, sc.cycles
r.resolution_x, r.resolution_y, r.resolution_percentage = 1080, 1920, 100
r.fps, r.fps_base = 60, 1.0
r.engine = "CYCLES"; cy.device = "CPU"; cy.samples = 48; cy.adaptive_threshold = 0.05; cy.use_adaptive_sampling = True
cy.use_denoising = True; cy.denoiser = "OPENIMAGEDENOISE"; cy.texture_limit_render = "OFF"
r.use_motion_blur = True; r.motion_blur_shutter = 0.5
cy.max_bounces = 8; cy.diffuse_bounces = 3; cy.glossy_bounces = 3; cy.transmission_bounces = 8; cy.transparent_max_bounces = 16
cy.caustics_reflective = False; cy.caustics_refractive = False; r.use_persistent_data = True
r.image_settings.file_format = "PNG"; r.image_settings.color_mode = "RGB"; r.image_settings.color_depth = "8"
sc.view_settings.view_transform = "AgX"; sc.view_settings.look = "AgX - Medium High Contrast"
# hide every helper from render
for o in bpy.data.objects:
    if o.type == "EMPTY": o.hide_render = True
bpy.ops.wm.save_as_mainfile(filepath=out, compress=True)
print("PREP SAVED", out, os.path.getsize(out) // 2**20, "MB")
