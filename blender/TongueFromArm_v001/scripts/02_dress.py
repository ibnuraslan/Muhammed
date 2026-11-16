"""Dress + eye fix. blender -b work/chars.blend --python 02_dress.py -- work/chars_dressed.blend"""
import bpy, sys, bmesh
HERE = "/home/user/Muhammed/blender/TongueFromArm_v001/"
out = sys.argv[sys.argv.index("--") + 1]
# ---- eye fix on every EnhancedEye group
for g in list(bpy.data.node_groups):
    if g.name.startswith("EnhancedEye") and "CorneaTransparentMix" not in g.nodes:
        P = next(n for n in g.nodes if n.type == "BSDF_PRINCIPLED"); OUTN = next(n for n in g.nodes if n.type == "GROUP_OUTPUT")
        tl = [l for l in g.links if l.to_node == P and l.to_socket.name == "Transmission Weight"]
        src = tl[0].from_socket if tl else None
        for l in tl: g.links.remove(l)
        P.inputs["Transmission Weight"].default_value = 0.0
        ol = [l for l in g.links if l.from_node == P and l.to_node == OUTN][0]; osk = ol.to_socket; g.links.remove(ol)
        tr = g.nodes.new("ShaderNodeBsdfTransparent"); mx = g.nodes.new("ShaderNodeMixShader"); mx.name = "CorneaTransparentMix"
        if src: g.links.new(src, mx.inputs[0])
        else: mx.inputs[0].default_value = 0.0
        g.links.new(P.outputs[0], mx.inputs[1]); g.links.new(tr.outputs[0], mx.inputs[2]); g.links.new(mx.outputs[0], osk)
        print("EYEFIX", g.name)

def tint(mat, rgb, fac=1.0, desat=True):
    nt = mat.node_tree; P = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    sock = P.inputs["Base Color"]
    if not sock.links: sock.default_value = (*rgb, 1); return
    src = sock.links[0].from_socket
    if desat:
        hs = nt.nodes.new("ShaderNodeHueSaturation"); hs.inputs["Saturation"].default_value = 0.0
        nt.links.new(src, hs.inputs["Color"]); src = hs.outputs[0]
    m = nt.nodes.new("ShaderNodeMix"); m.data_type = 'RGBA'; m.blend_type = 'MULTIPLY'; m.inputs[0].default_value = fac
    nt.links.new(src, m.inputs[6]); m.inputs[7].default_value = (*rgb, 1)
    nt.links.new(m.outputs[2], sock)

def solid_mat(name, rgb, rough=0.5):
    m = bpy.data.materials.new(name); m.use_nodes = True; P = m.node_tree.nodes["Principled BSDF"]
    P.inputs["Base Color"].default_value = (*rgb, 1); P.inputs["Roughness"].default_value = rough; return m

def garment(rig_name, name, groups, push, mat, cut_z=None, keep=None, smooth=0, thick=0.004, exclude=("ears",)):
    """skin-copy garment: body verts whose dominant bone group is in `groups`, pushed out along normals"""
    B = bpy.data.objects[rig_name + ".body"]; rig = bpy.data.objects[rig_name]
    me = B.data.copy(); o = bpy.data.objects.new(rig_name + "." + name, me); bpy.context.scene.collection.objects.link(o)
    o.parent = rig; o.matrix_world = B.matrix_world.copy()
    if me.shape_keys:
        o.shape_key_clear() if False else None
    bones = {b.name for b in rig.data.bones}
    gi = {g.index: g.name for g in B.vertex_groups}
    if me.shape_keys:   # bake the shape-key mix (the character's real shape) into the copy
        kbs = me.shape_keys.key_blocks; basis = kbs[0]
        mix = [basis.data[i].co.copy() for i in range(len(me.vertices))]
        for kb in kbs[1:]:
            if kb.value and not kb.mute:
                for i in range(len(mix)): mix[i] += kb.value * (kb.data[i].co - basis.data[i].co)
        for kb in list(kbs)[::-1]: o.shape_key_remove(kb)
        for i, v in enumerate(me.vertices): v.co = mix[i]
        print("SHAPEMIX", o.name, len(kbs))
    bm = bmesh.new(); bm.from_mesh(me)
    dl = bm.verts.layers.deform.active
    kill = []
    for v in bm.verts:
        ws = {gi[k]: w for k, w in v[dl].items()}
        if any(ws.get(h, 0) > 0.0 for h in ("HelperGeometry", "JointCubes")) or "body" not in ws: kill.append(v); continue
        bw = {k: w for k, w in ws.items() if k in bones}
        if not bw: kill.append(v); continue
        dom = max(bw, key=bw.get)
        if not any(dom.startswith(g) for g in groups): kill.append(v); continue
        if cut_z is not None and v.co.z < cut_z: kill.append(v); continue
        if any(ws.get(h, 0) > 0.3 for h in exclude): kill.append(v); continue
        if keep is not None and not keep(v): kill.append(v)
    bmesh.ops.delete(bm, geom=kill, context='VERTS')
    for v in bm.verts: v.co += v.normal * 0.0  # pushed by modifier
    bm.to_mesh(me); bm.free()
    if me.shape_keys:
        for kb in list(me.shape_keys.key_blocks)[::-1]: o.shape_key_remove(kb)
    me.materials.clear(); me.materials.append(mat)
    for p in me.polygons: p.material_index = 0; p.use_smooth = True
    d = o.modifiers.new("Push", 'DISPLACE'); d.strength = push; d.mid_level = 0.0; d.direction = 'NORMAL'
    if smooth:
        sm = o.modifiers.new("Loose", 'SMOOTH'); sm.factor = 1.0; sm.iterations = smooth
    so = o.modifiers.new("Thick", 'SOLIDIFY'); so.thickness = thick; so.offset = -1
    a = o.modifiers.new("Armature", 'ARMATURE'); a.object = rig
    s = o.modifiers.new("Subdivision", 'SUBSURF'); s.levels = 1; s.render_levels = 1
    print("GARMENT", o.name, len(me.vertices))
    return o

