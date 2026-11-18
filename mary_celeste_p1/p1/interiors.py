"""Below-deck sets for Part 1 (room coordinates: floor at z = 0, x fore-aft, y athwartships).

  captain_cabin()   the shared look frame (b) rebuilt as a reusable set: panelled cabin, skylight, wet berth with
                    the child-sized impression, sea chest, sword, puddles. Returns anchors (berth, child, door).
  mate_cabin()      smaller cabin: berth, a table with the logbook and the slate, a lamp bracket.
  galley()          the galley in the deckhouse: raised door sill (the "lip"), water slopping over the floor up to it,
                    the iron stove knocked off its chocks, pots on the floor.
Materials and the bed geometry follow mary_celeste_3d/scenes/sc_b_cabin.py (shared look), unchanged in spirit."""
import math, os
import numpy as np
import bpy
from mathutils import Vector, Matrix, noise
import env as E
import ship, ph


def wood(aid, scale, wet=0.0, tint=None, name=None):
    return ship.wood(aid, scale, wet=wet, tint=tint, name=name)


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
        sm = N.new("ShaderNodeMix"); sm.data_type = 'RGBA'; sm.inputs[7].default_value = (0.12, 0.05, 0.04, 1)
        Lk.new(st.outputs[0], sm.inputs['Factor']); Lk.new(base, sm.inputs[6]); base = sm.outputs[2]
    wn = N.new("ShaderNodeTexNoise"); wn.inputs['Scale'].default_value = 2.2; wn.inputs['Detail'].default_value = 6
    Lk.new(tc.outputs['Object'], wn.inputs['Vector'])
    wm = N.new("ShaderNodeMapRange"); wm.inputs['From Min'].default_value = 0.42 - 0.2 * wet; wm.inputs['From Max'].default_value = 0.5 - 0.2 * wet
    Lk.new(wn.outputs['Fac'], wm.inputs['Value'])
    dk = N.new("ShaderNodeMix"); dk.data_type = 'RGBA'; dk.blend_type = 'MULTIPLY'; dk.inputs[7].default_value = (0.52, 0.5, 0.47, 1)
    Lk.new(wm.outputs[0], dk.inputs['Factor']); Lk.new(base, dk.inputs[6])
    Lk.new(dk.outputs[2], p.inputs['Base Color'])
    rr = N.new("ShaderNodeMapRange"); rr.inputs['To Min'].default_value = 0.85; rr.inputs['To Max'].default_value = 0.3
    Lk.new(wm.outputs[0], rr.inputs['Value']); Lk.new(rr.outputs[0], p.inputs['Roughness'])
    p.inputs['Sheen Weight'].default_value = sheen; p.inputs['Specular IOR Level'].default_value = 0.55
    wv2 = N.new("ShaderNodeTexWave"); wv2.inputs['Scale'].default_value = 300; Lk.new(tc.outputs['Object'], wv2.inputs['Vector'])
    b = N.new("ShaderNodeBump"); b.inputs['Strength'].default_value = 0.12; Lk.new(wv2.outputs['Fac'], b.inputs['Height'])
    Lk.new(b.outputs['Normal'], p.inputs['Normal'])
    return m


def puddle_mat(name="puddle", cover=0.5, depth_col=(0.03, 0.022, 0.014)):
    m = bpy.data.materials.new(name); m.use_nodes = True
    N = m.node_tree.nodes; Lk = m.node_tree.links; p = N["Principled BSDF"]
    p.inputs['Roughness'].default_value = 0.03; p.inputs['Base Color'].default_value = (*depth_col, 1)
    p.inputs['Transmission Weight'].default_value = 0.6
    nz = N.new("ShaderNodeTexNoise"); nz.inputs['Scale'].default_value = 1.8
    mr = N.new("ShaderNodeMapRange"); mr.inputs['From Min'].default_value = 0.5 - cover * 0.06; mr.inputs['From Max'].default_value = 0.53 - cover * 0.06
    Lk.new(nz.outputs['Fac'], mr.inputs['Value']); Lk.new(mr.outputs[0], p.inputs['Alpha'])
    return m


