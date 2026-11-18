"""Part 3 props, real-scale and built in code: ship's boat, sextant case, food sack, pump brake (pivoted),
writing things (table, chair, lamp, inkwell, dip pen, letter), arrest notice with nails, sword and scabbard,
chemist's glassware, magnifying glass. Every prop is a closed solid with its own material."""
import math, random, os
import numpy as np
import bpy, bmesh
from mathutils import Vector, Matrix
import ship
import deveau as D
import crew


def _link(o, coll=None):
    (coll or bpy.context.scene.collection).objects.link(o) if o.name not in (coll or bpy.context.scene.collection).objects else None
    return o


def mat_wood(name, aid="dark_wooden_planks", scale=1.0, tint=None, wet=0.0):
    return ship.wood(aid, scale, wet=wet, tint=tint, name=name)


def M_at(loc, rot=(0, 0, 0)):
    from mathutils import Euler
    return Matrix.Translation(loc) @ Euler(rot).to_matrix().to_4x4()


def apply(o, M):
    o.matrix_world = M @ o.matrix_world
    return o


# ----------------------------------------------------------------------------- ship's boat (clinker, ~5.5 m)
def boat(name="boat", L=5.4, B=1.6, D_=0.62, mats=None, coll=None):
    """Double-ended clinker boat in local coords: bow +X, keel at z = 0, gunwale at z = D_.
    Returns dict(objs, floor_z, thwarts=[(x, z)], gunwale=z)."""
    mats = mats or {}
    paint = mats.get("hull") or ship.paint(name + "_paint", (0.45, 0.42, 0.36), rough=0.5, grime=0.5, chips=0.3)
    inner = mats.get("inner") or mat_wood(name + "_in", "weathered_planks", 1.0, tint=(0.85, 0.75, 0.6))
    ns, nt = 60, 14
    V = []; F = []
    for i in range(ns + 1):
        s = i / ns; x = (s - 0.5) * L
        e = abs(2 * s - 1)
        hb = B / 2 * (1 - e ** 2.2) ** 0.85
        sheer = D_ + 0.16 * e ** 2
        for j in range(nt + 1):
            tt = j / nt
            # section: round-bilged; clinker steps (strakes) as small stepped offsets
            ang = tt * math.pi / 2
            yy = hb * math.sin(ang) ** 0.75
            zz = sheer * (1 - math.cos(ang) ** 1.3)
            strake = (int(tt * 7) / 7.0)
            yy += 0.006 * ((tt * 7) % 1.0) * (1 - e)
            V.append((x, yy, zz))
    for i in range(ns):
        for j in range(nt):
            a = i * (nt + 1) + j
            F.append([a, a + nt + 1, a + nt + 2, a + 1])
    # mirror to port
    n0 = len(V)
    V += [(x, -y, z) for (x, y, z) in V]
    F += [[n0 + f[3], n0 + f[2], n0 + f[1], n0 + f[0]] for f in F]
    me = bpy.data.meshes.new(name + "_hull"); me.from_pydata(V, [], F); me.update()
    bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name + "_hull", me); _link(o, coll)
    me.polygons.foreach_set("use_smooth", [True] * len(me.polygons))
    so = o.modifiers.new("t", "SOLIDIFY"); so.thickness = 0.025; so.offset = 1
    me.materials.append(paint); me.materials.append(inner)
    so.material_offset = 1
    objs = [o]
    gun = D_
    # thwarts, floorboards, gunwale cap, stem posts
    fz = 0.12
    objs.append(ship.box(name + "_floor", (0, 0, fz), (L * 0.62, B * 0.5, 0.025), inner, coll=coll))
    th = []
    for xx in (-1.5, -0.3, 0.9):
        e = abs(2 * (xx / L + 0.5) - 1); hb = B / 2 * (1 - e ** 2.2) ** 0.85
        objs.append(ship.box(name + "_thwart", (xx, 0, gun - 0.2), (0.22, hb * 2 - 0.08, 0.04), inner, coll=coll))
        th.append((xx, gun - 0.18))
    for sgx in (1, -1):
        objs.append(ship.box(name + "_stem", (sgx * (L / 2 - 0.02), 0, D_ / 2 + 0.1), (0.07, 0.07, D_ + 0.35), paint, coll=coll))
    return dict(objs=objs, floor_z=fz + 0.013, thwarts=th, gunwale=gun, L=L, B=B, hull=o)


