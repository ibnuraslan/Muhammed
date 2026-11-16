"""AshaDegree Phase 1: characters animated per set (each beat's action ~30% longer than its provisional window),
one camera per shot, hard cuts by timeline markers. Provisional timing = the reference film's pacing (48 s);
Phase 2 re-lays the shot windows to the client's VO without stretching any animation.
blender -b work/sets.blend --python 04_shots.py -- work/film.blend"""
import bpy, sys, math, json, random
from mathutils import Vector, Matrix, Euler, Quaternion
P_ = "/home/user/Muhammed/blender/pipeline/"; HERE = "/home/user/Muhammed/blender/AshaDegree_v001/"
exec(open(P_ + "anim_lib.py").read()); exec(open(P_ + "hand_poses.py").read()); exec(open("/home/user/Muhammed/blender/AshaDegree_v002b/scripts/asha_lib.py").read())
out = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene; sc.render.fps = 60; sc.frame_start = 1; sc.frame_end = 2880
R_ = math.radians; random.seed(3)

# ------------------------------------------------------------------ shot table (provisional, reference pacing)
SHOTS = [  # id, set, f0, f1, note
    ("S01", "room", 1, 120, "In 2000 - kneeling, packing the book bag"),
    ("S02", "room", 121, 210, "9-year-old girl - close, looks up"),
    ("S03", "room", 211, 330, "named Asha / packed a book bag - stands with bag on, turns to the door"),
    ("S04", "room", 331, 420, "left her house in the rain - walks out through the French door"),
    ("S05", "road", 421, 540, "really early in the morning - walking away under the umbrella"),
    ("S06", "road", 541, 660, "front three-quarter, face under the umbrella"),
    ("S07", "road", 661, 780, "a passing motorist saw her - car passes"),
    ("S08", "road", 781, 870, "walking along the highway - wide, car stopped ahead"),
    ("S09", "road", 871, 960, "he circled back / approached - she stops, looks at the car"),
    ("S10", "road", 961, 1080, "Asha ran into - turns and runs off the road"),
    ("S11", "woods", 1081, 1170, "the woods - running between trees"),
    ("S12", "woods", 1171, 1260, "by daylight Asha was gone - wide, small figure disappears"),
    ("S13", "shed", 1261, 1380, "leaving behind a few belongings - two searchers at the shed"),
    ("S14", "shed", 1381, 1500, "in a nearby shed - searcher reads his clipboard"),
    ("S15", "woods", 1501, 1650, "extensive searches - torches sweep the woods"),
    ("S16", "woods", 1651, 1800, "no trace of her - closer, searcher walks forward"),
    ("S17", "site", 1801, 1890, "a year later - the wrapped bag, close"),
    ("S18", "site", 1891, 2040, "her book bag was found at a construction site - worker reaches"),
    ("S19", "site", 2041, 2190, "covered in a plastic bag - hand on the plastic, close"),
    ("S20", "site", 2191, 2280, "but it revealed nothing - worker looks at the bag"),
    ("S21", "road", 2281, 2370, "no one knows why she left - memory figure walks"),
    ("S22", "road", 2371, 2460, "or where she was going - side"),
    ("S23", "wall", 2461, 2670, "her disappearance... - the framed portrait"),
    ("S24", "wall", 2671, 2880, "unsolved cases in the United States - closer"),
]
SH = {s[0]: s for s in SHOTS}

def fcurves_of(idb):
    ad = getattr(idb, "animation_data", None)
    if not ad or not ad.action: return []
    act = ad.action; out = []
    if hasattr(act, "fcurves"):
        try: out = list(act.fcurves)
        except Exception: out = []
    if not out:
        for layer in getattr(act, "layers", []):
            for strip in layer.strips:
                for cb in getattr(strip, "channelbags", []): out += list(cb.fcurves)
    return out
def set_interp(idb, kind):
    for fc in fcurves_of(idb):
        for kp in fc.keyframe_points: kp.interpolation = kind
def vis_char(rig, ranges, extra=()):
    names = [c.name for c in rig.children if not c.hide_render]
    props = [o for o in bpy.data.objects if any(c.type == 'CHILD_OF' and c.target == rig for c in o.constraints)]
    for o in props: names += [o.name] + [c.name for c in o.children if not c.hide_render]
    key_vis(names + list(extra), ranges)

def A(rig, *v):
    """world point -> armature space of a rig at the origin (girls are scaled 0.9)"""
    return Vector(v) / rig.scale.x
def W2A(rig, v): return Vector(v) / rig.scale.x

def stand(H, f, pos, yaw, flex=2.0, head=(0.0, 0.0), twist=0.0, crouch=0.0, side=0.0, arms=True, fwd=0.0):
    rig = H.rig
    p = Vector((pos.x, pos.y, H.root_head.z - crouch))
    H.key_root(f, p, yaw=yaw, flex=flex * 0.4, side=side)
    H.key_spine(f, flex=flex, twist=twist, head=head)
    for s in "LR": H.key_foot(s, f, H.foot_xy(s, Vector((pos.x, pos.y, 0)), yaw), yaw)
    if arms: key_hang(H, f, Vector((pos.x, pos.y, H.root_head.z - crouch)), yaw, fwd=fwd)

def squat(H, f, pos, yaw, depth=0.42, flex=22.0, head=(0.0, 0.0), twist=0.0, feet_wide=1.25, hands=None, hips_back=0.10):
    """deep crouch: feet planted, knees forward (IK), torso leaning; hands rest on the knees unless given"""
    rig = H.rig; Rm = Rz(yaw)
    p = Vector((pos.x, pos.y, H.root_head.z * (1 - depth)))
    p += Rm @ Vector((0, hips_back, 0))   # hips go back
    H.key_root(f, p, yaw=yaw, flex=flex * 0.5)
    H.key_spine(f, flex=flex, twist=twist, head=head)
    for s in "LR":
        sx = 1 if s == "L" else -1
        xy = Vector((pos.x, pos.y)) + (Rm @ Vector((H.ankle[s].x * feet_wide, 0.02, 0))).to_2d()
        H.key_foot(s, f, xy, yaw + sx * 12)
    if hands is None:
        for s in "LR":
            sx = 1 if s == "L" else -1
            kn = Vector((H.ankle[s].x * 1.3, -0.30, H.root_head.z * 0.53 - (H.root_head.z * (1 - depth))))
            body_hand(H, s, f, p, yaw, (kn.x, kn.y, kn.z + 0.05), (0, -1.0, -0.6), (-sx * 0.3, 0, -1.0), pole_off=(0.5 * sx, 0.2, 0.0))
    else:
        hands(p)
    return p

def ensure_visible_range(names, ranges): key_vis(names, ranges)

def cam_shot(sid, keys, lens=35, target_keys=None, clip_start=0.05):
    """camera with a smooth path; keys = [(frame, loc)], target_keys = [(frame, point)] (Track To, world up)"""
    c = bpy.data.cameras.new("CAM_" + sid); c.lens = lens; c.clip_start = clip_start; c.clip_end = 600
    c.dof.use_dof = False; c.sensor_width = 36
    o = bpy.data.objects.new("CAM_" + sid, c); sc.collection.objects.link(o)
    t = bpy.data.objects.new("TGT_" + sid, None); sc.collection.objects.link(t)
    for f, p in keys:
        o.location = p; o.keyframe_insert("location", frame=f)
    for f, p in target_keys:
        t.location = p; t.keyframe_insert("location", frame=f)
    for ob in (o, t):
        if ob.animation_data:
            for fc in ob.animation_data.action.fcurves if hasattr(ob.animation_data.action, "fcurves") else []:
                for kp in fc.keyframe_points: kp.interpolation = 'BEZIER'; kp.handle_left_type = kp.handle_right_type = 'AUTO_CLAMPED'
    tr = o.constraints.new('TRACK_TO'); tr.target = t; tr.track_axis = 'TRACK_NEGATIVE_Z'; tr.up_axis = 'UP_Y'
    m = sc.timeline_markers.new(sid, frame=SH[sid][2]); m.camera = o
    return o

def recol(obj, rgb, rough=0.5):
    m = bpy.data.materials.new(obj.name + "_m"); m.use_nodes = True; Pn = m.node_tree.nodes["Principled BSDF"]
    Pn.inputs["Base Color"].default_value = (*rgb, 1); Pn.inputs["Roughness"].default_value = rough
    obj.data.materials.clear(); obj.data.materials.append(m); return m

def import_prop(name, fn, size, axis=2, coll_name="Props"):
    c = bpy.data.collections.get(coll_name) or bpy.data.collections.new(coll_name)
    if c.name not in sc.collection.children: sc.collection.children.link(c)
    before = set(bpy.data.objects); bpy.ops.import_scene.gltf(filepath=HERE + "assets/" + fn)
    new = [o for o in bpy.data.objects if o not in before]; ms = [o for o in new if o.type == 'MESH']
    bpy.context.view_layer.update()
    mws = {o.name: o.matrix_world.copy() for o in ms}
    for o in ms: o.parent = None
    for o in ms: o.matrix_world = mws[o.name]
    for o in new:
        if o not in ms: bpy.data.objects.remove(o)
    bpy.ops.object.select_all(action='DESELECT')
    for o in ms: o.select_set(True)
    bpy.context.view_layer.objects.active = ms[0]
    if len(ms) > 1: bpy.ops.object.join()
    o = bpy.context.object; o.name = name; bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    pts = [Vector(v.co) for v in o.data.vertices]
    mn = Vector([min(p[i] for p in pts) for i in range(3)]); mx = Vector([max(p[i] for p in pts) for i in range(3)])
    s = size / (mx - mn)[axis]; o.data.transform(Matrix.Scale(s, 4) @ Matrix.Translation(-(mn + mx) / 2))
    for uc in list(o.users_collection): uc.objects.unlink(o)
    c.objects.link(o)
    for p in o.data.polygons: p.use_smooth = True
    o.data.update(); bpy.context.view_layer.update()
    return o

