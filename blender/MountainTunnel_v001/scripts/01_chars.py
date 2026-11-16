"""MountainTunnel characters: MPFB2 rigs re-used from our own packages (Tsunami2004 locals, CaveRescue crowd), re-dressed.
blender -b --factory-startup --python 01_chars.py -- <repo_blender_dir> <out.blend>
Man = the hammer-and-chisel man (white top, cream dhoti; ages via the keyed 'Age' value: grey hair + beard)
Wife = red sari-like dress; V1..V3 = villagers in checked lungis and plain shirts."""
import sys, os, math
import bpy, bmesh
from mathutils import Vector, Matrix
a = sys.argv[sys.argv.index("--") + 1:]; ROOT, OUT = a[0], a[1]
for ob in list(bpy.data.objects): bpy.data.objects.remove(ob, do_unlink=True)
sc = bpy.context.scene
TS = os.path.join(ROOT, "Tsunami2004_v012/Tsunami2004_v012_60fps.blend")
CR = os.path.join(ROOT, "CaveRescue_v010/CaveRescue_v010_60fps.blend")
SB = os.path.join(ROOT, "ShoeBomber_v008/ShoeBomber_v008_60fps.blend")
SW = os.path.join(ROOT, "SpeakWithoutSight_v006/SpeakWithoutSight_v006_60fps.blend")
SRC = [(SB, "Sleeper1", "Man"), (SW, "Mother", "Wife"), (TS, "Fisher", "V1"), (TS, "TouristM_C08", "V2"), (CR, "Coach", "V3")]
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
        o.constraints.clear() if o is rig else None
    for o in [o for o in objs if o not in kids and o is not rig]: bpy.data.objects.remove(o, do_unlink=True)
    rig.name = new; rig.data.name = new
    for k in kids:
        k.name = new + "." + k.name.split(".", 1)[1]; k.data.name = k.name
        for m in k.modifiers:
            if m.type == 'ARMATURE': m.object = rig
    rig.parent = None
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

def PB(m):
    nt = m.node_tree; return nt, next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
def unlink(nt, sock):
    for l in list(sock.links): nt.links.remove(l)
def flat(m, rgb, rough=0.65):
    nt, P = PB(m); unlink(nt, P.inputs['Base Color']); P.inputs['Base Color'].default_value = (*rgb, 1)
    unlink(nt, P.inputs['Roughness']); P.inputs['Roughness'].default_value = rough
def two_tone(m, top, bottom, split, check=None, rough=0.7):
    """shirt colour above `split` (Generated Z of the suit mesh), the lower garment below; optional check pattern (c1, c2, scale)"""
    nt, P = PB(m); unlink(nt, P.inputs['Base Color']); unlink(nt, P.inputs['Roughness']); P.inputs['Roughness'].default_value = rough
    tc = nt.nodes.new('ShaderNodeTexCoord'); sep = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(tc.outputs['Generated'], sep.inputs[0])
    lt = nt.nodes.new('ShaderNodeMath'); lt.operation = 'GREATER_THAN'; lt.inputs[1].default_value = split; nt.links.new(sep.outputs['Z'], lt.inputs[0])
    mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.inputs['B'].default_value = (*top, 1)
    if check:
        c1, c2, scl = check
        ck = nt.nodes.new('ShaderNodeTexChecker'); ck.inputs['Scale'].default_value = scl
        ck.inputs['Color1'].default_value = (*c1, 1); ck.inputs['Color2'].default_value = (*c2, 1)
        nt.links.new(tc.outputs['Object'], ck.inputs['Vector']); nt.links.new(ck.outputs['Color'], mx.inputs['A'])
    else: mx.inputs['A'].default_value = (*bottom, 1)
    nt.links.new(lt.outputs[0], mx.inputs['Factor']); nt.links.new(mx.outputs['Result'], P.inputs['Base Color'])

def suit(n):
    return [k for k in RIGS[n].children if k.type == 'MESH' and "suit" in k.name]
