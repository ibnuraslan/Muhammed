# DogBuriedAlive v002b: separate garments (director: the one-colour suits read as onesies).
# exec'd by 02_build.py after the library objects. No MPFB garment library is installed, so each one-piece suit mesh is
# split at the waist into a shirt/blouse (upper) and jeans/shorts (lower) with their own materials, a belt band at the
# waist, and the shirt is lifted 4 mm off the trousers (a Displace on the shirt faces) so it reads as a layer over them.

def _pmat(name, kind, c1, c2=None, scale=60.0, rough=0.7):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; P = nt.nodes["Principled BSDF"]
    P.inputs["Roughness"].default_value = rough
    if "Specular IOR Level" in P.inputs: P.inputs["Specular IOR Level"].default_value = 0.2
    tc = nt.nodes.new("ShaderNodeTexCoord")
    if kind == "check":                      # gingham / check shirt
        ck = nt.nodes.new("ShaderNodeTexChecker"); ck.inputs["Scale"].default_value = scale
        ck.inputs["Color1"].default_value = (*c1, 1); ck.inputs["Color2"].default_value = (*c2, 1)
        nt.links.new(tc.outputs["Object"], ck.inputs["Vector"]); nt.links.new(ck.outputs["Color"], P.inputs["Base Color"])
    elif kind == "denim":                    # soft denim: fine noise between two blues
        nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 180.0; nz.inputs["Detail"].default_value = 4.0
        rp = nt.nodes.new("ShaderNodeValToRGB"); rp.color_ramp.elements[0].color = (*c1, 1); rp.color_ramp.elements[1].color = (*c2, 1)
        nt.links.new(tc.outputs["Object"], nz.inputs["Vector"]); nt.links.new(nz.outputs["Fac"], rp.inputs["Fac"])
        nt.links.new(rp.outputs["Color"], P.inputs["Base Color"])
    else:
        P.inputs["Base Color"].default_value = (*c1, 1)
    return m

WARDROBE = {
    # rig: (suit key, shirt material, trousers material)
    "Dad": ("casualsuit", _pmat("DadShirtCheck", "check", (0.62, 0.74, 0.88), (0.22, 0.36, 0.62), 55.0),
            _pmat("DadJeans", "denim", (0.07, 0.13, 0.28), (0.13, 0.22, 0.42))),
    "Son": ("casualsuit", _pmat("SonTopGreen", "solid", (0.10, 0.42, 0.18)),
            _pmat("SonJeans", "denim", (0.05, 0.06, 0.12), (0.10, 0.12, 0.22))),
    "Mom": ("casualsuit", _pmat("MomBlouse", "check", (0.95, 0.93, 0.88), (0.86, 0.80, 0.72), 90.0, 0.6),
            _pmat("MomDenimShorts", "denim", (0.22, 0.36, 0.62), (0.36, 0.52, 0.78))),
}
BELT_M = mat("BeltBrown", (0.20, 0.10, 0.05), 0.5)

for rn, (key, m_top, m_bot) in WARDROBE.items():
    rig = bpy.data.objects[rn]
    suit = next(c for c in rig.children if c.type == 'MESH' and key in c.name)
    me = suit.data
    waist = rig.data.bones["upperleg01.L"].head_local.z * 1.10
    me.materials.clear()
    me.materials.append(m_top); me.materials.append(m_bot); me.materials.append(BELT_M)
    vg = suit.vertex_groups.new(name="ShirtLayer")
    top_v = set()
    for p in me.polygons:
        z = p.center.z
        if z >= waist:
            p.material_index = 0; top_v.update(p.vertices)
        elif z >= waist - 0.035:
            p.material_index = 2
        else:
            p.material_index = 1
    vg.add(list(top_v), 1.0, 'REPLACE')
    d = suit.modifiers.new("ShirtLayer", 'DISPLACE'); d.vertex_group = "ShirtLayer"; d.mid_level = 0.0; d.strength = 0.004
    print("BUILD wardrobe", rn, "waist", round(waist, 3), "shirt faces", sum(1 for p in me.polygons if p.material_index == 0))
