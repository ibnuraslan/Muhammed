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
    """Grey plastic pipe from a to b with rows of small drilled holes (light pricks through: holes are alpha cut)."""
    m = bpy.data.materials.new(name + "M"); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; p = N["Principled BSDF"]
    p.inputs['Base Color'].default_value = (0.42, 0.42, 0.4, 1); p.inputs['Roughness'].default_value = 0.45
    tc = N.new("ShaderNodeTexCoord"); sep = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs['Generated'], sep.inputs[0])
    # holes on a grid in (along, around)
    vor = N.new("ShaderNodeTexVoronoi"); vor.inputs['Scale'].default_value = 60; vor.feature = 'F1'
    mp = N.new("ShaderNodeMapping"); mp.inputs['Scale'].default_value = (1.0, 1.0, 4.0); L.new(tc.outputs['Object'], mp.inputs['Vector'])
    L.new(mp.outputs[0], vor.inputs['Vector'])
    hole = N.new("ShaderNodeMath"); hole.operation = 'GREATER_THAN'; hole.inputs[1].default_value = 0.14; L.new(vor.outputs['Distance'], hole.inputs[0])
    L.new(hole.outputs[0], p.inputs['Alpha'])
    a = Vector(a); b = Vector(b); d = b - a
    o = cyl(name, (a + b) / 2, r, d.length, m, 24)
    o.rotation_euler = d.to_track_quat('Z', 'Y').to_euler()
    sol = o.modifiers.new("s", 'SOLIDIFY'); sol.thickness = 0.003
    return o


def build_box(c):
    ply = mat("pine"); dark = pbr("BoxInside", (0.22, 0.16, 0.1), 0.8)
    x0, x1, y0, y1 = -W / 2, W / 2, -D / 2, D / 2
    parts = [box("Pallet", (0, 0, Z0 / 2), (W + 0.25, D + 0.25, Z0), mat("rawwood")),
             box("Floor", (0, 0, Z0 + T / 2), (W, D, T), ply),
             box("Back", (0, y1 - T / 2, Z0 + H / 2), (W, T, H), ply),
             box("SideL", (x0 + T / 2, 0, Z0 + H / 2), (T, D, H), ply),
             box("SideR", (x1 - T / 2, 0, Z0 + H / 2), (T, D, H), ply),
             box("Top", (0, 0, Z0 + H - T / 2), (W, D, T), ply)]
    # the front panel stands beside the box, leaning on the pallet (the cutaway)
    fp = box("FrontPanel", (x1 + 0.45, y0 - 0.25, Z0 + H / 2 - 0.05), (W, T, H), ply, rot=(math.radians(-6), 0, math.radians(-35)))
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
    bl = bpy.data.lights.new("BulbL", 'POINT'); bl.energy = 6; bl.color = (1.0, 0.72, 0.42); bl.shadow_soft_size = 0.02
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
    # on the shelf: portable radio, water and orange soda bottles, chocolate, books
    rad, dial = rj.portable_radio("BoxRadio")
    rad.location = (-0.17, D / 2 - 0.14, sh_z); rad.scale = (0.8, 0.8, 0.8)
    c["radio_dial"] = dial; c["radio"] = rad
    clear = pbr("BottleGlass", (0.75, 0.8, 0.78), 0.05, 0.0, **{'Transmission Weight': 1.0, 'IOR': 1.45})
    orange = pbr("Soda", (0.7, 0.25, 0.02), 0.05, 0.0, **{'Transmission Weight': 0.8, 'IOR': 1.45})
    for k, (x, m) in enumerate(((0.04, clear), (0.1, clear), (0.16, orange), (0.22, orange))):
        cyl("Bottle", (x, D / 2 - 0.12, sh_z + 0.12), 0.03, 0.24, m, 20)
        cyl("BottleNeck", (x, D / 2 - 0.12, sh_z + 0.27), 0.012, 0.06, m, 12)
        cyl("BottleCap", (x, D / 2 - 0.12, sh_z + 0.305), 0.013, 0.012, pbr("Cap", (0.6, 0.6, 0.6), 0.3, 1.0), 12)
    choc = pbr("ChocWrap", (0.30, 0.10, 0.30), 0.35, 0.3)
    for k in range(3):
        box("Choc", (-0.02 + 0.0, D / 2 - 0.18, sh_z + 0.008 + k * 0.012), (0.17, 0.08, 0.011), choc, rot=(0, 0, 0.08 * k))
    for k, col in enumerate(((0.25, 0.08, 0.05), (0.1, 0.18, 0.3), (0.32, 0.28, 0.12))):
        box("Book", (W / 2 - T - 0.08, D / 2 - 0.13 - 0.0, sh_z + 0.1 + 0.0), (0.03 if True else 0.02, 0.16, 0.2), pbr(f"BookC{k}", col, 0.7)).location.x -= k * 0.035
    # water canister and a blanket on the seat
    box("Blanket", (0.0, D / 2 - 0.2, Z0 + 0.47), (W - 2 * T - 0.1, 0.32, 0.03), rj.fabric("Blanket", (0.25, 0.2, 0.15), 0.95, 0.4) if hasattr(rj, "fabric") else felt)
    # evidence tags (blank, no text) hanging off the battery and the radio
    tag = pbr("Tag", (0.75, 0.7, 0.55), 0.8)
    box("TagA", (batt.x + 0.1, batt.y - 0.1, 0.26), (0.06, 0.003, 0.1), tag, rot=(0, 0, 0.3))


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
    sp = bpy.data.lights.new("WorkL", 'SPOT'); sp.energy = 600; sp.spot_size = math.radians(70); sp.spot_blend = 0.5; sp.color = (1.0, 0.86, 0.7)
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
    try:
        rj.model_fit("steel_frame_shelves_01", (5.5, 4.5, 0), rot_z=math.pi, height=2.2)
        rj.model_fit("steel_frame_shelves_02", (5.5, 2.0, 0), rot_z=-math.pi / 2, height=2.2)
    except Exception:
        pass
    haze((0, 0, 2.5), (13.5, 11.5, 5.0), density=0.012, color=(0.85, 0.85, 0.85), anis=0.5)


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
    rj.finish_scene()
    return c


