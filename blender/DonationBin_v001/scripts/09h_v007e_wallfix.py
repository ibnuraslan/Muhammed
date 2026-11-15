"""DonationBin v007e fix: at 626-690 (she leans at the grate) 09f moved her +y, but that grate is on the BACK wall, so she went
into it. This shifts her the other way: net 20 cm out from the back wall (same eased window as 09f), then 09g re-tracks the shot.
blender -b in.blend --python 09h_v007e_wallfix.py -- out.blend"""
import sys
import bpy
from mathutils import Vector
OUT = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene; WO = bpy.data.objects["Woman"]
BN = ["root", "IK_hand.L", "IK_hand.R", "IK_foot.L", "IK_foot.R", "Pole_elbow.L", "Pole_elbow.R", "Pole_knee.L", "Pole_knee.R"]
for f in range(630, 688, 2):
    w = min(1.0, (f - 626) / 12.0, (690 - f) / 12.0)
    sc.frame_set(f)
    for b in BN:
        pb = WO.pose.bones[b]; M = pb.matrix.copy()
        M.translation += WO.matrix_world.inverted().to_3x3() @ Vector((0, -0.40 * w, 0))
        pb.matrix = M
    for b in BN: WO.pose.bones[b].keyframe_insert("location", frame=f, group=b)
sc.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print("WALLFIX_DONE")
