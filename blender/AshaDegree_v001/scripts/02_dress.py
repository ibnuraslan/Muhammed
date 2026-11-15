"""Dress the characters: garments generated from each body's own skin (same weights, so they deform with it),
offset outward; the skin under a garment is masked so nothing pokes through.
blender -b work/chars.blend --python 02_dress.py -- work/dressed.blend"""
import bpy, bmesh, sys, math
from mathutils import Vector
out = sys.argv[sys.argv.index("--") + 1]
NONBONE = ("HelperGeometry", "JointCubes", "Left", "Right", "Mid", "body")

def mat(name, rgb, rough=0.6, sheen=0.0, emit=None):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True; P = m.node_tree.nodes.get("Principled BSDF")
    P.inputs["Base Color"].default_value = (*rgb, 1); P.inputs["Roughness"].default_value = rough
    if sheen: P.inputs["Sheen Weight"].default_value = sheen
    return m

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

def garment(rig, name, keep, material, offset=0.012, thick=0.003, mask_body=True, zmin=None, zmax=None):
    body = bpy.data.objects[rig + ".body"]
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
        if not any(g.group == bidx and g.weight > 0.5 for g in v.groups): continue
        b = dominant_bone(v, names)
        if b and keep(b, v.co):
            sel.add(v.index)
    # garment object = copy of body restricted to sel
    g = body.copy(); g.data = body.data.copy(); g.name = rig + "." + name; g.data.name = g.name
    bpy.context.scene.collection.objects.link(g)
    for m in list(g.modifiers):
        if m.type != 'ARMATURE': g.modifiers.remove(m)
    bm = bmesh.new(); bm.from_mesh(g.data); bm.verts.ensure_lookup_table()
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.index not in sel], context='VERTS')
    bm.to_mesh(g.data); bm.free()
    g.data.materials.clear(); g.data.materials.append(material)
    for p in g.data.polygons: p.use_smooth = True
    d = g.modifiers.new("Offset", 'DISPLACE'); d.strength = offset; d.mid_level = 0.0; d.direction = 'NORMAL'
    sm = g.modifiers.new("Smooth", 'SMOOTH'); sm.factor = 0.5; sm.iterations = 3
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
        vg = body.vertex_groups.new(name="cover_" + name); vg.add(list(inner), 1.0, 'REPLACE')
        mk = body.modifiers.new("Mask_" + name, 'MASK'); mk.vertex_group = vg.name; mk.invert_vertex_group = True
        # place the mask right after the armature modifier
        while body.modifiers.find(mk.name) > 1: body.modifiers.move(body.modifiers.find(mk.name), body.modifiers.find(mk.name) - 1)
    print("GARMENT", g.name, len(sel), "verts")
    return g

TOP = ("spine", "clavicle", "shoulder", "breast", "pectoral", "upperarm", "lowerarm")
LEG = ("pelvis", "upperleg", "lowerleg")
def is_top(b, co): return b.startswith(TOP) or (b.startswith("pelvis") and False)
def is_vest(b, co): return b.startswith(("spine", "clavicle", "breast", "pectoral"))
def is_legs(b, co): return b.startswith(LEG) or b == "root"

def tint_group(ob, rgb):
    """multiply the diffuse texture inside the MPFB skin group"""
    for m in ob.data.materials:
        trees = [m.node_tree] + [n.node_tree for n in m.node_tree.nodes if n.type == 'GROUP']
        for nt in trees:
            for nd in list(nt.nodes):
                if nd.type == 'TEX_IMAGE' and nd.image and "diffuse" in nd.image.name.lower():
                    for lk in list(nd.outputs['Color'].links):
                        if lk.to_node.name.startswith("SkinTint"): continue
                        mx = nt.nodes.new('ShaderNodeMix'); mx.name = "SkinTint"; mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'
                        mx.inputs['Factor'].default_value = 1.0; mx.inputs['B'].default_value = (*rgb, 1)
                        nt.links.new(nd.outputs['Color'], mx.inputs['A']); nt.links.new(mx.outputs['Result'], lk.to_socket)
                    print("TINT", ob.name, nd.image.name)

for o in bpy.data.objects: o.hide_render = False; o.hide_viewport = False
POS = {}
for o in bpy.data.objects:
    if o.type == 'ARMATURE': POS[o.name] = o.location.copy(); o.location = (0, 0, 0)
