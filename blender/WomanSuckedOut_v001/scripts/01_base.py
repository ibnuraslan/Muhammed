"""B13 WomanSuckedOut, base set.
blender -b NoPilotPlane_v011_60fps.blend --python 01_base.py -- <build_dir>
Keeps the NoPilotPlane cabin, seats, passengers and sky; drops its cockpit crew and props; appends the three heroes;
cuts the broken window; builds the airliner exterior (fuselage, wings, engines with fan, tail with logo)."""
import bpy, bmesh, math, os, sys, random
from mathutils import Vector, Matrix
R_ = math.radians
BUILD = sys.argv[sys.argv.index("--") + 1]
HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.abspath(HERE + "/../../..")
TEX = BUILD + "/../tex"
sc = bpy.context.scene; D = bpy.data

def coll(name, parent=None):
    c = D.collections.get(name) or D.collections.new(name)
    if c.name not in [x.name for x in (parent or sc.collection).children]: (parent or sc.collection).children.link(c)
    return c
def kill(o):
    for c in list(o.children_recursive): D.objects.remove(c, do_unlink=True)
    D.objects.remove(o, do_unlink=True)

# ------------------------------------------------------------------ strip the old film
for n in ("HUMANS", "UNIFORM", "LOOSE", "BIRDS", "TOWNS"):
    c = D.collections.get(n)
    if c:
        for o in list(c.objects): D.objects.remove(o, do_unlink=True)
for n in ("WING_L", "WING_R", "CAM_Film"):
    if n in D.objects: D.objects.remove(D.objects[n], do_unlink=True)
for o in D.objects: o.animation_data_clear()
for o in D.objects:
    if o.type in ('MESH', 'LIGHT', 'CAMERA') and o.data and getattr(o.data, "animation_data", None): o.data.animation_data_clear()
for m in D.materials:
    if m.node_tree and m.node_tree.animation_data: m.node_tree.animation_data_clear()
if sc.world.node_tree and sc.world.node_tree.animation_data: sc.world.node_tree.animation_data_clear()
sc.timeline_markers.clear()
# passengers: drop the skin-tight sport-suit variant (reads as a mannequin) and the hero row (row 5 left) + HB's seat (6L0)
for a in [o for o in D.collections["PASSENGERS"].objects if o.type == 'ARMATURE']:
    nm = a.name
    if nm.startswith("PE") or nm.endswith("05L0") or nm.endswith("05L1") or nm.endswith("06L0") or nm.endswith("06L1"):
        kill(a)
for o in list(D.collections["PASSENGERS"].objects):
    if o.type == 'MESH' and o.parent is None: D.objects.remove(o, do_unlink=True)
# the base names (PA..PF without suffix) sit in row 1; row1 L seats: PA (1L0) PB (1L1)
print("PASSENGERS left", len([o for o in D.collections["PASSENGERS"].objects if o.type == 'ARMATURE']))
for l in ("L_alarm", "L_alarm_cabin", "L_panel_glow", "L_catch", "L_face_fill", "L_cockpit_softbox", "L_floor_fill", "L_galley_door_fill"):
    if l in D.objects: D.objects.remove(D.objects[l], do_unlink=True)

# ------------------------------------------------------------------ heroes
cH = coll("HEROES")
def append_rig(path, rig, newname):
    with D.libraries.load(path, link=False) as (fd, td):
        td.objects = list(fd.objects)
    root = None
    for o in td.objects:
        if o and o.type == 'ARMATURE' and o.name.split(".")[0] == rig and o.children: root = o
    keep = {root} | set(root.children_recursive)
    for o in td.objects:
        if o and o not in keep: D.objects.remove(o, do_unlink=True)
    for o in keep:
        cH.objects.link(o); o.hide_render = False; o.hide_viewport = False
        o.animation_data_clear()
    for o in list(root.children_recursive):
        o.name = newname + "." + o.name.split(".")[1] if "." in o.name else newname + "_" + o.name
    root.name = newname
    for pb in root.pose.bones:
        pb.rotation_mode = 'QUATERNION'; pb.location = (0, 0, 0); pb.rotation_quaternion = (1, 0, 0, 0); pb.scale = (1, 1, 1)
    for c in root.constraints: root.constraints.remove(c)
    root.location = (0, 0, 0); root.rotation_euler = (0, 0, 0); root.parent = None
    return root
