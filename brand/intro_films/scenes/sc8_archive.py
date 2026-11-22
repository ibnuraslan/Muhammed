"""Seldom intro 8: THE ARCHIVIST (12 s).
A deep archive after hours. A drawer that should be empty isn't: inside lies one folded file, and in the file an
embossed, enamelled plate carrying the official Seldom art.

SHOT=1  wide down the endless aisle of card-index cabinets, one desk lamp at the far end; she walks, a finger on the labels
SHOT=2  medium: the drawer with a blank label holder is stuck; she pulls with both hands
SHOT=3  close over her shoulder: the drawer slides out in a puff of dust, one folded file inside
SHOT=4  logo close-up / final hold: top-down on the opened file under the lamp, the plate inside
"""
import os, sys, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C
C.reset()
import bpy
from mathutils import Vector, Matrix
import ship, ph, poses as P, human as H, women as W
import intro_common as I

sc = I.setup(spp=48)
SHOT = I.SHOT
R = random.Random(8)

oak = I.tex("old_wood_floor" if False else "wood_table_worn", 1.6, tint=(0.62, 0.42, 0.26), name="oak", fallback=(0.3, 0.18, 0.09))
oak.node_tree.nodes["Principled BSDF"].inputs["Coat Weight"].default_value = 0.25
brass = I.grunge(I.principled("brass", (0.72, 0.52, 0.22), 0.32, 1.0), 20, 0.45, (0.3, 0.25, 0.15), (0.25, 0.5))
card = I.principled("label_card", (0.8, 0.76, 0.64), 0.85)
parq = I.tex("herringbone_parquet", 0.8, tint=(0.6, 0.45, 0.32), name="parquet", fallback=(0.25, 0.15, 0.08))
plaster = I.tex("grey_plaster", 0.8, tint=(0.5, 0.48, 0.44), name="arch_wall", fallback=(0.3, 0.3, 0.28))

DW, DH, DD = 0.125, 0.105, 0.42            # drawer face width, height, depth
COLS, ROWS = 6, 14                          # one cabinet unit: 6 x 14 drawers on a plinth
UNIT_W = COLS * DW + 0.06
UNIT_H = ROWS * DH + 0.06
PLINTH = 0.12
AISLE = 1.5                                # clear width between the facing cabinets
LENGTH = 22.0


def drawer(name, x, y, z, face_dir, out=0.0, blank=False, coll=None):
    """One card drawer: oak front with a brass pull and a brass label holder (card in it unless blank)."""
    n = Vector(face_dir)
    c = Vector((x, y, z)) + n * out
    objs = [ship.box(name, c - n * DD / 2, (DW - 0.006, DD, DH - 0.006) if n.y else (DD, DW - 0.006, DH - 0.006), oak, bevel=0.002)]
    fz = c + n * 0.003
    t = (0.06, 0.004, 0.026) if n.y else (0.004, 0.06, 0.026)
    objs.append(ship.box(name + "_holder", fz + Vector((0, 0, 0.022)), t, brass))
    if not blank:
        tc = (0.052, 0.002, 0.019) if n.y else (0.002, 0.052, 0.019)
        objs.append(ship.box(name + "_card", fz + n * 0.002 + Vector((0, 0, 0.022)), tc, card))
    objs.append(ship.cyl(name + "_pull", fz, fz + n * 0.018 + Vector((0, 0, -0.018)), 0.007, mat=brass, verts=10))
    return objs


def cabinet_unit(name):
    """Builds one cabinet unit (facing -Y, its front at y=0) and joins it into one mesh for instancing."""
    objs = [ship.box(name + "_carcass", (0, DD / 2 + 0.01, PLINTH + UNIT_H / 2), (UNIT_W, DD + 0.02, UNIT_H), oak),
            ship.box(name + "_plinth", (0, DD / 2, PLINTH / 2), (UNIT_W - 0.04, DD - 0.02, PLINTH), oak),
            ship.box(name + "_cornice", (0, DD / 2 - 0.01, PLINTH + UNIT_H + 0.03), (UNIT_W + 0.04, DD + 0.06, 0.06), oak)]
    for i in range(COLS):
        for j in range(ROWS):
            x = -UNIT_W / 2 + 0.03 + DW / 2 + i * DW; z = PLINTH + 0.03 + DH / 2 + j * DH
            objs += drawer(f"{name}_d", x, -0.001, z, (0, -1, 0))
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs:
        o.select_set(True)
    for o in objs:
        for m in o.modifiers:
            bpy.context.view_layer.objects.active = o
            bpy.ops.object.modifier_apply(modifier=m.name)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    u = bpy.context.active_object; u.name = name
    # joining keeps the carcass's origin (mid-height): move the geometry so the origin is the unit's foot at its front
    u.data.transform(u.matrix_world); u.matrix_world = Matrix.Identity(4)
    return u


