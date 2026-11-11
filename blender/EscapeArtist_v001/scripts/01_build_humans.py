"""Build all MPFB2 humans (MakeHuman CC0 assets). blender -b --python 01_build_humans.py -- <out.blend>"""
import sys, bpy
from bl_ext.user_default.mpfb.services.humanservice import HumanService
out = sys.argv[sys.argv.index("--") + 1]
for ob in list(bpy.data.objects): bpy.data.objects.remove(ob, do_unlink=True)
CAST = {
 "Prisoner":    dict(g=1.0, age=0.5,  mus=0.55, w=0.45, h=0.55, skin="young_caucasian_male2", hair="short02/short02.mhclo", brow="eyebrow001",
                     clothes=["male_worksuit01/male_worksuit01.mhclo", "shoes03/shoes03.mhclo"]),
 "PrisonerOld": dict(g=1.0, age=0.85, mus=0.45, w=0.5,  h=0.53, skin="old_caucasian_male", hair="short02/short02.mhclo", brow="eyebrow001",
                     clothes=["male_worksuit01/male_worksuit01.mhclo", "shoes03/shoes03.mhclo"]),
 "Boy":         dict(g=1.0, age=0.2,  mus=0.5,  w=0.45, h=0.5, skin="young_caucasian_male", hair="short04/short04.mhclo", brow="eyebrow002",
                     clothes=["male_casualsuit03/male_casualsuit03.mhclo", "shoes05/shoes05.mhclo"]),
 "Father":      dict(g=1.0, age=0.9,  mus=0.5,  w=0.6,  h=0.55, skin="old_caucasian_male", hair="short01/short01.mhclo", brow="eyebrow003",
                     clothes=["male_casualsuit03/male_casualsuit03.mhclo", "shoes01/shoes01.mhclo"]),
 "Stepmother":  dict(g=0.0, age=0.6,  mus=0.45, w=0.5,  h=0.5, skin="middleage_caucasian_female", hair="bob02/bob02.mhclo", brow="eyebrow008",
                     clothes=["female_elegantsuit01/female_elegantsuit01.mhclo", "shoes04/shoes04.mhclo"]),
 "Guard":       dict(g=1.0, age=0.55, mus=0.7,  w=0.6,  h=0.6, skin="middleage_caucasian_male", hair="short03/short03.mhclo", brow="eyebrow004",
                     clothes=["male_casualsuit01/male_casualsuit01.mhclo", "shoes03/shoes03.mhclo"]),
 "Guard2":      dict(g=1.0, age=0.5,  mus=0.6,  w=0.55, h=0.58, skin="middleage_african_male", hair="short04/short04.mhclo", brow="eyebrow005",
                     clothes=["male_casualsuit01/male_casualsuit01.mhclo", "shoes04/shoes04.mhclo"]),
 "Judge":       dict(g=1.0, age=0.8,  mus=0.4,  w=0.6,  h=0.52, skin="old_african_male", hair="short01/short01.mhclo", brow="eyebrow003",
                     clothes=["male_elegantsuit01/male_elegantsuit01.mhclo", "shoes04/shoes04.mhclo"]),
 "Protester1":  dict(g=0.0, age=0.4,  mus=0.4,  w=0.45, h=0.5, skin="young_asian_female", hair="ponytail01/ponytail01.mhclo", brow="eyebrow008",
                     clothes=["female_elegantsuit01/female_elegantsuit01.mhclo", "shoes02/shoes02.mhclo"]),
 "Protester2":  dict(g=1.0, age=0.45, mus=0.5,  w=0.55, h=0.55, skin="young_african_male", hair="afro01/afro01.mhclo", brow="eyebrow002",
                     clothes=["male_casualsuit05/male_casualsuit05.mhclo", "shoes02/shoes02.mhclo"]),
}
for name, c in CAST.items():
    info = HumanService._create_default_human_info_dict()
    info["name"] = name
    info["phenotype"] = {"gender": c["g"], "age": c["age"], "muscle": c["mus"], "weight": c["w"], "proportions": 0.6, "height": c["h"],
                         "cupsize": 0.5, "firmness": 0.5, "race": {"asian": 0.1, "caucasian": 0.8, "african": 0.1}}
    info["rig"] = "default"
    info["eyes"] = "high-poly/high-poly.mhclo"; info["eyebrows"] = c["brow"] + "/" + c["brow"] + ".mhclo"
    info["eyelashes"] = "eyelashes01/eyelashes01.mhclo"; info["teeth"] = "teeth_base/teeth_base.mhclo"; info["tongue"] = "tongue01/tongue01.mhclo"
    info["hair"] = c["hair"]; info["clothes"] = c["clothes"]
    info["skin_mhmat"] = c["skin"] + "/" + c["skin"] + ".mhmat"
    info["skin_material_type"] = "ENHANCED_SSS"; info["eyes_material_type"] = "PROCEDURAL_EYES"
    st = HumanService.get_default_deserialization_settings(); st["subdiv_levels"] = 1
    before = set(bpy.data.objects)
    bm = HumanService.deserialize_from_dict(info, st)
    new = set(bpy.data.objects) - before
    col = bpy.data.collections.new("H_" + name); bpy.context.scene.collection.children.link(col)
    for o in new:
        for uc in list(o.users_collection): uc.objects.unlink(o)
        col.objects.link(o)
    print("BUILT", name, sorted(o.name for o in new))
bpy.ops.wm.save_as_mainfile(filepath=out)
