"""run pipeline/body_prop_cross.py over a frame range: blender -b f.blend --python bpc_range.py -- F0 F1 out.json STEP props"""
import bpy, sys
a = sys.argv[sys.argv.index("--") + 1:]
sc = bpy.context.scene; sc.frame_start, sc.frame_end = int(a[0]), int(a[1])
sys.argv = sys.argv[:sys.argv.index("--") + 1] + a[2:]
exec(open("/home/user/Muhammed/blender/ClosetBathroom_v002/scripts/body_prop_cross_nohelper.py").read())
