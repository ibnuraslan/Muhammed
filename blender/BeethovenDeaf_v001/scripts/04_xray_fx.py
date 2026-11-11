"""X-ray dive: skull + ear cross-section inside the head, ghosted body, cyan studio backdrop, vibration rings, glows.
blender -b anim.blend --python 04_xray_fx.py -- <assets_dir> <out.blend>"""
import sys, os, math, random
import bpy
from mathutils import Vector, Matrix
HERE = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(HERE, "..", "..", "pipeline", "anim_lib.py")).read())
a = sys.argv[sys.argv.index("--") + 1:]; AS, OUT = a[0], a[1]
sc = bpy.context.scene; RND = random.Random(9)
def T(s): return 1 + round(s * 60)
BEAT = [T(t) for t in (0.0, 3.9, 5.2, 8.6, 11.9, 16.4, 18.4, 20.1)]; END = 1590
C = bpy.data.objects["Composer"]; BN = C.data.bones; PB = C.pose.bones
C_XR = bpy.data.collections["XRay"]; C_FX = bpy.data.collections["FX"]
HEAD_REST = BN["head"].matrix_local.copy()
def link(o, coll=C_XR):
    for c_ in o.users_collection: c_.objects.unlink(o)
    coll.objects.link(o)
def to_head(o):
    """keep o's current (rest-space) placement and make it ride the head bone"""
    c = o.constraints.new('CHILD_OF'); c.target = C; c.subtarget = "head"; c.inverse_matrix = (C.matrix_world @ HEAD_REST).inverted()
def head_world(f):
    ev(f); return C.matrix_world @ PB["head"].matrix @ HEAD_REST.inverted()
def key_vis(o, spans):
    o.hide_render = True; o.keyframe_insert("hide_render", frame=1)
    for f0, f1 in spans:
        o.hide_render = False; o.keyframe_insert("hide_render", frame=f0)
        o.hide_render = True; o.keyframe_insert("hide_render", frame=f1)
    o.hide_viewport = False
def emit_mat(name, col, strength):
    m = bpy.data.materials.new(name); m.use_nodes = True; n = m.node_tree.nodes; n.clear()
    o = n.new('ShaderNodeOutputMaterial'); e = n.new('ShaderNodeEmission'); e.inputs['Color'].default_value = (*col, 1); e.inputs['Strength'].default_value = strength
    e.name = "Emit"; m.node_tree.links.new(e.outputs[0], o.inputs['Surface']); return m
def key_val(sock, keys):
    for f, v in keys: sock.default_value = v; sock.keyframe_insert("default_value", frame=f)
def imp(name):
    before = set(bpy.data.objects); bpy.ops.import_scene.gltf(filepath=os.path.join(AS, "glb", name + ".glb"))
    return [o for o in bpy.data.objects if o not in before]
def flatten(new, keep=None):
    bpy.context.view_layer.update()
    ms = [o for o in new if o.type == 'MESH' and (keep is None or o.name in keep)]
    for o in ms: M = o.matrix_world.copy(); o.parent = None; o.matrix_world = M
    for o in new:
        if o not in ms: bpy.data.objects.remove(o)
    for o in bpy.context.selected_objects: o.select_set(False)
    for o in ms: o.select_set(True)
    bpy.context.view_layer.objects.active = ms[0]; bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    return ms
def vbox(objs):
    pts = [o.matrix_world @ v.co for o in objs for v in o.data.vertices]
    return Vector([min(p[i] for p in pts) for i in range(3)]), Vector([max(p[i] for p in pts) for i in range(3)])