def smoke(c):
    """A thin wisp of test smoke at the low pipe's mouth (volume, frame-driven drift): it barely moves."""
    o = box("Smoke", (W / 2 - T - 0.04, -D / 2 - 0.05, Z0 + 0.62), (0.12, 0.16, 0.12), None)
    m = bpy.data.materials.new("SmokeVol"); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; N.clear()
    out = N.new("ShaderNodeOutputMaterial"); vol = N.new("ShaderNodeVolumePrincipled")
    tc = N.new("ShaderNodeTexCoord"); nz = N.new("ShaderNodeTexNoise"); nz.noise_dimensions = '4D'; nz.inputs['Scale'].default_value = 9
    L.new(tc.outputs['Object'], nz.inputs['Vector']); rj.driven(nz.inputs['W'], "default_value", "frame * 0.01")
    gr = N.new("ShaderNodeTexGradient"); gr.gradient_type = 'SPHERICAL'; L.new(tc.outputs['Object'], gr.inputs['Vector'])
    mul = N.new("ShaderNodeMath"); mul.operation = 'MULTIPLY'; L.new(nz.outputs['Fac'], mul.inputs[0]); L.new(gr.outputs['Fac'], mul.inputs[1])
    mr = N.new("ShaderNodeMapRange"); mr.inputs['From Min'].default_value = 0.15; mr.inputs['From Max'].default_value = 0.5; mr.inputs['To Max'].default_value = 6.0
    L.new(mul.outputs[0], mr.inputs['Value']); L.new(mr.outputs[0], vol.inputs['Density'])
    vol.inputs['Color'].default_value = (0.85, 0.85, 0.85, 1)
    L.new(vol.outputs[0], out.inputs['Volume']); o.data.materials.append(m)
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
        stand(h, (W / 2 + 0.25, -D / 2 - 0.7, 0.0), math.radians(160))
        mouth = Vector((W / 2 - T - 0.04, -D / 2 - 0.02, Z0 + 0.62))
        fwd = forward(h); right = fwd.cross(Vector((0, 0, 1))).normalized()
        rj.rjp.bend_to(h, mouth, frac=0.8, max_deg=25)
        reach(h, "R", mouth + Vector((0.02, -0.16, -0.02)), Vector((0, 0, -1)) + right * 0.5, (mouth - h.bone_head("upperarm01.R")).normalized())
        tube = c["smoke_tube"]; w_ = h.bone_tail("wrist.R")
        aim = (mouth - w_).normalized()
        tube.matrix_world = Matrix.Translation(w_) @ aim.to_track_quat('Z', 'Y').to_matrix().to_4x4()
        c["smoke"].location = mouth + Vector((0.0, -0.04 - 0.01 * sec, 0.004 * sec))
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
    a = Vector((0.15, -1.2, 2.6)); b = Vector((0.1, -0.85, 1.25))
    return (a.lerp(b, e), Vector((0, 0.15, Z0 + 0.7)), 30)


