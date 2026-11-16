"""NeverBathed sets (one scene, areas far apart). blender -b chars.blend --python 02_sets.py -- <models_dir> <logo_png> <out.blend>
V  village lane  (origin): mud-brick houses both sides, the hermit's house (open door + lit interior), stone water trough,
                            logo crate, bath courtyard with a tin tub and a wooden bucket at the lane's far end.
D  desert edge   (x=+200): his shallow pit with the dug-out mound and a planted shovel, campfire, seat rock, dung cakes,
                            the pipe; the village skyline 40 m away.
R  dirt road     (x=-200): a dusty track with tyre ruts and a dead hare on the verge (no blood)."""
import sys, os, math, random
import bpy, bmesh
from mathutils import Vector, Matrix, noise
V = Vector
a = sys.argv[sys.argv.index("--") + 1:]; MD, LOGO, OUT = a[0], a[1], a[2]
sc = bpy.context.scene; R_ = math.radians
DX, RX = 200.0, -200.0
sc["DX"] = DX; sc["RX"] = RX
rnd = random.Random(11)

def coll(name):
    c = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if c.name not in sc.collection.children: sc.collection.children.link(c)
    return c
C = {k: coll(k) for k in ("SET_V", "SET_D", "SET_R", "PROPS", "LIGHTS")}
def link(o, c):
    for u in list(o.users_collection): u.objects.unlink(o)
    C[c].objects.link(o)

# ------------------------------------------------------------------ materials
def mat(name, rgb, rough=0.7, metal=0.0, noise_scale=0.0, var=0.12, bump=0.0, emit=None, alpha=None):
    m = bpy.data.materials.get(name)
    if m: return m
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; P = nt.nodes["Principled BSDF"]
    P.inputs['Base Color'].default_value = (*rgb, 1); P.inputs['Roughness'].default_value = rough; P.inputs['Metallic'].default_value = metal
    if noise_scale:
        tc = nt.nodes.new('ShaderNodeTexCoord'); no = nt.nodes.new('ShaderNodeTexNoise'); no.inputs['Scale'].default_value = noise_scale
        no.inputs['Detail'].default_value = 4.0
        mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'
        mx.inputs['A'].default_value = (*[c * (1 - var) for c in rgb], 1); mx.inputs['B'].default_value = (*[min(1, c * (1 + var)) for c in rgb], 1)
        nt.links.new(tc.outputs['Object'], no.inputs['Vector']); nt.links.new(no.outputs['Fac'], mx.inputs['Factor'])
        nt.links.new(mx.outputs['Result'], P.inputs['Base Color'])
        if bump:
            bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = bump; bp.inputs['Distance'].default_value = 0.02
            nt.links.new(no.outputs['Fac'], bp.inputs['Height']); nt.links.new(bp.outputs['Normal'], P.inputs['Normal'])
    if emit:
        P.inputs['Emission Color'].default_value = (*emit[0], 1); P.inputs['Emission Strength'].default_value = emit[1]
    if alpha is not None:
        P.inputs['Alpha'].default_value = alpha
    return m

M_PLASTER = mat("M_MudPlaster", (0.62, 0.40, 0.22), 0.85, noise_scale=1.6, var=0.1, bump=0.3)
M_PLASTER2 = mat("M_MudPlaster2", (0.70, 0.48, 0.28), 0.85, noise_scale=1.4, var=0.1, bump=0.3)
M_INT = mat("M_InteriorPlaster", (0.72, 0.55, 0.36), 0.9, noise_scale=2.0, var=0.06)
M_WOOD = mat("M_Wood", (0.30, 0.18, 0.09), 0.7, noise_scale=8.0, var=0.2, bump=0.2)
M_WOODL = mat("M_WoodLight", (0.50, 0.35, 0.20), 0.7, noise_scale=8.0, var=0.2, bump=0.2)
M_DOOR = mat("M_DoorBlue", (0.04, 0.20, 0.32), 0.6, noise_scale=6.0, var=0.12)
M_SAND = mat("M_Sand", (0.70, 0.50, 0.30), 0.9, noise_scale=0.35, var=0.1, bump=0.25)
M_SOIL = mat("M_DugSoil", (0.36, 0.24, 0.14), 0.95, noise_scale=3.0, var=0.18, bump=0.35)
M_ROCK = mat("M_Rock", (0.55, 0.47, 0.40), 0.8, noise_scale=3.0, var=0.18, bump=0.35)
M_STONE = mat("M_TroughStone", (0.62, 0.58, 0.52), 0.75, noise_scale=4.0, var=0.12, bump=0.3)
M_WATER = mat("M_Water", (0.20, 0.42, 0.50), 0.08)
M_WATER.node_tree.nodes["Principled BSDF"].inputs['Specular IOR Level'].default_value = 0.3
M_ROAD = mat("M_RoadDust", (0.50, 0.38, 0.27), 0.92, noise_scale=0.6, var=0.12, bump=0.25)
M_DUNG = mat("M_DungCake", (0.075, 0.05, 0.028), 0.98, noise_scale=25.0, var=0.35, bump=0.6)
M_POT = mat("M_ClayPot", (0.66, 0.36, 0.20), 0.65, noise_scale=5.0, var=0.08)
M_CLOTH = mat("M_Blanket", (0.16, 0.10, 0.06), 0.85, noise_scale=10.0, var=0.15)
M_SHRUB = mat("M_DryShrub", (0.45, 0.42, 0.22), 0.8, noise_scale=6.0, var=0.2)

def smooth(ob):
    for p in ob.data.polygons: p.use_smooth = True
def box(name, c, size, m, coll_, bevel=0.03, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=c, rotation=rot); o = bpy.context.active_object; o.name = name
    o.scale = size; bpy.ops.object.transform_apply(scale=True)
    if bevel:
        b = o.modifiers.new("Bev", 'BEVEL'); b.width = bevel; b.segments = 3
    o.data.materials.append(m); link(o, coll_); return o
