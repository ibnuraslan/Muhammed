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
        LH = lroot.copy(); C_STREET.objects.link(LH); LH.scale = (0.32,) * 3; LH.location = (x + 0.25, y, STREET_Z + 3.3); LH.rotation_euler = (0, 0, R_(-90))
        for p_ in lparts:
            if p_.parent == lroot: q_ = p_.copy(); C_STREET.objects.link(q_); q_.parent = LH
        pl = bpy.data.lights.new(f"GasLight{i}{y}", "POINT"); pl.energy = 120; pl.color = (1, 0.72, 0.42)
        po = bpy.data.objects.new(f"GasLight{i}{y}", pl); po.location = (x, y, STREET_Z + 3.6); C_STREET.objects.link(po)
FACADE_ROT, SIDE_ROT = R_(0), R_(0)
# ---- real scanned facades (CC-BY) replace the procedural hotel wall; carriage at the kerb
def fit_glb(path, name, height, loc, rot_z, coll):
    root, parts = glb(path, coll, name)
    ms = [o for o in parts if o.type == "MESH"]
    bpy.context.view_layer.update()
    pts = [o.matrix_world @ Vector(c) for o in ms for c in o.bound_box]
    mn = Vector([min(p[i] for p in pts) for i in range(3)]); mx = Vector([max(p[i] for p in pts) for i in range(3)])
    s = height / (mx.z - mn.z)
    root.rotation_mode = "XYZ"; root.scale = (root.scale.x * s, root.scale.y * s, root.scale.z * s)
    bpy.context.view_layer.update()
    pts = [o.matrix_world @ Vector(c) for o in ms for c in o.bound_box]
    mn = Vector([min(p[i] for p in pts) for i in range(3)]); mx = Vector([max(p[i] for p in pts) for i in range(3)])
    root.location -= Vector(((mn.x + mx.x) / 2, (mn.y + mx.y) / 2, mn.z))
    pivot = bpy.data.objects.new(name + "_Pivot", None); coll.objects.link(pivot); root.parent = pivot
    pivot.location = loc; pivot.rotation_euler.z = rot_z
    print("FIT", name, round(s, 4), "size", tuple(round(v, 2) for v in (mx - mn)))
    return pivot, ms
for nm in [o.name for o in C_STREET.objects if o.name.startswith(("HotelWall", "Win_", "Sill_", "Cornice", "Entrance"))]:
    bpy.data.objects.remove(bpy.data.objects[nm], do_unlink=True)
HOTEL, hms = fit_glb(A + "/models/facade_hotel.glb", "HotelFacade", 17.0, (0, 6.9, STREET_Z), FACADE_ROT, C_STREET)
for x in (-19.0, 19.0):
    fit_glb(A + "/models/facade_side.glb", f"SideFacade{int(x)}", 15.0, (x, 6.4, STREET_Z - 2.5), SIDE_ROT, C_STREET)
for nm in [o.name for o in C_STREET.objects if o.name.startswith("SideBld")]:
    bpy.data.objects.remove(bpy.data.objects[nm], do_unlink=True)
box("HotelBack", (60, 0.5, 20), (0, 9.5, STREET_Z + 10), flat("InteriorDark", (0.03, 0.02, 0.015), 0.9), C_STREET)   # rooms behind the scan's open frames
for fl in range(5):
    for k in range(-9, 10):
        if random.random() < 0.6: box(f"RoomLight_{fl}_{k}", (1.4, 0.1, 2.0), (k * 2.2, 9.2, STREET_Z + 3.0 + fl * 3.3), win_lit, C_STREET)
