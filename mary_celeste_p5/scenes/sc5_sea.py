"""Part 5 sea shots. SHOT=S01..S08, S27, S28 (env). Builds the set each shot needs and renders one still.

25 November 1872 (as the boat may have gone): a clear Atlantic morning off Santa Maria, warm low sun, deep blue
sea, broken white cloud. The ending (S27, S28) is the same sea at sunset, empty.
"""
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import p5; C = p5.C
C.reset()
import bpy
from mathutils import Vector, Matrix
import ship, sea, yawl, boatsea, boatcrew, props5

SHOT = os.environ.get("SHOT", "S01")
OUT = os.environ.get("OUT", os.path.join(p5.OUTDIR, f"{SHOT}.png"))
sc = C.render_setup(samples=int(os.environ.get("SPP", "96")), noise=0.03)
DENS = float(os.environ.get("HAIR", "1.0"))

WIND = Vector((0.55, -0.83, 0)).normalized()


def local_wind(hd):
    return Matrix.Rotation(math.radians(-hd), 3, 'Z') @ WIND


def sun(az_deg, el_deg, energy=3.2, color=(1.0, 0.86, 0.68), angle=1.5):
    s = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", 'SUN')); sc.collection.objects.link(s)
    s.data.energy = energy; s.data.angle = math.radians(angle); s.data.color = color
    az, el = math.radians(az_deg), math.radians(el_deg)
    d = Vector((math.cos(az) * math.cos(el), math.sin(az) * math.cos(el), math.sin(el)))
    s.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    return s


def sea_patch(size, res, scale, chop, wind, center=(0, 0), foam=0.25, seed=7):
    water = sea.water_material()
    oc = sea.ocean(size=size, res=res, scale=scale, chop=chop, wind=wind, repeat=2, foam=foam, mat=water, seed=seed,
                   direction=math.degrees(math.atan2(WIND.y, WIND.x)), loc=(center[0], center[1], 0))
    sea.far_sea(size * 1.0 + 10, mat=water, center=center)
    return oc


def mc_ship(heading, pos, sails="full", gap=(-2.7, -0.6, "S"), heel=4.0):
    mc = ship.build("MC", sails=sails, rail_gap=gap, wind=local_wind(heading), wet=0.5, detail=False)
    mc["root"].location = Vector(pos) + Vector((0, 0, -0.1))
    mc["root"].rotation_euler = (math.radians(-heel), 0, math.radians(heading))
    bpy.context.view_layer.update()
    return mc


def boat_at(oc, x, y, heading, oars="out", stroke=0.0, crew=True, look=None, extra_hulls=()):
    b = yawl.build("yawl", oars=oars, wet=0.6)
    boatsea.float_on(oc, b["root"], heading, x, y, draft=0.40)
    boatsea.cut_and_wash(oc, [b["hull"], *extra_hulls], [b["root"]])
    if crew:
        boatcrew.man_the_boat(b, look=look, density=DENS, stroke=stroke)
    return b


def cam(loc, tgt, lens, fstop=None, focus=None):
    return C.camera(Vector(loc), Vector(tgt), lens=lens, fstop=fstop, focus=focus)


cine = {"sat": 1.12, "exposure": 0.0}
# ============================================================================ the shots
if SHOT in ("S01", "S02", "S03"):
    # alongside: the yawl lies off the starboard side by the gap in the rail, the painter made fast aboard
    mc = mc_ship(0.0, (0, 0, 0), sails="full", heel=2.0)
    oc = sea_patch(140, 20, 1.1, 1.1, 9.0, center=(0, -10), foam=0.18)
    sea.sky(strength=1.0, rot_deg=40, res="4k", aid="kloofendal_48d_partly_cloudy_puresky")
    sun(-60, 22)
    by = -(ship.B / 2 + 1.45)
    rail = mc["root"].matrix_world @ Vector((-1.6, -(ship.half_breadth((-1.6 + ship.L / 2) / ship.L, 1.0) - 0.05),
                                             ship.zdeck(-1.6) + ship.RAIL_H))
    b = boat_at(oc, -1.8, by, 0.0, oars="out", crew=True, look=rail + Vector((0, 0, 0.5)), extra_hulls=(mc["hull"],))
    Mb = b["root"].matrix_world
    ring = Mb @ b["ring"]
    cleat = mc["root"].matrix_world @ Vector((4.5, -(ship.B / 2 - 0.25), ship.zdeck(4.5) + ship.RAIL_H + 0.05))
    yawl.painter("painter", ring, cleat, b["mats"]["rope"], sag=0.12)
    if SHOT == "S01":
        cam(Mb @ Vector((-9.5, -7.0, 0.9)), Mb @ Vector((1.0, 1.5, 2.4)), 26)
    elif SHOT == "S02":
        c0 = Mb @ Vector((-0.9, -3.6, 1.15)); tgt = Mb @ Vector((-2.3, 0.0, 1.1))
        cam(c0, tgt, 38, fstop=2.8, focus=(Mb @ Vector((-2.3, -0.2, 1.05)) - c0).length)
    else:
        c = Mb @ Vector((1.2, -1.9, 1.05))
        cam(c, ring.lerp(cleat, 0.3) + Vector((0, 0, -0.4)), 24, fstop=5.6, focus=(ring - c).length)
