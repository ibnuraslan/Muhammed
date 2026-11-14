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
DUR = {"mic": 9.0, "mic_dash": 4.0, "envelope": 9.0, "reels": 9.0}
VARIANT_FOR = {"mic": "mic_out", "mic_dash": "dash", "envelope": "street", "reels": "interior_day"}


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
    if v == "dash":
        # tight insert under the dashboard: wiring loom, a fuse cover, the steering column; a gloved hand (black nitrile)
        # presses a small microphone capsule up into place under a torch beam
        interior(c)
        under_m = pbr("DashUnder", (0.06, 0.06, 0.065), 0.75)
        nb = under_m.node_tree.nodes; lb = under_m.node_tree.links
        nz = nb.new("ShaderNodeTexNoise"); nz.inputs['Scale'].default_value = 400; bm_ = nb.new("ShaderNodeBump"); bm_.inputs['Strength'].default_value = 0.25
        lb.new(nz.outputs['Fac'], bm_.inputs['Height']); lb.new(bm_.outputs['Normal'], nb["Principled BSDF"].inputs['Normal'])   # grained plastic
        U = dd.Builder("DashUnder")
        U.box((1.15, 0.0, 0.54), (0.42, 1.4, 0.03), under_m)                # the under-dash closing panel
        U.box((1.08, -0.08, 0.505), (0.12, 0.2, 0.04), pbr("FuseCover", (0.09, 0.09, 0.095), 0.5))
        rng = np.random.default_rng(7)
        cols = [(0.03, 0.03, 0.03), (0.25, 0.12, 0.05), (0.05, 0.1, 0.3), (0.3, 0.3, 0.3), (0.03, 0.03, 0.03), (0.12, 0.2, 0.08),
                (0.03, 0.03, 0.03), (0.35, 0.05, 0.04), (0.2, 0.2, 0.22), (0.03, 0.03, 0.03), (0.25, 0.22, 0.05), (0.03, 0.03, 0.03)]
        for k in range(12):                                                 # the wiring loom: a bundle of insulated wires
            a_ = 2 * math.pi * k / 12; rr = 0.009 + 0.004 * (k % 3) / 2
            U.cyl((1.24 + rr * math.cos(a_), 0.15, 0.5 + rr * math.sin(a_)), 0.0028, 0.9, pbr(f"Wire{k}", cols[k], 0.45), verts=8, rot=(math.radians(90), 0, 0))
        tie = pbr("CableTie", (0.75, 0.74, 0.7), 0.5)
        for y in np.arange(-0.25, 0.6, 0.09):                               # nylon cable ties around the bundle
            U.cyl((1.24, float(y), 0.5), 0.0165, 0.005, tie, verts=16, rot=(math.radians(90), 0, 0))
            U.box((1.24, float(y), 0.481), (0.008, 0.006, 0.008), tie)
        U.box((1.0, 0.38, 0.2), (0.25, 0.08, 0.02), pbr("Pedal", (0.15, 0.15, 0.16), 0.4, 0.8), rot=(0, math.radians(-30), 0))
        U.done()
        mic = dd.Builder("BugMic"); mm = pbr("MicBody", (0.01, 0.01, 0.012), 0.3)
        mic.cyl((0, 0, 0), 0.008, 0.03, mm, verts=20, rot=(0, math.radians(90), 0))                       # small black capsule
        mic.cyl((0.0165, 0, 0), 0.0065, 0.003, pbr("MicGrille", (0.45, 0.45, 0.47), 0.35, 1.0), verts=20, rot=(0, math.radians(90), 0))
        mic.cyl((0.0, 0, 0), 0.0085, 0.008, pbr("Tape", (0.6, 0.6, 0.58), 0.8), verts=20, rot=(0, math.radians(90), 0))   # grey tape band
        mic.cyl((-0.07, 0, 0), 0.0011, 0.11, pbr("MicWire", (0.02, 0.02, 0.02), 0.5), verts=6, rot=(0, math.radians(90), 0))  # thin cable
        c["mic"] = mic.done((0, 0, -10))
        h = person("Tech", 1.0, 36, "male_casualsuit05", "short02", cval=1.1); c["tech"] = h
        glove = pbr("Nitrile", (0.08, 0.22, 0.6), 0.4, 0.0, **{"Coat Weight": 0.25})          # blue nitrile gloves
        h.body.data.materials[0] = glove                                    # only the forearm and hand are ever in frame
        for o in bpy.data.objects:
            if o is not h.body and ("hair" in o.name.lower() or "short02" in o.name.lower() or "eyebrow" in o.name.lower()):
                o.hide_render = True
        tl = bpy.data.lights.new("TechTorch", 'SPOT'); tl.energy = 14; tl.spot_size = math.radians(34); tl.spot_blend = 0.35
        tl.color = (1.0, 0.95, 0.86); tl.shadow_soft_size = 0.015
        to = bpy.data.objects.new("TechTorch", tl); bpy.context.collection.objects.link(to); c["torch"] = to
    elif v in ("interior", "interior_day"):
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
    elif v == "mic_out":
        # night, from outside: the driver's door open, a technician leaning into the footwell (back and legs only)
        world_flat((0.02, 0.025, 0.04), 1.0)
        road = dd.wet(dd.tex_mat("asphalt_02", 0.4, tint=(0.5, 0.5, 0.52), name="NightRoad", sat=0.4), 0.9, 0.3)
        box("Road", (0, 0, -0.06), (80, 30, 0.1), road)
        box("Pave", (0, 3.6, 0.05), (80, 2.4, 0.12), dd.wet(dd.tex_mat("concrete_floor_02", 0.5, tint=(0.5, 0.5, 0.5), name="NightPave", sat=0.3), 0.8, 0.4))
        for k, (a, b) in enumerate(((-40, -10), (-10, 20), (20, 50))):
            haussmann(a, b, seed=90 + k, origin=(0, 4.8, 0), lit_frac=0.3)
        car_ = dd.sedan("BugCar", (0.32, 0.03, 0.04), lights=False); car_.location = (0, 1.1, 0)   # deep burgundy metallic
        # cut the real front-door opening out of the body shell (kit seams: x 0.90 .. -0.49, sill 0.37 .. roof 1.40, +Y side)
        cut = box("DoorCut", (0.205, 1.1 + 0.95, 0.89), (1.36, 0.9, 1.03))
        cut.hide_render = True; cut.display_type = 'WIRE'; cut.visible_camera = False
        md = car_.modifiers.new("DoorOpening", 'BOOLEAN'); md.operation = 'DIFFERENCE'; md.object = cut; md.solver = 'FLOAT'

        # the open FRONT driver's door (left side = +Y), a real door with depth: outer skin, inner trim panel with an
        # armrest and pull, the window frame; hinged at its front edge and swung out 62 degrees
        paint = pbr("DoorPaint", (0.32, 0.03, 0.04), 0.22, 0.6, **{'Coat Weight': 1.0, 'Coat Roughness': 0.04})
        trim = pbr("DoorTrim", (0.05, 0.05, 0.055), 0.65)
        D = dd.Builder("OpenDoor")
        D.box((-0.69, 0.0, 0.65), (1.36, 0.05, 0.56), paint)               # outer skin, the size of the opening
        D.box((-0.69, -0.06, 0.65), (1.3, 0.07, 0.52), trim)               # inner trim panel (door thickness ~0.12)
        D.box((-0.85, -0.11, 0.74), (0.5, 0.06, 0.05), trim)               # armrest
        D.box((-0.4, -0.1, 0.85), (0.12, 0.04, 0.03), pbr("Pull", (0.5, 0.5, 0.52), 0.3, 1.0))
        for (cx, cz, sx, sz) in ((-0.82, 1.38, 1.1, 0.04), (-1.36, 1.16, 0.04, 0.44), (-0.03, 1.1, 0.05, 0.34)):
            D.box((cx, -0.02, cz), (sx, 0.05, sz), paint)                  # window frame: top rail, B-pillar edge, A edge
        D.box((-0.75, -0.02, 1.15), (1.2, 0.01, 0.42), pbr("DoorGlassD", (0.02, 0.025, 0.03), 0.04, 0.0, **{'Coat Weight': 1.0}))
        dobj = D.done((0.9, 2.0, 0.0)); dobj.rotation_euler = (0, 0, math.radians(-62))
        for x in (-3.0, 6.0):
            dd.model_h("street_lamp_02", (x, 3.3, 0.1), 5.0)
            sl = bpy.data.lights.new("StreetLamp", 'POINT'); sl.energy = 900; sl.color = (1.0, 0.68, 0.38); sl.shadow_soft_size = 0.2
            so = bpy.data.objects.new("StreetLamp", sl); bpy.context.collection.objects.link(so); so.location = (x, 3.0, 4.7)
        h = person("Tech", 1.0, 36, "male_casualsuit05", "short02", cval=1.1); c["tech"] = h
        tl = bpy.data.lights.new("TechTorch", 'SPOT'); tl.energy = 18; tl.spot_size = math.radians(35); tl.spot_blend = 0.5
        tl.color = (1.0, 0.95, 0.85); tl.shadow_soft_size = 0.02
        to = bpy.data.objects.new("TechTorch", tl); bpy.context.collection.objects.link(to); c["torch"] = to
        # the lookout: a detective at the rear of the car, watching the street, torch held low and off the car
        lk = dd.officer("Lookout", 44, seed=1, band=False); c["lookout"] = lk
        ll = bpy.data.lights.new("LookoutTorch", 'SPOT'); ll.energy = 30; ll.spot_size = math.radians(28); ll.spot_blend = 0.4
        ll.color = (1.0, 0.95, 0.88); ll.shadow_soft_size = 0.02
        lo = bpy.data.objects.new("LookoutTorch", ll); bpy.context.collection.objects.link(lo); c["lk_torch"] = lo
        c["lk_torch_body"] = cyl("LkTorch", (0, 0, -20), 0.016, 0.16, pbr("TorchBody", (0.03, 0.03, 0.035), 0.4, 0.6), verts=12)
        c["rain_ys"] = (4.5, 6.0)
        rain(c, 0, c["rain_ys"], width=30, height=8, strength=1.2, density=0.985)
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
        rain(c, 0, c["rain_ys"], width=30, height=8, strength=0.8, density=0.985)
    import look                                   # artificial light only: keep the set's lights, darker walls, warm practicals
    look.night_interior()
    return c


