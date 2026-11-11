"""Hero acting, crowds, bullet, cutaway, set swap, one continuous camera.
blender -b scene.blend --python 03_animate.py -- anim.blend"""
import sys, os, math, random, json
import bpy
from mathutils import Vector, Matrix, Quaternion, Euler
HERE = os.path.dirname(os.path.abspath(__file__))
exec(open(HERE + "/anim_lib.py").read())
out = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene
random.seed(3)
STREET_Z = sc["STREET_Z"]
B = [1, 187, 337, 445, 721, 877, 1003, 1189, 1285]   # beat start frames
F_FLASH, F_IMPACT, F_SWAP, END = 116, 168, 1100, 1500
F_OUT, F_IN = 506, 1165   # street hidden / hall shown (both behind the opaque studio dome)
C_STREET, C_HALL, C_STUDIO = (bpy.data.collections[n] for n in ("Street", "Hall", "Studio"))
def lerp(a, b, t): return a + (b - a) * t
def pk(keys):  # pchip on scalar or Vector keys
    if isinstance(keys[0][1], Vector):
        fs = [pchip([(f, v[i]) for f, v in keys]) for i in range(3)]
        return lambda x: Vector((fs[0](x), fs[1](x), fs[2](x)))
    return pchip(keys)

# ------------------------------------------------------------------ world time (freeze-frame from beat 3 to the swap)
def wt(f):
    """street world time in frames: normal, then ramps to 3 % speed over beat 3"""
    if f <= B[2]: return f
    a = B[2]; b = B[2] + 50
    if f <= b:
        u = (f - a) / (b - a); return a + (b - a) * (u - 0.485 * u * u)   # speed 1 -> 0.03
    return a + (b - a) * 0.515 + (f - b) * 0.03

# ------------------------------------------------------------------ hero rig
H = bpy.data.objects["Hero"]
R = make_human_ctrl(H); HU = Human(R)
HB = R.BN
def fingers(rig_pb, s, f, curl, thumb=None):
    for k in range(1, 6):
        for j in range(1, 4):
            n = f"finger{k}-{j}.{s}"
            if n not in rig_pb: continue
            a = (thumb if (k == 1 and thumb is not None) else curl) * (0.6 if k == 1 else 1.0) * (1.0 if j > 1 or k == 1 else 0.85)
            pb = rig_pb[n]; pb.rotation_mode = "QUATERNION"
            pb.rotation_quaternion = Quaternion((1, 0, 0), R_(a)); pb.keyframe_insert("rotation_quaternion", frame=f, group=n)

# feet planted: car floor and stage are both z = 0 at the same xy
FOOT = {"L": Vector((0.14, -0.02)), "R": Vector((-0.14, -0.02))}
STEP_R = Vector((-0.15, 0.08))     # right foot steps back half a pace in beat 2
def foot_R(f):
    if f < 200: return FOOT["R"], 0.0
    if f < 222:
        u = smooth((f - 200) / 22); return FOOT["R"].lerp(STEP_R, u), 0.06 * math.sin(math.pi * u)
    if f < 1150: return STEP_R, 0.0
    if f < 1170:   # set swap (hidden): feet back to neutral
        u = smooth((f - 1150) / 20); return STEP_R.lerp(FOOT["R"], u), 0.0
    return FOOT["R"], 0.0

# root/spine channels: (frame, value) keys on world-time for the street, plain frames for the hall
rx = pk([(1, 0.0), (60, 0.02), (120, -0.01), (F_IMPACT, 0.0), (F_IMPACT + 8, -0.03), (200, -0.06), (230, 0.03), (260, -0.01), (300, 0.0), (1190, 0.0), (1300, 0.02), (1400, -0.02), (1500, 0.0)])
ry = pk([(1, 0.0), (F_IMPACT, 0.0), (F_IMPACT + 6, 0.09), (200, 0.06), (240, 0.02), (300, 0.0), (1190, 0.0), (1300, -0.03), (1500, -0.02)])
rz = pk([(1, 0.0), (60, -0.01), (120, 0.0), (F_IMPACT, 0.0), (F_IMPACT + 10, -0.05), (205, -0.07), (250, -0.02), (300, 0.0), (1190, 0.0), (1290, -0.02), (1330, 0.0), (1380, -0.03), (1420, 0.0), (1500, -0.01)])
ryaw = pk([(1, 10.0), (60, -12.0), (120, 8.0), (F_IMPACT, 5.0), (190, -8.0), (260, 4.0), (330, 0.0), (1190, 0.0), (1300, 12.0), (1380, -14.0), (1450, 6.0), (1500, 0.0)])
rflex = pk([(1, 0.0), (F_IMPACT, 0.0), (F_IMPACT + 6, -12.0), (205, 6.0), (250, -2.0), (300, -4.0), (1190, 0.0), (1290, 6.0), (1330, 10.0), (1380, 4.0), (1420, 12.0), (1500, 4.0)])
rside = pk([(1, 0.0), (F_IMPACT, 0.0), (190, -5.0), (215, 6.0), (245, -2.0), (300, 0.0), (1500, 0.0)])
sflex = pk([(1, 2.0), (F_IMPACT, 2.0), (F_IMPACT + 5, -18.0), (200, 10.0), (240, -6.0), (300, -8.0), (1190, -4.0), (1260, -10.0), (1300, 8.0), (1340, 14.0), (1380, 4.0), (1420, 16.0), (1500, 6.0)])
stw = pk([(1, -8.0), (60, 12.0), (120, -6.0), (F_IMPACT, -4.0), (F_IMPACT + 6, -14.0), (210, 6.0), (300, 0.0), (1190, 0.0), (1260, -10.0), (1320, 14.0), (1380, -12.0), (1440, 10.0), (1500, 0.0)])
hpitch = pk([(1, -4.0), (F_IMPACT, -2.0), (F_IMPACT + 5, -14.0), (205, 10.0), (260, -6.0), (300, -8.0), (1190, 0.0), (1230, -14.0), (1290, 4.0), (1340, -8.0), (1400, 6.0), (1450, -10.0), (1500, -4.0)])
hyaw = pk([(1, -10.0), (60, 18.0), (120, -16.0), (F_IMPACT, -20.0), (200, 10.0), (260, -6.0), (300, 0.0), (1190, 0.0), (1250, 10.0), (1320, -16.0), (1380, 18.0), (1440, -10.0), (1500, 0.0)])

