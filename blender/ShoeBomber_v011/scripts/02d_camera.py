# ShoeBomber v011 stage B part 4 (exec'd from 02_animate.py after the story): the void cutaway, the sky, the airport,
# the ONE continuous camera and the set switches inside its whips.
SW1, SW2, SW3 = 885, 985, 1138          # whip mid-frames where the sets swap (cabin -> void -> sky -> airport)
VOIDR, SKYR, AIRR = O["SET_Void"], O["SET_Sky"], O["SET_Airport"]

# ================================================================== AIRPORT action (in airport-local coords, root at the origin while keying)
TV, AW = "Traveller", "AirWoman"
upd()
cb = [O["Air_Conveyor"].matrix_world @ Vector(c) for c in O["Air_Conveyor"].bound_box]
BELT_Z = max(p.z for p in cb); BX0, BX1 = min(p.x for p in cb), max(p.x for p in cb)
log("belt top", round(BELT_Z, 3), "x", round(BX0, 2), round(BX1, 2))
TR0, TR1, TR2, TR3 = [O["Tray%d" % k] for k in range(4)]
# empty trays stacked at the start of the belt (logo up), his tray and her tray on the rollers
for k, t in enumerate((TR3, TR2, TR1)):
    t.location = (BX0 + 0.10, 0.0, BELT_Z + 0.002 + 0.012 * k); t.rotation_euler = (0, 0, math.radians(90))
TR0.location = (-0.22, 0.0, BELT_Z + 0.002); TR0.rotation_euler = (0, 0, math.radians(90))
WT = TR1.copy(); WT.name = "TrayW"; TR1.users_collection[0].objects.link(WT)
for ch in TR1.children:
    c2 = ch.copy(); c2.parent = WT; TR1.users_collection[0].objects.link(c2)
WT.location = (0.55, 0.0, BELT_Z + 0.002)
TR1.location = (BX0 + 0.10, 0.0, BELT_Z + 0.002 + 0.012 * 2)
TS_L, TS_R = O["TravShoeL"], O["TravShoeR"]
for sh, dy, yw in ((TS_L, -0.07, 4), (TS_R, 0.07, -6)):
    sh.parent = TR0; sh.matrix_parent_inverse = Matrix.Identity(4)
    sh.location = (dy, 0.06, 0.010); sh.rotation_euler = (0, 0, math.radians(yw))
for k, sh in enumerate((O["WomanShoe0"], O["WomanShoe1"])):
    sh.parent = WT; sh.matrix_parent_inverse = Matrix.Identity(4); sh.location = (-0.07 + 0.14 * k, 0.0, 0.010)
for t in (TR0, WT):
    t.keyframe_insert("location", frame=1)
TR0.location.x = -0.22; TR0.keyframe_insert("location", frame=1215)
TR0.location.x = 0.75; TR0.keyframe_insert("location", frame=1335)
TR0.location.x = 1.25; TR0.keyframe_insert("location", frame=1469)
WT.location.x = 0.55; WT.keyframe_insert("location", frame=1137); WT.location.x = 1.45; WT.keyframe_insert("location", frame=1300)
# the traveller (socks) at the belt: hands on his tray's near rim, pushes it along, steps after it, then turns to camera and shrugs
TY = -0.62
def tray_rim(f):
    fs(f); M = TR0.matrix_world; return M @ Vector((0, -0.26, 0.10))
for f_ in (1, 1137, 1180):
    stand(TV, f_, -0.27, TY, 180.0, spine=14)
    P = tray_rim(f_)
    for s, dx in (("L", -0.13), ("R", 0.13)):
        rest_hand(TV, s, f_, P + Vector((dx, 0.0, 0.0)), (0, 1, -0.2), (0, 0.2, -1), pose="relaxed", pole=P + Vector((dx * 3, -0.5, 0.1)), skin=0.010)
for f_, x_ in ((1215, -0.27), (1255, -0.02), (1295, 0.22), (1335, 0.42)):
    stand(TV, f_, x_, TY, 180.0, spine=14)
    P = tray_rim(f_)
    for s, dx in (("L", -0.13), ("R", 0.13)):
        rest_hand(TV, s, f_, P + Vector((dx, 0.0, 0.0)), (0, 1, -0.2), (0, 0.2, -1), pose="relaxed", pole=P + Vector((dx * 3, -0.5, 0.1)), skin=0.010)