def cyl(name, c, r, h, m, coll_, rot=(0, 0, 0), verts=24):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=h, location=c, rotation=rot); o = bpy.context.active_object
    o.name = name; o.data.materials.append(m); smooth(o); link(o, coll_); return o

# ------------------------------------------------------------------ ground: grid with gentle dunes, flat near the action
def ground(name, cx, cy, size, res, m, coll_, flat_r=8.0, amp=0.35, hole=None, ruts=None):
    bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=res, y_segments=res, size=size / 2)
    for v in bm.verts:
        x, y = v.co.x + cx, v.co.y + cy
        d = math.hypot(v.co.x, v.co.y); fall = min(1.0, max(0.0, (d - flat_r) / 25.0))
        z = amp * fall * (noise.noise(V((x / 14.0, y / 14.0, 0.3))) + 0.4 * noise.noise(V((x / 5.0, y / 5.0, 1.7))))
        z += 0.02 * noise.noise(V((x * 1.3, y * 1.3, 5.0)))
        if d > size * 0.3: z += (d - size * 0.3) * 0.06 * (0.6 + 0.4 * noise.noise(V((x / 30, y / 30, 2))))   # far dunes rise into the horizon
        if ruts:
            for rx_ in ruts:
                dd = abs(v.co.x - rx_)
                if dd < 0.18 and abs(v.co.y) < size * 0.3: z -= 0.035 * (1 - dd / 0.18)
        v.co.z = z
    if hole:
        hx0, hy0, hx1, hy1 = hole
        bmesh.ops.delete(bm, geom=[f for f in bm.faces if any(hx0 <= vv.co.x <= hx1 and hy0 <= vv.co.y <= hy1 for vv in f.verts)], context='FACES')
        for v in bm.verts:
            if math.hypot(v.co.x, v.co.y) < 7.0: v.co.z -= 0.03
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); o.location = (cx, cy, 0); me.materials.append(m); smooth(o); link(o, coll_)
    return o

# ------------------------------------------------------------------ mud-brick house
def house(name, x, y, w, d, h, coll_, door=None, door_open=False, m=M_PLASTER, windows=(), beams=True, yaw=0.0):
    """box house, door/window on its -X or +X face ('-x'/'+x'), parapet, protruding roof beams; door=(face, offset_along_y)"""
    parts = []
    body = box(name, (x, y, h / 2), (w, d, h), m, coll_, bevel=0.06); parts.append(body)
    par = box(name + "_parapet", (x, y, h + 0.12), (w + 0.04, d + 0.04, 0.24), m, coll_, bevel=0.05)
    inner = box(name + "_roofcut", (x, y, h + 0.2), (w - 0.3, d - 0.3, 0.3), m, coll_, bevel=0)
    bo = par.modifiers.new("cut", 'BOOLEAN'); bo.object = inner; bo.operation = 'DIFFERENCE'
    inner.hide_render = inner.hide_viewport = True
    if beams:
        n = max(2, int(d / 0.7))
        for i in range(n):
            yy = y - d / 2 + (i + 0.5) * d / n
            for sx in (-1, 1):
                cyl(name + "_beam%d%s" % (i, "ab"[sx > 0]), (x + sx * (w / 2 + 0.12), yy, h - 0.25), 0.07, 0.35, M_WOOD, coll_, rot=(0, R_(90), 0), verts=10)
    if door:
        face, off = door; sx = -1 if face == '-x' else 1
        fx = x + sx * w / 2
        cut = box(name + "_doorcut", (fx, y + off, 1.0), (1.0, 0.95, 2.0), m, coll_, bevel=0)
        cut.hide_render = cut.hide_viewport = True
        bo = body.modifiers.new("door", 'BOOLEAN'); bo.object = cut; bo.operation = 'DIFFERENCE'
        body.modifiers.move(len(body.modifiers) - 1, 0)
        # frame
        box(name + "_lintel", (fx + sx * 0.03, y + off, 2.05), (0.12, 1.15, 0.12), M_WOOD, coll_, bevel=0.01)
        for s2 in (-1, 1):
            box(name + "_jamb%d" % s2, (fx + sx * 0.03, y + off + s2 * 0.52, 1.0), (0.12, 0.1, 2.0), M_WOOD, coll_, bevel=0.01)
        leaf = box(name + "_door", (0, 0, 0), (0.05, 0.9, 1.95), M_DOOR, coll_, bevel=0.01)
        for k in range(4):
            pl = box(name + "_doorplank%d" % k, (0.03 * sx, -0.33 + k * 0.22, 0), (0.012, 0.02, 1.9), M_WOOD, coll_, bevel=0)
            pl.parent = leaf
        hinge = V((fx - sx * 0.05, y + off - 0.45, 0.99))
        if door_open:
            leaf.location = hinge; leaf.rotation_euler = (0, 0, R_(-sx * 100))
            leaf.location += V((0, 0.45, 0)); leaf.data.transform(Matrix.Translation(V((0, 0.0, 0))))
            # rotate about the hinge: place leaf centre 0.45 m from the hinge along its own width
            ang = R_(sx * 100)
            leaf.location = hinge + Matrix.Rotation(ang, 3, 'Z') @ V((0, 0.45, 0))
            # interior room behind the door (lit, never a black void)
            room = box(name + "_interior", (x, y, (h - 0.15) / 2 - 0.05), (w - 0.5, d - 0.5, h - 0.05), M_INT, coll_, bevel=0)
            room.modifiers.clear()
            body.modifiers.new("hollow", 'BOOLEAN').object = room
            body.modifiers[-1].operation = 'DIFFERENCE'
            room.hide_render = room.hide_viewport = True
            L = bpy.data.lights.new(name + "_lamp", 'POINT'); L.energy = 120; L.color = (1.0, 0.85, 0.65); L.shadow_soft_size = 0.4
            lo = bpy.data.objects.new(name + "_lamp", L); lo.location = (x, y, h - 0.6); link(lo, "LIGHTS"); C["LIGHTS"].objects.link(lo) if lo.name not in C["LIGHTS"].objects else None
            # inside: a rug, a clay pot, a shelf
            box(name + "_floor", (x, y, 0.0), (w - 0.5, d - 0.5, 0.01), M_INT, coll_, bevel=0)
            box(name + "_rug", (x + sx * 0.3, y, 0.01), (1.4, 1.0, 0.02), M_CLOTH, coll_, bevel=0)
            pot(name + "_ipot", (x - sx * (w / 2 - 0.6), y + 0.6, 0), 0.25, coll_)
        else:
            leaf.location = (fx + sx * 0.02, y + off, 0.99)
    for wf, wo, wz in windows:
        sx = -1 if wf == '-x' else 1; fx = x + sx * w / 2
        box(name + "_win%.1f" % wo, (fx + sx * 0.02, y + wo, wz), (0.08, 0.6, 0.6), M_WOOD, coll_, bevel=0.01)      # closed shutters
        box(name + "_winbar%.1f" % wo, (fx + sx * 0.065, y + wo, wz), (0.02, 0.04, 0.58), M_WOODL, coll_, bevel=0)
        box(name + "_sill%.1f" % wo, (fx + sx * 0.06, y + wo, wz - 0.33), (0.14, 0.72, 0.06), M_WOOD, coll_, bevel=0.01)
    return body

