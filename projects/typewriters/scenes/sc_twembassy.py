"""US EMBASSY, MOSCOW, MAY 1984 (exterior). An eight-storey brick chancery on a wide boulevard: trolleybus wires,
boxy saloons, a militia booth at the gate, a flag stirring. On the roof, a steel hoist jib with a cable down the facade.

Intro 1A  street_push   slow push across the boulevard as a trolleybus and cars pass (2.5 s lead before the first word)
Intro 1B  crane_up      crane up the facade to the roof; the hoist arm turns
Intro 4A  hoist_rise    looking up the wall: a burlap crate rises past the windows on the hoist cable
Intro 4B  roof_swing    on the roof: two workers swing the crate in over the parapet
"""
import math
import numpy as np
import bpy
from mathutils import Vector, Matrix
from kit import *
import ph
import twp
import tw_vehicles as V
import machines as MC

EXPOSURE = -0.3
LEAD = 2.5
DUR = {"street_push": LEAD + 3.0, "crane_up": 4.5, "hoist_rise": 4.5, "roof_swing": 5.0, "trailer_seal": 4.5, "hoist_street": 5.0, "window_night": 6.0, "truck_leave": 5.0}
TRUCK = Vector((9.5, -8.3, 0.0))
VARIANT_FOR = {"window_night": "night"}
LIT = Vector((-22 + 6.5 * (44 / 14), 0.0, 4 * 3.4 + 1.7))      # the lit office window (column 6, fifth floor)
FLOORS, FH = 8, 3.4
BW = 44.0                    # facade width (x), facade plane y = 0, building extends to +y
ROOF = FLOORS * FH + 1.2     # top of the cornice / parapet base
COLS = 14
JIB = Vector((6.0, 0.9, ROOF + 0.9))      # hoist post on the roof, near the front edge
ROAD_Y = -14.0               # boulevard centreline
WIRE_Z = 5.8


def stone(name, col):
    m = pbr(name, col, 0.75)
    N = m.node_tree.nodes; L = m.node_tree.links; tc = N.new("ShaderNodeTexCoord")
    nz = N.new("ShaderNodeTexNoise"); nz.inputs['Scale'].default_value = 3.0; nz.inputs['Detail'].default_value = 8
    L.new(tc.outputs['Object'], nz.inputs['Vector'])
    rp = N.new("ShaderNodeValToRGB"); rp.color_ramp.elements[0].color = (*[v * 0.82 for v in col], 1); rp.color_ramp.elements[1].color = (*[min(1, v * 1.1) for v in col], 1)
    L.new(nz.outputs['Fac'], rp.inputs['Fac']); L.new(rp.outputs['Color'], N["Principled BSDF"].inputs['Base Color'])
    return m


def window_unit(name, w, h, frame_m, glass_m, curtain_m, sill_m, seed):
    """A recessed double-hung window: reveal, frame, glass, net curtain behind, stone sill."""
    rv = pbr("RevealPlaster", (0.42, 0.4, 0.36), 0.85)
    parts = [box("RevealL", (-w / 2 - 0.02, 0.12, 0), (0.04, 0.24, h), rv), box("RevealR", (w / 2 + 0.02, 0.12, 0), (0.04, 0.24, h), rv),
             box("RevealT", (0, 0.12, h / 2 + 0.02), (w + 0.08, 0.24, 0.04), rv),
             box("Room", (0, 1.6, -0.2), (w + 1.5, 0.05, h + 1.0), pbr("RoomDark", (0.05, 0.045, 0.04), 0.9)),
             box("Glass", (0, 0.2, 0), (w - 0.06, 0.01, h - 0.06), glass_m),
             box("Curtain", (0, 0.3, 0), (w - 0.08, 0.01, h - 0.1), curtain_m),
             box("Sill", (0, -0.06, -h / 2 - 0.05), (w + 0.2, 0.18, 0.08), sill_m)]
    for dz in (-h / 2 + 0.03, 0.0, h / 2 - 0.03):
        parts.append(box("FrameH", (0, 0.19, dz), (w - 0.02, 0.05, 0.05), frame_m))
    for dx in (-w / 2 + 0.03, 0.0, w / 2 - 0.03):
        parts.append(box("FrameV", (dx, 0.19, 0), (0.05, 0.05, h - 0.02), frame_m))
    return join(parts, name)


def burlap_crate(name, size=(1.3, 1.0, 1.1)):
    """Large crate sewn into burlap: coarse weave, rope lashing both ways, rows of staples along the seams, a tag."""
    hes = bpy.data.materials.get("BurlapBig") or ph.texture("hessian_230", scale=0.65, name="BurlapBig", tint=(0.72, 0.6, 0.42))
    rope = bpy.data.materials.get("Rope") or ph.texture("hessian_380", scale=6.0, name="Rope", tint=(0.55, 0.45, 0.32))
    stm = pbr("StapleE", (0.7, 0.7, 0.72), 0.25, 1.0)
    sx, sy, sz = size
    parts = [box("Crate", (0, 0, 0), size, hes, bevel=0.05)]
    for dx in (-sx * 0.3, sx * 0.3):
        parts.append(cyl("RopeV", (dx, -sy / 2 - 0.008, 0), 0.012, sz + 0.02, rope, verts=8))
        parts.append(cyl("RopeV", (dx, sy / 2 + 0.008, 0), 0.012, sz + 0.02, rope, verts=8))
        parts.append(cyl("RopeT", (dx, 0, sz / 2 + 0.008), 0.012, sy + 0.02, rope, verts=8, rot=(math.radians(90), 0, 0)))
    for dy in (-sy * 0.25, sy * 0.25):
        parts.append(cyl("RopeH", (0, dy, sz / 2 + 0.01), 0.012, sx + 0.02, rope, verts=8, rot=(0, math.radians(90), 0)))
    for k in range(14):                              # staples along the top seam of the front face
        parts.append(box("Staple", (-sx / 2 + 0.06 + k * (sx - 0.12) / 13, -sy / 2 - 0.004, sz / 2 - 0.04), (0.018, 0.003, 0.003), stm))
    parts.append(box("Tag", (sx * 0.15, -sy / 2 - 0.01, sz * 0.12), (0.18, 0.004, 0.11), pbr("Tag", (0.82, 0.8, 0.72), 0.8)))
    return join(parts, name)


