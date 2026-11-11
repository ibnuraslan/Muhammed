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
    (115,  B(115) - DIR * 0.20 + Z * 0.04 + S * 0.05, B(115) + DIR * 0.8, 30, 5.6),
    (133,  G - DIR * 0.42 + S * 0.05 + Z * 0.02, G + DIR * 0.8, 26, 4.0),
    (165,  G + DIR * 0.06 + Z * 0.02, B(165) + DIR * 0.4, 24, 4.0),
    (205,  B(205) - DIR * 0.16 + Z * 0.05 - S * 0.06, B(205) + DIR * 1.5, 30, 4.0),
    (241,  B(241) - DIR * 0.16 + Z * 0.06 + S * 0.03, PI, 32, 4.0),
    (300,  B(300) - DIR * 0.18 + Z * 0.06 + S * 0.10, headc(300), 35, 4.0),
    (355,  headc(355) + V(-0.35, -0.85, 0.45), headc(355) + V(0, 0, -0.05), 30, 4.0),
    (420,  headc(420) + V(0.55, -0.35, 0.32), V(0.18, 3.40, 0.82), 30, 4.0),
    (480,  V(0.48, 3.60, 1.06), headc(480), 28, 2.8),
    (530,  headc(530) + V(-0.62, 0.42, 0.04), headc(530), 32, 2.8),
    (571,  PI + V(-0.40, -0.22, 0.05), (B(571) + PI) / 2, 40, 2.8),
    (640,  PI + V(-0.17, -0.07, 0.02), (B(640) + PI) / 2, 50, 2.8),
    (697,  PI + V(-0.12, -0.045, 0.015), PI, 55, 2.8),
    (722,  pi_w(722) + V(-0.22, -0.10, 0.06), pi_w(722) * 0.7 + headc(722) * 0.3, 45, 2.8),
    (780,  pi_w(780) + V(-0.30, 0.04, 0.12), pi_w(780), 45, 2.8),
    (835,  pi_w(835) + V(-0.10, -0.06, 0.22), hsc(835) * 0.3 + pi_w(835) * 0.7, 45, 5.6),
    (885,  pi_w(885) + V(-0.14, -0.10, 0.17), pi_w(885), 50, 5.6),
    (930,  pi_w(930) + V(-0.16, -0.02, 0.14), pi_w(930), 55, 5.6),
    (955,  pi_w(955) + V(-0.22, 0.05, 0.12), pi_w(955) + DR * 0.10, 40, 4.0),
    (990,  P_RIC + V(0.15, -0.35, 0.18), B(990), 30, 4.0),
    (1030, V(-0.70, 2.55, 1.62), B(1030), 28, 4.0),
    (1078, HOLEv + V(0.60, -0.36, 0.05), HOLEv, 32, 2.8),
    (1112, HOLEv + V(0.34, -0.15, 0.02), HOLEv, 38, 2.8),
    (1142, V(-1.05, 2.50, 1.45), headc(1142), 30, 4.0),
    (1180, headc(1180) + V(-0.90, 0.25, 0.05), headc(1180) + V(0, 0, -0.10), 30, 4.0),
    (1222, headc(1222) + V(-0.75, 0.60, 0.10), headc(1222) + V(0, 0, 0.05), 30, 4.0),
    (1265, hsc(1265) + V(-0.36, 0.30, 0.16), hsc(1265), 35, 2.8),
    (1300, hsc(1300) + V(-0.26, 0.26, 0.06), hsc(1300), 40, 2.8),
    (1335, headc(1335) + V(-0.12, 0.55, 0.0), headc(1335), 45, 2.8),
    (1390, headc(1390) + V(-0.26, 0.47, 0.03), headc(1390), 50, 2.8),
    (1445, headc(1445) + V(0.50, -0.16, 0.13), HOLEv, 32, 4.0),
    (1500, headc(1500) + V(0.42, -0.13, 0.11), HOLEv, 36, 5.6)]
cam_d = bpy.data.cameras.new("CAM_Film"); cam_d.sensor_fit = 'AUTO'; cam_d.clip_start = 0.004; cam_d.clip_end = 300
cam_d.dof.use_dof = True
cam = bpy.data.objects.new("CAM_Film", cam_d); link(cam, "Camera"); sc.camera = cam
aim = bpy.data.objects.new("CAM_Film_Aim", None); link(aim, "Camera")
tt = cam.constraints.new('TRACK_TO'); tt.target = aim; tt.track_axis = 'TRACK_NEGATIVE_Z'; tt.up_axis = 'UP_Y'
foc = bpy.data.objects.new("CAM_Film_Focus", None); link(foc, "Camera"); cam_d.dof.focus_object = foc
FOCUS = {1: B(1), 40: B(40), 80: B(80), 115: B(115), 133: G, 165: B(165), 205: B(205), 241: B(241), 300: B(300),
         990: B(990), 1030: B(1030), 1445: HOLEv, 1500: HOLEv}
fc_ = catmull([(k[0], k[1]) for k in K]); fa_ = catmull([(k[0], k[2]) for k in K])
ff_ = catmull([(k[0], FOCUS.get(k[0], k[2])) for k in K])
fl_ = catmull([(k[0], float(k[3])) for k in K]); fs_ = catmull([(k[0], float(k[4])) for k in K])
# chase segments: interpolate the camera/aim OFFSET from the bullet (the bullet is too fast for absolute keys), blend out
CH1 = [k for k in K if k[0] <= 300]; CH2 = [k for k in K if 955 <= k[0] <= 1030]
def chase(keys):
    return (catmull([(k[0], k[1] - B(k[0])) for k in keys]), catmull([(k[0], k[2] - B(k[0])) for k in keys]))
co1, ao1 = chase(CH1); co2, ao2 = chase(CH2)
def cam_at(f):
    c, a = fc_(f), fa_(f)
    if f <= 300: return B(f) + co1(f), B(f) + ao1(f)
    if f < 355:
        w = smooth((f - 300) / 55); return (B(f) + co1(300)).lerp(c, w), (B(f) + ao1(300)).lerp(a, w)
    if 990 <= f <= 1030: return B(f) + co2(f), B(f) + ao2(f)
    if 955 <= f < 990:
        w = smooth((f - 955) / 35); return c.lerp(B(f) + co2(f), w), a.lerp(B(f) + ao2(f), w)
    if 1030 < f < 1078:
        w = smooth((f - 1030) / 48); return (B(f) + co2(1030)).lerp(c, w), (B(f) + ao2(1030)).lerp(a, w)
    return c, a
for f in list(range(1, 331)) + list(range(331, 955, 2)) + list(range(955, 1080)) + list(range(1080, 1501, 2)) + [1500]:
    cpos, apos = cam_at(f)
    cam.location = cpos; cam.keyframe_insert("location", frame=f)
    aim.location = apos; aim.keyframe_insert("location", frame=f)
    foc.location = B(f) if f <= 320 or 960 <= f <= 1075 else ff_(f); foc.keyframe_insert("location", frame=f)
    cam_d.lens = fl_(f); cam_d.keyframe_insert("lens", frame=f)
    cam_d.dof.aperture_fstop = max(1.8, fs_(f)); cam_d.dof.keyframe_insert("aperture_fstop", frame=f)
CAM_KEYS = K