def oar(name, a, b, mat, r=0.022):
    o1 = ship.cyl(name, a, b, r, r * 0.9, mat, verts=10)
    d = (Vector(b) - Vector(a)).normalized()
    blade = ship.box(name + "_blade", Vector(b) + d * 0.32, (0.64, 0.13, 0.012), mat)
    blade.rotation_euler = d.to_track_quat('X', 'Z').to_euler()
    return [o1, blade]


# ----------------------------------------------------------------------------- the instruments and food
def sextant_case(name="sextant_case"):
    """Mahogany box with brass corners and a handle: 0.32 x 0.30 x 0.16 m, origin at the bottom centre."""
    wood = mat_wood(name + "_mahog", "dark_wooden_planks", 3.0, tint=(0.95, 0.55, 0.38))
    brass = D.brass_material(name + "_brass")
    objs = [ship.box(name, (0, 0, 0.08), (0.32, 0.30, 0.16), wood, bevel=0.006)]
    objs.append(ship.box(name + "_lid", (0, 0, 0.163), (0.322, 0.302, 0.008), wood, bevel=0.003))
    for sx in (-1, 1):
        for sy in (-1, 1):
            objs.append(ship.box(name + "_corner", (sx * 0.157, sy * 0.147, 0.08), (0.012, 0.012, 0.165), brass))
    bpy.ops.mesh.primitive_torus_add(major_radius=0.035, minor_radius=0.006, location=(0, 0, 0.172), rotation=(math.pi / 2, 0, 0))
    hd = bpy.context.active_object; hd.name = name + "_handle"; hd.data.materials.append(brass); objs.append(hd)
    objs.append(ship.box(name + "_lock", (0.0, -0.151, 0.14), (0.03, 0.004, 0.03), brass))
    return objs


def sack(name="sack", size=(0.24, 0.19, 0.42), seed=2):
    """Canvas food bag, tied at the neck: a lumpy displaced capsule."""
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=20, radius=1)
    o = bpy.context.active_object; o.name = name
    me = o.data; rng = random.Random(seed)
    for v in me.vertices:
        x, y, z = v.co
        neck = max(0.0, z - 0.55) / 0.45
        r = 1 - 0.75 * neck ** 1.5
        v.co = Vector((x * r, y * r, z))
        v.co.z = (v.co.z + 1) / 2
        v.co.z *= 1.0 + 0.05 * math.sin(x * 9 + seed)
    me.update()
    me.transform(Matrix.Diagonal((size[0], size[1], size[2], 1)))      # bake the size into the mesh
    for p in me.polygons:
        p.use_smooth = True
    tx = bpy.data.textures.new(name + "_lumps", "CLOUDS"); tx.noise_scale = 0.35
    d = o.modifiers.new("lumps", "DISPLACE"); d.texture = tx; d.strength = 0.02
    o.data.materials.append(ship.canvas(name + "_canvas", wet=0.3, dirt=0.6, color=(0.55, 0.47, 0.34)))
    tie = ship.cyl(name + "_tie", (0, 0, size[2] * 0.92), (0, 0, size[2] * 1.02), size[0] * 0.18, size[0] * 0.22,
                   ship.tarred_rope(name + "_rope", (0.2, 0.15, 0.09)), verts=12)
    return [o, tie]


