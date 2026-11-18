"""(b) The captain's cabin. Deveau holds a lantern over the berth: the bedding is soaked, and on the bed is an
impression that looks to him as though a child has been lying there. Grey daylight falls through the
skylight; the lantern is the warm key. Volumetric air, shallow depth of field."""
import os, sys, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C
C.reset()
import numpy as np
import bpy, bmesh
from mathutils import Vector, Matrix, noise
import ph, ship, poses as P
import human as H, deveau as D

OUT = os.environ.get("OUT", os.path.join(C.HERE, "..", "out", "frames", "b_cabin.png"))
sc = C.render_setup(samples=int(os.environ.get("SPP", "320")), noise=0.02, bounces=8)
sc.cycles.volume_bounces = 0

RX, RY, RZ = 1.75, 1.45, 2.02          # half-length (fore-aft), half-width, headroom
BX0, BX1, BY0 = -1.68, 0.42, 0.62       # berth: x span, inner edge (toward the room)
TOP = 0.60                               # mattress top
BOARD = 0.80                             # berth front board top
WET = 0.85


def mat_from(aid, scale, wet=0.0, tint=None, name=None):
    return ship.wood(aid, scale, wet=wet, tint=tint, name=name)


POSE_TEST = os.environ.get("POSE_TEST")
# ----------------------------------------------------------------------------- the room
walls = mat_from("dark_wooden_planks", 1.4, wet=0.15, tint=(0.3, 0.2, 0.13), name="walls")
walls.node_tree.nodes["Principled BSDF"].inputs["Coat Weight"].default_value = 0.35   # old varnish
floor = mat_from("weathered_planks", 0.9, wet=WET, tint=(0.8, 0.72, 0.62), name="floor")
beams_m = ship.paint("beams", (0.16, 0.12, 0.08), rough=0.5, grime=0.7, chips=0.3, scale=6)
berth_m = mat_from("brown_planks_05", 1.6, wet=0.3, tint=(0.34, 0.22, 0.14), name="berthwood")
berth_m.node_tree.nodes["Principled BSDF"].inputs["Coat Weight"].default_value = 0.3


def plane(name, verts, mat, uvscale=1.0):
    o = ship.mesh_obj(name, verts, [[0, 1, 2, 3]], mat, smooth=False)
    sub = o.modifiers.new("Sub", "SUBSURF"); sub.subdivision_type = 'SIMPLE'; sub.levels = 0; sub.render_levels = 0
    return o


ship.box("floor", (0, 0, -0.03), (2 * RX, 2 * RY, 0.06), floor)
for sg in (1, -1):
    ship.box(f"wall_y{sg}", (0, sg * (RY + 0.03), RZ / 2), (2 * RX, 0.06, RZ + 0.1), walls)
    ship.box(f"wall_x{sg}", (sg * (RX + 0.03), 0, RZ / 2), (0.06, 2 * RY, RZ + 0.1), walls)
# deckhead: planks with a skylight opening, and beams under it
SKY = (0.05, -0.55, 0.62, 0.5)           # skylight centre x, y, size x, y
sx, sy, sw, sh = SKY
ship.box("ceil_a", ((sx - sw / 2 - RX) / 2, 0, RZ + 0.03), (sx - sw / 2 + RX, 2 * RY, 0.06), beams_m)
ship.box("ceil_b", ((sx + sw / 2 + RX) / 2, 0, RZ + 0.03), (RX - sx - sw / 2, 2 * RY, 0.06), beams_m)
ship.box("ceil_c", (sx, (sy - sh / 2 - RY) / 2, RZ + 0.03), (sw, sy - sh / 2 + RY, 0.06), beams_m)
ship.box("ceil_d", (sx, (sy + sh / 2 + RY) / 2, RZ + 0.03), (sw, RY - sy - sh / 2, 0.06), beams_m)
x = -RX + 0.25
while x < RX:
    if abs(x - sx) > sw / 2 + 0.05:
        ship.box("beam", (x, 0, RZ - 0.07), (0.11, 2 * RY, 0.14), beams_m, bevel=0.01)
    x += 0.52
