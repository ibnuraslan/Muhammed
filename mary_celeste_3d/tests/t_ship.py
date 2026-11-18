import sys, os, math, time; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
import bpy
from mathutils import Vector
bpy.ops.wm.read_factory_settings(use_empty=True)
import ship
t0 = time.time()
s = ship.build("MC", sails=os.environ.get("SAILS", "found"), rail_gap=(-2.7, -0.6, "S"), detail=False)
print("built", time.time() - t0, len(s["coll"].objects))
sc = bpy.context.scene; sc.render.engine = 'CYCLES'; sc.cycles.samples = 16; sc.cycles.use_denoising = True
sc.render.resolution_x, sc.render.resolution_y = 1280, 720
w = bpy.data.worlds.new("W"); sc.world = w
w.use_nodes = True; w.node_tree.nodes["Background"].inputs[0].default_value = (0.5, 0.55, 0.6, 1); w.node_tree.nodes["Background"].inputs[1].default_value = 0.8
l = bpy.data.lights.new("sun", 'SUN'); l.energy = 3; o = bpy.data.objects.new("sun", l); sc.collection.objects.link(o); o.rotation_euler = (0.7, 0.2, 2.2)
cam = bpy.data.objects.new("C", bpy.data.cameras.new("C")); sc.collection.objects.link(cam); sc.camera = cam
v = os.environ.get("VIEW", "34")
if v == "34":
    cam.location = (38, -42, 9); tgt = Vector((0, 0, 9)); cam.data.lens = 35
elif v == "deck":
    cam.location = (-6.0, 0.6, 3.0); tgt = Vector((-1.6, -3.2, 1.6)); cam.data.lens = 28
cam.rotation_euler = (tgt - cam.location).to_track_quat('-Z', 'Y').to_euler()
sc.view_settings.view_transform = 'AgX'
sc.render.filepath = os.environ.get("OUT", "/tmp/t_ship.png")
bpy.ops.render.render(write_still=True); print("done", time.time() - t0)
