import os, sys, math
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "p2lib"))
import env
import common as C
C.reset()
import bpy
from mathutils import Vector, Matrix
import cast, poses as P
sc = C.render_setup(samples=64, noise=0.05)
sc.render.resolution_x, sc.render.resolution_y = 1600, 900
WHO = os.environ.get("WHO", "Briggs,Sarah,Child,Sailor").split(",")
xs = [(-1.2 + 0.8 * i) for i in range(len(WHO))]
for i, w in enumerate(WHO):
    p = getattr(cast, w)()
    P.stand(p.h, weight="L"); P.arm_down(p.h, "L"); P.arm_down(p.h, "R")
    P.rest_hand(p.h, "L"); P.rest_hand(p.h, "R")
    p.finish_live(look_at=(0, -4, 1.5), place=Matrix.Translation((xs[i], 0, 0)), density=0.5)
w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (0.3, 0.22, 0.16, 1)
w.node_tree.nodes["Background"].inputs[1].default_value = 0.5
l = bpy.data.lights.new("key", 'AREA'); l.energy = 900; l.size = 2; l.color = (1, 0.85, 0.7)
o = bpy.data.objects.new("key", l); sc.collection.objects.link(o); o.location = (-2.5, -3, 3)
o.rotation_euler = (Vector((0, 0, 1)) - o.location).to_track_quat('-Z', 'Y').to_euler()
fl = bpy.data.objects.new("fl", bpy.data.meshes.new("fl")); sc.collection.objects.link(fl)
fl.data.from_pydata([(-5, -5, 0), (5, -5, 0), (5, 5, 0), (-5, 5, 0)], [], [[0, 1, 2, 3]])
Y = float(os.environ.get("CZ", "1.1"))
C.camera((0, -4.2, Y + 0.3), (0, 0, Y), lens=float(os.environ.get("LENS", "40")))

from bpy_extras.object_utils import world_to_camera_view
cam = sc.camera; dg = bpy.context.evaluated_depsgraph_get()
fr = cam.data.view_frame(scene=sc)  # tr, br, bl, tl in cam space
for (px, py) in [(100, 820), (180, 720), (250, 580)]:
    u = px / 1600; v = 1 - py / 900
    tl, tr, br, bl = fr[3], fr[0], fr[1], fr[2]
    p = bl + (br - bl) * u + (tl - bl) * v
    d = (cam.matrix_world.to_3x3() @ p).normalized()
    hit = sc.ray_cast(dg, cam.matrix_world.translation, d)
    print("HIT", px, py, hit[0], hit[4].name if hit[4] else None, tuple(round(c, 2) for c in hit[1]))
import numpy as np
for o in bpy.data.objects:
    if o.type == 'CURVES':
        cv = o.data; n = len(cv.points)
        P = np.zeros(n * 3, np.float32); cv.position_data.foreach_get("vector", P); P = P.reshape(-1, 3)
        print("CV", o.name, n, P.min(0).round(2), P.max(0).round(2), "far", int((P[:, 2] < 1.3).sum()))
        sz = np.array([c.points_length for c in cv.curves]) if hasattr(cv.curves[0], 'points_length') else None
        print("CV2", o.name, sz.min() if sz is not None else None, sz.max() if sz is not None else None)
for o in bpy.data.objects:
    if o.type not in ('MESH','CURVES') or 'button' not in o.name:
        print("ALL", o.name, o.type, tuple(round(c,2) for c in o.matrix_world.translation), o.hide_render)
