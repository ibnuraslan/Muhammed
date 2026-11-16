"""Cast: the diver (Worker from DrunkTrain_v007, re-dressed: bare chest, red swim trunks, barefoot) and two doctors
(VetA/VetB from ToucanBeak_v009, scrubs). The MakeHuman asset server was down (502), so we reuse our own CC0 MPFB
characters. Every rig gets fresh IK controls (anim_lib.make_human_ctrl), hand limits, an opened elbow limit and the eye fix.
blender -b --factory-startup -P 01_chars.py -- <repo>/blender out.blend"""
import bpy, bmesh, sys, os, math
from mathutils import Vector
a = sys.argv[sys.argv.index("--") + 1:]; ROOT, OUT = a[0], a[1]
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
exec(open(os.path.join(ROOT, "pipeline/anim_lib.py")).read())
exec(open(os.path.join(ROOT, "pipeline/hand_poses.py")).read())

def append_char(path, name, new):
    with bpy.data.libraries.load(path, link=False) as (src, dst):
        dst.objects = [n for n in src.objects if n == name or n.startswith(name + ".")]
    rig = next(o for o in dst.objects if o.type == 'ARMATURE')
    keep = [rig] + [o for o in dst.objects if o.type == 'MESH' and o.parent == rig]
    for o in dst.objects:
        if o not in keep: bpy.data.objects.remove(o)
    for o in keep: sc.collection.objects.link(o); o.hide_viewport = False; o.hide_set(False)
    rig.parent = None; rig.animation_data_clear(); rig.hide_viewport = rig.hide_render = False; rig.hide_set(False)
    for c in list(rig.constraints): rig.constraints.remove(c)
    for o in keep[1:]:
        o.animation_data_clear(); o.hide_render = o.hide_viewport = False
        o.name = new + "." + o.name.split(".", 1)[1]
    rig.name = new; rig.data.name = new + "_arm"
    bpy.context.view_layer.objects.active = rig
    for ob in bpy.context.selected_objects: ob.select_set(False)
    rig.select_set(True)
    bpy.ops.object.mode_set(mode='POSE')
    for pb in rig.pose.bones:
        for c in list(pb.constraints): pb.constraints.remove(c)
        pb.location = (0, 0, 0); pb.rotation_quaternion = (1, 0, 0, 0); pb.rotation_euler = (0, 0, 0); pb.scale = (1, 1, 1)
    bpy.ops.object.mode_set(mode='EDIT')
    for b in list(rig.data.edit_bones):
        if b.name.startswith(("IK_", "Pole_")): rig.data.edit_bones.remove(b)
    bpy.ops.object.mode_set(mode='OBJECT')
    rig.location = (0, 0, 0); rig.rotation_euler = (0, 0, 0); rig.scale = (1, 1, 1)
    return rig

BL = lambda f: os.path.join(ROOT, f)
diver = append_char(BL("DrunkTrain_v007/DrunkTrain_v007_60fps.blend"), "Worker", "Diver")
docM = append_char(BL("ToucanBeak_v009/ToucanBeak_v009_60fps.blend"), "VetB", "DocM")
docF = append_char(BL("ToucanBeak_v009/ToucanBeak_v009_60fps.blend"), "VetA", "DocF")

# ---- diver: strip the wetsuit and shoes, build red swim trunks from the body skin ----------------------------------
body = bpy.data.objects["Diver.body"]
for o in list(diver.children):
    if ("suit" in o.name and "worksuit" not in o.name) or "shoes" in o.name: bpy.data.objects.remove(o)
for m in list(body.modifiers):
    if m.type == 'MASK' and m.vertex_group.startswith("Delete.") and "worksuit" not in m.vertex_group: body.modifiers.remove(m)
BN = diver.data.bones
hip_z = BN["upperleg01.L"].head_local.z
top_z, bot_z = hip_z + 0.10, hip_z - 0.30
gi = {g.index: g.name for g in body.vertex_groups}
bone_names = set(b.name for b in BN)
keep = set()
bodyg = body.vertex_groups["body"].index
for v in body.data.vertices:
    if not any(g.group == bodyg and g.weight > 0.5 for g in v.groups): continue
    gs = [(gi[g.group], g.weight) for g in v.groups if gi[g.group] in bone_names]
    if not gs: continue
    dom = max(gs, key=lambda t: t[1])[0]
    if any(k in dom for k in ("arm", "wrist", "finger", "hand", "metacarpal", "clavicle", "shoulder")) or abs(v.co.x) > 0.3: continue
    if bot_z < v.co.z < top_z: keep.add(v.index)
tr = body.copy(); tr.data = body.data.copy(); tr.name = "Diver.trunks"; sc.collection.objects.link(tr); tr.parent = diver
bm = bmesh.new(); bm.from_mesh(tr.data)
bm.verts.ensure_lookup_table()
bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.index not in keep], context='VERTS')
for z, keep_side in ((top_z - 0.02, -1), (bot_z + 0.02, 1)):       # clean straight hems: bisect and drop the ragged band
    g = bm.verts[:] + bm.edges[:] + bm.faces[:]
    bmesh.ops.bisect_plane(bm, geom=g, plane_co=Vector((0, 0, z)), plane_no=Vector((0, 0, 1)), clear_outer=(keep_side < 0), clear_inner=(keep_side > 0))
