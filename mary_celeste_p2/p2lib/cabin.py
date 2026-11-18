"""The Mary Celeste's after cabin as the Briggs family lived in it (New York, November 1872), and the same room
as Deveau finds it (4 December, cold, wet). Built in code + Poly Haven CC0 props.

Frame: x fore-aft (+x forward), y athwartships (+y port), z up from the cabin sole. Room x [-RX, RX], y [-RY, RY].
Furniture: table with cloth and an oil lamp in the middle, two chairs, the berth along the port side (+y) behind
a curtain, Sarah's reed organ against the after bulkhead (-x), a sideboard and fiddled bookshelf on the starboard
side (-y), the companion ladder in the forward starboard corner, a skylight over the table and three small
lights high in the starboard side of the trunk.
"""
import math, random
import numpy as np
import bpy, bmesh
from mathutils import Vector, Matrix, noise
import ship, ph
import stage as S

RX, RY, RZ = 1.95, 1.6, 1.98
TABLE = Vector((0.15, -0.3, 0.76)); TW, TD = 1.15, 0.78
BERTH = dict(x0=-1.9, x1=0.35, y0=0.86, top=0.62)
ORGAN = Vector((-1.68, -0.75, 0.0))
COMP = dict(x0=1.22, x1=1.9, y0=-1.6, y1=-0.95)       # companion ladder footprint
SKY = (0.15, -0.3, 0.7, 0.55)                       # skylight centre x, y, size x, y


def M(aid, scale, tint=None, name=None, wet=0.0):
    return ship.wood(aid, scale, wet=wet, tint=tint, name=name)


def box(name, c, s, mat, bevel=0.0):
    return ship.box(name, c, s, mat, bevel=bevel)


def cyl(name, p0, p1, r, mat, r1=None, verts=20):
    return ship.cyl(name, p0, p1, r, r1, mat=mat, verts=verts)


def lathe(name, prof, mat, center=(0, 0, 0), n=32, smooth=True):
    """Turned wood: prof = [(r, z)]; returns the solid of revolution."""
    V = []; F = []
    for (r, z) in prof:
        for k in range(n):
            a = 2 * math.pi * k / n
            V.append((center[0] + r * math.cos(a), center[1] + r * math.sin(a), center[2] + z))
    for j in range(len(prof) - 1):
        for k in range(n):
            a, b = j * n + k, j * n + (k + 1) % n
            F.append([a, b, b + n, a + n])
    F.append(list(range(n))[::-1]); F.append([len(prof) * n - n + k for k in range(n)])
    return ship.mesh_obj(name, V, F, mat, smooth=smooth)


def plain(name, color, rough=0.5, metal=0.0, coat=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True; p = m.node_tree.nodes["Principled BSDF"]
    p.inputs['Base Color'].default_value = (*color, 1); p.inputs['Roughness'].default_value = rough
    p.inputs['Metallic'].default_value = metal; p.inputs['Coat Weight'].default_value = coat
    return m


def brass():
    m = plain("brass", (0.62, 0.42, 0.18), rough=0.28, metal=1.0)
    return m


def rug_material(name="rug"):
    """A worn Turkey carpet: oxblood field, indigo and ochre border, a medallion pattern; pile bump."""
    m = bpy.data.materials.new(name); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; p = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord")
    sep = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs['UV'], sep.inputs[0])
    def band(axis, lo, hi):
        a = N.new("ShaderNodeMath"); a.operation = 'PINGPONG'; a.inputs[1].default_value = 0.5
        L.new(sep.outputs[axis], a.inputs[0])
        d = N.new("ShaderNodeMath"); d.operation = 'SUBTRACT'; d.inputs[0].default_value = 0.5; L.new(a.outputs[0], d.inputs[1])
        return d.outputs[0]
    ex = band('X', 0, 0); ey = band('Y', 0, 0)
    mn = N.new("ShaderNodeMath"); mn.operation = 'MINIMUM'; L.new(ex, mn.inputs[0]); L.new(ey, mn.inputs[1])
    ramp = N.new("ShaderNodeValToRGB"); cr = ramp.color_ramp; cr.interpolation = 'CONSTANT'
    cr.elements[0].position = 0.0; cr.elements[0].color = (0.05, 0.045, 0.09, 1)
    cr.elements[1].position = 0.04; cr.elements[1].color = (0.42, 0.24, 0.07, 1)
    e = cr.elements.new(0.06); e.color = (0.05, 0.045, 0.09, 1)
    e = cr.elements.new(0.11); e.color = (0.28, 0.035, 0.03, 1)
    L.new(mn.outputs[0], ramp.inputs['Fac'])
    vor = N.new("ShaderNodeTexVoronoi"); vor.inputs['Scale'].default_value = 9; vor.feature = 'DISTANCE_TO_EDGE'
    L.new(tc.outputs['UV'], vor.inputs['Vector'])
    vm = N.new("ShaderNodeMapRange"); vm.inputs['From Min'].default_value = 0.02; vm.inputs['From Max'].default_value = 0.05
    L.new(vor.outputs['Distance'], vm.inputs['Value'])
    pat = N.new("ShaderNodeMix"); pat.data_type = 'RGBA'; pat.inputs[6].default_value = (0.36, 0.22, 0.06, 1)
    L.new(vm.outputs[0], pat.inputs['Factor']); L.new(ramp.outputs['Color'], pat.inputs[7])
    inner = N.new("ShaderNodeMath"); inner.operation = 'GREATER_THAN'; inner.inputs[1].default_value = 0.11
    L.new(mn.outputs[0], inner.inputs[0])
    sel = N.new("ShaderNodeMix"); sel.data_type = 'RGBA'; L.new(inner.outputs[0], sel.inputs['Factor'])
    L.new(ramp.outputs['Color'], sel.inputs[6]); L.new(pat.outputs[2], sel.inputs[7])
    wear = N.new("ShaderNodeTexNoise"); wear.inputs['Scale'].default_value = 3; L.new(tc.outputs['UV'], wear.inputs['Vector'])
    wm = N.new("ShaderNodeMix"); wm.data_type = 'RGBA'; wm.blend_type = 'MULTIPLY'; wm.inputs['Factor'].default_value = 0.5
    L.new(sel.outputs[2], wm.inputs[6]); L.new(wear.outputs['Color'], wm.inputs[7])
    L.new(wm.outputs[2], p.inputs['Base Color'])
    p.inputs['Roughness'].default_value = 0.95; p.inputs['Sheen Weight'].default_value = 1.0
    pile = N.new("ShaderNodeTexNoise"); pile.inputs['Scale'].default_value = 900; L.new(tc.outputs['UV'], pile.inputs['Vector'])
    b = N.new("ShaderNodeBump"); b.inputs['Strength'].default_value = 0.5; L.new(pile.outputs['Fac'], b.inputs['Height'])
    L.new(b.outputs['Normal'], p.inputs['Normal'])
    return m


