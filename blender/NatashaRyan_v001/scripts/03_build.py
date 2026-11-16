"""NatashaRyan Phase 1: sets, per-beat character actions (each ~30% longer than its provisional window),
one camera per shot, hard cuts by timeline markers. Provisional timing follows the reference film's beat order and pacing;
Phase 2 re-lays the shot windows to the VO word frames without stretching any animation.
blender -b work/dressed.blend --python 03_build.py -- work/film.blend"""
import bpy, bmesh, sys, math, json, random, os
from mathutils import Vector, Matrix, Euler, Quaternion
P_ = "/home/user/Muhammed/blender/pipeline/"; HERE = "/home/user/Muhammed/blender/NatashaRyan_v001/"
exec(open(P_ + "anim_lib.py").read()); exec(open(P_ + "hand_poses.py").read()); exec(open(HERE + "scripts/nat_lib.py").read())
out = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene; sc.render.fps = 60; sc.frame_start = 1
R_ = math.radians; random.seed(7)
A = HERE + "assets/"

SHOTS = [  # id, set, f0, f1, note  (provisional: reference pacing)
    ("S01", "port", 1, 150, "In 1998, a 14-year-old girl - school-photo sitting, medium"),
    ("S02", "port", 151, 240, "Natasha - close, she lifts her chin and smiles"),
    ("S03", "school", 241, 360, "was dropped off - aerial push toward the school, car at the kerb"),
    ("S04", "school", 361, 450, "by her mother - mother by the car waves, Natasha walks to school"),
    ("S05", "school", 451, 540, "at school. But she didn't - Natasha walks up the path toward camera"),
    ("S06", "home", 541, 660, "return home later that day - dusk, mother on the front path looks up and down the street"),
    ("S07", "field", 661, 780, "Her family contacted the police - searcher in orange walks the tall grass"),
    ("S08", "field", 781, 900, "but they couldn't find her - wide, two searchers; one crouches"),
    ("S09", "school", 901, 1080, "days turned into weeks, into months - memorial table at the school fence, light fades"),
    ("S10", "kitchen", 1081, 1260, "her parents started to assume the worst - mother at the kitchen table, father at the window"),
    ("S11", "station", 1261, 1380, "Then a year later, a local - officers walk a man out of the station"),
    ("S12", "station", 1381, 1500, "serial killer admitted - closer, his head down"),
    ("S13", "station", 1501, 1620, "to the murder of Natasha - side tracking"),
    ("S14", "kitchen", 1621, 1740, "Her family was devastated - parents at the table, father lowers his head"),
    ("S15", "court", 1741, 1860, "And four years later - courtroom wide"),
    ("S16", "court", 1861, 1980, "her murder trial began - gallery, side"),
    ("S17", "court", 1981, 2100, "in the middle of this trial the prosecutor - at the lectern, open-hand gesture"),
    ("S18", "court", 2101, 2220, "informed the court - closer, he turns to the judge"),
    ("S19", "court", 2221, 2340, "that after five years - parents turn to each other"),
    ("S20", "home", 2341, 2460, "Natasha had been found alive - night, she walks out to the police car beside an officer"),
    ("S21", "bedroom", 2461, 2580, "She was living - bedroom, she steps out of the open wardrobe"),
    ("S22", "home", 2581, 2700, "just 5 minutes down the road from her family - crane up from one house to the family house"),
    ("S23", "bedroom", 2701, 2820, "the entire time - closer, Natasha by the wardrobe"),
]
SH = {s[0]: s for s in SHOTS}
sc.frame_end = SHOTS[-1][3]
RAISED = []   # (x0, x1, y0, y1, z): raised floors the feet stand on (judge's dais, wardrobe base)
def ground_z(x, y):
    for x0, x1, y0, y1, z in RAISED:
        if x0 <= x <= x1 and y0 <= y <= y1: return z
    return 0.0
X = {"port": 0.0, "school": 100.0, "home": 200.0, "field": 300.0, "kitchen": 400.0, "station": 500.0, "court": 600.0, "bedroom": 700.0}

# ------------------------------------------------------------------ generic helpers
def M(name, rgb, rough=0.5, sheen=0.0, metal=0.0, emit=None, ems=0.0):
    m = bpy.data.materials.get(name)
    if m: return m
    m = bpy.data.materials.new(name); m.use_nodes = True; P = m.node_tree.nodes["Principled BSDF"]
    P.inputs["Base Color"].default_value = (*rgb, 1); P.inputs["Roughness"].default_value = rough
    P.inputs["Metallic"].default_value = metal
    if sheen: P.inputs["Sheen Weight"].default_value = sheen
    if emit: P.inputs["Emission Color"].default_value = (*emit, 1); P.inputs["Emission Strength"].default_value = ems
    return m
def noise_mat(name, c1, c2, scale=4.0, rough=0.6, bump=0.0):
    m = M(name, c1, rough); nt = m.node_tree; P = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord"); nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = scale
    nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
    cr = nt.nodes.new("ShaderNodeValToRGB"); cr.color_ramp.elements[0].color = (*c1, 1); cr.color_ramp.elements[1].color = (*c2, 1)
    nt.links.new(nz.outputs["Fac"], cr.inputs[0]); nt.links.new(cr.outputs[0], P.inputs["Base Color"])
    if bump:
        b = nt.nodes.new("ShaderNodeBump"); b.inputs["Strength"].default_value = bump; nt.links.new(nz.outputs["Fac"], b.inputs["Height"]); nt.links.new(b.outputs[0], P.inputs["Normal"])
    return m
COLL = {}
def coll(name):
    if name not in COLL:
        c = bpy.data.collections.new(name); sc.collection.children.link(c); COLL[name] = c
    return COLL[name]
def link(o, cn):
    for uc in list(o.users_collection): uc.objects.unlink(o)
    coll(cn).objects.link(o); return o
def box(name, dims, loc, mat, cn, bevel=0.01, rotz=0.0):
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts: v.co = Vector((v.co.x * dims[0], v.co.y * dims[1], v.co.z * dims[2]))
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); coll(cn).objects.link(o); o.location = loc; o.rotation_euler = (0, 0, R_(rotz))
    me.materials.append(mat)
    if bevel:
        b = o.modifiers.new("bev", 'BEVEL'); b.width = bevel; b.segments = 2; b.limit_method = 'ANGLE'
    return o
