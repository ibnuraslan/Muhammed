# Part of 03_animate.py: bullet, window shatter, cup crack + fragments, cutaway, ricochet sparks, wall hit, ambient life.
random.seed(77)
HS_ROOT = bpy.data.objects["Headset"]
def hs_world(f):
    ev(f); return HS_ROOT.matrix_world.copy()
# time scale (real seconds per frame) for debris physics: slow motion until the bullet hits the wall
def ts(f):
    if f < 110: return 1 / 60 / 6
    if f < 1050: return 1 / 60 / 28
    return 1 / 60 / 28 + (1 / 60 - 1 / 60 / 28) * smooth((f - 1050) / 60)
G = Vector((-1.30, 0.08, 1.30))                     # where the bullet meets the glass
Hs_imp = hs_world(F_IMPACT)
HC = Vector(sc["HEAD_C_REST"]); XC1 = sc["XC1"]; R_OUT = sc["R_OUT"]
PI_LOC = Vector((XC1 - 0.014, R_OUT, 0.004))         # back rim of the LEFT cup (headset-local; rest +X = his left, +Y = back)
PI = Hs_imp @ PI_LOC
DIR = (PI - G).normalized()
L1 = (PI - G).length
print("BULLET dir", tuple(round(v, 3) for v in DIR), "L1", round(L1, 3), "PI", tuple(round(v, 3) for v in PI))
sc["PI"] = tuple(PI); sc["G"] = tuple(G)

# ------------------------------------------------------------------ bullet (plain copper projectile, no cartridge)
prof = [(0.0, 0.0), (0.0042, 0.0), (0.0045, 0.0015), (0.0045, 0.0085), (0.0040, 0.0115), (0.0028, 0.0140), (0.0012, 0.0158), (0.0, 0.0163)]
seg = 48; vs = []; fs_ = []
for i in range(seg):
    t = 2 * math.pi * i / seg
    for r_, z_ in prof: vs.append((math.cos(t) * r_, math.sin(t) * r_, z_ - 0.008))
n_ = len(prof)
for i in range(seg):
    j = (i + 1) % seg
    for k in range(n_ - 1): fs_.append((i * n_ + k, j * n_ + k, j * n_ + k + 1, i * n_ + k + 1))
BUL = from_pydata("Bullet", vs, fs_, mat("BulletCopper", (0.95, 0.56, 0.34), 0.22, metal=1.0), c="FX")
bm_ = bmesh.new(); bm_.from_mesh(BUL.data); bmesh.ops.remove_doubles(bm_, verts=bm_.verts, dist=1e-6); bm_.to_mesh(BUL.data); bm_.free()
BUL.data.shade_smooth() if hasattr(BUL.data, "shade_smooth") else None
for p in BUL.data.polygons: p.use_smooth = True
BUL.rotation_mode = 'QUATERNION'
# air-distortion trail (refractive, faint) behind the bullet in flight
trail = cyl("Bullet_Trail", 0.0042, 0.30, (0, 0, 0), mat("AirTrail", (1, 1, 1), 0.0, trans=1.0, ior=1.03), c="FX", r2=0.0005)
trail.data.transform(Matrix.Translation((0, 0, -0.158)) @ Matrix.Rotation(R_(180), 4, 'X'))
trail.parent = BUL
D_KEYS = [(1, L1 + 22.0), (110, L1 + 3.0), (133, L1), (160, L1 - 0.35), (241, L1 - 1.45), (300, 1.0), (355, 0.55), (460, 0.38),
          (571, 0.22), (640, 0.075), (F_IMPACT, 0.0)]
d_of = pchip(D_KEYS)
PEN = pchip([(F_IMPACT, 0.0), (712, 0.0035), (760, 0.0048), (835, 0.0055), (900, 0.0090), (949, 0.0094)])   # metres past the rim
TILT = pchip([(F_IMPACT, 0.0), (835, 0.0), (900, 4.0), (949, 28.0)])
F_RIC, F_WALL = 949, 1078
DR = Vector((-0.95, 0.06, 0.14)).normalized()
def q_along(d, spin):
    return d.to_track_quat('Z', 'Y') @ Quaternion((0, 0, 1), R_(spin))
_qp = [None]
def key_bul(f, loc, q):
    if _qp[0] is not None and q.dot(_qp[0]) < 0: q = -q
    _qp[0] = q; BUL.location = loc; BUL.rotation_quaternion = q
    BUL.keyframe_insert("location", frame=f); BUL.keyframe_insert("rotation_quaternion", frame=f)
BPOS = {}
for f in range(1, F_IMPACT + 1):
    p = PI - DIR * d_of(f); BPOS[f] = p
    if f % 2 == 0 or f in (1, F_IMPACT) or f < 140:
        key_bul(f, p, q_along(DIR, f * 9.0))
