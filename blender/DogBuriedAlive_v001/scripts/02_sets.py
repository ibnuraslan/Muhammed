# DogBuriedAlive: sets. exec'd by 02_build.py (uses its helpers). Four sets far apart in one scene:
#   grave cross-section (x=0), road (x=100), yard with house + driveway + street (x=200), porch close-up set (x=300).
PHD = os.environ.get("DBA_PH", "/tmp/claude-0/-home-user-Muhammed/64f4260c-9e0f-5ce6-b29c-e21d57b5f409/scratchpad/ph/")

def tex_mat(name, tex, tint=(1, 1, 1), scale=1.0, rough=0.6, sat=1.0, bright=0.0, bump=0.3, coord="Object"):
    """Box-projected Poly Haven texture (object coords), tinted; clean look (low bump, roughness >= 0.35)."""
    if name in MATS: return MATS[name]
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree
    pr = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord"); mp = nt.nodes.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (scale,) * 3
    nt.links.new(tc.outputs[coord], mp.inputs["Vector"])
    d = PHD + tex + "/textures/"
    files = os.listdir(d)
    dif = next(f for f in files if "_diff_" in f)
    ti = nt.nodes.new("ShaderNodeTexImage"); ti.image = bpy.data.images.load(d + dif, check_existing=True)
    ti.projection = 'BOX'; ti.projection_blend = 0.3; nt.links.new(mp.outputs["Vector"], ti.inputs["Vector"])
    hs = nt.nodes.new("ShaderNodeHueSaturation"); hs.inputs["Saturation"].default_value = sat; hs.inputs["Value"].default_value = 1.0 + bright
    nt.links.new(ti.outputs["Color"], hs.inputs["Color"])
    mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs["Factor"].default_value = 1.0
    mx.inputs["B"].default_value = (*tint, 1); nt.links.new(hs.outputs["Color"], mx.inputs["A"]); nt.links.new(mx.outputs["Result"], pr.inputs["Base Color"])
    dsp = next((f for f in files if "_disp_" in f), None)
    if dsp and bump > 0:
        di = nt.nodes.new("ShaderNodeTexImage"); di.image = bpy.data.images.load(d + dsp, check_existing=True); di.image.colorspace_settings.name = 'Non-Color'
        di.projection = 'BOX'; di.projection_blend = 0.3; nt.links.new(mp.outputs["Vector"], di.inputs["Vector"])
        bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = bump; bp.inputs["Distance"].default_value = 0.01
        nt.links.new(di.outputs["Color"], bp.inputs["Height"]); nt.links.new(bp.outputs["Normal"], pr.inputs["Normal"])
    pr.inputs["Roughness"].default_value = max(0.35, rough)
    if "Specular IOR Level" in pr.inputs: pr.inputs["Specular IOR Level"].default_value = 0.25
    MATS[name] = m; return m

M_SOIL = tex_mat("Soil", "excavated_soil_wall", (0.92, 0.62, 0.50), 0.8, rough=0.85, sat=1.15, bright=0.10, bump=0.35)
M_FILL = tex_mat("LooseDirt", "red_dirt_mud_01", (0.95, 0.70, 0.55), 1.2, rough=0.9, sat=1.1, bright=0.05, bump=0.35)
M_GRASS = tex_mat("Lawn", "leafy_grass", (0.55, 0.95, 0.40), 0.35, rough=0.8, sat=1.25, bright=0.15, bump=0.2)
M_ASPH = tex_mat("Asphalt", "clean_asphalt", (0.85, 0.85, 0.9), 0.25, rough=0.7, bright=0.05, bump=0.15)
M_CONC = tex_mat("Driveway", "grooved_concrete_driveway", (1.0, 0.98, 0.95), 0.3, rough=0.7, bright=0.10, bump=0.15)
M_PLANK = mat("DeckGrey", (0.55, 0.55, 0.56), 0.6)
M_WHITE = mat("TrimWhite", (0.92, 0.93, 0.94), 0.4)
M_SIDING = mat("SidingBlue", (0.55, 0.68, 0.80), 0.55)
M_GLASS = mat("DoorGlass", (0.10, 0.14, 0.18), 0.08, metal=0.2)
M_CURB = mat("Curb", (0.72, 0.72, 0.70), 0.7)