def water_body_mat(name="bilgewater"):
    """Dirty sea water standing in a compartment: dark, slightly murky green-brown, glossy surface."""
    m = bpy.data.materials.new(name); m.use_nodes = True
    N = m.node_tree.nodes; Lk = m.node_tree.links; p = N["Principled BSDF"]
    p.inputs['Base Color'].default_value = (0.05, 0.06, 0.045, 1); p.inputs['Roughness'].default_value = 0.02
    p.inputs['Transmission Weight'].default_value = 0.85; p.inputs['IOR'].default_value = 1.333
    nz = N.new("ShaderNodeTexNoise"); nz.inputs['Scale'].default_value = 6; nz.inputs['Detail'].default_value = 6
    tc = N.new("ShaderNodeTexCoord"); Lk.new(tc.outputs['Object'], nz.inputs['Vector'])
    bm = N.new("ShaderNodeBump"); bm.inputs['Strength'].default_value = 0.15; bm.inputs['Distance'].default_value = 0.01
    Lk.new(nz.outputs['Fac'], bm.inputs['Height']); Lk.new(bm.outputs['Normal'], p.inputs['Normal'])
    out = N["Material Output"]
    vol = N.new("ShaderNodeVolumeAbsorption"); vol.inputs['Color'].default_value = (0.45, 0.5, 0.35, 1); vol.inputs['Density'].default_value = 6
    Lk.new(vol.outputs[0], out.inputs['Volume'])
    return m


def _room(RX, RY, RZ, walls, floor, beams_m, sky=None, door=None):
    """Box room with panelled walls, a planked deckhead with beams and an optional skylight opening.
    door = (wall 'x+'|'x-'|'y+'|'y-', centre along the wall, width, height): an opening in that wall."""
    ship.box("floor", (0, 0, -0.03), (2 * RX, 2 * RY, 0.06), floor)
    def wall(tag, c, size, along, lo, hi):
        if door and door[0] == tag:
            dc, dw, dh = door[1], door[2], door[3]
            a0, a1 = dc - dw / 2, dc + dw / 2
            pieces = [(lo, a0, 0, RZ + 0.1), (a1, hi, 0, RZ + 0.1), (a0, a1, dh, RZ + 0.1)]
            for k, (u0, u1, z0, z1) in enumerate(pieces):
                if u1 - u0 < 0.01:
                    continue
                cc = list(c); cc[along] = (u0 + u1) / 2; cc[2] = (z0 + z1) / 2
                ss = list(size); ss[along] = u1 - u0; ss[2] = z1 - z0
                ship.box(f"wall_{tag}{k}", cc, ss, walls)
        else:
            ship.box(f"wall_{tag}", c, size, walls)
    wall("y+", (0, RY + 0.03, RZ / 2), (2 * RX, 0.06, RZ + 0.1), 0, -RX, RX)
    wall("y-", (0, -RY - 0.03, RZ / 2), (2 * RX, 0.06, RZ + 0.1), 0, -RX, RX)
    wall("x+", (RX + 0.03, 0, RZ / 2), (0.06, 2 * RY, RZ + 0.1), 1, -RY, RY)
    wall("x-", (-RX - 0.03, 0, RZ / 2), (0.06, 2 * RY, RZ + 0.1), 1, -RY, RY)
    if sky:
        sx, sy, sw, sh = sky
        ship.box("ceil_a", ((sx - sw / 2 - RX) / 2, 0, RZ + 0.03), (sx - sw / 2 + RX, 2 * RY, 0.06), beams_m)
        ship.box("ceil_b", ((sx + sw / 2 + RX) / 2, 0, RZ + 0.03), (RX - sx - sw / 2, 2 * RY, 0.06), beams_m)
        ship.box("ceil_c", (sx, (sy - sh / 2 - RY) / 2, RZ + 0.03), (sw, sy - sh / 2 + RY, 0.06), beams_m)
        ship.box("ceil_d", (sx, (sy + sh / 2 + RY) / 2, RZ + 0.03), (sw, RY - sy - sh / 2, 0.06), beams_m)
        for sg in (1, -1):
            ship.box("well", (sx + sg * (sw / 2 + 0.02), sy, RZ + 0.2), (0.04, sh + 0.08, 0.4), beams_m)
            ship.box("well", (sx, sy + sg * (sh / 2 + 0.02), RZ + 0.2), (sw + 0.08, 0.04, 0.4), beams_m)
        for k in range(1, 3):
            ship.box("glazing_bar", (sx - sw / 2 + k * sw / 3, sy, RZ + 0.38), (0.025, sh, 0.03), beams_m)
        glass = E.principled("skyglass", (0.8, 0.85, 0.8), rough=0.25, **{"Transmission Weight": 1.0})
        g = ship.box("skylight_glass", (sx, sy, RZ + 0.39), (sw, sh, 0.008), glass); g.visible_shadow = False
    else:
        ship.box("ceil", (0, 0, RZ + 0.03), (2 * RX, 2 * RY, 0.06), beams_m)
    x = -RX + 0.25
    while x < RX:
        if not sky or abs(x - sky[0]) > sky[2] / 2 + 0.05:
            ship.box("beam", (x, 0, RZ - 0.07), (0.11, 2 * RY, 0.14), beams_m, bevel=0.01)
        x += 0.52