# skylight well and glazing bars
for sg in (1, -1):
    ship.box("well", (sx + sg * (sw / 2 + 0.02), sy, RZ + 0.2), (0.04, sh + 0.08, 0.4), beams_m)
    ship.box("well", (sx, sy + sg * (sh / 2 + 0.02), RZ + 0.2), (sw + 0.08, 0.04, 0.4), beams_m)
for k in range(1, 3):
    ship.box("glazing_bar", (sx - sw / 2 + k * sw / 3, sy, RZ + 0.38), (0.025, sh, 0.03), beams_m)
glass = bpy.data.materials.new("skyglass"); glass.use_nodes = True
gp = glass.node_tree.nodes["Principled BSDF"]; gp.inputs['Transmission Weight'].default_value = 1.0
gp.inputs['Roughness'].default_value = 0.25; gp.inputs['Base Color'].default_value = (0.8, 0.85, 0.8, 1)
ship.box("skylight_glass", (sx, sy, RZ + 0.39), (sw, sh, 0.008), glass)
# wainscot rail and panel stiles on the walls (gives the panelling scale)
for sg in (1, -1):
    ship.box("chair_rail", (0, sg * (RY - 0.015), 0.95), (2 * RX, 0.035, 0.06), berth_m, bevel=0.005)
for k in range(7):
    xx = -RX + 0.3 + k * 0.52
    ship.box("stile", (xx, -(RY - 0.012), 0.48), (0.08, 0.03, 0.9), berth_m)

# ----------------------------------------------------------------------------- berth
ship.box("berth_board", ((BX0 + BX1) / 2, BY0 - 0.02, BOARD / 2), (BX1 - BX0, 0.05, BOARD), berth_m, bevel=0.006)
ship.box("berth_board_cap", ((BX0 + BX1) / 2, BY0 - 0.02, BOARD + 0.015), (BX1 - BX0 + 0.04, 0.08, 0.03), berth_m, bevel=0.008)
ship.box("berth_end", (BX1 + 0.025, (BY0 + RY) / 2, BOARD / 2 + 0.1), (0.05, RY - BY0 + 0.04, BOARD + 0.2), berth_m, bevel=0.006)
ship.box("berth_base", ((BX0 + BX1) / 2, (BY0 + RY) / 2, TOP - 0.2), (BX1 - BX0, RY - BY0, 0.04), berth_m)
for k in range(3):                                         # drawers under the berth
    xx = BX0 + 0.38 + k * 0.68
    ship.box("drawer", (xx, BY0 - 0.05, 0.22), (0.6, 0.02, 0.28), berth_m, bevel=0.004)
    ship.cyl("knob", (xx, BY0 - 0.06, 0.24), (xx, BY0 - 0.085, 0.24), 0.014, mat=beams_m, verts=12)
# berth canopy shelf above
ship.box("berth_shelf", ((BX0 + BX1) / 2, RY - 0.18, 1.62), (BX1 - BX0, 0.36, 0.03), berth_m)
ship.box("berth_valance", ((BX0 + BX1) / 2, RY - 0.36, 1.56), (BX1 - BX0, 0.025, 0.14), berth_m)

# mattress with the impression
CHILD = dict(cx=-0.66, cy=(BY0 + RY) / 2 - 0.03, length=1.0)


