"""Merge the characters into one file, recolour clothes (non-skin colours, no logos), hair tints, eye fix.
blender -b --python 02_dress.py -- /tmp/claude-0/kh/work/chars.blend"""
import bpy, sys
out = sys.argv[sys.argv.index("--") + 1]
W = "/tmp/claude-0/kh/work/"
bpy.ops.wm.read_factory_settings(use_empty=True)
for i, c in enumerate(["Kid", "Mom", "AgentB", "AgentC"]):
    with bpy.data.libraries.load(W + "ch_%s.blend" % c) as (fd, td):
        td.objects = list(fd.objects)
    for o in td.objects:
        if o: bpy.context.scene.collection.objects.link(o)
    bpy.data.objects[c].location.x = i * 0.9
NONBONE = ("HelperGeometry", "JointCubes", "Left", "Right", "Mid", "body")
def mat(name, rgb, rough=0.6, sheen=0.0):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True; P = m.node_tree.nodes.get("Principled BSDF")
    P.inputs["Base Color"].default_value = (*rgb, 1); P.inputs["Roughness"].default_value = rough
    if sheen: P.inputs["Sheen Weight"].default_value = sheen
    return m
def floral(name):
    """cream blouse with soft pink/orange/blue blossoms (voronoi spots), no text"""
    m = mat(name, (0.9, 0.85, 0.78), 0.6, 0.3); nt = m.node_tree; P = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord"); mp = nt.nodes.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (14, 14, 14)
    nt.links.new(tc.outputs["Object"], mp.inputs[0])
    vo = nt.nodes.new("ShaderNodeTexVoronoi"); vo.feature = 'F1'; nt.links.new(mp.outputs[0], vo.inputs["Vector"])
    vo.inputs["Randomness"].default_value = 0.9
    ramp = nt.nodes.new("ShaderNodeValToRGB"); nt.links.new(vo.outputs["Distance"], ramp.inputs[0])
    ramp.color_ramp.elements[0].position = 0.26; ramp.color_ramp.elements[0].color = (1, 1, 1, 1)
    ramp.color_ramp.elements[1].position = 0.32; ramp.color_ramp.elements[1].color = (0, 0, 0, 1)
    cr = nt.nodes.new("ShaderNodeValToRGB"); nt.links.new(vo.outputs["Color"], cr.inputs[0])
    els = cr.color_ramp.elements; els[0].color = (0.95, 0.3, 0.45, 1); els[1].color = (1.0, 1.0, 1.0, 1)
    e = els.new(0.5); e.color = (0.95, 0.5, 0.15, 1); cr.color_ramp.interpolation = 'CONSTANT'
    mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = 'RGBA'; nt.links.new(ramp.outputs[0], mx.inputs['Factor'])
    mx.inputs['A'].default_value = (0.16, 0.38, 0.85, 1)   # sky-blue blouse base (clearly not skin); nt.links.new(cr.outputs[0], mx.inputs['B'])
    nt.links.new(mx.outputs['Result'], P.inputs["Base Color"])
    return m
def dominant_bone(v, names):
    best = None; bw = 0
    for g in v.groups:
        n = names.get(g.group, "")
        if n in NONBONE or n.startswith(("helper", "joint")): continue
        if g.weight > bw: bw = g.weight; best = n
    return best
TOP = ("spine", "clavicle", "shoulder", "breast", "pectoral", "upperarm", "lowerarm", "neck", "wrist")
def split_top(ob, top_mat, bot_mat, zcut):
    names = {g.index: g.name for g in ob.vertex_groups}
    ob.data.materials.clear(); ob.data.materials.append(bot_mat); ob.data.materials.append(top_mat)
    vt = [(lambda b: bool(b) and b.startswith(TOP))(dominant_bone(v, names)) and v.co.z > zcut for v in ob.data.vertices]
    for p in ob.data.polygons:
        p.material_index = 1 if sum(vt[i] for i in p.vertices) * 2 > len(p.vertices) else 0
