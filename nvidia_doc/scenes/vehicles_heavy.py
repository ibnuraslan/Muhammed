"""Construction / scrap machines for vehicles.py: excavator, grab crane (material handler), boom truck.

Moving parts (children, rotate about their local Y unless noted):
  excavator : house (rot Z), boom, stick, bucket                -> vehicles.pose_arm(root, swing, boom, stick, bucket)
  grab_crane: house (rot Z), boom, stick, grab (rot Z), tine_k   -> vehicles.pose_arm(...), vehicles.set_grab(root, open)
  boom_truck: turret (rot Z), boom, boom_ext (moves along X), hook
Hydraulic rams follow their pivots with Damped Track constraints, so any keyframed pose renders anywhere.
"""
import math
from mathutils import Vector, Matrix
import vehicles as V
from vehicles_cars import S, cab_1990s, truck_chassis, fender, plank_mat, deck_mat


def heavy_paint(tag, col=None, house=None):
    """Machine paint: object colour (or a fixed colour), satin, with oily dirt. house=(x_rear, x_front, half_w, z_top)
    adds service-door gaps and engine louvres on the engine hood (house coordinates)."""
    def masks(g):
        M = {}
        if house:
            xr, xf, hw, zt = house
            side = g.ss(0.55, 0.7, g.any)
            M['gap'] = V.gaps(g, [('x', xr + 0.55, 0.35, zt - 0.08), ('x', xr + 1.15, 0.35, zt - 0.08), ('x', xr + 1.75, 0.35, zt - 0.08),
                                  ('z', zt - 0.08, xr + 0.05, xr + 1.75), ('top_x', xr + 1.0, hw),
                                  ('z', zt - 0.16, -3.2, xr - 0.02), ('end_z', -1, zt - 0.16, 2.0), ('z', 0.38, -3.2, xr - 0.02)])
            cwr = g.ss(xr - 0.05, xr - 0.15, g.x)                     # counterweight: darker lower lip
            M['black'] = cwr * g.inside(g.z, 0.24, 0.36, 0.004)
            lv = side * g.inside(g.x, xr + 0.62, xr + 1.08) * g.inside(g.z, zt - 0.55, zt - 0.2)
            M['black'] = g.mx(M['black'], lv * g.ss(0.45, 0.6, V.E(g, g.math('FRACT', g.z / 0.045).s)))
        return M
    return V.paint_shader("V_Paint_" + tag, masks, rough=0.42, fixed_color=col)


def track_mat():
    def f():
        m, g = V._newmat("V_Track")
        gr = V.E(g, g.math('FRACT', (g.x + g.z * 0.7) / 0.19).s)
        grouser = g.ss(0.30, 0.18, abs(gr - 0.5))
        seam = g.ss(0.035, 0.0, gr) + g.ss(0.965, 1.0, gr)            # gap between link plates
        pin_ = g.band(g.ay, 0.0, 0.5, 0.01) * 0.0
        n = g.noise(4.0, 6.0)
        col = g.mix_col(n, (0.035, 0.033, 0.03), (0.11, 0.09, 0.07))
        col = g.mix_col(grouser * 0.6, col, (0.16, 0.15, 0.14))
        col = g.mix_col(seam, col, (0.004, 0.004, 0.004))
        p = g.bsdf((0.05, 0.05, 0.05), 0.7, 0.6); g.L.new(col, p.inputs['Base Color'])
        g.link(0.55 + n * 0.3, p.inputs['Roughness'])
        g.L.new(g.bump(grouser - seam * 0.8, 1.0, 0.025), p.inputs['Normal'])
        g.out(p); return m
    return V.mat("V_Track", f)


def empty(name, parent, loc):
    import bpy
    e = bpy.data.objects.new(name, None); V.link(e); e.empty_display_size = 0.1
    e.parent = parent; e.location = loc
    return e


def ram(name, a, pa, b, pb, r=0.075, rod_r=0.045, m_barrel=None):
    """Hydraulic ram between part a (at local point pa) and part b (at pb): a barrel on a, a chrome rod on b, both
    aimed at each other with Damped Track constraints."""
    import bpy
    bpy.context.view_layer.update()
    wa = a.matrix_world @ Vector(pa); wb = b.matrix_world @ Vector(pb)
    d = (wb - wa).length
    lb, lr = d * 0.62, d * 0.64
    mb = m_barrel or V.simple("V_RamBarrel", (0.02, 0.02, 0.022), 0.45, 0.3)
    barrel = V.join([V.cylinder("B", (0, lb / 2, 0), r, lb, mb, axis='Y', verts=20),
                     V.cylinder("Bc", (0, 0, 0), r * 0.9, r * 1.6, V.steel_dark(), axis='X', verts=16),
                     V.cylinder("Bg", (0, lb - 0.04, 0), r * 1.12, 0.08, mb, axis='Y', verts=20)], name + "Barrel")
    rod = V.join([V.cylinder("R", (0, lr / 2, 0), rod_r, lr, V.chrome(), axis='Y', verts=16),
                  V.cylinder("Rc", (0, 0, 0), rod_r * 1.6, r * 1.4, V.steel_dark(), axis='X', verts=16)], name + "Rod")
    ta = empty(name + "_ta", a, pa); tb = empty(name + "_tb", b, pb)
    barrel.parent = a; barrel.location = pa
    rod.parent = b; rod.location = pb
    for o, t in ((barrel, tb), (rod, ta)):
        c = o.constraints.new('DAMPED_TRACK'); c.target = t; c.track_axis = 'TRACK_Y'
    return barrel, rod


