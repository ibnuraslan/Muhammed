"""Procedural humans for Blender, built from MakeHuman's CC0 base mesh, morph targets and skeleton.

Everything is driven from code: body shape (age, gender, muscle, weight, height), a rigged
armature fitted to that shape, fitted eyes / eyebrows / eyelashes, posing helpers and
physically based skin.

Set MH_DATA to the MakeHuman 1.x `data` directory (see README).
"""
import os, json, math
import numpy as np
import bpy
from mathutils import Vector, Matrix, Quaternion

MH = os.environ.get("MH_DATA", "")
_TARGETS = None


def _unpack(strbuf, idx):
    s = strbuf.tobytes(); idx = list(idx) + [len(s)]
    return [s[idx[i]:idx[i + 1]].decode("utf8") for i in range(len(idx) - 1)]


def _targets():
    global _TARGETS
    if _TARGETS is None:
        _TARGETS = np.load(os.path.join(MH, "targets.npz"))
    return _TARGETS


def to_bl(c):
    """MakeHuman (decimetres, Y up) -> Blender (metres, Z up)."""
    c = np.asarray(c, np.float64)
    return np.stack([c[..., 0], -c[..., 2], c[..., 1]], -1) * 0.1


# ----------------------------------------------------------------------------- shape
def _lin3(v):
    """min/average/max weights for a [0,1] slider."""
    if v < 0.5:
        return {"min": 1 - 2 * v, "average": 2 * v, "max": 0.0}
    return {"min": 0.0, "average": 2 - 2 * v, "max": 2 * v - 1}


def _age_w(a):
    if a < 0.1875:
        return {"baby": 1 - a / 0.1875, "child": a / 0.1875, "young": 0, "old": 0}
    if a < 0.5:
        c = (0.5 - a) / 0.3125
        return {"baby": 0, "child": c, "young": 1 - c, "old": 0}
    return {"baby": 0, "child": 0, "young": 1 - (a - 0.5) * 2, "old": (a - 0.5) * 2}


def age_slider(years):
    if years < 25:
        return max(0.0, (years - 1) / 24 * 0.5)
    return 0.5 + min(1.0, (years - 25) / 65) * 0.5


def macro_targets(gender=1.0, years=25, muscle=0.5, weight=0.5, height=0.5, race="caucasian"):
    g = {"female": 1 - gender, "male": gender}
    ag = _age_w(age_slider(years))
    mu = _lin3(muscle); we = _lin3(weight)
    out = {}
    for gk, gv in g.items():
        for ak, av in ag.items():
            if gv * av == 0:
                continue
            out[f"targets/macrodetails/{race}-{gk}-{ak}"] = gv * av
            for mk, mv in mu.items():
                for wk, wv in we.items():
                    w = gv * av * mv * wv
                    if w == 0:
                        continue
                    out[f"targets/macrodetails/universal-{gk}-{ak}-{mk}muscle-{wk}weight"] = w
                    if height != 0.5:
                        hk, hv = ("maxheight", (height - 0.5) * 2) if height > 0.5 else ("minheight", (0.5 - height) * 2)
                        out[f"targets/macrodetails/height/{gk}-{ak}-{mk}muscle-{wk}weight-{hk}"] = w * hv
    return out


def apply_targets(coord, targets):
    T = _targets()
    c = coord.copy()
    for name, w in targets.items():
        if w == 0 or (name + ".index") not in T.files:
            continue
        idx = T[name + ".index"]
        if len(idx) == 0:
            continue
        c[idx] += T[name + ".vector"].astype(np.float32) * 1e-3 * w
    return c


def list_targets(prefix):
    return sorted({f[:-6] for f in _targets().files if f.startswith(prefix) and f.endswith(".index")})


# ----------------------------------------------------------------------------- mesh
class Base:
    def __init__(self):
        b = np.load(os.path.join(MH, "3dobjs", "base.npz"))
        self.coord = b["coord"].astype(np.float32)
        self.fvert = b["fvert"].astype(np.int64)
        self.fuvs = b["fuvs"].astype(np.int64)
        self.texco = b["texco"].astype(np.float32)
        self.group = b["group"]
        self.groups = _unpack(b["fgstr"], b["fgidx"])

    def faces_in(self, pred):
        gi = np.array([i for i, n in enumerate(self.groups) if pred(n)])
        return np.isin(self.group, gi)


