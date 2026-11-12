"""Realistic procedural vehicles (CC0, built from scratch) for every documentary in the pipeline.

    import vehicles
    car = vehicles.make("sedan_1990s_soviet", loc=(0, 0, 0), heading_deg=90, color=(0.6, 0.55, 0.42), dirt=0.3)
    vehicles.spin_wheels(car, distance_m)        # roll the wheels for a distance travelled (keyframe it per frame)
    vehicles.lights(car, on=True)                # head/tail lamps on (emissive lenses + optional real spot lights)

Conventions: the vehicle's forward axis is local +X, Y is left, Z is up, the origin is on the ground under the middle
of the vehicle. heading_deg=0 faces +X, 90 faces +Y. Every vehicle is one joined body mesh (the root object) with the
wheels, beacons and moving parts (booms, buckets, forks, grabs) as separate children. Wheels share one mesh per kind
(linked duplicates) and the second vehicle of a kind is a linked copy of the first, so traffic stays cheap.

How it is built (no boxes): bodies are lofted cross-sections through a subdivision cage, the wheel arches are boolean
cut with a dark liner, and glass, rubber seals, chrome trim, panel gaps, liveries and dirt are object-space shader
masks on the clear-coated paint (pixel-exact at any distance). Tyres and rims are lathed profiles with tread and
sidewall; lamps are lenses over chrome reflectors.

Sources checked for ready-made CC0 vehicles (none realistic enough or none of these types): Poly Haven (only
covered_car), Khronos glTF sample assets (ToyCar, CarConcept: stylised), Kenney and Quaternius car kits (low-poly),
OpenGameArt CC0 (low-poly), Smithsonian 3D (no road vehicles of these types). So everything here is procedural.
"""
import math
import bpy, bmesh
from mathutils import Vector, Matrix

KINDS = {}            # kind -> builder(variant) -> root object (template)
DEFAULT_DIRT = dict(excavator=0.45, grab_crane=0.55, boom_truck=0.35, flatbed_truck_1990s=0.35, delivery_truck=0.2,
                    forklift=0.3, van_1990s=0.15, bus_city=0.1)
_TEMPLATES = {}       # (kind, variant) -> template root, kept outside the scene
_MATS = {}


# ============================================================================ shader expressions
class E:
    """A shader-node socket with arithmetic, so masks read like formulas."""
    def __init__(self, g, s):
        self.g, self.s = g, s

    def _op(self, op, b=None, rev=False):
        a = self
        return self.g.math(op, b, a) if rev else self.g.math(op, a, b)
    __add__ = lambda s, b: s._op('ADD', b); __radd__ = lambda s, b: s._op('ADD', b, True)
    __sub__ = lambda s, b: s._op('SUBTRACT', b); __rsub__ = lambda s, b: s._op('SUBTRACT', b, True)
    __mul__ = lambda s, b: s._op('MULTIPLY', b); __rmul__ = lambda s, b: s._op('MULTIPLY', b, True)
    __truediv__ = lambda s, b: s._op('DIVIDE', b)
    __neg__ = lambda s: s._op('MULTIPLY', -1.0)
    def __abs__(self): return self.g.math('ABSOLUTE', self)


class G:
    def __init__(self, mat):
        self.m = mat; self.N = mat.node_tree.nodes; self.L = mat.node_tree.links
        tc = self.N.new("ShaderNodeTexCoord")
        so = self.N.new("ShaderNodeSeparateXYZ"); self.L.new(tc.outputs['Object'], so.inputs[0])
        sn = self.N.new("ShaderNodeSeparateXYZ"); self.L.new(tc.outputs['Normal'], sn.inputs[0])
        self.tc = tc
        self.x, self.y, self.z = (E(self, so.outputs[i]) for i in range(3))
        self.nx, self.ny, self.nz = (E(self, sn.outputs[i]) for i in range(3))
        self.ay = abs(self.y); self.any = abs(self.ny)

    def link(self, a, sock):
        if isinstance(a, E):
            self.L.new(a.s, sock)
        elif isinstance(a, (tuple, list)):
            sock.default_value = a
        else:
            sock.default_value = a

    def math(self, op, a, b=None, c=None):
        n = self.N.new("ShaderNodeMath"); n.operation = op
        for i, v in enumerate((a, b, c)):
            if v is not None:
                self.link(v, n.inputs[i])
        return E(self, n.outputs[0])

    def mn(self, a, b): return self.math('MINIMUM', a, b)
    def mx(self, a, b): return self.math('MAXIMUM', a, b)
    def clamp(self, a): return self.mn(self.mx(a, 0.0), 1.0)

    def ss(self, e0, e1, v):
        """smoothstep from e0 to e1 (e1 < e0 gives a falling edge)."""
        n = self.N.new("ShaderNodeMapRange"); n.interpolation_type = 'SMOOTHSTEP'; n.clamp = True
        if e1 < e0:
            e0, e1 = e1, e0; n.inputs['To Min'].default_value = 1.0; n.inputs['To Max'].default_value = 0.0
        self.link(v, n.inputs['Value']); n.inputs['From Min'].default_value = e0; n.inputs['From Max'].default_value = e1
        return E(self, n.outputs[0])

    def inside(self, v, a, b, soft=0.004):
        return self.ss(a - soft, a, v) * self.ss(b + soft, b, v)

    def band(self, v, c, hw, soft=0.002):
        return self.ss(hw + soft, hw, abs(v - c))

    def poly(self, u, v, pts):
        """signed distance (m, + inside) to a convex polygon given counter-clockwise in the (u, v) plane."""
        d = None
        for i in range(len(pts)):
            (a0, a1), (b0, b1) = pts[i], pts[(i + 1) % len(pts)]
            ex, ey = b0 - a0, b1 - a1; ln = math.hypot(ex, ey); nx, ny = -ey / ln, ex / ln     # inward normal (ccw)
            di = (u - a0) * nx + (v - a1) * ny
            d = di if d is None else self.mn(d, di)
        return d

    def circle(self, u, v, cu, cv, r):
        a = (u - cu) * (u - cu) + (v - cv) * (v - cv)
        return self.math('SQRT', a) - r

    def attr(self, name):
        n = self.N.new("ShaderNodeAttribute"); n.attribute_type = 'OBJECT'; n.attribute_name = name
        return E(self, n.outputs['Fac'])

    def noise(self, scale, detail=4.0, rough=0.6, vec=None):
        n = self.N.new("ShaderNodeTexNoise"); n.inputs['Scale'].default_value = scale
        n.inputs['Detail'].default_value = detail; n.inputs['Roughness'].default_value = rough
        self.L.new(vec if vec is not None else self.tc.outputs['Object'], n.inputs['Vector'])
        return E(self, n.outputs['Fac'])

    def noise_s(self, scale, sx, sy, sz, detail=4.0):
        mp = self.N.new("ShaderNodeMapping"); mp.inputs['Scale'].default_value = (sx, sy, sz)
        self.L.new(self.tc.outputs['Object'], mp.inputs['Vector'])
        return self.noise(scale, detail, 0.6, vec=mp.outputs[0])

    def backfacing(self):
        n = self.N.new("ShaderNodeNewGeometry")
        return E(self, n.outputs['Backfacing'])

    def bsdf(self, color, rough=0.5, metal=0.0, **kw):
        p = self.N.new("ShaderNodeBsdfPrincipled")
        self.link(color, p.inputs['Base Color']) if isinstance(color, E) else None
        if not isinstance(color, E):
            p.inputs['Base Color'].default_value = (*color[:3], 1)
        self.link(rough, p.inputs['Roughness']); p.inputs['Metallic'].default_value = metal
        for k, v in kw.items():
            self.link(v, p.inputs[k])
        return p

    def mix_col(self, fac, a, b):
        n = self.N.new("ShaderNodeMix"); n.data_type = 'RGBA'; self.link(fac, n.inputs[0])
        for sock, v in ((n.inputs[6], a), (n.inputs[7], b)):
            if isinstance(v, E):
                self.L.new(v.s, sock)
            elif hasattr(v, "bl_idname"):
                self.L.new(v, sock)
            else:
                sock.default_value = (*v[:3], 1)
        return n.outputs[2]

    def mix_shader(self, fac, a, b):
        n = self.N.new("ShaderNodeMixShader"); self.link(fac, n.inputs[0])
        self.L.new(a.outputs[0] if hasattr(a, "outputs") else a, n.inputs[1])
        self.L.new(b.outputs[0] if hasattr(b, "outputs") else b, n.inputs[2])
        return n

    def out(self, sh):
        o = self.N.get("Material Output") or self.N.new("ShaderNodeOutputMaterial")
        self.L.new(sh.outputs[0], o.inputs['Surface'])

    def bump(self, height, strength=1.0, dist=0.01):
        b = self.N.new("ShaderNodeBump"); b.inputs['Strength'].default_value = strength
        b.inputs['Distance'].default_value = dist; self.link(height, b.inputs['Height'])
        return b.outputs['Normal']


