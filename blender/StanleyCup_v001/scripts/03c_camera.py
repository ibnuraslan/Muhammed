# Part of 03_animate.py: ONE camera on one Catmull-Rom spline through ~1 s framings; lens and focus keyed with it.
cam_d = bpy.data.cameras.new("CAM_Film"); cam_d.sensor_fit = "AUTO"; cam_d.clip_start = 0.002; cam_d.clip_end = 300
cam_d.dof.use_dof = True; cam_d.dof.aperture_fstop = 2.8
cam = bpy.data.objects.new("CAM_Film", cam_d); sc.collection.objects.link(cam); sc.camera = cam
aim = bpy.data.objects.new("CAM_Film_Aim", None); sc.collection.objects.link(aim)
tt = cam.constraints.new("TRACK_TO"); tt.target = aim; tt.track_axis = "TRACK_NEGATIVE_Z"; tt.up_axis = "UP_Y"
cam_d.dof.focus_object = aim
Z = lambda z: Vector((0, 0, z))
HER_HEAD = Vector((WOMAN_SEAT.x - 0.12, WOMAN_SEAT.y, 1.27)); HIS_HEAD = Vector((FIANCE_SEAT.x, FIANCE_SEAT.y + 0.12, 1.5))
COUPLE = (HER_HEAD + HIS_HEAD) / 2 - Z(0.15)
HOUSE = Vector((WALL_OUT, HOLE.y, 1.0))
sc.frame_set(1452); HANDLE_POS = CUP.matrix_world @ Vector((0.0, 0.0, 0.14))
FL = P(1395)
sc.frame_set(842); _fr = bpy.data.objects['Fiance_rig']; HIS_HAND_842 = _fr.matrix_world @ _fr.pose.bones['wrist.R'].head
sc.frame_set(815); HH815 = _fr.matrix_world @ _fr.pose.bones['head'].tail
sc.frame_set(842); HH842 = _fr.matrix_world @ _fr.pose.bones['head'].tail
CAM = [  # frame, camera, aim, lens, fstop
    # beat 1: street at dusk, bullet streaks in past the lens, camera whips in behind it and chases it to the siding
    (1, P(1) - D * 0.13 - SV * 0.035 + Z(0.02), P(1) + D * 4.0, 24, 8),
    (34, P(34) - SV * 0.035 + Z(0.03) - D * 0.2, P(34) + D * 2.5, 22, 8),
    (70, P(70) - D * 0.14 + SV * 0.04 + Z(0.025), P(70) + D * 1.5, 26, 8),
    (110, P(110) - D * 0.07 + SV * 0.025 + Z(0.012), P(110) + D * 0.3, 28, 5.6),
    # beat 2: macro on the impact, then follows it through the hole into the wall cavity and out of the drywall
    (139, P(139) + SV * 0.015 - D * 0.13 + Z(0.01), P(139) + D * 0.01, 30, 8),
    (180, P(180) - D * 0.035 + SV * 0.004 + Z(0.004), P(180) + D * 0.05, 22, 11),
    (198, P(198) - D * 0.02 + SV * 0.002 + Z(0.002), P(198) + D * 0.03, 16, 8),
    (220, Vector((-0.072, P(220).y + 0.12, P(220).z + 0.035)), P(220), 16, 8),
    (240, Vector((-0.06, P(240).y - 0.11, P(240).z + 0.02)), P(240), 16, 8),
    (254, P(254) - D * 0.03 + SV * 0.003 + Z(0.003), P(254) + D * 0.05, 16, 8),
    (262, P(262) - D * 0.03 + SV * 0.002 + Z(0.002), P(262) + D * 0.04, 16, 8),
    # beat 3: room reveal over the bullet's shoulder, then overtakes it toward the couple
    (300, P(300) - D * 0.10 + SV * 0.04 + Z(0.05), COUPLE, 20, 5.6),
    (330, Vector((2.3, -0.75, 1.15)), COUPLE + Z(0.05), 26, 5.6),
    (365, Vector((3.35, -0.55, 1.2)), COUPLE + Z(0.08), 28, 5.6),
    (391, Vector((3.6, -0.2, 1.3)), HER_HEAD + Vector((0.0, -0.08, -0.08)), 30, 5.6),
    # beat 4: her face freezing, his reach, bullet-level side view, low along the line with the tumbler between them
    (440, Vector((4.30, 0.12, 1.30)), HER_HEAD, 40, 5.6),
    (451, Vector((4.55, -0.05, 1.38)), HER_HEAD + Vector((0.0, -0.05, 0.0)), 36, 5.6),
    (470, Vector((4.98, -0.42, 1.42)), HIS_HEAD + Vector((0.0, 0.1, -0.1)), 30, 5.6),
    (500, Vector((4.55, -0.25, 1.32)), HIS_HEAD + Vector((0.05, 0.25, -0.25)), 35, 2.8),
    (528, Vector((4.62, -0.05, 1.18)), HIS_HEAD + Vector((0.15, 0.3, -0.35)), 30, 4),
    (555, P(555) - D * 0.09 + SV * 0.022 + Z(0.012), P(555) + D * 1.2, 32, 5.6),
    (606, P(606) - D * 0.10 - SV * 0.02 + Z(-0.008), P(606), 40, 8),
    # beat 5: rack focus to the tumbler, orbit + condensation macro, top-down into the lid, reflection, alignment, contact point
    (640, P(640) - D * 0.1 + SV * 0.05 + Z(0.02), C3 - DXY * 0.045, 50, 2.8),
    (700, C3 + Vector((-0.14, 0.13, 0.02)), C3 + Vector((-0.03, 0.03, -0.01)), 55, 4),
    (724, Vector((4.36, -0.45, 1.17)), C3 + Vector((0.2, 0.1, 0.2)), 45, 4),
    (748, Vector((4.52, -0.14, 1.27)), HER_HEAD + Vector((0.0, 0.02, 0.02)), 45, 2.8),
    (772, Vector((4.52, -0.30, 1.30)), C3 + Z(0.12), 40, 5.6),
    (795, C3 + Vector((0.08, -0.10, 0.34)), C3 + Z(0.13), 40, 5.6),
    (815, HH815 + Vector((0.32, 0.55, 0.02)), HH815 + Vector((0.0, 0.0, -0.12)), 30, 5.6),
    (842, HH842 + Vector((0.36, 0.6, 0.02)), HH842 + Vector((0.06, 0.1, -0.16)), 26, 5.6),
    (885, Vector((4.15, -0.05, 1.12)), C3 + Vector((0.03, 0.0, 0.03)), 40, 5.6),
    (920, P(920) - D * 0.35 + SV * 0.10 + Z(0.07), C3 + Z(0.03), 40, 4),
    (960, IMP + SV * 0.10 - D * 0.04 + Z(0.015), IMP, 55, 2.8),
    # beat 6: macro impact, orbit through the sparks, dive into the x-ray cup to see the ripples, out again, wider on their reaction
    (990, IMP + SV * 0.075 - D * 0.02 + Z(0.01), IMP, 50, 2.8),
    (1040, IMP - SV * 0.07 - D * 0.12 + Z(0.05), IMP, 38, 2.8),
    (1100, C3 - DXY * 0.07 + Z(0.21), C3 + Vector((0, 0, sc['cup_top'] + 0.21 - IMPACT_Z)), 30, 5.6),
    (1160, Vector((3.95, -0.05, 1.08)), P(1160) + Vector((0.05, -0.05, 0.08)), 30, 5.6),
    (1220, Vector((3.85, -0.18, 1.22)), (HER_HEAD + HIS_HEAD) / 2 - Z(0.25), 26, 4),
    (1270, Vector((3.30, -0.55, 1.05)), P(1270), 32, 5.6),
    # beat 7: follow it over the edge and down, floor-level skim on the bounces, settle close-up
    (1300, Vector((3.35, -1.30, 0.90)), P(1300), 36, 5.6),
    (1345, Vector((3.40, -1.15, 0.14)), P(1345), 36, 5.6),
    (1400, FL + Vector((0.0, -0.16, 0.045)), FL, 50, 5.6),
    # beat 8: crane up beside the table edge, then over the table end to her, shaken, holding the dented tumbler
    (1417, Vector((3.4, -0.6, 1.05)), HER_HEAD + Vector((0.0, 0.0, -0.1)), 26, 5.6),
    (1450, Vector((3.45, -0.5, 1.02)), HER_HEAD + Vector((0.05, -0.05, -0.15)), 28, 5.6),
    (1485, Vector((3.55, -0.45, 1.12)), (HER_HEAD + HANDLE_POS) / 2, 30, 4),
    (1530, Vector((3.7, -0.2, 1.2)), (HER_HEAD + HANDLE_POS) / 2 + Z(0.03), 34, 4)]
