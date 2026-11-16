# ================================================================== helpers for B2..B6
def lin(obj_or_id):
    ad = obj_or_id.animation_data
    if ad and ad.action:
        for fc in _fcurves(ad.action):
            for k in fc.keyframe_points: k.interpolation = 'LINEAR'

def hand_about(R, s, f_src, f_dst, center, rot):
    sc.frame_set(f_src); M = R.PB["IK_hand." + s].matrix.copy(); c = Vector(center)
    R.key_world("IK_hand." + s, f_dst, Matrix.Translation(c) @ rot.to_4x4() @ Matrix.Translation(-c) @ M)

def coffee_level(cup, f, h):
    """key the cup's coffee disc at fill height h (fraction of CUP_H)"""
    cf = bpy.data.objects[cup.name + "_Coffee"]; r_ref = CUP_R0 + (CUP_R1 - CUP_R0) * 0.88; r = CUP_R0 + (CUP_R1 - CUP_R0) * h
    cf.location.z = (h - 0.88) * CUP_H; cf.scale = (r / r_ref, r / r_ref, 1)
    cf.keyframe_insert("location", frame=f); cf.keyframe_insert("scale", frame=f)

def hot_coffee_mat(name):
    m = mat(name, (0.11, 0.05, 0.02), 0.06).copy(); m.name = name; nt = m.node_tree; Pn = nt.nodes["Principled BSDF"]
    nz = nt.nodes.new("ShaderNodeTexNoise"); nz.noise_dimensions = '4D'; nz.inputs["Scale"].default_value = 60.0; nz.inputs["Detail"].default_value = 2.0
    wv = nt.nodes.new("ShaderNodeValue"); wv.name = "RippleW"; nt.links.new(wv.outputs[0], nz.inputs["W"])
    bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.35; bp.inputs["Distance"].default_value = 0.002
    nt.links.new(nz.outputs["Fac"], bp.inputs["Height"]); nt.links.new(bp.outputs["Normal"], Pn.inputs["Normal"])
    return m

def stand(H, R, name, f0, f1, pos, yaw, step=20, head=None, flex=0.0, sway=0.6):
    """standing idle at pos: planted feet, breathing, weight shift, optional head(f) -> (x, z)"""
    for s in "LR":
        for f in (f0, f1):
            H.key_foot(s, f, H.foot_xy(s, pos, yaw), yaw)
    for f in range(f0, f1 + 1, step):
        ph = math.sin(2 * math.pi * (f - f0) / 240)
        p = pos + Vector((0, 0, H.root_head.z - 0.01)) + Matrix.Rotation(R_(yaw), 3, 'Z') @ Vector((0.012 * ph * sway, 0, 0))
        H.key_root(f, p, yaw=yaw, flex=flex, side=1.2 * ph * sway)
        hx, hz = head(f) if head else (0.0, 0.0)
        H.key_spine(f, flex=1.2 * math.sin(2 * math.pi * (f - f0) / 190), head=(hx, hz))

def arms_relaxed(rig, R, H, f, pos, yaw, out=0.0):
    """hands hang beside the thighs with a slight elbow bend"""
    Rz = Matrix.Rotation(R_(yaw), 3, 'Z')
    for s in "LR":
        sx = 1 if s == "L" else -1
        W_ = pos + Rz @ Vector((sx * (0.24 + out), 0.02, 0.86))
        place_hand(rig, s, f, W_, Rz @ Vector((-sx, 0.15, 0)), Rz @ Vector((0.0, -0.12, -1)))
        pole(R, s, f, pos + Rz @ Vector((sx * 0.35, 0.45, 1.05)))
        apply_pose(rig, s, "relaxed", f)

