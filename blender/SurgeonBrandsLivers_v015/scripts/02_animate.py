"""SurgeonBrandsLivers v015 stage B: staging, acting, the branded liver, the one continuous camera.
blender -b base.blend --python 02_animate.py -- <out.blend> [stop_after_section]
Timing is built on the client's VO (v011/v014 voiceover, 26.3 s) from the start; see beats.json.
VO phrases (s): 0.0-4.2 burn initials | 4.8-9.2 stitched her up, acted like nothing happened | 9.7-10.6 a week later |
10.7-12.6 liver started to fail | 13.1-17.1 back into surgery, a different doctor | 17.4-19.3 found the initials inside |
19.8-23.8 admitted it wasn't the first time | 24.0-26.1 lost his medical license. Film frames 1-1644."""
import bpy, bmesh, sys, os, math, random
from mathutils import Vector, Matrix, Quaternion, Euler
from mathutils.bvhtree import BVHTree
HERE = os.path.dirname(os.path.abspath(__file__))
PIPE = os.path.abspath(os.path.join(HERE, "..", "..", "pipeline"))
exec(open(os.path.join(HERE, "lib.py")).read())
exec(open(PIPE + "/anim_lib.py").read())
exec(open(PIPE + "/hand_poses.py").read())
args = sys.argv[sys.argv.index("--") + 1:]
OUT = args[0]; STOP = args[1] if len(args) > 1 else ""
random.seed(11)
END = 1644
O = bpy.data.objects
LOG = []
def log(*a):
    s = " ".join(str(x) for x in a); LOG.append(s); print("LOG", s)
for o in O:
    for m in getattr(o, "modifiers", []):
        if m.type == 'SUBSURF': m.show_viewport = False

def upd(): bpy.context.view_layer.update()
def fs(f): sc.frame_set(int(f))
def W(rig, bone): return rig.matrix_world @ rig.pose.bones[bone].matrix
def Wh(rig, bone): return rig.matrix_world @ rig.pose.bones[bone].head
def Wt(rig, bone): return rig.matrix_world @ rig.pose.bones[bone].tail
def frame_from(y_dir, z_hint, origin):
    y = Vector(y_dir).normalized(); z = Vector(z_hint); z = (z - y * z.dot(y)).normalized(); x = y.cross(z)
    M = Matrix((x, y, z)).transposed().to_4x4(); M.translation = Vector(origin); return M
def sect(key, v):
    """sector-local point -> world"""
    th = {"OR1": 0.0, "HOME": -90.0, "OR2": 180.0, "HEAR": 90.0}[key]
    return Matrix.Rotation(R_(th), 4, 'Z') @ Vector(v)
def sectM(key):
    th = {"OR1": 0.0, "HOME": -90.0, "OR2": 180.0, "HEAR": 90.0}[key]
    return Matrix.Rotation(R_(th), 4, 'Z')
def const_interp(obj):
    ad = obj.animation_data
    if ad and ad.action:
        for fc in iter_fcurves(ad.action):
            for kp in fc.keyframe_points: kp.interpolation = 'CONSTANT'
def key_obj_matrix(o, f, M):
    o.matrix_world = M
    o.keyframe_insert("location", frame=f); o.keyframe_insert("rotation_euler", frame=f)

PAT, DOC, DOC2, JUD = O["Patient"], O["Surgeon"], O["Surgeon2"], O["Judge"]
PB, DB, DB2, JB = (part(r, ".body") for r in (PAT, DOC, DOC2, JUD))
TABLE_TOP = sc["TABLE_TOP"]; TABLE_C = Vector(sc["TABLE_C"])
STAGE = O["PATIENT_STAGE"]; LIV = O["Liver"]

# ================================================================== the schedule (VO frames)
F_S1_OUT = 610      # surgeon 1 leaves OR1 for the hearing room (camera is in HOME then)
F_PAT_HOME = 596    # patient appears standing at home (camera whipping OR1 -> HOME)
F_PAT_OR2 = 846     # patient lying in OR2 (camera whipping HOME -> OR2)
F_STAGE_OR2 = 846

# ================================================================== rigs
RIG = {}
for r in (PAT, DOC, DOC2, JUD):
    RIG[r.name] = make_human_ctrl(r); add_hand_limits(r)
    for pb in r.pose.bones: pb.rotation_mode = 'QUATERNION'
# the tool hands get the wrist solved by key_tool (no clamp fighting it), like EarInArm
for r in (DOC, DOC2, JUD):
    for s_ in "LR":
        for c in list(r.pose.bones["wrist." + s_].constraints):
            if c.name == "HandLimit": r.pose.bones["wrist." + s_].constraints.remove(c)
HU = {n: Human(RIG[n]) for n in RIG}
# open the elbow IK limit a little so arms can relax (LESSONS 8: rest elbow ~46 deg)
for r in (PAT, DOC, DOC2, JUD):
    for s_ in "LR":
        lo = r.pose.bones["lowerarm01." + s_]; lo.use_ik_limit_x = True; lo.ik_min_x = R_(-30); lo.ik_max_x = R_(145)

def key_pole(rig, side, f, target_arm_space):
    R = RIG[rig.name]; n = "Pole_elbow." + side; pb = R.PB[n]
    pb.location = R.rest(n).to_3x3().inverted() @ (Vector(target_arm_space) - R.BN[n].head_local)
    pb.keyframe_insert("location", frame=f, group=n)

def hand_world(rig, s, f, W_wrist, fdir, palm, pole=None):
    """key IK_hand.s with the wrist at W_wrist (world), fingers along fdir, palm facing palm (world)"""
    Mi = rig.matrix_world.inverted(); R3 = Mi.to_3x3()
    HU[rig.name].key_hand(s, f, Mi @ Vector(W_wrist), R3 @ Vector(fdir), R3 @ Vector(palm), pole=None if pole is None else Mi @ Vector(pole))

# ================================================================== PATIENT: lying on the table (OR1 world = OR1 local)
fs(1)
RLY = Matrix(((0, 0, 1), (-1, 0, 0), (0, -1, 0)))   # rest (x,y,z) -> (z,-x,-y): head to +x, face up, her right side to +y
bv = PB.data.vertices
torso_back = max(v.co.y for v in bv if 0.75 < v.co.z < 1.30)
head_back = max(v.co.y for v in bv if v.co.z > 1.40 and abs(v.co.x) < 0.06)
sp3 = PAT.data.bones["spine03"].head_local
LIE_T = Vector((TABLE_C.x + 0.12 - sp3.z, TABLE_C.y, TABLE_TOP + 0.004 + torso_back))
M_LIE_OR1 = Matrix.Translation(LIE_T) @ RLY.to_4x4()
log("lying: torso_back", round(torso_back, 3), "head_back", round(head_back, 3), "T", tuple(round(x, 3) for x in LIE_T))
PILLOW_TOP = LIE_T.z - head_back - 0.010
pil = box("Table_Pillow", (0.30, 0.42, max(0.03, PILLOW_TOP - TABLE_TOP) + 0.02), (0, 0, 0), fabric("M_Pillow", (0.92, 0.95, 0.98), scale=300, bump=0.4), bevel=0.03, segs=4)
pil.location = (LIE_T.x + 1.42 - 0.02, TABLE_C.y, TABLE_TOP + (PILLOW_TOP - TABLE_TOP) / 2 - 0.01 + 0.01); pil.parent = STAGE
log("pillow thickness", round(PILLOW_TOP - TABLE_TOP, 3))

M_HOME = sectM("HOME") @ Matrix.Translation(Vector((0.0, 4.55, 0))) @ Matrix.Rotation(R_(0), 4, 'Z')  # stands near the back wall, facing the hub
M_LIE_OR2 = sectM("OR2") @ M_LIE_OR1
key_obj_matrix(PAT, 1, M_LIE_OR1); key_obj_matrix(PAT, F_PAT_HOME, M_HOME); key_obj_matrix(PAT, F_PAT_OR2, M_LIE_OR2)
const_interp(PAT)
STAGE.rotation_euler = (0, 0, 0); STAGE.keyframe_insert("rotation_euler", frame=1)
STAGE.rotation_euler = (0, 0, math.pi); STAGE.keyframe_insert("rotation_euler", frame=F_STAGE_OR2)
const_interp(STAGE)
fs(1)

HP = HU["Patient"]; PR = RIG["Patient"]
def pat_lying_pose(f):
    HP.key_root(f, PR.BN["root"].head_local.copy())
    HP.key_spine(f, 0, 0, 0, head=(-4.0, 6.0))
    for s in "LR":
        sx = 1 if s == "L" else -1
        a = PR.BN["foot." + s].head_local
        PR.key_world("IK_foot." + s, f, Matrix.Translation(Vector((sx * 0.02, 0.0, 0.0))) @ Matrix.Translation(a) @ Matrix.Rotation(R_(-35), 4, 'X') @ Matrix.Translation(-a) @ PR.rest("IK_foot." + s))
        hip = PR.BN["pelvis." + s].head_local
        wr = Vector((sx * 0.20, 0.035, hip.z - 0.13))
        HP.key_hand(s, f, wr, Vector((0, 0.15, -1)), Vector((-sx, 0, 0)), pole=Vector((sx * 0.5, 0.4, 1.05)))
pat_lying_pose(1); pat_lying_pose(F_PAT_HOME - 1); pat_lying_pose(F_PAT_OR2); pat_lying_pose(END)
fs(1)
# PATIENT gown in theatre, home clothes at home
key_vis([O["PatHome.top"], O["PatHome.trousers"]], 1, False); key_vis([O["PatHome.top"], O["PatHome.trousers"]], F_PAT_HOME, True)
key_vis([O["PatHome.top"], O["PatHome.trousers"]], F_PAT_OR2, False)
key_vis([O["PatGown.top"]], 1, True); key_vis([O["PatGown.top"]], F_PAT_HOME, False); key_vis([O["PatGown.top"]], F_PAT_OR2, True)
gown = O["PatGown.top"]; gvg = gown.vertex_groups.new(name="gown_low")
lowz = PAT.data.bones["neck01"].head_local.z - 0.13
gvg.add([i for i, v in enumerate(gown.data.vertices) if v.co.z < lowz], 1.0, 'REPLACE')
gm_ = gown.modifiers.new("gown_low", 'MASK'); gm_.vertex_group = "gown_low"; gm_.invert_vertex_group = True
gown.modifiers.move(gown.modifiers.find("gown_low"), 1)
shoes_p = part(PAT, "shoes01")
key_vis([shoes_p], 1, False); key_vis([shoes_p], F_PAT_HOME, True); key_vis([shoes_p], F_PAT_OR2, False)

# ================================================================== the open abdomen: drape, wound patch, cavity, liver, the letters
fs(1)
_masks = [m for m in PB.modifiers if m.type == 'MASK']
for m in _masks: m.show_viewport = False
upd()
dg = bpy.context.evaluated_depsgraph_get()
pe = PB.evaluated_get(dg); pme = pe.to_mesh()
PW = [PB.matrix_world @ v.co for v in pme.vertices]
pfaces = [tuple(p.vertices) for p in pme.polygons]
pe.to_mesh_clear()
for m in _masks: m.show_viewport = True
assert len(PW) == len(PB.data.vertices), "evaluated body must keep the vertex order"
upd()
BVH_P = BVHTree.FromPolygons(PW, pfaces)
def surf_z(x, y, z0=2.0):
    loc, nrm, _, d = BVH_P.ray_cast(Vector((x, y, z0)), Vector((0, 0, -1)))
    return (loc.z, nrm) if loc is not None else (None, None)
