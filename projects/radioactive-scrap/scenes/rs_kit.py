"""Shared building blocks for "They Paid $30 for Radioactive Scrap" (Istanbul, winter 1998-99).

  ph_mat(id, scale, fallback)   Poly Haven texture with a plain fallback colour if the download fails
  container(name)               a grey lead-shielded transport container (drum in a steel frame, wooden skids)
  truck(name, col)              a 1990s light truck with drop sides (no badges)
  excavator(name)               tracked excavator; rig: c["ex"]["swing"/"boom"/"stick"/"tool"] pivot empties
  house(...)                    low plastered İkitelli house with a tiled roof, windows and a chimney
  person(...)                   unnamed MakeHuman figure in dark winter clothing
  sparks(...)                   cutting-torch sparks: N tiny emissive streaks posed per frame (bakeable)
  trefoil_material()            the three-blade radiation mark (yellow/black), drawn procedurally
"""
import math
import numpy as np
import bpy
from mathutils import Vector, Matrix, Euler
from kit import pbr, box, cyl, instance, join, emissive, glass
import ph


# ============================================================================ materials
def ph_mat(aid, scale=1.0, fallback=(0.3, 0.3, 0.3), rough=0.8, tint=None, name=None):
    try:
        return ph.texture(aid, scale=scale, tint=tint, name=name or aid)
    except Exception as e:
        print("[rs_kit] texture fallback", aid, e, flush=True)
        return pbr(name or aid, fallback, rough)


def ph_model(aid, loc=(0, 0, 0), rot_z=0.0, scale=1.0):
    try:
        return ph.model(aid, loc=loc, rot_z=rot_z, scale=scale)
    except Exception as e:
        print("[rs_kit] model missing", aid, e, flush=True)
        return None, []


def noisy(name, col, rough=0.7, metal=0.0, dirt=0.5, scale=3.0, dark=0.55):
    """Base colour broken up by noise (grime / rust patches)."""
    m = pbr(name, col, rough, metal)
    N = m.node_tree.nodes; L = m.node_tree.links; p = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord")
    n = N.new("ShaderNodeTexNoise"); n.inputs['Scale'].default_value = scale; n.inputs['Detail'].default_value = 8
    L.new(tc.outputs['Object'], n.inputs['Vector'])
    cr = N.new("ShaderNodeValToRGB"); cr.color_ramp.elements[0].position = 0.35; cr.color_ramp.elements[1].position = 0.7
    cr.color_ramp.elements[0].color = (col[0] * dark, col[1] * dark, col[2] * dark, 1); cr.color_ramp.elements[1].color = (*col, 1)
    L.new(n.outputs['Fac'], cr.inputs['Fac'])
    mx = N.new("ShaderNodeMix"); mx.data_type = 'RGBA'; mx.inputs['Factor'].default_value = dirt
    mx.inputs[6].default_value = (*col, 1); L.new(cr.outputs['Color'], mx.inputs[7])
    L.new(mx.outputs[2], p.inputs['Base Color'])
    return m


def rust_mat(name="Rust", base=(0.22, 0.09, 0.04), scale=4.0):
    """Rusted steel: orange-brown rust over dark steel, rough."""
    m = pbr(name, base, 0.85, 0.3)
    N = m.node_tree.nodes; L = m.node_tree.links; p = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord"); oi = N.new("ShaderNodeObjectInfo")
    n = N.new("ShaderNodeTexNoise"); n.inputs['Scale'].default_value = scale; n.inputs['Detail'].default_value = 10; n.inputs['Roughness'].default_value = 0.65
    L.new(tc.outputs['Object'], n.inputs['Vector'])
    cr = N.new("ShaderNodeValToRGB")
    cr.color_ramp.elements[0].position = 0.4; cr.color_ramp.elements[0].color = (0.05, 0.045, 0.04, 1)
    cr.color_ramp.elements[1].position = 0.62; cr.color_ramp.elements[1].color = (*base, 1)
    L.new(n.outputs['Fac'], cr.inputs['Fac'])
    hs = N.new("ShaderNodeHueSaturation"); L.new(cr.outputs['Color'], hs.inputs['Color'])
    vv = N.new("ShaderNodeMath"); vv.operation = 'MULTIPLY_ADD'; vv.inputs[1].default_value = 0.7; vv.inputs[2].default_value = 0.65
    L.new(oi.outputs['Random'], vv.inputs[0]); L.new(vv.outputs[0], hs.inputs['Value'])
    L.new(hs.outputs['Color'], p.inputs['Base Color'])
    mt = N.new("ShaderNodeMath"); mt.operation = 'SUBTRACT'; mt.inputs[0].default_value = 0.7; L.new(n.outputs['Fac'], mt.inputs[1])
    L.new(mt.outputs[0], p.inputs['Metallic'])
    b = N.new("ShaderNodeBump"); b.inputs['Strength'].default_value = 0.3; L.new(n.outputs['Fac'], b.inputs['Height']); L.new(b.outputs['Normal'], p.inputs['Normal'])
    return m


def painted_steel(name, col, rough=0.5, wear=0.35):
    m = noisy(name, col, rough, 0.2, dirt=wear, scale=5.0, dark=0.5)
    return m


def trefoil_material(name="Trefoil", fade=0.0):
    """Radiation trefoil on a yellow disc, in the object's local XZ plane (a plane facing -Y), unit radius 0.5."""
    m = bpy.data.materials.new(name); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; p = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord"); sep = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs['UV'], sep.inputs[0])
    # centred coords u,v in [-1,1]
    def mad(a, mul, add):
        n = N.new("ShaderNodeMath"); n.operation = 'MULTIPLY_ADD'; n.inputs[1].default_value = mul; n.inputs[2].default_value = add
        L.new(a, n.inputs[0]); return n.outputs[0]
    u = mad(sep.outputs[0], 2, -1); v = mad(sep.outputs[1], 2, -1)
    cx = N.new("ShaderNodeCombineXYZ"); L.new(u, cx.inputs[0]); L.new(v, cx.inputs[1])
    ln = N.new("ShaderNodeVectorMath"); ln.operation = 'LENGTH'; L.new(cx.outputs[0], ln.inputs[0]); r = ln.outputs['Value']
    at = N.new("ShaderNodeMath"); at.operation = 'ARCTAN2'; L.new(v, at.inputs[0]); L.new(u, at.inputs[1])
    # three blades: sin(3*(theta - 90deg)) > 0.5 approximates 60-degree blades, one pointing up
    a3 = N.new("ShaderNodeMath"); a3.operation = 'MULTIPLY_ADD'; a3.inputs[1].default_value = 3.0; a3.inputs[2].default_value = -math.pi / 2 * 3 + math.pi / 2
    L.new(at.outputs[0], a3.inputs[0])
    sn = N.new("ShaderNodeMath"); sn.operation = 'COSINE'; L.new(a3.outputs[0], sn.inputs[0])
    blade = N.new("ShaderNodeMath"); blade.operation = 'GREATER_THAN'; blade.inputs[1].default_value = 0.5; L.new(sn.outputs[0], blade.inputs[0])
    rin = N.new("ShaderNodeMath"); rin.operation = 'GREATER_THAN'; rin.inputs[1].default_value = 0.3; L.new(r, rin.inputs[0])
    rout = N.new("ShaderNodeMath"); rout.operation = 'LESS_THAN'; rout.inputs[1].default_value = 0.78; L.new(r, rout.inputs[0])
    ring = N.new("ShaderNodeMath"); ring.operation = 'MULTIPLY'; L.new(rin.outputs[0], ring.inputs[0]); L.new(rout.outputs[0], ring.inputs[1])
    bl = N.new("ShaderNodeMath"); bl.operation = 'MULTIPLY'; L.new(ring.outputs[0], bl.inputs[0]); L.new(blade.outputs[0], bl.inputs[1])
    hub = N.new("ShaderNodeMath"); hub.operation = 'LESS_THAN'; hub.inputs[1].default_value = 0.2; L.new(r, hub.inputs[0])
    black = N.new("ShaderNodeMath"); black.operation = 'MAXIMUM'; L.new(bl.outputs[0], black.inputs[0]); L.new(hub.outputs[0], black.inputs[1])
    disc = N.new("ShaderNodeMath"); disc.operation = 'LESS_THAN'; disc.inputs[1].default_value = 0.98; L.new(r, disc.inputs[0])
    col = N.new("ShaderNodeMix"); col.data_type = 'RGBA'; L.new(black.outputs[0], col.inputs['Factor'])
    col.inputs[6].default_value = (0.75, 0.55, 0.04, 1); col.inputs[7].default_value = (0.015, 0.012, 0.01, 1)
    # scuffed: grime noise darkens and desaturates it
    gn = N.new("ShaderNodeTexNoise"); gn.inputs['Scale'].default_value = 9; gn.inputs['Detail'].default_value = 10; L.new(tc.outputs['UV'], gn.inputs['Vector'])
    gm = N.new("ShaderNodeMix"); gm.data_type = 'RGBA'; gm.blend_type = 'MULTIPLY'; gm.inputs['Factor'].default_value = 0.6
    L.new(col.outputs[2], gm.inputs[6]); L.new(gn.outputs['Color'], gm.inputs[7])
    L.new(gm.outputs[2], p.inputs['Base Color'])
    L.new(disc.outputs[0], p.inputs['Alpha'])
    p.inputs['Roughness'].default_value = 0.6
    return m


