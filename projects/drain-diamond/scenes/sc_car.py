"""CAR: surveillance, 2008-09, night and rain.
  mic      (ch3 3A): from the back seat, a technician leans in under the dashboard of a parked car, a small torch glowing (medium)
  envelope (ch3 3B): wide through the rain: two cars parked side by side, an envelope passes between the open driver windows
  reels    (ch3 5B): in the unmarked car, a recorder's reels turn on the seat while the house sits blurred outside
"""
import math
import numpy as np
import bpy
from mathutils import Vector
from kit import *
import dd
from dd import person, place, face_to, zero, ground, rain, rain_fall
from human import reach, pose_sit, reset_pose, fingers_curl
from sc_boutique import haussmann

EXPOSURE = 0.6
DUR = {"mic": 9.0, "envelope": 9.0, "reels": 9.0}
VARIANT_FOR = {"mic": "interior", "envelope": "street", "reels": "interior_day"}


def interior(c, day=False):
    """Car cabin around the origin: driver seat at (+0.37, 0), dashboard ahead (+X), back seat behind."""
    seat_m = dd.tex_mat("fabric_pattern_05", 2.0, tint=(0.42, 0.4, 0.38), name="SeatFab", sat=0.2)
    plastic = pbr("DashPlastic", (0.07, 0.07, 0.075), 0.55)
    B = dd.Builder("Cabin")
    B.box((0, 0, 0.05), (3.0, 1.6, 0.1), pbr("CarCarpet", (0.04, 0.04, 0.045), 0.9))
    B.box((1.25, 0, 0.75), (0.5, 1.5, 0.4), plastic)                          # dashboard
    B.box((1.05, 0, 0.6), (0.35, 0.3, 0.5), plastic)                          # centre console
    B.box((0.15, 0, 0.35), (1.4, 0.2, 0.25), plastic)                         # tunnel
    for sy in (-1, 1):
        B.box((0.35, sy * 0.38, 0.38), (0.55, 0.52, 0.16), seat_m).box((0.1, sy * 0.38, 0.75), (0.14, 0.5, 0.65), seat_m, rot=(0, math.radians(-12), 0))
        B.box((0.0, sy * 0.78, 0.6), (2.4, 0.06, 0.62), pbr("DoorCard", (0.12, 0.12, 0.125), 0.6))
    B.box((-0.75, 0, 0.42), (0.6, 1.4, 0.2), seat_m).box((-1.05, 0, 0.8), (0.15, 1.4, 0.6), seat_m, rot=(0, math.radians(-15), 0))
    B.box((0.2, 0, 1.35), (2.2, 1.5, 0.05), fabric("Headliner", (0.35, 0.34, 0.32), 0.95, 0.3, 300))
    for sy in (-1, 1):
        B.box((0.95, sy * 0.72, 1.1), (0.08, 0.06, 0.55), plastic, rot=(0, math.radians(-30), 0))       # A-pillars
        B.box((-0.3, sy * 0.76, 1.1), (0.1, 0.06, 0.5), plastic)                                       # B-pillars
    B.done()
    # steering wheel
    bpy.ops.mesh.primitive_torus_add(major_radius=0.18, minor_radius=0.018, location=(0.85, 0.38, 0.95), rotation=(0, math.radians(65), 0))
    bpy.context.active_object.data.materials.append(plastic)
    cyl("Column", (0.98, 0.38, 0.85), 0.03, 0.3, plastic, verts=12, rot=(0, math.radians(65), 0))
    wind = box("Windscreen", (1.2, 0, 1.1), (0.02, 1.45, 0.62), rain_glass("CarRain", 90, 0.5), rot=(0, math.radians(-58), 0))
    for sy in (-1, 1):
        box("SideGlass", (0.3, sy * 0.79, 1.12), (1.3, 0.01, 0.38), rain_glass("CarRainS", 90, 0.6))
    box("RearGlass", (-1.25, 0, 1.1), (0.02, 1.35, 0.45), rain_glass("CarRainR", 90, 0.6), rot=(0, math.radians(50), 0))
    # outside: a wet street of blocks with lit windows and warm street lamps (soft bokeh)
    for k, (a, b) in enumerate(((-40, -10), (-10, 20), (20, 50))):
        haussmann(a, b, seed=70 + k, rot_z=0.0, origin=(0, 9.0, 0), lit_frac=0.35 if not day else 0.05)   # a block face along the kerb, 9 m away
    road = dd.wet(dd.tex_mat("asphalt_02", 0.4, tint=(0.5, 0.5, 0.52), name="NightRoad", sat=0.4), 0.9, 0.3)
    box("Road", (0, 0, -0.06), (80, 30, 0.1), road)
    if day:
        world_sky(sun_elev_deg=20, sun_rot_deg=200, strength=0.4, tint=(0.8, 0.85, 0.95))
        dd.pavillon((8.0, -6.0, 0), w=9.0, d=8.0, floors=2, rot_z=math.pi, name="TargetHouse")
    else:
        world_flat((0.02, 0.025, 0.04), 1.0)
        for k in range(6):
            l = bpy.data.lights.new("StreetLamp", 'POINT'); l.energy = 600; l.color = (1.0, 0.68, 0.38); l.shadow_soft_size = 0.2
            o = bpy.data.objects.new("StreetLamp", l); bpy.context.collection.objects.link(o); o.location = (-12 + k * 9.0, 5.0, 5.0)
            cyl("LampGlow", (-12 + k * 9.0, 5.0, 5.0), 0.15, 0.3, emissive("LampGlowE", (1.0, 0.7, 0.4), 30), verts=12)
        il = bpy.data.lights.new("Interior", 'POINT'); il.energy = 40; il.color = (1.0, 0.8, 0.6)
        io = bpy.data.objects.new("Interior", il); bpy.context.collection.objects.link(io); io.location = (0.2, 0, 1.3)


