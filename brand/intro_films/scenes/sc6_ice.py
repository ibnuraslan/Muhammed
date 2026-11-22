"""Seldom intro 6: ICE STATION (12 s).
Polar night, a blizzard. A researcher follows his head torch to a shape under the snow, digs, and brushes the last
snow from a steel drum: the official Seldom art is hand-painted on its rusted flank, frosted at the edges.

SHOT=1  wide: the head torch bobbing toward camera through the drifts (0-3 s)
SHOT=2  medium low: kneeling, chopping at the crust with an ice axe, snow streaming through the beam (3-6.5 s)
SHOT=3  close over his shoulder: the gloved hand brushing the drum's flank, paint showing (6.5-9.5 s)
SHOT=4  logo close-up / final hold: the painted drum in the steady beam, his breath clouding (9.5-12 s)
"""
import os, sys, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C
C.reset()
import numpy as np
import bpy, bmesh
from mathutils import Vector, Matrix, noise
import ship, ph, poses as P, human as H, deveau as D
import intro_common as I

sc = I.setup(spp=48)
SHOT = I.SHOT
R = random.Random(6)
DRUM = Vector((0.0, 0.0, 0.0))        # drum base centre (it stands on the old camp floor, buried to ~0.45 m)
DR, DH = 0.29, 0.88

# ----------------------------------------------------------------------------- snowfield
snow = I.tex("snow_02", 0.5, name="snow", fallback=(0.8, 0.85, 0.92), rough=0.6)
p = snow.node_tree.nodes["Principled BSDF"]
p.inputs["Subsurface Weight"].default_value = 0.25; p.inputs["Subsurface Radius"].default_value = (0.4, 0.6, 1.0)
p.inputs["Subsurface Scale"].default_value = 0.05


def drift_height(x, y):
    """Wind-carved drifts, plus the mound over the drum with the hole he has dug on the camera side (-Y)."""
    v = Vector((x * 0.18, y * 0.12, 0.3))
    z = 0.35 * noise.noise(v) + 0.12 * noise.noise(Vector((x * 0.9, y * 0.6, 2.0))) + 0.02 * noise.noise(Vector((x * 6, y * 6, 5)))
    d = math.hypot(x - DRUM.x, (y - DRUM.y) * 1.1)
    mound = (0.48 if SHOT != 1 else 0.62) * math.exp(-(d / (0.75 if SHOT != 1 else 1.05)) ** 2)   # shot 1: still buried
    # the dug hole: snow cleared from the drum's front, down to the drum's mid height
    hole = math.exp(-((x - DRUM.x) / 0.55) ** 2 - ((y - DRUM.y + 0.45) / 0.5) ** 2) if SHOT != 1 else 0.0
    return z + mound * (1 - 0.85 * hole) - 0.25 * hole + 0.25


def snowfield(size=60, n=260):
    V, F = [], []
    for j in range(n + 1):
        for i in range(n + 1):
            u = (i / n - 0.5); v = (j / n - 0.5)
            x = math.copysign(abs(u) ** 1.6, u) * size; y = math.copysign(abs(v) ** 1.6, v) * size   # denser near the drum
            V.append((x, y, drift_height(x, y)))
    for j in range(n):
        for i in range(n):
            a = j * (n + 1) + i; F.append([a, a + 1, a + n + 2, a + n + 1])
    o = ship.mesh_obj("snowfield", V, F, snow, smooth=True)
    return o


snowfield()

# ----------------------------------------------------------------------------- the drum
rust = I.tex("rusty_metal_03", 2.5, name="drum_rust", fallback=(0.3, 0.15, 0.07), rough=0.65)
paint_old = I.grunge(I.principled("drum_paint", (0.06, 0.12, 0.1), 0.6, 0.2), 8, 0.6, (0.4, 0.2, 0.1))


