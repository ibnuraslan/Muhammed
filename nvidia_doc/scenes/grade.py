"""The house look, as a compositor tree stored in each shot (so an external render comes out graded):
soft bloom, slight lens dispersion, vignette, gentle teal-shadow / warm-highlight balance. Film grain is added in the edit.
Default look="cinematic" (Nov 2026): darker, contrasty, rolled-off highlights, teal blacks / amber highlights.
Pair it with the lighting recipe in look.py: the grade alone cannot put shadows into an evenly lit set."""
import math
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


def _sock(n, name, kind=None):
    """Input socket by name; Blender 5 nodes carry a float and a colour socket with the same name (ColorBalance
    'Lift', 'Gain', ...): kind='RGBA' picks the colour one."""
    for i in n.inputs:
        if i.name == name and (kind is None or i.type == kind):
            return i
    return None


def _mix(nt, blend, a, b_val=None, b_sock=None, fac=1.0):
    m = nt.nodes.new("ShaderNodeMix"); m.data_type = 'RGBA'; m.blend_type = blend; m.clamp_result = False
    m.inputs['Factor'].default_value = fac
    nt.links.new(a, m.inputs[6])
    if b_sock is not None:
        nt.links.new(b_sock, m.inputs[7])
    else:
        m.inputs[7].default_value = (*b_val, 1)
    return m.outputs[2]


def _math(nt, op, a, b=None, bv=None):
    m = nt.nodes.new("ShaderNodeMath"); m.operation = op; m.use_clamp = False
    nt.links.new(a, m.inputs[0])
    if b is not None:
        nt.links.new(b, m.inputs[1])
    elif bv is not None:
        m.inputs[1].default_value = bv
    return m.outputs[0]


# The cinematic look (Nov 2026). Every op works on scene-linear light, BEFORE the AgX view transform, so it holds
# for values above 1 (no clipping at 0.84 linear, which is what made the first test flat and grey).
CINE = dict(exposure=-0.35,      # stops; the darker mood comes mostly from the lighting recipe (look.py)
            contrast=1.18,       # power around mid-grey 0.18: deeper shadows, firmer mids
            knee=0.55, span=1.4,  # luminance shoulder: highlights roll off towards knee+span (AgX then soft-clips)
            black=(0.0016, 0.0006, 0.0),   # subtracted in linear: rich blacks, shadows lean teal
            warm=(1.06, 1.0, 0.9),         # multiplied: highlights and skin lean amber
            sat=0.8)


def _cinematic(nt, src, k=None):
    """Darker, denser, filmic: exposure down, contrast around mid-grey, rolled-off highlights, rich teal blacks,
    amber highlights, saturation down. Linear-light safe."""
    k = dict(CINE, **(k or {}))
    L = nt.links
    ex = nt.nodes.new("CompositorNodeExposure")
    # contrast c around pivot p: p * (x/p)^c = x^c * p^(1-c) -> fold p^(1-c) into the exposure
    ex.inputs['Exposure'].default_value = (k["exposure"] + (1 - k["contrast"]) * math.log2(0.18)) / k["contrast"]
    L.new(src, ex.inputs['Image'])
    g = nt.nodes.new("ShaderNodeGamma"); g.inputs['Gamma'].default_value = k["contrast"]
    L.new(ex.outputs['Image'], g.inputs['Color'])
    img = g.outputs['Color']
    # luminance shoulder: Y' = Y below the knee, knee + d/(1 + d/span) above it; scale RGB by Y'/Y (hue kept)
    bw = nt.nodes.new("CompositorNodeRGBToBW"); L.new(img, bw.inputs['Image'])
    y = bw.outputs['Val']
    d = _math(nt, 'MAXIMUM', _math(nt, 'SUBTRACT', y, bv=k["knee"]), bv=0.0)
    soft = _math(nt, 'DIVIDE', d, _math(nt, 'ADD', _math(nt, 'DIVIDE', d, bv=k["span"]), bv=1.0))
    y2 = _math(nt, 'ADD', _math(nt, 'MINIMUM', y, bv=k["knee"]), soft)
    ratio = _math(nt, 'DIVIDE', y2, _math(nt, 'MAXIMUM', y, bv=1e-5))
    img = _mix(nt, 'MULTIPLY', img, b_sock=ratio)
    img = _mix(nt, 'SUBTRACT', img, b_val=k["black"])
    img = _mix(nt, 'MULTIPLY', img, b_val=k["warm"])
    hs = nt.nodes.new("CompositorNodeHueSat"); hs.inputs['Saturation'].default_value = k["sat"]
    L.new(img, hs.inputs['Image'])
    return hs.outputs['Image']


def grade_file(src, dst, look="cinematic", **kw):
    """Grade a still on disk (look tests, preview sheets)."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    img = bpy.data.images.load(src)
    sc.render.resolution_x, sc.render.resolution_y = img.size
    sc.render.resolution_percentage = 100
    if src.lower().endswith(".exr"):         # scene-linear render: grade then AgX, exactly as in a real render
        sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Medium High Contrast'
        sc.view_settings.exposure = kw.pop("exposure", 0.0)
    else:                                    # an already display-referred PNG (rough preview only)
        sc.view_settings.view_transform = 'Standard'
    sc.render.image_settings.file_format = 'JPEG' if dst.lower().endswith((".jpg", ".jpeg")) else 'PNG'
    add_grade(sc, look=look, image=img, **kw)
    sc.render.filepath = dst
    bpy.ops.render.render(write_still=True)
    return dst


def add_grade(scene, bloom=0.35, vignette=None, look="cinematic", image=None, cine=None):
    """look="cinematic" (default from Nov 2026): the person wants every scene, day included, moody and filmic,
    never a bright plain 'normal camera' day: about half a stop darker, firmer contrast, less saturation,
    cooler shadows and warm highlights. look="plain" gives the original house grade.
    image: a bpy Image to grade instead of the render (for look tests on stills).
    vignette: None = 0.55 plain / 0.68 cinematic. cine: overrides for grade.CINE (per-shot tweaks).
    The grade cannot make shadows: light the set with look.py (one key, negative fill, dark walls)."""
    if cine is None and scene.get("look_cine"):
        import json
        cine = json.loads(scene["look_cine"])
    if vignette is None:
        vignette = 0.68 if look == "cinematic" else 0.55
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
        sk = _sock(cb, name, 'RGBA') or _sock(cb, name)
        try:
            sk.default_value = val
        except Exception:
            pass
    links.new(vig_out, cb.inputs["Image"])
    last = cb.outputs["Image"]
    if look == "cinematic":
        last = _cinematic(nt, last, cine)
    links.new(last, out.inputs[0])
    scene.compositing_node_group = nt
    scene.render.use_compositing = True
    return nt
