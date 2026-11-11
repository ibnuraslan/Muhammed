"""Plus-size woman + two background shoppers (MPFB2, MakeHuman CC0 assets).
blender -b --python 01_build_woman.py -- <out.blend>"""
import sys
import bpy
from bl_ext.user_default.mpfb.services.humanservice import HumanService
out = sys.argv[sys.argv.index("--") + 1]
for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob, do_unlink=True)

def person(name, ph, hair, clothes, skin, tint=None):
    info = HumanService._create_default_human_info_dict()
    info["name"] = name
    info["phenotype"] = dict(ph)
    info["rig"] = "default"
    info["eyes"] = "high-poly/high-poly.mhclo"; info["eyebrows"] = "eyebrow001/eyebrow001.mhclo"
    info["eyelashes"] = "eyelashes01/eyelashes01.mhclo"; info["teeth"] = "teeth_base/teeth_base.mhclo"
    info["tongue"] = "tongue01/tongue01.mhclo"; info["hair"] = hair
    info["clothes"] = clothes
    info["skin_mhmat"] = skin; info["skin_material_type"] = "ENHANCED_SSS"; info["eyes_material_type"] = "PROCEDURAL_EYES"
    st = HumanService.get_default_deserialization_settings(); st["subdiv_levels"] = 1
    HumanService.deserialize_from_dict(info, st)
    rig = bpy.data.objects[name]
    if tint:
        for ch in rig.children:
            key = ch.name.split(".")[-1]
            if ch.type == 'MESH' and key in tint:
                for m in ch.data.materials:
                    for nd in list(m.node_tree.nodes):
                        if nd.type == 'TEX_IMAGE' and nd.image and "diffuse" in nd.image.name.lower():
                            for lk in list(nd.outputs['Color'].links):
                                mx = m.node_tree.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'
                                mx.inputs['Factor'].default_value = 1.0; mx.inputs['B'].default_value = tint[key]
                                m.node_tree.links.new(nd.outputs['Color'], mx.inputs['A']); m.node_tree.links.new(mx.outputs['Result'], lk.to_socket)
    return rig

W = person("Woman", {"gender": 0.0, "age": 0.55, "muscle": 0.35, "weight": 1.0, "proportions": 0.55, "height": 0.45,
                     "cupsize": 0.6, "firmness": 0.4, "race": {"asian": 0.1, "caucasian": 0.55, "african": 0.35}},
           "bob02/bob02.mhclo", ["female_casualsuit01/female_casualsuit01.mhclo", "shoes02/shoes02.mhclo"],
           "middleage_caucasian_female/middleage_caucasian_female.mhmat", tint={"bob02": (0.22, 0.13, 0.08, 1)})
S1 = person("ShopperA", {"gender": 1.0, "age": 0.7, "muscle": 0.5, "weight": 0.6, "proportions": 0.6, "height": 0.55,
                         "cupsize": 0.5, "firmness": 0.5, "race": {"asian": 0.6, "caucasian": 0.3, "african": 0.1}},
            "short02/short02.mhclo", ["male_casualsuit03/male_casualsuit03.mhclo", "shoes03/shoes03.mhclo"],
            "middleage_asian_male/middleage_asian_male.mhmat")
S2 = person("ShopperB", {"gender": 0.0, "age": 0.4, "muscle": 0.5, "weight": 0.45, "proportions": 0.6, "height": 0.5,
                         "cupsize": 0.5, "firmness": 0.5, "race": {"asian": 0.05, "caucasian": 0.15, "african": 0.8}},
            "ponytail01/ponytail01.mhclo", ["female_sportsuit01/female_sportsuit01.mhclo", "shoes02/shoes02.mhclo"],
            "young_african_female/young_african_female.mhmat")
import os
clean = os.path.join(os.path.dirname(os.path.abspath(out)), "assets/tex/woman_tee_clean_diffuse.png")
for m in bpy.data.objects["Woman.female_casualsuit01"].data.materials:
    for nd in m.node_tree.nodes:
        if nd.type == 'TEX_IMAGE' and nd.image and "diffuse" in nd.image.name.lower():
            nd.image = bpy.data.images.load(clean)
S1.location.x = 3; S2.location.x = 6
for ob in bpy.data.objects:
    print("OBJ", ob.name, ob.type, ob.parent.name if ob.parent else None,
          [m.name for m in ob.material_slots] if ob.type == "MESH" else "", tuple(round(d, 3) for d in ob.dimensions))
bpy.ops.wm.save_as_mainfile(filepath=out)
