"""Look-dev test: portrait of the procedural human."""
import sys, os, math
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import bpy
from mathutils import Vector
from common import *
from human import Human
OUT = sys.argv[sys.argv.index('--out') + 1]
s = reset(res=(960, 408), samples=int(sys.argv[sys.argv.index('--samples') + 1]) if '--samples' in sys.argv else 32)
h = Human("Otzi", gender=1.0, years=45, muscle=0.6, weight=0.4, height=0.35)
head = h.bone_head("head"); print("head at", head, "height", max(v.co.z for v in h.body.data.vertices))
world_flat((0.05, 0.06, 0.08), 1.0)
area_light((-1.2, -1.5, 2.2), (0, 0, 0), 1.2, 120, (1, 0.95, 0.9)); bpy.data.objects['Area'].rotation_euler = (0, 0, 0)
point_at(bpy.data.objects['Area'], tuple(head))
fill = area_light((1.5, -1.0, 1.6), (0, 0, 0), 1.5, 25, (0.6, 0.75, 1.0)); point_at(fill, tuple(head))
which = sys.argv[sys.argv.index('--view') + 1] if '--view' in sys.argv else 'face'
if which == 'face':
    cam = camera(tuple(head + Vector((0.25, -0.75, 0.05))), tuple(head + Vector((0, 0, 0.05))), lens=85)
else:
    cam = camera((1.2, -4.0, 1.1), (0, 0, 0.9), lens=40)
s.render.filepath = OUT; bpy.ops.render.render(write_still=True)