def jitter_top(o, amp, seed=1, zmin=-0.01):
    """bumpy loose-dirt top: displace the top vertices"""
    random.seed(seed)
    for v in o.data.vertices:
        if v.co.z > zmin: v.co.z += random.uniform(-amp, amp)

def grid_box(name, size, loc, m, c, cuts=24):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.active_object; o.name = name; o.scale = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.subdivide(number_cuts=cuts); bpy.ops.object.mode_set(mode='OBJECT')
    o.data.materials.append(m); move_to(o, c); return o

def boolean(o, cutter, name="cut"):
    md = o.modifiers.new(name, 'BOOLEAN'); md.operation = 'DIFFERENCE'; md.object = cutter; md.solver = 'EXACT'
    md.use_self = False; md.use_hole_tolerant = True
    cutter.hide_render = True; cutter.display_type = 'WIRE'
    return md

def scatter(srcs, n, xr, yr, c, zc=0.0, smin=0.8, smax=1.4, avoid=None, seed=3, prefix="Gr"):
    random.seed(seed); out = []
    for i in range(n):
        x = random.uniform(*xr); y = random.uniform(*yr)
        if avoid and avoid(x, y): continue
        out.append(dup(random.choice(srcs), f"{prefix}{i}", (x, y, zc), (0, 0, random.uniform(0, 6.28)), random.uniform(smin, smax), c))
    return out

GRASS_SRC = [PLANTS[n] for n in PLANTS if "grass_medium_01_" in n and "geonodes" not in n and n.endswith("LOD1") and ("large" in n or "mid" in n or "tall" in n)]
SHRUB_SRC = [PLANTS[n] for n in PLANTS if n.startswith("PH_shrub_02") and n.endswith("LOD1")]
ROCK = PLANTS["PH_rock_09_LOD2"]
# clumps: recoloured rock_09 (a real scan) in the loose-dirt colour
CLUMP_M = mat("ClumpDirt", (0.30, 0.14, 0.07), 0.9)
ROCK.data = ROCK.data.copy(); ROCK.data.materials.clear(); ROCK.data.materials.append(CLUMP_M)

# ================================================================== GRAVE cross-section (x=0). Camera looks +Y at the cut face y=0.
CG = coll("SET_Grave")
PIT = (1.10, 1.10, 1.05)                       # pit width (x), depth into the face (y), depth (z)
SOIL = grid_box("SoilBlock", (3.6, 2.6, 3.4), (0, 1.3, -1.7), M_SOIL, CG, cuts=30)
jitter_top(SOIL, 0.0)
# the top of the block is lawn: top faces get the grass material
SOIL.data.materials.append(M_GRASS)
for p in SOIL.data.polygons:
    if p.normal.z > 0.9: p.material_index = 1
