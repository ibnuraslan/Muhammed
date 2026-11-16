"""B14: lay the 1x clips onto the VO word frames (shift only, never stretch character animation), re-window the cameras,
add three extra B4 angles, add the VO, set the frame range.  blender -b work/anim.blend --python 04_vo.py -- out.blend"""
import bpy, sys, math, json
from mathutils import Vector, Matrix
W = "/tmp/claude-0/b14/"; P = "/home/user/Muhammed/blender/pipeline/"
OUT = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene; R_ = math.radians
CUR_WIN = None; RIGS = {}; HUM = {}
exec(open(P + "anim_lib.py").read()); exec(open(P + "hand_poses.py").read())
exec(open(W + "scripts/lib_anim.py").read())
F_END = 1577                      # 0.5 s after the last word ("impossible." ends 25.76 s)

def shift_owner(idb, off):
    ad = getattr(idb, "animation_data", None)
    if not ad or not ad.action: return 0
    n = 0
    for fc in _fcurves(ad.action):
        for k in fc.keyframe_points:
            k.co.x += off; k.handle_left.x += off; k.handle_right.x += off; n += 1
    return n

def shift_objs(objs, off):
    n = 0
    for o in objs:
        n += shift_owner(o, off)
        if o.type == 'ARMATURE': pass
        for m in (getattr(o.data, "materials", []) if o.data else []):
            pass
    return n

ob = bpy.data.objects
groups = {
    "adrenal": ([o for o in ob if o.name.startswith(("Adrenal", "Adr0_", "Adr1_"))], -180),
    "flow": ([o for o in ob if o.name.startswith(("FlowRBC_", "FlowO2_"))], -361),
    "muscle": ([o for o in ob if o.name == "Muscle" or o.name.startswith("MusO2_")], -523),
    "park": ([ob["Man"], ob["LogPivot"]], -661),
}
for k, (objs, off) in groups.items():
    print("SHIFT", k, len(objs), off, shift_objs(objs, off))
m_adr = bpy.data.materials["AdrenalGland"]
print("SHIFT adrenal material", shift_owner(m_adr.node_tree, -180))

# ---- shots on the VO (frame = 1 + round(seconds*60)); words in brackets
SHOTS = [  # name, t0, t1, src_f0, src_f1  (camera keys remapped from the src window to the target window)
    ("Cam1a", 1, 96, 1, 110),        # In 1964,
    ("Cam1b", 97, 245, 111, 260),    # a woman supposedly lifted a car
    ("Cam1c", 246, 319, 261, 380),   # off her trapped son
    ("Cam1d", 320, 401, 381, 470),   # completely by herself.
    ("Cam1e", 402, 486, 471, 600),   # This is often described as
    ("Cam2a", 487, 600, 601, 780),   # hysterical strength.
    ("Cam2b", 601, 712, 781, 1000),  # During extreme stress, the body
    ("Cam2c", 713, 839, 1001, 1200), # releases huge amounts of adrenaline,
    ("Cam3a", 840, 917, 1201, 1440), # increasing blood flow and
    ("Cam3b", 918, 1019, 1441, 1680),# energy to the muscles.
    ("Cam4a", 1020, 1140, 1681, 1880),  # For a very short time, this can
    ("Cam4a2", 1141, 1219, None, None), # allow someone to produce
    ("Cam4b", 1220, 1308, 1881, 2060),  # levels of strength they normally
    ("Cam4b2", 1309, 1399, None, None), # couldn't access, letting the
    ("Cam4c", 1400, 1488, 2061, 2200),  # body perform something that
    ("Cam4c2", 1489, F_END, None, None),# would usually seem impossible.
]
for m in list(sc.timeline_markers): sc.timeline_markers.remove(m)
XG, MY = 79.1, -0.50
man = ob["Man"]
NEW = {"Cam4a2": [(1141, (XG - 1.7, 2.3, 1.05), (XG, -0.3, 0.8)), (1219, (XG - 1.45, 2.0, 1.0), (XG, -0.3, 0.85))],
       "Cam4b2": [(1309, (XG + 0.35, 1.55, 1.38), (XG, MY, 1.28)), (1399, (XG + 0.2, 1.35, 1.36), (XG, MY, 1.3))],
       "Cam4c2": [(1489, (XG - 0.7, 3.0, 1.45), (XG, MY, 1.4)), (F_END, (XG - 0.5, 2.6, 1.42), (XG, MY, 1.42))]}
for name, t0, t1, s0, s1 in SHOTS:
    if s0 is None:
        c = cam_shot(name, t0, t1, NEW[name], lens=34)
        catchlight(man, c, 0, 0)
        continue
    c = ob[name]
    for fc in _fcurves(c.animation_data.action):
        for k in fc.keyframe_points:
            x = t0 + (k.co.x - s0) * (t1 - t0) / (s1 - s0)
            d = x - k.co.x; k.co.x = x; k.handle_left.x += d; k.handle_right.x += d
    if c.data.animation_data and c.data.animation_data.action:
        for fc in _fcurves(c.data.animation_data.action):
            for k in fc.keyframe_points:
                x = t0 + (k.co.x - s0) * (t1 - t0) / (s1 - s0); d = x - k.co.x; k.co.x = x; k.handle_left.x += d; k.handle_right.x += d
    mk = sc.timeline_markers.new(name, frame=t0); mk.camera = c
sc.frame_start, sc.frame_end = 1, F_END
sc.camera = ob["Cam1a"]
# ---- VO
if not sc.sequence_editor: sc.sequence_editor_create()
se = sc.sequence_editor
strips = se.strips if hasattr(se, "strips") else se.sequences
for s_ in list(strips): strips.remove(s_)
snd = strips.new_sound("VO", W + "assets/VO.mp3", 1, 1)
sc.render.ffmpeg.audio_codec = 'AAC'
json.dump([{"beat": n, "frame": t0, "first_words": w} for (n, t0, t1, a, b), w in zip(SHOTS, [
    "In 1964", "a woman supposedly lifted a car", "off her trapped son", "completely by herself", "This is often described as",
    "hysterical strength", "During extreme stress, the body", "releases huge amounts of adrenaline", "increasing blood flow and",
    "energy to the muscles", "For a very short time, this can", "allow someone to produce", "levels of strength they normally",
    "couldn't access, letting the", "body perform something that", "would usually seem impossible"])], open(W + "work/beats.json", "w"), indent=1)
sc.render.resolution_x, sc.render.resolution_y = 1080, 1920; sc.render.fps = 60
sc.cycles.samples = 48; sc.cycles.use_denoising = True
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print("VO_OK", OUT, sc.frame_end)
