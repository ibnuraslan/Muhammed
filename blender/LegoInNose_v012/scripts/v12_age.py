"""v012b aging time-lapse 1150-1291 (list 14, 26-29, 37):
 - Boy 1160-1229: hands resting on his knees instead of A-pose arms flung out.
 - Teen T-shirt navy (the terracotta read as bare skin on camera).
 - Phone screen dark glass (it read as a blank white card).
 - Each age is its own steady shot with a hard cut at the swap (boy | 1230 teen | 1267 man | 1292 bench): no pop-in inside a moving
   shot and no camera flight past his shoulder into the bench shot (list 28-29).
blender -b in.blend --python v12_age.py -- out.blend"""
import bpy, sys
from mathutils import Vector
OUT = sys.argv[sys.argv.index("--") + 1]; sc = bpy.context.scene; vl = bpy.context.view_layer
exec(open("/home/user/Muhammed/blender/pipeline/hand_poses.py").read())
def fcs(o):
    ad = o.animation_data
    return [fc for l in ad.action.layers for st in l.strips for cb in st.channelbags for fc in cb.fcurves] if ad and ad.action else []
# boy hands on knees
B = bpy.data.objects["Boy"]
for fc in fcs(B):
    if fc.data_path.startswith(('pose.bones["IK_hand.', 'pose.bones["finger', 'pose.bones["wrist.')):
        for k in [k for k in fc.keyframe_points if 1156 <= k.co.x <= 1229][::-1]: fc.keyframe_points.remove(k)
        fc.update()
def Wb(n): return B.matrix_world @ B.pose.bones[n].head
for f in (1166, 1200, 1229):
    for s in ("L", "R"):
        sc.frame_set(f); kn = Wb("lowerleg01." + s); ft = Wb("foot." + s); d = ft - kn; d.z = 0; d.normalize()
        place_hand(B, s, f, kn + Vector((0, 0, 0.045)) + d * 0.03, Vector((0, 0, -1)), d); apply_pose(B, s, "relaxed", f)
# teen shirt navy
tm = bpy.data.objects["Teen_Teen.male_casualsuit02"].data.materials[0]
for n in tm.node_tree.nodes:
    if n.type == "RGB" and abs(n.outputs[0].default_value[0] - 0.55) < 0.01: n.outputs[0].default_value = (0.05, 0.09, 0.22, 1)
# phone screen: dark glass
pm = bpy.data.objects["Prop_PhoneScreen"].active_material; P = pm.node_tree.nodes["Principled BSDF"]
for l in [l for l in pm.node_tree.links if l.to_node == P]: pm.node_tree.links.remove(l)
P.inputs["Base Color"].default_value = (0.02, 0.025, 0.035, 1); P.inputs["Roughness"].default_value = 0.08
for nm in ("Emission Strength",):
    if nm in P.inputs: P.inputs[nm].default_value = 0.0
# phone: its keys were doubled and jittery (it jumped and vanished); bake it to the midpoint of his hands, as posed at 1272
Mn = bpy.data.objects["Man"]; PH = bpy.data.objects["Prop_Phone"]
def mid(): return (Mn.matrix_world @ Mn.pose.bones["wrist.L"].head + Mn.matrix_world @ Mn.pose.bones["wrist.R"].head) / 2
sc.frame_set(1272); off = PH.matrix_world.translation - mid(); R = PH.matrix_world.to_3x3().to_4x4()
for fc in fcs(PH):
    if fc.data_path in ("location", "rotation_euler", "rotation_quaternion"):
        for k in [k for k in fc.keyframe_points if 1267 <= k.co.x <= 1291][::-1]: fc.keyframe_points.remove(k)
        fc.update()
from mathutils import Matrix
for f in range(1267, 1292):
    sc.frame_set(f); PH.matrix_world = Matrix.Translation(mid() + off) @ R; vl.update()
    PH.keyframe_insert("location", frame=f); PH.keyframe_insert("rotation_quaternion" if PH.rotation_mode == "QUATERNION" else "rotation_euler", frame=f)
for o in (PH, bpy.data.objects["Prop_PhoneScreen"]):
    for fc in fcs(o):
        if fc.data_path == "hide_render":
            for k in fc.keyframe_points:
                if 1289.5 < k.co.x < 1291.5: k.co.x = 1291.5; k.handle_left.x = 1291.5; k.handle_right.x = 1291.5   # through the last rug frame
            fc.update()
# hard cuts: hold each age's camera
CAM = bpy.data.objects["CAM_Film"]; AIM = bpy.data.objects["CAM_Film_Aim"]
chans = [fc for o in (CAM, AIM) for fc in fcs(o) if fc.data_path == "location"] + [fc for fc in fcs(CAM.data) if fc.data_path == "lens"]
def hold(a, b, ref):
    vals = [(fc, fc.evaluate(ref)) for fc in chans]
    for fc, v in vals:
        prev = fc.evaluate(a - 1)
        for k in [k for k in fc.keyframe_points if a - 1 <= k.co.x <= b][::-1]: fc.keyframe_points.remove(k)
        kp = fc.keyframe_points.insert(a - 1, prev, options={"FAST"}); kp.interpolation = "CONSTANT"
        k1 = fc.keyframe_points.insert(a, v, options={"FAST"}); k1.interpolation = "CONSTANT"
        k2 = fc.keyframe_points.insert(b, v, options={"FAST"}); k2.interpolation = "CONSTANT"
        fc.update()
hold(1230, 1266, 1250)     # teen
hold(1267, 1291, 1272)     # man on the rug with his phone; 1292 is the bench shot's own key
print("AGE done")
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