pitcut = rbox("PitCutter", (PIT[0], PIT[1] + 0.02, PIT[2] + 0.2), (0, PIT[1] / 2 - 0.02, -PIT[2] / 2 + 0.1), M_SOIL, CG, bevel=0.0)
boolean(SOIL, pitcut, "pit")
# loose backfill inside the pit (its height is keyed in G01)
FILL = grid_box("Backfill", (PIT[0] - 0.004, PIT[1] - 0.004, 1.0), (0, PIT[1] / 2, -0.5), M_FILL, CG, cuts=16)
for v in FILL.data.vertices: v.co.z += 0.5           # origin at the bottom -> scale z = fill height
FILL.location.z = -PIT[2]
jitter_top(FILL, 0.03, seed=5, zmin=0.49)
# dog pocket (air pocket around the lying dog): ellipsoid cutter, its material = soil
bpy.ops.mesh.primitive_uv_sphere_add(segments=40, ring_count=20, radius=1.0, location=(0, 0.24, -0.76))
POCKET = bpy.context.active_object; POCKET.name = "PocketCutter"; POCKET.scale = (0.74, 0.55, 0.36)
POCKET.data.materials.append(M_FILL); move_to(POCKET, CG)
boolean(FILL, POCKET, "pocket"); boolean(SOIL, POCKET, "pocket")
POCKET_REST = (POCKET.location.copy(), tuple(POCKET.scale))
# tunnel cutter for U13 (capsule that grows upward with the dog)
bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, radius=1.0, location=(0, 0.18, -60))
TUNNEL = bpy.context.active_object; TUNNEL.name = "TunnelCutter"; TUNNEL.scale = (0.42, 0.40, 0.55)
TUNNEL.data.materials.append(M_FILL); move_to(TUNNEL, CG)
boolean(FILL, TUNNEL, "tunnel"); boolean(SOIL, TUNNEL, "tunnel")
# mound on top after the burial (hidden in G01 until the pit is full)
bpy.ops.mesh.primitive_uv_sphere_add(segments=40, ring_count=20, radius=1.0, location=(0, PIT[1] / 2 + 0.02, 0.0))
MOUND_G = bpy.context.active_object; MOUND_G.name = "GraveMound"; MOUND_G.scale = (0.62, 0.62, 0.16)
for v in MOUND_G.data.vertices:
    if v.co.z < 0: v.co.z = 0
MOUND_G.data.materials.append(M_FILL); move_to(MOUND_G, CG); bpy.ops.object.shade_smooth()
boolean(MOUND_G, TUNNEL, "tunnel")
# lawn behind/around the block, grass tufts along the top
LAWN_G = plane("LawnG", (80, 60), (0, 2.6 + 30, 0), M_GRASS, CG)
for sx in (-1, 1):
    plane("LawnGside" + str(sx), (38, 2.6), (sx * (1.8 + 19), 1.3, 0), M_GRASS, CG)
scatter(GRASS_SRC, 260, (-1.8, 1.8), (0.0, 2.6), CG, avoid=lambda x, y: abs(x) < 0.75 and y < PIT[1] + 0.15, seed=11, prefix="GrG")
scatter(GRASS_SRC, 900, (-8, 8), (2.6, 12), CG, seed=12, prefix="GrG2")
scatter(SHRUB_SRC, 10, (-12, 12), (8, 16), CG, smin=1.0, smax=1.6, seed=13, prefix="ShG")
# a shovel standing in the spoil heap beside the grave (nobody holds it)
SPOIL = dup(MOUND_G, "SpoilHeap", (1.15, 1.6, 0), scale=(0.45, 0.45, 0.30), c=CG, linked=False)
SPOIL.modifiers.clear()
SHOV = bpy.data.objects["shovel_GEO"]
print("BUILD shovel", tuple(round(v, 2) for v in SHOV.dimensions), [c.name for c in SHOV.children])
# floor of the world under the block (camera never sees under it, but light bounces)
HOUSE = bpy.data.objects["House"]
dup(HOUSE, "HouseG", (2.5, 17, 0), (0, 0, R_(8)), 1.0, CG)

# ================================================================== ROAD (x=100). Road runs along Y; traffic drives toward -Y.
RX = Vector((100, 0, 0)); CR = coll("SET_Road")
plane("Road", (7.0, 120), RX + Vector((0, 20, 0.0)), M_ASPH, CR)
for sx in (-1, 1):
    rbox("Curb" + str(sx), (0.25, 120, 0.12), RX + Vector((sx * 3.62, 20, 0.04)), M_CURB, CR, bevel=0.02)
    plane("Verge" + str(sx), (30, 120), RX + Vector((sx * (3.75 + 15), 20, 0.0)), M_GRASS, CR)
