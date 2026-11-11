"""Beach crowd (MPFB2 + MakeHuman CC0). blender -b --python 01_build_people.py -- <out.blend>"""
import sys, bpy
from bl_ext.user_default.mpfb.services.humanservice import HumanService
out = sys.argv[sys.argv.index("--") + 1]
for ob in list(bpy.data.objects): bpy.data.objects.remove(ob, do_unlink=True)
A = {"asian": 0.85, "caucasian": 0.1, "african": 0.05}
C = {"asian": 0.05, "caucasian": 0.9, "african": 0.05}
PEOPLE = [  # name, gender, age, race, hair, clothes, shoes, skin, tint, height
    ("Fisher", 1.0, 0.62, A, "short02/short02.mhclo", "male_casualsuit03/male_casualsuit03.mhclo", "shoes01/shoes01.mhclo", "middleage_asian_male/middleage_asian_male.mhmat", (0.55, 0.45, 0.32), 0.45),
    ("LocalW", 0.0, 0.5, A, "long01/long01.mhclo", "female_casualsuit02/female_casualsuit02.mhclo", "shoes02/shoes02.mhclo", "young_asian_female/young_asian_female.mhmat", (0.75, 0.35, 0.3), 0.4),
    ("TouristM", 1.0, 0.55, C, "short04/short04.mhclo", "male_casualsuit02/male_casualsuit02.mhclo", "shoes04/shoes04.mhclo", "young_caucasian_male/young_caucasian_male.mhmat", (0.35, 0.55, 0.7), 0.6),
    ("TouristW", 0.0, 0.5, C, "ponytail01/ponytail01.mhclo", "female_sportsuit01/female_sportsuit01.mhclo", "shoes06/shoes06.mhclo", "young_caucasian_female/young_caucasian_female.mhmat", (0.95, 0.85, 0.6), 0.5),
    ("KidA", 1.0, 0.19, A, "short01/short01.mhclo", "male_casualsuit01/male_casualsuit01.mhclo", "shoes03/shoes03.mhclo", "young_asian_male/young_asian_male.mhmat", (0.85, 0.6, 0.2), 0.45),
    ("KidB", 0.0, 0.17, A, "bob01/bob01.mhclo", "female_casualsuit01/female_casualsuit01.mhclo", "shoes02/shoes02.mhclo", "young_asian_female/young_asian_female.mhmat", (0.4, 0.7, 0.55), 0.45),
    ("OldM", 1.0, 0.85, A, "short03/short03.mhclo", "male_casualsuit04/male_casualsuit04.mhclo", "shoes01/shoes01.mhclo", "old_asian_male/old_asian_male.mhmat", (0.9, 0.9, 0.85), 0.4),
    ("LocalM", 1.0, 0.45, {"asian": 0.6, "caucasian": 0.05, "african": 0.35}, "short02/short02.mhclo", "male_casualsuit05/male_casualsuit05.mhclo", "shoes03/shoes03.mhclo", "young_african_male/young_african_male.mhmat", (0.5, 0.3, 0.45), 0.55),
]
for i, (name, g, age, race, hair, clothes, shoes, skin, tint, h) in enumerate(PEOPLE):
    info = HumanService._create_default_human_info_dict(); info["name"] = name
    info["phenotype"] = {"gender": g, "age": age, "muscle": 0.5, "weight": 0.5, "proportions": 0.6, "height": h,
                         "cupsize": 0.5, "firmness": 0.5, "race": race}
    info["rig"] = "default"; info["eyes"] = "high-poly/high-poly.mhclo"; info["eyebrows"] = "eyebrow001/eyebrow001.mhclo"
    info["eyelashes"] = "eyelashes01/eyelashes01.mhclo"; info["teeth"] = "teeth_base/teeth_base.mhclo"; info["tongue"] = "tongue01/tongue01.mhclo"
    info["hair"] = hair; info["clothes"] = [clothes, shoes]; info["skin_mhmat"] = skin
    info["skin_material_type"] = "ENHANCED_SSS"; info["eyes_material_type"] = "PROCEDURAL_EYES"
    st = HumanService.get_default_deserialization_settings(); st["subdiv_levels"] = 1
    HumanService.deserialize_from_dict(info, st)
    rig = bpy.data.objects[name]; rig.location.x = i * 1.5
    for ch in rig.children:
        if ch.type == 'MESH' and ch.name.split(".")[-1] == clothes.split("/")[0]:
            for m in ch.data.materials:
                m = m.copy(); ch.data.materials[0] = m
                for nd in list(m.node_tree.nodes):
                    if nd.type == 'TEX_IMAGE' and nd.image and "diffuse" in nd.image.name.lower():
                        for lk in list(nd.outputs['Color'].links):
                            mx = m.node_tree.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'
                            mx.inputs['Factor'].default_value = 1.0; mx.inputs['B'].default_value = (*tint, 1)
                            m.node_tree.links.new(nd.outputs['Color'], mx.inputs['A']); m.node_tree.links.new(mx.outputs['Result'], lk.to_socket)
for ob in bpy.data.objects:
    if ob.type == 'ARMATURE': print("PERSON", ob.name, [c.name for c in ob.children], tuple(round(d, 2) for d in ob.dimensions))
bpy.ops.wm.save_as_mainfile(filepath=out)
