"""BOX: the forensic reconstruction of the box, shown EMPTY in a dim police evidence hall (Ch2 sets 7-10; reusable in Ch3-4).

The reconstructed box stands upright on a low pallet in the middle of the hall, one side panel removed (a cutaway) so
the inside reads: a shelf, a seat with a lid, a bulb wired out through the wall to a car battery on the floor, two
plastic pipes with many small holes (one high, one low) with fabric wrapped round their ends, a portable radio on the
shelf, bottles of water and orange soda, chocolate bars and books. No person, ever.
Hall: concrete floor, high windows (grey daylight), one work lamp over the box, a side table with files for the experts.
Coordinates: the box footprint is centred at the origin; the open side faces -Y.
"""
import math
import numpy as np
import bpy
from mathutils import Vector, Matrix
from kit import pbr, box, cyl, join, area_light, point_at, haze, emissive
from common import ease
import ph
import rj
from rj import mat, person, stand, walk, forward, upright, reach, fingers_curl, SIDE

EXPOSURE = 0.0
BOUNCES = 6
W, D, H = 0.72, 0.62, 1.38            # outer size of the box
T = 0.022
Z0 = 0.14                             # standing on a low pallet
DUR = {}
EXP_TABLE = Vector((-3.2, 1.6, 0.0))


def perforated_pipe(name, a, b, r=0.028):
    """Grey PVC pipe from a to b with rows of small drilled holes ON its surface: a hole grid in the pipe's own
    coordinates (along its axis x around it), dark and pressed in by a bump."""
    m = bpy.data.materials.new(name + "M"); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; p = N["Principled BSDF"]
    p.inputs['Roughness'].default_value = 0.42; p.inputs['Specular IOR Level'].default_value = 0.45
    tc = N.new("ShaderNodeTexCoord"); sep = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs['Object'], sep.inputs[0])
    ang = N.new("ShaderNodeMath"); ang.operation = 'ARCTAN2'; L.new(sep.outputs['Y'], ang.inputs[0]); L.new(sep.outputs['X'], ang.inputs[1])
    u = N.new("ShaderNodeMath"); u.operation = 'MULTIPLY'; u.inputs[1].default_value = 16.0 / (2 * math.pi); L.new(ang.outputs[0], u.inputs[0])
    v = N.new("ShaderNodeMath"); v.operation = 'MULTIPLY'; v.inputs[1].default_value = 1.0 / 0.022; L.new(sep.outputs['Z'], v.inputs[0])
    cmb = N.new("ShaderNodeCombineXYZ"); L.new(u.outputs[0], cmb.inputs[0]); L.new(v.outputs[0], cmb.inputs[1])
    fr = N.new("ShaderNodeVectorMath"); fr.operation = 'FRACTION'; L.new(cmb.outputs[0], fr.inputs[0])
    sub = N.new("ShaderNodeVectorMath"); sub.operation = 'SUBTRACT'; sub.inputs[1].default_value = (0.5, 0.5, 0.0); L.new(fr.outputs[0], sub.inputs[0])
    ln = N.new("ShaderNodeVectorMath"); ln.operation = 'LENGTH'; L.new(sub.outputs[0], ln.inputs[0])
    hole = N.new("ShaderNodeMath"); hole.operation = 'LESS_THAN'; hole.inputs[1].default_value = 0.12; L.new(ln.outputs['Value'], hole.inputs[0])
    nz = N.new("ShaderNodeTexNoise"); nz.inputs['Scale'].default_value = 80; L.new(tc.outputs['Object'], nz.inputs['Vector'])
    base = N.new("ShaderNodeMix"); base.data_type = 'RGBA'; base.inputs['Factor'].default_value = 0.08
    base.inputs[6].default_value = (0.24, 0.25, 0.25, 1); L.new(nz.outputs['Color'], base.inputs[7])
    dk = N.new("ShaderNodeMix"); dk.data_type = 'RGBA'; L.new(hole.outputs[0], dk.inputs['Factor'])
    L.new(base.outputs[2], dk.inputs[6]); dk.inputs[7].default_value = (0.006, 0.006, 0.006, 1)
    L.new(dk.outputs[2], p.inputs['Base Color'])
    inv = N.new("ShaderNodeMath"); inv.operation = 'SUBTRACT'; inv.inputs[0].default_value = 1.0; L.new(hole.outputs[0], inv.inputs[1])
    bm = N.new("ShaderNodeBump"); bm.inputs['Strength'].default_value = 0.8; bm.inputs['Distance'].default_value = 0.002
    L.new(inv.outputs[0], bm.inputs['Height']); L.new(bm.outputs['Normal'], p.inputs['Normal'])
    a = Vector(a); b = Vector(b); d = b - a
    o = cyl(name, (a + b) / 2, r, d.length, m, 32)
    o.rotation_euler = d.to_track_quat('Z', 'Y').to_euler()
    return o


def chipboard_ply():
    """Raw plywood for the reconstruction (Poly Haven 'plywood'); a pale procedural fallback, never pink."""
    try:
        return ph.texture("plywood", scale=1.6, name="ReconPly")
    except Exception:
        return pbr("ReconPly", (0.48, 0.38, 0.25), 0.75)