cpiv, cms = fit_glb(A + "/models/carriage.glb", "Carriage", 1.65, (-9.5, 3.0, STREET_Z), R_(90), C_STREET)
# warm lit windows with curtain drapes and mullions (far side of the street)
win_lit.node_tree.nodes.clear()
nt = win_lit.node_tree; n, l = nt.nodes, nt.links
out_ = n.new("ShaderNodeOutputMaterial"); tcw = n.new("ShaderNodeTexCoord"); sp_ = n.new("ShaderNodeSeparateXYZ"); l.new(tcw.outputs["Generated"], sp_.inputs[0])
glow_ = n.new("ShaderNodeValToRGB"); glow_.color_ramp.elements[0].color = (1.0, 0.45, 0.15, 1); glow_.color_ramp.elements[1].color = (1.0, 0.75, 0.4, 1)
l.new(sp_.outputs["Z"], glow_.inputs[0])
cur = n.new("ShaderNodeTexWave"); cur.bands_direction = "X"; cur.inputs["Scale"].default_value = 14; cur.inputs["Distortion"].default_value = 1.5; l.new(tcw.outputs["Generated"], cur.inputs["Vector"])
side = n.new("ShaderNodeMath"); side.operation = "ABSOLUTE"; sub = n.new("ShaderNodeMath"); sub.operation = "SUBTRACT"; sub.inputs[1].default_value = 0.5
l.new(sp_.outputs["X"], sub.inputs[0]); l.new(sub.outputs[0], side.inputs[0])
drape = n.new("ShaderNodeMapRange"); drape.inputs["From Min"].default_value = 0.22; drape.inputs["From Max"].default_value = 0.3; l.new(side.outputs[0], drape.inputs["Value"])
mull = n.new("ShaderNodeMath"); mull.operation = "LESS_THAN"; mull.inputs[1].default_value = 0.025; l.new(side.outputs[0], mull.inputs[0])
dm2 = n.new("ShaderNodeMath"); dm2.operation = "MULTIPLY"; l.new(drape.outputs["Result"], dm2.inputs[0]); l.new(cur.outputs["Fac"], dm2.inputs[1])
dk_ = n.new("ShaderNodeMath"); dk_.operation = "MAXIMUM"; l.new(dm2.outputs[0], dk_.inputs[0]); l.new(mull.outputs[0], dk_.inputs[1])
inv = n.new("ShaderNodeMath"); inv.operation = "SUBTRACT"; inv.inputs[0].default_value = 1.0; l.new(dk_.outputs[0], inv.inputs[1])
st_ = n.new("ShaderNodeMath"); st_.operation = "MULTIPLY"; st_.inputs[1].default_value = 2.2; l.new(inv.outputs[0], st_.inputs[0])
em_ = n.new("ShaderNodeEmission"); l.new(glow_.outputs["Color"], em_.inputs["Color"]); l.new(st_.outputs[0], em_.inputs["Strength"])
l.new(em_.outputs["Emission"], out_.inputs["Surface"])
# blank painted signboard over the canopy (no lettering)
for nm in [o.name for o in C_STREET.objects if o.name.startswith(("Canopy", "Sidewalk"))]:
    bpy.data.objects.remove(bpy.data.objects[nm], do_unlink=True)
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
# footlights: brass reflector hoods with glowing bulbs along the stage lip; follow-spots from the balcony
hood_m = flat("FootHood", (0.35, 0.25, 0.1), 0.35, 1.0); bulb_m = flat("FootBulb", (1, 0.85, 0.6), emit=(1, 0.8, 0.5), es=8)
for k in range(-8, 9):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.12, segments=24, ring_count=12, location=(k * 0.8, -1.9, 0.06))
    hd = bpy.context.object; hd.name = f"FootHood{k}"; hd.scale = (1.2, 0.8, 0.55)
    for v in hd.data.vertices:
        if v.co.y < 0.0: v.co.y = 0.0   # open half-shell facing the stage
    bpy.ops.object.shade_smooth(); hd.data.materials.append(hood_m); link(hd, C_HALL)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.035, location=(k * 0.8, -1.88, 0.07)); bb_ = bpy.context.object; bb_.name = f"FootBulb{k}"
    bb_.data.materials.append(bulb_m); link(bb_, C_HALL); bpy.ops.object.shade_smooth()
