# Part 2 of 03_animate.py (exec'd there): visibility, props, x-ray anatomy, FX, light grade, continuous camera.
import bmesh
random.seed(1717)
LADO = bpy.data.objects["Lad"]
f_fb0, SWIG_UP, SWIG_HOLD, SWIG_DOWN, f_fb1 = eval(sc["swig"])
f_r0, R_IMP, SLOW, f_r1 = eval(sc["replay"])
f_x0 = f_fb1
STUDIO = (f_x0, f_r1 - 7)                # world hidden only while the camera is inside the bubble
BUBBLE = (f_x0 - 16, f_r1 + 10)           # studio bubble visible (grows from his chest / collapses into it)

def set_const(idb):
    ad = idb.animation_data
    if not ad or not ad.action: return
    for layer in getattr(ad.action, "layers", []):
        for strip in layer.strips:
            for cb in strip.channelbags:
                for fc in cb.fcurves:
                    if fc.data_path in ("hide_render", "hide_viewport"):
                        for kp in fc.keyframe_points: kp.interpolation = 'CONSTANT'
def vis(o, ranges):
    """o visible only inside the given [f0, f1] ranges"""
    if o is None: return
    o.hide_render = True; o.hide_viewport = True
    o.keyframe_insert("hide_render", frame=1); o.keyframe_insert("hide_viewport", frame=1)
    for a, b in ranges:
        o.hide_render = False; o.hide_viewport = False
        o.keyframe_insert("hide_render", frame=a); o.keyframe_insert("hide_viewport", frame=a)
        o.hide_render = True; o.hide_viewport = True
        o.keyframe_insert("hide_render", frame=b + 1); o.keyframe_insert("hide_viewport", frame=b + 1)
    if ranges and ranges[0][0] <= 1:
        o.hide_render = False; o.hide_viewport = False
        o.keyframe_insert("hide_render", frame=1); o.keyframe_insert("hide_viewport", frame=1)
    set_const(o)
def hide_in(o, ranges):
    """o visible except inside the ranges"""
    keep = []; cur = 1
    for a, b in sorted(ranges):
        if a > cur: keep.append((cur, a - 1))
        cur = b + 1
    keep.append((cur, sc.frame_end + 10))
    vis(o, keep)

# ------------------------------------------------------------------ visibility plan
FLASH = (f_fb0, f_fb1 - 1)
for o in list(bpy.data.collections["Set"].all_objects) + [bpy.data.objects["Sun"]]:
    hide_in(o, [STUDIO])
for o in list(bpy.data.collections["Train"].all_objects):
    hide_in(o, [(f_fb0, f_r1)])
for o in list(bpy.data.collections["Studio"].all_objects):
    vis(o, [BUBBLE])
for nm in ("WitA", "WitB", "Worker"):
    for o in [bpy.data.objects[nm]] + list(bpy.data.objects[nm].children):
        hide_in(o, [(f_fb0, f_r1)])
DOME = bpy.data.objects["StudioCyc"]
CHEST_IN = V(2.45, -40.1, 1.3); CHEST_OUT = V(2.45, -40.35, 0.95)
def key_dome(f, s_, chest):
    s_ = max(0.001, s_)
    DOME.scale = (s_, s_, s_); DOME.location = V(2.4, -40.0, 0.0).lerp(chest, max(0.0, 1 - s_ / 0.35))
    DOME.keyframe_insert("scale", frame=f); DOME.keyframe_insert("location", frame=f)
for k in range(0, 23, 2):
    u = k / 22.0; key_dome(f_x0 - 16 + k, 0.003 + 0.997 * u ** 3, CHEST_IN)
for f_, s_ in ((f_r1 - 20, 1.0), (f_r1 - 12, 0.45), (f_r1 - 6, 0.18), (f_r1, 0.105), (f_r1 + 3, 0.1), (f_r1 + 7, 0.035), (f_r1 + 10, 0.002)):
    key_dome(f_, s_, CHEST_OUT)
# Lad: clothes/hair/eyes off in the x-ray (the body goes translucent)
XRAY = (f_x0, f_r1)
for o in LADO.children:
    if o.type == 'MESH' and not o.name.endswith(".body"):
        hide_in(o, [XRAY])
hide_in(bpy.data.objects["Lad.body"], [(f_r1 - 18, f_r1)])     # the replay body leaves while the bubble shrinks; he reappears standing inside it

# ------------------------------------------------------------------ helpers: bone attach + bake to a bone
def bone_world(rig, bn):
    return rig.matrix_world @ rig.pose.bones[bn].matrix
def attach_bone(o, rig, bn, M_world_rest):
    """parent o to a bone; M_world_rest is o's world matrix with the rig in rest pose"""
    rig.data.pose_position = 'REST'; bpy.context.view_layer.update()
    o.parent = rig; o.parent_type = 'BONE'; o.parent_bone = bn
    pb = rig.pose.bones[bn]
    tail = rig.matrix_world @ pb.matrix @ Matrix.Translation((0, pb.bone.length, 0))
    o.matrix_parent_inverse = tail.inverted()
    o.matrix_basis = M_world_rest
    rig.data.pose_position = 'POSE'; bpy.context.view_layer.update()

# hard hat on the worker's head bone
WKO = bpy.data.objects["Worker"]; hat = bpy.data.objects["HardHat"]
hb = WKO.data.bones["head"]
top = hb.head_local + (hb.tail_local - hb.head_local) * 1.0
attach_bone(hat, WKO, "head", Matrix.Translation(top + V(0, 0.005, -0.045)) @ Matrix.Rotation(R_(90), 4, 'Z') @ Matrix.Scale(1.12, 4))
hide_in(hat, [(f_fb0, f_r1)])
bpy.data.objects["Worker.short01"].animation_data_clear(); vis(bpy.data.objects["Worker.short01"], [])          # hair hidden under the hard hat

# palm cuts on Lad's left palm (metacarpal bone), visible from the walk-off
body = bpy.data.objects["Lad.body"]
LADO.data.pose_position = 'REST'; bpy.context.view_layer.update()
wr = LB.wr["L"]; mid = LADO.data.bones["finger3-1.L"].head_local
pc = wr.lerp(mid, 0.55); n_palm = LB.nn["L"]
dg = bpy.context.evaluated_depsgraph_get(); be = body.evaluated_get(dg)
inv = body.matrix_world.inverted()
hit, loc, nrm, idx = be.ray_cast(inv @ (pc + n_palm * 0.08), (inv.to_3x3() @ -n_palm).normalized())
LADO.data.pose_position = 'POSE'; bpy.context.view_layer.update()
palm_pt = body.matrix_world @ loc if hit else pc + n_palm * 0.015
print("PALM hit", hit, [round(v, 3) for v in palm_pt])
dpal = (mid - wr).normalized(); apal = n_palm.cross(dpal).normalized()
for k in range(3):
    cut = bpy.data.objects["PalmCut%d" % k]
    Rm = Matrix((apal, dpal, n_palm)).transposed().to_4x4() @ Matrix.Rotation(R_(25 + 12 * k), 4, 'Z')
    P = palm_pt + n_palm * 0.0016 + dpal * (0.012 * (k - 1)) + apal * (0.006 * (k - 1))
    attach_bone(cut, LADO, "metacarpal3.L", Matrix.Translation(P) @ Rm)
    vis(cut, [(f_r1 + 1, sc.frame_end)])

# bottle: in his right hand while he staggers (drops it at the trip, it rolls away), again in the flash-back swig
bot = bpy.data.objects["Bottle"]
GRIP = Matrix.Translation((0.0, 0.0, -0.13))          # bottle origin below the fist
def hand_bottle_matrix(f):
    sc.frame_set(f)
    M = bone_world(LADO, "wrist.R")
    # wrist bone: y along the hand; bottle axis along the palm, a little toward the fingers
    return M @ Matrix.Translation((0.0, 0.07, 0.0)) @ Matrix.Rotation(R_(-90), 4, 'Z') @ Matrix.Rotation(R_(90), 4, 'X') @ GRIP
def key_mat(o, f, M):
    o.matrix_world = M; o.keyframe_insert("location", frame=f); o.keyframe_insert("rotation_euler", frame=f)
bot.rotation_mode = 'XYZ'
f_drop = 120
for f in list(range(1, f_drop + 1, 2)):
    key_mat(bot, f, hand_bottle_matrix(f))
