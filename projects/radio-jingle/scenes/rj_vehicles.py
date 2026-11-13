"""Period vehicles for the Radio Jingle film, built with the shared vehicle kit (lofted bodies, no boxes) and registered
into vehicles.KINDS, so vehicles.make("fiat600", ...) works like every other kind.

  fiat600            small rear-engined 1960s-70s two-door (Fiat 600 style, no badge), default yellow
  polizei_1981       a West German style patrol saloon, white with green doors and bonnet, one blue rotating beacon (no crest, no text)
  helicopter_police  a generic light twin police helicopter (Bo 105 style, no markings): pod, tail boom, skids, spinning rotor
  boat_police        a small open police launch (no text) with an outboard
"""
import math, inspect
import bpy
from mathutils import Vector
import vehicles as V
import vehicles_cars as VC
from vehicles_cars import S, bumper, wheels4


# ============================================================================ Fiat 600 style
def fiat600(variant=None):
    XF, XR, R, RIM, TR = 1.0, -1.0, 0.268, 0.15, 0.60
    keys = [S(1.62, 0.40, 0.60, 0.64, 0.50, 0.42, rb=0.06, rs=0.05, crown=0.02),
            S(1.58, 0.33, 0.68, 0.72, 0.62, 0.54, rb=0.07, rs=0.05, crown=0.03),
            S(1.42, 0.29, 0.74, 0.79, 0.67, 0.60, crown=0.03),
            S(1.10, 0.27, 0.80, 0.84, 0.69, 0.62, crown=0.03),
            S(0.80, 0.27, 0.83, 0.875, 0.69, 0.62, crown=0.03),
            S(0.66, 0.27, 0.84, 0.92, 0.69, 0.60, crown=0.03),
            S(0.22, 0.27, 0.86, 1.36, 0.69, 0.54, crown=0.05, rt=0.12),
            S(-0.62, 0.27, 0.87, 1.37, 0.69, 0.55, crown=0.05, rt=0.12),
            S(-1.02, 0.28, 0.87, 1.20, 0.69, 0.57, crown=0.04, rt=0.1),
            S(-1.30, 0.29, 0.86, 0.98, 0.68, 0.60, crown=0.03),
            S(-1.52, 0.31, 0.78, 0.84, 0.64, 0.56, rb=0.07, rs=0.05, crown=0.03),
            S(-1.62, 0.37, 0.64, 0.68, 0.52, 0.44, rb=0.06, rs=0.05, crown=0.02)]

    def masks(g):
        M = V.window_masks(g, [[(-0.40, 0.92), (0.40, 0.92), (0.12, 1.30), (-0.40, 1.31)],
                               [(-1.02, 0.92), (-0.48, 0.92), (-0.48, 1.31), (-0.80, 1.31)]],
                           front=[(-0.58, 0.93), (0.58, 0.93), (0.46, 1.31), (-0.46, 1.31)],
                           rear=[(-0.46, 1.0), (0.46, 1.0), (0.40, 1.17), (-0.40, 1.17)], seal=0.016, trim=0.006)
        side = g.ss(0.55, 0.7, g.any)
        trim = g.inside(g.z, 0.735, 0.745, 0.002) * side * g.inside(g.x, -1.45, 1.5)
        M['chrome'] = g.mx(M['chrome'], trim)
        M['gap'] = V.gaps(g, [('x', 0.52, 0.32, 0.86), ('x', -0.46, 0.32, 0.87), ('z', 0.32, -0.46, 0.52),
                              ('top_x', 1.45, 0.5), ('top_x', 0.72, 0.5), ('top_y', 0.5, 0.72, 1.45),
                              ('top_x', -1.12, 0.45), ('top_x', -1.5, 0.45), ('top_y', 0.45, -1.5, -1.12)])
        return M
    paint = V.paint_shader("V_Paint_Fiat600", masks, rough=0.3)
    body = V.loft_body("FiatBody", keys, paint, step=0.09)
    V.cut_arches(body, [(XF, 0.27, 0.31, 0.5, 1.1), (XR, 0.27, 0.31, 0.5, 1.1)], V.liner())
    ch, rb, bp = V.chrome(), V.rubber(), V.black_plastic()
    parts = [body]
    fpts = [(1.50, -0.62), (1.62, -0.6), (1.67, -0.45), (1.685, 0), (1.67, 0.45), (1.62, 0.6), (1.50, 0.62)]
    rpts = [(-x, y) for (x, y) in fpts]
    parts += [bumper("BumpF", fpts, 0.43, 0.03, 0.05, ch, 0.012), bumper("BumpR", rpts, 0.43, 0.03, 0.05, ch, 0.012, flip=True)]
    for s in (-1, 1):                                   # over-riders
        parts.append(V.rbox("Over", (1.69, s * 0.3, 0.47), (0.04, 0.035, 0.14), 0.012, ch))
        parts.append(V.rbox("OverR", (-1.69, s * 0.3, 0.47), (0.04, 0.035, 0.14), 0.012, ch))
    heads = []
    for s in (-1, 1):
        parts.append(V.round_lamp(f"Head{s}", (1.585, s * 0.47, 0.66), 0.085, 0.05, "head"))
        heads.append((1.62, s * 0.47, 0.66))
        parts.append(V.lamp(f"Ind{s}", (1.66, s * 0.47, 0.52), (0.03, 0.08, 0.04), "ind", 0.01))
        parts.append(V.lamp(f"Tail{s}", (-1.57, s * 0.52, 0.72), (0.04, 0.07, 0.13), "tail", 0.012, facing=-1))
        parts.append(V.mirror(f"Mirror{s}", (0.62, s * 0.7, 0.93), s, ch, size=(0.04, 0.09, 0.07), arm=0.05, m_arm=ch))
        parts.append(V.rbox("Handle", (-0.36, s * 0.70, 0.82), (0.09, 0.02, 0.02), 0.006, ch))
    # the badge-less front: a chrome moustache trim; engine-lid louvres at the rear
    parts.append(V.rbox("Moustache", (1.655, 0, 0.6), (0.02, 0.36, 0.025), 0.008, ch))
    for k in range(7):
        parts.append(V.rbox("Louvre", (-1.42 + 0.015 * k, 0, 0.92 - 0.035 * k), (0.012, 0.42, 0.012), 0.004, bp))
    parts.append(V.plate("PlateR", (-1.645, 0, 0.53), facing=-1, size=(0.34, 0.2)))
    parts.append(V.plate("PlateF", (1.70, 0, 0.36), size=(0.4, 0.09)))
    for y in (-0.28, 0.12):
        parts.append(V.rbox("Wiper", (0.64, y, 0.935), (0.012, 0.36, 0.008), 0.003, bp, rot=(0, math.radians(-40), 0)))
    parts.append(V.cylinder("Exhaust", (-1.62, -0.35, 0.28), 0.02, 0.2, ch, axis='X', verts=12))
    parts.append(V.underbody("Floor", -1.4, 1.4, 0.48, 0.19, 0.28))
    V.cabin_interior(parts, [0.05, -0.75], 0.32, 0.47, 0.6, 0.80, 0.62)
    body = V.join(parts, "Fiat600")
    me = V.wheel_mesh("fiat", R, 0.14, RIM, "steel")
    wheels4(body, me, XF, XR, TR, R, RIM)
    return V._finish(body, "Fiat600", (0.78, 0.6, 0.08), heads=heads)


