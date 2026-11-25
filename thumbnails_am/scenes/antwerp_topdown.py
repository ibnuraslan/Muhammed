"""Antwerp thumbnail, dark premium style (matches the user's Mary Celeste thumb): a high 3/4 view (~43 deg down) into
the Diamond Centre vault. Steel safe-deposit boxes line the walls and a freestanding bank; almost every one is forced
and empty (doors bent open, dark holes); papers, empty diamond packets and a few stray gems on the floor. ONE box,
centre-left on the freestanding bank, is untouched, closed and locked: painted Seldom yellow #E3FF00, glowing under a
soft top spotlight with a faint volumetric cone and dust. Everything else is monochrome dark blue-grey (never black).
The big round vault door hangs open at the left edge. Clean, darker floor on the right for the user's arrow/text.
No people, no text.
    PREVIEW=0.4 SPP=32 blender -b --python antwerp_topdown.py"""
import os, sys, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tcommon as T
C = T.use("antwerp")
import bpy, bmesh
import numpy as np
from mathutils import Vector, Matrix
import sets as S, props as PR, ship as SH
E = os.environ.get
sc = T.res_setup(int(E("SPP", "256")), noise=0.012)
sc.cycles.max_bounces = 6
rng = random.Random(int(E("SEED", "11")))
col = sc.collection

# ---------------------------------------------------------------- palette: blue-grey monochrome + the brand yellow
def s2l(c):
    c = c / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
BRAND = tuple(s2l(c) for c in (227, 255, 0))


def mono(name, v, rough=0.45, metal=0.0, var=0.12, scale=4.0):
    """Blue-grey at value v, with a little noise so surfaces are not flat."""
    m = bpy.data.materials.new(name); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links
    p = N["Principled BSDF"]; p.inputs['Roughness'].default_value = rough; p.inputs['Metallic'].default_value = metal
    nz = N.new("ShaderNodeTexNoise"); nz.inputs['Scale'].default_value = scale; nz.inputs['Detail'].default_value = 8
    mr = N.new("ShaderNodeMapRange"); mr.inputs['To Min'].default_value = 1 - var; mr.inputs['To Max'].default_value = 1 + var * 0.5
    L.new(nz.outputs['Fac'], mr.inputs['Value'])
    mx = N.new("ShaderNodeMix"); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs['Factor'].default_value = 1.0
    mx.inputs[6].default_value = (v * 0.78, v * 0.9, v * 1.12, 1)
    cm = N.new("ShaderNodeCombineColor")
    for k in range(3):
        L.new(mr.outputs[0], cm.inputs[k])
    L.new(cm.outputs[0], mx.inputs[7]); L.new(mx.outputs[2], p.inputs['Base Color'])
    return m


def yellow(name, mult=1.0, rough=0.42):
    """Brand yellow paint with form: AO pushes the cavities to olive, a light coat sheen."""
    m = bpy.data.materials.new(name); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links
    p = N["Principled BSDF"]; p.inputs['Roughness'].default_value = rough
    p.inputs['Coat Weight'].default_value = 0.3; p.inputs['Coat Roughness'].default_value = 0.2
    c = tuple(x * mult for x in BRAND)
    ao = N.new("ShaderNodeAmbientOcclusion"); ao.inputs['Distance'].default_value = 0.08; ao.samples = 8
    mx = N.new("ShaderNodeMix"); mx.data_type = 'RGBA'; mx.inputs[6].default_value = (c[0] * 0.2, c[1] * 0.22, 0.005, 1)
    mx.inputs[7].default_value = (*c, 1); L.new(ao.outputs['AO'], mx.inputs['Factor']); L.new(mx.outputs[2], p.inputs['Base Color'])
    return m


