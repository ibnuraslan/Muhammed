"""STAIRS: the boutique's service stairwell. Painted concrete switchback stairs, a steel handrail, a caged bulb.
  powder (ch1 3A): looking down the stairwell, white extinguisher powder billows and drifts as figures hurry out of frame
  settle (ch1 3B): after they are gone the powder settles over the steps; a dropped extinguisher rolls to a stop
"""
import math
import numpy as np
import bpy
from mathutils import Vector
from kit import *
import dd
from dd import walk_to, place, face_to
from sc_boutique import painter

EXPOSURE = 1.0
DUR = {"powder": 9.0, "settle": 9.0}
VARIANT_FOR = {"settle": "settle"}
FH = 3.0            # floor height
NSTEP = 10          # steps per half flight
RUN = 0.3
L = NSTEP * RUN     # flight length (y 0.1 .. L + 0.1)
W = 1.2             # flight width


def stairwell(B, wall, step_m, nose):
    """Two half flights per floor between landings; well from x=-1.3..1.3, y=0..5."""
    rise = FH / 2 / NSTEP; run = RUN
    for f in range(-1, 2):
        z0 = f * FH
        # landings: low at y=0 (floor level) and mid at y=5 (half level)
        B.box((0, -0.6, z0 - 0.1), (2.6, 1.2, 0.2), step_m)
        B.box((0, L + 0.7, z0 + FH / 2 - 0.1), (2.6, 1.2, 0.2), step_m)
        for k in range(NSTEP):
            # up flight on the right (x>0) from y=0 to y=5; down flight on the left back to y=0
            B.box((0.65, k * run + run / 2 + 0.1, z0 + (k + 1) * rise - rise / 2), (W, run, rise), step_m)
            B.box((0.65, k * run + run + 0.08, z0 + (k + 1) * rise - 0.01), (W, 0.03, 0.02), nose)
            B.box((-0.65, L + 0.2 - (k * run + run / 2 + 0.1), z0 + FH / 2 + (k + 1) * rise - rise / 2), (W, run, rise), step_m)
            B.box((-0.65, L + 0.2 - (k * run + run + 0.08), z0 + FH / 2 + (k + 1) * rise - 0.01), (W, 0.03, 0.02), nose)
        # soffits under the flights
        ln = math.hypot(NSTEP * run, FH / 2)
        ang = math.atan2(FH / 2, NSTEP * run)
        B.box((0.65, NSTEP * run / 2 + 0.1, z0 + FH / 4 - 0.15), (W, ln, 0.15), wall, rot=(ang, 0, 0))
        B.box((-0.65, L + 0.2 - NSTEP * run / 2 - 0.1, z0 + FH * 0.75 - 0.15), (W, ln, 0.15), wall, rot=(-ang, 0, 0))
    B.box((-1.4, L / 2, 0.5), (0.2, L + 3.0, 3 * FH), wall); B.box((1.4, L / 2, 0.5), (0.2, L + 3.0, 3 * FH), wall)
    B.box((0, L + 1.4, 0.5), (2.6, 0.2, 3 * FH), wall); B.box((0, -1.3, 0.5), (2.6, 0.2, 3 * FH), wall)