# ----------------------------------------------------------------------------- pump brake (the see-saw handle)
def pump_brake(name, SHIP, angle_deg, mat):
    """Replaces the ship's fixed brake bar visually: a pivoted lever across the two pumps, rocked by the men.
    Returns (objects, handle end points in world (port, starboard))."""
    X = ship.MAIN_X + 0.9; z0 = ship.zdeck(ship.MAIN_X) + 1.15
    piv = SHIP @ Vector((X, 0, z0 + 0.12))
    a = math.radians(angle_deg)
    ends = []
    objs = []
    post = ship.box(name + "_post", SHIP @ Vector((X, 0, z0 - 0.45)), (0.16, 0.16, 1.15), mat)
    post.rotation_euler = SHIP.to_euler(); objs.append(post)
    for sg in (1, -1):
        end = SHIP @ Vector((X, sg * 1.25 * math.cos(a), z0 + 0.12 + sg * 1.25 * math.sin(a)))
        ends.append(end)
    bar = ship.cyl(name, ends[1], ends[0], 0.035, mat=mat, verts=12)
    objs.append(bar)
    # cross handles at each end
    fwd = (SHIP.to_3x3() @ Vector((1, 0, 0))).normalized()
    for e in ends:
        objs.append(ship.cyl(name + "_grip", e - fwd * 0.28, e + fwd * 0.28, 0.026, mat=mat, verts=10))
    return objs, ends, fwd


# ----------------------------------------------------------------------------- writing
def table(name, center, size=(1.0, 0.65, 0.74), mat=None):
    mat = mat or mat_wood(name + "_w", "dark_wooden_planks", 1.6, tint=(0.8, 0.5, 0.32))
    cx, cy, cz = center; w, d, h = size
    objs = [ship.box(name + "_top", (cx, cy, cz + h - 0.02), (w, d, 0.04), mat, bevel=0.004)]
    for sx in (-1, 1):
        for sy in (-1, 1):
            objs.append(ship.box(name + "_leg", (cx + sx * (w / 2 - 0.05), cy + sy * (d / 2 - 0.05), cz + (h - 0.04) / 2),
                                 (0.05, 0.05, h - 0.04), mat))
    objs.append(ship.box(name + "_apron", (cx, cy, cz + h - 0.09), (w - 0.1, d - 0.1, 0.1), mat))
    return objs


def chair(name, loc, heading_deg, mat=None, seat_h=0.45):
    mat = mat or mat_wood(name + "_w", "dark_wooden_planks", 1.6, tint=(0.7, 0.45, 0.3))
    R = Matrix.Translation(loc) @ Matrix.Rotation(math.radians(heading_deg), 4, 'Z')
    objs = []
    def b(c, s):
        o = ship.box(name, (0, 0, 0), s, mat); o.matrix_world = R @ Matrix.Translation(c); objs.append(o)
    b((0, 0, seat_h - 0.02), (0.42, 0.42, 0.04))
    for sx in (-1, 1):
        for sy in (-1, 1):
            b((sx * 0.18, sy * 0.18, (seat_h - 0.04) / 2), (0.035, 0.035, seat_h - 0.04))
    for sy in (-1, 1):
        b((-0.19, sy * 0.18, seat_h + 0.22), (0.035, 0.035, 0.46))
    b((-0.19, 0, seat_h + 0.42), (0.03, 0.4, 0.08))
    return objs