# drop: falls, bounces on the ballast, rolls toward the rail
M0 = hand_bottle_matrix(f_drop); p0 = M0.translation.copy(); e0 = M0.to_euler()
for i, f in enumerate(range(f_drop + 2, f_drop + 60, 2)):
    t = (f - f_drop) / FPS
    z = max(0.035, p0.z - 4.9 * t * t) if t < 0.4 else 0.035 + 0.06 * max(0, math.sin((t - 0.4) * 14)) * math.exp(-(t - 0.4) * 5)
    p = p0 + V(0.9 * t, -0.6 * t, 0); p.z = z
    bot.location = p; bot.rotation_euler = (math.radians(90), 0, e0.z + 3.5 * t)
    bot.keyframe_insert("location", frame=f); bot.keyframe_insert("rotation_euler", frame=f)
bot.keyframe_insert("location", frame=f_fb0 - 9); bot.keyframe_insert("rotation_euler", frame=f_fb0 - 9)   # it stays where it fell
for f in list(range(f_fb0 - 8, f_fb1, 2)):
    key_mat(bot, f, hand_bottle_matrix(f))
vis(bot, [(1, f_fb0 - 9), (f_fb0 - 8, f_fb1 - 1)])

# ------------------------------------------------------------------ hands grip, eyelids, birds
def key_local_rot(rig, n, f, deg):
    pb = rig.pose.bones[n]; pb.rotation_quaternion = Quaternion((1, 0, 0), math.radians(deg)); pb.keyframe_insert("rotation_quaternion", frame=f, group=n)
def ramp_keys(rig, names, pts):
    for f, deg in pts:
        for n, w_ in names:
            if n in rig.pose.bones: key_local_rot(rig, n, f, deg * w_)
FING_R = [("finger%d-%d.R" % (i, j), 0.6 if i == 1 else 1.0) for i in range(1, 6) for j in range(1, 4)]
ramp_keys(LADO, FING_R, [(1, 60), (f_drop - 2, 60), (f_drop + 4, 8), (f_fb0 - 14, 8), (f_fb0 - 8, 60), (f_fb1 - 2, 60), (f_fb1 + 4, 8)])
LIDS = [("orbicularis03.L", 1.0), ("orbicularis03.R", 1.0)]
f_land_ = int(eval(sc["lad_rest"]) and 0) or 0
f_shut = 262; f_open = sc["f_stir"] + 8
ramp_keys(LADO, LIDS, [(1, 18), (60, 26), (64, 6), (68, 22), (f_shut - 30, 22), (f_shut, 46), (f_open, 46), (f_open + 10, 20),
                       (f_open + 30, 10), (f_open + 34, 40), (f_open + 38, 12), (sc.frame_end - 120, 14), (sc.frame_end - 116, 38), (sc.frame_end - 112, 18)])
# hands (client, 23:00): relaxed curled default on every character, anatomical limits on fingers, thumbs and wrists
RIGS4 = [bpy.data.objects[n] for n in ("Lad", "WitA", "WitB", "Worker")]
def finger_names(rig, s_):
    return [b.name for b in rig.data.bones if b.name.startswith("finger") and b.name.endswith("." + s_)]
for rg in RIGS4:
    for pb in rg.pose.bones: pb.rotation_mode = 'QUATERNION'
    for s_ in "LR":
        for n in finger_names(rg, s_):
            pb = rg.pose.bones[n]
            thumb = n.startswith("finger1")
            c = pb.constraints.new('LIMIT_ROTATION'); c.owner_space = 'LOCAL'
            c.use_limit_x = c.use_limit_y = c.use_limit_z = True
            c.min_x, c.max_x = (math.radians(-5), math.radians(70)) if thumb else (0.0, math.radians(90))
            c.min_y, c.max_y = math.radians(-15 if thumb else -10), math.radians(15 if thumb else 10)
            c.min_z, c.max_z = math.radians(-20 if thumb else -10), math.radians(20 if thumb else 10)
        wb = rg.pose.bones["wrist." + s_]
        c = wb.constraints.new('LIMIT_ROTATION'); c.owner_space = 'LOCAL'; c.use_limit_x = c.use_limit_z = True
        c.min_x, c.max_x = math.radians(-60), math.radians(60); c.min_z, c.max_z = math.radians(-25), math.radians(25)
    # relaxed curl wherever the fingers are not already keyed (Lad's right hand keeps its bottle grip keys)
    keyed = set()
    ad_ = rg.animation_data
    if ad_ and ad_.action:
        for layer in getattr(ad_.action, "layers", []):
            for strip in layer.strips:
                for cb in strip.channelbags:
                    for fc in cb.fcurves:
                        if fc.data_path.startswith('pose.bones["finger'): keyed.add(fc.data_path.split('"')[1])
    for s_ in "LR":
        for n in finger_names(rg, s_):
            if n in keyed: continue
            j = int(n.split("-")[1].split(".")[0]); thumb = n.startswith("finger1")
            key_local_rot(rg, n, 1, (10 if thumb else 14 + 6 * j))
# Lad's open right hand (outside the bottle grips) also relaxes rather than going flat
FING_R = [("finger%d-%d.R" % (i, j), 0.6 if i == 1 else 1.0) for i in range(1, 6) for j in range(1, 4)]
ramp_keys(LADO, FING_R, [(f_drop + 4, 28), (f_fb0 - 14, 28), (f_fb1 + 4, 28)])
# faces: snore (jaw), horror (jaw drop), stunned/dazed lids, the final dopey grin
def key_jaw(rig, f, deg): key_local_rot(rig, "jaw", f, deg)
def key_grin(rig, f, k):
    for s_, sx_ in (("L", 1), ("R", -1)):
        for n in ("risorius03." + s_, "oris03." + s_, "oris04." + s_):
            if n not in rig.pose.bones: continue
            pb = rig.pose.bones[n]; Rl = pb.bone.matrix_local.to_3x3().inverted()
            pb.location = Rl @ V(sx_ * 0.008 * k, 0.004 * k, 0.008 * k); pb.keyframe_insert("location", frame=f, group=n)
key_jaw(LADO, 1, 3)
for f in range(f_shut, T_IMP, 6):
    key_jaw(LADO, f, 4 + 5 * max(0.0, math.sin(2 * math.pi * (f - f_shut) / 150.0)))      # snore: mouth drops on each breath
key_jaw(LADO, T_IMP, 8); key_jaw(LADO, sc["f_stir"], 6); key_jaw(LADO, sc["f_stir"] + 40, 10); key_jaw(LADO, sc["f_stir"] + 80, 3)
f_palm0_, f_palm1_ = eval(sc["palm"])
key_grin(LADO, 1, 0.0); key_grin(LADO, f_palm0_ + 36, 0.0); key_grin(LADO, f_palm0_ + 60, 0.55); key_grin(LADO, sc.frame_end, 0.6)
key_jaw(LADO, f_palm0_ + 50, 3); key_jaw(LADO, f_palm0_ + 75, 2)
for nm in ("WitA", "WitB", "Worker"):
    rg = bpy.data.objects[nm]
    for pb in rg.pose.bones: pb.rotation_mode = 'QUATERNION'
    key_jaw(rg, 1, 1); key_jaw(rg, T_IMP + 8, 1); key_jaw(rg, T_IMP + 20, 9); key_jaw(rg, T_IMP + 90, 3)
    key_jaw(rg, F(17.0), 4); key_jaw(rg, F(17.4), 13); key_jaw(rg, F(19.4), 11); key_jaw(rg, F(20.4), 16); key_jaw(rg, F(21.0), 8); key_jaw(rg, sc.frame_end, 7)
