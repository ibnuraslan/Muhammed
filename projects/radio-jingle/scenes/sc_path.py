"""PATH: the lakeside path between Eching and Schondorf on the Ammersee (built once, reused in every chapter).

Geometry (metres): the gravel path runs from Eching (west, -X) toward Schondorf (east, +X) along the shore. At the
BEND (origin) it turns sharply inland around a wooded spur. The lake lies to the north (+Y): reeds between the
path and the water. Birch and spruce woods with ferns to the south (-Y), denser past the bend.
  path(s): centreline polyline PTS ; path_point(d) -> (position, heading) at distance d from the west end
  BRUSH: where the bicycle lies, about 20 m off the path into the woods past the bend.

Light variants: "lowsun" (late-summer evening), "dusk", "bluehour", "night" (moon + torches), "mist" (morning),
"grey" (overcast day). Append "|role,role" to cast people (sister, father, uncle, brother, officer, officer2,
firefighter, diver, ...).
"""
import math
import numpy as np
import bpy
from mathutils import Vector, Matrix
from kit import pbr, box, cyl, join, area_light, point_at, haze, emissive
from common import ease
import ph
import rj
from rj import mat, person, stand, walk, forward, upright, reach, fingers_curl, SIDE

EXPOSURE = 0.0
BOUNCES = 5
PTS = [Vector(p) for p in ((-90, 6.0), (-55, 4.5), (-30, 3.0), (-12, 1.6), (-3, 0.6), (0, 0), (2.2, -2.2), (5, -7), (10, -11), (25, -15), (60, -18))]
PATH_W = 2.2
BRUSH = Vector((-10.0, -17.0, 0.0))          # the red bicycle in the brush, ~19 m into the woods south of the path
LAKE_Y = 9.0                                 # water line north of the bend (shore follows the path ~8 m out)
DUR = {}
rng = np.random.default_rng(11)
GAP = (-13.6, -11.6)                         # x range of the gap in the reeds (a bathing / landing spot)


def _cum():
    d = [0.0]
    for a, b in zip(PTS[:-1], PTS[1:]):
        d.append(d[-1] + (b - a).length)
    return d


CUM = _cum()
D_BEND = CUM[5]


def path_point(dist, offset=0.0):
    """Point on the path `dist` metres from the west end (offset: + to the left of the walking direction)."""
    dist = max(0.0, min(dist, CUM[-1] - 1e-3))
    for k in range(len(PTS) - 1):
        if CUM[k + 1] >= dist:
            a, b = PTS[k], PTS[k + 1]; t = (dist - CUM[k]) / (CUM[k + 1] - CUM[k])
            p = a.lerp(b, t); d = (b - a).normalized()
            # smooth the heading across the vertex (blend with the next/previous segment near the joints)
            hd = math.atan2(d.y, d.x)
            left = Vector((-d.y, d.x))
            q = p + left * offset
            return Vector((q.x, q.y, 0.0)), hd
    return Vector((PTS[-1].x, PTS[-1].y, 0)), 0.0


def _dist_to_path(x, y):
    best = 1e9
    p = Vector((x, y))
    for a, b in zip(PTS[:-1], PTS[1:]):
        ab = b - a; t = max(0.0, min(1.0, (p - a).dot(ab) / ab.length_squared))
        best = min(best, (p - (a + ab * t)).length)
    return best


def _shore_y(x):
    """Water line (y) as a function of x: about 8 m north of the path, bulging around the bend."""
    py = np.interp(x, [p.x for p in PTS], [p.y for p in PTS])
    return py + 7.5 + 2.0 * math.sin(x * 0.07) + (3.0 if x > 3 else 0.0) * min(1.0, (x - 3) / 8) if x > 3 else py + 7.5 + 2.0 * math.sin(x * 0.07)


def lake_side(x, y):
    return y > np.interp(x, [p.x for p in PTS], [p.y for p in PTS]) + 1.8


# ============================================================================ materials
def water_material():
    m = bpy.data.materials.new("Lake"); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; p = N["Principled BSDF"]
    p.inputs['Base Color'].default_value = (0.012, 0.02, 0.022, 1); p.inputs['Roughness'].default_value = 0.04
    p.inputs['Specular IOR Level'].default_value = 0.6; p.inputs['IOR'].default_value = 1.33
    tc = N.new("ShaderNodeTexCoord"); mp = N.new("ShaderNodeMapping"); L.new(tc.outputs['Object'], mp.inputs['Vector'])
    rj.driven(mp.inputs['Location'], "default_value", "frame * 0.004", 0)
    rj.driven(mp.inputs['Location'], "default_value", "frame * 0.0025", 1)
    n1 = N.new("ShaderNodeTexNoise"); n1.inputs['Scale'].default_value = 1.8; n1.inputs['Detail'].default_value = 6; n1.inputs['Roughness'].default_value = 0.55
    L.new(mp.outputs[0], n1.inputs['Vector'])
    mp2 = N.new("ShaderNodeMapping"); mp2.inputs['Scale'].default_value = (1.0, 3.5, 1.0); L.new(mp.outputs[0], mp2.inputs['Vector'])
    n2 = N.new("ShaderNodeTexWave"); n2.inputs['Scale'].default_value = 0.9; n2.inputs['Distortion'].default_value = 6; n2.inputs['Detail'].default_value = 3
    L.new(mp2.outputs[0], n2.inputs['Vector'])
    mx = N.new("ShaderNodeMath"); mx.operation = 'MULTIPLY_ADD'; mx.inputs[1].default_value = 0.5
    L.new(n1.outputs['Fac'], mx.inputs[0]); L.new(n2.outputs['Fac'], mx.inputs[2])
    b = N.new("ShaderNodeBump"); b.inputs['Strength'].default_value = 0.12; b.inputs['Distance'].default_value = 0.02
    L.new(mx.outputs[0], b.inputs['Height']); L.new(b.outputs['Normal'], p.inputs['Normal'])
    return m


