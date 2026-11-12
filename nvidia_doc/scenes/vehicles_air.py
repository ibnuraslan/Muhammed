"""cargo_plane for vehicles.py: a 1980s US military strategic airlifter in the C-141 Starlifter style (generic, no
real markings): long circular fuselage with an upswept tail, high swept wing with anhedral, T-tail, four podded fan
engines on pylons, main gear in side sponsons, a rear ramp plus clamshell doors and a dark cargo hold with rollers.

Moving parts: part(root, 'ramp') (rotates about local Y; vehicles.set_ramp(root, t) drives everything),
part(root, 'doors') (an empty holding 'door_l' / 'door_r', which rotate about local X).
    vehicles.set_ramp(root, 0.0)   # closed          vehicles.set_ramp(root, 1.0)   # doors open, ramp on the ground
"""
import math
import bpy, bmesh
from mathutils import Vector, Matrix
import vehicles as V

RAMP_HINGE = (-8.0, 1.30)          # (x, z) of the ramp hinge, at hold-floor level
RAMP_LEN = 5.2
CUT_END = (-19.5, 4.25)            # aft end of the ramp / door opening (the cut plane runs hinge -> here)
RAMP_CLOSED = math.degrees(math.atan2(CUT_END[1] - RAMP_HINGE[1], RAMP_HINGE[0] - CUT_END[0]))
RAMP_OPEN = -math.degrees(math.asin(RAMP_HINGE[1] / RAMP_LEN))
DOOR_SIGN = -1.0                   # swing direction of the clamshell doors about their hinge axes


# ============================================================================ geometry helpers
def _finish_shell(o):
    bm = bmesh.new(); bm.from_mesh(o.data)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    if bm.calc_volume(signed=True) < 0:
        bmesh.ops.reverse_faces(bm, faces=bm.faces)
    bm.to_mesh(o.data); bm.free()
    return o


def loft_ellipse(name, st, m, ring=40, levels=1, n=2.0, cap=True):
    """Superellipse cross-sections along X. st: [(x, zc, a(half width), b(half height))] front first."""
    vs, fs = [], []
    for (x, zc, a, b) in st:
        for k in range(ring):
            t = 2 * math.pi * k / ring
            c, s = math.cos(t), math.sin(t)
            vs.append((x, a * math.copysign(abs(c) ** (2 / n), c), zc + b * math.copysign(abs(s) ** (2 / n), s)))
    ns = len(st)
    for i in range(ns - 1):
        for j in range(ring):
            j2 = (j + 1) % ring
            fs.append((i * ring + j, i * ring + j2, (i + 1) * ring + j2, (i + 1) * ring + j))
    if cap:
        for i in (0, ns - 1):
            c = Vector((0, 0, 0))
            for j in range(ring):
                c += Vector(vs[i * ring + j])
            ci = len(vs); vs.append(tuple(c / ring))
            for j in range(ring):
                fs.append((i * ring + j, i * ring + (j + 1) % ring, ci))
    o = V.mesh_obj(name, vs, fs, [m])
    _finish_shell(o)
    if levels:
        V.subdivide(o, levels)
    return o


def airfoil(chord, th, camber=0.02, npts=14):
    """Closed airfoil loop in (u = distance aft of the leading edge, v = up), counter-clockwise."""
    def t(x):
        return 5 * th * (0.2969 * math.sqrt(x) - 0.126 * x - 0.3516 * x ** 2 + 0.2843 * x ** 3 - 0.1036 * x ** 4)
    xs = [(1 - math.cos(math.pi * i / npts)) / 2 for i in range(npts + 1)]
    up = [(x * chord, (t(x) + camber * 4 * x * (1 - x)) * chord) for x in xs]
    lo = [(x * chord, (-t(x) + camber * 4 * x * (1 - x)) * chord) for x in xs]
    return up[::-1] + lo[1:-1]