# birds on the fence lift off when he staggers by, and again at the horn
M_BIRD = bpy.data.materials.new("Bird"); M_BIRD.use_nodes = True
M_BIRD.node_tree.nodes["Principled BSDF"].inputs['Base Color'].default_value = (0.08, 0.08, 0.09, 1)
for k in range(9):
    bmg = bmesh.new()
    v = [bmg.verts.new(p_) for p_ in ((0, -0.09, 0), (0, 0.07, 0.01), (-0.17, 0.0, 0.0), (0.17, 0.0, 0.0), (0, 0.11, 0.0))]
    bmg.faces.new((v[0], v[2], v[1])); bmg.faces.new((v[0], v[1], v[3])); bmg.faces.new((v[1], v[2], v[4]))
    me = bpy.data.meshes.new("Bird%d" % k); bmg.to_mesh(me); bmg.free(); o = bpy.data.objects.new("Bird%d" % k, me); fx.objects.link(o) if 'fx' in dir() else sc.collection.objects.link(o)
    me.materials.append(M_BIRD)
    sk = o.shape_key_add(name="Basis"); up = o.shape_key_add(name="Up")
    for i in (2, 3): up.data[i].co.z += 0.12
    perch = V(9.5, random.uniform(-3, 8), 1.86); t0 = random.randint(40, 80) if k < 5 else random.randint(330, 380)
    d = V(random.uniform(0.3, 1.0), random.uniform(0.2, 1.0), 0.6).normalized()
    for f in [1, t0 - 1] + list(range(t0, min(sc.frame_end, t0 + 300), 3)):
        if f < t0: p_ = perch
        else:
            t = (f - t0) / FPS; p_ = perch + d * (4.5 * t) + V(0, 0, 1.2 * t * t)
        o.location = p_; o.rotation_euler = (0, 0, math.atan2(-d.x, d.y)); o.keyframe_insert("location", frame=f); o.keyframe_insert("rotation_euler", frame=f)
        up.value = 0.0 if f < t0 else 0.5 + 0.5 * math.sin((f - t0) * 1.3); up.keyframe_insert("value", frame=f)
    hide_in(o, [STUDIO, (f_fb0, f_fb1)])
# ------------------------------------------------------------------ x-ray: translucent body + loose "rope" muscles + skeleton
bm_ = body.data.materials[0]
nt = bm_.node_tree; outn = [n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL'][0]
srcs = outn.inputs['Surface'].links[0].from_socket
xr_tr = nt.nodes.new('ShaderNodeBsdfTransparent'); xr_em = nt.nodes.new('ShaderNodeEmission')
xr_em.inputs['Color'].default_value = (0.45, 0.85, 1.0, 1)
fres = nt.nodes.new('ShaderNodeLayerWeight'); fres.inputs['Blend'].default_value = 0.35
pw = nt.nodes.new('ShaderNodeMath'); pw.operation = 'POWER'; pw.inputs[1].default_value = 1.6
nt.links.new(fres.outputs['Facing'], pw.inputs[0])
emk = nt.nodes.new('ShaderNodeMath'); emk.operation = 'MULTIPLY'; emk.inputs[1].default_value = 4.0
nt.links.new(pw.outputs[0], emk.inputs[0]); nt.links.new(emk.outputs[0], xr_em.inputs['Strength'])
add = nt.nodes.new('ShaderNodeAddShader'); nt.links.new(xr_tr.outputs[0], add.inputs[0]); nt.links.new(xr_em.outputs[0], add.inputs[1])
mixx = nt.nodes.new('ShaderNodeMixShader'); XVAL = nt.nodes.new('ShaderNodeValue'); XVAL.name = "XRAY"; XVAL.label = "XRAY"
nt.links.new(XVAL.outputs[0], mixx.inputs['Fac']); nt.links.new(srcs, mixx.inputs[1]); nt.links.new(add.outputs[0], mixx.inputs[2])
nt.links.new(mixx.outputs[0], outn.inputs['Surface'])
for f, v in ((1, 0.0), (f_x0 - 10, 0.0), (f_x0 + 2, 1.0), (f_r1, 1.0), (f_r1 + 1, 0.0)):
    XVAL.outputs[0].default_value = v; XVAL.outputs[0].keyframe_insert("default_value", frame=f)
xr_em.inputs['Color'].default_value = (0.3, 0.75, 1.0, 1)
ad = bm_.node_tree.animation_data
for layer in getattr(ad.action, "layers", []):
    for strip in layer.strips:
        for cb in strip.channelbags:
            for fc in cb.fcurves:
                for kp in fc.keyframe_points: kp.interpolation = 'LINEAR' if kp.co.x <= f_x0 + 2 else 'CONSTANT'   # fade in, cut out (hidden in the bubble)

def mat_muscle(name, col, stripe=0.6):
    m = bpy.data.materials.new(name); m.use_nodes = True
    n, l = m.node_tree.nodes, m.node_tree.links; p = n["Principled BSDF"]
    tc = n.new('ShaderNodeTexCoord'); wv = n.new('ShaderNodeTexWave'); wv.inputs['Scale'].default_value = 40; wv.inputs['Distortion'].default_value = 3
    wv.wave_profile = 'SIN'; wv.bands_direction = 'X'
    l.new(tc.outputs['UV'], wv.inputs['Vector'])
    mr = n.new('ShaderNodeMapRange'); mr.inputs['To Min'].default_value = stripe; l.new(wv.outputs['Fac'], mr.inputs['Value'])
    mx = n.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs['A'].default_value = col + (1,); mx.inputs['B'].default_value = (1, 1, 1, 1)
    l.new(mr.outputs['Result'], mx.inputs['Factor'])
    mx.inputs['Factor'].default_value = 1.0
    l.new(mr.outputs['Result'], mx.inputs['B'])
    l.new(mx.outputs['Result'], p.inputs['Base Color'])
    p.inputs['Roughness'].default_value = 0.35; p.inputs['Subsurface Weight'].default_value = 0.4
    p.inputs['Subsurface Radius'].default_value = (0.6, 0.2, 0.1); p.inputs['Coat Weight'].default_value = 0.4
    return m
M_MUS = mat_muscle("XrayMuscle", (0.62, 0.07, 0.06), stripe=0.45)
_n = M_MUS.node_tree.nodes; _l = M_MUS.node_tree.links; _p = _n["Principled BSDF"]
_tc = [x for x in _n if x.type == 'TEX_COORD'][0]; _wv = [x for x in _n if x.type == 'TEX_WAVE'][0]
_mp = _n.new('ShaderNodeMapping'); _mp.inputs['Scale'].default_value = (3.0, 3.0, 0.25)
_l.new(_tc.outputs['Object'], _mp.inputs['Vector']); _l.new(_mp.outputs['Vector'], _wv.inputs['Vector']); _wv.inputs['Scale'].default_value = 60
_lw = _n.new('ShaderNodeLayerWeight'); _lw.inputs['Blend'].default_value = 0.4
_em = _n.new('ShaderNodeMath'); _em.operation = 'MULTIPLY'; _em.inputs[1].default_value = 1.6; _l.new(_lw.outputs['Facing'], _em.inputs[0])
_p.inputs['Emission Color'].default_value = (1.0, 0.16, 0.1, 1); _l.new(_em.outputs[0], _p.inputs['Emission Strength'])
_p.inputs['Coat Weight'].default_value = 0.7; _p.inputs['Coat Roughness'].default_value = 0.15
M_BONE = flat("XrayBone", (0.93, 0.9, 0.82), 0.45) if 'flat' in dir() else None
if M_BONE is None:
    M_BONE = bpy.data.materials.new("XrayBone"); M_BONE.use_nodes = True
    M_BONE.node_tree.nodes["Principled BSDF"].inputs['Base Color'].default_value = (0.93, 0.9, 0.82, 1)
    M_BONE.node_tree.nodes["Principled BSDF"].inputs['Roughness'].default_value = 0.45

DEFORM = [b.name for b in LADO.data.bones if b.use_deform]
def seg_dist(p, a, b):
    ab = b - a; t = max(0.0, min(1.0, (p - a).dot(ab) / max(1e-9, ab.dot(ab)))); return (a + ab * t - p).length
def skinned_tube(name, pts, radii, mat, bones, ring=10, cname="Xray"):
    """tube through pts (armature rest space), weights blended over the given bones by distance"""
    bmx = bmesh.new(); uv = bmx.loops.layers.uv.new("UVMap"); rings = []
    for i, (p, r) in enumerate(zip(pts, radii)):
        d = (pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]).normalized()
        a = d.orthogonal().normalized(); b = d.cross(a)
        rings.append([bmx.verts.new(p + (a * math.cos(2 * math.pi * k / ring) + b * math.sin(2 * math.pi * k / ring)) * r) for k in range(ring)])
    for i in range(len(rings) - 1):
        for k in range(ring):
            fce = bmx.faces.new((rings[i][k], rings[i][(k + 1) % ring], rings[i + 1][(k + 1) % ring], rings[i + 1][k]))
            for lp, (uu, vv) in zip(fce.loops, ((i, k), (i, k + 1), (i + 1, k + 1), (i + 1, k))):
                lp[uv].uv = (uu / (len(rings) - 1), vv / ring)
    bmx.faces.new(list(reversed(rings[0]))); bmx.faces.new(rings[-1])
    me = bpy.data.meshes.new(name); bmx.to_mesh(me); bmx.free()
    o = bpy.data.objects.new(name, me)
    if cname not in bpy.data.collections:
        c_ = bpy.data.collections.new(cname); sc.collection.children.link(c_)
    bpy.data.collections[cname].objects.link(o)
    me.materials.append(mat)
    for poly in me.polygons: poly.use_smooth = True
    segs = {bn: (LADO.data.bones[bn].head_local, LADO.data.bones[bn].tail_local) for bn in bones}
    groups = {bn: o.vertex_groups.new(name=bn) for bn in bones}
    for v_ in me.vertices:
        ds = {bn: seg_dist(v_.co, *segs[bn]) for bn in bones}
        ws = {bn: 1.0 / (d + 0.01) ** 4 for bn, d in ds.items()}; tot = sum(ws.values())
        for bn, w_ in ws.items():
            if w_ / tot > 0.02: groups[bn].add([v_.index], w_ / tot, 'REPLACE')
    o.parent = LADO
    am = o.modifiers.new("Armature", 'ARMATURE'); am.object = LADO
    sub = o.modifiers.new("Sub", 'SUBSURF'); sub.levels = 1; sub.render_levels = 1
    return o
