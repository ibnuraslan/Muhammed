"""Style look-test: the reference films' grammar (3D diorama floating in a black void, faceless pale matte mannequins,
high 3/4 overhead wide, very dark, ONE world tint, rim light on the figures, one accent on the key evidence), with the
world tinted Seldom YELLOW instead of navy: near-black olive shadows, dark mustard midtones, #E3FF00 highlights.
Scene: Antwerp cold open. The vault corridor at night as a diorama: the round vault door hanging open, a bank of forced
boxes, wet floor; three faceless thieves crouch away from the vault with bags. The key evidence (the lead thief's bag of
loot) gets the one accent: ACCENT=red or ACCENT=white.
Fast preset: 960x540, 16 spp, OIDN; upscaled to 1920x1080 afterwards.
    ACCENT=red blender -b --python style_yellow.py"""
import os, sys, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tcommon as T
C = T.use("antwerp")
import bpy
from mathutils import Vector, Matrix
import sets as S, props as PR, ship as SH
import vaultkit as V
import crew
E = os.environ.get
ACC = E("ACCENT", "red")
sc = C.render_setup(samples=int(E("SPP", "16")), noise=0.05, res=(960, 540))
sc.render.resolution_percentage = 100; sc.cycles.samples = int(E("SPP", "16"))
sc.cycles.sample_clamp_indirect = 4.0; sc.cycles.max_bounces = 6
rng = random.Random(3)
col = sc.collection