# liver work point: right upper abdomen (her right is +y), below the ribs
s3 = PAT.matrix_world @ PR.PB["spine04"].head.lerp(PR.PB["spine05"].head, 0.4)
WX = s3.x; WY = TABLE_C.y + 0.055
wz, wn = surf_z(WX, WY)
WORK = Vector((WX, WY, wz))
log("work point", tuple(round(x, 3) for x in WORK), "spine03", tuple(round(x, 3) for x in s3))

# --- drape: a projected sheet over her body and the table, hanging at the table edges, with a window at the work point
WIN_HX, WIN_HY = 0.15, 0.11
def drape():
    nx, ny = 200, 110
    x0, x1 = TABLE_C.x - 1.0 - 0.05, s3.x + 0.17
    y0, y1 = TABLE_C.y - 0.42, TABLE_C.y + 0.42
    tz = TABLE_TOP
    bm = bmesh.new(); grid = {}
    for i in range(nx + 1):
        for j in range(ny + 1):
            x = x0 + (x1 - x0) * i / nx; y = y0 + (y1 - y0) * j / ny
            ex = min(0.0, x - (TABLE_C.x - 1.0)); ey = 0.0
            yy = y
            if y < TABLE_C.y - 0.26: ey = (TABLE_C.y - 0.26) - y; yy = TABLE_C.y - 0.26 - 0.03 - ey * 0.25
            if y > TABLE_C.y + 0.26: ey = y - (TABLE_C.y + 0.26); yy = TABLE_C.y + 0.26 + 0.03 + ey * 0.25
            xx = x if x >= TABLE_C.x - 1.0 else TABLE_C.x - 1.0 - 0.03 + ex * 0.25
            z, n_ = surf_z(min(max(xx, TABLE_C.x - 1.0), 9), min(max(yy, TABLE_C.y - 0.26), TABLE_C.y + 0.26))
            top = max(tz + 0.012, (z + 0.034) if z is not None else tz + 0.012)
            zz = top - min(0.30, ey * 1.0 + (-ex) * 1.0)
            jit = 0.004 * math.sin(x * 37 + y * 11) + 0.003 * math.sin(y * 53 - x * 7)
            grid[i, j] = bm.verts.new((xx + (0.01 * ey if False else 0), yy, zz + jit))
    for i in range(nx):
        for j in range(ny):
            cx = x0 + (x1 - x0) * (i + 0.5) / nx; cy = y0 + (y1 - y0) * (j + 0.5) / ny
            dx = (cx - WORK.x) / WIN_HX; dy = (cy - WORK.y) / WIN_HY
            if abs(dx) ** 4 + abs(dy) ** 4 < 1.0: continue
            bm.faces.new((grid[i, j], grid[i + 1, j], grid[i + 1, j + 1], grid[i, j + 1]))
    loose = [v for v in bm.verts if not v.link_faces]; bmesh.ops.delete(bm, geom=loose, context='VERTS')
    for v in bm.verts:
        if v.is_boundary and abs(v.co.x - WORK.x) < WIN_HX * 1.3 and abs(v.co.y - WORK.y) < WIN_HY * 1.3:
            dx = (v.co.x - WORK.x) / WIN_HX; dy = (v.co.y - WORK.y) / WIN_HY
            r = (abs(dx) ** 4 + abs(dy) ** 4) ** 0.25
            if r > 1e-6:
                v.co.x = WORK.x + dx / r * WIN_HX; v.co.y = WORK.y + dy / r * WIN_HY
                z_, _ = surf_z(v.co.x, v.co.y); v.co.z = (z_ + 0.034) if z_ is not None else v.co.z
    me = bpy.data.meshes.new("Drape"); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new("Drape", me); sc.collection.objects.link(o)
    for p in me.polygons: p.use_smooth = True
    me.materials.append(fabric("M_Drape", (0.05, 0.30, 0.72), scale=400, bump=0.4))
    so = o.modifiers.new("solid", 'SOLIDIFY'); so.thickness = 0.004
    sm = o.modifiers.new("smooth", 'CORRECTIVE_SMOOTH'); sm.iterations = 4
    sd = o.modifiers.new("subd", 'SUBSURF'); sd.levels = 0; sd.render_levels = 1
    o.parent = STAGE
    return o
DRAPE = drape()

# --- skin patch around the window with the incision opening (shape key "closed"), cavity wall, cavity floor
skin_m = mat("M_SkinPatch", (0.86, 0.60, 0.48), rough=0.45, sss=0.15)
tissue_m = mat("M_Tissue", (0.55, 0.06, 0.07), rough=0.25, coat=0.4)
deep_m = mat("M_TissueDeep", (0.30, 0.03, 0.04), rough=0.3, coat=0.3)
INC_HX, INC_HY = 0.105, 0.062
def patch():
    nx, ny = 96, 72
    bm = bmesh.new(); vs = {}
    for i in range(nx + 1):
        for j in range(ny + 1):
            u = -1 + 2 * i / nx; v = -1 + 2 * j / ny
            x = WORK.x + u * (WIN_HX + 0.02); y = WORK.y + v * (WIN_HY + 0.02)
            z, _ = surf_z(x, y)
            vs[i, j] = bm.verts.new((x, y, (z if z is not None else WORK.z) + 0.003))
    for i in range(nx):
        for j in range(ny):
            cx = (vs[i, j].co.x + vs[i + 1, j + 1].co.x) / 2 - WORK.x; cy = (vs[i, j].co.y + vs[i + 1, j + 1].co.y) / 2 - WORK.y
            if (cx / INC_HX) ** 2 + (cy / INC_HY) ** 2 < 1.0: continue
            bm.faces.new((vs[i, j], vs[i + 1, j], vs[i + 1, j + 1], vs[i, j + 1]))
    loose = [v for v in bm.verts if not v.link_faces]; bmesh.ops.delete(bm, geom=loose, context='VERTS')
    for v in bm.verts:
        dx = (v.co.x - WORK.x) / INC_HX; dy = (v.co.y - WORK.y) / INC_HY; r = math.sqrt(dx * dx + dy * dy)
        if v.is_boundary and r < 1.6 and r > 1e-6:
            v.co.x = WORK.x + dx / r * INC_HX; v.co.y = WORK.y + dy / r * INC_HY
            z_, _ = surf_z(v.co.x, v.co.y); v.co.z = (z_ if z_ is not None else WORK.z) + 0.003
    me = bpy.data.meshes.new("SkinPatch"); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new("SkinPatch", me); sc.collection.objects.link(o); me.materials.append(skin_m)
    for p in me.polygons: p.use_smooth = True
    # shape key: the opening closes to a line along x
    o.shape_key_add(name="Basis"); kc = o.shape_key_add(name="closed")
    for i, v in enumerate(me.vertices):
        d = v.co - WORK; ex = d.x / INC_HX; ey = d.y / INC_HY; r = math.sqrt(ex * ex + ey * ey)
        if r < 2.4 and abs(ex) < 1.25:
            # pull toward the incision line, strongest at the rim, fading out by r=2.4
            w = max(0.0, min(1.0, (2.4 - r) / 1.4))
            target_y = WORK.y + math.copysign(0.0012, d.y)
            kc.data[i].co = Vector((v.co.x, v.co.y + (target_y - v.co.y) * w * (1.0 - 0.15 * (r - 1)), v.co.z + 0.002 * w))
    kc.value = 0.0
    o.parent = STAGE
    sd = o.modifiers.new("subd", 'SUBSURF'); sd.levels = 0; sd.render_levels = 1
    return o
SKIN = patch()
def cavity():
    """wall from the incision rim down 4.5 cm (shrinks with the closing key) + a deep floor; red, glossy, no gore"""
    n = 64; bm = bmesh.new(); top = []; bot = []
    for k in range(n):
        a_ = 2 * math.pi * k / n
        x = WORK.x + INC_HX * math.cos(a_); y = WORK.y + INC_HY * math.sin(a_)
        z, _ = surf_z(x, y)
        top.append(bm.verts.new((x, y, (z or WORK.z) + 0.002)))
        bot.append(bm.verts.new((WORK.x + INC_HX * 1.15 * math.cos(a_), WORK.y + INC_HY * 1.3 * math.sin(a_), WORK.z - 0.055)))
    for k in range(n):
        bm.faces.new((top[k], top[(k + 1) % n], bot[(k + 1) % n], bot[k]))
    c = bm.verts.new((WORK.x, WORK.y, WORK.z - 0.06));
    for k in range(n): bm.faces.new((bot[k], bot[(k + 1) % n], c))
    me = bpy.data.meshes.new("Cavity"); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new("Cavity", me); sc.collection.objects.link(o); me.materials.append(tissue_m); me.materials.append(deep_m)
    for p in me.polygons:
        p.use_smooth = True
        if len(p.vertices) == 3: p.material_index = 1
    o.shape_key_add(name="Basis"); kc = o.shape_key_add(name="closed")
    for i, v in enumerate(me.vertices):
        kc.data[i].co = Vector((v.co.x, WORK.y + (v.co.y - WORK.y) * 0.02, v.co.z))
    kc.value = 0.0
    o.parent = STAGE
    return o
CAV = cavity()
# hide her own abdominal skin under the window (the patch replaces it)
mvg = PB.vertex_groups.new(name="window_hole")
ids = [i for i, p in enumerate(PW) if abs(p.x - WORK.x) < WIN_HX + 0.035 and abs(p.y - WORK.y) < WIN_HY + 0.035 and p.z > WORK.z - 0.08]
mvg.add(ids, 1.0, 'REPLACE')
mk = PB.modifiers.new("window_hole", 'MASK'); mk.vertex_group = "window_hole"; mk.invert_vertex_group = True
mk.show_viewport = True
# the hole only exists in theatre: keyed off at home
mk.keyframe_insert("show_render", frame=1); mk.keyframe_insert("show_viewport", frame=1)
mk.show_render = mk.show_viewport = False; mk.keyframe_insert("show_render", frame=F_PAT_HOME); mk.keyframe_insert("show_viewport", frame=F_PAT_HOME)
mk.show_render = mk.show_viewport = True; mk.keyframe_insert("show_render", frame=F_PAT_OR2); mk.keyframe_insert("show_viewport", frame=F_PAT_OR2)

# --- the liver: broad face up, long axis along x, top 2.6 cm below the skin; glossy healthy red-brown, later failing
lv_m = mat("M_LiverFresh", (0.48, 0.08, 0.06), rough=0.22, coat=0.6, sss=0.08)
nt = lv_m.node_tree; pbsdf = nt.nodes["Principled BSDF"]
nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 40.0
cr = nt.nodes.new("ShaderNodeValToRGB"); cr.color_ramp.elements[0].color = (0.40, 0.05, 0.05, 1); cr.color_ramp.elements[1].color = (0.60, 0.12, 0.08, 1)
nt.links.new(nz.outputs["Fac"], cr.inputs["Fac"])
# failing: grey-purple mottling keyed in for the second surgery
nz2 = nt.nodes.new("ShaderNodeTexNoise"); nz2.inputs["Scale"].default_value = 9.0; nz2.inputs["Detail"].default_value = 6.0
cr2 = nt.nodes.new("ShaderNodeValToRGB"); cr2.color_ramp.elements[0].position = 0.45; cr2.color_ramp.elements[1].position = 0.62
nt.links.new(nz2.outputs["Fac"], cr2.inputs["Fac"])
mxf = nt.nodes.new("ShaderNodeMath"); mxf.operation = 'MULTIPLY'; mxf.name = "FailAmt"; mxf.inputs[1].default_value = 0.0
nt.links.new(cr2.outputs["Color"], mxf.inputs[0])
mix = nt.nodes.new("ShaderNodeMix"); mix.data_type = 'RGBA'; mix.inputs["B"].default_value = (0.30, 0.18, 0.22, 1)
nt.links.new(mxf.outputs[0], mix.inputs["Factor"]); nt.links.new(cr.outputs["Color"], mix.inputs["A"]); nt.links.new(mix.outputs["Result"], pbsdf.inputs["Base Color"])
mxf.inputs[1].keyframe_insert("default_value", frame=1)
mxf.inputs[1].default_value = 0.85; mxf.inputs[1].keyframe_insert("default_value", frame=F_PAT_OR2)
LIV.animation_data_clear(); LIV.location = (0, 0, 0); LIV.data.materials.clear(); LIV.data.materials.append(lv_m)
for p in LIV.data.polygons: p.use_smooth = True
LIV.rotation_euler = (R_(-90), 0, 0); upd()
LIV.scale = (0.85, 0.85, 0.85); upd()
bbw = [LIV.matrix_world @ Vector(c) for c in LIV.bound_box]
top_now = max(v.z for v in bbw)
LIV.location = Vector((WORK.x - 0.01, WORK.y, 0)) + Vector((0, 0, WORK.z - 0.026 - top_now))
upd(); LIV.parent = STAGE
LIV_BVH = None
def liver_bvh():
    dg = bpy.context.evaluated_depsgraph_get(); le = LIV.evaluated_get(dg); me = le.to_mesh()
    vs = [LIV.matrix_world @ v.co for v in me.vertices]; fs_ = [tuple(p.vertices) for p in me.polygons]; le.to_mesh_clear()
    return BVHTree.FromPolygons(vs, fs_)
