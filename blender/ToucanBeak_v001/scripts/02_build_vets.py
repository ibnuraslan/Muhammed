"""Rescue-clinic staff (MPFB2 + MakeHuman CC0). Scrubs = MakeHuman suits re-materialled with the CC0 Poly Haven
fabric scan (no prints/logos), nitrile-glove material on the MPFB hand faces.
blender -b --python 02_build_vets.py -- <out.blend>"""
import sys, os
import bpy
from bl_ext.user_default.mpfb.services.humanservice import HumanService
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FAB = os.path.join(HERE, "assets", "ph", "fabric_pattern_07", "textures")
out = sys.argv[sys.argv.index("--") + 1]
for ob in list(bpy.data.objects): bpy.data.objects.remove(ob, do_unlink=True)

def fabric_mat(name, rgb):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; N = nt.nodes; L = nt.links
    b = N["Principled BSDF"]
    files = {f.split("_")[-2] if f.count("_") > 2 else f: f for f in os.listdir(FAB)}
    def tex(key, non_color=False):
        f = [x for x in os.listdir(FAB) if key in x][0]
        t = N.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(os.path.join(FAB, f))
        if non_color: t.image.colorspace_settings.name = "Non-Color"
        mp = N.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (6, 6, 6); tc = N.new("ShaderNodeTexCoord")
        L.new(tc.outputs["UV"], mp.inputs[0]); L.new(mp.outputs[0], t.inputs[0]); return t
    d = tex("col_1"); bw = N.new("ShaderNodeRGBToBW"); L.new(d.outputs[0], bw.inputs[0])
    mr = N.new("ShaderNodeMapRange"); L.new(bw.outputs[0], mr.inputs[0]); mr.inputs[3].default_value = 0.75; mr.inputs[4].default_value = 1.15
    mx = N.new("ShaderNodeMix"); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs[0].default_value = 1
    cr = N.new("ShaderNodeCombineColor"); L.new(mr.outputs[0], cr.inputs[0]); L.new(mr.outputs[0], cr.inputs[1]); L.new(mr.outputs[0], cr.inputs[2])
    L.new(cr.outputs[0], mx.inputs[6]); mx.inputs[7].default_value = rgb + (1,)
    L.new(mx.outputs[2], b.inputs["Base Color"])
    r = tex("rough", True); L.new(r.outputs[0], b.inputs["Roughness"])
    n = tex("nor_gl", True); nm = N.new("ShaderNodeNormalMap"); L.new(n.outputs[0], nm.inputs["Color"]); L.new(nm.outputs[0], b.inputs["Normal"])
    b.inputs["Sheen Weight"].default_value = 0.4
    return m

def make_glove():
    if "Nitrile_glove" in bpy.data.materials: return bpy.data.materials["Nitrile_glove"]
    glove = bpy.data.materials.new("Nitrile_glove"); glove.use_nodes = True
    gb = glove.node_tree.nodes["Principled BSDF"]; gb.inputs["Base Color"].default_value = (0.04, 0.08, 0.36, 1)
    gb.inputs["Roughness"].default_value = 0.38; gb.inputs["Subsurface Weight"].default_value = 0.0
    gn_ = glove.node_tree.nodes.new("ShaderNodeTexNoise"); gn_.inputs["Scale"].default_value = 2500
    gbp = glove.node_tree.nodes.new("ShaderNodeBump"); gbp.inputs["Strength"].default_value = 0.08
    glove.node_tree.links.new(gn_.outputs["Fac"], gbp.inputs["Height"]); glove.node_tree.links.new(gbp.outputs["Normal"], gb.inputs["Normal"])
    glove.use_fake_user = True
    return glove

def person(name, gender, age, race, hair, clothes, shoes, skin, x, scrub_rgb, gloves, height=0.5, weight=0.5):
    info = HumanService._create_default_human_info_dict()
    info["name"] = name
    info["phenotype"] = {"gender": gender, "age": age, "muscle": 0.5, "weight": weight, "proportions": 0.6,
                         "height": height, "cupsize": 0.5, "firmness": 0.5, "race": race}
    info["rig"] = "default"
    info["eyes"] = "high-poly/high-poly.mhclo"; info["eyebrows"] = "eyebrow001/eyebrow001.mhclo"
    info["eyelashes"] = "eyelashes01/eyelashes01.mhclo"; info["teeth"] = "teeth_base/teeth_base.mhclo"
    info["tongue"] = "tongue01/tongue01.mhclo"; info["hair"] = hair
    info["clothes"] = [clothes, shoes]
    info["skin_mhmat"] = skin; info["skin_material_type"] = "ENHANCED_SSS"; info["eyes_material_type"] = "PROCEDURAL_EYES"
    st = HumanService.get_default_deserialization_settings(); st["subdiv_levels"] = 1
    HumanService.deserialize_from_dict(info, st)
    rig = bpy.data.objects[name]; rig.location.x = x
    fm = fabric_mat(name + "_scrubs", scrub_rgb)
    for ch in rig.children:
        if ch.type != 'MESH': continue
        if ch.name.split(".")[-1] == clothes.split("/")[0] or clothes.split("/")[0] in ch.name:
            for i in range(len(ch.data.materials)): ch.data.materials[i] = fm
        if gloves and ch.name.endswith(".body") or (gloves and "body" in ch.name.lower() and ch.name.startswith(name)):
            vg = {g.index: g.name for g in ch.vertex_groups}
            hand = set()
            for v in ch.data.vertices:
                w = sum(g.weight for g in v.groups if any(k in vg.get(g.group, "") for k in ("wrist", "finger", "metacarpal", "thumb")))
                if w > 0.5: hand.add(v.index)
            glove = make_glove(); ch.data.materials.append(glove); gi = len(ch.data.materials) - 1; n = 0
            for p in ch.data.polygons:
                if all(v in hand for v in p.vertices): p.material_index = gi; n += 1
            print("GLOVE faces", name, ch.name, n)
    return rig

person("VetA", 0.0, 0.45, {"asian": 0.1, "caucasian": 0.2, "african": 0.0, }, "ponytail01/ponytail01.mhclo",
       "male_worksuit01/male_worksuit01.mhclo", "shoes03/shoes03.mhclo", "young_caucasian_female2/young_caucasian_female2.mhmat", 0, (0.04, 0.2, 0.2), True, 0.45)
person("VetB", 1.0, 0.5, {"asian": 0.0, "caucasian": 0.3, "african": 0.7}, "short02/short02.mhclo",
       "male_worksuit01/male_worksuit01.mhclo", "shoes03/shoes03.mhclo", "young_african_male/young_african_male.mhmat", 2, (0.05, 0.1, 0.26), True, 0.55)
person("Assist", 1.0, 0.4, {"asian": 0.7, "caucasian": 0.3, "african": 0.0}, "short04/short04.mhclo",
       "male_casualsuit02/male_casualsuit02.mhclo", "shoes01/shoes01.mhclo", "young_asian_male/young_asian_male.mhmat", 4, (0.18, 0.2, 0.24), False, 0.5)
for ob in bpy.data.objects:
    if ob.type == 'ARMATURE': print("RIG", ob.name, len(ob.data.bones), [c.name for c in ob.children])
print("FACEBONES", [b.name for b in bpy.data.objects["VetA"].data.bones if any(k in b.name for k in ("jaw", "brow", "lid", "lip", "oris", "eye", "levator"))][:60])
bpy.ops.wm.save_as_mainfile(filepath=out)
