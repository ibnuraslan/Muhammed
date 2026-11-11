"""All MPFB2 humans for WW1Assassination (MakeHuman CC0 assets). Generic characters, no likenesses.
blender -b --python 01_build_humans.py -- <out.blend>"""
import sys
import bpy
from bl_ext.user_default.mpfb.services.humanservice import HumanService

out = sys.argv[sys.argv.index("--") + 1]
for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob, do_unlink=True)
C = lambda n: f"{n}/{n}.mhclo"
W = {"asian": 0.03, "caucasian": 0.92, "african": 0.05}

def tint(rig, cloth, rgb, mode="MULTIPLY", fac=1.0):
    for ch in rig.children:
        if ch.type == 'MESH' and ch.name.split(".")[-1] == cloth:
            for m in ch.data.materials:
                for nd in list(m.node_tree.nodes):
                    if nd.type == 'TEX_IMAGE' and nd.image and "diffuse" in nd.image.name.lower():
                        for lk in list(nd.outputs['Color'].links):
                            mx = m.node_tree.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = mode
                            mx.inputs['Factor'].default_value = fac; mx.inputs['B'].default_value = (*rgb, 1)
                            m.node_tree.links.new(nd.outputs['Color'], mx.inputs['A']); m.node_tree.links.new(mx.outputs['Result'], lk.to_socket)

def human(name, g, age, weight, hair, clothes, skin, tints=(), sub=1, height=None, muscle=0.5, eyes="high-poly"):
    info = HumanService._create_default_human_info_dict()
    info["name"] = name
    info["phenotype"] = {"gender": g, "age": age, "muscle": muscle, "weight": weight, "proportions": 0.6,
                         "height": height if height is not None else (0.55 if g > 0.5 else 0.45), "cupsize": 0.5, "firmness": 0.5, "race": W}
    info["rig"] = "default"
    info["eyes"] = C(eyes); info["eyebrows"] = C("eyebrow001"); info["eyelashes"] = C("eyelashes01")
    info["teeth"] = C("teeth_base"); info["tongue"] = C("tongue01"); info["hair"] = C(hair) if hair else ""
    info["clothes"] = [C(c) for c in clothes]
    info["skin_mhmat"] = f"{skin}/{skin}.mhmat"; info["skin_material_type"] = "ENHANCED_SSS" if sub else "DEFAULT"
    info["eyes_material_type"] = "PROCEDURAL_EYES"
    st = HumanService.get_default_deserialization_settings(); st["subdiv_levels"] = sub
    HumanService.deserialize_from_dict(info, st)
    rig = bpy.data.objects[name]
    for t in tints: tint(rig, *t)
    print("HUMAN", name, [c.name for c in rig.children])
    return rig

# principals
human("Archduke", 1, 0.62, 0.78, "short02", ["male_elegantsuit01", "shoes02"], "middleage_caucasian_male",
      [("male_elegantsuit01", (0.5, 0.64, 0.82), "MIX", 0.6)], height=0.6)
human("Duchess", 0, 0.55, 0.6, "bob02", ["female_elegantsuit01", "shoes01"], "middleage_caucasian_female",
      [("female_elegantsuit01", (0.97, 0.96, 0.93), "MIX", 0.82)])
human("Driver", 1, 0.45, 0.55, "short01", ["male_worksuit01", "shoes03"], "middleage_caucasian_male",
      [("male_worksuit01", (0.22, 0.24, 0.22))])
human("Gunman", 1, 0.24, 0.35, "short04", ["male_elegantsuit01", "shoes03"], "young_caucasian_male",
      [("male_elegantsuit01", (0.3, 0.28, 0.26), "MIX", 0.35)], height=0.45, muscle=0.4)
human("Bomber", 1, 0.3, 0.45, "short03", ["male_elegantsuit01", "fedora01", "shoes03"], "young_caucasian_male2",
      [("male_elegantsuit01", (0.42, 0.36, 0.3), "MIX", 0.4)])
human("NerveA", 1, 0.27, 0.4, "short01", ["male_elegantsuit01", "shoes03"], "young_caucasian_male",
      [("male_elegantsuit01", (0.36, 0.3, 0.24), "MIX", 0.45)], height=0.5)
human("NerveB", 1, 0.26, 0.45, "short02", ["male_elegantsuit01", "fedora_cocked", "shoes03"], "young_caucasian_male2",
      [("male_elegantsuit01", (0.36, 0.38, 0.42), "MIX", 0.4)])
human("Officer", 1, 0.5, 0.6, "short02", ["male_elegantsuit01", "shoes02"], "middleage_caucasian_male",
      [("male_elegantsuit01", (0.16, 0.2, 0.3))])
# crowd bases (no subdiv)
human("CrowdM1", 1, 0.5, 0.6, "short02", ["male_elegantsuit01", "fedora01", "shoes02"], "middleage_caucasian_male",
      [("male_elegantsuit01", (0.35, 0.3, 0.26))], sub=0, eyes="low-poly")
human("CrowdM2", 1, 0.4, 0.5, "short01", ["male_elegantsuit01", "fedora_cocked", "shoes03"], "young_caucasian_male",
      [("male_elegantsuit01", (0.5, 0.45, 0.38), "MIX", 0.45)], sub=0, eyes="low-poly")
human("CrowdM3", 1, 0.7, 0.7, "short03", ["male_worksuit01", "shoes03"], "old_caucasian_male",
      [("male_worksuit01", (0.4, 0.36, 0.3))], sub=0, eyes="low-poly")
human("CrowdF1", 0, 0.35, 0.5, "long01", ["female_elegantsuit01", "shoes01"], "young_caucasian_female",
      [("female_elegantsuit01", (0.55, 0.42, 0.38), "MIX", 0.55)], sub=0, eyes="low-poly")
human("CrowdF2", 0, 0.5, 0.6, "bob01", ["female_elegantsuit01", "shoes01"], "middleage_caucasian_female",
      [("female_elegantsuit01", (0.45, 0.35, 0.45))], sub=0, eyes="low-poly")
human("CrowdF3", 0, 0.3, 0.45, "braid01", ["female_elegantsuit01", "shoes01"], "young_caucasian_female2",
      [("female_elegantsuit01", (0.32, 0.38, 0.5), "MIX", 0.55)], sub=0, eyes="low-poly")
for ob in bpy.data.objects:
    if ob.type == 'ARMATURE': ob.location = (0, 0, 0)
bpy.ops.wm.save_as_mainfile(filepath=out)
print("SAVED", out)
