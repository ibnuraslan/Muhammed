"""Cladh Hallan excavation, 2001: what is in and around the open area.

  houses(T)               stone revetment rings of the three conjoined roundhouses, shared walls, east entrances,
                          central hearths (stone kerbs, burnt red sand), storage pits
  burial(T, "B1", ...)    a crouched skeleton laid in its grave pit (bones.Skeleton), settled into the fill
  kit(T, people=True)     spoil heap, black rubber buckets, wheelbarrows, trowels, ranging poles, string lines,
                          sieve on a trestle, kneeling pads, finds trays, planks, a site marquee
  digger(kind, ...)       archaeologists (MakeHuman, procedural 2001 fieldwear): kneeling with a trowel, standing
Every person is placed on the real ground height (uist.surface), kneelers rest their weight on the floor.
"""
import math, os, random
import numpy as np
import bpy, bmesh
from mathutils import Vector, Matrix
import uist as U
import ph, sf


def H(x, y):
    return float(U.surface(x, y))


# ----------------------------------------------------------------------------- materials
_M = {}


def mat(name):
    if name in _M:
        return _M[name]
    if name == "gneiss":                      # Hebridean grey banded stone
        m = ph.texture("rock_surface", scale=2.5, name="gneiss", tint=(1.25, 1.2, 1.12))
    elif name == "sand":
        m = ph.texture("dense_sand", scale=0.7, name="spoil", tint=(1.18, 1.1, 0.95))
    elif name == "burnt":
        m = ph.texture("brown_mud_dry", scale=1.2, name="burnt", tint=(0.9, 0.45, 0.28))
    elif name == "fill":                      # grave fill: darker, damp, slightly humic sand, trowelled
        m = ph.texture("dense_sand", scale=1.4, name="fill", tint=(0.82, 0.72, 0.56))
    elif name == "skirt":                     # trowelled pit edge between the scanned grave and the trench floor
        m = ph.texture("dense_sand", scale=0.9, name="skirt", tint=(0.78, 0.7, 0.55))
    elif name == "gravefloor":
        m = ph.texture("dense_sand", scale=1.6, name="gravefloor", tint=(0.86, 0.8, 0.68))
    elif name == "rubber":
        m = bpy.data.materials.new("rubber"); m.use_nodes = True; p = m.node_tree.nodes["Principled BSDF"]
        p.inputs['Base Color'].default_value = (0.012, 0.012, 0.012, 1); p.inputs['Roughness'].default_value = 0.55
    elif name == "plank":
        m = ph.texture("weathered_planks", scale=1.0, name="plank")
    elif name == "canvas":
        m = bpy.data.materials.new("canvas"); m.use_nodes = True; p = m.node_tree.nodes["Principled BSDF"]
        p.inputs['Base Color'].default_value = (0.78, 0.77, 0.72, 1); p.inputs['Roughness'].default_value = 0.85
        p.inputs['Subsurface Weight'].default_value = 0.15; p.inputs['Subsurface Radius'].default_value = (0.3, 0.3, 0.3); p.inputs['Subsurface Scale'].default_value = 0.01
        p.inputs['Sheen Weight'].default_value = 0.3
        p.inputs['Transmission Weight'].default_value = 0.0
    elif name == "pole_red":
        m = bpy.data.materials.new("pole"); m.use_nodes = True; nt = m.node_tree; N = nt.nodes; L = nt.links
        p = N["Principled BSDF"]; tc = N.new("ShaderNodeTexCoord"); sp = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs['Object'], sp.inputs[0])
        mm = N.new("ShaderNodeMath"); mm.operation = 'MULTIPLY'; mm.inputs[1].default_value = 2.0; L.new(sp.outputs['Z'], mm.inputs[0])
        fr = N.new("ShaderNodeMath"); fr.operation = 'FRACT'; L.new(mm.outputs[0], fr.inputs[0])
        st = N.new("ShaderNodeMath"); st.operation = 'GREATER_THAN'; st.inputs[1].default_value = 0.5; L.new(fr.outputs[0], st.inputs[0])
        mx = N.new("ShaderNodeMix"); mx.data_type = 'RGBA'; L.new(st.outputs[0], mx.inputs['Factor'])
        mx.inputs[6].default_value = (0.5, 0.02, 0.015, 1); mx.inputs[7].default_value = (0.75, 0.74, 0.7, 1)
        L.new(mx.outputs[2], p.inputs['Base Color']); p.inputs['Roughness'].default_value = 0.5
    elif name == "rope":
        m = bpy.data.materials.new("rope"); m.use_nodes = True; p = m.node_tree.nodes["Principled BSDF"]
        p.inputs['Base Color'].default_value = (0.7, 0.66, 0.55, 1); p.inputs['Roughness'].default_value = 0.8
    elif name == "string":
        m = bpy.data.materials.new("string"); m.use_nodes = True; p = m.node_tree.nodes["Principled BSDF"]
        p.inputs['Base Color'].default_value = (0.55, 0.42, 0.05, 1); p.inputs['Roughness'].default_value = 0.6
    elif name == "steel":
        m = bpy.data.materials.new("steel"); m.use_nodes = True; p = m.node_tree.nodes["Principled BSDF"]
        p.inputs['Base Color'].default_value = (0.35, 0.33, 0.3, 1); p.inputs['Metallic'].default_value = 1.0; p.inputs['Roughness'].default_value = 0.45
    elif name == "tray":
        m = bpy.data.materials.new("tray"); m.use_nodes = True; p = m.node_tree.nodes["Principled BSDF"]
        p.inputs['Base Color'].default_value = (0.5, 0.52, 0.5, 1); p.inputs['Roughness'].default_value = 0.4
    elif name == "pad":
        m = bpy.data.materials.new("pad"); m.use_nodes = True; p = m.node_tree.nodes["Principled BSDF"]
        p.inputs['Base Color'].default_value = (0.03, 0.08, 0.14, 1); p.inputs['Roughness'].default_value = 0.7
    _M[name] = m
    return m