def undercarriage(parts, L=4.45, gauge=2.0, tw=0.6, h=0.92, r=None):
    """Crawler tracks with frames, rollers, idlers and sprockets, plus the car body and swing ring."""
    r = r or h / 2 - 0.02
    dk = V.steel_dark(); tm = track_mat()
    xe = L / 2 - r
    for s in (-1, 1):
        y = s * gauge / 2
        pts = []
        for k in range(0, 13):                       # front curve
            a = math.radians(-90 + 180 * k / 12)
            pts.append((xe + r * math.cos(a), y, r + 0.03 + r * math.sin(a)))
        for k in range(1, 8):
            pts.append((xe - 2 * xe * k / 8, y, 2 * r + 0.03))
        for k in range(0, 13):
            a = math.radians(90 + 180 * k / 12)
            pts.append((-xe + r * math.cos(a), y, r + 0.03 + r * math.sin(a)))
        for k in range(1, 8):
            pts.append((-xe + 2 * xe * k / 8, y, 0.03))
        parts.append(V.sweep("Track", pts, V.rounded_rect(0.07, tw, 0.02, 2), tm, up=(0, 1, 0), closed_path=True, cap=False, sharp=70))
        parts.append(V.rbox("TrackFrame", (0, y, r + 0.03), (2 * xe, tw * 0.55, r * 1.1), 0.06, dk, sub=0))
        parts.append(V.cylinder("Idler", (xe, y, r + 0.03), r * 0.86, tw * 0.5, dk, axis='Y', verts=32))
        parts.append(V.cylinder("Sprocket", (-xe, y, r + 0.03), r * 0.9, tw * 0.45, dk, axis='Y', verts=32))
        for k in range(6):
            parts.append(V.cylinder("Roller", (-xe + 0.45 + k * (2 * xe - 0.9) / 5, y, 0.17), 0.1, tw * 0.5, dk, axis='Y', verts=20))
        for k in range(2):
            parts.append(V.cylinder("Carrier", (-xe * 0.4 + k * xe * 0.8, y, 2 * r - 0.07), 0.07, tw * 0.3, dk, axis='Y', verts=16))
    parts.append(V.rbox("CarBody", (0, 0, r + 0.05), (1.6, gauge - tw * 0.5, 0.45), 0.08, dk))
    parts.append(V.cylinder("SwingRing", (0, 0, 2 * r + 0.06), 0.85, 0.14, dk, axis='Z', verts=48))


def cab_glass_mat(tag, x0, x1, y0, y1, z0, z1):
    """Excavator cab paint with big glazing on all sides (masks in house coordinates)."""
    def masks(g):
        M = V.window_masks(g, [[(x0 + 0.06, z0 + 0.26), (x1 - 0.06, z0 + 0.26), (x1 - 0.06, z1 - 0.10), (x0 + 0.06, z1 - 0.10)]],
                           front=[(y0 + 0.07, z0 + 0.20), (y1 - 0.07, z0 + 0.20), (y1 - 0.07, z1 - 0.10), (y0 + 0.07, z1 - 0.10)],
                           rear=[(y0 + 0.1, z0 + 0.6), (y1 - 0.1, z0 + 0.6), (y1 - 0.1, z1 - 0.15), (y0 + 0.1, z1 - 0.15)], seal=0.025)
        # door pillar splitting the side glass
        side = g.ss(0.55, 0.7, g.any)
        pillar = g.band(g.x, (x0 + x1) / 2 - 0.1, 0.03, 0.004) * side * g.inside(g.z, z0, z1 - 0.1)
        M['glass'] = g.clamp(M['glass'] - pillar)
        M['black'] = pillar
        return M
    return V.paint_shader("V_Paint_" + tag, masks, rough=0.4, glass_thin=True)


def cab_box(tag, x0, x1, y0, y1, z0, z1, m):
    """Rounded, slightly tapered operator cab (subdivided cage)."""
    w = (y1 - y0) / 2; yc = (y0 + y1) / 2
    keys = [S(x1, z0, z0 + 0.25, z1 - 0.05, w - 0.03, w - 0.06, rb=0.04, rs=0.01, rt=0.06, crown=0.01, bul=0.0),
            S(x1 - 0.04, z0, z0 + 0.25, z1, w, w - 0.03, rb=0.04, rs=0.01, rt=0.08, crown=0.02, bul=0.0),
            S(x0 + 0.04, z0, z0 + 0.25, z1, w, w - 0.03, rb=0.04, rs=0.01, rt=0.08, crown=0.02, bul=0.0),
            S(x0, z0, z0 + 0.25, z1 - 0.05, w - 0.03, w - 0.06, rb=0.04, rs=0.01, rt=0.06, crown=0.01, bul=0.0)]
    c = V.loft_body(tag, keys, m, step=0.2, extra=0.02, levels=2)
    c.data.transform(Matrix.Translation((0, yc, 0)))
    return c