def pot(name, c, r, coll_):
    bm = bmesh.new()
    prof = [(0.25, 0.0), (0.7, 0.15), (1.0, 0.45), (0.9, 0.8), (0.5, 1.0), (0.55, 1.15), (0.5, 1.15)]
    segs = 24; rings = []
    for pr, pz in prof:
        rings.append([bm.verts.new((r * pr * math.cos(2 * math.pi * i / segs), r * pr * math.sin(2 * math.pi * i / segs), r * pz * 1.1)) for i in range(segs)])
    for ra, rb in zip(rings, rings[1:]):
        for i in range(segs): bm.faces.new((ra[i], ra[(i + 1) % segs], rb[(i + 1) % segs], rb[i]))
    bm.faces.new(rings[0][::-1])
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free(); o = bpy.data.objects.new(name, me); o.location = c
    me.materials.append(M_POT); smooth(o); link(o, coll_); return o

def rock(name, c, s, coll_, seed=0):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=1, location=c); o = bpy.context.active_object; o.name = name
    rr = random.Random(seed)
    for v in o.data.vertices:
        n = noise.noise(v.co * 1.6 + V((seed, 0, 0)))
        v.co *= 1 + 0.22 * n
    o.scale = (s * rr.uniform(0.9, 1.4), s * rr.uniform(0.8, 1.2), s * rr.uniform(0.45, 0.7)); bpy.ops.object.transform_apply(scale=True)
    o.data.materials.append(M_ROCK); smooth(o); link(o, coll_); return o

def shrub(name, c, s, coll_, seed=0):
    """dry desert shrub: many thin twigs (hair curves) from a point"""
    rr = random.Random(seed); strands = []
    for i in range(140):
        az = rr.uniform(0, 2 * math.pi); el = rr.uniform(R_(15), R_(80)); L = s * rr.uniform(0.5, 1.0)
        d = V((math.cos(az) * math.cos(el), math.sin(az) * math.cos(el), math.sin(el)))
        p = V((0, 0, 0)); seg = []
        for k in range(4):
            seg.append(p.copy()); d = (d + V((rr.uniform(-.3, .3), rr.uniform(-.3, .3), rr.uniform(-.2, .1)))).normalized(); p = p + d * L / 3
        strands.append(seg)
    cv = bpy.data.hair_curves.new(name); cv.add_curves([4] * len(strands))
    cv.attributes["position"].data.foreach_set("vector", [x for s_ in strands for q in s_ for x in q])
    rad = cv.attributes.get("radius") or cv.attributes.new("radius", 'FLOAT', 'POINT')
    rad.data.foreach_set("value", [x for _ in strands for x in (0.012 * s, 0.008 * s, 0.005 * s, 0.002 * s)])
    cv.materials.append(M_SHRUB); o = bpy.data.objects.new(name, cv); o.location = c; link(o, coll_); return o

# ------------------------------------------------------------------ imported models
def import_model(path, name, longest, coll_, up_fix=None):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    ms = [o for o in new if o.type == 'MESH']
    if len(ms) > 1:      # drop sky-dome / backdrop meshes shipped with some models (far larger than the rest)
        sz = {o: max(o.dimensions) * max(o.matrix_world.to_scale()) for o in ms}
        big = max(ms, key=lambda o: sz[o]); rest = [sz[o] for o in ms if o is not big]
        if sz[big] > 4 * max(rest):
            ms.remove(big); new = [o for o in new if o is not big]; bpy.data.objects.remove(big, do_unlink=True)
    for o in new:
        if o.type != 'MESH': continue
    bpy.ops.object.select_all(action='DESELECT')
    for o in ms: o.select_set(True)
    bpy.context.view_layer.objects.active = ms[0]
    if len(ms) > 1: bpy.ops.object.join()
    o = bpy.context.active_object
    o.parent = None; o.matrix_world = o.matrix_world.copy()
    bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    keep = o.name
    for x in list(bpy.data.objects):
        if x.name != keep and x.type != 'MESH' and x.parent is None and x.users_collection and x not in before:
            pass
    for x in [x for x in bpy.data.objects if x not in before and x.name != keep]:
        bpy.data.objects.remove(x, do_unlink=True)
    if up_fix: o.data.transform(up_fix); o.data.update()
    vs = [v.co for v in o.data.vertices]
    mn = V([min(v[i] for v in vs) for i in range(3)]); mx = V([max(v[i] for v in vs) for i in range(3)])
    s = longest / max(mx - mn)
    o.data.transform(Matrix.Scale(s, 4) @ Matrix.Translation(-V(((mn.x + mx.x) / 2, (mn.y + mx.y) / 2, mn.z))))
    o.data.update(); o.name = name; o.data.name = name; o.location = (0, 0, 0); o.rotation_mode = 'XYZ'; o.rotation_euler = (0, 0, 0); o.scale = (1, 1, 1)
    link(o, coll_); smooth(o)
    return o