LOC_IN = {}
for f in range(F_IMPACT, F_RIC + 1):
    H = hs_world(f) if f % 3 == 0 or f in (F_IMPACT, F_RIC) else None
    if H is None: continue
    dl = (Hs_imp.to_3x3().inverted() @ DIR).normalized()
    loc_l = PI_LOC + dl * PEN(f)
    tilt_axis = dl.cross(Vector((1, 0, 0))).normalized()
    dl_t = (Matrix.Rotation(R_(-TILT(f)), 3, tilt_axis) @ dl).normalized()
    p = H @ loc_l; d_w = (H.to_3x3().normalized() @ dl_t).normalized()
    BPOS[f] = p; LOC_IN[f] = (loc_l, dl_t)
    key_bul(f, p, q_along(d_w, F_IMPACT * 9.0 + (f - F_IMPACT) * 1.5))
P_RIC = BPOS[F_RIC]
t_wall = (P_RIC.x - (-2.2)) / -DR.x
HOLE = P_RIC + DR * t_wall
print("HOLE", tuple(round(v, 3) for v in HOLE))
sc["HOLE"] = tuple(HOLE)
R_OF = pchip([(F_RIC, 0.0), (975, 0.05), (1010, 0.30), (1045, 0.95), (F_WALL, t_wall - 0.008)])
for f in range(F_RIC + 1, F_WALL + 1):
    p = P_RIC + DR * R_OF(f); BPOS[f] = p
    wob = 25 * math.sin(f * 0.5) * (1 - smooth((f - F_RIC) / 80))
    d_w = (Matrix.Rotation(R_(wob), 3, Vector((0, 0, 1))) @ DR).normalized()
    if f % 2 == 0 or f == F_WALL: key_bul(f, p, q_along(d_w, f * 20.0))
for f in (F_WALL + 1, 1500):
    BPOS[f] = HOLE - DR * 0.008; key_bul(f, HOLE - DR * 0.008, q_along(DR, F_WALL * 20.0))
for f in range(F_WALL + 1, 1501): BPOS[f] = HOLE - DR * 0.008
key_vis(trail, [(1, True), (F_IMPACT - 30, True), (F_IMPACT - 29, False)])
constant_interp(trail)

# ------------------------------------------------------------------ window shatter (polar shards around G)
glass = bpy.data.objects["RoomWin_Glass"]
GX0, GX1, GZ0, GZ1 = -1.95, -0.65, 0.85, 2.05
GY = glass.location.y
def clip(poly, x0, x1, z0, z1):
    def cl(pts, inside, inter):
        out = []
        for i in range(len(pts)):
            a, b = pts[i - 1], pts[i]
            if inside(b):
                if not inside(a): out.append(inter(a, b))
                out.append(b)
            elif inside(a): out.append(inter(a, b))
        return out
    def ix(xc):
        return lambda a, b: (xc, a[1] + (b[1] - a[1]) * (xc - a[0]) / (b[0] - a[0]))
    def iz(zc):
        return lambda a, b: (a[0] + (b[0] - a[0]) * (zc - a[1]) / (b[1] - a[1]), zc)
    p = poly
    for ins, it in ((lambda q: q[0] >= x0, ix(x0)), (lambda q: q[0] <= x1, ix(x1)), (lambda q: q[1] >= z0, iz(z0)), (lambda q: q[1] <= z1, iz(z1))):
        if not p: return p
        p = cl(p, ins, it)
    return p
rings = [0.0, 0.015, 0.04, 0.075, 0.12, 0.18, 0.25, 0.34, 0.45, 0.58, 0.74, 0.95, 1.25, 1.6]
GM = mat("ShardGlass", (0.92, 0.97, 1.0), 0.03, trans=1.0, ior=1.5)
SHARDS = []
for ri in range(len(rings) - 1):
    r0, r1 = rings[ri], rings[ri + 1]
    na = max(5, int(2 * math.pi * (r0 + r1) / 2 / max(0.03, (r1 - r0) * 0.9)))
    na = min(na, 26)
    off = random.uniform(0, 1)
    angs = sorted([(k + off + random.uniform(-0.3, 0.3)) / na * 2 * math.pi for k in range(na)])
    for k in range(na):
        a0, a1 = angs[k], angs[(k + 1) % na] + (2 * math.pi if k == na - 1 else 0)
        poly = []
        for t in (a0, (a0 + a1) / 2, a1):
            poly.append((G.x + math.cos(t) * r0 * random.uniform(0.95, 1.05), G.z + math.sin(t) * r0))
        for t in (a1, (a0 + a1) / 2, a0):
            rr = r1 * random.uniform(0.93, 1.07)
            poly.append((G.x + math.cos(t) * rr, G.z + math.sin(t) * rr))
        poly = clip(poly, GX0, GX1, GZ0, GZ1)
        if len(poly) < 3: continue
        cx = sum(p[0] for p in poly) / len(poly); cz = sum(p[1] for p in poly) / len(poly)
        area = abs(sum(poly[i - 1][0] * poly[i][1] - poly[i][0] * poly[i - 1][1] for i in range(len(poly)))) / 2
        if area < 2e-5: continue
        n = len(poly)
        v = [(p[0] - cx, -0.003, p[1] - cz) for p in poly] + [(p[0] - cx, 0.003, p[1] - cz) for p in poly]
        fsx = [tuple(range(n))[::-1], tuple(range(n, 2 * n))] + [(i, (i + 1) % n, n + (i + 1) % n, n + i) for i in range(n)]
        o = from_pydata("Shard", v, fsx, GM, c="Shards"); o.location = (cx, GY, cz)
        SHARDS.append((o, math.hypot(cx - G.x, cz - G.z)))
