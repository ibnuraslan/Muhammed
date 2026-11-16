"""Recolour / dress the characters, caps for the police, eye fix on every EnhancedEye group.
blender -b work/chars.blend --python 02_dress.py -- work/dressed.blend"""
import bpy, sys, math
from mathutils import Vector
HERE = "/home/user/Muhammed/blender/NatashaRyan_v001/scripts/"
exec(open(HERE + "nat_lib.py").read()); exec(open(HERE + "dress_lib.py").read())
out = sys.argv[sys.argv.index("--") + 1]
for o in bpy.data.objects:
    if o.type == 'ARMATURE': o.location = (0, 0, 0)
bpy.context.view_layer.update()
O = bpy.data.objects
def flat(ob, material):
    ob.data.materials.clear(); ob.data.materials.append(material)
    for p in ob.data.polygons: p.material_index = 0
def hip_z(rig): return O[rig].data.bones["upperleg01.L"].head_local.z + 0.07
TOPB = lambda b, co: b.startswith(TOP) or b.startswith(("neck", "clavicle"))
# Natasha at 14: white school blouse, navy pinafore skirt, black shoes, dark-brown hair
navy = mat("Nat_Navy", (0.04, 0.05, 0.13), 0.6, sheen=0.2)
white = mat("Nat_WhiteBlouse", (0.88, 0.88, 0.86), 0.55, sheen=0.2)
suit = O["Nat.female_elegantsuit01"]; flat(suit, navy)
recolor_by_bone(suit, TOPB, white, zabs=hip_z("Nat"))
flat(O["Nat.shoes02"], mat("Shoe_Black", (0.02, 0.02, 0.02), 0.4))
tint_group(O["Nat.long01"], (0.35, 0.25, 0.2))
# closed neckline: a white undershirt from her own skin (chest + neck base), just under the blouse
garment("Nat", "undershirt", lambda b, co: b.startswith(("spine0", "breast", "pectoral", "clavicle", "neck01")), white, offset=0.004, thick=0.002, mask_body=False)
# Mom: soft teal top (tinted), jeans, honey-blonde bob (tinted grey hair)
tint_group(O["Mom.female_casualsuit01"], (0.35, 0.9, 0.85))
tint_group(O["Mom.bob02"], (1.0, 0.82, 0.5))
# searchers: orange overalls (SearchB's beige tinted orange)
tint_group(O["SearchB.male_worksuit01"], (1.0, 0.55, 0.15))
# the arrested local man: brown overalls (tinted), older grey hair
tint_group(O["Killer.male_worksuit01"], (0.45, 0.3, 0.2))
# police: navy shirts + navy caps
for r in ("CopA", "CopB", "CopF"):
    cs = next(c for c in O[r].children if "casualsuit" in c.name)
    tint_group(cs, (0.35, 0.4, 0.7))
    cap(r, (0.03, 0.04, 0.1))
# judge: black suit stays; extras keep their own clothes
# eye fix (idempotent) on every EnhancedEye group
for ng in list(bpy.data.node_groups):
    if ng.name.startswith("EnhancedEye") and "CorneaTransparentMix" not in ng.nodes:
        src = open(HERE + "eye_fix.py").read().replace('bpy.data.node_groups["EnhancedEye"]', 'bpy.data.node_groups["%s"]' % ng.name)
        exec(src, {"bpy": bpy, "sys": sys, "_NO_SAVE": True})
bpy.ops.wm.save_as_mainfile(filepath=out, compress=True)
print("DRESS_DONE")
