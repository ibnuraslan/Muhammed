"""v012b global fixes (director's 44-point list + RECURRING_FAULTS):
 - window view: one HDRI (no buildings->trees->snow change in a shot)       [26]
 - no blurred frames: f-stop >= 5.6 everywhere                               [11]
 - exposure lowered where washed out (teen, bench start, bed, sink)          [25]
 - removed: floating dream bricks + sparkles [12,13,D,E], the wall clock that read as a plate [21], the studio floor seam [17]
 - black square on the window bar: the vertical bar no longer shares the horizontal bar's plane [30]
 - teeth white [5]; eyes: a glossy cornea layer (catchlights) [3]; blinks every ~2.6 s on every character [3]
 - teen: a separate terracotta T-shirt over the jeans (no one-colour suit) [26]
 - cutaway: warm soft backdrop, pinker brain, no black hair cap [17]
blender -b in.blend --python v12_global.py -- out.blend"""
import bpy, sys
from mathutils import Vector
OUT = sys.argv[sys.argv.index("--") + 1]; sc = bpy.context.scene
def fcs(idb):
    ad = getattr(idb, "animation_data", None)
    return [fc for l in ad.action.layers for st in l.strips for cb in st.channelbags for fc in cb.fcurves] if ad and ad.action else []
# world: one HDRI
w = sc.world; nt = w.node_tree
if nt.animation_data: nt.animation_data_clear()
for n in nt.nodes:
    if n.type == "MIX_SHADER": n.inputs[0].default_value = 0.0
# DOF
cam = bpy.data.cameras["CAM_Film"]
for fc in fcs(cam):
    if fc.data_path == "dof.aperture_fstop":
        for k in fc.keyframe_points:
            k.co.y = max(k.co.y, 5.6); k.handle_left.y = max(k.handle_left.y, 5.6); k.handle_right.y = max(k.handle_right.y, 5.6)
        fc.update()
cam.dof.aperture_fstop = max(cam.dof.aperture_fstop, 5.6)
# exposure
ex = [fc for fc in fcs(sc) if fc.data_path == "view_settings.exposure"]
if ex:
    fc = ex[0]; base = {f: fc.evaluate(f) for f in range(1, 2037)}
    def dlt(f):
        for a, b, d in ((1195, 1300, -0.45), (1478, 1587, -0.7), (1587, 2036, -0.45)):
            if a <= f <= b: return d
        return 0.0
    for f in range(1190, 2037, 2): fc.keyframe_points.insert(f, base[f] + dlt(f), options={"FAST"})
    fc.update()
# hide
def hide(o):
    for x in [o] + list(o.children_recursive):
        if x.animation_data: x.animation_data_clear()
        x.hide_render = True; x.hide_viewport = True
for o in list(bpy.data.objects):
    if o.name.startswith(("Dream_", "FX_Sparkle")) or o.name in ("LR_WallClock", "Studio_Floor", "XS_Hair"): hide(o)
# window bars
vm = bpy.data.objects.get("LR_WindowM")
if vm: vm.location.y -= 0.004
for nm in ("LR_WindowL", "LR_WindowR"):
    o = bpy.data.objects.get(nm)
    if o: o.location.y -= 0.002
