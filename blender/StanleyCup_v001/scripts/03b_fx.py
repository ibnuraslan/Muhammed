# Part of 03_animate.py: wall break-through (booleans + keyed debris), tumbler impact (dent, sparks, ripples, x-ray), room life.
import bmesh
C_FX = bpy.data.collections["FX"]
random.seed(21)
def mat(name, color, rough=0.5, emit=None, estr=0.0, metal=0.0):
    m = bpy.data.materials.get(name)
    if m: return m
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1); b.inputs["Roughness"].default_value = rough; b.inputs["Metallic"].default_value = metal
    if emit: b.inputs["Emission Color"].default_value = (*emit, 1); b.inputs["Emission Strength"].default_value = estr
    return m
def jag_sphere(name, r, rough=0.35, seed=0, coll=C_FX):
    me = bpy.data.meshes.new(name); bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=2, radius=r)
    rnd = random.Random(seed)
    for v in bm.verts: v.co *= 1.0 + rnd.uniform(-rough, rough)
    bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); coll.objects.link(o); return o
def shard(name, size, m, seed, coll=C_FX, flat_=0.25):
    me = bpy.data.meshes.new(name); bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
    rnd = random.Random(seed)
    for v in bm.verts: v.co = Vector((v.co.x * size[0] * rnd.uniform(0.6, 1.4), v.co.y * size[1] * rnd.uniform(0.6, 1.4), v.co.z * size[2] * rnd.uniform(0.6, 1.4)))
    bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); coll.objects.link(o); me.materials.append(m); return o
def ballistic(o, f0, f1, p0, v, g, spin, scale0=1.0, step=2, settle_z=None, hide_before=True):
    """keyed flight in story-time: p(t) = p0 + v t + 0.5 g t^2, t in frames"""
    o.rotation_mode = "XYZ"
    if hide_before:
        o.scale = (0, 0, 0); o.keyframe_insert("scale", frame=f0 - 1)
    o.scale = (scale0,) * 3; o.keyframe_insert("scale", frame=f0)
    e0 = Vector((random.uniform(0, 6), random.uniform(0, 6), random.uniform(0, 6)))
    for f in list(range(f0, f1 + 1, step)) + [f1]:
        t = f - f0; p = p0 + v * t + 0.5 * g * t * t
        if settle_z is not None and p.z < settle_z: p.z = settle_z
        o.location = p; o.keyframe_insert("location", frame=f)
        o.rotation_euler = e0 + spin * t; o.keyframe_insert("rotation_euler", frame=f)

# ---------------- holes: one jagged cutter per layer, scaled up as the bullet nose reaches it
HOLE = Vector(sc["hole"])
def x_at_frame(xx):
    for f in range(100, 300):
        if P(f).x + NOSE * D.x >= xx: return f
    return 300
layers = [o for o in bpy.data.objects if o.name.split(".")[0] in ("Siding", "Sheathing", "Drywall", "Insulation") and o.type == "MESH"]
cut_n = 0
for o in layers:
    bb = [o.matrix_world @ Vector(c) for c in o.bound_box]
    y0, y1 = min(v.y for v in bb), max(v.y for v in bb); z0, z1 = min(v.z for v in bb), max(v.z for v in bb)
    x0, x1 = min(v.x for v in bb), max(v.x for v in bb)
    yc = HOLE.y + (x0 - HOLE.x) * D.y / D.x; zc = HOLE.z + (x0 - HOLE.x) * D.z / D.x
    if not (y0 - 0.03 < yc < y1 + 0.03 and z0 - 0.03 < zc < z1 + 0.03): continue
    kind = o.name.split(".")[0]
    rad = {"Siding": 0.016, "Sheathing": 0.011, "Insulation": 0.03, "Drywall": 0.03}[kind]
    c = jag_sphere("HoleCutter_" + kind, 1.0, 0.3, seed=cut_n); cut_n += 1
    c.location = on_line((x0 + x1) / 2); c.display_type = "WIRE"; c.hide_render = True
    c.rotation_euler = D.to_track_quat('X', 'Z').to_euler()     # long axis along the flight line: a clean tunnel through each layer
    fhit = x_at_frame(x0 if kind != "Drywall" else x0)
    for f, s in ((1, 0.0), (fhit - 1, 0.0), (fhit + 6, rad * 0.8), (fhit + 30, rad)):
        c.scale = (max(s, 1e-4) * 2.5, max(s, 1e-4), max(s, 1e-4)); c.keyframe_insert("scale", frame=f)
    set_interp(c, "LINEAR")
    bm_ = o.modifiers.new("hole", "BOOLEAN"); bm_.object = c; bm_.solver = "EXACT"
    if kind == "Insulation":   # boolean before the fluff displacement
        bpy.context.view_layer.objects.active = o
        while o.modifiers[0].name != "hole": bpy.ops.object.modifier_move_up(modifier="hole")
    print("HOLE", o.name, kind, "frame", fhit)