fs(1); upd(); LIV_BVH = liver_bvh()
def liver_surf(x, y):
    loc, nrm, _, _ = LIV_BVH.ray_cast(Vector((x, y, WORK.z + 0.2)), Vector((0, 0, -1)))
    return loc, nrm
c_loc, _ = liver_surf(WORK.x, WORK.y)
log("liver top at work point", None if c_loc is None else round(c_loc.z, 3), "skin", round(WORK.z, 3))

# --- the letters "SB": strokes in a 2D frame on the liver (readable from the camera on her left side: x right, y up)
LH = 0.034; LW = 0.024; GAP = 0.010
def S_path():
    pts = []
    for k in range(37):
        t = k / 36.0
        # an S: top arc (right->left), diagonal, bottom arc (right->left mirrored)
        if t < 0.5:
            a_ = math.pi * 0.15 + (t / 0.5) * math.pi * 1.35
            pts.append((0.5 * LW * math.cos(a_), 0.25 * LH + 0.25 * LH * math.sin(a_)))
        else:
            a_ = math.pi * 0.5 - ((t - 0.5) / 0.5) * math.pi * 1.35
            pts.append((0.5 * LW * math.cos(a_), -0.25 * LH + 0.25 * LH * math.sin(a_)))
    return pts
def B_path():
    pts = [(-0.5 * LW, -0.5 * LH + LH * k / 8.0) for k in range(9)]
    for k in range(1, 17):
        a_ = math.pi * 0.5 - math.pi * k / 16.0
        pts.append((-0.5 * LW + 0.85 * LW * math.cos(a_), 0.25 * LH + 0.25 * LH * math.sin(a_)))
    for k in range(1, 17):
        a_ = math.pi * 0.5 - math.pi * k / 16.0
        pts.append((-0.5 * LW + 1.0 * LW * math.cos(a_), -0.25 * LH + 0.25 * LH * math.sin(a_)))
    return pts
best_ = None
for gx_ in range(-8, 9):
    for gy_ in range(-6, 7):
        l_, _ = liver_surf(WORK.x + gx_ * 0.005, WORK.y + gy_ * 0.005)
        if l_ is not None and (best_ is None or l_.z > best_.z): best_ = l_
LET_C = Vector((best_.x, best_.y)) if best_ is not None else Vector((WORK.x, WORK.y))
log("letters centred on the liver crest", tuple(round(x, 3) for x in LET_C))
LETTERS = []
char_m = mat("M_Char", (0.06, 0.03, 0.02), rough=0.8)
nt = char_m.node_tree; pc = nt.nodes["Principled BSDF"]
pc.inputs["Emission Color"].default_value = (1.0, 0.35, 0.05, 1); pc.inputs["Emission Strength"].default_value = 0.0
def place_letter(name, path2d, cx):
    pts3 = []
    for (u, v) in path2d:
        x = LET_C.x + cx + u; y = LET_C.y + v
        loc, nrm = liver_surf(x, y)
        pts3.append(loc - nrm * 0.0011 if loc is not None else Vector((x, y, WORK.z - 0.03)))
    cu = bpy.data.curves.new(name, 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = 0.0022; cu.bevel_resolution = 2
    cu.use_fill_caps = True; cu.bevel_factor_mapping_end = 'SPLINE'
    sp = cu.splines.new('POLY'); sp.points.add(len(pts3) - 1)
    for p_, c_ in zip(sp.points, pts3): p_.co = (*c_, 1)
    o = bpy.data.objects.new(name, cu); sc.collection.objects.link(o); cu.materials.append(char_m)
    o.parent = STAGE
    return o, pts3
LS, PS = place_letter("Letter_S", S_path(), -0.5 * (LW + GAP))
LB, PBB = place_letter("Letter_B", B_path(), +0.5 * (LW + GAP))
log("letter z", round(PS[0].z, 3), round(PBB[0].z, 3))

if STOP == "abdomen":
    bpy.ops.wm.save_as_mainfile(filepath=OUT); raise SystemExit

# ================================================================== the argon pen (ours): body, blue grip band, nozzle, cable
pen_body = mat("M_PenBody", (0.93, 0.94, 0.95), rough=0.3); pen_blue = mat("M_PenBlue", (0.05, 0.35, 0.95), rough=0.35, coat=0.3)
def make_pen():
    parts = []
    parts.append(cyl("Pen_body", 0.0062, 0.25, (0, -0.075, 0), pen_body, rot=(R_(90), 0, 0), verts=24))
    parts.append(cyl("Pen_grip", 0.0068, 0.045, (0, 0.035, 0), pen_blue, rot=(R_(90), 0, 0), verts=24))
    bpy.ops.mesh.primitive_cone_add(radius1=0.0062, radius2=0.0022, depth=0.03, location=(0, 0.072, 0), rotation=(R_(-90), 0, 0), vertices=24)
    c = bpy.context.active_object; c.data.materials.append(pen_body); bpy.ops.object.shade_smooth(); parts.append(c)
    parts.append(cyl("Pen_noz", 0.0016, 0.016, (0, 0.093, 0), steel if "M_Steel" not in bpy.data.materials else bpy.data.materials["M_Steel"], rot=(R_(90), 0, 0), verts=12))
    parts.append(cyl("Pen_btn", 0.0025, 0.012, (0, 0.02, 0.0062), pen_blue, rot=(R_(90), 0, 0), verts=12))
    bpy.ops.object.select_all(action='DESELECT')
    for p_ in parts: p_.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]; bpy.ops.object.join()
    o = bpy.context.active_object; o.name = "ArgonPen"
    o.data.transform(Matrix.Translation(o.location)); o.location = (0, 0, 0)   # origin back at the build origin (tip at +0.101 Y)
    return o
PEN = make_pen()
PEN_TIP = Vector((0, 0.101, 0))

# ================================================================== tool grips: Child Of the wrist bone (R4), wrist solved naturally (R6)
TOOLS = {}
def tool_setup(rig, tool, side, pose, grip_y):
    fs(0)
    apply_pose(rig, side, pose, 0); apply_pose(rig, side, pose, 1); upd()
    th = Wt(rig, "finger1-3." + side); ix = Wt(rig, "finger2-3." + side)
    G = (th + ix) / 2 + (Wh(rig, "finger2-2." + side) - th).normalized() * 0.004
    fdir = (Wt(rig, "finger2-3." + side) - Wh(rig, "finger2-1." + side)).normalized()
    Mw = W(rig, "wrist." + side)
    wr, B0, basis, palm = _rest_hand(rig, side); sign = _rest_palm_sign(rig, side, B0.col[2])
    Rpose = (rig.matrix_world.to_3x3() @ rig.pose.bones["wrist." + side].matrix.to_3x3() @ rig.data.bones["wrist." + side].matrix_local.to_3x3().inverted())
    palmN = (Rpose @ (B0.col[2] * sign)).normalized()
    ydir = (fdir - palmN * fdir.dot(palmN) * 0.5).normalized()
    T = frame_from(ydir, -palmN, G) @ Matrix.Translation(Vector((0, -grip_y, 0)))
    tool.matrix_world = T
    c = tool.constraints.new('CHILD_OF'); c.name = "Hand"; c.target = rig; c.subtarget = "wrist." + side
    c.inverse_matrix = (rig.matrix_world @ rig.pose.bones["wrist." + side].matrix).inverted()
    c.set_inverse_pending = False
    tool.keyframe_insert("location", frame=0); tool.keyframe_insert("rotation_euler", frame=0)
    off = Mw.inverted() @ T
    TOOLS[tool.name] = dict(rig=rig, side=side, off=off, tip=Vector((0, max(v.co.y for v in tool.data.vertices), 0)))
    return off

EUL = [(x, y, z) for x in range(-40, 41, 10) for y in range(-30, 31, 15) for z in range(-24, 25, 12)]
WANG = []; ERR = []
def key_tool(tool, f, Tdes):
    """prop-led: key the tool's world matrix exactly (tip on target), key IK_hand so the hand holds it with the set-up grip"""
    info = TOOLS[tool.name]; rig = info["rig"]; R = RIG[rig.name]; s = info["side"]; off = info["off"]
    for c in list(tool.constraints): tool.constraints.remove(c)
    tool.matrix_world = Tdes
    tool.keyframe_insert("location", frame=f); tool.keyframe_insert("rotation_euler", frame=f)
    R.key_world("IK_hand." + s, f, rig.matrix_world.inverted() @ (Tdes @ off.inverted()))
    fs(f)
    tip_now = rig.matrix_world @ rig.pose.bones["wrist." + s].matrix @ off @ info["tip"]
    err = ((Tdes @ info["tip"]) - tip_now).length
    ERR.append((f, tool.name, round(err * 1000, 1)))
    return err

def pen_frame(tip, ydir, up=Vector((0, 0, 1))):
    M = frame_from(ydir, up, Vector((0, 0, 0)))
    M.translation = Vector(tip) - M.to_3x3() @ PEN_TIP
    return M

# ================================================================== SURGEON 1 in OR1: stands on her right side (+y), faces -y
DR = RIG["Surgeon"]; HD = HU["Surgeon"]
S1_POS = Vector((WORK.x + 0.20, TABLE_C.y + 0.26 + 0.33, 0))
DOC.location = S1_POS; DOC.rotation_euler = (0, 0, 0)
DOC.keyframe_insert("location", frame=1); DOC.keyframe_insert("rotation_euler", frame=1)
M_DEF = sectM("HEAR") @ Matrix.Translation(Vector((1.05, 3.70, 0))) @ Matrix.Rotation(R_(-60), 4, 'Z')   # defendant: faces -x (toward the bench)
key_obj_matrix(DOC, F_S1_OUT, M_DEF)
const_interp(DOC)
fs(1)
# wardrobe switch: theatre -> suit at F_S1_OUT
theatre = [O["S1Scrub.top"], O["S1Scrub.trousers"], O["S1.cap"], O["S1.mask"], O["S1.gloves"], O["Surgeon.hair_under_cap"]]
hearing = [O["S1Suit.top"], O["S1Suit.trousers"], part(DOC, "short02")]
key_vis(theatre, 1, True); key_vis(hearing, 1, False); key_vis(theatre, F_S1_OUT, False); key_vis(hearing, F_S1_OUT, True)
fs(1)
tool_setup(DOC, PEN, "R", "tripod", -0.15)
log("pen set up")

