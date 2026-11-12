"""Characters, props and acting for ElectricianPolice. Runs 03b (UI, FX, lights, camera) at the end.
blender -b build/scene.blend --python 03_animate.py -- <out_film.blend>"""
import bpy, bmesh, math, os, sys, random
from mathutils import Vector, Matrix, Quaternion, Euler
HERE = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(HERE, "common.py")).read())
_al = open(os.path.join(HERE, "..", "..", "pipeline", "anim_lib.py")).read()
_al = _al.replace("    for key, c in cons.items():\n        mid =", "    for key, c in cons.items():\n        ck = obj.name + key\n        if ck in POLE_CACHE:\n            c.pole_angle = POLE_CACHE[ck]; continue\n        mid =")
_al = _al.replace("        c.pole_angle = R_(best[0])\n", "        c.pole_angle = R_(best[0]); POLE_CACHE[ck] = c.pole_angle\n")
assert "POLE_CACHE[ck] = c.pole_angle" in _al
import json
_pc = os.path.join(BUILD, "pole_cache.json")
POLE_CACHE = json.load(open(_pc)) if os.path.exists(_pc) else {}
exec(_al)
exec(open(os.path.join(HERE, "..", "..", "pipeline", "hand_poses.py")).read())   # shared hand poses (director, 7155c8d)
OUT = sys.argv[sys.argv.index("--") + 1]
random.seed(7)
sc = bpy.context.scene
R_ = math.radians
def C(name):
    c = bpy.data.collections.get(name)
    if c is None:
        c = bpy.data.collections.new(name); sc.collection.children.link(c)
    return c
def ob(n): return bpy.data.objects[n]

# ------------------------------------------------------------------ fcurve helpers (Blender 5 layered actions)
def fcurves(idblock):
    ad = idblock.animation_data
    if not ad or not ad.action: return []
    out = []
    for layer in ad.action.layers:
        for strip in layer.strips:
            for cb in strip.channelbags:
                out.extend(cb.fcurves)
    return out
def set_interp(idblock, kind="CONSTANT", path=None):
    for fc in fcurves(idblock):
        if path is None or fc.data_path.endswith(path):
            for k in fc.keyframe_points: k.interpolation = kind
def key_vis(o, spans):
    """spans: list of (f0, f1) where the object renders; constant keys"""
    o.hide_render = True; o.keyframe_insert("hide_render", frame=1)
    for a, b in spans:
        o.hide_render = False; o.keyframe_insert("hide_render", frame=a)
        o.hide_render = True; o.keyframe_insert("hide_render", frame=b + 1)
    o.hide_viewport = False
    set_interp(o, "CONSTANT", "hide_render")

def teleport_constant(rig, frames):
    for fc in fcurves(rig):
        kp = sorted(fc.keyframe_points, key=lambda k: k.co.x)
        for a, b in zip(kp, kp[1:]):
            if any(a.co.x <= t < b.co.x and b.co.x - a.co.x > 2 for t in frames):
                a.interpolation = "CONSTANT"

# ------------------------------------------------------------------ load humans
def load_human(src, newname):
    path = os.path.join(BUILD, "h_%s.blend" % src)
    with bpy.data.libraries.load(path) as (s, d):
        d.objects = list(s.objects)
    col = C("Char_" + newname)
    arm = None
    for o in d.objects:
        col.objects.link(o)
        if o.type == "ARMATURE": arm = o
    arm.name = newname; arm.data.name = newname
    for o in d.objects:
        if o.type == "MESH":
            o.name = newname + "." + o.name.split(".", 1)[1]
    return arm
CH = {}
for src, nm in (("Man", "Man"), ("Man", "ManW"), ("OfficerA", "OfficerA"), ("OfficerB", "OfficerB"), ("OfficerC", "OfficerC"),
                ("PedA", "PedA"), ("PedB", "PedB")):
    CH[nm] = load_human(src, nm)
