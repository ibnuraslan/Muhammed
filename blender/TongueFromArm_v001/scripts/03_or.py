"""OR set from EarInArm (room, reclining chair, arm board, lamps, trolley) frozen at its frame 450; patient pose transferred.
blender -b work/chars_dressed.blend --python 03_or.py -- work/or.blend"""
import bpy, sys, json
from mathutils import Matrix, Vector, Quaternion
HERE = "/home/user/Muhammed/blender/TongueFromArm_v001/"
out = sys.argv[sys.argv.index("--") + 1]
J = json.load(open(HERE + "work/ear_pose.json")); F = "450"
SKIP = ("Patient", "Surgeon", "Nurse", "Ear_", "Shaving", "Chest_", "Suture", "CAM_", "SB_", "Bandage", "JoinVessel", "Arm_Pocket", "Cart_Block", "Studio")
with bpy.data.libraries.load("/home/user/Muhammed/blender/EarInArm_v011/EarInArm_v011_60fps.blend", link=False) as (src, dst):
    dst.objects = [n for n in src.objects if n in J[F]["objs"] and not n.startswith(SKIP)]
col = bpy.data.collections.new("OR"); bpy.context.scene.collection.children.link(col)
objs = [o for o in dst.objects if o is not None]
for o in objs:
    col.objects.link(o); o.animation_data_clear()
    for c in list(o.constraints): o.constraints.remove(c)
    if o.type == 'MESH' and o.data.shape_keys: o.data.shape_keys.animation_data_clear()
    if o.parent and o.parent.name not in [x.name for x in objs]: o.parent = None
def depth(o): return 0 if o.parent is None else 1 + depth(o.parent)
for o in sorted(objs, key=depth):
    o.matrix_world = Matrix(J[F]["objs"][o.name]); bpy.context.view_layer.update()
for o in objs:
    o.hide_render = False; o.hide_viewport = False
    if o.name.startswith("OR_LampGlint"): o.hide_render = True    # glint triangles reported in EarInArm
print("OR objects", len(objs))
# patient pose (FK) from EarInArm Patient at frame 450
def put_pose(rig, P, f=1):
    for pb in rig.pose.bones:
        if pb.name not in P: continue
        l, q = P[pb.name]; pb.rotation_mode = 'QUATERNION'; pb.rotation_quaternion = Quaternion(q)
        if pb.name == "root": pb.location = Vector(l)
        pb.keyframe_insert("rotation_quaternion", frame=f, group=pb.name)
        if pb.name == "root": pb.keyframe_insert("location", frame=f, group=pb.name)
rig = bpy.data.objects["Patient"]; rig.matrix_world = Matrix(J[F]["Patient"]["mw"])
put_pose(rig, J[F]["Patient"]["pose"])
S = bpy.data.objects["Surgeon"]; S.matrix_world = Matrix(J[F]["Surgeon"]["mw"]); put_pose(S, J[F]["Surgeon"]["pose"])
for n in ("Doctor", "Girl", "Nurse"): bpy.data.objects[n].location = (0, 0, -20)
bpy.ops.wm.save_as_mainfile(filepath=out, compress=True)