def build_mesh(name, verts_bl, fvert, fuvs=None, texco=None, smooth=True):
    """Quads (MakeHuman stores triangles as quads with a repeated last index)."""
    me = bpy.data.meshes.new(name)
    tri = fvert[:, 3] == fvert[:, 2]
    polys = [list(f[:3]) if t else list(f) for f, t in zip(fvert, tri)]
    me.from_pydata(verts_bl.tolist(), [], polys)
    if fuvs is not None and texco is not None:
        uv = me.uv_layers.new(name="UVMap")
        loops = np.concatenate([fu[:3] if t else fu for fu, t in zip(fuvs, tri)])
        uv.data.foreach_set("uv", texco[loops].ravel())
    me.polygons.foreach_set("use_smooth", np.full(len(me.polygons), smooth))
    me.update()
    o = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(o)
    return o


# ----------------------------------------------------------------------------- skeleton
class Rig:
    def __init__(self, coord_mh):
        sk = json.load(open(os.path.join(MH, "rigs", "default.mhskel")))
        self.sk = sk
        bc = to_bl(coord_mh)
        self.joint = {k: bc[np.array(v)].mean(0) for k, v in sk["joints"].items()}
        wf = json.load(open(os.path.join(MH, "rigs", "default_weights.mhw")))["weights"]
        self.weights = wf
        self.bones = list(sk["bones"].keys())

    def build(self, name="Armature"):
        arm = bpy.data.armatures.new(name)
        o = bpy.data.objects.new(name, arm); bpy.context.collection.objects.link(o)
        bpy.context.view_layer.objects.active = o
        bpy.ops.object.mode_set(mode="EDIT")
        eb = {}
        for bn, bd in self.sk["bones"].items():
            b = arm.edit_bones.new(bn)
            b.head = Vector(self.joint[bd["head"]]); b.tail = Vector(self.joint[bd["tail"]])
            if (b.tail - b.head).length < 1e-4:
                b.tail = b.head + Vector((0, 0, 0.01))
            eb[bn] = b
        for bn, bd in self.sk["bones"].items():
            if bd["parent"]:
                eb[bn].parent = eb[bd["parent"]]
        bpy.ops.object.mode_set(mode="OBJECT")
        self.obj = o
        return o

    def bone_matrix(self, n_verts):
        """Dense (n_verts x n_bones) weight matrix, normalised."""
        W = np.zeros((n_verts, len(self.bones)), np.float32)
        for j, bn in enumerate(self.bones):
            for v, w in self.weights.get(bn, []):
                if v < n_verts:
                    W[v, j] = w
        s = W.sum(1, keepdims=True); W /= np.maximum(s, 1e-8)
        return W

    def skin(self, mesh_obj, W):
        for j, bn in enumerate(self.bones):
            nz = np.nonzero(W[:, j] > 1e-4)[0]
            if len(nz) == 0:
                continue
            vg = mesh_obj.vertex_groups.new(name=bn)
            for v in nz:
                vg.add([int(v)], float(W[v, j]), "REPLACE")
        mod = mesh_obj.modifiers.new("Armature", "ARMATURE"); mod.object = self.obj
        mesh_obj.parent = self.obj


def rotate_bone(arm_obj, bone, axis, deg, space="WORLD"):
    """Rotate a pose bone about a world-space axis through its head (posing that ignores bone roll)."""
    bpy.context.view_layer.update()
    pb = arm_obj.pose.bones[bone]
    M = arm_obj.matrix_world @ pb.matrix
    head = M.to_translation()
    ax = Vector(axis).normalized()
    if space == "LOCAL":  # axis given in the bone's own frame (x=side, y=along bone, z=forward-ish)
        ax = (M.to_3x3() @ ax).normalized()
    R = Matrix.Translation(head) @ Quaternion(ax, math.radians(deg)).to_matrix().to_4x4() @ Matrix.Translation(-head)
    pb.matrix = arm_obj.matrix_world.inverted() @ (R @ M)
    bpy.context.view_layer.update()


def aim_bone(arm_obj, bone, direction, deg_limit=None):
    """Swing a bone so it points along a world direction (shortest rotation)."""
    bpy.context.view_layer.update()
    pb = arm_obj.pose.bones[bone]
    M = arm_obj.matrix_world @ pb.matrix
    cur = (M.to_3x3() @ Vector((0, 1, 0))).normalized()
    d = Vector(direction).normalized()
    ax = cur.cross(d)
    if ax.length < 1e-6:
        return
    ang = math.degrees(cur.angle(d))
    rotate_bone(arm_obj, bone, ax, ang)