def oil_lamp(name, base_loc, flame_energy=18.0):
    """Brass table lamp with a glass chimney and a real flame light. Returns (objs, flame world point, light).
    Uses the Sketchfab 'Victorian Brass Oil Lamp' (CC-BY, see CREDITS) when available, else a built lamp."""
    if os.environ.get("SKETCHFAB", "1") != "0":
        try:
            import sketchfab as SF
            ob = SF.model("oil_lamp", name=name)
            ob.location = base_loc
            hgt = ob["dims"][2]
            fp = Vector(base_loc) + Vector((0, 0, 0.5 * hgt))
            fl = bpy.data.materials.new(name + "_flame"); fl.use_nodes = True; N = fl.node_tree.nodes; N.remove(N["Principled BSDF"])
            em = N.new("ShaderNodeEmission"); em.inputs['Color'].default_value = (1.0, 0.55, 0.18, 1); em.inputs['Strength'].default_value = 40
            fl.node_tree.links.new(em.outputs[0], N["Material Output"].inputs['Surface'])
            bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8, radius=0.008, location=fp)
            f = bpy.context.active_object; f.scale = (1, 1, 2.4); f.name = name + "_flame"; f.data.materials.append(fl)
            L = bpy.data.lights.new(name + "_light", 'POINT'); L.energy = flame_energy; L.color = (1.0, 0.62, 0.32); L.shadow_soft_size = 0.02
            lo = bpy.data.objects.new(name + "_light", L); bpy.context.scene.collection.objects.link(lo); lo.location = fp + Vector((0, 0, 0.015))
            return [ob, f], fp, lo
        except Exception as e:
            print("sketchfab lamp unavailable:", e)
    brass = D.brass_material(name + "_brass")
    glass = bpy.data.materials.new(name + "_glass"); glass.use_nodes = True
    g = glass.node_tree.nodes["Principled BSDF"]; g.inputs['Transmission Weight'].default_value = 1.0
    g.inputs['Roughness'].default_value = 0.05; g.inputs['Base Color'].default_value = (0.95, 0.9, 0.82, 1)
    x, y, z = base_loc
    objs = [ship.cyl(name + "_foot", (x, y, z), (x, y, z + 0.02), 0.07, 0.065, brass, verts=32),
            ship.cyl(name + "_stem", (x, y, z + 0.02), (x, y, z + 0.16), 0.02, 0.025, brass, verts=24)]
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, radius=0.065, location=(x, y, z + 0.2))
    fo = bpy.context.active_object; fo.scale = (1, 1, 0.75); fo.name = name + "_font"; fo.data.materials.append(brass); objs.append(fo)
    objs.append(ship.cyl(name + "_chimney", (x, y, z + 0.245), (x, y, z + 0.44), 0.032, 0.022, glass, verts=32, caps=False))
    fl = bpy.data.materials.new(name + "_flame"); fl.use_nodes = True; N = fl.node_tree.nodes; N.remove(N["Principled BSDF"])
    em = N.new("ShaderNodeEmission"); em.inputs['Color'].default_value = (1.0, 0.55, 0.18, 1); em.inputs['Strength'].default_value = 40
    fl.node_tree.links.new(em.outputs[0], N["Material Output"].inputs['Surface'])
    bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8, radius=0.008, location=(x, y, z + 0.275))
    f = bpy.context.active_object; f.scale = (1, 1, 2.4); f.name = name + "_flame"; f.data.materials.append(fl); objs.append(f)
    L = bpy.data.lights.new(name + "_light", 'POINT'); L.energy = flame_energy; L.color = (1.0, 0.62, 0.32); L.shadow_soft_size = 0.02
    lo = bpy.data.objects.new(name + "_light", L); bpy.context.scene.collection.objects.link(lo); lo.location = (x, y, z + 0.29)
    return objs, Vector((x, y, z + 0.28)), lo


def paper(name, loc, size=(0.21, 0.27), rot_z=0.0, text_img=None, curl=0.004):
    m = bpy.data.materials.new(name); m.use_nodes = True; p = m.node_tree.nodes["Principled BSDF"]
    p.inputs['Base Color'].default_value = (0.78, 0.72, 0.6, 1); p.inputs['Roughness'].default_value = 0.8
    p.inputs['Subsurface Weight'].default_value = 0.05
    if text_img:
        N = m.node_tree.nodes; Lk = m.node_tree.links
        t = N.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(text_img)
        mx = N.new("ShaderNodeMix"); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs['Factor'].default_value = 1
        mx.inputs[6].default_value = (0.78, 0.72, 0.6, 1); Lk.new(t.outputs['Color'], mx.inputs[7]); Lk.new(mx.outputs[2], p.inputs['Base Color'])
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=12, y_subdivisions=12, size=1)
    o = bpy.context.active_object; o.name = name
    for v in o.data.vertices:
        v.co.z = curl * (v.co.x * 2) ** 2
    o.scale = (size[0], size[1], 1); o.location = loc; o.rotation_euler = (0, 0, rot_z)
    so = o.modifiers.new("t", "SOLIDIFY"); so.thickness = 0.0003
    o.data.materials.append(m)
    return o


