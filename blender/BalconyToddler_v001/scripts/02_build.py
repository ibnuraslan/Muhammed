"""BalconyToddler: set (street, apartment facade with the steel balcony cage, apartment room), cast controls, helpers.
Then exec 03_shots.py (per-shot animation at 1x, one camera per shot, hard-cut markers) and 04_finish.py (look, logo).
blender -b lib.blend --python 02_build.py -- <out.blend>"""
import bpy, sys, math, os, random, bmesh
from mathutils import Vector, Matrix, Euler, Quaternion
argv = sys.argv[sys.argv.index("--") + 1:]
OUT = argv[0]
ONLY = argv[1].split(",") if len(argv) > 1 and argv[1] else None    # optional: build only these shots (testing)
HERE = "/home/user/Muhammed/blender/BalconyToddler_v001/scripts"
BRAND = "/home/user/Muhammed/blender/assets/brand/"
P = "/home/user/Muhammed/blender/pipeline/"
exec(open(P + "anim_lib.py").read()); exec(open(P + "hand_poses.py").read())
exec(open(HERE + "/shots.py").read())
R_ = math.radians
random.seed(11)
sc = bpy.context.scene
sc.render.fps = 60; sc.render.resolution_x = 1080; sc.render.resolution_y = 1920
SH = {sid: (f0, f1) for sid, f0, f1 in layout()}
FEND = max(v[1] for v in SH.values())
sc.frame_start = 1; sc.frame_end = FEND
GZ = [0.0]
def ground_z(x, y): return GZ[0]          # overrides anim_lib's terrain (walk() and key_foot use it)

def coll(name):
    c = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if c.name not in sc.collection.children: sc.collection.children.link(c)
    return c
def move_to(o, c):
    for uc in list(o.users_collection): uc.objects.unlink(o)
    c.objects.link(o)

# ------------------------------------------------------------------ materials / shapes
MATS = {}
def mat(name, rgb, rough=0.5, metal=0.0, emit=None, ew=0.0):
    if name in MATS: return MATS[name]
    m = bpy.data.materials.new(name); m.use_nodes = True
    p = m.node_tree.nodes["Principled BSDF"]
    p.inputs["Base Color"].default_value = (*rgb, 1); p.inputs["Roughness"].default_value = rough
    p.inputs["Metallic"].default_value = metal
    if emit:
        p.inputs["Emission Color"].default_value = (*emit, 1); p.inputs["Emission Strength"].default_value = ew
    MATS[name] = m; return m

def texmat(name, tid, tint=(1, 1, 1), scale=1.0, rough=0.6, bump=0.3, sat=1.0):
    """Poly Haven texture (from the lib's TX_ images), tinted, world-box mapped, softened for the animated look"""
    if name in MATS: return MATS[name]
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree
    p = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord"); mp = nt.nodes.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (scale,) * 3
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
    tx = nt.nodes.new("ShaderNodeTexImage"); tx.image = bpy.data.images["TX_%s_diff" % tid]; tx.projection = 'BOX'; tx.projection_blend = 0.3
    nt.links.new(mp.outputs["Vector"], tx.inputs["Vector"])
    hs = nt.nodes.new("ShaderNodeHueSaturation"); hs.inputs["Saturation"].default_value = sat
    nt.links.new(tx.outputs["Color"], hs.inputs["Color"])
    mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs["Factor"].default_value = 1.0
    mx.inputs["B"].default_value = (*tint, 1)
    nt.links.new(hs.outputs["Color"], mx.inputs["A"]); nt.links.new(mx.outputs["Result"], p.inputs["Base Color"])
    p.inputs["Roughness"].default_value = rough
    nim = bpy.data.images.get("TX_%s_nor_gl" % tid)
    if nim and bump > 0:
        tn = nt.nodes.new("ShaderNodeTexImage"); tn.image = nim; tn.projection = 'BOX'; tn.projection_blend = 0.3
        nt.links.new(mp.outputs["Vector"], tn.inputs["Vector"])
        nm = nt.nodes.new("ShaderNodeNormalMap"); nm.inputs["Strength"].default_value = bump
        nt.links.new(tn.outputs["Color"], nm.inputs["Color"]); nt.links.new(nm.outputs["Normal"], p.inputs["Normal"])
    MATS[name] = m; return m

