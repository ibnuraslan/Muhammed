"""train_soviet_electric for vehicles.py: a 1990s Soviet / Russian suburban electric multiple unit in the ER2 / ER9
"elektrichka" style (generic, no real numbers or emblems).

    vehicles.make("train_soviet_electric", loc, heading_deg, cars=4)      # cab cars at both ends
The root is the leading cab car; the other cars are children spaced along -X (the train runs along +X of its heading).
Wheels are real rail wheels on bogies and spin with vehicles.spin_wheels(root, metres). Rail top is at z = 0.
Interiors: varnished bench seats, warm ceiling strips and real lights, seen through the windows.
"""
import math
import bpy
from mathutils import Vector, Matrix
import vehicles as V
from vehicles_cars import S

L = 19.6               # body length
PITCH = 20.0           # car spacing (body + gangway)
W = 1.74               # half width
DOOR_X = 7.95          # door centres at +-DOOR_X
GAUGE = 0.76           # half gauge (1520 mm)
WR = 0.5               # wheel radius


def _masks(head):
    def masks(g):
        x, z = g.x, g.z
        side = g.ss(0.6, 0.75, g.any)
        # passenger windows between the doors, cab side window on cab cars
        fr = V.E(g, g.math('FRACT', (x + 6.95) / 1.30).s)
        row = g.inside(fr, 0.09, 0.91, 0.004) * g.inside(x, -6.95, 6.95, 0.002) * g.inside(z, 2.05, 2.95, 0.004) * side
        seal = g.inside(fr, 0.07, 0.93, 0.004) * g.inside(x, -6.98, 6.98, 0.002) * g.inside(z, 2.02, 2.98, 0.004) * side
        glass = row; rub = g.clamp(seal - row)
        # sliding doors (two leaves) with tall windows
        doorf = None; dglass = None
        for c in ((-DOOR_X,) if head else (-DOOR_X, DOOR_X)):
            f_ = g.inside(x, c - 0.64, c + 0.64, 0.002) * g.inside(z, 1.28, 3.28, 0.002) * side
            gl = g.inside(z, 2.1, 3.05, 0.003) * side * g.mx(g.inside(x, c - 0.56, c - 0.06, 0.003), g.inside(x, c + 0.06, c + 0.56, 0.003))
            doorf = f_ if doorf is None else g.mx(doorf, f_)
            dglass = gl if dglass is None else g.mx(dglass, gl)
        glass = g.mx(glass, dglass)
        lines = [('x', c + d, 1.28, 3.28) for c in ((-DOOR_X,) if head else (-DOOR_X, DOOR_X)) for d in (-0.64, 0.0, 0.64)]
        lines += [('z', 3.28, -DOOR_X - 0.64, -DOOR_X + 0.64)]
        if not head:
            lines += [('z', 3.28, DOOR_X - 0.64, DOOR_X + 0.64)]
        gap = V.gaps(g, lines, 0.003)
        if head:
            cab = g.inside(x, 8.55, 9.25, 0.003) * g.inside(z, 2.15, 2.95, 0.004) * side
            frf = g.ss(0.3, 0.5, g.nx) * g.ss(9.3, 9.45, x)
            ws = g.mx(g.ss(0.0, 0.004, g.poly(g.y, z, [(0.1, 2.35), (1.08, 2.35), (1.0, 3.15), (0.1, 3.15)])),
                      g.ss(0.0, 0.004, g.poly(g.y, z, [(-1.08, 2.35), (-0.1, 2.35), (-0.1, 3.15), (-1.0, 3.15)]))) * frf
            wsr = g.mx(g.ss(-0.04, -0.02, g.poly(g.y, z, [(0.1, 2.35), (1.08, 2.35), (1.0, 3.15), (0.1, 3.15)])),
                       g.ss(-0.04, -0.02, g.poly(g.y, z, [(-1.08, 2.35), (-0.1, 2.35), (-0.1, 3.15), (-1.0, 3.15)]))) * frf
            glass = g.mx(g.mx(glass, cab), ws)
            rub = g.mx(rub, g.clamp(wsr - ws))
            gap = g.mx(gap, V.gaps(g, [('x', 8.45, 1.3, 3.25), ('x', 9.3, 1.3, 3.25)], 0.003))
        M = dict(glass=glass, rubber=rub, gap=g.mx(gap, g.clamp(doorf - dglass) * 0.0))
        roof = g.ss(3.45, 3.6, z)
        stripe = g.inside(z, 1.52, 1.64, 0.003) * g.mx(side, g.ss(0.3, 0.5, abs(g.nx)))
        nose = (g.ss(0.3, 0.5, g.nx) * g.ss(9.3, 9.45, x) * g.inside(z, 1.1, 2.2, 0.004)) if head else 0.0
        liv = [(roof, (0.42, 0.43, 0.42)), (stripe, (0.55, 0.05, 0.03))]
        if head:
            liv.append((nose, (0.75, 0.55, 0.05)))
        M['livery'] = liv
        return M
    return masks