box_m = mono("box_steel", 0.42, rough=0.3, metal=0.55, var=0.08)
plate_m = mono("box_plates", 0.3, rough=0.35, metal=0.6)
black = mono("keyhole", 0.02, rough=0.5)
cav_m = mono("cavity", 0.012, rough=0.8)
frame_m = mono("frames", 0.2, rough=0.45, metal=0.3)
wall_m = mono("walls", 0.22, rough=0.8, var=0.18, scale=2.0)
floor_m = mono("floor", 0.16, rough=0.55, var=0.2, scale=1.2)
floor_m.node_tree.nodes["Principled BSDF"].inputs['Coat Weight'].default_value = 0.25
paper_m = mono("paper", 0.38, rough=0.85, var=0.05)
door_m = mono("vault_door", 0.36, rough=0.28, metal=0.7, var=0.06)
HERO = yellow("hero_yellow"); HERO_D = yellow("hero_yellow_trim", mult=0.75, rough=0.35)

# ---------------------------------------------------------------- the room
RX, RY, RZ = 3.2, 6.0, 2.6
S.box("floor", (1, RY / 2 - 1, -0.05), (2 * RX + 6, RY + 6, 0.1), floor_m)
S.box("wall_back", (0, RY + 0.55, RZ / 2), (2 * RX + 1.2, 0.1, RZ), wall_m)
LWX = float(E("LWX", "-2.75"))
S.box("wall_side", (LWX - 0.55, RY / 2 - 1, RZ / 2), (0.1, RY + 5, RZ), wall_m)
S.box("wall_side", (RX + float(E("RWX", "1.6")) + 0.55, RY / 2 - 1, RZ / 2), (0.1, RY + 5, RZ), wall_m)

CW, RH, Z0 = 0.3, 0.36, 0.28
door_t = S._door_mesh(CW, RH, "boxdoor", (box_m, plate_m, black))
cav_t = S._cavity_mesh(CW, RH, 0.45, "cavity", cav_m)
for o in (door_t, cav_t):
    for c_ in list(o.users_collection):
        c_.objects.unlink(o)
hero_door = door_t.copy(); hero_door.data = door_t.data.copy()
hero_door.data.materials[0] = HERO; hero_door.data.materials[1] = HERO_D; hero_door.data.materials[2] = black
HERO_AT = None


def bank(org, yaw, ncol, nrow, hero=None, frame_depth=0.03, cw=None, rh=None):
    """A bank of boxes: org = lower-left front corner, yaw: facing direction (0 = faces -y). Every box forced except
    `hero` (col, row), which stays shut."""
    global HERO_AT, CW, RH, door_t, cav_t, hero_door
    sv = (CW, RH, door_t, cav_t, hero_door)
    if cw:
        CW, RH = cw, rh
        door_t = S._door_mesh(CW, RH, "bigdoor", (box_m, plate_m, black)); cav_t = S._cavity_mesh(CW, RH, 0.5, "bigcav", cav_m)
        for o in (door_t, cav_t):
            for c_ in list(o.users_collection):
                c_.objects.unlink(o)
        hero_door = door_t.copy(); hero_door.data = door_t.data.copy()
        hero_door.data.materials[0] = HERO; hero_door.data.materials[1] = HERO_D; hero_door.data.materials[2] = black
    R = Matrix.Rotation(yaw, 4, 'Z')
    for c in range(ncol):
        for r in range(nrow):
            o_ = Vector(org) + R @ Vector((c * CW, 0, Z0 + (r + 0.5) * RH))
            M = Matrix.Translation(o_) @ R
            if hero == (c, r):
                d = hero_door.copy(); col.objects.link(d); d.matrix_world = M
                HERO_AT = M @ Vector((CW / 2, -0.02, 0))
                continue
            cv = cav_t.copy(); col.objects.link(cv); cv.matrix_world = M
            if hero and (c, r) in ((hero[0] + 1, hero[1]), (hero[0] + 1, hero[1] - 1), (hero[0] + 1, hero[1] + 1)):
                # torn off and dropped on the floor in front
                d = door_t.copy(); col.objects.link(d)
                d.matrix_world = Matrix.Translation(Vector(org) + R @ Vector((c * CW + rng.uniform(-0.1, 0.2), -0.5 - rng.uniform(0, 0.3), 0.01))) @ R @ \
                    Matrix.Rotation(math.radians(90), 4, 'X') @ Matrix.Rotation(math.radians(rng.uniform(-30, 30)), 4, 'Y')
                continue
            d = door_t.copy(); col.objects.link(d)
            ang = rng.uniform(70, 160)
            d.matrix_world = M @ Matrix.Rotation(math.radians(-ang), 4, 'Z') @ Matrix.Rotation(math.radians(rng.uniform(-6, 6)), 4, 'X')
    # frame grid and plinth
    W, Hh = ncol * CW, nrow * RH
    for c in range(ncol + 1):
        p0 = Vector(org) + R @ Vector((c * CW, -0.007, Z0 + Hh / 2))
        b = S.box("stile", p0, (0.014, 0.03, Hh + 0.02), frame_m); b.rotation_euler.z = yaw
    for r in range(nrow + 1):
        p0 = Vector(org) + R @ Vector((W / 2, -0.007, Z0 + r * RH))
        b = S.box("rail", p0, (W + 0.014, 0.03, 0.014), frame_m); b.rotation_euler.z = yaw
    W, Hh = ncol * CW, nrow * RH
    out = (W, Hh)
    pl = S.box("plinth", Vector(org) + R @ Vector((W / 2, 0.1, Z0 / 2)), (W + 0.04, 0.2, Z0), frame_m); pl.rotation_euler.z = yaw
    cap = S.box("cap", Vector(org) + R @ Vector((W / 2, 0.2, Z0 + Hh + 0.05)), (W + 0.06, 0.5, 0.1), frame_m); cap.rotation_euler.z = yaw
    CW, RH, door_t, cav_t, hero_door = sv
    return out


