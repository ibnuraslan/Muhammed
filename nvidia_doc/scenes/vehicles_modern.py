"""1940s US sedan, modern saloon (+ police / taxi), city bus, delivery truck and forklift for vehicles.py."""
import math
from mathutils import Vector, Matrix
import vehicles as V
from vehicles_cars import S, bumper, wheels4, cab_1990s, truck_chassis, fender


def fender_loft(name, keys, m, y, arch=None):
    """A separate pontoon fender: lofted, its wheel opening cut, then moved out to y."""
    f = V.loft_body(name, keys, m, step=0.12, extra=0.03)
    if arch:
        x, z, r = arch
        c = V.cylinder("Cut", (x, 0, z), r, 1.2, V.liner(), axis='Y', verts=48)
        f.data.materials.append(V.liner())
        V.boolean_cut(f, c)
        import bpy; bpy.data.objects.remove(c)
        f.data.shade_smooth(); f.data.set_sharp_from_angle(angle=math.radians(40))
    f.data.transform(Matrix.Translation((0, y, 0)))
    return f


# ============================================================================ 6. 1940s US sedan (+ police)
def sedan_1940s_us(variant=None):
    police = variant == "police"
    XF, XR, R, RIM, TR = 1.55, -1.38, 0.36, 0.205, 0.74
    keys = [S(2.30, 0.56, 0.93, 0.96, 0.36, 0.30, rb=0.08, rs=0.08, crown=0.04, bul=0.0),
            S(2.22, 0.52, 0.98, 1.02, 0.45, 0.38, rb=0.1, rs=0.1, crown=0.05, bul=0.0),
            S(1.60, 0.50, 1.02, 1.06, 0.60, 0.50, rb=0.1, rs=0.1, crown=0.07, bul=0.0),
            S(0.86, 0.48, 1.03, 1.08, 0.75, 0.62, rb=0.1, rs=0.08, crown=0.06, bul=0.01),
            S(0.38, 0.48, 1.04, 1.60, 0.78, 0.60, rb=0.1, rs=0.08, rt=0.15, crown=0.07, bul=0.02),
            S(-0.78, 0.48, 1.05, 1.60, 0.78, 0.60, rb=0.1, rs=0.08, rt=0.15, crown=0.07, bul=0.02),
            S(-1.42, 0.48, 1.05, 1.18, 0.77, 0.63, rb=0.1, rs=0.08, crown=0.08, bul=0.02, soft=True),
            S(-1.92, 0.50, 1.02, 1.08, 0.72, 0.58, rb=0.1, rs=0.1, crown=0.07, bul=0.01, soft=True),
            S(-2.26, 0.55, 0.92, 0.95, 0.60, 0.48, rb=0.1, rs=0.1, crown=0.04, bul=0.0),
            S(-2.32, 0.62, 0.84, 0.86, 0.50, 0.40, rb=0.08, rs=0.08, crown=0.02, bul=0.0)]
    tag = "V_Paint_US40" + ("_police" if police else "")

    def masks(g):
        M = V.window_masks(g, [[(-0.30, 1.10), (0.30, 1.10), (0.10, 1.50), (-0.30, 1.50)],
                               [(-0.98, 1.10), (-0.38, 1.10), (-0.38, 1.50), (-0.86, 1.50)],
                               [(-1.32, 1.12), (-1.06, 1.12), (-1.06, 1.46), (-1.12, 1.48)]],
                           front=[[(0.02, 1.12), (0.56, 1.12), (0.50, 1.50), (0.02, 1.50)],
                                  [(-0.56, 1.12), (-0.02, 1.12), (-0.02, 1.50), (-0.50, 1.50)]],
                           rear=[(-0.38, 1.24), (0.38, 1.24), (0.30, 1.50), (-0.30, 1.50)], seal=0.012, trim=0.012)
        side = g.ss(0.55, 0.7, g.any); top = g.ss(0.6, 0.75, g.nz)
        strip = g.band(g.y, 0.0, 0.012) * top * g.inside(g.x, 0.9, 2.28)
        belt = g.inside(g.z, 1.005, 1.02, 0.002) * side * g.inside(g.x, -2.0, 2.2)
        M['chrome'] = g.mx(M['chrome'], g.mx(strip, belt))
        M['gap'] = V.gaps(g, [('x', 0.36, 0.50, 1.04), ('x', -0.34, 0.50, 1.05), ('x', -1.02, 0.50, 1.05),
                              ('top_x', 0.88, 0.70), ('top_x', -1.46, 0.6), ('top_y', 0.60, -2.25, -1.46)])
        if police:
            doors = side * g.inside(g.x, -1.02, 0.36, 0.002) * g.inside(g.z, 0.47, 1.0, 0.002)
            M['livery'] = [(doors, (0.85, 0.85, 0.82))]
        return M
    paint = V.paint_shader(tag, masks, rough=0.28)
    body = V.loft_body("US40Body", keys, paint, step=0.11)
    parts = [body]
    fk = [S(2.40, 0.64, 0.70, 0.72, 0.09, 0.05, rb=0.05, rs=0.04, crown=0.02, bul=0.0),
          S(2.30, 0.56, 0.80, 0.86, 0.15, 0.11, rb=0.06, rs=0.05, crown=0.03, bul=0.0),
          S(2.00, 0.50, 0.88, 0.97, 0.18, 0.14, rb=0.06, rs=0.05, crown=0.04, bul=0.0, soft=True),
          S(1.50, 0.50, 0.90, 1.00, 0.18, 0.14, rb=0.06, rs=0.05, crown=0.04, bul=0.0, soft=True),
          S(1.02, 0.47, 0.78, 0.86, 0.17, 0.13, rb=0.06, rs=0.05, crown=0.03, bul=0.0, soft=True),
          S(0.78, 0.44, 0.56, 0.62, 0.15, 0.10, rb=0.04, rs=0.04, crown=0.02, bul=0.0),
          S(0.70, 0.44, 0.49, 0.52, 0.12, 0.08, rb=0.03, rs=0.03, crown=0.01, bul=0.0)]
    rk = [S(-0.70, 0.44, 0.50, 0.53, 0.12, 0.08, rb=0.03, rs=0.03, crown=0.01, bul=0.0),
          S(-0.82, 0.44, 0.66, 0.74, 0.15, 0.11, rb=0.05, rs=0.05, crown=0.02, bul=0.0),
          S(-1.10, 0.47, 0.82, 0.90, 0.17, 0.13, rb=0.06, rs=0.05, crown=0.03, bul=0.0, soft=True),
          S(-1.55, 0.50, 0.86, 0.94, 0.17, 0.13, rb=0.06, rs=0.05, crown=0.04, bul=0.0, soft=True),
          S(-2.05, 0.55, 0.76, 0.82, 0.14, 0.10, rb=0.06, rs=0.05, crown=0.03, bul=0.0, soft=True),
          S(-2.30, 0.62, 0.66, 0.68, 0.08, 0.05, rb=0.04, rs=0.04, crown=0.02, bul=0.0)]
    fpaint = V.paint_shader(tag + "_fender", lambda g: {}, rough=0.28)
    for s in (-1, 1):
        parts.append(fender_loft("FenderF", fk, fpaint, s * 0.77, (XF, R + 0.02, R + 0.05)))
        parts.append(fender_loft("FenderR", rk, fpaint, s * 0.76, (XR, R + 0.02, R + 0.04)))
        parts.append(V.rbox("Apron", (1.6, s * 0.56, 0.70), (1.45, 0.30, 0.30), 0.05, fpaint))
        parts.append(V.rbox("RunBoard", (0.0, s * 0.80, 0.455), (1.5, 0.22, 0.035), 0.012, V.rubber()))
        parts.append(V.rbox("RunTrim", (0.0, s * 0.912, 0.455), (1.5, 0.01, 0.03), 0.004, V.chrome()))
    ch = V.chrome()
    # chrome grille: bowed horizontal bars between the fenders, plus a centre bar
    for k in range(9):
        z = 0.56 + k * 0.042; w = 0.44 - abs(k - 4) * 0.012
        path = [(2.30 - 0.06 * (1 - (y / w) ** 2) * 0 - 0.03 * abs(y / w) ** 2, y, z) for y in [w * (j / 6 - 1) for j in range(13)]]
        parts.append(V.sweep("GrilleBar", path, V.rounded_rect(0.02, 0.018, 0.008, 2), ch))
    parts.append(V.rbox("GrilleBack", (2.24, 0, 0.73), (0.06, 0.88, 0.40), 0.03, V.black_plastic()))
    parts.append(V.rbox("GrilleCentre", (2.315, 0, 0.73), (0.025, 0.03, 0.40), 0.01, ch))
    # massive chrome bumpers with overriders
    fp = [(2.30, -0.98), (2.46, -0.95), (2.52, -0.6), (2.53, 0), (2.52, 0.6), (2.46, 0.95), (2.30, 0.98)]
    parts.append(bumper("BumpF", fp, 0.47, 0.07, 0.15, ch, 0.04))
    rp = [(-x - 0.02, y) for (x, y) in fp]
    parts.append(bumper("BumpR", rp, 0.50, 0.07, 0.15, ch, 0.04, flip=True))
    for s in (-1, 1):
        parts.append(V.rbox("Guard", (2.55, s * 0.32, 0.52), (0.05, 0.05, 0.26), 0.02, ch))
        parts.append(V.rbox("Guard", (-2.57, s * 0.32, 0.55), (0.05, 0.05, 0.26), 0.02, ch))
        parts.append(V.round_lamp(f"Head{s}", (2.355, s * 0.77, 0.80), 0.095, 0.06, "head"))
        parts.append(V.round_lamp(f"Park{s}", (2.30, s * 0.52, 0.93), 0.03, 0.03, "ind"))
        parts.append(V.round_lamp(f"Tail{s}", (-2.27, s * 0.76, 0.76), 0.045, 0.04, "tail", facing=-1))
        parts.append(V.mirror(f"Mirror{s}", (0.42, s * 0.78, 1.12), s, ch, size=(0.04, 0.10, 0.07), arm=0.06, m_arm=ch))
        for x in (0.16, -0.55):
            parts.append(V.rbox("Handle", (x, s * 0.80, 0.98), (0.12, 0.02, 0.02), 0.008, ch))
    parts.append(V.lathe("HoodOrn", [(0.0, 0.10), (0.02, 0.07), (0.025, 0.02), (0.03, 0.0)], ch, 16, axis='Z'))
    parts[-1].data.transform(Matrix.Translation((2.18, 0, 1.0)))
    parts.append(V.plate("PlateF", (2.56, 0, 0.36), size=(0.30, 0.15)))
    parts.append(V.plate("PlateR", (-2.30, 0, 0.72), facing=-1, size=(0.30, 0.15)))
    parts.append(V.underbody("Floor", -1.9, 1.9, 0.6, 0.30, 0.50))
    V.cabin_interior(parts, [-0.05, -0.95], 0.36, 0.66, 0.62, 1.0, 0.70)
    body = V.join(parts, "Sedan1940s")
    me = V.wheel_mesh("us40", R, 0.17, RIM, "black" if police else "cream", whitewall=not police)
    wheels4(body, me, XF, XR, TR, R, RIM)
    if police:
        V.add_rotating_beacon(body, (0.0, 0, 1.66), (1.0, 0.06, 0.03), rate=1.2, rad=0.08, height=0.13)
        V.cylinder("Siren", (0.2, 0, 1.70), 0.06, 0.16, ch, axis='X', verts=24).parent = body
        for s in (-1, 1):
            t = V.side_text("Txt", "POLICE", -0.35, 0.80, 0.80, 0.11, V.simple("V_Black", (0.02, 0.02, 0.02), 0.4), s)
            sw = t.modifiers.new("sw", 'SHRINKWRAP'); sw.target = body; sw.offset = 0.002; sw.wrap_mode = 'OUTSIDE_SURFACE'
            V.bake(t); t.parent = body
    return V._finish(body, "Sedan1940s" + ("Police" if police else ""), (0.02, 0.022, 0.025) if police else (0.10, 0.16, 0.12))


