"""Hero + crowd variants with MPFB2 (MakeHuman CC0 assets).
blender -b --python 01_build_humans.py -- <out.blend>"""
import sys
import bpy
from bl_ext.user_default.mpfb.services.humanservice import HumanService
out = sys.argv[sys.argv.index("--") + 1]
for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob, do_unlink=True)

def human(name, ph, hair, clothes, skin, subdiv, x, brows="eyebrow001/eyebrow001.mhclo"):
    info = HumanService._create_default_human_info_dict()
    info["name"] = name
    base = {"gender": 1.0, "age": 0.5, "muscle": 0.5, "weight": 0.5, "proportions": 0.6, "height": 0.5,
            "cupsize": 0.5, "firmness": 0.5, "race": {"asian": 0.05, "caucasian": 0.9, "african": 0.05}}
    base.update(ph); info["phenotype"] = base
    info["rig"] = "default"
    info["eyes"] = "high-poly/high-poly.mhclo" if subdiv else "low-poly/low-poly.mhclo"
    info["eyebrows"] = brows; info["eyelashes"] = "eyelashes01/eyelashes01.mhclo"
    info["teeth"] = "teeth_base/teeth_base.mhclo" if subdiv else ""; info["tongue"] = "tongue01/tongue01.mhclo" if subdiv else ""
    info["hair"] = hair; info["clothes"] = clothes
    info["skin_mhmat"] = skin; info["skin_material_type"] = "ENHANCED_SSS" if subdiv else "ENHANCED"
    info["eyes_material_type"] = "PROCEDURAL_EYES"
    st = HumanService.get_default_deserialization_settings(); st["subdiv_levels"] = subdiv
    HumanService.deserialize_from_dict(info, st)
    rig = bpy.data.objects[name]; rig.location.x = x
    return rig

# Hero: stout man in his fifties, dark suit (overcoat tint applied in scene build), generic face
human("Hero", {"age": 0.78, "weight": 1.0, "muscle": 0.35, "height": 0.45, "proportions": 0.45},
      "short02/short02.mhclo", ["male_elegantsuit01/male_elegantsuit01.mhclo", "shoes02/shoes02.mhclo"],
      "middleage_caucasian_male/middleage_caucasian_male.mhmat", 1, 0, brows="eyebrow006/eyebrow006.mhclo")
C = [
 ("CrowdA", {"age": 0.6, "weight": 0.6}, "short01/short01.mhclo", ["male_elegantsuit01/male_elegantsuit01.mhclo", "shoes03/shoes03.mhclo", "fedora01/fedora01.mhclo"], "middleage_caucasian_male/middleage_caucasian_male.mhmat"),
 ("CrowdB", {"age": 0.45, "weight": 0.45, "height": 0.6}, "short03/short03.mhclo", ["male_elegantsuit01/male_elegantsuit01.mhclo", "shoes01/shoes01.mhclo", "fedora_cocked/fedora_cocked.mhclo"], "young_caucasian_male/young_caucasian_male.mhmat"),
 ("CrowdC", {"gender": 0.0, "age": 0.5, "weight": 0.5, "height": 0.45}, "bob02/bob02.mhclo", ["female_elegantsuit01/female_elegantsuit01.mhclo", "shoes05/shoes05.mhclo"], "young_caucasian_female/young_caucasian_female.mhmat"),
 ("CrowdD", {"age": 0.8, "weight": 0.7, "race": {"asian": 0.0, "caucasian": 0.95, "african": 0.05}}, "short04/short04.mhclo", ["male_casualsuit04/male_casualsuit04.mhclo", "shoes02/shoes02.mhclo", "fedora01/fedora01.mhclo"], "old_caucasian_male/old_caucasian_male.mhmat"),
 ("CrowdE", {"age": 0.5, "weight": 0.55, "race": {"asian": 0.0, "caucasian": 0.2, "african": 0.8}}, "short01/short01.mhclo", ["male_worksuit01/male_worksuit01.mhclo", "shoes03/shoes03.mhclo", "fedora_cocked/fedora_cocked.mhclo"], "middleage_african_male/middleage_african_male.mhmat"),
 ("CrowdF", {"gender": 0.0, "age": 0.65, "weight": 0.6, "height": 0.4}, "ponytail01/ponytail01.mhclo", ["female_casualsuit02/female_casualsuit02.mhclo", "shoes05/shoes05.mhclo"], "middleage_caucasian_female/middleage_caucasian_female.mhmat"),
]
for i, (n, ph, hr, cl, sk) in enumerate(C):
    human(n, ph, hr, cl, sk, 0, 1.5 * (i + 1))
for ob in bpy.data.objects:
    if ob.type == 'ARMATURE':
        print("HUMAN", ob.name, [(c.name, len(c.data.polygons)) for c in ob.children if c.type == 'MESH'])
bpy.ops.wm.save_as_mainfile(filepath=out)
