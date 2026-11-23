"""Seldom intro 5: PROJECTION BOOTH (13 s).
A shuttered cinema. The projectionist pulls an unlisted can from the vault, threads it, and the leader ends on a
title card: the official Seldom art, projected for real through the lens (a spot light carrying the film frame).

SHOT=1  vault: he holds the dusty can, blows the dust off (0-3 s)
SHOT=2  booth: side-lit by the lamphouse, his hand on the start lever (3-6.5 s)
SHOT=3  over his shoulder through the observation port: the beam over the seats, the card on the screen (6.5-10 s)
SHOT=4  logo close-up / final hold from the back rows: the screen, the beam overhead (10-13 s)
"""
import os, sys, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C
C.reset()
import bpy
from mathutils import Vector, Matrix
import ship, ph, poses as P, human as H, deveau as D
import intro_common as I

sc = I.setup(spp=48)
SHOT = I.SHOT
R = random.Random(5)
CARD = os.path.join(C.HERE, "..", "assets", "seldom_title_card.png")
CARD_AR = 2048 / 1490

# ----------------------------------------------------------------------------- materials
rust_can = I.grunge(I.tex("rusty_metal_02", 3.0, name="can_rust", fallback=(0.25, 0.14, 0.07), rough=0.6), 9, 0.4)
tin = I.grunge(I.principled("can_tin", (0.42, 0.42, 0.4), 0.35, 0.9), 14, 0.55, (0.3, 0.2, 0.12), (0.3, 0.7))
steel = I.grunge(I.principled("rack_steel", (0.16, 0.17, 0.16), 0.45, 0.8), 6, 0.5, (0.35, 0.22, 0.12))
conc = I.tex("concrete_floor_01", 0.6, name="conc", fallback=(0.25, 0.24, 0.22))
wallm = I.grunge(I.principled("wall", (0.3, 0.29, 0.26), 0.85), 3, 0.5, (0.45, 0.4, 0.33))
I.grunge(wallm, 25, 0.25, (0.6, 0.55, 0.5))
label = I.principled("label", (0.62, 0.56, 0.42), 0.85)
proj_paint = I.grunge(I.principled("proj_paint", (0.05, 0.07, 0.06), 0.35, 0.3), 10, 0.4, (0.4, 0.4, 0.4), (0.25, 0.55))
chrome = I.principled("chrome", (0.7, 0.7, 0.7), 0.18, 1.0)
blackm = I.principled("black", (0.012, 0.012, 0.012), 0.6)
glass_m = bpy.data.materials.new("port_glass"); glass_m.use_nodes = True
gp = glass_m.node_tree.nodes["Principled BSDF"]; gp.inputs["Transmission Weight"].default_value = 1.0; gp.inputs["Roughness"].default_value = 0.04
gp.inputs["Base Color"].default_value = (0.9, 0.92, 0.9, 1)


def film_can(name, c, rot=0.0, label_on=True, dusty=0.0):
    x, y, z = c
    m = rust_can if R.random() < 0.6 else tin
    ship.cyl(name, (x, y, z), (x, y, z + 0.052), 0.19, mat=m, verts=40)
    ship.cyl(name + "_lid", (x, y, z + 0.05), (x, y, z + 0.058), 0.193, mat=m, verts=40)
    if label_on:
        o = ship.box(name + "_tape", (x, y, z + 0.059), (0.15, 0.035, 0.002), label, rot=(0, 0, rot))
    if dusty:
        d = I.principled(name + "_dust", (0.5, 0.47, 0.42), 0.95)
        ship.cyl(name + "_dustlayer", (x, y, z + 0.058), (x, y, z + 0.0595), 0.188, mat=d, verts=40)


def rack(x0, x1, y, levels=(0.12, 0.55, 0.98, 1.41, 1.84), depth=0.5):
    for xx in (x0, x1):
        for yy in (y - depth / 2, y + depth / 2):
            ship.box("upright", (xx, yy, 1.05), (0.035, 0.035, 2.1), steel)
    for z in levels:
        ship.box("shelf", ((x0 + x1) / 2, y, z), (x1 - x0, depth, 0.02), steel)
        xx = x0 + 0.24
        while xx < x1 - 0.2:
            n = R.randint(1, 6) if z < 1.7 else R.randint(1, 4)
            for k in range(n):
                film_can("can", (xx + R.uniform(-0.01, 0.01), y + R.uniform(-0.02, 0.02), z + 0.01 + k * 0.06),
                         R.uniform(-0.3, 0.3), label_on=R.random() < 0.7)
            xx += 0.41