def tint_tex(ob, rgb):
    for m in ob.data.materials:
        if not m: continue
        trees = [m.node_tree] + [n.node_tree for n in m.node_tree.nodes if n.type == 'GROUP' and n.node_tree]
        for nt in trees:
            for nd in list(nt.nodes):
                if nd.type == 'TEX_IMAGE' and nd.image and "normal" not in nd.image.name.lower():
                    for lk in list(nd.outputs['Color'].links):
                        if lk.to_node.name.startswith("Tint"): continue
                        mx = nt.nodes.new('ShaderNodeMix'); mx.name = "Tint"; mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'
                        mx.inputs['Factor'].default_value = 1.0; mx.inputs['B'].default_value = (*rgb, 1)
                        nt.links.new(nd.outputs['Color'], mx.inputs['A']); nt.links.new(mx.outputs['Result'], lk.to_socket)
import bmesh, math
def garment(rig, name, keep, material, offset=0.012, thick=0.003, mask_body=True, zmin=None, zmax=None, src=None, smooth=(0.5, 3), flat_chest=False):
    body = bpy.data.objects[src or (rig + ".body")]
    skin = bpy.data.objects[rig + ".body"]
    names = {g.index: g.name for g in body.vertex_groups}
    bidx = body.vertex_groups["body"].index
    me = body.data
    kb = me.shape_keys.key_blocks if me.shape_keys else None
    if kb:
        base = kb[0].data; cos = [base[i].co.copy() for i in range(len(me.vertices))]
        for k in kb[1:]:
            if k.value == 0 or k.mute: continue
            for i, d in enumerate(k.data): cos[i] += k.value * (d.co - base[i].co)
    else:
        cos = [v.co.copy() for v in me.vertices]
    H = max(c.z for c in cos)
    sel = set()
    for v in me.vertices:
        if zmin is not None and cos[v.index].z < zmin * H: continue
        if zmax is not None and cos[v.index].z > zmax * H: continue
        if any(names.get(g.group, '') in ('HelperGeometry', 'JointCubes') and g.weight > 0.01 for g in v.groups): continue
        b = dominant_bone(v, names)
        if b and keep(b, v.co):
            sel.add(v.index)
    # close small holes in the selection (verts mostly surrounded by selected ones)
    nbr = {}
    for e in me.edges:
        a_, b_ = e.vertices; nbr.setdefault(a_, set()).add(b_); nbr.setdefault(b_, set()).add(a_)
    for _ in range(4):
        add = {i for i, ns in nbr.items() if i not in sel and ns and sum(1 for k in ns if k in sel) >= 0.6 * len(ns)}
        if not add: break
        sel |= add
    # garment object = copy of body restricted to sel
    g = body.copy(); g.data = body.data.copy(); g.name = rig + "." + name; g.data.name = g.name
    bpy.context.scene.collection.objects.link(g); g.hide_render = False; g.hide_viewport = False
    for m in list(g.modifiers):
        if m.type != 'ARMATURE': g.modifiers.remove(m)
    if g.data.shape_keys:   # bake the body shape (child) into the garment so it can be smoothed as real geometry
        with bpy.context.temp_override(object=g, active_object=g, selected_objects=[g]):
            bpy.ops.object.shape_key_remove(all=True, apply_mix=True)
    bm = bmesh.new(); bm.from_mesh(g.data); bm.verts.ensure_lookup_table()
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.index not in sel], context='VERTS')
    _he = [e for e in bm.edges if e.is_boundary]
    if smooth[1] > 5: bmesh.ops.holes_fill(bm, edges=_he, sides=16)
    if smooth[1] > 5:
        _dl = bm.verts.layers.deform.active
        _nm = {g.index: g.name for g in body.vertex_groups}
        def _torso(v):
            if _dl is None: return True
            best = max(((w, _nm.get(gi, "")) for gi, w in v[_dl].items() if not _nm.get(gi, "").startswith(NONBONE + ("helper", "joint"))), default=(0, ""))
            return best[1].startswith(("breast", "pectoral", "spine", "clavicle"))
        inner_v = [v for v in bm.verts if not v.is_boundary and _torso(v)]
        _c0 = [v.co.copy() for v in inner_v]
        for _ in range(smooth[1] * 6):
            bmesh.ops.smooth_vert(bm, verts=inner_v, factor=0.5, use_axis_x=True, use_axis_y=True, use_axis_z=True)
        print("SMOOTHED", name, len(inner_v), "mean move %.4f" % (sum((v.co - c).length for v, c in zip(inner_v, _c0)) / max(1, len(inner_v))))
    if flat_chest:
        # child chest: heavy local smoothing in a disc round each side of the upper chest (removes the body's nipple relief)
        for sx_ in (-1, 1):
            cands = [v for v in bm.verts if 0.04 < sx_ * v.co.x < 0.12 and v.co.y < 0]
            zc = sorted(v.co.z for v in cands)
            # the relief sits at the most forward point of the upper chest band
            top = max(v.co.z for v in bm.verts)
            band = [v for v in cands if 0.66 * top < v.co.z < 0.80 * top]
            if not band: continue
            c = min(band, key=lambda v: v.co.y).co.copy()
            disc = [v for v in bm.verts if (v.co - c).length < 0.05 and not v.is_boundary]
            for _ in range(200):
                bmesh.ops.smooth_vert(bm, verts=disc, factor=0.5, use_axis_x=True, use_axis_y=True, use_axis_z=True)
            print("NUBSMOOTH", sx_, tuple(round(x, 3) for x in c), len(disc))
        bins = {}
        for v in bm.verts:
            if abs(v.co.x) < 0.025: k = round(v.co.z / 0.01); bins[k] = min(bins.get(k, 9), v.co.y)
        n = 0; hit = set()
        for v in bm.verts:
            k = round(v.co.z / 0.01)
            if abs(v.co.x) < 0.16 and v.co.y < 0 and k in bins and v.co.y < bins[k] - 0.002:
                v.co.y = bins[k] - 0.002; n += 1; hit.add(v)
        ring = set(hit)
        for _ in range(3):
            ring |= {w for v in list(ring) for e in v.link_edges for w in e.verts}
        ring = [v for v in ring if not v.is_boundary]
        for _ in range(60):
            bmesh.ops.smooth_vert(bm, verts=ring, factor=0.5, use_axis_x=True, use_axis_y=True, use_axis_z=True)
        print("FLATCHEST", n, len(ring))
    bm.to_mesh(g.data); bm.free()
    with bpy.context.temp_override(object=g, active_object=g, selected_objects=[g]):
        try: bpy.ops.mesh.customdata_custom_splitnormals_clear()
        except Exception as ex: print("normals clear", ex)
    g.data.materials.clear(); g.data.materials.append(material)
    for p in g.data.polygons: p.use_smooth = True
    if offset:
        d = g.modifiers.new("Offset", 'DISPLACE'); d.strength = offset; d.mid_level = 0.0; d.direction = 'NORMAL'
        sm = g.modifiers.new("Smooth", 'SMOOTH'); sm.factor = smooth[0]; sm.iterations = smooth[1]
    so = g.modifiers.new("Thick", 'SOLIDIFY'); so.thickness = thick; so.offset = -1
    # move the armature modifier first (deform, then offset in posed space)
    while g.modifiers[0].type != 'ARMATURE': bpy.ops.object.modifier_move_up if False else g.modifiers.move(g.modifiers.find(g.modifiers[0].name), len(g.modifiers) - 1)
    if mask_body:
        # interior of sel (two rings in from the edge) is hidden on the skin
        adj = {i: set() for i in sel}
        for e in me.edges:
            a, b = e.vertices
            if a in adj: adj[a].add(b)
            if b in adj: adj[b].add(a)
        inner = set(sel)
        for _ in range(2):
            inner = {i for i in inner if adj[i] <= inner}
        vg = skin.vertex_groups.new(name="cover_" + name); vg.add(list(inner), 1.0, 'REPLACE')
        mk = skin.modifiers.new("Mask_" + name, 'MASK'); mk.vertex_group = vg.name; mk.invert_vertex_group = True
        while skin.modifiers.find(mk.name) > 1: skin.modifiers.move(skin.modifiers.find(mk.name), skin.modifiers.find(mk.name) - 1)
    print("GARMENT", g.name, len(sel), "verts")
    return g


