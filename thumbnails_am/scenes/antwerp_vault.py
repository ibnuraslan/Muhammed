"""Antwerp thumbnail A2, "the hole in the vault": an extreme wide shot through a massive round vault door hanging
open. Beyond it an impossibly long, brightly lit hall of safe-deposit boxes, every one forced, doors hanging,
papers on the floor. One tiny figure seen from behind with a torch far down the hall; one diamond glinting on the
floor in the foreground. Bright and clean. No text, no faces. The pale wall left of the door stays clean for the title.
Box doors and cells reuse the film's vault library (lib/sets.py).
    PREVIEW=0.4 SPP=48 blender -b --python antwerp_vault.py"""
import os, sys, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tcommon as T
C = T.use("antwerp")
import bpy, bmesh
from mathutils import Vector, Matrix
import sets as S, props as PR, ship as SH
E = os.environ.get
sc = T.res_setup(int(E("SPP", "256")), noise=0.01)
sc.cycles.max_bounces = 6; sc.cycles.diffuse_bounces = 3
col = sc.collection
rng = random.Random(int(E("SEED", "3")))

HW, HZ, HL = float(E("HW", "1.9")), float(E("HZ", "3.4")), float(E("HL", "34"))   # hall half-width, height, length
CW, RH, Z0 = 0.27, 0.38, 0.3
NROW = int((HZ - Z0 - 0.25) / RH); NCOL = int(HL / CW)
R_DOOR = float(E("RDOOR", "1.25")); DZ = R_DOOR + 0.12             # round opening radius, centre height
WALLT = 0.9

# ---------------------------------------------------------------- materials
box_steel = S.brushed("box_steel", (0.78, 0.76, 0.72), rough=0.22)
brass = S.gold("brass_plate", (0.85, 0.6, 0.22)); brass.node_tree.nodes["Principled BSDF"].inputs['Roughness'].default_value = 0.25
black = S.flat("keyhole", (0.005, 0.005, 0.005), 0.5)
cavity_m = S.flat("cavity", (0.16, 0.15, 0.14), 0.6, metal=0.2)
frame_m = S.steel_paint("box_frame", (0.42, 0.4, 0.37), rough=0.4, wear=0.15)
floor_m = S.tex("marble_01", 1.2, tint=(1.0, 0.98, 0.95), name="hall_floor")
floor_m.node_tree.nodes["Principled BSDF"].inputs['Coat Weight'].default_value = 0.35
ceil_m = S.flat("ceiling", (0.85, 0.85, 0.83), 0.8)
wall_m = S.flat("front_wall", tuple(float(x) for x in E("WALLC", "0.05,0.2,0.48").split(",")), 0.7)
door_steel = S.brushed("vault_steel", (0.8, 0.8, 0.8), rough=0.18)
door_paint = S.steel_paint("vault_paint", (0.55, 0.57, 0.58), rough=0.3, wear=0.1)
glow = S.emit("tube", (1.0, 0.88, 0.7), float(E("TUBE", "12")))

# ---------------------------------------------------------------- the hall: floor, ceiling, light strips
S.box("hall_floor", (0, HL / 2, -0.05), (2 * HW + 1, HL + 2, 0.1), floor_m)
S.box("hall_ceiling", (0, HL / 2, HZ + 0.05), (2 * HW + 1, HL + 2, 0.1), ceil_m)
S.box("hall_end", (0, HL + 0.6, HZ / 2), (2 * HW + 1, 0.1, HZ), frame_m)
for x in (-0.6, 0.6):
    S.box("strip", (x, HL / 2, HZ - 0.01), (0.12, HL, 0.02), glow)

# ---------------------------------------------------------------- boxes: every door forced open
door_t = S._door_mesh(CW, RH, "boxdoor", (box_steel, brass, black))
cav_t = S._cavity_mesh(CW, RH, 0.45, "cavity", cavity_m)
for o in (door_t, cav_t):
    for c_ in list(o.users_collection):
        c_.objects.unlink(o)
