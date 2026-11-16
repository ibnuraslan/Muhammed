"""run pipeline/body_prop_cross.py on a frame range: -- F0 F1 out.json STEP props [rigs]"""
import bpy, sys
i = sys.argv.index("--"); a = sys.argv[i + 1:]
sc = bpy.context.scene; sc.frame_start, sc.frame_end = int(a[0]), int(a[1])
sys.argv = sys.argv[:i + 1] + a[2:]
exec(open("/home/user/Muhammed/blender/pipeline/body_prop_cross.py").read())