# ---------------------------------------------------------------- head measurements (rest space)
body = bpy.data.objects["Composer.body"]
hv = [v.co for v in body.data.vertices if v.co.z > 1.45]
HX = max(abs(v.x) for v in hv if 1.55 < v.z < 1.62); HYB = max(v.y for v in hv); HZT = max(v.z for v in hv)
print("HEAD", HX, HYB, HZT)
# ---------------------------------------------------------------- skull (Yu, CC-BY) fitted inside the head
sk = flatten(imp("skull_a"))[0]; sk.name = "XRay_Skull"; link(sk)
mn, mx = vbox([sk]); s = (2 * HX - 0.022) / (mx.x - mn.x)
sk.data.transform(Matrix.Translation(-Vector(((mn.x + mx.x) / 2, mx.y, mx.z)))); sk.data.transform(Matrix.Scale(s, 4))
sk.location = (0, HYB - 0.012, HZT - 0.008); bpy.context.view_layer.update()
mn, mx = vbox([sk]); print("SKULL", tuple(mn), tuple(mx))
to_head(sk)
skm = sk.data.materials[0]; nt = skm.node_tree; Pk = next(x for x in nt.nodes if x.type == 'BSDF_PRINCIPLED')
Pk.inputs['Roughness'].default_value = 0.45; Pk.inputs['Subsurface Weight'].default_value = 0.15
# glow wave: emission where distance(jaw point) < keyed radius, soft edge
JAWP = Vector((0, -0.11, 1.50))
jawE = bpy.data.objects.new("XRay_JawPoint", None); jawE.location = JAWP; sc.collection.objects.link(jawE); link(jawE); to_head(jawE)
tc = nt.nodes.new('ShaderNodeTexCoord'); tc.object = jawE
ln = nt.nodes.new('ShaderNodeVectorMath'); ln.operation = 'LENGTH'; nt.links.new(tc.outputs['Object'], ln.inputs[0])
rad = nt.nodes.new('ShaderNodeValue'); rad.name = "GlowRadius"
sub = nt.nodes.new('ShaderNodeMath'); sub.operation = 'SUBTRACT'; nt.links.new(rad.outputs[0], sub.inputs[0]); nt.links.new(ln.outputs['Value'], sub.inputs[1])
mr = nt.nodes.new('ShaderNodeMapRange'); mr.inputs['From Min'].default_value = -0.01; mr.inputs['From Max'].default_value = 0.03
nt.links.new(sub.outputs[0], mr.inputs['Value'])
ring = nt.nodes.new('ShaderNodeMapRange'); ring.inputs['From Min'].default_value = -0.03; ring.inputs['From Max'].default_value = 0.0; ring.clamp = True
nt.links.new(sub.outputs[0], ring.inputs['Value'])   # bright leading edge
gs = nt.nodes.new('ShaderNodeValue'); gs.name = "GlowStrength"
edge = nt.nodes.new('ShaderNodeMath'); edge.operation = 'PINGPONG'; edge.inputs[1].default_value = 0.5; nt.links.new(ring.outputs['Result'], edge.inputs[0])
fillw = nt.nodes.new('ShaderNodeMath'); fillw.operation = 'MULTIPLY'; fillw.inputs[1].default_value = 0.35; nt.links.new(mr.outputs['Result'], fillw.inputs[0])
add = nt.nodes.new('ShaderNodeMath'); add.operation = 'MULTIPLY_ADD'; add.inputs[1].default_value = 3.5   # bright travelling wavefront + soft fill behind it
nt.links.new(edge.outputs[0], add.inputs[0]); nt.links.new(fillw.outputs[0], add.inputs[2])
mul = nt.nodes.new('ShaderNodeMath'); mul.operation = 'MULTIPLY'; nt.links.new(add.outputs[0], mul.inputs[0]); nt.links.new(gs.outputs[0], mul.inputs[1])
Pk.inputs['Emission Color'].default_value = (0.0, 0.42, 1.0, 1); nt.links.new(mul.outputs[0], Pk.inputs['Emission Strength'])
key_val(rad.outputs[0], [(1, 0.0), (BEAT[4] - 30, 0.0), (BEAT[4] + 90, 0.13), (BEAT[4] + 200, 0.3)])
key_val(gs.outputs[0], [(1, 0.0), (BEAT[3] + 20, 0.0), (BEAT[3] + 60, 0.6), (BEAT[4], 0.6), (BEAT[4] + 120, 0.8), (BEAT[5], 1.0), (BEAT[6] + 20, 0.4), (BEAT[6] + 90, 0.0)])
# bone translucency so the inner ear reads through the side of the skull (keyed up for the cross-section)
alpha = nt.nodes.new('ShaderNodeValue'); alpha.name = "SkullAlpha"
tr = nt.nodes.new('ShaderNodeBsdfTransparent'); mix = nt.nodes.new('ShaderNodeMixShader')
outk = next(x for x in nt.nodes if x.type == 'OUTPUT_MATERIAL')
src = outk.inputs['Surface'].links[0].from_socket
nt.links.new(alpha.outputs[0], mix.inputs['Fac']); nt.links.new(src, mix.inputs[1]); nt.links.new(tr.outputs[0], mix.inputs[2]); nt.links.new(mix.outputs[0], outk.inputs['Surface'])
key_val(alpha.outputs[0], [(1, 0.0), (BEAT[4] + 150, 0.0), (BEAT[4] + 210, 0.62), (BEAT[6] + 25, 0.62), (BEAT[6] + 52, 1.0)])

