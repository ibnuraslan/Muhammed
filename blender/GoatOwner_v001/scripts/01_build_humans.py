"""Build the five MPFB2 humans (MakeHuman CC0). blender -b --python 01_build_humans.py -- <out.blend>"""
import sys, bpy
from bl_ext.user_default.mpfb.services.humanservice import HumanService
out = sys.argv[sys.argv.index("--") + 1]
for ob in list(bpy.data.objects): bpy.data.objects.remove(ob, do_unlink=True)
def tint(rig, cl, col):
    for ch in rig.children:
        if ch.type == 'MESH' and ch.name.split(".")[-1] == cl.split("/")[0]:
            for m in ch.data.materials:
                for nd in list(m.node_tree.nodes):
                    if nd.type == 'TEX_IMAGE' and nd.image and "diffuse" in nd.image.name.lower():
                        for lk in list(nd.outputs['Color'].links):
                            mx = m.node_tree.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'
                            mx.inputs['Factor'].default_value = 1.0; mx.inputs['B'].default_value = col + (1,)
                            m.node_tree.links.new(nd.outputs['Color'], mx.inputs['A']); m.node_tree.links.new(mx.outputs['Result'], lk.to_socket)
def human(name, gender, age, race, hair, clothes, skin, x, muscle=0.5, weight=0.5, height=0.5, tints=()):
    info = HumanService._create_default_human_info_dict(); info["name"] = name
    info["phenotype"] = {"gender": gender, "age": age, "muscle": muscle, "weight": weight, "proportions": 0.6,
                         "height": height, "cupsize": 0.5, "firmness": 0.5, "race": race}
    info["rig"] = "default"
    info["eyes"] = "high-poly/high-poly.mhclo"; info["eyebrows"] = "eyebrow001/eyebrow001.mhclo"
    info["eyelashes"] = "eyelashes01/eyelashes01.mhclo"; info["teeth"] = "teeth_base/teeth_base.mhclo"
    info["tongue"] = "tongue01/tongue01.mhclo"; info["hair"] = hair; info["clothes"] = clothes
    info["skin_mhmat"] = skin; info["skin_material_type"] = "ENHANCED_SSS"; info["eyes_material_type"] = "PROCEDURAL_EYES"
    st = HumanService.get_default_deserialization_settings(); st["subdiv_levels"] = 1
    HumanService.deserialize_from_dict(info, st)
    rig = bpy.data.objects[name]; rig.location.x = x
    for cl, col in tints: tint(rig, cl, col)
    return rig
CA = {"asian": 0.05, "caucasian": 0.9, "african": 0.05}
human("Owner", 1.0, 0.62, CA, "short02/short02.mhclo", ["male_worksuit01/male_worksuit01.mhclo", "shoes03/shoes03.mhclo"],
      "middleage_caucasian_male/middleage_caucasian_male.mhmat", 0, muscle=0.6, weight=0.62, height=0.6,
      tints=[("male_worksuit01/x", (0.62, 0.55, 0.45))])
human("Passer", 1.0, 0.5, {"asian": 0.1, "caucasian": 0.2, "african": 0.7}, "short01/short01.mhclo",
      ["male_casualsuit03/male_casualsuit03.mhclo", "shoes01/shoes01.mhclo"], "young_african_male/young_african_male.mhmat", 2)
khaki = (0.55, 0.5, 0.36)
human("OffA", 1.0, 0.5, {"asian": 0.3, "caucasian": 0.6, "african": 0.1}, "short03/short03.mhclo",
      ["male_casualsuit01/male_casualsuit01.mhclo", "shoes03/shoes03.mhclo"], "young_caucasian_male/young_caucasian_male.mhmat", 4,
      muscle=0.6, tints=[("male_casualsuit01/x", khaki)])
human("OffB", 0.0, 0.45, {"asian": 0.1, "caucasian": 0.3, "african": 0.6}, "bob01/bob01.mhclo",
      ["female_casualsuit01/female_casualsuit01.mhclo", "shoes03/shoes03.mhclo"], "middleage_african_female/middleage_african_female.mhmat", 6,
      tints=[("female_casualsuit01/x", khaki)])
human("Rescuer", 0.0, 0.4, {"asian": 0.2, "caucasian": 0.75, "african": 0.05}, "ponytail01/ponytail01.mhclo",
      ["female_casualsuit01/female_casualsuit01.mhclo", "shoes01/shoes01.mhclo"], "young_caucasian_female/young_caucasian_female.mhmat", 8,
      tints=[("female_casualsuit01/x", (0.42, 0.55, 0.4))])
for ob in bpy.data.objects:
    if ob.type == 'ARMATURE': print("HUMAN", ob.name, [c.name for c in ob.children], len(ob.data.bones))
bpy.ops.wm.save_as_mainfile(filepath=out)
