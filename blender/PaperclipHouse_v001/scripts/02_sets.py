"""All sets for B36 PaperclipHouse, each at its own world offset (floors at z=0).
blender -b build/chars.blend --python 02_sets.py      -> build/sets.blend
STREET native around (0,0) (WaterTubes houses/street), HOME (0,300), OFFICE (30,300), GARAGE (60,300),
STUDIO (100,300), CAMP (0,420), SNOW (0,700), VOID (220,300)."""
import bpy, os, math, glob, random
from mathutils import Vector, Matrix
exec(open(os.path.dirname(__file__) + "/common.py").read())
R = math.radians
sc = bpy.context.scene
random.seed(36)
PH = SCR + "/ph"

def coll(name):
    c = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if c.name not in sc.collection.children: sc.collection.children.link(c)
    return c

def mat(name, col, rough=0.5, metal=0.0, emit=None, es=1.0):
    m = bpy.data.materials.get(name)
    if m: return m
    m = bpy.data.materials.new(name); m.use_nodes = True
    P = m.node_tree.nodes["Principled BSDF"]
    P.inputs["Base Color"].default_value = (*col, 1); P.inputs["Roughness"].default_value = rough
    P.inputs["Metallic"].default_value = metal
    if emit: P.inputs["Emission Color"].default_value = (*emit, 1); P.inputs["Emission Strength"].default_value = es
    return m

def box(name, size, loc, m, col, rot=(0, 0, 0)):
    me = bpy.data.meshes.new(name)
    sx, sy, sz = [s / 2 for s in size]
    vs = [(x, y, z) for x in (-sx, sx) for y in (-sy, sy) for z in (-sz, sz)]
    fs = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
    me.from_pydata(vs, [], fs); me.materials.append(m)
    o = bpy.data.objects.new(name, me); col.objects.link(o)
    o.location = loc; o.rotation_euler = rot
    return o

def plane(name, w, d, loc, m, col, rot=(0, 0, 0), sub=0):
    me = bpy.data.meshes.new(name)
    me.from_pydata([(-w / 2, -d / 2, 0), (w / 2, -d / 2, 0), (w / 2, d / 2, 0), (-w / 2, d / 2, 0)], [], [(0, 1, 2, 3)])
    me.materials.append(m)
    o = bpy.data.objects.new(name, me); col.objects.link(o); o.location = loc; o.rotation_euler = rot
    if sub:
        s = o.modifiers.new("sub", 'SUBSURF'); s.subdivision_type = 'SIMPLE'; s.levels = sub; s.render_levels = sub
    return o

LIBC = bpy.data.collections.new("LIB"); sc.collection.children.link(LIBC)
_lib = {}
TREES = {"fir_a": ("fir_tree_01", "fir_tree_01_a_LOD2"), "fir_b": ("fir_tree_01", "fir_tree_01_b_LOD2"),
         "fir_c": ("fir_tree_01", "fir_tree_01_c_LOD2"), "pine_a": ("pine_tree_01", "pine_tree_01_a_LOD2")}
def ph_lib(pid):
    """append a Poly Haven model once into its own collection under LIB (excluded); returns that collection.
    Rig widgets (wdg_*), graffiti and LOD variants are dropped; trees use one LOD2 mesh."""
    if pid in _lib: return _lib[pid]
    src, only = TREES.get(pid, (pid, None))
    f = glob.glob(f"{PH}/{src}/*.blend")[0]
    with bpy.data.libraries.load(f, link=False) as (fd, td):
        td.objects = [n for n in fd.objects if (only is None or n == only)]
    c = bpy.data.collections.new("LIB_" + pid); LIBC.children.link(c)
    for o in td.objects:
        if o is None or o.type not in ('MESH', 'EMPTY'): continue
        if o.name.startswith("wdg_") or "graffiti" in o.name or "_LOD1" in o.name or ("_LOD2" in o.name and only is None): continue
        if only: o.location = (0, 0, 0)
        c.objects.link(o)
    _lib[pid] = c
    return c