def hand_frame(rig, s):
    """posed hand frame in world: wrist point, finger direction d, thumb-side axis a, palm normal n, palm centre"""
    Mw = rig.matrix_world; PB = rig.pose.bones
    wr = Mw @ PB["wrist." + s].head; m3 = Mw @ PB["finger3-1." + s].head
    i2 = Mw @ PB["finger2-1." + s].head; p5 = Mw @ PB["finger5-1." + s].head
    d = (m3 - wr).normalized(); a = (i2 - p5).normalized()
    n = d.cross(a) if s == "L" else a.cross(d)
    n.normalize()
    # palm side check: curling fingers move toward n
    tip = Mw @ PB["finger3-3." + s].tail
    if (tip - m3).dot(n) < 0 and (tip - m3).length > 0.001 and (tip - m3).normalized().dot(d) < 0.95: n = -n
    return wr, d, a, n, wr.lerp(m3, 0.55)

def radius_at(obj, axis_local, centre_local, slab=0.03):
    """radial size of a prop around its local axis near a point on the axis (local units)"""
    ax = Vector(axis_local).normalized(); c = Vector(centre_local); rs = []
    for v in obj.data.vertices:
        d = v.co - c; t = d.dot(ax)
        if abs(t) < slab: rs.append((d - ax * t).length)
    return sorted(rs)[len(rs) // 2] if rs else 0.015

def grip_prop(obj, rig, s, f, axis_world, grip_local, r):
    """put the prop's grip point (local) in the fist at frame f: axis through the palm, fingers solved to touch it"""
    sc.frame_set(f); bpy.context.view_layer.update()
    wr, d, a, n, palm = hand_frame(rig, s)
    q = obj.rotation_quaternion
    gp_world_offset = q @ Vector(grip_local)
    C = palm + n * 0.012
    obj.location = C + n * (r + 0.013 + (0.007 if r < 0.02 else 0.0)) - gp_world_offset
    bpy.context.view_layer.update()
    rep = grip_object(rig, s, f, obj, C, n, finger_dir=d)
    for k in (5, 4, 3, 2):   # a finger that found no contact copies its neighbour's curl (no fanned-out finger)
        if rep.get("finger%d-3.%s" % (k, s)) is None:
            nb = k - 1 if k > 2 else 3
            for j in (1, 2, 3):
                src_ = rig.pose.bones["finger%d-%d.%s" % (nb, j, s)]; dst_ = rig.pose.bones["finger%d-%d.%s" % (k, j, s)]
                dst_.rotation_quaternion = src_.rotation_quaternion.copy(); dst_.keyframe_insert("rotation_quaternion", frame=f)
    for j in (1, 2, 3):   # thumb eased 35% open so its skin clears the surface
        pb = rig.pose.bones["finger1-%d.%s" % (j, s)]; q = pb.rotation_quaternion.copy()
        pb.rotation_quaternion = q.slerp(Quaternion((1, 0, 0, 0)) if j > 1 else q, 0.55); pb.keyframe_insert("rotation_quaternion", frame=f)
    print("GRIP", obj.name, rig.name, f, "r=%.3f" % r, rep)
    bpy.context.view_layer.update(); attach(obj, rig, "wrist." + s)
    return rep

def hold_in_hand(obj, rig, s, f, axis_local=Vector((0, 0, 1)), along="a", depth=0.028, shift=0.0):
    """place a cylinder-like prop through the fist at frame f (its local axis along the thumb-side axis), then Child Of the wrist"""
    sc.frame_set(f); bpy.context.view_layer.update()
    wr, d, a, n, palm = hand_frame(rig, s)
    ax = a if along == "a" else d
    q = axis_local.rotation_difference(ax)
    obj.rotation_mode = 'QUATERNION'; obj.rotation_quaternion = q
    obj.location = palm + n * depth + ax * shift
    bpy.context.view_layer.update()
    attach(obj, rig, "wrist." + s)
    apply_pose(rig, s, "wrap_grip", f)

# ================================================================== characters
G0 = bpy.data.objects["Girl"]
girls = {"room": G0}
for k in ("road", "woods", "ghost"):
    girls[k] = dup_char(G0, "Girl" + k.capitalize())
SA = bpy.data.objects["SearchA"]; SB = bpy.data.objects["SearchB"]; SC = bpy.data.objects["SearchC"]; WK = bpy.data.objects["Worker"]
SA2 = dup_char(SA, "SearchA2"); SB2 = dup_char(SB, "SearchB2")
for o in bpy.data.objects:
    if o.type == 'ARMATURE': o.location = (0, 0, 0)
HS = {}
for k, g in list(girls.items()): HS[k] = setup_char(g)
for r in (SA, SB, SC, SA2, SB2, WK): HS[r.name] = setup_char(r)
for r in list(girls.values()) + [SA, SB, SC, SA2, SB2, WK]:
    for s in "LR": apply_pose(r, s, "relaxed", 1)

# ================================================================== props: book bag (pink, two round badges), umbrella, clipboard, torches
pinkbag = bpy.data.materials.new("BagPink"); pinkbag.use_nodes = True; Pn = pinkbag.node_tree.nodes["Principled BSDF"]
Pn.inputs["Base Color"].default_value = (0.9, 0.12, 0.42, 1); Pn.inputs["Roughness"].default_value = 0.55; Pn.inputs["Sheen Weight"].default_value = 0.6
trimbag = bpy.data.materials.new("BagTrim"); trimbag.use_nodes = True; Pn = trimbag.node_tree.nodes["Principled BSDF"]
Pn.inputs["Base Color"].default_value = (0.55, 0.05, 0.22, 1); Pn.inputs["Roughness"].default_value = 0.5
def make_backpack(name):
    """our own kid's book bag: rounded body, front pocket, top loop, zip piping; origin at the bottom centre, front = -Y"""
    import bmesh
    bm = bmesh.new()
    def rbox(dims, loc, mi):
        r = bmesh.ops.create_cube(bm, size=1.0)
        for v_ in r['verts']:
            v_.co = Vector((v_.co.x * dims[0], v_.co.y * dims[1], v_.co.z * dims[2])) + Vector(loc)
        for f_ in bm.faces:
            if all(v_ in r['verts'] for v_ in f_.verts): f_.material_index = mi
    rbox((0.27, 0.13, 0.36), (0, 0, 0.18), 0)            # body
    rbox((0.24, 0.05, 0.16), (0, -0.075, 0.11), 0)       # front pocket
    rbox((0.27, 0.012, 0.012), (0, -0.066, 0.25), 1)     # zip piping
    rbox((0.22, 0.012, 0.012), (0, -0.101, 0.185), 1)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); sc.collection.objects.link(o)
    me.materials.append(pinkbag); me.materials.append(trimbag)
    b = o.modifiers.new("round", 'BEVEL'); b.width = 0.045; b.segments = 4; b.limit_method = 'ANGLE'
    sd = o.modifiers.new("smooth", 'SUBSURF'); sd.levels = 1; sd.render_levels = 1
    for p in me.polygons: p.use_smooth = True
    # top carry loop
    bpy.ops.mesh.primitive_torus_add(major_radius=0.045, minor_radius=0.009, location=(0, 0, 0))
    t = bpy.context.object; t.name = name + "_Loop"; t.data.materials.append(trimbag)
    for uc in list(t.users_collection): uc.objects.unlink(t)
    sc.collection.objects.link(t); t.parent = o; t.location = (0, 0.0, 0.36); t.rotation_euler = (R_(90), 0, R_(90))
    return o
bag = make_backpack("BookBag")
bpy.context.view_layer.update()
# the bag's front: find its thinnest axis
dims = bag.dimensions; thin = min(range(3), key=lambda i: dims[i])
print("BAG dims", tuple(round(x, 3) for x in dims), "thin axis", thin)
def badge(name, parent, rgb, heart=False, offs=(0, 0)):
    bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=0.035, depth=0.008)
    b = bpy.context.object; b.name = name
    m = bpy.data.materials.new(name); m.use_nodes = True; Pn = m.node_tree.nodes["Principled BSDF"]
    Pn.inputs["Base Color"].default_value = (*rgb, 1); Pn.inputs["Roughness"].default_value = 0.25
    if heart:
        nt = m.node_tree; tc = nt.nodes.new("ShaderNodeTexCoord"); sp = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(tc.outputs["Object"], sp.inputs[0])
        # heart = two circles + triangle in object xy (implicit), pink on light pink
        ex = nt.nodes.new("ShaderNodeMath"); ex.operation = 'MULTIPLY'; ex.inputs[1].default_value = 40; nt.links.new(sp.outputs[0], ex.inputs[0])
        ey = nt.nodes.new("ShaderNodeMath"); ey.operation = 'MULTIPLY'; ey.inputs[1].default_value = 40; nt.links.new(sp.outputs[1], ey.inputs[0])
        # (x^2 + y^2 - 1)^3 - x^2 y^3 < 0
        x2 = nt.nodes.new("ShaderNodeMath"); x2.operation = 'POWER'; x2.inputs[1].default_value = 2; nt.links.new(ex.outputs[0], x2.inputs[0])
        y2 = nt.nodes.new("ShaderNodeMath"); y2.operation = 'POWER'; y2.inputs[1].default_value = 2; nt.links.new(ey.outputs[0], y2.inputs[0])
        y3 = nt.nodes.new("ShaderNodeMath"); y3.operation = 'MULTIPLY'; nt.links.new(y2.outputs[0], y3.inputs[0]); nt.links.new(ey.outputs[0], y3.inputs[1])
        s1 = nt.nodes.new("ShaderNodeMath"); s1.operation = 'ADD'; nt.links.new(x2.outputs[0], s1.inputs[0]); nt.links.new(y2.outputs[0], s1.inputs[1])
        s2 = nt.nodes.new("ShaderNodeMath"); s2.operation = 'SUBTRACT'; s2.inputs[1].default_value = 1.0; nt.links.new(s1.outputs[0], s2.inputs[0])
        s3 = nt.nodes.new("ShaderNodeMath"); s3.operation = 'POWER'; s3.inputs[1].default_value = 3; nt.links.new(s2.outputs[0], s3.inputs[0])
        t1 = nt.nodes.new("ShaderNodeMath"); t1.operation = 'MULTIPLY'; nt.links.new(x2.outputs[0], t1.inputs[0]); nt.links.new(y3.outputs[0], t1.inputs[1])
        d_ = nt.nodes.new("ShaderNodeMath"); d_.operation = 'SUBTRACT'; nt.links.new(s3.outputs[0], d_.inputs[0]); nt.links.new(t1.outputs[0], d_.inputs[1])
        lt = nt.nodes.new("ShaderNodeMath"); lt.operation = 'LESS_THAN'; lt.inputs[1].default_value = 0.0; nt.links.new(d_.outputs[0], lt.inputs[0])
        mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = 'RGBA'; mx.inputs['A'].default_value = (*rgb, 1); mx.inputs['B'].default_value = (0.95, 0.15, 0.45, 1)
        nt.links.new(lt.outputs[0], mx.inputs['Factor']); nt.links.new(mx.outputs['Result'], Pn.inputs["Base Color"])
    b.data.materials.append(m)
    for uc in list(b.users_collection): uc.objects.unlink(b)
    parent.users_collection[0].objects.link(b)
    # on the front face of the bag (thin axis, negative side)
    ln = Vector((0, 0, 0)); ln[thin] = -dims[thin] / 2 - 0.002
    up = 2 if thin != 2 else 1; side = [i for i in range(3) if i not in (thin, up)][0]
    ln[side] = offs[0]; ln[up] = offs[1]
    ln = Vector((offs[0], -0.071, 0.295))
    rot = Vector((0, 0, 1)).rotation_difference(Vector([(-1.0 if i == thin else 0.0) for i in range(3)]))
    b.rotation_mode = 'QUATERNION'; b.rotation_quaternion = rot; b.location = ln; b.parent = parent
    return b
