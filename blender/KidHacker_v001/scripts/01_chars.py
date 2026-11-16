"""Characters from earlier studio packages (MakeHuman asset server is down), refitted with remake().
blender -b --factory-startup --python 01_chars.py -- <cid> -> /tmp/claude-0/kh/work/ch_<cid>.blend"""
import bpy, sys
exec(open("/home/user/Muhammed/blender/KidHacker_v001/scripts/remake.py").read())
R = "/home/user/Muhammed/blender/"
SWS = R + "SpeakWithoutSight_v006/SpeakWithoutSight_v006_60fps.blend"
TS = R + "Tsunami2004_v012/Tsunami2004_v012_60fps.blend"
TI = R + "TitanicIceberg_v014/TitanicIceberg_v014_60fps.blend"
RB = R + "RingBullet_v008/RingBullet_v008_60fps.blend"
SPEC = {
 "Kid":    (SWS, "Girl", {"age": 0.185, "height": 0.8}, ("long_skirt", "female_elegantsuit01", "shoes01", "braid01"), [(TS, "KidB", "female_casualsuit01"), (TS, "KidB", "shoes02"), (SWS, "Mother", "long01")]),   # v002c: the elegantsuit blouse was tried and dropped (sleeves stretched on reaching arms)
 "KidBob": (SWS, "Girl", {"age": 0.185, "height": 0.8}, ("long_skirt", "shoes01", "braid01"), [(TS, "KidB", "female_casualsuit01"), (TS, "KidB", "shoes02"), (R + "BellyFat_v010/BellyFat_v010_60fps.blend", "Woman", "bob02")]),
 "KidPony": (SWS, "Girl", {"age": 0.185, "height": 0.8}, ("long_skirt", "shoes01", "braid01"), [(TS, "KidB", "female_casualsuit01"), (TS, "KidB", "shoes02"), (SWS, "Teacher", "ponytail01")]),
 "Mom":    (SWS, "Mother", {}, (), []),
 "AgentA": (TI, "ExpertA", {"age": 0.55}, ("short03",), [(TI, "ExpertB", "short02")]),
 "AgentB": (TI, "ExpertB", {}, (), []),
 "AgentC": (SWS, "Father", {}, (), []),
}
cid = sys.argv[sys.argv.index("--") + 1]
bpy.ops.wm.read_factory_settings(use_empty=True)
src, donor, ph, drop, extra = SPEC[cid]
if not ph and not drop and not extra:
    if cid == "Mom": KEEP = ("ARMATURE", "MASK", "SUBSURF", "SHRINKWRAP", "SMOOTH", "NODES", "SOLIDIFY")
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
else:
    remake(src, donor, cid, ph, drop, extra)
for o in bpy.data.objects:
    o.hide_render = False; o.hide_viewport = False; o.hide_set(False)
    if o.parent and o.parent.type == 'ARMATURE': o.matrix_parent_inverse.identity()
bpy.ops.outliner.orphans_purge(do_recursive=True)
bpy.ops.wm.save_as_mainfile(filepath="/tmp/claude-0/kh/work/ch_%s.blend" % cid, compress=True)
print("SAVED", cid)