def ph(pid, loc, rotz=0.0, s=1.0, col=None, name=None):
    """collection instance of a PH model"""
    c = ph_lib(pid)
    e = bpy.data.objects.new(name or ("I_" + pid), None); e.instance_type = 'COLLECTION'; e.instance_collection = c
    e.location = loc; e.rotation_euler = (0, 0, R(rotz)); e.scale = (s, s, s)
    col.objects.link(e)
    return e

def ph_real(pid, loc, rotz=0.0, s=1.0, col=None):
    """real (non-instanced) copies of the PH meshes, parented to an empty (for things that are touched / checked)"""
    c = ph_lib(pid)
    e = bpy.data.objects.new("R_" + pid, None); col.objects.link(e)
    for o in c.objects:
        if o.parent is None:
            n = o.copy(); col.objects.link(n); n.parent = e
            for ch in o.children_recursive:
                k = ch.copy(); col.objects.link(k); k.parent = n
    e.location = loc; e.rotation_euler = (0, 0, R(rotz)); e.scale = (s, s, s)
    return e

def sky_window(name, x0, y, z0, w, h, col, frame_m):
    """window frame on a wall at y facing -y, with a bright sky-blue emissive pane behind it"""
    box(name + "_FrT", (w + 0.12, 0.10, 0.06), (x0, y - 0.02, z0 + h / 2 + 0.03), frame_m, col)
    box(name + "_FrB", (w + 0.20, 0.16, 0.06), (x0, y - 0.04, z0 - h / 2 - 0.03), frame_m, col)
    box(name + "_FrL", (0.06, 0.10, h), (x0 - w / 2 - 0.03, y - 0.02, z0), frame_m, col)
    box(name + "_FrR", (0.06, 0.10, h), (x0 + w / 2 + 0.03, y - 0.02, z0), frame_m, col)
    box(name + "_FrM", (0.04, 0.08, h), (x0, y - 0.02, z0), frame_m, col)
    sky = mat("WindowSky", (0.55, 0.80, 0.97), emit=(0.62, 0.85, 1.0), es=1.6)
    plane(name + "_Sky", w, h, (x0, y + 0.02, z0), sky, col, rot=(R(90), 0, 0))

def room(name, ox, oy, w, d, h, wall_m, floor_m, col, win=(), skirt_m=None):
    """floor + back wall (y=+d/2, with window holes) + side walls; open front and no ceiling (sky light from above)"""
    plane(name + "_Floor", w, d, (ox, oy, 0), floor_m, col)
    by = oy + d / 2
    # back wall built around window holes: win = [(x_center_rel, z_center, ww, wh), ...]
    xs = sorted(win, key=lambda t: t[0])
    if not xs:
        box(name + "_WallB", (w, 0.12, h), (ox, by + 0.06, h / 2), wall_m, col)
    else:
        x_prev = -w / 2
        for i, (xc, zc, ww, wh) in enumerate(xs):
            a, b = xc - ww / 2, xc + ww / 2
            if a > x_prev: box(f"{name}_WallB{i}", (a - x_prev, 0.12, h), (ox + (a + x_prev) / 2, by + 0.06, h / 2), wall_m, col)
            box(f"{name}_WallB{i}lo", (ww, 0.12, zc - wh / 2), (ox + xc, by + 0.06, (zc - wh / 2) / 2), wall_m, col)
            top = zc + wh / 2
            box(f"{name}_WallB{i}hi", (ww, 0.12, h - top), (ox + xc, by + 0.06, (h + top) / 2), wall_m, col)
            sky_window(f"{name}_Win{i}", ox + xc, by, zc, ww, wh, col, mat("WinFrame", (0.95, 0.95, 0.95), 0.4))
            x_prev = b
        box(f"{name}_WallBend", (w / 2 - x_prev, 0.12, h), (ox + (w / 2 + x_prev) / 2, by + 0.06, h / 2), wall_m, col)
    box(name + "_WallL", (0.12, d, h), (ox - w / 2 - 0.06, oy, h / 2), wall_m, col)
    box(name + "_WallR", (0.12, d, h), (ox + w / 2 + 0.06, oy, h / 2), wall_m, col)
    sk = skirt_m or mat("Skirt", (0.95, 0.95, 0.93), 0.4)
    box(name + "_SkB", (w, 0.03, 0.10), (ox, by - 0.015, 0.05), sk, col)
    box(name + "_SkL", (0.03, d, 0.10), (ox - w / 2 + 0.015, oy, 0.05), sk, col)
    box(name + "_SkR", (0.03, d, 0.10), (ox + w / 2 - 0.015, oy, 0.05), sk, col)

