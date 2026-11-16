"""run pipeline/body_prop_cross.py over a frame range: blender -b x.blend --python bpc_range.py -- f0 f1 <body_prop_cross args...>"""
import bpy, sys, os
i = sys.argv.index("--"); f0, f1 = int(sys.argv[i + 1]), int(sys.argv[i + 2])
sc = bpy.context.scene; sc.frame_start, sc.frame_end = f0, f1
sys.argv = sys.argv[:i + 1] + sys.argv[i + 3:]
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "pipeline", "body_prop_cross.py")).read())
