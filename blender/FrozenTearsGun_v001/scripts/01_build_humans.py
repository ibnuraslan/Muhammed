"""Build the two MPFB2 characters (CC0 MakeHuman assets).
blender -b --python 01_build_humans.py -- <out.blend>"""
import sys
import bpy
from bl_ext.user_default.mpfb.services.humanservice import HumanService
out = sys.argv[sys.argv.index("--") + 1]
for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob, do_unlink=True)

def build(name, phen, hair, clothes, skin, eyebrows="eyebrow001/eyebrow001.mhclo"):
    info = HumanService._create_default_human_info_dict()
    info["name"] = name
    info["phenotype"] = phen
    info["rig"] = "default"
    info["eyes"] = "high-poly/high-poly.mhclo"
    info["eyebrows"] = eyebrows
    info["eyelashes"] = "eyelashes01/eyelashes01.mhclo"
    info["teeth"] = "teeth_base/teeth_base.mhclo"
    info["tongue"] = "tongue01/tongue01.mhclo"
    info["hair"] = hair
    info["clothes"] = clothes
    info["skin_mhmat"] = skin
    info["skin_material_type"] = "ENHANCED_SSS"
    info["eyes_material_type"] = "MAKESKIN"
    st = HumanService.get_default_deserialization_settings()
    st["subdiv_levels"] = 1
    bm = HumanService.deserialize_from_dict(info, st)
    rig = bm.parent
    rig.name = name
    return rig

w = build("Inventor", {"gender": 0.0, "age": 0.45, "muscle": 0.5, "weight": 0.45, "proportions": 0.7, "height": 0.62,
                       "cupsize": 0.5, "firmness": 0.5, "race": {"asian": 0.2, "caucasian": 0.6, "african": 0.2}},
          "ponytail01/ponytail01.mhclo", ["female_casualsuit01/female_casualsuit01.mhclo", "shoes02/shoes02.mhclo"],
          "young_caucasian_female/young_caucasian_female.mhmat")
m = build("Mentor", {"gender": 1.0, "age": 0.88, "muscle": 0.45, "weight": 0.62, "proportions": 0.55, "height": 0.6,
                     "cupsize": 0.5, "firmness": 0.5, "race": {"asian": 0.1, "caucasian": 0.8, "african": 0.1}},
          "", ["male_elegantsuit01/male_elegantsuit01.mhclo", "shoes01/shoes01.mhclo"],
          "old_caucasian_male/old_caucasian_male.mhmat")
for ob in bpy.data.objects:
    print("OBJ", ob.name, ob.type, ob.parent.name if ob.parent else None,
          [s.name for s in ob.material_slots] if ob.type == "MESH" else "", tuple(round(d, 3) for d in ob.dimensions))
bpy.ops.wm.save_as_mainfile(filepath=out)