# hands (world wrist targets)
def wave_R(f):   # hat waving arc above the head
    a = math.sin(2 * math.pi * f / 42.0)
    return Vector((-0.36 + 0.10 * a, -0.16, 1.86 + 0.05 * abs(a)))
RAIL = Vector((0.26, -0.10, 0.99))            # brass grab rail on the front seat back
POCKET_REACH = Vector((-0.06, -0.30, 1.24))
hR_keys = [(1, wave_R(1)), (F_IMPACT, wave_R(F_IMPACT)), (F_IMPACT + 6, Vector((-0.42, -0.18, 1.5))), (195, Vector((-0.40, -0.12, 1.0))),
           (240, Vector((-0.33, -0.10, 0.92))), (300, Vector((-0.30, -0.08, 0.90))), (1150, Vector((-0.30, -0.08, 0.90))),
           (1185, Vector((-0.20, -0.30, 1.05))), (1205, POCKET_REACH), (1216, POCKET_REACH + Vector((0.0, 0.0, 0.0))),
           (1238, Vector((-0.30, -0.42, 1.45))), (1262, Vector((-0.30, -0.30, 1.98))), (1285, Vector((-0.30, -0.30, 2.0))),
           (1310, Vector((-0.26, -0.45, 1.35))), (1360, Vector((-0.22, -0.44, 1.22))), (1420, Vector((-0.30, -0.42, 1.40))), (1500, Vector((-0.24, -0.44, 1.25)))]
hL_keys = [(1, Vector((0.30, -0.12, 0.95))), (60, Vector((0.36, -0.30, 1.2))), (100, Vector((0.32, -0.20, 1.05))), (F_IMPACT, Vector((0.31, -0.14, 1.0))),
           (F_IMPACT + 7, Vector((0.48, -0.10, 1.25))), (188, RAIL + Vector((0, 0, 0.06))), (196, RAIL), (1150, RAIL), (1180, Vector((0.32, -0.25, 1.05))),
           (1192, Vector((0.24, -0.37, 1.13))), (1285, Vector((0.24, -0.37, 1.13))), (1300, Vector((0.36, -0.30, 1.75))), (1318, Vector((0.38, -0.28, 1.88))),
           (1336, Vector((0.36, -0.30, 1.70))), (1352, Vector((0.38, -0.28, 1.90))), (1372, Vector((0.24, -0.40, 1.16))), (1388, Vector((0.24, -0.40, 1.16))),
           (1410, Vector((0.37, -0.30, 1.86))), (1430, Vector((0.38, -0.28, 1.96))), (1460, Vector((0.37, -0.30, 1.84))), (1500, Vector((0.38, -0.28, 1.92)))]
hR = pk(hR_keys); hL = pk(hL_keys)
def hand_R(f):
    if f < F_IMPACT: return wave_R(f)
    return hR(f)
def hand_frame_R(f):  # (dir to fingers, palm normal)
    if f < F_IMPACT + 4: return Vector((0, 0.2, 1)), Vector((0.3, -1, 0))        # hand up, palm forward
    if 1195 <= f <= 1225: return Vector((0.3, 0.6, -0.3)), Vector((1, 0, 0))     # slipping into the coat
    if f > 1225: return Vector((0.1, -0.2, 1)), Vector((-0.2, -1, 0)) if f < 1300 else Vector((0.4, 0.2, -1))
    return Vector((0, -0.2, -1)), Vector((1, 0, 0))
def hand_frame_L(f):
    if 190 <= f <= 1170: return Vector((0.2, -1, -0.6)), Vector((0, 0, -1))       # gripping the rail, palm down
    if 1190 <= f <= 1290 or 1365 <= f <= 1395: return Vector((0, -1, -0.4)), Vector((0, 0, -1))   # on the podium edge
    if f > 1290: return Vector((0, 0, 1)), Vector((0, -1, 0))                     # raised fist
    return Vector((0, -0.2, -1)), Vector((-1, 0, 0))

for f in range(1, END + 1, 2):
    w = wt(f) if f < F_SWAP else f
    if f >= F_SWAP and f < 1190: w = 1190 if f > 1170 else wt(f)
    xyR, lift = foot_R(f)
    HU.key_foot("L", f, FOOT["L"], 0.0); HU.key_foot("R", f, xyR, 0.0, lift)
    pos = Vector((rx(w), ry(w), HB["root"].head_local.z + rz(w)))
    HU.key_root(f, pos, yaw=ryaw(w) * 0.25, flex=rflex(w) * 0.5, side=rside(w))
    breath = 1.5 * math.sin(2 * math.pi * w / 200.0)
    HU.key_spine(f, flex=sflex(w) + breath, twist=stw(w) * 0.6, side=rside(w) * 0.5, head=(hpitch(w), hyaw(w)))
    pr = Vector((-0.55, 0.45, 1.0)); pl = Vector((0.55, 0.45, 1.0))
    HU.key_hand("R", f, hand_R(w), *hand_frame_R(w), pole=pr)
    HU.key_hand("L", f, hL(w), *hand_frame_L(w), pole=pl)
    if "jaw" in R.PB:   # speaking in beat 9 (and a gasp at the hit)
        j = 0.0
        if f > 1240: j = 7 * max(0.0, math.sin(2 * math.pi * f / 11.0)) * (0.6 + 0.4 * math.sin(f / 23.0))
        elif F_IMPACT < w < F_IMPACT + 30: j = 9 * math.sin(math.pi * (w - F_IMPACT) / 30)
        R.key_rot("jaw", f, [("X", j)])