def projector(base, face=+1):
    """1940s 35 mm projector on its pedestal; optical axis along +Y; returns the lens point and lever point."""
    bx, by, bz = base
    ship.box("ped_foot", (bx, by, bz + 0.04), (0.55, 0.75, 0.08), proj_paint, bevel=0.01)
    ship.cyl("ped_col", (bx, by, bz + 0.08), (bx, by, bz + 0.85), 0.11, mat=proj_paint, verts=24)
    ship.box("mech", (bx, by + 0.05, bz + 1.05), (0.32, 0.42, 0.42), proj_paint, bevel=0.02)
    for sg, zc in ((1, bz + 1.62), (-1, bz + 0.6)):          # upper and lower magazines (round housings)
        ship.cyl("mag", (bx - 0.09, by + 0.02, zc), (bx + 0.09, by + 0.02, zc), 0.36, mat=proj_paint, verts=48)
        ship.cyl("mag_hub", (bx - 0.1, by + 0.02, zc), (bx - 0.13, by + 0.02, zc), 0.05, mat=chrome, verts=24)
        ship.box("throat", (bx, by + 0.05, (zc + bz + 1.05) / 2), (0.1, 0.1, abs(zc - (bz + 1.05)) - 0.3), proj_paint)
    ship.box("lamphouse", (bx, by - 0.5, bz + 1.12), (0.42, 0.62, 0.55), proj_paint, bevel=0.02)
    ship.cyl("chimney", (bx, by - 0.55, bz + 1.4), (bx, by - 0.55, bz + 2.6), 0.07, mat=proj_paint, verts=20)
    glow = I.principled("vent_glow", (1, 0.8, 0.6), 0.5, emit=(1.0, 0.78, 0.5), estr=14)
    for k in range(6):                                         # lamphouse vents on the operator side, lit from inside
        ship.box("vent", (bx - 0.212, by - 0.72 + k * 0.08, bz + 1.24), (0.004, 0.035, 0.18), glow)
    lens0 = Vector((bx, by + 0.26, bz + 1.08))
    ship.cyl("lens_barrel", lens0, lens0 + Vector((0, 0.26, 0)), 0.055, mat=chrome, verts=32)
    ship.cyl("lens_ring", lens0 + Vector((0, 0.2, 0)), lens0 + Vector((0, 0.27, 0)), 0.062, mat=blackm, verts=32)
    lev0 = Vector((bx - 0.17, by + 0.12, bz + 0.98))
    ship.cyl("lever", lev0, lev0 + Vector((-0.16, 0, 0.12)), 0.011, mat=chrome, verts=12)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.024, location=lev0 + Vector((-0.17, 0, 0.13))); kb = bpy.context.active_object
    kb.data.materials.append(blackm); bpy.ops.object.shade_smooth()
    # film path: the leader running from the upper magazine through the gate (thin dark strip)
    film = I.principled("film", (0.03, 0.025, 0.02), 0.25)
    ship.box("film_up", (bx - 0.16, by + 0.08, bz + 1.38), (0.002, 0.035, 0.4), film)
    I.area("lamphouse_spill", (bx - 0.4, by - 0.55, bz + 1.2), (bx - 1.5, by - 0.4, bz + 1.4), 28, (1.0, 0.72, 0.42), 0.25)
    for nm in ("lens_barrel", "lens_ring"):                    # the lens must not shadow its own beam
        for o in bpy.data.objects:
            if o.name.startswith(nm): o.visible_shadow = False
    return lens0 + Vector((0, 0.30, 0)), lev0 + Vector((-0.17, 0, 0.13))