def rbox(name, size, loc, m, c, bevel=0.01, rot=(0, 0, 0), seg=2):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    o = bpy.context.active_object; o.name = name; o.scale = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel:
        b = o.modifiers.new("bev", 'BEVEL'); b.width = bevel; b.segments = seg; b.limit_method = 'NONE'
    o.data.materials.append(m); move_to(o, c); return o

def cyl(name, r, depth, loc, m, c, rot=(0, 0, 0), verts=24):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=depth, location=loc, rotation=rot)
    o = bpy.context.active_object; o.name = name; bpy.ops.object.shade_smooth()
    o.data.materials.append(m); move_to(o, c); return o

def tube(name, a, b, r, m, c, verts=20):
    a = Vector(a); b = Vector(b); d = b - a
    o = cyl(name, r, d.length, (a + b) / 2, m, c, verts=verts)
    o.rotation_mode = 'QUATERNION'; o.rotation_quaternion = d.to_track_quat('Z', 'Y'); return o

def plane(name, size, loc, m, c, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_plane_add(size=1, location=loc, rotation=rot)
    o = bpy.context.active_object; o.name = name; o.scale = (size[0], size[1], 1)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    o.data.materials.append(m); move_to(o, c); return o

def dup(src, name, loc, rot=(0, 0, 0), scale=1.0, c=None, linked=True):
    o = src.copy()
    if not linked: o.data = src.data.copy()
    o.name = name; o.rotation_mode = 'XYZ'; o.location = loc; o.rotation_euler = rot
    o.scale = (scale, scale, scale) if isinstance(scale, (int, float)) else scale
    (c or src.users_collection[0]).objects.link(o); bpy.context.view_layer.update(); return o

def area(name, loc, target, energy, size, c, color=(1, 1, 1)):
    L = bpy.data.lights.new(name, 'AREA'); L.energy = energy; L.size = size; L.color = color
    o = bpy.data.objects.new(name, L); c.objects.link(o); o.location = loc
    o.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler(); return o

def logo_decal(name, loc, rot, width, dark, c):
    img = bpy.data.images.load(BRAND + ("DaKrasFilms_logo_dark.png" if dark else "DaKrasFilms_logo_white.png"), check_existing=True)
    m = bpy.data.materials.new(name + "_mat"); m.use_nodes = True; nt = m.node_tree
    pr = nt.nodes["Principled BSDF"]; tx = nt.nodes.new("ShaderNodeTexImage"); tx.image = img
    nt.links.new(tx.outputs["Color"], pr.inputs["Base Color"]); nt.links.new(tx.outputs["Alpha"], pr.inputs["Alpha"])
    pr.inputs["Roughness"].default_value = 0.5
    return plane(name, (width, width * 414 / 967), loc, m, c, rot)

# ------------------------------------------------------------------ world: blue sky seen by camera, soft light + sun
w = bpy.data.worlds.new("Sky"); sc.world = w; w.use_nodes = True; nt = w.node_tree; nt.nodes.clear()
o_ = nt.nodes.new("ShaderNodeOutputWorld"); lp = nt.nodes.new("ShaderNodeLightPath")
tc = nt.nodes.new("ShaderNodeTexCoord"); sep = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(tc.outputs["Generated"], sep.inputs[0])
mr = nt.nodes.new("ShaderNodeMapRange"); mr.inputs["From Min"].default_value = -0.05; mr.inputs["From Max"].default_value = 0.5
nt.links.new(sep.outputs["Z"], mr.inputs["Value"])
ramp = nt.nodes.new("ShaderNodeValToRGB"); ramp.color_ramp.elements[0].color = (0.72, 0.90, 1.0, 1); ramp.color_ramp.elements[1].color = (0.12, 0.50, 0.95, 1)
nt.links.new(mr.outputs["Result"], ramp.inputs["Fac"])
bg_cam = nt.nodes.new("ShaderNodeBackground"); nt.links.new(ramp.outputs["Color"], bg_cam.inputs["Color"])
bg_lit = nt.nodes.new("ShaderNodeBackground"); bg_lit.inputs["Color"].default_value = (0.85, 0.92, 1.0, 1); bg_lit.inputs["Strength"].default_value = 1.1
mix = nt.nodes.new("ShaderNodeMixShader"); nt.links.new(lp.outputs["Is Camera Ray"], mix.inputs["Fac"])
nt.links.new(bg_lit.outputs[0], mix.inputs[1]); nt.links.new(bg_cam.outputs[0], mix.inputs[2]); nt.links.new(mix.outputs[0], o_.inputs[0])
SUN = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", "SUN")); sc.collection.objects.link(SUN)
SUN.data.energy = 3.0; SUN.data.angle = R_(6); SUN.rotation_euler = (R_(50), R_(0), R_(-30))   # from the street side, front-left

# ------------------------------------------------------------------ SET: street, building, balcony cage, apartment
CS = coll("SET")
FLOOR2 = 3.2125           # 2nd-floor level (top of the room floor / slab / floor bars)
BAR_Z = 3.20; BAR_R = 0.0125
BAR_Y = [-0.27, -0.445, -0.62, -0.78]    # floor bars along X; 0.150 m clear gap at the boy's slot
SLOT_Y = -0.5325                         # the boy's gap (between bars -0.445 and -0.62)
CX = 0.75                                # cage half width
CY = -0.85                               # cage front

plaster = texmat("Plaster", "plastered_wall", (0.90, 0.50, 0.27), 0.6, 0.6, 0.25, 0.3)
plaster2 = texmat("Plaster2", "painted_plaster_wall", (0.70, 0.78, 0.86), 0.6, 0.6, 0.2, 0.3)
plaster3 = texmat("Plaster3", "painted_plaster_wall", (0.95, 0.88, 0.70), 0.6, 0.6, 0.2, 0.3)
pave = texmat("Pave", "concrete_pavement", (0.88, 0.86, 0.82), 0.5, 0.7, 0.3, 0.6)
asph = texmat("Asphalt", "asphalt_02", (0.55, 0.56, 0.60), 0.25, 0.75, 0.2, 0.4)
lam = mat("Laminate", (0.62, 0.42, 0.26), 0.5)
wallin = mat("WallIn", (0.62, 0.70, 0.80), 0.8)
ceil = mat("Ceiling", (0.95, 0.95, 0.93), 0.9)
conc = mat("Concrete", (0.80, 0.79, 0.76), 0.8)
steel = mat("Steel", (0.50, 0.53, 0.57), 0.4, 0.25)
wood = mat("DoorWood", (0.50, 0.28, 0.14), 0.5)
frame_w = mat("FrameWhite", (0.92, 0.92, 0.90), 0.5)
glassd = mat("WinGlass", (0.18, 0.30, 0.45), 0.08, 0.3)
curt = mat("Curtain", (0.92, 0.90, 0.84), 0.9)
curt2 = mat("Curtain2", (0.55, 0.75, 0.90), 0.9)
kerb = mat("Kerb", (0.70, 0.70, 0.70), 0.7)
line = mat("RoadLine", (0.95, 0.95, 0.9), 0.6)

# street
rbox("Pavement", (60, 4.0, 0.15), (0, -2.0, -0.075), pave, CS, 0.0)
rbox("Kerb", (60, 0.2, 0.17), (0, -4.1, -0.075), kerb, CS, 0.01)
rbox("Road", (60, 8.0, 0.1), (0, -8.2, -0.20), asph, CS, 0.0)
for i in range(-10, 11):
    rbox(f"Dash{i}", (1.6, 0.12, 0.01), (i * 3.0, -8.2, -0.145), line, CS, 0.0)
rbox("Pavement2", (60, 4.0, 0.15), (0, -14.2, -0.075), pave, CS, 0.0)

# main building: facade y=0 (front face), solid box behind except the 2nd-floor room
BW = 7.0; WT = 0.25
def facade_with_holes(name, holes, z0, z1, m):
    """facade slab (y 0..WT) between z0 and z1 for x in -BW..BW with rectangular holes [(x0,x1,za,zb)]"""
    bm = bmesh.new()
    xs = sorted({-BW, BW} | {h[0] for h in holes} | {h[1] for h in holes})
    zs = sorted({z0, z1} | {h[2] for h in holes} | {h[3] for h in holes})
    for i in range(len(xs) - 1):
        for j in range(len(zs) - 1):
            cx_ = (xs[i] + xs[i + 1]) / 2; cz_ = (zs[j] + zs[j + 1]) / 2
            if any(h[0] <= cx_ <= h[1] and h[2] <= cz_ <= h[3] for h in holes): continue
            bmesh.ops.create_cube(bm, size=1.0, matrix=Matrix.Translation((cx_, WT / 2, cz_)) @
                                  Matrix.Diagonal((xs[i + 1] - xs[i], WT, zs[j + 1] - zs[j], 1)))
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); CS.objects.link(o); me.materials.append(m); return o