# extras: cheap clones that share mesh data with an existing human (own armature, own pose)
def clone_human(src, newname, tint=None):
    arm0 = CH[src]; col = C("Char_" + newname)
    arm = arm0.copy(); arm.data = arm0.data.copy(); arm.name = newname; arm.data.name = newname; col.objects.link(arm)
    for o in [x for x in bpy.data.objects if x.parent == arm0 and x.type == "MESH"]:
        c_ = o.copy(); c_.name = newname + "." + o.name.split(".", 1)[1]; col.objects.link(c_); c_.parent = arm
        for md in c_.modifiers:
            if md.type == "ARMATURE": md.object = arm
        if tint and any(k in o.name for k in ("casualsuit", "elegantsuit")):
            for slot in c_.material_slots:
                m2 = slot.material.copy(); slot.link = "OBJECT"; slot.material = m2
                tex = m2.node_tree.nodes.get("diffuseTexture"); bsdf = next(n for n in m2.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
                mix = m2.node_tree.nodes.new("ShaderNodeMix"); mix.data_type = "RGBA"; mix.blend_type = "MULTIPLY"; mix.inputs["Factor"].default_value = 1
                src_s = bsdf.inputs["Base Color"].links[0].from_socket
                m2.node_tree.links.new(src_s, mix.inputs["A"]); mix.inputs["B"].default_value = (*tint, 1)
                m2.node_tree.links.new(mix.outputs["Result"], bsdf.inputs["Base Color"])
    return arm
EXTRAS = [("PedA", "ExA", (1.0, 0.55, 0.3)), ("PedB", "ExB", (0.5, 0.8, 1.0)), ("PedB", "Vendor", (1.0, 0.95, 0.8)),
          ("PedA", "ExC", (0.6, 1.0, 0.6)), ("PedB", "ExD", (1.0, 0.7, 0.7)), ("PedA", "ExE", (0.8, 0.6, 1.0))]
for src, nm, tint in EXTRAS:
    CH[nm] = clone_human(src, nm, tint)
CH["OfficerD"] = clone_human("OfficerB", "OfficerD"); CH["OfficerE"] = clone_human("OfficerC", "OfficerE")
# background characters never open their mouths to camera: drop their teeth/tongue meshes
for nm, arm in CH.items():
    if nm in ("Man", "ManW"): continue
    for o in [x for x in bpy.data.objects if x.parent == arm and any(k in x.name for k in (".teeth", ".tongue"))]:
        bpy.data.objects.remove(o, do_unlink=True)
# bake MPFB shape keys into the meshes (smaller file, same shape)
import numpy as np
for me in {o.data for o in bpy.data.objects if o.type == "MESH" and o.data.shape_keys}:
    kb = me.shape_keys.key_blocks; n = len(me.vertices)
    base = np.empty(n * 3); kb[0].data.foreach_get("co", base); co = base.copy()
    for k in kb[1:]:
        if k.mute or abs(k.value) < 1e-6: continue
        a_ = np.empty(n * 3); k.data.foreach_get("co", a_); r_ = np.empty(n * 3); k.relative_key.data.foreach_get("co", r_)
        co += (a_ - r_) * k.value
    users = [o for o in bpy.data.objects if o.data == me]
    users[0].shape_key_clear()
    me.vertices.foreach_set("co", co); me.update()
# de-duplicate images appended twice
for im in list(bpy.data.images):
    base = im.name.rsplit(".", 1)
    if len(base) == 2 and base[1].isdigit() and base[0] in bpy.data.images and im.filepath and im.filepath == bpy.data.images[base[0]].filepath:
        im.user_remap(bpy.data.images[base[0]]); bpy.data.images.remove(im)

def meshes(arm): return [o for o in bpy.data.objects if o.parent == arm and o.type == "MESH"]
def cloth(arm, key): return next(o for o in meshes(arm) if key in o.name)

# ------------------------------------------------------------------ wardrobe: red shirt, khaki uniforms, vest, gloves, caps
def recolor(mat, col, zmin=None, zmax=None, gain=1.8, name=None):
    """shirt/uniform recolour: texture luminance x colour, optionally only above a generated-Z threshold"""
    m = mat.copy() if name else mat
    if name: m.name = name
    nt = m.node_tree; n = nt.nodes
    tex = n.get("diffuseTexture"); bsdf = next(x for x in n if x.type == "BSDF_PRINCIPLED")
    bw = n.new("ShaderNodeRGBToBW"); nt.links.new(tex.outputs["Color"], bw.inputs[0])
    mul = n.new("ShaderNodeMix"); mul.data_type = "RGBA"; mul.blend_type = "MULTIPLY"; mul.inputs["Factor"].default_value = 1
    gm = n.new("ShaderNodeMath"); gm.operation = "MULTIPLY"; gm.inputs[1].default_value = gain
    nt.links.new(bw.outputs[0], gm.inputs[0])
    nt.links.new(gm.outputs[0], mul.inputs["A"]); mul.inputs["B"].default_value = (*col, 1)
    src = bsdf.inputs["Base Color"].links[0].from_socket
    mix = n.new("ShaderNodeMix"); mix.data_type = "RGBA"
    nt.links.new(src, mix.inputs["A"]); nt.links.new(mul.outputs["Result"], mix.inputs["B"])
    if zmin is not None:
        tc = n.new("ShaderNodeTexCoord"); sp = n.new("ShaderNodeSeparateXYZ"); mr = n.new("ShaderNodeMapRange")
        mr.inputs["From Min"].default_value = zmin; mr.inputs["From Max"].default_value = zmin + 0.02
        nt.links.new(tc.outputs["Generated"], sp.inputs[0]); nt.links.new(sp.outputs["Z"], mr.inputs["Value"])
        nt.links.new(mr.outputs["Result"], mix.inputs["Factor"])
    else:
        mix.inputs["Factor"].default_value = 1.0
    nt.links.new(mix.outputs["Result"], bsdf.inputs["Base Color"])
    return m
shirt_m = cloth(CH["Man"], "casualsuit").data.materials[0]
recolor(shirt_m, (0.8, 0.07, 0.05), zmin=0.63, gain=2.6)
recolor(cloth(CH["ManW"], "casualsuit").data.materials[0], (0.8, 0.07, 0.05), zmin=0.63, gain=2.6)
for nm, col in (("OfficerA", (0.50, 0.40, 0.22)), ("OfficerB", (0.53, 0.43, 0.25)), ("OfficerC", (0.48, 0.39, 0.22))):
    recolor(cloth(CH[nm], "casualsuit").data.materials[0], col, gain=1.9)

def derived_mesh(src, name, keep, push, mat, faces=False):
    """copy a skinned mesh, keep only vertices passing keep(co, groups), push along normals"""
    o = src.copy(); o.data = src.data.copy(); o.name = name; o.data.name = name
    for c in src.users_collection: c.objects.link(o)
    me = o.data; vg = {g.index: g.name for g in o.vertex_groups}
    bm = bmesh.new(); bm.from_mesh(me); dl = bm.verts.layers.deform.active
    if faces:
        kill = [p for p in bm.faces if not keep(p.calc_center_median(), {})]
        bmesh.ops.delete(bm, geom=kill, context="FACES")
        loose = [v for v in bm.verts if not v.link_faces]; bmesh.ops.delete(bm, geom=loose, context="VERTS")
        # relax the cut edge so it doesn't zig-zag
        for _ in range(6):
            bnd = [v for v in bm.verts if v.is_boundary]
            bmesh.ops.smooth_vert(bm, verts=bnd, factor=0.5, use_axis_x=True, use_axis_y=True, use_axis_z=True)
    else:
        kill = []
        for v in bm.verts:
            grp = {vg[k]: w for k, w in v[dl].items()} if dl else {}
            if not keep(v.co, grp): kill.append(v)
        bmesh.ops.delete(bm, geom=kill, context="VERTS")
    bm.to_mesh(me); bm.free()
    me.materials.clear(); me.materials.append(mat)
    for md in list(o.modifiers):
        if md.type not in ("ARMATURE",): o.modifiers.remove(md)
    so = o.modifiers.new("push", "DISPLACE"); so.strength = push; so.mid_level = 0.0
    if faces:
        sm = o.modifiers.new("smooth", "SMOOTH"); sm.factor = 0.6; sm.iterations = 6
    sol = o.modifiers.new("solid", "SOLIDIFY"); sol.thickness = 0.004
    return o
VEST = bpy.data.materials.new("HiVis"); VEST.use_nodes = True
nt = VEST.node_tree; b = nt.nodes["Principled BSDF"]
tc = nt.nodes.new("ShaderNodeTexCoord"); sp = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(tc.outputs["Object"], sp.inputs[0])
stripes = nt.nodes.new("ShaderNodeValToRGB"); cr = stripes.color_ramp; cr.interpolation = "CONSTANT"
cr.elements[0].color = (0.85, 0.95, 0.05, 1); cr.elements[1].position = 1.0
for pos, col in ((1.06, (0.75, 0.75, 0.78, 1)), (1.11, (0.85, 0.95, 0.05, 1)), (1.24, (0.75, 0.75, 0.78, 1)), (1.29, (0.85, 0.95, 0.05, 1))):
    e = cr.elements.new((pos - 0.9) / 0.6); e.color = col
mr = nt.nodes.new("ShaderNodeMapRange"); mr.inputs["From Min"].default_value = 0.9; mr.inputs["From Max"].default_value = 1.5
nt.links.new(sp.outputs["Z"], mr.inputs["Value"]); nt.links.new(mr.outputs["Result"], stripes.inputs[0])
nt.links.new(stripes.outputs["Color"], b.inputs["Base Color"]); b.inputs["Roughness"].default_value = 0.6
b.inputs["Emission Color"].default_value = (0.6, 0.8, 0.0, 1); b.inputs["Emission Strength"].default_value = 0.15
ARMS = ("upperarm", "lowerarm", "shoulder", "wrist", "finger", "clavicle")
def vest_keep(co, g):
    return (0.98 < co.z < 1.42) and abs(co.x) < (0.19 if co.z < 1.33 else 0.15)
derived_mesh(cloth(CH["ManW"], "casualsuit"), "ManW.vest", vest_keep, 0.018, VEST, faces=True)
GLOVE = bpy.data.materials.new("Gloves"); GLOVE.use_nodes = True
gb = GLOVE.node_tree.nodes["Principled BSDF"]; gb.inputs["Base Color"].default_value = (0.03, 0.03, 0.035, 1); gb.inputs["Roughness"].default_value = 0.55
def glove_keep(co, g):
    w = sum(v for k, v in g.items() if k.startswith(("wrist", "finger", "metacarpal")))
    return w > 0.5
GLOVES = derived_mesh(ob("Man.body"), "Man.gloves", glove_keep, 0.004, GLOVE)
MVEST = derived_mesh(cloth(CH["Man"], "casualsuit"), "Man.vest", vest_keep, 0.018, VEST, faces=True)
KHAKI_D = bpy.data.materials.new("CapKhaki"); KHAKI_D.use_nodes = True
KHAKI_D.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.32, 0.25, 0.13, 1)
VISOR = bpy.data.materials.new("CapVisor"); VISOR.use_nodes = True
VISOR.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.02, 0.02, 0.02, 1); VISOR.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.2
def cap(name):
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=24, radius1=0.118, radius2=0.132, depth=0.08)
    bmesh.ops.delete(bm, geom=[f_ for f_ in bm.faces if all(v.co.z < -0.039 for v in f_.verts)], context="FACES_ONLY")   # open underside: the head sits inside
    bm.to_mesh(me); bm.free(); o = bpy.data.objects.new(name, me); me.materials.append(KHAKI_D); C("Props").objects.link(o)
    for p in me.polygons: p.use_smooth = True
    o.scale = (1.0, 1.15, 1.0)
    vm = bpy.data.meshes.new(name + "_visor"); bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=16, radius1=0.09, radius2=0.09, depth=0.006); bm.to_mesh(vm); bm.free()
    v = bpy.data.objects.new(name + "_visor", vm); vm.materials.append(VISOR); C("Props").objects.link(v)
    v.parent = o; v.location = (0, -0.09, -0.04); v.scale = (1.0, 0.6, 1.0); v.rotation_euler = (R_(-12), 0, 0)
    badge = bpy.data.objects.new(name + "_badge", bpy.data.meshes.new(name + "_bm")); C("Props").objects.link(badge)
    bm = bmesh.new(); bmesh.ops.create_circle(bm, cap_ends=True, segments=10, radius=0.018); bm.to_mesh(badge.data); bm.free()
    badge.data.materials.append(bpy.data.materials["BadgeGold"]); badge.parent = o; badge.location = (0, -0.112, 0.0); badge.rotation_euler = (R_(90), 0, 0)
    return o
CAPS = {nm: cap("Cap_" + nm) for nm in ("OfficerA", "OfficerB")}

