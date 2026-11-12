"""Cars, vans and light trucks for vehicles.py (see that module for the API and conventions)."""
import math
from mathutils import Vector, Matrix
import vehicles as V


def S(x, zb, belt, top, w, wt, **kw):
    d = dict(x=x, zb=zb, belt=belt, top=top, w=w, wt=wt, crown=kw.pop('crown', 0.02), bul=kw.pop('bul', 0.01),
             rb=kw.pop('rb', 0.07), rs=kw.pop('rs', 0.045), rt=kw.pop('rt', 0.07))
    d.update(kw)
    return d


def bumper(name, pts, z, prof_w, prof_h, m, r=0.02, flip=False):
    path = [(x, y, z) for (x, y) in pts]
    if flip:
        path = list(reversed(path))
    return V.sweep(name, path, V.rounded_rect(prof_w, prof_h, r, 3), m)


def wheels4(root, me, xf, xr, y, R, rim_r, z=None):
    z = R if z is None else z
    out = []
    for x in (xf, xr):
        for s in (-1, 1):
            out.append(V.add_wheel(root, me, x, s * y, z, R, rim_r, s))
    return out


# ============================================================================ 1. Lada-like 1990s Soviet saloon
def sedan_1990s_soviet(variant=None):
    militia = variant == "militia"
    XF, XR, R, RIM, TR = 1.29, -1.13, 0.287, 0.165, 0.69
    keys = [S(2.02, 0.39, 0.79, 0.815, 0.775, 0.67, rb=0.035, rs=0.025, crown=0.008),
            S(2.0, 0.35, 0.80, 0.832, 0.80, 0.695, rb=0.05, rs=0.03, crown=0.012),
            S(1.87, 0.33, 0.812, 0.842, 0.80, 0.70, crown=0.016),
            S(0.66, 0.30, 0.86, 0.902, 0.81, 0.72, crown=0.02),
            S(0.57, 0.30, 0.864, 0.93, 0.81, 0.71, crown=0.02),
            S(-0.02, 0.30, 0.875, 1.405, 0.81, 0.615, crown=0.03, rt=0.075),
            S(-1.02, 0.30, 0.885, 1.395, 0.81, 0.615, crown=0.03, rt=0.075),
            S(-1.47, 0.305, 0.89, 0.955, 0.81, 0.71, crown=0.015),
            S(-1.89, 0.32, 0.895, 0.96, 0.80, 0.70, crown=0.012),
            S(-1.98, 0.35, 0.885, 0.95, 0.80, 0.695, rb=0.05, rs=0.03, crown=0.01),
            S(-2.0, 0.39, 0.875, 0.935, 0.775, 0.67, rb=0.035, rs=0.025, crown=0.006)]
    tag = "V_Paint_Lada" + ("_militia" if militia else "")

    def masks(g):
        M = V.window_masks(g, [[(-0.38, 0.905), (0.47, 0.905), (-0.05, 1.335), (-0.38, 1.335)],
                               [(-1.17, 0.905), (-0.45, 0.905), (-0.45, 1.335), (-0.99, 1.335)]],
                           front=[(-0.64, 0.955), (0.64, 0.955), (0.545, 1.375), (-0.545, 1.375)],
                           rear=[(-0.62, 0.99), (0.62, 0.99), (0.535, 1.36), (-0.535, 1.36)], seal=0.016, trim=0.007)
        side = g.ss(0.55, 0.7, g.any)
        rub = g.inside(g.z, 0.585, 0.625, 0.003) * side * g.inside(g.x, -1.98, 1.98)
        ins = g.inside(g.z, 0.601, 0.609, 0.002) * side * g.inside(g.x, -1.98, 1.98)
        drip = g.inside(g.z, 1.345, 1.36, 0.003) * g.ss(0.2, 0.35, g.any) * g.inside(g.x, -1.0, -0.04)
        M['rubber'] = g.mx(M['rubber'], rub)
        M['chrome'] = g.mx(g.mx(M['chrome'], ins), drip)
        M['gap'] = V.gaps(g, [('x', 0.60, 0.34, 0.866), ('x', -0.415, 0.34, 0.876), ('z', 0.345, -0.745, 0.60),
                              ('x', -1.075, 0.69, 0.886), ('arc', -1.13, 0.30, 0.39, -1.08, -0.70, 0.33, 0.70),
                              ('top_x', 0.63, 0.735), ('top_y', 0.735, 0.63, 2.0), ('top_x', -1.50, 0.735),
                              ('top_y', 0.735, -1.98, -1.50), ('end_y', -1, 0.33, 0.58, 0.93), ('end_z', -1, 0.58, 0.33)])
        if militia:
            band = g.inside(g.z, 0.64, 0.76, 0.002) * side * g.inside(g.x, -1.99, 1.99)
            M['livery'] = [(band, (0.02, 0.07, 0.32))]
        return M
    paint = V.paint_shader(tag, masks, rough=0.34)
    body = V.loft_body("LadaBody", keys, paint, step=0.10)
    V.cut_arches(body, [(XF, 0.292, 0.33, 0.53, 1.1), (XR, 0.292, 0.33, 0.53, 1.1)], V.liner())
    ch, rb, bp = V.chrome(), V.rubber(), V.black_plastic()
    parts = [body]
    # bumpers: chrome bars with thick black rubber overlay, wrapping round the corners
    fpts = [(1.80, -0.80), (1.98, -0.79), (2.06, -0.72), (2.085, -0.5), (2.09, 0), (2.085, 0.5), (2.06, 0.72), (1.98, 0.79), (1.80, 0.80)]
    rpts = [(-x - 0.02, y) for (x, y) in fpts]
    parts += [bumper("BumpF", fpts, 0.445, 0.045, 0.10, ch, 0.015),
              bumper("BumpFR", [(x + 0.012, y * 1.003) for x, y in fpts], 0.462, 0.04, 0.042, rb, 0.012),
              bumper("BumpR", rpts, 0.475, 0.045, 0.10, ch, 0.015, flip=True),
              bumper("BumpRR", [(x - 0.012, y * 1.003) for x, y in rpts], 0.492, 0.04, 0.042, rb, 0.012, flip=True)]
    # grille: chrome surround, black recess, vertical chrome slats
    gp = [(2.035, y, z) for (y, z) in V.rounded_rect(0.52, 0.235, 0.02, 2)]
    gp = [(2.035, p[0], p[1] + 0.665) for p in V.rounded_rect(0.50, 0.235, 0.02, 2)]
    parts.append(V.sweep("GrilleRing", gp, V.rounded_rect(0.02, 0.016, 0.005, 2), ch, up=(1, 0, 0), closed_path=True, cap=False))
    parts.append(V.rbox("GrilleBack", (2.015, 0, 0.665), (0.03, 0.49, 0.225), 0.01, bp))
    for k in range(13):
        parts.append(V.rbox("Slat", (2.034, -0.22 + k * 0.0367, 0.665), (0.012, 0.007, 0.21), 0.002, ch))
    parts.append(V.rbox("GrilleBar", (2.04, 0, 0.665), (0.014, 0.48, 0.012), 0.003, ch))
    # head lamps (rectangular, chrome trimmed), indicators below the bumper, tail lamp clusters
    heads = []
    for s in (-1, 1):
        parts.append(V.lamp(f"Head{s}", (2.03, s * 0.515, 0.665), (0.05, 0.245, 0.175), "head", 0.012))
        parts.append(V.sweep("HeadTrim", [(2.046, s * 0.515 + p[0], 0.665 + p[1]) for p in V.rounded_rect(0.255, 0.185, 0.014, 2)],
                             V.rounded_rect(0.012, 0.01, 0.003, 2), ch, up=(1, 0, 0), closed_path=True, cap=False))
        heads.append((2.06, s * 0.505, 0.665))
        parts.append(V.lamp(f"Ind{s}", (2.06, s * 0.56, 0.355), (0.04, 0.16, 0.05), "ind", 0.01))
        parts.append(V.lamp(f"TailR{s}", (-2.0, s * 0.665, 0.755), (0.05, 0.20, 0.17), "tail", 0.01, facing=-1))
        parts.append(V.lamp(f"TailA{s}", (-2.0, s * 0.515, 0.755), (0.05, 0.10, 0.17), "ind", 0.008, facing=-1))
        parts.append(V.lamp(f"TailW{s}", (-2.0, s * 0.41, 0.755), (0.05, 0.11, 0.17), "rev", 0.008, facing=-1))
        parts.append(V.sweep("TailTrim", [(-2.018, s * 0.54 + p[0], 0.755 + p[1]) for p in V.rounded_rect(0.42, 0.185, 0.012, 2)],
                             V.rounded_rect(0.01, 0.008, 0.003, 2), ch, up=(1, 0, 0), closed_path=True, cap=False))
        # mirrors, door handles, wheel-arch lips
        parts.append(V.mirror(f"Mirror{s}", (0.47, s * 0.79, 0.955), s, ch, size=(0.05, 0.13, 0.085), arm=0.06, m_arm=ch))
        for x in (0.33, -0.66):
            parts.append(V.rbox("Handle", (x, s * 0.806, 0.805), (0.11, 0.022, 0.022), 0.008, ch))
    parts.append(V.plate("PlateF", (2.115, 0, 0.43)))
    parts.append(V.plate("PlateR", (-2.012, 0, 0.62), facing=-1))
    # wipers, aerial, exhaust, floor pan
    for y in (-0.33, 0.12):
        w = V.rbox("Wiper", (0.535, y, 0.948), (0.014, 0.46, 0.01), 0.004, bp, rot=(0, math.radians(-39), 0)); parts.append(w)
    parts.append(V.cylinder("Aerial", (1.55, 0.70, 1.15), 0.0025, 0.62, ch, axis='Z', verts=8))
    parts.append(V.cylinder("Exhaust", (-1.80, -0.42, 0.25), 0.024, 0.55, ch, axis='X', verts=16))
    parts.append(V.underbody("Floor", -1.5, 1.6, 0.5, 0.21, 0.31))
    V.cabin_interior(parts, [-0.06, -0.85], 0.36, 0.48, 0.42, 0.80, 0.70)
    body = V.join(parts, "Sedan1990s")
    me = V.wheel_mesh("lada", R, 0.175, RIM, "steel")
    wheels4(body, me, XF, XR, TR, R, RIM)
    if militia:
        V.add_lightbar(body, (-0.35, 0, 1.43), length=0.95)
        for s in (-1, 1):
            t = V.side_text("Txt", "МИЛИЦИЯ", -0.05, 0.70, 0.823, 0.105, V.simple("V_White", (0.85, 0.86, 0.86), 0.35), s)
            sw = t.modifiers.new("sw", 'SHRINKWRAP'); sw.target = body; sw.offset = 0.002; sw.wrap_mode = 'OUTSIDE_SURFACE'
            V.bake(t); t.parent = body
        col = (0.82, 0.83, 0.84)
    else:
        col = (0.62, 0.56, 0.42)
    return V._finish(body, "Sedan1990s" + ("Militia" if militia else ""), col, heads=heads)


