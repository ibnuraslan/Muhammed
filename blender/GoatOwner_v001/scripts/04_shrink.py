"""Shrink textures for the <95 MB no-LFS package: every image to <=1024 px (512 for small props), JPEG unless it needs alpha.
blender -b anim.blend --python 04_shrink.py -- <tex_dir> <out.blend>"""
import sys, os
import bpy
a = sys.argv[sys.argv.index("--") + 1:]
TEX, OUT = a[0], a[1]
os.makedirs(TEX, exist_ok=True)
# the meadow HDRI is no longer used (horizon band disabled): drop it from the world
wt = bpy.context.scene.world.node_tree
for n in list(wt.nodes):
    if n.type == 'TEX_ENVIRONMENT' and n.image and "hausdorf" in n.image.name:
        wt.nodes.remove(n)
bpy.data.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)
ALPHA = ("eyebrow", "eyelash", "tree_small_02_leaves", "grass_medium", "short0", "ponytail", "bob0")
SMALL = ("teeth", "tongue", "crate", "eyelash", "eyebrow")
n = 0
for im in list(bpy.data.images):
    if im.source != 'FILE' or im.type != 'IMAGE' or im.name.lower().endswith((".hdr", ".exr")) and "nor" not in im.name.lower() and "rough" not in im.name.lower():
        continue
    if im.users == 0:
        continue
    try:
        w, h = im.size
        if w == 0: im.reload(); w, h = im.size
    except Exception:
        continue
    if w == 0:
        print("SKIP", im.name); continue
    lname = (im.name + im.filepath).lower()
    lim = 512 if any(k in lname for k in SMALL) else 1024
    alpha = any(k in lname for k in ALPHA) and im.channels == 4 and not any(k in lname for k in ("nor", "rough", "disp", "_ao", "normal", "spec"))
    if not alpha and im.channels == 4 and im.packed_file and not im.filepath:
        # GLB textures: keep PNG only if they really carry alpha
        px = im.pixels[:]; alpha = any(px[i] < 0.99 for i in range(3, len(px), 4 * 97))
    if max(w, h) > lim:
        s = lim / max(w, h); im.scale(max(1, int(w * s)), max(1, int(h * s)))
    base = "".join(c if c.isalnum() else "_" for c in os.path.splitext(im.name)[0])[:60] + "_%d" % n
    path = os.path.join(TEX, base + (".png" if alpha else ".jpg"))
    im.filepath_raw = path; im.file_format = 'PNG' if alpha else 'JPEG'
    try:
        im.save(quality=85) if not alpha else im.save()
    except TypeError:
        im.save()
    except Exception as e:
        rs = bpy.context.scene.render.image_settings
        rs.file_format = 'PNG' if alpha else 'JPEG'; rs.quality = 85; rs.color_mode = 'RGBA' if alpha else 'RGB'
        im.save_render(path)
    new = bpy.data.images.load(path); new.colorspace_settings.name = im.colorspace_settings.name
    new.alpha_mode = im.alpha_mode
    im.user_remap(new); bpy.data.images.remove(im)
    n += 1
bpy.data.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)
print("SHRINK", n, "images")
bpy.ops.wm.save_as_mainfile(filepath=OUT)
