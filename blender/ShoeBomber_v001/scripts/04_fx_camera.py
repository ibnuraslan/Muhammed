"""Props attached to hands/feet, effects, lights, grade, and the one continuous camera.
blender -b anim.blend --python 04_fx_camera.py -- <out_film.blend>"""
import sys, os, math, random
import bpy, bmesh
from mathutils import Vector, Matrix, Quaternion, Euler
HERE = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(HERE, "../../pipeline/anim_lib.py")).read())
sys.path.insert(0, HERE)
import sb_lib as L
OUT = sys.argv[sys.argv.index("--") + 1:][0]
V = Vector
random.seed(11)
sc = bpy.context.scene
END = 1620
O = bpy.data.objects
RIG = {n: O[n] for n in ["Bomber", "Attendant", "Steward", "PaxA", "PaxB", "PaxC", "PaxD", "Traveller", "Officer"]}
SXS = V((200, 0, 0)); KX = V((-2000, 0, 600)); AX = V((400, 0, 0))

def bone_w(rig, bone, f):
    sc.frame_set(f); return rig.matrix_world @ rig.pose.bones[bone].matrix

def constant_at(idb, frames, path_sub=None):
    ad = idb.animation_data
    if not ad or not ad.action: return
    for layer in ad.action.layers:
        for strip in layer.strips:
            for cb in strip.channelbags:
                for fc in cb.fcurves:
                    if path_sub and path_sub not in fc.data_path: continue
                    for kp in fc.keyframe_points:
                        if int(round(kp.co.x)) in frames: kp.interpolation = 'CONSTANT'

class Carry:
    """chain of Child Of constraints. hold(rig, bone, f, M_world) makes the object follow that bone from frame f on,
    starting at world matrix M_world (None = wherever it is at f). free(f, M) = static world matrix from f."""
    def __init__(self, ob):
        self.ob = ob; self.cons = []; ob.matrix_world = Matrix.Identity(4)
        ob.animation_data_clear()
        for c in list(ob.constraints): ob.constraints.remove(c)
    def _world(self, f):
        sc.frame_set(f); return self.ob.matrix_world.copy()
    def _switch(self, f, new):
        for c in self.cons:
            c.influence = 1.0 if c is new else 0.0
            c.keyframe_insert("influence", frame=f)
            c.influence = 1.0 if c is not new and c is self.cons[-1] and False else c.influence
    def hold(self, rig, bone, f, M=None):
        if M is None and self.cons:
            M = self._world(f - 1) if f > 1 else self._world(f)
        elif M is None:
            M = self.ob.matrix_world.copy()
        Bw = bone_w(rig, bone, f)
        c = self.ob.constraints.new('CHILD_OF'); c.target = rig; c.subtarget = bone
        c.set_inverse_pending = False
        c.inverse_matrix = (rig.matrix_world.inverted() @ Bw).inverted() @ rig.matrix_world.inverted() @ M if False else (Bw.inverted() @ M)
        c.use_scale_x = c.use_scale_y = c.use_scale_z = False
        # child-of composes: target_world @ inverse @ basis ; basis = identity
        if f > 1:
            c.influence = 0.0; c.keyframe_insert("influence", frame=f - 1)
        if self.cons:
            o_ = self.cons[-1]
            o_.influence = 1.0; o_.keyframe_insert("influence", frame=f - 1)
            o_.influence = 0.0; o_.keyframe_insert("influence", frame=f)
        c.influence = 1.0; c.keyframe_insert("influence", frame=f)
        self.cons.append(c)
        return c
    def free(self, f, M=None):
        """park at world matrix M (or current) from f: an 'empty' world-space hold"""
        if M is None: M = self._world(f - 1)
        emp = bpy.data.objects.get("Park_" + self.ob.name + "_%d" % f) or bpy.data.objects.new("Park_" + self.ob.name + "_%d" % f, None)
        if emp.name not in sc.collection.objects: sc.collection.objects.link(emp)
        emp.matrix_world = M; emp.hide_render = True
        c = self.ob.constraints.new('CHILD_OF'); c.target = emp; c.inverse_matrix = M.inverted() @ M if False else Matrix.Identity(4)
        c.inverse_matrix = Matrix.Identity(4)
        # target world @ I @ identity basis = M
        if self.cons:
            o_ = self.cons[-1]
            o_.influence = 1.0; o_.keyframe_insert("influence", frame=f - 1)
            o_.influence = 0.0; o_.keyframe_insert("influence", frame=f)
        c.influence = 0.0; c.keyframe_insert("influence", frame=f - 1); c.influence = 1.0; c.keyframe_insert("influence", frame=f)
        self.cons.append(c); return c
    def done(self):
        for c in self.cons:
            ad = self.ob.animation_data
        for layer in (self.ob.animation_data.action.layers if self.ob.animation_data and self.ob.animation_data.action else []):
            for strip in layer.strips:
                for cb in strip.channelbags:
                    for fc in cb.fcurves:
                        for kp in fc.keyframe_points: kp.interpolation = 'CONSTANT'

def shoe_on_foot(rig, s):
    """world matrix of a shoe (origin heel-bottom-centre, toe -Y) on the rig's foot at rest, as foot-bone-relative"""
    B = rig.data.bones["foot." + s]
    a = B.head_local
    Mrest = Matrix.Translation(V((a.x, a.y - 0.08, a.z - 0.095))) @ Matrix.Rotation(math.pi, 4, 'Z') @ Matrix.Scale(1.08, 4)   # origin = sole-bottom centre; model toe is +Y
    return B.matrix_local.inverted() @ Mrest          # offset in the foot bone's space

def attach_rest(ob, rig, bone, f, offset):
    """hold so that ob = bone_world @ offset at frame f"""
    return bone_w(rig, bone, f) @ offset

