import sys, os, math
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import bpy
from mathutils import Vector
from common import *
from human import *
from mummy import build_mummy
OUT = sys.argv[sys.argv.index('--out') + 1]
s = reset(res=(960, 408), samples=int(sys.argv[sys.argv.index('--samples') + 1]) if '--samples' in sys.argv else 24)
h = build_mummy()
lay_down(h, face_up=True, z=0.11)
bpy.ops.mesh.primitive_plane_add(size=4, location=(0, 0.8, 0)); 
world_flat((0.04, 0.05, 0.07), 1.0)
k = area_light((0.6, 0.8, 2.0), (0, 0, 0), 1.5, 80, (0.85, 0.92, 1.0)); point_at(k, (0, 0.9, 0.1))
r = area_light((-1.5, 2.2, 0.6), (0, 0, 0), 1.0, 40, (0.6, 0.75, 1.0)); point_at(r, (0, 1.3, 0.15))
head = h.bone_head("head")
view = sys.argv[sys.argv.index('--view') + 1] if '--view' in sys.argv else 'face'
if view == 'face':
    camera(tuple(head + Vector((0.35, 0.10, 0.32))), tuple(head + Vector((0, 0.02, 0.05))), lens=55)
else:
    camera((1.6, -0.6, 1.3), (0, 0.85, 0.1), lens=35)
s.render.filepath = OUT; bpy.ops.render.render(write_still=True)
