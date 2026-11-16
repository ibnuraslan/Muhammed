import bpy
sc = bpy.context.scene
import sys
for f in [int(x) for x in sys.argv[-1].split(",")]:
    sc.frame_set(f); dg = bpy.context.evaluated_depsgraph_get(); out = []
    for nm in ("Son.body", "Son.male_casualsuit04", "Son.shoes02", "Mom.shoes02", "Man.shoes01"):
        o = bpy.data.objects.get(nm)
        if not o: continue
        ob = o.evaluated_get(dg); me = ob.to_mesh(); z = min((ob.matrix_world @ v.co).z for v in me.vertices); ob.to_mesh_clear(); out.append((nm, round(z, 3)))
    print("LOWZ", f, out)
