"""AERIAL: the real lake shore from the air, realistic Cycles in look v5 (no graphics). About 1 km of the north shore:
the lake to the north, the reed belt, the gravel lakeside path through a mixed spruce-and-birch wood with its sharp
bend, the family's village to the east, the cousin's village to the west, fields and a road inland, the far shore in
haze. The clearing with the box lies in the wood south of the path.

  route  (Ch1 #3)  golden hour, 280 m up: a thin warm line draws itself along the path from the east village to the
                    west one ("she knows the route") while the camera drifts and turns slowly.
  meet   (Ch1 #6/7) blue hour: two torch lights come along the path from both ends and meet at the bend; slow
                    push down toward the bend.
  search (Ch1 #8)  night: torches come on along the path and fan out into the dark wood, a blue light pulses at the
                    end of the path, the village windows lit; slow descending orbit.
  back   (Ch2 #14) grey misty morning, autumn: above the small clearing the camera rises and pulls back toward the
                    path; a thin red line draws from the clearing to the bend ("back by the path, too").
Coordinates: metres; the bend at the origin; the lake north (+y).
"""
import math
import numpy as np
import bpy
from mathutils import Vector, Matrix
from kit import pbr, box, haze
from common import ease
import rj
from rj import mat
import rj_case as K

EXPOSURE = 1.3
AZ_GOLD = -115
BOUNCES = 4
DUR = {}
VARIANT_FOR = {"route": "golden", "meet": "bluehour", "search": "night", "back": "grey"}
EXT = (-470.0, 470.0, -330.0, 260.0)
CLEARING = Vector((-34.0, -118.0, 0.0))
EAST = Vector((370.0, -10.0, 0.0)); WEST = Vector((-380.0, 8.0, 0.0))


def shore_y(x):
    return 42.0 + 16.0 * math.sin(x / 150.0 + 0.4) + 7.0 * math.sin(x / 47.0) + 4.0 * math.sin(x / 19.0 + 1.0)


def _path_ctrl():
    pts = []
    for x in np.linspace(EAST.x, 30.0, 14):
        pts.append(Vector((x, shore_y(x) - 26.0 - 6.0 * math.sin(x / 60.0) + (0 if x < 340 else -(x - 340) * 0.9), 0)))
    pts += [Vector((14, 4, 0)), Vector((5, 1.5, 0)), Vector((0, 0, 0)), Vector((-3, -4, 0)), Vector((-9, -7, 0)), Vector((-20, -5, 0))]
    for x in np.linspace(-34.0, WEST.x, 14):
        pts.append(Vector((x, shore_y(x) - 27.0 + 5.0 * math.sin(x / 45.0) + (0 if x > -350 else (x + 350) * 0.6), 0)))
    out = [pts[0]]
    for a, b in zip(pts, pts[1:]):                         # resample ~2 m with light smoothing
        n = max(1, int((b - a).length / 2.0))
        for k in range(1, n + 1):
            out.append(a.lerp(b, k / n))
    for _ in range(3):
        out = [out[0]] + [(out[i - 1] + out[i] * 2 + out[i + 1]) / 4 for i in range(1, len(out) - 1)] + [out[-1]]
    return out


PATH = _path_ctrl()


def path_dist(x, y):
    P = np.array([(p.x, p.y) for p in PATH[::2]])
    return float(np.min(np.hypot(P[:, 0] - x, P[:, 1] - y)))


def forest_mask(x, y, clearing=True):
    """1 inside the wood: between the villages, from the shore margin to ~250 m inland, ragged edges, a clearing."""
    edge = 0.0
    edge += 28 * math.sin(x / 37.0) + 18 * math.sin(y / 23.0 + x / 61.0)
    inside = (-265 - edge * 0.6 < x < 255 + edge * 0.5) and (-260 + edge < y < shore_y(x) - 9)
    if not inside:
        return 0.0
    if clearing and (Vector((x, y, 0)) - CLEARING).length < 11.0:
        return 0.0
    return 1.0