def reed_material():
    m = bpy.data.materials.new("Reed"); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; p = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord"); sep = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs['Object'], sep.inputs[0])
    oi = N.new("ShaderNodeObjectInfo")
    mr = N.new("ShaderNodeMapRange"); mr.inputs['From Min'].default_value = 0.0; mr.inputs['From Max'].default_value = 2.2
    L.new(sep.outputs['Z'], mr.inputs['Value'])
    ramp = N.new("ShaderNodeValToRGB"); L.new(mr.outputs[0], ramp.inputs['Fac'])
    ramp.color_ramp.elements[0].color = (0.05, 0.07, 0.025, 1); ramp.color_ramp.elements[1].color = (0.36, 0.30, 0.15, 1)
    e = ramp.color_ramp.elements.new(0.55); e.color = (0.16, 0.17, 0.06, 1)
    hs = N.new("ShaderNodeHueSaturation"); L.new(ramp.outputs['Color'], hs.inputs['Color'])
    vv = N.new("ShaderNodeMath"); vv.operation = 'MULTIPLY_ADD'; vv.inputs[1].default_value = 0.5; vv.inputs[2].default_value = 0.75
    L.new(oi.outputs['Random'], vv.inputs[0]); L.new(vv.outputs[0], hs.inputs['Value'])
    L.new(hs.outputs['Color'], p.inputs['Base Color']); p.inputs['Roughness'].default_value = 0.55
    p.inputs['Subsurface Weight'].default_value = 0.0
    p.inputs['Transmission Weight'].default_value = 0.0
    p.inputs['Sheen Weight'].default_value = 0.3
    return m


# ============================================================================ geometry
def ribbon(name, pts, width, z, m, step=0.6, edge_noise=0.12):
    """A flat strip along the polyline (path surface), slightly cambered."""
    import bmesh
    me = bpy.data.meshes.new(name); bm = bmesh.new(); uv = bm.loops.layers.uv.new()
    total = CUM[-1]; n = int(total / step)
    rows = []
    for k in range(n + 1):
        d = k * step
        p, hd = path_point(d)
        # average heading across joints for a smooth bend
        p2, h2 = path_point(d + 1.5); p0, h0 = path_point(d - 1.5)
        dv = (p2 - p0); dv.z = 0; dv.normalize()
        left = Vector((-dv.y, dv.x, 0))
        row = []
        for s in (-1.0, -0.5, 0.0, 0.5, 1.0):
            wn = width / 2 * (1 + edge_noise * math.sin(d * 1.7 + s * 3) * abs(s))
            q = p + left * s * wn
            row.append(bm.verts.new((q.x, q.y, z + 0.03 * (1 - s * s))))
        rows.append(row)
    for a, b in zip(rows[:-1], rows[1:]):
        for i in range(4):
            bm.faces.new((a[i], a[i + 1], b[i + 1], b[i]))
    bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(o); o.data.materials.append(m)
    return o


def terrain(c, extent=(-70, 70, -60, 40)):
    x0, x1, y0, y1 = extent
    nx, ny = 141, 101
    xs = np.linspace(x0, x1, nx); ys = np.linspace(y0, y1, ny)
    H = np.zeros((ny, nx))
    for j, y in enumerate(ys):
        for i, x in enumerate(xs):
            d = _dist_to_path(x, y)
            sh = _shore_y(x)
            h = 0.0
            if y > sh:                                     # under the lake: slope down
                h = -0.25 - min(2.5, (y - sh) * 0.35)
            elif y > sh - 4:                               # reedy margin, near the water level
                h = -0.18 + 0.12 * (sh - y) / 4
            else:
                h = 0.05 + 0.25 * math.sin(x * 0.11 + y * 0.07) * min(1.0, max(0.0, d - 3) / 6) + (0.6 if y < -25 else 0) * min(1, (-25 - y) / 15)
            if d < PATH_W * 0.7:
                h = min(h, 0.0) if y < sh - 4 else h
            H[j, i] = h
    me = bpy.data.meshes.new("Terrain")
    verts = [(xs[i], ys[j], H[j, i]) for j in range(ny) for i in range(nx)]
    faces = [(j * nx + i, j * nx + i + 1, (j + 1) * nx + i + 1, (j + 1) * nx + i) for j in range(ny - 1) for i in range(nx - 1)]
    me.from_pydata(verts, [], faces); me.update()
    me.polygons.foreach_set("use_smooth", [True] * len(me.polygons))
    o = bpy.data.objects.new("Terrain", me); bpy.context.collection.objects.link(o)
    o.data.materials.append(mat("forest"))
    c["terrain"] = o
    c["H"] = (xs, ys, H)


def ground_z(c, x, y):
    xs, ys, H = c["H"]
    i = np.clip(np.searchsorted(xs, x) - 1, 0, len(xs) - 2); j = np.clip(np.searchsorted(ys, y) - 1, 0, len(ys) - 2)
    tx = (x - xs[i]) / (xs[i + 1] - xs[i]); ty = (y - ys[j]) / (ys[j + 1] - ys[j])
    return float((H[j, i] * (1 - tx) + H[j, i + 1] * tx) * (1 - ty) + (H[j + 1, i] * (1 - tx) + H[j + 1, i + 1] * tx) * ty)


def reed_clump(name, n=46, h=(1.4, 2.3), seed=0):
    """One clump of common reed: thin bent leaf blades plus a few stems with feathery brown plumes."""
    r = np.random.default_rng(seed)
    import bmesh
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    for k in range(n):
        x0, y0 = r.normal(0, 0.18, 2); H_ = r.uniform(*h); lean = r.uniform(0.05, 0.35); az = r.uniform(0, 6.28)
        w = r.uniform(0.008, 0.018); segs = 6
        prev = None
        for s in range(segs + 1):
            t = s / segs
            cx = x0 + math.cos(az) * lean * t * t * H_ * 0.5; cy = y0 + math.sin(az) * lean * t * t * H_ * 0.5
            z = H_ * t * (1 - 0.15 * t * lean)
            ww = w * (1 - 0.85 * t)
            px, py = -math.sin(az) * ww, math.cos(az) * ww
            a = bm.verts.new((cx - px, cy - py, z)); b = bm.verts.new((cx + px, cy + py, z))
            if prev:
                bm.faces.new((prev[0], prev[1], b, a))
            prev = (a, b)
        if k % 6 == 0:                                   # a plume
            for q in range(10):
                t = 0.92 + 0.08 * q / 10
                cx = x0 + math.cos(az) * lean * 0.5 * H_ * t * t; cy = y0 + math.sin(az) * lean * 0.5 * H_ * t * t
                z = H_ * t + 0.03 * q
                ww = 0.03 * math.sin(math.pi * q / 10) + 0.008
                a = bm.verts.new((cx - ww, cy, z)); b = bm.verts.new((cx + ww, cy, z)); c_ = bm.verts.new((cx + ww * 0.6, cy + 0.01, z + 0.05)); d = bm.verts.new((cx - ww * 0.6, cy + 0.01, z + 0.05))
                bm.faces.new((a, b, c_, d))
    bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(o)
    o.data.materials.append(c_reed())
    return o


_REED = {}


def c_reed():
    if "m" not in _REED or _REED["m"].name not in bpy.data.materials:
        _REED["m"] = reed_material()
    return _REED["m"]