W = append_rig(REPO + "/blender/CaveRescue_v010/CaveRescue_v010_60fps.blend", "Crowd1", "W")
HA = append_rig(REPO + "/blender/ShoeBomber_v008/ShoeBomber_v008_60fps.blend", "PaxB", "HA")
HB = append_rig(REPO + "/blender/BelugaRescue_v008/BelugaRescue_v008_60fps.blend", "SpecD", "HB")
STD = ("body", "eyebrow", "eyelash", "high-poly", "suit", "shoes", "teeth", "tongue", "bob", "short", "afro", "ponytail", "Body")
for r in (W, HA, HB):          # drop every extra the source film hung on the rig (cutaway layers, lights, props)
    for o in list(r.children_recursive):
        if o.type != 'MESH' or o.parent != r or not any(k in o.name for k in STD):
            print("DROP", o.name); D.objects.remove(o, do_unlink=True)
    for o in r.children:
        for m in list(o.modifiers):
            if m.type in ('WARP', 'WAVE', 'DISPLACE', 'NODES', 'SHRINKWRAP', 'SMOOTH'): print("DROPMOD", o.name, m.type); o.modifiers.remove(m)
        if o.data.shape_keys: print("SHAPEKEYS", o.name, [k.name for k in o.data.shape_keys.key_blocks][:6])

def retex(rig, key, png):
    for c in rig.children:
        if key in c.name:
            for m in c.data.materials:
                for n in m.node_tree.nodes:
                    if n.type == 'TEX_IMAGE' and n.image and "diffuse" in n.image.name.lower():
                        im = D.images.load(png); im.name = os.path.basename(png); n.image = im
                        print("RETEX", c.name, "->", im.name)
retex(W, "casualsuit01", TEX + "/W_outfit_diffuse.png")
for c in W.children:            # Crowd3's suit had a flat red base colour; drive it from the (recoloured) texture chain again
    if "casualsuit01" in c.name:
        for m in c.data.materials:
            nt = m.node_tree; hs = next((n for n in nt.nodes if n.type == 'HUE_SAT'), None); pr = nt.nodes.get("Principled BSDF")
            if hs and pr and not pr.inputs["Base Color"].is_linked: nt.links.new(hs.outputs[0], pr.inputs["Base Color"]); print("W suit relinked")
retex(HB, "casualsuit02", TEX + "/HB_sweater_diffuse.png")
for c in W.children:
    if any(k in c.name for k in ("ponytail", "bob")):
        for m in c.data.materials:
            nt = m.node_tree; pr = nt.nodes.get("Principled BSDF"); l = [x for x in nt.links if x.to_node == pr and x.to_socket.name == "Base Color"]
            if l:
                mu = nt.nodes.new("ShaderNodeMix"); mu.data_type = 'RGBA'; mu.blend_type = 'MULTIPLY'; mu.inputs["Factor"].default_value = 1.0
                mu.inputs["B"].default_value = (0.32, 0.24, 0.18, 1); nt.links.new(l[0].from_socket, mu.inputs["A"]); nt.links.new(mu.outputs["Result"], pr.inputs["Base Color"])
                print("W hair darkened", c.name)
# eye fix on every EnhancedEye group that lacks it
for g in list(D.node_groups):
    if g.name.startswith("EnhancedEye") and "CorneaTransparentMix" not in g.nodes:
        src = open(HERE + "/eye_fix.py").read().replace('D_GROUP = None', '').replace('bpy.data.node_groups["EnhancedEye"]', 'bpy.data.node_groups["%s"]' % g.name)
        _NO_SAVE = True; exec(src, {"bpy": bpy, "sys": sys, "_NO_SAVE": True})
# open elbows for every hero (MPFB rest elbow ~46 deg) and hand limits
exec(open(REPO + "/blender/pipeline/hand_poses.py").read())
for r in (W, HA, HB):
    if not any(c.type == 'LIMIT_ROTATION' for c in r.pose.bones["wrist.L"].constraints): add_hand_limits(r)
    for s in "LR":
        lo = r.pose.bones["lowerarm01." + s]; lo.use_ik_limit_x = True; lo.ik_min_x = R_(-40); lo.ik_max_x = R_(145)
    print("RIG", r.name, "IK", "IK_hand.L" in r.pose.bones, "height", round(max((r.matrix_world @ v.co).z for v in next(c for c in r.children if c.name.endswith(".body")).data.vertices), 3))