def mat(name, c, rough=0.6, metal=0.0, coat=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True; p = m.node_tree.nodes["Principled BSDF"]
    p.inputs['Base Color'].default_value = (*c, 1); p.inputs['Roughness'].default_value = rough
    p.inputs['Metallic'].default_value = metal; p.inputs['Coat Weight'].default_value = coat
    return m


# the world is built in neutral greys; the yellow comes from the light (as the refs do with blue)
grey = mat("set_grey", (0.32, 0.31, 0.29), 0.7)
steel = mat("set_steel", (0.4, 0.39, 0.36), 0.35, 0.6)
dark = mat("set_dark", (0.02, 0.02, 0.018), 0.8)
wet = mat("wet_floor", (0.1, 0.1, 0.09), 0.3, coat=1.0)
N_ = wet.node_tree.nodes; L_ = wet.node_tree.links; pw = N_["Principled BSDF"]
nz = N_.new("ShaderNodeTexNoise"); nz.inputs['Scale'].default_value = 1.6; nz.inputs['Detail'].default_value = 6
mr = N_.new("ShaderNodeMapRange"); mr.inputs['From Min'].default_value = 0.45; mr.inputs['From Max'].default_value = 0.6
mr.inputs['To Min'].default_value = 0.02; mr.inputs['To Max'].default_value = 0.5
L_.new(nz.outputs['Fac'], mr.inputs['Value']); L_.new(mr.outputs[0], pw.inputs['Roughness']); L_.new(mr.outputs[0], pw.inputs['Coat Roughness'])
clay = mat("mannequin", (0.86, 0.85, 0.81), 0.72)          # pale near-white matte clay

# ---------------------------------------------------------------- the diorama: a slab of corridor floating in black
FL = S.box("floor", (0, -1.5, -0.1), (6.0, 9.0, 0.2), wet)
S.box("back_wall", (0, 1.6, 1.6), (6.0, 0.9, 3.2), grey)
R = 1.15; DZ = R + 0.1
bpy.ops.mesh.primitive_cylinder_add(vertices=96, radius=R, depth=3, location=(0, 1.6, DZ), rotation=(math.pi / 2, 0, 0))
hole = bpy.context.active_object; hole.hide_render = True; hole.hide_viewport = True
bw = bpy.data.objects["back_wall"]; bo = bw.modifiers.new("hole", "BOOLEAN"); bo.object = hole; bo.operation = 'DIFFERENCE'; bo.solver = 'EXACT'
SH.cyl("jamb", (0, 1.15, DZ), (0, 2.05, DZ), R, mat=steel, verts=96, caps=False).modifiers.new("t", "SOLIDIFY").thickness = 0.05
# inside the vault: a glimpse of forced boxes
CW, RH = 0.18, 0.15
door_t = S._door_mesh(CW, RH, "bd", (steel, steel, dark)); cav_t = S._cavity_mesh(CW, RH, 0.4, "cv", dark)
for c in range(14):
    for r in range(int(E('VROWS', '11'))):
        M = Matrix.Translation((-1.25 + c * CW, 3.6, 0.2 + (r + 0.5) * RH))
        cv = cav_t.copy(); col.objects.link(cv); cv.matrix_world = M
        d = door_t.copy(); col.objects.link(d)
        d.matrix_world = M @ Matrix.Rotation(math.radians(-rng.uniform(70, 160)), 4, 'Z')
S.box("vault_floor", (0, 2.8, -0.05), (3.0, 2.6, 0.1), grey)
# the round door hanging open
leaf = V.vault_door(R - 0.02, steel, steel, dark, face=steel, bolt=steel)
leaf.location = (R + 0.3, 1.13, DZ); leaf.rotation_euler.z = math.radians(118)
# a bank of forced boxes on the corridor's left, open grille gate on the right
for c in range(10):
    for r in range(14):
        M = Matrix.Translation((-2.75, -1.0 - c * CW, 0.2 + (r + 0.5) * RH)) @ Matrix.Rotation(math.pi / 2, 4, 'Z')
        cv = cav_t.copy(); col.objects.link(cv); cv.matrix_world = M
        d = door_t.copy(); col.objects.link(d)
        d.matrix_world = M @ Matrix.Rotation(math.radians(-rng.uniform(70, 150)), 4, 'Z')
for k in range(9):
    S.box("grille_bar", (2.4, -0.2 - k * 0.12, 1.1), (0.03, 0.03, 2.2), steel)
S.box("grille_top", (2.4, -0.68, 2.2), (0.04, 1.1, 0.05), steel)
# corridor detail: pillars, cut-away ceiling beams, caged lamps, a CCTV camera; edges fade to black
for x in (-2.55, 2.55):
    for y in (0.95, -2.2, -5.0):
        S.box("pillar", (x, y, 1.7), (0.4, 0.4, 3.4), grey, bevel=0.02)
for y in (0.95,):
    S.box("beam", (0, y, 3.3), (5.5, 0.3, 0.35), grey, bevel=0.02)
lampm = bpy.data.materials.new("lamp"); lampm.use_nodes = True; LN = lampm.node_tree.nodes; LN.remove(LN["Principled BSDF"])
lem = LN.new("ShaderNodeEmission"); lem.inputs['Color'].default_value = (1.0, 0.6, 0.18, 1); lem.inputs['Strength'].default_value = 25
lampm.node_tree.links.new(lem.outputs[0], LN["Material Output"].inputs['Surface'])
for y in (-0.6, -3.6):
    SH.cyl("lamp_cable", (0, y, 4.5), (0, y, 3.12), 0.006, mat=dark, verts=6)
    SH.cyl("lamp", (0, y, 3.12), (0, y, 3.02), 0.12, mat=lampm, verts=24)
    pl_ = bpy.data.lights.new("lamp_l", 'POINT'); pl_.energy = float(E("LAMP_E", "40")); pl_.color = (1.0, 0.55, 0.16); pl_.shadow_soft_size = 0.1
    po = bpy.data.objects.new("lamp_l", pl_); col.objects.link(po); po.location = (0, y, 2.95)
# CCTV on the left pillar, looking down the corridor
cc = Vector((-2.3, 0.75, 2.9))
S.box("cctv_arm", cc + Vector((0.1, 0, 0)), (0.25, 0.05, 0.05), steel)
cam_body = S.box("cctv_body", cc + Vector((0.32, -0.12, -0.05)), (0.14, 0.3, 0.13), grey, bevel=0.01, rot=(math.radians(-25), 0, math.radians(20)))
SH.cyl("cctv_lens", cc + Vector((0.37, -0.28, -0.12)), cc + Vector((0.39, -0.32, -0.14)), 0.04, mat=dark, verts=16)
led = bpy.data.materials.new("led"); led.use_nodes = True; ln_ = led.node_tree.nodes; ln_.remove(ln_["Principled BSDF"])
le = ln_.new("ShaderNodeEmission"); le.inputs['Color'].default_value = (1, 0.05, 0.02, 1); le.inputs['Strength'].default_value = 30
led.node_tree.links.new(le.outputs[0], ln_["Material Output"].inputs['Surface'])
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.008, location=cc + Vector((0.3, -0.27, -0.03))); bpy.context.active_object.data.materials.append(led)
# the floor and walls fall off into black away from the action (radial darkening in their shading)
for m_ in (wet, grey):
    N2 = m_.node_tree.nodes; L2 = m_.node_tree.links; p2 = N2["Principled BSDF"]
    geo = N2.new("ShaderNodeNewGeometry"); sep = N2.new("ShaderNodeSeparateXYZ"); L2.new(geo.outputs['Position'], sep.inputs[0])
    cx = N2.new("ShaderNodeCombineXYZ"); L2.new(sep.outputs['X'], cx.inputs[0])
    yy = N2.new("ShaderNodeMath"); yy.operation = 'ADD'; yy.inputs[1].default_value = 1.2; L2.new(sep.outputs['Y'], yy.inputs[0])
    L2.new(yy.outputs[0], cx.inputs[1])
    ln2 = N2.new("ShaderNodeVectorMath"); ln2.operation = 'LENGTH'; L2.new(cx.outputs[0], ln2.inputs[0])
    fr = N2.new("ShaderNodeMapRange"); fr.inputs['From Min'].default_value = 2.6; fr.inputs['From Max'].default_value = 4.6
    fr.inputs['To Min'].default_value = 1.0; fr.inputs['To Max'].default_value = 0.0; fr.interpolation_type = 'SMOOTHSTEP'
    L2.new(ln2.outputs['Value'], fr.inputs['Value'])
    src = p2.inputs['Base Color'].links[0].from_socket if p2.inputs['Base Color'].links else None
    mx2 = N2.new("ShaderNodeMix"); mx2.data_type = 'RGBA'; mx2.blend_type = 'MULTIPLY'; L2.new(fr.outputs[0], mx2.inputs['Factor'])
    if src is not None:
        L2.new(src, mx2.inputs[6])
    else:
        mx2.inputs[6].default_value = p2.inputs['Base Color'].default_value
    mx2.inputs[7].default_value = (0, 0, 0, 1)
    # factor 1 near the centre should keep colour: invert
    inv = N2.new("ShaderNodeMath"); inv.operation = 'SUBTRACT'; inv.inputs[0].default_value = 1.0; L2.new(fr.outputs[0], inv.inputs[1])
    L2.new(inv.outputs[0], mx2.inputs['Factor']); L2.new(mx2.outputs[2], p2.inputs['Base Color'])
    sp_ = N2.new("ShaderNodeMath"); sp_.operation = 'MULTIPLY'; L2.new(fr.outputs[0], sp_.inputs[0]); sp_.inputs[1].default_value = 0.5
    L2.new(sp_.outputs[0], p2.inputs['Specular IOR Level'])
