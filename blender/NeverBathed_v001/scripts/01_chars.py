"""NeverBathed characters: MPFB2 rigs re-used from our own EscapeArtist_v010 package, re-dressed.
blender -b --factory-startup --python 01_chars.py -- <repo_blender_dir> <out.blend>
AmouY = the hermit young (dark hair, short dark beard), AmouO = the hermit old (grey hair, long grey beard, sooty skin),
V1, V2 = villagers (clean, coloured shirts). Same clothes colours on AmouY and AmouO (continuity)."""
import sys, os, math, random
import bpy, bmesh
from mathutils import Vector, Matrix
a = sys.argv[sys.argv.index("--") + 1:]; ROOT, OUT = a[0], a[1]
for ob in list(bpy.data.objects): bpy.data.objects.remove(ob, do_unlink=True)
sc = bpy.context.scene
EA = os.path.join(ROOT, "EscapeArtist_v010/EscapeArtist_v010_60fps.blend")
SRC = [(EA, "Prisoner", "AmouY"), (EA, "PrisonerOld", "AmouO"), (EA, "Father", "V1"), (EA, "Guard2", "V2")]
RIGS = {}
for path, src, new in SRC:
    with bpy.data.libraries.load(path, link=False) as (df, dt):
        dt.objects = [n for n in df.objects if n == src or n.startswith(src + ".")]
    objs = [o for o in dt.objects if o is not None]
    rig = next(o for o in objs if o.type == 'ARMATURE')
    kids = [o for o in objs if o.parent == rig]
    for o in [rig] + kids:
        sc.collection.objects.link(o); o.animation_data_clear()
        if o.type == 'MESH' and o.data.shape_keys: o.data.shape_keys.animation_data_clear()
        o.hide_render = o.hide_viewport = False; o.hide_set(False)
    for o in [o for o in objs if o not in kids and o is not rig]: bpy.data.objects.remove(o, do_unlink=True)
    rig.name = new; rig.data.name = new
    for k in kids: k.name = new + "." + k.name.split(".", 1)[1]; k.data.name = k.name
    rig.location = (0, 0, 0); rig.rotation_euler = (0, 0, 0); rig.scale = (1, 1, 1)
    for pb in rig.pose.bones:
        pb.location = (0, 0, 0); pb.rotation_mode = 'QUATERNION'; pb.rotation_quaternion = (1, 0, 0, 0); pb.scale = (1, 1, 1)
    RIGS[new] = rig
    print("CHAR", new, "from", src, [k.name for k in kids])
bpy.ops.outliner.orphans_purge(do_recursive=True)

for r in RIGS.values():
    for k in r.children:
        if k.type != 'MESH': continue
        for i, m in enumerate(k.data.materials):
            if m and m.users > 1: k.data.materials[i] = m.copy()

def PB(m): return m.node_tree, next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
def flat_colour(m, rgb, rough=0.6):
    nt, P = PB(m)
    for l in list(P.inputs['Base Color'].links): nt.links.remove(l)
    P.inputs['Base Color'].default_value = (*rgb, 1); P.inputs['Roughness'].default_value = rough
def tint(m, rgb, fac=1.0):
    """multiply the existing base colour (texture) by rgb"""
    nt, P = PB(m)
    src = P.inputs['Base Color'].links[0].from_socket if P.inputs['Base Color'].links else None
    mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs['Factor'].default_value = fac
    if src: nt.links.new(src, mx.inputs['A'])
    else: mx.inputs['A'].default_value = P.inputs['Base Color'].default_value
    mx.inputs['B'].default_value = (*rgb, 1); nt.links.new(mx.outputs['Result'], P.inputs['Base Color'])
def cloth_colour(m, rgb, rough=0.75, weave=True):
    """solid clothing colour with a soft fabric noise so it never reads as a skin-tight one-colour suit"""
    nt, P = PB(m)
    for l in list(P.inputs['Base Color'].links): nt.links.remove(l)
    tc = nt.nodes.new('ShaderNodeTexCoord'); no = nt.nodes.new('ShaderNodeTexNoise'); no.inputs['Scale'].default_value = 18.0
    ramp = nt.nodes.new('ShaderNodeMix'); ramp.data_type = 'RGBA'
    ramp.inputs['A'].default_value = (*[c * 0.78 for c in rgb], 1); ramp.inputs['B'].default_value = (*[min(1, c * 1.12) for c in rgb], 1)
    nt.links.new(tc.outputs['Object'], no.inputs['Vector']); nt.links.new(no.outputs['Fac'], ramp.inputs['Factor'])
    nt.links.new(ramp.outputs['Result'], P.inputs['Base Color']); P.inputs['Roughness'].default_value = rough
    for l in list(P.inputs['Roughness'].links): nt.links.remove(l)