def drum(c):
    # body as a UV'd cylinder: U runs round the drum, V up it
    nseg, nz = 96, 24
    V, F, UV = [], [], []
    for k in range(nz + 1):
        z = c.z + DH * k / nz
        for i in range(nseg + 1):
            a = 2 * math.pi * i / nseg
            rr = DR + 0.008 * (abs(math.cos(math.pi * (k / nz) * 3)) > 0.97)     # rolling hoops
            V.append((c.x + rr * math.sin(a), c.y - rr * math.cos(a), z))
    for k in range(nz):
        for i in range(nseg):
            a = k * (nseg + 1) + i; F.append([a, a + 1, a + nseg + 2, a + nseg + 1])
    body = ship.mesh_obj("drum_body", V, F, None, smooth=True)
    uvl = body.data.uv_layers.new(name="UV")
    for poly in body.data.polygons:
        for li, vi in zip(poly.loop_indices, poly.vertices):
            i = vi % (nseg + 1); k = vi // (nseg + 1)
            uvl.data[li].uv = (i / nseg, k / nz)
    # paint: the old green drum paint mostly rusted through
    m = I.tex("rusty_metal_03", 2.5, name="drum_mat", fallback=(0.3, 0.15, 0.07), rough=0.65)
    N = m.node_tree.nodes; L = m.node_tree.links; pr = N["Principled BSDF"]
    base = pr.inputs["Base Color"].links[0].from_socket
    nz_ = N.new("ShaderNodeTexNoise"); nz_.inputs["Scale"].default_value = 7; nz_.inputs["Detail"].default_value = 12
    mr = N.new("ShaderNodeMapRange"); mr.inputs[1].default_value = 0.55; mr.inputs[2].default_value = 0.6
    L.new(nz_.outputs["Fac"], mr.inputs[0])
    mx = N.new("ShaderNodeMix"); mx.data_type = 'RGBA'; L.new(mr.outputs[0], mx.inputs[0]); L.new(base, mx.inputs[6])
    mx.inputs[7].default_value = (0.03, 0.04, 0.025, 1); L.new(mx.outputs[2], pr.inputs["Base Color"])
    body.data.materials.append(m)
    ship.cyl("drum_top", c + Vector((0, 0, DH)), c + Vector((0, 0, DH + 0.012)), DR + 0.006, mat=m, verts=64)
    ship.cyl("bung", c + Vector((0.12, 0.05, DH + 0.012)), c + Vector((0.12, 0.05, DH + 0.03)), 0.03, mat=rust, verts=16)
    # the painted logo: a thin layer of brush paint on the flank facing -Y (the art spans 110 deg of the drum)
    span = math.radians(112); w = DR * span; hgt = w / I.LOGO_AR
    zc = c.z + 0.735; nu, nv = 80, 20
    V, F, UV = [], [], []
    for k in range(nv + 1):
        for i in range(nu + 1):
            a = -span / 2 + span * i / nu; rr = DR + 0.0016
            V.append((c.x + rr * math.sin(a), c.y - rr * math.cos(a), zc - hgt / 2 + hgt * k / nv))
    for k in range(nv):
        for i in range(nu):
            a = k * (nu + 1) + i; F.append([a, a + 1, a + nu + 2, a + nu + 1])
    dec = ship.mesh_obj("drum_logo", V, F, None, smooth=True)
    uvl = dec.data.uv_layers.new(name="UV")
    for poly in dec.data.polygons:
        for li, vi in zip(poly.loop_indices, poly.vertices):
            uvl.data[li].uv = ((vi % (nu + 1)) / nu, (vi // (nu + 1)) / nv)
    lm = bpy.data.materials.new("drum_logo_paint"); lm.use_nodes = True
    Nn = lm.node_tree.nodes; Ll = lm.node_tree.links; pp = Nn["Principled BSDF"]
    pp.inputs["Roughness"].default_value = 0.62; pp.inputs["Base Color"].default_value = (0.1, 0.1, 0.1, 1)
    im = I.logo_layer(lm, kind="paint", wear=0.25)
    # paint layer: transparent outside the art (and where the paint has flaked), so the drum shows through
    mixs = Nn.new("ShaderNodeMixShader"); tr = Nn.new("ShaderNodeBsdfTransparent")
    fl = Nn.new("ShaderNodeTexNoise"); fl.inputs["Scale"].default_value = 26; fl.inputs["Detail"].default_value = 14
    fr = Nn.new("ShaderNodeMapRange"); fr.inputs[1].default_value = 0.27; fr.inputs[2].default_value = 0.31
    Ll.new(fl.outputs["Fac"], fr.inputs[0])
    am = Nn.new("ShaderNodeMath"); am.operation = 'MULTIPLY'; Ll.new(im.outputs["Alpha"], am.inputs[0]); Ll.new(fr.outputs[0], am.inputs[1])
    Ll.new(am.outputs[0], mixs.inputs[0]); Ll.new(tr.outputs[0], mixs.inputs[1]); Ll.new(pp.outputs[0], mixs.inputs[2])
    Ll.new(mixs.outputs[0], Nn["Material Output"].inputs["Surface"])
    # brush texture: paint ridges
    bn = Nn.new("ShaderNodeTexWave"); bn.wave_type = 'BANDS'; bn.inputs["Scale"].default_value = 60; bn.inputs["Distortion"].default_value = 6
    bb = Nn.new("ShaderNodeBump"); bb.inputs["Strength"].default_value = 0.08; Ll.new(bn.outputs["Fac"], bb.inputs["Height"]); Ll.new(bb.outputs[0], pp.inputs["Normal"])
    dec.data.materials.append(lm)
    # frost: rime on the drum's edges and in the hoops (a white crust shell, densest near the top and the snow line)
    fm = bpy.data.materials.new("rime"); fm.use_nodes = True
    Nf = fm.node_tree.nodes; Lf = fm.node_tree.links; pf = Nf["Principled BSDF"]
    pf.inputs["Base Color"].default_value = (0.88, 0.92, 0.98, 1); pf.inputs["Roughness"].default_value = 0.5
    pf.inputs["Subsurface Weight"].default_value = 0.3
    gz = Nf.new("ShaderNodeTexCoord"); sz = Nf.new("ShaderNodeSeparateXYZ"); Lf.new(gz.outputs["Object"], sz.inputs[0])
    edge = Nf.new("ShaderNodeMapRange"); edge.inputs[1].default_value = c.z + 0.6; edge.inputs[2].default_value = c.z + DH
    edge.inputs[3].default_value = 0.0; edge.inputs[4].default_value = 1.0
    Lf.new(sz.outputs["Z"], edge.inputs[0])
    low = Nf.new("ShaderNodeMapRange"); low.inputs[1].default_value = c.z + 0.42; low.inputs[2].default_value = c.z + 0.3
    Lf.new(sz.outputs["Z"], low.inputs[0])
    mxm = Nf.new("ShaderNodeMath"); mxm.operation = 'MAXIMUM'; Lf.new(edge.outputs[0], mxm.inputs[0]); Lf.new(low.outputs[0], mxm.inputs[1])
    fn = Nf.new("ShaderNodeTexNoise"); fn.inputs["Scale"].default_value = 40; fn.inputs["Detail"].default_value = 14
    add = Nf.new("ShaderNodeMath"); add.operation = 'MULTIPLY_ADD'; add.inputs[2].default_value = -0.55
    Lf.new(fn.outputs["Fac"], add.inputs[0]); Lf.new(mxm.outputs[0], add.inputs[1])
    cl = Nf.new("ShaderNodeMapRange"); cl.inputs[1].default_value = 0.0; cl.inputs[2].default_value = 0.06
    Lf.new(add.outputs[0], cl.inputs[0])
    mixf = Nf.new("ShaderNodeMixShader"); trf = Nf.new("ShaderNodeBsdfTransparent")
    Lf.new(cl.outputs[0], mixf.inputs[0]); Lf.new(trf.outputs[0], mixf.inputs[1]); Lf.new(pf.outputs[0], mixf.inputs[2])
    Lf.new(mixf.outputs[0], Nf["Material Output"].inputs["Surface"])
    rime = body.copy(); rime.data = body.data.copy(); rime.name = "drum_rime"; bpy.context.scene.collection.objects.link(rime)
    rime.data.materials.clear(); rime.data.materials.append(fm)
    s = rime.modifiers.new("out", 'DISPLACE'); s.strength = 0.0032; s.mid_level = 0.0
    return body


if SHOT != 1:
    drum(DRUM)
# chunks of crust he has chopped out, and the snow he has thrown aside
crust = I.tex("snow_02", 1.2, name="crust", fallback=(0.85, 0.88, 0.95), rough=0.5)
for k in range(14 if SHOT != 1 else 0):
    a = R.uniform(-2.2, -0.9); d = R.uniform(0.55, 1.1)
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=R.uniform(0.04, 0.11),
                                          location=(DRUM.x + d * math.cos(a) * 1.2, DRUM.y + d * math.sin(a), 0.0))
    ch = bpy.context.active_object; ch.scale = (1, R.uniform(0.6, 1), R.uniform(0.4, 0.7))
    ch.location.z = drift_height(ch.location.x, ch.location.y) + 0.01
    ch.data.materials.append(crust)
# the old camp: a broken tent pole and a sledge runner poking out of the drifts (nobody ever camped here)
wood = I.tex("old_wood_floor", 0.8, name="sledge", fallback=(0.25, 0.17, 0.1))
ship.cyl("pole", (1.6, 1.4, drift_height(1.6, 1.4) - 0.2), (1.75, 1.3, drift_height(1.6, 1.4) + 1.1), 0.02, mat=wood, verts=10)
ship.box("runner", (-1.7, 1.1, drift_height(-1.7, 1.1) + 0.05), (1.4, 0.06, 0.08), wood, rot=(0.1, 0.25, 0.4))

# ----------------------------------------------------------------------------- light: polar night
w = bpy.context.scene.world
if w is None:
    w = bpy.data.worlds.new("World"); bpy.context.scene.world = w
w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (0.03, 0.05, 0.1, 1)
w.node_tree.nodes["Background"].inputs[1].default_value = 1.0
moon = bpy.data.lights.new("moon", 'SUN'); moon.energy = 0.25; moon.color = (0.55, 0.68, 1.0); moon.angle = math.radians(2)
mo = bpy.data.objects.new("moon", moon); sc.collection.objects.link(mo); mo.rotation_euler = (math.radians(62), 0, math.radians(150))
snow_m = I.principled("flake", (0.92, 0.95, 1.0), 0.4)
I.haze((0, 0, 3), (40, 40, 7), density=0.022, color=(0.8, 0.86, 0.98), aniso=0.55, noise_scale=0.7)


# ----------------------------------------------------------------------------- the researcher
def researcher(pose, M):
    rs = D.Deveau(name="Researcher", years=38, wet=0.15, cap=True)
    h = rs.h
    extra = pose(rs, h, M) or {}
    if extra.get("dz"):
        M = Matrix.Translation((0, 0, extra["dz"])) @ M
    fh, fwd = I.head_frame(h)
    rs.place_M = M
    rs.finish(look_at=extra.get("look"), place=M, density=float(os.environ.get("HAIR", "0.7")))
    I.glove_hands(rs)
    # head torch on an elastic strap over the cap: lamp body + lens glow + the beam
    W = M @ fh; F = (M.to_3x3() @ fwd).normalized()
    lamp_m = I.principled("torch_body", (0.03, 0.03, 0.03), 0.4)
    ship.cyl("headtorch", W - F * 0.01, W + F * 0.035, 0.022, mat=lamp_m, verts=20)
    ship.cyl("headtorch_lens", W + F * 0.035, W + F * 0.038, 0.018,
             mat=I.principled("torch_lens", (1, 1, 1), 0.05, emit=(0.85, 0.92, 1.0), estr=40), verts=20)
    aim = extra.get("aim", W + F * 6)
    beam = I.spot("headtorch_beam", W + F * 0.09, aim, float(os.environ.get("TORCH", "420")), (0.82, 0.9, 1.0),
                  size_deg=24, blend=0.45, radius=0.008)
    return rs, W, F


if SHOT == 1:
    def pose1(rs, h, M0):
        bob = H.pose_walk(h, 0.18, stride=22, arm_swing=14)
        P.head(h, pitch=14)
        for b in ("spine03", "spine02"):
            h.rot(b, (1, 0, 0), 9)                             # head down into the wind
        return dict(bob=bob, aim=Vector((1.5, 4.3, 0)) + Vector((-1.4, -4.5, 1.25)))
    rs_M = I.yaw(I.facing((-0.35, -1)), (1.5, 4.3, 0))
    rs_M = Matrix.Translation((0, 0, drift_height(1.5, 4.3) - 0.06)) @ rs_M
    researcher(pose1, rs_M)
    I.streaks("blizzard", (0.5, 2.5, 1.5), (9, 9, 3.5), 9000, wind=(1.0, -0.35, -0.3), length=(0.05, 0.14), mat=snow_m, seed=1)
    C.camera(Vector((-1.3, -2.3, 0.85)), Vector((1.1, 4.0, 1.1)), lens=32, fstop=2.8)
    C.finish(I.out("f6_k1_blizzard"), cine={"exposure": 0.25, "sat": 1.0})
elif SHOT in (2, 3):
    def pose2(rs, h, M0):
        dz = I.kneel(h, down="R", lean=26)
        Mi = (Matrix.Translation((0, 0, dz)) @ M0).inverted()
        P.head(h, pitch=30)
        if SHOT == 2:
            # right hand high on the ice axe, mid-swing; left hand braced on his raised knee
            P.hand_reach(h, "R", Vector((-0.12, -0.42, 1.05 - dz)), elbow=(-0.8, 0.4, 0.2))
            rs.axe_grip = Vector((-0.12, -0.42, 1.05 - dz))
            h.aim("wrist.R", (0.1, -0.3, 1)); P.grip(h, "R", 1.0)
            knee = h.bone_tail("upperleg02.L")
            P.hand_reach(h, "L", knee + Vector((0.0, -0.02, 0.07)), elbow=(0.8, 0.3, -0.2))
            h.aim("wrist.L", (0.1, -1, -0.5)); P.rest_hand(h, "L", curl=35)
        else:
            # right hand flat on the drum's flank, brushing; left hand on the drum's rim
            P.hand_reach(h, "R", Mi @ (DRUM + Vector((0.12, -DR - 0.06, 0.74))), elbow=(-0.7, 0.4, -0.5))
            h.aim("wrist.R", (Mi.to_3x3() @ Vector((0.6, 0.35, -0.7))).normalized()); P.rest_hand(h, "R", curl=12)
            P.hand_reach(h, "L", Mi @ (DRUM + Vector((-0.2, -0.17, DH + 0.06))), elbow=(0.8, 0.2, -0.5))
            h.aim("wrist.L", (Mi.to_3x3() @ Vector((0.2, 0.7, -0.6))).normalized()); P.grip(h, "L", 0.5)
        rs.lids(0.45)
        return dict(dz=dz, look=DRUM + Vector((0, -DR, 0.735)), aim=DRUM + Vector((0.0, -DR, 0.73)))
    base = DRUM + Vector((0.05, -1.02, 0))
    M = I.yaw(180, (base.x, base.y, drift_height(base.x, base.y)))
    rs, W, F = researcher(pose2, M)
    if SHOT == 2:
        # the ice axe in his right fist, pick end down toward the crust
        axe_m = I.principled("axe_steel", (0.35, 0.35, 0.36), 0.35, 1.0); shaft = I.tex("old_wood_floor", 3, name="shaft", fallback=(0.4, 0.28, 0.15))
        g = rs.place_M @ rs.axe_grip
        top = g + Vector((0.0, -0.05, 0.12)); bot = g + Vector((0.05, -0.55, -0.5))
        ship.cyl("axe_shaft", top + Vector((0, 0, 0.0)), bot, 0.016, mat=shaft, verts=14)
        hd = top + (top - bot).normalized() * 0.02
        ship.box("axe_head", hd, (0.025, 0.3, 0.03), axe_m, rot=(0.6, 0, 0))
        I.streaks("blizzard", (0.0, -1.0, 1.0), (5, 5, 2.4), 7000, wind=(1.0, -0.2, -0.25), length=(0.04, 0.11), mat=snow_m, seed=2)
        C.camera(Vector((-1.75, -2.6, 0.42)), Vector((-0.05, -0.75, 0.72)), lens=30, fstop=2.8)
        C.finish(I.out("f6_k2_dig"), cine={"exposure": 0.25, "sat": 1.0})
    else:
        I.streaks("blizzard", (0.0, -1.0, 1.0), (4, 4, 2.4), 4500, wind=(1.0, -0.2, -0.25), length=(0.04, 0.1), mat=snow_m, seed=3)
        C.camera(Vector((0.85, -1.7, 1.42)), DRUM + Vector((-0.05, -DR, 0.7)), lens=38, fstop=2.8)
        C.finish(I.out("f6_k3_brush"), cine={"exposure": 0.3, "sat": 1.0})
elif SHOT == 4:
    # final hold: locked off on the drum; his knee and gloved hand at frame edge, breath clouding in the beam
    def pose4(rs, h, M0):
        dz = I.kneel(h, down="R", lean=10)
        for b in ("spine03", "spine02"):
            h.rot(b, (1, 0, 0), -6)                            # sits back on his heels
        P.head(h, pitch=18)
        P.arm_down(h, "R", out=0.16, fwd=0.02, bend=20); P.rest_hand(h, "R", curl=30)
        knee = h.bone_tail("upperleg02.L")
        P.hand_reach(h, "L", knee + Vector((0.0, -0.02, 0.07)), elbow=(0.8, 0.3, -0.2))
        h.aim("wrist.L", (0.1, -1, -0.5)); P.rest_hand(h, "L", curl=35)
        return dict(dz=dz, look=DRUM + Vector((0, -DR, 0.735)), aim=DRUM + Vector((0.0, -DR, 0.735)))
    base = DRUM + Vector((-0.72, -0.78, 0))
    M = I.yaw(I.facing((0.62, 0.78)), (base.x, base.y, drift_height(base.x, base.y)))
    rs, W, F = researcher(pose4, M)
    mouth = W + F * 0.06 + Vector((0, 0, -0.1))
    I.haze(mouth + F * 0.14, (0.3, 0.28, 0.2), density=0.9, color=(0.95, 0.97, 1.0), noise_scale=9)
    I.streaks("blizzard", (0.0, -0.8, 0.9), (3, 3, 2), 1800, wind=(1.0, -0.2, -0.25), length=(0.03, 0.07), mat=snow_m, seed=4)
    if os.environ.get("OVERVIEW"):
        C.camera(Vector((2.6, -3.2, 2.2)), DRUM + Vector((0, -0.6, 0.5)), lens=28)
        print("TORCH AT", W, "FWD", F)
        C.finish(I.out("f6_overview"), cine={"exposure": 0.35, "sat": 1.05}); sys.exit(0)
    C.camera(Vector((0.18, -1.65, 0.86)), DRUM + Vector((-0.04, -DR, 0.71)), lens=40, fstop=4.0)
    C.finish(I.out("f6_k4_logo"), cine={"exposure": 0.35, "sat": 1.05})
