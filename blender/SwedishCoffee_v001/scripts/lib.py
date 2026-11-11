# SwedishCoffee shared helpers (exec'd by build scripts).  exec(open(LIB).read())
import bpy, math, os, glob, random
from mathutils import Vector, Matrix, Euler, Quaternion
PIPE = "/home/user/Muhammed/blender/pipeline/anim_lib.py"
exec(open(PIPE).read())
R_ = math.radians
sc = bpy.context.scene
SCR = "/tmp/claude-0/-home-user-Muhammed/cfa42660-5965-5bab-81cb-f3c15671f0c9/scratchpad"
GLB = SCR + "/glb"; PH = SCR + "/ph"
V = Vector

def coll(name, parent=None):
    c = bpy.data.collections.get(name)
    if not c:
        c = bpy.data.collections.new(name); (parent or sc.collection).children.link(c)
    return c

def link(o, c):
    for u in list(o.users_collection): u.objects.unlink(o)
    c.objects.link(o)

# ------------------------------------------------------------- assets
LIBC = None
def asset(name, size=None, axis="z", rot=(0, 0, 0), file=None):
    """import GLB once, join, bottom-centre at origin, scale so dimension[axis]==size. Returns template (in hidden ASSETS coll)."""
    global LIBC
    if LIBC is None:
        LIBC = coll("ASSETS"); LIBC.hide_render = True; LIBC.hide_viewport = True
    if name in bpy.data.objects: return bpy.data.objects[name]
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=file or f"{GLB}/{name}.glb")
    new = [o for o in bpy.data.objects if o not in before]
    ms = [o for o in new if o.type == 'MESH']
    for o in ms:
        mw = o.matrix_world.copy(); o.parent = None; o.matrix_world = mw
    bpy.ops.object.select_all(action='DESELECT')
    for o in ms: o.select_set(True)
    bpy.context.view_layer.objects.active = ms[0]
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    if len(ms) > 1: bpy.ops.object.join()
    ob = bpy.context.view_layer.objects.active
    for o in new:
        try:
            if o != ob: bpy.data.objects.remove(o)
        except ReferenceError: pass
    ob.name = name; ob.data.name = name
    me = ob.data
    me.transform(Euler([R_(a) for a in rot]).to_matrix().to_4x4())
    pts = [v.co for v in me.vertices]
    mn = V([min(p[i] for p in pts) for i in range(3)]); mx = V([max(p[i] for p in pts) for i in range(3)])
    me.transform(Matrix.Translation(-V(((mn.x + mx.x) / 2, (mn.y + mx.y) / 2, mn.z))))
    if size:
        d = (mx - mn)["xyz".index(axis)]; me.transform(Matrix.Scale(size / d, 4))
    for p in me.polygons: p.use_smooth = True
    link(ob, LIBC)
    return ob

def inst(tmpl, c, loc=(0, 0, 0), rz=0.0, s=1.0, name=None, rx=0.0, ry=0.0):
    o = bpy.data.objects.new(name or tmpl.name + "_i", tmpl.data)
    o.location = loc; o.rotation_euler = (R_(rx), R_(ry), R_(rz)); o.scale = (s, s, s)
    c.objects.link(o); return o

# ------------------------------------------------------------- materials
def _img(path, non_color=False):
    im = bpy.data.images.load(path, check_existing=True)
    if non_color: im.colorspace_settings.name = "Non-Color"
    return im