# ------------------------------------------------------------------ rigs
class Char:
    def __init__(self, arm):
        self.o = arm; self.R = make_human_ctrl(arm); self.H = Human(self.R)
        B = self.R.BN; self.ROOT = B["root"].head_local.copy()
        self.SH = {s: B["upperarm01." + s].head_local.copy() for s in "LR"}
        self.REST_HAND = {}
        for s in "LR":
            wv = B["wrist." + s].head_local; d = B["finger3-1." + s].head_local - wv
            a = B["finger2-1." + s].head_local - B["finger5-1." + s].head_local
            n = d.cross(a) if s == "L" else a.cross(d)
            self.REST_HAND[s] = self.basis(s, d, n)
        self.BODY = {}
        for pb in arm.pose.bones: pb.rotation_mode = "QUATERNION"
    def basis(self, s, d, n):
        d = d.normalized(); n = (n - d * n.dot(d)).normalized()
        a = d.cross(n) if s == "R" else n.cross(d)
        return Matrix((d, a, n)).transposed()
    # body: pos = world position of the root head (hip joint centre), yaw 0 faces -Y
    def body(self, f, pos, yaw=0.0, flex=0.0, side=0.0, spine=(0, 0, 0), head=(0, 0), jaw=0.0):
        pos = Vector(pos); self.BODY[f] = (pos.copy(), yaw)
        self.H.key_root(f, pos, yaw=yaw, flex=flex, side=side)
        self.H.key_spine(f, flex=spine[0], twist=spine[1], side=spine[2], head=head)
        self.R.key_rot("jaw", f, [("X", -jaw)])
    def walk(self, path, yaw_fn, f0, f1, **kw):
        self.H.walk(path, yaw_fn, f0, f1, **kw)
        for f in range(f0, f1 + 1, 2): self.BODY[f] = (path(f).copy(), yaw_fn(f))
    def frame_of(self, f):
        ks = sorted(self.BODY); k = max([x for x in ks if x <= f] or [ks[0]])
        return self.BODY[k]
    def pt(self, f, lat, fwd, z):
        """world point from body-relative (lateral to the character's left, forward, absolute height)"""
        pos, yaw = self.frame_of(f); Rz = Matrix.Rotation(R_(yaw), 3, "Z")
        return Vector((pos.x, pos.y, 0)) + Rz @ Vector((lat, -fwd, 0)) + Vector((0, 0, z))
    def dirv(self, f, lat, fwd, z):
        pos, yaw = self.frame_of(f); return (Matrix.Rotation(R_(yaw), 3, "Z") @ Vector((lat, -fwd, z))).normalized()
    def foot(self, s, f, xy, yaw, lift=0.0, pitch=0.0):
        self.H.key_foot(s, f, Vector(xy).to_2d() if not isinstance(xy, Vector) else xy.to_2d(), yaw, lift, pitch)
    def stand_feet(self, f, pos=None, yaw=None, width=1.0, stagger=0.0):
        if pos is None: pos, yaw = self.frame_of(f)
        for s in "LR":
            xy = self.H.foot_xy(s, Vector(pos), yaw)
            off = Matrix.Rotation(R_(yaw), 3, "Z") @ Vector((self.H.ankle[s].x * 0.75 * (width - 1), (-stagger if s == "L" else stagger), 0))
            self.foot(s, f, Vector((xy.x + off.x, xy.y + off.y)), yaw)
    def hand(self, s, f, W, d, n, pole=None):
        Rm = self.basis(s, d, n) @ self.REST_HAND[s].transposed()
        wr = self.R.BN["wrist." + s].head_local
        self.R.key_world("IK_hand." + s, f, Matrix.Translation(W) @ Rm.to_4x4() @ Matrix.Translation(-wr) @ self.R.rest("IK_hand." + s))
        sx = 1 if s == "L" else -1
        if pole is None:
            pole = self.pt(f, sx * 0.55, -0.45, 1.0)
        pb = self.R.PB["Pole_elbow." + s]; nme = "Pole_elbow." + s
        pb.location = self.R.rest(nme).to_3x3().inverted() @ (pole - self.R.BN[nme].head_local)
        pb.keyframe_insert("location", frame=f, group=nme)
    def hand_b(self, s, f, lat, fwd, z, d=(0, 0, -1), n=None, pole=None):
        sx = 1 if s == "L" else -1
        dd = self.dirv(f, *d); nn = self.dirv(f, *(n or (-sx, 0, 0)))
        self.hand(s, f, self.pt(f, lat, fwd, z), dd, nn, pole)
    def hang(self, s, f, swing=0.0, out=0.0):
        """relaxed arm by the side; swing>0 forward"""
        sx = 1 if s == "L" else -1
        self.hand_b(s, f, sx * (0.27 + out), 0.03 + swing, self.frame_of(f)[0].z - 0.12 + abs(swing) * 0.25, d=(sx * 0.06, 0.25 * (1 if swing >= 0 else -1) * min(1, abs(swing) * 4), -1), n=(-sx, 0.1, 0))
        self.fingers(s, f, 22, 26)
    def fingers(self, s, f, curl, thumb=18, pose=None):
        """finger + thumb pose via the shared library (blender/pipeline/hand_poses.py). Explicit `pose` wins;
        otherwise the legacy curl number picks the nearest library pose."""
        if pose is None:
            c = max(curl) if isinstance(curl, (list, tuple)) else curl
            pose = "flat_palm" if c <= 2 else "relaxed" if c <= 26 else "cup_hold" if c <= 44 else "wrap_grip"
        apply_pose(self.o, s, pose, f)
    def smile(self, f, amt, smirk=0.0):
        """mouth corners up/out with the MPFB face bones (oris03/04 = lip corners, risorius = cheeks); smirk>0 favours the left corner"""
        for s, sx in (("L", 1), ("R", -1)):
            k = amt * ((1 + smirk) if s == "L" else (1 - smirk))
            for bn, dz, dx in (("oris03.", 0.0038 * k, 0.0025 * k), ("risorius03.", 0.003 * k, 0.0015 * k)):
                n = bn + s
                if n not in self.R.PB: continue
                pb = self.R.PB[n]; Rr = self.R.rest(n).to_3x3()
                pb.location = Rr.inverted() @ Vector((sx * dx, 0, dz))
                pb.keyframe_insert("location", frame=f, group=n)
def ground_z(x, y):
    """walkable floor heights of our sets"""
    if STATION["x0"] < x < STATION["x1"] and STATION["y0"] < y < STATION["y1"]: return 0.02
    if OFFICE["x0"] < x < OFFICE["x1"] and OFFICE["y0"] < y < OFFICE["y1"]: return 0.02
    if SUB["x0"] < x < SUB["x1"] and SUB["y0"] < y < SUB["y1"]: return 0.05
    if 4.15 < abs(x) < 7.2: return 0.03
    return 0.0
RIG = {nm: Char(a) for nm, a in CH.items()}
# shoe soles: measure how far the sole sits below the bare-foot reference in the rest pose and lift the IK ankles by that
for nm, ch in RIG.items():
    arm = ch.o; arm.data.pose_position = "REST"; bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    sh = next(o for o in meshes(arm) if ".shoes" in o.name)
    me = sh.evaluated_get(dg).to_mesh(); zmin = min((sh.matrix_world @ v.co).z for v in me.vertices); sh.evaluated_get(dg).to_mesh_clear()
    bd = next(o for o in meshes(arm) if ".body" in o.name)
    me = bd.evaluated_get(dg).to_mesh(); bmin = min((bd.matrix_world @ v.co).z for v in me.vertices); bd.evaluated_get(dg).to_mesh_clear()
    arm.data.pose_position = "POSE"
    for s_ in "LR": ch.H.ankle[s_].z -= zmin
    print("SOLE", nm, round(zmin, 3), "body", round(bmin, 3))
json.dump(POLE_CACHE, open(_pc, "w"))
for nm, ch in RIG.items():
    print("RIG", nm, "root", tuple(round(x, 3) for x in ch.ROOT))
M, W, OA, OB, OC, PA, PB_ = (RIG[k] for k in ("Man", "ManW", "OfficerA", "OfficerB", "OfficerC", "PedA", "PedB"))
UP = Vector((0, 0, 1))

# ------------------------------------------------------------------ bike: split wheels, ride path
bike = ob("Bike")
def split_wheels(o, prefix):
    me = o.data
    wi = [i for i, m in enumerate(me.materials) if m and ("Wheel" in m.name)]
    out = []
    for side, cond in (("F", lambda y: y > 0), ("R", lambda y: y <= 0)):
        bm = bmesh.new(); bm.from_mesh(me)
        kill = [p for p in bm.faces if not (p.material_index in wi and cond(sum((v.co.y for v in p.verts)) / len(p.verts)))]
        bmesh.ops.delete(bm, geom=kill, context="FACES")
        if not bm.verts: bm.free(); continue
        pts = [v.co.copy() for v in bm.verts]
        mn = Vector([min(p[i] for p in pts) for i in range(3)]); mx = Vector([max(p[i] for p in pts) for i in range(3)])
        ctr = (mn + mx) / 2
        for v in bm.verts: v.co -= ctr
        wm = bpy.data.meshes.new(prefix + side); bm.to_mesh(wm); bm.free()
        for m in me.materials: wm.materials.append(m)
        w = bpy.data.objects.new(prefix + "_wheel" + side, wm); C("Props").objects.link(w)
        w.parent = o; w.location = ctr; w.rotation_mode = "XYZ"; out.append((w, (mx.z - mn.z) / 2))
    bm = bmesh.new(); bm.from_mesh(me)
    bmesh.ops.delete(bm, geom=[p for p in bm.faces if p.material_index in wi], context="FACES")
    nm = me.copy(); bm.to_mesh(nm); bm.free(); o.data = nm
    return out
BIKE_WHEELS = split_wheels(bike, "Bike")
print("WHEELS", [(w.name, round(r, 3), tuple(round(x, 2) for x in w.location)) for w, r in BIKE_WHEELS])
# ride: 7 m/s, braking from f148, stop at STOP at f220
V0 = 7.0; FB, FS = 148, 220
TB = (FS - FB) / 60.0; DB = V0 * TB / 2
Y_B = STOP.y - DB
def bike_y(f):
    if f <= FB: return Y_B - V0 * (FB - f) / 60.0
    if f >= FS: return STOP.y
    t = (f - FB) / 60.0; return Y_B + V0 * t - 0.5 * (V0 / TB) * t * t
