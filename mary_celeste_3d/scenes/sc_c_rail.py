"""(c) Back on deck: a section of the railing has been taken out and laid flat. The gap is wide enough to launch
a small boat; the boat's chocks on the main hatch are empty. Deveau stands at the gap, looking at it.
The Dei Gratia lies hove-to in the distance."""
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C
C.reset()
import bpy
from mathutils import Vector, Matrix
import ship, sea, poses as P
import human as H, deveau as D

OUT = os.environ.get("OUT", os.path.join(C.HERE, "..", "out", "frames", "c_rail.png"))
sc = C.render_setup(samples=int(os.environ.get("SPP", "224")), noise=0.02)

WIND_WORLD = Vector((0.3, -1.0, 0)).normalized()
def local_wind(hd):
    return Matrix.Rotation(math.radians(-hd), 3, 'Z') @ WIND_WORLD

GAP = (-2.7, -0.6, "S")
HEEL = 2.5
mc = ship.build("MC", sails="found", rail_gap=GAP, wind=local_wind(0), wet=0.8, detail=True)
R = Matrix.Rotation(math.radians(-HEEL), 4, 'X')            # heeled a little to starboard
mc["root"].matrix_world = R
bpy.context.view_layer.update()
SHIP = mc["root"].matrix_world.copy()

# the Dei Gratia, hove-to some 400 m off
DG_HEAD = 205.0
dg = ship.build("DG", sails="full", wind=local_wind(DG_HEAD), wet=0.6, detail=False, hatches_off=False)
dg["root"].location = (-330.0, -300.0, -0.1); dg["root"].rotation_euler = (math.radians(3), 0, math.radians(DG_HEAD))
bpy.context.view_layer.update()

water = sea.water_material()
sea.ocean(size=240, res=int(os.environ.get("OCEAN_RES", "24")), scale=2.4, chop=1.7, wind=15.0, repeat=3, foam=0.38, mat=water,
          direction=math.degrees(math.atan2(WIND_WORLD.y, WIND_WORLD.x)), hulls=(mc["hull"], dg["hull"]),
          loc=(-150, -150, 0), cut=(0.0, 0.0, ship.L / 2 - 0.4, ship.B / 2 - 0.15))
sea.far_sea(370, mat=water, center=(-150, -150))
sea.sky(strength=float(os.environ.get("SKY_K", "0.72")), rot_deg=float(os.environ.get("SKY_ROT", "255")))
sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", 'SUN')); sc.collection.objects.link(sun)
sun.data.energy = 1.4; sun.data.angle = math.radians(5); sun.data.color = (1.0, 0.94, 0.86)
az, el = math.radians(139.0 + float(os.environ.get("SKY_ROT", "255"))), math.radians(30)
sun.rotation_euler = (Vector((math.cos(az) * math.cos(el), math.sin(az) * math.cos(el), math.sin(el))) * -1).to_track_quat('-Z', 'Y').to_euler()

# a coil of rope and a bucket left by the gap (the ship as found: things lie where they were dropped)
import ph
bk, _ = ph.model("wooden_bucket_01")
bk.matrix_world = SHIP @ Matrix.Translation((-4.6, -1.9, ship.zdeck(-4.6) + 0.005)) @ Matrix.Rotation(0.5, 4, 'Z')
def coil(name, c, r0=0.22, turns=7, rr=0.016):
    pts = []
    for k in range(turns * 24 + 1):
        a = k / 24 * 2 * math.pi; r = r0 - 0.02 * (k / 24) / turns * turns * 0.25
        pts.append(SHIP @ Vector((c[0] + r * math.cos(a), c[1] + r * math.sin(a), c[2] + rr + 0.0005 * k / 24 * 0 + rr * 1.9 * (k // 24 % 2) * 0)))
    return ship.rope(name, pts, rr, mc["mats"]["rope"])
for k in range(3):
    coil(f"coil{k}", (0.9, -3.2, ship.zdeck(0.9) + 0.012 + k * 0.03), r0=0.26 - k * 0.025)

# ----------------------------------------------------------------------------- Deveau at the gap
dv = D.Deveau(wet=0.5)
h = dv.h
POS = Vector((-3.45, -3.05, 0.0))
ANG = math.radians(-35)                      # facing forward and outboard, toward the gap
zd = ship.zdeck(POS.x) + 0.006
Mloc = Matrix.Translation((POS.x, POS.y, zd)) @ Matrix.Rotation(ANG - math.radians(-90), 4, 'Z')
M = SHIP @ Mloc
Mi = M.inverted()
P.stand(h, lean=6, weight="R", twist=-3)
P.head(h, pitch=22, yaw=10, tilt=2)
dv.lids(0.7); dv.brow_knit(0.8)
# right hand on the cap rail where the bulwark ends at the gap; left arm hangs
cap = SHIP @ Vector((GAP[0] - 0.22, -(ship.half_breadth((GAP[0] + ship.L / 2) / ship.L, 1.0) - 0.03), ship.zdeck(GAP[0]) + ship.RAIL_H + 0.07 + 0.03))
P.hand_reach(h, "R", Mi @ cap, elbow=(-0.8, 0.4, -0.5))
h.aim("wrist.R", (Mi.to_3x3() @ Vector((0.35, -0.2, -0.85))).normalized())
P.rest_hand(h, "R", curl=26)
P.arm_down(h, "L", out=0.1, fwd=0.02, bend=14)
P.rest_hand(h, "L", curl=24)
look = SHIP @ Vector((-1.4, -2.9, ship.zdeck(-1.4)))
dv.finish(look_at=look, place=M, density=float(os.environ.get("HAIR", "1.0")))

# ----------------------------------------------------------------------------- camera
cam_loc = SHIP @ Vector((0.62, -1.25, ship.zdeck(0.62) + 1.66))
head_w = M @ Vector((0, -0.08, 1.64))
aim = head_w.lerp(SHIP @ Vector((-1.4, -3.0, ship.zdeck(-1.4))), 0.6) + Vector((0, 0, 0.42))
cam = C.camera(cam_loc, aim, lens=27, fstop=5.0, focus=(head_w - cam_loc).length, roll=0.0)

if os.environ.get("POSE_TEST"):
    sc.cycles.samples = 24
    sc.render.filepath = OUT.replace(".png", "_cam.png"); bpy.ops.render.render(write_still=True)
    hw = head_w
    C.camera(hw + (M.to_3x3() @ Vector((0.2, -0.9, 0.05))), hw, lens=50)
    sc.render.filepath = OUT.replace(".png", "_face.png"); bpy.ops.render.render(write_still=True)
    sys.exit(0)
C.finish(OUT, cine={"sat": 1.2, "exposure": -0.05, "warm": (1.03, 1.0, 0.97)})
print("RENDERED", OUT)