def frontage(cx, fy, width, floors, mat, unit, facing=1, bay=3.6, ww=1.35, wh=1.9):
    """A plaster frontage with true window recesses: piers and spandrels in front of a back wall, a window unit in each
    opening. facing=1: the front faces -Y (like the embassy); facing=-1: it faces +Y (across the street)."""
    n = int(width / bay)
    sgn = facing
    for f in range(1, floors + 1):
        box("FSpandrel", (cx, fy + sgn * 0.18, f * FH), (width, 0.4, FH - wh), mat)
    for k in range(n + 1):
        x = cx - width / 2 + k * bay
        box("FPier", (x, fy + sgn * 0.19, FH + (floors - 1) * FH / 2), (bay - ww, 0.4, (floors - 1) * FH), mat)
    box("FBack", (cx, fy + sgn * 1.75, floors * FH / 2), (width, 0.1, floors * FH), mat)
    for f in range(1, floors):
        for k in range(n):
            x = cx - width / 2 + (k + 0.5) * bay
            o = instance(unit, (x, fy, f * FH + FH / 2)); o.location = (x, fy, f * FH + FH / 2)
            if facing < 0:
                o.rotation_euler = (0, 0, math.pi)


def lattice(name, p0, p1, w, mat, n=None):
    """Steel lattice member from p0 to p1: four corner chords and zig-zag bracing (a real crane boom/mast look)."""
    p0 = Vector(p0); p1 = Vector(p1); d = p1 - p0; L = d.length
    n = n or max(3, int(L / w))
    q = d.normalized().to_track_quat('Z', 'Y')
    parts = []
    for sx in (-1, 1):
        for sy in (-1, 1):
            parts.append(cyl("Chord", (sx * w / 2, sy * w / 2, L / 2), 0.022, L, mat, verts=6))
    for k in range(n):
        z0 = k * L / n; z1 = (k + 1) * L / n
        for (a, b) in (((-1, -1), (1, -1)), ((1, -1), (1, 1)), ((1, 1), (-1, 1)), ((-1, 1), (-1, -1))):
            pa = Vector((a[0] * w / 2, a[1] * w / 2, z0)); pb = Vector((b[0] * w / 2, b[1] * w / 2, z1))
            m = (pa + pb) / 2; dd = pb - pa
            o = cyl("Brace", m.to_tuple(), 0.011, dd.length, mat, verts=5)
            o.rotation_mode = 'QUATERNION'; o.rotation_quaternion = dd.normalized().to_track_quat('Z', 'Y')
            parts.append(o)
    o = join(parts, name)
    o.rotation_mode = 'QUATERNION'; o.rotation_quaternion = q; o.location = p0
    return o