def rail_wheel_mesh():
    nm = "Wheel_rail"
    if nm in bpy.data.meshes:
        return bpy.data.meshes[nm]
    prof = [(0.0, 0.07), (0.13, 0.08), (0.15, 0.03), (0.40, 0.03), (0.44, 0.06), (WR - 0.01, 0.065), (WR, 0.03),
            (WR + 0.005, -0.04), (WR + 0.045, -0.055), (WR + 0.045, -0.07), (WR - 0.02, -0.08), (0.40, -0.05), (0.15, -0.05), (0.0, -0.06)]
    o = V.lathe("RailWheel", prof, V.simple("V_RailWheel", (0.22, 0.2, 0.18), 0.45, 0.7), 40)
    me = o.data; bpy.data.objects.remove(o)
    me.name = nm
    return me


def bogie(parts, bx, motor):
    dk = V.steel_dark()
    parts.append(V.rbox("BogieFrame", (bx, 0, 0.72), (2.9, 2.0, 0.32), 0.04, dk))
    for s in (-1, 1):
        parts.append(V.rbox("SideFrame", (bx, s * 1.0, 0.6), (3.1, 0.18, 0.42), 0.04, dk))
        for d in (-0.7, 0.7):
            parts.append(V.cylinder("Spring", (bx + d, s * 1.0, 0.95), 0.12, 0.3, V.simple("V_Spring", (0.1, 0.1, 0.1), 0.5, 0.6), axis='Z', verts=14))
        for ax in (-1.3, 1.3):
            parts.append(V.cylinder("AxleBox", (bx + ax, s * 1.0, WR), 0.17, 0.26, dk, axis='Y', verts=16))
    for ax in (-1.3, 1.3):
        parts.append(V.cylinder("Axle", (bx + ax, 0, WR), 0.08, 1.9, dk, axis='Y', verts=12))
        if motor:
            parts.append(V.rbox("Motor", (bx + ax * 0.55, 0, 0.62), (0.6, 1.1, 0.5), 0.05, dk))


def pantograph(parts, x):
    dk = V.steel_dark(); al = V.simple("V_PantoRed", (0.45, 0.08, 0.05), 0.5, 0.3)
    ins = V.simple("V_Insulator", (0.5, 0.45, 0.35), 0.3)
    z0 = 4.25
    for dx in (-0.8, 0.8):
        for dy in (-0.55, 0.55):
            parts.append(V.cylinder("Insulator", (x + dx, dy, z0 - 0.05), 0.06, 0.22, ins, axis='Z', verts=12))
    parts.append(V.rbox("PantoBase", (x, 0, z0 + 0.08), (1.9, 1.3, 0.08), 0.02, dk))
    tube = V.rounded_rect(0.045, 0.045, 0.02, 2)
    for dy in (-0.45, 0.45):
        parts.append(V.sweep("ArmL", [(x - 0.85, dy, z0 + 0.12), (x + 0.15, dy, z0 + 0.62), (x - 0.05, dy, z0 + 1.15)], tube, al, up=(0, 1, 0)))
        parts.append(V.sweep("ArmR", [(x + 0.85, dy, z0 + 0.12), (x - 0.15, dy, z0 + 0.62), (x + 0.05, dy, z0 + 1.15)], tube, al, up=(0, 1, 0)))
    parts.append(V.rbox("PantoHead", (x, 0, z0 + 1.18), (0.12, 1.9, 0.05), 0.02, V.simple("V_Carbon", (0.08, 0.08, 0.08), 0.4, 0.5)))
    parts.append(V.rbox("PantoHorn", (x, 0, z0 + 1.2), (0.06, 2.1, 0.03), 0.01, dk))