# ================================================================== V: village lane
ground("V_Ground", 0, 0, 220, 220, M_SAND, "SET_V", flat_r=16.0, amp=0.5)
# lane runs along +Y; houses on both sides; the hermit's house is on the right (+x side) at y=3, its door faces -x
HX = 3.2
specs_L = [(-HX - 2.0, -9.0, 4.0, 5.0, 3.0), (-HX - 1.8, -3.2, 3.6, 5.2, 3.4), (-HX - 2.2, 2.6, 4.4, 5.0, 2.9), (-HX - 1.9, 8.4, 3.8, 5.4, 3.3), (-HX - 2.1, 14.5, 4.2, 5.5, 3.1)]
specs_R = [(HX + 1.9, -9.2, 3.8, 5.2, 3.2), (HX + 2.0, -3.4, 4.0, 5.0, 2.9), (HX + 1.8, 2.6, 3.6, 5.6, 3.1), (HX + 2.1, 8.6, 4.2, 5.0, 3.4), (HX + 2.0, 14.6, 4.0, 5.6, 3.0)]
for i, (x, y, w, d, h) in enumerate(specs_L):
    house("V_HouseL%d" % i, x, y, w, d, h, "SET_V", door=('+x', 0.8 if i % 2 else -0.9), m=M_PLASTER if i % 2 else M_PLASTER2,
          windows=[('+x', -1.4 if i % 2 else 1.3, 1.5)])
for i, (x, y, w, d, h) in enumerate(specs_R):
    if i == 2:   # the hermit's house: open door, lit interior
        house("V_Hermit", x, y, w, d, h, "SET_V", door=('-x', 0.0), door_open=True, m=M_PLASTER2, windows=[('-x', 1.9, 1.5)])
    else:
        house("V_HouseR%d" % i, x, y, w, d, h, "SET_V", door=('-x', -0.8 if i % 2 else 0.9), m=M_PLASTER if i % 2 == 0 else M_PLASTER2,
              windows=[('-x', 1.4 if i % 2 else -1.3, 1.5)])
# the back row (skyline) and a mud-brick watch tower
for i in range(10):
    x = rnd.choice([-1, 1]) * rnd.uniform(9.5, 22); y = rnd.uniform(-14, 26); h = rnd.uniform(2.6, 4.2)
    house("V_Back%d" % i, x, y, rnd.uniform(3.5, 5.5), rnd.uniform(4, 6), h, "SET_V", beams=(i % 2 == 0), m=M_PLASTER if i % 2 else M_PLASTER2,
          windows=[('-x' if x > 0 else '+x', 0.5, 1.6)])
tw = box("V_Tower", (-11.0, 24.0, 4.0), (2.6, 2.6, 8.0), M_PLASTER2, "SET_V", bevel=0.08)
box("V_TowerTop", (-11.0, 24.0, 8.2), (3.0, 3.0, 0.4), M_PLASTER2, "SET_V", bevel=0.05)
# far end: the lane opens into a small square (the bath courtyard at y~20)
# stone water trough against the left house (young hermit, shots 1a/1b)
TR = V((-HX + 0.45, -3.6, 0))
tro = box("V_Trough", (TR.x, TR.y, 0.32), (0.75, 1.6, 0.64), M_STONE, "SET_V", bevel=0.05)
inn = box("V_TroughCut", (TR.x, TR.y, 0.5), (0.55, 1.4, 0.5), M_STONE, "SET_V", bevel=0)
bo = tro.modifiers.new("cut", 'BOOLEAN'); bo.object = inn; bo.operation = 'DIFFERENCE'; tro.modifiers.move(1, 0)
inn.hide_render = inn.hide_viewport = True
wat = box("V_TroughWater", (TR.x, TR.y, 0.56), (0.55, 1.4, 0.01), M_WATER, "SET_V", bevel=0)
sc["TROUGH"] = (TR.x, TR.y, 0.565)
# clay pots, firewood, a bench along the lane
for i, (x, y) in enumerate([(-HX + 0.35, -5.3), (-HX + 0.4, -5.8), (HX - 0.35, 5.4), (HX - 0.3, -6.0), (-HX + 0.3, 10.2), (HX - 0.4, 11.0)]):
    pot("V_Pot%d" % i, (x, y, 0), rnd.uniform(0.18, 0.28), "SET_V")
