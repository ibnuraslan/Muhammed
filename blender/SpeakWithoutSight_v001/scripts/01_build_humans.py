"""Four MPFB2 humans (MakeHuman CC0 assets): Girl, Teacher, Mother, Father.
blender -b --python 01_build_humans.py -- <out.blend>"""
import sys
import bpy
from bl_ext.user_default.mpfb.services.humanservice import HumanService
out = sys.argv[sys.argv.index("--") + 1]
for ob in list(bpy.data.objects): bpy.data.objects.remove(ob, do_unlink=True)

def tint(rig, cloth, rgb):
    for ch in rig.children:
        if ch.type == 'MESH' and ch.name.split(".")[-1] == cloth:
            for m in ch.data.materials:
                nt = m.node_tree
                for nd in list(nt.nodes):
                    if nd.type == 'TEX_IMAGE' and nd.image and "diffuse" in nd.image.name.lower():
                        for lk in list(nd.outputs['Color'].links):
                            hs = nt.nodes.new('ShaderNodeHueSaturation'); hs.inputs['Saturation'].default_value = 0.0
                            mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'
                            mx.inputs['Factor'].default_value = 1.0; mx.inputs['B'].default_value = (*rgb, 1)
                            nt.links.new(nd.outputs['Color'], hs.inputs['Color']); nt.links.new(hs.outputs['Color'], mx.inputs['A'])
                            mx2 = nt.nodes.new('ShaderNodeMix'); mx2.data_type = 'RGBA'; mx2.inputs['Factor'].default_value = 0.65
                            mx2.inputs['B'].default_value = (*rgb, 1)
                            nt.links.new(mx.outputs['Result'], mx2.inputs['A']); nt.links.new(mx2.outputs['Result'], lk.to_socket)

def human(name, ph, hair, clothes, skin, x, tints):
    info = HumanService._create_default_human_info_dict()
    info["name"] = name
    base = {"gender": 0.0, "age": 0.5, "muscle": 0.5, "weight": 0.5, "proportions": 0.6, "height": 0.5,
            "cupsize": 0.5, "firmness": 0.5, "race": {"asian": 0.0, "caucasian": 1.0, "african": 0.0}}
    base.update(ph); info["phenotype"] = base
    info["rig"] = "default"
    info["eyes"] = "high-poly/high-poly.mhclo"; info["eyebrows"] = "eyebrow001/eyebrow001.mhclo"
    info["eyelashes"] = "eyelashes01/eyelashes01.mhclo"; info["teeth"] = "teeth_base/teeth_base.mhclo"
    info["tongue"] = "tongue01/tongue01.mhclo"; info["hair"] = hair
    info["clothes"] = clothes
    info["skin_mhmat"] = skin; info["skin_material_type"] = "ENHANCED_SSS"; info["eyes_material_type"] = "PROCEDURAL_EYES"
    st = HumanService.get_default_deserialization_settings(); st["subdiv_levels"] = 1
    HumanService.deserialize_from_dict(info, st)
    rig = bpy.data.objects[name]; rig.location.x = x
    for c, rgb in tints.items(): tint(rig, c, rgb)
    return rig

human("Girl", {"age": 0.215, "height": 0.5, "proportions": 0.5, "weight": 0.45}, "braid01/braid01.mhclo",
      ["female_elegantsuit01/female_elegantsuit01.mhclo", "shoes01/shoes01.mhclo"],
      "young_caucasian_female/young_caucasian_female.mhmat", 0.0, {"female_elegantsuit01": (0.05, 0.09, 0.2)})
human("Teacher", {"age": 0.42, "height": 0.7, "weight": 0.45}, "ponytail01/ponytail01.mhclo",
      ["female_elegantsuit01/female_elegantsuit01.mhclo", "shoes01/shoes01.mhclo"],
      "young_caucasian_female2/young_caucasian_female2.mhmat", 1.0, {"female_elegantsuit01": (0.62, 0.58, 0.5)})
human("Mother", {"age": 0.6, "height": 0.65, "weight": 0.55}, "long01/long01.mhclo",
      ["female_elegantsuit01/female_elegantsuit01.mhclo", "shoes01/shoes01.mhclo"],
      "middleage_caucasian_female/middleage_caucasian_female.mhmat", 2.0, {"female_elegantsuit01": (0.14, 0.04, 0.045)})
human("Father", {"gender": 1.0, "age": 0.68, "height": 0.5, "weight": 0.6}, "short02/short02.mhclo",
      ["male_elegantsuit01/male_elegantsuit01.mhclo", "shoes01/shoes01.mhclo"],
      "middleage_caucasian_male/middleage_caucasian_male.mhmat", 3.0, {"male_elegantsuit01": (0.05, 0.045, 0.04)})