# ============================================================================ props
def container(name="Container", with_crate=False, trefoil=True, open_=False):
    """Cobalt transport package: a grey steel drum (lead inside) with ribs and lugs, in a square steel frame on skids.
    Footprint ~1.0 x 1.0 m, ~1.05 m tall. Origin at the floor centre. Returns (object, parts dict)."""
    grey = painted_steel(name + "Grey", (0.32, 0.33, 0.33), 0.55, 0.45)
    dark = painted_steel(name + "Frame", (0.14, 0.15, 0.15), 0.5, 0.5)
    lead = noisy(name + "Lead", (0.23, 0.235, 0.25), 0.45, 0.6, dirt=0.4, scale=8)
    parts = []
    body = cyl(name + "Drum", (0, 0, 0.55), 0.38, 0.8, grey, verts=40)
    parts.append(body)
    for z in (0.25, 0.55, 0.85):
        parts.append(cyl("Rib", (0, 0, z), 0.395, 0.04, dark, verts=40))
    parts.append(cyl("Lid", (0, 0, 0.97), 0.3, 0.06, dark, verts=32))
    parts.append(cyl("Plug", (0, 0, 1.02), 0.12, 0.06, grey, verts=24))
    for a in (0, math.pi):
        parts.append(box("Lug", (0.36 * math.cos(a), 0.36 * math.sin(a), 0.98), (0.1, 0.04, 0.1), dark))
    for sx in (-1, 1):
        for sy in (-1, 1):
            parts.append(box("Post", (sx * 0.46, sy * 0.46, 0.5), (0.06, 0.06, 1.0), dark))
    for z in (0.12, 0.98):
        for sx in (-1, 1):
            parts.append(box("RailX", (0, sx * 0.46, z), (0.98, 0.05, 0.05), dark))
            parts.append(box("RailY", (sx * 0.46, 0, z), (0.05, 0.98, 0.05), dark))
    for sy in (-1, 1):
        parts.append(box("Skid", (0, sy * 0.3, 0.04), (1.0, 0.1, 0.08), pbr("Skid", (0.18, 0.12, 0.07), 0.85)))
    o = join(parts, name)
    tre = None
    if trefoil:
        bpy.ops.mesh.primitive_plane_add(size=0.26, location=(0, -0.392, 0.66), rotation=(math.radians(90), 0, 0))
        tre = bpy.context.active_object; tre.name = name + "Trefoil"; tre.data.materials.append(trefoil_material(name + "TrefoilM"))
        tre.parent = o
        o["trefoil"] = tre.name
    return o, dict(lead=lead, grey=grey, dark=dark, trefoil=tre)


def crate(name, size=(1.15, 1.15, 1.2), loc=(0, 0, 0)):
    m = ph_mat("wood_planks_dirt", 1.0, (0.35, 0.25, 0.15), name=name + "Wood") if False else noisy(name + "Wood", (0.38, 0.27, 0.16), 0.85, dirt=0.6, scale=6)
    sx, sy, sz = size; parts = []
    for k in range(6):
        z = 0.1 + k * (sz - 0.1) / 6
        parts.append(box("SlatX", (0, -sy / 2, z + 0.08), (sx, 0.025, 0.15), m)); parts.append(box("SlatX", (0, sy / 2, z + 0.08), (sx, 0.025, 0.15), m))
        parts.append(box("SlatY", (-sx / 2, 0, z + 0.08), (0.025, sy, 0.15), m)); parts.append(box("SlatY", (sx / 2, 0, z + 0.08), (0.025, sy, 0.15), m))
    o = join(parts, name); o.location = loc
    return o


def wheel(name, r, w, tyre, hub, sy):
    """Tyre with sidewall, steel rim, hub and lug nuts; axle along Y (sy = +1 left side / -1 right side)."""
    parts = [cyl("Tyre", (0, 0, 0), r, w, tyre, verts=32, rot=(math.radians(90), 0, 0)),
             cyl("Rim", (0, sy * (w / 2 + 0.002), 0), r * 0.58, 0.02, hub, verts=24, rot=(math.radians(90), 0, 0)),
             cyl("Hub", (0, sy * (w / 2 + 0.02), 0), r * 0.22, 0.05, hub, verts=16, rot=(math.radians(90), 0, 0))]
    for k in range(6):
        a = k / 6 * 2 * math.pi
        parts.append(cyl("Nut", (r * 0.32 * math.cos(a), sy * (w / 2 + 0.02), r * 0.32 * math.sin(a)), 0.018, 0.03, hub, verts=6, rot=(math.radians(90), 0, 0)))
    return join(parts, name)


def truck(name="Truck", col=(0.12, 0.2, 0.3), bed_len=4.2):
    """1990s cab-over light truck (generic, no badges), drop-side bed. Front toward +X. Origin on the ground under
    the rear axle. Returns (body, wheels[list], bed_top_z, bed_x_range)."""
    paint = painted_steel(name + "Paint", col, 0.45, 0.55)
    black = pbr(name + "Black", (0.015, 0.015, 0.015), 0.65)
    rubber = pbr(name + "Rubber", (0.01, 0.01, 0.01), 0.8)
    chrome = pbr(name + "Bumper", (0.12, 0.12, 0.12), 0.5, 0.6)
    glass_m = pbr(name + "Glass", (0.02, 0.025, 0.03), 0.06, 0.0, **{'Coat Weight': 1.0})
    wood = noisy(name + "BedWood", (0.3, 0.22, 0.14), 0.85, dirt=0.7, scale=4)
    lamp = pbr(name + "Lamp", (0.85, 0.85, 0.8), 0.08, 0.0, **{'Coat Weight': 1.0})
    amber = pbr(name + "Amber", (0.8, 0.35, 0.02), 0.2)
    W = 2.1
    cab_x = bed_len / 2 + 0.25 + 0.9
    fx = cab_x + 0.88                                  # cab front face
    parts = [box("Chassis", (cab_x / 2 - 0.4, 0, 0.62), (bed_len + 2.7, 0.9, 0.22), black),
             box("Cab", (cab_x, 0, 1.62), (1.76, W, 1.5), paint, bevel=0.16),
             box("CabLow", (cab_x + 0.06, 0, 0.98), (1.64, W - 0.04, 0.55), paint, bevel=0.06),
             box("CabRoof", (cab_x - 0.05, 0, 2.38), (1.6, W - 0.12, 0.12), paint, bevel=0.05),
             box("ScreenFrame", (fx + 0.005, 0, 1.92), (0.03, W - 0.2, 0.86), rubber, rot=(0, math.radians(-8), 0)),
             box("Windscreen", (fx + 0.02, 0, 1.92), (0.02, W - 0.3, 0.76), glass_m, rot=(0, math.radians(-8), 0)),
             box("Wiper", (fx + 0.04, -0.35, 1.58), (0.015, 0.6, 0.02), black, rot=(math.radians(12), 0, 0)),
             box("Wiper", (fx + 0.04, 0.35, 1.58), (0.015, 0.6, 0.02), black, rot=(math.radians(12), 0, 0)),
             box("Bumper", (fx + 0.06, 0, 0.6), (0.14, W + 0.06, 0.24), chrome, bevel=0.03),
             box("Step", (cab_x + 0.25, W / 2 + 0.03, 0.55), (0.6, 0.12, 0.05), black),
             box("Step", (cab_x + 0.25, -W / 2 - 0.03, 0.55), (0.6, 0.12, 0.05), black)]
    for k in range(5):                                  # grille slats
        parts.append(box("Grille", (fx + 0.012, 0, 1.0 + k * 0.07), (0.02, 1.1, 0.035), black))
    for sy in (-1, 1):
        parts.append(cyl("Headlamp", (fx + 0.07, sy * 0.78, 0.78), 0.09, 0.04, lamp, verts=20, rot=(0, math.radians(90), 0)))
        parts.append(box("Indicator", (fx + 0.05, sy * 0.98, 1.05), (0.03, 0.1, 0.08), amber))
        parts.append(box("DoorSeam", (cab_x - 0.5, sy * (W / 2 + 0.003), 1.4), (0.012, 0.004, 1.3), black))
        parts.append(box("DoorSeam", (cab_x + 0.55, sy * (W / 2 + 0.003), 1.4), (0.012, 0.004, 1.3), black))
        parts.append(box("SideWin", (cab_x + 0.05, sy * (W / 2 + 0.006), 1.95), (0.95, 0.01, 0.62), glass_m))
        parts.append(box("Handle", (cab_x - 0.38, sy * (W / 2 + 0.015), 1.45), (0.16, 0.02, 0.03), black))
        parts.append(box("MirrorArm", (cab_x + 0.75, sy * (W / 2 + 0.12), 2.05), (0.03, 0.25, 0.03), black))
        parts.append(box("Mirror", (cab_x + 0.75, sy * (W / 2 + 0.25), 1.95), (0.05, 0.15, 0.32), black, bevel=0.01))
        parts.append(box("Fender", (cab_x + 0.05, sy * (W / 2 - 0.12), 0.95), (0.95, 0.3, 0.06), black))
        parts.append(box("RearFender", (-bed_len / 2 + 1.1, sy * (W / 2 - 0.15), 0.93), (1.0, 0.36, 0.04), black))
        parts.append(box("Tail", (-bed_len / 2 - 0.02, sy * 0.85, 0.72), (0.04, 0.22, 0.1), pbr(name + "TailM", (0.5, 0.03, 0.02), 0.2)))
    # bed: floor + low drop sides on a steel rim
    parts += [box("BedFloor", (0, 0, 0.86), (bed_len, W, 0.08), wood),
              box("SideL", (0, W / 2 - 0.02, 1.12), (bed_len, 0.04, 0.45), wood),
              box("SideR", (0, -W / 2 + 0.02, 1.12), (bed_len, 0.04, 0.45), wood),
              box("TailGate", (-bed_len / 2 + 0.02, 0, 1.12), (0.04, W, 0.45), wood),
              box("HeadBoard", (bed_len / 2 - 0.02, 0, 1.35), (0.06, W, 0.9), paint),
              box("RimL", (0, W / 2 - 0.02, 1.35), (bed_len, 0.05, 0.04), paint), box("RimR", (0, -W / 2 + 0.02, 1.35), (bed_len, 0.05, 0.04), paint)]
    for x in np.linspace(-bed_len / 2, bed_len / 2, 5):
        for sy in (-1, 1):
            parts.append(box("Stake", (x, sy * (W / 2 - 0.01), 1.12), (0.06, 0.05, 0.47), paint))
    body = join(parts, name)
    wheels = []
    tyre = pbr(name + "Tyre", (0.022, 0.022, 0.022), 0.85); hub = painted_steel(name + "Hub", (0.25, 0.26, 0.26), 0.5, 0.5)
    for wx in (-bed_len / 2 + 1.1, cab_x + 0.05):
        for sy in (-1, 1):
            w = wheel(name + "Wheel", 0.45, 0.3, tyre, hub, sy)
            w.parent = body; w.location = (wx, sy * (W / 2 - 0.2), 0.45)
            wheels.append(w)
    return body, wheels, 0.9, (-bed_len / 2, bed_len / 2)


