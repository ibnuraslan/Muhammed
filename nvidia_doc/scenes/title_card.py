"""Chapter title as part of the 3D shot: a camera-parented plane carrying a generated RGBA image
(small 'CHAPTER 1' over a bold slab-serif title with a soft glow). Its fade is a frame-driven driver, so it
plays in any render of the .blend with no scripts."""
import os, math
import numpy as np
import bpy
import skia
from scipy.ndimage import gaussian_filter

FONTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "fonts")
GEN = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "generated")


def title_image(small, big, path, W=1920, H=816):
    s = skia.Surface(W, H); c = s.getCanvas(); c.clear(skia.Color4f(0, 0, 0, 0))
    p = skia.Paint(AntiAlias=True); p.setColor4f(skia.Color4f(1, 1, 1, 1))
    f_big = skia.Font(skia.Typeface.MakeFromFile(os.path.join(FONTS, "RobotoSlab-ExtraBold.ttf")), 112)
    f_small = skia.Font(skia.Typeface.MakeFromFile(os.path.join(FONTS, "RobotoSlab-Bold.ttf")), 34)
    big = big.upper(); small = small.upper()
    wb = f_big.measureText(big); ws = sum(f_small.measureText(ch) for ch in small) + 9 * (len(small) - 1)
    x = W / 2 - ws / 2
    for ch in small:                                  # letter-spaced chapter number
        c.drawString(ch, x, H / 2 - 70, f_small, p); x += f_small.measureText(ch) + 9
    c.drawString(big, W / 2 - wb / 2, H / 2 + 50, f_big, p)
    a = s.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType).astype(np.float32) / 255
    alpha = a[..., 3]
    glow = gaussian_filter(alpha, 18) * 0.55 + gaussian_filter(alpha, 5) * 0.35
    out = np.zeros_like(a)
    out[..., :3] = np.array([1.0, 0.97, 0.92])
    out[..., 3] = np.clip(alpha + glow * (1 - alpha), 0, 1)
    from PIL import Image
    Image.fromarray((out * 255).astype(np.uint8), "RGBA").save(path)
    return path


def add_title(cam, small, big, f_in, f_out, fade=12, name="ChapterTitle"):
    """Plane in front of the camera filling the frame; fades in at f_in, out at f_out (frames)."""
    os.makedirs(GEN, exist_ok=True)
    path = title_image(small, big, os.path.join(GEN, f"{name}.png"))
    m = bpy.data.materials.new(name); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; N.clear()
    out = N.new("ShaderNodeOutputMaterial"); tc = N.new("ShaderNodeTexCoord")
    tex = N.new("ShaderNodeTexImage"); tex.image = bpy.data.images.load(path); tex.image.alpha_mode = 'STRAIGHT'
    L.new(tc.outputs['UV'], tex.inputs['Vector'])
    em = N.new("ShaderNodeEmission"); L.new(tex.outputs['Color'], em.inputs['Color']); em.inputs['Strength'].default_value = 1.0
    tr = N.new("ShaderNodeBsdfTransparent")
    fade_v = N.new("ShaderNodeValue"); fade_v.name = "Fade"
    mul = N.new("ShaderNodeMath"); mul.operation = 'MULTIPLY'; L.new(tex.outputs['Alpha'], mul.inputs[0]); L.new(fade_v.outputs[0], mul.inputs[1])
    mx = N.new("ShaderNodeMixShader"); L.new(mul.outputs[0], mx.inputs[0]); L.new(tr.outputs[0], mx.inputs[1]); L.new(em.outputs[0], mx.inputs[2])
    L.new(mx.outputs[0], out.inputs['Surface'])
    # driver: fade in over `fade` frames from f_in, out over `fade` frames before f_out (simple expression, no Python needed)
    d = fade_v.outputs[0].driver_add("default_value").driver
    d.type = 'SCRIPTED'
    d.expression = f"min(1, max(0, (frame - {f_in}) / {fade})) * min(1, max(0, ({f_out} - frame) / {fade}))"
    # a plane exactly covering the frame at distance 0.5 in front of the camera
    dist = 0.5
    cd = cam.data; sensor = cd.sensor_width
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, 0)); o = bpy.context.active_object; o.name = name
    o.data.materials.append(m)
    o.parent = cam; o.location = (0, 0, -dist)
    w = dist * sensor / cd.lens; h = w * 816 / 1920
    o.scale = (w, h, 1)
    # keep it sized to the lens if the lens animates
    for axis, k in ((0, 1.0), (1, 816 / 1920)):
        dd = o.driver_add("scale", axis).driver; dd.type = 'SCRIPTED'
        v = dd.variables.new(); v.name = "lens"; v.targets[0].id_type = 'CAMERA'; v.targets[0].id = cd; v.targets[0].data_path = "lens"
        dd.expression = f"{dist} * {sensor} / lens * {k}"
    o.visible_shadow = False; o.visible_diffuse = False; o.visible_glossy = False; o.visible_transmission = False
    return o