for nm, x in (("FollowSpotL", -6.0), ("FollowSpotR", 6.0)):
    lt = bpy.data.lights.new(nm, "SPOT"); lt.energy = 6000; lt.spot_size = R_(9); lt.spot_blend = 0.4; lt.color = (1, 0.92, 0.8); lt.shadow_soft_size = 0.1
    lo = bpy.data.objects.new(nm, lt); lo.location = (x, -21.5, 5.5); C_HALL.objects.link(lo)
    d = Vector((0, 0, 1.4)) - lo.location; lo.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
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
rp = n.new("ShaderNodeValToRGB"); rp.color_ramp.elements[0].color = (0.006, 0.025, 0.08, 1); rp.color_ramp.elements[1].color = (0.12, 0.5, 0.72, 1)
rp.color_ramp.elements[0].position = 0.15; rp.color_ramp.elements[1].position = 0.85
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

# manuscript: 50 real folded sheets (U-folded pages), staggered torn edges, fibre texture, illegible handwriting strokes
paper_m = bpy.data.materials.new("Paper"); paper_m.use_nodes = True
nt = paper_m.node_tree; n, l = nt.nodes, nt.links; b = n["Principled BSDF"]
b.inputs["Roughness"].default_value = 0.8; b.inputs["Subsurface Weight"].default_value = 0.25; b.inputs["Subsurface Radius"].default_value = (0.4, 0.35, 0.25)
tcp = n.new("ShaderNodeTexCoord")
uvs = n.new("ShaderNodeSeparateXYZ"); l.new(tcp.outputs["UV"], uvs.inputs[0])
# fibre colour variation + yellowed edges
fib = n.new("ShaderNodeTexNoise"); fib.inputs["Scale"].default_value = 600; fib.inputs["Detail"].default_value = 6; l.new(tcp.outputs["Object"], fib.inputs["Vector"])
blot = n.new("ShaderNodeTexNoise"); blot.inputs["Scale"].default_value = 40; l.new(tcp.outputs["Object"], blot.inputs["Vector"])
base = n.new("ShaderNodeMix"); base.data_type = "RGBA"; base.inputs["A"].default_value = (0.66, 0.58, 0.42, 1); base.inputs["B"].default_value = (0.76, 0.69, 0.54, 1)
l.new(fib.outputs["Fac"], base.inputs["Factor"])
yel = n.new("ShaderNodeMix"); yel.data_type = "RGBA"; yel.inputs["B"].default_value = (0.62, 0.5, 0.32, 1)
l.new(base.outputs["Result"], yel.inputs["A"])
ym = n.new("ShaderNodeMapRange"); ym.inputs["From Min"].default_value = 0.55; ym.inputs["From Max"].default_value = 0.8; ym.inputs["To Max"].default_value = 0.35
l.new(blot.outputs["Fac"], ym.inputs["Value"]); l.new(ym.outputs["Result"], yel.inputs["Factor"])
# handwriting: ruled bands along the page (UV y), broken into words, wobbly strokes
wv = n.new("ShaderNodeTexWave"); wv.wave_profile = "SAW"; wv.bands_direction = "Y"; wv.inputs["Scale"].default_value = 30
wv.inputs["Distortion"].default_value = 1.5; wv.inputs["Detail"].default_value = 3; l.new(tcp.outputs["UV"], wv.inputs["Vector"])
band = n.new("ShaderNodeMapRange"); band.inputs["From Min"].default_value = 0.7; band.inputs["From Max"].default_value = 0.8; l.new(wv.outputs["Fac"], band.inputs["Value"])
words = n.new("ShaderNodeTexNoise"); words.inputs["Scale"].default_value = 35; words.inputs["Detail"].default_value = 1; l.new(tcp.outputs["UV"], words.inputs["Vector"])
wm = n.new("ShaderNodeMapRange"); wm.inputs["From Min"].default_value = 0.4; wm.inputs["From Max"].default_value = 0.44; l.new(words.outputs["Fac"], wm.inputs["Value"])
strk = n.new("ShaderNodeTexWave"); strk.bands_direction = "X"; strk.inputs["Scale"].default_value = 260; strk.inputs["Distortion"].default_value = 12
strk.inputs["Detail"].default_value = 4; l.new(tcp.outputs["UV"], strk.inputs["Vector"])
sm_ = n.new("ShaderNodeMapRange"); sm_.inputs["From Min"].default_value = 0.35; sm_.inputs["From Max"].default_value = 0.55; l.new(strk.outputs["Fac"], sm_.inputs["Value"])
mrg = n.new("ShaderNodeMapRange"); mrg.inputs["From Min"].default_value = 0.08; mrg.inputs["From Max"].default_value = 0.1; l.new(uvs.outputs["X"], mrg.inputs["Value"])   # left margin
mrg2 = n.new("ShaderNodeMapRange"); mrg2.inputs["From Min"].default_value = 0.94; mrg2.inputs["From Max"].default_value = 0.92; l.new(uvs.outputs["X"], mrg2.inputs["Value"])
ink = n.new("ShaderNodeMath"); ink.operation = "MULTIPLY"; l.new(band.outputs["Result"], ink.inputs[0]); l.new(wm.outputs["Result"], ink.inputs[1])
ink2 = n.new("ShaderNodeMath"); ink2.operation = "MULTIPLY"; l.new(ink.outputs[0], ink2.inputs[0]); l.new(sm_.outputs["Result"], ink2.inputs[1])
ink3 = n.new("ShaderNodeMath"); ink3.operation = "MULTIPLY"; l.new(ink2.outputs[0], ink3.inputs[0]); l.new(mrg.outputs["Result"], ink3.inputs[1])
ink4 = n.new("ShaderNodeMath"); ink4.operation = "MULTIPLY"; l.new(ink3.outputs[0], ink4.inputs[0]); l.new(mrg2.outputs["Result"], ink4.inputs[1])
mc = n.new("ShaderNodeMix"); mc.data_type = "RGBA"; mc.inputs["B"].default_value = (0.09, 0.09, 0.13, 1)
l.new(yel.outputs["Result"], mc.inputs["A"]); l.new(ink4.outputs[0], mc.inputs["Factor"]); l.new(mc.outputs["Result"], b.inputs["Base Color"])
pb_ = n.new("ShaderNodeBump"); pb_.inputs["Strength"].default_value = 0.15; pb_.inputs["Distance"].default_value = 0.0002
l.new(fib.outputs["Fac"], pb_.inputs["Height"]); l.new(pb_.outputs["Normal"], b.inputs["Normal"])
MS = bpy.data.objects.new("Manuscript", None); C_STUDIO.objects.link(MS)
N_SHEETS = 50; W, H = 0.11, 0.16; T = 0.00011; R0 = 0.0007
NX, NS = 18, 64
for k in range(N_SHEETS):
    r = R0 + k * T; L = 2 * H + math.pi * r
    ox, oy = random.uniform(-0.0012, 0.0012), random.uniform(-0.0015, 0.0005)
    bm_ = bmesh.new(); grid = []
    for j in range(NS + 1):
        s = L * j / NS; row = []
        if s < H: y, z = -H / 2 + s, r
        elif s < H + math.pi * r:
            th = (s - H) / r; y, z = H / 2 + r * math.sin(th), r * math.cos(th)
        else: y, z = H / 2 - (s - H - math.pi * r), -r
        for i in range(NX + 1):
            x = -W / 2 + W * i / NX
            ex = 0.0005 * math.sin(x * 900 + k * 3.1) + 0.0003 * math.sin(x * 2300 + k)        # torn bottom edges
            yy = y + (ex if j in (0, NS) else 0.0)
            xx = x + (0.0004 * math.sin(y * 700 + k * 1.7) if i in (0, NX) else 0.0)
            zz = z + 0.00012 * math.sin(x * 120 + k) * math.sin(y * 90 + k * 0.3)
            row.append(bm_.verts.new((xx + ox, yy + oy, zz)))
        grid.append(row)
    for j in range(NS):
        for i in range(NX): bm_.faces.new((grid[j][i], grid[j][i + 1], grid[j + 1][i + 1], grid[j + 1][i]))
    me = bpy.data.meshes.new(f"Sheet{k:02d}"); bm_.to_mesh(me); bm_.free()
    uvl = me.uv_layers.new()
    for poly in me.polygons:
        for li in poly.loop_indices:
            vi = me.loops[li].vertex_index; j, i = divmod(vi, NX + 1); uvl.data[li].uv = (i / NX, j / NS * 2.0 % 1.0001)
    s_ = bpy.data.objects.new(f"Sheet{k:02d}", me); C_STUDIO.objects.link(s_); s_.parent = MS
    me.materials.append(paper_m)
    for poly in me.polygons: poly.use_smooth = True
    s_.shape_key_add(name="Basis"); pun = s_.shape_key_add(name="Punch"); fan = s_.shape_key_add(name="Fan")
    a_k = math.radians(22) * (k / (N_SHEETS - 1)) ** 1.4
    for vi, v in enumerate(me.vertices):
        rr = math.hypot(v.co.x - 0.012, v.co.y - 0.01)
        pun.data[vi].co.z = v.co.z + (0.005 if v.co.z > 0 else 0.005) * math.exp(-(rr / 0.012) ** 2)
        j = vi // (NX + 1); s = L * j / NS
        if s < H:   # front half swings open about the fold
            d = H / 2 - v.co.y
            fan.data[vi].co.y = H / 2 - d * math.cos(a_k); fan.data[vi].co.z = v.co.z + d * math.sin(a_k)
