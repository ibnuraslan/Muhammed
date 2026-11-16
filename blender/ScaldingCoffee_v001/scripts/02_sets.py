"""B09 ScaldingCoffee: build all sets into one file.  blender -b --python 02_sets.py -- out.blend
SetCar x=0, SetCafe x=40, SetHosp x=80, SetBoard x=120 (metres). Real models (CC-BY Sketchfab via Objaverse, CC0 Poly Haven)
plus our own cups, steam, dial, counter and rooms."""
import bpy, bmesh, sys, math, os
from mathutils import Vector, Matrix
W = "/tmp/claude-0/b09/"
A = W + "assets/"
BRAND = "/home/user/Muhammed/blender/assets/brand/"
OUT = sys.argv[sys.argv.index("--") + 1]
R_ = math.radians
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
exec(open(W + "scripts/teal_fix.py").read().split('if __name__')[0])

def col(name):
    c = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if c.name not in sc.collection.children: sc.collection.children.link(c)
    return c

def mat(name, rgb, rough=0.5, metal=0.0, emit=None, alpha=1.0, coat=0.0):
    m = bpy.data.materials.get(name)
    if m: return m
    m = bpy.data.materials.new(name); m.use_nodes = True
    P = m.node_tree.nodes["Principled BSDF"]
    P.inputs["Base Color"].default_value = (*rgb, 1); P.inputs["Roughness"].default_value = rough
    P.inputs["Metallic"].default_value = metal
    P.inputs["Coat Weight"].default_value = coat
    if emit: P.inputs["Emission Color"].default_value = (*emit[0], 1); P.inputs["Emission Strength"].default_value = emit[1]
    if alpha < 1: P.inputs["Alpha"].default_value = alpha
    return m

def alive(lst):
    out = []
    for o in lst:
        try: o.name; out.append(o)
        except ReferenceError: pass
    return out

def link(o, c):
    for cc in o.users_collection: cc.objects.unlink(o)
    c.objects.link(o)

def box(name, c, loc, size, m, bevel=0.01, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot); o = bpy.context.object; o.name = name
    o.scale = size; bpy.ops.object.transform_apply(scale=True)
    if bevel:
        b = o.modifiers.new("Bevel", 'BEVEL'); b.width = bevel; b.segments = 3; b.limit_method = 'ANGLE'
    o.data.materials.append(m); link(o, c)
    for p in o.data.polygons: p.use_smooth = True
    return o

def plane(name, c, loc, size, m, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_plane_add(size=1, location=loc, rotation=rot); o = bpy.context.object; o.name = name
    o.scale = (size[0], size[1], 1); bpy.ops.object.transform_apply(scale=True); o.data.materials.append(m); link(o, c); return o

def import_glb(path, name, c, scale=1.0, loc=(0, 0, 0), rotz=0.0, keep=None):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    root = bpy.data.objects.new(name, None); c.objects.link(root)
    for o in new:
        link(o, c)
        if o.parent is None: o.parent = root
    meshes = [o for o in new if o.type == 'MESH']
    if keep is not None:
        for o in meshes:
            if not keep(o): bpy.data.objects.remove(o)
        meshes = alive(meshes)
    root.scale = (scale,) * 3; root.location = loc; root.rotation_euler.z = rotz
    bpy.context.view_layer.update()
    return root, meshes

def bounds(obs):
    mn = Vector((1e9,) * 3); mx = Vector((-1e9,) * 3)
    for o in obs:
        for cc in o.bound_box:
            w = o.matrix_world @ Vector(cc); mn = Vector(map(min, mn, w)); mx = Vector(map(max, mx, w))
    return mn, mx

def lathe(name, c, prof, m, loc, segs=48, cap_bottom=True):
    """prof: list of (r, z) bottom->top; returns mesh object revolved around Z"""
    bm = bmesh.new(); rings = []
    for r, z in prof:
        ring = [bm.verts.new((r * math.cos(2 * math.pi * i / segs), r * math.sin(2 * math.pi * i / segs), z)) for i in range(segs)]
        rings.append(ring)
    for a, b in zip(rings, rings[1:]):
        for i in range(segs):
            bm.faces.new((a[i], a[(i + 1) % segs], b[(i + 1) % segs], b[i]))
    if cap_bottom and prof[0][0] > 0: bm.faces.new(list(reversed(rings[0])))
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); c.objects.link(o); o.location = loc
    for p in me.polygons: p.use_smooth = True
    me.materials.append(m); return o

def logo_mat(name, dark=True):
    m = bpy.data.materials.get(name)
    if m: return m
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; P = nt.nodes["Principled BSDF"]
    t = nt.nodes.new("ShaderNodeTexImage")
    t.image = bpy.data.images.load(BRAND + ("DaKrasFilms_logo_dark.png" if dark else "DaKrasFilms_logo_white.png"))
    t.extension = 'CLIP'
    nt.links.new(t.outputs["Color"], P.inputs["Base Color"]); nt.links.new(t.outputs["Alpha"], P.inputs["Alpha"])
    P.inputs["Roughness"].default_value = 0.4
    m.blend_method = 'HASHED' if hasattr(m, "blend_method") else None
    return m

