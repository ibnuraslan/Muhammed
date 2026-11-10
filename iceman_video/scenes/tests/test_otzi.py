import sys, os, math, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import bpy
from mathutils import Vector
from common import *
from human import pose_sit
from otzi import build_otzi
OUT = sys.argv[sys.argv.index('--out') + 1]
s = reset(res=(960, 408), samples=int(sys.argv[sys.argv.index('--samples') + 1]) if '--samples' in sys.argv else 32)
t0 = time.time()
h = build_otzi(hair_density=float(sys.argv[sys.argv.index('--density') + 1]) if '--density' in sys.argv else 1.0)
pose_sit(h); h.arm.location = (0, 0, -0.45)
print("build", time.time() - t0)
world_flat((0.01, 0.015, 0.03), 1.0)
fd = bpy.data.lights.new("Fire", 'POINT'); fd.energy = 25; fd.color = (1.0, 0.45, 0.15); fd.shadow_soft_size = 0.2
f = bpy.data.objects.new("Fire", fd); bpy.context.collection.objects.link(f); f.location = (0.05, -0.75, 0.25)
rim = area_light((-0.8, 1.2, 1.6), (0, 0, 0), 1.0, 30, (0.4, 0.6, 1.0)); point_at(rim, (0, 0, 0.9))
head = h.bone_head("head")
view = sys.argv[sys.argv.index('--view') + 1] if '--view' in sys.argv else 'face'
if view == 'face':
    eye = (h.eyes[0].matrix_world.to_translation() + h.eyes[1].matrix_world.to_translation()) / 2
    camera(tuple(eye + Vector((0.35, -0.75, -0.06))), tuple(eye + Vector((0, 0, -0.04))), lens=60)
else:
    camera((1.3, -2.2, 0.9), (0, 0, 0.55), lens=40)
s.render.filepath = OUT; bpy.ops.render.render(write_still=True)
print("total", time.time() - t0)
