"""The Iceman's mummy: an emaciated, desiccated MakeHuman body with leathery skin."""
import numpy as np
import bpy
from human import Human, pose_mummy, list_targets, MH

U = "targets/expression/units/caucasian/"
MUMMY_TARGETS = {
    # wasted limbs and torso
    "targets/measure/measure-thigh-circ-decr": 1.0, "targets/measure/measure-calf-circ-decr": 1.0,
    "targets/measure/measure-upperarm-circ-decr": 1.0, "targets/measure/measure-waist-circ-decr": 1.0,
    "targets/measure/measure-neck-circ-decr": 0.9, "targets/measure/measure-hips-circ-decr": 0.7,
    "targets/measure/measure-bust-circ-decr": 0.6,
    "targets/stomach/stomach-pregnant-decr": 1.0, "targets/stomach/stomach-tone-incr": 1.0,
    "targets/torso/torso-muscle-pectoral-decr": 1.0, "targets/torso/torso-scale-depth-decr": 0.5,
    # the face: sunken cheeks, prominent cheekbones, closed shrunken eyes, lips pulled back
    "targets/cheek/l-cheek-volume-decr": 1.0, "targets/cheek/r-cheek-volume-decr": 1.0,
    "targets/cheek/l-cheek-inner-decr": 1.0, "targets/cheek/r-cheek-inner-decr": 1.0,
    "targets/cheek/l-cheek-bones-incr": 0.7, "targets/cheek/r-cheek-bones-incr": 0.7,
    "targets/head/head-fat-decr": 1.0, "targets/chin/chin-bones-incr": 0.5,
    U + "eye-left-closure": 1.0, U + "eye-right-closure": 1.0,
    "targets/eyes/l-eye-push1-in": 1.0, "targets/eyes/r-eye-push1-in": 1.0,
    U + "mouth-open": 0.22, U + "mouth-retraction": 0.7, U + "mouth-upward-retraction": 0.4,
    "targets/mouth/mouth-lowerlip-volume-decr": 1.0, "targets/mouth/mouth-upperlip-volume-decr": 1.0,
    "targets/nose/nose-volume-decr": 0.6, "targets/nose/nose-compression-compress": 0.5,
    U + "neck-platysma": 0.6,
}


def _neighbours(fvert, n):
    """Vertex adjacency from quads (as CSR-ish list of arrays)."""
    e = np.concatenate([fvert[:, [0, 1]], fvert[:, [1, 2]], fvert[:, [2, 3]], fvert[:, [3, 0]]])
    e = e[e[:, 0] != e[:, 1]]
    e = np.concatenate([e, e[:, ::-1]])
    e = np.unique(e, axis=0)
    return e


def desiccate(hc, fvert, body_verts, strength=1.9, shrink=0.05, iters=12):
    """Exaggerate bony relief (unsharp mask on geometry) and shrink soft tissue inward.
    Units: MakeHuman decimetres (0.035 = 3.5 mm)."""
    e = _neighbours(fvert, len(hc))
    deg = np.bincount(e[:, 0], minlength=len(hc)).astype(np.float64)
    sm = hc.astype(np.float64).copy()
    for _ in range(iters):
        acc = np.zeros_like(sm)
        np.add.at(acc, e[:, 0], sm[e[:, 1]])
        nb = acc / np.maximum(deg, 1)[:, None]
        sm = np.where(deg[:, None] > 0, sm * 0.5 + nb * 0.5, sm)
    detail = hc - sm
    # normals (area weighted)
    v = hc.astype(np.float64)
    a, b, c, d = (v[fvert[:, i]] for i in range(4))
    fn = np.cross(c - a, d - b)
    vn = np.zeros_like(v)
    for i in range(4):
        np.add.at(vn, fvert[:, i], fn)
    vn /= np.maximum(np.linalg.norm(vn, axis=1, keepdims=True), 1e-9)
    # concavity measure: detail along normal (>0 convex / bony, <0 concave / soft hollow)
    conv = (detail * vn).sum(1)
    soft = np.clip(0.5 - conv * 8, 0, 1)            # flatter/concave areas lose more tissue
    out = hc.astype(np.float64).copy()
    m = np.zeros(len(hc), bool); m[body_verts] = True
    out[m] = sm[m] + detail[m] * strength - vn[m] * (shrink * soft[m])[:, None]
    # ribs: skin sinks between them over the ribcage (MakeHuman: y up, z forward, units dm)
    y, x, z = hc[:, 1], hc[:, 0], hc[:, 2]
    ys = np.sort(y[body_verts]); top = ys[-1]
    y_hi, y_lo = top - 3.9, top - 6.6                  # roughly armpit to lower ribs on a 1.6 m body
    band = np.clip((y - y_lo) / 0.6, 0, 1) * np.clip((y_hi - y) / 0.6, 0, 1)
    side = np.clip((np.abs(x) - 0.25) / 0.6, 0, 1)      # visible mostly on the flanks / lateral chest
    slope = np.abs(x) * 0.35 - z * 0.25                 # ribs run down toward the front
    rib = (0.5 - 0.5 * np.cos(2 * np.pi * (y + slope) / 0.27)) ** 2
    amt = 0.08 * band * side * rib
    sel = m & (amt > 0)
    out[sel] -= vn[sel] * amt[sel][:, None]
    return out.astype(np.float32)


