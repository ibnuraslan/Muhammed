"""The Mary Celeste's yawl: a clinker-built ship's boat, about 6 m, built in code.

Frame: bow toward +X, keel on z = 0 (local), centreline y = 0. Everything a person touches (thwarts, oar
looms, tiller, gunwale) is exposed as world-space helpers so poses can reach real geometry.

    b = build("yawl", wet=0.6); b["root"].matrix_world = M
    b["thwart_top"](i) -> local z of thwart i;  b["thwarts"] -> list of x positions
"""
import math
import numpy as np
import bpy
from mathutils import Vector, Matrix
import ship

L, W, D = 6.0, 1.86, 0.70                     # length, beam, depth amidships
NPLANK = 8                                     # clinker strakes per side
THWARTS = [1.55, 0.55, -0.45, -1.35]           # x of the four thwarts (bow -> aft)
STERN_SHEETS = (-2.85, -1.75)                  # x span of the stern bench
SEAT_Z = 0.40                                  # thwart top above the keel
FLOOR_Z = 0.13                                 # bottom boards


def _s(x):
    return (x + L / 2) / L


def width(s):
    """Half-breadth at the sheer, s = 0 transom .. 1 stem."""
    s = min(max(s, 0.0), 1.0)
    if s >= 0.42:
        u = (s - 0.42) / 0.58
        return W / 2 * max(0.0, 1 - u ** 2.1) ** 0.62
    u = (0.42 - s) / 0.42
    return W / 2 * (1 - 0.22 * u ** 1.7)


def keel_z(s):
    return 0.03 * (2 * s - 1) ** 2 + (0.10 * max(0, (s - 0.9) / 0.1) ** 2)


def sheer_z(s):
    return D + 0.16 * (2 * s - 1) ** 2 + 0.06 * max(0, s - 0.85) / 0.15


def section(s, t):
    """Point on the outer skin. t = 0 keel .. 1 sheer."""
    w = width(s)
    z0, z1 = keel_z(s), sheer_z(s)
    # rounded bilge: breadth grows fast off the keel then the sides stand up
    y = w * t ** 0.5                       # flat-ish floor, round bilge, flared topsides
    z = z0 + (z1 - z0) * t
    return Vector((-L / 2 + s * L, y, z))


def half_breadth_at(x, z):
    """Inner half-breadth of the hull at station x and height z (for thwart ends)."""
    s = _s(x); best = 0.0
    for k in range(121):
        t = k / 120; p = section(s, t)
        if p.z <= z:
            best = p.y
    return best - 0.03


def hull_mesh(name, mat_out, mat_in, ns=90, nt=8 * 6):
    verts, faces = [], []
    for i in range(ns + 1):
        s = i / ns
        for j in range(nt + 1):
            t = j / nt
            p = section(s, t)
            # clinker: each strake laps over the one below -> sawtooth outward step
            ph = (t * NPLANK) % 1.0
            step = 0.012 * ph if t < 0.999 else 0.012
            n = Vector((0, 1, 0.25 * (1 - t))).normalized()
            p = p + n * step
            verts.append((p.x, p.y, p.z))
    row = nt + 1
    for i in range(ns):
        for j in range(nt):
            a = i * row + j
            faces.append([a, a + row, a + row + 1, a + 1])
    # mirror to port
    n0 = len(verts)
    verts += [(x, -y, z) for (x, y, z) in verts]
    faces += [[f[0] + n0, f[3] + n0, f[2] + n0, f[1] + n0] for f in faces]
    o = ship.mesh_obj(name, verts, faces, mat_out, smooth=True)
    o.data.materials.append(mat_in)
    m = bpy.ops.object
    bpy.context.view_layer.objects.active = o
    o.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.remove_doubles(threshold=0.004); bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.mode_set(mode='OBJECT'); o.select_set(False)
    so = o.modifiers.new("Thick", "SOLIDIFY"); so.thickness = 0.022; so.offset = -1; so.material_offset = 1
    so.use_even_offset = True
    return o


def transom(name, mat):
    s = 0.0; pts = []
    for j in range(25):
        p = section(s, j / 24); pts.append((p.x, p.y, p.z))
    vs = [(p[0] - 0.01, p[1], p[2]) for p in pts] + [(p[0] - 0.01, -p[1], p[2]) for p in reversed(pts)]
    me = bpy.data.meshes.new(name); me.from_pydata(vs, [], [list(range(len(vs)))]); me.update()
    o = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(o); o.data.materials.append(mat)
    so = o.modifiers.new("Thick", "SOLIDIFY"); so.thickness = 0.04; so.offset = 1
    return o