def anim_mic_out(c, t):
    """Kneeling on the wet road at the open front door, leaning into the footwell, both hands up under the dash;
    the torch in his left hand lights the work. The lookout watches the street, torch low."""
    sec = t * DUR["mic"]
    rain_fall(c, sec)
    from dd import pose_kneel, arms_relaxed
    h = c["tech"]; pose_kneel(h, lean=48)
    sp = Vector((0.12, 2.3, 0.0)); place(h, sp, 0.0)                       # facing -Y: head and shoulders inside the opening
    dd.ground(h, 0.0)
    under = Vector((0.6, 1.55, 0.6))
    reach(h, "R", under + Vector((0.0, 0.0, 0.02 * math.sin(sec * 1.8))), Vector((0.3, 0.6, -0.8)))      # working the mic
    reach(h, "L", under + Vector((-0.2, 0.22, -0.05)), Vector((-0.4, 0.6, -0.8)))
    fingers_curl(h, 35)
    c["torch"].location = h.bone_tail("wrist.L") + Vector((0, -0.03, 0.0)); point_at(c["torch"], under)
    lk = c["lookout"]; zero(lk); from human import pose_walk
    pose_walk(lk, 0.0, stride=0.0, arm_swing=0.0)
    lp = Vector((4.6, 3.0, 0.12)); place(lk, lp, math.radians(100), z=0.12); arms_relaxed(lk)    # ahead of the car, watching the street
    lk.rot("head", (0, 0, 1), 18 * ease(min(1.0, max(0.0, (sec - 4.0) / 1.5))))     # a car passes at the end of the street: he looks
    tb = lk.bone_tail("wrist.R") if "wrist.R" in lk.arm.pose.bones else lk.bone_tail("lowerarm02.R")
    c["lk_torch_body"].location = tb + Vector((0, 0, -0.04)); c["lk_torch_body"].rotation_euler = (math.radians(70), 0, lk.arm.rotation_euler.z)
    c["lk_torch"].location = tb + Vector((0, 0, -0.06)); point_at(c["lk_torch"], lp + Vector((2.5, -0.6, 0.0)))