# Kid: floral blouse, blue jeans, brown hair
K = bpy.data.objects["Kid"]
suit = bpy.data.objects["Kid.female_casualsuit01"]
split_top(suit, floral("Kid_Floral"), mat("Kid_Jeans", (0.12, 0.2, 0.38), 0.7), K.data.bones["upperleg01.L"].head_local.z + 0.06)
tint_tex(bpy.data.objects["Kid.long01"], (0.75, 0.55, 0.4))   # long hair parted in the middle (no fringe over the eyes), mid brown
_o = bpy.data.objects["Kid.shoes02"]; _o.hide_render = True; _o.hide_viewport = True   # refit broke the shoe mesh: shoes are made from the foot skin instead
for m in list(bpy.data.objects["Kid.body"].modifiers):
    if m.type == 'MASK' and "shoes" in (m.vertex_group or ""): bpy.data.objects["Kid.body"].modifiers.remove(m)
garment("Kid", "sneakers", lambda b, co: b.startswith(("foot", "toe")), mat("Kid_Shoes", (0.8, 0.22, 0.32), 0.5), offset=0.008, thick=0.004)
# v002c: clean top. The casual suit stays (short sleeves deform well on reaching arms) but its lumps are smoothed out,
# the outward offset is tiny, and the skin under it is hidden by proximity so nothing pokes through.
_sm = suit.modifiers.new("Unlump", 'CORRECTIVE_SMOOTH'); _sm.factor = 1.0; _sm.iterations = 30; _sm.smooth_type = 'LENGTH_WEIGHTED'; _sm.rest_source = 'ORCO'
_d = suit.modifiers.new("Puff", "DISPLACE"); _d.strength = 0.007; _d.mid_level = 0.0
for _p in suit.data.polygons: _p.use_smooth = True
for _md in suit.modifiers:
    if _md.type == 'SUBSURF': _md.render_levels = 2; _md.levels = 1
