"""Build one MPFB2 human (MakeHuman CC0 assets) into its own .blend.
blender -b --python 01_build_humans.py -- <name> <out.blend>
names: Man, OfficerA, OfficerB, OfficerC, PedA, PedB"""
import sys
import bpy
from bl_ext.user_default.mpfb.services.humanservice import HumanService

name, out = sys.argv[sys.argv.index("--") + 1:][:2]
for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob, do_unlink=True)

SPEC = {
    "Man": dict(gender=1.0, age=0.5, muscle=0.6, weight=0.45, height=0.5, race=(0.0, 0.25, 0.75, 0.0),
                hair="short02/short02.mhclo", clothes=["male_casualsuit01/male_casualsuit01.mhclo", "shoes05/shoes05.mhclo"],
                skin="middleage_asian_male/middleage_asian_male.mhmat"),
    "OfficerA": dict(gender=1.0, age=0.6, muscle=0.55, weight=0.7, height=0.55, race=(0.0, 0.2, 0.8, 0.0),
                     hair="short04/short04.mhclo", clothes=["male_casualsuit01/male_casualsuit01.mhclo", "shoes03/shoes03.mhclo"],
                     skin="middleage_asian_male/middleage_asian_male.mhmat"),
    "OfficerB": dict(gender=1.0, age=0.45, muscle=0.5, weight=0.5, height=0.45, race=(0.1, 0.2, 0.7, 0.0),
                     hair="short01/short01.mhclo", clothes=["male_casualsuit01/male_casualsuit01.mhclo", "shoes04/shoes04.mhclo"],
                     skin="young_asian_male/young_asian_male.mhmat"),
    "OfficerC": dict(gender=1.0, age=0.75, muscle=0.4, weight=0.8, height=0.5, race=(0.2, 0.2, 0.6, 0.0),
                     hair="short03/short03.mhclo", clothes=["male_casualsuit01/male_casualsuit01.mhclo", "shoes03/shoes03.mhclo"],
                     skin="old_asian_male/old_asian_male.mhmat"),
    "PedA": dict(gender=0.0, age=0.45, muscle=0.4, weight=0.5, height=0.45, race=(0.0, 0.2, 0.8, 0.0),
                 hair="braid01/braid01.mhclo", clothes=["female_elegantsuit01/female_elegantsuit01.mhclo", "shoes01/shoes01.mhclo"],
                 skin="young_asian_female/young_asian_female.mhmat"),
    "PedB": dict(gender=1.0, age=0.85, muscle=0.4, weight=0.45, height=0.45, race=(0.2, 0.1, 0.7, 0.0),
                 hair="short01/short01.mhclo", clothes=["male_casualsuit03/male_casualsuit03.mhclo", "shoes01/shoes01.mhclo"],
                 skin="old_asian_male/old_asian_male.mhmat"),
}[name]
# race tuple: african, caucasian, asian (MakeHuman has only these three; asian+african blend for a South Asian look)
afr, cau, asi, _ = SPEC["race"]
asi, afr = SPEC["race"][2] * 0.6, SPEC["race"][2] * 0.4 + SPEC["race"][0]
info = HumanService._create_default_human_info_dict()
info["name"] = name
info["phenotype"] = {"gender": SPEC["gender"], "age": SPEC["age"], "muscle": SPEC["muscle"], "weight": SPEC["weight"],
                     "proportions": 0.6, "height": SPEC["height"], "cupsize": 0.5, "firmness": 0.5,
                     "race": {"asian": asi, "caucasian": cau, "african": afr}}
info["rig"] = "default"
info["eyes"] = "high-poly/high-poly.mhclo"
info["eyebrows"] = "eyebrow001/eyebrow001.mhclo"
info["eyelashes"] = "eyelashes01/eyelashes01.mhclo"
info["teeth"] = "teeth_base/teeth_base.mhclo"
info["tongue"] = "tongue01/tongue01.mhclo"
info["hair"] = SPEC["hair"]
info["clothes"] = SPEC["clothes"]
info["skin_mhmat"] = SPEC["skin"]
info["skin_material_type"] = "ENHANCED_SSS"
info["eyes_material_type"] = "PROCEDURAL_EYES"
settings = HumanService.get_default_deserialization_settings()
settings["subdiv_levels"] = 1 if name in ("Man",) else 0
HumanService.deserialize_from_dict(info, settings)
for ob in bpy.data.objects:
    print("OBJ", ob.name, ob.type, ob.parent.name if ob.parent else None,
          [m.name for m in ob.material_slots] if ob.type == "MESH" else "", tuple(round(d, 3) for d in ob.dimensions))
bpy.ops.wm.save_as_mainfile(filepath=out)