F_SIDING = x_at_frame(WALL_OUT); F_DRY = x_at_frame(WALL_IN - 0.0125)
print("F_SIDING", F_SIDING, "F_DRY", F_DRY)
# ---------------- debris: siding splinters + paint chips (out and in), sheathing chips, drywall chunks + gypsum dust (into the room)
M_SPL = mat("M_Splinter", (0.72, 0.6, 0.45), 0.7); M_PAINTCHIP = mat("M_PaintChip", (0.62, 0.70, 0.66), 0.5)
M_GYPCH = mat("M_GypChunk", (0.9, 0.89, 0.86), 0.9); M_DUSTP = mat("M_DustGrain", (0.85, 0.84, 0.8), 0.95)
slow = 1.0 / 40.0   # story-time factor inside the wall
for k in range(34):
    m = M_SPL if k % 3 else M_PAINTCHIP
    o = shard("Splinter", (random.uniform(0.002, 0.012), 0.0012, 0.0012) if m is M_SPL else (0.003, 0.003, 0.0006), m, 100 + k)
    out = k < 22
    dirn = (-D * random.uniform(0.6, 1.0) if out else D * random.uniform(0.3, 0.8)) + SV * random.uniform(-0.8, 0.8) + Vector((0, 0, random.uniform(-0.4, 0.9)))
    p0 = on_line(WALL_OUT + 0.005) + SV * random.uniform(-0.01, 0.01) + Vector((0, 0, random.uniform(-0.01, 0.01)))
    ballistic(o, F_SIDING + random.randint(0, 6), F_SIDING + 200, p0, dirn.normalized() * random.uniform(0.0008, 0.0022), Vector((0, 0, -0.0000045)),
              Vector((random.uniform(-0.05, 0.05), random.uniform(-0.05, 0.05), random.uniform(-0.05, 0.05))), step=3)
for k in range(46):
    big = k < 14
    o = shard("GypChunk", (0.004, 0.004, 0.003) if big else (0.0012, 0.0012, 0.0012), M_GYPCH, 300 + k)
    dirn = D * random.uniform(0.7, 1.0) + SV * random.uniform(-0.7, 0.7) + Vector((0, 0, random.uniform(-0.5, 0.8)))
    p0 = on_line(WALL_IN + 0.003) + SV * random.uniform(-0.012, 0.012) + Vector((0, 0, random.uniform(-0.012, 0.012)))
    ballistic(o, F_DRY + random.randint(0, 10), 700, p0, dirn.normalized() * random.uniform(0.0007, 0.0018), Vector((0, 0, -0.0000035)),
              Vector((random.uniform(-0.04, 0.04),) * 3), step=4)
