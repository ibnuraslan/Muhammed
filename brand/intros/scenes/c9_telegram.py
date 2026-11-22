import sys, os, math; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
out = sys.argv[sys.argv.index("--")+1]; spp = int(sys.argv[sys.argv.index("--")+2])
reset(samples=spp)
world((0.01,0.008,0.006), 0.5)
plane("Desk", 4, m=noise_bump(color_noise(mat("Wood", rough=0.4), (0.04,0.018,0.008,1), (0.12,0.055,0.025,1), 3), 50, 0.05))
form = color_noise(mat("Form", rough=0.85), (0.42,0.33,0.17,1), (0.5,0.4,0.22,1), 30)
box("Form", (0.62, 0.42, 0.002), (0, 0, 0.001), form, rot=(0,0,math.radians(3)))
ink = mat("Ink", (0.04,0.035,0.03,1), 0.7); red=mat("Red",(0.3,0.02,0.02,1),0.6)
mono = "/usr/share/fonts/truetype/freefont/FreeMonoBold.ttf"; serif="/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
R=(0,0,math.radians(3))
text("TELEGRAM", 0.05, (0, 0.165, 0.0022), R, red, serif)
text("NO. 1104      RECEIVED  22 NOV      CHECK  21 WDS", 0.012, (0, 0.12, 0.0022), R, ink, mono)
strip = mat("Strip", (0.85,0.82,0.72,1), 0.8)
lines = ["VIEWER DISCRETION ADVISED STOP", "WHAT FOLLOWS IS REAL STOP", "NAMES DATES AND PLACES ARE TRUE STOP", "SOME IMAGES MAY DISTURB STOP"]
for i, l in enumerate(lines):
    y = 0.06 - i*0.045
    box("strip%d"%i, (0.022*len(l)*0.55+0.02, 0.026, 0.0006), (math.sin(R[2])*-y, y, 0.0025), strip, rot=R)
    text(l, 0.017, (math.sin(R[2])*-y, y, 0.0029), R, ink, mono)
# brass paperweight and a pencil on the form edge, lamp light
cyl("Weight", 0.05, 0.03, (0.32, -0.2, 0.015), mat("Brass",(0.7,0.5,0.15,1),0.3,1.0))
cyl("Pencil", 0.005, 0.18, (-0.33, -0.17, 0.006), mat("Pn",(0.6,0.45,0.05,1),0.5), rot=(0,math.radians(90),math.radians(25)), verts=6)
light('SPOT', "Lamp", (-0.5, 0.45, 0.9), (0,0,0), energy=45, color=(1.0,0.78,0.5), spot=45, blend=0.7, size=0.05)
light('AREA', "Fill", (0.8,-0.8,0.6), (0,0,0), energy=3, color=(0.6,0.7,1.0), size=1)
camera((0.05, -0.62, 0.52), (0, -0.01, 0), lens=45, fstop=3.5)
render(out)