# ============================================================================ 1981 West German patrol car (from the saloon)
def _polizei_src():
    src = inspect.getsource(VC.sedan_1990s_soviet)
    src = src.replace("def sedan_1990s_soviet(variant=None):", "def polizei_1981(variant=None):")
    src = src.replace('militia = variant == "militia"', 'militia = True')
    src = src.replace('tag = "V_Paint_Lada" + ("_militia" if militia else "")', 'tag = "V_Paint_Polizei1981"')
    # livery: green doors (and bonnet) on the white body, no text
    src = src.replace("""            band = g.inside(g.z, 0.64, 0.76, 0.002) * side * g.inside(g.x, -1.99, 1.99)
            M['livery'] = [(band, (0.02, 0.07, 0.32))]""",
                      """            doors = g.inside(g.z, 0.30, 0.95, 0.002) * side * g.inside(g.x, -1.075, 0.60, 0.003)
            bon = g.ss(0.5, 0.65, g.nz) * g.inside(g.x, 0.63, 2.0, 0.003)
            M['livery'] = [(g.mx(doors, bon), (0.05, 0.16, 0.08))]""")
    a = src.index("    if militia:\n        V.add_lightbar"); b = src.index("        col = (0.82, 0.83, 0.84)")
    src = src[:a] + "    if militia:\n        V.add_rotating_beacon(body, (-0.5, 0, 1.43), (0.1, 0.3, 1.0), rate=1.3, rad=0.075, height=0.12)\n" + src[b:]
    src = src.replace('return V._finish(body, "Sedan1990s" + ("Militia" if militia else ""), col, heads=heads)',
                      'return V._finish(body, "Polizei1981", (0.80, 0.81, 0.80), heads=heads)')
    ns = dict(VC.__dict__)
    exec(compile(src, "polizei_1981", "exec"), ns)
    return ns["polizei_1981"]


