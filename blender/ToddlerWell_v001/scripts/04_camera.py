"""One continuous camera: Catmull-Rom spline through one framing per ~0.7-1 s (location, target, lens), keyed every 2 frames.
blender -b work/anim.blend --python scripts/04_camera.py -- work/film.blend"""
import sys, os, math
import bpy
from mathutils import Vector as V
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../pipeline/anim_lib.py")).read())
OUT = sys.argv[sys.argv.index("--") + 1]
DEPTH = 15.24; FL = -DEPTH + 0.05
def teen_head_z(f):
    k = (f - 1342) / 158.0; zr = 1.25 + ((FL + 2.0) - 1.25) * (ease_(k) * 0.6 + k * 0.4)
    return zr - 0.85
def ease_(t): t = max(0, min(1, t)); return t * t * (3 - 2 * t)
def tod_z(f):    # toddler pelvis during the fall
    u = max(0, min(1, (f - 104) / 92)); return 0.32 - (DEPTH - 0.05 + 0.32) * u * u + 0.354
K = [  # frame, location, target, lens
 (1,    (-0.75, -0.35, 0.38), (-1.62, -1.12, 0.42), 26),     # in front of the toddler: his face
 (40,   (-0.35, -1.95, 0.6), (-1.15, -0.8, 0.4), 26),
 (70,   (0.15, -1.55, 0.62), (-0.62, -0.48, 0.38), 28),
 (98,   (0.25, -0.95, 1.45), (-0.18, -0.15, 0.25), 24),
 (116,  (0.0, -0.03, 1.5), (0.0, 0.0, -2.0), 20),     # straight down the middle of the casing: held above the rim while he falls (no camera inside the dark pipe)
 (160,  (0.0, -0.03, 1.45), (0.0, 0.0, -6.0), 22),
 (196,  (0.0, -0.03, 1.4), (0.0, 0.0, -10.0), 24),
 # hard cut at 197: sharp top-down on him at the bottom
 (197,  (0.06, -0.09, -13.4), (0.0, 0.0, -14.8), 16),
 (218,  (0.08, -0.11, -13.3), (0.0, 0.0, -14.7), 18),     # well above his raised hands
 (240,  (0.07, -0.1, -13.45), (0.0, 0.0, -14.55), 20),
 # beat 2
 (247,  (0.07, -0.1, -13.45), (0.0, 0.0, -14.55), 20),
 # beat 2 - hard cut at 248 to the surface: no rise through the dark shaft
 (248,  (0.25, -0.35, 1.5), (-0.9, 5.6, 1.2), 30),     # the mother and crowd at the tape
 (270,  (0.15, -0.9, 1.9), (-0.7, 5.0, 1.1), 28),
 (290,  (0.0, -1.8, 2.4), (-0.5, 3.0, 1.0), 24),     # back and up: clear of the tripod leg and of ResA at the rope
 (318,  (-1.3, -3.0, 2.5), (-0.3, 0.4, 0.9), 22),
 (350,  (-1.6, -1.6, 1.6), (-0.3, 0.25, 1.0), 30),
 (378,  (-1.05, -0.55, 1.3), (-0.24, 0.18, 0.95), 36),
 (400,  (0.0, -0.05, 1.0), (0.0, 0.0, -3.0), 22),     # centred over the hole
 (427,  (0.0, -0.05, 0.8), (0.0, 0.0, -6.0), 22),
 # hard cut at 428 to the bottom view on the second descent
 (428,  (0.07, -0.1, -12.6), (0.0, 0.0, -14.4), 16),
 (448,  (0.12, -0.13, -13.5), (0.0, 0.0, -14.3), 18),
 # beat 3: through the wall into the cross-section, rise, break the surface on the excavator
 (468,  (0.05, -0.9, -13.4), (0.0, 0.0, -13.65), 18),
 (495,  (0.4, -5.2, -11.0), (0.1, 0.0, -11.6), 18),
 (525,  (1.2, -7.4, -6.5), (0.9, 0.0, -6.8), 22),     # stays deep, then breaks the surface fast: nobody seen from below the ground     # level, not looking up through the see-through ground at "floating" people
 (552,  (2.2, -7.6, 1.2), (4.2, 0.6, 0.9), 20),
 (585,  (5.0, -2.6, 0.5), (7.0, 1.0, 0.6), 24),
 (610,  (1.2, -0.9, 0.6), (2.2, 0.6, 0.15), 28),
 (638,  (4.4, -3.6, 2.8), (7.7, 0.6, 1.9), 30),     # back from the boom
 (662,  (2.8, 0.6, 2.6), (3.9, 2.4, 1.1), 26),
 # beat 4: time-lapse
 (690,  (6.5, -8.5, 7.0), (1.3, 1.5, 0.5), 22),
 (735,  (3.2, -3.4, 4.2), (1.8, 0.8, -0.2), 22),
 (772,  (1.7, -3.0, 2.6), (1.7, 0.2, -0.6), 20),
 (790,  (1.5, -4.6, -0.9), (1.5, 0.0, -2.0), 19),
 (805,  (1.3, -6.0, -3.2), (1.0, 0.0, -4.5), 17),
 (845,  (1.0, -8.0, -6.8), (0.6, 0.0, -6.8), 16),
 (870,  (0.0, -6.0, 0.9), (-0.7, 1.4, 0.6), 22),
 (882,  (-1.6, 1.2, 3.4), (-1.3, 6.15, 1.4), 30),     # over everyone's heads, not through them
 (893,  (-0.9, 3.5, 1.5), (-1.3, 6.15, 1.4), 40),
 (912,  (-1.6, 4.0, 1.5), (-2.4, 7.0, 1.45), 32),
 # beat 5: the teen
 (940,  (-0.4, 4.2, 1.45), (-2.4, 6.0, 1.35), 34),     # beside his path, not on it
 (968,  (0.1, 3.4, 1.35), (-2.0, 4.4, 1.2), 32),
 (1000, (0.35, 2.7, 1.4), (-1.35, 2.5, 1.35), 30),
 (1030, (0.6, 2.0, 1.5), (-1.12, 2.0, 1.55), 38),
 # hard cut at 1031: over his shoulder onto the rescuers listening (the teen alone is ~1.5 s)
 (1031, (-0.75, 2.95, 1.7), (-0.9, 0.9, 1.55), 32),     # over his shoulder: ResA listening
 (1110, (-0.7, 2.85, 1.68), (-0.9, 0.9, 1.55), 34),
 # hard cut at 1111
 (1111, (0.25, -0.35, 1.42), (-1.2, 1.4, 1.2), 30),
 (1125, (0.2, -0.4, 1.4), (-1.2, 1.4, 1.2), 30),
 (1142, (-1.0, -1.5, 1.6), (-1.3, 1.1, 1.25), 30),     # beat 6: on the teen walking to the knot; ResC (back to camera) out of frame
 # beat 6: knot
 (1160, (-3.0, 0.1, 1.45), (-1.62, 1.52, 1.2), 30),     # beat 6: side three-quarter at 2 m, ResB tying the knot at his back
 (1200, (-3.1, 0.15, 1.45), (-1.62, 1.52, 1.2), 30),
 (1240, (-3.05, 0.2, 1.45), (-1.6, 1.5, 1.25), 30),
 (1257, (-3.0, 0.22, 1.45), (-1.6, 1.5, 1.27), 30),
 # hard cut at 1258 (a move from the side would pass through a tripod leg)
 (1258, (-0.75, 0.0, 1.6), (-1.45, 1.25, 1.6), 40),     # his face as he gets ready: nervous, nodding
 (1287, (-0.7, 0.05, 1.6), (-1.45, 1.25, 1.62), 40),
 # hard cut at 1288
 (1288, (-1.8, -1.6, 1.6), (0.0, 0.4, 1.0), 26),
 (1295, (-1.8, -1.6, 1.6), (0.0, 0.4, 1.0), 26),     # outside the tripod
 # beat 7: head first
 (1310, (1.2, -1.4, 1.4), (0.0, 0.35, 1.0), 26),
 (1325, (0.0, -1.9, 1.3), (0.0, 0.2, 0.9), 24),
 (1342, (0.35, -1.1, 0.9), (0.0, 0.0, 0.2), 24),
 # beat 8: inside, torch
 (1358, (-0.5, -0.6, 1.5), (-0.1, 0.35, 0.8), 24),     # beat 8: ResB's face as they feed his legs in
 (1361, (-0.4, -0.7, 1.4), (-0.1, 0.3, 0.6), 24),
 (1371, (-0.35, -0.75, 1.35), (-0.1, 0.3, 0.5), 24),
 # hard cut at 1372 (CUTS): straight to beside his face inside the casing, never the empty pipe
 (1372, (0.3, -0.85, teen_head_z(1372) + 0.1), (0.0, 0.05, teen_head_z(1372) + 0.2), 24),
 (1380, (0.3, -0.85, teen_head_z(1380) + 0.1), (0.0, 0.05, teen_head_z(1380) + 0.2), 24),
 (1400, (0.3, -0.85, teen_head_z(1400) + 0.1), (0.0, 0.05, teen_head_z(1400) + 0.2), 24),     # beside his face, not the empty wall below
 (1440, (-0.3, -0.85, teen_head_z(1440) + 0.1), (0.0, 0.05, teen_head_z(1440) + 0.2), 24),
 (1475, (0.2, -0.9, teen_head_z(1475)), (0.0, 0.05, teen_head_z(1475)), 24),
 # beat 9: bottom, grab
 (1505, (0.05, -0.9, -14.3), (0.0, 0.0, -14.3), 26),
 (1550, (0.25, -0.75, -14.45), (0.0, 0.0, -14.45), 32),
 (1595, (-0.25, -0.75, -14.4), (0.0, 0.02, -14.5), 32),
 (1622, (0.0, -1.0, -14.0), (0.0, 0.0, -14.1), 26),
 # beat 10: out through the wall, side cross-section, rise to the haulers
 (1650, (0.1, -1.3, -13.3), (0.0, 0.0, -13.4), 18),
 # beat 11: emerge, lift, mother, crane up
 # hard cut at 1768 (CUTS): the mother at the tape while he is pulled out and swung upright with the toddler; she ducks under and runs in
 # hard cut at 1832: back on him, the toddler held against his chest
 (1668, (0.5, -3.2, -9.3), (0.0, 0.0, -9.5), 18),
 (1695, (0.8, -4.3, -3.0), (0.0, 0.2, -2.8), 18),
 (1705, (0.8, -4.3, -2.2), (0.0, 0.2, -1.9), 18),
 # hard cut at 1706: the haulers' last pulls; they let go and cheer (his upside-down exit stays off screen)
 (1706, (1.8, 3.4, 1.3), (-0.2, 2.3, 1.1), 34),
 (1781, (1.65, 3.25, 1.38), (-0.2, 2.3, 1.1), 34),
 # hard cut at 1782: him standing with the toddler held against his chest
 (1782, (0.5, 2.9, 1.5), (-0.3, 1.0, 1.25), 26),
 (1800, (0.7, 2.8, 1.5), (-0.4, 1.3, 1.25), 28),     # the mother runs in
 (1830, (0.9, 2.9, 1.55), (-0.5, 1.6, 1.3), 30),     # she takes him from the teen, in frame
 (1855, (0.95, 2.95, 1.55), (-0.5, 1.7, 1.3), 31),
 # hard cut at 1856
 (1856, (-1.31, 0.34, 1.55), (-0.65, 2.12, 1.5), 44),     # front-right of her: her face, and his turned out over her right shoulder     # the hug, from her side: both faces in profile
 (1915, (-1.27, 0.4, 1.52), (-0.65, 2.12, 1.47), 48),
 # hard cut at 1916: the wide (about 0.6 s)
 (1916, (2.4, -2.6, 2.6), (-0.3, 1.6, 1.0), 24),
 (1950, (2.6, -3.4, 3.6), (-0.3, 1.8, 0.9), 24),
]
CUTS = [197, 248, 428, 1031, 1111, 1258, 1288, 1372, 1706, 1782, 1856, 1916]     # hard cuts: separate splines either side, constant step between
cam = bpy.data.objects["Cam"]; tg = bpy.data.objects["CamTarget"]
bounds = [1] + CUTS + [1951]
for a_, b_ in zip(bounds[:-1], bounds[1:]):
    Ks = [k for k in K if a_ <= k[0] < b_]
    loc = catmull([(f, V(l)) for f, l, t, z in Ks]); tgt = catmull([(f, V(t)) for f, l, t, z in Ks]); lens = pchip([(f, z) for f, l, t, z in Ks])
    fr = list(range(a_, b_, 2)) + ([b_ - 1] if (b_ - 1 - a_) % 2 else [])
    for f in fr:
        cam.location = loc(f); tg.location = tgt(f); cam.data.lens = lens(f)
        cam.keyframe_insert("location", frame=f); tg.keyframe_insert("location", frame=f); cam.data.keyframe_insert("lens", frame=f)
for o in (cam, tg, cam.data):     # step, not blend, across each cut
    for layer in o.animation_data.action.layers:
        for strip in layer.strips:
            for cb in strip.channelbags:
                for fc in cb.fcurves:
                    for kp in fc.keyframe_points:
                        if any(c - 1 <= kp.co.x < c for c in CUTS): kp.interpolation = "CONSTANT"
# no lens/clip issues inside the shaft
cam.data.clip_start = 0.01
bpy.ops.wm.save_as_mainfile(filepath=OUT); print("CAM SAVED", OUT)
