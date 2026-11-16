"""Cast for B23 HandlessWarrior, appended from our finished packages (MPFB characters that already carry IK controls and
hand limits; MakeHuman's asset server is down). Eye fix applied to every EnhancedEye group, elbow IK limit opened,
clothes recoloured in solid/woven non-skin colours (also removes the MakeHuman logo prints on the tees).
The warrior's hands are removed with a Mask modifier (vertex groups wrist + fingers) and the stumps are closed by a
cloth bandage (no wound geometry at all).
blender -b --factory-startup --python 01_chars.py -- <out.blend>"""
import sys, os, math
import bpy, bmesh
from mathutils import Vector, Matrix
HERE = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(HERE, "00_lib.py")).read())
OUT = sys.argv[sys.argv.index("--") + 1]
ROOT = os.path.join(HERE, "..", "..")
SHOE = os.path.join(ROOT, "ShoeBomber_v008", "ShoeBomber_v008_60fps.blend")
TSU = os.path.join(ROOT, "Tsunami2004_v012", "Tsunami2004_v012_60fps.blend")
WW1B = os.path.join(ROOT, "WW1Assassination_v007", "WW1Assassination_v007_60fps.blend")
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.fps = 60; sc.render.resolution_x = 1080; sc.render.resolution_y = 1920
CC = coll("Cast")

def char(blend, src, new, skip=(), extras=()):
    with bpy.data.libraries.load(blend, link=False) as (s, d):
        kids = [n for n in s.objects if n.startswith(src + ".") or n.startswith(src + "_")]
    kids = [k for k in kids if not any(x in k for x in skip)]
    with bpy.data.libraries.load(blend, link=False) as (s, d):
        d.objects = [src] + kids + list(extras)
    objs = list(d.objects); rig = objs[0]
    for o in objs:
        CC.objects.link(o)
        o.animation_data_clear()
        if o.type == 'MESH' and o.data.shape_keys: o.data.shape_keys.animation_data_clear()
        o.hide_render = False; o.hide_viewport = False
        if o is not rig and o.name.startswith(src): o.name = new + "." + o.name[len(src) + 1:].split(".00")[0]
    rig.name = new; rig.data.name = new
    rig.location = (0, 0, 0); rig.rotation_euler = (0, 0, 0); rig.scale = (1, 1, 1)
    for pb in rig.pose.bones:
        pb.location = (0, 0, 0); pb.rotation_quaternion = (1, 0, 0, 0); pb.rotation_euler = (0, 0, 0); pb.scale = (1, 1, 1)
    for s in "LR":   # open the elbow IK limit (MPFB rests at ~46 deg; min 0 kept arms in an A-pose)
        pb = rig.pose.bones["lowerarm01." + s]; pb.use_ik_limit_x = True; pb.ik_min_x = -0.75; pb.ik_max_x = 2.53
    for o in objs:
        if o.type == 'MESH':
            for m in o.modifiers:
                if m.type == 'ARMATURE': m.object = rig
            if o.parent is None or o.parent.type == 'ARMATURE': o.parent = rig
    # drop the source film's visibility keys etc. on extras
    return rig, objs

def bone_parent(o, rig, bone):
    mw = o.matrix_world.copy()
    o.parent = rig; o.parent_type = 'BONE'; o.parent_bone = bone
    bpy.context.view_layer.update(); o.matrix_world = mw

def mesh_kids(rig, key):
    return [c for c in rig.children if c.type == 'MESH' and key in c.name]

