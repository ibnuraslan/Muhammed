# exec'd by 03_anim.py: underground S7, S8; dump site S9-S14; house frames on the cut-away S15
UX = Vector((600, 0, 0)); UX2 = Vector((600, 60, 0)); DX = Vector((900, 0, 0))
key_vis(OB["Backdrop_under"], [(0, False)] + [x for s_ in ("S7", "S8", "S15") for x in ((f0(s_), True), (f1(s_) + 1, False))])
camshot("S7", [(0.0, (600.0, -42.0, 4.0), (600.0, 0.0, 1.5), 32), (1.0, (600.0, -39.0, 2.2), (600.0, 0.0, -4.0), 32)])
camshot("S8", [(0.0, (597.5, -15.5, -5.6), (600.0, -4.0, -6.4), 30), (1.0, (598.8, -12.0, -5.7), (600.5, -3.0, -6.5), 30)])
SL = OB["Under_sludge"]; SL2 = OB["Under2_sludge"]
for o in (SL, SL2):             # slow flow: the ripple texture drifts (keyed, not Scene Time)
    tx = o.modifiers["ripple"].texture; tcoord = bpy.data.objects.new(o.name + "_flow", None); o.users_collection[0].objects.link(tcoord)
    o.modifiers["ripple"].texture_coords = 'OBJECT'; o.modifiers["ripple"].texture_coords_object = tcoord
    tcoord.location = (0, 0, 0); tcoord.keyframe_insert("location", frame=1); tcoord.location = (0, 18, 0); tcoord.keyframe_insert("location", frame=sc.frame_end)
    for fc in fcurves_of(tcoord.animation_data.action):
        for k in fc.keyframe_points: k.interpolation = 'LINEAR'

# ================================================================== S9: the Worker rolls a drum by pushing it with both palms
WK = CH["Worker"]; HAT = OB.get("Worker.hardhat")
if HAT:          # bone parent: the hat rides on the head bone, sitting on the crown
    rig = WK.r.o; bn = rig.data.bones["head"]
    tail = bn.tail_local; desired = Matrix.Translation(tail + Vector((0, -0.005, -0.045)))
    HAT.parent = rig; HAT.parent_type = 'BONE'; HAT.parent_bone = "head"
    Mb = Matrix.Translation(tail) @ bn.matrix_local.to_3x3().to_4x4()
    HAT.matrix_parent_inverse = Matrix.Identity(4); HAT.matrix_basis = Mb.inverted() @ desired
DR = copy_obj(OB["LIB_drum"], "PushDrum", (0, 0, 0), c=OB["DumpGround"].users_collection[0])
r_d = 0.285
WK0 = DX + Vector((-1.6, -18.0, 0)); V_W = 0.9
put("Worker", [("S9", WK0, 90), ("S10", DX + Vector((0, 18.6, 0)), 0)])
fa = f0("S9"); fe = fx("S9")
pth = lambda f: Vector((0, -V_W * (f - fa) / FPS, 0))
WK.walk(pth, lambda f: 0.0, fa, fe, stride=0.55, lift=0.06, bob=0.012, crouch=0.12, lean=30)
DR.rotation_mode = 'XYZ'
for f in range(fa - 1, fe + 2):
    d = V_W * (f - fa) / FPS
    c = WK0 + Vector((0.78 + d, 0, r_d))
    DR.location = c; DR.rotation_euler = (R_(90), d / r_d, 0)      # lying, axis along Y, rolling toward +X
    DR.keyframe_insert("location", frame=f); DR.keyframe_insert("rotation_euler", frame=f)
    if (f - fa) % 2: continue
    for s, sy in (("L", 0.17), ("R", -0.17)):
        p = c + Vector((-0.19, sy, 0.21)); n = (c + Vector((0, sy, 0)) - p).normalized()
        place_hand(WK.r.o, s, f, p, n, Vector((0.55, 0, 0.83)))
for s in "LR": apply_pose(WK.r.o, s, "flat_palm", fa)
face(WK, fa, -0.004, -12); blinks(WK, fa, fe, -0.004, -12)
for f in range(fa, fe + 1, 20): WK.key_spine(f, flex=30, head=(-30, 0))
camshot("S9", [(0.0, (DX.x + 3.4, -20.6, 0.95), (DX.x - 0.4, -18.0, 0.75), 30), (1.0, (DX.x + 3.8, -20.0, 0.9), (DX.x + 0.2, -18.0, 0.75), 30)])

# ================================================================== S10: trucks loaded with drums; the Worker walks between them
fa = f0("S10"); fe = fx("S10")
pth = walk_line(WK, fa, fe, (0, 0), 1.1)
walk_arms(WK, fa, fe, pth); face(WK, fa, -0.002, -8)
for f in range(fa, fe + 1, 20): WK.key_spine(f, flex=4, head=(2, 0))
camshot("S10", [(0.0, (DX.x + 1.8, 7.5, 1.75), (DX.x - 0.3, 17.0, 1.4), 24), (1.0, (DX.x + 1.5, 8.6, 1.7), (DX.x - 0.3, 17.0, 1.4), 24)])