# gypsum dust cone: soft volume puffs that grow and thin out
M_PUFF = bpy.data.materials.new("M_DustPuff"); M_PUFF.use_nodes = True; nt = M_PUFF.node_tree
nt.nodes.remove(nt.nodes["Principled BSDF"]); vol = nt.nodes.new("ShaderNodeVolumePrincipled"); vol.name = "VOL"
vol.inputs["Color"].default_value = (0.9, 0.88, 0.84, 1); vol.inputs["Density"].default_value = 12.0
nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 60; mm = nt.nodes.new("ShaderNodeMath"); mm.operation = "MULTIPLY"; mm.inputs[1].default_value = 30.0
gr = nt.nodes.new("ShaderNodeTexGradient"); gr.gradient_type = "SPHERICAL"; tc = nt.nodes.new("ShaderNodeTexCoord")
nt.links.new(tc.outputs["Object"], gr.inputs[0]); m2 = nt.nodes.new("ShaderNodeMath"); m2.operation = "MULTIPLY"
nt.links.new(gr.outputs[1], m2.inputs[0]); nt.links.new(nz.outputs[0], m2.inputs[1]); nt.links.new(m2.outputs[0], mm.inputs[0]); nt.links.new(mm.outputs[0], vol.inputs["Density"])
nt.links.new(vol.outputs[0], nt.nodes["Material Output"].inputs["Volume"])
for k, (side, f0, dist, rr) in enumerate([(+1, F_DRY, 0.06, 0.03), (+1, F_DRY + 8, 0.14, 0.05), (+1, F_DRY + 20, 0.25, 0.07), (-1, F_SIDING, 0.05, 0.03), (-1, F_SIDING + 12, 0.12, 0.05)]):
    o = jag_sphere("DustPuff", 1.0, 0.15, seed=50 + k); o.data.materials.append(M_PUFF); o.visible_shadow = False
    base = on_line(WALL_IN if side > 0 else WALL_OUT)
    o.scale = (0.001,) * 3; o.keyframe_insert("scale", frame=f0 - 1); o.location = base; o.keyframe_insert("location", frame=f0 - 1)
    o.scale = (rr,) * 3; o.location = base + D * side * dist + Vector((0, 0, 0.01)); o.keyframe_insert("scale", frame=f0 + 160); o.keyframe_insert("location", frame=f0 + 160)
    o.scale = (rr * 1.8,) * 3; o.location = base + D * side * dist * 1.6 + Vector((0, 0, 0.05)); o.keyframe_insert("scale", frame=f0 + 420); o.keyframe_insert("location", frame=f0 + 420)
    o.scale = (0.001,) * 3; o.keyframe_insert("scale", frame=f0 + 520)
# light leaking through the hole into the dark cavity (beat 2)
lk = bpy.data.lights.new("HoleLeak", "SPOT"); lk.energy = 0.0; lk.spot_size = R_(40); lk.color = (1.0, 0.75, 0.5); lk.shadow_soft_size = 0.002
lko = bpy.data.objects.new("HoleLeak", lk); C_FX.objects.link(lko); lko.location = on_line(WALL_OUT - 0.04)
lko.rotation_euler = D.to_track_quat("-Z", "Y").to_euler()
for f, e in ((1, 0), (F_SIDING, 0), (F_SIDING + 10, 2.5), (F_DRY + 30, 2.5), (F_DRY + 80, 0.6)):
    lk.energy = e; lk.keyframe_insert("energy", frame=f)
cav = bpy.data.lights.new("CavityFill", "POINT"); cav.energy = 0.0; cav.color = (1.0, 0.8, 0.6); cav.shadow_soft_size = 0.01
cvo = bpy.data.objects.new("CavityFill", cav); C_FX.objects.link(cvo); cvo.location = on_line(-0.075) + Vector((0, 0, 0.12))
for f, e in ((1, 0), (F_SIDING, 0), (F_SIDING + 20, 0.25), (F_DRY + 10, 0.25), (F_DRY + 40, 0.0)):
    cav.energy = e; cav.keyframe_insert("energy", frame=f)

# ---------------- tumbler impact
body = bpy.data.objects["Tumbler_Body"]; dk = body.data.shape_keys.key_blocks["Dent"]
for f, v in ((1, 0), (F_IMPACT - 1, 0), (F_IMPACT + 10, 0.75), (F_IMPACT + 26, 1.08), (F_IMPACT + 60, 1.0)):
    dk.value = v; dk.keyframe_insert("value", frame=f)
chipv = bpy.data.materials["M_Powdercoat"].node_tree.nodes["CHIP"].outputs[0]
for f, v in ((1, 0.0), (F_IMPACT, 0.0), (F_IMPACT + 12, 1.0)):
    chipv.default_value = v; chipv.keyframe_insert("default_value", frame=f)
# cup skids 1.5 cm and rocks (slow-mo), settles
CUP.rotation_mode = "XYZ"; c0 = CUP.location.copy(); r0 = CUP.rotation_euler.copy()
for f, dp, tilt in ((1, 0, 0), (F_IMPACT, 0, 0), (F_IMPACT + 60, 0.008, 3.0), (F_IMPACT + 160, 0.015, 1.5), (1285, 0.016, 0.0), (1300, 0.016, -0.8), (1330, 0.016, 0.0)):
    CUP.location = c0 + DXY * dp; CUP.keyframe_insert("location", frame=f)
    ax = Vector((-DXY.y, DXY.x, 0))
    CUP.rotation_euler = (Matrix.Rotation(R_(tilt), 3, ax) @ r0.to_matrix()).to_euler(); CUP.keyframe_insert("rotation_euler", frame=f)