def interior(parts, head):
    wood = V.simple("V_Varnish", (0.30, 0.13, 0.05), 0.35, 0.0, **{'Coat Weight': 0.6})
    frame = V.simple("V_SeatFrame", (0.15, 0.15, 0.16), 0.5, 0.6)
    parts.append(V.rbox("Floor", (0, 0, 1.33), (L - 0.4, 2 * W - 0.15, 0.06), 0.01, V.simple("V_Lino", (0.18, 0.15, 0.12), 0.7)))
    for k in range(10):
        x = -6.3 + k * 1.4
        for s in (-1, 1):
            parts.append(V.rbox("Bench", (x, s * 0.98, 1.82), (0.48, 1.25, 0.08), 0.02, wood))
            parts.append(V.rbox("BenchBack", (x - 0.26, s * 0.98, 2.2), (0.06, 1.25, 0.65), 0.02, wood, rot=(0, math.radians(-8), 0)))
            parts.append(V.rbox("BenchLeg", (x, s * 0.45, 1.58), (0.06, 0.06, 0.45), 0.01, frame))
    strip = V.simple("V_CeilStrip", (1.0, 0.9, 0.7), 0.5, 0.0, **{'Emission Color': (1.0, 0.82, 0.55, 1), 'Emission Strength': 4.0})
    for s in (-1, 1):
        parts.append(V.rbox("CeilLight", (0, s * 0.55, 3.85), (L - 3.0, 0.14, 0.04), 0.01, strip))
        parts.append(V.rbox("Rack", (0, s * 1.35, 3.25), (L - 3.5, 0.32, 0.03), 0.01, frame))
    if head:
        parts.append(V.rbox("CabWall", (8.4, 0, 2.3), (0.05, 2 * W - 0.2, 1.9), 0.01, V.interior()))
        parts.append(V.rbox("CabDesk", (9.15, 0, 2.15), (0.5, 2.6, 0.18), 0.05, V.interior(), sub=1))
        parts.append(V.rbox("CabSeat", (8.75, 0.6, 1.85), (0.45, 0.45, 0.12), 0.04, V.interior(), sub=1))


def car(name, head, motor):
    paint = V.paint_shader("V_Paint_Elektrichka" + ("_cab" if head else ""), _masks(head), rough=0.45,
                           back_col=(0.42, 0.40, 0.33))
    if head:
        keys = [S(9.8, 1.16, 3.15, 3.92, 1.42, 1.0, rb=0.12, rs=0.08, rt=0.3, crown=0.08, bul=0.0),
                S(9.68, 1.1, 3.25, 4.03, 1.6, 1.12, rb=0.12, rs=0.05, rt=0.33, crown=0.1, bul=0.0),
                S(9.42, 1.06, 3.32, 4.08, 1.7, 1.18, rb=0.1, rs=0.03, rt=0.35, crown=0.12, bul=0.0),
                S(9.0, 1.05, 3.35, 4.1, 1.74, 1.2, rb=0.1, rs=0.02, rt=0.35, crown=0.13, bul=0.0, soft=True),
                S(-9.72, 1.05, 3.35, 4.1, 1.74, 1.2, rb=0.1, rs=0.02, rt=0.35, crown=0.13, bul=0.0),
                S(-9.8, 1.08, 3.33, 4.06, 1.68, 1.16, rb=0.08, rs=0.02, rt=0.33, crown=0.12, bul=0.0)]
    else:
        keys = [S(9.8, 1.08, 3.33, 4.06, 1.68, 1.16, rb=0.08, rs=0.02, rt=0.33, crown=0.12, bul=0.0),
                S(9.72, 1.05, 3.35, 4.1, 1.74, 1.2, rb=0.1, rs=0.02, rt=0.35, crown=0.13, bul=0.0),
                S(-9.72, 1.05, 3.35, 4.1, 1.74, 1.2, rb=0.1, rs=0.02, rt=0.35, crown=0.13, bul=0.0),
                S(-9.8, 1.08, 3.33, 4.06, 1.68, 1.16, rb=0.08, rs=0.02, rt=0.33, crown=0.12, bul=0.0)]
    body = V.loft_body(name, keys, paint, step=0.6, extra=0.03)
    dk, bp = V.steel_dark(), V.black_plastic()
    parts = [body]
    for bx in (-7.0, 7.0):
        bogie(parts, bx, motor)
    for k, (x0, x1) in enumerate(((-5.3, -1.8), (-1.4, 1.6), (2.0, 5.2))):
        parts.append(V.rbox("Equip", ((x0 + x1) / 2, 0, 0.82), (x1 - x0, 2.3, 0.42), 0.04, dk))
    parts.append(V.rbox("Sole", (0, 0, 1.08), (L - 0.3, 2 * W - 0.1, 0.12), 0.02, dk))
    for s in (-1, 1):
        for d in (-DOOR_X,) if head else (-DOOR_X, DOOR_X):
            parts.append(V.rbox("Step", (d, s * (W + 0.02), 1.12), (1.2, 0.2, 0.05), 0.01, dk))
    for x in [-7.5 + 2.5 * k for k in range(7)]:
        parts.append(V.rbox("Vent", (x, 0, 4.25), (0.6, 0.45, 0.14), 0.05, V.simple("V_RoofGrey", (0.32, 0.33, 0.32), 0.6), sub=1))
    for e in ((-1,) if head else (-1, 1)):
        parts.append(V.rbox("Gangway", (e * 9.9, 0, 2.3), (0.22, 1.15, 2.1), 0.06, V.rubber()))
        parts.append(V.rbox("Coupler", (e * 9.95, 0, 1.0), (0.3, 0.3, 0.22), 0.04, dk))
    if motor:
        pantograph(parts, 4.0)
        parts.append(V.rbox("Resistors", (-3.0, 0, 4.3), (4.0, 1.1, 0.25), 0.04, V.simple("V_RoofGrey", (0.32, 0.33, 0.32), 0.6)))
    heads = []
    if head:
        parts.append(V.round_lamp("HeadLamp", (9.79, 0, 3.72), 0.14, 0.08, "head"))
        heads.append((9.85, 0, 3.72))
        for s in (-1, 1):
            parts.append(V.round_lamp(f"Marker{s}", (9.79, s * 0.95, 1.55), 0.065, 0.05, "head"))
            parts.append(V.round_lamp(f"MarkerR{s}", (9.79, s * 1.22, 1.55), 0.065, 0.05, "tail"))
            parts.append(V.rbox("Wiper", (9.84, s * 0.55, 2.55), (0.02, 0.02, 0.62), 0.006, bp, rot=(math.radians(25 * s), 0, 0)))
            parts.append(V.rbox("Handrail", (9.0, s * (W + 0.04), 2.2), (0.03, 0.03, 1.2), 0.012, V.alu()))
        parts.append(V.rbox("CabCoupler", (9.95, 0, 1.0), (0.4, 0.34, 0.26), 0.05, dk))
        parts.append(V.rbox("Plough", (9.7, 0, 0.42), (0.12, 2.0, 0.35), 0.03, dk))
        parts.append(V.cylinder("Horn", (9.2, 0.3, 4.12), 0.05, 0.3, V.alu(), axis='X', verts=12))
    interior(parts, head)
    o = V.join(parts, name)
    return o, heads