def impression(x, y):
    """Depth (0..1) of a small body's hollow: head, shoulders/torso, hips, legs (lying on its side, curled)."""
    cx, cy = CHILD["cx"], CHILD["cy"]
    u = (x - cx); v = (y - cy)
    parts = [(-0.42, 0.02, 0.085, 0.075, 1.0),      # head (toward the berth's head, -x)
             (-0.2, 0.0, 0.16, 0.11, 0.85),          # shoulders / torso
             (0.02, -0.01, 0.13, 0.1, 0.8),          # hips
             (0.24, 0.04, 0.16, 0.07, 0.55),         # thighs (knees drawn up a little)
             (0.42, 0.07, 0.11, 0.05, 0.35)]         # shins
    d = 0.0
    for px, py, rx, ry, w in parts:
        r2 = ((u - px) / rx) ** 2 + ((v - py) / ry) ** 2
        d = max(d, w * math.exp(-1.6 * r2 ** 1.4))
    return d


def mattress():
    nx, ny = 150, 60
    x0, x1, y0, y1 = BX0 + 0.03, BX1 - 0.03, BY0 + 0.03, RY - 0.03
    V = []; F = []; UV = []
    for j in range(ny + 1):
        for i in range(nx + 1):
            x = x0 + (x1 - x0) * i / nx; y = y0 + (y1 - y0) * j / ny
            edge = min(i, nx - i, j, ny - j) / 4.0
            roll = 1 - math.exp(-edge)                       # rounded mattress edges
            z = TOP - 0.085 * impression(x, y) - 0.03 * (1 - roll)
            z += 0.004 * noise.noise(Vector((x * 6, y * 6, 0.5))) + 0.014 * noise.noise(Vector((x * 2.6, y * 3.1, 4.2))) * roll
            z -= 0.012 * math.exp(-((x - (BX0 + 0.25)) / 0.25) ** 2) * 0                # (pillow sits here)
            V.append((x, y, z)); UV.append(((x - x0) * 2, (y - y0) * 2))
    for j in range(ny):
        for i in range(nx):
            a = j * (nx + 1) + i
            F.append([a, a + 1, a + nx + 2, a + nx + 1])
    return V, F, UV


def wet_cloth_mat(name, color, wet, stripes=False, sheen=0.4):
    m = bpy.data.materials.new(name); m.use_nodes = True
    N = m.node_tree.nodes; Lk = m.node_tree.links; p = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord")
    c = N.new("ShaderNodeRGB"); c.outputs[0].default_value = (*color, 1)
    base = c.outputs[0]
    if stripes:
        wv = N.new("ShaderNodeTexWave"); wv.wave_type = 'BANDS'; wv.bands_direction = 'Y'; wv.inputs['Scale'].default_value = 26
        wv.inputs['Distortion'].default_value = 0.2; Lk.new(tc.outputs['UV'], wv.inputs['Vector'])
        st = N.new("ShaderNodeMapRange"); st.inputs['From Min'].default_value = 0.55; st.inputs['From Max'].default_value = 0.6
        Lk.new(wv.outputs['Fac'], st.inputs['Value'])
        sm = N.new("ShaderNodeMix"); sm.data_type = 'RGBA'; sm.inputs[7].default_value = (0.09, 0.1, 0.13, 1)
        Lk.new(st.outputs[0], sm.inputs['Factor']); Lk.new(base, sm.inputs[6]); base = sm.outputs[2]
    # wet patches: a soaked map (darker, glossier), tide marks at the edges
    wn = N.new("ShaderNodeTexNoise"); wn.inputs['Scale'].default_value = 2.2; wn.inputs['Detail'].default_value = 6
    Lk.new(tc.outputs['Object'], wn.inputs['Vector'])
    wm = N.new("ShaderNodeMapRange"); wm.inputs['From Min'].default_value = 0.42 - 0.2 * wet; wm.inputs['From Max'].default_value = 0.5 - 0.2 * wet
    Lk.new(wn.outputs['Fac'], wm.inputs['Value'])
    dk = N.new("ShaderNodeMix"); dk.data_type = 'RGBA'; dk.blend_type = 'MULTIPLY'; dk.inputs[7].default_value = (0.52, 0.5, 0.47, 1)
    Lk.new(wm.outputs[0], dk.inputs['Factor']); Lk.new(base, dk.inputs[6])
    tide = N.new("ShaderNodeMapRange"); tide.inputs['From Min'].default_value = 0.38 - 0.2 * wet; tide.inputs['From Max'].default_value = 0.42 - 0.2 * wet
    tide.inputs['To Min'].default_value = 0; tide.inputs['To Max'].default_value = 1
    Lk.new(wn.outputs['Fac'], tide.inputs['Value'])
    td = N.new("ShaderNodeMix"); td.data_type = 'RGBA'; td.blend_type = 'MULTIPLY'; td.inputs[7].default_value = (0.8, 0.72, 0.6, 1)
    tm = N.new("ShaderNodeMath"); tm.operation = 'PINGPONG'; tm.inputs[1].default_value = 0.5; Lk.new(tide.outputs[0], tm.inputs[0])
    Lk.new(tm.outputs[0], td.inputs['Factor']); Lk.new(dk.outputs[2], td.inputs[6])
    Lk.new(td.outputs[2], p.inputs['Base Color'])
    rr = N.new("ShaderNodeMapRange"); rr.inputs['To Min'].default_value = 0.9; rr.inputs['To Max'].default_value = 0.5
    Lk.new(wm.outputs[0], rr.inputs['Value']); Lk.new(rr.outputs[0], p.inputs['Roughness'])
    p.inputs['Sheen Weight'].default_value = sheen; p.inputs['Specular IOR Level'].default_value = 0.55
    wv2 = N.new("ShaderNodeTexWave"); wv2.inputs['Scale'].default_value = 300; Lk.new(tc.outputs['Object'], wv2.inputs['Vector'])
    b = N.new("ShaderNodeBump"); b.inputs['Strength'].default_value = 0.12; Lk.new(wv2.outputs['Fac'], b.inputs['Height'])
    Lk.new(b.outputs['Normal'], p.inputs['Normal'])
    return m


