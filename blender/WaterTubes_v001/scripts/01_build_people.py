"""Hero homeowner + two neighbours (MPFB2 + MakeHuman CC0). blender -b --python 01_build_people.py -- <out.blend>"""
import sys, bpy
from bl_ext.user_default.mpfb.services.humanservice import HumanService
out = sys.argv[sys.argv.index("--") + 1]
for ob in list(bpy.data.objects): bpy.data.objects.remove(ob, do_unlink=True)
def person(name, gender, age, weight, race, hair, clothes, skin, x):
    info = HumanService._create_default_human_info_dict(); info["name"] = name
    info["phenotype"] = {"gender": gender, "age": age, "muscle": 0.55, "weight": weight, "proportions": 0.6,
                         "height": 0.55 if gender > 0.5 else 0.45, "cupsize": 0.5, "firmness": 0.5, "race": race}
    info["rig"] = "default"
    info["eyes"] = "high-poly/high-poly.mhclo"; info["eyebrows"] = "eyebrow001/eyebrow001.mhclo"
    info["eyelashes"] = "eyelashes01/eyelashes01.mhclo"; info["teeth"] = "teeth_base/teeth_base.mhclo"
    info["tongue"] = "tongue01/tongue01.mhclo"; info["hair"] = hair; info["clothes"] = clothes
    info["skin_mhmat"] = skin; info["skin_material_type"] = "ENHANCED_SSS"; info["eyes_material_type"] = "PROCEDURAL_EYES"
    st = HumanService.get_default_deserialization_settings(); st["subdiv_levels"] = 1
    HumanService.deserialize_from_dict(info, st)
    rig = bpy.data.objects[name]; rig.location.x = x
    print("PERSON", name, [c.name for c in rig.children])
person("Hero", 1.0, 0.55, 0.55, {"asian": 0.05, "caucasian": 0.85, "african": 0.1}, "short02/short02.mhclo",
       ["male_casualsuit02/male_casualsuit02.mhclo", "shoes01/shoes01.mhclo"], "middleage_caucasian_male/middleage_caucasian_male.mhmat", 0)
person("NeighbourA", 0.0, 0.5, 0.5, {"asian": 0.1, "caucasian": 0.8, "african": 0.1}, "bob01/bob01.mhclo",
       ["female_casualsuit02/female_casualsuit02.mhclo", "shoes03/shoes03.mhclo"], "middleage_caucasian_female/middleage_caucasian_female.mhmat", 2)
person("NeighbourB", 1.0, 0.7, 0.6, {"asian": 0.05, "caucasian": 0.1, "african": 0.85}, "short01/short01.mhclo",
       ["male_worksuit01/male_worksuit01.mhclo", "shoes03/shoes03.mhclo"], "old_african_male/old_african_male.mhmat", 4)
bpy.ops.wm.save_as_mainfile(filepath=out)
