import bpy
from mathutils import Vector
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath="/tmp/claude-0/b14/assets/car.glb")
dg = bpy.context.evaluated_depsgraph_get()
for o in bpy.data.objects:
    if o.type != 'MESH': print("OBJ", o.name, o.type); continue
    bb = [o.matrix_world @ Vector(c) for c in o.bound_box]
    mn = Vector(map(min, *bb)); mx = Vector(map(max, *bb))
    print("MESH", o.name, len(o.data.polygons), [m.name for m in o.data.materials], tuple(round(x,2) for x in mn), tuple(round(x,2) for x in mx))
for i in bpy.data.images: print("IMG", i.name, i.size[:])