# ---- patient: plain soft-blue hospital gown (a procedural stripe swam on the skin-copy mesh)
# loose top + trousers: the surgeon's scrub suit (MPFB casualsuit06) refitted onto the patient's body with Surface Deform
def shape_coords(ob):
    me = ob.data
    if not me.shape_keys: return [v.co.copy() for v in me.vertices]
    kbs = me.shape_keys.key_blocks; basis = kbs[0]; mix = [basis.data[i].co.copy() for i in range(len(me.vertices))]
    for kb in kbs[1:]:
        if kb.value and not kb.mute:
            for i in range(len(mix)): mix[i] += kb.value * (kb.data[i].co - basis.data[i].co)
    return mix
def refit(donor_rig, cloth, target_rig, new_name, mat_):
    DB = bpy.data.objects[donor_rig + ".body"]; TB = bpy.data.objects[target_rig + ".body"]
    src = shape_coords(DB); dst = shape_coords(TB); assert len(src) == len(dst), (len(src), len(dst))
    dme = bpy.data.meshes.new("refit_src"); dme.from_pydata([tuple(c) for c in src], [], [tuple(p.vertices) for p in DB.data.polygons])
    dob = bpy.data.objects.new("refit_src", dme); bpy.context.scene.collection.objects.link(dob)
    C = bpy.data.objects[donor_rig + "." + cloth]
    cm = C.data.copy()
    if cm.shape_keys:
        cc = shape_coords(C)
        tmp = bpy.data.objects.new("tmpc", cm); bpy.context.scene.collection.objects.link(tmp)
        for kb in list(cm.shape_keys.key_blocks)[::-1]: tmp.shape_key_remove(kb)
        for i, v in enumerate(cm.vertices): v.co = cc[i]
        bpy.data.objects.remove(tmp)
    co = bpy.data.objects.new(target_rig + "." + new_name, cm); bpy.context.scene.collection.objects.link(co)
    sd = co.modifiers.new("Refit", 'SURFACE_DEFORM'); sd.target = dob
    bpy.context.view_layer.objects.active = co
    with bpy.context.temp_override(object=co, active_object=co): bpy.ops.object.surfacedeform_bind(modifier="Refit")
    for i, v in enumerate(dme.vertices): v.co = dst[i]
    dme.update(); bpy.context.view_layer.update()
    with bpy.context.temp_override(object=co, active_object=co): bpy.ops.object.modifier_apply(modifier="Refit")
    bpy.data.objects.remove(dob)
    R = bpy.data.objects[target_rig]; co.parent = R; co.matrix_world = TB.matrix_world.copy()
    am = co.modifiers.new("Armature", 'ARMATURE'); am.object = R
    sub = co.modifiers.new("Subdivision", 'SUBSURF'); sub.levels = 1; sub.render_levels = 1
    cm.materials.clear(); cm.materials.append(mat_)
    print("REFIT", co.name, len(cm.vertices))
    return co