# ---------------------------------------------------------------- inner ear (osuecampus, CC-BY): eardrum, ossicles, labyrinth+cochlea, nerves; ~2.5x life size
new = imp("inner_ear2")
keep = None
ms = flatten(new)
for o in list(ms):
    if o.name.startswith("Cube") or o.name in ("Object_10", "Object_4"): bpy.data.objects.remove(o); ms.remove(o)
NAMES = {"Object_8": "Ear_Eardrum", "Object_14": "Ear_Labyrinth", "Object_18": "Ear_Stapes", "Object_20": "Ear_Incus", "Object_22": "Ear_Malleus",
         "Object_12": "Ear_Nerve1", "Object_16": "Ear_Nerve2", "Object_6": "Ear_Nerve3"}
EAR = {}
for o in ms: o.name = NAMES.get(o.name, o.name); EAR[o.name] = o; link(o)
lab = EAR["Ear_Labyrinth"]; dr = EAR["Ear_Eardrum"]
lmn, lmx = vbox([lab]); es = 0.05 / max(lmx - lmn)
dmn, dmx = vbox([dr]); dc = (dmn + dmx) / 2
EARDRUM_REST = Vector((HX - 0.012, -0.004, 1.556))
Mx = Matrix.Translation(EARDRUM_REST) @ Matrix.Diagonal((-es, es, es, 1)) @ Matrix.Translation(-dc)
for o in ms:
    o.data.transform(Mx); o.data.flip_normals(); o.data.update(); to_head(o)
lmn, lmx = (Vector([min(v.co[i] for v in lab.data.vertices) for i in range(3)]), Vector([max(v.co[i] for v in lab.data.vertices) for i in range(3)])); LAB_C = (lmn + lmx) / 2; print("LAB", tuple(lmn), tuple(lmx), "DRUM", tuple(EARDRUM_REST))
# cochlea = the anterior-inferior coil of the labyrinth
COCH = Vector((LAB_C.x, lmn.y + 0.3 * (lmx.y - lmn.y), lmn.z + 0.3 * (lmx.z - lmn.z)))
sc["coch"] = list(COCH); sc["drum"] = list(EARDRUM_REST); sc["lab_c"] = list(LAB_C)
# clean explainer materials
def pbr(name, col, rough=0.4, ss=0.2):
    m = bpy.data.materials.new(name); m.use_nodes = True; P = m.node_tree.nodes["Principled BSDF"]
    P.inputs['Base Color'].default_value = (*col, 1); P.inputs['Roughness'].default_value = rough; P.inputs['Subsurface Weight'].default_value = ss; return m
mb = pbr("M_Ossicle", (0.86, 0.78, 0.62), 0.35)
for k in ("Ear_Stapes", "Ear_Incus", "Ear_Malleus"): EAR[k].data.materials.clear(); EAR[k].data.materials.append(mb)
mn_ = pbr("M_Nerve", (0.9, 0.75, 0.35), 0.4)
for k in ("Ear_Nerve1", "Ear_Nerve2", "Ear_Nerve3"):
    if k in EAR: EAR[k].data.materials.clear(); EAR[k].data.materials.append(mn_)
