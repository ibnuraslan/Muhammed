"""Piecewise-linear time warp of every keyframe onto the voiceover, then swap in the VO strip.
blender -b anim.blend --python retime_to_vo.py -- anchors.json vo.mp3 out.blend
anchors.json: {"fps": 60, "end": 2100, "anchors": [[old_frame, new_frame_or_null, seconds_or_null], ...]}
Give each beat's old start frame and either the new frame or the second its first word is spoken."""
import sys, json
import bpy
a = sys.argv[sys.argv.index("--") + 1:]
cfg = json.load(open(a[0])); VO, OUT = a[1], a[2]
FPS = cfg.get("fps", 60)
AN = [(o, n if n is not None else 1 + round(t * FPS)) for o, n, t in cfg["anchors"]]
def warp(x):
    if x <= AN[0][0]: return AN[0][1] + (x - AN[0][0])
    for (a0, b0), (a1, b1) in zip(AN, AN[1:]):
        if x <= a1: return b0 + (x - a0) * (b1 - b0) / (a1 - a0)
    return AN[-1][1] + (x - AN[-1][0])
n = 0
for act in bpy.data.actions:
    for layer in getattr(act, "layers", []):
        for strip in layer.strips:
            for cb in getattr(strip, "channelbags", []):
                for fc in cb.fcurves:
                    for kp in fc.keyframe_points:
                        kp.co.x = warp(kp.co.x); kp.handle_left.x = warp(kp.handle_left.x); kp.handle_right.x = warp(kp.handle_right.x); n += 1
                    fc.update()
sc = bpy.context.scene
sc.frame_start, sc.frame_end = 1, cfg["end"]
se = sc.sequence_editor or sc.sequence_editor_create()
strips = se.strips if hasattr(se, "strips") else se.sequences
for s in list(strips): strips.remove(s)
strips.new_sound("VO", VO, channel=1, frame_start=1)
print("RETIMED keys", n, "end", sc.frame_end)
bpy.ops.wm.save_as_mainfile(filepath=OUT)
