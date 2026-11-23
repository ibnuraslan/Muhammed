# v012 looks (client rejection of v011). Runs on work/anim.blend after 03c_dress_v009d.py, before 04_camera_fx.py.
# 1. Patient: real short hair (the surgeon's MPFB short02 rebound to his head bone, shrinkwrapped close to the scalp),
#    warmer natural skin, dark brown irises. Eye fix (LegoInNose eye_fix.py) and a camera catchlight for every character.
# 2. The ear dressing (white gauze disc, read as headphones) becomes a soft skin-toned ear shape close to the head.
# 4. Staff: real hair under the caps (the nurse was bald), scrub top and trousers in different shades.
# 6. Set: warm wall paint, warmer lights, posters (no text), a tall cabinet, a sink unit, a wall clock, a chair rail.
import bpy, sys, bmesh, math
from mathutils import Vector, Matrix
OUT = sys.argv[sys.argv.index("--") + 1]
OB = bpy.data.objects; sc = bpy.context.scene
PAT, SUR, NUR = OB["Patient"], OB["Surgeon"], OB["Nurse"]

def mat(name, col, rough=0.5, sss=0.0, metal=0.0):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]; b.inputs["Base Color"].default_value = (*col, 1)
    b.inputs["Roughness"].default_value = rough; b.inputs["Metallic"].default_value = metal
    if sss:
        b.inputs["Subsurface Weight"].default_value = sss; b.inputs["Subsurface Radius"].default_value = (1.0, 0.35, 0.2)
    return m

# ---------------------------------------------------------------- eye fix (shared EnhancedEye group) + irises
_NO_SAVE = True
g = bpy.data.node_groups["EnhancedEye"]
if not any(n.name == "CorneaTransparentMix" for n in g.nodes):
    P = next(n for n in g.nodes if n.type == "BSDF_PRINCIPLED"); OUTN = next(n for n in g.nodes if n.type == "GROUP_OUTPUT")
    tl = [l for l in g.links if l.to_node == P and l.to_socket.name == "Transmission Weight"]
    src = tl[0].from_socket if tl else None
    for l in tl: g.links.remove(l)
    P.inputs["Transmission Weight"].default_value = 0.0
    ol = [l for l in g.links if l.from_node == P and l.to_node == OUTN][0]; out_sock = ol.to_socket; g.links.remove(ol)
    tr = g.nodes.new("ShaderNodeBsdfTransparent"); mx = g.nodes.new("ShaderNodeMixShader"); mx.name = "CorneaTransparentMix"
    if src: g.links.new(src, mx.inputs[0])
    else: mx.inputs[0].default_value = 0.0
    g.links.new(P.outputs[0], mx.inputs[1]); g.links.new(tr.outputs[0], mx.inputs[2]); g.links.new(mx.outputs[0], out_sock)
IRIS = {"Patient": ((0.16, 0.08, 0.035), (0.06, 0.03, 0.012)), "Surgeon": ((0.22, 0.14, 0.06), (0.08, 0.05, 0.02)),
        "Nurse": ((0.12, 0.06, 0.03), (0.045, 0.022, 0.01))}
for who, (a, b) in IRIS.items():
    m = bpy.data.materials[who + ".high-poly"]
    gn = next(n for n in m.node_tree.nodes if n.type == "GROUP")
    gn.inputs["IrisMajorColor"].default_value = (*a, 1); gn.inputs["IrisMinorColor"].default_value = (*b, 1)
# catchlight: a tiny emitter beside the camera, seen only in reflections (eyes), not by the camera or in diffuse light
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.03, segments=12, ring_count=6); cl = bpy.context.object; cl.name = "Catchlight"
em = bpy.data.materials.new("CatchlightEmit"); em.use_nodes = True; nt = em.node_tree
for n in list(nt.nodes):
    if n.type != "OUTPUT_MATERIAL": nt.nodes.remove(n)
