"""Part 3 interiors: a ship's cabin (Deveau writes home), the Vice-Admiralty Court at Gibraltar, a chemist's
laboratory, and the Mary Celeste's after cabin with the captain's berth. Atrium look: walnut and oxblood, brass,
warm window sun through haze, dark walls (albedo capped), one strong key per room."""
import math, random
import numpy as np
import bpy
from mathutils import Vector, Matrix
import ship, crew
import props as PR


def _plane_light(name, loc, target, size, energy, color, kind='AREA', spread=None, visible=False):
    L = bpy.data.lights.new(name, kind); L.energy = energy; L.color = color
    if kind == 'AREA':
        L.shape = 'RECTANGLE'; L.size, L.size_y = size
        if spread:
            L.spread = math.radians(spread)
    o = bpy.data.objects.new(name, L); bpy.context.scene.collection.objects.link(o)
    o.location = loc; o.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    o.visible_camera = visible
    return o


def world(color=(0.08, 0.06, 0.05), strength=0.3):
    w = bpy.data.worlds.new("W"); bpy.context.scene.world = w; w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[0].default_value = (*color, 1); w.node_tree.nodes["Background"].inputs[1].default_value = strength
    return w


def air(center, size, density=0.02, aniso=0.4):
    bpy.ops.mesh.primitive_cube_add(size=1, location=center)
    o = bpy.context.active_object; o.name = "room_air"; o.scale = size
    m = bpy.data.materials.new("room_air"); m.use_nodes = True; N = m.node_tree.nodes; N.remove(N["Principled BSDF"])
    v = N.new("ShaderNodeVolumeScatter"); v.inputs['Density'].default_value = density; v.inputs['Anisotropy'].default_value = aniso
    m.node_tree.links.new(v.outputs[0], N["Material Output"].inputs['Volume']); o.data.materials.append(m)
    o.visible_shadow = False
    return o


def sky_glow(name, loc, size, normal, color=(0.75, 0.82, 0.95), strength=4.0):
    """What you see through a window: a soft bright card outside the glass."""
    n = Vector(normal).normalized()
    o = ship.box(name, loc, (0.01, size[0], size[1]), None)
    o.rotation_euler = n.to_track_quat('X', 'Z').to_euler()
    m = bpy.data.materials.new(name); m.use_nodes = True; N = m.node_tree.nodes; N.remove(N["Principled BSDF"])
    em = N.new("ShaderNodeEmission"); em.inputs['Color'].default_value = (*color, 1); em.inputs['Strength'].default_value = strength
    m.node_tree.links.new(em.outputs[0], N["Material Output"].inputs['Surface']); o.data.materials.append(m)
    o.visible_shadow = False
    return o


def box_room(name, x0, x1, y0, y1, h, walls, floor, ceil=None, gaps=()):
    """Walls as boxes; gaps = [(wall, u0, u1, z0, z1)] openings (windows/doors) in wall 'n','s','e','w'."""
    t = 0.08; objs = []
    ceil = ceil or walls
    objs.append(ship.box(name + "_floor", ((x0 + x1) / 2, (y0 + y1) / 2, -0.03), (x1 - x0, y1 - y0, 0.06), floor))
    objs.append(ship.box(name + "_ceil", ((x0 + x1) / 2, (y0 + y1) / 2, h + 0.03), (x1 - x0, y1 - y0, 0.06), ceil))
    spec = {"s": ((x0, y0), (x1, y0)), "n": ((x0, y1), (x1, y1)), "w": ((x0, y0), (x0, y1)), "e": ((x1, y0), (x1, y1))}
    for wn, (a, b) in spec.items():
        a = Vector(a); b = Vector(b); L = (b - a).length; d = (b - a).normalized()
        cuts = sorted([g for g in gaps if g[0] == wn], key=lambda g: g[1])
        segs = []; u = 0.0
        for g in cuts:
            segs.append((u, g[1], 0, h)); segs.append((g[1], g[2], 0, g[3])); segs.append((g[1], g[2], g[4], h)); u = g[2]
        segs.append((u, L, 0, h))
        for (u0, u1, z0, z1) in segs:
            if u1 - u0 < 1e-3 or z1 - z0 < 1e-3:
                continue
            c = a + d * ((u0 + u1) / 2)
            sz = (u1 - u0, t, z1 - z0) if wn in "sn" else (t, u1 - u0, z1 - z0)
            objs.append(ship.box(f"{name}_wall_{wn}", (c.x, c.y, (z0 + z1) / 2), sz, walls))
    return objs