polizei_1981 = _polizei_src()


# ============================================================================ helicopter (Bo 105 style, generic)
def helicopter_police(variant=None):
    from vehicles_air import loft_ellipse
    paint = V.simple("V_HeliPaint", (0.82, 0.83, 0.82), 0.35, 0.0)
    green = V.simple("V_HeliGreen", (0.05, 0.16, 0.08), 0.35, 0.0)
    gl = V.glass(); dk = V.steel_dark(); bp = V.black_plastic()
    pod = loft_ellipse("HeliPod", [(2.15, 1.05, 0.05, 0.05), (2.05, 1.05, 0.38, 0.42), (1.7, 1.12, 0.66, 0.66), (1.0, 1.2, 0.78, 0.74),
                                   (0.0, 1.22, 0.8, 0.76), (-0.9, 1.25, 0.75, 0.7), (-1.6, 1.38, 0.5, 0.48), (-2.1, 1.5, 0.22, 0.22)], paint, ring=36, n=2.4)
    canopy = loft_ellipse("HeliCanopy", [(2.13, 1.05, 0.06, 0.06), (2.0, 1.08, 0.4, 0.44), (1.65, 1.18, 0.665, 0.66), (1.1, 1.28, 0.78, 0.72)],
                          gl, ring=36, n=2.4)
    canopy.scale = (1.004, 1.004, 1.004)
    band = loft_ellipse("HeliBand", [(0.8, 0.95, 0.805, 0.42), (-0.9, 0.98, 0.755, 0.38)], green, ring=36, n=2.4, cap=False)
    boom = loft_ellipse("HeliBoom", [(-1.9, 1.5, 0.2, 0.2), (-4.5, 1.62, 0.12, 0.12), (-5.6, 1.66, 0.09, 0.09)], paint, ring=20)
    fin = V.rbox("Fin", (-5.5, 0, 2.05), (0.5, 0.06, 0.9), 0.04, paint, rot=(0, math.radians(-15), 0))
    stab = V.rbox("Stab", (-5.1, 0, 1.66), (0.35, 1.3, 0.05), 0.02, paint)
    mast = V.cylinder("Mast", (0.15, 0, 2.15), 0.09, 0.3, dk, axis='Z', verts=16)
    eng = loft_ellipse("Engine", [(0.9, 2.0, 0.05, 0.05), (0.7, 2.0, 0.4, 0.2), (-0.8, 2.0, 0.42, 0.22), (-1.6, 1.85, 0.2, 0.12)], paint, ring=24)
    parts = [pod, canopy, band, boom, fin, stab, mast, eng]
    seam = V.simple("V_HeliSeam", (0.12, 0.12, 0.12), 0.5)
    for sy in (-1, 1):                                  # rear side windows, door seams, step, door handle
        parts.append(V.rbox("SideWin", (0.15, sy * 0.775, 1.28), (0.75, 0.02, 0.42), 0.06, gl))
        parts.append(V.rbox("DoorSeamF", (0.62, sy * 0.79, 1.0), (0.02, 0.012, 0.9), 0.004, seam))
        parts.append(V.rbox("DoorSeamR", (-0.28, sy * 0.79, 1.0), (0.02, 0.012, 0.9), 0.004, seam))
        parts.append(V.rbox("Step", (0.15, sy * 0.92, 0.32), (0.55, 0.12, 0.025), 0.01, dk))
        parts.append(V.rbox("Handle", (0.0, sy * 0.8, 1.02), (0.1, 0.015, 0.02), 0.005, dk))
    parts.append(V.rbox("TailBand", (-4.0, 0, 1.62), (1.2, 0.27, 0.27), 0.1, green))
    parts.append(V.cylinder("Exhaust", (-1.45, 0, 2.05), 0.09, 0.3, dk, axis='X', verts=16))
    parts.append(V.cylinder("Antenna", (-0.6, 0, 0.08), 0.008, 0.35, dk, axis='Z', verts=6))
    nl = V.simple("V_NoseLight", (1.0, 0.95, 0.85), 0.1, 0.0, **{'Emission Color': (1.0, 0.92, 0.75, 1), 'Emission Strength': 4.0})
    parts.append(V.cylinder("LandLight", (2.0, 0, 0.32), 0.06, 0.05, nl, axis='X', verts=16))
    rl = V.simple("V_AntiColl", (0.8, 0.05, 0.03), 0.3, 0.0, **{'Emission Color': (1.0, 0.05, 0.02, 1), 'Emission Strength': 6.0})
    parts.append(V.cylinder("AntiColl", (-1.2, 0, 1.98), 0.05, 0.06, rl, axis='Z', verts=12))
    for s in (-1, 1):                                   # skids
        parts.append(V.cylinder("Skid", (0.1, s * 0.95, 0.05), 0.035, 3.0, dk, axis='X', verts=12))
        for x in (0.9, -0.6):
            p = V.cylinder("Strut", (x, s * 0.8, 0.45), 0.03, 0.85, dk, axis='Z', verts=10)
            p.rotation_euler = (s * math.radians(22), 0, 0); parts.append(p)
    body = V.join(parts, "Helicopter")
    # main rotor (four blades) and tail rotor as spinning children (frame-driven)
    rot = bpy.data.objects.new("MainRotor", None); V.link(rot); rot.parent = body; rot.location = (0.15, 0, 2.34)
    rotor_m = V.simple("V_Blade", (0.05, 0.05, 0.055), 0.4)
    blades = []
    for k in range(4):
        b_ = V.rbox("Blade", (2.45, 0, 0), (4.9, 0.27, 0.035), 0.01, rotor_m); b_.rotation_euler.z = 0
        b2 = bpy.data.objects.new("BladeArm", None); V.link(b2); b2.parent = rot; b2.rotation_euler.z = k * math.pi / 2
        b_.parent = b2; blades.append(b_)
    disc = V.cylinder("RotorBlur", (0, 0, 0), 4.9, 0.01, V.simple("V_Blur", (0.03, 0.03, 0.03), 0.5, 0.0, **{'Alpha': 0.12}), axis='Z', verts=64)
    disc.parent = rot
    V._drive(rot, 'rotation_euler', "frame * 1.35", 2)       # ~6.6 rev/s at 24 fps (motion blur smears it)
    tr = bpy.data.objects.new("TailRotor", None); V.link(tr); tr.parent = body; tr.location = (-5.55, 0.12, 2.0)
    for k in range(2):
        tb = V.rbox("TBlade", (0, 0, 0.45), (0.12, 0.02, 0.9), 0.005, rotor_m); a = bpy.data.objects.new("TArm", None); V.link(a)
        a.parent = tr; a.rotation_euler.y = k * math.pi; tb.parent = a
    V._drive(tr, 'rotation_euler', "frame * 3.1", 1)
    heads = [(2.0, 0.0, 0.7)]
    return V._finish(body, "HelicopterPolice", (0.82, 0.83, 0.82), heads=heads)


