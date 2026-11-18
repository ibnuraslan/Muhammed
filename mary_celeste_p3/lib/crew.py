"""Part 3 cast, built on the shared Deveau character (mary_celeste_3d/lib/deveau.py) without changing it.

Each person is a Deveau-class man (MakeHuman body, clothes grown as shells, real strand hair) with his own face
targets, age, hair/beard spec and clothing colours. Extra kit lives here: top hats, a barrister's wig, white
bands, the diver's brass helmet and canvas dress.

    m = person("morehouse"); pose...; m.finish(look_at=..., place=M); extras(m, M)

Poses beyond the shared poses.py: seated (legs IK to the floor), kneeling, two-hand grips.
"""
import os, math
import numpy as np
import bpy
from mathutils import Vector, Matrix
import human as H, deveau as D, poses as P, ship

CACHE_DIR = None          # set by render.py for frame sequences (hair strand cache per shot and person)
CACHE_TAG = ""

# ----------------------------------------------------------------------------- cast sheet
# hair: (melanin, redness, grey); beard: density multipliers for the shared strand sets
CAST = {
    "deveau":    dict(),
    "morehouse": dict(years=40, extra={"targets/nose/nose-scale-horiz-incr": 0.3, "targets/chin/chin-width-incr": 0.4,
                                       "targets/head/head-fat-incr": 0.35, "targets/eyebrows/eyebrows-trans-down": 0.4,
                                       "targets/cheek/l-cheek-inflate-incr": 0.3, "targets/cheek/r-cheek-inflate-incr": 0.3},
                      weight=0.62, hair=(0.9, 0.2, 0.12), dens=dict(beard=1.3, moustache=1.2, hair=1.5), hlen=1.7,
                      jacket=(0.012, 0.011, 0.012)),
    "sailor_a":  dict(years=26, extra={"targets/nose/nose-point-width-incr": 0.4, "targets/chin/chin-prominent-decr": 0.2,
                                       "targets/cheek/l-cheek-bones-decr": 0.2, "targets/cheek/r-cheek-bones-decr": 0.2},
                      weight=0.45, hair=(0.55, 0.55, 0.0), dens=dict(beard=0.0, moustache=0.0, sideburns=0.6),
                      jacket=(0.055, 0.045, 0.035), skin=(0.47, 0.28, 0.18)),
    "sailor_b":  dict(years=30, extra={"targets/nose/nose-hump-incr": 0.7, "targets/head/head-oval": 0.4,
                                       "targets/eyebrows/eyebrows-angle-up": 0.3},
                      weight=0.5, hair=(0.95, 0.1, 0.0), dens=dict(beard=0.35, moustache=1.0),
                      jacket=(0.03, 0.032, 0.03), skin=(0.38, 0.22, 0.14)),
    "flood":     dict(years=43, extra={"targets/nose/nose-scale-vert-incr": 0.5, "targets/nose/nose-trans-down": 0.2,
                                       "targets/chin/chin-prominent-incr": 0.5, "targets/head/head-oval": 0.5,
                                       "targets/eyebrows/eyebrows-angle-down": 0.4, "targets/cheek/l-cheek-bones-incr": 0.5,
                                       "targets/cheek/r-cheek-bones-incr": 0.5},
                      weight=0.42, hair=(0.6, 0.3, 0.45), dens=dict(beard=0.0, moustache=0.0, sideburns=2.5, hair=0.8),
                      chops=True, jacket=(0.008, 0.008, 0.009), skin=(0.52, 0.33, 0.25), weather=0.25),
    "surveyor":  dict(years=52, extra={"targets/nose/nose-scale-horiz-incr": 0.5, "targets/head/head-age-incr": 0.6,
                                       "targets/chin/chin-width-incr": 0.3},
                      weight=0.6, hair=(0.5, 0.2, 0.7), dens=dict(beard=1.0, moustache=1.0, hair=0.6),
                      jacket=(0.02, 0.018, 0.016)),
    "judge":     dict(years=60, extra={"targets/head/head-age-incr": 0.8, "targets/nose/nose-scale-vert-incr": 0.3},
                      weight=0.55, hair=(0.4, 0.2, 0.9), dens=dict(beard=0.0, moustache=0.0, hair=0.0, sideburns=1.0),
                      jacket=(0.012, 0.01, 0.01), skin=(0.5, 0.31, 0.24), weather=0.2),
    "chemist":   dict(years=46, extra={"targets/nose/nose-point-width-incr": 0.6, "targets/head/head-round": 0.4,
                                       "targets/eyebrows/eyebrows-trans-up": 0.3},
                      weight=0.55, hair=(0.75, 0.25, 0.3), dens=dict(beard=0.0, moustache=1.3),
                      jacket=(0.03, 0.022, 0.016), skin=(0.46, 0.29, 0.2), weather=0.3),
    "captain2":  dict(years=38, extra={"targets/chin/chin-prominent-incr": 0.6, "targets/nose/nose-trans-up": 0.3},
                      weight=0.5, hair=(0.85, 0.3, 0.05), dens=dict(beard=1.0, moustache=1.0),
                      jacket=(0.008, 0.01, 0.02)),
    "diver":     dict(years=35, weight=0.6, hair=(0.8, 0.3, 0.0), dens=dict(beard=0.0, moustache=0.0, hair=0.0, sideburns=0.0, brows=0.0),
                      diver=True),
}


