# Part of 03_animate.py: ONE camera on one Catmull-Rom path through ~32 framings (new framing about every second, no cuts).
def headc(f): return head_delta(f) @ HEAD_C_REST
def pi_w(f): return hs_world(f) @ PI_LOC
def hsc(f): return hs_world(f).translation.copy()
Z = Vector((0, 0, 1)); S = DIR.cross(Z).normalized()       # S = right of the bullet's travel
B = lambda f: BPOS[int(f)]
V = lambda *a: Vector(a)
HOLEv = Vector(sc["HOLE"])
K = [  # frame, camera, aim, lens, f-stop
    (1,    B(1) - DIR * 0.12 + S * 0.03 + Z * 0.012,  B(1) + DIR * 0.4 - S * 0.03, 35, 8.0),
    (40,   B(40) - DIR * 0.14 + S * 0.05 + Z * 0.025, B(40) + DIR * 0.10 - S * 0.02, 32, 8.0),
    (80,   B(80) + S * 0.22 + Z * 0.06 - DIR * 0.02, B(80) + DIR * 0.03, 28, 8.0),
    (100,  B(100) - DIR * 0.13 + S * 0.10 + Z * 0.03, B(100) + DIR * 0.3 - S * 0.09, 30, 8.0),
    (115,  B(115) - DIR * 0.20 + Z * 0.04 + S * 0.05, B(115) + DIR * 0.8, 30, 5.6),
    (133,  G - DIR * 0.42 + S * 0.05 + Z * 0.02, G + DIR * 0.8, 26, 4.0),
    (165,  G + DIR * 0.06 + Z * 0.02, B(165) + DIR * 0.4, 24, 4.0),
    (205,  B(205) - DIR * 0.16 + Z * 0.05 - S * 0.06, B(205) + DIR * 1.5, 30, 8.0),
    (241,  B(241) - DIR * 0.16 + Z * 0.06 + S * 0.03, PI, 32, 11.0),
    (300,  B(300) - DIR * 0.20 + Z * 0.06 + S * 0.02, (B(300) + headc(300)) / 2, 35, 11.0),
    (328,  headc(328) + V(0.40, -0.62, 0.70), headc(328) + V(0, 0.05, -0.05), 30, 8.0),
    (355,  headc(355) + V(0.62, -0.10, 0.30), headc(355) + V(0, 0.05, -0.08), 30, 8.0),
    (420,  headc(420) + V(0.55, 0.30, 0.30), V(0.12, 3.38, 0.86), 30, 8.0),
    (480,  V(0.48, 3.60, 1.06), headc(480), 28, 2.8),
    (530,  headc(530) + V(-0.62, 0.42, 0.04), headc(530), 32, 2.8),
    # v007: 557-1142 restaged as simple steady framings (client: sharp, head always in frame, no cutaway, no empty wall)
    (571,  headc(571) + V(-0.80, 0.26, 0.08), headc(571) * 0.70 + B(571) * 0.30, 35, 8.0),
    (640,  headc(640) + V(-0.70, 0.22, 0.07), headc(640) * 0.72 + PI * 0.28, 37, 8.0),
    (697,  headc(697) + V(-0.62, 0.18, 0.06), headc(697) * 0.55 + PI * 0.45, 40, 8.0),
    (760,  headc(760) + V(-0.64, 0.26, 0.08), headc(760) * 0.65 + pi_w(760) * 0.35, 38, 8.0),
    (835,  headc(835) + V(-0.56, 0.20, 0.07), headc(835) * 0.45 + pi_w(835) * 0.55, 42, 8.0),
    (900,  headc(900) + V(-0.54, 0.10, 0.09), headc(900) * 0.45 + pi_w(900) * 0.55, 42, 8.0),
    (949,  headc(949) + V(-0.30, 0.58, 0.08), headc(949), 36, 8.0),
    (995,  headc(995) + V(0.55, 0.78, 0.12), headc(995) * 0.80 + HOLEv * 0.20, 26, 8.0),
    (1040, headc(1040) + V(0.85, 0.62, 0.14), headc(1040) * 0.74 + HOLEv * 0.26, 26, 8.0),
    (1078, headc(1078) + V(0.92, 0.55, 0.14), headc(1078) * 0.72 + HOLEv * 0.28, 26, 8.0),
    (1112, headc(1112) + V(0.85, 0.58, 0.13), headc(1112) * 0.76 + HOLEv * 0.24, 27, 8.0),
    (1142, headc(1142) + V(0.55, 0.52, 0.10), headc(1142), 32, 8.0),
    (1180, headc(1180) + V(-0.90, 0.25, 0.05), headc(1180) + V(0, 0, -0.10), 30, 4.0),
    (1222, headc(1222) + V(-0.75, 0.60, 0.10), headc(1222) + V(0, 0, 0.05), 30, 4.0),
    (1265, hsc(1265) + V(-0.55, 0.22, 0.24), hsc(1265) * 0.6 + headc(1265) * 0.4, 32, 8.0),
    (1300, hsc(1300) + V(-0.46, 0.20, 0.20), hsc(1300) * 0.45 + headc(1300) * 0.55, 32, 8.0),
    (1315, headc(1315) + V(-0.22, 0.56, -0.06), headc(1315) * 0.75 + hsc(1315) * 0.25, 36, 8.0),   # beat 10: his face, the broken headset below
    (1335, headc(1335) + V(-0.12, 0.50, -0.06), headc(1335) + V(0, 0, -0.02), 45, 8.0),
    (1390, headc(1390) + V(-0.24, 0.46, -0.06), headc(1390) + V(0, 0, -0.02), 48, 8.0),
    (1418, headc(1418) + V(0.32, 0.40, 0.08), headc(1418), 32, 6.0),
    (1445, headc(1445) + V(0.50, 0.24, 0.04), headc(1445) * 0.84 + HOLEv * 0.16, 30, 8.0),
    (1475, headc(1475) + V(0.56, 0.16, 0.03), headc(1475) * 0.80 + HOLEv * 0.20, 31, 8.0),
    (1500, headc(1500) + V(0.52, 0.12, 0.01), headc(1500) * 0.82 + HOLEv * 0.18, 33, 8.0)]   # end on his face, the hole behind him
