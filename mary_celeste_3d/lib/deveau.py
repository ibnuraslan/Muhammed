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
    nails.inputs[7].default_value = (0.62, 0.48, 0.42, 1); L.new(mask("mpfb_fingernails.jpg"), nails.inputs['Factor'])
    L.new(lips.outputs[2], nails.inputs[6])
    L.new(nails.outputs[2], p.inputs['Base Color'])
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
        trous = u & (z < hip_z + 0.11) & (z > ankle_z + 0.05) & (wfoot < 0.2) & (whand < 0.05)
        self.trousers, _ = self._shell("trousers", trous, 0.012, wool_material("trousers", (0.022, 0.02, 0.019), weave=500, wet=self.wet, sheen=0.25),
                                       solid=0.002, displace=0.004, drape=14,
                                       flare=lambda b: np.clip((knee_z + 0.1 - b[:, 2]) / 0.4, 0, 1) * 0.02)
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
        self._sea_boots()
        if hair:
            self._grow_all(density)
        h.arm.hide_render = True; h.arm.hide_viewport = True
        if place is not None:
            for o in self.objects:
                if o.parent is None:
                    o.matrix_world = place @ o.matrix_world
            bpy.context.view_layer.update()

    def _sea_boots(self):
        """Replace the foot-shaped boot shell with leather sea boots: the convex hull of each posed foot and shin
        (no toes, flat sole), pushed out a little and smoothed."""
        h = self.h
        P = np.array([v.co[:] for v in h.body.data.vertices])
        mat = self.boots.data.materials[0]
        self.boots.hide_render = True; self.boots.hide_viewport = True
        self.sea_boots = []
        for sg in (1, -1):
            sel = self.used & self.boot_mask & (np.sign(self.rest_co[:, 0]) == sg)
            pts = P[sel]
            if len(pts) < 8:
                continue
            bm = bmesh.new()
            for p in pts:
                bm.verts.new(p)
            r = bmesh.ops.convex_hull(bm, input=bm.verts)
            for v in [g for g in r.get("geom_interior", []) if isinstance(g, bmesh.types.BMVert)]:
                bm.verts.remove(v)
            bmesh.ops.dissolve_degenerate(bm, dist=1e-4, edges=bm.edges)
            bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
            me = bpy.data.meshes.new(f"{self.name}_seaboot"); bm.to_mesh(me); bm.free()
            o = bpy.data.objects.new(me.name, me); bpy.context.collection.objects.link(o)
            o.data.materials.append(mat)
            rm = o.modifiers.new("Remesh", "REMESH"); rm.mode = 'VOXEL'; rm.voxel_size = 0.006; rm.use_smooth_shade = True
            sm = o.modifiers.new("Smooth", "LAPLACIANSMOOTH"); sm.lambda_factor = 2.0; sm.iterations = 12; sm.use_volume_preserve = True
            d = o.modifiers.new("Out", "DISPLACE"); d.strength = 0.012; d.mid_level = 0.0
            sb = o.modifiers.new("Sub", "SUBSURF"); sb.levels = 1; sb.render_levels = 1
            # keep the sole on the ground
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
        line = np.interp(y, [-0.12, -0.06, 0.0, 0.05, 0.12], [0.06, 0.055, 0.02, -0.05, -0.085])
        scalp = head & (z > line)
        sideburn = head & (np.abs(x) > 0.055) & (y > -0.045) & (y < 0.0) & (z > -0.04) & (z <= line + 0.01)
        mz = np.array(mouth)[2] - ec[2]
        beard = head & (y < 0.03) & (z < -0.035) & (lips < 0.1) & ~((np.abs(x) < 0.03) & (y < -0.06) & (z > mz - 0.012) & (z < mz + 0.008))
        beard &= ~((z > -0.06) & (np.abs(x) < 0.045) & (y < -0.07) & (z > mz + 0.012))      # keep the nose bare
        beard &= ((z < mz + 0.02) | (np.abs(x) > 0.035))                                      # cheeks only below the cheekbones
        beard &= ~((z > mz - 0.004) & (z < mz + 0.009) & (np.abs(x) < 0.026))                 # mouth slit
        tache = head & (lips < 0.1) & (y < -0.06) & (z > mz + 0.004) & (z < mz + 0.026) & (np.abs(x) < 0.04)
        neck = self.used & (wh > 0.3) & (z < -0.11) & (z > -0.16) & (y < 0.0)
        brow = head & (z > 0.012) & (z < 0.03) & (y < -0.055) & (np.abs(x) > 0.012) & (np.abs(x) < 0.058)
        P, bvh = self._posed_surface()
        R = self.head_R
        brown = hair_material(self.name + "_hair", 0.82, 0.38)
        self.hair_objs = []
        self.hair_objs.append(self._strands("hair", scalp, P, bvh, int(70000 * density), (0.014, 0.028), 0.001,
                                            comb=lambda p: R @ Vector((0, 0.8, -0.45)), lift=0.0022, mat=brown, curl=0.22))
        self.hair_objs.append(self._strands("sideburns", sideburn, P, bvh, int(3000 * density), (0.012, 0.02), 0.0009,
                                            comb=lambda p: R @ Vector((0, 0.1, -1)), lift=0.002, mat=brown, curl=0.3))
        beard_m = hair_material(self.name + "_beard", 0.8, 0.45, rough=0.38)
        self.hair_objs.append(self._strands("beard", beard | neck, P, bvh, int(46000 * density), (0.014, 0.03), 0.0009,
                                            comb=lambda p: R @ Vector((0, -0.25, -1)), lift=0.003, mat=beard_m, curl=0.45))
        self.hair_objs.append(self._strands("moustache", tache, P, bvh, int(5000 * density), (0.012, 0.02), 0.0008,
                                            comb=lambda p: R @ Vector((math.copysign(0.7, p.x - self._mid_x), -0.2, -1)),
                                            lift=0.002, mat=beard_m, curl=0.2))
        self.hair_objs.append(self._strands("brows", brow, P, bvh, int(2600 * density), (0.006, 0.011), 0.0006,
                                            comb=lambda p: R @ Vector((math.copysign(1.0, p.x - self._mid_x), 0, 0.35)),
                                            lift=0.0012, mat=beard_m, curl=0.1))

    def _strands(self, label, vmask, P, bvh, count, length, radius, comb, lift, mat, curl=0.2, segs=7, seed=1):
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