# ============================================================================ police launch
def boat_police(variant=None):
    from vehicles_air import loft_ellipse
    hull_m = V.simple("V_BoatHull", (0.82, 0.83, 0.8), 0.3, 0.0, **{'Coat Weight': 0.6})
    stripe = V.simple("V_BoatGreen", (0.05, 0.16, 0.08), 0.4)
    hull = loft_ellipse("Hull", [(3.0, 0.55, 0.05, 0.3), (2.6, 0.45, 0.7, 0.45), (1.5, 0.4, 1.05, 0.5), (0.0, 0.4, 1.12, 0.52),
                                 (-2.0, 0.42, 1.08, 0.5), (-2.6, 0.45, 1.0, 0.45)], hull_m, ring=32, n=2.2)
    # cut the top off: an open boat (scale the top ring down: approximate with a deck plane at the gunwale)
    deck = V.rbox("Deck", (0.0, 0, 0.86), (4.6, 1.9, 0.04), 0.3, V.simple("V_Deck", (0.25, 0.25, 0.24), 0.7))
    band = loft_ellipse("BoatBand", [(2.4, 0.62, 0.79, 0.16), (-2.5, 0.62, 1.01, 0.16)], stripe, ring=32, n=2.2, cap=False)
    console = V.rbox("Console", (0.3, 0, 1.25), (0.8, 0.7, 0.8), 0.06, hull_m)
    screen = V.rbox("Screen", (0.72, 0, 1.75), (0.04, 0.7, 0.35), 0.02, V.glass(), rot=(0, math.radians(-25), 0))
    motor = V.rbox("Outboard", (-2.75, 0, 0.75), (0.4, 0.35, 0.6), 0.08, V.black_plastic())
    shaft = V.cylinder("OBShaft", (-2.8, 0, 0.2), 0.05, 0.6, V.steel_dark(), axis='Z', verts=12)
    body = V.join([hull, deck, band, console, screen, motor, shaft], "PoliceBoat")
    V.add_rotating_beacon(body, (0.3, 0, 1.68), (0.1, 0.3, 1.0), rate=1.3, rad=0.06, height=0.1, real_light=False)
    return V._finish(body, "PoliceBoat", (0.82, 0.83, 0.8))


