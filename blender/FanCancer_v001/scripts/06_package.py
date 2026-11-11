"""Shrink textures, pack, purge, check farm settings, save compressed.
blender -b work/anim.blend --python 06_package.py -- <out.blend>"""
import sys, os, bpy
out = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene
HERO = ("young_caucasian_female", "middleage_caucasian_male", "middleage_african_female")
n = 0
for im in bpy.data.images:
    if im.source != 'FILE' or not im.has_data and not im.filepath: continue
    try:
        w, h = im.size
    except Exception:
        continue
    lim = 2048 if any(k in im.name.lower() for k in HERO) and "diffuse" in im.name.lower() else 1024
    if im.name.lower().endswith(".hdr"): lim = 1024
    if max(w, h) > lim:
        s = lim / max(w, h); im.scale(max(1, int(w * s)), max(1, int(h * s))); n += 1
print("RESIZED", n)
bpy.ops.file.pack_all()
for im in bpy.data.images:
    if im.is_dirty:
        try: im.pack()
        except Exception as e: print("PACKFAIL", im.name, e)
for _ in range(3): bpy.data.orphans_purge(do_recursive=True)
# farm settings
r, cy = sc.render, sc.cycles
r.resolution_x, r.resolution_y, r.resolution_percentage = 1080, 1920, 100
r.fps, r.fps_base = 60, 1.0; sc.frame_start, sc.frame_end = 1, 2640
r.engine = 'CYCLES'; cy.device = 'CPU'; cy.samples = 48; cy.use_adaptive_sampling = True; cy.adaptive_threshold = 0.05
cy.use_denoising = True; cy.denoiser = 'OPENIMAGEDENOISE'; cy.texture_limit_render = 'OFF'
r.use_motion_blur = True; r.motion_blur_shutter = 0.5
sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Medium High Contrast'
r.image_settings.file_format = 'PNG'; r.image_settings.color_depth = '8'
base = os.path.splitext(os.path.basename(out))[0].replace("_60fps", "")
r.filepath = "//render/%s_" % base
cams = [o for o in bpy.data.objects if o.type == 'CAMERA']
probs = []
if len(cams) != 1: probs.append("cameras=%d" % len(cams))
if sc.timeline_markers and any(m.camera for m in sc.timeline_markers): probs.append("camera markers")
if bpy.data.libraries: probs.append("libraries")
unp = [i.name for i in bpy.data.images if i.source == 'FILE' and not i.packed_file]
if unp: probs.append("unpacked:" + ",".join(unp[:5]))
print("PROBLEMS", probs or "none")
bpy.ops.wm.save_as_mainfile(filepath=out, compress=True, relative_remap=True)
print("SAVED", out, round(os.path.getsize(out) / 2**20, 1), "MB")