def bpt(bn, t): b = LADO.data.bones[bn]; return b.head_local.lerp(b.tail_local, t)
def chain_pts(chain, n=8, off=V(0, 0, 0)):
    a = LADO.data.bones[chain[0]].head_local; b = LADO.data.bones[chain[-1]].tail_local
    return [a.lerp(b, i / (n - 1)) + off * math.sin(math.pi * i / (n - 1)) for i in range(n)]
XR_OBJS = []
for s in "LR":
    sx = 1 if s == "L" else -1
    arm_u = ["upperarm01." + s, "upperarm02." + s]; arm_l = ["lowerarm01." + s, "lowerarm02." + s]
    leg_u = ["upperleg01." + s, "upperleg02." + s]; leg_l = ["lowerleg01." + s, "lowerleg02." + s]
    # muscles: loose bundles (biceps, triceps, deltoid, forearm flexor/extensor, quads, hamstrings, calf, shin)
    for nm, ch, off, r in (("Biceps", arm_u, V(0, -0.035, 0), 0.026), ("Triceps", arm_u, V(0, 0.035, 0), 0.028),
                           ("Forearm1", arm_l, V(0, -0.02, 0.01), 0.022), ("Forearm2", arm_l, V(0, 0.02, -0.01), 0.02),
                           ("Quad1", leg_u, V(0, -0.05, 0), 0.05), ("Quad2", leg_u, V(sx * 0.035, -0.02, 0), 0.04),
                           ("Hamstring", leg_u, V(0, 0.045, 0), 0.045), ("Calf", leg_l, V(0, 0.04, 0), 0.04), ("Shin", leg_l, V(sx * 0.01, -0.02, 0), 0.022)):
        pts = chain_pts(ch, 9, off * 1.0)
        pts = [p + off * 0.4 for p in pts]
        radii = [r * (0.35 + 0.65 * math.sin(math.pi * i / 8) ** 0.7) for i in range(9)]
        XR_OBJS.append(skinned_tube("Mus_%s.%s" % (nm, s), pts, radii, M_MUS, ch))
    sh_ = bpt("upperarm01." + s, 0.0)
    XR_OBJS.append(skinned_tube("Mus_Deltoid.%s" % s, [bpt("clavicle." + s, 0.3) + V(0, 0, 0.02), sh_ + V(sx * 0.03, 0, 0.03), bpt("upperarm01." + s, 0.9) + V(sx * 0.02, 0, 0)],
                                [0.02, 0.04, 0.02], M_MUS, ["clavicle." + s, "shoulder01." + s, "upperarm01." + s]))
    # bones
    for ch, r in ((arm_u, 0.012), (arm_l, 0.01), (leg_u, 0.017), (leg_l, 0.014)):
        pts = chain_pts(ch, 5); XR_OBJS.append(skinned_tube("Bone_%s" % ch[0], pts, [r * 1.6, r, r, r, r * 1.6], M_BONE, ch, ring=8))
# torso: abdominals, pecs, back muscles, spine, ribs, skull
SP = ["spine05", "spine04", "spine03", "spine02", "spine01"]
for nm, off, r in (("Abs", V(0, -0.1, 0), 0.05), ("BackL", V(0.045, 0.08, 0), 0.035), ("BackR", V(-0.045, 0.08, 0), 0.035)):
    pts = [p + off for p in chain_pts(SP, 9)]
    XR_OBJS.append(skinned_tube("Mus_" + nm, pts, [r * (0.6 + 0.4 * math.sin(math.pi * i / 8)) for i in range(9)], M_MUS, SP))
for s in "LR":
    sx = 1 if s == "L" else -1
    c0 = bpt("spine01", 0.4) + V(sx * 0.02, -0.11, 0.02); c1 = bpt("upperarm01." + s, 0.2) + V(0, -0.04, -0.03)
    XR_OBJS.append(skinned_tube("Mus_Pec.%s" % s, [c0, c0.lerp(c1, 0.5) + V(0, -0.02, 0), c1], [0.035, 0.045, 0.02], M_MUS, ["spine01", "clavicle." + s, "upperarm01." + s]))
XR_OBJS.append(skinned_tube("Bone_Spine", chain_pts(SP + ["neck01", "neck02", "neck03"], 12, V(0, 0.02, 0)), [0.016] * 12, M_BONE, SP + ["neck01", "neck02", "neck03"], ring=8))
for k in range(7):
    z = bpt("spine02", 0.0).z + k * 0.045
    c_ = V(0, 0.0, z); rr = 0.12 - 0.006 * abs(k - 3)
    pts = [c_ + V(rr * math.cos(a), 0.09 * math.sin(a) - 0.01, -0.02 * math.cos(a)) for a in [math.radians(x) for x in range(-170, 171, 34)]]
    XR_OBJS.append(skinned_tube("Bone_Rib%d" % k, pts, [0.007] * len(pts), M_BONE, ["spine03", "spine02", "spine01"], ring=6))
hd = LADO.data.bones["head"]
skull_c = hd.head_local.lerp(hd.tail_local, 0.45) + V(0, 0.0, 0)
XR_OBJS.append(skinned_tube("Bone_Skull", [skull_c + V(0, 0, -0.1 + 0.2 * i / 6) for i in range(7)], [0.04, 0.075, 0.088, 0.09, 0.085, 0.065, 0.02], M_BONE, ["head"], ring=12))
pel = bpt("spine05", 0.0)
XR_OBJS.append(skinned_tube("Bone_Pelvis", [pel + V(x, 0.01, -0.03 + 0.03 * abs(x) / 0.14) for x in (-0.14, -0.07, 0, 0.07, 0.14)], [0.03, 0.035, 0.03, 0.035, 0.03], M_BONE, ["spine05", "root"], ring=8))
for o in XR_OBJS:
    bpy.data.objects.remove(o, do_unlink=True)
XR_OBJS = []
MUS = bpy.data.objects["XrayMuscles"]
for i in range(len(MUS.data.materials)): MUS.data.materials[i] = M_MUS
if not MUS.data.materials: MUS.data.materials.append(M_MUS)
XR_OBJS.append(MUS)
for o in XR_OBJS:
    if o.name.startswith("Mus_"):
        wm = o.modifiers.new("Ripple", 'WAVE'); wm.use_normal = True; wm.height = 0.004; wm.width = 0.06; wm.speed = 0.05; wm.time_offset = random.uniform(0, 30)
    o.animation_data_clear()          # drop the 'Lad children' x-ray keys first: one visibility track only
    vis(o, [(f_x0 - 6, f_r1 - 19)])