# ------------------------------------------------------------------ materials
def mat(name, col, rough=0.4, metal=0.0, emit=None, estr=0.0, alpha=None):
    m = D.materials.get(name) or D.materials.new(name); m.use_nodes = True; p = m.node_tree.nodes["Principled BSDF"]
    p.inputs["Base Color"].default_value = (*col, 1); p.inputs["Roughness"].default_value = rough; p.inputs["Metallic"].default_value = metal
    if emit: p.inputs["Emission Color"].default_value = (*emit, 1); p.inputs["Emission Strength"].default_value = estr
    return m
M_paint = mat("X_paint_white", (0.86, 0.87, 0.89), 0.32)
M_belly = mat("X_paint_grey", (0.56, 0.58, 0.62), 0.38)
M_tail = mat("X_paint_blue", (0.06, 0.22, 0.62), 0.35)
M_wing = mat("X_wing", (0.42, 0.45, 0.50), 0.4, 0.2)
M_cowl = mat("X_cowl", (0.88, 0.89, 0.91), 0.3)
M_cowl_in = mat("X_cowl_inner", (0.20, 0.21, 0.23), 0.45, 0.4)
M_fan = mat("X_fan_blade", (0.32, 0.34, 0.37), 0.3, 0.8)
M_spin = mat("X_spinner", (0.10, 0.10, 0.11), 0.3, 0.5)
M_dark = mat("X_dark", (0.03, 0.035, 0.04), 0.25)
M_frame = mat("X_win_frame", (0.70, 0.70, 0.68), 0.45)
M_glass = mat("X_glass", (0.25, 0.32, 0.38), 0.08, 0.0)
M_debris = mat("X_debris", (0.80, 0.81, 0.83), 0.35, 0.3)
M_smoke = mat("X_smoke", (0.58, 0.58, 0.60), 0.9)

def window_paint(m, base_sock_col, gate_y=(-6.0, -5.2)):
    """skin paint + dark rounded windows every 0.81 m on both sides at z 1.2 (object coords), white above z 0.3, grey below"""
    nt = m.node_tree; N, L = nt.nodes, nt.links; p = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord"); sp = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs["Object"], sp.inputs[0])
    def M(op, a, b=None):
        n = N.new("ShaderNodeMath"); n.operation = op
        for i, x in enumerate((a, b)):
            if x is None: continue
            if isinstance(x, (int, float)): n.inputs[i].default_value = x
            else: L.new(x, n.inputs[i])
        return n.outputs[0]
    X, Y, Z = sp.outputs[0], sp.outputs[1], sp.outputs[2]
    u = M("SUBTRACT", M("FRACT", M("ADD", M("DIVIDE", M("SUBTRACT", Y, -2.6), 0.81), 0.5)), 0.5)
    dy = M("DIVIDE", M("ABSOLUTE", M("MULTIPLY", u, 0.81)), 0.13); dz = M("DIVIDE", M("ABSOLUTE", M("SUBTRACT", Z, 1.2)), 0.19)
    e = M("ADD", M("POWER", dy, 4.0), M("POWER", dz, 4.0))
    gate = M("MULTIPLY", M("MULTIPLY", M("GREATER_THAN", Y, -13.4), M("LESS_THAN", Y, -2.0)), M("GREATER_THAN", M("ABSOLUTE", X), 0.9))
    gate = M("MULTIPLY", gate, M("SUBTRACT", 1.0, M("MULTIPLY", M("GREATER_THAN", Y, gate_y[0]), M("LESS_THAN", Y, gate_y[1]))))
    win = M("MULTIPLY", M("LESS_THAN", e, 1.0), gate)
    # cockpit windscreen band
    ws = M("MULTIPLY", M("MULTIPLY", M("GREATER_THAN", Y, 3.35), M("LESS_THAN", Y, 4.35)), M("MULTIPLY", M("GREATER_THAN", Z, 1.35), M("LESS_THAN", Z, 1.85)))
    ws = M("MULTIPLY", ws, M("GREATER_THAN", M("ABSOLUTE", X), 0.05))
    dark = M("MINIMUM", M("ADD", win, ws), 1.0)
    belly = M("LESS_THAN", Z, 0.25)
    mc = N.new("ShaderNodeMix"); mc.data_type = 'RGBA'; L.new(belly, mc.inputs["Factor"])
    mc.inputs["A"].default_value = (0.80, 0.81, 0.83, 1); mc.inputs["B"].default_value = (0.40, 0.42, 0.47, 1)
    mw = N.new("ShaderNodeMix"); mw.data_type = 'RGBA'; L.new(dark, mw.inputs["Factor"]); L.new(mc.outputs["Result"], mw.inputs["A"])
    mw.inputs["B"].default_value = (0.02, 0.025, 0.03, 1)
    L.new(mw.outputs["Result"], p.inputs["Base Color"])
    rr = N.new("ShaderNodeMapRange"); L.new(dark, rr.inputs[0]); rr.inputs[3].default_value = 0.32; rr.inputs[4].default_value = 0.08
    L.new(rr.outputs[0], p.inputs["Roughness"])
