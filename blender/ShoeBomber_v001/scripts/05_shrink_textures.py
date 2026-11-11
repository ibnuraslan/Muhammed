"""Cap textures before packing: everything <= 2048, textures used only by background extras <= 1024.
blender -b film.blend --python 05_shrink_textures.py -- <out.blend>"""
import sys, bpy
OUT = sys.argv[sys.argv.index("--") + 1]
EXTRAS = ("PaxA", "PaxB", "PaxC", "PaxD", "Officer")
users = {}
for ob in bpy.data.objects:
    if ob.type != 'MESH': continue
    owner = ob.parent.name if ob.parent and ob.parent.type == 'ARMATURE' else "_set"
    for sl in ob.material_slots:
        m = sl.material
        if not m or not m.node_tree: continue
        for n in m.node_tree.nodes:
            if n.type == 'TEX_IMAGE' and n.image: users.setdefault(n.image.name, set()).add(owner)
for im in bpy.data.images:
    if im.source != 'FILE' or im.size[0] == 0: continue
    own = users.get(im.name, set())
    cap = 1024 if own and own <= set(EXTRAS) else 2048
    w, h = im.size
    if max(w, h) > cap:
        s = cap / max(w, h); im.scale(int(w * s), int(h * s)); im.pack(); print("SCALED", im.name, (w, h), "->", tuple(im.size), sorted(own))
bpy.ops.wm.save_as_mainfile(filepath=OUT)