class Person(D.Deveau):
    def __init__(self, key="deveau", wet=0.2, wig=False, idx=0):
        spec = dict(CAST[key]); self.key = key; self.spec = spec; self.wig_on = wig
        self._dens = spec.get("dens", {})
        if key == "deveau":
            D.Deveau.__init__(self, name=f"Deveau{idx}", wet=wet)
        else:
            self._init_variant(spec, f"{key}{idx}", wet)
        if spec.get("jacket"):
            self.jacket.data.materials[0] = D.wool_material(self.name + "_jk", spec["jacket"], weave=380, wet=wet, dirt=0.18, sheen=0.3)
        if spec.get("diver"):
            self._diver_dress()
        if wig:
            self._wig()

    def _init_variant(self, spec, name, wet):
        # same construction as Deveau.__init__, with this man's face, age and build
        extra = dict(spec.get("extra", {}))
        self.h = H.Human(name, gender=1.0, years=spec.get("years", 34), muscle=0.6, weight=spec.get("weight", 0.5),
                         height=spec.get("height", 0.52), extra=extra, eyebrows=None, eyelashes=None, skin=None)
        h = self.h
        h.body.data.materials[0] = D.sailor_skin(name + "_skin", base=spec.get("skin", (0.43, 0.25, 0.16)),
                                                 weather=spec.get("weather", 0.6))
        if hasattr(self, "_skin_regions"):
            self._skin_regions()
        self.name = name; self.wet = wet
        self.rest_co = H.to_bl(h.hc)
        me = h.body.data
        self.rest_n = np.array([v.normal[:] for v in me.vertices], np.float64)
        uvs = np.zeros((len(me.vertices), 2)); uvl = me.uv_layers[0].data
        for l in me.loops:
            uvs[l.vertex_index] = uvl[l.index].uv
        self.uv = uvs
        self.used = np.zeros(len(me.vertices), bool)
        for pl in me.polygons:
            self.used[list(pl.vertices)] = True
        self.faces = [tuple(pl.vertices) for pl in me.polygons]
        self._dress()

    # -------------------------------------------------------------- hair: per-person density and colour
    def _strands(self, label, vmask, P_, bvh, count, length, radius, comb, lift, mat, curl=0.2, segs=7, seed=1, **kw):
        k = self._dens.get(label, 1.0)
        if self.wig_on and label in ("hair", "sideburns"):
            k = 0.0
        if label == "hair":
            length = (length[0] * self.spec.get("hlen", 1.0), length[1] * self.spec.get("hlen", 1.0))
        if label == "sideburns" and self.spec.get("chops"):
            length = (length[0] * 1.3, length[1] * 1.6)
        hc = self.spec.get("hair")
        if hc:
            mat = D.hair_material(f"{self.name}_{label}_m", hc[0], hc[1], rough=0.35)
            _grey_tint(mat, hc[2])
        return D.Deveau._strands(self, label, vmask, P_, bvh, int(count * k), length, radius, comb, lift, mat, curl, segs, seed, **kw)

    def finish(self, look_at=None, lids=0.0, hair=True, density=1.0, place=None):
        if CACHE_DIR and hair:
            return finish_cached(self, look_at=look_at, place=place, density=density,
                                 cache=os.path.join(CACHE_DIR, f"{CACHE_TAG}_{self.name}.npz"))
        return D.Deveau.finish(self, look_at=look_at, lids=lids, hair=hair, density=density, place=place)

    # -------------------------------------------------------------- wig and diving dress (shells, rest pose)
    def _scalp_mask(self, lo=0.0):
        h = self.h; co = self.rest_co
        wh = D._w(h, D.HEAD)
        eyeL = np.array(h.joint("eye.L____head")); eyeR = np.array(h.joint("eye.R____head")); ec = (eyeL + eyeR) / 2
        rel = co - ec; y, z = rel[:, 1], rel[:, 2]
        line = np.interp(y, [-0.12, -0.06, 0.0, 0.05, 0.12], [0.07, 0.06, 0.02, -0.04, -0.075])
        return self.used & (wh > 0.5) & (z > line + lo), ec

    def _wig(self):
        m, ec = self._scalp_mask()
        mat = wig_material(self.name + "_wig")
        self.wig, _ = self._shell("wig", m, 0.02, mat, solid=0.0, displace=0.0, drape=3)
        so = self.wig.modifiers.new("Thick", "SOLIDIFY"); so.thickness = 0.006; so.offset = -1; so.use_even_offset = False
        self.ec = ec

    def _diver_dress(self):
        can = rubber_twill(self.name + "_twill")
        for o in (self.jacket, self.trousers, self.shirt):
            o.data.materials[0] = can
        for b in getattr(self, "button_objs", []):
            b.hide_render = True
        self.boots.data.materials[0] = D.leather_material(self.name + "_boot", (0.03, 0.025, 0.02), rough=0.7, wet=0.9)


