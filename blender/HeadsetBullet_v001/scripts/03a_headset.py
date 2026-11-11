# Part of 03_animate.py: a generic over-ear headset built to the teen's head (no logo), with the parts the story needs:
# plastic shell (cracks), thick foam padding, a steel frame ring inside each cup, bendable band.
# Built in REST coordinates (MPFB faces -Y; his LEFT is +X), then attached with Child Of to the head bone.
A.data.pose_position = 'REST'; bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get()
body_e = bpy.data.objects["Teen.body"].evaluated_get(dg)
hair_e = bpy.data.objects["Teen.short02"].evaluated_get(dg)
bme = body_e.to_mesh()
EYE = FR.BN["eye.L"].head_local
hv = [body_e.matrix_world @ v.co for v in bme.vertices]
head_pts = [p for p in hv if p.z > EYE.z - 0.12 and abs(p.y - EYE.y - 0.08) < 0.16]
Z_EAR = EYE.z - 0.035
band_pts = [p for p in head_pts if abs(p.z - Z_EAR) < 0.012 and EYE.y + 0.05 < p.y < EYE.y + 0.13]
WX = max(abs(p.x) for p in band_pts)
Y_EAR = sum(p.y for p in band_pts if abs(p.x) > WX - 0.012) / max(1, len([p for p in band_pts if abs(p.x) > WX - 0.012]))
hm = hair_e.to_mesh(); hp = [hair_e.matrix_world @ v.co for v in hm.vertices]
TOP = max([p.z for p in hp] + [p.z for p in head_pts])
HEAD_C = Vector((0.0, Y_EAR, Z_EAR))
body_e.to_mesh_clear(); hair_e.to_mesh_clear()
print("HEADFIT WX", round(WX, 4), "Y_EAR", round(Y_EAR, 4), "Z_EAR", round(Z_EAR, 4), "TOP", round(TOP, 4))

HS = {}  # parts
MS = mat("HS_Shell", (0.035, 0.037, 0.042), 0.32, coat=0.4)
MF = bpy.data.materials.new("HS_Foam"); MF.use_nodes = True
fb = MF.node_tree.nodes["Principled BSDF"]; fb.inputs["Base Color"].default_value = (0.58, 0.55, 0.45, 1); fb.inputs["Roughness"].default_value = 0.95
_n = MF.node_tree.nodes.new("ShaderNodeTexNoise"); _n.inputs["Scale"].default_value = 900; _n.inputs["Detail"].default_value = 3
_b = MF.node_tree.nodes.new("ShaderNodeBump"); _b.inputs["Strength"].default_value = 0.6
MF.node_tree.links.new(_n.outputs[0], _b.inputs["Height"]); MF.node_tree.links.new(_b.outputs[0], fb.inputs["Normal"])
MM = mat("HS_Steel", (0.62, 0.63, 0.66), 0.22, metal=1.0)
MC = mat("HS_Cushion", (0.03, 0.03, 0.03), 0.6)           # leatherette ear cushion
MD = mat("HS_Driver", (0.08, 0.08, 0.09), 0.4, metal=0.5)
MB = mat("HS_BandPad", (0.05, 0.05, 0.055), 0.7)

R_OUT, R_SH, R_FO, R_ME0, R_ME1 = 0.050, 0.046, 0.040, 0.036, 0.0395     # shell outer/inner, foam inner, steel ring inner/outer
X0 = WX + 0.004                         # cushion touches here (4 mm off the skin)
XC0, XC1 = X0 + 0.022, X0 + 0.060       # cup body from/to (outward)