V, F, UV = mattress()
matt = ship.mesh_obj("mattress", V, F, wet_cloth_mat("ticking", (0.46, 0.4, 0.3), WET, stripes=True))
uvl = matt.data.uv_layers.new(name="UVMap")
for l in matt.data.loops:
    uvl.data[l.index].uv = UV[l.vertex_index]
so = matt.modifiers.new("Thick", "SOLIDIFY"); so.thickness = 0.16; so.offset = -1
# sheet: follows the mattress and the hollow, with creases radiating from it; turned back at the foot
sheet_V = []
for (x, y, z) in V:
    d = impression(x, y)
    cr = 0.006 * noise.noise(Vector((x * 9, y * 14, 2.0))) * (0.3 + d) + 0.009 * noise.noise(Vector((x * 5, y * 21, 7.0))) ** 2 + 0.006 * math.sin((y - CHILD["cy"]) * 55 + x * 11) * min(1.0, 3 * d * (1 - d))
    sheet_V.append((x, y, z + 0.006 + cr))
keepF = [f for f in F if V[f[0]][0] < BX1 - 0.55]
sheet_m = wet_cloth_mat("sheet", (0.26, 0.21, 0.16), WET + 0.1, sheen=0.55)   # grey-brown wool blanket over the mattress
sheet = ship.mesh_obj("sheet", sheet_V, keepF, sheet_m)
# water lying in the hollow: the sheet there is soaked through (darker, glossy)
ca = sheet.data.color_attributes.new("imp", 'FLOAT_COLOR', 'POINT')
for i, (x, y, z) in enumerate(sheet_V):
    d = min(1.0, impression(x, y) * 1.25); ca.data[i].color = (d, d, d, 1)
