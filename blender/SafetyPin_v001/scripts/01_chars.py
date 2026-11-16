"""Load finished MPFB characters from earlier packages, clean rigs, re-dress. blender -b --python 01_chars.py -- CID"""
import bpy, sys
exec(open("/home/user/Muhammed/blender/SafetyPin_v001/scripts/lib.py").read())
SPEC = {   # cid: (blend, donor)
    "Hunt":  (REPO + "BeethovenDeaf_v010/BeethovenDeaf_v010_60fps.blend", "Composer"),
    "Pal":   (REPO + "TitanicIceberg_v014/TitanicIceberg_v014_60fps.blend", "ExpertB"),
    "Buyer": (REPO + "PrisonKeyCake_v010/PrisonKeyCake_v010_60fps.blend", "President"),
}
cid = sys.argv[sys.argv.index("--") + 1]
bpy.ops.wm.read_factory_settings(use_empty=True)
src, donor = SPEC[cid]
if False:   # (tried: MPFB re-phenotype broke the refit) director: chest read as a bust -> MPFB re-phenotype (less muscle/weight), clothes and rig refitted
    exec(open("/home/user/Muhammed/blender/SafetyPin_v001/scripts/remake.py").read())
    remake(src, donor, donor, {"muscle": 0.35, "weight": 0.45})
    col_ = bpy.data.collections["CH_" + donor]; col_.name = "CH_" + cid
    objs = list(col_.objects); td = None
else:
    with bpy.data.libraries.load(src, link=False) as (fd, td):
        td.objects = [n for n in fd.objects if n == donor or n.startswith(donor + ".")]
    objs = [o for o in td.objects if o]
    col_ = bpy.data.collections.new("CH_" + cid); bpy.context.scene.collection.children.link(col_)
rig = bpy.data.objects[donor]
for o in objs:
    if o.type == 'EMPTY' or (o != rig and o.parent != rig): bpy.data.objects.remove(o); continue
    if o.name not in col_.objects: col_.objects.link(o)
    o.animation_data_clear()
    if o.type == 'MESH' and o.data.shape_keys: o.data.shape_keys.animation_data_clear()
    for c in list(o.constraints): o.constraints.remove(c)
    if o.type == 'MESH':
        for m in list(o.modifiers):
            if m.type not in ("ARMATURE", "MASK", "SUBSURF"): o.modifiers.remove(m)
for pb in rig.pose.bones:
    for c in list(pb.constraints): pb.constraints.remove(c)
    pb.location = (0, 0, 0); pb.rotation_quaternion = (1, 0, 0, 0); pb.rotation_euler = (0, 0, 0); pb.scale = (1, 1, 1)
rig.hide_viewport = False; rig.hide_set(False); bpy.context.view_layer.objects.active = rig; rig.select_set(True)
bpy.ops.object.mode_set(mode='EDIT')
for eb in list(rig.data.edit_bones):
    if eb.name.startswith(("IK_", "Pole_")): rig.data.edit_bones.remove(eb)
bpy.ops.object.mode_set(mode='OBJECT')
rig.location = (0, 0, 0); rig.rotation_euler = (0, 0, 0); rig.scale = (1, 1, 1)
for o in list(col_.objects):
    if o.name == donor: o.name = cid; o.data.name = cid
    elif o.name.startswith(donor + "."): o.name = cid + o.name[len(donor):]
    o.hide_render = False; o.hide_viewport = False

def recolor(rig, key, rgb, lo=0.22, hi=0.42, gain=2.2, all_=False):
    """recolour the DARK parts of a clothes texture (jacket/trousers) to rgb, keep light parts (shirt); all_=True: whole texture"""
    for ch in rig.children:
        if ch.type != 'MESH' or key not in ch.name: continue
        for i, m in enumerate(ch.data.materials):
            if not m: continue
            m = m.copy(); ch.data.materials[i] = m; nt = m.node_tree
            for nd in list(nt.nodes):
                if nd.type == 'TEX_IMAGE' and nd.image and "normal" not in nd.image.name.lower() and nd.outputs['Color'].links:
                    for lk in list(nd.outputs['Color'].links):
                        bw = nt.nodes.new('ShaderNodeRGBToBW'); nt.links.new(nd.outputs['Color'], bw.inputs[0])
                        mr = nt.nodes.new('ShaderNodeMapRange'); mr.inputs[1].default_value = lo; mr.inputs[2].default_value = hi
                        mr.inputs[3].default_value = 1.0; mr.inputs[4].default_value = 0.0; nt.links.new(bw.outputs[0], mr.inputs[0])
                        g = nt.nodes.new('ShaderNodeMath'); g.operation = 'MULTIPLY_ADD'; g.inputs[1].default_value = gain; g.inputs[2].default_value = 0.55; nt.links.new(bw.outputs[0], g.inputs[0])
                        cm = nt.nodes.new('ShaderNodeMix'); cm.data_type = 'RGBA'; cm.blend_type = 'MULTIPLY'; cm.inputs['Factor'].default_value = 1.0
                        nt.links.new(g.outputs[0], cm.inputs['A']); cm.inputs['B'].default_value = (*rgb, 1)
                        mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'
                        if all_: mx.inputs['Factor'].default_value = 1.0
                        else: nt.links.new(mr.outputs[0], mx.inputs['Factor'])
                        nt.links.new(nd.outputs['Color'], mx.inputs['A']); nt.links.new(cm.outputs['Result'], mx.inputs['B'])
                        nt.links.new(mx.outputs['Result'], lk.to_socket)