def lifting_surface(name, sections, m, vertical=False):
    """Loft airfoil sections. sections: [(span_pos, x_le, base, chord, th)] where span_pos runs along Y (or Z when
    vertical) and base is the section's z (or y when vertical)."""
    vs, fs = [], []
    k = None
    for (sp, xle, base, chord, th) in sections:
        loop = airfoil(chord, th, 0.0 if vertical else 0.02)
        k = len(loop)
        for (u, v) in loop:
            if vertical:
                vs.append((xle - u, base + v, sp))
            else:
                vs.append((xle - u, sp, base + v))
    ns = len(sections)
    for i in range(ns - 1):
        for j in range(k):
            j2 = (j + 1) % k
            fs.append((i * k + j, i * k + j2, (i + 1) * k + j2, (i + 1) * k + j))
    for i in (0, ns - 1):
        c = Vector((0, 0, 0))
        for j in range(k):
            c += Vector(vs[i * k + j])
        ci = len(vs); vs.append(tuple(c / k))
        for j in range(k):
            fs.append((i * k + j, i * k + (j + 1) % k, ci))
    o = V.mesh_obj(name, vs, fs, [m], sharp_deg=60)
    return _finish_shell(o)


def blink_mat(name, col, expr, base=2.0):
    m = bpy.data.materials.get(name)
    if m:
        return m
    m, g = V._newmat(name)
    p = g.bsdf(col, 0.1, 0.0, **{'Emission Color': (*col, 1), 'Emission Strength': base, 'Transmission Weight': 0.5})
    g.out(p)
    if expr:
        V._drive(p.inputs['Emission Strength'], 'default_value', expr)
    return m


# ============================================================================ materials
def plane_paint():
    def masks(g):
        x, z = g.x, g.z
        side = g.ss(0.35, 0.55, g.any)
        # cockpit glazing: windscreen (front view) and side windows, with frames
        ws = g.ss(0.0, 0.004, g.poly(g.ay, z, [(0.0, 3.80), (1.25, 3.72), (1.05, 4.32), (0.0, 4.40)])) * g.ss(0.15, 0.3, g.nx) * g.ss(17.6, 17.8, x)
        sw = g.ss(0.0, 0.004, g.poly(x, z, [(16.55, 3.72), (18.15, 3.72), (17.75, 4.28), (16.55, 4.28)])) * g.ss(0.4, 0.6, g.any)
        frames = g.mx(g.band(g.y, 0.0, 0.045, 0.004), g.mx(g.band(x, 17.15, 0.035, 0.004), g.band(x, 16.55, 0.035, 0.004)))
        glass = g.clamp(g.mx(ws, sw) - frames)
        rim = g.clamp(g.mx(g.ss(-0.05, -0.03, g.poly(g.ay, z, [(0.0, 3.80), (1.25, 3.72), (1.05, 4.32), (0.0, 4.40)])) * g.ss(0.15, 0.3, g.nx) * g.ss(17.6, 17.8, x),
                           g.ss(-0.05, -0.03, g.poly(x, z, [(16.55, 3.72), (18.15, 3.72), (17.75, 4.28), (16.55, 4.28)])) * g.ss(0.4, 0.6, g.any)) - glass)
        # panel lines: frames every 1.55 m, longerons, plus the crew door and the paratroop doors
        fr = V.E(g, g.math('FRACT', x / 1.55).s)
        rings = g.ss(0.004, 0.0, abs(fr - 0.5) - 0.497) * g.inside(x, -17.0, 16.0)
        rings = g.band(fr, 0.5, 0.0016, 0.0008) * g.inside(x, -17.0, 16.0)
        lon = g.mx(g.band(z, 3.1, 0.002, 0.001), g.band(z, 4.6, 0.002, 0.001)) * side * g.inside(x, -12.0, 16.0)
        doors = V.gaps(g, [('x', 14.6, 1.25, 3.2), ('x', 13.7, 1.25, 3.2), ('z', 3.2, 13.7, 14.6),
                           ('x', -6.2, 1.5, 3.3), ('x', -7.2, 1.5, 3.3), ('z', 3.3, -7.2, -6.2)])
        # hold windows (small round ports) and the walkway stripe
        M = dict(glass=glass, black=rim * 0.9,
                 gap=g.mx(g.mx(rings * 0.6, lon * 0.6), doors))
        # anti-glare panel ahead of the windscreen
        M['livery'] = [(g.ss(0.0, 0.01, g.poly(g.ay, z, [(0.0, 3.3), (1.6, 3.3), (1.3, 3.8), (0.0, 3.86)])) * g.ss(18.0, 18.3, x) * g.ss(0.05, 0.2, g.nx),
                        (0.03, 0.03, 0.035))]
        return M
    return V.paint_shader("V_Paint_Plane", masks, rough=0.5, metallic=0.1)


