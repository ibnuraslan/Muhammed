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
_d = suit.modifiers.new("Puff", 'DISPLACE'); _d.strength = 0.006; _d.mid_level = 0.0   # skin no longer pokes through at the shoulders
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
