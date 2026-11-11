"""Before packing: merge duplicate images, cap sizes and re-encode, so the packed .blend stays under ~95 MB (no LFS).
blender -b anim.blend --python slim_textures.py -- out.blend
- duplicates (x.png.001 of x.png) are merged
- HDRIs -> 1K Radiance .hdr; the hero male skin -> 2K; everything else -> 1K
- images that need alpha (hair, brows, lashes, leaves) stay PNG; all others are re-encoded as JPEG q90"""
import sys, os, re, tempfile, bpy
out = sys.argv[sys.argv.index("--") + 1]
tmp = tempfile.mkdtemp(prefix="slim_")
base = lambda n: re.sub(r"\.\d{3}$", "", n)
first = {}
for im in list(bpy.data.images):
    if im.source != "FILE": continue
    k = base(im.name)
    if k in first and tuple(first[k].size) == tuple(im.size):
        im.user_remap(first[k]); bpy.data.images.remove(im)
    else:
        first.setdefault(k, im)
ALPHA = ("hair", "short02", "ponytail", "eyebrow", "eyelash", "leaves", "leaf", "alpha", "opacity")
n = 0
for i, im in enumerate(list(bpy.data.images)):
    if im.source != "FILE" or im.size[0] == 0: continue
    nm = im.name.lower(); hdr = nm.endswith(".hdr")
    cap = 1024 if hdr else (2048 if "lightskinned_male_diffuse" in nm else 1024)
    w, h = im.size
    if max(w, h) > cap:
        s = cap / max(w, h); im.scale(int(w * s), int(h * s))
    if hdr: fmt, ext = "HDR", ".hdr"
    elif any(a in nm for a in ALPHA): fmt, ext = "PNG", ".png"
    else: fmt, ext = "JPEG", ".jpg"
    p = os.path.join(tmp, "img%03d%s" % (i, ext))
    cs = im.colorspace_settings.name
    im.filepath_raw = p; im.file_format = fmt
    sc = bpy.context.scene; sc.render.image_settings.quality = 90
    im.save(filepath=p, quality=90) if fmt == "JPEG" else im.save(filepath=p)
    if im.packed_file: im.unpack(method="REMOVE")
    im.filepath = p; im.reload(); im.colorspace_settings.name = cs; im.pack(); n += 1
bpy.ops.outliner.orphans_purge(do_recursive=True)
print("SLIM re-encoded", n, "images; total images", len(bpy.data.images),
      "packed MB", sum(i.packed_file.size for i in bpy.data.images if i.packed_file) // 2**20)
bpy.ops.wm.save_as_mainfile(filepath=out)
