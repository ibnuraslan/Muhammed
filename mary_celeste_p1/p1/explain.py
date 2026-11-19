"""Atrium-style explainer 3D for Part 1 (real 3D, never flat 2D):

  hold_cutaway()   the Mary Celeste as a glass 'X-ray' hull on a dark studio floor, the water in her hold
                   shown as a solid blue body 3.5 ft deep, with a 3D dimension marker and label.
  atlas()          a dark textured relief map of the eastern Atlantic (Natural Earth land, extruded), with
                   the Azores, Portugal, Spain, Morocco and Gibraltar; red hexagon markers, a dashed route,
                   3D labels in Courier Prime, filled soft orange 'ripple' bands round a marker.
"""
import math, os, struct
import numpy as np
import bpy
from mathutils import Vector, Matrix
import env as E
import ship

FONT = os.path.join(E.P1, "assets", "fonts", "CourierPrime-Bold.ttf")
RED = (0.85, 0.08, 0.05)
ORANGE = (1.0, 0.45, 0.12)


def text3d(name, body, loc, size=1.0, color=(1, 1, 1), strength=2.0, rot=(0, 0, 0), extrude=0.0, align='CENTER', font=FONT):
    cu = bpy.data.curves.new(name, 'FONT'); cu.body = body; cu.size = size; cu.extrude = extrude
    cu.align_x = align; cu.align_y = 'CENTER'
    try:
        cu.font = bpy.data.fonts.load(font, check_existing=True)
    except Exception:
        pass
    o = bpy.data.objects.new(name, cu); bpy.context.scene.collection.objects.link(o)
    o.location = loc; o.rotation_euler = rot
    o.data.materials.append(E.emission_mat(name + "_m", color, strength))
    o.visible_shadow = False
    return o


# ============================================================================ the hold, X-ray
def ghost_mat(name, edge=(0.95, 0.65, 0.35), body=(0.6, 0.75, 0.9), alpha=0.12):
    m = bpy.data.materials.new(name); m.use_nodes = True
    N = m.node_tree.nodes; Lk = m.node_tree.links; N.remove(N["Principled BSDF"])
    fr = N.new("ShaderNodeLayerWeight"); fr.inputs['Blend'].default_value = 0.12
    em = N.new("ShaderNodeEmission"); em.inputs['Color'].default_value = (*edge, 1); em.inputs['Strength'].default_value = 0.9
    tr = N.new("ShaderNodeBsdfTransparent")
    gl = N.new("ShaderNodeBsdfGlossy"); gl.inputs['Roughness'].default_value = 0.15; gl.inputs['Color'].default_value = (*body, 1)
    m1 = N.new("ShaderNodeMixShader"); m1.inputs[0].default_value = alpha
    Lk.new(tr.outputs[0], m1.inputs[1]); Lk.new(gl.outputs[0], m1.inputs[2])
    m2 = N.new("ShaderNodeMixShader"); Lk.new(fr.outputs['Facing'], m2.inputs[0])
    Lk.new(m1.outputs[0], m2.inputs[1]); Lk.new(em.outputs[0], m2.inputs[2])
    Lk.new(m2.outputs[0], N["Material Output"].inputs['Surface'])
    return m


def hold_water(z_top, inset=0.12, name="hold_water"):
    """A closed water body following the inside of the hull from the keel up to z_top (ship coords)."""
    ns, nt = 90, 16; rings = []
    for i in range(ns + 1):
        s = i / ns
        ring = []
        for j in range(nt + 1):
            t0 = j / nt
            # height fraction where the hull reaches z_top at this station
            xs, xb = ship._ends(0.3)
            x = xs + s * (xb - xs)
            tw = (z_top + ship.DRAFT) / (ship.zdeck(x) + ship.DRAFT)
            t = t0 * tw
            xs2, xb2 = ship._ends(t)
            x2 = xs2 + s * (xb2 - xs2)
            b = max(ship.half_breadth(s, t) - inset, 0.0)
            ring.append((x2, b, ship.hull_z(x2, t) + inset * (1 - t0)))
        rings.append(ring)
    V = []; F = []
    nr = nt + 1
    for i, ring in enumerate(rings):                      # each ring: starboard bottom->top, then port top->bottom
        for (x, b, z) in ring:
            V.append((x, -b, z))
        for (x, b, z) in reversed(ring):
            V.append((x, b, z))
    per = 2 * nr
    for i in range(ns):
        for k in range(per):
            a = i * per + k; b_ = i * per + (k + 1) % per
            F.append([a, b_, b_ + per, a + per])
    F.append(list(range(per))[::-1]); F.append([ns * per + k for k in range(per)])
    # real bilge water: dark sea-green, glossy, light dies in it with depth (no glow)
    m = E.principled("holdwater", (0.1, 0.2, 0.18), rough=0.08, **{"Transmission Weight": 0.5, "IOR": 1.333})
    va = m.node_tree.nodes.new("ShaderNodeVolumeAbsorption"); va.inputs['Color'].default_value = (0.25, 0.45, 0.38, 1)
    va.inputs['Density'].default_value = 1.5
    m.node_tree.links.new(va.outputs[0], m.node_tree.nodes["Material Output"].inputs['Volume'])
    o = ship.mesh_obj(name, V, F, m, smooth=True)
    return o