def train_soviet_electric(variant=None, cars=4):
    cars = max(2, int(cars))
    cab, heads = car("ElektrichkaCab", True, False)
    mid_m, _ = car("ElektrichkaMotor", False, True)
    mid_t, _ = car("ElektrichkaTrailer", False, False)
    wm = rail_wheel_mesh()
    light = bpy.data.lights.new("SaloonLight", 'POINT'); light.energy = 220; light.color = (1.0, 0.8, 0.55); light.shadow_soft_size = 0.4
    root = cab
    for k in range(cars):
        if k == 0:
            o = cab
        elif k == cars - 1:
            o = bpy.data.objects.new("ElektrichkaCabRear", cab.data); V.link(o)
            o.parent = root; o.location = (-k * PITCH, 0, 0); o.rotation_euler = (0, 0, math.pi)
        else:
            src = mid_m if k % 2 == 1 else mid_t
            o = bpy.data.objects.new(f"ElektrichkaCar{k}", src.data); V.link(o)
            o.parent = root; o.location = (-k * PITCH, 0, 0)
        flip = (k == cars - 1 and k > 0)
        for bx in (-7.0, 7.0):
            for ax in (-1.3, 1.3):
                for s in (-1, 1):
                    w = V.add_wheel(o, wm, bx + ax, s * GAUGE, WR, WR, 0.4, s)
                    if flip:
                        w["spin_sign"] = -w["spin_sign"]
        for lx in (-5.0, 0.0, 5.0):
            lo = V.link(bpy.data.objects.new("SaloonLight", light)); lo.parent = o; lo.location = (lx, 0, 3.6)
    for src in (mid_m, mid_t):
        bpy.data.objects.remove(src)
    root["train"] = 1
    return V._finish(root, "Elektrichka", (0.055, 0.19, 0.095), heads=heads)


def register(K):
    K["train_soviet_electric"] = train_soviet_electric
    V.DEFAULT_DIRT["train_soviet_electric"] = 0.3
