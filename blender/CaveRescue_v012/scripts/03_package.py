"""CaveRescue v012 stage C: package. blender -b film.blend --python 03_package.py -- <out.blend>
Textures: vegetation to 512 px, everything else to max 1024 px (the logo kept), re-saved as JPEG (PNG where alpha is
needed) and packed; orphans purged; compressed save."""
import bpy, sys, os, tempfile
OUT = sys.argv[sys.argv.index("--") + 1]
TMP = tempfile.mkdtemp(prefix="pkgimg_")
VEG = ("tree", "pachira", "fern", "boulder")
sc = bpy.context.scene
sc.render.image_settings.quality = 88
for i, im in enumerate(list(bpy.data.images)):
    if im.source != 'FILE' or "DaKras" in im.name: continue
    n = im.name.lower()
    if n.endswith((".hdr", ".exr")): continue
    _ = im.pixels[0] if len(im.pixels) else None          # force load (packed images report size 0 until loaded)
    if im.size[0] == 0: print("SKIP", im.name); continue
    lim = 512 if any(k in n for k in VEG) else 1024
    if max(im.size) > lim:
        s = lim / max(im.size); im.scale(max(1, int(im.size[0] * s)), max(1, int(im.size[1] * s)))
    alpha = any(k in n for k in ("leaves", "leaf", "alpha", "opacity", "fern", "lash", "brow", "short", "pony"))
    fn = os.path.join(TMP, "%03d.%s" % (i, "png" if alpha else "jpg"))
    im.filepath_raw = fn; im.file_format = 'PNG' if alpha else 'JPEG'
    im.save()
    if im.packed_file: im.unpack(method='REMOVE')
    im.filepath = fn; im.reload(); im.pack()
bpy.ops.file.pack_all()
for _ in range(3): bpy.ops.outliner.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)
sc.render.filepath = "//render/CaveRescue_v012_####"; sc.render.image_settings.file_format = 'PNG'
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1080, 1920, 100
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print("PACKAGE_DONE", OUT)