unit = cabinet_unit("cab_unit")
unit.location = (0, 1000, 0)                      # the master copy is parked off set
# the aisle: two facing runs of units (right run faces -X, left run faces +X); gaps every few units for cross-aisles
placed = []
y = -1.0
k = 0
while y < LENGTH:
    for side in (1, -1):
        o = unit.copy(); bpy.context.scene.collection.objects.link(o)
        o.location = (side * (AISLE / 2), y, 0); o.rotation_euler = (0, 0, math.radians(-90 if side > 0 else 90))   # fronts face the aisle
        placed.append(o)
    y += UNIT_W + (0.9 if k % 5 == 4 else 0.0)
    k += 1
ship.box("floor", (0, LENGTH / 2, -0.02), (8, LENGTH + 6, 0.04), parq)
ship.box("ceiling", (0, LENGTH / 2, 3.2), (8, LENGTH + 6, 0.06), plaster)
for side in (1, -1):
    ship.box("wall", (side * 2.3, LENGTH / 2, 1.6), (0.06, LENGTH + 6, 3.2), plaster)
ship.box("end_wall", (0, LENGTH + 0.6, 1.6), (8, 0.06, 3.2), plaster)

# far end: the reading desk and its green-shaded lamp (the only light), a chair
DESK = Vector((0.0, LENGTH - 0.6, 0.0))
ship.box("desk_top", DESK + Vector((0, 0, 0.76)), (1.2, 0.7, 0.04), oak)
for sx in (-0.55, 0.55):
    for sy in (-0.3, 0.3):
        ship.box("desk_leg", DESK + Vector((sx, sy, 0.37)), (0.05, 0.05, 0.74), oak)
green = I.principled("lamp_shade", (0.02, 0.18, 0.06), 0.15, 0.0)
green.node_tree.nodes["Principled BSDF"].inputs["Coat Weight"].default_value = 1.0
LAMP = DESK + Vector((0.32, 0.12, 0.76))
ship.cyl("lamp_base", LAMP, LAMP + Vector((0, 0, 0.025)), 0.07, mat=brass, verts=24)
ship.cyl("lamp_stem", LAMP + Vector((0, 0, 0.02)), LAMP + Vector((0, 0, 0.36)), 0.009, mat=brass, verts=10)
bpy.ops.mesh.primitive_cylinder_add(vertices=40, radius=0.12, depth=0.1, location=LAMP + Vector((-0.06, 0, 0.4)), rotation=(0, math.radians(90), 0))
shade = bpy.context.active_object; shade.scale = (0.55, 1, 1); shade.data.materials.append(green)
sol = shade.modifiers.new("s", 'SOLIDIFY'); sol.thickness = 0.004
LAMP_L = LAMP + Vector((-0.06, 0, 0.26))          # just under the shade
I.spot("desk_lamp", LAMP_L, LAMP_L + Vector((-0.1, -0.05, -0.4)), 140, (1.0, 0.78, 0.48), size_deg=95, blend=0.6, radius=0.03)
I.point("desk_lamp_glow", LAMP_L + Vector((0, 0, 0.01)), 9.0, (1.0, 0.8, 0.5), 0.03)
# the lamp's spill bouncing off the desk and floor toward the last cabinets (motivated warm fill)
I.area("lamp_bounce", DESK + Vector((0, -0.9, 1.0)), DESK + Vector((0.3, -3.0, 1.2)), 22, (1.0, 0.72, 0.45), 1.2)
# a faint, cold spill from a high window somewhere in the stacks, plus dust in the air
I.area("stack_spill", (1.8, 6.0, 3.0), (0, 4, 0.5), 160, (0.5, 0.6, 0.85), 2.5)
for yy in (3.0, 9.5, 16.0):                       # enamel pendants over the aisle, one in three still working
    ship.cyl("pendant_cord", (0, yy, 3.17), (0, yy, 2.65), 0.004, mat=I.principled("cord", (0.02, 0.02, 0.02), 0.6), verts=6)
    bpy.ops.mesh.primitive_cone_add(vertices=32, radius1=0.2, radius2=0.04, depth=0.14, location=(0, yy, 2.6))
    sh = bpy.context.active_object; sh.data.materials.append(I.principled("pendant", (0.08, 0.12, 0.1), 0.3))
    sol_ = sh.modifiers.new("s", 'SOLIDIFY'); sol_.thickness = 0.003
    if yy == 9.5:
        I.spot("pendant_L", (0, yy, 2.52), (0, yy, 0), 110, (1.0, 0.75, 0.45), size_deg=100, blend=0.7, radius=0.04)
        I.point("pendant_bulb", (0, yy, 2.55), 1.5, (1.0, 0.75, 0.45), 0.03)
