"""Seldom intro 7: DARKROOM (14 s).
Red safelight. A photographer develops a print from a roll found in a dead man's camera. Out of the white paper
rises a photograph of a sign painted on a night brick wall: the official Seldom art (a colour print).

SHOT=1  wide: the darkroom under the safelight, enlarger glowing, he slides the paper into the developer with tongs
SHOT=2  medium, side-lit red: he rocks the tray and stares into it
SHOT=3  top-down on the tray: the image rising through the developer, his tongs and arm in frame
SHOT=4  logo close-up / final hold: the dripping print pinned on the drying line under the white lamp
"""
import os, sys, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C
C.reset()
import bpy
from mathutils import Vector, Matrix
import ship, ph, poses as P, human as H, briggs as BR
import intro_common as I

sc = I.setup(spp=48)
SHOT = I.SHOT
R = random.Random(7)
PHOTO = os.path.join(C.HERE, "..", "assets", "seldom_sign_photo.png")

# ----------------------------------------------------------------------------- room
wallm = I.tex("painted_plaster_wall", 0.7, tint=(0.32, 0.32, 0.3), name="dr_wall", fallback=(0.2, 0.2, 0.2))
floorm = I.tex("dirty_tiles" if False else "floor_tiles_02", 1.0, tint=(0.6, 0.6, 0.6), name="dr_floor", fallback=(0.2, 0.2, 0.2))
bench_m = I.tex("old_wood_floor", 1.3, tint=(0.55, 0.45, 0.38), name="bench_top", fallback=(0.25, 0.18, 0.12))
steel = I.principled("sink_steel", (0.5, 0.5, 0.5), 0.3, 1.0)
enamel = I.principled("tray_enamel", (0.85, 0.85, 0.82), 0.15)
black = I.principled("enl_black", (0.02, 0.02, 0.02), 0.45, 0.3)
brown_glass = bpy.data.materials.new("brown_glass"); brown_glass.use_nodes = True
bg = brown_glass.node_tree.nodes["Principled BSDF"]; bg.inputs["Transmission Weight"].default_value = 0.9
bg.inputs["Base Color"].default_value = (0.35, 0.15, 0.04, 1); bg.inputs["Roughness"].default_value = 0.08

RX, RY, RZ = 1.9, 1.6, 2.5
ship.box("floor", (0, 0, -0.02), (2 * RX, 2 * RY, 0.04), floorm)
ship.box("wall_back", (0, RY, RZ / 2), (2 * RX, 0.06, RZ), wallm)
ship.box("wall_l", (-RX, 0, RZ / 2), (0.06, 2 * RY, RZ), wallm)
ship.box("wall_r", (RX, 0, RZ / 2), (0.06, 2 * RY, RZ), wallm)
ship.box("ceil", (0, 0, RZ), (2 * RX, 2 * RY, 0.06), wallm)

# wet bench along the back wall: the sink with three trays (developer, stop, fix)
BENCH_Z = 0.9
ship.box("wet_bench", (0.3, RY - 0.35, BENCH_Z - 0.03), (2.6, 0.7, 0.06), bench_m)
for xx in (-0.95, 1.55):
    ship.box("bench_leg", (xx, RY - 0.35, (BENCH_Z - 0.06) / 2), (0.06, 0.6, BENCH_Z - 0.06), bench_m)
ship.box("sink_floor", (0.3, RY - 0.36, BENCH_Z + 0.005), (2.3, 0.6, 0.01), steel)
for sg in (1, -1):
    ship.box("sink_lip", (0.3 + sg * 1.16, RY - 0.36, BENCH_Z + 0.06), (0.02, 0.62, 0.12), steel)
ship.box("sink_front", (0.3, RY - 0.67, BENCH_Z + 0.06), (2.34, 0.02, 0.12), steel)
ship.cyl("tap", (0.3, RY - 0.06, BENCH_Z + 0.35), (0.3, RY - 0.25, BENCH_Z + 0.35), 0.012, mat=steel, verts=12)
ship.cyl("tap_riser", (0.3, RY - 0.06, BENCH_Z), (0.3, RY - 0.06, BENCH_Z + 0.36), 0.014, mat=steel, verts=12)

TRAY_W, TRAY_D = 0.42, 0.34
TRAYS = [(-0.4, "dev"), (0.22, "stop"), (0.84, "fix")]


