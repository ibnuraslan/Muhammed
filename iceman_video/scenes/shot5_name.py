"""Shot 5 - Title: 'ÖTZI' pressed deep into the glacier snow, seen from above at night."""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import bpy
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from common import *
from terrain import fbm

arg = lambda k, d: type(d)(sys.argv[sys.argv.index(k) + 1]) if k in sys.argv else d
OUT = arg('--out', '/tmp/shot5'); FRAMES = arg('--frames', 1); STEP = arg('--step', 1)
s = reset(samples=arg('--samples', 32), exposure=-0.4)

W, Hh = 7.0, 4.2                      # metres (large enough that the rising camera never sees an edge)
NX, NY = 2625, 1575                   # 375 samples per metre
# --- letter mask
img = Image.new("L", (NX, NY), 0); d = ImageDraw.Draw(img)
font = ImageFont.truetype("/usr/share/fonts/opentype/inter/InterDisplay-Bold.otf", 470)
txt = "ÖTZI"
bb = d.textbbox((0, 0), txt, font=font)
d.text(((NX - (bb[2] - bb[0])) / 2 - bb[0], (NY - (bb[3] - bb[1])) / 2 - bb[1]), txt, fill=255, font=font)
mask = np.asarray(img, np.float32) / 255
soft = np.asarray(img.filter(ImageFilter.GaussianBlur(9)), np.float32) / 255
wide = np.asarray(img.filter(ImageFilter.GaussianBlur(26)), np.float32) / 255
# erode edges irregularly (hand-dug / wind-softened)
yy, xx = np.mgrid[0:NY, 0:NX]
edge_noise = fbm((NY, NX), 41, 5, 30.0)
carve = np.clip((soft - 0.5 + edge_noise * 0.22) * 3 + 0.5, 0, 1)
carve = np.asarray(Image.fromarray((carve * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(3)), np.float32) / 255
rim = np.clip(wide - soft, 0, 1) * (0.7 + 0.6 * fbm((NY, NX), 43, 4, 12.0))

base = fbm((NY, NX), 3, 6, 1.5) * 0.06 + fbm((NY, NX), 7, 5, 12.0) * 0.008
lumps = np.maximum(fbm((NY, NX), 17, 5, 30.0), 0) ** 1.5 * 0.012
warp = fbm((NY, NX), 23, 5, 2.5) * 0.25
X = xx / NX * W; Y = yy / NY * Hh
ripples = (np.sin((X * 0.7 + Y * 0.7 + warp) * 2 * np.pi * 14) * 0.5 + 0.5) ** 2 * 0.0012 * np.clip(fbm((NY, NX), 29, 3, 2.0) + 0.6, 0, 1.5)
grain = fbm((NY, NX), 13, 4, 90.0) * 0.0015
# fresh snowfall partially re-filling the trench bottom
fill = np.clip(fbm((NY, NX), 51, 4, 6.0) * 0.5 + 0.5, 0, 1) * 0.025
H = base + lumps + ripples + grain + rim * 0.035 - carve * (0.11 - fill)
ground = grid_mesh("Snow", H[::-1].astype(np.float32), W, Hh, 1.0)
ground.data.materials.append(snow_material(scale=1.6, glint=0.988))

# --- lighting: cold moonlight raking low across the letters, deep blue sky fill
world_flat((0.010, 0.018, 0.045), 1.0)
moon = sun(22, 155, energy=1.6, color=(0.62, 0.75, 1.0), angle_deg=1.5)
lamp = area_light((-2.5, -1.8, 1.2), (0, 0, 0), 1.0, 25, (1.0, 0.55, 0.25)); point_at(lamp, (0, 0, 0))

cam = camera((0, 0, 0), (0, 0, 0), lens=35)

def frame(i, t):
    e = ease(t)
    a = math.radians(-92 + 10 * e)
    r = 0.35 + 0.2 * e
    z = 3.7 + 1.1 * e
    cam.location = (math.cos(a) * r, math.sin(a) * r, z)
    point_at(cam, (0.0, 0.05, 0))
    cam.rotation_euler.rotate_axis('Z', math.radians(-6 + 8 * e))
    lamp.data.energy = 25 * (1 + 0.15 * math.sin(i * 1.3) + 0.1 * math.sin(i * 3.7))

render_frames(OUT, frame, FRAMES, STEP)