I.haze((0, LENGTH / 2, 1.6), (4.5, LENGTH + 4, 3.1), density=0.018, color=(0.95, 0.9, 0.85), aniso=0.5)

# the drawer: right-hand run, a unit about 3.5 m short of the desk, at her chest height, blank label holder
DR_Y = None
right = [o for o in placed if o.location.x > 0]
target_unit = min(right, key=lambda o: abs(o.location.y - (LENGTH - 2.7)))
# the stuck drawer is built as a separate object in front of the unit's slot (that slot is cut away by a hole box)
col, row = 2, 9
ux, uy = target_unit.location.x, target_unit.location.y
dx_local = -UNIT_W / 2 + 0.03 + DW / 2 + col * DW
# right run is rotated -90 deg: local -Y (front) -> world -X, local +X -> world -Y
slot = Vector((ux, uy - dx_local, PLINTH + 0.03 + DH / 2 + row * DH))
FACE = Vector((-1, 0, 0))
OUT = {1: 0.0, 2: 0.04, 3: 0.3, 4: 0.3}[SHOT]
# hide the unit's own drawer in that slot: a dark void box covers it, the real drawer sits in front of it
void = ship.box("slot_void", slot + Vector((0.004, 0, 0)), (0.012, DW - 0.004, DH - 0.004), I.principled("void", (0.005, 0.004, 0.003), 0.9))
dobjs = drawer("the_drawer", slot.x - 0.006, slot.y, slot.z, FACE, out=OUT, blank=True)
DRAWER_FRONT = slot + FACE * (OUT + 0.006)
# the folded file inside the drawer (manila, tied with tape)
manila = I.grunge(I.principled("manila", (0.68, 0.54, 0.3), 0.75), 14, 0.35, (0.5, 0.4, 0.3))
if SHOT in (2, 3):
    fpos = DRAWER_FRONT - FACE * 0.2 + Vector((0, 0, -DH / 2 + 0.03))
    ship.box("file_folded", fpos, (0.24, 0.09, 0.028), manila, bevel=0.002)
if SHOT == 3:
    I.haze(DRAWER_FRONT + Vector((-0.02, 0, 0.08)), (0.4, 0.35, 0.3), density=0.9, color=(0.95, 0.9, 0.82), noise_scale=12)
    I.streaks("dust_motes", DRAWER_FRONT + Vector((-0.2, 0, 0.15)), (0.8, 0.8, 0.6), 600, wind=(0.1, 0.2, 1.0),
              length=(0.002, 0.005), radius=0.0006, mat=I.principled("mote", (1, 0.95, 0.85), 0.5, emit=(1, 0.85, 0.6), estr=1.5))


