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
    cr.hold(att, "wrist." + hs, 878)            # grasped at the heel; leaves the foot with her hand
    cr.done()
    # traveller's pair
    ts = O["Shoe_%s_Trav" % s]
    ct = Carry(ts)
    offs_t = shoe_on_foot(trav, s)
    ct.hold(trav, "foot." + s, 1, attach_rest(ts, trav, "foot." + s, 1, offs_t))
    if s == "R":
        ct.free(1441)                          # he steps out of it: it stays on the floor
        ct.hold(trav, "wrist.R", 1478)         # picked up by the heel
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
for f, r, z in ((1, 0, 0.72), (520, 0, 0.72), (528, -35, 0.69), (536, -28, 0.70), (545, -32, 0.695)):
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
    base.location = SXS + V((-0.12 + 0.24 * k, 0.0, 1.15))
    # float, slow spin; split opens 1110-1150 (upper lifts 0.14 and tilts back), slab glows 1140-1230
    for f, rz, bob in ((1069, -30 + 60 * k, 0.0), (1130, 10 + 60 * k, 0.02), (1190, 45 + 60 * k, 0.0), (1250, 80 + 60 * k, 0.02)):
        base.rotation_euler = (math.radians(15), math.radians(-8 + 16 * k), math.radians(rz)); base.location.z = 1.15 + bob
        base.keyframe_insert("rotation_euler", frame=f); base.keyframe_insert("location", frame=f)
    for f, dz, rx in ((1069, 0.0, 0), (1105, 0.0, 0), (1140, 0.15, -25), (1160, 0.14, -22), (1250, 0.16, -26)):
        up.location = (0, 0.02 * (dz > 0), dz); up.rotation_euler = (math.radians(rx), 0, 0)
        up.keyframe_insert("location", frame=f); up.keyframe_insert("rotation_euler", frame=f)
    sl = O["Slab_Shoe_" + s]; sl.parent = base; sl.location = (0, 0.0, 0.062)
    for ob_ in (sl,):
        for f, h in ((1, True), (1112, True), (1113, False)):
            ob_.hide_render = h; ob_.keyframe_insert("hide_render", frame=f)
        constant_at(ob_, set(range(0, END + 1)))
rim = O["StudioCyanRim"].data
for f, e in ((1, 200.0), (1130, 200.0), (1150, 550.0), (1240, 550.0)):
    rim.energy = e; rim.keyframe_insert("energy", frame=f)

for nm, on0, on1 in (("SkyCloudEntry", 1240, 1266), ("SkyCloudExit", 1366, 1400), ("StudioCloudBank", 1215, 1252)):
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
for f, ex in ((1, 0.3), (1068, 0.3), (1069, -0.2), (1248, -0.2), (1249, 0.0), (1392, 0.0), (1393, -1.0), (END, -1.0)):
    sc.view_settings.exposure = ex; sc.view_settings.keyframe_insert("exposure", frame=f)
constant_at(sc, {1068, 1248, 1392})