# ----------------------------------------------------------------------------- proxies (eyes, brows, lashes, clothes)
class Proxy:
    def __init__(self, path):
        p = np.load(path)
        self.ref = p["ref_vIdxs"].astype(np.int64)
        self.w = p["weights"].astype(np.float32)
        if self.ref.ndim == 1:
            r = np.zeros((len(self.ref), 3), np.int64); r[:, 0] = self.ref; self.ref = r
            w = np.zeros((len(self.w), 3), np.float32); w[:, 0] = self.w; self.w = w
            self.off = np.zeros((len(self.ref), 3), np.float32)
        else:
            self.off = p["offsets"].astype(np.float32)
        self.scale = None
        if "tmat_scale" in p.files:
            sc, si = p["tmat_scale"], p["tmat_scale_idx"]
            self.scale = [(int(si[2 * i]), int(si[2 * i + 1]), float(sc[i])) for i in range(3)]
        d = os.path.dirname(path)
        self.obj_file = os.path.join(d, os.path.basename(str(p["obj_file"].tobytes(), "utf8")))
        self.mat_file = os.path.join(d, os.path.basename(str(p["material_file"].tobytes(), "utf8"))) if "material_file" in p.files else None
        m = np.load(os.path.splitext(self.obj_file)[0] + ".npz")
        self.fvert = m["fvert"].astype(np.int64); self.fuvs = m["fuvs"].astype(np.int64); self.texco = m["texco"].astype(np.float32)

    def fit(self, hc):
        M = np.identity(3)
        if self.scale:
            for n, (a, b, den) in enumerate(self.scale):
                M[n, n] = abs(hc[a][n] - hc[b][n]) / den
        return (hc[self.ref[:, 0]] * self.w[:, 0, None] + hc[self.ref[:, 1]] * self.w[:, 1, None]
                + hc[self.ref[:, 2]] * self.w[:, 2, None] + (M @ self.off.T).T)

    def weights_from(self, Wbody):
        return (Wbody[self.ref[:, 0]] * self.w[:, 0, None] + Wbody[self.ref[:, 1]] * self.w[:, 1, None]
                + Wbody[self.ref[:, 2]] * self.w[:, 2, None])


def read_mhmat(path):
    out = {}
    if not path or not os.path.exists(path):
        return out
    for line in open(path, encoding="utf8", errors="ignore"):
        parts = line.strip().split(None, 1)
        if len(parts) == 2 and not parts[0].startswith("#"):
            out[parts[0]] = parts[1]
    return out


def tex_path(base_dir, rel):
    for cand in (os.path.join(base_dir, rel), os.path.join(base_dir, os.path.basename(rel)),
                 os.path.join(MH, rel), os.path.join(MH, "skins", "textures", os.path.basename(rel))):
        if os.path.exists(cand):
            return cand
    return None


def alpha_material(name, tex, color_mul=(1, 1, 1), rough=0.6):
    m = bpy.data.materials.new(name); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links
    p = N["Principled BSDF"]
    t = N.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(tex)
    mul = N.new("ShaderNodeMix"); mul.data_type = 'RGBA'; mul.blend_type = 'MULTIPLY'; mul.inputs['Factor'].default_value = 1
    L.new(t.outputs['Color'], mul.inputs[6]); mul.inputs[7].default_value = (*color_mul, 1)
    L.new(mul.outputs[2], p.inputs['Base Color']); L.new(t.outputs['Alpha'], p.inputs['Alpha'])
    p.inputs['Roughness'].default_value = rough
    return m