# order: armature, unlump, subsurf, puff
for _nm_, _ix in (("Unlump", 1),):
    while suit.modifiers.find(_nm_) > _ix: suit.modifiers.move(suit.modifiers.find(_nm_), suit.modifiers.find(_nm_) - 1)
from mathutils.bvhtree import BVHTree as _BVH
_KB = bpy.data.objects["Kid.body"]
bpy.context.view_layer.update(); _dgx = bpy.context.evaluated_depsgraph_get()
_saved = [(m, m.show_viewport) for m in _KB.modifiers if m.type == 'MASK']
for m, _ in _saved: m.show_viewport = False
_se = suit.evaluated_get(_dgx).to_mesh(); _bv = _BVH.FromPolygons([v.co.copy() for v in _se.vertices], [tuple(p.vertices) for p in _se.polygons])
_be = _KB.evaluated_get(bpy.context.evaluated_depsgraph_get()); _bm_ = _be.to_mesh()
_ef = {}
for _p in _se.polygons:
    for _ek in _p.edge_keys: _ef[_ek] = _ef.get(_ek, 0) + 1
_bdv = sorted({vi for ek, n in _ef.items() if n == 1 for vi in ek})
from mathutils.kdtree import KDTree as _KDT
_kd = _KDT(len(_bdv))
for _n_, vi in enumerate(_bdv): _kd.insert(_se.vertices[vi].co, _n_)
_kd.balance()
_cov = [i for i, v in enumerate(_bm_.vertices) if i < len(_KB.data.vertices) and (_bv.find_nearest(v.co)[3] or 9) < 0.012
        and _kd.find(v.co)[2] > 0.035]   # well inside the garment only: neckline, hems and cuffs keep their skin