def tray(cx, cy, tag, liquid_tint=(0.9, 0.88, 0.75)):
    z0 = BENCH_Z + 0.012
    ship.box(f"tray_{tag}_base", (cx, cy, z0 + 0.003), (TRAY_W, TRAY_D, 0.006), enamel, bevel=0.003)
    for sx, sy, dx, dy in ((1, 0, 0.008, TRAY_D), (-1, 0, 0.008, TRAY_D), (0, 1, TRAY_W, 0.008), (0, -1, TRAY_W, 0.008)):
        ship.box(f"tray_{tag}_wall", (cx + sx * TRAY_W / 2, cy + sy * TRAY_D / 2, z0 + 0.03), (dx, dy, 0.06), enamel, bevel=0.002)
    # the liquid: a still surface with a gentle rocking wave (glass-like, slightly tinted)
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=60, y_subdivisions=50, size=1, location=(cx, cy, z0 + 0.028))
    lq = bpy.context.active_object; lq.name = f"liquid_{tag}"; lq.scale = (TRAY_W - 0.012, TRAY_D - 0.012, 1)
    wv = lq.modifiers.new("ripple", 'WAVE'); wv.height = 0.0012; wv.width = 0.04; wv.speed = 0.0; wv.start_position_x = -0.3
    wv.use_normal = False
    m = bpy.data.materials.new(f"liquid_{tag}"); m.use_nodes = True; p = m.node_tree.nodes["Principled BSDF"]
    p.inputs["Transmission Weight"].default_value = 1.0; p.inputs["Roughness"].default_value = 0.02; p.inputs["IOR"].default_value = 1.34
    p.inputs["Base Color"].default_value = (*liquid_tint, 1)
    # shadow rays pass the thin liquid layer (no refractive caustics in the render settings)
    N = m.node_tree.nodes; Lk = m.node_tree.links
    lp = N.new("ShaderNodeLightPath"); tr = N.new("ShaderNodeBsdfTransparent"); mx = N.new("ShaderNodeMixShader")
    Lk.new(lp.outputs["Is Shadow Ray"], mx.inputs[0]); Lk.new(p.outputs[0], mx.inputs[1]); Lk.new(tr.outputs[0], mx.inputs[2])
    Lk.new(mx.outputs[0], N["Material Output"].inputs["Surface"])
    lq.data.materials.append(m); bpy.ops.object.shade_smooth()
    return z0


for cx, tag in TRAYS:
    tray(cx, RY - 0.36, tag)


def print_paper(name, center, size, develop=1.0, rot=(0, 0, 0), border=0.05, wet=1.0, curl=0.0):
    """Fibre paper with the photograph; develop 0..1 brings the image up out of white (density curve)."""
    w, hgt = size
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=24, y_subdivisions=18, size=1, location=center, rotation=rot)
    o = bpy.context.active_object; o.name = name; o.scale = (w, hgt, 1); bpy.ops.object.transform_apply(scale=True)
    if curl:
        b = o.modifiers.new("curl", 'SIMPLE_DEFORM'); b.deform_method = 'BEND'; b.angle = curl; b.deform_axis = 'X'
    m = bpy.data.materials.new(name); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links
    p = N["Principled BSDF"]; p.inputs["Roughness"].default_value = 0.08 if wet else 0.35
    p.inputs["Coat Weight"].default_value = 0.6 * wet; p.inputs["Coat Roughness"].default_value = 0.03
    uv = N.new("ShaderNodeUVMap")
    mp = N.new("ShaderNodeMapping"); mp.inputs["Location"].default_value = (-border / w, -border / hgt, 0)
    mp.inputs["Scale"].default_value = (1 / (1 - 2 * border / w), 1 / (1 - 2 * border / hgt), 1)
    L.new(uv.outputs[0], mp.inputs[0])
    im = N.new("ShaderNodeTexImage"); im.image = bpy.data.images.load(PHOTO, check_existing=True); im.extension = 'CLIP'
    L.new(mp.outputs[0], im.inputs[0])
    paper = (0.86, 0.85, 0.8, 1)
    # inside the border: paper * mix(1, image, develop); outside the image: plain paper
    dv = N.new("ShaderNodeMix"); dv.data_type = 'RGBA'; dv.inputs[0].default_value = develop
    dv.inputs[6].default_value = (1, 1, 1, 1); L.new(im.outputs["Color"], dv.inputs[7])
    inside = N.new("ShaderNodeMix"); inside.data_type = 'RGBA'
    L.new(im.outputs["Alpha"], inside.inputs[0]); inside.inputs[6].default_value = (1, 1, 1, 1); L.new(dv.outputs[2], inside.inputs[7])
    mul = N.new("ShaderNodeMix"); mul.data_type = 'RGBA'; mul.blend_type = 'MULTIPLY'; mul.inputs[0].default_value = 1
    mul.inputs[6].default_value = paper; L.new(inside.outputs[2], mul.inputs[7])
    L.new(mul.outputs[2], p.inputs["Base Color"])
    o.data.materials.append(m)
    return o


