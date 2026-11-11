"""Resize every file texture to 1K (2K for the hero diver skin and the HDRI), save as PNG/JPG next to the work file,
remap the images, purge orphans, save.  blender -b film.blend --python shrink_textures.py -- <out.blend>"""
import bpy, sys, os
OUT = sys.argv[sys.argv.index("--") + 1]
D = os.path.join(os.path.dirname(OUT), "tex_small"); os.makedirs(D, exist_ok=True)
hero = set()
for ob in bpy.data.objects:
    if ob.name == "Diver.body" and ob.type == 'MESH':
        for m in ob.data.materials:
            if m and m.node_tree:
                for n in m.node_tree.nodes:
                    if n.type == 'TEX_IMAGE' and n.image: hero.add(n.image.name)
bpy.data.orphans_purge(do_recursive=True)
done = 0
for im in list(bpy.data.images):
    if im.source != 'FILE' or not im.has_data and not os.path.exists(bpy.path.abspath(im.filepath)): continue
    w, h = im.size
    if w == 0: continue
    is_hdr = im.filepath.lower().endswith(".hdr")
    lim = 2048 if (is_hdr or im.name in hero) else 1024
    if max(w, h) <= lim and not im.filepath.lower().endswith(".exr"): continue
    s = lim / max(w, h) if max(w, h) > lim else 1.0
    im.scale(max(1, int(w * s)), max(1, int(h * s)))
    base = bpy.path.clean_name(os.path.splitext(os.path.basename(im.filepath))[0])
    if is_hdr:
        p = os.path.join(D, base + ".hdr"); im.file_format = 'HDR'
    elif im.colorspace_settings.name == 'Non-Color' or im.is_float:
        p = os.path.join(D, base + ".png"); im.file_format = 'PNG'
    else:
        p = os.path.join(D, base + ".jpg"); im.file_format = 'JPEG'
    im.filepath_raw = p; im.save()
    im.filepath = p; im.reload(); done += 1
print("SHRUNK", done, "images")
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
