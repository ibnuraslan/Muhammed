"""(a) 4 December 1872, shortly after noon. From the bow of the Dei Gratia, the Mary Celeste off the starboard
bow: open Atlantic, a breaking sea, torn wet sails, nobody at her wheel."""
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C
C.reset()
import bpy
from mathutils import Vector, Matrix
import ship, sea

OUT = os.environ.get("OUT", os.path.join(C.HERE, "..", "out", "frames", "a_sighting.png"))
sc = C.render_setup(samples=int(os.environ.get("SPP", "192")), noise=0.02)

WIND_WORLD = Vector((0.3, -1.0, 0)).normalized()            # the wind blows toward -Y (from the north-ish)

def local_wind(heading_deg):
    return Matrix.Rotation(math.radians(-heading_deg), 3, 'Z') @ WIND_WORLD

# --- the Dei Gratia (we stand on her foredeck), heading +X, heeled a little to starboard
dg = ship.build("DG", sails="full", rail_gap=None, wind=local_wind(0), hatches_off=False, boat_chocks=True, wet=0.7)
dg["root"].rotation_euler = (math.radians(-4.0), math.radians(1.5), 0)
dg["root"].location = (0, 0, -0.15)

# --- the Mary Celeste, about 230 m off the starboard bow, yawing with her sails half gone
MC_HEAD = 128.0
mc = ship.build("MC", sails="found", rail_gap=(-2.7, -0.6, "S"), wind=local_wind(MC_HEAD), wet=0.8, detail=False, bow_wave_h=1.0)
mc_pos = Vector((100.0, -66.0, 0))
mc["root"].location = mc_pos + Vector((0, 0, -0.1))
mc["root"].rotation_euler = (math.radians(7.0), math.radians(-2.5), math.radians(MC_HEAD))

bpy.context.view_layer.update()

# --- sea and sky
water = sea.water_material()
oc = sea.ocean(size=260, res=int(os.environ.get("OCEAN_RES", "26")), scale=4.6, chop=2.2, wind=18.0, repeat=3,
               foam=0.55, mat=water, direction=math.degrees(math.atan2(WIND_WORLD.y, WIND_WORLD.x)),
               hulls=(dg["hull"], mc["hull"]), loc=(100, -60, 0))
sea.far_sea(380, mat=water, center=(100, -60))
sea.sky(strength=float(os.environ.get("SKY_K", "0.72")), rot_deg=float(os.environ.get("SKY_ROT", "240")))
sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", 'SUN')); sc.collection.objects.link(sun)
sun.data.energy = 1.1; sun.data.angle = math.radians(4); sun.data.color = (1.0, 0.93, 0.84)
az, el = math.radians(139.0 + float(os.environ.get("SKY_ROT", "240"))), math.radians(30)
sun.rotation_euler = (Vector((math.cos(az) * math.cos(el), math.sin(az) * math.cos(el), math.sin(el))) * -1).to_track_quat('-Z', 'Y').to_euler()


# white water thrown off the Mary Celeste's bow as she falls off a sea
bow = mc["root"].matrix_world @ Vector((ship.L / 2 - 1.5, -1.5, 0.4))
fwd = (mc["root"].matrix_world.to_3x3() @ Vector((1, -0.6, 0))).normalized()
sea.spray("MC_spray", bow, (1.4, 1.0, 6.0), count=14000, rmin=0.01, rmax=0.045, up=3.2, dirv=fwd)
sea.mist_puff("MC_mist", bow + fwd * 2.0 + Vector((0, 0, 0.8)), (3.5, 2.4, 1.3), density=0.25, seed=2)
# and off our own bow, close to camera (out of focus)
dbow = dg["root"].matrix_world @ Vector((ship.L / 2 + 0.6, -2.6, 0.2))


# --- camera: on the Dei Gratia's starboard bow, eye height, looking out over the rail
cam_loc = dg["root"].matrix_world @ Vector((3.2, -2.75, ship.zdeck(3.2) + 1.74))
tgt = mc_pos + Vector((-4, 0, 17.0))
cam = C.camera(cam_loc, tgt, lens=50, fstop=4.0, focus=(mc_pos - cam_loc).length, roll=-2.0)

C.finish(OUT, cine={"sat": 1.2, "exposure": -0.15, "warm": (1.03, 1.0, 0.97)})
print("RENDERED", OUT)