WINS = []   # (x, zc, w, h) decorative windows (frame + glass + curtain)
for x in (-4.6, -2.6, 2.6, 4.6):
    WINS.append((x, FLOOR2 + 1.45, 1.1, 1.4))
for x in (-4.6, -2.6, 0.0, 2.6, 4.6):
    WINS.append((x, FLOOR2 + 3.2 + 1.45, 1.1, 1.4))
    WINS.append((x, FLOOR2 + 6.4 + 1.45, 1.1, 1.4))
for x in (-4.6, -2.0):
    WINS.append((x, 1.55, 1.2, 1.5))
DOOR_X0, DOOR_X1, DOOR_Z1 = -0.5, 0.5, FLOOR2 + 2.15
FAC = facade_with_holes("Facade", [(DOOR_X0, DOOR_X1, FLOOR2, DOOR_Z1)], 0.0, 12.6, plaster)
# window insets: frame + glass + curtains just in front of the facade (no holes needed)
for i, (x, zc, ww, hh) in enumerate(WINS):
    rbox(f"WinFrame{i}", (ww + 0.12, 0.06, hh + 0.12), (x, -0.02, zc), frame_w, CS, 0.01)
    rbox(f"WinGlass{i}", (ww, 0.02, hh), (x, -0.05, zc), glassd, CS, 0.0)
    rbox(f"WinMull{i}", (0.05, 0.03, hh), (x, -0.065, zc), frame_w, CS, 0.0)
    cm = curt if i % 2 else curt2
    rbox(f"WinCurtL{i}", (ww * 0.22, 0.01, hh * 0.95), (x - ww * 0.36, -0.04, zc), cm, CS, 0.0)
    rbox(f"WinCurtR{i}", (ww * 0.22, 0.01, hh * 0.95), (x + ww * 0.36, -0.04, zc), cm, CS, 0.0)
    rbox(f"WinSill{i}", (ww + 0.25, 0.14, 0.05), (x, -0.07, zc - hh / 2 - 0.08), conc, CS, 0.01)
