"""Pre-package size pass: drop unlinked image nodes, dedupe images, downscale big textures (hero skin stays 2K).
blender -b film.blend --python scripts/05_optimize.py --python ../pipeline/package_for_farm.py -- <out.blend>"""
import bpy, os
removed = 0
for m in bpy.data.materials:
    if not m.node_tree: continue
    while True:
        dead = [n for n in m.node_tree.nodes if n.type in ('TEX_IMAGE', 'DISPLACEMENT', 'MAPPING') and not any(o.is_linked for o in n.outputs)]
        if not dead: break
        for n in dead: m.node_tree.nodes.remove(n); removed += 1
by = {}
for im in bpy.data.images:
    if im.source == 'FILE':
        k = bpy.path.abspath(im.filepath)
        if k in by and im != by[k]: im.user_remap(by[k])
        else: by.setdefault(k, im)
for im in list(bpy.data.images):
    if im.users == 0: bpy.data.images.remove(im)
KEEP2K = ("young_lightskinned_male_diffuse",)
scaled = 0
for im in bpy.data.images:
    if im.source != 'FILE' or im.size[0] == 0: continue
    if im.filepath.lower().endswith(".hdr"):
        if im.size[0] > 1024: im.scale(1024, 512); im.pack(); scaled += 1
        continue
    big = max(im.size)
    tgt = 2048 if any(k in im.name for k in KEEP2K) else 1024
    if big > tgt:
        im.scale(tgt, max(1, round(im.size[1] * tgt / im.size[0])))
        im.pack(); scaled += 1
print("OPT removed nodes", removed, "scaled", scaled, "images", len(bpy.data.images))

# re-encode every non-HDR packed image as JPEG (normal maps were stored as EXR)
jpg = 0
for im in bpy.data.images:
    if im.source != 'FILE' or im.size[0] == 0 or im.filepath.lower().endswith(".hdr"): continue
    try:
        import tempfile, os
        tmp = os.path.join(tempfile.gettempdir(), "pk_" + bpy.path.clean_name(im.name) + ".jpg")
        im.filepath_raw = tmp; im.file_format = 'JPEG'; im.save(filepath=tmp, quality=90)
        n = bpy.data.images.load(tmp); n.pack(); n.colorspace_settings.name = im.colorspace_settings.name
        im.user_remap(n); nm = im.name; bpy.data.images.remove(im); n.name = nm; n.filepath = "//textures/" + bpy.path.clean_name(nm) + ".jpg"
        os.remove(tmp); jpg += 1
    except Exception as e:
        print("OPT jpg fail", im.name, e)
# bake MPFB body shape keys into the final mix
sk = 0
for o in bpy.data.objects:
    if o.type == 'MESH' and o.data.shape_keys and o.data.users == 1 and not o.name.startswith(("WaxPool", "WaxMold")):
        bpy.context.view_layer.objects.active = o
        for x in bpy.context.selected_objects: x.select_set(False)
        o.select_set(True)
        try:
            bpy.ops.object.shape_key_remove(all=True, apply_mix=True); sk += 1
        except Exception as e: print("OPT sk fail", o.name, e)
bpy.data.orphans_purge(do_recursive=True)
print("OPT jpeg", jpg, "shapekeys baked", sk)
