"""Decimate background scan meshes before packaging.  blender -b in.blend --python 05_decimate_bg.py -- out.blend"""
import sys, bpy
out = sys.argv[sys.argv.index("--") + 1]
n0 = n1 = 0
for o in bpy.data.objects:
    if o.type != "MESH" or not o.parent: continue
    p = o
    while p.parent: p = p.parent
    if not p.name.startswith(("HotelFacade", "SideFacade")): continue
    n0 += len(o.data.polygons)
    bpy.context.view_layer.objects.active = o
    m = o.modifiers.new("Dec", "DECIMATE"); m.ratio = 0.3
    with bpy.context.temp_override(object=o, active_object=o): bpy.ops.object.modifier_apply(modifier="Dec")
    n1 += len(o.data.polygons)
print("DECIMATED", n0, "->", n1)
bpy.data.orphans_purge(do_recursive=True)
bpy.ops.wm.save_as_mainfile(filepath=out)
