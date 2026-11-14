"""Readable eyes: MPFB's procedural EnhancedEye (blended cornea) renders as black holes here. Replace each
character's eye material with an opaque image-textured eye (white sclera, grey iris, dark pupil) + a thin clear coat."""
import bpy, os
EYE_TEX = os.path.expanduser("~/.config/blender/5.2/extensions/.user/user_default/mpfb/data/eyes/materials/grey_eye.png")
img = bpy.data.images.load(EYE_TEX, check_existing=True)
n = 0
for o in bpy.data.objects:
    if o.type != 'MESH' or not o.name.endswith(".high-poly"): continue
    m = bpy.data.materials.new(o.name + "_eye"); m.use_nodes = True; nt = m.node_tree
    b = nt.nodes["Principled BSDF"]; t = nt.nodes.new("ShaderNodeTexImage"); t.image = img
    nt.links.new(t.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.25; b.inputs["Coat Weight"].default_value = 0.6; b.inputs["Coat Roughness"].default_value = 0.03
    b.inputs["Specular IOR Level"].default_value = 0.6
    o.data.materials.clear(); o.data.materials.append(m); n += 1
print("EYES replaced", n)
