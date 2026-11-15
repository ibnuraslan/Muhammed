"""(base of 09g) DonationBin v007e patch, applied to the v007d package (director review of 971ada3).
blender -b DonationBin_v007d_60fps.blend --python 09f_v007e_patch.py -- out.blend
1. Black-hole eye: the MPFB EnhancedEye shader (glass cornea over the eyeball) renders black/pink in Cycles here. Every
   character's eye gets a simple opaque eye: white, brown iris, dark pupil, glossy coat. The iris is painted from each
   eyeball's own forward direction (a per-vertex attribute), so it follows the gaze bones. A tiny catchlight rides with
   the camera (not visible to the camera).
2. 1561-1860: four shots (~1.5 s) at three-quarter angles (both eyes read), camera rolled with her head, with a head
   turn up to the grate; the camera keeps 28 cm clear of everything (no blurred tarp/bag slabs at the lens).
3. 1897-1935: the push on the passer-by stops; a steady front-left shot keeps his whole head in frame.
4. 636-680: she is 20 cm further back from the grate so her face is not pressed into it."""
import sys, math
import bpy
from mathutils import Vector, Matrix, Quaternion
OUT = sys.argv[sys.argv.index("--") + 1]
_src = open("/home/user/Muhammed/blender/DonationBin_v001/scripts/09e_v007d_roll.py").read()
_helpers = _src[:_src.index("\nA1 = (0, 20, -20")]
_helpers = _helpers.replace("OUT = sys.argv[sys.argv.index(\"--\") + 1]", "")
exec(_helpers)

# 09g: (a) 601-675 re-shot on her new position (20 cm back from the grate), (b) 1741-1860 re-shot with a view-cone check:
# nothing but her may sit within 40 cm of the lens anywhere in the frame (no blurred tarp/bag slabs at the edges)
def cone_clear(c, t, L=0.40):
    fw = (t - c).normalized(); up = Vector((0, 0, 1)); x = fw.cross(up).normalized(); y = x.cross(fw)
    for ax in (-0.45, -0.25, 0.0, 0.25, 0.45):
        for ay in (-0.6, -0.3, 0.0, 0.3, 0.6):
            d = (fw + x * ax + y * ay).normalized(); h = ray(c, d, L)
            if h is not None and (h[4].name not in WMESH or (h[1] - t).length > 0.22): return False
    return True
_sees = sees
def sees(c, p, own=WMESH): return _sees(c, p, own) and cone_clear(c, p)
_air = air
def air(c, r=0.22): return _air(c, r)
if not face_shot(601, 675, (60, -60, 70, -70, 50, -50, 80, -80, 40, -40, 90, -90), (0.62, 0.56, 0.50, 0.45), ups=(0.0, 0.10, -0.10, 0.20), lens=20, name="stands v2"):
    _tr = smooth_face(WO, 601, 675)
    fixed_shot(601, 675, (-0.50, -0.42, 1.50), (0, 0, 1), lens=18, track=lambda f: _tr[f] + Vector((0, 0, -0.15)), name="stands front-left")
for (a_, b_), angs in (((1561, 1650), (35, 30, 40, 25, 45, -35, -30, -40, 0, 15, -15)), ((1651, 1740), (-35, -30, -40, -25, -45, 35, 30, 40, 0, 15, -15)), ((1741, 1800), (-35, -30, -40, -25, -45, 35, 30, 40, 0, 15, -15)), ((1801, 1860), (35, 30, 40, 25, 45, -35, -30, -40, 0, 15, -15))):
    face_shot(a_, b_, angs, (0.62, 0.56, 0.50, 0.45), ups=(0.0, 0.06, 0.12, 0.20, 0.30, -0.04), lens=34, push=0.03, roll=True, aim=Vector(), name="days cone %d" % a_)
for f, (p, q, ln) in sorted(NEW.items()):
    cam.location = p; cam.keyframe_insert("location", frame=f)
    cam.rotation_mode = 'QUATERNION'
    q0 = cam.rotation_quaternion.copy()
    cam.rotation_quaternion = q if q.dot(q0) >= 0 else -q; cam.keyframe_insert("rotation_quaternion", frame=f)
    cd.lens = ln; cd.keyframe_insert("lens", frame=f)
sc.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print("V007E_G_DONE", sorted(set((min(NEW), max(NEW)))))
