import os, sys, math
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scenes"))
import common as C
C.reset()
import bpy
from mathutils import Vector
import bones as B
sc = C.render_setup(samples=24, noise=0.05, bounces=6)
cr = B.hero_cranium(); md = B.hero_mandible()
import numpy as np
def bb(o):
    co = np.array([v.co for v in o.data.vertices]); return co.min(0), co.max(0)
print("CR", bb(cr)); print("MD", bb(md))
cr.location = (0, 0, 0.12); md.location = (float(os.environ.get("MX", "0")), float(os.environ.get("MY", "0.01")), float(os.environ.get("MZ", "0.05")))
w = bpy.data.worlds.new("W"); sc.world = w; w.use_nodes = True; w.node_tree.nodes["Background"].inputs[1].default_value = 0.6
k = bpy.data.lights.new("key", 'AREA'); k.size = 0.5; k.energy = 30; ko = bpy.data.objects.new("key", k); sc.collection.objects.link(ko); ko.location = (0.4, -0.5, 0.6)
ko.rotation_euler = (Vector((0, 0, 0.1)) - ko.location).to_track_quat('-Z', 'Y').to_euler()
out = os.path.join(C.HERE, "..", "out", "tests")
for tag, loc, tgt in (("side", (0.55, 0.0, 0.08), (0, 0.0, 0.08)), ("under", (0.08, -0.15, -0.25), (0, 0.0, 0.06)), ("front", (0.1, -0.55, 0.1), (0, 0, 0.08))):
    C.camera(loc, tgt, lens=50)
    sc.render.filepath = os.path.join(out, f"skull_{tag}.png"); bpy.ops.render.render(write_still=True)
