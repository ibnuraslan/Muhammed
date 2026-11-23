"""v014b: real cloth garments (director: scrubs were body-shaped; the defendant's jacket read as stump shoulders).
blender -b b_looks.blend --python 25_v014b_garments.py -- <out.blend>        (after 21, before 22)

Each garment is its own loose cloth mesh, built in the rest pose around the skeleton, NOT a copy of the body:
- top: a straight boxy tube from the hip to the shoulders (its width set by the widest part of the chest,
  so it hangs straight with no waist, bust or belly read), a V-neck, and sleeve tubes round the upper arms
  (short for scrubs, long for a shirt)
- trousers: a waist band, a seat tube and two straight leg tubes to the ankle
- weights: copied from the nearest body vertices (rest pose), driven by the same armature; folds = displacement,
  then solidify + subdivision.
Scrubs for Surgeon1 (OR), Surgeon2, Nurse, Anaesth. In the hearing, the defendant (Surgeon1) wears a pale shirt with a
dark tie and dark trousers instead of the suit jacket."""
import sys, os, math
import bpy, bmesh
from mathutils import Vector, Matrix
from mathutils.kdtree import KDTree
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import v12lib as VL
OUT = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene; OB = bpy.data.objects; V = lambda *a: Vector(a)

def fabric(name, rgb, print_dots=False, rough=0.88):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; N, L = nt.nodes, nt.links
    b = N["Principled BSDF"]; b.inputs["Roughness"].default_value = rough; b.inputs["Sheen Weight"].default_value = 0.4
    tc = N.new("ShaderNodeTexCoord")
    wv = N.new("ShaderNodeTexWave"); wv.inputs["Scale"].default_value = 260; L.new(tc.outputs["Object"], wv.inputs["Vector"])
    nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 9; L.new(tc.outputs["Object"], nz.inputs["Vector"])
    bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.12
    L.new(wv.outputs["Fac"], bp.inputs["Height"]); L.new(bp.outputs["Normal"], b.inputs["Normal"])
    mr = N.new("ShaderNodeMapRange"); L.new(nz.outputs["Fac"], mr.inputs[0]); mr.inputs[3].default_value = 0.85; mr.inputs[4].default_value = 1.08
    cc = N.new("ShaderNodeCombineColor"); [L.new(mr.outputs[0], cc.inputs[i]) for i in range(3)]
    mx = N.new("ShaderNodeMix"); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs[0].default_value = 1
    mx.inputs[6].default_value = rgb + (1,); L.new(cc.outputs[0], mx.inputs[7]); col = mx.outputs[2]
    if print_dots:
        vo = N.new("ShaderNodeTexVoronoi"); vo.inputs["Scale"].default_value = 150; L.new(tc.outputs["Object"], vo.inputs["Vector"])
        lt = N.new("ShaderNodeMath"); lt.operation = 'LESS_THAN'; lt.inputs[1].default_value = 0.15; L.new(vo.outputs["Distance"], lt.inputs[0])
        m2 = N.new("ShaderNodeMix"); m2.data_type = 'RGBA'; L.new(lt.outputs[0], m2.inputs[0]); L.new(col, m2.inputs[6])
        m2.inputs[7].default_value = tuple(min(1, c * 0.5 + 0.45) for c in rgb) + (1,); col = m2.outputs[2]
    L.new(col, b.inputs["Base Color"])
    return m

def rest_body(rig, body):
    """rest-pose evaluated body coords (shape keys applied), aligned to body.data.vertices, + bone-name groups"""
    pp = rig.data.pose_position; rig.data.pose_position = 'REST'
    saved = {m.name: m.show_viewport for m in body.modifiers}
    for m in body.modifiers:
        if m.type != 'ARMATURE': m.show_viewport = False
    hv = body.hide_viewport; body.hide_viewport = False
    bpy.context.view_layer.update(); dg = bpy.context.evaluated_depsgraph_get()
    ev = body.evaluated_get(dg); me = ev.to_mesh()
    co = [body.matrix_world @ v.co for v in me.vertices]; ev.to_mesh_clear()
    for m in body.modifiers: m.show_viewport = saved[m.name]
    body.hide_viewport = hv; rig.data.pose_position = pp; bpy.context.view_layer.update()
    return co