# ------------------------------------------------------------------ shared: paper cup, lid, coffee, steam
CUP_H = 0.118; CUP_R0 = 0.029; CUP_R1 = 0.044
def paper_cup(name, c, loc, with_logo=False):
    m_cup = mat("PaperCup", (0.95, 0.94, 0.9), 0.45)
    prof = [(CUP_R0, 0.0)] + [(CUP_R0 + (CUP_R1 - CUP_R0) * t / 10, CUP_H * t / 10) for t in range(1, 11)]
    outer = lathe(name, c, prof, m_cup, loc)
    sol = outer.modifiers.new("Solid", 'SOLIDIFY'); sol.thickness = 0.0012; sol.offset = -1
    # sleeve band (warm brown) as a second, slightly larger lathe
    band = lathe(name + "_Band", c, [(CUP_R0 + (CUP_R1 - CUP_R0) * t + 0.0008, CUP_H * t) for t in (0.28, 0.5, 0.72)],
                 mat("CupBand", (0.55, 0.28, 0.12), 0.5), (0, 0, 0), cap_bottom=False)
    band.parent = outer
    rim = bpy.data.meshes.new(name + "_RimM"); bm = bmesh.new()
    bmesh.ops.create_circle(bm, segments=48, radius=CUP_R1); bm.to_mesh(rim); bm.free()
    bpy.ops.mesh.primitive_torus_add(major_radius=CUP_R1 + 0.0005, minor_radius=0.0018, major_segments=48, minor_segments=8,
                                     location=(0, 0, CUP_H))
    r = bpy.context.object; r.name = name + "_Rim"; r.data.materials.append(m_cup); link(r, c); r.parent = outer
    for p in r.data.polygons: p.use_smooth = True
    coffee = lathe(name + "_Coffee", c, [(CUP_R0 + (CUP_R1 - CUP_R0) * 0.88, CUP_H * 0.88 - 0.0002), (0.0, CUP_H * 0.88)],
                   mat("Coffee", (0.11, 0.05, 0.02), 0.08, coat=0.0), (0, 0, 0), cap_bottom=False)
    coffee.parent = outer
    if with_logo:
        # curved logo decal: a cylinder strip just outside the band, alpha from the logo image (967x414 -> ~2.34:1)
        bm = bmesh.new(); seg = 24; ang = R_(80); z0, z1 = CUP_H * 0.31, CUP_H * 0.69
        hgt = z1 - z0
        verts = []
        for i in range(seg + 1):
            a = -math.pi / 2 - ang / 2 + ang * i / seg
            for z in (z0, z1):
                rr = CUP_R0 + (CUP_R1 - CUP_R0) * (z / CUP_H) + 0.0016
                verts.append(bm.verts.new((rr * math.cos(a), rr * math.sin(a), z)))
        for i in range(seg):
            bm.faces.new((verts[2 * i], verts[2 * i + 2], verts[2 * i + 3], verts[2 * i + 1]))
        me = bpy.data.meshes.new(name + "_LogoM"); bm.to_mesh(me); bm.free()
        uv = me.uv_layers.new()
        for p in me.polygons:
            for li in p.loop_indices:
                v = me.vertices[me.loops[li].vertex_index].co
                a = math.atan2(v.y, v.x); u = (a - (-math.pi / 2 - ang / 2)) / ang
                uv.data[li].uv = (u, (v.z - z0) / hgt)
        lo = bpy.data.objects.new(name + "_Logo", me); c.objects.link(lo); lo.parent = outer
        me.materials.append(logo_mat("LogoDark", True))
        for p in me.polygons: p.use_smooth = True
    return outer

def lid(name, c, loc):
    m = mat("CupLid", (0.97, 0.97, 0.96), 0.35)
    o = lathe(name, c, [(CUP_R1 + 0.003, -0.006), (CUP_R1 + 0.0035, 0.002), (CUP_R1 - 0.002, 0.006), (CUP_R1 - 0.008, 0.008),
                        (0.03, 0.009), (0.0, 0.0095)], m, loc, cap_bottom=False)
    o.modifiers.new("Solid", 'SOLIDIFY').thickness = 0.001
    return o

def steam(name, c, loc, h=0.28, r=0.05, dens=0.6):
    """small volume steam column: noise density, fades upward; W keyed by the animation (no Scene Time)"""
    bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=r, depth=h, location=(loc[0], loc[1], loc[2] + h / 2))
    o = bpy.context.object; o.name = name; link(o, c)
    m = bpy.data.materials.new(name + "_M"); m.use_nodes = True; nt = m.node_tree
    for n in list(nt.nodes):
        if n.type != 'OUTPUT_MATERIAL': nt.nodes.remove(n)
    out = nt.nodes["Material Output"]
    vol = nt.nodes.new("ShaderNodeVolumePrincipled"); vol.inputs["Color"].default_value = (1, 1, 1, 1)
    tc = nt.nodes.new("ShaderNodeTexCoord"); mp = nt.nodes.new("ShaderNodeMapping")
    nz = nt.nodes.new("ShaderNodeTexNoise"); nz.noise_dimensions = '4D'; nz.inputs["Scale"].default_value = 9.0
    nz.inputs["Detail"].default_value = 3.0
    wv = nt.nodes.new("ShaderNodeValue"); wv.name = "SteamW"; wv.outputs[0].default_value = 0.0
    up = nt.nodes.new("ShaderNodeValue"); up.name = "SteamRise"; up.outputs[0].default_value = 0.0
    sep = nt.nodes.new("ShaderNodeSeparateXYZ"); comb = nt.nodes.new("ShaderNodeCombineXYZ")
    nt.links.new(tc.outputs["Generated"], sep.inputs[0])
    add = nt.nodes.new("ShaderNodeMath"); add.operation = 'SUBTRACT'
    nt.links.new(sep.outputs["Z"], add.inputs[0]); nt.links.new(up.outputs[0], add.inputs[1])
    nt.links.new(sep.outputs["X"], comb.inputs["X"]); nt.links.new(sep.outputs["Y"], comb.inputs["Y"]); nt.links.new(add.outputs[0], comb.inputs["Z"])
    nt.links.new(comb.outputs[0], nz.inputs["Vector"]); nt.links.new(wv.outputs[0], nz.inputs["W"])
    # radial + vertical falloff
    rad = nt.nodes.new("ShaderNodeVectorMath"); rad.operation = 'DISTANCE'
    nt.links.new(tc.outputs["Generated"], rad.inputs[0])
    sepz = sep
    cx = nt.nodes.new("ShaderNodeCombineXYZ"); cx.inputs["X"].default_value = 0.5; cx.inputs["Y"].default_value = 0.5
    nt.links.new(sepz.outputs["Z"], cx.inputs["Z"]); nt.links.new(cx.outputs[0], rad.inputs[1])
    rf = nt.nodes.new("ShaderNodeMapRange"); rf.inputs["From Min"].default_value = 0.5; rf.inputs["From Max"].default_value = 0.1
    nt.links.new(rad.outputs["Value"], rf.inputs["Value"])
    vf = nt.nodes.new("ShaderNodeMapRange"); vf.inputs["From Min"].default_value = 1.0; vf.inputs["From Max"].default_value = 0.15
    nt.links.new(sepz.outputs["Z"], vf.inputs["Value"])
    nr = nt.nodes.new("ShaderNodeMapRange"); nr.inputs["From Min"].default_value = 0.5; nr.inputs["From Max"].default_value = 0.75
    nt.links.new(nz.outputs["Fac"], nr.inputs["Value"])
    m1 = nt.nodes.new("ShaderNodeMath"); m1.operation = 'MULTIPLY'; nt.links.new(rf.outputs[0], m1.inputs[0]); nt.links.new(vf.outputs[0], m1.inputs[1])
    m2 = nt.nodes.new("ShaderNodeMath"); m2.operation = 'MULTIPLY'; nt.links.new(m1.outputs[0], m2.inputs[0]); nt.links.new(nr.outputs[0], m2.inputs[1])
    amt = nt.nodes.new("ShaderNodeValue"); amt.name = "SteamAmount"; amt.outputs[0].default_value = dens
    m3 = nt.nodes.new("ShaderNodeMath"); m3.operation = 'MULTIPLY'; nt.links.new(m2.outputs[0], m3.inputs[0]); nt.links.new(amt.outputs[0], m3.inputs[1])
    m4 = nt.nodes.new("ShaderNodeMath"); m4.operation = 'MULTIPLY'; m4.inputs[1].default_value = 40.0 / max(r * 20, 1)
    nt.links.new(m3.outputs[0], m4.inputs[0]); nt.links.new(m4.outputs[0], vol.inputs["Density"])
    nt.links.new(vol.outputs[0], out.inputs["Volume"])
    o.data.materials.append(m)
    o.visible_shadow = False
    return o

