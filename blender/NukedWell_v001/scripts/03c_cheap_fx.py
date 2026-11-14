"""Replace every volume shader with a cheap surface shader (farm cost: ~30 s/frame of ray marching -> one transparent hit).
Runs after 03b_look.py / eye_fix.py:  blender -b anim.blend --python 03c_cheap_fx.py -- <out.blend>
Same objects, same animation: the animated nodes (FireNoise, FlowMap, FireAmt, SteamAmt, SteamNoise, DustAmt) are kept and
re-wired, so 03_animate.py keys still drive the look. The volume "depth" is faked with the view-facing factor of the
cone/sphere surface (thick in the middle of the silhouette, thin at the rim)."""
import sys
import bpy

OUT = sys.argv[sys.argv.index("--") + 1]
M = bpy.data.materials


def math_(nt, op, a, b=None, clamp=False):
    n = nt.nodes.new('ShaderNodeMath'); n.operation = op; n.use_clamp = clamp
    for i, v in enumerate((a, b)):
        if v is None: continue
        if isinstance(v, (int, float)): n.inputs[i].default_value = v
        else: nt.links.new(v, n.inputs[i])
    return n.outputs[0]


def common(nt):
    """thickness (1 centre of silhouette .. 0 rim) and Generated Z"""
    lw = nt.nodes.new('ShaderNodeLayerWeight'); lw.inputs['Blend'].default_value = 0.5
    thick = math_(nt, 'SUBTRACT', 1.0, lw.outputs['Facing'], clamp=True)
    tc = next((n for n in nt.nodes if n.type == 'TEX_COORD'), None) or nt.nodes.new('ShaderNodeTexCoord')
    sep = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(tc.outputs['Generated'], sep.inputs['Vector'])
    return thick, sep.outputs['Z']


def finish(nt, alpha, shader):
    out = nt.nodes["Material Output"]
    for lk in list(out.inputs['Volume'].links): nt.links.remove(lk)
    for n in [n for n in nt.nodes if n.type in ('PRINCIPLED_VOLUME', 'VOLUME_SCATTER', 'VOLUME_ABSORPTION')]: nt.nodes.remove(n)
    tr = nt.nodes.new('ShaderNodeBsdfTransparent'); mx = nt.nodes.new('ShaderNodeMixShader')
    nt.links.new(alpha, mx.inputs['Fac']); nt.links.new(tr.outputs[0], mx.inputs[1]); nt.links.new(shader, mx.inputs[2])
    nt.links.new(mx.outputs[0], out.inputs['Surface'])


def fire(name, gain=1.0):
    nt = M[name].node_tree; nz = nt.nodes["FireNoise"]; amt = nt.nodes["FireAmt"].outputs[0]
    nz.inputs['Detail'].default_value = 5.0
    thick, z = common(nt)
    # same field as the volume: 0.5*core - 0.68 + noise - 0.4*z, with core ~ thickness
    f1 = math_(nt, 'MULTIPLY_ADD', thick, 0.55); f1.node.inputs[2].default_value = -0.66
    field = math_(nt, 'ADD', math_(nt, 'ADD', f1, nz.outputs['Fac']), math_(nt, 'MULTIPLY', z, -0.4))
    base = math_(nt, 'MULTIPLY', math_(nt, 'MULTIPLY', math_(nt, 'SUBTRACT', 0.22, z), 6.0, clamp=True), thick)
    field = math_(nt, 'ADD', field, math_(nt, 'MULTIPLY', base, 0.7))          # solid, hot base: the column stays rooted on the wellhead
    lift = math_(nt, 'MULTIPLY', math_(nt, 'SUBTRACT', z, 0.003), 120.0, clamp=True)   # only the bottom ~1 m fades: rooted on the wellhead
    alpha = math_(nt, 'MULTIPLY', math_(nt, 'MULTIPLY', math_(nt, 'MULTIPLY', field, 6.0, clamp=True), amt), lift)
    alpha = math_(nt, 'MINIMUM', math_(nt, 'MULTIPLY', alpha, math_(nt, 'MULTIPLY', math_(nt, 'SUBTRACT', 1.0, z), 5.0, clamp=True)), 1.0)   # fade out before the top cap
    hot = math_(nt, 'MULTIPLY', field, 1.6, clamp=True)      # keep noise variation inside the core (no flat cone)
    zz = math_(nt, 'MULTIPLY_ADD', z, -0.6); zz.node.inputs[2].default_value = 1.0
    ramp = next(n for n in nt.nodes if n.type == 'VALTORGB')
    els = ramp.color_ramp.elements
    for e, (pos, col) in zip(sorted(els, key=lambda e: e.position), ((0.0, (0.6, 0.04, 0.0, 1)), (0.35, (1.0, 0.16, 0.0, 1)), (0.7, (1.0, 0.38, 0.02, 1)), (1.0, (1.0, 0.62, 0.12, 1)))):
        e.position = pos; e.color = col                     # saturated orange-yellow (AgX turns a pale top colour into cream)
    for lk in list(ramp.inputs['Fac'].links): nt.links.remove(lk)
    nt.links.new(math_(nt, 'MULTIPLY', hot, zz), ramp.inputs['Fac'])
    em = nt.nodes.new('ShaderNodeEmission'); nt.links.new(ramp.outputs['Color'], em.inputs['Color'])
    st = math_(nt, 'MULTIPLY_ADD', math_(nt, 'MULTIPLY', hot, hot), 1.6 * gain); st.node.inputs[2].default_value = 1.1 * gain   # orange-yellow under AgX, not clipped white
    nt.links.new(st, em.inputs['Strength'])
    finish(nt, alpha, em.outputs[0])


