# B3..B8 for 03_anim.py (exec'd there; uses its helpers)
LEFT_FD = Vector((-0.45, -0.75, -0.45)); LEFT_PN = Vector((-0.2, -0.3, 1.0))

def look(H, f0, f1, flex, head_fn, step=20, period=170, amp=1.2):
    for f in list(range(f0, f1 + 1, step)) + [f1]:
        ph = math.sin(2 * math.pi * (f - f0) / period); hx, hz = head_fn(f)
        H.key_spine(f, flex=flex + amp * ph, head=(hx + 1.5 * ph, hz))

def rest_hands_on_bench(rig, f, xs, y=-0.24, flat=False):
    for s, x in zip("RL", xs):
        sx = 1 if s == "L" else -1
        hx = rig.matrix_world.translation.x if False else x
        place_hand(rig, s, f, Vector((x, 0.09 - 0.12, 0.69)), Vector((0, 0, -1)), Vector((-0.1 * sx, -1, -0.25)))   # on the thigh, under the bench
        apply_pose(rig, s, "relaxed", f)

def ease(u): u = max(0.0, min(1.0, u)); return u * u * (3 - 2 * u)

# ================================================================== B3 straight pins hurt (811..1200)
def beat_B3():
    f0, f1 = WIN["B3"]; rig, R, H = pal, RP, HP
    for f in (f0, f1): seat(R, H, f, HIP_P, flex=6)
    arm_poles(R, f0, HIP_P); arm_poles(R, f1, HIP_P)
    # 3a: he holds a straight pin up at chest height and looks at it
    PC = Vector((0.30, -0.36, 1.00))
    ax, g = pinch_at(rig, "R", f0, PC, RIGHT_FD, RIGHT_PN, gap=0.0017)
    d = (Vector((0.15, -0.3, -1.0)) - ax * Vector((0.15, -0.3, -1.0)).dot(ax)).normalized()    # pin points down-forward
    PC = LAST_Q.copy()
    spin.matrix_world = Matrix.Translation(PC) @ frame_from(ax.cross(d), -d).to_4x4()          # local -Z = shaft direction
    bpy.context.view_layer.update(); parent_to_bone(spin, rig, "wrist.R", f0)
    place_hand(rig, "L", f0, Vector((0.46, -0.30, BT + 0.008)), Vector((0, 0, -1)), Vector((-0.2, -1, 0))); apply_pose(rig, "L", "flat_palm", f0)
    place_hand(rig, "L", 1005, Vector((0.46, -0.30, BT + 0.008)), Vector((0, 0, -1)), Vector((-0.2, -1, 0))); apply_pose(rig, "L", "flat_palm", 1005)
    hand_delta(R, "R", f0, 900, (0, 0, 0.0)); hold_fingers(rig, "R", f0, 900)
    hand_delta(R, "R", f0, 950, (0.02, 0.0, -0.02)); hold_fingers(rig, "R", f0, 950)
    # 3b: he pins the cloth; the point slips onto his left fingertip (stops a few mm off the skin), he jerks the hand up
    sc.frame_set(1005); bpy.context.view_layer.update()
    tipL = bone_w(rig, "finger2-3.L", tail=True)
    sc.frame_set(950); bpy.context.view_layer.update()
    tip_now = spin.matrix_world @ Vector((0, 0, -0.034))
    target = tipL + Vector((-0.014, -0.004, 0.012))        # just beside/above the index tip
    hand_delta(R, "R", 950, 990, tuple((tipL + Vector((-0.04, 0, 0.04))) - tip_now)); hold_fingers(rig, "R", 950, 990)
    hand_delta(R, "R", 950, 1008, tuple(target - tip_now)); hold_fingers(rig, "R", 950, 1008)
    hand_delta(R, "R", 950, 1030, tuple(target - tip_now + Vector((-0.03, 0.02, 0.05)))); hold_fingers(rig, "R", 950, 1030)
    hand_delta(R, "R", 950, 1080, tuple(target - tip_now + Vector((-0.04, 0.03, 0.07)))); hold_fingers(rig, "R", 950, 1080)
    # left hand flinches up to the chest and turns the fingertip toward his eyes
    LH = Vector((0.58, -0.36, 1.00))
    place_hand(rig, "L", 1024, LH, Vector((-0.3, 0.6, 0.2)), Vector((-0.3, -0.2, 1))); apply_pose(rig, "L", "point", 1024, amount=0.6)
    place_hand(rig, "L", 1080, LH + Vector((0, -0.02, 0.02)), Vector((-0.3, 0.6, 0.2)), Vector((-0.3, -0.2, 1))); apply_pose(rig, "L", "point", 1080, amount=0.6)
    place_hand(rig, "L", f1, LH + Vector((0, -0.03, 0.03)), Vector((-0.3, 0.6, 0.2)), Vector((-0.3, -0.2, 1))); apply_pose(rig, "L", "point", f1, amount=0.6)
    hand_delta(R, "R", 950, f1, tuple(target - tip_now + Vector((-0.05, 0.04, 0.06)))); hold_fingers(rig, "R", 950, f1)
    look(H, f0, f1, 8, lambda f: (22, 0) if f < 1012 else (8 + 6 * ease((f - 1012) / 30), -10 * ease((f - 1012) / 30)))
    # red bead on the pricked fingertip pad (mild), redness grows a little (infection) in 3c
    sc.frame_set(1081); bpy.context.view_layer.update()
    body, ids = _pad_verts(rig, "L"); co = skin_coords(body)
    tipb = bone_w(rig, "finger2-3.L", tail=True); padv = min((co[i] for i in ids["index"]), key=lambda v: (v - (tipb + (LH - tipb) * 0.0)).length + 0.0 * v.z)
    # pad = index vertex farthest along the palm normal side: pick the vertex closest to the camera side later; use the tip-most vertex
    padv = max((co[i] for i in ids["index"]), key=lambda v: (v - bone_w(rig, "finger2-1.L")).length)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.0016, location=padv); bead = bpy.context.object; bead.name = "BloodBead"; link(bead, cP)
    bead.data.materials.append(mat("Bead", (0.75, 0.02, 0.03), 0.15, coat=0.6))
    for p in bead.data.polygons: p.use_smooth = True
    bpy.ops.mesh.primitive_circle_add(vertices=24, radius=0.0045, fill_type='NGON', location=padv); ring = bpy.context.object; ring.name = "Redness"; link(ring, cP)
    rm = mat("Redness", (0.95, 0.45, 0.45), 0.6); ring.data.materials.append(rm)
    nrm = (padv - tipb).normalized(); ring.rotation_euler = nrm.to_track_quat('Z', 'Y').to_euler(); ring.location = padv - nrm * 0.0008
    for o in (bead, ring): parent_to_bone(o, rig, "finger2-3.L", 1081)
    for f, s_ in ((1, 0.0), (1012, 0.0), (1040, 0.6), (1130, 1.0), (f1, 1.15)):
        bead.scale = (s_,) * 3; bead.keyframe_insert("scale", frame=f)
    for f, s_ in ((1, 0.0), (1100, 0.0), (f1, 1.0)):
        ring.scale = (s_,) * 3; ring.keyframe_insert("scale", frame=f)
    show_only(bead, [(1012, f1)]); show_only(ring, [(1100, f1)]); show_only(spin, [(f0, f1)])
    cam_shot("Cam3a", f0, 950, [(f0, (0.62, -1.05, 1.12), (0.36, -0.20, 1.05)), (950, (0.56, -0.92, 1.10), (0.36, -0.22, 1.03))], lens=45)
    cam_shot("Cam3b", 951, 1080, [(951, (0.95, -0.85, 1.20), (0.40, -0.30, 0.92)), (1080, (0.90, -0.80, 1.18), (0.40, -0.30, 0.96))], lens=40)
    cam_shot("Cam3c", 1081, f1, [(1081, (0.62, -0.95, 1.10), (0.48, -0.25, 1.08)), (f1, (0.61, -0.85, 1.10), (0.48, -0.25, 1.08))], lens=48, fstop=8)
    for c in ("Cam3a", "Cam3b", "Cam3c"): catchlight(rig, bpy.data.objects[c], 0, 0)