def hold_cup(rig, R, s, f, cup, yaw_face):
    """wrap grip on the cup's side, Child Of from f"""
    sc.frame_set(f); bpy.context.view_layer.update()
    c = cup.matrix_world @ Vector((0, 0, CUP_H * 0.42))
    sx = 1 if s == "L" else -1
    side = Matrix.Rotation(R_(yaw_face), 3, 'Z') @ Vector((sx * 1.0, 0.35, 0)); side.normalize()
    rr = CUP_R0 + (CUP_R1 - CUP_R0) * 0.5
    fd = Matrix.Rotation(R_(yaw_face), 3, 'Z') @ Vector((0, -1, 0))
    PALM = [n % s for n in ("wrist.%s", "metacarpal1.%s", "metacarpal2.%s", "metacarpal3.%s", "metacarpal4.%s",
                            "finger2-1.%s", "finger3-1.%s", "finger4-1.%s", "finger5-1.%s", "finger1-1.%s")]
    for off in (0.0, 0.006, 0.012, 0.018, 0.024, 0.030, 0.036, 0.042, 0.048, 0.054):
        rep = grip_object(rig, s, f, bpy.data.objects[cup.name + "_Band"], c + side * (rr + off + 0.001), -side, finger_dir=fd, finger_radius=0.013)
        sc.frame_set(f); bpy.context.view_layer.update(); M = rig.matrix_world
        dmin = min(_dist_to(cup, M @ rig.pose.bones[b].head.lerp(rig.pose.bones[b].tail, u)) for b in PALM for u in (0.0, 0.5, 1.0))
        if dmin > 0.024: break
    rep["palm_clear_m"] = round(dmin, 4); rep["offset_m"] = off
    return rep

# ================================================================== B2 the coffee (421..1200)
def beat_B2():
    cF = bpy.data.collections["SetCafe"]
    cup = bpy.data.objects["PourCup"]; strm = bpy.data.objects["PourStream"]
    spout = Vector((cup.location.x, cup.location.y, 1.12)); strm.location = spout
    stl = bpy.data.objects["PourStreamMesh"]
    for f, lvl in ((421, 0.15), (450, 0.15), (600, 0.80), (1200, 0.80)): coffee_level(cup, f, lvl)
    def top(lvl): return 0.941 + lvl * CUP_H
    for f, L in ((421, 0.002), (440, 0.002), (452, spout.z - top(0.15)), (600, spout.z - top(0.80)), (612, 0.002)):
        strm.scale = (1, 1, L); strm.keyframe_insert("scale", frame=f)
    vis(strm, 421, False); vis(strm, 440, True); vis(strm, 613, False)
    st = bpy.data.objects["PourSteam"]; st.hide_render = False; key_steam(st, 421, 640)
    am = st.active_material.node_tree.nodes["SteamAmount"].outputs[0]
    for f, v in ((421, 0.15), (470, 0.5), (640, 0.7)): am.default_value = v; am.keyframe_insert("default_value", frame=f)
    cy = cup.location.y
    c2a = cam_shot("Cam2a", 421, 640, [(421, (cup.location.x + 0.05, cy - 0.42, 1.10), (cup.location.x, cy, 1.05)),
                                      (640, (cup.location.x + 0.02, cy - 0.33, 1.10), (cup.location.x, cy, 1.06))], lens=40)
    # served cup on the front counter (logo to the customer side), steam; crane up over the rim, then the macro
    CY = 0.12
    cc = paper_cup("CounterCup", cF, (40.30, CY, 1.04), with_logo=True)
    cfo = bpy.data.objects["CounterCup_Coffee"]; hm = hot_coffee_mat("CoffeeHot"); cfo.data.materials[0] = hm
    rw = hm.node_tree.nodes["RippleW"].outputs[0]
    for f in (641, 1200): rw.default_value = (f - 641) / 60 * 0.6; rw.keyframe_insert("default_value", frame=f)
    lin(hm.node_tree)
    s2 = steam("CounterSteam", cF, (40.30, CY, 1.04 + CUP_H * 0.86), h=0.27, r=0.045, dens=0.75); key_steam(s2, 641, 1200)
    surf = 1.04 + CUP_H * 0.88
    bub = []
    for i in range(7):
        a = i * 2.4; r = 0.012 + 0.022 * ((i * 37) % 10) / 10
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.0028 + 0.0012 * (i % 3), location=(40.30 + r * math.cos(a), CY + r * math.sin(a), surf))
        b = bpy.context.object; b.name = "Bubble%d" % i; link(b, cF); b.data.materials.append(mat("BubbleM", (0.25, 0.14, 0.07), 0.05))
        b.scale = (1, 1, 0.5)
        for k in range(6):   # pop cycles: grow then vanish, staggered
            f0 = 901 + i * 13 + k * 50
            for f, sv in ((f0, 0.05), (f0 + 20, 1.0), (f0 + 24, 0.05)):
                b.scale = (sv, sv, 0.5 * sv); b.keyframe_insert("scale", frame=f)
        bub.append(b)
    cam_shot("Cam2b", 641, 900, [(641, (40.30, CY - 0.63, 1.13), (40.30, CY, 1.10)), (770, (40.30, CY - 0.38, 1.30), (40.30, CY, 1.12)),
                                 (900, (40.30, CY - 0.17, 1.40), (40.30, CY, 1.13))], lens=50)
    c = bpy.data.objects.new("Cam2c", bpy.data.cameras.new("Cam2c")); sc.collection.objects.link(c)
    c.data.lens = 70; c.data.dof.use_dof = True; c.data.dof.aperture_fstop = 11.0; c.data.clip_start = 0.01
    for f, z, rz in ((901, 1.47, 0.0), (1200, 1.425, 0.35)):
        c.location = (40.30, CY, z); c.rotation_euler = (0, 0, rz); c.keyframe_insert("location", frame=f); c.keyframe_insert("rotation_euler", frame=f)
        c.data.dof.focus_distance = z - surf; c.data.dof.keyframe_insert("focus_distance", frame=f)
    m = sc.timeline_markers.new("Cam2c", frame=901); m.camera = c; CAMS.append(("Cam2c", 901, 1200, c))

