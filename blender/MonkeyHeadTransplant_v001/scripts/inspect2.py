import bpy, sys
from mathutils import Vector
for f in ["spine","ortable","orset"]:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=f"assets/{f}.glb")
    ms = [o for o in bpy.data.objects if o.type == "MESH"]
    bb = [o.matrix_world @ Vector(c) for o in ms for c in o.bound_box]
    mn = Vector([min(v[i] for v in bb) for i in range(3)]); mx = Vector([max(v[i] for v in bb) for i in range(3)])
    print("ASSET", f, "meshes", len(ms), "verts", sum(len(o.data.vertices) for o in ms), "size", tuple(round(x,3) for x in (mx-mn)), "min", tuple(round(x,3) for x in mn))
    print("  names", [o.name for o in ms][:20]); print("  imgs", [(i.name, i.size[:]) for i in bpy.data.images])