# glasses case: steel clamshell, brushed + worn + small dents, hinge knuckles
bpy.ops.mesh.primitive_cube_add(size=1)
gc = bpy.context.object; gc.name = "GlassesCase"; gc.scale = (0.155, 0.06, 0.026); bpy.ops.object.transform_apply(scale=True)
bv = gc.modifiers.new("Bevel", "BEVEL"); bv.width = 0.012; bv.segments = 8; bpy.ops.object.modifier_apply(modifier="Bevel")
bpy.ops.object.mode_set(mode="EDIT"); bpy.ops.mesh.subdivide(number_cuts=8); bpy.ops.object.mode_set(mode="OBJECT")
for v in gc.data.vertices:   # slight clamshell bulge + seam groove at mid-height + old dings
    v.co.z *= 1.0 + 0.25 * (1 - (2 * v.co.x / 0.155) ** 2) * (1 - (2 * v.co.y / 0.06) ** 2)
    if abs(v.co.z) < 0.0015: v.co.x *= 0.995; v.co.y *= 0.985
    for cx, cy, dd in ((-0.04, 0.01, 0.0012), (0.05, -0.015, 0.0009), (-0.01, -0.02, 0.0007)):
        rr = math.hypot(v.co.x - cx, v.co.y - cy)
        if v.co.z > 0: v.co.z -= dd * math.exp(-(rr / 0.006) ** 2)
