"""Fit the package under 95 MB: downscale textures to 512 px, except the hero man, the croc, eyes, logo and portrait.
blender -b in.blend -P 07_shrink.py -- out.blend   (pixels re-packed in their own format, alpha kept)"""
import bpy, sys
OUT = sys.argv[-1]; OB = bpy.data.objects
def images_of(objs):
    s = set()
    for o in objs:
        for m in getattr(o.data, "materials", []) or []:
            if m and m.use_nodes:
                for n in m.node_tree.nodes:
                    if n.type == 'TEX_IMAGE' and n.image: s.add(n.image.name)
    return s
keep = images_of([OB["Croc_body"]] + [c for c in OB["Keeper"].children])
keep |= {i.name for i in bpy.data.images if any(k in i.name.lower() for k in ("dakras", "portrait", "eye", "brown", "iris"))}
n = 0
for img in bpy.data.images:
    if img.name in keep or img.source != 'FILE' or img.size[0] <= 512: continue
    w, h = img.size; f = 512 / max(w, h)
    img.scale(max(1, int(w * f)), max(1, int(h * f)))
    img.pack(); n += 1
# drop unused data
for o in [o for o in OB if o.name in ("Palm1", "Palm2", "Palm3", "Plant1", "Plant2", "Flowers", "Vase", "Bench") or o.name.startswith("Bench.")]:
    bpy.data.objects.remove(o)
bpy.data.orphans_purge(do_recursive=True)
print("SHRUNK", n, "kept", len(keep))
bpy.ops.wm.save_as_mainfile(filepath=OUT)