# lets go, straightens, looks down at his socks, then up at the camera with a shrug and a smile
TXE = 0.42
stand(TV, 1360, TXE, TY - 0.05, 190.0, spine=6); arms_down(TV, 1360, (TXE, TY - 0.05), 190.0)
stand(TV, 1395, TXE, TY - 0.05, 205.0, spine=10); arms_down(TV, 1395, (TXE, TY - 0.05), 205.0)
for f_, a in ((1420, 0.0), (1442, 1.0), (1469, 1.0)):
    yw = 215.0
    stand(TV, f_, TXE, TY - 0.05, yw, spine=3)
    for s in "LR":
        sx = 1 if s == "L" else -1
        P = body_pt(TV, (sx * (0.24 + 0.10 * a), -0.14 * a - 0.03, 0.80 + 0.12 * a), yw, (TXE, TY - 0.05, 0))
        hand_free(TV, s, f_, P, Ryaw(yw) @ Vector((sx * 0.6 * a, -0.4 * a, -1 + a)), Ryaw(yw) @ Vector((0, 0, 1)) if a else Ryaw(yw) @ Vector((-sx, 0, 0)),
                  pose="relaxed", pole=body_pt(TV, (sx * 0.55, 0.3, 0.95), yw, (TXE, TY - 0.05, 0)))
key_head(TV, 1137, 0, -30); key_head(TV, 1300, -10, -25); key_head(TV, 1370, 0, -26); key_head(TV, 1410, 5, -28); key_head(TV, 1438, 8, 4); key_head(TV, 1469, 6, 2)
key_face(TV, 1137, smile=0.1); key_face(TV, 1400, brow=0.4); key_face(TV, 1440, smile=0.75, brow=0.6); key_face(TV, 1469, smile=0.8, brow=0.5)
blinks(TV, [1160, 1260, 1352, 1425]); saccades(TV, 1137, 1469, seed=11)
# the woman (socks) walks through the arch behind the belt
walk(AW, [(-2.4, -1.75), (0.0, -1.85), (2.6, -1.95)], 1137, 1469, stride=0.62)
key_head(AW, 1137, 0, -6); key_head(AW, 1300, -10, -10); key_head(AW, 1469, -20, -4)
key_face(AW, 1137, smile=0.3); blinks(AW, [1200, 1330, 1440])
for n_ in (TV, AW):
    RIG[n_].parent = AIRR; RIG[n_].matrix_parent_inverse = Matrix.Identity(4)
for o in (TR0, TR1, TR2, TR3, WT):
    if o.parent != AIRR: o.parent = AIRR

fw = box("Air_WallFront", (14, 0.1, 4.0), (0, -4.2, 2.0), mat("M_AirWallFront", (0.85, 0.30, 0.05), rough=0.5), bevel=0)
fw.parent = AIRR
for c_ in list(fw.users_collection): c_.objects.unlink(fw)
bpy.data.collections["Airport"].objects.link(fw)
for k in range(4):
    L_ = bpy.data.objects.new("Air_FrontFill%d" % k, bpy.data.lights.new("Air_FrontFill%d" % k, 'AREA')); L_.data.energy = 120; L_.data.size = 2.0
    L_.location = (-3 + 2 * k, -3.0, 3.2); L_.parent = AIRR; bpy.data.collections["Airport"].objects.link(L_)
# ================================================================== VOID: the cutaway shoe (sole opens, the charge in the cavity)
CS, CU, CH, CV = O["CutShoe_Sole"], O["CutShoe_Upper"], O["CutShoe_Charge"], O["CutShoe_Cavity"]
for o in (CS, CU, CH, CV):
    o.parent = VOIDR; o.matrix_parent_inverse = Matrix.Identity(4)