# body: feet planted, lean over the patient while working, breathing + small sway
def s1_body(f, lean, side_shift=0.0, turn=0.0, head=(0, 0), twist=0.0):
    ph = f / 60.0
    HD.key_root(f, DR.BN["root"].head_local + Vector((side_shift + 0.004 * math.sin(ph * 2 * math.pi / 3.4), -0.02 * lean / 20.0, -0.004 * (1 + math.sin(ph * 2 * math.pi / 4.0)) - 0.012 * lean / 20.0)), yaw=turn, flex=0)
    HD.key_spine(f, flex=lean, twist=twist, head=head)
for s in "LR":
    a = DR.BN["foot." + s].head_local
    for f in (1, F_S1_OUT - 1):
        DR.key_world("IK_foot." + s, f, DR.rest("IK_foot." + s))
        n = "Pole_knee." + s; pb = DR.PB[n]; pb.location = Vector((0, 0, 0)); pb.keyframe_insert("location", frame=f, group=n)

# the writing: the tip travels the S then the B, 6 mm above the surface (the argon beam bridges the gap)
W0, W1 = 24, 230        # VO "burn his initials into the patient's new liver" ~ 1.1 - 3.9 s
S_F = (40, 125); B_F = (140, 228)
def path_param(pts, t):
    L = [0.0]
    for a_, b_ in zip(pts, pts[1:]): L.append(L[-1] + (b_ - a_).length)
    tgt = t * L[-1]
    for k in range(1, len(L)):
        if L[k] >= tgt:
            u = (tgt - L[k - 1]) / max(1e-9, L[k] - L[k - 1]); return pts[k - 1].lerp(pts[k], u)
    return pts[-1]
def pen_dir(f):
    # pen leans back toward the surgeon's hand (+y) and to his right (-x): a natural writing angle
    return Vector((0.12, -0.42, -0.90)).normalized()
HOVER = 0.006
for f in range(1, 290, 2):
    if f < S_F[0]:
        u = smooth((f - 1) / (S_F[0] - 1)); tip = PS[0] + Vector((0, 0, HOVER + 0.05 * (1 - u)))
    elif f <= S_F[1]:
        tip = path_param(PS, (f - S_F[0]) / (S_F[1] - S_F[0])) + Vector((0, 0, HOVER))
    elif f < B_F[0]:
        u = smooth((f - S_F[1]) / (B_F[0] - S_F[1])); tip = PS[-1].lerp(PBB[0], u) + Vector((0, 0, HOVER + 0.012 * math.sin(math.pi * u)))
    elif f <= B_F[1]:
        tip = path_param(PBB, (f - B_F[0]) / (B_F[1] - B_F[0])) + Vector((0, 0, HOVER))
    else:
        u = smooth((f - B_F[1]) / 50.0); tip = PBB[-1] + Vector((0, 0, HOVER + 0.10 * u)) + Vector((0.02, 0.10, 0)) * u
    if f > 288: break
    key_tool(PEN, f, pen_frame(tip, pen_dir(f)))
log("pen writing keyed; max tip err mm", max(e for *_, e in ERR))
if STOP == "pen":
    bpy.ops.wm.save_as_mainfile(filepath=OUT); raise SystemExit

# ---- letter reveal follows the real (evaluated) pen tip: bevel_factor_end keyed from the nearest path parameter
def reveal(letter, pts, f0, f1):
    cu = letter.data
    L = [0.0]
    for a_, b_ in zip(pts, pts[1:]): L.append(L[-1] + (b_ - a_).length)
    best = 0.0
    cu.bevel_factor_end = 0.0; cu.keyframe_insert("bevel_factor_end", frame=f0 - 1)
    for f in range(f0, f1 + 1):
        fs(f); tip = PEN.matrix_world @ PEN_TIP
        k = min(range(len(pts)), key=lambda i: (pts[i] - tip).length)
        if (pts[k] - tip).length < 0.02: best = max(best, L[k] / L[-1])
        cu.bevel_factor_end = best; cu.keyframe_insert("bevel_factor_end", frame=f)
    cu.bevel_factor_end = 1.0; cu.keyframe_insert("bevel_factor_end", frame=f1 + 3)
reveal(LS, PS, S_F[0], S_F[1]); reveal(LB, PBB, B_F[0], B_F[1])
# char glow: embers while burning, then dark char
pc.inputs["Emission Strength"].default_value = 0.0; pc.inputs["Emission Strength"].keyframe_insert("default_value", frame=S_F[0] - 2)
pc.inputs["Emission Strength"].default_value = 2.5; pc.inputs["Emission Strength"].keyframe_insert("default_value", frame=S_F[0] + 4)
pc.inputs["Emission Strength"].keyframe_insert("default_value", frame=B_F[1])
pc.inputs["Emission Strength"].default_value = 0.0; pc.inputs["Emission Strength"].keyframe_insert("default_value", frame=B_F[1] + 40)

# ---- the argon beam: a thin blue-white emissive jet from the nozzle to the tissue + a small point light, only while burning
beam_m = mat("M_Beam", (0.6, 0.8, 1.0), emit=((0.55, 0.80, 1.0), 25.0))
bpy.ops.mesh.primitive_cone_add(radius1=0.0035, radius2=0.0009, depth=HOVER + 0.002, location=(0, 0, 0), vertices=16)
BEAM = bpy.context.active_object; BEAM.name = "ArgonBeam"; BEAM.data.materials.append(beam_m)
BEAM.data.transform(Matrix.Translation(Vector((0, 0, -(HOVER + 0.002) / 2))))
BEAM.parent = PEN; BEAM.matrix_parent_inverse = Matrix.Identity(4)
BEAM.location = PEN_TIP; BEAM.rotation_euler = (R_(90), 0, 0)   # cone axis -Z of BEAM -> along pen +Y
lt = bpy.data.lights.new("BeamLight", 'POINT'); lt.energy = 0.0; lt.color = (0.55, 0.8, 1.0); lt.shadow_soft_size = 0.002
BL = bpy.data.objects.new("BeamLight", lt); sc.collection.objects.link(BL); BL.parent = PEN; BL.location = PEN_TIP + Vector((0, 0.006, 0))
burn = [(S_F[0], S_F[1]), (B_F[0], B_F[1])]
key_vis([BEAM], 1, False)
for a_, b_ in burn:
    key_vis([BEAM], a_, True); key_vis([BEAM], b_ + 1, False)
    lt.energy = 0.0; lt.keyframe_insert("energy", frame=a_ - 1); lt.energy = 1.2; lt.keyframe_insert("energy", frame=a_ + 1)
    lt.keyframe_insert("energy", frame=b_); lt.energy = 0.0; lt.keyframe_insert("energy", frame=b_ + 2)
# sparks: a few tiny emissive beads that pop at the burn point and fall away (keyed, no sims)
spark_m = mat("M_Spark", (1.0, 0.7, 0.3), emit=((1.0, 0.65, 0.25), 30.0))
rs = random.Random(3)
for k in range(14):
    sp_ = sphere("Spark%d" % k, 0.0011, (0, 0, 0), spark_m, segs=8)
    seg = burn[k % 2]; f0 = rs.randint(seg[0] + 4, seg[1] - 12)
    fs(f0); p0 = PEN.matrix_world @ PEN_TIP - Vector((0, 0, HOVER))
    v = Vector((rs.uniform(-1, 1), rs.uniform(-1, 1), rs.uniform(0.6, 1.4))).normalized() * rs.uniform(0.25, 0.5)
    key_vis([sp_], 1, False); key_vis([sp_], f0, True); key_vis([sp_], f0 + 9, False)
    for d in range(0, 10, 2):
        t = d / 60.0; sp_.location = p0 + v * t + Vector((0, 0, -4.9 * t * t)); sp_.keyframe_insert("location", frame=f0 + d)

# ================================================================== the tray (Mayo stand at his right) where the pen is put down
TRAY_C = Vector((S1_POS.x - 0.62, S1_POS.y - 0.25, 1.02))
box("MayoTray", (0.46, 0.34, 0.02), (TRAY_C.x, TRAY_C.y, TRAY_C.z - 0.01), bpy.data.materials["M_Steel"], bevel=0.006)
box("MayoDrape", (0.44, 0.32, 0.004), (TRAY_C.x, TRAY_C.y, TRAY_C.z + 0.002), bpy.data.materials["M_Drape"], bevel=0.001)
cyl("MayoPost", 0.018, TRAY_C.z - 0.02, (TRAY_C.x + 0.18, TRAY_C.y, (TRAY_C.z - 0.02) / 2), bpy.data.materials["M_Steel"])
cyl("MayoFoot", 0.20, 0.03, (TRAY_C.x + 0.18, TRAY_C.y, 0.015), bpy.data.materials["M_Steel"])
for n_ in ("MayoTray", "MayoDrape", "MayoPost", "MayoFoot"):
    o_ = O[n_]; o_.parent = STAGE
# a few instruments lying on it (no contacts): scissors-like clamps as flat steel shapes
for k in range(3):
    box("TrayTool%d" % k, (0.012, 0.15, 0.006), (TRAY_C.x - 0.12 + k * 0.05, TRAY_C.y + 0.02, TRAY_C.z + 0.008), bpy.data.materials["M_Steel"], bevel=0.002).parent = STAGE

# pen: after the B lift (to 290) the hand carries it to the tray and lays it down (frame 330); the release stays on the tray
F_PUT = 330
for f in range(292, F_PUT + 1, 4):
    u = smooth((f - 290) / (F_PUT - 290))
    fs(f)
    start = PBB[-1] + Vector((0.02, 0.10, HOVER + 0.10))
    end = TRAY_C + Vector((0.05, -0.04, 0.012))
    tip = start.lerp(end, u) + Vector((0, 0, 0.08 * math.sin(math.pi * u)))
    ydir = pen_dir(f).lerp(Vector((-0.2, -0.98, -0.05)).normalized(), u).normalized()
    key_tool(PEN, f, pen_frame(tip, ydir))
fs(F_PUT)
# with the constraint off the pen's own transform must be that resting matrix (flat on the tray)
Mrest = frame_from(Vector((-0.2, -0.98, 0)), Vector((0, 0, 1)), Vector((0, 0, 0)))
Mrest.translation = TRAY_C + Vector((0.05, -0.04, 0.0105)) - Mrest.to_3x3() @ PEN_TIP
PEN.matrix_world = Mrest; PEN.keyframe_insert("location", frame=F_PUT + 1); PEN.keyframe_insert("rotation_euler", frame=F_PUT + 1)
log("pen put down at", F_PUT)

# the cable: from the pen's back end down to the floor unit behind him (hooked to the pen)
gen = box("ArgonUnit", (0.40, 0.45, 0.9), (S1_POS.x - 0.75, S1_POS.y + 0.45, 0.45), mat("M_Unit", (0.92, 0.92, 0.9), rough=0.4), bevel=0.02)
gen.parent = STAGE
box("ArgonUnitPanel", (0.30, 0.01, 0.2), (S1_POS.x - 0.75, S1_POS.y + 0.22, 0.75), mat("M_UnitPanel", (0.05, 0.25, 0.6), rough=0.2, emit=((0.1, 0.4, 1.0), 1.0)), bevel=0).parent = STAGE
CAB = None

# ================================================================== SURGEON 1 acting (OR1): lean while writing, stitch (hands below frame), straighten, mask down, smirk
HEADK1 = [(1, 16, 0), (100, 18, 4), (230, 16, 0), (300, 20, -10), (330, 22, 6), (370, 18, -6), (420, 20, 4), (440, 8, 0), (470, 0, -4), (500, -6, 8), (530, -2, 14), (560, 2, 10), (600, 0, 0)]
LEANK1 = [(1, 22), (230, 22), (300, 16), (330, 26), (420, 26), (450, 6), (600, 4)]
TURNK1 = [(1, 0), (280, 0), (318, -16), (340, 0), (600, 0)]
hk_f = pchip([(f, p) for f, p, _ in HEADK1]); hy_f = pchip([(f, y) for f, _, y in HEADK1])
ln_f = pchip(LEANK1); tn_f = pchip(TURNK1)
for f in list(range(1, F_S1_OUT, 6)) + [F_S1_OUT - 1]:
    s1_body(f, ln_f(f), turn=tn_f(f), head=(hk_f(f), hy_f(f)))
