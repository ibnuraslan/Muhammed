"""Append generic MPFB (CC0) characters from earlier studio packages (the MakeHuman asset server is unreachable here),
strip their animation, recolour clothes. blender -b --factory-startup --python 01_chars.py -- work/chars.blend"""
import bpy, sys
from mathutils import Vector, Matrix
BL = "/home/user/Muhammed/blender/"
SRC = [("NoPilotPlane_v010/NoPilotPlane_v010_60fps.blend", "PE", "Girl"),
       ("ElectricianPolice_v010/ElectricianPolice_v010_60fps.blend", "Man", "SearchA"),
       ("ElectricianPolice_v010/ElectricianPolice_v010_60fps.blend", "Vendor", "SearchB"),
       ("EscapeArtist_v010/EscapeArtist_v010_60fps.blend", "Father", "SearchC"),
       ("DrunkTrain_v007/DrunkTrain_v007_60fps.blend", "Worker", "Worker")]
out = sys.argv[sys.argv.index("--") + 1]
for o in list(bpy.data.objects): bpy.data.objects.remove(o)
for path, rig, new in SRC:
    with bpy.data.libraries.load(BL + path, link=False) as (src, dst):
        dst.objects = [n for n in src.objects if n.startswith(rig + ".")]
    kids = [k for k in dst.objects if k is not None]
    r = next(k.parent for k in kids if k.parent and k.parent.type == 'ARMATURE')
    for k in kids:
        if k.parent is r: bpy.context.scene.collection.objects.link(k)
        else: bpy.data.objects.remove(k)
    kids = [k for k in r.children]
    bpy.context.scene.collection.objects.link(r)
    old = rig; r.name = new; r.data.name = new
    for k in kids: k.name = new + "." + k.name.split(".")[1]
    print("APPENDED", new, [k.name for k in kids])
for o in list(bpy.data.objects):
    if o.users_scene == () : bpy.data.objects.remove(o)
for o in bpy.data.objects:
    o.animation_data_clear()
    if o.type == 'MESH' and o.data.shape_keys: o.data.shape_keys.animation_data_clear()
    for c in list(o.constraints): o.constraints.remove(c)
    if o.type == 'ARMATURE':
        for pb in o.pose.bones:
            for c in list(pb.constraints): pb.constraints.remove(c)
            pb.location = (0, 0, 0); pb.rotation_mode = 'QUATERNION'; pb.rotation_quaternion = (1, 0, 0, 0); pb.scale = (1, 1, 1)
        o.location = (0, 0, 0); o.rotation_euler = (0, 0, 0)
for o in bpy.data.objects:
    o.hide_render = False; o.hide_viewport = False

# ---- make the girl read as 9 years old (director, Nov 15): a fresh MPFB child body + rig (~1.30 m, child proportions,
# rounder face); her hair, eyes, brows, lashes, teeth and clothes are carried over with Surface Deform onto the new shape.
from bl_ext.user_default.mpfb.services.humanservice import HumanService
info = HumanService._create_default_human_info_dict(); info["name"] = "Kid"
info["phenotype"] = {"gender": 0.0, "age": 0.165, "muscle": 0.5, "weight": 0.55, "proportions": 0.5, "height": 0.58,
                     "cupsize": 0.5, "firmness": 0.5, "race": {"african": 0.9, "caucasian": 0.05, "asian": 0.05}}
info["rig"] = "default"
for k in ("eyes", "eyebrows", "eyelashes", "teeth", "tongue", "hair"): info[k] = ""
info["clothes"] = []; info["skin_mhmat"] = ""
st = HumanService.get_default_deserialization_settings(); st["subdiv_levels"] = 0
HumanService.deserialize_from_dict(info, st)
KID = bpy.data.objects["Kid"]; KB = bpy.data.objects["Kid.body"]
OLD = bpy.data.objects["Girl"]; OB = bpy.data.objects["Girl.body"]
KID.location = OLD.location = (0, 0, 0); bpy.context.view_layer.update()
for m in KB.modifiers: m.show_viewport = False
bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get()
kco = [v.co.copy() for v in KB.evaluated_get(dg).to_mesh().vertices]
assert len(kco) == len(OB.data.vertices), (len(kco), len(OB.data.vertices))
masks = [m for m in OB.modifiers if m.type == 'MASK']
for m in masks: m.show_viewport = False; m.show_render = False
proxies = [c for c in OLD.children if c.type == 'MESH' and c is not OB]
for px in proxies:
    sd = px.modifiers.new("Refit", 'SURFACE_DEFORM'); sd.target = OB
    while px.modifiers.find("Refit") > 0: px.modifiers.move(px.modifiers.find("Refit"), px.modifiers.find("Refit") - 1)
    with bpy.context.temp_override(object=px, active_object=px):
        bpy.ops.object.surfacedeform_bind(modifier="Refit")
