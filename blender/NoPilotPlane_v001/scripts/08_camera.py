"""v009 (director): third-person camera. Re-keys CAM_Film on the packaged film as a cut list of short shots
(<= 2.5 s each), camera >= 1.5 m from the people in frame, faces in frame. Times are film seconds (1 + round(s * 60)).
Run last: blender -b film.blend --python 08_camera.py -- out.blend   (check: cam_dist_check.py)"""
import sys, bpy, math
from mathutils import Vector, Matrix
out = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene; FPS = 60; END = sc.frame_end
CAM = sc.camera; camd = CAM.data
def FN(t): return 1 + round(t * FPS)
def smooth(u): u = max(0.0, min(1.0, u)); return u * u * (3 - 2 * u)
YOU, CA, FO = (bpy.data.objects[n] for n in ("YOU", "CAPT", "FO"))
def bone_pt(rig, bone, off=(0, 0, 0)):
    def g(f):
        sc.frame_set(f); return rig.matrix_world @ rig.pose.bones[bone].head + Vector(off)
    return g
def fixed(p): return lambda f: Vector(p)
def mid(a, b, w=0.5): return lambda f: a(f).lerp(b(f), w)
YH = bone_pt(YOU, "head", (0, 0.04, 0.05))          # face centre
YC = bone_pt(YOU, "spine02", (0, 0, 0.10))          # chest
CH = bone_pt(CA, "head"); FH = bone_pt(FO, "head")
COCK_FRONT = ((0.45, 3.18, 1.55), (0.44, 3.15, 1.54))          # outside the windscreen, looking back at his face
COCK_SIDE = ((-1.15, 2.02, 1.56), (-1.13, 1.97, 1.55))         # front-left corner: face, arms and yoke in one frame
CORNER = ((-1.20, 2.10, 1.62), (-1.18, 2.05, 1.62))            # front-left corner, standing beats
CENTRE = ((-0.02, 1.08, 1.76), (0.0, 1.02, 1.75))              # between the pilot seats, looking aft
WINDOW = ((-0.52, 1.50, 1.32), (-0.52, 1.56, 1.31))            # captain's eye line, out of the windscreen
REAR = ((-0.32, -0.85, 1.72), (-0.30, -0.80, 1.70))            # doorway, looking forward over the cockpit
SHOTS = [
    # beat 1-2: the cabin
    (0.00, 2.10, (0.05, -3.02, 1.85), (0.05, -3.10, 1.82), YH, 30),
    (2.10, 4.06, (0.15, -3.30, 1.85), (0.12, -3.35, 1.82), mid(YH, fixed((-0.95, -4.50, 0.80)), 0.5), 28),
    (4.06, 5.40, (0.00, -6.60, 1.80), (0.00, -6.50, 1.78), YH, 30),
    (5.40, 6.74, (0.05, -3.00, 1.85), (0.05, -3.05, 1.85), mid(YH, fixed((-1.45, -4.70, 1.25)), 0.35), 26),
    # beat 3: up the aisle
    (6.74, 8.20, (0.00, -1.00, 1.70), (0.00, -1.05, 1.70), YH, 35),
    (8.20, 9.16, "follow", None, fixed((0.0, -0.40, 1.30)), 28),
    # beat 4-5: the door, the captain in the doorway
    (9.16, 10.90, CENTRE[0], CENTRE[1], mid(YH, fixed((0.0, -0.60, 1.20)), 0.5), 26),
    (10.90, 13.22, CENTRE[0], CENTRE[1], mid(YH, CH, 0.5), 24),
    # beat 6-8: the first officer, the radio
    (13.22, 15.50, (-1.05, 2.00, 1.50), (-1.03, 1.96, 1.50), mid(YH, FH, 0.5), 24),
    (15.50, 17.60, CORNER[0], CORNER[1], mid(YH, fixed((0.10, 1.40, 0.90)), 0.4), 28),
    (17.60, 19.20, (-1.00, 2.15, 1.45), (-0.99, 2.12, 1.45), mid(YH, fixed((0.00, 1.50, 0.85)), 0.7), 45),
    (19.20, 20.40, CORNER[0], CORNER[1], YH, 35),
    (20.40, 21.24, REAR[0], REAR[1], YH, 28),
    # beat 9: the haul
    (21.24, 23.50, CORNER[0], CORNER[1], mid(YH, FH, 0.5), 24),
    (23.50, 25.82, REAR[0], REAR[1], mid(YH, FH, 0.5), 22),
    # beat 10-11: alarms, the dive
    (25.82, 27.40, CORNER[0], CORNER[1], YH, 26),
    (27.40, 28.66, WINDOW[0], WINDOW[1], fixed((-0.52, 9.0, -0.6)), 24),
    (28.66, 30.32, REAR[0], REAR[1], mid(YH, fixed((0.4, 2.4, 1.1)), 0.4), 22),
    # beat 12-19: flying it; cut between his face, the side, the window
    (30.32, 31.90, COCK_SIDE[0], COCK_SIDE[1], YC, 28),
    (31.90, 33.42, COCK_FRONT[0], COCK_FRONT[1], YH, 40),
    (33.42, 35.20, WINDOW[0], WINDOW[1], fixed((-0.52, 9.0, 0.6)), 24),
    (35.20, 37.06, COCK_SIDE[0], COCK_SIDE[1], YC, 30),
    (37.06, 39.00, COCK_FRONT[0], COCK_FRONT[1], YH, 42),
    (39.00, 41.30, (-0.80, 0.30, 1.75), (-0.78, 0.36, 1.74), fixed((0.55, 2.40, 1.05)), 24),
    (41.30, 42.90, WINDOW[0], WINDOW[1], fixed((-0.52, 9.0, 0.2)), 24),
    (42.90, 44.20, COCK_FRONT[0], COCK_FRONT[1], YH, 40),
    (44.20, 46.00, COCK_SIDE[0], COCK_SIDE[1], YC, 26),
    (46.00, 47.80, WINDOW[0], WINDOW[1], fixed((-0.52, 9.0, 0.3)), 24),
    (47.80, 49.56, COCK_FRONT[0], COCK_FRONT[1], YH, 42),
    (49.56, 51.10, CORNER[0], CORNER[1], mid(YH, FH, 0.5), 22),
    (51.10, 52.48, CENTRE[0], CENTRE[1], FH, 28),                  # the first officer on his back, face up
    (52.48, 54.00, WINDOW[0], WINDOW[1], fixed((-0.52, 9.0, 0.3)), 24),
    (54.00, 55.72, COCK_SIDE[0], COCK_SIDE[1], YH, 32),
    # beat 19: the close-up of his face (kept from v008b by direction)
    (55.72, 58.00, (0.56, 1.93, 1.34), (0.535, 1.86, 1.31), YH, 24),
]
CAM.animation_data_clear()
if camd.animation_data: camd.animation_data_clear()
root = bone_pt(YOU, "spine05")
for (t0, t1, p0, p1, aim, lens) in SHOTS:
    f0, f1 = FN(t0), min(FN(t1) - 1, END)
    assert t1 - t0 <= 2.5 + 1e-6, (t0, t1)
    raw = {f: aim(f) for f in range(f0 - 8, f1 + 9)}
    rp = {f: root(f) for f in range(f0, f1 + 1)} if p0 == "follow" else None
    for f in range(f0, f1 + 1):
        ws = [raw[g] for g in range(f - 8, f + 9)]; a = sum(ws, Vector()) / len(ws)
        u = smooth((f - f0) / max(1, f1 - f0))
        p = rp[f] + Vector((0.08, -1.90, 0.70)) if rp else Vector(p0).lerp(Vector(p1), u)
        CAM.matrix_world = Matrix.Translation(p) @ (a - p).to_track_quat('-Z', 'Y').to_matrix().to_4x4()
        CAM.keyframe_insert("location", frame=f); CAM.keyframe_insert("rotation_euler", frame=f)
        camd.lens = lens; camd.keyframe_insert("lens", frame=f)
for idb in (CAM, camd):
    for lay in idb.animation_data.action.layers:
        for st in lay.strips:
            for cb in st.channelbags:
                for fc in cb.fcurves:
                    for kp in fc.keyframe_points: kp.interpolation = 'CONSTANT'
camd.clip_start = 0.05
sc.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=out, compress=True)
print("CAMERA shots", len(SHOTS), "saved", out)