def wood_floor(name, base=(0.62, 0.42, 0.26)):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree
    P = nt.nodes["Principled BSDF"]; P.inputs["Roughness"].default_value = 0.45
    tc = nt.nodes.new("ShaderNodeTexCoord"); mp = nt.nodes.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (1, 6, 1)
    br = nt.nodes.new("ShaderNodeTexBrick"); br.inputs["Scale"].default_value = 1.2; br.inputs["Mortar Size"].default_value = 0.004
    br.inputs["Color1"].default_value = (*base, 1); br.inputs["Color2"].default_value = (base[0] * 0.85, base[1] * 0.85, base[2] * 0.85, 1)
    br.inputs["Mortar"].default_value = (base[0] * 0.5, base[1] * 0.5, base[2] * 0.5, 1)
    nt.links.new(tc.outputs["Object"], mp.inputs[0]); nt.links.new(mp.outputs[0], br.inputs[0]); nt.links.new(br.outputs[0], P.inputs["Base Color"])
    return m

def noise_mat(name, c1, c2, scale=3.0, rough=0.7, bump=0.15):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree
    P = nt.nodes["Principled BSDF"]; P.inputs["Roughness"].default_value = rough
    tc = nt.nodes.new("ShaderNodeTexCoord")
    nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = scale; nz.inputs["Detail"].default_value = 6
    ramp = nt.nodes.new("ShaderNodeValToRGB"); ramp.color_ramp.elements[0].color = (*c1, 1); ramp.color_ramp.elements[1].color = (*c2, 1)
    nt.links.new(tc.outputs["Object"], nz.inputs[0]); nt.links.new(nz.outputs["Fac"], ramp.inputs[0]); nt.links.new(ramp.outputs[0], P.inputs["Base Color"])
    bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = bump
    nt.links.new(nz.outputs["Fac"], bp.inputs["Height"]); nt.links.new(bp.outputs[0], P.inputs["Normal"])
    return m

# ===================================================================== STREET (WaterTubes houses, street, lamps)
ST = coll("SET_STREET")
f = REPO + "/WaterTubes_v006/WaterTubes_v006_60fps.blend"
with bpy.data.libraries.load(f, link=False) as (fd, td):
    td.collections = [c for c in fd.collections if c in ("Houses", "Set")]
for c in td.collections:
    for o in list(c.all_objects):
        if o.name.startswith(("Hose", "Nozzle", "Sun")) or o.type == 'LIGHT':
            bpy.data.objects.remove(o); continue
    ST.children.link(c)
# street trees: PH-less low-poly: instance a few WaterTubes-free shrubs -> use pine_tree_01 sparsely behind houses
for i, x in enumerate((-34, -12, 10, 33, 55)):
    ph(["fir_a", "fir_c", "fir_b"][i % 3], (x, 9 + (i % 2) * 3, 0), rotz=i * 47, s=1.0, col=ST)
# hero's front lawn mailbox (no text): post + box
mb = mat("MailboxBlue", (0.15, 0.35, 0.75), 0.4, 0.3); post = mat("PostWood", (0.45, 0.32, 0.2), 0.6)
box("Mailbox_Post", (0.08, 0.08, 1.05), (3.0, -10.6, 0.52), post, ST)
box("Mailbox_Box", (0.22, 0.48, 0.24), (3.0, -10.6, 1.13), mb, ST)
box("Mailbox_Flag", (0.02, 0.05, 0.16), (3.12, -10.5, 1.24), mat("FlagRed", (0.85, 0.1, 0.08), 0.4), ST)
sc["STREET"] = (0.0, 0.0)

