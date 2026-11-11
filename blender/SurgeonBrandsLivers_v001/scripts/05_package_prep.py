"""Before packing: cap texture sizes (keeps the .blend under ~150 MB), restore farm render settings, name the output.
blender -b film.blend --python 05_package_prep.py -- <out_prep.blend>
then:  blender -b <out_prep.blend> --python ../../pipeline/package_for_farm.py -- ../../SurgeonBrandsLivers_v002/SurgeonBrandsLivers_v002_60fps.blend"""
import sys, os
import bpy
OUT = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene
KEEP_2K = ("middleage_lightskinned_male", "middleage_darkskinned_female", "young_lightskinned_female", "female_casualsuit02", "hospital_room_2")
n = 0
for im in bpy.data.images:
    if im.source != 'FILE' or im.size[0] == 0:
        continue
    cap = 2048 if any(k in im.name or k in im.filepath for k in KEEP_2K) else 1024
    w, h = im.size
    if max(w, h) > cap:
        s = cap / max(w, h)
        im.scale(max(1, int(w * s)), max(1, int(h * s)))
        im.pack()             # scaled pixels are stored inside the file (PNG)
        n += 1
print("SCALED", n)
r, cy = sc.render, sc.cycles
r.resolution_x, r.resolution_y, r.resolution_percentage = 1080, 1920, 100
r.fps, r.fps_base = 60, 1.0
cy.samples = 48; cy.use_adaptive_sampling = True; cy.adaptive_threshold = 0.05; cy.use_denoising = True
cy.texture_limit_render = 'OFF'
r.use_motion_blur = True; r.motion_blur_shutter = 0.5
r.image_settings.file_format = 'PNG'; r.image_settings.color_mode = 'RGB'; r.image_settings.color_depth = '8'
for o in [o for o in bpy.data.objects if o.type == 'CAMERA' and o.name != "CAM_Film"]:
    bpy.data.objects.remove(o, do_unlink=True)
sc.camera = bpy.data.objects["CAM_Film"]
bpy.ops.outliner.orphans_purge(do_recursive=True)
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("PREP_SAVED", OUT)