# papers on the wet floor
for i in range(40):
    S.box("paper", (rng.uniform(-2.4, 2.2), rng.uniform(-4.5, 1.0), 0.002), (0.18, 0.13, 0.001), grey, rot=(0, 0, rng.uniform(0, 6.3)))

# ---------------------------------------------------------------- three faceless thieves, crouching away with bags
figs = []
CLOTH = dict(jacket=mat("jacket", (0.8, 0.79, 0.75), 0.8), trousers=mat("trousers", (0.74, 0.73, 0.7), 0.8), gloves=mat("gloves", (0.6, 0.59, 0.57), 0.6))
ACC_M = mat("accent", (0.75, 0.02, 0.02), 0.45, coat=0.4) if ACC == "red" else mat("accent", (0.92, 0.92, 0.9), 0.4, coat=0.4)
for i, (x, y, hd) in enumerate(((0.0, -0.9, -150), (-0.9, -1.8, -160), (0.8, -2.2, -145))):
    pv, arm_, ms_, hand_ = crew.thief(Vector((x, y, 0)), hd, jitter=5, seed=i + 7, mat=clay, name=f"thief{i}")
    for cl in crew.add_clothes(ms_[0], CLOTH, name=f"thief{i}"):
        cl.parent = ms_[0].parent; cl.matrix_parent_inverse = ms_[0].matrix_parent_inverse.copy()
    for o in bpy.data.objects:
        if o.name.startswith(f"thief{i}_beanie"):
            o.data.materials.clear(); o.data.materials.append(clay)
    # blank mannequin head: a smooth egg over the face (no nose, no brow), parented to the head bone
    hb = arm_.pose.bones["head_07"]; base = arm_.matrix_world @ hb.head; top = arm_.matrix_world @ arm_.pose.bones["head_end_08"].head
    up = (top - base).normalized(); fwd_ = (arm_.matrix_world.to_3x3() @ Vector((0, -1, 0))).normalized()
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.1, segments=48, ring_count=24, location=base + (top - base) * 0.5 + fwd_ * 0.012)
    hd_ = bpy.context.active_object; hd_.name = f"thief{i}_blankhead"; hd_.scale = (0.98, 1.12, 1.22)
    hd_.rotation_euler = up.to_track_quat('Z', 'Y').to_euler(); hd_.data.materials.append(clay)
    for pl in hd_.data.polygons:
        pl.use_smooth = True
    mw_ = hd_.matrix_world.copy(); hd_.parent = arm_; hd_.parent_type = 'BONE'; hd_.parent_bone = "head_07"
    bpy.context.view_layer.update(); hd_.matrix_world = mw_
    figs.append(pv)
    bag = PR.holdall(f"bag{i}", (0.3, 0.3, 0.28), full=1.0, open_=False); bag.scale = (1.35, 1.35, 1.35)
    side = Matrix.Rotation(math.radians(hd), 3, 'Z') @ Vector((-0.16, 0, 0))
    bag.location = Vector((hand_.x, hand_.y, max(0.0, hand_.z - 0.45))) + side * 1.5
    bag.rotation_euler.z = math.radians(hd + 90)
    bm = ACC_M if i == 0 else clay
    for o in [bag] + list(bag.children_recursive):
        if o.type == 'MESH':
            o.data.materials.clear(); o.data.materials.append(bm)
    if i == 0:
        ACC_AT = bag.location.copy()