# ===================================================================== HOME (0,300): kitchen counter + living area
H = coll("SET_HOME"); HX, HY = 0.0, 300.0
room("HOME", HX, HY, 7.0, 5.0, 4.2, mat("HomeWall", (0.55, 0.78, 0.90), 0.6), wood_floor("HomeFloor"), H,
     win=[(-1.9, 1.55, 1.3, 1.2), (1.9, 1.55, 1.3, 1.2)])
top = mat("CounterTop", (0.92, 0.90, 0.86), 0.35); cab = mat("CounterCab", (0.98, 0.98, 0.97), 0.45)
box("HOME_Counter", (1.9, 0.52, 0.88), (HX, HY + 0.35, 0.44), cab, H)
box("HOME_CounterTop", (2.0, 0.60, 0.04), (HX, HY + 0.35, 0.90), top, H)
sc["COUNTER_Z"] = 0.92
box("HOME_BackCab", (2.6, 0.6, 0.9), (HX, HY + 2.18, 0.45), cab, H)
box("HOME_BackTop", (2.6, 0.62, 0.04), (HX, HY + 2.18, 0.92), top, H)
box("HOME_UpperCab", (2.6, 0.35, 0.7), (HX, HY + 2.30, 2.0), cab, H)
ph("Shelf_01", (HX + 2.9, HY + 2.25, 0), rotz=0, col=H)
ph("potted_plant_04", (HX - 3.1, HY + 2.1, 0), col=H)
ph("Sofa_01", (HX - 2.4, HY - 0.6, 0), rotz=90, col=H)
ph("modern_coffee_table_01", (HX - 1.5, HY - 0.6, 0), rotz=90, col=H)
ph("dining_table", (HX + 2.3, HY + 0.6, 0), rotz=90, col=H)
for dy in (-0.45, 0.45): ph("dining_chair_02", (HX + 2.3 - 0.75, HY + 0.6 + dy, 0), rotz=-90, col=H)
for i, c in enumerate([(0.95, 0.75, 0.2), (0.9, 0.3, 0.3), (0.3, 0.6, 0.9)]):      # bowl of fruit-coloured jars on the back counter
    o = box(f"HOME_Jar{i}", (0.10, 0.10, 0.16), (HX - 0.8 + i * 0.16, HY + 2.18, 1.02), mat(f"Jar{i}", c, 0.35), H)
sc["HOME"] = (HX, HY)

# ===================================================================== OFFICE / classroom (30,300): desk, chalkboard, bookshelf
OF = coll("SET_OFFICE"); OX, OY = 30.0, 300.0
room("OFF", OX, OY, 6.5, 5.0, 4.2, mat("OffWall", (0.35, 0.68, 0.80), 0.6), wood_floor("OffFloor", (0.70, 0.55, 0.38)), OF,
     win=[(2.0, 1.6, 1.4, 1.3)])
box("OFF_Board", (2.2, 0.05, 1.1), (OX - 0.8, OY + 2.47, 1.55), mat("Chalkboard", (0.12, 0.32, 0.24), 0.8), OF)
box("OFF_BoardFrame", (2.32, 0.06, 1.22), (OX - 0.8, OY + 2.49, 1.55), mat("BoardFrame", (0.55, 0.38, 0.22), 0.5), OF)
ph("metal_office_desk", (OX, OY + 0.35, 0), rotz=0, col=OF)
ph("desk_lamp_arm_01", (OX + 0.55, OY + 0.55, 0.76), rotz=200, col=OF)
ph("wooden_bookshelf_worn", (OX - 3.0, OY + 1.4, 0), rotz=-90, col=OF)
ph("potted_plant_04", (OX + 2.9, OY + 2.0, 0), col=OF)
sc["OFFICE"] = (OX, OY)