# ground-floor shop at x 1.2..4.2: door + window + sign board (logo goes on it)
rbox("ShopDoor", (1.0, 0.06, 2.2), (1.8, -0.03, 1.1), wood, CS, 0.01)
rbox("ShopDoorFrame", (1.15, 0.05, 2.3), (1.8, -0.01, 1.15), frame_w, CS, 0.01)
rbox("ShopWin", (1.6, 0.03, 1.5), (3.4, -0.04, 1.35), glassd, CS, 0.0)
rbox("ShopWinFrame", (1.72, 0.05, 1.62), (3.4, -0.015, 1.35), frame_w, CS, 0.01)
SIGN = rbox("ShopSign", (2.6, 0.08, 0.62), (2.6, -0.06, 2.65), mat("SignGreen", (0.20, 0.50, 0.40), 0.6), CS, 0.02)
rbox("Plinth", (2 * BW, 0.06, 0.35), (0, -0.03, 0.175), conc, CS, 0.0)
# floor-band ledges
for z in (FLOOR2 - 0.12, FLOOR2 + 3.2 - 0.12):
    rbox(f"Ledge{z:.1f}", (2 * BW, 0.10, 0.12), (0, -0.05, z), conc, CS, 0.01)
# building body (behind the facade) and the 2nd-floor room cut out of it
RX0, RX1, RY1 = -2.6, 2.6, 4.6        # room x range, room back wall y
RZ1 = FLOOR2 + 2.75
rbox("BodyLow", (2 * BW, 10, FLOOR2), (0, WT + 5, FLOOR2 / 2), conc, CS, 0.0)
rbox("BodyHigh", (2 * BW, 10, 12.6 - RZ1 - 0.15), (0, WT + 5, (RZ1 + 0.15 + 12.6) / 2), conc, CS, 0.0)
rbox("BodyL", (BW + RX0, 10, RZ1 + 0.15 - FLOOR2), ((-BW + RX0) / 2, WT + 5, (FLOOR2 + RZ1 + 0.15) / 2), conc, CS, 0.0)
rbox("BodyR", (BW - RX1, 10, RZ1 + 0.15 - FLOOR2), ((BW + RX1) / 2, WT + 5, (FLOOR2 + RZ1 + 0.15) / 2), conc, CS, 0.0)
# the block behind the room starts behind the hallway (the hallway must be empty space: grandma walks through it)
rbox("BodyBack", (RX1 - RX0, 10 - RY1 - 2.3, RZ1 + 0.15 - FLOOR2), (0, WT + RY1 + 2.3 + (10 - RY1 - 2.3) / 2, (FLOOR2 + RZ1 + 0.15) / 2), conc, CS, 0.0)
# room interior surfaces
rbox("RoomFloor", (RX1 - RX0, RY1, 0.02), (0, WT + RY1 / 2, FLOOR2 - 0.008), lam, CS, 0.0)
rbox("RoomCeil", (RX1 - RX0, RY1, 0.02), (0, WT + RY1 / 2, RZ1 + 0.01), ceil, CS, 0.0)
rbox("RoomWallL", (0.02, RY1, RZ1 - FLOOR2), (RX0 + 0.01, WT + RY1 / 2, (FLOOR2 + RZ1) / 2), wallin, CS, 0.0)
rbox("RoomWallR", (0.02, RY1, RZ1 - FLOOR2), (RX1 - 0.01, WT + RY1 / 2, (FLOOR2 + RZ1) / 2), wallin, CS, 0.0)
# back wall with the apartment door opening (x -1.6..-0.7) and a hallway behind
AD_X0, AD_X1 = -1.55, -0.65
bw_m = wallin
rbox("RoomBackA", (AD_X0 - RX0, 0.02, RZ1 - FLOOR2), ((RX0 + AD_X0) / 2, WT + RY1 - 0.01, (FLOOR2 + RZ1) / 2), bw_m, CS, 0.0)
rbox("RoomBackB", (RX1 - AD_X1, 0.02, RZ1 - FLOOR2), ((RX1 + AD_X1) / 2, WT + RY1 - 0.01, (FLOOR2 + RZ1) / 2), bw_m, CS, 0.0)
rbox("RoomBackTop", (AD_X1 - AD_X0, 0.02, RZ1 - FLOOR2 - 2.1), ((AD_X0 + AD_X1) / 2, WT + RY1 - 0.01, (FLOOR2 + 2.1 + RZ1) / 2), bw_m, CS, 0.0)
for nm, x in (("ADFrameL", AD_X0 - 0.04), ("ADFrameR", AD_X1 + 0.04)):
    rbox(nm, (0.08, 0.06, 2.14), (x, WT + RY1 - 0.03, FLOOR2 + 1.07), wood, CS, 0.01)