def link(o):
    if not o.users_collection:
        bpy.context.scene.collection.objects.link(o)
    return o


# ----------------------------------------------------------------------------- stones
_STONE_MESHES = []


def _stone_mesh(seed, flat=0.55):
    rng = np.random.default_rng(seed)
    bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=3, radius=0.5)
    nz = rng.uniform(0, 100, 3)
    for v in bm.verts:
        p = v.co
        d = 1 + 0.18 * math.sin(p.x * 5.3 + nz[0]) * math.cos(p.y * 4.1 + nz[1]) + 0.1 * math.sin(p.z * 7 + nz[2])
        v.co = Vector((p.x * d * rng.uniform(0.9, 1.25), p.y * d, p.z * d * flat))
    me = bpy.data.meshes.new(f"stone{seed}"); bm.to_mesh(me); bm.free()
    for poly in me.polygons:
        poly.use_smooth = True
    me.materials.append(mat("gneiss"))
    return me


def stone(loc, size, rot_z=0.0, seed=None, flat=0.55, tilt=(0, 0)):
    global _STONE_MESHES
    if not _STONE_MESHES:
        _STONE_MESHES = [_stone_mesh(s, f) for s, f in zip(range(10), (0.6, 0.75, 0.55, 0.8, 0.65, 0.6, 0.78, 0.55, 0.7, 0.62))]
    me = _STONE_MESHES[(seed if seed is not None else random.randrange(1000)) % len(_STONE_MESHES)]
    o = bpy.data.objects.new("stone", me); link(o)
    o.location = loc; o.rotation_euler = (tilt[0], tilt[1], rot_z)
    o.scale = size if isinstance(size, (tuple, list)) else (size, size * 0.7, size)
    return o


def houses(T=None, courses=4, seed=4):
    """Stone-faced revetment walls of the sunken roundhouses (shared walls where rings meet), east entrances."""
    rng = random.Random(seed)
    out = []
    for i, (hx, hy, r) in enumerate(U.HOUSES):
        n = int(2 * math.pi * r / 0.5)
        for k in range(n):
            a = 2 * math.pi * k / n
            deg = math.degrees(a) % 360
            if deg < 14 or deg > 346:                     # east entrance gap (paved threshold below)
                continue
            px, py = hx + (r + 0.05) * math.cos(a), hy + (r + 0.05) * math.sin(a)
            # skip stones inside a neighbouring house (the shared wall belongs to one ring only)
            if any(j != i and math.hypot(px - x2, py - y2) < r2 - 0.1 for j, (x2, y2, r2) in enumerate(U.HOUSES)):
                continue
            zf = H(px - 0.25 * math.cos(a), py - 0.25 * math.sin(a))      # house floor just inside
            for c in range(courses):
                s = rng.uniform(0.38, 0.55)
                z = zf + 0.08 + c * 0.14 + rng.uniform(-0.015, 0.015)
                out.append(stone((px + rng.uniform(-0.03, 0.03), py + rng.uniform(-0.03, 0.03), z),
                                 (s, s * 0.6, s * 0.36), rot_z=a + math.pi / 2 + rng.uniform(-0.2, 0.2), seed=rng.randrange(10),
                                 tilt=(rng.uniform(-0.08, 0.08), rng.uniform(-0.12, 0.12))))
        # threshold slabs at the east entrance
        for k in range(3):
            ex = hx + r - 0.2 + k * 0.35
            out.append(stone((ex, hy + rng.uniform(-0.1, 0.1), H(ex, hy) + 0.02), (0.42, 0.35, 0.06), rot_z=rng.uniform(0, 3), seed=k, flat=0.3))
        # central hearth: kerb of upright slabs round a rectangle of burnt red sand
        out += hearth(hx + 0.4, hy, rng)
    return out


def hearth(cx, cy, rng):
    z = H(cx, cy)
    bpy.ops.mesh.primitive_plane_add(size=1, location=(cx, cy, z + 0.012)); b = bpy.context.active_object
    b.scale = (0.95, 0.75, 1); b.name = "hearth_ash"; b.data.materials.append(mat("burnt"))
    sub = b.modifiers.new("sub", "SUBSURF"); sub.levels = 3; sub.render_levels = 3; sub.subdivision_type = 'SIMPLE'
    d = b.modifiers.new("d", "DISPLACE"); t = bpy.data.textures.new("ash", "CLOUDS"); t.noise_scale = 0.15; d.texture = t; d.strength = 0.02
    out = [b]
    for k in range(10):
        a = 2 * math.pi * k / 10
        px, py = cx + 0.55 * math.cos(a), cy + 0.42 * math.sin(a)
        out.append(stone((px, py, H(px, py) + 0.05), (0.26, 0.08, 0.16), rot_z=a + math.pi / 2, seed=k, flat=0.9,
                         tilt=(rng.uniform(-0.1, 0.1), 0)))
    return out


# ----------------------------------------------------------------------------- burials
def burial(key="B1", sex="M", tone="A", heading=None, side="R", arms="face", knee_missing=False, swap=None):
    """Crouched skeleton in its pit. swap = {"skull": Skeleton, "pelvis": Skeleton ...} to build a composite."""
    import bones as B
    px, py, a, b, dep, ang = U.PITS[key]
    sk = B.Skeleton(sex, tone, name=key, sand=0.85).pose_crouched(side=side, arms=arms)
    if knee_missing:
        sk.remove("patellaL")
    sk.place((px, py, H(px, py)), heading=heading if heading is not None else ang + 180, sink=0.01, ground_fn=H)
    sk.fill = grave_fill(sk, key)
    return sk


