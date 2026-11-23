"""Quick look at Sketchfab assets: blender -b --python tools/inspect_glb.py -- uid [uid...] -> out/inspect/<uid>.jpg"""
import bpy, sys, os
from mathutils import Vector
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
for uid in sys.argv[sys.argv.index("--") + 1:]:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene; sc.render.engine = 'CYCLES'; sc.cycles.samples = 12; sc.cycles.use_denoising = True
    sc.render.resolution_x, sc.render.resolution_y = 640, 360; sc.view_settings.view_transform = 'AgX'
    bpy.ops.import_scene.gltf(filepath=os.path.join(D, "assets", "sketchfab", uid + ".glb"))
    ms = [o for o in sc.objects if o.type == 'MESH']
    bpy.context.view_layer.update()
    pts = [o.matrix_world @ Vector(c) for o in ms for c in o.bound_box]
    lo = Vector([min(p[i] for p in pts) for i in range(3)]); hi = Vector([max(p[i] for p in pts) for i in range(3)])
    c = (lo + hi) / 2; r = (hi - lo).length
    print("BOUNDS", uid, [round(x, 3) for x in (hi - lo)], "meshes", len(ms), "faces", sum(len(o.data.polygons) for o in ms))
    cam = bpy.data.objects.new("c", bpy.data.cameras.new("c")); sc.collection.objects.link(cam); sc.camera = cam
    cam.location = c + Vector((0.7, -1.0, 0.8)).normalized() * r * 1.1
    cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler(); cam.data.clip_end = r * 10; cam.data.clip_start = r / 1000
    w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True; w.node_tree.nodes["Background"].inputs[1].default_value = 1.0
    l = bpy.data.objects.new("s", bpy.data.lights.new("s", 'SUN')); l.data.energy = 3; l.rotation_euler = (0.7, 0.2, 0.5); sc.collection.objects.link(l)
    sc.render.image_settings.file_format = 'JPEG'
    sc.render.filepath = os.path.join(D, "out", "inspect", uid + ".jpg"); bpy.ops.render.render(write_still=True)