window_paint(M_paint, None)

cX = coll("EXT_PLANE")
def new_obj(name, bm, m_list, c=cX, smooth=True):
    me = D.meshes.new(name); bm.to_mesh(me); bm.free()
    for mm in m_list: me.materials.append(mm)
    if smooth:
        for p in me.polygons: p.use_smooth = True
    o = D.objects.new(name, me); c.objects.link(o); return o

def lathe_rings(rings, seg=64, cap0=True, cap1=True):
    """rings: list of (y, r, zc[, rx]) -> closed tube along -y"""
    bm = bmesh.new(); prev = None; first = None; last = None
    for r_ in rings:
        y, r, zc = r_[0], r_[1], r_[2]; rx = r_[3] if len(r_) > 3 else r
        ring = [bm.verts.new((rx * math.cos(2 * math.pi * k / seg), y, zc + r * math.sin(2 * math.pi * k / seg))) for k in range(seg)]
        if prev:
            for k in range(seg): bm.faces.new((prev[k], prev[(k + 1) % seg], ring[(k + 1) % seg], ring[k]))
        else: first = ring
        prev = ring
    if cap0: bm.faces.new(list(reversed(first)))
    if cap1: bm.faces.new(prev)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm

# ---- fuselage
FR = [(5.25, 0.04, 0.55), (5.05, 0.42, 0.62), (4.75, 0.78, 0.70), (4.3, 1.08, 0.80), (3.6, 1.36, 0.90), (2.8, 1.52, 0.95), (2.0, 1.56, 0.95)]
FR += [(y, 1.56, 0.95) for y in (0.0, -3.0, -6.0, -9.0, -12.0, -14.0)]
FR += [(-15.5, 1.44, 1.05), (-17.0, 1.18, 1.25), (-18.5, 0.86, 1.48), (-20.0, 0.52, 1.70), (-21.2, 0.22, 1.86), (-21.6, 0.04, 1.9)]
fus = new_obj("FUSELAGE", lathe_rings(FR, seg=72), [M_paint])
# ---- the broken window: one rounded cutter through skin, cabin shell and wall trim
HOLE = Vector((-1.45, -5.58, 1.20)); HW, HH = 0.46, 0.56
bpy.ops.mesh.primitive_cube_add(size=1, location=HOLE)
cut = bpy.context.active_object; cut.name = "HOLE_CUTTER"; cut.scale = (1.0, HW, HH)
bpy.ops.object.transform_apply(scale=True)
bv = cut.modifiers.new("bv", 'BEVEL'); bv.width = 0.13; bv.segments = 8; bv.affect = 'EDGES'
bpy.context.view_layer.objects.active = cut; bpy.ops.object.modifier_apply(modifier="bv")
for tname in ("FUSELAGE", "CABIN_SHELL", "CABIN_FIXED"):
    t = D.objects[tname]; bo = t.modifiers.new("hole", 'BOOLEAN'); bo.object = cut; bo.operation = 'DIFFERENCE'; bo.solver = 'EXACT'
    bpy.context.view_layer.objects.active = t; bpy.ops.object.modifier_apply(modifier="hole")
    print("HOLE cut", tname, len(t.data.polygons))
# tunnel liner between cabin wall and skin (rounded rect, normals inward), and a trim ring on the cabin side
def rrect(w, h, r, n=8):
    pts = []
    for cy_, cz_, a0 in ((w / 2 - r, h / 2 - r, 0), (-(w / 2 - r), h / 2 - r, 90), (-(w / 2 - r), -(h / 2 - r), 180), (w / 2 - r, -(h / 2 - r), 270)):
        for k in range(n + 1):
            a = R_(a0 + 90 * k / n); pts.append((cy_ + r * math.cos(a), cz_ + r * math.sin(a)))
    return pts
