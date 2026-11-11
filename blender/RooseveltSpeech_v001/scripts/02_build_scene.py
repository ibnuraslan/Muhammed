"""Sets, props, crowd instances, studio dome.  blender -b humans.blend --python 02_build_scene.py -- scene.blend"""
import sys, os, math, random
import bpy, bmesh
from mathutils import Vector, Matrix
out = sys.argv[sys.argv.index("--") + 1]
D = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
A = D + "/assets"
R_ = math.radians
sc = bpy.context.scene
random.seed(7)

def coll(name):
    c = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if c.name not in sc.collection.children: sc.collection.children.link(c)
    return c
C_STREET, C_HALL, C_STUDIO, C_CROWD = coll("Street"), coll("Hall"), coll("Studio"), coll("CrowdLib")

def link(o, c):
    for uc in list(o.users_collection): uc.objects.unlink(o)
    c.objects.link(o)

def img(p, cs="sRGB"):
    i = bpy.data.images.load(p, check_existing=True); i.colorspace_settings.name = cs; return i

def pbr(name, tex, scale=1.0, tint=None, rough_mul=1.0, bump=0.3, box=False):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; n, l = nt.nodes, nt.links; b = n["Principled BSDF"]
    tc = n.new("ShaderNodeTexCoord"); mp = n.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (scale,) * 3
    l.new(tc.outputs["Object" if box else "UV"], mp.inputs["Vector"])
    d = f"{A}/tex/{tex}/textures/{tex}_"
    def T(suf, cs):
        for ext in ("jpg", "png", "exr"):
            if os.path.exists(f"{d}{suf}_1k.{ext}"):
                t = n.new("ShaderNodeTexImage"); t.image = img(f"{d}{suf}_1k.{ext}", cs)
                if box: t.projection = "BOX"; t.projection_blend = 0.2
                l.new(mp.outputs["Vector"], t.inputs["Vector"]); return t
    c = T("diff", "sRGB")
    if tint:
        mx = n.new("ShaderNodeMix"); mx.data_type = "RGBA"; mx.blend_type = "MULTIPLY"; mx.inputs["Factor"].default_value = 1
        mx.inputs["B"].default_value = (*tint, 1); l.new(c.outputs["Color"], mx.inputs["A"]); l.new(mx.outputs["Result"], b.inputs["Base Color"])
    else: l.new(c.outputs["Color"], b.inputs["Base Color"])
    r = T("rough", "Non-Color")
    if r:
        mm = n.new("ShaderNodeMath"); mm.operation = "MULTIPLY"; mm.inputs[1].default_value = rough_mul
        l.new(r.outputs["Color"], mm.inputs[0]); l.new(mm.outputs[0], b.inputs["Roughness"])
    ds = T("disp", "Non-Color")
    if ds:
        bp = n.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = bump; bp.inputs["Distance"].default_value = 0.02
        l.new(ds.outputs["Color"], bp.inputs["Height"]); l.new(bp.outputs["Normal"], b.inputs["Normal"])
    return m

def flat(name, col, rough=0.5, metal=0.0, emit=None, es=0.0, alpha=1.0):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*col, 1); b.inputs["Roughness"].default_value = rough; b.inputs["Metallic"].default_value = metal
    if emit: b.inputs["Emission Color"].default_value = (*emit, 1); b.inputs["Emission Strength"].default_value = es
    if alpha < 1: b.inputs["Alpha"].default_value = alpha
    return m