def _grey_tint(mat, grey):
    """Mix grey/white into a hair material (older men)."""
    if grey <= 0 or not mat.use_nodes:
        return
    N = mat.node_tree.nodes
    hb = next((n for n in N if n.type == 'BSDF_HAIR_PRINCIPLED'), None)
    if hb is None:
        return
    hb.inputs['Melanin'].default_value = hb.inputs['Melanin'].default_value * (1 - 0.55 * grey)
    hb.inputs['Melanin Redness'].default_value = hb.inputs['Melanin Redness'].default_value * (1 - 0.8 * grey)
    if 'Random Color' in hb.inputs:
        hb.inputs['Random Color'].default_value = 0.15 + 0.5 * grey


def person(key, **kw):
    return Person(key, **kw)


# ----------------------------------------------------------------------------- materials
def wig_material(name):
    m = bpy.data.materials.new(name); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; p = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord")
    wv = N.new("ShaderNodeTexWave"); wv.wave_type = 'RINGS'; wv.inputs['Scale'].default_value = 38
    wv.inputs['Distortion'].default_value = 6; wv.inputs['Detail'].default_value = 4
    L.new(tc.outputs['Object'], wv.inputs['Vector'])
    bm = N.new("ShaderNodeBump"); bm.inputs['Strength'].default_value = 0.8; bm.inputs['Distance'].default_value = 0.004
    L.new(wv.outputs['Fac'], bm.inputs['Height']); L.new(bm.outputs['Normal'], p.inputs['Normal'])
    cr = N.new("ShaderNodeValToRGB"); cr.color_ramp.elements[0].color = (0.42, 0.40, 0.36, 1); cr.color_ramp.elements[1].color = (0.72, 0.70, 0.64, 1)
    L.new(wv.outputs['Fac'], cr.inputs['Fac']); L.new(cr.outputs['Color'], p.inputs['Base Color'])
    p.inputs['Roughness'].default_value = 0.85; p.inputs['Sheen Weight'].default_value = 0.6
    return m


def rubber_twill(name):
    return D.wool_material(name, (0.30, 0.24, 0.15), rough=0.55, sheen=0.1, weave=700, bump=0.25, wet=0.6, dirt=0.4)


def flat(name, color, rough=0.5, metal=0.0, emit=None):
    m = bpy.data.materials.new(name); m.use_nodes = True; p = m.node_tree.nodes["Principled BSDF"]
    p.inputs['Base Color'].default_value = (*color, 1); p.inputs['Roughness'].default_value = rough
    p.inputs['Metallic'].default_value = metal
    if emit:
        p.inputs['Emission Color'].default_value = (*emit[0], 1); p.inputs['Emission Strength'].default_value = emit[1]
    return m


