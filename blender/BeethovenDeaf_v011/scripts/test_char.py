import bpy, sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(HERE, "lib.py")).read())
exec(open(os.path.join(HERE, "char.py")).read())
out = sys.argv[sys.argv.index("--") + 1]
sc.render.engine = 'CYCLES'; sc.cycles.samples = 24; sc.cycles.use_denoising = True
sc.render.resolution_x, sc.render.resolution_y = 540, 960
sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Punchy'
w = bpy.data.worlds.new("W"); sc.world = w; w.use_nodes = True; w.node_tree.nodes["Background"].inputs[0].default_value = (0.05, 0.25, 0.3, 1); w.node_tree.nodes["Background"].inputs[1].default_value = 1.0
for loc, pw in (((-1.5, -2.5, 2.5), 400), ((2, -1.5, 1.8), 200)):
    L = bpy.data.lights.new("L", 'AREA'); L.energy = pw; L.size = 1.5; o = bpy.data.objects.new("L", L); sc.collection.objects.link(o); o.location = loc
    c = o.constraints.new('TRACK_TO'); c.target = COMP; c.track_axis = 'TRACK_NEGATIVE_Z'
cam = bpy.data.cameras.new("C"); co = bpy.data.objects.new("C", cam); sc.collection.objects.link(co); sc.camera = co
head = COMP.matrix_world @ COMP.data.bones["head"].head_local
e = bpy.data.objects.new("T", None); sc.collection.objects.link(e)
tc = co.constraints.new('TRACK_TO'); tc.target = e; tc.track_axis = 'TRACK_NEGATIVE_Z'; tc.up_axis = 'UP_Y'
for i, (loc, tgt, lens) in enumerate([((0.9, -3.6, 1.1), (0, 0, 0.9), 40), ((0.35, -0.75, head.z + 0.08), head + Vector((0, 0, 0.06)), 50), ((-0.7, 0.2, 1.3), (0, 0, 1.0), 30)]):
    co.location = loc; e.location = tgt; cam.lens = lens
    sc.render.filepath = out + "_%d.png" % i; bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=out + ".blend")