# dry bench on the left wall: the enlarger
DRY_X = -RX + 0.38
ship.box("dry_bench", (DRY_X, 0.25, BENCH_Z - 0.03), (0.7, 1.6, 0.06), bench_m)
ship.box("dry_bench_front", (DRY_X + 0.33, 0.25, (BENCH_Z - 0.06) / 2), (0.04, 1.6, BENCH_Z - 0.06), bench_m)
ship.box("enl_base", (DRY_X, 0.5, BENCH_Z + 0.015), (0.5, 0.6, 0.03), black)
ship.box("easel", (DRY_X + 0.02, 0.45, BENCH_Z + 0.04), (0.3, 0.38, 0.02), I.principled("easel", (0.75, 0.7, 0.2), 0.4))
ship.cyl("enl_column", (DRY_X - 0.18, 0.72, BENCH_Z + 0.03), (DRY_X - 0.18, 0.72, BENCH_Z + 1.15), 0.025, mat=steel, verts=16)
ship.box("enl_head", (DRY_X, 0.6, BENCH_Z + 0.78), (0.22, 0.28, 0.24), black, bevel=0.01)
ship.box("enl_lamphouse", (DRY_X, 0.6, BENCH_Z + 0.97), (0.18, 0.2, 0.14), black, bevel=0.02)
ship.cyl("enl_bellows", (DRY_X, 0.56, BENCH_Z + 0.66), (DRY_X, 0.56, BENCH_Z + 0.56), 0.06, mat=black, verts=24)
ship.cyl("enl_lens", (DRY_X, 0.56, BENCH_Z + 0.56), (DRY_X, 0.56, BENCH_Z + 0.52), 0.03, mat=steel, verts=24)
glowm = I.principled("enl_glow", (1, 0.9, 0.7), 0.5, emit=(1.0, 0.85, 0.6), estr=25)
for k in range(4):
    ship.box("enl_vent", (DRY_X + 0.091, 0.53 + k * 0.04, BENCH_Z + 0.98), (0.004, 0.018, 0.08), glowm)
I.point("enl_leak", (DRY_X + 0.12, 0.6, BENCH_Z + 0.98), 0.6, (1.0, 0.8, 0.55), 0.02)

# bottles on a shelf, a timer, a print drying line across the room
ship.box("shelf", (0.3, RY - 0.12, BENCH_Z + 0.72), (2.4, 0.22, 0.025), bench_m)
for k in range(8):
    x = -0.75 + k * 0.28 + R.uniform(-0.03, 0.03); hgt = R.uniform(0.18, 0.28)
    ship.cyl("bottle", (x, RY - 0.12, BENCH_Z + 0.735), (x, RY - 0.12, BENCH_Z + 0.735 + hgt), 0.045, mat=brown_glass, verts=20)
    ship.cyl("cap", (x, RY - 0.12, BENCH_Z + 0.735 + hgt), (x, RY - 0.12, BENCH_Z + 0.76 + hgt), 0.02, mat=black, verts=12)