def pbr(name, tex, scale=1.0, tint=None, rough_mul=1.0, disp=0.0, coord="UV", bump=0.6, hsv=None):
    """Poly Haven texture set -> principled. coord: UV | Object | Generated (box projected)."""
    m = bpy.data.materials.get(name)
    if m: return m
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; N, L = nt.nodes, nt.links
    bs = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord"); mp = N.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (scale,) * 3
    L.new(tc.outputs[coord], mp.inputs["Vector"])
    fs = sorted(glob.glob(f"{PH}/{tex}/**/*.*", recursive=True))
    def f(k): return next((x for x in fs if "_" + k + "_" in os.path.basename(x).lower()), None)
    proj = 'BOX' if coord != "UV" else 'FLAT'
    def T(path, nc):
        t = N.new("ShaderNodeTexImage"); t.image = _img(path, nc); t.projection = proj; t.projection_blend = 0.25
        L.new(mp.outputs[0], t.inputs[0]); return t
    d = f("diff")
    if d:
        t = T(d, False); col = t.outputs[0]
        if hsv:
            h = N.new("ShaderNodeHueSaturation"); h.inputs["Hue"].default_value, h.inputs["Saturation"].default_value, h.inputs["Value"].default_value = hsv
            L.new(col, h.inputs["Color"]); col = h.outputs[0]
        if tint:
            mx = N.new("ShaderNodeMix"); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs[0].default_value = 1.0
            mx.inputs["B"].default_value = (*tint, 1); L.new(col, mx.inputs["A"]); col = mx.outputs["Result"]
        L.new(col, bs.inputs["Base Color"])
    r = f("rough")
    if r:
        t = T(r, True); mt = N.new("ShaderNodeMath"); mt.operation = 'MULTIPLY'; mt.inputs[1].default_value = rough_mul
        L.new(t.outputs[0], mt.inputs[0]); L.new(mt.outputs[0], bs.inputs["Roughness"])
    n = f("nor_gl")
    if n:
        t = T(n, True); nm = N.new("ShaderNodeNormalMap"); nm.inputs["Strength"].default_value = bump
        L.new(t.outputs[0], nm.inputs["Color"]); L.new(nm.outputs[0], bs.inputs["Normal"])
    dp = f("disp")
    if dp and disp > 0:
        t = T(dp, True); dn = N.new("ShaderNodeDisplacement"); dn.inputs["Scale"].default_value = disp
        L.new(t.outputs[0], dn.inputs["Height"]); L.new(dn.outputs[0], N["Material Output"].inputs["Displacement"])
        m.displacement_method = 'BOTH'
    return m

def simple(name, col, rough=0.5, metal=0.0, emit=None, ew=0.0, trans=0.0, ior=1.45, alpha=1.0):
    m = bpy.data.materials.get(name)
    if m: return m
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*col, 1); b.inputs["Roughness"].default_value = rough; b.inputs["Metallic"].default_value = metal
    b.inputs["Transmission Weight"].default_value = trans; b.inputs["IOR"].default_value = ior; b.inputs["Alpha"].default_value = alpha
    if emit: b.inputs["Emission Color"].default_value = (*emit, 1); b.inputs["Emission Strength"].default_value = ew
    return m

def setmat(o, m):
    o.data.materials.clear(); o.data.materials.append(m); return o

def plane(name, c, size, loc, mat, rot=(0, 0, 0), sub=0):
    bm = bpy.data.meshes.new(name)
    sx, sy = size if isinstance(size, tuple) else (size, size)
    bm.from_pydata([(-sx/2, -sy/2, 0), (sx/2, -sy/2, 0), (sx/2, sy/2, 0), (-sx/2, sy/2, 0)], [], [(0, 1, 2, 3)])
    bm.uv_layers.new(); uv = bm.uv_layers[0].data
    for i, (u, v) in enumerate([(0, 0), (sx, 0), (sx, sy), (0, sy)]): uv[i].uv = (u, v)
    o = bpy.data.objects.new(name, bm); c.objects.link(o); o.location = loc; o.rotation_euler = [R_(a) for a in rot]
    setmat(o, mat)
    if sub:
        md = o.modifiers.new("sub", 'SUBSURF'); md.subdivision_type = 'SIMPLE'; md.levels = md.render_levels = sub
    return o