def cloth_material(name, color, sheen=0.8, rough=0.85, pattern=None):
    import cast
    return cast.cotton_material(name, color, rough=rough, sheen=sheen, pattern=pattern)


def paper_material(name="letter", ink=True, lines=22):
    """Laid writing paper with lines of copperplate (procedural strokes)."""
    m = bpy.data.materials.new(name); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; p = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord")
    base = N.new("ShaderNodeRGB"); base.outputs[0].default_value = (0.78, 0.72, 0.6, 1)
    out = base.outputs[0]
    if ink:
        sep = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs['UV'], sep.inputs[0])
        # rows
        ry = N.new("ShaderNodeMath"); ry.operation = 'MULTIPLY'; ry.inputs[1].default_value = lines; L.new(sep.outputs['Y'], ry.inputs[0])
        fr = N.new("ShaderNodeMath"); fr.operation = 'FRACT'; L.new(ry.outputs[0], fr.inputs[0])
        row = N.new("ShaderNodeMapRange"); row.inputs['From Min'].default_value = 0.25; row.inputs['From Max'].default_value = 0.6
        row.clamp = True; L.new(fr.outputs[0], row.inputs['Value'])
        pp = N.new("ShaderNodeMath"); pp.operation = 'PINGPONG'; pp.inputs[1].default_value = 0.5; L.new(row.outputs[0], pp.inputs[0])
        rowm = N.new("ShaderNodeMath"); rowm.operation = 'GREATER_THAN'; rowm.inputs[1].default_value = 0.18; L.new(pp.outputs[0], rowm.inputs[0])
        # strokes along the row: high-frequency wave distorted, broken into words
        wv = N.new("ShaderNodeTexWave"); wv.wave_type = 'BANDS'; wv.bands_direction = 'X'; wv.inputs['Scale'].default_value = 140
        wv.inputs['Distortion'].default_value = 9; wv.inputs['Detail'].default_value = 3; L.new(tc.outputs['UV'], wv.inputs['Vector'])
        sm = N.new("ShaderNodeMapRange"); sm.inputs['From Min'].default_value = 0.82; sm.inputs['From Max'].default_value = 0.9
        L.new(wv.outputs['Fac'], sm.inputs['Value'])
        wd = N.new("ShaderNodeTexNoise"); wd.inputs['Scale'].default_value = 26; L.new(tc.outputs['UV'], wd.inputs['Vector'])
        wdm = N.new("ShaderNodeMath"); wdm.operation = 'GREATER_THAN'; wdm.inputs[1].default_value = 0.42; L.new(wd.outputs['Fac'], wdm.inputs[0])
        # margins and the unwritten bottom of the page
        mx = N.new("ShaderNodeMapRange"); mx.inputs['From Min'].default_value = 0.08; mx.inputs['From Max'].default_value = 0.081
        L.new(sep.outputs['X'], mx.inputs['Value'])
        mx2 = N.new("ShaderNodeMapRange"); mx2.inputs['From Min'].default_value = 0.93; mx2.inputs['From Max'].default_value = 0.92
        L.new(sep.outputs['X'], mx2.inputs['Value'])
        my = N.new("ShaderNodeMapRange"); my.inputs['From Min'].default_value = 0.38; my.inputs['From Max'].default_value = 0.381
        L.new(sep.outputs['Y'], my.inputs['Value'])
        m1 = N.new("ShaderNodeMath"); m1.operation = 'MULTIPLY'; L.new(sm.outputs[0], m1.inputs[0]); L.new(rowm.outputs[0], m1.inputs[1])
        m2 = N.new("ShaderNodeMath"); m2.operation = 'MULTIPLY'; L.new(m1.outputs[0], m2.inputs[0]); L.new(wdm.outputs[0], m2.inputs[1])
        m3 = N.new("ShaderNodeMath"); m3.operation = 'MULTIPLY'; L.new(m2.outputs[0], m3.inputs[0]); L.new(mx.outputs[0], m3.inputs[1])
        m4 = N.new("ShaderNodeMath"); m4.operation = 'MULTIPLY'; L.new(m3.outputs[0], m4.inputs[0]); L.new(mx2.outputs[0], m4.inputs[1])
        m5 = N.new("ShaderNodeMath"); m5.operation = 'MULTIPLY'; L.new(m4.outputs[0], m5.inputs[0]); L.new(my.outputs[0], m5.inputs[1])
        mix = N.new("ShaderNodeMix"); mix.data_type = 'RGBA'; mix.inputs[7].default_value = (0.03, 0.025, 0.04, 1)
        L.new(m5.outputs[0], mix.inputs['Factor']); L.new(out, mix.inputs[6]); out = mix.outputs[2]
        m["ink_mask_node"] = m5.name
    L.new(out, p.inputs['Base Color']); p.inputs['Roughness'].default_value = 0.7
    p.inputs['Sheen Weight'].default_value = 0.3
    tr = N.new("ShaderNodeBsdfTranslucent"); L.new(out, tr.inputs['Color'])
    mx3 = N.new("ShaderNodeMixShader"); mx3.inputs[0].default_value = 0.15
    L.new(p.outputs[0], mx3.inputs[1]); L.new(tr.outputs[0], mx3.inputs[2])
    L.new(mx3.outputs[0], N["Material Output"].inputs['Surface'])
    return m