# ================================================================== B4 the first safety pin (1201..1590)
def beat_B4():
    f0, f1 = WIN["B4"]
    for f in (f0, f1):
        seat(RH, HH, f, HIP_H, flex=6, yaw=18); seat(RP, HP, f, HIP_P, flex=6, yaw=-22)
    arm_poles(RH, f0, HIP_H, yaw=18); arm_poles(RH, f1, HIP_H, yaw=18); arm_poles(RP, f0, HIP_P, yaw=-22); arm_poles(RP, f1, HIP_P, yaw=-22)
    sb, sa = pin_parts("ShowPin", cP, clasp=True); sb = to_mesh(sb); sa = bpy.data.objects["ShowPin_Arm"]
    if sa.type == 'CURVE': to_mesh(sa)
    PC = Vector((0.0, -0.40, 0.98))
    hold_pin(sb, "L", f0, PC, fd=LEFT_FD, pn=LEFT_PN, point_dir=Vector((0.6, -0.7, 0.3)), out_w=1.0)
    for f, dz in ((1260, 0.03), (1400, 0.05), (1500, 0.06), (f1, 0.06)):
        hand_delta(RH, "L", f0, f, (0.0, 0.0, dz)); hold_fingers(hunt, "L", f0, f)
    rest_hands_on_bench(hunt, f0, (-0.42, None)) if False else None
    place_hand(hunt, "R", f0, Vector((-0.41, -0.03, 0.69)), Vector((0, 0, -1)), Vector((-0.1, -1, -0.25))); apply_pose(hunt, "R", "relaxed", f0)
    place_hand(hunt, "R", f1, Vector((-0.41, -0.03, 0.69)), Vector((0, 0, -1)), Vector((-0.1, -1, -0.25))); apply_pose(hunt, "R", "relaxed", f1)
    for s, x in (("L", 0.50), ("R", 0.28)):
        sx = 1 if s == "L" else -1
        for f in (f0, f1):
            place_hand(pal, s, f, Vector((x, -0.03, 0.69)), Vector((0, 0, -1)), Vector((-0.1 * sx, -1, -0.25))); apply_pose(pal, s, "relaxed", f)
    # Hunt looks between the pin and his friend; Pal leans in, studies it, looks up and nods
    look(HH, f0, f1, 6, lambda f: (16, 6) if f < 1330 else (6, 14) if f < 1470 else (12, 8))
    def palhead(f):
        if f < 1300: return (18, -10)
        if f < 1420: return (24, -14)
        if f < 1460: return (4, -14)
        n = 8 * math.sin((f - 1460) / 22 * math.pi) if f < 1520 else 0
        return (8 + n, -12)
    look(HP, f0, f1, 10, palhead, step=10)
    show_only(sb, [(f0, f1)])
    cam_shot("Cam4a", f0, 1400, [(f0, (0.10, -1.55, 1.12), (0.04, -0.15, 1.04)), (1400, (0.06, -1.35, 1.10), (0.04, -0.15, 1.04))], lens=40)
    cam_shot("Cam4b", 1401, f1, [(1401, (0.08, -0.98, 1.26), (0.32, -0.04, 1.24)), (f1, (0.10, -0.90, 1.26), (0.33, -0.04, 1.25))], lens=55)
    for c in ("Cam4a", "Cam4b"): catchlight(pal, bpy.data.objects[c], 0, 0)