def _newmat(name):
    m = bpy.data.materials.new(name); m.use_nodes = True
    m.node_tree.nodes.remove(m.node_tree.nodes["Principled BSDF"])
    return m, G(m)


def obj_color(g):
    n = g.N.new("ShaderNodeObjectInfo")
    return n.outputs['Color']


# ============================================================================ materials
def mat(key, fn):
    if key not in _MATS or _MATS[key].name not in bpy.data.materials:
        _MATS[key] = fn()
    return _MATS[key]


def simple(name, color, rough=0.5, metal=0.0, **kw):
    def f():
        m, g = _newmat(name); g.out(g.bsdf(color, rough, metal, **kw)); return m
    return mat(name, f)


def chrome():      return simple("V_Chrome", (0.92, 0.93, 0.95), 0.06, 1.0)
def alu():         return simple("V_Alu", (0.75, 0.76, 0.78), 0.28, 1.0)
def black_plastic(): return simple("V_BlackPlastic", (0.025, 0.025, 0.027), 0.55, 0.0)
def rubber():      return simple("V_Rubber", (0.012, 0.012, 0.012), 0.6, 0.0)
def liner():       return simple("V_Liner", (0.015, 0.015, 0.016), 0.85, 0.0)
def steel_dark():  return simple("V_SteelDark", (0.08, 0.08, 0.085), 0.45, 0.8)
def interior():    return simple("V_Interior", (0.03, 0.03, 0.032), 0.8, 0.0)
def glass():
    return simple("V_Glass", (0.85, 0.9, 0.9), 0.0, 0.0, **{'Transmission Weight': 1.0, 'IOR': 1.5})


def lens(name, color=(1, 1, 1), em_col=(1.0, 0.9, 0.75), fluted=True):
    """Lamp lens: thin clear (or tinted) glass with faint fluting, over a reflector; it glows when the object's
    'lamps' property is 1."""
    def f():
        m, g = _newmat(name)
        h = (g.math('SINE', g.y * 260.0) * 0.5 + 0.5) if fluted else 0.0
        on = g.attr("lamps")
        tint = color if min(color) < 0.9 else (0.97, 0.98, 0.99)
        p = g.bsdf(tint, 0.02, 0.0, **{'Transmission Weight': 1.0, 'IOR': 1.49, 'Emission Color': (*em_col, 1)})
        p.inputs['Thin Wall'].default_value = True
        g.link(on * 4.0, p.inputs['Emission Strength'])
        if fluted:
            g.L.new(g.bump(h, 0.35, 0.002), p.inputs['Normal'])
        g.out(p); return m
    return mat(name, f)


def lamp_core(name, em_col, strength):
    """Chrome reflector behind a lens (faceted, so it sparkles through the glass); glows when 'lamps' is 1."""
    def f():
        m, g = _newmat(name)
        p = g.bsdf((0.95, 0.95, 0.96), 0.26, 0.85, **{'Emission Color': (*em_col, 1)})
        fac = (g.math('SINE', g.y * 140.0) * g.math('SINE', g.z * 140.0)) * 0.5 + 0.5
        g.L.new(g.bump(fac, 0.6, 0.003), p.inputs['Normal'])
        g.link(g.attr("lamps") * strength, p.inputs['Emission Strength'])
        g.out(p); return m
    return mat(name, f)


def plate_mat(style="eu"):
    def f():
        m, g = _newmat("V_Plate_" + style)
        # white plate, dark border, faint generic characters as a dashed band (no real registration)
        u = g.y; v = g.z
        col = g.mix_col(0.0, (0.82, 0.82, 0.8), (0.02, 0.02, 0.02))
        p = g.bsdf((0.82, 0.82, 0.8), 0.35, 0.0)
        g.out(p); return m
    return mat("V_Plate_" + style, f)


def tyre_mat(whitewall=False):
    nm = "V_TyreWW" if whitewall else "V_Tyre"
    def f():
        m, g = _newmat(nm)
        x, y, z = g.x, g.y, g.z
        r = g.math('SQRT', x * x + z * z)
        ang = g.math('ARCTAN2', x, z)
        rmax = g.attr("tyre_r")
        tread = g.ss(-0.02, -0.008, r - rmax)        # 1 on the tread face
        blocks = g.math('SINE', ang * 70.0) * 0.5 + 0.5
        grooves = g.mn(g.band(y, 0.0, 0.006, 0.002) + g.band(abs(y), 0.045, 0.005, 0.002), 1.0)
        h = tread * (1.0 - g.ss(0.35, 0.55, blocks) * 0.8) * (1.0 - grooves)
        wear = g.noise(30.0, 3.0)
        p = g.bsdf((0.03, 0.03, 0.03), 0.62 + tread * 0.25 + wear * 0.06, 0.0)
        if whitewall:
            ww = g.inside(r / rmax, 0.66, 0.86, 0.01) * g.ss(0.03, 0.05, abs(y))
            g.L.new(g.mix_col(ww, (0.03, 0.03, 0.03), (0.78, 0.77, 0.72)), p.inputs['Base Color'])
        g.L.new(g.bump(h + (1 - tread) * wear * 0.05, 0.6, 0.004), p.inputs['Normal'])
        g.out(p); return m
    return mat(nm, f)