def plate_and_file(center):
    """The opened file on the desk: manila folder lying open, typed sheet on the left leaf, the plate on the right."""
    ship.box("folder_l", center + Vector((-0.17, 0, 0.0015)), (0.32, 0.25, 0.003), manila)
    ship.box("folder_r", center + Vector((0.17, 0, 0.0015)), (0.32, 0.25, 0.003), manila)
    ship.box("sheet", center + Vector((-0.17, 0.0, 0.0035)), (0.27, 0.22, 0.001), I.principled("onionskin", (0.85, 0.83, 0.75), 0.8))
    # embossed + enamelled brass plate: real relief from the art's alpha, enamel in the recesses-turned-raised letters
    pc = center + Vector((0.17, 0.0, 0.004))
    pw = 0.24; phh = pw / I.LOGO_AR * 1.5
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=420, y_subdivisions=180, size=1, location=pc)
    pl = bpy.context.active_object; pl.name = "logo_plate"; pl.scale = (pw, phh, 1); bpy.ops.object.transform_apply(scale=True)
    # UV: the art fills the centre 80% of the plate
    uvl = pl.data.uv_layers.active
    xs = [v.co.x for v in pl.data.vertices]; ys = [v.co.y for v in pl.data.vertices]
    cx0, cy0 = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    for lp in pl.data.loops:
        v = pl.data.vertices[lp.vertex_index].co
        u_ = ((v.x - cx0) / pw) / 0.84 + 0.5; v_ = ((v.y - cy0) / phh) / (0.84 / 1.5) + 0.5
        uvl.data[lp.index].uv = (u_, v_)
    tex = bpy.data.textures.new("logo_alpha", 'IMAGE'); tex.image = bpy.data.images.load(I.LOGO, check_existing=True)
    tex.use_alpha = True; tex.extension = 'CLIP'; tex.use_interpolation = True
    d = pl.modifiers.new("emboss", 'DISPLACE'); d.texture = tex; d.texture_coords = 'UV'; d.uv_layer = uvl.name
    d.direction = 'Z'; d.strength = 0.0016; d.mid_level = 0.0
    sm = pl.modifiers.new("soft", 'SMOOTH'); sm.factor = 0.5; sm.iterations = 2
    so = pl.modifiers.new("thick", 'SOLIDIFY'); so.thickness = 0.0025; so.offset = -1
    pm = I.grunge(I.principled("plate_brass", (0.75, 0.55, 0.24), 0.28, 1.0), 30, 0.3, (0.4, 0.3, 0.15), (0.2, 0.45))
    I.logo_layer(pm, kind="enamel", wear=0.05)
    pl.data.materials.append(pm); bpy.ops.object.shade_smooth()
    for sx in (-1, 1):
        for sy in (-1, 1):                                  # four domed rivets
            bpy.ops.mesh.primitive_uv_sphere_add(radius=0.004, location=pc + Vector((sx * (pw / 2 - 0.008), sy * (phh / 2 - 0.008), 0.001)))
            r_ = bpy.context.active_object; r_.scale = (1, 1, 0.5); r_.data.materials.append(brass)
    return pc


def archivist(pose, M, look):
    class Archivist(W.Sarah):
        DRESS = (0.022, 0.026, 0.04)     # dark navy wool day dress (reads as fabric, not skin, under the warm lamp)
        SHAWL = (0.035, 0.06, 0.04)      # bottle-green knitted shawl worn like a cardigan
    s = Archivist(name="Archivist", bonnet=False, shawl=True)
    h = s.h; Mi = M.inverted()
    ex = pose(s, h, Mi) or {}
    s.finish(look_at=look, place=M, density=float(os.environ.get("HAIR", "0.7")))
    return s, ex


if SHOT == 1:
    def pose1(s, h, Mi):
        P.stand(h, lean=3, weight="R")
        P.head(h, pitch=4, yaw=-28)
        # left hand out to the right-hand run? She walks the aisle from behind with her right hand on the labels.
        P.hand_reach(h, "R", Mi @ Vector((AISLE / 2 - 0.025, 6.6, 1.22)), elbow=(-0.5, 0.2, -0.9))
        h.aim("wrist.R", (Mi.to_3x3() @ Vector((0.35, 0.9, -0.1))).normalized()); P.rest_hand(h, "R", curl=18)
        P.arm_down(h, "L", out=0.28, fwd=0.04, bend=14); P.rest_hand(h, "L")
        return {}
    M = I.yaw(180, (0.22, 6.35, 0))
    archivist(pose1, M, Vector((0.6, 10, 1.3)))
    C.camera(Vector((-0.15, 2.4, 1.45)), Vector((0.05, LENGTH - 1, 1.15)), lens=28, fstop=2.8, focus=4.2)
    C.finish(I.out("f8_k1_aisle"), cine={"exposure": 0.25, "sat": 1.05})