# ------------------------------------------------------------------ bomber's sneakers -> attendant's hands (beat 6)
bom, att, stw, trav = RIG["Bomber"], RIG["Attendant"], RIG["Steward"], RIG["Traveller"]
for s, hs in (("L", "L"), ("R", "R")):
    shoe = O["Shoe_" + s]
    offs = shoe_on_foot(bom, s)
    cr = Carry(shoe)
    cr.hold(bom, "foot." + s, 1, attach_rest(shoe, bom, "foot." + s, 1, offs))
    cr.hold(RIG["PaxB"], "wrist." + hs, 878)    # v006d: PaxB grasps the heel; the shoe leaves the foot with his hand
    cr.free(930)                                # set down on the carpet: released, then settles the last few cm (no pop)
    cr.done()
    park = bpy.data.objects["Park_%s_930" % shoe.name]; sc.frame_set(929)
    Mw = shoe.matrix_world.copy(); zmin = min((Mw @ V(c)).z for c in shoe.bound_box)
    park.keyframe_insert("location", frame=930)
    park.location = park.location - V((0, 0, max(0.0, zmin - 0.003))); park.keyframe_insert("location", frame=938)
    # traveller's pair
    ts = O["Shoe_%s_Trav" % s]
    ct = Carry(ts)
    offs_t = shoe_on_foot(trav, s)
    ct.hold(trav, "foot." + s, 1, attach_rest(ts, trav, "foot." + s, 1, offs_t))
    if s == "R":
        ct.free(1441)                          # he steps out of it: it stays on the floor
        sc.frame_set(1477); Mpick = ts.matrix_world.copy()
        cpk = ct.hold(trav, "finger3-3.R", 1478)   # picked up by the collar
        # v006e: follow the fingertips' position only (the wrist's IK twist swung the sneaker round his head); it hangs from the fingers
        cpk.use_rotation_x = cpk.use_rotation_y = cpk.use_rotation_z = False
        cpk.inverse_matrix = Matrix.Translation(-bone_w(trav, "finger3-3.R", 1478).translation) @ Mpick
        print("PICK_GAP", (bone_w(trav, "finger3-3.R", 1478).translation - Mpick.translation))
        tray = O["Tray_1"]
        ct.hold_tray = True
        # into the tray at 1520: then rides with the tray (tray is an object: use a park-at-tray Child Of)
        Mt = None
        sc.frame_set(1519); M = ts.matrix_world.copy()
        sc.frame_set(1521); Mtr = tray.matrix_world.copy()
        c = ts.constraints.new('CHILD_OF'); c.target = tray
        Mdrop = Matrix.Translation(Mtr.translation + V((0.08, 0.0, 0.02))) @ Matrix.Rotation(math.radians(90), 4, 'Z')
        c.inverse_matrix = Mtr.inverted() @ Mdrop
        o_ = ct.cons[-1]
        o_.influence = 1.0; o_.keyframe_insert("influence", frame=1520); o_.influence = 0.0; o_.keyframe_insert("influence", frame=1521)
        c.influence = 0.0; c.keyframe_insert("influence", frame=1520); c.influence = 1.0; c.keyframe_insert("influence", frame=1521)
        ct.cons.append(c)
    else:
        # left shoe: already off, sitting in the tray from the start of beat 9
        sc.frame_set(1393); tray = O["Tray_1"]; Mtr = tray.matrix_world.copy()
        c = ts.constraints.new('CHILD_OF'); c.target = tray
        c.inverse_matrix = Mtr.inverted() @ (Matrix.Translation(Mtr.translation + V((-0.1, 0.0, 0.02))) @ Matrix.Rotation(math.radians(90), 4, 'Z'))
        for o_ in ct.cons:
            o_.influence = 0.0; o_.keyframe_insert("influence", frame=1)
        c.influence = 1.0; c.keyframe_insert("influence", frame=1)
        ct.cons.append(c)
    ct.done()

for s_ in "LR":
    fo = O["Fuse_Shoe_" + s_]
    for f, h in ((1, True), (877, True), (878, False)):
        fo.hide_render = h; fo.keyframe_insert("hide_render", frame=f)
    constant_at(fo, set(range(0, END + 1)))
# v006d: the fuselage shell's bottom sat ~0.18 m above the carpet and hid shins and feet; flatten it onto the carpet
cs_ = O["CabinShell"]; n_ = 0
for v in cs_.data.vertices:
    w_ = cs_.matrix_world @ v.co
    if w_.z < 0.32: v.co = cs_.matrix_world.inverted() @ V((w_.x, w_.y, -0.004)); n_ += 1
cs_.data.update(); print("SHELL_FLOOR_FLATTENED", n_)
# feet hidden inside the shoes (mask the foot/toe verts while the shoe is on)
def foot_mask(rig_name, s_, on_until):
    body = O[rig_name + ".body"]
    vg = body.vertex_groups.new(name="ShoeHide_" + s_)
    idx = {g.index for g in body.vertex_groups if g.name == "foot." + s_ or g.name.startswith("toe") and g.name.endswith("." + s_)}
    sel = [v.index for v in body.data.vertices if sum(g.weight for g in v.groups if g.group in idx) > 0.5]
    vg.add(sel, 0.9, 'REPLACE')
    # socks: the masked foot faces get a knit sock material (seen once the sneaker is off)
    sock = bpy.data.materials.get("Sock") or L.mat("Sock", (0.06, 0.06, 0.07), 0.9)
    if sock.name not in [m.name for m in body.data.materials if m]: body.data.materials.append(sock)
    si = [m.name if m else "" for m in body.data.materials].index(sock.name); ss = set(sel)
    sock_faces = 0
    for poly in body.data.polygons:
        if sum(1 for vi in poly.vertices if vi in ss) >= len(poly.vertices) - 1: poly.material_index = si; sock_faces += 1
    m = body.modifiers.new("ShoeHide_" + s_, 'MASK'); m.vertex_group = vg.name; m.invert_vertex_group = True
    while body.modifiers[0] != m and body.modifiers.find(m.name) > 0:
        bpy.ops.object.modifier_move_up({"object": body}, modifier=m.name) if False else None; break
    # toggled by threshold (0.5 = feet hidden, 0.95 = shown), not show_viewport, so a scan that disables masks keeps stable topology
    for f, on in ((1, True), (on_until, True), (on_until + 1, False)):
        m.threshold = 0.5 if on else 0.95; m.keyframe_insert("threshold", frame=f)
    constant_at(body, set(range(0, 2000)), "ShoeHide")

    print("MASK", rig_name, s_, len(sel))
for s_ in "LR":
    foot_mask("Bomber", s_, 877)
