"""Time-warp the whole film onto the delivered voiceover.
blender -b gr_anim.blend --python 05_retime_to_vo.py -- <vo.mp3> <out.blend>

Piecewise-linear warp: each story beat's old start frame maps onto the frame where that beat's first word
is spoken in the voiceover (word timestamps from faster-whisper). Every keyframe and handle in every action
(objects, bones, constraints, materials, world, lights, cameras, shape keys, scene exposure) is remapped.
"""
import sys
import bpy

argv = sys.argv[sys.argv.index("--") + 1:]
VO, OUT = argv[0], argv[1]
sc = bpy.context.scene
FPS = 60
def fr(t):
    return 1 + round(t * FPS)
# (old frame, new frame). Beat starts from the voiceover; two extra anchors keep the fall at real speed.
ANCHORS = [(1, 1), (36, 22), (92, 76),
           (193, fr(2.28)),    # "broke his hip"
           (285, fr(3.60)),    # "He couldn't move"
           (497, fr(6.86)),    # "For five days"
           (677, fr(9.74)),    # "baking"
           (753, fr(10.52)),   # "and freezing"
           (869, fr(12.28)),   # "But he wasn't alone"
           (969, fr(14.00)),   # "His goat"
           (1176, fr(16.82)),  # "At night"
           (1389, fr(20.14)),  # "Days went by"
           (1605, fr(23.80)),  # "But the goat let him milk her"
           (1831, fr(26.40)),  # "giving him just enough"
           (1974, fr(28.56)),  # "When help finally came"
           (2149, fr(31.76) - 1), (2150, fr(31.76)),   # sky tilt -> hospital ("And he swears")
           (2340, 2100)]       # end: voiceover ends at 34.27 s, film at 35.0 s
def warp(x):
    if x <= ANCHORS[0][0]:
        return ANCHORS[0][1] + (x - ANCHORS[0][0])
    for (a0, b0), (a1, b1) in zip(ANCHORS, ANCHORS[1:]):
        if x <= a1:
            return b0 + (x - a0) * (b1 - b0) / (a1 - a0)
    return ANCHORS[-1][1] + (x - ANCHORS[-1][0])

n_keys = 0
for act in bpy.data.actions:
    fcs = []
    for layer in getattr(act, "layers", []):
        for strip in layer.strips:
            for cb in getattr(strip, "channelbags", []):
                fcs.extend(cb.fcurves)
    for fc in fcs:
        for kp in fc.keyframe_points:
            kp.co.x = warp(kp.co.x)
            kp.handle_left.x = warp(kp.handle_left.x)
            kp.handle_right.x = warp(kp.handle_right.x)
            n_keys += 1
        fc.update()
sc.frame_start, sc.frame_end = 1, 2100
# narration: the delivered voiceover replaces the scratch track
se = sc.sequence_editor
strips = getattr(se, "strips", None) or se.sequences
for s in list(strips):
    strips.remove(s)
snd = strips.new_sound("VO_Marcus", VO, channel=1, frame_start=1)
sc.render.filepath = "//render/GoatRescue2_v002_"
print("RETIMED keys", n_keys, "end", sc.frame_end, "vo frames", snd.frame_final_duration)
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("SAVED", OUT)