rbox("ADFrameT", (AD_X1 - AD_X0 + 0.16, 0.06, 0.08), ((AD_X0 + AD_X1) / 2, WT + RY1 - 0.03, FLOOR2 + 2.14), wood, CS, 0.01)
# hallway (2 m deep) behind the door
HY = WT + RY1
rbox("HallFloor", (3.0, 2.3, 0.02), (AD_X0 + 0.45, HY + 1.1, FLOOR2 - 0.008), lam, CS, 0.0)
rbox("HallBack", (3.0, 0.02, 2.75), (AD_X0 + 0.45, HY + 2.2, FLOOR2 + 1.37), plaster3, CS, 0.0)
rbox("HallL", (0.02, 2.2, 2.75), (AD_X0 - 1.05, HY + 1.1, FLOOR2 + 1.37), plaster3, CS, 0.0)
rbox("HallR", (0.02, 2.2, 2.75), (AD_X0 + 1.95, HY + 1.1, FLOOR2 + 1.37), plaster3, CS, 0.0)
rbox("HallCeil", (3.0, 2.2, 0.02), (AD_X0 + 0.45, HY + 1.1, FLOOR2 + 2.75), ceil, CS, 0.0)
# apartment door leaf (hinged at x=AD_X0 on the room side, opens into the room); keyed in the shots
bpy.ops.object.empty_add(location=(AD_X0 + 0.02, HY - 0.05, FLOOR2)); DHINGE = bpy.context.active_object; DHINGE.name = "DoorHinge"; move_to(DHINGE, CS)
DLEAF = rbox("DoorLeaf", (AD_X1 - AD_X0 - 0.04, 0.045, 2.06), (AD_X0 + 0.02 + (AD_X1 - AD_X0 - 0.04) / 2, HY - 0.05, FLOOR2 + 1.04), wood, CS, 0.008)
DLEAF.parent = DHINGE; DLEAF.matrix_parent_inverse = DHINGE.matrix_world.inverted()
dk = cyl("DoorKnob", 0.025, 0.07, (AD_X1 - 0.12, HY - 0.10, FLOOR2 + 1.0), steel, CS, rot=(R_(90), 0, 0))
dk.parent = DHINGE; dk.matrix_parent_inverse = DHINGE.matrix_world.inverted()
# balcony door opening: reveal (jambs) + open glass door leaf folded back against the inside wall
rbox("BDJambL", (0.06, WT, 2.15), (DOOR_X0 - 0.03, WT / 2, FLOOR2 + 1.075), frame_w, CS, 0.005)
rbox("BDJambR", (0.06, WT, 2.15), (DOOR_X1 + 0.03, WT / 2, FLOOR2 + 1.075), frame_w, CS, 0.005)
rbox("BDHead", (1.12, WT, 0.06), (0, WT / 2, DOOR_Z1 + 0.03), frame_w, CS, 0.005)
rbox("BDLeafFrame", (0.05, 0.98, 2.1), (DOOR_X1 + 0.06, WT + 0.52, FLOOR2 + 1.05), frame_w, CS, 0.005)
# room furniture: sofa-like bench, plant, a framed picture (simple picture, no text)
sofa = mat("Sofa", (0.25, 0.45, 0.62), 0.8)
rbox("SofaSeat", (0.9, 1.9, 0.42), (RX1 - 0.5, WT + 2.6, FLOOR2 + 0.21), sofa, CS, 0.06)
rbox("SofaBack", (0.22, 1.9, 0.85), (RX1 - 0.13, WT + 2.6, FLOOR2 + 0.42), sofa, CS, 0.06)
rbox("SofaArmA", (0.9, 0.2, 0.6), (RX1 - 0.5, WT + 1.55, FLOOR2 + 0.3), sofa, CS, 0.06)
rbox("SofaArmB", (0.9, 0.2, 0.6), (RX1 - 0.5, WT + 3.65, FLOOR2 + 0.3), sofa, CS, 0.06)
rbox("Rug", (1.6, 2.2, 0.01), (0.2, WT + 2.4, FLOOR2 + 0.005), mat("Rug", (0.85, 0.55, 0.35), 0.95), CS, 0.0)
pic = mat("Picture", (0.45, 0.70, 0.55), 0.6)
rbox("PicFrame", (0.04, 0.9, 0.65), (RX0 + 0.04, WT + 2.4, FLOOR2 + 1.6), wood, CS, 0.01)
rbox("PicImg", (0.01, 0.8, 0.55), (RX0 + 0.065, WT + 2.4, FLOOR2 + 1.6), pic, CS, 0.0)
lamp_m = mat("CeilLamp", (1, 1, 1), 0.3, emit=(1, 0.95, 0.85), ew=4.0)
cyl("CeilLampShade", 0.22, 0.08, (0, WT + 2.3, RZ1 - 0.05), lamp_m, CS)