foot_mask("Traveller", "R", 1440)
shirt = O["Bomber.male_casualsuit04"]
cs_ = shirt.modifiers.new("CorrectiveSmooth", 'CORRECTIVE_SMOOTH'); cs_.factor = 0.9; cs_.iterations = 12; cs_.rest_source = 'ORCO'
pants = O.get("Bomber.male_casualsuit04")
# ------------------------------------------------------------------ match + matchbox (bomber's hands), drops in the tackle
match = O["Match"]; mbox = O["Matchbox"]
cm = Carry(match)
sc.frame_set(30)
fw = bone_w(bom, "finger2-3.R", 30); th = bone_w(bom, "finger1-3.R", 30)
tip = (fw @ V((0, bom.data.bones["finger2-3.R"].length * 0.8, 0)) + th @ V((0, bom.data.bones["finger1-3.R"].length * 0.8, 0))) / 2   # pinched between thumb and index
sh = bone_w(bom, "foot.R", 12).translation
d = (sh + V((0, 0, 0.05)) - tip).normalized()
Rm = d.to_track_quat('Z', 'Y').to_matrix().to_4x4()
_Mm = Matrix.Translation(tip - d * 0.012) @ Rm
cm.hold(bom, "wrist.R", 1, _Mm)
cm.cons[-1].inverse_matrix = bone_w(bom, "wrist.R", 30).inverted() @ _Mm
cm.free(486)                                  # knocked out of his fingers: falls to the floor
cm.done()
# fall: park target animated down to the carpet
park = bpy.data.objects.get("Park_Match_486")
if park:
    p0 = park.matrix_world.translation.copy()
    for f, p, r in ((486, p0, 0), (500, V((p0.x + 0.1, p0.y + 0.05, 0.3)), 90), (510, V((p0.x + 0.15, p0.y + 0.08, 0.004)), 180)):
        park.location = p; park.rotation_euler = (math.radians(r * 0.5), 0, math.radians(r)); park.keyframe_insert("location", frame=f); park.keyframe_insert("rotation_euler", frame=f)
cb_ = Carry(mbox)
lw = bone_w(bom, "wrist.L", 1)
cb_.hold(bom, "wrist.L", 1, lw @ Matrix.Translation(V((0.0, -0.06, -0.03))))
cb_.done()
# v006: the matchbox floated beside his busy left hand (HOVER); removed, he strikes the match on the sole
for c_ in list(mbox.children_recursive) + [mbox]: bpy.data.objects.remove(c_, do_unlink=True)
# flame: lights on the strike (f28), flickers, a second wobble, out when knocked away (486)
fl = O["Match_Flame"]; flight = O["Match_Light"]
# flame burns upward from the match head in world space (not along the stick)
fl.parent = None; fl.matrix_world = Matrix.Identity(4)
cl = fl.constraints.new('COPY_LOCATION'); cl.target = O["Match_Head"]
fl.delta_location = (0, 0, 0.0)
flight.parent = None; cl2 = flight.constraints.new('COPY_LOCATION'); cl2.target = O["Match_Head"]; flight.delta_location = (0, 0, 0.03)
for f in range(1, END + 1, 3):
    on = 28 <= f < 486
    if f < 28 or f >= 486:
        s = 0.0
    else:
        s = 1.0 + 0.25 * math.sin(f * 1.7) + 0.15 * random.uniform(-1, 1)
        if f < 34: s *= (f - 27) / 6 * 1.6
    fl.scale = (1.4 * max(s, 0.001), 1.4 * max(s, 0.001), 3.2 * max(s, 0.001)); fl.keyframe_insert("scale", frame=f)
    fl.delta_location = (0, 0, 0.022 * max(s, 0.001)); fl.keyframe_insert("delta_location", frame=f)
    flight.data.energy = 22.0 * s; flight.data.keyframe_insert("energy", frame=f)
    fl.hide_render = not on; fl.keyframe_insert("hide_render", frame=f)

# ------------------------------------------------------------------ syringe (steward's right hand, beat 5)
sy = O["Syringe"]
cs = Carry(sy)
sc.frame_set(640)
wr = bone_w(stw, "wrist.R", 640)
vs = [v.co for v in sy.data.vertices]
ext = [max(v[i] for v in vs) - min(v[i] for v in vs) for i in range(3)]
ax = max(range(3), key=lambda i: ext[i])          # long axis
# syringe long axis -> pointing down/inward (-Z world) from the palm
long_axis = [V((1, 0, 0)), V((0, 1, 0)), V((0, 0, 1))][ax]
Rq = long_axis.rotation_difference(V((-0.5, 0, -0.85)).normalized()).to_matrix().to_4x4()
pos = (bone_w(stw, "finger3-1.R", 640).translation + wr.translation) / 2
hide_before = 560
cs.hold(stw, "wrist.R", 640, Matrix.Translation(pos) @ Rq)
cs.done()
for f, h in ((1, True), (639, True), (640, False), (900, False), (901, True)):
    sy.hide_render = h; sy.keyframe_insert("hide_render", frame=f)
constant_at(sy, set(range(0, END + 1)), "hide_render")

# ------------------------------------------------------------------ tray table drop + cup tumble (beat 4 impact)
tt = O["TrayTable"]; cup = O["Cup"]
for f, r, z in ((1, 0, 0.72), (1068, 0, 0.72)):   # v006d: tray stays stowed (it cut through a head in the tackle)
    tt.rotation_euler = (math.radians(r), 0, 0); tt.location.z = z
    tt.keyframe_insert("rotation_euler", frame=f); tt.keyframe_insert("location", frame=f)
c0 = cup.location.copy()
for f, p, r in ((1, c0, (0, 0, 0)), (522, c0, (0, 0, 0)), (532, c0 + V((0.05, 0.12, -0.25)), (70, 0, 20)), (540, V((c0.x + 0.2, c0.y + 0.2, 0.035)), (90, 0, 60)),
                (548, V((c0.x + 0.3, c0.y + 0.28, 0.035)), (90, 0, 140)), (560, V((c0.x + 0.33, c0.y + 0.3, 0.035)), (90, 0, 170))):
    cup.location = p; cup.rotation_euler = [math.radians(x) for x in r]; cup.keyframe_insert("location", frame=f); cup.keyframe_insert("rotation_euler", frame=f)
# spilled drink puddle grows on the carpet
bpy.ops.mesh.primitive_circle_add(vertices=32, radius=0.12, fill_type='NGON', location=(c0.x + 0.38, c0.y + 0.36, 0.003))
pud = bpy.context.active_object; pud.name = "Spill"; L.set_mat(pud, L.mat("SpillMat", (0.25, 0.12, 0.05), 0.05))
for f, s in ((1, 0.001), (540, 0.001), (600, 1.0), (700, 1.4)):
    pud.scale = (s, s * 0.7, 1); pud.keyframe_insert("scale", frame=f)
