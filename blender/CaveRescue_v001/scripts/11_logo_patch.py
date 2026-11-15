"""Flat-tint MPFB female_casualsuit01 (its texture carries a printed emblem). blender -b pkg.blend --python 11_logo_patch.py"""
import bpy
n = 0
for o in bpy.data.objects:
    if o.type == 'MESH' and o.name.endswith("female_casualsuit01"):
        for m in o.data.materials:
            p = next((x for x in m.node_tree.nodes if x.type == 'BSDF_PRINCIPLED'), None)
            if p is None: continue
            for lk in list(p.inputs['Base Color'].links): m.node_tree.links.remove(lk)
            p.inputs["Base Color"].default_value = (0.05, 0.12, 0.3, 1) if o.name.startswith("Crowd1") else (0.4, 0.07, 0.06, 1)   # v009: navy / dark red (the pink and pale green read as bare skin)
            n += 1
print("LOGO_PATCHED", n)
bpy.ops.wm.save_mainfile(compress=True)