def plane(name, sx, sy, loc, mat, cn, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_plane_add(size=1.0, location=loc, rotation=rot); o = bpy.context.object; o.name = name
    o.scale = (sx, sy, 1); bpy.ops.object.transform_apply(scale=True); o.data.materials.append(mat); return link(o, cn)
GLB = {}
def import_glb(fn, size, axis=2):
    """import a glb once, join, scale so its extent along `axis` = size, origin at bottom centre; returns a hidden source object"""
    key = (fn, size, axis)
    if key in GLB: return GLB[key]
    before = set(bpy.data.objects); bpy.ops.import_scene.gltf(filepath=A + fn)
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
    o = bpy.context.object; o.name = "SRC_" + fn.split(".")[0]
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    pts = [Vector(v.co) for v in o.data.vertices]
    mn = Vector([min(p[i] for p in pts) for i in range(3)]); mx = Vector([max(p[i] for p in pts) for i in range(3)])
    s = size / (mx - mn)[axis]
    c = Vector(((mn.x + mx.x) / 2, (mn.y + mx.y) / 2, mn.z))
    o.data.transform(Matrix.Scale(s, 4) @ Matrix.Translation(-c))
    for p in o.data.polygons: p.use_smooth = True
    o.data.update(); link(o, "Sources"); o.hide_render = True; o.hide_viewport = True
    GLB[key] = o
    print("GLB", fn, "dims", tuple(round(x, 2) for x in o.dimensions))
    return o
def inst(src, name, loc, rotz=0.0, cn="Set", scale=1.0):
    o = src.copy(); o.name = name; coll(cn).objects.link(o); o.hide_render = False; o.hide_viewport = False
    o.location = loc; o.rotation_euler = (0, 0, R_(rotz)); o.scale = (scale,) * 3; return o
def soften(o, sat=1.0, rough_min=0.35):
    for ms in o.material_slots:
        m = ms.material
        if not m or not m.use_nodes: continue
        for n in m.node_tree.nodes:
            if n.type == 'BSDF_PRINCIPLED':
                n.inputs["Roughness"].default_value = max(n.inputs["Roughness"].default_value, rough_min)
            if n.type in ('NORMAL_MAP', 'BUMP'):
                n.inputs["Strength"].default_value = min(n.inputs["Strength"].default_value, 0.35)
def light(name, kind, loc, energy, size=1.0, rot=(0, 0, 0), color=(1, 1, 1), cn="Lights"):
    ld = bpy.data.lights.new(name, kind); ld.energy = energy; ld.color = color
    if kind == 'AREA': ld.size = size
    if kind in ('POINT', 'SPOT'): ld.shadow_soft_size = size
    o = bpy.data.objects.new(name, ld); coll(cn).objects.link(o); o.location = loc; o.rotation_euler = rot; return o

def fcurves_of(idb):
    ad = getattr(idb, "animation_data", None)
    if not ad or not ad.action: return []
    act = ad.action; out_ = []
    try: out_ = list(act.fcurves)
    except Exception: out_ = []
    if not out_:
        for layer in getattr(act, "layers", []):
            for strip in layer.strips:
                for cb in getattr(strip, "channelbags", []): out_ += list(cb.fcurves)
    return out_
def set_interp(idb, kind):
    for fc in fcurves_of(idb):
        for kp in fc.keyframe_points: kp.interpolation = kind

def cam_shot(sid, keys, lens=35, target_keys=None):
    c = bpy.data.cameras.new("CAM_" + sid); c.lens = lens; c.clip_start = 0.05; c.clip_end = 900
    c.dof.use_dof = False; c.sensor_width = 36
    o = bpy.data.objects.new("CAM_" + sid, c); coll("Cameras").objects.link(o)
    t = bpy.data.objects.new("TGT_" + sid, None); coll("Cameras").objects.link(t)
    for f, p in keys: o.location = p; o.keyframe_insert("location", frame=f)
    for f, p in target_keys: t.location = p; t.keyframe_insert("location", frame=f)
    for ob in (o, t):
        for fc in fcurves_of(ob):
            for kp in fc.keyframe_points: kp.interpolation = 'BEZIER'; kp.handle_left_type = kp.handle_right_type = 'AUTO_CLAMPED'
    tr = o.constraints.new('TRACK_TO'); tr.target = t; tr.track_axis = 'TRACK_NEGATIVE_Z'; tr.up_axis = 'UP_Y'
    m = sc.timeline_markers.new(sid, frame=SH[sid][2]); m.camera = o
    return o

# ------------------------------------------------------------------ character helpers
def stand(H, f, pos, yaw, flex=2.0, head=(0.0, 0.0), twist=0.0, crouch=0.0, arms=True, fwd=0.0, swing=(0.0, 0.0)):
    p = Vector((pos.x, pos.y, H.root_head.z - crouch))
    H.key_root(f, p, yaw=yaw, flex=flex * 0.4)
    H.key_spine(f, flex=flex, twist=twist, head=head)
    for s in "LR": H.key_foot(s, f, H.foot_xy(s, Vector((pos.x, pos.y, 0)), yaw), yaw)
    if arms: key_hang(H, f, p, yaw, swingL=swing[0], swingR=swing[1], fwd=fwd)
    return p
def idle(H, f0, f1, pos, yaw, heads=None, every=45, flex=2.0, arms=True):
    """standing idle with breathing and head moves; heads = list of (frame, (pitch, yaw))"""
    hk = sorted(heads or [(f0, (0, 0))])
    def head_at(f):
        prev = hk[0]
        for k in hk:
            if k[0] <= f: prev = k
        return prev[1]
    f = f0; i = 0
    while f <= f1:
        stand(H, f, pos, yaw, flex=flex + (0.8 if i % 2 else 0.0), head=head_at(f), arms=arms)
        f += every; i += 1
    for fk, hd in hk:
        if f0 <= fk <= f1: stand(H, fk, pos, yaw, flex=flex, head=hd, arms=arms)
def sit(H, f, pos, seat_z, yaw, flex=4.0, head=(0.0, 0.0), twist=0.0, hands="lap", table_z=None, foot_fwd=0.46, hip_up=0.18, knees=1.15):
    Rm = Rz(yaw)
    p = Vector((pos.x, pos.y, seat_z + hip_up))
    H.key_root(f, p, yaw=yaw, flex=0.0)
    H.key_spine(f, flex=flex, twist=twist, head=head)
    for s in "LR":
        xy = Vector((pos.x, pos.y)) + (Rm @ Vector((H.ankle[s].x * knees, -foot_fwd, 0))).to_2d()
        H.key_foot(s, f, xy, yaw)
    for s in "LR":
        sx = 1 if s == "L" else -1
        if hands == "lap":
            body_hand(H, s, f, p, yaw, (sx * 0.12, -0.24, 0.10), (-sx * 0.25, -1.0, -0.35), (0, 0, -1), pole_off=(0.45 * sx, 0.3, 0.2))
        elif hands == "table":
            body_hand(H, s, f, p, yaw, (sx * 0.17, -0.40, table_z - p.z + 0.05), (-sx * 0.35, -1.0, 0.0), (0, 0, -1), pole_off=(0.5 * sx, 0.25, 0.0))
            apply_pose(H.rig, s, "flat_palm", f)
    return p
def squat(H, f, pos, yaw, depth=0.42, flex=22.0, head=(0.0, 0.0), twist=0.0, feet_wide=1.25):
    """deep crouch (from B06): feet planted, knees forward (IK), torso leaning, hands resting on the knees"""
    Rm = Rz(yaw)
    p = Vector((pos.x, pos.y, H.root_head.z * (1 - depth))) + Rm @ Vector((0, 0.10, 0))
    H.key_root(f, p, yaw=yaw, flex=flex * 0.5)
    H.key_spine(f, flex=flex, twist=twist, head=head)
    for s in "LR":
        sx = 1 if s == "L" else -1
        xy = Vector((pos.x, pos.y)) + (Rm @ Vector((H.ankle[s].x * feet_wide, 0.02, 0))).to_2d()
        H.key_foot(s, f, xy, yaw + sx * 12)
    for s in "LR":
        sx = 1 if s == "L" else -1
        kn = Vector((H.ankle[s].x * 1.3, -0.30, H.root_head.z * 0.53 - (H.root_head.z * (1 - depth))))
        body_hand(H, s, f, p, yaw, (kn.x, kn.y, kn.z + 0.05), (0, -1.0, -0.6), (-sx * 0.3, 0, -1.0), pole_off=(0.5 * sx, 0.2, 0.0))
    return p
def walk(H, path, yaw_fn, f0, f1, stride=1.25, amp=0.09):
    walk_with_arms(H, path, yaw_fn, f0, f1, stride=stride, amp=amp)
def lin_path(a, b, f0, f1):
    a = Vector(a); b = Vector(b)
    def p(f):
        u = (f - f0) / max(1, (f1 - f0)); return a.lerp(b, max(0.0, min(1.0, u)))
    return p
def ease_path(a, b, f0, f1, ease_in=True, ease_out=True):
    a = Vector(a); b = Vector(b)
    def p(f):
        u = max(0.0, min(1.0, (f - f0) / max(1, (f1 - f0))))
        if ease_in and ease_out: u = smooth(u)
        elif ease_in: u = 0.5 * (u * u + u)          # soft start, continuous, no jump
        return a.lerp(b, u)
    return p
def heading(a, b):
    d = Vector(b) - Vector(a); return math.degrees(math.atan2(d.x, -d.y))

RELAX = {"Dad", "CopA", "CopB", "Killer", "Pros", "Nat18B", "CopFB", "Nat18", "CopF"}
def key_hang(H, f, pos, yaw, swingL=0.0, swingR=0.0, fwd=0.0):
    """relaxed hanging arms; for RELAX characters the elbows bend (wrist 10 cm up, 8 cm forward, slightly out)"""
    for s_, sw in (("L", swingL), ("R", swingR)):
        sx_ = 1 if s_ == "L" else -1
        off = hang_off(H, s_, fwd, sw)
        if H.rig.name in RELAX: off = (off[0] + 0.035 * sx_, off[1] - 0.08, off[2] + 0.10)
        body_hand(H, s_, f, pos, yaw, off, (0.0, -0.35, -1.0), (-sx_, 0.0, 0.0))
RIGS = {}
def char(src, name):
    r = dup_char(bpy.data.objects[src], name) if name != src else bpy.data.objects[src]
    r.location = (0, 0, 0)
    RIGS[name] = r
    return r
base = ["Nat", "Mom", "Dad", "SearchA", "SearchB", "Killer", "CopA", "CopB", "CopF", "Pros", "JudgeB", "ExA", "ExB", "ExD", "ExE"]
for n in base: RIGS[n] = bpy.data.objects[n]
for n in ("ExC",):
    o = bpy.data.objects.get(n)
    if o:
        for c in list(o.children): bpy.data.objects.remove(c)
        bpy.data.objects.remove(o)
# Natasha at 18 (found): same body, black top / dark trousers -> own clothing materials
char("Nat", "NatS"); char("Nat", "Nat18")
s18 = bpy.data.objects["Nat18.female_elegantsuit01"]; s18.data = s18.data.copy()
knit = noise_mat("Nat18_Sweater", (0.42, 0.07, 0.11), (0.55, 0.12, 0.16), 60.0, 0.75, bump=0.25)
knit.node_tree.nodes["Principled BSDF"].inputs["Sheen Weight"].default_value = 0.5
denim = noise_mat("Nat18_Denim", (0.1, 0.17, 0.33), (0.16, 0.24, 0.42), 80.0, 0.7)
s18.data.materials[0] = denim; s18.data.materials[1] = knit   # slot 0 = lower (skirt), slot 1 = top
u18 = bpy.data.objects.get("Nat18.undershirt")
if u18: u18.data = u18.data.copy(); u18.data.materials.clear(); u18.data.materials.append(knit)
char("Nat18", "Nat18B")
char("Mom", "MomH"); char("Mom", "MomK"); char("Mom", "MomC")
char("Dad", "DadC")
char("CopF", "CopFB")
char("ExA", "MournA"); char("ExD", "MournB")
HS = {}
for n, r in RIGS.items():
    r.location = (0, 0, 0)
for n, r in RIGS.items():
    HS[n] = setup_char(r)
    for s in "LR": apply_pose(r, s, "relaxed", 1)
print("RIGS", sorted(RIGS))

VISSET = set()
VISR = {}; HIDDENSET = set()
def vis_char(rig, ranges):
    VISSET.add(rig.name); VISR[rig.name] = list(ranges)
    HIDDENSET.update(c.name for c in rig.children if c.hide_render)
    names = [c.name for c in rig.children if not c.hide_render]
    props = [o for o in bpy.data.objects if any(c.type == 'CHILD_OF' and c.target == rig for c in o.constraints)]
    for o in props: names += [o.name] + [c.name for c in o.children if not c.hide_render]
    key_vis(names, ranges)

# ================================================================== look / world
sc.render.engine = 'CYCLES'; sc.cycles.samples = 48; sc.cycles.adaptive_threshold = 0.05; sc.cycles.use_denoising = True
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1080, 1920, 100
sc.view_settings.view_transform = 'AgX'
try: sc.view_settings.look = 'AgX - Punchy'
except Exception as e: print("look", e)
sc.render.use_motion_blur = False
W = bpy.data.worlds.new("World"); sc.world = W; W.use_nodes = True
bg = W.node_tree.nodes["Background"]
# camera sees a sky gradient; lighting uses the flat colour
nt = W.node_tree; lp = nt.nodes.new("ShaderNodeLightPath"); mixw = nt.nodes.new("ShaderNodeMixShader")
sky = nt.nodes.new("ShaderNodeBackground"); tc = nt.nodes.new("ShaderNodeTexCoord"); sep = nt.nodes.new("ShaderNodeSeparateXYZ")
nt.links.new(tc.outputs["Generated"], sep.inputs[0])
ramp = nt.nodes.new("ShaderNodeValToRGB"); nt.links.new(sep.outputs[2], ramp.inputs[0])
ramp.color_ramp.elements[0].position = 0.0; ramp.color_ramp.elements[0].color = (0.82, 0.93, 1.0, 1)
ramp.color_ramp.elements[1].position = 0.45; ramp.color_ramp.elements[1].color = (0.2, 0.62, 0.97, 1)
skyc = nt.nodes.new("ShaderNodeMix"); skyc.data_type = 'RGBA'; skyc.blend_type = 'MULTIPLY'; skyc.inputs['Factor'].default_value = 1.0
nt.links.new(ramp.outputs[0], skyc.inputs['A']); skyc.inputs['B'].default_value = (1, 1, 1, 1); skyc.name = "SkyTint"
nt.links.new(skyc.outputs['Result'], sky.inputs["Color"]); sky.inputs["Strength"].default_value = 1.0; sky.name = "SkyBG"
wo = nt.nodes["World Output"]
nt.links.new(bg.outputs[0], mixw.inputs[1]); nt.links.new(sky.outputs[0], mixw.inputs[2]); nt.links.new(lp.outputs["Is Camera Ray"], mixw.inputs[0])
nt.links.new(mixw.outputs[0], wo.inputs["Surface"])
sun = light("Sun", 'SUN', (0, 0, 50), 3.5, rot=(R_(45), 0, R_(35)), cn="Lights"); sun.data.angle = R_(3)

grass_m = noise_mat("Grass", (0.16, 0.42, 0.09), (0.28, 0.55, 0.12), 2.0, 0.8)
asph_m = noise_mat("Asphalt", (0.2, 0.2, 0.22), (0.27, 0.27, 0.29), 20, 0.7)
pave_m = noise_mat("Pavement", (0.55, 0.55, 0.53), (0.65, 0.64, 0.6), 6, 0.6)
white_line = M("RoadLine", (0.9, 0.9, 0.85), 0.5)
wood_m = noise_mat("WoodDark", (0.25, 0.12, 0.05), (0.33, 0.17, 0.07), 8, 0.45)
wood_l = noise_mat("WoodLight", (0.55, 0.36, 0.2), (0.62, 0.42, 0.24), 8, 0.45)

# ================================================================== PORTRAIT set (school photo)
XP = X["port"]
bm = bmesh.new()
for i in range(25):
    pass
bpy.ops.mesh.primitive_plane_add(size=1.0); bd = bpy.context.object; bd.name = "Port_Backdrop"
bd.scale = (6, 6, 1); bpy.ops.object.transform_apply(scale=True)
sd = bd.modifiers.new("sub", 'SUBSURF'); sd.levels = 0
bd.location = (XP, 0.0, 0.0)
# sweep: subdivide and bend the back half up
me = bd.data; bm = bmesh.new(); bm.from_mesh(me)
bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=30, use_grid_fill=True)
for v in bm.verts:
    y = v.co.y
    if y > 0.5:
        a = min((y - 0.5) / 1.6, 1.0) * math.pi / 2
        r = 1.6 * 2 / math.pi
        if y - 0.5 <= 1.6 * 1.0:
            v.co.y = 0.5 + r * math.sin(a); v.co.z = r * (1 - math.cos(a))
        if y - 0.5 > 1.6:
            v.co.y = 0.5 + r; v.co.z = r + (y - 0.5 - 1.6) * 1.5