# ============================================================================ 7. modern European saloon (+ police, unmarked, taxi)
def _modern_saloon(variant=None):
    XF, XR, R, RIM, TR = 1.40, -1.30, 0.316, 0.203, 0.77
    keys = [S(2.33, 0.36, 0.62, 0.66, 0.74, 0.64, rb=0.08, rs=0.08, crown=0.02, bul=0.0),
            S(2.28, 0.30, 0.70, 0.76, 0.82, 0.72, rb=0.08, rs=0.09, crown=0.03, bul=0.01),
            S(2.05, 0.28, 0.77, 0.83, 0.87, 0.76, rb=0.08, rs=0.08, crown=0.04, bul=0.015, soft=True),
            S(1.30, 0.28, 0.88, 0.93, 0.895, 0.78, rb=0.08, rs=0.06, crown=0.04, bul=0.02),
            S(0.86, 0.30, 0.92, 0.98, 0.90, 0.76, rb=0.08, rs=0.06, crown=0.03, bul=0.02),
            S(-0.10, 0.30, 0.95, 1.45, 0.90, 0.63, rb=0.08, rs=0.06, rt=0.1, crown=0.05, bul=0.025),
            S(-0.75, 0.30, 0.96, 1.44, 0.90, 0.63, rb=0.08, rs=0.06, rt=0.12, crown=0.05, bul=0.025, soft=True),
            S(-1.62, 0.31, 0.99, 1.06, 0.89, 0.72, rb=0.08, rs=0.06, crown=0.04, bul=0.02),
            S(-2.05, 0.33, 0.98, 1.045, 0.84, 0.70, rb=0.09, rs=0.08, crown=0.03, bul=0.01, soft=True),
            S(-2.22, 0.36, 0.95, 1.0, 0.76, 0.64, rb=0.1, rs=0.1, crown=0.025, bul=0.0),
            S(-2.29, 0.42, 0.88, 0.93, 0.64, 0.55, rb=0.08, rs=0.08, crown=0.015, bul=0.0)]
    tag = "V_Paint_Modern_" + (variant or "plain")

    def masks(g):
        M = V.window_masks(g, [[(-0.42, 0.985), (0.70, 0.985), (0.0, 1.37), (-0.42, 1.37)],
                               [(-1.20, 0.995), (-0.50, 0.995), (-0.50, 1.37), (-0.88, 1.37)]],
                           front=[(-0.72, 1.0), (0.72, 1.0), (0.56, 1.40), (-0.56, 1.40)],
                           rear=[(-0.66, 1.08), (0.66, 1.08), (0.56, 1.39), (-0.56, 1.39)], seal=0.012)
        side = g.ss(0.55, 0.7, g.any); fr = g.ss(0.15, 0.35, g.nx); rr = g.ss(0.15, 0.35, -g.nx)
        # black B-pillar and window line trim
        bp = side * g.inside(g.x, -0.50, -0.42, 0.003) * g.inside(g.z, 0.99, 1.37)
        M['black'] = bp
        # flush swept head lamps and tail lamps (wrap round the corners), lower grille, number-plate recess
        M['head'] = g.ss(0.0, 0.004, g.poly(g.ay, g.z, [(0.40, 0.64), (0.86, 0.67), (0.82, 0.79), (0.44, 0.76)])) * g.ss(0.05, 0.2, g.nx) * g.ss(1.6, 1.7, g.x)
        M['tail'] = g.ss(0.0, 0.004, g.poly(g.ay, g.z, [(0.45, 0.84), (0.86, 0.84), (0.84, 0.97), (0.50, 0.97)])) * g.ss(0.05, 0.2, -g.nx) * g.ss(-1.8, -1.9, g.x)
        grille = g.ss(0.0, 0.004, g.poly(g.ay, g.z, [(0.0, 0.62), (0.40, 0.64), (0.38, 0.71), (0.0, 0.71)])) * fr
        lower = g.ss(0.0, 0.004, g.poly(g.ay, g.z, [(0.0, 0.33), (0.62, 0.34), (0.58, 0.50), (0.0, 0.50)])) * fr
        hc = V.E(g, g.math('FRACT', g.z / 0.03).s); hc2 = V.E(g, g.math('FRACT', g.y / 0.03).s)
        mesh = g.mx(g.ss(0.2, 0.1, hc), g.ss(0.2, 0.1, hc2))
        M['black'] = g.mx(M['black'], g.mx(grille, lower) * (0.85 + mesh * 0.15))
        trimz = g.inside(g.z, 0.955, 0.975, 0.002) * side * g.inside(g.x, -1.2, 0.72)
        M['chrome'] = trimz
        M['rubber'] = g.mx(M['rubber'], side * g.inside(g.z, 0.30, 0.36, 0.004) * g.inside(g.x, -1.0, 1.0))
        M['gap'] = V.gaps(g, [('x', 0.98, 0.37, 0.93), ('x', -0.46, 0.37, 0.97), ('arc', XR, 0.32, 0.46, -1.10, -0.8, 0.35, 0.80),
                              ('x', -1.08, 0.78, 0.98), ('z', 0.37, -0.80, 0.98), ('top_x', 0.90, 0.8), ('top_y', 0.80, 0.9, 2.2),
                              ('top_x', -1.64, 0.8), ('end_z', -1, 0.70, 0.82), ('end_z', 1, 0.60, 0.8), ('end_z', -1, 0.56, 0.9)])
        M['black'] = g.mx(M['black'], g.ss(0.0, 0.004, g.poly(g.ay, g.z, [(0.0, 0.36), (0.7, 0.38), (0.7, 0.44), (0.0, 0.44)])) * g.ss(0.2, 0.4, -g.nx))
        liv = []
        if variant == "police_fr":
            band = side * g.inside(g.z, 0.38, 0.70, 0.002)
            red = side * g.inside(g.z, 0.72, 0.745, 0.002)
            liv = [(band, (0.02, 0.05, 0.25)), (red, (0.55, 0.02, 0.02))]
        elif variant == "police_fr_blue":
            stripe = side * g.inside(g.z, 0.60, 0.64, 0.002)
            liv = [(stripe, (0.8, 0.8, 0.8))]
        M['livery'] = liv
        return M
    paint = V.paint_shader(tag, masks, rough=0.3, metallic=0.25)
    body = V.loft_body("ModernBody", keys, paint, step=0.10)
    V.cut_arches(body, [(XF, 0.325, 0.37, 0.58, 1.2), (XR, 0.325, 0.37, 0.58, 1.2)], V.liner())
    parts = [body]
    bp = V.black_plastic()
    for s in (-1, 1):
        parts.append(V.mirror(f"Mirror{s}", (0.74, s * 0.84, 1.02), s, bp,
                              size=(0.10, 0.20, 0.13), arm=0.07))
        for x in (0.40, -0.70):
            parts.append(V.rbox("Handle", (x, s * 0.885, 0.90), (0.15, 0.03, 0.03), 0.012, bp))
    parts.append(V.plate("PlateF", (2.335, 0, 0.42)))
    parts.append(V.plate("PlateR", (-2.25, 0, 0.62), facing=-1))
    parts.append(V.rbox("Antenna", (-0.95, 0, 1.47), (0.12, 0.03, 0.05), 0.015, bp, sub=1))
    parts.append(V.underbody("Floor", -1.9, 1.9, 0.7, 0.16, 0.30))
    V.cabin_interior(parts, [-0.12, -1.0], 0.38, 0.50, 0.60, 0.86, 0.78)
    body = V.join(parts, "SedanModern")
    me = V.wheel_mesh("modern", R, 0.205, RIM, "alloy5")
    wheels4(body, me, XF, XR, TR, R, RIM)
    col = (0.22, 0.23, 0.25)
    white = V.simple("V_White", (0.85, 0.86, 0.86), 0.35)
    if variant in ("police_fr", "police_fr_blue"):
        V.add_lightbar(body, (-0.30, 0, 1.47), length=1.15)
        tc = white if variant == "police_fr" else white
        for s in (-1, 1):
            t = V.side_text("Txt", "POLICE", -0.30, 0.53 if variant == "police_fr" else 0.75, 0.905, 0.17, tc, s)
            sw = t.modifiers.new("sw", 'SHRINKWRAP'); sw.target = body; sw.offset = 0.002; sw.wrap_mode = 'OUTSIDE_SURFACE'
            V.bake(t); t.parent = body
        col = (0.88, 0.89, 0.9) if variant == "police_fr" else (0.02, 0.05, 0.22)
    elif variant == "unmarked":
        V.add_rotating_beacon(body, (-0.20, 0.38, 1.46), (0.1, 0.25, 1.0), rate=1.6, rad=0.075, height=0.10)
        col = (0.12, 0.13, 0.14)
    elif variant == "taxi":
        sign = V.join([V.rbox("Sign", (0, 0, 0.09), (0.18, 0.62, 0.14), 0.03, V.lens("V_Lens_taxi", (0.95, 0.93, 0.85), (1.0, 0.95, 0.75), False), sub=1),
                       V.rbox("SignBase", (0, 0, 0.012), (0.22, 0.66, 0.025), 0.01, bp)], "TaxiSign")
        sign.parent = body; sign.location = (-0.35, 0, 1.47)
        for s in (-1, 1):
            t = V.text_mesh("TaxiTxt", "TAXI", 0.085, V.simple("V_Black", (0.02, 0.02, 0.02), 0.4))
            t.data.transform(Matrix.Rotation(math.pi / 2, 4, 'X')); t.data.transform(Matrix.Rotation(-math.pi / 2 * s, 4, 'Z'))
            t.data.transform(Matrix.Translation((s * 0.092, 0, 0.09))); t.parent = sign
        col = (0.05, 0.05, 0.055)
    return V._finish(body, "SedanModern" + (variant or "").title().replace("_", ""), col,
                     heads=[(2.2, s * 0.62, 0.72) for s in (-1, 1)])


