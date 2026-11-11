"""Build all MPFB2 humans for DwarfGiant.  blender -b --python 01_build_people.py -- <out.blend>"""
import sys, bpy
from bl_ext.user_default.mpfb.services.humanservice import HumanService
out = sys.argv[sys.argv.index("--") + 1]
for ob in list(bpy.data.objects): bpy.data.objects.remove(ob, do_unlink=True)

def human(name, gender=1.0, age=0.5, muscle=0.5, weight=0.5, height=0.5, race=(0.0, 1.0, 0.0), skin="young_caucasian_male",
          hair="short02/short02.mhclo", clothes=(), brows="eyebrow001/eyebrow001.mhclo", subdiv=0, prop=0.5):
    info = HumanService._create_default_human_info_dict()
    info["name"] = name
    info["phenotype"] = {"gender": gender, "age": age, "muscle": muscle, "weight": weight, "proportions": prop, "height": height,
                         "cupsize": 0.5, "firmness": 0.5, "race": {"asian": race[0], "caucasian": race[1], "african": race[2]}}
    info["rig"] = "default"
    info["eyes"] = "high-poly/high-poly.mhclo"; info["eyebrows"] = brows; info["eyelashes"] = "eyelashes01/eyelashes01.mhclo"
    info["teeth"] = "teeth_base/teeth_base.mhclo"; info["tongue"] = "tongue01/tongue01.mhclo"
    info["hair"] = hair; info["clothes"] = list(clothes)
    info["skin_mhmat"] = f"{skin}/{skin}.mhmat"; info["skin_material_type"] = "ENHANCED_SSS"; info["eyes_material_type"] = "PROCEDURAL_EYES"
    st = HumanService.get_default_deserialization_settings(); st["subdiv_levels"] = subdiv
    before = set(bpy.data.objects)
    HumanService.deserialize_from_dict(info, st)
    new = [o for o in bpy.data.objects if o not in before]
    col = bpy.data.collections.new("CH_" + name); bpy.context.scene.collection.children.link(col)
    for o in new:
        for c in list(o.users_collection): c.objects.unlink(o)
        col.objects.link(o)
        if o.type == "ARMATURE": o.name = "RIG_" + name
    print("BUILT", name, [(o.name, o.type) for o in new])

C = lambda n: f"{n}/{n}.mhclo"
# hero: short young man (shirt+trousers via casualsuit), later grown with bone/armature scale
human("Hero", age=0.45, height=0.0, muscle=0.45, weight=0.45, skin="young_caucasian_male", hair="short02/short02.mhclo",
      clothes=[C("male_worksuit01"), C("shoes02")], subdiv=1, brows="eyebrow002/eyebrow002.mhclo")
human("Young", age=0.45, height=0.0, muscle=0.45, weight=0.45, skin="young_caucasian_male", hair="short02/short02.mhclo",
      clothes=[C("male_worksuit01"), C("shoes02")], brows="eyebrow002/eyebrow002.mhclo")
human("Officer1", age=0.7, height=0.6, muscle=0.6, weight=0.6, skin="middleage_caucasian_male", hair="short04/short04.mhclo",
      clothes=[C("male_elegantsuit01"), C("shoes03")], brows="eyebrow005/eyebrow005.mhclo")
human("Officer2", age=0.8, height=0.55, muscle=0.5, weight=0.7, skin="old_caucasian_male", hair="short01/short01.mhclo",
      clothes=[C("male_elegantsuit01"), C("shoes03")], brows="eyebrow007/eyebrow007.mhclo")
human("Clerk", age=0.6, height=0.5, weight=0.55, skin="middleage_caucasian_male", hair="short03/short03.mhclo",
      clothes=[C("male_elegantsuit01"), C("shoes01")])
human("Recruit1", age=0.4, height=0.6, skin="young_caucasian_male2", hair="short01/short01.mhclo",
      clothes=[C("male_casualsuit01"), C("shoes04")])
human("Recruit2", age=0.42, height=0.65, skin="young_caucasian_male", hair="short04/short04.mhclo",
      clothes=[C("male_casualsuit03"), C("shoes05")])
human("Surgeon1", age=0.65, height=0.55, skin="middleage_caucasian_male", hair="short02/short02.mhclo",
      clothes=[C("male_worksuit01"), C("shoes01")])
human("Surgeon2", age=0.55, height=0.6, skin="middleage_caucasian_male", hair="short03/short03.mhclo",
      clothes=[C("male_worksuit01"), C("shoes01")])
human("Nurse", gender=0.0, age=0.4, height=0.45, skin="young_caucasian_female", hair="bob01/bob01.mhclo",
      clothes=[C("female_elegantsuit01"), C("shoes06")], brows="eyebrow010/eyebrow010.mhclo")
human("Normal", age=0.75, height=0.5, skin="middleage_caucasian_male", hair="short03/short03.mhclo",
      clothes=[C("male_elegantsuit01"), C("shoes03")])
bpy.ops.wm.save_as_mainfile(filepath=out)