def rim_mat(style):
    """style: steel (vents, silver paint), alloy5 (5 spokes), alloy7, truck (dark red/black steel), black."""
    def f():
        m, g = _newmat("V_Rim_" + style)
        x, y, z = g.x, g.y, g.z
        r = g.math('SQRT', x * x + z * z); ang = g.math('ARCTAN2', x, z)
        rr = g.attr("rim_r")
        rel = r / rr
        if style.startswith("alloy"):
            n = 5 if style == "alloy5" else 7
            sp = g.math('COSINE', ang * float(n)) * 0.5 + 0.5
            gap = g.ss(0.62, 0.5, sp) * g.inside(rel, 0.30, 0.86, 0.03)
            base = g.mix_col(gap, (0.62, 0.63, 0.65), (0.015, 0.015, 0.016))
            p = g.bsdf((0.6, 0.6, 0.6), 0.25, 0.9); g.L.new(base, p.inputs['Base Color'])
            g.link(gap * -0.9 + 0.95, p.inputs['Metallic'])
        else:
            nh = 10.0 if style.startswith("truck") else 4.0
            sp = g.math('COSINE', ang * nh) * 0.5 + 0.5
            hole = g.ss(0.72, 0.85, sp) * g.inside(rel, 0.55, 0.70, 0.02)
            paint = {"steel": (0.42, 0.43, 0.44), "truck": (0.28, 0.04, 0.03), "black": (0.03, 0.03, 0.03),
                     "cream": (0.7, 0.66, 0.55), "truckgrey": (0.3, 0.31, 0.32)}.get(style, (0.4, 0.4, 0.4))
            cap = g.ss(0.38, 0.34, rel) * (0.0 if style.startswith("truck") else 1.0)
            base = g.mix_col(hole, paint, (0.01, 0.01, 0.01))
            base = g.mix_col(cap, base, (0.85, 0.86, 0.88))
            p = g.bsdf((0.5, 0.5, 0.5), 0.35, 0.0); g.L.new(base, p.inputs['Base Color'])
            g.link(cap * 1.0, p.inputs['Metallic']); g.link(0.35 - cap * 0.27, p.inputs['Roughness'])
        g.out(p); return m
    return mat("V_Rim_" + style, f)


# ============================================================================ mesh helpers
def link(o, coll=None):
    (coll or bpy.context.scene.collection).objects.link(o)
    return o


def mesh_obj(name, verts, faces, mats=(), smooth=True, sharp_deg=None, face_mats=None):
    me = bpy.data.meshes.new(name); me.from_pydata([tuple(v) for v in verts], [], faces); me.validate(); me.update()
    for m in mats:
        me.materials.append(m)
    if face_mats is not None:
        for p, mi in zip(me.polygons, face_mats):
            p.material_index = mi
    if smooth:
        me.shade_smooth()
        if sharp_deg:
            me.set_sharp_from_angle(angle=math.radians(sharp_deg))
    return link(bpy.data.objects.new(name, me))


def bake(o):
    """Apply all modifiers (returns the same object with a new mesh)."""
    if not o.modifiers:
        return o
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(o.evaluated_get(dg))
    o.modifiers.clear(); old = o.data; o.data = me
    if old.users == 0:
        bpy.data.meshes.remove(old)
    return o


def subdivide(o, levels=2, sharp_deg=None):
    m = o.modifiers.new("sub", 'SUBSURF'); m.levels = levels; m.render_levels = levels
    bake(o); o.data.shade_smooth()
    if sharp_deg:
        o.data.set_sharp_from_angle(angle=math.radians(sharp_deg))
    return o


def bevel(o, width, segs=3, angle=40):
    b = o.modifiers.new("bev", 'BEVEL'); b.width = width; b.segments = segs
    b.limit_method = 'ANGLE'; b.angle_limit = math.radians(angle); b.harden_normals = False
    return bake(o)


def join(objs, name=None):
    objs = [o for o in objs if o is not None]
    for o in objs:
        bake(o)
    root = objs[0]
    if len(objs) > 1:
        with bpy.context.temp_override(active_object=root, selected_editable_objects=objs, object=root):
            bpy.ops.object.join()
    if name:
        root.name = name; root.data.name = name
    return root


def rbox(name, c, size, r, m, segs=3, rot=(0, 0, 0), sub=0):
    """Rounded box (only for genuinely boxy parts: lamp housings, boxes, bumpers ends)."""
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co = Vector((v.co.x * size[0], v.co.y * size[1], v.co.z * size[2]))
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = link(bpy.data.objects.new(name, me)); me.materials.append(m)
    if r > 0:
        b = o.modifiers.new("bev", 'BEVEL'); b.width = min(r, min(size) * 0.49); b.segments = segs
    if sub:
        s = o.modifiers.new("sub", 'SUBSURF'); s.levels = sub; s.render_levels = sub
    bake(o); me = o.data; me.shade_smooth(); me.set_sharp_from_angle(angle=math.radians(50))
    o.data.transform(Matrix.LocRotScale(Vector(c), _euler(rot).to_quaternion(), None))
    return o


def _euler(rot):
    from mathutils import Euler
    return Euler(rot, 'XYZ')


def cylinder(name, c, r, depth, m, axis='Y', verts=24, r2=None, cap=True):
    """Cylinder / truncated cone along an axis through centre c."""
    r2 = r if r2 is None else r2
    vs, fs = [], []
    for k in range(verts):
        a = 2 * math.pi * k / verts
        for rr, h in ((r, -depth / 2), (r2, depth / 2)):
            vs.append((rr * math.cos(a), rr * math.sin(a), h))
    for k in range(verts):
        a0, a1 = 2 * k, 2 * ((k + 1) % verts)
        fs.append((a0, a1, a1 + 1, a0 + 1))
    if cap:
        fs.append(tuple(2 * k for k in reversed(range(verts)))); fs.append(tuple(2 * k + 1 for k in range(verts)))
    o = mesh_obj(name, vs, fs, [m], sharp_deg=40)
    R = {'X': Matrix.Rotation(math.pi / 2, 4, 'Y'), 'Y': Matrix.Rotation(-math.pi / 2, 4, 'X'), 'Z': Matrix()}[axis]
    o.data.transform(Matrix.Translation(Vector(c)) @ R)
    return o


def sweep(name, path, profile, m, up=(0, 0, 1), scales=None, cap=True, closed_path=False, smooth=True, sharp=50):
    """Sweep a closed 2D profile [(u, v)] along a 3D polyline. u is along side = T x up, v along up'."""
    P = [Vector(p) for p in path]; n = len(P); k = len(profile)
    vs, fs = [], []
    for i in range(n):
        if closed_path:
            T = (P[(i + 1) % n] - P[i - 1]).normalized()
        else:
            T = (P[min(i + 1, n - 1)] - P[max(i - 1, 0)]).normalized()
        S = T.cross(Vector(up)); S = S.normalized() if S.length > 1e-6 else Vector((1, 0, 0))
        U = S.cross(T).normalized()
        sc = scales[i] if scales else (1.0, 1.0)
        for (u, v) in profile:
            vs.append(P[i] + S * u * sc[0] + U * v * sc[1])
    rng = n if closed_path else n - 1
    for i in range(rng):
        i2 = (i + 1) % n
        for j in range(k):
            j2 = (j + 1) % k
            fs.append((i * k + j, i * k + j2, i2 * k + j2, i2 * k + j))
    if cap and not closed_path:
        fs.append(tuple(reversed(range(k)))); fs.append(tuple((n - 1) * k + j for j in range(k)))
    return mesh_obj(name, vs, fs, [m], smooth=smooth, sharp_deg=sharp)