for f, cr, cl in ((1, 70, 25), (F_IMPACT + 4, 70, 25), (F_IMPACT + 10, 30, 45), (188, 20, 30), (198, 20, 80), (1170, 20, 80), (1182, 20, 30),
                  (1192, 20, 25), (1204, 25, 25), (1216, 75, 25), (1290, 75, 25), (1300, 75, 95), (1365, 75, 95), (1372, 75, 25), (1395, 75, 25), (1405, 75, 95), (1500, 75, 95)):
    fingers(R.PB, "R", f, cr); fingers(R.PB, "L", f, cl)

# ------------------------------------------------------------------ head items: spectacles + moustache (Child Of head bone)
def child_of(o, rig, bone, f_set, from_rest=False):
    sc.frame_set(f_set)
    if from_rest:   # o was placed in rest-pose coordinates: carry it onto the posed bone first
        o.matrix_world = rig.matrix_world @ rig.pose.bones[bone].matrix @ rig.data.bones[bone].matrix_local.inverted() @ o.matrix_world
    c = o.constraints.new("CHILD_OF"); c.target = rig; c.subtarget = bone
    c.inverse_matrix = (rig.matrix_world @ rig.pose.bones[bone].matrix).inverted()
    return c
sc.frame_set(1)
headM = H.matrix_world @ R.PB["head"].matrix
def head_pt(v): return headM @ (HB["head"].matrix_local.inverted() @ Vector(v))
wire = bpy.data.materials.new("SpecWire"); wire.use_nodes = True
bw = wire.node_tree.nodes["Principled BSDF"]; bw.inputs["Base Color"].default_value = (0.5, 0.42, 0.25, 1); bw.inputs["Metallic"].default_value = 1; bw.inputs["Roughness"].default_value = 0.25
lens_m = bpy.data.materials.new("SpecLens"); lens_m.use_nodes = True
bl_ = lens_m.node_tree.nodes["Principled BSDF"]; bl_.inputs["Transmission Weight"].default_value = 1.0; bl_.inputs["Roughness"].default_value = 0.0; bl_.inputs["IOR"].default_value = 1.5
specs = []
_ev = next(o for o in H.children if o.name.endswith("high-poly"))
_vs = [_ev.matrix_world @ v.co for v in _ev.data.vertices]
EX = max(abs(v.x) for v in _vs) / 2 + 0.002; EY = min(v.y for v in _vs); EZ = sum(v.z for v in _vs) / len(_vs)
print("EYES", EX, EY, EZ)
def E(x, y, z): return (x, EY + y, EZ + z)
for sx in (-1, 1):
    # rest-pose eye centre (from the eye mesh): x = +-0.0325, front of eyes y = -0.143, z = 1.622; lenses 1.4 cm in front
    bpy.ops.mesh.primitive_torus_add(major_radius=0.018, minor_radius=0.0011, major_segments=40, minor_segments=8,
                                     location=E(sx * EX, -0.02, 0), rotation=(R_(90), 0, 0))
    t = bpy.context.object; t.name = f"SpecRim{sx}"; t.data.materials.append(wire); specs.append(t)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.0175, depth=0.0012, location=E(sx * EX, -0.02, 0), rotation=(R_(90), 0, 0), vertices=32)
    t = bpy.context.object; t.name = f"SpecLens{sx}"; t.data.materials.append(lens_m); specs.append(t)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.0009, depth=0.10, location=E(sx * (EX + 0.038), 0.031, 0.006), rotation=(R_(90), 0, 0), vertices=8)
    t = bpy.context.object; t.name = f"SpecArm{sx}"; t.data.materials.append(wire); specs.append(t)
bpy.ops.mesh.primitive_cylinder_add(radius=0.001, depth=0.03, location=E(0, -0.023, 0.006), rotation=(0, R_(90), 0), vertices=8)
t = bpy.context.object; t.name = "SpecBridge"; t.data.materials.append(wire); specs.append(t)
# moustache: a bushy walrus moustache (dense short hair strands on a hidden lip patch)
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.03, segments=24, ring_count=12, location=E(0, -0.009, -0.054))
mo = bpy.context.object; mo.name = "Moustache"; mo.scale = (1.55, 0.42, 0.42); bpy.ops.object.transform_apply(scale=True)
for v in mo.data.vertices:
    v.co.z -= 0.25 * (v.co.x / 0.046) ** 2 * 0.02    # droop at the ends
hairm = bpy.data.materials.new("MoustacheHair"); hairm.use_nodes = True
hb = hairm.node_tree.nodes["Principled BSDF"]; hb.inputs["Base Color"].default_value = (0.09, 0.06, 0.045, 1); hb.inputs["Roughness"].default_value = 0.7
mo.data.materials.append(hairm)
dsp = mo.modifiers.new("Bristle", "DISPLACE"); tx = bpy.data.textures.new("Bristle", "STUCCI"); tx.noise_scale = 0.004; dsp.texture = tx; dsp.strength = 0.003
bpy.ops.object.shade_smooth(); specs.append(mo)
for o in specs:
    for c_ in list(o.users_collection): c_.objects.unlink(o)
    sc.collection.objects.link(o)
    child_of(o, H, "head", 1, from_rest=True)

# ------------------------------------------------------------------ brass grab rail on the front seat back
brass = bpy.data.materials.get("Brass")
for nm, loc, rot, dep in (("GrabRail", (0.26, 0.0, 0.99), (R_(90), 0, 0), 0.9), ("GrabPostA", (0.26, -0.42, 0.81), (0, 0, 0), 0.36), ("GrabPostB", (0.26, 0.42, 0.81), (0, 0, 0), 0.36)):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.014, depth=dep, location=loc, rotation=rot, vertices=16)
    o = bpy.context.object; o.name = nm; o.data.materials.append(brass); bpy.ops.object.shade_smooth()
    for c in list(o.users_collection): c.objects.unlink(o)
    C_STREET.objects.link(o)

