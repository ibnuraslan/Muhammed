"""Farm package under 95 MB (no LFS): resize every texture to <= 1K (HDRIs to 1K), purge orphans, pack, verify settings, save compressed.
blender -b anim.blend --python 04_package.py -- <tmp_tex_dir> <out.blend>"""
import sys, os
import bpy
TMP, OUT = sys.argv[sys.argv.index("--") + 1:][:2]
os.makedirs(TMP, exist_ok=True)
sc = bpy.context.scene
for m in bpy.data.materials:          # only what the scene uses goes in the package
    m.use_fake_user = False
for _ in range(3):
    bpy.data.orphans_purge(do_recursive=True)
# de-duplicate data that every prop instance imported again (same file / same mesh)
first = {}
for im in list(bpy.data.images):
    if im.source != 'FILE' or not im.filepath: continue
    k = bpy.path.abspath(im.filepath)
    if k in first: im.user_remap(first[k]); bpy.data.images.remove(im)
    else: first[k] = im
import hashlib
firsth = {}
for im in list(bpy.data.images):   # images embedded in GLBs that were imported several times
    if not im.packed_file: continue
    k = hashlib.md5(bytes(im.packed_file.data)).hexdigest()
    if k in firsth: im.user_remap(firsth[k]); bpy.data.images.remove(im)
    else: firsth[k] = im
firstm = {}
for me in list(bpy.data.meshes):
    if me.shape_keys or any(o.find_armature() for o in bpy.data.objects if o.data == me): continue
    k = (me.name.split(".")[0], len(me.vertices), len(me.polygons), round(sum(v.co.x for v in list(me.vertices)[::97]), 3))
    if k in firstm: me.user_remap(firstm[k]); bpy.data.meshes.remove(me)
    else: firstm[k] = me
SMALL = ("crate", "barrel", "jerrycan", "cement", "radio", "searchlight", "compressor", "generator", "boulder", "shrub", "tree_trunk", "dead_tree", "propane", "binocular")
LIMIT = 1024
n_res = 0
for i, im in enumerate(list(bpy.data.images)):
    if im.source != 'FILE' or not im.filepath: continue
    w, h = im.size[:]
    if w == 0: continue
    hdr = im.filepath.lower().endswith((".hdr", ".exr"))
    noncolor = im.colorspace_settings.name in ('Non-Color', 'Linear', 'Raw')
    lim = 512 if any(k in im.filepath.lower() for k in SMALL) else LIMIT
    if max(w, h) > lim or im.filepath.lower().endswith((".exr", ".png")):
        s = min(1.0, lim / max(w, h))
        if s < 1.0: im.scale(max(1, int(w * s)), max(1, int(h * s)))
        base = "img%03d_%s" % (i, os.path.splitext(os.path.basename(im.filepath))[0][:40])
        if im.filepath.lower().endswith(".hdr"):
            path = os.path.join(TMP, base + ".hdr"); im.file_format = 'HDR'
        elif im.depth in (32, 64) and not noncolor:
            path = os.path.join(TMP, base + ".png"); im.file_format = 'PNG'
        else:
            path = os.path.join(TMP, base + ".jpg"); im.file_format = 'JPEG'
        sc.render.image_settings.quality = 88
        im.filepath_raw = path; im.save()
        im.filepath = path; im.reload(); n_res += 1
print("RESIZED", n_res)
bpy.ops.file.pack_all()
for s_ in bpy.data.sounds:
    if not s_.packed_file: s_.pack()
r, cy = sc.render, sc.cycles
problems = []
if (r.resolution_x, r.resolution_y, r.resolution_percentage) != (1080, 1920, 100): problems.append("resolution")
if r.fps != 60 or r.fps_base != 1.0: problems.append("fps")
if r.engine != "CYCLES": problems.append("engine")
if len([o for o in bpy.data.objects if o.type == "CAMERA"]) != 1 or any(m.camera for m in sc.timeline_markers): problems.append("must be ONE camera, no camera markers")
if bpy.data.libraries: problems.append("linked libraries")
if [i.name for i in bpy.data.images if i.source == "FILE" and not i.packed_file]: problems.append("unpacked images")
r.filepath = "//render/NukedWell_v002_"
print("FARM", dict(res=(r.resolution_x, r.resolution_y), fps=r.fps, frames=(sc.frame_start, sc.frame_end), samples=cy.samples,
                   thr=cy.adaptive_threshold, denoise=cy.use_denoising, mblur=(r.use_motion_blur, r.motion_blur_shutter),
                   view=(sc.view_settings.view_transform, sc.view_settings.look), fmt=r.image_settings.file_format, out=r.filepath))
print("PROBLEMS", problems or "none")
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True, relative_remap=True)
print("SAVED", OUT, os.path.getsize(OUT) // 2**20, "MB")