def box(name, size, loc, mat, c, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    o = bpy.context.object; o.name = name; o.scale = size
    bpy.ops.object.transform_apply(scale=True)
    bpy.ops.object.mode_set(mode="EDIT"); bpy.ops.uv.cube_project(cube_size=1.0); bpy.ops.object.mode_set(mode="OBJECT")
    o.data.materials.append(mat); link(o, c); return o

def plane(name, size, loc, mat, c, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_plane_add(size=1, location=loc, rotation=rot)
    o = bpy.context.object; o.name = name; o.scale = (size[0], size[1], 1); bpy.ops.object.transform_apply(scale=True)
    o.data.materials.append(mat); link(o, c); return o

def cyl(name, r, h, loc, mat, c, rot=(0, 0, 0), v=24):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=h, location=loc, rotation=rot, vertices=v)
    o = bpy.context.object; o.name = name; o.data.materials.append(mat); bpy.ops.object.shade_smooth(); link(o, c); return o

def glb(path, c, name):
    before = set(bpy.data.objects); bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    for o in new: link(o, c)
    root = next(o for o in new if o.parent is None); root.name = name
    return root, new

def ray_down(objs, x, y, z0=5.0):
    dg = bpy.context.evaluated_depsgraph_get(); best = None
    for o in objs:
        if o.type != "MESH": continue
        oe = o.evaluated_get(dg); Mi = o.matrix_world.inverted()
        ok, loc, nrm, idx = oe.ray_cast(Mi @ Vector((x, y, z0)), (Mi.to_3x3() @ Vector((0, 0, -1))).normalized())
        if ok:
            w = o.matrix_world @ loc
            if best is None or w.z > best[0].z: best = (w, o.name)
    return best

# ================================================================== CAR (CC-BY Libau Media), open tourer, front -> +X
car, parts = glb(A + "/models/car.glb", C_STREET, "Car")
for o in parts:
    if o.name.startswith("roof"): bpy.data.objects.remove(o, do_unlink=True)
parts = [o for o in C_STREET.objects if o.type == "MESH"]
car.rotation_mode = "XYZ"; car.scale = (0.0045,) * 3; car.rotation_euler.z = R_(90)
bpy.context.view_layer.update()
car.location = (0.45, 0, 0); bpy.context.view_layer.update()
hit = ray_down(parts, 0.0, 0.0, 1.5)
print("CAR floor hit", hit)
fz = hit[0].z if hit else 0.0
car.location.z -= fz; bpy.context.view_layer.update()
gnd = min((o.matrix_world @ Vector(c)).z for o in parts if "wheel" in o.name for c in o.bound_box)
STREET_Z = gnd
print("STREET_Z", STREET_Z)
# repaint: dark green-black lacquer, brass lamps glowing
for o in parts:
    for i, m in enumerate(o.data.materials):
        if m and m.name.startswith("light"):
            o.data.materials[i] = flat("CarLampGlow", (1, 0.85, 0.6), emit=(1, 0.8, 0.5), es=25)
        elif m and m.name.startswith("body") and "matte" not in m.name:
            b = m.node_tree.nodes.get("Principled BSDF")
            if b: b.inputs["Base Color"].default_value = (0.02, 0.035, 0.03, 1); b.inputs["Roughness"].default_value = 0.25
for s, y in (("L", -0.37), ("R", 0.37)):
    lt = bpy.data.lights.new("HeadLamp" + s, "SPOT"); lt.energy = 600; lt.spot_size = R_(50); lt.color = (1, 0.82, 0.55); lt.shadow_soft_size = 0.05
    lo = bpy.data.objects.new("HeadLamp" + s, lt); lo.location = (2.15, y, 0.55 + STREET_Z + 0.05); lo.rotation_euler = (0, R_(95), 0); C_STREET.objects.link(lo)

# ================================================================== STREET
cob = pbr("Cobble", "cobblestone_floor_01", 6.0, tint=(0.55, 0.55, 0.6), rough_mul=0.55, bump=0.5)
g = plane("StreetGround", (60, 60), (0, 0, STREET_Z), cob, C_STREET)
pave = pbr("Pavement", "cobblestone_floor_01", 3.0, tint=(0.6, 0.58, 0.55), rough_mul=0.8)
box("Sidewalk", (40, 3.0, 0.15), (0, 5.0, STREET_Z + 0.075), pave, C_STREET)
brick = pbr("Brick", "brick_4", 1.0, tint=(0.75, 0.62, 0.55), box=True)
win_lit = flat("WindowLit", (0.05, 0.04, 0.03), emit=(1.0, 0.62, 0.3), es=0.45)
win_dark = flat("WindowDark", (0.02, 0.025, 0.03), rough=0.1)
trim = flat("StoneTrim", (0.45, 0.42, 0.38), rough=0.8)
# hotel facade behind the car, 5 storeys, windows and a canopy entrance
box("HotelWall", (30, 0.6, 18), (0, 6.8, STREET_Z + 9), brick, C_STREET)
for fl in range(5):
    for k in range(-7, 8):
        x = k * 2.0; z = STREET_Z + 2.0 + fl * 3.4
        if fl == 0 and abs(k) <= 1: continue
        lit = random.random() < 0.55
        box(f"Win_{fl}_{k}", (1.0, 0.1, 1.7), (x, 6.48, z + 0.9), win_lit if lit else win_dark, C_STREET)
        box(f"Sill_{fl}_{k}", (1.25, 0.25, 0.12), (x, 6.42, z - 0.02), trim, C_STREET)
box("Entrance", (4.4, 0.2, 3.2), (0, 6.45, STREET_Z + 1.6), win_lit, C_STREET)
canopy = flat("Canopy", (0.25, 0.05, 0.04), rough=0.7)
box("Canopy", (5.4, 2.6, 0.15), (0, 5.3, STREET_Z + 3.4), canopy, C_STREET)
for x in (-2.5, 2.5): cyl(f"CanopyPost{x}", 0.05, 3.4, (x, 4.1, STREET_Z + 1.7), trim, C_STREET)
box("Cornice", (30, 1.0, 0.5), (0, 6.3, STREET_Z + 18.0), trim, C_STREET)
# side buildings and the far side of the street (seen during the whip)
for x, h in ((-17, 14), (17, 12)): box(f"SideBld{x}", (6, 14, h), (x, 1.0, STREET_Z + h / 2), brick, C_STREET)
box("FarBld", (40, 0.6, 14), (0, -16, STREET_Z + 7), brick, C_STREET)
for k in range(-9, 10):
    for fl in range(3):
        if random.random() < 0.5: box(f"FarWin_{fl}_{k}", (1.0, 0.1, 1.6), (k * 2.1, -15.65, STREET_Z + 2.5 + fl * 3.6), win_lit, C_STREET)
# wall lanterns (CC-BY Luca Giardina) + gas street lamps
lroot, lparts = glb(A + "/models/lantern.glb", C_STREET, "LanternSrc")
lroot.scale = (0.5,) * 3; bpy.context.view_layer.update()
for i, x in enumerate((-5.5, 5.5, -11, 11)):
    if i == 0: L = lroot
    else:
        L = lroot.copy(); C_STREET.objects.link(L)
        for p in lparts:
            if p.parent == lroot: q = p.copy(); C_STREET.objects.link(q); q.parent = L
    L.location = (x, 6.25, STREET_Z + 3.0); L.rotation_euler = (0, 0, R_(-90))
    pl = bpy.data.lights.new(f"LanternLight{i}", "POINT"); pl.energy = 150; pl.color = (1, 0.7, 0.4); pl.shadow_soft_size = 0.15
    po = bpy.data.objects.new(f"LanternLight{i}", pl); po.location = (x, 5.5, STREET_Z + 2.6); C_STREET.objects.link(po)
iron = flat("Iron", (0.03, 0.03, 0.03), rough=0.4, metal=0.8)
glow = flat("GasGlow", (1, 0.8, 0.5), emit=(1, 0.75, 0.45), es=15)
for i, x in enumerate((-8, 8, -14, 14)):
    for y in (3.7, -13.5):
        cyl(f"LampPost{i}{y}", 0.06, 3.6, (x, y, STREET_Z + 1.8), iron, C_STREET)
        box(f"LampHead{i}{y}", (0.32, 0.32, 0.45), (x, y, STREET_Z + 3.8), glow, C_STREET)
        pl = bpy.data.lights.new(f"GasLight{i}{y}", "POINT"); pl.energy = 120; pl.color = (1, 0.72, 0.42)
        po = bpy.data.objects.new(f"GasLight{i}{y}", pl); po.location = (x, y, STREET_Z + 3.6); C_STREET.objects.link(po)
# moon/sky fill
sun = bpy.data.lights.new("MoonFill", "SUN"); sun.energy = 0.04; sun.color = (0.55, 0.65, 1.0); sun.angle = R_(3)
so = bpy.data.objects.new("MoonFill", sun); so.rotation_euler = (R_(50), 0, R_(-30)); C_STREET.objects.link(so)
# second car parked behind (same mesh, linked data), lights off
car2 = car.copy(); C_STREET.objects.link(car2); car2.location = (-6.0, 2.6, car.location.z)
for p in [o for o in parts if o.parent == car]:
    q = p.copy(); C_STREET.objects.link(q); q.parent = car2
# hero key light (streetside rim + warm key from the entrance)
for nm, loc, e, col in (("HeroKey", (2.5, -3.0, 2.6), 160, (1, 0.72, 0.5)), ("HeroRim", (-2.0, 3.5, 3.0), 260, (0.5, 0.62, 1.0))):
    lt = bpy.data.lights.new(nm, "AREA"); lt.energy = e; lt.size = 1.2; lt.color = col
    lo = bpy.data.objects.new(nm, lt); lo.location = loc; C_STREET.objects.link(lo)
    cn = lo.constraints.new("TRACK_TO"); cn.target = None
    d = Vector((0, 0, 1.3)) - Vector(loc); lo.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()

# ================================================================== HALL (same origin: stage floor z = 0, hero at 0,0)
wood = pbr("StageWood", "old_wood_floor", 2.0, tint=(0.8, 0.65, 0.5), rough_mul=0.7)
box("Stage", (14, 7, 1.2), (0, 1.5, -0.6), wood, C_HALL)
hallfloor = pbr("HallFloor", "wood_table_worn", 1.0, tint=(0.6, 0.45, 0.35), box=True)
box("HallFloor", (30, 26, 0.2), (0, -12, -1.3), hallfloor, C_HALL)
plaster = pbr("HallPlaster", "painted_plaster_wall", 0.6, tint=(0.85, 0.75, 0.6), box=True)
box("BackWall", (30, 0.4, 14), (0, 5.2, 5.8), plaster, C_HALL)
box("FarWall", (30, 0.4, 14), (0, -25.2, 5.8), plaster, C_HALL)
for x in (-15, 15): box(f"SideWall{x}", (0.4, 31, 14), (x, -10, 5.8), plaster, C_HALL)
box("Ceiling", (30, 31, 0.4), (0, -10, 12.8), plaster, C_HALL)
velvet = pbr("Curtain", "velour_velvet", 2.0, tint=(0.55, 0.06, 0.06), rough_mul=0.9)
for x in (-6.5, 6.5):
    bpy.ops.mesh.primitive_plane_add(size=1, location=(x, 4.6, 4.5), rotation=(R_(90), 0, 0))
    cu = bpy.context.object; cu.name = f"CurtainSide{x}"; cu.scale = (2.2, 9, 1); bpy.ops.object.transform_apply(scale=True)
    bpy.ops.object.mode_set(mode="EDIT"); bpy.ops.mesh.subdivide(number_cuts=40); bpy.ops.object.mode_set(mode="OBJECT")
    for v in cu.data.vertices: v.co.y += 0.12 * math.sin(v.co.x * 9.0)
    cu.data.materials.append(velvet); link(cu, C_HALL); bpy.ops.object.shade_smooth()
box("Proscenium", (14, 0.6, 1.4), (0, 4.4, 9.2), velvet, C_HALL)
# flags: plain stripes, no emblem; animated wave via displace driven by a texture offset
def stripe_mat(name, cols, n_str, horiz=True):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; n, l = nt.nodes, nt.links; b = n["Principled BSDF"]
    tc = n.new("ShaderNodeTexCoord"); sp = n.new("ShaderNodeSeparateXYZ"); l.new(tc.outputs["UV"], sp.inputs[0])
    mm = n.new("ShaderNodeMath"); mm.operation = "MULTIPLY"; mm.inputs[1].default_value = n_str; l.new(sp.outputs["Y" if horiz else "X"], mm.inputs[0])
    fl = n.new("ShaderNodeMath"); fl.operation = "FLOORED_MODULO"; fl.inputs[1].default_value = len(cols); l.new(mm.outputs[0], fl.inputs[0])
    ramp = n.new("ShaderNodeValToRGB"); ramp.color_ramp.interpolation = "CONSTANT"
    dv = n.new("ShaderNodeMath"); dv.operation = "DIVIDE"; dv.inputs[1].default_value = len(cols); l.new(fl.outputs[0], dv.inputs[0]); l.new(dv.outputs[0], ramp.inputs[0])
    els = ramp.color_ramp.elements
    while len(els) < len(cols): els.new(0.5)
    for i, c in enumerate(cols): els[i].position = i / len(cols); els[i].color = (*c, 1)
    l.new(ramp.outputs["Color"], b.inputs["Base Color"]); b.inputs["Roughness"].default_value = 0.8
    b.inputs["Sheen Weight"].default_value = 0.4
    return m
RED, WHITE, BLUE = (0.45, 0.03, 0.04), (0.8, 0.78, 0.72), (0.03, 0.06, 0.25)
flagm = stripe_mat("FlagStripes", [RED, WHITE], 13)
flagb = stripe_mat("FlagBlue", [BLUE], 1)
wave_tex = bpy.data.textures.new("FlagWave", "CLOUDS"); wave_tex.noise_scale = 0.8
FLAGS = []
for i, x in enumerate((-10, -5, 5, 10)):
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=30, y_subdivisions=20, size=1, location=(x, 4.9, 6.5), rotation=(R_(90), 0, 0))
    f = bpy.context.object; f.name = f"Flag{i}"; f.scale = (2.6, 1.6, 1); bpy.ops.object.transform_apply(scale=True)
    f.data.materials.append(flagm); link(f, C_HALL)
    dm = f.modifiers.new("Wave", "DISPLACE"); dm.texture = wave_tex; dm.strength = 0.18; dm.texture_coords = "GLOBAL"; dm.direction = "Y"
    bpy.ops.object.shade_smooth(); FLAGS.append(f)
    box(f"FlagCanton{i}", (1.1, 0.02, 0.8), (x - 0.75, 4.86, 6.9), flagb, C_HALL)
    cyl(f"FlagPole{i}", 0.03, 4.0, (x - 1.35, 4.85, 5.5), flat("Brass", (0.6, 0.45, 0.2), 0.3, 1.0), C_HALL)
