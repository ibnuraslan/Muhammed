# Part of 03_animate.py: ONE camera on one Catmull-Rom spline through ~1 s framings; lens and focus keyed with it.
cam_d = bpy.data.cameras.new("CAM_Film"); cam_d.sensor_fit = "AUTO"; cam_d.clip_start = 0.002; cam_d.clip_end = 300
cam_d.dof.use_dof = True; cam_d.dof.aperture_fstop = 2.8
cam = bpy.data.objects.new("CAM_Film", cam_d); sc.collection.objects.link(cam); sc.camera = cam
aim = bpy.data.objects.new("CAM_Film_Aim", None); sc.collection.objects.link(aim)
tt = cam.constraints.new("TRACK_TO"); tt.target = aim; tt.track_axis = "TRACK_NEGATIVE_Z"; tt.up_axis = "UP_Y"
cam_d.dof.focus_object = aim
Z = lambda z: Vector((0, 0, z))
HER_HEAD = Vector((WOMAN_SEAT.x - 0.12, WOMAN_SEAT.y, 1.36)); HIS_HEAD = Vector((FIANCE_SEAT.x, FIANCE_SEAT.y + 0.12, 1.5))
COUPLE = (HER_HEAD + HIS_HEAD) / 2 - Z(0.15)
HOUSE = Vector((WALL_OUT, HOLE.y, 1.0))
sc.frame_set(1452); HANDLE_POS = CUP.matrix_world @ Vector((0.0, 0.0, 0.14))
FL = P(1395)
CAM = [  # frame, camera, aim, lens, fstop
    # beat 1: street at dusk, bullet streaks in past the lens, camera whips in behind it and chases it to the siding
    (1, P(28) - SV * 0.55 + Z(-0.12) - D * 0.1, HOUSE + Z(0.6), 18, 8),
    (34, P(34) - SV * 0.30 + Z(0.02) - D * 0.25, P(34) + D * 3.0, 20, 8),
    (70, P(70) - D * 0.22 + SV * 0.06 + Z(0.035), P(70) + D * 1.5, 24, 8),
    (110, P(110) - D * 0.07 + SV * 0.025 + Z(0.012), P(110) + D * 0.3, 28, 5.6),
    # beat 2: macro on the impact, then follows it through the hole into the wall cavity and out of the drywall
    (139, P(139) + SV * 0.07 - D * 0.04 + Z(0.012), P(139) + D * 0.004, 32, 8),
    (180, P(180) - D * 0.035 + SV * 0.004 + Z(0.004), P(180) + D * 0.05, 22, 11),
    (220, P(220) - D * 0.03 + SV * 0.003 + Z(0.003), P(220) + D * 0.04, 16, 11),
    (262, P(262) - D * 0.03 + SV * 0.002 + Z(0.002), P(262) + D * 0.04, 16, 8),
    # beat 3: room reveal over the bullet's shoulder, then overtakes it toward the couple
    (300, P(300) - D * 0.10 + SV * 0.04 + Z(0.05), COUPLE, 20, 5.6),
    (345, P(345) + D * 0.35 - SV * 0.18 + Z(0.08), COUPLE, 22, 4),
    (390, Vector((3.05, -0.72, 1.06)), COUPLE + Z(0.05), 26, 4),
    # beat 4: her face freezing, his reach, bullet-level side view, low along the line with the tumbler between them
    (440, HER_HEAD + Vector((-0.55, -0.32, -0.02)), HER_HEAD, 45, 2.8),
    (500, Vector((4.55, -0.25, 1.32)), HIS_HEAD + Vector((0.05, 0.25, -0.25)), 35, 2.8),
    (555, P(555) - D * 0.12 + SV * 0.05 + Z(0.025), HER_HEAD - Z(0.2), 40, 2.8),
    (606, P(606) - D * 0.28 - SV * 0.03 + Z(-0.02), P(606) + D * 0.1, 40, 4),
    # beat 5: rack focus to the tumbler, orbit + condensation macro, top-down into the lid, reflection, alignment, contact point
    (640, P(640) - D * 0.1 + SV * 0.05 + Z(0.02), C3 - DXY * 0.045, 50, 2.8),
    (700, C3 + Vector((-0.17, -0.15, 0.01)), C3 + Vector((-0.032, -0.03, -0.01)), 55, 4),
    (760, C3 + Vector((0.03, -0.23, 0.05)), C3 + Vector((0.005, -0.045, 0.0)), 60, 4),
    (820, C3 + Vector((0.09, -0.12, 0.36)), C3 + Z(0.13), 45, 5.6),
    (870, C3 + Vector((0.16, -0.16, 0.05)), C3 + Vector((0.03, -0.03, 0.02)), 45, 4),
    (920, P(920) - D * 0.35 + SV * 0.10 + Z(0.07), C3 + Z(0.03), 40, 4),
    (960, IMP + SV * 0.10 - D * 0.04 + Z(0.015), IMP, 55, 2.8),
    # beat 6: macro impact, orbit through the sparks, dive into the x-ray cup to see the ripples, out again, wider on their reaction
    (990, IMP + SV * 0.075 - D * 0.02 + Z(0.01), IMP, 50, 2.8),
    (1040, IMP - SV * 0.07 - D * 0.12 + Z(0.05), IMP, 38, 2.8),
    (1100, C3 - DXY * 0.075 + Z(0.09), C3 + Vector((0, 0, TOP + 0.21 - IMPACT_Z)), 26, 4),
    (1160, P(1160) + SV * 0.1 - D * 0.04 + Z(0.04), P(1160), 40, 8),
    (1220, Vector((3.85, -0.18, 1.22)), (HER_HEAD + HIS_HEAD) / 2 - Z(0.25), 26, 4),
    (1270, P(1270) + Vector((-0.16, -0.18, 0.06)), P(1270), 32, 2.8),
    # beat 7: follow it over the edge and down, floor-level skim on the bounces, settle close-up
    (1300, P(1300) + Vector((-0.25, -0.12, 0.10)), P(1300), 28, 2.8),
    (1345, Vector((FL.x - 0.42, FL.y - 0.08, 0.10)), P(1345), 26, 4),
    (1400, FL + Vector((-0.18, -0.06, 0.08)), FL, 36, 4),
    # beat 8: crane up beside the table edge, then over the table end to her, shaken, holding the dented tumbler
    (1440, Vector((FL.x - 0.45, -0.62, 0.5)), HER_HEAD + Vector((0.1, -0.1, -0.3)), 24, 4),
    (1485, Vector((3.55, -0.45, 1.12)), (HER_HEAD + HANDLE_POS) / 2, 30, 4),
    (1530, Vector((3.7, -0.2, 1.2)), (HER_HEAD + HANDLE_POS) / 2 + Z(0.03), 34, 4)]
fc = catmull([(f, c) for f, c, a, l, s in CAM]); fa = catmull([(f, Vector(a)) for f, c, a, l, s in CAM])
fl_ = catmull([(f, float(l)) for f, c, a, l, s in CAM]); fs_ = catmull([(f, float(s)) for f, c, a, l, s in CAM])
for f in range(1, END + 1):
    cl = fc(f)
    if cl.x > 0.05: cl.z = max(cl.z, 0.05)
    cam.location = cl; cam.keyframe_insert("location", frame=f)
    aim.location = fa(f); aim.keyframe_insert("location", frame=f)
    cam_d.lens = fl_(f); cam_d.keyframe_insert("lens", frame=f)
    cam_d.dof.aperture_fstop = fs_(f); cam_d.dof.keyframe_insert("aperture_fstop", frame=f)
sc["cam_framings"] = [c[0] for c in CAM]