def hold_cutaway(water_ft=3.5):
    E.render_setup(samples=96)
    mc = ship.build("MCx", sails="found", rail_gap=None, detail=False, wet=0.2)
    g = ghost_mat("xray", edge=(1.0, 0.62, 0.3), body=(0.5, 0.6, 0.7), alpha=0.015)
    for o in list(mc["coll"].objects):
        if o.type not in ('MESH', 'CURVE'):
            continue
        n = o.name.lower()
        if any(k in n for k in ("sail", "shred", "furl", "rope", "shroud", "stay", "brace", "lift", "ratline", "chain", "rig")):
            o.hide_render = True; continue                     # the X-ray shows the hull, deck and spars only
        o.data.materials.clear(); o.data.materials.append(g)
        o.visible_shadow = False
    keel_in = -ship.DRAFT + 0.25                         # inside of the bottom planking / ceiling
    ztop = keel_in + water_ft * 0.3048
    w = hold_water(ztop)
    # studio: dark floor, soft warm key, faint rim
    fl = E.principled("studiofloor", (0.02, 0.018, 0.016), rough=0.35)
    ship.box("floor", (0, 0, -ship.DRAFT - 0.6), (200, 200, 0.1), fl)
    wd = bpy.data.worlds.new("W"); bpy.context.scene.world = wd; wd.use_nodes = True
    wd.node_tree.nodes["Background"].inputs[0].default_value = (0.02, 0.018, 0.016, 1)
    E.area("key", (-12, -14, 14), (0, 0, -1), 4000, size=8, color=(1.0, 0.85, 0.7))
    E.area("rim", (14, 10, 6), (0, 0, -1), 1500, size=6, color=(0.7, 0.8, 1.0))
    # dimension marker at midships, starboard side: two ticks and a bar, label
    x = -1.2; y = -ship.B / 2 - 0.6
    bar = E.emission_mat("dim", ORANGE, 4.0)
    ship.cyl("dim_bar", (x, y, keel_in), (x, y, ztop), 0.035, mat=bar, verts=10)
    for z in (keel_in, ztop):
        ship.cyl("dim_tick", (x, y - 0.3, z), (x, y + 0.3, z), 0.03, mat=bar, verts=10)
    text3d("dim_label", "3½ FT", (x, y - 0.5, (keel_in + ztop) / 2), size=1.5, color=(1, 0.92, 0.85), strength=3.0,
           rot=(math.radians(90), 0, 0), align='RIGHT')
    return dict(ztop=ztop, keel=keel_in, x=x, y=y, mc=mc)


# ============================================================================ map
def _read_shp(path):
    """Minimal ESRI shapefile reader (polygons): returns a list of rings (lon, lat)."""
    data = open(path, "rb").read()
    pos = 100; rings = []
    while pos < len(data):
        _, clen = struct.unpack(">ii", data[pos:pos + 8]); pos += 8
        rec = data[pos:pos + clen * 2]; pos += clen * 2
        st = struct.unpack("<i", rec[:4])[0]
        if st not in (5, 15, 25):
            continue
        nparts, npts = struct.unpack("<ii", rec[36:44])
        parts = list(struct.unpack(f"<{nparts}i", rec[44:44 + 4 * nparts]))
        off = 44 + 4 * nparts
        pts = np.frombuffer(rec[off:off + 16 * npts], dtype="<f8").reshape(-1, 2)
        parts.append(npts)
        for a, b in zip(parts[:-1], parts[1:]):
            rings.append(pts[a:b])
    return rings