# sparks: emissive streaks thrown off the contact point in a cone back toward the shooter side, slow-mo ballistic
M_SPARK = mat("M_Spark", (1.0, 0.6, 0.2), 0.5, emit=(1.0, 0.5, 0.12), estr=9)
nrm = -DXY
for k in range(70):
    me = bpy.data.meshes.new("Spark"); bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=True, segments=6, radius1=0.00035, radius2=0.00005, depth=random.uniform(0.006, 0.02))
    bm.to_mesh(me); bm.free(); o = bpy.data.objects.new("Spark", me); C_FX.objects.link(o); me.materials.append(M_SPARK); o.visible_shadow = False
    o.rotation_mode = "QUATERNION"
    dirn = (nrm * random.uniform(0.2, 1.0) + SV * random.uniform(-1.2, 1.2) + Vector((0, 0, random.uniform(-0.6, 1.3)))).normalized()
    v = dirn * random.uniform(0.0006, 0.0022); g = Vector((0, 0, -0.0000025)); f0 = F_IMPACT + random.randint(0, 8); life = random.randint(90, 190)
    o.scale = (0, 0, 0); o.keyframe_insert("scale", frame=f0 - 1)
    for f in list(range(f0, f0 + life, 3)) + [f0 + life]:
        t = f - f0; p = IMP + v * t + 0.5 * g * t * t; vel = v + g * t
        o.location = p; o.keyframe_insert("location", frame=f)
        o.rotation_quaternion = vel.to_track_quat("Z", "Y"); o.keyframe_insert("rotation_quaternion", frame=f)
        fade = 1.0 - (t / life) ** 2
        o.scale = (1, 1, 1.0 + 1.5 * min(1, vel.length / 0.002)) if fade > 0.05 else (0, 0, 0); o.scale = Vector(o.scale) * max(fade, 0.0)
        o.keyframe_insert("scale", frame=f)
    o.scale = (0, 0, 0); o.keyframe_insert("scale", frame=f0 + life + 1)
fl = bpy.data.lights.new("SparkFlash", "POINT"); fl.color = (1.0, 0.6, 0.25); fl.shadow_soft_size = 0.005
flo = bpy.data.objects.new("SparkFlash", fl); C_FX.objects.link(flo); flo.location = IMP - DXY * 0.02
for f, e in ((1, 0), (F_IMPACT - 1, 0), (F_IMPACT + 2, 1.2), (F_IMPACT + 30, 0.6), (F_IMPACT + 120, 0.4), (F_IMPACT + 200, 0.0)):
    fl.energy = e; fl.keyframe_insert("energy", frame=f)
# condensation droplets shaken off the steel at impact
M_DROP = bpy.data.materials["M_Drop"]
for k in range(24):
    o = jag_sphere("FlyDrop", 1.0, 0.05, seed=700 + k); o.data.materials.append(M_DROP); o.visible_shadow = False
    s = random.uniform(0.0007, 0.0018); o.scale = (s,) * 3
    dirn = (nrm * random.uniform(0.3, 1.0) + SV * random.uniform(-1, 1) + Vector((0, 0, random.uniform(-0.2, 1.0)))).normalized()
    ballistic(o, F_IMPACT + random.randint(2, 14), F_IMPACT + 300, IMP + SV * random.uniform(-0.02, 0.02) + Vector((0, 0, random.uniform(-0.03, 0.03))),
              dirn * random.uniform(0.0002, 0.0007), Vector((0, 0, -0.000003)), Vector((0, 0, 0)), scale0=s, step=4, settle_z=TOP + s)
# ripples on the water surface (Wave modifier, radial from the impact side), ice bobbing, straw tremble
ws = bpy.data.objects["Tumbler_WaterSurf"]
wv = ws.modifiers.new("ripple", "WAVE"); wv.use_x = wv.use_y = True; wv.use_normal = False; wv.height = 0.0035; wv.width = 0.008; wv.narrowness = 1.2
wv.speed = 0.0004; wv.time_offset = F_IMPACT; wv.lifetime = 0; wv.damping_time = 300
loc_imp = (CUP.matrix_world.inverted() @ IMP); wv.start_position_x, wv.start_position_y = loc_imp.x * 0.9, loc_imp.y * 0.9
wv.falloff_radius = 0.0
for i, o in enumerate([bpy.data.objects["Tumbler_Ice%d" % k] for k in range(6)]):
    p0 = o.location.copy(); e0 = o.rotation_euler.copy()
    for f in (1, F_IMPACT, F_IMPACT + 40, F_IMPACT + 110, F_IMPACT + 200, 1285, 1330, 1420):
        a = 0.0 if f <= F_IMPACT else (1.0 if f < 1285 else 0.3)
        o.location = p0 + Vector((math.sin(f * 0.05 + i) * 0.003 * a, math.cos(f * 0.04 + i) * 0.003 * a, math.sin(f * 0.07 + 2 * i) * 0.004 * a))
        o.rotation_euler = (e0.x + 0.2 * a * math.sin(f * 0.03 + i), e0.y + 0.15 * a * math.cos(f * 0.02 + i), e0.z)
        o.keyframe_insert("location", frame=f); o.keyframe_insert("rotation_euler", frame=f)
    # tiny pre-impact clink: ice settles once during beat 5
    o.location = p0 + Vector((0, 0, -0.002 * (i % 2))); o.keyframe_insert("location", frame=760 + 12 * i)