print("SHARDS", len(SHARDS))
F_GLASS = 133
key_vis(glass, [(1, True), (F_GLASS, False)]); constant_interp(glass)
FLOOR_Z = 0.004
for o, r in SHARDS:
    o.rotation_mode = 'XYZ'
    p = o.location.copy(); rot = Vector((0, 0, 0))
    rel = Vector((p.x - G.x, 0, p.z - G.z)); rad = rel.normalized() if rel.length > 1e-6 else Vector((1, 0, 0))
    if r < 0.40:            # blown inward with the bullet
        sp = min(3.5, 0.4 / (r + 0.1) + 0.8)
        v = DIR * sp * random.uniform(0.6, 1.1) + rad * random.uniform(0.3, 1.2) + Vector((0, 0, random.uniform(-0.2, 0.6)))
        w = Vector([random.uniform(-15, 15) for _ in range(3)]); t0 = F_GLASS + int(r * 25)
    elif r < 0.62:          # loosened, drops later
        v = DIR * random.uniform(0.2, 0.8) + Vector((0, 0, -0.1)); w = Vector([random.uniform(-4, 4) for _ in range(3)]); t0 = F_GLASS + 40 + int(r * 80)
    else:
        v = None
    o.keyframe_insert("location", frame=1); o.keyframe_insert("rotation_euler", frame=1)
    if v is None:
        continue
    o.keyframe_insert("location", frame=t0); o.keyframe_insert("rotation_euler", frame=t0)
    landed = False
    for f in range(t0 + 1, 1501):
        dt = ts(f)
        if not landed:
            v = v + Vector((0, 0, -9.81 * dt)); v = v * (1 - 0.4 * dt)
            p = p + v * dt; rot = rot + w * dt
            fz = FLOOR_Z if p.y > 0.25 else (-0.02 if p.y < -0.05 else 0.83)
            if p.z < fz + 0.002:
                p.z = fz + 0.002; landed = True; rot.x = R_(90) * round(rot.x / R_(90)) if False else rot.x
                o.rotation_euler = (R_(90), rot.y, rot.z)
        if (f - t0) % 3 == 0 or landed:
            o.location = p
            if not landed: o.rotation_euler = (rot.x, rot.y, rot.z)
            o.keyframe_insert("location", frame=f); o.keyframe_insert("rotation_euler", frame=f)
        if landed: break
# a few cracks stay in the remaining pane: thin dark lines are implied by the shard gaps (shards shrink 3% so edges read)
for o, r in SHARDS: o.scale = (0.97, 1.0, 0.97)

