"""The composer (exec'd by 01_build.py and the tests): MPFB old man, real MakeHuman CC0 suit (navy coat, white shirt,
red neckcloth), boots, wild grey hair; the skin under the clothes is kept and inset (solid body), cloth thickened."""
SUIT = "toigo_male_suit_3/toigo_male_suit_3.mhclo"
BOOTS = "toigo_ankle_boots_male/toigo_ankle_boots_male.mhclo"
HAIR = "cortu_short_messy_hair/cortu_short_messy_hair.mhclo"
for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob, do_unlink=True)
COMP, CB = human("Composer", 1.0, 0.86, {"asian": 0.0, "caucasian": 1.0, "african": 0.0}, HAIR,
                 "old_caucasian_male/old_caucasian_male.mhmat", "eyebrow001/eyebrow001.mhclo", height=0.45, muscle=0.45,
                 weight=0.58, shoes=BOOTS, clothes=[SUIT])
bake_keys(CB); eye_fix(COMP); eye_group_fix()
for m in CB.data.materials: tint(m, (1.0, 0.88, 0.80))
SUIT_O = part(COMP, "suit_3"); HAIR_O = part(COMP, "short_messy"); BROW_O = part(COMP, "eyebrow")
for g in (SUIT_O, part(COMP, "boots")):
    if g is not None:
        for m in list(g.modifiers):
            if m.type == 'MASK': g.modifiers.remove(m)
# MPFB adds delete-group masks on the body for clothes: remove them (the body must stay solid), inset instead
for m in list(CB.modifiers):
    if m.type == "MASK" and m.name.startswith("Delete."): print("removed body mask", m.name); CB.modifiers.remove(m)
cov = covered_by(CB, [SUIT_O], dist=0.035)
solid_inset(CB, cov, inset=0.008, rings=4)
thicken(SUIT_O, 0.004)
sat_boost(SUIT_O, sat=1.35, val=0.9)
# wild grey hair: silver-grey with darker roots; brows grey
def grey_hair(o, col=(0.62, 0.62, 0.64)):
    for m in o.data.materials:
        nt = m.node_tree
        for p in [n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED']:
            bc = p.inputs["Base Color"]
            if bc.is_linked and False:
                src = bc.links[0].from_socket
                bw = nt.nodes.new("ShaderNodeRGBToBW"); nt.links.new(src, bw.inputs[0])
                mr = nt.nodes.new("ShaderNodeMapRange"); nt.links.new(bw.outputs[0], mr.inputs["Value"])
                mr.inputs["From Min"].default_value = 0.0; mr.inputs["From Max"].default_value = 0.6
                mr.inputs["To Min"].default_value = 0.55; mr.inputs["To Max"].default_value = 1.15
                mul = nt.nodes.new("ShaderNodeMix"); mul.data_type = 'RGBA'; mul.blend_type = 'MULTIPLY'; mul.inputs["Factor"].default_value = 1.0
                nt.links.new(mr.outputs["Result"], mul.inputs["A"]); mul.inputs["B"].default_value = (*col, 1)
                nt.links.new(mul.outputs["Result"], bc)
            else:
                for l in list(bc.links): nt.links.remove(l)
                tx_ = [n for n in nt.nodes if n.type == 'TEX_IMAGE' and "diffuse" in n.name.lower()]
                nz = nt.nodes.new("ShaderNodeMapRange"); nz.inputs["From Min"].default_value = 0.0; nz.inputs["From Max"].default_value = 0.12
                if tx_:
                    bw_ = nt.nodes.new("ShaderNodeRGBToBW"); nt.links.new(tx_[0].outputs["Color"], bw_.inputs[0]); nt.links.new(bw_.outputs[0], nz.inputs["Value"])
                cr = nt.nodes.new("ShaderNodeValToRGB"); cr.color_ramp.elements[0].color = (col[0] * 0.55, col[1] * 0.55, col[2] * 0.58, 1)
                cr.color_ramp.elements[1].color = (min(1, col[0] * 1.25), min(1, col[1] * 1.25), min(1, col[2] * 1.25), 1)
                nt.links.new(nz.outputs["Result"], cr.inputs["Fac"]); nt.links.new(cr.outputs["Color"], bc)
            p.inputs["Roughness"].default_value = 0.6
            p.inputs["Specular IOR Level"].default_value = 0.3
            for l in list(p.inputs["Normal"].links): nt.links.remove(l)
grey_hair(HAIR_O, (0.21, 0.21, 0.23)); grey_hair(BROW_O, (0.40, 0.39, 0.39))
print("CHAR", [c.name for c in COMP.children], [m.name + ":" + m.type for m in CB.modifiers])