# bunting swags along the stage front and balconies (half-disc fans, stripes)
bunt = stripe_mat("Bunting", [RED, WHITE, BLUE], 6, horiz=False)
def swag(name, cx, cy, cz, w, rot_z=0.0, drop=0.55):
    bm_ = bmesh.new(); N = 24; top = []; bot = []
    for k in range(N + 1):
        t = k / N; x = (t - 0.5) * w; sag = drop * math.sin(math.pi * t)
        top.append(bm_.verts.new((x, 0, 0))); bot.append(bm_.verts.new((x, -0.05 * math.sin(math.pi * t), -sag - 0.05)))
    uv_ = []
    for k in range(N): uv_.append(bm_.faces.new((top[k], top[k + 1], bot[k + 1], bot[k])))
    me = bpy.data.meshes.new(name); bm_.to_mesh(me); bm_.free()
    uvl = me.uv_layers.new()
    for poly in me.polygons:
        for li in poly.loop_indices:
            v = me.vertices[me.loops[li].vertex_index].co; uvl.data[li].uv = ((v.z + drop + 0.05) / (drop + 0.05), v.x / w + 0.5)
    o = bpy.data.objects.new(name, me); o.location = (cx, cy, cz); o.rotation_euler.z = rot_z; C_HALL.objects.link(o)
    me.materials.append(bunt); return o