# balcony: concrete slab (y -0.2..0), steel cage with floor bars and railings
rbox("BalconySlab", (2 * CX, 0.2, 0.18), (0, -0.1, FLOOR2 - 0.09), conc, CS, 0.01)
BARS = []
for i, y in enumerate(BAR_Y):
    BARS.append(tube(f"FloorBar{i}", (-CX, y, BAR_Z), (CX, y, BAR_Z), BAR_R, steel, CS))
for sx in (-1, 1):
    tube(f"CageSideBeam{sx}", (sx * CX, -0.2, BAR_Z), (sx * CX, CY, BAR_Z), 0.016, steel, CS)
    tube(f"CageStrut{sx}", (sx * CX, 0.0, BAR_Z - 0.75), (sx * CX, CY + 0.02, BAR_Z - 0.03), 0.016, steel, CS)
tube("CageFrontBeam", (-CX, CY, BAR_Z), (CX, CY, BAR_Z), 0.016, steel, CS)
RAIL_TOP = BAR_Z + 1.10
for sx in (-1, 1):
    for y in (CY, -0.02):
        tube(f"CagePost{sx}_{y}", (sx * CX, y, BAR_Z), (sx * CX, y, RAIL_TOP), 0.018, steel, CS)
for k, dz in enumerate((0.28, 0.55, 1.10)):
    z = BAR_Z + dz
    tube(f"RailFront{k}", (-CX, CY, z), (CX, CY, z), 0.013 if k < 2 else 0.02, steel, CS)
    for sx in (-1, 1):
        tube(f"RailSide{k}{sx}", (sx * CX, CY, z), (sx * CX, -0.02, z), 0.013 if k < 2 else 0.02, steel, CS)
