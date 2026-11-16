"""Edit the master timeline to the VO with hard cuts, at 1x (no time-stretch): every VO shot [v0, v1] takes the master
frames [m0, m0 + v1 - v0] of its shot. Every fcurve of every action is rebuilt: keys inside each slice are copied (shifted),
and the slice ends get keys sampled from the master curve (vector handles, so nothing overshoots across a cut).
blender -b cams.blend --python 05_edit.py -- vo.mp3 out.blend beats.json"""
import bpy, sys, json
a = sys.argv[sys.argv.index("--") + 1:]; VO, OUT, BEATS = a[0], a[1], a[2]
sc = bpy.context.scene
# (shot, v0, v1, m0)  VO frames = 1 + round(seconds * 60); film end = last word + 0.5 s
SEG = [("S01", 1, 80, 1), ("S02", 81, 155, 101), ("S03", 156, 255, 241), ("S04", 256, 348, 341), ("S05", 349, 468, 441),
       ("S06", 469, 536, 590), ("S07", 537, 620, 711), ("S08", 621, 700, 831), ("S09", 701, 809, 951), ("S10", 810, 930, 1111),
       ("S11", 931, 1006, 1281), ("S12", 1007, 1080, 1491), ("S13", 1081, 1133, 1611), ("S14", 1134, 1200, 1731),
       ("S15", 1201, 1273, 1851), ("S16", 1274, 1360, 1941), ("S17", 1361, 1440, 2031), ("S18", 1441, 1531, 2151),
       ("S19", 1532, 1600, 2271), ("S20", 1601, 1681, 2391), ("S22", 1682, 1739, 2621), ("S23", 1740, 1842, 2711),
       ("S24", 1843, 1918, 2831), ("S25", 1919, 2038, 2951), ("S26", 2039, 2113, 3071)]
END = SEG[-1][2]
for (s, v0, v1, m0), (_, w0, _, _) in zip(SEG, SEG[1:]): assert w0 == v1 + 1, s
cams = {m.name: m.camera for m in sc.timeline_markers}
for s, v0, v1, m0 in SEG:   # each slice must sit inside its master shot
    mk = sorted(sc.timeline_markers, key=lambda m: m.frame); i = [m.name for m in mk].index(s)
    mend = mk[i + 1].frame - 1 if i + 1 < len(mk) else sc.frame_end
    assert mk[i].frame <= m0 and m0 + (v1 - v0) <= mend, (s, m0, v1 - v0, mk[i].frame, mend)
def fcurves():
    for act in bpy.data.actions:
        for layer in getattr(act, "layers", []):
            for strip in layer.strips:
                for cb in getattr(strip, "channelbags", []):
                    for fc in cb.fcurves: yield fc
n_fc = n_k = 0
for fc in list(fcurves()):
    old = [(tuple(k.co), tuple(k.handle_left), tuple(k.handle_right), k.interpolation, k.handle_left_type, k.handle_right_type) for k in fc.keyframe_points]
    if not old: continue
    new = []
    for s, v0, v1, m0 in SEG:
        m1 = m0 + (v1 - v0); d = v0 - m0
        new.append(((v0, fc.evaluate(m0)), None, None, 'BEZIER', 'VECTOR', 'VECTOR'))
        for co, hl, hr, ip, tl, tr in old:
            if m0 < co[0] < m1:
                new.append(((co[0] + d, co[1]), (hl[0] + d, hl[1]), (hr[0] + d, hr[1]), ip, tl, tr))
        if v1 > v0: new.append(((v1, fc.evaluate(m1)), None, None, 'BEZIER', 'VECTOR', 'VECTOR'))
    fc.keyframe_points.clear(); fc.keyframe_points.add(len(new))
    for kp, (co, hl, hr, ip, tl, tr) in zip(fc.keyframe_points, new):
        kp.co = co; kp.interpolation = ip
        kp.handle_left_type = tl; kp.handle_right_type = tr
        if hl is not None: kp.handle_left = hl; kp.handle_right = hr
    fc.update(); n_fc += 1; n_k += len(new)
for m in list(sc.timeline_markers): sc.timeline_markers.remove(m)
for s, v0, v1, m0 in SEG:
    mk = sc.timeline_markers.new(s, frame=v0); mk.camera = cams[s]
sc.frame_start, sc.frame_end = 1, END
se = sc.sequence_editor or sc.sequence_editor_create()
for st in list(se.strips): se.strips.remove(st)
snd = se.strips.new_sound("VO", VO, channel=1, frame_start=1)
words = json.load(open(VO.rsplit(".", 1)[0] + ".words.json"))
def first_words(v0, v1):
    ws = [w[2] for w in words if v0 <= 1 + round(w[0] * 60) <= v1]
    return " ".join(ws[:6])
json.dump([{"beat": s, "frame": v0, "end": v1, "master_from": m0, "first_words": first_words(v0, v1)} for s, v0, v1, m0 in SEG],
          open(BEATS, "w"), indent=1)
sc.camera = cams["S01"]
print("EDIT fcurves", n_fc, "keys", n_k, "end", END)
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