def soot_skin(m, amount=0.55, scale=6.0, BASE_T=(0.80, 0.68, 0.56, 1)):
    """stylised (clean, matte) soot-brown patches over the skin texture: reads as 'never washed' without grime detail.
    MPFB skin is a node group: edit the Principled inside the material's own group tree."""
    grp = next(n for n in m.node_tree.nodes if n.type == 'GROUP')
    grp.node_tree = grp.node_tree.copy(); nt = grp.node_tree
    P = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    src = P.inputs['Base Color'].links[0].from_socket
    tc = nt.nodes.new('ShaderNodeTexCoord'); no = nt.nodes.new('ShaderNodeTexNoise'); no.inputs['Scale'].default_value = scale
    no.inputs['Detail'].default_value = 3.0
    cr = nt.nodes.new('ShaderNodeValToRGB'); cr.color_ramp.elements[0].position = 0.38; cr.color_ramp.elements[1].position = 0.62
    mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'
    mx.inputs['B'].default_value = (0.36, 0.25, 0.16, 1)
    mul = nt.nodes.new('ShaderNodeMath'); mul.operation = 'MULTIPLY'; mul.inputs[1].default_value = amount
    nt.links.new(tc.outputs['Object'], no.inputs['Vector']); nt.links.new(no.outputs['Fac'], cr.inputs['Fac'])
    nt.links.new(cr.outputs['Color'], mul.inputs[0]); nt.links.new(mul.outputs[0], mx.inputs['Factor'])
    nt.links.new(src, mx.inputs['A'])
    base = nt.nodes.new('ShaderNodeMix'); base.data_type = 'RGBA'; base.blend_type = 'MULTIPLY'; base.inputs['Factor'].default_value = 1.0
    base.inputs['B'].default_value = BASE_T        # overall sun-darkened, dusty tone
    nt.links.new(mx.outputs['Result'], base.inputs['A']); nt.links.new(base.outputs['Result'], P.inputs['Base Color'])

def part(n, tag): return next(k for k in RIGS[n].children if k.type == 'MESH' and k.name.endswith(tag))
def part_has(n, s): return [k for k in RIGS[n].children if k.type == 'MESH' and s in k.name]

# ---- clothes: the hermit keeps one outfit all film (olive-grey tunic overall, dark brown shoes)
for n in ("AmouY", "AmouO"):
    for k in part_has(n, "worksuit"):
        for m in k.data.materials: cloth_colour(m, (0.10, 0.12, 0.05), 0.85)
    for k in part_has(n, "shoes"):
        for m in k.data.materials: flat_colour(m, (0.07, 0.045, 0.03), 0.6)
for k in part_has("V1", "casualsuit"):
    for m in k.data.materials: cloth_colour(m, (0.03, 0.09, 0.30), 0.7)        # blue shirt
for k in part_has("V2", "casualsuit"):
    for m in k.data.materials: cloth_colour(m, (0.35, 0.05, 0.03), 0.7)        # brick-red shirt

# ---- skin: young hermit lightly dusty, old hermit sooty
soot_skin(part("AmouY", ".body").data.materials[0], amount=0.25, scale=5.0)
soot_skin(part("AmouO", ".body").data.materials[0], amount=1.0, scale=11.0, BASE_T=(0.55, 0.42, 0.31, 1))
# ---- hair colours
for k in part_has("AmouY", "short"):
    for m in k.data.materials: tint(m, (0.25, 0.2, 0.17))
for k in part_has("AmouO", "short"):
    for m in k.data.materials:
        nt, P = PB(m); src = P.inputs['Base Color'].links[0].from_socket if P.inputs['Base Color'].links else None
        flat_colour(m, (0.45, 0.43, 0.40), 0.55)
for k in part_has("AmouO", "eyebrow"):
    for m in k.data.materials:
        nt, P = PB(m)
        if P.inputs['Base Color'].links: tint(m, (2.2, 2.2, 2.2))