def _air(RX, RY, RZ, density):
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, RZ / 2 + 0.2))
    air = bpy.context.active_object; air.name = "cabin_air"; air.scale = (2 * RX - 0.02, 2 * RY - 0.02, RZ + 0.38)
    am = bpy.data.materials.new("air"); am.use_nodes = True; N = am.node_tree.nodes; N.remove(N["Principled BSDF"])
    vs = N.new("ShaderNodeVolumeScatter"); vs.inputs['Density'].default_value = density; vs.inputs['Anisotropy'].default_value = 0.35
    am.node_tree.links.new(vs.outputs[0], N["Material Output"].inputs['Volume']); air.data.materials.append(am)
    air.visible_shadow = False
    return air


def lantern(loc, energy=55.0, hang=True, rot=0.4):
    """Poly Haven wooden lantern with a real flame light inside; loc = the bail top (where a hand or hook holds it)."""
    lan, lms = ph.model("wooden_lantern_01")
    lan.location = Vector(loc) - Vector((0, 0, 0.505)) if hang else Vector(loc); lan.rotation_euler = (0, 0, rot)
    bpy.context.view_layer.update()
    flame_c = lan.location + Vector((0, 0, 0.2))
    fl = E.point("lantern_light", flame_c, energy, (1.0, 0.56, 0.24), radius=0.018)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.012, location=flame_c + Vector((0, 0, 0.01)))
    fm = bpy.context.active_object; fm.name = "flame"; fm.scale = (0.7, 0.7, 1.9)
    fm.data.materials.append(E.emission_mat("flame", (1.0, 0.62, 0.25), 60)); fm.visible_shadow = False
    lg = bpy.data.materials.new("lantern_glass"); lg.use_nodes = True
    N = lg.node_tree.nodes; Lk = lg.node_tree.links; p = N["Principled BSDF"]
    p.inputs['Transmission Weight'].default_value = 1.0; p.inputs['Roughness'].default_value = 0.06
    p.inputs['Base Color'].default_value = (1.0, 0.93, 0.8, 1); p.inputs['IOR'].default_value = 1.2
    lp = N.new("ShaderNodeLightPath"); tr = N.new("ShaderNodeBsdfTransparent"); tr.inputs['Color'].default_value = (1.0, 0.92, 0.78, 1)
    mx = N.new("ShaderNodeMixShader"); Lk.new(lp.outputs['Is Shadow Ray'], mx.inputs[0])
    Lk.new(p.outputs[0], mx.inputs[1]); Lk.new(tr.outputs[0], mx.inputs[2]); Lk.new(mx.outputs[0], N["Material Output"].inputs['Surface'])
    for o in lms:
        for sl in o.material_slots:
            if sl.material and "glass" in sl.material.name:
                sl.material = lg
    return dict(root=lan, light=fl, flame=fm, center=flame_c)


# ============================================================================ captain's cabin
CAB = dict(RX=1.75, RY=1.45, RZ=2.02, BX0=-1.68, BX1=0.42, BY0=0.62, TOP=0.60, BOARD=0.80, WET=0.85,
           SKY=(0.05, -0.55, 0.62, 0.5), DOOR=("x+", -0.55, 0.72, 1.82))
CHILD = dict(cx=-0.66, cy=(CAB["BY0"] + CAB["RY"]) / 2 - 0.03)


def impression(x, y):
    cx, cy = CHILD["cx"], CHILD["cy"]
    u = (x - cx); v = (y - cy)
    parts = [(-0.42, 0.02, 0.085, 0.075, 1.0), (-0.2, 0.0, 0.16, 0.11, 0.85), (0.02, -0.01, 0.13, 0.1, 0.8),
             (0.24, 0.04, 0.16, 0.07, 0.55), (0.42, 0.07, 0.11, 0.05, 0.35)]
    d = 0.0
    for px, py, rx, ry, w in parts:
        r2 = ((u - px) / rx) ** 2 + ((v - py) / ry) ** 2
        d = max(d, w * math.exp(-1.6 * r2 ** 1.4))
    return d


