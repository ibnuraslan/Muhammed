"""v009: time the film to the client's VO (director's beat frames = VO seconds x 60 + 1, end 2436). Each beat is
stretched or squeezed linearly between its start and the next beat's start; no other retime is needed downstream.
blender -b in.blend --python 23_v009_vo.py -- out.blend beats_in.json beats_out.json"""
import bpy, sys, json
a = sys.argv[sys.argv.index("--") + 1:]; OUT, BIN, BOUT = a[0], a[1], a[2]
sc = bpy.context.scene
VO = {1: 1, 2: 341, 3: 571, 4: 687, 5: 891, 6: 1065, 7: 1160, 8: 1321, 9: 1463, 10: 1591, 11: 1761, 12: 1885, 13: 2105, 14: 2249}
WORDS = {1: "In 2018", 2: "Then, heavy rain", 3: "They were over two miles in", 4: "and every passage out", 5: "After 10 days, divers",
         6: "But the tunnels", 7: "that even a skilled diver died", 8: "Swimming the boys out", 9: "So, rescuers tried something crazy",
         10: "They knocked the boys out", 11: "strapped diving masks", 12: "and carried them through the flooded tunnels",
         13: "And after 18 days underground", 14: "all 12 boys and their coach made it out alive"}
END_VO = 2436
beats = json.load(open(BIN))
old_end = sc.frame_end
AN = sorted([(b["frame"], VO[b["beat"]]) for b in beats]) + [(old_end + 1, END_VO + 1)]
def warp(x):
    if x <= AN[0][0]: return AN[0][1] + (x - AN[0][0])
    for (a0, b0), (a1, b1) in zip(AN, AN[1:]):
        if x <= a1: return b0 + (x - a0) * (b1 - b0) / (a1 - a0)
    return AN[-1][1] + (x - AN[-1][0])
for act in bpy.data.actions:
    for layer in getattr(act, "layers", []):
        for strip in layer.strips:
            for cb in getattr(strip, "channelbags", []):
                for fc in cb.fcurves:
                    for kp in fc.keyframe_points:
                        kp.co.x = warp(kp.co.x); kp.handle_left.x = warp(kp.handle_left.x); kp.handle_right.x = warp(kp.handle_right.x)
                    fc.update()
sc.frame_start, sc.frame_end = 1, END_VO
for b in beats:
    b["frame_cut"] = b["frame"]; b["frame"] = VO[b["beat"]]; b["vo_words"] = WORDS[b["beat"]]
json.dump(beats, open(BOUT, "w"), indent=1)
print("VO_RATIOS", [(a0, b0, round((b1 - b0) / (a1 - a0), 2)) for (a0, b0), (a1, b1) in zip(AN, AN[1:])])
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("V009_VO_OK end", END_VO)