e = nt.nodes.new("ShaderNodeEmission"); e.inputs["Strength"].default_value = 60.0
nt.links.new(e.outputs[0], nt.nodes["Material Output"].inputs["Surface"]); cl.data.materials.append(em)
cl.visible_camera = False; cl.visible_diffuse = False; cl.visible_transmission = False; cl.visible_volume_scatter = False; cl.visible_shadow = False
cl["follow_camera"] = (0.12, 0.1, 0.0)   # 04_camera_fx.py parents it to CAM_Film at this camera-local offset

# ---------------------------------------------------------------- patient skin: warmer, natural
pg = next(n for n in bpy.data.materials["Patient.body"].node_tree.nodes if n.type == "GROUP")
for k, v in (("colorMixIn", (0.92, 0.5, 0.36, 1.0)), ("colorMixInStrength", 0.14), ("Roughness", 0.5), ("SSS strength", 0.35), ("Pore strength", 0.3)):
    if k in pg.inputs: pg.inputs[k].default_value = v

# ---------------------------------------------------------------- hair: rebind a copy of MPFB short02 to another rig's head
def rest_mesh(src):
    rig = src.parent; old = rig.data.pose_position; rig.data.pose_position = 'REST'; bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get(); ev = src.evaluated_get(dg)
    me = bpy.data.meshes.new_from_object(ev, depsgraph=dg); rig.data.pose_position = old; bpy.context.view_layer.update()
    me.transform(src.matrix_world)          # rig objects sit at the origin: world == armature space at rest
    return me
def hair_on(rig, src, name, scale=1.0, lift=0.0, wrap=0.006):
    me = rest_mesh(src)
    hs, hp = src.parent.data.bones["head"], rig.data.bones["head"]
    k = hp.length / hs.length * scale
    me.transform(hp.matrix_local @ Matrix.Translation((0, lift, 0)) @ Matrix.Scale(k, 4) @ hs.matrix_local.inverted())
    o = bpy.data.objects.new(name, me)
    for c in src.users_collection: c.objects.link(o)
    o.parent = rig; o.parent_type = 'BONE'; o.parent_bone = "head"
    o.matrix_parent_inverse = (hp.matrix_local @ Matrix.Translation((0, hp.length, 0))).inverted(); o.matrix_basis = Matrix.Identity(4)
    body = OB[rig.name + ".body"]
    sw = o.modifiers.new("onscalp", 'SHRINKWRAP'); sw.target = body; sw.wrap_method = 'NEAREST_SURFACEPOINT'
    sw.wrap_mode = 'OUTSIDE_SURFACE'; sw.offset = wrap
    o.modifiers.new("sm", 'SUBSURF').levels = 1
    return o
ph = hair_on(PAT, OB["Surgeon.short02"], "Patient.hair", scale=1.0, wrap=0.005)
# v013: cut the hair away around both ears (it formed "earmuff" discs and hid the grafted ear)
import bmesh
_bm = bmesh.new(); _bm.from_mesh(ph.data)
_ec = Vector((0.0797, -0.0457, 1.6741))
_kill = [v for v in _bm.verts if abs(v.co.x) > 0.05 and ((v.co.y - _ec.y) / 0.045) ** 2 + ((v.co.z - _ec.z) / 0.05) ** 2 < 1.0]
bmesh.ops.delete(_bm, geom=_kill, context='VERTS'); _bm.to_mesh(ph.data); _bm.free(); print("HAIR_EARCUT", len(_kill))
hm = OB["Surgeon.short02"].data.materials[0].copy(); hm.name = "Patient.hair"; ph.data.materials.clear(); ph.data.materials.append(hm)
# the nurse's own bob, shown again under her cap (03c hid it); kept close to the head so it sits under the cap
nb = OB["Nurse.bob02"]; nb.hide_render = False; nb.hide_viewport = False
sw = nb.modifiers.new("close", 'SHRINKWRAP'); sw.target = OB["Nurse.body"]; sw.wrap_method = 'NEAREST_SURFACEPOINT'; sw.wrap_mode = 'OUTSIDE_SURFACE'; sw.offset = 0.008
while nb.modifiers.find("close") > nb.modifiers.find("SUBSURF") > -1 and nb.modifiers.find("close") > 1: nb.modifiers.move(nb.modifiers.find("close"), nb.modifiers.find("close") - 1)
for cap in (OB["Surgeon_Cap"], OB["Nurse_Cap"]):   # v012: a fitted cap, not a balloon: smaller and flatter, hair shows below, eyes clear
    cap.data.transform(Matrix.Diagonal((0.9, 0.78, 0.9, 1.0)))
    # v014: soft cloth, not a dome - gathered folds (radial waves), a slight droop at the back, a stitched brim band
    ctex = bpy.data.textures.new(cap.name + "_folds", 'WOOD'); ctex.wood_type = 'BANDNOISE'; ctex.noise_basis_2 = 'SIN'; ctex.turbulence = 2.0; ctex.noise_scale = 0.05
    sd = cap.modifiers.new("subd", 'SUBSURF'); sd.levels = sd.render_levels = 2
    dsp = cap.modifiers.new("folds", 'DISPLACE'); dsp.texture = ctex; dsp.strength = 0.0025; dsp.mid_level = 0.5; dsp.texture_coords = 'LOCAL'