# ----------------------------------------------------------------------------- head frame (after finish)
def head_frame(p, place=None):
    """Centre of the skull, up and forward axes, in world space (call after finish()).
    Uses the baked body vertices weighted to the head."""
    h = p.h
    wh = D._w(h, ("head",))
    me = h.body.data
    co = np.array([v.co[:] for v in me.vertices]) if len(me.vertices) == len(wh) else None
    R = p.head_R
    up = (R @ Vector((0, 0, 1))).normalized(); fwd = (R @ Vector((0, -1, 0))).normalized()
    if co is not None:
        sel = co[(wh > 0.8) & p.used]
        c = Vector(sel.mean(0))
        top = max((Vector(v) - c).dot(up) for v in sel[::7])
    else:
        c = h.bone_head("head") + up * 0.09; top = 0.1
    Mw = h.body.matrix_world
    c = Mw @ c; up = (Mw.to_3x3() @ up).normalized(); fwd = (Mw.to_3x3() @ fwd).normalized()
    return c, up, fwd, top


def top_hat(p, color=(0.012, 0.011, 0.011), h_=0.17, r=0.098):
    c, up, fwd, top = head_frame(p)
    side = up.cross(fwd).normalized(); fwd = side.cross(up).normalized()
    M = Matrix((side, fwd, up)).transposed().to_4x4()
    base = c + up * (top - 0.045) + fwd * -0.008
    M.translation = base
    mat = flat(p.name + "_hat", color, rough=0.45); mat.node_tree.nodes["Principled BSDF"].inputs['Sheen Weight'].default_value = 0.8
    bpy.ops.mesh.primitive_cylinder_add(vertices=40, radius=1, depth=1)
    crown = bpy.context.active_object; crown.name = p.name + "_hat_crown"
    crown.scale = (r * 1.04, r * 1.18, h_); crown.matrix_world = M @ Matrix.Translation((0, 0, h_ / 2)) @ Matrix.Diagonal((r * 1.04, r * 1.18, h_, 1))
    bv = crown.modifiers.new("b", "BEVEL"); bv.width = 0.006; bv.segments = 3
    crown.data.materials.append(mat); crown.data.polygons.foreach_set("use_smooth", [True] * len(crown.data.polygons))
    bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=1, depth=1)
    brim = bpy.context.active_object; brim.name = p.name + "_hat_brim"
    brim.matrix_world = M @ Matrix.Translation((0, 0, 0.004)) @ Matrix.Diagonal((r * 1.55, r * 1.72, 0.006, 1))
    brim.data.materials.append(mat)
    band = flat(p.name + "_hatband", (0.004, 0.004, 0.004), rough=0.3)
    bpy.ops.mesh.primitive_cylinder_add(vertices=40, radius=1, depth=1)
    bd = bpy.context.active_object; bd.name = p.name + "_hat_band"
    bd.matrix_world = M @ Matrix.Translation((0, 0, 0.025)) @ Matrix.Diagonal((r * 1.05, r * 1.19, 0.03, 1))
    bd.data.materials.append(band)
    return [crown, brim, bd]


def bands(p):
    """Barrister's white bands at the throat."""
    c, up, fwd, top = head_frame(p)
    side = up.cross(fwd).normalized()
    neck = c - up * 0.2 + fwd * 0.075
    mat = flat(p.name + "_bands", (0.8, 0.79, 0.75), rough=0.7)
    out = []
    for s in (-1, 1):
        q = neck + side * (0.011 * s) - up * 0.04
        bpy.ops.mesh.primitive_cube_add(size=1)
        o = bpy.context.active_object; o.name = p.name + "_band"
        M = Matrix((side, fwd, up)).transposed().to_4x4(); M.translation = q
        o.matrix_world = M @ Matrix.Diagonal((0.02, 0.003, 0.085, 1)); o.data.materials.append(mat); out.append(o)
    return out