# ----------------------------------------------------------------------------- skin
def skin_material(name, tex=None, tint=(1, 1, 1), rough=0.48, sss=0.25, pore_scale=1.0, bump=0.25,
                  color=None, sss_radius=(0.9, 0.35, 0.2)):
    m = bpy.data.materials.new(name); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links
    p = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord")
    if tex:
        t = N.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(tex)
        mul = N.new("ShaderNodeMix"); mul.data_type = 'RGBA'; mul.blend_type = 'MULTIPLY'; mul.inputs['Factor'].default_value = 1
        L.new(t.outputs['Color'], mul.inputs[6]); mul.inputs[7].default_value = (*tint, 1)
        base = mul.outputs[2]
    else:
        rgb = N.new("ShaderNodeRGB"); rgb.outputs[0].default_value = (*(color or (0.6, 0.42, 0.33)), 1)
        base = rgb.outputs[0]
    # blotchy variation (redness / sallowness)
    bl = N.new("ShaderNodeTexNoise"); bl.inputs['Scale'].default_value = 18; bl.inputs['Detail'].default_value = 4
    L.new(tc.outputs['Object'], bl.inputs['Vector'])
    blm = N.new("ShaderNodeMix"); blm.data_type = 'RGBA'; blm.blend_type = 'OVERLAY'; blm.inputs['Factor'].default_value = 0.18
    L.new(base, blm.inputs[6]); L.new(bl.outputs['Color'], blm.inputs[7])
    L.new(blm.outputs[2], p.inputs['Base Color'])
    p.inputs['Subsurface Weight'].default_value = sss
    p.inputs['Subsurface Radius'].default_value = sss_radius
    p.inputs['Subsurface Scale'].default_value = 0.012
    p.inputs['Specular IOR Level'].default_value = 0.45
    # roughness breakup + pores
    pn = N.new("ShaderNodeTexNoise"); pn.inputs['Scale'].default_value = 900 * pore_scale; pn.inputs['Detail'].default_value = 3
    L.new(tc.outputs['Object'], pn.inputs['Vector'])
    vor = N.new("ShaderNodeTexVoronoi"); vor.inputs['Scale'].default_value = 1500 * pore_scale
    L.new(tc.outputs['Object'], vor.inputs['Vector'])
    hm = N.new("ShaderNodeMath"); hm.operation = 'MULTIPLY_ADD'; hm.inputs[1].default_value = 0.5
    L.new(pn.outputs['Fac'], hm.inputs[0]); L.new(vor.outputs['Distance'], hm.inputs[2])
    rr = N.new("ShaderNodeMapRange"); rr.inputs['To Min'].default_value = rough - 0.08; rr.inputs['To Max'].default_value = rough + 0.1
    L.new(pn.outputs['Fac'], rr.inputs['Value']); L.new(rr.outputs[0], p.inputs['Roughness'])
    bmp = N.new("ShaderNodeBump"); bmp.inputs['Strength'].default_value = bump; bmp.inputs['Distance'].default_value = 0.0004
    L.new(hm.outputs[0], bmp.inputs['Height']); L.new(bmp.outputs['Normal'], p.inputs['Normal'])
    m["bump_node"] = bmp.name
    return m