def woven(name, top, band1, band2, legs, waist_z, period=0.22, rough=0.75, zr=(0.0, 1.8)):
    """cloth: solid top colour with two thin woven bands every `period` m, solid trouser colour below waist_z (mesh space)"""
    m = bpy.data.materials.get(name)
    if m: return m
    m = bpy.data.materials.new(name); n, l = nodes_of(m); n.clear()
    out = n.new('ShaderNodeOutputMaterial'); bs = n.new('ShaderNodeBsdfPrincipled'); l.new(bs.outputs[0], out.inputs[0])
    tc = n.new('ShaderNodeTexCoord'); sp0 = n.new('ShaderNodeSeparateXYZ'); l.new(tc.outputs['Generated'], sp0.inputs[0])
    rz = n.new('ShaderNodeMath'); rz.operation = 'MULTIPLY_ADD'; rz.inputs[1].default_value = zr[1] - zr[0]; rz.inputs[2].default_value = zr[0]
    l.new(sp0.outputs[2], rz.inputs[0])
    class _S: pass
    sp = _S(); sp.outputs = [None, None, rz.outputs[0]]   # rest-pose z (Generated = undeformed), not the posed z
    dv = n.new('ShaderNodeMath'); dv.operation = 'DIVIDE'; dv.inputs[1].default_value = period; l.new(sp.outputs[2], dv.inputs[0])
    fr = n.new('ShaderNodeMath'); fr.operation = 'FRACT'; l.new(dv.outputs[0], fr.inputs[0])
    rp = n.new('ShaderNodeValToRGB'); rp.color_ramp.interpolation = 'CONSTANT'; el = rp.color_ramp.elements
    el[0].position = 0.0; el[0].color = (*top, 1); el[1].position = 0.80; el[1].color = (*band1, 1)
    e = el.new(0.86); e.color = (*band2, 1); e = el.new(0.90); e.color = (*band1, 1); e = el.new(0.96); e.color = (*top, 1)
    l.new(fr.outputs[0], rp.inputs[0])
    gt = n.new('ShaderNodeMath'); gt.operation = 'GREATER_THAN'; gt.inputs[1].default_value = waist_z; l.new(sp.outputs[2], gt.inputs[0])
    mx = n.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.inputs['B'].default_value = (*legs, 1)
    l.new(gt.outputs[0], mx.inputs['Factor']); mx.inputs['A'].default_value = (*legs, 1); l.new(rp.outputs[0], mx.inputs['B'])
    l.new(mx.outputs['Result'], bs.inputs['Base Color'])
    bs.inputs['Roughness'].default_value = rough
    nz = n.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 300; bp = n.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = 0.1
    l.new(tc.outputs['Object'], nz.inputs['Vector']); l.new(nz.outputs['Fac'], bp.inputs['Height']); l.new(bp.outputs[0], bs.inputs['Normal'])
    m.diffuse_color = (*top, 1)
    return m

def zrange(rig, key):
    m = mesh_kids(rig, key)[0]; zs = [v.co.z for v in m.data.vertices]
    return (min(zs), max(zs))

def waist(rig):
    return rig.data.bones["pelvis.L"].head_local.z + 0.02 if "pelvis.L" in rig.data.bones else rig.data.bones["root"].head_local.z + 0.02

def dress(rig, key, mat):
    for ch in mesh_kids(rig, key):
        for i in range(len(ch.data.materials)): ch.data.materials[i] = mat
        if not ch.data.materials: ch.data.materials.append(mat)

def _tint_tree(nt, rgb):
    for nd in list(nt.nodes):
        if nd.type == 'GROUP' and nd.node_tree:
            nd.node_tree = nd.node_tree.copy()
            if _tint_tree(nd.node_tree, rgb): return True
    for nd in list(nt.nodes):
        if nd.type == 'TEX_IMAGE' and nd.image and ("diffuse" in nd.image.name.lower() or "diff" in nd.image.name.lower() or "albedo" in nd.image.name.lower() or "skin" in nd.image.name.lower()):
            for lk in list(nd.outputs['Color'].links):
                mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'
                mx.inputs['Factor'].default_value = 1.0; mx.inputs['B'].default_value = (*rgb, 1)
                nt.links.new(nd.outputs['Color'], mx.inputs['A']); nt.links.new(mx.outputs['Result'], lk.to_socket)
            return True
    return False