n = 0
for sg in (1, -1):
    xw = sg * HW
    for c in range(NCOL):
        for r in range(NROW):
            z = Z0 + (r + 0.5) * RH
            if sg < 0:
                org = Vector((xw + 0.005, c * CW, z)); yaw = math.pi / 2
            else:
                org = Vector((xw - 0.005, (c + 1) * CW, z)); yaw = -math.pi / 2
            R = Matrix.Rotation(yaw, 4, 'Z')
            cv = cav_t.copy(); col.objects.link(cv); cv.matrix_world = Matrix.Translation(org) @ R
            d = door_t.copy(); col.objects.link(d)
            ang = rng.uniform(75, 150)
            d.matrix_world = Matrix.Translation(org) @ R @ Matrix.Rotation(math.radians(-ang), 4, 'Z') @ \
                Matrix.Rotation(math.radians(rng.uniform(-5, 5)), 4, 'X')
            n += 1
    # the frame grid: stiles and rails
    for c in range(0, NCOL + 1):
        S.box("stile", (sg * (HW - 0.012), c * CW, Z0 + NROW * RH / 2), (0.03, 0.014, NROW * RH + 0.02), frame_m)
    for r in range(NROW + 1):
        S.box("rail", (sg * (HW - 0.012), HL / 2, Z0 + r * RH), (0.03, NCOL * CW, 0.014), frame_m)
    S.box("plinth", (sg * (HW - 0.06), HL / 2, Z0 / 2), (0.12, NCOL * CW, Z0), frame_m)
    S.box("cornice", (sg * (HW - 0.05), HL / 2, (Z0 + NROW * RH + HZ) / 2), (0.1, NCOL * CW, HZ - Z0 - NROW * RH), frame_m)
    S.box("backing", (sg * (HW + 0.47), HL / 2, Z0 + NROW * RH / 2), (0.02, NCOL * CW, NROW * RH), cavity_m)
print("BOXES", n)

# ---------------------------------------------------------------- papers and empty trays on the floor
PAPERC = [(0.92, 0.92, 0.9), (0.95, 0.6, 0.72), (0.35, 0.6, 0.98), (0.98, 0.88, 0.45)]
pmats = [S.paper_mat(f"paper{i}", c_) for i, c_ in enumerate(PAPERC)]
for i in range(int(E("NPAPER", "420"))):
    y = rng.uniform(0.3, HL - 1) ** 1.0
    x = rng.uniform(-HW + 0.2, HW - 0.2)
    m = pmats[rng.randrange(4)]
    S.box("paper", (x, y, 0.002 + 0.0006 * (i % 5)), (rng.uniform(0.12, 0.22), rng.uniform(0.09, 0.3), 0.0008), m,
          rot=(0, 0, rng.uniform(0, 6.28)))

# ---------------------------------------------------------------- front wall with the round opening
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, -WALLT / 2, HZ / 2 + 0.6))
fw = bpy.context.active_object; fw.name = "front_wall"; fw.scale = (14, WALLT, HZ + 1.2 + 3)
bpy.ops.mesh.primitive_cylinder_add(vertices=128, radius=R_DOOR, depth=WALLT * 3, location=(0, -WALLT / 2, DZ),
                                    rotation=(math.pi / 2, 0, 0))
hole = bpy.context.active_object; hole.hide_render = True; hole.hide_viewport = True
bo = fw.modifiers.new("hole", "BOOLEAN"); bo.object = hole; bo.operation = 'DIFFERENCE'; bo.solver = 'EXACT'
fw.data.materials.append(wall_m)
# the steel jamb ring lining the opening, and a stepped face ring
ring = SH.cyl("jamb", (0, 0.0, DZ), (0, -WALLT, DZ), R_DOOR + 0.001, mat=door_steel, verts=128, caps=False)
for o_ in (ring,):
    so = o_.modifiers.new("t", "SOLIDIFY"); so.thickness = 0.06
bpy.ops.mesh.primitive_torus_add(major_radius=R_DOOR + 0.12, minor_radius=0.08, major_segments=128, minor_segments=16,
                                 location=(0, -WALLT - 0.01, DZ), rotation=(math.pi / 2, 0, 0))
tr = bpy.context.active_object; tr.name = "face_ring"; tr.scale = (1, 1, 0.5); tr.data.materials.append(door_steel)
# floor outside (where the camera stands) and a sill across the opening
S.box("ante_floor", (0, -WALLT - 4, -0.05), (14, 8, 0.1), floor_m)
S.box("ante_ceiling", (0, -WALLT - 4, HZ + 1.8), (14, 8, 0.1), ceil_m)

# ---------------------------------------------------------------- the round door, swung wide open toward camera
TH = float(E("DOORT", "0.7"))
leaf = bpy.data.objects.new("vault_door", None); col.objects.link(leaf)


def part(o):
    o.parent = leaf; return o


