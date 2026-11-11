"""Cap textures before packing (target: packed .blend < 95 MB as a normal git file).
2K only for hero close-ups (bomber + attendant skin/eyes, the sneakers); 1K for everything else; purge orphans.
blender -b film.blend --python 05_shrink_textures.py -- <out.blend>"""
import sys, bpy
OUT = sys.argv[sys.argv.index("--") + 1]
HERO_RIGS = ("Bomber", "Attendant")
owners = {}
for ob in bpy.data.objects:
    if ob.type != 'MESH': continue
    for sl in ob.material_slots:
        m = sl.material
        if not m or not m.node_tree: continue
        for n in m.node_tree.nodes:
            if n.type == 'TEX_IMAGE' and n.image: owners.setdefault(n.image.name, set()).add(ob.name)
def hero(names):
    for nm in names:
        if nm.startswith("Shoe_"): return True
        rig, _, part = nm.partition(".")
        if rig in HERO_RIGS and part in ("body", "high-poly"): return True
    return False
for im in bpy.data.images:
    if im.source != 'FILE' or im.size[0] == 0: continue
    cap = 2048 if hero(owners.get(im.name, ())) else 1024
    w, h = im.size
    if max(w, h) > cap:
        s = cap / max(w, h); im.scale(max(1, int(w * s)), max(1, int(h * s))); im.pack()
        print("SCALED", im.name, (w, h), "->", tuple(im.size))
import os
TMP = "/tmp/sb_pack"; os.makedirs(TMP, exist_ok=True)
ALPHA = ("hair", "short0", "long0", "bob0", "ponytail", "afro", "braid", "eyebrow", "eyelash", "lash", "brow")
for im in list(bpy.data.images):
    if im.source != 'FILE' or im.size[0] == 0: continue
    n = im.name.lower()
    if n.endswith(".hdr"):
        p = os.path.join(TMP, "env_1k.hdr"); im.filepath_raw = p; im.file_format = 'HDR'; im.save()
        im.unpack(method='REMOVE') if im.packed_file else None; im.filepath = p; im.reload(); im.pack(); print("HDR", im.name); continue
    if "diffuse" in n and not any(k in n for k in ALPHA):
        p = os.path.join(TMP, os.path.splitext(im.name)[0] + ".jpg")
        im.filepath_raw = p; im.file_format = 'JPEG'; bpy.context.scene.render.image_settings.quality = 90; im.save()
        if im.packed_file: im.unpack(method='REMOVE')
        im.filepath = p; im.source = 'FILE'; im.reload(); im.pack(); print("JPG", im.name)
bpy.data.orphans_purge(do_recursive=True)
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
