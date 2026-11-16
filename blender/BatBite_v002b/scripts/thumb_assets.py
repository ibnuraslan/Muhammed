import bpy, sys, os, glob, math
from mathutils import Vector
A, OUT = sys.argv[sys.argv.index("--")+1:][:2]
os.makedirs(OUT, exist_ok=True)
for f in sorted(glob.glob(A+"/*.glb")):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=f)
    ms = [o for o in bpy.data.objects if o.type=='MESH']
    pts = [o.matrix_world @ Vector(c) for o in ms for c in o.bound_box]
    lo = Vector([min(p[i] for p in pts) for i in range(3)]); hi = Vector([max(p[i] for p in pts) for i in range(3)])
    c = (lo+hi)/2; r = (hi-lo).length/2
    sc = bpy.context.scene
    cam = bpy.data.objects.new("C", bpy.data.cameras.new("C")); sc.collection.objects.link(cam); sc.camera = cam
    d = Vector((1.0, -1.6, 0.7)).normalized()
    cam.location = c + d * r * 2.6; cam.rotation_euler = (-d).to_track_quat('-Z','Y').to_euler(); cam.data.clip_end = r*20; cam.data.clip_start = r*0.01
    w = bpy.data.worlds.new("W"); sc.world = w; w.use_nodes = True; w.node_tree.nodes["Background"].inputs[0].default_value=(0.6,0.7,0.8,1); w.node_tree.nodes["Background"].inputs[1].default_value=1.5
    L = bpy.data.objects.new("L", bpy.data.lights.new("L","SUN")); L.data.energy=3; L.rotation_euler=(0.6,0.2,0.5); sc.collection.objects.link(L)
    sc.render.engine='CYCLES'; sc.cycles.samples=8; sc.render.resolution_x=sc.render.resolution_y=300
    sc.render.filepath = os.path.join(OUT, os.path.basename(f)[:-4]+".jpg"); sc.render.image_settings.file_format='JPEG'
    bpy.ops.render.render(write_still=True)