def register(K):
    K["sedan_1990s_soviet"] = sedan_1990s_soviet


def _mesh_guard_mat():
    m, g = V._newmat("V_MeshGuard")
    gy = V.E(g, g.math('FRACT', g.y / 0.045).s); gz = V.E(g, g.math('FRACT', g.z / 0.045).s)
    wire = g.mx(g.ss(0.42, 0.36, abs(gy - 0.5)), g.ss(0.42, 0.36, abs(gz - 0.5)))
    wire = g.mx(g.ss(0.36, 0.44, abs(gy - 0.5)), g.ss(0.36, 0.44, abs(gz - 0.5)))
    col = g.mix_col(wire, (0.02, 0.02, 0.022), (0.42, 0.43, 0.44))
    p = g.bsdf((0.3, 0.3, 0.3), 0.4, 0.0); g.L.new(col, p.inputs['Base Color']); g.link(wire * 0.8, p.inputs['Metallic'])
    g.out(p); return m


# ============================================================================ 2. 1990s panel van (Transit Mk3-like)
def van_1990s(variant=None):
    XF, XR, R, RIM, TR = 1.45, -1.385, 0.31, 0.178, 0.82
    keys = [S(2.33, 0.46, 0.80, 0.84, 0.90, 0.80, rb=0.05, rs=0.04, crown=0.01),
            S(2.30, 0.42, 0.86, 0.935, 0.945, 0.845, rs=0.04, crown=0.015),
            S(2.14, 0.40, 0.93, 1.005, 0.965, 0.885, crown=0.02),
            S(1.52, 0.40, 1.075, 1.13, 0.97, 0.90, crown=0.02),
            S(0.78, 0.40, 1.10, 1.955, 0.97, 0.895, crown=0.035, rt=0.09),
            S(-2.25, 0.42, 1.12, 1.965, 0.97, 0.895, crown=0.035, rt=0.09),
            S(-2.33, 0.46, 1.10, 1.93, 0.93, 0.855, rb=0.05, rs=0.04, crown=0.03)]

    def masks(g):
        M = V.window_masks(g, [[(0.28, 1.155), (1.40, 1.155), (0.82, 1.85), (0.28, 1.85)]],
                           front=[(-0.83, 1.17), (0.83, 1.17), (0.79, 1.88), (-0.79, 1.88)],
                           rear=[[(0.05, 1.32), (0.80, 1.32), (0.78, 1.82), (0.05, 1.82)],
                                 [(-0.80, 1.32), (-0.05, 1.32), (-0.05, 1.82), (-0.78, 1.82)]], seal=0.02)
        side = g.ss(0.55, 0.7, g.any)
        rail = g.inside(g.z, 1.50, 1.535, 0.003) * side * g.inside(g.x, -2.22, -0.90)
        strip = g.inside(g.z, 0.70, 0.78, 0.003) * side * g.inside(g.x, -2.3, 2.3)
        M['rubber'] = g.mx(g.mx(M['rubber'], rail), strip)
        M['gap'] = V.gaps(g, [('x', 1.47, 0.72, 1.10), ('arc', XF, 0.31, 0.41, 1.04, 1.48, 0.42, 0.73),
                              ('z', 0.43, 0.22, 1.04), ('x', 0.25, 0.43, 1.93), ('x', 0.20, 0.43, 1.93),
                              ('x', -0.90, 0.43, 1.93), ('top_x', 1.53, 0.88), ('top_y', 0.895, 1.53, 2.28),
                              ('end_z', 1, 0.955, 0.89), ('end_y', -1, 0.0, 0.47, 1.92), ('end_y', -1, 0.885, 0.47, 1.90),
                              ('top_x', -2.27, 0.86)])
        return M
    paint = V.paint_shader("V_Paint_Van", masks, rough=0.36)
    body = V.loft_body("VanBody", keys, paint, step=0.12)
    V.cut_arches(body, [(XF, 0.315, 0.36, 0.60, 1.2), (XR, 0.315, 0.36, 0.60, 1.2)], V.liner())
    ch, rb, bp = V.chrome(), V.rubber(), V.black_plastic()
    parts = [body]
    fpts = [(2.0, -0.97), (2.22, -0.965), (2.33, -0.90), (2.375, -0.6), (2.385, 0), (2.375, 0.6), (2.33, 0.90), (2.22, 0.965), (2.0, 0.97)]
    parts.append(bumper("BumpF", fpts, 0.56, 0.09, 0.20, bp, 0.03))
    rpts = [(-2.10, -0.965), (-2.36, -0.95), (-2.39, -0.6), (-2.395, 0), (-2.39, 0.6), (-2.36, 0.95), (-2.10, 0.965)]
    parts.append(bumper("BumpR", list(reversed(rpts)), 0.53, 0.08, 0.17, bp, 0.025))
    # grille: black slatted panel between the head lamps (no badge)
    parts.append(V.rbox("Grille", (2.30, 0, 0.87), (0.04, 0.84, 0.17), 0.02, bp))
    for k in range(5):
        parts.append(V.rbox("Slat", (2.322, 0, 0.805 + k * 0.032), (0.01, 0.80, 0.012), 0.004, V.simple("V_DarkGrey", (0.06, 0.06, 0.065), 0.4)))
    heads = []
    for s in (-1, 1):
        parts.append(V.lamp(f"Head{s}", (2.295, s * 0.60, 0.87), (0.06, 0.34, 0.175), "head", 0.02))
        parts.append(V.lamp(f"Ind{s}", (2.265, s * 0.855, 0.87), (0.05, 0.12, 0.175), "ind", 0.02))
        heads.append((2.33, s * 0.64, 0.865))
        parts.append(V.lamp(f"Tail{s}", (-2.335, s * 0.885, 0.80), (0.05, 0.13, 0.36), "tail", 0.02, facing=-1))
        parts.append(V.lamp(f"TailI{s}", (-2.335, s * 0.885, 1.02), (0.05, 0.13, 0.08), "ind", 0.015, facing=-1))
        parts.append(V.mirror(f"Mirror{s}", (1.36, s * 0.96, 1.42), s, bp, size=(0.07, 0.17, 0.27), arm=0.12))
        parts.append(V.rbox("Handle", (0.42, s * 0.975, 1.03), (0.15, 0.03, 0.04), 0.012, bp))
        parts.append(V.rbox("SlideHandle", (0.05, s * 0.975, 1.03), (0.15, 0.03, 0.04), 0.012, bp))
        parts.append(V.rbox("Step", (0.0, s * 0.94, 0.38), (1.1, 0.12, 0.05), 0.015, bp))
    for y in (-0.42, 0.12):
        parts.append(V.rbox("Wiper", (1.50, y, 1.17), (0.016, 0.58, 0.012), 0.004, bp, rot=(0, math.radians(-50), 0)))
    parts.append(V.rbox("RearHandle", (-2.345, 0.12, 1.15), (0.03, 0.14, 0.035), 0.01, bp))
    parts.append(V.plate("PlateF", (2.43, 0, 0.55)))
    parts.append(V.plate("PlateR", (-2.44, 0, 0.53), facing=-1))
    parts.append(V.cylinder("Exhaust", (-2.30, -0.55, 0.30), 0.03, 0.2, V.steel_dark(), axis='X', verts=16))
    parts.append(V.underbody("Floor", -2.0, 2.0, 0.62, 0.24, 0.42))
    V.cabin_interior(parts, [0.82], 0.45, 0.80, 1.30, 1.10, 0.84)
    parts.append(V.rbox("Bulkhead", (0.24, 0, 1.2), (0.04, 1.8, 1.5), 0.02, V.interior()))
    # steel mesh guard behind the rear-door glass, and a ply-lined cargo floor
    parts.append(V.rbox("MeshGuard", (-2.22, 0, 1.56), (0.02, 1.7, 0.6), 0.005, V.mat("V_MeshGuard", _mesh_guard_mat)))
    parts.append(V.rbox("CargoFloor", (-0.95, 0, 0.62), (2.5, 1.75, 0.03), 0.01, V.simple("V_Ply", (0.32, 0.24, 0.15), 0.8)))
    body = V.join(parts, "Van1990s")
    me = V.wheel_mesh("van", R, 0.195, RIM, "steel")
    wheels4(body, me, XF, XR, TR, R, RIM)
    return V._finish(body, "Van1990s", (0.86, 0.87, 0.87), heads=heads)



