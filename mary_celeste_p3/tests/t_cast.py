import os, sys, math
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "lib")); sys.path.insert(0, os.path.join(HERE, "..", "..", "mary_celeste_3d", "scenes"))
import common as C
C.reset()
import bpy
from mathutils import Vector
import crew, poses as P
sc = C.render_setup(samples=48, noise=0.05)
keys = os.environ.get("KEYS", "morehouse,flood,surveyor,diver").split(",")
for i, k in enumerate(keys):
    p = crew.person(k, wig=(k in ("flood", "judge")))
    P.stand(p.h, lean=3); P.arm_down(p.h, "L"); P.arm_down(p.h, "R"); P.rest_hand(p.h, "L"); P.rest_hand(p.h, "R")
    M = crew.place((i * 0.8, 0, 0), -90)
    p.finish(look_at=(i * 0.8, -3, 1.6), place=M, density=0.5)
    if k in ("surveyor",): crew.top_hat(p)
    if k == "flood" and os.environ.get("ROLLS"): crew.wig_rolls(p)
    if k == "flood": crew.bands(p)
    if k == "diver": crew.diver_helmet(p)
w = bpy.data.worlds.new("W"); sc.world = w; w.use_nodes = True; w.node_tree.nodes["Background"].inputs[1].default_value = 0.3
l = bpy.data.objects.new("K", bpy.data.lights.new("K", 'AREA')); sc.collection.objects.link(l); l.data.energy = 600; l.data.size = 2
l.location = (-1, -3, 3); l.rotation_euler = (Vector((1.2, 0, 1.4)) - l.location).to_track_quat('-Z', 'Y').to_euler()
n = len(keys)
C.camera(Vector(((n - 1) * 0.4, -4.2, 1.45)), Vector(((n - 1) * 0.4, 0, 1.25)), lens=40)
sc.render.filepath = os.environ.get("OUT", "/tmp/claude-0/cast.png"); bpy.ops.render.render(write_still=True)
if os.environ.get("FACES"):
    for i, k in enumerate(keys):
        C.camera(Vector((i * 0.8, -1.0, 1.65)), Vector((i * 0.8, 0, 1.6)), lens=60)
        sc.render.filepath = f"/tmp/claude-0/face_{k}.png"; bpy.ops.render.render(write_still=True)