# left hand: sterile hold in front of his chest (palms toward him), clear of the patient and his torso by >= 10 cm
def chest_front(rig, f, dz=-0.16, fwd=0.26, lat=0.0):
    fs(f); c0 = (Wh(rig, "upperarm01.L") + Wh(rig, "upperarm01.R")) / 2
    face = rig.matrix_world.to_3x3() @ Vector((0, -1, 0)); latv = rig.matrix_world.to_3x3() @ Vector((1, 0, 0))
    return c0 + face * fwd + Vector((0, 0, dz)) + latv * lat, face, latv
def sterile(rig, s, f, lat=0.11, dz=-0.20, fwd=0.28):
    sx = 1 if s == "L" else -1
    p, face, latv = chest_front(rig, f, dz=dz, fwd=fwd, lat=sx * lat)
    hand_world(rig, s, f, p, Vector((0, 0, 1)) + face * 0.2, -face, pole=p + latv * sx * 0.35 + Vector((0, 0, -0.35)))
def hang(rig, s, f, out=0.13, fwd=-0.05, down=0.10, palm_in=True):
    sx = 1 if s == "L" else -1; fs(f); Mi = rig.matrix_world
    wr = Wh(rig, "upperleg01." + s) + Mi.to_3x3() @ Vector((sx * (out + 0.04), fwd, -down - 0.05))
    hand_world(rig, s, f, wr, Mi.to_3x3() @ Vector((0, -0.25, -1)), Mi.to_3x3() @ Vector((-sx, 0.2, 0)),
               pole=Wh(rig, "upperarm01." + s) + Mi.to_3x3() @ Vector((sx * 0.45, 0.5, -0.3)))
    apply_pose(rig, s, "relaxed", f)
# while writing, the left hand rests flat on the drape at the patient's flank? no: sterile hold (fewest contacts)
for f in (1, 120, 230, 300):
    sterile(DOC, "L", f, lat=0.14, dz=-0.30, fwd=0.30)
    apply_pose(DOC, "L", "relaxed", f)
# stitching (330-420): both hands low over the wound (below the frame), small rhythmic motion, no tool contact shown
for i, f in enumerate(range(336, 421, 12)):
    fs(f)
    for s in "LR":
        sx = 1 if s == "L" else -1
        p = WORK + Vector((sx * 0.10 - 0.01, 0.10, 0.13 + 0.025 * ((i + (0 if s == "L" else 1)) % 2)))
        hand_world(DOC, s, f, p, Vector((0, -0.5, -0.8)), Vector((0, 0, -1)), pole=p + Vector((sx * 0.4, 0.3, -0.2)))
        apply_pose(DOC, s, "pinch", f)
for s in "LR":
    for f in (432, 470):
        hang(DOC, s, f, out=0.10, fwd=-0.03, down=0.06)
# "acted like nothing had happened": hands drop to rest, a small shrug and a casual head tilt to the side
for f in (474, 512, 540, F_S1_OUT - 1):
    hang(DOC, "L", f, out=0.10, fwd=-0.03, down=0.06); hang(DOC, "R", f, out=0.10, fwd=-0.03, down=0.06)
for bn in ("clavicle.L", "clavicle.R"):
    if bn in DR.PB:
        for f, ang in ((496, 0), (508, 9), (520, 9), (534, 0)):
            DR.key_rot(bn, f, [("X", ang)])
# the wound closes while the camera is on his face (346-400), the sutures appear with it
for o_, k_ in ((SKIN, "closed"), (CAV, "closed")):
    kb = o_.data.shape_keys.key_blocks[k_]
    kb.value = 0.0; kb.keyframe_insert("value", frame=346); kb.value = 1.0; kb.keyframe_insert("value", frame=400)
    kb.keyframe_insert("value", frame=F_PAT_OR2 - 1); kb.value = 0.0; kb.keyframe_insert("value", frame=F_PAT_OR2)
sut_m = mat("M_Suture", (0.05, 0.10, 0.45), rough=0.4)
SUT = []
for k in range(9):
    x = WORK.x - INC_HX * 0.85 + k * (INC_HX * 1.7 / 8)
    z0, _ = surf_z(x, WORK.y)
    pts = [Vector((x - 0.002, WORK.y - 0.007, z0 + 0.0035)), Vector((x, WORK.y, z0 + 0.0055)), Vector((x + 0.002, WORK.y + 0.007, z0 + 0.0035))]
    st = curve_tube("Suture%d" % k, pts, 0.0007, sut_m, parent=STAGE)
    SUT.append(st)
    key_vis([st], 1, False); key_vis([st], 360 + k * 5, True); key_vis([st], F_PAT_OR2, False)

if STOP == "or1":
    bpy.ops.wm.save_as_mainfile(filepath=OUT); raise SystemExit

# ================================================================== FACES: blinks, smiles, pain, surprise, talk (numeric axis finding, no guessing)
def lid_sign(rig, s):
    pb = rig.pose.bones["orbicularis03." + s]; upd()
    t0 = Wt(rig, pb.name).z; pb.rotation_quaternion = Quaternion((1, 0, 0), R_(20)); upd(); t1 = Wt(rig, pb.name).z
    pb.rotation_quaternion = Quaternion(); upd()
    return 1.0 if t1 < t0 else -1.0
def blinks(rig, frames, base=0.0, base_keys=None):
    for s in "LR":
        n = "orbicularis03." + s
        if n not in rig.pose.bones: continue
        sg = lid_sign(rig, s); pb = rig.pose.bones[n]
        def lid(f, ang):
            pb.rotation_quaternion = Quaternion((1, 0, 0), R_(ang * sg)); pb.keyframe_insert("rotation_quaternion", frame=f, group=n)
        for f, a_ in (base_keys or [(1, base)]):
            lid(f, a_)
        for bf in frames:
            cur = base
            if base_keys:
                for f, a_ in base_keys:
                    if f <= bf: cur = a_
            lid(bf, cur); lid(bf + 4, 24); lid(bf + 7, 24); lid(bf + 13, cur)
def corner_axis(rig, bone, want):
    pb = rig.pose.bones[bone]; upd(); base = Wt(rig, bone); best = None
    for ax in ((1, 0, 0), (0, 0, 1), (0, 1, 0)):
        for sg in (1, -1):
            pb.rotation_quaternion = Quaternion(ax, R_(12 * sg)); upd()
            d = rig.matrix_world.inverted().to_3x3() @ (Wt(rig, bone) - base)
            v = d.dot(want)
            if best is None or v > best[0]: best = (v, ax, sg)
    pb.rotation_quaternion = Quaternion(); upd()
    return best
def expression(rig, keys, bones_want):
    """keys: [(frame, amount)], bones_want: {bone: (want_dir_rest, deg)}"""
    for bone, (want, deg) in bones_want.items():
        if bone not in rig.pose.bones: continue
        _, ax, sg = corner_axis(rig, bone, Vector(want))
        pb = rig.pose.bones[bone]
        for f, amt in keys:
            pb.rotation_quaternion = Quaternion(ax, R_(deg * sg * amt)); pb.keyframe_insert("rotation_quaternion", frame=f, group=bone)
def jaw_talk(rig, f0, f1, amp=7.0, seed=1):
    if "jaw" not in rig.pose.bones: return
    _, ax, sg = corner_axis(rig, "jaw", Vector((0, 0, -1)))
    pb = rig.pose.bones["jaw"]; rr = random.Random(seed)
    pb.rotation_quaternion = Quaternion(); pb.keyframe_insert("rotation_quaternion", frame=f0 - 4, group="jaw")
    f = f0
    while f < f1:
        a_ = rr.uniform(0.3, 1.0) * amp
        pb.rotation_quaternion = Quaternion(ax, R_(a_ * sg)); pb.keyframe_insert("rotation_quaternion", frame=f, group="jaw")
        f += rr.randint(6, 10)
        pb.rotation_quaternion = Quaternion(ax, R_(a_ * 0.25 * sg)); pb.keyframe_insert("rotation_quaternion", frame=f, group="jaw")
        f += rr.randint(4, 8)
    pb.rotation_quaternion = Quaternion(); pb.keyframe_insert("rotation_quaternion", frame=f1 + 4, group="jaw")
def eyes(rig, f0, f1, step=40, amp=(3, 5), seed=2):
    R = RIG[rig.name]; rr = random.Random(seed)
    for f in range(f0, f1, step):
        a_, b_ = rr.uniform(-amp[0], amp[0]), rr.uniform(-amp[1], amp[1])
        for s in "LR": R.key_rot("eye." + s, f, [("X", a_), ("Z", b_)])
SMILE = {"risorius03.L": ((1, 0, 0.6), 14), "risorius03.R": ((-1, 0, 0.6), 14), "levator05.L": ((0.3, 0, 1), 10), "levator05.R": ((-0.3, 0, 1), 10),
         "oris04.L": ((1, 0, 0.5), 10), "oris04.R": ((-1, 0, 0.5), 10)}
PAIN = {"risorius03.L": ((1, 0, -0.4), 12), "risorius03.R": ((-1, 0, -0.4), 12), "oris04.L": ((1, 0, -0.5), 8), "oris04.R": ((-1, 0, -0.5), 8)}
fs(1)
# surgeon 1: blinks; smug smile after the mask comes down (510-600), a slight one-sided lift
blinks(DOC, [90, 260, 380, 455, 530, 700, 1260, 1380, 1470, 1560])

eyes(DOC, 1, 600, seed=4)
# patient: eyes closed in theatre (anaesthesia), open at home; pain squint at home
for s in "LR":
    n = "orbicularis03." + s; sg = lid_sign(PAT, s); pb = PAT.pose.bones[n]
    for f, ang in ((1, 26), (F_PAT_HOME - 1, 26), (F_PAT_HOME, 0), (650, 0), (660, 5), (760, 3), (790, 4), (F_PAT_OR2 - 1, 4), (F_PAT_OR2, 26), (END, 26)):
        pb.rotation_quaternion = Quaternion((1, 0, 0), R_(ang * sg)); pb.keyframe_insert("rotation_quaternion", frame=f, group=n)
expression(PAT, [(1, 0), (648, 0), (664, 1.0), (790, 0.9), (F_PAT_OR2 - 1, 0.9), (F_PAT_OR2, 0.0)], PAIN)
eyes(PAT, F_PAT_HOME, F_PAT_OR2, step=30, seed=5)