# ---- eye fix (EnhancedEye cornea -> transparent mix)
g = bpy.data.node_groups.get("EnhancedEye")
if g and not any(nd.name.startswith("CorneaTransparentMix") for nd in g.nodes):
    _NO_SAVE = True
    exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "eye_fix.py")).read())
GE = part("V2", "high-poly").data.materials[0]
for n in RIGS: part(n, "high-poly").data.materials[0] = GE

# ---- open the elbow IK limit (MPFB rest elbow ~46 deg)
for r in RIGS.values():
    for s in "LR":
        lo = r.pose.bones["lowerarm01." + s]; lo.use_ik_limit_x = True; lo.ik_min_x = math.radians(-40); lo.ik_max_x = math.radians(100)

def parent_to_bone(o, r, bone):
    Mw = o.matrix_world.copy(); o.parent = r; o.parent_type = 'BONE'; o.parent_bone = bone
    bpy.context.view_layer.update(); o.matrix_world = Mw

# ---- beards: hair curves grown from the jaw / chin / upper-lip skin, parented to the head bone
def beard(n, length, lip_len, color, density=1.0, seed=1, melanin=0.0, rs=1.0):
    r = RIGS[n]; body = part(n, ".body"); me = body.data
    gi = body.vertex_groups["head"].index
    jaw = body.vertex_groups.get("jaw"); ji = jaw.index if jaw else -1
    BN = r.data.bones
    eye_z = (BN["eye.L"].head_local.z + BN["eye.R"].head_local.z) / 2
    hc = BN["head"].head_local
    mouth_z = eye_z - 0.075
    pts = []
    vs = me.vertices
    ys = [v.co.y for v in vs if any(g.group == gi and g.weight > 0.5 for g in v.groups)]
    front = min(ys)
    for v in vs:
        w = max([g.weight for g in v.groups if g.group in (gi, ji)] or [0])
        if w < 0.5: continue
        c = v.co; nrm = v.normal
        dz = c.z - eye_z
        if c.y > hc.y + 0.01: continue                       # front half of the head only
        if dz > -0.05: continue                             # below the cheekbones
        if c.z < eye_z - 0.165: continue                     # not down the neck
        side = abs(c.x - hc.x)
        if dz > -0.06 and side < 0.045: continue             # keep the nose / under-eye clean
        is_lip = (-0.095 < dz < -0.06) and side < 0.03 and c.y < front + 0.03
        lip_zone = (-0.11 < dz < -0.075) and side < 0.028     # the mouth itself stays clear
        if lip_zone and not is_lip: continue
        if nrm.y > 0.3 and c.z > eye_z - 0.13 and side > 0.075: continue   # back of the jaw, behind the ear line
        pts.append((c.copy(), nrm.copy(), is_lip))
    rnd = random.Random(seed)
    strands = []
    for c, nrm, lip in pts:
        k = 3 if not lip else 2
        for _ in range(int(k * density + rnd.random())):
            j = Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-1, 1))) * 0.003
            p0 = c + j - nrm * 0.002
            L = (lip_len if lip else length) * rnd.uniform(0.75, 1.15)
            down = Vector((0, 0, -1)); out = nrm.normalized()
            if lip:
                out = Vector((math.copysign(1, c.x - hc.x) * 0.8, -0.4, 0)).normalized()
            seg = []
            p = p0.copy(); d = (out * 0.45 + down * 0.55).normalized()
            if d.z > -0.35: d.z = -0.35; d.normalize()
            for i in range(6):
                seg.append(p.copy())
                d = (d + down * (0.45 if not lip else 0.6) + Vector((rnd.uniform(-.08, .08), rnd.uniform(-.06, .03), 0))).normalized()
                if lip: pass
                else: d = (d - out * (0.12 if i > 1 else 0.0)).normalized()
                p = p + d * (L / 5)
            strands.append(seg)
    cv = bpy.data.hair_curves.new(n + ".beard")
    cv.add_curves([6] * len(strands))
    pos = [q for s in strands for q in s]
    cv.attributes["position"].data.foreach_set("vector", [x for q in pos for x in q])
    rad = cv.attributes.get("radius") or cv.attributes.new("radius", 'FLOAT', 'POINT')
    rr = []
    for s in strands: rr += [x * rs for x in (0.0011, 0.001, 0.0009, 0.0008, 0.0006, 0.0003)]
    rad.data.foreach_set("value", rr)
    ob = bpy.data.objects.new(n + ".beard", cv); sc.collection.objects.link(ob)
    m = bpy.data.materials.new("M_Beard_" + n); m.use_nodes = True; nt = m.node_tree
    for nd in list(nt.nodes):
        if nd.type == 'BSDF_PRINCIPLED': nt.nodes.remove(nd)
    hb = nt.nodes.new('ShaderNodeBsdfHairPrincipled')
    if melanin > 0:
        hb.parametrization = 'MELANIN'; hb.inputs['Melanin'].default_value = melanin; hb.inputs['Melanin Redness'].default_value = 0.3
    else:
        hb.parametrization = 'COLOR'; hb.inputs['Color'].default_value = (*color, 1)
    hb.inputs['Roughness'].default_value = 0.45
    hb.inputs['Radial Roughness'].default_value = 0.6
    nt.links.new(hb.outputs[0], nt.nodes['Material Output'].inputs['Surface'])
    cv.materials.append(m)
    parent_to_bone(ob, r, "head")
    print("BEARD", n, len(strands), "strands")
    return ob

