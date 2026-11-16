"""Cut the 1x clips to the VO: each shot takes a 1x sub-range of its clip (no time-stretch).
blender -b look.blend --python 05_vo_cut.py -- out.blend segs.json vo.mp3
segs.json: [[shot, n0, n1, c0], ...] new frames n0..n1 show clip frames c0..c0+(n1-n0)."""
import bpy, sys, json
a = sys.argv[sys.argv.index("--") + 1:]; OUT, SEGS, VO = a[0], a[1], a[2]
S = json.load(open(SEGS)); sc = bpy.context.scene
seg = [(n0, n1, c0, c0 + (n1 - n0)) for _, n0, n1, c0 in S]
for i in range(len(seg) - 1):
    assert seg[i][3] < seg[i + 1][2] and seg[i][1] + 1 == seg[i + 1][0], seg[i]

def fcurves(act):
    out = list(getattr(act, "fcurves", []) or [])
    for layer in getattr(act, "layers", []):
        for strip in layer.strips:
            for cb in getattr(strip, "channelbags", []): out += list(cb.fcurves)
    return out

def remap(c):
    for n0, n1, c0, c1 in seg:
        if c0 <= c <= c1: return c - c0 + n0
    return None

nk = 0
for act in bpy.data.actions:
    for fc in fcurves(act):
        kp = fc.keyframe_points
        if not len(kp): continue
        const = all(k.interpolation == 'CONSTANT' for k in kp)
        vals = {}
        for n0, n1, c0, c1 in seg:
            for c in (c0, c1): vals[c] = fc.evaluate(c)
        for c, v in vals.items():
            k = kp.insert(c, v, options={'FAST'})
            if const: k.interpolation = 'CONSTANT'
        for i in range(len(kp) - 1, -1, -1):
            if remap(round(kp[i].co.x, 3)) is None and not any(c0 <= kp[i].co.x <= c1 for _, _, c0, c1 in seg): kp.remove(kp[i], fast=True)
        for k in kp:
            c = k.co.x
            for n0, n1, c0, c1 in seg:
                if c0 - 1e-3 <= c <= c1 + 1e-3:
                    d = n0 - c0; k.co.x += d; k.handle_left.x += d; k.handle_right.x += d; break
        fc.update(); nk += 1
# markers -> new shot starts (one per shot, bound to its camera)
cams = {m.name: m.camera for m in sc.timeline_markers}
for m in list(sc.timeline_markers): sc.timeline_markers.remove(m)
for shot, n0, n1, c0 in S:
    m = sc.timeline_markers.new(shot, frame=n0); m.camera = cams[shot]
sc.frame_start, sc.frame_end = 1, seg[-1][1]
# VO on the sequencer
if not sc.sequence_editor: sc.sequence_editor_create()
se = sc.sequence_editor
strips = se.strips if hasattr(se, "strips") else se.sequences
for s_ in list(strips): strips.remove(s_)
snd = strips.new_sound("VO", VO, 1, 1)

print("VO_CUT fcurves", nk, "frames", sc.frame_start, sc.frame_end, "markers", len(sc.timeline_markers))
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