def tint_tex(rig, key, rgb):
    """multiply the diffuse texture of a mesh's material by rgb (skin tone); descends into node groups"""
    for ch in mesh_kids(rig, key):
        for i, m in enumerate(ch.data.materials):
            if m is None: continue
            m = m.copy(); ch.data.materials[i] = m
            print("TINT", ch.name, _tint_tree(m.node_tree, rgb))

def flatcol(name, rgb, rough=0.6, metal=0.0):
    return flat(name, rgb, rough=rough, metal=metal)

def height(rig):
    body = mesh_kids(rig, "body")[0]
    dg = bpy.context.evaluated_depsgraph_get(); e = body.evaluated_get(dg)
    zs = [(body.matrix_world @ v.co).z for v in e.data.vertices]
    return max(zs) - min(zs)

# ======================================================================== the warrior
W, wobjs = char(SHOE, "Sleeper1", "Warrior")
dress(W, "casualsuit06", woven("WarriorTunic", (0.42, 0.05, 0.03), (0.06, 0.04, 0.03), (0.85, 0.62, 0.2), (0.16, 0.1, 0.06), waist(W), period=0.30, zr=zrange(W, "casualsuit06")))
tint_tex(W, "body", (0.78, 0.58, 0.42))         # warm tan skin
for ch in mesh_kids(W, "shoes"):
    for i in range(len(ch.data.materials)): ch.data.materials[i] = flatcol("Moccasin", (0.22, 0.12, 0.06), rough=0.8)
for ch in mesh_kids(W, "short"):
    tint_tex(W, ch.name.split(".")[-1], (0.25, 0.2, 0.18))   # near-black hair

for hc in mesh_kids(W, "short"):
    hb = W.data.bones["head"]; hz = hb.head_local.z
    vs = hc.data.vertices; ys = [v.co.y for v in vs]; ymin = min(ys)
    brow = hz + 0.085
    bm = bmesh.new(); bm.from_mesh(hc.data)
    kill = [f for f in bm.faces if f.calc_center_median().y < ymin + 0.06 and f.calc_center_median().z < brow + 0.035]
    bmesh.ops.delete(bm, geom=kill, context='FACES'); bm.to_mesh(hc.data); bm.free()
    print("FRINGE trimmed", len(kill), "brow", round(brow, 3), "ymin", round(ymin, 3))
# hands off: mask the wrist + finger vertices (dominant bone weight)
body = mesh_kids(W, "body")[0]
gi = {g.index: g.name for g in body.vertex_groups}
bones = {b.name for b in W.data.bones}
hand_v = []
for v in body.data.vertices:
    gs = [g for g in v.groups if gi.get(g.group) in bones and g.weight > 0]
    if not gs: continue
    dom = gi[max(gs, key=lambda g: g.weight).group]
    if dom.startswith("wrist") or dom.startswith("finger") or dom.startswith("metacarpal"):
        hand_v.append(v.index)
vg = body.vertex_groups.new(name="HANDS_OFF"); vg.add(hand_v, 1.0, 'REPLACE')
mk = body.modifiers.new("HandsOff", 'MASK'); mk.vertex_group = "HANDS_OFF"; mk.invert_vertex_group = True
body.modifiers.move(len(body.modifiers) - 1, 0)
print("HANDS_OFF verts", len(hand_v))

# stump bandages: measure the cut ring (body vertices of the lowerarm that touch a masked vertex) in rest pose
hv = set(hand_v)
adj = {}
for e in body.data.edges:
    a, b = e.vertices
    if (a in hv) != (b in hv):
        keep = b if a in hv else a; adj[keep] = True
