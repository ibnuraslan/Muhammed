"""ClosetBathroom: append 4 generic MPFB (CC0) characters from earlier studio packages, strip animation, hands back to skin,
recolour clothes/hair (non-skin solid colours, texture folds kept), eye fix.
blender -b --factory-startup --python 01_chars.py -- work/chars.blend"""
import bpy, sys, math
from mathutils import Vector
HERE = "/home/user/Muhammed/blender/ClosetBathroom_v001/"
exec(open(HERE + "scripts/00_lineup.py").read().split('if __name__')[0])
out = sys.argv[sys.argv.index("--") + 1]
CAST = [("BelugaRescue_v008", "SpecF", "Tom"), ("EarInArm_v011", "Surgeon", "Ray"),
        ("BellyFat_v007", "ShopperA", "Ken"), ("FanCancer_v011", "Doctor", "Doc")]
for o in list(bpy.data.objects): bpy.data.objects.remove(o)
for f, n, new in CAST:
    append(f, n, new)
for o in list(bpy.data.objects):
    if o.users_scene == (): bpy.data.objects.remove(o)

def tint_mat(m, top, bottom=None, split=None, a=0.72, b=0.38):
    """base colour = tint * (a + b * luminance(original)); bottom tint below generated-z split (rest-pose mesh)"""
    nt = m.node_tree; P = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    sock = P.inputs["Base Color"]
    src = sock.links[0].from_socket if sock.links else None
    for l in list(sock.links): nt.links.remove(l)
    rgb = nt.nodes.new("ShaderNodeRGB"); rgb.outputs[0].default_value = (*top, 1)
    tintsock = rgb.outputs[0]
    if bottom is not None:
        rb = nt.nodes.new("ShaderNodeRGB"); rb.outputs[0].default_value = (*bottom, 1)
        tc = nt.nodes.new("ShaderNodeTexCoord"); sp = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(tc.outputs["Generated"], sp.inputs[0])
        cmp = nt.nodes.new("ShaderNodeMath"); cmp.operation = 'GREATER_THAN'; cmp.inputs[1].default_value = split
        nt.links.new(sp.outputs["Z"], cmp.inputs[0])
        mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = 'RGBA'
        nt.links.new(cmp.outputs[0], mx.inputs["Factor"]); nt.links.new(rb.outputs[0], mx.inputs[6]); nt.links.new(rgb.outputs[0], mx.inputs[7])
        tintsock = mx.outputs[2]
    if src is not None:
        bw = nt.nodes.new("ShaderNodeRGBToBW"); nt.links.new(src, bw.inputs[0])
        ma = nt.nodes.new("ShaderNodeMath"); ma.operation = 'MULTIPLY_ADD'; ma.inputs[1].default_value = b; ma.inputs[2].default_value = a
        nt.links.new(bw.outputs[0], ma.inputs[0])
        mul = nt.nodes.new("ShaderNodeMix"); mul.data_type = 'RGBA'; mul.blend_type = 'MULTIPLY'; mul.inputs["Factor"].default_value = 1.0
        nt.links.new(tintsock, mul.inputs[6]); nt.links.new(ma.outputs[0], mul.inputs[7])
        nt.links.new(mul.outputs[2], sock)
    else:
        nt.links.new(tintsock, sock)
    P.inputs["Roughness"].default_value = max(0.55, P.inputs["Roughness"].default_value)

def split_z(rig, cloth, world_z):
    zs = [v.co.z for v in cloth.data.vertices]
    return (world_z - min(zs)) / (max(zs) - min(zs))

LOOK = {  # rig: {suffix: (top, bottom, split_world_z)}
    "Tom": {"male_casualsuit04": ((0.30, 0.62, 0.86), (0.13, 0.22, 0.42), None), "short01": ((0.20, 0.11, 0.06), None, None),
            "shoes01": ((0.75, 0.12, 0.12), None, None)},
    "Ray": {"male_casualsuit06": ((0.93, 0.92, 0.88), (0.16, 0.27, 0.50), None), "short02": ((0.55, 0.40, 0.22), None, None),
            "shoes05": ((0.45, 0.30, 0.18), None, None)},
    "Ken": {"male_casualsuit03": ((0.95, 0.78, 0.30), (0.20, 0.30, 0.48), None), "short02": ((0.72, 0.30, 0.10), None, None),
            "shoes03": ((0.12, 0.12, 0.13), None, None)},
    "Doc": {"female_elegantsuit01": ((0.95, 0.96, 0.97), (0.14, 0.18, 0.32), None), "ponytail01": ((0.12, 0.08, 0.05), None, None),
            "shoes02": ((0.15, 0.15, 0.17), None, None)},
}
for rn, d in LOOK.items():
    rig = bpy.data.objects[rn]
    waist = rig.data.bones["root"].head_local.z + 0.07
    body = bpy.data.objects[rn + ".body"]
    # gloves off: every face back to the skin slot
    for p in body.data.polygons:
        if p.material_index == 1 and len(body.data.materials) > 1 and "Glove" in (body.data.materials[1].name if body.data.materials[1] else ""):
            p.material_index = 0
    for suf, (top, bot, _) in d.items():
        o = bpy.data.objects[rn + "." + suf]
        m = o.data.materials[0].copy(); m.name = rn + "_" + suf; o.data.materials[0] = m
        if bot is not None:
            tint_mat(m, top, bot, split_z(rig, o, waist))
        elif "short" in suf or "pony" in suf:
            tint_mat(m, top, a=0.55, b=0.9)
        else:
            tint_mat(m, top)
    print("DRESSED", rn, "waist", round(waist, 3))
# eye fix (idempotent, every EnhancedEye group)
for ng in list(bpy.data.node_groups):
    if ng.name.startswith("EnhancedEye") and "CorneaTransparentMix" not in ng.nodes:
        src = open(HERE + "scripts/eye_fix.py").read().replace('bpy.data.node_groups["EnhancedEye"]', 'bpy.data.node_groups["%s"]' % ng.name)
        exec(src, {"bpy": bpy, "sys": sys, "_NO_SAVE": True})
    elif ng.name.startswith("EnhancedEye"): print("EYEFIX already", ng.name)
for i, n in enumerate(["Tom", "Ray", "Ken", "Doc"]):
    r = bpy.data.objects[n]; print("RIG", n, r.data.bones["head"].head_local.z, "root", r.data.bones["root"].head_local[:])
bpy.ops.wm.save_as_mainfile(filepath=out, compress=True)