def lathe(name, profile, m, segs=48, axis='Y'):
    """Revolve an open profile [(r, h)] around the axis (h along the axis)."""
    vs, fs = [], []
    k = len(profile)
    for s in range(segs):
        a = 2 * math.pi * s / segs
        for (r, h) in profile:
            vs.append((r * math.sin(a), h, r * math.cos(a)))
    for s in range(segs):
        s2 = (s + 1) % segs
        for j in range(k - 1):
            fs.append((s * k + j, s * k + j + 1, s2 * k + j + 1, s2 * k + j))
    o = mesh_obj(name, vs, fs, [m], sharp_deg=55)
    if axis == 'X':
        o.data.transform(Matrix.Rotation(-math.pi / 2, 4, 'Z'))
    elif axis == 'Z':
        o.data.transform(Matrix.Rotation(math.pi / 2, 4, 'X'))
    return o


def rounded_rect(w, h, r, n=4):
    """Closed 2D outline (ccw) of a w x h rectangle with corner radius r, centred."""
    pts = []
    for cx, cy, a0 in ((w / 2 - r, h / 2 - r, 0), (-w / 2 + r, h / 2 - r, 90), (-w / 2 + r, -h / 2 + r, 180), (w / 2 - r, -h / 2 + r, 270)):
        for i in range(n + 1):
            a = math.radians(a0 + 90 * i / n)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


# ============================================================================ body loft
def _lerp(a, b, t): return a + (b - a) * t


def section(st):
    """Half cross-section (y >= 0) from the bottom centre round the side to the top centre.
    st: zb (underside), belt (shoulder), top (roof / deck), w (half width at the side), wt (half width at the top),
    crown (roof camber), tumble (how far the greenhouse leans in), bul (side bulge), rb (bottom corner radius)."""
    zb, belt, top, w, wt = st['zb'], st['belt'], st['top'], st['w'], st['wt']
    crown = st.get('crown', 0.025); bul = st.get('bul', 0.012); rb = st.get('rb', 0.08); rs = st.get('rs', 0.05)
    rt = st.get('rt', 0.07)
    # keep every corner radius inside the section, or the loft folds through its centreline on narrow parts
    rt = min(rt, wt * 0.6); rb = min(rb, w * 0.5); rs = min(rs, w * 0.4)
    h_g = max(top - belt, 0.0)
    pts = [(0.0, zb), (min(w * 0.55, w - rb * 1.45), zb), (w - rb * 1.2, zb + 0.004), (w - rb * 0.35, zb + rb * 0.35), (w, zb + rb * 1.1),
           (w + bul, _lerp(zb, belt, 0.55)), (w + bul * 0.6, belt - rs * 1.4), (w - rs * 0.25, belt - rs * 0.25),
           (w - rs, belt + 0.004)]
    # greenhouse: lean in from the shoulder to the roof edge
    sh = w - rs
    pts += [(_lerp(sh, wt, 0.06), belt + min(0.02, h_g * 0.3)), (_lerp(sh, wt, 0.5), belt + h_g * 0.52),
            (wt, top - min(rt * 1.1, h_g * 0.62)), (wt - rt * 0.4, top - min(rt * 0.35, h_g * 0.22)), (wt - rt * 1.2, top - 0.002)]
    pts += [(wt * 0.5, top + crown * 0.8), (0.0, top + crown)]
    return pts


def loft_body(name, keys, m_paint, step=0.11, levels=2, extra=0.035, sharp=None):
    """keys: list of station dicts sorted by x descending (front first). Parameters are interpolated linearly between
    keys; stations are added at each key, at key +- extra (to keep creases crisp) and every `step` between."""
    keys = sorted(keys, key=lambda k: -k['x'])
    xs = set()
    for i, k in enumerate(keys):
        xs.add(round(k['x'], 4))
        if 0 < i < len(keys) - 1 and not k.get('soft'):
            xs.add(round(k['x'] + extra, 4)); xs.add(round(k['x'] - extra, 4))
        if i < len(keys) - 1:
            a, b = k['x'], keys[i + 1]['x']; n = max(1, int(abs(a - b) / step))
            for j in range(1, n):
                xs.add(round(_lerp(a, b, j / n), 4))
    xs = sorted(xs, reverse=True)
    names = [n for n in keys[0] if n not in ('x', 'soft')]

    def at(x):
        for i in range(len(keys) - 1):
            a, b = keys[i], keys[i + 1]
            if b['x'] <= x <= a['x']:
                t = (a['x'] - x) / max(a['x'] - b['x'], 1e-9)
                return {n: _lerp(a.get(n, keys[0][n]), b.get(n, keys[0][n]), t) for n in names}
        return {n: keys[0 if x > keys[0]['x'] else -1][n] for n in names}
    vs, fs = [], []
    ring = None
    for x in xs:
        half = section(at(x))
        full = half + [(-y, z) for (y, z) in reversed(half[1:-1])]
        ring = len(full)
        for (y, z) in full:
            vs.append((x, y, z))
    ns = len(xs)
    for i in range(ns - 1):
        for j in range(ring):
            j2 = (j + 1) % ring
            fs.append((i * ring + j, (i + 1) * ring + j, (i + 1) * ring + j2, i * ring + j2))
    # end caps: a fan to an inset centre point keeps the subdivided nose and tail flat
    for i, sgn in ((0, 1), (ns - 1, -1)):
        c = Vector((0, 0, 0))
        for j in range(ring):
            c += Vector(vs[i * ring + j])
        c /= ring; c.x += sgn * 0.004
        ci = len(vs); vs.append(tuple(c))
        for j in range(ring):
            j2 = (j + 1) % ring
            fs.append((i * ring + j2, i * ring + j, ci) if sgn > 0 else (i * ring + j, i * ring + j2, ci))
    o = mesh_obj(name, vs, fs, [m_paint])
    bm = bmesh.new(); bm.from_mesh(o.data)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)       # consistent winding (end caps included) ...
    if bm.calc_volume(signed=True) < 0:                       # ... and facing outward          # make the shell face outward (end-cap winding varies)
        bmesh.ops.reverse_faces(bm, faces=bm.faces)
    bm.to_mesh(o.data); bm.free()
    subdivide(o, levels)
    if sharp:
        o.data.set_sharp_from_angle(angle=math.radians(sharp))
    return o


def boolean_cut(obj, cutter, solver='EXACT'):
    """Difference with a safety net: if a solver unions instead of cutting (the bounds grow), try the next one."""
    dims = obj.dimensions.copy(); orig = obj.data.copy()
    for sv in [solver] + [x for x in ('MANIFOLD', 'EXACT', 'FLOAT') if x != solver]:
        b = obj.modifiers.new("cut", 'BOOLEAN'); b.operation = 'DIFFERENCE'; b.object = cutter; b.solver = sv
        try:
            b.material_mode = 'TRANSFER'
        except Exception:
            pass
        bake(obj); bpy.context.view_layer.update()
        if all(obj.dimensions[i] <= dims[i] + 1e-3 for i in range(3)):
            break
        obj.data = orig.copy()
    bpy.data.meshes.remove(orig)
    return obj


def cut_arches(body, arches, m_liner, solver='EXACT'):
    """arches: [(x, z, r, y_in, y_out)] cylinders cut out of both sides of the body; the cut is lined (dark)."""
    cutters = []
    for (x, z, r, yi, yo) in arches:
        for s in (-1, 1):
            c = cylinder("ArchCut", (x, s * (yi + yo) / 2, z), r, yo - yi, m_liner, axis='Y', verts=48)
            cutters.append(c)
    cu = join(cutters, "ArchCutters")
    body.data.materials.append(m_liner)
    boolean_cut(body, cu, solver)
    bpy.data.objects.remove(cu)
    body.data.shade_smooth(); body.data.set_sharp_from_angle(angle=math.radians(40))
    return body