# ================================================================== B3 hospital (1201..1700)
def beat_B3():
    cH = bpy.data.collections["SetHosp"]; X = 80.0
    rig, R, H = setup("GranH", "GranB")
    tint(rig, "short02", (0.62, 0.61, 0.60), "MIX", 0.6)
    for ch in rig.children:
        if "short02" in ch.name:
            d_ = ch.modifiers.new("Puff", 'DISPLACE'); d_.strength = 0.004; d_.mid_level = 0.0   # close scalp gaps in the re-fitted cap
    tint(rig, "elegantsuit", (0.78, 0.88, 0.95), "MIX", 0.85)   # pale blue gown
    for ch in rig.children:
        if "shoes" in ch.name: bpy.data.objects.remove(ch)   # no shoes in bed
    bx = 79.70; mtop = 0.66
    # pillow wedge (raised backrest) and pillow at the +Y end
    m_sheet = mat("Sheet", (0.95, 0.96, 0.97), 0.6)
    box("Mattress", cH, (bx, 0.30, mtop - 0.05), (0.84, 2.0, 0.10), m_sheet, 0.03)
    FLOORS[:] = [bpy.data.objects["Mattress"]]
    hip = Vector((bx, 0.55, mtop + 0.185))
    for f in range(1201, 1701, 20):
        ph = math.sin(2 * math.pi * (f - 1201) / 210)
        H.key_root(f, hip, yaw=0.0, flex=-58 + 0.8 * ph)
        tz = -18 if f < 1480 else -18 + 30 * min(1, (f - 1480) / 60)      # turns her head toward the staff, then back
        H.key_spine(f, flex=8 + 1.2 * ph, head=(18 + 0.6 * ph, tz))
    for s in "LR":
        sx = 1 if s == "L" else -1
        for f in (1201, 1700):
            foot_at(R, H, s, f, Vector((bx + sx * 0.12, hip.y - 0.86, mtop + 0.10)), pitch=-78)
            knee_pole(R, s, f, Vector((bx + sx * 0.15, hip.y - 0.45, mtop + 0.8)))
        # hands rest on the sheet beside the hips
        for f in (1201, 1700):
            sc.frame_set(f); bpy.context.view_layer.update()
            th = rig.matrix_world @ rig.pose.bones["upperleg02." + s].head
            place_hand(rig, s, f, th + Vector((sx * 0.01, 0.02, 0.09)), Vector((0, 0, -1)), Vector((-sx * 0.25, -1, 0)))
            apply_pose(rig, s, "relaxed", f); pole(R, s, f, Vector((bx + sx * 0.6, hip.y + 0.4, mtop + 0.5)))
    # clean white bandages around both lower thighs + knees (no wounds, no red)
    sc.frame_set(1201); bpy.context.view_layer.update()
    # backrest wedge + pillow fitted behind her spine and head (top face 13 cm / 11 cm behind the bone line)
    p0 = rig.matrix_world @ rig.pose.bones["spine05"].head; p1 = rig.matrix_world @ rig.pose.bones["neck01"].head
    hd_ = rig.matrix_world @ rig.pose.bones["head"].head
    dv = (p1 - p0).normalized(); nv = Vector((0, -dv.z, dv.y)).normalized()      # body front normal in the YZ plane
    if nv.z < 0: nv = -nv
    ang = math.atan2(-dv.y, dv.z)
    wc = (p0 + p1) / 2 - nv * (0.14 + 0.05)
    box("BedWedge", cH, tuple(wc), (0.80, 0.10, (p1 - p0).length + 0.45), m_sheet, 0.03, rot=(ang, 0, 0))
    box("Pillow", cH, tuple(hd_ - nv * (0.16 + 0.07) + dv * 0.05), (0.55, 0.14, 0.32), m_sheet, 0.06, rot=(ang, 0, 0))
    m_band = bpy.data.materials.new("Bandage"); m_band.use_nodes = True; nt = m_band.node_tree; Pn = nt.nodes["Principled BSDF"]
    Pn.inputs["Base Color"].default_value = (0.97, 0.96, 0.93, 1); Pn.inputs["Roughness"].default_value = 0.85
    wv = nt.nodes.new("ShaderNodeTexWave"); wv.inputs["Scale"].default_value = 18; wv.wave_type = 'BANDS'; wv.bands_direction = 'Z'
    tc = nt.nodes.new("ShaderNodeTexCoord"); nt.links.new(tc.outputs["Object"], wv.inputs["Vector"])
    bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.3; nt.links.new(wv.outputs["Fac"], bp.inputs["Height"]); nt.links.new(bp.outputs["Normal"], Pn.inputs["Normal"])
    body = next(o for o in rig.children if o.name.endswith(".body"))
    for s in "LR":
        for bn, u0, u1, r0, r1 in (("upperleg02." + s, 0.15, 1.0, 0.072, 0.060), ("lowerleg01." + s, 0.0, 0.45, 0.058, 0.050)):
            pb = rig.pose.bones[bn]; h = rig.matrix_world @ pb.head; t = rig.matrix_world @ pb.tail
            a_ = h.lerp(t, u0); b_ = h.lerp(t, u1); L = (b_ - a_).length
            o = lathe("Band_" + bn, cH, [(r0, 0), (r0 + 0.004, L * 0.5), (r1, L)], m_band, (0, 0, 0), segs=32, cap_bottom=False)
            o.location = a_; o.rotation_euler = (b_ - a_).to_track_quat('Z', 'Y').to_euler()
            sw_ = o.modifiers.new("Fit", 'SHRINKWRAP'); sw_.target = body; sw_.wrap_method = 'NEAREST_SURFACEPOINT'; sw_.offset = 0.006
            sw_.wrap_mode = 'OUTSIDE_SURFACE'
            c = o.constraints.new('CHILD_OF'); c.target = rig; c.subtarget = bn
            c.inverse_matrix = (rig.matrix_world @ pb.matrix).inverted()
    # blanket over the shins and feet
    bl = box("Blanket", cH, (bx, hip.y - 0.95, mtop + 0.18), (0.86, 0.66, 0.36), mat("Blanket", (0.45, 0.62, 0.85), 0.8), 0.05)
    bm_ = bmesh.new(); bm_.from_mesh(bl.data)
    kill = [fc for fc in bm_.faces if fc.normal.z < -0.9 or fc.normal.y > 0.9]
    bmesh.ops.delete(bm_, geom=kill, context='FACES'); bm_.to_mesh(bl.data); bm_.free()
    bl.modifiers.new("Solid", 'SOLIDIFY').thickness = 0.012
    bl.modifiers.new("Sub", 'SUBSURF').levels = 2
    # staff at the foot of the bed, facing the patient (+Y)
    staff = {}
    for cid, pos in (("Doctor", Vector((bx - 0.28, -1.45, 0))), ("Nurse", Vector((bx + 0.42, -1.40, 0)))):
        r2, R2, H2 = setup(cid); staff[cid] = (r2, R2, H2)
        FLOORS[:] = [bpy.data.objects["HospFloor"]]
        hd = (lambda f: (12 if f < 1450 else 4, 0)) if cid == "Doctor" else (lambda f: (6 + (5 * math.sin((f - 1400) / 9) if 1440 < f < 1500 else 0), 0))
        stand(H2, R2, cid, 1201, 1700, pos, 180.0, head=hd)
        o_ = -0.07 if cid == "Nurse" else 0.0
        arms_relaxed(r2, R2, H2, 1201, pos, 180.0, out=o_); arms_relaxed(r2, R2, H2, 1700, pos, 180.0, out=o_)
    tint(staff["Doctor"][0], "casualsuit01", (0.45, 0.62, 0.95))
    tint(staff["Nurse"][0], "sportsuit01", (0.45, 0.85, 0.70))
    lookat = Vector((bx, 0.75, 1.05))
    cam_shot("Cam3a", 1201, 1360, [(1201, (78.55, -0.55, 1.30), (79.70, 0.55, 0.88)), (1360, (78.65, -0.30, 1.26), (79.70, 0.60, 0.90))], lens=28)
    sc.frame_set(1460); bpy.context.view_layer.update()
    dh = staff["Doctor"][0].matrix_world @ staff["Doctor"][0].pose.bones["head"].head; nh = staff["Nurse"][0].matrix_world @ staff["Nurse"][0].pose.bones["head"].head
    mid = (dh + nh) / 2 - Vector((0, 0, 0.22))
    cam_shot("Cam3b", 1361, 1560, [(1361, (78.80, 0.05, 1.60), tuple(mid)), (1560, (78.83, -0.05, 1.59), tuple(mid))], lens=26)
    sc.frame_set(1630); bpy.context.view_layer.update()
    hf = rig.matrix_world @ rig.pose.bones["head"].tail
    c3 = cam_shot("Cam3c", 1561, 1700, [(1561, tuple(hf + Vector((-0.30, -0.62, 0.20))), tuple(hf)), (1700, tuple(hf + Vector((-0.27, -0.55, 0.18))), tuple(hf))], lens=45)
    catchlight(rig, c3, 1561, 1700)

