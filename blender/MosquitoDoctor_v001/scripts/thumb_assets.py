"""Render a quick look at each GLB asset. blender -b --factory-startup --python thumb_assets.py -- assets_dir out_dir name1 name2"""
import bpy, sys, os, math
from mathutils import Vector
a = sys.argv[sys.argv.index("--") + 1:]; A, O, names = a[0], a[1], a[2:]
os.makedirs(O, exist_ok=True)
sc = bpy.context.scene; sc.render.engine = 'CYCLES'; sc.cycles.samples = 16; sc.render.resolution_x = sc.render.resolution_y = 500
sc.world = bpy.data.worlds.new("w"); sc.world.color = (0.8, 0.85, 0.9)
for n in names:
    for o in list(bpy.data.objects): bpy.data.objects.remove(o, do_unlink=True)
    bpy.ops.import_scene.gltf(filepath=f"{A}/{n}.glb")
    ms = [o for o in bpy.data.objects if o.type == 'MESH']
    pts = [o.matrix_world @ Vector(c) for o in ms for c in o.bound_box]
    lo = Vector([min(p[i] for p in pts) for i in range(3)]); hi = Vector([max(p[i] for p in pts) for i in range(3)])
    c = (lo + hi) / 2; r = (hi - lo).length / 2
    print("ASSET", n, "size", [round(x, 3) for x in (hi - lo)], "meshes", len(ms), [o.name for o in ms][:20])
    cam = bpy.data.objects.new("C", bpy.data.cameras.new("C")); sc.collection.objects.link(cam); sc.camera = cam
    d = Vector((1, -1.3, 0.8)).normalized(); cam.location = c + d * r * 2.6
    cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
    L = bpy.data.objects.new("L", bpy.data.lights.new("L", 'SUN')); L.data.energy = 3; L.rotation_euler = (0.6, 0.2, 0.5); sc.collection.objects.link(L)
    sc.render.filepath = f"{O}/{n}.png"; bpy.ops.render.render(write_still=True)