def lathe(name, profile, mat_, segs=32):
    """Solid of revolution about Z from [(r, z), ...] (bottom to top), closed at both ends."""
    import bmesh
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    rings = []
    for (r, z) in profile:
        rings.append([bm.verts.new((r * math.cos(2 * math.pi * k / segs), r * math.sin(2 * math.pi * k / segs), z)) for k in range(segs)])
    for i in range(len(rings) - 1):
        for k in range(segs):
            bm.faces.new((rings[i][k], rings[i][(k + 1) % segs], rings[i + 1][(k + 1) % segs], rings[i + 1][k]))
    bm.faces.new(list(reversed(rings[0]))); bm.faces.new(rings[-1])
    bm.normal_update(); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(o); o.data.materials.append(mat_)
    for pg in me.polygons:
        pg.use_smooth = True
    return o


BOTTLE = [(0.001, 0.0), (0.03, 0.0), (0.033, 0.004), (0.034, 0.012), (0.034, 0.15), (0.032, 0.17), (0.024, 0.2), (0.016, 0.225),
          (0.0135, 0.245), (0.0135, 0.262), (0.0155, 0.266), (0.0155, 0.272), (0.012, 0.274)]


def bottle(name, loc, liquid, fill=0.78):
    """A 1981 0.7 l returnable glass bottle (no label, no brand), crown cap, with its liquid inside."""
    glass_m = pbr("BottleGlass2", (0.55, 0.72, 0.6), 0.06, 0.0, **{'Transmission Weight': 0.85, 'IOR': 1.5, 'Coat Weight': 0.6})   # pale green bottle glass
    g = lathe(name, BOTTLE, glass_m)
    top = 0.274 * fill
    inner = [(max(0.0005, r - 0.003), z) for (r, z) in BOTTLE if z <= top] + [(0.0005, top)]
    inner = [(r, max(0.003, z)) for (r, z) in inner]
    lq = lathe(name + "Liq", inner, liquid)
    cap = cyl(name + "Cap", (0, 0, 0.276), 0.0165, 0.008, pbr("CrownCap", (0.55, 0.52, 0.45), 0.35, 1.0), 20)
    for o in (g, lq, cap):
        o.location = Vector(loc) + o.location
    return [g, lq, cap]


def chocolate(name, loc, rz=0.0):
    """A plain wrapped chocolate bar: silver foil inside a paper sleeve (no print, no brand)."""
    foil = pbr("Foil", (0.8, 0.8, 0.82), 0.25, 1.0)
    paper = pbr("ChocPaper", (0.35, 0.16, 0.12), 0.7)
    f = box(name + "Foil", (0, 0, 0.006), (0.165, 0.078, 0.011), foil, bevel=0.002)
    pp = box(name + "Sleeve", (0, 0, 0.006), (0.11, 0.08, 0.0125), paper, bevel=0.001)
    o = join([f, pp], name); o.location = loc; o.rotation_euler.z = rz
    return o


def paperback(name, loc, col, thick=0.024, h=0.18, w=0.11, lean=0.0):
    """A worn paperback standing on its tail edge: soft card covers, a cream page block, a rounded spine."""
    cov = pbr(name + "Cov", col, 0.75)
    pages = pbr("Pages", (0.72, 0.66, 0.52), 0.85)
    parts = [box(name + "Blk", (0, 0, h / 2), (thick - 0.003, w - 0.004, h - 0.004), pages),
             box(name + "F", (-thick / 2 + 0.0008, 0, h / 2), (0.0016, w, h), cov, bevel=0.0006),
             box(name + "B", (thick / 2 - 0.0008, 0, h / 2), (0.0016, w, h), cov, bevel=0.0006),
             box(name + "S", (0, w / 2 - 0.001, h / 2), (thick, 0.003, h), cov, bevel=0.0012)]
    o = join(parts, name); o.location = loc; o.rotation_euler.x = lean
    return o


