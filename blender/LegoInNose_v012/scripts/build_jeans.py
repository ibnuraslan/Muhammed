"""v012 (jeans variant, build_jeans.py): Mom's jeans = the leg part of female_casualsuit01. Original doc: new outfits fitted by MPFB on the same phenotypes as 01_build_humans.py (Man: T-shirt + jeans, male_casualsuit06;
Mom: blouse + skirt, female_elegantsuit01). Saved to a temp file; import_clothes.py moves them onto the film rigs.
blender -b --python build_clothes.py -- out.blend"""
import sys, bpy
from bl_ext.user_default.mpfb.services.humanservice import HumanService
out = sys.argv[sys.argv.index("--") + 1]
for ob in list(bpy.data.objects): bpy.data.objects.remove(ob, do_unlink=True)
CH = [("Mom", dict(gender=0.0, age=0.5, muscle=0.5, weight=0.5, proportions=0.6, height=0.5, cupsize=0.5, firmness=0.5), "young_caucasian_female/young_caucasian_female.mhmat",
       ["female_casualsuit01/female_casualsuit01.mhclo"], 1)]
for name, ph, skin, clothes, subd in CH:
    info = HumanService._create_default_human_info_dict(); info["name"] = name
    p = {"gender": 0.5, "age": 0.5, "muscle": 0.5, "weight": 0.5, "proportions": 0.5, "height": 0.5, "cupsize": 0.5, "firmness": 0.5,
         "race": {"asian": 0.05, "caucasian": 0.9, "african": 0.05}}
    p.update(ph); info["phenotype"] = p; info["rig"] = "default"; info["clothes"] = clothes; info["skin_mhmat"] = skin
    st = HumanService.get_default_deserialization_settings(); st["subdiv_levels"] = subd
    before = set(bpy.data.objects); bm = HumanService.deserialize_from_dict(info, st); new = set(bpy.data.objects) - before
    arm = [o for o in new if o.type == "ARMATURE"][0]; arm.name = "NEW_" + name
    for o in new:
        if o.type == "MESH" and o is not bm: o.name = "NEW_" + name + "_" + o.name.split(".")[-1]
    bm.name = "NEW_" + name + "_Body"
    print("BUILT", name, sorted((o.name, len(o.data.vertices) if o.type == "MESH" else 0) for o in new))
bpy.ops.wm.save_as_mainfile(filepath=out)
