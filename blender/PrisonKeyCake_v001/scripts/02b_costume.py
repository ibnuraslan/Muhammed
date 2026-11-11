# 1919 costume pass (exec'd at the end of 02_build_scene.py): denim -> wool trousers, prisoner shirt -> drab linen.
def wool_pass(mat, mode, shirt_tint=None, wool=(0.30, 0.26, 0.21)):
    nt = mat.node_tree; N, L = nt.nodes, nt.links
    bs = next((n for n in N if n.type == 'BSDF_PRINCIPLED'), None)
    if not bs or not bs.inputs['Base Color'].links: return False
    src = bs.inputs['Base Color'].links[0].from_socket
    bw = N.new('ShaderNodeRGBToBW'); L.new(src, bw.inputs['Color'])
    gam = N.new('ShaderNodeMath'); gam.operation = 'MULTIPLY_ADD'; gam.inputs[1].default_value = 0.55; gam.inputs[2].default_value = 0.45
    L.new(bw.outputs['Val'], gam.inputs[0])
    nz = N.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 900.0; nz.inputs['Detail'].default_value = 2
    tc = N.new('ShaderNodeTexCoord'); L.new(tc.outputs['UV'], nz.inputs['Vector'])
    nzm = N.new('ShaderNodeMath'); nzm.operation = 'MULTIPLY_ADD'; nzm.inputs[1].default_value = 0.35; nzm.inputs[2].default_value = 0.82
    L.new(nz.outputs['Fac'], nzm.inputs[0])
    w1 = N.new('ShaderNodeMath'); w1.operation = 'MULTIPLY'; L.new(gam.outputs[0], w1.inputs[0]); L.new(nzm.outputs[0], w1.inputs[1])
    wc = N.new('ShaderNodeMix'); wc.data_type = 'RGBA'; wc.blend_type = 'MULTIPLY'; wc.inputs['Factor'].default_value = 1.0
    wc.inputs['B'].default_value = (*wool, 1)
    cv = N.new('ShaderNodeCombineColor'); [L.new(w1.outputs[0], cv.inputs[i]) for i in range(3)]
    L.new(cv.outputs['Color'], wc.inputs['A'])
    if mode == "uvband":
        sep = N.new('ShaderNodeSeparateXYZ'); L.new(tc.outputs['UV'], sep.inputs['Vector'])
        a = N.new('ShaderNodeMath'); a.operation = 'GREATER_THAN'; a.inputs[1].default_value = 0.355; L.new(sep.outputs['X'], a.inputs[0])
        b = N.new('ShaderNodeMath'); b.operation = 'LESS_THAN'; b.inputs[1].default_value = 0.715; L.new(sep.outputs['X'], b.inputs[0])
        mask = N.new('ShaderNodeMath'); mask.operation = 'MULTIPLY'; L.new(a.outputs[0], mask.inputs[0]); L.new(b.outputs[0], mask.inputs[1])
    else:   # blue denim by hue/saturation
        hsv = N.new('ShaderNodeSeparateColor'); hsv.mode = 'HSV'; L.new(src, hsv.inputs['Color'])
        h0 = N.new('ShaderNodeMapRange'); h0.inputs['From Min'].default_value = 0.5; h0.inputs['From Max'].default_value = 0.56; L.new(hsv.outputs[0], h0.inputs['Value'])
        h1 = N.new('ShaderNodeMapRange'); h1.inputs['From Min'].default_value = 0.72; h1.inputs['From Max'].default_value = 0.66; L.new(hsv.outputs[0], h1.inputs['Value'])
        s0 = N.new('ShaderNodeMapRange'); s0.inputs['From Min'].default_value = 0.12; s0.inputs['From Max'].default_value = 0.25; L.new(hsv.outputs[1], s0.inputs['Value'])
        m1 = N.new('ShaderNodeMath'); m1.operation = 'MINIMUM'; L.new(h0.outputs[0], m1.inputs[0]); L.new(h1.outputs[0], m1.inputs[1])
        mask = N.new('ShaderNodeMath'); mask.operation = 'MINIMUM'; L.new(m1.outputs[0], mask.inputs[0]); L.new(s0.outputs[0], mask.inputs[1])
    other = src
    if shirt_tint:
        sh = N.new('ShaderNodeMix'); sh.data_type = 'RGBA'; sh.blend_type = 'MULTIPLY'; sh.inputs['Factor'].default_value = 1.0
        sh.inputs['B'].default_value = (*shirt_tint, 1)
        cv2 = N.new('ShaderNodeCombineColor'); g2 = N.new('ShaderNodeMath'); g2.operation = 'MULTIPLY_ADD'; g2.inputs[1].default_value = 0.6; g2.inputs[2].default_value = 0.55
        L.new(bw.outputs['Val'], g2.inputs[0]); [L.new(g2.outputs[0], cv2.inputs[i]) for i in range(3)]
        L.new(cv2.outputs['Color'], sh.inputs['A']); other = sh.outputs['Result']
    fin = N.new('ShaderNodeMix'); fin.data_type = 'RGBA'; L.new(mask.outputs[0], fin.inputs['Factor'])
    L.new(other, fin.inputs['A']); L.new(wc.outputs['Result'], fin.inputs['B'])
    L.new(fin.outputs['Result'], bs.inputs['Base Color'])
    bs.inputs['Roughness'].default_value = 0.85
    return True
done = []
for ob in bpy.data.objects:
    if ob.type != 'MESH' or not ob.data.materials: continue
    suf = ob.name.split(".")[-1]
    for m in ob.data.materials:
        if not m or m.name in done: continue
        if suf == "male_casualsuit01":
            if wool_pass(m, "uvband", shirt_tint=(0.82, 0.76, 0.64) if ob.name.startswith(("Prisoner", "YardP1")) else None, wool=(0.27, 0.24, 0.2)): done.append(m.name)
        elif suf in ("male_casualsuit03", "male_casualsuit05"):
            if wool_pass(m, "hue", wool=(0.33, 0.29, 0.24)): done.append(m.name)
print("COSTUME wool", done)