# ---------------------------------------------------------------- ear dressing -> soft skin-toned ear shape close to the head
pad = OB["Bandage_Pad"]; en = OB["Ear_New"]
me = en.data.copy(); me.name = "EarStub"
me.transform(Matrix.Rotation(math.radians(90), 4, 'Z') @ Matrix.Rotation(math.radians(8), 4, 'X') @ Matrix.Scale(0.82, 4))
c = sum((v.co for v in me.vertices), Vector()) / len(me.vertices); me.transform(Matrix.Translation(-c + Vector((0.002, -0.004, 0.0))))
pad.data = me
skin = mat("EarStubSkin", (0.78, 0.5, 0.4), rough=0.5, sss=0.25)
pad.data.materials.clear(); pad.data.materials.append(skin)
for p in pad.data.polygons: p.use_smooth = True
if not any(m.type == 'SUBSURF' for m in pad.modifiers): pad.modifiers.new("soft", 'SUBSURF').levels = 1
for n in ("Bandage_Tape0", "Bandage_Tape1"):
    t = OB.get(n)
    if t:
        if t.animation_data: t.animation_data_clear()
        t.hide_render = True; t.hide_viewport = True

# ---------------------------------------------------------------- staff: trousers a darker shade than the scrub top
def legs_material(rig, ob, newmat):
    bones = {b.name.lower() for b in rig.data.bones}
    gi = {g.index: g.name.lower() for g in ob.vertex_groups if g.name.lower() in bones}
    idx = None
    for i, m in enumerate(ob.data.materials):
        if m and m.name == newmat.name: idx = i
    if idx is None: ob.data.materials.append(newmat); idx = len(ob.data.materials) - 1
    LEG = ("upperleg", "lowerleg", "pelvis", "foot", "toe", "glute")
    n = 0
    for p in ob.data.polygons:
        ok = True
        for vi in p.vertices:
            gs = [x for x in ob.data.vertices[vi].groups if x.group in gi]
            if not gs: ok = False; break
            dom = gi[max(gs, key=lambda x: x.weight).group]
            if not any(k in dom for k in LEG): ok = False; break
        if ok and ob.data.materials[p.material_index] and "Glove" not in ob.data.materials[p.material_index].name:
            p.material_index = idx; n += 1
    return n
tN = mat("NurseTrousers", (0.04, 0.08, 0.16), rough=0.8)
print("NURSE_TROUSERS", legs_material(NUR, OB["Nurse.female_sportsuit01"], tN), legs_material(NUR, OB["Nurse.body"], tN))
topN = mat("NurseTop", (0.35, 0.62, 0.78), rough=0.75)
ns = OB["Nurse.female_sportsuit01"]
for i, m in enumerate(ns.data.materials):
    if m and m.name != "NurseTrousers": ns.data.materials[i] = topN