def powder_volume(name, loc, size, expr_density, drift=(0.0, 0.0, -0.06), scale=3.0):
    """White extinguisher powder: a box volume, density from 4D noise whose W and offset run on frame drivers."""
    o = box(name, loc, size)
    m = bpy.data.materials.new(name); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; N.clear()
    out = N.new("ShaderNodeOutputMaterial"); vol = N.new("ShaderNodeVolumePrincipled")
    vol.inputs['Color'].default_value = (1.0, 1.0, 1.0, 1); vol.inputs['Anisotropy'].default_value = 0.35
    tc = N.new("ShaderNodeTexCoord"); t = dd.frame_value(N, "frame / 24.0", "T")
    off = N.new("ShaderNodeCombineXYZ")
    for i, ax in enumerate("XYZ"):
        mm = N.new("ShaderNodeMath"); mm.operation = 'MULTIPLY'; mm.inputs[1].default_value = -drift[i]
        L.new(t.outputs[0], mm.inputs[0]); L.new(mm.outputs[0], off.inputs[ax])
    add = N.new("ShaderNodeVectorMath"); add.operation = 'ADD'; L.new(tc.outputs['Object'], add.inputs[0]); L.new(off.outputs[0], add.inputs[1])
    nz = N.new("ShaderNodeTexNoise"); nz.noise_dimensions = '4D'; nz.inputs['Scale'].default_value = scale; nz.inputs['Detail'].default_value = 5
    nz.inputs['Roughness'].default_value = 0.55
    tw = N.new("ShaderNodeMath"); tw.operation = 'MULTIPLY'; tw.inputs[1].default_value = 0.25; L.new(t.outputs[0], tw.inputs[0])
    L.new(add.outputs[0], nz.inputs['Vector']); L.new(tw.outputs[0], nz.inputs['W'])
    mr = N.new("ShaderNodeMapRange"); mr.inputs['From Min'].default_value = 0.42; mr.inputs['From Max'].default_value = 0.72
    mr.inputs['To Max'].default_value = 3.0; L.new(nz.outputs['Fac'], mr.inputs['Value'])
    # soft edges toward the box faces (generated coords 0..1)
    edge = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs['Generated'], edge.inputs[0])
    fall = None
    for ax in "XYZ":
        a = N.new("ShaderNodeMath"); a.operation = 'PINGPONG'; a.inputs[1].default_value = 0.5; L.new(edge.outputs[ax], a.inputs[0])
        r = N.new("ShaderNodeMapRange"); r.inputs['From Max'].default_value = 0.2; L.new(a.outputs[0], r.inputs['Value'])
        if fall is None:
            fall = r
        else:
            mm = N.new("ShaderNodeMath"); mm.operation = 'MULTIPLY'; L.new(fall.outputs[0], mm.inputs[0]); L.new(r.outputs[0], mm.inputs[1]); fall = mm
    dens = dd.frame_value(N, expr_density, "Density")
    m1 = N.new("ShaderNodeMath"); m1.operation = 'MULTIPLY'; L.new(mr.outputs[0], m1.inputs[0]); L.new(fall.outputs[0], m1.inputs[1])
    m2 = N.new("ShaderNodeMath"); m2.operation = 'MULTIPLY'; L.new(m1.outputs[0], m2.inputs[0]); L.new(dens.outputs[0], m2.inputs[1])
    L.new(m2.outputs[0], vol.inputs['Density']); L.new(vol.outputs[0], out.inputs['Volume'])
    o.data.materials.append(m)
    return o


def dusted(m, expr):
    """Settle a white powder layer on upward faces, its amount on a frame driver."""
    N = m.node_tree.nodes; L = m.node_tree.links; p = N["Principled BSDF"]
    geo = N.new("ShaderNodeNewGeometry"); sep = N.new("ShaderNodeSeparateXYZ"); L.new(geo.outputs['Normal'], sep.inputs[0])
    up = N.new("ShaderNodeMapRange"); up.inputs['From Min'].default_value = 0.6; up.inputs['From Max'].default_value = 0.95
    L.new(sep.outputs['Z'], up.inputs['Value'])
    nz = N.new("ShaderNodeTexNoise"); nz.inputs['Scale'].default_value = 18
    amt = dd.frame_value(N, expr, "Dust")
    a = N.new("ShaderNodeMath"); a.operation = 'MULTIPLY'; L.new(up.outputs[0], a.inputs[0]); L.new(amt.outputs[0], a.inputs[1])
    b = N.new("ShaderNodeMath"); b.operation = 'MULTIPLY'; L.new(a.outputs[0], b.inputs[0]); L.new(nz.outputs['Fac'], b.inputs[1])
    c2 = N.new("ShaderNodeMath"); c2.operation = 'MULTIPLY'; c2.inputs[1].default_value = 1.8; L.new(b.outputs[0], c2.inputs[0])
    mx = N.new("ShaderNodeMix"); mx.data_type = 'RGBA'; mx.inputs[7].default_value = (0.9, 0.9, 0.88, 1)
    src = p.inputs['Base Color'].links[0].from_socket if p.inputs['Base Color'].is_linked else None
    if src:
        L.new(src, mx.inputs[6])
    else:
        mx.inputs[6].default_value = p.inputs['Base Color'].default_value
    L.new(c2.outputs[0], mx.inputs['Factor']); L.new(mx.outputs[2], p.inputs['Base Color'])
    return m


