"""v009 (director review of v008). Runs on the v008-timeline package, then cuts.
- Injection (1525-1600) and mask fit (1700-1775): close-ups on the boy's face and shoulder from the low front-right
  (the only line clear of the divers' bodies): the syringe at his upper arm, then the mask going onto his face. The
  long frozen group shot (1458-1524, 1601-1699) is cut.
- Cuts (hard cuts onto readable shots): 383-390 rock, 549-561 fade to dark, 733-765 gear bag in the lens,
  830-925 static wide + blurred water, 1143-1230 surfacing blur + dark far shot, 1458-1524 top-down, 1601-1699,
  1840-1908 boulder + murk, 1990-2000 and 2070-2090 blurred passes, 2026-2046 stretcher end crossing the carrier.
blender -b in.blend --python 22_v009_edit.py -- out.blend beats_v008.json beats_v009.json"""
import bpy, sys, json
from mathutils import Vector as V
a = sys.argv[sys.argv.index("--") + 1:]; OUT, BIN, BOUT = a[0], a[1], a[2]
sc = bpy.context.scene; cam = sc.camera; aim = cam.constraints[0].target
def fcs(o, path):
    ad = o.animation_data
    return sorted([fc for lay in ad.action.layers for st in lay.strips for cb in st.channelbags for fc in cb.fcurves if fc.data_path == path], key=lambda f: f.array_index)
CL, AL = fcs(cam, "location"), fcs(aim, "location"); LF = fcs(cam.data, "lens")
def setk(F, f, vals):
    for i, fc in enumerate(F):
        v = vals[i]
        ks = [k for k in fc.keyframe_points if int(round(k.co.x)) == f]
        if ks: ks[0].co.y = v; ks[0].handle_left.y = v; ks[0].handle_right.y = v; ks[0].interpolation = 'LINEAR'
        else: fc.keyframe_points.insert(f, v).interpolation = 'LINEAR'
b2 = bpy.data.objects["Boy2"]
def face(f):
    sc.frame_set(f); hb = b2.pose.bones["head"]
    return (b2.matrix_world @ hb.head).lerp(b2.matrix_world @ hb.tail, 0.45)
DIR = V((-0.28, -1.57, -0.01)).normalized()
for f0, f1, dist, drop, lens in ((1525, 1600, 0.85, 0.13, 38), (1700, 1775, 0.7, 0.02, 40)):
    for f in range(f0, f1 + 1):
        p = face(f); t = (f - f0) / (f1 - f0)
        d_ = dist - 0.08 * t                                    # a slow push in
        setk(CL, f, p + DIR * d_ + V((0, 0, 0.03))); setk(AL, f, p - V((0, 0, drop))); setk(LF, f, [lens])
    for F in (CL, AL, LF):
        for fc in F: fc.update()
CUT = [(383, 390), (549, 561), (733, 765), (830, 925), (1143, 1230), (1458, 1524), (1601, 1699), (1840, 1908), (1990, 2000), (2026, 2046), (2070, 2090)]
END0 = sc.frame_end
KEEP = []; s0 = 1
for c0, c1 in CUT:
    KEEP.append((s0, c0 - 1)); s0 = c1 + 1
KEEP.append((s0, END0))
AN = []
for o0, o1 in KEEP:
    n0 = 1 if not AN else AN[-1][1] + 1
    AN += [(o0, n0), (o1, n0 + (o1 - o0))]
def warp(x):
    if x <= AN[0][0]: return AN[0][1] + (x - AN[0][0])
    for (a0, b0), (a1, b1) in zip(AN, AN[1:]):
        if x <= a1: return b0 + (x - a0) * (b1 - b0) / (a1 - a0)
    return AN[-1][1] + (x - AN[-1][0])
def wkey(x):     # a frame inside a cut maps to the first frame after it
    for c0, c1 in CUT:
        if c0 <= x <= c1: return warp(c1 + 1)
    return warp(x)
nk = 0
for act in bpy.data.actions:
    for layer in getattr(act, "layers", []):
        for strip in layer.strips:
            for cb in getattr(strip, "channelbags", []):
                for fc in cb.fcurves:
                    for kp in fc.keyframe_points:
                        kp.co.x = warp(kp.co.x); kp.handle_left.x = warp(kp.handle_left.x); kp.handle_right.x = warp(kp.handle_right.x); nk += 1
                    fc.update()
END = AN[-1][1]; sc.frame_start, sc.frame_end = 1, END
beats = json.load(open(BIN))
for b in beats:
    b["frame_v008"] = b["frame"]; b["frame"] = int(round(wkey(b["frame"])))
json.dump(beats, open(BOUT, "w"), indent=1)
print("V009 keys", nk, "end", END, "beats", [(b["beat"], b["frame"]) for b in beats])
print("CUTS_NEW", [int(round(warp(c0 - 1))) for c0, c1 in CUT])
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("V009_EDIT_OK")
