"""lights per set + render settings. blender -b anim.blend --python 04_lights.py -- out.blend"""
import bpy, sys, math
from mathutils import Vector
OUT = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene; R_ = math.radians
def L(name, kind, loc, energy, size=1.0, rot=None, target=None, color=(1, 1, 1)):
    d = bpy.data.lights.new(name, kind); d.energy = energy; d.color = color
    if kind == 'AREA': d.size = size
    if kind == 'SUN': d.angle = R_(8)
    o = bpy.data.objects.new(name, d); sc.collection.objects.link(o); o.location = loc
    if target is not None: o.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    elif rot: o.rotation_euler = rot
    return o
# workshop: warm daylight from the window side + big soft fills (faces lit, shadows lifted)
L("WorkSun", 'SUN', (0, 3, 4), 2.2, rot=(R_(-40), R_(10), R_(160)), color=(1.0, 0.95, 0.88))
L("WorkKey", 'AREA', (-1.2, -1.8, 2.4), 260, 2.0, target=(-0.2, -0.2, 1.0), color=(1.0, 0.94, 0.86))
L("WorkFill", 'AREA', (1.6, -1.5, 1.8), 140, 2.5, target=(-0.2, -0.3, 1.0), color=(0.92, 0.95, 1.0))
L("WorkTop", 'AREA', (0, -0.3, 2.9), 220, 2.5, target=(0, -0.3, 0.8))
L("WorkBack", 'AREA', (0.5, 1.6, 2.6), 120, 2.0, target=(-0.3, 0.0, 1.2))
# warehouse
L("StoreTop", 'AREA', (40, 0.3, 3.4), 900, 5.0, target=(40, 0.3, 0))
L("StoreKey", 'AREA', (38.5, -2.5, 2.5), 300, 3.0, target=(40, 0.3, 0.3))
# park: sun handled by the sky world strength + a sun
L("ParkSun", 'SUN', (80, -3, 5), 3.2, rot=(R_(50), R_(-15), R_(-25)), color=(1.0, 0.96, 0.9))
L("ParkFill", 'AREA', (79.2, -1.6, 1.6), 60, 1.5, target=(79.9, -0.05, 0.6))
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = 48; sc.cycles.adaptive_threshold = 0.05
sc.cycles.use_denoising = True; sc.render.resolution_x, sc.render.resolution_y = 1080, 1920; sc.render.fps = 60
sc.render.use_motion_blur = False
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True); print("LIGHTS_OK")