# ===================================================================== GARAGE (60,300): roller door, shelves, tool chest; party lights
G = coll("SET_GARAGE"); GX, GY = 60.0, 300.0
room("GAR", GX, GY, 7.5, 6.0, 4.2, mat("GarWall", (0.70, 0.78, 0.84), 0.7), noise_mat("GarFloor", (0.30, 0.31, 0.33), (0.40, 0.41, 0.43), 4, 0.6, 0.05), G)
ph("rollershutter_door", (GX, GY + 2.95, 0), rotz=0, col=G)
ph("steel_frame_shelves_01", (GX - 3.4, GY + 1.0, 0), rotz=-90, col=G)
ph("steel_frame_shelves_01", (GX - 3.4, GY - 0.6, 0), rotz=-90, col=G)
ph("metal_tool_chest", (GX + 3.3, GY + 1.6, 0), rotz=90, col=G)
ph("tool_cart", (GX + 3.1, GY - 0.3, 0), rotz=90, col=G)
for x in (-1.5, 1.5): ph("hanging_industrial_lamp", (GX + x, GY + 0.5, 2.95), col=G)
# party: string of bulbs across the back + a few balloons (keg party)
PC = coll("PARTY")
bulb = mat("PartyBulb", (1, 0.85, 0.5), 0.3, emit=(1.0, 0.8, 0.45), es=6)
for i in range(16):
    u = i / 15; x = GX - 3.4 + 6.8 * u; z = 2.65 - 0.35 * math.sin(math.pi * u)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.045, location=(x, GY + 2.6, z), segments=12, ring_count=8)
    b = bpy.context.active_object; b.name = f"PartyBulb{i}"; b.data.materials.append(bulb)
    for c in b.users_collection: c.objects.unlink(b)
    PC.objects.link(b)
for i, (x, c) in enumerate([(-2.6, (0.95, 0.2, 0.3)), (-2.3, (0.2, 0.5, 0.95)), (2.4, (0.98, 0.8, 0.15)), (2.7, (0.6, 0.25, 0.85))]):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.16, location=(GX + x, GY + 2.3, 2.2 + 0.15 * (i % 2)), segments=24, ring_count=16)
    b = bpy.context.active_object; b.name = f"Balloon{i}"; b.scale = (1, 1, 1.18); b.data.materials.append(mat(f"Balloon{i}", c, 0.25))
    bpy.ops.object.shade_smooth()
    for cc in b.users_collection: cc.objects.unlink(b)
    PC.objects.link(b)
    box(f"BalloonString{i}", (0.004, 0.004, 1.0), (GX + x, GY + 2.3, 2.2 + 0.15 * (i % 2) - 0.68), mat("String", (0.9, 0.9, 0.9), 0.5), PC)
ph("wooden_picnic_table", (GX + 1.6, GY + 1.2, 0), rotz=0, s=0.9, col=G)     # party table (cups) at the back right
cup = mat("PartyCupRed", (0.85, 0.1, 0.1), 0.4)
for i in range(5):
    bpy.ops.mesh.primitive_cone_add(radius1=0.04, radius2=0.05, depth=0.12, location=(GX + 1.1 + i * 0.22, GY + 1.2 + (i % 2) * 0.12, 0.80))
    b = bpy.context.active_object; b.name = f"PartyCup{i}"; b.data.materials.append(cup)
    for cc in b.users_collection: cc.objects.unlink(b)
    PC.objects.link(b)
sc["GARAGE"] = (GX, GY)

# ===================================================================== STUDIO (100,300): record desk / bar corner / film corner
SD = coll("SET_STUDIO"); SX, SY = 100.0, 300.0
room("STU", SX, SY, 12.0, 7.0, 4.4, mat("StuWall", (0.20, 0.42, 0.78), 0.6), wood_floor("StuFloor", (0.45, 0.30, 0.20)), SD)
# acoustic panels on the back wall
pan = mat("StuPanel", (0.14, 0.30, 0.60), 0.8)
for i in range(6): box(f"STU_Panel{i}", (1.0, 0.06, 1.3), (SX - 5.0 + i * 2.0, SY + 3.45, 1.9), pan, SD)
# record zone (left, x -4): desk + shelf
ph("metal_office_desk", (SX - 4.0, SY + 0.8, 0), col=SD)
ph("wooden_bookshelf_worn", (SX - 5.7, SY + 2.3, 0), rotz=-90, col=SD)
# bar zone (centre): counter + stools + TV on the wall
box("STU_Bar", (2.6, 0.6, 1.05), (SX + 0.2, SY + 2.1, 0.525), mat("BarWood", (0.40, 0.22, 0.12), 0.45), SD)
box("STU_BarTop", (2.7, 0.7, 0.05), (SX + 0.2, SY + 2.1, 1.07), mat("BarTop", (0.12, 0.12, 0.14), 0.3, 0.4), SD)
for x in (-0.6, 0.2, 1.0): ph("bar_chair_round_01", (SX + x, SY + 1.45, 0), col=SD)
ph("Television_01", (SX + 0.2, SY + 3.3, 1.6), s=1.3, col=SD)
# film zone (right, x +4): flood lights + backdrop
ph("flood_lights", (SX + 5.3, SY + 1.8, 0), rotz=-140, col=SD)
ph("flood_lights", (SX + 2.8, SY + 2.6, 0), rotz=200, col=SD)
ph("ArmChair_01", (SX + 4.2, SY + 1.2, 0), rotz=-160, col=SD)
sc["STUDIO"] = (SX, SY)

