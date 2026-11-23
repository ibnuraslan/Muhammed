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
END = 1730
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
SHOE_LAP = V((-0.46, 0.24, 0.685)); SEAT4D = V((0.44, 0.98, 0.47)); WRISTS = V((-0.02, 0.50, 0.37))   # = cabin_v010.py
# v010 (director 1): the fuse pokes out of the shoe's collar opening behind the tongue, 7 cm above it, bent toward the aisle
_fc = O["Fuse_Shoe_R"].data; _fc.bevel_depth = 0.0045
for _i, _p in enumerate([V((0.0, 0.075, 0.09)), V((0.0, 0.050, 0.172)), V((-0.030, 0.030, 0.235))]):
    _bp = _fc.splines[0].bezier_points[_i]; _bp.co = _p; _bp.handle_left_type = _bp.handle_right_type = 'AUTO'
for s, hs in (("L", "L"), ("R", "R")):
    shoe = O["Shoe_" + s]
    offs = shoe_on_foot(bom, s)
    cr = Carry(shoe)
    if s == "R":
        # v010 (director 1, 9): his right sneaker lies on his lap (toe forward, sole on his thighs, his left hand gripping
        # the collar); the attendant takes it with her hand (466) and sets it down on empty seat 4D (490)
        Mlap = Matrix.Translation(SHOE_LAP) @ Matrix.Rotation(math.pi, 4, 'Z')
        cr.free(1, Mlap)
        cr.hold(att, "wrist.R", 466)
        cr.free(490)
        cr.done()
        park = bpy.data.objects["Park_%s_490" % shoe.name]; sc.frame_set(489)
        Mw = shoe.matrix_world.copy(); zmin = min((Mw @ V(c)).z for c in shoe.bound_box)
        park.keyframe_insert("location", frame=490); park.keyframe_insert("rotation_euler", frame=490)
        park.location = V((SEAT4D.x, SEAT4D.y, SEAT4D.z + 0.004)); park.rotation_euler = (0, 0, math.radians(75))   # upright on the cushion
        park.keyframe_insert("location", frame=496); park.keyframe_insert("rotation_euler", frame=496)
    else:
        cr.hold(bom, "foot." + s, 1, attach_rest(shoe, bom, "foot." + s, 1, offs))
        cr.hold(RIG["PaxB"], "wrist.R", 876)    # v010: PaxB grips heel + collar and pulls it off; holds it up to look (no set-down)
        cr.done()

for s_ in "LR":
    fo = O["Fuse_Shoe_" + s_]
    for f, h in (((1, False), (1068, False)) if s_ == "R" else ((1, True), (877, True), (878, False))):
        fo.hide_render = h; fo.keyframe_insert("hide_render", frame=f)   # v009: his right shoe's fuse shows while he lights it
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
foot_mask("Bomber", "L", 877)
foot_mask("Bomber", "R", 1)          # v009: right sneaker is off from the start (sock shows)
exec(open(os.path.join(os.path.dirname(L.__file__), "04_airpax.py")).read())   # v009 payoff passengers
shirt = O["Bomber.male_casualsuit05"]
cs_ = shirt.modifiers.new("CorrectiveSmooth", 'CORRECTIVE_SMOOTH'); cs_.factor = 0.9; cs_.iterations = 12; cs_.rest_source = 'ORCO'
_ts = O.get("Traveller.male_casualsuit01")   # v009 fix (director 21): his shirt shoulders ballooned at the airport
if _ts:
    _c = _ts.modifiers.new("CorrectiveSmooth", 'CORRECTIVE_SMOOTH'); _c.factor = 1.0; _c.iterations = 20; _c.rest_source = 'ORCO'