def inkwell(name, loc):
    glass = bpy.data.materials.new(name + "_g"); glass.use_nodes = True
    g = glass.node_tree.nodes["Principled BSDF"]; g.inputs['Base Color'].default_value = (0.02, 0.03, 0.05, 1); g.inputs['Roughness'].default_value = 0.08
    g.inputs['Coat Weight'].default_value = 1.0
    x, y, z = loc
    return [ship.cyl(name, (x, y, z), (x, y, z + 0.05), 0.035, 0.03, glass, verts=24),
            ship.cyl(name + "_neck", (x, y, z + 0.05), (x, y, z + 0.065), 0.014, 0.014, glass, verts=16)]


def dip_pen(name, tip, direction, length=0.18):
    """Wooden holder with a steel nib; tip = nib point (world), direction = from tip toward the back end."""
    d = Vector(direction).normalized()
    wood = crew.flat(name + "_w", (0.12, 0.05, 0.025), rough=0.4)
    steel = crew.flat(name + "_s", (0.5, 0.5, 0.5), rough=0.25, metal=1.0)
    a = Vector(tip); b = a + d * 0.025; c = a + d * length
    return [ship.cyl(name + "_nib", a, b, 0.0006, 0.0035, steel, verts=12), ship.cyl(name, b, c, 0.0045, 0.0038, wood, verts=12)]


# ----------------------------------------------------------------------------- the court and the inspection
def notice(name, loc, normal, up=(0, 0, 1), text_img=None):
    """The Admiralty marshal's arrest warrant, nailed to the mainmast."""
    n = Vector(normal).normalized(); u = Vector(up).normalized(); r = u.cross(n).normalized(); u = n.cross(r)
    o = paper(name, (0, 0, 0), size=(0.26, 0.36), text_img=text_img, curl=0.0)
    M = Matrix((r, u, n)).transposed().to_4x4(); M.translation = Vector(loc)
    o.matrix_world = M @ Matrix.Diagonal((0.26, 0.36, 1, 1))
    iron = ship.iron(name + "_nail")
    nails = []
    for sx, sy in ((-0.11, 0.16), (0.11, 0.16), (-0.11, -0.16), (0.11, -0.16)):
        p = Vector(loc) + r * sx + u * sy + n * 0.002
        nails.append(ship.cyl(name + "_nailhead", p, p + n * 0.004, 0.006, mat=iron, verts=10))
    return [o] + nails


def hammer(name, head_c, handle_dir, face_dir):
    iron = ship.iron(name + "_i"); wood = crew.flat(name + "_w", (0.25, 0.15, 0.08), rough=0.6)
    hd = Vector(handle_dir).normalized(); fd = Vector(face_dir).normalized()
    c = Vector(head_c)
    return [ship.cyl(name + "_head", c - fd * 0.05, c + fd * 0.06, 0.016, mat=iron, verts=12),
            ship.cyl(name + "_handle", c, c + hd * 0.32, 0.013, 0.015, wood, verts=10)]