badge("Bag_BadgeWhite", bag, (0.95, 0.95, 0.97), offs=(-0.055, 0.0))
badge("Bag_BadgeHeart", bag, (0.98, 0.75, 0.82), heart=True, offs=(0.055, 0.0))
def wear_bag(rig, name, f, yaw, material=None):
    b = copy_bag(name)
    sc.frame_set(f); bpy.context.view_layer.update()
    s3 = rig.matrix_world @ rig.pose.bones["spine03"].head; s5 = rig.matrix_world @ rig.pose.bones["spine05"].head
    back = Rz(yaw) @ Vector((0, 1, 0))
    b.rotation_mode = 'XYZ'; b.rotation_euler = (0, 0, R_(180 + yaw)); b.scale = (0.88, 0.88, 0.85)
    b.location = s3.lerp(s5, 0.3) + back * 0.15 + Vector((0, 0, -0.11))
    if material:
        for o in [b] + list(b.children):
            o.data = o.data.copy(); o.data.materials.clear(); o.data.materials.append(material)
    bpy.context.view_layer.update(); attach(b, rig, "spine03")
    for ch in b.children: pass
    return b

def copy_bag(name):
    b2 = bag.copy(); b2.name = name; bag.users_collection[0].objects.link(b2); b2.hide_render = False; b2.hide_viewport = False
    for ch in bag.children:
        c2 = ch.copy(); c2.parent = b2; c2.name = ch.name.replace("Bag_", name + "_").replace("BookBag_", name + "_"); bag.users_collection[0].objects.link(c2)
        c2.hide_render = False; c2.hide_viewport = False
    return b2

umb = import_prop("Umbrella", "umbrella.glb", 0.95)   # shaft length ~ 0.95 m with canopy
um = bpy.data.materials.new("UmbrellaRed"); um.use_nodes = True; Pn = um.node_tree.nodes["Principled BSDF"]
Pn.inputs["Base Color"].default_value = (0.85, 0.1, 0.18, 1); Pn.inputs["Roughness"].default_value = 0.35; Pn.inputs["Sheen Weight"].default_value = 0.3
dk = bpy.data.materials.new("UmbrellaHandle"); dk.use_nodes = True; dk.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.06, 0.06, 0.07, 1)
for i, m in enumerate(umb.data.materials): umb.data.materials[i] = um
umb.data.transform(Matrix.Scale(0.85, 4))
UMB_GRIP = 0.36 * 0.85   # origin sits this far above the grip (shaft just above the hook)
print("UMB dims", tuple(round(x, 3) for x in umb.dimensions), [m.name for m in umb.data.materials])

clip = import_prop("Clipboard", "clipboard.glb", 0.32, axis=1)
torch_src = import_prop("Torch", "flashlight.glb", 0.2, axis=0)

# ---- (v002b) shoulder straps for the worn book bag: a flat band over each shoulder, skinned to the girl
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree
STRAP_GRIP_I = 0
strapm = bpy.data.materials.new("BagStrap"); strapm.use_nodes = True
strapm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.22, 0.02, 0.09, 1); strapm.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.6
def make_straps(rig, bagobj, f_bag, name):
    global STRAP_GRIP_I
    sc.frame_set(f_bag); bpy.context.view_layer.update()
    Mw = rig.matrix_world; B = rig.data.bones
    s3_pose = (Mw @ rig.pose.bones["spine03"].matrix).copy(); bagM_pose = bagobj.matrix_world.copy()
    rig.data.pose_position = 'REST'; bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get(); dg.update()
    bagM = (Mw @ B["spine03"].matrix_local) @ s3_pose.inverted() @ bagM_pose      # the bag, carried into the rest pose
    skip = ("hair", "ponytail", "shoes", "eye", "brow", "lash", "teeth", "tongue", "jacketsrc", "scrunch", "high-poly")
    cloth = [o for o in rig.children if o.type == 'MESH' and not o.hide_render and not any(k in o.name.lower() for k in skip)]
    print("STRAP cloth", [o.name for o in cloth])
    trees = []
    for o in cloth:
        oe = o.evaluated_get(dg); me = oe.to_mesh()
        vs = [o.matrix_world @ v.co for v in me.vertices]; ps = [tuple(p.vertices) for p in me.polygons]
        trees.append(BVHTree.FromPolygons(vs, ps)); oe.to_mesh_clear()
    suit = next(o for o in cloth if "casualsuit" in o.name)
    kd = KDTree(len(suit.data.vertices))
    for v in suit.data.vertices: kd.insert(suit.matrix_world @ v.co, v.index)
    kd.balance()
    gname = {g.index: g.name for g in suit.vertex_groups}
    def bw(n): return Mw @ B[n].head_local
    nk = bw("neck01"); out = {}
    for s_ in "LR":
        sx = 1 if s_ == "L" else -1
        sh = bw("upperarm01." + s_)
        T = nk.lerp(sh, 0.5); T.z = sh.z + 0.07
        bt = max([bagM @ Vector((q * 0.075, 0.06, 0.31)) for q in (1, -1)], key=lambda p: p.x * sx)
        bb = max([bagM @ Vector((q * 0.11, 0.06, 0.06)) for q in (1, -1)], key=lambda p: p.x * sx)
        F1 = T + Vector((0.0, -0.07, -0.05))
        F2 = Vector((nk.x + (sh.x - nk.x) * 0.72, sh.y - 0.09, sh.z - 0.13))
        F3 = Vector((sh.x - 0.01 * sx, sh.y - 0.04, sh.z - 0.22))
        S1 = Vector((sh.x - 0.01 * sx, sh.y + 0.05, sh.z - 0.25))
        B1 = T + Vector((0.0, 0.07, -0.06))
        G_ = [bb, S1, F3, F2, F1, T, B1, bt]; OFF = [0, 0.020, 0.026, 0.028, 0.026, 0.018, 0.018, 0]
        pts = []; offs = []; proj = []
        for k in range(len(G_) - 1):
            n_ = 8
            for j in range(n_):
                u = j / n_; pts.append(G_[k].lerp(G_[k + 1], u)); offs.append(OFF[k] + (OFF[k + 1] - OFF[k]) * u)
                proj.append(0 < k < len(G_) - 2 or (k == 0 and j > 3) or (k == len(G_) - 2 and j < 5))
            if k == 2: STRAP_GRIP_I = len(pts)  # F2 is the next point
        pts.append(G_[-1]); offs.append(0); proj.append(False)
        nrms = [None] * len(pts)
        def project(P_, off):
            best = None
            for t_ in trees:
                r = t_.find_nearest(P_)
                if r[0] is not None and (best is None or r[3] < best[3]): best = r
            loc, nr = best[0], best[1].normalized()
            ctr = Vector((nk.x, sh.y, min(P_.z, sh.z - 0.08)))
            if nr.dot(loc - ctr) < 0: nr = -nr
            return loc + nr * off, nr
        for it in range(3):
            for i, P_ in enumerate(pts):
                if proj[i]: pts[i], nrms[i] = project(P_, offs[i])
            if it < 2:
                sm = [p.copy() for p in pts]
                for i in range(1, len(pts) - 1):
                    if proj[i]: sm[i] = pts[i] * 0.5 + (pts[i - 1] + pts[i + 1]) * 0.25
                pts = sm
        for i in range(len(pts)):
            if nrms[i] is None:
                j = min((k for k in range(len(pts)) if nrms[k] is not None), key=lambda k: abs(k - i)); nrms[i] = nrms[j]
        inv = rig.matrix_world.inverted()
        verts = []; faces = []
        for i, P_ in enumerate(pts):
            t_ = (pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]).normalized()
            w_ = t_.cross(nrms[i]).normalized() * 0.014
            verts += [inv @ (P_ - w_), inv @ (P_ + w_)]
            if i: faces.append((2 * i - 2, 2 * i - 1, 2 * i + 1, 2 * i))
        me = bpy.data.meshes.new(name + "." + s_); me.from_pydata(verts, [], faces); me.update()
        o = bpy.data.objects.new(name + "." + s_, me); sc.collection.objects.link(o); o.parent = rig
        me.materials.append(strapm)
        for pl in me.polygons: pl.use_smooth = True
        so = o.modifiers.new("thick", 'SOLIDIFY'); so.thickness = 0.004; so.offset = 0.0
        # skin: nearest suit vertex weights; the ends ride on spine03 like the bag
        for i in range(len(pts)):
            for vi in (2 * i, 2 * i + 1):
                if not proj[i]:
                    vg = o.vertex_groups.get("spine03") or o.vertex_groups.new(name="spine03"); vg.add([vi], 1.0, 'REPLACE'); continue
                co, idx, d = kd.find(Mw @ verts[vi])
                for ge in suit.data.vertices[idx].groups:
                    if ge.weight < 0.01 or gname[ge.group] not in B: continue
                    vg = o.vertex_groups.get(gname[ge.group]) or o.vertex_groups.new(name=gname[ge.group]); vg.add([vi], ge.weight, 'REPLACE')
        am = o.modifiers.new("arm", 'ARMATURE'); am.object = rig
        o.modifiers.move(len(o.modifiers) - 1, 0)
        out[s_] = o
    rig.data.pose_position = 'POSE'; bpy.context.view_layer.update()
    print("STRAPS", {k: v.name for k, v in out.items()}, "grip index", STRAP_GRIP_I)
    return out