clock_face = I.principled("timer_face", (0.85, 0.82, 0.7), 0.4, emit=(0.2, 1.0, 0.4), estr=0.02)
ship.cyl("timer", (1.35, RY - 0.03, BENCH_Z + 0.42), (1.35, RY - 0.06, BENCH_Z + 0.42), 0.09, mat=black, verts=32)
ship.cyl("timer_face", (1.35, RY - 0.061, BENCH_Z + 0.42), (1.35, RY - 0.063, BENCH_Z + 0.42), 0.08, mat=clock_face, verts=32)
LINE_Z = 2.05
line_m = I.principled("line", (0.6, 0.58, 0.5), 0.8)
ship.cyl("drying_line", (-RX, 0.1, LINE_Z), (RX, 0.1, LINE_Z), 0.0018, mat=line_m, verts=6)
pin_m = I.tex("old_wood_floor", 6, name="pin_wood", fallback=(0.55, 0.42, 0.28))


def pegged_print(x, develop, name, wet=1.0):
    pw, ph_ = 0.24, 0.18
    o = print_paper(name, (x, 0.1, LINE_Z - 0.01 - ph_ / 2), (pw, ph_), develop=develop,
                    rot=(math.radians(90), 0, 0), border=0.012, wet=wet)
    for dx in (-0.08, 0.08):
        ship.box("peg", (x + dx, 0.1, LINE_Z - 0.012), (0.012, 0.012, 0.07), pin_m)
    return o


for k, x in enumerate((-1.2, -0.85, 0.95)):
    pegged_print(x, 0.0 if k == 1 else 0.15, f"old_print_{k}", wet=0.0)

# ----------------------------------------------------------------------------- light: the safelight
safe_glass = I.principled("safelight_glass", (0.6, 0.02, 0.0), 0.3, emit=(1.0, 0.04, 0.0), estr=18)
ship.box("safelight_box", (-0.6, RY - 0.08, 2.05), (0.3, 0.12, 0.22), black, bevel=0.01)
ship.box("safelight_filter", (-0.6, RY - 0.142, 2.05), (0.26, 0.004, 0.18), safe_glass)
safe = I.area("safelight", (-0.6, RY - 0.16, 2.05), (0.0, RY - 0.6, 0.9), 55, (1.0, 0.05, 0.0), 0.25)
safe.data.shape = 'RECTANGLE'; safe.data.size = 0.26; safe.data.size_y = 0.18
I.area("red_bounce", (0.8, -0.8, 2.3), (0.3, 0.6, 1.0), 4, (1.0, 0.08, 0.02), 1.5)
I.haze((0, 0, RZ / 2), (2 * RX - 0.1, 2 * RY - 0.1, RZ - 0.05), density=0.03, color=(1, 0.95, 0.9), aniso=0.4)


def photographer(pose, M, look):
    ph_ = BR.Briggs(name="Photographer", wet=0.0)
    h = ph_.h; Mi = M.inverted()
    extra = pose(ph_, h, Mi) or {}
    ph_.finish(look_at=look, place=M, density=float(os.environ.get("HAIR", "0.7")))
    return ph_, extra


def tongs(tip, grip, mat=None):
    """Bamboo print tongs: two slim slats with rubber tips, from his fingers down to the paper's edge."""
    mat = mat or I.principled("bamboo", (0.6, 0.45, 0.22), 0.5)
    rub = I.principled("tong_rubber", (0.04, 0.035, 0.03), 0.6)
    tip = Vector(tip); grip = Vector(grip); d = (tip - grip).normalized(); side = d.cross(Vector((0, 0, 1))).normalized() * 0.006
    for s in (1, -1):
        ship.cyl("tong", grip + side * s, tip + side * s * 0.4 - d * 0.02, 0.0045, mat=mat, verts=8)
        ship.cyl("tong_tip", tip + side * s * 0.4 - d * 0.02, tip + side * s * 0.4, 0.006, mat=rub, verts=8)


