"""All MPFB2 characters for PopeShot (MakeHuman CC0 assets). Each in its own collection, lined up along X.
blender -b --python 01_build_humans.py -- <out.blend>"""
import sys, bpy
from bl_ext.user_default.mpfb.services.humanservice import HumanService
out = sys.argv[sys.argv.index("--") + 1]
for ob in list(bpy.data.objects): bpy.data.objects.remove(ob, do_unlink=True)
C = lambda n: n + "/" + n + ".mhclo"
def human(name, g, age, race, hair, clothes, skin, x, tint=None, weight=0.5, height=None, subdiv=1, brows="eyebrow001"):
    info = HumanService._create_default_human_info_dict(); info["name"] = name
    info["phenotype"] = {"gender": g, "age": age, "muscle": 0.5, "weight": weight, "proportions": 0.6,
                         "height": height if height is not None else (0.55 if g > 0.5 else 0.45), "cupsize": 0.5, "firmness": 0.5, "race": race}
    info["rig"] = "default"; info["eyes"] = "high-poly/high-poly.mhclo"; info["eyebrows"] = C(brows)
    info["eyelashes"] = C("eyelashes01"); info["teeth"] = C("teeth_base"); info["tongue"] = C("tongue01")
    info["hair"] = C(hair) if hair else ""; info["clothes"] = [C(c) for c in clothes]
    info["skin_mhmat"] = skin + "/" + skin + ".mhmat"; info["skin_material_type"] = "ENHANCED_SSS"; info["eyes_material_type"] = "PROCEDURAL_EYES"
    st = HumanService.get_default_deserialization_settings(); st["subdiv_levels"] = subdiv
    HumanService.deserialize_from_dict(info, st)
    rig = bpy.data.objects[name]; rig.location.x = x
    col = bpy.data.collections.new("CH_" + name); bpy.context.scene.collection.children.link(col)
    for o in [rig] + list(rig.children):
        for c in list(o.users_collection): c.objects.unlink(o)
        col.objects.link(o)
    for ch in rig.children:
        key = ch.name.split(".")[-1]
        if tint and key in tint:
            for m in ch.data.materials:
                if not m or not m.node_tree: continue
                for nd in list(m.node_tree.nodes):
                    if nd.type == 'TEX_IMAGE' and nd.image and "diffuse" in nd.image.name.lower():
                        for lk in list(nd.outputs['Color'].links):
                            # desaturate the print away, then tint: removes any shirt graphics
                            hs = m.node_tree.nodes.new('ShaderNodeHueSaturation'); hs.inputs['Saturation'].default_value = 0.0
                            mx = m.node_tree.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'
                            mx.inputs['Factor'].default_value = 1.0; mx.inputs['B'].default_value = tint[key] + (1,)
                            m.node_tree.links.new(nd.outputs['Color'], hs.inputs['Color']); m.node_tree.links.new(hs.outputs['Color'], mx.inputs['A'])
                            m.node_tree.links.new(mx.outputs['Result'], lk.to_socket)
    print("HUMAN", name, [c.name for c in rig.children])
    return rig
W = {"asian": 0.05, "caucasian": 0.9, "african": 0.05}
human("Pope", 1.0, 0.88, W, "short02", ["male_elegantsuit01", "shoes05"], "old_caucasian_male", 0,
      tint={"male_elegantsuit01": (1.6, 1.58, 1.5), "shoes05": (0.6, 0.35, 0.2)}, weight=0.6, height=0.5, subdiv=1)
human("Prisoner", 1.0, 0.45, {"asian": 0.1, "caucasian": 0.7, "african": 0.2}, "short04", ["male_casualsuit03", "shoes03"], "young_caucasian_male", 2,
      tint={"male_casualsuit03": (0.45, 0.42, 0.38)}, subdiv=1)
for i, (nm, sk, hr) in enumerate((("AideA", "middleage_caucasian_male", "short02"), ("AideB", "old_caucasian_male", "short01"),
                                  ("GuardA", "middleage_caucasian_male", "short03"), ("GuardB", "young_caucasian_male", "short01"))):
    human(nm, 1.0, 0.55 + 0.08 * (i % 2), W, hr, ["male_elegantsuit01", "shoes01"], sk, 4 + 2 * i,
          tint={"male_elegantsuit01": (0.12, 0.12, 0.14)} if nm.startswith("Guard") else {"male_elegantsuit01": (0.08, 0.07, 0.07)}, subdiv=0)
for i, nm in enumerate(("SurgA", "SurgB", "SurgC", "Nurse")):
    g = 0.0 if nm in ("SurgC", "Nurse") else 1.0
    human(nm, g, 0.5, W, "" if g else "bob01", ["male_casualsuit04" if g else "female_casualsuit01", "shoes03"],
          ("middleage_caucasian_male", "young_african_male", "young_caucasian_female", "middleage_asian_female")[i], 12 + 2 * i,
          tint={"male_casualsuit04": (0.35, 0.6, 0.55), "female_casualsuit01": (0.35, 0.6, 0.55)}, subdiv=0)
CROWD = [(1.0, 0.3, "young_caucasian_male", "short03", ["male_casualsuit01", "shoes02"], {"male_casualsuit01": (0.5, 0.55, 0.75)}),
         (0.0, 0.35, "young_caucasian_female", "long01", ["female_casualsuit02", "shoes04"], {"female_casualsuit02": (0.85, 0.4, 0.35)}),
         (1.0, 0.7, "old_caucasian_male", "short01", ["male_casualsuit02", "shoes03"], {"male_casualsuit02": (0.55, 0.5, 0.42)}),
         (0.0, 0.75, "old_caucasian_female", "bob02", ["female_elegantsuit01", "shoes06"], {"female_elegantsuit01": (0.3, 0.32, 0.45)}),
         (1.0, 0.45, "middleage_african_male", "short04", ["male_casualsuit05", "shoes01"], {"male_casualsuit05": (0.75, 0.7, 0.6)}),
         (0.0, 0.3, "young_asian_female", "ponytail01", ["female_sportsuit01", "shoes02"], {"female_sportsuit01": (0.4, 0.6, 0.45)}),
         (1.0, 0.5, "middleage_asian_male", "short02", ["male_worksuit01", "shoes03"], {"male_worksuit01": (0.6, 0.45, 0.3)}),
         (0.0, 0.5, "middleage_caucasian_female", "braid01", ["female_casualsuit01", "shoes04"], {"female_casualsuit01": (0.9, 0.85, 0.7)})]
for i, (g, a, sk, hr, cl, tn) in enumerate(CROWD):
    human("Crowd%d" % i, g, a, {"asian": 0.3 if "asian" in sk else 0.02, "caucasian": 0.9 if "cauc" in sk else 0.1, "african": 0.9 if "afric" in sk else 0.02},
          hr, cl, sk, 20 + 2 * i, tint=tn, subdiv=0)
bpy.ops.wm.save_as_mainfile(filepath=out)
