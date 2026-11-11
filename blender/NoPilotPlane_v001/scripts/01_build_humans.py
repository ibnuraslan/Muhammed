"""Build one MPFB2 human (CC0 MakeHuman assets) per call.
blender -b --python 01_build_humans.py -- <NAME> <out.blend>"""
import sys, bpy
from bl_ext.user_default.mpfb.services.humanservice import HumanService
NAME, out = sys.argv[sys.argv.index("--") + 1:][:2]
for ob in list(bpy.data.objects): bpy.data.objects.remove(ob, do_unlink=True)
S = {  # gender age muscle weight height race skin hair clothes
 "YOU":  (1.0, 0.42, 0.55, 0.45, 0.55, (0.1, 0.8, 0.1), "young_caucasian_male/young_caucasian_male.mhmat", "short02/short02.mhclo",
          ["male_casualsuit04/male_casualsuit04.mhclo", "shoes03/shoes03.mhclo"]),
 "CAPT": (1.0, 0.65, 0.5, 0.6, 0.55, (0.05, 0.85, 0.1), "middleage_caucasian_male/middleage_caucasian_male.mhmat", "short04/short04.mhclo",
          ["male_elegantsuit01/male_elegantsuit01.mhclo", "shoes01/shoes01.mhclo"]),
 "FO":   (1.0, 0.5, 0.5, 0.5, 0.55, (0.1, 0.1, 0.8), "middleage_african_male/middleage_african_male.mhmat", "short01/short01.mhclo",
          ["male_elegantsuit01/male_elegantsuit01.mhclo", "shoes01/shoes01.mhclo"]),
 "PA":   (0.0, 0.5, 0.5, 0.5, 0.5, (0.1, 0.85, 0.05), "young_caucasian_female/young_caucasian_female.mhmat", "bob02/bob02.mhclo",
          ["female_casualsuit01/female_casualsuit01.mhclo", "shoes05/shoes05.mhclo"]),
 "PB":   (1.0, 0.75, 0.45, 0.7, 0.5, (0.8, 0.1, 0.1), "old_asian_male/old_asian_male.mhmat", "short03/short03.mhclo",
          ["male_casualsuit02/male_casualsuit02.mhclo", "shoes03/shoes03.mhclo"]),
 "PC":   (0.0, 0.7, 0.4, 0.65, 0.45, (0.05, 0.1, 0.85), "middleage_african_female/middleage_african_female.mhmat", "afro01/afro01.mhclo",
          ["female_elegantsuit01/female_elegantsuit01.mhclo", "shoes06/shoes06.mhclo"]),
 "PD":   (1.0, 0.35, 0.6, 0.5, 0.6, (0.1, 0.85, 0.05), "young_caucasian_male2/young_caucasian_male2.mhmat", "short02/short02.mhclo",
          ["male_casualsuit05/male_casualsuit05.mhclo", "shoes04/shoes04.mhclo"]),
 "PE":   (0.0, 0.35, 0.5, 0.45, 0.5, (0.85, 0.1, 0.05), "young_asian_female/young_asian_female.mhmat", "ponytail01/ponytail01.mhclo",
          ["female_sportsuit01/female_sportsuit01.mhclo", "shoes05/shoes05.mhclo"]),
 "PF":   (1.0, 0.6, 0.5, 0.8, 0.5, (0.05, 0.9, 0.05), "middleage_caucasian_male/middleage_caucasian_male.mhmat", "short04/short04.mhclo",
          ["male_casualsuit03/male_casualsuit03.mhclo", "shoes03/shoes03.mhclo"]),
}
g, age, mus, w, h, race, skin, hair, clothes = S[NAME]
info = HumanService._create_default_human_info_dict()
info["name"] = NAME
info["phenotype"] = {"gender": g, "age": age, "muscle": mus, "weight": w, "proportions": 0.6, "height": h, "cupsize": 0.5,
                     "firmness": 0.5, "race": {"african": race[0], "asian": race[1], "caucasian": race[2]}}
info["rig"] = "default"
info["eyes"] = "high-poly/high-poly.mhclo"; info["eyebrows"] = "eyebrow001/eyebrow001.mhclo"
info["eyelashes"] = "eyelashes01/eyelashes01.mhclo"; info["teeth"] = "teeth_base/teeth_base.mhclo"; info["tongue"] = "tongue01/tongue01.mhclo"
info["hair"] = hair; info["clothes"] = clothes
info["skin_mhmat"] = skin; info["skin_material_type"] = "ENHANCED_SSS"; info["eyes_material_type"] = "PROCEDURAL_EYES"
st = HumanService.get_default_deserialization_settings(); st["subdiv_levels"] = 1 if NAME in ("YOU", "CAPT", "FO") else 0
HumanService.deserialize_from_dict(info, st)
for ob in bpy.data.objects:
    ob.name = NAME + "_" + ob.name if not ob.name.startswith(NAME) else ob.name
    print("OBJ", ob.name, ob.type, ob.parent.name if ob.parent else None, tuple(round(d, 3) for d in ob.dimensions))
bpy.ops.wm.save_as_mainfile(filepath=out)