# ----------------------------------------------------------------------------- full human
class Human:
    def __init__(self, name="Human", gender=1.0, years=45, muscle=0.6, weight=0.45, height=0.45,
                 extra=None, eyebrows="eyebrow001", eyelashes="eyelashes01", eyes=True, skin="old_lightskinned_male_diffuse.png",
                 skin_tint=(1, 1, 1), shrink=0.0):
        self.base = Base()
        tg = macro_targets(gender, years, muscle, weight, height)
        if extra:
            tg.update(extra)
        hc = apply_targets(self.base.coord, tg)
        if shrink:
            hc = self._shrink(hc, shrink)
        # stand on the ground: lowest body vertex at z = 0 (Blender z = MakeHuman y)
        body_v = np.unique(self.base.fvert[self.base.faces_in(lambda n: n == "body")])
        hc = hc.copy(); hc[:, 1] -= hc[body_v, 1].min()
        self.hc = hc
        self.name = name
        self.rig = Rig(hc)
        self.arm = self.rig.build(name + "_rig")
        nv = len(hc)
        self.W = self.rig.bone_matrix(nv)
        body_faces = self.base.faces_in(lambda n: n == "body")
        self.body = build_mesh(name + "_body", to_bl(hc), self.base.fvert[body_faces], self.base.fuvs[body_faces], self.base.texco)
        st = tex_path(os.path.join(MH, "skins", "textures"), skin) if skin else None
        self.skin_mat = skin_material(name + "_skin", st, skin_tint)
        self.body.data.materials.append(self.skin_mat)
        sub = self.body.modifiers.new("Subsurf", "SUBSURF"); sub.levels = 1; sub.render_levels = 2
        self.rig.skin(self.body, self.W)
        self.body.modifiers.move(len(self.body.modifiers) - 1, 0)  # armature before subsurf
        self.parts = [self.body]
        if eyes:
            self._make_eyes()
        if eyebrows:
            self.add_proxy(os.path.join(MH, "eyebrows", eyebrows, eyebrows + ".mhpxy"), "brows", alpha=True)
        if eyelashes:
            self.add_proxy(os.path.join(MH, "eyelashes", eyelashes, eyelashes + ".mhpxy"), "lashes", alpha=True)

    @staticmethod
    def _shrink(hc, amount):
        """Desiccation: pull flesh toward a smoothed 'skeleton' so bones and tendons stand out."""
        return hc  # refined per shot via shape keys / displacement

    def add_proxy(self, path, label, alpha=False, eyes_material=False, mat=None, subsurf=0):
        px = Proxy(path)
        co = px.fit(self.hc)
        o = build_mesh(f"{self.name}_{label}", to_bl(co), px.fvert, px.fuvs, px.texco)
        mm = read_mhmat(px.mat_file)
        d = os.path.dirname(path)
        if mat is not None:
            o.data.materials.append(mat)
        elif eyes_material:
            o.data.materials.append(self._eye_material(o))
        elif alpha and mm.get("diffuseTexture"):
            tp = tex_path(d, mm["diffuseTexture"])
            if tp:
                o.data.materials.append(alpha_material(f"{self.name}_{label}_m", tp, (0.35, 0.28, 0.24)))
        if subsurf:
            s = o.modifiers.new("Subsurf", "SUBSURF"); s.levels = subsurf; s.render_levels = subsurf
        Wp = px.weights_from(self.W)
        self.rig.skin(o, Wp)
        self.body_proxy = px
        self.parts.append(o)
        return o, px

    def _make_eyes(self, iris_col=(0.30, 0.14, 0.045)):
        """Eyeballs placed in the sockets (from MakeHuman's eye proxy fit), parented to the head bone.
        Shading is procedural in the sphere's local space, so the iris always faces where the head faces."""
        px = Proxy(os.path.join(MH, "eyes", "high-poly", "high-poly.mhpxy"))
        co = to_bl(px.fit(self.hc))
        m = self._eye_material(iris_col)
        self.eyes = []
        for sel in (co[:, 0] > 0, co[:, 0] <= 0):
            P = co[sel]; c = (P.min(0) + P.max(0)) / 2; r = 0.0122
            c = c + np.array([0, 0.0015, 0])  # seat the ball slightly deeper behind the lids
            bpy.ops.mesh.primitive_uv_sphere_add(segments=64, ring_count=48, radius=r, location=tuple(c))
            e = bpy.context.active_object; e.name = self.name + "_eye"
            bpy.ops.object.shade_smooth()
            e.data.materials.append(m)
            mw = e.matrix_world.copy()
            e.parent = self.arm; e.parent_type = 'BONE'; e.parent_bone = "head"
            bpy.context.view_layer.update(); e.matrix_world = mw
            self.eyes.append(e); self.parts.append(e)

    def _eye_material(self, iris_col):
        m = bpy.data.materials.new(self.name + "_eye"); m.use_nodes = True
        N = m.node_tree.nodes; L = m.node_tree.links; p = N["Principled BSDF"]
        tc = N.new("ShaderNodeTexCoord")
        nrm = N.new("ShaderNodeVectorMath"); nrm.operation = 'NORMALIZE'; L.new(tc.outputs['Object'], nrm.inputs[0])
        dot = N.new("ShaderNodeVectorMath"); dot.operation = 'DOT_PRODUCT'; dot.inputs[1].default_value = (0, -1, 0)
        L.new(nrm.outputs[0], dot.inputs[0])
        ang = N.new("ShaderNodeMath"); ang.operation = 'ARCCOSINE'; ang.use_clamp = False; L.new(dot.outputs['Value'], ang.inputs[0])
        deg = N.new("ShaderNodeMath"); deg.operation = 'DEGREES'; L.new(ang.outputs[0], deg.inputs[0])
        mr = N.new("ShaderNodeMath"); mr.operation = 'DIVIDE'; mr.inputs[1].default_value = 60.0
        L.new(deg.outputs[0], mr.inputs[0])
        ramp = N.new("ShaderNodeValToRGB"); cr = ramp.color_ramp
        stops = [(0.0, (0.004, 0.003, 0.003)), (0.11, (0.004, 0.003, 0.003)),      # pupil
                 (0.14, tuple(c * 0.5 for c in iris_col)), (0.30, iris_col),       # iris
                 (0.36, (0.03, 0.022, 0.018)),                                     # limbal ring
                 (0.42, (0.62, 0.55, 0.50)), (1.0, (0.55, 0.45, 0.42))]            # sclera
        cr.elements[0].position, cr.elements[0].color = stops[0][0], (*stops[0][1], 1)
        cr.elements[1].position, cr.elements[1].color = stops[-1][0], (*stops[-1][1], 1)
        for pos, col in stops[1:-1]:
            e = cr.elements.new(pos); e.color = (*col, 1)
        L.new(mr.outputs[0], ramp.inputs['Fac'])
        nz = N.new("ShaderNodeTexNoise"); nz.inputs['Scale'].default_value = 600; nz.inputs['Detail'].default_value = 6
        L.new(tc.outputs['Object'], nz.inputs['Vector'])
        mix = N.new("ShaderNodeMix"); mix.data_type = 'RGBA'; mix.blend_type = 'MULTIPLY'; mix.inputs['Factor'].default_value = 0.3
        L.new(ramp.outputs['Color'], mix.inputs[6]); L.new(nz.outputs['Color'], mix.inputs[7])
        L.new(mix.outputs[2], p.inputs['Base Color'])
        p.inputs['Roughness'].default_value = 0.4; p.inputs['Subsurface Weight'].default_value = 0.15
        p.inputs['Coat Weight'].default_value = 1.0; p.inputs['Coat Roughness'].default_value = 0.0; p.inputs['Coat IOR'].default_value = 1.376
        return m

    # ------------------------------------------------------------------ helpers
    def joint(self, name):
        return Vector(self.rig.joint[name])

    def bone_head(self, bone):
        bpy.context.view_layer.update()
        return self.arm.matrix_world @ self.arm.pose.bones[bone].head

    def bone_tail(self, bone):
        bpy.context.view_layer.update()
        return self.arm.matrix_world @ self.arm.pose.bones[bone].tail

    def rot(self, bone, axis, deg):
        rotate_bone(self.arm, bone, axis, deg)

    def aim(self, bone, direction):
        aim_bone(self.arm, bone, direction)

    def vertex_region(self, group_bones, thresh=0.3):
        """Indices of body vertices mostly weighted to given bones."""
        idx = [self.rig.bones.index(b) for b in group_bones if b in self.rig.bones]
        return np.nonzero(self.W[:, idx].sum(1) > thresh)[0]


