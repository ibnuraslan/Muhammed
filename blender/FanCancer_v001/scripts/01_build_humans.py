"""FanCancer cast (MPFB2 + MakeHuman CC0 assets).  blender -b --python 01_build_humans.py -- <out.blend>
Fan, Manager, Doctor, Nurse, 6 crowd variants, 2 player variants. Clothes tinted per role (no prints)."""
import sys
import bpy
from bl_ext.user_default.mpfb.services.humanservice import HumanService

out = sys.argv[sys.argv.index("--") + 1]
for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob, do_unlink=True)

def tint(rig, cloth, rgb, desat=False):
    for ch in rig.children:
        if ch.type == 'MESH' and cloth.split("/")[0] in ch.name:
            for m in ch.data.materials:
                m = m.copy() if m.users > 1 else m
                nt = m.node_tree
                for nd in list(nt.nodes):
                    if nd.type == 'TEX_IMAGE' and nd.image and "diffuse" in nd.image.name.lower():
                        for lk in list(nd.outputs['Color'].links):
                            hs = nt.nodes.new('ShaderNodeHueSaturation'); hs.inputs['Saturation'].default_value = 0.0
                            # brighten the greyscale so the tint carries the colour; kills any print colour
                            mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'
                            mx.inputs['Factor'].default_value = 1.0; mx.inputs['B'].default_value = (*rgb, 1)
                            nt.links.new(nd.outputs['Color'], hs.inputs['Color']); nt.links.new(hs.outputs['Color'], mx.inputs['A'])
                            nt.links.new(mx.outputs['Result'], lk.to_socket)

def human(name, gender, age, race, hair, clothes, skin, x, weight=0.5, height=None, tints=(), brows="eyebrow001", subdiv=1):
    info = HumanService._create_default_human_info_dict()
    info["name"] = name
    info["phenotype"] = {"gender": gender, "age": age, "muscle": 0.5, "weight": weight, "proportions": 0.6,
                         "height": height if height is not None else (0.55 if gender > 0.5 else 0.45),
                         "cupsize": 0.5, "firmness": 0.5, "race": race}
    info["rig"] = "default"
    info["eyes"] = "high-poly/high-poly.mhclo"; info["eyebrows"] = f"{brows}/{brows}.mhclo"
    info["eyelashes"] = "eyelashes01/eyelashes01.mhclo"; info["teeth"] = "teeth_base/teeth_base.mhclo"
    info["tongue"] = "tongue01/tongue01.mhclo"; info["hair"] = hair
    info["clothes"] = clothes
    info["skin_mhmat"] = skin; info["skin_material_type"] = "ENHANCED_SSS"; info["eyes_material_type"] = "PROCEDURAL_EYES"
    st = HumanService.get_default_deserialization_settings(); st["subdiv_levels"] = subdiv
    HumanService.deserialize_from_dict(info, st)
    rig = bpy.data.objects[name]
    rig.location.x = x
    for c, rgb in tints:
        tint(rig, c, rgb)
    return rig

W = {"asian": 0.05, "caucasian": 0.9, "african": 0.05}
B = {"asian": 0.05, "caucasian": 0.1, "african": 0.85}
As = {"asian": 0.85, "caucasian": 0.1, "african": 0.05}
FC2 = "female_casualsuit02/female_casualsuit02.mhclo"; FC1 = "female_casualsuit01/female_casualsuit01.mhclo"
MC = lambda i: f"male_casualsuit0{i}/male_casualsuit0{i}.mhclo"
SH = lambda i: f"shoes0{i}/shoes0{i}.mhclo"
H = lambda h: f"{h}/{h}.mhclo"

human("Fan", 0.0, 0.42, W, H("bob01"), [FC2, SH(2)], "young_caucasian_female/young_caucasian_female.mhmat", 0,
      tints=[(FC2, (0.30, 0.36, 0.28))])
human("Manager", 1.0, 0.72, W, H("short02"), [MC(4), SH(3)], "middleage_caucasian_male/middleage_caucasian_male.mhmat", 2,
      weight=0.6, tints=[(MC(4), (0.10, 0.13, 0.22))])
human("Doctor", 0.0, 0.68, B, H("ponytail01"), ["female_elegantsuit01/female_elegantsuit01.mhclo", SH(2)],
      "middleage_african_female/middleage_african_female.mhmat", 4, tints=[("female_elegantsuit01", (0.92, 0.93, 0.95))])
human("Nurse", 1.0, 0.45, As, H("short01"), [MC(1), SH(3)], "young_asian_male/young_asian_male.mhmat", 6,
      tints=[(MC(1), (0.25, 0.55, 0.55))])
crowd = [
    (1.0, 0.5, W, "short03", MC(2), "young_caucasian_male", (0.55, 0.12, 0.10)),
    (0.0, 0.5, B, "afro01", FC1, "young_african_female", (0.85, 0.80, 0.70)),
    (1.0, 0.8, As, "short04", MC(3), "middleage_asian_male", (0.15, 0.25, 0.45)),
    (0.0, 0.6, W, "long01", FC2, "middleage_caucasian_female", (0.45, 0.30, 0.20)),
    (1.0, 0.4, B, "short01", MC(5), "young_african_male", (0.20, 0.20, 0.22)),
    (0.0, 0.45, As, "ponytail01", FC1, "young_asian_female", (0.60, 0.15, 0.25)),
]
for i, (g, a, r, h, c, s, rgb) in enumerate(crowd):
    human(f"Crowd{i}", g, a, r, H(h), [c, SH(1 + i % 5)], f"{s}/{s}.mhmat", 8 + 2 * i, tints=[(c, rgb)], subdiv=0)
for i, (rgb, r, s) in enumerate((((0.55, 0.06, 0.06), W, "young_caucasian_male"), ((0.06, 0.12, 0.40), B, "young_african_male"))):
    human(f"Player{i}", 1.0, 0.45, r, H("short02"), [MC(3), SH(3)], f"{s}/{s}.mhmat", 22 + 2 * i, weight=0.65, height=0.7,
          tints=[(MC(3), rgb)], subdiv=0)

for ob in bpy.data.objects:
    if ob.type == 'ARMATURE':
        print("HUMAN", ob.name, len(ob.data.bones), [c.name for c in ob.children])
print("FACEBONES", [b.name for b in bpy.data.objects["Fan"].data.bones if any(k in b.name for k in ("jaw", "lid", "brow", "lip", "oris", "levator", "orbicularis", "eye"))])
bpy.ops.wm.save_as_mainfile(filepath=out, compress=True)