# walls: back wall bank faces -y; side walls face inward
NCB = int((2 * RX - 0.4) / CW); NRB = int((RZ - Z0 - 0.25) / RH)
bank((-NCB * CW / 2, RY, 0), 0.0, NCB, NRB)
NCS = int((RY - 0.6) / CW)
bank((RX + float(E("RWX", "1.6")), RY - 0.3, 0), -math.pi / 2, NCS, NRB)     # right wall (further off), faces -x
bank((LWX, 2.4, 0), math.pi / 2, int((RY - 2.7) / CW), NRB)           # left wall behind the vault door, faces +x
# the freestanding bank (two-sided), front face toward the camera; the hero sits centre-left on it
FB_X0, FB_Y, FB_N, FB_R = float(E("FBX", "-2.3")), float(E("FBY", "2.4")), 9, 3
BCW, BRH = 0.5, 0.48
HERO_C = (int(E("HERO_COL", "2")), int(E("HERO_ROW", "1")))
bank((FB_X0, FB_Y, 0), 0.0, FB_N, FB_R, hero=HERO_C, cw=BCW, rh=BRH)
bank((FB_X0 + FB_N * BCW, FB_Y + 1.05, 0), math.pi, FB_N, FB_R, cw=BCW, rh=BRH)
S.box("fb_core", (FB_X0 + FB_N * BCW / 2, FB_Y + 0.525, (Z0 + FB_R * BRH) / 2), (FB_N * BCW, 0.03, Z0 + FB_R * BRH), cav_m)

# ---------------------------------------------------------------- the round vault door, hanging open at the left edge
DX, DYW = -RX - 0.55, 0.0
Rd = 1.05
leaf = bpy.data.objects.new("vault_door", None); col.objects.link(leaf)
def part(o):
    o.parent = leaf; return o
part(SH.cyl("door_body", (-Rd, 0.0, 0), (-Rd, -0.5, 0), Rd, mat=door_m, verts=96))
part(SH.cyl("door_step", (-Rd, -0.5, 0), (-Rd, -0.58, 0), Rd + 0.08, mat=door_m, verts=96))
for rr in (Rd * 0.75, Rd * 0.45):
    bpy.ops.mesh.primitive_torus_add(major_radius=rr, minor_radius=0.025, major_segments=80, minor_segments=10,
                                     location=(-Rd, -0.585, 0), rotation=(math.pi / 2, 0, 0))
    t_ = bpy.context.active_object; t_.data.materials.append(plate_m); part(t_)