# ================================================================== B5 the $15 debt (1591..1860)
def beat_B5():
    f0, f1 = WIN["B5"]
    for f in (f0, f1): seat(RH, HH, f, HIP_H, flex=6)
    arm_poles(RH, f0, HIP_H, out=0.12, back=-0.35, z=0.45); arm_poles(RH, f1, HIP_H, out=0.12, back=-0.35, z=0.45)   # elbows in
    note = bpy.data.objects["DebtNote"]; note.location = (-0.30, -0.42, BT + 0.0012); note.rotation_euler = (0, 0, R_(8))
    for i, (dx, dy) in enumerate(((0.10, -0.03), (0.125, -0.012), (0.115, 0.012))):
        c_ = bpy.data.objects["Coin%d" % i]; c_.location = (-0.30 + dx, -0.42 + dy, BT + 0.001 + 0.0021 * i)
    # B5 only: the bench (and its dressing) sits 20 cm further away so his forearms hang in front of its edge
    DY = -0.20
    grp = ["Workbench", "Candle", "Spool"] + [o.name for o in bpy.data.objects if o.name.startswith("SpoolFlange")]
    for nm in grp:
        o = bpy.data.objects[nm]; y0 = o.location.y
        for f, y in ((f0 - 1, y0), (f0, y0 + DY), (f1, y0 + DY), (f1 + 1, y0)):
            o.location.y = y; o.keyframe_insert("location", index=1, frame=f)
        for fc in (o.animation_data.action.fcurves if hasattr(o.animation_data.action, "fcurves") and len(o.animation_data.action.fcurves) else _fcurves(o.animation_data.action)):
            for k in fc.keyframe_points: k.interpolation = 'CONSTANT'
        o.location.y = y0
    note.location.y += DY
    for i in range(3): bpy.data.objects["Coin%d" % i].location.y += DY
    # director v002b: leaning forward, forearms resting on his thighs, hands near the knees, elbows in
    for f in (f0, 1700, f1):
        for s_, sx in (("R", -1), ("L", 1)):
            place_hand(hunt, s_, f, Vector((-0.30 + sx * 0.14, -0.27, 0.66)), Vector((0, 0, -1)), Vector((-sx * 0.15, -1, -0.45)))
            apply_pose(hunt, s_, "relaxed", f)
    # slumped, slow head shake, a breath; face kept toward the low camera
    def hd(f):
        sh = 9 * math.sin((f - f0) / 45 * math.pi) if 1630 < f < 1720 else 0
        return (12, sh)
    look(HH, f0, f1, 22, hd, step=10, period=150, amp=2.0)
    for o in [note] + [bpy.data.objects["Coin%d" % i] for i in range(3)]: show_only(o, [(f0, f1)])
    cam_shot("Cam5a", f0, 1740, [(f0, (0.05, -1.50, 0.98), (-0.30, -0.20, 1.02)), (1740, (-0.05, -1.22, 0.98), (-0.30, -0.20, 1.02))], lens=40)
    cam_shot("Cam5b", 1741, f1, [(1741, (-0.10, -1.00, 1.08), (-0.30, -0.60, 0.80)), (f1, (-0.16, -0.90, 1.02), (-0.30, -0.61, 0.80))], lens=45, fstop=9)
    catchlight(hunt, bpy.data.objects["Cam5a"], 0, 0)