def taxi(variant=None):
    return _modern_saloon("taxi")


def sedan_modern(variant=None):
    """2007-2011 European 5-door hatchback (default, police_fr, police_fr_blue, unmarked); 'saloon' / 'taxi' give
    the 4-door saloon body."""
    if variant in ("saloon", "taxi"):
        return _modern_saloon(None if variant == "saloon" else "taxi")
    return _modern_hatch(variant)


def _modern_hatch(variant=None):
    XF, XR, R, RIM, TR = 1.27, -1.34, 0.316, 0.203, 0.77
    keys = [S(2.14, 0.34, 0.64, 0.70, 0.76, 0.66, rb=0.1, rs=0.12, crown=0.02, bul=0.0),
            S(2.08, 0.29, 0.72, 0.78, 0.84, 0.74, rb=0.1, rs=0.1, crown=0.03, bul=0.01),
            S(1.85, 0.28, 0.80, 0.86, 0.88, 0.78, rb=0.09, rs=0.08, crown=0.04, bul=0.015, soft=True),
            S(1.18, 0.29, 0.92, 0.98, 0.90, 0.79, rb=0.09, rs=0.06, crown=0.04, bul=0.02),
            S(0.15, 0.30, 0.95, 1.48, 0.90, 0.67, rb=0.09, rs=0.06, rt=0.12, crown=0.05, bul=0.025),
            S(-1.42, 0.31, 0.99, 1.45, 0.90, 0.67, rb=0.09, rs=0.06, rt=0.13, crown=0.05, bul=0.025, soft=True),
            S(-1.96, 0.33, 1.0, 1.09, 0.87, 0.73, rb=0.1, rs=0.07, crown=0.04, bul=0.015),
            S(-2.09, 0.36, 0.97, 1.03, 0.82, 0.70, rb=0.1, rs=0.1, crown=0.03, bul=0.0),
            S(-2.14, 0.42, 0.92, 0.96, 0.74, 0.62, rb=0.08, rs=0.08, crown=0.02, bul=0.0)]
    tag = "V_Paint_Hatch_" + (variant or "plain")

    def masks(g):
        M = V.window_masks(g, [[(-0.45, 0.99), (0.92, 0.99), (0.20, 1.405), (-0.45, 1.405)],
                               [(-1.18, 1.0), (-0.53, 1.0), (-0.53, 1.405), (-1.10, 1.405)],
                               [(-1.62, 1.03), (-1.27, 1.03), (-1.27, 1.38), (-1.40, 1.38)]],
                           front=[(-0.74, 1.0), (0.74, 1.0), (0.58, 1.43), (-0.58, 1.43)],
                           rear=[(-0.64, 1.12), (0.64, 1.12), (0.57, 1.40), (-0.57, 1.40)], seal=0.012)
        side = g.ss(0.55, 0.7, g.any); fr = g.ss(0.15, 0.35, g.nx); rr = g.ss(0.15, 0.35, -g.nx)
        bpil = side * g.inside(g.x, -0.53, -0.45, 0.003) * g.inside(g.z, 1.0, 1.4)
        cpil = side * g.inside(g.x, -1.27, -1.18, 0.003) * g.inside(g.z, 1.0, 1.4)
        M['black'] = g.mx(bpil, cpil)
        M['head'] = g.ss(0.0, 0.004, g.poly(g.ay, g.z, [(0.42, 0.70), (0.86, 0.72), (0.83, 0.85), (0.47, 0.81)])) * g.ss(0.05, 0.2, g.nx) * g.ss(1.75, 1.85, g.x)
        M['tail'] = g.ss(0.0, 0.004, g.poly(g.ay, g.z, [(0.52, 0.93), (0.87, 0.93), (0.85, 1.10), (0.60, 1.10)])) * g.ss(0.05, 0.2, -g.nx) * g.ss(-1.85, -1.95, g.x)
        grille = g.ss(0.0, 0.004, g.poly(g.ay, g.z, [(0.0, 0.66), (0.40, 0.68), (0.38, 0.73), (0.0, 0.73)])) * fr
        lower = g.ss(0.0, 0.004, g.poly(g.ay, g.z, [(0.0, 0.34), (0.58, 0.35), (0.54, 0.52), (0.0, 0.52)])) * fr
        hc = V.E(g, g.math('FRACT', g.z / 0.03).s); hc2 = V.E(g, g.math('FRACT', g.y / 0.03).s)
        mesh = g.mx(g.ss(0.2, 0.1, hc), g.ss(0.2, 0.1, hc2))
        diff = g.ss(0.0, 0.004, g.poly(g.ay, g.z, [(0.0, 0.38), (0.65, 0.40), (0.65, 0.46), (0.0, 0.46)])) * rr
        M['black'] = g.mx(M['black'], g.mx(g.mx(grille, lower) * (0.85 + mesh * 0.15), diff))
        M['rubber'] = g.mx(M['rubber'], side * g.inside(g.z, 0.30, 0.36, 0.004) * g.inside(g.x, -0.95, 0.88))
        M['gap'] = V.gaps(g, [('x', 0.90, 0.37, 0.93), ('x', -0.49, 0.37, 0.98), ('x', -1.20, 0.76, 1.0),
                              ('arc', XR, 0.33, 0.45, -1.21, -0.88, 0.35, 0.77), ('z', 0.37, -0.89, 0.90),
                              ('top_x', 1.20, 0.8), ('top_y', 0.80, 1.2, 2.1), ('top_x', -1.43, 0.75),
                              ('end_z', -1, 0.80, 0.62), ('end_y', -1, 0.62, 0.80, 1.1), ('end_z', 1, 0.58, 0.82),
                              ('end_z', -1, 0.58, 0.85)])
        liv = []
        if variant == "police_fr":
            liv = [(side * g.inside(g.z, 0.38, 0.68, 0.002), (0.02, 0.05, 0.25)),
                   (side * g.inside(g.z, 0.70, 0.725, 0.002), (0.55, 0.02, 0.02))]
        elif variant == "police_fr_blue":
            liv = [(side * g.inside(g.z, 0.60, 0.64, 0.002), (0.8, 0.8, 0.8))]
        M['livery'] = liv
        return M
    paint = V.paint_shader(tag, masks, rough=0.3, metallic=0.25)
    body = V.loft_body("HatchBody", keys, paint, step=0.10)
    V.cut_arches(body, [(XF, 0.325, 0.37, 0.58, 1.2), (XR, 0.325, 0.37, 0.58, 1.2)], V.liner())
    parts = [body]
    bp = V.black_plastic()
    for s in (-1, 1):
        parts.append(V.mirror(f"Mirror{s}", (0.98, s * 0.85, 1.03), s, bp, size=(0.10, 0.20, 0.13), arm=0.07))
        for x in (0.30, -0.80):
            parts.append(V.rbox("Handle", (x, s * 0.885, 0.90), (0.15, 0.03, 0.03), 0.012, bp))
    parts.append(V.plate("PlateF", (2.14, 0, 0.44)))
    parts.append(V.plate("PlateR", (-2.135, 0, 0.70), facing=-1))
    parts.append(V.rbox("Spoiler", (-1.47, 0, 1.465), (0.16, 1.15, 0.035), 0.012, V.black_plastic(), rot=(0, math.radians(8), 0)))
    parts.append(V.rbox("Antenna", (-1.2, 0, 1.49), (0.12, 0.03, 0.05), 0.015, bp, sub=1))
    parts.append(V.underbody("Floor", -1.8, 1.8, 0.7, 0.16, 0.30))
    V.cabin_interior(parts, [-0.15, -1.02], 0.38, 0.52, 0.80, 0.88, 0.78)
    parts.append(V.rbox("Parcel", (-1.62, 0, 1.0), (0.4, 1.4, 0.02), 0.01, V.interior()))
    body = V.join(parts, "Hatch")
    me = V.wheel_mesh("modern", R, 0.205, RIM, "alloy5")
    wheels4(body, me, XF, XR, TR, R, RIM)
    col = (0.55, 0.57, 0.6)
    white = V.simple("V_White", (0.85, 0.86, 0.86), 0.35)
    if variant in ("police_fr", "police_fr_blue"):
        V.add_lightbar(body, (-0.45, 0, 1.50), length=1.15)
        for s in (-1, 1):
            t = V.side_text("Txt", "POLICE", -0.35, 0.53 if variant == "police_fr" else 0.76, 0.905, 0.17, white, s)
            sw = t.modifiers.new("sw", 'SHRINKWRAP'); sw.target = body; sw.offset = 0.002; sw.wrap_mode = 'OUTSIDE_SURFACE'
            V.bake(t); t.parent = body
        col = (0.88, 0.89, 0.9) if variant == "police_fr" else (0.02, 0.05, 0.22)
    elif variant == "unmarked":
        V.add_rotating_beacon(body, (-0.25, 0.38, 1.49), (0.1, 0.25, 1.0), rate=1.6, rad=0.075, height=0.10)
        col = (0.13, 0.14, 0.15)
    return V._finish(body, "Hatch" + (variant or "").title().replace("_", ""), col,
                     heads=[(2.05, s * 0.64, 0.77) for s in (-1, 1)])


