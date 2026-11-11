"""Before packing: cap texture sizes (keeps the .blend under ~150 MB), restore farm render settings, name the output.
blender -b film.blend --python 05_package_prep.py -- <out_prep.blend>
then:  blender -b <out_prep.blend> --python ../../pipeline/package_for_farm.py -- ../../SurgeonBrandsLivers_v002/SurgeonBrandsLivers_v002_60fps.blend"""
import sys, os
import bpy
OUT = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene
KEEP_2K = ("middleage_lightskinned_male", "middleage_darkskinned_female", "young_lightskinned_female", "Image_0", "Image_1")   # hero faces + the liver
import numpy as np
TX = os.path.join(os.path.dirname(OUT), "tx_pack"); os.makedirs(TX, exist_ok=True)
n = 0
for i_, im in enumerate(list(bpy.data.images)):
    if im.source != 'FILE' or im.size[0] == 0 or im.name == "BrandBurnMask":
        continue
    fp = (im.filepath or im.name).lower()
    if fp.endswith(".hdr"):
        continue
    cap = 2048 if any(k in im.name or k in im.filepath for k in KEEP_2K) else 1024
    w, h = im.size
    s_ = min(1.0, cap / max(w, h)); nw, nh = max(1, int(w * s_)), max(1, int(h * s_))
    alpha = False
    if fp.endswith(".png") and im.channels == 4:
        a_ = np.array(im.pixels[:])[3::4]
        alpha = a_.size and a_.min() < 0.98
    if fp.endswith((".jpg", ".jpeg")) and s_ >= 1.0:
        continue                                    # already compact
    if (nw, nh) != (w, h):
        im.scale(nw, nh)
    out = os.path.join(TX, "%03d_%s.%s" % (i_, bpy.path.clean_name(im.name), "png" if alpha else "jpg"))
    im.file_format = 'PNG' if alpha else 'JPEG'
    im.save(filepath=out, quality=90)
    cs = im.colorspace_settings.name
    im.filepath = out; im.reload(); im.colorspace_settings.name = cs
    n += 1
print("SCALED", n)
# decimate heavy background meshes (not people, not the liver)
for o in [o for o in bpy.data.objects if o.type == 'MESH']:
    if o.parent and o.parent.type == 'ARMATURE': continue
    if o.name.startswith(("Liver", "GhostLiver", "XRayLiver")): continue
    nf = len(o.data.polygons)
    if nf > 20000 and o.data.users == 1:
        d = o.modifiers.new("dec", 'DECIMATE'); d.ratio = max(0.15, 20000.0 / nf)
        bpy.context.view_layer.objects.active = o
        with bpy.context.temp_override(object=o, active_object=o):
            bpy.ops.object.modifier_apply(modifier="dec")
        print("DECIMATED", o.name, nf, "->", len(o.data.polygons))
r, cy = sc.render, sc.cycles
r.resolution_x, r.resolution_y, r.resolution_percentage = 1080, 1920, 100
r.fps, r.fps_base = 60, 1.0
cy.samples = 48; cy.use_adaptive_sampling = True; cy.adaptive_threshold = 0.05; cy.use_denoising = True
cy.texture_limit_render = 'OFF'
r.use_motion_blur = True; r.motion_blur_shutter = 0.5; r.motion_blur_position = 'START'   # no smear across the one-frame transit snaps
r.image_settings.file_format = 'PNG'; r.image_settings.color_mode = 'RGB'; r.image_settings.color_depth = '8'
for o in [o for o in bpy.data.objects if o.type == 'CAMERA' and o.name != "CAM_Film"]:
    bpy.data.objects.remove(o, do_unlink=True)
sc.camera = bpy.data.objects["CAM_Film"]
bpy.ops.outliner.orphans_purge(do_recursive=True)
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("PREP_SAVED", OUT)
