"""Period vehicles for Moscow 1984 (generic, no badges): a boxy saloon, a larger saloon, a trolleybus,
a box-trailer truck. Each returns a root empty (front = +X) with child parts; wheels are listed for spinning."""
import math
import bpy, bmesh
from mathutils import Vector, Matrix
from kit import pbr, box, cyl, glass, emissive


def _prism_y(name, pts, w, mat, bevel=0.03):
    """Outline in (x, z), extruded across Y (width w), rounded edges."""
    bm = bmesh.new()
    a = [bm.verts.new((x, -w / 2, z)) for x, z in pts]
    b = [bm.verts.new((x, w / 2, z)) for x, z in pts]
    n = len(pts)
    bm.faces.new(a); bm.faces.new(b[::-1])
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((a[j], a[i], b[i], b[j]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(o)
    if bevel:
        bv = o.modifiers.new("bevel", 'BEVEL'); bv.width = bevel; bv.segments = 3; bv.limit_method = 'ANGLE'; bv.angle_limit = math.radians(20)
    for p in me.polygons:
        p.use_smooth = True
    o.modifiers.new("wn", 'WEIGHTED_NORMAL')
    me.materials.append(mat)
    return o


def _kid(o, root):
    o.parent = root; o.matrix_parent_inverse = Matrix.Identity(4)
    return o


_M = {}


def _mats():
    if not _M:
        _M["glass"] = pbr("CarGlass", (0.015, 0.02, 0.025), 0.04, 0.0, **{'Coat Weight': 1.0, 'Coat Roughness': 0.02})
        _M["chrome"] = pbr("CarChrome", (0.8, 0.8, 0.82), 0.12, 1.0)
        _M["tyre"] = pbr("Tyre", (0.018, 0.018, 0.02), 0.75)
        _M["rim"] = pbr("Rim", (0.45, 0.46, 0.48), 0.3, 1.0)
        _M["black"] = pbr("CarBlack", (0.02, 0.02, 0.022), 0.5)
        _M["lens"] = pbr("HeadLens", (0.9, 0.9, 0.85), 0.05, 0.0, **{'Transmission Weight': 0.6})
        _M["tail"] = pbr("TailLens", (0.45, 0.03, 0.02), 0.2)
        _M["arch"] = pbr("Arch", (0.01, 0.01, 0.01), 0.9)
    return _M


def _wheels(root, xs, half_w, r, M, out):
    for x in xs:
        for sy in (-1, 1):
            t = cyl("Tyre", (x, sy * half_w, r), r, 0.17, M["tyre"], verts=28, rot=(math.radians(90), 0, 0))
            hub = cyl("Hub", (x, sy * (half_w + 0.086), r), r * 0.55, 0.012, M["rim"], verts=20, rot=(math.radians(90), 0, 0))
            w = bpy.data.objects.new("Wheel", None); bpy.context.collection.objects.link(w)
            _kid(w, root); w.location = (x, sy * half_w, r)
            for o in (t, hub):
                o.parent = w; o.matrix_parent_inverse = Matrix.Translation((-x, -sy * half_w, -r))
            out.append(w)


def _box_saloon(name, color, length=4.15, width=1.62, big=False):
    """Boxy 1970s saloon. big=True: the longer, rounder-shouldered car with chrome trim."""
    M = _mats()
    root = bpy.data.objects.new(name, None); bpy.context.collection.objects.link(root)
    paint = pbr(name + "Paint", color, 0.3, 0.35, **{'Coat Weight': 0.8, 'Coat Roughness': 0.12})
    L = 4.75 if big else length; W_ = 1.8 if big else width
    hx = L / 2
    r = 0.32 if big else 0.3
    body = [(-hx, 0.28), (hx, 0.28), (hx + 0.02, 0.62), (hx - 0.12, 0.8), (hx * 0.38, 0.85), (-hx * 0.62, 0.86),
            (-hx + 0.04, 0.82), (-hx - 0.02, 0.58)]
    b = _kid(_prism_y(name + "_Body", body, W_, paint, 0.05), root)
    cab = [(hx * 0.38, 0.85), (hx * 0.06, 1.36 if not big else 1.42), (-hx * 0.42, 1.38 if not big else 1.43),
           (-hx * 0.66, 0.86)]
    _kid(_prism_y(name + "_Roof", cab, W_ - 0.12, paint, 0.06), root)
    # glass: side windows and screens set just proud of the cabin
    g = [(hx * 0.33, 0.9), (hx * 0.07, 1.31), (-hx * 0.4, 1.33), (-hx * 0.6, 0.9)]
    _kid(_prism_y(name + "_Glass", g, W_ - 0.1, M["glass"], 0.02), root)
    for k, x in enumerate((hx * 0.05 - 0.05, -hx * 0.18)):        # door pillars
        _kid(box("Pillar", (x, 0, 1.12), (0.06, W_ - 0.09, 0.42), paint), root)
    # wheel arches (dark), wheels, bumpers, lamps, grille
    for x in (hx - 0.82, -hx + 0.85):
        _kid(cyl("Arch", (x, 0, r), r + 0.05, W_ + 0.004, M["arch"], verts=28, rot=(math.radians(90), 0, 0)), root)
    wheels = []
    _wheels(root, (hx - 0.82, -hx + 0.85), W_ / 2 - 0.1, r, M, wheels)
    for sx in (-1, 1):
        _kid(box("Bumper", (sx * (hx + 0.06), 0, 0.42), (0.08, W_ + 0.04, 0.1), M["chrome"], bevel=0.02), root)
    _kid(box("Grille", (hx + 0.025, 0, 0.66), (0.02, W_ * 0.55, 0.15), M["black"]), root)
    for sy in (-1, 1):
        for dy in ((0.0,) if big else (0.0, 0.17)):
            y = sy * (W_ / 2 - 0.2 - dy)
            _kid(cyl("Head", (hx + 0.03, y, 0.66), 0.075, 0.03, M["lens"], verts=20, rot=(0, math.radians(90), 0)), root)
            _kid(cyl("HeadRim", (hx + 0.022, y, 0.66), 0.085, 0.02, M["chrome"], verts=20, rot=(0, math.radians(90), 0)), root)
        _kid(box("Tail", (-hx - 0.025, sy * (W_ / 2 - 0.22), 0.66), (0.03, 0.3, 0.12), M["tail"]), root)
        if big:
            _kid(box("Trim", (0, sy * (W_ / 2 + 0.003), 0.62), (L * 0.9, 0.01, 0.02), M["chrome"]), root)
        _kid(box("Handle", (hx * 0.0, sy * (W_ / 2 + 0.005), 0.8), (0.14, 0.02, 0.025), M["chrome"]), root)
        _kid(box("Mirror", (hx * 0.34, sy * (W_ / 2 + 0.06), 0.95), (0.06, 0.1, 0.07), M["black"]), root)
    return root, wheels


def _box_trolleybus(name, color=(0.62, 0.6, 0.52), stripe=(0.42, 0.12, 0.08)):
    """Boxy 1970s trolleybus with roof poles reaching up to the overhead wires (z ~ 5.6)."""
    M = _mats()
    root = bpy.data.objects.new(name, None); bpy.context.collection.objects.link(root)
    paint = pbr(name + "Paint", color, 0.35, 0.2, **{'Coat Weight': 0.5})
    st = pbr(name + "Stripe", stripe, 0.4, 0.2)
    L, W_, H = 11.8, 2.5, 3.1
    _kid(box("Body", (0, 0, 0.35 + H / 2), (L, W_, H), paint, bevel=0.12), root)
    _kid(box("Windows", (0, 0, 2.35), (L - 0.7, W_ + 0.01, 1.05), M["glass"], bevel=0.03), root)
    _kid(box("Screen", (L / 2 - 0.05, 0, 2.2), (0.06, W_ - 0.2, 1.3), M["glass"], bevel=0.05), root)
    _kid(box("Stripe", (0, 0, 1.4), (L + 0.01, W_ + 0.012, 0.16), st), root)
    _kid(box("Skirt", (0, 0, 0.55), (L - 0.2, W_ + 0.01, 0.3), M["black"]), root)
    for k in range(6):
        _kid(box("Pillar", (-L / 2 + 0.9 + k * 2.0, 0, 2.35), (0.08, W_ + 0.016, 1.06), paint), root)
    for x in (2.5, -2.0):
        _kid(box("Door", (x, -W_ / 2 - 0.006, 1.6), (1.2, 0.01, 2.3), M["glass"]), root)
    _kid(box("RoofPod", (0.5, 0, 0.35 + H + 0.12), (3.0, 1.2, 0.24), paint, bevel=0.05), root)
    poles = []
    for dy in (-0.3, 0.3):
        p = bpy.data.objects.new("PoleBase", None); bpy.context.collection.objects.link(p)
        _kid(p, root); p.location = (-1.0, dy, 0.35 + H + 0.25)
        pole = cyl("Pole", (0, 0, 0), 0.025, 5.6, M["black"], verts=8, rot=(0, math.radians(90 - 23), 0))
        pole.location = (-5.6 / 2 * math.cos(math.radians(23)), 0, 5.6 / 2 * math.sin(math.radians(23)))
        pole.parent = p; pole.matrix_parent_inverse = Matrix.Identity(4)
        poles.append(p)
    wheels = []
    _wheels(root, (L / 2 - 2.2, -L / 2 + 2.8), W_ / 2 - 0.15, 0.5, M, wheels)
    for sy in (-1, 1):
        _kid(cyl("Head", (L / 2 + 0.01, sy * 0.85, 0.9), 0.1, 0.03, M["lens"], verts=16, rot=(0, math.radians(90), 0)), root)
    return root, wheels


def _box_truck(name, cab_color=(0.24, 0.28, 0.22), trailer_color=(0.6, 0.6, 0.58)):
    """Tractor unit and a box trailer with twin rear doors (doors are separate pivots: c['doors'])."""
    M = _mats()
    root = bpy.data.objects.new(name, None); bpy.context.collection.objects.link(root)
    cab = pbr(name + "Cab", cab_color, 0.35, 0.2, **{'Coat Weight': 0.5})
    tr = pbr(name + "Trailer", trailer_color, 0.5, 0.4)
    _kid(box("Cab", (5.6, 0, 1.95), (1.9, 2.4, 2.3), cab, bevel=0.08), root)
    _kid(box("CabGlass", (6.56, 0, 2.45), (0.03, 2.1, 0.8), M["glass"]), root)
    _kid(box("CabSideGlass", (5.9, 0, 2.5), (0.9, 2.42, 0.6), M["glass"]), root)
    _kid(box("Chassis", (3.5, 0, 0.75), (7.0, 1.0, 0.3), M["black"]), root)
    _kid(box("Bumper", (6.6, 0, 0.7), (0.15, 2.4, 0.3), M["black"]), root)
    _kid(box("TrailerBox", (0.0, 0, 2.3), (9.5, 2.5, 2.7), tr, bevel=0.03), root)
    for k in range(12):
        _kid(box("Rib", (-4.6 + k * 0.85, 0, 2.3), (0.04, 2.52, 2.7), tr), root)
    doors = []
    for sy in (-1, 1):
        d = bpy.data.objects.new("DoorPivot", None); bpy.context.collection.objects.link(d)
        _kid(d, root); d.location = (-4.77, sy * 1.24, 2.3)
        leaf = box("Door", (0, -sy * 0.62, 0), (0.05, 1.22, 2.66), tr, bevel=0.01)
        bar = cyl("LockBar", (-0.045, -sy * 0.9, 0), 0.022, 2.55, M["chrome"], verts=8)
        bar2 = cyl("LockBar", (-0.045, -sy * 0.35, 0), 0.022, 2.55, M["chrome"], verts=8)
        hinges = [box("Hinge", (-0.03, -sy * 0.03, dz), (0.04, 0.1, 0.08), M["black"]) for dz in (-1.0, 0.0, 1.0)]
        seam = box("Seam", (-0.03, -sy * 1.215, 0), (0.02, 0.012, 2.6), M["black"])
        for o in [leaf, bar, bar2, seam] + hinges:
            o.parent = d; o.matrix_parent_inverse = Matrix.Identity(4)
        doors.append(d)
    _kid(box("Interior", (-0.2, 0, 2.3), (9.3, 2.38, 2.55), pbr("TrailerInside", (0.2, 0.2, 0.19), 0.8)), root)
    wheels = []
    _wheels(root, (5.6, 2.6), 1.05, 0.5, M, wheels)
    _wheels(root, (-2.8, -3.9), 1.05, 0.5, M, wheels)
    return root, wheels, doors


def _box_roll(wheels, dist, r):
    for w in wheels:
        w.rotation_euler = (0, dist / r, 0)



# ============================================================================ the shared vehicle kit (nvidia_doc/scenes/vehicles.py)
import vehicles as _K


def saloon(name, color, length=4.15, width=1.62, big=False):
    root = _K.make("sedan_1990s_soviet", color=color, dirt=0.25 if big else 0.15)
    root.name = name
    return root, [root]


def trolleybus(name, color=(0.62, 0.6, 0.52), stripe=None):
    """City bus body from the kit, with two trolley poles on the roof reaching up to the overhead wires."""
    root = _K.make("bus_city", color=color, dirt=0.2); root.name = name
    M = _mats()
    for dy in (-0.3, 0.3):
        p = bpy.data.objects.new("PoleBase", None); bpy.context.collection.objects.link(p)
        _kid(p, root); p.location = (-1.0, dy, 3.3)
        pole = cyl("Pole", (0, 0, 0), 0.025, 5.6, M["black"], verts=8, rot=(0, math.radians(90 - 23), 0))
        pole.location = (-5.6 / 2 * math.cos(math.radians(23)), 0, 5.6 / 2 * math.sin(math.radians(23)))
        pole.parent = p; pole.matrix_parent_inverse = Matrix.Identity(4)
    _kid(box("PoleBase", (-0.5, 0, 3.32), (1.4, 0.9, 0.12), M["black"]), root)
    return root, [root]


def truck(name, cab_color=(0.24, 0.28, 0.22), trailer_color=(0.6, 0.6, 0.58), boxy=False):
    """Box truck from the kit, with hinged twin rear doors added (pivots returned) for the sealing shots.
    boxy=True keeps the old placeholder with a hollow cargo box (only for the shot filmed from inside it)."""
    if boxy:
        return _box_truck(name, cab_color, trailer_color)
    root = _K.make("delivery_truck", color=trailer_color, dirt=0.2); root.name = name
    M = _mats()
    door_m = pbr(name + "DoorPaint", trailer_color, 0.5, 0.3)
    doors = []
    for sy in (-1, 1):
        d = bpy.data.objects.new("DoorPivot", None); bpy.context.collection.objects.link(d)
        _kid(d, root); d.location = (-3.79, sy * 1.2, 2.25)
        leaf = box("Door", (0, -sy * 0.6, 0), (0.04, 1.18, 2.3), door_m, bevel=0.01)
        bars = [cyl("LockBar", (-0.04, -sy * k, 0), 0.02, 2.35, M["chrome"], verts=8) for k in (0.3, 0.9)]
        hinges = [box("Hinge", (-0.03, -sy * 0.03, dz), (0.04, 0.1, 0.08), M["black"]) for dz in (-0.9, 0.0, 0.9)]
        for o in [leaf] + bars + hinges:
            o.parent = d; o.matrix_parent_inverse = Matrix.Identity(4)
        doors.append(d)
    return root, [root], doors


def roll(wheels, dist, r):
    for w in wheels:
        if w.get("vehicle_kind"):
            _K.spin_wheels(w, dist)
        else:
            w.rotation_euler = (0, dist / r, 0)