def projection(lens, target, energy=1500):
    """The real projection: a narrow spot at the lens whose emission is the film frame (title card) mapped by
    ray direction, so the card lands on the screen and the beam in the haze carries its shape."""
    o = I.spot("projector", lens, target, energy, (1.0, 0.95, 0.88), size_deg=28, blend=0.0, radius=0.0)
    l = o.data; l.use_nodes = True; nt = l.node_tree; N = nt.nodes; Lk = nt.links; em = N["Emission"]
    tc = N.new("ShaderNodeTexCoord"); sep = N.new("ShaderNodeSeparateXYZ"); Lk.new(tc.outputs["Normal"], sep.inputs[0])
    dist = (Vector(target) - Vector(lens)).length
    half_w = 3.3                                               # projected card half-width on the screen (m)
    k = 2 * dist / (2 * half_w)
    def m(i, scale):
        d = N.new("ShaderNodeMath"); d.operation = 'DIVIDE'; Lk.new(sep.outputs[i], d.inputs[0]); Lk.new(sep.outputs[2], d.inputs[1])
        f = N.new("ShaderNodeMath"); f.operation = 'MULTIPLY_ADD'; f.inputs[1].default_value = scale; f.inputs[2].default_value = 0.5
        Lk.new(d.outputs[0], f.inputs[0]); return f
    u = m(0, -k / 2); v = m(1, -k / 2 * CARD_AR)
    cb = N.new("ShaderNodeCombineXYZ"); Lk.new(u.outputs[0], cb.inputs[0]); Lk.new(v.outputs[0], cb.inputs[1])
    im = N.new("ShaderNodeTexImage"); im.image = bpy.data.images.load(CARD, check_existing=True); im.extension = 'CLIP'
    Lk.new(cb.outputs[0], im.inputs[0])
    mx = N.new("ShaderNodeMix"); mx.data_type = 'RGBA'; mx.inputs[6].default_value = (0, 0, 0, 1)
    Lk.new(im.outputs["Alpha"], mx.inputs[0]); Lk.new(im.outputs["Color"], mx.inputs[7]); Lk.new(mx.outputs[2], em.inputs["Color"])
    return o


# ----------------------------------------------------------------------------- the projectionist
def projectionist(pose, M, look):
    class Projectionist(D.Deveau):
        HAIR_COLOR = (0.62, 0.3); BEARD_COLOR = (0.55, 0.28)     # lighter sandy-brown: strands read, not a black patch
    pj = Projectionist(name="Projectionist", years=44, wet=0.0)
    h = pj.h; Mi = M.inverted()
    targets = pose(pj, h, Mi)
    pj.finish(look_at=look, place=M, density=max(1.0, float(os.environ.get("HAIR", "0.7"))))
    for o in [x for x in pj.hair_objs if x is not None]:       # clean-shaven projectionist: no beard/moustache strands
        if any(k in o.name.lower() for k in ("beard", "moust", "stache")):
            bpy.data.objects.remove(o, do_unlink=True)
    return pj, targets


if SHOT == 1:
    # ------------------------------------------------------------------- film vault
    ship.box("floor", (0, 1.5, -0.03), (6, 6, 0.06), conc)
    ship.box("wall_back", (0, 3.95, 1.3), (6, 0.1, 2.6), wallm)
    ship.box("wall_l", (-2.6, 1.5, 1.3), (0.1, 6, 2.6), wallm)
    ship.box("wall_r", (2.6, 1.5, 1.3), (0.1, 6, 2.6), wallm)
    ship.box("ceil", (0, 1.5, 2.65), (6, 6, 0.1), wallm)
    rack(-2.4, 2.4, 3.6)
    rack(1.35, 2.35, 1.0, depth=0.45)
    lamp = I.bulb("vault_bulb", (-0.25, 2.05, 2.05), energy=40, cord=0.55)

    def pose1(pj, h, Mi):
        P.stand(h, lean=8, weight="R")
        P.head(h, pitch=26, yaw=-4)
        sh = h.bone_head("upperarm01.L"); z = sh.z - 0.27
        for side, sg in (("L", 1), ("R", -1)):
            P.hand_reach(h, side, Vector((sg * 0.215, -0.29, z)), elbow=(sg * 0.8, 0.3, -0.6))
            h.aim(f"wrist.{side}", Vector((-sg * 0.45, -0.85, 0.05)))
            P.grip(h, side, 0.55)
        pj.lids(0.5)
        return dict(can_local=Vector((0, -0.37, z + 0.0)))
    M = I.yaw(I.facing((0.95, -0.25)), (0.35, 2.85, 0))     # 3/4 away from camera, face in shadow
    pj, t = projectionist(pose1, M, None)
    can_w = M @ t["can_local"]
    film_can("the_can", (can_w.x, can_w.y, can_w.z - 0.03), label_on=False, dusty=1)
    # the puff of dust he has just blown off the lid
    I.haze(can_w + Vector((-0.08, -0.1, 0.16)), (0.5, 0.45, 0.32), density=3.0, color=(0.95, 0.9, 0.82), noise_scale=9)
    I.haze((0, 1.5, 1.3), (5.8, 5.8, 2.6), density=0.035, color=(0.95, 0.9, 0.85), aniso=0.5)
    I.area("fill", (-1.8, -0.6, 1.6), (0.3, 2.7, 1.3), 6, (0.6, 0.7, 0.9), 1.5)
    C.camera(Vector((-1.45, 1.05, 1.12)), Vector((0.25, 2.75, 1.38)), lens=30, fstop=2.4)
    C.finish(I.out("f5_k1_vault"), cine={"exposure": 0.1, "sat": 1.05})
    sys.exit(0)