# ------------------------------------------------------------------ hat prop: a static copy of the CrowdA fedora, held then dropped
src = bpy.data.objects["CrowdA.fedora01"]
hat = src.copy(); hat.data = src.data.copy(); hat.name = "HeroHat"; hat.parent = None; hat.modifiers.clear()
for c in list(hat.users_collection): c.objects.unlink(hat)
C_STREET.objects.link(hat)
hat.matrix_world = Matrix.Identity(4)
mn = Vector([min(v.co[i] for v in hat.data.vertices) for i in range(3)]); mx = Vector([max(v.co[i] for v in hat.data.vertices) for i in range(3)])
hat.data.transform(Matrix.Translation(-(mn + mx) / 2))
for m in hat.data.materials:
    for nd in m.node_tree.nodes:
        if nd.type == "BSDF_PRINCIPLED": nd.inputs["Base Color"].default_value = (0.03, 0.03, 0.03, 1)
# held by the brim in the right hand until the hit, then free fall onto the car floor
sc.frame_set(1)
def wrist_w(s): pb = R.PB["wrist." + s]; return H.matrix_world @ pb.matrix
hc = hat.constraints.new("CHILD_OF"); hc.target = H; hc.subtarget = "wrist.R"
for f, inf in ((1, 1.0), (F_IMPACT + 3, 1.0), (F_IMPACT + 4, 0.0)):
    hc.influence = inf; hc.keyframe_insert("influence", frame=f)
Wr = wrist_w("R"); hat_off = Matrix.Translation(Vector((0.0, 0.0, 0.0)))
hat.matrix_world = Wr @ Matrix.Translation(Vector((0, 0.13, 0.03))) @ Matrix.Rotation(R_(90), 4, "X")
hc.inverse_matrix = Wr.inverted()
local = hat.matrix_basis.copy()
# free-fall keys (constraint off): start where the hand left it
sc.frame_set(F_IMPACT + 3)
start = (H.matrix_world @ R.PB["wrist.R"].matrix) @ Wr.inverted() @ (Wr @ Matrix.Translation(Vector((0, 0.13, 0.03))) @ Matrix.Rotation(R_(90), 4, "X"))
p0 = start.to_translation(); e0 = start.to_euler()
hat.rotation_mode = "XYZ"
land = Vector((-0.55, -0.62, STREET_Z + 0.06))   # tumbles over the door onto the street
for f in range(F_IMPACT + 4, F_OUT, 2):
    w = wt(f) - (F_IMPACT + 4); T = w / 60.0
    tl = math.sqrt(2 * (p0.z - land.z) / 9.81) * 1.25
    u = min(1.0, T / tl)
    p = p0.lerp(land, u); p.z = p0.z + (land.z - p0.z) * u * u + 0.25 * math.sin(math.pi * u) * (1 - u)
    if u >= 1.0: p = land
    hat.location = p; hat.rotation_euler = (e0.x + 4.0 * u, e0.y + 1.2 * u, e0.z + 2.5 * u) if u < 1 else (0, 0, 0.6)
    hat.keyframe_insert("location", frame=f); hat.keyframe_insert("rotation_euler", frame=f)
hat.location = p0; hat.rotation_euler = e0
sc.frame_set(1); hat.keyframe_insert("location", frame=1); hat.keyframe_insert("rotation_euler", frame=1)
hat.keyframe_insert("location", frame=F_IMPACT + 3); hat.keyframe_insert("rotation_euler", frame=F_IMPACT + 3)

# ------------------------------------------------------------------ pocket / wound anchor on the chest (spine01), from the frozen pose
sc.frame_set(400)
suit = next(o for o in H.children if "elegantsuit" in o.name)
dg = bpy.context.evaluated_depsgraph_get(); se = suit.evaluated_get(dg)
Mi = suit.matrix_world.inverted()
def chest_hit(x, z):
    ok, loc, nrm, idx = se.ray_cast(Mi @ Vector((x, -1.0, z)), (Mi.to_3x3() @ Vector((0, 1, 0))).normalized())
    return (suit.matrix_world @ loc, (suit.matrix_world.to_3x3() @ nrm).normalized()) if ok else (None, None)
P0, N0 = chest_hit(-0.10, 1.29)
print("POCKET", P0, N0)
sp01 = H.matrix_world @ R.PB["spine01"].matrix
Pocket = bpy.data.objects.new("PocketAnchor", None); C_STUDIO.objects.link(Pocket)
Pocket.matrix_world = Matrix.Translation(P0) @ Vector((0, -1, 0)).rotation_difference(N0).to_matrix().to_4x4()
child_of(Pocket, H, "spine01", 400)
PW = Pocket.matrix_world.copy()
def PL(v):   # pocket-local -> world (frozen pose)
    return PW @ Vector(v)

