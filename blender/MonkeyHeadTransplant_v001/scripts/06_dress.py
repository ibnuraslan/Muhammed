"""v013: dress the bare grey OR (client: "bare grey OR, flat light") — equipment and monitors along the walls the
cameras actually see, warmer motivated light, a warmer floor. Props sit against the walls, away from every camera
path and every character path. blender -b in.blend --python 06_dress.py -- out.blend"""
import bpy, sys, math
from mathutils import Vector as V

OUT = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene
col = bpy.data.collections.get("Dressing") or bpy.data.collections.new("Dressing")
if col.name not in [c.name for c in sc.collection.children]: sc.collection.children.link(col)

def mat(name, rgb, rough=0.5, metal=0.0, emit=None, estr=0.0):
    m = bpy.data.materials.get(name)
    if m: return m
    m = bpy.data.materials.new(name); m.use_nodes = True
    p = m.node_tree.nodes["Principled BSDF"]
    p.inputs["Base Color"].default_value = (*rgb, 1); p.inputs["Roughness"].default_value = rough; p.inputs["Metallic"].default_value = metal
    if emit:
        p.inputs["Emission Color"].default_value = (*emit, 1); p.inputs["Emission Strength"].default_value = estr
    return m
def box(name, size, loc, m, rz=0.0, bevel=0.006):
    me = bpy.data.meshes.new(name); o = bpy.data.objects.new(name, me); col.objects.link(o)
    import bmesh
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0); bm.to_mesh(me); bm.free()
    o.scale = size; o.location = loc; o.rotation_euler.z = math.radians(rz); me.materials.append(m)
    if bevel:
        b = o.modifiers.new("bev", "BEVEL"); b.width = bevel; b.segments = 2; b.limit_method = "ANGLE"
    for p_ in me.polygons: p_.use_smooth = False
    return o
def cyl(name, r, h, loc, m, rot=(0, 0, 0), seg=24):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=h, location=loc, rotation=rot, vertices=seg)
    o = bpy.context.active_object; o.name = name
    for c in o.users_collection: c.objects.unlink(o)
    col.objects.link(o); o.data.materials.append(m); bpy.ops.object.shade_smooth() if False else None
    for p_ in o.data.polygons: p_.use_smooth = True
    return o

CREAM = mat("D_Enamel", (0.82, 0.80, 0.72), 0.35)
STEEL = mat("D_Steel", (0.75, 0.76, 0.78), 0.25, 0.9)
DARK = mat("D_Panel", (0.05, 0.06, 0.06), 0.4)
RED = mat("D_CartRed", (0.55, 0.06, 0.05), 0.4)
GAS_BLUE = mat("D_GasBlue", (0.08, 0.18, 0.45), 0.3)
GAS_GREEN = mat("D_GasGreen", (0.12, 0.35, 0.18), 0.3)
SCREEN = mat("D_Screen", (0.01, 0.03, 0.02), 0.2, emit=(0.15, 0.85, 0.35), estr=1.6)
LIGHTBOX = mat("D_Lightbox", (0.9, 0.95, 1.0), 0.3, emit=(0.85, 0.92, 1.0), estr=2.5)
FILM = mat("D_Film", (0.05, 0.06, 0.08), 0.3)
BOXES = [mat("D_Box%d" % i, c, 0.7) for i, c in enumerate(((0.75, 0.68, 0.5), (0.62, 0.72, 0.78), (0.85, 0.85, 0.82), (0.55, 0.62, 0.5)))]
BOTTLE = mat("D_Bottle", (0.45, 0.28, 0.12), 0.15)

# 1. anaesthesia machine + gas cylinders against the front wall (opening background)
ax, ay = -2.2, -3.62
box("AnaMach_Body", (0.70, 0.52, 0.95), (ax, ay, 0.58), CREAM)
box("AnaMach_Top", (0.74, 0.56, 0.05), (ax, ay, 1.08), STEEL)
box("AnaMach_Panel", (0.50, 0.02, 0.30), (ax, ay + 0.27, 0.80), DARK, bevel=0.002)
for k, dx in enumerate((-0.15, 0.0, 0.15)):
    cyl("AnaMach_Gauge%d" % k, 0.05, 0.02, (ax + dx, ay + 0.285, 0.85), STEEL, rot=(math.radians(90), 0, 0))
box("AnaMach_MonBody", (0.42, 0.22, 0.32), (ax, ay - 0.02, 1.28), CREAM)
box("AnaMach_MonScreen", (0.34, 0.01, 0.24), (ax, ay + 0.095, 1.28), SCREEN, bevel=0.0)
for k, dx in enumerate((-0.5, -0.62)):
    cyl("Gas_%d" % k, 0.085, 0.95, (ax + dx, ay + 0.05, 0.48), GAS_BLUE if k == 0 else GAS_GREEN)
    cyl("GasCap_%d" % k, 0.04, 0.08, (ax + dx, ay + 0.05, 0.99), STEEL)
for sx in (-1, 1):
    for sy in (-1, 1):
        cyl("AnaMach_Wheel%d%d" % (sx + 1, sy + 1), 0.035, 0.03, (ax + sx * 0.3, ay + sy * 0.2, 0.035), DARK, rot=(0, math.radians(90), 0))