# ================================================================== B6 sells the patent for $400 (1861..2220)
def beat_B6():
    f0, f1 = WIN["B6"]
    for f in (f0, f1):
        seat(RH, HH, f, HIP_H, flex=6); seat(RB, HB, f, HIP_B, flex=6, yaw=180)
    arm_poles(RH, f0, HIP_H); arm_poles(RH, f1, HIP_H); arm_poles(RB, f0, HIP_B, yaw=180); arm_poles(RB, f1, HIP_B, yaw=180)
    pat = bpy.data.objects["Patent"]; stack = bpy.data.objects["MoneyStack"]
    p0 = Vector((-0.36, -0.30, BT + 0.0012)); p1 = Vector((-0.36, -0.56, BT + 0.0012))
    m0 = Vector((0.02, -0.66, BT + 0.0005)); m1 = Vector((-0.12, -0.40, BT + 0.0005))
    pat.rotation_euler = (0, 0, R_(4)); stack.rotation_euler = (0, 0, R_(-6))
    def slide(obj, a, b, fa, fb):
        for f, p in ((f0, a), (fa, a), (fb, b), (f1, b)):
            obj.location = p; obj.keyframe_insert("location", frame=f)
    slide(pat, p1, p1, 1900, 1975); slide(stack, m0, m1, 1935, 2005)   # patent already lies in front of the buyer
    # Hunt's hands stay in his lap (no push: re-staged, the push hand crossed the bench)
    place_hand(hunt, "R", f0, Vector((-0.41, -0.03, 0.69)), Vector((0, 0, -1)), Vector((-0.1, -1, -0.25))); apply_pose(hunt, "R", "relaxed", f0)
    place_hand(hunt, "R", 2000, Vector((-0.41, -0.03, 0.69)), Vector((0, 0, -1)), Vector((-0.1, -1, -0.25))); apply_pose(hunt, "R", "relaxed", 2000)
    place_hand(hunt, "R", f1, Vector((-0.41, -0.03, 0.69)), Vector((0, 0, -1)), Vector((-0.1, -1, -0.25))); apply_pose(hunt, "R", "relaxed", f1)
    place_hand(hunt, "L", f0, Vector((-0.19, -0.03, 0.69)), Vector((0, 0, -1)), Vector((0.1, -1, -0.25))); apply_pose(hunt, "L", "relaxed", f0)
    place_hand(hunt, "L", f1, Vector((-0.19, -0.03, 0.69)), Vector((0, 0, -1)), Vector((0.1, -1, -0.25))); apply_pose(hunt, "L", "relaxed", f1)
    # Buyer (faces +Y; his right hand is on +X) slides the money stack over, then takes the patent toward himself
    for f, p in ((f0, m0), (1935, m0), (2005, m1)):
        place_hand(buyer, "R", f, p + Vector((0, 0, 0.016)), Vector((0, 0, -1)), Vector((-0.15, 1, 0))); apply_pose(buyer, "R", "flat_palm", f)
    place_hand(buyer, "R", 2035, Vector((0.05, -1.04, 0.69)), Vector((0, 0, -1)), Vector((-0.1, 1, -0.25))); apply_pose(buyer, "R", "relaxed", 2035)
    place_hand(buyer, "R", f1, Vector((0.05, -1.04, 0.69)), Vector((0, 0, -1)), Vector((-0.1, 1, -0.25))); apply_pose(buyer, "R", "relaxed", f1)
    place_hand(buyer, "L", f0, Vector((-0.15, -1.04, 0.69)), Vector((0, 0, -1)), Vector((0.1, 1, -0.25))); apply_pose(buyer, "L", "relaxed", f0)
    place_hand(buyer, "L", f1, Vector((-0.15, -1.04, 0.69)), Vector((0, 0, -1)), Vector((0.1, 1, -0.25))); apply_pose(buyer, "L", "relaxed", f1)
    look(HH, f0, f1, 8, lambda f: (20, 0) if f < 2060 else (14 - 10 * ease((f - 2060) / 40), 0))
    look(HB, f0, f1, 6, lambda f: (18, 0) if f < 2040 else (4, 0))
    for o in [pat, stack] + list(stack.children): show_only(o, [(f0, f1)])
    cam_shot("Cam6a", f0, 2040, [(f0, (-1.95, -0.62, 1.22), (-0.15, -0.55, 1.02)), (2040, (-1.80, -0.62, 1.20), (-0.15, -0.55, 1.02))], lens=24)
    cam_shot("Cam6b", 2041, f1, [(2041, (-0.95, -0.95, 1.12), (-0.30, -0.25, 1.00)), (f1, (-0.88, -0.86, 1.12), (-0.30, -0.22, 1.02))], lens=40)
    for c in ("Cam6a", "Cam6b"): catchlight(hunt, bpy.data.objects[c], 0, 0)

