"""v012 camera (client rejection, Nov 21: items 14, 15, 18, 21, 22, 26, 33, 34; director: hard cuts between locations are fine).
One camera, CAM_Film, aimed at CAM_Film_Aim. Each shot is its own move (keys inside the shot, CONSTANT at the cut).
Cuts at the client's cut points. Frames 1-1644; the last shot holds on the clerk and the red X to the last frame.
blender -b in.blend --python 23_v012_camera.py -- <out.blend>"""
import sys, os, math, json
import bpy
from mathutils import Vector
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import v12lib as VL
OUT = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene; V = lambda *a: Vector(a)
SITE = json.load(open(os.path.join(os.path.dirname(OUT), "or_site.json")))
CX, CY, SKZ = SITE["CX"], SITE["CY"], SITE["SKZ"]
OB = bpy.data.objects
cam = OB["CAM_Film"]; aim = OB["CAM_Film_Aim"]
def bone(rig, b, off=(0, 0, 0)):
    return lambda f: (OB[rig].matrix_world @ OB[rig].pose.bones[b].head) + V(*off)
def obj(o, off=(0, 0, 0)):
    return lambda f: OB[o].matrix_world.translation + V(*off)
def fixed(p): return lambda f: V(*p)
def mix(a, b, t): return lambda f: a(f).lerp(b(f), t)
# (first, last, cam_start, cam_end, aim_fn, lens, fstop)
SHOTS = [
    (1, 135, (0.30, 0.78, 1.78), (0.22, 0.70, 1.74), fixed((-0.30, -0.28, 1.30)), 28, 5.6),          # S1 surgeon at the open patient
    (136, 275, (0.02, -0.08, 1.45), (-0.02, -0.06, 1.41), fixed((CX, CY, SKZ - 0.01)), 38, 8.0),    # S2 argon beam brands the liver in the body
    (276, 429, (0.20, 0.40, 1.60), (0.16, 0.36, 1.58), fixed((CX, CY - 0.06, SKZ + 0.03)), 30, 5.6), # S3 stitching
    (430, 570, (0.06, 0.52, 1.63), (0.00, 0.44, 1.62), bone("Surgeon1", "head", (0, 0, -0.06)), 40, 5.6),   # S4 mask down, smirk
    (571, 640, (1.50, -1.80, 1.60), (1.55, -1.85, 1.58), mix(fixed((3.46, -0.9, 1.52)), bone("Surgeon1", "neck01"), 0.55), 26, 5.6),  # S5 week later
    (641, 775, (5.05, -1.60, 1.45), (5.15, -1.40, 1.32), bone("Patient", "spine01", (0, 0, 0.08)), 30, 5.6),  # S6 home
    (776, 915, (0.15, 6.40, 1.62), (0.25, 4.40, 1.58), mix(bone("Patient", "head"), bone("Nurse", "head"), 0.45), 24, 5.6),  # S7 bed in
    (916, 1060, (0.45, -0.40, 1.55), (0.28, -0.28, 1.55), bone("Surgeon2", "neck01", (0, 0, -0.05)), 30, 5.6),  # S8 new doctor
    (1061, 1175, (0.24, -0.12, 1.56), (0.20, -0.10, 1.52), obj("LiverRig", (0, 0, 0.03)), 35, 8.0),  # S9 liver lifted
    (1176, 1240, (-0.22, -0.72, 1.62), (-0.24, -0.62, 1.62), bone("Surgeon2", "head", (0, 0, -0.10)), 36, 5.6),  # S10 her eyes
    (1241, 1310, (-6.15, -1.05, 1.76), (-6.25, -0.95, 1.74), fixed((-9.60, 0.15, 1.40)), 26, 5.6),  # S11a hearing wide
    (1311, 1445, (-8.00, -0.55, 1.58), (-7.90, -0.45, 1.58), bone("Surgeon1", "spine01", (0, 0, 0.05)), 32, 5.6),  # S11b defendant
    (1446, 1575, (-9.20, -0.95, 1.55), (-9.24, -0.90, 1.53), fixed((-10.15, -0.05, 1.36)), 30, 5.6),  # S12 gavel
    (1576, 1644, (-9.25, -1.55, 1.62), (-9.30, -1.50, 1.60), fixed((-10.15, -1.12, 1.33)), 32, 5.6),  # S13 stamp
]
for o in (cam, aim):
    if o.animation_data: o.animation_data_clear()
if cam.data.animation_data: cam.data.animation_data_clear()
cam.data.dof.use_dof = True; cam.data.dof.focus_object = aim
def ease(u): return u * u * (3 - 2 * u)
for a, b, c0, c1, aimf, lens, fs in SHOTS:
    for f in list(range(a, b + 1, 3)) + [b]:
        sc.frame_set(f)
        u = (f - a) / max(1, b - a)
        cam.location = V(*c0).lerp(V(*c1), ease(u)); cam.keyframe_insert("location", frame=f)
        aim.location = aimf(f); aim.keyframe_insert("location", frame=f)
        cam.data.lens = lens; cam.data.keyframe_insert("lens", frame=f)
        cam.data.dof.aperture_fstop = fs; cam.data.dof.keyframe_insert("aperture_fstop", frame=f)
for idb in (cam, aim, cam.data):
    for fc in VL.fcurves(idb):
        for kp in fc.keyframe_points:
            kp.interpolation = 'LINEAR'
        for kp in fc.keyframe_points:
            if int(kp.co.x) in {s[1] for s in SHOTS}: kp.interpolation = 'CONSTANT'
sc.frame_start, sc.frame_end = 1, 1644
json.dump([s[:2] for s in SHOTS], open(os.path.join(os.path.dirname(OUT), "shots.json"), "w"))
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print("CAM_DONE", OUT)
