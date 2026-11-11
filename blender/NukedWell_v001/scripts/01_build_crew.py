"""Six generic 1960s crew (MPFB2 + MakeHuman CC0). blender -b --python 01_build_crew.py -- <out.blend>"""
import sys
import bpy
from bl_ext.user_default.mpfb.services.humanservice import HumanService
out = sys.argv[sys.argv.index("--") + 1]
for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob, do_unlink=True)

def tint(rig, cloth_key, rgb):
    for ch in rig.children:
        if ch.type == 'MESH' and ch.name.split(".")[-1] == cloth_key:
            for m in ch.data.materials:
                for nd in list(m.node_tree.nodes):
                    if nd.type == 'TEX_IMAGE' and nd.image and "diffuse" in nd.image.name.lower():
                        for lk in list(nd.outputs['Color'].links):
                            hs = m.node_tree.nodes.new('ShaderNodeHueSaturation'); hs.inputs['Saturation'].default_value = 0.0; hs.inputs['Value'].default_value = 1.0
                            mx = m.node_tree.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'
                            mx.inputs['Factor'].default_value = 1.0; mx.inputs['B'].default_value = (*rgb, 1)
                            m.node_tree.links.new(nd.outputs['Color'], hs.inputs['Color']); m.node_tree.links.new(hs.outputs['Color'], mx.inputs['A'])
                            m.node_tree.links.new(mx.outputs['Result'], lk.to_socket)

def person(name, age, race, hair, clothes, skin, tintrgb, x, muscle=0.6, weight=0.5, height=0.55):
    info = HumanService._create_default_human_info_dict()
    info["name"] = name
    info["phenotype"] = {"gender": 1.0, "age": age, "muscle": muscle, "weight": weight, "proportions": 0.6,
                         "height": height, "cupsize": 0.5, "firmness": 0.5, "race": race}
    info["rig"] = "default"
    info["eyes"] = "high-poly/high-poly.mhclo"; info["eyebrows"] = "eyebrow001/eyebrow001.mhclo"
    info["eyelashes"] = "eyelashes01/eyelashes01.mhclo"; info["teeth"] = "teeth_base/teeth_base.mhclo"
    info["tongue"] = "tongue01/tongue01.mhclo"; info["hair"] = hair
    info["clothes"] = [clothes, "shoes03/shoes03.mhclo"]
    info["skin_mhmat"] = skin; info["skin_material_type"] = "ENHANCED_SSS"; info["eyes_material_type"] = "PROCEDURAL_EYES"
    st = HumanService.get_default_deserialization_settings(); st["subdiv_levels"] = 0
    HumanService.deserialize_from_dict(info, st)
    rig = bpy.data.objects[name]; rig.location.x = x
    tint(rig, clothes.split("/")[0], tintrgb)
    return rig

OLIVE = (0.30, 0.33, 0.17); KHAKI = (0.55, 0.47, 0.32); GREY = (0.36, 0.36, 0.34)
person("SolA", 0.45, {"asian": 0.6, "caucasian": 0.4, "african": 0.0}, "short02/short02.mhclo", "male_worksuit01/male_worksuit01.mhclo", "young_asian_male/young_asian_male.mhmat", OLIVE, 0)
person("SolB", 0.42, {"asian": 0.2, "caucasian": 0.8, "african": 0.0}, "short01/short01.mhclo", "male_worksuit01/male_worksuit01.mhclo", "young_caucasian_male/young_caucasian_male.mhmat", OLIVE, 2, height=0.6)
person("SolC", 0.48, {"asian": 0.8, "caucasian": 0.2, "african": 0.0}, "short03/short03.mhclo", "male_worksuit01/male_worksuit01.mhclo", "middleage_asian_male/middleage_asian_male.mhmat", OLIVE, 4, weight=0.6)
person("EngA", 0.7, {"asian": 0.1, "caucasian": 0.9, "african": 0.0}, "short04/short04.mhclo", "male_worksuit01/male_worksuit01.mhclo", "middleage_caucasian_male/middleage_caucasian_male.mhmat", KHAKI, 6)
person("EngB", 0.6, {"asian": 0.5, "caucasian": 0.5, "african": 0.0}, "short02/short02.mhclo", "male_worksuit01/male_worksuit01.mhclo", "middleage_asian_male/middleage_asian_male.mhmat", GREY, 8, weight=0.55)
person("SolD", 0.4, {"asian": 0.4, "caucasian": 0.6, "african": 0.0}, "short01/short01.mhclo", "male_worksuit01/male_worksuit01.mhclo", "young_caucasian_male2/young_caucasian_male2.mhmat", OLIVE, 10, height=0.5)
for ob in bpy.data.objects:
    if ob.type == 'ARMATURE':
        print("CREW", ob.name, [c.name for c in ob.children])
bpy.ops.wm.save_as_mainfile(filepath=out)
