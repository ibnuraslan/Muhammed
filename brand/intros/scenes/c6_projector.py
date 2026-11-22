import sys, os, math; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
out = sys.argv[sys.argv.index("--")+1]; spp = int(sys.argv[sys.argv.index("--")+2])
reset(samples=spp)
world((0.005,0.005,0.006), 1.0)
plane("Floor", 30, m=noise_bump(color_noise(mat("Fl", rough=0.5), (0.03,0.02,0.015,1), (0.07,0.05,0.035,1), 3), 40, 0.05))
plane("BackWall", 30, (0, 9.0, 5), (math.radians(90),0,0), m=mat("Wall",(0.04,0.04,0.045,1),0.9))
# the screen shows the projected logo (emissive where the beam lands; slightly soft, warm, flickering bulb)
scr_m, tex = image_mat("Screen")
nt = scr_m.node_tree; p = nt.nodes["Principled BSDF"]
mixc = nt.nodes.new("ShaderNodeMixRGB"); mixc.inputs[1].default_value=(0.55,0.5,0.42,1)
nt.links.new(tex.outputs["Alpha"], mixc.inputs[0]); nt.links.new(tex.outputs["Color"], mixc.inputs[2])
nt.links.new(mixc.outputs[0], p.inputs["Emission Color"]); p.inputs["Base Color"].default_value=(0.01,0.01,0.01,1); p.inputs["Emission Strength"].default_value = 0.9
p.inputs["Alpha"].default_value = 1.0
for l in list(nt.links):
    if l.to_socket == p.inputs["Alpha"]: nt.links.remove(l)
scr = plane("Screen", 1, (0, 8.9, 2.4), (math.radians(90),0,0), scr_m, sx=4.6, sy=4.6*404/1361*1.9)
box("Frame", (4.9, 0.05, 2.9), (0, 8.95, 2.4), mat("Fr",(0.01,0.01,0.01,1),0.9))
# 16mm projector body on a stand in the foreground (silhouette, lit by spill)
metal = mat("Body", (0.05,0.05,0.055,1), 0.35, 0.6)
box("Body", (0.45, 0.35, 0.32), (0.9, -2.0, 1.25), metal, bevel=0.02)
cyl("Lens", 0.07, 0.22, (0.9, -1.75, 1.25), mat("Lens",(0.02,0.02,0.02,1),0.1,0.9), rot=(math.radians(90),0,0))
for z,y in ((1.62,-1.95),(1.62,-2.35)):
    cyl("Reel", 0.28, 0.03, (1.1, y, z), metal, rot=(0,math.radians(90),0))
    cyl("Hub", 0.05, 0.05, (1.1, y, z), metal, rot=(0,math.radians(90),0))
box("Stand", (0.6, 0.5, 1.1), (0.9, -2.1, 0.55), mat("St",(0.03,0.025,0.02,1),0.7))
light('SPOT', "ProjBeam", (0.9, -1.62, 1.25), (0, 8.9, 2.4), energy=150000, color=(1.0,0.9,0.75), spot=26, blend=0.05, size=0.02)
light('POINT', "Lamphouse", (0.9, -2.1, 1.25), energy=3, color=(1,0.6,0.3), size=0.1)
fog("Dust", (12, 14, 6), (0, 3.5, 3), density=0.1, color=(0.9,0.9,0.95), aniso=0.6, noise=1.5)
# rows of cinema seat backs between projector and screen
seat = mat("Seat", (0.08,0.015,0.015,1), 0.8)
for row in range(4):
    for s in range(-6, 7):
        box("seat", (0.48, 0.12, 0.6), (s*0.55, row*1.3 + 1.0, 0.75), seat, bevel=0.04)
camera((2.6, -5.4, 2.1), (0.0, 8.9, 2.0), lens=30, fstop=5.6, focus=8)
render(out)