# ============================================================================ paint with masks
def paint_shader(name, build_masks, metallic=0.0, rough=0.32, glass_thin=True, fixed_color=None, back_col=(0.035, 0.035, 0.037)):
    """Clear-coat paint whose base colour comes from the object colour (so one material serves a whole fleet) and
    whose glass, seals, chrome, gaps and livery come from object-space masks.
    build_masks(g) -> dict with optional keys: glass, rubber, chrome, black, gap, livery=[(mask, colour)],
    and 'paint_override' etc. Each is an E (0..1)."""
    def f():
        m, g = _newmat(name)
        M = build_masks(g)
        base = obj_color(g) if fixed_color is None else g.mix_col(0.0, fixed_color, fixed_color)
        for msk, col in M.get('livery', []):
            base = g.mix_col(msk, base, col)
        dirt = g.attr("dirt")
        dn = g.noise(3.5, 6.0, 0.65)
        dmask = g.clamp(dirt * (g.ss(0.9, 0.15, g.z) * 1.1 + (dn - 0.45) * 2.2))
        streak = g.noise(18.0, 3.0)
        # wear: sun-faded paint, rust streaks running down from seams, mud on the lower body
        fade = g.clamp(dirt * (g.noise(0.8, 2.0) * 1.2 - 0.1))
        base = g.mix_col(fade * 0.4, base, (0.46, 0.45, 0.42))
        rust = g.clamp(g.ss(0.6, 0.74, g.noise_s(4.0, 7.0, 7.0, 0.5)) * g.clamp(dirt * 2.0 - 0.3))
        base = g.mix_col(rust * 0.75, base, (0.20, 0.085, 0.03))
        base = g.mix_col(dmask * 0.85, base, (0.16, 0.13, 0.095))
        gap = M.get('gap', 0.0)
        if isinstance(gap, E):
            base = g.mix_col(gap * 0.9, base, (0.01, 0.01, 0.01))
        # one Principled BSDF whose inputs are blended by the masks (cheap: few closures, fast to render)
        col = base
        rgh = rough + dmask * 0.5 + streak * 0.04
        met = metallic; coat = 1.0 - dmask * 0.9; trn = 0.0; spec = 0.5
        ecol = None; estr = 0.0
        def lerp(a, b, m):
            return a + (b - a) * m if isinstance(m, E) else a
        layers = []
        if 'black' in M:
            layers.append((M['black'], (0.02, 0.02, 0.022), 0.5, 0.0, 0.0, 0.0, None, 0.0))
        if 'glass' in M:
            if glass_thin:
                layers.append((M['glass'], (0.62, 0.68, 0.68), 0.0 + dirt * 0.12, 0.0, 0.0, 1.0, None, 0.0))
            else:
                layers.append((M['glass'], (0.004, 0.005, 0.006), 0.015 + dirt * 0.25, 0.0, 0.0, 0.0, None, 0.0))
        if 'rubber' in M:
            layers.append((M['rubber'], (0.012, 0.012, 0.012), 0.55, 0.0, 0.0, 0.0, None, 0.0))
        if 'chrome' in M:
            layers.append((M['chrome'], (0.9, 0.9, 0.92), 0.07 + dirt * 0.2, 1.0, 0.0, 0.0, None, 0.0))
        on = g.attr("lamps")
        for key, lc, ec, st in (('head', (0.62, 0.63, 0.65), (1.0, 0.93, 0.8), 25.0), ('tail', (0.32, 0.01, 0.008), (1.0, 0.04, 0.02), 10.0),
                                ('ind', (0.6, 0.26, 0.01), (1.0, 0.45, 0.02), 0.0), ('drl', (0.7, 0.72, 0.75), (0.9, 0.95, 1.0), 12.0)):
            if key in M:
                layers.append((M[key], lc, 0.08, 0.6 if key in ('head', 'drl') else 0.1, 1.0, 0.0, ec, st))
        # inside of the shell (seen through the glass): dark trim / headliner, never paint
        if 'glass' in M:
            back = g.backfacing() * (1.0 - M['glass'])
            layers.append((back, back_col, 0.8, 0.0, 0.0, 0.0, None, 0.0))
        for (mk, lc, lr, lm, lco, lt, ec, st) in layers:
            col = g.mix_col(mk, col, lc)
            rgh = lerp(rgh, lr, mk); met = lerp(met, lm, mk); coat = lerp(coat, lco, mk); trn = lerp(trn, lt, mk)
            if ec is not None:
                ecol = g.mix_col(mk, ecol if ecol is not None else (0, 0, 0), ec)
                estr = estr + mk * on * st
        p = g.bsdf((0.5, 0.5, 0.5), 0.3, 0.0, **{'Coat Roughness': 0.03, 'IOR': 1.5})
        g.L.new(col, p.inputs['Base Color']) if not isinstance(col, E) else g.link(col, p.inputs['Base Color'])
        g.link(rgh, p.inputs['Roughness']); g.link(met, p.inputs['Metallic']); g.link(coat, p.inputs['Coat Weight'])
        g.link(trn, p.inputs['Transmission Weight'])
        p.inputs['Thin Wall'].default_value = bool(glass_thin)
        if ecol is not None:
            g.L.new(ecol, p.inputs['Emission Color']); g.link(estr, p.inputs['Emission Strength'])
        dent = g.noise(1.3, 2.0) * g.clamp(dirt * 1.5 - 0.15) * 0.6
        nrm = g.bump((gap * -1.0 if isinstance(gap, E) else 0.0) + dent, 0.8, 0.004)
        g.L.new(nrm, p.inputs['Normal'])
        sh = p
        g.out(sh); return m
    return mat(name, f)


def window_masks(g, side_polys, front=None, rear=None, seal=0.016, trim=0.0, side_min_ny=0.55):
    """Glass + rubber seal (+ optional chrome trim) masks.
    side_polys: convex polygons in (x, z) for side glass; front / rear: convex polygons in (y, z) for the screens."""
    gl = None; rb = None; ch = None
    def acc(a, b): return b if a is None else g.mx(a, b)
    sideness = g.ss(side_min_ny - 0.08, side_min_ny, g.any)
    for P in side_polys:
        d = g.poly(g.x, g.z, P)
        acc_g = g.ss(0.0, 0.002, d) * sideness
        gl = acc(gl, acc_g)
        rb = acc(rb, g.ss(-seal - 0.002, -seal, d) * sideness)
        if trim:
            ch = acc(ch, g.ss(-seal - trim - 0.002, -seal - trim, d) * sideness)
    screens = []
    for P, sgn in ((front, 1), (rear, -1)):
        if P is None:
            continue
        for Q in (P if isinstance(P[0][0], (tuple, list)) else [P]):
            screens.append((Q, sgn))
    for P, sgn in screens:
        fr = g.ss(0.18, 0.32, g.nx * float(sgn))
        d = g.poly(g.y, g.z, P)
        gl = acc(gl, g.ss(0.0, 0.002, d) * fr)
        rb = acc(rb, g.ss(-seal - 0.002, -seal, d) * fr)
        if trim:
            ch = acc(ch, g.ss(-seal - trim - 0.002, -seal - trim, d) * fr)
    out = dict(glass=gl, rubber=g.clamp(rb - gl))
    if trim:
        out['chrome'] = g.clamp(ch - rb)
    return out


