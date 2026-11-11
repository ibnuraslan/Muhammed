"""Patient, surgeon, nurse (MPFB2 + MakeHuman CC0). blender -b --python 01_build_humans.py -- <out.blend>"""
import sys, os
import bpy
from bl_ext.user_default.mpfb.services.humanservice import HumanService
from bl_ext.user_default.mpfb.services.targetservice import TargetService
out = sys.argv[sys.argv.index("--") + 1]
for ob in list(bpy.data.objects): bpy.data.objects.remove(ob, do_unlink=True)
EXPR = os.path.expanduser("~/.config/blender/5.2/extensions/user_default/mpfb/data/targets/expression/units/caucasian/")
UNITS = ["eye-left-opened-up", "eye-right-opened-up", "eyebrows-left-up", "eyebrows-right-up", "eyebrows-left-inner-up",
         "eyebrows-right-inner-up", "mouth-open", "mouth-corner-puller", "mouth-upward-retraction", "eye-left-slit", "eye-right-slit",
         "eye-left-closure", "eye-right-closure", "mouth-compression", "mouth-depression"]

def tint(m, col):
    for nd in list(m.node_tree.nodes):
        if nd.type == 'TEX_IMAGE' and nd.image and "diffuse" in nd.image.name.lower():
            for lk in list(nd.outputs['Color'].links):
                mx = m.node_tree.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'
                mx.inputs['Factor'].default_value = 1.0; mx.inputs['B'].default_value = (*col, 1)
                hs = m.node_tree.nodes.new('ShaderNodeHueSaturation'); hs.inputs['Saturation'].default_value = 0.0
                m.node_tree.links.new(nd.outputs['Color'], hs.inputs['Color'])
                m.node_tree.links.new(hs.outputs['Color'], mx.inputs['A']); m.node_tree.links.new(mx.outputs['Result'], lk.to_socket)

def human(name, gender, age, race, hair, clothes, skin, x, weight=0.5, muscle=0.55, height=0.55, eyebrows="eyebrow001/eyebrow001.mhclo"):
    info = HumanService._create_default_human_info_dict()
    info["name"] = name
    info["phenotype"] = {"gender": gender, "age": age, "muscle": muscle, "weight": weight, "proportions": 0.6,
                         "height": height, "cupsize": 0.5, "firmness": 0.5, "race": race}
    info["rig"] = "default"
    info["eyes"] = "high-poly/high-poly.mhclo"; info["eyebrows"] = eyebrows
    info["eyelashes"] = "eyelashes01/eyelashes01.mhclo"; info["teeth"] = "teeth_base/teeth_base.mhclo"
    info["tongue"] = "tongue01/tongue01.mhclo"; info["hair"] = hair
    info["clothes"] = clothes
    info["skin_mhmat"] = skin; info["skin_material_type"] = "ENHANCED_SSS"; info["eyes_material_type"] = "PROCEDURAL_EYES"
    st = HumanService.get_default_deserialization_settings(); st["subdiv_levels"] = 1
    HumanService.deserialize_from_dict(info, st)
    rig = bpy.data.objects[name]; rig.location.x = x
    body = [c for c in rig.children if c.type == 'MESH' and "body" in c.name.lower() or c.name.endswith(".body")]
    print("HUMAN", name, [c.name for c in rig.children])
    return rig

P = human("Patient", 1.0, 0.5, {"asian": 0.1, "caucasian": 0.6, "african": 0.3}, "",
          ["male_casualsuit06/male_casualsuit06.mhclo", "shoes04/shoes04.mhclo"], "middleage_caucasian_male/middleage_caucasian_male.mhmat", 0, weight=0.55)
S = human("Surgeon", 1.0, 0.45, {"asian": 0.6, "caucasian": 0.3, "african": 0.1}, "short02/short02.mhclo",
          ["male_casualsuit06/male_casualsuit06.mhclo", "shoes05/shoes05.mhclo"], "middleage_asian_male/middleage_asian_male.mhmat", 2)
N = human("Nurse", 0.0, 0.4, {"asian": 0.1, "caucasian": 0.2, "african": 0.7}, "bob02/bob02.mhclo",
          ["female_sportsuit01/female_sportsuit01.mhclo", "shoes05/shoes05.mhclo"], "young_african_female/young_african_female.mhmat", 4, height=0.45)
for rig, col in ((S, (0.25, 0.55, 0.55)), (N, (0.35, 0.5, 0.7))):
    for ch in rig.children:
        if ch.type == 'MESH' and ("casualsuit" in ch.name or "sportsuit" in ch.name):
            for m in ch.data.materials: tint(m, col)
# MakeHuman tee texture carries a logo: swap in the cleaned copy (assets/tee_plain_diffuse.png)
TEE = bpy.data.images.load(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "tee_plain_diffuse.png"))
for ob in bpy.data.objects:
    if ob.type == 'MESH' and "casualsuit06" in ob.name:
        for m in ob.data.materials:
            for nd in m.node_tree.nodes:
                if nd.type == 'TEX_IMAGE' and nd.image and "diffuse" in nd.image.name.lower(): nd.image = TEE
# expression shape keys on every body
for rig in (P, S, N):
    for ch in rig.children:
        if ch.type == 'MESH' and ch.name.lower().endswith("body"):
            for u in UNITS: TargetService.load_target(ch, EXPR + u + ".target.gz", weight=0.0, name="X_" + u)
            print("EXPR", ch.name, len(ch.data.shape_keys.key_blocks))
for ob in bpy.data.objects: print("OBJ", ob.name, ob.type, ob.parent.name if ob.parent else None, tuple(round(d, 2) for d in ob.dimensions))
bpy.ops.wm.save_as_mainfile(filepath=out)