# ------------------------------------------------------------------ ONE camera
cam_d = bpy.data.cameras.new("CAM_Film"); cam_d.sensor_fit = 'AUTO'; cam_d.clip_start = 0.01; cam_d.clip_end = 6000
cam_d.dof.use_dof = True; cam_d.dof.aperture_fstop = 2.8
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
SEG = [
    # beat 1: over the seatbacks in front, down into his lap -> push to his lit face -> macro on match + shoe -> rise out to the aisle
    (1,   V((-1.12, 0.50, 0.34)), (op("Shoe_R", 1, (0, 0, 0.1)) + bp("Bomber", "head", 1)) / 2, 20),
    (45,  V((-0.86, 0.44, 1.32)), (op("Match_Flame", 45) * 0.5 + bp("Bomber", "head", 45) * 0.5), 26),
    (100, V((-0.94, 0.44, 1.18)), (op("Match_Flame", 100) * 0.45 + bp("Bomber", "head", 100) * 0.55), 24),
    (150, V((-1.00, 0.47, 0.66)), (op("Match_Flame", 150) + bp("Bomber", "head", 150)) / 2, 24),
    (198, V((-0.40, 0.44, 1.50)), bp("Bomber", "head", 198, (0, 0.2, -0.3)), 26),
    # beat 2: swing round down the aisle toward the trolley, low dolly back, crane up, whip to her face, push on eyes
    (225, V((0.02, 1.05, 1.05)), V((0.0, 5.0, 1.1)), 26),
    (265, V((0.0, 1.35, 0.70)), bp("Attendant", "head", 265, (0, 0, -0.35)), 30),
    (300, V((0.05, 1.55, 1.45)), bp("Attendant", "head", 300), 35),
    (330, V((0.16, 1.80, 1.50)), bp("Attendant", "head", 330, (0, 0, -0.05)), 42),
    (372, V((0.02, 1.95, 1.46)), bp("Attendant", "head", 372, (0, -0.02, -0.02)), 52),
    # beat 3: over her shoulder, pushing over the seatback to the flame and his startled face
    (400, V((0.22, 1.15, 1.62)), op("Match_Flame", 400), 35),
    (440, V((0.20, 0.82, 1.48)), (op("Match_Flame", 440) + bp("Bomber", "head", 440)) / 2, 45),
    (480, V((0.10, 0.95, 1.55)), bp("Bomber", "head", 480), 40),
    # beat 4: wide from the aisle ahead -> crane to near top-down over the pile -> drop to carpet level for the pin
    (515, V((0.70, 3.00, 1.55)), bp("Bomber", "spine01", 515), 22),
    (555, V((0.42, 1.90, 1.95)), bp("Bomber", "spine01", 555, (0, 0, -0.1)), 22),
    (600, V((0.25, 2.30, 1.55)), bp("Bomber", "spine01", 600, (0, 0.3, 0)), 22),
    (640, V((0.05, 1.70, 2.05)), bp("Bomber", "spine01", 640, (0, 0.2, 0)), 22),
    # beat 5: low push to the arm -> macro syringe -> orbit to his face as he goes limp
    (680, V((0.05, 1.05, 2.05)), bp("Bomber", "upperarm02.R", 680), 28),
    (697, V((0.05, 0.85, 1.30)), bp("Bomber", "upperarm02.R", 697), 32),
    (712, V((0.32, 1.00, 0.50)), bp("Bomber", "upperarm02.R", 712), 34),
    (736, V((-0.22, 1.30, 0.62)), bp("Bomber", "head", 736), 26),
    (756, V((-0.24, 1.32, 0.60)), bp("Bomber", "head", 756), 26),
    (774, V((0.10, 1.10, 1.05)), bp("Bomber", "head", 774), 26),
    # beat 6: kneeling level at his feet -> rise with the shoes -> orbit to the soles -> macro fuse 1 -> rack to fuse 2 -> into the sole
    (800, V((0.52, 1.20, 1.60)), bp("Bomber", "foot.L", 800), 26),
    (866, V((0.12, 0.55, 0.80)), bp("Attendant", "head", 866, (0, 0.25, -0.35)), 28),
    (920, V((0.12, 0.55, 1.35)), ((op("Shoe_L", 920) + op("Shoe_R", 920)) / 2 * 0.5 + bp("Attendant", "head", 920) * 0.5), 26),
    (965, V((0.14, 0.40, 1.38)), (fuse_tip("L", 965) * 0.5 + bp("Attendant", "head", 965) * 0.5), 28),
    (1015, V((0.16, 0.40, 1.40)), (fuse_tip("R", 1015) * 0.5 + bp("Attendant", "head", 1015) * 0.5), 30),
    (1062, fuse_tip("L", 1062) + V((0, 0.03, 0.03)), op("Shoe_L", 1062, (0, 0, 0.05)), 40),
]
# studio: out of the black, pulling back from shoe L; orbit as they split; low 3/4; pull back into the cloud wipe
SEG2 = [
    (1069, SXS + V((-0.12, 0.05, 1.30)), SXS + V((-0.12, 0.0, 1.17)), 30),
    (1100, SXS + V((-0.25, -0.55, 1.45)), SXS + V((-0.06, 0.0, 1.18)), 35),
    (1140, SXS + V((0.35, -0.75, 1.40)), SXS + V((0.0, 0.0, 1.2)), 35),
    (1185, SXS + V((0.55, -0.45, 1.05)), SXS + V((0.0, 0.0, 1.2)), 32),
    (1225, SXS + V((0.15, -1.6, 1.35)), SXS + V((0.0, 0.0, 1.2)), 28),
    (1248, SXS + V((0.0, -3.2, 1.45)), SXS + V((0.0, 0.0, 1.25)), 26),
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
    (1393, AX + V((-0.6, -0.4, 6.4)), AX + V((-0.9, -0.5, 0.0)), 22),
    (1440, AX + V((-0.95, 0.40, 1.55)), bp("Traveller", "head", 1440, (0, 0, -0.35)), 26),
    (1470, AX + V((-1.25, 0.40, 0.98)), bp("Traveller", "head", 1470), 26),
    (1490, AX + V((-1.30, 0.35, 1.10)), bp("Traveller", "head", 1490, (0, 0, -0.1)), 28),
    (1508, AX + V((-0.85, 0.30, 1.40)), bp("Traveller", "head", 1508, (0, 0, -0.2)), 28),
    (1540, AX + V((-0.2, -1.9, 1.05)), op("Tray_1", 1540, (0, 0, 0.1)), 32),
    (1562, AX + V((-1.9, 0.10, 1.45)), bp("Traveller", "head", 1562, (0, 0, -0.3)), 30),
    (1585, AX + V((-1.5, 0.15, 1.55)), bp("Traveller", "head", 1580, (0, 0, -0.25)), 32),
    (END, AX + V((-1.35, 0.05, 1.50)), bp("Traveller", "head", END, (0, 0, -0.15)), 40),
]
for seg in (SEG, SEG2, SEG3, SEG4):
    fc = catmull([(f, c) for f, c, a, l in seg]); fa = catmull([(f, a) for f, c, a, l in seg]); fl_ = catmull([(f, float(l)) for f, c, a, l in seg])
    f0, f1 = seg[0][0], seg[-1][0]
    for f in list(range(f0, f1 + 1, 2)) + [f1]:
        cam.location = fc(f); cam.keyframe_insert("location", frame=f)
        aim.location = fa(f); aim.keyframe_insert("location", frame=f)
        cam_d.lens = fl_(f); cam_d.keyframe_insert("lens", frame=f)