def grave_fill(sk, key, cell=0.008, embed=0.42, margin=0.05):
    """Sand left round the bones as an excavator pedestals them: a surface that hugs each bone up to `embed` of its
    thickness, falling away to the pit floor between bones. Built from a height raster of the posed skeleton."""
    px, py, a, b, dep, ang = U.PITS[key]
    pts = []
    for o in sk.parts.values():
        M = np.array(o.matrix_world)
        co = np.empty(len(o.data.vertices) * 3, np.float32); o.data.vertices.foreach_get("co", co)
        pts.append(co.reshape(-1, 3) @ M[:3, :3].T + M[:3, 3])
    P = np.concatenate(pts)
    from mathutils.bvhtree import BVHTree
    dg = bpy.context.evaluated_depsgraph_get()
    trees = [BVHTree.FromObject(o, dg) for o in sk.parts.values()]
    lo = P[:, :2].min(0) - 0.18; hi = P[:, :2].max(0) + 0.18
    nx = int((hi[0] - lo[0]) / cell) + 1; ny = int((hi[1] - lo[1]) / cell) + 1
    xs = lo[0] + np.arange(nx) * cell; ys = lo[1] + np.arange(ny) * cell
    X, Y = np.meshgrid(xs, ys)
    G0 = U.surface(X, Y)                               # pit floor and sides
    ztop = P[:, 2].max() + 0.1; zbot = P[:, 2].min() - 0.1
    Zb = np.full((ny, nx), np.nan)
    down = Vector((0, 0, -1)); up = Vector((0, 0, 1))
    for j in range(ny):
        for i in range(nx):
            t = None; bt = None
            for tr in trees:
                h = tr.ray_cast(Vector((xs[i], ys[j], ztop)), down)
                if h[0] is not None and (t is None or h[0].z > t):
                    t = h[0].z
                    hb = tr.ray_cast(Vector((xs[i], ys[j], zbot)), up)
                    bt = hb[0].z if hb[0] is not None else t
            if t is not None:
                Zb[j, i] = bt + embed * (t - bt)
    has = ~np.isnan(Zb)
    Z = np.where(has, Zb, G0)
    # sand ramps away from every bone at ~40 degrees down to the pit floor (pedestalled, as excavated)
    from numpy.lib.stride_tricks import sliding_window_view as sw
    R = Z.copy()
    for _ in range(int(0.09 / cell)):
        pad = np.pad(R, 1, mode='edge'); mx = sw(pad, (3, 3)).max(axis=(-1, -2)) - cell * 0.85
        R = np.where(has, Z, np.maximum(G0, np.minimum(mx, np.maximum(R, mx))))
    pad = np.pad(R, 2, mode='edge'); R = np.where(has, R, sw(pad, (5, 5)).mean(axis=(-1, -2)))
    Z = np.maximum(R, G0 + 0.003)
    # only inside the pit (ellipse), blended to the original surface at its edge
    c, s_ = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    u = ((X - px) * c + (Y - py) * s_) / a; v = (-(X - px) * s_ + (Y - py) * c) / b
    e = np.hypot(u, v); w = 1 - U._smooth(0.75, 1.0, e)
    Z = G0 + (Z - G0) * w + 0.002
    V = np.stack([X, Y, Z], -1).reshape(-1, 3)
    idx = np.arange(nx * ny).reshape(ny, nx)
    F = np.stack([idx[:-1, :-1].ravel(), idx[:-1, 1:].ravel(), idx[1:, 1:].ravel(), idx[1:, :-1].ravel()], -1)
    F = F[(e[:-1, :-1].ravel() < 1.0)]                  # keep the fill inside the pit only (no visible patch edge)
    me = bpy.data.meshes.new("fill_" + key)
    me.vertices.add(len(V)); me.vertices.foreach_set("co", V.astype(np.float32).ravel())
    me.loops.add(len(F) * 4); me.loops.foreach_set("vertex_index", F.astype(np.int32).ravel())
    me.polygons.add(len(F)); me.polygons.foreach_set("loop_start", np.arange(0, len(F) * 4, 4, dtype=np.int32))
    me.polygons.foreach_set("use_smooth", np.ones(len(F), bool)); me.update(calc_edges=True)
    me.materials.append(mat("fill"))
    o = bpy.data.objects.new("fill_" + key, me); link(o)
    return o


# ----------------------------------------------------------------------------- kit
def _lathe(name, prof, segs=40, mat_name="rubber", loc=(0, 0, 0)):
    bm = bmesh.new(); rings = []
    for r, z in prof:
        ring = [bm.verts.new((r * math.cos(2 * math.pi * k / segs), r * math.sin(2 * math.pi * k / segs), z)) for k in range(segs)]
        rings.append(ring)
    for r0, r1 in zip(rings, rings[1:]):
        for k in range(segs):
            bm.faces.new((r0[k], r0[(k + 1) % segs], r1[(k + 1) % segs], r1[k]))
    bm.faces.new(rings[0][::-1])
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for p in me.polygons:
        p.use_smooth = True
    me.materials.append(mat(mat_name))
    o = bpy.data.objects.new(name, me); link(o); o.location = loc
    return o


def bucket(x, y, full=True, rot=0.0):
    """Black rubber 'tubby' (the archaeologist's bucket), with two rope handles, full of sand."""
    z = H(x, y)
    o = _lathe("tubby", [(0.13, 0), (0.15, 0.01), (0.17, 0.28), (0.185, 0.3), (0.18, 0.31), (0.165, 0.29), (0.15, 0.03), (0.0, 0.03)],
               loc=(x, y, z))
    o.rotation_euler.z = rot
    if full:
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.16, location=(x, y, z + 0.27)); s = bpy.context.active_object
        s.scale = (1, 1, 0.28); s.data.materials.append(mat("sand")); s.name = "tubby_sand"
    return o


def ranging_pole(x, y, h=2.0, lean=(0, 0)):
    z = H(x, y)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.013, depth=h, location=(x, y, z + h / 2 - 0.15)); o = bpy.context.active_object
    o.rotation_euler = (lean[0], lean[1], 0); o.data.materials.append(mat("pole_red")); o.name = "ranging_pole"
    return o


def peg(x, y, z=None):
    z = H(x, y) if z is None else z
    bpy.ops.mesh.primitive_cube_add(size=1, location=(x, y, z + 0.08)); o = bpy.context.active_object
    o.scale = (0.025, 0.025, 0.2); o.data.materials.append(mat("plank")); o.name = "peg"
    return o