# ================================================================== ROOM  (S01-S04, action frames 1-480)
G = girls["room"]; H = HS["room"]
K = Vector((0.0, 0.3))   # kneel spot (world)
bag_floor = copy_bag("BagFloor"); bag_floor.rotation_euler = (0, 0, 0)
# bag stands upright on the rug in front of her, its front (badges) facing the camera
bag_floor.rotation_mode = 'XYZ'
if thin == 1: bag_floor.rotation_euler = (0, 0, 0)
elif thin == 0: bag_floor.rotation_euler = (0, 0, R_(90))
else: bag_floor.rotation_euler = (R_(90), 0, 0)
bpy.context.view_layer.update()
bz = -min((bag_floor.matrix_world @ Vector(c)).z for c in bag_floor.bound_box)
bag_floor.location = (0.0, -0.30, bz + 0.004)
bpy.context.view_layer.update()
bag_top = max((bag_floor.matrix_world @ Vector(c)).z for c in bag_floor.bound_box)
print("BAG top", round(bag_top, 3))

def kneel(H, f, pos, yaw, lean=14.0, head=(0.0, 0.0), sit=0.0, hands_on=None, twist=0.0):
    """tall kneel: knees on the floor, shins back, toes down"""
    rig = H.rig; Rm = Rz(yaw); s_ = rig.scale.x
    thigh = (H.r.BN["upperleg01.L"].head_local - H.r.BN["lowerleg01.L"].head_local).length
    shin = (H.r.BN["lowerleg01.L"].head_local - H.r.BN["foot.L"].head_local).length
    hipz = 0.05 / s_ + thigh * (0.93 - 0.35 * sit)
    p = W2A(rig, (pos.x, pos.y, 0)); p.z = hipz + (H.root_head.z - H.r.BN["upperleg01.L"].head_local.z)
    H.key_root(f, p, yaw=yaw, flex=lean * 0.6)
    H.key_spine(f, flex=lean, head=head, twist=twist)
    for s in "LR":
        sx = 1 if s == "L" else -1
        ft = Vector((p.x, p.y, 0)) + Rm @ Vector((H.ankle[s].x * 1.0, shin * 0.95 + 0.06 / s_, 0))
        H.key_foot(s, f, ft.to_2d(), yaw, lift=0.03 / s_, pitch=-62)
        pn = "Pole_knee." + s; pb = H.r.PB[pn]
        pole = Vector((p.x, p.y, 0.05 / s_)) + Rm @ Vector((H.ankle[s].x, -0.9, 0))
        pb.location = H.r.rest(pn).to_3x3().inverted() @ (pole - H.r.BN[pn].head_local); pb.keyframe_insert("location", frame=f, group=pn)
    if hands_on: hands_on(p)
    return p

# hands on the bag top: R zips across, L steadies
top_c = W2A(G, (0.0, -0.30, bag_top + 0.012))
def bag_hands(f, zx):
    def h(p):
        for s, x in (("L", 0.095), ("R", -0.11 + zx * 0.4)):
            sx = 1 if s == "L" else -1
            Wp = top_c + Vector((x, 0.0, 0.0)) / G.scale.x
            H.key_hand(s, f, Wp + Vector((0.0, 0.07, 0.03)) / G.scale.x, Vector((0.0, -1.0, -0.5)), Vector((0, 0.15, -1.0)),
                       pole=p + Vector((0.5 * sx, 0.2, -0.1)))
            wtop = G.matrix_world @ (top_c + Vector((x, 0.035, 0.0)) / G.scale.x)
            place_hand(G, s, f, wtop + Vector((0, 0, 0.004)), Vector((0, 0.0, -1.0)), Vector((0, -1.0, 0.0)), skin=0.024)
    return h
yaw0 = -10.0
for f, zx, head in ((1, 0.0, (22, 0)), (40, 0.06, (24, -4)), (80, 0.12, (20, 4)), (120, 0.04, (16, 0)),
                    (150, 0.0, (-2, 6)), (185, 0.02, (-6, 10)), (210, 0.02, (-6, 10))):
    def _hang(p, f=f):
        for s_ in "LR":
            sx_ = 1 if s_ == "L" else -1
            body_hand(H, s_, f, p, yaw0, (H.sh[s_].x + 0.05 * sx_ - H.root_head.x, H.sh[s_].y - H.root_head.y - 0.10, H.sh[s_].z - H.root_head.z - H.arm * 0.9),
                      (0, -0.2, -1), (-sx_, 0, 0), pole_off=(0.4 * sx_, 0.4, -0.2))
    kneel(H, f, K, yaw0, lean=8 if f < 140 else 4, head=head, hands_on=_hang)
for s in "LR":
    apply_pose(G, s, "relaxed", 1); apply_pose(G, s, "relaxed", 210)
# S03 211..: standing (bag on back), small settle, then turns and walks to the open door
yaw_s = -10.0
GLANCE = float(__import__("os").environ.get("ASHA_GLANCE", "-35"))   # head yaw toward the open door
def bent_arm(s_, f):
    sx_ = 1 if s_ == "L" else -1
    body_hand(H, s_, f, Vector((K.x, K.y, H.root_head.z)), yaw_s,
              (H.sh[s_].x + 0.02 * sx_ - H.root_head.x, H.sh[s_].y - H.root_head.y - 0.10, H.sh[s_].z - H.root_head.z - H.arm * 0.80),
              (0.0, -0.45, -1), (-sx_, 0.2, 0), pole_off=(0.3 * sx_, 0.5, -0.15))
for f, sd, hd in ((211, 0.0, (2, 0)), (224, 2.0, (0, -6)), (238, 3.0, (-2, GLANCE)), (250, 2.0, (-4, GLANCE * 0.8)), (258, 1.0, (-2, GLANCE * 0.4))):
    stand(H, f, W2A(G, (K.x, K.y, 0)), yaw_s, flex=2, head=hd, side=sd, arms=False, twist=-0.4 * hd[1])
    bent_arm("L", f)
    if f <= 224: bent_arm("R", f)
for s in "LR": apply_pose(G, s, "relaxed", 212)
path_pts = [(262, (K.x, K.y)), (300, (0.35, 0.75)), (345, (0.9, 1.6)), (395, (1.15, 2.55)), (440, (1.17, 3.6)), (480, (1.17, 4.6))]
def room_path(f):
    pts = path_pts
    if f <= pts[0][0]: return W2A(G, (pts[0][1][0], pts[0][1][1], 0))
    for (fa, a), (fb, b) in zip(pts, pts[1:]):
        if f <= fb:
            u = (f - fa) / (fb - fa); return W2A(G, (a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u, 0))
    return W2A(G, (pts[-1][1][0], pts[-1][1][1], 0))
def room_yaw(f):
    if f < 262: return yaw_s
    a = room_path(max(262, f - 6)); b = room_path(f + 6); d = b - a
    tgt = math.degrees(math.atan2(-d.x, d.y)) + 180 if d.length > 1e-4 else 180
    # MPFB faces -Y: yaw 180 faces +Y
    u = min(1.0, (f - 262) / 30.0); tgt = ((tgt + 180) % 360) - 180
    return yaw_s + (tgt - yaw_s if abs(tgt - yaw_s) <= 180 else tgt - yaw_s - 360 * math.copysign(1, tgt - yaw_s)) * smooth(u)
walk_with_arms(H, room_path, room_yaw, 262, 480, stride=1.0 / G.scale.x)
# book bag: on the floor until the cut at 211, then on her back
sc.frame_set(230)
bag_back = wear_bag(G, "BagBack", 230, yaw_s)
key_vis(["BagFloor"] + [c.name for c in bpy.data.objects["BagFloor"].children], [(1, 210)])
key_vis(["BagBack"] + [c.name for c in bpy.data.objects["BagBack"].children], [(211, 480)])
STRAP = make_straps(G, bag_back, 230, "BagBack_Strap")
key_vis([o.name for o in STRAP.values()], [(211, 480)])
# right hand comes up to the strap (228-234) and holds it through the walk out
def strap_frame(f):
    sc.frame_set(f); bpy.context.view_layer.update()
    o = STRAP["R"]; dg = bpy.context.evaluated_depsgraph_get(); oe = o.evaluated_get(dg); me = oe.to_mesh()
    i = STRAP_GRIP_I; Mw = o.matrix_world
    va = Mw @ me.vertices[2 * i].co; vb = Mw @ me.vertices[2 * i + 1].co
    t = (Mw @ me.vertices[2 * i + 2].co) - (Mw @ me.vertices[2 * i - 2].co)
    oe.to_mesh_clear()
    P = (va + vb) / 2; wv = (vb - va).normalized(); n = wv.cross(t).normalized()
    chest = G.matrix_world @ G.pose.bones["spine05"].head
    if n.dot(P - chest) < 0: n = -n
    tn = t.normalized(); med = chest - P; med = med - n * med.dot(n); med = (med - tn * med.dot(tn)).normalized()
    return P, n, med
P, n, med = strap_frame(228)
place_hand(G, "R", 228, P + n * 0.07 + Vector((0, 0, -0.03)), -n, med, skin=0.016)
apply_pose(G, "R", "relaxed", 228)
for f in range(234, 481, 2):
    P, n, med = strap_frame(f)
    place_hand(G, "R", f, P, -n, med, skin=0.022)
for f in (234, 300, 400, 480): apply_pose(G, "R", "shield", f)
for nm in ["BookBag"] + [c.name for c in bpy.data.objects["BookBag"].children]:
    bpy.data.objects[nm].hide_render = True; bpy.data.objects[nm].hide_viewport = True
key_vis(["Room_ToyBox", "Room_ToyBoxLogo"], [(1, 153), (211, 287)])   # source frames: only S01 and S03 (logo whole, flat-on)
# French doors: right leaf open the whole time (night rain visible outside), left leaf closed
bpy.data.objects["DoorLeafR"].rotation_euler = (0, 0, R_(-95))

cam_shot("S01", [(1, (0.78, -1.62, 0.55)), (130, (0.62, -1.3, 0.5))], lens=32,
         target_keys=[(1, (0.0, 0.05, 0.5)), (130, (0.0, 0.1, 0.55))])
cam_shot("S02", [(121, (0.9, -0.8, 0.76)), (220, (0.75, -0.6, 0.74))], lens=45,
         target_keys=[(121, (0.0, 0.2, 0.72)), (220, (0.0, 0.22, 0.74))])
