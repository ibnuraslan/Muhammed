"""Singer gets the long01 hair (moved from the donor's head space into the singer's), black clothes; doctor in scrub blue;
fans tinted in clear non-skin colours. Every EnhancedEye group gets the cornea fix if it lacks it.
blender -b chars_raw.blend --python 02_chars_fix.py -- out.blend"""
import bpy, sys
from mathutils import Vector, Matrix
OUT = sys.argv[sys.argv.index("--") + 1]
D = bpy.data.objects
def rm(name):
    o = D.get(name)
    if o:
        for c in list(o.children): bpy.data.objects.remove(c, do_unlink=True)
        bpy.data.objects.remove(o, do_unlink=True)
S, H = D["Singer"], D["HairDonor"]
# head frame: head bone head + eye midpoint, scale from eye distance
def frame(r):
    B = r.data.bones; e = (B["eye.L"].head_local + B["eye.R"].head_local) / 2
    hd = B["head"].head_local; s = (B["eye.L"].head_local - B["eye.R"].head_local).length
    return hd, e, s
h0, e0, s0 = frame(H); h1, e1, s1 = frame(S)
k = s1 / s0 * 1.04
hair = D["HairDonor.long01"]
hair.parent = S
for v in hair.data.vertices:
    v.co = h1 + (v.co - h0) * k
for m in hair.modifiers:
    if m.type == 'ARMATURE': m.object = S
hair.name = "Singer.long01"
print("HAIR scale", round(k, 3), "eye dist", round(s0, 4), round(s1, 4))
rm("Singer.short02") if False else None
o = D.get("Singer.short02")
if o: bpy.data.objects.remove(o, do_unlink=True)
sh = D["Fan4.shoes03"].copy(); sh.data = sh.data.copy(); bpy.context.scene.collection.objects.link(sh)
F4 = D["Fan4"]
for v in sh.data.vertices:
    s_ = "L" if v.co.x > 0 else "R"
    a0 = F4.data.bones["foot." + s_].head_local; a1 = S.data.bones["foot." + s_].head_local
    l0 = (F4.data.bones["foot." + s_].head_local - F4.data.bones["toe1-1." + s_].head_local).length if "toe1-1." + s_ in F4.data.bones else 0.1
    l1 = (S.data.bones["foot." + s_].head_local - S.data.bones["toe1-1." + s_].head_local).length if "toe1-1." + s_ in S.data.bones else 0.1
    v.co = a1 + (v.co - a0) * (l1 / l0) * 1.03
sh.parent = S; sh.name = "Singer.shoes03"
for m in sh.modifiers:
    if m.type == 'ARMATURE': m.object = S
print("SHOES moved")
rm("HairDonor"); rm("Fan2")