# wound decal on the suit and body: small hole + dark spot, keyed in at the hit
wound = bpy.data.objects.new("WoundEmpty", None); C_STUDIO.objects.link(wound)
wound.location = PL((0.01, 0.0, -0.02)); child_of(wound, H, "spine01", 400)
# x-ray centre
xc = bpy.data.objects.new("XRayCenter", None); C_STUDIO.objects.link(xc); xc.location = PL((0, 0.03, 0)); child_of(xc, H, "spine01", 400)
XRAY = ((1, 0.0), (B[3] + 10, 0.0), (B[3] + 45, 1.0), (1165, 1.0), (1205, 0.0))
WOUND = ((1, 0.0), (F_IMPACT, 0.0), (F_IMPACT + 2, 1.0), (END, 1.0))
done = set()
for ob in [o for o in H.children if o.type == "MESH"]:
    for m in ob.data.materials:
        if not m or m.name in done or not m.node_tree: continue
        done.add(m.name); nt = m.node_tree; n, l = nt.nodes, nt.links
        o_ = next((x for x in n if x.type == "OUTPUT_MATERIAL" and x.is_active_output), None)
        if not o_ or not o_.inputs["Surface"].links: continue
        srcs = o_.inputs["Surface"].links[0].from_socket
        if "elegantsuit" in m.name or "body" in m.name:
            tcw = n.new("ShaderNodeTexCoord"); tcw.object = wound
            lw = n.new("ShaderNodeVectorMath"); lw.operation = "LENGTH"; l.new(tcw.outputs["Object"], lw.inputs[0])
            spot = n.new("ShaderNodeMapRange"); spot.inputs["From Min"].default_value = 0.006; spot.inputs["From Max"].default_value = 0.028
            spot.inputs["To Min"].default_value = 1.0; spot.inputs["To Max"].default_value = 0.0; l.new(lw.outputs["Value"], spot.inputs["Value"])
            wa = n.new("ShaderNodeValue"); wa.name = "WoundAmt"
            for f_, v_ in WOUND: wa.outputs[0].default_value = v_; wa.outputs[0].keyframe_insert("default_value", frame=f_)
            mu = n.new("ShaderNodeMath"); mu.operation = "MULTIPLY"; l.new(spot.outputs["Result"], mu.inputs[0]); l.new(wa.outputs[0], mu.inputs[1])
            dk = n.new("ShaderNodeBsdfPrincipled"); dk.inputs["Base Color"].default_value = (0.035, 0.012, 0.01, 1); dk.inputs["Roughness"].default_value = 0.9
            mxw = n.new("ShaderNodeMixShader"); l.new(mu.outputs[0], mxw.inputs["Fac"]); l.new(srcs, mxw.inputs[1]); l.new(dk.outputs["BSDF"], mxw.inputs[2])
            srcs = mxw.outputs["Shader"]
        # x-ray: porthole fully clear around the pocket, glass ghost elsewhere
        tc = n.new("ShaderNodeTexCoord"); tc.object = xc
        ln = n.new("ShaderNodeVectorMath"); ln.operation = "LENGTH"; l.new(tc.outputs["Object"], ln.inputs[0])
        mr = n.new("ShaderNodeMapRange"); mr.inputs["From Min"].default_value = 0.10; mr.inputs["From Max"].default_value = 0.22
        mr.inputs["To Min"].default_value = 1.0; mr.inputs["To Max"].default_value = 0.0; l.new(ln.outputs["Value"], mr.inputs["Value"])
        tr = n.new("ShaderNodeBsdfTransparent")
        fr = n.new("ShaderNodeLayerWeight"); fr.inputs["Blend"].default_value = 0.25
        em = n.new("ShaderNodeEmission"); em.inputs["Color"].default_value = (0.55, 0.9, 1.0, 1); em.inputs["Strength"].default_value = 0.8
        gm = n.new("ShaderNodeMixShader"); l.new(fr.outputs["Facing"], gm.inputs["Fac"]); l.new(tr.outputs["BSDF"], gm.inputs[1]); l.new(em.outputs["Emission"], gm.inputs[2])
        hole = n.new("ShaderNodeMixShader"); l.new(mr.outputs["Result"], hole.inputs["Fac"]); l.new(gm.outputs["Shader"], hole.inputs[1]); l.new(tr.outputs["BSDF"], hole.inputs[2])
        val = n.new("ShaderNodeValue"); val.name = "XRayFade"
        for f_, v_ in XRAY: val.outputs[0].default_value = v_; val.outputs[0].keyframe_insert("default_value", frame=f_)
        mx = n.new("ShaderNodeMixShader"); l.new(val.outputs[0], mx.inputs["Fac"]); l.new(srcs, mx.inputs[1]); l.new(hole.outputs["Shader"], mx.inputs[2])
        l.new(mx.outputs["Shader"], o_.inputs["Surface"])

# ------------------------------------------------------------------ cutaway props in the pocket (pocket-local: x right, -y out of the chest, z up)
MS = bpy.data.objects["Manuscript"]; GC = bpy.data.objects["GlassesCase"]; BL = bpy.data.objects["Bullet"]
SHEETS = sorted([o for o in MS.children if o.name.startswith("Sheet")], key=lambda o: o.name)
# stack normal (local +z) points out of the chest; sheet 49 outermost
MS.matrix_world = PW @ Matrix.Translation(Vector((-0.002, 0.032, -0.03))) @ Matrix.Rotation(R_(90), 4, "X")
c_sp = child_of(MS, H, "spine01", 400)
GC.matrix_world = PW @ Matrix.Translation(Vector((0.035, 0.047, -0.03))) @ Matrix.Rotation(R_(90), 4, "Y") @ Matrix.Rotation(R_(90), 4, "X")
child_of(GC, H, "spine01", 400)
# visible only inside the x-ray; the manuscript reappears in the hall in his hand
def vis(o, keys):
    for f_, h_ in keys:
        o.hide_render = h_; o.keyframe_insert("hide_render", frame=f_); o.hide_viewport = h_; o.keyframe_insert("hide_viewport", frame=f_)
for o in [GC] + list(GC.children): vis(o, ((1, True), (B[3] + 15, False), (1200, True)))
for o in [MS] + list(MS.children): vis(o, ((1, True), (B[3] + 15, False)))
# manuscript hand-off: pocket (spine01) -> right hand from the grasp at 1216
c_hand = MS.constraints.new("CHILD_OF"); c_hand.target = H; c_hand.subtarget = "wrist.R"
sc.frame_set(1216); c_hand.inverse_matrix = (H.matrix_world @ R.PB["wrist.R"].matrix).inverted() @ (H.matrix_world @ R.PB["spine01"].matrix) @ c_sp.inverse_matrix
for f_, a_, b_ in ((1, 1.0, 0.0), (1215, 1.0, 0.0), (1216, 0.0, 1.0)):
    c_sp.influence = a_; c_hand.influence = b_
    c_sp.keyframe_insert("influence", frame=f_); c_hand.keyframe_insert("influence", frame=f_)