def string_line(p0, p1, sag=0.01):
    v = Vector(p1) - Vector(p0); n = 16
    pts = [Vector(p0) + v * (k / n) - Vector((0, 0, sag * 4 * (k / n) * (1 - k / n))) for k in range(n + 1)]
    cu = bpy.data.curves.new("string", 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = 0.0012
    sp = cu.splines.new('POLY'); sp.points.add(len(pts) - 1)
    for i, p in enumerate(pts):
        sp.points[i].co = (*p, 1)
    o = bpy.data.objects.new("string", cu); link(o); cu.materials.append(mat("string"))
    return o


def plank(x, y, z, length=2.4, rot=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=(x, y, z + 0.025)); o = bpy.context.active_object
    o.scale = (length, 0.22, 0.05); o.rotation_euler.z = rot; o.data.materials.append(mat("plank")); o.name = "plank"
    return o


def trowel(loc, rot=(0, 0, 0)):
    root, ms = sf.model("46c6a91c78d1451bb3f9081543c31144", loc=loc, rot_z=0)
    root.rotation_euler = rot
    s = 0.24 / 0.24; root.scale = (s, s, s)
    for o in root.children_recursive:
        o.name = "trowel"
    return root


def wheelbarrow(x, y, rot=0.0):
    root, ms = sf.model("2be2971dbfa742c292bfff11451d5bb8", loc=(x, y, H(x, y)), rot_z=rot, height=0.62)
    for o in ms:
        o.name = "wheelbarrow"
    return root


def spoil_heap(cx, cy, sx=7.0, sy=5.0, h=1.9):
    n = 64
    xs = np.linspace(-1, 1, n); X, Y = np.meshgrid(xs, xs)
    r = np.hypot(X, Y)
    Z = h * np.clip(1 - r ** 1.6, 0, 1) ** 0.8 * (1 + 0.08 * U.fbm(X * 4, Y * 4, 3, seed=55))
    V = []
    for j in range(n):
        for i in range(n):
            wx, wy = cx + X[j, i] * sx, cy + Y[j, i] * sy
            V.append((wx, wy, H(wx, wy) + max(Z[j, i], 0) - 0.05))
    F = [(j * n + i, j * n + i + 1, (j + 1) * n + i + 1, (j + 1) * n + i) for j in range(n - 1) for i in range(n - 1)]
    me = bpy.data.meshes.new("spoil"); me.from_pydata(V, [], F); me.update()
    for p in me.polygons:
        p.use_smooth = True
    me.materials.append(mat("sand"))
    o = bpy.data.objects.new("spoil", me); link(o)
    return o


def sieve(x, y, rot=0.0):
    z = H(x, y); parts = []
    for dx in (-0.45, 0.45):
        for dy in (-0.3, 0.3):
            bpy.ops.mesh.primitive_cube_add(size=1, location=(x + dx, y + dy, z + 0.4)); o = bpy.context.active_object
            o.scale = (0.04, 0.04, 0.8); o.data.materials.append(mat("plank")); parts.append(o)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(x, y, z + 0.82)); fr = bpy.context.active_object
    fr.scale = (1.0, 0.7, 0.08); fr.data.materials.append(mat("plank")); parts.append(fr)
    sol = fr.modifiers.new("hollow", "SOLIDIFY")
    bpy.ops.mesh.primitive_plane_add(size=1, location=(x, y, z + 0.8)); mesh = bpy.context.active_object
    mesh.scale = (0.95, 0.65, 1); mesh.data.materials.append(mat("steel")); parts.append(mesh)
    for o in parts:
        o.name = "sieve"
    return parts