def bike_x(f):
    return STOP.x + 0.35 * math.sin((f - 1) / 60.0 * 1.6) * (1 - smooth((f - 120) / 80))   # gentle weave past the rickshaw
for f in list(range(1, 400, 2)):
    y = bike_y(f); x = bike_x(f)
    dx = bike_x(f + 1) - bike_x(f - 1); dy = max(1e-3, bike_y(f + 1) - bike_y(f - 1))
    head = -math.atan2(dx, dy) if f < FS else 0.0
    lean = -head * 1.6
    stopped_lean = R_(-7) * smooth((f - FS + 6) / 12)       # leans onto his left foot once stopped
    bike.location = (x, y, 0.0); bike.rotation_euler = (0, lean + stopped_lean, head)
    bike.keyframe_insert("location", frame=f); bike.keyframe_insert("rotation_euler", frame=f)
for w, r in BIKE_WHEELS:
    w.rotation_euler = (0, 0, 0); w.keyframe_insert("rotation_euler", frame=1)
    for f in range(1, 400, 2):
        dist = bike_y(f) - bike_y(1)
        w.rotation_euler = (-dist / max(0.2, r), 0, 0); w.keyframe_insert("rotation_euler", frame=f)
def bike_pt(f, lx, ly, lz):
    """bike-local point -> world (uses the keyed transform)"""
    y = bike_y(f); x = bike_x(f)
    dx = bike_x(f + 1) - bike_x(f - 1); dy = max(1e-3, bike_y(f + 1) - bike_y(f - 1))
    head = -math.atan2(dx, dy) if f < FS else 0.0
    lean = -head * 1.6 + R_(-7) * smooth((f - FS + 6) / 12)
    Mb = Matrix.Translation((x, y, 0)) @ Matrix.Rotation(head, 4, "Z") @ Matrix.Rotation(lean, 4, "Y")
    return Mb @ Vector((lx, ly, lz)), head
SEAT = (0.0, -0.22, 0.80); GRIP = {"L": (-0.205, 0.245, 0.99), "R": (0.205, 0.245, 0.99)}; PEG = {"L": (-0.2, 0.02, 0.30), "R": (0.2, 0.02, 0.30)}   # bike faces +Y: rider's left = -X

# ------------------------------------------------------------------ Man (road): ride, stop, ticket, hard hat
def ride_pose(f, look=0.0, hair=0.0):
    p, h = bike_pt(f, *SEAT); yaw = 180 + math.degrees(h)
    M.body(f, p + Vector((0, 0, 0.12)), yaw=yaw, flex=10, spine=(30 + 2 * math.sin(f * 0.21), look * 0.3, 0), head=(-22, look))
    for s in "LR":
        g, _ = bike_pt(f, *GRIP[s]); M.hand(s, f, g + Vector((0, 0, 0.03)), (bike_pt(f, GRIP[s][0] * 1.6, GRIP[s][1] + 0.05, GRIP[s][2])[0] - g).normalized() if False else M.dirv(f, (1 if s == "L" else -1) * 0.7, 0.4, -0.2), M.dirv(f, 0, 0.2, -1))
        M.fingers(s, f, 72, 50)
        if f < FS - 14:
            pg, _ = bike_pt(f, *PEG[s]); M.foot(s, f, pg.to_2d(), yaw, lift=pg.z, pitch=-5)
for f in range(1, FS - 10, 6):
    ride_pose(f, look=(18 * math.sin(f / 40.0)) if f < 140 else (25 if f > 160 else 0))
# stop: left foot down to the road (f205->218), right stays on the peg
ride_pose(FS - 8, look=30); ride_pose(FS, look=35)
pg, h0 = bike_pt(FS, *PEG["R"]); yaw0 = 180
for f in (FS - 14, FS - 8):
    pg2, _ = bike_pt(f, *PEG["R"]); M.foot("R", f, pg2.to_2d(), yaw0, lift=pg2.z, pitch=-5)
lfoot = bike_pt(FS, -0.42, 0.05, 0)[0]
pgl, _ = bike_pt(FS - 14, *PEG["L"]); M.foot("L", FS - 14, pgl.to_2d(), yaw0, lift=pgl.z, pitch=-5)
M.foot("L", FS - 7, ((pgl + lfoot) / 2).to_2d(), yaw0, lift=0.12, pitch=10)
M.foot("L", FS, lfoot.to_2d(), yaw0)
for f in (FS + 30, 400):
    pg2, _ = bike_pt(f, *PEG["R"]); M.foot("R", f, pg2.to_2d(), yaw0, lift=pg2.z, pitch=-5); M.foot("L", f, lfoot.to_2d(), yaw0)
# wind while riding: hair and shirt ripple (noise displacement swept by a moving empty), dies away as he stops
wind = bpy.data.objects.new("WindSweep", None); C("Props").objects.link(wind)
for f, y in ((1, 0.0), (FS, -12.0), (FS + 40, -12.5)):
    wind.location = (0, y, 0); wind.keyframe_insert("location", frame=f)
wtex = bpy.data.textures.new("WindNoise", "CLOUDS"); wtex.noise_scale = 0.06
for o, st in ((next(x for x in meshes(CH["Man"]) if ".short" in x.name), 0.018), (cloth(CH["Man"], "casualsuit"), 0.007)):
    md = o.modifiers.new("wind", "DISPLACE"); md.texture = wtex; md.texture_coords = "OBJECT"; md.texture_coords_object = wind
    md.mid_level = 0.5
    for f, v in ((1, st), (FS - 10, st), (FS + 15, 0.0)):
        md.strength = v; o.keyframe_insert('modifiers["wind"].strength', frame=f)
SP, _ = bike_pt(FS, *SEAT); SP = SP + Vector((0, 0, 0.12))
TICKET_F = 276
# annoyed acting while the officer writes; takes the slip with the right hand, shakes head
M.body(FS + 12, SP + Vector((0.0, 0, 0)), yaw=192, flex=2, spine=(8, 14, -6), head=(-6, 40))
M.body(FS + 30, SP, yaw=195, spine=(4, 18, -8), head=(4, 48), jaw=4)
M.body(250, SP, yaw=195, spine=(6, 22, -8), head=(10, 42))
M.body(TICKET_F, SP + Vector((-0.03, 0.02, 0)), yaw=197, spine=(10, 28, -10), head=(6, 38))
M.body(286, SP, yaw=190, spine=(2, 6, 2), head=(-8, -18), jaw=6)       # head shake (annoyed)
M.body(294, SP, yaw=186, spine=(0, -4, 2), head=(-8, 18), jaw=2)
M.body(304, SP, yaw=178, spine=(14, 20, 4), head=(10, 22))              # turns back to grab the hat off the seat
M.body(316, SP, yaw=176, spine=(4, 6, 0), head=(-10, 0))
M.body(330, SP, yaw=176, spine=(2, 0, 0), head=(-6, -8))
for f in (FS + 12, FS + 30, 250):
    M.hand("L", f, bike_pt(f, *GRIP["L"])[0] + Vector((0, 0, 0.03)), M.dirv(f, 0.7, 0.4, -0.2), M.dirv(f, 0, 0.2, -1)); M.fingers("L", f, 72, 50)
# right hand off the grip, reaches for the slip (officer is to his left/front)
M.hand("R", FS + 12, bike_pt(FS + 12, *GRIP["R"])[0] + Vector((0, 0, 0.03)), M.dirv(FS + 12, -0.7, 0.4, -0.2), M.dirv(FS + 12, 0, 0.2, -1))
M.hand_b("R", 250, -0.28, 0.18, 1.2, d=(0.2, 0.9, 0.1), n=(-0.9, 0, -0.3)); M.fingers("R", 250, 20, 20)
SLIP_HAND = Vector((OFFICER_SPOT.x + 1.15, OFFICER_SPOT.y - 1.55, 1.26))
M.hand("R", TICKET_F, SLIP_HAND + Vector((0.07, -0.05, -0.02)), (SLIP_HAND - M.pt(TICKET_F, -0.2, 0, 1.3)).normalized(), Vector((0, 0, -1))); M.fingers("R", TICKET_F, 0, pose="pinch")
M.hand_b("R", 292, -0.2, 0.2, 1.22, d=(0.1, 1, 0.2), n=(0, 0, 1)); M.fingers("R", 292, 0, pose="pinch")      # holds the slip, looks at it
# left hand grabs the hard hat off the rear seat, swings it onto his head
HAT_SEAT = (0.0, -0.62, 0.86)
M.hand("L", 296, bike_pt(296, -0.25, -0.5, 1.0)[0], M.dirv(296, -0.2, -0.6, -0.8), M.dirv(296, -0.8, 0, -0.3)); M.fingers("L", 296, 25, 20)
hs, _ = bike_pt(302, *HAT_SEAT)
M.hand("L", 302, hs + Vector((-0.11, 0.02, 0.06)), M.dirv(302, -0.3, -0.4, -0.8), M.dirv(302, -1, 0, 0)); M.fingers("L", 302, 0, pose="pinch")
M.hand_b("L", 306, 0.48, 0.05, 1.2, d=(0.1, -0.3, 0.9), n=(-1, 0, 0), pole=M.pt(306, 0.8, -0.2, 1.1))   # hat swings out wide, not through his chest
M.hand_b("L", 310, 0.38, 0.18, 1.6, d=(-0.3, 0.3, 0.8), n=(-1, 0, 0), pole=M.pt(310, 0.8, 0.0, 1.3)); M.fingers("L", 310, 0, pose="pinch")
M.hand_b("L", 318, 0.06, 0.0, 1.9, d=(-0.5, 0.6, -0.15), n=(0, 0, -1), pole=M.pt(318, 0.7, 0.2, 1.7)); M.fingers("L", 318, 0, pose="pinch")
M.hand_b("L", 330, 0.06, 0.02, 1.9, d=(-0.5, 0.6, -0.15), n=(0, 0, -1), pole=M.pt(330, 0.7, 0.2, 1.7)); M.fingers("L", 330, 0, pose="pinch")
M.hand_b("R", 318, -0.22, 0.32, 1.12, d=(0.1, 1, 0.2), n=(0, 0, 1))
M.smile(1, 0.0); M.smile(240, 0.0); M.smile(260, -0.8); M.smile(300, -0.6); M.smile(325, 0.4)
for o in meshes(CH["Man"]):
    key_vis(o, [(900, 1165)] if o in (GLOVES, MVEST) else [(1, 345), (900, 1165)])