# right hand reaches the manuscript's top edge in the pocket (1199-1216), re-keyed now that the pocket is known
for f in range(1197, 1219, 2):
    sc.frame_set(f)
    top = MS.matrix_world @ Vector((0.0, 0.08, 0.014))
    u = smooth((f - 1197) / 10.0)
    Wt = hR(1196).lerp(top + Vector((0.0, -0.025, 0.075)), u)
    HU.key_hand("R", f, Wt, Vector((0.05, 0.25, -1)), Vector((0, 1, 0)), pole=Vector((-0.55, 0.45, 1.0)))
c_hand.influence = 0.0; c_sp.influence = 1.0
sc.frame_set(1216); c_hand.inverse_matrix = (H.matrix_world @ R.PB["wrist.R"].matrix).inverted() @ (H.matrix_world @ R.PB["spine01"].matrix) @ c_sp.inverse_matrix
# paper hole: charred ring + clear hole through every sheet after the bullet passes (paper material, object coords of HoleEmpty)
hole_e = bpy.data.objects.new("HoleEmpty", None); C_STUDIO.objects.link(hole_e); hole_e.parent = MS
HP_LOCAL = Vector((0.012, 0.01, 0.0))
hole_e.location = HP_LOCAL
pm = bpy.data.materials["Paper"]; nt = pm.node_tree; n, l = nt.nodes, nt.links
o_ = n["Material Output"]; srcs = o_.inputs["Surface"].links[0].from_socket
tc = n.new("ShaderNodeTexCoord"); tc.object = hole_e
sxy = n.new("ShaderNodeSeparateXYZ"); l.new(tc.outputs["Object"], sxy.inputs[0])
cxy = n.new("ShaderNodeCombineXYZ"); l.new(sxy.outputs["X"], cxy.inputs["X"]); l.new(sxy.outputs["Y"], cxy.inputs["Y"])
ln = n.new("ShaderNodeVectorMath"); ln.operation = "LENGTH"; l.new(cxy.outputs["Vector"], ln.inputs[0])
nzh = n.new("ShaderNodeTexNoise"); nzh.inputs["Scale"].default_value = 900; l.new(tc.outputs["Object"], nzh.inputs["Vector"])
ad = n.new("ShaderNodeMath"); ad.operation = "MULTIPLY_ADD"; ad.inputs[1].default_value = 0.002; l.new(nzh.outputs["Fac"], ad.inputs[0]); l.new(ln.outputs["Value"], ad.inputs[2])
ha = n.new("ShaderNodeValue"); ha.name = "HoleAmt"
for f_, v_ in ((1, 0.0), (B[5], 0.0), (B[5] + 50, 1.0)): ha.outputs[0].default_value = v_; ha.outputs[0].keyframe_insert("default_value", frame=f_)
r_h = n.new("ShaderNodeMath"); r_h.operation = "MULTIPLY"; r_h.inputs[1].default_value = 0.0055; l.new(ha.outputs[0], r_h.inputs[0])
lt_ = n.new("ShaderNodeMath"); lt_.operation = "LESS_THAN"; l.new(ad.outputs[0], lt_.inputs[0]); l.new(r_h.outputs[0], lt_.inputs[1])
r_c = n.new("ShaderNodeMath"); r_c.operation = "MULTIPLY"; r_c.inputs[1].default_value = 0.0095; l.new(ha.outputs[0], r_c.inputs[0])
lc = n.new("ShaderNodeMath"); lc.operation = "LESS_THAN"; l.new(ad.outputs[0], lc.inputs[0]); l.new(r_c.outputs[0], lc.inputs[1])
char = n.new("ShaderNodeBsdfPrincipled"); char.inputs["Base Color"].default_value = (0.12, 0.08, 0.05, 1); char.inputs["Roughness"].default_value = 0.95
m1 = n.new("ShaderNodeMixShader"); l.new(lc.outputs[0], m1.inputs["Fac"]); l.new(srcs, m1.inputs[1]); l.new(char.outputs["BSDF"], m1.inputs[2])
trp = n.new("ShaderNodeBsdfTransparent")
m2 = n.new("ShaderNodeMixShader"); l.new(lt_.outputs[0], m2.inputs["Fac"]); l.new(m1.outputs["Shader"], m2.inputs[1]); l.new(trp.outputs["BSDF"], m2.inputs[2])
l.new(m2.outputs["Shader"], o_.inputs["Surface"])
# punch ripple per sheet as the bullet passes (outermost first)
T_IN, T_OUT = B[5] + 6, B[5] + 60
for k, s in enumerate(reversed(SHEETS)):
    kb = s.data.shape_keys.key_blocks["Punch"]; kb.slider_min = -1.0
    fk = T_IN + (T_OUT - T_IN) * (k / len(SHEETS)) ** 0.8
    for f_, v_ in ((1, 0.0), (fk - 2, 0.0), (fk + 3, -1.0), (fk + 30, -0.35), (END, -0.35)):
        kb.value = v_; kb.keyframe_insert("value", frame=int(f_))
# bullet: street flight, then the slow-motion replay inside the cutaway
SHOOTER = Vector((-1.15, -3.35, STREET_Z + 1.55))   # raised hand of the silhouette
sc.frame_set(F_IMPACT); HIT = wound.matrix_world.to_translation()
sc.frame_set(400)
HPw = MS.matrix_world @ HP_LOCAL            # where it crosses the stack
dirv = (HIT - SHOOTER).normalized()
sp_out = HPw - dirv * 0.06
CASEw = GC.matrix_world.to_translation()
case_hit = HPw + dirv * 0.032
stop = HPw + dirv * 0.062
BL.rotation_mode = "QUATERNION"; qd = Vector((0, 1, 0)).rotation_difference(dirv)
trail = bpy.data.objects["BulletTrail"]
for f in range(F_FLASH, F_IMPACT + 1):
    u = (f - F_FLASH) / (F_IMPACT - F_FLASH)
    BL.location = SHOOTER.lerp(HIT, u); BL.rotation_quaternion = qd
    BL.keyframe_insert("location", frame=f); BL.keyframe_insert("rotation_quaternion", frame=f)
