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
def track(rig, b, off):
    return lambda f: (OB[rig].matrix_world @ OB[rig].pose.bones[b].head) + V(*off)
def letters(off=(0, 0, 0)):
    return lambda f: OB["BrandSB"].matrix_world.translation + V(*off)
SHOTS = [
    (1, 135, (0.10, 0.62, 1.55), (0.06, 0.56, 1.53), fixed((-0.38, -0.20, 1.20)), 28, 5.6),        # S1 closer, below the lamps: surgeon, pen, her head + body
    (136, 200, (0.40, -0.20, 1.72), (0.37, -0.20, 1.70), fixed((CX - 0.03, CY - 0.16, SKZ + 0.14)), 30, 5.6),  # S2a foot end: his face, hand, the liver
    (201, 275, (CX + 0.30, CY + 0.01, SKZ + 0.26), (CX + 0.27, CY + 0.01, SKZ + 0.24), letters((0, 0, 0)), 55, 8.0),  # S2b the beam burns S B (legible)
    (276, 429, (0.32, 0.62, 1.78), (0.28, 0.56, 1.74), fixed((CX - 0.02, CY - 0.22, SKZ + 0.18)), 26, 5.6),  # S3 closing + stitching
    (430, 570, (0.12, 0.78, 1.52), (0.06, 0.68, 1.55), bone("Surgeon1", "spine01", (0, 0, 0.12)), 30, 5.6),  # S4 arm lift, mask down, acting
    (571, 640, (1.45, -1.85, 1.72), (1.45, -1.92, 1.72), mix(fixed((3.46, -0.9, 1.55)), bone("Surgeon1", "head"), 0.6), 30, 5.6),  # S5 chest-up
    (641, 775, (5.05, -1.60, 1.45), (5.15, -1.40, 1.32), bone("Patient", "spine01", (0, 0, 0.08)), 30, 5.6),  # S6 home
    (776, 915, (0.15, 6.40, 1.62), (0.22, 5.10, 1.60), mix(bone("Patient", "head"), bone("Nurse", "head"), 0.45), 24, 5.6),  # S7 bed + doctor
    (916, 1060, track("Surgeon2", "head", (1.15, -0.85, 0.02)), None, bone("Surgeon2", "spine01", (0, 0, 0.16)), 30, 5.6),  # S8 tracks her, side-front
    (1061, 1175, (0.50, 0.02, 1.62), (0.16, -0.02, 1.44), lambda f: obj("LiverRig", (0, 0.16, 0.12))(f).lerp(letters()(f), ease(min(1.0, max(0.0, (f - 1080) / 80.0)))), 32, 5.6),   # wide (her body, hands) -> push in to the letters  # S9 foot end: her hands lift the branded liver
    (1176, 1240, (-0.22, -0.72, 1.62), (-0.24, -0.66, 1.62), bone("Surgeon2", "head", (0, 0, 0.05)), 70, 5.6),  # S10 her face
    (1241, 1310, (-8.55, -1.95, 1.70), (-8.75, -1.45, 1.66), fixed((-10.40, 0.05, 1.45)), 20, 5.6),  # S11a closer, dolly past the panel (all three, faces, action)
    (1311, 1445, (-8.00, -0.55, 1.50), (-7.92, -0.47, 1.50), bone("Surgeon1", "neck01", (0, 0, -0.14)), 32, 5.6),  # S11b defendant, level
    (1446, 1575, (-9.20, -0.95, 1.55), (-9.24, -0.90, 1.53), fixed((-10.15, -0.05, 1.36)), 30, 5.6),  # S12 gavel
    (1576, 1644, (-9.25, -1.55, 1.62), (-9.45, -1.42, 1.55), fixed((-10.15, -1.15, 1.30)), 32, 5.6),  # S13 stamp
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
        cam.location = c0(f) if callable(c0) else V(*c0).lerp(V(*c1), ease(u)); cam.keyframe_insert("location", frame=f)
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