def key_steam(o, f0, f1, rate=0.9, rise=0.5):
    """linear keys on the steam material's W and rise values for frames f0..f1 (keyed, so a VO shift moves them)"""
    nt = o.active_material.node_tree
    for nm, per_s in (("SteamW", rate), ("SteamRise", rise)):
        v = nt.nodes[nm].outputs[0]
        for f in (f0, f1):
            v.default_value = per_s * (f - f0) / 60.0; v.keyframe_insert("default_value", frame=f)
    for fc in nt.animation_data.action.fcurves if hasattr(nt.animation_data.action, "fcurves") else []:
        for k in fc.keyframe_points: k.interpolation = 'LINEAR'

# ================================================================== SetCar (x = 0)
cC = col("SetCar")
root_car, car = import_glb(A + "volvo.glb", "Car", cC, 0.01, (0, 0, 0), 0.0)
bpy.context.view_layer.update()
for o in list(car):
    mn, mx = bounds([o])
    if mn.x > 1.2 or "plate letters" in o.name or o.name.startswith(("Cube.018", "Cube.022", "Cube.019")):
        bpy.data.objects.remove(o)
car = alive(car)
for o in car:
    if "number plate" in o.name or "yellow" in o.name:
        o.data.materials.clear(); o.data.materials.append(mat("PlateBlank", (0.92, 0.92, 0.9), 0.4))
    for ms in o.material_slots:
        if ms.material and ms.material.name.startswith("main body"):
            ms.material = mat("CarPaint", (0.62, 0.12, 0.10), 0.3, coat=0.6)
# split the passenger (x<0) front door parts out of the Cube.006 meshes and swing the door open
for o in car:
    if "glass" in o.name.lower(): o.visible_shadow = False   # glass must not dim the light into the cabin (left a light/shadow band across her head)
door = bpy.data.objects.new("CarDoorP", None); cC.objects.link(door)
door.location = (-0.89, -0.975, 0.0)
for o in [o for o in car if o.name.startswith(("Cube.006", "Cube.015"))]:
    me = o.data.copy(); d = bpy.data.objects.new("DoorP_" + o.name, me); cC.objects.link(d)
    d.matrix_world = o.matrix_world.copy()
    for ob, keep_neg in ((o, False), (d, True)):
        bm = bmesh.new(); bm.from_mesh(ob.data)
        kill = [v for v in bm.verts if ((ob.matrix_world @ v.co).x < 0) != keep_neg]
        bmesh.ops.delete(bm, geom=kill, context='VERTS'); bm.to_mesh(ob.data); bm.free()
    mw = d.matrix_world.copy(); d.parent = door; d.matrix_world = mw
door.rotation_euler.z = R_(68)
# interior: floor carpet, dash, steering wheel, roof liner, far door trim, two seats
m_trim = mat("CarTrim", (0.16, 0.16, 0.17), 0.6); m_carpet = mat("CarCarpet", (0.12, 0.12, 0.13), 0.9)
box("CarFloor", cC, (0, -0.25, 0.30), (1.62, 1.9, 0.04), m_carpet, 0.005)
box("CarRoofLiner", cC, (0, -0.03, 1.49), (1.40, 1.45, 0.02), mat("CarLiner", (0.72, 0.70, 0.66), 0.8), 0.005)
box("CarDoorTrimFar", cC, (0.84, -0.48, 0.70), (0.04, 0.95, 0.42), m_trim, 0.01)
# dashboard: swept profile along X
prof = [(-1.02, 0.55), (-1.02, 0.78), (-0.98, 0.95), (-0.88, 1.02), (-0.76, 1.00), (-0.70, 0.90), (-0.74, 0.70), (-0.86, 0.55)]
bm = bmesh.new(); L = []
for x in (-0.80, 0.80):
    L.append([bm.verts.new((x, y, z)) for y, z in prof])
for i in range(len(prof)):
    bm.faces.new((L[0][i], L[0][(i + 1) % len(prof)], L[1][(i + 1) % len(prof)], L[1][i]))
bm.faces.new(L[0]); bm.faces.new(list(reversed(L[1])))
me = bpy.data.meshes.new("Dash"); bm.to_mesh(me); bm.free(); dash = bpy.data.objects.new("CarDash", me); cC.objects.link(dash)
me.materials.append(m_trim); b = dash.modifiers.new("Bevel", 'BEVEL'); b.width = 0.02; b.segments = 3
dash.modifiers.new("Sub", 'SUBSURF').levels = 1
bpy.ops.mesh.primitive_torus_add(major_radius=0.19, minor_radius=0.016, location=(0.40, -0.55, 0.90), rotation=(R_(-62), 0, 0))
sw = bpy.context.object; sw.name = "CarWheel"; link(sw, cC); sw.data.materials.append(m_trim)
for p in sw.data.polygons: p.use_smooth = True
root_seat, seats = import_glb(A + "frontseats.glb", "CarSeats", cC, 1.0)
bpy.context.view_layer.update()
for o in list(seats):
    omn, omx = bounds([o])
    if abs((omn.x + omx.x) / 2) < 2.2: bpy.data.objects.remove(o)
seats = alive(seats)
S = 0.13
root_seat.scale = (S, S, S); bpy.context.view_layer.update()
mn, mx = bounds(seats)
root_seat.location = (-(mn.x + mx.x) / 2, -0.15 - (mn.y + mx.y) / 2, 0.32 - mn.z); bpy.context.view_layer.update()
side = {o: ((bounds([o])[0].x + bounds([o])[1].x) / 2 < 0) for o in seats}
for neg in (True, False):
    grp = [o for o in seats if side[o] == neg]; gmn, gmx = bounds(grp); cx = (gmn.x + gmx.x) / 2
    d = Matrix.Translation(((-0.42 if neg else 0.42) - cx, 0, 0))
    for o in grp: o.matrix_world = d @ o.matrix_world