def tube_rr(name, x0, x1, w, h, r, m, inward=True):
    bm = bmesh.new(); P = rrect(w, h, r)
    A = [bm.verts.new((x0, HOLE.y + p[0], HOLE.z + p[1])) for p in P]; B = [bm.verts.new((x1, HOLE.y + p[0], HOLE.z + p[1])) for p in P]
    for k in range(len(P)):
        f = bm.faces.new((A[k], A[(k + 1) % len(P)], B[(k + 1) % len(P)], B[k]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    if inward:
        c = Vector(((x0 + x1) / 2, HOLE.y, HOLE.z))
        for f in bm.faces:
            if (f.calc_center_median() - c).dot(f.normal) > 0: f.normal_flip()
    return new_obj(name, bm, [m])
tube_rr("HOLE_LINER", -1.25, -1.60, HW - 0.004, HH - 0.004, 0.125, M_frame)
# cabin-side trim frame: flat ring 0.09 wide around the hole on the wall (covers the old painted window edge)
bm = bmesh.new(); Pi = rrect(HW, HH, 0.125); Po = rrect(HW + 0.22, HH + 0.24, 0.2)
xw = -1.385
I = [bm.verts.new((xw, HOLE.y + p[0], HOLE.z + p[1])) for p in Pi]; O = [bm.verts.new((xw + 0.02, HOLE.y + p[0], HOLE.z + p[1])) for p in Po]
for k in range(len(Pi)): bm.faces.new((I[k], I[(k + 1) % len(Pi)], O[(k + 1) % len(Pi)], O[k]))
trim = new_obj("HOLE_TRIM", bm, [M_frame], c=D.collections["SET"])
# the trim must follow the curved wall: shrink-wrap onto the cabin shell from inside
sw = trim.modifiers.new("sw", 'SHRINKWRAP'); sw.target = D.objects["CABIN_SHELL"]; sw.wrap_method = 'PROJECT'; sw.use_project_x = True
sw.use_negative_direction = True; sw.use_positive_direction = True; sw.offset = 0.012
D.objects.remove(cut, do_unlink=True)
# window pane (exterior, breaks in S07) and shards
pane_bm = bmesh.new(); Pp = rrect(HW - 0.03, HH - 0.03, 0.11)
vv = [pane_bm.verts.new((-1.555, HOLE.y + p[0], HOLE.z + p[1])) for p in Pp]; pane_bm.faces.new(vv)
pane = new_obj("PANE", pane_bm, [M_glass], smooth=False)
rnd = random.Random(13)
for i in range(22):
    bm = bmesh.new(); s_ = rnd.uniform(0.04, 0.09)
    a = [bm.verts.new((0, rnd.uniform(-s_, s_), rnd.uniform(-s_, s_))) for _ in range(3)]; bm.faces.new(a)
    o = new_obj("SHARD_%02d" % i, bm, [M_glass], smooth=False); o["home"] = (-1.56, HOLE.y + rnd.uniform(-0.18, 0.18), HOLE.z + rnd.uniform(-0.22, 0.22))
    sol = o.modifiers.new("s", 'SOLIDIFY'); sol.thickness = 0.006

# ---- wings (low, swept, dihedral)
def wing(side):
    sx = -1 if side == "L" else 1
    st = [(1.2, -4.3, 4.3, -0.30, 0.48), (4.6, -5.6, 3.0, 0.05, 0.32), (13.5, -9.6, 1.35, 0.98, 0.13)]
    prof = [(0, 0), (0.02, 0.045), (0.08, 0.075), (0.2, 0.09), (0.4, 0.08), (0.65, 0.05), (0.88, 0.02), (1.0, 0.0)]
    bm = bmesh.new(); rings = []
    for x, le, ch, z, th in st:
        up = [(le - c * ch, z + t * th / 0.09 * 0.5 * 1.0) for c, t in prof]
        lo = [(le - c * ch, z - t * th / 0.09 * 0.5 * 0.6) for c, t in reversed(prof[1:-1])]
        rings.append([bm.verts.new((sx * x, y_, z_)) for y_, z_ in up + lo])
    n = len(rings[0])
    for a_, b_ in zip(rings, rings[1:]):
        for k in range(n): bm.faces.new((a_[k], a_[(k + 1) % n], b_[(k + 1) % n], b_[k]))
    bm.faces.new(rings[-1]); bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = new_obj("WINGX_" + side, bm, [M_wing])
    # winglet
    bm = bmesh.new(); x, le, ch, z, th = st[-1]
    q = [bm.verts.new(v) for v in ((sx * x, le, z), (sx * x, le - ch, z), (sx * (x + 0.25), le - ch - 0.5, z + 1.6), (sx * (x + 0.25), le - 0.75, z + 1.6))]
    bm.faces.new(q); o2 = new_obj("WINGLET_" + side, bm, [M_tail], smooth=False)
    s2 = o2.modifiers.new("s", 'SOLIDIFY'); s2.thickness = 0.08
    return o
wing("L"); wing("R")

# ---- engines: nacelle (lathe), inner duct, fan (spinner + 18 blades) on a rotating empty, pylon
ENG = {}
def engine(side, broken_arc=False):
    sx = -1 if side == "L" else 1
    cx, cz, y0 = sx * 4.5, -0.92, -2.15
    seg = 64
    outer = [(y0, 0.80), (y0 - 0.12, 0.86), (y0 - 0.6, 0.90), (y0 - 1.6, 0.88), (y0 - 2.8, 0.74), (y0 - 3.4, 0.62)]
    inner = [(y0 - 0.04, 0.72), (y0 - 0.5, 0.72), (y0 - 3.4, 0.55)]
    def ring_mesh(prof_o, prof_i, a0, a1, name, mats):
        bm = bmesh.new(); kk = int(round(seg * (a1 - a0) / 360)) + 1
        def mk(prof):
            return [[bm.verts.new((cx + r * math.cos(R_(a0 + (a1 - a0) * k / (kk - 1))), y, cz + r * math.sin(R_(a0 + (a1 - a0) * k / (kk - 1))))) for k in range(kk)] for y, r in prof]
        O = mk(prof_o); I = mk(prof_i)
        lip = O[0]; ilip = I[0]
        full = (a1 - a0) >= 359.9
        for rows, mi in ((O, 0), (I, 1)):
            for ra, rb in zip(rows, rows[1:]):
                for k in range(kk - (0 if full else 1)):
                    k2 = (k + 1) % kk if full else k + 1
                    if full and k2 == 0: continue
                    f = bm.faces.new((ra[k], ra[k2], rb[k2], rb[k])); f.material_index = mi
        for k in range(kk - 1):
            f = bm.faces.new((lip[k], lip[k + 1], ilip[k + 1], ilip[k])); f.material_index = 0
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        return new_obj(name, bm, mats)
    if broken_arc:
        # inboard-upper arc of the inlet is a separate piece (it breaks away in S06)
        main = ring_mesh(outer, inner, 75, 360 - 15, "NACELLE_" + side, [M_cowl, M_cowl_in])
        arc = ring_mesh(outer[:3], inner[:2], -15, 75, "NACELLE_ARC_" + side, [M_cowl, M_cowl_in])
        # the remaining aft part of the arc (behind the break) stays
        rest = ring_mesh(outer[2:], [(outer[2][0], 0.72)] + inner[2:], -15, 75, "NACELLE_ARCREST_" + side, [M_cowl, M_cowl_in])
        # jagged break edge: dark lining strip
        ENG["arc"] = arc
    else:
        ring_mesh(outer, inner, 0, 360, "NACELLE_" + side, [M_cowl, M_cowl_in])
    # exhaust plug
    bm = lathe_rings([(y0 - 3.3, 0.5, cz), (y0 - 3.9, 0.32, cz), (y0 - 4.3, 0.05, cz)], seg=32, cap0=True, cap1=False)
    for v in bm.verts: v.co.x += cx
    new_obj("PLUG_" + side, bm, [M_cowl_in])
    # back plate (hides the empty duct)
    bm = bmesh.new(); bmesh.ops.create_circle(bm, cap_ends=True, segments=48, radius=0.70)
    for v in bm.verts: v.co = Vector((cx + v.co.x, y0 - 0.95, cz + v.co.y))
    new_obj("FANBACK_" + side, bm, [M_dark], smooth=False)
    # fan
    fan = D.objects.new("FAN_" + side, None); cX.objects.link(fan); fan.location = (cx, y0 - 0.62, cz); fan.rotation_mode = 'XYZ'
    bm = lathe_rings([(0.32, 0.0, 0.0), (0.22, 0.10, 0.0), (0.05, 0.22, 0.0), (-0.12, 0.24, 0.0)], seg=32, cap0=False, cap1=True)
    sp = new_obj("SPINNER_" + side, bm, [M_spin]); sp.parent = fan
    # white swirl mark on spinner (simple stripe via second material on half the faces)
    blades = bmesh.new(); brk = bmesh.new()
    for k in range(18):
        a = 2 * math.pi * k / 18; b = brk if (k == 4 and broken_arc) else blades
        vs = []
        for r, tw, ch in ((0.23, 52, 0.17), (0.45, 42, 0.16), (0.70, 30, 0.13)):
            t = R_(tw)
            for c in (-0.5, 0.5):
                # blade chord in the (tangent, y) plane twisted by tw
                tang = Vector((-math.sin(a), 0, math.cos(a))); rad = Vector((math.cos(a), 0, math.sin(a)))
                p = rad * r + tang * (c * ch * math.cos(t)) + Vector((0, c * ch * math.sin(t), 0))
                vs.append(b.verts.new(p))
        for j in range(2):
            b.faces.new((vs[2 * j], vs[2 * j + 1], vs[2 * j + 3], vs[2 * j + 2]))
    bo = new_obj("BLADES_" + side, blades, [M_fan], smooth=False); bo.parent = fan
    so = bo.modifiers.new("s", 'SOLIDIFY'); so.thickness = 0.012
    if broken_arc:
        bb = new_obj("BLADE_BREAK_" + side, brk, [M_fan], smooth=False); bb.parent = fan
        so = bb.modifiers.new("s", 'SOLIDIFY'); so.thickness = 0.012; ENG["blade"] = bb
    # pylon
    bm = bmesh.new()
    q = [bm.verts.new(v) for v in ((cx, y0 - 0.9, cz + 0.82), (cx, y0 - 3.2, cz + 0.7), (cx, -6.9, cz + 1.05), (cx, y0 - 1.4, cz + 1.05))]
    bm.faces.new(q); py = new_obj("PYLON_" + side, bm, [M_cowl], smooth=False)
    s2 = py.modifiers.new("s", 'SOLIDIFY'); s2.thickness = 0.22; s2.offset = 0
    ENG["fan_" + side] = fan
engine("L", broken_arc=True); engine("R")

# ---- tail: fin (blue) + stabilizers, logo on the right side of the fin
def slab(name, pts, thick, m):
    bm = bmesh.new(); vs = [bm.verts.new(p) for p in pts]; bm.faces.new(vs)
    o = new_obj(name, bm, [m], smooth=False); s = o.modifiers.new("s", 'SOLIDIFY'); s.thickness = thick; s.offset = 0
    b = o.modifiers.new("b", 'BEVEL'); b.width = 0.03; b.segments = 3
    return o
slab("FIN", [(0, -15.6, 1.9), (0, -20.9, 2.1), (0, -22.6, 7.6), (0, -20.6, 7.6)], 0.28, M_tail)
for sx in (-1, 1):
    slab("STAB_%d" % sx, [(sx * 0.3, -18.4, 1.55), (sx * 0.3, -21.3, 1.6), (sx * 5.6, -22.6, 1.95), (sx * 5.6, -21.6, 1.95)], 0.16, M_paint)
logo = D.images.load(REPO + "/blender/assets/brand/DaKrasFilms_logo_white.png"); logo.name = "DaKrasFilms_logo_white"
lw = 3.0; lh = lw * 414 / 967
bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=0.5)
uv = bm.loops.layers.uv.new()
for f in bm.faces:
    for l in f.loops: l[uv].uv = (l.vert.co.x + 0.5, l.vert.co.y + 0.5)
lg = new_obj("LOGO_TAIL", bm, [], smooth=False)
lm = D.materials.new("LogoTail"); lm.use_nodes = True; nt = lm.node_tree; nt.nodes.clear()
o_ = nt.nodes.new("ShaderNodeOutputMaterial"); t_ = nt.nodes.new("ShaderNodeTexImage"); t_.image = logo; t_.extension = 'CLIP'
pr = nt.nodes.new("ShaderNodeBsdfPrincipled"); pr.inputs["Roughness"].default_value = 0.4
tr = nt.nodes.new("ShaderNodeBsdfTransparent"); mx = nt.nodes.new("ShaderNodeMixShader")
nt.links.new(t_.outputs["Color"], pr.inputs["Base Color"]); nt.links.new(t_.outputs["Alpha"], mx.inputs[0])
nt.links.new(tr.outputs[0], mx.inputs[1]); nt.links.new(pr.outputs[0], mx.inputs[2]); nt.links.new(mx.outputs[0], o_.inputs[0])
lg.data.materials.append(lm)
lg.scale = (lw, lh, 1); lg.rotation_euler = (R_(90), 0, R_(90)); lg.location = (0.16, -20.2, 4.35)
# fin leans back: shear the logo with the fin leading edge is not needed (flat decal on the flat fin side)

# ---- debris chunks (engine inlet pieces) and smoke puffs
rnd = random.Random(7)
for i in range(14):
    bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=1, radius=1.0)
    for v in bm.verts: v.co = Vector((v.co.x * rnd.uniform(0.5, 1.0), v.co.y * rnd.uniform(0.6, 1.0), v.co.z * rnd.uniform(0.2, 0.45)))
    s_ = rnd.uniform(0.05, 0.12) if i < 10 else rnd.uniform(0.03, 0.05)
    for v in bm.verts: v.co *= s_
    o = new_obj("DEBRIS_%02d" % i, bm, [M_debris if i % 3 else M_cowl_in], smooth=False)