# white edge lines (paint, no text)
M_LINE = mat("RoadLine", (0.95, 0.95, 0.92), 0.6)
for sx in (-1, 1):
    plane("EdgeLine" + str(sx), (0.12, 120), RX + Vector((sx * 3.2, 20, 0.003)), M_LINE, CR)
for i in range(12):
    plane(f"CentreDash{i}", (0.12, 2.5), RX + Vector((0, -20 + i * 6, 0.003)), M_LINE, CR)
scatter(GRASS_SRC, 300, (3.9, 9), (-10, 40), CR, seed=21, prefix="GrR")
scatter(GRASS_SRC, 300, (-9, -3.9), (-10, 40), CR, seed=22, prefix="GrRL")
for i, (x, y) in enumerate([(-11, 8), (12, 14), (-12, 26), (11, 32), (-10, -2)]):
    dup(HOUSE, f"HouseR{i}", RX + Vector((x, y, 0)), (0, 0, R_(90 if x < 0 else -90)), 0.95, CR)
scatter(SHRUB_SRC, 16, (5, 9), (-6, 40), CR, smin=1.0, smax=1.5, seed=23, prefix="ShR")
scatter(SHRUB_SRC, 16, (-9, -5), (-6, 40), CR, smin=1.0, smax=1.5, seed=24, prefix="ShRL")
PICKUP = bpy.data.objects["Pickup"]

# ================================================================== YARD (x=200): house faces -Y, driveway on +X side, street at y<-6
YX = Vector((200, 0, 0)); CY = coll("SET_Yard")
YHOUSE = dup(HOUSE, "HouseY", YX + Vector((0, 12, 0)), (0, 0, 0), 1.0, CY)
plane("LawnY", (90, 70), YX + Vector((0, 20, 0)), M_GRASS, CY)
plane("Street", (90, 8), YX + Vector((0, -10, 0.004)), M_ASPH, CY)
rbox("CurbY", (90, 0.25, 0.12), YX + Vector((0, -5.9, 0.04)), M_CURB, CY, bevel=0.02)
DRIVE = plane("DrivewayY", (3.6, 16), YX + Vector((6.0, 1.0, 0.006)), M_CONC, CY)
for i, x in enumerate((-16, 16, -32, 32)):
    dup(HOUSE, f"HouseY{i}", YX + Vector((x, 13 + (i % 2), 0)), (0, 0, R_(0)), 1.0, CY)
