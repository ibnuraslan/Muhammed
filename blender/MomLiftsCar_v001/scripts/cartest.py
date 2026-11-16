import bpy, math
from mathutils import Vector
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
bpy.ops.import_scene.gltf(filepath="/tmp/claude-0/b14/assets/car.glb")
root = [o for o in bpy.data.objects if o.parent is None][0]; root.scale = (0.01,)*3 if root.scale[0] > 0.5 else root.scale
bpy.context.view_layer.update()
w = bpy.data.worlds.new("W"); sc.world = w; w.use_nodes = True; w.node_tree.nodes["Background"].inputs[0].default_value = (0.6,0.8,1,1)
l = bpy.data.objects.new("S", bpy.data.lights.new("S", 'SUN')); l.data.energy = 3; l.rotation_euler = (0.8, 0.2, 0.3); sc.collection.objects.link(l)
cam = bpy.data.objects.new("C", bpy.data.cameras.new("C")); sc.collection.objects.link(cam); sc.camera = cam
sc.render.engine = 'CYCLES'; sc.cycles.samples = 8; sc.render.resolution_x, sc.render.resolution_y = 800, 500
sc.render.image_settings.file_format = 'JPEG'
for nm, p in (("a", (7, 5, 2.5)), ("b", (-7, -5, 2.5)), ("c", (0, 0, 12))):
    cam.location = p; d = Vector((0,0,0.6)) - Vector(p); cam.rotation_euler = d.to_track_quat('-Z','Y').to_euler(); cam.data.lens = 30
    sc.render.filepath = "/tmp/claude-0/b14/review/car_%s.jpg" % nm; bpy.ops.render.render(write_still=True)
for o in bpy.data.objects:
    if o.type=='MESH':
        bb=[o.matrix_world @ Vector(c) for c in o.bound_box]; print("WB", o.name, tuple(round(x,2) for x in map(min,*bb)), tuple(round(x,2) for x in map(max,*bb)))