def build(variant=None):
    c = {}
    v = variant or "interior"
    if v in ("interior", "interior_day"):
        interior(c, day=(v == "interior_day"))
        if v == "interior":
            h = person("Tech", 1.0, 36, "male_casualsuit05", "short02", cval=1.1)
            c["tech"] = h
            tl = bpy.data.lights.new("TechTorch", 'SPOT'); tl.energy = 25; tl.spot_size = math.radians(40); tl.color = (1.0, 0.95, 0.85)
            to = bpy.data.objects.new("TechTorch", tl); bpy.context.collection.objects.link(to); c["torch"] = to
            c["mic"] = cyl("Mic", (0, 0, -10), 0.008, 0.03, pbr("MicM", (0.02, 0.02, 0.02), 0.5), verts=10)
        else:
            rec = dd.model_h("portable_cassette_player", (0.35, -0.38, 0.46), 0.1, rot_z=1.2)
            c["reels"] = []
            for k in range(2):          # the turning spools behind the player's window
                r = cyl(f"Reel{k}", (0.33, -0.42 + 0.05 * k, 0.575), 0.015, 0.004, pbr("ReelM", (0.75, 0.75, 0.77), 0.3, 1.0), verts=6)
                c["reels"].append(r)
            c["rec"] = rec
    else:
        world_flat((0.02, 0.025, 0.04), 1.0)
        road = dd.wet(dd.tex_mat("asphalt_02", 0.4, tint=(0.5, 0.5, 0.52), name="NightRoad", sat=0.4), 0.9, 0.3)
        box("Road", (0, 0, -0.06), (80, 30, 0.1), road)
        for k, (a, b) in enumerate(((-40, -10), (-10, 20), (20, 50))):
            haussmann(a, b, seed=80 + k, origin=(0, 6.5, 0), lit_frac=0.35)
        box("Pave", (0, 4.5, 0.05), (80, 4, 0.12), dd.wet(dd.tex_mat("concrete_floor_02", 0.5, tint=(0.5, 0.5, 0.5), name="NightPave", sat=0.3), 0.8, 0.4))
        for k in range(5):
            l = bpy.data.lights.new("StreetLamp", 'POINT'); l.energy = 900; l.color = (1.0, 0.68, 0.38); l.shadow_soft_size = 0.2
            o = bpy.data.objects.new("StreetLamp", l); bpy.context.collection.objects.link(o); o.location = (-14 + k * 7.0, 2.8, 5.0)
            dd.model_h("street_lamp_02", (-14 + k * 7.0, 3.0, 0.1), 5.0)
        a = dd.sedan("CarA", (0.08, 0.09, 0.1), lights=False, window_open=1.0); a.location = (0, 1.2, 0)
        b = dd.sedan("CarB", (0.35, 0.36, 0.38), lights=False, window_open=1.0); b.location = (0.4, -1.2, 0); b.rotation_euler = (0, 0, math.pi)
        c["env"] = box("Envelope", (0, 0, 0), (0.23, 0.005, 0.12), pbr("EnvM", (0.7, 0.6, 0.42), 0.7))
        for name, loc in (("DrvA", (0.3, 0.55, 0.0)), ("DrvB", (0.1, -0.55, 0.0))):
            h = person(name, 1.0, 40, "male_casualsuit05", "short02", cval=1.0)
            zero(h); reset_pose(h); pose_sit(h, lean=4)
            place(h, loc, math.radians(-90) if name == "DrvA" else math.radians(90))
            hip = (h.bone_head("upperleg01.L") + h.bone_head("upperleg01.R")) / 2; h.arm.location.z += 0.5 - hip.z
            c[name] = h
        c["rain_ys"] = (-6.0, -3.0, -1.6)
        rain(c, 0, c["rain_ys"], width=30, height=8, strength=1.6, density=0.985)
    return c