for i in range(7):
    bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=3, radius=1.0)
    for v in bm.verts: v.co *= 1 + 0.18 * math.sin(v.co.x * 5 + i) * math.cos(v.co.z * 4 + i)
    new_obj("SMOKE_%d" % i, bm, [M_smoke])

# ---- set dressing in the cabin: paper napkins / magazines that fly to the hole (S08)
M_paper = mat("X_paper", (0.92, 0.92, 0.88), 0.7)
for i in range(6):
    bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=2, y_segments=2, size=0.07)
    o = new_obj("PAPER_%d" % i, bm, [M_paper], c=D.collections["SET"], smooth=False)
    s = o.modifiers.new("s", 'SOLIDIFY'); s.thickness = 0.002


# ---- sky: deeper blue overhead, bright near the horizon; puffy cloud clusters around the plane (they drift past in 02)
wn = sc.world.node_tree.nodes
for n in wn:            # director P1 note: deep blue sky, real sun key with shadows on the fuselage
    if n.type == 'VALTORGB':
        n.color_ramp.elements[0].color = (0.22, 0.48, 0.88, 1); n.color_ramp.elements[-1].color = (0.015, 0.14, 0.55, 1)
    if n.name == "Background": n.inputs["Color"].default_value = (0.35, 0.5, 0.75, 1); n.inputs["Strength"].default_value = 0.5
