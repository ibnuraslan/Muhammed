"""Trim textures for the farm package (target < 150 MB): drop unused maps (displacement, anisotropy, spec IOR),
downscale everything to 1K except hero maps (woman skin/clothes, bin steel, asphalt diffuse) at 2K, keep the 2K HDRI.
blender -b anim.blend --python 04_package_prep.py -- <tex_dir> <out.blend>"""
import sys, os
import bpy
a = sys.argv[sys.argv.index("--") + 1:]
TEX, OUT = a[0], a[1]
os.makedirs(TEX, exist_ok=True)
DROP = ("_disp_", "anisotropy", "spec_ior", "_metal_2k", "displacement")
removed = 0
for m in bpy.data.materials:
    if not m.use_nodes: continue
    nt = m.node_tree
    for nd in list(nt.nodes):
        if nd.type == 'TEX_IMAGE' and nd.image and any(k in nd.image.name.lower() or k in os.path.basename(nd.image.filepath).lower() for k in DROP):
            nt.nodes.remove(nd); removed += 1
        elif nd.type == 'DISPLACEMENT':
            nt.nodes.remove(nd)
for i in list(bpy.data.images):
    if i.users == 0: bpy.data.images.remove(i)
HERO = ("middleage_",)
n = 0
for i in bpy.data.images:
    if i.source != 'FILE' or i.type != 'IMAGE': continue
    p = bpy.path.abspath(i.filepath); ext = os.path.splitext(p)[1].lower()
    if ext == ".hdr": continue
    w, h = i.size
    lim = 2048 if any(k in os.path.basename(p) for k in HERO) else 1024
    if max(w, h) <= lim and ext in (".jpg", ".jpeg"): continue
    s = min(1.0, lim / max(w, h))
    if s < 1.0: i.scale(max(1, int(w * s)), max(1, int(h * s)))
    base = os.path.splitext(os.path.basename(p))[0]
    alpha = False
    if i.channels == 4:
        import numpy as np
        px = np.empty(len(i.pixels), dtype=np.float32); i.pixels.foreach_get(px)
        alpha = bool((px[3::4] < 0.98).any())
    if alpha:                               # hair, lashes, brows: keep the alpha channel
        q = os.path.join(TEX, base + ".png"); i.file_format = 'PNG'
    else:                                   # everything else (incl. normal / roughness data) as 8-bit JPEG
        q = os.path.join(TEX, base + ".jpg"); i.file_format = 'JPEG'
    i.filepath_raw = q; i.save(); i.filepath = q; i.reload(); n += 1
print("PREP removed_nodes", removed, "resaved", n)
bpy.ops.wm.save_as_mainfile(filepath=OUT)