def extinguisher(name):
    """A red stored-pressure extinguisher lying on its side (axis along Y, so it rolls along X): domed cylinder, neck,
    black valve head with carry handle and squeeze lever, a plain white label band, a black hose with a nozzle."""
    red = pbr("ExtRed", (0.55, 0.02, 0.015), 0.22, 0.1, **{'Coat Weight': 1.0, 'Coat Roughness': 0.05})
    blk = pbr("ExtBlack", (0.02, 0.02, 0.02), 0.45)
    chrome = pbr("ExtChrome", (0.7, 0.7, 0.72), 0.15, 1.0)
    label = pbr("ExtLabel", (0.82, 0.82, 0.78), 0.6)
    R = (math.radians(90), 0, 0)
    B = dd.Builder(name)
    B.cyl((0, 0, 0), 0.08, 0.42, red, verts=32, rot=R)
    B.cyl((0, -0.02, 0), 0.0805, 0.16, label, verts=32, rot=R)
    for k in range(5):                                   # the domed top as stacked rings
        r_ = 0.08 * math.cos(math.radians(18 * (k + 1)))
        B.cyl((0, 0.21 + 0.012 * k + 0.006, 0), r_, 0.014, red, verts=32, rot=R)
    B.cyl((0, -0.215, 0), 0.078, 0.012, blk, verts=32, rot=R)
    B.cyl((0, 0.29, 0), 0.022, 0.05, chrome, verts=16, rot=R)
    B.box((0, 0.335, 0.0), (0.05, 0.05, 0.05), blk)
    B.box((0, 0.36, 0.06), (0.03, 0.12, 0.012), blk, rot=(math.radians(-15), 0, 0))     # lever
    B.box((0, 0.35, -0.045), (0.03, 0.1, 0.012), blk, rot=(math.radians(10), 0, 0))     # carry handle
    for k in range(10):                                  # hose: a curve of short segments down the body
        a = k / 9.0
        B.cyl((0.075 + 0.02 * math.sin(a * 3.0), 0.33 - 0.5 * a, 0.03 - 0.06 * a), 0.011, 0.07, blk, verts=8, rot=R)
    B.cyl((0.09, -0.2, -0.03), 0.016, 0.07, blk, verts=10, rot=R)
    return B.done()


