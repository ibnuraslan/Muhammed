"""Cast for B36 from cast.blend (MPFB rigs re-used from delivered packages), re-dressed + eye fix + hand/elbow limits.
blender -b build/cast.blend --python 01_chars.py"""
import bpy, os, math
from mathutils import Vector
exec(open(os.path.dirname(__file__) + "/common.py").read())
exec(open(PIPE + "/hand_poses.py").read())
CAST = {"cHero": "Hero", "cWo": "PenLady", "cMan": "KnobMan", "cP2": "Camper", "cNB": "Worker", "cGa": "KegGuy",
        "cTeen": "SledGuy", "cSA": "VanGuy", "cJu": "Exec", "cSC": "Landlady", "cFi": "Rocker", "cCl": "Director", "cSt": "Mayor"}
dead = [o.name for o in bpy.data.objects if o.type == 'ARMATURE' and o.name not in CAST]
for n in dead:
    r = bpy.data.objects[n]
    for cn in [c.name for c in r.children_recursive]: bpy.data.objects.remove(bpy.data.objects[cn])
    bpy.data.objects.remove(r)
bpy.ops.outliner.orphans_purge(do_recursive=True)
for old, new in CAST.items(): bpy.data.objects[old].name = new

def clothes(rig, key):
    return [c for c in rig.children if key in c.name]

def region_attr(rig, me_obj, name="rc_top"):
    """color attribute: 1 on upper-body vertices (spine/arms/neck), 0 on legs/pelvis-down; from dominant bone weight"""
    gi = {g.index: g.name for g in me_obj.vertex_groups}
    bones = {b.name for b in rig.data.bones}
    me = me_obj.data
    if name in me.color_attributes: me.color_attributes.remove(me.color_attributes[name])
    a = me.color_attributes.new(name, 'FLOAT_COLOR', 'POINT')
    lab = []
    for v in me.vertices:
        gs = [g for g in v.groups if gi.get(g.group) in bones]
        b = gi[max(gs, key=lambda g: g.weight).group] if gs else ""
        lab.append(0.0 if any(k in b for k in ("leg", "foot", "toe", "pelvis", "root")) else 1.0)
    # whole connected pieces (shirt vs trousers) get one label: majority of their vertices (no colour band at the hem)
    import bmesh
    bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
    seen = [False] * len(bm.verts); n_isl = 0
    for v0 in bm.verts:
        if seen[v0.index]: continue
        stack = [v0]; isl = []; seen[v0.index] = True
        while stack:
            v = stack.pop(); isl.append(v.index)
            for e in v.link_edges:
                w = e.other_vert(v)
                if not seen[w.index]: seen[w.index] = True; stack.append(w)
        x = 1.0 if sum(lab[i] for i in isl) / len(isl) > 0.5 else 0.0
        for i in isl: a.data[i].color = (x, x, x, 1)
        n_isl += 1
    bm.free(); print("ISLANDS", me_obj.name, n_isl)
    return name

def recolor(rig, key, region, hue=0.5, sat=1.0, val=1.0, add=(0, 0, 0)):
    """insert HSV (+add) before the Principled base colour of the clothes material; region 'top'/'bottom'/'all'"""
    for ob in clothes(rig, key):
        attr = region_attr(rig, ob) if region != "all" else None
        for slot in ob.material_slots:
            m = slot.material.copy(); slot.material = m; nt = m.node_tree
            P = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
            lk = [l for l in nt.links if l.to_socket == P.inputs["Base Color"]]
            src = lk[0].from_socket if lk else None
            hsv = nt.nodes.new("ShaderNodeHueSaturation"); hsv.inputs["Hue"].default_value = hue
            hsv.inputs["Saturation"].default_value = sat; hsv.inputs["Value"].default_value = val
            if src: nt.links.new(src, hsv.inputs["Color"])
            else: hsv.inputs["Color"].default_value = P.inputs["Base Color"].default_value
            ad = nt.nodes.new("ShaderNodeMix"); ad.data_type = 'RGBA'; ad.blend_type = 'ADD'; ad.inputs[0].default_value = 1.0
            nt.links.new(hsv.outputs[0], ad.inputs[6]); ad.inputs[7].default_value = (*add, 1)
            out = ad.outputs[2]
            if attr:
                at = nt.nodes.new("ShaderNodeAttribute"); at.attribute_name = attr
                mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = 'RGBA'
                fac = at.outputs["Fac"]
                if region == "bottom":
                    inv = nt.nodes.new("ShaderNodeMath"); inv.operation = 'SUBTRACT'; inv.inputs[0].default_value = 1.0
                    nt.links.new(at.outputs["Fac"], inv.inputs[1]); fac = inv.outputs[0]
                nt.links.new(fac, mx.inputs[0])
                if src: nt.links.new(src, mx.inputs[6])
                else: mx.inputs[6].default_value = P.inputs["Base Color"].default_value
                nt.links.new(out, mx.inputs[7]); out = mx.outputs[2]
            nt.links.new(out, P.inputs["Base Color"])
            print("RECOLOR", rig.name, ob.name, m.name, region)

O = bpy.data.objects
recolor(O["Hero"], "casualsuit02", "top", hue=0.70, sat=1.25, val=0.85)            # blue sweater -> purple (jeans kept)
recolor(O["KegGuy"], "casualsuit03", "top", hue=0.80, sat=1.0, val=1.0)            # red stripes -> green stripes
recolor(O["Rocker"], "casualsuit05", "all", hue=0.5, sat=0.25, val=0.30)           # all dark: black jacket, dark jeans
recolor(O["Director"], "elegantsuit01", "all", hue=0.5, sat=1.0, val=1.0, add=(0.03, 0.06, 0.20))   # black suit -> navy
recolor(O["Exec"], "elegantsuit01", "all", hue=0.5, sat=1.0, val=1.0, add=(0.10, 0.10, 0.11))       # black -> charcoal grey
recolor(O["SledGuy"], "casualsuit02", "top", hue=0.0, sat=1.2, val=1.0)            # blue tee -> orange-red (winter)
recolor(O["Landlady"], "elegantsuit01", "top", hue=0.12, sat=1.0, val=1.0)          # red stripes -> blue stripes (vs PenLady)
recolor(O["Mayor"], "worksuit01", "bottom", hue=0.35, sat=0.9, val=0.8)            # overalls -> olive

# eye fix on every EnhancedEye group not yet fixed
for g in [g for g in bpy.data.node_groups if g.name.startswith("EnhancedEye")]:
    if any(n.name.startswith("CorneaTransparentMix") for n in g.nodes): continue
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
    print("EYEFIX", g.name)

for i, r in enumerate([o for o in O if o.type == 'ARMATURE']):
    if not any(c.type == 'LIMIT_ROTATION' for c in r.pose.bones["wrist.L"].constraints): add_hand_limits(r)
    for s in "LR":
        lo = r.pose.bones["lowerarm01." + s]; lo.use_ik_limit_x = True; lo.ik_min_x = math.radians(-40); lo.ik_max_x = math.radians(145)
    r.location = (i * 1.0, 40, 0)
    print("CHAR", r.name, [c.name for c in r.children])
bpy.ops.wm.save_as_mainfile(filepath=BUILD + "/chars.blend")
