"""Append generic MPFB (CC0) characters from earlier studio packages, strip animation, refit Natasha to a 14-year-old
body (fresh MPFB teen shape, her hair/eyes/clothes carried over with Surface Deform), recolour clothes, eye fix.
blender -b --factory-startup --python 01_chars.py -- work/chars.blend"""
import bpy, sys
from mathutils import Vector, Matrix
BL = "/home/user/Muhammed/blender/"
SRC = [("StanleyCup_v009", "Woman", "Nat"),
       ("DonationBin_v009", "Woman", "Mom"),
       ("EscapeArtist_v010", "Father", "Dad"),
       ("EscapeArtist_v010", "Prisoner", "SearchA"),
       ("PopeShot_v012", "Shooter", "SearchB"),
       ("EscapeArtist_v010", "PrisonerOld", "Killer"),
       ("EscapeArtist_v010", "Guard", "CopA"),
       ("GoatOwner_v009", "OffA", "CopB"),
       ("GoatOwner_v009", "OffB", "CopF"),
       ("EscapeArtist_v010", "Judge", "Pros"),
       ("PopeShot_v012", "GuardA", "JudgeB"),
       ("SpeakWithoutSight_v006", "Teacher", "ExA"),
       ("ToddlerWell_v008", "Teen", "ExB"),
       ("WaterTubes_v006", "NeighbourA", "ExC"),
       ("HeadsetBullet_v008", "Teen", "ExD"),
       ("ToddlerWell_v008", "Mother", "ExE")]
out = sys.argv[sys.argv.index("--") + 1]
for o in list(bpy.data.objects): bpy.data.objects.remove(o)
for path, rig, new in SRC:
    with bpy.data.libraries.load(BL + f"{path}/{path}_60fps.blend", link=False) as (src, dst):
        dst.objects = [n for n in src.objects if n in (rig, rig + "_rig") or n.startswith(rig + ".")]
    objs = [k for k in dst.objects if k is not None]
    print("LOADED", path, rig, [(k.name, k.type) for k in objs if k.type != "MESH"])
    r = next(k for k in objs if k.type == "ARMATURE" and k.name.split(".")[0] in (rig, rig + "_rig"))
    kids = [k for k in objs if k.type == 'MESH' and (k.parent is r or any(m.type == 'ARMATURE' and m.object is r for m in k.modifiers))]
    for k in objs:
        if k is not r and k not in kids: bpy.data.objects.remove(k)
    bpy.context.scene.collection.objects.link(r)
    for k in kids:
        bpy.context.scene.collection.objects.link(k)
        if k.parent is not r: mw = k.matrix_world.copy(); k.parent = r
    r.name = new; r.data.name = new
    for k in kids:
        base = k.name.split(".")[1]
        base = base or k.name
        if base.startswith("body"): base = "body"
        if base.startswith("high-poly"): base = "high-poly"
        k.name = new + "." + base
    print("APPENDED", new, sorted(k.name for k in kids))
for o in list(bpy.data.objects):
    if o.users_scene == () or "torch_" in o.name: bpy.data.objects.remove(o)
for o in bpy.data.objects:
    o.animation_data_clear()
    if o.type == 'MESH' and o.data.shape_keys: o.data.shape_keys.animation_data_clear()
    for c in list(o.constraints): o.constraints.remove(c)
    if o.type == 'ARMATURE':
        for pb in o.pose.bones:
            for c in list(pb.constraints): pb.constraints.remove(c)
            pb.location = (0, 0, 0); pb.rotation_mode = 'QUATERNION'; pb.rotation_quaternion = (1, 0, 0, 0); pb.scale = (1, 1, 1)
        o.location = (0, 0, 0); o.rotation_euler = (0, 0, 0); o.scale = (1, 1, 1); o.parent = None
    o.hide_render = False; o.hide_viewport = False
    if o.type == 'MESH' and o.parent and o.parent.type == 'ARMATURE':
        o.matrix_parent_inverse.identity(); o.location = (0, 0, 0); o.rotation_euler = (0, 0, 0); o.scale = (1, 1, 1)