# ----------------------------------------------------------------------------- booth + auditorium (shots 2-4)
# booth floor z=0, its front wall is y=0; the auditorium floor is at z=-4.2, the screen at y=17
BOOTH_W = 4.0
ship.box("booth_floor", (0, -1.6, -0.03), (BOOTH_W, 3.2, 0.06), conc)
ship.box("booth_back", (0, -3.2, 1.3), (BOOTH_W, 0.1, 2.6), wallm)
ship.box("booth_l", (-2.0, -1.6, 1.3), (0.1, 3.2, 2.6), wallm)
ship.box("booth_r", (2.0, -1.6, 1.3), (0.1, 3.2, 2.6), wallm)
ship.box("booth_ceil", (0, -1.6, 2.65), (BOOTH_W, 3.2, 0.1), wallm)
# front wall with two ports: projection port (x=0) and observation port (x=-0.85)
PORTS = [(0.0, 1.08, 0.38, 0.3), (-0.85, 1.55, 0.62, 0.42)]
def wall_with_ports(y, x0, x1, z0, z1, ports, mat):
    # build the wall as a grid of boxes around the openings
    xs = sorted({x0, x1, *[p[0] - p[2] / 2 for p in ports], *[p[0] + p[2] / 2 for p in ports]})
    zs = sorted({z0, z1, *[p[1] - p[3] / 2 for p in ports], *[p[1] + p[3] / 2 for p in ports]})
    for i in range(len(xs) - 1):
        for j in range(len(zs) - 1):
            cx, cz = (xs[i] + xs[i + 1]) / 2, (zs[j] + zs[j + 1]) / 2
            if any(abs(cx - p[0]) < p[2] / 2 and abs(cz - p[1]) < p[3] / 2 for p in ports):
                continue
            ship.box("wallpiece", (cx, y, cz), (xs[i + 1] - xs[i], 0.22, zs[j + 1] - zs[j]), mat)
wall_with_ports(0.11, -2.0, 2.0, 0.0, 2.6, PORTS, wallm)
ship.box("obs_glass", (PORTS[1][0], 0.05, PORTS[1][1]), (PORTS[1][2], 0.008, PORTS[1][3]), glass_m)
for p in PORTS:                                                # steel shutters hooked up above each port
    ship.box("shutter", (p[0], -0.03, p[1] + p[3] / 2 + 0.17), (p[2] + 0.06, 0.012, 0.3), steel)
lens, lever = projector((0.0, -0.62, 0.0))
# spare reels and a rewind bench along the side wall
bench = I.tex("old_wood_floor", 1.2, name="bench", fallback=(0.3, 0.2, 0.12))
ship.box("bench", (1.55, -1.6, 0.85), (0.6, 2.2, 0.05), bench)
for yy in (-2.4, -1.0):
    ship.box("bench_leg", (1.55, yy, 0.42), (0.5, 0.05, 0.84), steel)
for k in range(4):
    film_can("bench_can", (1.6, -2.3 + k * 0.42, 0.875), R.uniform(-1, 1))
I.bulb("booth_bulb", (-0.9, -1.6, 2.25), energy=8 if SHOT == 3 else 2.5, cord=0.35)

