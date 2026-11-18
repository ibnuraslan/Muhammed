import os, sys, math
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
import p4
p4.C.reset()
import bpy
from mathutils import Vector
import terrain as T, ship
sc = p4.C.render_setup(samples=48, noise=0.03, bounces=6)
BBOX = (-31.6, 35.2, -15.4, 40.6)
e, lons, lats = T.grid(*BBOX, zoom=7, out_w=900)
print("GRID", e.shape, e.min(), e.max())
SX = 2.2; SY = SX * e.shape[0] / e.shape[1]
o = T.relief_mesh("map", e, SX, SY, land_k=1.2e-5, sea_k=2.4e-6, mat=T.map_material(), skirt=0.03)
o.location.z = 0.8
p4.world_color((0.02, 0.012, 0.008))
p4.light('SPOT', "lamp", 260, (1.0, 0.75, 0.5), loc=(0.4, 0.5, 2.2), target=(0.2, 0, 0.8), size=0.15, spot=70, blend=0.6)
cam = p4.C.camera((0.9, -1.9, 1.95), (0.3, 0.05, 0.8), lens=40, fstop=4, focus=2.3)
p4.C.finish(os.environ.get("OUT", "/tmp/t/map.png"), cine={"sat": 1.0, "exposure": 0.0})
