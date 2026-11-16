"""All ChicagoRaised sets in one scene, each at its own origin.
blender -b work/chars.blend -P 02_sets.py -- work/sets.blend
A square + hero building (0,0) | B parlour (300,0) | C swamp (600,0) | D 1850s town (1200,0) | E flood street (1800,0) | F modern skyline (2600,0)"""
import sys, os
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib.py")).read())
out = sys.argv[sys.argv.index("--") + 1]
random.seed(27)
LIB = coll("LIB"); LIB.hide_render = True; LIB.hide_viewport = True
BRAND = os.path.join(FILM, "..", "assets", "brand")

# ------------------------------------------------------------------ world, look
w = bpy.data.worlds.new("Sky"); sc.world = w; w.use_nodes = True; nt = w.node_tree
env = nt.nodes.new("ShaderNodeTexEnvironment"); env.image = bpy.data.images.load(os.path.join(PH, "hdri", "kloofendal_48d_partly_cloudy_puresky_2k.hdr"))
mpw = nt.nodes.new("ShaderNodeMapping"); tcw = nt.nodes.new("ShaderNodeTexCoord"); nt.links.new(tcw.outputs["Generated"], mpw.inputs[0]); nt.links.new(mpw.outputs[0], env.inputs[0])
mpw.inputs["Rotation"].default_value = (0, 0, R_(200))
bg = nt.nodes["Background"]; nt.links.new(env.outputs[0], bg.inputs[0]); bg.inputs[1].default_value = 1.0
sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", 'SUN')); sc.collection.objects.link(sun)
sun.data.energy = 3.4; sun.data.angle = R_(3); sun.rotation_euler = (R_(45), 0, R_(-30)); sun.data.color = (1.0, 0.97, 0.92)
sc.render.engine = 'CYCLES'; sc.render.resolution_x, sc.render.resolution_y = 1080, 1920; sc.render.fps = 60
sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Punchy'

# ------------------------------------------------------------------ materials
M_cob = pbr("Cobbles", "cobblestone_floor_04", 0.35, tint=(1.15, 1.1, 1.05), coords="Object")
M_mud = pbr("Mud", "brown_mud", 0.2, tint=(1.0, 0.85, 0.7), coords="Object")
M_brick = pbr("Brick", "red_brick_03", 0.6, tint=(1.15, 0.95, 0.9), coords="Object")
M_plank = pbr("Planks", "wood_planks_grey", 0.5, tint=(1.1, 0.9, 0.7), coords="Object")
M_timber = pbr("Timber", "rough_wood", 0.6, tint=(1.15, 0.85, 0.6), coords="Object")
M_plaster = pbr("Plaster", "plastered_wall_02", 0.5, tint=(1.05, 0.95, 0.82), coords="Object")
M_iron = mat("JackIron", (0.55, 0.05, 0.03), 0.45, metal=0.3)            # red cast iron (reference: red jacks)
M_steel = mat("Steel", (0.35, 0.35, 0.37), 0.35, metal=0.9)
M_gripwood = mat("GripWood", (0.42, 0.25, 0.12), 0.55)
M_dark = mat("DarkIron", (0.06, 0.06, 0.07), 0.5, metal=0.5)
M_sign = mat("SignBoard", (0.88, 0.84, 0.72), 0.6)
M_water = mat("MudWater", (0.24, 0.17, 0.09), 0.12, spec=0.05)            # opaque muddy brown, low specular (no sky sheet)
M_swampw = mat("SwampWater", (0.16, 0.22, 0.16), 0.2, spec=0.05)
M_reed = mat("Reed", (0.42, 0.55, 0.18), 0.7)
M_reed2 = mat("ReedDry", (0.62, 0.55, 0.30), 0.7)
M_grass = mat("SwampGrass", (0.30, 0.48, 0.14), 0.85)
M_river = mat("River", (0.04, 0.16, 0.24), 0.1, spec=0.3)


def water_bump(m, scale=6.0, strength=0.15):
    nt = m.node_tree; P = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord"); nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = scale
    bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = strength
    nt.links.new(tc.outputs["Object"], nz.inputs["Vector"]); nt.links.new(nz.outputs["Fac"], bp.inputs["Height"]); nt.links.new(bp.outputs["Normal"], P.inputs["Normal"])
water_bump(M_water, 1.5, 0.35); water_bump(M_swampw, 3.0, 0.08); water_bump(M_river, 2.0, 0.1)

def logo_mat(name, png):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; P = nt.nodes["Principled BSDF"]
    t = nt.nodes.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(os.path.join(BRAND, png)); t.extension = 'CLIP'
    nt.links.new(t.outputs["Color"], P.inputs["Base Color"]); nt.links.new(t.outputs["Alpha"], P.inputs["Alpha"])
    P.inputs["Roughness"].default_value = 0.6
    return m

