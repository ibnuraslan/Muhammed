"""All ShoeBomber humans (MPFB2 + MakeHuman CC0). blender -b --python 01_build_humans.py -- <out.blend>"""
import sys, bpy
from bl_ext.user_default.mpfb.services.humanservice import HumanService
out = sys.argv[sys.argv.index("--") + 1]
for ob in list(bpy.data.objects): bpy.data.objects.remove(ob, do_unlink=True)

def tint(rig, cname, col):
    for ch in rig.children:
        if ch.type == 'MESH' and ch.name.split(".")[-1] == cname:
            for m in ch.data.materials:
                for nd in list(m.node_tree.nodes):
                    if nd.type == 'TEX_IMAGE' and nd.image and "diffuse" in nd.image.name.lower():
                        for lk in list(nd.outputs['Color'].links):
                            mx = m.node_tree.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'
                            mx.inputs['Factor'].default_value = 1.0; mx.inputs['B'].default_value = (*col, 1)
                            m.node_tree.links.new(nd.outputs['Color'], mx.inputs['A']); m.node_tree.links.new(mx.outputs['Result'], lk.to_socket)

def human(name, gender, age, race, hair, clothes, skin, x, height=0.55, weight=0.5, muscle=0.5, sub=1, tints=None, brows="eyebrow001"):
    info = HumanService._create_default_human_info_dict()
    info["name"] = name
    info["phenotype"] = {"gender": gender, "age": age, "muscle": muscle, "weight": weight, "proportions": 0.6,
                         "height": height, "cupsize": 0.5, "firmness": 0.5, "race": race}
    info["rig"] = "default"
    info["eyes"] = "high-poly/high-poly.mhclo"; info["eyebrows"] = brows + "/" + brows + ".mhclo"
    info["eyelashes"] = "eyelashes01/eyelashes01.mhclo"; info["teeth"] = "teeth_base/teeth_base.mhclo"
    info["tongue"] = "tongue01/tongue01.mhclo"; info["hair"] = hair
    info["clothes"] = clothes
    info["skin_mhmat"] = skin; info["skin_material_type"] = "ENHANCED_SSS"; info["eyes_material_type"] = "PROCEDURAL_EYES"
    st = HumanService.get_default_deserialization_settings(); st["subdiv_levels"] = sub
    HumanService.deserialize_from_dict(info, st)
    rig = bpy.data.objects[name]; rig.location.x = x
    for c, col in (tints or {}).items(): tint(rig, c, col)
    return rig

C = lambda n: "%s/%s.mhclo" % (n, n)
# bomber: tall, lean, generic; sneakers are separate props (no MPFB shoes)
human("Bomber", 1.0, 0.5, {"asian": 0.1, "caucasian": 0.6, "african": 0.3}, C("short02"), [C("male_casualsuit04")],
      "middleage_caucasian_male/middleage_caucasian_male.mhmat", 0, height=0.72, weight=0.42, sub=1)
human("Attendant", 0.0, 0.45, {"asian": 0.15, "caucasian": 0.8, "african": 0.05}, C("ponytail01"), [C("female_elegantsuit01"), C("shoes02")],
      "young_caucasian_female/young_caucasian_female.mhmat", 2, height=0.5, sub=1, tints={"female_elegantsuit01": (0.25, 0.3, 0.5)})
human("Steward", 1.0, 0.42, {"asian": 0.1, "caucasian": 0.1, "african": 0.8}, C("short01"), [C("male_elegantsuit01"), C("shoes03")],
      "young_african_male/young_african_male.mhmat", 4, height=0.6, muscle=0.65, sub=1, tints={"male_elegantsuit01": (0.3, 0.35, 0.55)})
human("PaxA", 1.0, 0.6, {"asian": 0.05, "caucasian": 0.9, "african": 0.05}, C("short04"), [C("male_casualsuit03"), C("shoes01")],
      "middleage_caucasian_male/middleage_caucasian_male.mhmat", 6, height=0.6, weight=0.65, muscle=0.6, sub=0)
human("PaxB", 1.0, 0.4, {"asian": 0.85, "caucasian": 0.1, "african": 0.05}, C("short03"), [C("male_casualsuit05"), C("shoes04")],
      "young_asian_male/young_asian_male.mhmat", 8, height=0.55, muscle=0.6, sub=0)
human("PaxC", 0.0, 0.55, {"asian": 0.05, "caucasian": 0.25, "african": 0.7}, C("afro01"), [C("female_sportsuit01"), C("shoes05")],
      "middleage_african_female/middleage_african_female.mhmat", 10, height=0.45, sub=0)
human("PaxD", 0.0, 0.7, {"asian": 0.1, "caucasian": 0.85, "african": 0.05}, C("bob01"), [C("female_casualsuit02"), C("shoes02")],
      "old_caucasian_female/old_caucasian_female.mhmat", 12, height=0.4, weight=0.6, sub=0)
human("Traveller", 1.0, 0.45, {"asian": 0.2, "caucasian": 0.4, "african": 0.4}, C("short01"), [C("male_casualsuit01")],
      "young_caucasian_male/young_caucasian_male.mhmat", 14, height=0.65, sub=1)
human("Officer", 1.0, 0.5, {"asian": 0.1, "caucasian": 0.7, "african": 0.2}, C("short04"), [C("male_worksuit01"), C("shoes03")],
      "middleage_caucasian_male/middleage_caucasian_male.mhmat", 16, height=0.6, sub=0, tints={"male_worksuit01": (0.35, 0.4, 0.5)})
# sleeping passengers (background, low subdiv)
human("Sleeper1", 1.0, 0.55, {"asian": 0.6, "caucasian": 0.3, "african": 0.1}, C("short03"), [C("male_casualsuit06"), C("shoes01")],
      "middleage_asian_male/middleage_asian_male.mhmat", 18, height=0.55, sub=0, tints={"male_casualsuit06": (0.35, 0.3, 0.28)})
human("Sleeper2", 0.0, 0.35, {"asian": 0.1, "caucasian": 0.7, "african": 0.2}, C("long01"), [C("female_casualsuit01"), C("shoes05")],
      "young_caucasian_female/young_caucasian_female.mhmat", 20, height=0.45, sub=0, tints={"female_casualsuit01": (0.45, 0.3, 0.3)})
human("Sleeper3", 1.0, 0.75, {"asian": 0.05, "caucasian": 0.25, "african": 0.7}, C("short04"), [C("male_casualsuit01"), C("shoes03")],
      "old_african_male/old_african_male.mhmat", 22, height=0.5, weight=0.65, sub=0)
human("Sleeper4", 0.0, 0.6, {"asian": 0.7, "caucasian": 0.2, "african": 0.1}, C("bob02"), [C("female_elegantsuit01"), C("shoes02")],
      "middleage_asian_female/middleage_asian_female.mhmat", 24, height=0.42, sub=0, tints={"female_elegantsuit01": (0.3, 0.4, 0.35)})
for ob in bpy.data.objects:
    if ob.type == 'ARMATURE': print("HUMAN", ob.name, [c.name for c in ob.children], tuple(round(d, 2) for d in ob.dimensions))
bpy.ops.wm.save_as_mainfile(filepath=out)
