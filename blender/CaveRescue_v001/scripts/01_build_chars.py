"""Boys, coach and divers (MPFB2 + MakeHuman CC0 assets).
blender -b --python 01_build_chars.py -- <out.blend>"""
import sys
import bpy
from bl_ext.user_default.mpfb.services.humanservice import HumanService
out = sys.argv[sys.argv.index("--") + 1]
for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob, do_unlink=True)

def tint(rig, cloth_key, rgb, rough=None):
    for ch in rig.children:
        if ch.type == 'MESH' and cloth_key in ch.name:
            for m in ch.data.materials:
                if m.get("tinted"): continue
                m["tinted"] = 1
                for nd in list(m.node_tree.nodes):
                    if nd.type == 'TEX_IMAGE' and nd.image and "diffuse" in nd.image.name.lower():
                        for lk in list(nd.outputs['Color'].links):
                            mx = m.node_tree.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'
                            mx.inputs['Factor'].default_value = 1.0; mx.inputs['B'].default_value = (*rgb, 1)
                            m.node_tree.links.new(nd.outputs['Color'], mx.inputs['A']); m.node_tree.links.new(mx.outputs['Result'], lk.to_socket)

def human(name, gender, age, race, hair, clothes, skin, x, muscle=0.5, weight=0.5, height=0.5, subdiv=1):
    info = HumanService._create_default_human_info_dict()
    info["name"] = name
    info["phenotype"] = {"gender": gender, "age": age, "muscle": muscle, "weight": weight, "proportions": 0.55,
                         "height": height, "cupsize": 0.5, "firmness": 0.5, "race": race}
    info["rig"] = "default"
    info["eyes"] = "high-poly/high-poly.mhclo"; info["eyebrows"] = "eyebrow001/eyebrow001.mhclo"
    info["eyelashes"] = "eyelashes01/eyelashes01.mhclo"; info["teeth"] = "teeth_base/teeth_base.mhclo"
    info["tongue"] = "tongue01/tongue01.mhclo"; info["hair"] = hair
    info["clothes"] = clothes
    info["skin_mhmat"] = skin; info["skin_material_type"] = "ENHANCED_SSS"; info["eyes_material_type"] = "PROCEDURAL_EYES"
    st = HumanService.get_default_deserialization_settings(); st["subdiv_levels"] = subdiv
    HumanService.deserialize_from_dict(info, st)
    rig = bpy.data.objects[name]; rig.location.x = x
    return rig

AS = {"asian": 0.9, "caucasian": 0.05, "african": 0.05}
boys = [("Boy1", 0.22, "short02/short02.mhclo", "male_casualsuit02", (0.75, 0.2, 0.18)),
        ("Boy2", 0.19, "short03/short03.mhclo", "male_casualsuit03", (0.25, 0.4, 0.85)),
        ("Boy3", 0.26, "short01/short01.mhclo", "male_casualsuit05", (0.85, 0.75, 0.3)),
        ("Boy4", 0.21, "short04/short04.mhclo", "male_casualsuit03", (0.3, 0.55, 0.3)),
        ("Boy5", 0.24, "short02/short02.mhclo", "male_casualsuit02", (0.9, 0.9, 0.9))]
for i, (n, age, hair, suit, col) in enumerate(boys):
    r = human(n, 1.0, age, AS, hair, [suit + "/" + suit + ".mhclo", "shoes02/shoes02.mhclo"], "young_asian_male/young_asian_male.mhmat",
              i * 1.0, muscle=0.45, weight=0.4, height=0.45)
    tint(r, suit, col)
c = human("Coach", 1.0, 0.45, AS, "short01/short01.mhclo", ["male_casualsuit01/male_casualsuit01.mhclo", "shoes03/shoes03.mhclo"],
          "young_asian_male/young_asian_male.mhmat", 6, muscle=0.55, weight=0.45, height=0.5)
tint(c, "male_casualsuit01", (0.45, 0.5, 0.55))
divers = [("DiverA", {"asian": 0.1, "caucasian": 0.85, "african": 0.05}, "young_caucasian_male/young_caucasian_male.mhmat"),
          ("DiverB", {"asian": 0.85, "caucasian": 0.1, "african": 0.05}, "middleage_asian_male/middleage_asian_male.mhmat"),
          ("DiverC", {"asian": 0.1, "caucasian": 0.3, "african": 0.6}, "middleage_african_male/middleage_african_male.mhmat")]
for i, (n, race, skin) in enumerate(divers):
    r = human(n, 1.0, 0.5, race, "short04/short04.mhclo" if i != 1 else "short03/short03.mhclo",
              ["male_worksuit01/male_worksuit01.mhclo", "shoes04/shoes04.mhclo"], skin, 8 + i, muscle=0.65, weight=0.5, height=0.55)
    tint(r, "male_worksuit01", (0.05, 0.055, 0.06) if i != 1 else (0.06, 0.08, 0.12))
    tint(r, "shoes04", (0.05, 0.05, 0.05))
crowd = [("Crowd1", 0.0, 0.4, {"asian": 0.9, "caucasian": 0.05, "african": 0.05}, "ponytail01/ponytail01.mhclo", "female_casualsuit02", "young_asian_female/young_asian_female.mhmat", (0.8, 0.5, 0.5)),
         ("Crowd2", 1.0, 0.55, {"asian": 0.9, "caucasian": 0.05, "african": 0.05}, "short02/short02.mhclo", "male_casualsuit05", "middleage_asian_male/middleage_asian_male.mhmat", (0.6, 0.7, 0.9)),
         ("Crowd3", 0.0, 0.6, {"asian": 0.85, "caucasian": 0.1, "african": 0.05}, "bob02/bob02.mhclo", "female_casualsuit01", "middleage_asian_female/middleage_asian_female.mhmat", (0.5, 0.65, 0.5)),
         ("Crowd4", 1.0, 0.42, {"asian": 0.8, "caucasian": 0.15, "african": 0.05}, "short04/short04.mhclo", "male_casualsuit02", "young_asian_male/young_asian_male.mhmat", (0.85, 0.85, 0.7))]
for i, (n, g, age, race, hair, suit, skin, col) in enumerate(crowd):
    r = human(n, g, age, race, hair, [suit + "/" + suit + ".mhclo", "shoes02/shoes02.mhclo"], skin, 12 + i, height=0.5 if g > 0.5 else 0.42, subdiv=0)
    tint(r, suit, col)
for ob in bpy.data.objects:
    if ob.type == 'ARMATURE':
        print("CHAR", ob.name, [ch.name for ch in ob.children], tuple(round(d, 2) for d in ob.dimensions))
bpy.ops.wm.save_as_mainfile(filepath=out)