for v in bm.verts: v.co += v.normal * 0.007
bm.to_mesh(tr.data); bm.free()
tr.data.materials.clear()
red = bpy.data.materials.new("Trunks_red"); red.use_nodes = True
rp = red.node_tree.nodes["Principled BSDF"]; rp.inputs['Base Color'].default_value = (0.75, 0.06, 0.05, 1); rp.inputs['Roughness'].default_value = 0.55
tr.data.materials.append(red)
for m in list(tr.modifiers):
    if m.type == 'MASK': tr.modifiers.remove(m)
so = tr.modifiers.new("Solidify", 'SOLIDIFY'); so.thickness = 0.004; so.offset = 1
print("TRUNKS verts", len(tr.data.vertices), "hip_z", round(hip_z, 3))

# ---- hospital shirt: his own fitted coverall (same body, so no clipping), cut at the hips, tinted pale blue ---------
shirt = next(o for o in diver.children if "worksuit" in o.name); shirt.name = "Diver.shirt"
cut_z = hip_z + 0.06
sbm = bmesh.new(); sbm.from_mesh(shirt.data)
if shirt.data.shape_keys: shirt.shape_key_clear()
bmesh.ops.bisect_plane(sbm, geom=sbm.verts[:] + sbm.edges[:] + sbm.faces[:], plane_co=Vector((0, 0, cut_z)), plane_no=Vector((0, 0, 1)), clear_inner=True)
bmesh.ops.bisect_plane(sbm, geom=sbm.verts[:] + sbm.edges[:] + sbm.faces[:], plane_co=Vector((0, 0, BN['neck01'].head_local.z - 0.015)), plane_no=Vector((0, 0, 1)), clear_outer=True)   # no standing collar
sbm.to_mesh(shirt.data); sbm.free()
# plain clean cloth (the source material carried alpha cut-outs and an earlier recolour chain)
nm_img = None
for m in shirt.data.materials:
    for nd in m.node_tree.nodes:
        if nd.type == 'TEX_IMAGE' and nd.image and "normal" in nd.image.name.lower(): nm_img = nd.image
sm = bpy.data.materials.new("Shirt_paleblue"); sm.use_nodes = True; P_ = sm.node_tree.nodes["Principled BSDF"]
P_.inputs['Base Color'].default_value = (0.56, 0.71, 0.86, 1); P_.inputs['Roughness'].default_value = 0.75; P_.inputs['Sheen Weight'].default_value = 0.3
if nm_img:
    ti_ = sm.node_tree.nodes.new('ShaderNodeTexImage'); ti_.image = nm_img; nm_img.colorspace_settings.name = 'Non-Color'
    nmn = sm.node_tree.nodes.new('ShaderNodeNormalMap'); nmn.inputs['Strength'].default_value = 0.5
    sm.node_tree.links.new(ti_.outputs['Color'], nmn.inputs['Color']); sm.node_tree.links.new(nmn.outputs['Normal'], P_.inputs['Normal'])
shirt.data.materials.clear(); shirt.data.materials.append(sm)
# the body mask under the coverall must not hide the legs any more: keep only the part above the cut
dg_ = body.vertex_groups.get("Delete.male_worksuit01")
if dg_:
    dg_.remove([v.index for v in body.data.vertices if v.co.z < cut_z + 0.02])
    mk = next(m for m in body.modifiers if m.type == 'MASK' and m.vertex_group == dg_.name); mk.name = "ShirtMask"
    mk.show_render = mk.show_viewport = False        # keyed on only in the hospital shots (04_anim)
print("SHIRT verts", len(shirt.data.vertices), "cut_z", round(cut_z, 3))

# ---- rigs: IK controls, hand limits, open elbows, eye fix ------------------------------------------------------------
for r in (diver, docM, docF):
    make_human_ctrl(r)
    add_hand_limits(r)
    for s in "LR":
        lo = r.pose.bones["lowerarm01." + s]
        lo.use_ik_limit_x = True; lo.ik_min_x = math.radians(-40); lo.ik_max_x = math.radians(100)
    r["char"] = 1
def eye_fix(g):
    """LegoInNose eye_fix.py (commit a44130b) as a function: cornea = Transparent BSDF mixed by the old transmission."""
    if any(n.name == "CorneaTransparentMix" for n in g.nodes): return "already"
    P = next(n for n in g.nodes if n.type == "BSDF_PRINCIPLED"); OUTN = next(n for n in g.nodes if n.type == "GROUP_OUTPUT")
    tl = [l for l in g.links if l.to_node == P and l.to_socket.name == "Transmission Weight"]
    src = tl[0].from_socket if tl else None
    for l in tl: g.links.remove(l)
    P.inputs["Transmission Weight"].default_value = 0.0
    ol = [l for l in g.links if l.from_node == P and l.to_node == OUTN][0]; out_sock = ol.to_socket; g.links.remove(ol)
    tr_ = g.nodes.new("ShaderNodeBsdfTransparent"); mx = g.nodes.new("ShaderNodeMixShader"); mx.name = "CorneaTransparentMix"
    if src: g.links.new(src, mx.inputs[0])
    else: mx.inputs[0].default_value = 0.0
    g.links.new(P.outputs[0], mx.inputs[1]); g.links.new(tr_.outputs[0], mx.inputs[2]); g.links.new(mx.outputs[0], out_sock)
    return "fixed"
for g in bpy.data.node_groups:
    if g.name.startswith("EnhancedEye"): print("EYEFIX", g.name, eye_fix(g))
docM.location.x = 2; docF.location.x = 4
for o in sc.objects: print("OB", o.name, o.type)
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print("CHARS_DONE", OUT)