sun = D.objects["SUN"]; sun.data.energy = 6.5; sun.data.angle = R_(1.5)
sun.rotation_mode = 'XYZ'; sun.rotation_euler = Vector((0.6, -0.3, -0.75)).normalized().to_track_quat('-Z', 'Y').to_euler()
cC = coll("CLOUDS_NEAR")
M_cloud = mat("X_cloud", (0.95, 0.96, 0.98), 0.95)
M_cloud.node_tree.nodes["Principled BSDF"].inputs["Emission Color"].default_value = (0.9, 0.93, 1.0, 1)
M_cloud.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].default_value = 0.35
rnd = random.Random(21)
CL = [(-60, -20, 25), (-90, 30, -10), (-45, -60, -25), (-120, -10, 40), (-70, 60, 15), (70, -30, 20), (110, 10, -15), (60, -70, 35),
      (-30, -110, 10), (-100, -80, -30), (90, 60, 30), (-55, 10, -45), (40, 20, -40), (-150, 40, 5)]
for i, (x, y, z) in enumerate(CL):
    bm = bmesh.new()
    for j in range(9):
        r = rnd.uniform(5, 11); c = Vector((rnd.uniform(-14, 14), rnd.uniform(-10, 10), rnd.uniform(-3, 4)))
        g = bmesh.ops.create_icosphere(bm, subdivisions=2, radius=r)
        for v in g["verts"]: v.co = Vector((v.co.x * 1.4, v.co.y, v.co.z * 0.75)) + c
    o = new_obj("CLOUDN_%02d" % i, bm, [M_cloud], c=cC); o.location = (x, y, z)

for n in ("GROUND",):
    if n in D.objects: D.objects[n].hide_render = True; D.objects[n].hide_viewport = True
# exterior hidden by default (keyed per shot in 02)
for o in cX.objects: o.hide_render = False
print("EXT objects", len(cX.objects))
sc.frame_start = 1
bpy.ops.wm.save_as_mainfile(filepath=BUILD + "/base.blend")
print("BASE saved")
