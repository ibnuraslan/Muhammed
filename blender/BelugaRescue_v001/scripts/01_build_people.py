"""Freediver + gallery/deck spectators + keeper (MPFB2 + MakeHuman CC0 assets).
blender -b --python 01_build_people.py -- <out.blend>"""
import sys
import bpy
from bl_ext.user_default.mpfb.services.humanservice import HumanService

out = sys.argv[sys.argv.index("--") + 1]
for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob, do_unlink=True)

def tint(rig, cloth, rgb, rough=None):
    for ch in rig.children:
        if ch.type == 'MESH' and ch.name.split(".")[-1] == cloth.split("/")[0]:
            for m in ch.data.materials:
                nt = m.node_tree
                for nd in list(nt.nodes):
                    if nd.type == 'TEX_IMAGE' and nd.image and "diffuse" in nd.image.name.lower():
                        for lk in list(nd.outputs['Color'].links):
                            mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'
                            mx.inputs['Factor'].default_value = 1.0; mx.inputs['B'].default_value = (*rgb, 1)
                            nt.links.new(nd.outputs['Color'], mx.inputs['A']); nt.links.new(mx.outputs['Result'], lk.to_socket)
                if rough is not None:
                    for nd in nt.nodes:
                        if nd.type == 'BSDF_PRINCIPLED':
                            for lk in list(nd.inputs['Roughness'].links): nt.links.remove(lk)
                            nd.inputs['Roughness'].default_value = rough

def human(name, gender, age, race, hair, clothes, skin, x, subdiv=1, muscle=0.5, weight=0.5, height=None):
    info = HumanService._create_default_human_info_dict()
    info["name"] = name
    info["phenotype"] = {"gender": gender, "age": age, "muscle": muscle, "weight": weight, "proportions": 0.6,
                         "height": height if height is not None else (0.62 if gender > 0.5 else 0.78),
                         "cupsize": 0.5, "firmness": 0.5, "race": race}
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

EU = {"asian": 0.05, "caucasian": 0.9, "african": 0.05}
AS = {"asian": 0.85, "caucasian": 0.1, "african": 0.05}
AF = {"asian": 0.05, "caucasian": 0.1, "african": 0.85}
d = human("Diver", 0.0, 0.32, {"asian": 0.1, "caucasian": 0.8, "african": 0.1}, "ponytail01/ponytail01.mhclo",
          ["female_sportsuit01/female_sportsuit01.mhclo"], "young_caucasian_female/young_caucasian_female.mhmat", 0, muscle=0.62, weight=0.42, height=0.85)
tint(d, "female_sportsuit01", (0.16, 0.17, 0.18), rough=0.42)
k = human("Keeper", 1.0, 0.4, AF, "short02/short02.mhclo", ["male_casualsuit01/male_casualsuit01.mhclo", "shoes03/shoes03.mhclo"],
          "young_african_male/young_african_male.mhmat", 2, subdiv=0)
tint(k, "male_casualsuit01", (0.2, 0.26, 0.42))
SPEC = [("SpecA", 0.0, 0.3, AS, "bob01/bob01.mhclo", "female_casualsuit02", "young_asian_female", (0.55, 0.3, 0.3)),
        ("SpecB", 1.0, 0.55, EU, "short03/short03.mhclo", "male_casualsuit03", "middleage_caucasian_male", (0.5, 0.55, 0.6)),
        ("SpecC", 0.0, 0.12, EU, "ponytail01/ponytail01.mhclo", "female_casualsuit01", "young_caucasian_female2", (0.7, 0.62, 0.4)),
        ("SpecD", 1.0, 0.25, AF, "afro01/afro01.mhclo", "male_casualsuit02", "young_african_male2" if False else "young_african_male", (0.35, 0.45, 0.35)),
        ("SpecE", 0.0, 0.6, AF, "bob02/bob02.mhclo", "female_casualsuit01", "middleage_african_female", (0.45, 0.35, 0.55)),
        ("SpecF", 1.0, 0.35, AS, "short01/short01.mhclo", "male_casualsuit04", "young_asian_male", (0.6, 0.6, 0.62)),
        ("SpecG", 1.0, 0.05, EU, "short04/short04.mhclo", "male_casualsuit05", "young_caucasian_male", (0.4, 0.5, 0.75))]
for i, (nm, g, a, r, h, cl, sk, col) in enumerate(SPEC):
    s = human(nm, g, a, r, h, [cl + "/" + cl + ".mhclo", "shoes0%d/shoes0%d.mhclo" % (1 + i % 5, 1 + i % 5)], sk + "/" + sk + ".mhmat",
              4 + 2 * i, subdiv=0, height=(0.4 if a < 0.15 else None))
    tint(s, cl, col)
for ob in bpy.data.objects:
    if ob.type == 'ARMATURE':
        print("HUMAN", ob.name, [c.name for c in ob.children])
bpy.ops.wm.save_as_mainfile(filepath=out)
