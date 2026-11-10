"""Build the motion-test character with MPFB2 (MakeHuman CC0 system assets).

Run:  blender -b --factory-startup? (no: MPFB must be enabled) ->
      blender -b --python 01_build_character.py -- <out.blend>
Requires the MPFB 2.0.18 extension and the MakeHuman system asset pack
installed in MPFB's user data directory.
"""
import sys
import bpy
from bl_ext.user_default.mpfb.services.humanservice import HumanService

out = sys.argv[sys.argv.index("--") + 1]

# Start empty
for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob, do_unlink=True)

info = HumanService._create_default_human_info_dict()
info["name"] = "Farmer"
info["phenotype"] = {
    "gender": 1.0, "age": 0.86, "muscle": 0.5, "weight": 0.55,
    "proportions": 0.6, "height": 0.55, "cupsize": 0.5, "firmness": 0.5,
    "race": {"asian": 0.05, "caucasian": 0.85, "african": 0.10},
}
info["rig"] = "default"
info["eyes"] = "high-poly/high-poly.mhclo"
info["eyebrows"] = "eyebrow001/eyebrow001.mhclo"
info["eyelashes"] = "eyelashes01/eyelashes01.mhclo"
info["teeth"] = "teeth_base/teeth_base.mhclo"
info["tongue"] = "tongue01/tongue01.mhclo"
info["hair"] = ""
info["clothes"] = ["male_worksuit01/male_worksuit01.mhclo", "male_casualsuit06/male_casualsuit06.mhclo",   # casualsuit06 = hospital gown (tinted, shown only in the hospital)
                   "shoes03/shoes03.mhclo"]
info["skin_mhmat"] = "old_caucasian_male/old_caucasian_male.mhmat"
info["skin_material_type"] = "ENHANCED_SSS"
info["eyes_material_type"] = "PROCEDURAL_EYES"

settings = HumanService.get_default_deserialization_settings()
settings["subdiv_levels"] = 1
basemesh = HumanService.deserialize_from_dict(info, settings)

for ob in bpy.data.objects:
    print("OBJ", ob.name, ob.type, ob.parent.name if ob.parent else None,
          [m.name for m in ob.material_slots] if ob.type == "MESH" else "",
          tuple(round(d, 3) for d in ob.dimensions))
bpy.ops.wm.save_as_mainfile(filepath=out)
