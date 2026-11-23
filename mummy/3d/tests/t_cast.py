"""Cast lineup: the six men side by side (3/4 back + front views), low samples."""
import os, sys, math
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scenes"))
import common as C
C.reset()
import bpy
from mathutils import Vector, Matrix
import modern as MD, look
sc = C.render_setup(samples=int(os.environ.get("SPP", "48")), noise=0.05, bounces=6)
names = os.environ.get("CAST", "Leonardo,DOnorio,Finotto,Guard,Porter,Investigator").split(",")
people = []
for i, n in enumerate(names):
    m = MD.CAST[n]()
    m.relaxed()
    x = (i - (len(names) - 1) / 2) * 0.9
    m.finish(look_at=(x, -5, 1.6), place=Matrix.Translation((x, 0, 0)), density=float(os.environ.get("HAIR", "0.6")))
    people.append(m)
bpy.ops.mesh.primitive_plane_add(size=30); fl = bpy.context.active_object
fm = bpy.data.materials.new("floor"); fm.use_nodes = True; fm.node_tree.nodes["Principled BSDF"].inputs[0].default_value = (0.12, 0.1, 0.08, 1)
fl.data.materials.append(fm)
w = bpy.data.worlds.new("W"); sc.world = w; w.use_nodes = True; w.node_tree.nodes["Background"].inputs[1].default_value = 0.3
k = bpy.data.lights.new("key", 'AREA'); k.size = 3; k.energy = 1500; k.color = (1, 0.85, 0.7)
ko = bpy.data.objects.new("key", k); sc.collection.objects.link(ko); ko.location = (-3, -4, 4)
ko.rotation_euler = (Vector((0, 0, 1)) - ko.location).to_track_quat('-Z', 'Y').to_euler()
r = bpy.data.lights.new("rim", 'AREA'); r.size = 2; r.energy = 800
ro = bpy.data.objects.new("rim", r); sc.collection.objects.link(ro); ro.location = (3, 3, 3)
ro.rotation_euler = (Vector((0, 0, 1)) - ro.location).to_track_quat('-Z', 'Y').to_euler()
out = os.path.join(C.HERE, "..", "out", "tests")
os.makedirs(out, exist_ok=True)
W = len(names) * 0.9
for tag, loc in (("front", (0, -7.5, 1.2)), ("back34", (3.5, 6.0, 1.6))):
    C.camera(Vector(loc), Vector((0, 0, 0.95)), lens=40)
    sc.render.filepath = os.path.join(out, f"cast_{tag}.png")
    bpy.ops.render.render(write_still=True)
    print("RENDERED", sc.render.filepath)