cam_shot("S03", [(211, (0.25, -2.3, 0.95)), (340, (0.5, -1.7, 1.0))], lens=30,
         target_keys=[(211, (0.05, 0.4, 0.8)), (300, (0.4, 0.9, 0.85)), (340, (0.6, 1.3, 0.9))])
cam_shot("S04", [(331, (2.45, 0.6, 1.05)), (440, (2.25, 1.15, 1.1))], lens=28,
         target_keys=[(331, (0.75, 1.4, 0.85)), (400, (1.15, 2.6, 0.9)), (440, (1.17, 3.5, 0.9))])

# ================================================================== ROAD  (S05-S10, action 400-1100) and ghost (S21-S22)
G = girls["road"]; H = HS["road"]; XR = 100.0
SX = XR + 5.0                      # sidewalk line
v = 1.0 / 60.0                      # m per frame
def road_y(f): return -34.0 + max(0, min(f, 905) - 400) * v + (max(0, f - 905) * v * 0.15 if f < 925 else 20 * v * 0.15)
road_path = lambda f: W2A(G, (SX, road_y(f), 0))
walk_with_arms(H, road_path, lambda f: 180.0, 400, 905, stride=1.0 / G.scale.x)
# umbrella in the right hand: forearm up, fist in front of the shoulder
def umb_arm(f, p, yaw, look=(0, 0), out=-0.06):
    s = "R"; sx = -1
    body_hand(H, s, f, p, yaw, (H.sh[s].x + 0.07 - out - H.root_head.x, H.sh[s].y - H.root_head.y - 0.36, H.sh[s].z - H.root_head.z - 0.04),
              (0.35, -1.0, 0.0), (1.0, 0.35, 0.0), pole_off=(-0.35, 0.0, -0.5))
for f in range(400, 906, 2):
    p = road_path(f); p = Vector((p.x, p.y, H.root_head.z))
    umb_arm(f, p, 180.0)
# stop, look over the left shoulder at the car (905-960), then turn right and run into the trees (960-1100)
y_stop = road_y(925)
for f, hd, tw in ((925, (0, 0), 0), (940, (0, 14), 6), (958, (-2, 20), 8)):
    stand(H, f, W2A(G, (SX, y_stop, 0)), 180.0, flex=1, head=hd, twist=tw, arms=False)
    umb_arm(f, W2A(G, (SX, y_stop, 0)) + Vector((0, 0, H.root_head.z)), 180.0)
    body_hand(H, "L", f, W2A(G, (SX, y_stop, 0)) + Vector((0, 0, H.root_head.z)), 180.0, hang_off(H, "L"), (0, -0.15, -1), (-1, 0, 0))
for f in range(905, 962, 2):   # umbrella hand keyed continuously through the stop (no quaternion flip between keys)
    umb_arm(f, W2A(G, (SX, road_y(min(f, 925)), 0)) + Vector((0, 0, H.root_head.z)), 180.0)
run_pts = [(965, (SX, y_stop)), (985, (SX + 1.2, y_stop + 0.6)), (1010, (SX + 3.2, y_stop + 1.4)), (1050, (SX + 6.0, y_stop + 3.0)), (1100, (SX + 9.0, y_stop + 5.0))]
def run_path(f):
    for (fa, a), (fb, b) in zip(run_pts, run_pts[1:]):
        if f <= fb:
            u = max(0.0, (f - fa) / (fb - fa)); return W2A(G, (a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u, 0))
    return W2A(G, (run_pts[-1][1][0], run_pts[-1][1][1], 0))
def run_yaw(f):
    u = smooth((f - 960) / 22.0); return 180.0 + (110.0 - 180.0) * u   # turns to face +x (toward the trees)
H.walk(run_path, run_yaw, 960, 1100, stride=1.5 / G.scale.x, duty=0.42, lift=0.12, bob=0.035, crouch=0.04, lean=10, step=2)
dist = 0.0; prev = run_path(960)
for f in range(960, 1101, 2):
    p = run_path(f); dist += (p - prev).to_2d().length; prev = p
    ph = 2 * math.pi * dist / (1.5 / G.scale.x); pz = Vector((p.x, p.y, H.root_head.z - 0.04))
    # umbrella hand: lowered and held out to the side while she runs
    umb_arm(f, Vector((pz.x, pz.y, H.root_head.z)), run_yaw(f))   # umbrella stays up, as in the walk
    body_hand(H, "L", f, pz, run_yaw(f), (H.sh["L"].x + 0.05 - H.root_head.x, H.sh["L"].y - H.root_head.y - 0.06 - 0.16 * math.sin(ph),
              H.sh["L"].z - H.root_head.z - 0.36), (0, -0.7, 0.4), (-1, 0, 0), pole_off=(0.5, 0.35, -0.3))
umb_road = umb.copy(); umb_road.name = "UmbrellaRoad"; umb.users_collection[0].objects.link(umb_road)
sc.frame_set(420); bpy.context.view_layer.update()
wr, d, a, n, palm = hand_frame(G, "R")
ax = a.normalized()
if ax.z < 0: ax = -ax
umb_road.rotation_mode = 'QUATERNION'; umb_road.rotation_quaternion = (1, 0, 0, 0)
_low = [v.co for v in umb.data.vertices if v.co.z < -0.38 * 0.85]
_h = Vector((sum(c.x for c in _low), sum(c.y for c in _low), 0)).normalized() if _low else Vector((1, 0, 0))
umb_road.rotation_quaternion = _h.rotation_difference(Vector((1, 0, 0)))
UMB_GL = Vector((0, 0, -UMB_GRIP)); UMB_R = radius_at(umb, (0, 0, 1), UMB_GL, 0.04)
grip_prop(umb_road, G, "R", 400, Vector((0, 0, 1)), UMB_GL, UMB_R)
for s in "L": apply_pose(G, s, "relaxed", 400)
wear_bag(G, "BagRoad", 420, 180.0)
# soft warm face fill from the street-lamp side (<= 10 W) with a catchlight, riding with her head
fl = bpy.data.lights.new("FaceFill_Road", 'AREA'); fl.energy = 8; fl.size = 0.35; fl.color = (1.0, 0.85, 0.65)
flo = bpy.data.objects.new("FaceFill_Road", fl); sc.collection.objects.link(flo)
sc.frame_set(560); bpy.context.view_layer.update()
hp_ = G.matrix_world @ G.pose.bones["head"].head
flo.location = hp_ + Vector((0.35, 0.55, 0.05)); flo.rotation_euler = (hp_ - flo.location).to_track_quat('-Z', 'Y').to_euler()
attach(flo, G, "head")
# the motorist's car: passes from behind (S07), stops ahead (S08), holds with brake/head lights (S09-S10)
car = bpy.data.objects["Car"]
car.rotation_euler = (0, 0, 0)
CAR_KEYS = [(600, road_y(661) - 40.0), (661, road_y(661) - 22.0), (722, road_y(722) + 0.5), (780, road_y(780) + 13.0), (815, road_y(800) + 16.0), (870, road_y(800) + 16.0), (955, road_y(800) + 12.0), (1100, road_y(800) + 12.0)]   # 870-955: reverses slowly back toward her
car_y = pchip([(f_, y_) for f_, y_ in CAR_KEYS])
for f in range(600, 1101, 4):
    car.location = (XR + 1.9, car_y(f), 0.0); car.keyframe_insert("location", frame=f)
hl = []
for sx_ in (-0.6, 0.6):
    l = bpy.data.lights.new("CarHead", 'SPOT'); l.energy = 600; l.spot_size = R_(45); l.spot_blend = 0.5; l.color = (1.0, 0.95, 0.85)
    o = bpy.data.objects.new("CarHeadlight", l); sc.collection.objects.link(o); o.parent = car
    o.location = (sx_, 0, 0.7); hl.append(o)
    l2 = bpy.data.lights.new("CarTail", 'POINT'); l2.energy = 15; l2.color = (1.0, 0.1, 0.05); l2.shadow_soft_size = 0.05
    o2 = bpy.data.objects.new("CarTaillight", l2); sc.collection.objects.link(o2); o2.parent = car; o2.location = (sx_, 0, 0.8)
print("CAR dims", tuple(round(x, 2) for x in car.dimensions))

cam_shot("S05", [(421, (SX - 0.9, road_y(421) - 3.4, 0.85)), (560, (SX - 0.8, road_y(560) - 2.6, 0.9))], lens=32,
         target_keys=[(421, (SX, road_y(421), 1.25)), (560, (SX, road_y(560), 1.25))])
cam_shot("S06", [(541, (SX - 1.6, road_y(541) + 3.0, 1.0)), (680, (SX - 1.5, road_y(680) + 2.4, 1.0))], lens=35,
         target_keys=[(541, (SX, road_y(541), 1.1)), (680, (SX, road_y(680), 1.12))])
cam_shot("S07", [(661, (XR - 0.4, road_y(661) - 3.2, 1.25)), (730, (XR - 0.4, road_y(730) - 3.1, 1.25)), (800, (XR - 0.4, road_y(800) - 3.0, 1.25))], lens=30,
         target_keys=[(661, (SX - 0.2, road_y(661) + 0.6, 0.95)), (730, (SX - 0.2, road_y(730) + 0.6, 0.95)), (800, (SX - 0.2, road_y(800) + 0.6, 0.95))])
cam_shot("S08", [(781, (XR - 4.0, road_y(781) - 12.0, 4.2)), (890, (XR - 3.6, road_y(890) - 10.5, 4.0))], lens=26,
         target_keys=[(781, (XR + 3.5, road_y(781) + 5.0, 0.6)), (890, (XR + 3.5, road_y(890) + 5.0, 0.6))])
cam_shot("S09", [(871, (SX + 0.6, road_y(871) - 2.6, 0.95)), (980, (SX + 0.9, road_y(925) - 2.1, 0.95))], lens=30,
         target_keys=[(871, (SX - 0.4, road_y(871) + 3.0, 1.0)), (980, (SX - 0.6, road_y(925) + 3.0, 1.0))])
cam_shot("S10", [(961, (XR + 2.4, y_stop - 1.5, 1.05)), (1100, (XR + 3.0, y_stop - 0.2, 1.2))], lens=28,
         target_keys=[(961, (SX + 0.3, y_stop + 0.3, 0.9)), (1040, (SX + 4.0, y_stop + 2.0, 0.8)), (1100, (SX + 6.5, y_stop + 3.5, 0.8))])

