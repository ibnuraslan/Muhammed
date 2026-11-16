"""Phase 2: cut the P1 build (every shot animated at 1x in its own range) to the VO frames WITHOUT time-stretching.
blender -b p1_build.blend --python 05_vo_cut.py -- <vo.mp3> <out.blend> <beats.json>
For every kept shot, the keys in [P1 start, P1 start + VO length - 1] are shifted (never scaled) to the shot's VO start frame,
with the evaluated value keyed at both ends so each shot starts and ends exactly as it played in P1. Dropped shots disappear.
Markers (hard cuts) are rebuilt on the VO frames, the VO is added to the sequencer, the frame range is set."""
import bpy, sys, json
a = sys.argv[sys.argv.index("--") + 1:]
VO, OUT, BEATS = a
HERE = "/home/user/Muhammed/blender/BalconyToddler_v002/scripts"
exec(open(HERE + "/shots.py").read())
sc = bpy.context.scene
P1 = {sid: (f0, f1) for sid, f0, f1 in layout()}
CUT = vo_layout()
segs = []          # (p0, pe, d)
for sid, n0, n1, w in CUT:
    p0, p1 = P1[sid]; L = n1 - n0 + 1
    assert L <= p1 - p0 + 1, ("shot longer than its 1x animation", sid)
    segs.append((p0, p0 + L - 1, n0 - p0))

def channelbags(act):
    for lay in getattr(act, "layers", []):
        for st in lay.strips:
            for cb in getattr(st, "channelbags", []):
                yield cb
    if hasattr(act, "fcurves") and not hasattr(act, "layers"):
        yield act

n_fc = 0
for act in bpy.data.actions:
    for cb in channelbags(act):
        for fc in cb.fcurves:
            old = [(k.co.x, k.co.y, k.interpolation) for k in fc.keyframe_points]
            if not old: continue
            new = {}
            for p0, pe, d in segs:
                ks = [(x, y, it) for x, y, it in old if p0 - 1e-3 <= x <= pe + 1e-3]
                for x, y, it in ks: new[round(x + d, 3)] = (y, it)
                for b in (p0, pe):
                    if round(b + d, 3) not in new: new[round(b + d, 3)] = (fc.evaluate(b), 'BEZIER')
            fc.keyframe_points.clear()
            fc.keyframe_points.add(len(new))
            for k, (x, (y, it)) in zip(fc.keyframe_points, sorted(new.items())):
                k.co = (x, y); k.interpolation = it; k.handle_left_type = k.handle_right_type = 'AUTO_CLAMPED'
            fc.update(); n_fc += 1
print("CUT fcurves", n_fc)

cams = {m.name[1:]: m.camera for m in sc.timeline_markers}
sc.timeline_markers.clear()
for sid, n0, n1, w in CUT:
    mk = sc.timeline_markers.new("S" + sid, frame=n0); mk.camera = cams[sid]
sc.frame_start = 1; sc.frame_end = VO_END; sc.camera = cams[CUT[0][0]]
# shots that were dropped: remove their cameras and catchlights
keep = {c[0] for c in CUT}
for sid, cam in cams.items():
    if sid not in keep:
        for ch in list(cam.children): bpy.data.objects.remove(ch, do_unlink=True)
        bpy.data.objects.remove(cam, do_unlink=True)
# the VO on the sequencer (packed), so the farm render and previews carry the timing reference
if not sc.sequence_editor: sc.sequence_editor_create()
se = sc.sequence_editor
strips = se.strips if hasattr(se, "strips") else se.sequences
snd = strips.new_sound("VO", VO, 2, 1)
snd.sound.pack() if hasattr(snd.sound, "pack") else None
sc.render.use_sequencer = False      # render the 3D scene, the VO is a reference track
json.dump([{"beat": sid, "frame": n0, "first_words": w} for sid, n0, n1, w in CUT], open(BEATS, "w"), indent=1)
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("CUT_OK", OUT, sc.frame_start, sc.frame_end, len(CUT), "shots")
