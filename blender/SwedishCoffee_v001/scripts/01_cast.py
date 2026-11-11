"""Build the SwedishCoffee cast with MPFB2 (MakeHuman CC0).  blender -b --python 01_cast.py -- <out.blend>"""
import sys, bpy
from bl_ext.user_default.mpfb.services.humanservice import HumanService
out = sys.argv[sys.argv.index("--") + 1]
for ob in list(bpy.data.objects): bpy.data.objects.remove(ob, do_unlink=True)
CAU = {"asian": 0.02, "caucasian": 0.96, "african": 0.02}
def human(name, gender, age, hair, clothes, skin, x, muscle=0.5, weight=0.5, height=0.55, brow="eyebrow001", prop=0.6):
    info = HumanService._create_default_human_info_dict()
    info["name"] = name
    info["phenotype"] = {"gender": gender, "age": age, "muscle": muscle, "weight": weight, "proportions": prop,
                         "height": height, "cupsize": 0.5, "firmness": 0.5, "race": CAU}
    info["rig"] = "default"
    info["eyes"] = "high-poly/high-poly.mhclo"; info["eyebrows"] = brow + "/" + brow + ".mhclo"
    info["eyelashes"] = "eyelashes01/eyelashes01.mhclo"; info["teeth"] = "teeth_base/teeth_base.mhclo"
    info["tongue"] = "tongue01/tongue01.mhclo"; info["hair"] = hair
    info["clothes"] = clothes
    info["skin_mhmat"] = skin; info["skin_material_type"] = "ENHANCED_SSS"; info["eyes_material_type"] = "PROCEDURAL_EYES"
    st = HumanService.get_default_deserialization_settings(); st["subdiv_levels"] = 1
    HumanService.deserialize_from_dict(info, st)
    rig = bpy.data.objects[name]; rig.location.x = x
    print("CAST", name, [c.name for c in rig.children])
    return rig
H = lambda h: h + "/" + h + ".mhclo"
TW = dict(gender=1.0, height=0.55, muscle=0.45, weight=0.45, brow="eyebrow002")
human("TwinA", age=0.5, hair=H("short02"), clothes=[H("male_casualsuit01"), H("shoes02")], skin="young_caucasian_male/young_caucasian_male.mhmat", x=0, **TW)
human("TwinB", age=0.5, hair=H("short02"), clothes=[H("male_casualsuit01"), H("shoes02")], skin="young_caucasian_male/young_caucasian_male.mhmat", x=1, **TW)
human("TwinA_old", age=0.82, hair=H("short02"), clothes=[H("male_elegantsuit01"), H("shoes02")], skin="middleage_caucasian_male/middleage_caucasian_male.mhmat", x=2, **TW)
human("TwinB_old", age=0.82, hair=H("short02"), clothes=[H("male_elegantsuit01"), H("shoes02")], skin="middleage_caucasian_male/middleage_caucasian_male.mhmat", x=3, **TW)
human("TwinA_vold", age=1.0, hair=H("short02"), clothes=[H("male_elegantsuit01"), H("shoes02")], skin="old_caucasian_male/old_caucasian_male.mhmat", x=4, **TW)
human("King", 1.0, 0.68, "", [H("male_elegantsuit01"), H("shoes06")], "middleage_caucasian_male/middleage_caucasian_male.mhmat", 5, weight=0.7, brow="eyebrow004")
human("Guard", 1.0, 0.45, H("short04"), [H("male_worksuit01"), H("shoes03")], "young_caucasian_male2/young_caucasian_male2.mhmat", 6, muscle=0.7, height=0.6)
human("Doctor1", 1.0, 0.92, H("short03"), [H("male_elegantsuit01"), H("shoes06")], "old_caucasian_male/old_caucasian_male.mhmat", 7, weight=0.6, brow="eyebrow003")
human("Doctor2", 1.0, 0.88, "", [H("male_elegantsuit01"), H("shoes06")], "old_caucasian_male/old_caucasian_male.mhmat", 8, weight=0.4, brow="eyebrow005")
human("Woman", 0.0, 0.45, H("bob02"), [H("female_elegantsuit01"), H("shoes01")], "young_caucasian_female/young_caucasian_female.mhmat", 9, height=0.45)
human("Townsman", 1.0, 0.6, H("short01"), [H("male_casualsuit01"), H("shoes03")], "middleage_caucasian_male/middleage_caucasian_male.mhmat", 10, weight=0.6)
human("Townswoman", 0.0, 0.7, H("ponytail01"), [H("female_elegantsuit01"), H("shoes01")], "middleage_caucasian_female/middleage_caucasian_female.mhmat", 11, height=0.42)
bpy.ops.wm.save_as_mainfile(filepath=out)