# ================================================================== B4 complaints (1701..2280)
def beat_B4():
    cF = bpy.data.collections["SetCafe"]; FLOORS[:] = [bpy.data.objects["CafeFloor"]]
    line = [("C2", 38.95, -1.30, 15), ("C1", 39.50, -1.10, 8), ("C4", 40.05, -1.15, 0), ("Hero", 40.62, -1.12, -8), ("C5", 41.18, -1.32, -15)]
    cols = {"Hero": ("casualsuit03", (0.30, 0.55, 0.85)), "C1": ("casualsuit02", (0.95, 0.45, 0.35)), "C4": ("casualsuit04", (0.20, 0.21, 0.24))}
    cups = {}
    for cid, x, y, yaw in line:
        rig, R, H = setup(cid); pos = Vector((x, y, 0)); yaw_ = 180.0 + 180.0 + yaw   # face -Y (camera), small turn
        yaw_ = yaw
        if cid in cols: tint(rig, cols[cid][0], cols[cid][1])
        hd = {"C4": lambda f: (18 if f < 1830 else 2, 0), "C1": lambda f: (22, 0), "Hero": lambda f: (8, 10 * math.sin((f - 2000) / 14) if 1990 < f < 2090 else 0),
              "C2": lambda f: (4, -20 if f > 2050 else 0), "C5": lambda f: (6, 18 if f > 2100 else 0), "C3": lambda f: (2, 0)}[cid]
        stand(H, R, cid, 1701, 2280, pos, yaw_, head=hd, flex=(6 if cid == "C1" else 0))
        arms_relaxed(rig, R, H, 1701, pos, yaw_); arms_relaxed(rig, R, H, 2280, pos, yaw_)
        if cid in ("C4", "C2"):
            Rz = Matrix.Rotation(R_(yaw_), 3, 'Z')
            sc.frame_set(1701); bpy.context.view_layer.update()
            cp = pos + Rz @ Vector((-0.04, -0.30, 1.12 if cid != "C2" else 1.06))
            cup = paper_cup("Cup_" + cid, cF, tuple(cp), with_logo=(cid == "C4")); cup.rotation_euler.z = R_(yaw_)
            st = steam("Steam_" + cid, cF, (cp.x, cp.y, cp.z + CUP_H * 0.86), h=0.25, r=0.04, dens=0.55); st.parent = cup
            st.matrix_parent_inverse = cup.matrix_world.inverted(); key_steam(st, 1701, 2280)
            # right hand holds the cup in front of the chest; the left hand stays relaxed
            rep = hold_cup(rig, R, "R", 1701, cup, yaw_)
            pole(R, "R", 1701, pos + Rz @ Vector((-0.45, 0.3, 0.95)))
            child_of_hand(cup, rig, "R", 1701)
            for f in (1760, 1900, 2000, 2150, 2280): hold_fingers(rig, "R", 1701, f)
            lift = {"C4": [(1830, (0, -0.06, 0.06)), (1960, (0, -0.08, 0.08)), (2280, (0, -0.02, 0.02))],
                    "C1": [(1900, (0, 0, 0.05)), (2000, (0, 0, 0.08)), (2120, (0, 0, 0.02)), (2280, (0, 0, 0.03))],
                    "Hero": [(2000, (0, -0.03, 0.07)), (2100, (0, -0.02, 0.03)), (2280, (0, 0, 0.0))],
                    "C2": [(2100, (0, 0, 0.03)), (2280, (0, 0, 0.0))]}[cid]
            for f, d in lift: hand_delta(R, "R", 1701, f, Rz @ Vector(d))
            print("B4 cup grip", cid, rep)
            vis(cup, 1, False); vis(cup, 1701, True); vis(cup, 2281, False)
            cups[cid] = cup
    cam_shot("Cam4a", 1701, 1960, [(1701, (40.02, -2.75, 1.52), (40.05, -1.15, 1.45)), (1960, (39.98, -2.50, 1.50), (40.05, -1.15, 1.44))], lens=42)
    c4b = cam_shot("Cam4b", 1961, 2280, [(1961, (38.95, -3.55, 1.50), (39.75, -1.25, 1.30)), (2280, (41.05, -3.55, 1.50), (40.45, -1.25, 1.30))], lens=30)