# ----------------------------------------------------------------------------- poses
SIDE = {"L": 1.0, "R": -1.0}  # character's left is +X (body faces -Y in rest pose)


def reset_pose(h):
    for pb in h.arm.pose.bones:
        pb.matrix_basis = Matrix.Identity(4)
    bpy.context.view_layer.update()


def _chain(h, bones_dirs):
    for b, d in bones_dirs:
        h.aim(b, d)


def fingers_curl(h, deg=35, side=("L", "R"), thumb=15):
    for sd in side:
        sgn = SIDE[sd]
        for f in range(2, 6):
            for k in (1, 2, 3):
                h.rot(f"finger{f}-{k}.{sd}", (1, 0, 0), deg * (0.8 if k == 1 else 1.0))
        for k in (2, 3):
            h.rot(f"finger1-{k}.{sd}", (0, 0, sgn), thumb)


def pose_sit(h, lean=18, hands="knees"):
    """Seated on a low rock, forearms on knees, leaning toward the fire (fire is at -Y)."""
    for sd, sg in SIDE.items():
        _chain(h, [(f"upperleg01.{sd}", (0.17 * sg, -1, -0.12)), (f"upperleg02.{sd}", (0.17 * sg, -1, -0.12)),
                   (f"lowerleg01.{sd}", (0.05 * sg, -0.28, -1)), (f"lowerleg02.{sd}", (0.05 * sg, -0.28, -1)),
                   (f"foot.{sd}", (0.1 * sg, -1, -0.35))])
    for b, a in (("spine05", 4), ("spine04", 5), ("spine03", 5), ("spine02", 4), ("spine01", 3)):
        h.rot(b, (1, 0, 0), lean * a / 21)
    for sd, sg in SIDE.items():
        knee = h.bone_tail(f"upperleg02.{sd}")
        sh = h.bone_head(f"upperarm01.{sd}")
        d = knee - sh + Vector((0.0, -0.03, 0.04))
        _chain(h, [(f"upperarm01.{sd}", d), (f"upperarm02.{sd}", d)])
        _chain(h, [(f"lowerarm01.{sd}", (-0.35 * sg, -1, -0.15)), (f"lowerarm02.{sd}", (-0.35 * sg, -1, -0.15))])
        h.aim(f"wrist.{sd}", (-0.3 * sg, -1, -0.45))
    fingers_curl(h, 30)
    h.rot("neck01", (1, 0, 0), 4); h.rot("head", (1, 0, 0), 12)


def pose_walk(h, phase, stride=28, arm_swing=22):
    """Procedural walk cycle. phase in [0,1). Body walks toward -Y."""
    reset_pose(h)
    ph = 2 * math.pi * phase
    for sd, sg in SIDE.items():
        p = ph + (0 if sd == "L" else math.pi)
        hip = stride * math.sin(p)                         # + forward
        knee = 8 + 30 * max(0.0, math.sin(p + 1.3)) ** 1.5  # bends while swinging forward
        h.rot(f"upperleg01.{sd}", (1, 0, 0), -hip)
        h.rot(f"lowerleg01.{sd}", (1, 0, 0), knee)
        h.rot(f"foot.{sd}", (1, 0, 0), -8 * math.sin(p + 0.6))
        h.rot(f"upperarm01.{sd}", (1, 0, 0), arm_swing * math.sin(p + math.pi))
        h.rot(f"lowerarm01.{sd}", (1, 0, 0), -12 - 10 * max(0, math.sin(p + math.pi)))
    h.rot("spine03", (0, 0, 1), 5 * math.sin(ph)); h.rot("spine05", (1, 0, 0), -6)
    h.rot("spine01", (0, 0, 1), -4 * math.sin(ph)); h.rot("head", (1, 0, 0), -4)
    # bring arms closer to the body than MakeHuman's A-pose
    for sd, sg in SIDE.items():
        h.rot(f"upperarm01.{sd}", (0, 1, 0), sg * 30)
    fingers_curl(h, 25)
    # vertical bob: lowest foot touches the ground
    return 0.025 * (1 - math.cos(2 * ph)) * 0.5


