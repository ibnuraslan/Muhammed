"""All humans for SurgeonBrandsLivers (MPFB2 + MakeHuman CC0 assets). Generic people, no likeness.
blender -b --python 01_build_people.py -- <out.blend>"""
import sys
import bpy
from bl_ext.user_default.mpfb.services.humanservice import HumanService

out = sys.argv[sys.argv.index("--") + 1]
for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob, do_unlink=True)

SCRUB_TEAL = (0.30, 0.55, 0.55, 1)
SCRUB_CEIL = (0.38, 0.50, 0.75, 1)
GLOVE = (0.42, 0.38, 0.85, 1)


def tint(rig, part, rgb):
    """multiply the diffuse texture of every mesh child whose name ends in <part>"""
    for ch in rig.children:
        if ch.type == 'MESH' and ch.name.split(".")[-1] == part:
            for m in ch.data.materials:
                if m.get("tinted"):
                    continue
                m["tinted"] = 1
                for nd in list(m.node_tree.nodes):
                    if nd.type == 'TEX_IMAGE' and nd.image and "diffuse" in nd.image.name.lower():
                        for lk in list(nd.outputs['Color'].links):
                            mx = m.node_tree.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'
                            mx.inputs['Factor'].default_value = 1.0; mx.inputs['B'].default_value = rgb
                            m.node_tree.links.new(nd.outputs['Color'], mx.inputs['A']); m.node_tree.links.new(mx.outputs['Result'], lk.to_socket)


def person(name, gender, age, race, hair, clothes, skin, muscle=0.5, weight=0.5, height=None):
    info = HumanService._create_default_human_info_dict()
    info["name"] = name
    info["phenotype"] = {"gender": gender, "age": age, "muscle": muscle, "weight": weight, "proportions": 0.6,
                         "height": height if height is not None else (0.55 if gender > 0.5 else 0.45),
                         "cupsize": 0.5, "firmness": 0.5, "race": race}
    info["rig"] = "default"
    info["eyes"] = "high-poly/high-poly.mhclo"; info["eyebrows"] = "eyebrow001/eyebrow001.mhclo"
    info["eyelashes"] = "eyelashes01/eyelashes01.mhclo"; info["teeth"] = "teeth_base/teeth_base.mhclo"
    info["tongue"] = "tongue01/tongue01.mhclo"; info["hair"] = hair
    info["clothes"] = clothes
    info["skin_mhmat"] = skin; info["skin_material_type"] = "ENHANCED_SSS"; info["eyes_material_type"] = "PROCEDURAL_EYES"
    st = HumanService.get_default_deserialization_settings(); st["subdiv_levels"] = 1
    HumanService.deserialize_from_dict(info, st)
    return bpy.data.objects[name]


# Surgeon 1: scrubs (casualsuit01 tinted teal) + hearing-room suit (elegantsuit01); hair hidden under the cap in the OR
s1 = person("Surgeon1", 1.0, 0.52, {"asian": 0.25, "caucasian": 0.6, "african": 0.15}, "short02/short02.mhclo",
            ["male_casualsuit01/male_casualsuit01.mhclo", "male_elegantsuit01/male_elegantsuit01.mhclo", "shoes02/shoes02.mhclo"],
            "middleage_caucasian_male/middleage_caucasian_male.mhmat", muscle=0.5, weight=0.55)
tint(s1, "male_casualsuit01", SCRUB_TEAL)
# Patient: hospital gown (male_casualsuit06, tinted pale blue) + home clothes (female_casualsuit02)
pt = person("Patient", 0.0, 0.40, {"asian": 0.1, "caucasian": 0.7, "african": 0.2}, "bob02/bob02.mhclo",
            ["female_casualsuit02/female_casualsuit02.mhclo", "male_casualsuit06/male_casualsuit06.mhclo", "shoes01/shoes01.mhclo"],
            "young_caucasian_female/young_caucasian_female.mhmat", weight=0.5)
tint(pt, "male_casualsuit06", (0.75, 0.85, 0.95, 1))
# Surgeon 2: a different person (female, darker skin, slimmer), ceil-blue scrubs
s2 = person("Surgeon2", 0.0, 0.5, {"asian": 0.05, "caucasian": 0.1, "african": 0.85}, "",
            ["female_casualsuit01/female_casualsuit01.mhclo", "shoes03/shoes03.mhclo"],
            "middleage_african_female/middleage_african_female.mhmat", weight=0.45, muscle=0.5)
tint(s2, "female_casualsuit01", SCRUB_CEIL)
# Nurse: male, teal scrubs
nu = person("Nurse", 1.0, 0.35, {"asian": 0.7, "caucasian": 0.2, "african": 0.1}, "",
            ["male_casualsuit01/male_casualsuit01.mhclo", "shoes03/shoes03.mhclo"],
            "young_asian_male/young_asian_male.mhmat", weight=0.5)
tint(nu, "male_casualsuit01", (0.36, 0.48, 0.62, 1))
# Gloved hands for the studio macro (a copy of surgeon 2, masked down to forearms + hands later)
gh = person("GloveHands", 0.0, 0.5, {"asian": 0.05, "caucasian": 0.1, "african": 0.85}, "", [],
            "middleage_african_female/middleage_african_female.mhmat", weight=0.45)
# Hearing panel
p1 = person("PanelA", 1.0, 0.75, {"asian": 0.1, "caucasian": 0.5, "african": 0.4}, "short01/short01.mhclo",
            ["male_elegantsuit01/male_elegantsuit01.mhclo", "shoes02/shoes02.mhclo"], "old_african_male/old_african_male.mhmat", weight=0.6)
p2 = person("PanelB", 0.0, 0.62, {"asian": 0.6, "caucasian": 0.35, "african": 0.05}, "bob01/bob01.mhclo",
            ["female_elegantsuit01/female_elegantsuit01.mhclo", "shoes01/shoes01.mhclo"], "middleage_asian_female/middleage_asian_female.mhmat")
p3 = person("PanelC", 1.0, 0.6, {"asian": 0.05, "caucasian": 0.9, "african": 0.05}, "short04/short04.mhclo",
            ["male_casualsuit03/male_casualsuit03.mhclo", "shoes02/shoes02.mhclo"], "old_caucasian_male/old_caucasian_male.mhmat", weight=0.65)

for i, ob in enumerate([o for o in bpy.data.objects if o.type == 'ARMATURE']):
    ob.location.x = i * 1.5
    print("PERSON", ob.name, [c.name for c in ob.children])
bpy.ops.wm.save_as_mainfile(filepath=out)
