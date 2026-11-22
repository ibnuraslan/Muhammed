"""Sets for the Antwerp Diamond Center film (Blender 5.2, metres, Z up).

vault_complex(state)  The vault two floors under the Diamond Center, with its corridor, grille and stairs.
    state: "day"   business hours: steel door open, grille closed, lights on, every box shut
           "night" steel door shut, lights off (sensors' LEDs, corridor night light)
           "wreck" Monday morning: door and grille open, lights on, 109 boxes forced, contents on the floor
           "heist" (part 2) as night but door open, lights on, boxes being forced
    Layout: vault room x in [-VX, VX], y in [0, VY]; the door wall is y in [-WALL, 0], door centred on x = 0;
    the corridor runs from the door toward -y (x in [-CX, CX]), grille across it at y = GRILLE_Y, stairs at its far end;
    the key cupboard room opens off the corridor at x = -CX.
Returns a dict of anchors (world points) for shots.
"""
import math, random, os
import numpy as np
import bpy, bmesh
from mathutils import Vector, Matrix, Euler
import ship as S
import ph

VX, VY, VZ = 3.0, 4.6, 2.45          # vault half-width, depth, height
WALL = 0.55                           # door wall thickness (reinforced concrete)
DW, DH = 1.0, 2.0                     # door opening
CX, CY, CZ = 1.05, 7.0, 2.6           # corridor half-width, length, height
GRILLE_Y = -2.1
NCOL, NROW, CW, RH, Z0 = 14, 5, 0.27, 0.38, 0.32     # side walls: 14 x 5 boxes each
BCOL, BROW, BW, BH, BZ0 = 5, 4, 0.5, 0.47, 0.32      # back wall: 5 x 4 larger boxes  -> 160 in all


# ----------------------------------------------------------------------------- materials
def _p(m):
    return m.node_tree.nodes["Principled BSDF"]