for m, sv in _saved: m.show_viewport = sv
_vg = _KB.vertex_groups.new(name="cover_casualsuit_v002c"); _vg.add(_cov, 1.0, 'REPLACE')
_mk = _KB.modifiers.new("Mask_casual_v002c", 'MASK'); _mk.vertex_group = _vg.name; _mk.invert_vertex_group = True
while _KB.modifiers.find(_mk.name) > 1: _KB.modifiers.move(_KB.modifiers.find(_mk.name), _KB.modifiers.find(_mk.name) - 1)
print("TOP_UNLUMP cover", len(_cov))
# hair: a proper strand shader on long01 (strand bump + streaks from its own texture, anisotropic sheen, darker brown) + small clumping
_H = bpy.data.objects["Kid.long01"]
for _m in _H.data.materials:
    _nt = _m.node_tree; _P = next(n for n in _nt.nodes if n.type == 'BSDF_PRINCIPLED')
    _tx = next(n for n in _nt.nodes if n.type == 'TEX_IMAGE')
    _bw = _nt.nodes.new("ShaderNodeRGBToBW"); _nt.links.new(_tx.outputs["Color"], _bw.inputs[0])
    _cr = _nt.nodes.new("ShaderNodeValToRGB"); _nt.links.new(_bw.outputs[0], _cr.inputs[0])
    _cr.color_ramp.elements[0].position = 0.15; _cr.color_ramp.elements[0].color = (0.035, 0.018, 0.009, 1)
    _cr.color_ramp.elements[1].position = 0.75; _cr.color_ramp.elements[1].color = (0.30, 0.17, 0.08, 1)
    _nt.links.new(_cr.outputs[0], _P.inputs["Base Color"])
    _bp = _nt.nodes.new("ShaderNodeBump"); _bp.inputs["Strength"].default_value = 0.6; _bp.inputs["Distance"].default_value = 0.002
    _nt.links.new(_bw.outputs[0], _bp.inputs["Height"]); _nt.links.new(_bp.outputs[0], _P.inputs["Normal"])
    _P.inputs["Roughness"].default_value = 0.42
    if "Anisotropic" in _P.inputs: _P.inputs["Anisotropic"].default_value = 0.7
    if "Sheen Weight" in _P.inputs: _P.inputs["Sheen Weight"].default_value = 0.35; _P.inputs["Sheen Tint"].default_value = (0.6, 0.4, 0.25, 1)
    if "Specular IOR Level" in _P.inputs: _P.inputs["Specular IOR Level"].default_value = 0.35
_ct = bpy.data.textures.new("HairClumps", 'CLOUDS'); _ct.noise_scale = 0.03
_dm = _H.modifiers.new("Clumps", 'DISPLACE'); _dm.texture = _ct; _dm.strength = 0.006; _dm.mid_level = 0.5; _dm.texture_coords = 'LOCAL'
print("HAIR_SHADER", len(_H.data.materials))
# Mom: light-blue work suit (no badges), warm auburn hair
ws = bpy.data.objects["Mom.female_elegantsuit01"]; ws.data.materials.clear(); ws.data.materials.append(mat("Mom_BlueJacket", (0.12, 0.3, 0.75), 0.55, 0.2))
sk = bpy.data.objects["Mom.long_skirt"]; sk.data.materials.clear(); sk.data.materials.append(mat("Mom_NavySkirt", (0.06, 0.09, 0.22), 0.6))
sh = bpy.data.objects["Mom.shoes01"]; sh.data.materials.clear(); sh.data.materials.append(mat("Mom_Shoes", (0.08, 0.06, 0.05), 0.4))
tint_tex(bpy.data.objects["Mom.long01"], (1.0, 0.75, 0.5))
for n in [c + s for c in ("Kid", "Mom", "AgentB", "AgentC") for s in (".teeth_base", ".tongue01")]:
    o = bpy.data.objects.get(n)
    if o: o.hide_render = True; o.hide_viewport = True
# director P1 note: the girl read as a porcelain doll. Normal-size, darker (brown) iris, less glassy cornea, warmer skin.
for n in bpy.data.objects["Kid.high-poly"].active_material.node_tree.nodes:
    if n.type == 'GROUP' and "IrisMajorColor" in n.inputs:
        n.inputs["IrisMajorColor"].default_value = (0.16, 0.085, 0.04, 1); n.inputs["IrisMinorColor"].default_value = (0.07, 0.035, 0.015, 1)
        n.inputs["IrisSection4Color"].default_value = (0.05, 0.03, 0.015, 1)
        n.inputs["IrisToEyeWhiteRelation"].default_value = 0.33
        n.inputs["EyeWhiteColor"].default_value = (0.9, 0.88, 0.86, 1)
        n.inputs["Clearcoat"].default_value = 0.15; n.inputs["OuterLayerRoughness"].default_value = 0.08