BOX = (-34.0, -3.0, 30.0, 45.0)      # lon0, lon1, lat0, lat1
SCALE = 1.0                          # 1 unit per degree of longitude (lat scaled by 1/cos at 37N for shape)
KLAT = 1.0 / math.cos(math.radians(37.0))


def geo(lon, lat, z=0.0):
    return Vector(((lon - (BOX[0] + BOX[1]) / 2) * SCALE, (lat - (BOX[2] + BOX[3]) / 2) * SCALE * KLAT, z))


def atlas():
    """Builds the map table. Land rings are clipped to BOX and extruded as low dark relief."""
    E.render_setup(samples=64)
    shp = os.path.join(E.P1, "assets", "geo", "ne_50m_land.shp")
    rings = _read_shp(shp)
    land = bpy.data.materials.new("land"); land.use_nodes = True
    N = land.node_tree.nodes; Lk = land.node_tree.links; p = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord"); nz = N.new("ShaderNodeTexNoise"); nz.inputs['Scale'].default_value = 3.0; nz.inputs['Detail'].default_value = 12
    Lk.new(tc.outputs['Object'], nz.inputs['Vector'])
    rp = N.new("ShaderNodeValToRGB"); rp.color_ramp.elements[0].color = (0.10, 0.075, 0.05, 1); rp.color_ramp.elements[1].color = (0.32, 0.24, 0.15, 1)
    Lk.new(nz.outputs['Fac'], rp.inputs['Fac']); Lk.new(rp.outputs['Color'], p.inputs['Base Color'])
    bm = N.new("ShaderNodeBump"); bm.inputs['Strength'].default_value = 0.6; Lk.new(nz.outputs['Fac'], bm.inputs['Height'])
    Lk.new(bm.outputs['Normal'], p.inputs['Normal']); p.inputs['Roughness'].default_value = 0.8
    import bmesh
    for k, r in enumerate(rings):
        lon, lat = r[:, 0], r[:, 1]
        if lon.max() < BOX[0] - 2 or lon.min() > BOX[1] + 2 or lat.max() < BOX[2] - 2 or lat.min() > BOX[3] + 2:
            continue
        pts = [geo(a, b) for a, b in r[:-1]]
        if len(pts) < 3:
            continue
        bmm = bmesh.new()
        vs = [bmm.verts.new(p) for p in pts]
        try:
            f = bmm.faces.new(vs)
        except ValueError:
            bmm.free(); continue
        bmesh.ops.triangulate(bmm, faces=[f])
        ext = bmesh.ops.extrude_face_region(bmm, geom=list(bmm.faces))
        for v in [g for g in ext["geom"] if isinstance(g, bmesh.types.BMVert)]:
            v.co.z += 0.12
        me = bpy.data.meshes.new(f"land{k}"); bmm.to_mesh(me); bmm.free()
        o = bpy.data.objects.new(f"land{k}", me); bpy.context.scene.collection.objects.link(o)
        o.data.materials.append(land)
        bv = o.modifiers.new("b", "BEVEL"); bv.width = 0.04; bv.segments = 2
    # the sea: a dark blue textured table with faint depth bands
    sea = bpy.data.materials.new("mapsea"); sea.use_nodes = True
    N = sea.node_tree.nodes; Lk = sea.node_tree.links; p = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord"); nz = N.new("ShaderNodeTexNoise"); nz.inputs['Scale'].default_value = 0.6; nz.inputs['Detail'].default_value = 10
    Lk.new(tc.outputs['Object'], nz.inputs['Vector'])
    rp = N.new("ShaderNodeValToRGB"); rp.color_ramp.elements[0].color = (0.006, 0.03, 0.07, 1); rp.color_ramp.elements[1].color = (0.02, 0.08, 0.16, 1)
    Lk.new(nz.outputs['Fac'], rp.inputs['Fac']); Lk.new(rp.outputs['Color'], p.inputs['Base Color'])
    p.inputs['Roughness'].default_value = 0.35
    ship.box("mapsea", (0, 0, -0.05), (80, 60, 0.1), sea)
    # grid of meridians/parallels as fine raised lines (old chart)
    gl = E.emission_mat("grid", (0.5, 0.6, 0.7), 0.25)
    for lon in range(-35, 0, 5):
        a = geo(lon, BOX[2] - 3, 0.005); b = geo(lon, BOX[3] + 3, 0.005)
        ship.cyl("meridian", a, b, 0.006, mat=gl, verts=6)
    for lat in range(25, 50, 5):
        a = geo(BOX[0] - 5, lat, 0.005); b = geo(BOX[1] + 5, lat, 0.005)
        ship.cyl("parallel", a, b, 0.006, mat=gl, verts=6)
    wd = bpy.data.worlds.new("W"); bpy.context.scene.world = wd; wd.use_nodes = True
    wd.node_tree.nodes["Background"].inputs[0].default_value = (0.05, 0.06, 0.08, 1)
    wd.node_tree.nodes["Background"].inputs[1].default_value = 0.4
    E.area("mapkey", geo(-26, 30, 18), geo(-18, 38, 0), 9000, size=16, color=(1.0, 0.86, 0.7))
    E.area("mapfill", geo(-8, 46, 10), geo(-18, 38, 0), 1500, size=12, color=(0.7, 0.8, 1.0))


