import bpy, sys
a = sys.argv[sys.argv.index("--") + 1:]; sc = bpy.context.scene; sc.frame_start, sc.frame_end = int(a[2]), int(a[3])
sys.argv = [sys.argv[0], "--", a[0], a[1]]
exec(open("/home/user/Muhammed/blender/pipeline/preview.py").read())