# dust/impact puff on the carpet when he hits the floor (580): expanding translucent discs
dm = L.mat("DustPuff", (0.7, 0.68, 0.65), 1.0, alpha=0.25)
for k in range(5):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=0.08, location=(random.uniform(-0.2, 0.2), 0.75 + random.uniform(-0.5, 0.5), 0.05))
    p = bpy.context.active_object; p.name = "Dust_%d" % k; L.set_mat(p, dm)
    for f, s in ((1, 0.001), (578, 0.001), (584, 1.0), (610, 2.2), (630, 0.001)):
        p.scale = (s, s, s * 0.4); p.keyframe_insert("scale", frame=f)

# ------------------------------------------------------------------ smoke wisp from the shoe (beat 1-3): rising translucent blobs
sm = bpy.data.materials.new("Smoke"); sm.use_nodes = True; N = sm.node_tree.nodes
for n in list(N): N.remove(n)
out = N.new("ShaderNodeOutputMaterial"); vol = N.new("ShaderNodeVolumePrincipled"); vol.inputs["Density"].default_value = 0.35
vol.inputs["Color"].default_value = (0.6, 0.6, 0.62, 1); sm.node_tree.links.new(vol.outputs[0], out.inputs["Volume"])
for k in range(8):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=0.03, location=(0, 0, 0))
    p = bpy.context.active_object; p.name = "Smoke_%d" % k; L.set_mat(p, sm)
    for f in range(40 + k * 12, 480, 96):
        sc.frame_set(f); src = O["Match_Flame"].matrix_world.translation.copy()
        p.location = src; p.scale = (0.3, 0.3, 0.3); p.keyframe_insert("location", frame=f); p.keyframe_insert("scale", frame=f)
        p.location = src + V((0.5 + 0.1 * k, 0.4, 0.75)); p.scale = (2.5, 2.5, 3.5); p.keyframe_insert("location", frame=f + 95); p.keyframe_insert("scale", frame=f + 95)
    p.scale = (0.001,) * 3; p.keyframe_insert("scale", frame=39 + k * 12); p.keyframe_insert("scale", frame=600)

# ------------------------------------------------------------------ studio cutaway: split each studio shoe into upper + sole, putty slab revealed
def split(ob, zcut):
    up = ob.copy(); up.data = ob.data.copy(); up.name = ob.name + "_Upper"; ob.users_collection[0].objects.link(up)
    for o_, keep_above in ((up, True), (ob, False)):
        bm = bmesh.new(); bm.from_mesh(o_.data)
        r = bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=(0, 0, zcut), plane_no=(0, 0, 1),
                                   clear_inner=keep_above, clear_outer=not keep_above)
        edges = [e for e in r["geom_cut"] if isinstance(e, bmesh.types.BMEdge)]
        if edges:
            try: bmesh.ops.holes_fill(bm, edges=edges, sides=0)
            except Exception as e: print("FILL", e)
        bm.to_mesh(o_.data); bm.free()
    up.parent = ob; up.matrix_parent_inverse = Matrix.Identity(4); up.location = (0, 0, 0)
    return up