# ---------------------------------------------------------------------------------------------- ground
def height(x, y):
    sh = shore_y(x)
    if y > sh:
        return -0.4 - min(3.0, (y - sh) * 0.08)
    inland = sh - y
    h = 0.4 + min(1.0, inland / 30.0) * (2.0 + 6.0 * (0.5 + 0.5 * math.sin(x / 90.0 + y / 70.0)) * min(1.0, inland / 160.0))
    return h


def terrain(c):
    x0, x1, y0, y1 = EXT
    nx, ny = 236, 148
    xs = np.linspace(x0, x1, nx); ys = np.linspace(y0, y1, ny)
    verts, fm = [], []
    for y in ys:
        for x in xs:
            h = height(x, y)
            if path_dist(x, y) < 3.0 and y < shore_y(x):
                h -= 0.15
            verts.append((x, y, h)); fm.append(forest_mask(x, y, clearing=False))
    faces = [(j * nx + i, j * nx + i + 1, (j + 1) * nx + i + 1, (j + 1) * nx + i) for j in range(ny - 1) for i in range(nx - 1)]
    me = bpy.data.meshes.new("AerialGround"); me.from_pydata(verts, [], faces); me.update()
    me.polygons.foreach_set("use_smooth", [True] * len(me.polygons))
    at = me.attributes.new("forest", 'FLOAT', 'POINT'); at.data.foreach_set("value", fm)
    o = bpy.data.objects.new("AerialGround", me); bpy.context.collection.objects.link(o)
    o.data.materials.append(ground_mat())
    c["H"] = (xs, ys, np.array([v[2] for v in verts]).reshape(ny, nx))
    return o


def gz(c, x, y):
    xs, ys, H = c["H"]
    i = int(np.clip(np.searchsorted(xs, x) - 1, 0, len(xs) - 2)); j = int(np.clip(np.searchsorted(ys, y) - 1, 0, len(ys) - 2))
    fx = (x - xs[i]) / (xs[i + 1] - xs[i]); fy = (y - ys[j]) / (ys[j + 1] - ys[j])
    return float((H[j, i] * (1 - fx) + H[j, i + 1] * fx) * (1 - fy) + (H[j + 1, i] * (1 - fx) + H[j + 1, i + 1] * fx) * fy)