for k in range(14):
    a = 2 * math.pi * k / 14
    part(SH.cyl("bolt", (-Rd + math.cos(a) * (Rd - 0.02), -0.25, math.sin(a) * (Rd - 0.02)),
                (-Rd + math.cos(a) * (Rd + 0.14), -0.25, math.sin(a) * (Rd + 0.14)), 0.045, mat=plate_m, verts=16))
leaf.location = (float(E("DOOR_X", "-1.9")), float(E("DOOR_Y", "1.7")), Rd + 0.05)
leaf.rotation_euler.z = math.radians(float(E("DOOR_ANG", "65")))

bpy.context.view_layer.update()
if E('DBG_DOOR'):
    import ph
    ms_ = [o for o in leaf.children_recursive if o.type == 'MESH']
    print('DOORB', ph.bounds(ms_), [o.name for o in ms_][:3], leaf.matrix_world.translation)
    sys.exit(0)
# ---------------------------------------------------------------- floor: papers, empty diamond packets, a few gems
for i in range(int(E("NPAPER", "140"))):
    x = rng.uniform(-RX + 0.3, RX - 0.3); y = rng.uniform(0.0, RY - 0.4)
    if x > 0.6 and y < FB_Y and rng.random() < 0.8:      # keep the right-hand floor clean for the title
        continue
    if abs(y - FB_Y - 0.47) < 0.6 and FB_X0 - 0.1 < x < FB_X0 + FB_N * BCW + 0.1:
        continue
    w_, h_ = (rng.uniform(0.12, 0.2), rng.uniform(0.09, 0.28)) if i % 3 else (0.11, 0.075)
    S.box("paper", (x, y, 0.002 + 0.0006 * (i % 5)), (w_, h_, 0.0008), paper_m, rot=(0, 0, rng.uniform(0, 6.28)))
fire = PR.fire_glass("gem_fire")
for i in range(int(E("NGEM", "9"))):
    d = rng.uniform(0.012, 0.022)
    g = PR.brilliant(f"gem{i}", d, fire)
    g.location = (rng.uniform(-1.8, 0.8), rng.uniform(0.6, 2.0), d * 0.43)
    g.rotation_euler = (rng.uniform(-0.2, 0.2), rng.uniform(-0.2, 0.2), rng.uniform(0, 6.28))

# ---------------------------------------------------------------- light: dim blue-grey ambience, a soft top spot on the hero
w = bpy.data.worlds.new("vault"); sc.world = w; w.use_nodes = True
bg = w.node_tree.nodes["Background"]; bg.inputs['Color'].default_value = (0.09, 0.12, 0.16, 1)
bg.inputs['Strength'].default_value = float(E("WORLD", "1.2"))
T.area("ceiling_fill", (0, RY / 2 - 0.5, RZ + 2.5), (0, RY / 2 - 0.5, 0), 6.0, float(E("FILL_E", "300")), color=(0.7, 0.8, 1.0), size_y=8)
HP = HERO_AT if HERO_AT is not None else Vector((0, FB_Y, 1))
KEYP = HP + Vector((float(E("KEYX", "0.6")), float(E("KEYY", "-2.6")), float(E("KEYH", "3.4"))))
sp = bpy.data.lights.new("key", 'SPOT'); sp.energy = float(E("KEY_E", "1400")); sp.spot_size = math.radians(float(E("KEY_ANG", "17")))
sp.spot_blend = 0.6; sp.shadow_soft_size = 0.25; sp.color = (1.0, 0.97, 0.88)
key = bpy.data.objects.new("key", sp); col.objects.link(key); key.location = KEYP
key.rotation_euler = (HP - KEYP).to_track_quat('-Z', 'Y').to_euler()
# beam haze cone + dust, lit only by the key
L_ = (HP - KEYP).length * 1.15
bpy.ops.mesh.primitive_cone_add(vertices=64, radius1=0.05, radius2=math.tan(math.radians(float(E("KEY_ANG", "17")) / 2)) * L_ * 1.2,
                                depth=L_, location=KEYP + (HP - KEYP).normalized() * L_ / 2)