def sword(name, hilt, direction, blade_len=0.78, rust=0.6):
    """A 19th-c. sword: steel blade (rust bloom), brass guard, leather-wrapped grip. hilt = guard centre."""
    d = Vector(direction).normalized()
    side = d.cross(Vector((0, 0, 1)))
    if side.length < 1e-3:
        side = d.cross(Vector((1, 0, 0)))
    side.normalize(); flat_n = d.cross(side).normalized()
    steel = bpy.data.materials.new(name + "_steel"); steel.use_nodes = True
    N = steel.node_tree.nodes; Lk = steel.node_tree.links; p = N["Principled BSDF"]
    p.inputs['Metallic'].default_value = 1.0; p.inputs['Base Color'].default_value = (0.55, 0.55, 0.55, 1); p.inputs['Roughness'].default_value = 0.25
    nz = N.new("ShaderNodeTexNoise"); nz.inputs['Scale'].default_value = 60; nz.inputs['Detail'].default_value = 8
    mr = N.new("ShaderNodeMapRange"); mr.inputs['From Min'].default_value = 0.62 - 0.2 * rust; mr.inputs['From Max'].default_value = 0.72 - 0.2 * rust
    Lk.new(nz.outputs['Fac'], mr.inputs['Value'])
    rustc = N.new("ShaderNodeMix"); rustc.data_type = 'RGBA'; rustc.inputs[6].default_value = (0.55, 0.55, 0.55, 1)
    rustc.inputs[7].default_value = (0.25, 0.08, 0.025, 1); Lk.new(mr.outputs[0], rustc.inputs['Factor']); Lk.new(rustc.outputs[2], p.inputs['Base Color'])
    inv = N.new("ShaderNodeMath"); inv.operation = 'SUBTRACT'; inv.inputs[0].default_value = 1.0; Lk.new(mr.outputs[0], inv.inputs[1])
    Lk.new(inv.outputs[0], p.inputs['Metallic'])
    rr = N.new("ShaderNodeMapRange"); rr.inputs['To Min'].default_value = 0.22; rr.inputs['To Max'].default_value = 0.85
    Lk.new(mr.outputs[0], rr.inputs['Value']); Lk.new(rr.outputs[0], p.inputs['Roughness'])
    brass = D.brass_material(name + "_brass"); leather = D.leather_material(name + "_lth", (0.05, 0.03, 0.02))
    # blade: a tapered flat bar (lofted quads), slight curve
    n = 24; V = []; F = []
    for i in range(n + 1):
        s = i / n; w = 0.016 * (1 - s) + 0.002; th = 0.0035 * (1 - 0.6 * s)
        c = Vector(hilt) + d * (0.01 + blade_len * s) + flat_n * 0.03 * s * s
        for (a, b) in ((w, 0), (0, th), (-w, 0), (0, -th)):
            V.append(c + side * a + flat_n * b)
    for i in range(n):
        for k in range(4):
            a = i * 4 + k; b2 = i * 4 + (k + 1) % 4
            F.append([a, b2, b2 + 4, a + 4])
    F.append([n * 4 + 3, n * 4 + 2, n * 4 + 1, n * 4]); F.append([0, 1, 2, 3])
    me = bpy.data.meshes.new(name + "_blade"); me.from_pydata([v[:] for v in V], [], F); me.update()
    bl = bpy.data.objects.new(name + "_blade", me); bpy.context.scene.collection.objects.link(bl); me.materials.append(steel)
    h = Vector(hilt)
    guard = ship.box(name + "_guard", h, (0.1, 0.02, 0.012), brass)
    guard.rotation_euler = Matrix((side, flat_n, d)).transposed().to_euler()
    grip = ship.cyl(name + "_grip", h, h - d * 0.11, 0.013, 0.014, leather, verts=12)
    pommel = ship.cyl(name + "_pommel", h - d * 0.11, h - d * 0.13, 0.017, 0.012, brass, verts=12)
    return [bl, guard, grip, pommel], steel


def scabbard(name, mouth, direction, length=0.8):
    d = Vector(direction).normalized()
    leather = D.leather_material(name + "_l", (0.06, 0.035, 0.02), rough=0.5, wet=0.2)
    brass = D.brass_material(name + "_b")
    a = Vector(mouth); b = a + d * length
    return [ship.cyl(name, a, b, 0.02, 0.012, leather, verts=12), ship.cyl(name + "_chape", b - d * 0.06, b, 0.013, 0.009, brass, verts=12),
            ship.cyl(name + "_locket", a, a + d * 0.05, 0.022, mat=brass, verts=12)]


def test_tube(name, base, height=0.15, r=0.008, liquid=None):
    glass = bpy.data.materials.new(name + "_g"); glass.use_nodes = True
    g = glass.node_tree.nodes["Principled BSDF"]; g.inputs['Transmission Weight'].default_value = 1.0; g.inputs['Roughness'].default_value = 0.02
    o = ship.cyl(name, base, Vector(base) + Vector((0, 0, height)), r, mat=glass, verts=24)
    so = o.modifiers.new("t", "SOLIDIFY"); so.thickness = 0.0008
    out = [o]
    if liquid:
        lm = bpy.data.materials.new(name + "_liq"); lm.use_nodes = True
        q = lm.node_tree.nodes["Principled BSDF"]; q.inputs['Transmission Weight'].default_value = 0.9; q.inputs['Base Color'].default_value = (*liquid, 1)
        q.inputs['Roughness'].default_value = 0.05
        out.append(ship.cyl(name + "_liq", Vector(base) + Vector((0, 0, 0.002)), Vector(base) + Vector((0, 0, height * 0.4)), r * 0.85, mat=lm, verts=24))
    return out