bm.to_mesh(me); bm.free()
for p in me.polygons: p.use_smooth = True
bdm = noise_mat("PhotoBackdrop", (0.22, 0.5, 0.7), (0.55, 0.8, 0.9), 2.2, 0.8)
me.materials.append(bdm); link(bd, "Port")
stool_seat = 0.47
st = box("Port_StoolSeat", (0.26, 0.26, 0.05), (XP, 0.0, stool_seat - 0.025), M("StoolTop", (0.12, 0.12, 0.14), 0.5), "Port", bevel=0.02)
for i, (dx, dy) in enumerate(((-0.1, -0.1), (0.1, -0.1), (-0.1, 0.1), (0.1, 0.1))):
    box("Port_StoolLeg%d" % i, (0.035, 0.035, stool_seat - 0.05), (XP + dx, dy, (stool_seat - 0.05) / 2), M("Chrome", (0.75, 0.75, 0.78), 0.25, metal=1.0), "Port", bevel=0.005)
light("Port_Key", 'AREA', (XP - 1.6, -2.2, 2.2), 260, size=1.6, rot=(R_(60), 0, R_(-35)), cn="Port")
light("Port_Fill", 'AREA', (XP + 1.8, -2.0, 1.6), 90, size=1.6, rot=(R_(65), 0, R_(40)), cn="Port")
light("Port_Rim", 'AREA', (XP + 0.6, 1.4, 2.4), 60, size=0.8, rot=(R_(-40), 0, R_(160)), cn="Port")
# softbox stands (real studio kit, keeps the frame alive)
for nm, x_, y_ in (("Port_SBoxL", XP - 2.1, -1.0), ("Port_SBoxR", XP + 2.2, -1.2)):
    box(nm + "_pole", (0.03, 0.03, 1.9), (x_, y_, 0.95), M("Chrome", (0.75, 0.75, 0.78), 0.25, metal=1.0), "Port", bevel=0.0)
    box(nm, (0.75, 0.25, 0.75), (x_, y_, 1.95), M("SoftboxWhite", (0.95, 0.95, 0.95), 0.6, emit=(1, 1, 1), ems=1.5), "Port", bevel=0.03, rotz=-30 if x_ < XP else 30)

H = HS["Nat"]; pos = Vector((XP, 0.0)); yaw = 0.0
for f, fl, hd in ((1, 9, (12, -14)), (50, 6, (6, -6)), (86, 3, (2, 0)), (110, 4, (2, -12)), (152, 2, (-5, 5)), (200, 3, (-3, 2)), (330, 3, (-3, 2))):
    sit(H, f, pos, stool_seat, yaw, flex=fl, head=hd, hands="lap", foot_fwd=0.40, knees=0.55, hip_up=0.22)
vis_char(RIGS["Nat"], [(1, 330)])
# visible studio kit for S01: light stand + softbox behind right, backdrop roll stands, stool footring
for nm, x_, y_, rz in (("Port_StandA", XP + 0.62, 0.55, 35),):
    box(nm + "_pole", (0.03, 0.03, 1.75), (x_, y_, 0.875), M("StandBlack", (0.03, 0.03, 0.035), 0.35, metal=0.6), "Port", bevel=0.0)
    for k, a_ in enumerate((0, 120, 240)):
        lg = box(nm + "_leg%d" % k, (0.02, 0.45, 0.02), (x_ + 0.18 * math.sin(R_(a_)), y_ + 0.18 * math.cos(R_(a_)), 0.08), M("StandBlack", (0.03, 0.03, 0.035), 0.35, metal=0.6), "Port", bevel=0.0)
        lg.rotation_euler = (R_(-18), 0, R_(-a_))
    sb = box(nm + "_box", (0.55, 0.35, 0.55), (x_, y_, 1.85), M("SoftboxBlack", (0.04, 0.04, 0.05), 0.5), "Port", bevel=0.03); sb.rotation_euler = (R_(10), 0, R_(rz))
    fr = box(nm + "_diff", (0.5, 0.02, 0.5), (0, 0, 0), M("SoftboxWhite", (0.95, 0.95, 0.95), 0.6, emit=(1, 1, 1), ems=1.5), "Port", bevel=0.0)
    fr.parent = sb; fr.location = (0, -0.18, 0)
box("Port_StoolRing", (0.3, 0.3, 0.02), (XP, 0.0, 0.22), M("Chrome", (0.75, 0.75, 0.78), 0.25, metal=1.0), "Port", bevel=0.01)
cam_shot("S01", [(1, (XP + 0.35, -2.45, 0.95)), (86, (XP + 0.22, -2.15, 0.98))], lens=35,
         target_keys=[(1, (XP + 0.1, 0.1, 0.9)), (86, (XP + 0.08, 0.1, 0.94))])
cam_shot("S02", [(87, (XP - 0.45, -1.2, 1.24)), (152, (XP - 0.15, -1.0, 1.21))], lens=60,
         target_keys=[(87, (XP, 0.0, 1.17)), (152, (XP, 0.0, 1.18))])

# ================================================================== SCHOOL set (drop-off + memorial)
XS = X["school"]
plane("School_Lawn", 92, 120, (XS, 40, -0.01), grass_m, "School")
plane("School_Road", 92, 7, (XS, -0.5, 0.0), asph_m, "School")
for i in range(9):
    plane("School_Line%d" % i, 2.5, 0.12, (XS - 40 + i * 10, -0.5, 0.004), white_line, "School")
plane("School_Pavement", 92, 3.0, (XS, 4.5, 0.06), pave_m, "School")
box("School_Kerb", (92, 0.2, 0.14), (XS, 3.0, 0.05), M("Kerb", (0.7, 0.7, 0.68), 0.6), "School", bevel=0.01)
plane("School_Path", 3.0, 14, (XS, 13, 0.065), pave_m, "School")
schsrc = import_glb("school.glb", 40.0, axis=0)
school = inst(schsrc, "School_Building", (XS, 33, 0.0), 0.0, "School"); soften(school)
bpy.context.view_layer.update(); print("SCHOOL bbox y", round(min((school.matrix_world @ Vector(c)).y for c in school.bound_box), 2), "dims", tuple(round(x, 2) for x in school.dimensions))
treesrc = import_glb("tree.glb", 8.0, axis=2)
for i, (tx, ty) in enumerate(((-9, 12), (9, 13), (-16, 10), (16, 11), (-24, 14), (24, 13), (-6, -12), (8, -14), (-30, 22), (31, 24))):
    inst(treesrc, "School_Tree%d" % i, (XS + tx, ty, 0), random.uniform(0, 360), "School", scale=random.uniform(0.85, 1.15))
# railing fence along the pavement (gap for the path)
rail = M("FenceGreen", (0.1, 0.22, 0.14), 0.45, metal=0.6)
for i in range(-30, 31):
    x_ = XS + i * 0.6
    if abs(x_ - XS) < 2.0: continue
    box("School_FencePost%d" % (i + 40), (0.04, 0.04, 1.2), (x_, 6.1, 0.66), rail, "School", bevel=0.0)
for xa, xb in ((XS - 18, XS - 2.0), (XS + 2.0, XS + 18)):
    for z_ in (0.25, 1.15):
        box("School_FenceRail_%d_%d" % (int(xa), int(z_ * 100)), (xb - xa, 0.05, 0.05), ((xa + xb) / 2, 6.1, z_ + 0.06), rail, "School", bevel=0.0)
sedan_src = import_glb("sedan.glb", 4.6, axis=1)
sedan_src.data.transform(Matrix.Diagonal((1.0, 1.0, 0.72, 1.0)))   # the low-poly model is toy-tall; real sedan ~1.48 m
car = inst(sedan_src, "Mom_Car", (XS + 2.5, 1.9, 0.0), 90.0, "School"); soften(car)
van_src = import_glb("van.glb", 5.2, axis=0)
van = inst(van_src, "Delivery_Van", (XS - 4.6, 1.9, 0.0), 0.0, "School"); soften(van)
for ms in van.material_slots:
    pass
print("VAN dims", tuple(round(x, 2) for x in van.dimensions), "CAR dims", tuple(round(x, 2) for x in car.dimensions))
# DA KRAS FILMS logo decal (white version: the van model is black) on the road-facing side (-Y), below the windows
logo_img = bpy.data.images.load("/home/user/Muhammed/blender/assets/brand/DaKrasFilms_logo_white.png"); logo_img.pack()
lm = bpy.data.materials.new("LogoDecal"); lm.use_nodes = True; lnt = lm.node_tree; LP = lnt.nodes["Principled BSDF"]
ti = lnt.nodes.new("ShaderNodeTexImage"); ti.image = logo_img; ti.extension = 'CLIP'
lnt.links.new(ti.outputs["Color"], LP.inputs["Base Color"]); lnt.links.new(ti.outputs["Alpha"], LP.inputs["Alpha"]); LP.inputs["Roughness"].default_value = 0.4
bpy.context.view_layer.update()
vbb = [van.matrix_world @ Vector(c) for c in van.bound_box]
vminy = min(p.y for p in vbb); vz0 = min(p.z for p in vbb); vz1 = max(p.z for p in vbb)
logo = plane("Van_Logo", 2.2, 2.2 * 414 / 967, (van.location.x + 0.2, vminy - 0.03, vz0 + (vz1 - vz0) * 0.42), lm, "School", rot=(R_(90), 0, 0))
logo.rotation_euler = (0, 0, 0)   # plane() leaves the mesh already upright
bpy.context.view_layer.update(); logo.parent = van; logo.matrix_parent_inverse = van.matrix_world.inverted()
key_vis(["Delivery_Van", "Van_Logo"], [(241, 450)])   # the van is only there on the drop-off morning

# Natasha walks from the car to the school; mother stands by the car and waves
H = HS["NatS"]; a = (XS + 1.4, 3.9, 0); b = (XS + 0.2, 14.0, 0)
pth = ease_path(a, b, 240, 620, ease_in=False, ease_out=False)
yw = heading((XS + 1.4, 3.9), (XS + 0.2, 14.0)) + 180.0 - 180.0
walk(H, pth, lambda f: heading(a, b), 236, 620, stride=1.2)
vis_char(RIGS["NatS"], [(241, 540)])
# backpack on Natasha (navy, our own model), Child Of spine03
def backpack(rig, name):
    bm = bmesh.new()
    def rbox(d, l):
        r = bmesh.ops.create_cube(bm, size=1.0)
        for v in r['verts']: v.co = Vector((v.co.x * d[0], v.co.y * d[1], v.co.z * d[2])) + Vector(l)
    rbox((0.30, 0.13, 0.38), (0, 0, 0.19)); rbox((0.25, 0.05, 0.16), (0, 0.08, 0.11))
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); coll("Props").objects.link(o)
    me.materials.append(M("BagMaroon", (0.45, 0.06, 0.1), 0.55, sheen=0.4))
    bv = o.modifiers.new("r", 'BEVEL'); bv.width = 0.045; bv.segments = 4; bv.limit_method = 'ANGLE'
    ss = o.modifiers.new("s", 'SUBSURF'); ss.levels = 1; ss.render_levels = 1
    for p in me.polygons: p.use_smooth = True
    sc.frame_set(260); bpy.context.view_layer.update()
    s3 = rig.matrix_world @ rig.pose.bones["spine03"].head; s5 = rig.matrix_world @ rig.pose.bones["spine05"].head
    yaw_ = math.degrees(Matrix(rig.pose.bones["spine03"].matrix.to_3x3()).to_euler().z)
    hdg = heading(a, b)
    back = Rz(hdg) @ Vector((0, 1, 0))
    o.rotation_euler = (0, 0, R_(hdg)); o.location = s3.lerp(s5, 0.3) + back * 0.18 + Vector((0, 0, -0.09))
    bpy.context.view_layer.update(); attach(o, rig, "spine03")
    return o