# auditorium (front wall of the booth is the auditorium's back wall, upper level)
AZ = -4.2; SCREEN_Y = 17.0; SW = 7.2
red = I.tex("velour_velvet", 2.0, tint=(0.55, 0.06, 0.05), name="velvet", fallback=(0.3, 0.03, 0.03))
plaster = I.tex("painted_plaster_wall", 0.8, tint=(0.35, 0.12, 0.08), name="aud_wall", fallback=(0.25, 0.08, 0.06))
carpet = I.tex("dirty_carpet", 1.0, tint=(0.4, 0.15, 0.1), name="carpet", fallback=(0.2, 0.06, 0.05))
ship.box("aud_floor", (0, 8.5, AZ - 0.05), (14, 17.5, 0.1), carpet)
ship.box("aud_backwall_lower", (0, 0.3, AZ / 2), (14, 0.2, -AZ), plaster)
for sg in (1, -1):
    ship.box("aud_side", (sg * 7.0, 8.5, AZ + 4.0), (0.2, 17.5, 8.0), plaster)
ship.box("aud_ceiling", (0, 8.5, AZ + 8.0), (14, 17.5, 0.2), plaster)
ship.box("aud_back_upper_l", (-4.5, 0.3, 1.3), (5, 0.2, 2.6), plaster)
ship.box("aud_back_upper_r", (4.5, 0.3, 1.3), (5, 0.2, 2.6), plaster)
ship.box("aud_back_top", (0, 0.3, 3.3), (14, 0.2, 1.4), plaster)
screen_m = I.principled("screen", (0.82, 0.82, 0.8), 0.9)
SC_Z = AZ + 3.6
ship.box("screen", (0, SCREEN_Y, SC_Z), (SW, 0.02, SW / 1.6), screen_m)
ship.box("masking_top", (0, SCREEN_Y - 0.05, SC_Z + SW / 3.2 + 0.25), (SW + 1.2, 0.04, 0.5), blackm)
ship.box("masking_bot", (0, SCREEN_Y - 0.05, SC_Z - SW / 3.2 - 0.2), (SW + 1.2, 0.04, 0.4), blackm)
for sg in (1, -1):                                            # stage curtains drawn back, heavy folds
    for k in range(9):
        ship.cyl("curtain", (sg * (SW / 2 + 0.35 + k * 0.13), SCREEN_Y - 0.3 + 0.08 * (k % 2), AZ),
                 (sg * (SW / 2 + 0.35 + k * 0.13), SCREEN_Y - 0.3 + 0.08 * (k % 2), AZ + 7.6), 0.1, mat=red, verts=12)
ship.box("stage", (0, SCREEN_Y - 1.2, AZ + 0.45), (13, 2.4, 0.9), I.tex("old_wood_floor", 0.8, name="stage", fallback=(0.2, 0.12, 0.07)))
# seats: rows rising gently toward the back
seat_frame = I.principled("seat_frame", (0.05, 0.04, 0.03), 0.5, 0.6)
for row in range(12):
    y = 2.2 + row * 1.05; z = AZ + max(0, (11 - row)) * 0.12
    ship.box("riser", (0, y, z - 0.06), (12.5, 1.05, 0.12), carpet)
    for s in range(-11, 12):
        if s == 0:
            continue                                            # centre aisle
        x = s * 0.56 - (0.28 if s > 0 else -0.28) * 0
        ship.box("seat_back", (x, y + 0.25, z + 0.62), (0.5, 0.09, 0.62), red, rot=(math.radians(-8), 0, 0), bevel=0.02)
        ship.box("seat_cush", (x, y + 0.02, z + 0.42), (0.48, 0.42, 0.1), red, rot=(math.radians(70), 0, 0), bevel=0.02)
        ship.box("arm", (x + 0.27, y + 0.05, z + 0.55), (0.05, 0.42, 0.05), seat_frame)
# wall sconces, dead; one exit sign glow for depth
for sg in (1, -1):
    for yy in (4, 9, 14):
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.12, location=(sg * 6.85, yy, AZ + 4.5)); s_ = bpy.context.active_object
        s_.scale = (0.5, 1, 1.4); s_.data.materials.append(I.principled("sconce", (0.5, 0.4, 0.3), 0.3, 0.6))
exit_m = I.principled("exit", (0.1, 0.4, 0.1), 0.4, emit=(0.15, 0.9, 0.25), estr=8)
ship.box("exit_sign", (6.88, 15.5, AZ + 2.6), (0.04, 0.5, 0.18), exit_m)