bpy.context.view_layer.update()

def eval_pts(ob):
    dg = bpy.context.evaluated_depsgraph_get(); e = ob.evaluated_get(dg)
    return [ob.matrix_world @ v.co for v in e.to_mesh().vertices]

def attach(o, rig, bone):
    R = bpy.data.objects[rig]; pb = R.pose.bones[bone]
    c = o.constraints.new('CHILD_OF'); c.target = R; c.subtarget = bone
    c.inverse_matrix = (R.matrix_world @ pb.matrix).inverted()

def recolor_by_bone(ob, keep, material, zmin=0.57):
    """assign faces of a clothing mesh whose vertices are dominated by `keep` bones to a new material slot"""
    names = {g.index: g.name for g in ob.vertex_groups}
    ob.data.materials.append(material); mi = len(ob.data.materials) - 1
    H = max(v.co.z for v in bpy.data.objects[ob.parent.name + ".body"].data.vertices) if False else ob.parent.dimensions.z
    H = max(v.co.z for v in ob.data.vertices) / 0.8 if H < 0.5 else H
    vt = [bool((lambda b: b and keep(b, None))(dominant_bone(v, names))) and v.co.z > zmin * H for v in ob.data.vertices]
    n = 0
    for p in ob.data.polygons:
        if sum(vt[i] for i in p.vertices) * 2 > len(p.vertices): p.material_index = mi; n += 1
    print("RECOLOR", ob.name, n, "faces")

# ---------------- Girl: 9 years old, pink jacket, white trousers, pink shoes, dark ponytail with a pink scrunchie
G = bpy.data.objects["Girl"]
tint_group(bpy.data.objects["Girl.body"], (0.30, 0.19, 0.135))
pink = mat("Asha_PinkJacket", (0.85, 0.12, 0.38), 0.55, sheen=0.3)
white = mat("Asha_WhiteTrousers", (0.86, 0.84, 0.80), 0.6, sheen=0.2)
shoe = mat("Asha_PinkShoes", (0.9, 0.25, 0.5), 0.45)
hair = mat("Asha_Hair", (0.035, 0.022, 0.016), 0.55)
suit = bpy.data.objects["Girl.female_sportsuit01"]; suit.data.materials.clear(); suit.data.materials.append(white)
for p in suit.data.polygons: p.material_index = 0
sh = bpy.data.objects["Girl.shoes05"]; sh.data.materials.clear(); sh.data.materials.append(shoe)
hp = bpy.data.objects["Girl.ponytail01"]
for i, m in enumerate(hp.data.materials):
    # keep the hair card alpha: tint the diffuse very dark instead of replacing the material
    pass
tint_group(hp, (0.08, 0.06, 0.05))
recolor_by_bone(suit, is_top, pink, zmin=0.52)
# the crop top stays (pink); the bare skin that MPFB left (arms, midriff) gets a thin pink sleeve/band layer
garment("Girl", "jacket", lambda b, co: not b.startswith(("neck", "head", "wrist", "finger", "metacarpal", "jaw", "eye", "tongue", "levator", "oris", "orbicularis", "temporalis", "risorius", "special", "mandible", "cheek", "nose", "brow")), pink, offset=0.005, thick=0.003, zmin=0.50, zmax=0.83)
for n in bpy.data.objects["Girl.high-poly"].active_material.node_tree.nodes:
    if n.type == 'GROUP' and "IrisMajorColor" in n.inputs:
        n.inputs["IrisMajorColor"].default_value = (0.16, 0.08, 0.03, 1); n.inputs["IrisMinorColor"].default_value = (0.07, 0.035, 0.015, 1)
        n.inputs["IrisSection4Color"].default_value = (0.03, 0.015, 0.01, 1)

# ---------------- Searchers: yellow rain jackets / hi-vis vests, caps; Worker: yellow hi-vis jacket
yel = stripe_mat("HiVis_Yellow", (0.95, 0.82, 0.05), (0.75, 0.75, 0.72), [(1.05, 1.09), (1.25, 1.29)])
navy = mat("Searcher_Navy", (0.08, 0.1, 0.18), 0.6)
grey = mat("Searcher_Grey", (0.32, 0.33, 0.35), 0.6)
for n, cloth_col in (("SearchA", grey), ("SearchB", navy), ("SearchC", grey)):
    for ch in bpy.data.objects[n].children:
        if "casualsuit" in ch.name:
            # recolour only: keep their own (non-skin) trousers/shirt texture but darken
            tint_group(ch, (0.45, 0.48, 0.55))
