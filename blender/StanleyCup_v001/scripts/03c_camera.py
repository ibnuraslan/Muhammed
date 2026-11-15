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
TWO = Vector((4.58, -0.52, 1.02))
sc.frame_set(842); _fr = bpy.data.objects['Fiance_rig']; HIS_HAND_842 = _fr.matrix_world @ _fr.pose.bones['wrist.R'].head
sc.frame_set(815); HH815 = _fr.matrix_world @ _fr.pose.bones['head'].tail
sc.frame_set(842); HH842 = _fr.matrix_world @ _fr.pose.bones['head'].tail
_wr = bpy.data.objects['Woman_rig']
sc.frame_set(748); HW748 = _wr.matrix_world @ _wr.pose.bones['head'].center
sc.frame_set(772); HW772 = _wr.matrix_world @ _wr.pose.bones['head'].center
CAM = [  # frame, camera, aim, lens, fstop
    # beat 1: street at dusk, bullet streaks in past the lens, camera whips in behind it and chases it to the siding
    (1, P(1) - D * 0.13 - SV * 0.035 + Z(0.02), P(1) + D * 4.0, 24, 8),
    (34, P(34) - SV * 0.035 + Z(0.03) - D * 0.2, P(34) + D * 2.5, 22, 8),
    (70, P(70) - D * 0.14 + SV * 0.04 + Z(0.025), P(70) + D * 1.5, 26, 8),
    (110, P(110) - D * 0.07 + SV * 0.025 + Z(0.012), P(110) + D * 0.3, 28, 5.6),
    # beat 2: macro on the impact, then follows it through the hole into the wall cavity and out of the drywall
    (139, Vector((WALL_OUT - 0.40, HOLE.y + 0.14, HOLE.z + 0.06)), HOLE, 35, 16),
    (149, Vector((WALL_OUT - 0.37, HOLE.y + 0.11, HOLE.z + 0.05)), HOLE, 37, 16),
    # CUT (f150): inside, behind the couple: the bullet bursts out of the wall behind them (f262)
    (150, Vector((6.00, 0.30, 1.45)), Vector((2.0, -1.35, 1.05)), 24, 8),
    (265, Vector((5.95, 0.28, 1.45)), Vector((2.0, -1.35, 1.05)), 25, 8),
    # CUT (f266): reverse onto their faces
    (266, Vector((1.20, 0.55, 1.18)), COUPLE + Z(0.05), 32, 5.6),
    (305, Vector((1.30, 0.50, 1.20)), COUPLE + Z(0.05), 34, 5.6),
    (330, Vector((2.30, 0.70, 1.20)), COUPLE + Z(0.05), 36, 5.6),
    (365, Vector((3.30, 0.62, 1.22)), COUPLE + Z(0.08), 32, 5.6),
    (391, Vector((3.6, -0.2, 1.3)), HER_HEAD + Vector((0.0, -0.08, -0.08)), 30, 5.6),
    # beat 4: her face freezing, his reach, bullet-level side view, low along the line with the tumbler between them
    (440, Vector((4.30, 0.12, 1.30)), HER_HEAD, 40, 5.6),
    (451, Vector((4.30, -0.10, 1.25)), HER_HEAD + Vector((0.0, -0.05, -0.05)), 30, 5.6),
    (454, Vector((4.30, -0.12, 1.25)), HER_HEAD + Vector((0.0, -0.05, -0.05)), 30, 5.6),
    # CUT (f455): her face -> his face
    (455, Vector((3.97, -0.42, 1.48)), HIS_HEAD + Vector((0.0, 0.06, -0.12)), 34, 5.6),
    (500, Vector((3.95, -0.40, 1.48)), HIS_HEAD + Vector((0.0, 0.08, -0.14)), 34, 5.6),
    (528, Vector((3.92, -0.30, 1.44)), HIS_HEAD + Vector((0.05, 0.12, -0.18)), 32, 5.6),
    (540, Vector((3.92, -0.29, 1.44)), HIS_HEAD + Vector((0.05, 0.12, -0.18)), 32, 5.6),
    # CUT (f541): the wide bullet-level view
    (541, P(541) - D * 0.45 + SV * 0.24 + Z(0.26), P(541) + D * 1.0 + Z(0.05), 32, 5.6),
    (555, P(555) - D * 0.45 + SV * 0.24 + Z(0.26), P(555) + D * 1.0 + Z(0.05), 32, 5.6),
    (606, P(606) - D * 0.40 + SV * 0.22 + Z(0.24), P(606) + D * 0.6, 40, 8),
    # beat 5: rack focus to the tumbler, orbit + condensation macro, top-down into the lid, reflection, alignment, contact point
    (640, P(640) - D * 0.30 + SV * 0.22 + Z(0.22), C3 - DXY * 0.045, 50, 2.8),
    (670, Vector((3.62, -0.10, 1.14)), C3 + Vector((0.0, 0.0, 0.0)), 50, 4),
    (700, C3 + Vector((-0.32, 0.26, 0.12)), C3 + Vector((-0.03, 0.03, 0.02)), 40, 8),
    (724, Vector((4.18, -0.45, 1.20)), C3 + Vector((0.2, 0.1, 0.2)), 45, 4),
    (736, Vector((4.17, -0.20, 1.30)), C3 + Vector((0.2, 0.1, 0.25)), 45, 4),
    (748, Vector((4.36, -0.02, 1.18)), HW748 + Vector((0.0, 0.0, -0.03)), 40, 5.6),
    (772, Vector((4.36, -0.30, 1.26)), HW772 + Vector((0.0, -0.04, -0.10)), 34, 5.6),
    (783, Vector((4.24, -0.36, 1.24)), Vector((4.70, -0.06, 1.15)), 32, 5.6),     # cup in the foreground, her face behind it
    (789, Vector((4.23, -0.37, 1.24)), Vector((4.70, -0.06, 1.15)), 32, 5.6),
    # CUT (f790): his face
    (790, HH815 + Vector((-0.28, 0.58, 0.05)), HH815 + Vector((0.02, 0.04, -0.14)), 30, 5.6),
    (815, HH815 + Vector((-0.28, 0.58, 0.05)), HH815 + Vector((0.02, 0.04, -0.14)), 30, 5.6),
    (842, HH842 + Vector((-0.30, 0.60, 0.05)), HH842 + Vector((0.04, 0.08, -0.16)), 28, 5.6),
    (879, HH842 + Vector((-0.30, 0.61, 0.05)), HH842 + Vector((0.04, 0.08, -0.16)), 28, 5.6),
    # CUT (f880): both faces, the cup between them, until the impact shot
    (880, Vector((3.62, 0.80, 1.45)), TWO + Vector((0.04, 0.0, 0.22)), 23, 5.6),
    (944, Vector((3.66, 0.84, 1.45)), TWO + Vector((0.04, 0.0, 0.20)), 24, 5.6),
    # CUT (f945): the impact, one medium shot: the cup sharp at f/11, her face behind it
    (945, C3 - DXY * 0.85 + SV * 0.28 + Z(0.20), C3 + DXY * 0.25 + Z(0.12), 38, 11),
    (1010, C3 - DXY * 0.78 + SV * 0.26 + Z(0.20), C3 + DXY * 0.25 + Z(0.12), 40, 11),
    # CUT (f1011): both reactions
    (1011, Vector((3.72, 0.86, 1.40)), Vector((4.58, -0.45, 1.12)), 22, 5.6),
    (1160, Vector((3.72, 0.86, 1.40)), Vector((4.58, -0.45, 1.12)), 22, 5.6),      # two-shot from her side wall: both reactions
    (1220, Vector((3.68, 0.90, 1.42)), Vector((4.56, -0.45, 1.14)), 22, 4),
    (1270, Vector((3.55, 0.72, 1.18)), P(1270), 34, 5.6),
    # beat 7: follow it over the edge and down, floor-level skim on the bounces, settle close-up
    (1285, Vector((3.50, 0.62, 1.12)), P(1285), 32, 5.6),
    (1303, Vector((3.50, 0.62, 1.12)), P(1285), 32, 5.6),
    # CUT (f1304): low and close on the floor where the bullet lands and bounces (sharp, f/11)
    (1304, LAND + Vector((-0.24, -0.21, 0.105)), LAND + Vector((0.0, 0.0, 0.05)), 55, 16),
    (1316, LAND + Vector((-0.25, -0.20, 0.105)), LAND + Vector((-0.02, 0.0, 0.04)), 55, 16),
    # CUT (f1317): her face, looking down at it
    (1317, Vector((4.30, 0.50, 1.15)), Vector((4.84, 0.0, 1.15)), 50, 5.6),
    (1350, Vector((4.30, 0.50, 1.16)), Vector((4.84, 0.0, 1.14)), 50, 5.6),
    # CUT (f1351): two-shot from her side wall
    (1351, Vector((3.48, 0.76, 1.40)), TWO + Vector((0.04, 0.0, 0.20)), 23, 5.6),
    (1417, Vector((3.50, 0.78, 1.42)), TWO + Vector((0.04, 0.0, 0.22)), 23, 5.6),
    (1450, Vector((3.70, 0.92, 1.45)), TWO + Vector((0.04, 0.0, 0.22)), 21, 5.6),
    (1485, Vector((3.78, 1.04, 1.45)), TWO + Vector((0.04, 0.0, 0.22)), 22, 5.6),
    (1530, Vector((3.88, 1.12, 1.46)), TWO + Vector((0.04, 0.0, 0.22)), 22, 5.6)]