gc.shape_key_add(name="Basis"); dk = gc.shape_key_add(name="Dent")
steel = bpy.data.materials.new("BrushedSteel"); steel.use_nodes = True
nt = steel.node_tree; n, l = nt.nodes, nt.links; bs = n["Principled BSDF"]
bs.inputs["Metallic"].default_value = 1.0; bs.inputs["Anisotropic"].default_value = 0.7
tco = n.new("ShaderNodeTexCoord"); mpn = n.new("ShaderNodeMapping"); mpn.inputs["Scale"].default_value = (3.0, 600.0, 600.0); l.new(tco.outputs["Object"], mpn.inputs["Vector"])
brn = n.new("ShaderNodeTexNoise"); brn.inputs["Scale"].default_value = 6; brn.inputs["Detail"].default_value = 8; l.new(mpn.outputs["Vector"], brn.inputs["Vector"])
scr = n.new("ShaderNodeTexNoise"); scr.inputs["Scale"].default_value = 90; scr.inputs["Distortion"].default_value = 3; l.new(tco.outputs["Object"], scr.inputs["Vector"])
rgh = n.new("ShaderNodeMapRange"); rgh.inputs["To Min"].default_value = 0.35; rgh.inputs["To Max"].default_value = 0.6; l.new(brn.outputs["Fac"], rgh.inputs["Value"]); l.new(rgh.outputs["Result"], bs.inputs["Roughness"])
col = n.new("ShaderNodeMix"); col.data_type = "RGBA"; col.inputs["A"].default_value = (0.3, 0.3, 0.31, 1); col.inputs["B"].default_value = (0.52, 0.5, 0.47, 1)
l.new(scr.outputs["Fac"], col.inputs["Factor"]); l.new(col.outputs["Result"], bs.inputs["Base Color"])
sbp = n.new("ShaderNodeBump"); sbp.inputs["Strength"].default_value = 0.08; l.new(brn.outputs["Fac"], sbp.inputs["Height"]); l.new(sbp.outputs["Normal"], bs.inputs["Normal"])
gc.data.materials.append(steel); link(gc, C_STUDIO); bpy.ops.object.shade_smooth()
for kk in range(5):   # hinge knuckles along the back edge
    hx = -0.06 + kk * 0.03
    bpy.ops.mesh.primitive_cylinder_add(radius=0.0028, depth=0.026, location=(hx, 0.031, 0.0), rotation=(0, R_(90), 0), vertices=16)
    hk = bpy.context.object; hk.name = f"CaseHinge{kk}"; hk.data.materials.append(steel); link(hk, C_STUDIO); hk.parent = gc; bpy.ops.object.shade_smooth()