YMOUND = Vector((200 - 3.8, 3.0, 0))       # the grave in the lawn (left of the path)
scatter(GRASS_SRC, 1400, (-14, 3.8), (-5.5, 7.5), CY, avoid=lambda x, y: (Vector((x, y)) - (YMOUND - YX).to_2d()).length < 1.0, seed=31, prefix="GrY")
for i, gx in enumerate(scatter(GRASS_SRC, 0, (0, 1), (0, 1), CY)): pass
for o in [o for o in CY.objects if o.name.startswith("GrY")]: o.location.x += 200
scatter(SHRUB_SRC, 14, (-4.2, 3.6), (7.4, 8.2), CY, smin=0.9, smax=1.2, seed=32, prefix="ShY")
for o in [o for o in CY.objects if o.name.startswith("ShY")]: o.location.x += 200
MOUND_Y = dup(MOUND_G, "MoundY", YMOUND, scale=(0.75, 0.55, 0.20), c=CY, linked=False)
MOUND_Y.modifiers.clear()
SHOVEL_Y = None
# hole for the dog's exit (Y14): cylinder cutter through the mound and the lawn, a dark soil pit below
bpy.ops.mesh.primitive_cylinder_add(vertices=40, radius=1.0, depth=1.0, location=YMOUND + Vector((0, 0, -60)))
HOLE = bpy.context.active_object; HOLE.name = "HoleCutter"; HOLE.scale = (0.34, 0.40, 1.2); HOLE.data.materials.append(M_FILL); move_to(HOLE, CY)
boolean(MOUND_Y, HOLE, "hole")
LAWNY = bpy.data.objects["LawnY"]; LAWNY.data = LAWNY.data.copy()
bpy.context.view_layer.objects.active = LAWNY
bpy.ops.object.mode_set(mode="EDIT"); bpy.ops.mesh.subdivide(number_cuts=12); bpy.ops.object.mode_set(mode="OBJECT")
boolean(LAWNY, HOLE, "hole")
bpy.ops.mesh.primitive_cylinder_add(vertices=40, radius=0.42, depth=1.4, location=YMOUND + Vector((0, 0, -0.71)))
bpy.ops.mesh.primitive_cylinder_add(vertices=40, radius=0.40, depth=0.004, location=YMOUND + Vector((0, 0, 0.004)))
_hf = bpy.context.active_object; _hf.name = "HoleFloor"; _hf.data.materials.append(M_FILL); move_to(_hf, CY)
bpy.ops.mesh.primitive_cylinder_add(vertices=40, radius=0.42, depth=1.4, location=YMOUND + Vector((0, 0, -0.71)))
PITY = bpy.context.active_object; PITY.name = "ExitPit"; PITY.data.materials.append(M_FILL); move_to(PITY, CY)
for p in PITY.data.polygons: p.flip()
import bmesh as _bm
_pb = _bm.new(); _pb.from_mesh(PITY.data)
_bm.ops.delete(_pb, geom=[f_ for f_ in _pb.faces if f_.calc_center_median().z > 0.6], context='FACES')
_pb.to_mesh(PITY.data); _pb.free()
SUV = bpy.data.objects["SUV"]

# ================================================================== PORCH close-up set (x=300): siding wall, white french doors, plank deck
PX = Vector((300, 0, 0)); CP = coll("SET_Porch")
DECK_Z = 0.55
for i in range(40):
    rbox(f"Plank{i}", (0.135, 4.0, 0.035), PX + Vector((-2.6 + i * 0.14, -0.6, DECK_Z - 0.0175)), M_PLANK, CP, bevel=0.006, seg=2)
rbox("DeckBase", (5.8, 4.0, DECK_Z - 0.04), PX + Vector((0, -0.6, (DECK_Z - 0.04) / 2)), M_WHITE, CP, bevel=0.01)
# siding wall (horizontal lap boards) at y=1.4
for i in range(22):
    rbox(f"Siding{i}", (6.0, 0.03, 0.155), PX + Vector((0, 1.42, DECK_Z + 0.08 + i * 0.15)), M_SIDING, CP, bevel=0.008, seg=2,
         rot=(R_(-6), 0, 0))
# french doors: two leaves with 10 lites each, white frames
DOOR_W, DOOR_H = 0.80, 2.15
for k, x0 in enumerate((-DOOR_W, 0.0)):
    cx = x0 + DOOR_W / 2
    rbox(f"DoorStileL{k}", (0.09, 0.06, DOOR_H), PX + Vector((x0 + 0.045, 1.38, DECK_Z + DOOR_H / 2)), M_WHITE, CP, bevel=0.0)
    rbox(f"DoorStileR{k}", (0.09, 0.06, DOOR_H), PX + Vector((x0 + DOOR_W - 0.045, 1.38, DECK_Z + DOOR_H / 2)), M_WHITE, CP, bevel=0.0)
    rbox(f"DoorRailB{k}", (DOOR_W - 0.18, 0.055, 0.28), PX + Vector((cx, 1.38, DECK_Z + 0.14)), M_WHITE, CP, bevel=0.0)
    rbox(f"DoorRailT{k}", (DOOR_W - 0.18, 0.055, 0.10), PX + Vector((cx, 1.38, DECK_Z + DOOR_H - 0.05)), M_WHITE, CP, bevel=0.0)
    plane(f"DoorGlass{k}", (DOOR_W - 0.16, DOOR_H - 0.36), PX + Vector((cx, 1.40, DECK_Z + 0.28 + (DOOR_H - 0.38) / 2)), M_GLASS, CP, rot=(R_(90), 0, 0))
    for j in range(1, 5):
        rbox(f"DoorMullH{k}{j}", (DOOR_W - 0.16, 0.035, 0.03), PX + Vector((cx, 1.375, DECK_Z + 0.28 + j * (DOOR_H - 0.38) / 5)), M_WHITE, CP, bevel=0.0)
    rbox(f"DoorMullV{k}", (0.03, 0.035, DOOR_H - 0.38), PX + Vector((cx, 1.375, DECK_Z + 0.28 + (DOOR_H - 0.38) / 2)), M_WHITE, CP, bevel=0.0)
