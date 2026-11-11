"""The house look, as a compositor tree stored in each shot (so an external render comes out graded):
soft bloom, slight lens dispersion, vignette, gentle teal-shadow / warm-highlight balance. Film grain is added in the edit."""
import bpy


def _node(nt, kind, **inputs):
    n = nt.nodes.new(kind)
    for k, v in inputs.items():
        if k in n.inputs:
            n.inputs[k].default_value = v
    return n


def add_grade(scene, bloom=0.35, vignette=0.55):
    nt = bpy.data.node_groups.new("HouseGrade", "CompositorNodeTree")
    if hasattr(nt, "interface"):
        nt.interface.new_socket("Image", in_out='OUTPUT', socket_type='NodeSocketColor')
    rl = nt.nodes.new("CompositorNodeRLayers"); rl.scene = scene
    out = nt.nodes.new("NodeGroupOutput")
    glare = nt.nodes.new("CompositorNodeGlare")
    for attr, val in (("glare_type", 'FOG_GLOW'), ("quality", 'MEDIUM')):
        try:
            setattr(glare, attr, val)
        except Exception:
            pass
    for name, val in (("Type", 'Fog Glow'), ("Strength", bloom), ("Threshold", 0.9), ("Size", 0.6), ("Quality", 'Medium')):
        if name in glare.inputs:
            try:
                glare.inputs[name].default_value = val
            except Exception:
                pass
    lens = nt.nodes.new("CompositorNodeLensdist")
    for name, val in (("Dispersion", 0.012), ("Distortion", 0.0)):
        if name in lens.inputs:
            lens.inputs[name].default_value = val
    ell = nt.nodes.new("CompositorNodeEllipseMask")
    for name, val in (("Size", (0.95, 0.85)), ("Width", 0.95), ("Height", 0.85)):
        if name in ell.inputs:
            try:
                ell.inputs[name].default_value = val
            except Exception:
                pass
    blur = nt.nodes.new("CompositorNodeBlur")
    for name, val in (("Size", (300, 300)), ("Size X", 300), ("Size Y", 300)):
        if name in blur.inputs:
            try:
                blur.inputs[name].default_value = val
            except Exception:
                pass
    for attr in ("size_x", "size_y"):
        if hasattr(blur, attr):
            setattr(blur, attr, 300)
    vig = nt.nodes.new("ShaderNodeMix") if False else nt.nodes.new("CompositorNodeMixRGB") if hasattr(bpy.types, "CompositorNodeMixRGB") else nt.nodes.new("ShaderNodeMix")
    links = nt.links
    links.new(rl.outputs["Image"], glare.inputs["Image"])
    links.new(glare.outputs["Image"], lens.inputs["Image"])
    # vignette: image * mix(1 - vignette, 1, blurred ellipse)
    if vig.bl_idname == "ShaderNodeMix":
        vig.data_type = 'RGBA'; vig.blend_type = 'MULTIPLY'
        links.new(lens.outputs["Image"], vig.inputs[6])
        mr = nt.nodes.new("ShaderNodeMapRange"); mr.inputs['To Min'].default_value = 1.0 - vignette; mr.inputs['To Max'].default_value = 1.0
        links.new(ell.outputs[0], blur.inputs[0]); links.new(blur.outputs[0], mr.inputs['Value'])
        links.new(mr.outputs[0], vig.inputs[7]); vig.inputs['Factor'].default_value = 1.0
        vig_out = vig.outputs[2]
    else:
        vig.blend_type = 'MULTIPLY'
        links.new(lens.outputs["Image"], vig.inputs[1]); links.new(ell.outputs[0], blur.inputs[0])
        links.new(blur.outputs[0], vig.inputs[2]); vig_out = vig.outputs[0]
    cb = nt.nodes.new("CompositorNodeColorBalance")
    for name, val in (("Lift", (0.985, 1.0, 1.02, 1)), ("Gain", (1.03, 1.0, 0.97, 1))):
        if name in cb.inputs:
            try:
                cb.inputs[name].default_value = val
            except Exception:
                pass
    links.new(vig_out, cb.inputs["Image"])
    links.new(cb.outputs["Image"], out.inputs[0])
    scene.compositing_node_group = nt
    scene.render.use_compositing = True
    return nt
