"""Shrink and pack for the farm: drop the hidden library originals, purge orphans, normal/roughness maps (and background tree
textures) to 512 px as 8-bit PNG, everything packed, compressed save.
blender -b film.blend --python 03_package.py -- <out.blend>"""
import bpy, sys, os
out = sys.argv[sys.argv.index("--") + 1]
for cn in ("PLANTS", "PROPS"):
    c = bpy.data.collections.get(cn)
    if c:
        for o in list(c.objects): bpy.data.objects.remove(o, do_unlink=True)
for _ in range(3): bpy.data.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)
n = 0
for im in list(bpy.data.images):
    if im.source != 'FILE' or im.size[0] <= 512: continue
    nm = im.name.lower()
    if "leaves" in nm or "alpha" in nm or "linen" in nm: continue      # leaf cutouts keep their full maps (alpha)
    if any(k in nm for k in ("nor", "rough", "disp", "spec", "sss", "_ao")) or ("branches_diff" in nm):
        w, h = 512, max(1, int(512 * im.size[1] / im.size[0]))
        im.scale(w, h)
        new = bpy.data.images.new(im.name + "_s", w, h, alpha=True, float_buffer=False)
        new.pixels.foreach_set(im.pixels[:])
        new.colorspace_settings.name = im.colorspace_settings.name
        new.alpha_mode = im.alpha_mode
        new.file_format = 'PNG'; new.pack()
        im.user_remap(new); bpy.data.images.remove(im); n += 1
print("PKG scaled", n)
exec(open("/home/user/Muhammed/blender/pipeline/package_for_farm.py").read())
