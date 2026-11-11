"""Make the X-ray films used on the lightboxes, from the real typewriter model:
every surface becomes a faint additive glow, so where the machine is dense (stacked metal) the film is white,
just as on a radiograph. Writes assets/generated/xray_<name>.png.

  PYTHONPATH=projects/typewriters/scenes:nvidia_doc/scenes python projects/typewriters/scenes/gen_xray.py
"""
import os, sys, math
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bpy
import numpy as np
from mathutils import Vector
from common import reset
import typewriter as T


def film(name, bugged, region=None, res=(1400, 1100)):
    s = reset(res=res, samples=16)
    s.view_settings.view_transform = 'Standard'; s.view_settings.look = 'None'
    s.world = bpy.data.worlds.new("Black"); s.world.use_nodes = True
    s.world.node_tree.nodes["Background"].inputs['Color'].default_value = (0, 0, 0, 1)
    tw = T.make("X", text=" ", bugged=bugged, glyphs=False, legends=False)
    tw["paper"].hide_render = True
    for o in tw["root"].children_recursive:
        if "_Foot" in o.name or "_PaperRest" in o.name:
            o.hide_render = True
    def xm(name, k):
        m = bpy.data.materials.new(name); m.use_nodes = True
        N = m.node_tree.nodes; L = m.node_tree.links; N.clear()
        out = N.new("ShaderNodeOutputMaterial"); tr = N.new("ShaderNodeBsdfTransparent"); em = N.new("ShaderNodeEmission")
        em.inputs['Strength'].default_value = k
        ad = N.new("ShaderNodeAddShader"); L.new(tr.outputs[0], ad.inputs[0]); L.new(em.outputs[0], ad.inputs[1]); L.new(ad.outputs[0], out.inputs['Surface'])
        return m
    plastic, metal, dense = xm("XPlastic", 0.012), xm("XMetal", 0.05), xm("XDense", 0.16)
    shell = set(o.name for o in tw["shell"])
    for o in [tw["root"]] + list(tw["root"].children_recursive):
        if o.type not in ('MESH', 'CURVE'):
            continue
        n = o.name
        mat = dense if ("Bug" in n or "Coil" in n or "Motor" in n) else (plastic if (n in shell or "_Key_" in n or "Glyph" in n or "_Knob" in n or "_Scale" in n) else metal)
        o.data = o.data.copy(); o.data.materials.clear(); o.data.materials.append(mat)
    s.cycles.transparent_max_bounces = 64; s.cycles.max_bounces = 64
    cam_d = bpy.data.cameras.new("Ortho"); cam_d.type = 'ORTHO'
    cx, cy, w = region or (0.0, -0.01, 0.46)
    cam_d.ortho_scale = w
    cam = bpy.data.objects.new("Ortho", cam_d); bpy.context.collection.objects.link(cam); s.camera = cam
    cam.location = (cx, cy, 1.0); cam.rotation_euler = (0, 0, 0)
    path = os.path.join(T.GEN, f"xray_{name}.png")
    s.render.filepath = path; s.render.image_settings.color_depth = '8'
    bpy.ops.render.render(write_still=True)
    # film look: slight blue base, soft edges, grain, a dark clear border
    from PIL import Image, ImageFilter
    im = np.asarray(Image.open(path).convert("L")).astype(np.float32) / 255
    im = np.clip(im, 0, 1) ** 0.8
    rng = np.random.default_rng(1)
    im = im + rng.normal(0, 0.025, im.shape)
    h, w_ = im.shape
    yy, xx = np.mgrid[0:h, 0:w_]
    vig = 1 - 0.35 * (((xx - w_ / 2) / (w_ / 2)) ** 2 + ((yy - h / 2) / (h / 2)) ** 2)
    im = np.clip(im * vig, 0, 1)
    rgb = np.stack([0.06 + 0.86 * im, 0.08 + 0.88 * im, 0.11 + 0.89 * im], -1)
    Image.fromarray((rgb * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.8)).save(path)
    print("[xray]", path, flush=True)
    return path


if __name__ == "__main__":
    film("altered", True)
    film("ordinary", False)
    film("motor", False, region=(-0.11, 0.1, 0.22))
