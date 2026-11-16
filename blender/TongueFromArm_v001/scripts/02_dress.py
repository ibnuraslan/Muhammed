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

def garment(rig_name, name, groups, push, mat, cut_z=None):
    """skin-copy garment: body verts whose dominant bone group is in `groups`, pushed out along normals"""
    B = bpy.data.objects[rig_name + ".body"]; rig = bpy.data.objects[rig_name]
    me = B.data.copy(); o = bpy.data.objects.new(rig_name + "." + name, me); bpy.context.scene.collection.objects.link(o)
    o.parent = rig; o.matrix_world = B.matrix_world.copy()
    if me.shape_keys:
        o.shape_key_clear() if False else None
    bones = {b.name for b in rig.data.bones}
    gi = {g.index: g.name for g in B.vertex_groups}
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
        if cut_z is not None and v.co.z < cut_z: kill.append(v)
    bmesh.ops.delete(bm, geom=kill, context='VERTS')
    for v in bm.verts: v.co += v.normal * 0.0  # pushed by modifier
    bm.to_mesh(me); bm.free()
    if me.shape_keys:
        for kb in list(me.shape_keys.key_blocks)[::-1]: o.shape_key_remove(kb)
    me.materials.clear(); me.materials.append(mat)
    for p in me.polygons: p.material_index = 0; p.use_smooth = True
    d = o.modifiers.new("Push", 'DISPLACE'); d.strength = push; d.mid_level = 0.0; d.direction = 'NORMAL'
    so = o.modifiers.new("Thick", 'SOLIDIFY'); so.thickness = 0.004; so.offset = -1
    a = o.modifiers.new("Armature", 'ARMATURE'); a.object = rig
    s = o.modifiers.new("Subdivision", 'SUBSURF'); s.levels = 1; s.render_levels = 1
    print("GARMENT", o.name, len(me.vertices))
    return o

# ---- patient: plain soft-blue hospital gown (a procedural stripe swam on the skin-copy mesh)
g = solid_mat("Gown", (0.26, 0.48, 0.84), 0.75)
garment("Patient", "gown", ("spine", "pelvis", "breast", "clavicle", "shoulder", "upperarm01", "upperleg01", "neck01"), 0.016, g)
# crop top part of the sportsuit removed (the gown covers the torso); leggings stay
def strip_top(rig_name, cloth):
    C = bpy.data.objects[rig_name + "." + cloth]; rig = bpy.data.objects[rig_name]; bones = {b.name for b in rig.data.bones}
    gi = {g.index: g.name for g in C.vertex_groups}
    bm = bmesh.new(); bm.from_mesh(C.data); dl = bm.verts.layers.deform.active; kill = []
    for v in bm.verts:
        bw = {gi[k]: w for k, w in v[dl].items() if gi[k] in bones}
        if bw and max(bw, key=bw.get).startswith(("spine", "breast", "clavicle", "shoulder", "upperarm", "neck")): kill.append(v)
    bmesh.ops.delete(bm, geom=kill, context='VERTS'); bm.to_mesh(C.data); bm.free(); print("STRIPTOP", len(kill))
strip_top("Patient", "female_sportsuit01")
# dark brown hair for the patient
for n in ("Patient.ponytail01", "Patient.eyebrow001"):
    tint(bpy.data.objects[n].data.materials[0], (0.16, 0.09, 0.05), 1.0)
# ---- doctor: bare hands (no gloves on the ward), navy skirt
D = bpy.data.objects["Doctor.body"]
for p in D.data.polygons: p.material_index = 0
while len(D.data.materials) > 1: D.data.materials.pop(index=1)
# ---- surgeon & nurse already in teal scrubs + caps + masks
# ---- girl: part the fringe (remove the bob's front cards that hang over the eyes)
G = bpy.data.objects["Girl"]; hb = bpy.data.objects["Girl.bob01"]
ey = G.data.bones["eye.L"].head_local; hc = G.data.bones["head"].head_local
bm = bmesh.new(); bm.from_mesh(hb.data)
kill = [v for v in bm.verts if v.co.y < ey.y + 0.025 and v.co.z < ey.z + 0.045 and abs(v.co.x) < 0.085]
bmesh.ops.delete(bm, geom=kill, context='VERTS'); bm.to_mesh(hb.data); bm.free(); print("FRINGE", len(kill), tuple(ey))
# ---- girl: blue outfit
tint(bpy.data.objects["Girl.female_casualsuit01"].data.materials[0], (0.25, 0.42, 0.95), 1.0)
bpy.ops.wm.save_as_mainfile(filepath=out, compress=True)