import math, bmesh
from mathutils import Vector
def long_skirt(rig, rgb, flare=0.14):
    body = next(c for c in rig.children if c.name.endswith(".body"))
    B = rig.data.bones
    zw = B["spine04"].head_local.z + 0.02
    cx, cy = B["root"].head_local.x, B["root"].head_local.y + 0.0
    suit = next(c for c in rig.children if c.name.endswith("elegantsuit01"))
    dg = bpy.context.evaluated_depsgraph_get(); em = body.evaluated_get(dg).to_mesh()
    V = [v.co.copy() for v in em.vertices]
    NS, NR = 48, 18
    bm = bmesh.new(); rings = []
    for r in range(NR):
        t = r / (NR - 1); z = zw - t * (zw - 0.03)
        band = [v for v in V if abs(v.z - z) < 0.02 and abs(v.x - cx) < 0.21 and abs(v.y - cy) < 0.2]
        rx = 1.15 * max([abs(v.x - cx) for v in band] or [0.15]); ry = 1.15 * max([abs(v.y - cy) for v in band] or [0.12])
        if r > 0:
            rx = max(rx, rings_r[-1][0]); ry = max(ry, rings_r[-1][1])
        rings_r = (rings_r if r else []) + [(rx, ry)]
        ex = 0.025 + flare * t ** 1.4
        ring = [bm.verts.new((cx + (rx + ex) * math.sin(2 * math.pi * k / NS), cy + (ry + ex * 0.8) * -math.cos(2 * math.pi * k / NS), z)) for k in range(NS)]
        rings.append(ring)
    for a, b in zip(rings, rings[1:]):
        for k in range(NS):
            bm.faces.new((a[k], a[(k + 1) % NS], b[(k + 1) % NS], b[k]))
    me = bpy.data.meshes.new(rig.name + "_LongSkirt"); bm.to_mesh(me)
    for p in me.polygons: p.use_smooth = True
    ob = bpy.data.objects.new(rig.name + ".long_skirt", me); bpy.context.scene.collection.objects.link(ob)
    ob.parent = rig
    # hem bone: keeps the hem on the floor (animated to follow the root in xy/yaw, scaled when she kneels or sits)
    bpy.context.view_layer.objects.active = rig
    for o_ in bpy.context.selected_objects: o_.select_set(False)
    rig.select_set(True); bpy.ops.object.mode_set(mode='EDIT')
    eb = rig.data.edit_bones; hb = eb.new("SkirtHem"); hb.head = (cx, cy, 0.0); hb.tail = (cx, cy, 0.15); hb.use_deform = True; hb.parent = None
    bpy.ops.object.mode_set(mode='OBJECT')
    G = {n: ob.vertex_groups.new(name=n) for n in ("root", "upperleg02.L", "upperleg02.R", "SkirtHem")}
    for v in me.vertices:
        t = (zw - v.co.z) / (zw - 0.03); side = max(-1, min(1, (v.co.x - cx) / 0.09)); wl = 0.5 + 0.5 * side
        wr = max(0.0, 1 - t / 0.45); wh = max(0.0, (t - 0.45) / 0.55) ** 0.8; wleg = max(0.0, 1 - wr - wh)
        G["root"].add([v.index], wr, 'REPLACE'); G["SkirtHem"].add([v.index], wh, 'REPLACE')
        G["upperleg02.L"].add([v.index], wleg * wl, 'REPLACE'); G["upperleg02.R"].add([v.index], wleg * (1 - wl), 'REPLACE')
    am = ob.modifiers.new("Armature", 'ARMATURE'); am.object = rig
    vg = suit.vertex_groups.new(name="upper_only")
    vg.add([v.index for v in suit.data.vertices if v.co.z > zw - 0.06], 1.0, "REPLACE")
    mk = suit.modifiers.new("HideSkirt", 'MASK'); mk.vertex_group = "upper_only"
    while suit.modifiers[0].name != "HideSkirt": bpy.ops.object.modifier_move_up({"object": suit}, modifier="HideSkirt") if False else suit.modifiers.move(len(suit.modifiers)-1, 0)
    ob.modifiers.new("Solid", 'SOLIDIFY').thickness = 0.006
    ob.modifiers.new("Sub", 'SUBSURF').levels = 1
    m = bpy.data.materials.new(rig.name + "_SkirtFabric"); m.use_nodes = True
    p = m.node_tree.nodes["Principled BSDF"]; p.inputs["Base Color"].default_value = (*rgb, 1); p.inputs["Roughness"].default_value = 0.85
    nz = m.node_tree.nodes.new("ShaderNodeTexWave"); nz.inputs["Scale"].default_value = 30; nz.wave_type = 'BANDS'; nz.bands_direction = 'X'
    bp = m.node_tree.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.15
    m.node_tree.links.new(nz.outputs["Fac"], bp.inputs["Height"]); m.node_tree.links.new(bp.outputs["Normal"], p.inputs["Normal"])
    me.materials.append(m)
    return ob
# long skirts dropped: they balloon when kneeling (kept the function for later)

for ob in bpy.data.objects:
    if ob.type == 'ARMATURE':
        print("HUMAN", ob.name, [(c.name, tuple(round(d, 2) for d in c.dimensions)) for c in ob.children])
bpy.ops.wm.save_as_mainfile(filepath=out)