# ------------------------------------------------------------------ Officer A: wave, write, hand over; later slumped inside the station
OA_POS = OFFICER_SPOT + Vector((0, 0, OA.ROOT.z))
oa_yaw = 30                                   # faces the oncoming bike (towards -Y, slightly +X)
OA.body(1, OA_POS, yaw=oa_yaw - 20, spine=(2, 0, 0), head=(0, -20)); OA.stand_feet(1)
OA.hang("L", 1, out=0.15); OA.hang("R", 1, swing=0.05)
OA.body(150, OA_POS, yaw=oa_yaw, spine=(-2, 0, 0), head=(0, 10)); OA.stand_feet(150)
OA.hang("L", 150, out=0.15); OA.hang("R", 150)
# raises the right arm, palm out (stop), then waves him over to the side
OA.body(170, OA_POS, yaw=oa_yaw, spine=(-4, -6, -4), head=(-4, 6), jaw=6)
OA.hand_b("R", 170, -0.34, 0.25, 1.75, d=(0, 0.2, 1), n=(0, 1, 0)); OA.fingers("R", 170, 0, 0)
for i, f in enumerate(range(182, 232, 10)):
    OA.body(f, OA_POS + Vector((0, 0, -0.01 * (i % 2))), yaw=oa_yaw + 4 * (i % 2), spine=(-2, -10 + 8 * (i % 2), -4), head=(-4, 4))
    OA.hand_b("R", f, -0.62 + 0.18 * (i % 2), 0.48 - 0.08 * (i % 2), 1.42, d=(-0.6 + 0.6 * (i % 2), 0.6, 0.3), n=(0, 0.3, -1), pole=OA.pt(f, -0.7, -0.2, 1.1))
    OA.fingers("R", f, 10, 10)