for k in range(-3, 4): swag(f"StageSwag{k}", k * 2.0, -2.02, -0.02, 2.0)
# balcony along the far wall
box("Balcony", (28, 4, 0.4), (0, -22.5, 3.2), hallfloor, C_HALL)
box("BalconyFront", (28, 0.2, 1.0), (0, -20.5, 3.8), plaster, C_HALL)
for k in range(-6, 7): swag(f"BalcSwag{k}", k * 2.0, -20.38, 4.25, 2.0)
for sx in (-1, 1):   # side walls: bunting rows, striped banners, pilasters
    for k in range(12): swag(f"SideSwag{sx}_{k}", sx * 14.75, 3.0 - k * 2.0, 5.2, 2.0, rot_z=R_(90 * sx))
    for k in range(5):
        y = 1.5 - k * 5.0
        bpy.ops.mesh.primitive_grid_add(x_subdivisions=8, y_subdivisions=24, size=1, location=(sx * 14.76, y, 7.8), rotation=(R_(90), 0, R_(90 * sx)))
        bn = bpy.context.object; bn.name = f"Banner{sx}_{k}"; bn.scale = (1.1, 3.2, 1); bpy.ops.object.transform_apply(scale=True)
        bn.data.materials.append(stripe_mat(f"BannerM{sx}{k}", [RED, WHITE] if k % 2 else [BLUE, WHITE, RED], 7, horiz=False)); link(bn, C_HALL)
        box(f"Pilaster{sx}_{k}", (0.5, 0.6, 12), (sx * 14.7, y + 2.5, 5.8), trim, C_HALL)