WHITE, CREAM = (0.88, 0.88, 0.86), (0.80, 0.76, 0.64)
for k in suit("Man"):
    for m in k.data.materials:
        two_tone(m, WHITE, None, 0.50, check=((0.80, 0.84, 0.92), (0.55, 0.62, 0.78), 40.0)); unlink(m.node_tree, PB(m)[1].inputs['Normal'])     # the donor shirt's print lived in its normal map
        P_ = PB(m)[1]
        for l in list(m.node_tree.links):
            if l.to_node == P_ and l.to_socket.name in ('Alpha', 'Emission Color', 'Coat Weight'): m.node_tree.links.remove(l)
for k in suit("Wife"):          # blouse
    for m in k.data.materials: flat(m, (0.10, 0.42, 0.18), 0.6)
for k in RIGS["Wife"].children:  # long skirt: sari red with a gold hem band
    if "skirt" in k.name:
        for m in k.data.materials: two_tone(m, (0.62, 0.03, 0.05), (0.85, 0.6, 0.12), 0.12); unlink(m.node_tree, PB(m)[1].inputs['Normal'])
        # the donor skirt has two oval holes at the hips: an under-layer 8 mm inside fills them with the same red
        us = k.copy(); us.name = "Wife.underskirt"; sc.collection.objects.link(us)
        dp = us.modifiers.new("Inward", 'DISPLACE'); dp.strength = -0.008; dp.mid_level = 0.0
        while us.modifiers.find("Inward") > 0 and us.modifiers[us.modifiers.find("Inward") - 1].type in ('SUBSURF', 'SOLIDIFY'):
            i_ = us.modifiers.find("Inward"); us.modifiers.move(i_, i_ - 1)
        print("UNDERSKIRT", [md.type for md in us.modifiers])
DRESS = {"V1": ((0.15, 0.35, 0.75), ((0.08, 0.30, 0.12), (0.85, 0.85, 0.8), 18.0)),
         "V2": ((0.75, 0.30, 0.30), ((0.15, 0.15, 0.45), (0.85, 0.85, 0.8), 18.0)),
         "V3": ((0.90, 0.75, 0.25), ((0.10, 0.10, 0.10), (0.80, 0.80, 0.78), 18.0))}
for n, (top, ck) in DRESS.items():
    for k in suit(n):
        for m in k.data.materials: two_tone(m, top, None, 0.50, check=ck)
for r in RIGS.values():
    for k in r.children:
        if "shoes" in k.name:
            for m in k.data.materials: flat(m, (0.22, 0.13, 0.07), 0.5)     # brown sandals/leather

# ---- skin: warm medium-brown for every character (South Asian village), irises dark brown, hair near-black
TINT = {"Man": (0.78, 0.60, 0.46), "Wife": (0.82, 0.64, 0.50), "V1": (0.72, 0.55, 0.42), "V2": (0.70, 0.52, 0.40), "V3": (0.80, 0.62, 0.48)}
for n, r in RIGS.items():
    b = next(k for k in r.children if k.name.endswith(".body"))
    for m in b.data.materials:
        for gn in [nd for nd in m.node_tree.nodes if nd.type == 'GROUP']:
            g = gn.node_tree
            if g.users > 1: g = gn.node_tree = g.copy()
            bc = next((nd for nd in g.nodes if nd.type == 'BRIGHTCONTRAST'), None)
            P = next((nd for nd in g.nodes if nd.type == 'BSDF_PRINCIPLED'), None)
            if not (bc and P) or "SkinTint" in g.nodes: continue
            mx = g.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.name = "SkinTint"
            mx.inputs['Factor'].default_value = 1.0; mx.inputs['B'].default_value = (*TINT[n], 1)
            g.links.new(bc.outputs['Color'], mx.inputs['A']); g.links.new(mx.outputs['Result'], P.inputs['Base Color'])
            print("TINT", n, g.name)
    eye = next(k for k in r.children if k.name.endswith("high-poly"))
    for m in eye.data.materials:
        for gn in [nd for nd in m.node_tree.nodes if nd.type == 'GROUP']:
            if 'IrisMajorColor' in gn.inputs:
                gn.inputs['IrisMajorColor'].default_value = (0.20, 0.10, 0.04, 1); gn.inputs['IrisMinorColor'].default_value = (0.09, 0.045, 0.02, 1)
    for k in r.children:
        if any(h in k.name for h in ("short0", "long0")):
            for m in k.data.materials:
                nt, P_ = PB(m); l = P_.inputs['Base Color'].links
                if l and "HairTint" not in nt.nodes:
                    mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.name = "HairTint"
                    mx.inputs['Factor'].default_value = 1.0; mx.inputs['B'].default_value = (0.25, 0.2, 0.18, 1)
                    nt.links.new(l[0].from_socket, mx.inputs['A']); nt.links.new(mx.outputs['Result'], P_.inputs['Base Color'])

