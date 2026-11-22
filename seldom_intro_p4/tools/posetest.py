"""Quick pose check: one person on a floor, side + front views, low res.  blender -b -P tools/posetest.py -- kind posename out.png"""
import os, sys, math
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
import si; si.C.reset()
import bpy, p4, ship, poses as P
from mathutils import Vector
a = sys.argv[sys.argv.index("--") + 1:]
kind, pname, out = a[0], a[1], a[2]
def kneelR(h, dv, M, Mi):
    si.kneel(h, down="R", lean=18, drop=0.42, fwd=0.40); P.head(h, pitch=18)
def sarah_hold(h, dv, M, Mi):
    P.stand(h, lean=3, weight="L"); P.head(h, pitch=30)
    P.hand_reach(h, "R", Vector((-0.22, -0.32, 1.12)), elbow=(-0.7, 0.4, -0.6), hand_dir=Vector((0, -0.3, -1)))
    P.grip(h, "R", 1.0)
    P.hand_reach(h, "L", Vector((0.2, -0.38, 0.86)), elbow=(0.7, 0.4, -0.5), hand_dir=Vector((-0.1, -0.9, -0.4)))
    P.rest_hand(h, "L", curl=12)
POSES = dict(kneelR=kneelR, sarah_hold=sarah_hold)
sc = si.C.render_setup(samples=16, noise=0.1, bounces=4); sc.render.resolution_percentage = 20
ship.box("floor", (0, 0, -0.01), (6, 6, 0.02), p4.mat("fl", (0.3, 0.3, 0.3), 0.8))
p4.world_color((0.4, 0.4, 0.42)); p4.sun(30, 50, 3)
dv, M = si.person(kind, (0, 0), 0, POSES[pname], (2, 0, 1), hair=0.0, shawl=os.environ.get("SHAWL", "1") == "1")
import subprocess
for nm, loc in (("side", (0.3, -2.6, 1.1)), ("front", (2.6, 0.2, 1.1))):
    si.cam(loc, (0, 0, 0.9), lens=35)
    sc.render.filepath = out.replace(".png", f"_{nm}.png"); bpy.ops.render.render(write_still=True)