for k in range(-6, 7): swag(f"BackSwag{k}", k * 2.0, 4.95, 9.9, 2.0)
# podium (procedural, oak with brass trim)
oak = pbr("Oak", "wood_table_worn", 1.5, tint=(0.75, 0.5, 0.3), box=True)
box("PodiumBody", (0.7, 0.45, 1.05), (0, -0.62, 0.525), oak, C_HALL)
box("PodiumTop", (0.8, 0.55, 0.06), (0, -0.62, 1.08), oak, C_HALL, rot=(R_(-12), 0, 0))
box("PodiumBase", (0.85, 0.6, 0.08), (0, -0.62, 0.04), oak, C_HALL)
# wall clock (CC-BY 3DGunsmith) on the far wall above the balcony; hands spun in animation
croot, cparts = glb(A + "/models/clock.glb", C_HALL, "WallClock")
croot.scale = (6.0,) * 3; croot.location = (0, -24.9, 7.6); croot.rotation_euler = (0, 0, 0)
handm = flat("ClockHand", (0.02, 0.02, 0.02), 0.4, 0.5)
for nm, ln, wd in (("ClockHour", 0.62, 0.09), ("ClockMinute", 0.98, 0.06)):
    o = box(nm, (wd, 0.02, ln), (0, 0, ln / 2 - 0.05), handm, C_HALL)
    bpy.context.scene.cursor.location = (0, 0, 0); bpy.ops.object.origin_set(type="ORIGIN_CURSOR")
    o.location = (0, -24.72, 7.6)
# chandeliers + warm hall light
for i, (x, y) in enumerate(((-6, -6), (6, -6), (-6, -15), (6, -15), (0, -10.5))):
    box(f"Chand{i}", (0.6, 0.6, 0.5), (x, y, 10.6), flat(f"ChandGlow{i}", (1, 0.85, 0.6), emit=(1, 0.8, 0.5), es=12), C_HALL)
    pl = bpy.data.lights.new(f"ChandLight{i}", "POINT"); pl.energy = 900; pl.color = (1, 0.78, 0.5); pl.shadow_soft_size = 0.5
    po = bpy.data.objects.new(f"ChandLight{i}", pl); po.location = (x, y, 10.0); C_HALL.objects.link(po)
for nm, loc, e, col, sz in (("StageKey", (3.0, -5.0, 5.0), 900, (1, 0.85, 0.65), 2.0), ("StageRim", (-2.5, 3.6, 5.0), 700, (0.8, 0.85, 1.0), 1.5),
                            ("Footlights", (0, -2.3, 0.2), 300, (1, 0.7, 0.4), 6.0)):
    lt = bpy.data.lights.new(nm, "AREA"); lt.energy = e; lt.size = sz; lt.color = col
    lo = bpy.data.objects.new(nm, lt); lo.location = loc; C_HALL.objects.link(lo)
    d = Vector((0, 0, 1.3)) - Vector(loc); lo.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