def lib_model(name, size, axis=2, drop=(), rz=0.0, keep=None):
    ms = import_glb(name)
    bad = [o for o in ms if (o.name.split(".")[0] == "Cube" and len(o.data.polygons) <= 6) or any(k in (o.name + " ".join(m.name for m in o.data.materials if m)) for k in drop) or (keep and not keep(o))]
    for o in bad: bpy.data.objects.remove(o, do_unlink=True)
    ms = [o for o in ms if o not in bad]
    if rz:
        for o in ms: o.data.transform(Matrix.Rotation(R_(rz), 4, 'Z'))
    normalize(ms, size, axis)
    o = join(ms, "LIB_" + name); link(o, LIB)
    for p_ in o.data.polygons: p_.use_smooth = False
    return o

def soften(o, sat=1.1, rough=0.45):
    """animated look on scanned/game materials: roughness floor, normal maps down"""
    for m in o.data.materials:
        if not m or not m.use_nodes: continue
        for n in m.node_tree.nodes:
            if n.type == 'BSDF_PRINCIPLED':
                if not n.inputs["Roughness"].is_linked: n.inputs["Roughness"].default_value = max(rough, n.inputs["Roughness"].default_value)
            if n.type == 'NORMAL_MAP': n.inputs["Strength"].default_value = min(n.inputs["Strength"].default_value, 0.35)

# ================================================================== A: the square + hero building (origin 0,0,0)
SQ = coll("SET_square")
# hero building: Victorian corner block (CC-BY), plinth/base slab and manhole removed, scaled to ~16 m, front (-Y) facade at y=0
hb_parts = import_glb("vicbldg")
_drop = [o for o in hb_parts if o.name in ("Object_4", "Object_224") or o.name.startswith("Cube")]
hb_parts = [o for o in hb_parts if o not in _drop]
for o in _drop: bpy.data.objects.remove(o, do_unlink=True)
core = bpy.data.objects["Object_6"]
mn, mx = bbox([core]); k = 16.0 / (mx.z - mn.z)
off = Vector(((mn.x + mx.x) / 2, mn.y, mn.z))
for o in hb_parts: o.data.transform(Matrix.Scale(k, 4) @ Matrix.Translation(-off))
HB = join(hb_parts, "HeroBuilding"); link(HB, SQ); soften(HB)
def window_mat():
    m = bpy.data.materials.new("WindowCurtain"); m.use_nodes = True; nt = m.node_tree; P = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord"); wv = nt.nodes.new("ShaderNodeTexWave"); wv.wave_type = 'BANDS'; wv.bands_direction = 'X'
    wv.inputs["Scale"].default_value = 3.0; wv.inputs["Distortion"].default_value = 1.5; nt.links.new(tc.outputs["Object"], wv.inputs["Vector"])
    rp = nt.nodes.new("ShaderNodeValToRGB"); nt.links.new(wv.outputs["Fac"], rp.inputs[0])
    rp.color_ramp.elements[0].color = (0.16, 0.24, 0.38, 1); rp.color_ramp.elements[1].color = (0.36, 0.48, 0.62, 1)
    nt.links.new(rp.outputs[0], P.inputs["Base Color"]); P.inputs["Roughness"].default_value = 0.35
    P.inputs["Coat Weight"].default_value = 1.0; P.inputs["Coat Roughness"].default_value = 0.03; P.inputs["Coat IOR"].default_value = 1.6
    nt.links.new(rp.outputs[0], P.inputs["Emission Color"]); P.inputs["Emission Strength"].default_value = 0.25
    return m
M_win = window_mat()
HBCOL = {"Material.010": (0.80, 0.72, 0.58), "Material.007": (0.80, 0.72, 0.58), "Material.012": (0.62, 0.52, 0.40), "Material.005": (0.35, 0.28, 0.20),
         "Material.015": (0.70, 0.60, 0.48)}
for i, m in enumerate(HB.data.materials):
    if not m: continue
    if m.name in ("Material.004", "Material.006", "material_0"): HB.data.materials[i] = M_win; continue
    if m.name in HBCOL:
        P_ = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'); P_.inputs["Base Color"].default_value = (*HBCOL[m.name], 1)
hbmn, hbmx = bbox([HB]); print("HERO bbox", hbmn, hbmx)
BW = hbmx.x - hbmn.x; BD = hbmx.y - hbmn.y
# the building rides on an empty (keyed in 03): Z0 = underside of the walls
BLDG = bpy.data.objects.new("Bldg", None); link(BLDG, SQ); BLDG.location = (0, 0, 1.6)
HB.parent = BLDG
# a solid floor slab closes the underside (no see-through void under the raised building)
box("HB_underside", (BW - 0.3, BD - 0.4, 0.25), (0, BD / 2, -0.12), M_timber, SQ).parent = BLDG
# sill: heavy timber beam under the front wall, needle beams through it at every jack
box("Sill", (BW + 0.4, 0.4, 0.32), (0, 0.25, -0.16), M_timber, SQ, bevel=0.01).parent = BLDG
JX = [-6.0, -4.0, -2.0, 0.0, 2.0, 4.0, 6.0]
JX = [x for x in JX if abs(x) < BW / 2 - 0.5]
for i, x in enumerate(JX):
    box("Needle.%d" % i, (0.32, 3.2, 0.3), (x, 1.0, -0.47), M_timber, SQ, bevel=0.01).parent = BLDG