def flat(name, color, rough=0.5, metal=0.0, coat=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True; p = _p(m)
    p.inputs['Base Color'].default_value = (*color, 1); p.inputs['Roughness'].default_value = rough
    p.inputs['Metallic'].default_value = metal; p.inputs['Coat Weight'].default_value = coat
    return m


def emit(name, color, strength):
    m = bpy.data.materials.new(name); m.use_nodes = True; N = m.node_tree.nodes
    N.remove(N["Principled BSDF"]); e = N.new("ShaderNodeEmission")
    e.inputs['Color'].default_value = (*color, 1); e.inputs['Strength'].default_value = strength
    m.node_tree.links.new(e.outputs[0], N["Material Output"].inputs['Surface'])
    return m


def enamel(name, color, rough=0.45, var=0.18, scale=3.0, bump=0.05):
    """Painted surface: flat colour with soft tonal variation (no streaks), fine orange-peel bump."""
    m = bpy.data.materials.new(name); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links; p = _p(m)
    tc = N.new("ShaderNodeTexCoord")
    nz = N.new("ShaderNodeTexNoise"); nz.inputs['Scale'].default_value = scale; nz.inputs['Detail'].default_value = 4
    L.new(tc.outputs['Object'], nz.inputs['Vector'])
    mr = N.new("ShaderNodeMapRange"); mr.inputs['To Min'].default_value = 1 - var; mr.inputs['To Max'].default_value = 1 + var * 0.5
    L.new(nz.outputs['Fac'], mr.inputs['Value'])
    c = N.new("ShaderNodeRGB"); c.outputs[0].default_value = (*color, 1)
    mx = N.new("ShaderNodeVectorMath"); mx.operation = 'SCALE'; L.new(c.outputs[0], mx.inputs[0]); L.new(mr.outputs[0], mx.inputs['Scale'])
    L.new(mx.outputs[0], p.inputs['Base Color'])
    rr = N.new("ShaderNodeMapRange"); rr.inputs['To Min'].default_value = rough - 0.08; rr.inputs['To Max'].default_value = rough + 0.08
    L.new(nz.outputs['Fac'], rr.inputs['Value']); L.new(rr.outputs[0], p.inputs['Roughness'])
    if bump:
        fn = N.new("ShaderNodeTexNoise"); fn.inputs['Scale'].default_value = 400; L.new(tc.outputs['Object'], fn.inputs['Vector'])
        b = N.new("ShaderNodeBump"); b.inputs['Strength'].default_value = bump; b.inputs['Distance'].default_value = 0.0005
        L.new(fn.outputs['Fac'], b.inputs['Height']); L.new(b.outputs['Normal'], p.inputs['Normal'])
    return m


def steel_paint(name, color, rough=0.38, wear=0.25):
    """Stove-enamelled steel (box doors, vault door): satin paint, fine orange peel."""
    m = enamel(name, color, rough=rough, var=wear * 0.6, scale=6, bump=0.08)
    p = _p(m); p.inputs['Coat Weight'].default_value = 0.3; p.inputs['Coat Roughness'].default_value = 0.15
    p.inputs['Metallic'].default_value = 0.35
    return m


def brushed(name="brushed_steel", color=(0.55, 0.55, 0.56), rough=0.28):
    m = bpy.data.materials.new(name); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links; p = _p(m)
    tc = N.new("ShaderNodeTexCoord"); mp = N.new("ShaderNodeMapping"); mp.inputs['Scale'].default_value = (1, 1, 140)
    L.new(tc.outputs['Object'], mp.inputs['Vector'])
    nz = N.new("ShaderNodeTexNoise"); nz.inputs['Scale'].default_value = 30; nz.inputs['Detail'].default_value = 10
    L.new(mp.outputs[0], nz.inputs['Vector'])
    rr = N.new("ShaderNodeMapRange"); rr.inputs['To Min'].default_value = rough - 0.08; rr.inputs['To Max'].default_value = rough + 0.1
    L.new(nz.outputs['Fac'], rr.inputs['Value']); L.new(rr.outputs[0], p.inputs['Roughness'])
    p.inputs['Base Color'].default_value = (*color, 1); p.inputs['Metallic'].default_value = 1.0
    return m


def tex(aid, scale, tint=None, name=None):
    try:
        return ph.texture(aid, scale=scale, tint=tint, name=name or aid)
    except Exception as e:                      # offline fallback
        print("ph texture fallback", aid, e)
        return flat(name or aid, tint or (0.3, 0.3, 0.3), 0.8)


def paper_mat(name="paper", color=(0.78, 0.74, 0.64)):
    m = flat(name, color, rough=0.85); p = _p(m)
    p.inputs['Subsurface Weight'].default_value = 0.15; p.inputs['Subsurface Radius'].default_value = (0.3, 0.3, 0.3)
    return m


def gold(name="gold", color=(0.9, 0.62, 0.22)):
    return flat(name, color, rough=0.18, metal=1.0)


def gem(name="diamond"):
    m = bpy.data.materials.new(name); m.use_nodes = True; p = _p(m)
    p.inputs['Transmission Weight'].default_value = 1.0; p.inputs['IOR'].default_value = 2.42; p.inputs['Roughness'].default_value = 0.0
    p.inputs['Base Color'].default_value = (1, 1, 1, 1)
    return m


def velvet(name, color):
    m = flat(name, color, rough=0.9); p = _p(m); p.inputs['Sheen Weight'].default_value = 1.0
    p.inputs['Sheen Tint'].default_value = (*[min(1, c * 3 + 0.2) for c in color], 1)
    return m


# ----------------------------------------------------------------------------- small helpers
def box(name, c, s, mat=None, bevel=0.0, rot=(0, 0, 0)):
    return S.box(name, c, s, mat, rot=rot, bevel=bevel)


def light_area(name, loc, target, size, energy, color=(1, 0.9, 0.78), shape='RECTANGLE', size_y=None, spread=None):
    l = bpy.data.lights.new(name, 'AREA'); l.size = size; l.energy = energy; l.color = color
    if size_y:
        l.shape = shape; l.size_y = size_y
    if spread:
        l.spread = math.radians(spread)
    o = bpy.data.objects.new(name, l); bpy.context.scene.collection.objects.link(o); o.location = loc
    o.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    o.visible_camera = False
    return o


def light_point(name, loc, energy, color=(1, 0.8, 0.6), radius=0.05):
    l = bpy.data.lights.new(name, 'POINT'); l.energy = energy; l.color = color; l.shadow_soft_size = radius
    o = bpy.data.objects.new(name, l); bpy.context.scene.collection.objects.link(o); o.location = loc
    return o


def light_spot(name, loc, target, energy, angle=60, blend=0.6, color=(1, 0.85, 0.7), radius=0.05):
    l = bpy.data.lights.new(name, 'SPOT'); l.energy = energy; l.color = color; l.spot_size = math.radians(angle)
    l.spot_blend = blend; l.shadow_soft_size = radius
    o = bpy.data.objects.new(name, l); bpy.context.scene.collection.objects.link(o); o.location = loc
    o.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    return o


def world(color=(0.02, 0.02, 0.022), strength=1.0):
    w = bpy.data.worlds.new("W"); bpy.context.scene.world = w; w.use_nodes = True
    bg = w.node_tree.nodes["Background"]; bg.inputs[0].default_value = (*color, 1); bg.inputs[1].default_value = strength
    return w


def link_copy(src, name, loc, rot=(0, 0, 0), scale=None):
    o = src.copy(); o.name = name; bpy.context.scene.collection.objects.link(o)
    o.location = loc; o.rotation_euler = rot
    if scale is not None:
        o.scale = scale
    return o


def _bm_obj(name, bm, mat=None, smooth=False):
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    if smooth:
        me.polygons.foreach_set("use_smooth", np.ones(len(me.polygons), bool))
    o = bpy.data.objects.new(name, me)
    if mat:
        me.materials.append(mat)
    return o


def _hidden(o):
    """Template object: kept out of the scene (instances are linked copies)."""
    return o


# ----------------------------------------------------------------------------- safe-deposit box parts
def _door_mesh(w, h, name, mats):
    """A box door: plate (origin on its hinge edge, x along the wall 0..w, front face y = -t), two keyholes, a small
    number plate, a pull. mats = (paint, brass, black)."""
    t = 0.012
    bm = bmesh.new()
    r = bmesh.ops.create_cube(bm, size=1.0)
    for v in r["verts"]:
        v.co = Vector((v.co.x * (w - 0.006) + w / 2, v.co.y * t - t / 2, v.co.z * (h - 0.006)))
    for f in bm.faces:
        f.material_index = 0
    def cyl(x, z, rad, depth, mi, segs=16):
        r = bmesh.ops.create_cone(bm, cap_ends=True, segments=segs, radius1=rad, radius2=rad, depth=depth)
        for v in r["verts"]:
            v.co = Vector((v.co.x + x, -v.co.z - t - depth / 2 + 0.0005, v.co.y + z))
        for f in bm.faces[:]:
            pass
        for v in r["verts"]:
            for f in v.link_faces:
                f.material_index = mi
    cyl(w * 0.72, h * 0.12, 0.011, 0.004, 1)          # two lock escutcheons (renter's key + bank's key)
    cyl(w * 0.72, -h * 0.12, 0.011, 0.004, 1)
    cyl(w * 0.72, h * 0.12, 0.0035, 0.005, 2, 8)
    cyl(w * 0.72, -h * 0.12, 0.0035, 0.005, 2, 8)
    # number plate
    r = bmesh.ops.create_cube(bm, size=1.0)
    for v in r["verts"]:
        v.co = Vector((v.co.x * 0.05 + w * 0.3, v.co.y * 0.002 - t - 0.001, v.co.z * 0.025 + h * 0.3))
    for v in r["verts"]:
        for f in v.link_faces:
            f.material_index = 1
    o = _bm_obj(name, bm, None)
    for m in mats:
        o.data.materials.append(m)
    bv = o.modifiers.new("Bevel", "BEVEL"); bv.width = 0.0015; bv.segments = 2; bv.limit_method = 'ANGLE'
    return o


def _cavity_mesh(w, h, d, name, mat):
    """Open-fronted box (the cell behind a door): 5 faces, origin at the front-left-centre like the door."""
    bm = bmesh.new()
    vs = [(0, 0, -h / 2), (w, 0, -h / 2), (w, 0, h / 2), (0, 0, h / 2),
          (0, d, -h / 2), (w, d, -h / 2), (w, d, h / 2), (0, d, h / 2)]
    V = [bm.verts.new(v) for v in vs]
    for f in ((4, 5, 6, 7), (0, 4, 7, 3), (1, 2, 6, 5), (0, 1, 5, 4), (3, 7, 6, 2)):
        bm.faces.new([V[i] for i in f])
    o = _bm_obj(name, bm, mat)
    so = o.modifiers.new("Thick", "SOLIDIFY"); so.thickness = 0.003
    return o


def _tray_mesh(w, h, d, name, mat):
    """The inner steel tray of a box (lifted out by the renter, thrown down by the thieves): open top."""
    bm = bmesh.new()
    hh = h * 0.8
    vs = [(0, 0, 0), (w, 0, 0), (w, d, 0), (0, d, 0), (0, 0, hh), (w, 0, hh), (w, d, hh), (0, d, hh)]
    V = [bm.verts.new(v) for v in vs]
    for f in ((0, 1, 2, 3), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)):
        bm.faces.new([V[i] for i in f])
    o = _bm_obj(name, bm, mat)
    so = o.modifiers.new("Thick", "SOLIDIFY"); so.thickness = 0.0025
    bv = o.modifiers.new("Bevel", "BEVEL"); bv.width = 0.002; bv.segments = 2
    return o