bpy.context.view_layer.update(); print("SEATS", bounds(seats))
# cabin lights (camera-invisible): roof fill + door-side face fill
for nm, loc, rot, size, en in (("DoorFill", (-1.7, -0.6, 1.25), (-0.42, -0.1, 0.9), 0.9, 60.0),):
    L = bpy.data.lights.new(nm, 'AREA'); L.size = size; L.energy = en; L.color = (1.0, 0.97, 0.93)
    lo = bpy.data.objects.new(nm, L); cC.objects.link(lo); lo.location = loc; lo.rotation_euler = (Vector(rot) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler(); lo.visible_camera = False
# cabin fill: a soft point light in front of her face (an area light at head height cut a light band across her head)
L = bpy.data.lights.new("CabinFill", 'POINT'); L.energy = 25.0; L.shadow_soft_size = 0.25; L.color = (1.0, 0.97, 0.93)
lo = bpy.data.objects.new("CabinFill", L); cC.objects.link(lo); lo.location = (-0.30, -0.80, 1.30); lo.visible_camera = False
# car park
m_asph = mat("Asphalt", (0.30, 0.31, 0.33), 0.85)
plane("CarPark", cC, (0, 0, 0.0), (60, 60), m_asph)
m_line = mat("ParkLine", (0.95, 0.95, 0.92), 0.6)
for x in (-1.55, 1.55, 4.65, -4.65):
    plane("Line%.1f" % x, cC, (x, -0.5, 0.002), (0.10, 5.0), m_line)
root_pk, pk = import_glb(A + "carpack.glb", "ParkedCars", cC, 1.0, (0, 0, 0))
for o in list(pk):
    if not o.name.startswith(("Sedan", "Hatchback", "Wagon", "SUV")) and "Wheel" not in o.name and "Cylinder" not in o.name:
        bpy.data.objects.remove(o)
pk = alive(pk)
for o in list(pk):
    if o.type == 'MESH' and (o.name.startswith("Cylinder")): bpy.data.objects.remove(o)
pk = alive(pk)
# move the kept cars to the next bays: hide this pack beyond bays; position per body group by bounds
bpy.context.view_layer.update()
groups = {}
for o in pk:
    mn_, mx_ = bounds([o]); groups.setdefault((round((mn_.x + mx_.x) / 4), round((mn_.y + mx_.y) / 4)), []).append(o)
bays = [(3.1, -0.4, 0.0), (-9.3, -0.3, R_(180)), (6.2, -0.5, R_(180)), (12.4, -0.4, 0.0)]
for (k, obs), bay in zip(sorted(groups.items(), key=lambda kv: -len(kv[1])), bays):
    e = bpy.data.objects.new("Parked_%d" % len(bays), None); cC.objects.link(e)
    mn_, mx_ = bounds(obs); ctr = (mn_ + mx_) / 2
    for o in obs:
        mw = o.matrix_world.copy(); o.parent = e; o.matrix_world = Matrix.Translation(-Vector((ctr.x, ctr.y, 0))) @ mw
    # orient long axis along Y
    if (mx_.x - mn_.x) > (mx_.y - mn_.y): e.rotation_euler.z = R_(90) + bay[2]
    else: e.rotation_euler.z = bay[2]
    e.location = (bay[0], bay[1], 0)
for o in pk:
    if o.parent == root_pk: bpy.data.objects.remove(o)
# low hedge + lamp posts behind the bays (real-looking shapes, simple)
m_hedge = mat("Hedge", (0.16, 0.45, 0.14), 0.8)
for i in range(9):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=0.75, location=(-8 + i * 2.0, 4.2, 0.55)); h = bpy.context.object
    h.name = "Hedge%d" % i; h.scale = (1.3, 0.7, 0.8); link(h, cC); h.data.materials.append(m_hedge)
    d = h.modifiers.new("D", 'DISPLACE'); t = bpy.data.textures.get("HedgeTex") or bpy.data.textures.new("HedgeTex", 'CLOUDS'); t.noise_scale = 0.25; d.texture = t; d.strength = 0.18
    for p in h.data.polygons: p.use_smooth = True

# ================================================================== SetCafe (x = 40)
cF = col("SetCafe"); X = 40.0
m_floorF = mat("CafeFloor", (0.78, 0.74, 0.68), 0.5)
plane("CafeFloor", cF, (X, -1.5, 0), (10, 9), m_floorF)
m_tile = bpy.data.materials.new("CafeTile"); m_tile.use_nodes = True; nt = m_tile.node_tree
bt = nt.nodes.new("ShaderNodeTexBrick"); bt.inputs["Color1"].default_value = (0.96, 0.95, 0.92, 1); bt.inputs["Color2"].default_value = (0.93, 0.92, 0.88, 1)
bt.inputs["Mortar"].default_value = (0.72, 0.70, 0.66, 1); bt.inputs["Scale"].default_value = 9.0; bt.inputs["Mortar Size"].default_value = 0.012
bt.offset = 0.0
tc = nt.nodes.new("ShaderNodeTexCoord"); nt.links.new(tc.outputs["Object"], bt.inputs["Vector"])
nt.links.new(bt.outputs["Color"], nt.nodes["Principled BSDF"].inputs["Base Color"]); nt.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.35
wall = box("CafeBackWall", cF, (X, 2.1, 1.5), (8, 0.1, 3.0), m_tile, 0)
box("CafeCeiling", cF, (X, -1.5, 3.0), (10, 9, 0.05), mat("CafeCeil", (0.95, 0.95, 0.95), 0.8), 0)
m_side = mat("CafeSideWall", (0.98, 0.86, 0.62), 0.6)
box("CafeWallL", cF, (X - 4.0, -1.0, 1.5), (0.1, 6.2, 3.0), m_side, 0)
box("CafeWallR", cF, (X + 4.0, -1.0, 1.5), (0.1, 6.2, 3.0), m_side, 0)
# front counter (customer side faces -Y)
m_ctrF = mat("CounterFront", (0.86, 0.36, 0.12), 0.45, coat=0.3)
m_ctrTop = mat("CounterTop", (0.80, 0.81, 0.82), 0.25, metal=0.8)
box("FrontCounter", cF, (X, 0.10, 0.50), (4.2, 0.70, 1.0), m_ctrF, 0.015)
box("FrontCounterTop", cF, (X, 0.08, 1.02), (4.3, 0.78, 0.04), m_ctrTop, 0.008)
box("CounterKick", cF, (X, -0.255, 0.06), (4.2, 0.02, 0.12), mat("Kick", (0.2, 0.2, 0.22), 0.5), 0.003)
# back counter (machines)
box("BackCounter", cF, (X, 1.575, 0.45), (5.0, 1.0, 0.9), mat("BackCab", (0.85, 0.85, 0.86), 0.4), 0.01)
box("BackCounterTop", cF, (X, 1.565, 0.915), (5.1, 1.04, 0.03), m_ctrTop, 0.006)
# menu boards: blank light panels with simple colour blocks (no text)
m_board = mat("MenuBoard", (0.12, 0.12, 0.13), 0.4)
m_panel = mat("MenuPanel", (0.97, 0.95, 0.90), 0.6, emit=((1, 0.97, 0.9), 0.6))
for i, x in enumerate((-1.6, 0.0, 1.6)):
    box("Menu%d" % i, cF, (X + x, 2.02, 2.35), (1.45, 0.06, 0.75), m_board, 0.01)
    plane("MenuP%d" % i, cF, (X + x, 1.985, 2.35), (1.35, 0.65), m_panel, rot=(R_(90), 0, 0))
    for j, (cx, cz, colr) in enumerate(((-0.4, 0.08, (0.86, 0.55, 0.18)), (0.0, 0.08, (0.75, 0.25, 0.15)), (0.4, 0.08, (0.35, 0.6, 0.25)))):
        bpy.ops.mesh.primitive_circle_add(vertices=32, radius=0.14, fill_type='NGON', location=(X + x + cx, 1.98, 2.35 + cz), rotation=(R_(90), 0, 0))
        ci = bpy.context.object; ci.name = "MenuPic%d_%d" % (i, j); link(ci, cF); ci.data.materials.append(mat("MenuPic%d" % j, colr, 0.5))
        box("MenuLine%d_%d" % (i, j), cF, (X + x + cx, 1.979, 2.35 - 0.17), (0.22, 0.004, 0.025), mat("MenuLine", (0.5, 0.48, 0.45), 0.6), 0)