def hex_marker(name, lon, lat, color=RED, r=0.38, h=0.12):
    c = geo(lon, lat, 0.12)
    V = []; F = []
    for k in range(6):
        a = math.radians(30 + 60 * k)
        V += [(c.x + r * math.cos(a), c.y + r * math.sin(a), c.z), (c.x + r * math.cos(a), c.y + r * math.sin(a), c.z + h)]
    for k in range(6):
        a, b = 2 * k, 2 * ((k + 1) % 6)
        F.append([a, b, b + 1, a + 1])
    F.append([2 * k + 1 for k in range(6)]); F.append([2 * k for k in range(6)][::-1])
    o = ship.mesh_obj(name, V, F, E.emission_mat(name + "_m", color, 3.0), smooth=False)
    return o


def ripple_bands(name, lon, lat, radii=((0.5, 0.75), (0.95, 1.15)), color=ORANGE, strength=1.6):
    """Filled soft orange bands round a point (the house 'ripple': filled, soft-edged, never thin lines)."""
    c = geo(lon, lat, 0.03); out = []
    for k, (r0, r1) in enumerate(radii):
        n = 64; V = []; F = []
        for i in range(n):
            a = 2 * math.pi * i / n
            V += [(c.x + r0 * math.cos(a), c.y + r0 * math.sin(a), c.z), (c.x + r1 * math.cos(a), c.y + r1 * math.sin(a), c.z)]
        for i in range(n):
            a, b = 2 * i, 2 * ((i + 1) % n)
            F.append([a, b, b + 1, a + 1])
        m = bpy.data.materials.new(f"{name}{k}_m"); m.use_nodes = True; N = m.node_tree.nodes; Lk = m.node_tree.links
        N.remove(N["Principled BSDF"])
        em = N.new("ShaderNodeEmission"); em.inputs['Color'].default_value = (*color, 1); em.inputs['Strength'].default_value = strength
        tr = N.new("ShaderNodeBsdfTransparent")
        tc = N.new("ShaderNodeTexCoord"); gr = N.new("ShaderNodeTexGradient"); gr.gradient_type = 'SPHERICAL'
        s = 1.0 / r1
        mp = N.new("ShaderNodeMapping"); mp.inputs['Location'].default_value = (-c.x * s, -c.y * s, -c.z * s)   # (p - c) / r1
        mp.inputs['Scale'].default_value = (s, s, s)
        Lk.new(tc.outputs['Object'], mp.inputs['Vector']); Lk.new(mp.outputs[0], gr.inputs['Vector'])
        # soft band profile: 0 at the inner and outer edge, 1 in the middle
        mr = N.new("ShaderNodeMapRange"); mr.inputs['From Min'].default_value = 1 - r1 / r1; mr.inputs['From Max'].default_value = 1 - r0 / r1
        Lk.new(gr.outputs['Fac'], mr.inputs['Value'])
        pp = N.new("ShaderNodeMath"); pp.operation = 'PINGPONG'; pp.inputs[1].default_value = 0.5; Lk.new(mr.outputs[0], pp.inputs[0])
        sm = N.new("ShaderNodeMath"); sm.operation = 'MULTIPLY'; sm.inputs[1].default_value = 1.6 * (0.8 - 0.25 * k); Lk.new(pp.outputs[0], sm.inputs[0])
        mx = N.new("ShaderNodeMixShader"); Lk.new(sm.outputs[0], mx.inputs[0])
        Lk.new(tr.outputs[0], mx.inputs[1]); Lk.new(em.outputs[0], mx.inputs[2])
        Lk.new(mx.outputs[0], N["Material Output"].inputs['Surface'])
        o = ship.mesh_obj(f"{name}{k}", V, F, m, smooth=False); o.visible_shadow = False
        out.append(o)
    return out