# ------------------------------------------------------------------ ghost replay set: ghost rails + ghost loco front + force arrows
R_HEAD = V(*eval(sc["replay_head"]))
GX = R_HEAD.x - 0.02 - GAUGE
M_GHOST = bpy.data.materials.new("Ghost"); M_GHOST.use_nodes = True
gn = M_GHOST.node_tree.nodes; gl = M_GHOST.node_tree.links
gp = gn["Principled BSDF"]; gp.inputs['Base Color'].default_value = (0.0, 0.25, 0.62, 1); gp.inputs['Alpha'].default_value = 0.45
gp.inputs['Emission Color'].default_value = (0.0, 0.6, 1.0, 1); gp.inputs['Emission Strength'].default_value = 1.0
_lw = gn.new('ShaderNodeLayerWeight'); _lw.inputs['Blend'].default_value = 0.12
_rm = gn.new('ShaderNodeMath'); _rm.operation = 'MULTIPLY'; _rm.inputs[1].default_value = 7.0; gl.new(_lw.outputs['Facing'], _rm.inputs[0])
_ad = gn.new('ShaderNodeMath'); _ad.operation = 'ADD'; _ad.inputs[1].default_value = 0.04; gl.new(_rm.outputs[0], _ad.inputs[0]); gl.new(_ad.outputs[0], gp.inputs['Emission Strength'])
_al = gn.new('ShaderNodeMath'); _al.operation = 'ADD'; _al.inputs[1].default_value = 0.38; gl.new(_lw.outputs['Facing'], _al.inputs[0]); gl.new(_al.outputs[0], gp.inputs['Alpha'])
M_ARROW = bpy.data.materials.new("ForceArrow"); M_ARROW.use_nodes = True
ap = M_ARROW.node_tree.nodes["Principled BSDF"]; ap.inputs['Base Color'].default_value = (0.0, 0.45, 0.9, 1)
ap.inputs['Emission Color'].default_value = (0.0, 0.55, 1.0, 1); ap.inputs['Emission Strength'].default_value = 1.6
ghost_coll = bpy.data.collections.new("Ghost"); sc.collection.children.link(ghost_coll)
for sx in (-1, 1):
    src = bpy.data.objects["Rail_AR"]
    bmg = bmesh.new()
    ring0 = [bmg.verts.new((GX + sx * GAUGE + x, STOP_Y - 11.0, z)) for x, z in [(-0.075, 0), (0.075, 0), (0.036, 0.13), (0.036, RAIL_H), (-0.036, RAIL_H), (-0.036, 0.13)]]
    ring1 = [bmg.verts.new((v_.co.x, STOP_Y + 11.0, v_.co.z)) for v_ in ring0]
    for i in range(6): bmg.faces.new((ring0[i], ring0[(i + 1) % 6], ring1[(i + 1) % 6], ring1[i]))
    me = bpy.data.meshes.new("GhostRail"); bmg.to_mesh(me); bmg.free(); go = bpy.data.objects.new("GhostRail%d" % sx, me); ghost_coll.objects.link(go)
    me.materials.append(M_GHOST); vis(go, [(f_r0, f_r1)])
loco = bpy.data.objects["Loco"]
GHOSTS = []
for src in (loco,):
    g = src.copy(); g.name = "Ghost" + src.name; g.parent = None; ghost_coll.objects.link(g)
    g.animation_data_clear()
    for sl in g.material_slots: sl.link = 'OBJECT'; sl.material = M_GHOST
    GHOSTS.append((g, src.matrix_local.copy()))
def ghost_front(f):
    fr = T_IMP + (f - R_IMP) / SLOW
    return R_HEAD.y + (train_front(fr) - HEAD_Y)
for f in list(range(f_r0, f_r1 + 1, 2)) + [f_r1]:
    y = ghost_front(f) - plough_off
    for g, ml in GHOSTS:
        g.matrix_world = Matrix.Translation((GX, y, 0)) @ ml
        g.keyframe_insert("location", frame=f)
for g, ml in GHOSTS:
    vis(g, [(f_r0, f_r1 - 28)])         # gone before the whip out, so the exit is not a white-out
# force arrows flowing along -Y around the body
def arrow(name, L_):
    bmg = bmesh.new()
    bmesh.ops.create_cone(bmg, cap_ends=True, segments=12, radius1=0.06, radius2=0.06, depth=L_ * 0.7,
                          matrix=Matrix.Translation((0, 0, L_ * 0.35)))
    bmesh.ops.create_cone(bmg, cap_ends=True, segments=12, radius1=0.16, radius2=0.0, depth=L_ * 0.3,
                          matrix=Matrix.Translation((0, 0, L_ * 0.85)))
    me = bpy.data.meshes.new(name); bmg.to_mesh(me); bmg.free(); o = bpy.data.objects.new(name, me); ghost_coll.objects.link(o)
    me.materials.append(M_ARROW); return o
ARROWS = []
for k in range(7):
    a = arrow("ForceArrow%d" % k, random.uniform(0.6, 0.9)); ARROWS.append((a, V(random.uniform(-0.2, 1.6), random.uniform(0.3, 1.4), random.uniform(0.2, 0.9)), random.uniform(0, 1)))
for f in list(range(R_IMP - 10, f_r1 + 1, 3)) + [f_r1]:
    fr = T_IMP + (f - R_IMP) / SLOW
    body_p, _ = drag_full(int(max(T_IMP, min(fr, f_rest))))
    body_p = body_p + (V(R_HEAD.x, R_HEAD.y, 0) - V(*eval(sc["head_rest"]))) ; body_p.z = 0.0
    for a, off, ph in ARROWS:
        cyc_ = ((f - R_IMP) / 90.0 + ph) % 1.0
        a.location = V(body_p.x - 0.6 + off.x, body_p.y + off.y + 1.2 - 2.4 * cyc_, off.z)
        a.rotation_euler = (math.radians(90), 0, 0)           # +Z of the arrow -> -Y (direction of the push)
        sz = math.sin(math.pi * cyc_)
        a.scale = (sz, sz, sz)
        a.keyframe_insert("location", frame=f); a.keyframe_insert("rotation_euler", frame=f); a.keyframe_insert("scale", frame=f)
    if f == R_IMP - 10:
        for a, off, ph in ARROWS:
            vis(a, [(R_IMP - 10, f_r1 - 28)])

# ------------------------------------------------------------------ FX: gravel jitter, impact debris + dust, sparks, stop dust
fx = bpy.data.collections.new("FX"); sc.collection.children.link(fx)
M_DUST = bpy.data.materials.new("Dust"); M_DUST.use_nodes = True
dn = M_DUST.node_tree.nodes; dl_ = M_DUST.node_tree.links
dn.remove(dn["Principled BSDF"]); vol = dn.new('ShaderNodeVolumePrincipled')
vol.inputs['Color'].default_value = (0.6, 0.55, 0.48, 1)
_nz = dn.new('ShaderNodeTexNoise'); _nz.inputs['Scale'].default_value = 2.5; _nz.inputs['Detail'].default_value = 4
_tc = dn.new('ShaderNodeTexCoord'); dl_.new(_tc.outputs['Object'], _nz.inputs['Vector'])
_gr = dn.new('ShaderNodeTexGradient'); _gr.gradient_type = 'SPHERICAL'; dl_.new(_tc.outputs['Object'], _gr.inputs['Vector'])
_m1 = dn.new('ShaderNodeMath'); _m1.operation = 'MULTIPLY'; dl_.new(_nz.outputs['Fac'], _m1.inputs[0]); dl_.new(_gr.outputs['Fac'], _m1.inputs[1])
_m2 = dn.new('ShaderNodeMath'); _m2.operation = 'MULTIPLY'; _m2.name = "DustDen"; _m2.inputs[1].default_value = 0.9
dl_.new(_m1.outputs[0], _m2.inputs[0]); dl_.new(_m2.outputs[0], vol.inputs['Density'])
dl_.new(vol.outputs[0], dn["Material Output"].inputs['Volume'])
def stone(name, r):
    bmg = bmesh.new(); bmesh.ops.create_icosphere(bmg, subdivisions=1, radius=r)
    for v_ in bmg.verts: v_.co = Vector((v_.co.x * random.uniform(0.7, 1.3), v_.co.y * random.uniform(0.7, 1.3), v_.co.z * random.uniform(0.6, 1.0)))
    me = bpy.data.meshes.new(name); bmg.to_mesh(me); bmg.free(); o = bpy.data.objects.new(name, me); fx.objects.link(o)
    me.materials.append(bpy.data.materials["Ballast"]); return o