# ---- memory figure (cyan, solid, softly glowing) on the road further up
GG = girls["ghost"]; HG = HS["ghost"]
ghost_m = bpy.data.materials.new("MemoryCyan"); ghost_m.use_nodes = True; Pn = ghost_m.node_tree.nodes["Principled BSDF"]
Pn.inputs["Base Color"].default_value = (0.05, 0.5, 1.0, 1); Pn.inputs["Emission Color"].default_value = (0.05, 0.55, 1.0, 1)
Pn.inputs["Emission Strength"].default_value = 1.1; Pn.inputs["Roughness"].default_value = 0.4
# (v002b) no glow, no see-through: the memory figure is the girl herself in her real clothes; the beat reads by its cooler grade
gy = lambda f: 62.0 + max(0, f - 2250) * v
walk_with_arms(HG, lambda f: W2A(GG, (XR + 1.6, gy(f), 0)), lambda f: 180.0, 2250, 2500, stride=1.0 / GG.scale.x)
for f in range(2250, 2501, 2):
    p = W2A(GG, (XR + 1.6, gy(f), 0)); p.z = HG.root_head.z
    HH = H; H = HG; umb_arm(f, p, 180.0); H = HH
umb_g = umb.copy(); umb_g.name = "UmbrellaGhost"; umb.users_collection[0].objects.link(umb_g)
sc.frame_set(2300); bpy.context.view_layer.update()
wr, d, a, n, palm = hand_frame(GG, "R"); ax = a.normalized()
if ax.z < 0: ax = -ax
umb_g.rotation_mode = 'QUATERNION'; umb_g.rotation_quaternion = umb_road.rotation_quaternion.copy()
grip_prop(umb_g, GG, "R", 2250, Vector((0, 0, 1)), UMB_GL, UMB_R); apply_pose(GG, "L", "relaxed", 2250)
wear_bag(GG, "BagGhost", 2260, 180.0)
cam_shot("S21", [(2281, (XR + 0.6, gy(2281) - 3.2, 0.9)), (2390, (XR + 0.8, gy(2390) - 2.6, 0.95))], lens=32,
         target_keys=[(2281, (XR + 1.6, gy(2281), 1.0)), (2390, (XR + 1.6, gy(2390), 1.05))])
cam_shot("S22", [(2371, (XR - 1.6, gy(2371) + 0.5, 1.0)), (2480, (XR - 1.4, gy(2480) - 0.2, 1.05))], lens=35,
         target_keys=[(2371, (XR + 1.6, gy(2371), 0.95)), (2480, (XR + 1.6, gy(2480), 0.95))])

# ================================================================== WOODS run (S11-S12, action 1060-1290)
G = girls["woods"]; H = HS["woods"]; XW = 200.0
wy = lambda f: -8.0 + (f - 1060) * 3.0 / 60.0
def wpath(f): return W2A(G, (XW + 0.4 * math.sin((f - 1060) / 70.0), wy(f), 0))
def wyaw(f):
    a = wpath(f - 2); b = wpath(f + 2); d = b - a
    return math.degrees(math.atan2(-d.x, d.y)) + 180.0 - 180.0 + 180.0 if False else 180.0 + math.degrees(math.atan2(-(b - a).x, (b - a).y))
H.walk(wpath, lambda f: 180.0 - math.degrees(math.atan2((wpath(f + 2) - wpath(f - 2)).x, (wpath(f + 2) - wpath(f - 2)).y)) + 0.0 if False else 180.0,
       1060, 1290, stride=1.7 / G.scale.x, duty=0.40, lift=0.14, bob=0.04, crouch=0.05, lean=12, step=2)
dist = 0.0; prev = wpath(1060)
for f in range(1060, 1291, 2):
    p = wpath(f); dist += (p - prev).to_2d().length; prev = p
    ph = 2 * math.pi * dist / (1.7 / G.scale.x); pz = Vector((p.x, p.y, H.root_head.z - 0.05))
    for s, sg in (("L", -1), ("R", 1)):
        sx = 1 if s == "L" else -1
        body_hand(H, s, f, pz, 180.0, (H.sh[s].x + 0.04 * sx - H.root_head.x, H.sh[s].y - H.root_head.y - 0.06 + sg * 0.17 * math.sin(ph),
                  H.sh[s].z - H.root_head.z - 0.34 + 0.05 * abs(math.sin(ph))), (0, -0.7, 0.4), (-sx, 0, 0), pole_off=(0.5 * sx, 0.35, -0.3))
wear_bag(G, "BagWoods", 1070, 180.0)
cam_shot("S11", [(1081, (XW - 2.4, wy(1081) - 1.0, 1.0)), (1190, (XW - 2.4, wy(1190) - 1.6, 1.05))], lens=28,
         target_keys=[(1081, (XW, wy(1081), 0.85)), (1190, (XW, wy(1190), 0.85))])
cam_shot("S12", [(1171, (XW - 0.8, wy(1171) - 4.0, 1.5)), (1290, (XW - 0.7, wy(1171) - 3.0, 1.5))], lens=30,
         target_keys=[(1171, (XW, wy(1171) + 2.0, 0.9)), (1290, (XW, wy(1290), 0.9))])

# ================================================================== SHED (S13-S14, day, action 1240-1530)
XS = 300.0
H = HS["SearchA"]; R = SA
a_pos = Vector((XS + 1.35, 0.25)); a_yaw = 18.0
for f, hd, tw in ((1240, (14, 0), 0), (1300, (18, -4), 0), (1360, (16, 4), 0), (1420, (20, 0), 0), (1460, (6, -14), -6), (1500, (-2, -22), -10), (1530, (0, -20), -10)):
    stand(H, f, Vector((a_pos.x, a_pos.y, 0)), a_yaw, flex=4, head=hd, twist=tw, arms=False)
    pz = Vector((a_pos.x, a_pos.y, H.root_head.z))
    # left hand holds the clipboard at chest height; right hand rests at his side
    body_hand(H, "L", f, pz, a_yaw, (0.07, -0.48, 0.33), (-0.3, -0.45, 0.35), (-0.1, -1.0, 0.25), pole_off=(0.45, 0.25, -0.25))
    body_hand(H, "R", f, pz, a_yaw, hang_off(H, "R"), (0, -0.15, -1), (1, 0, 0))
sc.frame_set(1240); bpy.context.view_layer.update()
wr, d, a, n, palm = hand_frame(SA, "L")
clip.rotation_mode = 'QUATERNION'
# board plane faces his eyes: normal ~ toward the head, long side up
headp = SA.matrix_world @ SA.pose.bones["head"].head
nrm = (headp - palm).normalized()
q1 = Vector((0, 0, 1)).rotation_difference(nrm)
clip.rotation_quaternion = q1
clip.location = palm + n * 0.012 + (d * 0.0) + Rz(a_yaw) @ Vector((-0.10, 0, 0.04))
bpy.context.view_layer.update(); attach(clip, SA, "wrist.L"); apply_pose(SA, "L", "hold_flat_object", 1240); apply_pose(SA, "R", "relaxed", 1240)
H = HS["SearchB"]
b_pos = Vector((XS - 0.75, 0.62)); b_yaw = 150.0
for f, hd in ((1240, (10, 0)), (1320, (14, 10)), (1400, (12, -8)), (1530, (14, 0))):
    squat(H, f, Vector((b_pos.x, b_pos.y, 0)), b_yaw, depth=0.45, flex=26, head=hd)
for s in "LR": apply_pose(SB, s, "relaxed", 1240)
cam_shot("S13", [(1261, (XS + 0.2, -4.6, 1.55)), (1400, (XS + 0.6, -3.9, 1.5))], lens=30,
         target_keys=[(1261, (XS + 0.2, 1.0, 0.95)), (1400, (XS + 0.4, 1.0, 0.95))])
cam_shot("S14", [(1381, (XS + 1.95, -1.7, 1.55)), (1530, (XS + 1.75, -1.45, 1.55))], lens=35,
         target_keys=[(1381, (a_pos.x, a_pos.y, 1.35)), (1530, (a_pos.x, a_pos.y, 1.4))])

# ================================================================== WOODS search with torches (S15-S16, dusk, action 1480-1830)
CL = Vector((XW + 12.0, 10.0))
torches = []
def torch_for(rig, f0):
    t = torch_src.copy(); t.data = torch_src.data; t.name = "Torch_" + rig.name; torch_src.users_collection[0].objects.link(t)
    sc.frame_set(f0); bpy.context.view_layer.update()
    wr, d, a, n, palm = hand_frame(rig, "R")
    t.rotation_mode = 'QUATERNION'
    # torch axis (its local x) along the thumb side so it points forward out of the fist
    t.rotation_quaternion = Vector((1, 0, 0)).rotation_difference(a)
    TGL = Vector((-0.04, 0, 0)); TR = radius_at(torch_src, (1, 0, 0), TGL, 0.02)
    grip_prop(t, rig, "R", f0, a, TGL, TR)
    l = bpy.data.lights.new("TorchBeam_" + rig.name, 'SPOT'); l.energy = 700; l.spot_size = R_(30); l.spot_blend = 0.35; l.color = (1.0, 0.95, 0.85); l.shadow_soft_size = 0.02
    lo = bpy.data.objects.new("TorchBeam_" + rig.name, l); sc.collection.objects.link(lo)
    lo.parent = t; lo.location = (0.1, 0, 0); lo.rotation_mode = 'XYZ'; lo.rotation_euler = (0, R_(90), 0)   # spot looks down its -Z -> along +x
    gl = bpy.data.lights.new("TorchGlow_" + rig.name, 'POINT'); gl.energy = 2.0; gl.color = (1.0, 0.95, 0.85); gl.shadow_soft_size = 0.02
    go = bpy.data.objects.new("TorchGlow_" + rig.name, gl); sc.collection.objects.link(go); go.parent = t; go.location = (0.11, 0, 0)
    return t