CS.location = (0, 0, 0); CV.location = (0, 0, CV.location.z); CH.location = (0, 0, CH.location.z)
CU.location = (0, 0, 0); CU.keyframe_insert("location", frame=SW1 + 8); CU.rotation_euler = (0, 0, 0); CU.keyframe_insert("rotation_euler", frame=SW1 + 8)
CU.location = (0, 0, 0.075); CU.rotation_euler = (math.radians(-12), 0, 0); CU.keyframe_insert("location", frame=SW1 + 40); CU.keyframe_insert("rotation_euler", frame=SW1 + 40)
CU.location = (0, 0.01, 0.085); CU.keyframe_insert("location", frame=SW2)
# a fuse running into the charge
fz = O["FuseR"].copy(); fz.data = O["FuseR"].data.copy(); fz.name = "CutShoe_Fuse"; CS.users_collection[0].objects.link(fz)
fz.parent = VOIDR; fz.matrix_parent_inverse = Matrix.Identity(4); fz.location = (0, 0.02, CH.location.z + 0.004); fz.rotation_euler = (math.radians(-20), 0, 0)
VOID_PARTS = [CS, CU, CH, CV, fz]
# slow spin of the whole cutaway (one object: a turntable empty)
tt = bpy.data.objects.new("Void_Turntable", None); VOIDR.users_collection[0].objects.link(tt); tt.parent = VOIDR
for o in VOID_PARTS: o.parent = tt; o.matrix_parent_inverse = Matrix.Identity(4)
tt.rotation_euler = (0, 0, math.radians(-30)); tt.keyframe_insert("rotation_euler", frame=SW1)
tt.rotation_euler = (0, 0, math.radians(30)); tt.keyframe_insert("rotation_euler", frame=SW2)

# ================================================================== SKY: logo livery on the fuselage, clouds drifting back
PL = O["Airliner"]
vs = [PL.matrix_world @ v.co for v in PL.data.vertices]
LXa, LXb = min(p.x for p in vs), max(p.x for p in vs)
nose_pos = 1     # checked in the set render: the nose points +X
LX = (LXa + LXb) / 2 + nose_pos * 11.0
ring = [p for p in vs if abs(p.x - LX) < 0.6 and abs(p.y) < 3.0]
fz_mid = (max(p.z for p in ring) + min(p.z for p in ring)) / 2 if ring else 3.0
fy = min(p.y for p in ring if abs(p.z - fz_mid) < 0.6) if ring else -2.0
log("plane x", round(LXa, 1), round(LXb, 1), "logo x", round(LX, 1), "fuselage y", round(fy, 2), "z", round(fz_mid, 2), "nose sign", nose_pos)
LOGO_DARK = "/home/user/Muhammed/blender/assets/brand/DaKrasFilms_logo_dark.png"
img = bpy.data.images.load(LOGO_DARK); asp = img.size[1] / img.size[0]
bpy.ops.mesh.primitive_plane_add(size=1, location=(LX, fy - 0.03, fz_mid + 0.2), rotation=(math.radians(90), 0, 0))
LG = bpy.context.active_object; LG.name = "Logo_Fuselage"; LG.scale = (6.0, 6.0 * asp, 1)
if nose_pos < 0: LG.rotation_euler.z = 0
m = bpy.data.materials.new("M_LogoFuselage"); m.use_nodes = True; nt_ = m.node_tree; p_ = nt_.nodes["Principled BSDF"]
ti = nt_.nodes.new("ShaderNodeTexImage"); ti.image = img
nt_.links.new(ti.outputs["Color"], p_.inputs["Base Color"]); nt_.links.new(ti.outputs["Alpha"], p_.inputs["Alpha"]); p_.inputs["Roughness"].default_value = 0.35
LG.data.materials.append(m)
sdl = LG.modifiers.new("sd", 'SUBSURF'); sdl.subdivision_type = 'SIMPLE'; sdl.levels = sdl.render_levels = 5
swl = LG.modifiers.new("wrap", 'SHRINKWRAP'); swl.target = PL; swl.wrap_method = 'NEAREST_SURFACEPOINT'
swl.wrap_mode = 'OUTSIDE_SURFACE'; swl.offset = 0.04
bpy.context.view_layer.objects.active = LG
for mname in ("sd", "wrap"): bpy.ops.object.modifier_apply(modifier=mname)
LG.parent = SKYR; SKYR.users_collection[0].objects.link(LG) if LG.name not in SKYR.users_collection[0].objects else None
for c_ in list(LG.users_collection):
    if c_ != SKYR.users_collection[0]: c_.objects.unlink(LG)