def build(name="yawl", wet=0.6, oars="out", oar_angle=None, rudder=True, painter=None, boated=()):
    """oars: "out" (shipped in the rowlocks, blades in the water), "in" (laid along the thwarts) or None.
    painter: optional world end point for the bow line (a rope to the ship)."""
    coll = bpy.data.collections.new(name); bpy.context.scene.collection.children.link(coll)
    root = bpy.data.objects.new(name + "_root", None); coll.objects.link(root)
    # old white lead paint gone to a dirty cream-grey, grimy streaks, worn through to the grey wood in soft patches
    outside = ship.paint(name + "_paint", (0.13, 0.125, 0.11), rough=0.66, grime=0.9, wet=wet, scale=2.5, chips=0.25,
                         under=(0.08, 0.07, 0.055))
    inside = ship.wood("weathered_planks", 0.8, wet=wet * 0.8, tint=(0.6, 0.5, 0.4), name=name + "_inwood")
    seat = ship.wood("weathered_planks", 1.1, wet=wet * 0.6, tint=(0.62, 0.5, 0.38), name=name + "_seat")
    trim = ship.paint(name + "_trim", (0.05, 0.08, 0.06), rough=0.4, grime=0.4, wet=wet, scale=5, chips=0.3)
    rope_m = ship.tarred_rope(name + "_rope", (0.16, 0.12, 0.07))
    objs = []
    hull = hull_mesh(name + "_hull", outside, inside); objs.append(hull)
    objs.append(transom(name + "_transom", inside))
    # gunwale capping, port and starboard
    for sg in (1, -1):
        pts = [section(i / 60, 1.0) for i in range(61)]
        pts = [Vector((p.x, sg * (p.y + 0.004), p.z + 0.012)) for p in pts]
        objs.append(ship.rope(f"{name}_gunwale{sg}", pts, 0.026, trim))
    # stem post
    stem = [section(1.0, j / 10) + Vector((0.02, 0, 0)) for j in range(11)]
    objs.append(ship.rope(name + "_stem", stem, 0.035, trim))
    # keel strip
    objs.append(ship.rope(name + "_keel", [section(i / 30, 0) + Vector((0, 0, -0.03)) for i in range(31)], 0.03, trim))
    # bottom boards
    for k in range(-3, 4):
        y = k * 0.13
        xs = [x for x in np.linspace(-L / 2 + 0.5, L / 2 - 0.9, 30) if half_breadth_at(x, FLOOR_Z + 0.02) > abs(y) + 0.07]
        if xs:
            objs.append(ship.box(f"{name}_board{k}", ((xs[0] + xs[-1]) / 2, y, FLOOR_Z), (xs[-1] - xs[0], 0.115, 0.022), seat))
    # thwarts
    for i, x in enumerate(THWARTS):
        hb = half_breadth_at(x, SEAT_Z)
        objs.append(ship.box(f"{name}_thwart{i}", (x, 0, SEAT_Z - 0.02), (0.24, 2 * hb, 0.04), seat, bevel=0.006))
        # knees under the ends
        for sg in (1, -1):
            objs.append(ship.box(f"{name}_knee{i}{sg}", (x, sg * (hb - 0.05), SEAT_Z - 0.12), (0.06, 0.08, 0.2), seat))
    # stern sheets: a bench across the stern, deeper on the port side (the helmsman's side is shallow so his knees
    # clear its edge and his feet reach the bottom boards); open forward of it for the feet
    x0, x1 = STERN_SHEETS
    for nm, xb, sgn in (("_sternseat", -2.27, 1), ("_sternseatp", -1.95, -1)):
        hb = half_breadth_at((x0 + xb) / 2, SEAT_Z)
        objs.append(ship.box(name + nm, ((x0 + xb) / 2, sgn * hb / 2, SEAT_Z - 0.02), (xb - x0, hb, 0.04), seat, bevel=0.006))
    # rowlocks (pairs of thole pins) at each rowing thwart
    tholes = {}
    for i, x in enumerate(THWARTS[:3]):
        xr = x - 0.45                    # rowlocks well aft of the thwart: the loom stays in front of the rower
        for sg in (1, -1):
            p = section(_s(xr), 1.0); top = Vector((xr, sg * p.y, p.z + 0.03))
            for dx in (-0.045, 0.045):
                objs.append(ship.cyl(f"{name}_thole{i}{sg}{dx}", top + Vector((dx, 0, 0)), top + Vector((dx, 0, 0.11)), 0.012, mat=seat, verts=10))
            tholes[(i, sg)] = top + Vector((0, 0, 0.05))
    # rudder and tiller
    tiller = None
    if rudder:
        p0 = section(0.0, 0.0); p1 = section(0.0, 1.0)
        rv = [(p0.x - 0.04, 0, p0.z - 0.25), (p0.x - 0.42, 0, p0.z - 0.25), (p1.x - 0.24, 0, p1.z - 0.05), (p1.x - 0.04, 0, p1.z + 0.05)]
        r = ship.mesh_obj(name + "_rudder", rv, [[0, 1, 2, 3]], trim, smooth=False)
        so = r.modifiers.new("Thick", "SOLIDIFY"); so.thickness = 0.035; so.offset = 0; objs.append(r)
        head = Vector((p1.x - 0.08, 0, p1.z + 0.03)); tip = head + Vector((0.86, 0.0, -0.2))   # slopes down to lap height
        objs.append(ship.cyl(name + "_tiller", head, tip, 0.022, 0.016, mat=seat, verts=12))
        tiller = tip - Vector((0.12, 0, 0))
    # oars: loom through the rowlocks; handle inboard, blade outboard and down into the sea
    oar_handles = {}; oar_dirs = {}
    oar_m = ship.wood("brown_planks_05", 2.0, wet=wet, tint=(0.95, 0.85, 0.66), name=name + "_oarwood")
    if oars == "out":
        for (i, sg), pv in tholes.items():
            if sg in boated:
                continue
            ang = (oar_angle or {}).get((i, sg), 0.0)
            d = Vector((math.sin(math.radians(ang)), sg * math.cos(math.radians(ang)), -0.13)).normalized()
            # inboard length: the handle ends ~0.24 m off the centreline, so the two men on a thwart keep apart
            inb = 0.84 if abs(ang) > 60 else max(0.5, (abs(pv.y) - 0.24) / max(0.5, abs(d.y)))
            handle = pv - d * inb
            blade_root = pv + d * 1.6; tip = pv + d * 2.45
            objs.append(ship.cyl(f"{name}_oar{i}{sg}", handle, blade_root, 0.024, 0.02, mat=oar_m, verts=12))
            bl = ship.box(f"{name}_blade{i}{sg}", (blade_root + tip) / 2, (0.15, (tip - blade_root).length, 0.016), oar_m, bevel=0.004)
            bl.rotation_mode = 'QUATERNION'
            bl.rotation_quaternion = d.to_track_quat('Y', 'Z'); objs.append(bl)
            oar_handles[(i, sg)] = handle + d * 0.18
            oar_dirs[(i, sg)] = d.copy()
    # boated oars (alongside a ship): laid fore-and-aft along the middle of the boat, resting on the thwarts between
    # the two rows of men (below their hands, clear of their legs), blades toward the bow
    for k, sg in enumerate(sorted(boated)):
        for j in range(3):
            yo = 0.045 * (j - 1); zo = SEAT_Z + 0.025 + 0.048 * k          # a second side's oars lie on top
            a = Vector((-1.05, yo, zo)); b2 = Vector((1.85, yo, zo))
            objs.append(ship.cyl(f"{name}_oarboated{sg}{j}", a, b2, 0.024, mat=oar_m, verts=12))
            bl = ship.box(f"{name}_bladeboated{sg}{j}", b2 + Vector((0.42 + 0.9 * k, 0, 0.004)), (0.84, 0.05, 0.016), oar_m, bevel=0.004)
            objs.append(bl)
    if oars == "in":
        for k, sg in enumerate((1, -1, 1, -1)):
            y = sg * (0.25 + 0.12 * (k // 2))
            objs.append(ship.cyl(f"{name}_oarin{k}", Vector((-1.6, y, SEAT_Z + 0.03)), Vector((2.0, y, SEAT_Z + 0.08)), 0.024, mat=oar_m, verts=12))
    # painter: bow ring -> rope
    ring = section(1.0, 0.92) + Vector((0.03, 0, 0))
    for o in objs:
        _link(o, coll)
        o.parent = root
    return dict(root=root, coll=coll, hull=hull, tholes=tholes, oar_handles=oar_handles, oar_dirs=oar_dirs, tiller=tiller, ring=ring,
                mats=dict(rope=rope_m, seat=seat), seat_z=SEAT_Z, floor_z=FLOOR_Z, thwarts=THWARTS)


def _link(o, coll):
    for c in list(o.users_collection):
        c.objects.unlink(o)
    coll.objects.link(o)


def painter(name, a, b, mat, sag=0.25):
    """Rope from world a to world b with a catenary-ish sag (taut when sag is small)."""
    pts = []
    for k in range(25):
        t = k / 24
        p = a.lerp(b, t); p = p - Vector((0, 0, sag * 4 * t * (1 - t)))
        pts.append(p)
    return ship.rope(name, pts, 0.011, mat)