# ---------------------------------------------------------------- light: everything yellow; one accent light on the evidence
w = bpy.data.worlds.new("void"); sc.world = w; w.use_nodes = True
w.node_tree.nodes["Background"].inputs['Color'].default_value = (0, 0, 0, 1)
YEL = (0.78, 1.0, 0.0)                       # #E3FF00 (linear)
OLIVE = (1.0, 0.5, 0.1)        # warm amber-gold world fill (shadows go brown-black)
T.area("fill", (0, -1.0, 7.0), (0, -1.0, 0), 7.0, float(E("FILL_E", "260")), color=OLIVE, size_y=9)
T.area("moon", (-4, -6, 5), (0, -1, 0.5), 3.0, float(E("MOON_E", "300")), color=OLIVE)
# the vault interior glows yellow and rims the thieves from behind
T.area("vault_light", (0, 2.9, 3.0), (0, 2.9, 0), 2.4, float(E("VAULT_E", "700")), color=(1.0, 0.82, 0.0), size_y=2.4)
rim = bpy.data.lights.new("rim", 'SPOT'); rim.energy = float(E("RIM_E", "2200")); rim.spot_size = math.radians(70); rim.spot_blend = 0.5
rim.color = (1.0, 0.75, 0.1); rim.shadow_soft_size = 0.4
ro = bpy.data.objects.new("rim", rim); col.objects.link(ro); ro.location = (0.3, 1.4, 2.0)
ro.rotation_euler = (Vector((0, -2.0, 0.6)) - ro.location).to_track_quat('-Z', 'Y').to_euler()
# the figures: a neutral cool-white key (figures only) and a warm orange rim, so the clay stays pale and pops
figc = bpy.data.collections.new("figures"); col.children.link(figc)
for pv in figs:
    for o in [pv] + list(pv.children_recursive):
        if o.type == 'MESH' and figc not in o.users_collection:
            figc.objects.link(o)
for o in bpy.data.objects:
    if "_blankhead" in o.name or "_beanie" in o.name:
        if figc not in o.users_collection:
            figc.objects.link(o)
fk = T.area("fig_key", (-3.0, -5.0, 4.5), (0, -1.5, 0.8), 2.0, float(E("FKEY_E", "220")), color=(0.92, 0.96, 1.0))
fk.data.light_linking if hasattr(fk.data, "light_linking") else None
fk.light_linking.receiver_collection = figc
rim2 = T.area("fig_rim", (1.5, 1.0, 2.2), (0, -1.6, 0.9), 1.0, float(E("FRIM_E", "260")), color=(1.0, 0.55, 0.12))
rim2.light_linking.receiver_collection = figc
# the accent: a tight spot on the evidence bag
acc_col = (1.0, 0.15, 0.1) if ACC == "red" else (1.0, 1.0, 1.0)
asp = bpy.data.lights.new("accent", 'SPOT'); asp.energy = float(E("ACC_E", "120")); asp.spot_size = math.radians(14); asp.spot_blend = 0.4
asp.color = acc_col; ao_ = bpy.data.objects.new("accent", asp); col.objects.link(ao_)
ao_.location = ACC_AT + Vector((-0.6, -1.2, 2.6)); ao_.rotation_euler = (ACC_AT - ao_.location).to_track_quat('-Z', 'Y').to_euler()

# ---------------------------------------------------------------- camera: high 3/4 overhead wide
EL = math.radians(float(E("CAM_EL", "42"))); DIST = float(E("DIST", "9.5")); AZ = math.radians(float(E("CAM_AZ", "-118")))
tgt = Vector((0.0, -0.6, float(E('TGZ', '1.5'))))
cam = tgt + Vector((math.cos(AZ) * math.cos(EL), math.sin(AZ) * math.cos(EL), math.sin(EL))) * DIST
C.camera(cam, tgt, lens=float(E("LENS", "35")))

# grade: very dark, heavy vignette (house grade with the vignette pushed)
import grade as G
G.add_grade(sc, bloom=0.25, vignette=float(E("VIG", "0.85")), look="cinematic",
            cine={"exposure": float(E("EXPO", "-0.2")), "contrast": 1.15, "sat": 1.1, "knee": 0.6, "span": 1.4})
out = E("OUT", os.path.join(T.OUTDIR, f"style_yellow_{ACC}.png"))
sc.render.filepath = out; os.makedirs(os.path.dirname(out), exist_ok=True)
bpy.ops.render.render(write_still=True); print("RENDERED", out)