def house_parts(tag, L_front=1.15, L_rear=-1.75, W=2.5, z0=0.0, cab=(-0.5, 1.15, 0.22, 1.24, 0.2, 1.85), tail_r=2.6, hood_h=1.05):
    """Upper structure in house coordinates (origin on the swing axis, z0 = top of the swing ring)."""
    pm = heavy_paint(tag + "House", house=(L_rear, L_front, W / 2, z0 + 0.24 + hood_h)); dk = V.steel_dark()
    parts = [V.rbox("Deck", ((L_front + L_rear) / 2, 0, z0 + 0.12), (L_front - L_rear, W, 0.24), 0.05, dk)]
    parts.append(V.rbox("Hood", ((L_rear + 0.25) / 2 - 0.05, -0.12, z0 + 0.24 + hood_h / 2), (0.25 - L_rear, W - 0.28, hood_h), 0.12, pm, sub=1))
    parts.append(V.rbox("Tank", (0.72, -(W / 2 - 0.45), z0 + 0.24 + 0.45), (0.8, 0.9, 0.9), 0.08, pm, sub=1))
    # curved counterweight round the tail
    arc = [(tail_r * math.cos(math.radians(a)), tail_r * math.sin(math.radians(a)), z0 + 0.25) for a in range(152, 209, 4)]
    cw = V.sweep("Counterweight", arc, V.rounded_rect(0.62, hood_h - 0.04, 0.16, 3), pm, up=(0, 0, 1))
    cw.data.transform(Matrix.Translation((0, 0, 0.24 + (hood_h - 0.04) / 2 - 0.25)))
    parts.append(cw)
    # operator cab, exhaust stack, handrails, lamps
    cx0, cx1, cy0, cy1, cz0, cz1 = cab
    cm = cab_glass_mat(tag + "Cab", cx0, cx1, cy0, cy1, z0 + cz0, z0 + cz0 + cz1)
    parts.append(cab_box(tag + "Cab", cx0, cx1, cy0, cy1, z0 + cz0, z0 + cz0 + cz1, cm))
    yc = (cy0 + cy1) / 2; it = V.interior()
    parts.append(V.rbox("Seat", (cx0 + 0.55, yc, z0 + cz0 + 0.35), (0.5, 0.5, 0.18), 0.06, it, sub=1))
    parts.append(V.rbox("SeatBack", (cx0 + 0.3, yc, z0 + cz0 + 0.75), (0.14, 0.5, 0.7), 0.06, it, sub=1))
    for s_ in (-1, 1):
        parts.append(V.rbox("Console", (cx0 + 0.65, yc + s_ * 0.36, z0 + cz0 + 0.42), (0.55, 0.14, 0.3), 0.03, it))
    parts.append(V.rbox("CabFloor", ((cx0 + cx1) / 2, yc, z0 + cz0 + 0.06), (cx1 - cx0 - 0.1, cy1 - cy0 - 0.1, 0.1), 0.02, it))
    parts.append(V.cylinder("Stack", (-0.9, -0.55, z0 + 0.24 + hood_h + 0.2), 0.06, 0.45, dk, axis='Z', verts=16))
    for x, y in ((-1.4, -0.9), (-0.2, -0.9)):
        parts.append(V.rbox("RailPost", (x, y, z0 + 0.24 + hood_h + 0.12), (0.03, 0.03, 0.25), 0.01, V.simple("V_Yellow2", (0.7, 0.5, 0.05), 0.4)))
    parts.append(V.rbox("Rail", (-0.8, -0.9, z0 + 0.24 + hood_h + 0.25), (1.25, 0.035, 0.035), 0.012, V.simple("V_Yellow2", (0.7, 0.5, 0.05), 0.4)))
    parts.append(V.lamp("WorkLamp", (cx1 - 0.05, (cy0 + cy1) / 2, z0 + cz0 + cz1 + 0.05), (0.1, 0.18, 0.1), "head", 0.02))
    parts.append(V.rbox("BoomFoot", (L_front - 0.15, -0.05, z0 + 0.45), (0.5, 0.7, 0.5), 0.06, pm))
    parts.append(V.rbox("RamMount", (L_front + 0.15, -0.05, z0 + 0.2), (0.4, 0.95, 0.25), 0.04, pm))
    return parts


def boom_mesh(name, pts, hs, width, m, up=(0, 1, 0)):
    """Box-section boom swept along points in the local x-z plane with depth profile hs."""
    path = [(x, 0, z) for (x, z) in pts]
    return V.sweep(name, path, V.rounded_rect(1.0, 1.0, 0.12, 3), m, up=up, scales=[(h, width) for h in hs], sharp=60)


def hose(name, pts, r=0.022):
    return V.sweep(name, pts, [(r * math.cos(a), r * math.sin(a)) for a in [k * math.pi / 4 for k in range(8)]],
                   V.rubber(), up=(0, 1, 0) if abs(pts[1][1] - pts[0][1]) < 0.5 else (0, 0, 1), cap=True, sharp=80)


def pin(name, c, r, w, m=None):
    return V.cylinder(name, c, r, w, m or V.steel_dark(), axis='Y', verts=20)