# ============================================================================ 3. 1990s cab-over light truck + flatbed
def plank_mat(name="V_DropSide", col=(0.62, 0.63, 0.64), pitch=0.09, metal=0.8):
    """Aluminium drop-side boards: horizontal plank grooves and light wear."""
    def f():
        m, g = V._newmat(name)
        gr = V.E(g, g.math('FRACT', g.z / pitch).s)
        groove = g.ss(0.06, 0.0, gr) + g.ss(0.94, 1.0, gr)
        wear = g.noise(6.0, 5.0)
        p = g.bsdf(col, 0.38, metal)
        g.link(0.3 + wear * 0.25 + groove * 0.3, p.inputs['Roughness'])
        g.L.new(g.bump(-groove, 0.7, 0.004), p.inputs['Normal'])
        g.out(p); return m
    return V.mat(name, f)


def deck_mat():
    def f():
        m, g = V._newmat("V_DeckWood")
        gr = V.E(g, g.math('FRACT', g.y / 0.16).s)
        groove = g.ss(0.04, 0.0, gr) + g.ss(0.96, 1.0, gr)
        n = g.noise(2.0, 8.0, 0.7)
        col = g.mix_col(n, (0.12, 0.09, 0.06), (0.22, 0.17, 0.11))
        col = g.mix_col(groove, col, (0.02, 0.02, 0.02))
        p = g.bsdf((0.2, 0.15, 0.1), 0.8, 0.0); g.L.new(col, p.inputs['Base Color'])
        g.L.new(g.bump(-groove + n * 0.2, 0.5, 0.004), p.inputs['Normal'])
        g.out(p); return m
    return V.mat("V_DeckWood", f)