# ================================================================== B7 made millions (2221..2460)
def beat_B7():
    f0, f1 = WIN["B7"]; X = 40.0
    for o in bpy.data.objects:      # logo only on the two front-centre boxes (director: no logos cut by the frame edge)
        if o.name.startswith("PinBox") and o.name.endswith("_Logo") and o.name not in ("PinBox01_Logo", "PinBox02_Logo"):
            o.hide_render = True; o.hide_viewport = True
    cam_shot("Cam7a", f0, 2340, [(f0, (X - 0.07, -1.85, 0.62), (X - 0.07, 0.2, 0.18)), (2340, (X - 0.07, -1.60, 0.58), (X - 0.07, 0.2, 0.18))], lens=26)
    cam_shot("Cam7b", 2341, f1, [(2341, (X - 0.07, -1.45, 0.95), (X - 0.07, 0.4, 0.2)), (f1, (X - 0.07, -1.15, 2.1), (X - 0.07, 0.6, 0.15))], lens=26)

# ================================================================== B8 died poor but respected (2461..2730)
def beat_B8():
    f0, f1 = WIN["B8"]; X = 80.0; sz = sc.get("park_seat_z", 0.65)
    # three leaves drift down onto the bench area (keyed, no particles)
    for i in range(3):
        bpy.ops.mesh.primitive_circle_add(vertices=8, radius=0.035, fill_type='NGON', location=(0, 0, 0)); l_ = bpy.context.object
        l_.name = "FallLeaf%d" % i; l_.scale.y = 0.55; link(l_, bpy.data.collections["SetPark"]); l_.data.materials.append(bpy.data.materials["Leaf%d" % i])
        x0 = X - 0.5 + 0.4 * i
        for f in range(f0, f1 + 1, 15):
            u = (f - f0) / (f1 - f0)
            l_.location = (x0 + 0.08 * math.sin(6 * u + i), -0.25 + 0.1 * i, max(sz + 0.02 if abs(x0 - X) < 0.5 else 0.01, 1.9 - 1.6 * u - 0.2 * i))
            l_.rotation_euler = (0.6 * math.sin(5 * u + i), 0.5 * math.cos(4 * u), 3 * u + i)
            l_.keyframe_insert("location", frame=f); l_.keyframe_insert("rotation_euler", frame=f)
    cam_shot("Cam8a", f0, 2600, [(f0, (X - 0.40, -1.55, 1.15), (X - 0.08, 0.05, 0.55)), (2600, (X - 0.33, -1.30, 1.08), (X - 0.08, 0.05, 0.56))], lens=30)
    cam_shot("Cam8b", 2601, f1, [(2601, (X - 0.45, -0.60, sz + 0.42), (X - 0.08, -0.04, sz)), (f1, (X - 0.30, -0.66, sz + 0.40), (X - 0.06, -0.04, sz))], lens=40, fstop=9)