nbm = OB["Nurse.body"]
for i, m in enumerate(nbm.data.materials):
    if m and m.name == "NurseScrubBody": nbm.data.materials[i] = topN
tS = mat("SurgeonTrousers", (0.06, 0.2, 0.22), rough=0.75)
print("SURGEON_TROUSERS", legs_material(SUR, OB["Surgeon.male_casualsuit06"], tS), legs_material(SUR, OB["Surgeon.body"], tS))

# ---------------------------------------------------------------- set: warm walls and light, posters, cabinet, sink, clock, rail
SET = bpy.data.collections.get("Set_v012") or bpy.data.collections.new("Set_v012")
if SET.name not in sc.collection.children: sc.collection.children.link(SET)
wall = mat("WallWarm", (0.84, 0.79, 0.7), rough=0.85)
for n in ("OR_WallBack", "OR_WallLeft", "OR_WallRight", "OR_WallFront"):
    o = OB[n]
    for i in range(len(o.data.materials)): o.data.materials[i] = wall
def box(name, loc, dims, m, rot=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=loc); o = bpy.context.object; o.name = name
    o.scale = dims; o.rotation_euler = (0, 0, math.radians(rot)); bpy.ops.object.transform_apply(scale=True, rotation=True)
    o.data.materials.append(m)
    for c in list(o.users_collection): c.objects.unlink(o)
    SET.objects.link(o); return o
def poster(name, loc, w, h, rotz, seed, hue, into=1.0):
    frame = mat("PosterFrame", (0.12, 0.11, 0.1), rough=0.4)
    box(name + "_frame", loc, (0.02, w + 0.04, h + 0.04), frame, rotz)
    pm = bpy.data.materials.new(name + "_art"); pm.use_nodes = True; nt = pm.node_tree; b = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord"); vo = nt.nodes.new("ShaderNodeTexVoronoi"); vo.inputs["Scale"].default_value = 3.0 + seed
    vo.inputs["Randomness"].default_value = 0.8; wv = nt.nodes.new("ShaderNodeTexWave"); wv.inputs["Scale"].default_value = 1.5 + seed * 0.3
    ramp = nt.nodes.new("ShaderNodeValToRGB"); el = ramp.color_ramp.elements
    el[0].color = (0.95, 0.93, 0.88, 1); el[1].color = (*hue, 1); el.new(0.5).color = (hue[2], hue[0] * 0.8, hue[1], 1)
    mix = nt.nodes.new("ShaderNodeMix"); mix.data_type = 'FLOAT'; mix.inputs[0].default_value = 0.5
    nt.links.new(tc.outputs["Object"], vo.inputs["Vector"]); nt.links.new(tc.outputs["Object"], wv.inputs["Vector"])
    nt.links.new(vo.outputs["Distance"], mix.inputs[2]); nt.links.new(wv.outputs["Fac"], mix.inputs[3])
    nt.links.new(mix.outputs[0], ramp.inputs[0]); nt.links.new(ramp.outputs[0], b.inputs["Base Color"]); b.inputs["Roughness"].default_value = 0.6
    off = Vector((0.012, 0, 0)); off.rotate(Matrix.Rotation(math.radians(rotz), 3, 'Z'))
    box(name, Vector(loc) - off * into, (0.006, w, h), pm, rotz)