# labyrinth: pale bone-pink, lights up cyan -> warm white from the cochlea base along the coil
lm = pbr("M_Cochlea", (0.85, 0.7, 0.66), 0.35, 0.3); lab.data.materials.clear(); lab.data.materials.append(lm)
nt = lm.node_tree; P = nt.nodes["Principled BSDF"]
cE = bpy.data.objects.new("XRay_CochleaBase", None); cE.location = COCH; sc.collection.objects.link(cE); link(cE); to_head(cE)
tc = nt.nodes.new('ShaderNodeTexCoord'); tc.object = cE
ln = nt.nodes.new('ShaderNodeVectorMath'); ln.operation = 'LENGTH'; nt.links.new(tc.outputs['Object'], ln.inputs[0])
cr = nt.nodes.new('ShaderNodeValue'); cr.name = "CochleaRadius"
sb = nt.nodes.new('ShaderNodeMath'); sb.operation = 'SUBTRACT'; nt.links.new(cr.outputs[0], sb.inputs[0]); nt.links.new(ln.outputs['Value'], sb.inputs[1])
mr = nt.nodes.new('ShaderNodeMapRange'); mr.inputs['From Min'].default_value = -0.004; mr.inputs['From Max'].default_value = 0.004; nt.links.new(sb.outputs[0], mr.inputs['Value'])
cs = nt.nodes.new('ShaderNodeValue'); cs.name = "CochleaStrength"
mu = nt.nodes.new('ShaderNodeMath'); mu.operation = 'MULTIPLY'; nt.links.new(mr.outputs['Result'], mu.inputs[0]); nt.links.new(cs.outputs[0], mu.inputs[1])
ccol = nt.nodes.new('ShaderNodeMix'); ccol.data_type = 'RGBA'; ccol.name = "CochleaColour"
ccol.inputs['A'].default_value = (0.3, 0.85, 1.0, 1); ccol.inputs['B'].default_value = (1.0, 0.85, 0.6, 1)
nt.links.new(ccol.outputs['Result'], P.inputs['Emission Color']); nt.links.new(mu.outputs[0], P.inputs['Emission Strength'])
key_val(cr.outputs[0], [(1, 0.0), (BEAT[6] - 10, 0.0), (BEAT[6] + 45, 0.05)])
key_val(cs.outputs[0], [(1, 0.0), (BEAT[4] + 60, 0.0), (BEAT[4] + 80, 0.6), (BEAT[6] - 10, 0.6), (BEAT[6] + 30, 3.0), (BEAT[6] + 75, 2.0), (BEAT[7] + 20, 0.0)])
key_val(ccol.inputs['Factor'], [(1, 0.0), (BEAT[6] + 20, 0.0), (BEAT[6] + 60, 0.85)])
# the eardrum: dull, grey, scarred and torn (ragged hole), no glow
dm = bpy.data.materials.new("M_EardrumTorn"); dm.use_nodes = True; nt = dm.node_tree; P = nt.nodes["Principled BSDF"]
P.inputs['Base Color'].default_value = (0.42, 0.38, 0.36, 1); P.inputs['Roughness'].default_value = 0.85; P.inputs['Subsurface Weight'].default_value = 0.1
tE = bpy.data.objects.new("XRay_TearPoint", None); tE.location = EARDRUM_REST + Vector((0, 0.004, -0.002)); sc.collection.objects.link(tE); link(tE); to_head(tE)
tc = nt.nodes.new('ShaderNodeTexCoord'); tc.object = tE
nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 400; nz.inputs['Detail'].default_value = 6
nt.links.new(tc.outputs['Object'], nz.inputs['Vector'])
ln = nt.nodes.new('ShaderNodeVectorMath'); ln.operation = 'LENGTH'; nt.links.new(tc.outputs['Object'], ln.inputs[0])
ad = nt.nodes.new('ShaderNodeMath'); ad.operation = 'MULTIPLY_ADD'; ad.inputs[1].default_value = 0.004
nt.links.new(nz.outputs['Fac'], ad.inputs[0]); nt.links.new(ln.outputs['Value'], ad.inputs[2])
hole = nt.nodes.new('ShaderNodeMath'); hole.operation = 'GREATER_THAN'; hole.inputs[1].default_value = 0.0052; nt.links.new(ad.outputs[0], hole.inputs[0])
scar = nt.nodes.new('ShaderNodeMapRange'); scar.inputs['From Min'].default_value = 0.004; scar.inputs['From Max'].default_value = 0.009
nt.links.new(ad.outputs[0], scar.inputs['Value'])
scol = nt.nodes.new('ShaderNodeMix'); scol.data_type = 'RGBA'; scol.inputs['A'].default_value = (0.18, 0.12, 0.11, 1); scol.inputs['B'].default_value = (0.42, 0.38, 0.36, 1)
nt.links.new(scar.outputs['Result'], scol.inputs['Factor']); nt.links.new(scol.outputs['Result'], P.inputs['Base Color'])
tr = nt.nodes.new('ShaderNodeBsdfTransparent'); mx_ = nt.nodes.new('ShaderNodeMixShader'); o_ = nt.nodes["Material Output"]
nt.links.new(hole.outputs[0], mx_.inputs['Fac']); nt.links.new(tr.outputs[0], mx_.inputs[1]); nt.links.new(P.outputs[0], mx_.inputs[2]); nt.links.new(mx_.outputs[0], o_.inputs['Surface'])
dr.data.materials.clear(); dr.data.materials.append(dm)
# ear canal cut-away (half pipe from the outer ear in to the drum), skin-pink, cut face toward the front
can_m = pbr("M_EarCanal", (0.72, 0.42, 0.38), 0.5, 0.4)
segs, rings_ = 24, 14
verts, faces = [], []
for i in range(rings_ + 1):
    u = i / rings_; x = EARDRUM_REST.x + 0.002 + u * 0.034; zc = EARDRUM_REST.z + 0.004 * math.sin(u * math.pi); r = 0.0055 + 0.002 * u
    for j in range(segs + 1):
        th = math.pi * (0.1 + 1.0 * j / segs)   # half pipe: open toward -Y (the face side)
        verts.append((x, EARDRUM_REST.y + 0.002 + r * math.cos(th + math.pi / 2) * -1, zc + r * math.sin(th + math.pi / 2)))
