"""v007: the syringe is IN the medic's hand (LESSONS 2.2). It was keyed in world space at the injection point, and the
hand passes (12_depenetrate) moved the hand off it (qa_check PROPMOVE at 2275-2281). Now the syringe is a bone child of
DiverA's right wrist for the whole time it is shown, holding the grip offset it had at 2190 (fingers on the barrel).
blender -b in.blend --python 18_v007_syringe.py -- out.blend"""
import bpy, sys
OUT = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene; syr = bpy.data.objects["Prop_Syringe"]; rig = bpy.data.objects["DiverA"]; B = "wrist.R"
def bone_w(f):
    sc.frame_set(f); pb = rig.pose.bones[B]; return rig.matrix_world @ pb.matrix
sc.frame_set(2190); rel = bone_w(2190).inverted() @ syr.matrix_world.copy()
ad = syr.animation_data
if ad and ad.action:
    for lay in ad.action.layers:
        for st in lay.strips:
            for cb in st.channelbags:
                for fc in list(cb.fcurves):
                    if fc.data_path in ("location", "rotation_euler", "rotation_quaternion", "scale"): cb.fcurves.remove(fc)
syr.parent = rig; syr.parent_type = 'BONE'; syr.parent_bone = B
bpy.context.view_layer.update()
sc.frame_set(2190); syr.matrix_world = bone_w(2190) @ rel   # constant local offset in the hand bone: rides with the hand
syr.keyframe_insert("location", frame=1); syr.keyframe_insert("rotation_euler", frame=1)
print("SYRINGE_IN_HAND")
bpy.ops.wm.save_as_mainfile(filepath=OUT)
