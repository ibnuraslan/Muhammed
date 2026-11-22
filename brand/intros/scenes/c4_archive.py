import sys, os, math; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
out = sys.argv[sys.argv.index("--")+1]; spp = int(sys.argv[sys.argv.index("--")+2])
reset(samples=spp)
world((0.01,0.01,0.012), 1.0)
floor = plane("Floor", 30, m=noise_bump(color_noise(mat("Fl", rough=0.6), (0.05,0.045,0.04,1), (0.1,0.09,0.08,1), 4), 20, 0.1))
steel = mat("Steel", (0.18,0.19,0.2,1), 0.55, 0.8)
card = color_noise(mat("Card", rough=0.85), (0.22,0.16,0.09,1), (0.32,0.24,0.14,1), 15)
label = mat("Label", (0.7,0.66,0.55,1), 0.8)
for side in (-1, 1):
    x0 = side * 1.1
    for k in range(5):
        box("shelf", (0.6, 14, 0.03), (x0, 4, 0.25 + k*0.55), steel)
        for j in range(26):
            y = -2.6 + j*0.5
            if side == -1 and k == 2 and j == 2: continue
            box("bx", (0.42, 0.4, 0.3), (x0 - side*0.05, y, 0.42 + k*0.55), card, bevel=0.01)
            box("lab", (0.003, 0.18, 0.08), (x0 - side*0.265, y, 0.42 + k*0.55), label)
    for j in range(8):
        for yy in (-0.3, 0.3):
            box("up", (0.03, 0.03, 2.8), (x0 + yy*0.0 + side*0.3*(1 if yy>0 else -1), -2.8 + j*2, 1.4), steel)
# the pulled box, half out of the shelf, lid with the brand plate
bx = box("Pulled", (0.42, 0.4, 0.3), (-0.62, -1.6, 1.52), card, rot=(0,0,math.radians(8)), bevel=0.01)
lg = logo(width=0.36, depth=0.006, loc=(-0.405, -1.57, 1.53), rot=(math.radians(90), 0, math.radians(98)),
          fill_mat=mat("Brass", (0.75,0.55,0.15,1), 0.3, 1.0), edge_mat=mat("E",(0.03,0.025,0.02,1),0.5))
# light shaft from a high window at the end of the aisle
light('SPOT', "Shaft", (0.6, 6, 4.2), (-0.5, -1.6, 1.55), energy=9000, color=(1.0,0.85,0.6), spot=9, blend=0.3, size=0.05)
light('AREA', "Amb", (0, 2, 3.2), (0,2,0), energy=8, color=(0.5,0.6,0.8), size=2)
fog("Haze", (4, 18, 4), (0, 3, 2), density=0.05, color=(1,0.95,0.85), aniso=0.6)
# dust motes kicked off the lid
dm = mat("Mote", (1,1,1,1), 0.5, emit=(1,0.9,0.7,1), estr=0.6)
def mote(i, rnd):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=rnd.uniform(0.0008,0.002),
        location=(-0.45 + rnd.gauss(0,0.12), -1.55 + rnd.gauss(0,0.25), 1.72 + abs(rnd.gauss(0,0.25))))
    bpy.context.active_object.data.materials.append(dm)
scatter(300, mote, 3)
camera((0.55, -2.55, 1.72), (-0.42, -1.57, 1.55), lens=35, fstop=2.8)
render(out)