def ground_mat():
    """Fields as a patchwork (meadow, stubble, ploughed earth) with grass texture; dark needle floor under the wood."""
    m = bpy.data.materials.new("AerialGround"); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; p = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord")
    vor = N.new("ShaderNodeTexVoronoi"); vor.inputs['Scale'].default_value = 0.012; vor.inputs['Randomness'].default_value = 0.9
    L.new(tc.outputs['Object'], vor.inputs['Vector'])
    sep = N.new("ShaderNodeSeparateColor"); L.new(vor.outputs['Color'], sep.inputs[0])
    ramp = N.new("ShaderNodeValToRGB"); ramp.color_ramp.interpolation = 'CONSTANT'; L.new(sep.outputs[0], ramp.inputs['Fac'])
    els = ramp.color_ramp.elements
    els[0].position = 0.0; els[0].color = (0.085, 0.12, 0.04, 1)       # meadow
    els[1].position = 0.55; els[1].color = (0.23, 0.19, 0.09, 1)       # stubble
    e = els.new(0.35); e.color = (0.12, 0.15, 0.05, 1)                  # second meadow
    e = els.new(0.80); e.color = (0.075, 0.06, 0.045, 1)                # ploughed
    # crop rows / mowing stripes inside each field
    wv = N.new("ShaderNodeTexWave"); wv.inputs['Scale'].default_value = 0.6; wv.inputs['Distortion'].default_value = 0.4
    L.new(tc.outputs['Object'], wv.inputs['Vector'])
    stripes = N.new("ShaderNodeMixRGB"); stripes.blend_type = 'MULTIPLY'; stripes.inputs['Fac'].default_value = 0.12
    L.new(ramp.outputs['Color'], stripes.inputs[1]); L.new(wv.outputs['Color'], stripes.inputs[2])
    nz = N.new("ShaderNodeTexNoise"); nz.inputs['Scale'].default_value = 0.4; nz.inputs['Detail'].default_value = 10
    L.new(tc.outputs['Object'], nz.inputs['Vector'])
    var = N.new("ShaderNodeMixRGB"); var.blend_type = 'OVERLAY'; var.inputs['Fac'].default_value = 0.35
    L.new(stripes.outputs[0], var.inputs[1]); L.new(nz.outputs['Color'], var.inputs[2])
    # the wood's floor
    at = N.new("ShaderNodeAttribute"); at.attribute_name = "forest"
    floor = N.new("ShaderNodeMixRGB"); L.new(at.outputs['Fac'], floor.inputs['Fac'])
    L.new(var.outputs[0], floor.inputs[1]); floor.inputs[2].default_value = (0.03, 0.03, 0.018, 1)
    # the reedy shore margin and wet sand darker near the water (by height)
    sep2 = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs['Object'], sep2.inputs[0])
    wet = N.new("ShaderNodeMapRange"); wet.inputs['From Min'].default_value = -0.2; wet.inputs['From Max'].default_value = 0.6
    wet.inputs['To Min'].default_value = 1.0; wet.inputs['To Max'].default_value = 0.0; L.new(sep2.outputs['Z'], wet.inputs['Value'])
    shore = N.new("ShaderNodeMixRGB"); L.new(wet.outputs[0], shore.inputs['Fac'])
    L.new(floor.outputs[0], shore.inputs[1]); shore.inputs[2].default_value = (0.05, 0.055, 0.03, 1)
    L.new(shore.outputs[0], p.inputs['Base Color'])
    p.inputs['Roughness'].default_value = 0.92
    bp = N.new("ShaderNodeBump"); bp.inputs['Strength'].default_value = 0.4; L.new(nz.outputs['Fac'], bp.inputs['Height'])
    L.new(bp.outputs['Normal'], p.inputs['Normal'])
    return m


def strip(name, pts, width, m, zoff=0.05, c=None):
    """A ribbon draped on the ground along pts."""
    verts, faces = [], []
    for k, p in enumerate(pts):
        d = (pts[min(k + 1, len(pts) - 1)] - pts[max(k - 1, 0)]); d.z = 0; d.normalize()
        n = Vector((-d.y, d.x, 0)) * width / 2
        for q in (p - n, p + n):
            verts.append((q.x, q.y, (gz(c, q.x, q.y) if c else 0) + zoff))
    for k in range(len(pts) - 1):
        faces.append((2 * k, 2 * k + 2, 2 * k + 3, 2 * k + 1))
    me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces); me.update()
    o = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(o); o.data.materials.append(m)
    return o


# ---------------------------------------------------------------------------------------------- the world
def kind_hint(x, y):
    return False


def trees(c, autumn=False):
    rr = np.random.default_rng(5)
    place = {"fir_a": [], "fir_b": [], "birch": []}
    x0, x1, y0, y1 = -300, 290, -300, 70
    step = 5.2
    for y in np.arange(y0, y1, step):
        for x in np.arange(x0, x1, step):
            px, py = x + rr.uniform(-2.2, 2.2), y + rr.uniform(-2.2, 2.2)
            if forest_mask(px, py) < 0.5 or path_dist(px, py) < 7.0:
                continue
            gap = math.sin(px / 23.0 + 1.3) * math.sin(py / 17.0) + 0.6 * math.sin(px / 9.0 - py / 13.0)
            if gap > 0.95:                                   # glades and thinner patches, so the wood is not one carpet
                continue
            birchy = 0.55 if (py > -70 or math.sin(px / 40.0) > 0.3) else 0.25
            kind = "birch" if rr.uniform() < birchy else ("fir_a" if rr.uniform() < 0.55 else "fir_b")
            s = rr.uniform(0.8, 1.3) * (3.0 if kind == "birch" else 1.0)
            place[kind].append((Vector((px, py, gz(c, px, py) - 0.2)), rr.uniform(0, 6.28), s))
    # hedgerows and single trees in the fields; garden trees in the villages
    for _ in range(260):
        px, py = rr.uniform(-460, 460), rr.uniform(-320, 30)
        if forest_mask(px, py) > 0.5 or py > shore_y(px) - 6:
            continue
        kind = "birch" if rr.uniform() < 0.6 else "fir_a"
        place[kind].append((Vector((px, py, gz(c, px, py) - 0.2)), rr.uniform(0, 6.28), rr.uniform(0.9, 1.3) * (2.4 if kind == "birch" else 1.0)))
    for kind, pl in place.items():
        rj.low_instances(kind, pl)
    if autumn:
        import sc_woods
        sc_woods.autumn_canopy() if hasattr(sc_woods, "autumn_canopy") else _autumn_birch()