# ================================================================== B5 backlash (2281..2560)
def beat_B5():
    cB = bpy.data.collections["SetBoard"]; FLOORS[:] = [bpy.data.objects["BoardFloor"]]
    tbl = [o for o in bpy.data.objects if o.parent and o.parent.name == "BoardTable" or (o.parent and o.parent.parent and o.parent.parent.name == "BoardTable")]
    ttop = 0.762
    lead = "ExecA" if bpy.data.filepath and False else None
    lead = "ExecC"
    rigA, RA, HA = setup(lead, "BossA"); FLOORS[:] = [bpy.data.objects["BoardFloor"]]
    tint(rigA, "suit", (0.62, 0.64, 0.68), "MIX", 0.7)
    ch0 = bpy.data.objects["BoardChair0"]; cmn, cmx = bounds([ch0]); ccx, ccy = (cmn.x + cmx.x) / 2, (cmn.y + cmx.y) / 2
    dg = bpy.context.evaluated_depsgraph_get(); hit = sc.ray_cast(dg, Vector((ccx, ccy + 0.08, 1.2)), Vector((0, 0, -1)))
    seat = hit[1].z if hit[0] and 0.3 < hit[1].z < 0.7 else 0.47
    print("B5 seat z", round(seat, 3), "chair", round(ccx, 2), round(ccy, 2))
    hipA = Vector((120.0, ccy + 0.10, seat + 0.13))
    # seated at the head of the table facing +Y: lean in with palms flat, then sit back and exhale
    for f, fl in ((2281, 7), (2330, 16), (2400, 16), (2440, 6), (2560, 6)): HA.key_root(f, hipA, yaw=180.0, flex=fl)
    for f in range(2281, 2561, 20): HA.key_spine(f, flex=4 + 1.2 * math.sin((f - 2281) / 30), head=(14 if 2320 < f < 2410 else -6, (7 * math.sin((f - 2470) / 9) if 2470 < f < 2530 else 0)))   # looks down at the cup, up, exhales, small head shake
    for s in "LR":
        sx = 1 if s == "L" else -1
        for f in (2281, 2560):
            foot_at(RA, HA, s, f, Vector((120.0 - sx * 0.12, -2.0, HA.ankle[s].z)), yaw=180)
            knee_pole(RA, s, f, Vector((120.0 - sx * 0.15, -1.2, 0.6)))
        for f in (2281, 2560):
            sc.frame_set(f); bpy.context.view_layer.update()
            th = rigA.matrix_world @ rigA.pose.bones["upperleg02." + s].head
            place_hand(rigA, s, f, th + Vector((0, 0, 0.09)), Vector((0, 0, -1)), Vector((sx * 0.25, 1, 0)))
            apply_pose(rigA, s, "relaxed", f); pole(RA, s, f, Vector((120.0 - sx * 0.45, -2.5, 0.75)))
    cF_ = paper_cup("BoardCup", cB, (120.25, -1.60, ttop), with_logo=False)
    st = steam("BoardSteam", cB, (120.25, -1.60, ttop + CUP_H * 0.86), h=0.22, r=0.035, dens=0.45); key_steam(st, 2281, 2560)
    others = []   # 5b is a close-up of the boss (side executives dropped: fewer bodies, no chair contacts)
    for cid, hp, yaw in others:
        r2, R2, H2 = setup(cid, cid + "B5")
        Rz = Matrix.Rotation(R_(yaw), 3, 'Z')
        for f in (2281, 2560): H2.key_root(f, hp, yaw=yaw, flex=7)
        for f in range(2281, 2561, 20):
            nod = 8 * math.sin((f - 2440) / 8) if 2450 < f < 2520 else 0
            H2.key_spine(f, flex=3 + math.sin((f - 2281) / 33), head=(6 + nod, (-25 if cid == "ExecB" else 25) if f > 2445 else 0))
        for s in "LR":
            sx = 1 if s == "L" else -1
            for f in (2281, 2560):
                foot_at(R2, H2, s, f, hp + Rz @ Vector((sx * 0.12, -0.42, 0)) + Vector((0, 0, H2.ankle[s].z - hp.z)), yaw=yaw)
                knee_pole(R2, s, f, hp + Rz @ Vector((sx * 0.15, -0.9, 0.1)))
                sc.frame_set(f); bpy.context.view_layer.update()
                ex = r2.matrix_world @ r2.pose.bones["upperleg02." + s].head + Vector((0, 0, 0.09))   # hands rest on the thighs
                place_hand(r2, s, f, ex, Vector((0, 0, -1)), Rz @ Vector((-sx * 0.2, -1, 0)))
                apply_pose(r2, s, "relaxed", f); pole(R2, s, f, hp + Rz @ Vector((sx * 0.5, 0.2, 0.4)))
    cA = cam_shot("Cam5a", 2281, 2440, [(2281, (120.05, -0.10, 1.32), (120.0, -2.25, 1.10)), (2440, (120.0, -0.45, 1.28), (120.0, -2.25, 1.10))], lens=38)
    catchlight(rigA, cA, 2281, 2440)
    c5b = cam_shot("Cam5b", 2441, 2560, [(2441, (120.75, -1.30, 1.30), (120.0, -2.28, 1.18)), (2560, (120.68, -1.42, 1.29), (120.0, -2.28, 1.17))], lens=40)
    catchlight(rigA, c5b, 2441, 2560)

