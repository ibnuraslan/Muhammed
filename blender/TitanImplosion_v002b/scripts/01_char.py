"""Extract the man (MPFB 'ShopperA' from the approved BellyFat_v010) into chars.blend, clean of animation.
blender -b --factory-startup --python 01_char.py -- <src.blend> <out.blend>"""
import bpy, sys
a = sys.argv[sys.argv.index("--") + 1:]
SRC, OUT = a[0], a[1]
for o in list(bpy.data.objects): bpy.data.objects.remove(o, do_unlink=True)
with bpy.data.libraries.load(SRC, link=False) as (fr, to):
    to.objects = [n for n in fr.objects if n == "ShopperA" or n.startswith("ShopperA.")]
sc = bpy.context.scene
for o in to.objects:
    if o is None: continue
    sc.collection.objects.link(o)
rig = bpy.data.objects["ShopperA"]
for o in [rig] + list(rig.children):
    o.animation_data_clear()
    if o.type == 'MESH' and o.data.shape_keys: o.data.shape_keys.animation_data_clear()
for pb in rig.pose.bones:
    for c in list(pb.constraints): pb.constraints.remove(c)
    pb.location = (0, 0, 0); pb.rotation_mode = 'QUATERNION'; pb.rotation_quaternion = (1, 0, 0, 0); pb.scale = (1, 1, 1)
# drop helper bones added by the old film (IK/pole) so make_human_ctrl can recreate them
bpy.context.view_layer.objects.active = rig; bpy.ops.object.mode_set(mode='EDIT')
for b in list(rig.data.edit_bones):
    if b.name.startswith(("IK_", "Pole_")): rig.data.edit_bones.remove(b)
bpy.ops.object.mode_set(mode='OBJECT')
rig.name = "Man"; rig.location = (0, 0, 0); rig.rotation_euler = (0, 0, 0)
for c in rig.children:
    c.name = c.name.replace("ShopperA", "Man")
    for m in c.modifiers:
        if m.type == 'ARMATURE': m.object = rig
print("EYEFIX present:", any(n.name == "CorneaTransparentMix" for n in bpy.data.node_groups["EnhancedEye"].nodes) if "EnhancedEye" in bpy.data.node_groups else "no group")
print("KIDS", [(c.name, [m.name for m in c.data.materials]) for c in rig.children if c.type == 'MESH'])
print("DIM", rig.dimensions[:], [m.type for c in rig.children for m in c.modifiers][:20])
bpy.ops.wm.save_as_mainfile(filepath=OUT)