f_rumble = F(6.3)
for k in range(36):
    o = stone("Jitter%d" % k, random.uniform(0.018, 0.035))
    base = V(random.uniform(0.35, 1.5), random.uniform(-1.5, 4.0), 0.0)
    if abs(base.x - GAUGE) < 0.08: base.x += 0.15
    vel = V(random.uniform(-1.5, 2.5), random.uniform(-7, -2), random.uniform(2, 5))
    for f in range(1, sc.frame_end + 1, 2):
        if f < f_rumble: p = base
        elif f < T_IMP + (base.y - HEAD_Y) / V0 * FPS * 0 - 2:
            amp = 0.006 + 0.03 * ((f - f_rumble) / (T_IMP - f_rumble)) ** 2
            p = base + V(0, 0, amp * abs(math.sin(f * 1.7 + k)))
        else:
            t = (f - (T_IMP - 2)) / FPS
            z = vel.z * t - 4.9 * t * t
            if z < 0 and t > 0.1:
                # landed: stays where it fell
                tl = (vel.z + math.sqrt(vel.z ** 2)) / 9.8; p = base + V(vel.x * tl, vel.y * tl, 0)
            else:
                p = base + V(vel.x * t, vel.y * t, max(0.0, z))
        if f in (1, f_rumble - 1) or f >= f_rumble:
            o.location = p; o.keyframe_insert("location", frame=f)
    hide_in(o, [STUDIO])
# impact dust: volume puffs expand and drift with the train
for k in range(9):
    bmg = bmesh.new(); bmesh.ops.create_icosphere(bmg, subdivisions=2, radius=1.0)
    me = bpy.data.meshes.new("Dust%d" % k); bmg.to_mesh(me); bmg.free(); o = bpy.data.objects.new("ImpactDust%d" % k, me); fx.objects.link(o)
    me.materials.append(M_DUST)
    st_ = T_IMP + k * 4; off = V(random.uniform(0.5, 1.6), random.uniform(-0.5, 0.5), random.uniform(0.1, 0.5))
    for f, s_ in ((st_ - 1, 0.01), (st_, 0.15), (st_ + 20, 0.6), (st_ + 70, 1.1), (st_ + 140, 1.4)):
        o.scale = (s_, s_ * 1.2, s_ * 0.7)
        o.location = V(off.x, min(train_front(f) - 0.3, off.y + train_front(st_)) if f < st_ + 20 else train_front(st_) - 4 - 0.02 * (f - st_), off.z + 0.2 * s_)
        o.keyframe_insert("scale", frame=f); o.keyframe_insert("location", frame=f)
    vis(o, [(st_, st_ + 140)])
# sparks: streak clusters at the wheel/rail contacts, flickering (re-rotated every 2 frames), brightest when the wheels lock
M_SPARK = bpy.data.materials.new("Spark"); M_SPARK.use_nodes = True
spn = M_SPARK.node_tree.nodes; spn.remove(spn["Principled BSDF"]); em_ = spn.new('ShaderNodeEmission')
em_.inputs['Color'].default_value = (1.0, 0.55, 0.15, 1); em_.inputs['Strength'].default_value = 40
M_SPARK.node_tree.links.new(em_.outputs[0], spn["Material Output"].inputs['Surface'])
def spark_cluster(name, n=40):
    bmg = bmesh.new()
    for i in range(n):
        d = V(random.uniform(-0.6, 0.6), random.uniform(0.4, 1.0), random.uniform(0.0, 0.7)).normalized()
        L_ = random.uniform(0.15, 0.6); st = d * random.uniform(0.0, 0.25)
        a = d.orthogonal().normalized() * 0.004
        v = [bmg.verts.new(p) for p in (st - a, st + a, st + d * L_ + a * 0.3, st + d * L_ - a * 0.3)]
        bmg.faces.new(v)
    me = bpy.data.meshes.new(name); bmg.to_mesh(me); bmg.free(); o = bpy.data.objects.new(name, me); fx.objects.link(o)
    me.materials.append(M_SPARK); return o
TRO = bpy.data.objects["TrainRig"]
whl = sorted([o for o in bpy.data.objects if o.parent == TRO and o.name.startswith("wheel")], key=lambda o: (o.location.x, o.location.y))
f_sp0, f_lock = T_IMP + 20, F(14.5)
SPK = [(sx_ * GAUGE, w_.location.y) for w_ in whl for sx_ in (-1, 1)]
for i, (wx_, wy_) in enumerate(SPK):
    o = spark_cluster("Sparks%d" % i)
    o.parent = TRO; o.location = (wx_, wy_ + 0.25, RAIL_H + 0.01)
    o.rotation_mode = 'XYZ'
    for f in range(f_sp0, T_STOP + 12, 2):
        o.rotation_euler = (random.uniform(-0.3, 0.3), random.uniform(-0.4, 0.4), random.uniform(-0.25, 0.25))
        k = 0.35 if f < f_lock else 1.0
        if f > T_STOP: k *= max(0, 1 - (f - T_STOP) / 12)
        sz = k * random.uniform(0.6, 1.3)
        o.scale = (sz, sz * (1.6 if f >= f_lock else 1.0), sz)
        o.keyframe_insert("rotation_euler", frame=f); o.keyframe_insert("scale", frame=f)
    ad = o.animation_data
    for layer in getattr(ad.action, "layers", []):
        for strip in layer.strips:
            for cb in strip.channelbags:
                for fc in cb.fcurves:
                    for kp in fc.keyframe_points: kp.interpolation = 'CONSTANT'
    vis(o, [(f_sp0, T_STOP + 10)])
    if i % 3 == 0:
        ld = bpy.data.lights.new("SparkLight%d" % i, 'POINT'); ld.color = (1.0, 0.55, 0.2); ld.shadow_soft_size = 0.05
        lo = bpy.data.objects.new("SparkLight%d" % i, ld); fx.objects.link(lo); lo.parent = TRO; lo.location = o.location + V(0, 0.3, 0.2)
        for f in range(f_sp0, T_STOP + 14, 2):
            k = (0.3 if f < f_lock else 1.0) * (1 if f <= T_STOP else max(0, 1 - (f - T_STOP) / 12))
            ld.energy = 160 * k * random.uniform(0.5, 1.2); ld.keyframe_insert("energy", frame=f)
        ld.energy = 0; ld.keyframe_insert("energy", frame=f_sp0 - 2); ld.keyframe_insert("energy", frame=T_STOP + 16)
# dust wave as it grinds to a halt, then slowly settling
for k in range(10):
    bmg = bmesh.new(); bmesh.ops.create_icosphere(bmg, subdivisions=2, radius=1.0)
    me = bpy.data.meshes.new("StopDust%d" % k); bmg.to_mesh(me); bmg.free(); o = bpy.data.objects.new("StopDust%d" % k, me); fx.objects.link(o)
    me.materials.append(M_DUST)
    yy = train_front(T_STOP) + 1.5 + k * 4.2; sx = 1 if k % 2 else -1
    st_ = T_STOP - 40 + k * 3
    for f, s_, dx in ((st_, 0.2, 1.6), (st_ + 40, 1.0, 2.4), (st_ + 120, 1.6, 3.2), (st_ + 240, 2.0, 3.8)):
        o.scale = (s_ * 0.9, s_ * 1.6, s_ * 0.45); o.location = (sx * dx, yy, 0.25 * s_)
        o.keyframe_insert("scale", frame=f); o.keyframe_insert("location", frame=f)
    vis(o, [(st_, min(st_ + 240, F(16.6)))])
dust_den = dn["DustDen"].inputs[1]
for f, d in ((1, 0.6), (T_STOP + 60, 0.35), (T_STOP + 200, 0.12)):
    dust_den.default_value = d; dust_den.keyframe_insert("default_value", frame=f)

# ------------------------------------------------------------------ light grade: flash-back warm, studio, under-train exposure lift
SUN = bpy.data.objects["Sun"].data
W_BG = sc.world.node_tree.nodes["Background"].inputs['Strength']
def key_light(f, col, en, wb, ex):
    SUN.color = col; SUN.energy = en; SUN.keyframe_insert("color", frame=f); SUN.keyframe_insert("energy", frame=f)
    W_BG.default_value = wb; W_BG.keyframe_insert("default_value", frame=f)
    sc.view_settings.exposure = ex; sc.view_settings.keyframe_insert("exposure", frame=f)
