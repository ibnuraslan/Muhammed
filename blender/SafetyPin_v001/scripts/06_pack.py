"""Shrink textures, dedupe, pack, farm settings, save.  blender -b vo.blend --python 06_pack.py -- out.blend texdir
- duplicate images (same source file) are merged
- character maps max 1024, set/prop maps max 512 (hero paper textures kept), EXR/PNG -> JPEG unless they carry alpha
- images re-saved with Image.save() (keeps alpha: LESSONS 3, black hairline)"""
import bpy, sys, os
a = sys.argv[sys.argv.index("--") + 1:]; OUT, TD = a[0], a[1]
os.makedirs(TD, exist_ok=True); sc = bpy.context.scene
# 1) dedupe by absolute source path
seen = {}
for im in list(bpy.data.images):
    if im.source != 'FILE': continue
    key = bpy.path.abspath(im.filepath)
    if key in seen and seen[key] != im:
        im.user_remap(seen[key]); bpy.data.images.remove(im)
    else: seen[key] = im
KEEP = ("newspaper", "patent", "debtnote", "banknote", "DaKras")
n = 0
for im in list(bpy.data.images):
    if im.source != 'FILE' or im.size[0] == 0: continue
    nm = im.name; path = bpy.path.abspath(im.filepath)
    if any(k.lower() in nm.lower() for k in KEEP): continue
    char = any(k in path for k in ("mpfb", "skins", "clothes", "hair", "eyes", "teeth", "textures/", "pkg", "work/textures")) and "assets/" not in path
    lim = 1024 if char else 512
    alpha = any(k in nm.lower() for k in ("alpha", "hair", "short0", "eyebrow", "eyelash", "logo", "leaf", "leaves", "shrub", "tree")) or (im.channels == 4 and path.lower().endswith(".png"))
    w, h = im.size
    if max(w, h) > lim: im.scale(max(1, w * lim // max(w, h)), max(1, h * lim // max(w, h)))
    fmt = 'PNG' if alpha else 'JPEG'
    new = os.path.join(TD, "%03d_%s.%s" % (n, bpy.path.clean_name(nm), "png" if alpha else "jpg")); n += 1
    im.filepath_raw = new; im.file_format = fmt
    try:
        im.save()
    except Exception as e:
        print("SAVE_FAIL", nm, e); continue
    im.filepath = new; im.reload()
print("TEX", n, "images re-saved")
bpy.ops.outliner.orphans_purge(do_recursive=True)
bpy.ops.file.pack_all()
for s in bpy.data.sounds:
    if not s.packed_file: s.pack()
r = sc.render
r.resolution_x, r.resolution_y, r.resolution_percentage = 1080, 1920, 100; r.fps = 60; r.fps_base = 1.0
r.engine = 'CYCLES'; sc.cycles.samples = 48; sc.cycles.adaptive_threshold = 0.05; sc.cycles.use_denoising = True
r.use_motion_blur = False; r.image_settings.file_format = 'PNG'
base = os.path.splitext(os.path.basename(OUT))[0].replace("_60fps", "")
r.filepath = "//render/%s_" % base
print("UNPACKED", [i.name for i in bpy.data.images if i.source == 'FILE' and not i.packed_file])
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True, relative_remap=True)
print("SAVED", OUT, os.path.getsize(OUT) // 2**20, "MB")