cab = mat("CabinetWhite", (0.86, 0.87, 0.86), rough=0.5); cabd = mat("CabinetBlue", (0.32, 0.47, 0.6), rough=0.5)
steel = mat("Steel", (0.7, 0.7, 0.72), rough=0.3, metal=1.0)
# back wall, right of the existing cabinets
box("V12_TallCab", (2.42, 2.32, 1.0), (0.62, 0.42, 2.0), cab)
box("V12_TallCabDoorL", (2.27, 2.105, 1.05), (0.29, 0.01, 1.8), cabd); box("V12_TallCabDoorR", (2.57, 2.105, 1.05), (0.29, 0.01, 1.8), cabd)
box("V12_TallCabHandle", (2.42, 2.095, 1.05), (0.02, 0.02, 0.3), steel)
poster("V12_PosterB1", (0.95, 2.545, 1.72), 0.46, 0.62, 90, 1, (0.75, 0.28, 0.22))
poster("V12_PosterB2", (1.62, 2.545, 1.78), 0.52, 0.7, 90, 3, (0.2, 0.45, 0.7))
bpy.ops.mesh.primitive_cylinder_add(radius=0.16, depth=0.04, location=(1.62, 2.53, 2.42), rotation=(math.radians(90), 0, 0)); ck = bpy.context.object; ck.name = "V12_Clock"
ck.data.materials.append(mat("ClockFace", (0.95, 0.95, 0.93), rough=0.4))
for c in list(ck.users_collection): c.objects.unlink(ck)
SET.objects.link(ck)
for a, L in ((math.radians(60), 0.09), (math.radians(-30), 0.12)):
    h_ = box("V12_ClockHand", (1.62 + math.sin(a) * L / 2, 2.505, 2.42 + math.cos(a) * L / 2), (0.012, 0.006, L), mat("ClockHand", (0.05, 0.05, 0.05)))
    h_.rotation_euler = (0, -a, 0)
# right wall
poster("V12_PosterR1", (2.945, 0.55, 1.72), 0.5, 0.68, 0, 2, (0.3, 0.6, 0.4))
box("V12_SinkCab", (2.7, 1.55, 0.45), (0.5, 0.9, 0.9), cab); box("V12_SinkTop", (2.7, 1.55, 0.915), (0.52, 0.92, 0.03), mat("Worktop", (0.25, 0.28, 0.3), rough=0.35))
box("V12_SinkBasin", (2.68, 1.55, 0.93), (0.36, 0.44, 0.02), steel); box("V12_Tap", (2.88, 1.55, 1.05), (0.03, 0.03, 0.22), steel)
box("V12_SinkDoor", (2.444, 1.55, 0.45), (0.01, 0.84, 0.8), cabd)
# left wall
poster("V12_PosterL1", (-2.535, -0.35, 1.72), 0.5, 0.68, 0, 4, (0.85, 0.6, 0.2), into=-1.0)
poster("V12_PosterL2", (-2.535, 0.55, 1.78), 0.44, 0.6, 0, 5, (0.55, 0.3, 0.6), into=-1.0)
# chair rail round the room (breaks the flat wall)
rail = mat("Rail", (0.36, 0.52, 0.58), rough=0.5)
box("V12_RailB", (1.65, 2.54, 1.0), (2.7, 0.03, 0.06), rail, 0); box("V12_RailR", (2.94, 0.2, 1.0), (0.03, 2.4, 0.06), rail)
box("V12_RailL", (-2.54, 0.0, 1.0), (0.03, 5.0, 0.06), rail)
# ---------------------------------------------------------------- tailored scrubs: hide the boxy clothes shells (shoulder hump, tube
# arms); the bodies already wear the scrub top / trousers materials, so the garments follow the body. Folds via a fabric bump.
for n in ("Surgeon.male_casualsuit06", "Nurse.female_sportsuit01"):
    OB[n].hide_render = True; OB[n].hide_viewport = True