# ================================================================== HOME (596-846): she stands, glances at the calendar, the pain hits, she doubles over
fs(F_PAT_HOME)
def pat_home_pose(f, flex, knee, head, right_on=0.0, left_on=0.0, sway=0.0):
    root = PR.BN["root"].head_local.copy() + Vector((sway, 0.0, -knee))
    HP.key_root(f, root + Vector((0, 0.03 * flex / 30.0, 0)), flex=0)
    HP.key_spine(f, flex=flex, twist=0.0, head=head)
    for s in "LR":
        PR.key_world("IK_foot." + s, f, PR.rest("IK_foot." + s))
        n = "Pole_knee." + s; pb = PR.PB[n]; pb.location = Vector((0, 0, 0)); pb.keyframe_insert("location", frame=f, group=n)
    fs(f)
    sx_ = {"L": 1, "R": -1}
    # relaxed arms (slight bend) -> right hand on the right upper abdomen, left hand on the left thigh above the knee
    for s, on in (("R", right_on), ("L", left_on)):
        sx = sx_[s]
        sh = Wh(PAT, "upperarm01." + s); Mi = PAT.matrix_world
        hang = Wh(PAT, "upperleg01." + s) + Mi.to_3x3() @ Vector((sx * 0.10, -0.11, -0.13))
        if s == "R":
            # abdomen point in the spine04 bone frame (rest), 2.6 cm out from the skin: shirt (1.2 cm) + palm skin (1.4 cm)
            Mb = PAT.matrix_world @ PR.PB["spine04"].matrix @ PR.BN["spine04"].matrix_local.inverted()
            tgt = Mb @ ABD_REST; nrm = (Mb.to_3x3() @ Vector((-0.35, -1, 0))).normalized()
            wr_on = tgt + nrm * 0.026 + (Mb.to_3x3() @ Vector((-0.07, 0.0, -0.01)))
            fdir_on = Mb.to_3x3() @ Vector((0.85, 0.0, 0.35)); palm_on = -nrm
        else:
            Mb = PAT.matrix_world @ PR.PB["upperleg02.L"].matrix @ PR.BN["upperleg02.L"].matrix_local.inverted()
            tgt = Mb @ THIGH_REST; nrm = (Mb.to_3x3() @ Vector((0.15, -1, 0.0))).normalized()
            wr_on = tgt + nrm * 0.03 + (Mb.to_3x3() @ Vector((0.0, 0.0, 0.07)))
            fdir_on = Mb.to_3x3() @ Vector((0.0, -0.2, -1.0)); palm_on = -nrm
        wr = hang.lerp(wr_on, on)
        fd = (Mi.to_3x3() @ Vector((0, -0.15, -1))).lerp(fdir_on, on)
        pm = (Mi.to_3x3() @ Vector((-sx, 0, 0))).lerp(palm_on, on)
        hand_world(PAT, s, f, wr, fd, pm, pole=sh + Mi.to_3x3() @ Vector((sx * 0.45, 0.45, -0.25)))
        apply_pose(PAT, s, "relaxed" if on < 0.5 else ("cup_hold" if s == "R" else "relaxed"), f)
# rest-space contact points
def front_surface(x, z, rig_body):
    best = None
    for v in rig_body.data.vertices:
        if abs(v.co.x - x) < 0.012 and abs(v.co.z - z) < 0.012:
            if best is None or v.co.y < best: best = v.co.y
    return best
sp4 = PR.BN["spine04"].head_local; sp5 = PR.BN["spine05"].head_local
az = sp4.z + 0.03
ABD_REST = Vector((-0.085, front_surface(-0.085, az, PB) - 0.0, az))
kn = PR.BN["lowerleg01.L"].head_local
THIGH_REST = Vector((kn.x, front_surface(kn.x, kn.z + 0.12, PB), kn.z + 0.12))
log("abd rest", tuple(round(x, 3) for x in ABD_REST), "thigh", tuple(round(x, 3) for x in THIGH_REST))
HOMEK = [  # f, flex, knee, head(pitch,yaw), right_on, left_on, sway
    (F_PAT_HOME, 2, 0.0, (-2, 0), 0, 0, 0.0), (612, 2, 0.0, (-4, -22), 0, 0, 0.004), (632, 3, 0.0, (-2, -26), 0, 0, 0.0),
    (644, 4, 0.0, (0, -8), 0, 0, -0.004), (652, 12, 0.02, (8, 0), 0.6, 0, 0.0), (662, 24, 0.045, (14, 4), 1.0, 0.6, 0.006),
    (674, 40, 0.07, (10, 2), 1.0, 1.0, 0.0), (700, 42, 0.07, (2, -2), 1.0, 1.0, -0.006), (726, 38, 0.065, (-6, 2), 1.0, 1.0, 0.004),
    (752, 42, 0.07, (0, -4), 1.0, 1.0, 0.0), (780, 40, 0.07, (-8, 0), 1.0, 1.0, -0.004), (810, 41, 0.07, (-4, 3), 1.0, 1.0, 0.003), (F_PAT_OR2 - 1, 41, 0.07, (-4, 3), 1.0, 1.0, 0.0)]
for k_ in HOMEK:
    pat_home_pose(*k_)
# breathing in the pain (small extra spine flex wobble) every 12 frames between keys is carried by the keys above
# lying again in OR2 (re-key the lying pose so the home pose doesn't blend into it)
pat_lying_pose(F_PAT_OR2)
fs(F_PAT_OR2)

# ================================================================== OR2: the second surgeon (a different doctor) finds the initials
DR2 = RIG["Surgeon2"]; HD2 = HU["Surgeon2"]
M_S2 = sectM("OR2") @ Matrix.Translation(S1_POS + Vector((0.02, 0.0, 0)))
DOC2.matrix_world = M_S2; DOC2.keyframe_insert("location", frame=1); DOC2.keyframe_insert("rotation_euler", frame=1)
fs(F_PAT_OR2)
for s in "LR":
    for f in (1, END):
        DR2.key_world("IK_foot." + s, f, DR2.rest("IK_foot." + s))
PROBE = None
probe_m = bpy.data.materials["M_Steel"]
parts_ = [cyl("Pr_shaft", 0.0018, 0.12, (0, 0.05, 0), probe_m, rot=(R_(90), 0, 0), verts=12),
          cyl("Pr_handle", 0.0055, 0.22, (0, -0.12, 0), mat("M_ProbeGrip", (0.85, 0.85, 0.88), rough=0.3, metal=0.9), rot=(R_(90), 0, 0), verts=16),
          sphere("Pr_ball", 0.0024, (0, 0.11, 0), probe_m, segs=10)]
bpy.ops.object.select_all(action='DESELECT')
for p_ in parts_: p_.select_set(True)
bpy.context.view_layer.objects.active = parts_[1]; bpy.ops.object.join(); PROBE = bpy.context.active_object; PROBE.name = "Probe"
PROBE.data.transform(Matrix.Translation(PROBE.location)); PROBE.location = (0, 0, 0)
tool_setup(DOC2, PROBE, "R", "tripod", -0.17)
PROBE_TIP = TOOLS["Probe"]["tip"]
WORK2 = sectM("OR2") @ WORK
PS2 = [sectM("OR2") @ p_ for p_ in PS]; PB2 = [sectM("OR2") @ p_ for p_ in PBB]
def probe_frame(tip, ydir):
    M = frame_from(ydir, Vector((0, 0, 1)), Vector((0, 0, 0))); M.translation = Vector(tip) - M.to_3x3() @ PROBE_TIP; return M
pdir2 = (sectM("OR2").to_3x3() @ Vector((0.12, -0.42, -0.90))).normalized()
# body: approaches the table (lean grows), looks down, finds it, straightens with wide eyes
S2HEAD = [(1, 10, 0), (870, 12, 0), (930, 26, 6), (1000, 32, 0), (1110, 34, 2), (1135, 14, -4), (1160, 4, -8), (END, 0, -6)]
S2LEAN = [(1, 4), (870, 4), (940, 18), (1110, 22), (1140, 8), (END, 6)]
h2p = pchip([(f, p) for f, p, _ in S2HEAD]); h2y = pchip([(f, y) for f, _, y in S2HEAD]); l2 = pchip(S2LEAN)
for f in list(range(1, END, 6)) + [END]:
    ph = f / 60.0
    HD2.key_root(f, DR2.BN["root"].head_local + Vector((0.004 * math.sin(ph * 2 * math.pi / 3.1), -0.02 * l2(f) / 20.0, -0.004 * (1 + math.sin(ph * 2 * math.pi / 4.2)) - 0.012 * l2(f) / 20.0)), flex=0)
    HD2.key_spine(f, flex=l2(f), head=(h2p(f), h2y(f)))
for f in (1, 900, 960, 1135, 1180, END):
    sterile(DOC2, "L", f, lat=0.13, dz=-0.26, fwd=0.28); apply_pose(DOC2, "L", "relaxed", f)
# probe: held up in ready position, then the tip glides 8 mm above the letters (no contact), pauses on the B, lifts
for f in range(850, 1182, 3):
    fs(f)
    READY2 = WORK2 + Vector((0, 0, 0.12)) + (sectM("OR2").to_3x3() @ Vector((0.03, 0.10, 0.0)))
    if f < 960:
        tip = READY2; yd = pdir2
    elif f < 1000:
        u = smooth((f - 960) / 40.0)
        tip = READY2.lerp(PS2[0] + Vector((0, 0, 0.012)), u); yd = pdir2
    elif f < 1100:
        u = (f - 1000) / 100.0
        allp = PS2 + PB2
        tip = allp[min(len(allp) - 1, int(u * (len(allp) - 1)))] + Vector((0, 0, 0.010)); yd = pdir2
    else:
        u = smooth((f - 1100) / 50.0)
        tip = (PB2[-1] + Vector((0, 0, 0.010))).lerp(READY2, min(1, u)); yd = pdir2
    key_tool(PROBE, f, probe_frame(tip, yd))
blinks(DOC2, [880, 990, 1070, 1220])
eyes(DOC2, 846, 1182, seed=8)
# surprise: lids lift (negative blink) + brows (levator) at 1112-1182
for s in "LR":
    n = "orbicularis03." + s; sg = lid_sign(DOC2, s); pb = DOC2.pose.bones[n]
    for f, ang in ((1100, 0), (1116, -9), (1175, -9), (1200, 0)):
        pb.rotation_quaternion = Quaternion((1, 0, 0), R_(ang * sg)); pb.keyframe_insert("rotation_quaternion", frame=f, group=n)

if STOP == "or2":
    bpy.ops.wm.save_as_mainfile(filepath=OUT); raise SystemExit

# ================================================================== HEARING (1183-1644): defendant (surgeon 1 in a suit) admits; the judge's gavel comes down
HEAR = O["SECT_HEAR"]
fs(1300)
# defendant: standing, arms relaxed with a slight bend, one open-palm gesture as he admits, head bows at the verdict
DEFH = [(F_S1_OUT, 0, 0), (1250, -2, 6), (1300, 4, 2), (1340, 8, -4), (1380, 2, 4), (1420, 6, 0), (1460, -2, 10), (1500, 0, 8), (1512, 4, 6),
        (1540, 14, 2), (1570, 20, 0), (1598, 6, -6), (1622, -4, -8), (END, -2, -8)]
DEFL = [(F_S1_OUT, 2), (1300, 4), (1500, 3), (1540, 8), (1600, 12), (END, 12)]
dp = pchip([(f, p) for f, p, _ in DEFH]); dy = pchip([(f, y) for f, _, y in DEFH]); dl = pchip(DEFL)
for f in list(range(F_S1_OUT, END, 6)) + [END]:
    ph = f / 60.0
    HD.key_root(f, DR.BN["root"].head_local + Vector((0.004 * math.sin(ph * 2 * math.pi / 3.6), 0, -0.004 * (1 + math.sin(ph * 2 * math.pi / 4.4)) - (0.012 if f > 1530 else 0))), flex=0)
    HD.key_spine(f, flex=dl(f), head=(dp(f), dy(f)))
for s in "LR":
    for f in (F_S1_OUT, END):
        DR.key_world("IK_foot." + s, f, DR.rest("IK_foot." + s))
for f in (F_S1_OUT, 1290, 1372, 1400, 1470, 1520, 1560, END):
    hang(DOC, "L", f, out=0.06, fwd=-0.10, down=0.04)
for f in (F_S1_OUT, 1290, 1400, 1470, 1520, 1560, END):
    hang(DOC, "R", f, out=0.06, fwd=-0.10, down=0.04)
