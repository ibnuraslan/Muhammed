import bpy
from mathutils import Vector
sc = bpy.context.scene; dg = bpy.context.evaluated_depsgraph_get()
mon = bpy.data.objects["Monitor"]
print("MON", mon.location, mon.dimensions, mon.rotation_euler)
for z in [0.85,0.9,0.95,1.0,1.05,1.1,1.15]:
    row=[]
    for x in [2.95,3.0,3.05,3.1,3.15]:
        h = sc.ray_cast(dg, Vector((x,-1,z)), Vector((0,1,0)))
        row.append(round(h[1].y,3) if h[0] and h[4].name=="Monitor" else None)
    print("ROW", z, row)
for nm in ("Surgeon","Nurse"):
    r = bpy.data.objects[nm]; print("BONE", nm, r.data.bones["root"].head_local, r.data.bones["wrist.L"].head_local, r.data.bones["head"].head_local)
nr = bpy.data.objects["NeckRef"]; print("NECKREF", nr.location, nr.matrix_world.translation)
print("ROOTB", bpy.data.objects["MonkeyRootB"].matrix_world)