def tag_part(o, name):
    o["part"] = name
    return o


def excavator(variant=None):
    pm = heavy_paint("Exc")
    parts = []
    undercarriage(parts)
    base = V.join(parts, "Excavator")
    zr = 0.92 + 0.13
    house = V.join(house_parts("Exc", tail_r=2.08), "ExcHouse"); house.parent = base; house.location = (0, 0, zr)
    tag_part(house, "house")
    # boom (banana), stick, bucket
    bp = (1.05, -0.05, 0.55)
    bpts = [(-0.15, 0.0), (0.6, 0.55), (1.6, 1.35), (2.6, 1.95), (3.3, 2.05), (4.4, 1.55), (5.5, 0.95), (5.85, 0.75)]
    bhs = [0.55, 0.6, 0.72, 0.82, 0.85, 0.7, 0.55, 0.5]
    hs = [hose("Hose", [(x, s_ * 0.2, z + h * 0.5 + 0.03) for (x, z), h in zip(bpts[1:-1], bhs[1:-1])]) for s_ in (-1, 1)]
    boom = V.join([boom_mesh("Boom", bpts, bhs, 0.52, pm), pin("Pin", (0, 0, 0), 0.09, 0.62), pin("Pin", (5.7, 0, 0.84), 0.09, 0.6)] + hs, "ExcBoom")
    boom.parent = house; boom.location = bp; tag_part(boom, "boom")
    tip = Vector((5.7, 0, 0.84))
    spts = [(-0.55, 0.42), (-0.2, 0.1), (0.1, -0.5), (0.35, -1.6), (0.5, -2.65)]
    stick = V.join([boom_mesh("Stick", spts, [0.5, 0.58, 0.55, 0.45, 0.36], 0.4, pm), pin("Pin", (0.5, 0, -2.7), 0.07, 0.5)], "ExcStick")
    stick.parent = boom; stick.location = tip; tag_part(stick, "stick")
    bucket = make_bucket(pm); bucket.parent = stick; bucket.location = (0.5, 0, -2.7); tag_part(bucket, "bucket")
    ram("BoomRamL", house, (1.35, 0.30, 0.22), boom, (2.1, 0.32, 1.22), r=0.1, rod_r=0.06)
    ram("BoomRamR", house, (1.35, -0.40, 0.22), boom, (2.1, -0.42, 1.22), r=0.1, rod_r=0.06)
    ram("StickRam", boom, (2.4, 0, 2.15), stick, (-0.55, 0, 0.62), r=0.095, rod_r=0.055)
    ram("BucketRam", stick, (-0.1, 0, 0.3), bucket, (-0.15, 0, 0.12), r=0.075)
    pose_arm(base, 0, -15, 40, 70)
    return V._finish(base, "Excavator", (0.72, 0.48, 0.05))


def make_bucket(pm, width=1.0, scale=1.0):
    """Digging bucket: curved shell, side plates, teeth. Local origin at the stick pin."""
    sc = scale
    shell = [(0.05, -0.05), (-0.28, -0.32), (-0.33, -0.72), (-0.12, -1.02), (0.25, -1.16), (0.68, -1.05)]
    shell = [(x * sc, z * sc) for x, z in shell]
    sh = V.sweep("Shell", [(x, 0, z) for x, z in shell], V.rounded_rect(0.03, width, 0.01, 1), pm, up=(0, 1, 0), sharp=70)
    parts = [sh]
    poly = shell + [(0.15 * sc, -0.12 * sc)]
    for s in (-1, 1):
        vs = [(x, s * width / 2, z) for (x, z) in poly]
        side = V.mesh_obj("Side", vs, [tuple(range(len(vs)))], [pm], smooth=False)
        sd = side.modifiers.new("t", 'SOLIDIFY'); sd.thickness = 0.03; V.bake(side)
        parts.append(side)
    for k in range(5):
        y = -width * 0.4 + k * width * 0.2
        t = V.sweep("Tooth", [(0.62 * sc, y, -1.06 * sc), (0.80 * sc, y, -1.02 * sc)], V.rounded_rect(0.07, 0.07, 0.01, 1), V.steel_dark(),
                    up=(0, 1, 0), scales=[(1, 1), (0.35, 0.6)])
        parts.append(t)
    parts.append(pin("Pin", (0, 0, 0), 0.06, width))
    return V.join(parts, "Bucket")


def pose_arm(root, swing=None, boom=None, stick=None, bucket=None):
    """Pose an excavator / grab-crane arm in degrees (boom negative = raise; stick / bucket positive = curl in).
    A grab hangs plumb under the stick whatever the pose."""
    for nm, v, ax in (("house", swing, 2), ("boom", boom, 1), ("stick", stick, 1), ("bucket", bucket, 1)):
        p = V.part(root, nm)
        if p is not None and v is not None:
            p.rotation_euler[ax] = math.radians(v)
    g = V.part(root, "grab")
    if g is not None:
        b, s = V.part(root, "boom"), V.part(root, "stick")
        g.rotation_euler[1] = -(b.rotation_euler[1] + s.rotation_euler[1])


V.pose_arm = pose_arm


