"""One continuous camera (CAM_Film) on a Catmull-Rom spline through one framing per ~1 s.
blender -b xray.blend --python 05_camera.py -- <out.blend>"""
import sys, os, math, json
import bpy
from mathutils import Vector, Matrix
HERE = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(HERE, "..", "..", "pipeline", "anim_lib.py")).read())
OUT = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene; C = bpy.data.objects["Composer"]; HR = C.data.bones["head"].matrix_local
def T(s): return 1 + round(s * 60)
BEAT = [T(t) for t in (0.0, 3.9, 5.2, 8.6, 11.9, 16.4, 18.4, 20.1)]
ANCHOR = Vector(sc["anchor"]); bite = bpy.data.objects["Bite"]
V = lambda *a: Vector(a[0]) if len(a) == 1 else Vector(a)
def HS(f, p): ev(f); return C.matrix_world @ C.pose.bones["head"].matrix @ HR.inverted() @ V(p)
def ROD(f, u): ev(f); return ANCHOR.lerp(bite.matrix_world.translation, u)
COCH = V(sc["coch"]); DRUM = V(sc["drum"])
K = []   # frame, camera, aim, lens
def H(f, c, a, l): K.append((f, HS(f, c), HS(f, a), l))
def W(f, c, a, l): K.append((f, V(c), V(a), l))
# beat 1: macro on the bite -> profile -> back along the rod -> room
H(1, (0.24, -0.44, 1.56), (0.0, -0.13, 1.545), 38)
H(45, (0.30, -0.42, 1.57), (0.0, -0.12, 1.55), 36)
H(95, (0.42, -0.30, 1.56), (0.0, -0.10, 1.54), 34)
K.append((150, ROD(150, 0.45) + V(-0.42, 0.14, 0.14), ROD(150, 0.55), 30))
W(200, (-1.45, 0.55, 1.40), (0.0, -0.3, 1.08), 24)
W(232, (-1.05, 0.05, 1.3), (-0.05, 0.0, 0.9), 26)
# beat 2: low on the keys during the crash, then orbit up toward the rod
W(258, (-0.5, -0.2, 1.05), (-0.1, 0.06, 0.83), 28)
W(290, (-0.55, 0.02, 1.02), (-0.05, 0.14, 0.97), 30)
# beat 3: ride the rod from the piano to the teeth
K.append((322, ANCHOR + V(-0.11, -0.07, 0.05), ANCHOR + V(0, -0.03, 0), 38))
K.append((380, ROD(380, 0.3) + V(-0.1, 0.01, 0.045), ROD(380, 0.48), 35))
K.append((440, ROD(440, 0.62) + V(-0.12, 0.05, -0.01), ROD(440, 0.82), 35))
H(505, (0.22, -0.36, 1.57), (0.0, -0.12, 1.56), 36)
# beat 4: x-ray dive into the jaw, up to the inner ear
H(545, (0.30, -0.30, 1.57), (0.0, -0.10, 1.55), 38)
H(600, (0.28, -0.24, 1.56), (0.03, -0.05, 1.53), 35)
H(655, (0.24, -0.17, 1.58), (0.04, -0.03, 1.54), 34)
H(705, (0.21, -0.12, 1.6), (0.05, -0.01, 1.55), 36)
# beat 5: orbit the glowing skull, over the cranium, down the side into the ear cross-section
H(765, (0.22, -0.30, 1.68), (0.0, -0.04, 1.55), 28)
H(830, (0.06, -0.14, 1.86), (0.0, -0.02, 1.57), 28)
H(890, (0.27, 0.06, 1.63), (0.03, 0.0, 1.56), 30)
H(940, (0.17, -0.10, 1.60), (0.06, 0.0, 1.56), 40)
H(982, (0.13, -0.08, 1.585), tuple(DRUM + V(-0.005, 0.0, 0.0)), 50)
# beat 6: torn eardrum, then along the bypass to the cochlea
H(1020, (0.115, -0.06, 1.59), tuple(DRUM + V(-0.002, 0.003, 0.0)), 55)
H(1068, (0.11, -0.05, 1.60), (0.055, 0.0, 1.565), 50)
# beat 7: cochlea lights up, pull back out to the face, eyes closing
H(1118, (0.10, -0.06, 1.59), tuple(COCH), 50)
H(1160, (0.20, -0.24, 1.60), (0.03, -0.04, 1.565), 38)
H(1200, (0.22, -0.42, 1.59), (0.0, -0.11, 1.58), 38)
# beat 8: pull out, crane up, orbit over the lid, spiral up to top-down
H(1245, (0.55, -0.40, 1.58), (0.0, -0.1, 1.56), 30)
W(1300, (-1.5, -0.15, 1.45), (0.0, -0.3, 1.18), 26)
W(1360, (-1.45, 0.55, 1.6), (0.0, -0.35, 1.15), 24)
W(1420, (-1.7, -0.7, 2.4), (0.0, -0.3, 0.95), 22)
W(1480, (-1.0, -1.6, 3.2), (0.0, -0.15, 0.7), 20)
W(1540, (0.4, -1.5, 3.4), (0.0, -0.1, 0.6), 20)
W(1590, (1.0, -0.75, 3.45), (0.0, 0.05, 0.55), 19)
cd = bpy.data.cameras.new("CAM_Film"); cd.sensor_fit = 'AUTO'; cd.clip_start = 0.004; cd.clip_end = 60
cd.dof.use_dof = True; cd.dof.aperture_fstop = 4.0
cam = bpy.data.objects.new("CAM_Film", cd); sc.collection.objects.link(cam); sc.camera = cam
aim = bpy.data.objects.new("CAM_Film_Aim", None); sc.collection.objects.link(aim)
tt = cam.constraints.new('TRACK_TO'); tt.target = aim; tt.track_axis = 'TRACK_NEGATIVE_Z'; tt.up_axis = 'UP_Y'
cd.dof.focus_object = aim
fc = catmull([(f, c) for f, c, a, l in K]); fa = catmull([(f, a) for f, c, a, l in K]); fl = catmull([(f, float(l)) for f, c, a, l in K])
for f in list(range(1, 1591, 2)) + [1590]:
    cam.location = fc(f); cam.keyframe_insert("location", frame=f)
    aim.location = fa(f); aim.keyframe_insert("location", frame=f)
    cd.lens = fl(f); cd.keyframe_insert("lens", frame=f)
    # macro shots need deeper focus
    d = (fc(f) - fa(f)).length; cd.dof.aperture_fstop = 4.0 if d > 0.6 else (8.0 if d > 0.25 else 11.0); cd.dof.keyframe_insert("aperture_fstop", frame=f)
sc["cam_keys"] = json.dumps([[f, list(c), list(a), l] for f, c, a, l in K])
json.dump([{"beat": i + 1, "frame": b, "first_words": w} for i, (b, w) in enumerate(zip(BEAT, ["He would bite down", "as he played", "The piano's vibrations", "into his jawbone", "This sent the sound", "completely skipping his", "so he could", "And by using"]))],
          open(os.path.join(HERE, "..", "beats.json"), "w"), indent=1)
bpy.ops.wm.save_as_mainfile(filepath=OUT); print("CAMERA_DONE", len(K))
