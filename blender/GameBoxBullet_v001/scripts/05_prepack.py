"""Shrink before packing so the farm .blend stays under 95 MB (plain git, no LFS):
- displacement nodes (scale 0 everywhere) and their maps are removed
- every file texture is re-saved at <= 1K: JPEG q88 for opaque maps, PNG for maps whose alpha is used (leaves, grass)
- the HDRI stays 2K .hdr; orphans are purged; saved compressed
blender -b work/film.blend --python scripts/05_prepack.py -- work/film_small.blend
then pipeline/package_for_farm.py packs everything into the final file."""
import sys, os
import bpy
out = sys.argv[sys.argv.index("--") + 1]
TEX = os.path.join(os.path.dirname(os.path.abspath(out)), "tex"); os.makedirs(TEX, exist_ok=True)
for m in bpy.data.materials:
    if not m.use_nodes: continue
    nt = m.node_tree
    for n in [n for n in nt.nodes if n.type == "DISPLACEMENT"]:
        for l in n.inputs["Height"].links:
            if l.from_node.type == "TEX_IMAGE": nt.nodes.remove(l.from_node)
        nt.nodes.remove(n)
# de-duplicate images loaded twice from the same file
seen = {}
for im in list(bpy.data.images):
    if im.source != "FILE" or im.packed_file: continue
    k = bpy.path.abspath(im.filepath)
    if k in seen: im.user_remap(seen[k])
    else: seen[k] = im
bpy.data.orphans_purge(do_recursive=True)
ALPHA_KEYS = ("leaves", "leaf", "grass", "shrub", "mask", "alpha", "branch", "opacity", "eyelash", "eyebrow", "hair", "ponytail", "short02")
n_done = 0
for im in list(bpy.data.images):
    if im.source != "FILE" or im.packed_file or im.filepath.lower().endswith(".hdr"): continue
    try:
        im.reload(); _ = im.pixels[0]
    except Exception as e:
        print("SKIP", im.name, e); continue
    w, h = im.size
    if max(w, h) > 1024:
        k = 1024 / max(w, h); im.scale(int(w * k), int(h * k))
    nm = (im.name + im.filepath).lower()
    alpha = ("diff" in nm or "col" in nm or "opacity" in nm or "mask" in nm or "mpfb" in nm) and any(k in nm for k in ALPHA_KEYS)
    fmt, ext = ("PNG", ".png") if alpha else ("JPEG", ".jpg")
    p = os.path.join(TEX, bpy.path.clean_name(im.name) + ext)
    sc = bpy.context.scene.render.image_settings
    im.filepath_raw = p; im.file_format = fmt
    if fmt == "JPEG": sc.quality = 88
    im.save(filepath=p, quality=88) if fmt == "JPEG" else im.save(filepath=p)
    im.filepath = p; im.reload(); n_done += 1
print("RESAVED", n_done)
# MPFB body shape keys are static macro targets: bake them into the mesh
for o in bpy.data.objects:
    if o.type == "MESH" and o.data.shape_keys and o.name.endswith(".body"):
        o.shape_key_clear() if False else None
        bpy.context.view_layer.objects.active = o
        o.active_shape_key_index = 0
        bpy.ops.object.shape_key_remove(all=True, apply_mix=True); print("BAKED_SK", o.name)
bpy.ops.wm.save_as_mainfile(filepath=out, compress=True)
print("PREPACK_DONE")