pants = O.get("Bomber.male_casualsuit05")
# ------------------------------------------------------------------ match + matchbox (bomber's hands), drops in the tackle
match = O["Match"]; mbox = O["Matchbox"]
cm = Carry(match)
sc.frame_set(30)
fw = bone_w(bom, "finger2-3.R", 30); th = bone_w(bom, "finger1-3.R", 30)
tip = (fw @ V((0, bom.data.bones["finger2-3.R"].length * 0.8, 0)) + th @ V((0, bom.data.bones["finger1-3.R"].length * 0.8, 0))) / 2   # pinched between thumb and index
sc.frame_set(30); _fo = O["Fuse_Shoe_R"]; sh = _fo.matrix_world @ _fo.data.splines[0].bezier_points[-1].co - V((0, 0, 0.05))   # v009: match points at the fuse end
d = (sh + V((0, 0, 0.05)) - tip).normalized()
Rm = d.to_track_quat('Z', 'Y').to_matrix().to_4x4()
_Mm = Matrix.Translation(tip - d * 0.012) @ Rm
cm.hold(bom, "wrist.R", 1, _Mm)
cm.cons[-1].inverse_matrix = bone_w(bom, "wrist.R", 30).inverted() @ _Mm
cm.free(466)                                  # v010: he drops it when she takes the shoe
cm.done()
# fall: park target animated down to the carpet
park = bpy.data.objects.get("Park_Match_466")
if park:
    p0 = park.matrix_world.translation.copy()
    for f, p, r in ((466, p0, 0), (476, V((p0.x + 0.05, p0.y + 0.05, 0.40)), 90), (484, V((p0.x + 0.08, p0.y + 0.06, 0.004)), 180)):
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
    on = 28 <= f < 466
    if f < 28 or f >= 466:
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
sc.frame_set(640); wr = bone_w(stw, "wrist.R", 640); pos = (bone_w(stw, "finger3-1.R", 640).translation + wr.translation) / 2
cs.hold(stw, "wrist.R", 600, Matrix.Translation(pos) @ Rq)
cs.cons[-1].inverse_matrix = wr.inverted() @ (Matrix.Translation(pos) @ Rq)
cs.hold(att, "wrist.R", 652)
cs.done()
for f, h in ((1, True), (599, True), (600, False), (740, False), (741, True)):
    sy.hide_render = h; sy.keyframe_insert("hide_render", frame=f)
constant_at(sy, set(range(0, END + 1)), "hide_render")
# v010 (director 16): restraint -- a webbing strap looped round his wrists behind his back by PaxA (776-852)
bpy.ops.mesh.primitive_torus_add(major_radius=0.05, minor_radius=0.006, major_segments=40, minor_segments=8, location=(0, 0, 0))
strap = bpy.context.active_object; strap.name = "Strap"; L.set_mat(strap, L.mat("StrapWebbing", (0.05, 0.055, 0.07), 0.6))
for p_ in strap.data.polygons: p_.use_smooth = True
strap.rotation_euler = (0, math.radians(90), math.radians(8))
for f, s_, dz in ((1, 0.001, 0.0), (775, 0.001, 0.10), (776, 1.7, 0.10), (790, 1.6, 0.02), (820, 1.3, 0.0), (852, 1.0, 0.0), (1068, 1.0, 0.0)):
    strap.scale = (s_, s_, 3.0 * min(1.0, s_ * 10)); strap.location = WRISTS + V((0, 0, dz))
    strap.keyframe_insert("scale", frame=f); strap.keyframe_insert("location", frame=f)
for f, h in ((1, True), (775, True), (776, False)):
    strap.hide_render = h; strap.keyframe_insert("hide_render", frame=f)
