"""Shrink a packed package under 95 MB: drop displacement images (displacement is off), maps other than colour/alpha to
512 px JPEG, large colour maps to 1024 px; images with alpha stay PNG (Image.save keeps alpha, unlike save_render).
blender -b pkg.blend --python 05_shrink.py -- out.blend"""
import bpy, sys, os, tempfile
out = sys.argv[sys.argv.index("--") + 1]
tmp = tempfile.mkdtemp(dir="/home/user/Muhammed/blender/FakeDrainRescue_v001/work")
for m in bpy.data.materials:
    if not m.use_nodes: continue
    for n in list(m.node_tree.nodes):
        if n.type == 'TEX_IMAGE' and n.image and "disp" in n.image.name.lower(): m.node_tree.nodes.remove(n)
for ng in bpy.data.node_groups:
    for n in list(ng.nodes):
        if n.type == 'TEX_IMAGE' and n.image and "disp" in n.image.name.lower(): ng.nodes.remove(n)
for im in list(bpy.data.images):
    if im.users == 0: bpy.data.images.remove(im)
saved = 0
for i, im in enumerate(list(bpy.data.images)):
    if im.source != 'FILE' or not im.packed_file or im.name.lower().endswith((".hdr", ".exr")): continue
    nm = im.name.lower(); w, h = im.size
    if w == 0: continue
    colour = any(k in nm for k in ("diff", "diffuse", "col", "logo", "form", "phone", "screen", "basecolor", "albedo"))
    alpha = colour and im.channels == 4 and any(k in nm for k in ("leaves", "hair", "bob", "brow", "lash", "logo", "fence", "wire", "short", "eyebrow"))
    target = 1024 if colour else 512
    if max(w, h) <= target and im.packed_file.size < 600000: continue
    if max(w, h) > target: im.scale(int(w * target / max(w, h)), int(h * target / max(w, h)))
    ext = ".png" if alpha else ".jpg"
    p = os.path.join(tmp, "img%03d%s" % (i, ext))
    im.save(filepath=p, quality=88) if hasattr(im, "save") else None
    if not os.path.exists(p) or os.path.getsize(p) == 0: print("SKIP", im.name); continue
    new = bpy.data.images.load(p); new.colorspace_settings.name = im.colorspace_settings.name; new.alpha_mode = im.alpha_mode
    new.pack(); im.user_remap(new); nm0 = im.name; bpy.data.images.remove(im); new.name = nm0; saved += 1
print("SHRUNK", saved)
bpy.ops.wm.save_as_mainfile(filepath=out, compress=True)
print("SIZE MB", round(os.path.getsize(out) / 1e6, 1))