def _paper_mesh(name, w, l, mat, bend=0.02, seed=0):
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=6, y_segments=8, size=0.5)
    rng = random.Random(seed)
    a, b = rng.uniform(-1, 1), rng.uniform(-1, 1)
    for v in bm.verts:
        x, y = v.co.x * w, v.co.y * l
        v.co = Vector((x, y, bend * (math.sin(3 * x / w + a) * 0.5 + (y / l) ** 2 * b + 0.5)))
    o = _bm_obj(name, bm, mat, smooth=True)
    so = o.modifiers.new("Thick", "SOLIDIFY"); so.thickness = 0.0006
    return o


# ----------------------------------------------------------------------------- the vault complex
def vault_complex(state="day", seed=7, forced=109, debris=1.0, extra_open=(), gate_angle=None, tray_out=0.18,
                  lights=None, door_angle=None, contacts="normal", taped=False):
    rng = random.Random(seed)
    A = {}
    col = bpy.context.scene.collection
    wreck = state == "wreck"; night = state == "night"; heist = state == "heist"
    lights_on = state in ("day", "wreck", "heist") if lights is None else lights
    door_open = state in ("day", "wreck", "heist") if door_angle is None else door_angle > 0.5
    # materials
    import detail as DT
    concrete = DT.wall_paint("vault_wall_paint", (0.4, 0.37, 0.32), rough=0.78)
    floor_m = tex("large_grey_tiles" if True else "terrazzo_tiles", 0.7, tint=(0.72, 0.64, 0.54), name="vault_floor")
    corr_floor = tex("concrete_floor_painted", 0.9, tint=(0.55, 0.48, 0.4), name="corr_floor")
    ceil_m = flat("ceiling", (0.32, 0.3, 0.27), 0.9)
    box_paint = brushed("box_steel", (0.62, 0.6, 0.56), rough=0.3)                       # brushed stainless box doors
    frame_paint = steel_paint("box_frame", (0.22, 0.2, 0.17), rough=0.45, wear=0.2)
    cavity_m = flat("cavity", (0.06, 0.055, 0.05), 0.6, metal=0.3)
    brass = gold("brass_plate", (0.62, 0.45, 0.2)); brass.node_tree.nodes["Principled BSDF"].inputs['Roughness'].default_value = 0.35
    black = flat("keyhole", (0.005, 0.005, 0.005), 0.5)
    vdoor_m = steel_paint("vault_door_paint", (0.18, 0.2, 0.2), rough=0.32, wear=0.15)
    steel = brushed()
    grille_m = steel_paint("grille_paint", (0.05, 0.05, 0.055), rough=0.45)
    A["mats"] = dict(box=box_paint, brass=brass, steel=steel, concrete=concrete, floor=floor_m)

    # ---- vault room shell
    D_ = 0.5                                     # the box banks are 0.5 m deep steel units set into the walls
    box("vault_floor_ext", (0, VY / 2, -0.05), (2 * VX + 2 * D_ + 0.4, VY + 2 * D_, 0.1), floor_m)
    for sg in (1, -1):
        box(f"vault_wall_x{sg}", (sg * (VX + D_ + 0.1), VY / 2, VZ / 2), (0.2, VY + 2 * D_, VZ), concrete)
        yb0 = (VY - NCOL * CW) / 2
        for (ya, yb) in ((0.0, yb0), (yb0 + NCOL * CW, VY)):       # end fillers beside each bank
            box("bank_end", (sg * (VX + D_ / 2), (ya + yb) / 2, VZ / 2), (D_, yb - ya, VZ), concrete)
        box("bank_top", (sg * (VX + D_ / 2), VY / 2, (Z0 + NROW * RH + VZ) / 2), (D_, VY, VZ - Z0 - NROW * RH), concrete)
        box("bank_bottom", (sg * (VX + D_ / 2 + 0.05), VY / 2, Z0 / 2), (D_, VY, Z0), concrete)
    box("vault_wall_back", (0, VY + D_ + 0.1, VZ / 2), (2 * VX + 2 * D_ + 0.4, 0.2, VZ), concrete)
    for sg in (1, -1):
        box("bank_back_side", (sg * (BCOL * BW / 2 + (VX - BCOL * BW / 2) / 2), VY + D_ / 2, VZ / 2), (VX - BCOL * BW / 2, D_, VZ), concrete)
    box("bank_back_top", (0, VY + D_ / 2, (BZ0 + BROW * BH + VZ) / 2), (BCOL * BW, D_, VZ - BZ0 - BROW * BH), concrete)
    box("bank_back_bottom", (0, VY + D_ / 2 + 0.05, BZ0 / 2), (BCOL * BW, D_, BZ0), concrete)
    box("vault_ceiling_ext", (0, VY / 2, VZ + 0.05), (2 * VX + 2 * D_ + 0.4, VY + 2 * D_, 0.1), ceil_m)
    # door wall with the opening, and its massive frame
    side_w = VX + 0.2 - DW / 2
    for sg in (1, -1):
        box(f"doorwall{sg}", (sg * (DW / 2 + side_w / 2), -WALL / 2, VZ / 2), (side_w, WALL, VZ + 0.2), concrete)
    box("doorwall_top", (0, -WALL / 2, (DH + VZ + 0.2) / 2), (DW, WALL, VZ + 0.2 - DH), concrete)
    fr = 0.12
    for sg in (1, -1):
        box(f"vframe{sg}", (sg * (DW / 2 + fr / 2 - 0.02), -WALL / 2, DH / 2), (fr, WALL + 0.06, DH + 0.1), steel, bevel=0.01)
    box("vframe_top", (0, -WALL / 2, DH + fr / 2 - 0.02), (DW + 2 * fr, WALL + 0.06, fr), steel, bevel=0.01)
    box("vframe_sill", (0, -WALL / 2, 0.01), (DW, WALL + 0.06, 0.02), steel)

    # ---- the boxes
    door_t = _door_mesh(CW, RH, "boxdoor_side", (box_paint, brass, black))
    door_b = _door_mesh(BW, BH, "boxdoor_back", (box_paint, brass, black))
    cav_t = _cavity_mesh(CW, RH, 0.45, "cavity_side", cavity_m)
    cav_b = _cavity_mesh(BW, BH, 0.45, "cavity_back", cavity_m)
    tray_t = _tray_mesh(CW - 0.04, RH - 0.06, 0.4, "tray_side", steel_paint("tray_paint", (0.3, 0.29, 0.26), rough=0.45))
    cells = []          # (wall, col, row, origin, yaw, w, h)
    y0 = (VY - NCOL * CW) / 2
    for sg in (1, -1):                                  # side walls: doors face into the room (toward x = 0)
        for c in range(NCOL):
            for r in range(NROW):
                z = Z0 + (r + 0.5) * RH
                if sg < 0:          # wall at x = -VX, door faces +x; local x (hinge->free) runs along +y
                    org = Vector((-VX + 0.005, y0 + c * CW, z)); yaw = math.pi / 2
                else:               # wall at x = +VX, door faces -x; local x runs along -y
                    org = Vector((VX - 0.005, y0 + (c + 1) * CW, z)); yaw = -math.pi / 2
                cells.append(("side", sg, c, r, org, yaw, CW, RH))
    xb0 = -BCOL * BW / 2
    for c in range(BCOL):
        for r in range(BROW):
            z = BZ0 + (r + 0.5) * BH
            org = Vector((xb0 + c * BW, VY - 0.005, z)); yaw = 0.0                # faces -y
            cells.append(("back", 0, c, r, org, yaw, BW, BH))
    A["n_boxes"] = len(cells)
    # front frames (the grid of stiles and rails round the doors)
    for sg in (1, -1):
        xw = sg * (VX - 0.012)
        for c in range(NCOL + 1):
            box("box_stile", (xw, y0 + c * CW, Z0 + NROW * RH / 2), (0.03, 0.014, NROW * RH + 0.02), frame_paint)
        for r in range(NROW + 1):
            box("box_rail", (xw, VY / 2, Z0 + r * RH), (0.03, NCOL * CW + 0.014, 0.014), frame_paint)
        box("box_plinth", (sg * (VX - 0.08), VY / 2, Z0 / 2), (0.16, NCOL * CW + 0.04, Z0), frame_paint)
        box("box_cornice", (sg * (VX - 0.06), VY / 2, Z0 + NROW * RH + 0.05), (0.12, NCOL * CW + 0.04, 0.1), frame_paint)
    for c in range(BCOL + 1):
        box("box_stile", (xb0 + c * BW, VY - 0.012, BZ0 + BROW * BH / 2), (0.014, 0.03, BROW * BH + 0.02), frame_paint)
    for r in range(BROW + 1):
        box("box_rail", (0, VY - 0.012, BZ0 + r * BH), (BCOL * BW + 0.014, 0.03, 0.014), frame_paint)
    box("box_plinth_back", (0, VY - 0.08, BZ0 / 2), (BCOL * BW + 0.04, 0.16, BZ0), frame_paint)
    box("box_cornice_back", (0, VY - 0.06, BZ0 + BROW * BH + 0.05), (BCOL * BW + 0.04, 0.12, 0.1), frame_paint)

    for sg in (1, -1):
        box("bank_back_dark", (sg * (VX + 0.47), VY / 2, Z0 + NROW * RH / 2), (0.02, NCOL * CW, NROW * RH), cavity_m)
    box("bank_back_dark_b", (0, VY + 0.47, BZ0 + BROW * BH / 2), (BCOL * BW, 0.02, BROW * BH), cavity_m)
    open_set = set()
    if wreck or heist:
        idx = list(range(len(cells))); rng.shuffle(idx)
        open_set = set(idx[:forced])
    A["open_cells"] = []; A["cells"] = cells
    num_m = flat("engraved", (0.02, 0.018, 0.015), 0.5)
    for (esg, ec, er) in extra_open:
        for i, cl in enumerate(cells):
            if cl[0] == "side" and cl[1] == esg and cl[2] == ec and cl[3] == er:
                open_set.add(i); A.setdefault("extra_cells", []).append(i)
    for i, (kind, sg, c, r, org, yaw, w, h) in enumerate(cells):
        R = Matrix.Rotation(yaw, 4, 'Z')
        cav = cav_t if kind == "side" else cav_b
        dr = door_t if kind == "side" else door_b
        is_open = i in open_set
        if is_open:
            o = cav.copy(); col.objects.link(o); o.matrix_world = Matrix.Translation(org) @ R @ Matrix.Translation((0, 0.0, 0))
            # forced door: wrenched round its hinge (pried at the lock side, often bent a little)
            ang = rng.uniform(70, 125)
            if i in A.get("extra_cells", []):
                ang = 165.0
                # the renter's tray drawn part-way out of its cell
                tr = tray_t.copy(); col.objects.link(tr)
                tr.matrix_world = Matrix.Translation(org) @ R @ Matrix.Translation((0.02, -tray_out, -h / 2 + 0.03))
                A["tray_front"] = tr.matrix_world @ Vector(((w - 0.04) / 2, 0.0, (h - 0.06) * 0.4))
                A["box_lock"] = Matrix.Translation(org) @ R @ Vector((w * 0.72, -0.02, h * 0.12))
            d = dr.copy(); col.objects.link(d)
            d.matrix_world = Matrix.Translation(org) @ R @ Matrix.Rotation(math.radians(-ang), 4, 'Z') @ \
                Matrix.Rotation(math.radians(rng.uniform(-4, 4)), 4, 'X')
            A["open_cells"].append((kind, org.copy(), yaw, w, h))
        else:
            d = dr.copy(); col.objects.link(d)
            d.matrix_world = Matrix.Translation(org) @ R
        DT.number_text(str(i + 1), d.matrix_world @ Matrix.Translation((w * 0.3, -0.0145, h * 0.3)), size=0.016, mat=num_m)
    for t in (door_t, door_b, cav_t, cav_b, tray_t):
        pass                                             # templates are not linked into the scene

    # ---- the vault door (leaf ~ 0.36 m thick, hinged on the corridor side at x = +DW/2)
    leaf = _vault_leaf(vdoor_m, steel, brass)
    hinge = Vector((DW / 2 + 0.03, -WALL - 0.02, 0))
    ang = 0.0
    if door_open:
        ang = 92.0 if door_angle is None else door_angle
    leaf.matrix_world = Matrix.Translation(hinge) @ Matrix.Rotation(math.radians(ang), 4, 'Z')
    A["vault_door"] = leaf; A["door_hinge"] = hinge
    bpy.context.view_layer.update()
    A["dial"] = leaf.matrix_world @ Vector((-DW / 2 - 0.03, -0.40, 1.4)); A["keylock"] = leaf.matrix_world @ Vector((-DW / 2 - 0.03, -0.37, 0.7))
    # hinge pillars
    for z in (0.35, 1.0, 1.65):
        S.cyl("vault_hinge", (hinge.x, hinge.y, z - 0.14), (hinge.x, hinge.y, z + 0.14), 0.05, mat=steel, verts=24)

    # ---- alarm sensors
    led_r = emit("led_red", (1.0, 0.05, 0.02), 30); led_g = emit("led_green", (0.1, 1.0, 0.2), 25)
    white_plastic = flat("sensor_plastic", (0.7, 0.68, 0.62), 0.45)
    # magnetic door contact: one half on the frame head, the other on the door leaf top
    mc1 = box("magcontact_frame", (-DW / 2 + 0.15, -WALL - 0.035, DH + 0.03), (0.09, 0.025, 0.02), white_plastic, bevel=0.003)
    A["mag_contact"] = Vector(mc1.location)
    if contacts == "bypassed":
        # the crew unscrewed both halves, kept them face to face (still 'closed') and fixed them on a small aluminium
        # plate taped to the wall beside the frame: the door can now open while the alarm reads 'shut'
        BX, BZ = -0.1, DH + 0.3                     # on the wall above the door head (room to stand under it)
        mc1.location = (BX, -WALL - 0.03, BZ + 0.01)
        alu = flat("alu_plate", (0.6, 0.6, 0.6), 0.35, metal=0.9); tape = flat("duct_tape", (0.32, 0.32, 0.33), 0.6)
        box("bypass_plate", (BX, -WALL - 0.008, BZ), (0.16, 0.006, 0.09), alu)
        box("magcontact_door", (BX, -WALL - 0.03, BZ - 0.016), (0.09, 0.025, 0.02), white_plastic, bevel=0.003)
        for dz in (0.03, -0.06):
            box("bypass_tape", (BX, -WALL - 0.006, BZ + dz), (0.2, 0.003, 0.035), tape)
        S.cyl("contact_wire", (BX + 0.08, -WALL - 0.02, BZ), (-DW / 2 + 0.1, -WALL - 0.02, DH + 0.03), 0.002,
              mat=flat("wire_white", (0.8, 0.8, 0.78), 0.5), verts=6)
        A["mag_contact"] = Vector(mc1.location)
    elif not door_open:
        box("magcontact_door", (-DW / 2 + 0.15, -WALL - 0.035, DH - 0.012), (0.09, 0.025, 0.02), white_plastic, bevel=0.003)
    # light detector on the vault ceiling (photocell), PIR in the far corners, seismic/heat plates on the walls
    ld = box("light_detector", (0, VY * 0.45, VZ - 0.03), (0.08, 0.08, 0.04), white_plastic, bevel=0.005)
    S.cyl("light_detector_eye", (0, VY * 0.45, VZ - 0.05), (0, VY * 0.45, VZ - 0.062), 0.016, mat=black, verts=20)
    A["light_detector"] = Vector((0, VY * 0.45, VZ - 0.05))
    A["pirs"] = []
    for sx in (-1, 1):
        p = Vector((sx * (VX - 0.15), VY - 0.15, VZ - 0.15))
        o = box("pir", p, (0.1, 0.1, 0.13), white_plastic, bevel=0.02, rot=(0, 0, math.radians(45 * sx)))
        b = box("pir_led", p + Vector((-sx * 0.04, -0.04, -0.04)), (0.008, 0.008, 0.008), led_r if not night else led_r)
        A["pirs"].append(p)
    if taped:
        tape = flat("duct_tape2", (0.3, 0.3, 0.31), 0.55)
        for dx in (-0.025, 0.0, 0.025):
            box("tape_strip", (dx, VY * 0.45, VZ - 0.064), (0.03, 0.12, 0.002), tape, rot=(0, 0, 0.1))
        bagm = bpy.data.materials.new("polythene"); bagm.use_nodes = True; bp = bagm.node_tree.nodes["Principled BSDF"]
        bp.inputs['Base Color'].default_value = (0.85, 0.85, 0.82, 1); bp.inputs['Roughness'].default_value = 0.35
        bp.inputs['Transmission Weight'].default_value = 0.6; bp.inputs['Alpha'].default_value = 0.9
        for p in A["pirs"]:
            bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=10, radius=0.1, location=p + Vector((0, 0, -0.02)))
            o = bpy.context.active_object; o.name = "pir_bag"; o.scale = (1.0, 1.0, 1.25); o.data.materials.append(bagm)
            d = o.modifiers.new("Crumple", "DISPLACE"); t = bpy.data.textures.new("crumple", "CLOUDS"); t.noise_scale = 0.05; d.texture = t; d.strength = 0.015
            bpy.ops.object.shade_smooth()
    A["seismic"] = []
    for p in ((-VX + 0.004, 0.25, 2.3), (VX - 0.004, 0.25, 2.3)):
        box("seismic_plate", p, (0.008, 0.12, 0.12), white_plastic, bevel=0.003); A["seismic"].append(Vector(p))

    # ---- corridor (from the door toward -y), grille, camera, stairs, key cupboard
    y_end = -WALL - CY
    box("corr_floor", (0, (-WALL + y_end) / 2, -0.05), (2 * CX + 0.2, CY + 0.2, 0.1), corr_floor)
    box("corr_ceil", (0, (-WALL + y_end) / 2, CZ + 0.05), (2 * CX + 0.2, CY + 0.2, 0.1), ceil_m)
    cw = DT.wall_paint("corr_wall_paint", (0.5, 0.48, 0.43), rough=0.8)
    # left wall with the cupboard-room door at y = -3.4
    KY = -3.6
    box("corr_wall_R", (CX + 0.1, (-WALL + y_end) / 2, CZ / 2), (0.2, CY + 0.2, CZ), cw)
    box("corr_wall_L_a", (-CX - 0.1, (-WALL + KY + 0.45) / 2, CZ / 2), (0.2, abs(-WALL - KY - 0.45), CZ), cw)
    box("corr_wall_L_b", (-CX - 0.1, (KY - 0.45 + y_end) / 2, CZ / 2), (0.2, abs(KY - 0.45 - y_end), CZ), cw)
    box("corr_wall_L_top", (-CX - 0.1, KY, (2.05 + CZ) / 2), (0.2, 0.9, CZ - 2.05), cw)
    box("corr_dado", (CX - 0.01, (-WALL + y_end) / 2, 0.55), (0.02, CY, 0.04), frame_paint)
    # cupboard room (key kept with its other half, hanging in a steel cabinet)
    box("cup_floor", (-CX - 1.2, KY, -0.05), (2.2, 2.2, 0.1), corr_floor)
    box("cup_ceil", (-CX - 1.2, KY, CZ + 0.05), (2.2, 2.2, 0.1), ceil_m)
    box("cup_wall_back", (-CX - 2.3, KY, CZ / 2), (0.2, 2.2, CZ), cw)
    for sg in (1, -1):
        box("cup_wall", (-CX - 1.2, KY + sg * 1.1, CZ / 2), (2.2, 0.2, CZ), cw)
    cab = box("key_cabinet", (-CX - 2.12, KY + 0.35, 1.5), (0.14, 0.5, 0.6), steel_paint("cab_paint", (0.25, 0.3, 0.26)), bevel=0.006)
    A["key_cabinet"] = Vector((-CX - 2.04, KY + 0.35, 1.5)); A["cupboard_door"] = Vector((-CX, KY, 1.0))
    # (the key itself is a prop placed by the shots: props.vault_key)
    # grille: steel bars across the corridor, a gate leaf with a lock box
    gy = GRILLE_Y
    box("grille_frame_top", (0, gy, 2.2), (2 * CX, 0.06, 0.06), grille_m)
    box("grille_frame_bot", (0, gy, 0.03), (2 * CX, 0.06, 0.06), grille_m)
    box("grille_head", (0, gy, (2.23 + CZ) / 2), (2 * CX, 0.08, CZ - 2.23), cw)
    if gate_angle is None:
        gate_angle = 100.0 if state == "wreck" else 0.0
    gate_w = 0.9
    x = -CX + 0.06
    while x < CX - 0.03:
        if not (-gate_w / 2 - 0.02 < x < gate_w / 2 + 0.02):
            S.cyl("grille_bar", (x, gy, 0.05), (x, gy, 2.18), 0.011, mat=grille_m, verts=12)
        x += 0.11
    for sx in (-gate_w / 2 - 0.03, gate_w / 2 + 0.03):
        box("grille_post", (sx, gy, 1.1), (0.04, 0.05, 2.15), grille_m)
    gate = bpy.data.objects.new("grille_gate", None); col.objects.link(gate)
    gparts = []
    for k in range(9):
        xx = 0.05 + k * 0.1
        gparts.append(S.cyl("grille_gate_bar", (xx, 0, 0.08), (xx, 0, 2.12), 0.011, mat=grille_m, verts=12))
    for zz in (0.1, 1.0, 2.1):
        gparts.append(box("grille_gate_rail", (gate_w / 2, 0, zz), (gate_w - 0.02, 0.03, 0.03), grille_m))
    lock = box("grille_lock", (gate_w - 0.06, -0.04, 1.05), (0.1, 0.05, 0.16), grille_m, bevel=0.005); gparts.append(lock)
    for o in gparts:
        o.parent = gate
    gate.matrix_world = Matrix.Translation((-gate_w / 2, gy, 0)) @ Matrix.Rotation(math.radians(-gate_angle), 4, 'Z')
    bpy.context.view_layer.update()
    A["gate_handle"] = gate.matrix_world @ Vector((gate_w - 0.1, -0.05, 1.05))
    A["gate_bar"] = gate.matrix_world @ Vector((0.65, 0.0, 1.3)); A["gate_bar_dir"] = gate.matrix_world.to_3x3() @ Vector((0, 0, 1))
    A["grille_y"] = gy; A["grille_lock"] = A["gate_handle"]
    # camera over the grille (looking at whoever stands outside it) + intercom panel
    try:
        root, ms = ph.model("security_camera_01", loc=(-CX + 0.15, gy - 0.1, CZ - 0.08), rot_z=math.radians(-60))
        root.scale = (1.0, 1.0, 1.0)
    except Exception as e:
        print("camera fallback", e)
        box("cctv", (-CX + 0.2, gy - 0.15, CZ - 0.2), (0.1, 0.25, 0.1), white_plastic)
    A["cctv"] = Vector((-CX + 0.15, gy - 0.1, CZ - 0.15))
    box("intercom", (CX - 0.005, gy - 0.35, 1.35), (0.02, 0.1, 0.16), steel, bevel=0.004)
    box("intercom_btn", (CX - 0.016, gy - 0.35, 1.32), (0.006, 0.03, 0.03), black)
    # stairs up at the far end (toward -y), rising
    for k in range(12):
        box("stair", (0, y_end - 0.15 - k * 0.28, 0.09 + k * 0.18), (2 * CX, 0.3, 0.18 + 0.0), corr_floor)
    box("stair_ceil", (0, y_end - 1.7, CZ + 1.2), (2 * CX + 0.2, 3.6, 0.1), ceil_m)
    for sg in (1, -1):
        box("stair_wall", (sg * (CX + 0.1), y_end - 1.7, CZ), (0.2, 3.6, 2 * CZ), cw)
    S.cyl("handrail", (CX - 0.05, y_end - 0.2, 0.95), (CX - 0.05, y_end - 3.4, 3.0), 0.02, mat=steel, verts=12)
    A["stairs_bottom"] = Vector((0, y_end - 0.1, 0)); A["corr_end"] = Vector((0, y_end, 0))

    # ---- dressing: dado, skirting, cable tray, vents, extinguisher, signs, CCTV domes, electrical box
    dado = DT.wall_paint("corr_dado_paint", (0.2, 0.22, 0.23), rough=0.55)
    for sx, ya, yb in ((CX - 0.004, -WALL, y_end), (-CX + 0.004, -WALL, KY + 0.45), (-CX + 0.004, KY - 0.45, y_end)):
        box("corr_dado_panel", (sx, (ya + yb) / 2, 0.55), (0.008, abs(yb - ya), 1.1), dado)
        DT.skirting((sx, ya, 0), (sx, yb, 0), (-1 if sx > 0 else 1, 0, 0))
    DT.cable_tray((CX - 0.25, -WALL - 0.2), (CX - 0.25, y_end + 0.2), CZ - 0.32, n_cables=6)
    DT.vent((-CX + 0.005, -1.2, 2.25), (1, 0, 0), 0.45, 0.22)
    DT.vent((CX - 0.005, -5.6, 2.25), (-1, 0, 0), 0.45, 0.22)
    DT.extinguisher((-CX + 0.005, -2.75, 0.12), (1, 0, 0))
    DT.sign((CX - 0.005, -1.75, 1.6), (-1, 0, 0), kind="notice", w=0.3, h=0.21)
    DT.sign((CX - 0.005, y_end + 0.6, 2.25), (-1, 0, 0), kind="exit", w=0.26, h=0.13)
    DT.cctv_dome((0.3, -4.4, CZ)); DT.cctv_dome((VX - 0.6, 0.6, VZ)); DT.cctv_dome((-VX + 0.6, VY - 0.6, VZ))
    DT.elec_box((CX - 0.005, -6.6, 1.3), (-1, 0, 0))
    for x in (-1.6, 1.6):
        DT.vent((x, VY / 2, VZ - 0.005), (0, 0, -1), 0.5, 0.3)
    for sg in (1, -1):
        DT.skirting((sg * (VX - 0.004), -0.0, 0), (sg * (VX - 0.004), y0, 0), (-sg, 0, 0))
    # ---- lights
    lum_on = emit("fluor_on", (1.0, 0.86, 0.66), 9.0)
    lum_off = flat("fluor_off", (0.6, 0.6, 0.58), 0.3)
    for (x, y) in [(-1.5, 1.2), (1.5, 1.2), (-1.5, 3.3), (1.5, 3.3)]:
        box("vault_fluor", (x, y, VZ - 0.025), (1.25, 0.18, 0.04), lum_on if lights_on else lum_off)
        if lights_on:
            light_area("vault_light", (x, y, VZ - 0.06), (x, y, 0), 1.2, 95, (1.0, 0.84, 0.64), size_y=0.18)
    for y in (-1.2, -3.0, -5.0, -6.8):
        box("corr_fluor", (0, y, CZ - 0.025), (0.18, 1.2, 0.04), lum_on if (lights_on or state == "wreck") else lum_off)
        if lights_on:
            light_area("corr_light", (0, y, CZ - 0.06), (0, y, 0), 0.18, 55, (1.0, 0.8, 0.58), size_y=1.2)
    if not lights_on:
        # night: a single caged night light by the stairs and a green exit sign; LEDs on the sensors
        light_point("night_light", (CX - 0.12, -WALL - CY + 0.3, 2.2), 40, (1.0, 0.6, 0.3), radius=0.04)
        light_point("door_night_light", (-CX + 0.15, -WALL - 0.9, 2.3), 12, (1.0, 0.62, 0.32), radius=0.05)
        # soft bounce of the crew's torches / the night light off the pale walls (keeps night shots readable)
        light_area("night_bounce_corr", (0, -3.0, CZ - 0.1), (0, -3.0, 0), 1.6, 35, (1.0, 0.75, 0.5), size_y=5.0)
        light_area("night_bounce_vault", (0, VY / 2, VZ - 0.1), (0, VY / 2, 0), 3.0, 25, (1.0, 0.72, 0.48), size_y=3.0)
        light_area("night_bounce_cup", (-CX - 1.2, -3.6, CZ - 0.1), (-CX - 1.2, -3.6, 0), 1.2, 15, (1.0, 0.75, 0.5))
        box("exit_sign", (0, -WALL - CY + 0.05, 2.35), (0.3, 0.02, 0.12), emit("exit_green", (0.1, 1.0, 0.35), 6))
        light_point("exit_glow", (0, -WALL - CY + 0.2, 2.3), 1.2, (0.2, 1.0, 0.4), radius=0.1)
    world((0.01, 0.01, 0.012), 0.5)

    # ---- the wreck: contents on the floor
    if wreck or (heist and debris > 0):
        _strew(A, rng, steel, tray_t, amount=debris)
    A["center"] = Vector((0, VY / 2, 0)); A["door_center"] = Vector((0, -WALL / 2, 1.0))
    A["state"] = state
    return A


