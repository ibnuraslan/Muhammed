import sys, bpy, math
exec(open("/home/user/Muhammed/blender/Tsunami2004_v001/scripts/lib.py").read())
names = sys.argv[sys.argv.index("--") + 1:]
for o in list(bpy.data.objects): bpy.data.objects.remove(o)
sc = bpy.context.scene; sc.render.engine = 'CYCLES'; sc.cycles.samples = 8
sc.render.resolution_x = sc.render.resolution_y = 300
w = bpy.data.worlds.new("W"); sc.world = w; w.use_nodes = True; w.node_tree.nodes["Background"].inputs["Strength"].default_value = 1.0
sd = bpy.data.lights.new("s", 'SUN'); sd.energy = 4; so = bpy.data.objects.new("s", sd); sc.collection.objects.link(so); so.rotation_euler = (0.8, 0.2, 0.6)
cd = bpy.data.cameras.new("c"); cam = bpy.data.objects.new("c", cd); sc.collection.objects.link(cam); sc.camera = cam
for n in names:
    ob = import_glb(n, 10.0, "max", sc.collection)
    d = ob.dimensions
    vs = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
    print("DIM", n, tuple(round(x, 2) for x in d), len(ob.data.polygons), [ (m.name if m else None) for m in ob.data.materials][:6])
    for k, ang in enumerate((0, 90)):
        a = math.radians(ang)
        cam.location = (16 * math.sin(a), -16 * math.cos(a), 6); cam.rotation_euler = (Vector((0, 0, d.z / 2)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
        sc.render.filepath = "/tmp/claude-0/pm/%s_%d.jpg" % (n, k); bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(ob)