# ------------------------------------------------------------------ cup crack (procedural, grows from the impact point) + fragments
shellL = bpy.data.objects["HS_Shell_L"]; faceL = bpy.data.objects["HS_Face_L"]
MSL = mat("HS_Shell", (0, 0, 0)).copy(); MSL.name = "HS_Shell_Cracked"
nt = MSL.node_tree; Nn, Ll = nt.nodes, nt.links; bsdf = Nn["Principled BSDF"]
tc = Nn.new("ShaderNodeTexCoord"); vor = Nn.new("ShaderNodeTexVoronoi"); vor.feature = 'DISTANCE_TO_EDGE'; vor.inputs["Scale"].default_value = 90
# jagged: distort the lookup with noise, and stretch the cells radially away from the impact point
nz = Nn.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 300; Ll.new(tc.outputs["Object"], nz.inputs[0])
sub_ = Nn.new("ShaderNodeVectorMath"); sub_.operation = 'SUBTRACT'; Ll.new(tc.outputs["Object"], sub_.inputs[0]); sub_.inputs[1].default_value = PI_LOC
mixv = Nn.new("ShaderNodeMix"); mixv.data_type = 'VECTOR'; mixv.inputs[0].default_value = 0.004
Ll.new(sub_.outputs[0], mixv.inputs[4]); Ll.new(nz.outputs["Color"], mixv.inputs[5])
Ll.new(mixv.outputs[1], vor.inputs[0])
dist = Nn.new("ShaderNodeVectorMath"); dist.operation = 'DISTANCE'; dist.inputs[1].default_value = PI_LOC; Ll.new(tc.outputs["Object"], dist.inputs[0])
rad = Nn.new("ShaderNodeValue"); rad.name = "CrackRadius"; rad.outputs[0].default_value = 0.0
inr = Nn.new("ShaderNodeMath"); inr.operation = 'LESS_THAN'; Ll.new(dist.outputs["Value"], inr.inputs[0]); Ll.new(rad.outputs[0], inr.inputs[1])
edge = Nn.new("ShaderNodeMath"); edge.operation = 'LESS_THAN'; edge.inputs[1].default_value = 0.022; Ll.new(vor.outputs["Distance"], edge.inputs[0])
# radial streaks: stretch voronoi along the angle around the impact point via noise
both = Nn.new("ShaderNodeMath"); both.operation = 'MULTIPLY'; Ll.new(inr.outputs[0], both.inputs[0]); Ll.new(edge.outputs[0], both.inputs[1])
mixc = Nn.new("ShaderNodeMix"); mixc.data_type = 'RGBA'
Ll.new(both.outputs[0], mixc.inputs[0]); mixc.inputs[6].default_value = (0.035, 0.037, 0.042, 1); mixc.inputs[7].default_value = (0.32, 0.32, 0.33, 1)
Ll.new(mixc.outputs[2], bsdf.inputs["Base Color"])
bmp = Nn.new("ShaderNodeBump"); bmp.inputs["Strength"].default_value = 0.8; bmp.invert = True; Ll.new(both.outputs[0], bmp.inputs["Height"]); Ll.new(bmp.outputs[0], bsdf.inputs["Normal"])
shellL.data.materials[0] = MSL; faceL.data.materials[0] = MSL
for f, v in ((1, 0.0), (F_IMPACT, 0.0), (F_IMPACT + 3, 0.008), (F_IMPACT + 20, 0.018), (F_IMPACT + 60, 0.026)):
    rad.outputs[0].default_value = v; rad.outputs[0].keyframe_insert("default_value", frame=f)
# the hit cup's RGB ring flickers and dies on impact
rgbL = bpy.data.objects["HS_RGB_L"]; mL = rgbL.data.materials[0].copy(); mL.name = "HS_RGB_L_dying"; rgbL.data.materials[0] = mL
eL = mL.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]
for f, v in ((1, 8.0), (F_IMPACT, 8.0), (F_IMPACT + 2, 25.0), (F_IMPACT + 5, 0.5), (F_IMPACT + 9, 6.0), (F_IMPACT + 13, 0.0), (F_IMPACT + 40, 1.5), (F_IMPACT + 44, 0.0)):
    eL.default_value = v; eL.keyframe_insert("default_value", frame=f)
CHIPM = mat("ChipPlastic", (0.035, 0.037, 0.042), 0.35)
DUSTM = mat("PlasticDust", (0.5, 0.5, 0.52), 0.9)
def debris(name, n, origin_fn, f0, vel_fn, size, m, floor_fn, life=None, c="FX"):
    out = []
    for i in range(n):
        s_ = size * random.uniform(0.5, 1.3)
        v_ = [(random.uniform(-1, 1) * s_, random.uniform(-1, 1) * s_ * 0.5, random.uniform(-1, 1) * s_) for _ in range(4)]
        o = from_pydata(name, v_, [(0, 1, 2), (0, 2, 3), (0, 3, 1), (1, 3, 2)], m, c=c)
        p = origin_fn(f0).copy(); v = vel_fn(i); w = Vector([random.uniform(-30, 30) for _ in range(3)]); rot = Vector((0, 0, 0))
        key_vis(o, [(1, False), (f0, True)] + ([(f0 + life, False)] if life else [])); constant_interp(o)
        o.location = p; o.keyframe_insert("location", frame=f0); o.keyframe_insert("rotation_euler", frame=f0)
        landed = False
        for f in range(f0 + 1, min(1501, f0 + (life or 900))):
            dt = ts(f)
            if not landed:
                v = v + Vector((0, 0, -9.81 * dt)); p = p + v * dt; rot = rot + w * dt
                if p.z < floor_fn(p) + 0.002: p.z = floor_fn(p) + 0.002; landed = True
            if (f - f0) % 3 == 0 or landed:
                o.location = p; o.rotation_euler = rot
                o.keyframe_insert("location", frame=f); o.keyframe_insert("rotation_euler", frame=f)
            if landed: break
        out.append(o)
    return out