def pose_mummy(h):
    """Ötzi's preserved pose: left arm frozen across the chest toward the right; right arm by the side;
    legs straight, head turned slightly. Defined standing (then lay the rig down with the object transform)."""
    # (standing frame: -Y is the chest side, +Z toward the head). The arm lies flat across the body
    _chain(h, [("upperarm01.L", (-0.8, -0.16, 0.32)), ("upperarm02.L", (-0.8, -0.16, 0.32)),
               ("lowerarm01.L", (-1, -0.06, 0.32)), ("lowerarm02.L", (-1, -0.06, 0.32)), ("wrist.L", (-1, 0.0, 0.25))])
    _chain(h, [("upperarm01.R", (-0.14, -0.04, -1)), ("upperarm02.R", (-0.14, -0.04, -1)),
               ("lowerarm01.R", (-0.06, -0.10, -1)), ("lowerarm02.R", (-0.06, -0.10, -1))])
    for sd, sg in SIDE.items():
        h.rot(f"upperleg01.{sd}", (0, 1, 0), sg * 2.5)      # close the A-stance slightly
        h.rot(f"foot.{sd}", (1, 0, 0), 50)                  # plantar-flexed: toes point away, as on the mummy
    h.rot("head", (0, 0, 1), -18); h.rot("head", (1, 0, 0), 8)
    fingers_curl(h, 55, side=("L",), thumb=40)
    fingers_curl(h, 18, side=("R",), thumb=5)


def lay_down(h, face_up=True, z=0.0):
    """Rotate the whole rig so the body lies along +Y (head toward +Y)."""
    h.arm.rotation_euler = (math.radians(-90 if face_up else 90), 0, 0)
    if not face_up:
        h.arm.rotation_euler = (math.radians(90), 0, math.radians(180))
    h.arm.location = (0, 0, z)
    bpy.context.view_layer.update()


def evaluated_bounds(objs):
    """World-space bounding box of deformed (posed) meshes."""
    dg = bpy.context.evaluated_depsgraph_get()
    lo = np.array([1e9] * 3); hi = -lo
    for o in objs:
        oe = o.evaluated_get(dg); me = oe.to_mesh()
        co = np.empty(len(me.vertices) * 3, np.float32); me.vertices.foreach_get("co", co)
        co = co.reshape(-1, 3)
        M = np.array(oe.matrix_world)
        w = co @ M[:3, :3].T + M[:3, 3]
        lo = np.minimum(lo, w.min(0)); hi = np.maximum(hi, w.max(0))
        oe.to_mesh_clear()
    return lo, hi


def _world_verts(o):
    """World positions of the deformed surface (vertices used by faces only - MakeHuman meshes carry
    loose helper vertices that must not count)."""
    dg = bpy.context.evaluated_depsgraph_get()
    oe = o.evaluated_get(dg); me = oe.to_mesh()
    co = np.empty(len(me.vertices) * 3, np.float32); me.vertices.foreach_get("co", co)
    lv = np.empty(len(me.loops), np.int32); me.loops.foreach_get("vertex_index", lv)
    M = np.array(oe.matrix_world); w = co.reshape(-1, 3)[np.unique(lv)] @ M[:3, :3].T + M[:3, 3]
    oe.to_mesh_clear()
    return w


def settle(h, surface_z, along=1, iters=3):
    """Tilt a lying rig about X so its upper body and its legs both rest on a plane, then drop it onto it.
    `along` is the world axis the body lies along (1 = Y)."""
    for _ in range(iters):
        w = _world_verts(h.body)
        a = w[:, along]; lo_a, hi_a = a.min(), a.max(); L_ = hi_a - lo_a
        up = w[a > lo_a + 0.55 * L_]; dn = w[a < lo_a + 0.35 * L_]
        pu = up[np.argmin(up[:, 2])]; pd = dn[np.argmin(dn[:, 2])]
        ang = math.atan2(pu[2] - pd[2], pu[along] - pd[along])
        if abs(ang) < 1e-3:
            break
        e = h.arm.rotation_euler.copy()
        e.x += ang if along == 1 else 0
        h.arm.rotation_euler = e
        bpy.context.view_layer.update()
    w = _world_verts(h.body)
    h.arm.location.z += surface_z - w[:, 2].min()
    bpy.context.view_layer.update()


