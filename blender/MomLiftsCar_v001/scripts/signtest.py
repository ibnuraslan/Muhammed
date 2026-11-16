import bpy, math, sys
from mathutils import Vector
P = "/home/user/Muhammed/blender/pipeline/"
exec(open(P + "anim_lib.py").read()); exec(open(P + "hand_poses.py").read())
sc = bpy.context.scene; R_ = math.radians; CUR_WIN = None; RIGS = {}; HUM = {}
exec(open("/tmp/claude-0/b14/scripts/lib_anim.py").read())
rig, R, H = setup("MomB", "Mom")
H.key_root(1, Vector((0, 4.0, H.root_head.z)), flex=30)
H.key_spine(1, flex=30, head=(20, 0))
sc.frame_set(1); bpy.context.view_layer.update()
print("HEAD", bone_w(rig, "head"), "ROOT", bone_w(rig, "root"), "RH", H.root_head)
