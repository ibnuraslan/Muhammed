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
CH = bone_pt(CA, "head"); FH = bone_pt(FO, "head"); FS = bone_pt(FO, "spine03")
COCK_FRONT = ((0.45, 3.18, 1.55), (0.44, 3.15, 1.54))          # outside the windscreen, looking back at his face
COCK_SIDE = ((-1.02, 1.76, 1.60), (-1.01, 1.72, 1.59))         # front-left, inside the windscreen pillar: face, arms and yoke
STAND_FRONT = ((0.30, 3.18, 1.78), (0.29, 3.15, 1.77))          # outside the windscreen right of the centre post: his face while standing
CENTRE = ((-0.02, 1.08, 1.76), (0.0, 1.02, 1.75))              # between the pilot seats, looking aft
WINDOW = ((-0.52, 1.50, 1.32), (-0.52, 1.56, 1.31))            # captain's eye line, out of the windscreen
REAR = ((-0.32, -0.85, 1.72), (-0.30, -0.80, 1.70))            # doorway, looking forward over the cockpit
HAUL_HI = ((0.35, 2.35, 1.70), (0.34, 2.33, 1.70))             # v009c: lower than v009b (the overhead panel cut the top of the frame)
INFRONT = ((-0.25, 2.45, 1.62), (-0.24, 2.43, 1.62))          # v009c: inside the windscreen, left of centre (outside, the frames and the nose filled the lens; right of centre the FO's arm did)
SIDE_F = ((-0.98, 1.95, 1.56), (-0.97, 1.92, 1.56))           # v009c: front-left, tighter on his face and hands on the yoke
OTS = ((-0.80, 0.30, 1.75), (-0.78, 0.36, 1.74))               # behind-left, over the seats to the windscreen
OTS2 = ((-0.15, 0.60, 1.90), (-0.14, 0.63, 1.89))             # v009g: high between the seats (from OTS the captain seat back filled half the frame)
SHOTS = [
    # beat 1-2: the cabin; by 0.9 s a close shot of his face waking (director: it was unclear who "you" is)
    (0.00, 0.90, (0.05, -3.02, 1.85), (0.05, -3.04, 1.85), YH, 30),
    (0.90, 2.80, (0.15, -3.50, 1.75), (0.13, -3.45, 1.74), YH, 55),
    (2.80, 4.06, (0.15, -3.30, 1.85), (0.12, -3.35, 1.82), mid(YH, fixed((-0.95, -4.50, 0.80)), 0.5), 28),
    (4.06, 5.40, (0.00, -6.60, 1.80), (0.00, -6.50, 1.78), YH, 30),
    (5.40, 6.74, (0.05, -3.00, 1.85), (0.05, -3.05, 1.85), mid(YH, fixed((-1.45, -4.70, 1.25)), 0.35), 26),
    # beat 3: up the aisle
    (6.74, 8.20, (0.00, -1.00, 1.70), (0.00, -1.05, 1.70), YH, 35),
    # beat 3-5 (v009c): from the cockpit, through the door: he comes up the aisle toward us (the follow shot from behind
    # showed arms coming up from the frame corners), then crouches beside the captain in the doorway
    (8.20, 8.60, "follow", (0.08, -1.60, 1.00), YH, 60),           # tight on his head and shoulders as he reaches the door
    (8.60, 10.93, CENTRE[0], CENTRE[1], mid(YH, fixed((0.0, -0.60, 1.20)), 0.5), 26),
    (10.93, 13.22, INFRONT[0], INFRONT[1], mid(YH, CH, 0.2), 24),     # crouched beside the captain, then steps over him
    # beat 6-8: the first officer, the radio
    (13.22, 15.50, (-0.90, 2.20, 1.55), (-0.89, 2.17, 1.55), mid(YH, FH, 0.3), 24),
    (15.50, 16.50, REAR[0], REAR[1], mid(YH, fixed((0.10, 1.40, 0.90)), 0.4), 30),     # v009c: from the doorway (inside-front had the FO's sleeve in the lens)
    (16.50, 17.60, (-0.90, 2.20, 1.55), (-0.89, 2.18, 1.55), YH, 30),     # v009g: his face at the panel (the back view held 2.1 s)
    (17.60, 19.20, (-1.00, 2.15, 1.45), (-0.99, 2.12, 1.45), mid(YH, fixed((0.00, 1.50, 0.85)), 0.7), 45),
    (19.20, 20.40, INFRONT[0], INFRONT[1], YH, 35),
    (20.40, 21.24, (-1.00, 2.15, 1.45), (-0.99, 2.12, 1.45), YH, 35),
    # beat 9: the haul (v009c: from behind while he reaches in, his arms hidden by his body; then high from the front)
    (21.24, 23.30, OTS[0], OTS[1], mid(YH, FH, 0.5), 26),            # behind-left: his reaching arms stay behind his body
    # v009h (client): the FO passed through the seat back during the haul. Re-staged as a cut: from behind him, both
    # hands on the FO's shoulders (0.5 s); the window; then the FO already on the floor beside the seat, the boy beside him
    (23.30, 23.80, REAR[0], REAR[1], mid(YH, FH, 0.5), 22),
    (23.80, 24.80, WINDOW[0], WINDOW[1], fixed((-0.52, 9.0, 0.3)), 24),
    (24.80, 25.30, WINDOW[0], WINDOW[1], fixed((-0.52, 9.0, -0.6)), 24),
    (25.30, 25.82, HAUL_HI[0], HAUL_HI[1], mid(YH, FH, 0.6), 22),
    # beat 10-11: alarms, the dive
    (25.82, 27.40, INFRONT[0], INFRONT[1], YH, 26),
    (27.40, 28.40, WINDOW[0], WINDOW[1], fixed((-0.52, 9.0, -0.6)), 24),
    (28.40, 29.20, REAR[0], REAR[1], mid(YH, fixed((0.4, 2.4, 1.1)), 0.4), 22),
    (29.20, 30.32, (-0.90, 2.20, 1.55), (-0.89, 2.18, 1.55), YH, 40),     # v009g: his face as he lunges for the seat (the doorway wide held 1.8 s)
    # beat 12-19: flying it. v009c: no shots through the windscreen at his front (arms folded behind the glare shield);
    # side shots with his hands on the yoke, the over-the-shoulder, and window inserts of 1 s at most
    (30.32, 31.90, COCK_SIDE[0], COCK_SIDE[1], YC, 28),
    (31.90, 33.42, SIDE_F[0], SIDE_F[1], YH, 40),
    (33.42, 34.40, WINDOW[0], WINDOW[1], fixed((-0.52, 9.0, 0.6)), 24),
    (34.40, 35.90, OTS2[0], OTS2[1], fixed((0.55, 2.20, 1.00)), 24),
    (35.90, 37.06, COCK_SIDE[0], COCK_SIDE[1], YC, 30),
    (37.06, 38.70, SIDE_F[0], SIDE_F[1], YH, 42),
    (38.70, 40.10, OTS2[0], OTS2[1], fixed((0.55, 2.20, 1.00)), 26),
    (40.10, 41.30, COCK_SIDE[0], COCK_SIDE[1], YC, 28),
    (41.30, 42.30, WINDOW[0], WINDOW[1], fixed((-0.52, 9.0, 0.2)), 24),
    (42.30, 44.20, SIDE_F[0], SIDE_F[1], YH, 40),
    (44.20, 46.00, COCK_SIDE[0], COCK_SIDE[1], YC, 26),
    (46.00, 47.00, WINDOW[0], WINDOW[1], fixed((-0.52, 9.0, 0.3)), 24),
    (47.00, 48.40, OTS2[0], OTS2[1], fixed((0.55, 2.20, 1.00)), 24),
    (48.40, 49.30, COCK_SIDE[0], COCK_SIDE[1], YC, 28),            # v009g: both arms to the hands (the tight side shot read as a missing arm)
    (49.30, 50.30, OTS2[0], OTS2[1], fixed((0.55, 2.20, 1.00)), 24),   # v009h: from 49.3 s his left arm points at the side camera (a stub); from above both arms read
    (50.30, 51.10, WINDOW[0], WINDOW[1], fixed((-0.52, 9.0, 0.3)), 24),
    (51.10, 51.80, (1.00, 0.90, 1.90), (0.99, 0.88, 1.89), mid(FH, FS, 0.4), 22),   # the first officer on his back, face up (0.7 s)
    (51.80, 53.00, COCK_SIDE[0], COCK_SIDE[1], YC, 28),
    (53.00, 53.90, WINDOW[0], WINDOW[1], fixed((-0.52, 9.0, 0.3)), 24),
    (53.90, 55.72, SIDE_F[0], SIDE_F[1], YH, 40),
    # beat 19: the close-up of his face, three-quarter from front-left, slow push in
    (55.72, 58.00, (0.05, 2.50, 1.33), (0.09, 2.42, 1.33), YH, 50),   # at his eye level (from above the lids hid the eyes)
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
        p = rp[f] + Vector(p1) if rp else Vector(p0).lerp(Vector(p1), u)
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
for o in bpy.data.objects:          # v009c: the sun visors hung in front of the inside cameras as a dark blurred slab
    if o.name.startswith("SUNSHADE"): o.visible_camera = False
for n_ in ("YOU.high-poly", "YOU.eyelashes01"):          # v009c: no eye/lash self-shadow (the eyes read as dark holes)
    bpy.data.objects[n_].visible_shadow = False
# v009c: the close-up was blown out by the face fill (front-on, 25 W); dim it for the last shot
ff = bpy.data.objects["L_face_fill"].data
ff.energy = 25; ff.keyframe_insert("energy", frame=FN(55.72) - 1)
ff.energy = 12; ff.keyframe_insert("energy", frame=FN(55.72))
for fc in ff.animation_data.action.layers[0].strips[0].channelbags[0].fcurves:
    for kp in fc.keyframe_points: kp.interpolation = 'CONSTANT'
sc.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=out, compress=True)
print("CAMERA shots", len(SHOTS), "saved", out)
