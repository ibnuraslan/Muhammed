"""Oliver Deveau, first mate of the Dei Gratia (1872): a MakeHuman body (lib/human.py) dressed in code.

* Clothes are shells grown off the body surface (same skin weights, so they bend with him and never clip):
  linen shirt, knotted neckerchief, a double-breasted wool reefer jacket with a rolled collar and brass
  buttons, wool trousers and leather sea boots.
* Hair, beard, moustache and brows are real strands (Blender hair curves) grown on the posed, baked body and
  kept outside the skin with a BVH push-out.
* Eyes are aimed at a world target, lids follow.

    d = Deveau(); pose(d.h); d.finish(look_at=(x, y, z))
"""
import os, math, random
import numpy as np
import bpy, bmesh
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
import human as H

MASKS = os.path.expanduser("~/.config/blender/5.2/extensions/user_default/mpfb/data/textures")

HEAD = ("head", "jaw", "neck02", "neck03", "eye", "oculi", "oris", "levator", "risorius", "temporalis",
        "orbicularis", "special", "tongue")
HAND = ("wrist", "metacarpal", "finger")
FOOT = ("foot", "toe")


def _w(h, prefixes):
    idx = [i for i, b in enumerate(h.rig.bones) if b.split(".")[0].startswith(prefixes)]
    return h.W[:, idx].sum(1)


def _mask_at_uv(img_path, uv):
    img = bpy.data.images.load(img_path, check_existing=True)
    wid, hgt = img.size
    px = np.empty(wid * hgt * img.channels, np.float32); img.pixels.foreach_get(px)
    im = px.reshape(hgt, wid, img.channels)[..., 0]          # Blender rows run bottom-up, like UV v
    x = np.clip((uv[:, 0] * (wid - 1)).astype(int), 0, wid - 1)
    y = np.clip((uv[:, 1] * (hgt - 1)).astype(int), 0, hgt - 1)
    return im[y, x]


# ----------------------------------------------------------------------------- materials
def _mat(name):
    m = bpy.data.materials.new(name); m.use_nodes = True
    return m, m.node_tree.nodes, m.node_tree.links, m.node_tree.nodes["Principled BSDF"]


def wool_material(name, color, rough=0.92, sheen=0.6, weave=420.0, bump=0.35, wet=0.0, dirt=0.25):
    m, N, L, p = _mat(name)
    tc = N.new("ShaderNodeTexCoord")
    # felted wool: fine fibre noise + broad tonal wear
    fib = N.new("ShaderNodeTexNoise"); fib.inputs['Scale'].default_value = weave; fib.inputs['Detail'].default_value = 8
    fib.inputs['Roughness'].default_value = 0.7; L.new(tc.outputs['Object'], fib.inputs['Vector'])
    wear = N.new("ShaderNodeTexNoise"); wear.inputs['Scale'].default_value = 6; wear.inputs['Detail'].default_value = 5
    L.new(tc.outputs['Object'], wear.inputs['Vector'])
    base = N.new("ShaderNodeRGB"); base.outputs[0].default_value = (*color, 1)
    mx = N.new("ShaderNodeMix"); mx.data_type = 'RGBA'; mx.blend_type = 'OVERLAY'; mx.inputs['Factor'].default_value = dirt
    L.new(base.outputs[0], mx.inputs[6]); L.new(wear.outputs['Color'], mx.inputs[7])
    mx2 = N.new("ShaderNodeMix"); mx2.data_type = 'RGBA'; mx2.blend_type = 'MULTIPLY'; mx2.inputs['Factor'].default_value = 0.35
    L.new(mx.outputs[2], mx2.inputs[6]); L.new(fib.outputs['Color'], mx2.inputs[7])
    out = mx2.outputs[2]
    if wet:
        dk = N.new("ShaderNodeMix"); dk.data_type = 'RGBA'; dk.blend_type = 'MULTIPLY'; dk.inputs['Factor'].default_value = 1
        dk.inputs[7].default_value = (1 - 0.45 * wet, 1 - 0.45 * wet, 1 - 0.42 * wet, 1); L.new(out, dk.inputs[6]); out = dk.outputs[2]
    L.new(out, p.inputs['Base Color'])
    p.inputs['Roughness'].default_value = rough - 0.35 * wet
    p.inputs['Sheen Weight'].default_value = sheen; p.inputs['Sheen Roughness'].default_value = 0.5
    p.inputs['Sheen Tint'].default_value = (*[min(1.0, c * 6 + 0.12) for c in color], 1)
    p.inputs['Specular IOR Level'].default_value = 0.18 + 0.25 * wet
    b = N.new("ShaderNodeBump"); b.inputs['Strength'].default_value = bump; b.inputs['Distance'].default_value = 0.0015
    L.new(fib.outputs['Fac'], b.inputs['Height']); L.new(b.outputs['Normal'], p.inputs['Normal'])
    return m


def linen_material(name, color=(0.62, 0.57, 0.48), wet=0.0):
    m, N, L, p = _mat(name)
    tc = N.new("ShaderNodeTexCoord")
    wv = N.new("ShaderNodeTexWave"); wv.inputs['Scale'].default_value = 900; wv.inputs['Distortion'].default_value = 2
    L.new(tc.outputs['Object'], wv.inputs['Vector'])
    nz = N.new("ShaderNodeTexNoise"); nz.inputs['Scale'].default_value = 30; L.new(tc.outputs['Object'], nz.inputs['Vector'])
    c = N.new("ShaderNodeRGB"); c.outputs[0].default_value = (*color, 1)
    mx = N.new("ShaderNodeMix"); mx.data_type = 'RGBA'; mx.blend_type = 'OVERLAY'; mx.inputs['Factor'].default_value = 0.3
    L.new(c.outputs[0], mx.inputs[6]); L.new(nz.outputs['Color'], mx.inputs[7]); L.new(mx.outputs[2], p.inputs['Base Color'])
    p.inputs['Roughness'].default_value = 0.85 - 0.3 * wet; p.inputs['Sheen Weight'].default_value = 0.3
    b = N.new("ShaderNodeBump"); b.inputs['Strength'].default_value = 0.2; b.inputs['Distance'].default_value = 0.0008
    L.new(wv.outputs['Fac'], b.inputs['Height']); L.new(b.outputs['Normal'], p.inputs['Normal'])
    return m


def leather_material(name, color=(0.06, 0.035, 0.02), rough=0.42, wet=0.3):
    m, N, L, p = _mat(name)
    tc = N.new("ShaderNodeTexCoord")
    vo = N.new("ShaderNodeTexVoronoi"); vo.inputs['Scale'].default_value = 260; L.new(tc.outputs['Object'], vo.inputs['Vector'])
    nz = N.new("ShaderNodeTexNoise"); nz.inputs['Scale'].default_value = 14; nz.inputs['Detail'].default_value = 6
    L.new(tc.outputs['Object'], nz.inputs['Vector'])
    c = N.new("ShaderNodeRGB"); c.outputs[0].default_value = (*color, 1)
    mx = N.new("ShaderNodeMix"); mx.data_type = 'RGBA'; mx.blend_type = 'OVERLAY'; mx.inputs['Factor'].default_value = 0.5
    L.new(c.outputs[0], mx.inputs[6]); L.new(nz.outputs['Color'], mx.inputs[7]); L.new(mx.outputs[2], p.inputs['Base Color'])
    rr = N.new("ShaderNodeMapRange"); rr.inputs['To Min'].default_value = rough - 0.2 * wet - 0.1; rr.inputs['To Max'].default_value = rough + 0.15
    L.new(nz.outputs['Fac'], rr.inputs['Value']); L.new(rr.outputs[0], p.inputs['Roughness'])
    p.inputs['Coat Weight'].default_value = 0.4 * wet; p.inputs['Coat Roughness'].default_value = 0.15
    b = N.new("ShaderNodeBump"); b.inputs['Strength'].default_value = 0.25; b.inputs['Distance'].default_value = 0.0006
    L.new(vo.outputs['Distance'], b.inputs['Height']); L.new(b.outputs['Normal'], p.inputs['Normal'])
    return m


