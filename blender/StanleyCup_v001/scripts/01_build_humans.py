"""Build the couple with MPFB2 (MakeHuman CC0 assets).
blender -b --python 01_build_humans.py -- <out.blend>"""
import sys
import bpy
from bl_ext.user_default.mpfb.services.humanservice import HumanService
out = sys.argv[sys.argv.index("--") + 1]
for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob, do_unlink=True)

def build(name, pheno, hair, clothes, skin, brows):
    info = HumanService._create_default_human_info_dict()
    info["name"] = name
    info["phenotype"] = pheno
    info["rig"] = "default"
    info["eyes"] = "high-poly/high-poly.mhclo"
    info["eyebrows"] = brows
    info["eyelashes"] = "eyelashes01/eyelashes01.mhclo"
    info["teeth"] = "teeth_base/teeth_base.mhclo"
    info["tongue"] = "tongue01/tongue01.mhclo"
    info["hair"] = hair
    info["clothes"] = clothes
    info["skin_mhmat"] = skin
    info["skin_material_type"] = "ENHANCED_SSS"
    info["eyes_material_type"] = "PROCEDURAL_EYES"
    st = HumanService.get_default_deserialization_settings()
    st["subdiv_levels"] = 1
    before = set(bpy.data.objects)
    HumanService.deserialize_from_dict(info, st)
    new = set(bpy.data.objects) - before
    col = bpy.data.collections.new(name); bpy.context.scene.collection.children.link(col)
    for o in new:
        for c in o.users_collection: c.objects.unlink(o)
        col.objects.link(o)
        if o.type == "ARMATURE": o.name = name + "_rig"
    return new

build("Woman", {"gender": 0.0, "age": 0.5, "muscle": 0.5, "weight": 0.45, "proportions": 0.65, "height": 0.45,
                "cupsize": 0.5, "firmness": 0.55, "race": {"asian": 0.1, "caucasian": 0.75, "african": 0.15}},
      "long01/long01.mhclo", ["female_elegantsuit01/female_elegantsuit01.mhclo", "shoes02/shoes02.mhclo"],
      "young_caucasian_female/young_caucasian_female.mhmat", "eyebrow010/eyebrow010.mhclo")
build("Fiance", {"gender": 1.0, "age": 0.52, "muscle": 0.6, "weight": 0.5, "proportions": 0.6, "height": 0.6,
                 "cupsize": 0.5, "firmness": 0.5, "race": {"asian": 0.1, "caucasian": 0.6, "african": 0.3}},
      "short02/short02.mhclo", ["male_casualsuit05/male_casualsuit05.mhclo", "shoes03/shoes03.mhclo"],
      "young_caucasian_male/young_caucasian_male.mhmat", "eyebrow001/eyebrow001.mhclo")
for ob in bpy.data.objects:
    print("OBJ", ob.name, ob.type, ob.parent.name if ob.parent else None, tuple(round(d, 3) for d in ob.dimensions),
          len(ob.data.shape_keys.key_blocks) if ob.type == "MESH" and ob.data.shape_keys else 0)
rig = bpy.data.objects["Woman_rig"]
print("BONES", len(rig.data.bones), [b.name for b in rig.data.bones])
bpy.ops.wm.save_as_mainfile(filepath=out)
