"""Concept (b): from high above, the Mary Celeste alone in a pool of light on a vast, dark Atlantic. Her deck is
empty, the boat chocks on the main hatch are empty (the yawl is gone), the rail is open where it was launched,
torn fore-topsails. No people, no text."""
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tcommon as T
T.C.reset()
import bpy
from mathutils import Vector, Matrix
import ship, sea

E = os.environ.get
OUT = E("OUT", os.path.join(T.OUTDIR, "b_alone.png"))
sc = T.res_setup(int(E("SPP", "256")), noise=0.02)

WIND_WORLD = Vector((-0.4, -1.0, 0)).normalized()
MC_HEAD = float(E("HEAD", "32"))
mc = ship.build("MC", sails="found", rail_gap=(-2.7, -0.6, "S"),
                wind=Matrix.Rotation(math.radians(-MC_HEAD), 3, 'Z') @ WIND_WORLD, wet=0.85, detail=True, bow_wave_h=0.4)
mc["root"].location = (0, 0, -0.7)
mc["root"].rotation_euler = (math.radians(-5.0), math.radians(1.5), math.radians(MC_HEAD))
bpy.context.view_layer.update()

water = sea.water_material(deep=(0.0005, 0.007, 0.012), crest=(0.003, 0.04, 0.045), fog_color=(0.05, 0.06, 0.07))
sea.ocean(size=200, res=int(E("OCEAN_RES", "11")), scale=3.0, chop=1.9, wind=16.0, repeat=3, foam=float(E("FOAM", "0.15")), mat=water,
          direction=math.degrees(math.atan2(WIND_WORLD.y, WIND_WORLD.x)), hulls=(mc["hull"],), loc=(0, 0, 0), seed=5)
sea.far_sea(300, mat=water, center=(0, 0))

# a dim storm sky (only the sea's reflections see it), a weak cool sun, and the break in the cloud: a big soft spot
rot, el = T.sky_with_sun_at(E("SKY", "kloofendal_overcast_puresky"), 200, strength=float(E("SKY_K", "0.06")))
T.sun(200, 20, energy=float(E("SUN_E", "0.05")), color=(0.75, 0.85, 1.0), angle=3)
T.shaft((float(E("SPX", "-60")), float(E("SPY", "90")), 300), (0, 0, 0), float(E("SPOT_E", "8e6")), float(E("SPOT_DEG", "18")),
        haze=float(E("HAZE", "0.01")), color=(1.0, 0.86, 0.66), soft=6.0)
T.lights_skip_haze()

cam_loc = Vector((float(E("CX", "-20")), float(E("CY", "-80")), float(E("CZ", "75"))))
tgt = Vector((float(E("TX", "2")), float(E("TY", "0")), 3))
T.C.camera(cam_loc, tgt, lens=float(E("LENS", "40")), fstop=8, focus=(tgt - cam_loc).length, roll=float(E("ROLL", "0")))
T.C.finish(OUT, cine={"sat": 1.1, "exposure": float(E("EXPO", "0.0")), "contrast": 1.12}, bloom=0.4)
print("RENDERED", OUT)
