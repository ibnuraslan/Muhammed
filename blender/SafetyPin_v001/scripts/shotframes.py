"""print first/mid/last frame of every shot (marker cameras)"""
import bpy
sc = bpy.context.scene; ms = sorted([m for m in sc.timeline_markers if m.camera], key=lambda m: m.frame)
out = []
for i, m in enumerate(ms):
    f0 = m.frame; f1 = (ms[i + 1].frame - 1) if i + 1 < len(ms) else sc.frame_end
    out += [f0, (f0 + f1) // 2, f1]
    print("SHOT", m.name, f0, f1)
print("FRAMES", ",".join(map(str, out)))
