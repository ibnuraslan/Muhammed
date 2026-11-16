"""Phase 2: trim the P1 shot clips to the VO word frames (1x, never stretched), bake ONE camera with hard-cut keys,
add the VO, write beats.json.   blender -b work/look.blend -P 06_to_vo.py -- <vo.mp3> <out.blend> <beats.json>
Each kept shot = P1 clip frames [p0+offset, p0+offset+dur-1] moved to [new_f0, new_f0+dur-1]."""
import bpy, sys, os, json
from mathutils import Matrix
a = sys.argv[sys.argv.index("--") + 1:]; VO, OUT, BEATS = a
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sc = bpy.context.scene; OB = bpy.data.objects
P1 = {s["name"].split("_")[0]: s for s in json.load(open(os.path.join(HERE, "shots.json")))}
# (shot, new_f0, dur, offset into the P1 clip, beat, first words)
PLAN = [("S01", 1, 138, 0, "B1", "He found a dying crocodile on the riverbank"),
        ("S03", 139, 56, 0, "B2", "and brought it home"),
        ("S04", 195, 105, 0, "B3", "to treat its injuries"),
        ("S05", 300, 128, 0, "B4", "For six months, he secretly kept it"),
        ("S06", 428, 114, 0, "B4", "in a pond behind his house"),
        ("S07", 542, 115, 40, "B5", "feeding it around nine pounds of meat"),
        ("S08", 657, 81, 0, "B5", "every day"),
        ("S09", 738, 78, 0, "B6", "He even slept beside it"),
        ("S10", 816, 170, 0, "B6", "because he believed affection would help it recover"),
        ("S11", 986, 171, 0, "B7", "When he finally tried releasing it back into the wild"),
        ("S12", 1157, 135, 0, "B7", "the crocodile refused to leave"),
        ("S13", 1292, 78, 100, "B8", "Instead, it stayed with him"),
        ("S14", 1370, 118, 0, "B8", "for more than 20 years"),
        ("S16", 1488, 105, 0, "B9", "They even performed shows together"),
        ("S18", 1593, 104, 0, "B10", "and when the crocodile died"),
        ("S19", 1697, 88, 0, "B11", "the man held a public funeral"),
        ("S20", 1785, 111, 0, "B11", "and sang for his friend")]
FRAME_END = 1895
WIN = []  # (old_a, old_b, delta)
for n, f0, dur, off, *_ in PLAN:
    oa = P1[n]["f0"] + off; ob = oa + dur - 1
    assert ob <= P1[n]["f1"], (n, ob, P1[n]["f1"])
    WIN.append((oa, ob, f0 - oa))
# ---- capture the shot cameras' path BEFORE remapping (sampled every frame of each window)
cam_samples = []
for (n, f0, dur, off, *_), (oa, ob, d) in zip(PLAN, WIN):
    c = OB["CAM_" + P1[n]["name"]]
    for f in range(oa, ob + 1):
        sc.frame_set(f); cam_samples.append((f + d, c.matrix_world.copy(), c.data.lens))
# ---- every F-curve in the file (Blender 5 layered actions)
def fcurves():
    for act in bpy.data.actions:
        for L in act.layers:
            for st in L.strips:
                for cb in st.channelbags:
                    for fc in cb.fcurves: yield fc
FCS = list(fcurves()); print("FCURVES", len(FCS))
for fc in FCS:
    kp = fc.keyframe_points
    if not len(kp): continue
    # 1) pin the exact value at every window edge
    edges = []
    for oa, ob, d in WIN: edges += [oa, ob]
    vals = [(f, fc.evaluate(f)) for f in edges]
    interp = {}
    for f, v in vals:
        prev = [k for k in kp if k.co.x <= f]
        it = prev[-1].interpolation if prev else kp[0].interpolation
        k = kp.insert(f, v, options={'FAST'}); k.interpolation = it
    # 2) drop keys outside the windows, shift the rest
    for i in range(len(kp) - 1, -1, -1):
        x = kp[i].co.x; w = next((W for W in WIN if W[0] - 1e-3 <= x <= W[1] + 1e-3), None)
        if w is None: kp.remove(kp[i], fast=True)
    for k in kp:
        x = k.co.x; w = next(W for W in WIN if W[0] - 1e-3 <= x <= W[1] + 1e-3)
        k.co.x += w[2]; k.handle_left.x += w[2]; k.handle_right.x += w[2]
    fc.update()
# ---- one camera, keyed every frame (linear), hard cuts between shots
cd = bpy.data.cameras.new("Camera"); cam = bpy.data.objects.new("Camera", cd); sc.collection.objects.link(cam)
cd.clip_start = 0.05; cd.sensor_width = 36; cd.dof.use_dof = False
for f, M, lens in cam_samples:
    cam.matrix_world = M; cd.lens = lens
    cam.keyframe_insert("location", frame=f); cam.keyframe_insert("rotation_euler", frame=f); cd.keyframe_insert("lens", frame=f)
for act in (cam.animation_data.action, cd.animation_data.action):
    for L in act.layers:
        for st in L.strips:
            for cb in st.channelbags:
                for fc in cb.fcurves:
                    for k in fc.keyframe_points: k.interpolation = 'LINEAR'
sc.camera = cam
for m in list(sc.timeline_markers): sc.timeline_markers.remove(m)
# catchlight: one, on the single camera (light-linked to the eyes)
catch = [o for o in OB if o.name.startswith("Catch_")]
keep = catch[0]; keep.parent = cam; keep.location = (0.15, 0.25, 0.0); keep.name = "Catchlight"
for o in catch[1:]: bpy.data.objects.remove(o)
for o in [o for o in OB if o.name.startswith("CAM_")]: bpy.data.objects.remove(o)
for o in [o for o in OB if o.type == 'CAMERA' and o is not cam]: bpy.data.objects.remove(o)
# ---- VO + range
sc.sequence_editor_create()
st = sc.sequence_editor.strips.new_sound("VO", VO, 2, 1)
sc.frame_start, sc.frame_end = 1, FRAME_END
sc.render.fps = 60; sc.render.fps_base = 1.0
json.dump([{"beat": b, "shot": n, "frame": f0, "first_words": w} for n, f0, dur, off, b, w in PLAN], open(BEATS, "w"), indent=1)
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("VO_DONE", sc.frame_start, sc.frame_end, "cams", [o.name for o in OB if o.type == 'CAMERA'])