def box(name, c, dims, loc, mat, rz=0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.active_object; o.name = name; o.scale = dims; o.rotation_euler.z = R_(rz)
    bpy.ops.object.transform_apply(scale=True)
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.uv.cube_project(cube_size=1.0); bpy.ops.object.mode_set(mode='OBJECT')
    link(o, c); setmat(o, mat); return o

# ------------------------------------------------------------- visibility
ALLVIS = {}
def vis(c, on, off):
    """collection c renders only for frames [on, off)"""
    ALLVIS[c.name] = (on, off)
    def objs(cc):
        for o in cc.objects: yield o
        for ch in cc.children: yield from objs(ch)
    for o in objs(c):
        for f, h in ((1, on > 1), (on, False), (off, True)):
            if f < 1: continue
            o.hide_render = h; o.keyframe_insert("hide_render", frame=f)
        if o.animation_data and o.animation_data.action:
            for fc in o.animation_data.action.fcurves if hasattr(o.animation_data.action, "fcurves") else []:
                pass

# ------------------------------------------------------------- humans
CAST = "/home/user/Muhammed/blender/SwedishCoffee_v001/assets/cast.blend"
BASE = {}
def base_human(name):
    if name in BASE: return BASE[name]
    with bpy.data.libraries.load(CAST, link=False) as (src, dst):
        dst.objects = [n for n in src.objects if n == name or n.startswith(name + ".")]
    hc = coll("HUMAN_BASE"); hc.hide_render = True; hc.hide_viewport = False
    arm = None
    for o in dst.objects:
        hc.objects.link(o)
        if o.type == 'ARMATURE': arm = o
    restyle(arm)
    R = make_human_ctrl(arm)
    hc.hide_viewport = True
    BASE[name] = arm; return arm

def clone(base, name, c, loc=(0, 0, 0), rz=0.0):
    a = BASE[base] if isinstance(base, str) else base
    n = a.copy(); n.name = name; n.animation_data_clear(); c.objects.link(n)
    for pb in n.pose.bones:
        for k in pb.constraints:
            if hasattr(k, "target") and k.target == a: k.target = n
            if hasattr(k, "pole_target") and k.pole_target == a: k.pole_target = n
    for ch in a.children:
        m = ch.copy(); m.name = name + "." + ch.name.split(".", 1)[-1]; c.objects.link(m)
        m.parent = n
        for md in m.modifiers:
            if md.type == 'ARMATURE': md.object = n
    n.location = loc; n.rotation_euler = (0, 0, R_(rz))
    for pb in n.pose.bones:
        pb.rotation_mode = 'QUATERNION'; pb.rotation_quaternion = (1, 0, 0, 0); pb.location = (0, 0, 0)
    return n

# ---- period costume: replace modern clothing materials with zoned period fabric (coat / breeches / stockings)
COSTUME = {}
def costume_mat(key, coat, breech, stock=(0.85, 0.83, 0.78), coat_tex="wool_boucle", knee=0.27, waist=0.52, skirt=False):
    nm = "cos_" + key
    if nm in bpy.data.materials: return bpy.data.materials[nm]
    m = bpy.data.materials.new(nm); m.use_nodes = True
    nt = m.node_tree; N, L = nt.nodes, nt.links; bs = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord"); sep = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs["Generated"], sep.inputs[0])
    def tex(t, sc_, nc):
        fs = sorted(glob.glob(f"{PH}/{t}/**/*.*", recursive=True)); p = next((x for x in fs if "_" + nc + "_" in os.path.basename(x).lower()), None)
        mp = N.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (sc_,) * 3; L.new(tc.outputs["UV"], mp.inputs[0])
        ti = N.new("ShaderNodeTexImage"); ti.image = _img(p, nc != "diff"); L.new(mp.outputs[0], ti.inputs[0]); return ti
    def zone(col, t, s_):
        d = tex(t, s_, "diff"); bw = N.new("ShaderNodeRGBToBW"); L.new(d.outputs[0], bw.inputs[0])
        mr = N.new("ShaderNodeMapRange"); mr.inputs[3].default_value = 0.55; mr.inputs[4].default_value = 1.25; L.new(bw.outputs[0], mr.inputs[0])
        mx = N.new("ShaderNodeMix"); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs[0].default_value = 1
        cc = N.new("ShaderNodeCombineColor"); L.new(mr.outputs[0], cc.inputs[0]); L.new(mr.outputs[0], cc.inputs[1]); L.new(mr.outputs[0], cc.inputs[2])
        mx.inputs["A"].default_value = (*col, 1); L.new(cc.outputs[0], mx.inputs["B"]); return mx.outputs["Result"]
    c_coat = zone(coat, coat_tex, 6); c_br = zone(breech, "wool_boucle" if not skirt else coat_tex, 6); c_st = zone(stock, "rough_linen", 10)
    def step(edge, a, b):
        mr = N.new("ShaderNodeMapRange"); mr.inputs[1].default_value = edge - 0.005; mr.inputs[2].default_value = edge + 0.005
        L.new(sep.outputs["Z"], mr.inputs[0])
        mx = N.new("ShaderNodeMix"); mx.data_type = 'RGBA'; L.new(mr.outputs[0], mx.inputs[0]); L.new(a, mx.inputs["A"]); L.new(b, mx.inputs["B"]); return mx.outputs["Result"]
    lower = step(knee, c_st, c_br)
    sub = N.new("ShaderNodeMath"); sub.operation = 'SUBTRACT'; sub.inputs[1].default_value = 0.5; L.new(sep.outputs["X"], sub.inputs[0])
    ab = N.new("ShaderNodeMath"); ab.operation = 'ABSOLUTE'; L.new(sub.outputs[0], ab.inputs[0])
    gt = N.new("ShaderNodeMath"); gt.operation = 'GREATER_THAN'; gt.inputs[1].default_value = 0.2; L.new(ab.outputs[0], gt.inputs[0])
    def step(edge, a, b, arm=False):
        mr = N.new("ShaderNodeMapRange"); mr.inputs[1].default_value = edge - 0.005; mr.inputs[2].default_value = edge + 0.005
        L.new(sep.outputs["Z"], mr.inputs[0])
        fac = mr.outputs[0]
        if arm:
            mx_ = N.new("ShaderNodeMath"); mx_.operation = 'MAXIMUM'; L.new(fac, mx_.inputs[0]); L.new(gt.outputs[0], mx_.inputs[1]); fac = mx_.outputs[0]
        mx = N.new("ShaderNodeMix"); mx.data_type = 'RGBA'; L.new(fac, mx.inputs[0]); L.new(a, mx.inputs["A"]); L.new(b, mx.inputs["B"]); return mx.outputs["Result"]
    full = step(waist, lower, c_coat, True) if not skirt else step(knee * 0.4, c_st, c_coat, True)
    L.new(full, bs.inputs["Base Color"]); bs.inputs["Roughness"].default_value = 0.85
    bs.inputs["Sheen Weight"].default_value = 0.4
    n = tex("wool_boucle", 6, "nor_gl"); nm = N.new("ShaderNodeNormalMap"); nm.inputs["Strength"].default_value = 0.5
    L.new(n.outputs[0], nm.inputs["Color"]); L.new(nm.outputs[0], bs.inputs["Normal"])
    return m

STYLE = {
 "TwinA": ("prisoner", (0.62, 0.55, 0.44), (0.62, 0.55, 0.44), (0.40, 0.33, 0.25), "rough_linen", 0.30, 0.62),
 "TwinB": ("prisoner", (0.62, 0.55, 0.44), (0.62, 0.55, 0.44), (0.40, 0.33, 0.25), "rough_linen", 0.30, 0.62),
 "TwinA_old": ("twinold", (0.16, 0.20, 0.30), (0.16, 0.20, 0.30), (0.80, 0.78, 0.72), "wool_boucle", 0.30, 0.62),
 "TwinB_old": ("twinoldB", (0.30, 0.18, 0.12), (0.30, 0.18, 0.12), (0.80, 0.78, 0.72), "wool_boucle", 0.30, 0.62),
 "TwinA_vold": ("twinvold", (0.20, 0.17, 0.13), (0.20, 0.17, 0.13), (0.80, 0.78, 0.72), "wool_boucle", 0.30, 0.62),
 "King": ("king", (0.08, 0.12, 0.35), (0.08, 0.12, 0.35), (0.92, 0.90, 0.86), "velour_velvet", 0.30, 0.60),
 "Guard": ("guard", (0.08, 0.16, 0.42), (0.08, 0.16, 0.42), (0.75, 0.70, 0.55), "wool_boucle", 0.32, 0.62),
 "Doctor1": ("doc", (0.07, 0.06, 0.06), (0.07, 0.06, 0.06), (0.75, 0.73, 0.70), "wool_boucle", 0.30, 0.60),
 "Doctor2": ("doc2", (0.18, 0.12, 0.08), (0.18, 0.12, 0.08), (0.75, 0.73, 0.70), "wool_boucle", 0.30, 0.60),
 "Woman": ("woman", (0.35, 0.10, 0.12), (0.35, 0.10, 0.12), (0.8, 0.78, 0.74), "velour_velvet", 0.30, 0.62),
 "Townsman": ("towns", (0.28, 0.22, 0.14), (0.28, 0.22, 0.14), (0.65, 0.62, 0.55), "wool_boucle", 0.30, 0.62),
 "Townswoman": ("townsw", (0.22, 0.28, 0.20), (0.22, 0.28, 0.20), (0.7, 0.68, 0.62), "rough_linen", 0.30, 0.62),
}
CLOTH_KEYS = ("suit", "casual", "worksuit", "elegant")
def restyle(arm):
    st = STYLE[arm.name]
    for ch in arm.children:
        tag = ch.name.split(".")[-1]
        if any(k in tag for k in CLOTH_KEYS):
            setmat(ch, costume_mat(st[0], st[1], st[2], st[3], st[4], st[5], st[6], skirt=arm.name.startswith(("Woman", "Townsw"))))
        if tag.startswith("shoes"):
            setmat(ch, pbr("shoe_leather", "brown_leather", 3, tint=(0.25, 0.2, 0.17), rough_mul=0.7))

# ---- face: MPFB face bones
def face(R, f, brow=0.0, lids=0.0, jaw=0.0, smile=0.0, frown=0.0):
    """brow +up/-down(angry) ; lids +close ; jaw open deg ; smile/frown 0..1"""
    P = R.PB
    def loc(n, v):
        if n in P: P[n].location = v; P[n].keyframe_insert("location", frame=f, group=n)
    def rot(n, ax, d):
        if n in P:
            P[n].rotation_mode = 'QUATERNION'; P[n].rotation_quaternion = Quaternion(V(ax), R_(d)); P[n].keyframe_insert("rotation_quaternion", frame=f, group=n)
    for s in "LR":
        loc("oculi01." + s, (0, brow * 0.006, 0)); loc("oculi02." + s, (0, brow * 0.004 + (-0.004 if brow < 0 else 0), 0))
        rot("orbicularis03." + s, (1, 0, 0), -lids * 25); rot("orbicularis04." + s, (1, 0, 0), lids * 10)
        loc("risorius03." + s, (0, smile * 0.006 - frown * 0.005, 0)); loc("levator06." + s, (0, smile * 0.003, 0))
    rot("jaw", (1, 0, 0), jaw)

# ------------------------------------------------------------- actor wrapper (IK everywhere, body frame: forward = -Y, left = +X)
class Actor:
    def __init__(self, arm):
        self.a = arm; self.R = Rig(arm); self.H = Human(self.R)
        self.pos = V((0, 0)); self.yaw = 0.0; self.z = 0.0
    def W(self, p, pos=None, yaw=None):
        pos = self.pos if pos is None else pos; yaw = self.yaw if yaw is None else yaw
        q = Matrix.Rotation(R_(yaw), 3, 'Z') @ V(p)
        return V((pos[0] + q.x, pos[1] + q.y, self.z + q.z))
    def Wd(self, d, yaw=None):
        return Matrix.Rotation(R_(self.yaw if yaw is None else yaw), 3, 'Z') @ V(d)
    def stand(self, f, pos=None, yaw=None, crouch=0.0, flex=0.0, twist=0.0, side=0.0, head=(0, 0), lean=0.0, feet=True, rootz=None, feetpos=None):
        if pos is not None: self.pos = V(pos)
        if yaw is not None: self.yaw = yaw
        rz = self.H.root_head.z - crouch if rootz is None else rootz
        self.H.key_root(f, V((self.pos[0], self.pos[1], self.z + rz)), yaw=self.yaw, flex=lean, side=side)
        self.H.key_spine(f, flex=flex, twist=twist, head=head)
        if feet:
            for s in "LR":
                if feetpos and s in feetpos: xy = self.W(feetpos[s]).to_2d()
                else: xy = self.H.foot_xy(s, self.pos, self.yaw)
                self.H.key_foot(s, f, xy, self.yaw)
    def hand(self, f, s, p, d=(0, 0, -1), n=None, pole=None):
        sx = 1 if s == "L" else -1
        if n is None: n = (-sx, 0, 0)
        if pole is None: pole = (0.45 * sx, 0.5, 1.0)
        self.H.key_hand(s, f, self.W(p), self.Wd(d).normalized(), self.Wd(n).normalized(), pole=self.W(pole))
    def arms_down(self, f, sway=0.0):
        for s in "LR":
            sx = 1 if s == "L" else -1
            self.hand(f, s, (0.24 * sx, -0.02 + sway * sx, 0.86), d=(0.05 * sx, -0.05, -1), n=(-sx, 0, 0), pole=(0.3 * sx, 0.6, 1.1))
    def face(self, f, **k): face(self.R, f, **k)
    def sit(self, f, seat_z=0.47, knee_fwd=0.48, flex=8.0, twist=0.0, head=(0, 0)):
        """seated on a chair whose seat front is ~0.1 in front of root; feet on floor in front"""
        self.H.key_root(f, V((*self.W((0, 0.05, 0)).to_2d(), self.z + seat_z + 0.06)), yaw=self.yaw, flex=-4)
        self.H.key_spine(f, flex=flex, twist=twist, head=head)
        for s in "LR":
            sx = 1 if s == "L" else -1
            self.H.key_foot(s, f, self.W((0.13 * sx, -knee_fwd, 0)).to_2d(), self.yaw)
            pb = self.R.PB["Pole_knee." + s]; n_ = "Pole_knee." + s
            pole = self.W((0.13 * sx, -1.2, 0.6))
            pb.location = self.R.rest(n_).to_3x3().inverted() @ (pole - self.R.BN[n_].head_local); pb.keyframe_insert("location", frame=f, group=n_)

LOCALROOT = [None]
def attach(o, arm, bone, f=None, local=False):
    """Child Of to bone keeping current world transform (evaluated at frame f). local=True: o was placed in set-local coords"""
    if local and LOCALROOT[0] is not None: o.matrix_world = LOCALROOT[0].matrix_world @ o.matrix_world
    if f is not None: sc.frame_set(f)
    bpy.context.view_layer.update()
    c = o.constraints.new('CHILD_OF'); c.target = arm; c.subtarget = bone
    c.inverse_matrix = (arm.matrix_world @ arm.pose.bones[bone].matrix).inverted()
    return c

def hand_world(arm, s, f=None):
    if f is not None: sc.frame_set(f)
    pb = arm.pose.bones["finger3-1." + s]; return arm.matrix_world @ pb.head

def ph_model(name, size=None, axis="z", rot=(0, 0, 0)):
    """Poly Haven .blend model -> joined template"""
    global LIBC
    if LIBC is None:
        LIBC = coll("ASSETS"); LIBC.hide_render = True; LIBC.hide_viewport = True
    if name in bpy.data.objects and bpy.data.objects[name].users_collection[0] == LIBC: return bpy.data.objects[name]
    path = glob.glob(f"{PH}/{name}/*.blend")[0]
    with bpy.data.libraries.load(path, link=False) as (src, dst):
        dst.objects = list(src.objects)
    ms = [o for o in dst.objects if o and o.type == 'MESH']
    for o in ms: sc.collection.objects.link(o)
    bpy.context.view_layer.update()
    for o in ms:
        mw = o.matrix_world.copy(); o.parent = None; o.matrix_world = mw
    bpy.ops.object.select_all(action='DESELECT')
    for o in ms: o.select_set(True)
    bpy.context.view_layer.objects.active = ms[0]
    bpy.ops.object.make_single_user(object=True, obdata=True)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    if len(ms) > 1: bpy.ops.object.join()
    ob = bpy.context.view_layer.objects.active; ob.name = name
    me = ob.data; me.transform(Euler([R_(a) for a in rot]).to_matrix().to_4x4())
    pts = [v.co for v in me.vertices]
    mn = V([min(p[i] for p in pts) for i in range(3)]); mx = V([max(p[i] for p in pts) for i in range(3)])
    me.transform(Matrix.Translation(-V(((mn.x + mx.x) / 2, (mn.y + mx.y) / 2, mn.z))))
    if size:
        d = (mx - mn)["xyz".index(axis)]; me.transform(Matrix.Scale(size / d, 4))
    link(ob, LIBC); return ob

GRIP_AX = (1, 0, 0)
def grip(R, f, s, amt=1.0, thumb=0.6):
    """curl fingers (amt 0 open .. 1 fist) for holding a handle/cup"""
    for fi in (2, 3, 4, 5):
        for j, w in ((1, 35), (2, 45), (3, 30)):
            n = "finger%d-%d.%s" % (fi, j, s)
            if n in R.PB:
                pb = R.PB[n]; pb.rotation_mode = 'QUATERNION'
                pb.rotation_quaternion = Quaternion(V(GRIP_AX), R_(w * amt)); pb.keyframe_insert("rotation_quaternion", frame=f, group=n)
    for j, w in ((2, 25), (3, 25)):
        n = "finger1-%d.%s" % (j, s)
        if n in R.PB:
            pb = R.PB[n]; pb.rotation_mode = 'QUATERNION'
            pb.rotation_quaternion = Quaternion(V(GRIP_AX), R_(w * thumb)); pb.keyframe_insert("rotation_quaternion", frame=f, group=n)
