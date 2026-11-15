"""v009 (director reviews of v008). Runs on the v009 long timeline (v008 plus more divers on the line, a longer death
beat and the long tow, all real 1x animation), re-frames, then removes the faulty frames. 23_v009_vo.py then places
each beat on the client's VO frame; the source lengths are chosen so character beats play at ~1x.
Camera:
- 732-905 chamber: a slow push-in on the boys waiting on the ledge (their heads turn), instead of the static wide.
- 1528-1594: the low frontal medium on the boy and the kneeling divers (was a top-down where tanks merged).
- 1595-1635 and 1711-1764: the edge boy's face reacting; 1636-1710: close-up of the syringe at the boy's upper arm.
- 1769-1845: close-up of the boy's face as the mask goes on (diver hands at the rim).
- 1900-2119: the tow, a steady side track on the diver and the boy at the same offset as the approved v007 shot.
Cuts: 383-390 rock, 549-561 fade, 712-731, 906-918 water blur, 1176-1315 surfacing blur + dark far shot,
1457-1466, 1765-1768, 1846-1899 dive murk, 2201-2211 and 2281-2301 blurred passes, 2237-2257 stretcher end
through the carrier.
blender -b in.blend --python 22_v009_edit.py -- out.blend beats_in.json beats_out.json"""
import bpy, sys, json
from mathutils import Vector as V
a = sys.argv[sys.argv.index("--") + 1:]; OUT, BIN, BOUT = a[0], a[1], a[2]
sc = bpy.context.scene; cam = sc.camera; aim = cam.constraints[0].target; CX = 400.0
def fcs(o, path):
    ad = o.animation_data
    return sorted([fc for lay in ad.action.layers for st in lay.strips for cb in st.channelbags for fc in cb.fcurves if fc.data_path == path], key=lambda f: f.array_index)
CL, AL = fcs(cam, "location"), fcs(aim, "location"); LF = fcs(cam.data, "lens")
def ev(F, f): return V([fc.evaluate(f) for fc in F])
def setk(F, f, vals):
    for i, fc in enumerate(F):
        v = vals[i]
        ks = [k for k in fc.keyframe_points if int(round(k.co.x)) == f]
        if ks: ks[0].co.y = v; ks[0].handle_left.y = v; ks[0].handle_right.y = v; ks[0].interpolation = 'LINEAR'
        else: fc.keyframe_points.insert(f, v).interpolation = 'LINEAR'
SHOTS = []
def shot(f0, f1, fn):
    SHOTS.append((f0, f1, fn))
def ss(t): t = max(0.0, min(1.0, t)); return t * t * (3 - 2 * t)
# chamber push-in
c0, a0, l0 = ev(CL, 800), ev(AL, 800), LF[0].evaluate(800)
shot(732, 905, lambda f: (c0.lerp(a0, 0.5 * ss((f - 732) / 173)), a0 + V((0, 0, 0.15 * ss((f - 732) / 173))), l0 + 6 * ss((f - 732) / 173)))
# frontal medium on the kneeling group
shot(1528, 1594, lambda f: (V((CX + 0.48, -0.59 - 0.1 * (f - 1528) / 66, 0.8)), V((CX + 0.68, 0.95, 0.83)), 36))
b2 = bpy.data.objects["Boy2"]
def face(f):
    sc.frame_set(f); hb = b2.pose.bones["head"]
    return (b2.matrix_world @ hb.head).lerp(b2.matrix_world @ hb.tail, 0.45)
DIR = V((-0.28, -1.57, -0.01)).normalized()
# reaction: the edge boy's face, framing taken from the approved close-up (1370)
cr, ar, lr = ev(CL, 1370), ev(AL, 1370), LF[0].evaluate(1370)
shot(1595, 1635, lambda f: (cr + (ar - cr) * 0.04 * (f - 1595) / 40, ar, lr))
shot(1711, 1764, lambda f: (cr + (ar - cr) * 0.04 * (f - 1711) / 53, ar, lr))
shot(1636, 1710, lambda f: (face(f) + DIR * (0.85 - 0.08 * (f - 1636) / 74) + V((0, 0, 0.03)), face(f) - V((0, 0, 0.13)), 38))
shot(1769, 1845, lambda f: (face(f) + DIR * (0.7 - 0.08 * (f - 1769) / 76) + V((0, 0, 0.03)), face(f) - V((0, 0, 0.02)), 40))
# tow: steady track at the approved v007 offset (frame 1959 here) from the pair
db = bpy.data.objects["DiverB"]
def pair(f):
    sc.frame_set(f)
    return ((db.matrix_world @ db.pose.bones["root"].head) + (b2.matrix_world @ b2.pose.bones["root"].head)) / 2
P0 = pair(1959); rc, ra, rl = ev(CL, 1959) - P0, ev(AL, 1959) - P0, LF[0].evaluate(1959)
shot(1900, 2119, lambda f: (pair(f) + rc, pair(f) + ra, rl))
for f0, f1, fn in SHOTS:
    vals = {f: fn(f) for f in range(f0, f1 + 1)}
    for f, (c, t, l) in vals.items():
        setk(CL, f, c); setk(AL, f, t); setk(LF, f, [l])
    for F in (CL, AL, LF):
        for fc in F: fc.update()
CUT = [(383, 390), (549, 561), (712, 731), (906, 918), (1176, 1315), (1457, 1466), (1765, 1768), (1846, 1899), (2201, 2211), (2237, 2257), (2281, 2301)]
END0 = sc.frame_end
KEEP = []; s0 = 1
for c0_, c1_ in CUT:
    KEEP.append((s0, c0_ - 1)); s0 = c1_ + 1
KEEP.append((s0, END0))
AN = []
for o0, o1 in KEEP:
    n0 = 1 if not AN else AN[-1][1] + 1
    AN += [(o0, n0), (o1, n0 + (o1 - o0))]
def warp(x):
    if x <= AN[0][0]: return AN[0][1] + (x - AN[0][0])
    for (a_, b_), (a1, b1) in zip(AN, AN[1:]):
        if x <= a1: return b_ + (x - a_) * (b1 - b_) / (a1 - a_)
    return AN[-1][1] + (x - AN[-1][0])
def wkey(x):
    for c0_, c1_ in CUT:
        if c0_ <= x <= c1_: return warp(c1_ + 1)
    return warp(x)
for act in bpy.data.actions:
    for layer in getattr(act, "layers", []):
        for strip in layer.strips:
            for cb in getattr(strip, "channelbags", []):
                for fc in cb.fcurves:
                    for kp in fc.keyframe_points:
                        kp.co.x = warp(kp.co.x); kp.handle_left.x = warp(kp.handle_left.x); kp.handle_right.x = warp(kp.handle_right.x)
                    fc.update()
END = AN[-1][1]; sc.frame_start, sc.frame_end = 1, END
beats = json.load(open(BIN))
for b in beats:
    src = 330 if b["beat"] == 2 else b["frame"]          # beat 2's VO line lands as the rain starts; the walk-in runs on to it
    b["frame_long"] = src; b["frame"] = int(round(wkey(src)))
json.dump(beats, open(BOUT, "w"), indent=1)
print("V009 end", END, "beats", [(b["beat"], b["frame"]) for b in beats])
print("CUTS_NEW", [int(round(warp(c0_ - 1))) for c0_, c1_ in CUT])
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("V009_EDIT_OK")
