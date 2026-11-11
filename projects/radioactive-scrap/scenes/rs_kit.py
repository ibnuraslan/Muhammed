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


def person(name, gender=1.0, years=40, clothes="coat", hair="short02", cval=0.25, hue=0.5, sat=0.4, hv=0.15, weight=0.5,
           height=0.5, skin=None, cap=False):
    from human import Human, add_asset
    sk = skin or {True: "middleage_lightskinned_male_diffuse2.png", False: "middleage_lightskinned_female_diffuse2.png"}[gender > 0.5]
    if years > 55:
        sk = "old_lightskinned_male_diffuse2.png" if gender > 0.5 else "old_lightskinned_female_diffuse2.png"
    if years < 28:
        sk = "young_lightskinned_male_diffuse.png" if gender > 0.5 else "young_lightskinned_female_diffuse.png"
    h = Human(name, gender=gender, years=years, muscle=0.5, weight=weight, height=height, skin=sk,
              eyebrows="eyebrow002" if gender > 0.5 else "eyebrow001", eyelashes="eyelashes01")
    add_asset(h, "clothes", CLOTHES.get(clothes, clothes), hue=hue, sat=sat, val=cval, rough=0.8, sheen=0.3)
    add_asset(h, "clothes", "shoes02", val=0.15, rough=0.5)
    if hair:
        add_asset(h, "hair", hair, val=hv, rough=0.5)
    sb = h.skin_mat.node_tree.nodes["Principled BSDF"]
    sb.inputs['Subsurface Weight'].default_value = 0.1
    if cap:                                   # a dark knitted cap (simple dome over the skull)
        bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=12, radius=0.105)
        c = bpy.context.active_object; c.name = name + "Cap"; c.scale = (1.0, 1.08, 0.82)
        from kit import fabric
        c.data.materials.append(fabric(name + "CapM", (0.05, 0.05, 0.055), 0.95, 0.4, 400))
        h.cap = c
        bpy.ops.object.shade_smooth()
    return h


def attach_cap(h):
    if getattr(h, "cap", None) is not None:
        hd = h.bone_head("head"); tl = h.bone_tail("head")
        h.cap.location = hd + (tl - hd) * 0.62 + Vector((0, 0, 0.0))


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


def arms_relaxed(h, swing=0.0):
    from human import aim_bone
    for sd, sg in (("L", 1), ("R", -1)):
        aim_bone(h.arm, f"upperarm01.{sd}", (sg * 0.12, 0.02 * swing, -1.0)); aim_bone(h.arm, f"upperarm02.{sd}", (sg * 0.12, 0.02, -1.0))
        aim_bone(h.arm, f"lowerarm01.{sd}", (sg * 0.06, -0.18, -1.0)); aim_bone(h.arm, f"lowerarm02.{sd}", (sg * 0.06, -0.18, -1.0))


def forward(h):
    return (h.arm.matrix_world.to_3x3() @ Vector((0, -1, 0))).normalized()


def stand_pose(h, sway=0.0, head_down=0.0, hands_pockets=False):
    from human import reset_pose, fingers_curl
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


def flicker_light(name, loc, color=(1.0, 0.6, 0.3), energy=400, radius=0.05, seed=1.7):
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