# ================================================================== STUDIO dome + cutaway props (real scale, in the right breast pocket)
dome_m = bpy.data.materials.new("StudioDome"); dome_m.use_nodes = True
nt = dome_m.node_tree; n, l = nt.nodes, nt.links
for x in list(n):
    if x.type != "OUTPUT_MATERIAL": n.remove(x)
tc = n.new("ShaderNodeTexCoord"); sp = n.new("ShaderNodeSeparateXYZ"); l.new(tc.outputs["Generated"], sp.inputs[0])
rp = n.new("ShaderNodeValToRGB"); rp.color_ramp.elements[0].color = (0.25, 0.72, 0.9, 1); rp.color_ramp.elements[1].color = (0.92, 0.97, 1.0, 1)
rp.color_ramp.elements[0].position = 0.25; rp.color_ramp.elements[1].position = 0.8
l.new(sp.outputs["Z"], rp.inputs[0])
em = n.new("ShaderNodeEmission"); em.inputs["Strength"].default_value = 1.0; l.new(rp.outputs["Color"], em.inputs["Color"])
tr = n.new("ShaderNodeBsdfTransparent"); mx = n.new("ShaderNodeMixShader"); mx.name = "DomeMix"
fade = n.new("ShaderNodeValue"); fade.name = "DomeFade"; fade.outputs[0].default_value = 0.0
l.new(fade.outputs[0], mx.inputs["Fac"]); l.new(tr.outputs["BSDF"], mx.inputs[1]); l.new(em.outputs["Emission"], mx.inputs[2])
l.new(mx.outputs["Shader"], n["Material Output"].inputs["Surface"])
bpy.ops.mesh.primitive_uv_sphere_add(radius=1.6, location=(-0.1, -0.2, 1.25), segments=48, ring_count=24)
dome = bpy.context.object; dome.name = "StudioDome"; dome.data.materials.append(dome_m); link(dome, C_STUDIO)
bpy.ops.object.shade_smooth()
dome.visible_shadow = False
for nm, loc, e, col in (("StudioKey", (0.6, -1.0, 1.9), 60, (1, 1, 1)), ("StudioFill", (-0.9, -0.9, 1.0), 25, (0.7, 0.9, 1.0)), ("StudioRim", (0.2, 0.6, 1.8), 40, (1, 1, 1))):
    lt = bpy.data.lights.new(nm, "AREA"); lt.energy = e; lt.size = 0.5; lt.color = col
    lo = bpy.data.objects.new(nm, lt); lo.location = loc; C_STUDIO.objects.link(lo)
    d = Vector((-0.1, -0.2, 1.28)) - Vector(loc); lo.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()

# manuscript: 50 folded sheets (each a thin bent card), pencil-grey illegible line marks
paper_m = bpy.data.materials.new("Paper"); paper_m.use_nodes = True
nt = paper_m.node_tree; n, l = nt.nodes, nt.links; b = n["Principled BSDF"]
b.inputs["Base Color"].default_value = (0.8, 0.74, 0.6, 1); b.inputs["Roughness"].default_value = 0.85
b.inputs["Subsurface Weight"].default_value = 0.15
tcp = n.new("ShaderNodeTexCoord"); wv = n.new("ShaderNodeTexWave"); wv.wave_profile = "SAW"; wv.inputs["Scale"].default_value = 22
wv.bands_direction = "Y"; l.new(tcp.outputs["UV"], wv.inputs["Vector"])
nz = n.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 90; l.new(tcp.outputs["Generated"], nz.inputs["Vector"])
mr = n.new("ShaderNodeMapRange"); mr.inputs["From Min"].default_value = 0.86; mr.inputs["From Max"].default_value = 0.93
l.new(wv.outputs["Fac"], mr.inputs["Value"])
mu = n.new("ShaderNodeMath"); mu.operation = "MULTIPLY"; l.new(mr.outputs["Result"], mu.inputs[0]); l.new(nz.outputs["Fac"], mu.inputs[1])
mc = n.new("ShaderNodeMix"); mc.data_type = "RGBA"; mc.inputs["A"].default_value = (0.8, 0.74, 0.6, 1); mc.inputs["B"].default_value = (0.16, 0.16, 0.2, 1)
l.new(mr.outputs["Result"], mc.inputs["Factor"]); l.new(mc.outputs["Result"], b.inputs["Base Color"])
MS = bpy.data.objects.new("Manuscript", None); C_STUDIO.objects.link(MS)
N_SHEETS = 50; W, H = 0.11, 0.16; T = 0.00028
for k in range(N_SHEETS):
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=10, y_subdivisions=14, size=1, location=(0, 0, 0))
    s = bpy.context.object; s.name = f"Sheet{k:02d}"
    for v in s.data.vertices:
        v.co.x *= W; v.co.y *= H
        v.co.z = k * T * 2 + 0.0006 * math.sin(v.co.x * 40 + k) + 0.0004 * math.sin(v.co.y * 31 + k * 0.7)
    sk = s.shape_key_add(name="Basis"); sk2 = s.shape_key_add(name="Punch"); sk2.value = 0
    for i, v in enumerate(s.data.vertices):
        r = math.hypot(v.co.x - 0.012, v.co.y - 0.01)
        sk2.data[i].co.z = v.co.z + 0.006 * math.exp(-(r / 0.012) ** 2)
    s.data.materials.append(paper_m); link(s, C_STUDIO); s.parent = MS
    bpy.ops.object.shade_smooth()
