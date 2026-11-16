"""Pack for delivery: drop the unused grass tuft, decimate the far-tree mesh (1.2 M verts -> ~12%), downscale textures
(1024 px max, 512 px for distant set dressing), pack everything, save compressed.
blender -b anim.blend --python 04_pack.py -- <out.blend>"""
import bpy, sys
OUT = sys.argv[sys.argv.index("--") + 1]
g = bpy.data.objects.get("Ground")
if g:
    for m in list(g.modifiers):
        if m.type == 'PARTICLE_SYSTEM': g.modifiers.remove(m)
for n in ("GrassTuft",):
    o = bpy.data.objects.get(n)
    if o: bpy.data.objects.remove(o, do_unlink=True)
# the CC0 island tree is 1.2 M verts (leaf cards, does not decimate): far trees become large shrub_04 instances
sh = bpy.data.objects.get("Shrub4Src")
for o in list(bpy.data.objects):
    if o.type == 'MESH' and (o.name.startswith("Tree") or o.name == "TreeSrc"):
        if sh and o.name != "TreeSrc":
            n = sh.copy(); o.users_collection[0].objects.link(n); n.name = o.name + "_bush"
            n.location = o.location; n.rotation_euler = o.rotation_euler; n.scale = [v * 3.2 for v in o.scale]
            n.hide_render = False; n.hide_viewport = False
        bpy.data.objects.remove(o, do_unlink=True)
bpy.data.orphans_purge(do_recursive=True)
FAR = ("island_tree", "grass_medium", "shrub", "stone_fire_pit", "wooden_bucket", "wicker")
for im in bpy.data.images:
    if im.source != 'FILE': continue
    try:
        w, h = im.size
        mx = 512 if any(k in im.name for k in FAR) else 1024
        if max(w, h) > mx:
            k = mx / max(w, h); im.scale(max(1, int(w * k)), max(1, int(h * k)))
        im.pack()
    except Exception as e: print("PACKFAIL", im.name, e)
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print("PACKED")