def sheet(name, c, w, d, mat, rot=0.0, curl=0.004):
    nx, ny = 20, 26
    V = []; F = []; UV = []
    for j in range(ny + 1):
        for i in range(nx + 1):
            u, v = i / nx, j / ny
            x = (u - 0.5) * w; y = (v - 0.5) * d
            z = curl * (math.sin(u * math.pi) * 0.4 + (v - 0.5) ** 2 * 1.5)
            xr = x * math.cos(rot) - y * math.sin(rot); yr = x * math.sin(rot) + y * math.cos(rot)
            V.append((c[0] + xr, c[1] + yr, c[2] + z)); UV.append((u, v))
    for j in range(ny):
        for i in range(nx):
            a = j * (nx + 1) + i
            F.append([a, a + 1, a + nx + 2, a + nx + 1])
    o = ship.mesh_obj(name, V, F, mat)
    uv = o.data.uv_layers.new(name="UVMap")
    for l in o.data.loops:
        uv.data[l.index].uv = UV[l.vertex_index]
    o.modifiers.new("t", "SOLIDIFY").thickness = 0.0004
    return o


# ----------------------------------------------------------------------------- build
def build(mood="warm", letter_side=1, wet=0.0, lamp_on=True, skylight=1.0, organ=True, letters=True, family=True, slate=False,
          chrono="full", maquette=False, slate_at=(-0.1, -0.08)):
    """mood: warm (New York morning), night (evening, lamp only), dawn (25 Nov), cold (Deveau, 4 Dec)."""
    A = {}
    wd = wet
    walnut = M("dark_wooden_planks", 1.6, tint=(0.9, 0.62, 0.42), name="walnut", wet=wd * 0.3)
    pine = M("wood_floor_deck", 1.1, tint=(0.95, 0.78, 0.6), name="sole", wet=wd)
    paint_c = ship.paint("cream", (0.72, 0.6, 0.42), rough=0.4, grime=0.15, scale=5, chips=0.05)
    beams = ship.paint("beams", (0.6, 0.52, 0.38), rough=0.5, grime=0.5, scale=6)
    mahog = M("brown_planks_05", 5.0, tint=(0.75, 0.42, 0.26), name="mahogany", wet=wd * 0.2)
    br = brass()
    # sole, bulkheads (walnut wainscot below, cream panels above), deckhead with beams and skylight
    box("floor_sole", (0, 0, -0.03), (2 * RX, 2 * RY, 0.06), pine)
    for sg in (1, -1):
        box(f"wain_y{sg}", (0, sg * (RY + 0.03), 0.45), (2 * RX + 0.3, 0.06, 0.9), walnut)
        box(f"wall_y{sg}", (0, sg * (RY + 0.035), 0.9 + (RZ - 0.9) / 2), (2 * RX + 0.3, 0.06, RZ - 0.9 + 0.15), paint_c)
        box(f"wain_x{sg}", (sg * (RX + 0.03), 0, 0.45), (0.06, 2 * RY + 0.3, 0.9), walnut)
        box(f"wall_x{sg}", (sg * (RX + 0.035), 0, 0.9 + (RZ - 0.9) / 2), (0.06, 2 * RY + 0.3, RZ - 0.9 + 0.15), paint_c)
        box(f"rail_y{sg}", (0, sg * (RY - 0.005), 0.92), (2 * RX, 0.04, 0.05), mahog, bevel=0.006)
        box(f"rail_x{sg}", (sg * (RX - 0.005), 0, 0.92), (0.04, 2 * RY, 0.05), mahog, bevel=0.006)
    # raised panel mouldings on the upper bulkheads
    for k in range(7):
        xx = -RX + 0.28 + k * 0.56
        if COMP["x0"] - 0.2 < xx:
            continue
        for (y, z0, z1) in ((-(RY - 0.004), 1.02, 1.9),):
            box("stile", (xx, y, (z0 + z1) / 2), (0.05, 0.02, z1 - z0), mahog)
    sx, sy, sw, sh = SKY
    box("ceil_a", ((sx - sw / 2 - RX) / 2, 0, RZ + 0.03), (sx - sw / 2 + RX, 2 * RY, 0.06), beams)
    box("ceil_b", ((sx + sw / 2 + COMP["x0"]) / 2, 0.3, RZ + 0.03), (COMP["x0"] - sx - sw / 2, 2 * RY + 0.6, 0.06), beams)
    box("ceil_b2", ((COMP["x0"] + RX) / 2, (COMP["y1"] + RY) / 2, RZ + 0.03), (RX - COMP["x0"], RY - COMP["y1"], 0.06), beams)
    box("ceil_c", (sx, (sy - sh / 2 - RY) / 2, RZ + 0.03), (sw, sy - sh / 2 + RY, 0.06), beams)
    box("ceil_d", (sx, (sy + sh / 2 + RY) / 2, RZ + 0.03), (sw, RY - sy - sh / 2, 0.06), beams)
    x = -RX + 0.22
    while x < RX:
        if abs(x - sx) > sw / 2 + 0.06 and x < COMP["x0"] - 0.05:
            box("beam", (x, 0, RZ - 0.06), (0.1, 2 * RY, 0.12), beams, bevel=0.01)
        x += 0.5
    for sg in (1, -1):
        box("well", (sx + sg * (sw / 2 + 0.025), sy, RZ + 0.22), (0.05, sh + 0.1, 0.44), mahog)
        box("well", (sx, sy + sg * (sh / 2 + 0.025), RZ + 0.22), (sw + 0.1, 0.05, 0.44), mahog)
    for k in range(1, 3):
        box("glazing_bar", (sx - sw / 2 + k * sw / 3, sy, RZ + 0.42), (0.022, sh, 0.028), mahog)
    glass = bpy.data.materials.new("skyglass"); glass.use_nodes = True
    gp = glass.node_tree.nodes["Principled BSDF"]; gp.inputs['Transmission Weight'].default_value = 1.0
    gp.inputs['Roughness'].default_value = 0.15; gp.inputs['Base Color'].default_value = (0.85, 0.88, 0.8, 1)
    box("skylight_glass", (sx, sy, RZ + 0.43), (sw, sh, 0.006), glass)
    # three small lights high in the starboard (-y) side of the trunk
    A["windows"] = []
    for k, wx in enumerate((-1.2, -0.25, 0.7)):
        cy = -(RY + 0.035)
        for sg in (1, -1):
            box("wframe", (wx + sg * 0.17, cy + 0.02, 1.62), (0.04, 0.1, 0.3), mahog)
            box("wframe", (wx, cy + 0.02, 1.62 + sg * 0.13), (0.38, 0.1, 0.04), mahog)
        box("wglass", (wx, cy, 1.62), (0.3, 0.004, 0.22), glass)
        A["windows"].append(Vector((wx, cy, 1.62)))
    # cut holes in the starboard upper wall behind the windows: rebuild it in pieces
    w = bpy.data.objects["wall_y-1"]
    bpy.data.objects.remove(w)
    cy = -(RY + 0.035)
    zs = [(0.9, 1.49), (1.75, RZ + 0.05)]
    for (z0, z1) in zs:
        box("wall_s", (0, cy, (z0 + z1) / 2), (2 * RX + 0.3, 0.06, z1 - z0 + 0.02), paint_c)
    xs = [-RX, -1.37, -1.03, -0.42, -0.08, 0.53, 0.87, RX]
    for a, b in zip(xs[0::2], xs[1::2]):
        box("wall_s", ((a + b) / 2, cy, 1.62), (b - a + (0.3 if a == -RX or b == RX else 0.0), 0.06, 0.28), paint_c)
    # companion ladder up to the deck, with the hatch opening above
    cx0, cx1, cy0, cy1 = COMP["x0"], COMP["x1"], COMP["y0"], COMP["y1"]
    for k in range(8):
        t = (k + 1) / 9
        box("step", (cx0 + 0.12 + (cx1 - cx0 - 0.2) * t, (cy0 + cy1) / 2, RZ * t), (0.2, cy1 - cy0 - 0.06, 0.035), mahog, bevel=0.004)
    for yy in (cy0 + 0.02, cy1 - 0.02):
        o = box("stringer", ((cx0 + cx1) / 2 + 0.05, yy, RZ / 2), (math.hypot(cx1 - cx0, RZ) + 0.1, 0.035, 0.18), mahog)
        o.rotation_euler = (0, -math.atan2(RZ, cx1 - cx0 - 0.2), 0)
    box("comp_beam", (cx0, (cy0 + cy1) / 2, RZ - 0.07), (0.1, cy1 - cy0, 0.14), beams, bevel=0.01)
    A["comp_beam"] = Vector((cx0, (cy0 + cy1) / 2, RZ - 0.14))
    box("comp_coaming", ((cx0 + cx1) / 2, cy1 + 0.02, RZ + 0.25), (cx1 - cx0, 0.05, 0.5), mahog)
    # ---- table: mahogany top, turned legs, a chenille cloth with a fringe
    tx, ty, tz = TABLE
    box("table_top", (tx, ty, tz - 0.02), (TW, TD, 0.04), mahog, bevel=0.01)
    box("table_apron", (tx, ty, tz - 0.06), (TW - 0.1, TD - 0.1, 0.04), mahog)
    leg = [(0.03, 0), (0.035, 0.05), (0.025, 0.12), (0.03, 0.3), (0.042, 0.45), (0.028, 0.55), (0.032, 0.66), (0.03, tz - 0.04)]
    for sx_ in (-1, 1):
        for sy_ in (-1, 1):
            lathe("table_leg", leg, mahog, center=(tx + sx_ * (TW / 2 - 0.08), ty + sy_ * (TD / 2 - 0.08), 0))
    A["table"] = TABLE.copy()
    clothm = cloth_material("tablecloth", (0.2, 0.035, 0.03), sheen=0.25, rough=0.9)
    _tablecloth(tx, ty, tz, TW + 0.02, TD + 0.02, clothm)
    # ---- chairs (Poly Haven), one each side of the table
    A["chairs"] = []
    for (cy_, yaw) in ((ty - 0.66, math.pi), (ty + 0.66, 0.0)):
        r, ms = S.place_model("WoodenChair_01", (tx - 0.05, cy_, 0), size=1.02, rot_z=yaw)
        A["chairs"].append((Vector((tx - 0.05, cy_, 0)), yaw, ms))
    lo, hi = ph.bounds(A["chairs"][0][2])
    lo, hi = ph.bounds(A["chairs"][0][2])
    A["seat_z"] = 0.48
    # ---- the lamp on the table (Poly Haven vintage oil lamp) with its flame
    if lamp_on is not None:
        r, ms = S.place_model("vintage_oil_lamp", (tx + 0.33, ty + 0.18, tz), size=0.42)
        lo, hi = ph.bounds(ms)
        A["lamp"] = Vector((tx + 0.33, ty + 0.18, lo.z + (hi.z - lo.z) * 0.52))
        if lamp_on:
            S.flame("flame", A["lamp"], h=0.035, strength=80)
            S.point("LampLight", A["lamp"] + Vector((0, 0, 0.02)), 22, color=(1.0, 0.62, 0.3), radius=0.03)
    # ---- the berth along the port side, curtained; patchwork quilt
    b = BERTH
    box("berth_board", ((b["x0"] + b["x1"]) / 2, b["y0"], 0.38), (b["x1"] - b["x0"], 0.05, 0.76), mahog, bevel=0.006)
    box("berth_base", ((b["x0"] + b["x1"]) / 2, (b["y0"] + RY) / 2, b["top"] - 0.18), (b["x1"] - b["x0"], RY - b["y0"], 0.04), mahog)
    box("berth_end", (b["x1"] + 0.03, (b["y0"] + RY) / 2, 0.95), (0.05, RY - b["y0"] + 0.05, 1.9), walnut)
    box("berth_top", ((b["x0"] + b["x1"]) / 2, (b["y0"] + RY) / 2, 1.62), (b["x1"] - b["x0"], RY - b["y0"], 0.04), mahog)
    box("mattress", ((b["x0"] + b["x1"]) / 2, (b["y0"] + RY) / 2 + 0.02, b["top"] - 0.08), (b["x1"] - b["x0"] - 0.04, RY - b["y0"] - 0.06, 0.16),
        cloth_material("ticking", (0.6, 0.56, 0.48), pattern="stripe"), bevel=0.04)
    quilt = cloth_material("quilt", (0.45, 0.2, 0.08), sheen=0.6, pattern="check")
    _quilt((b["x0"] + 0.5, b["x1"] - 0.02), (b["y0"] + 0.03, RY - 0.03), b["top"] + 0.005, quilt)
    lathe("pillow", [(0.0, 0), (0.18, 0.02), (0.2, 0.06), (0.16, 0.1), (0.0, 0.11)], cloth_material("pillow", (0.72, 0.7, 0.64)),
          center=(b["x0"] + 0.3, (b["y0"] + RY) / 2, b["top"] - 0.005)).scale = (1.0, 1.4, 1.0)
    _curtain(b["x1"] - 0.6, b["x1"] - 0.02, b["y0"] - 0.03, 1.58, 0.1, cloth_material("curtain", (0.32, 0.07, 0.05), sheen=1.0))
    A["berth"] = Vector(((b["x0"] + b["x1"]) / 2, (b["y0"] + RY) / 2, b["top"]))
    # ---- Sarah's reed organ against the after bulkhead
    if organ:
        A["organ"] = _organ(ORGAN, mahog, br)
    # ---- sideboard + fiddled shelf + books, chronometer box, clock on the starboard side
    sbx = -1.0
    box("sideboard", (sbx, -RY + 0.24, 0.42), (1.2, 0.46, 0.84), mahog, bevel=0.01)
    for k in range(3):
        box("sb_door", (sbx - 0.4 + k * 0.4, -RY + 0.47, 0.42), (0.36, 0.01, 0.68), walnut)
        cyl("sb_knob", (sbx - 0.28 + k * 0.4, -RY + 0.47, 0.5), (sbx - 0.28 + k * 0.4, -RY + 0.495, 0.5), 0.012, br, verts=10)
    box("fiddle", (sbx, -RY + 0.46, 0.89), (1.2, 0.015, 0.05), mahog)
    box("shelf", (sbx + 0.55, -RY + 0.12, 1.32), (1.3, 0.22, 0.025), mahog)
    box("shelf_fiddle", (sbx + 0.55, -RY + 0.225, 1.36), (1.3, 0.012, 0.06), mahog)
    try:
        r, ms = S.place_model("decorative_book_set_01", (sbx + 0.2, -RY + 0.12, 1.333), size=0.5, axis=0)
    except Exception:
        pass
    try:
        r, ms = S.place_model("mantel_clock_01", (sbx + 0.85, -RY + 0.12, 1.333), size=0.26)
    except Exception:
        pass
    A["chrono_box"] = _chronometer_box(Vector((sbx + 0.38, -RY + 0.24, 0.84)), mahog, br, state=chrono)
    A["sideboard_top"] = Vector((sbx, -RY + 0.24, 0.84))
    # ---- the rug
    rug = ship.mesh_obj("rug", [(-1.0, -1.0, 0.004), (1.15, -1.0, 0.004), (1.15, 0.78, 0.004), (-1.0, 0.78, 0.004)], [[0, 1, 2, 3]],
                        rug_material(), smooth=False)
    uv = rug.data.uv_layers.new(name="UVMap")
    for l, (u, v) in zip(rug.data.loops, [(0, 0), (1, 0), (1, 1), (0, 1)]):
        uv.data[l.index].uv = (u, v)
    rug.modifiers.new("t", "SOLIDIFY").thickness = 0.006
    # ---- the letter, inkwell and pen on the table
    if letters:
        A["letter"] = Vector((tx - 0.1, ty + 0.16 * letter_side, tz + 0.001))
        sheet("letter", A["letter"], 0.2, 0.25, paper_material("letter"), rot=0.12)
        sheet("letter2", A["letter"] + Vector((-0.24, 0.06, -0.0004)), 0.2, 0.25, paper_material("letter_b", lines=22), rot=-0.25)
        A["inkwell"] = _inkwell(A["letter"] + Vector((0.22, 0.05 * letter_side, 0)), br)
    if slate:
        A["slate"] = _slate(Vector((tx + slate_at[0], ty + slate_at[1], tz)), mahog)
    # ---- daylight through the skylight and the trunk lights; cabin air
    A["sky_c"] = Vector((sx, sy, RZ + 0.44))
    _light(mood, A, skylight)
    return A