LG["logo_frames"] = "1000-1095"
# deep red cheatline under the windows (procedural band on the fuselage: a thin strip)
CL = O["Sky_Clouds"]
cm = CL.data.materials[0]; nt_ = cm.node_tree; pb = nt_.nodes["Principled BSDF"]
tc_ = nt_.nodes.new("ShaderNodeTexCoord"); sx_ = nt_.nodes.new("ShaderNodeSeparateXYZ"); mr_ = nt_.nodes.new("ShaderNodeMapRange")
mr_.inputs["From Min"].default_value = -6; mr_.inputs["From Max"].default_value = 18
cr_ = nt_.nodes.new("ShaderNodeValToRGB"); cr_.color_ramp.elements[0].color = (0.18, 0.32, 0.70, 1); cr_.color_ramp.elements[1].color = (1, 1, 1, 1)
nt_.links.new(tc_.outputs["Object"], sx_.inputs[0]); nt_.links.new(sx_.outputs["Z"], mr_.inputs["Value"]); nt_.links.new(mr_.outputs["Result"], cr_.inputs["Fac"])
nt_.links.new(cr_.outputs["Color"], pb.inputs["Base Color"]); pb.inputs["Emission Strength"].default_value = 0.0
O["Sky_Sun"].rotation_euler = (math.radians(62), math.radians(15), math.radians(40))
CL.location = (0, 0, -60); CL.keyframe_insert("location", frame=SW2)
CL.location = (-nose_pos * 60, 0, -60); CL.keyframe_insert("location", frame=SW3)
set_interp(CL, 'LINEAR')

# ================================================================== CAMERA keys per set (local coords), joined into one world path
TLc = fuse_tip(FUSE_L); TRc = fuse_tip(FUSE_R)
def V(*a): return Vector(a)
CABK = [  # frame, camera, aim, lens
 (1, V(-0.50, 1.42, 1.30), V(-0.63, 0.30, 0.90), 30), (50, V(-0.60, 1.15, 1.12), V(-0.62, 0.42, 0.82), 32),
 (105, V(-0.70, 0.92, 1.00), TLc + V(0.02, 0, -0.02), 34), (150, V(-0.62, 0.88, 0.98), TLc + V(0.02, 0, -0.01), 36), (166, V(-0.52, 0.78, 1.12), V(-0.15, 1.70, 1.30), 34),
 (182, V(-0.30, 0.74, 1.30), V(0.05, 2.6, 1.45), 30), (215, V(0.12, 0.72, 1.48), V(0.08, 1.48, 1.52), 34),
 (255, V(0.24, 0.86, 1.52), V(0.06, 1.48, 1.48), 34), (272, V(0.34, 1.20, 1.60), V(-0.40, 0.45, 1.02), 32), (292, V(0.42, 1.62, 1.66), V(-0.30, 0.55, 1.00), 30),
 (340, V(0.22, 1.66, 1.56), V(-0.60, 0.38, 0.92), 34), (372, V(0.50, 1.95, 1.80), V(-0.45, 0.70, 1.05), 26),
 (405, V(0.90, 1.70, 1.88), V(-0.35, 0.85, 1.12), 24), (420, V(0.90, 1.70, 1.88), V(-0.20, 0.92, 0.95), 24), (432, V(0.88, 1.72, 1.86), V(0.0, 1.0, 0.70), 24),
 (439, V(0.86, 1.72, 1.86), V(-1.22, 1.52, 1.45), 30), (448, V(0.84, 1.72, 1.85), V(-1.20, 1.52, 1.42), 32),
 (460, V(0.70, 1.72, 1.80), V(0.62, 0.92, 0.25), 24), (500, V(0.72, 1.70, 1.72), V(0.64, 0.92, 0.28), 26),
 (535, V(0.80, 1.58, 1.22), V(0.76, 0.98, 0.36), 32), (575, V(0.84, 1.55, 1.12), V(0.80, 1.00, 0.34), 34), (615, V(0.95, 1.55, 1.08), V(0.98, 1.08, 0.24), 34),
 (650, V(-0.20, 1.45, 1.55), V(-0.60, 0.40, 0.80), 28), (700, V(0.02, 0.30, 1.32), V(-0.70, 0.45, 0.92), 28),
 (752, V(-0.45, 0.42, 0.98), TLc + V(0, 0, -0.04), 34), (780, V(-0.86, 0.52, 1.28), V(-0.88, 0.08, 0.60), 30), (812, V(-0.94, 0.34, 0.92), TRc + V(0, 0, -0.04), 34),
 (860, V(-0.98, 0.25, 0.74), TRc + V(0, 0.0, -0.06), 40), (880, V(-1.02, 0.24, 0.72), TRc + V(0, 0.0, -0.07), 42),
]
# whip out of the cabin: the aim swings up and to the left over ~10 frames
def whip_dir(f0, d0, ang_deg, axis):
    return (Matrix.Rotation(math.radians(ang_deg), 3, axis) @ d0)