constant_at(strap, {1, 775}, "hide_render")

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
    if s == "L":   # v010 (director 11): a clean open sole -- outsole tray with a cavity, the explosive mass filling it, the cord
        import bmesh as _bm
        from mathutils.geometry import convex_hull_2d
        for o_ in (base, up): o_.hide_render = True; o_.location = SXS + V((5, 5, -50))   # the old bisected pieces are not used
        src = O["Shoe_L"].data
        pts = [v.co for v in src.vertices if v.co.z < 0.02]
        hull = [pts[k].to_2d() for k in convex_hull_2d([p.to_2d() for p in pts])]
        c2 = sum(hull, V((0, 0))) / len(hull)
        def ring(scale, z): return [V((c2.x + (p.x - c2.x) * scale, c2.y + (p.y - c2.y) * scale, z)) for p in hull]
        bm = _bm.new()
        outer_b = [bm.verts.new(p) for p in ring(1.0, 0.0)]; outer_t = [bm.verts.new(p) for p in ring(1.0, 0.034)]
        inner_t = [bm.verts.new(p) for p in ring(0.80, 0.034)]; inner_b = [bm.verts.new(p) for p in ring(0.80, 0.010)]
        n_ = len(hull)
        bm.faces.new(list(reversed(outer_b)))
        for k in range(n_):
            k2 = (k + 1) % n_
            bm.faces.new((outer_b[k], outer_b[k2], outer_t[k2], outer_t[k]))     # outer wall
            bm.faces.new((outer_t[k], outer_t[k2], inner_t[k2], inner_t[k]))     # rim
            bm.faces.new((inner_t[k], inner_t[k2], inner_b[k2], inner_b[k]))     # cavity wall
        bm.faces.new(inner_b)                                                     # cavity floor
        me = bpy.data.meshes.new("OpenSole"); bm.to_mesh(me); bm.free()
        sole = bpy.data.objects.new("OpenSole_L", me); base.users_collection[0].objects.link(sole)
        sole.data.materials.append(L.mat("SoleRubber", (0.80, 0.79, 0.76), 0.7))
        # the explosive: a lumpy putty mass filling the cavity (no other detail)
        bm = _bm.new()
        pb_ = [bm.verts.new(p) for p in ring(0.74, 0.011)]; pt_ = [bm.verts.new(p) for p in ring(0.70, 0.036)]
        bm.faces.new(list(reversed(pb_))); bm.faces.new(pt_)
        for k in range(n_):
            k2 = (k + 1) % n_; bm.faces.new((pb_[k], pb_[k2], pt_[k2], pt_[k]))
        me2 = bpy.data.meshes.new("Charge"); bm.to_mesh(me2); bm.free()
        old = O.get("Slab_Shoe_L")
        if old: old.name = "Slab_Shoe_L_old"; old.hide_render = True; old.location = SXS + V((5, 5, -50))
        for o_ in [o for o in O if o.name.startswith("SlabOutline_Shoe_L")]: o_.hide_render = True; o_.location = SXS + V((5, 5, -50))
        sl = bpy.data.objects.new("Slab_Shoe_L", me2); sole.users_collection[0].objects.link(sl)
        rm_ = sl.modifiers.new("rm", 'REMESH'); rm_.mode = 'SMOOTH'; rm_.octree_depth = 6; rm_.use_smooth_shade = True
        tx = bpy.data.textures.new("PuttyLumps", 'CLOUDS'); tx.noise_scale = 0.02
        dp = sl.modifiers.new("lumps", 'DISPLACE'); dp.texture = tx; dp.strength = 0.004; dp.mid_level = 0.5
        pm_ = L.mat("ChargePutty", (0.78, 0.72, 0.56), 0.9); sl.data.materials.append(pm_)
        sl.parent = sole
        # cord from the mass out over the heel rim (the same cord as the fuse in the cabin)
        hy = max(p.y for p in hull)
        cu = bpy.data.curves.new("Fuse_Studio_L", 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = 0.0045; cu.bevel_resolution = 2
        spn = cu.splines.new('BEZIER'); spn.bezier_points.add(2)
        for bp_, co in zip(spn.bezier_points, ((c2.x, hy - 0.05, 0.034), (c2.x + 0.005, hy - 0.005, 0.040), (c2.x + 0.03, hy + 0.05, 0.004))):
            bp_.co = co; bp_.handle_left_type = bp_.handle_right_type = 'AUTO'
        fz = bpy.data.objects.new("Fuse_Studio_L", cu); sole.users_collection[0].objects.link(fz); fz.parent = sole
        cu.materials.append(bpy.data.materials["FuseCord"])
        # the sneaker it came out of (sole removed): lying on its side beside it, open bottom turned away from the lens
        upp = O["Shoe_L"].copy(); upp.data = O["Shoe_L"].data.copy(); upp.name = "Upper_Open_L"
        upp.animation_data_clear(); [upp.constraints.remove(c_) for c_ in list(upp.constraints)]
        sole.users_collection[0].objects.link(upp)
        bm = _bm.new(); bm.from_mesh(upp.data)
        _bm.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=(0, 0, 0.034), plane_no=(0, 0, 1), clear_inner=True)
        bm.to_mesh(upp.data); bm.free()
        sole.location = V((0.0, 3.60, 0.004)); sole.rotation_euler = (0, 0, math.radians(160))
        upp.location = V((0.16, 3.58, 0.055)); upp.rotation_euler = (math.radians(0), math.radians(-90), math.radians(170))
        for f, h in ((1, True), (1068, True), (1069, False), (1158, False), (1159, True)):
            for ob_ in (sole, sl, fz, upp):
                ob_.hide_render = h; ob_.keyframe_insert("hide_render", frame=f)
        for ob_ in (sole, sl, fz, upp): constant_at(ob_, set(range(0, END + 1)))
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
for f, e in ((1, 0.0), (1158, 0.0), (1159, 4.0), (1392, 4.0), (1393, 2.5)):
    sun.energy = e; sun.keyframe_insert("energy", frame=f)