day = ((1.0, 0.97, 0.92), 4.2, 1.3)
key_light(1, *day, 0.0)
key_light(F(11.3), *day, 0.0); key_light(F(11.7), *day, 1.2); key_light(F(14.0), *day, 1.2); key_light(F(14.6), *day, 0.0)  # under the train
key_light(sc['f_stir'] - 20, *day, 0.0); key_light(sc['f_stir'] + 10, *day, 0.7); key_light(f_fb0 - 8, *day, 0.7); key_light(f_fb0 - 3, *day, 0.0); key_light(f_fb0 + 3, (1.0, 0.62, 0.32), 4.5, 0.55, 0.25)       # flash-back: warm, low gold sun
key_light(f_fb1 - 2, (1.0, 0.62, 0.32), 4.5, 0.55, 0.25); key_light(f_fb1, *day, 0.0)
key_light(f_r1, *day, 0.0); key_light(F(33.0), *day, 0.0); key_light(F(33.6), *day, 0.55); key_light(sc.frame_end, *day, 0.55)
for f, sat in ((f_fb0 - 3, 1.0), (f_fb0 + 3, 0.4), (f_fb1 - 2, 0.4), (f_fb1, 1.0)):
    pass

# ------------------------------------------------------------------ continuous camera (one camera, one spline)
cam_d = bpy.data.cameras.new("CAM_Film"); cam_d.lens = 28; cam_d.sensor_fit = 'AUTO'; cam_d.clip_start = 0.02; cam_d.clip_end = 600
cam_d.dof.use_dof = True; cam_d.dof.aperture_fstop = 2.8
cam = bpy.data.objects.new("CAM_Film", cam_d); sc.collection.objects.link(cam); sc.camera = cam
aim = bpy.data.objects.new("CAM_Film_Aim", None); sc.collection.objects.link(aim)
tt = cam.constraints.new('TRACK_TO'); tt.target = aim; tt.track_axis = 'TRACK_NEGATIVE_Z'; tt.up_axis = 'UP_Y'
cam_d.dof.focus_object = aim
def lad_p(f, dz=0.0):
    """Lad's pelvis (root) world position from the analytic paths used to animate him"""
    if f <= f_trip: return WP(f) + V(0, 0, RH.z - 0.05 + dz)
    if f < T_IMP: return V(LIE_X, HEAD_Y, 0.15 + dz) if f > F(2.9) else V(1.7, 0.4, 0.6 + dz)
    if f <= f_rest: p, _ = drag_full(f); return p + V(0, 0, dz)
    return REST_P + V(0, 0, dz)
TF = train_front
R_HEAD_ = V(*eval(sc["replay_head"])); HR_ = V(*eval(sc["head_rest"]))
def rp(f):
    fr = T_IMP + (f - R_IMP) / SLOW
    p, _ = drag_full(int(max(T_IMP, min(fr, f_rest)))) if fr >= T_IMP else (V(LIE_X, HEAD_Y, 0.15), None)
    return p + (V(R_HEAD_.x, R_HEAD_.y, 0) - V(HR_.x, HEAD_Y, 0)) + V(0, 0, 0.1)
y = lambda f: lad_p(f).y
CAM = [  # frame, camera, aim, lens
    (1, V(-1.15, -2.7, 1.35), WP(1) + V(0.1, 0, 1.25), 30),
    (45, V(-0.65, -2.35, 1.15), WP(45) + V(0, 0, 1.15), 30),
    (85, V(0.35, -2.1, 0.95), WP(85) + V(0.1, 0, 1.0), 30),
    (115, V(1.55, -1.75, 0.6), V(0.45, 1.0, 0.85), 28),
    (160, V(3.4, -1.3, 1.05), V(1.55, 0.7, 0.9), 26),
    (215, V(3.4, 1.9, 1.15), V(1.6, 0.1, 0.5), 28),
    (240, V(3.0, -1.9, 0.95), V(1.45, 0.0, 0.4), 26),
    (268, V(2.2, -2.3, 0.7), V(1.55, 0.0, 0.35), 24),
    (325, V(1.55, -1.7, 0.55), V(1.0, 0.1, 0.25), 26),
    (390, V(1.35, -2.0, 0.42), V(0.85, 6.0, 0.35), 26),
    (450, V(1.6, -2.6, 0.5), V(0.7, 16.0, 1.3), 24),
    (505, V(2.3, -3.2, 0.5), V(0.9, 5.0, 1.2), 24),
    (535, V(2.7, -2.7, 0.75), V(1.2, 0.2, 0.35), 24),
    (548, V(2.85, -3.4, 0.85), lad_p(548), 24),
    (575, V(3.3, -9.5, 1.15), lad_p(575, 0.1), 24),
    (615, V(3.2, y(615) - 3.5, 0.95), lad_p(615), 24),
    (660, V(2.7, y(660) - 3.6, 0.36), lad_p(660), 24),
    (700, V(0.3, y(700) - 1.25, 0.34), lad_p(700), 18),
    (755, V(-0.25, y(755) - 1.25, 0.32), lad_p(755), 18),
    (815, V(0.3, y(815) - 1.4, 0.36), lad_p(815), 18),
    (842, V(1.9, y(842) - 1.2, 0.36), lad_p(842), 20),
    (866, V(2.7, -42.8, 0.45), V(0.2, -40.0, 0.25), 24),
    (905, V(2.35, TF(905) + 1.5, 0.7), V(0.72, TF(905) + 4.5, 0.5), 24),
    (935, V(3.5, -46.0, 2.2), V(0.9, -50.0, 0.8), 23),
    (960, V(5.6, -31.0, 2.2), V(1.0, -45.0, 1.0), 22),
    (1015, V(7.6, -33.5, 6.4), V(2.2, -42.0, 0.6), 22),
    (1045, V(2.0, -40.2, 1.5), V(3.8, -38.9, 1.25), 20),
    (1090, V(1.95, -39.2, 1.45), V(3.9, -39.4, 1.2), 20),
    (1113, V(1.8, -40.4, 1.45), V(4.0, -38.4, 1.3), 18),
    (1138, V(1.85, -40.1, 0.95), V(2.62, -41.6, 0.8), 24),
    (1168, V(2.7, -40.9, 0.62), V(0.3, -40.0, 0.35), 24),
    (1200, V(2.95, -41.0, 0.5), V(1.3, -40.0, 0.45), 24),
    (1230, V(3.45, -40.95, 0.9), V(2.2, -40.1, 1.05), 26),
    (1250, V(3.95, -40.6, 1.45), V(2.4, -40.1, 1.45), 28),
    (1275, V(3.1, -41.7, 1.75), V(2.45, -40.1, 1.62), 30),
    (1322, V(3.25, -39.45, 1.78), V(2.5, -40.05, 1.62), 36),
    (1385, V(3.35, -40.25, 1.5), V(2.45, -40.1, 1.42), 30),
    (1408, V(3.15, -40.35, 1.4), V(2.45, -40.1, 1.3), 28),
    (1440, V(3.45, -40.1, 1.3), V(2.45, -40.1, 1.15), 26),
    (1500, V(3.1, -41.7, 1.35), V(2.45, -40.1, 1.05), 26),
    (1560, V(3.2, -41.25, 1.2), V(2.45, -40.35, 1.05), 32),
    (1605, V(rp(1605).x + 1.4, rp(1605).y - 1.7, 1.0), rp(1605), 28),
    (1625, V(rp(1625).x + 0.9, rp(1625).y - 1.0, 0.7), rp(1625), 30),
    (1680, V(rp(1680).x + 1.3, rp(1680).y - 1.5, 0.85), rp(1680), 28),
    (1750, V(rp(1750).x - 1.1, rp(1750).y - 1.0, 0.8), rp(1750), 30),
    (1812, V(rp(1812).x + 1.0, rp(1812).y - 1.1, 0.75), rp(1812), 30),
    (1834, V(rp(1834).x + 1.0, rp(1834).y - 1.0, 0.8), rp(1834), 30),
    (1846, V(2.7, -38.0, 1.6), V(2.45, -40.3, 1.1), 26),
    (1876, V(2.65, -38.3, 1.65), V(2.4, -41.0, 1.3), 28),
    (1920, V(3.4, -40.0, 1.5), V(2.45, -41.8, 1.2), 28),
    (1985, V(2.95, -44.6, 1.45), V(2.45, -42.85, 1.35), 28),
    (2020, V(2.78, -43.6, 1.5), V(2.5, -43.1, 1.42), 40),
    (2070, V(2.64, -43.8, 1.62), V(2.45, -42.9, 1.63), 40)]