cone = bpy.context.active_object; cone.name = "beam_haze"
cone.rotation_euler = (HP - KEYP).to_track_quat('-Z', 'Y').to_euler()
bmat = bpy.data.materials.new("beam_haze"); bmat.use_nodes = True; BN = bmat.node_tree.nodes; BN.remove(BN["Principled BSDF"])
bv = BN.new("ShaderNodeVolumePrincipled"); bv.inputs['Color'].default_value = (0.95, 0.95, 0.88, 1); bv.inputs['Anisotropy'].default_value = 0.5
bv.inputs['Density'].default_value = float(E("BEAM_D", "0.12"))
bmat.node_tree.links.new(bv.outputs[0], BN["Material Output"].inputs['Volume']); cone.data.materials.append(bmat); cone.visible_shadow = False
N_MOTE = int(E("NMOTE", "90"))
r_ = np.random.default_rng(5); t_ = r_.uniform(0.1, 0.95, N_MOTE)
ax = np.array(HP - KEYP); rad = np.tan(math.radians(float(E("KEY_ANG", "17")) / 2)) * np.linalg.norm(ax) * t_ * np.sqrt(r_.uniform(0, 1, N_MOTE))
ph_ = r_.uniform(0, 2 * np.pi, N_MOTE)
P = np.array(KEYP) + t_[:, None] * ax + np.stack([np.cos(ph_) * rad, np.sin(ph_) * rad, np.zeros(N_MOTE)], 1)
me = bpy.data.meshes.new("motes"); me.from_pydata(P.tolist(), [], []); me.update()
mo = bpy.data.objects.new("motes", me); col.objects.link(mo)
ng = bpy.data.node_groups.new("motes_pts", "GeometryNodeTree")
ng.interface.new_socket("Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
ng.interface.new_socket("Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')
gi = ng.nodes.new("NodeGroupInput"); go = ng.nodes.new("NodeGroupOutput"); mp = ng.nodes.new("GeometryNodeMeshToPoints")
mp.inputs['Radius'].default_value = 0.004
smn = ng.nodes.new("GeometryNodeSetMaterial")
mm = bpy.data.materials.new("mote"); mm.use_nodes = True; MN = mm.node_tree.nodes; MN.remove(MN["Principled BSDF"])
em = MN.new("ShaderNodeEmission"); em.inputs['Color'].default_value = (1.0, 0.96, 0.85, 1); em.inputs['Strength'].default_value = float(E("MOTE_E", "4"))
mm.node_tree.links.new(em.outputs[0], MN["Material Output"].inputs['Surface']); smn.inputs['Material'].default_value = mm
ng.links.new(gi.outputs[0], mp.inputs['Mesh']); ng.links.new(mp.outputs['Points'], smn.inputs['Geometry']); ng.links.new(smn.outputs['Geometry'], go.inputs[0])
mo.modifiers.new("pts", "NODES").node_group = ng
for o in sc.objects:
    if o.type == 'LIGHT' and o.name != "key":
        o.visible_volume_scatter = False
try:
    sc.world.cycles_visibility.scatter = False
except Exception:
    pass

# ---------------------------------------------------------------- camera: ~43 deg down, hero on the left third
EL = math.radians(float(E("CAM_EL", "43"))); DIST = float(E("DIST", "5.0")); AZ = math.radians(float(E("CAM_AZ", "-100")))
tgt = Vector((float(E("TX", "0.55")), float(E("TY", "2.3")), float(E("TZ", "0.7"))))
cam = tgt + Vector((math.cos(AZ) * math.cos(EL), math.sin(AZ) * math.cos(EL), math.sin(EL))) * DIST
C.camera(cam, tgt, lens=float(E("LENS", "26")), fstop=float(E("FSTOP", "6")), focus=(HP - cam).length)

T.grade(sc, sat=float(E("SAT", "1.25")), con=float(E("CON", "1.15")), expo=float(E("EXPO", "0.0")), vig=float(E("VIG", "0.4")))
T.render(sc, "antwerp_topdown")