def search_walk(Hh, rig, pts, f0, f1, sweep_phase=0.0):
    """walk slowly through pts, the torch arm raised forward and sweeping left-right"""
    def path(f):
        u = max(0.0, min(1.0, (f - f0) / (f1 - f0))); seg = u * (len(pts) - 1); i = min(int(seg), len(pts) - 2); t = seg - i
        a_, b_ = pts[i], pts[i + 1]; return Vector((a_[0] + (b_[0] - a_[0]) * t, a_[1] + (b_[1] - a_[1]) * t, 0))
    def yaw(f):
        a_ = path(f - 6); b_ = path(f + 6); d_ = b_ - a_
        return 180.0 + math.degrees(math.atan2(-d_.x, d_.y)) if d_.length > 1e-3 else 180.0
    Hh.walk(path, yaw, f0, f1, stride=1.3, step=2, crouch=0.02, lean=4, bob=0.012)
    for f in range(f0, f1 + 1, 2):
        p = path(f); pz = Vector((p.x, p.y, Hh.root_head.z)); sw = math.sin((f - f0) / 45.0 + sweep_phase)
        body_hand(Hh, "R", f, pz, yaw(f), (Hh.sh["R"].x - Hh.root_head.x - 0.05 + 0.14 * sw, Hh.sh["R"].y - Hh.root_head.y - 0.38, Hh.sh["R"].z - Hh.root_head.z - 0.22),
                  (0.0, -1.0, 0.0), (0.0, 0.0, -1.0), pole_off=(-0.5, 0.25, -0.35))
        body_hand(Hh, "L", f, pz, yaw(f), hang_off(Hh, "L"), (0, -0.15, -1), (-1, 0, 0))
    return path, yaw
pB, yB = search_walk(HS["SearchB2"], SB2, [(CL.x - 3.0, CL.y - 4.0), (CL.x - 2.0, CL.y - 1.0), (CL.x - 1.5, CL.y + 2.0)], 1480, 1830, 0.0)
pA, yA = search_walk(HS["SearchA2"], SA2, [(CL.x + 2.5, CL.y - 3.0), (CL.x + 2.0, CL.y + 0.0), (CL.x + 2.8, CL.y + 3.0)], 1480, 1830, 1.7)
H = HS["SearchC"]
c_pos = Vector((CL.x - 0.2, CL.y - 2.4)); c_yaw = 160.0
for f, hd in ((1480, (18, 0)), (1560, (22, 15)), (1640, (16, -15)), (1720, (20, 5)), (1830, (18, 0))):
    def ch(p, f=f):
        HC = HS["SearchC"]
        body_hand(HC, "R", f, p, c_yaw, (HC.sh["R"].x - HC.root_head.x - 0.08, -0.52, -0.02), (0.0, -1.0, -0.35), (0.0, 0.0, -1.0), pole_off=(-0.5, 0.1, -0.3))
        body_hand(HC, "L", f, p, c_yaw, (HC.ankle["L"].x * 1.3, -0.30, HC.root_head.z * 0.53 - p.z + 0.05), (0, -1.0, -0.6), (-0.3, 0, -1.0), pole_off=(0.5, 0.2, 0.0))
    squat(H, f, Vector((c_pos.x, c_pos.y, 0)), c_yaw, depth=0.45, flex=24, head=hd, hands=ch)
for r in (SB2, SA2, SC):
    torches.append(torch_for(r, 1480))
    apply_pose(r, "L", "relaxed", 1480)
for r in (SB2, SA2, SC): vis_char(r, [(1480, 1830)])
for _g in ('SearchA2.gloves',):
    _o = bpy.data.objects.get(_g)
    if _o:
        _o.animation_data_clear(); _o.hide_render = True; _o.hide_viewport = True
for r in (SA, SB): vis_char(r, [(1240, 1530)])
vis_char(girls["woods"], [(1060, 1290)]); vis_char(girls["ghost"], [(2250, 2500)])
cam_shot("S15", [(1501, (CL.x - 1.5, CL.y - 9.0, 2.0)), (1660, (CL.x - 0.5, CL.y - 8.0, 1.9))], lens=26,
         target_keys=[(1501, (CL.x, CL.y - 1.0, 1.0)), (1660, (CL.x, CL.y - 0.5, 1.0))])
cam_shot("S16", [(1651, (CL.x - 3.6, CL.y + 2.6, 1.55)), (1830, (CL.x - 3.4, CL.y + 3.4, 1.55))], lens=32,
         target_keys=[(1651, (CL.x - 2.0, CL.y - 1.0, 1.3)), (1830, (CL.x - 1.6, CL.y + 1.6, 1.4))])

# ================================================================== SITE (S17-S20, day, action 1780-2310)
XT = 400.0
bag_site = copy_bag("BagSite")
bag_site.rotation_mode = 'XYZ'
# lying on its back (front with badges up), slightly turned
rot_up = (R_(-90), 0, 0)
bag_site.rotation_euler = Euler(rot_up); bag_site.rotation_euler.z = R_(20)
bpy.context.view_layer.update()
bz = -min((bag_site.matrix_world @ Vector(c)).z for c in bag_site.bound_box)
bag_site.location = (XT + 0.15, 0.3, bz + 0.005)
# clear plastic wrap: a loose, crinkled shell around the bag (cloudy, not x-ray clear)
bpy.context.view_layer.update()
_bb = [bag_site.matrix_world @ Vector(c) for c in bag_site.bound_box]
_mn = Vector([min(q[i] for q in _bb) for i in range(3)]); _mx = Vector([max(q[i] for q in _bb) for i in range(3)])
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=5, radius=1.0, location=(_mn + _mx) / 2)
wrap = bpy.context.object; wrap.name = "BagWrap"; wrap.scale = (_mx - _mn) * 0.75
for uc in list(wrap.users_collection): uc.objects.unlink(wrap)
bag_site.users_collection[0].objects.link(wrap)
shw = wrap.modifiers.new("shrink", 'SHRINKWRAP'); shw.target = bag_site; shw.wrap_method = 'NEAREST_SURFACEPOINT'; shw.offset = 0.012
dsp = wrap.modifiers.new("crinkle", 'DISPLACE'); tx = bpy.data.textures.new("Crinkle", 'VORONOI'); tx.noise_scale = 0.03; dsp.texture = tx; dsp.strength = 0.012
pm = bpy.data.materials.new("PlasticWrap"); pm.use_nodes = True; Pn = pm.node_tree.nodes["Principled BSDF"]
Pn.inputs["Base Color"].default_value = (0.9, 0.92, 0.95, 1); Pn.inputs["Roughness"].default_value = 0.2; Pn.inputs["Alpha"].default_value = 0.45
Pn.inputs["Coat Weight"].default_value = 0.6
if hasattr(pm, "blend_method"): pm.blend_method = 'HASHED'
wrap.data.materials.clear(); wrap.data.materials.append(pm)
bpy.context.view_layer.update()
SITE_TOP = max((bag_site.matrix_world @ Vector(c)).z for c in bag_site.bound_box)
H = HS["Worker"]
w_pos = Vector((XT + 0.72, 0.38)); w_yaw = -90.0 + 0.0   # faces -x toward the bag
bag_c = Vector(bag_site.location) + Vector((0, 0, 0.0))
# (v002b) he reaches, takes the wrapped bag by its two ends, lifts it while he rises, turns it to look, lowers it and looks up
lp = bpy.data.objects.get("BagSite_Loop")
if lp: lp.rotation_euler = (0, 0, 0); lp.location = (0, 0, 0.362)   # carry loop folded flat on the bag top, inside the plastic
bpy.context.view_layer.update()
M0 = bag_site.matrix_world.copy(); R0 = M0.to_quaternion(); C0 = M0 @ Vector((0, 0, 0.18))
carrier = bpy.data.objects.new("BagCarrier", None); sc.collection.objects.link(carrier)
carrier.rotation_mode = 'QUATERNION'; carrier.location = C0; carrier.rotation_quaternion = R0
bpy.context.view_layer.update()
for o in (bag_site, wrap):
    o.parent = carrier; o.matrix_parent_inverse = carrier.matrix_world.inverted()
bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get(); Ci = carrier.matrix_world.inverted()
zs = []; XLO = YLO = 9.0; XHI = YHI = -9.0
for ob in (wrap, lp) if lp else (wrap,):
    oe = ob.evaluated_get(dg); me = oe.to_mesh()
    for v in me.vertices:
        q = Ci @ (ob.matrix_world @ v.co)
        if abs(q.x) < 0.06 and abs(q.y) < 0.045: zs.append(q.z)
        if ob is wrap and abs(q.z) < 0.12: XLO = min(XLO, q.x); XHI = max(XHI, q.x); YLO = min(YLO, q.y); YHI = max(YHI, q.y)
    oe.to_mesh_clear()
ZP, ZM = max(zs), min(zs)
AX = R0 @ Vector((0, 0, 1))
R_END = ZP if AX.y > 0 else ZM; L_END = ZM if AX.y > 0 else ZP
sgn = 1.0 if (Quaternion(AX, R_(90)) @ R0 @ Vector((0, -1, 0))).x > 0 else -1.0
print("SITE box", round(XLO, 3), round(XHI, 3), round(YLO, 3), round(YHI, 3), "ends", round(ZP, 3), round(ZM, 3), "axis", tuple(round(x, 2) for x in AX), "tilt sign", sgn)
def key_carrier(f, c, tilt=0.0, yaw=0.0):
    carrier.location = c
    carrier.rotation_quaternion = Quaternion((0, 0, 1), R_(yaw)) @ Quaternion(AX, R_(sgn * tilt)) @ R0
    carrier.keyframe_insert("location", frame=f); carrier.keyframe_insert("rotation_quaternion", frame=f)
WX, WY = w_pos.x, w_pos.y
for f, c, tl, yw in ((1780, C0, 0, 0), (1966, C0, 0, 0), (2002, Vector((WX - 0.52, WY - 0.02, 0.42)), 35, 0),
                     (2040, Vector((WX - 0.46, WY, 0.98)), 88, 0), (2066, Vector((WX - 0.47, WY, 1.04)), 92, 0),
                     (2092, Vector((WX - 0.47, WY + 0.02, 1.07)), 100, 5), (2122, Vector((WX - 0.47, WY - 0.02, 1.07)), 98, -12),
                     (2150, Vector((WX - 0.46, WY, 1.04)), 92, 0), (2188, Vector((WX - 0.38, WY, 0.94)), 72, 0), (2278, Vector((WX - 0.38, WY, 0.93)), 70, 0)):
    key_carrier(f, c, tl, yw)