def _guy(p0, p1, sag=0.03, r=0.004, m=None):
    """A guy rope from p0 (tent) to p1 (peg) with a slight sag, and the peg."""
    v = Vector(p1) - Vector(p0); n = 10
    pts = [Vector(p0) + v * (k / n) - Vector((0, 0, sag * 4 * (k / n) * (1 - k / n))) for k in range(n + 1)]
    cu = bpy.data.curves.new("guy", 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = r
    sp = cu.splines.new('POLY'); sp.points.add(len(pts) - 1)
    for i, p in enumerate(pts):
        sp.points[i].co = (*p, 1)
    o = bpy.data.objects.new("guyrope", cu); link(o); cu.materials.append(m or mat("rope"))
    peg(p1[0], p1[1], z=p1[2] - 0.05)
    return o


def marquee(cx, cy, w=6.0, d=4.2, h=2.1, ridge=3.1, rot=0.0):
    """White canvas frame marquee: four walls (front rolled up), pitched roof, sagging canvas, guy ropes to pegs."""
    z = H(cx, cy)
    R = Matrix.Rotation(rot, 4, 'Z')
    def W(p):
        return Matrix.Translation((cx, cy, z)) @ R @ Vector(p)
    V = [(-w / 2, -d / 2, 0), (w / 2, -d / 2, 0), (w / 2, d / 2, 0), (-w / 2, d / 2, 0),
         (-w / 2, -d / 2, h), (w / 2, -d / 2, h), (w / 2, d / 2, h), (-w / 2, d / 2, h), (-w / 2, 0, ridge), (w / 2, 0, ridge)]
    F = [(3, 7, 6, 2), (4, 5, 9, 8), (7, 8, 9, 6), (0, 4, 8, 7, 3), (1, 2, 6, 9, 5)]   # front (south) wall open
    me = bpy.data.meshes.new("marquee"); me.from_pydata(V, [], F); me.update()
    me.materials.append(mat("canvas"))
    o = bpy.data.objects.new("marquee", me); link(o)
    o.location = (cx, cy, z); o.rotation_euler.z = rot
    sub = o.modifiers.new("sub", "SUBSURF"); sub.subdivision_type = 'SIMPLE'; sub.levels = 5; sub.render_levels = 5
    dsp = o.modifiers.new("sag", "DISPLACE"); t = bpy.data.textures.new("canvas", "CLOUDS"); t.noise_scale = 0.6
    dsp.texture = t; dsp.strength = 0.05
    sol = o.modifiers.new("th", "SOLIDIFY"); sol.thickness = 0.004
    # front wall rolled up under the eave; poles at the corners and the open front
    bpy.ops.mesh.primitive_cylinder_add(radius=0.09, depth=w, location=W((0, -d / 2, h - 0.08))); rl = bpy.context.active_object
    rl.rotation_euler = (0, math.pi / 2, rot); rl.data.materials.append(mat("canvas")); rl.name = "rolledwall"
    for px in (-w / 2, -w / 6, w / 6, w / 2):
        bpy.ops.mesh.primitive_cylinder_add(radius=0.025, depth=h, location=W((px, -d / 2, h / 2))); p = bpy.context.active_object
        p.data.materials.append(mat("steel")); p.name = "tentpole"
    # guy ropes from the eaves, 1.6 m out
    for px in (-w / 2, -w / 6, w / 6, w / 2):
        for sy in (-1, 1):
            e = W((px, sy * d / 2, h)); g = W((px, sy * (d / 2 + 1.6), 0))
            g.z = H(g.x, g.y) + 0.06
            _guy(e, g)
    for sy in (-1, 1):
        for sx in (-1, 1):
            e = W((sx * w / 2, sy * d / 2, h)); g = W((sx * (w / 2 + 1.4), sy * d / 2, 0)); g.z = H(g.x, g.y) + 0.06
            _guy(e, g)
    return o


def site_hut(cx, cy, rot=0.0, w=6.0, d=2.6, h=2.6):
    """Site cabin (portakabin): painted steel box on blocks, windows, door, two steps."""
    z = H(cx, cy) + 0.15
    R = Matrix.Rotation(rot, 4, 'Z')
    def W(p):
        return Matrix.Translation((cx, cy, z)) @ R @ Vector(p)
    body = bpy.data.materials.new("hutpaint"); body.use_nodes = True; bp = body.node_tree.nodes["Principled BSDF"]
    bp.inputs['Base Color'].default_value = (0.14, 0.2, 0.16, 1); bp.inputs['Roughness'].default_value = 0.6
    glass = bpy.data.materials.new("hutglass"); glass.use_nodes = True; gp = glass.node_tree.nodes["Principled BSDF"]
    gp.inputs['Base Color'].default_value = (0.02, 0.025, 0.03, 1); gp.inputs['Roughness'].default_value = 0.05
    bpy.ops.mesh.primitive_cube_add(size=1, location=W((0, 0, h / 2))); b = bpy.context.active_object
    b.scale = (w, d, h); b.rotation_euler.z = rot; b.data.materials.append(body); b.name = "sitehut"
    bv = b.modifiers.new("bev", "BEVEL"); bv.width = 0.03; bv.segments = 2
    # corrugation: wave bump on the walls
    nt = body.node_tree; wv = nt.nodes.new("ShaderNodeTexWave"); wv.inputs['Scale'].default_value = 30
    tc = nt.nodes.new("ShaderNodeTexCoord"); nt.links.new(tc.outputs['Object'], wv.inputs['Vector'])
    bm_ = nt.nodes.new("ShaderNodeBump"); bm_.inputs['Strength'].default_value = 0.3; nt.links.new(wv.outputs['Fac'], bm_.inputs['Height'])
    nt.links.new(bm_.outputs['Normal'], bp.inputs['Normal'])
    for k, px in enumerate((-2.0, -0.7, 1.6)):
        bpy.ops.mesh.primitive_cube_add(size=1, location=W((px, -d / 2 - 0.01, h * 0.62))); wdw = bpy.context.active_object
        wdw.scale = (0.9 if k != 2 else 0.85, 0.02, 0.7 if k != 2 else 1.9); wdw.rotation_euler.z = rot
        if k == 2:
            wdw.location = W((px, -d / 2 - 0.01, 0.98))
        wdw.data.materials.append(glass); wdw.name = "hutwindow"
    for k in range(2):
        bpy.ops.mesh.primitive_cube_add(size=1, location=W((1.6, -d / 2 - 0.25 - 0.25 * k, -0.15 + 0.11 * (1 - k)))); st = bpy.context.active_object
        st.scale = (1.0, 0.28, 0.1); st.rotation_euler.z = rot; st.data.materials.append(mat("plank")); st.name = "hutstep"
    return b


def kit(people=False, seed=3):
    rng = random.Random(seed)
    D = U.DIG
    out = {}
    out["spoil"] = spoil_heap(D["x1"] + 8.5, 1.0, 6.0, 9.0, 2.2)
    out["marquee"] = marquee(-17.0, 22.0, rot=0.35)
    out["hut"] = site_hut(-22.0, 10.0, rot=1.75)
    out["spoil2"] = spoil_heap(-15.0, -20.0, 5.0, 4.0, 1.6)
    # string grid across the north house (planning grid, 1 m squares) on pins at the trench floor
    gx0, gy0 = -4.0, -4.0
    for k in range(10):
        zz = H(gx0 + k, gy0) + 0.15
        string_line((gx0 + k, gy0, H(gx0 + k, gy0) + 0.15), (gx0 + k, gy0 + 9, H(gx0 + k, gy0 + 9) + 0.15), sag=0.005)
    for k in range(10):
        string_line((gx0, gy0 + k, H(gx0, gy0 + k) + 0.15), (gx0 + 9, gy0 + k, H(gx0 + 9, gy0 + k) + 0.15), sag=0.005)
    # string lines along the trench edge, pegs at the corners, a ranging pole at each corner
    zc = H(D["x0"] - 0.5, D["y0"] - 0.5)
    corners = [(D["x0"] - 0.35, D["y0"] - 0.35), (D["x1"] + 0.35, D["y0"] - 0.35), (D["x1"] + 0.35, D["y1"] + 0.35), (D["x0"] - 0.35, D["y1"] + 0.35)]
    for (x0, y0), (x1, y1) in zip(corners, corners[1:] + corners[:1]):
        string_line((x0, y0, H(x0, y0) + 0.12), (x1, y1, H(x1, y1) + 0.12), sag=0.02)
    for x, y in corners:
        peg(x, y)
    for k, (x, y) in enumerate(corners[:3]):
        ranging_pole(x + 0.2, y + 0.2, lean=(rng.uniform(-0.04, 0.04), rng.uniform(-0.04, 0.04)))
    # buckets and barrows on the east lip by the spoil heap; planks bridging into the trench
    for k in range(9):
        x = D["x1"] + 1.2 + rng.uniform(0, 1.5); y = -4 + k * 1.1 + rng.uniform(-0.2, 0.2)
        bucket(x, y, full=rng.random() < 0.7, rot=rng.uniform(0, 6))
    out["barrow1"] = wheelbarrow(D["x1"] + 3.0, -1.5, rot=1.6)
    out["barrow2"] = wheelbarrow(D["x1"] + 2.6, 4.2, rot=1.3)
    plank(D["x1"] + 1.4, 1.0, H(D["x1"] + 2.6, 1.0), length=3.2, rot=0.0)
    out["sieve"] = sieve(D["x1"] + 4.5, -6.0, rot=0.3)
    # buckets and a tray down in the trench near the north house
    for (x, y) in ((2.8, 7.0), (-4.6, 12.6), (3.6, 10.2)):
        bucket(x, y, full=False, rot=rng.uniform(0, 6))
    return out


# ----------------------------------------------------------------------------- people
def lift(st, dz):
    """Move a placed person (and attached props) up by dz after finish()."""
    for o in st.m.objects:
        if o.parent is None:
            o.location.z += dz
    for k, v in list(getattr(st, "attached", ())):
        k.location.z += dz
    bpy.context.view_layer.update()


# ----------------------------------------------------------------------------- photogrammetry graves (real excavated
# crouched burials, Sketchfab CC-BY) set into the north-house pits, joined to the trench floor by a sand skirt
SINK = {"B1": -0.02, "B2": -0.02}                                          # scan surface below the floor; the floor overlaps its edges
PRE = {}
MIRROR = {"B2"}                                                # B2: the same type of grave, mirrored and turned                  # rotate X, then crop (fractions of x, y extent)
STRIP = {}      # scan-unit box (x0, x1, y0, y1, z above which to cut)
SCANS = {
    # key: (uid, scan-unit centre of the body, scale to metres, cut faces with x < cut (scan units), skull (scan units))
    "B1": ("4e02811d415943d39715c131acb387a7", (-0.102, 0.026), 11.0, None, (-0.09, 0.072)),
    "B2": ("4e02811d415943d39715c131acb387a7", (-0.102, 0.026), 10.4, None, (-0.09, 0.072)),
}


def burial_scan(key="B1", rot=None, skirt=0.0):
    import bones as B
    uid, cen, sc, cut, skull = SCANS[key]
    px, py, a, b, dep, ang = U.PITS[key]
    rot = math.radians(ang if rot is None else rot)
    o = B._import(uid); o.name = "grave_" + key
    me = o.data
    pre = PRE.get(key)
    if pre:                      # scans captured standing up (photo slabs): lay flat, then keep only the crop box
        rx, crop = pre
        me.transform(Matrix.Rotation(math.radians(rx), 4, 'X'))
        co0 = np.empty(len(me.vertices) * 3, np.float32); me.vertices.foreach_get("co", co0); co0 = co0.reshape(-1, 3)
        lo, hi = co0.min(0), co0.max(0); ext = hi - lo
        x0 = lo[0] + crop[0] * ext[0]; x1 = lo[0] + crop[1] * ext[0]; y0 = lo[1] + crop[2] * ext[1]; y1 = lo[1] + crop[3] * ext[1]
        bm = bmesh.new(); bm.from_mesh(me)
        bmesh.ops.delete(bm, geom=[f for f in bm.faces if not (x0 < f.calc_center_median().x < x1 and y0 < f.calc_center_median().y < y1)
                                    or max(e.calc_length() for e in f.edges) > 0.012], context="FACES")   # drop stretched edge polygons
        bm.to_mesh(me); bm.free()
    if cut is not None:
        bm = bmesh.new(); bm.from_mesh(me)
        bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.calc_center_median().x < cut], context='FACES')
        bm.to_mesh(me); bm.free()
    strip = STRIP.get(key)
    patch = None
    if strip:                     # grave goods in the source scan (pots) do not belong at Cladh Hallan: cut them out
        x0, x1, y0, y1, zc = strip
        bm = bmesh.new(); bm.from_mesh(me)
        kill = [f for f in bm.faces if x0 < f.calc_center_median().x < x1 and y0 < f.calc_center_median().y < y1
                and f.calc_center_median().z > zc]
        bmesh.ops.delete(bm, geom=kill, context='FACES'); bm.to_mesh(me); bm.free()
        patch = (x0, x1, y0, y1)
    co = np.empty(len(me.vertices) * 3, np.float32); me.vertices.foreach_get("co", co); co = co.reshape(-1, 3)
    if cen is None:
        cen = tuple(((co.min(0) + co.max(0)) / 2)[:2])
    co[:, 0] -= cen[0]; co[:, 1] -= cen[1]; co *= sc
    if key in MIRROR:
        co[:, 0] *= -1
    c, s = math.cos(rot), math.sin(rot)
    x = co[:, 0] * c - co[:, 1] * s; y = co[:, 0] * s + co[:, 1] * c
    floor_z = float(U.surface(px + 2.2 * math.cos(rot + 1.2), py + 2.2 * math.sin(rot + 1.2)))  # house floor beside the pit
    co[:, 0] = x + px; co[:, 1] = y + py
    co[:, 2] += floor_z + SINK.get(key, 0.004) - co[:, 2].max()
    me.vertices.foreach_set("co", co.ravel()); me.update()
    # drop every scan face outside the cut in the trench floor (its outer walls would poke through as pale streaks)
    if key in U.PIT_CUT:
        du, ca, cb = U.PIT_CUT[key]
        cxp, cyp = px + du * c, py + du * s
        bm = bmesh.new(); bm.from_mesh(me)
        kill = []
        for f in bm.faces:
            q = f.calc_center_median()
            uu = ((q.x - cxp) * c + (q.y - cyp) * s) / ca; vv = (-(q.x - cxp) * s + (q.y - cyp) * c) / cb
            e_ = math.hypot(uu, vv)
            if e_ > 0.95 and q.z > floor_z - 0.12:
                kill.append(f)
            elif (e_ > 0.78 and abs(f.normal.z) > 0.7 and q.z > float(U.surface(q.x, q.y)) + 0.005) or \
                    (e_ > 0.88 and q.z > float(U.surface(q.x, q.y)) + 0.01):
                kill.append(f)        # flat scan floor lying over the terrain's pit wall (a pale plate at the rim)
        bmesh.ops.delete(bm, geom=kill, context='FACES'); bm.to_mesh(me); bm.free()
    # warm the scan toward the pale machair shell sand
    for m in me.materials:
        if m and m.use_nodes and "warmed" not in m:
            N = m.node_tree.nodes; Lk = m.node_tree.links; p = [n for n in N if n.type == 'BSDF_PRINCIPLED']
            if p and p[0].inputs['Base Color'].links:
                src = p[0].inputs['Base Color'].links[0].from_socket
                mx = N.new("ShaderNodeMix"); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs['Factor'].default_value = 1.0
                Lk.new(src, mx.inputs[6]); mx.inputs[7].default_value = (1.4, 1.18, 0.86, 1); Lk.new(mx.outputs[2], p[0].inputs['Base Color'])
            m["warmed"] = True
    if patch:                     # floor patch where the pots stood (scan floor level, same sand)
        x0, x1, y0, y1 = patch
        zf = float(np.percentile(co[:, 2], 30))
        corners = [((xx - cen[0]) * sc * (-1 if key in MIRROR else 1), (yy - cen[1]) * sc) for xx, yy in ((x0, y0), (x1, y0), (x1, y1), (x0, y1))]
        V = [(X * c - Y * s + px, X * s + Y * c + py, zf + 0.002) for X, Y in corners]
        pm = bpy.data.meshes.new("gravepatch"); pm.from_pydata(V, [], [(0, 1, 2, 3)]); pm.update(); pm.materials.append(mat("gravefloor"))
        po = bpy.data.objects.new("gravepatch", pm); link(po)
        sub = po.modifiers.new("s", "SUBSURF"); sub.subdivision_type = 'SIMPLE'; sub.levels = 4; sub.render_levels = 4
        dsp = po.modifiers.new("d", "DISPLACE"); t = bpy.data.textures.new("gp", "CLOUDS"); t.noise_scale = 0.05; dsp.texture = t; dsp.strength = 0.012
    # skirt: from every open edge of the scan outward and up to the floor level
    bm = bmesh.new(); bm.from_mesh(me)
    bnd = [e for e in bm.edges if e.is_boundary] if skirt > 0 else []
    rr = lambda v: math.hypot(v.co.x - px, v.co.y - py)
    rmax = max([max(rr(v) for v in e.verts) for e in bnd] or [1.0])
    bnd = [e for e in bnd if min(rr(v) for v in e.verts) > 0.72 * rmax]          # the outer rim only
    outer = {}
    for e in bnd:
        for v in e.verts:
            if v.index not in outer:
                d = Vector((v.co.x - px, v.co.y - py, 0)); d = d.normalized() if d.length > 1e-6 else Vector((1, 0, 0))
                outer[v.index] = bm.verts.new((v.co.x + d.x * skirt, v.co.y + d.y * skirt, floor_z + 0.004))
    bm.verts.ensure_lookup_table()
    sk_faces = []
    for e in bnd:
        v0, v1 = e.verts
        try:
            sk_faces.append(bm.faces.new((v0, v1, outer[v1.index], outer[v0.index])))
        except ValueError:
            pass
    nm = len(me.materials)
    for f in sk_faces:
        f.material_index = nm; f.smooth = False
    bm.to_mesh(me); bm.free()
    me.materials.append(mat("skirt"))
    o["grave"] = key
    def w(pt):
        X = (pt[0] - cen[0]) * sc * (-1 if key in MIRROR else 1); Y = (pt[1] - cen[1]) * sc
        return Vector((X * c - Y * s + px, X * s + Y * c + py, floor_z - 0.25))
    info = dict(obj=o, centre=Vector((px, py, floor_z - 0.3)), floor=floor_z,
                skull=(w(skull) if skull else Vector((px, py, floor_z - 0.3))))
    return info