for f, r in ((1392, (80, 0, -60)), (1393, (78, 0, 175))):
    su.rotation_euler = [math.radians(v) for v in r]; su.keyframe_insert("rotation_euler", frame=f)
constant_at(su, {1392, 1393})
constant_at(sun, {1158, 1159, 1392, 1393})

# ------------------------------------------------------------------ grade
sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Medium High Contrast'
for f, ex in ((1, 0.3), (1158, 0.3), (1159, 0.0), (1392, 0.0), (1393, -1.0), (END, -1.0)):
    sc.view_settings.exposure = ex; sc.view_settings.keyframe_insert("exposure", frame=f)
constant_at(sc, {1158, 1392})

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
    # v010 (director 1-2): S1 medium -- him in aisle seat 3C, the sneaker on his lap, match to the fuse (from over seat 4D)
    (1,   V((0.34, 1.05, 1.45)), V((-0.44, 0.20, 0.98)), 26),
    (95,  V((0.33, 1.02, 1.44)), V((-0.44, 0.21, 0.97)), 27),
], [
    # S2 closer: chin-to-head with the shoe, his hands and the flame at the fuse
    (97,  V((0.20, 0.86, 1.30)), V((-0.43, 0.20, 1.03)), 27),
    (197, V((0.19, 0.83, 1.29)), V((-0.43, 0.20, 1.03)), 28),
], [
    # S3 (director 3-4): the attendant walks down the aisle; the camera retreats ahead of her, 1.75 m from her face
    (199, bp("Attendant", "head", 199, (0, -1.75, 0.02)), bp("Attendant", "head", 199, (0, 0, -0.18)), 30),
    (240, bp("Attendant", "head", 240, (0, -1.75, 0.02)), bp("Attendant", "head", 240, (0, 0, -0.18)), 30),
    (280, bp("Attendant", "head", 280, (0, -1.75, 0.02)), bp("Attendant", "head", 280, (0, 0, -0.18)), 30),
    (318, bp("Attendant", "head", 318, (0, -1.75, 0.02)), bp("Attendant", "head", 318, (0, 0, -0.15)), 30),
    (372, bp("Attendant", "head", 318, (0.03, -1.78, 0.02)), bp("Attendant", "head", 372, (0, 0, -0.12)), 32),
], [
    # S4 (director 5): from the aisle behind him -- she arrives, palm out ("stop!"), and takes the shoe off his lap
    (373, V((0.12, -1.55, 1.52)), V((-0.12, 0.60, 1.02)), 28),
    (467, V((0.12, -1.48, 1.50)), V((-0.16, 0.45, 0.92)), 28),
], [
    # S5 (director 6): the tackle in the aisle, from forward and above (level), >= 1.5 m from everyone
    (468, V((0.04, 3.00, 1.95)), V((-0.10, 0.50, 0.95)), 26),
    (561, V((0.04, 3.00, 1.95)), V((-0.05, 0.70, 0.80)), 26),
], [
    # S6 (director 7-8): takedown, pin + sedation, level, from above seat 2D (clear of PaxB's head): the attendant and the
    # steward face the lens, the bomber face-down in the aisle
    (562, V((0.45, -1.55, 1.85)), V((-0.05, 1.00, 0.50)), 24),
    (768, V((0.45, -1.52, 1.85)), V((-0.05, 1.05, 0.48)), 25),
], [
    # S7 (director 16): restraint -- PaxA straps his wrists behind his back (from above empty seat 4D)
    (769, V((0.50, 1.05, 1.55)), V((-0.22, 0.32, 0.68)), 24),
    (866, V((0.49, 1.03, 1.55)), V((-0.22, 0.32, 0.66)), 25),
], [
    # S8 (director 9-10): PaxB face-on pulls the left sneaker off his foot and holds it up to look at it
    (868, V((0.13, 0.62, 1.30)), V((0.06, -0.62, 0.62)), 28),
    (930, V((0.13, 0.66, 1.38)), V((0.10, -0.55, 0.92)), 30),
    (1068, V((0.13, 0.70, 1.40)), V((0.12, -0.55, 0.96)), 32),
  ]]