def _tablecloth(tx, ty, tz, w, d, mat, drop=0.055):
    """A heavy cloth: flat on top, falling over each edge with soft folds and a rounded corner drape."""
    n = 60
    V = []; F = []
    hw, hd = w / 2, d / 2
    cols = n + 1
    for j in range(n + 1):
        for i in range(n + 1):
            u = -1 + 2 * i / n; v = -1 + 2 * j / n
            ex = max(0.0, (abs(u) * (hw + drop) - hw)) ; ey = max(0.0, (abs(v) * (hd + drop) - hd))
            x = math.copysign(min(abs(u) * (hw + drop), hw), u); y = math.copysign(min(abs(v) * (hd + drop), hd), v)
            e = math.hypot(ex, ey)
            if e > 0:
                fold = 0.012 * math.sin((x + y) * 38) * min(1, e / drop)
                x += math.copysign(0.012 + fold * (1 if ex > 0 else 0), u) * (ex > 0)
                y += math.copysign(0.012 + fold * (1 if ey > 0 else 0), v) * (ey > 0)
            z = tz + 0.003 - min(e, drop) * 1.0
            V.append((tx + x, ty + y, z))
    for j in range(n):
        for i in range(n):
            a = j * cols + i
            F.append([a, a + 1, a + cols + 1, a + cols])
    o = ship.mesh_obj("tablecloth", V, F, mat)
    o.modifiers.new("t", "SOLIDIFY").thickness = 0.003
    return o