for i in range(9):
    cyl("V_Firewood%d" % i, (HX - 0.3, -1.2 + (i % 3) * 0.13, 0.07 + (i // 3) * 0.12), 0.06, 0.9, M_WOODL, "SET_V", rot=(R_(90), 0, R_(rnd.uniform(-8, 8))), verts=10)
box("V_Bench", (-HX + 0.3, 6.8, 0.42), (0.4, 1.6, 0.08), M_WOOD, "SET_V", bevel=0.01)
for yy in (6.2, 7.4): box("V_BenchLeg%.1f" % yy, (-HX + 0.3, yy, 0.2), (0.35, 0.06, 0.4), M_WOOD, "SET_V", bevel=0.005)
# logo crates by the shop door (right side, y=-2.2): stacked, logo on the face toward the lane
crate = import_model(os.path.join(MD, "crate.glb"), "V_Crate", 0.6, "SET_V")
crate.location = (HX - 0.4, -1.95 - 0.0, 0.0); crate.rotation_euler = (0, 0, 0)
c2 = crate.copy(); c2.name = "V_Crate2"; C["SET_V"].objects.link(c2); c2.location = (HX - 0.4, -2.6, 0); c2.rotation_euler = (0, 0, R_(8))
c3 = crate.copy(); c3.name = "V_Crate3"; C["SET_V"].objects.link(c3); c3.location = (HX - 0.4, -2.25, 0.6); c3.rotation_euler = (0, 0, R_(-5))
lm = bpy.data.materials.new("M_Logo"); lm.use_nodes = True; nt = lm.node_tree; P = nt.nodes["Principled BSDF"]
im = bpy.data.images.load(LOGO); tx = nt.nodes.new('ShaderNodeTexImage'); tx.image = im
nt.links.new(tx.outputs['Color'], P.inputs['Base Color']); nt.links.new(tx.outputs['Alpha'], P.inputs['Alpha']); P.inputs['Roughness'].default_value = 0.8
lm.blend_method = 'BLEND' if hasattr(lm, 'blend_method') else None
bpy.ops.mesh.primitive_plane_add(size=1); lg = bpy.context.active_object; lg.name = "V_LogoDecal"
lg.scale = (0.54, 0.54 * 414 / 967, 1); bpy.ops.object.transform_apply(scale=True)
lg.rotation_euler = (R_(90), 0, R_(-90)); lg.data.materials.append(lm); link(lg, "SET_V")
lg.location = (HX - 0.4 - 0.318, -2.25 + 0.02, 0.6 + 0.3)
lg.parent = c3; lg.matrix_parent_inverse = c3.matrix_world.inverted()
# bath courtyard (far end of the lane): tin tub of water, wooden bucket, a low wall
tub = import_model(os.path.join(MD, "tub.glb"), "V_Tub", 1.85, "SET_V")
# the model's water surface is part of its mesh: split it off (the body sits IN the water; walls stay checkable)
bm = bmesh.new(); bm.from_mesh(tub.data)
wf = [f for f in bm.faces if abs(f.normal.z) > 0.97 and 0.30 < f.calc_center_median().z < 0.40]
bm.faces.index_update(); keep = {f.index for f in wf}
bm2 = bm.copy(); bmesh.ops.delete(bm, geom=wf, context='FACES')
bm2.faces.ensure_lookup_table(); bm2.faces.index_update()
bmesh.ops.delete(bm2, geom=[f for f in bm2.faces if f.index not in keep], context='FACES')
bm.to_mesh(tub.data); bm.free()
mw = bpy.data.meshes.new("V_TubWaterTop"); bm2.to_mesh(mw); bm2.free(); mw.materials.append(tub.data.materials[0])
wtop = bpy.data.objects.new("V_TubWaterTop", mw); link(wtop, "SET_V")
TUB = V((0.3, 19.5, 0)); tub.location = TUB; tub.rotation_euler = (0, 0, R_(0)); wtop.location = TUB
for s_ in tub.data.materials:
    if s_: s_.node_tree.nodes.get("Principled BSDF") and setattr(s_.node_tree.nodes["Principled BSDF"].inputs['Metallic'], 'default_value', 0.6)
sc["TUB"] = tuple(TUB)
bpy.context.view_layer.update(); _tb = [tub.matrix_world @ v.co for v in tub.data.vertices]
_x0, _x1 = min(p.x for p in _tb), max(p.x for p in _tb); _y0, _y1 = min(p.y for p in _tb), max(p.y for p in _tb); _z1 = max(p.z for p in _tb)
bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=1.0, depth=0.01, location=((_x0 + _x1) / 2, (_y0 + _y1) / 2, _z1 * 0.72))
tw_ = bpy.context.active_object; tw_.name = "V_TubWater"; tw_.scale = ((_x1 - _x0) / 2 * 0.86, (_y1 - _y0) / 2 * 0.80, 1)
M_SOAP = mat("M_BathWater", (0.55, 0.72, 0.78), 0.15, noise_scale=6.0, var=0.12)
tw_.data.materials.append(M_SOAP); link(tw_, "SET_V"); print("TUB", round(_x1 - _x0, 2), round(_y1 - _y0, 2), round(_z1, 2))
bucket = import_model(os.path.join(MD, "bucket.glb"), "Bucket", 0.36, "PROPS")
bucket.location = (TUB.x + 1.1, TUB.y - 0.3, 0)
box("V_CourtWall", (0, 23.5, 0.55), (9.0, 0.4, 1.1), M_PLASTER, "SET_V", bevel=0.05)

# ================================================================== D: desert edge (x = DX)
PIT = V((DX, 0.0, 0.0)); sc["PIT"] = tuple(PIT)
ground("D_Ground", DX, 0, 220, 200, M_SAND, "SET_D", flat_r=10.0, amp=0.6, hole=(-3.3, -2.3, 3.3, 2.3))
# pit insert: fine grid 4 x 3 m, edges at z=0, a shallow body-length hollow (2.0 x 0.8 m, 0.32 m deep)
bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=150, y_segments=120, size=1.0)
for v in bm.verts:
    v.co.x *= 4.6; v.co.y *= 3.6
    ex = (v.co.x / 1.05) ** 2 + (v.co.y / 0.45) ** 2
    d = max(0.0, 1.0 - ex) ** 0.6
    edge = min(1.0, (4.6 - abs(v.co.x)) / 0.6, (3.6 - abs(v.co.y)) / 0.6)
    v.co.z = -0.32 * d + 0.015 * noise.noise(V((v.co.x * 6, v.co.y * 6, 1))) * max(0, edge)
    # the dug-out mound along the +y side of the pit
    md = math.hypot(v.co.x / 1.2, (v.co.y - 0.95) / 0.32)
    if md < 1.0: v.co.z += 0.22 * (1 - md * md) * max(0, edge)
    if edge < 1.0: v.co.z -= 0.035 * (1 - max(0.0, edge))
me = bpy.data.meshes.new("D_Pit"); bm.to_mesh(me); bm.free()
pit = bpy.data.objects.new("D_Pit", me); pit.location = PIT; me.materials.append(M_SOIL); smooth(pit); link(pit, "SET_D")
# blend the pit insert into the sand smoothly: a per-vertex 'soil' weight drives a soil/sand mix in one material
me.materials.clear()
M_PITM = bpy.data.materials.new("M_PitBlend"); M_PITM.use_nodes = True; nt = M_PITM.node_tree; P = nt.nodes["Principled BSDF"]
ca = nt.nodes.new('ShaderNodeVertexColor'); ca.layer_name = "soil"
tc = nt.nodes.new('ShaderNodeTexCoord'); no = nt.nodes.new('ShaderNodeTexNoise'); no.inputs['Scale'].default_value = 3.0
mxa = nt.nodes.new('ShaderNodeMix'); mxa.data_type = 'RGBA'; mxa.inputs['A'].default_value = (0.30, 0.20, 0.11, 1); mxa.inputs['B'].default_value = (0.40, 0.27, 0.15, 1)
nt.links.new(tc.outputs['Object'], no.inputs['Vector']); nt.links.new(no.outputs['Fac'], mxa.inputs['Factor'])
mxb = nt.nodes.new('ShaderNodeMix'); mxb.data_type = 'RGBA'; mxb.inputs['A'].default_value = (0.70, 0.50, 0.30, 1)
nt.links.new(mxa.outputs['Result'], mxb.inputs['B']); nt.links.new(ca.outputs['Color'], mxb.inputs['Factor'])
nt.links.new(mxb.outputs['Result'], P.inputs['Base Color']); P.inputs['Roughness'].default_value = 0.92
me.materials.append(M_PITM)
col = me.color_attributes.new("soil", 'FLOAT_COLOR', 'POINT')
for v in me.vertices:
    c = v.co
    e1 = (c.x / 1.25) ** 2 + (c.y / 0.62) ** 2; e2 = math.hypot(c.x / 1.4, (c.y - 0.95) / 0.45)
    w = max(min(1.0, max(0.0, (1.35 - e1) / 0.5)), min(1.0, max(0.0, (1.25 - e2) / 0.4)))
    w = w * w * (3 - 2 * w)
    col.data[v.index].color = (w, w, w, 1)
# a folded blanket at the pit's head end, a water jug
box("D_Blanket", (PIT.x - 0.75, PIT.y + 0.0, -0.22), (0.35, 0.55, 0.08), M_CLOTH, "SET_D", bevel=0.03)
shovel = import_model(os.path.join(MD, "shovel.glb"), "D_Shovel", 1.15, "SET_D")
shovel.location = (PIT.x + 0.7, PIT.y + 1.0, -0.12); shovel.rotation_euler = (R_(-8), R_(6), R_(20))
FIRE = V((DX - 2.6, 2.8, 0)); sc["FIRE"] = tuple(FIRE)
camp = import_model(os.path.join(MD, "campfire.glb"), "D_Campfire", 0.75, "SET_D"); camp.location = FIRE
SEAT = V((DX - 2.6, 3.75, 0)); sc["SEAT"] = tuple(SEAT)
seat = rock("D_SeatRock", (SEAT.x, SEAT.y, 0.12), 0.32, "SET_D", seed=3)
_mz = max(v.co.z for v in seat.data.vertices)
for v in seat.data.vertices:          # a flat sitting top
    if v.co.z > 0.55 * _mz: v.co.z = 0.55 * _mz + (v.co.z - 0.55 * _mz) * 0.08
seat.location.z = 0.17
FLAT = V((DX - 3.7, 2.4, 0)); sc["FLAT"] = tuple(FLAT)
fr_ = rock("D_FlatRock", (FLAT.x, FLAT.y, 0.08), 0.42, "SET_D", seed=8)
for v in fr_.data.vertices:
    if v.co.z > 0.1: v.co.z = 0.1 + (v.co.z - 0.1) * 0.1
for i in range(6):     # dried dung cakes on the flat rock
    bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=rnd.uniform(0.05, 0.075), depth=0.016,
                                        location=(FLAT.x + 0.14 * math.cos(i) - 0.12, FLAT.y + 0.12 * math.sin(i * 1.7), 0.2 + 0.012 * (i % 2)),
                                        rotation=(R_(rnd.uniform(-8, 8)), R_(rnd.uniform(-8, 8)), 0))
    dc = bpy.context.active_object; dc.name = "D_Dung%d" % i
    for v in dc.data.vertices: v.co += V((0.006 * noise.noise(v.co * 30 + V((7, 0, 0))), 0.006 * noise.noise(v.co * 30 + V((0, 7, 0))), 0.006 * noise.noise(v.co * 40)))
    dc.data.materials.append(M_DUNG); smooth(dc); link(dc, "SET_D")