OA.stand_feet(170); OA.hang("L", 170, out=0.15)
# steps up to the bike (f224 -> 250) and writes on the pad held in the left hand
OA_W = Vector((STOP.x - 1.35, STOP.y + 1.05, OA.ROOT.z))
OA.walk(lambda f: OA_POS.lerp(OA_W, smooth((f - 222) / 24)), lambda f: oa_yaw + 10 * smooth((f - 222) / 24), 222, 246, stride=0.6, step=2)
for f in (250, 258, 266):
    OA.body(f, OA_W - Vector((0, 0, 0.01)), yaw=oa_yaw + 10, spine=(16, 0, 0), head=(20, 0))
    OA.hand_b("L", f, 0.05, 0.33, 1.12, d=(-0.8, 0.4, 0), n=(0, 0, 1)); OA.fingers("L", f, 0, pose="hold_flat_object")
    OA.hand_b("R", f, -0.06 + 0.03 * ((f // 8) % 2), 0.38, 1.21, d=(0.5, 0.8, -0.3), n=(0, 0, -1)); OA.fingers("R", f, 0, pose="pinch")
OA.stand_feet(250)
# tears the slip and holds it out to the man
OA.body(270, OA_W, yaw=oa_yaw + 14, spine=(10, 8, 0), head=(10, 10))
OA.hand_b("R", 270, -0.15, 0.45, 1.2, d=(0.2, 1, 0.1), n=(0, 0, -1)); OA.fingers("R", 270, 0, pose="pinch")
OA.hand("R", TICKET_F, SLIP_HAND, (SLIP_HAND - OA.pt(TICKET_F, -0.2, 0, 1.35)).normalized(), Vector((0, 0, -1))); OA.fingers("R", TICKET_F, 22, 20)
OA.body(TICKET_F, OA_W, yaw=oa_yaw + 16, spine=(12, 10, 0), head=(8, 14))
for f in (270, TICKET_F):
    OA.hand_b("L", f, 0.08, 0.3, 1.1, d=(-0.8, 0.4, 0), n=(0, 0, 1)); OA.fingers("L", f, 0, pose="hold_flat_object")
OA.body(296, OA_W, yaw=oa_yaw + 10, spine=(-2, 0, 0), head=(-6, 0), jaw=4)
OA.hang("R", 296, swing=0.1); OA.hand_b("L", 296, 0.12, 0.25, 1.05, d=(-0.6, 0.3, -0.4), n=(0, 0, 1))
OA.body(400, OA_W, yaw=oa_yaw + 10, spine=(0, 0, 0), head=(0, 0)); OA.hang("R", 400); OA.hand_b("L", 400, 0.15, 0.2, 1.0, d=(-0.5, 0.2, -0.6), n=(0, 0, 1))
OA.stand_feet(296)

# ------------------------------------------------------------------ pedestrians on the road (beats 1-3)
PA_A, PA_B = Vector((-5.7, 30.0, PA.ROOT.z)), Vector((-5.9, 12.0, PA.ROOT.z))
PA.walk(lambda f: PA_A.lerp(PA_B, (f - 1) / 400), lambda f: 0.0, 1, 400, stride=0.62, step=2)
for f in range(1, 401, 40):
    for s, ph in (("L", 0), ("R", math.pi)):
        PA.hang(s, f, swing=0.18 * math.sin(f / 18 + ph))
PB_A, PB_B = Vector((5.6, 2.0, PB_.ROOT.z)), Vector((5.6, 20.0, PB_.ROOT.z))
PB_.walk(lambda f: PB_A.lerp(PB_B, (f - 1) / 400), lambda f: 180.0, 1, 400, stride=0.6, step=2)
for f in range(1, 401, 40):
    for s, ph in (("L", 0), ("R", math.pi)):
        PB_.hang(s, f, swing=0.16 * math.sin(f / 18 + ph))
# dusk: both stroll past the dark station at the end
PA_C, PA_D = Vector((-1.6, 66.0, PA.ROOT.z)), Vector((-1.6, 59.5, PA.ROOT.z))
PA.walk(lambda f: PA_C.lerp(PA_D, (f - 1385) / 175), lambda f: 0.0, 1385, 1560, stride=0.62, step=2)
for f in range(1385, 1561, 40):
    for s, ph in (("L", 0), ("R", math.pi)):
        PA.hang(s, f, swing=0.18 * math.sin(f / 18 + ph))
for f in (401, 1384):
    PA.body(f, PA_B if f == 401 else PA_C, yaw=0); PA.stand_feet(f)
teleport_constant(PA.o, [1000])
for o in meshes(CH["PedA"]): key_vis(o, [(1, 400), (1385, 1560)])
for o in meshes(CH["PedB"]): key_vis(o, [(1, 400)])

# ------------------------------------------------------------------ ManW: substation gate, walk in; office; cabinet; final stroll
WG = Vector((GATE.x - 0.7, ob("Gate").location.y, W.ROOT.z))
W.body(320, WG, yaw=-70, spine=(-4, 0, 0), head=(-6, 8)); W.stand_feet(320)
W.hang("L", 320); W.hand_b("R", 320, -0.12, 0.2, 1.08, d=(0.6, 0.5, -0.3), n=(0, 0, 1)); W.fingers("R", 320, 50, 30)   # holding the key
W.body(360, WG, yaw=-66, spine=(-6, -4, 0), head=(-10, 0), jaw=2); W.stand_feet(360); W.hang("L", 360, swing=0.03)
W.hand_b("R", 360, -0.14, 0.22, 1.12, d=(0.6, 0.5, -0.2), n=(0, 0, 1))
W.body(340, WG + Vector((0.02, 0, -0.005)), yaw=-68, spine=(-3, 3, 2), head=(-2, 10)); W.stand_feet(340); W.hang("L", 340, swing=0.04)
W.hand_b("R", 340, -0.15, 0.24, 1.1, d=(0.6, 0.5, -0.2), n=(0, 0, 1))
W.body(376, WG + Vector((-0.02, 0, 0.0)), yaw=-70, spine=(-5, -2, -2), head=(4, 4)); W.stand_feet(376); W.hang("L", 376, swing=-0.03)   # small nod
W.hand_b("R", 376, -0.16, 0.27, 1.12, d=(0.6, 0.5, -0.2), n=(0, 0, 1))
W.body(392, WG, yaw=-74, spine=(-8, 2, 0), head=(-12, -6)); W.stand_feet(392); W.hang("L", 392)
W.hand_b("R", 392, -0.17, 0.3, 1.1, d=(0.6, 0.5, -0.2), n=(0, 0, 1))
# turn to the gate in two steps (left foot, then right), not a spin on planted feet
fa = {s_: W.H.foot_xy(s_, WG, -74) for s_ in "LR"}; fb = {s_: W.H.foot_xy(s_, WG, 90) for s_ in "LR"}
W.body(401, WG + Vector((0, 0, -0.01)), yaw=10, spine=(2, 6, 0), head=(4, 18))
W.hand_b("R", 401, -0.22, 0.38, 1.12, d=(0.5, 0.6, -0.1), n=(0, 0, 1)); W.hang("L", 401, swing=0.05, out=0.05)
W.foot("L", 397, fa["L"], -74, lift=0.05, pitch=10); W.foot("L", 400, fa["L"].lerp(fb["L"], 0.5), 8, lift=0.08, pitch=15); W.foot("L", 403, fb["L"], 90)
W.foot("R", 397, fa["R"], -74); W.foot("R", 403, fa["R"], -74); W.foot("R", 406, fa["R"].lerp(fb["R"], 0.5), 8, lift=0.08, pitch=15)
W.foot("L", 406, fb["L"], 90)
# turns to the gate, unlocks (right hand to the latch), pushes it open with the left, walks in
GATE_O = ob("Gate"); GY = GATE_O.location.y
LATCH = Vector((GATE.x - 0.06, GY - 0.40, 1.05))
W.body(410, WG, yaw=90, spine=(8, 0, 0), head=(10, 0)); W.foot("R", 410, fb["R"], 90); W.foot("L", 410, fb["L"], 90)
W.hand("R", 410, LATCH, Vector((1, 0, -0.2)), Vector((0, 1, 0))); W.fingers("R", 410, 55, 30)
W.hand("L", 410, Vector((GATE.x - 0.08, GY - 0.15, 1.15)), Vector((1, 0, 0.3)), Vector((1, 0, 0)))
W.hand("L", 432, Vector((GATE.x + 0.15, GY - 0.25, 1.15)), Vector((1, 0, 0.2)), Vector((1, 0, 0))); W.fingers("L", 410, 10, 10)
W.hand("R", 422, LATCH + Vector((0, 0, 0.03)), Vector((1, 0, -0.2)), Vector((0, 1, 0)))
WIN_A = WG + Vector((0, 0, 0)); WIN_B = Vector((10.2, 25.7, W.ROOT.z))
def wpath(f):
    u = smooth((f - 436) / 84)
    a = WIN_A.lerp(Vector((GATE.x + 1.0, GY, W.ROOT.z)), min(1, u * 2))
    return a.lerp(WIN_B, max(0, u * 2 - 1))
W.walk(wpath, lambda f: 90 - 30 * smooth((f - 480) / 40), 436, 520, stride=0.66, step=2)
for f, hp in ((530, -20), (545, -28)):     # stops, looks up at the pylon and lines
    W.body(f, WIN_B, yaw=60, spine=(-6, 0, 0), head=(hp, 8)); W.stand_feet(f, pos=WIN_B, yaw=60)
    W.hang("L", f); W.hang("R", f)
for f in range(428, 521, 16):
    for s, ph in (("L", 0), ("R", math.pi)):
        W.hang(s, f, swing=0.2 * math.sin(f / 13 + ph))
# office: seated at the laptop from f508
SEAT_P = Vector((CHAIR.x, CHAIR.y + 0.02, 0.60))
KB = Vector((DESK.x, DESK.y - 0.27, 0.815))     # keyboard centre
def seated(f, lean=18, twist=0, head=(-8, 0), jaw=0.0, dz=0.0, dy=0.0):
    W.body(f, SEAT_P + Vector((0, dy, dz)), yaw=180, flex=lean * 0.4, spine=(lean, twist, 0), head=head, jaw=jaw)
    for s, sx in (("L", 1), ("R", -1)):
        W.foot(s, f, Vector((CHAIR.x - sx * 0.14, CHAIR.y + 0.42)), 180 + sx * 6)
for f in range(548, 640, 8):          # typing / scrolling, head bobbing over the screen
    seated(f, lean=20 + 2 * math.sin(f / 9), head=(-6 + 3 * math.sin(f / 11), 4 * math.sin(f / 23)))
    for s, sx in (("L", 1), ("R", -1)):
        tap = 0.012 * (((f // 8) + (0 if s == "L" else 1)) % 2)
        W.hand(s, f, KB + Vector((-sx * 0.11 * 1.0, -0.06, 0.035 + tap)), Vector((0, 1, -0.25)), Vector((0, 0, -1)))
        W.fingers(s, f, 30, 16)
# leans in to the red row, slow grin
for f, ln, hd, sm in ((660, 22, (-6, 0), 0.2), (700, 25, (-6, 0), 0.5), (760, 26, (-8, -4), 0.9), (820, 27, (-6, 4), 1.2), (880, 27, (-8, 0), 1.4)):
    seated(f, lean=ln, head=hd, dy=0.02 * (ln - 20) / 24); W.smile(f, sm)
    for s, sx in (("L", 1), ("R", -1)):
        W.hand(s, f, KB + Vector((-sx * 0.14, -0.1, 0.03)), Vector((0, 1, -0.25)), Vector((0, 0, -1))); W.fingers(s, f, 30, 20)
W.smile(548, 0.0); W.smile(640, 0.0)
# bill grows: sits back, arms flung out in delight
for f, ln, arm in ((905, 26, 0.0), (925, -6, 1.0), (950, -12, 1.0), (980, -8, 0.8), (1000, -10, 0.9)):
    seated(f, lean=ln, head=(-10 if arm else 0, 0), jaw=8 * arm, dz=-0.01); W.smile(f, 1.6)
    for s, sx in (("L", 1), ("R", -1)):
        if arm:
            W.hand_b(s, f, sx * 0.62, 0.05, 1.6 + 0.05 * math.sin(f / 7), d=(sx * 0.5, 0, 1), n=(0, 1, 0)); W.fingers(s, f, 20, 12)
        else:
            W.hand(s, f, KB + Vector((-sx * 0.14, -0.1, 0.03)), Vector((0, 1, -0.25)), Vector((0, 0, -1)))
# cabinet: stands facing +X, right glove on the lever handle, throws it down (lever keyed in 03b)
CAB_STAND = Vector((CABINET.x - 0.86, CABINET.y + 0.12, M.ROOT.z))
LEVER_PIVOT = Vector((CABINET.x - 0.24, CABINET.y - 0.08, 1.25))
LEVER_LEN = 0.38
def lever_ang(a): return R_(70) - R_(140) * a
def lever_tip(a):   # a: 0 = up (on), 1 = down (off); rod swings in the XZ plane towards -X (the man)
    ang = lever_ang(a)
    return LEVER_PIVOT + Vector((-math.cos(ang) * LEVER_LEN, 0, math.sin(ang) * LEVER_LEN))
LEVER_KEYS = [(1010, 0.0), (1048, 0.0), (1056, 0.15), (1066, 0.95), (1070, 1.04), (1076, 1.0), (1560, 1.0)]
def lever_a(f):
    for (f0, a0), (f1, a1) in zip(LEVER_KEYS, LEVER_KEYS[1:]):
        if f0 <= f <= f1: return a0 + (a1 - a0) * smooth((f - f0) / (f1 - f0))
    return LEVER_KEYS[-1][1]
for f in (900, 1010, 1030, 1044):
    M.body(f, CAB_STAND, yaw=90, spine=(6, 0, 0), head=(-4 + (8 if f == 1044 else 0), 0)); M.stand_feet(f, width=1.2, stagger=0.06)
    M.hang("L", f, out=0.02)
M.hand("R", 1010, lever_tip(0) + Vector((-0.12, -0.06, -0.12)), Vector((1, 0, 0.5)), Vector((0, 1, 0))); M.fingers("R", 1010, 20, 15)
M.hand("R", 1030, lever_tip(0) + Vector((-0.07, -0.02, -0.05)), Vector((0.6, 0, 0.8)), Vector((0.2, 1, 0))); M.fingers("R", 1030, 30, 20)
for f in (1044, 1048, 1056, 1062, 1066, 1070, 1076, 1088):
    a = lever_a(f); tp = lever_tip(a)
    M.hand("R", f, tp + Vector((-0.055, 0.0, -0.02)), Vector((0.55, 0, 0.5)) if a < 0.5 else Vector((0.7, 0, -0.4)), Vector((0, 1, 0))); M.fingers("R", f, 74, 52)
M.body(1056, CAB_STAND + Vector((0.02, 0, 0.01)), yaw=88, spine=(-4, 6, 0), head=(-8, 0)); M.stand_feet(1056, width=1.2, stagger=0.06)
M.body(1068, CAB_STAND + Vector((0.06, 0, -0.06)), yaw=86, spine=(22, -8, 4), head=(16, 0), jaw=4); M.stand_feet(1068, width=1.2, stagger=0.06)
M.body(1080, CAB_STAND + Vector((0.04, 0, -0.05)), yaw=88, spine=(18, -8, 2), head=(8, -6))
M.body(1092, CAB_STAND + Vector((0.0, 0, -0.03)), yaw=90, spine=(12, -10, 0), head=(0, -10)); M.stand_feet(1080, width=1.2, stagger=0.06)
M.hang("L", 1056, swing=-0.15, out=0.05); M.hang("L", 1068, swing=0.1, out=0.12); M.hang("L", 1080, out=0.04)
M.body(1110, CAB_STAND + Vector((-0.08, 0, 0)), yaw=60, spine=(-4, -20, 0), head=(-6, -30)); M.stand_feet(1110, width=1.2)
M.hand_b("R", 1110, -0.25, 0.25, 1.05, d=(0, 1, 0), n=(1, 0, 0)); M.hang("L", 1110)
M.smile(1010, 0.6); M.smile(1080, 1.3)
for o in meshes(CH["ManW"]):
    if o is not GLOVES: key_vis(o, [(318, 546), (548, 1012), (1380, 1560)])
# final stroll in front of the dark station at dusk, hands in pockets, smirk to camera
SA, SB = Vector((-3.6, 52.6, W.ROOT.z)), Vector((-3.6, 56.8, W.ROOT.z))
W.walk(lambda f: SA.lerp(SB, smooth((f - 1380) / 135) * 0.6 + 0.4 * (f - 1380) / 135), lambda f: 180 + 15 * smooth((f - 1490) / 25), 1380, 1515, stride=0.85, lift=0.08, bob=0.035, crouch=0.0, lean=-3.0, step=2)
for f in range(1380, 1516, 10):   # chin up, shoulders rolling: a swagger
    ph = math.sin((f - 1380) / 135 * 2 * math.pi * 2.3)
    W.H.key_spine(f, flex=-3, twist=10 * ph, side=3 * ph, head=(-8, -6 * ph))
for f in range(1380, 1561, 10):
    ph = (f - 1380) / 135 * 2 * math.pi * 2.3 if f <= 1515 else 0.0
    for s, sx in (("L", 1), ("R", -1)):
        W.hang(s, f, swing=0.2 * math.sin(ph + (0 if s == "L" else math.pi)) * (1.0 if f <= 1515 else 0.0), out=0.04)
for f, hd, sm in ((1515, (-4, 4), 0.5), (1535, (-8, 12), 1.4), (1560, (-9, 14), 1.6)):
    W.body(f, SB, yaw=195, spine=(-4, 6, 0), head=hd); W.stand_feet(f); W.smile(f, sm, smirk=0.6)
# teleports between segments are constant (keys exist at both ends)
teleport_constant(W.o, [1379])
teleport_constant(M.o, [340])

# ------------------------------------------------------------------ street extras (beats 1-3) and the final street
def stroll(ch, a, b_, f0, f1, stride=0.62, yaw=None):
    a, b_ = Vector(a), Vector(b_)
    d = b_ - a; yw = math.degrees(math.atan2(-d.x, d.y)) + 180 if yaw is None else yaw
    a.z = b_.z = ch.ROOT.z
    ch.walk(lambda f: a.lerp(b_, (f - f0) / (f1 - f0)), lambda f: yw, f0, f1, stride=stride, step=2)
    for f in range(f0, f1 + 1, 30):
        for s_, ph in (("L", 0), ("R", math.pi)):
            ch.hang(s_, f, swing=0.17 * math.sin(f / 17 + ph))
def idle(ch, pos, yaw, f0, f1, talk=False):
    pos = Vector((pos[0], pos[1], ch.ROOT.z))
    for i, f in enumerate(range(f0, f1 + 1, 40)):
        ch.body(f, pos + Vector((0, 0, -0.01 * (i % 2))), yaw=yaw + 8 * math.sin(f / 50), spine=(4, 6 * math.sin(f / 33), 0), head=(-4, 18 * math.sin(f / 41)), jaw=4 * (i % 2) if talk else 0)
        ch.stand_feet(f)
        sx = 1
        (ch.hand_b("R", f, -0.2, 0.3 + 0.1 * (i % 2), 1.1 + 0.15 * (i % 2), d=(0.2, 1, 0.3), n=(0, 0, 1)), ch.fingers("R", f, 34, 30)) if talk else ch.hang("R", f)
        ch.hang("L", f, swing=0.05)
EX = {k: RIG[k] for k in ("ExA", "ExB", "Vendor", "ExC", "ExD", "ExE")}
stroll(EX["ExA"], (-6.6, 4.0, 0), (-6.6, 22.0, 0), 1, 420, 0.6)
stroll(EX["ExB"], (6.0, 34.0, 0), (6.0, 14.0, 0), 1, 420, 0.62)
idle(EX["Vendor"], (-4.75, 14.2), 90, 1, 420, talk=True)
stroll(EX["ExC"], (6.1, -2.0, 0), (6.1, 16.0, 0), 1, 420, 0.6)
stroll(EX["ExD"], (-4.6, 36.5, 0), (4.4, 37.5, 0), 40, 420, 0.62)
idle(EX["ExE"], (-4.9, 30.6), 90, 1, 420)
# dusk: two of them walk past the dark station at the end
stroll(EX["ExA"], (-5.9, 66.0, 0), (-5.9, 52.0, 0), 1165, 1560, 0.6)
stroll(EX["ExB"], (4.0, 40.0, 0), (2.4, 64.0, 0), 1140, 1560, 0.62)
for nm in ("ExA", "ExB"): teleport_constant(RIG[nm].o, [1000])
for nm, ch in EX.items():
    for o in meshes(CH[nm]): key_vis(o, [(1, 420), (1140, 1560)] if nm in ("ExA", "ExB") else [(1, 420)])

# ------------------------------------------------------------------ station interior: OfficerA slumped, OfficerB fanning, OfficerC phone torch
def sit(ch, f, base, yaw, lean=0, twist=0, head=(0, 0), seat_z=0.56, jaw=0.0, slide=0.0):
    fw = Matrix.Rotation(R_(yaw), 3, "Z") @ Vector((0, -1, 0))
    ch.body(f, Vector((base.x, base.y, seat_z)) + fw * slide, yaw=yaw, flex=lean * 0.4, spine=(lean, twist, 0), head=head, jaw=jaw)
    lf = Matrix.Rotation(R_(yaw), 3, "Z") @ Vector((1, 0, 0))
    for s, sx in (("L", 1), ("R", -1)):
        xy = base + fw * (0.48 + slide * 1.4) + lf * sx * 0.16
        ch.foot(s, f, xy.to_2d(), yaw + sx * 8)
# OfficerA (moves in while the camera is flying over the roofs): slumped, head back, wiping his brow
A_SEAT = Vector((-11.4, 60.5, 0.0))
for f, hd, wipe in ((1170, (-25, 10), 0), (1260, (-30, 14), 1), (1300, (-28, 4), 0), (1340, (-32, 10), 1), (1381, (-30, 8), 0), (1560, (-30, 8), 0)):
    sit(OA, f, A_SEAT, 90, lean=-14, head=hd, slide=0.12, jaw=6)
    OA.hand_b("R", f, -0.3, 0.12, 0.72, d=(0, 0.3, -1), n=(1, 0, 0))
    if wipe: OA.hand_b("L", f, 0.02, 0.18, 1.62, d=(-1, 0.1, 0.3), n=(0, 1, 0.4))
    else: OA.hand_b("L", f, 0.22, 0.25, 0.85, d=(0, 1, -0.3), n=(0, 0, -1))
teleport_constant(OA.o, [401])
OB_SEAT = Vector((-11.4, 53.5, 0.0))
for i, f in enumerate(range(1160, 1561, 9)):
    sit(OB, f, OB_SEAT, 90 + 6 * math.sin(f / 37), lean=6, head=(-6, 10 * math.sin(f / 31)), jaw=3)
    up = i % 2
    OB.hand_b("R", f, -0.2 - 0.1 * up, 0.46, 1.42 + 0.05 * up, d=(0.3, 0.2, 1), n=(0.3, 1, 0)); OB.fingers("R", f, 0, pose="pinch")
    OB.hand_b("L", f, 0.22, 0.4, 0.83, d=(0, 1, -0.2), n=(0, 0, -1)); OB.fingers("L", f, 15, 10)
OC_POS = Vector((-14.3, 56.4, OC.ROOT.z))
for i, f in enumerate(range(1160, 1561, 30)):
    yw = 70 + 25 * math.sin(f / 50)
    OC.body(f, OC_POS, yaw=yw, spine=(2, 8 * math.sin(f / 40), 0), head=(-4, -10 * math.sin(f / 50))); OC.stand_feet(f, width=1.1)
    OC.hand_b("R", f, -0.16, 0.42, 1.22, d=(0.25, 0.6, 0.75), n=(0.2, -1, 0.3)); OC.fingers("R", f, 0, pose="pinch")
    OC.hand_b("L", f, 0.3, 0.04, 0.9, d=(0.15, 0.2, -1), n=(-1, 0, 0))
OD, OE = RIG["OfficerD"], RIG["OfficerE"]
OD_POS = Vector((-11.95, 58.05, OD.ROOT.z)); FAN_TIP = Vector((-12.25, 57.45, 2.47))
for i, f in enumerate(range(1160, 1561, 8)):
    tap = i % 2
    OD.body(f, OD_POS + Vector((0, 0, 0.02 * tap)), yaw=-150, spine=(-14, 0, -4), head=(-38, 0), jaw=6 if tap else 0)
    OD.stand_feet(f)
    OD.hand("R", f, FAN_TIP + Vector((0.1, 0.12, -0.28 - 0.08 * tap)), (FAN_TIP - OD.pt(f, -0.2, 0, 1.4)).normalized(), Vector((0, 0, -1))); OD.fingers("R", f, 0, pose="pinch")
    OD.hand_b("L", f, 0.24, 0.05, 0.95 + 0.05 * tap, d=(0.2, 0.3, -1), n=(-1, 0, 0))
OE_POS = Vector((-17.3, 62.2, OE.ROOT.z))
for i, f in enumerate(range(1160, 1561, 9)):
    up = i % 2; wipe = (i // 6) % 3 == 2
    OE.body(f, OE_POS, yaw=60, spine=(8, 6 * up, 0), head=(-10, 8), jaw=4)
    OE.stand_feet(f)
    OE.hand_b("R", f, -0.2 - 0.1 * up, 0.44, 1.42 + 0.05 * up, d=(0.3, 0.2, 1), n=(0.3, 1, 0)); OE.fingers("R", f, 0, pose="pinch")
    if wipe: OE.hand_b("L", f, 0.02, 0.24, 1.66, d=(-1, 0.1, 0.3), n=(0, 1, 0.4), pole=OE.pt(f, 0.6, 0.1, 1.5))
    else: OE.hang("L", f, swing=0.05, out=0.07)
for nm in ("OfficerB", "OfficerC", "OfficerD", "OfficerE"):
    for o in meshes(CH[nm]): key_vis(o, [(1150, 1560)])
for o in meshes(CH["OfficerA"]): key_vis(o, [(1, 420), (1171, 1560)])

# ------------------------------------------------------------------ hands pass (client 23:00 UTC): joint limits + relaxed default
def hand_limits(ch):
    B = ch.R.PB
    for s_ in "LR":
        Rh = ch.REST_HAND[s_]; d, a = Rh.col[0].copy(), Rh.col[1].copy(); sign = 1 if s_ == "R" else -1
        for k in range(1, 6):
            for j in range(1, 4):
                bn = "finger%d-%d.%s" % (k, j, s_)
                if bn not in B: continue
                e = ch.R.local_q(bn, Matrix.Rotation(R_(60 * sign), 3, a)).to_euler()
                ax = max(range(3), key=lambda i: abs(e[i])); sg = 1 if e[ax] > 0 else -1
                c = B[bn].constraints.new("LIMIT_ROTATION"); c.name = "hand_limit"; c.owner_space = "LOCAL"
                c.use_limit_x = c.use_limit_y = c.use_limit_z = True
                lim = [(-R_(12), R_(12))] * 3 if k > 1 else [(-R_(45), R_(45))] * 3
                lim = list(lim)
                bend = (R_(0), R_(95)) if sg > 0 else (R_(-95), R_(0))
                if k == 1: bend = (R_(-25), R_(70)) if sg > 0 else (R_(-70), R_(25))
                lim[ax] = bend
                (c.min_x, c.max_x), (c.min_y, c.max_y), (c.min_z, c.max_z) = lim
        w = B["wrist." + s_].constraints.new("LIMIT_ROTATION"); w.name = "hand_limit"; w.owner_space = "LOCAL"
        w.use_limit_x = w.use_limit_y = w.use_limit_z = True
        w.min_x, w.max_x = -R_(60), R_(60); w.min_z, w.max_z = -R_(35), R_(35); w.min_y, w.max_y = -R_(50), R_(50)
for nm, ch in RIG.items():
    add_hand_limits(ch.o)
    fk = [fc for fc in fcurves(ch.o) if '"finger' in fc.data_path]
    first = min((k.co.x for fc in fk for k in fc.keyframe_points), default=10 ** 6)
    if first > 1:
        for s_ in "LR": ch.fingers(s_, 1, 22, 26)        # relaxed, gently curled until the first acted key
print("HAND_LIMITS_DONE")
print("ANIM_CHARS_DONE")
# ---- grip solver: move each grasping hand so the object runs through the hole of the curled fist
def fist_hole(rig, s):
    mw = rig.matrix_world; pts = []
    for k in range(2, 6):
        for bn, tl in (("finger%d-1." % k, False), ("finger%d-2." % k, False), ("finger%d-3." % k, True)):
            pb_ = rig.pose.bones[bn + s]; pts.append(mw @ (pb_.tail if tl else pb_.head))
    return sum(pts, Vector()) / len(pts)
def grip_fix(ch, s, f0, f1, target_fn, iters=2):
    rig = ch.o; nm = "IK_hand." + s; dp = 'pose.bones["%s"].location' % nm
    fc = [c for c in rig.animation_data.action.fcurves if c.data_path == dp] if hasattr(rig.animation_data.action, "fcurves") else []
    if not fc:
        from bpy_extras import anim_utils
        cb = anim_utils.action_get_channelbag_for_slot(rig.animation_data.action, rig.animation_data.action_slot)
        fc = [c for c in cb.fcurves if c.data_path == dp]
    frames = sorted({int(round(k.co.x)) for c in fc for k in c.keyframe_points if f0 <= k.co.x <= f1})
    worst = 0.0
    for f in frames:
        for _ in range(iters):
            bpy.context.scene.frame_set(f)
            d = target_fn(f) - fist_hole(rig, s)
            pb_ = rig.pose.bones[nm]
            ch.R.key_world(nm, f, Matrix.Translation(d) @ pb_.matrix)
        bpy.context.scene.frame_set(f); worst = max(worst, (target_fn(f) - fist_hole(rig, s)).length)
    print("GRIPFIX", ch.o.name, s, f0, f1, len(frames), "worst %.3f m" % worst)
def _ik_frames(ch, s, f0, f1):
    rig = ch.o; dp = 'pose.bones["IK_hand.%s"].location' % s
    return sorted({int(round(k.co.x)) for c in fcurves(rig) if c.data_path == dp for k in c.keyframe_points if f0 <= k.co.x <= f1})
def touch_fix(ch, s, f0, f1, obj, tips=(2, 3), inset=0.003, iters=2):
    """move the hand (IK) so the given fingertips rest on obj's surface (nearest point), `inset` into it"""
    from mathutils.bvhtree import BVHTree
    rig = ch.o; nm = "IK_hand." + s; worst = 0.0; fr = _ik_frames(ch, s, f0, f1)
    def bvh():
        dg = bpy.context.evaluated_depsgraph_get(); ev_ = obj.evaluated_get(dg); me = ev_.to_mesh(); mw = obj.matrix_world
        t = BVHTree.FromPolygons([mw @ v.co for v in me.vertices], [tuple(p.vertices) for p in me.polygons]); ev_.to_mesh_clear(); return t
    def probe():
        return sum((rig.matrix_world @ rig.pose.bones["finger%d-3.%s" % (k, s)].tail for k in tips), Vector()) / len(tips)
    for f in fr:
        for _ in range(iters):
            bpy.context.scene.frame_set(f); t = bvh(); p_ = probe(); loc, nrm, _i, dist = t.find_nearest(p_, 1.0)
            if loc is None: break
            nrm = nrm if (p_ - loc).dot(nrm) >= 0 else -nrm
            ch.R.key_world(nm, f, Matrix.Translation(loc - nrm * inset - p_) @ rig.pose.bones[nm].matrix)
        bpy.context.scene.frame_set(f); t = bvh(); p_ = probe(); loc = t.find_nearest(p_, 1.0)[0]
        if loc is not None: worst = max(worst, (loc - p_).length)
    print("TOUCHFIX", rig.name, s, obj.name, f0, f1, len(fr), "worst %.3f m" % worst)
for s_ in "LR":
    grip_fix(M, s_, 1, FS - 1, lambda f, s_=s_: bike_pt(f, *GRIP[s_])[0])
grip_fix(M, "R", FS, FS + 12, lambda f: bike_pt(f, *GRIP["R"])[0])
grip_fix(M, "L", FS, 250, lambda f: bike_pt(f, *GRIP["L"])[0])
grip_fix(M, "R", 1044, 1088, lambda f: lever_tip(lever_a(f)))
exec(open(os.path.join(HERE, "03b_fx_camera.py")).read())
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("SAVED", OUT)
