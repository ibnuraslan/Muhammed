"""Package size: remap duplicate images (.001/.002 copies from repeated library loads) to one, and scale the
environment textures (trees, bark, bench, ground, glb props) to 512 px; character (MPFB) textures stay as they are.
Image.pack() after scale() keeps alpha (no save_render). blender -b film_vo.blend --python 07_shrink.py -- out.blend"""
import bpy, sys, re
out = sys.argv[sys.argv.index("--") + 1]
imgs = list(bpy.data.images)
by = {i.name: i for i in imgs}
n_remap = 0
for i in imgs:
    m = re.match(r"^(.*)\.\d{3}$", i.name)
    if m and m.group(1) in by and by[m.group(1)] is not i and tuple(by[m.group(1)].size) == tuple(i.size):
        i.user_remap(by[m.group(1)]); n_remap += 1
for i in list(bpy.data.images):
    if i.users == 0: bpy.data.images.remove(i)
CHAR = ("young_", "middleage_", "old_", "brown", "ponytail", "eyebrow", "eyelash", "casualsuit", "worksuit", "shoes", "short0", "teeth", "tongue",
        "female_", "male_", "afro", "bob0", "long0", "braid", "texture", "diffuse", "normal", "skin", "eye", "_sss", "litsphere")
n_scaled = 0
for i in bpy.data.images:
    if i.source not in ('FILE',) or i.size[0] <= 512: continue
    nm = i.name.lower()
    is_char = any(k in nm for k in CHAR) and not any(k in nm for k in ("fir_", "bark", "twig", "trunk", "shrub", "fern", "bench", "cement", "dead_tree", "asphalt", "gravel", "forest", "laminate", "rocky", "mud", "image_"))
    if is_char: continue
    w, h = i.size; i.scale(max(256, w // 2), max(256, h // 2)); i.pack(); n_scaled += 1
print("SHRINK remapped", n_remap, "scaled", n_scaled, "images left", len(bpy.data.images))
bpy.ops.wm.save_as_mainfile(filepath=out, compress=True)