def place_linked(src, placements, name):
    out = []
    for (loc, rz, s) in placements:
        o = bpy.data.objects.new(name, src.data); bpy.context.collection.objects.link(o)
        o.location = loc; o.rotation_euler = (0, 0, rz); o.scale = (s, s, s)
        out.append(o)
    return out


def scatter(c, region, n, ok, seed):
    r = np.random.default_rng(seed); out = []
    x0, x1, y0, y1 = region
    tries = 0
    while len(out) < n and tries < n * 30:
        tries += 1
        x = r.uniform(x0, x1); y = r.uniform(y0, y1)
        if ok(x, y):
            out.append((x, y, r.uniform(0, 6.28), r.uniform(0.8, 1.25)))
    return out


def vegetation(c, density=1.0):
    D = _dist_to_path
    # --- reeds along the shore (lake side of the path), in a band between the water line and the path verge
    clumps = [reed_clump(f"ReedSrc{k}", seed=k) for k in range(4)]
    for cl in clumps:
        cl.hide_render = True; cl.location.z = -500
    pts = scatter(c, (-70, 60, -20, 30), int(1300 * density),
                  lambda x, y: lake_side(x, y) and D(x, y) > 1.9 and y < _shore_y(x) + 2.5 and y > _shore_y(x) - 6.5
                  and not (GAP[0] < x < GAP[1]), 3)                                  # a small landing gap in the reeds
    c["reeds"] = []
    for k, (x, y, rz, s) in enumerate(pts):
        o = bpy.data.objects.new("Reed", clumps[k % 4].data); bpy.context.collection.objects.link(o)
        o.location = (x, y, ground_z(c, x, y) - 0.05); o.rotation_euler = (0, 0, rz); o.scale = (s, s, s * rng.uniform(0.8, 1.15))
        c["reeds"].append(o)
    # --- woods: spruce/fir and birch on the inland side, some birches on the shore side near the bend
    wood_pts = scatter(c, (-70, 60, -45, 10), int(150 * density), lambda x, y: not lake_side(x, y) and D(x, y) > 3.2, 5)
    shore_birch = scatter(c, (-25, 25, -10, 12), int(16 * density), lambda x, y: lake_side(x, y) and D(x, y) > 2.6 and y < _shore_y(x) - 4.0, 9)
    firs = [(Vector((x, y, ground_z(c, x, y))), rz, s * 1.1) for (x, y, rz, s) in wood_pts[0::3]]
    pines = [(Vector((x, y, ground_z(c, x, y))), rz, s) for (x, y, rz, s) in wood_pts[1::3]]
    birches = [(Vector((x, y, ground_z(c, x, y))), rz, s * 2.6) for (x, y, rz, s) in wood_pts[2::3] + shore_birch]
    c["trees"] = []
    c["trees"] += rj.low_instances("fir_a", firs)
    c["trees"] += rj.low_instances("fir_b", pines)
    c["trees"] += rj.low_instances("birch", birches)
    # --- undergrowth: ferns, shrubs and grass along the verges and in the woods
    ferns = scatter(c, (-50, 45, -30, 8), int(260 * density), lambda x, y: not lake_side(x, y) and 1.5 < D(x, y) < 14, 7)
    c["ferns"] = rj.ph_instances("fern_02", [(Vector((x, y, ground_z(c, x, y))), rz, s * 1.2) for (x, y, rz, s) in ferns])
    shrubs = scatter(c, (-50, 45, -30, 12), int(70 * density), lambda x, y: 1.6 < D(x, y) < 18, 8)
    c["shrubs"] = rj.ph_instances("shrub_02", [(Vector((x, y, ground_z(c, x, y))), rz, s) for (x, y, rz, s) in shrubs[0::2]])
    c["shrubs"] += rj.ph_instances("shrub_04", [(Vector((x, y, ground_z(c, x, y))), rz, s) for (x, y, rz, s) in shrubs[1::2]])
    grass = scatter(c, (-50, 45, -25, 12), int(500 * density), lambda x, y: 1.25 < D(x, y) < 5, 12)
    c["grass"] = rj.ph_instances("grass_medium_01", [(Vector((x, y, ground_z(c, x, y))), rz, s * 1.3) for (x, y, rz, s) in grass])


def lake(c):
    w = box("Lake", (0, 82.5, -0.32), (400, 155, 0.02), water_material())
    c["lake"] = w
    # far shore: low wooded hills in haze across the water (Ammersee is ~4 km wide)
    hill = pbr("FarHills", (0.06, 0.08, 0.07), 0.9)
    for k in range(9):
        x = -240 + k * 60
        bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=12, radius=1, location=(x, 420 + 30 * math.sin(k), -6))
        o = bpy.context.active_object; o.scale = (70, 30, 22 + 8 * math.sin(k * 1.7)); o.data.materials.append(hill)
    # the nearer far shore: a low bank with a ragged spruce-and-birch tree line (reads as forest in the mist,
    # instead of smooth hills) and a thin haze over the open water
    box("FarBank", (-25, 185, -0.15), (420, 50, 0.3), pbr("FarBank", (0.05, 0.06, 0.045), 0.95))
    rr = np.random.default_rng(11)
    trees = []
    x = -210.0
    while x < 170:
        y = 163 + rr.uniform(0, 14); kind = "birch" if rr.uniform() < 0.25 else ("fir_a" if rr.uniform() < 0.6 else "fir_b")
        trees.append((kind, (Vector((x, y, 0.0)), rr.uniform(0, 6.28), rr.uniform(0.9, 1.4) * (2.4 if kind == "birch" else 1.0))))
        x += rr.uniform(2.2, 4.5)
    for kind in ("fir_a", "fir_b", "birch"):
        rj.low_instances(kind, [t for k_, t in trees if k_ == kind])
    if c.get("light") in ("mist", "grey", "lowsun"):
        haze((-25, 120, 10), (420, 110, 20), density=0.006, color=(0.78, 0.8, 0.82), anis=0.4)


def lighting(c):
    L = c["light"]
    sc = bpy.context.scene
    if L == "lowsun":
        rj.sky("lowsun", rot=-10)           # sun low in the west over the lake, behind the trees
    elif L == "dusk":
        w, _ = rj.sky("dusk")
        w.node_tree.nodes["Background"].inputs['Strength'].default_value = 1.1
        from common import sun
        sun(1.5, 290, 0.9, (1.0, 0.45, 0.25), 3)          # the last afterglow low over the lake
    elif L == "bluehour":
        rj.sky("bluehour")
    elif L == "night":
        rj.sky("night")
        mo = bpy.data.lights.new("Moon", 'SUN'); mo.energy = 0.035; mo.color = (0.55, 0.65, 1.0); mo.angle = math.radians(1)
        o = bpy.data.objects.new("Moon", mo); bpy.context.collection.objects.link(o); o.rotation_euler = (math.radians(55), 0, math.radians(200))
    elif L == "mist":
        rj.sky("mist", rot=0)
    else:
        rj.sky("grey")