def _quilt(xr, yr, z, mat):
    nx, ny = 40, 24
    V = []; F = []; UV = []
    for j in range(ny + 1):
        for i in range(nx + 1):
            u, v = i / nx, j / ny
            x = xr[0] + (xr[1] - xr[0]) * u; y = yr[0] + (yr[1] - yr[0]) * v
            dz = 0.025 + 0.012 * noise.noise(Vector((x * 4, y * 4, 0.3)))
            V.append((x, y, z + dz)); UV.append((u * 4, v * 2.4))
    for j in range(ny):
        for i in range(nx):
            a = j * (nx + 1) + i
            F.append([a, a + 1, a + nx + 2, a + nx + 1])
    o = ship.mesh_obj("quilt", V, F, mat)
    uv = o.data.uv_layers.new(name="UVMap")
    for l in o.data.loops:
        uv.data[l.index].uv = UV[l.vertex_index]
    o.modifiers.new("t", "SOLIDIFY").thickness = 0.01
    return o


def _curtain(x0, x1, y, ztop, gather, mat, zbot=0.66):
    n, m = 70, 30
    V = []; F = []
    for j in range(m + 1):
        for i in range(n + 1):
            u, v = i / n, j / m
            x = x0 + (x1 - x0) * u
            z = ztop - (ztop - zbot) * v
            yy = y - gather * 0.35 * (0.5 + 0.5 * math.sin(u * 2 * math.pi * 7)) * (0.6 + 0.4 * v)
            V.append((x, yy, z))
    for j in range(m):
        for i in range(n):
            a = j * (n + 1) + i
            F.append([a, a + 1, a + n + 2, a + n + 1])
    o = ship.mesh_obj("curtain", V, F, mat)
    o.modifiers.new("t", "SOLIDIFY").thickness = 0.003
    cyl("curtain_rod", (x0 - 0.05, y, ztop + 0.02), (x1 + 0.1, y, ztop + 0.02), 0.008, brass(), verts=10)
    return o