def _vault_leaf(paint, steel, brass):
    """A Lips-style rectangular vault door leaf: 0.36 m of steel, origin on the hinge line (local x <= 0 is the leaf,
    local -y is the outer face when shut), a stepped edge, five locking bolts, handle, dial and key lock."""
    t = 0.36
    leaf = bpy.data.objects.new("vault_door", None); bpy.context.scene.collection.objects.link(leaf)
    def part(o):
        o.parent = leaf; return o
    body = part(box("vault_leaf", (-DW / 2 - 0.03, -t / 2 + 0.02, DH / 2), (DW + 0.04, t, DH + 0.02), paint, bevel=0.02))
    part(box("vault_leaf_face", (-DW / 2 - 0.03, -t + 0.012, DH / 2), (DW - 0.08, 0.03, DH - 0.12), paint, bevel=0.012))
    # bolts on the free edge (lock side)
    for z in (0.35, 0.68, 1.0, 1.32, 1.65):
        part(S.cyl("vault_bolt", (-DW - 0.05, -t / 2 + 0.02, z), (-DW - 0.13, -t / 2 + 0.02, z), 0.032, mat=steel, verts=24))
    # inner face: bolt-work cover plate
    part(box("vault_cover", (-DW / 2 - 0.03, 0.035, DH / 2), (DW - 0.16, 0.012, DH - 0.4), steel, bevel=0.004))
    # outer face: three-spoke handle, combination dial, key lock
    hx, hz = -DW / 2 - 0.03, 1.0
    part(S.cyl("vault_hub", (hx, -t, hz), (hx, -t - 0.06, hz), 0.045, mat=steel, verts=32))
    for k in range(3):
        a = math.radians(90 + 120 * k)
        part(S.cyl("vault_spoke", (hx, -t - 0.05, hz), (hx + 0.2 * math.cos(a), -t - 0.05, hz + 0.2 * math.sin(a)), 0.012, mat=steel, verts=12))
    dx, dz = hx, 1.4
    part(S.cyl("vault_dial_ring", (dx, -t, dz), (dx, -t - 0.012, dz), 0.075, mat=steel, verts=48))
    part(S.cyl("vault_dial", (dx, -t - 0.012, dz), (dx, -t - 0.04, dz), 0.055, mat=flat("dial_black", (0.02, 0.02, 0.02), 0.3), verts=48))
    part(S.cyl("vault_dial_knob", (dx, -t - 0.04, dz), (dx, -t - 0.07, dz), 0.022, mat=steel, verts=24))
    white = flat("dial_marks", (0.85, 0.83, 0.78), 0.4)
    for k in range(100):                      # 0-99 graduations, every tenth long
        a_ = 2 * math.pi * k / 100; L_ = 0.012 if k % 10 == 0 else 0.006
        r0 = 0.053 - L_
        part(box("dial_tick", (dx + math.sin(a_) * (r0 + L_ / 2), -t - 0.0405, dz + math.cos(a_) * (r0 + L_ / 2)),
                 (0.0012 if k % 10 else 0.002, 0.0008, L_), white, rot=(0, -a_, 0)))
    part(box("dial_index", (dx, -t - 0.0125, dz + 0.068), (0.004, 0.002, 0.012), flat("index_red", (0.6, 0.03, 0.02), 0.4)))
    part(S.cyl("vault_keylock", (dx, -t, 0.7), (dx, -t - 0.01, 0.7), 0.03, mat=brass, verts=32))
    part(box("vault_keyslot", (dx, -t - 0.012, 0.7), (0.006, 0.004, 0.03), flat("slot", (0, 0, 0), 0.5)))
    return leaf