def section(co, groups, z, prefixes, cy, xlim=9.0):
    """half-width (x) and front/back depth at height z (95th percentile; arms excluded by xlim)"""
    pts = [p for p, g in zip(co, groups) if g and g.startswith(prefixes) and abs(p.z - z) < 0.02 and abs(p.x) < xlim]
    if len(pts) < 8: return None
    q = lambda vals: sorted(vals)[int(len(vals) * 0.95) - 1]
    return q([abs(p.x) for p in pts]), q([cy - p.y for p in pts]), q([p.y - cy for p in pts])

def build(rig_name, kind, mat, src_vis, sleeve="short", ease=0.03, name=None):
    r = OB[rig_name]; body = OB[rig_name + ".body"]; BN = r.data.bones; BONES = set(BN.keys())
    co = rest_body(r, body)
    idx = {g.index: g.name for g in body.vertex_groups}
    dom = []; bgi = body.vertex_groups.get("body")
    for v in body.data.vertices:
        if bgi is not None and not any(g.group == bgi.index and g.weight > 0.5 for g in v.groups): dom.append(None); continue
        best = (0, None)
        for g in v.groups:
            n = idx.get(g.group)
            if n in BONES and g.weight > best[0]: best = (g.weight, n)
        dom.append(best[1])
    H = lambda n: BN[n].head_local.copy(); T = lambda n: BN[n].tail_local.copy()
    sp = {n: H(n) for n in ("spine05", "spine04", "spine03", "spine02", "spine01", "neck01")}
    def cy_at(z):
        zs = sorted((p.z, p.y) for p in sp.values())
        if z <= zs[0][0]: return zs[0][1]
        for (z0, y0), (z1, y1) in zip(zs, zs[1:]):
            if z0 <= z <= z1: return y0 + (y1 - y0) * (z - z0) / max(z1 - z0, 1e-6)
        return zs[-1][1]
    bm = bmesh.new(); NA = 40
    TORSO = ("spine", "pelvis", "breast", "pectoral", "clavicle", "shoulder", "root", "upperleg01")
    def ring_faces(rows, closed=True):
        for a, b in zip(rows, rows[1:]):
            n = len(a)
            for i in range(n if closed else n - 1):
                bm.faces.new((a[i], a[(i + 1) % n], b[(i + 1) % n], b[i]))
    if kind == "Top":
        hip = (H("upperleg01.L").z + H("upperleg01.R").z) / 2
        zarm = (H("upperarm01.L").z + H("upperarm01.R").z) / 2 - 0.07      # armpit
        neck = H("neck01"); zt = neck.z - 0.005
        z0 = hip - 0.07
        xl = abs(H("upperarm01.L").x) - 0.025
        secs = [section(co, dom, z0 + (zarm - z0) * k / 12, ("spine", "pelvis", "breast", "pectoral", "root"), cy_at(z0 + (zarm - z0) * k / 12)) for k in range(1, 12)]
        secs = [s for s in secs if s]
        A = max(s[0] for s in secs) + 0.018; Fd = max(s[1] for s in secs) + ease; Bd = max(s[2] for s in secs) + ease * 0.7
        rows = []; NZ = 20
        for k in range(NZ + 1):
            z = z0 + (zt - z0) * k / NZ; c = cy_at(z); row = []
            Ar, Fr, Br = A, Fd, Bd
            if z > zarm:                                                   # above the armpit: follow the shoulders/upper chest
                sz = section(co, dom, z, ("spine", "clavicle", "breast", "pectoral", "neck"), c, xl - 0.01)
                if sz:
                    u_ = min(1.0, (z - zarm) / 0.05)
                    Ar = A + (sz[0] + 0.012 - A) * u_; Br = Bd + (sz[2] + 0.012 - Bd) * u_
                    Fr = max(sz[1] + 0.012, Fd * (1 - min(1.0, (z - zarm) / 0.09)))   # front stays flat over the chest
            for i in range(NA):
                th = 2 * math.pi * i / NA; sx, cyv = math.sin(th), -math.cos(th)
                d = Fr if cyv < 0 else Br
                row.append(bm.verts.new((Ar * sx, c + d * cyv, z)))
            rows.append(row)
        ring_faces(rows)
        inV = lambda c_: c_.y < cy_at(c_.z) - 0.02 and c_.z > neck.z - (0.12 - 1.4 * abs(c_.x))
        cut = [f for f in bm.faces if sum(1 for v in f.verts if inV(v.co)) >= 2]
        bmesh.ops.delete(bm, geom=cut, context='FACES')
        bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
        for it in range(40):                                            # smooth the V-neck edge
            newp = {}
            for v in [v for v in bm.verts if v.is_boundary and v.co.z > zarm]:
                nb = [e.other_vert(v) for e in v.link_edges if e.is_boundary]
                if len(nb) == 2: newp[v] = v.co * 0.4 + (nb[0].co + nb[1].co) * 0.3
            for v, p_ in newp.items(): v.co = p_
    else:   # trousers
        waist = (sp["spine04"].z + sp["spine05"].z) / 2 + 0.01
        hipz = (H("upperleg01.L").z + H("upperleg01.R").z) / 2; crotch = hipz - 0.09
        LEG = ("upperleg", "lowerleg")
        sec = [section(co, dom, z, ("spine", "pelvis", "root", "upperleg"), cy_at(z), 0.25) for z in (waist, (waist + hipz) / 2, hipz)]
        sec = [s for s in sec if s]
        A = max(s[0] for s in sec) + ease * 0.6; Fd = max(s[1] for s in sec) + ease * 0.6; Bd = max(s[2] for s in sec) + ease * 0.6
        rows = []
        for k in range(6):
            z = waist + (crotch - waist) * k / 5; c = cy_at(z); row = []
            for i in range(NA):
                th = 2 * math.pi * i / NA; sx, cyv = math.sin(th), -math.cos(th)
                row.append(bm.verts.new((A * sx, c + (Fd if cyv < 0 else Bd) * cyv, z)))
            rows.append(row)
        ring_faces(rows)
        for s in "LR":
            a0 = H("upperleg01." + s); a0.z = crotch + 0.06; a1 = H("foot." + s) + V(0, 0, 0.02)
            ax = (a1 - a0).normalized(); L_ = (a1 - a0).length
            b1 = ax.cross(V(0, 1, 0)).normalized(); b2 = ax.cross(b1)
            leg = [p for p, g in zip(co, dom) if g and g.startswith(LEG) and g.endswith(s)]
            ds0 = [((p - a0) - ax * (p - a0).dot(ax)).length for p in leg if abs((p - a0).dot(ax)) < 0.04]
            ds0 = sorted(ds0); r0 = min((ds0[int(len(ds0) * 0.9) - 1] if len(ds0) > 4 else 0.08) + ease * 0.5, 0.10)
            lrows = []
            for k in range(10):
                t = k / 9; c = a0 + ax * (L_ * t); rr = r0 * (1 - 0.28 * t)            # straight, slightly tapered
                lrows.append([bm.verts.new(c + (b1 * math.cos(2 * math.pi * i / 24) + b2 * math.sin(2 * math.pi * i / 24)) * rr) for i in range(24)])
            ring_faces(lrows)
    me = bpy.data.meshes.new(name or (rig_name + ".Cloth" + kind)); bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = True
    ob = OB.new(name or (rig_name + ".Cloth" + kind), me); bpy.data.collections["Collection"].objects.link(ob)
    ob.parent = r; ob.matrix_world = Matrix.Identity(4)
    me.materials.append(mat)
    # weights: average of the 6 nearest rest-pose body vertices (only real bones)
    bg = body.vertex_groups.get("body")
    real = [i for i, v in enumerate(body.data.vertices) if bg is None or any(g.group == bg.index and g.weight > 0.5 for g in v.groups)]
    kd = KDTree(len(real))
    for i in real: kd.insert(co[i], i)
    kd.balance()                                     # real skin only (no hidden MPFB helper geometry)
    vg = {}
    for v in me.vertices:
        acc = {}
        nn = kd.find_n(v.co, 6); tot = 0.0
        for p, i, d in nn:
            w0 = 1.0 / max(d, 0.005); tot += w0
            for g in body.data.vertices[i].groups:
                n = idx.get(g.group)
                if n in BONES and g.weight > 0.01: acc[n] = acc.get(n, 0) + g.weight * w0
        for n, w in acc.items():
            if n not in vg: vg[n] = ob.vertex_groups.new(name=n)
            vg[n].add([v.index], w / tot, 'REPLACE')
    tx = bpy.data.textures.get("ClothFolds") or bpy.data.textures.new("ClothFolds", 'CLOUDS'); tx.noise_scale = 0.06
    d = ob.modifiers.new("Folds", 'DISPLACE'); d.texture = tx; d.strength = 0.012; d.texture_coords = 'LOCAL'
    am = ob.modifiers.new("Armature", 'ARMATURE'); am.object = r
    so = ob.modifiers.new("Cloth", 'SOLIDIFY'); so.thickness = 0.003; so.offset = -1.0
    sd = ob.modifiers.new("Subdivision", 'SUBSURF'); sd.levels = 1; sd.render_levels = 2
    VL.clear_keys(ob, ("hide_render",))
    fc = [f for f in VL.fcurves(src_vis) if f.data_path == "hide_render"]
    if fc and len(fc[0].keyframe_points):
        for kp in fc[0].keyframe_points: ob.hide_render = bool(kp.co.y); ob.keyframe_insert("hide_render", frame=int(kp.co.x))
        VL.constant(ob, ("hide_render",))
    else: ob.hide_render = src_vis.hide_render
    print("CLOTH", ob.name, len(me.vertices))
    return ob