st = bpy.data.objects["Tumbler_Straw"]; st0 = st.rotation_euler.copy()
for f in range(F_IMPACT, 1330, 6):
    a = math.exp(-(f - F_IMPACT) / 90.0) * R_(3.0)
    st.rotation_euler = (st0.x + a * math.sin(f * 0.35), st0.y + a * math.cos(f * 0.29), st0.z); st.keyframe_insert("rotation_euler", frame=f)
st.rotation_euler = st0; st.keyframe_insert("rotation_euler", frame=1); st.keyframe_insert("rotation_euler", frame=F_IMPACT - 1)
# x-ray: the steel turns to a cyan ghost while the camera dives in to see the water ripple
mx = bpy.data.materials["M_Powdercoat"].node_tree.nodes["XRAY"].inputs[0]
for f, v in ((1, 0), (1035, 0), (1070, 0.88), (1150, 0.88), (1185, 0)):
    mx.default_value = v; mx.keyframe_insert("default_value", frame=f)
for nm in ("M_LidPlastic", "M_Steel"):
    pass
# lid goes ghost too (so the camera can look down into the water)
ml = bpy.data.materials["M_LidPlastic"]; nt = ml.node_tree; b = nt.nodes["Principled BSDF"]
tr = nt.nodes.new("ShaderNodeBsdfTransparent"); ms = nt.nodes.new("ShaderNodeMixShader"); ms.name = "XRAY"
nt.links.new(b.outputs[0], ms.inputs[1]); nt.links.new(tr.outputs[0], ms.inputs[2]); nt.links.new(ms.outputs[0], nt.nodes["Material Output"].inputs[0])
for f, v in ((1, 0), (1035, 0), (1070, 0.9), (1150, 0.9), (1185, 0)):
    ms.inputs[0].default_value = v; ms.inputs[0].keyframe_insert("default_value", frame=f)
# condensation: a few beads run down during beat 5
drops = sorted([o for o in bpy.data.objects if o.name.startswith("Drop")], key=lambda o: -o.location.z)[:14]
for i, o in enumerate(drops):
    p0 = o.location.copy(); f0 = 620 + i * 23; zz = max(0.03, p0.z - random.uniform(0.03, 0.08))
    a = math.atan2(p0.y, p0.x); rr = r_out(zz) + 0.0001
    o.keyframe_insert("location", frame=f0)
    o.location = (rr * math.cos(a), rr * math.sin(a), zz); o.keyframe_insert("location", frame=f0 + 150)
    o.scale = Vector(o.scale) * 1.3; o.keyframe_insert("scale", frame=f0 + 150)

# ---------------- room life: candle flicker, picture frame rattle, dust motes in the lamp light, curtains breathing
cf = bpy.data.objects["CandleFlame"]; cl = bpy.data.lights["CandleLight"]
for f in range(1, END + 1, 4):
    rate = 0.08 if 271 < f < 1285 else 0.6
    cf.scale = (1 + 0.08 * math.sin(f * rate * 1.3), 1 + 0.08 * math.cos(f * rate), 1 + 0.18 * math.sin(f * rate * 0.7 + 1)); cf.keyframe_insert("scale", frame=f)
    cl.energy = 4 + 1.2 * math.sin(f * rate * 0.9); cl.keyframe_insert("energy", frame=f)