def vpchip(keys):
    """monotone cubic per axis: C1-continuous, never overshoots past a framing (the bullet's speed ramp made Catmull-Rom overshoot)"""
    fx = [pchip([(f, v[i]) for f, v in keys]) for i in range(3)]
    return lambda t: Vector((fx[0](t), fx[1](t), fx[2](t)))
CUT = 150
def _seg(keys):
    return (vpchip([(f, c) for f, c, a, l, s in keys]), vpchip([(f, Vector(a)) for f, c, a, l, s in keys]),
            catmull([(f, float(l)) for f, c, a, l, s in keys]), catmull([(f, float(s)) for f, c, a, l, s in keys]))
CUTS = [1, CUT, 266, 455, 541, 790, 880, 945, 1011, 1304, 1317, 1351, END + 1]   # hard cuts (clean, no camera moves through walls, bodies or props)
SEGS = [(lo, hi, _seg([k for k in CAM if lo <= k[0] < hi])) for lo, hi in zip(CUTS[:-1], CUTS[1:])]
for f in range(1, END + 1):
    fc, fa, fl_, fs_ = next(sg for lo, hi, sg in SEGS if lo <= f < hi)
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
for f, e in ((1, 0.0), (CUT - 1, 0.0), (CUT, -0.45)):
    sc.view_settings.exposure = e; sc.view_settings.keyframe_insert("exposure", frame=f)
