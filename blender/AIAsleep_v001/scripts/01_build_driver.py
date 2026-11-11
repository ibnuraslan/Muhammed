"""Driver: generic East Asian man, 30s, MPFB2 (MakeHuman CC0).  blender -b --python 01_build_driver.py -- <out.blend>"""
import sys, bpy
from bl_ext.user_default.mpfb.services.humanservice import HumanService
out = sys.argv[sys.argv.index("--") + 1]
for ob in list(bpy.data.objects): bpy.data.objects.remove(ob, do_unlink=True)
info = HumanService._create_default_human_info_dict()
info["name"] = "Driver"
info["phenotype"] = {"gender": 1.0, "age": 0.5, "muscle": 0.5, "weight": 0.5, "proportions": 0.55, "height": 0.5,
                     "cupsize": 0.5, "firmness": 0.5, "race": {"asian": 0.95, "caucasian": 0.05, "african": 0.0}}
info["rig"] = "default"
info["eyes"] = "high-poly/high-poly.mhclo"
info["eyebrows"] = "eyebrow001/eyebrow001.mhclo"
info["eyelashes"] = "eyelashes01/eyelashes01.mhclo"
info["teeth"] = "teeth_base/teeth_base.mhclo"
info["tongue"] = "tongue01/tongue01.mhclo"
info["hair"] = "short02/short02.mhclo"
info["clothes"] = ["male_casualsuit01/male_casualsuit01.mhclo", "shoes02/shoes02.mhclo"]
info["skin_mhmat"] = "middleage_asian_male/middleage_asian_male.mhmat"
info["skin_material_type"] = "ENHANCED_SSS"
info["eyes_material_type"] = "PROCEDURAL_EYES"
st = HumanService.get_default_deserialization_settings(); st["subdiv_levels"] = 1
HumanService.deserialize_from_dict(info, st)
for ob in bpy.data.objects:
    print("OBJ", ob.name, ob.type, ob.parent.name if ob.parent else None, [m.name for m in ob.material_slots] if ob.type == "MESH" else "", tuple(round(d, 3) for d in ob.dimensions))
rig = [o for o in bpy.data.objects if o.type == "ARMATURE"][0]
print("BONES", len(rig.data.bones), [b.name for b in rig.data.bones if any(k in b.name for k in ("lid", "brow", "jaw", "oris", "levator", "eye", "risorius", "head", "neck"))])
bpy.ops.wm.save_as_mainfile(filepath=out)