rbox("DoorCasingT", (2 * DOOR_W + 0.30, 0.08, 0.16), PX + Vector((0, 1.36, DECK_Z + DOOR_H + 0.08)), M_WHITE, CP, bevel=0.01)
for sx in (-1, 1):
    rbox("DoorCasing" + str(sx), (0.14, 0.08, DOOR_H + 0.1), PX + Vector((sx * (DOOR_W + 0.07), 1.36, DECK_Z + DOOR_H / 2)), M_WHITE, CP, bevel=0.01)
    # windows either side
    wx = sx * 1.9
    rbox("WinFrame" + str(sx), (1.0, 0.07, 1.3), PX + Vector((wx, 1.37, DECK_Z + 1.55)), M_WHITE, CP, bevel=0.01)
    plane("WinGlass" + str(sx), (0.84, 1.14), PX + Vector((wx, 1.33, DECK_Z + 1.55)), M_GLASS, CP, rot=(R_(90), 0, 0))
    rbox("WinMull" + str(sx), (0.03, 0.04, 1.14), PX + Vector((wx, 1.32, DECK_Z + 1.55)), M_WHITE, CP, bevel=0.004)
    rbox("WinMullH" + str(sx), (0.84, 0.04, 0.03), PX + Vector((wx, 1.32, DECK_Z + 1.55)), M_WHITE, CP, bevel=0.004)
    # porch posts and a rail at the edge
    cyl("Post" + str(sx), 0.075, 2.7, PX + Vector((sx * 2.5, -2.35, DECK_Z + 1.35)), M_WHITE, CP)
rbox("PorchCeiling", (6.0, 4.0, 0.06), PX + Vector((0, -0.6, DECK_Z + 2.75)), M_WHITE, CP, bevel=0.01)
plane("LawnP", (60, 40), PX + Vector((0, -20, 0)), M_GRASS, CP)
scatter(GRASS_SRC, 300, (-8, 8), (-12, -2.7), CP, seed=41, prefix="GrP")
for o in [o for o in CP.objects if o.name.startswith("GrP")]: o.location.x += 300
scatter(SHRUB_SRC, 6, (-3, 3), (-3.4, -2.8), CP, smin=0.6, smax=0.8, seed=42, prefix="ShP")
for o in [o for o in CP.objects if o.name.startswith("ShP")]: o.location.x += 300
for i in range(4):
    rbox(f"Step{i}", (1.6, 0.30, DECK_Z - i * 0.14), PX + Vector((0, -2.75 - i * 0.30, (DECK_Z - i * 0.14) / 2)), M_PLANK, CP, bevel=0.01)

# thin set pieces: flat shading (smooth shading on bevelled thin boxes gave black corners)
for o in list(CP.objects) + list(CR.objects):
    if o.type == 'MESH':
        for p in o.data.polygons: p.use_smooth = False