# ----------------------------------------------------------------------------- Deveau's cabin (Dei Gratia, Gibraltar)
def cabin_letter(day=True):
    walls = PR.mat_wood("cab_walls", "dark_wooden_planks", 1.4, tint=(0.75, 0.5, 0.33))
    floor = PR.mat_wood("cab_floor", "weathered_planks", 0.9, tint=(0.7, 0.52, 0.38))
    beams = ship.paint("cab_beams", (0.3, 0.2, 0.12), rough=0.5, grime=0.5, chips=0.2, scale=6)
    X0, X1, Y0, Y1, Hh = -1.6, 1.6, -1.4, 1.4, 2.0
    box_room("cab", X0, X1, Y0, Y1, Hh, walls, floor, beams, gaps=[("e", 1.0, 1.55, 0.95, 1.35)])
    x = X0 + 0.3
    while x < X1:
        ship.box("cab_beam", (x, 0, Hh - 0.06), (0.1, Y1 - Y0, 0.12), beams); x += 0.55
    sky_glow("cab_port", (X1 + 0.25, -0.12, 1.15), (0.6, 0.45), (-1, 0, 0), color=(0.85, 0.88, 0.95), strength=3.0)
    if day:
        _plane_light("cab_sun", (X1 + 0.8, -0.2, 2.0), (0.2, -0.1, 0.75), (0.55, 0.4), 260, (1.0, 0.85, 0.66), spread=25)
    tb = PR.table("cab_table", (0.35, -0.1, 0.0), size=(1.0, 0.7, 0.74))
    ch = PR.chair("cab_chair", (-0.7, -0.1, 0.0), 0)
    lamp, flame, lt = PR.oil_lamp("cab_lamp", (0.7, 0.12, 0.74), flame_energy=10)
    _plane_light("cab_lampkey", flame + Vector((-0.1, 0.0, 0.5)), (0.2, -0.1, 0.74), (0.4, 0.4), 30, (1.0, 0.66, 0.4))
    world((0.08, 0.06, 0.045), 0.25)
    air((0, 0, Hh / 2), (X1 - X0, Y1 - Y0, Hh), density=0.03)
    return dict(table_z=0.74, chair=(-0.45, -0.1), lamp=flame)      # chair centre is 0.13 behind the sitter's place