def register():
    V.KINDS["fiat600"] = fiat600
    V.KINDS["polizei_1981"] = polizei_1981
    V.KINDS["helicopter_police"] = helicopter_police
    V.KINDS["boat_police"] = boat_police


register()


# ============================================================================ police diving dinghy (inflatable)
def dinghy_police(variant=None):
    """A 1970s inflatable (grey Hypalon tubes in a U, a pointed bow, a plywood transom with an outboard, a floor,
    grab lines along the tubes, a dark-green rubbing strake)."""
    tube_m = V.simple("V_DinghyTube", (0.16, 0.17, 0.17), 0.55, 0.0)
    strake = V.simple("V_DinghyStrake", (0.04, 0.11, 0.06), 0.5)
    floor_m = V.simple("V_DinghyFloor", (0.10, 0.10, 0.10), 0.8)
    wood = V.simple("V_Transom", (0.22, 0.15, 0.08), 0.6)
    rope = V.simple("V_Rope", (0.6, 0.55, 0.45), 0.8)
    bpy.ops.mesh.primitive_torus_add(major_radius=1.0, minor_radius=0.22, major_segments=64, minor_segments=20, location=(0.2, 0, 0.3))
    tube = bpy.context.active_object; tube.name = "DinghyTube"; tube.scale = (2.0, 0.78, 1.0); tube.data.materials.append(tube_m)
    bpy.ops.object.transform_apply(scale=True)
    import bmesh                                          # cut the stern: the tubes end at the transom (x < -1.6)
    bm = bmesh.new(); bm.from_mesh(tube.data)
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.x < -1.55], context='VERTS'); bm.to_mesh(tube.data); bm.free()
    parts = [tube]
    bpy.ops.mesh.primitive_torus_add(major_radius=1.0, minor_radius=0.03, major_segments=64, minor_segments=8, location=(0.2, 0, 0.3))
    st = bpy.context.active_object; st.scale = (2.13, 0.92, 1.0); st.data.materials.append(strake); bpy.ops.object.transform_apply(scale=True)
    bm = bmesh.new(); bm.from_mesh(st.data); bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.x < -1.55], context='VERTS'); bm.to_mesh(st.data); bm.free()
    parts.append(st)
    bpy.ops.mesh.primitive_torus_add(major_radius=1.0, minor_radius=0.008, major_segments=64, minor_segments=6, location=(0.2, 0, 0.52))
    rp = bpy.context.active_object; rp.scale = (1.95, 0.74, 1.0); rp.data.materials.append(rope); bpy.ops.object.transform_apply(scale=True)
    bm = bmesh.new(); bm.from_mesh(rp.data); bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.x < -1.5], context='VERTS'); bm.to_mesh(rp.data); bm.free()
    parts.append(rp)
    parts.append(V.rbox("DinghyFloor", (0.0, 0, 0.12), (3.2, 1.05, 0.04), 0.1, floor_m))
    parts.append(V.rbox("Transom", (-1.6, 0, 0.32), (0.05, 1.5, 0.42), 0.02, wood))
    parts.append(V.rbox("Outboard", (-1.82, 0, 0.62), (0.32, 0.28, 0.38), 0.07, V.black_plastic()))
    parts.append(V.cylinder("OBShaft", (-1.86, 0, 0.12), 0.04, 0.6, V.steel_dark(), axis='Z', verts=12))
    parts.append(V.rbox("Thwart", (0.4, 0, 0.42), (0.28, 1.4, 0.04), 0.01, wood))
    parts.append(V.rbox("TankBox", (-0.9, 0.25, 0.25), (0.45, 0.3, 0.22), 0.03, V.simple("V_Fuel", (0.5, 0.08, 0.05), 0.5)))
    for k in range(3):                                   # spare air tanks lying on the floor
        parts.append(V.cylinder("SpareTank", (-0.3 + 0.0 * k, -0.25 + 0.17 * k, 0.22), 0.08, 0.62, V.simple("V_TankS", (0.62, 0.6, 0.55), 0.3, 0.6), axis='X', verts=16))
    body = V.join(parts, "PoliceDinghy")
    return V._finish(body, "PoliceDinghy", (0.16, 0.17, 0.17))


V.KINDS["dinghy_police"] = dinghy_police