def wig_rolls(p):
    """Horizontal curls along the back and sides of a barrister's wig."""
    c, up, fwd, top = head_frame(p)
    side = up.cross(fwd).normalized()
    mat = p.wig.data.materials[0]
    out = []
    for row, (dz, rr) in enumerate(((-0.02, 0.095), (-0.045, 0.098), (-0.07, 0.1))):
        bpy.ops.mesh.primitive_torus_add(major_radius=rr, minor_radius=0.011, major_segments=48, minor_segments=10)
        o = bpy.context.active_object; o.name = f"{p.name}_roll{row}"
        M = Matrix((side, fwd, up)).transposed().to_4x4(); M.translation = c + up * dz - fwd * 0.012
        o.matrix_world = M @ Matrix.Diagonal((1.0, 1.08, 1, 1))
        # keep only the back half (curls sit behind the ears)
        me = o.data
        import bmesh
        bm = bmesh.new(); bm.from_mesh(me)
        kill = [v for v in bm.verts if v.co.y > -0.025]
        bmesh.ops.delete(bm, geom=kill, context='VERTS'); bm.to_mesh(me); bm.free()
        me.materials.append(mat); out.append(o)
    return out


def diver_helmet(p):
    """Standard diving dress: spun-copper/brass helmet with front and side ports, on a breastplate (corselet)."""
    c, up, fwd, top = head_frame(p)
    side = up.cross(fwd).normalized(); fwd = side.cross(up).normalized()
    if os.environ.get("SKETCHFAB", "1") != "0":
        try:
            import sketchfab as SF
            ob = SF.model("diving_helmet", name=p.name + "_helmet_sf")
            R = Matrix(((-fwd).cross(up), -fwd, up)).transposed().to_4x4()
            R.translation = c - up * 0.29
            ob.matrix_world = R
            for o in getattr(p, "hair_objs", []):
                if o:
                    o.hide_render = True
            return [ob], c - fwd * 0.17 + up * 0.04
        except Exception as e:
            print("sketchfab helmet unavailable:", e)
    M = Matrix((side, fwd, up)).transposed().to_4x4(); M.translation = c + up * 0.01
    brass = D.brass_material(p.name + "_brass") if hasattr(D, "brass_material") else flat("brass", (0.6, 0.4, 0.2), 0.3, 1.0)
    copper = flat(p.name + "_copper", (0.55, 0.28, 0.16), rough=0.35, metal=1.0)
    glass = bpy.data.materials.new(p.name + "_port"); glass.use_nodes = True
    gp = glass.node_tree.nodes["Principled BSDF"]; gp.inputs['Base Color'].default_value = (0.02, 0.03, 0.03, 1)
    gp.inputs['Roughness'].default_value = 0.05; gp.inputs['Coat Weight'].default_value = 1.0
    out = []
    bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, radius=1)
    hm = bpy.context.active_object; hm.name = p.name + "_helmet"
    hm.matrix_world = M @ Matrix.Diagonal((0.17, 0.17, 0.18, 1)); hm.data.materials.append(copper)
    hm.data.polygons.foreach_set("use_smooth", [True] * len(hm.data.polygons)); out.append(hm)
    # corselet (breastplate) over the shoulders
    bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, radius=1)
    cs = bpy.context.active_object; cs.name = p.name + "_corselet"
    cs.matrix_world = M @ Matrix.Translation((0, 0.01, -0.2)) @ Matrix.Diagonal((0.27, 0.2, 0.12, 1))
    cs.data.materials.append(copper); cs.data.polygons.foreach_set("use_smooth", [True] * len(cs.data.polygons)); out.append(cs)
    # neck ring and port frames (brass)
    bpy.ops.mesh.primitive_torus_add(major_radius=0.15, minor_radius=0.018, major_segments=48)
    nr = bpy.context.active_object; nr.name = p.name + "_neckring"; nr.matrix_world = M @ Matrix.Translation((0, 0, -0.13))
    nr.data.materials.append(brass); out.append(nr)
    for ax, r, depth in ((fwd, 0.075, 0.165), (side, 0.05, 0.16), (-side, 0.05, 0.16)):
        Mp = ax.to_track_quat('Z', 'Y').to_matrix().to_4x4(); Mp.translation = M.translation + ax * depth
        bpy.ops.mesh.primitive_torus_add(major_radius=r, minor_radius=0.014, major_segments=40)
        ring = bpy.context.active_object; ring.name = p.name + "_portring"; ring.matrix_world = Mp
        ring.data.materials.append(brass); out.append(ring)
        bpy.ops.mesh.primitive_cylinder_add(vertices=40, radius=r, depth=0.01)
        gl = bpy.context.active_object; gl.name = p.name + "_portglass"; gl.matrix_world = Mp
        gl.data.materials.append(glass); out.append(gl)
    # air hose fitting at the back
    back = M.translation - fwd * 0.16 + up * 0.03
    bpy.ops.mesh.primitive_cylinder_add(vertices=20, radius=0.022, depth=0.08)
    f = bpy.context.active_object; f.name = p.name + "_airfit"
    Mf = (-fwd).to_track_quat('Z', 'Y').to_matrix().to_4x4(); Mf.translation = back; f.matrix_world = Mf
    f.data.materials.append(brass); out.append(f)
    # hide the head/hair under the helmet
    for o in getattr(p, "hair_objs", []):
        if o:
            o.hide_render = True
    return out, back


