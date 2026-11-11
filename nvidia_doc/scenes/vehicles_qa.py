"""Turntable QA sheet for vehicles.py: each vehicle at 3/4 front, side and 3/4 rear, soft overcast light.

  python vehicles_qa.py tile <kind> [variant] --out DIR [--pct 50] [--samples 32] [--dirt 0.2]
  python vehicles_qa.py sheet out.jpg DIR kind[:variant] ...
"""
import os, sys, math, subprocess
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
arg = lambda k, d: type(d)(sys.argv[sys.argv.index(k) + 1]) if k in sys.argv else d
ANGLES = (("3/4 front", 38), ("side", 90), ("3/4 rear", 142))


def tile(kind, variant, out, pct, samples, dirt):
    import bpy
    from mathutils import Vector
    from common import reset, camera
    import kit, ph, vehicles
    s = reset(res=kit.RES, samples=samples)
    s.render.resolution_percentage = pct
    ph.world_hdri("kloofendal_overcast", strength=0.9, rot_z=1.2, res="2k")
    # ground: light worn concrete with a soft contact shadow
    g = bpy.data.materials.new("Ground"); g.use_nodes = True
    p = g.node_tree.nodes["Principled BSDF"]; N = g.node_tree.nodes; L = g.node_tree.links
    n = N.new("ShaderNodeTexNoise"); n.inputs['Scale'].default_value = 0.6; n.inputs['Detail'].default_value = 8
    r = N.new("ShaderNodeValToRGB"); r.color_ramp.elements[0].color = (0.22, 0.22, 0.21, 1); r.color_ramp.elements[1].color = (0.33, 0.325, 0.31, 1)
    L.new(n.outputs['Fac'], r.inputs[0]); L.new(r.outputs[0], p.inputs['Base Color']); p.inputs['Roughness'].default_value = 0.85
    bpy.ops.mesh.primitive_plane_add(size=400); bpy.context.active_object.data.materials.append(g)
    v = vehicles.make(kind, variant=variant or None, dirt=dirt)
    bpy.context.view_layer.update()
    pts = [o.matrix_world @ Vector(c) for o in [v] + list(v.children_recursive) if o.type == 'MESH' for c in o.bound_box]
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), 0)); hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    c = (lo + hi) / 2; ext = max(hi.x - lo.x, hi.y - lo.y, (hi.z - lo.z) * 1.9)
    cam = camera((0, 0, 0), (0, 1, 0), lens=50)
    for k, (lab, az) in enumerate(ANGLES):
        d = ext * 1.55 + 2.0
        a = math.radians(az)
        cam.location = (c.x + d * math.cos(a), c.y + d * math.sin(a), 1.55 + (hi.z - lo.z) * 0.18)
        tgt = Vector((c.x, c.y, hi.z * 0.42))
        cam.rotation_euler = (tgt - cam.location).to_track_quat('-Z', 'Y').to_euler()
        s.render.filepath = os.path.join(out, f"{kind}{'_' + variant if variant else ''}_{k}.png")
        bpy.ops.render.render(write_still=True)


def sheet(path, d, items):
    from PIL import Image, ImageDraw, ImageFont
    ims = []
    for it in items:
        kind, _, var = it.partition(":")
        row = [Image.open(os.path.join(d, f"{kind}{'_' + var if var else ''}_{k}.png")).convert("RGB") for k in range(3)]
        ims.append((kind + (f" ({var})" if var else ""), row))
    w, h = ims[0][1][0].size; pad = 6; lab = 30
    S = Image.new("RGB", (3 * w + 4 * pad, len(ims) * (h + lab + pad) + pad + 34), (18, 19, 21))
    dr = ImageDraw.Draw(S)
    f = ImageFont.truetype("/usr/share/fonts/opentype/inter/Inter-SemiBold.otf", 20)
    dr.text((pad, 6), "vehicles.py v1 - turntable QA (Cycles, overcast HDRI for QA only)", fill=(220, 220, 220), font=f)
    y = 34
    for name, row in ims:
        dr.text((pad, y + 4), name, fill=(235, 200, 120), font=f)
        for k, im in enumerate(row):
            S.paste(im, (pad + k * (w + pad), y + lab))
            dr.text((pad + k * (w + pad) + 8, y + lab + 6), ANGLES[k][0], fill=(240, 240, 240), font=f)
        y += h + lab + pad
    S.save(path, quality=88)
    print("sheet", path, S.size)


if __name__ == "__main__":
    if sys.argv[1] == "tile":
        kind = sys.argv[2]; var = sys.argv[3] if len(sys.argv) > 3 and not sys.argv[3].startswith("--") else None
        out = arg('--out', "/tmp/vqa"); os.makedirs(out, exist_ok=True)
        tile(kind, var, out, arg('--pct', 50), arg('--samples', 32), arg('--dirt', 0.0))
    elif sys.argv[1] == "sheet":
        sheet(sys.argv[2], sys.argv[3], sys.argv[4:])
