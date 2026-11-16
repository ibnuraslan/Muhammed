"""B09 v002b look fixes on the laid-out file (director review of v002):
 - C1's fringe off her eyes (as in v002, scripts/fringe_fix.py)
 - the older woman (GranC car, GranB patient): dark hazel-brown irises instead of pale blue, grey strand hair instead of a white helmet
 - no skin-tight one-colour 'onesies': the suit meshes are split at the hip into a top and trousers/skirt in different colours,
   and pushed 8-10 mm off the body (Displace after the Armature) so they read as loose cloth
blender -b lay.blend --python looks_v002b.py -- out.blend"""
import bpy, sys
a = sys.argv[sys.argv.index("--") + 1:]; OUT = a[0]
O = bpy.data.objects

# ---- 1. C1 fringe (same edit as v002)
h = O["C1.bob01"]; BROW = 1.598; n = 0
for v in h.data.vertices:
    x, y, z = v.co
    if y > -0.085 or z >= BROW: continue
    w = max(0.0, min(1.0, (0.085 - abs(x)) / 0.02))
    if w <= 0: continue
    nz = BROW + (BROW - z) * 0.12; v.co.z = z + (nz - z) * w; v.co.y = y + 0.012 * w; n += 1
h.data.update(); print("FRINGE", n)

# ---- 2. eyes: hazel-brown irises for the older woman (car + hospital)
for cid in ("GranC", "GranB"):
    for m in O[cid + ".high-poly"].data.materials:
        for nd in m.node_tree.nodes:
            if nd.type == 'GROUP' and "IrisMajorColor" in nd.inputs:
                nd.inputs["IrisMajorColor"].default_value = (0.20, 0.11, 0.045, 1)
                nd.inputs["IrisMinorColor"].default_value = (0.075, 0.04, 0.018, 1)
                nd.inputs["IrisSection4Color"].default_value = (0.03, 0.02, 0.012, 1)
                print("EYES", cid, m.name)

# ---- 3. hair: mid grey with the strand texture showing through (was near-white, flat)
for cid in ("GranC", "GranB"):
    o = O[cid + ".short02"]
    for i, m in enumerate(o.data.materials):
        m = m.copy(); o.data.materials[i] = m
        for nd in m.node_tree.nodes:
            if nd.type == 'MIX' and nd.data_type == 'RGBA':
                nd.inputs[0].default_value = 0.35; nd.inputs[7].default_value = (0.36, 0.355, 0.35, 1)
            if nd.type == 'HUE_SAT':
                nd.inputs["Saturation"].default_value = 0.35; nd.inputs["Value"].default_value = 0.78
        print("HAIR", cid, m.name)

# ---- 4. two-tone loose outfits
def recolor(m, rgb, val):
    nt = m.node_tree; P = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    src = P.inputs["Base Color"].links[0].from_socket
    c = nt.nodes.new("ShaderNodeMix"); c.data_type = 'RGBA'; c.blend_type = 'COLOR'; c.inputs[0].default_value = 1.0
    c.inputs[7].default_value = (*rgb, 1); nt.links.new(src, c.inputs[6])
    mu = nt.nodes.new("ShaderNodeMix"); mu.data_type = 'RGBA'; mu.blend_type = 'MULTIPLY'; mu.inputs[0].default_value = 1.0
    mu.inputs[7].default_value = (val, val, val, 1); nt.links.new(c.outputs[2], mu.inputs[6])
    nt.links.new(mu.outputs[2], P.inputs["Base Color"])

def two_tone(obj_name, top_rgb, top_val, bot_rgb, bot_val, loose, hem=0.05):
    o = O[obj_name]; rig = o.parent
    if o.data.users > 1: o.data = o.data.copy()
    base = o.data.materials[0]
    mt = base.copy(); mt.name = obj_name + "_Top"; recolor(mt, top_rgb, top_val)
    mb = base.copy(); mb.name = obj_name + "_Bottom"; recolor(mb, bot_rgb, bot_val)
    o.data.materials[0] = mt; o.data.materials.append(mb); bi = len(o.data.materials) - 1
    inv = o.matrix_world.inverted() @ rig.matrix_world
    hip = max((inv @ rig.data.bones["upperleg01." + s].head_local).z for s in "LR") + hem
    nt = nb = 0
    for p in o.data.polygons:
        if p.material_index != 0: continue
        if p.center.z < hip: p.material_index = bi; nb += 1
        else: nt += 1
    d = o.modifiers.new("Loose", 'DISPLACE'); d.direction = 'NORMAL'; d.mid_level = 0.0; d.strength = loose
    ai = next(i for i, md in enumerate(o.modifiers) if md.type == 'ARMATURE')
    o.modifiers.move(len(o.modifiers) - 1, ai + 1)
    print("TWOTONE", obj_name, "hip z %.3f" % hip, "top", nt, "bottom", nb, [md.type for md in o.modifiers])

two_tone("GranC.female_elegantsuit01", (0.80, 0.74, 0.93), 1.0, (0.24, 0.26, 0.32), 0.50, 0.008)   # lavender blouse + slate skirt
two_tone("Doc2.male_casualsuit04", (0.45, 0.62, 0.92), 1.0, (0.10, 0.13, 0.26), 0.42, 0.010)      # blue scrub top + navy trousers
two_tone("Nurse2.female_casualsuit01", (0.32, 0.74, 0.62), 1.0, (0.20, 0.21, 0.23), 0.45, 0.010)  # teal scrub top + charcoal trousers
two_tone("C5.female_casualsuit01", (0.88, 0.64, 0.22), 1.0, (0.20, 0.30, 0.48), 0.60, 0.008)      # mustard top + denim trousers
# ---- 5. 4b: the glossy front counter top mirrored the queue into a big blurred blob at the bottom of the frame: matte it
ct = O["FrontCounterTop"]
for i, m in enumerate(ct.data.materials):
    m = m.copy(); ct.data.materials[i] = m
    for nd in m.node_tree.nodes:
        if nd.type == 'BSDF_PRINCIPLED':
            print("COUNTERTOP was rough %.2f metal %.2f" % (nd.inputs["Roughness"].default_value, nd.inputs["Metallic"].default_value))
            nd.inputs["Roughness"].default_value = 0.62; nd.inputs["Metallic"].default_value = min(nd.inputs["Metallic"].default_value, 0.3)
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print("LOOKS_OK", OUT)
