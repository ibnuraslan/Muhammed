"""Safety pin, wire, pins-in-box and paper props. exec() after lib.py."""
PIN_L = 0.052      # hero pin length (m)
PIN_R = 0.0045     # coil radius
WIRE = 0.00065     # wire radius
STEEL = None

def steel():
    m = bpy.data.materials.get("PinSteel")
    if m: return m
    return mat("PinSteel", (0.80, 0.82, 0.86), 0.22, 1.0)

def poly_curve(name, c, pts, radius=WIRE, m=None, taper_end=False):
    cu = bpy.data.curves.new(name, 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = radius; cu.bevel_resolution = 4
    cu.use_fill_caps = True
    sp = cu.splines.new('POLY'); sp.points.add(len(pts) - 1)
    for i, p in enumerate(pts):
        sp.points[i].co = (*p, 1)
        if taper_end: sp.points[i].radius = 1.0 if i < len(pts) - 6 else max(0.05, (len(pts) - 1 - i) / 6)
    o = bpy.data.objects.new(name, cu); c.objects.link(o); cu.materials.append(m or steel())
    return o

def coil_pts(n=60, turns=1.5):
    """helix about Y through the origin, starting at the bottom (z=-R) going round to the top (z=+R) after 1.5 turns"""
    pts = []
    for i in range(n + 1):
        t = i / n; a = -math.pi / 2 - 2 * math.pi * turns * t      # start at bottom, wind backwards (toward -x first)
        pts.append((PIN_R * math.cos(a), -0.0012 + 0.0024 * t, PIN_R * math.sin(a)))
    return pts

def pin_parts(name, c, clasp=True):
    """body = fixed bottom leg + coil (+ clasp head), arm = pointed top leg (pivot = coil axis = body origin).
    Pin lies along +X in its local XZ plane. returns (body, arm)"""
    L = PIN_L
    cp = coil_pts()
    leg = [(L * u, -0.0012, -PIN_R) for u in [i / 20 for i in range(20, 0, -1)]]
    body_pts = leg + cp[1:]
    body = poly_curve(name + "_Body", c, body_pts)
    arm_pts = [(0.0005 + (L - 0.006) * i / 30, 0.0012, PIN_R - 0.0013 * i / 30) for i in range(31)]
    arm = poly_curve(name + "_Arm", c, arm_pts, taper_end=True)
    arm.parent = body
    if clasp:   # folded clasp head over the leg end: a rounded hood open toward +Y/up for the point
        bm = bmesh.new()
        prof = []
        for i in range(25):   # U profile in YZ around the leg end
            a = math.pi * (0.5 + 1.3 * i / 24)
            prof.append((0.0042 * math.cos(a) * 0.9, PIN_R * 0.25 + 0.0062 * math.sin(a)))
        ring0 = [bm.verts.new((L - 0.0085, y, z - PIN_R * 0.55)) for y, z in prof]
        ring1 = [bm.verts.new((L + 0.0012, y, z - PIN_R * 0.55)) for y, z in prof]
        for i in range(len(prof) - 1):
            bm.faces.new((ring0[i], ring0[i + 1], ring1[i + 1], ring1[i]))
        end = bm.faces.new(list(reversed(ring1))) if False else None
        me = bpy.data.meshes.new(name + "_Clasp"); bm.to_mesh(me); bm.free()
        cl = bpy.data.objects.new(name + "_Clasp", me); c.objects.link(cl); me.materials.append(steel())
        so = cl.modifiers.new("Solid", 'SOLIDIFY'); so.thickness = 0.0007
        sb = cl.modifiers.new("Sub", 'SUBSURF'); sb.levels = 2; sb.render_levels = 2
        cl.parent = body
    return body, arm

def straight_pin(name, c, L=0.034):
    """dressmaker's straight pin with a small round head (pivot at the head)"""
    o = poly_curve(name, c, [(0, 0, -L * i / 24) for i in range(25)], radius=0.00045, taper_end=True)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.0019, location=(0, 0, 0.0008)); h = bpy.context.object; h.name = name + "_Head"
    link(h, c); h.data.materials.append(steel()); h.parent = o
    for p in h.data.polygons: p.use_smooth = True
    return o