def gaps(g, lines, w=0.0022):
    """Panel-gap grooves. lines: list of tuples
       ('x', x0, zlo, zhi)            vertical line on the sides (|ny| > .4) at x = x0 from z lo..hi
       ('z', z0, xlo, xhi)            horizontal line on the sides
       ('top_x', x0, ymax)            line across the top deck at x = x0 (|y| < ymax)
       ('top_y', y0, xlo, xhi)        line along the deck at |y| = y0
       ('end_z', sgn, z0, ymax)       horizontal line on the nose (sgn 1) or tail (-1)
       ('end_y', sgn, y0, zlo, zhi)   vertical line on the nose / tail at |y| = y0
       ('arc', x, z, r, xlo, xhi, zlo, zhi)  arc on the sides (doors around wheel arches)"""
    acc = None
    side = g.ss(0.35, 0.5, g.any); top = g.ss(0.45, 0.6, g.nz)
    for L in lines:
        k = L[0]
        if k == 'x':
            m = g.band(g.x, L[1], w) * g.inside(g.z, L[2], L[3]) * side
        elif k == 'z':
            m = g.band(g.z, L[1], w) * g.inside(g.x, L[2], L[3]) * side
        elif k == 'top_x':
            m = g.band(g.x, L[1], w) * g.ss(L[2] + 0.004, L[2], g.ay) * top
        elif k == 'top_y':
            m = g.band(g.ay, L[1], w) * g.inside(g.x, L[2], L[3]) * top
        elif k == 'end_z':
            m = g.band(g.z, L[2], w) * g.ss(L[3] + 0.004, L[3], g.ay) * g.ss(0.4, 0.6, g.nx * float(L[1]))
        elif k == 'end_y':
            m = g.band(g.ay, L[2], w) * g.inside(g.z, L[3], L[4]) * g.ss(0.4, 0.6, g.nx * float(L[1]))
        elif k == 'arc':
            d = g.circle(g.x, g.z, L[1], L[2], L[3])
            m = g.band(d, 0.0, w) * g.inside(g.x, L[4], L[5]) * g.inside(g.z, L[6], L[7]) * side
        acc = m if acc is None else g.mx(acc, m)
    return acc


# ============================================================================ wheels
def wheel_mesh(key, R, W, rim_r, style="steel", segs=56, dual=False, whitewall=False):
    """One shared wheel mesh: lathed tyre (sidewall bulge, rounded shoulder, tread via shader) + rim + hub.
    Outer face towards local +Y."""
    nm = f"Wheel_{key}"
    if nm in bpy.data.meshes:
        return bpy.data.meshes[nm]
    h = W / 2
    sw = R - rim_r
    tp = [(rim_r - 0.004, -h * 0.80), (rim_r + 0.012, -h * 0.94), (rim_r + sw * 0.3, -h * 1.04), (rim_r + sw * 0.62, -h * 1.07),
          (R - sw * 0.16, -h * 1.0), (R - 0.008, -h * 0.84), (R, -h * 0.64), (R, -h * 0.2), (R, h * 0.2), (R, h * 0.64),
          (R - 0.008, h * 0.84), (R - sw * 0.16, h * 1.0), (rim_r + sw * 0.62, h * 1.07), (rim_r + sw * 0.3, h * 1.04),
          (rim_r + 0.012, h * 0.94), (rim_r - 0.004, h * 0.80)]
    tyre = lathe("Tyre", tp, tyre_mat(whitewall), segs)
    rr = rim_r
    if style.startswith("alloy"):
        rp = [(rr - 0.01, -h * 0.75), (rr - 0.008, h * 0.70), (rr + 0.006, h * 0.80), (rr + 0.004, h * 0.88), (rr - 0.006, h * 0.86),
              (rr * 0.93, h * 0.80), (rr * 0.80, h * 0.86), (rr * 0.45, h * 0.82), (rr * 0.30, h * 0.9), (rr * 0.18, h * 0.92),
              (rr * 0.17, h * 0.97), (0.0, h * 0.98)]
    else:
        rp = [(rr - 0.01, -h * 0.75), (rr - 0.008, h * 0.62), (rr + 0.012, h * 0.76), (rr + 0.009, h * 0.86), (rr - 0.006, h * 0.80),
              (rr * 0.93, h * 0.40), (rr * 0.80, h * 0.10), (rr * 0.62, h * 0.18), (rr * 0.48, h * 0.08), (rr * 0.40, h * 0.40),
              (rr * 0.34, h * 0.66), (rr * 0.2, h * 0.76), (0.0, h * 0.80)]
    rim = lathe("Rim", rp, rim_mat(style), segs)
    disc = cylinder("Disc", (0, -h * 0.2, 0), rr * 0.8, 0.02, steel_dark(), axis='Y', verts=32)
    parts = [tyre, rim, disc]
    if dual:     # twin rear wheels: a second tyre inboard
        t2 = lathe("Tyre2", [(r, y - W * 1.05) for (r, y) in tp], tyre_mat(), segs); parts.append(t2)
        b2 = lathe("Rim2", [(rr - 0.01, -W * 1.05 - h * 0.75), (rr - 0.01, -W * 1.05 + h * 0.75)], rim_mat(style), segs); parts.append(b2)
    o = join(parts, nm)
    me = o.data; bpy.data.objects.remove(o)
    return me


def add_wheel(root, me, x, y, z, R, rim_r, side, coll=None):
    o = bpy.data.objects.new(f"{root.name}_wheel", me); link(o)
    o.parent = root; o.location = (x, y, z)
    o.rotation_euler = (0, 0, 0 if side > 0 else math.pi)
    o["spin_sign"] = 1.0 if side > 0 else -1.0
    o["radius"] = R; o["tyre_r"] = R; o["rim_r"] = rim_r; o["is_wheel"] = 1
    return o


# ============================================================================ lamps, plates, mirrors
def lamp(name, c, size, kind="head", r=0.02, facing=1, shape="rect"):
    """A lamp unit: chrome reflector core behind a lens, in a thin black bezel. kind: head, tail, ind (amber), fog, rev.
    facing: +1 lens faces +X, -1 faces -X, 'L'/'R' faces +Y/-Y."""
    cols = dict(head=((0.95, 0.96, 0.97), (1.0, 0.93, 0.8), 30), tail=((0.42, 0.012, 0.01), (1.0, 0.05, 0.02), 12),
                ind=((0.75, 0.3, 0.015), (1.0, 0.45, 0.02), 10), rev=((0.95, 0.95, 0.95), (1, 1, 1), 6),
                fog=((0.95, 0.95, 0.9), (1.0, 0.9, 0.7), 18))
    lc, ec, st = cols[kind]
    d, w, h = size
    core = rbox(name + "Core", (0, 0, 0), (d * 0.6, w * 0.92, h * 0.88), min(r, h * 0.3), lamp_core(f"V_LampCore_{kind}", ec, st))
    ln = rbox(name + "Lens", (d * 0.25, 0, 0), (d * 0.5, w, h), min(r, h * 0.45), lens(f"V_Lens_{kind}", lc, ec, kind == "head"), sub=0)
    bz = rbox(name + "Bezel", (-d * 0.1, 0, 0), (d * 0.8, w + 0.012, h + 0.012), min(r + 0.006, h * 0.45), black_plastic())
    o = join([core, ln, bz], name)
    rotz = {1: 0, -1: math.pi, 'L': math.pi / 2, 'R': -math.pi / 2}[facing]
    o.data.transform(Matrix.Translation(Vector(c)) @ Matrix.Rotation(rotz, 4, 'Z'))
    return o