# ceiling light panels
for i, x in enumerate((-2.5, 0.0, 2.5)):
    for y in (-2.0, 0.6):
        plane("CafeLight%d_%.0f" % (i, y), cF, (X + x, y, 2.97), (1.2, 0.6), mat("LightPanel", (1, 1, 1), 0.5, emit=((1, 0.98, 0.94), 6.0)), rot=(R_(180), 0, 0))
# espresso machine (brand letters removed) on the back counter, front facing -Y (toward the counter/customers)
root_m, mach = import_glb(A + "coffee_teal.glb", "Brewer", cF, 1.0)
tops = [o for o in root_m.children]; sv = [t.scale.copy() for t in tops]
for t in tops: t.scale = (1, 1, 1)
bpy.context.view_layer.update()
for o in mach:
    o.data = o.data.copy(); print("TEAL_TEXT_REMOVED", strip_teal_text(o))
for t, s_ in zip(tops, sv): t.scale = s_
bpy.context.view_layer.update()
mn, mx = bounds(mach)
SM = 0.94 / (mx.x - mn.x)
root_m.scale = (SM,) * 3; bpy.context.view_layer.update(); mn, mx = bounds(mach)
root_m.rotation_euler.z = R_(-90); bpy.context.view_layer.update(); mn, mx = bounds(mach)   # dial side faces the aisle
root_m.location += Vector((X - 0.9 - (mn.x + mx.x) / 2, 1.60 - (mn.y + mx.y) / 2, 0.93 - mn.z))
bpy.context.view_layer.update()
print("BREWER_BOUNDS", bounds(mach))
# our temperature dial on the brewer's right side panel (+X side): bezel, coloured arc, needle, knob
dial = bpy.data.objects.new("TempDial", None); cF.objects.link(dial)
mn, mx = bounds(mach)
dial.location = ((mn.x + mx.x) / 2 + 0.14, mn.y - 0.006, mn.z + 0.40); dial.rotation_euler = (R_(90), 0, 0)
bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=0.055, depth=0.012, location=(0, 0, 0)); bz = bpy.context.object
bz.name = "DialBezel"; link(bz, cF); bz.parent = dial; bz.data.materials.append(mat("Chrome", (0.9, 0.9, 0.92), 0.15, metal=1.0))
bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=0.048, depth=0.002, location=(0, 0, 0.0065)); face = bpy.context.object
face.name = "DialFace"; link(face, cF); face.parent = dial
fm = bpy.data.materials.new("DialFace"); fm.use_nodes = True; nt = fm.node_tree; P = nt.nodes["Principled BSDF"]
tc = nt.nodes.new("ShaderNodeTexCoord"); grad = nt.nodes.new("ShaderNodeTexGradient"); grad.gradient_type = 'RADIAL'
sepg = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(tc.outputs["Object"], sepg.inputs[0])
# polar angle -> colour ramp (blue at left, yellow top, red right) only on a ring 0.030..0.044 m
ramp = nt.nodes.new("ShaderNodeValToRGB"); el = ramp.color_ramp.elements
el[0].position = 0.0; el[0].color = (0.15, 0.35, 0.95, 1); el[1].position = 1.0; el[1].color = (0.95, 0.12, 0.08, 1)
e2 = el.new(0.5); e2.color = (1.0, 0.82, 0.1, 1)
at = nt.nodes.new("ShaderNodeMath"); at.operation = 'ARCTAN2'
nt.links.new(sepg.outputs["X"], at.inputs[0]); nt.links.new(sepg.outputs["Y"], at.inputs[1])
mr = nt.nodes.new("ShaderNodeMapRange"); mr.inputs["From Min"].default_value = -2.2; mr.inputs["From Max"].default_value = 2.2
mr.inputs["To Min"].default_value = 0.0; mr.inputs["To Max"].default_value = 1.0
nt.links.new(at.outputs[0], mr.inputs["Value"]); nt.links.new(mr.outputs[0], ramp.inputs["Fac"])
ln = nt.nodes.new("ShaderNodeVectorMath"); ln.operation = 'LENGTH'
cxy = nt.nodes.new("ShaderNodeCombineXYZ"); nt.links.new(sepg.outputs["X"], cxy.inputs["X"]); nt.links.new(sepg.outputs["Y"], cxy.inputs["Y"])
nt.links.new(cxy.outputs[0], ln.inputs[0])
ring_lo = nt.nodes.new("ShaderNodeMath"); ring_lo.operation = 'GREATER_THAN'; ring_lo.inputs[1].default_value = 0.031
ring_hi = nt.nodes.new("ShaderNodeMath"); ring_hi.operation = 'LESS_THAN'; ring_hi.inputs[1].default_value = 0.044
nt.links.new(ln.outputs["Value"], ring_lo.inputs[0]); nt.links.new(ln.outputs["Value"], ring_hi.inputs[0])
arcm = nt.nodes.new("ShaderNodeMath"); arcm.operation = 'LESS_THAN'; arcm.inputs[1].default_value = 2.2
absa = nt.nodes.new("ShaderNodeMath"); absa.operation = 'ABSOLUTE'; nt.links.new(at.outputs[0], absa.inputs[0]); nt.links.new(absa.outputs[0], arcm.inputs[0])
mm1 = nt.nodes.new("ShaderNodeMath"); mm1.operation = 'MULTIPLY'; nt.links.new(ring_lo.outputs[0], mm1.inputs[0]); nt.links.new(ring_hi.outputs[0], mm1.inputs[1])
mm2 = nt.nodes.new("ShaderNodeMath"); mm2.operation = 'MULTIPLY'; nt.links.new(mm1.outputs[0], mm2.inputs[0]); nt.links.new(arcm.outputs[0], mm2.inputs[1])
mix = nt.nodes.new("ShaderNodeMix"); mix.data_type = 'RGBA'; mix.inputs["A"].default_value = (0.97, 0.97, 0.96, 1)
nt.links.new(mm2.outputs[0], mix.inputs["Factor"]); nt.links.new(ramp.outputs["Color"], mix.inputs["B"])
nt.links.new(mix.outputs["Result"], P.inputs["Base Color"]); P.inputs["Roughness"].default_value = 0.3
face.data.materials.append(fm)
# tick marks (plain, no numbers)
m_tick = mat("DialTick", (0.1, 0.1, 0.1), 0.4)
for i in range(11):
    a = -2.2 + 4.4 * i / 10
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0.027 * math.sin(a), 0.027 * math.cos(a), 0.0078)); t = bpy.context.object
    t.scale = (0.0012, 0.006 if i % 5 else 0.009, 0.0006); t.rotation_euler.z = -a; t.name = "DialTick%d" % i; link(t, cF); t.parent = dial
    t.data.materials.append(m_tick)