def roller_floor_mat():
    def f():
        m, g = V._newmat("V_HoldFloor")
        fr = V.E(g, g.math('FRACT', g.x / 0.25).s)
        lane = g.mx(g.inside(g.ay, 0.55, 0.75, 0.01), g.inside(g.ay, 1.2, 1.4, 0.01))
        roller = lane * g.ss(0.35, 0.2, abs(fr - 0.5))
        col = g.mix_col(roller, (0.08, 0.08, 0.085), (0.45, 0.46, 0.47))
        col = g.mix_col(lane * (1 - roller), col, (0.02, 0.02, 0.02))
        p = g.bsdf((0.1, 0.1, 0.1), 0.6, 0.0); g.L.new(col, p.inputs['Base Color'])
        g.link(roller * 0.9, p.inputs['Metallic']); g.link(0.6 - roller * 0.35, p.inputs['Roughness'])
        g.L.new(g.bump(roller, 0.6, 0.01), p.inputs['Normal'])
        g.out(p); return m
    return V.mat("V_HoldFloor", f)


# ============================================================================ the aircraft
FUSE = [(22.05, 3.02, 0.04, 0.04), (21.85, 3.02, 0.55, 0.52), (21.35, 3.06, 1.03, 0.98), (20.45, 3.12, 1.48, 1.45),
        (19.25, 3.18, 1.83, 1.84), (17.6, 3.14, 2.0, 1.99), (15.5, 3.1, 2.05, 2.05), (8.0, 3.1, 2.05, 2.05),
        (0.0, 3.1, 2.05, 2.05), (-7.5, 3.1, 2.05, 2.05), (-10.0, 3.35, 2.0, 1.8), (-13.0, 3.75, 1.85, 1.42),
        (-16.0, 4.15, 1.6, 1.05), (-19.0, 4.5, 1.25, 0.72), (-21.5, 4.75, 0.8, 0.45), (-22.2, 4.85, 0.35, 0.22)]


def _dense(st, step=1.2):
    out = [st[0]]
    for a, b in zip(st, st[1:]):
        n = max(1, int(abs(a[0] - b[0]) / step))
        for k in range(1, n + 1):
            t = k / n
            out.append(tuple(a[i] + (b[i] - a[i]) * t for i in range(4)))
    return out