_N = sheet_m.node_tree.nodes; _L = sheet_m.node_tree.links; _p = _N["Principled BSDF"]
_at = _N.new("ShaderNodeAttribute"); _at.attribute_name = "imp"
_bc = _p.inputs['Base Color'].links[0].from_socket
_dk = _N.new("ShaderNodeMix"); _dk.data_type = 'RGBA'; _dk.blend_type = 'MULTIPLY'; _dk.inputs[7].default_value = (0.42, 0.4, 0.37, 1)
_L.new(_at.outputs['Fac'], _dk.inputs['Factor']); _L.new(_bc, _dk.inputs[6]); _L.new(_dk.outputs[2], _p.inputs['Base Color'])
_rs = _p.inputs['Roughness'].links[0].from_socket
_rm = _N.new("ShaderNodeMix"); _rm.data_type = 'FLOAT'; _rm.inputs[3].default_value = 0.12
_L.new(_at.outputs['Fac'], _rm.inputs['Factor']); _L.new(_rs, _rm.inputs[2]); _L.new(_rm.outputs[0], _p.inputs['Roughness'])
uvl = sheet.data.uv_layers.new(name="UVMap")
for l in sheet.data.loops:
    uvl.data[l.index].uv = UV[l.vertex_index]
sheet.modifiers.new("Thick", "SOLIDIFY").thickness = 0.002
# blanket: thrown back in a heavy wet heap toward the foot, one corner over the board
def blanket():
    nx, ny = 70, 46
    V = []; F = []
    for j in range(ny + 1):
        for i in range(nx + 1):
            u = i / nx; v = j / ny
            x = BX1 - 1.0 + 0.98 * u
            y = BY0 - 0.12 + (RY - BY0 + 0.1) * v
            # folds: a few big rolls across the bed plus noise
            h = 0.03 + 0.06 * math.sin(u * math.pi * 4.2 + v * 2.1) ** 2 * (0.4 + u) + 0.03 * noise.noise(Vector((u * 7, v * 6, 3.0))) + 0.015 * noise.noise(Vector((u * 19, v * 17, 1.0)))
            z = TOP + 0.01 + h
            if y < BY0 + 0.02:                      # spills over the berth board and hangs down
                over = (BY0 + 0.02 - y)
                z = BOARD + 0.03 - over * 5.0 * (0.6 + 0.4 * u)
                y = BY0 - 0.06 - 0.02 * math.sin(u * 9)
            V.append((x, y, z))
    for j in range(ny):
        for i in range(nx):
            a = j * (nx + 1) + i
            F.append([a, a + 1, a + nx + 2, a + nx + 1])
    return V, F
bV, bF = blanket()
bl = ship.mesh_obj("blanket", bV, bF, wet_cloth_mat("blanket", (0.1, 0.075, 0.055), WET, sheen=0.6))
bl.modifiers.new("Thick", "SOLIDIFY").thickness = 0.008
s = bl.modifiers.new("Sub", "SUBSURF"); s.levels = 1; s.render_levels = 2
# pillow with the dent of a small head
bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, radius=1, location=(BX0 + 0.24, CHILD["cy"] + 0.03, TOP + 0.06))
pil = bpy.context.active_object; pil.name = "pillow"; pil.scale = (0.2, 0.3, 0.07)
bpy.ops.object.transform_apply(scale=True)
for v in pil.data.vertices:
    w = pil.matrix_world @ v.co
    dd = math.exp(-(((w.x - (BX0 + 0.3)) / 0.08) ** 2 + ((w.y - (CHILD["cy"] + 0.02)) / 0.08) ** 2))
    if v.co.z > 0:
        v.co.z -= 0.035 * dd
    v.co.z = max(v.co.z, -0.055)
bpy.ops.object.shade_smooth()
pil.data.materials.append(wet_cloth_mat("pillowcase", (0.5, 0.46, 0.38), WET))