fc_ = catmull([(f, c) for f, c, a, l in CAM]); fa_ = catmull([(f, a) for f, c, a, l in CAM]); fl_ = catmull([(f, float(l)) for f, c, a, l in CAM])
for f in list(range(1, sc.frame_end + 1, 2)) + [sc.frame_end]:
    cam.location = fc_(f); cam.keyframe_insert("location", frame=f)
    aim.location = fa_(f); aim.keyframe_insert("location", frame=f)
    cam_d.lens = fl_(f); cam_d.keyframe_insert("lens", frame=f)
sc["cam_keys"] = str([(f, tuple(round(v, 2) for v in c), tuple(round(v, 2) for v in a), l) for f, c, a, l in CAM])
# headlight flare: soft emissive glow shells in front of each lamp (fake bloom, no compositor)
M_FLARE = bpy.data.materials.new("Flare"); M_FLARE.use_nodes = True
fn_ = M_FLARE.node_tree.nodes; fl_ = M_FLARE.node_tree.links; fn_.remove(fn_["Principled BSDF"])
tr_ = fn_.new('ShaderNodeBsdfTransparent'); em2 = fn_.new('ShaderNodeEmission'); em2.inputs['Color'].default_value = (1.0, 0.92, 0.75, 1)
lw2 = fn_.new('ShaderNodeLayerWeight'); lw2.inputs['Blend'].default_value = 0.5
pw2 = fn_.new('ShaderNodeMath'); pw2.operation = 'POWER'; pw2.inputs[1].default_value = 5.0
inv2 = fn_.new('ShaderNodeMath'); inv2.operation = 'SUBTRACT'; inv2.inputs[0].default_value = 1.0
fl_.new(lw2.outputs['Facing'], inv2.inputs[1]); fl_.new(inv2.outputs[0], pw2.inputs[0])
ms2 = fn_.new('ShaderNodeMixShader'); fl_.new(pw2.outputs[0], ms2.inputs['Fac']); fl_.new(tr_.outputs[0], ms2.inputs[1]); fl_.new(em2.outputs[0], ms2.inputs[2])
em2.inputs['Strength'].default_value = 6
fl_.new(ms2.outputs[0], fn_["Material Output"].inputs['Surface'])
for nm_ in ("HeadlampL", "HeadlampR", "HeadlampTop"):
    hl_ = bpy.data.objects[nm_]
    bmg = bmesh.new(); bmesh.ops.create_uvsphere(bmg, u_segments=24, v_segments=12, radius=0.24)
    me_ = bpy.data.meshes.new("Flare"); bmg.to_mesh(me_); bmg.free(); fo = bpy.data.objects.new("Flare_" + nm_, me_); fx.objects.link(fo)
    me_.materials.append(M_FLARE); fo.parent = TRO; fo.location = hl_.location + V(0, -0.3, 0)
    for poly in me_.polygons: poly.use_smooth = True
    vis(fo, [(1, T_IMP - 6)])
# horn blast: exhaust/dust kick off the roof and a ground dust kick ahead of the plough as the horn sounds
f_horn = F(6.8)
for k in range(6):
    bmg = bmesh.new(); bmesh.ops.create_icosphere(bmg, subdivisions=2, radius=1.0)
    me_ = bpy.data.meshes.new("HornDust%d" % k); bmg.to_mesh(me_); bmg.free(); o = bpy.data.objects.new("HornDust%d" % k, me_); fx.objects.link(o)
    me_.materials.append(M_DUST)
    roof = k < 2
    for f, s_ in ((f_horn + k * 3, 0.1), (f_horn + k * 3 + 25, 0.8), (f_horn + k * 3 + 90, 1.6)):
        o.scale = (s_, s_ * 1.5, s_ * (0.8 if roof else 0.4))
        y_ = train_front(f) + (6.0 if roof else -1.0 - k * 0.4)
        o.location = (random.uniform(-0.8, 0.8) if not roof else 0.0, y_ + (0.0 if roof else -0.5 * (f - f_horn) / 60), (sc["loco_top"] + 0.4 + 0.6 * s_) if roof else 0.15 + 0.3 * s_)
        o.keyframe_insert("scale", frame=f); o.keyframe_insert("location", frame=f)
    vis(o, [(f_horn + k * 3, f_horn + k * 3 + 90)])
# rumble: camera shake grows as the train nears, a jolt at the impact, settles after
import mathutils.noise as mn_
for f in range(F(6.3), T_IMP + 60, 2):
    amp = 0.004 + 0.02 * ((f - F(6.3)) / (T_IMP - F(6.3))) ** 2 if f < T_IMP else 0.03 * math.exp(-(f - T_IMP) / 15.0)
    base = fc_(f); n_ = mn_.noise_vector(Vector((f * 0.35, 1.7, 3.1)))
    cam.location = base + n_ * amp; cam.keyframe_insert("location", frame=f)
fl_d = bpy.data.lights.new("UnderFill", 'POINT'); fl_d.color = (0.75, 0.88, 1.0); fl_d.shadow_soft_size = 0.6
fl_o = bpy.data.objects.new("UnderFill", fl_d); sc.collection.objects.link(fl_o)
for f in list(range(F(10.6), F(14.6), 4)) + list(range(sc["f_stir"] - 30, F(21.0), 4)):
    p_ = lad_p(min(f, f_rest)) if f < F(15) else V(*eval(sc["lad_rest"]))
    if f >= F(15) and f > sc["f_stir"] + 12: p_ = V(min(2.0, 0.2 + 1.8 * (f - sc["f_stir"] - 12) / (F(20.4) - sc["f_stir"] - 12)), p_.y, 0)
    fl_o.location = V(p_.x + 1.2, p_.y - 0.6, 0.45); fl_o.keyframe_insert("location", frame=f)
    fl_d.energy = 60.0; fl_d.keyframe_insert("energy", frame=f)
for f in (F(10.5), F(14.7), sc["f_stir"] - 34, F(21.05)):
    fl_d.energy = 0.0; fl_d.keyframe_insert("energy", frame=f)
# stylised impact flash: a bright star burst at the plough at the hit, gone in 8 frames
bmg = bmesh.new()
for k in range(12):
    a0 = 2 * math.pi * k / 12; r_ = 0.9 if k % 2 == 0 else 0.45
    v0 = bmg.verts.new((0, 0, 0)); v1 = bmg.verts.new((r_ * math.cos(a0 - 0.12), 0, r_ * math.sin(a0 - 0.12))); v2 = bmg.verts.new((r_ * math.cos(a0 + 0.12), 0, r_ * math.sin(a0 + 0.12)))
    bmg.faces.new((v0, v1, v2))
me_ = bpy.data.meshes.new("ImpactStar"); bmg.to_mesh(me_); bmg.free(); star = bpy.data.objects.new("ImpactStar", me_); fx.objects.link(star)
M_STAR = bpy.data.materials.new("ImpactStar"); M_STAR.use_nodes = True
spn2 = M_STAR.node_tree.nodes; spn2.remove(spn2["Principled BSDF"]); es_ = spn2.new('ShaderNodeEmission'); es_.inputs['Color'].default_value = (1.0, 0.62, 0.12, 1); es_.inputs['Strength'].default_value = 3.5
M_STAR.node_tree.links.new(es_.outputs[0], spn2["Material Output"].inputs['Surface']); me_.materials.append(M_STAR)
for f, s_ in ((T_IMP - 1, 0.05), (T_IMP + 1, 1.0), (T_IMP + 4, 1.5), (T_IMP + 8, 0.1)):
    star.location = V(LIE_X - 0.5, train_front(f) - 0.25, 0.45); star.scale = (s_, s_, s_)
    star.keyframe_insert("location", frame=f); star.keyframe_insert("scale", frame=f)
star.rotation_euler = (0, 0, math.radians(-30))
vis(star, [(T_IMP - 1, T_IMP + 8)])
print("FX_CAMERA_DONE")