# ===================================================================== CAMP (0,420): grass, firs, tent, picnic table, fire pit
CP = coll("SET_CAMP"); CX, CY = 0.0, 420.0
gr = noise_mat("CampGrass", (0.25, 0.55, 0.16), (0.40, 0.68, 0.22), 2.0, 0.8, 0.2)
plane("CAMP_Ground", 120, 120, (CX, CY, 0), gr, CP)
for i in range(26):
    a = random.uniform(0, 2 * math.pi); r = random.uniform(9, 30)
    p = (CX + r * math.cos(a), CY + 6 + abs(r * math.sin(a)), 0)
    ph(["fir_a", "fir_b", "fir_c", "fir_b"][i % 4], p, rotz=random.uniform(0, 360), s=random.uniform(0.8, 1.2), col=CP)
ph("wooden_picnic_table", (CX + 0.0, CY + 0.6, 0), col=CP)
ph("stone_fire_pit", (CX + 2.8, CY - 0.4, 0), col=CP)
# blue dome tent (procedural): 4 arched ribs -> skin as a scaled UV half-sphere
bpy.ops.mesh.primitive_uv_sphere_add(radius=1.0, location=(CX - 2.6, CY + 2.2, 0), segments=24, ring_count=12)
t = bpy.context.active_object; t.name = "CAMP_Tent"; t.scale = (1.3, 1.1, 0.95)
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='DESELECT'); bpy.ops.object.mode_set(mode='OBJECT')
for v in t.data.vertices: v.select = v.co.z < -0.001
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.delete(type='VERT'); bpy.ops.object.mode_set(mode='OBJECT')
t.data.materials.append(mat("TentBlue", (0.10, 0.45, 0.85), 0.6)); bpy.ops.object.shade_smooth()
for cc in t.users_collection: cc.objects.unlink(t)
CP.objects.link(t)
box("CAMP_TentDoor", (0.6, 0.02, 0.7), (CX - 2.6, CY + 2.2 - 1.09, 0.35), mat("TentDoor", (0.05, 0.22, 0.45), 0.7), CP)
sc["CAMP"] = (CX, CY)

# ===================================================================== SNOW (0,700): snow field, trail, mountains, firs
SN = coll("SET_SNOW"); NX, NY = 0.0, 700.0
snow = noise_mat("Snow", (0.86, 0.90, 0.97), (0.97, 0.98, 1.0), 1.5, 0.55, 0.12)
g = plane("SNOW_Ground", 400, 400, (NX, NY, 0), snow, SN, sub=0)
bpy.context.view_layer.objects.active = g
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.subdivide(number_cuts=60); bpy.ops.object.mode_set(mode='OBJECT')
for v in g.data.vertices:            # flat inside |x|<12, gentle drifts further out (trail stays flat at z=0)
    d = max(0.0, abs(v.co.x) - 12.0)
    v.co.z = 0.02 * d * d * 0.05 * (1 + 0.6 * math.sin(v.co.y * 0.05) * math.cos(v.co.x * 0.07)) if d > 0 else 0.0