MW = body.matrix_world
BANDAGE = flat("Bandage", (0.93, 0.89, 0.8), rough=0.85)
BANDAGE_RED = flat("BandageStain", (0.62, 0.12, 0.1), rough=0.8)
for s, sx in (("L", 1), ("R", -1)):
    ring = [MW @ body.data.vertices[i].co for i in adj if (body.data.vertices[i].co.x > 0) == (sx > 0)]
    c = sum(ring, Vector()) / len(ring)
    wb = W.data.bones["wrist." + s]; la = W.data.bones["lowerarm02." + s]
    ax = (la.tail_local - la.head_local).normalized()              # forearm axis (towards the hand)
    rad = max(((p - c) - ax * (p - c).dot(ax)).length for p in ring)
    # bandage: closed tube from 7 cm up the forearm to 2.2 cm past the cut, rounded end
    bm = bmesh.new()
    segs, rings_ = 20, []
    prof = [(-0.07, 1.06), (-0.05, 1.16), (-0.025, 1.14), (0.0, 1.12), (0.012, 1.0), (0.020, 0.75), (0.025, 0.4), (0.027, 0.0)]
    # forearm is slightly flattened: measure the cross-section shape per angle at the cut
    up = Vector((0, 0, 1)); u = (up - ax * up.dot(ax)).normalized(); w = ax.cross(u)
    def rad_at(t):
        best = 0.0
        for p in ring:
            d = (p - c) - ax * (p - c).dot(ax)
            best = max(best, d.length)
        return best
    for (t, k) in prof:
        rr = []
        for j in range(segs):
            a = 2 * math.pi * j / segs
            # per-angle radius from the ring (nearest ring direction)
            dirv = u * math.cos(a) + w * math.sin(a)
            rj = max((((p - c) - ax * (p - c).dot(ax)).dot(dirv)) for p in ring)
            rj = max(rj, rad * 0.55)
            r_ = (rj + 0.004) * k if k > 0 else 0.0
            rr.append(bm.verts.new(c + ax * t + dirv * r_))
        rings_.append(rr)
    for i in range(len(rings_) - 1):
        for j in range(segs):
            bm.faces.new([rings_[i][j], rings_[i][(j + 1) % segs], rings_[i + 1][(j + 1) % segs], rings_[i + 1][j]])
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    for f in bm.faces: f.smooth = True
    o = mesh_obj("Warrior_Bandage." + s, bm, [BANDAGE, BANDAGE], CC)
    # a faint stain ring near the end (clean, small, no wound)
    for p in o.data.polygons:
        cz = (sum((o.data.vertices[v].co for v in p.vertices), Vector()) / len(p.vertices) - c).dot(ax)
        if 0.004 < cz < 0.016: p.material_index = 1
    # wrap ridges: subtle bands
    sm = o.modifiers.new("Sub", 'SUBSURF'); sm.levels = 1; sm.render_levels = 1
    bpy.context.view_layer.update(); bone_parent(o, W, "lowerarm02." + s)
    W["cut_" + s] = list(c); W["cut_ax_" + s] = list(ax); W["cut_rad_" + s] = rad
    print("BANDAGE", s, tuple(round(x, 3) for x in c), round(rad, 3))
# keep wrists straight relative to the forearm (the IK copy-rotation would twist the stump)
for s in "LR":
    for cn in W.pose.bones["wrist." + s].constraints:
        if cn.type == 'COPY_ROTATION': cn.mute = True

# ======================================================================== villagers (woven robes)
ROBES = [((0.9, 0.86, 0.76), (0.05, 0.05, 0.06), (0.15, 0.3, 0.7), (0.25, 0.17, 0.1)),
         ((0.8, 0.45, 0.1), (0.1, 0.06, 0.04), (0.92, 0.88, 0.78), (0.3, 0.12, 0.08)),
         ((0.12, 0.38, 0.3), (0.92, 0.88, 0.78), (0.05, 0.05, 0.06), (0.2, 0.15, 0.1)),
         ((0.9, 0.86, 0.76), (0.45, 0.06, 0.06), (0.05, 0.05, 0.06), (0.12, 0.12, 0.2))]