def _berth(BX0, BX1, BY0, RY, TOP, BOARD, berth_m, beams_m, imp=None, wet=0.85, blanket_heap=True, name="b"):
    ship.box("berth_board", ((BX0 + BX1) / 2, BY0 - 0.02, BOARD / 2), (BX1 - BX0, 0.05, BOARD), berth_m, bevel=0.006)
    ship.box("berth_board_cap", ((BX0 + BX1) / 2, BY0 - 0.02, BOARD + 0.015), (BX1 - BX0 + 0.04, 0.08, 0.03), berth_m, bevel=0.008)
    ship.box("berth_end", (BX1 + 0.025, (BY0 + RY) / 2, BOARD / 2 + 0.1), (0.05, RY - BY0 + 0.04, BOARD + 0.2), berth_m, bevel=0.006)
    ship.box("berth_base", ((BX0 + BX1) / 2, (BY0 + RY) / 2, TOP - 0.2), (BX1 - BX0, RY - BY0, 0.04), berth_m)
    for k in range(3):
        xx = BX0 + 0.38 + k * 0.68
        if xx > BX1 - 0.3:
            break
        ship.box("drawer", (xx, BY0 - 0.05, 0.22), (0.6, 0.02, 0.28), berth_m, bevel=0.004)
        ship.cyl("knob", (xx, BY0 - 0.06, 0.24), (xx, BY0 - 0.085, 0.24), 0.014, mat=beams_m, verts=12)
    ship.box("berth_shelf", ((BX0 + BX1) / 2, RY - 0.18, 1.62), (BX1 - BX0, 0.36, 0.03), berth_m)
    ship.box("berth_valance", ((BX0 + BX1) / 2, RY - 0.36, 1.56), (BX1 - BX0, 0.025, 0.14), berth_m)
    imp = imp or (lambda x, y: 0.0)
    nx, ny = 150, 60
    x0, x1, y0, y1 = BX0 + 0.03, BX1 - 0.03, BY0 + 0.03, RY - 0.03
    V = []; F = []; UV = []
    for j in range(ny + 1):
        for i in range(nx + 1):
            x = x0 + (x1 - x0) * i / nx; y = y0 + (y1 - y0) * j / ny
            edge = min(i, nx - i, j, ny - j) / 4.0
            z = TOP - 0.085 * imp(x, y) - 0.03 * math.exp(-edge) + 0.004 * noise.noise(Vector((x * 6, y * 6, 0.5)))
            V.append((x, y, z)); UV.append(((x - x0) * 2, (y - y0) * 2))
    for j in range(ny):
        for i in range(nx):
            a = j * (nx + 1) + i
            F.append([a, a + 1, a + nx + 2, a + nx + 1])
    matt = ship.mesh_obj(name + "_mattress", V, F, wet_cloth_mat("ticking", (0.62, 0.55, 0.44), wet, stripes=True))
    uvl = matt.data.uv_layers.new(name="UVMap")
    for l in matt.data.loops:
        uvl.data[l.index].uv = UV[l.vertex_index]
    so = matt.modifiers.new("Thick", "SOLIDIFY"); so.thickness = 0.16; so.offset = -1
    sheet_V = []
    for (x, y, z) in V:
        d = imp(x, y)
        cr = 0.006 * noise.noise(Vector((x * 9, y * 14, 2.0))) * (0.3 + d) + 0.006 * math.sin((y - CHILD["cy"]) * 55 + x * 11) * min(1.0, 3 * d * (1 - d))
        sheet_V.append((x, y, z + 0.006 + cr))
    keepF = [f for f in F if V[f[0]][0] < BX1 - 0.55]
    sheet_m = wet_cloth_mat("sheet", (0.72, 0.66, 0.56), wet + 0.1, sheen=0.3)
    sheet = ship.mesh_obj(name + "_sheet", sheet_V, keepF, sheet_m)
    ca = sheet.data.color_attributes.new("imp", 'FLOAT_COLOR', 'POINT')
    for i, (x, y, z) in enumerate(sheet_V):
        d = min(1.0, imp(x, y) * 1.25); ca.data[i].color = (d, d, d, 1)
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
    if blanket_heap:
        nx, ny = 70, 46; bV = []; bF = []
        for j in range(ny + 1):
            for i in range(nx + 1):
                u = i / nx; v = j / ny
                x = BX1 - 0.62 + 0.6 * u
                y = BY0 - 0.12 + (RY - BY0 + 0.1) * v
                hh = 0.05 + 0.05 * math.sin(u * math.pi * 3.2 + v * 1.5) ** 2 + 0.035 * noise.noise(Vector((u * 5, v * 5, 3.0)))
                z = TOP + 0.01 + hh
                if y < BY0 + 0.02:
                    over = (BY0 + 0.02 - y)
                    z = BOARD + 0.03 - over * 5.0 * (0.6 + 0.4 * u)
                    y = BY0 - 0.06 - 0.02 * math.sin(u * 9)
                bV.append((x, y, z))
        for j in range(ny):
            for i in range(nx):
                a = j * (nx + 1) + i
                bF.append([a, a + 1, a + nx + 2, a + nx + 1])
        bl = ship.mesh_obj(name + "_blanket", bV, bF, wet_cloth_mat("blanket", (0.20, 0.07, 0.05), wet, sheen=0.7))
        bl.modifiers.new("Thick", "SOLIDIFY").thickness = 0.008
        s = bl.modifiers.new("Sub", "SUBSURF"); s.levels = 1; s.render_levels = 2
    bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, radius=1, location=(BX0 + 0.24, (BY0 + RY) / 2, TOP + 0.06))
    pil = bpy.context.active_object; pil.name = name + "_pillow"; pil.scale = (0.2, 0.3, 0.07)
    bpy.ops.object.transform_apply(scale=True)
    for v in pil.data.vertices:
        w = pil.matrix_world @ v.co
        dd = math.exp(-(((w.x - (BX0 + 0.3)) / 0.08) ** 2 + ((w.y - (CHILD["cy"] + 0.02)) / 0.08) ** 2)) if imp(w.x + 0.1, w.y) > 0 else 0
        if v.co.z > 0:
            v.co.z -= 0.035 * dd
        v.co.z = max(v.co.z, -0.055)
    bpy.ops.object.shade_smooth()
    pil.data.materials.append(wet_cloth_mat("pillowcase", (0.7, 0.64, 0.54), wet))
    return matt, sheet