# ================================================================== S11-S13: drums tip out of the truck beds and pile up in the pit (rigid bodies baked to keys)
SIM0 = f0("S11") - 1; SIM1 = fx("S13") + 90
DCOLL = coll("SET_drums")
bpy.ops.rigidbody.world_add(); rbw = sc.rigidbody_world
rbw.substeps_per_frame = 8; rbw.solver_iterations = 20
rbw.point_cache.frame_start = SIM0; rbw.point_cache.frame_end = SIM1
if not rbw.collection: rbw.collection = bpy.data.collections.new("RigidBodyWorld")
def rb(o, typ, shape, kin=False, mass=180.0, fr=0.55, rest=0.05):
    with bpy.context.temp_override(object=o, active_object=o, selected_objects=[o]):
        bpy.ops.rigidbody.object_add()
    r = o.rigid_body; r.type = typ; r.collision_shape = shape; r.kinematic = kin; r.mass = mass; r.friction = fr; r.restitution = rest
    r.collision_margin = 0.01; r.use_deactivation = False; r.linear_damping = 0.35; r.angular_damping = 0.75
    return r
rb(OB["DumpGround"], 'PASSIVE', 'MESH', fr=0.95)
BEDS = [OB["DumpTruck%d_bed" % i] for i in range(2)]
for b in BEDS:
    rb(b, 'PASSIVE', 'MESH', kin=True); b.rigid_body.collision_margin = 0.02
    b.rotation_mode = 'XYZ'
    b.rotation_euler = (0, 0, 0); b.keyframe_insert("rotation_euler", frame=0); b.keyframe_insert("rotation_euler", frame=SIM0 + 10)
    b.rotation_euler = (R_(-52), 0, 0); b.keyframe_insert("rotation_euler", frame=SIM0 + 100); b.keyframe_insert("rotation_euler", frame=SIM1)
L_dr = OB["LIB_drum"]; drums = []
random.seed(11)
ev(1)
for bi, b in enumerate(BEDS):            # wave 1: drums standing in each bed (visible in S10)
    bmn, bmx = bbox([b])
    for ix in range(3):
        for iy in range(5):
            x = bmn.x + 0.45 + ix * 0.62; y = bmn.y + 0.7 + iy * 0.75
            d = copy_obj(L_dr, "Drum_b%d_%d%d" % (bi, ix, iy), (x, y, bmn.z + 0.32 + 0.002), c=DCOLL); d.rotation_euler = (0, 0, random.random() * 6)
            rb(d, 'ACTIVE', 'CYLINDER'); drums.append(d)
N2 = 560
for i in range(N2):                      # wave 2: drums keep coming over the rim from the truck side (spawned out of frame)
    rel = SIM0 + 70 + int((SIM1 - SIM0 - 220) * (i / N2) ** 0.85)
    x = DX.x + random.uniform(-3.5, 3.5); y = 8.5 + random.uniform(0, 1.8); z = 1.2 + random.uniform(0, 1.2)
    d = copy_obj(L_dr, "Drum_w%03d" % i, (x, y, z), c=DCOLL)
    d.rotation_euler = (R_(random.choice((0, 0, 0, 90))), 0, random.random() * 6)
    r = rb(d, 'ACTIVE', 'CYLINDER', kin=True)
    d.keyframe_insert("location", frame=rel - 6); r.keyframe_insert("kinematic", frame=rel - 1)
    d.location = (x - (x - DX.x) * 0.04, y - 0.45, z - 0.05); d.keyframe_insert("location", frame=rel)
    r.kinematic = False; r.keyframe_insert("kinematic", frame=rel)
    key_vis(d, [(0, False), (rel - 6, True)])
    drums.append(d)
for o in rbw.collection.objects: pass
print("SIM drums", len(drums), SIM0, SIM1)
rec = {d.name: [] for d in drums}
for f in range(SIM0, SIM1 + 1):
    sc.frame_set(f)
    if (f - SIM0) % 2 and f != SIM1: continue
    for d in drums: rec[d.name].append((f, d.matrix_world.copy()))
for d in drums:
    with bpy.context.temp_override(object=d, active_object=d, selected_objects=[d]):
        bpy.ops.rigidbody.object_remove()
    ad = d.animation_data
    if ad and ad.action:
        for fc in list(fcurves_of(ad.action)):
            if fc.data_path in ("location", "rotation_euler", "rotation_quaternion"): fc.keyframe_points.clear()
    d.rotation_mode = 'QUATERNION'; prev = None
    for f, M in rec[d.name]:
        l_, q_, _ = M.decompose()
        if prev is not None and prev.dot(q_) < 0: q_ = -q_
        prev = q_; d.location = l_; d.rotation_quaternion = q_
        d.keyframe_insert("location", frame=f); d.keyframe_insert("rotation_quaternion", frame=f)