# flames: emissive flame tongues + a warm light (flicker is keyed in the shots)
M_FLAME = mat("M_Flame", (0.9, 0.25, 0.02), 0.5, emit=((1.0, 0.30, 0.02), 0.9))
for i in range(5):
    bpy.ops.mesh.primitive_cone_add(vertices=16, radius1=0.09 - 0.01 * (i % 3), depth=0.38 + 0.06 * (i % 2), location=(0, 0, 0))
    fl = bpy.context.active_object; fl.name = "D_Flame%d" % i
    for v in fl.data.vertices: v.co += V((0.02 * noise.noise(v.co * 9), 0.02 * noise.noise(v.co * 9 + V((3, 0, 0))), 0))
    fl.data.transform(Matrix.Translation(V((0, 0, 0.19))))
    fl.location = FIRE + V((0.08 * math.cos(i * 1.3), 0.08 * math.sin(i * 1.3), 0.12)); fl.scale = (0.75, 0.75, 0.75); fl.rotation_euler = (R_(rnd.uniform(-10, 10)), R_(rnd.uniform(-10, 10)), 0)
    fl.data.materials.append(M_FLAME); smooth(fl); link(fl, "SET_D")
L = bpy.data.lights.new("D_FireLight", 'POINT'); L.energy = 60; L.color = (1.0, 0.55, 0.2); L.shadow_soft_size = 0.2
lo = bpy.data.objects.new("D_FireLight", L); lo.location = FIRE + V((0, 0, 0.5)); C["LIGHTS"].objects.link(lo)
# rocks and dry shrubs scattered; the village skyline 40 m behind (-x side)
for i in range(30):
    ang = rnd.uniform(0, 2 * math.pi); r = rnd.uniform(5, 30)
    rock("D_Rock%d" % i, (DX + r * math.cos(ang), r * math.sin(ang), 0.05), rnd.uniform(0.15, 0.6), "SET_D", seed=20 + i)