# Poly Haven props (library copies parked far below)
PH = {o.name: o for o in bpy.data.collections["PROPS"].objects}
PH0 = {n: o.location.copy() for n, o in PH.items()}
for n in list(PH):
    PH[n].location = (0, 0, -50)
for i, (x, y, s) in enumerate(((-1.6, -0.45, 1.0), (1.5, -0.4, 1.0), (5.6, -0.5, 1.2))):
    for part in ("pot", "leaves", "dirt"):
        n = "PH_potted_plant_02_" + part
        dup(PH[n], f"Plant{i}_{part}", Vector((x, y, 0.0)) + PH0[n] * s, (0, 0, 0), s, CS)
for i, (x, z) in enumerate(((3.6, FLOOR2 + 0.35), (-3.4, FLOOR2 + 3.55))):
    dup(PH["PH_exterior_aircon_unit"], f"AC{i}", (x, -0.20, z), (0, 0, 0), 1.0, CS)
dup(PH["PH_street_lamp_01"], "StreetLamp", (-3.6, -3.7, 0.0), (0, 0, R_(180)), 1.15, CS)
for n in ("PH_fire_hydrant", "PH_fire_hydrant_cap_01", "PH_fire_hydrant_cap_02", "PH_fire_hydrant_cap_03", "PH_fire_hydrant_chain"):
    dup(PH[n], "Hydrant_" + n[3:], Vector((5.0, -3.6, 0.0)) + (PH0[n] - PH0["PH_fire_hydrant"]) * 1.2, (0, 0, 0), 1.2, CS)

# chairs: Poly Haven WoodenChair_01 is modelled at ~2.2x; scale it to a 1.0 m chair. Front = -Y, backrest at +Y.
CHAIR_SRC = PH["PH_painted_wooden_chair_01"]
CH_S = 1.0
def chair(name, loc, yaw, s=CH_S):
    return dup(CHAIR_SRC, name, loc, (0, 0, yaw), s, CS)
# seat height of the scaled chair (ray down at the seat centre)
_tmp = chair("ChairProbe", (0, 0, 0), 0.0); bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get()
def ray_down(o, x, y, z0=3.0):
    inv = o.matrix_world.inverted()
    ok, loc, n, i = o.ray_cast(inv @ Vector((x, y, z0)), inv.to_3x3() @ Vector((0, 0, -1)))
    return (o.matrix_world @ loc).z if ok else None
_pts = [_tmp.matrix_world @ v.co for v in _tmp.data.vertices]
SEAT_H = max(ray_down(_tmp, x_, y_) or 0.0 for x_ in (-0.08, 0.0, 0.08) for y_ in (-0.08, 0.02, 0.10))
CH_TOP = max(p.z for p in _pts); CH_YMIN = min(p.y for p in _pts); CH_YMAX = max(p.y for p in _pts)
BACK_FRONT = min(p.y for p in _pts if p.z > SEAT_H + 0.06)
SEAT_FRONT = min(p.y for p in _pts if abs(p.z - SEAT_H) < 0.03)
SEAT_XMIN = min(p.x for p in _pts if abs(p.z - SEAT_H) < 0.03)
print("BUILD chair seat", round(SEAT_H, 3), "top", round(CH_TOP, 3), "y", round(CH_YMIN, 3), round(CH_YMAX, 3), "back front", round(BACK_FRONT, 3), "seat front", round(SEAT_FRONT, 3))
bpy.data.objects.remove(_tmp, do_unlink=True)

# ------------------------------------------------------------------ opposite side of the street (seen from the balcony)
opp = [texmat("OppA", "painted_plaster_wall", (0.95, 0.85, 0.65), 0.5, 0.6, 0.2, 0.3),
       texmat("OppB", "painted_plaster_wall", (0.70, 0.85, 0.95), 0.5, 0.6, 0.2, 0.3),
       texmat("OppC", "painted_plaster_wall", (0.95, 0.75, 0.75), 0.5, 0.6, 0.2, 0.3)]
for i, x in enumerate((-12, -4, 4, 12)):
    hgt = 9 + 3 * (i % 2)
    rbox(f"OppBldg{i}", (7.6, 6, hgt), (x, -19.5, hgt / 2), opp[i % 3], CS, 0.02)
    for fx in (-2.2, 0, 2.2):
        for fz in (1.6, 4.6, 7.6):
            if fz < hgt - 1:
                rbox(f"OppWin{i}_{fx}_{fz}", (1.0, 0.06, 1.3), (x + fx, -16.47, fz), glassd, CS, 0.0)
