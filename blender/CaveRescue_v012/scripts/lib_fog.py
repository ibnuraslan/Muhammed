# CaveRescue v012: teal emission-gradient underwater fog (no volumes: fast, never murky-black).
# Every surface material gets the node group UW_Fog spliced in front of its Material Output:
#   out = mix(shader, emission(teal gradient), fac),  fac = CamUnder * smoothstep-ish(view distance 0.9 m -> 12 m) * 0.86
# The fog colour is a gradient: bright cyan-teal near the water line, deep blue-teal at depth (by world Z), so distance
# reads as clear teal water. CamUnder (a keyed Value in the group) is 1 only on frames where the camera is under water.
import bpy

def fog_group():
    g = bpy.data.node_groups.get("UW_Fog")
    if g: return g
    g = bpy.data.node_groups.new("UW_Fog", 'ShaderNodeTree')
    g.interface.new_socket("Shader", in_out='INPUT', socket_type='NodeSocketShader')
    g.interface.new_socket("Shader", in_out='OUTPUT', socket_type='NodeSocketShader')
    nt = g.nodes; L = g.links.new
    gi = nt.new("NodeGroupInput"); go = nt.new("NodeGroupOutput")
    cu = nt.new("ShaderNodeValue"); cu.name = "CamUnder"; cu.outputs[0].default_value = 0.0
    cd = nt.new("ShaderNodeCameraData")
    mr = nt.new("ShaderNodeMapRange"); mr.interpolation_type = 'SMOOTHERSTEP'
    mr.inputs["From Min"].default_value = 0.9; mr.inputs["From Max"].default_value = 12.0
    mr.inputs["To Min"].default_value = 0.0; mr.inputs["To Max"].default_value = 0.86
    L(cd.outputs["View Distance"], mr.inputs["Value"])
    m1 = nt.new("ShaderNodeMath"); m1.operation = 'MULTIPLY'; L(mr.outputs["Result"], m1.inputs[0]); L(cu.outputs[0], m1.inputs[1])
    geo = nt.new("ShaderNodeNewGeometry"); sp = nt.new("ShaderNodeSeparateXYZ"); L(geo.outputs["Position"], sp.inputs[0])
    zr = nt.new("ShaderNodeMapRange"); zr.inputs["From Min"].default_value = -6.5; zr.inputs["From Max"].default_value = 1.2
    L(sp.outputs["Z"], zr.inputs["Value"])
    cr = nt.new("ShaderNodeValToRGB"); E = cr.color_ramp.elements
    E[0].position = 0.0; E[0].color = (0.0, 0.16, 0.22, 1); E[1].position = 1.0; E[1].color = (0.07, 0.62, 0.64, 1)
    e = E.new(0.55); e.color = (0.02, 0.36, 0.42, 1)
    L(zr.outputs["Result"], cr.inputs["Fac"])
    em = nt.new("ShaderNodeEmission"); em.inputs["Strength"].default_value = 1.0; L(cr.outputs["Color"], em.inputs["Color"])
    ms = nt.new("ShaderNodeMixShader"); L(m1.outputs[0], ms.inputs["Fac"]); L(gi.outputs[0], ms.inputs[1]); L(em.outputs[0], ms.inputs[2])
    L(ms.outputs[0], go.inputs[0])
    return g

def apply_fog(skip_names=("M_Route", "M_Beacon", "M_Orb", "M_Rain")):
    g = fog_group(); n = 0
    for m in bpy.data.materials:
        if not m.node_tree or m.get("no_fog") or m.name in skip_names: continue
        nt = m.node_tree
        if any(nd.type == 'GROUP' and nd.node_tree == g for nd in nt.nodes): continue
        outs = [nd for nd in nt.nodes if nd.type == 'OUTPUT_MATERIAL' and nd.target in ('ALL', 'CYCLES')]
        for out in outs:
            sock = out.inputs["Surface"]
            if not sock.is_linked: continue
            lk = sock.links[0]; src = lk.from_socket
            gn = nt.nodes.new("ShaderNodeGroup"); gn.node_tree = g; gn.location = (out.location.x - 200, out.location.y)
            nt.links.remove(lk); nt.links.new(src, gn.inputs[0]); nt.links.new(gn.outputs[0], sock); n += 1
    return n

def key_cam_under(frames_under, f0, f1):
    """frames_under: set of frames where the camera is under water -> constant keys on the group's CamUnder value"""
    v = fog_group().nodes["CamUnder"].outputs[0]; prev = None
    for f in range(f0, f1 + 1):
        u = 1.0 if f in frames_under else 0.0
        if u != prev:
            v.default_value = u; v.keyframe_insert("default_value", frame=f); prev = u
    ad = fog_group().animation_data
    if ad and ad.action:
        for fc in iter_fcurves(ad.action):
            for kp in fc.keyframe_points: kp.interpolation = 'CONSTANT'