for i in range(26):
    ang = rnd.uniform(0, 2 * math.pi); r = rnd.uniform(4, 28)
    shrub("D_Shrub%d" % i, (DX + r * math.cos(ang), r * math.sin(ang), 0), rnd.uniform(0.4, 0.9), "SET_D", seed=40 + i)
for i in range(9):
    house("D_FarHouse%d" % i, DX - 38 - rnd.uniform(0, 8), -16 + i * 4.2, rnd.uniform(3.5, 5), rnd.uniform(3.5, 4.5), rnd.uniform(2.6, 3.8), "SET_D",
          m=M_PLASTER if i % 2 else M_PLASTER2, beams=False, windows=[('+x', 0.3, 1.6)])

# ================================================================== R: dirt road (x = RX), the track runs along y
ground("R_Ground", RX, 0, 220, 220, M_ROAD, "SET_R", flat_r=12.0, amp=0.6, ruts=(-0.75, 0.75))
M_TRACK = mat("M_Track", (0.40, 0.29, 0.19), 0.95, noise_scale=1.2, var=0.15, bump=0.3)
M_RUT = mat("M_Rut", (0.28, 0.20, 0.13), 0.95, noise_scale=3.0, var=0.15)
bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=12, y_segments=300, size=1.0)
for v in bm.verts:
    v.co.x *= 1.6; v.co.y *= 70.0; v.co.z = 0.004 + 0.006 * noise.noise(V((v.co.x * 3, v.co.y * 3, 0)))
    if abs(abs(v.co.x) - 0.75) < 0.16: v.co.z -= 0.025
me = bpy.data.meshes.new("R_Track"); bm.to_mesh(me); bm.free(); tr_ = bpy.data.objects.new("R_Track", me); tr_.location = (RX, 0, 0)
me.materials.append(M_TRACK); me.materials.append(M_RUT); smooth(tr_); link(tr_, "SET_R")
for p in me.polygons:
    if abs(abs(p.center.x) - 0.75) < 0.12: p.material_index = 1
for i in range(12):
    ang = rnd.uniform(0, 2 * math.pi); r = rnd.uniform(5, 30)
    if abs(r * math.cos(ang)) < 3: continue
    rock("R_Rock%d" % i, (RX + r * math.cos(ang), r * math.sin(ang), 0.05), rnd.uniform(0.15, 0.5), "SET_R", seed=60 + i)
for i in range(18):
    x = rnd.choice([-1, 1]) * rnd.uniform(2.5, 20); y = rnd.uniform(-25, 25)
    shrub("R_Shrub%d" % i, (RX + x, y, 0), rnd.uniform(0.4, 0.8), "SET_R", seed=80 + i)
for i in range(14):    # wooden roadside posts
    cyl("R_Post%d" % i, (RX + 2.6, -24 + i * 4.0, 0.5), 0.05, 1.0, M_WOOD, "SET_R", verts=8)
hare = import_model(os.path.join(MD, "hare.glb"), "R_Hare", 0.42, "SET_R")
# lie the (sitting) hare on its side on the verge, eyes closed (eye area darkened by the fur texture already)
hare.rotation_euler = (0, R_(90), R_(75)); hare.location = (RX + 1.25, 0.0, 0.07)
hare.data.materials.clear(); hare.data.materials.append(mat("M_HareFur", (0.30, 0.20, 0.11), 0.85, noise_scale=40.0, var=0.25, bump=0.2))
for s_ in []:
    if s_ and s_.node_tree.nodes.get("Principled BSDF"):
        P = s_.node_tree.nodes["Principled BSDF"]
        if not P.inputs['Base Color'].links: P.inputs['Base Color'].default_value = (0.42, 0.30, 0.18, 1)
        else:
            src = P.inputs['Base Color'].links[0].from_socket; mx = s_.node_tree.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'
            mx.inputs['Factor'].default_value = 1.0; mx.inputs['B'].default_value = (0.55, 0.38, 0.22, 1)
            s_.node_tree.links.new(src, mx.inputs['A']); s_.node_tree.links.new(mx.outputs['Result'], P.inputs['Base Color'])
sc["HARE"] = tuple(hare.location)

