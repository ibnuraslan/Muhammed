import os, sys
sys.path.insert(0, "/home/user/Muhammed/antwerp_heist/3d/lib"); sys.path.insert(0, "/home/user/Muhammed/antwerp_heist/3d/scenes")
import common as C; C.reset()
import bpy, sf, ph, sets as ST
from mathutils import Vector
sc = C.render_setup(samples=48, noise=0.05, bounces=8)
ST.box("tray", (0, 0, -0.01), (0.8, 0.5, 0.02), ST.velvet("v", (0.15, 0.02, 0.03)))
def put(uid, loc, height=None, width=None, rz=0):
    r, ms = sf.model(uid, loc=(0,0,0), rot_z=rz)
    lo, hi = ph.bounds(ms)
    if width: s = width / max(hi.x - lo.x, hi.y - lo.y)
    else: s = height / (hi.z - lo.z)
    r.scale = (s, s, s); bpy.context.view_layer.update(); lo, hi = ph.bounds(ms)
    r.location = Vector(loc) - Vector(((lo.x+hi.x)/2, (lo.y+hi.y)/2, lo.z))
    return r
put("23603d130e684401be3ed7c482c3076e", (-0.25, 0, 0), width=0.16)
put("87e4e0a9da7f4c8a9561a932d09279bd", (-0.05, 0, 0), width=0.116)
put("0d1ff6b3e6d045cba78889caf7f5bc6e", (0.1, 0.0, 0), width=0.12)
put("5a03949eea904d6989f87aaf5d172722", (0.22, 0.05, 0), width=0.022)
put("378f6df2c4f444399b83db2037258470", (0.22, -0.05, 0), height=0.022)
ST.light_spot("k", (-0.4, -0.6, 0.8), (0, 0, 0), 90, angle=40)
ST.light_area("r", (0.5, 0.5, 0.4), (0, 0, 0), 0.4, 20)
C.camera(Vector((0.0, -0.45, 0.32)), Vector((0, 0, 0.0)), lens=40)
sc.render.filepath = "/home/user/Muhammed/antwerp_heist/3d/out/tests/hero.png"; bpy.ops.render.render(write_still=True)
