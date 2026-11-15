"""All Love Canal sets in one scene, each at its own origin. blender -b work/chars.blend -P 02_sets.py -- work/sets.blend"""
import sys, os
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib.py")).read())
out = sys.argv[sys.argv.index("--") + 1]
random.seed(5)
LIB = coll("LIB"); LIB.hide_render = True; LIB.hide_viewport = True

# ------------------------------------------------------------------ world, look
w = bpy.data.worlds.new("Sky"); sc.world = w; w.use_nodes = True; nt = w.node_tree
env = nt.nodes.new("ShaderNodeTexEnvironment"); env.image = bpy.data.images.load(os.path.join(PH, "hdri", "kloofendal_48d_partly_cloudy_puresky_2k.hdr"))
mpw = nt.nodes.new("ShaderNodeMapping"); tcw = nt.nodes.new("ShaderNodeTexCoord"); nt.links.new(tcw.outputs["Generated"], mpw.inputs[0]); nt.links.new(mpw.outputs[0], env.inputs[0])
mpw.inputs["Rotation"].default_value = (0, 0, R_(140))
bg = nt.nodes["Background"]; nt.links.new(env.outputs[0], bg.inputs[0]); bg.inputs[1].default_value = 1.0
sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", 'SUN')); sc.collection.objects.link(sun)
sun.data.energy = 3.2; sun.data.angle = R_(3); sun.rotation_euler = (R_(42), 0, R_(35)); sun.data.color = (1.0, 0.97, 0.92)
sc.render.engine = 'CYCLES'; sc.render.resolution_x, sc.render.resolution_y = 1080, 1920; sc.render.fps = 60
sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Punchy'

# ------------------------------------------------------------------ shared materials
M_asph = pbr("Asphalt", "asphalt_02", 0.25, tint=(0.75, 0.75, 0.78), coords="Object")
M_walk = pbr("Sidewalk", "concrete_tiles", 0.4, tint=(1.05, 1.05, 1.05), coords="Object")
M_lawn = pbr("Lawn", "leafy_grass", 0.3, tint=(0.55, 0.95, 0.4), coords="Object")
M_farg = mat("FarGrass", (0.18, 0.42, 0.1), 0.9)
M_mud = pbr("Dirt", "brown_mud", 0.2, tint=(1.0, 0.85, 0.7), coords="Object")
M_soil = pbr("SoilWall", "excavated_soil_wall", 0.25, tint=(0.85, 0.65, 0.5), coords="Object")
M_block = pbr("CinderBlock", "concrete_block_wall", 0.5, tint=(1.6, 1.55, 1.4), coords="Object")
M_floorwood = pbr("FloorWood", "laminate_floor_02", 0.5, coords="Object")
M_white = mat("PaintWhite", (0.9, 0.9, 0.88), 0.6)
M_dash = mat("RoadDash", (0.95, 0.95, 0.9), 0.5)
M_curb = mat("Curb", (0.7, 0.7, 0.68), 0.7)
M_tox = mat("Toxic", (0.12, 0.95, 0.02), 0.15, emit=(0.25, 1.0, 0.0), emit_s=4.0, spec=0.5)
M_toxd = mat("ToxicDim", (0.2, 0.9, 0.08), 0.2, emit=(0.25, 0.9, 0.05), emit_s=0.9, spec=0.4)

# ------------------------------------------------------------------ library models
def lib_model(name, size, axis=2, drop=(), rz=0.0):
    ms = import_glb(name)
    bad = [o for o in ms if any(k in (o.name + " ".join(m.name for m in o.data.materials if m)) for k in drop)]
    for o in bad: bpy.data.objects.remove(o, do_unlink=True)
    ms = [o for o in ms if o not in bad]
    if rz:
        for o in ms: o.data.transform(Matrix.Rotation(R_(rz), 4, 'Z'))
    normalize(ms, size, axis)
    o = join(ms, "LIB_" + name); link(o, LIB)
    return o
L_house0 = lib_model("house0", 12.5, axis=0)
L_house5 = lib_model("house5", 6.5, drop=("Grass", "Brick_Rough", "Snow"))
L_fence = lib_model("fence", 1.0, rz=90)                  # runs along Y
L_lamp = lib_model("lamp", 6.0)
L_tree = lib_model("tree", 7.0, drop=("Groundcover", "grass"))
L_drum = lib_model("drum", 0.88)

# ------------------------------------------------------------------ STREET (origin 0,0,0): road along +Y
STREET = coll("SET_street")
road = plane("Road", (7.0, 170), (0, 15, 0.0), M_asph, STREET)
for y in range(-60, 100, 6): plane("Dash.%d" % y, (0.12, 2.6), (0, y, 0.004), M_dash, STREET)
for sx in (-1, 1):
    box("Curb.%d" % sx, (0.18, 170, 0.15), (sx * 3.59, 15, 0.075), M_curb, STREET)
    box("Walk.%d" % sx, (2.4, 170, 0.12), (sx * 4.88, 15, 0.06), M_walk, STREET)
    plane("Lawn.%d" % sx, (60, 170), (sx * 36.1, 15, 0.1), M_lawn, STREET)
plane("Ground_far", (500, 600), (-20, 100, 0.0), M_farg, STREET).location.z = -0.03
HOUSE_Y = [-24, -6, 12, 30, 48, 66, 84]
for sx in (-1, 1):
    for i, y in enumerate(HOUSE_Y):
        src = L_house0 if (i + (sx > 0)) % 2 == 0 else L_house5
        copy_obj(src, "House.%s%d" % ("L" if sx < 0 else "R", i), (sx * 17.5, y, 0.1), rz=(-90 if sx < 0 else 90), c=STREET)
        for k in range(6):                                                   # fence along the lawn front with a gate gap
            yy = y - 8.0 + k * 2.27 + (2.4 if k >= 3 else 0)
            if yy > y + 9: continue
            copy_obj(L_fence, "Fence.%s%d_%d" % ("L" if sx < 0 else "R", i, k), (sx * 6.25, yy + 1.13, 0.1), c=STREET)
        copy_obj(L_tree, "Tree.%s%d" % ("L" if sx < 0 else "R", i), (sx * (10 + random.random() * 3), y + 6 + random.random() * 2, 0.1), rz=random.random() * 360, c=STREET).scale = [0.8 + random.random() * 0.4] * 3
for k, y in enumerate(range(-40, 100, 28)):
    for sx in (-1, 1): copy_obj(L_lamp, "Lamp.%d%d" % (k, sx), (sx * 5.7, y + (14 if sx > 0 else 0), 0.12), rz=(0 if sx < 0 else 180), c=STREET)

exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "02b_sets.py")).read())
bpy.ops.wm.save_as_mainfile(filepath=out)