def cab_1990s(x_front=3.40, width=2.20, roof=2.62, floor=0.93, depth=1.62, tag="Cab90"):
    """Cab-over truck cab, lofted (rounded corners, slight rake), with windscreen, door glass, grille band and lamps.
    Returns the list of parts and the head-lamp positions."""
    w = width / 2; xb = x_front - depth
    keys = [S(x_front, floor + 0.06, 1.62, roof - 0.16, w - 0.16, w - 0.21, rb=0.1, rs=0.03, rt=0.12, crown=0.02, bul=0.0),
            S(x_front - 0.03, floor + 0.02, 1.62, roof - 0.06, w - 0.06, w - 0.11, rb=0.12, rs=0.03, rt=0.16, crown=0.03, bul=0.0),
            S(x_front - 0.12, floor, 1.62, roof - 0.01, w - 0.01, w - 0.065, rb=0.12, rs=0.03, rt=0.18, crown=0.035, bul=0.004),
            S(x_front - 0.30, floor, 1.62, roof, w, w - 0.06, rb=0.12, rs=0.03, rt=0.18, crown=0.035, bul=0.006, soft=True),
            S(xb + 0.08, floor, 1.62, roof, w, w - 0.06, rb=0.12, rs=0.03, rt=0.18, crown=0.035, bul=0.006),
            S(xb, floor + 0.05, 1.62, roof - 0.08, w - 0.06, w - 0.11, rb=0.1, rs=0.03, rt=0.12, crown=0.02, bul=0.0)]
    xd0, xd1 = xb + 0.20, x_front - 0.12

    def masks(g):
        M = V.window_masks(g, [[(xd0 + 0.04, 1.66), (xd1 - 0.06, 1.66), (xd1 - 0.06, roof - 0.17), (xd0 + 0.04, roof - 0.17)]],
                           front=[(-(w - 0.13), 1.66), (w - 0.13, 1.66), (w - 0.17, roof - 0.2), (-(w - 0.17), roof - 0.2)],
                           rear=[(-0.5, 1.75), (0.5, 1.75), (0.5, 2.15), (-0.5, 2.15)], seal=0.022)
        side = g.ss(0.55, 0.7, g.any)
        M['gap'] = V.gaps(g, [('x', xd0, floor + 0.05, roof - 0.12), ('x', xd1, floor + 0.05, roof - 0.12),
                              ('z', floor + 0.06, xd0, xd1), ('end_z', 1, 1.50, w - 0.1), ('end_z', 1, 1.12, w - 0.12),
                              ('end_y', 1, w - 0.12, 1.12, 1.50)])
        split = g.band(g.y, 0.0, 0.03, 0.003) * g.ss(0.5, 0.7, g.nx) * g.inside(g.z, 1.62, roof - 0.15)
        M['glass'] = g.clamp(M['glass'] - split); M['rubber'] = g.mx(M['rubber'], split)
        frontface = g.ss(0.5, 0.7, g.nx)
        grille = frontface * g.inside(g.z, 1.18, 1.46, 0.004) * g.ss(w - 0.32, w - 0.34, g.ay)
        slats = grille * g.ss(0.35, 0.5, V.E(g, g.math('FRACT', g.z / 0.035).s))
        M['black'] = g.mx(grille * 0.85, slats)
        return M
    paint = V.paint_shader("V_Paint_" + tag, masks, rough=0.34)
    cab = V.loft_body(tag, keys, paint, step=0.12, extra=0.02)
    bp = V.black_plastic()
    parts = [cab]
    # bumper with lamps, steps, mirrors on arms, wipers, roof marker lamps, sun visor
    parts.append(V.rbox("Bumper", (x_front + 0.02, 0, floor - 0.13), (0.22, width + 0.04, 0.30), 0.05, V.simple("V_TruckGrey", (0.12, 0.12, 0.125), 0.5)))
    heads = []
    for s in (-1, 1):
        parts.append(V.lamp(f"Head{s}", (x_front + 0.12, s * (w - 0.30), floor - 0.10), (0.06, 0.34, 0.15), "head", 0.02))
        parts.append(V.lamp(f"Ind{s}", (x_front + 0.12, s * (w - 0.07), floor - 0.10), (0.06, 0.10, 0.15), "ind", 0.02))
        heads.append((x_front + 0.15, s * (w - 0.30), floor - 0.10))
        for k in range(2):
            parts.append(V.rbox("Step", (xd0 + 0.55, s * (w - 0.06), floor - 0.30 - k * 0.28), (0.45, 0.22, 0.04), 0.01, V.steel_dark()))
        arm = V.sweep("MirArm", [(x_front - 0.25, s * (w - 0.02), 2.25), (x_front - 0.05, s * (w + 0.18), 2.30), (x_front - 0.05, s * (w + 0.22), 1.65)],
                      V.rounded_rect(0.025, 0.025, 0.01, 2), bp)
        parts.append(arm)
        parts.append(V.rbox("Mirror", (x_front - 0.07, s * (w + 0.24), 2.02), (0.06, 0.20, 0.36), 0.03, bp))
        parts.append(V.rbox("MirrorG", (x_front - 0.105, s * (w + 0.24), 2.02), (0.01, 0.17, 0.32), 0.01, V.chrome()))
        parts.append(V.rbox("Handle", (xd0 + 0.2, s * (w + 0.005), 1.55), (0.18, 0.03, 0.04), 0.012, bp))
        parts.append(V.lamp(f"Mark{s}", (x_front - 0.05, s * (w - 0.25), roof + 0.035), (0.05, 0.10, 0.05), "ind", 0.015))
    for y in (-0.5, 0.25):
        parts.append(V.rbox("Wiper", (x_front + 0.005, y, 1.70), (0.016, 0.012, 0.62), 0.004, bp, rot=(math.radians(70), 0, 0)))
    parts.append(V.plate("PlateF", (x_front + 0.14, 0, floor - 0.32)))
    parts.append(V.rbox("Visor", (x_front + 0.06, 0, roof - 0.13), (0.30, width - 0.25, 0.035), 0.012, bp, rot=(0, math.radians(8), 0)))
    for s_ in (-1, 1):
        parts.append(V.rbox("VisorArm", (x_front - 0.02, s_ * (w - 0.2), roof - 0.10), (0.16, 0.03, 0.03), 0.01, bp))
    V.cabin_interior(parts, [x_front - 0.95], 0.5, floor + 0.55, x_front - 0.36, floor + 0.62, w - 0.14, bench_rear=False, wheel_r=0.23)
    return parts, heads