NRM_W = (Hs_imp.to_3x3().normalized() @ Vector((0.35, 1, 0))).normalized()   # outward-back from the cup rim
def chip_vel(i):
    return (NRM_W * random.uniform(1.0, 3.5) + Vector([random.uniform(-1.6, 1.6) for _ in range(3)]) + Vector((0, 0, 0.6)))
debris("CupChip", 26, lambda f: PI, F_IMPACT + 1, chip_vel, 0.0035, CHIPM, lambda p: FLOOR_Z)
debris("CupDust", 30, lambda f: PI, F_IMPACT + 1, lambda i: chip_vel(i) * 0.5, 0.0012, DUSTM, lambda p: FLOOR_Z, life=220)

# ------------------------------------------------------------------ cutaway of the left cup (boolean, cutter parented to the headset)
CUT = box("Cutaway_Cutter", (0.2, 0.2, 0.1), (0, 0, 0), None, c="FX"); CUT.display_type = 'WIRE'; CUT.hide_render = True
CUT.parent = HS_ROOT
CZ = lambda dz: Vector((XC1, 0.0, 0.0045 + 0.05 + dz))
for f, dz in ((1, 0.08), (818, 0.07), (850, 0.0), (948, 0.0), (972, 0.07)):
    CUT.location = CZ(dz); CUT.keyframe_insert("location", frame=f)
for nm in ("HS_Shell_L", "HS_Face_L", "HS_Foam_L", "HS_Steel_L", "HS_Driver_L", "HS_Cushion_L", "HS_Yoke_L0", "HS_Yoke_L1", "HS_RGB_L", "HS_Trim_L"):
    o = bpy.data.objects[nm]
    md = o.modifiers.new("Cutaway", 'BOOLEAN'); md.object = CUT; md.operation = 'DIFFERENCE'; md.solver = 'EXACT'
    for f, on in ((1, False), (815, True), (975, False)):
        md.show_render = on; md.show_viewport = on
        o.keyframe_insert('modifiers["Cutaway"].show_render', frame=f); o.keyframe_insert('modifiers["Cutaway"].show_viewport', frame=f)
    for fc in fcurves(o):
        for kp in fc.keyframe_points: kp.interpolation = 'CONSTANT'
# foam dents where the bullet pushes in (shape key)
foam = bpy.data.objects["HS_Foam_L"]
foam.shape_key_add(name="Basis"); dk = foam.shape_key_add(name="dent")
for v in dk.data:
    d_ = (v.co - PI_LOC).length
    if d_ < 0.02:
        k = (1 - d_ / 0.02) ** 2; radial = Vector((0, v.co.y, v.co.z)).normalized()
        v.co = v.co - radial * 0.006 * k
for f, val in ((1, 0.0), (835, 0.0), (900, 1.0), (949, 1.0), (990, 0.35)):
    dk.value = val; dk.keyframe_insert("value", frame=f)
# cyan explainer rim light for the cutaway (studio look), parented to the headset
cyl_d = bpy.data.lights.new("Cutaway_Cyan", 'AREA'); cyl_d.size = 0.25; cyl_d.color = (0.45, 0.85, 1.0)
cl = bpy.data.objects.new("Cutaway_Cyan", cyl_d); link(cl, "Lights"); cl.parent = HS_ROOT; cl.location = (XC1 + 0.12, 0.10, 0.20)
cl.rotation_euler = (Vector((XC1, 0, 0)) - Vector(cl.location)).to_track_quat('-Z', 'Y').to_euler(); cl.visible_camera = False
for f, e in ((1, 0.0), (820, 0.0), (850, 6.0), (945, 6.0), (975, 0.0)):
    cyl_d.energy = e; cyl_d.keyframe_insert("energy", frame=f)

# ------------------------------------------------------------------ ricochet sparks + flash
SPM = mat("Spark", (1, 0.6, 0.2), 0.5, emit=(1.0, 0.55, 0.15), estr=60.0)
for i in range(34):
    o = box("Spark", (0.0006, 0.0006, 0.012), (0, 0, 0), SPM, c="FX"); o.rotation_mode = 'QUATERNION'
    d = (DR * random.uniform(0.3, 1.0) + NRM_W * random.uniform(0.0, 1.0) + Vector([random.uniform(-0.8, 0.8) for _ in range(3)])).normalized()
    sp = random.uniform(0.0004, 0.0016); life = random.randint(30, 70); f0 = F_RIC + random.randint(-2, 6)
    key_vis(o, [(1, False), (f0, True), (f0 + life, False)]); constant_interp(o)
    for k in range(0, life + 1, 3):
        o.location = P_RIC + d * sp * k + Vector((0, 0, -0.0000012 * k * k)); o.rotation_quaternion = d.to_track_quat('Z', 'Y')
        s_ = max(0.05, 1 - k / life); o.scale = (s_, s_, 0.4 + 1.5 * s_)
        o.keyframe_insert("location", frame=f0 + k); o.keyframe_insert("rotation_quaternion", frame=f0 + k); o.keyframe_insert("scale", frame=f0 + k)