# needle pivot (keyed rotation): pointer from centre toward the arc
needle = bpy.data.objects.new("DialNeedle", None); cF.objects.link(needle); needle.parent = dial; needle.location = (0, 0, 0.009)
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0.017, 0)); nd = bpy.context.object; nd.name = "DialNeedleMesh"; link(nd, cF)
nd.scale = (0.0028, 0.036, 0.0012); bpy.ops.object.transform_apply(scale=True); nd.parent = needle; nd.data.materials.append(mat("Needle", (0.08, 0.08, 0.09), 0.3))
bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=0.0055, depth=0.004, location=(0, 0, 0.001)); hub = bpy.context.object
hub.name = "DialHub"; link(hub, cF); hub.parent = needle; hub.data.materials.append(mat("Chrome", (0.9, 0.9, 0.92), 0.15, metal=1.0))
needle.rotation_euler.z = -1.9   # red end (hot) by default
# knob below the dial (keyed rotation, turned by the employee's hand)
knob = bpy.data.objects.new("DialKnob", None); cF.objects.link(knob); knob.parent = dial; knob.location = (0, -0.11, 0.0)
bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=0.022, depth=0.03, location=(0, 0, 0.015)); kb = bpy.context.object
kb.name = "DialKnobMesh"; link(kb, cF); kb.parent = knob; kb.data.materials.append(mat("KnobBlack", (0.05, 0.05, 0.05), 0.35))
bv = kb.modifiers.new("Bevel", 'BEVEL'); bv.width = 0.004; bv.segments = 3
box("DialKnobMark", cF, (0, 0.014, 0.0305), (0.003, 0.012, 0.001), mat("KnobMark", (0.95, 0.95, 0.95), 0.4), 0).parent = knob
# coffee urn dispenser (pours straight down from its tap into the cup; no lip in front of the cup)
UX, UY = X + 0.75, 1.74
m_steel = mat("Steel", (0.82, 0.83, 0.85), 0.22, metal=1.0)
lathe("UrnBody", cF, [(0.155, 0.0), (0.160, 0.02), (0.160, 0.40), (0.150, 0.43), (0.08, 0.47), (0.02, 0.48), (0.0, 0.48)], m_steel, (UX, UY, 1.13))
lathe("UrnBase", cF, [(0.17, 0.0), (0.17, 0.02), (0.12, 0.05), (0.06, 0.07), (0.06, 0.20)], m_steel, (UX, UY, 0.93))
bpy.ops.mesh.primitive_torus_add(major_radius=0.162, minor_radius=0.006, location=(UX, UY, 1.15)); t_ = bpy.context.object; t_.name = "UrnRing"; link(t_, cF); t_.data.materials.append(m_steel)
for sx in (-1, 1):
    bpy.ops.mesh.primitive_torus_add(major_radius=0.035, minor_radius=0.008, location=(UX + sx * 0.17, UY, 1.45), rotation=(R_(90), 0, 0))
    h_ = bpy.context.object; h_.name = "UrnHandle%d" % sx; link(h_, cF); h_.data.materials.append(mat("KnobBlack", (0.05, 0.05, 0.05), 0.35))
# sight glass (coffee level tube) on the front
bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=0.011, depth=0.30, location=(UX + 0.07, UY - 0.163, 1.36)); g_ = bpy.context.object
g_.name = "UrnSight"; link(g_, cF); g_.data.materials.append(mat("Coffee", (0.11, 0.05, 0.02), 0.08))
# tap: block + spout pointing down + lever
box("UrnTapBody", cF, (UX, UY - 0.185, 1.20), (0.05, 0.06, 0.05), m_steel, 0.01)
bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=0.009, depth=0.07, location=(UX, UY - 0.205, 1.155)); sp_ = bpy.context.object
sp_.name = "UrnSpout"; link(sp_, cF); sp_.data.materials.append(m_steel)
box("UrnLever", cF, (UX, UY - 0.215, 1.255), (0.016, 0.016, 0.07), mat("KnobBlack", (0.05, 0.05, 0.05), 0.35), 0.006)
box("UrnDrip", cF, (UX, UY - 0.205, 0.935), (0.16, 0.13, 0.012), m_steel, 0.004)
cup2 = paper_cup("PourCup", cF, (UX, UY - 0.205, 0.941), with_logo=True)
st2 = steam("PourSteam", cF, (UX, UY - 0.205, 0.941 + CUP_H * 0.7), h=0.30, r=0.045, dens=0.5)
st2.hide_render = True
# pour stream (glossy coffee column), its visible length keyed via scale
bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=0.0035, depth=1.0, location=(0, 0, -0.5)); s = bpy.context.object
s.name = "PourStreamMesh"; link(s, cF); bpy.ops.object.transform_apply(location=True)
s.data.materials.append(mat("Coffee", (0.11, 0.05, 0.02), 0.08))
stream = bpy.data.objects.new("PourStream", None); cF.objects.link(stream); s.parent = stream
# hero / customer cups (with logo) for B4 are made by the animation script from paper_cup()