def torso_material(rig, ob, m):
    """every torso, shoulder, upper-arm (sleeve) and lower-neck polygon wears the scrub top (no bare shoulders)"""
    bones = {b.name.lower() for b in rig.data.bones}; gi = {g.index: g.name.lower() for g in ob.vertex_groups if g.name.lower() in bones}
    if m.name not in [x.name for x in ob.data.materials if x]: ob.data.materials.append(m)
    idx = [x.name if x else "" for x in ob.data.materials].index(m.name)
    nz = rig.data.bones["neck01"].head_local.z + 0.015
    TOP = ("spine", "clavicle", "shoulder", "breast", "pectoral", "upperarm01", "upperarm02")
    n = 0
    for p in ob.data.polygons:
        cur = ob.data.materials[p.material_index]
        if cur and ("Glove" in cur.name or "Trousers" in cur.name): continue
        ok = True
        for vi in p.vertices:
            v = ob.data.vertices[vi]; gs = [x for x in v.groups if x.group in gi]
            if not gs: ok = False; break
            dom = gi[max(gs, key=lambda x: x.weight).group]
            if not (any(dom.startswith(k) for k in TOP) or (dom.startswith("neck") and v.co.z < nz)): ok = False; break
        if ok: p.material_index = idx; n += 1
    return n
scrubS = next(m for m in OB["Surgeon.body"].data.materials if m and "casualsuit" in m.name)
print("TORSO", torso_material(SUR, OB["Surgeon.body"], scrubS), torso_material(NUR, OB["Nurse.body"], bpy.data.materials["NurseTop"]))
# the carved ear on the tray reads as a skin-toned ear (helix and lobe), not white paper
ec = OB.get("Ear_Cartilage")
if ec:
    ec.data.materials.clear(); ec.data.materials.append(bpy.data.materials["Cartilage"])   # v013: the carved ear is the same ivory cartilage as the block and the ear in the arm (one look, no model pop)
def fabric(m, scale=18.0, strength=0.35):
    if not m or not m.use_nodes: return
    nt = m.node_tree; b = next((n for n in nt.nodes if n.type == "BSDF_PRINCIPLED"), None)
    if b is None or b.inputs["Normal"].is_linked: return
    tc = nt.nodes.new("ShaderNodeTexCoord"); nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = scale
    nz.inputs["Detail"].default_value = 3.0; wv = nt.nodes.new("ShaderNodeTexWave"); wv.inputs["Scale"].default_value = scale * 0.4
    wv.inputs["Distortion"].default_value = 6.0; mx = nt.nodes.new("ShaderNodeMath"); mx.operation = 'ADD'
    bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = strength; bp.inputs["Distance"].default_value = 0.004
    nt.links.new(tc.outputs["Object"], nz.inputs["Vector"]); nt.links.new(tc.outputs["Object"], wv.inputs["Vector"])
    nt.links.new(nz.outputs["Fac"], mx.inputs[0]); nt.links.new(wv.outputs["Fac"], mx.inputs[1]); nt.links.new(mx.outputs[0], bp.inputs["Height"])
    nt.links.new(bp.outputs["Normal"], b.inputs["Normal"])
for cap in (OB["Surgeon_Cap"], OB["Nurse_Cap"]):   # v014: cloth weave + folds on the caps
    if cap.data.materials and cap.data.materials[0]: fabric(cap.data.materials[0], scale=30.0, strength=0.6)
for mn in ("NurseTop", "NurseTrousers", "SurgeonTrousers"):
    fabric(bpy.data.materials.get(mn))
for i, m in enumerate(OB["Surgeon.body"].data.materials):
    if m and "casualsuit" in m.name: fabric(m)
pt = OB["Patient.male_casualsuit06"].data.materials[0]
pg_ = next((n for n in pt.node_tree.nodes if n.type == "GROUP"), None)
if pg_ is None: fabric(pt, scale=14.0, strength=0.45)
else:   # MPFB clothes material: put the bump on the group's output side via a wrapper BSDF input if present
    for k in ("Bump strength", "Normal strength"):
        if k in pg_.inputs: pg_.inputs[k].default_value = 0.6
