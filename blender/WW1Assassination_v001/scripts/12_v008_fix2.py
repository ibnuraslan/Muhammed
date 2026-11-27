# v008 fixes, part 2 (exec'd by 12_v008.py after 12_v008_fix.py)
import bpy, bmesh, math, random
from mathutils import Vector, Matrix, Quaternion
random.seed(8)
exec(open(os.path.join(HERE, "..", "..", "pipeline", "hand_poses.py")).read())

KEEP_EVAL = {"Car1_FoldedRoof", "Car1_Body"}
def fset(f): sc.frame_set(int(f))
def mesh_hidden_eval(on):
    """skip mesh evaluation while sampling bones (speed)"""
    global _mh
    if on:
        _mh = [o for o in O if o.type == 'MESH' and not o.hide_viewport and o.name not in KEEP_EVAL]
        for o in _mh: o.hide_viewport = True
    else:
        for o in _mh: o.hide_viewport = False
def key_vis(o, pairs):
    """pairs: [(frame, hidden_bool)] constant keys on hide_render + hide_viewport"""
    drop_curves(o, lambda f: f.data_path in ("hide_render", "hide_viewport"))
    for f, h in pairs:
        o.hide_render = h; o.hide_viewport = h
        o.keyframe_insert("hide_render", frame=f); o.keyframe_insert("hide_viewport", frame=f)
    for f in fcurves(o):
        if f.data_path in ("hide_render", "hide_viewport"):
            for k in f.keyframe_points: k.interpolation = 'CONSTANT'