# ================================================================== SetHosp (x = 80)
cH = col("SetHosp"); X = 80.0
plane("HospFloor", cH, (X, 0, 0), (6, 6), mat("HospFloor", (0.80, 0.82, 0.80), 0.4))
m_hw = mat("HospWall", (0.80, 0.90, 0.88), 0.7)
box("HospWallBack", cH, (X, 2.2, 1.4), (6, 0.1, 2.8), m_hw, 0)
box("HospWallLeft", cH, (X - 2.6, 0, 1.4), (0.1, 6, 2.8), m_hw, 0)
box("HospWallRight", cH, (X + 2.6, 0, 1.4), (0.1, 6, 2.8), m_hw, 0)
box("HospWallFront", cH, (X, -2.9, 1.4), (6, 0.1, 2.8), m_hw, 0)
box("HospCeil", cH, (X, 0, 2.8), (6, 6, 0.05), mat("HospCeil", (0.96, 0.96, 0.96), 0.8), 0)
plane("HospLight", cH, (X, 0.3, 2.77), (1.4, 0.7), mat("LightPanel", (1, 1, 1), 0.5, emit=((1, 0.98, 0.94), 6.0)), rot=(R_(180), 0, 0))
# window in the back wall: bright sky panel behind a frame, blinds half up
plane("HospSky", cH, (X + 1.2, 2.14, 1.6), (1.6, 1.1), mat("WinSky", (0.5, 0.8, 1.0), 0.5, emit=((0.62, 0.85, 1.0), 2.5)), rot=(R_(90), 0, 0))
m_frame = mat("WinFrame", (0.95, 0.95, 0.95), 0.4)
for nm, loc, sz in (("WinFrameT", (X + 1.2, 2.12, 2.17), (1.7, 0.06, 0.06)), ("WinFrameB", (X + 1.2, 2.12, 1.03), (1.7, 0.06, 0.06)),
                    ("WinFrameL", (X + 0.38, 2.12, 1.6), (0.06, 0.06, 1.2)), ("WinFrameR", (X + 2.02, 2.12, 1.6), (0.06, 0.06, 1.2)),
                    ("WinFrameM", (X + 1.2, 2.12, 1.6), (0.04, 0.05, 1.12))):
    box(nm, cH, loc, sz, m_frame, 0.005)
for i in range(7):
    box("Blind%d" % i, cH, (X + 1.2, 2.10, 2.12 - i * 0.035), (1.62, 0.03, 0.006), m_frame, 0.002)
# privacy curtain on the left
cur = plane("HospCurtain", cH, (X - 1.7, -0.6, 1.25), (1.6, 2.2), mat("Curtain", (0.55, 0.75, 0.85), 0.8), rot=(R_(90), 0, R_(90)))
wv = cur.modifiers.new("Wave", 'WAVE'); wv.use_normal = False
sub = cur.modifiers.new("Sub", 'SUBSURF'); sub.levels = 0
bpy.ops.object.select_all(action='DESELECT'); cur.select_set(True); bpy.context.view_layer.objects.active = cur
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.subdivide(number_cuts=30); bpy.ops.object.mode_set(mode='OBJECT')
cur.modifiers.remove(wv)
for v in cur.data.vertices: v.co.z += 0.0
for v in cur.data.vertices: v.co.y += 0.0
for v in cur.data.vertices: v.co.z += 0.04 * math.sin(v.co.x * 28)   # pleats (plane local x)
# bed
root_b, bed = import_glb(A + "bed.glb", "Bed", cH, 1.0)
mn, mx = bounds(bed); sb = 2.1 / (mx.y - mn.y)
root_b.scale = (sb,) * 3; bpy.context.view_layer.update(); mn, mx = bounds(bed)
root_b.location = (X - 0.3 - (mn.x + mx.x) / 2, 0.3 - (mn.y + mx.y) / 2, -mn.z)
bpy.context.view_layer.update(); print("BED_BOUNDS", bounds(bed))
for o in bed:
    for ms in o.material_slots: ms.material = mat("BedWhite", (0.93, 0.94, 0.95), 0.45)
root_iv, iv = import_glb(A + "iv.glb", "IVStand", cH, 1.0)
mn, mx = bounds(iv); si = 1.95 / (mx.z - mn.z); root_iv.scale = (si,) * 3; bpy.context.view_layer.update(); mn, mx = bounds(iv)
root_iv.location = (X + 0.75 - (mn.x + mx.x) / 2, 1.3 - (mn.y + mx.y) / 2, -mn.z)
# bedside cabinet + small vase of flowers (simple, readable)
box("Bedside", cH, (X + 0.85, 0.9, 0.38), (0.45, 0.42, 0.76), mat("Cabinet", (0.92, 0.88, 0.80), 0.5), 0.01)
lathe("Vase", cH, [(0.04, 0), (0.05, 0.06), (0.035, 0.16), (0.04, 0.2)], mat("Vase", (0.35, 0.55, 0.85), 0.2), (X + 0.85, 0.9, 0.765))
for i, (dx, dy, cl) in enumerate(((0, 0, (1, .85, .2)), (.04, .02, (.95, .4, .5)), (-.03, .03, (1, 1, 1)))):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.03, location=(X + 0.85 + dx, 0.9 + dy, 1.03 + 0.02 * i)); fl = bpy.context.object
    fl.name = "Flower%d" % i; link(fl, cH); fl.data.materials.append(mat("Flower%d" % i, cl, 0.6))

