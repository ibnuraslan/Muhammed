"""v012 (found by watching the preview): Mom's knees poked through the front of the skirt as she walked in (~821-831).
The skirt region (garment vertices dominated by pelvis/upper-leg bones) is pushed 2.2 cm out along its normals (Displace modifier
on a vertex group, before the subdivision), so the skirt clears her legs. blender -b in.blend --python skirt_room.py -- out.blend"""
import bpy, sys
OUT = sys.argv[sys.argv.index("--") + 1]
o = bpy.data.objects["Mom_female_elegantsuit01"]; gi = {g.index: g.name for g in o.vertex_groups}
vg = o.vertex_groups.get("SkirtRoom") or o.vertex_groups.new(name="SkirtRoom"); n = 0
for v in o.data.vertices:
    g = max(v.groups, key=lambda g: g.weight, default=None); nm = gi.get(g.group, "") if g else ""
    if nm.startswith(("pelvis", "upperleg")) and v.co.z < 0.86:
        w = min(1.0, max(0.0, (0.86 - v.co.z) / 0.25)); vg.add([v.index], w, "REPLACE"); n += 1
d = o.modifiers.new("SkirtRoom", "DISPLACE"); d.vertex_group = "SkirtRoom"; d.strength = 0.022; d.mid_level = 0.0; d.direction = "NORMAL"
arm_i = next(i for i, m in enumerate(o.modifiers) if m.type == "ARMATURE"); o.modifiers.move(o.modifiers.find("SkirtRoom"), arm_i + 1)
print("SKIRT verts", n, [m.type for m in o.modifiers])
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
