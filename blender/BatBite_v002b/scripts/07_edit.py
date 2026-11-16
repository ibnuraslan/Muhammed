"""Lay the master shots onto the VO word frames: piecewise SHIFT of every keyframe (speed 1, no time-stretch).
Each shot = source window [s0, s1) of the master shown at [d0, d0 + s1 - s0). Source windows are in increasing order, so the
remap is monotonic; keys outside the windows are dropped, boundary values are keyed, and the last key of each window is CONSTANT
(a hard cut). Adds the VO, markers bound to the shot cameras, frame range, render settings.
blender -b look.blend --python 07_edit.py -- out.blend VO.mp3"""
import bpy, sys
a = sys.argv[sys.argv.index("--") + 1:]; OUT, VO = a[0], a[1]
sc = bpy.context.scene
#        (camera,          s0,   s1,   d0)   d0 = 1 + round(word_start * 60)
EDIT = [("S01_crowd_bat",    1,   95,    1),   # A fan threw what looked like a rubber bat
        ("S02_bat_lands",   95,  150,   95),   # onto the stage (2.32 s -> 140)
        ("S03_notices",    150,  276,  150),   # during the concert (3.12 -> 188)
        ("S04_steps",      300,  373,  276),   # Without thinking (4.58 -> 276)
        ("S05_grabs",      408,  445,  349),   # Ozzy Osbourne picked it up (5.80 -> 349)
        ("S06_rises",      516,  546,  386),   #   (grab window 445-515 cut)
        ("S07_to_mouth",   636,  680,  416),   # and bit into it (6.92 -> 416)
        ("S08_bite",       680,  714,  460),   #   profile, cut on contact (src 712 -> 492)
        ("S08c_crowd",     714,  819,  494),   # believing it was just a toy (8.22 -> 494)
        ("S09_recoil",     820,  933,  599),   # But the moment he bit down (9.96 -> 599)
        ("S10_shock",      934, 1065,  712),   # he realized the bat was real (11.84 -> 712)
        ("S11_stares",    1066, 1152,  843),   # Its blood filled his mouth (14.04 -> 843)
        ("S12_drops",     1280, 1380,  929),   # and he immediately understood (15.46 -> 929)
        ("S13_bends",     1400, 1464, 1029),   #   what had happened
        ("S14_hospital",  1625, 1771, 1093),   # v002b: source starts 25 frames in (his legs have settled under his hands). After the concert, he was rushed to the hospital (18.20 -> 1093)
        ("S15_mask_cu",   1800, 1924, 1239)]   # where doctors gave him rabies shots (20.64 -> 1239)
END = 1362                                     # last word ends 22.18 s; +0.5 s
for (n0, s0, s1, d0), (n1, t0, t1, e0) in zip(EDIT, EDIT[1:]):
    assert d0 + (s1 - s0) == e0 and t0 >= s1, (n0, n1)
assert EDIT[-1][3] + EDIT[-1][2] - EDIT[-1][1] == END + 1
def fcurves_of(act):
    if hasattr(act, "fcurves"): return list(act.fcurves)
    return [fc for l in act.layers for st in l.strips for cb in st.channelbags for fc in cb.fcurves]
acts = set()
for o in bpy.data.objects:
    if o.animation_data and o.animation_data.action: acts.add(o.animation_data.action)
for c in list(bpy.data.cameras) + list(bpy.data.lights):
    if c.animation_data and c.animation_data.action: acts.add(c.animation_data.action)
nk = 0
for act in acts:
    for fc in fcurves_of(act):
        old = [(k.co.x, k.co.y, k.interpolation, k.handle_left.copy(), k.handle_right.copy(), k.handle_left_type, k.handle_right_type) for k in fc.keyframe_points]
        new = []
        for (_, s0, s1, d0) in EDIT:
            off = d0 - s0
            inside = [k for k in old if s0 <= k[0] < s1]
            first = (s0, fc.evaluate(s0), 'LINEAR', None, None, None, None)
            last = (s1 - 1, fc.evaluate(s1 - 1), 'CONSTANT', None, None, None, None)
            seg = ([first] if not inside or inside[0][0] > s0 else []) + inside + ([last] if not inside or inside[-1][0] < s1 - 1 else [])
            for i, k in enumerate(seg):
                x, y, ip, hl, hr, hlt, hrt = k
                if i == len(seg) - 1: ip = 'CONSTANT'
                new.append((x + off, y, ip, hl and hl + type(hl)((off, 0)), hr and hr + type(hr)((off, 0)), hlt, hrt))
        fc.keyframe_points.clear()
        fc.keyframe_points.add(len(new))
        for kp, (x, y, ip, hl, hr, hlt, hrt) in zip(fc.keyframe_points, new):
            kp.co = (x, y); kp.interpolation = ip
            if hl is not None:
                kp.handle_left_type, kp.handle_right_type = hlt, hrt; kp.handle_left = hl; kp.handle_right = hr
            else:
                kp.handle_left_type = kp.handle_right_type = 'AUTO_CLAMPED'
        fc.update(); nk += len(new)
print("EDIT keys", nk, "in", len(acts), "actions")
for m in list(sc.timeline_markers): sc.timeline_markers.remove(m)
for (cam, s0, s1, d0) in EDIT:
    mk = sc.timeline_markers.new(cam, frame=d0); mk.camera = bpy.data.objects[cam]
for o in list(bpy.data.objects):     # cameras not used in the edit are removed
    if o.type == 'CAMERA' and o.name not in {e[0] for e in EDIT}:
        for ch in list(o.children): bpy.data.objects.remove(ch, do_unlink=True)
        bpy.data.objects.remove(o, do_unlink=True)
sc.camera = bpy.data.objects[EDIT[0][0]]
sc.frame_start, sc.frame_end = 1, END
sc.render.fps = 60; sc.render.fps_base = 1.0
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1080, 1920, 100
sc.render.engine = 'CYCLES'; sc.cycles.samples = 64; sc.cycles.use_denoising = True
sc.render.use_motion_blur = False
sc.render.image_settings.file_format = 'PNG'
sc.render.filepath = "//render/BatBite_"
se = sc.sequence_editor_create()
coll = se.strips if hasattr(se, "strips") else se.sequences
for s_ in list(coll): coll.remove(s_)
snd = coll.new_sound("VO", VO, 1, 1); snd.sound.pack()
import json
words = json.load(open(VO.replace(".mp3", ".words.json")))
beats = [{"beat": e[0], "frame": e[3], "first_words": " ".join(w[2] for w in words if 1 + round(w[0] * 60) >= e[3])[:60]} for e in EDIT]
json.dump(beats, open(OUT.rsplit("/", 1)[0] + "/beats.json", "w"), indent=1)
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print("EDIT saved", OUT, "frames", sc.frame_start, sc.frame_end)