for m in bpy.data.objects["Kid.body"].data.materials:
    if not m: continue
    for nt in [m.node_tree] + [x.node_tree for x in m.node_tree.nodes if x.type == 'GROUP' and x.node_tree]:
        for nd in list(nt.nodes):
            if nd.type == 'TEX_IMAGE' and nd.image and "diffuse" in nd.image.name.lower():
                for lk in list(nd.outputs['Color'].links):
                    mx = nt.nodes.new('ShaderNodeMix'); mx.name = "WarmSkin"; mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'
                    mx.inputs['Factor'].default_value = 1.0; mx.inputs['B'].default_value = (1.0, 0.8, 0.66, 1)
                    nt.links.new(nd.outputs['Color'], mx.inputs['A']); nt.links.new(mx.outputs['Result'], lk.to_socket)
                print("WARMSKIN", nd.image.name)
# v002: (1) faces beside the nostrils whose UVs fall on a red patch of the skin texture (child refit) -> neighbour skin UV;
# (2) eyeballs set 2 mm back / 1 mm up so the white no longer shows below the lower lid
import numpy as _np
_B = bpy.data.objects["Kid.body"]; _me = _B.data; _uv = _me.uv_layers.active.data
_img = next(n.image for m in _me.materials[:1] for nt in [m.node_tree] + [x.node_tree for x in m.node_tree.nodes if x.type == 'GROUP' and x.node_tree]
            for n in nt.nodes if n.type == 'TEX_IMAGE' and n.image and "diffuse" in n.image.name.lower())
_w, _h = _img.size; _px = _np.array(_img.pixels[:]).reshape(_h, _w, 4)
def _ctr(p): return (sum(_uv[l].uv[0] for l in p.loop_indices) / p.loop_total, sum(_uv[l].uv[1] for l in p.loop_indices) / p.loop_total)
def _red(u, v):
    c = _px[min(_h - 1, int(v * _h)), min(_w - 1, int(u * _w))]; return c[0] - c[1] > 0.33
_boxes = ((0.765, 0.80, 0.02, 0.06), (0.885, 0.92, 0.02, 0.06))
_bad = [p for p in _me.polygons if any(b0 <= _ctr(p)[0] <= b1 and b2 <= _ctr(p)[1] <= b3 for b0, b1, b2, b3 in _boxes) and _red(*_ctr(p))]
_vf = {}
for p in _me.polygons:
    for vi in p.vertices: _vf.setdefault(vi, []).append(p.index)
_badset = {p.index for p in _bad}
for p in _bad:
    nb = [_me.polygons[j] for vi in p.vertices for j in _vf[vi] if j not in _badset and not _red(*_ctr(_me.polygons[j]))]
    if not nb: continue
    u, v = _ctr(nb[0])
    pass
print("NOSTRIL_UV_FIX", len(_bad))
# the remap alone did not clear it: inside the two UV boxes the shader now uses a flat sampled skin colour, alpha 1
_ring = [_px[y, x][:3] for (b0, b1, b2, b3) in _boxes for y in range(int(b2 * _h), int(b3 * _h)) for x in range(int(b0 * _w), int(b1 * _w))
         if _px[y, x][0] - _px[y, x][1] < 0.22 and _px[y, x][3] > 0.9]
_skin = _np.mean(_ring, axis=0) if _ring else _np.array([0.8, 0.6, 0.5]); print("NOSTRIL_SKIN", _skin.round(3), len(_ring))
_nt, _dt = next((nt, n) for m in _me.materials[:1] for nt in [m.node_tree] + [x.node_tree for x in m.node_tree.nodes if x.type == 'GROUP' and x.node_tree]
                 for n in nt.nodes if n.type == 'TEX_IMAGE' and n.image == _img)