def magnifier(name, centre, normal, handle_dir, r=0.045):
    brass = D.brass_material(name + "_b"); wood = crew.flat(name + "_w", (0.1, 0.05, 0.03), rough=0.5)
    glass = bpy.data.materials.new(name + "_g"); glass.use_nodes = True
    g = glass.node_tree.nodes["Principled BSDF"]; g.inputs['Transmission Weight'].default_value = 1.0; g.inputs['Roughness'].default_value = 0.0
    n = Vector(normal).normalized(); c = Vector(centre)
    Mq = n.to_track_quat('Z', 'Y').to_matrix().to_4x4(); Mq.translation = c
    bpy.ops.mesh.primitive_torus_add(major_radius=r, minor_radius=0.004, major_segments=40)
    ring = bpy.context.active_object; ring.name = name; ring.matrix_world = Mq; ring.data.materials.append(brass)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, radius=1)
    lens = bpy.context.active_object; lens.name = name + "_lens"; lens.matrix_world = Mq @ Matrix.Diagonal((r, r, 0.006, 1))
    lens.data.materials.append(glass)
    hd = Vector(handle_dir).normalized()
    hs = c + hd * r
    handle = ship.cyl(name + "_handle", hs, hs + hd * 0.11, 0.008, 0.01, wood, verts=12)
    return [ring, lens, handle]


# ----------------------------------------------------------------------------- stains in the deck grain
def stain_decal_mat(base_mat, centres, radius=0.06):
    """Add darker, reddish-brown stains soaked into a wood material at given object-space points."""
    m = base_mat.copy(); m.name = base_mat.name + "_stain"
    N = m.node_tree.nodes; L = m.node_tree.links
    p = next(n for n in N if n.type == 'BSDF_PRINCIPLED')
    src = p.inputs['Base Color'].links[0].from_socket if p.inputs['Base Color'].links else None
    geo = N.new("ShaderNodeNewGeometry")
    acc = None
    for i, c in enumerate(centres):
        vd = N.new("ShaderNodeVectorMath"); vd.operation = 'DISTANCE'; vd.inputs[1].default_value = c
        L.new(geo.outputs['Position'], vd.inputs[0])
        nz = N.new("ShaderNodeTexNoise"); nz.inputs['Scale'].default_value = 30; nz.inputs['Detail'].default_value = 6
        L.new(geo.outputs['Position'], nz.inputs['Vector'])
        ad = N.new("ShaderNodeMath"); ad.operation = 'MULTIPLY_ADD'; ad.inputs[1].default_value = radius * 0.6
        L.new(nz.outputs['Fac'], ad.inputs[0]); L.new(vd.outputs['Value'], ad.inputs[2])
        mr = N.new("ShaderNodeMapRange"); mr.inputs['From Min'].default_value = radius * 1.1; mr.inputs['From Max'].default_value = radius * 0.6
        L.new(ad.outputs[0], mr.inputs['Value'])
        if acc is None:
            acc = mr.outputs[0]
        else:
            mx = N.new("ShaderNodeMath"); mx.operation = 'MAXIMUM'; L.new(acc, mx.inputs[0]); L.new(mr.outputs[0], mx.inputs[1]); acc = mx.outputs[0]
    mul = N.new("ShaderNodeMix"); mul.data_type = 'RGBA'; mul.blend_type = 'MULTIPLY'
    if src:
        L.new(src, mul.inputs[6])
    else:
        mul.inputs[6].default_value = p.inputs['Base Color'].default_value
    mul.inputs[7].default_value = (0.16, 0.055, 0.04, 1)
    k = N.new("ShaderNodeMath"); k.operation = 'MULTIPLY'; k.inputs[1].default_value = 0.95; L.new(acc, k.inputs[0])
    L.new(k.outputs[0], mul.inputs['Factor']); L.new(mul.outputs[2], p.inputs['Base Color'])
    return m