# grass tufts a little bigger and greener
for o in GRASS_SRC:
    for m in o.data.materials:
        if m and m.node_tree:
            P_ = next((n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)
            if P_ and "Specular IOR Level" in P_.inputs: P_.inputs["Specular IOR Level"].default_value = 0.2

# shovel as one mesh (ToddlerWell asset), standing in the spoil heap / the yard mound; nobody holds it
_sh = [c_ for c_ in bpy.data.objects["shovel_GEO"].children if c_.type == 'MESH']
_cp = []
for c_ in _sh:
    o_ = c_.copy(); o_.data = c_.data.copy(); o_.parent = None; o_.matrix_world = c_.matrix_world.copy(); CG.objects.link(o_); _cp.append(o_)
bpy.ops.object.select_all(action='DESELECT')
for o_ in _cp: o_.select_set(True)
bpy.context.view_layer.objects.active = _cp[0]; bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
bpy.ops.object.join(); SHOVEL = bpy.context.view_layer.objects.active; SHOVEL.name = "Shovel"
_pts = [v.co for v in SHOVEL.data.vertices]
_mn = Vector([min(p[i] for p in _pts) for i in range(3)]); _mx = Vector([max(p[i] for p in _pts) for i in range(3)])
_ax = max(range(3), key=lambda i: _mx[i] - _mn[i])
if _ax != 2:   # long axis -> Z, blade down
    SHOVEL.data.transform(Matrix.Rotation(R_(90), 4, 'X' if _ax == 1 else 'Y'))
_pts = [v.co for v in SHOVEL.data.vertices]
_mn = Vector([min(p[i] for p in _pts) for i in range(3)]); _mx = Vector([max(p[i] for p in _pts) for i in range(3)])
_s = 1.45 / (_mx.z - _mn.z)
SHOVEL.data.transform(Matrix.Scale(_s, 4) @ Matrix.Translation(-Vector(((_mn.x + _mx.x) / 2, (_mn.y + _mx.y) / 2, _mn.z))))
# blade at the bottom: the wider end should be low
_lo = [p for p in SHOVEL.data.vertices if p.co.z < 0.3]; _hi = [p for p in SHOVEL.data.vertices if p.co.z > 1.15]
_w = lambda vs: (max(v.co.x for v in vs) - min(v.co.x for v in vs)) if vs else 0
if _w(_hi) > _w(_lo): SHOVEL.data.transform(Matrix.Translation((0, 0, 1.45)) @ Matrix.Rotation(R_(180), 4, 'X'))
bpy.context.view_layer.update(); print("BUILD shovel dims", tuple(round(v, 2) for v in SHOVEL.dimensions))
SHOVEL.location = (1.15, 1.6, -0.12); SHOVEL.rotation_euler = (R_(-12), R_(8), R_(20))
SHOVY = dup(SHOVEL, "ShovelY", YMOUND + Vector((0.55, 0.25, -0.12)), (R_(-10), R_(14), R_(-30)), 1.0, CY)
# soft fill on the cut face (the grave cross-section) and a little sky bounce for the yard faces
area("GraveFill", (0.5, -3.5, 0.6), (0, 0.3, -0.7), 120, 3.0, CG, (1.0, 0.97, 0.92))

# even, sunny light on the dog in the porch and road sets (the coat must match the sunlit yard shots)
area("PorchKey", PX + Vector((0.6, -2.6, 2.2)), PX + Vector((0, 0.3, 0.8)), 220, 3.0, CP, (1.0, 0.97, 0.92))
area("PorchFill", PX + Vector((-1.8, -1.5, 1.2)), PX + Vector((0, 0.3, 0.8)), 90, 2.0, CP, (0.95, 0.97, 1.0))
area("RoadKey", RX + Vector((3.8, 0.0, 3.0)), RX + Vector((1.8, 4.5, 0.4)), 2200, 6.0, CR, (1.0, 0.97, 0.92))
area("YardDogFill", YX + Vector((0.4, 7.4, 1.6)), YX + Vector((2.1, 6.0, 0.4)), 260, 2.5, CY, (1.0, 0.97, 0.92))