def build(variant=None):
    c = {}
    world_flat((0.04, 0.04, 0.045), 1.0)
    wall = dd.tex_mat("painted_concrete", 0.6, tint=(0.88, 0.88, 0.85), name="StairWall", sat=0.4)
    step = dd.tex_mat("concrete_floor_02", 1.0, tint=(0.75, 0.75, 0.74), name="StairStep", sat=0.2)
    settle = "min(1, max(0, (frame - 10) / 100.0))" if variant == "settle" else "min(0.5, frame / 240.0)"
    dusted(step, settle); dusted(wall, settle + " * 0.4")
    nose = pbr("Nosing", (0.2, 0.2, 0.21), 0.4, 0.8)
    B = dd.Builder("Stairwell"); stairwell(B, wall, step, nose); B.done()
    rail = pbr("Rail", (0.1, 0.11, 0.12), 0.35, 0.8)
    for f in range(-1, 2):
        z0 = f * FH
        for sx in (0.05, -0.05):
            ang = math.atan2(FH / 2, L); ln = math.hypot(L, FH / 2)
            zc = z0 + FH / 4 + 0.95 if sx > 0 else z0 + FH * 0.75 + 0.95
            cyl("Rail", (sx, L / 2 + 0.1, zc), 0.022, ln, rail, verts=10, rot=(math.pi / 2 + (-ang if sx > 0 else ang), 0, 0))
    # light: one caged bulb per landing, warm; a green exit sign glow (no text)
    for f in range(-1, 2):
        for (y, dz) in ((-0.9, 2.6), (L + 1.0, 2.6 + FH / 2)):
            l = bpy.data.lights.new("Fluo", 'AREA'); l.shape = 'RECTANGLE'; l.size = 1.2; l.size_y = 0.12; l.energy = 260; l.color = (0.9, 0.96, 1.0)
            o = bpy.data.objects.new("Fluo", l); bpy.context.collection.objects.link(o); o.location = (0.0, y, f * FH + dz + 0.25)
            box("FluoHousing", (0.0, y, f * FH + dz + 0.33), (1.25, 0.14, 0.05), pbr("FluoH", (0.85, 0.85, 0.83), 0.5))
            box("FluoTube", (0.0, y, f * FH + dz + 0.29), (1.2, 0.05, 0.03), emissive("FluoE", (0.9, 0.96, 1.0), 12))
    box("ExitSign", (-1.29, -0.6, 2.4), (0.02, 0.35, 0.15), emissive("ExitGreen", (0.1, 1.0, 0.35), 3))
    box("ExitDoor", (-1.29, -0.5, 1.05), (0.04, 0.95, 2.1), pbr("ExitDoorM", (0.25, 0.27, 0.28), 0.4, 0.6))
    if variant == "settle":
        c["ext"] = extinguisher("Ext1")
        e2 = extinguisher("Ext2"); e2.location = (-0.3, -0.75, 0.09); e2.rotation_euler = (0, 0, 0.7)
        powder_volume("Powder", (0, -0.3, 0.6), (2.6, 2.0, 1.2), "max(0.08, 1.1 - frame / 110.0)", drift=(0.0, 0.03, -0.12), scale=2.2)
    else:
        powder_volume("Powder", (0, 0.8, 1.0), (2.6, 4.0, 3.0), "min(3.0, 0.8 + frame / 30.0)", drift=(0.05, -0.15, -0.05), scale=2.6)
        powder_volume("Billow", (0.4, 0.2, 0.9), (1.6, 1.8, 1.8), "min(4.0, frame / 15.0)", drift=(0.25, 0.4, 0.3), scale=3.5)
        c["men"] = []
        for k in range(2):
            h = painter(f"Run{k}", 30 + 8 * k, k + 1)
            c["men"].append(h)
    return c


def anim_powder(c, t):
    sec = t * DUR["powder"]
    for k, h in enumerate(c["men"]):
        # down the lower flight toward the exit door at the bottom landing
        a = Vector((0.65 + 0.12 * k, L + 0.3 - 1.1 * k, 0.0)); b = Vector((-0.6, -0.7, 0.0))
        walk_to(h, a, b, sec * 1.0 + 0.6 * k, speed=1.4, cadence=2.4)
        y = h.arm.location.y
        frac = max(0.0, min(1.0, (y - 0.1) / L))
        dd.ground(h, frac * (FH / 2))                # on the flight: feet follow the slope


def anim_settle(c, t):
    sec = t * DUR["settle"]
    u = 1 - (1 - min(1.0, sec / 3.6)) ** 2         # decelerating roll to a stop
    x = -0.9 + 1.5 * u
    e = c["ext"]; e.location = (x, -0.45, 0.08); e.rotation_euler = (0, (1.5 * u) / 0.08, 0)


MOVES = {
    "powder": dict(kind="anim", dof=4.0, anim=anim_powder,
                   cam=lambda c, t: (Vector((0.75, L + 0.95, 3.1)).lerp(Vector((0.6, L + 0.8, 2.95)), ease(t)), Vector((0.1, 1.0, 0.4)), 22),
                   focus=lambda c, t: Vector((-0.6, 1.8, 0.8))),
    "settle": dict(kind="anim", dof=4.0, anim=anim_settle,
                   cam=lambda c, t: (Vector((0.7, 1.7, 1.55)).lerp(Vector((0.55, 1.4, 1.4)), ease(t)), Vector((0.0, -0.6, 0.15)), 26),
                   focus=lambda c, t: c["ext"].location),
}
