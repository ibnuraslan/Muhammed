import bpy, sys
from mathutils import Vector
p = sys.argv[sys.argv.index("--")+1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=p)
for o in bpy.data.objects:
    bb = [o.matrix_world @ Vector(c) for c in o.bound_box]
    mn = Vector([min(v[i] for v in bb) for i in range(3)]); mx = Vector([max(v[i] for v in bb) for i in range(3)])
    extra = ""
    if o.type == "MESH": extra = f"v={len(o.data.vertices)} mats={[m.name for m in o.data.materials]} vg={len(o.vertex_groups)} shapekeys={bool(o.data.shape_keys)}"
    if o.type == "ARMATURE": extra = f"bones={len(o.data.bones)} {[b.name for b in o.data.bones][:60]}"
    print("OBJ", o.name, o.type, "parent", o.parent.name if o.parent else None, "min", tuple(round(x,3) for x in mn), "max", tuple(round(x,3) for x in mx), extra)
print("IMGS", [(i.name, i.size[:]) for i in bpy.data.images])
print("ACTIONS", [(a.name, a.frame_range[:]) for a in bpy.data.actions])