def truck_chassis(parts, x0, x1, z, rail_w=0.42):
    dk = V.steel_dark()
    for s in (-1, 1):
        parts.append(V.rbox("Rail", ((x0 + x1) / 2, s * rail_w, z), (x1 - x0, 0.08, 0.24), 0.01, dk))
    for x in (x0 + 0.3, (x0 + x1) / 2, x1 - 0.3):
        parts.append(V.rbox("Cross", (x, 0, z), (0.10, rail_w * 2, 0.18), 0.01, dk))


def fender(name, x, z, r, y, width, m):
    """Quarter-round mudguard shell over a wheel."""
    pts = [(x + r * math.cos(a), z + r * math.sin(a)) for a in [math.radians(d) for d in range(0, 181, 15)]]
    path = [(px, y, pz) for (px, pz) in pts]
    return V.sweep(name, path, V.rounded_rect(width, 0.012, 0.004, 1), m, up=(0, 1, 0))


def flatbed_truck_1990s(variant=None):
    XF, XR, R, RIM = 2.55, -1.45, 0.40, 0.225
    parts, heads = cab_1990s(3.40)
    truck_chassis(parts, -3.55, 3.2, 0.82)
    dk, bp = V.steel_dark(), V.black_plastic()
    # flatbed: wooden deck on a steel frame, aluminium drop sides, a tall headboard with a rack
    x0, x1, BW, DZ = -3.65, 1.62, 2.30, 1.22
    parts.append(V.rbox("Deck", ((x0 + x1) / 2, 0, DZ), (x1 - x0, BW, 0.06), 0.008, deck_mat()))
    parts.append(V.rbox("DeckFrame", ((x0 + x1) / 2, 0, DZ - 0.07), (x1 - x0, BW + 0.02, 0.10), 0.01, dk))
    for x in [x0 + 0.25 + k * 0.6 for k in range(9)]:
        parts.append(V.rbox("Bearer", (x, 0, DZ - 0.17), (0.08, BW - 0.1, 0.12), 0.005, dk))
    al = plank_mat()
    H = 0.48
    for s in (-1, 1):
        for k in range(3):
            L = (x1 - x0 - 0.12) / 3
            xc = x0 + 0.06 + L * (k + 0.5)
            parts.append(V.rbox("DropSide", (xc, s * (BW / 2 - 0.02), DZ + 0.03 + H / 2), (L - 0.03, 0.04, H), 0.008, al))
        for k in range(4):
            xp = x0 + 0.04 + k * (x1 - x0 - 0.08) / 3
            parts.append(V.rbox("Post", (xp, s * (BW / 2 - 0.01), DZ + 0.03 + H / 2), (0.05, 0.06, H + 0.02), 0.008, dk))
    parts.append(V.rbox("Tailgate", (x0 + 0.02, 0, DZ + 0.03 + H / 2), (0.04, BW - 0.06, H), 0.008, al))
    parts.append(V.rbox("Headboard", (x1 - 0.03, 0, DZ + 0.55), (0.05, BW, 1.1), 0.01, al))
    for y in (-0.9, -0.3, 0.3, 0.9):
        parts.append(V.rbox("RackBar", (x1 - 0.03, y, DZ + 1.22), (0.05, 0.04, 0.25), 0.005, dk))
    parts.append(V.rbox("RackTop", (x1 - 0.03, 0, DZ + 1.34), (0.06, BW, 0.05), 0.01, dk))
    # running gear: fuel tank, battery box, mudguards, under-run bar, tail lamps
    parts.append(V.cylinder("Tank", (0.65, -0.78, 0.78), 0.26, 1.0, V.alu(), axis='X', verts=32))
    parts.append(V.rbox("Battery", (0.65, 0.78, 0.72), (0.7, 0.4, 0.45), 0.02, bp))
    parts.append(fender("FenderF", XF, R, R + 0.07, 0.93, 0.38, bp))
    parts.append(fender("FenderF", XF, R, R + 0.07, -0.93, 0.38, bp))
    for s in (-1, 1):
        parts.append(fender("FenderR", XR, R, R + 0.08, s * 0.80, 0.66, bp))
        parts.append(V.rbox("Flap", (XR - 0.52, s * 0.80, 0.48), (0.01, 0.6, 0.58), 0.005, V.rubber()))
        parts.append(V.lamp(f"Tail{s}", (x0 - 0.03, s * 0.92, 0.80), (0.06, 0.30, 0.12), "tail", 0.015, facing=-1))
        parts.append(V.rbox("SideGuard", (-0.4, s * 1.08, 0.78), (2.2, 0.03, 0.10), 0.01, V.alu()))
    parts.append(V.rbox("Underrun", (x0 + 0.05, 0, 0.62), (0.08, 2.1, 0.12), 0.01, dk))
    parts.append(V.rbox("LampBar", (x0 + 0.02, 0, 0.80), (0.05, 2.12, 0.09), 0.01, dk))
    for s in (-1, 1):
        parts.append(V.rbox("LampHanger", (x0 + 0.04, s * 0.85, 0.89), (0.05, 0.06, 0.20), 0.005, dk))
    parts.append(V.plate("PlateR", (x0 - 0.04, 0.0, 0.80), facing=-1))
    parts.append(V.cylinder("Exhaust", (1.3, 0.75, 0.68), 0.05, 0.9, dk, axis='X', verts=16))
    body = V.join(parts, "FlatbedTruck1990s")
    mf = V.wheel_mesh("truck_f", R, 0.22, RIM, "truckgrey")
    md = V.wheel_mesh("truck_d", R, 0.22, RIM, "truckgrey", dual=True)
    for s in (-1, 1):
        V.add_wheel(body, mf, XF, s * 0.92, R, R, RIM, s)
        V.add_wheel(body, md, XR, s * 0.98, R, R, RIM, s)
    return V._finish(body, "FlatbedTruck1990s", (0.62, 0.08, 0.06), heads=heads)


def register(K):
    K["sedan_1990s_soviet"] = sedan_1990s_soviet
    K["van_1990s"] = van_1990s
    K["flatbed_truck_1990s"] = flatbed_truck_1990s
