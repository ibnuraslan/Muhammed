"""Shot 1 - Dawn aerial drift over the Ötztal Alps above a sea of clouds."""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import bpy
from common import *
from terrain import eroded_alpine

arg = lambda k, d: type(d)(sys.argv[sys.argv.index(k) + 1]) if k in sys.argv else d
OUT = arg('--out', '/tmp/shot1'); FRAMES = arg('--frames', 1); STEP = arg('--step', 1)

s = reset(samples=arg('--samples', 40), exposure=-1.2)
SIZE = 16000.0; ZS = 3000.0
h = eroded_alpine(1024, seed=21, peak_bias=[(0.56, 0.50, 0.10, 0.9), (0.62, 0.38, 0.07, 0.5)])
terr = grid_mesh("Terrain", h, SIZE, SIZE, ZS)
mat = snow_rock_material(snow_thresh=0.60, fog_color=(0.50, 0.52, 0.62), fog_density=0.00004, fog_max=0.8,
                         bump_scale=40, rock_col=(0.022, 0.022, 0.024), snow_col=(0.80, 0.83, 0.90))
terr.data.materials.append(mat)

world_sky(sun_elev_deg=3.5, sun_rot_deg=200, strength=0.6, tint=(0.95, 0.97, 1.0), aerosol=1.5)
sun(3.5, 290, energy=5.0, color=(1.0, 0.70, 0.48), angle_deg=1.0)
clouds, noise = cloud_volume("Clouds", (0, 0, 900), (SIZE / 2, SIZE / 2, 500), density=0.02,
                             color=(1.0, 0.97, 0.97), anisotropy=0.75, top_soft=0.6)
noise.inputs['Scale'].default_value = 6.0

cam = camera((0, 0, 0), (0, 0, 0), lens=30)

def frame(i, t):
    cam.location = lerp((-2600, -7200, 3200), (-1700, -6000, 3050), t)
    point_at(cam, lerp((-300, 900, 2100), (100, 1200, 2150), t))
    noise.inputs['W'].default_value = t * 0.15

render_frames(OUT, frame, FRAMES, STEP)