# local frame: hinge at origin, door disc centred at x = -R (closed it would fill the opening), outer face at -y
Rd = R_DOOR - 0.01
part(SH.cyl("door_body", (-Rd, 0.0, 0), (-Rd, -TH, 0), Rd, mat=door_paint, verts=128))
part(SH.cyl("door_step", (-Rd, -TH, 0), (-Rd, -TH - 0.08, 0), Rd + 0.1, mat=door_steel, verts=128))
for k, rr in enumerate((Rd * 0.82, Rd * 0.6)):
    bpy.ops.mesh.primitive_torus_add(major_radius=rr, minor_radius=0.025, major_segments=96, minor_segments=12,
                                     location=(-Rd, -TH - 0.08, 0), rotation=(math.pi / 2, 0, 0))
    t_ = bpy.context.active_object; t_.data.materials.append(door_steel); part(t_)
# inner face (seen when open): bolt-work cover plate with rings and a centre gear
part(SH.cyl("inner_plate", (-Rd, 0.0, 0), (-Rd, 0.04, 0), Rd * 0.88, mat=door_steel, verts=96))
for rr in (Rd * 0.75, Rd * 0.45, Rd * 0.2):
    bpy.ops.mesh.primitive_torus_add(major_radius=rr, minor_radius=0.03, major_segments=96, minor_segments=12,
                                     location=(-Rd, 0.045, 0), rotation=(math.pi / 2, 0, 0))
    t_ = bpy.context.active_object; t_.data.materials.append(brass); part(t_)
for k in range(8):
    a = 2 * math.pi * k / 8
    part(SH.cyl("bar", (-Rd, 0.05, 0), (-Rd + math.cos(a) * Rd * 0.8, 0.05, math.sin(a) * Rd * 0.8), 0.035, mat=door_steel, verts=12))
# locking bolts all round the rim (chrome)
for k in range(int(E("NBOLT", "16"))):
    a = 2 * math.pi * k / 16
    c0 = Vector((-Rd + math.cos(a) * (Rd - 0.02), -TH * 0.45, math.sin(a) * (Rd - 0.02)))
    c1 = Vector((-Rd + math.cos(a) * (Rd + 0.16), -TH * 0.45, math.sin(a) * (Rd + 0.16)))
    part(SH.cyl("bolt", c0, c1, 0.055, mat=door_steel, verts=24))
# hub and three-spoke wheel on the outer face
hub = Vector((-Rd, -TH - 0.08, 0))
part(SH.cyl("hub", hub, hub + Vector((0, -0.12, 0)), 0.14, mat=door_steel, verts=48))
for k in range(3):
    a = math.radians(90 + 120 * k)
    part(SH.cyl("spoke", hub + Vector((0, -0.1, 0)), hub + Vector((math.cos(a) * 0.55, -0.1, math.sin(a) * 0.55)), 0.03,
                mat=door_steel, verts=16))
    part(SH.cyl("knob", hub + Vector((math.cos(a) * 0.55, -0.1, math.sin(a) * 0.55)),
                hub + Vector((math.cos(a) * 0.55, -0.22, math.sin(a) * 0.55)), 0.04, mat=door_steel, verts=16))
# hinge arm and pin (outside the wall on the right)
HX = R_DOOR + 0.25
leaf.location = (HX, -WALLT - 0.12, DZ)
leaf.rotation_euler.z = math.radians(float(E("DOOR_ANG", "122")))
S.box("hinge_block", (HX + 0.1, -WALLT - 0.12, DZ), (0.3, 0.3, 1.6), door_steel, bevel=0.02)
SH.cyl("hinge_pin", (HX, -WALLT - 0.12, DZ - 1.0), (HX, -WALLT - 0.12, DZ + 1.0), 0.09, mat=door_steel, verts=32)
for dz in (-0.55, 0.55):
    S.box("hinge_arm", (HX - 0.25, -WALLT - 0.3, DZ + dz), (0.5, 0.18, 0.18), door_steel, bevel=0.02)
    part_ = None

# ---------------------------------------------------------------- the tiny figure with a torch, from behind
FY = float(E("FIG_Y", "11"))
dark = S.flat("clothes", (0.03, 0.03, 0.035), 0.7)
skin_hair = S.flat("hair", (0.02, 0.015, 0.012), 0.6)
fig = bpy.data.objects.new("figure", None); col.objects.link(fig)
def fp(o):
    o.parent = fig; return o