bl_keys = [(B[5] - 10, sp_out - dirv * 0.03), (B[5] + 6, HPw - dirv * 0.004), (T_OUT, HPw + dirv * 0.03), (B[5] + 100, case_hit), (B[6] + 10, stop - dirv * 0.008), (B[6] + 60, stop)]
blf = pk(bl_keys)
for f in range(B[5] - 10, B[6] + 61, 2):
    BL.location = blf(f); BL.rotation_quaternion = qd @ Quaternion((0, 1, 0), R_(f * 6))
    BL.keyframe_insert("location", frame=f); BL.keyframe_insert("rotation_quaternion", frame=f)
for o in (BL, trail): vis(o, ((1, True), (F_FLASH, False), (F_IMPACT + 1, True), (B[5] - 10, False), (1180, True)))
for f_, h_ in ((1, False), (B[5] + 100, True)): trail.hide_render = h_; trail.keyframe_insert("hide_render", frame=f_)
# dent in the case when the bullet arrives
dk = GC.data.shape_keys.key_blocks["Dent"]
hl = GC.matrix_world.inverted() @ case_hit
for i, v in enumerate(GC.data.vertices):
    r = math.hypot(v.co.x - hl.x, v.co.y - hl.y)
    dk.data[i].co = v.co.copy()
    if v.co.z > 0: dk.data[i].co.z = v.co.z - 0.0065 * math.exp(-(r / 0.008) ** 2)
for f_, v_ in ((1, 0.0), (B[5] + 96, 0.0), (B[5] + 108, 1.0), (END, 1.0)): dk.value = v_; dk.keyframe_insert("value", frame=f_)
# paper flecks spraying back out of the entry hole
fm = pm
for i in range(36):
    bpy.ops.mesh.primitive_plane_add(size=0.0025)
    fl = bpy.context.object; fl.name = f"Fleck{i:02d}"; fl.data.materials.append(fm)
    for c in list(fl.users_collection): c.objects.unlink(fl)
    C_STUDIO.objects.link(fl)
    t0 = T_IN + random.uniform(0, 40); v = (-dirv * random.uniform(0.02, 0.06) + Vector([random.uniform(-0.04, 0.04) for _ in range(3)]))
    for f in range(int(t0) - 1, int(t0) + 120, 4):
        tt = max(0.0, (f - t0) / 60.0)
        fl.location = HPw - dirv * 0.002 + v * tt + Vector((0, 0, -0.01 * tt * tt))
        fl.rotation_euler = (tt * 7 + i, tt * 5, i); fl.keyframe_insert("location", frame=f); fl.keyframe_insert("rotation_euler", frame=f)
    vis(fl, ((1, True), (int(t0), False), (int(t0) + 120, True)))
# anatomy behind: ribs and lungs fitted to the thorax, muscle patch with the bullet resting short of the lung
sc.frame_set(400)
sp = H.matrix_world @ R.PB["spine02"].matrix
thor = (H.matrix_world @ R.PB["spine01"].head) * 0.5 + (H.matrix_world @ R.PB["neck01"].head) * 0.5
def fit(objs, size, center):
    import mathutils
    pts = [o.matrix_world @ Vector(c) for o in objs for c in o.bound_box]
    mn = Vector([min(p[i] for p in pts) for i in range(3)]); mx = Vector([max(p[i] for p in pts) for i in range(3)])
    d = mx - mn; s = min(size[i] / d[i] for i in range(3)); return s, (mn + mx) / 2
ribs = [o for o in C_STUDIO.objects if o.type == "MESH" and o.name.startswith(("Rib", "Spine2", "spine"))]
lungs = [o for o in C_STUDIO.objects if o.type == "MESH" and o.parent and o.parent.name.startswith("LungsSrc")] or [o for o in C_STUDIO.objects if o.type == "MESH" and o.name in ("0", "1")]
for grp, nm, size, cen in ((ribs, "RibsRoot", (0.33, 0.24, 0.34), thor + Vector((0, 0.0, -0.08))), (lungs, "LungsRoot", (0.26, 0.15, 0.25), thor + Vector((0, 0.02, -0.07)))):
    root = bpy.data.objects.new(nm, None); C_STUDIO.objects.link(root)
    bpy.context.view_layer.update()
    s, c0 = fit(grp, size, cen)
    for o in grp:
        Mw = o.matrix_world.copy(); o.parent = None; o.matrix_world = Mw
    for o in grp:
        o.matrix_world = Matrix.Translation(cen) @ Matrix.Scale(s, 4) @ Matrix.Translation(-c0) @ o.matrix_world
        o.parent = root; o.matrix_parent_inverse = root.matrix_world.inverted()
    child_of(root, H, "spine01", 400)
    for o in [root] + grp: vis(o, ((1, True), (B[6] - 40, False), (1180, True)))
    if nm == "LungsRoot":
        for f in range(B[6] - 40, 1181, 10):
            k = 1.0 + 0.03 * math.sin(2 * math.pi * f / 120.0); root.scale = (k, k, k); root.keyframe_insert("scale", frame=f)
mp = bpy.data.objects["MusclePatch"]; mp.location = stop + dirv * 0.004; mp.rotation_mode = "QUATERNION"; mp.rotation_quaternion = qd
child_of(mp, H, "spine01", 400); vis(mp, ((1, True), (B[6] - 20, False), (1180, True)))
gr = bpy.data.objects["GapRing"]; gr.location = stop + dirv * 0.02; gr.rotation_mode = "QUATERNION"; gr.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(dirv)
child_of(gr, H, "spine01", 400); vis(gr, ((1, True), (B[6] + 40, False), (1180, True)))
for f_, s_ in ((B[6] + 40, 0.2), (B[6] + 70, 1.0), (1180, 1.0)): gr.scale = (s_,) * 3; gr.keyframe_insert("scale", frame=f_)
# ------------------------------------------------------------------ studio dome + lights, set swap
dome = bpy.data.objects["StudioDome"]; dome.visible_shadow = True
sc.frame_set(400); dome.location = PL((0, 0.02, 0))
dfade = dome.data.materials[0].node_tree.nodes["DomeFade"]
for f_, v_ in ((1, 0.0), (B[3] + 15, 0.0), (B[3] + 60, 1.0), (1170, 1.0), (1205, 0.0)):
    dfade.outputs[0].default_value = v_; dfade.outputs[0].keyframe_insert("default_value", frame=f_)