# ============================================================================ grab crane (scrap material handler)
def make_grab(pm, n=5, r=0.55):
    """Orange-peel grab: rotator + motor housing, with n curved tines (children 'tine_k') that open and close."""
    hub = V.join([V.cylinder("Rot", (0, 0, -0.18), 0.22, 0.25, V.steel_dark(), axis='Z', verts=24),
                  V.cylinder("Body", (0, 0, -0.62), 0.5, 0.6, pm, axis='Z', verts=32, r2=0.30),
                  V.cylinder("Cap", (0, 0, -0.95), 0.52, 0.1, V.steel_dark(), axis='Z', verts=32),
                  V.rbox("Link", (0, 0, 0.0), (0.14, 0.3, 0.2), 0.03, V.steel_dark())], "Grab")
    tines = []
    for k in range(n):
        a = 2 * math.pi * k / n
        pts = [(0.0, 0.0), (0.16, -0.2), (0.30, -0.55), (0.26, -0.9), (0.06, -1.18)]
        tn = V.sweep("Tine", [(x, 0, z) for x, z in pts], V.rounded_rect(0.07, 0.62, 0.03, 2), pm, up=(0, 1, 0),
                     scales=[(1, 0.55), (1, 0.95), (1, 1.0), (0.9, 0.75), (0.7, 0.3)], sharp=70)
        rib = V.sweep("Rib", [(x - 0.06, 0, z) for x, z in pts[:4]], V.rounded_rect(0.14, 0.05, 0.02, 1), pm, up=(0, 1, 0))
        tip = V.sweep("TineTip", [(0.12, 0, -1.08), (0.0, 0, -1.25)], V.rounded_rect(0.05, 0.12, 0.01, 1), V.steel_dark(), up=(0, 1, 0))
        t = V.join([tn, rib, tip], f"Tine{k}")
        t.parent = hub; t.location = (0.46 * math.cos(a), 0.46 * math.sin(a), -0.97)
        t.rotation_euler = (0, 0, a); t["part"] = f"tine_{k}"; t["tine"] = 1
        tines.append(t)
    return hub, tines


def set_grab(root, openness=1.0):
    """0 = closed (tines meet underneath), 1 = fully open."""
    for o in root.children_recursive:
        if o.get("tine"):
            o.rotation_euler[1] = math.radians(14 - 46 * openness)


V.set_grab = set_grab


def grab_crane(variant=None):
    pm = heavy_paint("Handler")
    parts = []
    undercarriage(parts, L=4.9, gauge=2.3, tw=0.6, h=0.98)
    base = V.join(parts, "GrabCrane")
    zr = 0.98 + 0.13
    hp = house_parts("Handler", L_front=1.25, L_rear=-1.9, W=2.6, cab=(-0.2, 1.35, 0.3, 1.3, 1.6, 1.75), tail_r=2.22, hood_h=1.15)
    # the cab rides high on a riser for a view into the scrap pile
    hp.append(V.rbox("Riser", (0.55, 0.8, 0.24 + 0.68), (1.0, 0.65, 1.36), 0.05, heavy_paint("HandlerRiser")))
    hp.append(V.rbox("Ladder", (-0.05, 1.32, 0.9), (0.4, 0.04, 1.4), 0.01, V.steel_dark()))
    house = V.join(hp, "HandlerHouse"); house.parent = base; house.location = (0, 0, zr); tag_part(house, "house")
    bpts = [(-0.15, 0.0), (1.5, 1.2), (3.5, 2.7), (6.0, 4.2), (8.2, 5.0), (9.0, 5.1)]
    boom = V.join([boom_mesh("Boom", bpts, [0.6, 0.75, 0.85, 0.75, 0.6, 0.55], 0.55, pm), pin("Pin", (0, 0, 0), 0.1, 0.64),
                   pin("Pin", (8.9, 0, 5.1), 0.09, 0.62)], "HandlerBoom")
    boom.parent = house; boom.location = (1.15, -0.2, 0.6); tag_part(boom, "boom")
    spts = [(-0.7, 0.45), (-0.2, 0.1), (0.4, -1.5), (1.1, -4.2), (1.4, -5.6)]
    gh = [hose("GrabHose", [(0.55, s_ * 0.27, -2.0), (0.95, s_ * 0.27, -4.4), (1.25, s_ * 0.33, -5.25), (1.5, s_ * 0.22, -5.62), (1.42, s_ * 0.14, -5.82)], 0.028)
          for s_ in (-1, 1)]
    stick = V.join([boom_mesh("Stick", spts, [0.5, 0.6, 0.55, 0.45, 0.38], 0.42, pm), pin("Pin", (1.4, 0, -5.65), 0.08, 0.5)] + gh, "HandlerStick")
    stick.parent = boom; stick.location = (8.9, 0, 5.1); tag_part(stick, "stick")
    grab, tines = make_grab(pm)
    grab.parent = stick; grab.location = (1.4, 0, -5.75); tag_part(grab, "grab")
    ram("BoomRamL", house, (1.0, 0.25, 0.3), boom, (3.4, 0.25, 2.2), r=0.1, rod_r=0.06)
    ram("BoomRamR", house, (1.0, -0.65, 0.3), boom, (3.4, -0.65, 2.2), r=0.1, rod_r=0.06)
    ram("StickRam", boom, (6.0, 0, 4.75), stick, (-0.7, 0, 0.72), r=0.09)
    pose_arm(base, 0, -10, 28)
    set_grab(base, 0.55)
    return V._finish(base, "GrabCrane", (0.10, 0.22, 0.09))