def yoke(rig_name, mat, src_vis, sleeve="short", off=0.012, name=None, torso=False):
    r = OB[rig_name]; body = OB[rig_name + ".body"]; BN = r.data.bones; BONES = set(BN.keys())
    co = rest_body(r, body)
    ob = body.copy(); ob.data = body.data.copy(); ob.name = name or (rig_name + ".Yoke"); bpy.data.collections["Collection"].objects.link(ob)
    for m in list(ob.modifiers): ob.modifiers.remove(m)
    if ob.animation_data: ob.animation_data_clear()
    if ob.data.shape_keys:
        for o in bpy.context.selected_objects: o.select_set(False)
        bpy.context.view_layer.objects.active = ob; ob.select_set(True); bpy.ops.object.shape_key_remove(all=True, apply_mix=True)
    idx = {g.index: g.name for g in ob.vertex_groups}; bodyg = ob.vertex_groups.get("body")
    zsplit = (BN["upperarm01.L"].head_local.z + BN["upperarm01.R"].head_local.z) / 2 - 0.075
    neck = BN["neck01"].head_local
    keep = set()
    for v in ob.data.vertices:
        if bodyg is not None and not any(g.group == bodyg.index and g.weight > 0.5 for g in v.groups): continue
        best = (0, None)
        for g in v.groups:
            n = idx.get(g.group)
            if n in BONES and g.weight > best[0]: best = (g.weight, n)
        d = best[1]; c = co[v.index]
        if d is None: continue
        if d.startswith(("upperarm", "lowerarm")) if sleeve == "long" else d.startswith("upperarm"):
            if sleeve == "short" and d.startswith("upperarm02"):
                s_ = d[-1]; a, b = BN["upperarm02." + s_].head_local, BN["upperarm02." + s_].tail_local
                if (c - a).dot(b - a) / (b - a).length_squared > 0.45: continue
            if sleeve == "long" and d.startswith("lowerarm02"):
                s_ = d[-1]; a, b = BN["lowerarm02." + s_].head_local, BN["lowerarm02." + s_].tail_local
                if (c - a).dot(b - a) / (b - a).length_squared > 0.8: continue
            keep.add(v.index); continue
        if torso and d.startswith(("spine", "pelvis", "breast", "pectoral", "root", "clavicle", "shoulder", "neck01")):
            hipz = (BN["upperleg01.L"].head_local.z + BN["upperleg01.R"].head_local.z) / 2
            if c.z < hipz - 0.06 or d.startswith("neck01") or c.z > neck.z + 0.005: continue
            if c.y < neck.y - 0.02 and c.z > neck.z - (0.07 - 1.3 * abs(c.x)): continue        # open collar
            keep.add(v.index); continue
        if sleeve == "short" and d.startswith(("shoulder", "clavicle")) and abs(c.x) > abs(BN["upperarm01.L"].head_local.x) - 0.03:
            keep.add(v.index)                                                     # shoulder cap joins sleeve to body
    for v in ob.data.vertices: v.co = co[v.index]
    bm = bmesh.new(); bm.from_mesh(ob.data); bm.verts.ensure_lookup_table()
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.index not in keep], context='VERTS')
    for it in range(10):
        newp = {}
        for v in [v for v in bm.verts if v.is_boundary]:
            nb = [e.other_vert(v) for e in v.link_edges if e.is_boundary]
            if len(nb) == 2: newp[v] = v.co * 0.4 + (nb[0].co + nb[1].co) * 0.3
        for v, p_ in newp.items(): v.co = p_
    bm.normal_update()
    for v in bm.verts: v.co = v.co + v.normal * off
    bm.to_mesh(ob.data); bm.free()
    ob.data.materials.clear(); ob.data.materials.append(mat)
    for p in ob.data.polygons: p.material_index = 0; p.use_smooth = True
    ob.parent = r; ob.matrix_world = Matrix.Identity(4)
    tx = bpy.data.textures.get("ClothFolds") or bpy.data.textures.new("ClothFolds", 'CLOUDS')
    dd = ob.modifiers.new("Folds", 'DISPLACE'); dd.texture = tx; dd.strength = 0.006; dd.texture_coords = 'LOCAL'
    am = ob.modifiers.new("Armature", 'ARMATURE'); am.object = r
    so = ob.modifiers.new("Cloth", 'SOLIDIFY'); so.thickness = 0.003; so.offset = 1.0
    sd = ob.modifiers.new("Subdivision", 'SUBSURF'); sd.levels = 0; sd.render_levels = 1
    VL.clear_keys(ob, ("hide_render",))
    fc = [f for f in VL.fcurves(src_vis) if f.data_path == "hide_render"]
    if fc and len(fc[0].keyframe_points):
        for kp in fc[0].keyframe_points: ob.hide_render = bool(kp.co.y); ob.keyframe_insert("hide_render", frame=int(kp.co.x))
        VL.constant(ob, ("hide_render",))
    else: ob.hide_render = src_vis.hide_render
    print("YOKE", ob.name, len(ob.data.vertices))
    return ob

