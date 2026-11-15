"""v008b post-build key fixes, run on the packaged file (after 04_package.py). Each removes YOU's keys at one frame on one
arm so it interpolates between the clean neighbouring keys. Nothing else moves: the camera and every other frame stay
bit-identical.
- 1771 (29.5 s), right arm: the haul key put YOU's right palm on a fold face of the FO jacket (normal z -0.25 instead of
  +0.33 at the neighbouring keys), so the hand tilted into his shoulder for frames 1770-1773 (clip_scan: 4 cm into his
  body). 03_animate.py now averages the jacket normal over 4 cm for future builds.
- 2353 (39.2 s), right fingers: the first yoke regrip came out as a starfish hand (index vs little finger 96 deg, qa FAN);
  without it the fingers go from the arrival curl straight into the 2368 horn grip (max 21 deg).
blender -b in.blend --python 07_haul_key_fix.py -- out.blend"""
import sys, bpy, re
out = sys.argv[sys.argv.index("--") + 1]
FIXES = [(1771, re.compile(r'pose\.bones\["((IK_hand|Pole_elbow|hand|wrist|metacarpal|finger|thumb|lowerarm)[^"]*\.R)"\]')),
         (2353, re.compile(r'pose\.bones\["((finger|thumb)[^"]*\.R)"\]'))]
Y = bpy.data.objects["YOU"]; act = Y.animation_data.action
for bad, pat in FIXES:
    n = 0
    for lay in act.layers:
        for st in lay.strips:
            for cb in st.channelbags:
                for fc in cb.fcurves:
                    if not pat.match(fc.data_path): continue
                    for k in [k for k in fc.keyframe_points if abs(k.co[0] - bad) < 0.01]:
                        fc.keyframe_points.remove(k); n += 1
                    fc.update()
    print("KEYFIX removed", n, "keys at", bad)
bpy.context.scene.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=out, compress=True)
print("KEYFIX saved", out)