def _cutter():
    (hx, hz), (ex, ez) = RAMP_HINGE, CUT_END
    poly = [(hx, hz), (ex, ez), (ex, -1.0), (hx, -1.0)]
    vs = [(x, y, z) for y in (-1.75, 1.75) for (x, z) in poly]
    fs = [(0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]
    c = V.mesh_obj("RampCut", vs, fs, [V.liner()], smooth=False)
    return _finish_shell(c)


def cargo_plane(variant=None):
    pm = plane_paint()
    dk, bp = V.steel_dark(), V.black_plastic()
    fus = loft_ellipse("Fuselage", _dense(FUSE), pm, ring=48, levels=1, n=2.0)
    # clamshell doors: the skin piece under the ramp opening, split left / right
    cut = _cutter()
    piece = bpy.data.objects.new("DoorPiece", fus.data.copy()); V.link(piece)
    b = piece.modifiers.new("i", 'BOOLEAN'); b.operation = 'INTERSECT'; b.object = cut; b.solver = 'MANIFOLD'
    V.bake(piece)
    bm = bmesh.new(); bm.from_mesh(piece.data)                      # keep only the skin, drop the cutter's faces
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if piece.data.materials[f.material_index] is None
                               or piece.data.materials[f.material_index].name.startswith("V_Liner")], context='FACES')
    bm.to_mesh(piece.data); bm.free()
    fus.data.materials.append(V.liner())
    V.boolean_cut(fus, cut, 'MANIFOLD')
    bpy.data.objects.remove(cut)
    # the cut leaves the cutter's faces sealing the hole: delete them so the opening shows into the hold
    li = [i for i, mt in enumerate(fus.data.materials) if mt and mt.name.startswith("V_Liner")]
    bm = bmesh.new(); bm.from_mesh(fus.data)
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.material_index in li], context='FACES')
    bm.to_mesh(fus.data); bm.free()
    doors = []
    for s in (1, -1):
        d = bpy.data.objects.new(f"Door{'L' if s > 0 else 'R'}", piece.data.copy()); V.link(d)
        bm = bmesh.new(); bm.from_mesh(d.data)
        res = bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=(0, 0, 0), plane_no=(0, 1, 0),
                                     clear_inner=(s > 0), clear_outer=(s < 0))
        bm.to_mesh(d.data); bm.free()
        d.data.shade_smooth()
        doors.append(d)
    bpy.data.objects.remove(piece)
    parts = [fus]
    # main-gear sponsons, wing-root fairing, tail-cone fairing at the fin
    for s in (-1, 1):
        sp = loft_ellipse("Sponson", _dense([(4.8, 1.75, 0.05, 0.05), (4.3, 1.72, 0.45, 0.55), (3.2, 1.72, 0.68, 0.8),
                                             (-3.8, 1.72, 0.68, 0.8), (-5.2, 1.75, 0.45, 0.55), (-5.9, 1.8, 0.05, 0.05)], 0.8), pm, ring=24)
        sp.data.transform(Matrix.Translation((0, s * 1.85, 0)))
        parts.append(sp)
    parts.append(loft_ellipse("WingFairing", _dense([(4.2, 5.0, 0.05, 0.05), (3.4, 5.05, 1.1, 0.35), (1.0, 5.1, 1.5, 0.55),
                                                     (-4.0, 5.1, 1.5, 0.55), (-6.0, 5.0, 0.9, 0.3), (-7.0, 4.95, 0.05, 0.05)], 0.8), pm, ring=24))
    # wing: swept, high-mounted, with anhedral
    span, sweep, anh = 24.4, math.radians(26.0), math.radians(4.0)
    secs = []
    for k in range(-12, 13):
        y = span * (k / 12.0)
        f = abs(y) / span
        secs.append((y, 2.6 - abs(y) * math.tan(sweep), 5.25 - abs(y) * math.tan(anh), 7.0 - 4.6 * f, 0.11 - 0.03 * f))
    wing = lifting_surface("Wing", secs, pm)
    parts.append(wing)
    # flap-track fairings under the trailing edge
    for y in (4.5, 10.3, 16.2, -4.5, -10.3, -16.2):
        x_te = 2.6 - abs(y) * math.tan(sweep) - (7.0 - 4.6 * abs(y) / span)
        z = 5.25 - abs(y) * math.tan(anh)
        ff = loft_ellipse("FlapFairing", [(x_te + 2.2, z - 0.15, 0.03, 0.03), (x_te + 1.2, z - 0.3, 0.16, 0.22),
                                          (x_te - 0.6, z - 0.3, 0.14, 0.2), (x_te - 1.2, z - 0.25, 0.03, 0.03)], pm, ring=12, levels=0)
        ff.data.transform(Matrix.Translation((0, y, 0)))
        parts.append(ff)
    # T-tail: fin plus tailplane on top, with a bullet fairing
    fin = lifting_surface("Fin", [(4.6, -13.6, 0.0, 7.6, 0.075), (8.0, -15.6, 0.0, 5.6, 0.07), (11.4, -18.0, 0.0, 4.0, 0.075)], pm, vertical=True)
    parts.append(fin)
    tsecs = []
    for k in range(-6, 7):
        y = 8.0 * k / 6.0; f = abs(y) / 8.0
        tsecs.append((y, -17.6 - abs(y) * math.tan(math.radians(25)), 11.45 - abs(y) * 0.02, 3.9 - 2.1 * f, 0.09))
    parts.append(lifting_surface("Tailplane", tsecs, pm))
    parts.append(loft_ellipse("TailBullet", [(-16.4, 11.45, 0.03, 0.03), (-17.1, 11.45, 0.32, 0.32), (-20.2, 11.45, 0.36, 0.36),
                                             (-22.4, 11.45, 0.12, 0.12)], pm, ring=16, levels=1))
    # engines on pylons
    for y in (7.4, 13.3, -7.4, -13.3):
        x_le = 2.6 - abs(y) * math.tan(sweep); zw = 5.25 - abs(y) * math.tan(anh)
        cx, cz = x_le + 1.4, zw - 1.55
        nac = V.lathe("Nacelle", [(0.56, 2.32), (0.66, 2.46), (0.76, 2.38), (0.8, 1.9), (0.8, 0.2), (0.74, -1.0), (0.66, -1.15),
                                  (0.6, -2.0), (0.47, -2.35)], pm, 40, axis='X')
        inner = V.lathe("Intake", [(0.56, 2.32), (0.57, 1.95)], dk, 32, axis='X')
        fan = V.lathe("Fan", [(0.0, 2.15), (0.18, 2.02), (0.57, 1.95)], V.simple("V_Fan", (0.05, 0.05, 0.055), 0.35, 0.9), 32, axis='X')
        noz = V.lathe("Nozzle", [(0.47, -2.35), (0.44, -2.2), (0.3, -2.5), (0.12, -2.95), (0.0, -3.05)],
                      V.simple("V_Exhaust", (0.12, 0.1, 0.09), 0.5, 0.8), 24, axis='X')
        eng = V.join([nac, inner, fan, noz], "Engine")
        eng.data.transform(Matrix.Translation((cx, y, cz)))
        parts.append(eng)
        pyl = lifting_surface("Pylon", [(cz + 0.6, cx + 1.6, y, 4.6, 0.09), (zw - 0.05, x_le - 0.4, y, 3.6, 0.1)], pm, vertical=True)
        parts.append(pyl)
    # cargo hold: roller floor, ribs, side seats; ramp-hinge sill
    parts.append(V.rbox("HoldFloor", (3.0, 0, 1.24), (22.0, 3.1, 0.12), 0.01, roller_floor_mat()))
    rib = V.simple("V_HoldRib", (0.11, 0.115, 0.12), 0.7)
    for k in range(9):
        x = -7.6 + k * 1.1
        ring = [(x, 1.98 * math.cos(a), 3.1 + 1.98 * math.sin(a)) for a in [math.radians(d) for d in range(-60, 241, 15)]]
        parts.append(V.sweep("Rib", ring, V.rounded_rect(0.06, 0.12, 0.02, 1), rib, up=(1, 0, 0)))
    for s in (-1, 1):
        parts.append(V.rbox("TroopSeats", (-2.0, s * 1.62, 1.75), (9.0, 0.35, 0.08), 0.02, V.simple("V_Webbing", (0.18, 0.2, 0.12), 0.9)))
    # quilted insulation liner over the upper hold (open below floor level and over the ramp opening)
    def liner_mat():
        m, g = V._newmat("V_HoldLiner")
        q = V.E(g, g.math('FRACT', g.x / 0.55).s); q2 = V.E(g, g.math('FRACT', g.z / 0.45).s)
        quilt = g.mx(g.ss(0.06, 0.0, q) + g.ss(0.94, 1.0, q), g.ss(0.06, 0.0, q2) + g.ss(0.94, 1.0, q2))
        p = g.bsdf((0.36, 0.37, 0.33), 0.85, 0.0); g.L.new(g.bump(-quilt + g.noise(3.0, 2.0) * 0.3, 0.5, 0.02), p.inputs['Normal'])
        g.out(p); return m
    lm = V.mat("V_HoldLiner", liner_mat)
    vs, fs = [], []
    angs = [math.radians(a) for a in range(-12, 193, 12)]
    xs = [15.0 - k * 1.0 for k in range(26)]                 # 15 .. -10
    for x in xs:
        zc, a, b = 3.1, 1.93, 1.93
        if x < -7.5:
            t = (-7.5 - x) / 2.5; zc, a, b = 3.1 + 0.25 * t, 2.05 - 0.15 * t - 0.12, 2.05 - 0.25 * t - 0.12
        for an in angs:
            vs.append((x, a * math.cos(an), zc + b * math.sin(an)))
    k = len(angs)
    for i in range(len(xs) - 1):
        for j in range(k - 1):
            fs.append((i * k + j, (i + 1) * k + j, (i + 1) * k + j + 1, i * k + j + 1))
    parts.append(V.mesh_obj("HoldLiner", vs, fs, [lm]))
    hold_l = bpy.data.lights.new("HoldLight", 'POINT'); hold_l.energy = 450; hold_l.color = (1.0, 0.86, 0.65); hold_l.shadow_soft_size = 0.6
    # gear: nose twin wheels with strut and doors
    parts.append(V.cylinder("NoseStrut", (17.0, 0, 0.95), 0.08, 1.3, V.alu(), axis='Z', verts=12))
    for s in (-1, 1):
        parts.append(V.rbox("NoseDoor", (17.0, s * 0.62, 1.15), (1.6, 0.04, 0.7), 0.01, pm))
    for x in (0.4, -1.5):
        for s in (-1, 1):
            parts.append(V.cylinder("MainStrut", (x, s * 1.95, 1.0), 0.09, 0.8, V.alu(), axis='Z', verts=12))
    # nav lights, beacons, landing light
    parts.append(V.round_lamp("Landing", (17.15, 0, 0.95), 0.07, 0.05, "head"))
    body = V.join(parts, "CargoPlane")
    for x in (-5.0, 2.0, 9.0):
        lo = V.link(bpy.data.objects.new("HoldLight", hold_l)); lo.parent = body; lo.location = (x, 0, 4.4)
    red = blink_mat("V_NavRed", (1.0, 0.05, 0.03), None, 6.0); green = blink_mat("V_NavGreen", (0.1, 1.0, 0.3), None, 6.0)
    white = blink_mat("V_NavWhite", (1.0, 1.0, 1.0), "8.0 * (1 if (frame % 36) < 3 else 0)")
    bcn = blink_mat("V_AntiColl", (1.0, 0.05, 0.02), "14.0 * max(0.0, cos(frame * 0.26)) ** 8")
    tip_x = 2.6 - span * math.tan(sweep) - 1.2; tip_z = 5.25 - span * math.tan(anh)
    for s, mm in ((1, red), (-1, green)):
        o = V.lathe("Nav", [(0.0, 0.15), (0.09, 0.1), (0.1, 0.0)], mm, 12, axis='Z')
        o.data.transform(Matrix.Translation((tip_x, s * (span + 0.05), tip_z))); o.parent = body
    for (x, z, flip) in ((3.0, 5.48, 1), (2.0, 1.05, -1)):
        o = V.lathe("Beacon", [(0.0, 0.16), (0.1, 0.12), (0.12, 0.0)], bcn, 16, axis='Z')
        if flip < 0:
            o.data.transform(Matrix.Rotation(math.pi, 4, 'X'))
        o.data.transform(Matrix.Translation((x, 0, z))); o.parent = body
    o = V.lathe("TailLight", [(0.0, 0.1), (0.08, 0.0)], white, 12, axis='X'); o.data.transform(Matrix.Translation((-22.45, 0, 11.45))); o.parent = body
    # wheels: nose twin, main tandem twin
    mn = V.wheel_mesh("plane_nose", 0.45, 0.28, 0.25, "black")
    mm_ = V.wheel_mesh("plane_main", 0.62, 0.36, 0.33, "black", dual=True)
    for s in (-1, 1):
        V.add_wheel(body, mn, 17.0, s * 0.3, 0.45, 0.45, 0.25, s)
        for x in (0.4, -1.5):
            V.add_wheel(body, mm_, x, s * 2.35, 0.62, 0.62, 0.33, s)
    # ramp (part 'ramp'): a ribbed plate hinged at the hold floor; doors (part 'doors' -> door_l, door_r)
    rx, rz = RAMP_HINGE
    ramp = V.join([V.rbox("Ramp", (-RAMP_LEN / 2, 0, -0.06), (RAMP_LEN, 3.0, 0.12), 0.02, roller_floor_mat()),
                   V.rbox("RampUnder", (-RAMP_LEN / 2, 0, -0.16), (RAMP_LEN, 3.1, 0.08), 0.02, pm)] +
                  [V.rbox("RampToe", (-RAMP_LEN - 0.35 - 0.0 * k, s * 0.9, -0.08), (0.7, 0.6, 0.05), 0.02, dk) for k, s in enumerate((-1, 1))],
                  "Ramp")
    ramp.parent = body; ramp.location = (rx, 0, rz); ramp["part"] = "ramp"
    hub = V.link(bpy.data.objects.new("Doors", None)); hub.parent = body; hub["part"] = "doors"
    for d, s in zip(doors, (1, -1)):
        # hinge along the door's upper edge, which follows the cut line from the ramp hinge up to the tail
        A = Vector((RAMP_HINGE[0], s * 1.72, 2.05)); B = Vector((CUT_END[0], s * 0.9, CUT_END[1]))
        d.data.transform(Matrix.Translation(-A))
        d.parent = hub; d.location = A; d.rotation_mode = 'AXIS_ANGLE'
        ax = (B - A).normalized(); d["hinge_axis"] = tuple(ax)
        d["part"] = "door_l" if s > 0 else "door_r"; d["door_side"] = s
    # generic markings
    for s in (-1, 1):
        t = V.side_text("Txt", "U.S. AIR FORCE", 10.5, 4.15, 2.06, 0.42, V.simple("V_Black", (0.02, 0.02, 0.02), 0.4), s)
        sw = t.modifiers.new("sw", 'SHRINKWRAP'); sw.target = body; sw.offset = 0.004; sw.wrap_mode = 'OUTSIDE_SURFACE'
        V.bake(t); t.parent = body
    set_ramp(body, 0.0)
    return V._finish(body, "CargoPlane", (0.40, 0.42, 0.44), heads=[(17.25, 0, 0.95)])


def set_ramp(root, t=1.0, door_deg=55.0):
    """0 = closed, 1 = clamshell doors open and the ramp down on the ground (doors lead, ramp follows)."""
    td = min(1.0, max(0.0, t * 1.6)); tr = min(1.0, max(0.0, (t - 0.3) / 0.7))
    for o in root.children_recursive:
        if o.get("part") == "ramp":
            o.rotation_euler = (0, math.radians(RAMP_CLOSED + (RAMP_OPEN - RAMP_CLOSED) * tr), 0)
        if "door_side" in o.keys():
            ax = o["hinge_axis"]
            o.rotation_axis_angle = (math.radians(door_deg * td) * o["door_side"] * DOOR_SIGN, ax[0], ax[1], ax[2])


V.set_ramp = set_ramp


def register(K):
    K["cargo_plane"] = cargo_plane
    V.DEFAULT_DIRT["cargo_plane"] = 0.25