fp(SH.cyl("legL", (-0.09, 0, 0.0), (-0.1, 0, 0.88), 0.075, 0.085, mat=dark, verts=16))
fp(SH.cyl("legR", (0.09, 0.04, 0.0), (0.1, 0, 0.88), 0.075, 0.085, mat=dark, verts=16))
fp(SH.cyl("torso", (0, 0, 0.85), (0, 0, 1.45), 0.17, 0.2, mat=dark, verts=20))
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.115, location=(0, 0, 1.6)); h_ = bpy.context.active_object
h_.data.materials.append(skin_hair); h_.scale = (0.9, 1.0, 1.1); fp(h_)
fp(SH.cyl("armL", (-0.22, 0, 1.42), (-0.25, 0.02, 0.85), 0.05, mat=dark, verts=12))
fp(SH.cyl("armR", (0.22, 0, 1.42), (0.28, -0.15 + 0.4, 1.1), 0.05, mat=dark, verts=12))   # torch arm raised forward
fp(SH.cyl("torch", (0.28, 0.25, 1.1), (0.29, 0.42, 1.12), 0.025, mat=dark, verts=12))
fig.location = (float(E("FIG_X", "0.15")), FY, 0)
sp = bpy.data.lights.new("torch", 'SPOT'); sp.energy = float(E("TORCH_E", "150")); sp.spot_size = math.radians(30)
sp.spot_blend = 0.5; sp.color = (1.0, 0.92, 0.75); sp.shadow_soft_size = 0.02
so_ = bpy.data.objects.new("torch_l", sp); col.objects.link(so_)
so_.location = fig.location + Vector((0.29, 0.45, 1.12))
so_.rotation_euler = (Vector((0.6, 4.0, -1.0))).to_track_quat('-Z', 'Y').to_euler()
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.03, location=so_.location); bulb = bpy.context.active_object
bulb.data.materials.append(S.emit("torch_glow", (1.0, 0.9, 0.7), 60))

# ---------------------------------------------------------------- one diamond glinting in the foreground
gem = PR.brilliant("hero_gem", float(E("GEM_D", "0.085")))
GP = Vector((float(E("GEM_X", "-0.1")), float(E("GEM_Y", "-2.75")), 0.0))
gem.location = GP + Vector((0, 0, float(E("GEM_D", "0.085")) * 0.43)); gem.rotation_euler = (0.15, -0.1, 0.4)
gl = bpy.data.lights.new("gem_glint", 'POINT'); gl.energy = float(E("GLINT_E", "150")); gl.shadow_soft_size = 0.01
go = bpy.data.objects.new("gem_glint", gl); col.objects.link(go); go.location = GP + Vector((0.3, -0.8, 0.9))
gc = bpy.data.collections.new("gemc"); col.children.link(gc)
for c_ in list(gem.users_collection):
    c_.objects.unlink(gem)
gc.objects.link(gem); go.light_linking.receiver_collection = gc; go.visible_diffuse = False

# ---------------------------------------------------------------- light: bright hall, soft daylight-white outside
S.light_area("hall_fill", (0, HL * 0.3, HZ - 0.2), (0, HL * 0.3, 0), 2.0, float(E("HALL_E", "800")), color=(1, 0.85, 0.62),
             size_y=HL * 0.5)
S.light_area("ante_key", (-2.5, -5.0, 3.0), (0, -WALLT, 1.2), 4.0, float(E("KEY_E", "420")), color=(1.0, 0.96, 0.9))
S.light_area("ante_fill", (2.5, -5.5, 2.0), (0, -WALLT, 1.0), 4.0, float(E("FILL_E", "220")), color=(0.92, 0.96, 1.0))
S.world((0.8, 0.82, 0.85), float(E("WORLD", "0.25")))

# ---------------------------------------------------------------- camera: low, wide, through the round door
cam = Vector((float(E("CAMX", "-0.5")), float(E("CAMY", "-4.6")), float(E("CAMZ", "0.75"))))
tgt = Vector((float(E("AX", "0.35")), float(E("AY", "4")), float(E("AZ", "1.15"))))
C.camera(cam, tgt, lens=float(E("LENS", "20")), fstop=float(E("FSTOP", "8")), focus=(GP - cam).length * 1.6)

if E("CLIP"):
    import clipcheck
    clipcheck.check("antwerp_vault", limit=40); sys.exit(0)
T.grade(sc, sat=float(E("SAT", "1.3")), con=float(E("CON", "1.15")), expo=float(E("EXPO", "0.0")), vig=float(E("VIG", "0.2")))
T.glints(sc, thr=float(E("GLT", "1.0")), strength=float(E("GLS", "0.5")))
T.render(sc, "antwerp_a2")
