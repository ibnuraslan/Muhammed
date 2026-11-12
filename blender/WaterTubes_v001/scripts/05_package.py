"""Farm package: downsize packed textures (1K; 2K for hero skin/face/clothes), drop helpers, purge orphans, then run pipeline/package_for_farm.py.
blender -b fx.blend --python 05_package.py -- <out.blend>"""
import bpy, sys, os
OUT = sys.argv[sys.argv.index("--") + 1]
HERE = os.path.dirname(os.path.abspath(__file__))
sc = bpy.context.scene
# final farm settings
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1080, 1920, 100
sc.cycles.samples = 48; sc.cycles.adaptive_threshold = 0.05; sc.cycles.use_denoising = True
sc.render.use_motion_blur = False   # animated-CG look: no motion blur
sc.render.image_settings.file_format = "PNG"; sc.cycles.texture_limit_render = "OFF"
# remove the asset library source objects (their mesh data stays used by the placed instances)
for o in list(bpy.data.objects):
    if o.users_collection and all(c.name == "AssetLib" for c in o.users_collection):
        bpy.data.objects.remove(o)
lib = bpy.data.collections.get("AssetLib")
if lib: bpy.data.collections.remove(lib)
# any extra cameras (none expected)
for o in [o for o in bpy.data.objects if o.type == "CAMERA" and o != sc.camera]: bpy.data.objects.remove(o)
for _ in range(3): bpy.data.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)
import tempfile
TMP = tempfile.mkdtemp()
BIG = ("male_casualsuit02", "female_casualsuit02", "skinned", "caucasian", "african", "grass_ground", "brown_mud", "asphalt", "rocky_trail", "grass_medium", "eyebrow", "high-poly")
n = 0
for im in list(bpy.data.images):
    if im.source != "FILE": continue
    if im.name.endswith(".hdr") or "kloofendal" in im.name: continue
    try: w, h = im.size
    except Exception: continue
    if w == 0: continue
    lim = 1024 if any(k in im.name.lower() for k in BIG) else 512
    if max(w, h) > lim:
        s_ = lim / max(w, h); im.scale(max(1, int(w * s_)), max(1, int(h * s_)))
    alpha = any(k in im.name.lower() for k in ("leaves", "leaf", "grass_medium", "lash", "eyebrow", "short0", "bob0")) and im.channels == 4
    fmt, ext = ("PNG", ".png") if alpha else ("JPEG", ".jpg")
    path = os.path.join(TMP, "img%04d%s" % (n, ext))
    try:
        im.save(filepath=path, quality=88) if fmt == "JPEG" else im.save(filepath=path)
    except Exception as e:
        print("SAVEFAIL", im.name, e); continue
    if im.packed_file: im.packed_files[0].filepath if False else None
    for pf in list(im.packed_files): pass
    try: im.unpack(method="REMOVE")
    except Exception: pass
    im.filepath = path; im.source = "FILE"; im.reload(); im.pack(); n += 1
print("RESIZED", n)
sys.argv = [sys.argv[0], "--", OUT]
exec(open(os.path.join(HERE, "..", "..", "pipeline", "package_for_farm.py")).read())