# ================================================================== SetBoard (x = 120)
cB = col("SetBoard"); X = 120.0
m_wood = bpy.data.materials.new("BoardFloor"); m_wood.use_nodes = True; nt = m_wood.node_tree
wvv = nt.nodes.new("ShaderNodeTexWave"); wvv.inputs["Scale"].default_value = 3.0; wvv.inputs["Distortion"].default_value = 4.0
cr = nt.nodes.new("ShaderNodeValToRGB"); cr.color_ramp.elements[0].color = (0.45, 0.30, 0.18, 1); cr.color_ramp.elements[1].color = (0.62, 0.44, 0.28, 1)
nt.links.new(wvv.outputs["Fac"], cr.inputs["Fac"]); nt.links.new(cr.outputs["Color"], nt.nodes["Principled BSDF"].inputs["Base Color"])
nt.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.4
plane("BoardFloor", cB, (X, 0, 0), (9, 8), m_wood)
m_bw = mat("BoardWall", (0.93, 0.90, 0.84), 0.7)
box("BoardWallL", cB, (X - 3.5, 0, 1.5), (0.1, 8, 3.0), m_bw, 0)
box("BoardWallBack", cB, (X, 3.0, 1.5), (7, 0.1, 3.0), m_bw, 0)
box("BoardCeil", cB, (X, 0, 3.0), (9, 8, 0.05), mat("CafeCeil", (0.95, 0.95, 0.95), 0.8), 0)
# right wall = window wall: mullions, open to the HDRI sky
m_mul = mat("Mullion", (0.25, 0.26, 0.28), 0.4, metal=0.6)
for i in range(6):
    box("Mullion%d" % i, cB, (X + 3.5, -3.0 + i * 1.2, 1.5), (0.08, 0.08, 3.0), m_mul, 0.005)
box("WinSill", cB, (X + 3.5, 0, 0.35), (0.1, 8, 0.7), m_mul, 0.005)
# city skyline outside (simple tower blocks far away, soft colours)
for i in range(12):
    hgt = 8 + (i * 37 % 11) * 2.5
    box("Tower%d" % i, cB, (X + 30 + (i % 3) * 9, -20 + i * 4.0, hgt / 2 - 6), (6, 3, hgt), mat("Tower%d" % (i % 3), [(0.75, 0.82, 0.9), (0.85, 0.85, 0.88), (0.7, 0.78, 0.86)][i % 3], 0.4), 0)
# wall art (abstract colour panels, no text)
for i, (y, cl) in enumerate(((-1.0, (0.2, 0.45, 0.75)), (1.0, (0.85, 0.55, 0.2)))):
    box("Art%d" % i, cB, (X - 3.43, y, 1.65), (0.04, 1.1, 0.75), mat("Art%d" % i, cl, 0.5), 0.005)
root_t, tbl = import_glb(A + "conf_table.glb", "BoardTable", cB, 1.0)
mn, mx = bounds(tbl); root_t.scale = (0.72, 0.72, 0.76); bpy.context.view_layer.update(); mn, mx = bounds(tbl)
root_t.rotation_euler.z = R_(90); bpy.context.view_layer.update(); mn, mx = bounds(tbl)
root_t.location = (X - (mn.x + mx.x) / 2, 0.2 - (mn.y + mx.y) / 2, -mn.z); bpy.context.view_layer.update()
print("TABLE_BOUNDS", bounds(tbl))
root_c, chs = import_glb(A + "chair.glb", "ChairProto", cB, 0.85)
mn, mx = bounds(chs); root_c.location.z -= mn.z; bpy.context.view_layer.update()
proto = chs[0]; CHAIR_FIX = math.pi   # the model's seat faces -Y
tmn, tmx = bounds(tbl)
chairs = []
for i, (cx, cy, rz) in enumerate(((X, tmn.y - 0.57, 0.0), (X - 1.05, tmn.y + 0.9, R_(90)), (X + 1.05, tmn.y + 0.9, R_(-90)),
                                    (X - 1.05, tmn.y + 1.9, R_(90)), (X + 1.05, tmn.y + 1.9, R_(-90)))):
    pmn, pmx = bounds([proto]); pc = Vector(((pmn.x + pmx.x) / 2, (pmn.y + pmx.y) / 2, pmn.z))
    o = proto.copy(); cB.objects.link(o); o.parent = None
    o.matrix_world = Matrix.Translation((cx, cy, 0)) @ Matrix.Rotation(rz + CHAIR_FIX, 4, 'Z') @ Matrix.Translation(-pc) @ proto.matrix_world
    o.name = "BoardChair%d" % i; chairs.append(o)
bpy.data.objects.remove(proto)
# potted plant (Poly Haven CC0)
pp = W + "ph/potted_plant_01/"
bl = [f for f in os.listdir(pp) if f.endswith(".blend")]
if bl:
    with bpy.data.libraries.load(pp + bl[0], link=False) as (fd, td): td.objects = list(fd.objects)
    for o in td.objects:
        if o and o.type == 'MESH': cB.objects.link(o); o.location = (X - 2.9, 2.5, 0); o.scale = (1.2,) * 3; o.name = "Plant_" + o.name
for i in range(1):
    pass

for i, y in enumerate((-2.0, 0.0, 2.0)):
    plane("BoardLight%d" % i, cB, (X, y, 2.97), (1.2, 0.6), mat("LightPanel", (1, 1, 1), 0.5, emit=((1, 0.98, 0.94), 6.0)), rot=(R_(180), 0, 0))
L = bpy.data.lights.new("BoardFill", 'AREA'); L.size = 3.0; L.energy = 400.0
lo = bpy.data.objects.new("BoardFill", L); cB.objects.link(lo); lo.location = (X, -0.5, 2.85); lo.visible_camera = False
L = bpy.data.lights.new("HospFill", 'AREA'); L.size = 2.0; L.energy = 150.0
lo = bpy.data.objects.new("HospFill", L); cH.objects.link(lo); lo.location = (79.7, 0.0, 2.7); lo.visible_camera = False
# ================================================================== world / colour
w = bpy.data.worlds.new("World"); sc.world = w; w.use_nodes = True; nt = w.node_tree
env = nt.nodes.new("ShaderNodeTexEnvironment"); env.image = bpy.data.images.load(W + "ph/hdri/kloofendal_43d_clear_puresky_2k.hdr")
nt.links.new(env.outputs["Color"], nt.nodes["Background"].inputs["Color"]); nt.nodes["Background"].inputs["Strength"].default_value = 1.0
sc.view_settings.view_transform = 'AgX'
try: sc.view_settings.look = 'AgX - Punchy'
except Exception: sc.view_settings.look = 'Punchy'
sc.render.engine = 'CYCLES'; sc.render.fps = 60; sc.render.resolution_x = 1080; sc.render.resolution_y = 1920
sc.cycles.samples = 48; sc.cycles.adaptive_threshold = 0.05; sc.cycles.use_denoising = True
# sun for the car park
sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", 'SUN')); sc.collection.objects.link(sun)
sun.data.energy = 3.0; sun.rotation_euler = (R_(40), R_(10), R_(35)); sun.data.angle = R_(4)
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print("SETS_OK", OUT)