def build(variant=None):
    c = {"variant": variant}
    night = variant == "night"
    rng = np.random.default_rng(84)
    w = world_sky(sun_elev_deg=26, sun_rot_deg=150, strength=0.55, tint=(0.86, 0.9, 1.0), air=1.2, aerosol=1.8)
    w.node_tree.nodes["Sky Texture"].sun_disc = False          # the sun lamp does the sunlight (the disc burns out the facade)
    twp.cloud_sky(w, cover=0.55)
    if night:
        w.node_tree.nodes["Background"].inputs['Strength'].default_value = 0.012
    sn = bpy.data.lights.new("Sun", 'SUN'); sn.energy = 3.0 if not night else 0.0; sn.angle = math.radians(2.0); sn.color = (1.0, 0.93, 0.84)
    so = bpy.data.objects.new("Sun", sn); bpy.context.collection.objects.link(so)
    so.rotation_euler = (math.radians(64), 0, math.radians(-150))          # morning sun from the street side, raking
    # ---------------------------------------------------------------- the chancery
    brick = ph.texture("brick_wall_09", scale=0.55, name="Brick", tint=(0.92, 0.82, 0.76))
    st = stone("Limestone", (0.55, 0.52, 0.46))
    frame_m = pbr("WinFrameW", (0.62, 0.6, 0.55), 0.5)
    glass_m = pbr("WinGlassE", (0.03, 0.035, 0.04), 0.06, 0.0, **{'Coat Weight': 1.0, 'Coat Roughness': 0.02})
    curtain = pbr("NetCurtain", (0.55, 0.55, 0.52), 0.9)
    bay = BW / COLS; ww, wh = 1.35, 1.9
    unit = window_unit("WinUnit", ww, wh, frame_m, glass_m, curtain, st, 0)
    unit.location = (0, 0, -100)
    # piers and spandrels (true recesses for the windows)
    for k in range(COLS + 1):
        x = -BW / 2 + k * bay
        box("Pier", (x, 0.2, FH + (FLOORS - 1) * FH / 2), (bay - ww, 0.4, (FLOORS - 1) * FH), brick)
    for f in range(1, FLOORS + 1):
        z0 = f * FH
        box("Spandrel", (0, 0.19, z0), (BW, 0.4, FH - wh), brick)
    box("TopBand", (0, 0.19, FLOORS * FH + 0.15), (BW, 0.4, 0.5), brick)
    for f in range(1, FLOORS):
        z = f * FH + FH / 2
        for k in range(COLS):
            x = -BW / 2 + (k + 0.5) * bay
            o = instance(unit, (x, 0.0, z))
            o.location = (x, 0.0, z)
    box("BackWall", (0, 0.45, ROOF / 2), (BW, 0.1, ROOF), pbr("Inside", (0.08, 0.075, 0.07), 0.9))
    box("Body", (0, 8.4, ROOF / 2), (BW, 16, ROOF), brick)
    # rusticated stone ground floor with the entrance, cornice, parapet
    box("Base", (0, 0.1, FH / 2), (BW + 0.2, 0.6, FH), st)
    for k in range(9):
        box("Joint", (0, -0.205, 0.35 + k * 0.36), (BW + 0.2, 0.02, 0.02), pbr("Joint", (0.25, 0.24, 0.22), 0.9))
    for k in range(6):
        x = -BW / 2 + (k + 0.5) * BW / 6 if k not in (2, 3) else None
        if x is not None:
            box("GWin", (x, -0.21, FH * 0.55), (1.8, 0.05, 1.8), glass_m)
            box("GBars", (x, -0.24, FH * 0.55), (1.85, 0.03, 1.85), pbr("Bars", (0.05, 0.05, 0.05), 0.4, 0.8)) if False else None
    box("Entrance", (0, -0.21, 1.4), (3.0, 0.1, 2.8), pbr("Doors", (0.08, 0.06, 0.045), 0.5))
    box("Canopy", (0, -0.9, 3.0), (4.2, 1.6, 0.2), st)
    box("Cornice", (0, -0.1, ROOF - 0.2), (BW + 0.6, 1.0, 0.4), st, bevel=0.05)
    box("Parapet", (0, 0.05, ROOF + 0.5), (BW, 0.35, 1.0), brick)
    box("ParapetCap", (0, 0.05, ROOF + 1.02), (BW + 0.05, 0.45, 0.08), st)
    box("RoofDeck", (0, 8.2, ROOF + 0.1), (BW - 0.4, 16, 0.2), ph.texture("asphalt_02", scale=0.3, name="RoofFelt"))
    box("StairHouse", (-12, 9, ROOF + 1.6), (5, 4, 3.0), brick)
    # roof clutter: aerials and masts (the embassy roof bristled with them), vents, aircon boxes
    mast_m = pbr("Mast", (0.35, 0.36, 0.37), 0.4, 0.9)
    for k, (x, y, h_) in enumerate(((-6, 5, 7), (-2, 10, 9), (12, 6, 6), (16, 12, 10), (-18, 4, 5), (2, 13, 6))):
        cyl("Mast", (x, y, ROOF + h_ / 2), 0.05, h_, mast_m, verts=8)
        for j in range(3):
            box("Aerial", (x, y, ROOF + h_ * (0.6 + 0.15 * j)), (1.6 - 0.4 * j, 0.03, 0.03), mast_m, rot=(0, 0, k * 0.7))
        for a in range(3):
            ang = a * 2.1
            box("Guy", (x + 0.5 * h_ * 0.35 * math.cos(ang), y + 0.5 * h_ * 0.35 * math.sin(ang), ROOF + h_ * 0.35), (0.01, 0.01, h_ * 0.75), mast_m,
                rot=(-math.sin(ang) * 0.45, math.cos(ang) * 0.45, 0))
    for x, y in ((-8, 3.5), (10, 4.0), (14, 9)):
        ph.model("exterior_aircon_unit", loc=(x, y, ROOF + 0.2), rot_z=math.pi)
    # neighbours: grey and ochre plaster blocks either side
    # neighbours: Stalinist plaster blocks, rusticated base, heavy cornice, recessed windows (instanced units)
    for sx, col, h in ((-1, (0.6, 0.52, 0.4), 27.2), (1, (0.55, 0.54, 0.5), 30.6)):
        ph_ = stone(f"Plaster{sx}", col)
        cx = sx * (BW / 2 + 16.5)
        box("Neighbour", (cx, 9.85, h / 2), (32, 16, h), ph_)
        floors = int(h / FH)
        frontage(cx, 0.0, 32.4, floors, ph_, unit, facing=1)
        box("NCornice", (cx, -0.3, h - 0.3), (32.4, 0.9, 0.6), ph_, bevel=0.06)
        box("NBase", (cx, -0.12, FH / 2), (32, 0.3, FH), stone(f"NBase{sx}", (col[0] * 0.75, col[1] * 0.75, col[2] * 0.75)))
        for k in range(5):
            box("Shopfront", (cx - 12.8 + k * 6.4, -0.28, 1.5), (3.2, 0.05, 2.2), glass_m)
    # Moscow rooftops behind the embassy, fading into haze
    rng2 = np.random.default_rng(7)
    for k in range(40):
        x = rng2.uniform(-120, 120); y = rng2.uniform(30, 220); hh = rng2.uniform(14, 34)
        box("BackBlock", (x, y, hh / 2), (rng2.uniform(18, 40), rng2.uniform(12, 20), hh), stone(f"BackPl{k % 4}", [(0.6, 0.55, 0.45), (0.52, 0.52, 0.5), (0.58, 0.48, 0.4), (0.5, 0.47, 0.44)][k % 4]))
    haze((0, 120, 30), (300, 180, 60), density=0.0025, color=(0.78, 0.83, 0.92), anis=0.3)
    # flag on a short staff over the entrance (wave modifier: plays in any render)
    cyl("FlagStaff", (0, -1.4, 4.2), 0.04, 3.2, pbr("Staff", (0.7, 0.7, 0.7), 0.3, 1.0), rot=(math.radians(-35), 0, 0))
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=40, y_subdivisions=20, size=1, location=(0, 0, 0))
    fl = bpy.context.active_object; fl.name = "Flag"; fl.scale = (1.9, 1.0, 1)
    bpy.ops.object.transform_apply(scale=True)
    fl.rotation_euler = (math.radians(90), 0, 0); fl.location = (0.95, -2.3, 5.1)
    fl.data.materials.append(flag_material())
    wv = fl.modifiers.new("wave", 'WAVE'); wv.use_normal = False; wv.use_x = True; wv.use_y = False
    wv.height = 0.06; wv.width = 0.7; wv.speed = 0.06; wv.narrowness = 1.5; wv.start_position_x = -1.0; wv.time_offset = 0
    # ---------------------------------------------------------------- street: pavement, kerb, boulevard, trolley wires, lamps
    pave = ph.texture("concrete_pavers_02", scale=0.4, name="Pave")
    box("Pavement", (0, -3.2, -0.05), (200, 6.4, 0.2), pave)
    box("Kerb", (0, -6.4, 0.0), (200, 0.25, 0.22), st)
    box("Road", (0, ROAD_Y, -0.1), (200, 15, 0.1), ph.texture("asphalt_04", scale=0.25, name="Asphalt"))
    box("FarPavement", (0, ROAD_Y - 9.0, -0.05), (200, 3.0, 0.2), pave)
    # the far side of the boulevard: a long Stalinist frontage with recessed windows facing the embassy
    fp = stone("FarPlaster", (0.62, 0.55, 0.44)); fy = ROAD_Y - 10.5
    box("FarBlock", (0, fy - 8.85, 13.6), (200, 14, 27.2), fp)
    frontage(0.0, fy, 129.6, 8, fp, unit, facing=-1)
    box("FarCornice", (0, fy + 0.3, 27.0), (200, 0.9, 0.6), fp, bevel=0.06)
    box("FarBase", (0, fy + 0.12, FH / 2), (200, 0.3, FH), stone("FarBaseS", (0.45, 0.42, 0.36)))
    wire_m = pbr("Wire", (0.02, 0.02, 0.02), 0.4, 0.8)
    for dy in (-3.6, -3.0, 3.0, 3.6):
        cyl("TrolleyWire", (0, ROAD_Y + dy, WIRE_Z), 0.008, 200, wire_m, verts=6, rot=(0, math.radians(90), 0))
    for k in range(7):
        x = -45 + k * 15
        cyl("WirePole", (x, -6.9, 4.5), 0.09, 9.0, pbr("PoleGrey", (0.3, 0.31, 0.3), 0.5, 0.6), verts=12)
        cyl("Span", (x, ROAD_Y + 0.5, WIRE_Z + 0.3), 0.012, 15, wire_m, verts=6, rot=(math.radians(90), 0, 0))
    for k in range(7):                                   # Soviet concrete masts, arms reaching over the carriageway
        for y_, rz, sgn in ((-6.85, -math.pi / 2, -1), (ROAD_Y - 7.6, math.pi / 2, 1)):
            x_ = -45 + k * 15 + 7.5
            twp.soviet_lamp((x_, y_, 0.0), rot_z=rz, height=9.0, arm=2.4, lit=night)
            if night:
                sl = bpy.data.lights.new("Sodium", 'SPOT'); sl.energy = 2500; sl.spot_size = math.radians(110); sl.spot_blend = 0.7; sl.color = (1.0, 0.62, 0.32)
                so_ = bpy.data.objects.new("Sodium", sl); bpy.context.collection.objects.link(so_); so_.location = (x_, y_ + sgn * 2.65, 8.8)
    if night:                                           # lit offices: warm light behind a few windows, one typist at work
        for k in range(14):
            col = int(rng.integers(0, COLS)); fl_ = int(rng.integers(1, FLOORS))
            p_ = Vector((-BW / 2 + (col + 0.5) * BW / COLS, 1.2, fl_ * FH + FH / 2))
            l = area_light(p_.to_tuple(), (math.radians(90), 0, 0), 1.6, 60, (1.0, 0.78, 0.5)); l.visible_camera = False
        l = area_light((LIT.x, 1.3, LIT.z + 0.6), (math.radians(110), 0, 0), 1.2, 90, (1.0, 0.8, 0.55)); l.visible_camera = False
        ty = twp.person("NightTypist", 0.0, 40, "female_elegantsuit01", "ponytail01", hv=0.3, cval=0.55, hue=0.55, sat=0.2)
        twp.seat(ty, (LIT.x + 0.2, 1.15, LIT.z - FH / 2), math.pi / 2, lean=14)
        twp.ground(ty, LIT.z - FH / 2 + 0.02)
        c["night_typist"] = ty
        box("NightDesk", (LIT.x + 0.85, 1.15, LIT.z - FH / 2 + 0.75), (0.7, 1.2, 0.04), ph.texture("dark_wood", scale=1.0, name="NDesk"))
    # the militia booth at the gate, a fence of railings either side of the entrance
    booth = pbr("Booth", (0.4, 0.42, 0.38), 0.5)
    box("Booth", (-3.6, -4.8, 1.2), (1.2, 1.2, 2.4), booth, bevel=0.03)
    box("BoothGlass", (-3.6, -5.42, 1.6), (1.0, 0.02, 0.8), glass_m)
    box("BoothRoof", (-3.6, -4.8, 2.45), (1.4, 1.4, 0.12), booth)
    rail = pbr("Railing", (0.04, 0.04, 0.045), 0.45, 0.7)
    for sx in (-1, 1):
        for k in range(40):
            x = sx * (2.5 + k * 0.22)
            cyl("Bar", (x, -1.6, 0.9), 0.012, 1.8, rail, verts=6)
        box("RailTop", (sx * 6.9, -1.6, 1.8), (8.8, 0.05, 0.05), rail)
    peds = []
    for k, (nm, g, yrs, cl, hr, cv, hu) in enumerate((("PedA", 0.0, 55, "female_elegantsuit01", "bob01", 0.55, 0.08), ("PedB", 1.0, 40, "male_worksuit01", "short04", 0.45, 0.6),
                                                      ("PedC", 1.0, 62, "male_casualsuit04", "short02", 0.5, 0.1), ("PedD", 0.0, 30, "female_elegantsuit01", "long01", 0.6, 0.55))):
        peds.append(dict(h=twp.person(nm, g, yrs, cl, hr, hv=0.35, cval=cv, hue=hu, sat=0.25), x0=-34 + k * 9.0, y=-2.6 - 3.2 * (k % 2), d=1 if k % 2 else -1, v=1.1 + 0.1 * k))
    c["peds"] = peds
    militia = twp.person("Militia", 1.0, 30, "male_worksuit01", "short01", hv=0.25, cval=0.4, hue=0.3, sat=0.3)
    twp.stand(militia, (-4.6, -4.9, 0.0), math.radians(10))
    c["militia"] = militia
    # ---------------------------------------------------------------- traffic
    paints = [(0.55, 0.52, 0.45), (0.18, 0.24, 0.3), (0.62, 0.62, 0.6), (0.3, 0.12, 0.08), (0.12, 0.15, 0.13), (0.7, 0.66, 0.5)]
    traffic = []
    for k in range(7):
        lane = ROAD_Y + (2.2 if k % 2 == 0 else -2.2) + rng.uniform(-0.3, 0.3); d = 1 if lane > ROAD_Y else -1
        r, wh_ = V.saloon(f"Car{k}", paints[k % len(paints)], big=(k % 3 == 1))
        r.rotation_euler = (0, 0, 0 if d > 0 else math.pi)
        traffic.append(dict(o=r, w=wh_, y=lane, d=d, x0=float(rng.uniform(-70, 40)), v=float(rng.uniform(9, 13)), r=0.31))
    bus, bw = V.trolleybus("Trolley")
    traffic.append(dict(o=bus, w=bw, y=ROAD_Y + 3.3, d=1, x0=-28.0, v=6.5, r=0.5))
    c["traffic"] = traffic
    # ---------------------------------------------------------------- the hoist on the roof, its cable, the crate, workers
    post_m = pbr("HoistSteel", (0.22, 0.24, 0.22), 0.45, 0.8)
    yel = pbr("HoistPaint", (0.3, 0.33, 0.27), 0.55, 0.5)
    # a slewing roof derrick: lattice mast on a steel base frame with ballast, a lattice boom over the parapet,
    # a sheave at the boom tip, guy cables, and an electric winch with its drum on the back of the base
    box("DerrickBase", (JIB.x, JIB.y + 0.6, ROOF + 0.3), (2.2, 2.6, 0.2), post_m)
    for dx in (-0.9, 0.9):
        box("BaseRail", (JIB.x + dx, JIB.y + 0.6, ROOF + 0.45), (0.16, 2.6, 0.16), post_m)
    for k in range(4):
        box("Ballast", (JIB.x - 0.6 + (k % 2) * 1.2, JIB.y + 1.45 + (k // 2) * 0.0, ROOF + 0.62 + (k // 2) * 0.3), (0.55, 0.5, 0.28),
            ph.texture("concrete_floor_02", scale=1.0, name="BallastConc"))
    lattice("Mast", (JIB.x, JIB.y, ROOF + 0.4), (JIB.x, JIB.y, ROOF + 2.6), 0.35, yel)
    jib = bpy.data.objects.new("Jib", None); bpy.context.collection.objects.link(jib)
    jib.location = (JIB.x, JIB.y, ROOF + 2.5)
    boom = lattice("Boom", (0, 0.4, 0.0), (0, -3.15, -0.1), 0.28, yel)
    tie = cyl("Tie", (0, -1.3, 0.6), 0.012, 3.4, post_m, verts=6, rot=(math.radians(-73), 0, 0))
    for o in (boom, tie, cyl("Sheave", (0, -3.05, -0.22), 0.16, 0.06, post_m, verts=24, rot=(0, math.radians(90), 0)),
              cyl("SheaveCheekL", (0.05, -3.05, -0.2), 0.2, 0.012, yel, verts=24, rot=(0, math.radians(90), 0)),
              cyl("SheaveCheekR", (-0.05, -3.05, -0.2), 0.2, 0.012, yel, verts=24, rot=(0, math.radians(90), 0)),
              cyl("Apex", (0, 0, 0.75), 0.06, 0.7, yel, verts=8)):
        o.parent = jib
    box("WinchMotor", (JIB.x + 0.5, JIB.y + 1.0, ROOF + 0.75), (0.45, 0.5, 0.42), pbr("Motor", (0.2, 0.25, 0.32), 0.45, 0.4), bevel=0.04)
    c["drum"] = cyl("WinchDrum", (JIB.x - 0.25, JIB.y + 1.0, ROOF + 0.75), 0.18, 0.6, post_m, verts=24, rot=(0, math.radians(90), 0))
    for a in (0.7, 2.4):
        cyl("Guy", (JIB.x + 1.6 * math.cos(a), JIB.y + 1.6 * math.sin(a), ROOF + 1.45), 0.01, 3.5, post_m, verts=6,
            rot=(-math.sin(a) * 0.95, math.cos(a) * 0.95, 0))
    c["jib"] = jib
    cable = cyl("Cable", (0, 0, -0.5), 0.012, 1.0, pbr("CableSteel", (0.25, 0.25, 0.26), 0.35, 1.0), verts=8)
    cable.data.transform(Matrix.Translation((0, 0, 0.5)))           # origin at the top: scale z = length downward
    cable.location = (0, 0, 0); cable.rotation_euler = (math.radians(180), 0, 0)
    c["cable"] = cable
    crate = burlap_crate("BurlapCrate")
    c["crate"] = crate
    hook = join([cyl("HookBlock", (0, 0, 0.12), 0.08, 0.2, post_m, verts=16), box("Sling", (0, 0, -0.25), (0.02, 0.6, 0.5), pbr("Sling", (0.4, 0.3, 0.12), 0.8))], "HookBlock")
    c["hook"] = hook
    workers = []
    for k, (nm, cl) in enumerate((("WorkerA", "male_worksuit01"), ("WorkerB", "male_worksuit01"))):
        w = twp.person(nm, 1.0, 35 + 10 * k, cl, "short03" if k else "short01", hv=0.3, cval=0.28 + 0.1 * k, hue=0.58, sat=0.12)
        workers.append(w)
    c["workers"] = workers
    tr, twh, doors = V.truck("Truck")
    tr.location = TRUCK
    c["truck"] = tr; c["truck_w"] = twh; c["doors"] = doors
    seal = join([cyl("SealWire", (0, 0, 0), 0.002, 0.12, pbr("SealWireM", (0.6, 0.6, 0.62), 0.3, 1.0), verts=6),
                 cyl("SealLead", (0, 0, -0.07), 0.012, 0.012, pbr("Lead", (0.42, 0.43, 0.45), 0.5, 0.8), verts=16, rot=(math.radians(90), 0, 0))], "Seal")
    c["seal"] = seal
    sealer = twp.person("Sealer", 1.0, 47, "male_casualsuit02", "short04", hv=0.45, cval=0.5, hue=0.6, sat=0.1)
    c["sealer"] = sealer
    animate(c, 0.0, "street_push")
    return c


def flag_material():
    """Generic stripes-and-canton flag (procedural; no seal, no text)."""
    m = bpy.data.materials.new("Flag"); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; p = N["Principled BSDF"]
    uv = N.new("ShaderNodeTexCoord"); sp = N.new("ShaderNodeSeparateXYZ"); L.new(uv.outputs['UV'], sp.inputs[0])
    st = N.new("ShaderNodeMath"); st.operation = 'MULTIPLY'; st.inputs[1].default_value = 6.5; L.new(sp.outputs[1], st.inputs[0])
    fr = N.new("ShaderNodeMath"); fr.operation = 'FRACT'; L.new(st.outputs[0], fr.inputs[0])
    red = N.new("ShaderNodeMath"); red.operation = 'GREATER_THAN'; red.inputs[1].default_value = 0.5; L.new(fr.outputs[0], red.inputs[0])
    cx = N.new("ShaderNodeMath"); cx.operation = 'LESS_THAN'; cx.inputs[1].default_value = 0.4; L.new(sp.outputs[0], cx.inputs[0])
    cy = N.new("ShaderNodeMath"); cy.operation = 'GREATER_THAN'; cy.inputs[1].default_value = 0.46; L.new(sp.outputs[1], cy.inputs[0])
    can = N.new("ShaderNodeMath"); can.operation = 'MULTIPLY'; L.new(cx.outputs[0], can.inputs[0]); L.new(cy.outputs[0], can.inputs[1])
    m1 = N.new("ShaderNodeMix"); m1.data_type = 'RGBA'; L.new(red.outputs[0], m1.inputs['Factor'])
    m1.inputs[6].default_value = (0.75, 0.74, 0.7, 1); m1.inputs[7].default_value = (0.42, 0.05, 0.05, 1)
    m2 = N.new("ShaderNodeMix"); m2.data_type = 'RGBA'; L.new(can.outputs[0], m2.inputs['Factor'])
    L.new(m1.outputs[2], m2.inputs[6]); m2.inputs[7].default_value = (0.06, 0.08, 0.2, 1)
    L.new(m2.outputs[2], p.inputs['Base Color']); p.inputs['Roughness'].default_value = 0.85
    p.inputs['Sheen Weight'].default_value = 0.5
    return m


# ============================================================================ animation
def move_traffic(c, sec):
    for tr in c["traffic"]:
        x = tr["x0"] + tr["d"] * tr["v"] * sec
        x = ((x + 90) % 180) - 90
        tr["o"].location = (x, tr["y"], 0.0)
        V.roll(tr["w"], tr["v"] * sec, tr["r"])


def hoist(c, sec, lift):
    """lift: crate height above the pavement (m). The jib slews out over the street side, then back in."""
    jib = c["jib"]
    swing = c.get("swing", 0.0)
    jib.rotation_euler = (0, 0, swing)
    bpy.context.view_layer.update()
    sheave = jib.matrix_world @ Vector((0, -3.05, -0.38))
    crate = c["crate"]; hook = c["hook"]
    top = Vector((sheave.x, sheave.y, lift + 1.1 + 0.5))
    sway = 0.04 * math.sin(sec * 1.7)
    hook.location = top + Vector((sway, 0, 0)); crate.location = top + Vector((sway, 0, -1.1))
    crate.rotation_euler = (0, 0, 0.05 * math.sin(sec * 0.9))
    cab = c["cable"]; cab.location = sheave; L = max(0.05, sheave.z - hook.location.z - 0.22)
    d = (hook.location + Vector((0, 0, 0.22))) - sheave
    cab.scale = (1, 1, d.length); cab.rotation_euler = (0, 0, 0)
    cab.rotation_mode = 'QUATERNION'; cab.rotation_quaternion = (-d).normalized().to_track_quat('-Z', 'Y') if False else d.normalized().to_track_quat('Z', 'Y')


def truck_shot(c, sec, shot):
    from human import reach, fingers_curl
    tr = c["truck"]; sealer = c["sealer"]
    on = shot in ("trailer_seal", "truck_leave")
    twp.hide(twp.person_objs(sealer), shot != "trailer_seal")
    rear = TRUCK + Vector((-3.85, 0, 0))
    if shot == "trailer_seal":
        close = ease(min(1.0, sec / 1.3))
        for d, sy in zip(c["doors"], (-1, 1)):
            d.rotation_euler = (0, 0, -sy * math.radians(105) * (1 - close))
        tr.location = TRUCK
        twp.stand(sealer, (rear.x - 0.75, rear.y + 0.35, 0.0), math.pi / 2 + 0.25)      # faces +X, the doors
        sp = rear + Vector((-0.06, 0.1, 1.35))
        c["seal"].location = sp if sec > 1.6 else Vector((0, 0, -50))
        crimp = max(0.0, math.sin(math.pi * min(1.0, max(0.0, (sec - 2.4) / 0.6))))
        reach(sealer, "R", sp + Vector((-0.08, -0.02, 0.03 - 0.02 * crimp)), Vector((-0.3, -0.8, -0.6)), Vector((1, 0, -0.2)))
        reach(sealer, "L", sp + Vector((-0.06, 0.12, 0.0)), Vector((-0.3, 0.8, -0.6)), Vector((1, 0, 0)))
        fingers_curl(sealer, 45 + 30 * crimp, thumb=25)
    elif shot == "truck_leave":
        for d in c["doors"]:
            d.rotation_euler = (0, 0, 0)
        go = max(0.0, sec - 0.8)
        dist = 0.5 * 1.6 * go * go
        tr.location = TRUCK + Vector((dist, 0, 0)); V.roll(c["truck_w"], dist, 0.5)
        c["seal"].location = tr.location + Vector((-3.86, 0.1, 1.35))
    else:
        tr.location = Vector((0, 0, -60))
    return on


def animate(c, sec, shot):
    truck_shot(c, sec, shot)
    from human import pose_walk
    for p in c["peds"]:
        h = p["h"]; x = p["x0"] + p["d"] * p["v"] * sec
        twp.upright(h); pose_walk(h, (abs(x) / 1.35) % 1.0, stride=24, arm_swing=18)
        twp.face(h, math.atan2(p["d"], 0.0)); h.arm.location = (x, p["y"], 0); twp.ground(h, 0.0)
        twp.hide(twp.person_objs(h), shot not in ("street_push", "truck_leave"))
    if "drum" in c:
        c["drum"].rotation_euler = (sec * 2.0, math.radians(90), 0)
    move_traffic(c, sec)
    for w in c["workers"]:
        twp.hide(twp.person_objs(w), shot != "roof_swing")
    if shot == "street_push":
        c["swing"] = 0.0; hoist(c, sec, ROOF + 0.4)
    elif shot == "crane_up":
        c["swing"] = math.radians(-35) * ease(min(1.0, max(0.0, (sec - 0.8) / 3.0))); hoist(c, sec, ROOF + 0.6)
    elif shot == "hoist_street":
        c["swing"] = 0.0; hoist(c, sec, 17.0 + 1.0 * sec)
    elif shot == "hoist_rise":
        c["swing"] = 0.0; hoist(c, sec, 9.0 + 1.1 * sec)
    elif shot == "roof_swing":
        k = ease(min(1.0, max(0.0, (sec - 0.6) / 3.6)))
        c["swing"] = math.radians(-180) * k                         # slews the crate in over the parapet
        hoist(c, sec, ROOF + 1.5 - 1.2 * ease(max(0.0, (sec - 3.8) / 1.2)))
        from human import reach, fingers_curl
        cr = c["crate"].location
        for k_, w in enumerate(c["workers"]):
            off = Vector((-0.95, 0.1, 0)) if k_ == 0 else Vector((0.95, 0.25, 0))
            base = Vector((cr.x, cr.y, 0)) + off
            base.y = max(base.y, JIB.y - 2.6)                       # stay on the roof
            d = cr - Vector((base.x, base.y, cr.z)); ang = math.atan2(d.x, -d.y)
            twp.stand(w, (base.x, base.y, ROOF + 0.2), ang)
            side = Vector((math.cos(ang), math.sin(ang), 0))
            for sd, sg in (("L", 1), ("R", -1)):
                tgt = cr + Vector((0, 0, 0.1)) - (cr - w.arm.location).normalized() * 0.5 + side * 0.18 * sg
                reach(w, sd, tgt, Vector((sg * side.x, sg * side.y, -0.7)), cr - w.arm.location)
            fingers_curl(w, 50, thumb=25)
    bpy.context.view_layer.update()


def anim(shot):
    return lambda c, t: animate(c, t * DUR[shot], shot)


def cam_street(c, t):
    e = ease(t)
    a = Vector((-34.0, -5.0, 1.75)); b = Vector((-31.0, -5.6, 1.85))       # down the pavement, three-quarter on the facade
    return (a.lerp(b, e), Vector((2.0, -1.0, 8.5)).lerp(Vector((3.0, -1.0, 9.0)), e), 30)


def cam_crane(c, t):
    e = ease(t)
    a = Vector((-4.0, -14.0, 12.0)); b = Vector((-1.5, -13.0, ROOF + 6.0))
    ta = Vector((2.0, 0, 13.0)); tb = Vector((JIB.x, JIB.y, ROOF + 1.8))
    return (a.lerp(b, e), ta.lerp(tb, e), 32)


def cam_hoist(c, t):
    e = ease(t)
    cr = c["crate"].location
    a = Vector((JIB.x - 5.0, -7.0, 5.0)); b = Vector((JIB.x - 4.6, -6.6, 6.0))
    return (a.lerp(b, e), Vector((JIB.x - 1.0, -2.0, cr.z + 1.0)), 30)


def cam_roof(c, t):
    e = ease(t)
    a = Vector((JIB.x - 5.0, 8.5, ROOF + 1.9)); b = Vector((JIB.x - 4.4, 7.8, ROOF + 1.85))
    return (a.lerp(b, e), Vector((JIB.x, JIB.y - 0.8, ROOF + 1.4)), 30)


def cam_seal(c, t):
    e = ease(t); r = TRUCK + Vector((-3.85, 0, 0))
    return (r + Vector((-4.2, -2.6, 1.35)).lerp(Vector((-3.8, -2.3, 1.35)), e), r + Vector((0.0, 0.0, 1.5)), 35)


def cam_leave(c, t):
    e = ease(t)
    return (Vector((-1.5, -3.6, 1.5)).lerp(Vector((-1.2, -3.8, 1.55)), e), Vector((10.0, -8.3, 1.8)).lerp(Vector((16.0, -8.3, 1.8)), e), 28)


def cam_hoist_street(c, t):
    e = ease(t)
    return (Vector((JIB.x + 3.5, -9.0, 1.7)).lerp(Vector((JIB.x + 3.2, -8.6, 1.7)), e), Vector((JIB.x - 0.4, -1.6, 21.0)), 24)


def cam_window_night(c, t):
    e = ease(t)
    a = LIT + Vector((-1.2, -4.5, 0.2)); b = LIT + Vector((-6.0, -20.0, -4.0))
    return (a.lerp(b, e), LIT + Vector((0.0, 0.0, -0.2)).lerp(LIT + Vector((0, 0, -2.0)), e), 32)


MOVES = {
    "window_night": dict(kind="anim", dof=None, cam=cam_window_night, anim=anim("window_night")),
    "hoist_street": dict(kind="anim", dof=None, cam=cam_hoist_street, anim=anim("hoist_street")),
    "trailer_seal": dict(kind="anim", dof=3.0, cam=cam_seal, focus=lambda c, t: TRUCK + Vector((-3.85, 0.1, 1.35)), anim=anim("trailer_seal")),
    "truck_leave": dict(kind="anim", dof=None, cam=cam_leave, anim=anim("truck_leave")),
    "street_push": dict(kind="anim", dof=None, cam=cam_street, anim=anim("street_push")),
    "crane_up": dict(kind="anim", dof=None, cam=cam_crane, anim=anim("crane_up")),
    "hoist_rise": dict(kind="anim", dof=None, cam=cam_hoist, anim=anim("hoist_rise")),
    "roof_swing": dict(kind="anim", dof=4.0, cam=cam_roof, focus=lambda c, t: c["crate"].location, anim=anim("roof_swing")),
}