class Grave:
    """Adapter so shots can ask a scanned grave for centre() / part_centre(seg) like a posed Skeleton."""
    def __init__(self, info):
        self.info = info

    def centre(self):
        return self.info["centre"].copy(), Vector((1.2, 1.0, 0.3))

    def part_centre(self, seg):
        c = self.info["centre"]; k = self.info["skull"]
        if seg in ("skull", "mandible"):
            return k + (Vector((0, 0, -0.03)) if seg == "mandible" else Vector((0, 0, 0)))
        if seg in ("thorax",):
            return c.lerp(k, 0.45)
        if seg.startswith("femur"):
            return c.lerp(k, -0.35)
        return c.copy()

    world_pivot = part_centre


def section_tags(y_face, x0, x1, n=7, seed=8):
    """Nails with blank aluminium tags pushed into the section at the layer boundaries (as on a recorded section)."""
    rng = random.Random(seed)
    al = bpy.data.materials.new("tagalu"); al.use_nodes = True; p = al.node_tree.nodes["Principled BSDF"]
    p.inputs['Base Color'].default_value = (0.75, 0.76, 0.78, 1); p.inputs['Metallic'].default_value = 1.0; p.inputs['Roughness'].default_value = 0.35
    depths = [d for d, _ in U.STRATA if 0.25 < d < 1.5][::2]
    out = []
    for k in range(n):
        x = x0 + (x1 - x0) * (k + 0.5) / n + rng.uniform(-0.2, 0.2)
        dd = depths[k % len(depths)] + rng.uniform(-0.01, 0.01)
        z = U.SITE_Z - dd
        # the face sits at y_face minus the bench offsets: find it by stepping in from the edge
        yy = y_face
        for step in range(200):
            if float(U.surface(x, yy - 0.01 * step)) < z - 0.002:
                yy = yy - 0.01 * step + 0.01; break
        bpy.ops.mesh.primitive_cylinder_add(radius=0.0025, depth=0.09, location=(x, yy - 0.03, z)); nl = bpy.context.active_object
        nl.rotation_euler = (math.pi / 2, 0, 0); nl.data.materials.append(mat("steel")); nl.name = "tagnail"
        bpy.ops.mesh.primitive_cube_add(size=1, location=(x + 0.012, yy - 0.075, z - 0.03)); tg = bpy.context.active_object
        tg.scale = (0.03, 0.003, 0.05); tg.rotation_euler = (rng.uniform(-0.15, 0.15), 0, rng.uniform(-0.2, 0.2)); tg.data.materials.append(al); tg.name = "tag"
        out.append(tg)
    return out