# ---- eye fix on every EnhancedEye group not yet fixed
for g in [g for g in bpy.data.node_groups if g.name.startswith("EnhancedEye")]:
    if not any(nd.name.startswith("CorneaTransparentMix") for nd in g.nodes):
        print("EYEFIX on", g.name)
        src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "eye_fix.py")).read().replace('bpy.data.node_groups["EnhancedEye"]', 'bpy.data.node_groups[%r]' % g.name)
        _NO_SAVE = True; exec(src)
for r in RIGS.values():
    for k in r.children:
        if k.name.endswith(("eyebrow001", "eyelashes01")):
            for m in k.data.materials:
                for nd in m.node_tree.nodes:
                    if nd.type == 'TEX_IMAGE' and nd.image:
                        al = nd.image.pixels[3::4]; print("CARD", k.name, nd.image.name, "alpha min", round(min(al), 3))

# V3's donor cards lost their alpha (black bands, LESSONS s3): take V1's intact brow/lash materials
for suf in ("eyebrow001", "eyelashes01"):
    good = next(k for k in RIGS["V1"].children if k.name.endswith(suf)).data.materials[0]
    for k in RIGS["V3"].children:
        if k.name.endswith(suf): k.data.materials[0] = good

# ---- open the elbow IK limit (MPFB rest elbow ~46 deg)
for r in RIGS.values():
    for s in "LR":
        lo = r.pose.bones["lowerarm01." + s]; lo.use_ik_limit_x = True; lo.ik_min_x = math.radians(-40); lo.ik_max_x = math.radians(100)

# ---- ageing for the Man: hair goes grey/white with the keyed Age value; beard grows (scale keyed in 03_shots)
man = RIGS["Man"]
hair = next(k for k in man.children if "short0" in k.name)
for m in hair.data.materials:
    nt, P = PB(m)
    l = P.inputs['Base Color'].links
    srcs = l[0].from_socket if l else None
    age = nt.nodes.new('ShaderNodeValue'); age.name = "Age"; age.outputs[0].default_value = 0.0
    mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.name = "AgeMix"
    if srcs: nt.links.new(srcs, mx.inputs['A'])
    else: mx.inputs['A'].default_value = P.inputs['Base Color'].default_value
    mx.inputs['B'].default_value = (0.95, 0.95, 0.93, 1)
    nt.links.new(age.outputs[0], mx.inputs['Factor']); nt.links.new(mx.outputs['Result'], P.inputs['Base Color'])
    print("AGE hair material", m.name)
for k in man.children:      # brows also whiten
    if k.name.endswith("eyebrow001"):
        for m in k.data.materials:
            nt, P = PB(m); l = P.inputs['Base Color'].links
            if l:
                mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.name = "AgeMix"
                nt.links.new(l[0].from_socket, mx.inputs['A']); mx.inputs['B'].default_value = (0.8, 0.8, 0.78, 1)
                age = nt.nodes.new('ShaderNodeValue'); age.name = "Age"
                nt.links.new(age.outputs[0], mx.inputs['Factor']); nt.links.new(mx.outputs['Result'], P.inputs['Base Color'])

