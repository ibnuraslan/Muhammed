import os, sys, math
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
import p4
p4.C.reset()
import bpy
from mathutils import Vector, Matrix
import cutaway, barrels as BR
sc = p4.C.render_setup(samples=int(os.environ.get("SPP","48")), noise=0.03, bounces=6)
print("FULL HOLD COUNT", BR.count_full_hold())
s = cutaway.build("MCX", y_cut=0.02)
res = BR.stow(ymax=0.02, red_slots=[40, 41, 42, 77, 78, 120, 121, 160, 161])
print("STOWED", len(res))
p4.world_color((0.035, 0.02, 0.014), 1.0)
p4.light('AREA', "key", 9000, (1.0, 0.78, 0.55), loc=(6, 14, 12), target=(0, 0, -0.5), size=8)
p4.light('AREA', "rim", 3000, (0.9, 0.7, 0.5), loc=(-14, -6, 8), target=(0, 0, 0), size=6)
p4.light('POINT', "lantern", 120, (1.0, 0.62, 0.3), loc=(0.5, -1.0, 0.6), size=0.05)
floor = p4.mat("void_floor", (0.05, 0.03, 0.02), rough=0.8)
import ship
ship.box("ground", (0, 0, -3.2), (80, 80, 0.02), floor)
cam = p4.C.camera((7, 13, 1.2), (0.0, -1.2, -0.9), lens=30)
p4.C.finish(os.environ.get("OUT", "/tmp/t/cut.png"), cine={"sat": 1.0, "exposure": 0.0})