def flat_mat(name, col, emit=None, strength=0.0, rough=0.6, metal=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    p = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    p.inputs["Base Color"].default_value = (*col, 1); p.inputs["Roughness"].default_value = rough; p.inputs["Metallic"].default_value = metal
    if emit:
        p.inputs["Emission Color"].default_value = (*emit, 1); p.inputs["Emission Strength"].default_value = strength
    return m

# ---------------------------------------------------------------- 7. "he wasn't the first": the two would-be assassins stand at their spot during 342-472
# (the v007 world plays its rewind there; their own animation 451-581 is copied in at 1x so they are present and acting)
for n in ("NerveA", "NerveB"):
    for f in fcurves(O[n]):
        kp = f.keyframe_points
        v341, v473 = f.evaluate(341), f.evaluate(473)
        smp = [(fr, f.evaluate(fr + 109)) for fr in list(range(342, 472, 2)) + [472]]
        for k in [k for k in kp if 341 <= k.co[0] <= 473][::-1]: kp.remove(k)
        for fr, v in [(341, v341)] + smp + [(473, v473)]: kp.insert(fr, v, options={'FAST'})
        f.update()
mesh_hidden_eval(True)
near = set()
for fr in range(342, 473, 10):
    fset(fr)
    for a_ in O:
        if a_.type == 'ARMATURE' and a_.name.startswith("Crowd"):
            h = a_.matrix_world @ a_.pose.bones["root"].head
            if 87.0 < h.x < 96.5 and 3.0 < h.y < 10.0: near.add(a_.name)
mesh_hidden_eval(False)
for n_ in near:
    for ch in [c for c in O if c.parent and c.parent.name == n_]:
        vis0 = [(f.evaluate(341), f.evaluate(473)) for f in fcurves(ch) if f.data_path == "hide_render"]
        h0, h1 = vis0[0] if vis0 else (ch.hide_render, ch.hide_render)
        key_vis(ch, [(1, bool(h0)), (342, True), (473, bool(h1))] + ([(1433, True), (1681, False)] if vis0 else []))
print("NERVES present 342-472; extras cleared from the shot:", sorted(near))

# ---------------------------------------------------------------- 8. map swap on the cut (1433) and no cloud layer (items 22, 23)
SW_OLD, SW_NEW = 1474, 1433
for o in O:
    for f in fcurves(o):
        if f.data_path in ("hide_render", "hide_viewport"):
            for k in f.keyframe_points:
                if int(round(k.co[0])) == SW_OLD: k.co[0] = SW_NEW; k.handle_left[0] = SW_NEW; k.handle_right[0] = SW_NEW
            f.update()
for idb in list(bpy.data.lights) + [sc.world]:
    for f in fcurves(idb):
        for k in f.keyframe_points:
            if SW_OLD - 2 <= k.co[0] <= SW_OLD + 2: k.co[0] -= (SW_OLD - SW_NEW); k.handle_left[0] -= (SW_OLD - SW_NEW); k.handle_right[0] -= (SW_OLD - SW_NEW)
        f.update()
hide_always(O["CloudLayer"])
print("MAP swap at", SW_NEW)

# ---------------------------------------------------------------- 9. following car: own paint copies, charred after the blast; wheels green too
fb_curves = [f for f in fcurves(O["BlastFireball"]) if f.data_path == "scale"]
FB = next(f for f in range(560, 1100) if fb_curves[0].evaluate(f) > 0.05)
print("BLAST frame", FB)
char_nodes = []
car1_mats = {}
for o in O:
    if o.name.startswith("Car1_") and o.type == 'MESH':
        for s in o.material_slots:
            if s.material: car1_mats[s.material.name.replace("Car1_", "").rsplit(".", 1)[0]] = s.material
for o in [x for x in O if x.name.startswith("Car2_") and x.type == 'MESH']:
    for s in o.material_slots:
        m = s.material
        if not m: continue
        base = m.name.replace("Car2_", "").replace("Car1_", "").rsplit(".", 1)[0]
        srcm = car1_mats.get(base, m)
        c = srcm.copy(); c.name = "Car2v8_" + base; s.material = c
        p = principled(c)
        if p and not p.inputs["Base Color"].is_linked:
            mix = c.node_tree.nodes.new("ShaderNodeMix"); mix.data_type = 'RGBA'; mix.blend_type = 'MULTIPLY'
            mix.inputs["A"].default_value = p.inputs["Base Color"].default_value[:]
            mix.inputs["B"].default_value = (0.08, 0.07, 0.06, 1)
            c.node_tree.links.new(mix.outputs["Result"], p.inputs["Base Color"])
            fac = mix.inputs["Factor"]
            fac.default_value = 0.0; fac.keyframe_insert("default_value", frame=FB)
            fac.default_value = 0.9; fac.keyframe_insert("default_value", frame=FB + 4)
# the blast heaves the car: lift and tilt, then it settles nose-down on a blown front wheel
sw = O["Car2_Sway"]; sw.rotation_mode = 'XYZ'
base_loc = sw.location.copy(); base_rot = sw.rotation_euler.copy()
for df, dz, rx, ry in ((0, 0, 0, 0), (3, 0.35, 0.10, 0.05), (9, 0.12, 0.05, 0.02), (14, -0.06, -0.06, 0.03), (20, -0.08, -0.05, 0.03)):
    sw.location = base_loc + Vector((0, 0, dz)); sw.rotation_euler = (base_rot.x + rx, base_rot.y + ry, base_rot.z)
    sw.keyframe_insert("location", frame=FB + df); sw.keyframe_insert("rotation_euler", frame=FB + df)
print("CAR2 own paint, charred + heaved at", FB)

# ---------------------------------------------------------------- 10. explosion: real fireball and rising smoke puffs, no flat dome, no smoke planes (item 17)
for n in ("BlastFireball", "BlastDustRing") + tuple("BlastSmoke_%d" % i for i in range(5)): hide_always(O[n])
E = Vector((84.0, 1.5, 0.35))
tex = bpy.data.textures.new("PuffNoise", 'CLOUDS'); tex.noise_scale = 0.45; tex.noise_depth = 2
fire_m = bpy.data.materials.new("FireballV8"); fire_m.use_nodes = True
nt = fire_m.node_tree; nt.nodes.clear()
out = nt.nodes.new("ShaderNodeOutputMaterial"); em = nt.nodes.new("ShaderNodeEmission"); pr = nt.nodes.new("ShaderNodeBsdfPrincipled"); mx = nt.nodes.new("ShaderNodeMixShader")
em.inputs["Strength"].default_value = 3.0
pr.inputs["Base Color"].default_value = (0.09, 0.085, 0.08, 1); pr.inputs["Roughness"].default_value = 1.0
nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 3.0; nz.inputs["Detail"].default_value = 6.0
ramp = nt.nodes.new("ShaderNodeValToRGB"); cr = ramp.color_ramp
cr.elements[0].position = 0.35; cr.elements[0].color = (0.55, 0.03, 0.0, 1)
cr.elements[1].position = 0.7; cr.elements[1].color = (1.0, 0.75, 0.15, 1)
nt.links.new(nz.outputs["Fac"], ramp.inputs[0]); nt.links.new(ramp.outputs[0], em.inputs["Color"])
ramp2 = nt.nodes.new("ShaderNodeValToRGB"); c2 = ramp2.color_ramp
c2.elements[0].position = 0.3; c2.elements[0].color = (0.03, 0.028, 0.026, 1); c2.elements[1].position = 0.75; c2.elements[1].color = (0.22, 0.21, 0.2, 1)
nt.links.new(nz.outputs["Fac"], ramp2.inputs[0]); nt.links.new(ramp2.outputs[0], pr.inputs["Base Color"])
nt.links.new(em.outputs[0], mx.inputs[1]); nt.links.new(pr.outputs[0], mx.inputs[2]); nt.links.new(mx.outputs[0], out.inputs[0])
mf = mx.inputs[0]
for f, v in ((FB, 0.0), (FB + 14, 0.1), (FB + 26, 0.8), (FB + 36, 1.0)):
    mf.default_value = v; mf.keyframe_insert("default_value", frame=f)
smoke_m = flat_mat("SmokePuffV8", (0.16, 0.155, 0.15), rough=1.0)
_n = smoke_m.node_tree; _p = principled(smoke_m)
_nz = _n.nodes.new("ShaderNodeTexNoise"); _nz.inputs["Scale"].default_value = 2.5; _nz.inputs["Detail"].default_value = 6.0
_r = _n.nodes.new("ShaderNodeValToRGB"); _c = _r.color_ramp
_c.elements[0].position = 0.3; _c.elements[0].color = (0.05, 0.048, 0.045, 1); _c.elements[1].position = 0.75; _c.elements[1].color = (0.3, 0.29, 0.28, 1)
_n.links.new(_nz.outputs["Fac"], _r.inputs[0]); _n.links.new(_r.outputs[0], _p.inputs["Base Color"])
def puff(name, mat, pos, r0, r1, f0, f1, rise, f_hide):
    bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=3, radius=1.0)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = True
    o = bpy.data.objects.new(name, me); sc.collection.objects.link(o); o.data.materials.append(mat)
    d = o.modifiers.new("Puff", 'DISPLACE'); d.texture = tex; d.strength = 0.6; d.texture_coords = 'OBJECT'
    o.visible_shadow = False
    for f, u in ((f0, 0.0), (f0 + max(2, (f1 - f0) // 5), 0.55), (f1, 1.0)):
        r = r0 + (r1 - r0) * u if f > f0 else 0.02
        o.location = pos + Vector((0, 0, rise * u)); o.scale = (r, r, r * 0.9)
        o.keyframe_insert("location", frame=f); o.keyframe_insert("scale", frame=f)
    key_vis(o, [(1, True), (f0, False), (f_hide, True)])
    return o
for i in range(6):   # fireball lobes
    off = Vector((random.uniform(-0.6, 0.6), random.uniform(-0.5, 0.5), random.uniform(0.0, 0.5)))
    puff("FireLobe_%d" % i, fire_m, E + off, 0.05, random.uniform(0.7, 1.1), FB, FB + 40, random.uniform(0.8, 1.6), FB + 70)
for i in range(12):  # smoke that rises and spreads, attached to the car (starts at the car, never a floating plane)
    off = Vector((random.uniform(-1.0, 1.0), random.uniform(-0.8, 0.8), random.uniform(0.2, 0.9)))
    f0 = FB + 6 + i * 3
    puff("SmokePuff_%02d" % i, smoke_m, E + off, 0.1, random.uniform(0.7, 1.2), f0, f0 + 110, random.uniform(2.0, 3.8), 1433)
bl = O["BlastLight"].data
for f in fcurves(bl):
    if f.data_path == "energy":
        for k in f.keyframe_points: k.co[1] *= 0.5; k.handle_left[1] *= 0.5; k.handle_right[1] *= 0.5
print("BLAST fireball + smoke puffs")

# ---------------------------------------------------------------- 11. the bomb: in the hand, arc onto the folded roof, bounce onto the road, roll under the car behind
bomb = O["Bomb"]
bomb.scale = (1.35, 1.35, 1.35)
for c in list(bomb.constraints): bomb.constraints.remove(c)
drop_curves(bomb, lambda f: True)
bomb.parent = None
BR = O["Bomber"]
mesh_hidden_eval(True)
def palm(f):
    fset(f); pb = BR.pose.bones
    w = BR.matrix_world @ pb["wrist.R"].head; m = BR.matrix_world @ pb["finger3-1.R"].head
    return w.lerp(m, 0.75)
T0, TREL = 600, 645
hand = {f: palm(f) for f in range(T0, TREL + 1)}
# throw release: the frame where the hand is highest and forward; keep the bomb in the palm until then
TREL = max(range(625, TREL + 1), key=lambda f: hand[f].z - 0.3 * hand[f].y)
THIT = TREL + 22
fset(THIT); roof = O["Car1_FoldedRoof"]
rv = [roof.matrix_world @ v.co for v in roof.data.vertices]
RH = sum(rv, Vector()) / len(rv); RH.z = max(v.z for v in rv) + 0.06
car_v = (O["Car1"].matrix_world.translation.copy()); fset(THIT + 6); car_v = (O["Car1"].matrix_world.translation - car_v) / 6.0
P0 = hand[TREL]; dt = (THIT - TREL) / 60.0; g = Vector((0, 0, -9.81))
V0 = (RH - P0 - 0.5 * g * dt * dt) / dt
REST = Vector((83.6, 1.4, 0.055))
LAND = Vector((RH.x + 1.1, 1.3, 0.055)); TLAND = THIT + 18
TREST = TLAND + 34
for f in range(T0, TREL + 1):
    bomb.location = hand[f]; bomb.keyframe_insert("location", frame=f)
for f in range(TREL + 1, THIT + 1):
    t = (f - TREL) / 60.0
    bomb.location = P0 + V0 * t + 0.5 * g * t * t; bomb.keyframe_insert("location", frame=f)
dt2 = (TLAND - THIT) / 60.0; V1 = (LAND - RH - 0.5 * g * dt2 * dt2) / dt2
for f in range(THIT + 1, TLAND + 1):
    t = (f - THIT) / 60.0
    bomb.location = RH + V1 * t + 0.5 * g * t * t; bomb.keyframe_insert("location", frame=f)
# two small hops then a roll to rest where the following car stops
hops = [(LAND, LAND.lerp(REST, 0.45), 0.22, 12), (LAND.lerp(REST, 0.45), LAND.lerp(REST, 0.75), 0.08, 8)]
f = TLAND
for a, b, hgt, n in hops:
    for i in range(1, n + 1):
        u = i / n; p = a.lerp(b, u); p.z = REST.z + 4 * hgt * u * (1 - u)
        f += 1; bomb.location = p; bomb.keyframe_insert("location", frame=f)
a = LAND.lerp(REST, 0.75); n = max(6, TREST - f)
for i in range(1, n + 1):
    u = 1 - (1 - i / n) ** 2; f += 1; bomb.location = a.lerp(REST, u); bomb.keyframe_insert("location", frame=f)
bomb.location = REST; bomb.keyframe_insert("location", frame=FB)
for fc in fcurves(bomb):
    for k in fc.keyframe_points: k.interpolation = 'LINEAR'
key_vis(bomb, [(1, True), (T0, False), (FB + 1, True)])
mesh_hidden_eval(False)
print("BOMB roofpt", tuple(round(x, 2) for x in RH), "hand", T0, "release", TREL, "roof", THIT, "land", TLAND, "rest", f, "blast", FB)

# ---------------------------------------------------------------- 12. pistol: dark gunmetal, grip seated in the palm (item 20)
pis = O["Pistol"]
for s in pis.material_slots:
    if s.material:
        m = s.material.copy(); m.name = "PistolMetalV8"; s.material = m
        p = principled(m)
        if p:
            for l in list(m.node_tree.links):
                if l.to_socket == p.inputs["Base Color"]: m.node_tree.links.remove(l)
            p.inputs["Base Color"].default_value = (0.035, 0.035, 0.04, 1); p.inputs["Metallic"].default_value = 0.8; p.inputs["Roughness"].default_value = 0.35
GN = O["Gunman"]
# grip from the hand bones every frame: grip centre in the fist, muzzle along the hand, top of the slide up (no Child Of offset)
for c in list(pis.constraints): pis.constraints.remove(c)
drop_curves(pis, lambda f: f.data_path in ("location", "rotation_euler", "rotation_quaternion", "scale"))
pis.parent = None
Sc = Vector((1, 1, 1))
lv = [v.co for v in pis.data.vertices]
zmin = min(v.z for v in lv); ymax = max(v.y for v in lv)
g_loc = sum([v for v in lv if v.z < zmin + 0.05 and v.y > ymax - 0.07], Vector()) / max(1, len([v for v in lv if v.z < zmin + 0.05 and v.y > ymax - 0.07]))
g_loc.z = zmin + 0.035
pis.rotation_mode = 'QUATERNION'
mesh_hidden_eval(True)
pb = GN.pose.bones; prevq = None
for f in list(range(1, 1827, 2)) + [1826]:
    fset(f); Mw = GN.matrix_world
    w = Mw @ pb["wrist.R"].head; m3 = Mw @ pb["finger3-1.R"].head
    i2 = Mw @ pb["finger2-1.R"].head; i5 = Mw @ pb["finger5-1.R"].head
    d = (m3 - w).normalized(); lat = (i2 - i5).normalized()
    up = lat.cross(d).normalized()
    if up.z < 0: up = -up
    Y = -d; Z = (up - Y * up.dot(Y)).normalized(); X = Y.cross(Z)
    R = Matrix((X, Y, Z)).transposed()
    palm = w.lerp(m3, 0.5) + up * 0.01
    q = R.to_quaternion()
    if prevq is not None and prevq.dot(q) < 0: q.negate()
    pis.rotation_quaternion = q; pis.location = palm - R @ g_loc
    pis.keyframe_insert("location", frame=f); pis.keyframe_insert("rotation_quaternion", frame=f); prevq = q
mesh_hidden_eval(False)
for s_ in O["MuzzleFlash"].material_slots:
    if s_.material:
        mm = s_.material.copy(); s_.material = mm; pp = principled(mm)
        if pp:
            pp.inputs["Base Color"].default_value = (1.0, 0.55, 0.1, 1); pp.inputs["Emission Color"].default_value = (1.0, 0.45, 0.05, 1); pp.inputs["Emission Strength"].default_value = 12.0
O["MuzzleFlash"].scale = (0.6, 0.6, 0.6)
print("PISTOL keyed to the hand every 2 frames")

# ---------------------------------------------------------------- 13. Duchess: legs inside the door, free hand on her lap, hat tilted up so the eyes read (items 1, 3, 4)
DU = O["Duchess"]
def shift_bone_keys(arm, bone, dv_rig, f1=10**9):
    b = arm.data.bones[bone]; dl = b.matrix_local.to_3x3().inverted() @ dv_rig
    for f in fcurves(arm):
        if f.data_path == f'pose.bones["{bone}"].location':
            for k in f.keyframe_points:
                if k.co[0] <= f1:
                    k.co[1] += dl[f.array_index]; k.handle_left[1] += dl[f.array_index]; k.handle_right[1] += dl[f.array_index]
            f.update()
for bn in ("IK_foot.L", "IK_foot.R", "Pole_knee.L", "Pole_knee.R"):
    shift_bone_keys(DU, bn, Vector((-0.09, 0, 0)))
for bn in ("IK_foot.L", "IK_foot.R", "Pole_knee.L", "Pole_knee.R"):   # the Archduke's outer knee came through the door (pale-blue "blade")
    shift_bone_keys(O["Archduke"], bn, Vector((0.11, 0, 0)))
# free (parasol) hand: rests on her lap until she is hit
drop_curves(DU, lambda f: any(f.data_path.startswith('pose.bones["%s' % x) for x in ("finger1-", "finger2-", "finger3-", "finger4-", "finger5-")) and f.data_path.split('"')[1].endswith(".L"))
for f in fcurves(DU):
    if f.data_path in ('pose.bones["IK_hand.L"].location', 'pose.bones["IK_hand.L"].rotation_quaternion'):
        for k in [k for k in f.keyframe_points if k.co[0] < 1262][::-1]: f.keyframe_points.remove(k)
SEATZ = sc.get("SEAT_R", 0.96)
mesh_hidden_eval(True)
for fr in (1, 1256):
    fset(fr); Ms = O["Car1_Sway"].matrix_world; R3 = Ms.to_3x3()
    place_hand(DU, "L", fr, Ms @ Vector((0.40, 0.58, SEATZ + 0.13)), (R3 @ Vector((0, 0.1, -1))).normalized(), (R3 @ Vector((-0.35, -1, -0.2))).normalized())
apply_pose(DU, "L", "relaxed", 1)
mesh_hidden_eval(False)
hat = O["WideHat"]
hat.rotation_mode = 'XYZ'; hat.rotation_euler.x -= math.radians(12); hat.location.z += 0.012
print("DUCHESS legs in, lap hand, hat tilted")

# ---------------------------------------------------------------- 14. map flags rise out of the map instead of popping; Serbian flag clear of the relief (item 24)
for n, dz in (("Flag_AH", 0.0), ("Flag_SRB", 1.3)):
    fl = O[n]
    sc_c = [f for f in fcurves(fl) if f.data_path == "scale"]
    if not sc_c: continue
    fon = next((f for f in range(SW_NEW, 1826) if sc_c[0].evaluate(f) > 0.5), SW_NEW + 20)
    S_full = max(k.co[1] for k in sc_c[0].keyframe_points)
    drop_curves(fl, lambda f: f.data_path in ("scale", "location"))
    base = fl.location.copy() + Vector((0, 0, dz))
    fl.scale = (S_full,) * 3
    for f, u in ((fon - 1, 0.0), (fon + 24, 1.0)):
        fl.location = base + Vector((0, 0, -S_full * 1.2 * (1 - u))); fl.keyframe_insert("location", frame=f)
    for fc in fcurves(fl):
        if fc.data_path == "location":
            for k in fc.keyframe_points: k.easing = 'EASE_OUT'
    print("FLAG", n, "rises from", fon)

# ---------------------------------------------------------------- 15. logo: DA KRAS FILMS on a sandwich board on the quay pavement (opening shot only)
LOGO = os.path.join(HERE, "..", "..", "assets", "brand", "DaKrasFilms_logo_dark.png")
img = bpy.data.images.load(LOGO); img.pack()
lm = bpy.data.materials.new("LogoBoardV8"); lm.use_nodes = True
nt = lm.node_tree; p = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
ti = nt.nodes.new("ShaderNodeTexImage"); ti.image = img
mixc = nt.nodes.new("ShaderNodeMix"); mixc.data_type = 'RGBA'
mixc.inputs["A"].default_value = (0.86, 0.82, 0.70, 1)
nt.links.new(ti.outputs["Color"], mixc.inputs["B"]); nt.links.new(ti.outputs["Alpha"], mixc.inputs["Factor"])
nt.links.new(mixc.outputs["Result"], p.inputs["Base Color"]); p.inputs["Roughness"].default_value = 0.7
wood = flat_mat("BoardWoodV8", (0.18, 0.1, 0.05), rough=0.8)
bm = bmesh.new()
W_, H_ = 1.17, 0.25
bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=0.5)
for v in bm.verts: v.co = Vector((v.co.x * W_, 0, v.co.y * H_ * 2))   # panel in XZ, logo aspect 2.34:1
uv = bm.loops.layers.uv.new()
for fa in bm.faces:
    for lo in fa.loops: lo[uv].uv = (lo.vert.co.x / W_ + 0.5, lo.vert.co.z / (2 * H_) + 0.5)
me = bpy.data.meshes.new("LogoPanel"); bm.to_mesh(me); bm.free(); me.materials.append(lm)
panel = bpy.data.objects.new("LogoBoard_Panel", me); sc.collection.objects.link(panel)
bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
me2 = bpy.data.meshes.new("LogoFrame"); bm.to_mesh(me2); bm.free(); me2.materials.append(wood)
frame_o = bpy.data.objects.new("LogoBoard_Frame", me2); sc.collection.objects.link(frame_o)
frame_o.scale = (W_ + 0.1, 0.05, 1.3); frame_o.location = (0, 0.03, 0.0)
frame_o.parent = panel
board = bpy.data.objects.new("LogoBoard", None); sc.collection.objects.link(board)
panel.parent = board; panel.location = (0, -0.006, 1.0)
frame_o.location = (0, 0.03, -0.35); frame_o.scale = (W_ + 0.12, 0.05, 1.3)
board.location = (9.7, 3.75, 0.0)
cam_p = Vector((1.5, -1.0, 1.7)); d = (cam_p - board.location); d.z = 0
board.rotation_euler = (0, 0, math.atan2(d.x, -d.y))
key_vis(panel, [(1, False), (1433, True), (END0, False)]); key_vis(frame_o, [(1, False), (1433, True), (END0, False)])
print("LOGO board placed")