elif SHOT in ("S04", "S05"):
    # the ship moving off on the wind, the boat left behind
    mc = mc_ship(-60.0, (60, -30, 0), sails="full", heel=6.0)
    oc = sea_patch(150, 20, 1.4, 1.3, 11.0, center=(20, -10), foam=0.25)
    sea.sky(strength=1.0, rot_deg=40, res="4k", aid="kloofendal_48d_partly_cloudy_puresky")
    sun(-60, 20)
    b = boat_at(oc, 0, 0, -30.0, oars="out", stroke=0.3, look=Vector((60, -30, 6)))
    Mb = b["root"].matrix_world
    if SHOT == "S04":
        cam(Mb @ Vector((-11, 3.5, 5.0)), Mb @ Vector((14, -2.5, 0.0)).lerp(Vector((60, -30, 6)), 0.35), 30)
    else:
        cam(Mb @ Vector((-3.25, 0.25, 1.55)), Mb @ Vector((4.0, -0.4, 1.0)), 32, fstop=4.0, focus=4.5)
elif SHOT == "S06":
    # top-down 3D maquette: ship, boat, and the unknown: soft orange bands round the boat
    mc = mc_ship(-60.0, (70, -40, 0), sails="full", heel=6.0)
    oc = sea_patch(220, 18, 1.4, 1.3, 11.0, center=(30, -20), foam=0.08)
    sea.sky(strength=1.0, rot_deg=40, res="4k", aid="kloofendal_48d_partly_cloudy_puresky")
    sun(-60, 35)
    b = boat_at(oc, 0, 0, -30.0, oars="out", crew=True, look=Vector((70, -40, 6)))
    props5.bands(Vector((0, 0, 4.0)), [12, 22, 32], width=7.0, alpha=0.42, strength=1.4)
    cam((32, -18, 165), (32, -18, 0), 35)
elif SHOT == "S07":
    oc = sea_patch(150, 20, 1.3, 1.2, 10.0, foam=0.22)
    sea.sky(strength=1.0, rot_deg=40, res="4k", aid="kloofendal_48d_partly_cloudy_puresky")
    sun(-80, 18)
    props5.island(Vector((-1500, 9500, 0)), length=9000, height=560)
    b = boat_at(oc, 0, 0, 90.0, oars="out", stroke=0.6, look=Vector((0, 9000, 200)))
    Mb = b["root"].matrix_world
    cam(Mb @ Vector((-8.5, 0.9, 2.0)), Mb @ Vector((40, -2.0, 2.5)), 40)
elif SHOT == "S08":
    oc = sea_patch(160, 22, 2.6, 1.8, 16.0, foam=0.42, seed=11)
    sea.sky(strength=0.9, rot_deg=120, res="4k", aid="kloofendal_38d_partly_cloudy_puresky")
    sun(-100, 14, energy=2.6)
    b = boat_at(oc, 0, 0, 30.0, oars="out", stroke=0.4, look=Vector((-50, 30, 3)))
    cam((-32, -46, 15), (0, 0, 0.5), 50)
    cine = {"sat": 1.05, "exposure": -0.1}
elif SHOT in ("S27", "S28"):
    oc = sea_patch(170, 20, 1.6, 1.3, 12.0, foam=0.2, seed=5)
    sea.sky(strength=0.32, rot_deg=180, res="4k", aid="qwantani_sunset_puresky")
    sun(90, 3.5, energy=1.6, color=(1.0, 0.62, 0.36), angle=0.8)
    if SHOT == "S27":
        b = boat_at(oc, 0, 0, 80.0, oars="out", crew=True, look=Vector((0, 400, 4)))
        cam((-6, -48, 6.0), (0, 30, 0.5), 60)
    else:
        cam((0, -40, 3.0), (0, 400, 3.5), 40)
    cine = {"sat": 1.25, "exposure": -0.45}

C.finish(OUT, cine=cine, bloom=0.4)
print("RENDERED", OUT)