def _organ(p, wood_m, br):
    """A parlour reed organ (melodeon): cabinet, keyboard of 49 keys, music rest, two treadles, carved top."""
    x, y = p.x, p.y
    W, Dp, H = 1.05, 0.5, 0.78
    o = []
    box("organ_case", (x, y, H / 2 + 0.06), (Dp, W, H - 0.12), wood_m, bevel=0.012)
    box("organ_plinth", (x, y, 0.04), (Dp + 0.04, W + 0.04, 0.08), wood_m, bevel=0.01)
    box("organ_top", (x - 0.06, y, 1.12), (0.3, W, 0.5), wood_m, bevel=0.01)
    box("organ_cornice", (x - 0.06, y, 1.39), (0.34, W + 0.06, 0.05), wood_m, bevel=0.012)
    box("organ_keybed", (x + 0.2, y, H + 0.01), (0.22, W - 0.08, 0.03), wood_m)
    white = plain("ivory", (0.7, 0.65, 0.52), rough=0.3, coat=0.4); black = plain("ebony", (0.01, 0.008, 0.008), rough=0.25, coat=0.4)
    nk = 29; kw = (W - 0.14) / nk
    for k in range(nk):
        box("key", (x + 0.24, y - (W - 0.14) / 2 + kw * (k + 0.5), H + 0.035), (0.14, kw * 0.92, 0.018), white)
        if k % 7 not in (2, 6) and k < nk - 1:
            box("bkey", (x + 0.215, y - (W - 0.14) / 2 + kw * (k + 1), H + 0.052), (0.085, kw * 0.55, 0.02), black)
    box("music_rest", (x + 0.06, y, H + 0.2), (0.02, 0.5, 0.26), wood_m)
    for sg in (-1, 1):
        box("treadle", (x + 0.3, y + sg * 0.14, 0.12), (0.3, 0.2, 0.02), wood_m).rotation_euler = (0, math.radians(-14), 0)
        cyl("stop", (x + 0.12, y + sg * 0.35, H + 0.12), (x + 0.16, y + sg * 0.35, H + 0.12), 0.012, br, verts=12)
    # fretwork panel (cloth behind)
    box("organ_cloth", (x + Dp / 2 + 0.001, y, 0.45), (0.004, W - 0.2, 0.32), cloth_material("organ_cloth", (0.35, 0.06, 0.05)))
    return Vector((x + 0.25, y, H + 0.04))


def _chronometer_box(p, wood_m, br, state="full"):
    """A brass-bound mahogany box (lid up) with its shaped bed; the gimballed chronometer in it unless 'empty'."""
    w, d, h = 0.2, 0.2, 0.15
    box("chrono_base", (p.x, p.y, p.z + h / 2), (w, d, h), wood_m, bevel=0.004)
    for sx in (-1, 1):
        for sy in (-1, 1):
            box("chrono_corner", (p.x + sx * w / 2, p.y + sy * d / 2, p.z + h / 2), (0.008, 0.008, h + 0.004), br)
    lid = box("chrono_lid", (p.x, p.y + d / 2 + 0.01, p.z + h + d / 2), (w, 0.015, d), wood_m, bevel=0.003)
    inner = plain("velvet", (0.12, 0.02, 0.03), rough=1.0)
    box("chrono_bed", (p.x, p.y, p.z + h - 0.015), (w - 0.02, d - 0.02, 0.005), inner)
    if state == "full":
        cyl("chrono_bowl", (p.x, p.y, p.z + h - 0.06), (p.x, p.y, p.z + h + 0.005), 0.075, br, verts=40)
        face = plain("dial", (0.8, 0.76, 0.66), rough=0.3, coat=1.0)
        cyl("chrono_dial", (p.x, p.y, p.z + h + 0.004), (p.x, p.y, p.z + h + 0.0065), 0.066, face, verts=48)
        dk = plain("hands", (0.02, 0.02, 0.03), rough=0.3, metal=0.6)
        box("chrono_hand", (p.x, p.y + 0.02, p.z + h + 0.008), (0.004, 0.045, 0.001), dk).rotation_euler = (0, 0, 0.6)
        box("chrono_hand2", (p.x + 0.012, p.y, p.z + h + 0.0085), (0.03, 0.003, 0.001), dk).rotation_euler = (0, 0, -0.3)
        for k in range(12):
            a = k / 12 * 2 * math.pi
            box("tick", (p.x + 0.058 * math.cos(a), p.y + 0.058 * math.sin(a), p.z + h + 0.0068), (0.008, 0.002, 0.0006), dk).rotation_euler = (0, 0, a)
    else:
        # the empty shaped bed: a round velvet-lined hollow where the bowl sat
        cyl("chrono_hollow", (p.x, p.y, p.z + h - 0.06), (p.x, p.y, p.z + h - 0.014), 0.078, inner, verts=40)
    return Vector((p.x, p.y, p.z + h))


def _inkwell(p, br):
    g = bpy.data.materials.new("inkglass"); g.use_nodes = True
    gp = g.node_tree.nodes["Principled BSDF"]; gp.inputs['Transmission Weight'].default_value = 1.0
    gp.inputs['Roughness'].default_value = 0.05; gp.inputs['Base Color'].default_value = (0.7, 0.8, 0.75, 1)
    lathe("inkwell", [(0.0, 0), (0.03, 0.0), (0.032, 0.035), (0.012, 0.05), (0.012, 0.055), (0.0, 0.055)], g, center=tuple(p), n=24)
    lathe("ink", [(0.0, 0.003), (0.027, 0.003), (0.027, 0.02), (0.0, 0.02)], plain("ink", (0.005, 0.005, 0.01), rough=0.05), center=tuple(p), n=24)
    cyl("inklid", p + Vector((0, 0, 0.055)), p + Vector((0, 0, 0.065)), 0.014, br, verts=16)
    return p