beard("AmouY", 0.014, 0.010, (0.06, 0.045, 0.035), density=3.0, seed=3, melanin=0.92, rs=0.35)
beard("AmouO", 0.16, 0.045, (0.30, 0.28, 0.25), density=1.8, seed=7)

# ---- a knit cap for V2 (Child Of the head bone; hair hidden, no fringe)
def head_metrics(r):
    body = next(k for k in r.children if k.name.endswith(".body"))
    gi = body.vertex_groups["head"].index
    pts = [v.co.copy() for v in body.data.vertices if any(gg.group == gi and gg.weight > 0.5 for gg in v.groups)]
    xs = [p.x for p in pts]; ys = [p.y for p in pts]; zs = [p.z for p in pts]
    eye_z = (r.data.bones["eye.L"].head_local.z + r.data.bones["eye.R"].head_local.z) / 2
    return Vector(((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, 0)), max(xs) - min(xs), max(ys) - min(ys), max(zs), eye_z
def make_cap(n, rgb, rim_off):
    r = RIGS[n]
    for k in r.children:
        if k.type == 'MESH' and "short0" in k.name: k.hide_render = True; k.hide_viewport = True
    body = next(k for k in r.children if k.name.endswith(".body"))
    c, wx, wy, top, eye_z = head_metrics(r); rim = eye_z + rim_off
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=48, v_segments=32, radius=1.0)
    rx, ry, rz = wx / 2 * 1.15, wy / 2 * 1.15, (top - rim) * 1.3
    for v in bm.verts: v.co = Vector((v.co.x * rx, v.co.y * ry, v.co.z * rz))
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z < -0.002], context='VERTS')
    me = bpy.data.meshes.new(n + ".cap"); bm.to_mesh(me); bm.free()
    cap = bpy.data.objects.new(n + ".cap", me); sc.collection.objects.link(cap); cap.location = (c.x, c.y, rim)
    m = bpy.data.materials.new("M_Cap_" + n); m.use_nodes = True; m.node_tree.nodes["Principled BSDF"].inputs['Base Color'].default_value = (*rgb, 1)
    m.node_tree.nodes["Principled BSDF"].inputs['Roughness'].default_value = 0.85; me.materials.append(m)
    for p_ in me.polygons: p_.use_smooth = True
    sw = cap.modifiers.new("Fit", 'SHRINKWRAP'); sw.target = body; sw.wrap_method = 'NEAREST_SURFACEPOINT'; sw.offset = 0.007
    cap.modifiers.new("Solid", 'SOLIDIFY').thickness = 0.006; cap.modifiers.new("Sub", 'SUBSURF').levels = 1
    bpy.context.view_layer.update(); parent_to_bone(cap, r, "head")
make_cap("V2", (0.92, 0.9, 0.84), 0.05)          # white skullcap

for n, r in RIGS.items():
    print("RIG", n, tuple(round(d, 2) for d in r.dimensions), "head z", round(r.data.bones["head"].head_local.z, 3))
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print("CHARS_OK")