def hide_under(rig_name, vis_src, sleeve="short", tag="UnderCloth"):
    """mask the body skin covered by the garments (torso, upper arms to the sleeve hem, legs to the ankle), only while worn"""
    r = OB[rig_name]; body = OB[rig_name + ".body"]; BN = r.data.bones; BONES = set(BN.keys())
    idx = {g.index: g.name for g in body.vertex_groups}
    co = rest_body(r, body); neck = BN["neck01"].head_local; ank = min(BN["foot.L"].head_local.z, BN["foot.R"].head_local.z)
    sel = []
    for v in body.data.vertices:
        best = (0, None)
        for g in v.groups:
            n = idx.get(g.group)
            if n in BONES and g.weight > best[0]: best = (g.weight, n)
        d = best[1]; c = co[v.index]
        if d is None: continue
        if d.startswith(("spine", "pelvis", "breast", "pectoral", "root", "upperleg", "lowerleg")):
            if c.z > neck.z - 0.02: continue
            if c.y < neck.y + 0.01 and c.z > neck.z - (0.16 - 1.2 * abs(c.x)): continue           # V-neck skin stays (no hole edge)
            if c.z < ank + 0.07: continue
            sel.append(v.index)
        elif d.startswith("upperarm") and sleeve == "short":
            s_ = d[-1]; a, b = BN["upperarm01." + s_].head_local, BN["upperarm02." + s_].tail_local
            if (c - a).dot(b - a) / (b - a).length_squared < 0.22: sel.append(v.index)
        elif d.startswith(("upperarm", "lowerarm")) and sleeve == "long":
            s_ = d[-1]; a, b = BN["upperarm01." + s_].head_local, BN["wrist." + s_].head_local
            if (c - a).dot(b - a) / (b - a).length_squared < 0.9: sel.append(v.index)
    g = body.vertex_groups.get(tag) or body.vertex_groups.new(name=tag); g.add(sel, 1.0, 'REPLACE')
    m = body.modifiers.get(tag) or body.modifiers.new(tag, 'MASK'); m.vertex_group = tag; m.invert_vertex_group = True
    VL.clear_keys(body, ('modifiers["%s"]' % tag,))
    fc = [f for f in VL.fcurves(vis_src) if f.data_path == "hide_render"]
    if fc and len(fc[0].keyframe_points):
        for kp in fc[0].keyframe_points:
            m.show_render = not bool(kp.co.y); body.keyframe_insert('modifiers["%s"].show_render' % tag, frame=int(kp.co.x))
        VL.constant(body)
    else: m.show_render = not vis_src.hide_render
    print("UNDER", rig_name, tag, len(sel))