def _slate(p, wood_m):
    """The log slate: a framed school slate with chalked columns."""
    w, d = 0.36, 0.26
    box("slate_frame", (p.x, p.y, p.z + 0.006), (w, d, 0.012), wood_m, bevel=0.003)
    m = bpy.data.materials.new("slate"); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; pr = N["Principled BSDF"]
    pr.inputs['Base Color'].default_value = (0.03, 0.035, 0.035, 1); pr.inputs['Roughness'].default_value = 0.75
    box("slate_face", (p.x, p.y, p.z + 0.0125), (w - 0.04, d - 0.04, 0.002), m)
    return Vector((p.x, p.y, p.z + 0.014))


def _light(mood, A, skylight):
    import look
    sc = bpy.context.scene
    sx, sy, sw, sh = SKY
    if mood in ("warm", "dawn", "cold"):
        sun_col = {"warm": (1.0, 0.82, 0.62), "dawn": (1.0, 0.62, 0.38), "cold": (0.78, 0.84, 0.95)}[mood]
        sky_col = {"warm": (0.55, 0.6, 0.7), "dawn": (0.6, 0.5, 0.5), "cold": (0.45, 0.5, 0.58)}[mood]
        w = bpy.data.worlds.new("w"); sc.world = w
        w.use_nodes = True; w.node_tree.nodes["Background"].inputs[0].default_value = (*sky_col, 1)
        w.node_tree.nodes["Background"].inputs[1].default_value = 0.6 * skylight
        # sun through the starboard lights and skylight: raking shafts across the cabin
        sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", 'SUN')); sc.collection.objects.link(sun)
        sun.data.energy = {"warm": 5.0, "dawn": 4.0, "cold": 0.0}[mood] * skylight; sun.data.color = sun_col
        sun.data.angle = math.radians(1.5)
        az, el = math.radians(-70), math.radians({"warm": 28, "dawn": 12, "cold": 40}[mood])
        sun.rotation_euler = (Vector((math.cos(az) * math.cos(el), math.sin(az) * math.cos(el), math.sin(el))) * -1).to_track_quat('-Z', 'Y').to_euler()
        S.area("SkyFill", A["sky_c"] + Vector((0, 0, 0.3)), A["sky_c"] - Vector((0, 0, 1)), 90 * skylight * (4.5 if mood == "cold" else 1),
               size=sw, size_y=sh, color=sky_col)
        for wv in A["windows"]:
            S.area("WinFill", wv + Vector((0, -0.08, 0)), wv + Vector((0, 1, -0.3)), 10 * skylight, size=0.3, size_y=0.22, color=sky_col)
        S.area("CompDay", Vector(((COMP["x0"] + COMP["x1"]) / 2 + 0.2, (COMP["y0"] + COMP["y1"]) / 2, RZ + 0.5)),
               Vector((COMP["x0"], (COMP["y0"] + COMP["y1"]) / 2, 0.5)), 120 * skylight * (2.5 if mood == "cold" else 1), size=0.6, color=sky_col)
        # air: a thin volume so the shafts read
        vol = bpy.data.materials.new("air"); vol.use_nodes = True
        N = vol.node_tree.nodes; N.remove(N["Principled BSDF"])
        pv = N.new("ShaderNodeVolumePrincipled"); pv.inputs['Density'].default_value = 0.05 if mood != "cold" else 0.08
        pv.inputs['Anisotropy'].default_value = 0.5
        vol.node_tree.links.new(pv.outputs[0], N["Material Output"].inputs['Volume'])
        o = ship.box("air", (0, 0, RZ / 2), (2 * RX - 0.02, 2 * RY - 0.02, RZ - 0.02), vol)
        o.visible_shadow = False
        if S.NOVOL:
            o.hide_render = True
    else:   # night: the lamp alone, a little moonless blue at the skylight
        w = bpy.data.worlds.new("w"); sc.world = w
        w.use_nodes = True; w.node_tree.nodes["Background"].inputs[0].default_value = (0.02, 0.025, 0.04, 1)
        w.node_tree.nodes["Background"].inputs[1].default_value = 0.3
    A["bounds"] = (-RX + 0.1, RX - 0.1, -RY + 0.1, RY - 0.1, 0.25, RZ - 0.08)
    S.area("Bounce", Vector((TABLE.x, TABLE.y, 0.2)), Vector((TABLE.x, TABLE.y, 1.6)), 8, size=1.2, color=(1, 0.7, 0.45))


def pen(name, hand_person, side="R"):
    """A dip pen held in the pinch of thumb and index: wooden holder, steel nib; parented to the wrist bone."""
    import poses as P
    h = hand_person.h
    bpy.context.view_layer.update()
    w = h.bone_head(f"wrist.{side}"); t1 = h.bone_tail(f"finger2-3.{side}") if f"finger2-3.{side}" in h.arm.pose.bones else h.bone_tail(f"wrist.{side}")
    th = h.bone_tail(f"finger1-3.{side}")
    grip = t1.lerp(th, 0.5)
    d = (grip - w).normalized()
    tip = grip + (d + Vector((0, 0, -0.9))).normalized() * 0.03
    top = grip - (tip - grip).normalized() * 0.13 + Vector((0, 0, 0.02))
    o = cyl(name, top, tip, 0.0045, plain("penholder", (0.08, 0.035, 0.015), rough=0.35, coat=0.5), r1=0.0035, verts=12)
    n = cyl(name + "_nib", tip, tip + (tip - top).normalized() * 0.012, 0.003, plain("nib", (0.2, 0.2, 0.22), rough=0.2, metal=1.0), r1=0.0003, verts=10)
    for x in (o, n):
        mw = x.matrix_world.copy(); x.parent = h.arm; x.parent_type = 'BONE'; x.parent_bone = f"wrist.{side}"
        bpy.context.view_layer.update(); x.matrix_world = mw
    return o


def attach(o, person, bone):
    h = person.h
    mw = o.matrix_world.copy(); o.parent = h.arm; o.parent_type = 'BONE'; o.parent_bone = bone
    bpy.context.view_layer.update(); o.matrix_world = mw
    return o