def cam_cable(c, t):
    e = ease(t)
    p0 = c["cable_pts"]
    a = Vector((W / 2 + 0.25, -0.75, 1.3)); b = Vector((W / 2 + 0.95, -0.45, 0.45))
    tgt = Vector((W / 2 + 0.05, 0.15, Z0 + H - 0.1)).lerp(Vector(c["battery"]) + Vector((0, 0, 0.15)), e)
    return (a.lerp(b, e), tgt, 40)


def cam_shelf(c, t):
    e = ease(t)
    a = Vector((-0.22, -0.55, Z0 + 1.2)); b = Vector((0.2, -0.5, Z0 + 1.17))
    return (a.lerp(b, e), Vector((-0.05 + 0.2 * e, D / 2 - 0.14, Z0 + 1.1)), 40)


def cam_radio(c, t):
    e = ease(t)
    a = Vector((-0.95, -1.25, 1.5)); b = Vector((-0.85, -1.1, 1.45))
    return (a.lerp(b, e), Vector((-0.12, D / 2 - 0.14, Z0 + 1.08)), 38)


def cam_pipe(c, t):
    e = ease(t)
    x = -W / 2 + T + 0.04; z = Z0 + H - 0.2
    a = Vector((x + 0.16, -D / 2 - 0.05, z - 0.08)); b = Vector((x + 0.17, D / 2 - 0.12, z - 0.07))
    return (a.lerp(b, e), Vector((x, 0.1 + 0.2 * e, z)), 35)


def cam_smoke(c, t):
    e = ease(t)
    a = Vector((W / 2 + 0.9, -1.5, 1.1)); b = Vector((W / 2 + 0.75, -1.3, 1.0))
    return (a.lerp(b, e), Vector((W / 2 - 0.05, -D / 2 - 0.1, Z0 + 0.62)), 40)


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
VARIANT_FOR = {"radio": "hall|tech", "smoke": "hall+smoke|tech", "experts": "hall|expert,expert2", "door": "hall|expert,expert2"}

_build = build


def build(variant=None):                      # noqa: F811
    c = _build(variant)
    if "smoke" in (variant or ""):
        c["smoke_tube"] = cyl("SmokeTube", (0, 0, 0), 0.012, 0.14, pbr("SmokeTubeM", (0.75, 0.75, 0.72), 0.4), 12)
    # the radio dial glows once the technician turns it on (frame-driven)
    if "tech" in (variant or "") and "smoke" not in (variant or ""):
        rj.emission_driven(c["radio_dial"], "1.6 * min(1, max(0, (frame - 30) / 6))")
    return c