VILL = [("LocalM_C10", "Elder", "casualsuit05"), ("LocalW_C03", "VillagerW", "casualsuit02"),
        ("Fisher_C06", "VillagerM1", "casualsuit03"), ("TouristM_C08", "VillagerM2", "casualsuit02")]
for i, (src, new, suit) in enumerate(VILL):
    r, _ = char(TSU, src, new)
    dress(r, suit, woven("Robe%d" % i, *ROBES[i], waist(r), period=0.18 + 0.03 * i, zr=zrange(r, suit)))
    tint_tex(r, "body", (0.9, 0.74, 0.6))
    for ch in mesh_kids(r, "shoes"):
        for k in range(len(ch.data.materials)): ch.data.materials[k] = flatcol("Moccasin", (0.22, 0.12, 0.06), rough=0.8)

# ======================================================================== soldiers (steel helmet, breastplate, red doublet)
DOUBLET = flat("Doublet", (0.45, 0.07, 0.06), rough=0.65)
DOUBLET2 = flat("DoubletBlue", (0.08, 0.12, 0.35), rough=0.65)
HOSE = flat("Hose", (0.12, 0.1, 0.09), rough=0.7)
BOOT = flat("Boot", (0.1, 0.07, 0.05), rough=0.5)
STEEL = flat("Steel", (0.72, 0.75, 0.8), rough=0.28, metal=1.0)
BRASS = flat("Brass", (0.85, 0.62, 0.25), rough=0.3, metal=1.0)
def head_top(rig):
    body = mesh_kids(rig, "body")[0]
    dg = bpy.context.evaluated_depsgraph_get(); e = body.evaluated_get(dg)
    vs = [body.matrix_world @ v.co for v in e.data.vertices]
    return max(vs, key=lambda v: v.z)