# shop sign over the ground-floor centre (logo placement 1): cream board on the facade, logo decal just proud of it
sg = box("ShopSign", (4.4, 0.08, 1.35), (0, -0.25, 4.35), M_sign, SQ, bevel=0.015); sg.parent = BLDG
lg = plane("Logo_sign", (3.6, 3.6 * 414 / 967), (0, -0.295, 4.35), logo_mat("Logo_dark", "DaKrasFilms_logo_dark.png"), SQ)
lg.rotation_euler = (R_(90), 0, 0); lg.parent = BLDG
print("SIGN z (relative to walls bottom) 4.35; building width", round(BW, 2), "depth", round(BD, 2))

# jackscrews: red cast-iron body + screw + cap (cap and screw ride with the building), worm-drive windlass crank in front
def make_jack(i, x):
    y0 = -0.25
    J = bpy.data.objects.new("Jack.%d" % i, None); link(J, SQ); J.location = (x, y0, 0)
    bpy.ops.mesh.primitive_cone_add(vertices=24, radius1=0.24, radius2=0.12, depth=0.95, location=(x, y0, 0.475)); b = bpy.context.active_object
    b.name = "JackBody.%d" % i; b.data.materials.append(M_iron); link(b, SQ); bpy.ops.object.shade_smooth(); b.parent = J; b.matrix_parent_inverse = J.matrix_world.inverted()
    cyl("JackFoot.%d" % i, 0.3, 0.06, (x, y0, 0.03), M_iron, SQ).parent = J
    cyl("JackCollar.%d" % i, 0.15, 0.08, (x, y0, 0.93), M_iron, SQ).parent = J
    for o in (OB_["JackFoot.%d" % i], OB_["JackCollar.%d" % i]): o.matrix_parent_inverse = J.matrix_world.inverted()
    # screw (2.2 m long, its lower part hidden in the body/ground) and the cap: parented to the building
    sc_ = cyl("Screw.%d" % i, 0.065, 2.2, (x, y0, 0.0), M_steel, SQ)
    sc_.location = (x, y0, BLDG.location.z - 0.62 - 1.1)
    bp = sc_.modifiers.new("thread", 'DISPLACE')   # thread ridges (procedural)
    tx = bpy.data.textures.new("Thread", 'STUCCI'); tx.noise_scale = 0.02; bp.texture = tx; bp.strength = 0.004
    cap = cyl("JackCap.%d" % i, 0.17, 0.08, (x, y0, BLDG.location.z - 0.62 + 0.04), M_iron, SQ)
    for o in (sc_, cap):
        Mw = o.matrix_world.copy(); o.parent = BLDG; o.matrix_parent_inverse = BLDG.matrix_world.inverted()
    # windlass: axle along X at z=1.05, 0.55 in front of the jack axis; uprights outside the crank arms; drive shaft to the body
    ay = y0 - 0.55; az = 1.05
    for sx in (-1, 1):
        u = box("JackUpright.%d%s" % (i, "LR"[sx > 0]), (0.05, 0.12, az + 0.05), (x + sx * 0.36, ay, (az + 0.05) / 2), M_iron, SQ, bevel=0.01); u.parent = J; u.matrix_parent_inverse = J.matrix_world.inverted()
        f_ = box("JackUpFoot.%d%s" % (i, "LR"[sx > 0]), (0.12, 0.32, 0.05), (x + sx * 0.36, ay, 0.025), M_iron, SQ); f_.parent = J; f_.matrix_parent_inverse = J.matrix_world.inverted()
    for sx in (-1, 1):   # stub axles from each upright to its crank arm only: nothing between the arms but the grip
        ax = cyl("JackAxle.%d%s" % (i, "LR"[sx > 0]), 0.025, 0.14, (x + sx * 0.33, ay, az), M_steel, SQ, rot=(0, R_(90), 0)); ax.parent = J; ax.matrix_parent_inverse = J.matrix_world.inverted()
    sh = cyl("JackShaft.%d" % i, 0.022, 0.42, (x + 0.40, ay + 0.21, az), M_steel, SQ, rot=(R_(90), 0, 0)); sh.parent = J; sh.matrix_parent_inverse = J.matrix_world.inverted()
    gb = box("JackGear.%d" % i, (0.16, 0.14, 0.16), (x + 0.33, y0 - 0.17, az - 0.0), M_iron, SQ, bevel=0.015); gb.parent = J; gb.matrix_parent_inverse = J.matrix_world.inverted()
    gb2 = box("JackGearArm.%d" % i, (0.22, 0.08, 0.08), (x + 0.20, y0 - 0.12, az - 0.12), M_iron, SQ); gb2.parent = J; gb2.matrix_parent_inverse = J.matrix_world.inverted()
    # crank pivot (rotation keyed about X in 03), two arms; the grip bar is separate (location keyed, it is a free-turning sleeve)
    P = bpy.data.objects.new("CrankPivot.%d" % i, None); link(P, SQ); P.location = (x, ay, az); P.rotation_mode = 'XYZ'
    for sx in (-1, 1):
        a = box("CrankArm.%d%s" % (i, "LR"[sx > 0]), (0.03, 0.05, 0.16), (x + sx * 0.27, ay, az - 0.06), M_iron, SQ, bevel=0.008)
        a.parent = P; a.matrix_parent_inverse = P.matrix_world.inverted()
    g = cyl("CrankGrip.%d" % i, 0.02, 0.50, (x, ay, az - 0.12), M_gripwood, SQ, rot=(0, R_(90), 0))
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
    g["axle"] = (x, ay, az); g["radius"] = 0.12
    return J
