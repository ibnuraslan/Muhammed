import sys, os, math; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
out = sys.argv[sys.argv.index("--")+1]; spp = int(sys.argv[sys.argv.index("--")+2])
reset(samples=spp)
world((0.01,0.015,0.025), 1.0)
ground = plane("Ground", 80, m=noise_bump(color_noise(mat("Conc", rough=0.3), (0.03,0.03,0.03,1), (0.09,0.09,0.085,1), 3), 25, 0.3, (0.08, 0.6)))
lg = logo(width=5.0, depth=0.35, loc=(0, 0, 0.82), fill_mat=mat("F", YEL, 0.4), edge_mat=mat("E", (0.015,0.015,0.012,1), 0.35))
# perimeter fence behind: concrete posts with wires
post = mat("Post", (0.05,0.05,0.05,1), 0.8)
for i in range(-9, 10):
    cyl("p", 0.06, 4.2, (i*2.0, 7, 2.1), post, verts=8)
for k in range(6):
    cyl("w", 0.006, 40, (0, 7, 1.0+k*0.6), post, rot=(0, math.radians(90), 0), verts=6)
# watchtower silhouettes
for x in (-14, 13):
    box("tw", (2.2, 2.2, 0.2), (x, 10, 9), post); cyl("leg", 0.12, 9, (x, 10, 4.5), post, verts=8)
fog("Fog", (60, 60, 14), (0, 0, 7), density=0.035, color=(0.75,0.82,0.95), aniso=0.45, noise=0.25)
# searchlights from the towers, all locked on the logo; one still sweeping
light('SPOT', "S1", (-13, 8.3, 9.6), (0.2, 0, 1.3), energy=90000, color=(0.85,0.92,1.0), spot=7, blend=0.25, size=0.3)
light('SPOT', "S2", (12, 8.3, 9.6), (-0.3, 0, 1.2), energy=90000, color=(0.85,0.92,1.0), spot=7, blend=0.25, size=0.3)
light('SPOT', "S3", (3, 14, 12), (-8, -6, 0), energy=40000, color=(0.85,0.92,1.0), spot=5, blend=0.2, size=0.3)
light('SPOT', "Key", (0, -12, 8), (0, 0, 1), energy=3000, color=(0.9,0.95,1.0), spot=12, blend=0.4, size=0.5)
camera((0.7, -8.5, 0.7), (0, 0, 2.3), lens=28)
render(out)