trail = mat("SnowTrail", (0.80, 0.84, 0.92), 0.6)
plane("SNOW_Trail", 4.0, 400, (NX, NY, 0.005), trail, SN)
rock = noise_mat("Mountain", (0.80, 0.84, 0.92), (0.98, 0.99, 1.0), 0.6, 0.6, 0.3)
for i, (mx, my, mh, mr) in enumerate([(-90, 160, 70, 60), (-30, 190, 95, 70), (40, 175, 80, 65), (110, 160, 60, 55), (-150, 120, 55, 50), (160, 130, 65, 55)]):
    bpy.ops.mesh.primitive_cone_add(vertices=48, radius1=mr, depth=mh, location=(NX + mx, NY + my, mh / 2 - 2))
    m_ = bpy.context.active_object; m_.name = f"SNOW_Mtn{i}"
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.subdivide(number_cuts=10); bpy.ops.object.mode_set(mode='OBJECT')
    tx = bpy.data.textures.new(f"MtnTex{i}", 'CLOUDS'); tx.noise_scale = 18 + i * 3
    dm = m_.modifiers.new("disp", 'DISPLACE'); dm.texture = tx; dm.strength = mh * 0.18
    m_.data.materials.append(rock); bpy.ops.object.shade_smooth()
    for cc in m_.users_collection: cc.objects.unlink(m_)
    SN.objects.link(m_)
for i in range(60):
    side = -1 if i % 2 else 1
    x = side * random.uniform(7, 40); y = random.uniform(-60, 120)
    ph(["fir_a", "fir_b", "fir_c", "fir_b"][i % 4], (NX + x, NY + y, 0), rotz=random.uniform(0, 360), s=random.uniform(0.9, 1.4), col=SN)
for i in range(30):                   # trail marker posts (orange tips) every 6 m on the right side
    y = -40 + i * 6
    box(f"SNOW_Post{i}", (0.06, 0.06, 1.1), (NX + 2.6, NY + y, 0.55), mat("PostWood", (0.45, 0.32, 0.2), 0.6), SN)
    box(f"SNOW_PostTip{i}", (0.07, 0.07, 0.18), (NX + 2.6, NY + y, 1.15), mat("PostTip", (1.0, 0.45, 0.05), 0.5), SN)
sc["SNOW"] = (NX, NY)

# ===================================================================== VOID (220,300): bright sky-blue gradient explainer stage
VD = coll("SET_VOID"); VX, VY = 220.0, 300.0
gm = bpy.data.materials.new("SkyGradient"); gm.use_nodes = True; nt = gm.node_tree; nt.nodes.clear()
o_ = nt.nodes.new("ShaderNodeOutputMaterial"); em = nt.nodes.new("ShaderNodeEmission"); em.inputs[1].default_value = 1.0
tc = nt.nodes.new("ShaderNodeTexCoord"); sep = nt.nodes.new("ShaderNodeSeparateXYZ"); rp = nt.nodes.new("ShaderNodeMapRange")
rp.inputs[1].default_value = -0.2; rp.inputs[2].default_value = 0.6
ramp = nt.nodes.new("ShaderNodeValToRGB")
ramp.color_ramp.elements[0].color = (0.08, 0.50, 0.92, 1); ramp.color_ramp.elements[1].color = (0.78, 0.92, 1.0, 1)
nt.links.new(tc.outputs["Normal"], sep.inputs[0]); nt.links.new(sep.outputs[2], rp.inputs[0]); nt.links.new(rp.outputs[0], ramp.inputs[0])
nt.links.new(ramp.outputs[0], em.inputs[0]); nt.links.new(em.outputs[0], o_.inputs[0])
bpy.ops.mesh.primitive_uv_sphere_add(radius=40, location=(VX, VY, 0), segments=48, ring_count=24)
d_ = bpy.context.active_object; d_.name = "VOID_Dome"; d_.data.materials.append(gm); bpy.ops.object.shade_smooth()
d_.visible_shadow = False
for cc in d_.users_collection: cc.objects.unlink(d_)
VD.objects.link(d_)
sc["VOID"] = (VX, VY)


# ===================================================================== props (10_props.py) + DA KRAS FILMS logo decals
with bpy.data.libraries.load(BUILD + "/props.blend", link=False) as (fd, td):
    td.collections = [c for c in fd.collections if c == "PROPS"]