c880, a880 = CABK[-1][1], CABK[-1][2]
d880 = (a880 - c880).normalized()
WH1 = [(f, c880 + V(0, 0.002 * (f - 880), 0), c880 + whip_dir(880, d880, 70 * (f - 880) / 5.0, 'Z'), 44) for f in (882, 884)]
CABK += WH1
# void (local to SET_Void; the shoe at the origin)
VK_local = [(SW1, None, None, 44), (SW1 + 3, V(0.30, -0.42, 0.20), V(0, 0, 0.05), 44), (SW1 + 40, V(0.22, -0.46, 0.26), V(0, 0, 0.06), 46),
            (SW1 + 85, V(-0.05, -0.50, 0.30), V(0, 0, 0.07), 48), (SW2 - 3, V(-0.10, -0.48, 0.34), V(0, 0, 0.12), 48)]
# sky (local to SET_Sky; the fuselage logo at (LX, fy, fz))
SK_local = [(SW2, None, None, 35), (SW2 + 8, V(LX - 1.5, fy - 15.0, fz_mid - 1.0), V(LX, fy, fz_mid + 0.9), 35),
            (1090, V(LX + 4.5, fy - 17.0, fz_mid - 1.4), V(LX + 1.5, fy, fz_mid + 0.8), 35),
            (1125, V(LX - 12, fy - 50, fz_mid + 14), V((LXa + LXb) / 2, 0, fz_mid), 35), (SW3 - 3, V(LX - 14, fy - 58, fz_mid + 16), V((LXa + LXb) / 2, 0, fz_mid - 2), 35)]
# airport (local to SET_Airport)
AK_local = [(SW3, None, None, 30), (SW3 + 6, V(BX0 - 0.08, -0.46, 1.40), V(BX0 + 0.10, 0.02, BELT_Z), 30),
            (1225, V(BX0 + 0.22, -0.36, 1.28), V(BX0 + 0.12, 0.02, BELT_Z), 32), (1245, V(-0.85, 0.30, 1.45), V(-0.40, -0.30, 1.00), 28), (1262, V(-0.60, 0.55, 1.48), V(-0.20, -0.35, 0.98), 28),
            (1330, V(-0.20, 0.58, 1.48), V(0.20, -0.40, 1.00), 28), (1400, V(-0.45, 0.30, 1.45), V(0.40, -0.62, 1.20), 30),
            (1469, V(-0.38, 0.22, 1.48), V(0.42, -0.62, 1.35), 34)]