def wire_morph(name, c):
    """a piece of wire: shape key 'Pin' bends a straight 0.13 m wire into the pin shape (coil + two legs).
    returns (obj, end_A(straight), end_A(pin), end_B(straight), end_B(pin)) in object space"""
    L = PIN_L; cp = coil_pts(80)
    leg = [(L * u, -0.0012, -PIN_R) for u in [i / 30 for i in range(30, 0, -1)]]
    arm = [(0.0005 + (L - 0.006) * i / 30, 0.0012, PIN_R - 0.0013 * i / 30) for i in range(1, 31)]
    pin = [Vector(p) for p in leg + cp[1:] + arm]
    s = [0.0]
    for a, b in zip(pin, pin[1:]): s.append(s[-1] + (b - a).length)
    tot = s[-1]
    straight = [Vector((L * 0.5 - tot / 2 + si, 0, 0)) for si in s]    # same arc length, centred under the pin
    o = poly_curve(name, c, [tuple(p) for p in straight])
    o.shape_key_add(name="Basis")
    k = o.shape_key_add(name="Pin")
    for i, p in enumerate(pin): k.data[i].co = p
    return o, straight[0], pin[0], straight[-1], pin[-1]

def pin_heap(name, c, src_body, size=(0.30, 0.22), z=0.0, count=900, seed=3):
    """open-box filling: a mound of instanced safety pins (geometry nodes on a domed grid)"""
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=16, y_subdivisions=16, size=1, location=(0, 0, 0))
    g = bpy.context.object; g.name = name; link(g, c); g.scale = (size[0], size[1], 1)
    bpy.ops.object.transform_apply(scale=True)
    for v in g.data.vertices:
        u = (v.co.x / size[0]) * 2; w = (v.co.y / size[1]) * 2
        v.co.z = 0.05 * max(0.0, 1 - 0.6 * (u * u + w * w)) + 0.004 * math.sin(30 * v.co.x + seed) * math.cos(27 * v.co.y)
    g.location.z = z
    g.data.materials.append(mat("HeapBase", (0.55, 0.57, 0.6), 0.35, 1.0))
    ng = bpy.data.node_groups.get("PinHeapGN")
    if ng is None:
        ng = bpy.data.node_groups.new("PinHeapGN", 'GeometryNodeTree')
        ng.interface.new_socket("Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
        ng.interface.new_socket("Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')
        N = ng.nodes; Ln = ng.links
        gi = N.new("NodeGroupInput"); go = N.new("NodeGroupOutput")
        dist = N.new("GeometryNodeDistributePointsOnFaces"); dist.inputs["Density"].default_value = 9000; dist.name = "Dist"
        oi = N.new("GeometryNodeObjectInfo"); oi.name = "PinObj"; oi.transform_space = 'ORIGINAL'
        rr = N.new("FunctionNodeRandomValue"); rr.data_type = 'FLOAT_VECTOR'
        vin = [i for i in rr.inputs if i.type == 'VECTOR']; vin[0].default_value = (0, 0, 0); vin[1].default_value = (6.28, 6.28, 6.28)
        vout = [o for o in rr.outputs if o.type == 'VECTOR'][0]
        inst = N.new("GeometryNodeInstanceOnPoints")
        sc_ = N.new("FunctionNodeRandomValue"); sc_.data_type = 'FLOAT'
        fin = [i for i in sc_.inputs if i.type == 'VALUE']; fin[0].default_value = 0.85; fin[1].default_value = 1.1
        fout = [o for o in sc_.outputs if o.type == 'VALUE'][0]
        real = N.new("GeometryNodeRealizeInstances"); jo = N.new("GeometryNodeJoinGeometry")
        Ln.new(gi.outputs[0], dist.inputs["Mesh"]); Ln.new(dist.outputs["Points"], inst.inputs["Points"])
        Ln.new(oi.outputs["Geometry"], inst.inputs["Instance"]); Ln.new(vout, inst.inputs["Rotation"])
        Ln.new(fout, inst.inputs["Scale"])
        Ln.new(gi.outputs[0], jo.inputs[0]); Ln.new(inst.outputs[0], jo.inputs[0]); Ln.new(jo.outputs[0], go.inputs[0])
    mo = g.modifiers.new("Pins", 'NODES'); mo.node_group = ng
    ng.nodes["PinObj"].inputs[0].default_value = src_body
    return g

def tube_mesh(name, c, shapes, radius=WIRE, sides=8, m=None):
    """mesh tube along polyline shapes[0]; extra polylines (same point count) become shape keys named S1, S2..."""
    def ring_frames(pts):
        T = [(pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]).normalized() for i in range(len(pts))]
        n = T[0].orthogonal().normalized(); out = []
        for t in T:
            n = (n - t * n.dot(t)).normalized(); out.append((t, n, t.cross(n)))
        return out
    def verts(pts):
        pts = [Vector(p) for p in pts]; fr = ring_frames(pts); vs = []
        for p, (t, n, b) in zip(pts, fr):
            for k in range(sides):
                a = 2 * math.pi * k / sides; vs.append(p + (n * math.cos(a) + b * math.sin(a)) * radius)
        return vs
    v0 = verts(shapes[0]); N = len(shapes[0])
    faces = []
    for i in range(N - 1):
        for k in range(sides):
            a = i * sides + k; b = i * sides + (k + 1) % sides
            faces.append((a, b, b + sides, a + sides))
    faces.append(tuple(range(sides))[::-1]); faces.append(tuple((N - 1) * sides + k for k in range(sides)))
    me = bpy.data.meshes.new(name); me.from_pydata([tuple(v) for v in v0], [], faces); me.update()
    o = bpy.data.objects.new(name, me); c.objects.link(o); me.materials.append(m or steel())
    for p in me.polygons: p.use_smooth = True
    if len(shapes) > 1:
        o.shape_key_add(name="Basis")
        for j, sh in enumerate(shapes[1:]):
            k = o.shape_key_add(name="S%d" % (j + 1)); vs = verts(sh)
            for i, v in enumerate(vs): k.data[i].co = v
    return o

def twist_wire(name, c, half=0.035):
    """straight wire between (-half,0,0) and (+half,0,0); shape S1 winds a 1.5-turn coil (axis Y) into its middle,
    ends stay where the fingers pinch them"""
    n = 160; t0, t1 = 0.36, 0.64; xc = 0.0; k = 0.22
    def coil_pt(t):
        u = (t - t0) / (t1 - t0); a = 2 * math.pi * 1.5 * u; x_lin = -half + 2 * half * t
        return Vector((xc + (x_lin - xc) * k - PIN_R * math.sin(a), -0.0016 + 0.0032 * u, PIN_R * (1 - math.cos(a))))
    A = coil_pt(t0); B = coil_pt(t1)
    straight = []; coil = []
    for i in range(n + 1):
        t = i / n; straight.append(Vector((-half + 2 * half * t, 0, 0)))
        if t < t0: coil.append(Vector((-half, 0, 0)).lerp(A, t / t0))
        elif t > t1: coil.append(B.lerp(Vector((half, 0, 0)), (t - t1) / (1 - t1)))
        else: coil.append(coil_pt(t))
    return tube_mesh(name, c, [straight, coil])

def to_mesh(obj):
    """convert a curve object (and its curve children) to mesh in place, keeping names/parents"""
    for o in [obj] + [ch for ch in obj.children_recursive if ch.type == 'CURVE']:
        if o.type != 'CURVE': continue
        dg = bpy.context.evaluated_depsgraph_get(); me = bpy.data.meshes.new_from_object(o.evaluated_get(dg))
        nm = o.name; mw = o.matrix_world.copy(); par = o.parent; kids = list(o.children); cols = list(o.users_collection)
        new = bpy.data.objects.new(nm + "_m", me)
        for c_ in cols: c_.objects.link(new)
        new.parent = par; new.matrix_world = mw
        for k in kids: km = k.matrix_world.copy(); k.parent = new; k.matrix_world = km
        bpy.data.objects.remove(o); new.name = nm
        for p in me.polygons: p.use_smooth = True
        if o is obj: obj = new
    return obj