def dashed_route(name, pts_lonlat, color=ORANGE, dash=0.35, gap=0.22, r=0.05, z=0.15, strength=3.0):
    m = E.emission_mat(name + "_m", color, strength)
    P = [geo(a, b, z) for a, b in pts_lonlat]
    out = []; carry = 0.0; on = True
    for a, b in zip(P[:-1], P[1:]):
        L = (b - a).length; d = (b - a).normalized(); t = 0.0
        while t < L:
            seg = (dash if on else gap) - carry; t1 = min(L, t + seg)
            if on:
                out.append(ship.cyl(name, a + d * t, a + d * t1, r, mat=m, verts=8))
            carry = 0.0 if t + seg <= L else (t1 - t)
            if t + seg <= L:
                on = not on
            t = t1
    return out


def label(name, body, lon, lat, size=0.55, dx=0.0, dy=0.6, color=(0.95, 0.92, 0.86)):
    p = geo(lon, lat, 0.25) + Vector((dx, dy, 0))
    return text3d(name, body, p, size=size, color=color, strength=2.2)


# ============================================================================ the chart table (P4's look, shared)
AZORES_BBOX = (-28.6, 35.6, -15.6, 39.9)          # = mary_celeste_p4 MAP_BBOX, so P1 and P4 maps match
WIDE_BBOX = (-28.6, 33.4, -4.6, 41.6)             # out to Gibraltar
LAST = (-24.98, 37.03)                            # 25 Nov 1872, 8 a.m.: Santa Maria's eastern point SSW, 6 miles (the slate)
FOUND = (-17.25, 38.33)                           # 4 Dec 1872 (sea time): where the Dei Gratia found her
GIB = (-5.35, 36.13)
INK = (0.82, 0.76, 0.62)          # cream chart lettering (reads on the dark painted sea)


def chart_table(bbox=AZORES_BBOX, zoom=8, out_w=1100, SX=2.2):
    """A real 3D relief chart on a chart table under a lamp (mary_celeste_p4 shots/sets.set_table, same recipe):
    terrain + bathymetry from the AWS Terrain Tiles, painted-relief chart material, an oak frame, papers, a lamp.
    Returns dict with mp(lon, lat, lift) -> world point on the chart surface."""
    import terrain as T, ph
    E.render_setup(samples=64)
    out = {}
    tbl = ship.wood("wood_table_large", 0.7, tint=(0.85, 0.6, 0.42), name="chart_table")
    ship.box("tabletop", (0, 0, 0.75), (3.2, 1.9, 0.06), tbl, bevel=0.01)
    for sx in (-1.45, 1.45):
        for sy in (-0.8, 0.8):
            ship.box("leg", (sx, sy, 0.36), (0.09, 0.09, 0.72), tbl)
    TZ = 0.78
    e, lons, lats = T.grid(*bbox, zoom=zoom, out_w=out_w)
    SY = SX * e.shape[0] / e.shape[1]
    base = ship.wood("oak_veneer_01", 0.5, tint=(0.8, 0.6, 0.42), name="mapbase")
    ship.box("map_frame", (0, 0.1, TZ + 0.012), (SX + 0.08, SY + 0.08, 0.024), base, bevel=0.004)
    mo = T.relief_mesh("map", e, SX, SY, land_k=3.0e-5, sea_k=2.6e-6, mat=T.map_material(), skirt=0.0)
    MZ = TZ + 0.024 + 6200 * 2.6e-6 + 0.001
    mo.location = (0, 0.1, MZ)

    def mp(lon, lat, lift=0.0):
        x, y = T.lonlat_to_map(lon, lat, bbox, (SX, SY))
        h = T.height_at(e, lons, lats, lon, lat)
        return Vector((x, y + 0.1, MZ + (h * 2.6e-6 if h < 0 else h * 3.0e-5) + lift))
    out.update(mp=mp, SX=SX, SY=SY, TZ=TZ, MZ=MZ, bbox=bbox)
    pap = E.principled("paper", (0.78, 0.68, 0.5), rough=0.8)
    import random
    rng = random.Random(2)
    for k in range(5):
        ship.box("paper", (1.32 + rng.uniform(-0.05, 0.05), -0.62 + rng.uniform(-0.05, 0.05), TZ + 0.002 + k * 0.0015),
                 (0.21, 0.297, 0.001), pap, rot=(0, 0, rng.uniform(-0.3, 0.3)))
    lamp, lms = ph.model("vintage_oil_lamp"); lamp.location = (1.35, 0.7, TZ)
    E.point("lampflame", (1.35, 0.7, TZ + 0.42), 22, (1.0, 0.6, 0.3))
    k = bpy.data.lights.new("key", 'SPOT'); k.energy = 420; k.color = (1.0, 0.74, 0.48); k.shadow_soft_size = 0.25
    k.spot_size = math.radians(60); k.spot_blend = 0.7
    ko = bpy.data.objects.new("key", k); bpy.context.scene.collection.objects.link(ko); ko.location = (0.6, 0.4, 2.6)
    ko.rotation_euler = (Vector((-0.1, 0.05, TZ)) - ko.location).to_track_quat('-Z', 'Y').to_euler()
    E.area("rim", (-1.8, 1.8, 1.4), (0, 0, TZ), 80, size=1.5, color=(0.9, 0.7, 0.5))
    w = bpy.data.worlds.new("W"); bpy.context.scene.world = w; w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[0].default_value = (0.008, 0.005, 0.004, 1)
    walls = ship.wood("dark_wooden_planks", 1.2, tint=(0.6, 0.42, 0.3), name="room")
    ship.box("wall_back", (0, 2.6, 1.6), (8, 0.1, 3.2), walls)
    ship.box("floor_room", (0, 0, -0.01), (8, 8, 0.02), walls)
    return out