# the open-palm admission gesture (right hand rises to waist height in front, palm up, 22 cm clear of the torso)
for f, amt in ((1312, 0.6), (1330, 1.0), (1356, 1.0), (1372, 0.5)):
    fs(f); Mi = DOC.matrix_world
    p0 = Wh(DOC, "upperleg01.R") + Mi.to_3x3() @ Vector((-0.17, -0.05, -0.15))
    p1 = Wh(DOC, "spine03") + Mi.to_3x3() @ Vector((-0.16, -0.30, 0.02))
    wr = p0.lerp(p1, amt)
    hand_world(DOC, "R", f, wr, (Mi.to_3x3() @ Vector((0.25, -1, 0.1))).normalized(), (Mi.to_3x3() @ Vector((0, 0, 1))).lerp(Mi.to_3x3() @ Vector((1, 0, 0)), 1 - amt),
               pole=Wh(DOC, "upperarm01.R") + Mi.to_3x3() @ Vector((-0.45, 0.35, -0.35)))
    apply_pose(DOC, "R", "open_alarm" if amt > 0.8 else "relaxed", f)
jaw_talk(DOC, 1262, 1425, amp=7, seed=3)
eyes(DOC, F_S1_OUT, END, step=50, seed=9)

# judge: seated (pelvis on the seat, feet on the floor under the bench), left hand flat on the bench, gavel in the right hand
JR = RIG["Judge"]; HJ = HU["Judge"]
CHAIR_L = Vector((-1.38, 3.70)); SEAT_TOP = 0.47 + 0.045
M_J = sectM("HEAR") @ Matrix.Translation(Vector((CHAIR_L.x + 0.04, CHAIR_L.y, 0))) @ Matrix.Rotation(R_(90), 4, 'Z')
JUD.matrix_world = M_J; JUD.keyframe_insert("location", frame=1); JUD.keyframe_insert("rotation_euler", frame=1)
fs(1)
hipj = JR.BN["upperleg01.L"].head_local.z
drop = hipj - (SEAT_TOP + 0.085)
JH = [(1, 2, 0), (1440, 4, -6), (1462, -4, 4), (1490, 6, 6), (1502, 10, 4), (1530, 2, -10), (1580, -2, -16), (END, 0, -14)]
jp = pchip([(f, p) for f, p, _ in JH]); jy = pchip([(f, y) for f, _, y in JH])
for f in list(range(1, END, 6)) + [END]:
    ph = f / 60.0
    HJ.key_root(f, JR.BN["root"].head_local + Vector((0, 0.0, -drop - 0.003 * (1 + math.sin(ph * 2 * math.pi / 4.0)))), flex=0)
    HJ.key_spine(f, flex=6 + (5 if 1488 <= f <= 1512 else 0), head=(jp(f), jy(f)))
for s in "LR":
    sx = 1 if s == "L" else -1
    a = JR.BN["foot." + s].head_local
    for f in (1, END):
        JR.key_world("IK_foot." + s, f, Matrix.Translation(Vector((sx * 0.02, -0.42, 0.0))) @ JR.rest("IK_foot." + s))
        n = "Pole_knee." + s; pb = JR.PB[n]; pb.location = Vector((0, 0, 0.5)); pb.keyframe_insert("location", frame=f, group=n)
BENCH_TOP = 0.825
# left hand flat on the bench (R2: palm on the surface + 0.5 cm, fingers forward)
for f in (1, 1480, 1500, END):
    fs(f)
    p = sect("HEAR", (-0.96, 3.98, BENCH_TOP))
    place_hand(JUD, "L", f, p, Vector((0, 0, -1)), sectM("HEAR").to_3x3() @ Vector((1, 0.1, 0)), skin=0.017)
    apply_pose(JUD, "L", "flat_palm", f)
# gavel: hammer grip on the handle (wrap), Child Of the right wrist; head strikes the block on "lost" (~1500)
GAV = O["Gavel"]; BLK = O["GavelBlock"]
fs(1)
apply_pose(JUD, "R", "wrap_grip", 0); apply_pose(JUD, "R", "wrap_grip", 1); upd()
def wrap_frame(rig, s):
    k1 = Wh(rig, "finger2-1." + s); k5 = Wh(rig, "finger5-1." + s); mid = Wh(rig, "finger3-2." + s)
    across = (k1 - k5).normalized(); wr = Wh(rig, "wrist." + s)
    palm_c = (k1 + k5) / 2 * 0.6 + wr * 0.4
    inward = (mid - palm_c); inward = (inward - across * inward.dot(across)).normalized()
    centre = palm_c + inward * 0.022
    return centre, across, inward
cen, acr, inw = wrap_frame(JUD, "R")
fdir_ = (Wh(JUD, "finger3-1.R") - Wh(JUD, "wrist.R")).normalized()
# tool frame: +Y along the handle toward the head (= across the palm, out of the index side), +Z = head axis
GRIP_Y = -0.17
up_ = fdir_.cross(acr).normalized()
T = frame_from(acr, acr.cross(inw), cen) @ Matrix.Translation(Vector((0, -GRIP_Y, 0)))
GAV.parent = None; GAV.matrix_world = T
c = GAV.constraints.new('CHILD_OF'); c.name = "Hand"; c.target = JUD; c.subtarget = "wrist.R"
c.inverse_matrix = (JUD.matrix_world @ JUD.pose.bones["wrist.R"].matrix).inverted(); c.set_inverse_pending = False
GAV.keyframe_insert("location", frame=0); GAV.keyframe_insert("rotation_euler", frame=0)
TOOLS["Gavel"] = dict(rig=JUD, side="R", off=W(JUD, "wrist.R").inverted() @ T, tip=Vector((0, 0, 0)))
blk_top = BLK.matrix_world.translation + Vector((0, 0, 0.0175))
toward = (sectM("HEAR").to_3x3() @ Vector((0.35, -1.0, 0))).normalized()   # handle points from his hand toward the block (his right, forward)
def gavel_at(head_c, tilt):
    """head centre at head_c, handle direction `toward` tilted up by `tilt` deg (wrist lift), head axis near vertical"""
    yd = (toward * math.cos(R_(tilt)) + Vector((0, 0, math.sin(R_(tilt))))).normalized()
    M = frame_from(yd, Vector((0, 0, 1)), Vector((0, 0, 0))); M.translation = head_c; return M
REST_HEAD = blk_top + Vector((0, 0, 0.032))          # head resting on the block (radius 3 cm)
GK = [(1, 0.0, -20), (1440, 0.0, -20), (1462, 0.03, -12), (1484, 0.20, 18), (1494, 0.22, 20), (1500, 0.0, -20), (1504, 0.012, -17), (1510, 0.0, -20), (1560, 0.0, -20), (END, 0.0, -20)]
gdz = pchip([(k[0], k[1]) for k in GK]); gtl = pchip([(k[0], k[2]) for k in GK])
for f in [1, 1200] + list(range(1430, 1570, 2)) + [END]:
    key_tool(GAV, f, gavel_at(REST_HEAD + Vector((0, 0, max(0.0, gdz(f)))), gtl(f)))
log("gavel keyed")
jaw_talk(JUD, 1440, 1496, amp=8, seed=12)
blinks(JUD, [200, 1300, 1452, 1530, 1600])
eyes(JUD, 1183, END, step=45, seed=13)

for s_ in "LR":
    n_ = "orbicularis03." + s_; sg_ = lid_sign(DOC, s_); pb_ = DOC.pose.bones[n_]
    for f_, ang_ in ((1612, 0), (1630, 20), (END, 22)):
        pb_.rotation_quaternion = Quaternion((1, 0, 0), R_(ang_ * sg_)); pb_.keyframe_insert("rotation_quaternion", frame=f_, group=n_)
# breathing-out shoulders on the final beat
for bn in ("clavicle.L", "clavicle.R"):
    if bn in DR.PB:
        for f_, ang_ in ((1600, 0), (1618, 6), (1640, -3)):
            DR.key_rot(bn, f_, [("X", ang_)])
if STOP == "hear":
    bpy.ops.wm.save_as_mainfile(filepath=OUT); raise SystemExit

# ================================================================== evidence photo for the hearing-room screen: the branded liver, rendered from this scene
fs(262)
ecam_d = bpy.data.cameras.new("EvidenceCam"); ECAM = bpy.data.objects.new("EvidenceCam", ecam_d); sc.collection.objects.link(ECAM)
ecam_d.lens = 50; ecam_d.sensor_fit = 'HORIZONTAL'
ctr = WORK + Vector((-0.006, -0.004, -0.03))
ECAM.location = ctr + Vector((0.0, -0.10, 0.30)); ECAM.rotation_euler = (ctr - ECAM.location).to_track_quat('-Z', 'Y').to_euler()
hidden = []
for o in (PEN, BEAM, DOC):
    hidden.append((o, o.hide_render)); o.hide_render = True
for ch_ in DOC.children:
    hidden.append((ch_, ch_.hide_render)); ch_.hide_render = True
old = (sc.camera, sc.render.resolution_x, sc.render.resolution_y, sc.cycles.samples, sc.render.filepath, sc.render.image_settings.file_format)
sc.camera = ECAM; sc.render.resolution_x, sc.render.resolution_y = 600, 450; sc.cycles.samples = 48
EVP = os.path.join(os.path.dirname(OUT), "evidence_liver.png"); sc.render.filepath = EVP; sc.render.image_settings.file_format = 'PNG'
bpy.ops.render.render(write_still=True)
sc.camera, sc.render.resolution_x, sc.render.resolution_y, sc.cycles.samples, sc.render.filepath, sc.render.image_settings.file_format = old
for o, h in hidden: o.hide_render = h
bpy.data.objects.remove(ECAM, do_unlink=True)
img = bpy.data.images.load(EVP); img.pack()
scr = O["HEAR_Screen"]
em = bpy.data.materials.new("M_EvidenceScreen"); em.use_nodes = True; nt = em.node_tree; N = nt.nodes; Lk = nt.links
N.remove(N["Principled BSDF"]); outn = N["Material Output"]
tc = N.new("ShaderNodeTexCoord"); sep = N.new("ShaderNodeSeparateXYZ"); Lk.new(tc.outputs["Generated"], sep.inputs[0])
# three photos side by side: u in [0,1] -> tile index and local u; a thin dark gap between tiles
mul = N.new("ShaderNodeMath"); mul.operation = 'MULTIPLY'; mul.inputs[1].default_value = 3.0; Lk.new(sep.outputs["X"], mul.inputs[0])
frc = N.new("ShaderNodeMath"); frc.operation = 'FRACT'; Lk.new(mul.outputs[0], frc.inputs[0])
flo = N.new("ShaderNodeMath"); flo.operation = 'FLOOR'; Lk.new(mul.outputs[0], flo.inputs[0])
# generated Y on the thin screen box runs along its depth for some faces; use Z for the vertical
cmb = N.new("ShaderNodeCombineXYZ")
su = N.new("ShaderNodeMapRange"); su.inputs[1].default_value = 0.04; su.inputs[2].default_value = 0.96; Lk.new(frc.outputs[0], su.inputs[0]); Lk.new(su.outputs[0], cmb.inputs[0])
sv = N.new("ShaderNodeMapRange"); sv.inputs[1].default_value = 0.08; sv.inputs[2].default_value = 0.92; Lk.new(sep.outputs["Z"], sv.inputs[0]); Lk.new(sv.outputs[0], cmb.inputs[1])
tx = N.new("ShaderNodeTexImage"); tx.image = img; tx.extension = 'CLIP'; Lk.new(cmb.outputs[0], tx.inputs[0])
hue = N.new("ShaderNodeHueSaturation"); Lk.new(tx.outputs["Color"], hue.inputs["Color"])
hm = N.new("ShaderNodeMath"); hm.operation = 'MULTIPLY_ADD'; hm.inputs[1].default_value = 0.025; hm.inputs[2].default_value = 0.475; Lk.new(flo.outputs[0], hm.inputs[0]); Lk.new(hm.outputs[0], hue.inputs["Hue"])
em_ = N.new("ShaderNodeEmission"); em_.inputs["Strength"].default_value = 1.6; Lk.new(hue.outputs["Color"], em_.inputs["Color"])
Lk.new(em_.outputs[0], outn.inputs["Surface"])
scr.data.materials.clear(); scr.data.materials.append(em)
log("evidence image", EVP)