# teeth
for m in bpy.data.materials:
    if m.name.endswith("teeth_base") and m.node_tree:
        p = next((n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
        if p:
            for l in [l for l in m.node_tree.links if l.to_node == p and l.to_socket.name == "Base Color"]: m.node_tree.links.remove(l)
            p.inputs["Base Color"].default_value = (0.92, 0.9, 0.84, 1); p.inputs["Roughness"].default_value = 0.35
# catchlights: glossy cornea
g = bpy.data.node_groups["EnhancedEye"]; mx = g.nodes.get("CorneaTransparentMix")
if mx:
    tr = [l.from_node for l in g.links if l.to_node == mx and l.to_socket == mx.inputs[2]][0]
    gl = g.nodes.new("ShaderNodeBsdfGlossy"); gl.inputs["Roughness"].default_value = 0.03
    fr = g.nodes.new("ShaderNodeFresnel"); fr.inputs["IOR"].default_value = 1.6
    m2 = g.nodes.new("ShaderNodeMixShader"); g.links.new(fr.outputs[0], m2.inputs[0]); g.links.new(tr.outputs[0], m2.inputs[1]); g.links.new(gl.outputs[0], m2.inputs[2])
    g.links.new(m2.outputs[0], mx.inputs[2])
# blinks
nb = 0
for nm in ("Boy", "Teen", "Man", "Mom"):
    body = bpy.data.objects[nm + "_Body"]; kb = body.data.shape_keys
    if not kb: continue
    keys = [kb.key_blocks.get("expr_eye-left-slit"), kb.key_blocks.get("expr_eye-right-slit")]
    keys = [k for k in keys if k]
    if not keys: continue
    afc = {fc.data_path: fc for fc in fcs(kb)}
    for f0 in range(40 + 37 * ["Boy", "Teen", "Man", "Mom"].index(nm), 2036, 157):
        for k in keys:
            path = 'key_blocks["%s"].value' % k.name
            fc = afc.get(path)
            cur = (lambda f: fc.evaluate(f)) if fc else (lambda f: k.value)
            vals = {f0 - 2: cur(f0 - 2), f0: 1.0, f0 + 2: 1.0, f0 + 5: cur(f0 + 5)}
            for f, v in vals.items(): k.value = v; k.keyframe_insert("value", frame=f)
            afc = {fc.data_path: fc for fc in fcs(kb)}
        nb += 1
# teen T-shirt
te = bpy.data.objects["Teen_Teen.male_casualsuit02"]; gi = {g_.index: g_.name for g_ in te.vertex_groups}
vals = []
for v in te.data.vertices:
    gg = max(v.groups, key=lambda x: x.weight, default=None); n = gi.get(gg.group, "") if gg else ""
    vals.append(0.0 if n.startswith(("pelvis", "upperleg", "lowerleg", "foot", "toe")) else 1.0)
at = te.data.attributes.get("shirt") or te.data.attributes.new("shirt", "FLOAT", "POINT"); at.data.foreach_set("value", vals)
mt = te.data.materials[0]; tn = mt.node_tree; P = next(n for n in tn.nodes if n.type == "BSDF_PRINCIPLED")
bl = [l for l in tn.links if l.to_node == P and l.to_socket.name == "Base Color"][0]; src = bl.from_socket; tn.links.remove(bl)
att = tn.nodes.new("ShaderNodeAttribute"); att.attribute_name = "shirt"; col = tn.nodes.new("ShaderNodeRGB"); col.outputs[0].default_value = (0.55, 0.22, 0.12, 1)
mm = tn.nodes.new("ShaderNodeMix"); mm.data_type = "RGBA"; tn.links.new(att.outputs["Fac"], mm.inputs["Factor"]); tn.links.new(src, mm.inputs[6]); tn.links.new(col.outputs[0], mm.inputs[7])
tn.links.new(mm.outputs[2], P.inputs["Base Color"])
# cutaway backdrop + brain
sg = bpy.data.materials["M_StudioGradient"]
for n in sg.node_tree.nodes:
    if n.type == "VALTORGB":
        el = n.color_ramp.elements; el[0].color = (0.98, 0.9, 0.82, 1); el[-1].color = (0.82, 0.62, 0.55, 1)
    if n.type in ("EMISSION", "BACKGROUND") and "Color" in n.inputs and not n.inputs["Color"].is_linked: n.inputs["Color"].default_value = (0.95, 0.85, 0.78, 1)
br = bpy.data.materials["XS_Brain_M"]; pb = next((n for n in br.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
if pb:
    for l in [l for l in br.node_tree.links if l.to_node == pb and l.to_socket.name == "Base Color"]: br.node_tree.links.remove(l)
    pb.inputs["Base Color"].default_value = (0.86, 0.6, 0.62, 1)
print("GLOBAL done; blinks", nb)
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
