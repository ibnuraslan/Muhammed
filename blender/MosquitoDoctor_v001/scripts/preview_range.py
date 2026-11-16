"""preview.py over a frame range: blender -b pkg.blend --python preview_range.py -- f0 f1 OUT_DIR [step]"""
import bpy, sys, os
i = sys.argv.index("--"); f0, f1 = int(sys.argv[i + 1]), int(sys.argv[i + 2])
sc = bpy.context.scene; sc.frame_start, sc.frame_end = f0, f1
sys.argv = sys.argv[:i + 1] + sys.argv[i + 3:]
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "pipeline", "preview.py")).read())
