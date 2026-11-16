# garment() and stripe_mat() from AshaDegree_v001/scripts/02_dress.py (ConnectB06): a garment cut from the body skin, offset outward, same weights.
def stripe_mat(name, base, stripe, z_bands, axis_z=True):
    """hi-vis: base colour with reflective silver bands at given heights (object space z of the rest mesh)"""
    m = mat(name, base, 0.45); nt = m.node_tree; P = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord"); sep = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(tc.outputs["Object"], sep.inputs[0])
    acc = None
    for z0, z1 in z_bands:
        a = nt.nodes.new("ShaderNodeMath"); a.operation = 'GREATER_THAN'; a.inputs[1].default_value = z0
        b = nt.nodes.new("ShaderNodeMath"); b.operation = 'LESS_THAN'; b.inputs[1].default_value = z1
        nt.links.new(sep.outputs[2], a.inputs[0]); nt.links.new(sep.outputs[2], b.inputs[0])
        c = nt.nodes.new("ShaderNodeMath"); c.operation = 'MULTIPLY'; nt.links.new(a.outputs[0], c.inputs[0]); nt.links.new(b.outputs[0], c.inputs[1])
        if acc is None: acc = c
        else:
            d = nt.nodes.new("ShaderNodeMath"); d.operation = 'MAXIMUM'; nt.links.new(acc.outputs[0], d.inputs[0]); nt.links.new(c.outputs[0], d.inputs[1]); acc = d
    mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = 'RGBA'; nt.links.new(acc.outputs[0], mx.inputs['Factor'])
    mx.inputs['A'].default_value = (*base, 1); mx.inputs['B'].default_value = (*stripe, 1)
    nt.links.new(mx.outputs['Result'], P.inputs["Base Color"])
    mr = nt.nodes.new("ShaderNodeMapRange"); nt.links.new(acc.outputs[0], mr.inputs[0]); mr.inputs[3].default_value = 0.0; mr.inputs[4].default_value = 0.7
    nt.links.new(mr.outputs[0], P.inputs["Metallic"])
    return m

def dominant_bone(v, names):
    best = None; bw = 0
    for g in v.groups:
        n = names[g.group]
        if n in NONBONE or n.startswith(("helper", "joint")): continue
        if g.weight > bw: bw = g.weight; best = n
    return best

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

