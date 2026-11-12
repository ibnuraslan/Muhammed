"""Shrink textures (1K, JPEG except alpha cut-outs), purge orphans, then run pipeline/package_for_farm.py.
blender -b film.blend --python 04_package.py -- <out.blend> <tmp_dir> [maxres]"""
import sys, os, bpy
a = sys.argv[sys.argv.index("--") + 1:]
OUT, TMP = a[0], a[1]; MAXR = int(a[2]) if len(a) > 2 else 1024
os.makedirs(TMP, exist_ok=True)
ALPHA_KEYS = ("hair", "eyebrow", "eyelash", "ponytail", "afro", "bob0", "short0", "braid", "long01", "lashes", "brow")
def needs_alpha(im):
    n = im.name.lower(); fp = (im.filepath or "").lower()
    return any(k in n or k in fp for k in ALPHA_KEYS)
for i, im in enumerate(list(bpy.data.images)):
    if im.source != "FILE" or im.type != "IMAGE": continue
    if im.name.lower().endswith((".hdr", ".exr")) and "hdri" not in (im.filepath or "").lower() and "golf" not in im.name: pass
    if "golf" in im.name: continue                        # keep the 1K HDRI as is
    try:
        w, h = im.size
    except Exception:
        continue
    if w == 0: continue
    lim = 2048 if (("young_caucasian_male2" in (im.filepath or "") or "young_lightskinned_male_diffuse2" in im.name) and "diffuse" in im.name.lower()) else MAXR
    if max(w, h) > lim:
        s = lim / max(w, h); im.scale(max(1, int(w * s)), max(1, int(h * s)))
    alpha = needs_alpha(im)
    ext = ".png" if alpha else ".jpg"
    p = os.path.join(TMP, "tex_%03d%s" % (i, ext))
    im.filepath_raw = p; im.file_format = "PNG" if alpha else "JPEG"
    try:
        im.save()
    except Exception as e:
        print("SAVE_FAIL", im.name, e); continue
    if im.packed_file: im.unpack(method="REMOVE")
    im.filepath = p; im.reload(); im.pack()
bpy.data.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)
sys.argv = [sys.argv[0], "--", OUT]
exec(open("/home/user/Muhammed/blender/pipeline/package_for_farm.py").read())