def captain_cabin(fog=0.022, skylight=450.0):
    c = CAB; RX, RY, RZ = c["RX"], c["RY"], c["RZ"]
    walls = wood("dark_wooden_planks", 1.4, wet=0.15, tint=(0.85, 0.6, 0.42), name="walls")
    floor = wood("weathered_planks", 0.9, wet=c["WET"], tint=(0.8, 0.66, 0.52), name="floor")
    beams_m = ship.paint("beams", (0.42, 0.33, 0.22), rough=0.5, grime=0.6, chips=0.3, scale=6)
    berth_m = wood("brown_planks_05", 1.6, wet=0.3, tint=(0.75, 0.5, 0.34), name="berthwood")
    _room(RX, RY, RZ, walls, floor, beams_m, sky=c["SKY"], door=c["DOOR"])
    for sg in (1, -1):
        ship.box(f"chair_rail{sg}", (0, sg * (RY - 0.015), 0.95), (2 * RX, 0.035, 0.06), berth_m, bevel=0.005)
    for k in range(7):
        ship.box("stile", (-RX + 0.3 + k * 0.52, -(RY - 0.012), 0.48), (0.08, 0.03, 0.9), berth_m)
    _berth(c["BX0"], c["BX1"], c["BY0"], RY, c["TOP"], c["BOARD"], berth_m, beams_m, imp=impression, wet=c["WET"], name="cap")
    r, _ = ph.model("wooden_handle_saber")
    r.location = (c["BX0"] + 0.9, c["BY0"] + 0.08, 0.035); r.rotation_euler = (math.radians(90), 0, math.radians(96))
    r2, _ = ph.model("wooden_bucket_01"); r2.location = (1.25, 1.05, 0.0); r2.rotation_euler = (0, 0, 0.7)
    chest_m = wood("wood_table_worn", 1.5, wet=0.4, tint=(0.62, 0.42, 0.28), name="chest")
    ship.box("chest", (1.15, 0.95, 0.24), (0.75, 0.5, 0.48), chest_m, rot=(0, 0, 0.12), bevel=0.012)
    ship.box("chest_lid", (1.15, 0.95, 0.495), (0.78, 0.53, 0.04), chest_m, rot=(0, 0, 0.12), bevel=0.01)
    ship.box("puddles", (0, 0, 0.002), (2 * RX - 0.02, 2 * RY - 0.02, 0.003), puddle_mat())
    _daylight(c["SKY"], RZ, skylight)
    if float(os.environ.get("NOFOG", "0")) == 0:
        _air(RX, RY, RZ, fog)
    return dict(child=Vector((CHILD["cx"], CHILD["cy"], c["TOP"])), board=Vector((0.0, c["BY0"] - 0.02, c["BOARD"] + 0.045)),
                door=Vector((RX, c["DOOR"][1], 0)))


def _daylight(skyrect, RZ, energy):
    sx, sy, sw, sh = skyrect
    sk = bpy.data.lights.new("skylight", 'AREA'); sk.shape = 'RECTANGLE'; sk.size = sw * 0.95; sk.size_y = sh * 0.95
    sk.energy = energy; sk.color = (0.8, 0.87, 1.0)
    try:
        sk.spread = math.radians(40)
    except Exception:
        pass
    sko = bpy.data.objects.new("skylight", sk); bpy.context.scene.collection.objects.link(sko); sko.location = (sx, sy, RZ + 0.36)
    sko.visible_volume_scatter = float(os.environ.get("SHAFTS", "0")) > 0      # no blown light shafts near the lens
    sko.rotation_euler = (math.radians(-14), math.radians(8), 0)
    w = bpy.data.worlds.new("W"); bpy.context.scene.world = w; w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[0].default_value = (0.5, 0.42, 0.34, 1); w.node_tree.nodes["Background"].inputs[1].default_value = 0.03