elif SHOT in (2, 3):
    def pose2(s, h, Mi):
        P.stand(h, lean=10 if SHOT == 2 else 8, weight="L" if SHOT == 2 else "R", twist=0)
        P.head(h, pitch=14 if SHOT == 2 else 30)
        pull = DRAWER_FRONT + FACE * 0.02
        if SHOT == 2:
            P.hand_reach(h, "R", Mi @ (pull + Vector((0, -0.01, -0.03))), elbow=(-0.7, 0.3, -0.6))
            h.aim("wrist.R", (Mi.to_3x3() @ Vector((0.9, 0.0, -0.3))).normalized()); P.grip(h, "R", 0.9)
            P.hand_reach(h, "L", Mi @ (DRAWER_FRONT + FACE * 0.01 + Vector((0, 0.09, 0.0))), elbow=(0.7, 0.3, -0.6))
            h.aim("wrist.L", (Mi.to_3x3() @ Vector((0.9, -0.15, 0.0))).normalized()); P.rest_hand(h, "L", curl=40)
        else:
            P.hand_reach(h, "R", Mi @ (DRAWER_FRONT + Vector((0.08, -0.07, 0.02))), elbow=(-0.7, 0.3, -0.6))
            h.aim("wrist.R", (Mi.to_3x3() @ Vector((0.9, 0.0, -0.35))).normalized()); P.grip(h, "R", 0.6)
            P.arm_down(h, "L", out=0.28, fwd=0.1, bend=24); P.rest_hand(h, "L")
        s.lids(0.3)
        return {}
    base = Vector((slot.x - 0.62 - OUT, slot.y + 0.1, 0))
    M = I.yaw(I.facing((1, -0.08)), base)
    archivist(pose2, M, DRAWER_FRONT)
    if SHOT == 2:
        C.camera(Vector((-0.5, slot.y - 1.55, 1.5)), Vector((slot.x - 0.38, slot.y - 0.05, 1.42)), lens=40, fstop=2.4)   # waist-up
        C.finish(I.out("f8_k2_stuck"), cine={"exposure": 0.3, "sat": 1.05})
    else:
        C.camera(Vector((base.x - 0.42, base.y + 0.38, 1.72)), DRAWER_FRONT - FACE * 0.18 + Vector((0, 0, -0.03)), lens=38, fstop=2.8)
        C.finish(I.out("f8_k3_drawer"), cine={"exposure": 0.35, "sat": 1.05})
else:
    FILE = DESK + Vector((-0.12, -0.08, 0.78))
    pc = plate_and_file(FILE)

    def pose4(s, h, Mi):
        P.stand(h, lean=26, weight="L")
        P.head(h, pitch=40, yaw=-10)
        for sd, dx in (("L", -0.33), ("R", 0.33)):
            edge = FILE + Vector((dx, -0.1, 0.004))
            P.hand_reach(h, sd, Mi @ (edge + Vector((0, -0.04, 0.035))), elbow=(0.8 * H.SIDE[sd], 0.3, -0.5))
            h.aim(f"wrist.{sd}", (Mi.to_3x3() @ Vector((-0.2 * H.SIDE[sd], 1, -0.55))).normalized()); P.rest_hand(h, sd, curl=20)
        s.lids(0.6)
        return {}
    M = I.yaw(0, (FILE.x, FILE.y - 0.58, 0))
    archivist(pose4, M, pc)
    C.camera(pc + Vector((-0.17, 0.3, 0.55)), pc + Vector((-0.12, -0.04, 0.0)), lens=40, fstop=4.0, roll=180)
    C.finish(I.out("f8_k4_logo"), cine={"exposure": 0.3, "sat": 1.1})
