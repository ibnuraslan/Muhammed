"""Phase 2: lay the 1x P1 clips onto the VO word frames by TRIM + SHIFT only (no time scaling).
For every shot in timing.VO_BEATS the window [P1 start + TRIM, + length - 1] of the P1 timeline is moved to
[VO start, VO end]. Every F-curve of every action (rigs, copies, cameras, lights, world, fire clocks, visibility) gets
boundary keys at the window edges (evaluated values), keeps its keys inside the window, and drops everything else.
Markers bind the cameras at the VO starts; the VO mp3 is added to the sequencer and packed.
blender -b anim_p1.blend --python 05_vo.py -- <vo.mp3> <out.blend>"""
import sys, os, json
import bpy
HERE = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(HERE, "timing.py")).read())
a = sys.argv[sys.argv.index("--") + 1:]
VO, OUT = a[0], a[1]
sc = bpy.context.scene

WIN = []   # (old0, old1, shift, shot)
for n, _, _, _ in VO_BEATS:
    L = vo_end(n) - VO_START[n] + 1
    o0 = START[n] + VO_TRIM[n]; o1 = o0 + L - 1
    assert o1 <= shot_end(n), n
    WIN.append((o0, o1, VO_START[n] - o0, n))

def fcurves_of(act):
    out = []
    try: out += list(act.fcurves)
    except Exception: pass
    try:
        for L_ in act.layers:
            for st in L_.strips:
                for cb in st.channelbags: out += list(cb.fcurves)
    except Exception: pass
    return out

def remap(fc):
    kps = list(fc.keyframe_points)
    if not kps: return
    old = [(k.co.x, k.co.y, k.interpolation, tuple(k.handle_left), tuple(k.handle_right), k.handle_left_type, k.handle_right_type) for k in kps]
    def interp_at(x):
        prev = None
        for k in old:
            if k[0] <= x: prev = k
            else: break
        return prev[2] if prev else old[0][2]
    new = []
    for o0, o1, d, _ in WIN:
        v0 = fc.evaluate(o0); v1 = fc.evaluate(o1)
        new.append((o0 + d, v0, interp_at(o0), None))
        for k in old:
            if o0 < k[0] < o1:
                new.append((k[0] + d, k[1], k[2], (k[3][0] + d, k[3][1], k[4][0] + d, k[4][1], k[5], k[6])))
        if o1 > o0: new.append((o1 + d, v1, interp_at(o1), None))
    while len(fc.keyframe_points): fc.keyframe_points.remove(fc.keyframe_points[0], fast=True)
    fc.keyframe_points.add(len(new))
    for kp, (x, y, ip, h) in zip(fc.keyframe_points, new):
        kp.co = (x, y); kp.interpolation = ip
        if h is None:
            kp.handle_left_type = kp.handle_right_type = 'AUTO_CLAMPED'
        else:
            kp.handle_left_type, kp.handle_right_type = 'FREE', 'FREE'
            kp.handle_left = (h[0], h[1]); kp.handle_right = (h[2], h[3])
    fc.update()

done = set(); n_fc = 0
colls = [bpy.data.objects, bpy.data.meshes, bpy.data.lights, bpy.data.cameras, bpy.data.materials, bpy.data.worlds,
         bpy.data.node_groups, bpy.data.shape_keys, bpy.data.scenes, bpy.data.armatures]
for coll in colls:
    for idb in coll:
        trees = [idb]
        if getattr(idb, "node_tree", None) is not None: trees.append(idb.node_tree)
        for t in trees:
            ad = getattr(t, "animation_data", None)
            if not ad or not ad.action or ad.action.name in done: continue
            done.add(ad.action.name)
            for fc in fcurves_of(ad.action):
                remap(fc); n_fc += 1
print("REMAPPED actions", len(done), "fcurves", n_fc)

# markers / cameras / range
sc.timeline_markers.clear()
for o0, o1, d, n in WIN:
    m = sc.timeline_markers.new(n, frame=VO_START[n]); m.camera = bpy.data.objects["CAM_" + n]
sc.frame_start = 1; sc.frame_end = VO_END
sc.camera = bpy.data.objects["CAM_S01"]
sc["SHOTS_JSON"] = json.dumps([[n, VO_START[n], vo_end(n)] for n, _, _, _ in VO_BEATS])
# the VO
if not sc.sequence_editor: sc.sequence_editor_create()
se = sc.sequence_editor
strips = se.strips if hasattr(se, "strips") else se.sequences
for s_ in list(strips): strips.remove(s_)
snd = strips.new_sound("VO", VO, 1, 1)
try: snd.sound.pack()
except Exception as e: print("SOUNDPACK", e)
sc.render.ffmpeg.audio_codec = 'AAC'
beats = [{"beat": n, "frame": VO_START[n], "first_words": w} for n, _, w, _ in VO_BEATS]
json.dump(beats, open(os.path.join(os.path.dirname(OUT), "beats.json"), "w"), indent=1)
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("VO_DONE", sc.frame_start, sc.frame_end)
