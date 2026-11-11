"""Composer (generic, MPFB2 / MakeHuman CC0). blender -b --python 01_build_composer.py -- <out.blend> [hair]"""
import sys, bpy
from bl_ext.user_default.mpfb.services.humanservice import HumanService
a = sys.argv[sys.argv.index("--") + 1:]
out = a[0]; hair = a[1] if len(a) > 1 else "short04"
for ob in list(bpy.data.objects): bpy.data.objects.remove(ob, do_unlink=True)
info = HumanService._create_default_human_info_dict()
info["name"] = "Composer"
info["phenotype"] = {"gender": 1.0, "age": 0.72, "muscle": 0.5, "weight": 0.6, "proportions": 0.55, "height": 0.45,
                     "cupsize": 0.5, "firmness": 0.5, "race": {"asian": 0.0, "caucasian": 0.95, "african": 0.05}}
info["rig"] = "default"
info["eyes"] = "high-poly/high-poly.mhclo"
info["eyebrows"] = "eyebrow010/eyebrow010.mhclo"
info["eyelashes"] = "eyelashes01/eyelashes01.mhclo"
info["teeth"] = "teeth_base/teeth_base.mhclo"
info["tongue"] = "tongue01/tongue01.mhclo"
info["hair"] = "%s/%s.mhclo" % (hair, hair)
info["clothes"] = ["male_elegantsuit01/male_elegantsuit01.mhclo", "shoes03/shoes03.mhclo"]
info["skin_mhmat"] = "old_caucasian_male/old_caucasian_male.mhmat"
info["skin_material_type"] = "ENHANCED_SSS"
info["eyes_material_type"] = "PROCEDURAL_EYES"
st = HumanService.get_default_deserialization_settings(); st["subdiv_levels"] = 1
HumanService.deserialize_from_dict(info, st)
for ob in bpy.data.objects:
    print("OBJ", ob.name, ob.type, ob.parent.name if ob.parent else None, [m.name for m in ob.material_slots] if ob.type == "MESH" else "", tuple(round(d, 3) for d in ob.dimensions))
arm = next(o for o in bpy.data.objects if o.type == "ARMATURE")
print("BONES", [b.name for b in arm.data.bones])
bpy.ops.wm.save_as_mainfile(filepath=out)