DEV = Vector((TRAYS[0][0], RY - 0.36, BENCH_Z + 0.04))
if SHOT in (1, 2, 3):
    develop = {1: 0.0, 2: 0.25, 3: 0.72}[SHOT]
    pr = print_paper("print_in_tray", DEV + Vector((0.0, 0.0, -0.016)), (0.3, 0.22), develop=develop, border=0.015, wet=1.0)

    def pose_tray(ph_, h, Mi):
        P.stand(h, lean=22, weight="L", twist=-4)
        P.head(h, pitch=36, yaw=-4)
        # right hand: the tongs, tips at the near edge of the print in the developer
        grip_w = DEV + Vector((0.06, -0.24, 0.17))
        P.hand_reach(h, "R", Mi @ grip_w, elbow=(-0.6, 0.6, -0.5))
        h.aim("wrist.R", (Mi.to_3x3() @ Vector((0.1, 0.8, -0.6))).normalized()); P.grip(h, "R", 0.7)
        # left hand: rocking the developer tray by its corner
        corner = Vector((DEV.x - TRAY_W / 2 - 0.02, DEV.y - TRAY_D / 2 + 0.03, BENCH_Z + 0.075))
        P.hand_reach(h, "L", Mi @ corner, elbow=(0.7, 0.4, -0.6))
        h.aim("wrist.L", (Mi.to_3x3() @ Vector((0.3, 0.8, -0.45))).normalized()); P.grip(h, "L", 0.55)
        ph_.lids(0.55); ph_.brow_knit(0.5)
        return dict(grip_w=grip_w)
    M = I.yaw(180, (DEV.x - 0.02, DEV.y - 0.72, 0))
    ph_, ex = photographer(pose_tray, M, DEV)
    tongs(DEV + Vector((0.03, -0.09, -0.005)), ex["grip_w"] + Vector((0, 0.02, -0.02)))
    if SHOT == 1:
        C.camera(Vector((1.55, -1.35, 1.75)), Vector((-0.35, 0.95, 1.05)), lens=22, fstop=2.8)
        C.finish(I.out("f7_k1_darkroom"), cine={"exposure": 0.45, "sat": 1.05})
    elif SHOT == 2:
        C.camera(Vector((-1.45, 0.75, 1.42)), Vector((-0.45, 0.68, 1.42)), lens=35, fstop=2.4)
        C.finish(I.out("f7_k2_rock"), cine={"exposure": 0.5, "sat": 1.05})
    else:
        C.camera(DEV + Vector((0.42, -0.95, 1.05)), DEV + Vector((0.0, -0.02, -0.01)), lens=32, fstop=4.0)   # over his right shoulder
        C.finish(I.out("f7_k3_tray"), cine={"exposure": 0.55, "sat": 1.05})
else:
    # the hold: he has pegged the print on the line and switched on the white bench lamp; it drips
    X = 0.25
    pr = pegged_print(X, 1.0, "the_print", wet=1.0)
    water = bpy.data.materials.new("drip"); water.use_nodes = True; wp = water.node_tree.nodes["Principled BSDF"]
    wp.inputs["Transmission Weight"].default_value = 1; wp.inputs["Roughness"].default_value = 0.02; wp.inputs["IOR"].default_value = 1.33
    for k in range(3):
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.0035, location=(X - 0.06 + k * 0.06, 0.1, LINE_Z - 0.2 - 0.002 - k * 0.01))
        d = bpy.context.active_object; d.scale = (1, 1, 1.6); d.data.materials.append(water)
    def pose_line(ph_, h, Mi):
        P.stand(h, lean=0, weight="R")
        P.head(h, pitch=-12, yaw=6)
        # his right hand still at the peg he has just pressed shut
        peg = Vector((X + 0.08, 0.1, LINE_Z - 0.02))
        P.hand_reach(h, "R", Mi @ (peg + Vector((0.03, -0.05, -0.06))), elbow=(-0.5, 0.4, -0.8))
        h.aim("wrist.R", (Mi.to_3x3() @ Vector((-0.2, 0.5, 0.85))).normalized()); P.grip(h, "R", 0.6)
        P.arm_down(h, "L", out=0.12, fwd=0.05, bend=15); P.rest_hand(h, "L")
        ph_.lids(0.2)
        return {}
    M = I.yaw(0, (X + 0.32, -0.42, 0))      # as rendered: he turns from the line toward the lamp
    photographer(pose_line, M, Vector((X, 0.1, LINE_Z - 0.1)))
    lamp = I.spot("white_lamp", (X - 0.6, -0.9, 2.3), (X, 0.1, LINE_Z - 0.1), 90, (1.0, 0.92, 0.8), size_deg=40, blend=0.5, radius=0.04)
    C.camera(Vector((X - 0.75, -1.45, LINE_Z - 0.32)), Vector((X + 0.12, 0.05, LINE_Z - 0.2)), lens=32, fstop=3.2)
    C.finish(I.out("f7_k4_logo"), cine={"exposure": 0.3, "sat": 1.1})
