"""After anim_look: restore the water/river looks (anim_look lifts roughness to 0.35, which made the flood read as sand).
blender -b work/look.blend -P 04_post_look.py -- out.blend"""
import bpy, sys
def P(n): return next(x for x in bpy.data.materials[n].node_tree.nodes if x.type == 'BSDF_PRINCIPLED')
w = P("MudWater"); w.inputs["Base Color"].default_value = (0.13, 0.10, 0.055, 1); w.inputs["Roughness"].default_value = 0.06; w.inputs["Specular IOR Level"].default_value = 0.05
r = P("River"); r.inputs["Base Color"].default_value = (0.02, 0.07, 0.12, 1); r.inputs["Roughness"].default_value = 0.08
c = P("Concrete"); c.inputs["Base Color"].default_value = (0.32, 0.32, 0.33, 1)
sw = P("SwampWater"); sw.inputs["Base Color"].default_value = (0.06, 0.14, 0.16, 1); sw.inputs["Roughness"].default_value = 0.08
for m in bpy.data.materials:
    if m.name.startswith("Rug"): P(m.name).inputs["Base Color"].default_value = (0.42, 0.10, 0.08, 1)
bpy.ops.wm.save_as_mainfile(filepath=sys.argv[sys.argv.index("--") + 1], compress=True)
print("POST_OK")
