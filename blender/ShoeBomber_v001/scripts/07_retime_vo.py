"""v009: build the delivered film straight on the VO frames (1-1469, director's sync/07.anchors.json beats).
Source film -> delivered frame map, piecewise linear between anchors:
   delivered  1..870   <- source 1..1068   (cabin beats 1-6; each beat lands on its VO word)
   delivered  871..978 <- source 1069..1158 (beat 7, the cut-open shoe; camera-only push on a still prop)
   delivered  979..1134 <- source 1215..1370 (beat 8, the plane: authored at 1:1)
   delivered 1135..1469 <- source 1393..1727 (beat 9, security: authored at 1:1)
Every animation curve is resampled as per-frame CONSTANT keys (exact values; hard cuts stay hard).
blender -b film.blend --python 07_retime_vo.py -- <out.blend>"""
import sys, bpy
OUT = sys.argv[sys.argv.index("--") + 1]
END = 1469
# (delivered, source) anchor pairs; segments are joined only within the same block
BLOCKS = [
    [(1, 1), (157, 199), (289, 373), (373, 481), (505, 655), (625, 769), (870, 1068)],
    [(871, 1069), (978, 1158)],
    [(979, 1215), (1134, 1370)],
    [(1135, 1393), (1469, 1727)],
]
def src(t):
    for blk in BLOCKS:
        if blk[0][0] <= t <= blk[-1][0]:
            for (d0, s0), (d1, s1) in zip(blk, blk[1:]):
                if d0 <= t <= d1:
                    return s0 + (s1 - s0) * (t - d0) / (d1 - d0)
    raise ValueError(t)

sc = bpy.context.scene
def all_fcurves():
    seen = set()
    for act in bpy.data.actions:
        if act.name in seen: continue
        seen.add(act.name)
        for layer in getattr(act, "layers", []):
            for strip in layer.strips:
                for cb in strip.channelbags:
                    for fc in cb.fcurves: yield fc

n_fc = 0
for fc in list(all_fcurves()):
    if not fc.keyframe_points: continue
    vals = [(t, fc.evaluate(src(t))) for t in range(1, END + 1)]
    kp = fc.keyframe_points
    for i in range(len(kp) - 1, -1, -1): kp.remove(kp[i], fast=True)
    kp.add(len(vals))
    for j, (t, v) in enumerate(vals):
        p = kp[j]; p.co = (t, v); p.handle_left = (t - 0.3, v); p.handle_right = (t + 0.3, v); p.interpolation = 'CONSTANT'
    fc.update(); n_fc += 1
sc.frame_start, sc.frame_end = 1, END
print("RETIMED_VO", n_fc, "fcurves; frame_end", sc.frame_end)
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print("RETIME_SAVED", OUT)
