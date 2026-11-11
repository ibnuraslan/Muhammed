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
import vehicles as V

EXPOSURE = -0.3
LEAD = 2.5
DUR = {"street_push": LEAD + 3.0, "crane_up": 4.5, "hoist_rise": 4.5, "roof_swing": 5.0}
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


def burlap_crate(name, size=(0.95, 0.75, 0.85)):
    hes = ph.texture("hessian_230", scale=2.0, name="Burlap", tint=(0.78, 0.66, 0.5))
    rope = pbr("Strap", (0.32, 0.27, 0.2), 0.8)
    sx, sy, sz = size
    parts = [box("Crate", (0, 0, 0), size, hes, bevel=0.03)]
    for dx in (-sx * 0.3, sx * 0.3):
        parts.append(box("StrapV", (dx, 0, 0), (0.05, sy + 0.012, sz + 0.012), rope))
    parts.append(box("StrapH", (0, 0, 0), (sx + 0.012, sy + 0.012, 0.05), rope))
    parts.append(box("Tag", (sx * 0.15, -sy / 2 - 0.008, sz * 0.15), (0.16, 0.004, 0.1), pbr("Tag", (0.82, 0.8, 0.72), 0.8)))
    return join(parts, name)


def build(variant=None):
    c = {}
    rng = np.random.default_rng(84)
    w = world_sky(sun_elev_deg=26, sun_rot_deg=150, strength=0.55, tint=(0.86, 0.9, 1.0), air=1.2, aerosol=1.8)
    w.node_tree.nodes["Sky Texture"].sun_disc = False          # the sun lamp does the sunlight (the disc burns out the facade)
    sn = bpy.data.lights.new("Sun", 'SUN'); sn.energy = 3.0; sn.angle = math.radians(2.0); sn.color = (1.0, 0.93, 0.84)
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
    for sx, col, h in ((-1, (0.52, 0.47, 0.38), 24), (1, (0.46, 0.46, 0.44), 30)):
        box("Neighbour", (sx * (BW / 2 + 16.5), 8, h / 2), (32, 16, h), stone("Plaster", col))
        for f in range(1, int(h / 3.2)):
            for k in range(9):
                box("NWin", (sx * (BW / 2 + 3.5 + k * 3.3), -0.03, f * 3.2 + 0.4), (1.3, 0.05, 1.7), glass_m)
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
    box("FarBlock", (0, ROAD_Y - 18.0, 12), (200, 14, 24), stone("FarPlaster", (0.48, 0.44, 0.38)))
    wire_m = pbr("Wire", (0.02, 0.02, 0.02), 0.4, 0.8)
    for dy in (-3.6, -3.0, 3.0, 3.6):
        cyl("TrolleyWire", (0, ROAD_Y + dy, WIRE_Z), 0.008, 200, wire_m, verts=6, rot=(0, math.radians(90), 0))
    for k in range(7):
        x = -45 + k * 15
        cyl("WirePole", (x, -6.9, 4.5), 0.09, 9.0, pbr("PoleGrey", (0.3, 0.31, 0.3), 0.5, 0.6), verts=12)
        cyl("Span", (x, ROAD_Y + 0.5, WIRE_Z + 0.3), 0.012, 15, wire_m, verts=6, rot=(math.radians(90), 0, 0))
    for k in range(6):
        twp.model_fit("street_lamp_01", (-37 + k * 15, -6.0, 0.0), rot_z=math.pi / 2, height=8.0)
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
    militia = twp.person("Militia", 1.0, 30, "male_worksuit01", "short01", hv=0.25, cval=0.22, hue=0.33, sat=0.25)
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
    yel = pbr("HoistPaint", (0.26, 0.3, 0.24), 0.55, 0.4)
    cyl("HoistPost", (JIB.x, JIB.y, ROOF + 1.3), 0.12, 2.4, post_m, verts=16)
    box("HoistBase", (JIB.x, JIB.y + 0.4, ROOF + 0.35), (1.6, 1.8, 0.5), post_m, bevel=0.03)
    box("Counterweight", (JIB.x, JIB.y + 1.0, ROOF + 0.85), (0.9, 0.7, 0.5), pbr("Weights", (0.12, 0.12, 0.12), 0.6))
    jib = bpy.data.objects.new("Jib", None); bpy.context.collection.objects.link(jib)
    jib.location = (JIB.x, JIB.y, ROOF + 2.5)
    for o in (box("JibBeam", (0, -1.4, 0), (0.22, 3.6, 0.3), yel, bevel=0.01),
              box("JibTie", (0, -0.4, 0.55), (0.06, 2.2, 0.06), post_m, rot=(math.radians(-22), 0, 0)),
              cyl("Sheave", (0, -3.05, -0.22), 0.16, 0.08, post_m, verts=24, rot=(0, math.radians(90), 0)),
              box("Winch", (0, 0.5, -0.35), (0.5, 0.6, 0.45), yel, bevel=0.02)):
        o.parent = jib
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
    top = Vector((sheave.x, sheave.y, lift + 0.95 + 0.5))
    sway = 0.04 * math.sin(sec * 1.7)
    hook.location = top + Vector((sway, 0, 0)); crate.location = top + Vector((sway, 0, -0.95))
    crate.rotation_euler = (0, 0, 0.05 * math.sin(sec * 0.9))
    cab = c["cable"]; cab.location = sheave; L = max(0.05, sheave.z - hook.location.z - 0.22)
    d = (hook.location + Vector((0, 0, 0.22))) - sheave
    cab.scale = (1, 1, d.length); cab.rotation_euler = (0, 0, 0)
    cab.rotation_mode = 'QUATERNION'; cab.rotation_quaternion = (-d).normalized().to_track_quat('-Z', 'Y') if False else d.normalized().to_track_quat('Z', 'Y')


def animate(c, sec, shot):
    move_traffic(c, sec)
    for w in c["workers"]:
        twp.hide(twp.person_objs(w), shot != "roof_swing")
    if shot == "street_push":
        c["swing"] = 0.0; hoist(c, sec, ROOF + 0.4)
    elif shot == "crane_up":
        c["swing"] = math.radians(-35) * ease(min(1.0, max(0.0, (sec - 0.8) / 3.0))); hoist(c, sec, ROOF + 0.6)
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
    a = Vector((-3.0, ROAD_Y - 8.5, 1.55)); b = Vector((-2.4, ROAD_Y - 5.5, 1.75))
    return (a.lerp(b, e), Vector((0.5, 0, 5.5)).lerp(Vector((0.6, 0, 6.5)), e), 24)


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


MOVES = {
    "street_push": dict(kind="anim", dof=None, cam=cam_street, anim=anim("street_push")),
    "crane_up": dict(kind="anim", dof=None, cam=cam_crane, anim=anim("crane_up")),
    "hoist_rise": dict(kind="anim", dof=None, cam=cam_hoist, anim=anim("hoist_rise")),
    "roof_swing": dict(kind="anim", dof=4.0, cam=cam_roof, focus=lambda c, t: c["crate"].location, anim=anim("roof_swing")),
}