# ----------------------------------------------------------------------------- Vice-Admiralty Court
def court():
    """A high panelled room: judge's bench raised at the north wall, witness box east, counsel's table centre,
    benches for the salvors south-west, tall windows on the west wall with sun shafts through the haze."""
    pan = PR.mat_wood("ct_panel", "dark_wooden_planks", 0.8, tint=(0.62, 0.36, 0.22))
    plaster = crew.flat("ct_plaster", (0.36, 0.3, 0.24), rough=0.9)
    floor = PR.mat_wood("ct_floor", "weathered_planks", 0.7, tint=(0.55, 0.36, 0.24))
    cloth = crew.flat("ct_baize", (0.22, 0.04, 0.03), rough=0.85)            # oxblood
    X0, X1, Y0, Y1, Hh = -5.0, 5.0, 0.0, 12.0, 6.5
    gaps = [("w", 2.0, 3.6, 1.6, 5.2), ("w", 5.4, 7.0, 1.6, 5.2), ("w", 8.8, 10.4, 1.6, 5.2)]
    box_room("ct", X0, X1, Y0, Y1, Hh, plaster, floor, plaster, gaps=gaps)
    # wainscot panelling to 2.2 m on all walls (not over the windows' sill line)
    for (c, s) in (((0, Y1 - 0.06, 1.1), (X1 - X0, 0.05, 2.2)), ((0, Y0 + 0.06, 1.1), (X1 - X0, 0.05, 2.2)),
                   ((X1 - 0.06, (Y0 + Y1) / 2, 1.1), (0.05, Y1 - Y0, 2.2))):
        ship.box("ct_wainscot", c, s, pan)
    for (u0, u1) in ((0, 2.0), (3.6, 5.4), (7.0, 8.8), (10.4, 12.0)):
        ship.box("ct_wainscot", (X0 + 0.06, (u0 + u1) / 2, 1.1), (0.05, u1 - u0, 2.2), pan)
    for (u0, u1) in ((2.0, 3.6), (5.4, 7.0), (8.8, 10.4)):
        ship.box("ct_wainscot", (X0 + 0.06, (u0 + u1) / 2, 0.8), (0.05, u1 - u0, 1.6), pan)
    # windows: glazing bars and the bright sky outside
    for (u0, u1) in ((2.0, 3.6), (5.4, 7.0), (8.8, 10.4)):
        for k in range(1, 3):
            ship.box("ct_bar", (X0, u0 + (u1 - u0) * k / 3, 3.4), (0.06, 0.05, 3.6), pan)
        for zb in (2.8, 4.0):
            ship.box("ct_bar", (X0, (u0 + u1) / 2, zb), (0.06, u1 - u0, 0.05), pan)
        sky_glow("ct_sky", (X0 - 0.6, (u0 + u1) / 2, 3.4), (u1 - u0 + 0.6, 3.9), (1, 0, 0), color=(0.8, 0.86, 0.95), strength=2.5)
    # judge's bench (raised dais) at the north wall
    ship.box("ct_dais", (0, Y1 - 1.3, 0.3), (5.0, 2.4, 0.6), pan)
    ship.box("ct_bench_front", (0, Y1 - 2.4, 1.15), (4.4, 0.12, 1.1), pan, bevel=0.01)
    ship.box("ct_bench_top", (0, Y1 - 2.2, 1.72), (4.6, 0.6, 0.06), pan, bevel=0.01)
    ship.box("ct_bench_cloth", (0, Y1 - 2.2, 1.755), (4.0, 0.5, 0.01), cloth)
    PR.chair("ct_judgechair", (0, Y1 - 1.5, 0.6), -90, seat_h=0.78)
    # witness box (east)
    wb = (3.2, 7.2)
    ship.box("ct_wbox_floor", (wb[0], wb[1], 0.2), (1.2, 1.2, 0.4), pan)
    for (c, s) in (((wb[0] - 0.6, wb[1], 0.95), (0.06, 1.2, 1.1)), ((wb[0], wb[1] - 0.6, 0.95), (1.2, 0.06, 1.1)), ((wb[0], wb[1] + 0.6, 0.95), (1.2, 0.06, 1.1))):
        ship.box("ct_wbox", c, s, pan, bevel=0.005)
    ship.box("ct_wbox_rail", (wb[0] - 0.6, wb[1], 1.52), (0.12, 1.25, 0.05), pan, bevel=0.005)
    # counsel's table and the clerk's desk
    PR.table("ct_counsel", (-0.6, 5.2, 0.0), size=(2.4, 0.9, 0.78), mat=pan)
    ship.box("ct_counsel_cloth", (-0.6, 5.2, 0.785), (2.3, 0.8, 0.01), cloth)
    PR.table("ct_clerk", (0.0, Y1 - 3.4, 0.0), size=(1.6, 0.7, 0.76), mat=pan)
    # benches for the salvors (south-west)
    for k, yy in enumerate((3.0, 1.9)):
        ship.box("ct_pew_seat", (-2.6, yy, 0.45), (3.4, 0.42, 0.05), pan)
        ship.box("ct_pew_back", (-2.6, yy - 0.22, 0.9), (3.4, 0.05, 0.9), pan)
        for xx in (-4.2, -1.0):
            ship.box("ct_pew_end", (xx, yy - 0.05, 0.5), (0.06, 0.5, 1.0), pan)
    # papers and books
    for k in range(5):
        PR.paper(f"ct_paper{k}", (-1.4 + k * 0.32, 5.1 + 0.05 * (k % 2), 0.795 + 0.001 * k), size=(0.21, 0.29), rot_z=0.2 * (k - 2))
    _plane_light("ct_sun", (X0 - 4.0, 6.0, 7.5), (0.5, 6.2, 0.0), (10, 9), 3500, (1.0, 0.8, 0.58), spread=8)
    _plane_light("ct_bounce", (2.0, 4.0, 5.8), (0, 6, 0), (4, 4), 160, (1.0, 0.75, 0.55))
    world((0.07, 0.05, 0.04), 0.3)
    air((0, 6, Hh / 2), (X1 - X0, Y1 - Y0, Hh), density=0.012, aniso=0.55)
    return dict(witness=wb, judge=(0, Y1 - 1.5, 0.6), counsel=(-0.6, 5.2), clerk=(0.0, Y1 - 3.4), pews=((-2.6, 3.0), (-2.6, 1.9)))


