"""Shrink textures before packing: merge duplicate images, convert float EXR maps (normal/roughness) to 8-bit PNG at 1K,
cap everything else at 2K. blender -b anim.blend --python 04_slim_textures.py -- <tex_out_dir> <out.blend>"""
import sys, os, bpy
a = sys.argv[sys.argv.index("--") + 1:]; TD, OUT = a[0], a[1]; os.makedirs(TD, exist_ok=True)
HERO_MAX = int(a[2]) if len(a) > 2 else 2048; PROP_MAX = int(a[3]) if len(a) > 3 else 2048
HERO = ("skin", "lightskinned", "suit", "long01", "short02", "wood_floor_diff", "painted_plaster_wall_diff", "eyebrow", "high-poly", "brown")
# 1) duplicates (same file loaded twice by appends)
by_path = {}
for im in list(bpy.data.images):
    if im.source != "FILE": continue
    k = (os.path.basename(bpy.path.abspath(im.filepath)), im.colorspace_settings.name)
    if k in by_path:
        im.user_remap(by_path[k]); bpy.data.images.remove(im)
    else: by_path[k] = im
# 2) resize / convert
n = 0
for im in list(bpy.data.images):
    if im.source != "FILE" or not im.has_data and not im.size[0]:
        try: im.reload()
        except Exception: pass
    w, h = im.size[:]
    if w == 0: continue
    is_exr = im.filepath.lower().endswith(".exr")
    hero = any(k in im.name.lower() for k in HERO)
    lim = 1024 if is_exr else (HERO_MAX if hero else PROP_MAX)
    jpg = not hero and "alpha" not in im.name.lower() and im.alpha_mode != "NONE" or (not hero and "alpha" not in im.name.lower())
    if not is_exr and max(w, h) <= lim and not jpg: continue
    s = lim / max(w, h)
    if s < 1: im.scale(max(1, int(w * s)), max(1, int(h * s)))
    cs = im.colorspace_settings.name
    p = os.path.join(TD, "%03d_%s.%s" % (n, bpy.path.clean_name(im.name), "jpg" if jpg else "png")); n += 1
    im.filepath_raw = p; im.file_format = "JPEG" if jpg else "PNG"
    bpy.context.scene.render.image_settings.quality = 90
    sc = bpy.context.scene; sc.render.image_settings.color_depth = "8"
    im.save(filepath=p)
    im.filepath = p; im.source = "FILE"; im.reload(); im.colorspace_settings.name = cs
    print("SLIM", im.name, (w, h), "->", im.size[:])
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("SLIM_DONE", n)