body = next(k for k in man.children if k.name.endswith(".body"))
# the body's real shape includes its shape keys: read evaluated coordinates with the modifiers off (vertex order kept)
_sv = [(m, m.show_viewport) for m in body.modifiers]
for m, _ in _sv: m.show_viewport = False
bpy.context.view_layer.update(); _dg = bpy.context.evaluated_depsgraph_get()
_em = body.evaluated_get(_dg).to_mesh(); ECO = [v.co.copy() for v in _em.vertices]; body.evaluated_get(_dg).to_mesh_clear()
for m, sv in _sv: m.show_viewport = sv
print("SHAPEKEYS", bool(body.data.shape_keys), "verts", len(ECO), len(body.data.vertices))
gi = body.vertex_groups["head"].index
eye_z = (man.data.bones["eye.L"].head_local.z + man.data.bones["eye.R"].head_local.z) / 2
eye_y = man.data.bones["eye.L"].head_local.y
hv = [v for v in body.data.vertices if any(g.group == gi and g.weight > 0.5 for g in v.groups)]
cx = sum(ECO[v.index].x for v in hv) / len(hv)
teeth = next(k for k in man.children if "teeth" in k.name)
tz = [v.co.z for v in teeth.data.vertices]; ty = [v.co.y for v in teeth.data.vertices]
mouth_z = (min(tz) + max(tz)) / 2; mouth_y = min(ty)
print("HEAD eye_z", round(eye_z, 3), "eye_y", round(eye_y, 3), "mouth_z", round(mouth_z, 3), "mouth_y", round(mouth_y, 3))

# clean head target (no MPFB helper / joint geometry, which sits inside the head and caught the shrinkwrap)
HELP = {g.index for g in body.vertex_groups if g.name.startswith(("helper", "joint")) or g.name in ("HelperGeometry", "JointCubes")}
def clean(v): return not any(g.group in HELP and g.weight > 0.0 for g in v.groups)
CLEAN = {v.index for v in body.data.vertices if clean(v)}
HEADV = {v.index for v in hv if v.index in CLEAN}
bmt = bmesh.new(); bmt.from_mesh(body.data); bmt.verts.ensure_lookup_table()
for v in bmt.verts: v.co = ECO[v.index]
bmesh.ops.delete(bmt, geom=[v for v in bmt.verts if v.index not in CLEAN or v.co.z < eye_z - 0.20], context='VERTS')
tme = bpy.data.meshes.new("Man.headtgt"); bmt.to_mesh(tme); bmt.free()
tgt = bpy.data.objects.new("Man.headtgt", tme); sc.collection.objects.link(tgt)
def bake(o):
    bpy.context.view_layer.update(); dg = bpy.context.evaluated_depsgraph_get()
    m2 = bpy.data.meshes.new_from_object(o.evaluated_get(dg)); old = o.data; o.modifiers.clear(); o.data = m2; m2.name = old.name
    bpy.data.meshes.remove(old)

# real hair: the donor's short hair, with the fringe trimmed back above the brows (it covered one eye); greys with Age
hair = next(k for k in man.children if "short0" in k.name)
hair.hide_render = hair.hide_viewport = False
_sv = [(m, m.show_viewport) for m in hair.modifiers]
for m, _ in _sv: m.show_viewport = False
bpy.context.view_layer.update(); _dg = bpy.context.evaluated_depsgraph_get()
_hm = hair.evaluated_get(_dg).to_mesh(); HCO = [v.co.copy() for v in _hm.vertices]; hair.evaluated_get(_dg).to_mesh_clear()
for m, sv in _sv: m.show_viewport = sv
brow_z = eye_z + 0.040
# comb the fringe up and back (rotate those strands about a lateral axis through the crown) instead of cutting them:
# a cut left a saw-tooth edge that read badly once the hair turned white
piv = Vector((cx, eye_y + 0.06, eye_z + 0.02)); moved = 0
deltas = {}
for i, p_ in enumerate(HCO):
    if p_.y > eye_y + 0.05: continue
    need = (brow_z + 0.022) - p_.z
    if need <= 0: continue
    w = min(1.0, need / 0.06)
    ang = math.radians(10 + 38 * w)
    q = p_ - piv; R = Matrix.Rotation(-ang, 3, 'X') if False else Matrix.Rotation(ang, 3, 'X')
    r_ = R @ q
    if r_.z < q.z: r_ = Matrix.Rotation(-ang, 3, 'X') @ q        # pick the direction that lifts the strand
    deltas[i] = (piv + r_) - p_; moved += 1