def brass_material(name="brass"):
    m, N, L, p = _mat(name)
    p.inputs['Base Color'].default_value = (0.55, 0.38, 0.16, 1); p.inputs['Metallic'].default_value = 1.0
    nz = N.new("ShaderNodeTexNoise"); nz.inputs['Scale'].default_value = 80
    rr = N.new("ShaderNodeMapRange"); rr.inputs['To Min'].default_value = 0.25; rr.inputs['To Max'].default_value = 0.55
    L.new(nz.outputs['Fac'], rr.inputs['Value']); L.new(rr.outputs[0], p.inputs['Roughness'])
    return m


def hair_material(name, melanin=0.78, redness=0.35, rough=0.32, grey=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links
    for n in list(N):
        if n.type != 'OUTPUT_MATERIAL':
            N.remove(n)
    hb = N.new("ShaderNodeBsdfHairPrincipled")
    try:
        hb.parametrization = 'MELANIN'
    except Exception:
        pass
    hb.inputs['Melanin'].default_value = melanin; hb.inputs['Melanin Redness'].default_value = redness
    hb.inputs['Roughness'].default_value = rough; hb.inputs['Radial Roughness'].default_value = 0.4
    hb.inputs['Coat'].default_value = 0.1
    if 'Random Color' in hb.inputs:
        hb.inputs['Random Color'].default_value = 0.15
    if 'Random Roughness' in hb.inputs:
        hb.inputs['Random Roughness'].default_value = 0.2
    L.new(hb.outputs[0], N["Material Output"].inputs['Surface'])
    return m


def sailor_skin(name, base=(0.43, 0.25, 0.16), weather=0.6):
    """Wind-burnt skin: procedural base (MakeHuman ships no skin textures here) with MPFB UV masks for lips and
    nails, redder cheeks/nose, stubble shadow, SSS and pores (lib/human.skin_material does the pore bump)."""
    m = H.skin_material(name, None, color=base, rough=0.5, sss=0.3, bump=0.3)
    N = m.node_tree.nodes; L = m.node_tree.links; p = N["Principled BSDF"]
    src = p.inputs['Base Color'].links[0].from_socket
    uv = N.new("ShaderNodeUVMap"); uv.uv_map = "UVMap"
    def mask(fn):
        t = N.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(os.path.join(MASKS, fn), check_existing=True)
        t.image.colorspace_settings.name = 'Non-Color'; L.new(uv.outputs['UV'], t.inputs['Vector']); return t.outputs['Color']
    tc = N.new("ShaderNodeTexCoord")
    # weathering: broad blotches of redness on the exposed skin
    bl = N.new("ShaderNodeTexNoise"); bl.inputs['Scale'].default_value = 7; bl.inputs['Detail'].default_value = 3
    L.new(tc.outputs['Object'], bl.inputs['Vector'])
    br = N.new("ShaderNodeMapRange"); br.inputs['From Min'].default_value = 0.45; br.inputs['From Max'].default_value = 0.7
    br.inputs['To Max'].default_value = 0.35 * weather; L.new(bl.outputs['Fac'], br.inputs['Value'])
    red = N.new("ShaderNodeMix"); red.data_type = 'RGBA'; red.blend_type = 'MULTIPLY'
    red.inputs[7].default_value = (1.0, 0.62, 0.55, 1); L.new(br.outputs[0], red.inputs['Factor']); L.new(src, red.inputs[6])
    lips = N.new("ShaderNodeMix"); lips.data_type = 'RGBA'; lips.blend_type = 'MULTIPLY'
    lips.inputs[7].default_value = (0.72, 0.42, 0.40, 1); L.new(mask("mpfb_lips.jpg"), lips.inputs['Factor'])
    L.new(red.outputs[2], lips.inputs[6])
    nails = N.new("ShaderNodeMix"); nails.data_type = 'RGBA'; nails.blend_type = 'MIX'
    nails.inputs[7].default_value = (0.42, 0.28, 0.23, 1)
    nf = N.new("ShaderNodeMath"); nf.operation = 'MULTIPLY'; nf.inputs[1].default_value = 0.6
    L.new(mask("mpfb_fingernails.jpg"), nf.inputs[0]); L.new(nf.outputs[0], nails.inputs['Factor'])
    L.new(lips.outputs[2], nails.inputs[6])
    # regions: wind-burn, socket shadow, oily T-zone (vertex colour 'skinvar', see Deveau._skin_regions)
    at = N.new("ShaderNodeAttribute"); at.attribute_name = "skinvar"
    spc = N.new("ShaderNodeSeparateColor"); L.new(at.outputs['Color'], spc.inputs[0])
    rr = N.new("ShaderNodeMix"); rr.data_type = 'RGBA'; rr.blend_type = 'MULTIPLY'; rr.inputs[7].default_value = (1.0, 0.58, 0.5, 1)
    rf = N.new("ShaderNodeMath"); rf.operation = 'MULTIPLY'; rf.inputs[1].default_value = 0.55; L.new(spc.outputs[0], rf.inputs[0])
    L.new(rf.outputs[0], rr.inputs['Factor']); L.new(nails.outputs[2], rr.inputs[6])
    sk = N.new("ShaderNodeMix"); sk.data_type = 'RGBA'; sk.blend_type = 'MULTIPLY'; sk.inputs[7].default_value = (0.62, 0.5, 0.48, 1)
    sf = N.new("ShaderNodeMath"); sf.operation = 'MULTIPLY'; sf.inputs[1].default_value = 0.6; L.new(spc.outputs[1], sf.inputs[0])
    L.new(sf.outputs[0], sk.inputs['Factor']); L.new(rr.outputs[2], sk.inputs[6])
    L.new(sk.outputs[2], p.inputs['Base Color'])
    rs = p.inputs['Roughness'].links[0].from_socket
    ro = N.new("ShaderNodeMath"); ro.operation = 'MULTIPLY_ADD'; ro.inputs[1].default_value = -0.16
    L.new(spc.outputs[2], ro.inputs[0]); L.new(rs, ro.inputs[2]); L.new(ro.outputs[0], p.inputs['Roughness'])
    p.inputs['Subsurface Weight'].default_value = 0.55
    p.inputs['Subsurface Radius'].default_value = (1.0, 0.38, 0.18)
    p.inputs['Subsurface Scale'].default_value = 0.009
    p.inputs['Coat Weight'].default_value = 0.08; p.inputs['Coat Roughness'].default_value = 0.35
    return m


def mesh_obj(name, verts, faces, mat):
    me = bpy.data.meshes.new(name); me.from_pydata([tuple(v) for v in verts], [], faces); me.update()
    me.polygons.foreach_set("use_smooth", np.ones(len(me.polygons), bool))
    o = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(o); o.data.materials.append(mat)
    return o


def boot_leather(name, color=(0.055, 0.034, 0.02), rough=0.62, creases=1.0):
    """Matte, worn, salt-stained boot leather: creases across the vamp and ankle, scuffed toes and edges,
    pale salt tide-marks low on the boot."""
    m, N, L, p = _mat(name)
    tc = N.new("ShaderNodeTexCoord")
    base = N.new("ShaderNodeRGB"); base.outputs[0].default_value = (*color, 1)
    wear = N.new("ShaderNodeTexNoise"); wear.inputs['Scale'].default_value = 40; wear.inputs['Detail'].default_value = 8
    L.new(tc.outputs['Object'], wear.inputs['Vector'])
    sc = N.new("ShaderNodeMapRange"); sc.inputs['From Min'].default_value = 0.55; sc.inputs['From Max'].default_value = 0.75
    sc.inputs['To Max'].default_value = 0.35; L.new(wear.outputs['Fac'], sc.inputs['Value'])
    mx = N.new("ShaderNodeMix"); mx.data_type = 'RGBA'; mx.inputs[7].default_value = (0.16, 0.11, 0.075, 1)   # scuffed
    L.new(sc.outputs[0], mx.inputs['Factor']); L.new(base.outputs[0], mx.inputs[6])
    geo = N.new("ShaderNodeNewGeometry"); sp = N.new("ShaderNodeSeparateXYZ"); L.new(geo.outputs['Position'], sp.inputs[0])
    salt = N.new("ShaderNodeTexNoise"); salt.inputs['Scale'].default_value = 9; L.new(tc.outputs['Object'], salt.inputs['Vector'])
    zz = N.new("ShaderNodeMath"); zz.operation = 'MULTIPLY_ADD'; zz.inputs[1].default_value = 0.03
    L.new(salt.outputs['Fac'], zz.inputs[0]); L.new(sp.outputs['Z'], zz.inputs[2])
    sm = N.new("ShaderNodeMapRange"); sm.inputs['From Min'].default_value = 0.085; sm.inputs['From Max'].default_value = 0.05
    sm.inputs['To Max'].default_value = 0.18; L.new(zz.outputs[0], sm.inputs['Value'])
    mx2 = N.new("ShaderNodeMix"); mx2.data_type = 'RGBA'; mx2.inputs[7].default_value = (0.36, 0.32, 0.27, 1)  # salt
    L.new(sm.outputs[0], mx2.inputs['Factor']); L.new(mx.outputs[2], mx2.inputs[6])
    L.new(mx2.outputs[2], p.inputs['Base Color'])
    rr = N.new("ShaderNodeMapRange"); rr.inputs['To Min'].default_value = rough - 0.12; rr.inputs['To Max'].default_value = rough + 0.15
    L.new(wear.outputs['Fac'], rr.inputs['Value']); L.new(rr.outputs[0], p.inputs['Roughness'])
    p.inputs['Specular IOR Level'].default_value = 0.35
    # creases: stretched noise across the boot + fine grain
    mp = N.new("ShaderNodeMapping"); mp.inputs['Scale'].default_value = (60, 6, 60); L.new(tc.outputs['Object'], mp.inputs['Vector'])
    cr = N.new("ShaderNodeTexNoise"); cr.inputs['Scale'].default_value = 1.0; cr.inputs['Detail'].default_value = 4
    L.new(mp.outputs[0], cr.inputs['Vector'])
    gr = N.new("ShaderNodeTexVoronoi"); gr.inputs['Scale'].default_value = 900; L.new(tc.outputs['Object'], gr.inputs['Vector'])
    b1 = N.new("ShaderNodeBump"); b1.inputs['Strength'].default_value = 0.35 * creases; b1.inputs['Distance'].default_value = 0.002
    L.new(cr.outputs['Fac'], b1.inputs['Height'])
    b2 = N.new("ShaderNodeBump"); b2.inputs['Strength'].default_value = 0.15; b2.inputs['Distance'].default_value = 0.0003
    L.new(gr.outputs['Distance'], b2.inputs['Height']); L.new(b1.outputs['Normal'], b2.inputs['Normal'])
    L.new(b2.outputs['Normal'], p.inputs['Normal'])
    return m


# ----------------------------------------------------------------------------- the man
class Deveau:
    def __init__(self, name="Deveau", years=34, wet=0.35, cap=False):
        extra = {"targets/chin/chin-prominent-incr": 0.3, "targets/nose/nose-hump-incr": 0.4,
                 "targets/nose/nose-scale-vert-incr": 0.2, "targets/eyebrows/eyebrows-trans-down": 0.3,
                 "targets/cheek/l-cheek-bones-incr": 0.35, "targets/cheek/r-cheek-bones-incr": 0.35,
                 "targets/head/head-age-incr": 0.25, "targets/chin/chin-bones-incr": 0.3}
        self.h = H.Human(name, gender=1.0, years=years, muscle=0.66, weight=0.52, height=0.56,
                         extra=extra, eyebrows=None, eyelashes=None, skin=None)
        h = self.h
        h.body.data.materials[0] = sailor_skin(name + "_skin")
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

    def _skin_regions(self):
        """Vertex colour 'skinvar': R = wind-burn redness (nose, cheeks, ears), G = shadowed eye sockets,
        B = oily T-zone (forehead, nose) for a lower roughness. Drives sailor_skin."""
        h = self.h; co = H.to_bl(h.hc)
        ec = (np.array(h.joint("eye.L____head")) + np.array(h.joint("eye.R____head"))) / 2
        r = co - ec; x, y, z = r[:, 0], r[:, 1], r[:, 2]
        g = lambda cx, cy, cz, sx, sy, sz: np.exp(-(((x - cx) / sx) ** 2 + ((y - cy) / sy) ** 2 + ((z - cz) / sz) ** 2))
        red = np.clip(0.9 * g(0, -0.06, -0.035, 0.018, 0.03, 0.025) + 0.7 * g(0.045, -0.035, -0.03, 0.025, 0.03, 0.025)
                      + 0.7 * g(-0.045, -0.035, -0.03, 0.025, 0.03, 0.025) + 0.35 * g(0.075, 0.01, -0.01, 0.015, 0.03, 0.03)
                      + 0.35 * g(-0.075, 0.01, -0.01, 0.015, 0.03, 0.03), 0, 1)
        sock = np.clip(0.8 * g(0.032, -0.01, -0.004, 0.022, 0.03, 0.016) + 0.8 * g(-0.032, -0.01, -0.004, 0.022, 0.03, 0.016), 0, 1)
        oily = np.clip(g(0, -0.05, 0.05, 0.03, 0.05, 0.03) + g(0, -0.06, -0.03, 0.012, 0.04, 0.03), 0, 1)
        ca = h.body.data.color_attributes.new("skinvar", 'FLOAT_COLOR', 'POINT')
        ca.data.foreach_set("color", np.stack([red, sock, oily, np.ones_like(red)], 1).astype(np.float32).ravel())

    # ------------------------------------------------------------------ clothes
    def _shell(self, label, vmask, offset, mat, solid=0.003, smooth=0.0, displace=0.0, keep_faces=None, drape=0, flare=None):
        h = self.h
        fsel = [f for f in self.faces if all(vmask[list(f)])]
        if keep_faces is not None:
            fsel = [f for f in fsel if keep_faces(f)]
        used = sorted({v for f in fsel for v in f}); remap = {v: i for i, v in enumerate(used)}
        body = self.rest_co[used]; nrm = self.rest_n[used]
        off = np.full(len(used), offset)
        if flare is not None:
            off = off + flare(body)
        co = body + nrm * off[:, None]
        if drape:
            # cloth bridges the body's hollows: Laplacian-smooth the shell, then push it back out so it never
            # comes closer to the skin than `offset` along the rest normal (no clipping, no muscle definition)
            nb = [[] for _ in used]
            for f in fsel:
                ff = [remap[v] for v in dict.fromkeys(f)]
                for a in range(len(ff)):
                    nb[ff[a]] += [ff[a - 1], ff[(a + 1) % len(ff)]]
            ecount = {}
            for f in fsel:
                ff = [remap[v] for v in dict.fromkeys(f)]
                for a in range(len(ff)):
                    e = tuple(sorted((ff[a - 1], ff[a]))); ecount[e] = ecount.get(e, 0) + 1
            pin = np.zeros(len(used), bool)
            for e, c in ecount.items():
                if c == 1:
                    pin[list(e)] = True               # garment edges (hems, cuffs) stay where they are
            nb = [np.array(sorted(set(n))) for n in nb]
            for _ in range(drape):
                avg = np.array([co[n].mean(0) if len(n) else co[i] for i, n in enumerate(nb)])
                avg[pin] = co[pin]
                co = co * 0.4 + avg * 0.6
                d = ((co - body) * nrm).sum(1)
                co += nrm * np.maximum(off - d, 0)[:, None]
        me = bpy.data.meshes.new(f"{self.name}_{label}")
        me.from_pydata(co.tolist(), [], [[remap[v] for v in f] for f in fsel]); me.update()
        me.polygons.foreach_set("use_smooth", np.ones(len(me.polygons), bool))
        o = bpy.data.objects.new(me.name, me); bpy.context.collection.objects.link(o)
        o.data.materials.append(mat)
        h.rig.skin(o, h.W[used])
        if smooth:
            sm = o.modifiers.new("Smooth", "SMOOTH"); sm.factor = smooth; sm.iterations = 6
        if displace:
            tx = bpy.data.textures.new(f"{label}_folds", "CLOUDS"); tx.noise_scale = 0.06; tx.noise_depth = 2
            d = o.modifiers.new("Folds", "DISPLACE"); d.texture = tx; d.strength = displace; d.mid_level = 0.5
            d.texture_coords = 'OBJECT'
        s = o.modifiers.new("Sub", "SUBSURF"); s.levels = 1; s.render_levels = 2
        if solid:
            so = o.modifiers.new("Thick", "SOLIDIFY"); so.thickness = solid; so.offset = -1; so.use_even_offset = True
        h.parts.append(o)
        o["src_verts"] = used
        return o, used

    def _hide_skin(self, vmask, erode=2):
        """Delete body faces that lie completely under a garment (eroded so the edges stay covered)."""
        h = self.h
        m = vmask.copy()
        for _ in range(erode):
            bad = np.zeros_like(m)
            for f in self.faces:
                fl = list(f)
                if not all(m[fl]):
                    bad[fl] = True
            m &= ~bad
        bm = bmesh.new(); bm.from_mesh(h.body.data); bm.verts.ensure_lookup_table()
        kill = [f for f in bm.faces if all(m[v.index] for v in f.verts)]
        bmesh.ops.delete(bm, geom=kill, context='FACES_ONLY')
        bm.to_mesh(h.body.data); bm.free(); h.body.data.update()

    def _dress(self):
        h = self.h; co = self.rest_co
        wh = _w(h, HEAD); wn = _w(h, ("neck01",)); whand = _w(h, HAND); wfoot = _w(h, FOOT)
        z = co[:, 2]; x = co[:, 0]; y = co[:, 1]
        hip_z = h.joint("upperleg01.L____head")[2]
        neck_z = h.joint("neck01____head")[2]
        ankle_z = h.joint("foot.L____head")[2]; knee_z = h.joint("lowerleg01.L____head")[2]
        wrist = np.array(h.joint("wrist.L____head"))
        self.marks = dict(hip=hip_z, neck=neck_z, ankle=ankle_z, knee=knee_z)
        u = self.used
        # ---- shirt (linen): torso + arms to the wrist, up the neck a little
        shirt = u & (wh < 0.35) & (whand < 0.25) & (z > hip_z - 0.06) & (z < neck_z + 0.035)
        self.shirt, _ = self._shell("shirt", shirt, 0.004, linen_material("shirt", wet=self.wet), solid=0.0015, displace=0.002)
        # ---- neckerchief: a band round the neck
        nk = u & (z > neck_z - 0.02) & (z < neck_z + 0.045) & (wh < 0.6) & (whand < 0.1)
        self.scarf, _ = self._shell("scarf", nk, 0.011, wool_material("scarf", (0.20, 0.035, 0.025), rough=0.8, sheen=0.3, weave=900, dirt=0.3),
                                    solid=0.003, displace=0.003)
        # ---- trousers (wool): pelvis and legs down to the boot tops
        trous = u & (z < hip_z + 0.11) & (z > ankle_z + 0.2) & (wfoot < 0.2) & (whand < 0.05)
        self.trousers, _ = self._shell("trousers", trous, 0.009, wool_material("trousers", (0.022, 0.02, 0.019), weave=500, wet=self.wet, sheen=0.25),
                                       solid=0.002, displace=0.004, drape=14,
                                       flare=lambda b: np.clip((knee_z + 0.1 - b[:, 2]) / 0.4, 0, 1) * 0.006)
        # ---- boots (leather): feet and shins, smoothed so the toes read as a boot
        boot = u & (z < ankle_z + 0.27)
        self.boot_mask = boot.copy()
        self.boots, _ = self._shell("boots", boot, 0.011, leather_material("boots", wet=self.wet + 0.2), solid=0.0025, drape=90,
                                    flare=lambda b: np.clip((ankle_z - b[:, 2]) / 0.06, 0, 1) * 0.006)
        # ---- reefer jacket (heavy navy wool): torso + arms, hem at the hip, cuffs short of the wrist
        dist_wrist = np.minimum(np.linalg.norm(co - wrist, axis=1), np.linalg.norm(co - wrist * np.array([-1, 1, 1]), axis=1))
        jacket = u & (wh < 0.2) & (whand < 0.05) & (z > hip_z - 0.13) & (z < neck_z + 0.01) & (dist_wrist > 0.045)
        self.jacket, jv = self._shell("jacket", jacket, 0.014, wool_material("jacket", (0.010, 0.012, 0.02), weave=380, wet=self.wet, dirt=0.18, sheen=0.3),
                                      solid=0.005, displace=0.003, drape=12,
                                      flare=lambda b: np.clip((hip_z + 0.05 - b[:, 2]) / 0.15, 0, 1) * 0.012)
        self._collar(self.jacket)
        self._buttons(jv)
        self._hide_skin(shirt | trous | boot | jacket)

    def _collar(self, o):
        """Roll the jacket's neck opening up and out into a collar."""
        me = o.data; bm = bmesh.new(); bm.from_mesh(me)
        top = max(v.co.z for v in bm.verts)
        edges = [e for e in bm.edges if e.is_boundary and all(v.co.z > top - 0.06 for v in e.verts)]
        if not edges:
            bm.free(); return
        c = sum((v.co for e in edges for v in e.verts), Vector()) / (2 * len(edges))
        r = bmesh.ops.extrude_edge_only(bm, edges=edges)
        nv = [g for g in r["geom"] if isinstance(g, bmesh.types.BMVert)]
        for v in nv:
            d = Vector((v.co.x - c.x, v.co.y - c.y, 0)).normalized()
            v.co += d * 0.004 + Vector((0, 0, 0.018))
        ne = [g for g in r["geom"] if isinstance(g, bmesh.types.BMEdge) and all(vv in nv for vv in g.verts)]
        r2 = bmesh.ops.extrude_edge_only(bm, edges=ne)
        for v in [g for g in r2["geom"] if isinstance(g, bmesh.types.BMVert)]:
            d = Vector((v.co.x - c.x, v.co.y - c.y, 0)).normalized()
            v.co += d * 0.008 + Vector((0, 0, 0.022))       # upturned collar, against the weather
        bm.to_mesh(me); bm.free(); me.update()
        # new vertices take the weights of their nearest neighbours already in the groups
        self._fill_weights(o)

    def _fill_weights(self, o):
        me = o.data
        have = np.zeros(len(me.vertices), bool)
        for v in me.vertices:
            if len(v.groups):
                have[v.index] = True
        if have.all():
            return
        from mathutils.kdtree import KDTree
        idx = np.nonzero(have)[0]; kd = KDTree(len(idx))
        for i in idx:
            kd.insert(me.vertices[int(i)].co, int(i))
        kd.balance()
        for v in me.vertices:
            if have[v.index]:
                continue
            _, j, _ = kd.find(v.co)
            for g in me.vertices[j].groups:
                o.vertex_groups[g.group].add([v.index], g.weight, 'REPLACE')

    def _buttons(self, jv):
        """Two rows of brass buttons down the front of the double-breasted jacket (parented to the chest bone)."""
        h = self.h; co = self.rest_co[jv] + self.rest_n[jv] * 0.02
        front = co[(co[:, 1] < -0.02)]
        mat = brass_material(self.name + "_brass")
        self.button_objs = []
        zmin, zmax = self.marks["hip"] - 0.08, self.marks["neck"] - 0.12
        for k in range(4):
            zz = zmax - k * (zmax - zmin) / 3.4
            for sx in (-0.07, 0.07):
                cand = front[np.abs(front[:, 2] - zz) < 0.012]
                if len(cand) == 0:
                    continue
                p = cand[np.argmin(np.abs(cand[:, 0] - sx))]
                bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=0.0085, depth=0.004, location=tuple(p),
                                                    rotation=(math.pi / 2, 0, 0))
                b = bpy.context.active_object; b.name = "button"
                bv = b.modifiers.new("Bevel", "BEVEL"); bv.width = 0.0015; bv.segments = 3
                bpy.ops.object.shade_smooth()
                b.data.materials.append(mat)
                mw = b.matrix_world.copy()
                b.parent = h.arm; b.parent_type = 'BONE'; b.parent_bone = "spine03"
                bpy.context.view_layer.update(); b.matrix_world = mw
                self.button_objs.append(b)

    def lids(self, amount):
        """Lower the upper lids (looking down): MakeHuman's orbicularis03 bones are the upper lids."""
        for sd in ("L", "R"):
            b = f"orbicularis03.{sd}"
            if b in self.h.arm.pose.bones:
                self.h.rot(b, (1, 0, 0), 18 * amount)

    def brow_knit(self, amount):
        """Concern: inner brows drawn down and together (oculi01 / oculi02 bones)."""
        for sd, sg in (("L", 1), ("R", -1)):
            for b, ax, d in ((f"oculi01.{sd}", (1, 0, 0), 6), (f"oculi02.{sd}", (0, 0, sg), 5)):
                if b in self.h.arm.pose.bones:
                    self.h.rot(b, ax, d * amount)

    # ------------------------------------------------------------------ after posing
    def finish(self, look_at=None, lids=0.0, hair=True, density=1.0, place=None):
        """Bake the pose, grow hair, aim the eyes, then move him to `place` (a world Matrix).
        look_at is in world space (after placing)."""
        h = self.h
        if place is not None and look_at is not None:
            look_at = place.inverted() @ Vector(look_at)
        bpy.context.view_layer.update()
        head_M = (h.arm.matrix_world @ h.arm.pose.bones["head"].matrix).copy()
        head_R = head_M.to_3x3() @ h.arm.data.bones["head"].matrix_local.to_3x3().inverted()
        self.head_R = head_R
        for b in self.button_objs + h.eyes:
            mw = b.matrix_world.copy(); b.parent = None; b.matrix_world = mw
        H.bake_pose(h)
        if look_at is not None:
            for e in h.eyes:
                d = (Vector(look_at) - e.location).normalized()
                e.rotation_mode = 'QUATERNION'; e.rotation_quaternion = (-d).to_track_quat('Y', 'Z')
        self._corneas()
        if not self._asset_boots():
            self._sea_boots()
        if hair:
            self._grow_all(density)
        h.arm.hide_render = True; h.arm.hide_viewport = True
        if place is not None:
            for o in self.objects:
                if o.parent is None:
                    o.matrix_world = place @ o.matrix_world
            bpy.context.view_layer.update()

    def _corneas(self):
        """A clear, wet cornea over each eyeball: the bulge catches sharp highlights (no more 'dead' eyes)."""
        cm = bpy.data.materials.new(self.name + "_cornea"); cm.use_nodes = True
        N = cm.node_tree.nodes; L = cm.node_tree.links; p = N["Principled BSDF"]
        # clear film: see-through (no refraction), with a fresnel mirror layer for the wet highlight
        gl = N.new("ShaderNodeBsdfGlossy"); gl.inputs['Roughness'].default_value = 0.02
        tr = N.new("ShaderNodeBsdfTransparent"); fr = N.new("ShaderNodeFresnel"); fr.inputs['IOR'].default_value = 1.376
        mx = N.new("ShaderNodeMixShader"); L.new(fr.outputs[0], mx.inputs[0]); L.new(tr.outputs[0], mx.inputs[1]); L.new(gl.outputs[0], mx.inputs[2])
        lp = N.new("ShaderNodeLightPath"); mx2 = N.new("ShaderNodeMixShader")
        L.new(lp.outputs['Is Shadow Ray'], mx2.inputs[0]); L.new(mx.outputs[0], mx2.inputs[1]); L.new(tr.outputs[0], mx2.inputs[2])
        L.new(mx2.outputs[0], N["Material Output"].inputs['Surface'])
        self.corneas = []
        for e in self.h.eyes:
            r = e.dimensions.x / 2
            bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=32, radius=r * 1.012, location=e.matrix_world.translation)
            c = bpy.context.active_object; c.name = self.name + "_cornea"
            for v in c.data.vertices:                         # bulge forward (local -Y is where the iris looks)
                if v.co.y < 0:
                    k = max(0.0, -v.co.y / (r * 1.012)) ** 3
                    v.co.y -= r * 0.06 * k
            bpy.ops.object.shade_smooth()
            c.data.materials.append(cm)
            c.rotation_mode = 'QUATERNION'; c.rotation_quaternion = e.matrix_world.to_quaternion()
            self.corneas.append(c); self.h.parts.append(c)

    BOOT_ASSET = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "sketchfab",
                              "988f94a8fc6945749e2b2ffdcce05e98.glb")   # "Leather boots" by kifir, CC-BY (see CREDITS)

    def _asset_boots(self):
        """Fit a scanned/modelled pair of leather boots (Sketchfab CC-BY) to the posed feet: split the pair, scale each
        boot to the foot length, turn it to the foot, stand it on the ground, widen the shaft where the leg needs room."""
        if not os.path.exists(self.BOOT_ASSET):
            return False
        h = self.h
        P = np.array([v.co[:] for v in h.body.data.vertices])
        before = set(bpy.data.objects)
        bpy.ops.import_scene.gltf(filepath=self.BOOT_ASSET)
        new = [o for o in bpy.data.objects if o not in before]
        ms = [o for o in new if o.type == 'MESH']
        others = [o.name for o in new if o.type != 'MESH']
        bpy.ops.object.select_all(action='DESELECT')
        for o in ms:
            o.select_set(True)
        bpy.context.view_layer.objects.active = ms[0]
        bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        if len(ms) > 1:
            bpy.ops.object.join()
        pair = bpy.context.active_object
        for nm in others:
            if nm in bpy.data.objects:
                bpy.data.objects.remove(bpy.data.objects[nm])
        V = np.array([v.co[:] for v in pair.data.vertices])
        lo, hi = V.min(0), V.max(0); size = hi - lo
        ax = int(np.argmax(size[:2]))                    # the pair stands side by side along this axis
        mid = (lo[ax] + hi[ax]) / 2
        # keep one whole boot: the connected parts whose centre lies on the low side of the pair
        bm = bmesh.new(); bm.from_mesh(pair.data); bm.verts.ensure_lookup_table()
        seen = set(); kill = []
        for v0 in bm.verts:
            if v0.index in seen:
                continue
            comp = []; stack = [v0]; seen.add(v0.index)
            while stack:
                v = stack.pop(); comp.append(v)
                for e in v.link_edges:
                    w = e.other_vert(v)
                    if w.index not in seen:
                        seen.add(w.index); stack.append(w)
            if sum(v.co[ax] for v in comp) / len(comp) > mid:
                kill += comp
        bmesh.ops.delete(bm, geom=kill, context='VERTS'); bm.to_mesh(pair.data); bm.free()
        B0 = np.array([v.co[:] for v in pair.data.vertices])
        blo, bhi = B0.min(0), B0.max(0)
        low = B0[B0[:, 2] < blo[2] + 0.12 * (bhi[2] - blo[2])]
        lc = low[:, :2].mean(0); w_, v_ = np.linalg.eigh(np.cov((low[:, :2] - lc).T)); bl = v_[:, np.argmax(w_)]
        shaft = B0[B0[:, 2] > blo[2] + 0.6 * (bhi[2] - blo[2])]
        if ((low[:, :2] - shaft[:, :2].mean(0)) @ bl).max() < -((low[:, :2] - shaft[:, :2].mean(0)) @ bl).min():
            bl = -bl                                          # toe end = the far end of the sole from the shaft
        bs = np.array([-bl[1], bl[0]])
        ub = (B0[:, :2] - lc) @ bl; vb = (B0[:, :2] - lc) @ bs; zb = B0[:, 2] - blo[2]
        blen = float(ub.max() - ub.min())
        self.boots.hide_render = True; self.boots.hide_viewport = True
        self.sea_boots = []
        for sg in (1, -1):
            side = self.used & (np.sign(self.rest_co[:, 0]) == sg)
            foot = P[side & (self.rest_co[:, 2] < self.marks["ankle"] + 0.03)]
            g = float(foot[:, 2].min())
            ank = np.array(h.bone_head(f"foot.{'L' if sg > 0 else 'R'}"))[:2]
            xy = foot[:, :2] - foot[:, :2].mean(0)
            w2, v2 = np.linalg.eigh(np.cov(xy.T)); fwd = v2[:, np.argmax(w2)]
            if ((foot[:, :2] - ank) @ fwd).mean() < 0:
                fwd = -fwd
            fl = float((xy @ fwd).max() - (xy @ fwd).min()); heel_u = float((xy @ fwd).min())
            k = (fl + 0.04) / blen
            o = pair.copy(); o.data = pair.data.copy(); bpy.context.collection.objects.link(o)
            u = ub * k; vv = vb * k * (1 if sg < 0 else -1); z = zb * k     # mirror for the other foot
            u = u + (heel_u - 0.022) - float(u.min())
            side_v = np.array([-fwd[1], fwd[0]]); c0 = foot[:, :2].mean(0)
            W = np.column_stack([c0 + np.outer(u, fwd) + np.outer(vv, side_v), z + g])
            if sg > 0:                                        # mirrored: flip the faces so normals point out
                bmm = bmesh.new(); bmm.from_mesh(o.data); bmesh.ops.reverse_faces(bmm, faces=bmm.faces); bmm.to_mesh(o.data); bmm.free()
            # make room for the shin and trouser leg in the shaft
            leg = P[side & (self.rest_co[:, 2] > self.marks["ankle"]) & (self.rest_co[:, 2] < self.marks["ankle"] + 0.4)]
            for zz in np.linspace(g + 0.12, g + float(z.max()) - 0.01, 10):
                band = np.abs(W[:, 2] - zz) < 0.03; lb = leg[np.abs(leg[:, 2] - zz) < 0.03]
                if band.sum() < 6 or len(lb) < 4:
                    continue
                cc = lb[:, :2].mean(0)
                need = float(np.linalg.norm(lb[:, :2] - cc, axis=1).max()) + 0.016
                have = float(np.median(np.linalg.norm(W[band, :2] - cc, axis=1)))
                if have < need:
                    f = need / have
                    W[band, :2] = cc + (W[band, :2] - cc) * f
            o.data.vertices.foreach_set("co", W.astype(np.float32).ravel()); o.data.update()
            o.matrix_world = Matrix.Identity(4)
            # keep the model's own textures but darken/matte them toward worn brown leather
            for sl in o.material_slots:
                m = sl.material
                if m and m.node_tree and m.node_tree.nodes.get("Principled BSDF"):
                    pp = m.node_tree.nodes["Principled BSDF"]
                    bc = pp.inputs['Base Color']
                    if bc.links:
                        src = bc.links[0].from_socket
                        mx = m.node_tree.nodes.new("ShaderNodeMix"); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'
                        mx.inputs['Factor'].default_value = 1.0; mx.inputs[7].default_value = (0.75, 0.55, 0.4, 1)
                        m.node_tree.links.new(src, mx.inputs[6]); m.node_tree.links.new(mx.outputs[2], bc)
                    if not pp.inputs['Roughness'].links:
                        pp.inputs['Roughness'].default_value = 0.6
                    pp.inputs['Coat Weight'].default_value = 0.0
            o.name = f"{self.name}_boot{'L' if sg > 0 else 'R'}"
            self.sea_boots.append(o); h.parts.append(o)
        bpy.data.objects.remove(pair)
        return True

    def _sea_boots(self):
        """1870s leather sea boots, modelled per posed foot (replaces the body-shaped boot shell):
        a lofted upper (rounded toe, instep, heel counter) sized to enclose the foot, a stitched sole that overhangs
        a few mm, a stacked leather heel, and a shaft that rises over the tucked-in trousers to below the knee."""
        h = self.h
        P = np.array([v.co[:] for v in h.body.data.vertices])
        self.boots.hide_render = True; self.boots.hide_viewport = True
        dg = bpy.context.evaluated_depsgraph_get()
        te = self.trousers.evaluated_get(dg); tm = te.to_mesh()
        T = np.array([te.matrix_world @ v.co for v in tm.vertices]); te.to_mesh_clear()
        upper_m = boot_leather(self.name + "_boot_leather")
        sole_m = boot_leather(self.name + "_boot_sole", color=(0.035, 0.024, 0.016), rough=0.8, creases=0.0)
        self.sea_boots = []
        for sg in (1, -1):
            side = self.used & (np.sign(self.rest_co[:, 0]) == sg)
            foot = P[side & (self.rest_co[:, 2] < self.marks["ankle"] + 0.03)]
            if len(foot) < 20:
                continue
            g = float(foot[:, 2].min())                                     # ground under this foot
            ank = np.array(h.bone_head(f"foot.{'L' if sg > 0 else 'R'}"))[:2]
            xy = foot[:, :2] - foot[:, :2].mean(0)
            w_, v_ = np.linalg.eigh(np.cov(xy.T)); fwd = v_[:, np.argmax(w_)]
            if ((foot[:, :2] - ank) @ fwd).mean() < 0:
                fwd = -fwd                                                  # toes point away from the ankle
            F3 = np.array([fwd[0], fwd[1], 0.0]); S3 = np.array([-fwd[1], fwd[0], 0.0])
            c0 = foot[:, :2].mean(0)
            loc = np.stack([(foot[:, :2] - c0) @ fwd, (foot[:, :2] - c0) @ S3[:2], foot[:, 2] - g], 1)
            u0, u1 = loc[:, 0].min() - 0.012, loc[:, 0].max() + 0.02            # heel back .. toe tip (room for the toe)
            ns = 22; nr = 28
            def env(u):
                m = np.abs(loc[:, 0] - u) < 0.02
                q = loc[m] if m.sum() > 3 else loc
                return (float(q[:, 1].min()) - 0.011, float(q[:, 1].max()) + 0.011, float(q[:, 2].max()) + 0.012)
            V = []; F = []
            rings = []
            for i in range(ns + 1):
                t = i / ns; u = u0 + (u1 - u0) * t
                ylo, yhi, top = env(min(max(u, u0 + 0.02), u1 - 0.03))
                # rounded toe and heel in plan; instep falls away to the toe cap
                taper = math.sin(math.pi * min(1.0, t / 0.12) / 2) ** 0.5 * math.sin(math.pi * min(1.0, (1 - t) / 0.2) / 2) ** 0.6
                toe = math.sqrt(max(0.0, 1 - max(0.0, (t - 0.72) / 0.28) ** 2))      # round toe in plan
                hee = math.sqrt(max(0.0, 1 - max(0.0, (0.1 - t) / 0.1) ** 2))         # round heel counter
                yc = (ylo + yhi) / 2; hw = max(0.008, (yhi - ylo) / 2 * (0.25 + 0.75 * min(toe, hee)))
                top = max(0.03, 0.03 + (top - 0.03) * (0.35 + 0.65 * toe)) if t > 0.6 else top
                ring = []
                for k in range(nr):
                    a = 2 * math.pi * k / nr
                    cy, sz = math.cos(a), math.sin(a)
                    zz = 0.012 + (top - 0.012) * (0.5 + 0.5 * sz) ** 1.0
                    yy = yc + hw * np.sign(cy) * abs(cy) ** 0.55 * (1 - 0.15 * max(0, sz))
                    if sz < 0:                                             # flat welt along the bottom
                        zz = 0.012 + 0.006 * (1 + sz)
                    ring.append(len(V)); V.append((u, yy, zz))
                rings.append(ring)
            for i in range(ns):
                for k in range(nr):
                    F.append([rings[i][k], rings[i][(k + 1) % nr], rings[i + 1][(k + 1) % nr], rings[i + 1][k]])
            F.append(rings[0][::-1]); F.append(rings[-1])
            # shaft: ellipses round the (tucked) trouser leg from the ankle to below the knee
            leg = side & (self.rest_co[:, 2] > self.marks["ankle"] - 0.01) & (self.rest_co[:, 2] < self.marks["ankle"] + 0.34)
            Lp = P[leg]
            tsel = (np.sign(T[:, 0] - P[self.used, 0].mean()) == sg) & (T[:, 2] < g + 0.42)
            Tp = T[tsel]
            shaft = []
            zs = np.linspace(g + 0.07, g + 0.36, 12)
            Vs = []; Fs = []
            for j, z in enumerate(zs):
                q = Lp[np.abs(Lp[:, 2] - z) < 0.025]
                if len(q) < 6:
                    q = Lp[np.argsort(np.abs(Lp[:, 2] - z))[:40]]
                c = q[:, :2].mean(0); d = q[:, :2] - c
                ra = float(np.abs(d @ fwd).max()) + 0.013; rb = float(np.abs(d @ S3[:2]).max()) + 0.013
                flare = 1.0 + 0.05 * max(0.0, (j - 9) / 2)
                ring = []
                for k in range(nr):
                    a = 2 * math.pi * k / nr
                    p = c + fwd * math.cos(a) * ra * flare + S3[:2] * math.sin(a) * rb * flare
                    ring.append(len(Vs)); Vs.append((p[0], p[1], z))
                shaft.append(ring)
            for j in range(len(zs) - 1):
                for k in range(nr):
                    Fs.append([shaft[j][k], shaft[j][(k + 1) % nr], shaft[j + 1][(k + 1) % nr], shaft[j + 1][k]])
            # to world: foot-local (u, v, z) -> c0 + u*fwd + v*side, ground g
            W = [(c0[0] + uu * fwd[0] + vv * S3[0], c0[1] + uu * fwd[1] + vv * S3[1], g + zz) for uu, vv, zz in V]
            nm = f"{self.name}_boot{'L' if sg > 0 else 'R'}"
            up = mesh_obj(nm + "_upper", W, F, upper_m)
            sb = up.modifiers.new("Sub", "SUBSURF"); sb.levels = 2; sb.render_levels = 2
            sh = mesh_obj(nm + "_shaft", Vs, Fs, upper_m)
            so = sh.modifiers.new("Thick", "SOLIDIFY"); so.thickness = 0.004; so.offset = 1
            sb = sh.modifiers.new("Sub", "SUBSURF"); sb.levels = 2; sb.render_levels = 2
            # sole (overhangs the welt by 4 mm) and a stacked heel
            outline = []
            for i in range(ns + 1):
                k0 = rings[i][0]; k1 = rings[i][nr // 2]
                outline.append((V[k0], V[k1]))
            SV = []; SF = []
            for i, (pa, pb) in enumerate(outline):
                for (uu, vv, _), z in ((pa, 0.0), (pa, 0.012), (pb, 0.012), (pb, 0.0)):
                    off = 0.004 if vv > (pa[1] + pb[1]) / 2 else -0.004
                    SV.append((c0[0] + uu * fwd[0] + (vv + off) * S3[0], c0[1] + uu * fwd[1] + (vv + off) * S3[1], g + z))
            for i in range(ns):
                q = 4 * i; r = 4 * (i + 1)
                SF += [[q, r, r + 1, q + 1], [q + 1, r + 1, r + 2, q + 2], [q + 2, r + 2, r + 3, q + 3], [q + 3, r + 3, r, q]]
            SF += [[0, 1, 2, 3][::-1], [4 * ns, 4 * ns + 1, 4 * ns + 2, 4 * ns + 3]]
            so_ = mesh_obj(nm + "_sole", SV, SF, sole_m)
            bv = so_.modifiers.new("Bevel", "BEVEL"); bv.width = 0.002; bv.segments = 2
            hl = ns // 4
            HV = []; HF = []
            for i in range(hl + 1):
                pa, pb = outline[i]
                for (uu, vv, _), z in ((pa, -0.022), (pa, 0.0), (pb, 0.0), (pb, -0.022)):
                    HV.append((c0[0] + uu * fwd[0] + vv * S3[0], c0[1] + uu * fwd[1] + vv * S3[1], g + z + 0.022))
            for i in range(hl):
                q = 4 * i; r = 4 * (i + 1)
                HF += [[q, r, r + 1, q + 1], [q + 1, r + 1, r + 2, q + 2], [q + 2, r + 2, r + 3, q + 3], [q + 3, r + 3, r, q]]
            HF += [[0, 1, 2, 3][::-1], [4 * hl, 4 * hl + 1, 4 * hl + 2, 4 * hl + 3]]
            hh = mesh_obj(nm + "_heel", HV, HF, sole_m)
            for o in (up, sh, so_, hh):
                self.sea_boots.append(o); h.parts.append(o)

    def _posed_surface(self):
        dg = bpy.context.evaluated_depsgraph_get()
        oe = self.h.body.evaluated_get(dg); me = oe.to_mesh()
        bvh = BVHTree.FromObject(self.h.body, dg)
        oe.to_mesh_clear()
        me0 = self.h.body.data
        P = np.array([v.co[:] for v in me0.vertices])           # baked base positions (world, identity transform)
        return P, bvh

    def _grow_all(self, density):
        co = self.rest_co; h = self.h
        wh = _w(h, HEAD); ears = _mask_at_uv(os.path.join(MASKS, "mpfb_ears.jpg"), self.uv)
        lips = _mask_at_uv(os.path.join(MASKS, "mpfb_lips.jpg"), self.uv)
        eyeL = np.array(h.joint("eye.L____head")); eyeR = np.array(h.joint("eye.R____head"))
        ec = (eyeL + eyeR) / 2
        mouth = co[self.used & (lips > 0.5)].mean(0)
        rel = co - ec
        x, y, z = rel[:, 0], rel[:, 1], rel[:, 2]
        head = self.used & (wh > 0.55) & (ears < 0.2)
        # hairline: high on the forehead, low at the nape; sideburns down in front of the ears
        line = np.interp(y, [-0.06, -0.03, 0.0, 0.05, 0.12], [0.088, 0.078, 0.05, -0.05, -0.085])
        scalp = head & (z > line)
        sideburn = head & (np.abs(x) > 0.055) & (y > -0.045) & (y < 0.0) & (z > -0.04) & (z <= line + 0.01)
        mz = np.array(mouth)[2] - ec[2]
        beard = head & (y < 0.03) & (z < -0.035) & (lips < 0.1) & ~((np.abs(x) < 0.03) & (y < -0.06) & (z > mz - 0.012) & (z < mz + 0.008))
        beard &= ~((z > -0.06) & (np.abs(x) < 0.045) & (y < -0.07) & (z > mz + 0.012))      # keep the nose bare
        beard &= ((z < mz + 0.02) | (np.abs(x) > 0.035))                                      # cheeks only below the cheekbones
        beard &= ~((z > mz - 0.004) & (z < mz + 0.009) & (np.abs(x) < 0.026))                 # mouth slit
        tache = head & (lips < 0.1) & (y < -0.06) & (z > mz + 0.004) & (z < mz + 0.026) & (np.abs(x) < 0.04)
        neck = self.used & (wh > 0.3) & (z < -0.11) & (z > -0.16) & (y < 0.0)
        brow = head & (z > 0.014) & (z < 0.03 - 0.12 * np.abs(np.abs(x) - 0.03)) & (y < -0.012) & (self.rest_n[:, 1] < -0.45) & (np.abs(x) > 0.011) & (np.abs(x) < 0.054)
        P, bvh = self._posed_surface()
        R = self.head_R
        brown = hair_material(self.name + "_hair", 0.82, 0.38)
        self.hair_objs = []
        self.hair_objs.append(self._strands("hair", scalp, P, bvh, int(70000 * density), (0.014, 0.028), 0.001,
                                            comb=lambda p: R @ Vector((0, 0.8, -0.45)), lift=0.0022, mat=brown, curl=0.22, clump=0.35))
        beard_m = hair_material(self.name + "_beard", 0.8, 0.45, rough=0.38)
        self.hair_objs.append(self._strands("beard", beard | neck, P, bvh, int(46000 * density), (0.014, 0.03), 0.0009,
                                            comb=lambda p: R @ Vector((0, -0.25, -1)), lift=0.003, mat=beard_m, curl=0.35, clump=0.55, segs=9))
        self.hair_objs.append(self._strands("moustache", tache, P, bvh, int(5000 * density), (0.012, 0.02), 0.0008,
                                            comb=lambda p: R @ Vector((math.copysign(0.7, p.x - self._mid_x), -0.2, -1)),
                                            lift=0.002, mat=beard_m, curl=0.2))
        self.hair_objs.append(self._strands("brows", brow, P, bvh, int(1500 * density), (0.007, 0.012), 0.0007,
                                            comb=lambda p: R @ Vector((math.copysign(1.0, p.x - self._mid_x), 0, 0.25)),
                                            lift=0.0008, mat=beard_m, curl=0.08))

    def _strands(self, label, vmask, P, bvh, count, length, radius, comb, lift, mat, curl=0.2, segs=7, seed=1, clump=0.0):
        rng = np.random.default_rng(seed + len(label))
        self._mid_x = float(P[self.used, 0].mean())
        fs = [f for f in self.faces if vmask[list(f)].sum() >= 3]
        if not fs or count <= 0:
            return None
        tris = []
        for f in fs:
            f = list(dict.fromkeys(f))
            for k in range(1, len(f) - 1):
                tris.append((f[0], f[k], f[k + 1]))
        tris = np.array(tris)
        A = P[tris[:, 0]]; B = P[tris[:, 1]]; C = P[tris[:, 2]]
        area = np.linalg.norm(np.cross(B - A, C - A), axis=1) / 2
        pick = rng.choice(len(tris), count, p=area / area.sum())
        r1 = np.sqrt(rng.random(count)); r2 = rng.random(count)
        roots = A[pick] * (1 - r1)[:, None] + B[pick] * (r1 * (1 - r2))[:, None] + C[pick] * (r1 * r2)[:, None]
        lens = rng.uniform(length[0], length[1], count)
        pts = np.zeros((count, segs, 3), np.float32); ok = np.zeros(count, bool)
        for i in range(count):
            p = Vector(roots[i]); loc, n, _, _ = bvh.find_nearest(p)
            if loc is None or (loc - p).length > 0.01:
                continue
            ok[i] = True
            n = n.normalized(); p = loc - n * 0.0006
            cd = comb(p).normalized()
            jit = Vector(rng.normal(0, 1, 3)) * curl
            step = lens[i] / (segs - 1)
            dirv = (n * 0.9 + cd * 0.6 + jit * 0.3).normalized()
            pts[i, 0] = p
            for k in range(1, segs):
                t = k / (segs - 1)
                target = (cd + jit * 0.5 * math.sin(3.0 * t + i)).normalized()
                dirv = (dirv * (1 - 0.45) + target * 0.45).normalized()
                q = p + dirv * step
                loc, nn, _, dist = bvh.find_nearest(q)
                if loc is not None:
                    want = lift * min(1.0, t * 1.6) + 0.0008
                    side = (q - loc).dot(nn)
                    if side < want:
                        q = loc + nn.normalized() * want
                        dirv = (q - p).normalized()
                pts[i, k] = q; p = q
        span = np.linalg.norm(pts[:, -1] - pts[:, 0], axis=1)
        ok &= span < lens * 1.2
        pts = pts[ok]; count = int(ok.sum())
        if clump and count > 50:
            # groomed look: strands gather toward the tips of nearby guide strands
            from mathutils.kdtree import KDTree
            ng = max(20, count // 60); gi = rng.choice(count, ng, replace=False)
            kd = KDTree(ng)
            for j, g in enumerate(gi):
                kd.insert(Vector(pts[g, 0]), j)
            kd.balance()
            t = np.linspace(0, 1, segs)[None, :, None] ** 1.4
            G = np.array([gi[kd.find(Vector(pts[i, 0]))[1]] for i in range(count)])
            tgt = pts[G] - pts[G][:, :1] + pts[:, :1]
            pts = pts + (tgt - pts) * clump * t
        cv = bpy.data.hair_curves.new(f"{self.name}_{label}")
        cv.add_curves([segs] * count)
        cv.position_data.foreach_set("vector", pts.reshape(-1))
        rad = np.tile(np.linspace(radius * 1.0, radius * 0.35, segs, dtype=np.float32), count) * 0.05
        try:
            cv.attributes["radius"].data.foreach_set("value", rad)
        except Exception:
            a = cv.attributes.new("radius", 'FLOAT', 'POINT'); a.data.foreach_set("value", rad)
        o = bpy.data.objects.new(cv.name, cv); bpy.context.collection.objects.link(o)
        cv.materials.append(mat)
        return o

    @property
    def objects(self):
        return [p for p in self.h.parts] + self.button_objs + [o for o in getattr(self, "hair_objs", []) if o]