# ============================================================================ mate's cabin
MATE = dict(RX=1.35, RY=1.2, RZ=1.98, BX0=-1.28, BX1=0.62, BY0=0.5, TOP=0.62, BOARD=0.82, TABLE=(0.35, -0.55, 0.74),
            SKY=(-0.45, -0.5, 0.5, 0.42), DOOR=("x+", 0.55, 0.68, 1.8))


def mate_cabin(fog=0.02, skylight=320.0):
    c = MATE; RX, RY, RZ = c["RX"], c["RY"], c["RZ"]
    walls = wood("dark_wooden_planks", 1.4, wet=0.1, tint=(0.9, 0.64, 0.46), name="walls")
    floor = wood("weathered_planks", 0.9, wet=0.5, tint=(0.8, 0.66, 0.52), name="floor")
    beams_m = ship.paint("beams", (0.42, 0.33, 0.22), rough=0.5, grime=0.6, chips=0.3, scale=6)
    berth_m = wood("brown_planks_05", 1.6, wet=0.2, tint=(0.75, 0.5, 0.34), name="berthwood")
    _room(RX, RY, RZ, walls, floor, beams_m, sky=c["SKY"], door=c["DOOR"])
    ship.box("chair_rail", (0, -(RY - 0.015), 0.95), (2 * RX, 0.035, 0.06), berth_m, bevel=0.005)
    _berth(c["BX0"], c["BX1"], c["BY0"], RY, c["TOP"], c["BOARD"], berth_m, beams_m, wet=0.35, blanket_heap=False, name="mate")
    # table bolted to the floor (a ship's table has a fiddle rail round its edge)
    tx, ty, tz = c["TABLE"]
    top_m = wood("wood_table_worn", 1.2, wet=0.1, tint=(0.7, 0.45, 0.3), name="tabletop")
    ship.box("table_top", (tx, ty, tz), (1.0, 0.7, 0.04), top_m, bevel=0.006)
    for sx_ in (-1, 1):
        ship.box("fiddle", (tx, ty + sx_ * 0.34, tz + 0.035), (1.0, 0.02, 0.03), top_m)
        ship.box("fiddle", (tx + sx_ * 0.49, ty, tz + 0.035), (0.02, 0.7, 0.03), top_m)
    ship.cyl("table_post", (tx, ty, 0), (tx, ty, tz - 0.02), 0.06, mat=top_m, verts=16)
    ship.box("table_foot", (tx, ty, 0.02), (0.5, 0.4, 0.04), top_m, bevel=0.01)
    st, _ = ph.model("wooden_stool_01"); st.location = (tx + 0.1, ty + 0.62, 0); st.rotation_euler = (0, 0, 0.3)
    book = logbook((tx - 0.12, ty + 0.02, tz + 0.02), rot=0.12)
    sl = slate((tx + 0.3, ty - 0.08, tz + 0.02), rot=-0.25)
    lamp = lantern((tx - 0.1, ty - 0.55, RZ - 0.15), energy=30.0)
    ship.cyl("lamp_hook", (tx - 0.1, ty - 0.55, RZ - 0.15), (tx - 0.1, ty - 0.55, RZ), 0.006, mat=ship.iron("hookiron"), verts=8)
    ship.box("puddles", (0, 0, 0.002), (2 * RX - 0.02, 2 * RY - 0.02, 0.003), puddle_mat(cover=0.2))
    _daylight(c["SKY"], RZ, skylight)
    if float(os.environ.get("NOFOG", "0")) == 0:
        _air(RX, RY, RZ, fog)
    return dict(table=Vector(c["TABLE"]), book=book, slate=sl, lamp=lamp, door=Vector((RX, c["DOOR"][1], 0)))


# ---------------------------------------------------------------------------- written props (real 3D objects)
def _page_texture(path, kind):
    """The logbook's last page / the slate's chalk lines are drawn by tools/make_textures.py (system Python + PIL;
    Blender's Python has no PIL). Run on demand."""
    if not os.path.exists(path):
        import subprocess
        subprocess.run(["python3", os.path.join(E.P1, "tools", "make_textures.py"), kind, path], check=True)
    return path


def _img_mat(name, path, rough=0.8):
    m = bpy.data.materials.new(name); m.use_nodes = True; N = m.node_tree.nodes; Lk = m.node_tree.links
    t = N.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(path, check_existing=True)
    Lk.new(t.outputs['Color'], N["Principled BSDF"].inputs['Base Color'])
    N["Principled BSDF"].inputs['Roughness'].default_value = rough
    return m


def _uv_quad(o, flip=False):
    uvl = o.data.uv_layers.new(name="UVMap")
    for l in o.data.loops:
        v = o.data.vertices[l.vertex_index].co
        uvl.data[l.index].uv = (0, 0)
    return uvl