def anim_mic(c, t):
    sec = t * DUR["mic"]
    h = c["tech"]; zero(h); reset_pose(h); pose_sit(h, lean=40)
    place(h, (0.3, 0.42, 0), math.radians(-90))
    hip = (h.bone_head("upperleg01.L") + h.bone_head("upperleg01.R")) / 2; h.arm.location.z += 0.48 - hip.z; bpy.context.view_layer.update()
    h.rot("spine03", (0, 1, 0), -10)
    under = Vector((1.05, 0.25, 0.55 + 0.02 * math.sin(sec * 1.4)))
    reach(h, "R", under, Vector((0, 1, -0.5))); reach(h, "L", under + Vector((-0.12, 0.08, 0.05)), Vector((0, 1, -0.5)))
    fingers_curl(h, 40)
    c["torch"].location = under + Vector((-0.2, 0.05, 0.1)); point_at(c["torch"], under + Vector((0.2, -0.05, 0.1)))
    c["mic"].location = under + Vector((0.02, 0, 0.03))


def anim_envelope(c, t):
    sec = t * DUR["envelope"]
    rain_fall(c, sec)
    u = ease(min(1.0, max(0.0, (sec - 2.5) / 2.5)))
    a = Vector((0.3, 1.2 - 0.8, 1.08)); b = Vector((0.15, -1.2 + 0.8, 1.08))
    e = c["env"]; e.location = a.lerp(b, u) + Vector((0, 0, 0.05 * math.sin(math.pi * u))); e.rotation_euler = (0, 0, 0)
    da, db = c["DrvA"], c["DrvB"]
    if u < 0.55:
        reach(da, "R", e.location + Vector((0.0, 0.08, -0.02)), Vector((0, 0.5, -0.6)))
    if u > 0.45:
        reach(db, "L", e.location + Vector((0.0, -0.08, -0.02)), Vector((0, -0.5, -0.6)))


def anim_reels(c, t):
    sec = t * DUR["reels"]
    for k, r in enumerate(c["reels"]):
        r.rotation_euler = (0, 0, sec * 2.5)


MOVES = {
    "mic": dict(kind="anim", dof=2.8, anim=anim_mic,
                cam=lambda c, t: (Vector((-0.85, -0.1, 1.28)).lerp(Vector((-0.75, -0.05, 1.26)), ease(t)), Vector((0.95, 0.35, 0.62)), 20),
                focus=lambda c, t: Vector((0.8, 0.35, 0.8))),
    "envelope": dict(kind="anim", dof=5.6, anim=anim_envelope,
                     cam=lambda c, t: (Vector((6.5, -6.5, 2.4)).lerp(Vector((5.8, -6.0, 2.2)), ease(t)), Vector((0.2, 0.0, 1.0)), 32),
                     focus=lambda c, t: Vector((0.2, 0.0, 1.0))),
    "reels": dict(kind="anim", dof=1.8, anim=anim_reels,
                  cam=lambda c, t: (Vector((0.1, 0.45, 1.18)).lerp(Vector((0.15, 0.42, 1.16)), ease(t)), Vector((0.2, -0.8, 0.82)), 24),
                  focus=lambda c, t: Vector((-0.1, -0.33, 0.52))),
}