def clear_floor(points, radius=0.6):
    """Remove floor debris (papers, trays, boxes, rings, gems) within `radius` of each point (x, y): nobody kneels
    or stands on top of a paper in our shots, so no prop ever passes through a person."""
    pts = [Vector((p[0], p[1], 0)) for p in points]
    for o in list(bpy.data.objects):
        if not o.name.startswith(("tpl_", "tray_side", "Torus", "Icosphere")) or o.location.z > 0.4:
            continue
        q = Vector((o.location.x, o.location.y, 0))
        if any((q - p).length < radius for p in pts):
            bpy.data.objects.remove(o)


def _strew(A, rng, steel, tray_t, amount=1.0):
    """Monday morning: trays thrown down, papers, jewellery boxes, diamond papers, envelopes and a few gems on the
    floor, mostly along the box walls and in front of the forced doors."""
    col = bpy.context.scene.collection
    paper = paper_mat(); enve = paper_mat("envelope", (0.62, 0.48, 0.3)); white = paper_mat("diamond_paper", (0.86, 0.85, 0.8))
    blue = paper_mat("blue_doc", (0.3, 0.38, 0.55)); pink = paper_mat("pink_doc", (0.75, 0.45, 0.42))
    vel = [velvet("velvet_red", (0.35, 0.02, 0.03)), velvet("velvet_blue", (0.02, 0.05, 0.25)), velvet("velvet_green", (0.02, 0.15, 0.06))]
    au = gold(); dia = gem()
    papers = [_paper_mesh(f"tpl_paper{k}", 0.21, 0.297, m, 0.02, k) for k, m in enumerate((paper, paper, blue, pink))]
    envs = [_paper_mesh("tpl_env", 0.23, 0.16, enve, 0.01, 9)]
    dpap = [_paper_mesh("tpl_dpap", 0.06, 0.1, white, 0.004, 3)]
    # jewellery box (lid flipped open), ring, bracelet, gem
    jb = box("tpl_jbox", (0, 0, 0.02), (0.06, 0.06, 0.04), vel[0], bevel=0.008); col.objects.unlink(jb)
    bpy.ops.mesh.primitive_torus_add(major_radius=0.009, minor_radius=0.0018); ring = bpy.context.active_object; ring.data.materials.append(au); col.objects.unlink(ring)
    bpy.ops.mesh.primitive_torus_add(major_radius=0.035, minor_radius=0.004); brace = bpy.context.active_object; brace.data.materials.append(au); col.objects.unlink(brace)
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=0.004); g = bpy.context.active_object; g.data.materials.append(dia); col.objects.unlink(g)
    n = 0
    def drop(tpl, p, yaw, tilt=0.0, z=0.0, scale=None):
        nonlocal n
        o = tpl.copy(); col.objects.link(o); n += 1
        o.location = (p.x, p.y, z); o.rotation_euler = (tilt, rng.uniform(-0.15, 0.15), yaw)
        if scale:
            o.scale = scale
        return o
    def floor_pt(near_wall=True):
        if near_wall and rng.random() < 0.8:
            side = rng.choice((-1, 1, 0))
            if side:
                return Vector((side * rng.uniform(VX - 1.3, VX - 0.2), rng.uniform(0.3, VY - 0.3), 0))
            return Vector((rng.uniform(-1.3, 1.3), rng.uniform(VY - 1.2, VY - 0.25), 0))
        return Vector((rng.uniform(-VX + 0.3, VX - 0.3), rng.uniform(0.4, VY - 0.3), 0))
    k = amount
    stack = {}
    def zstack(p, h):
        key = (round(p.x * 4), round(p.y * 4)); z = stack.get(key, 0.0); stack[key] = z + h
        return z
    # trays: upside down or on their side, near the walls
    for i in range(int(46 * k)):
        p = floor_pt(); o = tray_t.copy(); col.objects.link(o); n += 1
        flip = rng.random()
        if flip < 0.5:
            o.location = (p.x, p.y, 0.0); o.rotation_euler = (0, 0, rng.uniform(0, 6.28))
        else:      # upside down
            o.location = (p.x, p.y, 0.305 * 0.8 * (RH - 0.06) / 0.38 + 0.0); o.rotation_euler = (math.pi, 0, rng.uniform(0, 6.28))
            o.location.z = (RH - 0.06) * 0.8 + 0.003
        zstack(p, 0.0)
    for i in range(int(260 * k)):
        p = floor_pt(rng.random() < 0.85)
        drop(rng.choice(papers), p, rng.uniform(0, 6.28), z=0.001 + zstack(p, 0.0009) )
    for i in range(int(70 * k)):
        p = floor_pt(); drop(envs[0], p, rng.uniform(0, 6.28), z=0.001 + zstack(p, 0.0009))
    for i in range(int(120 * k)):
        p = floor_pt(); drop(dpap[0], p, rng.uniform(0, 6.28), z=0.0012 + zstack(p, 0.0009))
    for i in range(int(40 * k)):
        p = floor_pt(); o = drop(jb, p, rng.uniform(0, 6.28), z=0.0, tilt=0.0)
        o.material_slots[0].link = 'OBJECT'; o.material_slots[0].material = vel[i % 3]
    for i in range(int(30 * k)):
        p = floor_pt(); drop(ring, p, rng.uniform(0, 6.28), z=0.0018, tilt=0.0)
    for i in range(int(12 * k)):
        p = floor_pt(); drop(brace, p, rng.uniform(0, 6.28), z=0.004)
    for i in range(int(60 * k)):
        p = floor_pt(); drop(g, p, rng.uniform(0, 6.28), z=0.003)
    A["debris"] = n