# studio: out of the black, pulling back from shoe L; orbit as they split; low 3/4; pull back into the cloud wipe
SEG2 = [   # v006e: beat 7 -- ONE cut-open shoe resting on the cabin aisle floor, slow push to the charge in the sole (1.5 s)
    # v006f (director): on the cabin carpet with the seat legs and the aisle around it, push in to the cut sole and the cord (~1.2 s)
    (1069, V((0.0, 2.65, 0.55)), op("Slab_Shoe_L", 1069, (0.0, 0.10, 0.10)), 26),
    (1140, V((-0.02, 3.28, 0.34)), op("Slab_Shoe_L", 1140, (0.0, -0.03, 0.0)), 40),
    (1158, V((-0.02, 3.29, 0.335)), op("Slab_Shoe_L", 1158, (0.0, -0.03, 0.0)), 40),
]
# sky: from the cloud next to a cabin window, back along the wing, huge pull-out, tilt down into the deck
SEG3 = [
    # v010 (director 12): blue sky, sharp, moving -- the camera sweeps past the airliner's nose and swings round its side
    (1215, KX + V((48.0, 10.0, 8.0)), KX + V((4.0, 0.0, 0.0)), 35),
    (1290, KX + V((36.0, 34.0, 12.0)), KX + V((0.0, 0.0, 0.0)), 38),
    (1370, KX + V((10.0, 48.0, 14.0)), KX + V((-4.0, 0.0, 0.0)), 40),
]
# airport: dropping through the skylight -> crane to belt level -> dolly with the tray -> settle on the traveller in socks
SEG4 = [
    # v010 (director 13): A1 across the belt, face-on: the traveller (socks) sets his sneakers in the tray -- head with headroom
    (1393, AX + V((-0.62, 1.55, 1.55)), AX + V((-1.05, -0.35, 1.08)), 28),
    (1459, AX + V((-0.66, 1.50, 1.52)), AX + V((-1.00, -0.30, 1.00)), 30),
], [
    # A2 (director 14, the payoff): both passengers set their sneakers flat in their trays
    (1461, AX + V((0.30, 1.60, 1.60)), AX + V((0.28, -0.45, 1.00)), 24),
    (1532, AX + V((0.34, 1.55, 1.58)), AX + V((0.32, -0.45, 0.98)), 25),
], [
    # A3: the trays roll into the X-ray; the traveller watches beyond the belt
    (1534, AX + V((-0.40, 1.60, 1.45)), AX + V((-0.30, -0.20, 0.95)), 26),
    (1640, AX + V((0.90, 1.55, 1.45)), AX + V((1.50, -0.20, 0.92)), 26),
], [
    # A4 (director 15): he walks toward the lens in his socks, stops, looks down at them, shrugs -- chest-up, headroom
    (1642, bp("Traveller", "head", 1642, (1.90, -0.12, -0.05)), bp("Traveller", "head", 1642, (0, 0, -0.28)), 32),
    (1670, bp("Traveller", "head", 1670, (1.85, -0.12, -0.05)), bp("Traveller", "head", 1670, (0, 0, -0.28)), 32),
    (1698, bp("Traveller", "head", 1698, (1.70, -0.12, -0.05)), bp("Traveller", "head", 1698, (0, 0, -0.28)), 33),
    (END,  bp("Traveller", "head", 1698, (1.62, -0.12, -0.05)), bp("Traveller", "head", 1698, (0, 0, -0.25)), 34),
]
CUTS = {seg[-1][0] for seg in CAB}
SEG4S = list(SEG4)      # v009: four airport shots joined by cuts
for seg in CAB + [SEG2, SEG3] + SEG4S:
    fc = catmull([(f, c) for f, c, a, l in seg]); fa = catmull([(f, a) for f, c, a, l in seg]); fl_ = catmull([(f, float(l)) for f, c, a, l in seg])
    f0, f1 = seg[0][0], seg[-1][0]
    for f in list(range(f0, f1 + 1, 2)) + [f1]:
        cam.location = fc(f); cam.keyframe_insert("location", frame=f)
        aim.location = fa(f); aim.keyframe_insert("location", frame=f)
        cam_d.lens = fl_(f); cam_d.keyframe_insert("lens", frame=f)