# fold edge (rounded spine of the folded stack)
bpy.ops.mesh.primitive_cylinder_add(radius=N_SHEETS * T, depth=W, location=(0, H / 2, N_SHEETS * T), rotation=(0, R_(90), 0), vertices=24)
fe = bpy.context.object; fe.name = "ManuscriptFold"; fe.data.materials.append(paper_m); link(fe, C_STUDIO); fe.parent = MS
# hole decal on the top sheet (keyed later)
# glasses case: rounded steel box with a hinge line, dent shape key
bpy.ops.mesh.primitive_cube_add(size=1)
gc = bpy.context.object; gc.name = "GlassesCase"; gc.scale = (0.155, 0.06, 0.026); bpy.ops.object.transform_apply(scale=True)
bv = gc.modifiers.new("Bevel", "BEVEL"); bv.width = 0.011; bv.segments = 6
bpy.ops.object.modifier_apply(modifier="Bevel")
bpy.ops.object.mode_set(mode="EDIT"); bpy.ops.mesh.subdivide(number_cuts=6); bpy.ops.object.mode_set(mode="OBJECT")
gc.shape_key_add(name="Basis"); dk = gc.shape_key_add(name="Dent")
for i, v in enumerate(gc.data.vertices):
    r = math.hypot(v.co.x - 0.02, v.co.y - 0.0)
    if v.co.z < 0: dk.data[i].co.z = v.co.z + 0.007 * math.exp(-(r / 0.009) ** 2)
steel = flat("BrushedSteel", (0.5, 0.5, 0.52), rough=0.32, metal=1.0)
bs = steel.node_tree.nodes["Principled BSDF"]; bs.inputs["Anisotropic"].default_value = 0.6
gc.data.materials.append(steel); link(gc, C_STUDIO); bpy.ops.object.shade_smooth()
box("CaseHinge", (0.15, 0.004, 0.004), (0, 0.03, 0.013), steel, C_STUDIO).parent = gc
# bullet (round-nose lead slug), heat streak
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.0045, segments=24, ring_count=12)
bl = bpy.context.object; bl.name = "Bullet"
for v in bl.data.vertices:
    if v.co.y > 0: v.co.y *= 1.0
    else: v.co.y = v.co.y * 2.4
bl.data.materials.append(flat("Lead", (0.42, 0.42, 0.44), 0.35, 0.9)); link(bl, C_STUDIO); bpy.ops.object.shade_smooth()
bpy.ops.mesh.primitive_cone_add(radius1=0.0035, radius2=0.0, depth=0.06, location=(0, -0.035, 0), rotation=(R_(90), 0, 0), vertices=16)
trail = bpy.context.object; trail.name = "BulletTrail"
tm = flat("Trail", (1, 0.9, 0.7), emit=(1, 0.85, 0.6), es=4, alpha=0.35); tm.blend_method = "BLEND" if hasattr(tm, "blend_method") else None
trail.data.materials.append(tm); link(trail, C_STUDIO); trail.parent = bl
# anatomy: ribs from CC-BY skeleton (Samy Belaloui), lungs CC-BY (alejandro8976)
sroot, sparts = glb(A + "/models/skeleton.glb", C_STUDIO, "SkeletonSrc")
for p in sparts:
    if p.type == "MESH" and not p.name.startswith("Rib Cage"):
        bpy.data.objects.remove(p, do_unlink=True)
lroot2, lparts2 = glb(A + "/models/lungs.glb", C_STUDIO, "LungsSrc")
# bone and lung look: clean glossy explainer
bone_m = flat("BoneClean", (0.88, 0.84, 0.74), 0.35); bone_m.node_tree.nodes["Principled BSDF"].inputs["Subsurface Weight"].default_value = 0.2
for o in C_STUDIO.objects:
    if o.type == "MESH" and o.parent and o.parent.name.startswith("SkeletonSrc") or (o.type == "MESH" and o.name.startswith(("Rib", "Spine", "spine"))):
        o.data.materials.clear(); o.data.materials.append(bone_m)