fl = bpy.data.lights.new("Ricochet_Flash", 'POINT'); fl.color = (1.0, 0.6, 0.25); fl.shadow_soft_size = 0.01
flo = bpy.data.objects.new("Ricochet_Flash", fl); link(flo, "Lights"); flo.location = P_RIC + NRM_W * 0.02
for f, e in ((1, 0), (F_RIC - 1, 0), (F_RIC + 2, 6.0), (F_RIC + 30, 1.5), (F_RIC + 70, 0)):
    fl.energy = e; fl.keyframe_insert("energy", frame=f)

# ------------------------------------------------------------------ wall hit: hole, plaster chips, dust puff
holeM = bpy.data.materials.new("BulletHole"); holeM.use_nodes = True; hn = holeM.node_tree.nodes; hb = hn["Principled BSDF"]
tcH = hn.new("ShaderNodeTexCoord"); gr = hn.new("ShaderNodeTexGradient"); gr.gradient_type = 'SPHERICAL'
mpH = hn.new("ShaderNodeMapping"); mpH.inputs["Scale"].default_value = (29, 29, 29)
holeM.node_tree.links.new(tcH.outputs["Object"], mpH.inputs[0]); holeM.node_tree.links.new(mpH.outputs[0], gr.inputs[0])
rp = hn.new("ShaderNodeValToRGB"); e0, e1 = rp.color_ramp.elements; e0.position = 0.0; e0.color = (0.52, 0.55, 0.58, 1)
e1.position = 0.55; e1.color = (0.02, 0.02, 0.02, 1); rp.color_ramp.elements.new(0.35).color = (0.85, 0.83, 0.78, 1)
holeM.node_tree.links.new(gr.outputs[0], rp.inputs[0]); holeM.node_tree.links.new(rp.outputs[0], hb.inputs["Base Color"])
hb.inputs["Roughness"].default_value = 0.95
PRF = bpy.data.objects["Print_Frame"]
hole = cyl("BulletHole", 0.030, 0.002, Vector((PRF.location.x + 0.0195, HOLE.y, HOLE.z)), holeM, c="FX", rot=(0, R_(90), 0), seg=24)
hole.parent = PRF; hole.matrix_parent_inverse = PRF.matrix_world.inverted()
key_vis(hole, [(1, False), (F_WALL, True)]); constant_interp(hole)
WALLN = Vector((1, 0, 0))
PLM = mat("PlasterChip", (0.8, 0.8, 0.76), 0.9)
debris("PlasterChip", 30, lambda f: HOLE + WALLN * 0.01, F_WALL, lambda i: (WALLN * random.uniform(0.8, 2.6) - DR * 0.3 + Vector([random.uniform(-1.2, 1.2) for _ in range(3)])),
       0.004, PLM, lambda p: FLOOR_Z)
PUFF = mat("DustPuff", (0.85, 0.84, 0.8), 1.0, alpha=0.18)
PUFF.blend_method = 'BLEND' if hasattr(PUFF, "blend_method") else None
for i in range(28):
    o = bpy.data.objects.new("Dust", bpy.data.meshes.new("Dust")); link(o, "FX")
    bm_ = bmesh.new(); bmesh.ops.create_icosphere(bm_, subdivisions=2, radius=1.0); bm_.to_mesh(o.data); bm_.free(); o.data.materials.append(PUFF)
    d = (WALLN * random.uniform(0.4, 1.0) + Vector([random.uniform(-0.6, 0.6) for _ in range(3)])).normalized()
    key_vis(o, [(1, False), (F_WALL, True), (F_WALL + 160, False)]); constant_interp(o)
    for k in range(0, 161, 8):
        u = k / 160; o.location = HOLE + d * 0.16 * (1 - (1 - u) ** 3) + Vector((0, 0, -0.03 * u)); s_ = 0.004 + 0.022 * (u ** 0.5) * (1 - u * 0.5)
        o.scale = (s_, s_, s_); o.keyframe_insert("location", frame=F_WALL + k); o.keyframe_insert("scale", frame=F_WALL + k)

