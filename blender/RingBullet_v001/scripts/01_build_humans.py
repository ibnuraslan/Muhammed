"""Build Owner (bald, middle-aged, suit+tie) and Robber (dark clothes) with MPFB2.
blender -b --python 01_build_humans.py -- <out.blend>"""
import sys, bpy
from bl_ext.user_default.mpfb.services.humanservice import HumanService
out = sys.argv[sys.argv.index("--") + 1]
for ob in list(bpy.data.objects): bpy.data.objects.remove(ob, do_unlink=True)

def make(name, pheno, clothes, skin, hair=""):
    info = HumanService._create_default_human_info_dict()
    info["name"] = name; info["phenotype"] = pheno; info["rig"] = "default"
    info["eyes"] = "high-poly/high-poly.mhclo"; info["eyebrows"] = "eyebrow001/eyebrow001.mhclo"
    info["eyelashes"] = "eyelashes01/eyelashes01.mhclo"; info["teeth"] = "teeth_base/teeth_base.mhclo"
    info["tongue"] = "tongue01/tongue01.mhclo"; info["hair"] = hair; info["clothes"] = clothes
    info["skin_mhmat"] = skin; info["skin_material_type"] = "ENHANCED_SSS"; info["eyes_material_type"] = "PROCEDURAL_EYES"
    st = HumanService.get_default_deserialization_settings(); st["subdiv_levels"] = 1
    before = set(bpy.data.objects)
    HumanService.deserialize_from_dict(info, st)
    new = set(bpy.data.objects) - before
    col = bpy.data.collections.new(name); bpy.context.scene.collection.children.link(col)
    for o in new:
        for c in list(o.users_collection): c.objects.unlink(o)
        col.objects.link(o)
    return new

make("Owner", {"gender": 1.0, "age": 0.62, "muscle": 0.45, "weight": 0.6, "proportions": 0.6, "height": 0.5,
               "cupsize": 0.5, "firmness": 0.5, "race": {"asian": 0.1, "caucasian": 0.8, "african": 0.1}},
     ["male_elegantsuit01/male_elegantsuit01.mhclo", "shoes02/shoes02.mhclo"], "middleage_caucasian_male/middleage_caucasian_male.mhmat")
make("Robber", {"gender": 1.0, "age": 0.45, "muscle": 0.6, "weight": 0.5, "proportions": 0.6, "height": 0.6,
                "cupsize": 0.5, "firmness": 0.5, "race": {"asian": 0.3, "caucasian": 0.4, "african": 0.3}},
     ["male_casualsuit01/male_casualsuit01.mhclo", "shoes02/shoes02.mhclo"], "young_caucasian_male/young_caucasian_male.mhmat", hair="short02/short02.mhclo")
make("Officer", {"gender": 1.0, "age": 0.5, "muscle": 0.6, "weight": 0.55, "proportions": 0.6, "height": 0.6,
                 "cupsize": 0.5, "firmness": 0.5, "race": {"asian": 0.2, "caucasian": 0.4, "african": 0.4}},
     ["male_worksuit01/male_worksuit01.mhclo", "shoes02/shoes02.mhclo"], "middleage_african_male/middleage_african_male.mhmat", hair="short01/short01.mhclo")
for ob in bpy.data.objects:
    print("OBJ", ob.name, ob.type, ob.parent.name if ob.parent else None, [c.name for c in ob.users_collection],
          tuple(round(d, 3) for d in ob.dimensions))
bpy.ops.wm.save_as_mainfile(filepath=out)