# cafe on the opposite side: white sign board (our logo goes on it in 04_finish), awning, window
OSIGN = rbox("CafeSign", (2.6, 0.08, 0.85), (-2.4, -16.42, 3.0), frame_w, CS, 0.02)
rbox("CafeWin", (2.4, 0.05, 1.5), (-2.4, -16.45, 1.3), glassd, CS, 0.0)
rbox("CafeAwning", (2.8, 0.7, 0.06), (-2.4, -16.1, 2.45), mat("Awning", (0.85, 0.25, 0.20), 0.7), CS, 0.01, rot=(R_(-12), 0, 0))
# side buildings next to the main one
rbox("SideBldgL", (6, 10, 10), (-BW - 3.05, 5, 5), opp[1], CS, 0.02)
rbox("SideBldgR", (6, 10, 14), (BW + 3.05, 5, 7), opp[0], CS, 0.02)
for x in (-BW - 4.5, -BW - 1.6):
    for z in (1.6, 4.6, 7.6):
        rbox(f"SideWinL{x}_{z}", (1.0, 0.06, 1.3), (x, -0.03, z), glassd, CS, 0.0)
for x in (BW + 1.6, BW + 4.5):
    for z in (1.6, 4.6, 7.6, 10.6):
        rbox(f"SideWinR{x}_{z}", (1.0, 0.06, 1.3), (x, -0.03, z), glassd, CS, 0.0)

# interior lights
area("RoomLight", (0, WT + 2.3, RZ1 - 0.1), (0, WT + 2.3, FLOOR2), 220, 2.0, CS, (1.0, 0.96, 0.9))
area("HallLight", (AD_X0 + 0.45, HY + 1.1, FLOOR2 + 2.65), (AD_X0 + 0.45, HY + 1.1, FLOOR2), 120, 1.2, CS, (1.0, 0.95, 0.88))
area("BalconyFill", (0.0, -3.0, 4.6), (0, -0.4, 3.5), 220, 2.0, CS, (1.0, 0.98, 0.95))
area("StreetFill", (0.0, -6.0, 3.0), (0, -1.0, 1.0), 300, 6.0, CS, (0.95, 0.97, 1.0))
# face fills (not seen by the camera): grandma in the room and at the balcony
for nm, loc, tgt, e in (("RoomFaceFill", (0.4, 0.9, FLOOR2 + 1.7), (-0.6, 3.5, FLOOR2 + 1.4), 90),
                        ("BalconyFaceFill", (0.5, -1.4, FLOOR2 + 1.15), (0.0, 0.1, FLOOR2 + 0.95), 70)):
    _l = area(nm, loc, tgt, e, 0.8, CS, (1.0, 0.97, 0.94)); _l.visible_camera = False

# ------------------------------------------------------------------ cast: controls, limits, subsurf for close-ups
CAST = {}
for n in ("Toddler", "Man", "Grandma", "OldMan", "Woman", "YoungMan", "Lady"):
    rig = bpy.data.objects[n]
    for ch in rig.children:
        if ch.type == 'MESH' and not any(m.type == 'SUBSURF' for m in ch.modifiers):
            ss = ch.modifiers.new("subsurf", 'SUBSURF'); ss.levels = 0; ss.render_levels = 1
        for m in ch.modifiers:
            if m.type == 'SUBSURF': m.levels = 0
    R = make_human_ctrl(rig); add_hand_limits(rig)
    for s in "LR":
        for bn in ("lowerarm01." + s, "lowerarm02." + s):
            pb = rig.pose.bones.get(bn)
            if pb:
                for ax in "xyz":
                    if getattr(pb, "use_ik_limit_" + ax):
                        setattr(pb, "ik_min_" + ax, min(getattr(pb, "ik_min_" + ax), R_(-60)))
                for c in pb.constraints:
                    if c.type == 'LIMIT_ROTATION':
                        c.min_x = min(c.min_x, R_(-60)); c.min_z = min(c.min_z, R_(-60))
    H = Human(R)
    CAST[n] = (rig, R, H)
    print("BUILD cast", n, "root", tuple(round(v, 3) for v in H.root_head))
TOD = bpy.data.objects["Toddler"]
TOD.pose.bones["head"].scale = (1.05, 1.05, 1.05)      # toddler head a touch larger (reads younger, and the head is what sticks)

exec(open(HERE + "/03_shots.py").read())
exec(open(HERE + "/04_finish.py").read())
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("BUILD_OK", OUT, sc.frame_start, sc.frame_end)
