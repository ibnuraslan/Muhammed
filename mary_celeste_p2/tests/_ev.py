exec(open("/home/user/Muhammed/mary_celeste_p2/tests/_nohair.py").read().split("C.finish")[0])
import numpy as np
for o in bpy.data.objects:
    if o.type == 'MESH':
        for m in o.modifiers:
            if m.type == 'SUBSURF': m.levels = m.render_levels
bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get()
for o in bpy.data.objects:
    if o.type == 'MESH' and 'button' not in o.name:
        oe = o.evaluated_get(dg); me = oe.to_mesh()
        P = np.array([(o.matrix_world @ v.co)[:] for v in me.vertices])
        print("EV", o.name, len(P), P.min(0).round(2), P.max(0).round(2))
        oe.to_mesh_clear()