def mummy_skin(name="MummySkin"):
    m = bpy.data.materials.new(name); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links
    p = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord"); geo = N.new("ShaderNodeNewGeometry")
    # colour: dark reddish-brown base, pale parchment where skin is stretched over bone (pointiness)
    pt = N.new("ShaderNodeMapRange"); pt.inputs['From Min'].default_value = 0.47; pt.inputs['From Max'].default_value = 0.56
    L.new(geo.outputs['Pointiness'], pt.inputs['Value'])
    n1 = N.new("ShaderNodeTexNoise"); n1.inputs['Scale'].default_value = 14; n1.inputs['Detail'].default_value = 8; n1.inputs['Roughness'].default_value = 0.65
    L.new(tc.outputs['Object'], n1.inputs['Vector'])
    mixf = N.new("ShaderNodeMath"); mixf.operation = 'MULTIPLY_ADD'; mixf.inputs[1].default_value = 0.55
    L.new(n1.outputs['Fac'], mixf.inputs[0]); L.new(pt.outputs[0], mixf.inputs[2])
    ramp = N.new("ShaderNodeValToRGB"); cr = ramp.color_ramp
    cr.elements[0].position = 0.25; cr.elements[0].color = (0.045, 0.014, 0.006, 1)
    cr.elements[1].position = 1.05; cr.elements[1].color = (0.36, 0.24, 0.13, 1)
    e = cr.elements.new(0.55); e.color = (0.13, 0.045, 0.018, 1)
    e = cr.elements.new(0.80); e.color = (0.24, 0.11, 0.05, 1)
    L.new(mixf.outputs[0], ramp.inputs['Fac'])
    # wrinkles: distorted bands + fine cracks + pores, all as bump
    wv = N.new("ShaderNodeTexWave"); wv.inputs['Scale'].default_value = 34; wv.inputs['Distortion'].default_value = 22
    wv.inputs['Detail'].default_value = 8; wv.inputs['Detail Scale'].default_value = 1.5
    L.new(tc.outputs['Object'], wv.inputs['Vector'])
    vor = N.new("ShaderNodeTexVoronoi"); vor.feature = 'DISTANCE_TO_EDGE'; vor.inputs['Scale'].default_value = 320
    vor.inputs['Randomness'].default_value = 1.0
    L.new(tc.outputs['Object'], vor.inputs['Vector'])
    crk = N.new("ShaderNodeMapRange"); crk.inputs['From Min'].default_value = 0.0; crk.inputs['From Max'].default_value = 0.035
    L.new(vor.outputs['Distance'], crk.inputs['Value'])
    n3 = N.new("ShaderNodeTexNoise"); n3.inputs['Scale'].default_value = 600; n3.inputs['Detail'].default_value = 4
    L.new(tc.outputs['Object'], n3.inputs['Vector'])
    cm = N.new("ShaderNodeTexNoise"); cm.inputs['Scale'].default_value = 6; cm.inputs['Detail'].default_value = 3
    L.new(tc.outputs['Object'], cm.inputs['Vector'])
    cmr = N.new("ShaderNodeMapRange"); cmr.inputs['From Min'].default_value = 0.5; cmr.inputs['From Max'].default_value = 0.65
    L.new(cm.outputs['Fac'], cmr.inputs['Value'])
    cinv = N.new("ShaderNodeMath"); cinv.operation = 'SUBTRACT'; cinv.inputs[0].default_value = 1.0
    L.new(crk.outputs[0], cinv.inputs[1])
    cmask = N.new("ShaderNodeMath"); cmask.operation = 'MULTIPLY'
    L.new(cinv.outputs[0], cmask.inputs[0]); L.new(cmr.outputs[0], cmask.inputs[1])
    crack = N.new("ShaderNodeMath"); crack.operation = 'SUBTRACT'; crack.inputs[0].default_value = 1.0
    L.new(cmask.outputs[0], crack.inputs[1])   # 1 = intact skin, 0 = in a crack
    h1 = N.new("ShaderNodeMath"); h1.operation = 'MULTIPLY_ADD'; h1.inputs[1].default_value = 0.45
    L.new(wv.outputs['Fac'], h1.inputs[0]); L.new(crack.outputs[0], h1.inputs[2])
    h2 = N.new("ShaderNodeMath"); h2.operation = 'MULTIPLY_ADD'; h2.inputs[1].default_value = 0.25
    L.new(n3.outputs['Fac'], h2.inputs[0]); L.new(h1.outputs[0], h2.inputs[2])
    bump = N.new("ShaderNodeBump"); bump.inputs['Strength'].default_value = 0.6; bump.inputs['Distance'].default_value = 0.0008
    L.new(h2.outputs[0], bump.inputs['Height']); L.new(bump.outputs['Normal'], p.inputs['Normal'])
    # cracks darken the colour slightly
    dk = N.new("ShaderNodeMix"); dk.data_type = 'RGBA'; dk.blend_type = 'MULTIPLY'
    fac = N.new("ShaderNodeMath"); fac.operation = 'MULTIPLY'; fac.inputs[1].default_value = 0.6
    L.new(cmask.outputs[0], fac.inputs[0]); L.new(fac.outputs[0], dk.inputs['Factor'])
    L.new(ramp.outputs['Color'], dk.inputs[6]); dk.inputs[7].default_value = (0.25, 0.12, 0.07, 1)
    L.new(dk.outputs[2], p.inputs['Base Color'])
    # dry but waxy: rough base with a thin glossy film in places
    rn = N.new("ShaderNodeMapRange"); rn.inputs['To Min'].default_value = 0.42; rn.inputs['To Max'].default_value = 0.7
    L.new(n1.outputs['Fac'], rn.inputs['Value']); L.new(rn.outputs[0], p.inputs['Roughness'])
    p.inputs['Coat Weight'].default_value = 0.35; p.inputs['Coat Roughness'].default_value = 0.2
    p.inputs['Subsurface Weight'].default_value = 0.08; p.inputs['Subsurface Radius'].default_value = (0.6, 0.25, 0.1)
    p.inputs['Subsurface Scale'].default_value = 0.004
    p.inputs['Specular IOR Level'].default_value = 0.5
    return m