for i, dlt in deltas.items(): hair.data.vertices[i].co += dlt
if hair.data.shape_keys:
    for kb in hair.data.shape_keys.key_blocks:
        for i, dlt in deltas.items(): kb.data[i].co += dlt
print("HAIR combed back verts", moved, "of", len(HCO))
for m in body.data.materials:
    for gn in [nd for nd in m.node_tree.nodes if nd.type == 'GROUP']:
        g = gn.node_tree; st = g.nodes.get("SkinTint")
        if not st or "ScalpGrey" in g.nodes: continue
        P_ = next(nd for nd in g.nodes if nd.type == 'BSDF_PRINCIPLED')
        tc = g.nodes.new('ShaderNodeTexCoord'); sp = g.nodes.new('ShaderNodeSeparateXYZ'); g.links.new(tc.outputs['Object'], sp.inputs[0])
        def cmp(sock, op, v):
            n_ = g.nodes.new('ShaderNodeMath'); n_.operation = op; n_.inputs[1].default_value = v; g.links.new(sock, n_.inputs[0]); return n_.outputs[0]
        a1 = cmp(sp.outputs['Z'], 'GREATER_THAN', eye_z + 0.075)
        a2 = cmp(sp.outputs['Z'], 'GREATER_THAN', eye_z + 0.025); b2 = cmp(sp.outputs['Y'], 'GREATER_THAN', eye_y + 0.05)
        mul = g.nodes.new('ShaderNodeMath'); mul.operation = 'MULTIPLY'; g.links.new(a2, mul.inputs[0]); g.links.new(b2, mul.inputs[1])
        mx_ = g.nodes.new('ShaderNodeMath'); mx_.operation = 'MAXIMUM'; g.links.new(a1, mx_.inputs[0]); g.links.new(mul.outputs[0], mx_.inputs[1])
        age = g.nodes.new('ShaderNodeValue'); age.name = "Age"
        f_ = g.nodes.new('ShaderNodeMath'); f_.operation = 'MULTIPLY'; g.links.new(mx_.outputs[0], f_.inputs[0]); g.links.new(age.outputs[0], f_.inputs[1])
        mix = g.nodes.new('ShaderNodeMix'); mix.data_type = 'RGBA'; mix.name = "ScalpGrey"; mix.inputs['B'].default_value = (0.72, 0.70, 0.68, 1)
        g.links.new(st.outputs['Result'], mix.inputs['A']); g.links.new(f_.outputs[0], mix.inputs['Factor']); g.links.new(mix.outputs['Result'], P_.inputs['Base Color'])
        print("SCALP grey added in", g.name)
for k in suit("Man"):
    so = k.modifiers.new("OuterShell", 'SOLIDIFY'); so.thickness = 0.006; so.offset = 1.0
    subs = [i for i, md in enumerate(k.modifiers) if md.type == 'SUBSURF']
    if subs: k.modifiers.move(len(k.modifiers) - 1, subs[0])
    print("SHELL", k.name, [md.type for md in k.modifiers])

def in_beard(p):
    dx = abs(p.x - cx); dz = p.z - mouth_z
    if p.y > eye_y + 0.07: return False
    if dz < -0.085: return False                                   # under the chin, not down the throat
    if dx < 0.021 and abs(dz) < 0.0055: return False               # the lips show (a fully covered mouth read as a surgical mask)
    top = 0.021 + max(0.0, dx - 0.030) / 0.045 * 0.036             # one smooth upper edge: moustache -> cheeks -> sideburns
    return dz < top