def ring(name, r0, r1, xa, xb, seg=72, m=None, cap_outer=False):
    """annular tube along X between xa..xb (rest coords, sign handled by caller), closed manifold"""
    vs, fs = [], []
    for k, x in enumerate((xa, xb)):
        for r in (r0, r1):
            for i in range(seg):
                t = 2 * math.pi * i / seg
                vs.append((x, math.cos(t) * r, math.sin(t) * r))
    def idx(k, j, i): return (k * 2 + j) * seg + i % seg
    for i in range(seg):
        fs.append((idx(0, 1, i), idx(1, 1, i), idx(1, 1, i + 1), idx(0, 1, i + 1)))   # outer
        fs.append((idx(0, 0, i + 1), idx(1, 0, i + 1), idx(1, 0, i), idx(0, 0, i)))   # inner
        fs.append((idx(0, 0, i), idx(0, 1, i), idx(0, 1, i + 1), idx(0, 0, i + 1)))   # end a
        fs.append((idx(1, 0, i + 1), idx(1, 1, i + 1), idx(1, 1, i), idx(1, 0, i)))   # end b
    return from_pydata(name, vs, fs, m, c="Headset")

def disc(name, r, xa, xb, seg=72, m=None):
    vs = []
    for x in (xa, xb):
        for i in range(seg):
            t = 2 * math.pi * i / seg; vs.append((x, math.cos(t) * r, math.sin(t) * r))
    vs += [(xa, 0, 0), (xb, 0, 0)]
    fs = [(i, (i + 1) % seg, seg + (i + 1) % seg, seg + i) for i in range(seg)]
    fs += [((i + 1) % seg, i, 2 * seg) for i in range(seg)] + [(seg + i, seg + (i + 1) % seg, 2 * seg + 1) for i in range(seg)]
    return from_pydata(name, vs, fs, m, c="Headset")

HS_ROOT = bpy.data.objects.new("Headset", None); link(HS_ROOT, "Headset")
HS_ROOT.location = HEAD_C
CUPS = {}
for side, sx in (("L", 1), ("R", -1)):
    parts = {}
    def X(x): return sx * x
    parts["shell"] = ring("HS_Shell_" + side, R_SH, R_OUT, X(XC0), X(XC1 - 0.003), m=MS)
    parts["face"] = disc("HS_Face_" + side, R_OUT, X(XC1 - 0.003), X(XC1), m=MS)
    parts["foam"] = ring("HS_Foam_" + side, R_FO, R_SH, X(XC0 + 0.006), X(XC1 - 0.004), m=MF)
    parts["steel"] = ring("HS_Steel_" + side, R_ME0, R_ME1, X(XC0 + 0.002), X(XC1 - 0.008), m=MM)
    parts["driver"] = disc("HS_Driver_" + side, R_ME0, X(XC0 + 0.004), X(XC0 + 0.008), m=MD)
    parts["cushion"] = ring("HS_Cushion_" + side, 0.026, 0.047, X(X0), X(XC0), m=MC)
    for nm, o in parts.items():
        if sx < 0:   # mirrored rings need flipped normals
            me = o.data; bm_ = bmesh.new(); bm_.from_mesh(me); bmesh.ops.reverse_faces(bm_, faces=bm_.faces); bm_.to_mesh(me); bm_.free()
        o.parent = HS_ROOT; o.location = (0, 0, 0)
        if nm in ("cushion", "shell", "face"):
            bv = o.modifiers.new("bev", 'BEVEL'); bv.width = 0.006 if nm == "cushion" else 0.0025; bv.segments = 3; bv.limit_method = 'ANGLE'
        for poly in o.data.polygons: poly.use_smooth = True
        sub = o.modifiers.new("ws", 'WEIGHTED_NORMAL') if False else None
    # steel yoke arms (the metal frame) from the band down both sides of the cup
    for k, dy in enumerate((-1, 1)):
        y = box("HS_Yoke_%s%d" % (side, k), (0.006, 0.008, 0.075), (sx * (XC0 + 0.02), dy * (R_OUT + 0.006), 0.0325), MM, c="Headset")
        y.parent = HS_ROOT
    y = box("HS_YokeTop_" + side, (0.006, 2 * (R_OUT + 0.006) + 0.008, 0.006), (sx * (XC0 + 0.02), 0, R_OUT + 0.02), MM, c="Headset")
    y.parent = HS_ROOT
    CUPS[side] = parts