def pin(ch, name, lon, lat, head=(0.55, 0.04, 0.02), scale=1.6):
    """A brass chart pin with a red glass head, pushed into the chart."""
    p = ch["mp"](lon, lat)
    brass = E.principled("pinbrass", (0.72, 0.5, 0.22), rough=0.25, metal=1.0)
    red = E.principled("pinhead_" + name, head, rough=0.25)
    ship.cyl(f"pin_{name}", p - Vector((0, 0, 0.004)), p + Vector((0, 0, 0.07 * scale)), 0.0016 * scale, mat=brass, verts=10)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.008 * scale, location=p + Vector((0, 0, 0.074 * scale)))
    o = bpy.context.active_object; o.name = f"pinhead_{name}"; o.data.materials.append(red); bpy.ops.object.shade_smooth()
    return p


def chart_bands(ch, name, lon, lat, radii=((0.02, 0.035), (0.05, 0.062)), strength=1.4):
    """The house highlight on the chart: a FILLED soft orange glow, a disc whose fill is strongest in a broad band
    two-thirds of the way out and fades smoothly to nothing at its rim (no line rings). radii: the outer radius used is
    the largest given."""
    R = max(r1 for r0, r1 in radii) * 1.15
    c = ch["mp"](lon, lat, 0.0012)
    nr, na = 40, 96; V = []; F = []; A = []
    for i in range(nr + 1):
        r = R * i / nr; u = r / R
        a_ = 0.38 * (1 - u * u) + 0.55 * math.exp(-((u - 0.66) / 0.17) ** 2)
        a_ *= min(1.0, (1 - u) / 0.18)                      # soft fade at the rim
        for k in range(na):
            t = 2 * math.pi * k / na
            V.append((c.x + r * math.cos(t), c.y + r * math.sin(t), c.z + 0.0004)); A.append(max(0.0, a_))
    for i in range(nr):
        for k in range(na):
            a0 = i * na + k; a1 = i * na + (k + 1) % na
            F.append([a0, a1, a1 + na, a0 + na])
    o = ship.mesh_obj(name, V, F, None, smooth=True)
    ca = o.data.color_attributes.new("a", 'FLOAT_COLOR', 'POINT')
    for i, v in enumerate(A):
        ca.data[i].color = (v, v, v, 1)
    m = bpy.data.materials.new(name + "_m"); m.use_nodes = True; N = m.node_tree.nodes; Lk = m.node_tree.links
    N.remove(N["Principled BSDF"])
    at = N.new("ShaderNodeAttribute"); at.attribute_name = "a"
    em = N.new("ShaderNodeEmission"); em.inputs['Color'].default_value = (*ORANGE, 1); em.inputs['Strength'].default_value = strength
    tr = N.new("ShaderNodeBsdfTransparent"); mx = N.new("ShaderNodeMixShader")
    Lk.new(at.outputs['Fac'], mx.inputs[0]); Lk.new(tr.outputs[0], mx.inputs[1]); Lk.new(em.outputs[0], mx.inputs[2])
    Lk.new(mx.outputs[0], N["Material Output"].inputs['Surface'])
    o.data.materials.append(m); o.visible_shadow = False
    return [o]


