import bpy, sys
exec(open("/tmp/claude-0/b09/scripts/remake.py").read())
R = "/home/user/Muhammed/blender/"
BF = R + "BellyFat_v010/BellyFat_v010_60fps.blend"
SPEC = {
 "Gran":  (BF, "ShopperB", {"age": 0.92, "weight": 0.62, "height": 0.35, "muscle": 0.3}, ("ponytail01",), [(BF, "Woman", "bob02")]),
 "GranH": (BF, "ShopperC", {"age": 0.92, "weight": 0.62, "height": 0.35, "muscle": 0.3}, ("long01",), [(BF, "ShopperA", "short02")]),
 "Doctor": (R + "MonkeyHeadTransplant_v012/MonkeyHeadTransplant_v012_60fps.blend", "Surgeon", {"age": 0.6}, (), [(R + "AIAsleep_v007/AIAsleep_v007_60fps.blend", "Driver", "short02")]),
 "Nurse": (R + "EarInArm_v011/EarInArm_v011_60fps.blend", "Nurse", {}, (), []),
 "Hero":  (R + "BelugaRescue_v008/BelugaRescue_v008_60fps.blend", "SpecB", {}, (), []),
 "C1": (R + "BelugaRescue_v008/BelugaRescue_v008_60fps.blend", "SpecA", {}, (), []),
 "C2": (R + "BelugaRescue_v008/BelugaRescue_v008_60fps.blend", "SpecD", {}, (), []),
 "C3": (R + "NoPilotPlane_v010/NoPilotPlane_v010_60fps.blend", "PD", {}, (), []),
 "C4": (R + "BelugaRescue_v008/BelugaRescue_v008_60fps.blend", "SpecF", {}, (), []),
 "C5": (R + "BelugaRescue_v008/BelugaRescue_v008_60fps.blend", "SpecE", {}, (), []),
 "ExecA": (R + "TitanicIceberg_v014/TitanicIceberg_v014_60fps.blend", "ExpertA", {"age": 0.7, "weight": 0.65}, (), []),
 "ExecB": (R + "TitanicIceberg_v014/TitanicIceberg_v014_60fps.blend", "ExpertB", {}, (), []),
 "ExecC": (R + "PrisonKeyCake_v010/PrisonKeyCake_v010_60fps.blend", "President", {}, (), []),
 "Employee": (BF, "Stocker", {}, (), []),
 "Nurse2": (R + "ToucanBeak_v009/ToucanBeak_v009_60fps.blend", "VetA", {}, (), []),
 "Hero2": (R + "AIAsleep_v007/AIAsleep_v007_60fps.blend", "Driver", {}, (), []),
 "Boss2": (R + "BeethovenDeaf_v010/BeethovenDeaf_v010_60fps.blend", "Composer", {"age": 0.62}, (), []),
}
cid = sys.argv[sys.argv.index("--") + 1]
bpy.ops.wm.read_factory_settings(use_empty=True)
src, donor, ph, drop, extra = SPEC[cid]
if not ph and not drop and not extra:
    # unchanged phenotype: load and clean only
    objs = _load(src, donor); col = bpy.data.collections.new("CH_" + cid); bpy.context.scene.collection.children.link(col)
    rig = bpy.data.objects[donor]
    for o in objs:
        if o.type == 'EMPTY' or (o != rig and o.parent != rig): bpy.data.objects.remove(o); continue
        col.objects.link(o)
    for pb in rig.pose.bones:
        for c in list(pb.constraints): pb.constraints.remove(c)
        pb.location = (0, 0, 0); pb.rotation_quaternion = (1, 0, 0, 0); pb.rotation_euler = (0, 0, 0); pb.scale = (1, 1, 1)
    rig.hide_viewport = False; rig.hide_set(False); bpy.context.view_layer.objects.active = rig; rig.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    for eb in list(rig.data.edit_bones):
        if eb.name.startswith(("IK_", "Pole_")): rig.data.edit_bones.remove(eb)
    bpy.ops.object.mode_set(mode='OBJECT')
    rig.location = (0, 0, 0); rig.rotation_euler = (0, 0, 0); rig.scale = (1, 1, 1)
    for o in list(col.objects):
        if o.name == donor: o.name = cid; o.data.name = cid
        elif o.name.startswith(donor + "."): o.name = cid + o.name[len(donor):]
    print("LOADED", cid, sorted(o.name for o in col.objects))
else:
    remake(src, donor, cid, ph, drop, extra)
for o in bpy.data.objects:
    o.hide_render = False; o.hide_viewport = False; o.hide_set(False)
bpy.ops.outliner.orphans_purge(do_recursive=True)
bpy.ops.wm.save_as_mainfile(filepath="/tmp/claude-0/b09/work/ch_%s.blend" % cid, compress=True)
