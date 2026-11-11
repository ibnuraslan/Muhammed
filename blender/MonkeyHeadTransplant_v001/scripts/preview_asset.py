import bpy, sys, math
from mathutils import Vector
a = sys.argv[sys.argv.index("--")+1:]; p, out = a[0], a[1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=p)
ms = [o for o in bpy.data.objects if o.type == "MESH" and o.name != "Icosphere"]
for o in bpy.data.objects:
    if o.name == "Icosphere": o.hide_render = True
bb = [o.matrix_world @ Vector(c) for o in ms for c in o.bound_box]
mn = Vector([min(v[i] for v in bb) for i in range(3)]); mx = Vector([max(v[i] for v in bb) for i in range(3)])
c = (mn+mx)/2; r = (mx-mn).length
print("WORLD BB", mn, mx)
sc = bpy.context.scene
cam = bpy.data.objects.new("c", bpy.data.cameras.new("c")); sc.collection.objects.link(cam); sc.camera = cam
w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True; w.node_tree.nodes["Background"].inputs[0].default_value = (0.6,0.7,0.8,1)
L = bpy.data.objects.new("l", bpy.data.lights.new("l", "SUN")); sc.collection.objects.link(L); L.rotation_euler = (0.8, 0.2, 0.5); L.data.energy = 3
sc.render.engine = "CYCLES"; sc.cycles.samples = 16; sc.render.resolution_x = 400; sc.render.resolution_y = 400
for i, ang in enumerate([0, 90, 180]):
    d = Vector((math.sin(math.radians(ang)), -math.cos(math.radians(ang)), 0.25)).normalized()
    cam.location = c + d * r * 1.3
    cam.rotation_euler = (c - cam.location).to_track_quat("-Z", "Y").to_euler()
    sc.render.filepath = f"{out}_{ang}.jpg"; sc.render.image_settings.file_format = "JPEG"
    bpy.ops.render.render(write_still=True)