def excavator(name="Excavator", col=(0.75, 0.55, 0.08), tool="bucket"):
    """Tracked excavator built as a pivot hierarchy: base -> swing (z) -> boom (y-axis pitch) -> stick -> tool.
    Faces +X. Set rig['swing'].rotation_euler.z, rig['boom'/'stick'/'tool'].rotation_euler.y (radians)."""
    paint = painted_steel(name + "Paint", col, 0.45, 0.5)
    black = pbr(name + "Black", (0.03, 0.03, 0.03), 0.7)
    steel = painted_steel(name + "Steel", (0.12, 0.12, 0.12), 0.5, 0.6)
    glass_m = pbr(name + "Glass", (0.03, 0.04, 0.05), 0.05, 0.0, **{'Coat Weight': 1.0})
    base = join([box("TrackL", (0, 1.0, 0.45), (3.8, 0.6, 0.9), black, bevel=0.2), box("TrackR", (0, -1.0, 0.45), (3.8, 0.6, 0.9), black, bevel=0.2),
                 box("Under", (0, 0, 0.8), (2.4, 1.6, 0.5), steel)], name + "Base")

    def pivot(nm, parent, loc):
        e = bpy.data.objects.new(nm, None); bpy.context.collection.objects.link(e); e.parent = parent; e.location = loc
        return e
    swing = pivot(name + "Swing", base, (0, 0, 1.1))
    house = join([box("House", (-0.5, 0, 0.55), (2.8, 2.3, 1.0), paint, bevel=0.06),
                  box("Counter", (-1.85, 0, 0.6), (0.4, 2.3, 1.1), paint, bevel=0.15),
                  box("Cab", (0.45, 0.6, 1.55), (1.0, 0.95, 1.1), paint, bevel=0.05),
                  box("CabGlassF", (0.96, 0.6, 1.6), (0.02, 0.8, 0.85), glass_m),
                  box("CabGlassS", (0.45, 0.08, 1.6), (0.8, 0.02, 0.8), glass_m),
                  box("Exhaust", (-1.2, -0.7, 1.4), (0.08, 0.08, 0.7), black)], name + "House")
    house.parent = swing; house.location = (0, 0, 0)
    boom = pivot(name + "Boom", swing, (0.8, -0.3, 0.9))
    BL = 3.6
    bm = join([box("BoomArm", (BL / 2, 0, 0), (BL, 0.45, 0.55), paint, bevel=0.05),
               cyl("Ram", (BL * 0.35, 0, -0.45), 0.08, BL * 0.6, steel, verts=12, rot=(0, math.radians(90), 0))], name + "BoomM")
    bm.parent = boom; bm.location = (0, 0, 0)
    stick = pivot(name + "Stick", boom, (BL, 0, 0))
    SL = 2.2
    sm = box("StickArm", (SL / 2, 0, 0), (SL, 0.32, 0.4), paint, bevel=0.04); sm.parent = stick; sm.location = (SL / 2, 0, 0)
    toolp = pivot(name + "Tool", stick, (SL, 0, 0))
    if tool == "bucket":
        tm = join([box("BucketBack", (0.25, 0, -0.1), (0.5, 0.9, 0.06), steel, rot=(0, math.radians(70), 0)),
                   box("BucketL", (0.25, 0.45, -0.25), (0.6, 0.04, 0.55), steel), box("BucketR", (0.25, -0.45, -0.25), (0.6, 0.04, 0.55), steel),
                   box("BucketFloor", (0.45, 0, -0.5), (0.5, 0.9, 0.05), steel)], name + "Bucket")
        for k in range(4):
            tooth = box("Tooth", (0.72, -0.33 + k * 0.22, -0.5), (0.12, 0.06, 0.04), steel); tooth.parent = tm
    else:   # orange-peel scrap grab: hanging hub with 5 tines
        tm = join([cyl("GrabHub", (0, 0, -0.35), 0.28, 0.5, steel, verts=16)], name + "Grab")
        tines = []
        for k in range(5):
            a = k / 5 * 2 * math.pi
            tp = pivot(name + f"Tine{k}", tm, (0.25 * math.cos(a), 0.25 * math.sin(a), -0.55))
            tp.rotation_euler = (0, 0, a)
            tn = box("Tine", (0.0, 0, -0.45), (0.12, 0.35, 0.9), steel); tn.parent = tp; tn.location = (0.05, 0, -0.45)
            tines.append(tp)
        tm["n_tines"] = 5
    tm.parent = toolp; tm.location = (0, 0, 0)
    rig = dict(base=base, swing=swing, boom=boom, stick=stick, tool=toolp, tool_mesh=tm, BL=BL, SL=SL)
    if tool != "bucket":
        rig["tines"] = tines
    return rig


def set_grab(rig, open_):
    """open_ 0 closed .. 1 open (tines splay outward)."""
    for tp in rig.get("tines", []):
        a = tp.rotation_euler.z
        tp.rotation_euler = Euler((0, -math.radians(10 + 45 * open_), a), 'ZYX')


def pose_arm(rig, swing, boom, stick, tool):
    rig["swing"].rotation_euler = (0, 0, swing)
    rig["boom"].rotation_euler = (0, -boom, 0)
    rig["stick"].rotation_euler = (0, stick, 0)
    rig["tool"].rotation_euler = (0, tool, 0)


def arm_ik(rig, target, elbow_up=True):
    """Swing + boom + stick so the stick end (tool pivot) reaches the world point `target`."""
    bpy.context.view_layer.update()
    base = rig["base"].matrix_world
    tl = base.inverted() @ Vector(target)
    sw_origin = rig["swing"].location
    rig["swing"].rotation_euler = (0, 0, math.atan2(tl.y - rig["boom"].location.y * 0, tl.x))
    bpy.context.view_layer.update()
    bp = rig["boom"].matrix_world.translation
    fwd = (rig["swing"].matrix_world.to_3x3() @ Vector((1, 0, 0))).normalized()
    v = Vector(target) - bp
    d = max(0.3, v.dot(fwd)); h = v.z
    a = rig["BL"]; b = rig["SL"]
    D = min(a + b - 1e-3, math.hypot(d, h))
    c2 = (D * D - a * a - b * b) / (2 * a * b); c2 = max(-1.0, min(1.0, c2))
    q2 = math.acos(c2)
    q1 = math.atan2(h, d) + math.atan2(b * math.sin(q2), a + b * math.cos(q2))
    rig["boom"].rotation_euler = (0, -q1, 0)
    rig["stick"].rotation_euler = (0, q2, 0)
    bpy.context.view_layer.update()


def hang_tool_level(rig):
    """Keep a hanging grab vertical whatever the boom and stick angles (call after pose_arm)."""
    b = rig["boom"].rotation_euler.y; s = rig["stick"].rotation_euler.y
    rig["tool"].rotation_euler = (0, -(b + s), 0)