# ------------------------------------------------------------------ ambient life outside: birds, sprinkler, leaves
BIRDM = mat("Bird", (0.12, 0.10, 0.09), 0.7)
for i in range(6):
    body_ = bpy.data.objects.new("Bird%d" % i, bpy.data.meshes.new("Bird")); link(body_, "Life")
    bm_ = bmesh.new(); bmesh.ops.create_uvsphere(bm_, u_segments=10, v_segments=6, radius=0.05); bm_.to_mesh(body_.data); bm_.free()
    body_.data.materials.append(BIRDM); body_.scale = (0.7, 1.4, 0.7)
    wings = []
    for sx in (-1, 1):
        w_ = from_pydata("BirdWing", [(0, -0.03, 0), (sx * 0.16, -0.01, 0), (sx * 0.12, 0.05, 0), (0, 0.04, 0)], [(0, 1, 2, 3)], BIRDM, c="Life")
        w_.parent = body_; wings.append((w_, sx))
    x0 = -8.6 + i * 0.55; p0 = Vector((x0, -17.38, 1.0))
    t_off = 15 + i * 6
    for f in range(1, 241, 2):
        if f < t_off:
            p = p0 + Vector((0, 0, 0.005 * math.sin(f * 0.3 + i))); flap = 0.2 * math.sin(f * 0.2)
        else:
            u = (f - t_off) / 60.0
            p = p0 + Vector((random.uniform(-0.002, 0.002) + (i - 2.5) * 0.5 * u, -1.5 * u, 1.6 * u + 0.3 * u * u))
            flap = 1.0 * math.sin((f - t_off) * 0.55)
        body_.location = p; body_.rotation_euler = (R_(-20 if f >= t_off else 0), 0, R_(180 + i * 10))
        body_.keyframe_insert("location", frame=f); body_.keyframe_insert("rotation_euler", frame=f)
        for w_, sx in wings:
            w_.rotation_euler = (0, sx * flap, 0); w_.keyframe_insert("rotation_euler", frame=f)
# sprinkler: a rotating head throwing droplet arcs over the lawn
SPR = Vector((-1.2, -9.0, 0.0))
cyl("Sprinkler_Base", 0.06, 0.08, SPR + Vector((0, 0, 0.04)), mat("SprinklerGreen", (0.1, 0.3, 0.12), 0.5), c="Life")
WATER = mat("Water", (0.9, 0.95, 1.0), 0.02, trans=1.0, ior=1.33)
drops = []
for j in range(3):
    for k in range(18):
        o = bpy.data.objects.new("Drop", bpy.data.meshes.new("Drop")); link(o, "Life")
        bm_ = bmesh.new(); bmesh.ops.create_icosphere(bm_, subdivisions=1, radius=0.012); bm_.to_mesh(o.data); bm_.free(); o.data.materials.append(WATER)
        drops.append((o, j, k))
for f in range(1, 241, 2):
    ang = R_(f * 1.2)
    for o, j, k in drops:
        a = ang + j * 2.1; u = ((k / 18.0) + f * 0.004) % 1.0
        r = 2.6 * u; z = 0.1 + 1.4 * u - 1.6 * u * u
        o.location = SPR + Vector((math.cos(a) * r, math.sin(a) * r, max(0.0, z)))
        o.keyframe_insert("location", frame=f)
# drifting leaves from the tree
LEAFM = mat("Leaf", (0.25, 0.32, 0.10), 0.6)
for i in range(14):
    o = from_pydata("Leaf", [(-0.03, 0, 0), (0, -0.05, 0), (0.03, 0, 0), (0, 0.05, 0)], [(0, 1, 2, 3)], LEAFM, c="Life")
    p0 = Vector((-7.5 + random.uniform(-2.5, 2.5), -6 + random.uniform(-2.5, 2.5), random.uniform(2.0, 4.5)))
    for f in range(1, 241, 3):
        u = f / 240
        o.location = p0 + Vector((math.sin(f * 0.05 + i) * 0.4 + 1.2 * u, 0.6 * u, -1.6 * u))
        o.rotation_euler = (math.sin(f * 0.07 + i) * 1.2, math.cos(f * 0.05 + i), f * 0.02)
        o.keyframe_insert("location", frame=f); o.keyframe_insert("rotation_euler", frame=f)

# ------------------------------------------------------------------ inside life: curtains flutter after the glass breaks, screen, LEDs
for side in "LR":
    c_ = bpy.data.objects["Curtain_" + side]
    wv = c_.modifiers.new("Flutter", 'WAVE'); wv.use_normal = True; wv.use_x = False; wv.use_y = False
    wv.height = 0.0; wv.width = 0.35; wv.speed = 0.012; wv.narrowness = 1.2
    for f, h in ((1, 0.004), (F_GLASS, 0.004), (F_GLASS + 20, 0.035), (700, 0.02), (1100, 0.012), (1500, 0.008)):
        wv.height = h; c_.keyframe_insert('modifiers["Flutter"].height', frame=f)