for o in (OB["DumpGround"], *BEDS):
    with bpy.context.temp_override(object=o, active_object=o, selected_objects=[o]):
        bpy.ops.rigidbody.object_remove()
with bpy.context.temp_override(scene=sc):
    bpy.ops.rigidbody.world_remove()
for d in drums:                          # drums that rolled out onto the flat would sit in front of the S13/S14 lenses: gone after the cut
    fz, Mz = rec[d.name][-1]
    if (Mz.translation.to_2d() - DX.to_2d()).length > 10.0 or Mz.translation.y < -6.5:
        key_vis(d, [(f0("S13"), False)])
camshot("S11", [(0.0, (DX.x + 0.01, 10.5, 18.0), (DX.x, 10.51, 0.0), 26), (1.0, (DX.x + 0.01, 9.0, 21.0), (DX.x, 9.01, 0.0), 26)])
camshot("S12", [(0.0, (DX.x + 0.01, 0.0, 15.0), (DX.x, 0.01, 0.0), 24), (1.0, (DX.x + 0.01, 0.0, 17.5), (DX.x, 0.01, 0.0), 24)])
camshot("S13", [(0.0, (DX.x - 11.0, -10.0, 3.6), (DX.x, 0.0, -1.2), 28), (1.0, (DX.x - 7.8, -12.6, 3.8), (DX.x, 0.0, -1.2), 28)])

# ================================================================== S14: the bulldozer pushes a wave of dirt over the drums
fa = f0("S14"); fe = fx("S14")
DOZ = OB["Dozer"]; DOZ.rotation_mode = 'XYZ'
DOZ_RZ = 180.0                       # the model's blade faces -X
M_dirt = bpy.data.materials["Dirt"]
FILL = box("DirtFill", (1, 30, 4.0), (0, 0, -2.0), M_dirt, OB["DumpGround"].users_collection[0])
FILL.data.transform(Matrix.Translation((0.5, 0, 0))); FILL.location = DX + Vector((-16, 0, 0.12))
x0 = DX.x - 15.0; v = 2.4
for f in range(fa - 1, fe + 2, 2):
    x = x0 + v * max(0, (f - fa)) / FPS
    key_prop(DOZ, f, (x, 0.0, 0.12), (0, 0, DOZ_RZ))
    FILL.scale = (max(0.01, x - 1.0 - FILL.location.x), 1, 1); FILL.keyframe_insert("scale", frame=f)
bpy.ops.mesh.primitive_uv_sphere_add(radius=1, segments=24, ring_count=12); MOUND = bpy.context.active_object; MOUND.name = "DirtWave"
MOUND.scale = (0.9, 2.6, 0.75); MOUND.data.materials.append(pbr('DirtWave', 'brown_mud', 0.5, tint=(0.75, 0.55, 0.4), coords='Object')); link(MOUND, OB["DumpGround"].users_collection[0])
txm = bpy.data.textures.new("mound", 'CLOUDS'); txm.noise_scale = 0.35; dm = MOUND.modifiers.new("lumps", 'DISPLACE'); dm.texture = txm; dm.strength = 0.25
for f in range(fa - 1, fe + 2, 2):
    x = x0 + v * max(0, (f - fa)) / FPS
    key_prop(MOUND, f, (x + DOZ.get("blade", 3.6), 0.0, 0.25), (0, 0, 0))
key_vis(MOUND, [(0, False), (fa, True)]); key_vis(FILL, [(0, False), (fa, True)])
camshot("S14", [(0.0, (DX.x - 7.0, -13.0, 3.3), (DX.x - 13.0, 0.0, 0.9), 32), (1.0, (DX.x - 6.6, -12.2, 3.1), (DX.x - 11.5, 0.0, 0.9), 32)])

# ================================================================== S15: houses are framed on top of the cut-away while the green pockets glow underneath
fa = f0("S15"); fe = fx("S15")
k = 0
for r_ in ("Frame0", "Frame1"):
    root = OB[r_]
    kids = sorted([c for c in root.children], key=lambda o: (0 if "deck" in o.name else 2 if "roof" in o.name else 1, o.name))
    for c in kids:
        st = fa + 6 + k * 9 + (40 if "roof" in c.name else 0); k += 1
        base = c.location.copy()
        c.location = base + Vector((0, 0, -3.4)); c.keyframe_insert("location", frame=0); c.keyframe_insert("location", frame=st)
        c.location = base + Vector((0, 0, 0.12)); c.keyframe_insert("location", frame=st + 18)
        c.location = base; c.keyframe_insert("location", frame=st + 24)
camshot("S15", [(0.0, (574.0, 30.0, 9.0), (600.0, 60.0, -1.5), 30), (1.0, (589.0, 24.5, 8.0), (600.0, 60.0, -1.5), 30)])