CUT = {}
for k, s in enumerate(("L", "R")):
    base = O["Shoe_%s_Studio" % s]
    for c in list(base.constraints): base.constraints.remove(c)
    up = split(base, 0.05)
    CUT[s] = (base, up)
    if s == "L":   # v006e: resting on the cabin aisle floor, upper lifted to show the sole's insides
        # v006e-2: the sole lies open on the aisle carpet, well behind PaxB; the cut-off upper rests beside it on the carpet
        base.rotation_euler = (0, 0, math.radians(-20)); base.location = V((0.0, -2.50, 0.0)); bpy.context.view_layer.update()
        zmin = min((base.matrix_world @ V(c)).z for c in base.bound_box); base.location.z -= zmin - 0.003
        up.location = (0.13, -0.02, -0.047); up.rotation_euler = (0, 0, math.radians(12))
        sl = O["Slab_Shoe_" + s]; sl.parent = base; sl.matrix_parent_inverse = Matrix.Identity(4); sl.location = (0, 0.0, 0.058)
        # the cut face of the sole: light rubber, so the section reads as a section
        mc = bpy.data.materials.new("SoleCut"); mc.use_nodes = True
        mc.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.42, 0.40, 0.37, 1)
        mc.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.8
        for ob_ in (base, up):
            ob_.data.materials.append(mc); mi = len(ob_.data.materials) - 1
            for pl in ob_.data.polygons:
                if abs(pl.normal.z) > 0.9 and abs(pl.center.z - 0.05) < 0.004: pl.material_index = mi
        # a plain cord from the end of the slab, lying on the cut face (prop only, no detail)
        cu = bpy.data.curves.new("Fuse_Studio_L", 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = 0.0028; cu.bevel_resolution = 2
        spn = cu.splines.new('BEZIER'); spn.bezier_points.add(2)
        for bp_, co in zip(spn.bezier_points, ((0.0, 0.080, 0.066), (0.012, 0.105, 0.064), (0.020, 0.128, 0.060))):
            bp_.co = co; bp_.handle_left_type = bp_.handle_right_type = 'AUTO'
        fz = bpy.data.objects.new("Fuse_Studio_L", cu); base.users_collection[0].objects.link(fz); fz.parent = base
        cu.materials.append(bpy.data.materials["FuseCord"])
        for f, h in ((1, True), (1068, True), (1069, False), (1158, False), (1159, True)):
            for ob_ in (base, up, sl, fz):
                ob_.hide_render = h; ob_.keyframe_insert("hide_render", frame=f)
        for ob_ in (base, up, sl, fz): constant_at(ob_, set(range(0, END + 1)))
    else:
        base.location = SXS + V((0.12, 0.0, 1.15))
rim = O["StudioCyanRim"].data
for f, e in ((1, 200.0), (1130, 200.0), (1150, 550.0), (1240, 550.0)):
    rim.energy = e; rim.keyframe_insert("energy", frame=f)

for nm, on0, on1 in (("SkyCloudEntry", 5000, 5001), ("SkyCloudExit", 5000, 5001), ("StudioCloudBank", 5000, 5001)):   # v006e: never shown
    ob_ = bpy.data.objects[nm]
    for f, h in ((1, True), (on0 - 1, True), (on0, False), (on1, False), (on1 + 1, True)):
        ob_.hide_render = h; ob_.keyframe_insert("hide_render", frame=f)
    constant_at(ob_, set(range(0, END + 1)))
for o in bpy.data.objects:
    if o.name.startswith("EngineGlow_"): o.hide_render = True     # disc read as a stray white circle
for o in bpy.data.objects:      # SSS puffs read as craters; the dusk deck + volume banks carry the sky
    if o.name.startswith("Puff_"): o.hide_render = True
# ------------------------------------------------------------------ sky: relative wind (clouds stream past the static aircraft), blinking nav/strobes
for o in bpy.data.objects:
    if o.name.startswith("Puff_"):
        x0 = o.location.x
        o.location.x = x0 + 40; o.keyframe_insert("location", frame=1240)
        o.location.x = x0 - 40; o.keyframe_insert("location", frame=1400)
cdm = bpy.data.materials["CloudDeck"]
tc = [n for n in cdm.node_tree.nodes if n.type == 'TEX_NOISE'][0]
mp = cdm.node_tree.nodes.new("ShaderNodeMapping"); cdm.node_tree.links.new([n for n in cdm.node_tree.nodes if n.type == 'TEX_COORD'][0].outputs["Object"], mp.inputs["Vector"])
cdm.node_tree.links.new(mp.outputs["Vector"], tc.inputs["Vector"])
mp.inputs["Location"].default_value = (0, 0, 0); mp.inputs["Location"].keyframe_insert("default_value", frame=1240)
mp.inputs["Location"].default_value = (500, 0, 0); mp.inputs["Location"].keyframe_insert("default_value", frame=1400)
sw = bpy.data.materials.get("StrobeWhite")
if sw:
    bb = sw.node_tree.nodes["Principled BSDF"]
    for f in range(1240, 1400, 30):
        for df, e in ((0, 0.5), (2, 12), (5, 0.5)):
            bb.inputs["Emission Strength"].default_value = e; bb.inputs["Emission Strength"].keyframe_insert("default_value", frame=f + df)
# cabin windows: night clouds drift past
wm = bpy.data.materials["WindowNight"]; cd = wm.node_tree.nodes["CloudDrift"]
cd.inputs["Location"].default_value = (0, 0, 0); cd.inputs["Location"].keyframe_insert("default_value", frame=1)
cd.inputs["Location"].default_value = (0, -30, 0); cd.inputs["Location"].keyframe_insert("default_value", frame=1100)

# ------------------------------------------------------------------ lights
def area(name, loc, aim, energy, size, col=(1, 1, 1), shape='RECTANGLE', sy_=None):
    ld = bpy.data.lights.new(name, 'AREA'); ld.energy = energy; ld.size = size; ld.color = col
    if sy_: ld.shape = shape; ld.size_y = sy_
    lo = bpy.data.objects.new(name, ld); sc.collection.objects.link(lo); lo.location = loc
    lo.rotation_euler = (V(aim) - V(loc)).to_track_quat('-Z', 'Y').to_euler(); return lo
# cabin night: soft blue fill down the aisle, warm reading-light pool on 3A, galley spill
for i, y in enumerate((-2.5, 0.0, 2.5, 5.0, 7.5)):
    area("CabinFill_%d" % i, (0, y, 2.15), (0, y, 0), 4, 1.0, (0.55, 0.65, 1.0), 'RECTANGLE', 2.0)
spot = bpy.data.lights.new("ReadingSpot_3A", 'SPOT'); spot.energy = 3; spot.spot_size = math.radians(45); spot.spot_blend = 0.6; spot.color = (1.0, 0.85, 0.65); spot.shadow_soft_size = 0.03
so = bpy.data.objects.new("ReadingSpot_3A", spot); sc.collection.objects.link(so); so.location = (-0.98 - 0.25 * 0 - 0.4, -0.05, 1.6)
so.rotation_euler = (V((-1.35, 0.2, 0.6)) - so.location).to_track_quat('-Z', 'Y').to_euler()
_fills = []
for nm_, loc_, aim_, en_, f0_, f1_ in (("FillOpening", (-0.95, 0.55, 0.55), (-1.35, 0.25, 0.75), 25, 1, 200),
                                      ("FillInjection", (0.05, 1.05, 1.15), (0.26, 1.38, 0.25), 20, 670, 770)):
    lo_ = area(nm_, loc_, aim_, en_, 0.35, (0.85, 0.9, 1.0))
    for f_, e_ in ((1, 0.0), (max(1, f0_ - 1), 0.0), (f0_, en_), (f1_, en_), (f1_ + 1, 0.0)):
        if f_ == 1 and f0_ == 1: e_ = en_
        lo_.data.energy = e_; lo_.data.keyframe_insert("energy", frame=f_)
area("GalleyWarm", (0, 9.2, 1.6), (0, 4, 0.8), 15, 0.8, (1.0, 0.8, 0.6))
area("KeyFaceAisle", (0.4, 1.5, 1.9), (-1.2, 0.0, 0.8), 4, 0.4, (0.6, 0.7, 1.0))
for i, (sx_, sy_) in enumerate(((0.94, 2.58), (-0.94, 3.44), (1.42, -1.72), (0.94, 6.88), (-1.42, 5.16))):
    sp_ = bpy.data.lights.new("ReadingPool_%d" % i, 'SPOT'); sp_.energy = 18; sp_.spot_size = math.radians(40); sp_.spot_blend = 0.7
    sp_.color = (1.0, 0.8, 0.55); sp_.shadow_soft_size = 0.03
    so_ = bpy.data.objects.new("ReadingPool_%d" % i, sp_); sc.collection.objects.link(so_); so_.location = (sx_ * 0.8, sy_ - 0.05, 1.6)
    so_.rotation_euler = (V((sx_, sy_ + 0.2, 0.55)) - so_.location).to_track_quat('-Z', 'Y').to_euler()
# sky: warm low sun
sun = bpy.data.lights.new("DuskSun", 'SUN'); sun.energy = 3.0; sun.color = (1.0, 0.72, 0.5); sun.angle = math.radians(2)
su = bpy.data.objects.new("DuskSun", sun); sc.collection.objects.link(su); su.rotation_euler = (math.radians(80), 0, math.radians(-60))
# airport: big soft skylight panels + glass wall bounce
for i, x in enumerate((-4, 0, 4)):
    area("TerminalSky_%d" % i, AX + V((x, 0, 6.8)), AX + V((x, 0, 0)), 250, 3.0, (0.95, 0.97, 1.0), 'RECTANGLE', 6.0)
area("TerminalWindow", AX + V((0, 8.5, 2.5)), AX + V((0, 0, 1)), 300, 10.0, (0.9, 0.95, 1.0), 'RECTANGLE', 4.0)
# the sun lamp affects the whole world; keep it off outside the sky beat
for f, e in ((1, 0.0), (1248, 0.0), (1249, 4.0), (1392, 4.0), (1393, 2.5)):
    sun.energy = e; sun.keyframe_insert("energy", frame=f)
for f, r in ((1392, (80, 0, -60)), (1393, (78, 0, 175))):
    su.rotation_euler = [math.radians(v) for v in r]; su.keyframe_insert("rotation_euler", frame=f)
constant_at(su, {1392, 1393})
constant_at(sun, {1248, 1249, 1392, 1393})

# ------------------------------------------------------------------ grade
sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Medium High Contrast'
for f, ex in ((1, 0.3), (1158, 0.3), (1249, 0.0), (1392, 0.0), (1393, -1.0), (END, -1.0)):
    sc.view_settings.exposure = ex; sc.view_settings.keyframe_insert("exposure", frame=f)
constant_at(sc, {1158, 1248, 1392})

# v006e: the pin is shot at aisle height from the window side; the four empty seats behind that lens are struck for the cut (580-602)
for o in bpy.data.objects:
    if any(o.name.endswith(k) for k in ("_04D", "_04E", "_05D", "_05E")) or o.name == "TrayTable":
        for f, h in ((1, False), (579, False), (580, True), (602, True), (603, False)):
            o.hide_render = h; o.keyframe_insert("hide_render", frame=f)
        constant_at(o, set(range(0, END + 1)))
# ------------------------------------------------------------------ ONE camera
cam_d = bpy.data.cameras.new("CAM_Film"); cam_d.sensor_fit = 'AUTO'; cam_d.clip_start = 0.01; cam_d.clip_end = 6000
cam_d.dof.use_dof = True; cam_d.dof.aperture_fstop = 8.0   # v006e: f/8 (director)
cam = bpy.data.objects.new("CAM_Film", cam_d); sc.collection.objects.link(cam); sc.camera = cam
aim = bpy.data.objects.new("CAM_Film_Aim", None); sc.collection.objects.link(aim)
tt_ = cam.constraints.new('TRACK_TO'); tt_.target = aim; tt_.track_axis = 'TRACK_NEGATIVE_Z'; tt_.up_axis = 'UP_Y'
cam_d.dof.focus_object = aim

def bp(rig, bone, f, off=(0, 0, 0)):
    return bone_w(RIG[rig], bone, f).translation + V(off)
def fuse_tip(s, f):
    sc.frame_set(f); fo = O["Fuse_Shoe_" + s]; p = fo.data.splines[0].bezier_points[-1].co
    return fo.matrix_world @ p
def op(name, f, off=(0, 0, 0)):
    sc.frame_set(f); return O[name].matrix_world.translation + V(off)

# framings: (frame, camera, aim, lens). Aims follow the action (evaluated bone / prop positions).
# v006: cabin camera as shots joined by cuts (CUTS); every static shot was chosen with qa_check's own criteria (face readable,
# character fills the frame, nothing in front of the lens) by scripts/cam_search.py
P = lambda x, y, z: V((x, y, z))
CAB = [[
    # ONE continuous camera (client spec). The cam_search framings are key poses; holds are repeated keys and
    # moves between them are 20-40 f with Catmull ease, routed over the seat backs (z >= 1.6) where a straight move would cross a row.
    # beat 1: his face over the shoe and the match
    # v006e: opens on a medium shot of him in his seat, face visible, bent over his shoe (over the row-4 seat back)
    (1,   V((-0.94, 1.00, 1.35)), bp("Bomber", "head", 1, (0, 0, -0.15)), 30),
    (88,  V((-0.94, 1.00, 1.35)), bp("Bomber", "head", 88, (0, 0, -0.15)), 30),
    # <= 1 s closer on the match and his face (f/8)
    (108, V((-0.96, 0.55, 1.36)), (op("Match_Flame", 108) * 0.25 + bp("Bomber", "head", 108, (0, 0, 0.04)) * 0.75), 32),
    (150, V((-0.96, 0.55, 1.36)), (op("Match_Flame", 150) * 0.25 + bp("Bomber", "head", 150, (0, 0, 0.04)) * 0.75), 32),
    (182, V((-0.40, 0.44, 1.50)), bp("Bomber", "head", 182, (0, 0.2, -0.3)), 26),
    (199, V((-0.40, 0.44, 1.50)), bp("Bomber", "head", 199, (0, 0.2, -0.3)), 26),
    # beat 2: travel up the aisle above head height to the attendant walking down it, dolly back ahead of her, push to her eyes
    (216, V((0.02, 2.40, 1.70)), bp("Attendant", "head", 216, (0, 0, -0.1)), 26),
    (232, P(0.064, 4.198, 1.041), bp("Attendant", "head", 232, (0, 0, -0.1)), 28),
    (244, P(0.064, 4.198, 1.041), bp("Attendant", "head", 244, (0, 0, -0.1)), 28),
    (265, bp("Attendant", "spine03", 265, (0.04, -1.5, 0.15)), bp("Attendant", "head", 265, (0, 0, -0.25)), 28),
    (300, bp("Attendant", "spine03", 300, (0.05, -1.3, 0.35)), bp("Attendant", "head", 300, (0, 0, -0.1)), 30),
    (330, V((0.16, 1.80, 1.50)), bp("Attendant", "head", 330, (0, 0, -0.05)), 42),
    (373, V((0.02, 1.95, 1.46)), bp("Attendant", "head", 373, (0, -0.02, -0.02)), 52),
    # beat 3: dolly back down the aisle ahead of her, drift over to the seat row as she reaches his row and catches him
    (386, P(-0.052, 1.264, 1.035), bp("Attendant", "head", 386, (0, 0, -0.1)), 34),
    (398, P(-0.089, 0.589, 1.046), bp("Attendant", "head", 398, (0, 0, -0.1)), 28),
    (408, V((-0.40, 0.72, 1.40)), bp("Attendant", "head", 408, (0, 0, -0.1)), 28),   # v006d: over the seat backs
    (418, P(-0.732, 0.846, 1.116), bp("Attendant", "head", 418, (0, 0, -0.1)), 28),
    (428, P(-0.732, 0.846, 1.116), bp("Attendant", "head", 428, (0, 0, -0.1)), 28),
    (446, P(-0.817, 1.19, 1.077), bp("Attendant", "head", 446, (0, 0, -0.1)), 28),
    (455, P(-0.817, 1.19, 1.077), bp("Attendant", "head", 455, (0, 0, -0.1)), 28),
    # beat 4: up over the seat backs and down into the aisle on PaxA as he lunges (reached by 481)
    (468, V((-0.55, 1.05, 1.85)), bp("PaxA", "head", 468), 24),   # v006d rule 3: high and clear of PaxA's head
    (481, P(0.154, -0.254, 1.057), bp("PaxA", "head", 481), 28),
    (508, P(0.154, -0.254, 1.057), bp("PaxA", "head", 508), 28),
    (521, V((-0.37, 0.39, 1.68)), bp("Attendant", "head", 521, (0, 0, -0.1)), 28),
    (534, P(-0.892, 1.042, 1.143), bp("Attendant", "head", 534, (0, 0, -0.1)), 28),
    (540, P(-0.892, 1.042, 1.143), bp("Attendant", "head", 540, (0, 0, -0.1)), 28),
    (556, P(-1.011, 0.664, 1.523), bp("Attendant", "head", 556, (0, 0, -0.1)), 28),
    (566, P(-1.011, 0.664, 1.523), bp("Attendant", "head", 566, (0, 0, -0.1)), 28),
    # v006e: the pin from the side at aisle height (faces of the attendant, PaxA and PaxB in profile; his face sideways toward us)
], [
    # v006e-2: cut across to the window side at aisle height: the attendant and PaxA face us across his back, his face turned toward us
    (580, V((1.10, 1.20, 1.00)), V((0.0, 1.22, 0.58)), 18),
    (602, V((1.10, 1.20, 1.00)), V((0.0, 1.22, 0.58)), 18),
], [
    # cut back before the steward walks into that side; he arrives and kneels seen from the aisle side
    (604, V((-0.55, 1.20, 1.75)), (bp("Steward", "head", 604) + bp("Bomber", "spine01", 604)) / 2, 22),
    (640, V((-0.55, 1.20, 1.75)), (bp("Steward", "head", 640) + bp("Bomber", "spine01", 640)) / 2, 22),   # v006c: down beside the steward, never over the aim
    (655, V((-0.80, 1.25, 1.60)), bp("Steward", "head", 655), 28),
    # v006d: a steady shot on the steward's face while he injects (the arm macro filled the frame with sleeves)
    (680, V((-0.80, 1.25, 1.60)), bp("Steward", "head", 680), 28),
    (722, V((-0.80, 1.25, 1.60)), bp("Steward", "head", 722), 28),
    (736, V((-0.80, 1.25, 1.60)), (bp("Steward", "head", 736) + bp("Attendant", "head", 736)) / 2 + V((0, 0, -0.05)), 20),
    (752, V((-0.80, 1.25, 1.60)), (bp("Steward", "head", 752) + bp("Attendant", "head", 752)) / 2 + V((0, 0, -0.08)), 20),
    (769, V((-0.80, 1.25, 1.60)), bp("Attendant", "head", 769, (0, 0, -0.1)), 28),
    (776, V((-0.80, 1.25, 1.60)), bp("Attendant", "head", 776, (0, 0, -0.1)), 28),
    # beat 6: rise to his feet -> kneeling level -> with the shoes -> orbit to the soles -> macro fuse 1 -> rack to fuse 2 -> into the sole
    (852, V((-0.80, 1.25, 1.60)), bp("PaxB", "head", 852, (0, 0, -0.1)), 24),   # v006d: hold until PaxA has finished his few steps
    (872, V((0.20, 0.70, 1.45)), bp("PaxB", "head", 872, (0, 0, -0.1)), 24),   # v006d: nobody walks the aisle now; a slow pan to PaxB at his feet
    # v006d: her face while she pulls the shoes off (the old framing looked down on the top of her head)
    (880, P(0.223, 0.702, 1.347), bp("PaxB", "head", 880, (0, 0, -0.1)), 22),
    (890, P(0.223, 0.702, 1.347), bp("PaxB", "head", 890, (0, 0, -0.1)), 22),
    (902, P(0.05, 1.089, 1.202), bp("PaxB", "head", 902, (0, 0, -0.1)), 22),
    (920, P(0.05, 1.089, 1.202), bp("PaxB", "head", 920, (0, 0, -0.1)), 22),
    # v006e: PaxB kneeling, face visible, the two shoes on the carpet in front of him (no leg close-ups, no dive into the sole)
    (960, P(0.223, 0.702, 1.347), (bp("PaxB", "head", 960) * 0.6 + op("Shoe_L", 960) * 0.4), 24),
    (1068, P(0.223, 0.702, 1.347), (bp("PaxB", "head", 1068) * 0.6 + op("Shoe_L", 1068) * 0.4), 24),
  ]]
# studio: out of the black, pulling back from shoe L; orbit as they split; low 3/4; pull back into the cloud wipe
SEG2 = [   # v006e: beat 7 -- ONE cut-open shoe resting on the cabin aisle floor, slow push to the charge in the sole (1.5 s)
    (1069, V((0.02, -2.12, 0.66)), op("Slab_Shoe_L", 1069, (0.0, -0.01, 0.0)), 34),
    (1158, V((0.02, -2.27, 0.44)), op("Slab_Shoe_L", 1158, (0.0, 0.03, 0.0)), 40),
]
# sky: from the cloud next to a cabin window, back along the wing, huge pull-out, tilt down into the deck
SEG3 = [
    (1249, KX + V((11.0, 5.2, 1.6)), KX + V((10.5, 0.0, 1.0)), 32),
    (1290, KX + V((4.0, 12.0, 4.5)), KX + V((3.0, 0.0, 0.8)), 26),
    (1335, KX + V((-22.0, 34.0, 12.0)), KX + V((0.0, 0.0, 0.0)), 24),
    (1372, KX + V((-55.0, 75.0, 22.0)), KX + V((0.0, 0.0, -5.0)), 22),
    (1392, KX + V((-60.0, 82.0, 5.0)), KX + V((-58.0, 85.0, -80.0)), 22),
]
# airport: dropping through the skylight -> crane to belt level -> dolly with the tray -> settle on the traveller in socks
SEG4 = [
    (1393, AX + V((-1.15, 1.25, 2.55)), bp("Traveller", "head", 1393, (0, 0, -0.3)), 24),
    (1440, AX + V((-0.95, 0.40, 1.55)), bp("Traveller", "head", 1440, (0, 0, -0.35)), 26),
    (1459, AX + V((-0.631, 0.306, 1.315)), bp("Traveller", "head", 1459), 28),
], [
    # v006e (director): the kneel, side-on at belt height from his right: knees on the floor beside the belt, sneaker by his knee, hand into the tray
    (1462, AX + V((-0.15, -0.85, 1.0)), AX + V((-1.2, -0.40, 0.55)), 24),
    (1527, AX + V((-0.15, -0.85, 1.0)), AX + V((-1.2, -0.40, 0.55)), 24),
], [
    (1529, AX + V((-1.219, 0.39, 1.492)), bp("Traveller", "head", 1529), 28),
    (1537, AX + V((-1.219, 0.39, 1.492)), bp("Traveller", "head", 1537), 28),
    (1562, AX + V((-1.9, 0.10, 1.45)), bp("Traveller", "head", 1562, (0, 0, -0.3)), 30),
    (1585, AX + V((-1.5, 0.15, 1.55)), bp("Traveller", "head", 1580, (0, 0, -0.25)), 32),
    (END, AX + V((-1.35, 0.05, 1.50)), bp("Traveller", "head", END, (0, 0, -0.15)), 40),
]
CUTS = {seg[-1][0] for seg in CAB}
SEG4S = list(SEG4)      # v006e: the airport is three shots joined by cuts
for seg in CAB + [SEG2, SEG3] + SEG4S:
    fc = catmull([(f, c) for f, c, a, l in seg]); fa = catmull([(f, a) for f, c, a, l in seg]); fl_ = catmull([(f, float(l)) for f, c, a, l in seg])
    f0, f1 = seg[0][0], seg[-1][0]
    for f in list(range(f0, f1 + 1, 2)) + [f1]:
        cam.location = fc(f); cam.keyframe_insert("location", frame=f)
        aim.location = fa(f); aim.keyframe_insert("location", frame=f)
        cam_d.lens = fl_(f); cam_d.keyframe_insert("lens", frame=f)
CUTS |= {1068, 1158, 1248, 1392}
CUTS |= {seg[-1][0] for seg in SEG4S[:-1]}
constant_at(cam, CUTS); constant_at(aim, CUTS); constant_at(cam_d, CUTS)

# wipes: a card in front of the lens (black into the shoe; white cloud out of the studio, white cloud dive into the airport)
bpy.ops.mesh.primitive_plane_add(size=1.0)
card = bpy.context.active_object; card.name = "WipeCard"; card.parent = cam; card.location = (0, 0, -0.03)
wmat = bpy.data.materials.new("WipeMat"); wmat.use_nodes = True; N = wmat.node_tree.nodes
for n in list(N): N.remove(n)
o_ = N.new("ShaderNodeOutputMaterial"); em = N.new("ShaderNodeEmission"); tr = N.new("ShaderNodeBsdfTransparent"); mx = N.new("ShaderNodeMixShader")
nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 4; tc = N.new("ShaderNodeTexCoord")
cr = N.new("ShaderNodeMath"); cr.operation = 'ADD'; cr.name = "WipeAmt"; cl = N.new("ShaderNodeClamp")
wmat.node_tree.links.new(tc.outputs["Generated"], nz.inputs["Vector"])
wmat.node_tree.links.new(nz.outputs["Fac"], cr.inputs[0]); wmat.node_tree.links.new(cr.outputs[0], cl.inputs["Value"])
wmat.node_tree.links.new(cl.outputs[0], mx.inputs["Fac"]); wmat.node_tree.links.new(tr.outputs[0], mx.inputs[1]); wmat.node_tree.links.new(em.outputs[0], mx.inputs[2])
wmat.node_tree.links.new(mx.outputs[0], o_.inputs["Surface"])
L.set_mat(card, wmat)
amt = cr.inputs[1]
for f, a_, col in ((1, -2, (0, 0, 0)), (END, -2, (0, 0, 0))):   # v006e: no wipe cards (clean cuts)
    amt.default_value = a_; amt.keyframe_insert("default_value", frame=f)
    em.inputs["Color"].default_value = (*col, 1); em.inputs["Color"].keyframe_insert("default_value", frame=f)

# ------------------------------------------------------------------ render baseline
r = sc.render; cy = sc.cycles
r.resolution_x, r.resolution_y, r.resolution_percentage = 1080, 1920, 100; r.fps = 60; r.fps_base = 1.0
sc.frame_start, sc.frame_end = 1, END
cy.samples = 48; cy.adaptive_threshold = 0.05; cy.use_denoising = True; cy.denoiser = 'OPENIMAGEDENOISE'
cy.max_bounces = 8; cy.diffuse_bounces = 3; cy.glossy_bounces = 3; cy.transmission_bounces = 8; cy.transparent_max_bounces = 8
cy.caustics_reflective = cy.caustics_refractive = False
cy.volume_step_rate = 4.0; cy.volume_max_steps = 256     # cloud banks only; keeps preview + farm cost sane
r.use_motion_blur = True; r.motion_blur_shutter = 0.5; r.use_persistent_data = True
r.image_settings.file_format = 'PNG'; r.image_settings.color_mode = 'RGB'; r.image_settings.compression = 15
# hide the human rigs' rest-pose doubles: nothing to hide; remove the scratch temp cameras if any
for o in list(bpy.data.objects):
    if o.type == 'CAMERA' and o is not cam: bpy.data.objects.remove(o)
# beats.json
import json
B = {1: (1, "In the middle of a flight"), 2: (199, "But a flight attendant"), 3: (373, "and caught him"), 4: (481, "Passengers and crew tackled him"),
     5: (655, "and he was finally sedated"), 6: (769, "When they checked his shoes"), 7: (1069, "Both shoes were packed"),
     8: (1159, "to bring down the entire plane"), 9: (1219, "And that's why you have to take your shoes off")}   # v006e: after 07_retime.py
json.dump([{"beat": k, "frame": v[0], "first_words": v[1]} for k, v in B.items()], open(os.path.join(HERE, "..", "beats.json"), "w"), indent=1)
# strip MPFB helper geometry (always masked out of the render) so it can never act as a collision target
import bmesh
for ob in [o for o in O if o.type == 'MESH' and o.name.endswith(".body")]:
    gi = {g.index for g in ob.vertex_groups if g.name.lower().startswith(("helper", "joint")) or g.name in ("HelperGeometry", "JointCubes")}
    if not gi: continue
    bm = bmesh.new(); bm.from_mesh(ob.data); dl = bm.verts.layers.deform.verify()
    kill = [v for v in bm.verts if any(k in gi and w > 0.5 for k, w in v[dl].items())]
    bmesh.ops.delete(bm, geom=kill, context='VERTS'); bm.to_mesh(ob.data); bm.free(); ob.data.update()
    print("HELPERS_STRIPPED", ob.name, len(kill))
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("FILM_SAVED", OUT)