# ----------------------------------------------------------------------------- the chemist's laboratory
def lab():
    walls = crew.flat("lab_walls", (0.3, 0.26, 0.2), rough=0.9)
    floor = PR.mat_wood("lab_floor", "weathered_planks", 0.8, tint=(0.6, 0.45, 0.32))
    bench = PR.mat_wood("lab_bench", "dark_wooden_planks", 1.2, tint=(0.7, 0.45, 0.28))
    X0, X1, Y0, Y1, Hh = -2.5, 2.5, -2.0, 2.5, 3.2
    box_room("lab", X0, X1, Y0, Y1, Hh, walls, floor, walls, gaps=[("n", 1.6, 3.2, 1.0, 2.7)])
    for k in range(1, 3):
        ship.box("lab_bar", (X0 + 1.6 + 1.6 * k / 3, Y1, 1.85), (0.05, 0.06, 1.7), bench)
    ship.box("lab_bar", (X0 + 2.4, Y1, 1.85), (1.6, 0.06, 0.05), bench)
    sky_glow("lab_sky", (X0 + 2.4, Y1 + 0.5, 1.85), (2.2, 2.2), (0, -1, 0), color=(0.85, 0.88, 0.94), strength=1.2)
    PR.table("lab_benchtop", (0.0, 1.8, 0.0), size=(3.2, 0.8, 0.9), mat=bench)
    _plane_light("lab_sun", (X0 + 2.4, Y1 + 1.5, 3.2), (0, 1.2, 0.9), (1.6, 1.7), 320, (1.0, 0.84, 0.64), spread=30)
    world((0.08, 0.065, 0.05), 0.3)
    air((0, 0.2, Hh / 2), (X1 - X0, Y1 - Y0, Hh), density=0.02)
    # shelves of bottles on the east wall
    rng = random.Random(3)
    for row in range(3):
        ship.box("lab_shelf", (X1 - 0.18, 0.6, 1.3 + row * 0.45), (0.3, 1.8, 0.03), bench)
        for k in range(9):
            col = rng.choice([(0.25, 0.12, 0.05), (0.08, 0.15, 0.07), (0.45, 0.4, 0.3), (0.1, 0.1, 0.18)])
            b = PR.test_tube(f"lab_bottle{row}_{k}", (X1 - 0.18, -0.2 + k * 0.2, 1.32 + row * 0.45), height=0.22, r=0.04, liquid=col)
    return dict(bench_z=0.9, bench=(0.0, 1.8))


# ----------------------------------------------------------------------------- the Mary Celeste's after cabin
def mc_cabin(skylight=True):
    """The captain's cabin as Flood's men found it: plank walls, the berth to port with drawers under it,
    a skylight overhead (grey-gold daylight), a table and the ship's clock on the bulkhead."""
    walls = PR.mat_wood("mcc_walls", "dark_wooden_planks", 1.4, tint=(0.72, 0.52, 0.36))
    floor = PR.mat_wood("mcc_floor", "weathered_planks", 0.9, tint=(0.78, 0.6, 0.44))
    beams = ship.paint("mcc_beams", (0.36, 0.3, 0.22), rough=0.5, grime=0.6, chips=0.3, scale=6)
    berthw = PR.mat_wood("mcc_berth", "brown_planks_05", 1.6, tint=(0.75, 0.5, 0.34))
    X0, X1, Y0, Y1, Hh = -1.8, 1.8, -1.5, 1.5, 2.02
    box_room("mcc", X0, X1, Y0, Y1, Hh, walls, floor, beams)
    x = X0 + 0.25
    while x < X1:
        if abs(x - 0.05) > 0.4:
            ship.box("mcc_beam", (x, 0, Hh - 0.07), (0.11, Y1 - Y0, 0.14), beams)
        x += 0.52
    # berth along the port side: board, mattress, drawers under it
    BX0, BX1, BY = -1.7, 0.4, 0.62
    ship.box("mcc_berth_base", ((BX0 + BX1) / 2, (BY + Y1) / 2, 0.22), (BX1 - BX0, Y1 - BY, 0.44), berthw)
    for k in range(3):
        xx = BX0 + 0.35 + k * 0.7
        ship.box("mcc_drawer", (xx, BY - 0.005, 0.22), (0.6, 0.02, 0.3), berthw, bevel=0.004)
    ship.box("mcc_board", ((BX0 + BX1) / 2, BY, 0.62), (BX1 - BX0, 0.04, 0.36), berthw, bevel=0.005)
    ship.box("mcc_mattress", ((BX0 + BX1) / 2, (BY + Y1) / 2 + 0.02, 0.52), (BX1 - BX0 - 0.06, Y1 - BY - 0.1, 0.14),
             ship.canvas("mcc_tick", wet=0.5, dirt=0.4, color=(0.5, 0.45, 0.36)))
    # the dark space under the berth, open at the foot (where the sword lay)
    ship.box("mcc_under", (BX1 + 0.01, (BY + Y1) / 2, 0.2), (0.02, Y1 - BY - 0.1, 0.3), crew.flat("mcc_dark", (0.01, 0.008, 0.006), 0.9))
    PR.table("mcc_table", (0.9, -0.7, 0.0), size=(0.9, 0.7, 0.74), mat=berthw)
    if skylight:
        _plane_light("mcc_sky", (0.05, -0.55, Hh - 0.16), (0.2, -0.2, 0.0), (0.6, 0.5), 90, (0.95, 0.9, 0.82), spread=60, visible=False)
    _plane_light("mcc_fill", (-1.2, -1.0, 1.4), (0.2, 0.3, 0.6), (1.2, 1.2), 14, (1.0, 0.8, 0.6))
    world((0.1, 0.09, 0.08), 0.15)
    air((0, 0, Hh / 2), (X1 - X0, Y1 - Y0, Hh), density=0.06)
    return dict(berth=(BX0, BX1, BY), under=(BX1, (BY + Y1) / 2, 0.06))


