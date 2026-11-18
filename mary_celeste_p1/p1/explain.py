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
    em = N.new("ShaderNodeEmission"); em.inputs['Color'].default_value = (*edge, 1); em.inputs['Strength'].default_value = 1.6
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
    m = E.principled("holdwater", (0.04, 0.3, 0.75), rough=0.08, **{"Emission Color": (0.03, 0.25, 0.75, 1), "Emission Strength": 1.4})
    o = ship.mesh_obj(name, V, F, m, smooth=True)
    return o


def hold_cutaway(water_ft=3.5):
    E.render_setup(samples=96)
    mc = ship.build("MCx", sails="found", rail_gap=None, detail=False, wet=0.2)
    g = ghost_mat("xray", edge=(1.0, 0.62, 0.3), body=(0.5, 0.6, 0.7), alpha=0.03)
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