def catmull_at(keys, f):
    xs = [k[0] for k in keys]
    if f <= xs[0]: return keys[0][1]
    if f >= xs[-1]: return keys[-1][1]
    i = max(j for j in range(len(xs) - 1) if xs[j] <= f)
    p0 = keys[max(0, i - 1)][1]; p1 = keys[i][1]; p2 = keys[i + 1][1]; p3 = keys[min(len(keys) - 1, i + 2)][1]
    t0, t1 = xs[i], xs[i + 1]; u = (f - t0) / (t1 - t0)
    # monotone-ish: tangents scaled by interval (finite differences), clamp overshoot by using 0.5 factor
    def tan(a, b, ta, tb): return (b - a) / max(1e-6, tb - ta)
    m1 = (tan(p0, p2, keys[max(0, i - 1)][0], xs[i + 1])) * (t1 - t0) * 0.5
    m2 = (tan(p1, p3, xs[i], keys[min(len(keys) - 1, i + 2)][0])) * (t1 - t0) * 0.5
    h00 = 2 * u ** 3 - 3 * u ** 2 + 1; h10 = u ** 3 - 2 * u ** 2 + u; h01 = -2 * u ** 3 + 3 * u ** 2; h11 = u ** 3 - u ** 2
    return p1 * h00 + m1 * h10 + p2 * h01 + m2 * h11
def lens_at(keys, f):
    xs = [k[0] for k in keys]
    if f <= xs[0]: return keys[0][3]
    if f >= xs[-1]: return keys[-1][3]
    i = max(j for j in range(len(xs) - 1) if xs[j] <= f); u = smoothstep((f - xs[i]) / (xs[i + 1] - xs[i]))
    return keys[i][3] + (keys[i + 1][3] - keys[i][3]) * u
CAMP = {}; AIMP = {}; LENS = {}
def run(keys, f0, f1):
    ck = [(k[0], k[1], None, k[3]) for k in keys]; ak = [(k[0], k[2], None, k[3]) for k in keys]
    for f in range(f0, f1 + 1):
        CAMP[f] = catmull_at(ck, f); AIMP[f] = catmull_at(ak, f); LENS[f] = lens_at(keys, f)
run(CABK, 1, SW1 - 1)
def join_set(root, local_keys, f_swap, f_end, prev_dir_frames=3):
    """place the set root so the camera is continuous at the swap; the first post-swap aim continues the whip"""
    c_prev = CAMP[f_swap - 1]; a_prev = AIMP[f_swap - 1]; d_prev = (a_prev - CAMP[f_swap - 1]).normalized()
    c_loc = local_keys[1][1] + (local_keys[1][1] - local_keys[2][1]) * 0.15
    root.location = c_prev - c_loc
    upd()
    k0 = (f_swap, c_prev, root.location + local_keys[1][2], local_keys[0][3])
    wk = [k0] + [(f, root.location + c, root.location + a, l) for (f, c, a, l) in local_keys[1:]]
    run(wk, f_swap, f_end)
    return wk
join_set(VOIDR, VK_local, SW1, SW2 - 1)
# whip out of the void: aim swings to the side
cv, av = CAMP[SW2 - 3], AIMP[SW2 - 3]; dv = (av - cv).normalized()
for k_, f in enumerate((SW2 - 2, SW2 - 1)):
    AIMP[f] = cv + Matrix.Rotation(math.radians(-35 * (k_ + 1)), 3, 'Z') @ dv; CAMP[f] = cv
join_set(SKYR, SK_local, SW2, SW3 - 1)
cs_, as_ = CAMP[SW3 - 3], AIMP[SW3 - 3]; ds = (as_ - cs_).normalized()
for k_, f in enumerate((SW3 - 2, SW3 - 1)):
    ax_ = ds.cross(V(0, 0, 1)).normalized()
    AIMP[f] = cs_ + Matrix.Rotation(math.radians(-30 * (k_ + 1)), 3, ax_) @ ds; CAMP[f] = cs_