# ============================================================================ architecture
def house(name, loc, w=8.0, d=7.0, floors=1, plaster=None, roof=None, rot_z=0.0, lit=0.0, chimney=True, rng=None):
    """Low İkitelli house: plastered walls, hipped clay-tile roof, timber-framed windows, a door. Faces -Y (local)."""
    rng = rng or np.random.default_rng(len(name))
    h = 2.9 * floors
    parts = [box("Walls", (0, 0, h / 2), (w, d, h), plaster)]
    frame = pbr(name + "Frame", (0.45, 0.4, 0.33), 0.7)
    win_g = pbr(name + "WinGlass", (0.035, 0.035, 0.04), 0.22, 0.0)
    if lit > 0:
        win_g = emissive(name + "WinLit", (1.0, 0.72, 0.42), lit)
    for f in range(floors):
        for k in range(max(1, int(w // 2.6))):
            x = -w / 2 + 1.3 + k * 2.6
            if f == 0 and k == 1:
                parts.append(box("Door", (x, -d / 2 - 0.01, 1.05), (0.95, 0.04, 2.1), pbr(name + "Door", (0.22, 0.14, 0.08), 0.7)))
                continue
            z = 1.55 + f * 2.9
            parts.append(box("WinFrame", (x, -d / 2 - 0.02, z), (1.1, 0.06, 1.3), frame))
            parts.append(box("Win", (x, -d / 2 - 0.05, z), (0.95, 0.02, 1.15), win_g))
            parts.append(box("Sill", (x, -d / 2 - 0.08, z - 0.7), (1.2, 0.16, 0.05), plaster))
    o = join(parts, name)
    # hipped roof: a squashed 4-sided pyramid frustum
    bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=1.0, radius2=0.25, depth=1.0, location=(0, 0, h + 0.65), rotation=(0, 0, math.radians(45)))
    r = bpy.context.active_object; r.name = name + "Roof"; r.scale = (w * 0.76, d * 0.76, 1.3)
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    r.data.materials.append(roof); r.parent = o
    if chimney:
        ch = box(name + "Chimney", (w * 0.25, d * 0.15, h + 1.3), (0.45, 0.45, 1.4), plaster); ch.parent = o
    o.location = loc; o.rotation_euler = (0, 0, rot_z)
    return o


def wall(name, a, b, h, thick, mat):
    a = Vector(a); b = Vector(b); m = (a + b) / 2; L = (b - a).length
    ang = math.atan2(b.y - a.y, b.x - a.x)
    return box(name, (m.x, m.y, h / 2), (L, thick, h), mat, rot=(0, 0, ang))


# ============================================================================ people
CLOTHES = {"coat": "male_casualsuit05", "jacket": "male_casualsuit05", "work": "male_worksuit01",
           "sweater": "male_casualsuit04", "woman": "female_casualsuit01", "suit": "male_elegantsuit01"}


# 1998 Istanbul winter wear: (clothes asset, tint, value) -- muted, varied; never all-black
OUTFITS = {
    "wool_brown": ("male_casualsuit05", (0.62, 0.45, 0.32), 1.1),
    "wool_grey":  ("male_casualsuit05", (0.62, 0.62, 0.6), 1.2),
    "parka_green": ("male_casualsuit05", (0.4, 0.46, 0.3), 1.2),
    "navy":       ("male_casualsuit05", (0.32, 0.38, 0.52), 1.1),
    "camel":      ("male_casualsuit05", (0.8, 0.62, 0.42), 1.25),
    "charcoal":   ("male_casualsuit05", (0.45, 0.45, 0.46), 1.1),
    "suit_grey":  ("male_elegantsuit01", (0.6, 0.6, 0.62), 1.6),
    "suit_brown": ("male_elegantsuit01", (0.6, 0.5, 0.4), 1.6),
    "doctor":     ("male_elegantsuit01", (1.0, 1.0, 1.0), 5.0),      # white coat
    "nurse":      ("female_elegantsuit01", (1.0, 1.0, 1.0), 4.5),
    "woman_coat": ("male_casualsuit05", (0.55, 0.38, 0.36), 1.2),
    "overall_white": ("male_worksuit01", (1.0, 1.0, 0.98), 3.2),     # coverall look: whole suit tinted
    "overall_orange": ("male_worksuit01", (1.0, 0.38, 0.06), 3.4),
    "police":     ("male_elegantsuit01", (0.35, 0.42, 0.55), 1.8),
}


def _hat(h, kind, col):
    """Knit cap / flat cap, parented to the head bone (follows every pose, bakes with the rig)."""
    from kit import fabric
    from mathutils import Matrix
    bpy.context.view_layer.update()
    hd = h.bone_head("head"); tl = h.bone_tail("head")
    up = (tl - hd).normalized()
    crown = hd + (tl - hd) * 0.85
    m = fabric(h.name + kind, col, 1.0, 0.8, 900)
    if kind == "knit":
        bpy.ops.mesh.primitive_uv_sphere_add(segments=28, ring_count=14, radius=0.112, location=crown + up * 0.01)
        c = bpy.context.active_object; c.scale = (1.02, 1.08, 0.95)
        bpy.ops.object.shade_smooth()
        bpy.ops.object.mode_set(mode='EDIT'); import bmesh
        bm = bmesh.from_edit_mesh(c.data)
        for v in [v for v in bm.verts if v.co.z < -0.02]:
            bm.verts.remove(v)
        bmesh.update_edit_mesh(c.data); bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.mesh.primitive_torus_add(major_radius=0.108, minor_radius=0.018, major_segments=28, minor_segments=8, location=crown + up * 0.01 - Vector((0, 0, 0.022)))
        band = bpy.context.active_object; band.scale = (1.0, 1.06, 1.0); bpy.ops.object.shade_smooth()
        parts = [c, band]
    elif kind == "nurse":   # small starched white cap sitting on the crown, slightly back
        bpy.ops.mesh.primitive_cube_add(size=1, location=crown + up * 0.035 + Vector((0, 0.03, 0)))
        c = bpy.context.active_object; c.scale = (0.17, 0.09, 0.05); c.rotation_euler = (math.radians(-15), 0, 0)
        bv = c.modifiers.new("Bevel", 'BEVEL'); bv.width = 0.012; bv.segments = 3
        bpy.context.view_layer.objects.active = c; bpy.ops.object.modifier_apply(modifier="Bevel"); bpy.ops.object.shade_smooth()
        parts = [c]
    else:   # flat cap: low crown + short brim toward the face (-Y in rest pose)
        bpy.ops.mesh.primitive_uv_sphere_add(segments=28, ring_count=14, radius=0.115, location=crown + up * 0.005 + Vector((0, -0.012, 0)))
        c = bpy.context.active_object; c.scale = (1.02, 1.12, 0.48); bpy.ops.object.shade_smooth()
        bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=0.075, depth=0.012, location=crown + Vector((0, -0.11, -0.025)))
        brim = bpy.context.active_object; brim.scale = (1.1, 0.75, 1.0); brim.rotation_euler = (math.radians(-12), 0, 0)
        parts = [c, brim]
    for p in parts:
        p.data.materials.append(m)
    hat = join(parts, h.name + "Hat")
    _to_bone(h, hat, "head")
    return hat


def _to_bone(h, o, bone):
    bpy.context.view_layer.update()
    mw = o.matrix_world.copy()
    o.parent = h.arm; o.parent_type = 'BONE'; o.parent_bone = bone
    bpy.context.view_layer.update()
    o.matrix_world = mw
    h.parts.append(o)


def _moustache(h, col=(0.03, 0.022, 0.018)):
    """Dark moustache: an eyebrow strip reused, flipped and moved to the upper lip."""
    br = [o for o in h.parts if o.name.endswith("_brows")]
    if not br:
        return None
    me = br[0].data.copy(); o = bpy.data.objects.new(h.name + "Moustache", me); bpy.context.collection.objects.link(o)
    co = np.empty(len(me.vertices) * 3, np.float32); me.vertices.foreach_get("co", co); co = co.reshape(-1, 3)
    zc = co[:, 2].mean()
    nose = h.bone_head("head")
    co[:, 0] *= 0.42                                    # narrower than the brows
    co[:, 2] = zc - (co[:, 2] - zc) * 0.6 - 0.083      # flip the arch and drop to the upper lip
    co[:, 1] += 0.012                                   # lip is set back a little from the brow ridge
    me.vertices.foreach_set("co", co.ravel()); me.update()
    o.data.materials.clear(); o.data.materials.append(pbr(h.name + "MoustM", col, 0.8))
    for md in list(o.modifiers):
        o.modifiers.remove(md)
    _to_bone(h, o, "head")
    return o


def coverall_material(name, col):
    """Cotton drill: matte, fine weave bump, soft fold shading, grime toward the hems and knees."""
    m = bpy.data.materials.new(name); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; p = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord"); geo = N.new("ShaderNodeNewGeometry")
    weave = N.new("ShaderNodeTexWave"); weave.inputs['Scale'].default_value = 900; weave.inputs['Distortion'].default_value = 2
    L.new(tc.outputs['Object'], weave.inputs['Vector'])
    folds = N.new("ShaderNodeTexNoise"); folds.inputs['Scale'].default_value = 9; folds.inputs['Detail'].default_value = 4
    L.new(tc.outputs['Object'], folds.inputs['Vector'])
    dirt = N.new("ShaderNodeTexNoise"); dirt.inputs['Scale'].default_value = 5; dirt.inputs['Detail'].default_value = 10
    L.new(tc.outputs['Object'], dirt.inputs['Vector'])
    sep = N.new("ShaderNodeSeparateXYZ"); L.new(geo.outputs['Position'], sep.inputs[0])
    low = N.new("ShaderNodeMapRange"); low.inputs['From Min'].default_value = 0.9; low.inputs['From Max'].default_value = 0.0
    L.new(sep.outputs['Z'], low.inputs['Value'])
    dm = N.new("ShaderNodeMath"); dm.operation = 'MULTIPLY'; L.new(dirt.outputs['Fac'], dm.inputs[0]); L.new(low.outputs[0], dm.inputs[1])
    base = N.new("ShaderNodeMix"); base.data_type = 'RGBA'; L.new(dm.outputs[0], base.inputs['Factor'])
    base.inputs[6].default_value = (*col, 1); base.inputs[7].default_value = (col[0] * 0.45, col[1] * 0.42, col[2] * 0.38, 1)
    fd = N.new("ShaderNodeMix"); fd.data_type = 'RGBA'; fd.blend_type = 'MULTIPLY'; fd.inputs['Factor'].default_value = 0.35
    L.new(base.outputs[2], fd.inputs[6]); L.new(folds.outputs['Color'], fd.inputs[7]); L.new(fd.outputs[2], p.inputs['Base Color'])
    p.inputs['Roughness'].default_value = 0.97; p.inputs['Specular IOR Level'].default_value = 0.2
    p.inputs['Sheen Weight'].default_value = 0.25
    h = N.new("ShaderNodeMath"); h.operation = 'MULTIPLY_ADD'; h.inputs[1].default_value = 0.15
    L.new(weave.outputs['Fac'], h.inputs[0]); L.new(folds.outputs['Fac'], h.inputs[2])
    b = N.new("ShaderNodeBump"); b.inputs['Strength'].default_value = 0.35; b.inputs['Distance'].default_value = 0.02
    L.new(h.outputs[0], b.inputs['Height']); L.new(b.outputs['Normal'], p.inputs['Normal'])
    return m


def gloves(h, col=(0.16, 0.12, 0.08)):
    """Work gloves: hand faces of the body re-materialled (leather / rubberised cotton)."""
    idx = set(h.vertex_region([b for b in h.rig.bones if b.startswith(("finger", "metacarpal", "wrist"))], 0.5).tolist())
    me = h.body.data
    me.materials.append(pbr(h.name + "Glove", col, 0.8))
    gi = len(me.materials) - 1
    for p in me.polygons:
        if all(v in idx for v in p.vertices):
            p.material_index = gi


def person(name, gender=1.0, years=40, outfit="wool_brown", hair="short02", hv=0.15, weight=0.5, height=0.5, skin=None,
           hat=None, hat_col=(0.18, 0.06, 0.05), moustache=False, dosimeter=False, base_layer=False, **_):
    from human import Human, add_asset
    sk = skin or {True: "middleage_lightskinned_male_diffuse2.png", False: "middleage_lightskinned_female_diffuse2.png"}[gender > 0.5]
    if years > 55:
        sk = "old_lightskinned_male_diffuse2.png" if gender > 0.5 else "old_lightskinned_female_diffuse2.png"
    if years < 28:
        sk = "young_lightskinned_male_diffuse.png" if gender > 0.5 else "young_lightskinned_female_diffuse.png"
    h = Human(name, gender=gender, years=years, muscle=0.5, weight=weight, height=height, skin=sk,
              eyebrows="eyebrow002" if gender > 0.5 else "eyebrow001", eyelashes="eyelashes01")
    asset, tint, val = OUTFITS.get(outfit, OUTFITS["wool_brown"])
    if asset == "male_worksuit01" or base_layer:        # long-sleeved shirt and trousers under overalls (winter)
        add_asset(h, "clothes", "male_casualsuit01", tint=(0.55, 0.55, 0.58), val=0.8, rough=0.85)
    add_asset(h, "clothes", asset, tint=tint, sat=0.0 if outfit.startswith(("overall", "doctor", "nurse")) else 0.35, val=val, rough=0.85, sheen=0.3)
    PLAIN = {"doctor": (0.82, 0.83, 0.82), "nurse": (0.8, 0.82, 0.82), "overall_white": (0.75, 0.76, 0.74), "overall_orange": (0.7, 0.26, 0.05)}
    if outfit in PLAIN:                                  # cotton coats / coveralls: plain cloth, not the suit texture
        from kit import fabric as _fab
        cm = coverall_material(name + "Cloth", PLAIN[outfit])
        names = (asset, "male_casualsuit01") if outfit.startswith("overall") else (asset,)   # one-piece coverall: shirt layer too
        for o in h.parts:
            if o.name.endswith(names):
                o.data.materials.clear(); o.data.materials.append(cm)
    add_asset(h, "clothes", "shoes02", val=0.15, rough=0.5)
    if hair:
        add_asset(h, "hair", hair, val=hv, rough=0.5)
    sb = h.skin_mat.node_tree.nodes["Principled BSDF"]
    sb.inputs['Subsurface Weight'].default_value = 0.1
    if hat:
        _hat(h, hat, hat_col)
    if moustache and gender > 0.5:
        _moustache(h)
    if outfit.startswith("overall"):
        gloves(h, (0.22, 0.17, 0.1) if outfit == "overall_white" else (0.12, 0.1, 0.08))
    if dosimeter:                                       # film-badge dosimeter clipped on the chest pocket
        bpy.context.view_layer.update()
        ch = h.bone_head("spine02")
        b = box(name + "Dosi", ch + Vector((0.09, -0.135, 0.12)), (0.035, 0.008, 0.045), pbr(name + "DosiM", (0.85, 0.82, 0.7), 0.4), bevel=0.003)
        _to_bone(h, b, "spine02")
    return h


def attach_cap(h):
    """Hats and badges are parented to bones now; kept for older call sites."""
    return None


def place(h, loc, face_z):
    """Rotation z = θ turns the rest pose (facing −Y) to face (sin θ, −cos θ). Feet on z=loc.z."""
    from human import _world_verts
    h.arm.rotation_euler = (0, 0, face_z); h.arm.location = loc; bpy.context.view_layer.update()
    w = np.concatenate([_world_verts(o) for o in h.parts if o.type == 'MESH' and "shoes" in o.name or o is h.body])
    h.arm.location.z += loc[2] - w[:, 2].min(); bpy.context.view_layer.update()


def face_angle(src, dst):
    """θ so that a person at src faces dst."""
    d = Vector(tuple(dst)[:2]) - Vector(tuple(src)[:2])
    return math.atan2(d.x, -d.y)


def arms_relaxed(h, phase=0.0, swing=0.0):
    """Arms hanging close to the body (relative to the rig's facing), optional walk swing in degrees."""
    M = h.arm.matrix_world.to_3x3(); fwd = (M @ Vector((0, -1, 0))).normalized(); left = (M @ Vector((1, 0, 0))).normalized()
    for sd, sg in (("L", 1), ("R", -1)):
        a = math.radians(swing) * math.sin(2 * math.pi * phase + (math.pi if sd == "L" else 0.0))
        up = (Vector((0, 0, -1)) * math.cos(a) + fwd * math.sin(a) + left * (0.1 * sg)).normalized()
        lo = (up + fwd * (0.22 + 0.15 * max(0.0, math.sin(a)))).normalized()
        h.aim(f"upperarm01.{sd}", up); h.aim(f"upperarm02.{sd}", up)
        h.aim(f"lowerarm01.{sd}", lo); h.aim(f"lowerarm02.{sd}", lo); h.aim(f"wrist.{sd}", lo + left * (0.1 * sg))


def arms_crossed(h):
    from human import reach
    fwd = forward(h); side = fwd.cross(Vector((0, 0, 1))).normalized()
    chest = h.bone_head("spine02") + fwd * 0.2 + Vector((0, 0, -0.02))
    reach(h, "R", chest + side * 0.1, Vector((side.x, side.y, -0.6)) + fwd * 0.2, -side)
    reach(h, "L", chest - side * 0.1 + Vector((0, 0, 0.04)), Vector((-side.x, -side.y, -0.6)) + fwd * 0.2, side)


def point_at_dir(h, target):
    from human import reach
    sh = h.bone_head("upperarm01.R"); d = (Vector(target) - sh).normalized()
    reach(h, "R", sh + d * 0.62, Vector((0, 0, -1)), d)


def forward(h):
    return (h.arm.matrix_world.to_3x3() @ Vector((0, -1, 0))).normalized()


def stand_pose(h, sway=0.0, head_down=0.0, hands_pockets=False, crossed=False):
    from human import reset_pose, fingers_curl
    h.arm.rotation_euler = (0, 0, 0); h.arm.location = (0, 0, 0)
    reset_pose(h)
    for sd, sg in (("L", 1), ("R", -1)):
        h.rot(f"upperleg01.{sd}", (0, 1, 0), sg * 2.0)
    arms_relaxed(h)
    if hands_pockets:
        fwd = forward(h); side = fwd.cross(Vector((0, 0, 1))).normalized()
        from human import reach
        for sd, sg in (("L", -1), ("R", 1)):
            hip = h.bone_head(f"upperleg01.{sd}")
            reach(h, sd, hip + side * (0.08 * sg) + fwd * 0.08 + Vector((0, 0, 0.1)), Vector((sg * side.x, sg * side.y, 0)) - fwd * 0.5, Vector((0, 0, -1)))
    if crossed:
        arms_crossed(h)
    fingers_curl(h, 30)
    h.rot("spine03", (0, 1, 0), sway)
    if head_down:
        h.rot("neck01", (1, 0, 0), head_down * 0.4); h.rot("head", (1, 0, 0), head_down * 0.6)


# ============================================================================ effects
def sparks(name, n=70, color=(1.0, 0.55, 0.18), strength=60.0, seed=3):
    """Pre-made spark streak objects; call pose_sparks(...) each frame."""
    m = emissive(name + "M", color, strength)
    rng = np.random.default_rng(seed)
    src = box(name + "Src", (0, 0, -50), (0.004, 0.004, 0.05), m)
    src.visible_shadow = False
    objs = [instance(src, (0, 0, -50), name=f"{name}{k}") for k in range(n)]
    for o in objs:
        o.visible_shadow = False
    vel = [Vector((rng.normal(0, 1.2), rng.normal(0, 1.2), rng.uniform(0.3, 2.5))) for _ in range(n)]
    life = rng.uniform(0.25, 0.7, n); off = rng.uniform(0, 1, n)
    return dict(objs=objs, vel=vel, life=life, off=off, src=src)


def pose_sparks(sp, origin, sec, direction=Vector((1, 0, 0)), spread=1.0, on=True, floor=0.0):
    """Ballistic sparks spraying from origin along `direction`, bouncing off the floor (kept simple)."""
    o0 = Vector(origin); d = Vector(direction).normalized()
    for k, o in enumerate(sp["objs"]):
        if not on:
            o.location = (0, 0, -50); continue
        L_ = sp["life"][k]; age = ((sec / L_) + sp["off"][k]) % 1.0 * L_
        v = d * 3.2 + sp["vel"][k] * spread
        p = o0 + v * age + Vector((0, 0, -4.9 * age * age))
        if p.z < floor:
            p.z = floor + 0.005 + (floor - p.z) * 0.15
        vv = v + Vector((0, 0, -9.8 * age))
        o.location = p
        o.rotation_mode = 'QUATERNION'; o.rotation_quaternion = vv.normalized().to_track_quat('Z', 'Y')
        s = max(0.05, 1 - age / L_); o.scale = (1, 1, 0.5 + 2.5 * s)


def flicker_light(name, loc, color=(1.0, 0.6, 0.3), energy=400, radius=0.05, seed=1.7):  # noqa
    l = bpy.data.lights.new(name, 'POINT'); l.color = color; l.shadow_soft_size = radius
    d = l.driver_add("energy").driver; d.type = 'SCRIPTED'
    d.expression = f"{energy} * (0.75 + 0.25 * sin(frame * 2.1 + {seed}) * sin(frame * 0.73))"
    o = bpy.data.objects.new(name, l); bpy.context.collection.objects.link(o); o.location = loc
    return o


def overcast(strength=0.12, sun_energy=0.8, sun_elev=25, sun_az=150, tint=(0.92, 0.95, 1.0)):
    """Flat winter sky: Nishita sky dimmed and desaturated, plus a very soft sun."""
    from common import world_sky, sun
    w = world_sky(sun_elev_deg=sun_elev, sun_rot_deg=sun_az, strength=strength, tint=tint, aerosol=6.0, air=1.4)
    N = w.node_tree.nodes; L = w.node_tree.links
    sky = [n for n in N if n.bl_idname == "ShaderNodeTexSky"][0]; sky.sun_disc = False
    hs = N.new("ShaderNodeHueSaturation"); hs.inputs['Saturation'].default_value = 0.25
    mix = [n for n in N if n.bl_idname == "ShaderNodeMix"][0]
    L.new(sky.outputs['Color'], hs.inputs['Color']); L.new(hs.outputs['Color'], mix.inputs[6])
    s = sun(sun_elev, sun_az, energy=sun_energy, color=(1.0, 0.95, 0.9), angle_deg=25)
    return w


# ============================================================================ scrap kit (instanced over heaps)
def ph_proto(aid, name=None, target_size=None):
    """Import a Poly Haven model as ONE mesh object (transforms applied, origin at its base centre), parked
    below ground, ready for instance(). Returns None if the download fails."""
    root, ms = ph_model(aid)
    if not ms:
        return None
    bpy.context.view_layer.update()
    objs = []
    for o in ms:
        mw = o.matrix_world.copy(); o.parent = None; o.matrix_world = mw
        objs.append(o)
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    if len(objs) > 1:
        bpy.ops.object.join()
    o = bpy.context.active_object; o.name = name or aid
    lo = Vector((min(v.co.x for v in o.data.vertices), min(v.co.y for v in o.data.vertices), min(v.co.z for v in o.data.vertices)))
    hi = Vector((max(v.co.x for v in o.data.vertices), max(v.co.y for v in o.data.vertices), max(v.co.z for v in o.data.vertices)))
    c = Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z))
    o.data.transform(Matrix.Translation(-c))
    if target_size:
        s = target_size / max(hi - lo)
        o.data.transform(Matrix.Scale(s, 4))
    o.location = (0, 0, -500)
    if root:
        bpy.data.objects.remove(root)
    return o