# band: steel strip + padded cover, an arc from cup top to cup top over the hair
def band(name, r_in, thick, width, m, z_off=0.0):
    pts = []
    zt = TOP + 0.010 - HEAD_C.z + z_off
    ax, az = sx_c = XC0 + 0.02, R_OUT + 0.02
    seg = 40
    vs, fs = [], []
    for i in range(seg + 1):
        t = math.pi * i / seg
        # ellipse through (+ax, az) .. (0, zt) .. (-ax, az)
        x = ax * math.cos(t); z = az + (zt - az) * math.sin(t)
        nrm = Vector((x / (ax * ax), 0, (z - az) / ((zt - az) ** 2))).normalized() if i not in (0, seg) else Vector((math.copysign(1, x), 0, 0))
        for j, (dn, dw) in enumerate(((0, -1), (0, 1), (thick, 1), (thick, -1))):
            p = Vector((x, 0, z)) + nrm * (r_in + dn)
            vs.append((p.x, dw * width / 2, p.z))
    for i in range(seg):
        for j in range(4):
            a0, a1 = i * 4 + j, i * 4 + (j + 1) % 4
            fs.append((a0, a1, a1 + 4, a0 + 4))
    fs.append((3, 2, 1, 0)); fs.append((seg * 4, seg * 4 + 1, seg * 4 + 2, seg * 4 + 3))
    o = from_pydata(name, vs, fs, m, c="Headset"); o.parent = HS_ROOT
    return o
HS_BAND_PAD = band("HS_BandPad", 0.0, 0.014, 0.040, MB)
HS_BAND_STEEL = band("HS_BandSteel", 0.014, 0.004, 0.030, MM)
HS_BAND_TOP = band("HS_BandTop", 0.018, 0.006, 0.036, MS)
for o in (HS_BAND_PAD, HS_BAND_STEEL, HS_BAND_TOP):
    o.modifiers.new("sub", 'SUBSURF').levels = 1
    # shape key 'bent': the left half kinks outward and twists (the band bends on impact)
    o.shape_key_add(name="Basis"); kb_ = o.shape_key_add(name="bent")
    for v in kb_.data:
        if v.co.x > 0.02:
            u = min(1.0, (v.co.x - 0.02) / 0.08)
            v.co = Matrix.Rotation(R_(-14 * u), 3, 'Y') @ v.co + Vector((0.012 * u, 0.006 * u * (v.co.z - 0.05) * 10, -0.004 * u))
for side in "LR":   # cups follow the bent band end on the left
    pass
HEAD_C_REST = HEAD_C.copy()
A.data.pose_position = 'POSE'; bpy.context.view_layer.update()

# attach: Child Of -> head bone (inverse = rest), second Child Of -> carrier (switched on at F_GRAB)
CARRIER = bpy.data.objects.new("Headset_Carrier", None); link(CARRIER, "Headset")
c1 = HS_ROOT.constraints.new('CHILD_OF'); c1.name = "OnHead"; c1.target = A; c1.subtarget = "head"
c1.inverse_matrix = (A.matrix_world @ FR.BN["head"].matrix_local).inverted()
c2 = HS_ROOT.constraints.new('CHILD_OF'); c2.name = "InHands"; c2.target = CARRIER
c2.inverse_matrix = Matrix.Identity(4)
for f, a1 in ((1, 1.0), (F_GRAB - 1, 1.0), (F_GRAB, 0.0)):
    c1.influence = a1; HS_ROOT.keyframe_insert('constraints["OnHead"].influence', frame=f)
    c2.influence = 1.0 - a1; HS_ROOT.keyframe_insert('constraints["InHands"].influence', frame=f)
for fc in fcurves(HS_ROOT):
    for kp in fc.keyframe_points: kp.interpolation = 'CONSTANT'
# hide the top of the hair under the band: small shrinkwrap-free fix -> hair mask not needed (band sits 1 cm above hair top)
def hs_local(p_rest):
    """rest-space point -> point in Headset local space"""
    return p_rest - HEAD_C_REST