constant_at(cam, {1068, 1248, 1392}); constant_at(aim, {1068, 1248, 1392}); constant_at(cam_d, {1068, 1248, 1392})

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
for f, a_, col in ((1, -2, (0, 0, 0)), (1061, -2, (0, 0, 0)), (1066, 1.5, (0, 0, 0)), (1069, 1.5, (0, 0, 0)), (1074, -2, (0, 0, 0)),
                   (1243, -2, (1, 1, 1)), (1247, 1.5, (1, 1, 1)), (1250, 1.5, (1, 1, 1)), (1254, -2, (1, 1, 1)),
                   (1386, -2, (1, 0.95, 0.92)), (1390, 1.5, (1, 0.95, 0.92)), (1394, 1.5, (1, 1, 1)), (1399, -2, (1, 1, 1))):
    amt.default_value = a_; amt.keyframe_insert("default_value", frame=f)
    em.inputs["Color"].default_value = (*col, 1); em.inputs["Color"].keyframe_insert("default_value", frame=f)
    em.inputs["Strength"].default_value = 1.0 if col[0] == 0 else 2.0; em.inputs["Strength"].keyframe_insert("default_value", frame=f)

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
     8: (1249, "to bring down the entire plane"), 9: (1393, "And that's why you have to take your shoes off")}
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
