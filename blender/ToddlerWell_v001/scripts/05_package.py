"""Farm package: shrink textures (characters 1K, crowd 512, set textures stay 2K), pack everything, check farm settings, save compressed.
blender -b work/film.blend --python scripts/05_package.py -- ../ToddlerWell_v002/ToddlerWell_v002_60fps.blend"""
import sys, os
import bpy
OUT = os.path.abspath(sys.argv[sys.argv.index("--") + 1])
TMP = os.path.abspath("work/packtex"); os.makedirs(TMP, exist_ok=True)
sc = bpy.context.scene
KEEP2K = ()      # everything to 1K (or 512 for crowd-only textures) to stay under 95 MB
CROWD = ("Crowd",)
users = {}
for m in bpy.data.materials:
    if m.node_tree:
        for n in m.node_tree.nodes:
            if n.type == "TEX_IMAGE" and n.image: users.setdefault(n.image.name, set()).add(m.name)
ALPHA = ("short0", "bob0", "ponytail", "long0", "afro", "eyebrow", "eyelash", "leaves", "shrub", "grass", "_alpha", "opacity")
SMALL = ("tree", "shrub", "grass", "bucket", "pickup", "crowd")
for im in list(bpy.data.images):
    if im.source != "FILE" or im.size[0] == 0: continue
    if im.packed_file: im.unpack(method="WRITE_LOCAL") if False else None
    name = im.name; low = (name + " " + im.filepath).lower()
    mats = users.get(name, set())
    tgt = 512 if (any(k in low for k in SMALL) or "nor" in low or "normal" in low or (mats and all(("Crowd" in u or "Operator" in u) for u in mats))) else 1024
    w, h = im.size
    if max(w, h) > tgt: im.scale(tgt, max(1, round(h * tgt / w)))
    is_data = im.colorspace_settings.name == "Non-Color"
    ext = ".png" if any(k in low for k in ALPHA) else ".jpg"
    path = os.path.join(TMP, bpy.path.clean_name(name) + ext)
    im.filepath_raw = path; im.file_format = "PNG" if ext == ".png" else "JPEG"
    im.save()
    if im.packed_file: im.unpack(method="REMOVE")
    im.filepath = path; im.reload()
    if is_data: im.colorspace_settings.name = "Non-Color"
bpy.data.orphans_purge(do_recursive=True)
bpy.ops.file.pack_all()
r, cy = sc.render, sc.cycles
r.resolution_x, r.resolution_y, r.resolution_percentage = 1080, 1920, 100
r.fps, r.fps_base = 60, 1.0; r.engine = "CYCLES"; cy.samples = 48; cy.adaptive_threshold = 0.05; cy.use_denoising = True
r.use_motion_blur = True; r.motion_blur_shutter = 0.5
r.image_settings.file_format = "PNG"; r.image_settings.color_mode = "RGB"; r.image_settings.color_depth = "8"
r.use_persistent_data = True
problems = []
if [o for o in bpy.data.objects if o.type == "CAMERA"].__len__() != 1 or any(m.camera for m in sc.timeline_markers): problems.append("camera")
if bpy.data.libraries: problems.append("linked libraries")
if [i.name for i in bpy.data.images if i.source == "FILE" and not i.packed_file]: problems.append("unpacked images")
r.filepath = "//render/ToddlerWell_v002_"
sc.frame_set(1)
print("FARM", dict(res=(r.resolution_x, r.resolution_y), fps=r.fps, frames=(sc.frame_start, sc.frame_end), samples=cy.samples,
                   denoise=cy.use_denoising, mblur=(r.use_motion_blur, r.motion_blur_shutter), view=(sc.view_settings.view_transform, sc.view_settings.look)))
print("PROBLEMS", problems or "none")
os.makedirs(os.path.dirname(OUT), exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True, relative_remap=True)
print("SAVED", OUT, os.path.getsize(OUT) // 2**20, "MB")
