"""Shrink and re-encode every image before packing (keeps the farm .blend under ~95 MB, no Git LFS).
blender -b film.blend --python 05_shrink_textures.py -- <tmp_dir> <out.blend>
Colour/data maps -> JPEG (q 88); maps whose alpha is used -> PNG.  Max 1024 px; MPFB normal/rough/etc maps 512 px.  HDRIs untouched."""
import sys, os
import bpy
a = sys.argv[sys.argv.index("--") + 1:]
TMP, OUT = a[0], a[1]
os.makedirs(TMP, exist_ok=True)
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
    cap = 512 if small else 1024
    s = min(1.0, cap / max(w, h))
    nw, nh = max(4, int(w * s)), max(4, int(h * s))
    if (nw, nh) != (w, h):
        img.scale(nw, nh)
    use_png = alpha_used(img)
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
bpy.ops.outliner.orphans_purge(do_recursive=True) if False else bpy.data.orphans_purge(do_recursive=True)
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print("SHRUNK", n, "images ->", OUT, os.path.getsize(OUT) // 2**20, "MB")