def round_lamp(name, c, rad, depth, kind="head", facing=1, chrome_ring=True):
    cols = dict(head=((0.95, 0.96, 0.97), (1.0, 0.93, 0.8), 30), tail=((0.42, 0.012, 0.01), (1.0, 0.05, 0.02), 12),
                ind=((0.75, 0.3, 0.015), (1.0, 0.45, 0.02), 10))
    lc, ec, st = cols[kind]
    ln = lathe(name + "Lens", [(0.0, depth * 0.55), (rad * 0.5, depth * 0.5), (rad * 0.9, depth * 0.35), (rad, depth * 0.1)],
               lens(f"V_Lens_{kind}", lc, ec, kind == "head"), 32, axis='X')
    core = lathe(name + "Core", [(0.0, -depth * 0.1), (rad * 0.6, -depth * 0.05), (rad * 0.97, depth * 0.1)],
                 lamp_core(f"V_LampCore_{kind}", ec, st), 32, axis='X')
    parts = [ln, core]
    if chrome_ring:
        parts.append(lathe(name + "Ring", [(rad * 0.97, depth * 0.2), (rad * 1.08, depth * 0.25), (rad * 1.14, depth * 0.05),
                                           (rad * 1.12, -depth * 0.6)], chrome(), 32, axis='X'))
    o = join(parts, name)
    rotz = {1: 0, -1: math.pi}[facing]
    o.data.transform(Matrix.Translation(Vector(c)) @ Matrix.Rotation(rotz, 4, 'Z'))
    return o


def plate(name, c, facing=1, size=(0.52, 0.112)):
    w, h = size
    p = rbox(name, (0, 0, 0), (0.008, w, h), 0.006, plate_mat())
    b = rbox(name + "B", (-0.004, 0, 0), (0.006, w + 0.012, h + 0.012), 0.006, black_plastic())
    o = join([p, b], name)
    o.data.transform(Matrix.Translation(Vector(c)) @ Matrix.Rotation(0 if facing > 0 else math.pi, 4, 'Z'))
    return o


def mirror(name, c, side, m_head, size=(0.06, 0.16, 0.10), arm=0.08, m_arm=None):
    """Door mirror: tapered housing on a short arm, glass face to the rear."""
    d, w, h = size
    hd = rbox(name + "H", (0, side * (arm + w / 2), 0), (d, w, h), min(d, h) * 0.45, m_head, sub=1)
    gl = rbox(name + "G", (-d * 0.5, side * (arm + w / 2), 0), (0.004, w * 0.86, h * 0.8), 0.01, chrome())
    am = rbox(name + "A", (0.0, side * arm / 2, -h * 0.15), (d * 0.6, arm + 0.02, h * 0.35), 0.01, m_arm or black_plastic())
    o = join([hd, gl, am], name)
    o.data.transform(Matrix.Translation(Vector(c)))
    return o


def text_mesh(name, s, size, m, font="/usr/share/fonts/opentype/inter/Inter-Bold.otf", extrude=0.0015):
    import os
    cu = bpy.data.curves.new(name, 'FONT'); cu.body = s; cu.size = size; cu.extrude = extrude
    if os.path.exists(font):
        cu.font = bpy.data.fonts.load(font, check_existing=True)
    cu.align_x = 'CENTER'; cu.align_y = 'CENTER'
    o = link(bpy.data.objects.new(name, cu))
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(o.evaluated_get(dg)); bpy.data.objects.remove(o)
    me.materials.clear(); me.materials.append(m)
    return link(bpy.data.objects.new(name, me))


def side_text(name, s, x, z, y, size, m, side):
    """Text on a body side (reads correctly on both sides)."""
    o = text_mesh(name, s, size, m)
    R = Matrix.Rotation(math.pi / 2, 4, 'X')
    if side < 0:
        R = Matrix.Rotation(math.pi / 2, 4, 'X')
        o.data.transform(R); o.data.transform(Matrix.Translation((x, -y, z)))
    else:
        o.data.transform(Matrix.Rotation(math.pi, 4, 'Z') @ R); o.data.transform(Matrix.Translation((x, y, z)))
    return o


def cabin_interior(parts, rows, y_off, z_seat, x_dash, z_dash, w_in, driver=1, bench_rear=True, wheel_r=0.19, rear_headrests=False):
    """Seats with headrests, a dashboard and a steering wheel, so the cabin reads through real glass.
    rows: seat-cushion centre x per row (front first). driver: +1 = left-hand drive (wheel at +y)."""
    it = interior(); fab = simple("V_SeatFabric", (0.055, 0.055, 0.06), 0.9)
    for k, x in enumerate(rows):
        ys = (0.0,) if (k > 0 and bench_rear) else (-y_off, y_off)
        wd = 2 * y_off + 0.46 if (k > 0 and bench_rear) else 0.48
        for y in ys:
            parts.append(rbox("Cushion", (x, y, z_seat), (0.5, wd, 0.13), 0.05, fab, sub=1))
            parts.append(rbox("SeatBack", (x - 0.27, y, z_seat + 0.33), (0.13, wd, 0.58), 0.05, fab, rot=(0, math.radians(-12), 0), sub=1))
            for yh in ((y,) if wd < 1 else ((y - y_off, y + y_off) if rear_headrests else ())):
                parts.append(rbox("Headrest", (x - 0.36, yh, z_seat + 0.72), (0.09, 0.26, 0.17), 0.04, fab, sub=1))
    parts.append(rbox("Dash", (x_dash, 0, z_dash), (0.38, 2 * w_in, 0.2), 0.06, it, sub=1))
    yw = driver * y_off
    ring = lathe("Steer", [(wheel_r, 0.0), (wheel_r + 0.015, 0.012), (wheel_r + 0.03, 0.0), (wheel_r + 0.015, -0.012)], it, 24, axis='X')
    ring.data.polygons.foreach_set("use_smooth", [True] * len(ring.data.polygons))
    ring.data.transform(Matrix.Translation((x_dash - 0.3, yw, z_dash + 0.02)) @ Matrix.Rotation(math.radians(-25), 4, 'Y'))
    parts.append(ring)
    parts.append(cylinder("Column", (x_dash - 0.2, yw, z_dash - 0.02), 0.025, 0.25, it, axis='X', verts=10))


def underbody(name, x0, x1, w, z0, z1):
    """A dark floor pan / chassis under the body so the gap under the car reads with depth."""
    return rbox(name, ((x0 + x1) / 2, 0, (z0 + z1) / 2), (x1 - x0, 2 * w, z1 - z0), 0.03, liner())


# ============================================================================ beacons (frame drivers, no scripts)
def _drive(idblock, path, expr, index=-1):
    fc = idblock.driver_add(path, index) if index >= 0 else idblock.driver_add(path)
    fc.driver.type = 'SCRIPTED'; fc.driver.expression = expr
    return fc


def beacon_mat(name, col, expr):
    m, g = _newmat(name)
    p = g.bsdf(col, 0.08, 0.0, **{'Transmission Weight': 0.6, 'Emission Color': (*col, 1), 'Emission Strength': 0.0})
    g.out(p)
    _drive(p.inputs['Emission Strength'], 'default_value', expr)
    return m