for o in bpy.data.objects:   # unhide modifiers keyed off etc
    for m in getattr(o, "modifiers", []): m.show_render = m.show_render

# ---- Natasha at 14: a fresh MPFB teen body shape; hair, eyes, brows, lashes, teeth and clothes refitted with Surface Deform
from bl_ext.user_default.mpfb.services.humanservice import HumanService
info = HumanService._create_default_human_info_dict(); info["name"] = "Kid"
info["phenotype"] = {"gender": 0.0, "age": 0.30, "muscle": 0.5, "weight": 0.5, "proportions": 0.6, "height": 0.62,
                     "cupsize": 0.4, "firmness": 0.5, "race": {"african": 0.0, "caucasian": 0.95, "asian": 0.05}}
info["rig"] = "default"
for k in ("eyes", "eyebrows", "eyelashes", "teeth", "tongue", "hair"): info[k] = ""
info["clothes"] = []; info["skin_mhmat"] = ""
st = HumanService.get_default_deserialization_settings(); st["subdiv_levels"] = 0
HumanService.deserialize_from_dict(info, st)
KID = bpy.data.objects["Kid"]; KB = bpy.data.objects["Kid.body"]
OLD = bpy.data.objects["Nat"]; OB = bpy.data.objects["Nat.body"]
KID.location = OLD.location = (0, 0, 0); bpy.context.view_layer.update()
for m in KB.modifiers: m.show_viewport = False
bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get()
kco = [v.co.copy() for v in KB.evaluated_get(dg).to_mesh().vertices]
n0 = len(OB.data.vertices)
_d = sorted((kco[i] - OB.data.vertices[i].co).length for i in range(0, n0, 7))
print("MAPCHECK", len(kco), n0, "median", round(_d[len(_d)//2], 3), "p95", round(_d[int(len(_d)*.95)], 3))
kco = kco[:n0]
masks = [m for m in OB.modifiers if m.type == 'MASK']
for m in masks: m.show_viewport = False; m.show_render = False
proxies = [c for c in OLD.children if c.type == 'MESH' and c is not OB]
for px in proxies:
    for m in px.modifiers:
        if m.type == 'SUBSURF': m.show_viewport = False
    sd = px.modifiers.new("Refit", 'SURFACE_DEFORM'); sd.target = OB
    while px.modifiers.find("Refit") > 0: px.modifiers.move(px.modifiers.find("Refit"), px.modifiers.find("Refit") - 1)
    with bpy.context.temp_override(object=px, active_object=px):
        bpy.ops.object.surfacedeform_bind(modifier="Refit")
if not OB.data.shape_keys: OB.shape_key_add(name="Basis", from_mix=False)
for kb in OB.data.shape_keys.key_blocks: kb.value = 0.0
ck = OB.shape_key_add(name="Teen14", from_mix=False)
for i, c in enumerate(kco): ck.data[i].co = c
ck.value = 1.0
bpy.context.view_layer.update()
for px in proxies:
    if px.data.shape_keys:
        with bpy.context.temp_override(object=px, active_object=px, selected_objects=[px]):
            bpy.ops.object.shape_key_remove(all=True, apply_mix=True)
    with bpy.context.temp_override(object=px, active_object=px):
        bpy.ops.object.modifier_apply(modifier="Refit")
    for m in px.modifiers:
        if m.type == 'SUBSURF': m.show_viewport = True
for m in masks: m.show_viewport = True; m.show_render = True
for ch in list(OLD.children):
    mw = ch.matrix_world.copy(); ch.parent = KID; ch.matrix_world = mw
    for m in ch.modifiers:
        if m.type == 'ARMATURE': m.object = KID
bpy.data.objects.remove(KB); bpy.data.objects.remove(OLD)
KID.name = "Nat"; KID.data.name = "Nat"
print("TEEN height", round(max(c.z for c in kco), 3))
bpy.ops.wm.save_as_mainfile(filepath=out, compress=True)