def pencil_route(ch, name, pts, dash=0.03, gap=0.018, r=0.0024):
    """The route drawn on the chart in pencil: short graphite dashes lying on the paper."""
    m = E.principled("graphite", (0.06, 0.06, 0.065), rough=0.45, metal=0.3)
    P = [ch["mp"](a, b, 0.0006) for a, b in pts]
    out = []; on = True
    for a, b in zip(P[:-1], P[1:]):
        L = (b - a).length; d = (b - a).normalized(); t = 0.0
        while t < L:
            t1 = min(L, t + (dash if on else gap))
            if on:
                out.append(ship.cyl(name, a + d * t, a + d * t1, r, mat=m, verts=6))
            on = not on; t = t1
    return out


def chart_label(ch, name, body, lon, lat, size=0.022, dx=0.0, dy=0.03, rot=0.0):
    """Lettering printed on the chart (dark ink, lying flat on the paper)."""
    p = ch["mp"](lon, lat, 0.001) + Vector((dx, dy, 0))
    cu = bpy.data.curves.new(name, 'FONT'); cu.body = body; cu.size = size; cu.align_x = 'CENTER'; cu.align_y = 'CENTER'
    cu.font = bpy.data.fonts.load(FONT, check_existing=True)
    o = bpy.data.objects.new(name, cu); bpy.context.scene.collection.objects.link(o)
    o.location = p; o.rotation_euler = (0, 0, rot)
    o.data.materials.append(E.principled(name + "_ink", INK, rough=0.6))
    return o


# ============================================================================ the hold, real cutaway (P4's look)
def hold_cutaway_real(water_ft=3.5):
    """P4's dim cutaway of the hold (p4lib/cutaway.py + barrels.py, copied unchanged): the brigantine sliced fore-aft,
    the port half removed, the cargo of barrels in their tiers, one hold lamp; the bilge water standing 3.5 ft deep,
    following the inside of the hull, dark and glossy. No graphics: the caption carries the number."""
    import sys as _s, os as _o
    p4dir = _o.path.join(E.P1, "p4lib")
    if p4dir not in _s.path:
        _s.path.insert(0, p4dir)
    import p4, cutaway as CX, barrels as BR
    E.render_setup(samples=96)
    s = CX.build("MCX", y_cut=0.02)
    res = BR.stow(ymax=0.02, red_slots=CX.RED_SLOTS if hasattr(CX, "RED_SLOTS") else None)
    p4.world_color((0.03, 0.017, 0.011), 1.0)
    floor = p4.mat("void_floor", (0.04, 0.025, 0.017), rough=0.6)
    ship.box("ground", (0, 0, -3.25), (200, 200, 0.02), floor)
    p4.light('AREA', "key", 5000, (1.0, 0.76, 0.52), loc=(8, 15, 11), target=(0, -1, -0.5), size=9)
    p4.light('AREA', "fill", 700, (0.55, 0.6, 0.75), loc=(-12, 12, 2), target=(0, 0, 0), size=10)
    p4.light('AREA', "rim", 2000, (1.0, 0.7, 0.45), loc=(-16, -8, 9), target=(0, 0, 0), size=6)
    p4.light('POINT', "holdlamp", 60, (1.0, 0.6, 0.28), loc=(-1.2, -0.6, 0.9), size=0.04)
    keel_in = -ship.DRAFT + 0.25
    w = hold_water(keel_in + water_ft * 0.3048, inset=0.28, name="bilgewater")
    w.data.materials.clear(); w.data.materials.append(p4.mat("bilge", (0.06, 0.1, 0.085), rough=0.03))
    p4.light('POINT', "bilge_glint", 40, (1.0, 0.6, 0.28), loc=(0.8, -1.0, keel_in + water_ft * 0.3048 + 0.5), size=0.04)
    CX._bisect(w, 0.02)
    return dict(ship=s, barrels=res, ztop=keel_in + water_ft * 0.3048)