def add_rotating_beacon(root, loc, col, rate=1.6, phase=0.0, rad=0.075, height=0.11, real_light=True, energy=250):
    """A rotating beacon: a coloured dome with a pulsing glow and a spot light inside that spins (driver on frame)."""
    key = f"V_Beacon_{col}_{rate}_{phase}"
    expr = f"2.0 + 18.0 * max(0.0, cos((frame * {rate} + {phase}) * 0.2618)) ** 6"
    m = bpy.data.materials.get(key) or beacon_mat(key, col, expr)
    dome = lathe("Dome", [(0.0, height), (rad * 0.6, height * 0.95), (rad * 0.95, height * 0.65), (rad, 0.0)], m, 24, axis='Z')
    base = cylinder("BeaconBase", (0, 0, -0.012), rad * 1.15, 0.025, black_plastic(), axis='Z', verts=24)
    o = join([dome, base], "Beacon"); o.parent = root; o.location = loc
    if real_light:
        ld = bpy.data.lights.new("BeaconL", 'SPOT'); ld.color = col; ld.energy = energy
        ld.spot_size = math.radians(35); ld.spot_blend = 0.4; ld.shadow_soft_size = 0.02
        lo = link(bpy.data.objects.new("BeaconL", ld)); lo.parent = o; lo.location = (0, 0, height * 0.45)
        lo.rotation_euler = (math.radians(90), 0, 0)
        _drive(lo, 'rotation_euler', f"(frame * {rate} + {phase}) * 0.2618", 2)
    return o


def add_lightbar(root, loc, length=1.1, cols=((0.1, 0.25, 1.0), (0.1, 0.25, 1.0)), rate=1.6, real_light=True):
    """Low modern light bar: a black base with two clear-blue rotating units and a centre siren grille."""
    x, y, z = loc
    base = rbox("BarBase", (0, 0, 0.03), (0.26, length, 0.06), 0.025, black_plastic(), sub=1)
    feet = [rbox("BarFoot", (0, s * length * 0.38, -0.005), (0.18, 0.06, 0.03), 0.01, black_plastic()) for s in (-1, 1)]
    o = join([base] + feet, "LightBar"); o.parent = root; o.location = loc
    for k, (s, col) in enumerate(zip((-1, 1), cols)):
        b = add_rotating_beacon(o, (0, s * length * 0.3, 0.06), col, rate, phase=k * 6, rad=0.09, height=0.08, real_light=real_light)
    return o


# ============================================================================ instancing
def _template_coll():
    c = bpy.data.collections.get("_vehicle_templates")
    if c is None:
        c = bpy.data.collections.new("_vehicle_templates")
    return c


def _stash(root):
    """Move a freshly built hierarchy out of the scene into the template collection."""
    tc = _template_coll()
    for o in [root] + list(root.children_recursive):
        for c in list(o.users_collection):
            c.objects.unlink(o)
        tc.objects.link(o)


def _clone(root):
    mp = {}
    def rec(o, parent):
        n = o.copy()
        if n.animation_data:
            for fc in n.animation_data.drivers:
                pass
        link(n); mp[o] = n
        if parent is not None:
            n.parent = parent; n.matrix_parent_inverse = o.matrix_parent_inverse.copy()
        for ch in o.children:
            rec(ch, n)
        return n
    r = rec(root, None)
    for o, n in mp.items():
        for c in n.constraints:
            t = getattr(c, "target", None)
            if t in mp:
                c.target = mp[t]
    return r


def make(kind, loc=(0, 0, 0), heading_deg=0.0, color=None, variant=None, dirt=None, lamps=False, real_lights=False, **opts):
    """Return the root object of a new vehicle of `kind` placed at loc, facing heading_deg (0 = +X).
    Extra keyword options go to the builder (e.g. cars=4 for trains)."""
    if kind not in KINDS:
        raise KeyError(f"unknown vehicle kind {kind!r}; have {sorted(KINDS)}")
    key = (kind, variant, tuple(sorted(opts.items())))
    if key not in _TEMPLATES or _TEMPLATES[key].name not in bpy.data.objects:
        t = KINDS[kind](variant, **opts) if opts else KINDS[kind](variant)
        t["vehicle_kind"] = kind; t["vehicle_variant"] = variant or ""
        _stash(t); _TEMPLATES[key] = t
    root = _clone(_TEMPLATES[key])
    root.location = loc; root.rotation_euler = (0, 0, math.radians(heading_deg))
    col = color or tuple(root.get("default_color", (0.5, 0.5, 0.5)))
    if dirt is None:          # working machines and trucks come worn by default, cars clean
        dirt = DEFAULT_DIRT.get(kind, 0.0)
    for o in [root] + list(root.children_recursive):
        o.color = (*col[:3], 1.0)
        o["dirt"] = float(dirt); o["lamps"] = 1.0 if lamps else 0.0
    if real_lights and lamps:
        _add_real_lamps(root)
    return root


def _add_real_lamps(root):
    for (x, y, z) in root.get("headlamps", []):
        ld = bpy.data.lights.new("HeadL", 'SPOT'); ld.energy = 400; ld.spot_size = math.radians(55); ld.spot_blend = 0.5
        ld.color = (1.0, 0.92, 0.8); ld.shadow_soft_size = 0.05
        lo = link(bpy.data.objects.new("HeadL", ld)); lo.parent = root; lo.location = (x + 0.05, y, z)
        lo.rotation_euler = (0, math.radians(95), 0)


def lights(root, on=True):
    for o in [root] + list(root.children_recursive):
        o["lamps"] = 1.0 if on else 0.0


def wheels(root):
    return [o for o in root.children_recursive if o.get("is_wheel")]


def spin_wheels(root, distance, keyframe_frame=None):
    """Roll every wheel for `distance` metres travelled forward (negative = reversing)."""
    for w in wheels(root):
        w.rotation_euler[1] = w["spin_sign"] * distance / w["radius"]
        if keyframe_frame is not None:
            w.keyframe_insert("rotation_euler", index=1, frame=keyframe_frame)


def part(root, name):
    """A named moving part (e.g. 'boom', 'stick', 'bucket', 'house', 'grab', 'forks', 'mast')."""
    for o in root.children_recursive:
        if o.get("part") == name:
            return o
    return None


def _finish(body, name, color, wheel_list=(), heads=()):
    body.name = name
    body["default_color"] = color
    body["headlamps"] = [tuple(h) for h in heads]
    return body


# ============================================================================ vehicle builders
from vehicles_cars import register as _reg_cars          # noqa: E402
_reg_cars(KINDS)
try:
    from vehicles_modern import register as _reg_modern  # noqa: E402
    _reg_modern(KINDS)
except ImportError as e:
    if "vehicles_modern" not in str(e):
        raise
try:
    from vehicles_rail import register as _reg_rail      # noqa: E402
    _reg_rail(KINDS)
except ImportError as e:
    if "vehicles_rail" not in str(e):
        raise
try:
    from vehicles_air import register as _reg_air        # noqa: E402
    _reg_air(KINDS)
except ImportError as e:
    if "vehicles_air" not in str(e):
        raise
try:
    from vehicles_heavy import register as _reg_heavy    # noqa: E402
    _reg_heavy(KINDS)
except ImportError:
    pass