bpy.ops.mesh.primitive_cylinder_add(radius=0.0009, depth=0.15, location=(0, 0.031, 0), rotation=(0, R_(90), 0), vertices=8)
hp = bpy.context.object; hp.name = "CaseHingePin"; hp.data.materials.append(steel); link(hp, C_STUDIO); hp.parent = gc
# bullet: lead round-nose slug, deformed nose (shape key later), soot ring
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.0045, segments=32, ring_count=16)
bl = bpy.context.object; bl.name = "Bullet"
for v in bl.data.vertices:
    if v.co.y < 0: v.co.y *= 2.4
    v.co += v.co.normalized() * 0.00015 * math.sin(v.co.x * 3000) * math.sin(v.co.z * 2700)
lead = bpy.data.materials.new("Lead"); lead.use_nodes = True; lb = lead.node_tree.nodes["Principled BSDF"]
lb.inputs["Base Color"].default_value = (0.36, 0.36, 0.38, 1); lb.inputs["Metallic"].default_value = 0.85; lb.inputs["Roughness"].default_value = 0.38
bl.data.materials.append(lead); link(bl, C_STUDIO); bpy.ops.object.shade_smooth()
# anatomy: ribs from CC-BY skeleton (Samy Belaloui), lungs CC-BY (alejandro8976)
sroot, sparts = glb(A + "/models/skeleton.glb", C_STUDIO, "SkeletonSrc")
for p in sparts:
    if p.type == "MESH" and not p.name.startswith("Rib Cage"):
        bpy.data.objects.remove(p, do_unlink=True)
lroot2, lparts2 = glb(A + "/models/lungs.glb", C_STUDIO, "LungsSrc")
# realistic look: porous bone, wet SSS lungs (model textures kept), fibrous muscle slab
bone_m = bpy.data.materials.new("BonePorous"); bone_m.use_nodes = True
nt = bone_m.node_tree; n, l = nt.nodes, nt.links; bb = n["Principled BSDF"]
bb.inputs["Subsurface Weight"].default_value = 0.35; bb.inputs["Subsurface Radius"].default_value = (0.6, 0.4, 0.25); bb.inputs["Roughness"].default_value = 0.5
tcb = n.new("ShaderNodeTexCoord")
vor = n.new("ShaderNodeTexVoronoi"); vor.inputs["Scale"].default_value = 900; l.new(tcb.outputs["Object"], vor.inputs["Vector"])
nzb = n.new("ShaderNodeTexNoise"); nzb.inputs["Scale"].default_value = 60; nzb.inputs["Detail"].default_value = 8; l.new(tcb.outputs["Object"], nzb.inputs["Vector"])
cb_ = n.new("ShaderNodeMix"); cb_.data_type = "RGBA"; cb_.inputs["A"].default_value = (0.78, 0.7, 0.55, 1); cb_.inputs["B"].default_value = (0.9, 0.86, 0.76, 1)
l.new(nzb.outputs["Fac"], cb_.inputs["Factor"]); l.new(cb_.outputs["Result"], bb.inputs["Base Color"])
bpb = n.new("ShaderNodeBump"); bpb.inputs["Strength"].default_value = 0.35; bpb.inputs["Distance"].default_value = 0.0004
l.new(vor.outputs["Distance"], bpb.inputs["Height"]); l.new(bpb.outputs["Normal"], bb.inputs["Normal"])
for o in C_STUDIO.objects:
    if o.type == "MESH" and o.name.startswith("Rib"):
        o.data.materials.clear(); o.data.materials.append(bone_m)
