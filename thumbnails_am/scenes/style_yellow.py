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
clay = mat("mannequin", (0.78, 0.74, 0.62), 0.75)          # pale cream matte clay

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
    for r in range(16):
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
# papers on the wet floor
for i in range(40):
    S.box("paper", (rng.uniform(-2.4, 2.2), rng.uniform(-4.5, 1.0), 0.002), (0.18, 0.13, 0.001), grey, rot=(0, 0, rng.uniform(0, 6.3)))

# ---------------------------------------------------------------- three faceless thieves, crouching away with bags
ACC_M = mat("accent", (0.75, 0.02, 0.02), 0.45, coat=0.4) if ACC == "red" else mat("accent", (0.92, 0.92, 0.9), 0.4, coat=0.4)
for i, (x, y, hd) in enumerate(((0.0, -0.9, -150), (-0.9, -1.8, -160), (0.8, -2.2, -145))):
    pv, arm_, ms_, hand_ = crew.thief(Vector((x, y, 0)), hd, jitter=5, seed=i + 7, mat=clay, name=f"thief{i}")
    for o in bpy.data.objects:
        if o.name.startswith(f"thief{i}_beanie"):
            o.data.materials.clear(); o.data.materials.append(clay)
    bag = PR.holdall(f"bag{i}", (0.3, 0.3, 0.28), full=0.9, open_=False)
    side = Matrix.Rotation(math.radians(hd), 3, 'Z') @ Vector((-0.16, 0, 0))
    bag.location = Vector((hand_.x, hand_.y, max(0.0, hand_.z - 0.32))) + side
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
OLIVE = (0.55, 0.5, 0.08)
T.area("fill", (0, -1.0, 7.0), (0, -1.0, 0), 7.0, float(E("FILL_E", "260")), color=OLIVE, size_y=9)
T.area("moon", (-4, -6, 5), (0, -1, 0.5), 3.0, float(E("MOON_E", "300")), color=OLIVE)
# the vault interior glows yellow and rims the thieves from behind
T.area("vault_light", (0, 2.9, 3.0), (0, 2.9, 0), 2.4, float(E("VAULT_E", "700")), color=YEL, size_y=2.4)
rim = bpy.data.lights.new("rim", 'SPOT'); rim.energy = float(E("RIM_E", "2200")); rim.spot_size = math.radians(70); rim.spot_blend = 0.5
rim.color = YEL; rim.shadow_soft_size = 0.4
ro = bpy.data.objects.new("rim", rim); col.objects.link(ro); ro.location = (0.3, 1.4, 2.0)
ro.rotation_euler = (Vector((0, -2.0, 0.6)) - ro.location).to_track_quat('-Z', 'Y').to_euler()
# the accent: a tight spot on the evidence bag
acc_col = (1.0, 0.15, 0.1) if ACC == "red" else (1.0, 1.0, 1.0)
asp = bpy.data.lights.new("accent", 'SPOT'); asp.energy = float(E("ACC_E", "120")); asp.spot_size = math.radians(14); asp.spot_blend = 0.4
asp.color = acc_col; ao_ = bpy.data.objects.new("accent", asp); col.objects.link(ao_)
ao_.location = ACC_AT + Vector((-0.6, -1.2, 2.6)); ao_.rotation_euler = (ACC_AT - ao_.location).to_track_quat('-Z', 'Y').to_euler()

# ---------------------------------------------------------------- camera: high 3/4 overhead wide
EL = math.radians(float(E("CAM_EL", "42"))); DIST = float(E("DIST", "9.5")); AZ = math.radians(float(E("CAM_AZ", "-118")))
tgt = Vector((0.0, -0.6, 0.6))
cam = tgt + Vector((math.cos(AZ) * math.cos(EL), math.sin(AZ) * math.cos(EL), math.sin(EL))) * DIST
C.camera(cam, tgt, lens=float(E("LENS", "35")))

# grade: very dark, heavy vignette (house grade with the vignette pushed)
import grade as G
G.add_grade(sc, bloom=0.25, vignette=float(E("VIG", "0.85")), look="cinematic",
            cine={"exposure": float(E("EXPO", "-0.2")), "contrast": 1.15, "sat": 1.1, "knee": 0.6, "span": 1.4})
out = E("OUT", os.path.join(T.OUTDIR, f"style_yellow_{ACC}.png"))
sc.render.filepath = out; os.makedirs(os.path.dirname(out), exist_ok=True)
bpy.ops.render.render(write_still=True); print("RENDERED", out)