def build_box(c):
    ply = chipboard_ply(); dark = pbr("BoxInside", (0.22, 0.16, 0.1), 0.8)
    x0, x1, y0, y1 = -W / 2, W / 2, -D / 2, D / 2
    parts = [box("Pallet", (0, 0, Z0 / 2), (W + 0.25, D + 0.25, Z0), mat("rawwood")),
             box("Floor", (0, 0, Z0 + T / 2), (W, D, T), ply),
             box("Back", (0, y1 - T / 2, Z0 + H / 2), (W, T, H), ply),
             box("SideL", (x0 + T / 2, 0, Z0 + H / 2), (T, D, H), ply),
             box("SideR", (x1 - T / 2, 0, Z0 + H / 2), (T, D, H), ply),
             box("Top", (0, 0, Z0 + H - T / 2), (W, D, T), ply)]
    # the front panel stands beside the box, leaning on the pallet (the cutaway)
    fp = box("FrontPanel", (x0 - 0.5, y0 - 0.2, Z0 + H / 2 - 0.05), (W, T, H), ply, rot=(math.radians(-6), 0, math.radians(35)))
    for k in range(4):                                     # frame battens inside the corners
        sx = -1 if k % 2 else 1; sy = -1 if k < 2 else 1
        parts.append(box("Batten", (sx * (W / 2 - T - 0.02), sy * (D / 2 - T - 0.02), Z0 + H / 2), (0.04, 0.04, H - 2 * T), mat("rawwood")))
    # seat with a hinged lid (toilet opening), shelf, a strip of fabric over the pipe mouths
    parts += [box("SeatBox", (0, y1 - 0.2, Z0 + 0.22), (W - 2 * T, 0.36, 0.42), ply),
              box("SeatLid", (0, y1 - 0.2, Z0 + 0.44), (W - 2 * T - 0.06, 0.3, 0.02), mat("oak")),
              box("Shelf", (0, y1 - 0.14, Z0 + 1.0), (W - 2 * T, 0.24, 0.022), ply),
              box("ShelfLip", (0, y1 - 0.255, Z0 + 1.03), (W - 2 * T, 0.012, 0.04), ply)]
    bj = join(parts, "ReconBox")
    c["box"] = bj
    sh_z = Z0 + 1.011
    # the bulb: a holder on the ceiling, a lit bulb, a cable out through the side to the battery
    holder = cyl("BulbHolder", (0, 0, Z0 + H - T - 0.03), 0.02, 0.05, pbr("Bakelite", (0.05, 0.04, 0.03), 0.4), 16)
    bulb_m = pbr("BulbGlass", (1, 0.9, 0.7), 0.1, 0.0, **{'Emission Color': (1.0, 0.75, 0.45, 1), 'Emission Strength': 4.0})
    bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=16, radius=0.025, location=(0, 0, Z0 + H - T - 0.075))
    bulb = bpy.context.active_object; bulb.data.materials.append(bulb_m)
    c["bulb_mat"] = bulb_m
    bl = bpy.data.lights.new("BulbL", 'POINT'); bl.energy = 22; bl.color = (1.0, 0.72, 0.42); bl.shadow_soft_size = 0.02
    bo = bpy.data.objects.new("BulbL", bl); bpy.context.collection.objects.link(bo); bo.location = (0, 0, Z0 + H - T - 0.075)
    batt = Vector((W / 2 + 0.85, 0.35, 0.0))
    bat = join([box("Battery", (batt.x, batt.y, 0.1), (0.3, 0.18, 0.2), pbr("BattCase", (0.04, 0.04, 0.045), 0.5), bevel=0.01),
                cyl("TermA", (batt.x - 0.09, batt.y, 0.215), 0.012, 0.03, pbr("Lead", (0.5, 0.5, 0.5), 0.4, 1.0), 12),
                cyl("TermB", (batt.x + 0.09, batt.y, 0.215), 0.012, 0.03, pbr("Lead2", (0.5, 0.5, 0.5), 0.4, 1.0), 12)], "CarBattery")
    c["battery"] = batt
    cable = [Vector((0, 0, Z0 + H - T - 0.03)), Vector((0.2, 0.05, Z0 + H - T - 0.015)), Vector((W / 2 - T - 0.01, 0.15, Z0 + H - 0.1)),
             Vector((W / 2 + 0.02, 0.15, Z0 + H - 0.1)), Vector((W / 2 + 0.12, 0.2, Z0 + 0.6)), Vector((W / 2 + 0.3, 0.3, 0.01)),
             Vector((batt.x - 0.2, batt.y, 0.01)), Vector((batt.x - 0.09, batt.y, 0.23))]
    cu = bpy.data.curves.new("BulbCable", 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = 0.004; cu.bevel_resolution = 2
    sp = cu.splines.new('NURBS'); sp.points.add(len(cable) - 1)
    for p, q in zip(sp.points, cable):
        p.co = (*q, 1)
    sp.use_endpoint_u = True; sp.order_u = 3
    co = bpy.data.objects.new("BulbCable", cu); bpy.context.collection.objects.link(co); co.data.materials.append(pbr("CableBlack", (0.02, 0.02, 0.02), 0.5))
    c["cable_pts"] = cable
    # two perforated ventilation pipes: one high on the left wall, one low on the right, running out through the back
    c["pipes"] = [perforated_pipe("PipeHigh", (-W / 2 + T + 0.04, -D / 2 + 0.08, Z0 + H - 0.2), (-W / 2 + T + 0.04, D / 2 + 0.6, Z0 + H - 0.2)),
                  perforated_pipe("PipeLow", (W / 2 - T - 0.04, -D / 2 + 0.08, Z0 + 0.62), (W / 2 - T - 0.04, D / 2 + 0.6, Z0 + 0.62))]
    felt = pbr("Felt", (0.25, 0.22, 0.2), 0.95)
    for (x, z) in ((-W / 2 + T + 0.04, Z0 + H - 0.2), (W / 2 - T - 0.04, Z0 + 0.62)):
        cyl("Muffle", (x, -D / 2 + 0.1, z), 0.04, 0.08, felt, 20, rot=(math.radians(90), 0, 0))
    # on the shelf: portable radio, water and orange soda bottles, chocolate, paperbacks
    rad, dial = rj.portable_radio("BoxRadio")
    rad.location = (-0.17, D / 2 - 0.14, sh_z); rad.scale = (0.8, 0.8, 0.8)
    c["radio_dial"] = dial; c["radio"] = rad
    water = pbr("Water", (0.8, 0.88, 0.9), 0.0, 0.0, **{'Transmission Weight': 1.0, 'IOR': 1.33})
    soda = pbr("OrangeSoda", (0.95, 0.42, 0.04), 0.0, 0.0, **{'Transmission Weight': 0.85, 'IOR': 1.34})
    for k, (x, lq) in enumerate(((0.035, water), (0.1, water), (0.165, soda))):
        bottle(f"Bottle{k}", (x, D / 2 - 0.1, sh_z), lq, fill=0.5 if lq is water else 0.45)      # below the shoulder: the neck reads
    for k in range(3):
        chocolate(f"Choc{k}", (0.0 + 0.004 * k, D / 2 - 0.205, sh_z + 0.0005 + k * 0.0125), rz=0.06 * (k - 1))
    for k, (col, th) in enumerate((((0.42, 0.12, 0.07), 0.028), ((0.12, 0.2, 0.3), 0.022), ((0.5, 0.42, 0.16), 0.03), ((0.18, 0.28, 0.16), 0.02))):
        paperback(f"Paperback{k}", (W / 2 - T - 0.03 - 0.03 * k, D / 2 - 0.13, sh_z), col, thick=th, lean=0.0 if k < 3 else -0.25)
    # screws along the panel edges (outside faces) and round the shelf
    scr = pbr("ScrewHead", (0.38, 0.37, 0.34), 0.35, 1.0)
    pts = []
    for z in np.linspace(Z0 + 0.06, Z0 + H - 0.06, 9):
        for x in (x0 - 0.001, x1 + 0.001):
            for y in (y0 + 0.03, y1 - 0.03):
                pts.append(((x, y, z), 'X'))
    for x in np.linspace(x0 + 0.06, x1 - 0.06, 6):
        for y in (y0 + 0.03, y1 - 0.03):
            pts.append(((x, y, Z0 + H + 0.001), 'Z'))
    sparts = []
    for (q, ax) in pts:
        sparts.append(cyl("Screw", q, 0.0045, 0.002, scr, 8, rot=(0, math.radians(90), 0) if ax == 'X' else (0, 0, 0)))
    join(sparts, "Screws")
    # water canister and a blanket on the seat
    box("Blanket", (0.0, D / 2 - 0.2, Z0 + 0.47), (W - 2 * T - 0.1, 0.32, 0.03), rj.fabric("Blanket", (0.25, 0.2, 0.15), 0.95, 0.4) if hasattr(rj, "fabric") else felt)
    # evidence tags (blank, no text) hanging off the battery and the radio
    tag = pbr("Tag", (0.75, 0.7, 0.55), 0.8)
    box("TagA", (batt.x + 0.1, batt.y - 0.1, 0.26), (0.06, 0.003, 0.1), tag, rot=(0, 0, 0.3))
    box("TagBox", (x1 + 0.004, y0 + 0.12, Z0 + H - 0.25), (0.003, 0.07, 0.12), tag, rot=(math.radians(4), 0, 0))
    cyl("TagString", (x1 + 0.006, y0 + 0.12, Z0 + H - 0.15), 0.0012, 0.09, pbr("String", (0.6, 0.55, 0.45), 0.9), 6)


def hall(c):
    conc = mat("conc"); wall = pbr("HallWall", (0.36, 0.37, 0.36), 0.85)
    box("HallFloor", (0, 0, -0.01), (14, 12, 0.02), conc)
    for (x, y, sx, sy) in ((0, 6, 14, 0.2), (0, -6, 14, 0.2), (7, 0, 0.2, 12), (-7, 0, 0.2, 12)):
        rj.wall_x("HW", -7, 7, y, 0, 5, 0.2, wall, holes=[(-5, -2, 3.2, 4.4), (1, 4, 3.2, 4.4)]) if sy == 0.2 and y > 0 else (box("HallW", (x, y, 2.5), (sx, sy, 5), wall))
    box("HallCeil", (0, 0, 5.05), (14, 12, 0.1), wall)
    # high windows (north): grey daylight
    for x in (-3.5, 2.5):
        box("HighWin", (x, 6.05, 3.8), (3.0, 0.02, 1.2), rj.mat("glass"))
    sky = area_light((-0.5, 8.5, 4.0), (0, 0, 0), 6.0, 600, (0.75, 0.82, 0.95)); point_at(sky, (0, 0, 0.5)); sky.visible_camera = False
    # the work lamp over the box (a hanging enamel shade) and a dim warm practical over the experts' table
    lamp = cyl("WorkShade", (0, -0.1, 2.6), 0.22, 0.14, pbr("Enamel", (0.18, 0.2, 0.18), 0.4), 32)
    cyl("WorkCord", (0, -0.1, 3.8), 0.005, 2.4, mat("black"), 6)
    top = area_light((0, -0.4, 2.3), (0, 0, 0), 1.2, 260, (1.0, 0.94, 0.86)); top.visible_camera = False; point_at(top, (0, 0.0, 0.6)); top.name = "TopSoft"
    insp = area_light((0.15, -1.3, 1.5), (0, 0, 0), 0.5, 60, (1.0, 0.9, 0.78)); insp.visible_camera = False; point_at(insp, (0, 0.15, 0.9))
    insp.name = "InspLamp"                                   # the investigators' lamp into the open side
    sp = bpy.data.lights.new("WorkL", 'SPOT'); sp.energy = 900; sp.spot_size = math.radians(70); sp.spot_blend = 0.5; sp.color = (1.0, 0.93, 0.84)
    so = bpy.data.objects.new("WorkL", sp); bpy.context.collection.objects.link(so); so.location = (0, -0.1, 2.5)
    fill = area_light((2.5, -4.0, 2.5), (0, 0, 0), 2.0, 40, (0.7, 0.8, 1.0)); point_at(fill, (0, 0, 0.8)); fill.visible_camera = False
    # experts' table with files and a desk lamp
    tr, _ = rj.model_fit("metal_office_desk", (EXP_TABLE.x, EXP_TABLE.y, 0), rot_z=0.0, height=0.76)
    c["desk"] = tr
    lo, hi = ph.bounds([o for o in tr.children_recursive if o.type == 'MESH']); c["desk_top"] = hi.z
    for k in range(5):
        box("File", (EXP_TABLE.x - 0.4 + 0.18 * k, EXP_TABLE.y - 0.05 + 0.03 * (k % 2), hi.z + 0.015 + 0.0), (0.24, 0.32, 0.03 + 0.01 * k), pbr(f"FileC{k}", [(0.55, 0.45, 0.25), (0.2, 0.3, 0.45), (0.6, 0.55, 0.45)][k % 3], 0.7))
    c["folder"] = box("Folder", (0, 0, 0), (0.24, 0.32, 0.02), pbr("FolderC", (0.5, 0.15, 0.1), 0.7))
    dl = area_light((EXP_TABLE.x + 0.5, EXP_TABLE.y + 0.2, 1.4), (0, 0, 0), 0.3, 30, (1.0, 0.78, 0.5)); point_at(dl, EXP_TABLE + Vector((0, 0, 0.7))); dl.visible_camera = False
    try:
        rj.model_fit("desk_lamp_arm_01", (EXP_TABLE.x + 0.55, EXP_TABLE.y + 0.25, hi.z), rot_z=2.5, height=0.45)
    except Exception:
        pass
    evidence_hall(c)
    # (no indoor haze: it goes milky)


def evidence_hall(c):
    """Dress the hall as a police evidence store: steel shelving along the walls loaded with cardboard evidence
    boxes (blank tags), a painted dado band, fluorescent tubes on the ceiling, a floodlight on a tripod by the box."""
    card = [pbr(f"Card{k}", col, 0.85) for k, col in enumerate(((0.42, 0.31, 0.18), (0.36, 0.27, 0.16), (0.48, 0.38, 0.24)))]
    tag = pbr("ShelfTag", (0.78, 0.74, 0.6), 0.8)
    steel = pbr("ShelfSteel", (0.22, 0.24, 0.25), 0.45, 0.8)
    rr = np.random.default_rng(3)
    for (cx, cy, rz, n) in ((6.6, 3.0, math.pi / 2, 3), (6.6, -1.5, math.pi / 2, 2), (-6.6, 2.5, -math.pi / 2, 3), (-6.6, -2.0, -math.pi / 2, 2), (2.0, 5.6, math.pi, 3)):
        for k in range(n):
            # one bay: 4 posts, 4 shelves 1.0 x 0.5, 2.2 m high (built here so its size is exact)
            off = (k - (n - 1) / 2) * 1.05
            ux, uy = (0.0, 1.0) if abs(math.sin(rz)) > 0.5 else (1.0, 0.0)
            bx, by = cx + ux * off, cy + uy * off
            sx, sy = (0.5, 1.0) if ux == 0.0 else (1.0, 0.5)
            parts = []
            for px in (-1, 1):
                for py in (-1, 1):
                    parts.append(box("Post", (bx + px * (sx / 2 - 0.02), by + py * (sy / 2 - 0.02), 1.1), (0.035, 0.035, 2.2), steel))
            for z in (0.12, 0.72, 1.32, 1.92):
                parts.append(box("ShelfB", (bx, by, z), (sx, sy, 0.02), steel))
                for j in range(2):
                    if rr.uniform() < 0.85:
                        w_, d_, h_ = rr.uniform(0.32, 0.45), rr.uniform(0.3, 0.42), rr.uniform(0.22, 0.4)
                        jx = (j - 0.5) * 0.48 if ux == 1.0 else 0.0; jy = (j - 0.5) * 0.48 if uy == 1.0 else 0.0
                        cb = box("EvBox", (bx + jx, by + jy, z + 0.01 + h_ / 2), (w_ if ux else d_, d_ if ux else w_, h_), card[int(rr.integers(0, 3))], bevel=0.004)
                        cb.rotation_euler.z = rr.uniform(-0.05, 0.05)
                        parts.append(cb)
                        nx, ny = (-math.cos(rz - math.pi / 2), -math.sin(rz - math.pi / 2))
                        parts.append(box("EvTag", (bx + jx + nx * 0.0, by + jy, z + 0.01 + h_ * 0.6), (0.09, 0.09, 0.05), tag))
            join(parts, "ShelfBay")
    wall = pbr("Dado", (0.24, 0.3, 0.27), 0.7)
    for (x, y, sx, sy) in ((0, 5.88, 13.8, 0.02), (0, -5.88, 13.8, 0.02), (6.88, 0, 0.02, 11.8), (-6.88, 0, 0.02, 11.8)):
        box("DadoBand", (x, y, 0.6), (sx, sy, 1.2), wall)
    tube = pbr("Tube", (1, 1, 1), 0.3, 0.0, **{'Emission Color': (0.92, 0.96, 1.0, 1), 'Emission Strength': 6.0})
    for x in (-4.0, 0.0, 4.0):
        for y in (-3.0, 2.0):
            box("TubeFix", (x, y, 4.95), (1.3, 0.16, 0.06), pbr("TubeFixM", (0.75, 0.75, 0.72), 0.5))
            box("TubeLight", (x, y, 4.91), (1.2, 0.05, 0.03), tube)
    # floodlight on a tripod beside the box (the work lamp of the reconstruction team)
    fl = Vector((1.25, -1.35, 0.0))
    legs = []
    for k in range(3):
        a_ = k * 2 * math.pi / 3
        f0 = fl + Vector((0.42 * math.cos(a_), 0.42 * math.sin(a_), 0.0)); f1 = fl + Vector((0, 0, 1.15))
        mid = (f0 + f1) / 2; dv = f1 - f0
        lg = cyl("TripodLeg", mid, 0.012, dv.length, steel, 8); lg.rotation_euler = dv.to_track_quat('Z', 'Y').to_euler(); legs.append(lg)
    legs.append(cyl("TripodPole", fl + Vector((0, 0, 1.4)), 0.015, 0.55, steel, 8))
    head = box("FloodHead", fl + Vector((0, 0, 1.72)), (0.26, 0.14, 0.2), pbr("FloodBody", (0.12, 0.12, 0.11), 0.5), bevel=0.02)
    head.rotation_euler = (math.radians(-20), 0, math.radians(35)); legs.append(head)
    join(legs, "Floodlight")


def build(variant=None):
    v = variant or "hall"
    roles = v.split("|")[1].split(",") if "|" in v else []
    c = dict(variant=v, P={})
    rj.sky("grey")
    for o in [o for o in bpy.data.objects if o.type == 'LIGHT' and o.data.type == 'SUN']:
        o.data.energy = 0.0
    build_box(c)
    hall(c)
    for r in roles:
        base = r if r in rj.ROLES else r.rstrip("0123456789")
        c["P"][r] = person(base, name=r.capitalize(), cap=False)
    if "smoke" in v:
        smoke(c)
    import look
    look.interior_day(window=((-0.5, 7.5, 4.0), (0.0, 0.0, 0.7)), mood="overcast", key_size=3.0, keep=tuple(bpy.data.objects[n] for n in ("WorkL", "BulbL", "TopSoft", "InspLamp")))
    bpy.context.scene.view_settings.exposure += 0.5            # was +1.0: the cutaway read washed out
    rj.finish_scene()
    return c


def smoke(c):
    """A thin wisp of test smoke curling out of the low pipe's mouth: a slim curved volume tube whose density is a
    slowly drifting noise (frame-driven), so it reads as a broken thread of smoke that barely moves."""
    m0 = Vector((0, 0, 0))                                # built about the pipe mouth; the shot places it there
    pts = [m0, m0 + Vector((-0.02, -0.05, 0.01)), m0 + Vector((-0.04, -0.09, 0.05)), m0 + Vector((-0.07, -0.11, 0.12)),
           m0 + Vector((-0.08, -0.12, 0.2)), m0 + Vector((-0.11, -0.13, 0.3)), m0 + Vector((-0.12, -0.13, 0.42))]   # leans into the open box
    cu = bpy.data.curves.new("SmokeWisp", 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = 0.024; cu.bevel_resolution = 4
    cu.use_fill_caps = True
    sp = cu.splines.new('NURBS'); sp.points.add(len(pts) - 1)
    for q, pnt in zip(sp.points, pts):
        q.co = (*pnt, 1)
    sp.use_endpoint_u = True; sp.order_u = 4
    for k, q in enumerate(sp.points):                    # thinner at the mouth, spreading as it rises
        q.radius = 0.35 + 0.15 * k
    o = bpy.data.objects.new("Smoke", cu); bpy.context.collection.objects.link(o)
    bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); bpy.context.view_layer.objects.active = o
    bpy.ops.object.convert(target='MESH'); o = bpy.context.active_object
    import bmesh                                          # a closed, outward-facing shell (volumes need it)
    bm = bmesh.new(); bm.from_mesh(o.data); bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bmesh.ops.holes_fill(bm, edges=bm.edges, sides=0); bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(o.data); bm.free()
    m = bpy.data.materials.new("SmokeVol"); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; N.clear()
    out = N.new("ShaderNodeOutputMaterial"); vol = N.new("ShaderNodeVolumePrincipled")
    tc = N.new("ShaderNodeTexCoord"); nz = N.new("ShaderNodeTexNoise"); nz.noise_dimensions = '4D'; nz.inputs['Scale'].default_value = 40
    nz.inputs['Detail'].default_value = 4; nz.inputs['Distortion'].default_value = 0.6
    L.new(tc.outputs['Object'], nz.inputs['Vector']); rj.driven(nz.inputs['W'], "default_value", "frame * 0.006")
    mr = N.new("ShaderNodeMapRange"); mr.inputs['From Min'].default_value = 0.42; mr.inputs['From Max'].default_value = 0.66; mr.inputs['To Max'].default_value = 30.0
    L.new(nz.outputs['Fac'], mr.inputs['Value']); L.new(mr.outputs[0], vol.inputs['Density'])
    vol.inputs['Color'].default_value = (0.82, 0.83, 0.84, 1); vol.inputs['Anisotropy'].default_value = 0.3
    vol.inputs['Emission Strength'].default_value = 0.0
    L.new(vol.outputs[0], out.inputs['Volume']); o.data.materials.clear(); o.data.materials.append(m)
    try:
        m.cycles.volume_step_rate = 0.05                 # a 1-5 cm thread: sample it finely or it is skipped
    except Exception:
        pass
    bpy.context.scene.cycles.volume_step_rate = 0.1
    o.location = Vector((W / 2 - T - 0.04, -D / 2 - 0.03, Z0 + 0.62))
    c["smoke"] = o


# ============================================================================ shots
def _idle(c, sec):
    c["bulb_mat"].node_tree.nodes["Principled BSDF"].inputs['Emission Strength'].default_value = 4.0


def anim_box(c, t, shot, dur):
    sec = t * dur
    if shot == "radio" and "tech" in c["P"]:
        h = c["P"]["tech"]
        stand(h, (0.05, -D / 2 - 0.55, 0.0), math.pi)          # faces +Y into the open box
        k = ease(min(1.0, sec / 1.2)); back = ease(max(0.0, min(1.0, (sec - 2.0) / 1.0)))
        knob = c["radio"].matrix_world @ Vector((0.085, -0.045, 0.11))
        fwd = forward(h); right = fwd.cross(Vector((0, 0, 1))).normalized()
        rest = rj.rjp.chest_point(h, 0.25, 0.35) + right * 0.15
        tgt = rest.lerp(knob, k * (1 - back)) if True else knob
        rj.rjp.bend_to(h, knob, frac=0.85, max_deg=18)
        reach(h, "R", tgt, Vector((0, 0, -1)) + right * 0.5, fwd)
        fingers_curl(h, 40)
    if shot == "smoke" and "tech" in c["P"]:
        h = c["P"]["tech"]
        stand(h, (W / 2 + 0.15, -D / 2 - 0.55, 0.0), math.radians(165))
        mouth = Vector((W / 2 - T - 0.04, -D / 2 - 0.02, Z0 + 0.62))
        fwd = forward(h); right = fwd.cross(Vector((0, 0, 1))).normalized()
        rj.rjp.bend_to(h, mouth, frac=0.8, max_deg=25)
        reach(h, "R", mouth + Vector((0.02, -0.16, -0.02)), Vector((0, 0, -1)) + right * 0.5, (mouth - h.bone_head("upperarm01.R")).normalized())
        tube = c["smoke_tube"]; w_ = h.bone_tail("wrist.R")
        aim = (mouth - w_).normalized()
        tube.matrix_world = Matrix.Translation(w_) @ aim.to_track_quat('Z', 'Y').to_matrix().to_4x4()
        c["smoke"].location = mouth + Vector((0.0, -0.04 - 0.01 * sec, 0.004 * sec))
    if shot == "smoke" and "tech" not in c["P"]:
        mouth = Vector((W / 2 - T - 0.04, -D / 2 - 0.02, Z0 + 0.62))
        c["smoke"].location = mouth + Vector((0.0, 0.06 - 0.008 * sec, 0.004 * sec))       # out of the pipe mouth; the test smoke barely drifts
    if shot in ("experts", "door"):
        ex = [c["P"][r] for r in ("expert", "expert2") if r in c["P"]]
        if ex:
            e1 = ex[0]; stand(e1, (EXP_TABLE.x - 0.25, EXP_TABLE.y - 0.75, 0.0), math.pi)
            k = ease(min(1.0, sec / 1.8))
            f = c["folder"]
            top = c["desk_top"]
            held = rj.rjp.chest_point(e1, 0.3, 0.3)
            dest = EXP_TABLE + Vector((-0.25, -0.1, top + 0.012))
            f.location = held.lerp(dest, k); f.rotation_euler = (math.radians(50 * (1 - k)), 0, 0.1)
            fwd = forward(e1); right = fwd.cross(Vector((0, 0, 1))).normalized()
            for sd, sg in SIDE.items():
                reach(e1, sd, f.location + right * sg * -0.1 * (-1 if sd == "L" else 1) + Vector((0, 0, 0.01)), Vector((0, 0, -1)) + right * (0.5 if sd == "R" else -0.5), fwd)
            if len(ex) > 1:
                e2 = ex[1]; stand(e2, (EXP_TABLE.x + 0.55, EXP_TABLE.y - 0.65, 0.0), math.radians(200))
                s2 = forward(e2).cross(Vector((0, 0, 1))).normalized(); e2.rot("head", s2, -18)
    _idle(c, sec)


def cam_crane(c, t):
    e = ease(t)
    a = Vector((0.15, -1.6, 2.4)); b = Vector((0.08, -1.05, 1.15))
    return (a.lerp(b, e), Vector((0, 0.15, Z0 + 0.75)), 28)


def cam_cable(c, t):
    e = ease(t)
    p0 = c["cable_pts"]
    a = Vector((W / 2 + 2.4, -1.6, 1.5)); b = Vector((W / 2 + 2.3, -1.0, 0.8))
    tgt = Vector((W / 2 + 0.05, 0.15, Z0 + H - 0.15)).lerp(Vector(c["battery"]) + Vector((0, 0, 0.12)), e)
    return (a.lerp(b, e), tgt, 32)


def cam_shelf(c, t):
    e = ease(t)
    a = Vector((-0.22, -0.55, Z0 + 1.2)); b = Vector((0.2, -0.5, Z0 + 1.17))
    return (a.lerp(b, e), Vector((-0.05 + 0.2 * e, D / 2 - 0.14, Z0 + 1.1)), 40)


def cam_radio(c, t):
    e = ease(t)
    a = Vector((-1.6, -1.8, 1.7)); b = Vector((-1.45, -1.6, 1.65))
    return (a.lerp(b, e), Vector((-0.1, 0.0, Z0 + 0.95)), 28)


def cam_pipe(c, t):
    e = ease(t)
    x = -W / 2 + T + 0.04; z = Z0 + H - 0.2
    a = Vector((x + 0.16, -D / 2 - 0.05, z - 0.08)); b = Vector((x + 0.17, D / 2 - 0.12, z - 0.07))
    return (a.lerp(b, e), Vector((x, 0.1 + 0.2 * e, z)), 35)


def cam_smoke(c, t):
    e = ease(t)
    a = Vector((-0.22, -1.05, 1.0)); b = Vector((-0.15, -0.95, 0.96))                   # close on the pipe mouth and the thread rising
    return (a.lerp(b, e), Vector((W / 2 - T - 0.1, -D / 2 - 0.02, Z0 + 0.72)), 45)


def cam_experts(c, t):
    e = ease(t)
    a = EXP_TABLE + Vector((1.4, -2.4, 1.55)); b = EXP_TABLE + Vector((1.2, -2.1, 1.5))
    return (a.lerp(b, e), EXP_TABLE + Vector((0.0, -0.4, 1.0)), 35)


def cam_door(c, t):
    e = ease(t)
    a = Vector((4.5, -5.6, 1.7)); b = Vector((4.0, -5.2, 1.65))
    return (a.lerp(b, e), Vector((-0.9, 0.3, 0.8)), 28)


def _mk(shot, dur, cam, focus=None, dof=None):
    DUR[shot] = dur
    spec = dict(kind="anim", cam=cam, anim=lambda c, t: anim_box(c, t, shot, dur))
    if focus:
        spec["focus"] = focus; spec["dof"] = dof or 4.0
    return spec


MOVES = {
    "crane": _mk("crane", 5.0, cam_crane, lambda c, t: Vector((0, 0.1, Z0 + 0.8)), 4.0),
    "cable": _mk("cable", 4.5, cam_cable),
    "shelf": _mk("shelf", 4.5, cam_shelf, lambda c, t: Vector((0.0, D / 2 - 0.14, Z0 + 1.1)), 2.4),
    "radio": _mk("radio", 4.5, cam_radio, lambda c, t: Vector((-0.12, D / 2 - 0.14, Z0 + 1.08)), 2.8),
    "pipe": _mk("pipe", 4.5, cam_pipe, lambda c, t: Vector((-W / 2 + T + 0.04, 0.1, Z0 + H - 0.2)), 2.0),
    "smoke": _mk("smoke", 5.0, cam_smoke, lambda c, t: Vector((W / 2 - 0.05, -D / 2 - 0.1, Z0 + 0.62)), 2.8),
    "experts": _mk("experts", 4.5, cam_experts),
    "door": _mk("door", 5.0, cam_door),
}
VARIANT_FOR = {"radio": "hall|tech", "smoke": "hall+smoke", "experts": "hall|expert,expert2", "door": "hall|expert,expert2"}

_build = build


def build(variant=None):                      # noqa: F811
    c = _build(variant)
    if "smoke" in (variant or ""):
        c["smoke_tube"] = cyl("SmokeTube", (0, 0, 0), 0.012, 0.14, pbr("SmokeTubeM", (0.75, 0.75, 0.72), 0.4), 12)
    # the radio dial glows once the technician turns it on (frame-driven)
    if "tech" in (variant or "") and "smoke" not in (variant or ""):
        rj.emission_driven(c["radio_dial"], "1.6 * min(1, max(0, (frame - 30) / 6))")
    return c
