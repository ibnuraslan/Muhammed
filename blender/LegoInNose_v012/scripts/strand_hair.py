"""v012: real strand hair (client: 'helmet hair'). For each MPFB character a curves layer is grown from the scalp of the
deformed body (geometry nodes, follows every head move) over the existing hair cards, rendered as Cycles curves with a
Principled Hair BSDF. blender -b in.blend --python strand_hair.py -- out.blend [only=Name]"""
import bpy, sys, math
from mathutils import Vector
a = sys.argv[sys.argv.index("--") + 1:]; OUT = a[0]; ONLY = next((x.split("=")[1] for x in a if x.startswith("only=")), None)
# name: (strand length m, density /m2, melanin, redness, comb back, lift, radius m)
CFG = {"Boy": (0.032, 130000, 0.8, 0.3, 0.9, 0.2, 0.00028), "Teen": (0.035, 130000, 0.82, 0.3, 0.9, 0.2, 0.00028),
       "Man": (0.035, 130000, 0.85, 0.25, 0.9, 0.2, 0.0003), "Mom": (0.05, 110000, 0.7, 0.6, 1.0, 0.05, 0.00026)}
def scalp_attr(body, arm):
    me = body.data; bones = set(arm.data.bones.keys()); gi = {g.index: g.name for g in body.vertex_groups if g.name in bones}
    hv = []
    for v in me.vertices:
        g = max((g for g in v.groups if g.group in gi), key=lambda g: g.weight, default=None)
        if g and gi.get(g.group, "").startswith("head"): hv.append(v)
    zs = [v.co.z for v in hv]; ys = [v.co.y for v in hv]; z0, z1 = min(zs), max(zs); y0, y1 = min(ys), max(ys)
    at = me.attributes.get("scalp") or me.attributes.new("scalp", "FLOAT", "POINT")
    vals = [0.0] * len(me.vertices); n = 0
    for v in hv:
        zt = (v.co.z - z0) / (z1 - z0); yt = (v.co.y - y0) / (y1 - y0)     # rest pose faces -Y: y0 = face front
        front = yt < 0.3
        if (zt > 0.62 and not (front and zt < 0.83)) or (zt > 0.5 and yt > 0.55):
            vals[v.index] = 1.0; n += 1
    at.data.foreach_set("value", vals); return n
