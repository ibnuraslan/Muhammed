"""Re-render one range of the preview (same settings and naming as pipeline/preview.py) for splicing.
blender -b pkg.blend --python preview_range.py -- OUT step f0 f1   (f0 is snapped up to the preview grid 1+k*step)"""
import bpy, sys
a = sys.argv[sys.argv.index("--") + 1:]
out, step, f0, f1 = a[0], int(a[1]), int(a[2]), int(a[3])
sc = bpy.context.scene
f0 = f0 + ((1 - f0) % step)
sc.frame_start, sc.frame_end = f0, f1
sys.argv = [sys.argv[0], "--", out, str(step)]
exec(open("/home/user/Muhammed/blender/pipeline/preview.py").read())
