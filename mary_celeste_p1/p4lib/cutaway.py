# Copied unchanged from branch claude/mary-celeste-p4, mary_celeste_p4/lib/cutaway.py (shared cutaway look across the film).
"""Explainer cutaway of the Mary Celeste (Atrium-style X-ray): the shared brigantine from ship.py, sliced on a
fore-aft vertical plane so the port half is removed and the hold is seen from the port side. Cut faces get a
section colour. Planking gets real thickness (frames + outer planking + ceiling) so the cut reads as solid."""
import math
import bpy, bmesh
from mathutils import Vector, Matrix
import ship
import p4

SECTION = (0.55, 0.12, 0.06)      # warm oxblood section colour (Atrium cutaway red)


def _bisect(o, y_cut, keep_neg=True):
    if o.type != 'MESH':
        return
    bm = bmesh.new(); bm.from_mesh(o.data)
    Mw = o.matrix_world; Mi = Mw.inverted()
    co = Mi @ Vector((0, y_cut, 0)); no = (Mi.to_3x3().transposed().inverted() @ Vector((0, 1, 0))).normalized() \
        if False else (Mw.to_3x3().transposed() @ Vector((0, 1, 0))).normalized()
    geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
    bmesh.ops.bisect_plane(bm, geom=geom, plane_co=co, plane_no=no, clear_outer=keep_neg, clear_inner=not keep_neg)
    bm.to_mesh(o.data); bm.free(); o.data.update()


def section_material():
    m = p4.mat("section", SECTION, rough=0.7)
    return m


def build(name="MCX", y_cut=0.02, sails=False, rigging=False, detail=True, thickness=0.26):
    s = ship.build(name, sails="found", rail_gap=None, detail=detail, wet=0.1, hatches_off=False, boat_chocks=True)
    root = s["root"]
    bpy.context.view_layer.update()
    sec = section_material()
    for o in list(s["coll"].all_objects):
        if o.type == 'CURVE':
            if not rigging:
                bpy.data.objects.remove(o, do_unlink=True)
            continue
        if o.type != 'MESH':
            continue
        if ("_sail" in o.name or "shred" in o.name or "furl" in o.name) and not sails:
            bpy.data.objects.remove(o, do_unlink=True); continue
        # bake modifiers that change shape (bevels), then cut
        if o.modifiers:
            dg = bpy.context.evaluated_depsgraph_get()
            me = bpy.data.meshes.new_from_object(o.evaluated_get(dg)); o.modifiers.clear(); o.data = me
        ws = [o.matrix_world @ v.co for v in o.data.vertices]
        if not ws:
            continue
        if min(w.y for w in ws) > y_cut:
            bpy.data.objects.remove(o, do_unlink=True); continue
        if max(w.y for w in ws) > y_cut:
            _bisect(o, y_cut)
            # a section cap colour on the cut: second material, assigned by a thin box at the plane later
    hull = bpy.data.objects.get(f"{name}_hull")
    if hull:
        so = hull.modifiers.new("Thick", "SOLIDIFY"); so.thickness = thickness; so.offset = -1.0
        so.use_rim = True; so.use_rim_only = False
        hull.data.materials.append(sec); so.material_offset_rim = len(hull.data.materials) - 1
        so.material_offset = 0
    hold_interior(name, y_cut)
    return s


def hold_interior(name, y_cut, inset=0.26, ns=90, nt=24):
    """Ceiling planking inside the frames (starboard half), deck beams and the keelson, in warm unpainted wood."""
    wood = ship.wood("brown_planks_05", 0.9, wet=0.15, tint=(0.95, 0.7, 0.5), name="ceiling_wood")
    V = []; F = []; UV = []
    for j in range(nt + 1):
        t = 0.06 + 0.9 * j / nt
        xs, xb = ship._ends(t)
        for i in range(ns + 1):
            s = 0.03 + 0.94 * i / ns
            x = xs + s * (xb - xs)
            y = -max(ship.half_breadth(s, t) - inset, 0.05)
            z = ship.hull_z(x, t) + inset * 0.6 * (1 - t)
            V.append((x, y, z)); UV.append((x * 0.4, z * 0.4 + y * 0.4))
    for j in range(nt):
        for i in range(ns):
            a = j * (ns + 1) + i
            F.append([a, a + ns + 1, a + ns + 2, a + 1])
    o = ship.mesh_obj(f"{name}_ceiling", V, F, wood)
    uv = o.data.uv_layers.new(name="UVMap")
    for l in o.data.loops:
        uv.data[l.index].uv = UV[l.vertex_index]
    # floor of the hold over the keelson
    ship.box(f"{name}_keelson", (0.8, -0.12, -2.62), (24.0, 0.32, 0.34), wood)
    ship.box(f"{name}_holdfloor", (0.8, -0.9, -2.47), (21.0, 1.8, 0.04), wood)
    # deck beams (seen end-on at the cut)
    x = -9.0
    while x < 11.0:
        zd = ship.zdeck(x); s = (x - ship._ends(1.0)[0]) / (ship._ends(1.0)[1] - ship._ends(1.0)[0])
        hb = ship.half_breadth(s, 0.98) - inset
        ship.box(f"{name}_beam", (x, -hb / 2 + y_cut / 2, zd - 0.17), (0.2, hb + y_cut, 0.22), wood)
        x += 1.15
    return o


def section_planes(name, y_cut, x0=-15.7, x1=15.7, mat=None):
    """Not used for meshes without volume; the hull's solidify rim already caps the cut."""
    return None