# ============================================================================ boom truck (truck-mounted telescopic boom)
def boom_truck(variant=None):
    XF, XR, R, RIM = 2.55, -1.45, 0.40, 0.225
    parts, heads = cab_1990s(3.40, tag="CabBT")
    truck_chassis(parts, -3.55, 3.2, 0.82)
    dk, bp = V.steel_dark(), V.black_plastic()
    cm = heavy_paint("Crane", col=(0.75, 0.47, 0.04))
    x0, x1, BW, DZ = -3.65, 1.62, 2.30, 1.22
    parts.append(V.rbox("Deck", ((x0 + x1) / 2, 0, DZ), (x1 - x0, BW, 0.06), 0.008, deck_mat()))
    parts.append(V.rbox("DeckFrame", ((x0 + x1) / 2, 0, DZ - 0.07), (x1 - x0, BW + 0.02, 0.10), 0.01, dk))
    # outriggers (front and rear) and the crane pedestal behind the cab
    for x in (1.25, -3.3):
        parts.append(V.rbox("OutBox", (x, 0, 0.95), (0.3, 2.5, 0.25), 0.03, cm))
        for s in (-1, 1):
            parts.append(V.rbox("OutLeg", (x, s * 1.22, 0.72), (0.18, 0.18, 0.5), 0.03, cm))
            parts.append(V.rbox("OutPad", (x, s * 1.22, 0.45), (0.34, 0.34, 0.05), 0.02, dk))
    parts.append(V.cylinder("Pedestal", (1.25, 0, 1.55), 0.38, 0.6, cm, axis='Z', verts=32))
    parts.append(V.cylinder("Tank", (0.2, -0.78, 0.78), 0.26, 1.0, V.alu(), axis='X', verts=32))
    parts.append(fender("FenderF", XF, R, R + 0.07, 0.93, 0.38, bp))
    parts.append(fender("FenderF", XF, R, R + 0.07, -0.93, 0.38, bp))
    for s in (-1, 1):
        parts.append(fender("FenderR", XR, R, R + 0.08, s * 0.80, 0.66, bp))
        parts.append(V.lamp(f"Tail{s}", (x0 - 0.03, s * 0.92, 0.80), (0.06, 0.30, 0.12), "tail", 0.015, facing=-1))
    parts.append(V.rbox("LampBar", (x0 + 0.02, 0, 0.80), (0.05, 2.12, 0.09), 0.01, dk))
    parts.append(V.rbox("BoomRest", (-3.0, 0, 1.86), (0.16, 0.16, 1.2), 0.02, cm))
    parts.append(V.rbox("BoomRestTop", (-3.0, 0, 2.48), (0.2, 0.62, 0.06), 0.02, cm))
    body = V.join(parts, "BoomTruck")
    turret = V.join([V.cylinder("Slew", (0, 0, 0.1), 0.42, 0.2, dk, axis='Z', verts=32),
                     V.rbox("Mast", (0.0, 0, 0.5), (0.62, 0.62, 0.8), 0.08, cm, sub=1),
                     V.rbox("Seat", (0.05, 0.6, 0.42), (0.4, 0.4, 0.45), 0.06, V.interior()),
                     V.rbox("Controls", (0.32, 0.6, 0.75), (0.06, 0.34, 0.16), 0.02, dk)], "Turret")
    turret.parent = body; turret.location = (1.25, 0, 1.85); turret.rotation_euler = (0, 0, math.pi)
    tag_part(turret, "turret")
    # three-section telescopic boom along turret +X (towards the truck rear when stowed, resting on the rest)
    BL = 4.5
    b1 = V.join([V.rbox("Boom1", (BL / 2 - 0.2, 0, 0), (BL, 0.46, 0.52), 0.06, cm, sub=1), pin("Pin", (0, 0, 0), 0.09, 0.62)], "Boom")
    b1.parent = turret; b1.location = (0.05, 0, 0.82); tag_part(b1, "boom")
    b2 = V.join([V.rbox("Boom2", (BL / 2 - 0.2, 0, 0.0), (BL, 0.38, 0.43), 0.05, cm, sub=1)], "BoomExt")
    b2.parent = b1; b2.location = (0.35, 0, 0.0); tag_part(b2, "boom_ext")
    b3 = V.join([V.rbox("Boom3", (BL / 2 - 0.2, 0, 0.0), (BL, 0.31, 0.35), 0.04, cm, sub=1),
                 V.rbox("Head", (BL - 0.05, 0, -0.04), (0.3, 0.34, 0.45), 0.04, cm),
                 V.cylinder("Sheave", (BL + 0.05, 0, -0.1), 0.16, 0.1, dk, axis='Y', verts=24)], "BoomExt2")
    b3.parent = b2; b3.location = (0.3, 0, 0.0); tag_part(b3, "boom_ext2")
    hook = V.join([V.cylinder("Cable", (0, 0, -0.35), 0.012, 0.7, dk, axis='Z', verts=8),
                   V.rbox("Block", (0, 0, -0.8), (0.22, 0.16, 0.3), 0.04, V.simple("V_HookYellow", (0.8, 0.55, 0.03), 0.4)),
                   V.sweep("Hook", [(0.0, 0, -0.95), (0.0, 0, -1.1), (0.1, 0, -1.2), (0.15, 0, -1.1)], V.rounded_rect(0.04, 0.04, 0.015, 2), dk, up=(0, 1, 0))], "Hook")
    hook.parent = b3; hook.location = (BL + 0.05, 0, -0.2); tag_part(hook, "hook")
    ram("LuffRam", turret, (0.3, 0, 0.25), b1, (1.4, 0, -0.27), r=0.085, rod_r=0.05)
    b1.rotation_euler = (0, math.radians(1.0), 0)
    me = V.wheel_mesh("truck_f", R, 0.22, RIM, "truckgrey")
    md = V.wheel_mesh("truck_d", R, 0.22, RIM, "truckgrey", dual=True)
    for s in (-1, 1):
        V.add_wheel(body, me, XF, s * 0.92, R, R, RIM, s)
        V.add_wheel(body, md, XR, s * 0.98, R, R, RIM, s)
    return V._finish(body, "BoomTruck", (0.85, 0.85, 0.82), heads=heads)