def smoke(name):
    nt = M[name].node_tree; nz = nt.nodes["FireNoise"]; amt = nt.nodes["FireAmt"].outputs[0]
    nz.inputs['Detail'].default_value = 5.0
    thick, z = common(nt)
    f1 = math_(nt, 'MULTIPLY_ADD', thick, 0.45); f1.node.inputs[2].default_value = -0.62
    field = math_(nt, 'ADD', f1, nz.outputs['Fac'])
    zin = math_(nt, 'MULTIPLY', z, 6.0, clamp=True)
    alpha = math_(nt, 'MULTIPLY', math_(nt, 'MULTIPLY', math_(nt, 'MULTIPLY', field, 2.6, clamp=True), amt), zin)
    alpha = math_(nt, 'MULTIPLY', math_(nt, 'MULTIPLY', alpha, 0.92), math_(nt, 'MULTIPLY', math_(nt, 'SUBTRACT', 1.0, z), 3.0, clamp=True))   # no hard top cap
    df = nt.nodes.new('ShaderNodeBsdfDiffuse'); df.inputs['Color'].default_value = (0.30, 0.29, 0.29, 1)
    finish(nt, alpha, df.outputs[0])


def puff(name, amt_name, color, power=2.0, cap=0.6, thresh=0.45):
    nt = M[name].node_tree; nz = nt.nodes["SteamNoise"]; amt = nt.nodes[amt_name].outputs[0]
    thick, z = common(nt)
    nzr = math_(nt, 'MULTIPLY', math_(nt, 'SUBTRACT', nz.outputs['Fac'], thresh), 2.5, clamp=True)
    alpha = math_(nt, 'MINIMUM', math_(nt, 'MULTIPLY', math_(nt, 'MULTIPLY', nzr, math_(nt, 'POWER', thick, power)), amt), cap)
    df = nt.nodes.new('ShaderNodeBsdfDiffuse'); df.inputs['Color'].default_value = color
    em = nt.nodes.new('ShaderNodeEmission'); em.inputs['Color'].default_value = color; em.inputs['Strength'].default_value = 0.25
    ad = nt.nodes.new('ShaderNodeAddShader'); nt.links.new(df.outputs[0], ad.inputs[0]); nt.links.new(em.outputs[0], ad.inputs[1])
    finish(nt, alpha, ad.outputs[0])


fire("M_Fire"); fire("M_FissureFire", 1.2); smoke("M_Smoke")
puff("M_Steam", "SteamAmt", (0.95, 0.95, 0.95, 1)); puff("M_Dust", "DustAmt", (0.78, 0.62, 0.44, 1), power=0.8, cap=0.85, thresh=0.3)   # the dust ring must read in wide shots
for o in bpy.data.objects:
    if o.type == 'MESH' and o.data.materials and o.data.materials[0] and o.data.materials[0].name in ("M_Fire", "M_FissureFire", "M_Steam"):
        o.visible_shadow = False            # emissive / thin: no dark cut-out shadows; the fire lights do the lighting
    if o.type == 'MESH' and o.data.materials and o.data.materials[0] and o.data.materials[0].name in ("M_Fire", "M_FissureFire", "M_Smoke", "M_Steam", "M_Dust"):
        for p_ in o.data.polygons: p_.use_smooth = True     # smooth facing factor (no faceted 'paper' look)
left = [m.name for m in M if m.node_tree and any(n.type in ('PRINCIPLED_VOLUME', 'VOLUME_SCATTER', 'VOLUME_ABSORPTION') for n in m.node_tree.nodes) and m.users]
sc = bpy.context.scene
sc.cycles.transparent_max_bounces = max(sc.cycles.transparent_max_bounces, 16)
print("CHEAPFX done; volume materials still in use:", left)
bpy.ops.wm.save_as_mainfile(filepath=OUT)
