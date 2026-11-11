import bpy, glob, os
from mathutils import Vector
for f in sorted(glob.glob(os.path.abspath("assets/models/*.glb"))):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=f)
    new = [o for o in bpy.data.objects if o not in before]
    ms = [o for o in new if o.type == 'MESH']
    bpy.context.view_layer.update()
    pts = [o.matrix_world @ Vector(c) for o in ms for c in o.bound_box]
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts))); hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    imgs = {i.name: tuple(i.size) for m in ms for s in m.material_slots if s.material and s.material.node_tree for n in s.material.node_tree.nodes if n.type == 'TEX_IMAGE' and n.image for i in [n.image]}
    print("MODEL", os.path.basename(f), "objs", len(new), "meshes", len(ms), "polys", sum(len(o.data.polygons) for o in ms), "size", tuple(round(v, 2) for v in hi - lo), "min", tuple(round(v, 2) for v in lo), "imgs", imgs)
    for o in new: bpy.data.objects.remove(o, do_unlink=True)