for i in range(rings_):
    for j in range(segs):
        k = i * (segs + 1) + j; faces.append((k, k + 1, k + segs + 2, k + segs + 1))
me = bpy.data.meshes.new("Ear_Canal"); me.from_pydata(verts, [], faces); can = bpy.data.objects.new("Ear_Canal", me); C_XR.objects.link(can)
can.modifiers.new("sol", 'SOLIDIFY').thickness = 0.0025; can.modifiers.new("sub", 'SUBSURF').levels = 1
can.data.materials.append(can_m); to_head(can)
EAR["Ear_Canal"] = can
ANAT_SPAN = [(BEAT[3] + 30, BEAT[6] + 55)]
for o in list(EAR.values()) + [sk]: key_vis(o, ANAT_SPAN)
# ---------------------------------------------------------------- ghost the composer: spherical porthole around the head, then the whole body
xc = bpy.data.objects.new("XRay_Center", None); xc.location = Vector((0, -0.05, 1.55)); sc.collection.objects.link(xc); link(xc); to_head(xc)
XR_R = [(1, 0.0), (BEAT[3] - 5, 0.0), (BEAT[3] + 40, 0.16), (BEAT[3] + 75, 0.22), (BEAT[3] + 115, 2.5), (BEAT[6] + 25, 2.5), (BEAT[6] + 55, 0.2), (BEAT[6] + 75, 0.0)]
done = set()
cobjs = [o for o in bpy.data.objects if o.parent == C and o.type == 'MESH']
for ob in cobjs:
    for m in ob.data.materials:
        if not m or m.name in done or not m.node_tree: continue
        done.add(m.name); nt = m.node_tree; n, l = nt.nodes, nt.links
        out = next((x for x in n if x.type == 'OUTPUT_MATERIAL' and x.is_active_output), None)
        if not out or not out.inputs['Surface'].links: continue
        src = out.inputs['Surface'].links[0].from_socket
        tc = n.new('ShaderNodeTexCoord'); tc.object = xc
        ln = n.new('ShaderNodeVectorMath'); ln.operation = 'LENGTH'; l.new(tc.outputs['Object'], ln.inputs[0])
        rv = n.new('ShaderNodeValue'); rv.name = "XRayRadius"; key_val(rv.outputs[0], XR_R)
        sb = n.new('ShaderNodeMath'); sb.operation = 'SUBTRACT'; l.new(rv.outputs[0], sb.inputs[0]); l.new(ln.outputs['Value'], sb.inputs[1])
        mr = n.new('ShaderNodeMapRange'); mr.inputs['From Min'].default_value = -0.01; mr.inputs['From Max'].default_value = 0.03; l.new(sb.outputs[0], mr.inputs['Value'])
        # glass ghost: transparent + thin cyan fresnel rim
        tr = n.new('ShaderNodeBsdfTransparent'); fr = n.new('ShaderNodeLayerWeight'); fr.inputs['Blend'].default_value = 0.15
        em = n.new('ShaderNodeEmission'); em.inputs['Color'].default_value = (0.4, 0.85, 1.0, 1)
        gm = n.new('ShaderNodeMath'); gm.operation = 'MULTIPLY'; gm.inputs[1].default_value = 0.6; l.new(fr.outputs['Fresnel'], gm.inputs[0])
        # rim fades as the body fully dissolves (radius > 0.5)
        rf = n.new('ShaderNodeMapRange'); rf.inputs['From Min'].default_value = 0.3; rf.inputs['From Max'].default_value = 1.2; rf.inputs['To Min'].default_value = 1.0; rf.inputs['To Max'].default_value = 0.0
        l.new(rv.outputs[0], rf.inputs['Value']); gm2 = n.new('ShaderNodeMath'); gm2.operation = 'MULTIPLY'; l.new(gm.outputs[0], gm2.inputs[0]); l.new(rf.outputs['Result'], gm2.inputs[1])
        l.new(gm2.outputs[0], em.inputs['Strength'])
        ad = n.new('ShaderNodeAddShader'); l.new(tr.outputs[0], ad.inputs[0]); l.new(em.outputs[0], ad.inputs[1])
        mx = n.new('ShaderNodeMixShader'); l.new(mr.outputs['Result'], mx.inputs['Fac']); l.new(src, mx.inputs[1]); l.new(ad.outputs[0], mx.inputs[2])
        l.new(mx.outputs[0], out.inputs['Surface'])