def _autumn_birch():
    import sc_woods
    t = bpy.data.objects.get("TPL_birch")
    if t:
        for sl in t.material_slots:
            m = sl.material
            if m and m.get("birch") and not m.get("autumn"):
                sc_woods._yellow(m, (0.8, 0.58, 0.08), (0.5, 0.52, 0.12), 1.0); m["autumn"] = 1


def aerial_house(name, loc, rz, w, d, lit, mats, rr):
    """A Bavarian house for distances of 50-300 m: plastered body, timber-clad upper storey band, a wide gable roof with
    overhang, a balcony line on the gable side and window rows (lit warm at night). Built as one mesh, no bpy.ops."""
    import bmesh
    from mathutils import Matrix
    bm = bmesh.new()
    def cube(cx, cy, cz, sx, sy, sz, mi):
        r = bmesh.ops.create_cube(bm, size=1.0, matrix=Matrix.Translation((cx, cy, cz)) @ Matrix.Diagonal((sx, sy, sz, 1)))
        for f in {f for v in r["verts"] for f in v.link_faces}:
            f.material_index = mi
    H = 5.8
    cube(0, 0, H / 2, w, d, H, 0)                       # body
    cube(0, 0, H - 0.7, w + 0.04, d + 0.04, 1.4, 1)     # timber band
    cube(0, -d / 2 - 0.6, 3.1, w * 0.9, 1.2, 0.15, 1)   # balcony slab
    cube(0, -d / 2 - 1.15, 3.6, w * 0.9, 0.08, 0.9, 1)  # balcony rail
    for row_z in (1.4, 4.2):                            # window rows on the long sides
        for k in range(int(w // 2.4)):
            x = -w / 2 + 1.4 + k * 2.4
            for sy in (-1, 1):
                cube(x, sy * (d / 2 + 0.01), row_z, 1.0, 0.04, 1.2, 3)
    # gable roof: ridge along x, overhang 1.2 m, pitch 24 deg
    ov = 1.2; rise = (d / 2 + ov) * math.tan(math.radians(24))
    v = [bm.verts.new(p) for p in ((-w / 2 - ov, -d / 2 - ov, H - 0.15), (w / 2 + ov, -d / 2 - ov, H - 0.15), (w / 2 + ov, 0, H + rise),
                                   (-w / 2 - ov, 0, H + rise), (-w / 2 - ov, d / 2 + ov, H - 0.15), (w / 2 + ov, d / 2 + ov, H - 0.15))]
    for f in (bm.faces.new((v[0], v[1], v[2], v[3])), bm.faces.new((v[3], v[2], v[5], v[4]))):
        f.material_index = 2
    bmesh.ops.solidify(bm, geom=[f for f in bm.faces if f.material_index == 2], thickness=0.25) if hasattr(bmesh.ops, "solidify") else None
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for m in mats:
        me.materials.append(m)
    me.materials.append(mats[4] if lit else mats[3])
    for p in me.polygons:
        if p.material_index == 3:
            p.material_index = 4 if lit and rr.random() < 0.55 else 3
    o = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(o)
    o.location = loc; o.rotation_euler.z = rz
    return o


def villages(c, lit=0.0):
    rr = np.random.default_rng(9)
    mats = [pbr("AHPlaster", (0.62, 0.58, 0.50), 0.85), pbr("AHTimber", (0.16, 0.09, 0.05), 0.8),
            pbr("AHRoof", (0.20, 0.09, 0.06), 0.75), pbr("AHWin", (0.03, 0.035, 0.04), 0.15),
            pbr("AHWinLit", (0.0, 0.0, 0.0), 0.3, 0.0, **{"Emission Color": (1.0, 0.70, 0.38, 1), "Emission Strength": max(lit, 0.1)})]
    import random
    rnd = random.Random(4)
    for k, ctr in enumerate((EAST, WEST)):
        for i in range(30):
            a = rr.uniform(0, 2 * math.pi); r = rr.uniform(14, 100)
            x, y = ctr.x + r * math.cos(a) * 1.2, ctr.y - 30 + r * math.sin(a) * 0.9
            if y > shore_y(x) - 14:
                continue
            aerial_house(f"AHouse{k}_{i}", (x, y, gz(c, x, y) - 0.3), rr.uniform(-0.3, 0.3) + (math.pi / 2 if rr.uniform() < 0.3 else 0),
                         rr.uniform(9, 14), rr.uniform(8, 10.5), lit > 0, mats, rnd)
    # village streets
    asph = pbr("Asphalt", (0.06, 0.06, 0.065), 0.8)
    for ctr in (EAST, WEST):
        strip("Street", [ctr + Vector((0, 8, 0)), ctr + Vector((0, -120, 0))], 6.0, asph, 0.06, c)
    road = [Vector((x, -205 + 22 * math.sin(x / 130.0), 0)) for x in np.linspace(-470, 470, 120)]
    strip("Road", road, 7.0, asph, 0.06, c)


def lake(c, kind):
    import sc_path as SP
    w = box("AerialLake", (0, 600, -0.35), (2400, 1200, 0.02), SP.water_material())
    reed = SP.reed_material()
    rp = [Vector((x, shore_y(x) + 1.5, 0)) for x in np.linspace(-470, 470, 400)]
    o = strip("ReedBelt", rp, 7.0, pbr("ReedBelt", (0.11, 0.10, 0.045), 0.8), 0.25, None)
    for v in o.data.vertices:
        v.co.z = -0.1 + 0.6 * (0.5 + 0.5 * math.sin(v.co.x * 0.7))
    # far shore in haze
    hill = pbr("AFarHills", (0.05, 0.065, 0.055), 0.9)
    for k in range(10):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=12, radius=1, location=(-1300 + k * 290, 2300 + 100 * math.sin(k), -40))
        h = bpy.context.active_object; h.scale = (260, 140, 120 + 40 * math.sin(k * 1.7)); h.data.materials.append(hill)


def light(c, kind):
    if kind == "golden":
        w, s_ = rj.sky("lowsun", rot=-10)
        if s_ is not None:                              # from the air: a little higher so the wood is not one shadow
            bpy.data.objects.remove(s_)
        from common import sun
        sun(16, AZ_GOLD, 7.0, (1.0, 0.68, 0.40), 1.0)
    elif kind == "bluehour":
        rj.sky("bluehour")
    elif kind == "night":
        rj.sky("night")
        mo = bpy.data.lights.new("Moon", 'SUN'); mo.energy = 0.06; mo.color = (0.55, 0.65, 1.0); mo.angle = math.radians(1)
        o = bpy.data.objects.new("Moon", mo); bpy.context.collection.objects.link(o); o.rotation_euler = (math.radians(50), 0, math.radians(200))
    else:
        rj.sky("mist", rot=0)
    # low ground mist over the wood and the shore (thicker in grey/blue hour)
    dens = {"golden": 0.00025, "bluehour": 0.0012, "night": 0.0030, "grey": 0.0015}[kind]
    col = {"golden": (1.0, 0.86, 0.7), "bluehour": (0.7, 0.78, 0.95), "night": (0.6, 0.68, 0.9), "grey": (0.82, 0.84, 0.86)}[kind]
    haze((0, -60, 9), (620, 420, 18), density=dens, color=col, anis=0.5)


def build(variant=None):
    kind = variant or "golden"
    c = dict(variant=kind)
    terrain(c)
    path = strip("AerialPath", PATH, 2.0, mat("gravel"), 0.08, c)
    villages(c, lit=(6.0 if kind == "night" else (2.0 if kind == "bluehour" else 0.0)))
    lake(c, kind)
    light(c, kind)
    rj.sink_haze(depth=1.0)
    # the bare earth of the clearing, then the five little spruces on it
    soil = pbr("ClearSoil", (0.11, 0.08, 0.05), 0.95)
    N = soil.node_tree.nodes; L = soil.node_tree.links
    tc = N.new("ShaderNodeTexCoord"); nz = N.new("ShaderNodeTexNoise"); nz.inputs['Scale'].default_value = 1.6; nz.inputs['Detail'].default_value = 12
    L.new(tc.outputs['Object'], nz.inputs['Vector']); rp = N.new("ShaderNodeValToRGB"); L.new(nz.outputs['Fac'], rp.inputs['Fac'])
    rp.color_ramp.elements[0].position = 0.4; rp.color_ramp.elements[0].color = (0.05, 0.035, 0.022, 1)
    rp.color_ramp.elements[1].position = 0.7; rp.color_ramp.elements[1].color = (0.20, 0.13, 0.06, 1)
    L.new(rp.outputs['Color'], N["Principled BSDF"].inputs['Base Color'])
    bp = N.new("ShaderNodeBump"); bp.inputs['Strength'].default_value = 0.8; L.new(nz.outputs['Fac'], bp.inputs['Height'])
    L.new(bp.outputs['Normal'], N["Principled BSDF"].inputs['Normal'])
    bpy.ops.mesh.primitive_circle_add(vertices=40, radius=9.5, fill_type='NGON', location=(CLEARING.x, CLEARING.y, gz(c, CLEARING.x, CLEARING.y) + 0.05))
    so = bpy.context.object; so.name = "ClearingSoil"; so.data.materials.append(soil)
    for k, v in enumerate(so.data.vertices):
        v.co.x *= 1 + 0.12 * math.sin(k * 1.7); v.co.y *= 1 + 0.12 * math.cos(k * 2.3)
    # five little spruces on the bare clearing (seen from above as a lighter gap with a few dark points)
    rj.low_instances("fir_a", [(CLEARING + Vector((dx, dy, gz(c, CLEARING.x + dx, CLEARING.y + dy) - 0.05)), 0.3 * i, 0.12)
                               for i, (dx, dy) in enumerate(((0, 0), (1.2, 0.6), (-1.0, 0.8), (0.4, -1.1), (-0.8, -0.9)))])
    # the red bicycle and its rider (route only: seen from high behind, small)
    if kind == "golden":
        c["bike"] = rj.bicycle("Bike")
        c["sister"] = rj.person("sister", name="Sister")
    # the father and the uncle, each carrying a torch (meet: they are seen, small, from above)
    if kind == "bluehour":
        c["men"] = []
        for role in ("father", "uncle"):
            h = rj.person(role, name=role.capitalize())
            tr = rj.torch(role + "Torch", on=True, energy=260.0, cone=30.0)
            c["men"].append((h, tr))
    # torches and the police light
    c["torches"] = []
    if kind in ("bluehour", "night"):
        rr = np.random.default_rng(2)
        n = 0 if kind == "bluehour" else 34
        bead = K.pbr("TorchBead", (0, 0, 0), 0.5, **{"Emission Color": (1.0, 0.75, 0.42, 1), "Emission Strength": 60.0})
        for i in range(n):
            l = bpy.data.lights.new(f"ATorch{i}", 'SPOT'); l.energy = 140.0; l.color = (1.0, 0.82, 0.58); l.shadow_soft_size = 0.05
            l.spot_size = math.radians(38); l.spot_blend = 0.5
            o = bpy.data.objects.new(f"ATorch{i}", l); bpy.context.collection.objects.link(o)
            bpy.ops.mesh.primitive_uv_sphere_add(radius=0.22, segments=10, ring_count=6); b_ = bpy.context.object
            b_.name = f"ATorchBead{i}"; b_.data.materials.append(bead); b_.parent = o
            o["seed"] = float(rr.uniform(0, 1))
            c["torches"].append(o)
        if kind == "night":
            l = bpy.data.lights.new("PoliceBlue", 'POINT'); l.energy = 400.0; l.color = (0.25, 0.45, 1.0)
            o = bpy.data.objects.new("PoliceBlue", l); bpy.context.collection.objects.link(o)
            q = PATH[len(PATH) // 5]; o.location = (q.x, q.y, gz(c, q.x, q.y) + 1.6)
            rj.driven(l, "energy", "400 * (0.5 + 0.5 * sin(frame * 0.9)) ** 4")
    bpy.context.scene.view_settings.exposure += {"golden": 0.0, "bluehour": 1.3, "night": 0.7, "grey": 0.3}[kind]
    trees(c, autumn=(kind == "grey"))            # last: thousands of objects make every later bpy.ops slow
    rj.finish_scene()
    return c


# ---------------------------------------------------------------------------------------------- shots
def _cum(pts):
    L = [0.0]
    for a, b in zip(pts, pts[1:]):
        L.append(L[-1] + (b - a).length)
    return L


_PL = _cum(PATH)
I_BEND = min(range(len(PATH)), key=lambda i: PATH[i].length)


def at_dist(s):
    s = max(0.0, min(_PL[-1], s))
    for k in range(len(PATH) - 1):
        if _PL[k + 1] >= s:
            w = (s - _PL[k]) / max(_PL[k + 1] - _PL[k], 1e-9)
            return PATH[k].lerp(PATH[k + 1], w)
    return PATH[-1]


def sm(t, a, b):
    return ease(max(0.0, min(1.0, (t - a) / max(b - a, 1e-6))))


def walk_along(c, h, s, sg, walked):
    """Walk along the curved path: at distance s, heading +/-; the stride phase follows the distance walked."""
    from rjp import upright, pose_walk
    from human import SIDE
    p = at_dist(s); d = at_dist(s + sg * 1.0) - at_dist(s - sg * 1.0); d.z = 0; d.normalize()
    moving = True
    upright(h)
    pose_walk(h, walked / 1.35, stride=26, arm_swing=20)
    for sd, sg_ in SIDE.items():
        h.rot(f"upperarm01.{sd}", (0, 1, 0), sg_ * 12)
        h.rot(f"lowerarm01.{sd}", (1, 0, 0), 35)
    h.arm.rotation_euler = (0, 0, math.atan2(d.x, -d.y))
    h.arm.location = (p.x, p.y, gz(c, p.x, p.y) + 0.06)
    bpy.context.view_layer.update()


def _torch_on(c, o, p, on=True, d=None):
    o.location = (p.x, p.y, gz(c, p.x, p.y) + 1.3) if on else (0, 0, -200)
    if d is not None:                                  # beam ahead and down onto the ground
        aim = Vector((d.x, d.y, 0)).normalized() * 3.0 + Vector((0, 0, -1.3))
        o.rotation_euler = aim.to_track_quat('-Z', 'Y').to_euler()


def anim(c, t, shot):
    for o in c["torches"]:
        o.location = (0, 0, -200)
    if shot == "route":
        ride(c, S_RIDE0 + RIDE_SPEED * t * DUR["route"])
    if shot == "meet":
        sb = _PL[I_BEND]; k = sm(t, 0.0, 0.85)
        for (h, tr), s0, sg in ((c["men"][0], sb - 38 + 36.6 * k, 1), (c["men"][1], sb + 38 - 36.6 * k, -1)):
            walk_along(c, h, s0, sg, 38 * k)
            import sc_path as SP
            fwd = rj.rjp.forward(h)
            SP.hold_torch(h, tr, SP._sweep_dir(fwd, t * DUR["meet"] + sg, 0.35, 0.4, 0.45))
    if shot == "search":
        sb = _PL[I_BEND]
        for i, o in enumerate(c["torches"]):
            t0 = 0.03 + 0.5 * o["seed"]
            if t < t0:
                continue
            k = (t - t0)
            start = at_dist(sb + (o["seed"] - 0.5) * 160)
            if i % 3 == 0:                                 # a third stay on the path, walking it
                sg = 1 if i % 2 else -1; s0 = sb + (o["seed"] - 0.5) * 160 + (k * 14.0) * sg
                p = at_dist(s0); dirn = at_dist(s0 + sg) - at_dist(s0 - sg)
            else:                                          # the rest leave it and fan out into the wood
                dirn = Vector((math.sin(i * 2.4) * 0.6, -1.0, 0)).normalized()
                p = start + dirn * (k * 22.0)
            sweep = Matrix.Rotation(0.5 * math.sin(t * 9.0 + i), 3, 'Z') @ Vector((dirn.x, dirn.y, 0))
            _torch_on(c, o, p, d=sweep)


S_RIDE0 = 260.0          # metres along the path from the east end where the shot starts
RIDE_SPEED = 4.2


def ride(c, s):
    bk = c["bike"]
    p = at_dist(s); p2 = at_dist(s + 1.5); p0 = at_dist(s - 1.5)
    dv = p2 - p0; hd = math.atan2(dv.y, dv.x)
    bk["root"].location = (p.x, p.y, gz(c, p.x, p.y) - 0.1); bk["root"].rotation_euler = (0, 0, hd)
    rj.roll_bike(bk, s)
    bpy.context.view_layer.update()
    rj.ride_pose(c["sister"], bk, s)


def cam_route(c, t):
    e = ease(t)
    """A drone straight above, following the red bicycle along the path through the wood (seen only from above, far)."""
    s = S_RIDE0 + RIDE_SPEED * t * DUR["route"]
    bike = at_dist(s); ahead = at_dist(s + 25.0); back = at_dist(s - 25.0)
    d = (ahead - back); d.z = 0; d.normalize()
    g = gz(c, bike.x, bike.y)
    tgt = bike + d * 4.0 + Vector((0, 0, g))
    loc = tgt + Vector((0, 0, 19.0 + 4.0 * ease(t)))
    return (loc, tgt, 35, (d.x, d.y, 0))


def cam_meet(c, t):
    """Straight down over the bend, turning slowly and sinking: a drone looking down on the path in the dark wood."""
    e = ease(t)
    tgt = Vector((0, -2, 0))
    a = math.radians(20 - 25 * e)
    loc = tgt + Vector((0, 0, 95 - 30 * e))
    return (loc, tgt, 35, (math.sin(a), math.cos(a), 0))


def cam_search(c, t):
    e = ease(t)
    tgt = Vector((0, -25, 0))
    a = math.radians(-15 + 25 * e)
    loc = tgt + Vector((0, 0, 150 - 25 * e))
    return (loc, tgt, 30, (math.sin(a), math.cos(a), 0))


def cam_back(c, t):
    """Straight down on the small clearing, rising and drifting north until the path along the shore comes in."""
    e = ease(t)
    tgt = CLEARING.lerp(Vector((0, 25, 0)), 0.8 * e)
    loc = tgt + Vector((0, 0, 38 + 112 * e))
    return (loc, tgt, 35, (0, 1, 0))


def _mk(shot, dur, cam):
    DUR[shot] = dur
    return dict(kind="anim", cam=cam, anim=lambda c, t: anim(c, t, shot))


MOVES = {
    "route": _mk("route", 7.0, cam_route),
    "meet": _mk("meet", 6.0, cam_meet),
    "search": _mk("search", 6.0, cam_search),
    "back": _mk("back", 6.5, cam_back),
}
