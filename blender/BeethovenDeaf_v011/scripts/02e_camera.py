# 02e: ONE continuous camera (no cuts). Framings are keyed relative to the actual mouth / clamp / hands / ear positions of
# the animated composer, then interpolated with clamped Bezier (no overshoot), Track To an aim empty with world up (level).
def WREST(p, f):
    sc.frame_set(f); return COMP.matrix_world @ PB["head"].matrix @ HRi @ p
FACE_REST = Vector((0.0, -0.085, 1.585))
def pts(f):
    sc.frame_set(f)
    return dict(M=BITE.matrix_world.translation.copy(), C=CLAMP.matrix_world.translation.copy(),
                H=(COMP.matrix_world @ ((PB["wrist.L"].head + PB["wrist.R"].head) / 2)),
                E=WREST(EAR_C, f), F=WREST(FACE_REST, f), K=WREST(COCH_C, f))
V = Vector
KEYS_ = [
    (1,    lambda p: (p["M"] + V((-0.30, -0.40, 0.07)), p["M"] + V((0, 0, 0.035)), 38, 6.0)),
    (70,   lambda p: (p["M"] + V((-0.36, -0.33, 0.03)), p["M"] + V((0, -0.03, 0.03)), 38, 6.0)),
    (T["attached"], lambda p: (p["M"].lerp(p["C"], 0.45) + V((-0.34, 0.02, 0.10)), p["M"].lerp(p["C"], 0.5), 32, 8.0)),
    (T["piano"] + 10, lambda p: (p["C"] + V((-0.40, -0.10, 0.16)), p["C"] + V((0, 0.07, 0.0)), 34, 9.0)),
    (T["playing"] + 10, lambda p: (p["H"] + V((-0.50, -0.12, 0.36)), p["H"] + V((0, 0.08, 0.12)), 30, 8.0)),
    (T["pianos"], lambda p: (p["C"].lerp(p["M"], 0.3) + V((-0.38, -0.05, 0.08)), p["C"].lerp(p["M"], 0.3), 30, 8.0)),
    (T["through"] - 15, lambda p: (p["C"].lerp(p["M"], 0.7) + V((-0.34, -0.02, 0.05)), p["C"].lerp(p["M"], 0.7), 32, 8.0)),
    (T["into"], lambda p: (p["M"].lerp(p["E"], 0.45) + V((-0.42, -0.12, 0.03)), p["M"].lerp(p["E"], 0.45), 38, 8.0)),
    (T["reached"] - 24, lambda p: (p["M"].lerp(p["E"], 0.5) + V((-0.32, -0.08, 0.02)), p["M"].lerp(p["E"], 0.5), 42, 9.0)),
    (T["inner"] + 16, lambda p: (p["E"] + V((-0.32, -0.08, 0.02)), p["E"] + V((0, -0.03, -0.02)), 48, 10.0)),
    (T["sent"], lambda p: (p["F"].lerp(p["E"], 0.5) + V((-0.46, -0.16, 0.05)), p["F"].lerp(p["E"], 0.5), 40, 8.0)),
    (T["skull"] - 26, lambda p: (p["F"].lerp(p["E"], 0.5) + V((-0.42, -0.30, 0.07)), p["F"].lerp(p["E"], 0.5), 40, 8.0)),
    (T["bypass"], lambda p: (p["E"] + V((-0.30, -0.12, -0.03)), p["E"].lerp(p["K"], 0.3), 52, 10.0)),
    (T["eardrum"] + 6, lambda p: (p["E"] + V((-0.27, -0.06, -0.04)), p["E"].lerp(p["K"], 0.4), 58, 11.0)),
    (T["hear"], lambda p: (p["E"].lerp(p["F"], 0.5) + V((-0.30, -0.14, 0.02)), p["E"].lerp(p["F"], 0.5), 45, 9.0)),
    (T["using"] + 4, lambda p: (p["F"] + V((-0.36, -0.40, 0.0)), p["F"], 40, 8.0)),
    (T["beethoven"], lambda p: (V((-0.95, -0.55, 1.55)), V((0.0, 0.25, 1.10)), 32, 8.0)),
    (T["composing"] + 14, lambda p: (V((-0.75, -1.25, 1.90)), V((0.0, 0.25, 1.05)), 28, 8.0)),
    (1280, lambda p: (V((-0.10, -1.45, 2.35)), V((0.10, 0.40, 1.30)), 27, 8.0)),
    (END,  lambda p: (V((0.40, -1.40, 2.35)), V((0.18, 0.45, 1.35)), 27, 8.0)),
]
cd_ = bpy.data.cameras.new("CAM_Film"); CAM = bpy.data.objects.new("CAM_Film", cd_); sc.collection.objects.link(CAM); sc.camera = CAM
AIM = bpy.data.objects.new("CAM_Film_Aim", None); sc.collection.objects.link(AIM)
tt = CAM.constraints.new('TRACK_TO'); tt.target = AIM; tt.track_axis = 'TRACK_NEGATIVE_Z'; tt.up_axis = 'UP_Y'
cd_.clip_start = 0.01; cd_.sensor_fit = 'AUTO'; cd_.sensor_width = 36
cd_.dof.use_dof = True; cd_.dof.focus_object = AIM
for f, fn in KEYS_:
    c, a, lens, fst = fn(pts(f))
    CAM.location = c; AIM.location = a; cd_.lens = lens; cd_.dof.aperture_fstop = fst
    CAM.keyframe_insert("location", frame=f); AIM.keyframe_insert("location", frame=f)
    cd_.keyframe_insert("lens", frame=f); cd_.dof.keyframe_insert("aperture_fstop", frame=f)
for idb in (CAM, AIM, cd_):
    for fc in iter_fcurves(idb.animation_data.action):
        for kp in fc.keyframe_points: kp.interpolation = 'BEZIER'; kp.handle_left_type = kp.handle_right_type = 'AUTO_CLAMPED'
        fc.update()
log("camera keys", [k[0] for k in KEYS_])