join_set(AIRR, AK_local, SW3, END)
log("roots", "void", tuple(round(v, 2) for v in VOIDR.location), "sky", tuple(round(v, 2) for v in SKYR.location), "air", tuple(round(v, 2) for v in AIRR.location))
# write the camera
cam = bpy.data.objects.get("CAM_Film") or bpy.data.objects.new("CAM_Film", bpy.data.cameras.new("CAM_Film"))
if cam.name not in sc.collection.objects: sc.collection.objects.link(cam)
aim = bpy.data.objects.get("CAM_Film_Aim") or bpy.data.objects.new("CAM_Film_Aim", None)
if aim.name not in sc.collection.objects: sc.collection.objects.link(aim)
tr = cam.constraints.new('TRACK_TO'); tr.target = aim; tr.track_axis = 'TRACK_NEGATIVE_Z'; tr.up_axis = 'UP_Y'
cam.data.dof.use_dof = True; cam.data.dof.focus_object = aim; cam.data.dof.aperture_fstop = 11.0
cam.data.clip_start = 0.01; cam.data.clip_end = 1200; cam.data.sensor_fit = 'AUTO'
for f in range(1, END + 1):
    cam.location = CAMP[f]; cam.keyframe_insert("location", frame=f)
    aim.location = AIMP[f]; aim.keyframe_insert("location", frame=f)
    cam.data.lens = LENS[f]; cam.data.keyframe_insert("lens", frame=f)
for o in (cam, aim, cam.data): set_interp(o, 'LINEAR')
sc.camera = cam
cl_ = bpy.data.objects.new("CAM_Catchlight", bpy.data.lights.new("CAM_Catchlight", 'POINT')); sc.collection.objects.link(cl_)
cl_.data.energy = 6.0; cl_.data.shadow_soft_size = 0.25; cl_.data.color = (1.0, 0.95, 0.9); cl_.parent = cam; cl_.location = (0.10, 0.15, 0.0)
cl_.visible_glossy = True
# ================================================================== set visibility (keyed hide_render + hide_viewport)
def coll_objs(name): return [o for o in bpy.data.collections[name].all_objects]
CAB_SET = coll_objs("Cabin") + coll_objs("Props") + [o for o in O if o.name.startswith(("SpentMatch", "Cuff_"))]
for n_ in ("Bomber", "Attendant", "Steward", "PaxA", "PaxW"): CAB_SET += [RIG[n_]] + list(RIG[n_].children_recursive)
AIR_SET = coll_objs("Airport") + [RIG[TV]] + list(RIG[TV].children_recursive) + [RIG[AW]] + list(RIG[AW].children_recursive) + [WT] + list(WT.children)
VOID_SET = coll_objs("Void") + [tt]
SKY_SET = coll_objs("Sky")
def show(objs, ranges):
    seen = set()
    for o in objs:
        if o.name in seen: continue
        seen.add(o.name)
        keep_hidden = {f: None for f in ()}
        vis(o, 1, False)
        for a, b in ranges:
            vis(o, a, True); vis(o, b + 1, False)
show(CAB_SET, [(1, SW1 - 1)]); show(VOID_SET, [(SW1, SW2 - 1)]); show(SKY_SET, [(SW2, SW3 - 1)]); show(AIR_SET, [(SW3, END)])
# objects that were already switched inside the cabin story keep their own keys: flame (off 383), syringe (on 440), cuffs (on 440)
for o, on in ((O["Flame"], (1, 382)), (O["FlameLight"], (1, 382)), (O["Syringe"], (450, SW1 - 1)), (O["Cuff_Strap"], (440, SW1 - 1)), (O["Cuff_L"], (440, SW1 - 1)), (O["Cuff_R"], (440, SW1 - 1))):
    for fc in (o.animation_data.action.fcurves if hasattr(o.animation_data.action, "fcurves") else []):
        pass
    o.animation_data_clear() if False else None
    # rebuild hide keys cleanly
    ad = o.animation_data
    if ad and ad.action:
        for fc in list(iter_fcurves(ad.action)):
            if fc.data_path.startswith("hide"):
                while len(fc.keyframe_points): fc.keyframe_points.remove(fc.keyframe_points[0])
    vis(o, 1, False); vis(o, on[0], True); vis(o, on[1] + 1, False)
# per-set exposure
for f, ev_ in ((1, -0.2), (SW1, 0.0), (SW2, -0.65), (SW3, -0.45)):
    sc.view_settings.exposure = ev_; sc.view_settings.keyframe_insert("exposure", frame=f)
for fc in iter_fcurves(sc.animation_data.action):
    for kp in fc.keyframe_points: kp.interpolation = 'CONSTANT'