# ----------------------------------------------------------------------------- props
r, ms = ph.model("wooden_handle_saber")       # the sword from beneath the captain's berth (in its sheath)
r.location = (BX0 + 0.9, BY0 + 0.08, 0.035); r.rotation_euler = (math.radians(90), 0, math.radians(96))
r2, _ = ph.model("wooden_bucket_01")
r2.location = (1.25, 1.05, 0.0); r2.rotation_euler = (0, 0, 0.7)
# a sea chest at the foot of the berth
chest_m = mat_from("wood_table_worn", 1.5, wet=0.4, tint=(0.6, 0.45, 0.32), name="chest")
ship.box("chest", (1.15, 0.95, 0.24), (0.75, 0.5, 0.48), chest_m, rot=(0, 0, 0.12), bevel=0.012)
ship.box("chest_lid", (1.15, 0.95, 0.495), (0.78, 0.53, 0.04), chest_m, rot=(0, 0, 0.12), bevel=0.01)
# standing water on the floor (it has come in through the skylight and the companion)
water = bpy.data.materials.new("puddle"); water.use_nodes = True
wp = water.node_tree.nodes["Principled BSDF"]; wp.inputs['Roughness'].default_value = 0.02
wp.inputs['Base Color'].default_value = (0.02, 0.018, 0.015, 1); wp.inputs['Transmission Weight'].default_value = 0.6
tcn = water.node_tree.nodes.new("ShaderNodeTexNoise"); tcn.inputs['Scale'].default_value = 1.8
mr = water.node_tree.nodes.new("ShaderNodeMapRange"); mr.inputs['From Min'].default_value = 0.47; mr.inputs['From Max'].default_value = 0.5
water.node_tree.links.new(tcn.outputs['Fac'], mr.inputs['Value'])
water.node_tree.links.new(mr.outputs[0], wp.inputs['Alpha'])
pd = ship.box("puddles", (0, 0, 0.002), (2 * RX - 0.02, 2 * RY - 0.02, 0.003), water)

# lantern (Poly Haven) — positioned after Deveau's hand is posed
lan, lms = ph.model("wooden_lantern_01")

# ----------------------------------------------------------------------------- Deveau
dv = D.Deveau(wet=0.55)
h = dv.h
ANG = math.radians(223)                          # he faces the berth, turned toward the hollow at its head end
POS = Vector((0.22, 0.3, 0.0))
M = Matrix.Translation(POS) @ Matrix.Rotation(ANG, 4, 'Z')
P.cabin(dv, M, (0.48, BY0 - 0.02, BOARD + 0.045), (-0.12, 0.5, 1.3), lantern_side="L")
bpy.context.view_layer.update()
grip_local = P.palm_point(h, "L")
look = Vector((CHILD["cx"] - 0.05, CHILD["cy"], TOP))
dv.finish(look_at=look, place=M, density=float(os.environ.get("HAIR", "1.0")))
grip_w = M @ grip_local
# the lantern hangs straight down from his fist by its bail (bail top is 0.519 above the lantern's base)
lan.location = grip_w - Vector((0, 0, 0.505)); lan.rotation_euler = (0, 0, 0.4)
bpy.context.view_layer.update()
flame_c = lan.location + Vector((0, 0, 0.2))
fl = bpy.data.lights.new("lantern", 'POINT'); fl.energy = float(os.environ.get('LANTERN', '55')); fl.color = (1.0, 0.56, 0.24); fl.shadow_soft_size = 0.018
flo = bpy.data.objects.new("lantern_light", fl); sc.collection.objects.link(flo); flo.location = flame_c
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.012, location=flame_c + Vector((0, 0, 0.01)))
fm = bpy.context.active_object; fm.name = "flame"; fm.scale = (0.7, 0.7, 1.9)
em = bpy.data.materials.new("flame"); em.use_nodes = True; N = em.node_tree.nodes
N.remove(N["Principled BSDF"]); e = N.new("ShaderNodeEmission"); e.inputs['Color'].default_value = (1.0, 0.62, 0.25, 1)
e.inputs['Strength'].default_value = 60; em.node_tree.links.new(e.outputs[0], N["Material Output"].inputs['Surface'])
fm.data.materials.append(em); fm.visible_shadow = False
# lantern glass: warm smoked glass that lets light through
lglass = bpy.data.materials.new("lantern_glass"); lglass.use_nodes = True
lg = lglass.node_tree.nodes["Principled BSDF"]; lg.inputs['Transmission Weight'].default_value = 1.0
lg.inputs['Roughness'].default_value = 0.06; lg.inputs['Base Color'].default_value = (1.0, 0.93, 0.8, 1); lg.inputs['IOR'].default_value = 1.2
# shadow rays pass straight through the thin panes (no caustics needed for the lantern to light the cabin)
_N = lglass.node_tree.nodes; _L = lglass.node_tree.links
_lp = _N.new("ShaderNodeLightPath"); _tr = _N.new("ShaderNodeBsdfTransparent"); _tr.inputs['Color'].default_value = (1.0, 0.92, 0.78, 1)
_mx = _N.new("ShaderNodeMixShader"); _L.new(_lp.outputs['Is Shadow Ray'], _mx.inputs[0])
_L.new(lg.outputs[0], _mx.inputs[1]); _L.new(_tr.outputs[0], _mx.inputs[2])
_L.new(_mx.outputs[0], _N["Material Output"].inputs['Surface'])
for o in lms:
    for sl in o.material_slots:
        if sl.material and "glass" in sl.material.name:
            sl.material = lglass

