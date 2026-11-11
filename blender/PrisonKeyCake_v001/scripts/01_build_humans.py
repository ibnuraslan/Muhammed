"""All MPFB2 characters for PrisonKeyCake (MakeHuman CC0 assets).
blender -b --python 01_build_humans.py -- <out.blend>"""
import sys
import bpy
from bl_ext.user_default.mpfb.services.humanservice import HumanService
out = sys.argv[sys.argv.index("--") + 1]
for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob, do_unlink=True)

def tint(rig, cloth, rgb):
    for ch in rig.children:
        if ch.type == 'MESH' and ch.name.split(".")[-1] == cloth:
            for m in ch.data.materials:
                for nd in list(m.node_tree.nodes):
                    if nd.type == 'TEX_IMAGE' and nd.image and "diffuse" in nd.image.name.lower():
                        for lk in list(nd.outputs['Color'].links):
                            mx = m.node_tree.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'
                            mx.inputs['Factor'].default_value = 1.0; mx.inputs['B'].default_value = (*rgb, 1)
                            m.node_tree.links.new(nd.outputs['Color'], mx.inputs['A']); m.node_tree.links.new(mx.outputs['Result'], lk.to_socket)

def human(name, x, gender, age, race, hair, clothes, skin, muscle=0.5, weight=0.5, height=0.55, subdiv=1, brow="eyebrow001", tints=()):
    info = HumanService._create_default_human_info_dict()
    info["name"] = name
    info["phenotype"] = {"gender": gender, "age": age, "muscle": muscle, "weight": weight, "proportions": 0.6,
                         "height": height, "cupsize": 0.5, "firmness": 0.5, "race": race}
    info["rig"] = "default"
    info["eyes"] = "high-poly/high-poly.mhclo"; info["eyebrows"] = brow + "/" + brow + ".mhclo"
    info["eyelashes"] = "eyelashes01/eyelashes01.mhclo"; info["teeth"] = "teeth_base/teeth_base.mhclo"
    info["tongue"] = "tongue01/tongue01.mhclo"; info["hair"] = hair
    info["clothes"] = clothes
    info["skin_mhmat"] = skin; info["skin_material_type"] = "ENHANCED_SSS"; info["eyes_material_type"] = "PROCEDURAL_EYES"
    st = HumanService.get_default_deserialization_settings(); st["subdiv_levels"] = subdiv
    HumanService.deserialize_from_dict(info, st)
    rig = bpy.data.objects[name]; rig.location.x = x
    for c, rgb in tints: tint(rig, c, rgb)
    return rig

C = lambda n: n + "/" + n + ".mhclo"
W = {"asian": 0.03, "caucasian": 0.94, "african": 0.03}
human("Prisoner", 0, 1.0, 0.5, W, C("short02"), [C("male_casualsuit01"), C("shoes01")],
      "young_caucasian_male/young_caucasian_male.mhmat", muscle=0.55, weight=0.45, height=0.62,
      tints=(("male_casualsuit01", (0.78, 0.74, 0.62)),))
human("President", 2, 1.0, 0.9, W, C("short04"), [C("male_elegantsuit01"), C("shoes02")],
      "old_caucasian_male/old_caucasian_male.mhmat", muscle=0.45, weight=0.5, height=0.62, brow="eyebrow003",
      tints=(("male_elegantsuit01", (0.35, 0.35, 0.38)),))
human("Visitor", 4, 1.0, 0.62, {"asian": 0.02, "caucasian": 0.9, "african": 0.08}, "", [C("male_casualsuit05"), C("fedora01"), C("shoes03")],
      "middleage_caucasian_male/middleage_caucasian_male.mhmat", muscle=0.5, weight=0.6, height=0.5, brow="eyebrow002",
      tints=(("male_casualsuit05", (0.75, 0.62, 0.5)),))
human("Guard", 6, 1.0, 0.55, W, C("short01"), [C("male_elegantsuit01"), C("fedora_cocked"), C("shoes05")],
      "middleage_caucasian_male/middleage_caucasian_male.mhmat", muscle=0.65, weight=0.65, height=0.6,
      tints=(("male_elegantsuit01", (0.35, 0.42, 0.7)), ("fedora_cocked", (0.25, 0.28, 0.36))))
human("CrowdA", 8, 0.0, 0.45, W, C("bob02"), [C("female_elegantsuit01"), C("shoes04")],
      "young_caucasian_female/young_caucasian_female.mhmat", subdiv=0, height=0.45)
human("CrowdB", 10, 1.0, 0.5, {"asian": 0.05, "caucasian": 0.85, "african": 0.1}, "", [C("male_casualsuit03"), C("fedora01"), C("shoes03")],
      "middleage_caucasian_male/middleage_caucasian_male.mhmat", subdiv=0, height=0.5)
human("CrowdC", 12, 1.0, 0.7, W, C("short03"), [C("male_elegantsuit01"), C("shoes02")],
      "old_caucasian_male/old_caucasian_male.mhmat", subdiv=0, height=0.55, weight=0.6,
      tints=(("male_elegantsuit01", (0.4, 0.33, 0.28)),))
for ob in bpy.data.objects:
    if ob.type == 'ARMATURE':
        print("HUMAN", ob.name, [c.name for c in ob.children], tuple(round(d, 2) for d in ob.dimensions))
bpy.ops.wm.save_as_mainfile(filepath=out)