# ============================================================================ 8. city bus
def bus_city(variant=None):
    XF, XR, R, RIM, TR = 3.30, -2.60, 0.50, 0.29, 1.05
    W = 1.27; H = 3.0
    keys = [S(6.0, 0.36, 1.05, H - 0.10, W - 0.06, W - 0.10, rb=0.06, rs=0.02, rt=0.14, crown=0.02, bul=0.0),
            S(5.95, 0.33, 1.05, H - 0.02, W - 0.01, W - 0.04, rb=0.07, rs=0.02, rt=0.16, crown=0.03, bul=0.0),
            S(5.75, 0.32, 1.05, H, W, W - 0.03, rb=0.07, rs=0.02, rt=0.16, crown=0.035, bul=0.0),
            S(-5.85, 0.36, 1.05, H, W, W - 0.03, rb=0.07, rs=0.02, rt=0.16, crown=0.035, bul=0.0),
            S(-6.0, 0.40, 1.05, H - 0.05, W - 0.04, W - 0.07, rb=0.06, rs=0.02, rt=0.14, crown=0.02, bul=0.0)]
    doors = [(4.85, 6.0 - 0.15), (0.5, 1.75), (-4.3, -3.05)]

    def masks(g):
        side = g.ss(0.55, 0.7, g.any)
        win = g.inside(g.z, 1.12, 2.62, 0.004) * side
        pillars = None
        xs = [5.65 - k * 1.42 for k in range(9)]
        for x in xs:
            p = g.band(g.x, x, 0.045, 0.004)
            pillars = p if pillars is None else g.mx(pillars, p)
        door_glass = None; door_frame = None
        for (a, b) in doors:
            dgl = side * g.inside(g.x, a + 0.06, b - 0.06) * g.inside(g.z, 0.45, 2.62) * (1.0 - g.band(g.x, (a + b) / 2, 0.035, 0.003))
            dfr = side * g.inside(g.x, a, b) * g.inside(g.z, 0.36, 2.66)
            door_glass = dgl if door_glass is None else g.mx(door_glass, dgl)
            door_frame = dfr if door_frame is None else g.mx(door_frame, dfr)
        # the doors are on the right-hand (kerb) side only: y < 0
        kerb = g.ss(0.02, -0.02, g.y)
        door_glass = door_glass * kerb; door_frame = door_frame * kerb
        glass = g.mx(g.clamp(win * g.inside(g.x, -5.75, 5.6) - pillars), door_glass)
        fr = g.ss(0.3, 0.5, g.nx)
        ws = g.ss(0.0, 0.004, g.poly(g.ay, g.z, [(0.0, 0.95), (1.18, 0.95), (1.18, 2.60), (0.0, 2.60)])) * fr
        dest = g.ss(0.0, 0.004, g.poly(g.ay, g.z, [(0.0, 2.66), (1.0, 2.66), (1.0, 2.88), (0.0, 2.88)])) * fr
        rw = g.ss(0.0, 0.004, g.poly(g.ay, g.z, [(0.0, 1.9), (1.0, 1.9), (1.0, 2.6), (0.0, 2.6)])) * g.ss(0.3, 0.5, -g.nx)
        M = dict(glass=g.mx(g.mx(glass, ws), rw))
        M['black'] = g.mx(g.clamp(door_frame - door_glass) * 0.9, dest)
        M['rubber'] = side * g.inside(g.z, 0.36, 0.48, 0.004) * (1 - door_frame)
        M['head'] = g.ss(0.0, 0.004, g.poly(g.ay, g.z, [(0.78, 0.55), (1.15, 0.55), (1.15, 0.72), (0.78, 0.72)])) * fr
        M['tail'] = g.ss(0.0, 0.004, g.poly(g.ay, g.z, [(0.95, 0.6), (1.2, 0.6), (1.2, 1.3), (0.95, 1.3)])) * g.ss(0.3, 0.5, -g.nx)
        # livery band below the windows
        M['livery'] = [(side * g.inside(g.z, 0.92, 1.05, 0.003), (0.05, 0.25, 0.42))]
        M['gap'] = V.gaps(g, [('z', 1.07, -5.8, 5.8)] + [('x', x, 0.48, 1.07) for x in (-1.5, 3.3 - 1.0, 4.5)])
        return M
    paint = V.paint_shader("V_Paint_Bus", masks, rough=0.32)
    body = V.loft_body("BusBody", keys, paint, step=0.6, extra=0.04)
    V.cut_arches(body, [(XF, 0.52, 0.58, 0.75, 1.5), (XR, 0.52, 0.58, 0.75, 1.5)], V.liner())
    parts = [body]
    bp = V.black_plastic()
    for s in (-1, 1):
        arm = V.sweep("MirArm", [(5.9, s * 1.15, 2.45), (6.25, s * 1.30, 2.55), (6.35, s * 1.30, 2.2)], V.rounded_rect(0.03, 0.03, 0.01, 2), bp)
        parts.append(arm)
        parts.append(V.rbox("Mirror", (6.35, s * 1.32, 1.95), (0.07, 0.22, 0.42), 0.04, bp))
    parts.append(V.rbox("RoofPod", (-1.0, 0, H + 0.12), (6.0, 1.9, 0.22), 0.09, V.paint_shader("V_Paint_BusPod", lambda g: {}, rough=0.35), sub=1))
    parts.append(V.rbox("Bumper", (6.02, 0, 0.45), (0.12, 2.5, 0.22), 0.05, bp))
    parts.append(V.plate("PlateF", (6.09, 0, 0.47)))
    parts.append(V.rbox("Wiper", (6.02, -0.3, 1.25), (0.02, 0.02, 0.9), 0.005, bp, rot=(math.radians(-30), 0, 0)))
    parts.append(V.rbox("Wiper", (6.02, 0.5, 1.25), (0.02, 0.02, 0.9), 0.005, bp, rot=(math.radians(-30), 0, 0)))
    parts.append(V.rbox("EngineGrille", (-5.3, -1.271, 1.5), (0.9, 0.01, 0.6), 0.01, bp))
    parts.append(V.underbody("Floor", -5.5, 5.5, 1.1, 0.25, 0.40))
    fab = V.simple("V_BusSeat", (0.05, 0.08, 0.14), 0.85)
    for k in range(9):
        x = 4.4 - k * 1.05
        for s in (-1, 1):
            if s < 0 and k in (0, 4, 8):
                continue
            parts.append(V.rbox("BusSeat", (x, s * 0.75, 0.88), (0.45, 0.85, 0.12), 0.04, fab))
            parts.append(V.rbox("BusSeatB", (x - 0.24, s * 0.75, 1.2), (0.1, 0.85, 0.62), 0.04, fab))
    parts.append(V.rbox("Grabrail", (0, 0, 2.3), (11.0, 0.04, 0.04), 0.015, V.alu()))
    for x in (4.85, 3.0, 1.15, -0.7, -2.4, -4.1):
        for s in (-1, 1):
            parts.append(V.cylinder("Pole", (x, s * 0.32, 1.45), 0.018, 1.9, V.simple("V_PoleYellow", (0.75, 0.55, 0.05), 0.35), axis='Z', verts=10))
    led = V.simple("V_Dest", (0.02, 0.015, 0.0), 0.4, 0.0, **{'Emission Color': (1.0, 0.55, 0.12, 1), 'Emission Strength': 2.5})
    for txt, y0, sz in (("12", 0.78, 0.17), ("CENTRE", -0.12, 0.15)):
        t = V.text_mesh("Dest", txt, sz, led)
        t.data.transform(Matrix.Rotation(math.pi / 2, 4, 'X')); t.data.transform(Matrix.Rotation(math.pi / 2, 4, 'Z'))
        t.data.transform(Matrix.Translation((6.005, y0, 2.77))); parts.append(t)
    rk = V.paint_shader("V_Paint_BusPod", lambda g: {}, rough=0.35)
    for x, sx in ((4.2, 0.8), (2.6, 0.6), (-4.6, 1.4)):
        parts.append(V.rbox("RoofHatch", (x, 0.3, H + 0.04), (sx, 0.8, 0.1), 0.03, rk))
    V.cabin_interior(parts, [5.0], 0.75, 0.85, 5.6, 1.15, 1.1, bench_rear=False, wheel_r=0.24)
    body = V.join(parts, "BusCity")
    mf = V.wheel_mesh("bus_f", R, 0.28, RIM, "alloy7")
    md = V.wheel_mesh("bus_d", R, 0.28, RIM, "alloy7", dual=True)
    for s in (-1, 1):
        V.add_wheel(body, mf, XF, s * 1.05, R, R, RIM, s)
        V.add_wheel(body, md, XR, s * 1.0, R, R, RIM, s)
    return V._finish(body, "BusCity", (0.86, 0.87, 0.86), heads=[(6.05, s * 0.95, 0.63) for s in (-1, 1)])


