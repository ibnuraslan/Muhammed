"""v006e retime (director, Nov 15): shorten the end so beat 8 (sky) is 1 s and beat 9 (airport) follows right after.
   target frame t  <- source frame
   t <= 1158       <- t            (cabin, incl. the new beat-7 shot 1069-1158)
   1159 .. 1218    <- t + 152      (sky: source 1311-1370, the plane over the clouds)
   1219 .. 1446    <- t + 174      (airport: source 1393-1620)
Every animation curve in the file is resampled after 1158 as per-frame CONSTANT keys (exact values, hard cuts between sets),
and a constant key at 1158 holds the cabin pose until the cut.
blender -b film.blend --python 07_retime.py -- <out.blend>"""
import sys, bpy
OUT = sys.argv[sys.argv.index("--") + 1]
T0, T_SKY, T_AIR, T_END = 1158, 1159, 1219, 1446
def src(t):
    return t if t <= T0 else (t + 152 if t < T_AIR else t + 174)
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

n_fc = n_keys = 0
for fc in list(all_fcurves()):
    if not fc.keyframe_points or fc.keyframe_points[-1].co.x <= T0: continue
    vals = [(t, fc.evaluate(src(t))) for t in range(T_SKY, T_END + 1)]
    hold = fc.evaluate(T0)
    # drop every key after T0
    kp = fc.keyframe_points
    for i in range(len(kp) - 1, -1, -1):
        if kp[i].co.x > T0: kp.remove(kp[i], fast=True)
    k = kp.insert(T0, hold, options={'FAST'}); k.interpolation = 'CONSTANT'
    base = len(kp); kp.add(len(vals))
    for j, (t, v) in enumerate(vals):
        p = kp[base + j]; p.co = (t, v); p.handle_left = (t - 0.3, v); p.handle_right = (t + 0.3, v); p.interpolation = 'CONSTANT'
    fc.update()
    n_fc += 1; n_keys += len(vals)
sc.frame_end = T_END
print("RETIMED", n_fc, "fcurves", n_keys, "keys; frame_end", sc.frame_end)
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print("RETIME_SAVED", OUT)
