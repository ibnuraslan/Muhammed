"""New Part 1 asset (not in the shared library): a 16 ft clinker ship's boat, the kind the Dei Gratia sent across.
Bow toward +X, gunwale at z = GUN, waterline z = 0 when floated at loc z = 0. Built in code like lib/ship.py.

    b = build("DGboat"); b["root"].matrix_world = ...        seats: b["thwarts"] (local points to sit on)"""
import math
import bpy
from mathutils import Vector, Matrix
import ship

LB, BB, DEPTH = 4.9, 1.62, 0.66
GUN = 0.42                    # gunwale height above the waterline (laden with three men)


def _hb(s, t):
    """half breadth at s (0 stern .. 1 bow), t (0 keel .. 1 gunwale)."""
    sec = (1 - (1 - t) ** 2.2) ** (1 / 2.2) * 0.92 + 0.08
    if s > 0.6:
        pl = (1 - ((s - 0.6) / 0.4) ** 1.8) ** 0.7
    elif s < 0.18:
        pl = 0.62 + 0.38 * (s / 0.18) ** 0.6
    else:
        pl = 1.0
    return BB / 2 * sec * max(pl, 0.0)


def build(name="boat", oars_out=True):
    coll = bpy.data.collections.new(name); bpy.context.scene.collection.children.link(coll)
    paint = ship.paint(name + "_paint", (0.38, 0.3, 0.2), rough=0.45, grime=0.6, chips=0.5, wet=0.6, scale=4)
    inner = ship.wood("brown_planks_05", 1.6, wet=0.5, tint=(0.8, 0.6, 0.42), name=name + "_inner")
    strake = ship.paint(name + "_strake", (0.05, 0.12, 0.16), rough=0.4, grime=0.4, wet=0.6, scale=4)
    ns, nt = 60, 14; V = []; idx = {}
    for j in range(nt + 1):
        t = j / nt
        for i in range(ns + 1):
            s = i / ns
            x = -LB / 2 + s * LB
            z = GUN - DEPTH + t * DEPTH + 0.12 * ((s - 0.5) * 2) ** 2 * t      # sheer rises at both ends
            for side, sg in (("P", 1), ("S", -1)):
                idx[(i, j, side)] = len(V); V.append((x, sg * _hb(s, t), z))
    F = []
    for j in range(nt):
        for i in range(ns):
            F.append([idx[(i, j, "P")], idx[(i + 1, j, "P")], idx[(i + 1, j + 1, "P")], idx[(i, j + 1, "P")]])
            F.append([idx[(i, j, "S")], idx[(i, j + 1, "S")], idx[(i + 1, j + 1, "S")], idx[(i + 1, j, "S")]])
    for i in range(ns):
        F.append([idx[(i, 0, "S")], idx[(i + 1, 0, "S")], idx[(i + 1, 0, "P")], idx[(i, 0, "P")]])
    for j in range(nt):
        F.append([idx[(0, j, "P")], idx[(0, j + 1, "P")], idx[(0, j + 1, "S")], idx[(0, j, "S")]])
    hull = ship.mesh_obj(name + "_hull", V, F, paint, coll=coll)
    hull.data.materials.append(inner)
    so = hull.modifiers.new("Thick", "SOLIDIFY"); so.thickness = 0.022; so.offset = 1; so.material_offset = 1
    # clinker laps: bump bands along the planking
    out = [hull]
    for k, (u0, u1) in enumerate(((0.55, 0.68), )):
        pass
    # gunwale rail (painted band) and thwarts
    for side, sg in (("P", 1), ("S", -1)):
        pts = []
        for i in range(ns + 1):
            s = i / ns; x = -LB / 2 + s * LB
            pts.append((x, sg * _hb(s, 1.0), GUN + 0.12 * ((s - 0.5) * 2) ** 2 + 0.015))
        out.append(ship.rope(f"{name}_gunwale{side}", pts, 0.028, strake, coll=coll))
    thw = []
    for xs in (-1.25, -0.1, 1.0):
        s = (xs + LB / 2) / LB; hb = _hb(s, 0.78)
        z = GUN - 0.2
        out.append(ship.box(f"{name}_thwart", (xs, 0, z), (0.22, 2 * hb, 0.04), inner, coll=coll, bevel=0.005))
        thw.append(Vector((xs, 0, z + 0.02)))
    out.append(ship.box(f"{name}_sternsheet", (-LB / 2 + 0.45, 0, GUN - 0.22), (0.7, 2 * _hb(0.08, 0.8), 0.04), inner, coll=coll))
    out.append(ship.box(f"{name}_floorboards", (0.1, 0, GUN - DEPTH + 0.1), (LB * 0.7, 0.7, 0.025), inner, coll=coll))
    # transom and stem
    out.append(ship.box(f"{name}_transom", (-LB / 2 + 0.01, 0, GUN - DEPTH / 2 + 0.05), (0.04, BB * 0.62, DEPTH * 0.95), paint, coll=coll))
    out.append(ship.cyl(f"{name}_stem", (LB / 2 - 0.02, 0, GUN - DEPTH + 0.05), (LB / 2 + 0.03, 0, GUN + 0.18), 0.04, mat=paint, coll=coll, verts=8))
    # oars: two pairs, blades in the water when out (looms rest in thole pins on the gunwale)
    oars = []
    if oars_out:
        spruce = ship.paint(name + "_oar", (0.5, 0.38, 0.22), rough=0.5, grime=0.3, scale=6)
        for xs in (-0.1, 1.0):
            for sg in (1, -1):
                # the thole pins are just aft of each thwart (the rowers face aft): handles come to the rower's lap
                s = (xs - 0.32 + LB / 2) / LB; hb = _hb(s, 1.0)
                pin = Vector((xs - 0.32, sg * hb, GUN + 0.12 * ((s - 0.5) * 2) ** 2 + 0.04))
                inboard = pin + Vector((-0.04, -sg * 0.78, 0.1))
                blade = pin + Vector((0.35, sg * 2.3, -0.5))
                o = ship.cyl(f"{name}_oar", inboard, blade, 0.022, 0.018, mat=spruce, verts=10, coll=coll)
                d = (blade - inboard).normalized()
                b = ship.box(f"{name}_blade", blade - d * 0.25, (0.6, 0.13, 0.015), spruce, coll=coll)
                b.rotation_euler = d.to_track_quat('X', 'Z').to_euler(); out += [o, b]
                oars.append((inboard, pin, blade))
    root = bpy.data.objects.new(name + "_root", None); coll.objects.link(root)
    for o in coll.objects:
        if o is not root and o.parent is None:
            o.parent = root
    return dict(root=root, hull=hull, thwarts=thw, oars=oars, coll=coll)