def register(K):
    K["excavator"] = excavator
    K["grab_crane"] = grab_crane
    K["boom_truck"] = boom_truck


# ============================================================================ concrete mixer truck
def drum_mat():
    def masks(g):
        ang = g.math('ARCTAN2', g.z, g.y)
        u = V.E(g, g.math('FRACT', ang / (2 * math.pi) + g.x / -1.6).s)
        stripe = g.inside(u, 0.0, 0.16, 0.01)                         # painted spiral bands following the blades
        splat = g.clamp(g.ss(0.55, 0.68, g.noise(2.2, 6.0, 0.7)) + g.ss(-3.6, -4.6, g.x) * 0.8)
        drips = g.ss(0.62, 0.72, g.noise_s(6.0, 2.0, 2.0, 0.15)) * g.ss(0.2, -0.4, g.z)
        crust = g.clamp(splat * 0.85 + drips * 0.9)
        return dict(livery=[(stripe, (0.85, 0.85, 0.82)), (crust, (0.52, 0.51, 0.47))])
    return V.paint_shader("V_Paint_Drum", masks, rough=0.45, fixed_color=(0.78, 0.36, 0.05))


def concrete_mixer(variant=None):
    from vehicles_cars import cab_1990s, truck_chassis, fender
    XF, XR1, XR2, R, RIM = 2.95, -1.55, -2.95, 0.45, 0.25
    parts, heads = cab_1990s(3.85, tag="CabMix")
    truck_chassis(parts, -4.3, 3.6, 0.85)
    dk, bp = V.steel_dark(), V.black_plastic()
    grey = V.paint_shader("V_Paint_MixerFrame", lambda g: {}, rough=0.5, fixed_color=(0.32, 0.33, 0.34))
    # drum supports: front pedestal, rear roller frame, water tank, hopper and chute frame
    parts.append(V.rbox("FrontStand", (1.95, 0, 1.45), (0.35, 1.3, 1.1), 0.05, grey))
    for s in (-1, 1):
        parts.append(V.rbox("RearLeg", (-2.07, s * 0.62, 1.42), (0.22, 0.18, 0.9), 0.03, grey))
        parts.append(V.cylinder("Roller", (-2.07, s * 0.55, 1.86), 0.12, 0.16, dk, axis='Y', verts=16))
        parts.append(V.rbox("Brace", (-2.7, s * 0.62, 1.3), (1.2, 0.12, 0.12), 0.02, grey, rot=(0, math.radians(-30), 0)))
    parts.append(V.rbox("RollerBeam", (-2.07, 0, 1.72), (0.3, 1.5, 0.16), 0.03, grey))
    for s in (-1, 1):
        parts.append(V.rbox("HopperLeg", (-3.8, s * 0.55, 2.4), (0.14, 0.14, 2.9), 0.02, grey))
    parts.append(V.cylinder("WaterTank", (2.25, 0, 2.45), 0.32, 1.6, V.paint_shader("V_Paint_MixerTank", lambda g: {}, rough=0.4,
                                                                                    fixed_color=(0.7, 0.7, 0.68)), axis='Y', verts=28))
    hop = V.lathe("Hopper", [(0.26, 0.0), (0.32, 0.25), (0.62, 0.75), (0.66, 0.8)], grey, 24, axis='Z')
    hop.data.transform(Matrix.Translation((-3.8, 0, 3.55))); parts.append(hop)
    chute = V.sweep("Chute", [(-3.85, 0, 2.75), (-4.35, 0, 2.45), (-4.95, 0, 2.05)],
                    [(-0.28, 0.0), (-0.24, -0.16), (0.0, -0.22), (0.24, -0.16), (0.28, 0.0), (0.24, -0.12), (0.0, -0.18), (-0.24, -0.12)],
                    grey, up=(0, 0, 1), cap=False, sharp=70)
    parts.append(chute)
    parts.append(V.rbox("ChuteSlide", (-3.95, 0, 2.95), (0.5, 0.6, 0.05), 0.02, grey))
    # ladder up the rear to the hopper platform
    for s in (-1, 1):
        parts.append(V.rbox("LadderRail", (-4.0, 0.8 + s * 0.22, 2.0), (0.04, 0.04, 2.5), 0.01, V.alu(), rot=(0, math.radians(-12), 0)))
    for k in range(8):
        z = 1.0 + k * 0.3
        parts.append(V.cylinder("Rung", (-4.0 - (z - 2.0) * 0.21, 0.8, z), 0.018, 0.44, V.alu(), axis='Y', verts=8))
    parts.append(V.rbox("Platform", (-4.25, 0.8, 3.3), (0.5, 0.6, 0.04), 0.01, V.alu()))
    # fenders over all three axles, under-run, lamps, plate
    parts.append(fender("FenderF", XF, R, R + 0.07, 0.95, 0.4, bp))
    parts.append(fender("FenderF", XF, R, R + 0.07, -0.95, 0.4, bp))
    for s in (-1, 1):
        parts.append(V.rbox("RearGuard", ((XR1 + XR2) / 2, s * 0.85, R + 0.55), (2.6, 0.62, 0.03), 0.01, bp))
        parts.append(V.rbox("Flap", (XR2 - 0.6, s * 0.85, 0.5), (0.01, 0.55, 0.6), 0.005, V.rubber()))
        parts.append(V.lamp(f"Tail{s}", (-4.35, s * 0.95, 0.9), (0.06, 0.28, 0.12), "tail", 0.015, facing=-1))
        parts.append(V.rbox("SideGuard", (0.4, s * 1.1, 0.8), (1.8, 0.03, 0.1), 0.01, V.alu()))
    parts.append(V.rbox("LampBar", (-4.32, 0, 0.9), (0.05, 2.1, 0.09), 0.01, dk))
    parts.append(V.rbox("Underrun", (-4.3, 0, 0.62), (0.08, 2.1, 0.12), 0.01, dk))
    parts.append(V.plate("PlateR", (-4.37, 0.0, 0.62), facing=-1))
    parts.append(V.cylinder("Tank", (0.6, -0.8, 0.8), 0.26, 0.9, V.alu(), axis='X', verts=28))
    body = V.join(parts, "ConcreteMixer")
    # the drum (part 'drum'): spins about its own axis = local X; tilted up towards the rear opening
    L = 5.7
    prof = [(0.0, 0.0), (0.45, -0.03), (0.95, -0.35), (1.17, -1.1), (1.2, -2.4), (1.12, -3.4), (0.88, -4.4), (0.62, -5.2),
            (0.55, -5.55), (0.6, -5.62), (0.62, -5.7)]
    dm = drum_mat()
    shell = V.lathe("DrumShell", [(r, h) for (r, h) in prof], dm, 56, axis='X')
    # lathe(axis='X') maps h -> +x; mirror so the opening points to -x
    fins = []
    for k in range(2):
        pts = []
        for i in range(90):
            t = i / 89.0
            x = -0.25 - t * 5.2
            ang = 2 * math.pi * (t * 3.2 + k * 0.5)
            # radius of the profile at this x
            r = 0.0
            for (r0, h0), (r1, h1) in zip(prof, prof[1:]):
                if h1 <= x <= h0:
                    r = r0 + (r1 - r0) * (x - h0) / (h1 - h0); break
            pts.append((x, (r + 0.025) * math.cos(ang), (r + 0.025) * math.sin(ang)))
        fins.append(V.sweep("Fin", pts, V.rounded_rect(0.05, 0.09, 0.015, 1), dm, up=(1, 0, 0), sharp=70))
    ring = V.lathe("Track", [(1.0, -4.0), (1.0, -4.2)], dk, 40, axis='X')
    gear = V.lathe("Gearbox", [(0.0, 0.25), (0.35, 0.2), (0.35, 0.0)], dk, 24, axis='X')
    drum = V.join([shell, ring, gear] + fins, "Drum")
    drum.parent = body; drum.location = (1.95, 0, 2.05); drum.rotation_euler = (0, math.radians(11), 0)
    drum["part"] = "drum"
    mf = V.wheel_mesh("mixer_f", R, 0.3, RIM, "truckgrey")
    md = V.wheel_mesh("mixer_d", R, 0.28, RIM, "truckgrey", dual=True)
    for s in (-1, 1):
        V.add_wheel(body, mf, XF, s * 0.98, R, R, RIM, s)
        for x in (XR1, XR2):
            V.add_wheel(body, md, x, s * 1.0, R, R, RIM, s)
    return V._finish(body, "ConcreteMixer", (0.86, 0.86, 0.84), heads=heads)


def spin_drum(root, angle_rad, keyframe_frame=None):
    """Turn the mixer drum about its own (tilted) axis."""
    d = V.part(root, "drum")
    d.rotation_euler[0] = angle_rad
    if keyframe_frame is not None:
        d.keyframe_insert("rotation_euler", index=0, frame=keyframe_frame)


V.spin_drum = spin_drum
_old_register = register


def register(K):
    _old_register(K)
    K["concrete_mixer"] = concrete_mixer
    V.DEFAULT_DIRT["concrete_mixer"] = 0.45
