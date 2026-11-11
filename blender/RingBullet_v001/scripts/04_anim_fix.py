"""RingBullet v004: hand fixes after pipeline/anim_look.py (bright, clean 3D-animation look).
RB_LOOK=anim blender -b anim.blend --python 03b_fx_camera.py -- film_anim_base.blend
blender -b film_anim_base.blend --python ../../pipeline/anim_look.py -- film_anim_look.blend
blender -b film_anim_look.blend --python 04_anim_fix.py -- film_v004.blend [exposure]"""
import sys
import bpy

a = sys.argv[sys.argv.index("--") + 1:]; OUT = a[0]; EXPO = float(a[1]) if len(a) > 1 else 0.6
sc = bpy.context.scene; O = bpy.data.objects; M = bpy.data.materials
sc.view_settings.exposure = EXPO

def fcurves_of(idb):
    ad = idb.animation_data
    if not ad or not ad.action: return []
    out = []
    for layer in getattr(ad.action, "layers", []):
        for strip in layer.strips:
            for cb in getattr(strip, "channelbags", []): out += list(cb.fcurves)
    return out

# skin: smooth CG skin (no pores, no sweat), slightly warmer SSS
for m in M:
    if not m.node_tree: continue
    g = m.node_tree.nodes.get("SkinGroup")
    if g:
        g.inputs["Pore strength"].default_value = 0.04; g.inputs["SSS strength"].default_value = 0.3
        g.inputs["Roughness"].default_value = 0.42; g.inputs["Clearcoat Roughness"].default_value = 0.4

# set: lighter, cleaner wood and floor (still a night interior, but high-key and readable)
for nm, val in (("M_WallPanel", 1.9), ("M_Parquet", 1.25), ("M_DeskWood", 1.4)):
    m = M.get(nm)
    if m:
        for n in m.node_tree.nodes:
            if n.bl_idname == 'ShaderNodeHueSaturation' and not n.inputs['Value'].is_linked and n.inputs['Value'].default_value != 1.0:
                n.inputs['Value'].default_value = val
m = M.get("M_Ceiling")
if m:
    p = m.node_tree.nodes["Principled BSDF"]
    for n in m.node_tree.nodes:
        if n.bl_idname == 'ShaderNodeValToRGB':
            n.color_ramp.elements[0].color = (0.62, 0.55, 0.45, 1); n.color_ramp.elements[1].color = (0.55, 0.48, 0.4, 1)

# window backdrop -> the studio's sky-blue gradient (cyan top, near-white bottom), soft clouds of light
bd = O.get("NightBackdrop")
if bd:
    mb = bd.data.materials[0]; nt = mb.node_tree; N, L = nt.nodes, nt.links
    for n in list(N):
        if n.bl_idname != 'ShaderNodeOutputMaterial': N.remove(n)
    tc = N.new('ShaderNodeTexCoord'); sep = N.new('ShaderNodeSeparateXYZ'); L.new(tc.outputs['Generated'], sep.inputs[0])
    ramp = N.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].position = 0.15; ramp.color_ramp.elements[0].color = (0.80, 0.93, 1.0, 1)
    ramp.color_ramp.elements[1].position = 0.85; ramp.color_ramp.elements[1].color = (0.08, 0.55, 0.93, 1)
    L.new(sep.outputs['Z'], ramp.inputs['Fac'])
    em = N.new('ShaderNodeEmission'); em.inputs['Strength'].default_value = 1.4; L.new(ramp.outputs['Color'], em.inputs['Color'])
    L.new(em.outputs[0], N["Material Output"].inputs['Surface'])
fa = O.get("FacadeAcross")
if fa:
    for n in fa.data.materials[0].node_tree.nodes:
        if n.bl_idname == 'ShaderNodeHueSaturation': n.inputs['Value'].default_value = 0.9

# lighting: high-key, shadows lifted (static energies x, keyed energies scaled on their keys)
BOOST = {"L_KeyWarm": 2.4, "L_FillBounce": 3.0, "L_Sconce": 2.0, "L_Moon": 1.6, "L_RimCool": 1.5, "L_DeskLamp": 1.6,
         "L_LampPool": 1.5, "L_CabinetDisplay": 1.8, "L_StreetDoor": 1.5}
for nm, k in BOOST.items():
    o = O.get(nm)
    if not o: continue
    fcs = [fc for fc in fcurves_of(o.data) if fc.data_path == "energy"]
    if fcs:
        for fc in fcs:
            for kp in fc.keyframe_points: kp.co.y *= k; kp.handle_left.y *= k; kp.handle_right.y *= k
    else:
        o.data.energy *= k
w = sc.world
for n in w.node_tree.nodes:
    if n.type == 'BACKGROUND' and not n.inputs['Color'].is_linked is False:
        pass
# injuries: stylised small clean red (no realistic wound)
for nm, col in (("M_Nick", (0.75, 0.04, 0.05)), ("M_NeckMark", (0.85, 0.12, 0.12))):
    m = M.get(nm)
    if m:
        p = m.node_tree.nodes["Principled BSDF"]; p.inputs['Base Color'].default_value = (*col, 1); p.inputs['Roughness'].default_value = 0.4
# fragments + bullet: clean polished metal (no grime)
for nm in ("M_Fragment", "M_BulletCopper"):
    m = M.get(nm)
    if m:
        for n in m.node_tree.nodes:
            if n.bl_idname == 'ShaderNodeBump': n.inputs['Strength'].default_value = 0.0
sc["look"] = "animated_v004"
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print("SAVED", OUT)