muscle = flat("ChestMuscle", (0.55, 0.12, 0.1), 0.45)
muscle.node_tree.nodes["Principled BSDF"].inputs["Subsurface Weight"].default_value = 0.3
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.035, segments=32, ring_count=16)
mp = bpy.context.object; mp.name = "MusclePatch"; mp.scale = (1.0, 0.3, 1.0); bpy.ops.object.transform_apply(scale=True)
mp.data.materials.append(muscle); link(mp, C_STUDIO); bpy.ops.object.shade_smooth()
bpy.ops.mesh.primitive_torus_add(major_radius=0.03, minor_radius=0.0015)
gr = bpy.context.object; gr.name = "GapRing"; gr.data.materials.append(flat("GapGlow", (0.3, 0.9, 1), emit=(0.3, 0.9, 1.0), es=6)); link(gr, C_STUDIO)

# ================================================================== CROWD LIBRARY: variants are kept hidden; instances made in the animate step
for nm in ("CrowdA", "CrowdB", "CrowdC", "CrowdD", "CrowdE", "CrowdF"):
    rig = bpy.data.objects[nm]; link(rig, C_CROWD)
    for ch in rig.children: link(ch, C_CROWD)
TINTS = {"CrowdA": (0.35, 0.3, 0.26), "CrowdB": (0.22, 0.22, 0.25), "CrowdC": (0.45, 0.25, 0.22), "CrowdD": (0.3, 0.27, 0.22), "CrowdE": (0.33, 0.3, 0.25), "CrowdF": (0.3, 0.32, 0.38)}
for nm, tint in TINTS.items():   # period wool tones instead of modern blue denim
    for ch in bpy.data.objects[nm].children:
        if ch.type != "MESH" or not any(k in ch.name for k in ("suit", "fedora")): continue
        for m in ch.data.materials:
            for nd in list(m.node_tree.nodes):
                if nd.type == "TEX_IMAGE" and nd.image and "diffuse" in nd.image.name.lower():
                    for lk in list(nd.outputs["Color"].links):
                        bw_ = m.node_tree.nodes.new("ShaderNodeRGBToBW"); mx = m.node_tree.nodes.new("ShaderNodeMix"); mx.data_type = "RGBA"; mx.blend_type = "MULTIPLY"
                        mx.inputs["Factor"].default_value = 1.0; mx.inputs["B"].default_value = (*[c * 2.2 for c in tint], 1)
                        m.node_tree.links.new(nd.outputs["Color"], bw_.inputs[0]); m.node_tree.links.new(bw_.outputs[0], mx.inputs["A"]); m.node_tree.links.new(mx.outputs["Result"], lk.to_socket)
hero = bpy.data.objects["Hero"]
# overcoat tint (charcoal) on the hero suit, fedora prop made from CrowdA's hat later
for ch in hero.children:
    if ch.type == "MESH" and "elegantsuit" in ch.name:
        for m in ch.data.materials:
            for nd in list(m.node_tree.nodes):
                if nd.type == "TEX_IMAGE" and nd.image and "diffuse" in nd.image.name.lower():
                    for lk in list(nd.outputs["Color"].links):
                        mx = m.node_tree.nodes.new("ShaderNodeMix"); mx.data_type = "RGBA"; mx.blend_type = "MULTIPLY"
                        mx.inputs["Factor"].default_value = 1.0; mx.inputs["B"].default_value = (0.28, 0.27, 0.3, 1)
                        m.node_tree.links.new(nd.outputs["Color"], mx.inputs["A"]); m.node_tree.links.new(mx.outputs["Result"], lk.to_socket)
# world: night HDRI, dim
w = sc.world or bpy.data.worlds.new("World"); sc.world = w; w.use_nodes = True
wn = w.node_tree.nodes; wl = w.node_tree.links
env = wn.new("ShaderNodeTexEnvironment"); env.image = img(A + "/tex/hdri/cobblestone_street_night_2k.hdr", "Linear Rec.709")
bg = wn["Background"]; bg.inputs["Strength"].default_value = 0.05; wl.new(env.outputs["Color"], bg.inputs["Color"])
# render settings
r = sc.render; r.engine = "CYCLES"; r.resolution_x, r.resolution_y, r.resolution_percentage = 1080, 1920, 100
r.fps = 60; r.fps_base = 1.0; sc.frame_start, sc.frame_end = 1, 1500
sc.cycles.samples = 48; sc.cycles.adaptive_threshold = 0.05; sc.cycles.use_denoising = True; sc.cycles.denoiser = "OPENIMAGEDENOISE"
sc.cycles.device = "CPU"; sc.view_settings.view_transform = "AgX"; sc.view_settings.look = "AgX - Medium High Contrast"
r.use_motion_blur = True; r.motion_blur_shutter = 0.5
sc["STREET_Z"] = STREET_Z
print("BUILD OK", "objects", len(bpy.data.objects))
bpy.ops.wm.save_as_mainfile(filepath=out)
