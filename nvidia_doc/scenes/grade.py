"""The house look, as a compositor tree stored in each shot (so an external render comes out graded):
soft bloom, slight lens dispersion, vignette, gentle teal-shadow / warm-highlight balance. Film grain is added in the edit."""
import bpy


def _node(nt, kind, **inputs):
    n = nt.nodes.new(kind)
    for k, v in inputs.items():
        if k in n.inputs:
            n.inputs[k].default_value = v
    return n


def _set(n, name, val):
    if name in n.inputs:
        try:
            n.inputs[name].default_value = val
        except Exception:
            pass


def _cinematic(nt, src):
    """Darker, denser, filmic day: exposure down, S-curve with rolled-off highlights (no white walls),
    saturation down, teal shadows / amber highlights."""
    L = nt.links
    ex = nt.nodes.new("CompositorNodeExposure"); _set(ex, "Exposure", -0.8)
    L.new(src, ex.inputs["Image"])
    cv = nt.nodes.new("CompositorNodeCurveRGB")
    c = cv.mapping.curves[3]
    for (x, y), pt in zip([(0.0, 0.0), (1.0, 0.84)], c.points):
        pt.location = (x, y)
    for x, y in [(0.12, 0.035), (0.30, 0.15), (0.55, 0.38), (0.85, 0.71)]:
        c.points.new(x, y)
    cv.mapping.update()
    L.new(ex.outputs["Image"], cv.inputs["Image"])
    hs = nt.nodes.new("CompositorNodeHueSat"); _set(hs, "Saturation", 0.78)
    L.new(cv.outputs["Image"], hs.inputs["Image"])
    cb = nt.nodes.new("CompositorNodeColorBalance")
    _set(cb, "Lift", (0.92, 0.955, 1.0, 1)); _set(cb, "Gamma", (1.0, 0.99, 0.97, 1)); _set(cb, "Gain", (1.05, 1.0, 0.92, 1))
    L.new(hs.outputs["Image"], cb.inputs["Image"])
    return cb.outputs["Image"]


def grade_file(src, dst, look="cinematic", **kw):
    """Grade a still on disk (look tests, preview sheets)."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    img = bpy.data.images.load(src)
    sc.render.resolution_x, sc.render.resolution_y = img.size
    sc.render.resolution_percentage = 100
    sc.view_settings.view_transform = 'Standard'
    add_grade(sc, look=look, image=img, **kw)
    sc.render.filepath = dst
    bpy.ops.render.render(write_still=True)
    return dst


def add_grade(scene, bloom=0.35, vignette=0.55, look="cinematic", image=None):
    """look="cinematic" (default from Nov 2026): the person wants every scene, day included, moody and filmic,
    never a bright plain 'normal camera' day: about half a stop darker, firmer contrast, less saturation,
    cooler shadows and warm highlights. look="plain" gives the original house grade.
    image: a bpy Image to grade instead of the render (for look tests on stills)."""
    nt = bpy.data.node_groups.new("HouseGrade", "CompositorNodeTree")
    if hasattr(nt, "interface"):
        nt.interface.new_socket("Image", in_out='OUTPUT', socket_type='NodeSocketColor')
    if image is not None:
        rl = nt.nodes.new("CompositorNodeImage"); rl.image = image
    else:
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
    last = cb.outputs["Image"]
    if look == "cinematic":
        last = _cinematic(nt, last)
    links.new(last, out.inputs[0])
    scene.compositing_node_group = nt
    scene.render.use_compositing = True
    return nt