hp = bpy.data.objects["Composer.short02"].modifiers["WildHair"]
for f, v in ((1, True), (BEAT[3] + 95, False), (BEAT[6] + 45, True)): hp.show_render = v; hp.keyframe_insert("show_render", frame=f)
print("GHOSTED", sorted(done))

# ---------------------------------------------------------------- cyan-to-white studio backdrop around the head (inside it the room is gone)
bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, radius=0.5, location=(0, -0.05, 1.55)); bd = bpy.context.active_object; bd.name = "XRay_Backdrop"; link(bd)
bd.visible_shadow = False
bm = bpy.data.materials.new("M_StudioBackdrop"); bm.use_nodes = True; nt = bm.node_tree; n = nt.nodes; n.clear()
o_ = n.new('ShaderNodeOutputMaterial'); tc = n.new('ShaderNodeTexCoord'); sp = n.new('ShaderNodeSeparateXYZ'); nt.links.new(tc.outputs['Generated'], sp.inputs[0])
cr = n.new('ShaderNodeValToRGB'); e = cr.color_ramp.elements; e[0].position = 0.2; e[0].color = (0.25, 0.62, 0.78, 1); e[1].position = 0.85; e[1].color = (0.92, 0.97, 1.0, 1)
nt.links.new(sp.outputs['Z'], cr.inputs['Fac'])
em = n.new('ShaderNodeEmission'); em.inputs['Strength'].default_value = 1.1; nt.links.new(cr.outputs['Color'], em.inputs['Color'])
tr = n.new('ShaderNodeBsdfTransparent'); mx = n.new('ShaderNodeMixShader'); fv = n.new('ShaderNodeValue'); fv.name = "BackdropFade"
nt.links.new(fv.outputs[0], mx.inputs['Fac']); nt.links.new(tr.outputs[0], mx.inputs[1]); nt.links.new(em.outputs[0], mx.inputs[2]); nt.links.new(mx.outputs[0], o_.inputs['Surface'])
key_val(fv.outputs[0], [(1, 0.0), (BEAT[3] + 60, 0.0), (BEAT[3] + 110, 1.0), (BEAT[6] + 30, 1.0), (BEAT[6] + 70, 0.0)])
for n_ in ["Bench", "Piano", "Fallboard_Panel", "MusicDesk", "MusicDesk_Ledge"] + list(sc["desk_pages"]):   # set pieces that poke into the studio sphere
    o = bpy.data.objects[n_]
    for f, v in ((1, False), (BEAT[3] + 112, True), (BEAT[6] + 32, False)): o.hide_render = v; o.keyframe_insert("hide_render", frame=f)