PR = td.collections[0]; sc.collection.children.link(PR)
for o in PR.objects: o.location = (300, 0, -50)          # parked; 03_anim keys them per shot

def logo_decal(name, img, w, parent, loc, rot, col):
    h = w * 414 / 967
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    o_ = nt.nodes.new("ShaderNodeOutputMaterial"); t_ = nt.nodes.new("ShaderNodeTexImage"); t_.image = img; t_.extension = 'CLIP'
    pr = nt.nodes.new("ShaderNodeBsdfPrincipled"); pr.inputs["Roughness"].default_value = 0.5
    tr = nt.nodes.new("ShaderNodeBsdfTransparent"); mx = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(t_.outputs["Color"], pr.inputs["Base Color"]); nt.links.new(t_.outputs["Alpha"], mx.inputs[0])
    nt.links.new(tr.outputs[0], mx.inputs[1]); nt.links.new(pr.outputs[0], mx.inputs[2]); nt.links.new(mx.outputs[0], o_.inputs[0])
    me = bpy.data.meshes.new(name)
    me.from_pydata([(-w / 2, 0, -h / 2), (w / 2, 0, -h / 2), (w / 2, 0, h / 2), (-w / 2, 0, h / 2)], [], [(0, 1, 2, 3)])
    me.uv_layers.new(); uv = me.uv_layers[0].data
    for i, c in enumerate([(0, 0), (1, 0), (1, 1), (0, 1)]): uv[i].uv = c
    me.materials.append(m)
    o = bpy.data.objects.new(name, me); col.objects.link(o); o.parent = parent; o.location = loc; o.rotation_euler = rot
    o.visible_shadow = False
    return o
LW = bpy.data.images.load(REPO + "/assets/brand/DaKrasFilms_logo_white.png"); LW.pack()
LD = bpy.data.images.load(REPO + "/assets/brand/DaKrasFilms_logo_dark.png"); LD.pack()
van = bpy.data.objects["P_Van"]
# van side panels: find the side surface x from the mesh (front at -Y)
xs = [v.co.x for v in van.data.vertices]; vx = max(xs)
zs = [v.co.z for v in van.data.vertices]; vz = (min(zs) + max(zs)) * 0.55
logo_decal("Logo_VanR", LW, 1.6, van, (vx + 0.012, 0.35, vz), (0, 0, R(90)), PR)
logo_decal("Logo_VanL", LW, 1.6, van, (-vx - 0.012, 0.35, vz), (0, 0, R(-90)), PR)
# cardboard box with the dark logo on the garage shelf side (keg-party shots)
bx = box("GAR_LogoBox", (0.55, 0.40, 0.40), (GX - 2.2, GY + 2.55, 0.20), mat("Cardboard", (0.78, 0.60, 0.38), 0.7), G)
logo_decal("Logo_Box", LD, 0.46, bx, (0, -0.205, 0.0), (0, 0, 0), G)
bx2 = box("GAR_LogoBox2", (0.55, 0.40, 0.35), (GX - 2.2, GY + 2.55, 0.575), mat("Cardboard", (0.78, 0.60, 0.38), 0.7), G)

# ===================================================================== world: soft partly-cloudy sky
w = bpy.data.worlds.new("SkyWorld"); sc.world = w; w.use_nodes = True; nt = w.node_tree
env = nt.nodes.new("ShaderNodeTexEnvironment"); env.image = bpy.data.images.load(PH + "/hdri/kloofendal_48d_partly_cloudy_puresky_1k.hdr")
nt.links.new(env.outputs[0], nt.nodes["Background"].inputs[0]); nt.nodes["Background"].inputs[1].default_value = 1.0
sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", 'SUN')); sc.collection.objects.link(sun)
sun.data.energy = 3.2; sun.data.angle = R(8); sun.data.color = (1.0, 0.97, 0.92); sun.rotation_euler = (R(42), R(8), R(-35))
LIBC.hide_render = True; LIBC.hide_viewport = True
for lc in bpy.context.view_layer.layer_collection.children:
    if lc.name == "LIB": lc.exclude = True
bpy.ops.wm.save_as_mainfile(filepath=BUILD + "/sets.blend")
print("SETS saved")
