import bpy, sys
from mathutils import Vector
OUT = sys.argv[sys.argv.index("--")+1]; sc = bpy.context.scene
w = bpy.data.worlds.new("W"); sc.world = w; w.use_nodes=True; w.node_tree.nodes["Background"].inputs[0].default_value=(0.7,0.8,0.9,1)
L = bpy.data.objects.new("L", bpy.data.lights.new("L","SUN")); L.data.energy=3; L.rotation_euler=(0.9,0,0.4); sc.collection.objects.link(L)
cam = bpy.data.objects.new("C", bpy.data.cameras.new("C")); sc.collection.objects.link(cam); sc.camera=cam
sc.render.engine='CYCLES'; sc.cycles.samples=12; sc.render.image_settings.file_format='JPEG'; sc.render.resolution_x=400; sc.render.resolution_y=500
for n in sys.argv[sys.argv.index("--")+2:]:
    r = bpy.data.objects[n]; e = r.matrix_world @ r.data.bones["head"].head_local + Vector((0,0,0.06))
    for tag, off in (("f", Vector((0.25,-1.1,0.05))), ("s", Vector((1.0,-0.6,0.05))), ("b", Vector((0.2,1.1,0.1)))):
        cam.location = e + off; cam.rotation_euler = (-off).to_track_quat('-Z','Y').to_euler(); cam.data.lens=85
        sc.render.filepath = "%s_%s_%s.jpg" % (OUT, n, tag); bpy.ops.render.render(write_still=True)