def bent_panel(name, w, h, bend, mat, thick=0.015):
    """A sheet bent along its width (bonnets, roofs, corrugated sheet): simple deform BEND, applied."""
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=16, y_subdivisions=4, size=1)
    o = bpy.context.active_object; o.name = name; o.scale = (w, h, 1)
    bpy.ops.object.transform_apply(scale=True)
    sd = o.modifiers.new("Bend", 'SIMPLE_DEFORM'); sd.deform_method = 'BEND'; sd.angle = bend; sd.deform_axis = 'Y'
    so = o.modifiers.new("Solid", 'SOLIDIFY'); so.thickness = thick
    bpy.ops.object.modifier_apply(modifier="Bend"); bpy.ops.object.modifier_apply(modifier="Solid")
    o.data.materials.append(mat)
    return o


def scrap_kit(rng):
    """Returns a list of (proto, weight). Materials: Poly Haven rust textures + painted panels with rust."""
    rust = [ph_mat("rusty_metal_02", 0.6, (0.25, 0.12, 0.06), name="ScrRust1"),
            ph_mat("rust_coarse_01", 0.7, (0.3, 0.14, 0.06), name="ScrRust2"),
            ph_mat("rusty_painted_metal", 0.6, (0.2, 0.25, 0.3), name="ScrPaintRust"),
            ph_mat("green_metal_rust", 0.6, (0.15, 0.22, 0.15), name="ScrGreenRust"),
            rust_mat("ScrRust3", (0.26, 0.11, 0.05), 5.0)]
    corr = ph_mat("rusty_corrugated_iron", 0.8, (0.3, 0.2, 0.12), name="ScrCorr")
    paints = [(0.3, 0.07, 0.05), (0.42, 0.42, 0.4), (0.08, 0.13, 0.22), (0.36, 0.3, 0.14), (0.09, 0.17, 0.1), (0.24, 0.25, 0.26)]
    pmats = []
    for k, col in enumerate(paints):
        m = rust_mat(f"PaintedRust{k}", (0.22, 0.1, 0.05), 3.0)
        N = m.node_tree.nodes; L = m.node_tree.links; p = N["Principled BSDF"]
        tc = N.new("ShaderNodeTexCoord"); nz = N.new("ShaderNodeTexNoise"); nz.inputs['Scale'].default_value = 2.5; nz.inputs['Detail'].default_value = 12
        L.new(tc.outputs['Object'], nz.inputs['Vector'])
        th = N.new("ShaderNodeMath"); th.operation = 'GREATER_THAN'; th.inputs[1].default_value = 0.56; L.new(nz.outputs['Fac'], th.inputs[0])
        cur = p.inputs['Base Color'].links[0].from_socket
        mx = N.new("ShaderNodeMix"); mx.data_type = 'RGBA'; L.new(th.outputs[0], mx.inputs['Factor'])
        L.new(cur, mx.inputs[6]); mx.inputs[7].default_value = (*col, 1)
        L.new(mx.outputs[2], p.inputs['Base Color'])
        pmats.append(m)
    K = []
    def add(o, w):
        o.location = (0, 0, -500); K.append((o, w))
    for k in range(3):                                    # car doors: outer panel + window frame
        m = pmats[k * 2 % len(pmats)]
        d = join([box("DoorPanel", (0, 0, 0.3), (1.1, 0.06, 0.6), m, bevel=0.03),
                  box("FrameT", (0.05, 0, 0.98), (0.95, 0.04, 0.04), m), box("FrameF", (-0.48, 0, 0.8), (0.04, 0.04, 0.4), m, rot=(0, math.radians(-15), 0)),
                  box("FrameB", (0.53, 0, 0.8), (0.04, 0.04, 0.4), m)], "CarDoor")
        add(d, 1.0)
    for k in range(3):                                    # bonnets / roofs
        add(bent_panel("Bonnet", 1.5, 1.2, rng.uniform(0.3, 0.8), pmats[(k * 2 + 1) % len(pmats)]), 1.0)
    for k in range(2):
        add(bent_panel("Corrugated", 2.4, 0.9, rng.uniform(0.1, 0.6), corr, 0.008), 1.0)
    for k, m in enumerate(rust):
        add(box("Plate", (0, 0, 0), (1.3, 0.9, 0.02), m), 1.2)
        ib = join([box("W", (0, 0, 0), (2.4, 0.02, 0.3), m), box("F1", (0, 0, 0.15), (2.4, 0.16, 0.02), m), box("F2", (0, 0, -0.15), (2.4, 0.16, 0.02), m)], "IBeam")
        add(ib, 0.8)
        add(cyl("Pipe", (0, 0, 0), rng.uniform(0.05, 0.14), rng.uniform(1.5, 3.0), m, verts=14, rot=(0, math.radians(90), 0)), 0.8)
        ang = join([box("A1", (0, 0, 0), (2.0, 0.08, 0.008), m), box("A2", (0, 0.04, 0.04), (2.0, 0.008, 0.08), m)], "Angle"); add(ang, 0.6)
    rebar_m = rust[4]
    for k in range(2):                                    # rebar bundles, bent
        bars = []
        for j in range(7):
            b = cyl("Rebar", (0, rng.uniform(-0.05, 0.05), rng.uniform(-0.05, 0.05)), 0.008, 3.0, rebar_m, verts=6, rot=(0, math.radians(90), 0))
            sd = b.modifiers.new("Bend", 'SIMPLE_DEFORM'); sd.deform_method = 'BEND'; sd.angle = rng.uniform(0.3, 1.4); sd.deform_axis = 'Y'
            bpy.context.view_layer.objects.active = b; bpy.ops.object.modifier_apply(modifier="Bend")
            bars.append(b)
        add(join(bars, "RebarBundle"), 0.6)
    for k in range(2):                                    # wire coils
        rings = []
        for j in range(9):
            bpy.ops.mesh.primitive_torus_add(major_radius=0.32 + rng.uniform(-0.02, 0.02), minor_radius=0.006, major_segments=40, minor_segments=4,
                                             location=(0, 0, j * 0.012), rotation=(rng.uniform(-0.06, 0.06), rng.uniform(-0.06, 0.06), 0))
            rings.append(bpy.context.active_object)
        c = join(rings, "WireCoil"); c.data.materials.append(rebar_m); add(c, 0.4)
    for k in range(2):                                    # radiators
        fins = [box("RadFin", (-0.45 + j * 0.075, 0, 0.3), (0.05, 0.1, 0.6), pmats[1 if k == 0 else 5], bevel=0.01) for j in range(13)]
        fins.append(box("RadTop", (0, 0, 0.62), (1.0, 0.04, 0.04), pmats[1])); fins.append(box("RadBot", (0, 0, -0.02), (1.0, 0.04, 0.04), pmats[1]))
        add(join(fins, "Radiator"), 0.4)
    white = rust_mat("EnamelRust", (0.25, 0.12, 0.06), 6.0)
    N = white.node_tree.nodes; L = white.node_tree.links; p = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord"); nz = N.new("ShaderNodeTexNoise"); nz.inputs['Scale'].default_value = 4; nz.inputs['Detail'].default_value = 10
    L.new(tc.outputs['Object'], nz.inputs['Vector']); th = N.new("ShaderNodeMath"); th.operation = 'GREATER_THAN'; th.inputs[1].default_value = 0.4
    L.new(nz.outputs['Fac'], th.inputs[0]); cur = p.inputs['Base Color'].links[0].from_socket
    mx = N.new("ShaderNodeMix"); mx.data_type = 'RGBA'; L.new(th.outputs[0], mx.inputs['Factor']); L.new(cur, mx.inputs[6]); mx.inputs[7].default_value = (0.48, 0.47, 0.44, 1)
    L.new(mx.outputs[2], p.inputs['Base Color'])
    wm = join([box("WMBody", (0, 0, 0.42), (0.6, 0.6, 0.84), white, bevel=0.03),
               cyl("WMDoor", (0, -0.305, 0.48), 0.2, 0.03, pbr("WMGlass", (0.05, 0.06, 0.07), 0.1), verts=24, rot=(math.radians(90), 0, 0)),
               cyl("WMRing", (0, -0.31, 0.48), 0.23, 0.02, pmats[5], verts=24, rot=(math.radians(90), 0, 0))], "WashingMachine")
    add(wm, 0.25)
    fr = join([box("FridgeBody", (0, 0, 0.75), (0.6, 0.62, 1.5), white, bevel=0.04), box("FridgeSeam", (0, -0.312, 1.05), (0.58, 0.01, 0.01), pmats[5])], "Fridge")
    add(fr, 0.15)
    for k, col in enumerate(((0.12, 0.22, 0.4), (0.45, 0.08, 0.05), (0.25, 0.12, 0.05))):
        dm = pmats[[2, 0, 4][k]]
        dr = join([cyl("Drum", (0, 0, 0.44), 0.29, 0.88, dm, verts=24)] + [cyl("DrumRib", (0, 0, z), 0.296, 0.02, dm, verts=24) for z in (0.3, 0.58)], "OilDrum")
        add(dr, 0.5)
    for aid, sz, w in (("rusted_wheel_rim_01", 0.6, 0.6), ("rusted_wheel_rim_02", 0.6, 0.6), ("old_tyre", 0.75, 0.9), ("Barrel_01", None, 0.4),
                       ("propane_tank", None, 0.2), ("can_rusted", None, 0.15), ("metal_jerrycan", None, 0.25)):
        o = ph_proto(aid, target_size=sz)
        if o is not None:
            add(o, w)
    car = join([box("CarShell", (0, 0, 0.55), (3.8, 1.6, 0.7), pmats[0], bevel=0.2), box("CarRoof", (-0.2, 0, 1.1), (1.9, 1.45, 0.5), pmats[0], bevel=0.15)], "CarShell")
    add(car, 0.12)
    return K