def vpchip(keys):
    """monotone cubic per axis: C1-continuous, never overshoots past a framing (the bullet's speed ramp made Catmull-Rom overshoot)"""
    fx = [pchip([(f, v[i]) for f, v in keys]) for i in range(3)]
    return lambda t: Vector((fx[0](t), fx[1](t), fx[2](t)))
fc = vpchip([(f, c) for f, c, a, l, s in CAM]); fa = vpchip([(f, Vector(a)) for f, c, a, l, s in CAM])
fl_ = catmull([(f, float(l)) for f, c, a, l, s in CAM]); fs_ = catmull([(f, float(s)) for f, c, a, l, s in CAM])
for f in range(1, END + 1):
    cl = fc(f)
    if cl.x > 0.05: cl.z = max(cl.z, 0.05)
    cam.location = cl; cam.keyframe_insert("location", frame=f)
    al = fa(f)
    if al.x > 0.05: al.z = max(al.z, 0.006)
    aim.location = al; aim.keyframe_insert("location", frame=f)
    cam_d.lens = fl_(f); cam_d.keyframe_insert("lens", frame=f)
    cam_d.dof.aperture_fstop = fs_(f); cam_d.dof.keyframe_insert("aperture_fstop", frame=f)
sc["cam_framings"] = [c[0] for c in CAM]

# exposure: dusk exterior at 0, the lamp-lit room at -0.45 (ramped while the camera is inside the wall)
for f, e in ((1, 0.0), (150, 0.0), (240, -0.45)):
    sc.view_settings.exposure = e; sc.view_settings.keyframe_insert("exposure", frame=f)