def _textured_plane(name, center, w, h, mat, rot_z=0.0, z_off=0.0):
    V = [(-w / 2, -h / 2, 0), (w / 2, -h / 2, 0), (w / 2, h / 2, 0), (-w / 2, h / 2, 0)]
    o = ship.mesh_obj(name, V, [[0, 1, 2, 3]], mat, smooth=False)
    uvl = o.data.uv_layers.new(name="UVMap")
    for l, uv in zip(o.data.loops, [(0, 0), (1, 0), (1, 1), (0, 1)]):
        uvl.data[l.index].uv = uv
    o.location = Vector(center) + Vector((0, 0, z_off)); o.rotation_euler = (0, 0, rot_z)
    return o


def logbook(c, rot=0.0):
    """An open ledger: leather boards, a block of pages either side of the spine (gently curved), the written page."""
    tex = _page_texture(os.path.join(E.P1, "out", "tex", "logpage.png"), "log")
    lw, lh = 0.46, 0.3                                     # open spread
    root = bpy.data.objects.new("logbook", None); bpy.context.scene.collection.objects.link(root)
    leather = E.principled("ledger_leather", (0.09, 0.035, 0.02), rough=0.55)
    cover = ship.box("log_cover", (0, 0, 0.004), (lw + 0.02, lh + 0.02, 0.008), leather, bevel=0.003); cover.parent = root
    paper = E.principled("ledger_paper", (0.78, 0.72, 0.58), rough=0.9)
    for sg in (-1, 1):
        b = ship.box("log_block", (sg * lw / 4, 0, 0.016), (lw / 2 - 0.01, lh - 0.008, 0.016), paper, bevel=0.002); b.parent = root
    pg = _textured_plane("log_page", (0, 0, 0.0245), lw - 0.012, lh - 0.012, _img_mat("logpage", tex, 0.85))
    sub = pg.modifiers.new("Sub", "SUBSURF"); sub.subdivision_type = 'SIMPLE'; sub.levels = 4; sub.render_levels = 4
    pg.parent = root
    root.location = c; root.rotation_euler = (0, 0, rot)
    return root


def slate(c, rot=0.0):
    """A school-type writing slate in a wooden frame with the chalk log of the last morning."""
    tex = _page_texture(os.path.join(E.P1, "out", "tex", "slate.png"), "slate")
    root = bpy.data.objects.new("slate", None); bpy.context.scene.collection.objects.link(root)
    fr = ship.wood("brown_planks_05", 3.0, tint=(0.8, 0.6, 0.4), name="slateframe")
    W, Hh = 0.34, 0.24
    for (x, y, sx, sy) in ((0, Hh / 2, W + 0.03, 0.022), (0, -Hh / 2, W + 0.03, 0.022), (W / 2, 0, 0.022, Hh), (-W / 2, 0, 0.022, Hh)):
        o = ship.box("slate_frame", (x, y, 0.008), (sx, sy, 0.016), fr, bevel=0.003); o.parent = root
    st = _textured_plane("slate_face", (0, 0, 0.007), W - 0.02, Hh - 0.02, _img_mat("slateface", tex, 0.7)); st.parent = root
    ch = E.principled("chalk", (0.85, 0.85, 0.8), rough=0.9)
    o = ship.cyl("chalk", (W / 2 + 0.05, -0.05, 0.006), (W / 2 + 0.09, -0.02, 0.006), 0.005, mat=ch, verts=10); o.parent = root
    root.location = c; root.rotation_euler = (0, 0, rot)
    return root


# ============================================================================ galley
GAL = dict(RX=1.9, RY=1.55, RZ=1.95, SILL=0.32, WATER=0.29, DOOR=("x-", 0.35, 0.72, 1.7))