for o in lparts2:
    if o.type != "MESH": continue
    for m in o.data.materials:
        pb2 = m.node_tree.nodes.get("Principled BSDF")
        if not pb2: continue
        pb2.inputs["Subsurface Weight"].default_value = 0.5; pb2.inputs["Subsurface Radius"].default_value = (0.9, 0.3, 0.25)
        pb2.inputs["Coat Weight"].default_value = 0.6; pb2.inputs["Coat Roughness"].default_value = 0.15; pb2.inputs["Roughness"].default_value = 0.4
        if not pb2.inputs["Base Color"].links: pb2.inputs["Base Color"].default_value = (0.72, 0.45, 0.47, 1)
muscle = bpy.data.materials.new("ChestMuscle"); muscle.use_nodes = True
nt = muscle.node_tree; n, l = nt.nodes, nt.links; mb_ = n["Principled BSDF"]
mb_.inputs["Subsurface Weight"].default_value = 0.45; mb_.inputs["Subsurface Radius"].default_value = (1.0, 0.25, 0.2)
mb_.inputs["Coat Weight"].default_value = 0.7; mb_.inputs["Coat Roughness"].default_value = 0.1; mb_.inputs["Roughness"].default_value = 0.45
tcm = n.new("ShaderNodeTexCoord"); fw = n.new("ShaderNodeTexWave"); fw.bands_direction = "X"; fw.inputs["Scale"].default_value = 90
fw.inputs["Distortion"].default_value = 4; fw.inputs["Detail"].default_value = 6; l.new(tcm.outputs["Object"], fw.inputs["Vector"])
cm_ = n.new("ShaderNodeMix"); cm_.data_type = "RGBA"; cm_.inputs["A"].default_value = (0.32, 0.05, 0.05, 1); cm_.inputs["B"].default_value = (0.6, 0.15, 0.13, 1)
l.new(fw.outputs["Fac"], cm_.inputs["Factor"]); l.new(cm_.outputs["Result"], mb_.inputs["Base Color"])
mbp = n.new("ShaderNodeBump"); mbp.inputs["Strength"].default_value = 0.5; mbp.inputs["Distance"].default_value = 0.0006
l.new(fw.outputs["Fac"], mbp.inputs["Height"]); l.new(mbp.outputs["Normal"], mb_.inputs["Normal"])
# muscle slab: curved fibrous sheet with thickness (pectoral layer over the ribs), irregular outline
bm_ = bmesh.new(); GN = 24; gv = []
for j in range(GN + 1):
    row = []
    for i in range(GN + 1):
        x = (i / GN - 0.5) * 0.11; z = (j / GN - 0.5) * 0.09
        row.append(bm_.verts.new((x, 0.012 * ((x / 0.055) ** 2 + (z / 0.045) ** 2), z)))
    gv.append(row)
for j in range(GN):
    for i in range(GN): bm_.faces.new((gv[j][i], gv[j][i + 1], gv[j + 1][i + 1], gv[j + 1][i]))
me = bpy.data.meshes.new("MusclePatch"); bm_.to_mesh(me); bm_.free()
mp = bpy.data.objects.new("MusclePatch", me); C_STUDIO.objects.link(mp); me.materials.append(muscle)
for poly in me.polygons: poly.use_smooth = True
so_ = mp.modifiers.new("Thick", "SOLIDIFY"); so_.thickness = 0.012
dt = bpy.data.textures.new("MuscleFibre", "WOOD"); dt.wood_type = "BANDNOISE"; dt.noise_scale = 0.02; dt.turbulence = 8
dm_ = mp.modifiers.new("Fibre", "DISPLACE"); dm_.texture = dt; dm_.strength = 0.002; dm_.direction = "Y"

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
