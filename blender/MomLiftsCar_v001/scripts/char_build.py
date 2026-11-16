import bpy, sys
exec(open("/tmp/claude-0/b14/scripts/remake.py").read())
R = "/home/user/Muhammed/blender/"
SPEC = {
 "Mom":  (R + "GameBoxBullet_v010/GameBoxBullet_v010_60fps.blend", "Walker"),
 "MomB": (R + "FrozenTearsGun_v010/FrozenTearsGun_v010_60fps.blend", "Inventor"),
 "Son":  (R + "CaveRescue_v010/CaveRescue_v010_60fps.blend", "Boy1"),
 "SonB": (R + "HeadsetBullet_v008/HeadsetBullet_v008_60fps.blend", "Teen"),
 "Man":  (R + "Tsunami2004_v012/Tsunami2004_v012_60fps.blend", "LocalM"),
 "ManB": (R + "WaterTubes_v006/WaterTubes_v006_60fps.blend", "Hero"),
 "ManC": (R + "ToucanBeak_v009/ToucanBeak_v009_60fps.blend", "VetB"),
 "ManD": (R + "ShoeBomber_v008/ShoeBomber_v008_60fps.blend", "Bomber"),
 "ManE": (R + "BelugaRescue_v008/BelugaRescue_v008_60fps.blend", "SpecF"),
}
cid = sys.argv[sys.argv.index("--") + 1]
bpy.ops.wm.read_factory_settings(use_empty=True)
src, donor = SPEC[cid]
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
for o in bpy.data.objects:
    o.hide_render = False; o.hide_viewport = False; o.hide_set(False)
bpy.ops.outliner.orphans_purge(do_recursive=True)
print("LOADED", cid, sorted(o.name for o in col.objects), [m.name for o in col.objects for m in o.modifiers if m.type=='MASK'])
bpy.ops.wm.save_as_mainfile(filepath="/tmp/claude-0/b14/work/ch_%s.blend" % cid, compress=True)
