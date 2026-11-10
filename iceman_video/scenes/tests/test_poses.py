import sys, os, math
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import bpy
from mathutils import Vector
from common import *
from human import *
OUT = sys.argv[sys.argv.index('--out') + 1]
s = reset(res=(960, 408), samples=16)
a = Human("A", years=45, weight=0.4, muscle=0.6, height=0.35, eyelashes=None)
pose_sit(a); a.arm.location = (-1.3, 0, -0.5)
b = Human("B", years=45, weight=0.4, muscle=0.6, height=0.35, eyelashes=None)
pose_walk(b, 0.25); b.arm.location = (0, 0, 0)
c = Human("C", years=55, weight=0.0, muscle=0.0, height=0.35, eyelashes=None)
pose_mummy(c); c.arm.location = (1.3, 0, 0)
world_flat((0.3, 0.32, 0.36), 1.0)
k = area_light((-2, -3, 4), (0, 0, 0), 2, 400); point_at(k, (0, 0, 1))
camera((0.6, -6.5, 1.2), (0, 0, 0.85), lens=35)
s.render.filepath = OUT; bpy.ops.render.render(write_still=True)
camera((6.5, -0.4, 1.2), (0, 0, 0.85), lens=35)
s.render.filepath = OUT.replace('.png', '_side.png'); bpy.ops.render.render(write_still=True)