target = Vector((0, SCREEN_Y, SC_Z))
projection(lens, target, energy=float(os.environ.get("PROJ", "60000")))
if not os.environ.get("NOHAZE"): I.haze((0, 5.0 if SHOT != 4 else 3.6, AZ + 4), (13.8, 10.4 if SHOT != 4 else 7.6, 8), density=0.026, color=(0.88, 0.9, 0.95), aniso=0.6)
if not os.environ.get("NOHAZE") and SHOT != 4: I.haze((0, 13.6, AZ + 4), (13.8, 6.8, 8), density=0.007, color=(0.88, 0.9, 0.95), aniso=0.6)
for yy in (4.0, 9.0, 14.0):
    I.area("house", (0, yy - 1.5, AZ + 7.7), (0, yy - 3, AZ), 30 if SHOT == 4 else 9, (1.0, 0.72, 0.45), 2.5)   # house lights at a glimmer
I.haze((0, -1.6, 1.3), (3.9, 3.1, 2.6), density=0.012, color=(0.95, 0.9, 0.85), aniso=0.4)
# the screen's own spill back into the room (light bounced from the card) is computed by Cycles; a faint bounce fill:
I.area("screen_bounce", (0, SCREEN_Y - 2, SC_Z), (0, 0.3, 0.5), 90, (0.75, 0.85, 0.45), 6)

if SHOT == 2:
    def pose2(pj, h, Mi):
        P.stand(h, lean=10, weight="L", twist=-6)
        P.head(h, pitch=20, yaw=12)
        P.hand_reach(h, "L", Mi @ (lever + Vector((-0.02, 0, -0.07))), elbow=(0.6, 0.6, -0.6))
        h.aim("wrist.L", (Mi.to_3x3() @ Vector((0.25, 0.1, 1))).normalized()); P.grip(h, "L", 0.85)
        P.arm_down(h, "R", out=0.1, fwd=0.12, bend=22); P.rest_hand(h, "R")
        pj.lids(0.4); pj.brow_knit(0.6)
        return {}
    M = I.yaw(I.facing((1, 0.12)), (-0.66, -0.45, 0))
    projectionist(pose2, M, lens + Vector((0, -0.4, 0.1)))
    I.area("rim", (-1.5, 0.3, 2.3), (-0.6, -0.4, 1.4), 12, (0.7, 0.8, 1.0), 0.8)
    I.area("beard_rim", (0.1, -1.1, 1.7), (-0.6, -0.45, 1.45), 6, (1.0, 0.75, 0.5), 0.3)   # lamphouse kick on the jaw
    C.camera(Vector((-0.5, -2.05, 1.5)), Vector((-0.5, -0.45, 1.35)), lens=30, fstop=2.8)   # side-lit profile from his right
    C.finish(I.out("f5_k2_booth"), cine={"exposure": 0.05, "sat": 1.05})
elif SHOT == 3:
    def pose3(pj, h, Mi):
        P.stand(h, lean=12, weight="R")
        P.head(h, pitch=8)
        P.hand_reach(h, "L", Mi @ Vector((PORTS[1][0] - 0.2, -0.05, PORTS[1][1] - 0.2)), elbow=(0.7, 0.2, -0.7))
        h.aim("wrist.L", (Mi.to_3x3() @ Vector((0.0, 1, -0.15))).normalized()); P.rest_hand(h, "L", curl=30)
        P.arm_down(h, "R", out=0.12, fwd=0.05, bend=15); P.rest_hand(h, "R")
        pj.lids(0.2)
        return {}
    M = I.yaw(I.facing((0.15, 1)), (PORTS[1][0] - 0.05, -0.36, 0))
    projectionist(pose3, M, target)
    # reverse angle from the seats: the beam pours out of the port over the rows, his silhouette in the window
    C.camera(Vector((1.2, 6.5, AZ + 2.6)), Vector((-0.45, 0.2, 1.35)), lens=60, fstop=4.0, focus=8.6)
    C.finish(I.out("f5_k3_port"), cine={"exposure": 0.15, "sat": 1.05})
elif SHOT == 4:
    # final hold: from the back rows; no person needed (no hand in frame), the booth port glows above behind camera
    C.camera(Vector((0.05, 7.6, AZ + 2.0)), Vector((0.0, SCREEN_Y, SC_Z + 1.2)), lens=24, fstop=5.6, focus=14)
    exec(open(os.environ["DBG"]).read()) if os.environ.get("DBG") else None
    C.finish(I.out("f5_k4_logo"), cine={"exposure": 0.15, "sat": 1.1})