# B3-only dressing (cloth + cushion) hidden elsewhere; pliers removed (read as food)
for nm in ("Cloth0", "Cloth1", "PinCushion") + tuple("CushionPin%d" % i for i in range(7)):
    o = bpy.data.objects.get(nm)
    if o: show_only(o, [WIN["B3"]])
pl = bpy.data.objects.get("Pliers")
if pl:
    for ch in list(pl.children_recursive): bpy.data.objects.remove(ch)
    bpy.data.objects.remove(pl)
for nm, loc in (("Candle", (0.80, -0.20)),):
    o = bpy.data.objects[nm]; o.location.x, o.location.y = loc
# park pin: lying flat on the newspaper picture
pp = bpy.data.objects["ParkPin_Body"]; szp = sc.get("park_seat_z", 0.65)
pp.location = (80.0 - 0.16, -0.06, szp + 0.022); pp.rotation_euler = (R_(90), 0, R_(20))
# park: the low-poly blob trees are removed (director note); lawn, shrubs and sky remain
for o in list(bpy.data.collections["SetPark"].objects):
    if o.type == 'MESH' and o.data.materials and o.data.materials[0] and o.data.materials[0].name in ("Bark", "Leaves"):
        bpy.data.objects.remove(o)
path_m = bpy.data.materials.get("Path")
if path_m:   # gravel path: warm brown, mottled
    _nt = path_m.node_tree; _P = _nt.nodes["Principled BSDF"]
    _nz = _nt.nodes.new("ShaderNodeTexNoise"); _nz.inputs["Scale"].default_value = 60.0; _nz.inputs["Detail"].default_value = 8.0
    _cr = _nt.nodes.new("ShaderNodeValToRGB"); _cr.color_ramp.elements[0].color = (0.30, 0.24, 0.17, 1); _cr.color_ramp.elements[1].color = (0.52, 0.44, 0.33, 1)
    _nt.links.new(_nz.outputs["Fac"], _cr.inputs[0]); _nt.links.new(_cr.outputs[0], _P.inputs["Base Color"])

for b, fn in (("B3", beat_B3), ("B4", beat_B4), ("B5", beat_B5), ("B6", beat_B6), ("B7", beat_B7), ("B8", beat_B8)):
    if want(b): fn()