def build_mummy(name="Mummy", pose=True):
    h = Human(name, gender=1.0, years=46, muscle=0.0, weight=0.0, height=0.3, extra=dict(MUMMY_TARGETS),
              eyebrows=None, eyelashes=None, eyes=False, skin=None)
    # rebuild body vertices with desiccation applied
    body_faces = h.base.faces_in(lambda n: n == "body")
    bv = np.unique(h.base.fvert[body_faces])
    from human import to_bl
    hc2 = desiccate(h.hc, h.base.fvert[body_faces], bv)
    co = to_bl(hc2)
    h.body.data.vertices.foreach_set("co", co.astype(np.float32).ravel())
    h.body.data.update()
    h.hc = hc2
    h.body.data.materials.clear()
    h.body.data.materials.append(mummy_skin(name + "_skin"))
    # large-scale shrivelled folds via displacement on the subdivided surface
    sub = h.body.modifiers["Subsurf"]; sub.levels = 2; sub.render_levels = 2
    tex = bpy.data.textures.new(name + "_folds", 'VORONOI'); tex.noise_scale = 0.035; tex.distance_metric = 'DISTANCE'
    tex2 = bpy.data.textures.new(name + "_lumps", 'CLOUDS'); tex2.noise_scale = 0.05; tex2.noise_depth = 4
    d1 = h.body.modifiers.new("Folds", 'DISPLACE'); d1.texture = tex; d1.strength = 0.003; d1.mid_level = 0.5
    d1.texture_coords = 'LOCAL'
    d2 = h.body.modifiers.new("Lumps", 'DISPLACE'); d2.texture = tex2; d2.strength = 0.004; d2.mid_level = 0.5
    d2.texture_coords = 'LOCAL'
    if pose:
        pose_mummy(h)
    return h
