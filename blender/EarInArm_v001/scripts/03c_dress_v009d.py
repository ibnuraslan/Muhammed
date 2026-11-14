# v009d dressing fixes (client review of v010). Runs on work/anim.blend after 03b_hands_v009b.py, before 04_camera_fx.py.
# 1. Surgeon: the body under the scrubs was deleted by the MPFB clothes mask, so wherever the sleeve gaps from the arm the
#    hollow inside showed as a dark "torn hole". The mask is off and those body faces wear the scrub material instead.
# 2. Nurse: crop top and jeans -> scrubs. Her torso/legs wear the scrub material (the crop-top gap reads as scrubs), her hands
#    wear the nitrile glove, and she gets the same cap and mask as the surgeon, bound to her head bone.
import bpy, sys
from mathutils import Vector, Matrix
OUT = sys.argv[sys.argv.index("--") + 1]
OB = bpy.data.objects

def dom_bone(body, rig):
    gi = {g.index: g.name for g in body.vertex_groups}; bones = {b.name for b in rig.data.bones}; out = {}
    for v in body.data.vertices:
        gs = [g for g in v.groups if gi.get(g.group) in bones]
        out[v.index] = gi[max(gs, key=lambda g: g.weight).group].lower() if gs else ""
    return out
def in_group(body, name, thr=0.5):
    g = body.vertex_groups.get(name)
    if not g: return set()
    return {v.index for v in body.data.vertices for x in v.groups if x.group == g.index and x.weight > thr}
def add_mat(ob, mat):
    if mat.name not in [m.name for m in ob.data.materials if m]: ob.data.materials.append(mat)
    return [m.name for m in ob.data.materials].index(mat.name)

# ---------------------------------------------------------------- 1. surgeon: no hollow under the scrubs
SB = OB["Surgeon.body"]; scrub = OB["Surgeon.male_casualsuit06"].data.materials[0]
under = in_group(SB, "Delete.male_casualsuit06")
mi = add_mat(SB, scrub)
for p in SB.data.polygons:
    if all(i in under for i in p.vertices): p.material_index = mi
SB.modifiers["Delete.male_casualsuit06"].show_render = False; SB.modifiers["Delete.male_casualsuit06"].show_viewport = False

# ---------------------------------------------------------------- 2. nurse in scrubs, gloves, cap and mask
N = OB["Nurse"]; NB = OB["Nurse.body"]; NS = OB["Nurse.female_sportsuit01"]
scrubN = scrub.copy(); scrubN.name = "NurseScrubBody"
glove = bpy.data.materials["NitrileGlove"]
ms = add_mat(NB, scrubN); mg = add_mat(NB, glove)
db = dom_bone(NB, N)
SCRUB_K = ("spine", "pelvis", "upperleg", "lowerleg", "clavicle", "shoulder", "breast", "pectoral", "upperarm01", "glute", "root")
HAND_K = ("wrist", "metacarpal", "finger", "hand", "thumb", "palm")
for p in NB.data.polygons:
    ks = [db[i] for i in p.vertices]
    if all(any(k in b for k in HAND_K) for b in ks): p.material_index = mg
    elif all(any(k in b for k in SCRUB_K) for b in ks) and not any("neck" in b or "head" in b for b in ks): p.material_index = ms
for m in NB.modifiers:
    if m.type == 'MASK' and "sportsuit" in m.name: m.show_render = False; m.show_viewport = False
# the sports top/jeans themselves take the scrub colour (sleeves and cloth shape stay)
NS.data.materials[0] = scrub
# cap and mask: copies of the surgeon's, re-bound to the nurse's head bone at the same offset from the head
def rebind(src_name, new_name, offset):
    """copy of the surgeon's cap/mask on the nurse's head bone, placed like attach_bone() in 03_animate.py"""
    src = OB[src_name]; o = src.copy(); o.data = src.data.copy(); o.name = new_name
    for c in src.users_collection: c.objects.link(o)
    BN = N.data.bones; ks = BN["head"].length / OB["Surgeon"].data.bones["head"].length
    M_rest = Matrix.Translation(BN["head"].head_local + Vector(offset) * ks) @ Matrix.Scale(ks, 4)
    o.parent = N; o.parent_type = 'BONE'; o.parent_bone = "head"; o.matrix_parent_inverse = Matrix.Identity(4)
    o.matrix_basis = (Matrix.Translation((0, BN["head"].length, 0)).inverted() @ BN["head"].matrix_local.inverted()) @ M_rest
    return o
print("CAP_PARENT", OB["Surgeon_Cap"].parent and OB["Surgeon_Cap"].parent.name, OB["Surgeon_Cap"].parent_type, OB["Surgeon_Cap"].parent_bone)
cap = rebind("Surgeon_Cap", "Nurse_Cap", (0, 0.01, 0.12)); mk = rebind("Surgeon_Mask", "Nurse_Mask", (0, 0.008, -0.025))
for o in [c for c in N.children if c.type == 'MESH' and any(k in c.name.lower() for k in ("bob", "hair", "short0", "long0", "ponytail", "braid", "afro"))]:
    o.hide_render = True; o.hide_viewport = True   # the cap covers her hair
# masks stand off the face: the nose and lips pushed through the thin shell when the head pitched down (client: "no mask")
for nm in ("Surgeon_Mask", "Nurse_Mask"):
    OB[nm].data.transform(Matrix.Scale(1.1, 4))
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("DRESS_DONE")