bag = backpack(RIGS["NatS"], "Nat_Backpack")
H = HS["Mom"]; mp = Vector((XS + 3.9, 3.85)); myaw = heading(mp, (XS + 0.8, 10))
idle(H, 236, 640, mp, myaw, heads=[(236, (2, 0)), (330, (0, -4)), (450, (-2, 4)), (560, (0, 0))])
for f, amt in ((372, 0.0), (392, 1.0), (404, 0.85), (416, 1.0), (428, 0.85), (440, 1.0), (462, 0.0)):
    p = Vector((mp.x, mp.y, H.root_head.z))
    sh = H.sh["R"] - H.root_head
    hang = hang_off(H, "R")
    up = (sh.x - 0.12 - 0.04 * (amt % 1 if amt < 1 else 0), sh.y - 0.22, sh.z + 0.12)
    off = tuple(hang[i] + (up[i] - hang[i]) * (1.0 if amt > 0.5 else amt) for i in range(3))
    off = (off[0] + (0.05 if amt == 0.85 else 0.0), off[1], off[2])
    if amt == 0.0:
        body_hand(H, "R", f, p, myaw, hang, (0.0, -0.15, -1.0), (1, 0, 0))
    else:
        body_hand(H, "R", f, p, myaw, off, (0.0, -0.1, 1.0), (0, -1, 0), pole_off=(-0.45, 0.35, 0.0))
apply_pose(RIGS["Mom"], "R", "relaxed", 372); apply_pose(RIGS["Mom"], "R", "flat_palm", 392); apply_pose(RIGS["Mom"], "R", "flat_palm", 440); apply_pose(RIGS["Mom"], "R", "relaxed", 462)
vis_char(RIGS["Mom"], [(241, 540)])
cam_shot("S03", [(295, (XS - 6.4, -3.5, 1.3)), (360, (XS - 5.6, -4.4, 2.6))], lens=26,
         target_keys=[(295, (XS - 2.4, 4.0, 1.2)), (360, (XS - 1.0, 6.5, 1.6))])
cam_shot("S04", [(361, (XS - 1.6, 9.8, 1.55)), (450, (XS - 1.75, 10.3, 1.6))], lens=30,
         target_keys=[(361, (XS + 2.6, 4.2, 1.15)), (450, (XS + 2.3, 4.6, 1.15))])
cam_shot("S05", [(451, (XS - 0.7, 15.2, 1.45)), (540, (XS - 1.0, 15.0, 2.0))], lens=40,
         target_keys=[(451, (XS + 0.6, 10.0, 1.15)), (540, (XS + 0.4, 11.5, 1.1))])

# memorial at the school fence (left of the gate): table, framed photo, candles, flowers, two mourners
tbl_src = import_glb("desk.glb", 0.78, axis=2)
mem_t = inst(tbl_src, "Mem_Table", (XS - 4.5, 5.35, 0.06), 0.0, "School", scale=1.0); soften(mem_t)
mem_t.scale = (0.75, 0.75, 1.0)
bpy.context.view_layer.update()
TZ = max((mem_t.matrix_world @ Vector(c)).z for c in mem_t.bound_box)
# framed school photo (our own render of the generic girl), standing on the table, leaning back 10 deg
pf = box("Mem_Frame", (0.36, 0.03, 0.46), (XS - 4.5, 5.5, TZ + 0.235), wood_m, "School", bevel=0.008); pf.rotation_euler = (R_(-10), 0, 0)
photo_m = bpy.data.materials.new("PortraitPhoto"); photo_m.use_nodes = True
if os.path.exists(HERE + "portrait.png"):
    pi_ = photo_m.node_tree.nodes.new("ShaderNodeTexImage"); pi_.image = bpy.data.images.load(HERE + "portrait.png"); pi_.image.pack()
    photo_m.node_tree.links.new(pi_.outputs["Color"], photo_m.node_tree.nodes["Principled BSDF"].inputs["Base Color"])
    pi_.image.name = "NatPortraitPhoto"
else:
    photo_m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.4, 0.6, 0.75, 1)
photo_m.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.35
bpy.context.view_layer.update()
ph = plane("Mem_Photo", 0.29, 0.39, (0, 0, 0), photo_m, "School", rot=(R_(90), 0, 0))
ph.parent = pf; ph.location = (0, -0.017, 0.0); ph.rotation_euler = (0, 0, 0)   # plane() leaves the mesh already upright
cand_src = import_glb("candles.glb", 0.42, axis=0)
for i, (dx, dy, rz) in enumerate(((-0.42, -0.08, 0), (0.42, -0.05, 40))):
    inst(cand_src, "Mem_Candles%d" % i, (XS - 4.5 + dx, 5.3 + dy, TZ), rz, "School")
flw_src = import_glb("flowers.glb", 0.42, axis=2)
for i, (dx, dy, rz, z_) in enumerate(((-0.8, -0.05, 20, 0.06), (0.9, 0.0, -30, 0.06), (-1.2, -0.25, 70, 0.06), (1.25, -0.2, -60, 0.06))):
    o = inst(flw_src, "Mem_Flowers%d" % i, (XS - 4.5 + dx, 5.4 + dy, z_), rz, "School"); o.rotation_euler = (R_(-75), 0, R_(rz))
    o.location.z = 0.14
for i, (dx, dy) in enumerate(((-0.3, -0.1), (0.25, -0.12), (0.0, -0.18))):
    lc = light("Mem_CandleGlow%d" % i, 'POINT', (XS - 4.5 + dx * 1.4, 5.3 + dy, TZ + 0.3), 4.0, size=0.05, color=(1.0, 0.65, 0.3), cn="School")
for nm, mp_, hds in (("MournA", Vector((XS - 5.45, 4.35)), [(880, (14, 0)), (980, (18, 6)), (1060, (14, -4))]),
                     ("MournB", Vector((XS - 3.55, 4.25)), [(880, (16, 0)), (960, (20, -5)), (1060, (16, 3))])):
    idle(HS[nm], 870, 1100, mp_, heading(mp_, (XS - 4.5, 5.35)), heads=hds)
    vis_char(RIGS[nm], [(901, 1080)])
key_vis([o.name for o in bpy.data.objects if o.name.startswith("Mem_") and o.type in ('MESH', 'LIGHT')], [(901, 1080)])
VISR["__mem__"] = [(901, 1080)]
cam_shot("S09", [(901, (XS - 4.3, -0.2, 1.55)), (1080, (XS - 4.45, 2.6, 1.3))], lens=28,
         target_keys=[(901, (XS - 4.5, 5.4, 0.95)), (1080, (XS - 4.5, 5.45, 0.98))])

# ================================================================== HOME street (dusk S06, night S20, aerial S22)
XH = X["home"]
plane("Home_Lawn", 92, 120, (XH + 4, 40, -0.01), grass_m, "Home")
plane("Home_Road", 92, 7, (XH + 4, -1.0, 0.0), asph_m, "Home")
plane("Home_Pavement", 92, 2.4, (XH + 4, 3.7, 0.06), pave_m, "Home")
box("Home_Kerb", (92, 0.2, 0.14), (XH + 4, 2.5, 0.05), M("Kerb", (0.7, 0.7, 0.68), 0.6), "Home", bevel=0.01)
h2src = import_glb("house2.glb", 8.0, axis=2); h1src = import_glb("house1.glb", 7.0, axis=2)
fam = inst(h2src, "Home_FamilyHouse", (XH, 14.0, 0.0), 0.0, "Home"); soften(fam)
houses = [fam]
for i, (dx, src_) in enumerate(((-16, h1src), (16, h1src), (32, h1src), (-32, h1src))):
    houses.append(inst(src_, "Home_House%d" % i, (XH + dx, 14.0 + (5.57 if src_ is h1src else 0.0), 0.0), 0.0, "Home"))   # fronts in line
for h in houses: soften(h)
bf = houses[3]   # the house where she was found: two doors down (x + 32)
for i, tx in enumerate((-24, -8, 8, 24, 40, -38)):
    inst(treesrc, "Home_Tree%d" % i, (XH + tx, 7.5 + (i % 2) * 1.2, 0), random.uniform(0, 360), "Home", scale=random.uniform(0.8, 1.0))
for i, tx in enumerate(range(-38, 47, 14)):
    box("Home_LampPost%d" % i, (0.12, 0.12, 5.0), (XH + tx, 3.0, 2.5), M("LampGrey", (0.3, 0.32, 0.34), 0.4, metal=0.7), "Home", bevel=0.0)
    box("Home_LampHead%d" % i, (0.5, 0.25, 0.14), (XH + tx, 2.75, 5.0), M("LampGlow", (1, 0.9, 0.7), 0.3, emit=(1.0, 0.85, 0.6), ems=6.0), "Home", bevel=0.02)
    light("Home_Lamp%d" % i, 'POINT', (XH + tx, 2.7, 4.7), 450, size=0.4, color=(1.0, 0.82, 0.55), cn="Home")
bpy.context.view_layer.update()
def front_y(o):
    return min((o.matrix_world @ Vector(c)).y for c in o.bound_box)
FY = front_y(fam); BFY = front_y(bf)
print("HOUSE fronts", round(FY, 2), round(BFY, 2), "fam dims", tuple(round(x, 2) for x in fam.dimensions))
plane("Home_FamPath", 1.6, FY - 4.9, (XH, (FY + 4.9) / 2, 0.065), pave_m, "Home")
plane("Home_BfPath", 1.6, BFY - 4.9, (XH + 32, (BFY + 4.9) / 2, 0.065), pave_m, "Home")
light("Home_PorchLight", 'POINT', (XH, FY - 0.6, 2.6), 120, size=0.2, color=(1.0, 0.8, 0.5), cn="Home")
light("Home_BfPorchLight", 'POINT', (XH + 32, BFY - 0.6, 2.6), 150, size=0.2, color=(1.0, 0.8, 0.5), cn="Home")
# S06: mother walks down the family path at dusk and looks up and down the street
H = HS["MomH"]; a = (XH + 0.1, FY - 1.2, 0); b = (XH + 0.1, 6.0, 0)
walk(H, ease_path(a, b, 520, 590), lambda f: heading(a, b), 520, 590, stride=1.0)
idle(H, 592, 700, Vector((b[0], b[1])), heading(a, b), heads=[(592, (0, 0)), (612, (2, 38)), (640, (2, 38)), (662, (2, -40)), (690, (2, -40))])
vis_char(RIGS["MomH"], [(541, 660)])
cam_shot("S06", [(541, (XH - 2.6, 1.0, 1.5)), (660, (XH - 2.0, 2.3, 1.55))], lens=32,
         target_keys=[(541, (XH + 0.1, 8.0, 1.4)), (660, (XH + 0.1, 6.5, 1.45))])