# ----------------------------------------------------------------------------- under the hull (Gibraltar harbour)
def underwater(depth=5.2):
    """Green-filtered daylight under the harbour: water volume, sand bed, light shafts from the surface."""
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, -depth / 2 - 0.01))
    v = bpy.context.active_object; v.name = "harbour_water"; v.scale = (80, 80, depth)
    m = bpy.data.materials.new("harbour_water"); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links
    N.remove(N["Principled BSDF"])
    vp = N.new("ShaderNodeVolumePrincipled"); vp.inputs['Color'].default_value = (0.35, 0.75, 0.6, 1)
    vp.inputs['Density'].default_value = 0.045; vp.inputs['Anisotropy'].default_value = 0.6
    vp.inputs['Absorption Color'].default_value = (0.25, 0.6, 0.5, 1)
    L.new(vp.outputs[0], N["Material Output"].inputs['Volume']); v.data.materials.append(m)
    # the surface seen from below: a rippled mirror
    bpy.ops.mesh.primitive_plane_add(size=80, location=(0, 0, -0.02))
    s = bpy.context.active_object; s.name = "surface_under"
    ms = bpy.data.materials.new("surface_under"); ms.use_nodes = True; p = ms.node_tree.nodes["Principled BSDF"]
    p.inputs['Transmission Weight'].default_value = 1.0; p.inputs['Roughness'].default_value = 0.05; p.inputs['IOR'].default_value = 1.33
    nz = ms.node_tree.nodes.new("ShaderNodeTexNoise"); nz.inputs['Scale'].default_value = 1.2; nz.inputs['Detail'].default_value = 6
    bm = ms.node_tree.nodes.new("ShaderNodeBump"); bm.inputs['Strength'].default_value = 0.4
    ms.node_tree.links.new(nz.outputs['Fac'], bm.inputs['Height']); ms.node_tree.links.new(bm.outputs['Normal'], p.inputs['Normal'])
    s.data.materials.append(ms)
    # sand bed with ripples
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=160, y_subdivisions=160, size=60, location=(0, 0, -depth))
    g = bpy.context.active_object; g.name = "seabed"
    for vv in g.data.vertices:
        x, y = vv.co.x, vv.co.y
        vv.co.z = 0.06 * math.sin(x * 2.1 + 0.6 * math.sin(y * 0.7)) + 0.25 * math.sin(x * 0.13 + y * 0.09)
    g.data.polygons.foreach_set("use_smooth", [True] * len(g.data.polygons))
    sand = crew.flat("sand", (0.42, 0.38, 0.28), rough=0.95)
    g.data.materials.append(sand)
    # sun shafts: sun lamp through the volume, with a caustic gobo
    sn = bpy.data.objects.new("sun_under", bpy.data.lights.new("sun_under", 'SUN')); bpy.context.scene.collection.objects.link(sn)
    sn.data.energy = 9.0; sn.data.color = (0.9, 1.0, 0.9); sn.data.angle = math.radians(1.5)
    sn.rotation_euler = (math.radians(20), math.radians(10), 0)
    w = world((0.02, 0.06, 0.05), 0.5)
    return dict(bed=-depth)