# warm bounce off the lantern's glass and the wet bedding up into his face (motivated by the lantern)
head_w0 = M @ Vector((0, -0.1, 1.64))
ff = bpy.data.lights.new("lantern_bounce", 'AREA'); ff.size = 0.35; ff.energy = float(os.environ.get("BOUNCE", "4")); ff.color = (1.0, 0.62, 0.36)
ffo = bpy.data.objects.new("lantern_bounce", ff); sc.collection.objects.link(ffo)
ffo.location = flame_c.lerp(head_w0, 0.35) + Vector((0, 0, -0.15))
ffo.rotation_euler = (head_w0 - ffo.location).to_track_quat('-Z', 'Y').to_euler(); ffo.visible_camera = False
ffo.visible_glossy = False
# soot: years of lamp smoke darken the deckhead and planking above where the lantern hangs
for _m in (beams_m, walls):
    _N = _m.node_tree.nodes; _L = _m.node_tree.links; _p = _N["Principled BSDF"]
    _g = _N.new("ShaderNodeNewGeometry"); _d = _N.new("ShaderNodeVectorMath"); _d.operation = 'DISTANCE'
    _d.inputs[1].default_value = (flame_c.x, flame_c.y, RZ); _L.new(_g.outputs['Position'], _d.inputs[0])
    _mr = _N.new("ShaderNodeMapRange"); _mr.inputs['From Min'].default_value = 0.25; _mr.inputs['From Max'].default_value = 1.1
    _mr.inputs['To Min'].default_value = 0.85; _mr.inputs['To Max'].default_value = 0.0; _L.new(_d.outputs['Value'], _mr.inputs['Value'])
    _src = _p.inputs['Base Color'].links[0].from_socket if _p.inputs['Base Color'].links else None
    if _src is not None:
        _mx = _N.new("ShaderNodeMix"); _mx.data_type = 'RGBA'; _mx.blend_type = 'MULTIPLY'; _mx.inputs[7].default_value = (0.08, 0.07, 0.06, 1)
        _L.new(_mr.outputs[0], _mx.inputs['Factor']); _L.new(_src, _mx.inputs[6]); _L.new(_mx.outputs[2], _p.inputs['Base Color'])
# ----------------------------------------------------------------------------- light and air
sk = bpy.data.lights.new("skylight", 'AREA'); sk.shape = 'RECTANGLE'; sk.size = sw * 0.95; sk.size_y = sh * 0.95
sk.energy = float(os.environ.get('SKYL', '420')); sk.color = (0.72, 0.8, 0.92)
try:
    sk.spread = math.radians(40)