def build(variant=None):
    variant = variant or "lowsun"
    light = variant.split("|")[0]
    roles = variant.split("|")[1].split(",") if "|" in variant else []
    c = dict(variant=variant, light=light, P={})
    terrain(c)
    ribbon("Path", PTS, PATH_W, 0.0, mat("gravel"))
    vegetation(c, density=1.0)
    lake(c)
    lighting(c)
    for role in roles:
        base = role if role in rj.ROLES else role.rstrip("0123456789")
        c["P"][role] = person(base, name=role.capitalize())
    rj.finish_scene()
    return c


# ============================================================================ shots
def _onpath(c, h, d, offset=0.0):
    p, hd = path_point(d, offset); p.z = ground_z(c, p.x, p.y) + 0.0
    return p, hd


def bike_at(c, d, offset=-0.3):
    """Place the bike and its rider at distance d along the path."""
    bk = c["bike"]
    p, hd = _onpath(c, None, d, offset)
    p2, _ = _onpath(c, None, d + 1.2, offset); p0, _ = _onpath(c, None, d - 1.2, offset)
    dv = p2 - p0; hd = math.atan2(dv.y, dv.x)
    bk["root"].location = p + Vector((0, 0, 0.03)); bk["root"].rotation_euler = (0, 0, hd)
    rj.roll_bike(bk, d)
    bpy.context.view_layer.update()
    if "sister" in c["P"]:
        rj.ride_pose(c["P"]["sister"], bk, d)


def anim_ride(c, t, shot, dur):
    sec = t * dur
    d0, speed = SHOT_RIDE[shot]
    bike_at(c, d0 + speed * sec)
    rj.sway(c["reeds"][::7], sec, 0.02, 0.35)
    rj.sway(c["trees"], sec, 0.006, 0.2)


SHOT_RIDE = {"ride_track": (D_BEND - 34, 4.2), "ride_reeds": (D_BEND - 22, 4.2)}


def cam_ride_track(c, t):
    e = ease(t)
    d = D_BEND - 46 + 9 * e
    p, hd = path_point(d, 2.8); p.z = 1.25
    tgt, _ = path_point(D_BEND - 34 + 4.2 * 6.0 * t * 0.0 + 4.2 * 6.0 * t, -0.3)
    tgt.z = 0.9
    return (p, tgt, 50)


def cam_ride_reeds(c, t):
    e = ease(t)
    a = Vector((-24, 9.4, 0.15)); b = Vector((-19, 9.0, 0.2))
    tgt, _ = path_point(D_BEND - 22 + 4.2 * 5.0 * 0.5, 0.0); tgt.z = 0.8
    return (a.lerp(b, e), tgt, 85)


# window-view plate for the house (kitchen windows): the misty lake beyond the garden, no people
def cam_view(c, t):
    return (Vector((-6.0, 7.0, 5.5)), Vector((-4.0, 70.0, 2.0)), 30)              # over the reed tops: water, mist, far shore


def _f_bike(c, t):
    return c["bike"]["root"].location + Vector((0, 0, 0.8))


def _mk(shot, dur, cam, anim_fn, focus=None, dof=None):
    DUR[shot] = dur
    spec = dict(kind="anim", cam=cam, anim=lambda c, t: anim_fn(c, t, shot, dur))
    if focus:
        spec["focus"] = focus; spec["dof"] = dof or 4.0
    return spec


def _with_bike(fn):
    def b(variant=None):
        c = build(variant)
        c["bike"] = rj.bicycle("Bike")
        return c
    return b


# ---------------------------------------------------------------------------- helpers for people on the path
def hold_torch(h, tr, aim):
    """Right hand holds the torch in front of the chest; the beam (torch local -Y) points along `aim`."""
    fwd = forward(h); right = fwd.cross(Vector((0, 0, 1))).normalized()
    ch = rj.rjp.chest_point(h, 0.28, 0.22) + right * 0.12
    reach(h, "R", ch, Vector((0, 0, -1)) + right * 0.5, Vector(aim))
    fingers_curl(h, 60, side=("R",), thumb=30)
    w = h.bone_tail("wrist.R")
    tr.location = w + Vector(aim).normalized() * 0.02
    tr.rotation_euler = Vector(aim).to_track_quat('-Y', 'Z').to_euler()