def galley(fog=0.015, water=True):
    """The galley in the deckhouse. The door in the after wall has a raised sill (the coaming, 'the raised lip').
    Water has sloshed about inside up to the sill; the stove has shifted off its chocks."""
    c = GAL; RX, RY, RZ = c["RX"], c["RY"], c["RZ"]
    walls = ship.paint("galleywalls", (0.55, 0.46, 0.32), rough=0.6, grime=0.8, chips=0.4, scale=5, wet=0.4)
    floor = wood("weathered_planks", 0.9, wet=0.9, tint=(0.75, 0.6, 0.45), name="gfloor")
    beams_m = ship.paint("gbeams", (0.3, 0.24, 0.17), rough=0.5, grime=0.7, chips=0.3, scale=6)
    _room(RX, RY, RZ, walls, floor, beams_m, door=c["DOOR"])
    # the door sill: a raised board across the bottom of the doorway
    dc, dw = c["DOOR"][1], c["DOOR"][2]
    sill_m = wood("brown_planks_05", 1.4, wet=0.8, tint=(0.75, 0.5, 0.32), name="sill")
    ship.box("door_sill", (-RX - 0.03, dc, c["SILL"] / 2), (0.12, dw + 0.12, c["SILL"]), sill_m, bevel=0.01)
    # outside: daylight on the deck beyond the door
    ext = ship.wood("wood_floor_deck", 1.0, wet=0.6, name="deckout")
    ship.box("deck_out", (-RX - 1.6, dc, -0.03), (3.0, 3.0, 0.06), ext)
    # beyond the door: the sunlit deck, a bulwark and bright sky (an emissive backdrop), daylight pouring in
    ship.box("bulwark_out", (-RX - 2.9, dc, 0.5), (0.15, 3.0, 1.0), ship.paint("bwout", (0.42, 0.38, 0.3), rough=0.5, grime=0.5))
    ship.box("sky_out", (-RX - 4.0, dc, 2.0), (0.05, 8.0, 5.0), E.emission_mat("skyout", (0.55, 0.72, 1.0), 2.2))
    E.area("door_day", (-RX - 1.2, dc, 1.6), (-RX + 1.2, dc, 0.1), 900, size=1.4, color=(0.9, 0.95, 1.0))
    E.area("deck_sun", (-RX - 2.0, dc - 1.5, 3.0), (-RX - 1.4, dc, 0.0), 1500, size=1.0, color=(1.0, 0.86, 0.66))
    # the stove: an iron barrel stove, knocked off its brick hearth and leaning, its pipe pulled out of the deck collar
    hearth_m = ship.paint("hearth", (0.36, 0.12, 0.07), rough=0.8, grime=0.6, scale=12)
    hx, hy = 0.9, -0.85
    ship.box("hearth", (hx, hy, 0.05), (0.9, 0.8, 0.1), hearth_m, bevel=0.01)
    ship.box("hearth_chock", (hx - 0.42, hy, 0.15), (0.06, 0.8, 0.1), sill_m)
    sv, sms = ph.model("barrel_stove")
    lo, hi = ph.bounds(sms); s = 0.85 / max(hi.z - lo.z, 1e-3); sv.scale = (s, s, s)
    sv.location = (hx - 0.55, hy + 0.25, 0.0); sv.rotation_euler = (math.radians(7), math.radians(-5), math.radians(38))
    bpy.context.view_layer.update(); lo, hi = ph.bounds(sms); sv.location.z -= lo.z
    iron = ship.iron("gpipe")
    ship.cyl("stovepipe_hanging", (hx, hy, RZ), (hx + 0.05, hy - 0.05, RZ - 0.55), 0.07, mat=iron, verts=16)
    ship.cyl("stovepipe_fallen", (hx - 0.2, hy + 0.7, 0.07), (hx - 0.95, hy + 0.55, 0.07), 0.07, mat=iron, verts=16)
    # pots and a kettle thrown down
    for aid, loc, rot in (("pot_enamel_01", (0.1, 0.6, 0.0), (0, 0, 0.5)), ("brass_pot_01", (-0.6, -0.9, 0.0), (1.5, 0, 0.3)),
                          ("wooden_bucket_02", (1.3, 0.9, 0.0), (0, 0, 0.0))):
        o, ms = ph.model(aid); o.location = loc; o.rotation_euler = rot
        bpy.context.view_layer.update(); lo, hi = ph.bounds(ms); o.location.z -= lo.z
    # shelf with a lip along the fore wall, some crockery still on it
    ship.box("shelf", (RX - 0.18, 0, 1.25), (0.3, 2.2, 0.03), sill_m)
    ship.box("shelf_lip", (RX - 0.32, 0, 1.3), (0.02, 2.2, 0.08), sill_m)
    # the water: standing just under the sill top, with the tide line on the walls and on the sill
    if water:
        wm = water_body_mat()
        ship.box("galley_water", (0, 0, c["WATER"] / 2), (2 * RX - 0.01, 2 * RY - 0.01, c["WATER"]), wm)
    tide = ship.paint("tideline", (0.16, 0.14, 0.11), rough=0.4, grime=0.2, wet=0.9)
    for sg in (1, -1):
        ship.box("tide_y", (0, sg * (RY - 0.004), c["SILL"] - 0.03), (2 * RX, 0.004, 0.06), tide)
    ship.box("tide_x", (RX - 0.004, 0, c["SILL"] - 0.03), (0.004, 2 * RY, 0.06), tide)
    w = bpy.data.worlds.new("W"); bpy.context.scene.world = w; w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[0].default_value = (0.5, 0.42, 0.34, 1); w.node_tree.nodes["Background"].inputs[1].default_value = 0.02
    if float(os.environ.get("NOFOG", "0")) == 0:
        _air(RX, RY, RZ, fog)
    return dict(sill=Vector((-RX - 0.03, dc, c["SILL"])), stove=Vector((hx - 0.55, hy + 0.25, 0.4)), door=Vector((-RX, dc, 0)))