# v014: the patient's suit is split into two garments - a white cotton tee whose hem sits over the jeans' waistband,
# and blue denim jeans (the one-piece texture ran the tee down into the crotch like a onesie)
_ps = OB["Patient.male_casualsuit06"]
denim = mat("PatientDenim", (0.07, 0.13, 0.26), rough=0.85); fabric(denim, scale=40.0, strength=0.5)
tee = mat("PatientTee", (0.82, 0.82, 0.8), rough=0.9); fabric(tee, scale=10.0, strength=0.55)
print("PATIENT_JEANS", legs_material(PAT, _ps, denim))
_ti = len(_ps.data.materials); _ps.data.materials.append(tee)
_di = next(i for i, m in enumerate(_ps.data.materials) if m and m.name == "PatientDenim")
_bones = {b.name.lower() for b in PAT.data.bones}; _gi = {g.index: g.name.lower() for g in _ps.vertex_groups if g.name.lower() in _bones}
_nt = 0
for p_ in _ps.data.polygons:
    if p_.material_index == _di: continue
    zs = [_ps.data.vertices[v].co.z for v in p_.vertices]
    p_.material_index = _ti; _nt += 1
# v014: everything below the hips is denim (the tee mesh hung down into a V between the legs); a straight hem just below the waist
for p_ in _ps.data.polygons:
    if p_.center.z < 0.985: p_.material_index = _di
    elif p_.material_index == _di and p_.center.z > 1.0: p_.material_index = _ti
# hem: tee faces whose lowest vertex is within 4 cm above the jeans' top become tee (overhang), so the hem crosses the waistband
_dz = [ _ps.data.vertices[v].co.z for p_ in _ps.data.polygons if p_.material_index == _di for v in p_.vertices]
_top = sorted(_dz)[int(len(_dz) * 0.995)] if _dz else 0
for p_ in _ps.data.polygons:
    if p_.material_index == _di and min(_ps.data.vertices[v].co.z for v in p_.vertices) > _top - 0.035 and p_.center.z > 0.95:
        p_.material_index = _ti
print("PATIENT_TEE", _nt, "top", round(_top, 3))
# the ear in the forearm turns from cartilage to living pink skin over the growth close-ups (progression)
ea = OB.get("Ear_InArm")
if ea:
    gm = mat("EarInArmGrow", (0.9, 0.86, 0.8), rough=0.45, sss=0.2); ea.data.materials.clear(); ea.data.materials.append(gm)
    bc = gm.node_tree.nodes["Principled BSDF"].inputs["Base Color"]
    for f, c in ((1, (0.9, 0.86, 0.8)), (871, (0.9, 0.86, 0.8)), (960, (0.84, 0.62, 0.55)), (1010, (0.8, 0.5, 0.42))):
        bc.default_value = (*c, 1); bc.keyframe_insert("default_value", frame=f)
# v013: the grafted ear matches the end of the in-arm wipe (living pink skin), not a dark brown blob; no stray source ear
es = bpy.data.materials.get("EarSkin")
if es: next(n for n in es.node_tree.nodes if n.type == 'BSDF_PRINCIPLED').inputs["Base Color"].default_value = (0.8, 0.5, 0.42, 1)
if OB.get("Ear_Src"): OB["Ear_Src"].hide_render = True; OB["Ear_Src"].hide_viewport = True
# v012b: harvested rib cartilage reads as living tissue (pearly ivory-pink, SSS, glossy), not white paper; block smoothed
cm = bpy.data.materials.get("Cartilage")
if cm and cm.node_tree:
    pb = next(n for n in cm.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    pb.inputs["Base Color"].default_value = (0.9, 0.74, 0.66, 1); pb.inputs["Roughness"].default_value = 0.32
    pb.inputs["Subsurface Weight"].default_value = 0.4; pb.inputs["Subsurface Radius"].default_value = (0.6, 0.3, 0.2)
    pb.inputs["Subsurface Scale"].default_value = 0.01
for n in ("Cart_Block", "Chest_Piece_Carry"):
    o = bpy.data.objects.get(n)
    if o and o.type == 'MESH':
        for p_ in o.data.polygons: p_.use_smooth = True
        if not any(m.type == 'SUBSURF' for m in o.modifiers):
            sm = o.modifiers.new("Smooth", 'SUBSURF'); sm.levels = sm.render_levels = 2
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("LOOKS_DONE")