def hide_head(p):
    """For the diver: remove head skin faces (inside the helmet, never seen) and eyes."""
    for e in p.h.eyes:
        e.hide_render = True


# ----------------------------------------------------------------------------- poses
def leg_reach(h, side, ankle_target, knee_pole):
    """Two-segment IK for a leg (upperleg01/02 -> lowerleg01/02): ankle to the target, knee toward the pole."""
    b = h.arm.data.bones
    a = b[f"upperleg01.{side}"].length + b[f"upperleg02.{side}"].length
    c = b[f"lowerleg01.{side}"].length + b[f"lowerleg02.{side}"].length
    S = h.bone_head(f"upperleg01.{side}"); T = Vector(ankle_target)
    dv = T - S; d = min(max(dv.length, abs(a - c) + 1e-3), (a + c) * 0.999); u = dv.normalized()
    cosA = (a * a + d * d - c * c) / (2 * a * d); sinA = math.sqrt(max(0.0, 1 - cosA * cosA))
    p = Vector(knee_pole); p = (p - u * p.dot(u)).normalized()
    E = S + u * (a * cosA) + p * (a * sinA)
    h.aim(f"upperleg01.{side}", E - S); h.aim(f"upperleg02.{side}", E - S)
    h.aim(f"lowerleg01.{side}", S + u * d - E); h.aim(f"lowerleg02.{side}", S + u * d - E)


def foot_flat(h, side, fwd=(0, -1, 0)):
    h.aim(f"foot.{side}", Vector(fwd) + Vector((0, 0, -0.42)))


def hip_height(h):
    return h.joint("upperleg01.L____head")[2]


def sit(h, drop, lean=8, knee_fwd=0.46, feet_apart=0.13, feet_fwd=0.5):
    """Seated: the rig is lowered by `drop` (the caller puts that into the place matrix). Thighs forward,
    shins down, feet flat on the floor at local z = 0 after the drop."""
    for sd, sg in H.SIDE.items():
        hip = Vector(h.joint(f"upperleg01.{sd}____head"))
        ank = Vector((hip.x + sg * (feet_apart - abs(hip.x)), -feet_fwd, drop + 0.085))
        leg_reach(h, sd, ank, (0, -1, 0.3))
        foot_flat(h, sd)
    for b, k in (("spine05", 0.2), ("spine04", 0.3), ("spine03", 0.3), ("spine02", 0.2)):
        h.rot(b, (1, 0, 0), lean * k)


def kneel(h, drop, knee="L", lean=10):
    """One knee down (`knee` side), the other foot flat in front; rig lowered by `drop`."""
    other = "R" if knee == "L" else "L"
    for sd, sg in H.SIDE.items():
        hip = Vector(h.joint(f"upperleg01.{sd}____head"))
        if sd == knee:
            ank = Vector((hip.x, 0.42, drop + 0.11))
            leg_reach(h, sd, ank, (0, -1, -0.2))
            h.aim(f"foot.{sd}", (0, 0.3, -1))
        else:
            ank = Vector((hip.x + sg * 0.04, -0.42, drop + 0.085))
            leg_reach(h, sd, ank, (0, -1, 0.6))
            foot_flat(h, sd)
    for b, k in (("spine04", 0.35), ("spine03", 0.35), ("spine02", 0.3)):
        h.rot(b, (1, 0, 0), lean * k)


