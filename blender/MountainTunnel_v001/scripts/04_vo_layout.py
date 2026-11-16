"""Place each built clip on its VO window by TRIMMING (never stretching): keys inside [B0, B0+L-1] of the build timeline
move to [V0, V0+L-1]; keys after B0+L-1 are dropped (a boundary key holds the value at the trim point).
blender -b build.blend --python 04_vo_layout.py -- shots_build.json shots_vo.json out.blend vo.mp3 frame_end"""
import bpy, sys, json
a = sys.argv[sys.argv.index("--") + 1:]
B = {s["id"]: s for s in json.load(open(a[0]))}; VO = json.load(open(a[1])); OUT, MP3, FEND = a[2], a[3], int(a[4])
sc = bpy.context.scene
W = []                                    # (b0, b1_build, keep_len, v0)
for s in VO:
    b = B[s["id"]]; W.append((b["f0"], b["f0"] + b["len"] - 1, s["len"], s["f0"], s["id"]))
def win(x):
    for w in W:
        if w[0] - 0.5 <= x <= w[1] + 0.5: return w
    return None
def fcurves(idb):
    ad = getattr(idb, "animation_data", None)
    if not ad or not ad.action: return []
    out = []
    for layer in getattr(ad.action, "layers", []):
        for strip in layer.strips:
            for cb in strip.channelbags: out.extend(cb.fcurves)
    return out
ids = list(bpy.data.objects) + list(bpy.data.cameras) + list(bpy.data.lights) + list(bpy.data.curves) + list(bpy.data.node_groups) + \
      [m.node_tree for m in bpy.data.materials if m.node_tree] + [k for k in bpy.data.shape_keys]
nf = nk = 0
SEEN = set()          # Blender 5 slotted actions: an object and its data can share one action -> remap each F-curve once
for idb in ids:
    for fc in fcurves(idb):
        if fc.as_pointer() in SEEN: continue
        SEEN.add(fc.as_pointer())
        pts = [(kp.co.x, kp.co.y, kp.interpolation) for kp in fc.keyframe_points]
        new = {}
        for w in W:
            b0, b1, L, v0, sid = w
            inside = [(x, y, it) for x, y, it in pts if b0 - 0.5 <= x <= b0 + L - 1 + 0.5]
            touches = any(b0 - 0.5 <= x <= b1 + 0.5 for x, _, _ in pts)
            if not touches: continue
            for x, y, it in inside: new[round(x - b0 + v0, 3)] = (y, it)
            xe = b0 + L - 1
            if not any(abs(x - xe) < 0.01 for x, _, _ in inside):
                it = 'CONSTANT' if any(it_ == 'CONSTANT' for _, _, it_ in pts) else 'BEZIER'
                new[float(v0 + L - 1)] = (fc.evaluate(xe), it)
            if not any(abs(x - b0) < 0.01 for x, _, _ in inside):
                it = 'CONSTANT' if any(it_ == 'CONSTANT' for _, _, it_ in pts) else 'BEZIER'
                new[float(v0)] = (fc.evaluate(b0), it)
        # keys outside every window (e.g. frame-1 initial hides) keep their frame
        for x, y, it in pts:
            if win(x) is None and x < W[0][0] + 0.5: new.setdefault(x, (y, it))
        while fc.keyframe_points: fc.keyframe_points.remove(fc.keyframe_points[0], fast=True)
        for x in sorted(new):
            y, it = new[x]; kp = fc.keyframe_points.insert(x, y, options={'FAST'}); kp.interpolation = it
        fc.update(); nf += 1; nk += len(new)
# markers: one per shot at its VO frame
cams = {}
for m in list(sc.timeline_markers):
    w = win(m.frame)
    if w and abs(m.frame - w[0]) < 1: cams[w[4]] = m.camera
    sc.timeline_markers.remove(m)
for s in VO:
    m = sc.timeline_markers.new("S" + s["id"], frame=s["f0"]); m.camera = cams[s["id"]]
sc.camera = cams[VO[0]["id"]]
# props whose last visible key fell on a trimmed tail: force hidden right after their window
SEEN2 = set()
for o in bpy.data.objects:
    for fc in fcurves(o):
        if fc.data_path not in ("hide_render", "hide_viewport") or fc.as_pointer() in SEEN2: continue
        SEEN2.add(fc.as_pointer())
        for w in W:
            b0, b1, L, v0, sid = w
            e = v0 + L
            if fc.evaluate(e - 1) < 0.5 and not any(abs(kp.co.x - e) < 0.01 for kp in fc.keyframe_points):
                # visible at the end of this window: hide unless the next window shows it again at its first frame anyway
                kp = fc.keyframe_points.insert(e, 1.0, options={'FAST'}); kp.interpolation = 'CONSTANT'
        fc.update()
sc.frame_start = 1; sc.frame_end = FEND
if not sc.sequence_editor: sc.sequence_editor_create()
for st in list(sc.sequence_editor.strips_all if hasattr(sc.sequence_editor, "strips_all") else sc.sequence_editor.sequences_all): pass
snd = bpy.data.sounds.load(MP3, check_existing=True)
try: sc.sequence_editor.strips.new_sound("VO", MP3, 1, 1)
except AttributeError: sc.sequence_editor.sequences.new_sound("VO", MP3, 1, 1)
sc.render.ffmpeg.audio_codec = 'AAC'
print("LAYOUT_OK fcurves", nf, "keys", nk, "markers", len(sc.timeline_markers))
sc.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