def recolor(obj_name, rgb, rough=None, metal=None, spec=None):
    """multiply every base colour (texture or value) by rgb; optional roughness override"""
    o = D[obj_name]
    for slot in o.material_slots:
        m = slot.material
        if not m or not m.use_nodes or m.get("rc"): continue
        m = m.copy(); slot.material = m; m["rc"] = 1
        nt = m.node_tree
        for P in [n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED']:
            inp = P.inputs['Base Color']
            if inp.links:
                src = inp.links[0].from_socket
                mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs['Factor'].default_value = 1
                # desaturate first so the tint reads as a clean solid colour
                hsv = nt.nodes.new('ShaderNodeHueSaturation'); hsv.inputs['Saturation'].default_value = 0.0
                nt.links.new(src, hsv.inputs['Color']); nt.links.new(hsv.outputs['Color'], mx.inputs['A'])
                mx.inputs['B'].default_value = (*rgb, 1); nt.links.new(mx.outputs['Result'], inp)
            else:
                inp.default_value = (*rgb, 1)
            if rough is not None:
                for l in list(P.inputs['Roughness'].links): nt.links.remove(l)
                P.inputs['Roughness'].default_value = rough
            if spec is not None and 'Specular IOR Level' in P.inputs: P.inputs['Specular IOR Level'].default_value = spec
recolor("Singer.male_casualsuit04", (0.06, 0.06, 0.07), rough=0.55)      # black tee + black jeans
recolor("Singer.body", (1, 1, 1)) if False else None
# socks material on the body -> black boots look
for slot in D["Singer.body"].material_slots:
    if slot.material and slot.material.name.startswith("Sock"):
        m = slot.material.copy(); slot.material = m
        P = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
        for l in list(P.inputs['Base Color'].links): m.node_tree.links.remove(l)
        P.inputs['Base Color'].default_value = (0.03, 0.03, 0.035, 1); P.inputs['Roughness'].default_value = 0.35
recolor("Singer.long01", (0.95, 0.74, 0.48))
for m in [sl.material for sl in D["Singer.long01"].material_slots]:      # brighten to a dark-blond read (the texture is near black)
    nt = m.node_tree; P = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    if P.inputs['Base Color'].links:
        src = P.inputs['Base Color'].links[0].from_socket
        hv = nt.nodes.new('ShaderNodeHueSaturation'); hv.inputs['Value'].default_value = 3.2
        nt.links.new(src, hv.inputs['Color']); nt.links.new(hv.outputs['Color'], P.inputs['Base Color'])                                 # dark-blond hair
recolor("Doctor.male_worksuit01", (0.20, 0.42, 0.85), rough=0.6)             # scrub blue
for n, c in (("Fan1.male_casualsuit01", (0.85, 0.25, 0.2)), ("Fan3.male_casualsuit05", (0.2, 0.55, 0.3)), ("Fan4.male_worksuit01", (0.95, 0.75, 0.2))):
    recolor(n, c, rough=0.6)
# eye fix on any EnhancedEye group lacking it
for g in bpy.data.node_groups:
    if g.name.startswith("EnhancedEye") and not any(n.name.startswith("CorneaTransparentMix") for n in g.nodes):
        print("EYEFIX applying to", g.name)
        P = next(n for n in g.nodes if n.type == "BSDF_PRINCIPLED"); OUTN = next(n for n in g.nodes if n.type == "GROUP_OUTPUT")
        tl = [l for l in g.links if l.to_node == P and l.to_socket.name == "Transmission Weight"]; src = tl[0].from_socket if tl else None
        for l in tl: g.links.remove(l)
        P.inputs["Transmission Weight"].default_value = 0.0
        ol = [l for l in g.links if l.from_node == P and l.to_node == OUTN][0]; out_sock = ol.to_socket; g.links.remove(ol)
        tr = g.nodes.new("ShaderNodeBsdfTransparent"); mx = g.nodes.new("ShaderNodeMixShader"); mx.name = "CorneaTransparentMix"
        if src: g.links.new(src, mx.inputs[0])
        g.links.new(P.outputs[0], mx.inputs[1]); g.links.new(tr.outputs[0], mx.inputs[2]); g.links.new(mx.outputs[0], out_sock)
# real heights (the source packages had object-level scales that 01 reset): scale rig + children and apply
H_T = {"Singer": 1.80, "Doctor": 1.78, "Fan1": 1.74, "Fan3": 1.78, "Fan4": 1.70}
for n, ht in H_T.items():
    r = D[n]; top = r.data.bones["head"].tail_local.z; k = ht / top
    bpy.ops.object.select_all(action='DESELECT')
    r.scale = (k, k, k); r.select_set(True)
    for c in r.children: c.select_set(True)
    bpy.context.view_layer.objects.active = r
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    print("SCALE", n, round(k, 3), "head top", round(r.data.bones["head"].tail_local.z, 3),
          "body top", round(max((c.matrix_world @ v.co).z for c in r.children if c.name.endswith(".body") for v in c.data.vertices), 3))
for i, n in enumerate(["Singer", "Doctor", "Fan1", "Fan3", "Fan4"]): D[n].location.x = i * 1.2
bpy.ops.outliner.orphans_purge(do_recursive=True)
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