def doll(name, at, up=Vector((0, 0, 1)), s=1.0):
    """A china-head doll: glazed head with painted black hair, cloth body, calico dress, kid-leather arms."""
    china = plain("china", (0.8, 0.72, 0.66), rough=0.15, coat=1.0)
    hairp = plain("doll_hair", (0.01, 0.008, 0.008), rough=0.1, coat=1.0)
    dress = cloth_material("doll_dress", (0.35, 0.1, 0.12), pattern="check")
    kid = plain("kid", (0.62, 0.5, 0.36), rough=0.6)
    parts = []
    z = Vector(at)
    parts.append(lathe(name + "_skirt", [(0.0, 0), (0.05, 0.0), (0.045, 0.06), (0.03, 0.12), (0.02, 0.15), (0.0, 0.15)], dress, center=tuple(z), n=24))
    bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=16, radius=0.028, location=tuple(z + Vector((0, 0, 0.18))))
    hd = bpy.context.active_object; hd.name = name + "_head"; hd.data.materials.append(china); bpy.ops.object.shade_smooth()
    bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=16, radius=0.0295, location=tuple(z + Vector((0, 0.004, 0.186))))
    hr = bpy.context.active_object; hr.name = name + "_hair"; hr.scale = (1, 1, 0.75); hr.data.materials.append(hairp); bpy.ops.object.shade_smooth()
    parts += [hd, hr]
    for sg in (-1, 1):
        parts.append(cyl(name + "_arm", z + Vector((sg * 0.03, 0, 0.14)), z + Vector((sg * 0.05, -0.01, 0.07)), 0.009, kid, verts=10))
    root = bpy.data.objects.new(name, None); bpy.context.collection.objects.link(root); root.location = z
    for o in parts:
        mw = o.matrix_world.copy(); o.parent = root; o.matrix_world = mw
    root.scale = (s, s, s)
    return root


def bonnet(person, name="bonnet"):
    """An 1870s straw bonnet: a shallow crown over the bun, a brim framing the face; ribbons under the chin.
    Built in the head frame from the posed head and parented to the head bone."""
    h = person.h
    bpy.context.view_layer.update()
    hb = h.arm.matrix_world @ h.arm.pose.bones["head"].matrix
    R = hb.to_3x3().normalized() @ h.arm.data.bones["head"].matrix_local.to_3x3().inverted()
    eyes = [e.matrix_world.translation for e in h.eyes]
    ec = (eyes[0] + eyes[1]) / 2
    c = ec + R @ Vector((0, 0.05, 0.03))
    n = 48; V = []; F = []
    rings = [(0.0, 0.11), (0.06, 0.108), (0.095, 0.085), (0.112, 0.05), (0.118, 0.0), (0.122, -0.03)]
    for (r, z) in rings:
        for k in range(n):
            a = 2 * math.pi * k / n
            V.append(c + R @ Vector((r * math.cos(a), r * 1.12 * math.sin(a) + 0.01, z)))
    for j in range(len(rings) - 1):
        for k in range(n):
            a, b = j * n + k, j * n + (k + 1) % n
            F.append([a, b, b + n, a + n])
    st = straw()
    crown = ship.mesh_obj(name + "_crown", [tuple(v) for v in V], F, st)
    crown.modifiers.new("t", "SOLIDIFY").thickness = 0.004
    # brim: a band in front of the face, tilted up
    V2 = []; F2 = []
    m = 32
    for j, (r, rise) in enumerate(((0.12, 0.0), (0.155, 0.025))):
        for k in range(m + 1):
            a = math.pi * (0.05 + 0.9 * k / m) + math.pi    # front half (toward -Y)
            V2.append(c + R @ Vector((r * math.cos(a), r * 1.1 * math.sin(a) - 0.01 - 0.02 * j, -0.01 + rise + 0.02 * math.sin(math.pi * k / m))))
    for k in range(m):
        F2.append([k, k + 1, k + 1 + m + 1, k + m + 1])
    brim = ship.mesh_obj(name + "_brim", [tuple(v) for v in V2], F2, st)
    brim.modifiers.new("t", "SOLIDIFY").thickness = 0.004
    rib = cloth_material(name + "_ribbon", (0.25, 0.05, 0.08), sheen=1.0)
    for o in (crown, brim):
        attach(o, person, "head")
    return crown, brim


def straw():
    import cast
    return cast.straw_material("straw")


def sextant_case(p, wood_m, empty=True, yaw=0.0):
    """The sextant's wooden box, lid open, with the fitted wedge-shaped bed (empty)."""
    w, d, h = 0.3, 0.28, 0.12
    o = [box("sx_base", (p.x, p.y, p.z + h / 2), (w, d, h), wood_m, bevel=0.004)]
    o.append(box("sx_lid", (p.x, p.y + d / 2 + 0.008, p.z + h + d / 2 - 0.01), (w, 0.012, d), wood_m, bevel=0.003))
    vel = plain("sx_velvet", (0.05, 0.08, 0.15), rough=1.0)
    o.append(box("sx_bed", (p.x, p.y, p.z + h - 0.012), (w - 0.02, d - 0.02, 0.004), vel))
    if empty:
        # the wedge-shaped recess where the frame sat
        V = [(p.x - 0.1, p.y - 0.09, p.z + h - 0.009), (p.x + 0.1, p.y - 0.09, p.z + h - 0.009), (p.x, p.y + 0.11, p.z + h - 0.009)]
        o.append(ship.mesh_obj("sx_recess", V, [[0, 1, 2]], plain("sx_shadow", (0.01, 0.015, 0.03), rough=1.0), smooth=False))
    return o


def chalk_text(name, c, w, d, lines, size=0.018, rot=0.0):
    """Chalked slate entries as real text objects (Courier-like hand); flat on the slate face."""
    objs = []
    chalk = plain("chalk", (0.72, 0.72, 0.68), rough=0.95)
    for i, t in enumerate(lines):
        cu = bpy.data.curves.new(f"{name}{i}", 'FONT'); cu.body = t; cu.size = size
        try:
            cu.font = bpy.data.fonts.load(FONT_HAND)
        except Exception:
            pass
        o = bpy.data.objects.new(f"{name}{i}", cu); bpy.context.collection.objects.link(o)
        o.location = (c.x - w / 2 + 0.02, c.y + d / 2 - 0.04 - i * size * 1.6, c.z + 0.0006)
        o.data.materials.append(chalk)
        objs.append(o)
    return objs


import os as _os
FONT_HAND = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", "assets", "fonts", "CourierPrime-Regular.ttf")