_tc = _nt.nodes.new("ShaderNodeTexCoord")
_sep = _nt.nodes.new("ShaderNodeSeparateXYZ"); _nt.links.new(_tc.outputs["UV"], _sep.inputs[0])
_acc = None
for (b0, b1, b2, b3) in _boxes:
    parts = []
    for comp, lo, hi in ((0, b0, b1), (1, b2, b3)):
        g = _nt.nodes.new("ShaderNodeMath"); g.operation = 'GREATER_THAN'; g.inputs[1].default_value = lo; _nt.links.new(_sep.outputs[comp], g.inputs[0])
        l_ = _nt.nodes.new("ShaderNodeMath"); l_.operation = 'LESS_THAN'; l_.inputs[1].default_value = hi; _nt.links.new(_sep.outputs[comp], l_.inputs[0])
        parts += [g, l_]
    mul = parts[0]
    for q in parts[1:]:
        mm = _nt.nodes.new("ShaderNodeMath"); mm.operation = 'MULTIPLY'; _nt.links.new(mul.outputs[0], mm.inputs[0]); _nt.links.new(q.outputs[0], mm.inputs[1]); mul = mm
    if _acc is None: _acc = mul
    else:
        mx_ = _nt.nodes.new("ShaderNodeMath"); mx_.operation = 'MAXIMUM'; _nt.links.new(_acc.outputs[0], mx_.inputs[0]); _nt.links.new(mul.outputs[0], mx_.inputs[1]); _acc = mx_
_inv = _nt.nodes.new("ShaderNodeMath"); _inv.operation = 'SUBTRACT'; _inv.inputs[0].default_value = 1.0; _nt.links.new(_dt.outputs['Alpha'], _inv.inputs[1])
_fac = _nt.nodes.new("ShaderNodeMath"); _fac.operation = 'MAXIMUM'; _nt.links.new(_acc.outputs[0], _fac.inputs[0]); _nt.links.new(_inv.outputs[0], _fac.inputs[1])
_acc = _fac   # patch inside the boxes AND wherever the texture is transparent (white texels)
for lk in list(_dt.outputs['Color'].links):
    mc = _nt.nodes.new('ShaderNodeMix'); mc.data_type = 'RGBA'; mc.name = "NostrilPatch"
    _nt.links.new(_acc.outputs[0], mc.inputs['Factor']); _nt.links.new(_dt.outputs['Color'], mc.inputs['A']); mc.inputs["B"].default_value = (*(_skin * 0.58).tolist(), 1)
    _nt.links.new(mc.outputs['Result'], lk.to_socket)
for lk in list(_dt.outputs['Alpha'].links):   # skin is opaque: the texture alpha opened see-through specks beside the nose
    sock = lk.to_socket; _nt.links.remove(lk); sock.default_value = 1.0
_E = bpy.data.objects["Kid.high-poly"]
for _v in _E.data.vertices: _v.co.y += 0.002; _v.co.z += 0.001   # (kept) then scaled 0.87 about each eye below
if _E.data.shape_keys:
    for _kb in _E.data.shape_keys.key_blocks:
        for _d in _kb.data: _d.co.y += 0.002; _d.co.z += 0.001
# v002b (director): no faceting at full quality, smaller eyes with less white, slightly lowered upper lids, soft brows, less waxy skin
for _n in ("Kid.long01", "Kid.female_casualsuit01", "Kid.eyebrow001"):
    _o = bpy.data.objects[_n]
    for _p in _o.data.polygons: _p.use_smooth = True
    for _md in _o.modifiers:
        if _md.type == 'SUBSURF': _md.render_levels = 2; _md.levels = 1
from mathutils import Vector as _V
_E = bpy.data.objects["Kid.high-poly"]
_ctr = {}
for _sd in (1, -1):
    _vs = [v for v in _E.data.vertices if v.co.x * _sd > 0]
    _c = sum((v.co for v in _vs), _V()) / len(_vs); _ctr[_sd] = _c.copy()
    for v in _vs: v.co = _c + (v.co - _c) * 0.87 + _V((0, -0.001, 0))
for n in _E.active_material.node_tree.nodes:
    if n.type == 'GROUP' and "IrisToEyeWhiteRelation" in n.inputs: n.inputs["IrisToEyeWhiteRelation"].default_value = 0.46
# upper lids: new shape key on the body, a soft 2.5 mm drop of the skin just above each eye (front of the face only)
_kb = _B.data.shape_keys.key_blocks
_rest = [_kb[0].data[i].co.copy() for i in range(len(_B.data.vertices))]
for _k in _kb[1:]:
    if _k.value and not _k.mute:
        for i, d in enumerate(_k.data): _rest[i] += _k.value * (d.co - _kb[0].data[i].co)