def place(pos, heading_deg, drop=0.0, base=None):
    """World matrix for a rig: stand at pos (x, y, floor z), facing heading (deg, 0 = +X), lowered by drop."""
    M = Matrix.Translation((pos[0], pos[1], pos[2] - drop)) @ Matrix.Rotation(math.radians(heading_deg + 90), 4, 'Z')
    return (base @ M) if base is not None else M


# ----------------------------------------------------------------------------- hair cache for animation
# Growing ~130k strands takes most of a person's build time. For the frames of one shot we grow the hair once
# (frame 0) and afterwards carry the cached strands rigidly with the head bone (hair, beard and brows all sit
# on the skull; there is no jaw animation), so every frame matches frame 0's groom exactly - no flicker.
def _hair_mat(p, label):
    hc = p.spec.get("hair")
    if hc:
        m = D.hair_material(f"{p.name}_{label}_m", hc[0], hc[1], rough=0.35); _grey_tint(m, hc[2]); return m
    if label in ("hair", "sideburns"):
        return D.hair_material(p.name + "_hair", 0.82, 0.38)
    return D.hair_material(p.name + "_beard", 0.8, 0.45, rough=0.38)


def finish_cached(p, look_at=None, place=None, density=1.0, cache=None, hair=True):
    """Person.finish with an optional strand cache (path to .npz). Same result as p.finish(...)."""
    if not hair or not cache:
        return D.Deveau.finish(p, look_at=look_at, place=place, density=density, hair=hair)
    if not os.path.exists(cache):
        D.Deveau.finish(p, look_at=look_at, place=place, density=density)
        Pi = place.inverted() if place is not None else Matrix.Identity(4)
        R0 = np.array(p.head_R); p0 = np.array(p.h.bone_head("head"))
        data = dict(R0=R0, p0=p0)
        for i, o in enumerate([o for o in getattr(p, "hair_objs", []) if o]):
            n = len(o.data.points); pos = np.empty(n * 3, np.float32); o.data.position_data.foreach_get("vector", pos)
            pos = pos.reshape(-1, 3)
            Mw = np.array(Pi @ o.matrix_world)
            pos = pos @ Mw[:3, :3].T + Mw[:3, 3]
            sizes = np.array([c.points_length for c in o.data.curves], np.int32)
            rad = np.empty(n, np.float32); o.data.attributes["radius"].data.foreach_get("value", rad)
            data[f"pos{i}"] = pos; data[f"siz{i}"] = sizes; data[f"rad{i}"] = rad; data[f"lab{i}"] = np.array(o.name.rsplit("_", 1)[1])
        os.makedirs(os.path.dirname(cache), exist_ok=True)
        np.savez_compressed(cache, **data)
        return
    # cached: pose and bake without growing, then rebuild the strands carried by the head
    look_local = (place.inverted() @ Vector(look_at)) if (place is not None and look_at is not None) else look_at
    D.Deveau.finish(p, look_at=look_local, place=None, density=density, hair=False)
    z = np.load(cache)
    R0 = z["R0"]; p0 = z["p0"]; R1 = np.array(p.head_R); p1 = np.array(p.h.bone_head("head"))
    T = R1 @ np.linalg.inv(R0)
    p.hair_objs = []
    i = 0
    while f"pos{i}" in z.files:
        pos = (z[f"pos{i}"] - p0) @ T.T + p1
        cv = bpy.data.hair_curves.new(f"{p.name}_{str(z[f'lab{i}'])}")
        cv.add_curves(z[f"siz{i}"].tolist())
        cv.position_data.foreach_set("vector", pos.astype(np.float32).ravel())
        try:
            cv.attributes["radius"].data.foreach_set("value", z[f"rad{i}"])
        except Exception:
            a = cv.attributes.new("radius", 'FLOAT', 'POINT'); a.data.foreach_set("value", z[f"rad{i}"])
        o = bpy.data.objects.new(cv.name, cv); bpy.context.collection.objects.link(o)
        cv.materials.append(_hair_mat(p, str(z[f"lab{i}"])))
        p.hair_objs.append(o); i += 1
    if place is not None:
        for o in p.objects:
            if o.parent is None:
                o.matrix_world = place @ o.matrix_world
        bpy.context.view_layer.update()