def bake_pose(h):
    """Freeze the current pose into the meshes (armature applied), keeping world placement.
    Lets us sculpt contact with the ground afterwards. Subsurf/displace stay live."""
    bpy.context.view_layer.update()
    for o in [p for p in h.parts if p.type == 'MESH']:
        mods = [m for m in o.modifiers if m.type == 'ARMATURE']
        if not mods:
            continue
        mw = o.matrix_world.copy()
        bpy.context.view_layer.objects.active = o
        for ob in bpy.context.selected_objects:
            ob.select_set(False)
        o.select_set(True)
        bpy.ops.object.modifier_apply(modifier=mods[0].name)
        o.parent = None; o.matrix_world = mw
        o.data.transform(mw); o.matrix_world = Matrix.Identity(4)
    bpy.context.view_layer.update()


def flatten_contact(o, z0, band=0.05, squash=0.35, spread=0.25):
    """Soft tissue resting on a surface: compress the lowest `band` metres toward the plane z0 and let it
    bulge slightly sideways (o must be baked, with identity transform)."""
    me = o.data
    co = np.empty(len(me.vertices) * 3, np.float32); me.vertices.foreach_get("co", co); co = co.reshape(-1, 3)
    d = co[:, 2] - z0
    w = np.clip(1 - d / band, 0, 1) ** 2
    co[:, 2] = z0 + d * (1 - w * (1 - squash))
    co[:, 2] = np.maximum(co[:, 2], z0 + 0.0005)
    me.vertices.foreach_set("co", co.ravel()); me.update()


# ----------------------------------------------------------------------------- clothes & hair proxies
def textured_material(name, diffuse, normal=None, tint=(1, 1, 1), rough=0.75, hue=0.5, sat=1.0, val=1.0, alpha=False, sheen=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; p = N["Principled BSDF"]
    t = N.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(diffuse)
    hs = N.new("ShaderNodeHueSaturation"); hs.inputs['Hue'].default_value = hue
    hs.inputs['Saturation'].default_value = sat; hs.inputs['Value'].default_value = val
    L.new(t.outputs['Color'], hs.inputs['Color'])
    mul = N.new("ShaderNodeMix"); mul.data_type = 'RGBA'; mul.blend_type = 'MULTIPLY'; mul.inputs['Factor'].default_value = 1
    L.new(hs.outputs['Color'], mul.inputs[6]); mul.inputs[7].default_value = (*tint, 1)
    L.new(mul.outputs[2], p.inputs['Base Color'])
    if alpha:
        L.new(t.outputs['Alpha'], p.inputs['Alpha'])
    if normal and os.path.exists(normal):
        nt = N.new("ShaderNodeTexImage"); nt.image = bpy.data.images.load(normal); nt.image.colorspace_settings.name = 'Non-Color'
        nm = N.new("ShaderNodeNormalMap"); nm.inputs['Strength'].default_value = 1.0
        L.new(nt.outputs['Color'], nm.inputs['Color']); L.new(nm.outputs['Normal'], p.inputs['Normal'])
    p.inputs['Roughness'].default_value = rough
    p.inputs['Sheen Weight'].default_value = sheen
    return m


def add_asset(h, kind, name, **matkw):
    """Fit a MakeHuman clothes/hair asset to human `h` (textured, rigged, hides covered skin)."""
    d = os.path.join(MH, kind, name)
    path = os.path.join(d, name + ".mhpxy")
    mm = read_mhmat(os.path.join(d, name + ".mhmat"))
    diff = tex_path(d, mm.get("diffuseTexture", name + "_diffuse.png"))
    nrm = tex_path(d, mm.get("normalmapTexture", name + "_normal.png")) if mm.get("normalmapTexture") or os.path.exists(os.path.join(d, name + "_normal.png")) else None
    mat = textured_material(f"{h.name}_{name}", diff, nrm, alpha=(kind == "hair"), **matkw)
    o, px = h.add_proxy(path, name, mat=mat, subsurf=0 if kind == "hair" else 1)
    p = np.load(path)
    if "deleteVerts" in p.files:
        dv = p["deleteVerts"]
        import bmesh
        bm = bmesh.new(); bm.from_mesh(h.body.data); bm.verts.ensure_lookup_table()
        kill = [f for f in bm.faces if all(dv[v.index] for v in f.verts)]
        bmesh.ops.delete(bm, geom=kill, context='FACES_ONLY')
        bm.to_mesh(h.body.data); bm.free(); h.body.data.update()
    return o