# ============================================================================ 8. delivery truck (modern box body)
def box_mat():
    def f():
        def masks(g):
            side = g.ss(0.55, 0.7, g.any)
            seams = None
            for k in range(9):
                x = -3.55 + k * 0.6
                m = g.band(g.x, x, 0.004, 0.002) * side
                seams = m if seams is None else g.mx(seams, m)
            rear = g.ss(0.5, 0.7, -g.nx)
            shutter = rear * g.ss(0.5, 0.4, abs(V.E(g, g.math('FRACT', g.z / 0.09).s) - 0.5))
            return dict(gap=g.mx(seams, shutter * 0.6))
        return V.paint_shader("V_Paint_BoxBody", masks, rough=0.4, fixed_color=(0.88, 0.88, 0.87))
    return f()


def delivery_truck(variant=None):
    XF, XR, R, RIM = 2.55, -1.45, 0.40, 0.225
    parts, heads = cab_1990s(3.40, roof=2.70, tag="CabDT")
    truck_chassis(parts, -3.6, 3.2, 0.82)
    dk, bp = V.steel_dark(), V.black_plastic()
    bx0, bx1 = -3.7, 1.55
    parts.append(V.rbox("Box", ((bx0 + bx1) / 2, 0, 1.15 + 1.2), (bx1 - bx0, 2.48, 2.4), 0.05, box_mat()))
    parts.append(V.rbox("BoxSill", ((bx0 + bx1) / 2, 0, 1.12), (bx1 - bx0, 2.5, 0.12), 0.01, dk))
    for s in (-1, 1):
        parts.append(fender("FenderR", XR, R, R + 0.08, s * 0.80, 0.66, bp))
        parts.append(V.rbox("SideGuard", (-0.4, s * 1.10, 0.78), (2.2, 0.03, 0.10), 0.01, V.alu()))
        parts.append(V.rbox("SideGuard", (-0.4, s * 1.10, 0.55), (2.2, 0.03, 0.10), 0.01, V.alu()))
        parts.append(V.lamp(f"Tail{s}", (bx0 - 0.03, s * 0.98, 0.85), (0.06, 0.32, 0.14), "tail", 0.015, facing=-1))
        parts.append(V.lamp(f"Mark{s}", (bx0 - 0.02, s * 1.15, 3.45), (0.04, 0.08, 0.05), "tail", 0.01, facing=-1))
    parts.append(fender("FenderF", XF, R, R + 0.07, 0.93, 0.38, bp))
    parts.append(fender("FenderF", XF, R, R + 0.07, -0.93, 0.38, bp))
    parts.append(V.rbox("Underrun", (bx0 + 0.05, 0, 0.62), (0.08, 2.1, 0.12), 0.01, dk))
    parts.append(V.rbox("LampBar", (bx0 + 0.02, 0, 0.85), (0.05, 2.2, 0.09), 0.01, dk))
    parts.append(V.cylinder("Tank", (0.65, -0.78, 0.78), 0.26, 1.0, V.alu(), axis='X', verts=32))
    parts.append(V.plate("PlateR", (bx0 - 0.04, 0.0, 0.62), facing=-1))
    body = V.join(parts, "DeliveryTruck")
    mf = V.wheel_mesh("truck_f", R, 0.22, RIM, "truckgrey")
    md = V.wheel_mesh("truck_d", R, 0.22, RIM, "truckgrey", dual=True)
    for s in (-1, 1):
        V.add_wheel(body, mf, XF, s * 0.92, R, R, RIM, s)
        V.add_wheel(body, md, XR, s * 0.98, R, R, RIM, s)
    return V._finish(body, "DeliveryTruck", (0.75, 0.76, 0.78), heads=heads)