vis(dome, ((1, True), (B[3] + 14, False), (1206, True)))
for nm in ("StudioKey", "StudioFill", "StudioRim"):
    lo = bpy.data.objects[nm]; e = lo.data.energy
    lo.location = PL(lo.location - Vector((-0.1, -0.2, 1.28))) if False else lo.location
    for f_, v_ in ((1, 0.0), (B[3] + 15, 0.0), (B[3] + 50, e), (1170, e), (1205, 0.0)):
        lo.data.energy = v_; lo.data.keyframe_insert("energy", frame=f_)
street_objs = [o for o in C_STREET.all_objects]; hall_objs = [o for o in C_HALL.all_objects]
for o in street_objs:
    o.hide_render = False; o.keyframe_insert("hide_render", frame=1); o.hide_render = True; o.keyframe_insert("hide_render", frame=F_OUT)
for o in hall_objs:
    o.hide_render = True; o.keyframe_insert("hide_render", frame=1); o.hide_render = False; o.keyframe_insert("hide_render", frame=F_IN)
wbg = sc.world.node_tree.nodes["Background"]
for f_, v_ in ((1, 0.05), (F_IN - 1, 0.05), (F_IN, 0.3)): wbg.inputs["Strength"].default_value = v_; wbg.inputs["Strength"].keyframe_insert("default_value", frame=f_)
# muzzle flash: emissive star card + light, 3 frames
flash_l = bpy.data.lights.new("MuzzleLight", "POINT"); flash_l.color = (1, 0.75, 0.4); flash_l.shadow_soft_size = 0.02
fo = bpy.data.objects.new("MuzzleLight", flash_l); fo.location = SHOOTER + dirv * 0.12; C_STREET.objects.link(fo)
for f_, e in ((1, 0), (F_FLASH - 1, 0), (F_FLASH, 4000), (F_FLASH + 2, 1500), (F_FLASH + 4, 0)): flash_l.energy = e; flash_l.keyframe_insert("energy", frame=f_)
bpy.ops.mesh.primitive_ico_sphere_add(radius=0.06, subdivisions=2, location=SHOOTER + dirv * 0.12)
fc_ = bpy.context.object; fc_.name = "MuzzleFlash"; fc_.scale = (1.0, 2.2, 1.0)
fc_.rotation_mode = "QUATERNION"; fc_.rotation_quaternion = qd
fc_.data.materials.append(bpy.data.materials.get("GasGlow"))
for c in list(fc_.users_collection): c.objects.unlink(fc_)
C_STREET.objects.link(fc_); vis(fc_, ((1, True), (F_FLASH, False), (F_FLASH + 4, True)))
# smoke puff after the flash
bpy.ops.mesh.primitive_ico_sphere_add(radius=0.1, subdivisions=3, location=SHOOTER + dirv * 0.15)
sm = bpy.context.object; sm.name = "GunSmoke"
smm = bpy.data.materials.new("Smoke"); smm.use_nodes = True; nt = smm.node_tree
for x in list(nt.nodes):
    if x.type == "BSDF_PRINCIPLED": nt.nodes.remove(x)
vol = nt.nodes.new("ShaderNodeVolumePrincipled"); vol.inputs["Density"].default_value = 3.0; vol.inputs["Color"].default_value = (0.6, 0.6, 0.62, 1)
nt.links.new(vol.outputs[0], nt.nodes["Material Output"].inputs["Volume"]); sm.data.materials.append(smm)
for c in list(sm.users_collection): c.objects.unlink(sm)
C_STREET.objects.link(sm); vis(sm, ((1, True), (F_FLASH + 1, False), (F_OUT, True)))
for f in range(F_FLASH + 1, F_OUT, 6):
    t = (wt(f) - F_FLASH) / 60.0; s_ = 0.4 + 2.5 * t; sm.scale = (s_,) * 3; sm.location = SHOOTER + dirv * 0.15 + Vector((0, 0, 0.25 * t))
    sm.keyframe_insert("scale", frame=f); sm.keyframe_insert("location", frame=f)
for f_, d_ in ((F_FLASH + 1, 3.0), (F_FLASH + 120, 0.6), (F_OUT, 0.4)): vol.inputs["Density"].default_value = d_; vol.inputs["Density"].keyframe_insert("default_value", frame=f_)
# wall clock hands spin (time passing) in beat 9
for nm, rate in (("ClockMinute", 1.0), ("ClockHour", 1 / 12)):
    o = bpy.data.objects[nm]; o.rotation_mode = "XYZ"
    for f_, a_ in ((1, 0.0), (B[8], 0.0), (END, -2 * math.pi * 1.5 * rate * 6)):
        o.rotation_euler = (0, a_, 0); o.keyframe_insert("rotation_euler", frame=f_)
# flags ripple
for i, f_ in enumerate([o for o in bpy.data.objects if o.name.startswith("Flag") and o.type == "MESH" and "Canton" not in o.name and "Pole" not in o.name]):
    dmod = f_.modifiers.get("Wave")
    if dmod:
        e = bpy.data.objects.new(f"FlagWind{i}", None); C_HALL.objects.link(e); dmod.texture_coords = "OBJECT"; dmod.texture_coords_object = e
        for fr_, x_ in ((1, 0.0), (END, 6.0 + i)): e.location = (x_, 0, x_ * 0.3); e.keyframe_insert("location", frame=fr_)
exec(open(HERE + "/03b_crowd_camera.py").read())
bpy.ops.wm.save_as_mainfile(filepath=out)
print("ANIM OK")
