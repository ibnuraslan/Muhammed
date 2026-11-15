import bpy, sys, os
from mathutils import Vector
OUT = sys.argv[sys.argv.index("--")+1]
sc = bpy.context.scene
for o in bpy.data.objects:
    if o.type=='MESH' and o.data.shape_keys: print("SK", o.name, [(k.name, round(k.value,2)) for k in o.data.shape_keys.key_blocks])
    if o.type=='MESH': print("MATS", o.name, [m.name for m in o.data.materials if m])
w = bpy.data.worlds.new("W"); sc.world = w; w.use_nodes=True; w.node_tree.nodes["Background"].inputs[0].default_value=(0.7,0.8,0.9,1)
L = bpy.data.objects.new("L", bpy.data.lights.new("L","SUN")); L.data.energy=3; L.rotation_euler=(0.8,0,0.3); sc.collection.objects.link(L)
cam = bpy.data.objects.new("C", bpy.data.cameras.new("C")); sc.collection.objects.link(cam); sc.camera=cam
sc.render.engine='CYCLES'; sc.cycles.samples=8; sc.render.image_settings.file_format='JPEG'
cam.location=(3.6,-9,1.0); cam.rotation_euler=(1.5708,0,0); cam.data.lens=35
sc.render.resolution_x=1400; sc.render.resolution_y=700; sc.render.filepath=OUT+"_full.jpg"; bpy.ops.render.render(write_still=True)
sc.render.resolution_x=1400; sc.render.resolution_y=240
cam.location=(3.6,-5.5,1.62); cam.data.lens=85; sc.render.filepath=OUT+"_faces.jpg"; bpy.ops.render.render(write_still=True)