bd.data.materials.append(bm); to_head(bd); key_vis(bd, [(BEAT[3] + 55, BEAT[6] + 75)])
# studio key + rim on the anatomy, riding the head
for nm, off, en, col in (("XRay_Key", Vector((0.35, -0.35, 0.3)), 6.0, (1, 0.97, 0.92)), ("XRay_Rim", Vector((-0.2, 0.4, 0.2)), 4.0, (0.6, 0.9, 1.0))):
    ld = bpy.data.lights.new(nm, 'AREA'); ld.size = 0.25; ld.color = col; L = bpy.data.objects.new(nm, ld); C_XR.objects.link(L)
    L.location = Vector((0, -0.05, 1.55)) + off; L.rotation_euler = (-off).to_track_quat('-Z', 'Y').to_euler(); to_head(L)
    for f, v in ((1, 0), (BEAT[3] + 60, 0), (BEAT[3] + 110, en), (BEAT[6] + 30, en), (BEAT[6] + 70, 0)):
        ld.energy = v; ld.keyframe_insert("energy", frame=f)

# ---------------------------------------------------------------- vibration rings
cyan = emit_mat("M_RingCyan", (0.05, 0.7, 1.0), 5.0); red = emit_mat("M_PulseRed", (1.0, 0.08, 0.05), 16.0)
def make_ring(name, R, r, mat):
    bpy.ops.mesh.primitive_torus_add(major_radius=1.0, minor_radius=r / R, major_segments=32, minor_segments=8); o = bpy.context.active_object
    o.name = name; o.data.materials.append(mat); o.visible_shadow = False; link(o, C_FX); return o
def orient(t):  # torus axis (local Z) along the travel direction
    return t.normalized().to_track_quat('Z', 'Y').to_euler()
# (1) rod rings: world space, anchor -> bite, sampled per frame
ANCHOR = Vector(sc["anchor"]); bite = bpy.data.objects["Bite"]
BW = {}
for f in range(BEAT[2] - 2, END + 1, 2): ev(f); BW[f] = bite.matrix_world.translation.copy()
def bw(f): f = int(f); f -= (f - (BEAT[2] - 2)) % 2; return BW.get(f, BW[min(BW)])
starts = list(range(BEAT[2], BEAT[3] + 120, 13)) + list(range(BEAT[7] - 20, END - 40, 24))
for i, f0 in enumerate(starts):
    o = make_ring("Ring_Rod%02d" % i, 0.011, 0.0022, cyan); dur = 46
    o.hide_render = True; o.keyframe_insert("hide_render", frame=1)
    for k in range(0, dur + 1, 2):
        f = f0 + k; u = k / dur; tip = bw(f); p = ANCHOR.lerp(tip, u); d = tip - ANCHOR
        o.location = p; o.rotation_euler = orient(d); sz = 0.011 * (0.6 + 0.8 * math.sin(math.pi * min(1, u * 1.3)) ** 0.5) * (1 + 0.15 * math.sin(k))
        o.scale = (sz, sz, sz)
        o.keyframe_insert("location", frame=f); o.keyframe_insert("rotation_euler", frame=f); o.keyframe_insert("scale", frame=f)
        if k == 0: o.hide_render = False; o.keyframe_insert("hide_render", frame=f)
    o.hide_render = True; o.keyframe_insert("hide_render", frame=f0 + dur + 1)
# soundboard burst rings where the rod meets the piano (born at each ring start)
for i, f0 in enumerate(starts[::2]):
    o = make_ring("Ring_Board%02d" % i, 0.05, 0.002, cyan); o.location = ANCHOR + Vector((0, 0.01, 0.0)); o.rotation_euler = (math.radians(90), 0, 0)
    o.hide_render = True; o.keyframe_insert("hide_render", frame=1); o.hide_render = False; o.keyframe_insert("hide_render", frame=f0)
    for k, sz in ((0, 0.01), (14, 0.06), (24, 0.09)): o.scale = (sz, sz, sz); o.keyframe_insert("scale", frame=f0 + k)
    o.hide_render = True; o.keyframe_insert("hide_render", frame=f0 + 25)
# (2) head-space paths (rest coordinates; rings ride the head bone)
D, Cc = EARDRUM_REST, COCH
JAW_PATH = [Vector((0, -0.128, 1.531)), Vector((0.022, -0.118, 1.508)), Vector((0.042, -0.085, 1.49)), Vector((0.05, -0.04, 1.485)),
            Vector((0.052, -0.012, 1.51)), Vector((0.05, -0.002, 1.545)), Cc]
