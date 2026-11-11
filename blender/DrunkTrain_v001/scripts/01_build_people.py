"""All humans for DrunkTrain (MPFB2 + MakeHuman CC0 assets).
blender -b --python 01_build_people.py -- <out.blend>"""
import sys
import bpy
from bl_ext.user_default.mpfb.services.humanservice import HumanService
out = sys.argv[sys.argv.index("--") + 1]
for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob, do_unlink=True)

def person(name, gender, age, race, hair, clothes, skin, x, muscle=0.5, weight=0.5, height=None, brows="eyebrow001"):
    info = HumanService._create_default_human_info_dict()
    info["name"] = name
    info["phenotype"] = {"gender": gender, "age": age, "muscle": muscle, "weight": weight, "proportions": 0.6,
                         "height": height if height is not None else (0.55 if gender > 0.5 else 0.45),
                         "cupsize": 0.5, "firmness": 0.5, "race": race}
    info["rig"] = "default"
    info["eyes"] = "high-poly/high-poly.mhclo"; info["eyebrows"] = brows + "/" + brows + ".mhclo"
    info["eyelashes"] = "eyelashes01/eyelashes01.mhclo"; info["teeth"] = "teeth_base/teeth_base.mhclo"
    info["tongue"] = "tongue01/tongue01.mhclo"; info["hair"] = hair
    info["clothes"] = clothes
    info["skin_mhmat"] = skin; info["skin_material_type"] = "ENHANCED_SSS"; info["eyes_material_type"] = "PROCEDURAL_EYES"
    st = HumanService.get_default_deserialization_settings(); st["subdiv_levels"] = 1
    HumanService.deserialize_from_dict(info, st)
    rig = bpy.data.objects[name]; rig.location.x = x
    print("PERSON", name, [c.name for c in rig.children])
    return rig

person("Lad", 1.0, 0.5, {"asian": 0.1, "caucasian": 0.8, "african": 0.1}, "short02/short02.mhclo",
       ["male_casualsuit06/male_casualsuit06.mhclo", "shoes05/shoes05.mhclo"], "young_caucasian_male/young_caucasian_male.mhmat", 0,
       muscle=0.45, weight=0.42, height=0.5)
person("WitA", 0.0, 0.45, {"asian": 0.15, "caucasian": 0.15, "african": 0.7}, "bob02/bob02.mhclo",
       ["female_elegantsuit01/female_elegantsuit01.mhclo", "shoes02/shoes02.mhclo"], "middleage_african_female/middleage_african_female.mhmat", 2,
       brows="eyebrow010")
person("WitB", 1.0, 0.7, {"asian": 0.6, "caucasian": 0.3, "african": 0.1}, "short04/short04.mhclo",
       ["male_casualsuit03/male_casualsuit03.mhclo", "shoes01/shoes01.mhclo"], "middleage_asian_male/middleage_asian_male.mhmat", 4,
       weight=0.62)
person("Worker", 1.0, 0.5, {"asian": 0.05, "caucasian": 0.35, "african": 0.6}, "short01/short01.mhclo",
       ["male_worksuit01/male_worksuit01.mhclo", "shoes04/shoes04.mhclo"], "middleage_african_male/middleage_african_male.mhmat", 6,
       muscle=0.65, weight=0.6)
bpy.ops.wm.save_as_mainfile(filepath=out)