# ============================================================================ 9. forklift (counterbalance, ~2.5 t)
def forklift(variant=None):
    pm = V.paint_shader("V_Paint_Forklift", lambda g: {}, rough=0.4)
    dk, bp = V.steel_dark(), V.black_plastic()
    RF, RR = 0.33, 0.27
    XF, XR = 0.42, -1.12
    parts = []
    # chassis: one lofted tub - low operator floor, hood and seat box, heavy rounded counterweight - with wheel arches
    keys = [S(0.66, 0.30, 0.56, 0.62, 0.50, 0.46, rb=0.06, rs=0.04, crown=0.01, bul=0.0),
            S(0.60, 0.20, 0.58, 0.64, 0.56, 0.52, rb=0.07, rs=0.04, crown=0.01, bul=0.0),
            S(-0.12, 0.20, 0.58, 0.64, 0.56, 0.52, rb=0.07, rs=0.04, crown=0.01, bul=0.0),
            S(-0.24, 0.20, 0.92, 0.98, 0.56, 0.52, rb=0.07, rs=0.05, crown=0.02, bul=0.0),
            S(-1.05, 0.20, 0.98, 1.04, 0.57, 0.52, rb=0.07, rs=0.05, crown=0.03, bul=0.004, soft=True),
            S(-1.42, 0.24, 1.02, 1.10, 0.56, 0.50, rb=0.1, rs=0.08, crown=0.03, bul=0.0),
            S(-1.52, 0.34, 0.95, 1.0, 0.48, 0.42, rb=0.1, rs=0.08, crown=0.02, bul=0.0)]
    tub = V.loft_body("Tub", keys, pm, step=0.12, extra=0.025)
    V.cut_arches(tub, [(XF, RF, RF + 0.04, 0.30, 0.8), (XR, RR, RR + 0.04, 0.28, 0.8)], V.liner())
    parts.append(tub)
    # seat, steering column + wheel, dash cowl
    parts.append(V.rbox("Seat", (-0.42, 0, 1.06), (0.45, 0.48, 0.12), 0.05, V.interior(), sub=1))
    parts.append(V.rbox("SeatBack", (-0.66, 0, 1.30), (0.12, 0.46, 0.5), 0.05, V.interior(), sub=1))
    parts.append(V.rbox("Cowl", (0.48, 0, 0.82), (0.24, 0.86, 0.42), 0.06, pm))
    parts.append(V.cylinder("Column", (0.24, 0, 1.18), 0.03, 0.42, dk, axis='Z', verts=12))
    sw = V.lathe("SteerWheel", [(0.15, 0.0), (0.17, 0.01), (0.17, -0.01), (0.15, 0.0)], bp, 24, axis='Z')
    sw.data.transform(Matrix.Translation((0.20, 0, 1.40)) @ Matrix.Rotation(math.radians(-30), 4, 'Y')); parts.append(sw)
    # overhead guard: four posts and a slatted roof
    for x, s in ((0.42, 1), (0.42, -1), (-0.82, 1), (-0.82, -1)):
        top = 2.15
        path = [(x, s * 0.5, 0.7 if x > 0 else 1.0), (x - 0.04 if x > 0 else x, s * 0.5, top)]
        parts.append(V.sweep("Post", path, V.rounded_rect(0.06, 0.06, 0.012, 2), dk))
    parts.append(V.sweep("GuardFrame", [(0.45, -0.5, 2.15), (0.45, 0.5, 2.15), (-0.85, 0.5, 2.15), (-0.85, -0.5, 2.15)],
                         V.rounded_rect(0.06, 0.06, 0.012, 2), dk, closed_path=True, cap=False))
    for k in range(6):
        parts.append(V.rbox("Slat", (0.30 - k * 0.22, 0, 2.15), (0.04, 1.0, 0.04), 0.008, dk))
    parts.append(V.cylinder("LPG", (-1.05, 0, 1.38), 0.16, 0.85, V.simple("V_LPG", (0.75, 0.76, 0.77), 0.35, 0.2), axis='Y', verts=24))
    for s in (-1, 1):
        parts.append(V.round_lamp(f"Work{s}", (0.47, s * 0.45, 2.08), 0.05, 0.05, "head"))
        parts.append(V.round_lamp(f"Tail{s}", (-1.43, s * 0.45, 0.95), 0.04, 0.04, "tail", facing=-1))
        parts.append(V.rbox("Step", (-0.05, s * 0.56, 0.33), (0.35, 0.12, 0.03), 0.01, dk))
    parts.append(V.round_lamp("Beacon", (-0.70, 0, 2.22), 0.05, 0.05, "ind"))
    body = V.join(parts, "Forklift")
    # mast (part 'mast', tilts about Y), carriage + forks (part 'forks', slides in Z)
    mast = V.join([V.rbox("Rail", (0, s * 0.33, 1.1), (0.10, 0.07, 2.2), 0.01, dk) for s in (-1, 1)] +
                  [V.rbox("Rail2", (0.05, s * 0.26, 1.15), (0.08, 0.06, 2.1), 0.01, dk) for s in (-1, 1)] +
                  [V.rbox("Cross", (0.02, 0, z), (0.08, 0.72, 0.08), 0.01, dk) for z in (0.18, 2.15)] +
                  [V.cylinder("LiftRam", (-0.02, 0, 1.0), 0.05, 1.6, V.chrome(), axis='Z', verts=16)] +
                  [V.rbox("Chain", (0.0, s * 0.12, 1.25), (0.02, 0.03, 1.7), 0.004, V.simple("V_Chain", (0.05, 0.05, 0.05), 0.5, 0.8)) for s in (-1, 1)], "Mast")
    mast.parent = body; mast.location = (0.80, 0, 0.05); mast["part"] = "mast"
    forks = V.join([V.rbox("Carriage", (0.12, 0, 0.45), (0.06, 1.0, 0.45), 0.01, dk),
                    V.rbox("Backrest", (0.12, 0, 0.95), (0.03, 1.0, 0.55), 0.005, dk)] +
                   [V.rbox("ForkV", (0.16, s * 0.3, 0.3), (0.05, 0.12, 0.6), 0.008, dk) for s in (-1, 1)] +
                   [V.rbox("ForkH", (0.16 + 0.55, s * 0.3, 0.03), (1.15, 0.12, 0.045), 0.008, dk) for s in (-1, 1)], "Forks")
    forks.parent = mast; forks.location = (0.0, 0, 0.0); forks["part"] = "forks"
    mf = V.wheel_mesh("fork_f", RF, 0.22, 0.17, "black")
    mr = V.wheel_mesh("fork_r", RR, 0.18, 0.14, "black")
    for s in (-1, 1):
        V.add_wheel(body, mf, XF, s * 0.44, RF, RF, 0.17, s)
        V.add_wheel(body, mr, XR, s * 0.42, RR, RR, 0.14, s)
    return V._finish(body, "Forklift", (0.80, 0.42, 0.04), heads=[(0.5, s * 0.45, 2.08) for s in (-1, 1)])


def register(K):
    K["sedan_1940s_us"] = sedan_1940s_us
    K["sedan_modern"] = sedan_modern
    K["taxi"] = taxi
    K["bus_city"] = bus_city
    K["delivery_truck"] = delivery_truck
    K["forklift"] = forklift
