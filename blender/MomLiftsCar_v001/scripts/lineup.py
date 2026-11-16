import bpy, math
sc = bpy.context.scene
names = ["Mom","MomB","Son","SonB","Man","ManB"]
for i, n in enumerate(names):
    with bpy.data.libraries.load("/tmp/claude-0/b14/work/ch_%s.blend" % n) as (fd, td): td.objects = list(fd.objects)
    for o in td.objects:
        if o: sc.collection.objects.link(o)
    bpy.data.objects[n].location.x = (i - 2.5) * 0.85
cam = bpy.data.objects.new("C", bpy.data.cameras.new("C")); sc.collection.objects.link(cam); sc.camera = cam
cam.location = (0, -6.5, 1.1); cam.rotation_euler = (math.radians(90), 0, 0); cam.data.lens = 40
w = bpy.data.worlds.new("W"); sc.world = w; w.use_nodes = True; w.node_tree.nodes["Background"].inputs[0].default_value = (0.6,0.8,1,1)
l = bpy.data.objects.new("S", bpy.data.lights.new("S", 'SUN')); l.data.energy = 3; l.rotation_euler = (0.8, 0.2, 0.3); sc.collection.objects.link(l)
sc.render.engine = 'CYCLES'; sc.cycles.samples = 8; sc.render.resolution_x, sc.render.resolution_y = 1600, 700
sc.render.filepath = "/tmp/claude-0/b14/review/lineup.jpg"; sc.render.image_settings.file_format = 'JPEG'
bpy.ops.render.render(write_still=True)