_lid = _B.shape_key_add(name="LidDrop", from_mix=False); _nlid = 0
for i, co in enumerate(_rest):
    for _sd, c in _ctr.items():
        dx, dz = co.x - c.x, co.z - c.z; r = (dx * dx + (dz * 0.8) ** 2) ** 0.5
        if r < 0.021 and dz > 0.004 and co.y < c.y - 0.002:
            f_ = 1 - (r / 0.021) ** 2
            _lid.data[i].co = _kb[0].data[i].co + _V((0, 0, -0.0025 * f_)); _nlid += 1
_lid.value = 1.0
print("LIDDROP", _nlid)
# nostril fold (mesh level): Laplacian-smooth the small fold beside each nostril so no crease or fleck shows
_nv = set(vi for p in _bad for vi in p.vertices)
_nbr = {}
for e in _B.data.edges:
    a_, b_ = e.vertices; _nbr.setdefault(a_, set()).add(b_); _nbr.setdefault(b_, set()).add(a_)
_cur = {i: _rest[i].copy() for i in _nv}
for _it in range(12):
    _new = {}
    for i in _nv:
        ns = [(_cur[j] if j in _cur else _rest[j]) for j in _nbr.get(i, ())]
        if ns: _new[i] = _cur[i] * 0.5 + (sum(ns, _V()) / len(ns)) * 0.5
    _cur.update(_new)
_nf = _B.shape_key_add(name="NoseFix", from_mix=False)
for i in _nv: _nf.data[i].co = _kb[0].data[i].co + (_cur[i] - _rest[i])
_nf.value = 1.0
print("NOSEFIX", len(_nv), "max move %.4f" % max((_cur[i] - _rest[i]).length for i in _nv))
# brows: thicker, softer brown
_BR = bpy.data.objects["Kid.eyebrow001"]
for _sd in (1, -1):
    _vs = [v for v in _BR.data.vertices if v.co.x * _sd > 0]
    _c = sum((v.co for v in _vs), _V()) / len(_vs)
    for v in _vs: v.co.z = _c.z + (v.co.z - _c.z) * 1.55
tint_tex(_BR, (0.55, 0.38, 0.25))
# skin: warmer, less waxy (less subsurface, a little rougher)
for m in _B.data.materials[:1]:
    for nt in [m.node_tree] + [x.node_tree for x in m.node_tree.nodes if x.type == 'GROUP' and x.node_tree]:
        for nd in nt.nodes:
            if nd.name == "WarmSkin": nd.inputs['B'].default_value = (1.0, 0.74, 0.58, 1)
            if nd.type == 'BSDF_PRINCIPLED':
                nd.inputs["Roughness"].default_value = max(0.55, nd.inputs["Roughness"].default_value)
                if not nd.inputs["Subsurface Weight"].links: nd.inputs["Subsurface Weight"].default_value = min(0.12, nd.inputs["Subsurface Weight"].default_value)
                print("SKINBSDF", nt.name, nd.inputs["Subsurface Weight"].default_value, bool(nd.inputs["Subsurface Weight"].links))
            if nd.name == "SSSStrength" and hasattr(nd, "outputs") and nd.type == 'VALUE': nd.outputs[0].default_value = min(0.12, nd.outputs[0].default_value)
# eye fix on every EnhancedEye group
for ng in list(bpy.data.node_groups):
    if ng.name.startswith("EnhancedEye") and "CorneaTransparentMix" not in ng.nodes:
        src = open("/home/user/Muhammed/blender/KidHacker_v001/scripts/eye_fix.py").read().replace('bpy.data.node_groups["EnhancedEye"]', 'bpy.data.node_groups["%s"]' % ng.name)
        exec(src, {"bpy": bpy, "sys": sys, "_NO_SAVE": True})
for o in bpy.data.objects:
    if o.type == 'MESH':
        for m in o.data.materials:
            if m and "eye" in m.name.lower(): print("EYEMAT", o.name, m.name)
bpy.ops.wm.save_as_mainfile(filepath=out, compress=True)
print("DRESSED")