SCRUB = {"Surgeon1": ((0.10, 0.42, 0.40), "male_casualsuit01"), "Surgeon2": ((0.10, 0.20, 0.52), "female_casualsuit01"),
         "Nurse": ((0.12, 0.30, 0.50), "male_casualsuit01"), "Anaesth": ((0.18, 0.38, 0.20), "male_casualsuit01")}
for nm, (rgb, suit) in SCRUB.items():
    src = OB[nm + "." + suit]
    # visibility source = the v013 scrub pieces (they carry the shot visibility); then hide them for good
    vis_src = OB.get(nm + ".ScrubTop") or src
    mt = fabric(nm + "ClothTop", rgb, print_dots=(nm == "Surgeon2"))
    build(nm, "Top", mt, vis_src, "short", 0.032); yoke(nm, mt, vis_src, "short", 0.012)
    hide_under(nm, vis_src, "short")
    build(nm, "Trousers", fabric(nm + "ClothTrousers", tuple(c * 0.75 for c in rgb)), vis_src, "short", 0.03)
    for o in (OB.get(nm + ".ScrubTop"), OB.get(nm + ".ScrubTrousers")):
        if o: VL.key_hide(o, [])
# defendant: shirt + tie + trousers (no jacket)
suit = OB["Surgeon1.male_elegantsuit01"]
msh = fabric("DefShirt", (0.72, 0.76, 0.82), rough=0.7)
shirt = yoke("Surgeon1", msh, suit, "long", 0.010, name="Surgeon1.Shirt", torso=True)   # fitted dress shirt
hide_under("Surgeon1", suit, "long", tag="UnderShirt")
trs = build("Surgeon1", "Trousers", fabric("DefTrousers", (0.10, 0.10, 0.13)), suit, "long", 0.025, name="Surgeon1.Slacks")
r = OB["Surgeon1"]; BN = r.data.bones
n0 = BN["neck01"].head_local
bm = bmesh.new()
pts = [(0, -0.002, 0.0, 0.012), (0, -0.004, -0.06, 0.03), (0, -0.006, -0.30, 0.042), (0, -0.004, -0.36, 0.0)]
rows = []
for x, y, z, w in pts:
    rows.append([bm.verts.new((n0.x + x + w * u, n0.y - 0.075 + y, n0.z - 0.03 + z)) for u in (-1, 1)])
