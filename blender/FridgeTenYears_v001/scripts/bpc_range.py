"""run pipeline/body_prop_cross.py on a frame range with the rigs that are visible at its first frame.
blender -b film.blend --python bpc_range.py -- F0 F1 out.json STEP Props"""
import bpy, sys
a = sys.argv[sys.argv.index("--") + 1:]
sc = bpy.context.scene; sc.frame_start = int(a[0]); sc.frame_end = int(a[1]); sc.frame_set(int(a[0]))
sys.argv = sys.argv[:sys.argv.index("--") + 1] + a[2:]
exec(open("/home/user/Muhammed/blender/pipeline/body_prop_cross.py").read())
