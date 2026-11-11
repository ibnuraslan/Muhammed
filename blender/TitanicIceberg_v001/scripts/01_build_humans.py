"""Five MPFB2 humans (MakeHuman CC0): steward, deckhand, darkroom tech, two experts.
blender -b --python 01_build_humans.py -- <out.blend>"""
import sys, bpy
from bl_ext.user_default.mpfb.services.humanservice import HumanService
out = sys.argv[sys.argv.index("--") + 1]
for ob in list(bpy.data.objects): bpy.data.objects.remove(ob, do_unlink=True)

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

def human(name, gender, age, race, hair, clothes, skin, x, weight=0.5, tints=()):
    info = HumanService._create_default_human_info_dict()
    info["name"] = name
    info["phenotype"] = {"gender": gender, "age": age, "muscle": 0.55, "weight": weight, "proportions": 0.6,
                         "height": 0.55, "cupsize": 0.5, "firmness": 0.5, "race": race}
    info["rig"] = "default"
    info["eyes"] = "high-poly/high-poly.mhclo"; info["eyebrows"] = "eyebrow001/eyebrow001.mhclo"
    info["eyelashes"] = "eyelashes01/eyelashes01.mhclo"; info["teeth"] = "teeth_base/teeth_base.mhclo"
    info["tongue"] = "tongue01/tongue01.mhclo"; info["hair"] = hair
    info["clothes"] = clothes
    info["skin_mhmat"] = skin; info["skin_material_type"] = "ENHANCED_SSS"; info["eyes_material_type"] = "PROCEDURAL_EYES"
    st = HumanService.get_default_deserialization_settings(); st["subdiv_levels"] = 1
    HumanService.deserialize_from_dict(info, st)
    rig = bpy.data.objects[name]; rig.location.x = x
    for c, rgb in tints: tint(rig, c, rgb)
    return rig

W = {"asian": 0.05, "caucasian": 0.9, "african": 0.05}
human("Steward", 1.0, 0.45, W, "short02/short02.mhclo",
      ["male_elegantsuit01/male_elegantsuit01.mhclo", "fedora01/fedora01.mhclo", "shoes02/shoes02.mhclo"],
      "middleage_caucasian_male/middleage_caucasian_male.mhmat", 0, tints=(("male_elegantsuit01", (0.18, 0.22, 0.36)), ("fedora01", (0.25, 0.25, 0.3))))
human("Deckhand", 1.0, 0.35, {"asian": 0.05, "caucasian": 0.75, "african": 0.2}, "short04/short04.mhclo",
      ["male_worksuit01/male_worksuit01.mhclo", "shoes03/shoes03.mhclo"],
      "young_caucasian_male/young_caucasian_male.mhmat", 2, tints=(("male_worksuit01", (0.45, 0.42, 0.38)),))
human("Tech", 1.0, 0.5, {"asian": 0.1, "caucasian": 0.85, "african": 0.05}, "short01/short01.mhclo",
      ["male_casualsuit02/male_casualsuit02.mhclo", "shoes03/shoes03.mhclo"],
      "middleage_caucasian_male/middleage_caucasian_male.mhmat", 4, weight=0.6)
human("ExpertA", 1.0, 0.8, W, "short03/short03.mhclo",
      ["male_elegantsuit01/male_elegantsuit01.mhclo", "shoes02/shoes02.mhclo"],
      "old_caucasian_male/old_caucasian_male.mhmat", 6, weight=0.62, tints=(("male_elegantsuit01", (0.35, 0.3, 0.26)),))
human("ExpertB", 1.0, 0.6, {"asian": 0.05, "caucasian": 0.6, "african": 0.35}, "short02/short02.mhclo",
      ["male_elegantsuit01/male_elegantsuit01.mhclo", "shoes02/shoes02.mhclo"],
      "middleage_african_male/middleage_african_male.mhmat", 8, tints=(("male_elegantsuit01", (0.22, 0.22, 0.24)),))
for ob in bpy.data.objects:
    if ob.type == 'ARMATURE': print("HUMAN", ob.name, [c.name for c in ob.children])
bpy.ops.wm.save_as_mainfile(filepath=out)