CUTS |= {1068, 1158, 1214, 1370, 1392}
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
r.use_motion_blur = False;   # v010 (director 12): sharp frames
r.use_persistent_data = True
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
# v010 (director 13): the terminal is dressed -- apron + terminal buildings outside the glass (no blank/pink void), end and back
# walls with plain panels, benches, a second (empty) security lane; no text or logos anywhere
A_ = "Airport"
L.add_box("Apron", (300, 160, 0.05), AX + V((0, 90, -0.06)), L.mat("ApronTarmac", (0.20, 0.21, 0.22), 0.85), A_)
for k_, (x_, w_, h_) in enumerate(((-60, 70, 14), (25, 60, 10), (95, 50, 18))):
    L.add_box("FarTerminal_%d" % k_, (w_, 12, h_), AX + V((x_, 150, h_ / 2)), L.mat("FarTerminal", (0.62, 0.64, 0.66), 0.6), A_)
panel = L.mat("WallPanel", (0.80, 0.80, 0.78), 0.5); trim_ = L.mat("WallTrim", (0.30, 0.32, 0.36), 0.4)
for nm_, loc_, size_ in (("EndWallW", (-14, 0, 3.5), (0.2, 18, 7)), ("EndWallE", (14, 0, 3.5), (0.2, 18, 7)), ("BackWall", (0, -9.0, 3.5), (28, 0.2, 7))):
    L.add_box(nm_, size_, AX + V(loc_), panel, A_)
for k_ in range(-6, 7):
    L.add_box("BackWallJoint_%d" % k_, (0.04, 0.05, 7), AX + V((k_ * 2.0, -8.88, 3.5)), trim_, A_)
    L.add_box("EndWallJointW_%d" % k_, (0.05, 0.04, 7), AX + V((-13.88, k_ * 1.4, 3.5)), trim_, A_)
    L.add_box("EndWallJointE_%d" % k_, (0.05, 0.04, 7), AX + V((13.88, k_ * 1.4, 3.5)), trim_, A_)
for k_ in range(4):
    L.add_box("Bench_%d" % k_, (1.8, 0.5, 0.45), AX + V((-6 + k_ * 3.5, -7.6, 0.225)), trim_, A_, bevel=0.03)
for nm_ in [n for n in [o.name for o in O] if n.startswith(("Conveyor_", "Xray", "Curtain_", "Tray_"))]:
    o_ = O[nm_]
    if o_.parent is not None: continue
    c_ = o_.copy(); c_.name = nm_ + "_lane2"; c_.animation_data_clear()
    for cc in list(c_.constraints): c_.constraints.remove(cc)
    o_.users_collection[0].objects.link(c_); c_.location = o_.matrix_world.translation + V((0, 3.4, 0))
    for ch in o_.children:
        cch = ch.copy(); cch.parent = c_; o_.users_collection[0].objects.link(cch)
# v010 (director 3, 7, 15): dual-quaternion skinning on every body + garment (no puffed shoulders), and matte hair (no
# grey sheen that read as a different head between shots)
for ob in O:
    for m in ob.modifiers:
        if m.type == 'ARMATURE': m.use_deform_preserve_volume = True
HAIRS = ("short02", "short04", "ponytail01", "long01", "afro01", "bob01", "bob02")
for ob in O:
    if ob.type == 'MESH' and any(ob.name.endswith("." + h) for h in HAIRS):
        for mt in ob.data.materials:
            if not mt or not mt.use_nodes: continue
            for n in mt.node_tree.nodes:
                if n.type == 'BSDF_PRINCIPLED':
                    if "Specular IOR Level" in n.inputs: n.inputs["Specular IOR Level"].default_value = 0.12
                    n.inputs["Roughness"].default_value = 0.8
                    if "Coat Weight" in n.inputs: n.inputs["Coat Weight"].default_value = 0.0
                    if "Sheen Weight" in n.inputs: n.inputs["Sheen Weight"].default_value = 0.0
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("FILM_SAVED", OUT)