def steelify(o):
    for i in range(len(o.data.materials)):
        m = o.data.materials[i]
        if m is None: continue
        m = m.copy(); o.data.materials[i] = m
        bs = next((n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)
        if bs:
            for lk in list(bs.inputs['Base Color'].links): m.node_tree.links.remove(lk)
            bs.inputs['Base Color'].default_value = (0.8, 0.82, 0.86, 1); bs.inputs['Metallic'].default_value = 1.0
            for lk in list(bs.inputs['Roughness'].links): m.node_tree.links.remove(lk)
            bs.inputs['Roughness'].default_value = 0.25
SOL = [(WW1B, "Officer", "SoldierA", DOUBLET, "morion", ("OfficerCap",)),
       (WW1B, "NerveB", "SoldierB", DOUBLET2, "morion", ("fedora",)),
       (WW1B, "Gunman", "Second", DOUBLET, "morion", ()),
       (WW1B, "NerveA", "SoldierC", DOUBLET, "morion", ())]
for blend, src, new, dbl, helm, skip in SOL:
    r, objs = char(blend, src, new, skip=skip)
    dress(r, "suit", dbl)
    for ch in mesh_kids(r, "shoes"):
        for k in range(len(ch.data.materials)): ch.data.materials[k] = BOOT
    bpy.context.view_layer.update()
    top = head_top(r)
    hb = r.pose.bones["head"]; hm = r.matrix_world @ hb.matrix
    h = glb_asset(helm, CC, target_size=0.36 if helm == "morion" else 0.36, axis=1)
    h.name = new + "_Helmet"; steelify(h)
    if new == "Second":
        for i in range(len(h.data.materials)): h.data.materials[i] = BRASS
    r[ "helm_top"] = list(top)
    bpy.context.view_layer.update()
    mn, mx = bbox_world([h])
    print("HELMET", new, helm, tuple(round(d, 3) for d in h.dimensions), "top", tuple(round(x, 3) for x in top))
    # brim sits ~5 cm above the brows: helmet bowl bottom at top - 0.11
    h.location = (top.x, top.y + 0.0, top.z - (0.10 if helm == 'morion' else 0.16))
    bpy.context.view_layer.update(); bone_parent(h, r, "head")
    # cuirass: a copy of the jacket's torso (same skin weights, so it deforms with the body), pushed out 1.2 cm, solidified, steel
    jk = mesh_kids(r, "suit")[0]
    bp = jk.copy(); bp.data = jk.data.copy(); CC.objects.link(bp); bp.name = new + "_Plate"
    gi_ = {g.index: g.name for g in bp.vertex_groups}; bn_ = {b.name for b in r.data.bones}
    zt = r.data.bones["neck01"].head_local.z - 0.06; zb = waist(r) + 0.03
    bm = bmesh.new(); bm.from_mesh(bp.data); dl = bm.verts.layers.deform.active
    kill = []
    for v in bm.verts:
        gs = [(gi_[k], w) for k, w in v[dl].items() if gi_.get(k) in bn_] if dl else []
        dom = max(gs, key=lambda t: t[1])[0] if gs else ""
        if not (zb < v.co.z < zt) or not (dom.startswith("spine") or dom.startswith("breast") or dom.startswith("pelvis") or dom == "root"):
            kill.append(v)
    bmesh.ops.delete(bm, geom=kill, context='VERTS'); bm.to_mesh(bp.data); bm.free()
    for i in range(len(bp.data.materials)): bp.data.materials[i] = STEEL if new != "Second" else BRASS
    smm = bp.modifiers.new("Smooth", 'SMOOTH'); smm.factor = 1.0; smm.iterations = 12
    dp = bp.modifiers.new("Push", 'DISPLACE'); dp.strength = 0.012; dp.mid_level = 0.0
    so = bp.modifiers.new("Thick", 'SOLIDIFY'); so.thickness = 0.006; so.offset = 1.0
    for _ in range(len(bp.modifiers) - 2): pass
    # keep armature modifier first
    am = next((m for m in bp.modifiers if m.type == 'ARMATURE'), None)
    if am: bp.modifiers.move(list(bp.modifiers).index(am), 0)
    print("PLATE", new, len(bp.data.vertices))
    continue
    print("PLATE", new, tuple(round(d, 3) for d in bp.dimensions))

# ======================================================================== eye fix on every EnhancedEye group
for g in bpy.data.node_groups:
    if not g.name.startswith("EnhancedEye") or "CorneaTransparentMix" in g.nodes: continue
    P = next((n for n in g.nodes if n.type == "BSDF_PRINCIPLED"), None); OUTN = next((n for n in g.nodes if n.type == "GROUP_OUTPUT"), None)
    if P is None or OUTN is None: continue
    tl = [l for l in g.links if l.to_node == P and l.to_socket.name == "Transmission Weight"]
    src = tl[0].from_socket if tl else None
    for l in tl: g.links.remove(l)
    P.inputs["Transmission Weight"].default_value = 0.0
    ol = [l for l in g.links if l.from_node == P and l.to_node == OUTN]
    if not ol: continue
    out_sock = ol[0].to_socket; g.links.remove(ol[0])
    tr = g.nodes.new("ShaderNodeBsdfTransparent"); mx = g.nodes.new("ShaderNodeMixShader"); mx.name = "CorneaTransparentMix"
    if src: g.links.new(src, mx.inputs[0])
    else: mx.inputs[0].default_value = 0.0
    g.links.new(P.outputs[0], mx.inputs[1]); g.links.new(tr.outputs[0], mx.inputs[2]); g.links.new(mx.outputs[0], out_sock)
    print("EYEFIX", g.name)

x = 0
for o in bpy.data.objects:
    if o.type == 'ARMATURE':
        o.location = (x, 0, 0); x += 1.2
        print("CHAR", o.name, round(height(o), 3), [c.name for c in o.children])
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("CHARS_DONE")