cam_d = bpy.data.cameras.new("CAM_Film"); cam_d.sensor_fit = 'AUTO'; cam_d.clip_start = 0.004; cam_d.clip_end = 300
cam_d.dof.use_dof = True
cam = bpy.data.objects.new("CAM_Film", cam_d); link(cam, "Camera"); sc.camera = cam
aim = bpy.data.objects.new("CAM_Film_Aim", None); link(aim, "Camera")
tt = cam.constraints.new('TRACK_TO'); tt.target = aim; tt.track_axis = 'TRACK_NEGATIVE_Z'; tt.up_axis = 'UP_Y'
foc = bpy.data.objects.new("CAM_Film_Focus", None); link(foc, "Camera"); cam_d.dof.focus_object = foc
FOCUS = {640: B(640), 1: B(1), 40: B(40), 80: B(80), 115: B(115), 133: G, 165: B(165), 205: B(205), 241: B(241), 300: B(300),
         1475: headc(1475), 1500: headc(1500)}
fc_ = catmull([(k[0], k[1]) for k in K])
_fa = [pchip([(k[0], k[2][i]) for k in K]) for i in range(3)]      # monotone aim: no overshoot toward far targets
fa_ = lambda f: Vector([g(f) for g in _fa])
ff_ = catmull([(k[0], FOCUS.get(k[0], k[2])) for k in K])
fl_ = catmull([(k[0], float(k[3])) for k in K]); fs_ = catmull([(k[0], float(k[4])) for k in K])
# chase segments: interpolate the camera/aim OFFSET from the bullet (the bullet is too fast for absolute keys), blend out
CH1 = [k for k in K if k[0] <= 300]
def chase(keys):
    return (catmull([(k[0], k[1] - B(k[0])) for k in keys]), catmull([(k[0], k[2] - B(k[0])) for k in keys]))
co1, ao1 = chase(CH1)
def cam_at(f):
    c, a = fc_(f), fa_(f)
    if f <= 300: return B(f) + co1(f), B(f) + ao1(f)
    if f < 355:
        w = smooth((f - 300) / 55); return (B(f) + co1(300)).lerp(c, w), (B(f) + ao1(300)).lerp(a, w)
    return c, a
for f in list(range(1, 331)) + list(range(331, 955, 2)) + list(range(955, 1080)) + list(range(1080, 1501, 2)) + [1500]:
    cpos, apos = cam_at(f)
    cam.location = cpos; cam.keyframe_insert("location", frame=f)
    aim.location = apos; aim.keyframe_insert("location", frame=f)
    foc.location = B(f) if f <= 320 else ff_(f); foc.keyframe_insert("location", frame=f)
    cam_d.lens = fl_(f); cam_d.keyframe_insert("lens", frame=f)
    cam_d.dof.aperture_fstop = max(1.8, fs_(f)); cam_d.dof.keyframe_insert("aperture_fstop", frame=f)
CAM_KEYS = K