for kb in OB.data.shape_keys.key_blocks: kb.value = 0.0
ck = OB.shape_key_add(name="Child9", from_mix=False)
for i, c in enumerate(kco): ck.data[i].co = c
ck.value = 1.0
bpy.context.view_layer.update()
for px in proxies:
    with bpy.context.temp_override(object=px, active_object=px):
        bpy.ops.object.modifier_apply(modifier="Refit")
for m in masks: m.show_viewport = True; m.show_render = True
# child clothes: the long-sleeved casual suit from an existing child character (BelugaRescue SpecC), refitted the same way
with bpy.data.libraries.load(BL + "BelugaRescue_v008/BelugaRescue_v008_60fps.blend", link=False) as (src, dst):
    dst.objects = [n for n in src.objects if n in ("SpecC.body", "SpecC.female_casualsuit01")]
SCB = next(o for o in dst.objects if o.name.startswith('SpecC.body')); SCS = next(o for o in dst.objects if 'casualsuit' in o.name)
print('SPECC', SCB.name, SCB.type, bool(SCB.data.shape_keys), len(SCB.data.vertices))
for o in (SCB, SCS):
    bpy.context.scene.collection.objects.link(o); o.animation_data_clear(); o.parent = None; o.matrix_world = Matrix.Identity(4)
    for c in list(o.constraints): o.constraints.remove(c)
for m in list(SCB.modifiers): SCB.modifiers.remove(m)
for m in list(SCS.modifiers):
    if m.type == 'ARMATURE': SCS.modifiers.remove(m)
if SCB.data.shape_keys: SCB.data.shape_keys.animation_data_clear()
bpy.context.view_layer.update()
sd = SCS.modifiers.new("Refit", 'SURFACE_DEFORM'); sd.target = SCB
with bpy.context.temp_override(object=SCS, active_object=SCS):
    bpy.ops.object.surfacedeform_bind(modifier="Refit")
if SCB.data.shape_keys:
    for kb in SCB.data.shape_keys.key_blocks: kb.value = 0.0
else:
    SCB.shape_key_add(name='Basis', from_mix=False)
ck2 = SCB.shape_key_add(name="Child9", from_mix=False)
for i, c in enumerate(kco): ck2.data[i].co = c
ck2.value = 1.0; bpy.context.view_layer.update()
with bpy.context.temp_override(object=SCS, active_object=SCS):
    bpy.ops.object.modifier_apply(modifier="Refit")
SCS.name = "Girl.casualsuit"; SCS.parent = KID
am = SCS.modifiers.new("Armature", 'ARMATURE'); am.object = KID
while SCS.modifiers.find("Armature") > 0: SCS.modifiers.move(SCS.modifiers.find("Armature"), 0)
bpy.data.objects.remove(SCB)
print("CASUALSUIT", len(SCS.data.vertices), [g.name for g in SCS.vertex_groups][:5])
for ch in list(OLD.children):
    mw = ch.matrix_world.copy(); ch.parent = KID; ch.matrix_world = mw
    for m in ch.modifiers:
        if m.type == 'ARMATURE': m.object = KID
# keep a clean, complete copy of the child skin (no deleted faces) as the source for garments
JS = KB.copy(); JS.data = KB.data.copy(); JS.name = "Girl.jacketsrc"; bpy.context.scene.collection.objects.link(JS)
for m in list(JS.modifiers):
    if m.type != 'ARMATURE': JS.modifiers.remove(m)
JS.parent = KID; JS.hide_render = True; JS.hide_viewport = True
bpy.data.objects.remove(KB); bpy.data.objects.remove(OLD)
KID.name = "Girl"; KID.data.name = "Girl"
print("CHILD height", round(max(c.z for c in kco), 3))
for i, n in enumerate(["Girl", "SearchA", "SearchB", "SearchC", "Worker"]):
    bpy.data.objects[n].location.x = i * 1.0
for o in bpy.data.objects:
    print("OBJ", o.name, o.type, o.parent.name if o.parent else None, [m.type + ":" + (getattr(m, 'object', None).name if getattr(m, 'object', None) else '') for m in o.modifiers][:4], [m.name for m in getattr(o.data, 'materials', [])][:3])
bpy.ops.wm.save_as_mainfile(filepath=out, compress=True)