# ================================================================== the camera: ONE camera, one continuous move (whips at the hub between rooms)
fs(300); FACE1 = Wh(DOC, "head") + Vector((0, 0, 0.05))
fs(1140); FACE2 = Wh(DOC2, "head") + Vector((0, 0, 0.05))
def L2(v): return sectM("OR2") @ Vector(v)
def LH(v): return sect("HOME", v)
def LR(v): return sect("HEAR", v)
F2 = sectM("OR2") @ (FACE2 if False else FACE2)
FACE2W = FACE2  # already world (her rig is placed in OR2)
LETC = Vector((LET_C.x - WORK.x, LET_C.y - WORK.y, PS[0].z - WORK.z))
CK = [  # frame, camera position, aim, lens, f-stop
    (1,    WORK + LETC + Vector((0.05, -0.30, 0.31)), WORK + LETC + Vector((0, 0.03, 0.0)), 45, 11),
    (34,   WORK + LETC + Vector((0.035, -0.24, 0.26)), WORK + LETC + Vector((0, 0.02, 0.0)), 48, 11),
    (62,   WORK + LETC + Vector((0.02, -0.19, 0.22)), WORK + LETC, 50, 11),
    (150,  WORK + LETC + Vector((-0.012, -0.17, 0.20)), WORK + LETC, 50, 11),
    (240,  WORK + LETC + Vector((0.0, -0.15, 0.185)), WORK + LETC, 52, 11),
    (270,  WORK + LETC + Vector((0.01, -0.20, 0.24)), WORK + LETC + Vector((0, 0.02, 0.01)), 50, 11),
    (305,  FACE1 + Vector((-0.10, -0.95, -0.16)), FACE1 + Vector((0, 0, -0.08)), 40, 8),
    (340,  FACE1 + Vector((0.16, -0.84, -0.20)), FACE1 + Vector((0, 0, -0.08)), 42, 8),
    (372,  FACE1 + Vector((0.0, -0.74, -0.26)), FACE1 + Vector((0, 0, -0.08)), 45, 8),
    (405,  FACE1 + Vector((-0.17, -0.80, -0.20)), FACE1 + Vector((0, 0, -0.08)), 45, 8),
    (445,  WORK + Vector((0.10, -0.42, 0.42)), WORK + Vector((0, 0.12, 0.10)), 35, 11),
    (480,  FACE1 + Vector((0.10, -0.85, -0.12)), FACE1 + Vector((0, 0, -0.10)), 40, 8),
    (522,  FACE1 + Vector((-0.06, -0.70, -0.08)), FACE1 + Vector((0, 0, -0.07)), 42, 8),
    (560,  FACE1 + Vector((0.04, -0.85, -0.08)), FACE1 + Vector((0, 0, -0.08)), 40, 8),
    (590,  Vector((0.0, 0.30, 1.55)), Vector((0.0, 3.0, 1.45)), 32, 8),
    (606,  Vector((0.0, 0.02, 1.55)), LH((0.0, 3.0, 1.5)), 30, 8),
    (640,  LH((0.10, 2.40, 1.45)), LH((0.08, 4.6, 1.45)), 28, 8),
    (690,  LH((0.10, 2.95, 1.36)), LH((0.06, 4.5, 1.30)), 30, 8),
    (740,  LH((0.22, 3.30, 1.25)), LH((0.0, 4.5, 1.20)), 36, 8),
    (782,  LH((-0.18, 3.38, 1.24)), LH((0.0, 4.5, 1.18)), 38, 8),
    (814,  LH((0.0, 1.30, 1.5)), LH((0.0, 4.0, 1.32)), 30, 8),
    (836,  Vector((0.02, 0.0, 1.55)), LH((0.0, 3.0, 1.42)), 30, 8),
    (852,  Vector((0.0, -0.02, 1.55)), L2((0.0, 3.0, 1.40)), 32, 8),
    (905,  L2((-0.45, 1.40, 1.65)), L2((-0.15, 2.9, 1.25)), 32, 8),
    (965,  sectM("OR2") @ (WORK + Vector((-0.25, -0.90, 0.50))), sectM("OR2") @ (WORK + Vector((0, 0.25, 0.28))), 35, 8),
    (1030, sectM("OR2") @ (WORK + LETC + Vector((0.04, -0.30, 0.30))), sectM("OR2") @ (WORK + LETC + Vector((0, 0.02, 0.0))), 45, 11),
    (1056, sectM("OR2") @ (WORK + LETC + Vector((0.02, -0.19, 0.22))), sectM("OR2") @ (WORK + LETC), 50, 11),
    (1108, sectM("OR2") @ (WORK + LETC + Vector((-0.01, -0.16, 0.19))), sectM("OR2") @ (WORK + LETC), 52, 11),
    (1134, FACE2W + (sectM("OR2").to_3x3() @ Vector((-0.05, -0.85, -0.05))), FACE2W + Vector((0, 0, -0.05)), 45, 8),
    (1172, FACE2W + (sectM("OR2").to_3x3() @ Vector((0.06, -0.72, -0.05))), FACE2W + Vector((0, 0, -0.05)), 45, 8),
    (1198, Vector((0.0, -0.02, 1.55)), L2((0.0, 3.0, 1.45)), 32, 8),
    (1214, Vector((0.02, 0.0, 1.55)), LR((0.0, 3.0, 1.45)), 32, 8),
    (1262, LR((0.10, 2.30, 1.62)), LR((0.95, 3.66, 1.55)), 40, 8),
    (1322, LR((0.20, 2.75, 1.52)), LR((1.0, 3.64, 1.38)), 36, 8),
    (1372, LR((0.30, 2.95, 1.55)), LR((1.02, 3.66, 1.50)), 36, 8),
    (1426, LR((0.38, 3.08, 1.58)), LR((1.04, 3.68, 1.58)), 42, 8),
    (1440, LR((0.15, 3.05, 1.45)), LR((-1.05, 3.70, 1.18)), 35, 8),
    (1480, LR((-0.05, 3.30, 1.36)), LR((-1.10, 3.62, 1.08)), 35, 8),
    (1514, LR((-0.10, 3.26, 1.32)), LR((-1.05, 3.55, 1.02)), 35, 8),
    (1528, LR((0.18, 2.92, 1.50)), LR((1.05, 3.68, 1.50)), 36, 8),
    (1590, LR((0.26, 3.00, 1.48)), LR((1.05, 3.68, 1.48)), 40, 8),
    (END,  LR((0.30, 3.04, 1.47)), LR((1.05, 3.68, 1.47)), 42, 8),
]
cam_d = bpy.data.cameras.new("CAM_Film"); CAM = bpy.data.objects.new("CAM_Film", cam_d); sc.collection.objects.link(CAM); sc.camera = CAM
AIM = bpy.data.objects.new("CAM_Film_Aim", None); sc.collection.objects.link(AIM)
cam_d.sensor_fit = 'AUTO'; cam_d.sensor_width = 36; cam_d.clip_start = 0.02; cam_d.dof.use_dof = True; cam_d.dof.focus_object = AIM
yaws = []; prev = None
for f, p, a_, l_, fst in CK:
    d = a_ - p; yw = math.atan2(d.y, d.x)
    if prev is not None:
        while yw - prev > math.pi: yw -= 2 * math.pi
        while yw - prev < -math.pi: yw += 2 * math.pi
    yaws.append(yw); prev = yw
fx = pchip([(k[0], k[1].x) for k in CK]); fy = pchip([(k[0], k[1].y) for k in CK]); fz = pchip([(k[0], k[1].z) for k in CK])
fyaw = pchip([(k[0], yaws[i]) for i, k in enumerate(CK)])
fpit = pchip([(k[0], math.atan2((k[2] - k[1]).z, (k[2] - k[1]).to_2d().length)) for k in CK])
fdis = pchip([(k[0], (k[2] - k[1]).length) for k in CK]); flen = pchip([(k[0], k[3]) for k in CK]); fstp = pchip([(k[0], k[4]) for k in CK])
maxstep = 0.0; prev_y = None
for f in range(1, END + 1):
    p = Vector((fx(f), fy(f), fz(f))); yw = fyaw(f); pt = fpit(f); ds = fdis(f)
    dvec = Vector((math.cos(yw) * math.cos(pt), math.sin(yw) * math.cos(pt), math.sin(pt)))
    CAM.location = p; CAM.rotation_euler = (math.pi / 2 + pt, 0, yw - math.pi / 2)
    CAM.keyframe_insert("location", frame=f); CAM.keyframe_insert("rotation_euler", frame=f)
    AIM.location = p + dvec * ds; AIM.keyframe_insert("location", frame=f)
    cam_d.lens = flen(f); cam_d.keyframe_insert("lens", frame=f)
    cam_d.dof.aperture_fstop = fstp(f); cam_d.dof.keyframe_insert("aperture_fstop", frame=f)
    if prev_y is not None: maxstep = max(maxstep, abs(math.degrees(yw - prev_y)))
    prev_y = yw
log("camera keyed; max yaw step deg/frame", round(maxstep, 1))

# ================================================================== VO, output, quaternion continuity, pack
try:
    se = sc.sequence_editor_create()
    vo = os.path.join(HERE, "..", "SurgeonBrandsLivers_v015_VO.mp3")
    coll = se.strips if hasattr(se, "strips") else se.sequences
    st = coll.new_sound("VO", os.path.abspath(vo), channel=1, frame_start=1)
    log("VO strip", st.frame_final_start, st.frame_final_end)
except Exception as e:
    log("vo strip failed", e)
def quat_continuity(obj):
    groups = {}
    if not obj.animation_data or not obj.animation_data.action: return 0
    for fc in iter_fcurves(obj.animation_data.action):
        if fc.data_path.endswith("rotation_quaternion"): groups.setdefault(fc.data_path, {})[fc.array_index] = fc
    nfix = 0
    for dp, ch in groups.items():
        if len(ch) != 4: continue
        frames = sorted({kp.co.x for kp in ch[0].keyframe_points})
        idx = [{kp.co.x: kp for kp in ch[i].keyframe_points} for i in range(4)]
        prev = None
        for fr in frames:
            kps = [idx[i].get(fr) for i in range(4)]
            if any(k is None for k in kps): continue
            q = Quaternion([k.co.y for k in kps])
            if prev is not None and prev.dot(q) < 0:
                for k in kps:
                    k.co.y = -k.co.y; k.handle_left.y = -k.handle_left.y; k.handle_right.y = -k.handle_right.y
                q = -q; nfix += 1
            prev = q
        for c_ in ch.values(): c_.update()
    return nfix
log("quat flips fixed", [quat_continuity(r) for r in (PAT, DOC, DOC2, JUD)])
log("tool tip err max mm", max(e for *_, e in ERR) if ERR else None)
for w_ in WANG:
    if max(abs(x) for x in w_[2]) > 58: log("WRIST", w_)
for o in O:
    for m in getattr(o, "modifiers", []):
        if m.type == 'SUBSURF': m.show_viewport = True
sc.frame_start, sc.frame_end = 1, END
sc.render.filepath = "//render/SurgeonBrandsLivers_v015_####.png"; sc.render.image_settings.file_format = 'PNG'
sc.render.image_settings.color_mode = 'RGB'; sc.render.image_settings.compression = 15
sc.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
open(OUT + ".log.txt", "w").write("\n".join(LOG))
print("ANIM_OK", OUT)