# 2. steel supply shelf with boxes and bottles (front wall)
sx0, sy0 = -0.75, -3.72
for z in (0.15, 0.6, 1.05, 1.5):
    box("Shelf_%d" % int(z * 100), (1.1, 0.4, 0.025), (sx0, sy0, z), STEEL, bevel=0.002)
for dx in (-0.53, 0.53):
    for dy in (-0.18, 0.18):
        cyl("ShelfPost_%d_%d" % (int(dx * 100), int(dy * 100)), 0.012, 1.6, (sx0 + dx, sy0 + dy, 0.8), STEEL, seg=10)
import random
random.seed(13)
for z in (0.6, 1.05, 1.5):
    x = sx0 - 0.48
    while x < sx0 + 0.42:
        if random.random() < 0.3:
            h = random.uniform(0.12, 0.2); cyl("Bottle_%d_%d" % (int(z * 100), int(x * 1000)), 0.04, h, (x + 0.04, sy0, z + h / 2 + 0.013), BOTTLE)
            x += 0.1
        else:
            w = random.uniform(0.14, 0.26); h = random.uniform(0.1, 0.25)
            box("Box_%d_%d" % (int(z * 100), int(x * 1000)), (w, 0.3, h), (x + w / 2, sy0, z + h / 2 + 0.013), random.choice(BOXES), bevel=0.003)
            x += w + 0.02

# 3. x-ray lightbox on the front wall, with two films
box("Lightbox_Frame", (0.95, 0.06, 0.62), (0.75, -3.92, 1.6), CREAM)
box("Lightbox_Glow", (0.86, 0.01, 0.53), (0.75, -3.885, 1.6), LIGHTBOX, bevel=0.0)
for k, dx in enumerate((-0.21, 0.21)):
    box("Lightbox_Film%d" % k, (0.36, 0.005, 0.46), (0.75 + dx, -3.878, 1.6), FILM, bevel=0.0)

# 4. wall monitor on the left wall (opening background)
box("WallMon_Arm", (0.06, 0.25, 0.06), (-3.5, -1.5, 1.95), STEEL)
box("WallMon_Body", (0.06, 0.55, 0.4), (-3.38, -1.5, 1.95), DARK)
box("WallMon_Screen", (0.01, 0.48, 0.33), (-3.345, -1.5, 1.95), SCREEN, bevel=0.0)

# 5. red crash cart and an oxygen cylinder in the recovery corner (end background)
cx0, cy0 = 0.85, 2.55
box("CrashCart_Body", (0.6, 0.48, 0.92), (cx0, cy0, 0.54), RED)
for k, z in enumerate((0.25, 0.45, 0.65, 0.85)):
    box("CrashCart_Drawer%d" % k, (0.52, 0.01, 0.16), (cx0, cy0 - 0.245, z), mat("D_RedLight", (0.7, 0.1, 0.08), 0.35), bevel=0.002)
    box("CrashCart_Handle%d" % k, (0.3, 0.02, 0.015), (cx0, cy0 - 0.255, z + 0.04), STEEL, bevel=0.0)
box("CrashCart_Top", (0.64, 0.52, 0.03), (cx0, cy0, 1.015), STEEL, bevel=0.002)
cyl("O2_Cyl", 0.08, 1.0, (1.75, 2.45, 0.5), GAS_GREEN)
cyl("O2_Cap", 0.035, 0.09, (1.75, 2.45, 1.04), STEEL)

# 6. warmer, motivated light: an overhead warm key on the tables and a warm practical-side key in the recovery corner
def area(name, loc, tgt, size, energy, color):
    ld = bpy.data.lights.new(name, "AREA"); ld.size = size; ld.energy = energy; ld.color = color
    o = bpy.data.objects.new(name, ld); col.objects.link(o); o.location = loc
    o.rotation_mode = "QUATERNION"; o.rotation_quaternion = (V(tgt) - V(loc)).to_track_quat("-Z", "Y")
    return o
area("Key_WarmOR", (-1.0, -2.2, 2.85), (0.0, 0.0, 1.0), 1.6, 380.0, (1.0, 0.84, 0.66))
area("Key_WarmCorner", (1.2, -0.9, 2.7), (2.35, 1.0, 0.8), 1.2, 230.0, (1.0, 0.82, 0.62))
area("Rim_Cool", (3.6, 2.4, 2.6), (2.35, 1.0, 1.0), 0.8, 120.0, (0.75, 0.88, 1.0))

# 7. warmer floor (was flat grey)
fm = bpy.data.materials.get("M_Floor")
if fm and fm.use_nodes:
    nt = fm.node_tree; p = next((n for n in nt.nodes if n.type == "BSDF_PRINCIPLED"), None)
    if p and p.inputs["Base Color"].links:
        src = p.inputs["Base Color"].links[0].from_socket
        mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = "RGBA"; mx.blend_type = "MULTIPLY"; mx.inputs["Factor"].default_value = 1.0
        mx.inputs["B"].default_value = (1.0, 0.90, 0.76, 1.0)
        nt.links.new(src, mx.inputs["A"]); nt.links.new(mx.outputs["Result"], p.inputs["Base Color"])
print("DRESSED", len(col.objects), "objects")
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("DRESS_SAVED", OUT)