# ================================================================== B6 lower the temperature (2561..2860)
def beat_B6():
    FLOORS[:] = [bpy.data.objects["CafeFloor"]]
    rig, R, H = setup("Employee")
    tint(rig, "worksuit", (0.95, 0.55, 0.15))
    dial = bpy.data.objects["TempDial"]; knob = bpy.data.objects["DialKnob"]; needle = bpy.data.objects["DialNeedle"]
    sc.frame_set(2561); bpy.context.view_layer.update()
    kc = knob.matrix_world @ Vector((0, 0, 0.015)); kn = (knob.matrix_world.to_3x3() @ Vector((0, 0, 1))).normalized()
    pos = Vector((kc.x + 0.22, kc.y - 0.45, 0)); yaw = 180.0 + 18.0
    def hd(f): return (14, 0)
    stand(H, R, "Employee", 2561, 2860, pos, yaw, head=hd, flex=4)
    arms_relaxed(rig, R, H, 2561, pos, yaw)
    # left hand reaches the knob at 2600, turns it 2630..2690 (knob and hand rotate together), releases at 2730
    Rz = Matrix.Rotation(R_(yaw), 3, 'Z')
    pole(R, "L", 2561, pos + Rz @ Vector((0.4, 0.3, 1.0))); pole(R, "L", 2600, pos + Rz @ Vector((0.45, 0.1, 0.85)))
    knobm = bpy.data.objects["DialKnobMesh"]
    # tripod grip on the knob's rim: palm toward the knob face, then land the thumb/index midpoint on the rim front
    place_hand(rig, "L", 2600, kc + kn * 0.075, -kn, Vector((0.3, 0, -1)))
    apply_pose(rig, "L", "tripod", 2600)
    tgt = kc + kn * 0.026
    for it in range(8):
        sc.frame_set(2600); bpy.context.view_layer.update(); M = rig.matrix_world
        mid = M @ ((rig.pose.bones["finger2-3.L"].tail + rig.pose.bones["finger1-3.L"].tail) / 2)
        err = tgt - mid
        if err.length < 0.004: break
        hand_delta(R, "L", 2600, 2600, err)
    print("B6 knob grip err", round(err.length, 4))
    apply_pose(rig, "L", "relaxed", 2575)
    for f in (2630,): hold_fingers(rig, "L", 2600, f); hand_delta(R, "L", 2600, f, (0, 0, 0))
    turn = R_(-70)
    for f, a_ in ((2561, 0.0), (2630, 0.0), (2690, turn), (2860, turn)):
        knob.rotation_euler.z = a_; knob.keyframe_insert("rotation_euler", frame=f)
    hold_fingers(rig, "L", 2600, 2690); hand_about(R, "L", 2600, 2690, kc, Matrix.Rotation(turn, 3, kn))
    hold_fingers(rig, "L", 2600, 2705); hand_about(R, "L", 2600, 2705, kc, Matrix.Rotation(turn, 3, kn))
    hand_delta(R, "L", 2705, 2735, Rz @ Vector((0.05, 0.12, -0.05)))
    apply_pose(rig, "L", "relaxed", 2735)
    arms_relaxed(rig, R, H, 2800, pos, yaw); arms_relaxed(rig, R, H, 2860, pos, yaw)
    for f, a_ in ((2561, -1.9), (2650, -1.9), (2720, -0.35), (2760, -0.25), (2860, -0.25)):
        needle.rotation_euler.z = a_; needle.keyframe_insert("rotation_euler", frame=f)
    sc.frame_set(2650); bpy.context.view_layer.update()
    eh = rig.matrix_world @ rig.pose.bones["head"].tail; look = eh.lerp(kc, 0.45)
    c6a = cam_shot("Cam6a", 2561, 2700, [(2561, (kc.x + 0.85, kc.y - 0.10, 1.62), tuple(look)), (2700, (kc.x + 0.80, kc.y - 0.12, 1.60), tuple(look))], lens=24)
    catchlight(rig, c6a, 2561, 2700)
    dp = dial.matrix_world.translation
    cam_shot("Cam6b", 2701, 2860, [(2701, (dp.x + 0.02, dp.y - 0.30, dp.z + 0.02), tuple(dp)), (2860, (dp.x + 0.01, dp.y - 0.22, dp.z + 0.015), tuple(dp))], lens=50)

WIN = {"B2": (421, 1200), "B3": (1201, 1700), "B4": (1701, 2280), "B5": (2281, 2560), "B6": (2561, 2860)}
for b, fn in (("B2", beat_B2), ("B3", beat_B3), ("B4", beat_B4), ("B5", beat_B5), ("B6", beat_B6)):
    if want(b):
        CUR_WIN = WIN[b]; fn()