for o in bpy.data.objects:
    if o.name.startswith("hanging_picture_frame_02_root"):
        o.rotation_mode = "XYZ"; r0 = o.rotation_euler.copy()
        for f in range(1, END + 1, 6):
            a = 0.0
            if f > F_DRY: a = R_(1.6) * math.exp(-(f - F_DRY) / 400.0) * math.sin((f - F_DRY) * 0.05)
            if f > 1285: a += R_(1.0) * math.exp(-(f - 1285) / 60.0) * math.sin((f - 1285) * 0.5)
            o.rotation_euler = (r0.x, r0.y + a, r0.z); o.keyframe_insert("rotation_euler", frame=f)
M_MOTE = mat("M_Mote", (1, 0.9, 0.75), 0.5, emit=(1.0, 0.85, 0.6), estr=3.0)
for k in range(90):
    o = jag_sphere("DustMote", 1.0, 0.1, seed=900 + k); o.data.materials.append(M_MOTE); o.visible_shadow = False
    s = random.uniform(0.0003, 0.0009); o.scale = (s,) * 3
    p0 = Vector((random.uniform(2.6, 4.9), random.uniform(-0.9, 0.6), random.uniform(0.85, 1.6)))
    for f in (1, 400, 800, 1200, 1530):
        sp = 0.00004 if 271 < f < 1285 else 0.0004
        o.location = p0 + Vector((math.sin(f * 0.002 + k) * 0.05, math.cos(f * 0.0017 + k) * 0.05, -f * 0.00002 + math.sin(f * 0.003 + k) * 0.03))
        o.keyframe_insert("location", frame=f)
# exterior: leaves blowing across the lawn in the dusk wind (beat 1)
M_LEAF = mat("M_Leaf", (0.45, 0.25, 0.08), 0.7)
for k in range(26):
    o = shard("Leaf", (0.03, 0.022, 0.0008), M_LEAF, 1200 + k, coll=bpy.data.collections["Exterior"])
    p0 = Vector((random.uniform(-9, -2), random.uniform(-6, 2), GROUND_Z + random.uniform(0.05, 1.2)))
    ballistic(o, 1, 160, p0, Vector((random.uniform(0.005, 0.015), random.uniform(0.01, 0.03), 0.0)), Vector((0, 0, -0.000004)),
              Vector((0.05, 0.08, 0.03)), step=4, settle_z=GROUND_Z + 0.01, hide_before=False)

# birds startle off the neighbour's roof ridge at the shot (beat 1): simple flapping V shapes
M_BIRD = mat("M_Bird", (0.05, 0.05, 0.06), 0.6)
for k in range(9):
    me = bpy.data.meshes.new("Bird"); me.from_pydata([(0, 0, 0), (-0.18, 0.05, 0.0), (0.18, 0.05, 0.0), (0, -0.08, 0)], [], [(0, 1, 3), (0, 3, 2)])
    o = bpy.data.objects.new("Bird", me); bpy.data.collections["Exterior"].objects.link(o); me.materials.append(M_BIRD)
    sk = o.shape_key_add(name="Basis"); up = o.shape_key_add(name="WingsUp")
    up.data[1].co = (-0.13, 0.05, 0.12); up.data[2].co = (0.13, 0.05, 0.12)
    p0 = Vector((random.uniform(3.5, 5.5), random.uniform(-3.5, 1.5), 5.18 + random.uniform(0, 0.05)))
    v = Vector((random.uniform(-0.05, 0.02), random.uniform(0.02, 0.06), random.uniform(0.02, 0.04)))
    for f in range(1, 200, 4):
        t = max(0, f - 25 - k * 2)
        o.location = p0 + v * t; o.keyframe_insert("location", frame=f)
        o.rotation_euler = (0, 0, math.atan2(v.y, v.x) - math.pi / 2); o.keyframe_insert("rotation_euler", frame=f)
        up.value = 0.5 + 0.5 * math.sin(t * 0.9 + k) if t > 0 else 0.0; up.keyframe_insert("value", frame=f)
# street lamps flicker on at dusk during beat 1 (light change outside)
for o in bpy.data.objects:
    if o.name.startswith("StreetLamp") and o.type == "LIGHT":
        for f, e in ((1, 0), (14, 600), (18, 80), (24, 900), (30, 300), (40, 900)):
            o.data.energy = e; o.data.keyframe_insert("energy", frame=f)
m = bpy.data.materials.get("M_StreetGlow")
if m:
    es = m.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]
    for f, e in ((1, 0.5), (14, 9), (18, 1.5), (24, 12), (30, 4), (40, 12)):
        es.default_value = e; es.keyframe_insert("default_value", frame=f)