def build(nm):
    L, DENS, MEL, RED, BACK, LIFT, RAD = CFG[nm]
    arm = bpy.data.objects[nm]; body = bpy.data.objects[nm + "_Body"]
    n = scalp_attr(body, arm)
    fr = bpy.data.objects.new("HairFrame_" + nm, None); bpy.context.scene.collection.objects.link(fr)
    fr.parent = arm; fr.parent_type = "BONE"; fr.parent_bone = "head"; fr.matrix_parent_inverse.identity()
    bpy.context.view_layer.update()
    # the frame's rotation = head rotation relative to rest: use the bone's rest matrix so local axes = rest world axes
    fr.matrix_world = arm.matrix_world @ arm.pose.bones["head"].matrix @ arm.data.bones["head"].matrix_local.inverted() if False else fr.matrix_world
    cv = bpy.data.hair_curves.new("HairHost_" + nm); host = bpy.data.objects.new("Hair_" + nm, cv); bpy.context.scene.collection.objects.link(host)   # a Curves object: Cycles renders GN curves only on these
    mat = bpy.data.materials.new("M_HairStrands_" + nm); mat.use_nodes = True; nt = mat.node_tree; nt.nodes.clear()
    hb = nt.nodes.new("ShaderNodeBsdfHairPrincipled"); hb.parametrization = "MELANIN"
    hb.inputs["Melanin"].default_value = MEL; hb.inputs["Melanin Redness"].default_value = RED; hb.inputs["Roughness"].default_value = 0.35
    o = nt.nodes.new("ShaderNodeOutputMaterial"); nt.links.new(hb.outputs[0], o.inputs["Surface"])
    g = bpy.data.node_groups.new("GN_StrandHair_" + nm, "GeometryNodeTree")
    g.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry"); g.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    N = g.nodes; Lk = g.links.new
    gin = N.new("NodeGroupInput"); gout = N.new("NodeGroupOutput")
    cards = [c for c in arm.children_recursive if c.type == "MESH" and any(k in c.name for k in ("short0", "ponytail", "bob0", "long0"))]
    src = cards[0] if cards else body
    oi = N.new("GeometryNodeObjectInfo"); oi.inputs["Object"].default_value = src; oi.transform_space = "RELATIVE"
    fi = N.new("GeometryNodeObjectInfo"); fi.inputs["Object"].default_value = fr; fi.transform_space = "ORIGINAL"
    sc_ = N.new("GeometryNodeInputNamedAttribute"); sc_.data_type = "FLOAT"; sc_.inputs["Name"].default_value = "scalp"
    dist = N.new("GeometryNodeDistributePointsOnFaces"); dist.distribute_method = "RANDOM"; dist.inputs["Density"].default_value = DENS
    Lk(oi.outputs["Geometry"], dist.inputs["Mesh"])
    if src is body: Lk(sc_.outputs["Attribute"], dist.inputs["Selection"])
    idx = N.new("GeometryNodeInputIndex")
    cap = N.new("GeometryNodeCaptureAttribute"); cap.domain = "POINT"
    try: cap.capture_items.new("INT", "pid"); cap.capture_items.new("VECTOR", "nrm"); cap.capture_items.new("VECTOR", "root")
    except Exception: pass
    Lk(dist.outputs["Points"], cap.inputs[0]); Lk(idx.outputs[0], cap.inputs["pid"]); Lk(dist.outputs["Normal"], cap.inputs["nrm"])
    pos0 = N.new("GeometryNodeInputPosition"); Lk(pos0.outputs[0], cap.inputs["root"])
    dup = N.new("GeometryNodeDuplicateElements"); dup.domain = "POINT"; dup.inputs["Amount"].default_value = 5
    Lk(cap.outputs[0], dup.inputs["Geometry"])
    # t = duplicate index / 4
    t = N.new("ShaderNodeMath"); t.operation = "DIVIDE"; t.inputs[1].default_value = 4.0; Lk(dup.outputs["Duplicate Index"], t.inputs[0])
    rnd = N.new("FunctionNodeRandomValue"); rnd.data_type = "FLOAT"; rnd.inputs["Min"].default_value = 0.6; rnd.inputs["Max"].default_value = 1.2
    Lk(cap.outputs["pid"], rnd.inputs["ID"])
    lenn = N.new("ShaderNodeMath"); lenn.operation = "MULTIPLY"; lenn.inputs[1].default_value = L; Lk(rnd.outputs["Value"], lenn.inputs[0])
    # head-space comb direction (back + down), rotated by the head frame
    back = N.new("FunctionNodeInputVector"); back.vector = (0.0, BACK, 0.12)      # combed back, slightly up: no fringe over the eyes
    rot = N.new("ShaderNodeVectorRotate"); rot.rotation_type = "EULER_XYZ"; Lk(back.outputs[0], rot.inputs["Vector"]); Lk(fi.outputs["Rotation"], rot.inputs["Rotation"])
    nl = N.new("ShaderNodeVectorMath"); nl.operation = "SCALE"; nl.inputs["Scale"].default_value = LIFT; Lk(cap.outputs["nrm"], nl.inputs[0])
    jit = N.new("FunctionNodeRandomValue"); jit.data_type = "FLOAT_VECTOR"; jit.inputs["Min"].default_value = (-0.2, -0.2, -0.2); jit.inputs["Max"].default_value = (0.2, 0.2, 0.2)
    Lk(cap.outputs["pid"], jit.inputs["ID"])
    dv0 = N.new("ShaderNodeVectorMath"); dv0.operation = "ADD"; Lk(nl.outputs[0], dv0.inputs[0]); Lk(rot.outputs[0], dv0.inputs[1])
    dirv = N.new("ShaderNodeVectorMath"); dirv.operation = "ADD"; Lk(dv0.outputs[0], dirv.inputs[0]); Lk(jit.outputs[0], dirv.inputs[1])
    dn = N.new("ShaderNodeVectorMath"); dn.operation = "NORMALIZE"; Lk(dirv.outputs[0], dn.inputs[0])
    # bend toward the scalp along the strand: lift fades with t (droop): offset = dir*len*t + nrm*len*0.15*t - nrm*len*0.25*t^2
    tl = N.new("ShaderNodeMath"); tl.operation = "MULTIPLY"; Lk(t.outputs[0], tl.inputs[0]); Lk(lenn.outputs[0], tl.inputs[1])
    off = N.new("ShaderNodeVectorMath"); off.operation = "SCALE"; Lk(dn.outputs[0], off.inputs[0]); Lk(tl.outputs[0], off.inputs["Scale"])
    t2 = N.new("ShaderNodeMath"); t2.operation = "MULTIPLY"; Lk(t.outputs[0], t2.inputs[0]); Lk(t.outputs[0], t2.inputs[1])
    dr = N.new("ShaderNodeMath"); dr.operation = "MULTIPLY"; Lk(t2.outputs[0], dr.inputs[0]); Lk(lenn.outputs[0], dr.inputs[1])
    dr2 = N.new("ShaderNodeMath"); dr2.operation = "MULTIPLY"; dr2.inputs[1].default_value = -0.55 if nm != "Mom" else -0.9; Lk(dr.outputs[0], dr2.inputs[0])
    dnv = N.new("ShaderNodeVectorMath"); dnv.operation = "SCALE"; Lk(cap.outputs["nrm"], dnv.inputs[0]); Lk(dr2.outputs[0], dnv.inputs["Scale"])
    lift0 = N.new("ShaderNodeVectorMath"); lift0.operation = "SCALE"; lift0.inputs["Scale"].default_value = 0.002; Lk(cap.outputs["nrm"], lift0.inputs[0])
    s1 = N.new("ShaderNodeVectorMath"); s1.operation = "ADD"; Lk(off.outputs[0], s1.inputs[0]); Lk(dnv.outputs[0], s1.inputs[1])
    s2 = N.new("ShaderNodeVectorMath"); s2.operation = "ADD"; Lk(s1.outputs[0], s2.inputs[0]); Lk(lift0.outputs[0], s2.inputs[1])
    s3 = N.new("ShaderNodeVectorMath"); s3.operation = "ADD"; Lk(s2.outputs[0], s3.inputs[0]); Lk(cap.outputs["root"], s3.inputs[1])
    sp = N.new("GeometryNodeSetPosition"); Lk(dup.outputs["Geometry"], sp.inputs["Geometry"]); Lk(s3.outputs[0], sp.inputs["Position"])
    p2c = N.new("GeometryNodePointsToCurves"); Lk(sp.outputs[0], p2c.inputs["Points"]); Lk(cap.outputs["pid"], p2c.inputs["Curve Group ID"]); Lk(dup.outputs["Duplicate Index"], p2c.inputs["Weight"])
    # radius: thin toward the tip
    sp_par = N.new("GeometryNodeSplineParameter")
    rr = N.new("ShaderNodeMapRange"); rr.inputs["From Min"].default_value = 0; rr.inputs["From Max"].default_value = 1; rr.inputs["To Min"].default_value = RAD; rr.inputs["To Max"].default_value = RAD * 0.3
    Lk(sp_par.outputs["Factor"], rr.inputs["Value"])
    scr = N.new("GeometryNodeSetCurveRadius"); Lk(p2c.outputs[0], scr.inputs["Curve"]); Lk(rr.outputs["Result"], scr.inputs["Radius"])
    sm = N.new("GeometryNodeSetMaterial"); sm.inputs["Material"].default_value = mat; Lk(scr.outputs[0], sm.inputs["Geometry"])
    Lk(sm.outputs[0], gout.inputs[0])
    cv.materials.append(mat)
    mod = host.modifiers.new("StrandHair", "NODES"); mod.node_group = g
    # host sits at the body's frame (relative transform space)
    host.parent = src; host.matrix_parent_inverse.identity()
    # visibility follows the character
    for src in (arm, body):
        ad = src.animation_data
        if ad and ad.action:
            for l in ad.action.layers:
                for st in l.strips:
                    for cb in st.channelbags:
                        for fc in cb.fcurves:
                            if fc.data_path == "hide_render":
                                for k in fc.keyframe_points:
                                    host.hide_render = bool(k.co.y); host.keyframe_insert("hide_render", frame=k.co.x)
    host.hide_render = body.hide_render if not (host.animation_data and host.animation_data.action) else host.hide_render
    for c in arm.children_recursive:              # the hair cards become a dark under-layer (shadow at the roots)
        if c.type == "MESH" and any(k in c.name for k in ("short0", "ponytail", "bob0", "long0")):
            for m in c.data.materials:
                hs = next((x for x in m.node_tree.nodes if x.type == "HUE_SAT"), None)
                if hs: hs.inputs["Value"].default_value = hs.inputs["Value"].default_value * 0.55
    print("HAIR", nm, "scalp verts", n)
for nm in CFG:
    if ONLY and nm != ONLY: continue
    build(nm)
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