def walker(c, h, p0, p1, sec, speed=1.3, stride=26, z=None):
    z0 = ground_z(c, (p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2) if z is None else z
    moving = walk(h, p0, p1, sec, speed=speed, stride=stride)
    gz = ground_z(c, h.arm.location.x, h.arm.location.y)
    h.arm.location.z += gz
    return moving


def add_torch(c, key, energy=320.0, cone=24.0):
    t = rj.torch(key, on=True, energy=energy, cone=cone)
    c.setdefault("torches", {})[key] = t
    return t


def police_car(c, loc, heading):
    import rj_vehicles, vehicles
    car = vehicles.make("polizei_1981", loc=loc, heading_deg=heading, lamps=True, real_lights=True)
    c["car"] = car
    return car


def _sweep_dir(fwd, sec, amp=0.5, rate=0.7, down=0.35, ph=0.0):
    a = amp * math.sin(sec * rate * 2 * math.pi + ph)
    ca, sa = math.cos(a), math.sin(a)
    d = Vector((fwd.x * ca - fwd.y * sa, fwd.x * sa + fwd.y * ca, -down))
    return d.normalized()


def _ambient(c, sec):
    rj.sway(c["reeds"][::5], sec, 0.025, 0.3)
    rj.sway(c["trees"], sec, 0.005, 0.18)


def P(d, off=0.0):
    p, hd = path_point(d, off)
    return p


# ---------------------------------------------------------------------------- shots
SHOT_RIDE = {"ride_track": (D_BEND - 34, 4.2), "ride_reeds": (D_BEND - 22, 4.2)}


def anim_ride(c, t, shot, dur):
    sec = t * dur
    d0, speed = SHOT_RIDE[shot]
    bike_at(c, d0 + speed * sec)
    _ambient(c, sec)


def cam_ride_track(c, t):
    e = ease(t)
    p = P(D_BEND - 46 + 10 * e, 1.3); p.z = 1.65
    tgt = c["bike"]["root"].location + Vector((0, 0, 0.8))
    return (p, tgt, 50)


def cam_ride_reeds(c, t):
    e = ease(t)
    x = -12.9 + 0.5 * e
    a = Vector((x, _shore_y(-12.6) + 8.0, 0.55))                   # low over the water, far, looking through the gap
    tgt = Vector((-12.4, np.interp(-12.4, [p.x for p in PTS], [p.y for p in PTS]), 0.85))
    return (a, tgt, 50)


# 5A / 5B: the empty bend at dusk
def anim_empty(c, t, shot, dur):
    _ambient(c, t * dur)


def cam_bend_push(c, t):
    e = ease(t)
    a = P(D_BEND - 13, 0.4); b = P(D_BEND - 8.5, 0.2); a.z = b.z = 1.45
    tgt = P(D_BEND + 4, 0.0); tgt.z = 1.2
    return (a.lerp(b, e), tgt, 35)


def cam_bend_high(c, t):
    e = ease(t)
    a = Vector((-9, 16, 7.5)); b = Vector((-5, 16.5, 7.0))
    return (a.lerp(b, e), Vector((1, -1.5, 0.3)), 30)


# 6A: father walks fast along the path left to right (side track); 6B: the uncle right to left with a torch
def anim_father(c, t, shot, dur):
    sec = t * dur
    h = c["P"]["father"]
    walker(c, h, P(D_BEND - 24), P(D_BEND - 2), sec + 0.5, speed=1.6, stride=30)
    side = forward(h).cross(Vector((0, 0, 1))).normalized()
    h.rot("head", (0, 0, 1), 10 * math.sin(sec * 0.9))
    _ambient(c, sec)


def cam_father(c, t):
    h = c["P"]["father"]; p = Vector(h.arm.location)
    cam = p + Vector((0.6, -6.0, 1.3)) + Vector((-0.3 * (1 - t), 0, 0))
    return (cam, p + Vector((0.4, 0, 1.15)), 45)


def anim_uncle(c, t, shot, dur):
    sec = t * dur
    h = c["P"]["uncle"]
    walker(c, h, P(D_BEND + 5, 0.3), P(D_BEND - 6, 0.0), sec + 0.3, speed=1.5, stride=28)
    fwd = forward(h)
    hold_torch(h, c["torches"]["u"], _sweep_dir(fwd, sec, 0.45, 0.35, 0.3))
    _ambient(c, sec)


def cam_uncle(c, t):
    e = ease(t)
    h = c["P"]["uncle"]; p = Vector(h.arm.location)
    a = P(D_BEND - 6.5, 1.5); b = P(D_BEND - 7.5, 1.5); a.z = 1.1; b.z = 1.15     # on the lake-side verge, looking up the path
    return (a.lerp(b, e), p + Vector((0, 0, 1.2)), 40)


# 7A: the two men meet at the bend (wide, high) ; 7B: low behind the father calling into the woods
def anim_meet(c, t, shot, dur):
    sec = t * dur
    f = c["P"]["father"]; u = c["P"]["uncle"]
    if shot == "meet_wide":
        walker(c, f, P(D_BEND - 9), P(D_BEND - 1.0), sec + 0.5, speed=1.3)
        walker(c, u, P(D_BEND + 7), P(D_BEND + 0.2), sec + 0.5, speed=1.3)
        hold_torch(u, c["torches"]["u"], _sweep_dir(forward(u), sec, 0.2, 0.3, 0.45))
    else:
        rj.stand(f, P(D_BEND + 0.6, -1.0), 0.0); f.arm.location.z += ground_z(c, *P(D_BEND + 0.6, -1.0).xy)
        f.arm.rotation_euler.z = math.radians(-20)            # faces the woods (south-west of the bend)
        fwd = forward(f); right = fwd.cross(Vector((0, 0, 1))).normalized()
        head = f.bone_head("head"); call = 0.5 + 0.5 * math.sin(sec * 1.1)
        mouth = head + fwd * 0.12 + Vector((0, 0, -0.03))
        for sd, sg in SIDE.items():
            reach(f, sd, mouth + right * sg * 0.06 + fwd * 0.02 - Vector((0, 0, 0.04)), Vector((0, 0, -1)) + right * sg * 0.8, fwd + Vector((0, 0, 0.3)))
        f.rot("spine03", right, 6 * call); f.rot("head", right, 6 * call)          # leans into the call
        rj.stand(u, P(D_BEND + 2.2, -0.6), 0.0); u.arm.location.z += ground_z(c, *P(D_BEND + 2.2).xy)
        u.arm.rotation_euler.z = math.radians(10)
        hold_torch(u, c["torches"]["u"], _sweep_dir(forward(u), sec, 0.6, 0.15, 0.25))
    _ambient(c, sec)


def cam_meet_wide(c, t):
    e = ease(t)
    a = Vector((-5, 9, 5.2)); b = Vector((-3.8, 9.4, 4.8))                 # closer and lower: the two men read
    return (a.lerp(b, e), Vector((0.0, -0.5, 0.9)), 32)


def cam_father_call(c, t):
    e = ease(t)
    f = c["P"]["father"]; p = Vector(f.arm.location)
    a = p + Vector((0.9, 2.4, 0.55)); b = p + Vector((0.7, 2.0, 0.6))
    tgt = p + Vector((-0.8, -6.0, 1.4))
    return (a.lerp(b, e), tgt, 28)


# 8A: a line of torches through the birches, the patrol car's blue beacon on the path ; 8B: firefighters at the reeds
LINE = ["officer", "officer2", "neighbour", "officer3", "uncle"]


def anim_line(c, t, shot, dur):
    sec = t * dur
    roles = [r for r in LINE if r in c["P"]]
    for k, r in enumerate(roles):
        h = c["P"][r]
        x0 = -24.5 + k * 2.4; y0 = -2.6 - 0.5 * (k % 2)
        walker(c, h, (x0, y0), (x0 - 0.6, y0 - 8), sec + k * 0.3, speed=0.7, stride=22)
        hold_torch(h, c["torches"][r], _sweep_dir(forward(h), sec, 0.55, 0.25, 0.35, ph=k * 1.3))
    _ambient(c, sec)


def cam_line(c, t):
    e = ease(t)
    a = Vector((-15.5, 3.2, 1.6)); b = Vector((-16.6, 2.8, 1.6))
    return (a.lerp(b, e), Vector((-21.5, -5.0, 0.9)), 30)


def anim_fire(c, t, shot, dur):
    sec = t * dur
    for k, r in enumerate([r for r in ("firefighter", "firefighter2") if r in c["P"]]):
        h = c["P"][r]
        x0 = -16 + k * 2.5
        y0 = np.interp(x0, [p.x for p in PTS], [p.y for p in PTS]) + 3.0 + k * 0.6
        walker(c, h, (x0, y0), (x0 + 10, y0 - 1.3), sec + k * 0.4, speed=0.9)
        lan = c["lanterns"][k]
        fwd = forward(h); right = fwd.cross(Vector((0, 0, 1))).normalized()
        hand = h.arm.location + right * 0.32 + fwd * 0.15 + Vector((0, 0, 0.72))
        reach(h, "R", hand + Vector((0, 0, 0.12)), Vector((0, 0, -1)) + right, Vector((0, 0, -1)))
        lan.location = h.bone_tail("wrist.R") + Vector((0, 0, -0.32 + 0.015 * math.sin(sec * 4 + k)))
        lan.rotation_euler = (0.06 * math.sin(sec * 3 + k), 0, 0)
    _ambient(c, sec)


def cam_fire(c, t):
    e = ease(t)
    a = P(D_BEND - 19, -1.2); a.z = 1.5; b = P(D_BEND - 18, -1.4); b.z = 3.6        # from the woods side of the path, crane up
    f = c["P"].get("firefighter"); tgt = Vector(f.arm.location) + Vector((1.0, 0, 1.0)) if f else Vector((-10, 3, 1))
    return (a.lerp(b, e), tgt, 32)


# 9A: the dog leads its handler away from the lakeshore into the trees ; 9B: the beam bobs toward camera
def anim_dog(c, t, shot, dur):
    sec = t * dur
    h = c["P"]["officer"]; dg = c["dog"]
    if shot == "dog_low":
        a = Vector((-13.5, 5.5)); b = Vector((-11.8, -6.0))
    else:
        a = Vector((-11.6, -5.0)); b = Vector((-10.6, -13.0))
    d = (b - a); u = d.normalized(); dist = min(d.length, sec * 1.25)
    dpos = a + u * (dist + 1.6)
    dg["root"].location = (dpos.x, dpos.y, ground_z(c, dpos.x, dpos.y)); dg["root"].rotation_euler.z = math.atan2(u.y, u.x)
    rj.dog_walk(dg, dist, pull=1.0, sniff=0.6 + 0.4 * math.sin(sec * 1.3), sec=sec)
    walker(c, h, a, b, sec, speed=1.25, stride=28)
    fwd = forward(h); right = fwd.cross(Vector((0, 0, 1))).normalized()
    hold_torch(h, c["torches"]["officer"], _sweep_dir(fwd, sec, 0.3, 0.6, 0.4))
    # leash from the left hand to the collar
    lh = rj.rjp.chest_point(h, 0.4, 0.45) - right * 0.15
    reach(h, "L", lh, Vector((0, 0, -1)) - right * 0.5, fwd)
    collar = dg["root"].matrix_world @ Vector((0.42, 0, 0.72))
    w = h.bone_tail("wrist.L")
    sp = c["leash"].data.splines[0]
    for k, pt in enumerate(sp.points):
        q = k / (len(sp.points) - 1)
        pp = w.lerp(collar, q) + Vector((0, 0, -0.15 * math.sin(math.pi * q)))
        pt.co = (*pp, 1)
    _ambient(c, sec)


def cam_dog_low(c, t):
    e = ease(t)
    a = Vector((-8.0, -0.2, 0.5)); b = Vector((-8.5, -0.9, 0.55))
    return (a.lerp(b, e), c["dog"]["root"].location + Vector((-0.8, 0, 0.6)), 26)


def cam_dog_front(c, t):
    e = ease(t)
    a = Vector((-10.2, -15.8, 0.9)); b = Vector((-10.25, -15.4, 0.95))
    return (a.lerp(b, e), c["P"]["officer"].bone_head("spine05"), 45)


# 10A: the torch finds the bicycle in the brush ; 10B: officers ring it with torches, the camera pulls back
def anim_brush(c, t, shot, dur):
    sec = t * dur
    bk = c["bike"]
    bk["root"].location = BRUSH + Vector((0, 0, ground_z(c, BRUSH.x, BRUSH.y) + 0.13)); bk["root"].rotation_euler = (math.radians(84), 0, math.radians(35))
    h = c["P"]["officer"]
    if shot == "brush_find":
        rj.stand(h, BRUSH + Vector((-1.4, 2.8, 0)), 0.0); h.arm.rotation_euler.z = math.radians(-25)
        h.arm.location.z += ground_z(c, BRUSH.x - 1.4, BRUSH.y + 2.8)
        fwd = forward(h)
        target = BRUSH + Vector((0, 0, 0.3)); w0 = h.bone_head("upperarm01.R")
        hit = (target - w0).normalized()
        swp = _sweep_dir(fwd, 0.0, 0.0, 0.0, 0.4)
        k = ease(min(1.0, sec / (dur * 0.65)))
        a0 = Vector((math.cos(-1.2), math.sin(-1.2), -0.35)).normalized()
        aim = a0.lerp(hit, k).normalized()
        aim = (aim + Vector((0.08 * math.sin(sec * 3.0) * (1 - k), 0, 0))).normalized()
        hold_torch(h, c["torches"]["officer"], aim)
        if "dog" in c:
            dg = c["dog"]; dg["root"].location = BRUSH + Vector((0.9, 1.3, ground_z(c, BRUSH.x + 0.9, BRUSH.y + 1.3)))
            dg["root"].rotation_euler.z = math.radians(-120); rj.dog_walk(dg, 0.2 * sec, sniff=1.0, sec=sec)
    else:
        roles = [r for r in ("officer", "officer2", "officer3", "neighbour", "uncle") if r in c["P"]]
        for k, r in enumerate(roles):
            hh = c["P"][r]; ang = k / len(roles) * 2 * math.pi + 0.4
            pos = BRUSH + Vector((math.cos(ang), math.sin(ang), 0)) * 2.6
            rj.stand(hh, pos, 0.0)
            dvec = BRUSH - pos; hh.arm.rotation_euler.z = math.atan2(dvec.x, -dvec.y)
            hh.arm.location.z += ground_z(c, pos.x, pos.y)
            aim = (BRUSH + Vector((0, 0, 0.2)) - hh.bone_head("upperarm01.R")).normalized()
            aim = (aim + Vector((0.05 * math.sin(sec * 1.5 + k), 0.05 * math.cos(sec * 1.2 + k), 0))).normalized()
            hold_torch(hh, c["torches"][r], aim)
    _ambient(c, sec)


def cam_brush_find(c, t):
    e = ease(t)
    a = BRUSH + Vector((-3.4, 4.2, 1.7)); b = BRUSH + Vector((-3.0, 3.7, 1.6))
    return (a.lerp(b, e), BRUSH + Vector((0.2, 0.3, 0.2)), 35)


def cam_brush_ring(c, t):
    e = ease(t)
    a = BRUSH + Vector((-3.0, 4.5, 2.2)); b = BRUSH + Vector((-4.8, 7.2, 4.6))
    return (a.lerp(b, e), BRUSH + Vector((0, 0, 0.3)), 30)


# 11A: the brother runs down the night path toward the torches ; 11B: he joins the line of searchers
def anim_bro(c, t, shot, dur):
    sec = t * dur
    b = c["P"]["brother"]
    if shot == "bro_run":
        walker(c, b, P(D_BEND - 40), P(D_BEND - 8), sec, speed=3.4, stride=42)
        b.rot("spine03", forward(b).cross(Vector((0, 0, 1))).normalized(), -8)
        for k, r in enumerate([r for r in LINE if r in c["P"]]):
            h = c["P"][r]; x0 = -16 + k * 2.6; y0 = -4 - (k % 2)
            walker(c, h, (x0, y0), (x0 + 0.6, y0 - 7), sec + k * 0.3, speed=0.6, stride=20)
            hold_torch(h, c["torches"][r], _sweep_dir(forward(h), sec, 0.5, 0.25, 0.3, ph=k))
    else:
        walker(c, b, (-23.5, -1.5), (-22.5, -9.0), sec + 0.2, speed=1.0, stride=24)
        for k, r in enumerate([r for r in LINE if r in c["P"]]):
            h = c["P"][r]; x0 = -26 + k * 3.0 + (1.6 if k >= 1 else 0); y0 = -4.0 - 0.5 * (k % 2)
            walker(c, h, (x0, y0), (x0 + 0.5, y0 - 7), sec + k * 0.3, speed=0.65, stride=22)
            hold_torch(h, c["torches"][r], _sweep_dir(forward(h), sec, 0.5, 0.25, 0.3, ph=k))
    _ambient(c, sec)


def cam_bro_run(c, t):
    b = c["P"]["brother"]; p = Vector(b.arm.location)
    back = P(D_BEND - 40 + 3.4 * t * DUR["bro_run"] - 4.5, 0.5)
    back.z = p.z + 1.5
    return (back, p + Vector((0, 0, 1.2)) + (P(D_BEND - 8) - p) * 0.15, 40)


def cam_bro_line(c, t):
    e = ease(t)
    a = Vector((-30.5, -7.0, 1.3)); b = Vector((-30.0, -7.6, 1.35))
    return (a.lerp(b, e), Vector((-23.0, -6.0, 1.2)), 35)


# 13A: helicopter low over the misty lake ; 13B: divers in the reeds, a police boat beyond
def anim_heli(c, t, shot, dur):
    sec = t * dur
    hl = c["heli"]
    x = -48 + 11 * sec                                   # low and slow along the shore, over the misty water
    hl.location = (x, 52 - 0.1 * x, 8.0 + 0.4 * math.sin(sec * 0.7)); hl.rotation_euler = (0, math.radians(-5), math.radians(-6))
    _ambient(c, sec)


def cam_heli(c, t):
    e = ease(t)
    y0 = _shore_y(-12.6) + 2.2                                           # standing in the shallows past the reeds: water, far shore, sky
    a = Vector((-12.9, y0, 1.35)); b = Vector((-12.6, y0 + 0.3, 1.4))
    tgt = c["heli"].location * 0.75 + Vector((-14.0, 200.0, 2.0)) * 0.25
    return (a.lerp(b, e), tgt, 40)


def anim_divers(c, t, shot, dur):
    sec = t * dur
    for k, r in enumerate([r for r in ("diver", "diver2") if r in c["P"]]):
        h = c["P"][r]; x0 = -13.3 + k * 1.3; y0 = _shore_y(-12.6) + 1.0 + k * 0.9
        moving = walk(h, (x0, y0), (x0 + 0.4, y0 + 1.8), sec + k * 0.7, speed=0.4, stride=16)
        h.arm.location.z = -0.62                     # waist deep among the reeds
    b = c["boat"]
    b.location = (-15 + 0.4 * sec, 24, -0.38 + 0.03 * math.sin(sec * 1.3)); b.rotation_euler = (0.02 * math.sin(sec), 0.015 * math.sin(sec * 1.4), math.radians(170))
    _ambient(c, sec)


def cam_divers(c, t):
    e = ease(t)
    a = Vector((-12.8, 3.6, 1.45)); b = Vector((-12.6, 4.1, 1.45))          # through the reed gap toward the water
    return (a.lerp(b, e), Vector((-12.6, _shore_y(-12.6) + 2.5, 0.2)), 40)


# Ch2 14B: a long lens on the empty bend in grey day, drifting toward the trees
def cam_bend_long(c, t):
    e = ease(t)
    a = Vector((-30, 4.5, 1.6)); b = Vector((-30, 3.6, 1.6))
    return (a.lerp(b, e), Vector((1.0, -2.0, 1.2)).lerp(Vector((2.5, -4.0, 1.3)), e), 120)


# window-view plate for the house (kitchen windows): the misty lake beyond the garden, no people
def cam_view(c, t):
    return (Vector((-6.0, 7.0, 5.5)), Vector((-4.0, 70.0, 2.0)), 30)              # over the reed tops: water, mist, far shore


def _f_bike(c, t):
    return c["bike"]["root"].location + Vector((0, 0, 0.8))


def _mk(shot, dur, cam, anim_fn, focus=None, dof=None):
    DUR[shot] = dur
    spec = dict(kind="anim", cam=cam, anim=lambda c, t: anim_fn(c, t, shot, dur))
    if focus:
        spec["focus"] = focus; spec["dof"] = dof or 4.0
    return spec


def _fp(role, bone="head"):
    return lambda c, t: c["P"][role].bone_head(bone)


MOVES = {
    "ride_track": _mk("ride_track", 6.0, cam_ride_track, anim_ride, _f_bike, 5.6),
    "ride_reeds": _mk("ride_reeds", 5.0, cam_ride_reeds, anim_ride, _f_bike, 8.0),
    "bend_push": _mk("bend_push", 5.0, cam_bend_push, anim_empty),
    "bend_high": _mk("bend_high", 4.5, cam_bend_high, anim_empty),
    "father_walk": _mk("father_walk", 4.5, cam_father, anim_father, _fp("father"), 4.0),
    "uncle_torch": _mk("uncle_torch", 4.0, cam_uncle, anim_uncle, _fp("uncle"), 4.0),
    "meet_wide": _mk("meet_wide", 4.5, cam_meet_wide, anim_meet),
    "father_call": _mk("father_call", 4.5, cam_father_call, anim_meet, _fp("father"), 2.8),
    "night_line": _mk("night_line", 4.5, cam_line, anim_line, lambda c, t: Vector((-21, -8, 1.2)), 4.0),
    "night_fire": _mk("night_fire", 4.5, cam_fire, anim_fire),
    "dog_low": _mk("dog_low", 4.5, cam_dog_low, anim_dog, lambda c, t: c["dog"]["root"].location + Vector((0, 0, 0.5)), 2.8),
    "dog_front": _mk("dog_front", 4.0, cam_dog_front, anim_dog, _fp("officer", "spine05"), 2.8),
    "brush_find": _mk("brush_find", 4.5, cam_brush_find, anim_brush, lambda c, t: BRUSH, 2.8),
    "brush_ring": _mk("brush_ring", 4.5, cam_brush_ring, anim_brush, lambda c, t: BRUSH, 4.0),
    "bro_run": _mk("bro_run", 4.0, cam_bro_run, anim_bro, _fp("brother", "spine05"), 4.0),
    "bro_line": _mk("bro_line", 4.0, cam_bro_line, anim_bro, _fp("brother"), 4.0),
    "heli": _mk("heli", 5.0, cam_heli, anim_heli),
    "divers": _mk("divers", 5.0, cam_divers, anim_divers, lambda c, t: Vector((-12, 8.6, 0.1)), 5.6),
    "bend_long": _mk("bend_long", 5.0, cam_bend_long, anim_empty),
    "view": _mk("view", 3.0, cam_view, anim_empty),
}
NIGHT_LINE = "night|officer,officer2,neighbour,officer3,uncle"
VARIANT_FOR = {"ride_track": "lowsun|sister", "ride_reeds": "lowsun|sister", "bend_push": "dusk", "bend_high": "dusk",
               "father_walk": "dusk|father", "uncle_torch": "dusk|uncle", "meet_wide": "bluehour|father,uncle+lift",
               "father_call": "bluehour|father,uncle", "night_line": NIGHT_LINE + "+car", "night_fire": "night|firefighter,firefighter2",
               "dog_low": "night|officer+dog", "dog_front": "night|officer+dog", "brush_find": "night|officer+dog+lift",
               "brush_ring": "night|officer,officer2,officer3,neighbour,uncle", "bro_run": "night|brother,officer,officer2,neighbour",
               "bro_line": "night|brother,officer,officer2,neighbour,officer3", "heli": "mist+heli", "divers": "mist|diver,diver2+boat",
               "bend_long": "grey", "view": "mist"}

_build = build


def build(variant=None):                      # noqa: F811
    variant = variant or "lowsun"
    extras = set()
    head = variant.split("|")[0]
    parts = head.split("+"); light = parts[0]; extras |= set(parts[1:])
    roles = ""
    if "|" in variant:
        rp = variant.split("|")[1].split("+"); roles = rp[0]; extras |= set(rp[1:])
    c = _build(light + ("|" + roles if roles else ""))
    c["bike"] = rj.bicycle("Bike"); c["bike"]["root"].location = (0, 0, -100)
    if light in ("night", "dusk", "bluehour"):
        for r in c["P"]:
            if r in LINE or r in ("officer", "uncle") or r.startswith("officer"):
                add_torch(c, r if r != "uncle" or light == "night" else "u")
        if "uncle" in c["P"] and "u" not in c.get("torches", {}):
            add_torch(c, "u")
    if "car" in extras:
        police_car(c, P(D_BEND - 20, -1.4), -6)
    if "dog" in extras or light == "night":
        # brush round the place where the bicycle lies
        rj.ph_instances("fern_02", [(Vector((BRUSH.x + dx, BRUSH.y + dy, ground_z(c, BRUSH.x + dx, BRUSH.y + dy))), dx * 3, 1.3)
                                     for (dx, dy) in ((-1.2, 0.6), (1.1, -0.4), (0.4, 1.3), (-0.6, -1.2), (1.6, 0.9))])
    if "dog" in extras:
        c["dog"] = rj.dog("Dog")
        dark = rj.pbr("DogNight", (0.012, 0.011, 0.01), 0.7)          # at night only a dark shape in the torch light
        for o in c["dog"]["root"].children_recursive:
            if o.type == 'MESH':
                o.data.materials.clear(); o.data.materials.append(dark)
        cu = bpy.data.curves.new("Leash", 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = 0.006
        sp = cu.splines.new('POLY'); sp.points.add(7)
        o = bpy.data.objects.new("Leash", cu); bpy.context.collection.objects.link(o); o.data.materials.append(rj.mat("black"))
        c["leash"] = o
    if "firefighter" in c["P"] or "firefighter2" in c["P"]:
        c["lanterns"] = []
        for k in range(2):
            ln = rj.model_fit("Lantern_01", (0, 0, -50), height=0.32)[0]
            l = bpy.data.lights.new("LanternL", 'POINT'); l.energy = 25; l.color = (1.0, 0.7, 0.4); l.shadow_soft_size = 0.03
            lo = bpy.data.objects.new("LanternL", l); bpy.context.collection.objects.link(lo); lo.parent = ln; lo.location = (0, 0, 0.14 / max(ln.scale.x, 1e-3))
            c["lanterns"].append(ln)
    if "heli" in extras:
        import rj_vehicles, vehicles
        c["heli"] = vehicles.make("helicopter_police", loc=(0, 40, 14), heading_deg=0)
    if "boat" in extras:
        import rj_vehicles, vehicles
        c["boat"] = vehicles.make("dinghy_police", loc=(-9, 21, -0.3), heading_deg=170)
    import look
    if light in ("lowsun", "mist", "grey"):
        look.forest(mood="mist", azim={"lowsun": 5, "mist": 110, "grey": 200}[light], area=((-5, 0), (110, 70)), canopy=16.0,
                    exposure={"lowsun": 0.9, "mist": 0.55, "grey": 1.0}[light])
    elif light in ("dusk", "bluehour"):
        look.forest(mood="dusk", azim=290, area=((-5, 0), (110, 70)), canopy=16.0)
    else:                                   # night: a moonlit version of the dusk look (readable deep blue) + torches
        look.forest(mood="dusk", azim=200, area=((-5, -5), (110, 70)), canopy=16.0, exposure=1.0)
    rj.sink_haze()
    if "lift" in extras:                    # readable night: figures, beams and the red bike must read (keeps the blue mood)
        bpy.context.scene.view_settings.exposure += 0.8 + (0.45 if light == "bluehour" else 0.0)
        for o in bpy.data.objects:
            if o.type == 'LIGHT' and o.data.type == 'SPOT':
                o.data.energy *= 2.0
        if light == "night":                # a low cool moon fill skimming the scene
            ml = bpy.data.lights.new("MoonFill", 'SUN'); ml.energy = 0.08; ml.color = (0.55, 0.65, 1.0); ml.angle = math.radians(3)
            mo = bpy.data.objects.new("MoonFill", ml); bpy.context.collection.objects.link(mo)
            mo.rotation_euler = (math.radians(62), 0, math.radians(150))
    return c
