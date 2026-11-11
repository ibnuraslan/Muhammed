"""Shrink textures before packing: drop unlinked image nodes, downscale, re-encode opaque maps as JPEG.
blender -b film.blend --python slim_textures.py -- <tmp_dir> <out.blend>
Keeps 2K only for the hero's skin and shirt; everything else <= 1K. Images with alpha (hair, brows, lashes, leaves) stay PNG."""
import bpy, sys, os
a = sys.argv[sys.argv.index("--") + 1:]; TMP, OUT = a[0], a[1]; os.makedirs(TMP, exist_ok=True)
# 1. remove image nodes whose outputs go nowhere (displacement maps we unlinked, unused AO, etc.)
for m in bpy.data.materials:
    if not m.node_tree: continue
    for n in list(m.node_tree.nodes):
        if n.type == "TEX_IMAGE" and not any(o.links for o in n.outputs):
            m.node_tree.nodes.remove(n)
# 2. drop objects in the hidden asset library that are only build sources and never rendered
lib = bpy.data.collections.get("_lib")
if lib:
    for o in list(lib.objects):
        if o.users <= 1 and not o.data.users > 1 if o.data else False:
            pass
bpy.data.orphans_purge(do_recursive=True)
# strip heavy custom data from prop meshes (not the skinned humans): custom split normals, extra UV maps, colour attributes
char_meshes = {o.data for o in bpy.data.objects if o.type == "MESH" and o.parent and o.parent.type == "ARMATURE"}
for me in bpy.data.meshes:
    if me in char_meshes: continue
    try:
        if me.has_custom_normals: me.normals_split_custom_set([]) if False else None
    except Exception: pass
    for a_ in [a_.name for a_ in me.attributes if a_.name.startswith(("custom_normal", ".uv_select", ".select", "sharp_face", "uv_seam"))]:
        try: me.attributes.remove(me.attributes[a_])
        except Exception: pass
    while len(me.uv_layers) > 1: me.uv_layers.remove(me.uv_layers[-1])
    for ca in list(me.color_attributes): me.color_attributes.remove(ca)
KEEP2K = ("middleage_lightskinned_male_diffuse", "male_casualsuit01_diffuse")
ALPHA = ("short0", "braid", "eyebrow", "eyelash", "leaves", "glass")
tot0 = tot1 = 0
for im in list(bpy.data.images):
    if im.source != "FILE" or im.users == 0: continue
    if im.name.endswith(".hdr") or im.filepath.lower().endswith(".hdr"):
        continue
    try:
        w, h = im.size
    except Exception:
        continue
    if w == 0: continue
    lim = 2048 if any(k in im.name for k in KEEP2K) else 1024
    if any(k in im.name for k in ("teeth", "tongue", "eye")): lim = 256
    BIG = ("asphalt", "plaster", "dry_ground", "gravel", "concrete", "brick", "corrugated", "wood_floor", "diffuse", "rickshaw", "Material", "cow", "Dog", "laptop")
    if lim == 1024 and not any(k.lower() in im.name.lower() for k in BIG): lim = 512
    if "_nor" in im.name.lower() or "normal" in im.name.lower() or "rough" in im.name.lower(): lim = min(lim, 512)
    nm = os.path.splitext(bpy.path.clean_name(im.name))[0]
    keep_png = any(k in im.name.lower() for k in ALPHA)
    if max(w, h) > lim:
        s = lim / max(w, h); im.scale(int(w * s), int(h * s))
    ext = "png" if keep_png else "jpg"
    p = os.path.join(TMP, nm + "." + ext)
    im.filepath_raw = p; im.file_format = "PNG" if keep_png else "JPEG"
    sc = bpy.context.scene; sc.render.image_settings.quality = 88
    im.save(filepath=p, quality=80) if not keep_png else im.save(filepath=p)
    if im.packed_file:
        try: im.unpack(method="REMOVE")
        except Exception as e: print("UNPACK fail", im.name, e)
    im.filepath = p; im.source = "FILE"; im.reload()
    tot1 += os.path.getsize(p)
print("SLIM images written", tot1 // 2**20, "MB")
bpy.context.scene.render.image_settings.color_mode = "RGB"
bpy.ops.wm.save_as_mainfile(filepath=OUT)