scr_m = bpy.data.materials["Screen"]; pan = scr_m.node_tree.nodes["ScreenPan"]; emit = scr_m.node_tree.nodes["ScreenEmit"]
for f in range(1, 1501, 10):
    pan.inputs["Rotation"].default_value = (0, 0, R_(0.06 * f + 8 * math.sin(f * 0.03)))
    pan.inputs["Rotation"].keyframe_insert("default_value", frame=f)
    emit.inputs["Strength"].default_value = 2.2 + 0.5 * math.sin(f * 0.37) + (0.8 if (f // 10) % 9 == 0 else 0.0)
    emit.inputs["Strength"].keyframe_insert("default_value", frame=f)
glow = bpy.data.lights["Monitor_Glow"]
for f in range(1, 1501, 10):
    glow.energy = 35 + 10 * math.sin(f * 0.37) + (14 if (f // 10) % 9 == 0 else 0); glow.keyframe_insert("energy", frame=f)
    hue = (f / 600.0) % 1.0
    import colorsys
    glow.color = colorsys.hsv_to_rgb(0.58 + 0.05 * math.sin(f * 0.01), 0.35, 1.0); glow.keyframe_insert("color", frame=f)
led = bpy.data.materials["LEDStrip"].node_tree.nodes["Principled BSDF"]
for f in range(1, 1501, 20):
    led.inputs["Emission Color"].default_value = (*colorsys.hsv_to_rgb((0.75 + f / 1500.0 * 0.6) % 1.0, 0.85, 1.0), 1)
    led.inputs["Emission Color"].keyframe_insert("default_value", frame=f)

# the framed print: glass shatters, the frame swings on its nail and settles
pglass = bpy.data.objects["Print_Glass"]; key_vis(pglass, [(1, True), (F_WALL, False)]); constant_interp(pglass)
debris("PrintShard", 40, lambda f: HOLE + WALLN * 0.03, F_WALL, lambda i: (WALLN * random.uniform(0.3, 1.4) + Vector((0, random.uniform(-1, 1), random.uniform(-0.6, 0.8)))),
       0.012, GM, lambda p: FLOOR_Z)
PRF.rotation_mode = 'XYZ'
for k in range(0, 260, 3):
    f = F_WALL + k; ang = 9.0 * math.exp(-k / 70.0) * math.sin(k / 9.0)
    PRF.rotation_euler = (R_(ang), 0, 0); PRF.keyframe_insert("rotation_euler", frame=f)
PRF.rotation_euler = (0, 0, 0); PRF.keyframe_insert("rotation_euler", frame=1); PRF.keyframe_insert("rotation_euler", frame=F_WALL - 1)
# the can by his keyboard tips over when his knees jerk the desk at the impact, and rolls a little
CAN = bpy.data.objects["Can_Tip"]; CAN.rotation_mode = 'QUATERNION'
c0 = CAN.location.copy(); tipd = Vector((0.55, -0.83, 0)).normalized(); P0 = c0 + tipd * 0.033 - Vector((0, 0, 0.06))
axis = Vector((0, 0, 1)).cross(tipd).normalized()
for f in []:   # v006: the can no longer tips on its own (props only move by a hand)
    if f < 712: th, roll = 0.0, 0.0
    else:
        u = min(1.0, (f - 712) / 20.0); th = R_(90) * u * u
        roll = max(0, f - 732) * 0.012 * math.exp(-max(0, f - 732) / 60.0) * 60
    if th < R_(90) - 1e-4 or roll == 0:
        q = Quaternion(axis, th); loc = P0 + q @ (c0 - P0)
    else:
        q = Quaternion(axis, R_(90)); loc = P0 + q @ (c0 - P0)
        dist = 0.033 * math.radians(roll * 57.3) / 57.3 * 57.3 * 0.0 + 0.033 * roll / 57.3
        loc = loc + Vector((-tipd.y, tipd.x, 0)) * dist; q = Quaternion(Vector((-tipd.y, tipd.x, 0)) .cross(Vector((0, 0, 1))).normalized(), -roll / 57.3) @ q
    CAN.location = loc; CAN.rotation_quaternion = q
    CAN.keyframe_insert("location", frame=f); CAN.keyframe_insert("rotation_quaternion", frame=f)
# chair: a startled swivel after the impact
CH = bpy.data.objects["Chair"]
for fc in fcurves(CH):
    if fc.data_path == "rotation_euler" and fc.array_index == 2:
        for kp in fc.keyframe_points:
            f = kp.co.x
            if f > 700: kp.co.y += R_(8) * math.exp(-(f - 700) / 90.0) * math.sin((f - 700) / 14.0); kp.handle_left.y = kp.handle_right.y = kp.co.y
        fc.update()