def noh(p): pass
# body: deep squat over the bag, rises as he lifts it, nearly upright at the end with the head up
BODY = [(1780, 0.5, 40, (-14, 0), 0), (1900, 0.5, 40, (-12, 0), 0), (1928, 0.54, 52, (-14, 0), 0), (1945, 0.56, 60, (-20, 0), 0), (1966, 0.56, 60, (-20, 0), 0),
        (2004, 0.38, 40, (0, 0), 0), (2040, 0.17, 16, (16, 0), 0), (2092, 0.15, 14, (22, 10), 3), (2122, 0.15, 14, (22, -10), -3),
        (2152, 0.14, 12, (18, 0), 0), (2190, 0.07, 5, (-10, -18), -6), (2235, 0.06, 4, (-16, -26), -9), (2278, 0.06, 4, (-14, -24), -8)]
for f, dep, fl, hd, tw in BODY:
    squat(H, f, Vector((w_pos.x, w_pos.y, 0)), w_yaw, depth=dep, flex=fl, head=hd, twist=tw, hands=(None if f <= 1900 else noh), hips_back=0.10 * dep / 0.5)
def key_pole(s, f, W):
    nme = "Pole_elbow." + s; pb = H.r.PB[nme]; Wa = to_arm(WK, W)
    pb.location = H.r.rest(nme).to_3x3().inverted() @ (Wa - H.r.BN[nme].head_local); pb.keyframe_insert("location", frame=f, group=nme)
def end_hands(f, approach=0.0):
    sc.frame_set(f); bpy.context.view_layer.update()
    M = carrier.matrix_world; M3 = M.to_3x3()
    for s_, zz in (("R", R_END), ("L", L_END)):
        sx = 1 if s_ == "L" else -1
        nrm = (M3 @ Vector((0, 0, -1 if zz > 0 else 1))).normalized()          # palm faces the bag end
        P_ = M @ Vector((0, 0, zz)) - nrm * approach + Vector((0, 0, approach * 0.6))
        fd = Vector((-1, 0, -0.25)); fd = (fd - nrm * fd.dot(nrm)).normalized()
        root = WK.matrix_world @ WK.pose.bones["root"].head
        key_pole(s_, f, root + Rz(w_yaw) @ Vector((0.55 * sx, 0.35, 0.0)))
        place_hand(WK, s_, f, P_, nrm, fd, skin=0.011)
        for _ in range(2):   # fingers follow the forearm line (no wrist bend past its limits)
            sc.frame_set(f); bpy.context.view_layer.update()
            el = WK.matrix_world @ WK.pose.bones["lowerarm01." + s_].head
            fa = P_ - el; fa = fa - nrm * fa.dot(nrm)
            if fa.length > 1e-3: fd = (fa.normalized() * 0.8 + fd * 0.2).normalized()
            place_hand(WK, s_, f, P_, nrm, fd, skin=0.011)
        # if the wrist limit tilts the hand into the bag end, slide the hand out until palm and fingertips clear it by 6 mm
        skin_ = 0.011
        for _ in range(4):   # hand SKIN (body mesh) 4 mm off the plastic: in or out as needed
            sc.frame_set(f); bpy.context.view_layer.update()
            surf = M @ Vector((0, 0, zz)) - nrm * approach
            dg_ = bpy.context.evaluated_depsgraph_get(); be = WKB.evaluated_get(dg_); bm_ = be.to_mesh(); mwb = WKB.matrix_world
            Cq = M.inverted() @ mwb
            over = [Cq @ bm_.vertices[i].co for i in HANDV[s_]]
            over = [q for q in over if XLO < q.x < XHI and YLO < q.y < YHI]   # only skin that is over the end face
            out_ = min((q.z * (1 if zz > 0 else -1) - abs(zz)) for q in over) - approach if over else 0.004
            be.to_mesh_clear()
            if abs(out_ - 0.004) < 0.0015: break
            skin_ += 0.004 - out_
            place_hand(WK, s_, f, P_, nrm, fd, skin=skin_)
for s_ in "LR":
    apply_pose(WK, s_, "relaxed", 1780); apply_pose(WK, s_, "relaxed", 1928); apply_pose(WK, s_, "flat_palm", 1946); apply_pose(WK, s_, "flat_palm", 2278)
WKB = bpy.data.objects["Worker.body"]; _mods = [(m, m.show_viewport) for m in WKB.modifiers if m.type in ("MASK", "SUBSURF")]
for m, _v in _mods: m.show_viewport = False
_gi = {g.index: g.name for g in WKB.vertex_groups}; HANDV = {"L": [], "R": []}
for v in WKB.data.vertices:
    gs = [g for g in v.groups if g.weight > 0.3 and _gi[g.group] in WK.data.bones]
    if not gs: continue
    nm = _gi[max(gs, key=lambda g: g.weight).group]
    if nm.startswith(("wrist.", "metacarpal", "finger")): HANDV[nm[-1]].append(v.index)
print("HAND verts", {k: len(v) for k, v in HANDV.items()})
end_hands(1928, approach=0.09)
for f in range(1946, 2279, 2): end_hands(f)
for m, _v in _mods: m.show_viewport = _v
NAMESET_EXTRA = {"BagCarrier": "site"}
cam_shot("S17", [(1801, (XT - 0.25, -0.42, 0.42)), (1900, (XT - 0.12, -0.25, 0.36))], lens=40,
         target_keys=[(1801, (XT + 0.15, 0.3, 0.08)), (1900, (XT + 0.15, 0.3, 0.08))])
cam_shot("S18", [(1891, (XT - 0.5, -1.45, 0.42)), (2050, (XT - 0.35, -1.25, 0.42))], lens=28,
         target_keys=[(1891, (XT + 0.5, 0.35, 0.45)), (2050, (XT + 0.45, 0.35, 0.45))])
cam_shot("S19", [(2041, (XT + 0.05, -0.62, 0.55)), (2200, (XT + 0.2, -0.5, 0.5))], lens=35,
         target_keys=[(2041, (XT + 0.35, 0.3, 0.2)), (2200, (XT + 0.35, 0.3, 0.2))])
cam_shot("S20", [(2191, (XT - 0.15, -1.15, 0.38)), (2300, (XT - 0.05, -1.0, 0.38))], lens=30,
         target_keys=[(2191, (XT + 0.6, 0.38, 0.62)), (2300, (XT + 0.6, 0.38, 0.65))])

# ================================================================== WALL (S23-S24)
XP = 500.0
_pm = bpy.data.materials["PortraitPhoto"]; _nt = _pm.node_tree; _P = _nt.nodes["Principled BSDF"]
_ti = _nt.nodes.new("ShaderNodeTexImage"); _ti.image = bpy.data.images.load(HERE + "assets/portrait.png"); _ti.image.pack()
_nt.links.new(_ti.outputs["Color"], _P.inputs["Base Color"]); _P.inputs["Roughness"].default_value = 0.3
cam_shot("S23", [(2461, (XP + 0.0, -2.3, 2.45)), (2680, (XP + 0.0, -1.55, 2.5))], lens=40,
         target_keys=[(2461, (XP, 0, 2.48)), (2680, (XP, 0, 2.5))])
cam_shot("S24", [(2671, (XP + 0.5, -1.9, 2.42)), (2880, (XP + 0.25, -1.6, 2.48))], lens=45,
         target_keys=[(2671, (XP + 0.0, 0, 2.5)), (2880, (XP, 0, 2.5))])

for nm in ("Umbrella", "Torch", "Clipboard_src"):
    o = bpy.data.objects.get(nm)
    if o: o.hide_render = True; o.hide_viewport = True
# ---- keep every camera path clear: no vegetation instance within 1.6 m (xy) of any camera position
cams = [o for o in bpy.data.objects if o.name.startswith("CAM_")]
pts = []
for c in cams:
    for f in range(1, 2881, 10):
        pass
for sid, setn, f0, f1, note in SHOTS:
    c = bpy.data.objects["CAM_" + sid]
    for f in range(f0, f1 + 1, 6):
        sc.frame_set(f); pts.append(c.matrix_world.translation.copy())
removed = 0
for o in list(bpy.data.objects):
    if o.name.startswith(("Woods_Under", "Woods_Tree", "Woods_LaneTree", "Road_Shrub", "Shed_Under", "Shed_Tree", "Site_Tree", "Road_Tree")):
        rad = 4.5 if o.name.startswith("Woods_Tree") else 1.6
        if any((o.location.xy - p.xy).length < rad for p in pts):
            bpy.data.objects.remove(o); removed += 1
print("CLEARED near-lens vegetation", removed)
bar = bpy.data.objects.get("Site_Barrier")
if bar: bar.location = (XT - 2.6, 4.6, 0); bar.rotation_euler = (0, 0, R_(20))
# ================================================================== per-shot world / sun (constant keys at the cuts)
sun = bpy.data.lights["Sun"]; bg = sc.world.node_tree.nodes["Background"]
bpy.context.preferences.edit.keyframe_new_interpolation_type = 'CONSTANT'
LOOK = {"room": (0.0, (0.03, 0.045, 0.09), 0.6), "road": (0.0, (0.045, 0.06, 0.13), 1.0), "woods": (0.0, (0.07, 0.09, 0.18), 1.0),
        "shed": (4.5, (0.55, 0.72, 0.95), 1.0), "site": (4.5, (0.6, 0.75, 0.95), 1.0), "wall": (0.0, (0.05, 0.04, 0.03), 0.3)}
for sid, setn, f0, f1, note in SHOTS:
    se, col, st = LOOK[setn]
    sun.energy = se; sun.keyframe_insert("energy", frame=f0)
    bg.inputs["Color"].default_value = (*col, 1); bg.inputs["Color"].keyframe_insert("default_value", frame=f0)
    bg.inputs["Strength"].default_value = st; bg.inputs["Strength"].keyframe_insert("default_value", frame=f0)
set_interp(sun, 'CONSTANT'); set_interp(sc.world.node_tree, 'CONSTANT')
print("INTERP", [kp.interpolation for fc in fcurves_of(sun) for kp in fc.keyframe_points][:4])
# a soft face fill that rides with the woods-search camera (<=10 W rule is about faces: keep it gentle)
json.dump([{"shot": s[0], "set": s[1], "f0": s[2], "f1": s[3], "note": s[4]} for s in SHOTS], open(HERE + "shots_provisional.json", "w"), indent=1)
bpy.ops.wm.save_as_mainfile(filepath=out, compress=True)
print("SHOTS_DONE")
