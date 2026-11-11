"""Cast for ToddlerWell (MPFB2 + MakeHuman CC0 assets).
blender -b --python 01_build_cast.py -- <out.blend>"""
import sys
import bpy
from bl_ext.user_default.mpfb.services.humanservice import HumanService

out = sys.argv[sys.argv.index("--") + 1]
for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob, do_unlink=True)

def tint(rig, cloth_key, rgb):
    for ch in rig.children:
        if ch.type == 'MESH' and cloth_key in ch.name:
            for m in ch.data.materials:
                for nd in list(m.node_tree.nodes):
                    if nd.type == 'TEX_IMAGE' and nd.image and "diffuse" in nd.image.name.lower():
                        for lk in list(nd.outputs['Color'].links):
                            mx = m.node_tree.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'
                            mx.inputs['Factor'].default_value = 1.0; mx.inputs['B'].default_value = (*rgb, 1)
                            m.node_tree.links.new(nd.outputs['Color'], mx.inputs['A']); m.node_tree.links.new(mx.outputs['Result'], lk.to_socket)

def human(name, gender, age, race, hair, clothes, skin, x, muscle=0.5, weight=0.5, height=0.5, sub=1, tints=()):
    info = HumanService._create_default_human_info_dict()
    info["name"] = name
    info["phenotype"] = {"gender": gender, "age": age, "muscle": muscle, "weight": weight, "proportions": 0.6,
                         "height": height, "cupsize": 0.5, "firmness": 0.5, "race": race}
    info["rig"] = "default"
    info["eyes"] = "high-poly/high-poly.mhclo"; info["eyebrows"] = "eyebrow001/eyebrow001.mhclo"
    info["eyelashes"] = "eyelashes01/eyelashes01.mhclo"; info["teeth"] = "teeth_base/teeth_base.mhclo"
    info["tongue"] = "tongue01/tongue01.mhclo"; info["hair"] = hair
    info["clothes"] = clothes
    info["skin_mhmat"] = skin; info["skin_material_type"] = "ENHANCED_SSS"; info["eyes_material_type"] = "PROCEDURAL_EYES"
    st = HumanService.get_default_deserialization_settings(); st["subdiv_levels"] = sub
    HumanService.deserialize_from_dict(info, st)
    rig = bpy.data.objects[name]
    rig.location.x = x
    for k, rgb in tints: tint(rig, k, rgb)
    return rig

C = "/{0}.mhclo"
def c(n): return n + "/" + n + ".mhclo"
CAU = {"asian": 0.05, "caucasian": 0.9, "african": 0.05}
MIX = {"asian": 0.2, "caucasian": 0.6, "african": 0.2}
AFR = {"asian": 0.05, "caucasian": 0.1, "african": 0.85}
ASI = {"asian": 0.85, "caucasian": 0.1, "african": 0.05}
HIVIS = (0.42, 0.45, 0.55)   # dark work dungarees; the hi-vis vest is added in the scene build
human("Toddler", 1.0, 0.03, MIX, c("short02"), [c("male_casualsuit04"), c("shoes01")], "young_caucasian_male/young_caucasian_male.mhmat", 0,
      weight=0.6)
human("Teen", 1.0, 0.30, MIX, c("short04"), [c("male_casualsuit01"), c("shoes02")], "young_caucasian_male2/young_caucasian_male2.mhmat", 1,
      muscle=0.45, weight=0.3, height=0.75)
human("ResA", 1.0, 0.55, AFR, c("short01"), [c("male_worksuit01"), c("shoes03")], "middleage_african_male/middleage_african_male.mhmat", 2,
      muscle=0.65, weight=0.6, height=0.6, tints=(("male_worksuit01", HIVIS),))
human("ResB", 1.0, 0.45, CAU, c("short03"), [c("male_worksuit01"), c("shoes03")], "middleage_caucasian_male/middleage_caucasian_male.mhmat", 3,
      muscle=0.6, weight=0.65, height=0.5, tints=(("male_worksuit01", (0.5, 0.5, 0.5)),))
human("ResC", 1.0, 0.62, ASI, c("short02"), [c("male_worksuit01"), c("shoes03")], "middleage_asian_male/middleage_asian_male.mhmat", 4,
      muscle=0.55, weight=0.55, height=0.45, tints=(("male_worksuit01", HIVIS),))
human("Mother", 0.0, 0.42, MIX, c("ponytail01"), [c("female_elegantsuit01"), c("shoes05")], "young_caucasian_female/young_caucasian_female.mhmat", 5,
      weight=0.45, height=0.5)
human("Crowd1", 0.0, 0.7, AFR, c("bob02"), [c("male_casualsuit03"), c("shoes05")], "old_african_female/old_african_female.mhmat", 6, sub=0)
human("Crowd2", 1.0, 0.8, CAU, c("short01"), [c("male_casualsuit03"), c("shoes03")], "old_caucasian_male/old_caucasian_male.mhmat", 7, sub=0, weight=0.7)
human("Crowd3", 1.0, 0.35, ASI, c("short03"), [c("male_casualsuit05"), c("shoes04")], "young_asian_male/young_asian_male.mhmat", 8, sub=0)
human("Crowd4", 0.0, 0.3, MIX, c("long01"), [c("female_sportsuit01"), c("shoes06")], "young_asian_female/young_asian_female.mhmat", 9, sub=0)
human("Operator", 1.0, 0.5, MIX, c("short01"), [c("male_worksuit01"), c("shoes03")], "middleage_caucasian_male/middleage_caucasian_male.mhmat", 10, sub=0,
      tints=(("male_worksuit01", HIVIS),))
for ob in bpy.data.objects:
    if ob.type == 'ARMATURE':
        print("CAST", ob.name, round(max(ch.dimensions.z for ch in ob.children if ch.type == 'MESH'), 3), [ch.name for ch in ob.children])
bpy.ops.wm.save_as_mainfile(filepath=out)