for a, b in zip(rows, rows[1:]): bm.faces.new((a[0], a[1], b[1], b[0]))
tm = bpy.data.meshes.new("Tie"); bm.to_mesh(tm); bm.free()
tie = OB.new("Surgeon1.Tie", tm); bpy.data.collections["Collection"].objects.link(tie)
tie.parent = r; tie.matrix_world = Matrix.Identity(4)
tmat = bpy.data.materials.new("TieSilk"); tmat.use_nodes = True
tmat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.08, 0.05, 0.25, 1); tmat.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.35
tm.materials.append(tmat)
sw = tie.modifiers.new("OnShirt", 'SHRINKWRAP'); sw.target = shirt; sw.wrap_method = 'NEAREST_SURFACEPOINT'; sw.offset = 0.003
g = tie.vertex_groups.new(name="spine01"); g.add(list(range(len(tm.vertices))), 1.0, 'REPLACE')
am = tie.modifiers.new("Armature", 'ARMATURE'); am.object = r; tie.modifiers.move(1, 0)
so = tie.modifiers.new("t", 'SOLIDIFY'); so.thickness = 0.003
VL.clear_keys(tie, ("hide_render",))
for kp in [f for f in VL.fcurves(suit) if f.data_path == "hide_render"][0].keyframe_points:
    tie.hide_render = bool(kp.co.y); tie.keyframe_insert("hide_render", frame=int(kp.co.x))
VL.constant(tie, ("hide_render",))
VL.key_hide(suit, [])
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print("GARMENTS_DONE", OUT)
