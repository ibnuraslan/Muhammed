"""Two paramedics (MPFB2 + MakeHuman CC0 assets).
blender -b --python 01b_build_medics.py -- <out.blend>"""
import sys
import bpy
from bl_ext.user_default.mpfb.services.humanservice import HumanService

out = sys.argv[sys.argv.index("--") + 1]
for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob, do_unlink=True)

def medic(name, gender, age, race, hair, clothes, shoes, skin, x):
    info = HumanService._create_default_human_info_dict()
    info["name"] = name
    info["phenotype"] = {"gender": gender, "age": age, "muscle": 0.6, "weight": 0.5, "proportions": 0.6,
                         "height": 0.55 if gender > 0.5 else 0.45, "cupsize": 0.5, "firmness": 0.5, "race": race}
    info["rig"] = "default"
    info["eyes"] = "high-poly/high-poly.mhclo"; info["eyebrows"] = "eyebrow001/eyebrow001.mhclo"
    info["eyelashes"] = "eyelashes01/eyelashes01.mhclo"; info["teeth"] = "teeth_base/teeth_base.mhclo"
    info["tongue"] = "tongue01/tongue01.mhclo"; info["hair"] = hair
    info["clothes"] = [clothes, shoes]
    info["skin_mhmat"] = skin; info["skin_material_type"] = "ENHANCED_SSS"; info["eyes_material_type"] = "PROCEDURAL_EYES"
    st = HumanService.get_default_deserialization_settings(); st["subdiv_levels"] = 1
    HumanService.deserialize_from_dict(info, st)
    rig = bpy.data.objects[name]
    rig.location.x = x
    # paramedic navy: tint the clothes
    for ch in rig.children:
        if ch.type == 'MESH' and ch.name.split(".")[-1] == clothes.split("/")[0]:
            for m in ch.data.materials:
                for nd in list(m.node_tree.nodes):
                    if nd.type == 'TEX_IMAGE' and nd.image and "diffuse" in nd.image.name.lower():
                        for lk in list(nd.outputs['Color'].links):
                            mx = m.node_tree.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'
                            mx.inputs['Factor'].default_value = 1.0; mx.inputs['B'].default_value = (0.32, 0.38, 0.55, 1)
                            m.node_tree.links.new(nd.outputs['Color'], mx.inputs['A']); m.node_tree.links.new(mx.outputs['Result'], lk.to_socket)
    return rig

medic("MedicA", 1.0, 0.45, {"asian": 0.05, "caucasian": 0.15, "african": 0.8}, "short01/short01.mhclo",
      "male_casualsuit01/male_casualsuit01.mhclo", "shoes03/shoes03.mhclo", "young_african_male/young_african_male.mhmat", 0)
medic("MedicB", 0.0, 0.42, {"asian": 0.2, "caucasian": 0.75, "african": 0.05}, "ponytail01/ponytail01.mhclo",
      "female_casualsuit01/female_casualsuit01.mhclo", "shoes03/shoes03.mhclo", "young_caucasian_female/young_caucasian_female.mhmat", 2)
for ob in bpy.data.objects:
    if ob.type == 'ARMATURE':
        print("MEDIC", ob.name, [c.name for c in ob.children])
bpy.ops.wm.save_as_mainfile(filepath=out)
