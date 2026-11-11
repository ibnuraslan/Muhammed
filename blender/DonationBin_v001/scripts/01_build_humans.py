"""Five generic MPFB2 humans (MakeHuman CC0 assets).
blender -b --python 01_build_humans.py -- <out.blend>"""
import sys
import bpy
from bl_ext.user_default.mpfb.services.humanservice import HumanService
out = sys.argv[sys.argv.index("--") + 1]
for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob, do_unlink=True)

def tint(rig, cloth_key, rgb):
    for ch in rig.children:
        if ch.type == 'MESH' and cloth_key in ch.name:
            for m in ch.data.materials:
                for nd in list(m.node_tree.nodes):
                    if nd.type == 'TEX_IMAGE' and nd.image and "diffuse" in nd.image.name.lower():
                        for lk in list(nd.outputs['Color'].links):
                            mx = m.node_tree.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'
                            mx.inputs['Factor'].default_value = 1.0; mx.inputs['B'].default_value = rgb + (1,)
                            m.node_tree.links.new(nd.outputs['Color'], mx.inputs['A']); m.node_tree.links.new(mx.outputs['Result'], lk.to_socket)

def human(name, gender, age, race, hair, clothes, skin, x, weight=0.5, height=0.5, muscle=0.5, subdiv=1, brow="eyebrow001"):
    info = HumanService._create_default_human_info_dict()
    info["name"] = name
    info["phenotype"] = {"gender": gender, "age": age, "muscle": muscle, "weight": weight, "proportions": 0.6,
                         "height": height, "cupsize": 0.5, "firmness": 0.5, "race": race}
    info["rig"] = "default"
    info["eyes"] = "high-poly/high-poly.mhclo"; info["eyebrows"] = brow + "/" + brow + ".mhclo"
    info["eyelashes"] = "eyelashes01/eyelashes01.mhclo"; info["teeth"] = "teeth_base/teeth_base.mhclo"
    info["tongue"] = "tongue01/tongue01.mhclo"; info["hair"] = hair
    info["clothes"] = clothes
    info["skin_mhmat"] = skin; info["skin_material_type"] = "ENHANCED_SSS"; info["eyes_material_type"] = "PROCEDURAL_EYES"
    st = HumanService.get_default_deserialization_settings(); st["subdiv_levels"] = subdiv
    HumanService.deserialize_from_dict(info, st)
    rig = bpy.data.objects[name]; rig.location.x = x
    return rig

W = human("Woman", 0.0, 0.55, {"asian": 0.1, "caucasian": 0.8, "african": 0.1}, "bob02/bob02.mhclo",
          ["female_casualsuit01/female_casualsuit01.mhclo", "shoes02/shoes02.mhclo"], "middleage_caucasian_female/middleage_caucasian_female.mhmat", 0, weight=0.5, height=0.45, brow="eyebrow002")
import os
NOLOGO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "textures", "female_casualsuit01_diffuse_nologo.jpg")
for ch in W.children:     # plain tee: the stock texture's logo and piping are painted out (see textures/)
    if "casualsuit01" in ch.name:
        for m in ch.data.materials:
            for nd in m.node_tree.nodes:
                if nd.type == 'TEX_IMAGE' and nd.image and "diffuse" in nd.image.name.lower():
                    nd.image = bpy.data.images.load(os.path.abspath(NOLOGO))
S = human("Shover", 1.0, 0.4, {"asian": 0.2, "caucasian": 0.6, "african": 0.2}, "short02/short02.mhclo",
          ["male_casualsuit03/male_casualsuit03.mhclo", "shoes01/shoes01.mhclo"], "young_caucasian_male/young_caucasian_male.mhmat", 2, subdiv=0)
tint(S, "casualsuit03", (0.18, 0.18, 0.2))
P = human("Passerby", 1.0, 0.6, {"asian": 0.1, "caucasian": 0.2, "african": 0.7}, "short01/short01.mhclo",
          ["male_casualsuit01/male_casualsuit01.mhclo", "shoes03/shoes03.mhclo"], "middleage_african_male/middleage_african_male.mhmat", 4, weight=0.6, subdiv=0)
for nm, x, race, skin, hair in (("FireA", 6, {"asian": 0.05, "caucasian": 0.9, "african": 0.05}, "young_caucasian_male/young_caucasian_male.mhmat", "short04/short04.mhclo"),
                                ("FireB", 8, {"asian": 0.7, "caucasian": 0.2, "african": 0.1}, "young_asian_male/young_asian_male.mhmat", "short03/short03.mhclo")):
    F = human(nm, 1.0, 0.45, race, skin=skin, hair=hair, clothes=["male_worksuit01/male_worksuit01.mhclo", "shoes06/shoes06.mhclo"], x=x, muscle=0.7, weight=0.6, height=0.6, subdiv=0)
    tint(F, "worksuit01", (0.55, 0.42, 0.2)); tint(F, "shoes06", (0.06, 0.06, 0.06))
for ob in bpy.data.objects:
    if ob.type == 'ARMATURE':
        print("HUMAN", ob.name, [c.name for c in ob.children], tuple(round(d, 2) for d in ob.dimensions))
bpy.ops.wm.save_as_mainfile(filepath=out)
