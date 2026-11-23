import os, sys, math
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scenes"))
import common as C
C.reset()
import bpy
from mathutils import Vector
import bones as B
sc = C.render_setup(samples=int(os.environ.get("SPP", "24")), noise=0.05, bounces=6)
bpy.ops.mesh.primitive_plane_add(size=6); fl = bpy.context.active_object
fm = bpy.data.materials.new("floor"); fm.use_nodes = True; fm.node_tree.nodes["Principled BSDF"].inputs[0].default_value = (0.4, 0.34, 0.25, 1)
fl.data.materials.append(fm)
sk = B.Skeleton("M", "A").pose_crouched().place((0, 0, 0), heading=90)
std = B.Skeleton("F", "B"); std.root.location = (0, 1.4, 0.88)     # rest pose reference
cr = B.hero_cranium(); cr.location = (1.2, -0.6, 0.09)
md = B.hero_mandible(); md.location = (1.45, -0.6, 0.04)
w = bpy.data.worlds.new("W"); sc.world = w; w.use_nodes = True; w.node_tree.nodes["Background"].inputs[1].default_value = 0.4
k = bpy.data.lights.new("key", 'AREA'); k.size = 2; k.energy = 600; ko = bpy.data.objects.new("key", k); sc.collection.objects.link(ko); ko.location = (-2, -2, 3)
ko.rotation_euler = (Vector((0, 0, 0)) - ko.location).to_track_quat('-Z', 'Y').to_euler()
out = os.path.join(C.HERE, "..", "out", "tests")
for tag, loc, tgt, lens in (("top", (0.3, 0.2, 3.2), (0.3, 0.2, 0), 28), ("side", (0.2, -2.4, 0.7), (0.2, 0.3, 0.3), 30),
                             ("skull", (1.32, -1.05, 0.14), (1.32, -0.6, 0.05), 60), ("skull2", (1.0, -0.55, 0.06), (1.35, -0.6, 0.05), 60)):
    C.camera(loc, tgt, lens=lens)
    sc.render.filepath = os.path.join(out, f"bones_{tag}.png"); bpy.ops.render.render(write_still=True)
for s, o in sk.parts.items():
    pass
print("SEGS", sorted(sk.parts))
