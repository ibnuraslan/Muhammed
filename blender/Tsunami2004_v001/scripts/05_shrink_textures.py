"""Shrink and re-encode every image before packing (keeps the farm .blend under ~95 MB, no Git LFS).
blender -b film.blend --python 05_shrink_textures.py -- <tmp_dir> <out.blend>
Colour/data maps -> JPEG (q 88); maps whose alpha is used -> PNG.  Max 1024 px; MPFB normal/rough/etc maps 512 px.  HDRIs untouched."""
import sys, os
import bpy
a = sys.argv[sys.argv.index("--") + 1:]
TMP, OUT = a[0], a[1]
os.makedirs(TMP, exist_ok=True)
def has_alpha(img):
    if img.channels < 4: return False
    try:
        import numpy as np
        px = np.empty(img.size[0] * img.size[1] * 4, np.float32); img.pixels.foreach_get(px)
        return float(px[3::4].min()) < 0.98
    except Exception:
        return True
def alpha_used(img):
    for m in bpy.data.materials:
        if not m.use_nodes: continue
        for n in m.node_tree.nodes:
            if n.type == 'TEX_IMAGE' and n.image == img and n.outputs["Alpha"].links:
                return True
    return False
n = 0
for img in list(bpy.data.images):
    if img.source != 'FILE' or img.file_format in ('HDR',) or img.name.lower().endswith(".hdr"): continue
    try:
        w, h = img.size
    except Exception:
        continue
    if w == 0: continue
    nm = img.name.lower()
    small = any(k in nm for k in ("normal", "_nor", "rough", "spec", "bump", "_disp", "ao")) and not nm.startswith(("coast", "damp", "coral"))
    hero = any(k in nm for k in ("skin", "diffuse", "sand", "coast", "damp")) and not nm.startswith("image_")
    cap = 512 if (small or nm.startswith("image_")) else 1024
    s = min(1.0, cap / max(w, h))
    nw, nh = max(4, int(w * s)), max(4, int(h * s))
    if (nw, nh) != (w, h):
        img.scale(nw, nh)
    use_png = alpha_used(img) and has_alpha(img)
    ext = "png" if use_png else "jpg"
    path = os.path.join(TMP, "%04d.%s" % (n, ext)); n += 1
    sc = bpy.context.scene.render.image_settings
    img.filepath_raw = path
    img.file_format = 'PNG' if use_png else 'JPEG'
    st = bpy.context.scene.render.image_settings
    st.file_format = 'PNG' if use_png else 'JPEG'; st.quality = 88; st.color_mode = 'RGBA' if use_png else 'RGB'
    img.save_render(path, scene=bpy.context.scene) if False else img.save(filepath=path, quality=88)
    if img.packed_file: img.unpack(method='REMOVE')
    img.filepath = path; img.reload(); img.pack()
# bodies: bake shape keys into the mesh (they are static after MPFB build)
for ob in bpy.data.objects:
    if ob.type == 'MESH' and ob.data.shape_keys and ob.name.endswith(".body") and ob.data.users == 1:
        ob.shape_key_clear() if False else None
for me in bpy.data.meshes:
    if me.shape_keys and (me.name.startswith("base") or ".body" in me.name):
        kb = me.shape_keys.key_blocks
        if all(k.name != "S1" for k in kb):
            co = [v.co.copy() for v in me.vertices]
            ref = me.shape_keys.reference_key
            # keep the evaluated mix of the current values (all static)
            import numpy as np
            mix = np.zeros(len(me.vertices) * 3); ref.data.foreach_get("co", mix); mix = mix.reshape(-1, 3)
            for k in kb[1:]:
                if k.value and not k.mute:
                    a = np.zeros(len(me.vertices) * 3); k.data.foreach_get("co", a); mix += k.value * (a.reshape(-1, 3) - np.array([d.co[:] for d in ref.data]))
            obs = [o for o in bpy.data.objects if o.data == me]
            for o in obs: o.shape_key_clear()
            me.vertices.foreach_set("co", mix.ravel()); me.update()
# decimate the heaviest building meshes
for nm, ratio in (("LIB_mosque", 0.45), ("LIB_b_rumah", 0.5), ("LIB_b_pariaman", 0.6)):
    me = bpy.data.meshes.get(nm)
    if not me: continue
    import bmesh
    o = bpy.data.objects.new("tmpdec", me); bpy.context.scene.collection.objects.link(o)
    md = o.modifiers.new("dec", 'DECIMATE'); md.ratio = ratio
    dg = bpy.context.evaluated_depsgraph_get(); ev = o.evaluated_get(dg); nmesh = bpy.data.meshes.new_from_object(ev)
    me_old_users = [x for x in bpy.data.objects if x.data == me and x != o]
    for x in me_old_users: x.data = nmesh
    bpy.data.objects.remove(o); nmesh.name = nm + "_dec"
bpy.context.scene.render.image_settings.file_format = 'PNG'; bpy.context.scene.render.image_settings.color_mode = 'RGB'
lib_c = bpy.data.collections.get("LIB")
if lib_c:   # library source objects: their meshes are used by instances; the objects themselves are never rendered
    for o in list(lib_c.objects): bpy.data.objects.remove(o, do_unlink=True)
bpy.data.orphans_purge(do_recursive=True)
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print("SHRUNK", n, "images ->", OUT, os.path.getsize(OUT) // 2**20, "MB")