bm = bmesh.new(); bm.from_mesh(body.data); bm.verts.ensure_lookup_table()
for v in bm.verts: v.co = ECO[v.index]
keep = [f for f in bm.faces if all(v.index in CLEAN and abs(v.co.x - cx) < 0.085 and in_beard(v.co) for v in f.verts)]
bm2 = bmesh.new(); vm = {}
for f in keep:
    vs = []
    for v in f.verts:
        if v.index not in vm: vm[v.index] = bm2.verts.new(v.co)
        vs.append(vm[v.index])
    bm2.faces.new(vs)
me = bpy.data.meshes.new("Man.beard"); bm2.to_mesh(me); bm.free(); bm2.free()
# soft edge: alpha fades over the outer 1.4 cm of the beard (distance to its boundary along the surface)
import heapq
bmb = bmesh.new(); bmb.from_mesh(me); bmb.verts.ensure_lookup_table()
dist = {v.index: (0.0 if any(e.is_boundary for e in v.link_edges) else 9.0) for v in bmb.verts}
pq = [(0.0, i) for i, d_ in dist.items() if d_ == 0.0]; heapq.heapify(pq)
while pq:
    d_, i = heapq.heappop(pq)
    if d_ > dist[i]: continue
    for e in bmb.verts[i].link_edges:
        j = e.other_vert(bmb.verts[i]).index; nd_ = d_ + e.calc_length()
        if nd_ < dist[j]: dist[j] = nd_; heapq.heappush(pq, (nd_, j))
bmb.free()
fa = me.attributes.new("edge_fade", 'FLOAT', 'POINT')
for i in range(len(me.vertices)): fa.data[i].value = min(1.0, dist[i] / 0.014)
beard = bpy.data.objects.new("Man.beard", me); sc.collection.objects.link(beard)
for p_ in me.polygons: p_.use_smooth = True
mb = bpy.data.materials.new("M_Beard"); mb.use_nodes = True; nt = mb.node_tree; P = nt.nodes["Principled BSDF"]
P.inputs['Base Color'].default_value = (0.70, 0.70, 0.68, 1); P.inputs['Roughness'].default_value = 0.85
tc = nt.nodes.new('ShaderNodeTexCoord'); w = nt.nodes.new('ShaderNodeTexNoise'); w.inputs['Scale'].default_value = 300.0
bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = 0.25
nt.links.new(tc.outputs['Object'], w.inputs['Vector']); nt.links.new(w.outputs['Fac'], bp.inputs['Height']); nt.links.new(bp.outputs['Normal'], P.inputs['Normal'])
at = nt.nodes.new('ShaderNodeAttribute'); at.attribute_name = "edge_fade"; nt.links.new(at.outputs['Fac'], P.inputs['Alpha'])
me.materials.append(mb)
sw = beard.modifiers.new("Fit", 'SHRINKWRAP'); sw.target = tgt; sw.wrap_method = 'NEAREST_SURFACEPOINT'; sw.offset = 0.003
sm = beard.modifiers.new("Smooth", 'SMOOTH'); sm.factor = 0.8; sm.iterations = 14
bt = bpy.data.textures.new("T_BeardFluff", 'CLOUDS'); bt.noise_scale = 0.012
fl = beard.modifiers.new("Fluff", 'DISPLACE'); fl.texture = bt; fl.strength = 0.007; fl.mid_level = 0.3
bake(beard)
sol = beard.modifiers.new("Solid", 'SOLIDIFY'); sol.thickness = 0.006; sol.offset = 1.0
beard.modifiers.new("Sub", 'SUBSURF').levels = 2
Mw = beard.matrix_world.copy(); beard.parent = man; beard.parent_type = 'BONE'; beard.parent_bone = "head"
bpy.context.view_layer.update(); beard.matrix_world = Mw
print("BEARD faces", len(beard.data.polygons))
bpy.data.objects.remove(tgt, do_unlink=True)

for n, r in RIGS.items():
    print("RIG", n, tuple(round(d, 2) for d in r.dimensions), "head z", round(r.data.bones["head"].head_local.z, 3))
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print("CHARS_OK")