g = bpy.data.materials.new("GownPrint"); g.use_nodes = True; nt = g.node_tree; P = nt.nodes["Principled BSDF"]
uv = nt.nodes.new("ShaderNodeTexCoord"); vo = nt.nodes.new("ShaderNodeTexVoronoi"); vo.inputs["Scale"].default_value = 150
nt.links.new(uv.outputs["UV"], vo.inputs["Vector"])
cr = nt.nodes.new("ShaderNodeValToRGB"); cr.color_ramp.elements[0].position = 0.16; cr.color_ramp.elements[1].position = 0.21
cr.color_ramp.elements[0].color = (0.10, 0.20, 0.50, 1); cr.color_ramp.elements[1].color = (0.40, 0.58, 0.86, 1)
nt.links.new(vo.outputs["Distance"], cr.inputs[0]); nt.links.new(cr.outputs[0], P.inputs["Base Color"]); P.inputs["Roughness"].default_value = 0.85
refit("Surgeon", "male_casualsuit06", "Patient", "gown", g)
bpy.data.objects["Patient.female_sportsuit01"].hide_render = True; bpy.data.objects["Patient.female_sportsuit01"].hide_viewport = True

# crop top part of the sportsuit removed (the gown covers the torso); leggings stay
def strip_top(rig_name, cloth):
    C = bpy.data.objects[rig_name + "." + cloth]; rig = bpy.data.objects[rig_name]; bones = {b.name for b in rig.data.bones}
    gi = {g.index: g.name for g in C.vertex_groups}
    bm = bmesh.new(); bm.from_mesh(C.data); dl = bm.verts.layers.deform.active; kill = []
    for v in bm.verts:
        bw = {gi[k]: w for k, w in v[dl].items() if gi[k] in bones}
        if bw and max(bw, key=bw.get).startswith(("spine", "breast", "clavicle", "shoulder", "upperarm", "neck")): kill.append(v)
    bmesh.ops.delete(bm, geom=kill, context='VERTS'); bm.to_mesh(C.data); bm.free(); print("STRIPTOP", len(kill))

# dark brown hair for the patient
for n in ("Patient.ponytail01", "Patient.eyebrow001"):
    tint(bpy.data.objects[n].data.materials[0], (0.16, 0.09, 0.05), 1.0)
# ---- doctor: bare hands (no gloves on the ward), navy skirt
D = bpy.data.objects["Doctor.body"]
for p in D.data.polygons: p.material_index = 0
while len(D.data.materials) > 1: D.data.materials.pop(index=1)
# ---- surgeon & nurse: proper scrub caps (scalp copy) and masks over nose + mouth (face copy); hair hidden under the cap
for rn, hair in (("Surgeon", "short02"), ("Nurse", "bob02")):
    for k in ("_FaceMask", "_Mask", "_Cap"):
        bpy.data.objects.remove(bpy.data.objects[rn + k])
    R = bpy.data.objects[rn]; EY = R.data.bones["eye.L"].head_local.copy(); HD = R.data.bones["head"].head_local.copy()
    hob = bpy.data.objects[rn + "." + hair]; hob.hide_render = True; hob.hide_viewport = True
    capm = solid_mat(rn + "_ScrubCap", (0.30, 0.62, 0.66), 0.8)
    garment(rn, "cap", ("head",), 0.012, capm, keep=lambda v, EY=EY: v.co.z > EY.z + 0.028 or (v.co.z > EY.z - 0.02 and v.co.y > EY.y + 0.075), smooth=6, thick=0.003)
    mk = solid_mat(rn + "_MaskM", (0.70, 0.84, 0.93), 0.85)
    garment(rn, "mask", ("head", "jaw", "special", "oris", "levator", "risorius", "tongue", "temporalis"), 0.008, mk,
            keep=lambda v, EY=EY: EY.z - 0.115 < v.co.z < EY.z - 0.022 and v.co.y < EY.y + 0.035 and abs(v.co.x) < 0.072, smooth=8, thick=0.002)
# nurse: scrub-teal trousers/top band (the black band at her waist read as bare)
tint(bpy.data.objects["Nurse.female_sportsuit01"].data.materials[0], (0.30, 0.60, 0.62), 1.0)
for m in bpy.data.objects["Nurse.body"].data.materials:
    if m.name.startswith("NurseScrub"): tint(m, (0.30, 0.60, 0.62), 1.0)
# ---- girl: part the fringe (remove the bob's front cards that hang over the eyes)
G = bpy.data.objects["Girl"]; hb = bpy.data.objects["Girl.bob01"]
ey = G.data.bones["eye.L"].head_local; hc = G.data.bones["head"].head_local
bm = bmesh.new(); bm.from_mesh(hb.data)
kill = [v for v in bm.verts if v.co.y < ey.y + 0.025 and v.co.z < ey.z + 0.045 and abs(v.co.x) < 0.085]
bmesh.ops.delete(bm, geom=kill, context='VERTS'); bm.to_mesh(hb.data); bm.free(); print("FRINGE", len(kill), tuple(ey))
# ---- girl: blue outfit
tint(bpy.data.objects["Girl.female_casualsuit01"].data.materials[0], (0.25, 0.42, 0.95), 1.0)
bpy.ops.wm.save_as_mainfile(filepath=out, compress=True)