# S20: night; Natasha (18) walks down the path of the house two doors away beside a female officer, to the police car
pcar = inst(sedan_src, "Police_Car", (XH + 34.5, 1.2, 0.0), 90.0, "Home")
pcar.data = pcar.data.copy() if False else pcar.data
pm_w = M("PoliceWhite", (0.92, 0.92, 0.95), 0.3); pm_b = M("PoliceNavy", (0.04, 0.05, 0.12), 0.3)
pcar_body = pcar
bpy.context.view_layer.update()
pz1 = max((pcar.matrix_world @ Vector(c)).z for c in pcar.bound_box)
lb = box("Police_LightBar", (0.25, 1.2, 0.1), (XH + 34.5, 1.2, pz1 + 0.05), M("BarBase", (0.1, 0.1, 0.1), 0.4), "Home", bevel=0.02)
red = M("BarRed", (1, 0.1, 0.1), 0.3, emit=(1, 0.05, 0.05), ems=0.0); blue = M("BarBlue", (0.1, 0.2, 1), 0.3, emit=(0.1, 0.2, 1), ems=0.0)
lr = box("Police_LightR", (0.22, 0.5, 0.1), (XH + 34.5, 1.2 - 0.3, pz1 + 0.12), red, "Home", bevel=0.02)
lbl = box("Police_LightB", (0.22, 0.5, 0.1), (XH + 34.5, 1.2 + 0.3, pz1 + 0.12), blue, "Home", bevel=0.02)
plR = light("Police_FlashR", 'POINT', (XH + 34.5, 0.9, pz1 + 0.4), 0, size=0.1, color=(1, 0.1, 0.1), cn="Home")
plB = light("Police_FlashB", 'POINT', (XH + 34.5, 1.5, pz1 + 0.4), 0, size=0.1, color=(0.15, 0.25, 1), cn="Home")
er = red.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]; eb = blue.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]
for f in range(2280, 2560, 12):
    on = (f // 12) % 2 == 0
    er.default_value = 25 if on else 2; er.keyframe_insert("default_value", frame=f)
    eb.default_value = 2 if on else 25; eb.keyframe_insert("default_value", frame=f)
    plR.data.energy = 250 if on else 20; plR.data.keyframe_insert("energy", frame=f)
    plB.data.energy = 20 if on else 250; plB.data.keyframe_insert("energy", frame=f)
set_interp(red.node_tree, 'CONSTANT'); set_interp(blue.node_tree, 'CONSTANT'); set_interp(plR.data, 'CONSTANT'); set_interp(plB.data, 'CONSTANT')
for nm, dx in (("Nat18", 0.0), ("CopF", -0.75)):
    H = HS[nm]; a = (XH + 32 + dx, BFY - 1.0, 0); b = (XH + 32 + dx, 3.4, 0)
    walk(H, ease_path(a, b, 2300, 2520, ease_out=False), lambda f, a=a, b=b: heading(a, b), 2300, 2520, stride=1.05, amp=0.07)
    vis_char(RIGS[nm], [(2341, 2460)])
cam_shot("S20", [(2341, (XH + 31.0, 2.2, 1.55)), (2460, (XH + 31.2, 2.5, 1.5))], lens=40,
         target_keys=[(2341, (XH + 31.8, 7.6, 1.35)), (2460, (XH + 31.8, 5.6, 1.35))])
# soft face fill for the night walk (street-lamp coloured, only during S20)
pf_ = light("Police_FaceFill", 'AREA', (XH + 31.2, 3.0, 2.4), 0.0, size=2.5, rot=(R_(70), 0, 0), color=(1.0, 0.9, 0.8), cn="Home")
for f, e in ((2300, 0.0), (2341, 160.0), (2470, 160.0), (2471, 0.0)):
    pf_.data.energy = e; pf_.data.keyframe_insert("energy", frame=f)
set_interp(pf_.data, 'CONSTANT')
cam_shot("S22", [(2581, (XH + 44, -5.0, 2.5)), (2700, (XH + 47, -9.0, 9.0))], lens=28,
         target_keys=[(2581, (XH + 30, 9, 2.5)), (2700, (XH + 14, 9, 2.0))])
for nm in ("MomH",):
    pass

# ================================================================== FIELD (search)
XF = X["field"]
plane("Field_Ground", 92, 160, (XF, 30, 0.0), noise_mat("FieldGround", (0.3, 0.42, 0.12), (0.42, 0.5, 0.18), 1.5, 0.85), "Field")
# tall grass: one mesh of ~22k blades (our own), deterministic
bm = bmesh.new(); rnd = random.Random(11)
for i in range(22000):
    x_ = rnd.uniform(-20, 20); y_ = rnd.uniform(-2, 24); h_ = rnd.uniform(0.45, 0.85); w_ = rnd.uniform(0.012, 0.02)
    a_ = rnd.uniform(0, math.pi); lx, ly = rnd.uniform(-0.12, 0.12), rnd.uniform(-0.12, 0.12)
    cx, cy = math.cos(a_) * w_, math.sin(a_) * w_
    v0 = bm.verts.new((x_ - cx, y_ - cy, 0)); v1 = bm.verts.new((x_ + cx, y_ + cy, 0))
    v2 = bm.verts.new((x_ + cx * 0.5 + lx * 0.6, y_ + cy * 0.5 + ly * 0.6, h_ * 0.6)); v3 = bm.verts.new((x_ - cx * 0.5 + lx * 0.6, y_ - cy * 0.5 + ly * 0.6, h_ * 0.6))
    v4 = bm.verts.new((x_ + lx, y_ + ly, h_))
    bm.faces.new((v0, v1, v2, v3)); bm.faces.new((v3, v2, v4))
gme = bpy.data.meshes.new("Field_Grass"); bm.to_mesh(gme); bm.free()
gr = bpy.data.objects.new("Field_Grass", gme); coll("Field").objects.link(gr); gr.location = (XF, 0, 0)
gme.materials.append(noise_mat("GrassBladeMat", (0.32, 0.5, 0.1), (0.55, 0.62, 0.18), 3.0, 0.7))
for i, tx in enumerate(range(-40, 41, 7)):
    inst(treesrc, "Field_Tree%d" % i, (XF + tx + random.uniform(-2, 2), 30 + random.uniform(-3, 3), 0), random.uniform(0, 360), "Field", scale=random.uniform(0.9, 1.3))
H = HS["SearchA"]; a = (XF - 3.0, 5.0, 0); b = (XF + 3.2, 5.6, 0)
walk(H, lin_path(a, b, 640, 800), lambda f: heading(a, b), 640, 800, stride=1.1, amp=0.07)
a2 = (XF + 3.2, 5.6, 0); b2 = (XF + 3.6, 9.0, 0)
walk(H, lin_path(a2, b2, 802, 860), lambda f: heading(a2, b2), 802, 860, stride=1.0, amp=0.07)
for f in (862, 880):
    stand(H, f, Vector((b2[0], b2[1])), heading(a2, b2), head=(12, 0))
for f, hd in ((900, (25, -10)), (930, (28, 10)), (960, (25, 0))):
    squat(H, f, Vector((b2[0], b2[1] + 0.15, 0)), heading(a2, b2), depth=0.45, flex=28, head=hd)
H = HS["SearchB"]; a = (XF - 4.0, 9.0, 0); b = (XF + 2.0, 13.0, 0)
walk(H, lin_path(a, b, 640, 960), lambda f: heading(a, b), 640, 960, stride=1.05, amp=0.07)
for nm in ("SearchA", "SearchB"): vis_char(RIGS[nm], [(661, 900)])
cam_shot("S07", [(661, (XF - 2.2, 1.0, 1.25)), (780, (XF + 2.6, 1.3, 1.3))], lens=36,
         target_keys=[(661, (XF - 1.8, 5.2, 1.05)), (780, (XF + 2.6, 5.6, 1.05))])
cam_shot("S08", [(781, (XF + 5.0, 11.8, 1.55)), (900, (XF + 4.9, 11.6, 1.35))], lens=28,
         target_keys=[(781, (XF + 3.4, 7.2, 1.1)), (900, (XF + 3.6, 9.1, 0.75))])

# ================================================================== KITCHEN
XK = X["kitchen"]
wall_m = M("KitchenWall", (0.93, 0.86, 0.68), 0.7); floor_m = noise_mat("KitchenFloor", (0.55, 0.38, 0.22), (0.62, 0.45, 0.27), 3.0, 0.45)
plane("Kit_Floor", 7, 7, (XK, 1.0, 0.0), floor_m, "Kitchen")
box("Kit_WallBack", (7, 0.15, 2.8), (XK, 3.5, 1.4), wall_m, "Kitchen", bevel=0.0)
box("Kit_WallLeft", (0.15, 7, 2.8), (XK - 3.5, 1.0, 1.4), wall_m, "Kitchen", bevel=0.0)
box("Kit_WallRight", (0.15, 7, 2.8), (XK + 3.5, 1.0, 1.4), wall_m, "Kitchen", bevel=0.0)
# window in the back wall (bright garden beyond)
box("Kit_WindowGlow", (1.6, 0.05, 1.1), (XK + 1.4, 3.42, 1.55), M("WindowGarden", (0.6, 0.85, 0.6), 0.5, emit=(0.75, 0.9, 1.0), ems=2.5), "Kitchen", bevel=0.0)
for nm, d, l in (("Kit_WinFrameT", (1.75, 0.1, 0.08), (XK + 1.4, 3.38, 2.12)), ("Kit_WinFrameB", (1.75, 0.18, 0.08), (XK + 1.4, 3.36, 0.98)),
                 ("Kit_WinFrameL", (0.08, 0.1, 1.2), (XK + 0.56, 3.38, 1.55)), ("Kit_WinFrameR", (0.08, 0.1, 1.2), (XK + 2.24, 3.38, 1.55)), ("Kit_WinFrameM", (0.05, 0.1, 1.1), (XK + 1.4, 3.38, 1.55))):
    box(nm, d, l, M("WhiteFrame", (0.95, 0.95, 0.93), 0.4), "Kitchen", bevel=0.005)
cab = M("CabinetSage", (0.45, 0.58, 0.48), 0.45); top = M("Worktop", (0.85, 0.83, 0.78), 0.3)
box("Kit_Counter", (3.0, 0.62, 0.88), (XK - 1.6, 3.1, 0.44), cab, "Kitchen", bevel=0.01)
box("Kit_Worktop", (3.05, 0.66, 0.04), (XK - 1.6, 3.08, 0.9), top, "Kitchen", bevel=0.005)
box("Kit_WallCab", (3.0, 0.35, 0.7), (XK - 1.6, 3.25, 1.95), cab, "Kitchen", bevel=0.01)
for i in range(5):
    box("Kit_CabLine%d" % i, (0.01, 0.01, 0.8), (XK - 3.1 + i * 0.6 + 0.3, 2.785, 0.45), M("CabLine", (0.3, 0.38, 0.32), 0.5), "Kitchen", bevel=0.0)
box("Kit_Fridge", (0.75, 0.7, 1.85), (XK - 3.0, 1.9, 0.925), M("FridgeWhite", (0.92, 0.92, 0.94), 0.25), "Kitchen", bevel=0.03)
ktab = box("Kit_Table", (1.4, 0.85, 0.045), (XK, 0.8, 0.7525), wood_l, "Kitchen", bevel=0.01)
for i, (dx, dy) in enumerate(((-0.64, -0.36), (0.64, -0.36), (-0.64, 0.36), (0.64, 0.36))):
    box("Kit_TableLeg%d" % i, (0.06, 0.06, 0.73), (XK + dx, 0.8 + dy, 0.365), wood_m, "Kitchen", bevel=0.005)
for i, (d, l) in enumerate((((1.25, 0.03, 0.08), (XK, 0.8 - 0.37, 0.69)), ((1.25, 0.03, 0.08), (XK, 0.8 + 0.37, 0.69)))):
    box("Kit_TableApron%d" % i, d, l, wood_m, "Kitchen", bevel=0.003)
bpy.context.view_layer.update()
KTZ = max((ktab.matrix_world @ Vector(c)).z for c in ktab.bound_box)
chair_src = import_glb("chair.glb", 1.0, axis=2)
def seat_height(o):
    bpy.context.view_layer.update(); dg = bpy.context.evaluated_depsgraph_get()
    c = o.matrix_world.translation
    hit, loc, n, i, ob, mx = sc.ray_cast(dg, Vector((c.x, c.y, 2.5)), Vector((0, 0, -1)))
    return loc.z if hit else 0.45
kc1 = inst(chair_src, "Kit_ChairMom", (XK, 1.80, 0.0), 180.0, "Kitchen")
kc2 = inst(chair_src, "Kit_ChairDad", (XK + 1.3, 0.75, 0.0), 90.0, "Kitchen")
for o in (kc1, kc2): o.scale = (1.0, 1.0, 0.9)
for o in (kc1, kc2): soften(o)
fruit = None
box("Kit_Mug", (0.08, 0.08, 0.1), (XK + 0.35, 0.65, KTZ + 0.05), M("MugRed", (0.75, 0.15, 0.12), 0.3), "Kitchen", bevel=0.02)
box("Kit_Ceiling", (7.2, 7.2, 0.1), (XK, 1.0, 2.85), M("Ceiling", (0.95, 0.95, 0.93), 0.8), "Kitchen", bevel=0.0)
light("Kit_Area", 'AREA', (XK, -1.0, 2.6), 800, size=3.0, rot=(R_(30), 0, 0), cn="Kitchen")
light("Kit_Win", 'AREA', (XK + 1.4, 3.2, 1.6), 200, size=1.5, rot=(R_(-90), 0, 0), color=(0.85, 0.92, 1.0), cn="Kitchen")
S1 = seat_height(kc1); S2 = seat_height(kc2)
print("KITCHEN table", round(KTZ, 3), "seats", round(S1, 3), round(S2, 3))
H = HS["MomK"]; mpos = Vector((XK, 1.72))
for f, fl, hd in ((1060, 10, (18, 0)), (1120, 12, (22, -5)), (1190, 10, (20, 4)), (1260, 12, (24, 0)), (1300, 12, (24, 0)),
                  (1600, 12, (24, 0)), (1650, 10, (18, 10)), (1700, 12, (22, 14)), (1780, 12, (22, 10))):
    sit(H, f, mpos, S1, 0.0, flex=fl, head=hd, hands="lap", foot_fwd=0.40)
vis_char(RIGS["MomK"], [(1081, 1260), (1621, 1740)])
H = HS["Dad"]; dp = Vector((XK + 1.4, 2.65))
idle(H, 1060, 1125, dp, 180.0, heads=[(1060, (0, 0)), (1100, (-2, 8))])
# he turns from the window to look at her (a 0.6 s turn in place), then stays facing her
idle(H, 1160, 1300, dp, heading(dp, (XK, 1.72)), heads=[(1160, (6, 0)), (1220, (12, 4)), (1280, (14, -2))])
dsp = Vector((XK + 1.35, 0.75))
# S14: the father stands beside her at the table and lowers his head (no seat, no contact)
idle(H, 1600, 1780, Vector((XK + 0.8, 2.05)), heading((XK + 0.8, 2.05), (XK + 0.2, 0.0)), heads=[(1600, (10, -10)), (1660, (24, -14)), (1720, (30, -16)), (1780, (30, -16))])
vis_char(RIGS["Dad"], [(1081, 1260), (1621, 1740)])
cam_shot("S10", [(1081, (XK - 0.95, -2.0, 1.5)), (1260, (XK - 0.35, -0.95, 1.35))], lens=32,
         target_keys=[(1081, (XK + 0.3, 2.0, 1.1)), (1260, (XK + 0.2, 1.8, 1.05))])
cam_shot("S14", [(1621, (XK - 1.3, -1.4, 1.3)), (1740, (XK - 1.0, -1.1, 1.25))], lens=36,
         target_keys=[(1621, (XK + 0.5, 1.3, 0.95)), (1740, (XK + 0.5, 1.25, 0.95))])

# ================================================================== STATION (escort)
XT = X["station"]
plane("Stn_Ground", 92, 80, (XT, 20, -0.01), pave_m, "Station")
plane("Stn_Road", 92, 7, (XT, -3.5, 0.0), asph_m, "Station")
brick = noise_mat("StationBrick", (0.55, 0.3, 0.22), (0.62, 0.36, 0.26), 30, 0.7)
box("Stn_Facade", (24, 0.6, 9), (XT, 14.0, 4.5), brick, "Station", bevel=0.02)
box("Stn_Cornice", (24.4, 0.9, 0.35), (XT, 13.9, 9.0), M("Stone", (0.85, 0.82, 0.75), 0.6), "Station", bevel=0.03)
glass = M("WindowDark", (0.25, 0.35, 0.45), 0.08, metal=0.3)
for i in range(-5, 6):
    for j in (2.5, 6.0):
        if abs(i) < 1 and j < 3: continue
        box("Stn_Win_%d_%d" % (i + 5, int(j)), (1.3, 0.1, 1.7), (XT + i * 2.1, 13.68, j), glass, "Station", bevel=0.0)
        box("Stn_Sill_%d_%d" % (i + 5, int(j)), (1.5, 0.2, 0.1), (XT + i * 2.1, 13.62, j - 0.9), M("Stone", (0.85, 0.82, 0.75), 0.6), "Station", bevel=0.01)
box("Stn_Door", (2.2, 0.15, 2.6), (XT, 13.65, 1.3 + 0.45), M("DoorBlue", (0.08, 0.15, 0.35), 0.4), "Station", bevel=0.02)
for k in range(3):
    box("Stn_Step%d" % k, (5.0, 0.4, 0.15), (XT, 13.3 - k * 0.4, 0.075 + (2 - k) * 0.15), M("Stone", (0.85, 0.82, 0.75), 0.6), "Station", bevel=0.01)
box("Stn_BlueLamp", (0.3, 0.3, 0.45), (XT - 1.6, 13.5, 3.4), M("BlueLamp", (0.2, 0.4, 1.0), 0.3, emit=(0.2, 0.4, 1.0), ems=4.0), "Station", bevel=0.03)
pcar2 = inst(sedan_src, "Stn_PoliceCar", (XT + 4.0, -1.8, 0.0), 90.0, "Station")
for i, tx in enumerate((-10, 10)):
    inst(treesrc, "Stn_Tree%d" % i, (XT + tx, 9.0, 0), random.uniform(0, 360), "Station", scale=0.8)
for nm, dx in (("Killer", 0.0), ("CopA", -0.72), ("CopB", 0.72)):
    H = HS[nm]; a = (XT + dx, 12.2, 0); b = (XT + dx, 1.0, 0)
    walk(H, lin_path(a, b, 1240, 1660), lambda f, a=a, b=b: heading(a, b), 1240, 1660, stride=1.0, amp=0.06 if nm == "Killer" else 0.08)
    vis_char(RIGS[nm], [(1261, 1620)])
# killer: head lowered through the walk (re-key the head on top of the walk's spine keys)
for f in range(1240, 1661, 2):
    for n_, w_ in Human.HEAD_W.items():
        RIGS["Killer"].pose.bones[n_].rotation_quaternion = Quaternion((1, 0, 0), R_(16 * w_ * (1 if True else 0)))
        RIGS["Killer"].pose.bones[n_].keyframe_insert("rotation_quaternion", frame=f)
for nm_, ph_ in (("CopA", 0.0), ("CopB", 1.7)):
    for f in range(1240, 1661, 2):
        yawh = 22.0 * max(0.0, math.sin((f - 1240) / 55.0 + ph_)) * (1 if nm_ == "CopA" else -1)
        for n_, w_ in Human.HEAD_W.items():
            HS[nm_].r.key_rot(n_, f, [("X", 4 * w_), ("Z", yawh * w_)])
def zpos(f): return 12.2 + (1.0 - 12.2) * (f - 1240) / 420.0
cam_shot("S11", [(1261, (XT + 1.6, 4.0, 1.2)), (1380, (XT + 1.4, 3.0, 1.25))], lens=30,
         target_keys=[(1261, (XT, zpos(1261), 1.3)), (1380, (XT, zpos(1380), 1.35))])
cam_shot("S12", [(1381, (XT + 0.35, zpos(1381) - 3.6, 1.6)), (1500, (XT + 0.3, zpos(1500) - 3.0, 1.6))], lens=32,
         target_keys=[(1381, (XT, zpos(1381), 1.55)), (1500, (XT, zpos(1500), 1.55))])
cam_shot("S13", [(1501, (XT + 2.9, zpos(1501) - 2.6, 1.7)), (1620, (XT + 2.6, zpos(1620) - 2.0, 1.7))], lens=34,
         target_keys=[(1501, (XT, zpos(1501), 1.4)), (1620, (XT, zpos(1620), 1.4))])

# ================================================================== COURTROOM
XC = X["court"]
cw = M("CourtWallCream", (0.9, 0.86, 0.76), 0.7); panel = wood_m
plane("Crt_Floor", 16, 18, (XC, 0, 0.0), noise_mat("CourtCarpet", (0.35, 0.12, 0.1), (0.42, 0.16, 0.12), 12, 0.9), "Court")
box("Crt_WallBack", (16, 0.2, 6), (XC, 8.5, 3), cw, "Court", bevel=0.0)
box("Crt_WallFront", (16, 0.2, 6), (XC, -9.0, 3), cw, "Court", bevel=0.0)
box("Crt_WallL", (0.2, 18, 6), (XC - 8, 0, 3), cw, "Court", bevel=0.0)
box("Crt_WallR", (0.2, 18, 6), (XC + 8, 0, 3), cw, "Court", bevel=0.0)
for nm, d, l in (("Crt_PanelB", (15.9, 0.06, 1.2), (XC, 8.38, 0.6)), ("Crt_PanelF", (15.9, 0.06, 1.2), (XC, -8.88, 0.6)),
                 ("Crt_PanelL", (0.06, 17.9, 1.2), (XC - 7.88, 0, 0.6)), ("Crt_PanelR", (0.06, 17.9, 1.2), (XC + 7.88, 0, 0.6))):
    box(nm, d, l, panel, "Court", bevel=0.005)
# tall windows with blinds on the right wall (reference look)
for i, y_ in enumerate((-6, -2, 2, 6)):
    box("Crt_Win%d" % i, (0.05, 1.6, 2.6), (XC + 7.88, y_, 3.0), M("CourtWinGlow", (0.9, 0.95, 1.0), 0.5, emit=(0.95, 0.97, 1.0), ems=2.0), "Court", bevel=0.0)
    for k in range(12):
        box("Crt_Blind%d_%d" % (i, k), (0.04, 1.58, 0.07), (XC + 7.82, y_, 1.8 + k * 0.21), M("Blind", (0.82, 0.78, 0.68), 0.6), "Court", bevel=0.0)
    box("Crt_Drape%d" % i, (0.12, 0.35, 3.0), (XC + 7.8, y_ - 1.0, 3.0), M("Drape", (0.45, 0.12, 0.15), 0.8, sheen=0.5), "Court", bevel=0.03)
# judge's bench (raised dais)
box("Crt_Dais", (6.0, 2.2, 0.45), (XC, 7.0, 0.225), panel, "Court", bevel=0.01)
RAISED.append((XC - 3.0, XC + 3.0, 5.9, 8.1, 0.46))
box("Crt_Bench", (5.0, 0.6, 1.25), (XC, 6.0, 0.45 + 0.625), panel, "Court", bevel=0.02)
box("Crt_BenchTop", (5.2, 0.8, 0.06), (XC, 6.05, 1.72), wood_l, "Court", bevel=0.01)
box("Crt_JudgeChairBack", (0.7, 0.12, 1.3), (XC, 7.55, 0.46 + 0.85), M("LeatherGreen", (0.08, 0.2, 0.12), 0.4), "Court", bevel=0.04)
box("Crt_JudgeChairSeat", (0.6, 0.6, 0.1), (XC, 7.2, 0.46 + 0.37), M("LeatherGreen", (0.08, 0.2, 0.12), 0.4), "Court", bevel=0.03)
box("Crt_Crest", (1.0, 0.05, 1.0), (XC, 8.38, 3.6), M("CrestGold", (0.75, 0.6, 0.25), 0.3, metal=0.8), "Court", bevel=0.05)
# counsel tables + chairs, lectern
ct1 = inst(tbl_src, "Crt_TableL", (XC - 2.4, 3.3, 0.0), 0.0, "Court"); ct2 = inst(tbl_src, "Crt_TableR", (XC + 2.4, 3.3, 0.0), 0.0, "Court")
for o in (ct1, ct2): o.scale = (1.0, 1.0, 0.96); soften(o)
for i, x_ in enumerate((-3.0, -1.8, 1.8, 3.0)):
    soften(inst(chair_src, "Crt_CounselChair%d" % i, (XC + x_, 2.55, 0.0), 0.0, "Court"))
lec = M("LecternWood", (0.36, 0.2, 0.1), 0.45)
box("Crt_LecternBase", (0.6, 0.45, 1.05), (XC - 0.6, 4.55, 0.525), lec, "Court", bevel=0.02)
lt = box("Crt_LecternTop", (0.7, 0.55, 0.05), (XC - 0.6, 4.55, 1.1), wood_l, "Court", bevel=0.01); lt.rotation_euler = (R_(-12), 0, 0)
# gallery: our own wooden benches facing the bench (+Y); backrest on the -Y side
SEATZ = 0.42; ROWS = (-1.2, -2.6, -4.0, -5.4)
for r_, y_ in enumerate(ROWS):
    for side, x_ in (("L", -2.4), ("R", 2.4)):
        nm = "Crt_Bench%s%d" % (side, r_)
        box(nm + "_Seat", (3.0, 0.46, 0.06), (XC + x_, y_, SEATZ - 0.03), wood_l, "Court", bevel=0.01)
        box(nm + "_Back", (3.0, 0.06, 0.55), (XC + x_, y_ - 0.26, SEATZ + 0.3), wood_m, "Court", bevel=0.01)
        box(nm + "_Front", (3.0, 0.04, 0.32), (XC + x_, y_ + 0.18, SEATZ - 0.22), wood_m, "Court", bevel=0.005)
        for ex in (-1.5, 1.5):
            box(nm + "_End%d" % int(ex > 0), (0.06, 0.6, 0.9), (XC + x_ + ex, y_ - 0.03, 0.45), wood_m, "Court", bevel=0.01)
box("Crt_Rail", (14, 0.08, 0.9), (XC, 0.4, 0.45), panel, "Court", bevel=0.01)
# judge seated behind the bench
JS = 0.46 + 0.42
for f, hd in ((1720, (6, 0)), (1860, (8, 5)), (2000, (4, -10)), (2140, (2, -18)), (2260, (6, -6)), (2380, (6, 0))):
    sit(HS["JudgeB"], f, Vector((XC, 7.15)), JS, 0.0, flex=6, head=hd, hands="lap", foot_fwd=0.42)
vis_char(RIGS["JudgeB"], [(1741, 2340)])
# prosecutor at the lectern, facing the judge (+Y)
PP = Vector((XC - 1.25, 4.05)); PY = 180.0
def pros_hang(s_):
    h_ = hang_off(HS["Pros"], s_, fwd=0.07); sx_ = 1 if s_ == "L" else -1
    return (h_[0] + 0.07 * sx_, h_[1] - 0.06, h_[2] + 0.12)   # bent elbows, hands clear of his thighs (clip_scan)
for f, hd in ((1720, (4, 0)), (1765, (4, 4)), (1810, (5, 8)), (1850, (6, 10)), (1895, (4, 4)), (1940, (2, 0)), (1960, (2, 0))):
    p = stand(HS["Pros"], f, PP, PY, head=hd, arms=False)
    for s_ in "LR":
        sx_ = 1 if s_ == "L" else -1
        body_hand(HS["Pros"], s_, f, p, PY, pros_hang(s_), (0.0, -0.15, -1.0), (-sx_, 0, 0))
Hp = HS["Pros"]
for f, hd, g in ((1990, (0, 0), 0.0), (2020, (-2, -8), 1.0), (2080, (-2, 6), 1.0), (2120, (0, -12), 0.6), (2160, (2, -25), 0.0), (2240, (2, -28), 0.0), (2300, (4, -10), 0.0), (2380, (4, 0), 0.0)):
    p = stand(Hp, f, PP, PY, head=hd, arms=False)
    body_hand(Hp, "R", f, p, PY, pros_hang("R"), (0.0, -0.15, -1.0), (1, 0, 0))
    hg = pros_hang("L"); gest = (0.2, -0.36, 0.02)
    body_hand(Hp, "L", f, p, PY, tuple(hg[i] + (gest[i] - hg[i]) * g for i in range(3)), (-0.25 * g, -1.0, -0.3 * (1 - g)), (0, 0, 1) if g > 0.5 else (-1, 0, 0), pole_off=(0.4, 0.35, -0.1))
for f, g in ((2125, 0.0), (2150, 1.0), (2200, 1.0), (2228, 0.0)):
    sc.frame_set(f)
    p = Vector((PP.x, PP.y, Hp.root_head.z))
    hg = pros_hang("R"); gest = (-0.2, -0.38, 0.04)
    body_hand(Hp, "R", f, p, PY, tuple(hg[i] + (gest[i] - hg[i]) * g for i in range(3)), (0.25 * g, -1.0, -0.3 * (1 - g)), (0, 0, 1) if g > 0.5 else (1, 0, 0), pole_off=(-0.4, 0.35, -0.1))
apply_pose(RIGS["Pros"], "R", "relaxed", 2125); apply_pose(RIGS["Pros"], "R", "open_alarm", 2150); apply_pose(RIGS["Pros"], "R", "open_alarm", 2200); apply_pose(RIGS["Pros"], "R", "relaxed", 2228)
apply_pose(RIGS["Pros"], "L", "relaxed", 1990); apply_pose(RIGS["Pros"], "L", "open_alarm", 2020); apply_pose(RIGS["Pros"], "L", "open_alarm", 2080); apply_pose(RIGS["Pros"], "L", "relaxed", 2160)
vis_char(RIGS["Pros"], [(1741, 2340)])
# gallery: parents front row left, extras
GAL = [("MomC", -2.05, ROWS[0], [(1720, (4, 0)), (1900, (6, 4)), (2230, (2, 0)), (2262, (2, -38)), (2380, (2, -40))]),
       ("DadC", -2.75, ROWS[0], [(1720, (6, 0)), (1950, (8, -3)), (2240, (4, 0)), (2272, (2, 40)), (2380, (2, 42))]),
       ("ExB", 2.8, ROWS[1], [(1720, (6, 0)), (1980, (4, -10)), (2240, (2, 18)), (2380, (2, 20))]),
       ]
for nm, gx, gy, hds in GAL:
    for f, hd in hds:
        sit(HS[nm], f, Vector((XC + gx, gy + 0.02)), SEATZ, 180.0, flex=4, head=hd, hands="lap", foot_fwd=0.44, hip_up=0.21 if nm == "ExD" else 0.18)
    vis_char(RIGS[nm], [(1741, 2340)])
idle(HS["ExA"], 1720, 2380, Vector((XC + 6.6, -6.8)), heading((XC + 6.6, -6.8), (XC, 4.0)), heads=[(1720, (4, 0)), (2000, (2, 10)), (2250, (0, -12))])
vis_char(RIGS["ExA"], [(1741, 2340)])
idle(HS["ExD"], 1720, 2380, Vector((XC - 6.6, -6.4)), heading((XC - 6.6, -6.4), (XC, 4.0)), heads=[(1720, (6, 0)), (1880, (4, 12)), (2250, (0, 25))])
vis_char(RIGS["ExD"], [(1741, 2340)])
cam_shot("S15", [(1741, (XC - 1.0, 4.6, 3.0)), (1860, (XC - 1.9, 1.6, 1.9))], lens=28,
         target_keys=[(1741, (XC - 2.2, -1.6, 0.9)), (1860, (XC - 2.4, -1.3, 1.0))])
cam_shot("S16", [(1861, (XC - 6.4, 1.6, 1.7)), (1980, (XC - 5.0, 0.2, 1.45))], lens=30,
         target_keys=[(1861, (XC - 1.0, -2.6, 0.95)), (1980, (XC - 0.8, -2.6, 0.95))])
cam_shot("S17", [(1981, (XC - 3.4, 6.0, 1.6)), (2100, (XC - 3.0, 5.7, 1.6))], lens=32,
         target_keys=[(1981, (XC - 1.25, 3.95, 1.35)), (2100, (XC - 1.25, 3.95, 1.4))])
cam_shot("S18", [(2101, (XC - 2.5, 5.6, 1.7)), (2220, (XC - 2.3, 5.4, 1.7))], lens=45,
         target_keys=[(2101, (XC - 1.25, 4.05, 1.6)), (2220, (XC - 1.25, 4.05, 1.6))])
cam_shot("S19", [(2221, (XC - 2.2, 0.9, 1.25)), (2340, (XC - 2.35, 0.6, 1.2))], lens=34,
         target_keys=[(2221, (XC - 2.4, ROWS[0], 1.1)), (2340, (XC - 2.4, ROWS[0], 1.1))])
box("Crt_Ceiling", (16.4, 18.4, 0.2), (XC, 0, 6.05), M("CourtCeiling", (0.92, 0.9, 0.85), 0.8), "Court", bevel=0.0)
for i in range(3):
    box("Crt_CeilLamp%d" % i, (6.0, 0.4, 0.06), (XC, -5 + i * 5, 5.94), M("CeilLampGlow", (1, 1, 1), 0.5, emit=(1, 0.97, 0.9), ems=4.0), "Court", bevel=0.0)
light("Crt_Fill", 'AREA', (XC, -3.0, 5.6), 2200, size=9.0, rot=(0, 0, 0), cn="Court")
light("Crt_FillFront", 'AREA', (XC, 5.0, 5.6), 900, size=8.0, rot=(0, 0, 0), cn="Court")
light("Crt_WinLight", 'AREA', (XC + 7.4, 0, 3.0), 600, size=6.0, rot=(0, R_(-90), 0), color=(0.9, 0.95, 1.0), cn="Court")
print("COURT set ok")

# ================================================================== BEDROOM (wardrobe)
XB = X["bedroom"]
bw = M("BedroomWall", (0.78, 0.84, 0.9), 0.7)
plane("Bed_Floor", 6, 6, (XB, 0.5, 0.0), noise_mat("BedFloor", (0.6, 0.45, 0.3), (0.66, 0.5, 0.34), 4, 0.45), "Bedroom")
box("Bed_WallBack", (6, 0.15, 2.7), (XB, 3.0, 1.35), bw, "Bedroom", bevel=0.0)
box("Bed_WallL", (0.15, 6, 2.7), (XB - 3.0, 0.5, 1.35), bw, "Bedroom", bevel=0.0)
box("Bed_WallR", (0.15, 6, 2.7), (XB + 3.0, 0.5, 1.35), bw, "Bedroom", bevel=0.0)
plane("Bed_Rug", 2.0, 1.4, (XB - 0.4, 0.9, 0.005), M("RugTeal", (0.15, 0.45, 0.5), 0.9), "Bedroom")
bed_src = import_glb("bed.glb", 2.2, axis=0)
bedo = inst(bed_src, "Bed_Bed", (XB + 1.6, 1.6, 0.0), 0.0, "Bedroom"); soften(bedo)
# wardrobe (our own build): carcass, open doors, rail with hanging clothes, against the back wall at the left
wd = M("WardrobeWhite", (0.9, 0.88, 0.84), 0.45); WX = XB - 1.3; WY = 2.6
box("Ward_Back", (1.2, 0.03, 2.2), (WX, WY + 0.3, 1.1), wd, "Bedroom", bevel=0.0)
box("Ward_SideL", (0.03, 0.62, 2.2), (WX - 0.6, WY, 1.1), wd, "Bedroom", bevel=0.005)
box("Ward_SideR", (0.03, 0.62, 2.2), (WX + 0.6, WY, 1.1), wd, "Bedroom", bevel=0.005)
box("Ward_Top", (1.23, 0.62, 0.04), (WX, WY, 2.2), wd, "Bedroom", bevel=0.005)
box("Ward_Base", (1.23, 0.62, 0.08), (WX, WY, 0.04), wd, "Bedroom", bevel=0.005)
RAISED.append((WX - 0.66, WX + 0.66, WY - 0.36, WY + 0.36, 0.10))
box("Ward_Rail", (1.16, 0.02, 0.02), (WX, WY + 0.05, 1.95), M("Chrome", (0.75, 0.75, 0.78), 0.25, metal=1.0), "Bedroom", bevel=0.0)
for i, x_ in enumerate((-0.48, -0.4, 0.38, 0.47)):
    cl = box("Ward_Coat%d" % i, (0.06, 0.45, 0.85), (WX + x_, WY + 0.05, 1.45), M("Coat%d" % i, [(0.6, 0.1, 0.15), (0.15, 0.25, 0.5), (0.3, 0.3, 0.32), (0.75, 0.6, 0.2)][i], 0.8, sheen=0.4), "Bedroom", bevel=0.02)
for nm, sx in (("Ward_DoorL", -1), ("Ward_DoorR", 1)):
    d = box(nm, (0.6, 0.025, 2.1), (0, 0, 0), wd, "Bedroom", bevel=0.005)
    d.data.transform(Matrix.Translation((sx * 0.3, 0, 0)))
    d.location = (WX + sx * 0.6, WY - 0.31, 1.12); d.rotation_euler = (0, 0, R_(sx * 100))
    hdl = box(nm + "Handle", (0.02, 0.03, 0.25), (0, 0, 0), M("Chrome", (0.75, 0.75, 0.78), 0.25, metal=1.0), "Bedroom", bevel=0.0)
    hdl.parent = d; hdl.location = (sx * 0.55, -0.03, 0.0)
box("Bed_Window", (1.4, 0.05, 1.2), (XB + 1.4, 2.92, 1.6), M("BedWinGlow", (0.85, 0.92, 1.0), 0.5, emit=(0.9, 0.95, 1.0), ems=2.0), "Bedroom", bevel=0.0)
box("Bed_Nightstand", (0.45, 0.4, 0.55), (XB + 0.2, 2.6, 0.275), wood_l, "Bedroom", bevel=0.01)
box("Bed_Lamp", (0.18, 0.18, 0.28), (XB + 0.2, 2.6, 0.7), M("LampShade", (1, 0.9, 0.75), 0.6, emit=(1, 0.85, 0.6), ems=3.0), "Bedroom", bevel=0.05)
box("Bed_Ceiling", (6.2, 6.2, 0.1), (XB, 0.5, 2.75), M("Ceiling", (0.95, 0.95, 0.93), 0.8), "Bedroom", bevel=0.0)
light("Bed_Area", 'AREA', (XB, -1.5, 2.5), 700, size=3.0, rot=(R_(35), 0, 0), cn="Bedroom")
light("Bed_Lamp", 'POINT', (XB + 0.2, 2.4, 1.0), 40, size=0.1, color=(1.0, 0.75, 0.45), cn="Bedroom")
H = HS["Nat18B"]; a = (WX, WY + 0.02, 0); b = (WX + 0.25, WY - 1.25, 0)
for f in (2440, 2470):
    stand(H, f, Vector((a[0], a[1])), heading(a, b), head=(8, 0))
walk(H, ease_path(a, b, 2472, 2560), lambda f: heading(a, b), 2472, 2560, stride=0.85, amp=0.06)
idle(H, 2562, 2706, Vector((b[0], b[1])), heading(a, b), heads=[(2562, (6, 0)), (2620, (8, 20)), (2690, (12, 10))])
CAM23 = Vector((WX + 1.75, WY - 2.9))
c_ = Vector((b[0], b[1])) + (CAM23 - Vector((b[0], b[1]))).normalized() * 0.4
walk(H, ease_path((b[0], b[1], 0), (c_.x, c_.y, 0), 2712, 2752), lambda f: heading((b[0], b[1]), c_), 2712, 2752, stride=0.55, amp=0.04)
idle(H, 2754, 2860, c_, heading(c_, CAM23), heads=[(2754, (8, 0)), (2775, (-3, 0)), (2860, (-4, 2))])
vis_char(RIGS["Nat18B"], [(2461, 2580), (2701, 2820)])
H = HS["CopFB"]; cp = Vector((WX + 1.35, WY - 0.55))
idle(H, 2440, 2860, cp, heading(cp, (WX - 0.2, WY - 0.9)), heads=[(2440, (4, 0)), (2560, (6, -8)), (2700, (6, 0))])
vis_char(RIGS["CopFB"], [(2461, 2580), (2701, 2820)])
cam_shot("S21", [(2461, (XB + 1.5, -2.3, 1.55)), (2580, (XB + 1.0, -1.8, 1.5))], lens=28,
         target_keys=[(2461, (WX + 0.4, WY - 0.5, 1.15)), (2580, (WX + 0.4, WY - 0.8, 1.2))])
cam_shot("S23", [(2701, (WX + 1.75, WY - 2.9, 1.5)), (2790, (WX + 1.45, WY - 2.6, 1.48))], lens=45,
         target_keys=[(2701, (b[0], b[1], 1.42)), (2760, (c_.x, c_.y, 1.45)), (2790, (c_.x, c_.y, 1.45))])

# ================================================================== per-shot sun / world (constant keys at the cuts)
LOOK = {  # sun energy, sun colour, world light colour, world strength, sky tint
    "port": (1.0, (1, 1, 1), (0.6, 0.7, 0.8), 0.4, (1, 1, 1)),
    "school": (4.0, (1, 0.97, 0.92), (0.55, 0.7, 0.95), 1.0, (1, 1, 1)),
    "field": (4.0, (1, 0.97, 0.92), (0.55, 0.7, 0.95), 1.0, (1, 1, 1)),
    "kitchen": (2.0, (1, 0.97, 0.92), (0.6, 0.7, 0.85), 0.6, (1, 1, 1)),
    "station": (4.0, (1, 0.97, 0.92), (0.55, 0.7, 0.95), 1.0, (1, 1, 1)),
    "court": (0.0, (1, 1, 1), (0.6, 0.6, 0.6), 0.5, (1, 1, 1)),
    "bedroom": (1.5, (1, 0.97, 0.92), (0.6, 0.7, 0.85), 0.6, (1, 1, 1)),
}
SPECIAL = {"S06": (1.6, (1.0, 0.6, 0.35), (0.45, 0.4, 0.6), 0.6, (1.0, 0.7, 0.6)),
           "S20": (0.0, (1, 1, 1), (0.2, 0.26, 0.45), 0.9, (0.16, 0.2, 0.42)),
           "S22": (4.0, (1, 0.97, 0.92), (0.55, 0.7, 0.95), 1.0, (1, 1, 1))}
skyt = nt.nodes["SkyTint"].inputs['B']
for sid, setn, f0, f1, note in SHOTS:
    se, scol, wcol, wst, tint = SPECIAL.get(sid, LOOK.get(setn, LOOK["school"]))
    sun.data.energy = se; sun.data.keyframe_insert("energy", frame=f0)
    sun.data.color = scol; sun.data.keyframe_insert("color", frame=f0)
    bg.inputs["Color"].default_value = (*wcol, 1); bg.inputs["Color"].keyframe_insert("default_value", frame=f0)
    bg.inputs["Strength"].default_value = wst; bg.inputs["Strength"].keyframe_insert("default_value", frame=f0)
    skyt.default_value = (*tint, 1); skyt.keyframe_insert("default_value", frame=f0)
# memorial: afternoon -> late golden light across S09 (days into months)
for f, e, c in ((901, 4.0, (1, 0.97, 0.92)), (1080, 2.0, (1.0, 0.7, 0.45))):
    sun.data.energy = e; sun.data.keyframe_insert("energy", frame=f); sun.data.color = c; sun.data.keyframe_insert("color", frame=f)
set_interp(sun.data, 'CONSTANT'); set_interp(W.node_tree, 'CONSTANT')
for fc in fcurves_of(sun.data):
    for kp in fc.keyframe_points:
        if 901 <= kp.co.x < 1080: kp.interpolation = 'LINEAR'
gm = bpy.data.materials.get("Translucent_Glass_Safety")
if gm:
    gP = next(n for n in gm.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    gP.inputs["Emission Color"].default_value = (1.0, 0.72, 0.38, 1)
    gE = gP.inputs["Emission Strength"]
    for f, on in ((1, 0), (541, 1), (661, 0), (2341, 1), (2461, 0)):
        gE.default_value = 4.0 if on else 0.0; gE.keyframe_insert("default_value", frame=f)
    set_interp(gm.node_tree, 'CONSTANT')
# camera-only catchlights: a tiny specular-only light riding with every camera
for c in [o for o in bpy.data.objects if o.name.startswith("CAM_")]:
    cl = light("Catch_" + c.name[4:], 'POINT', (0, 0, 0), 2.5, size=0.03, cn="Cameras")
    cl.data.diffuse_factor = 0.0; cl.data.volume_factor = 0.0; cl.data.specular_factor = 1.0
    cl.parent = c; cl.location = (0.0, 0.06, 0.0)
# per-set lights only where they belong (porch / street lights only at dusk and night)
for o in bpy.data.objects:
    if o.name.startswith(("Home_Lamp", "Home_PorchLight", "Home_BfPorchLight")) and o.type == 'LIGHT':
        en = o.data.energy
        for f, on in ((1, 0), (541, 1), (661, 0), (2341, 1), (2461, 0)):
            o.data.energy = en if on else 0.0; o.data.keyframe_insert("energy", frame=f)
        set_interp(o.data, 'CONSTANT')
for n, r in RIGS.items():
    if n not in VISSET: vis_char(r, [])
VISR["__van__"] = [(241, 450)]
json.dump(VISR, open(HERE + "work/visr.json", "w")); json.dump(sorted(HIDDENSET), open(HERE + "work/hidden.json", "w"))
json.dump([{"shot": s[0], "set": s[1], "f0": s[2], "f1": s[3], "note": s[4]} for s in SHOTS], open(HERE + "shots_provisional.json", "w"), indent=1)
bpy.ops.wm.save_as_mainfile(filepath=out, compress=True)
print("BUILD_DONE")