# ================================================================== props
pipe = import_model(os.path.join(MD, "pipe.glb"), "Pipe", 0.17, "PROPS")
pipe.location = (FLAT.x + 0.12, FLAT.y - 0.15, 0.17)
twig = cyl("Twig", (0, 0, 0), 0.008, 0.42, M_WOODL, "PROPS", verts=8); twig.rotation_euler = (0, R_(90), 0)
bpy.context.view_layer.objects.active = twig; bpy.ops.object.transform_apply(rotation=True)
twig.location = (FIRE.x + 0.5, FIRE.y - 0.4, 0.03)
bpy.ops.mesh.primitive_cone_add(vertices=12, radius1=0.014, depth=0.065, location=(0, 0, 0)); tfl = bpy.context.active_object
tfl.name = "TwigFlame"; tfl.data.transform(Matrix.Translation(V((0, 0, 0.045))))
M_TFL = mat("M_TwigFlame", (1.0, 0.25, 0.0), 0.5, emit=((1.0, 0.22, 0.0), 1.6)); tfl.data.materials.append(M_TFL); link(tfl, "PROPS")
L = bpy.data.lights.new("TwigGlow", 'POINT'); L.energy = 2.0; L.color = (1.0, 0.55, 0.2); L.shadow_soft_size = 0.02
tgl = bpy.data.objects.new("TwigGlow", L); C["PROPS"].objects.link(tgl)
tfl.location = twig.location + V((0.21, 0, 0)); tfl.parent = twig; tfl.matrix_parent_inverse = twig.matrix_world.inverted()
tgl.location = tfl.location + V((0, 0, 0.05)); tgl.parent = twig; tgl.matrix_parent_inverse = twig.matrix_world.inverted()
# meat on a spit over the fire (6b), propped on two forked sticks: no hands
meat = bpy.data.objects.new("D_Meat", None)
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.08, location=(FIRE.x, FIRE.y, 0.55)); mt = bpy.context.active_object; mt.name = "D_Meat"
mt.scale = (1.5, 0.8, 0.75); bpy.ops.object.transform_apply(scale=True)
for v in mt.data.vertices: v.co += v.normal * 0.012 * noise.noise(v.co * 25)
mt.data.materials.append(mat("M_RoastMeat", (0.38, 0.17, 0.07), 0.45, noise_scale=20, var=0.25, bump=0.3)); smooth(mt); link(mt, "SET_D")
cyl("D_Spit", (FIRE.x, FIRE.y, 0.55), 0.008, 1.1, M_WOODL, "SET_D", rot=(0, R_(90), 0), verts=8)
for sx in (-1, 1):
    cyl("D_SpitPost%d" % sx, (FIRE.x + sx * 0.5, FIRE.y, 0.28), 0.015, 0.56, M_WOOD, "SET_D", verts=8)
    for k in (-1, 1):
        cyl("D_Fork%d%d" % (sx, k), (FIRE.x + sx * 0.5 + k * 0.025, FIRE.y, 0.6), 0.01, 0.1, M_WOOD, "SET_D", rot=(0, R_(k * 25), 0), verts=8)
for o in (mt,): o.hide_render = o.hide_viewport = False

# smoke puffs (pipe and hair singe) and flies: built here, animated in the shots
M_SMOKE = mat("M_Smoke", (0.62, 0.62, 0.65), 0.9, alpha=0.22)
for i in range(8):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=0.018, location=(0, 0, -50))
    p = bpy.context.active_object; p.name = "Smoke%d" % i; p.data.materials.append(M_SMOKE); smooth(p); link(p, "PROPS")
    p.visible_shadow = False
M_FLY = mat("M_Fly", (0.03, 0.03, 0.03), 0.3)
M_WING = mat("M_FlyWing", (0.8, 0.85, 0.9), 0.2, alpha=0.4)
for i in range(6):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=10, ring_count=6, radius=0.006, location=(0, 0, -50)); fly = bpy.context.active_object
    fly.name = "Fly%d" % i; fly.scale = (1.0, 1.8, 0.9); fly.data.materials.append(M_FLY); link(fly, "PROPS")
    for sx in (-1, 1):
        bpy.ops.mesh.primitive_plane_add(size=0.012, location=(sx * 0.007, 0, 0.004)); w = bpy.context.active_object
        w.name = "FlyWing%d%d" % (i, sx); w.data.materials.append(M_WING); link(w, "PROPS"); w.parent = fly

# ================================================================== world and sun
w = sc.world or bpy.data.worlds.new("World"); sc.world = w; w.use_nodes = True; nt = w.node_tree
for n in list(nt.nodes):
    if n.type != 'OUTPUT_WORLD': nt.nodes.remove(n)
OUTW = next(n for n in nt.nodes if n.type == 'OUTPUT_WORLD')
sky = nt.nodes.new('ShaderNodeTexSky')
for t in ('MULTIPLE_SCATTERING', 'NISHITA', 'SINGLE_SCATTERING', 'HOSEK_WILKIE'):
    try: sky.sky_type = t; break
    except Exception: pass
try:
    sky.sun_elevation = R_(42); sky.sun_rotation = R_(210); sky.altitude = 200
except Exception: pass
bg = nt.nodes.new('ShaderNodeBackground'); bg.name = "SkyBG"; bg.inputs['Strength'].default_value = 0.18
nt.links.new(sky.outputs['Color'], bg.inputs['Color']); nt.links.new(bg.outputs[0], OUTW.inputs['Surface'])
print("SKY", sky.sky_type)
SUN = bpy.data.lights.new("Sun", 'SUN'); SUN.energy = 2.6; SUN.angle = R_(3); SUN.color = (1.0, 0.95, 0.86)
so = bpy.data.objects.new("Sun", SUN); so.rotation_euler = (R_(48), 0, R_(210 - 180 + 15)); C["LIGHTS"].objects.link(so)
sc.view_settings.view_transform = 'AgX'; sc.view_settings.exposure = -0.9
for lk in ("AgX - Punchy", "Punchy"):
    try: sc.view_settings.look = lk; break
    except Exception: pass
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = 48; sc.cycles.adaptive_threshold = 0.05; sc.cycles.use_denoising = True
sc.render.resolution_x, sc.render.resolution_y = 1080, 1920; sc.render.fps = 60
sc.cycles.max_bounces = 6; sc.cycles.caustics_reflective = False; sc.cycles.caustics_refractive = False
sc.render.use_motion_blur = False
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print("SETS_OK")
