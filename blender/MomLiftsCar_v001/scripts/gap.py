import bpy
from mathutils import Vector
sc = bpy.context.scene
for f in (1, 60, 120, 160):
    sc.frame_set(f); dg = bpy.context.evaluated_depsgraph_get()
    cars = [o for o in bpy.data.objects if o.name.startswith("Object_")]
    worst = (9, None)
    for nm in ("Son.body", "Son.male_casualsuit04"):
        ob = bpy.data.objects[nm].evaluated_get(dg); me = ob.to_mesh(); M = ob.matrix_world
        for v in list(me.vertices)[::7]:
            p = M @ v.co
            if p.z > 0.6: continue
            for c in cars:
                ce = c.evaluated_get(dg); inv = ce.matrix_world.inverted()
                hit, loc, n, i = ce.ray_cast(inv @ Vector((p.x, p.y, 0.02)), (inv.to_3x3() @ Vector((0, 0, 1))).normalized())
                if hit:
                    g = (ce.matrix_world @ loc).z - p.z
                    if g < worst[0]: worst = (g, tuple(round(t, 2) for t in p), c.name)
        ob.to_mesh_clear()
    print("GAP", f, worst)
