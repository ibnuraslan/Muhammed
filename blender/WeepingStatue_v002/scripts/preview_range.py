"""Re-render only a frame range of the preview (aligned to the every-5th grid), then preview.py.
blender -b pkg.blend --python preview_range.py -- OUT_DIR a b"""
import bpy, sys, os
a = sys.argv[sys.argv.index("--") + 1:]; out, fa, fb = a[0], int(a[1]), int(a[2])
sc = bpy.context.scene; sc.frame_start = 1 + 5 * ((fa - 1 + 4) // 5); sc.frame_end = fb
sys.argv = [sys.argv[0], "--", out, "5"]
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "pipeline", "preview.py")).read())