OB_ = bpy.data.objects
for i, x in enumerate(JX): make_jack(i, x)

# cribbing stacks (crisscross timbers) between the jacks and under the building: each layer is its own object (keyed visible in 03)
def crib(name, x, y, layers, z0=0.0, L=1.5, t=0.2):
    objs = []
    for l in range(layers):
        z = z0 + t * l + t / 2
        for k in (-1, 1):
            if l % 2 == 0: o = box("%s.L%02d%s" % (name, l, "ab"[k > 0]), (L, t, t), (x, y + k * (L / 2 - t / 2 - 0.05), z), M_timber, SQ, bevel=0.012)
            else:          o = box("%s.L%02d%s" % (name, l, "ab"[k > 0]), (t, L, t), (x + k * (L / 2 - t / 2 - 0.05), y, z), M_timber, SQ, bevel=0.012)
            objs.append(o)
    return objs
CRIB_X = [(JX[i] + JX[i + 1]) / 2 for i in range(len(JX) - 1)]
for i, x in enumerate(CRIB_X): crib("Crib%d" % i, x, 0.6, 14)
for i, x in enumerate(CRIB_X[::2]): crib("CribB%d" % i, x, 4.5, 14)
# loose timber pile + the timber the worker slides on (S8)
for k in range(6): box("TimberPile.%d" % k, (1.5, 0.2, 0.2), (10.5, -5.0 + (k % 3) * 0.24, 0.1 + 0.2 * (k // 3)), M_timber, SQ, bevel=0.012).rotation_euler = (0, 0, R_(4 * (k - 3)))
box("SlideTimber", (1.5, 0.2, 0.2), (0, 0, 0), M_timber, SQ, bevel=0.012)
# new brick foundation: courses (0.25 m) under the front wall, keyed visible in 03
for c in range(12):
    box("FoundCourse.%02d" % c, (BW - 0.2, 0.42, 0.25), (0, 0.25, 0.125 + 0.25 * c), M_brick, SQ)
box("HandBrick", (0.23, 0.11, 0.075), (0, 0, 0), M_brick, SQ, bevel=0.004)
# ground: cobbled square + surrounding buildings (period brick rows) + far ground
plane("Square", (120, 120), (0, 10, 0), M_cob, SQ)
L_shop = lib_model("shopbldg", 24.0, axis=0); soften(L_shop)
for (x, y, rz) in ((-26, 8, 0), (26, 8, 0), (-30, -26, 180), (2, -34, 180), (30, -28, 180)):
    copy_obj(L_shop, "SqShop.%d" % (x + 100), (x, y, 0), rz=rz, c=SQ)
L_row = lib_model("vicrow", 0.75 * 16.85, keep=lambda o: "polySurface" in o.name); soften(L_row)
copy_obj(L_row, "SqRow", (-40, 60, 0), rz=90, c=SQ)
# crate with nothing on it near the timber pile (props, no text)
for k, (x, y) in enumerate(((11.5, -3.6), (12.2, -3.9))):
    box("Crate.%d" % k, (0.6, 0.6, 0.6), (x, y, 0.3), M_plank, SQ, bevel=0.02)

# ================================================================== B: parlour (300,0): room 6 x 5 x 3.4, open on -Y (camera side)
PA = coll("SET_parlour"); X0 = 300.0
box("PFloor", (6, 5, 0.1), (X0, 2.5, -0.05), M_plank, PA)
box("PWallBack", (6, 0.15, 3.4), (X0, 5.07, 1.7), M_plaster, PA)
box("PWallL", (0.15, 5.2, 3.4), (X0 - 3.07, 2.5, 1.7), M_plaster, PA)
# right wall with a window opening (x = +3): built from 4 pieces around a 1.2 x 1.5 opening centred y=2.6, z=1.0..2.5
for nm, sz, loc in (("PWallR_a", (0.15, 2.0, 3.4), (X0 + 3.07, 1.0, 1.7)), ("PWallR_b", (0.15, 2.0, 3.4), (X0 + 3.07, 4.2, 1.7)),
                    ("PWallR_c", (0.15, 1.2, 1.0), (X0 + 3.07, 2.6, 0.5)), ("PWallR_d", (0.15, 1.2, 0.9), (X0 + 3.07, 2.6, 2.95))):
    box(nm, sz, loc, M_plaster, PA)
box("PCeiling", (6.3, 5.3, 0.12), (X0, 2.5, 3.46), M_plaster, PA)
box("PWainscot", (6, 0.04, 0.9), (X0, 4.98, 0.45), M_timber, PA)
for k, (yy, zz, sy, sz) in enumerate(((2.6, 1.0, 1.32, 0.08), (2.6, 2.5, 1.32, 0.08), (2.0, 1.75, 0.08, 1.5), (3.2, 1.75, 0.08, 1.5), (2.6, 1.75, 0.04, 1.5))):
    box("PWinFrame.%d" % k, (0.2, sy, sz), (X0 + 3.04, yy, zz), mat("WinFrameWhite", (0.92, 0.9, 0.85), 0.5), PA)
# rug
plane("PRug", (2.6, 1.8), (X0 + 0.2, 2.4, 0.005), mat("Rug", (0.55, 0.12, 0.10), 0.9), PA)
# armchair (Poly Haven, CC0), recoloured deep red (reference: red armchair)
def ph_blend(folder, name_hint=None):
    d = os.path.join(PH, folder); f = [x for x in os.listdir(d) if x.endswith(".blend")][0]
    with bpy.data.libraries.load(os.path.join(d, f), link=False) as (src, dst): dst.objects = list(src.objects)
    objs = [o for o in dst.objects if o and o.type == 'MESH']
    for o in objs: sc.collection.objects.link(o)
    bpy.context.view_layer.update()
    return objs
ach = ph_blend("ArmChair_01"); ach = join(ach, "Armchair"); link(ach, PA)
for m in ach.data.materials:
    if m and m.use_nodes:
        nt_ = m.node_tree; P_ = next(n for n in nt_.nodes if n.type == 'BSDF_PRINCIPLED'); t_ = next((n for n in nt_.nodes if n.type == 'TEX_IMAGE' and n.outputs[0].links and n.outputs[0].links[0].to_socket == P_.inputs["Base Color"]), None)
        mx_ = nt_.nodes.new("ShaderNodeMix"); mx_.data_type = 'RGBA'; mx_.blend_type = 'COLOR'; mx_.inputs[0].default_value = 0.85
        if t_: nt_.links.new(t_.outputs[0], mx_.inputs[6])
        mx_.inputs[7].default_value = (0.55, 0.04, 0.04, 1); nt_.links.new(mx_.outputs[2], P_.inputs["Base Color"])
mn, mx = bbox([ach]); print("ARMCHAIR", mn, mx)
ach.location = Vector((X0 + 0.0, 2.9, 0)) - Vector(((mn.x + mx.x) / 2, (mn.y + mx.y) / 2, mn.z)); ach.rotation_euler = (0, 0, 0)
sh_ = ph_blend("Shelf_01"); sh_ = join(sh_, "Bookshelf"); link(sh_, PA); mn, mx = bbox([sh_]); print("SHELF", mn, mx)
k_ = 2.2 / (mx.z - mn.z); sh_.scale = (k_, k_, k_); bpy.context.view_layer.update(); mn, mx = bbox([sh_])
sh_.location += Vector((X0 - 1.9, 4.95, 0)) - Vector(((mn.x + mx.x) / 2, mx.y, mn.z)); bpy.context.view_layer.update(); smn, smx = bbox([sh_])
BOOKC = [mat("BookC%d" % i, c, 0.55) for i, c in enumerate(((0.45, 0.08, 0.06), (0.10, 0.22, 0.40), (0.12, 0.32, 0.15), (0.50, 0.35, 0.12), (0.30, 0.12, 0.30), (0.75, 0.65, 0.45)))]
lv_n = 5
for lvl in range(lv_n):
    z = smn.z + 0.06 + lvl * (smx.z - smn.z - 0.1) / lv_n
    x = smn.x + 0.06; j = 0
    while x < smx.x - 0.08:
        t_ = 0.03 + random.random() * 0.03; h_ = 0.2 + random.random() * 0.08
        b_ = box("Book.%d_%d" % (lvl, j), (t_, 0.17 + random.random() * 0.04, h_), (x + t_ / 2, (smn.y + smx.y) / 2, z + h_ / 2), BOOKC[random.randrange(6)], PA)
        x += t_ + 0.004; j += 1
# the lap book: a closed-looking open book slab (cover + pages), placed in 03
lb = box("LapBook", (0.30, 0.22, 0.035), (X0, 0, 0), mat("BookCover", (0.20, 0.12, 0.30), 0.5), PA, bevel=0.004)
box("LapBookPages", (0.285, 0.205, 0.012), (X0, 0, 0.02), mat("Paper", (0.95, 0.93, 0.86), 0.7), PA).parent = lb
# picture frame (landscape colours, no text) + side table + lamp
box("PFrame", (1.0, 0.05, 0.7), (X0 + 0.6, 4.97, 2.0), M_timber, PA, bevel=0.02)
plane("PPicture", (0.85, 0.55), (X0 + 0.6, 4.94, 2.0), mat("Painting", (0.35, 0.55, 0.65), 0.7), PA).rotation_euler = (R_(90), 0, 0)
cyl("PTable", 0.3, 0.04, (X0 + 1.1, 3.0, 0.62), M_timber, PA); cyl("PTableLeg", 0.04, 0.6, (X0 + 1.1, 3.0, 0.3), M_timber, PA)
# outside the window: a street-front backdrop that slides DOWN as the room rises (keyed in 03)
OUTV = bpy.data.objects.new("WindowView", None); link(OUTV, PA); OUTV.location = (X0 + 12, 2.6, 0); bpy.context.view_layer.update()
v_ = copy_obj(L_shop, "WinViewShop", (X0 + 14, 2.6, -6.0), rz=90, c=PA); v_.parent = OUTV; v_.matrix_parent_inverse = OUTV.matrix_world.inverted()
pv = plane("WinViewGround", (30, 30), (X0 + 12, 2.6, -6.0), M_cob, PA); pv.parent = OUTV; pv.matrix_parent_inverse = OUTV.matrix_world.inverted()
# interior light (soft area through the window + ceiling fill)
L1 = bpy.data.objects.new("PWinLight", bpy.data.lights.new("PWinLight", 'AREA')); link(L1, PA); L1.data.energy = 400; L1.data.size = 1.5
L1.location = (X0 + 3.4, 2.6, 1.8); L1.rotation_euler = (0, R_(-90), 0)
L2 = bpy.data.objects.new("PCeilLight", bpy.data.lights.new("PCeilLight", 'AREA')); link(L2, PA); L2.data.energy = 250; L2.data.size = 3.0
L2.location = (X0, 1.8, 3.3)

# ================================================================== C: swamp (600,0): 400 x 400 m of mud flats, pools, reeds
SW = coll("SET_swamp"); X0 = 600.0
def swamp_mat():
    m = bpy.data.materials.new("SwampGroundMat"); m.use_nodes = True; nt = m.node_tree; P = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord"); nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 0.08; nz.inputs["Detail"].default_value = 6
    nt.links.new(tc.outputs["Object"], nz.inputs["Vector"]); rp = nt.nodes.new("ShaderNodeValToRGB"); nt.links.new(nz.outputs["Fac"], rp.inputs[0])
    el = rp.color_ramp.elements; el[0].position = 0.42; el[0].color = (0.32, 0.25, 0.15, 1); el[1].position = 0.55; el[1].color = (0.26, 0.42, 0.12, 1)
    e3 = el.new(0.7); e3.color = (0.42, 0.52, 0.18, 1)
    nt.links.new(rp.outputs[0], P.inputs["Base Color"]); P.inputs["Roughness"].default_value = 0.9
    return m
g_ = plane("SwampGround", (400, 400), (X0, 100, 0), swamp_mat(), SW, subdiv=80)
d_ = g_.modifiers.new("dsp", 'DISPLACE'); tx = bpy.data.textures.new("SwampNoise", 'CLOUDS'); tx.noise_scale = 25; d_.texture = tx; d_.strength = 2.4; d_.mid_level = 0.5
d_.texture_coords = 'GLOBAL'
plane("SwampWaterPlane", (400, 400), (X0, 100, 0.0), M_swampw, SW)
M_swampw.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.10, 0.20, 0.22, 1)
M_swampw.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.08
M_swampw.node_tree.nodes["Principled BSDF"].inputs["Specular IOR Level"].default_value = 0.35
def reed_clump(name, h, m, n=16):
    bm = bmesh.new()
    for b in range(n):
        a = random.random() * 6.283; tilt = R_(5 + random.random() * 18); hh = h * (0.6 + random.random() * 0.5)
        base = Vector((math.cos(a) * 0.12, math.sin(a) * 0.12, -0.05)); dr = Vector((math.cos(a), math.sin(a), 0))
        top = base + dr * math.sin(tilt) * hh + Vector((0, 0, math.cos(tilt) * hh)); side = Vector((-dr.y, dr.x, 0)) * 0.03
        v = [bm.verts.new(base - side), bm.verts.new(base + side), bm.verts.new(base.lerp(top, 0.6) + side * 0.6), bm.verts.new(top), bm.verts.new(base.lerp(top, 0.6) - side * 0.6)]
        bm.faces.new(v)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free(); o = bpy.data.objects.new(name, me); o.data.materials.append(m); link(o, LIB); return o
RC1 = reed_clump("ReedClump", 2.0, M_reed); RC2 = reed_clump("ReedClumpDry", 1.6, M_reed2)
rc = bpy.data.collections.new("ReedSet"); rc.objects.link(RC1); rc.objects.link(RC2)
def scatter_gn(target, coll_, density, smin, smax, zmin=-0.3):
    ng = bpy.data.node_groups.new("Scatter_" + target.name, 'GeometryNodeTree')
    ng.interface.new_socket("Geometry", in_out='INPUT', socket_type='NodeSocketGeometry'); ng.interface.new_socket("Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')
    N = ng.nodes; L_ = ng.links
    gi = N.new("NodeGroupInput"); go = N.new("NodeGroupOutput")
    dp = N.new("GeometryNodeDistributePointsOnFaces"); dp.inputs["Density"].default_value = density
    pos = N.new("GeometryNodeInputPosition"); sep = N.new("ShaderNodeSeparateXYZ"); cmp_ = N.new("FunctionNodeCompare"); cmp_.data_type = 'FLOAT'; cmp_.operation = 'GREATER_THAN'
    cmp_.inputs[1].default_value = zmin
    L_.new(pos.outputs[0], sep.inputs[0]); L_.new(sep.outputs["Z"], cmp_.inputs[0]); L_.new(cmp_.outputs[0], dp.inputs["Selection"])
    ci = N.new("GeometryNodeCollectionInfo"); ci.inputs["Collection"].default_value = coll_; ci.inputs["Separate Children"].default_value = True; ci.inputs["Reset Children"].default_value = True
    ip = N.new("GeometryNodeInstanceOnPoints"); ip.inputs["Pick Instance"].default_value = True
    def rnd(dt, lo, hi):
        n = N.new("FunctionNodeRandomValue"); n.data_type = dt
        ins = [i for i in n.inputs if i.name in ("Min", "Max") and i.enabled]
        ins[0].default_value = lo; ins[1].default_value = hi
        out = next(o for o in n.outputs if o.enabled)
        return n, out
    rr, rro = rnd('FLOAT_VECTOR', (0, 0, 0), (0, 0, 6.283)); rs, rso = rnd('FLOAT', smin, smax); ri, rio = rnd('INT', 0, 10)
    jg = N.new("GeometryNodeJoinGeometry")
    L_.new(gi.outputs[0], dp.inputs["Mesh"]); L_.new(dp.outputs["Points"], ip.inputs["Points"]); L_.new(ci.outputs[0], ip.inputs["Instance"])
    L_.new(rro, ip.inputs["Rotation"]); L_.new(rso, ip.inputs["Scale"]); L_.new(rio, ip.inputs["Instance Index"])
    L_.new(gi.outputs[0], jg.inputs[0]); L_.new(ip.outputs[0], jg.inputs[0]); L_.new(jg.outputs[0], go.inputs[0])
    md = target.modifiers.new("Scatter", 'NODES'); md.node_group = ng
    return md
scatter_gn(g_, rc, 0.35, 0.7, 1.6)

# ================================================================== D: 1850s town on the mud (1200,0)
TW = coll("SET_town"); X0 = 1200.0
tg = plane("TownGround", (500, 500), (X0, 0, 0), M_mud, TW)
for k in range(40):     # puddles
    p_ = plane("Puddle.%d" % k, (4 + random.random() * 10, 3 + random.random() * 6), (X0 - 120 + random.random() * 240, -120 + random.random() * 240, 0.03), M_water, TW)
    p_.rotation_euler = (0, 0, random.random() * 3)
M_roof = mat("Shingle", (0.30, 0.20, 0.16), 0.8); M_clap = mat("Clapboard", (0.72, 0.62, 0.46), 0.75)
def house(name, x, y, rz, w=6.0, d=9.0, h=5.0):
    b_ = box(name, (w, d, h), (x, y, h / 2), M_clap, TW, bevel=0.05)
    bm = bmesh.new()
    vs = [bm.verts.new(v) for v in ((-w / 2 - 0.3, -d / 2 - 0.3, 0), (w / 2 + 0.3, -d / 2 - 0.3, 0), (0, -d / 2 - 0.3, w * 0.45),
                                    (-w / 2 - 0.3, d / 2 + 0.3, 0), (w / 2 + 0.3, d / 2 + 0.3, 0), (0, d / 2 + 0.3, w * 0.45))]
    for f in ((0, 1, 2), (3, 5, 4), (0, 2, 5, 3), (1, 4, 5, 2), (0, 3, 4, 1)): bm.faces.new([vs[i] for i in f])
    me = bpy.data.meshes.new(name + "_roof"); bm.to_mesh(me); bm.free(); r_ = bpy.data.objects.new(name + "_roof", me); me.materials.append(M_roof); link(r_, TW)
    r_.location = (x, y, h); r_.parent = None
    for o in (b_, r_):
        o.rotation_euler = (0, 0, R_(rz))
    r_.location = (x, y, h)
TOWN = []
for gx in range(-5, 6):
    for gy in range(-5, 6):
        bx, by = X0 + gx * 30, gy * 34
        if gx % 3 == 0: continue            # north-south mud streets
        for k in range(3):
            xx, yy = bx - 8 + k * 9 + random.random(), by + random.random() * 2
            if random.random() < 0.35:
                o = copy_obj(L_shop, "TownB.%d_%d_%d" % (gx, gy, k), (xx, yy, 0), rz=random.choice((0, 180)), c=TW); s_ = 0.32 + random.random() * 0.06; o.scale = (s_, s_, s_)
            else:
                house("TownH.%d_%d_%d" % (gx, gy, k), xx, yy, random.choice((0, 90)), 5 + random.random() * 2, 8 + random.random() * 3, 4 + random.random() * 2.5)
# the lake beyond the town edge
plane("TownLake", (600, 300), (X0, 380, 0.02), M_river, TW)

# ================================================================== E: flood street (1800,0): street along +Y, water at z=0.35
FS = coll("SET_flood"); X0 = 1800.0
plane("FloodGround", (40, 200), (X0, 40, 0), M_mud, FS)
fw = plane("FloodWater", (40, 200), (X0, 40, 0.35), M_water, FS)
for k, y in enumerate(range(-10, 110, 26)):
    copy_obj(L_shop, "FsShopL.%d" % k, (X0 - 11.5, y, 0), rz=-90, c=FS).scale = (0.9, 0.9, 0.9)
L_row2 = L_row.copy(); L_row2.data = L_row.data.copy(); L_row2.name = "LIB_vicrow_painted"; LIB.objects.link(L_row2)
for i, m in enumerate(L_row2.data.materials):
    if m and "lambert52" in m.name:
        m2 = m.copy(); P_ = next(n for n in m2.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
        for l in list(P_.inputs["Base Color"].links): m2.node_tree.links.remove(l)
        P_.inputs["Base Color"].default_value = (0.42, 0.55, 0.40, 1); L_row2.data.materials[i] = m2
for k, y in enumerate(range(-10, 110, 30)):
    copy_obj(L_row2, "FsRowR.%d" % k, (X0 + 13, y, 0), rz=90, c=FS)
for k in range(10):
    pk = box("FloatPlank.%d" % k, (1.2, 0.18, 0.05), (X0 - 4 + random.random() * 8, 5 + random.random() * 60, 0.36), M_plank, FS); pk.rotation_euler = (0, 0, random.random() * 3)
# plank sidewalks along both fronts, partly awash
for sx in (-1, 1):
    box("FsWalk.%d" % sx, (1.8, 200, 0.1), (X0 + sx * 7.6, 40, 0.38), M_plank, FS)
# S21: the raised block at the street end: red brick building on a tall new brick foundation + filled raised street
RB = coll("SET_raised")
plat = box("RaisedStreet", (34, 30, 2.4), (X0, 132, 1.2), M_cob, RB)
fnd = box("RaisedFoundation", (26, 9, 2.4), (X0, 120.5, 1.2), M_brick, RB)
rb = copy_obj(L_shop, "RaisedShop", (X0, 125, 2.4), rz=0, c=RB)
box("RaisedCurb", (34, 0.3, 0.25), (X0, 116.9, 2.52), mat("Curb", (0.7, 0.7, 0.68), 0.7), RB)

# ================================================================== F: modern skyline (2600,0)
MC = coll("SET_modern"); X0 = 2600.0
plane("ModernGround", (1600, 1600), (X0, 300, 0), mat("CityGround", (0.22, 0.23, 0.24), 0.8), MC)
plane("ModernRiver", (1600, 60), (X0, -40, 0.05), M_river, MC)
L_sky = lib_model("skyscrapers", 160.0, axis=2)
for k, (x, y, rz, s_) in enumerate(((0, 120, 0, 1.0), (-140, 200, 90, 1.2), (150, 180, 30, 0.9), (60, 330, 180, 1.35), (-80, 380, 60, 1.1),
                                    (240, 300, 120, 1.0), (-260, 280, 10, 0.85), (20, 520, 200, 1.25))):
    o = copy_obj(L_sky, "Tower.%d" % k, (X0 + x, y, 0), rz=rz, c=MC); o.scale = (s_, s_, s_)
# old blocks in the foreground on the raised bank (cream and red), between the river and the towers
for k, (x, y, rz) in enumerate(((-60, 30, 0), (-25, 32, 0), (15, 30, 0), (55, 34, 0))):
    copy_obj(L_shop, "OldBlock.%d" % k, (X0 + x, y, 0), rz=rz, c=MC).scale = (1.4, 1.4, 1.4)
hb2 = copy_obj(HB, "OldHero", (X0 + 95, 38, 0), c=MC); hb2.parent = None; hb2.location = (X0 + 95, 26, 0); hb2.scale = (1.0, 1.0, 1.0)
# steel truss bridge over the river
for sx in (-1, 1):
    box("BridgeChord.%d" % sx, (0.6, 70, 0.6), (X0 - 10 + sx * 6, -40, 6), mat("BridgeSteel", (0.18, 0.32, 0.45), 0.4, metal=0.6), MC)
    box("BridgeDeckRail.%d" % sx, (0.4, 70, 0.4), (X0 - 10 + sx * 6, -40, 1.2), mat("BridgeSteel", (0.18, 0.32, 0.45), 0.4, metal=0.6), MC)
    for j in range(15):
        d_ = box("BridgeDiag.%d_%d" % (sx, j), (0.3, 0.3, 5.6), (X0 - 10 + sx * 6, -75 + j * 5 + 2.5, 3.6), mat("BridgeSteel", (0.18, 0.32, 0.45), 0.4, metal=0.6), MC)
        d_.rotation_euler = (R_(40 if j % 2 else -40), 0, 0)
box("BridgeDeck", (12, 70, 0.5), (X0 - 10, -40, 0.9), mat("Concrete", (0.6, 0.6, 0.6), 0.8), MC)
box("Embankment", (1600, 6, 1.2), (X0, -7, 0.6), mat("Concrete", (0.6, 0.6, 0.6), 0.8), MC)
box("Embankment2", (1600, 6, 1.2), (X0, -73, 0.6), mat("Concrete", (0.6, 0.6, 0.6), 0.8), MC)

bpy.ops.wm.save_as_mainfile(filepath=out, compress=True)
print("SETS_OK")
