"""C1 (orange shirt, bob01): lift the fringe off her eyes (LESSONS: fringe covering one eye). Edits rest-pose hair
vertices in front of the face below brow height; side hair (|x|>8 cm) untouched, 2 cm blend in between."""
import bpy, sys
a = sys.argv[sys.argv.index("--") + 1:]; OUT = a[0]
h = bpy.data.objects["C1.bob01"]
EYE_Z, BROW = 1.561, 1.598
n = 0
for v in h.data.vertices:
    x, y, z = v.co
    if y > -0.085 or z >= BROW: continue
    w = max(0.0, min(1.0, (0.085 - abs(x)) / 0.02))
    if w <= 0: continue
    nz = BROW + (BROW - z) * 0.12            # fold the hanging strands up to the brow line
    v.co.z = z + (nz - z) * w; v.co.y = y + 0.012 * w   # and tuck slightly back toward the forehead
    n += 1
h.data.update()
print("FRINGE_FIXED", n, "verts")
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