BYPASS = [Vector((0.05, -0.002, 1.545)), Vector((0.05, 0.012, 1.57)), Vector((Cc.x + 0.004, Cc.y + 0.012, Cc.z + 0.016)), Cc]
CANAL = [Vector((D.x + 0.036, D.y + 0.002, D.z + 0.002)), Vector((D.x + 0.018, D.y + 0.002, D.z + 0.004)), D + Vector((0.002, 0.002, 0))]
def poly(pts, u):
    L = [0.0]
    for a_, b_ in zip(pts, pts[1:]): L.append(L[-1] + (b_ - a_).length)
    s_ = u * L[-1]
    for i in range(len(pts) - 1):
        if s_ <= L[i + 1] or i == len(pts) - 2:
            t_ = (s_ - L[i]) / max(1e-6, L[i + 1] - L[i]); return pts[i].lerp(pts[i + 1], t_), pts[i + 1] - pts[i]
def path_rings(prefix, pts, starts_, dur, R, mat, grow=1.0):
    for i, f0 in enumerate(starts_):
        o = make_ring("%s%02d" % (prefix, i), R, R * 0.2, mat); link(o, C_XR)
        o.hide_render = True; o.keyframe_insert("hide_render", frame=1)
        for k in range(0, dur + 1, 2):
            u = smooth(k / dur) * 0.6 + 0.4 * (k / dur); p, d = poly(pts, u)
            o.location = p; o.rotation_euler = orient(d); sz = R * (0.7 + grow * math.sin(math.pi * k / dur)); o.scale = (sz, sz, sz)
            for dp in ("location", "rotation_euler", "scale"): o.keyframe_insert(dp, frame=f0 + k)
            if k == 0: o.hide_render = False; o.keyframe_insert("hide_render", frame=f0)
        o.hide_render = True; o.keyframe_insert("hide_render", frame=f0 + dur + 1)
        to_head(o)
path_rings("Ring_Jaw", JAW_PATH, list(range(BEAT[3] + 20, BEAT[5] - 40, 15)), 70, 0.006, cyan, 0.6)
path_rings("Ring_Bypass", BYPASS, list(range(BEAT[5] + 8, BEAT[6] + 40, 12)), 40, 0.005, cyan, 0.5)
# red 'normal path' pulse: down the canal, hits the torn drum and dies
for i, f0 in enumerate((BEAT[5] + 2, BEAT[5] + 40)):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8, radius=1.0); o = bpy.context.active_object; o.name = "Pulse_Red%d" % i
    o.data.materials.append(red); o.visible_shadow = False; link(o)
    o.hide_render = True; o.keyframe_insert("hide_render", frame=1); o.hide_render = False; o.keyframe_insert("hide_render", frame=f0)
    for k in range(0, 41, 2):
        u = min(1.0, k / 30); p, d = poly(CANAL, u); o.location = p
        sz = 0.0035 * (1.0 if k <= 30 else max(0.05, 1 - (k - 30) / 10) * (1.6 if k == 32 else 1.0)); o.scale = (sz, sz, sz)
        o.keyframe_insert("location", frame=f0 + k); o.keyframe_insert("scale", frame=f0 + k)
    o.hide_render = True; o.keyframe_insert("hide_render", frame=f0 + 42); to_head(o)
# red trace line along the canal (the 'skipped' path), flashes on then fades
bpy.ops.curve.primitive_bezier_curve_add(); cv = bpy.context.active_object; cv.name = "Trace_Red"; link(cv)
spn = cv.data.splines[0]; spn.bezier_points.add(len(CANAL) - 2)
for bp, p in zip(spn.bezier_points, CANAL): bp.co = p; bp.handle_left_type = bp.handle_right_type = 'AUTO'
cv.data.bevel_depth = 0.0009; cv.data.materials.append(red); cv.location = (0, 0, 0); to_head(cv)
cv.data.bevel_factor_end = 0.0; cv.data.keyframe_insert("bevel_factor_end", frame=BEAT[5]); cv.data.bevel_factor_end = 1.0; cv.data.keyframe_insert("bevel_factor_end", frame=BEAT[5] + 30)
key_vis(cv, [(BEAT[5], BEAT[6] + 10)])
bpy.ops.wm.save_as_mainfile(filepath=OUT); print("XRAY_DONE")