def scatter_scrap(kit_, hfun, cx, cy, R, n, rng, embed=0.15, scl=(0.8, 1.5), exclude=(), lie=0.7):
    """Pieces lying on the heap surface: random yaw, tilted toward lying flat, partly embedded."""
    protos = [p for p, w in kit_ if not any(p.name.startswith(e) for e in exclude)]
    weights = np.array([w for p, w in kit_ if not any(p.name.startswith(e) for e in exclude)]); weights /= weights.sum()
    objs = []
    for k in range(n):
        r = R * math.sqrt(rng.uniform(0, 0.97)); a = rng.uniform(0, 2 * math.pi)
        x, y = cx + r * math.cos(a), cy + r * math.sin(a)
        z = hfun(x, y) - embed * rng.uniform(0, 1)
        p = protos[rng.choice(len(protos), p=weights)]
        if p.name.startswith("CarShell") and r > 0.55 * R:
            continue
        tilt = lie * rng.uniform(-1, 1)
        objs.append(instance(p, (x, y, z), rot=(tilt + rng.normal(0, 0.4), rng.normal(0, 0.5), rng.uniform(0, 6.28)), scale=(rng.uniform(*scl),) * 3))
    return objs


def gn_instances(name, protos, locs, rots, scls, idxs):
    """One object that instances `protos` on points via geometry nodes (fast to build, renders in any Blender).
    locs: (n,3), rots: (n,3) euler, scls: (n,) uniform, idxs: (n,) index into protos."""
    col = bpy.data.collections.get(name + "Protos") or bpy.data.collections.new(name + "Protos")
    for i, p in enumerate(protos):                      # children are picked in name order: prefix the index
        p.name = f"{name}{i:03d}_{p.name}"
    for p in protos:
        if p.name not in col.objects:
            col.objects.link(p)
    me = bpy.data.meshes.new(name + "Pts"); me.from_pydata([tuple(map(float, l)) for l in locs], [], [])
    a = me.attributes.new("rot", 'FLOAT_VECTOR', 'POINT'); a.data.foreach_set("vector", np.asarray(rots, np.float32).ravel())
    a = me.attributes.new("scl", 'FLOAT', 'POINT'); a.data.foreach_set("value", np.asarray(scls, np.float32).ravel())
    a = me.attributes.new("idx", 'INT', 'POINT'); a.data.foreach_set("value", np.asarray(idxs, np.int32).ravel())
    o = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(o)
    ng = bpy.data.node_groups.new(name + "GN", 'GeometryNodeTree')
    ng.interface.new_socket("Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket("Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')
    N = ng.nodes; L = ng.links
    gi = N.new("NodeGroupInput"); go = N.new("NodeGroupOutput")
    ci = N.new("GeometryNodeCollectionInfo"); ci.inputs['Collection'].default_value = col
    ci.inputs['Separate Children'].default_value = True; ci.inputs['Reset Children'].default_value = True
    ip = N.new("GeometryNodeInstanceOnPoints"); ip.inputs['Pick Instance'].default_value = True
    def attr(nm, t):
        n = N.new("GeometryNodeInputNamedAttribute"); n.data_type = t; n.inputs['Name'].default_value = nm; return n
    ar, asc, ai = attr("rot", 'FLOAT_VECTOR'), attr("scl", 'FLOAT'), attr("idx", 'INT')
    e2r = N.new("FunctionNodeEulerToRotation"); L.new(ar.outputs['Attribute'], e2r.inputs[0])
    L.new(gi.outputs[0], ip.inputs['Points']); L.new(ci.outputs[0], ip.inputs['Instance'])
    L.new(ai.outputs['Attribute'], ip.inputs['Instance Index']); L.new(e2r.outputs[0], ip.inputs['Rotation'])
    L.new(asc.outputs['Attribute'], ip.inputs['Scale'])
    L.new(ip.outputs[0], go.inputs[0])
    md = o.modifiers.new("Scatter", 'NODES'); md.node_group = ng
    return o


def scrap_points(kit_, hfun, cx, cy, R, n, rng, embed=0.15, scl=(0.8, 1.5), exclude=(), lie=0.7):
    """Like scatter_scrap, but returns point data for gn_instances (index refers to the full kit list)."""
    names = [p.name.split("_", 1)[-1] if p.name[:1] == "S" and "_" in p.name else p.name for p, w in kit_]
    ok = [i for i, (p, w) in enumerate(kit_) if not any(p.name.startswith(e) for e in exclude)]
    wts = np.array([kit_[i][1] for i in ok]); wts /= wts.sum()
    L_, R_, S_, I_ = [], [], [], []
    for k in range(n):
        r = R * math.sqrt(rng.uniform(0, 0.97)); a = rng.uniform(0, 2 * math.pi)
        x, y = cx + r * math.cos(a), cy + r * math.sin(a)
        i = ok[rng.choice(len(ok), p=wts)]
        if names[i].startswith("CarShell") and r > 0.55 * R:
            continue
        L_.append((x, y, hfun(x, y) - embed * rng.uniform(0, 1)))
        R_.append((lie * rng.uniform(-1, 1) + rng.normal(0, 0.4), rng.normal(0, 0.5), rng.uniform(0, 6.28)))
        S_.append(rng.uniform(*scl)); I_.append(i)
    return L_, R_, S_, I_


# ============================================================================ interiors
def two_tone(name, low=(0.32, 0.42, 0.36), high=(0.78, 0.74, 0.64), split=1.2):
    """Classic 1990s Turkish institutional wall: oil-painted dado below, distemper above (world Z split)."""
    m = bpy.data.materials.new(name); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; p = N["Principled BSDF"]
    geo = N.new("ShaderNodeNewGeometry"); sep = N.new("ShaderNodeSeparateXYZ"); L.new(geo.outputs['Position'], sep.inputs[0])
    gt = N.new("ShaderNodeMath"); gt.operation = 'GREATER_THAN'; gt.inputs[1].default_value = split; L.new(sep.outputs['Z'], gt.inputs[0])
    tc = N.new("ShaderNodeTexCoord"); nz = N.new("ShaderNodeTexNoise"); nz.inputs['Scale'].default_value = 0.35; nz.inputs['Detail'].default_value = 2
    L.new(tc.outputs['Object'], nz.inputs['Vector'])     # broad, soft mottling only (no fine speckle)
    mx = N.new("ShaderNodeMix"); mx.data_type = 'RGBA'; L.new(gt.outputs[0], mx.inputs['Factor'])
    mx.inputs[6].default_value = (*low, 1); mx.inputs[7].default_value = (*high, 1)
    st = N.new("ShaderNodeMix"); st.data_type = 'RGBA'; st.blend_type = 'MULTIPLY'; st.inputs['Factor'].default_value = 0.12
    L.new(mx.outputs[2], st.inputs[6]); L.new(nz.outputs['Color'], st.inputs[7]); L.new(st.outputs[2], p.inputs['Base Color'])
    rr = N.new("ShaderNodeMapRange"); L.new(gt.outputs[0], rr.inputs['Value']); rr.inputs['To Min'].default_value = 0.35; rr.inputs['To Max'].default_value = 0.85
    L.new(rr.outputs[0], p.inputs['Roughness'])
    return m


def room(name, ctr, w, d, h, floor_m, wall_m, ceil_m=None, windows=(), doors=(), ceil=True):
    """A room shell built from wall slabs (thickness 0.2) with real openings (boolean) for windows and doors.
    windows/doors: list of (side, offset_along_wall, sill_z, width, height); side in 'N','S','E','W'.
    Returns dict with wall objects and a list of window centres (for glass / daylight)."""
    x, y, _ = ctr; t = 0.2
    walls = {"N": box(name + "N", (x, y + d / 2 + t / 2, h / 2), (w + 2 * t, t, h), wall_m),
             "S": box(name + "S", (x, y - d / 2 - t / 2, h / 2), (w + 2 * t, t, h), wall_m),
             "E": box(name + "E", (x + w / 2 + t / 2, y, h / 2), (t, d, h), wall_m),
             "W": box(name + "W", (x - w / 2 - t / 2, y, h / 2), (t, d, h), wall_m)}
    box(name + "Floor", (x, y, -0.02), (w + 0.4, d + 0.4, 0.04), floor_m)
    if ceil:
        box(name + "Ceil", (x, y, h + 0.03), (w + 0.4, d + 0.4, 0.06), ceil_m or pbr(name + "CeilM", (0.8, 0.79, 0.75), 0.9))
    centres = []
    for kind, lst in (("win", windows), ("door", doors)):
        for side, off, z0, ww, hh in lst:
            if side in "NS":
                cx, cy = x + off, y + (d / 2 + t / 2) * (1 if side == "N" else -1); size = (ww, t * 3, hh)
            else:
                cx, cy = x + (w / 2 + t / 2) * (1 if side == "E" else -1), y + off; size = (t * 3, ww, hh)
            cut = box("Cut", (cx, cy, z0 + hh / 2), size)
            wo = walls[side]; md = wo.modifiers.new("Cut", 'BOOLEAN'); md.object = cut; md.operation = 'DIFFERENCE'
            bpy.context.view_layer.objects.active = wo; bpy.ops.object.modifier_apply(modifier="Cut"); bpy.data.objects.remove(cut)
            if kind == "win":
                fr = pbr(name + "WinFrame", (0.85, 0.84, 0.8), 0.5)
                gsz = (ww, 0.01, hh) if side in "NS" else (0.01, ww, hh)
                box(name + "Glass", (cx, cy, z0 + hh / 2), gsz, glass(name + "GlassM", (0.92, 0.94, 0.93), 0.02))
                for k in range(3):
                    if side in "NS":
                        box("Mullion", (cx - ww / 2 + k * ww / 2, cy, z0 + hh / 2), (0.05, t * 1.05, hh), fr)
                    else:
                        box("Mullion", (cx, cy - ww / 2 + k * ww / 2, z0 + hh / 2), (t * 1.05, 0.05, hh), fr)
                box("Transom", (cx, cy, z0 + hh * 0.7), (ww if side in "NS" else t * 1.05, t * 1.05 if side in "NS" else ww, 0.05), fr)
                box("WinSill", (cx, cy, z0 - 0.03), (ww + 0.2 if side in "NS" else t * 1.6, t * 1.6 if side in "NS" else ww + 0.2, 0.05), fr)
            centres.append((kind, Vector((cx, cy, z0 + hh / 2)), side))
    return dict(walls=walls, openings=centres)


def tube_light(loc, length=1.2, energy=60, color=(0.95, 0.97, 1.0), on_expr=None):
    """Ceiling fluorescent fitting: Poly Haven fixture if available + an area light beneath it."""
    root, ms = ph_model("mounted_fluorescent_lights", loc=loc)
    if root is None:
        box("TubeFix", loc, (length, 0.18, 0.08), pbr("TubeFixM", (0.85, 0.85, 0.82), 0.4))
    l = bpy.data.lights.new("Tube", 'AREA'); l.shape = 'RECTANGLE'; l.size = length; l.size_y = 0.15; l.energy = energy; l.color = color
    if on_expr:
        d = l.driver_add("energy").driver; d.type = 'SCRIPTED'; d.expression = on_expr
    o = bpy.data.objects.new("Tube", l); bpy.context.collection.objects.link(o); o.location = (loc[0], loc[1], loc[2] - 0.12)
    o.visible_camera = False
    return o


def daylight_window(centre, side, size=(1.6, 1.6), energy=250, color=(0.85, 0.9, 1.0)):
    """Soft daylight pouring in through a window: an area light just outside the glass, facing in."""
    l = bpy.data.lights.new("Daylight", 'AREA'); l.shape = 'RECTANGLE'; l.size = size[0]; l.size_y = size[1]; l.energy = energy; l.color = color
    o = bpy.data.objects.new("Daylight", l); bpy.context.collection.objects.link(o)
    n = {"N": Vector((0, 1, 0)), "S": Vector((0, -1, 0)), "E": Vector((1, 0, 0)), "W": Vector((-1, 0, 0))}[side]
    o.location = Vector(centre) + n * 0.6
    o.rotation_euler = (-n).to_track_quat('-Z', 'Y').to_euler()
    o.visible_camera = False; o.visible_transmission = False; o.visible_glossy = False   # never seen through the glass
    return o


def lie_in_bed(h, head_at, foot_dir, z):
    """Patient lying face up; body runs from head_at toward foot_dir (unit XY)."""
    from human import reset_pose, lay_down
    h.arm.rotation_euler = (0, 0, 0); h.arm.location = (0, 0, 0); reset_pose(h)
    arms_relaxed(h)
    lay_down(h, face_up=True, z=0)
    ang = math.atan2(-foot_dir[0], foot_dir[1]) + math.pi     # lay_down puts the head toward +Y
    h.arm.rotation_euler = Euler((math.radians(-90), 0, ang), 'XYZ')
    bpy.context.view_layer.update()
    from human import _world_verts
    w = np.concatenate([_world_verts(o) for o in h.parts if o is h.body])
    top = w[np.argmax((w[:, :2] @ np.array([-foot_dir[0], -foot_dir[1]])))]
    h.arm.location = Vector((head_at[0] - top[0], head_at[1] - top[1], z - w[:, 2].min()))
    bpy.context.view_layer.update()


# ============================================================================ vehicles: the shared realistic kit replaces the placeholders
from rs_vehicles import truck, excavator, pose_arm, set_grab, arm_ik, hang_tool_level, roll   # noqa: E402,F811


def filing_cabinet(loc, rz, col=(0.42, 0.45, 0.42), name="FilingCabinet"):
    """Four-drawer steel filing cabinet."""
    from kit import pbr, box, join
    m = painted_steel(name + "M", col, 0.45, 0.45); k_ = pbr("FCHandle", (0.55, 0.55, 0.55), 0.3, 0.9)
    parts = [box("FCBody", (0, 0, 0.66), (0.47, 0.62, 1.32), m, bevel=0.01)]
    for j in range(4):
        parts += [box("FCDrawer", (0, -0.315, 0.17 + j * 0.32), (0.43, 0.012, 0.29), m, bevel=0.004), box("FCPull", (0, -0.33, 0.25 + j * 0.32), (0.12, 0.02, 0.02), k_)]
    o = join(parts, name); o.location = loc; o.rotation_euler = (0, 0, rz)
    return o


# ---------------------------------------------------------------------------- arms: elbows always bent
import human as _human
_reach_raw = _human.reach


def reach(h, side, target, pole=None, hand_dir=None, *a, **kw):
    """human.reach with the target pulled toward the shoulder so the elbow keeps at least ~45 degrees of bend
    (no puppet arms). Every set script imports reach after rs_kit, so they all get this version."""
    from mathutils import Vector as _V
    try:
        sh = h.bone_head(f"upperarm01.{side}"); el = h.bone_head(f"lowerarm01.{side}"); wr = h.bone_head(f"wrist.{side}")
        L = (el - sh).length + (wr - el).length
        t = _V(target); d = t - sh
        if d.length > 0.9 * L:
            t = sh + d.normalized() * 0.9 * L
        target = t
    except Exception:
        pass
    return _reach_raw(h, side, target, pole, hand_dir, *a, **kw)


_human.reach = reach