def anim_mic_dash(c, t):
    """The gloved right hand brings the capsule up and presses it into the corner by the loom, then holds it there."""
    sec = t * DUR["mic_dash"]
    from dd import pose_kneel
    h = c["tech"]; pose_kneel(h, lean=80)                                   # bent right down into the footwell
    place(h, Vector((1.02, 0.82, 0.0)), 0.0); dd.ground(h, 0.0)            # kneeling at the open door sill
    spot = Vector((1.2, 0.2, 0.522))
    u = ease(min(1.0, max(0.0, (sec - 0.4) / 1.6)))
    tgt = spot + Vector((-0.1 * (1 - u), 0.12 * (1 - u), -0.09 * (1 - u)))
    reach(h, "R", tgt + Vector((-0.02, 0.05, -0.03)), Vector((0.2, 0.6, -0.8)))
    fingers_curl(h, 45)
    hand = h.bone_tail("wrist.R") if "wrist.R" in h.arm.pose.bones else h.bone_tail("lowerarm02.R")
    c["mic"].location = tgt + Vector((-0.03, -0.015, -0.004)); c["mic"].rotation_euler = (0, 0, math.radians(25))  # at his fingertips, pressed up to the loom
    c["torch"].location = Vector((0.9, 0.3, 0.36)); point_at(c["torch"], c["mic"].location)        # the torch beside the lens, on hand and mic


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
    "mic": dict(kind="anim", dof=5.6, anim=anim_mic_out,
                cam=lambda c, t: (Vector((-3.3, 4.4, 1.7)).lerp(Vector((-2.9, 4.2, 1.62)), ease(t)), Vector((1.2, 2.2, 0.95)), 30),
                focus=lambda c, t: Vector((0.55, 2.3, 0.7))),
    "mic_dash": dict(kind="anim", dof=5.6, anim=anim_mic_dash,
                     cam=lambda c, t: (Vector((0.86, 0.36, 0.36)).lerp(Vector((0.9, 0.34, 0.37)), ease(t)), Vector((1.17, 0.22, 0.52)), 32),
                     focus=lambda c, t: c["mic"].location),
    "mic_old": dict(kind="anim", dof=2.8, anim=anim_mic,
                cam=lambda c, t: (Vector((-0.85, -0.1, 1.28)).lerp(Vector((-0.75, -0.05, 1.26)), ease(t)), Vector((0.95, 0.35, 0.62)), 20),
                focus=lambda c, t: Vector((0.8, 0.35, 0.8))),
    "envelope": dict(kind="anim", dof=5.6, anim=anim_envelope,
                     cam=lambda c, t: (Vector((6.5, -6.5, 2.4)).lerp(Vector((5.8, -6.0, 2.2)), ease(t)), Vector((0.2, 0.0, 1.0)), 32),
                     focus=lambda c, t: Vector((0.2, 0.0, 1.0))),
    "reels": dict(kind="anim", dof=1.8, anim=anim_reels,
                  cam=lambda c, t: (Vector((0.1, 0.45, 1.18)).lerp(Vector((0.15, 0.42, 1.16)), ease(t)), Vector((0.2, -0.8, 0.82)), 24),
                  focus=lambda c, t: Vector((-0.1, -0.33, 0.52))),
}