def _face_y(x, z, y_face):
    """y of the section face at (x, depth z): step in from the trench edge until the ground drops below z."""
    for step in range(260):
        yy = y_face - 0.01 * step
        if float(U.surface(x, yy)) < z - 0.002:
            return yy + 0.01
    return y_face - 1.0


def section_dressing(y_face, x0, x1, n_stones=30, n_roots=26, seed=12):
    """Stones bedded in the section face (half proud of it) and fine roots hanging from the turf line."""
    rng = random.Random(seed)
    for k in range(n_stones):
        x = rng.uniform(x0, x1); dd = rng.uniform(0.15, 1.5); z = U.SITE_Z - dd
        yy = _face_y(x, z, y_face)
        s = rng.uniform(0.03, 0.11)
        stone((x, yy - s * 0.15, z), (s, s * rng.uniform(0.6, 0.9), s * rng.uniform(0.5, 0.8)), rot_z=rng.uniform(0, 6), seed=rng.randrange(10),
              tilt=(rng.uniform(-0.5, 0.5), rng.uniform(-0.5, 0.5)))
    root = bpy.data.materials.new("roots"); root.use_nodes = True; p = root.node_tree.nodes["Principled BSDF"]
    p.inputs['Base Color'].default_value = (0.07, 0.05, 0.03, 1); p.inputs['Roughness'].default_value = 0.8
    for k in range(n_roots):
        x = rng.uniform(x0, x1); z0 = U.SITE_Z - 0.04
        yy = _face_y(x, z0 - 0.02, y_face)
        L = rng.uniform(0.08, 0.35); pts = []
        for j in range(9):
            t = j / 8
            pts.append(Vector((x + 0.015 * math.sin(t * 7 + k), yy - 0.006 - 0.02 * t * rng.random(), z0 - L * t)))
        cu = bpy.data.curves.new("root", 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = rng.uniform(0.0008, 0.002)
        sp = cu.splines.new('POLY'); sp.points.add(len(pts) - 1)
        for i, p_ in enumerate(pts):
            sp.points[i].co = (*p_, 1)
        o = bpy.data.objects.new("root", cu); link(o); cu.materials.append(root)


SECTION_SCAN = "ae929d64bedf4568bc68e73894b69394"      # Silchester Baths 2021 Trench 2 Section 1 (UoR-Archaeology, CC-BY)


def section_scan(y_face, x_center=2.6, tint=(1.15, 1.05, 0.88)):
    """A real photogrammetry trench section set in as the lower face of the north section (below the step):
    long axis along x, the recorded face looking south into the trench, top at the step level."""
    import bones as B
    o = B._import(SECTION_SCAN); o.name = "sectionscan"; me = o.data
    co = np.empty(len(me.vertices) * 3, np.float32); me.vertices.foreach_get("co", co); co = co.reshape(-1, 3)
    c0 = co.mean(0); xy = co[:, :2] - c0[:2]
    u, s_, vt = np.linalg.svd(xy, full_matrices=False); ax = vt[0]
    ang = math.atan2(ax[1], ax[0])
    # face direction: area-weighted mean horizontal normal
    nrm = np.zeros(3)
    for p in me.polygons:
        nrm += np.array(p.normal) * p.area
    R = Matrix.Rotation(-ang, 4, 'Z')
    n2 = R.to_3x3() @ Vector((nrm[0], nrm[1], 0))
    flip = Matrix.Rotation(math.pi, 4, 'Z') if n2.y > 0 else Matrix.Identity(4)        # face must look -y
    me.transform(Matrix.Translation(Vector((0, 0, 0))) @ flip @ R @ Matrix.Translation(-Vector(c0.tolist())))
    co = np.empty(len(me.vertices) * 3, np.float32); me.vertices.foreach_get("co", co); co = co.reshape(-1, 3)
    step_z = U.SITE_Z - U.DIG["depth"] * 0.55
    lo, hi = co.min(0), co.max(0)
    # face plane = the front (min-y) 10th percentile of the surface; put it just in front of the terrain's lower face
    yf = float(np.percentile(co[:, 1], 85))            # put (nearly) the whole recorded face in front of the terrain face
    o.location = (x_center - (lo[0] + hi[0]) / 2, y_face - 1.02 - yf, step_z + 0.02 - hi[2])
    for m in me.materials:
        if m and m.use_nodes:
            N = m.node_tree.nodes; Lk = m.node_tree.links; p = [n for n in N if n.type == 'BSDF_PRINCIPLED']
            if p and p[0].inputs['Base Color'].links:
                src = p[0].inputs['Base Color'].links[0].from_socket
                mx = N.new("ShaderNodeMix"); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs['Factor'].default_value = 1.0
                Lk.new(src, mx.inputs[6]); mx.inputs[7].default_value = (*tint, 1); Lk.new(mx.outputs[2], p[0].inputs['Base Color'])
    return o
