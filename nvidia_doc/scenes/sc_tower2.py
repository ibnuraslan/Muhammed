"""CH4 redo: the Nvidia-stand-in HQ tower (sc_hq geometry), two new angles.
  street   CH4 5C (196 f) night: from street level across a road, closer; ONE board floor lit high up; cars with
           headlights and tail lights pass below (vehicles.py), slow tilt up toward the lit floor
  windscreen CH4 7D (199 f) dawn: from inside a parked car, through a rain-dotted windscreen; the wipers sweep once
           and the tower stands clear behind the glass in the early light
"""
import math
import numpy as np
import bpy
from mathutils import Vector
from kit import *
from common import area_light
import sc_hq

EXPOSURE = 0.0
VARIANT_FOR = {"street": "street", "windscreen": "windscreen"}
FRAMES = {"street": 196, "windscreen": 199}


def build(variant=None):
    c = {}
    if variant == "street":
        sc_hq.build("lit")
        from common import world_flat
        world_flat((0.018, 0.028, 0.06), 1.0)                       # deep blue night sky: the glass tower reflects it, its edges read
        # a four-lane road in front of the plaza, lane markings, kerbs, streetlights
        asph = pbr("Asphalt", (0.03, 0.03, 0.032), 0.35, 0.0, **{'Coat Weight': 0.4})
        box("Road", (0, 2.0, -0.05), (400, 22, 0.1), asph)
        paint = pbr("Lane", (0.7, 0.7, 0.65), 0.5)
        dash = box("Dash", (0, 0, -30), (3.0, 0.15, 0.01), paint)
        for lane_y in (-3.0, 2.0, 7.0):
            for k in range(-40, 40):
                instance(dash, (k * 6.0, lane_y, 0.006))
        box("Kerb", (0, 13.2, 0.08), (400, 0.4, 0.16), pbr("Kerb", (0.25, 0.25, 0.25), 0.7))
        box("Pavement", (0, -10, 0.05), (400, 4, 0.1), pbr("Pave", (0.12, 0.12, 0.13), 0.8))
        for k in range(-6, 7):
            x = k * 18.0
            cyl("LampPole", (x, 13.6, 4.5), 0.09, 9.0, pbr("Pole", (0.08, 0.08, 0.09), 0.4, 0.7), verts=10)
            box("LampHead", (x, 12.6, 8.9), (0.5, 2.2, 0.2), emissive("Sodium", (1.0, 0.7, 0.4), 30))
            l = bpy.data.lights.new("StreetL", 'SPOT'); l.energy = 2500; l.spot_size = math.radians(110); l.color = (1.0, 0.75, 0.45)
            o = bpy.data.objects.new("StreetL", l); bpy.context.collection.objects.link(o); o.location = (x, 11.5, 8.7); point_at(o, (x, 6, 0))
        # cars: two lanes each way, headlights (warm white) and tail lights (red) as emissive panels + real headlamps
        import vehicles
        cars = []
        for k, (kind, lane, x0, v) in enumerate((("sedan_modern", -3.0, -70, 11.0), ("taxi", 2.0, 40, -9.0),
                                                 ("sedan_modern", 7.0, -20, 12.5), ("van_1990s", -3.0, 15, 10.0),
                                                 ("sedan_modern", 2.0, 95, -10.5))):
            car = vehicles.make(kind, loc=(x0, lane, 0), heading_deg=0 if v > 0 else 180, lamps=True, real_lights=True)
            cars.append((car, x0, v))
        c["cars"] = cars
        c["board"] = Vector((0, 43, sc_hq.LIT_FLOOR * 4.0 + 2.0))
    else:   # windscreen at dawn
        sc_hq.build("dusk")
        asph = pbr("Asphalt", (0.05, 0.05, 0.055), 0.25, 0.0, **{'Coat Weight': 0.6})
        box("Road", (0, -20, -0.05), (400, 60, 0.1), asph)
        # the car interior around the camera (camera sits at the driver's eye, x=-10.4 y=-36 z=1.2)
        e = Vector((-14.0, -95.0, 1.2)); c["eye"] = e
        dark = pbr("Interior", (0.012, 0.012, 0.014), 0.6); dash_m = pbr("Dash", (0.02, 0.02, 0.022), 0.55)
        fwd = (Vector((0, 43, 23)) - e).normalized(); fwd.z = 0; fwd.normalize()
        side = fwd.cross(Vector((0, 0, 1))).normalized()
        def at(f, s, z):
            return e + fwd * f + side * s + Vector((0, 0, z))
        rz = math.atan2(fwd.y, fwd.x) - math.pi / 2
        TILT = math.radians(110)                                    # pane faces the driver, top leaning back toward them
        D = 0.62                                                    # glass distance ahead of the eye
        box("Dash", at(D + 0.15, 0.0, -0.42), (1.8, 0.7, 0.14), dash_m, bevel=0.03, rot=(0, 0, rz))
        box("DashTop", at(D - 0.05, 0.0, -0.36), (1.8, 0.3, 0.025), dark, rot=(math.radians(8), 0, rz))
        box("Roof", at(D - 0.25, 0.0, 0.43), (1.8, 0.7, 0.04), dark, rot=(math.radians(-6), 0, rz))
        for s_ in (-0.8, 0.8):                                      # A-pillars following the glass edges
            box("APillar", at(D, s_, 0.02), (0.09, 0.12, 0.85), dark, rot=(math.radians(-20), 0, rz))
        box("Mirror", at(D - 0.12, 0.08, 0.3), (0.24, 0.03, 0.07), dark, bevel=0.01, rot=(0, 0, rz))
        cyl("Wheel", at(0.4, -0.36, -0.3), 0.19, 0.03, dark, verts=40, rot=(math.radians(62), 0, rz))
        rain = rain_glass("Windscreen", scale=55, density=0.55)
        bpy.ops.mesh.primitive_plane_add(size=1, location=at(D, 0.0, 0.02), rotation=(TILT, 0, rz))
        ws = bpy.context.active_object; ws.name = "Windscreen"; ws.scale = (1.7, 0.85, 1); ws.data.materials.append(rain)
        # two wipers pivoting at the base of the glass (in the glass plane); one sweep up and back (frame driver)
        wiper_m = pbr("Wiper", (0.01, 0.01, 0.01), 0.5)
        up_g = Vector((0, math.cos(TILT), math.sin(TILT))); up_g.rotate(__import__("mathutils").Euler((0, 0, rz)))
        base = at(D, 0.0, 0.02) - up_g * 0.4
        for k, s_ in enumerate((-0.62, 0.02)):
            piv = bpy.data.objects.new(f"WiperPivot{k}", None); bpy.context.collection.objects.link(piv)
            piv.location = base + side * s_ - (at(D, 0, 0) - at(D - 0.01, 0, 0)) * 0.0
            piv.rotation_mode = 'XYZ'; piv.rotation_euler = (TILT, 0, rz)
            arm = box(f"Wiper{k}", (0, 0, 0), (0.6, 0.012, 0.02), wiper_m)
            arm.data.transform(__import__("mathutils").Matrix.Translation((0.3, 0, 0)))
            arm.parent = piv; arm.location = (0, 0, 0.015); arm.rotation_mode = 'XYZ'
            d = arm.driver_add("rotation_euler", 2).driver; d.type = 'SCRIPTED'
            d.expression = "0.05 + 1.45 * max(0, sin(min(max((frame - 60) / 60, 0), 1) * pi))"
        c["tower"] = Vector((0, 43, 24))
    return c


def anim_street(c, t):
    sec = t * FRAMES["street"] / 24
    for car, x0, v in c["cars"]:
        car.location.x = x0 + v * sec


def cam_street(c, t):
    e = ease(t)
    return (Vector((-24, -24, 1.35)).lerp(Vector((-21, -22, 1.5)), e), Vector((0, 40, 16)).lerp(Vector((0, 42, 23)), e), 22)


def cam_wind(c, t):
    e = ease(t)
    eye = c["eye"] + Vector((0, 0.08 * e, 0.01 * e))
    return (eye, c["tower"] + Vector((0, 0, -6)), 21)


MOVES = {
    "street": dict(kind="anim", far=400.0, anim=anim_street, cam=cam_street),
    "windscreen": dict(kind="anim", dof=8.0, far=400.0, cam=cam_wind, focus=lambda c, t: c["tower"]),
}
