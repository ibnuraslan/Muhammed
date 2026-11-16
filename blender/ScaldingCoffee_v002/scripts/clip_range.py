import bpy, sys
a = sys.argv[sys.argv.index("--") + 1:]; sc = bpy.context.scene; sc.frame_start, sc.frame_end = int(a[1]), int(a[2]); sc.frame_set(int(a[1]))
sys.argv = [sys.argv[0], "--", a[0], "6"]
exec(open("/home/user/Muhammed/blender/pipeline/clip_scan.py").read())