for n in ("SearchB", "SearchC"):
    recolor_by_bone(next(c for c in bpy.data.objects[n].children if "casualsuit" in c.name), is_top, yel)
garment("Worker", "hivis", is_top, yel, offset=0.03, thick=0.004, zmin=0.58)

# ---------------- caps (Child Of head via bone parenting)
def cap(rig, col, name="cap", hard=False):
    R = bpy.data.objects[rig]; hb = R.data.bones["head"]
    body = bpy.data.objects[rig + ".body"]
    # crown of the head from the skin: highest body vertex
    top = max(eval_pts(body), key=lambda c: c.z)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, radius=1.0)
    c = bpy.context.object; c.name = rig + "_" + name
    bm = bmesh.new(); bm.from_mesh(c.data)
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z < -0.05], context='VERTS')
    bm.to_mesh(c.data); bm.free()
    c.scale = (0.105, 0.118, 0.085 if not hard else 0.095)
    c.location = (top.x, top.y + 0.004, top.z - 0.075)
    so = c.modifiers.new("t", 'SOLIDIFY'); so.thickness = 0.08
    c.data.materials.append(mat(name + "_" + rig, col, 0.5))
    # brim
    bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=1.0, depth=0.01)
    b = bpy.context.object; b.name = rig + "_" + name + "Brim"
    b.scale = (0.1, 0.08, 1.0) if not hard else (0.15, 0.17, 1)
    b.location = (top.x, top.y - (0.1 if not hard else 0.0), top.z - 0.07)
    b.rotation_euler = (math.radians(-8 if not hard else 0), 0, 0)
    b.data.materials.append(c.data.materials[0])
    bpy.context.view_layer.update()
    for o in (c, b): attach(o, rig, "head")
    return c
cap("SearchA", (0.18, 0.2, 0.24)); cap("SearchB", (0.9, 0.75, 0.05)); cap("SearchC", (0.15, 0.16, 0.2))
cap("Worker", (0.95, 0.95, 0.92), "hardhat", hard=True)
bpy.data.objects["Worker.short01"].hide_render = True; bpy.data.objects["Worker.short01"].hide_viewport = True

# scrunchie on the ponytail
hpts = eval_pts(hp)
back = min(hpts, key=lambda p: p.y) if False else None
# ponytail tie: the ponytail mesh's vertex cluster just behind the crown -> find the narrowest band near the back
ys = sorted(hpts, key=lambda p: -p.y)
c0 = max(hpts, key=lambda p: (p.y))  # MPFB faces -Y, so +Y is the back of the head
bpy.ops.mesh.primitive_torus_add(major_radius=0.026, minor_radius=0.011, major_segments=24, minor_segments=10)
t = bpy.context.object; t.name = "Girl_Scrunchie"; t.data.materials.append(mat("Asha_Scrunchie", (0.95, 0.3, 0.6), 0.5, sheen=0.5))
t.location = (c0.x, c0.y - 0.03, c0.z + 0.04); t.rotation_euler = (math.radians(90), 0, 0)
print("SCRUNCHIE at", tuple(round(x, 3) for x in t.location), "hair back pt", tuple(round(x, 3) for x in c0))
bpy.context.view_layer.update(); attach(t, "Girl", "head")

# eye fix (idempotent)
g = bpy.data.node_groups.get("EnhancedEye")
for ng in bpy.data.node_groups:
    if ng.name.startswith("EnhancedEye") and "CorneaTransparentMix" not in ng.nodes:
        _src = open("/home/user/Muhammed/blender/AshaDegree_v001/scripts/eye_fix.py").read().replace('bpy.data.node_groups["EnhancedEye"]', 'bpy.data.node_groups["%s"]' % ng.name)
        _NO_SAVE = True; exec(_src, {"bpy": bpy, "sys": sys, "_NO_SAVE": True})
for n, p in POS.items(): bpy.data.objects[n].location = p
G.scale = (0.9, 0.9, 0.9)
bpy.ops.wm.save_as_mainfile(filepath=out, compress=True)
