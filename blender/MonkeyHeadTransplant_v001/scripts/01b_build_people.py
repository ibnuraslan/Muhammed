"""Surgeon + assistant (MPFB2 + MakeHuman CC0). blender -b --python scripts/01b_build_people.py -- build/people.blend
Both wear male_casualsuit01 tinted 1970s surgical green; caps/masks/gloves are added in 02."""
import sys
import bpy
from bl_ext.user_default.mpfb.services.humanservice import HumanService
out = sys.argv[sys.argv.index("--") + 1]
for ob in list(bpy.data.objects): bpy.data.objects.remove(ob, do_unlink=True)
def person(name, gender, age, race, skin, clothes, x, tint):
    info = HumanService._create_default_human_info_dict()
    info["name"] = name
    info["phenotype"] = {"gender": gender, "age": age, "muscle": 0.5, "weight": 0.5, "proportions": 0.6,
                         "height": 0.55 if gender > 0.5 else 0.45, "cupsize": 0.5, "firmness": 0.5, "race": race}
    info["rig"] = "default"
    info["eyes"] = "high-poly/high-poly.mhclo"; info["eyebrows"] = "eyebrow001/eyebrow001.mhclo"
    info["eyelashes"] = "eyelashes01/eyelashes01.mhclo"; info["teeth"] = "teeth_base/teeth_base.mhclo"
    info["tongue"] = "tongue01/tongue01.mhclo"; info["hair"] = ""
    info["clothes"] = clothes
    info["skin_mhmat"] = skin; info["skin_material_type"] = "ENHANCED_SSS"; info["eyes_material_type"] = "PROCEDURAL_EYES"
    st = HumanService.get_default_deserialization_settings(); st["subdiv_levels"] = 1
    HumanService.deserialize_from_dict(info, st)
    rig = bpy.data.objects[name]; rig.location.x = x
    for ch in rig.children:
        if ch.type == 'MESH' and ch.name.split(".")[-1] in [c.split("/")[0] for c in clothes] and "shoes" not in ch.name:
            for m in ch.data.materials:
                for nd in list(m.node_tree.nodes):
                    if nd.type == 'TEX_IMAGE' and nd.image and "diffuse" in nd.image.name.lower():
                        for lk in list(nd.outputs['Color'].links):
                            hs = m.node_tree.nodes.new('ShaderNodeHueSaturation'); hs.inputs['Saturation'].default_value = 0.0
                            mx = m.node_tree.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'
                            mx.inputs['Factor'].default_value = 1.0; mx.inputs['B'].default_value = tint
                            m.node_tree.links.new(nd.outputs['Color'], hs.inputs['Color']); m.node_tree.links.new(hs.outputs['Color'], mx.inputs['A'])
                            m.node_tree.links.new(mx.outputs['Result'], lk.to_socket)
    print("PERSON", name, [c.name for c in rig.children])
    return rig
person("Surgeon", 1.0, 0.55, {"asian": 0.1, "caucasian": 0.8, "african": 0.1}, "middleage_caucasian_male/middleage_caucasian_male.mhmat",
       ["male_casualsuit01/male_casualsuit01.mhclo", "shoes03/shoes03.mhclo"], 0, (0.42, 0.62, 0.52, 1))
person("Nurse", 0.0, 0.4, {"asian": 0.3, "caucasian": 0.4, "african": 0.3}, "young_african_female/young_african_female.mhmat",
       ["male_casualsuit01/male_casualsuit01.mhclo", "shoes03/shoes03.mhclo"], 1.5, (0.55, 0.72, 0.66, 1))
person("Anaes", 0.0, 0.6, {"asian": 0.7, "caucasian": 0.2, "african": 0.1}, "middleage_asian_female/middleage_asian_female.mhmat",
       ["male_casualsuit01/male_casualsuit01.mhclo", "shoes03/shoes03.mhclo"], 3.0, (0.42, 0.62, 0.52, 1))
bpy.ops.wm.save_as_mainfile(filepath=out)
print("SAVED", out)