except Exception:
    pass
sko = bpy.data.objects.new("skylight", sk); sc.collection.objects.link(sko); sko.location = (sx, sy, RZ + 0.36)
sko.rotation_euler = (math.radians(-14), math.radians(8), 0)
# bounce off the wet floor / weak cool ambient so the shadows are not dead black
w = bpy.data.worlds.new("W"); sc.world = w; w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (0.45, 0.5, 0.58, 1); w.node_tree.nodes["Background"].inputs[1].default_value = 0.02
fill = bpy.data.lights.new("fill", 'AREA'); fill.size = 1.2; fill.energy = 2.5; fill.color = (0.65, 0.72, 0.85)
fo = bpy.data.objects.new("fill", fill); sc.collection.objects.link(fo); fo.location = (-1.2, -1.0, 1.4)
fo.rotation_euler = (Vector((0.2, 0.3, 1.2)) - fo.location).to_track_quat('-Z', 'Y').to_euler()
fo.visible_camera = False; fo.visible_glossy = False
# cabin air: damp, a little haze so the lantern and the skylight read as light in the air
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, RZ / 2 + 0.2))
air = bpy.context.active_object; air.name = "cabin_air"; air.scale = (2 * RX - 0.02, 2 * RY - 0.02, RZ + 0.38)
am = bpy.data.materials.new("air"); am.use_nodes = True; N = am.node_tree.nodes; N.remove(N["Principled BSDF"])
vs = N.new("ShaderNodeVolumeScatter"); vs.inputs['Density'].default_value = float(os.environ.get("FOG", "0.045")); vs.inputs['Anisotropy'].default_value = 0.35
am.node_tree.links.new(vs.outputs[0], N["Material Output"].inputs['Volume']); air.data.materials.append(am)
air.visible_shadow = False

# ----------------------------------------------------------------------------- camera
head_w = M @ Vector((0, -0.05, 1.66))
# medium shot: waist-up, the lantern at frame left side-lighting him, the far side of his face in shadow;
# the hollow in the berth runs out of the bottom-left corner of the frame
cam_loc = Vector((-1.56, 0.5, 1.78))                # high at the head of the berth, looking along the bedding to him
aim = (M @ Vector((0.0, -0.05, 1.55))).lerp(Vector((CHILD["cx"], CHILD["cy"], TOP)), 0.33)
cam = C.camera(cam_loc, aim, lens=26, fstop=3.2, focus=(head_w - cam_loc).length, roll=-1.0)
if POSE_TEST:
    air.hide_render = True; sc.cycles.samples = 24
    for o in bpy.data.objects:
        if o.name.startswith(("wall_y-1", "wall_x-1")):
            o.hide_render = True
    sc.render.filepath = OUT.replace(".png", "_cam.png"); bpy.ops.render.render(write_still=True)
    C.camera(Vector((0.4, -3.2, 1.3)), Vector((0.0, 0.2, 1.1)), lens=28)
    sc.render.filepath = OUT.replace(".png", "_side.png"); bpy.ops.render.render(write_still=True)
    C.camera(Vector((-0.6, 0.6, 3.6)), Vector((-0.6, 1.0, 0.0)), lens=24)
    for o in bpy.data.objects:
        if o.name.startswith(("ceil", "beam", "berth_shelf", "berth_valance", "well", "glazing", "skylight_glass")):
            o.hide_render = True
    sc.render.filepath = OUT.replace(".png", "_top.png"); bpy.ops.render.render(write_still=True)
    hw = M @ Vector((0, -0.12, 1.66))
    C.camera(hw + Vector((-0.75, -0.45, 0.05)), hw, lens=50)
    sc.render.filepath = OUT.replace(".png", "_face.png"); bpy.ops.render.render(write_still=True)
    sys.exit(0)
C.finish(OUT, cine={"exposure": 0.1, "sat": 0.95})
print("RENDERED", OUT)
