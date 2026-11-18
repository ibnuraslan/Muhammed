import sys, os, math, time; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
import bpy
from mathutils import Vector
bpy.ops.wm.read_factory_settings(use_empty=True)
import human as H, deveau as D
t0 = time.time()
d = D.Deveau(); h = d.h
for sd, sg in H.SIDE.items():
    h.aim(f"upperarm01.{sd}", (0.18 * sg, 0.05, -1)); h.aim(f"upperarm02.{sd}", (0.18 * sg, 0.05, -1))
    h.aim(f"lowerarm01.{sd}", (0.1 * sg, -0.25, -1)); h.aim(f"lowerarm02.{sd}", (0.1 * sg, -0.25, -1))
    h.aim(f"wrist.{sd}", (0.05 * sg, -0.15, -1))
H.fingers_curl(h, 22)
h.rot("head", (1, 0, 0), 6)
d.finish(look_at=(0.6, -3, 1.4), density=float(os.environ.get("DENS", "0.5")))
print("built", time.time() - t0)
sc = bpy.context.scene; sc.render.engine = 'CYCLES'; sc.cycles.samples = int(os.environ.get("SPP", "48")); sc.cycles.use_denoising = True
sc.render.resolution_x, sc.render.resolution_y = 1280, 720
w = bpy.data.worlds.new("W"); sc.world = w; w.use_nodes = True; w.node_tree.nodes["Background"].inputs[0].default_value = (0.02, 0.022, 0.025, 1)
def light(loc, e, size, col=(1, 0.85, 0.7)):
    l = bpy.data.lights.new("L", 'AREA'); l.energy = e; l.size = size; l.color = col
    o = bpy.data.objects.new("L", l); sc.collection.objects.link(o); o.location = loc; o.visible_camera = False
    o.rotation_euler = (Vector((0, -0.2, 1.5)) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
light((-1.2, -1.5, 2.0), 60, 0.8); light((1.5, -1.0, 1.5), 10, 2, (0.7, 0.8, 1)); light((0.3, 1.5, 2.2), 30, 1)
cam = bpy.data.objects.new("C", bpy.data.cameras.new("C")); sc.collection.objects.link(cam); sc.camera = cam
mode = os.environ.get("MODE", "face")
if mode == "face":
    cam.data.lens = 85; cam.location = (0.35, -1.05, 1.62); tgt = Vector((0, -0.05, 1.6))
else:
    cam.data.lens = 35; cam.location = (1.2, -3.4, 1.2); tgt = Vector((0, 0, 0.95))
cam.rotation_euler = (tgt - cam.location).to_track_quat('-Z', 'Y').to_euler()
sc.view_settings.view_transform = 'AgX'
sc.render.filepath = os.environ.get("OUT", "/tmp/t_char.png")
bpy.ops.render.render(write_still=True); print("done", time.time() - t0)