def set_tint(rig, key, node, rgb):
    for ch in rig.children:
        if ch.type == 'MESH' and key in ch.name:
            for m in ch.data.materials:
                n = m.node_tree.nodes[node]; print("TINT", m.name, node, n.blend_type, tuple(n.inputs[7].default_value))
                n.inputs[7].default_value = (*rgb, 1)

def hair(rig, rgb):
    for ch in rig.children:
        if ch.type == 'MESH' and any(k in ch.name for k in ("short0", "eyebrow")):
            for i, m in enumerate(ch.data.materials):
                if not m: continue
                m = m.copy(); ch.data.materials[i] = m; nt = m.node_tree
                for nd in list(nt.nodes):
                    if nd.type == 'TEX_IMAGE' and nd.image and "normal" not in nd.image.name.lower() and nd.outputs['Color'].links:
                        for lk in list(nd.outputs['Color'].links):
                            bw = nt.nodes.new('ShaderNodeRGBToBW'); nt.links.new(nd.outputs['Color'], bw.inputs[0])
                            g = nt.nodes.new('ShaderNodeMath'); g.operation = 'MULTIPLY'; g.inputs[1].default_value = 2.0; nt.links.new(bw.outputs[0], g.inputs[0])
                            cm = nt.nodes.new('ShaderNodeMix'); cm.data_type = 'RGBA'; cm.blend_type = 'MULTIPLY'; cm.inputs['Factor'].default_value = 1.0
                            nt.links.new(g.outputs[0], cm.inputs['A']); cm.inputs['B'].default_value = (*rgb, 1)
                            nt.links.new(cm.outputs['Result'], lk.to_socket)

if cid == "Hunt":     # 1840s inventor: charcoal frock-coat suit, grey waistcoat look kept, dark brown hair
    set_tint(rig, "elegantsuit", "Mix.002", (0.075, 0.075, 0.09))   # donor's red coat -> charcoal
    hair(rig, (0.16, 0.10, 0.06))
elif cid == "Pal":    # young friend: green jacket (reference), light shirt kept, blond hair
    # the Composer suit material keys its regions by channel (jacket / shirt / trim): green jacket, cream shirt
    with bpy.data.libraries.load(REPO + "BeethovenDeaf_v010/BeethovenDeaf_v010_60fps.blend", link=False) as (fd, td):
        td.materials = [n for n in fd.materials if n.startswith("Composer.male_elegantsuit01")][:1]
    sm = td.materials[0]; sm.name = "Pal_Suit"
    sm.node_tree.nodes["Mix"].inputs[7].default_value = (0.12, 0.34, 0.08, 1)      # jacket region
    sm.node_tree.nodes["Mix.001"].inputs[7].default_value = (0.86, 0.82, 0.72, 1)  # shirt region
    sm.node_tree.nodes["Mix.002"].inputs[7].default_value = (0.30, 0.20, 0.10, 1)  # tie stripes
    for ch in rig.children:
        if "elegantsuit" in ch.name:
            for i in range(len(ch.data.materials)): ch.data.materials[i] = sm
    hair(rig, (0.85, 0.70, 0.42))
elif cid == "Buyer":  # buyer: brown suit, dark hair
    recolor(rig, "elegantsuit", (0.42, 0.26, 0.14), gain=1.5)
# strip the donor film's x-ray (camera-distance transparency) shaders: BSDF straight to the output
for o in col_.objects:
    if o.type != 'MESH': continue
    for m in o.data.materials:
        if not m or not m.node_tree: continue
        nt = m.node_tree
        if not any(n.name.startswith("XRay") or n.label.startswith("XRay") for n in nt.nodes): continue
        out = next(n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL' and n.is_active_output) if any(n.type == 'OUTPUT_MATERIAL' and n.is_active_output for n in nt.nodes) else next(n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL')
        bsdf = next((n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'), None)
        if bsdf:
            nt.links.new(bsdf.outputs[0], out.inputs["Surface"]); print("XRAY_STRIPPED", o.name, m.name)
# donor aging hair material (grey) -> back to the textured hair material
for o in col_.objects:
    if o.type == 'MESH' and len(o.data.materials) > 1:
        good = next((m for m in o.data.materials if m and "Grey" not in m.name), None)
        for i, m in enumerate(o.data.materials):
            if m and "Grey" in m.name and good: o.data.materials[i] = good; print("GREY_SWAP", o.name)
# clear donor material animation (e.g. keyed skin fades) and force opaque skin/clothes
for o in col_.objects:
    if o.type != 'MESH': continue
    for m in o.data.materials:
        if not m or not m.node_tree: continue
        if m.node_tree.animation_data: m.node_tree.animation_data_clear(); print("MATANIM_CLEARED", o.name, m.name)
        if m.animation_data: m.animation_data_clear()
        for n in m.node_tree.nodes:
            if n.type == 'BSDF_PRINCIPLED' and not n.inputs["Alpha"].is_linked: n.inputs["Alpha"].default_value = 1.0
for o in bpy.data.objects: o.hide_render = False; o.hide_viewport = False
bpy.ops.outliner.orphans_purge(do_recursive=True)
bpy.ops.wm.save_as_mainfile(filepath=W + "ch_%s.blend" % cid, compress=True)
print("CHAR_OK", cid, sorted(o.name for o in col_.objects))
