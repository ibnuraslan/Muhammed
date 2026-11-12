"""Post-pass after pipeline/anim_look.py for LegoInNose (client look change, Nov 11 22:45 UTC: bright clean 3D animation).
blender -b looked.blend --python anim_fix.py -- out.blend
anim_look.py sets static values, but this film keys light energy, world strength, exposure and f-stop, so those keys are
re-applied here. Also: sky-blue studio gradient, clean colour-coded anatomy (cream bone, glossy pink mucosa), cleaner tunnel."""
import sys, bpy
out = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene
def fcurves(idb):
    ad = getattr(idb, "animation_data", None)
    if not ad or not ad.action: return []
    o = []
    for l in getattr(ad.action, "layers", []):
        for s in l.strips:
            for cb in getattr(s, "channelbags", []): o += list(cb.fcurves)
    return o
def scale_keys(idb, path_part, k=None, lo=None, fn=None):
    for fc in fcurves(idb):
        if path_part in fc.data_path:
            for kp in fc.keyframe_points:
                v = kp.co.y
                if fn: v = fn(v)
                if k is not None: v *= k
                if lo is not None: v = max(lo, v)
                d = v - kp.co.y; kp.co.y = v; kp.handle_left.y += d; kp.handle_right.y += d
            fc.update()
# 1. keyed lights x1.25 (high key), keyed world strength x1.4, moonlit bedroom stays readable
for L in bpy.data.lights:
    scale_keys(L, "energy", k=1.25 if L.type != "POINT" else 1.0)
bm = bpy.data.lights.get("BR_Moon")
if bm: scale_keys(bm, "energy", fn=lambda v: v * 1.6)
lamp = bpy.data.lights.get("BR_NightLamp")
if lamp: lamp.energy = 25
if sc.world and sc.world.node_tree: scale_keys(sc.world.node_tree, "nodes[\"BG", k=1.4)
# readable blue night in the bedroom: a soft blue fill over the bed during the night beat + warm lamp
bf = bpy.data.lights.new("BR_BlueNightFill", "AREA"); bf.size = 2.5; bf.color = (0.5, 0.62, 1.0)
bo = bpy.data.objects.new("BR_BlueNightFill", bf); bpy.data.collections["Set_Bedroom"].objects.link(bo); bo.location = (4.4, 0.9, 2.55)
for f, e in ((1, 0), (1716, 0), (1736, 260), (1866, 260), (1880, 0)):
    bf.energy = e; bf.keyframe_insert("energy", frame=f)
if lamp: lamp.energy = 40
# 2. exposure: brighter overall, but bright beats must not blow out (studio and bathroom are already bright)
scale_keys(sc, "view_settings.exposure", fn=lambda v: v + 0.25 if v < 1.0 else v + 0.1)
# 3. f-stop >= 5.6 everywhere (keyed); true macros keep 5.6
for cam in bpy.data.cameras: scale_keys(cam, "aperture_fstop", lo=5.6)
# 4. studio: bright sky-blue gradient (cyan top -> near-white bottom), light floor
m = bpy.data.materials["M_StudioGradient"]; nt = m.node_tree
ramp = [n for n in nt.nodes if n.type == "VALTORGB"][0]
ramp.color_ramp.elements[0].color = (0.62, 0.88, 1.0, 1); ramp.color_ramp.elements[0].position = 0.3
ramp.color_ramp.elements[1].color = (0.0, 0.42, 0.95, 1); ramp.color_ramp.elements[1].position = 0.62
nt.nodes["Emission"].inputs[1].default_value = 1.15
fl = bpy.data.materials.get("M_StudioFloor")
if fl: fl.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.75, 0.9, 1.0, 1)
for i in range(3):
    o = bpy.data.objects.get("Studio_Key%d" % i)
    if o: o.data.energy = (380, 200, 260)[i]
# 5. anatomy: clean, glossy, colour-coded (cream bone, pink mucosa, red-pink muscle) - no wet/medical-photo look
def recolour(name, ramp_cols=None, base=None, rough=None, coat=None, back=None):
    m = bpy.data.materials.get(name)
    if not m: return
    nt = m.node_tree
    for n in nt.nodes:
        if n.type == "VALTORGB" and ramp_cols:
            n.color_ramp.elements[0].color = (*ramp_cols[0], 1); n.color_ramp.elements[1].color = (*ramp_cols[1], 1)
        if n.type == "BSDF_PRINCIPLED":
            front = any(l.to_node.type == "MIX_SHADER" and l.to_socket == l.to_node.inputs[1] for l in n.outputs[0].links) or not any(l.to_node.type == "MIX_SHADER" for l in n.outputs[0].links)
            isback = any(l.to_node.type == "MIX_SHADER" and l.to_socket == l.to_node.inputs[2] for l in n.outputs[0].links)
            if isback and back:
                n.inputs["Base Color"].default_value = (*back, 1); n.inputs["Roughness"].default_value = 0.4
            elif front:
                if base and not n.inputs["Base Color"].is_linked: n.inputs["Base Color"].default_value = (*base, 1)
                if rough is not None: n.inputs["Roughness"].default_value = rough
                if coat is not None: n.inputs["Coat Weight"].default_value = coat
                n.inputs["Subsurface Weight"].default_value = min(0.15, n.inputs["Subsurface Weight"].default_value)
        if n.type == "BUMP": n.inputs["Strength"].default_value = min(n.inputs["Strength"].default_value, 0.12)
CREAM = ((0.85, 0.76, 0.58), (0.95, 0.89, 0.74)); PINK = ((0.9, 0.36, 0.45), (1.0, 0.55, 0.6))
recolour("M_XS_SkullCut", CREAM, rough=0.4, coat=0.3, back=(0.96, 0.9, 0.76))
recolour("M_XS_Bone", CREAM, rough=0.4, coat=0.3)
recolour("M_XS_SinusCut", PINK, rough=0.25, coat=0.7, back=(0.75, 0.2, 0.3))
recolour("M_XS_Mucosa", PINK, rough=0.25, coat=0.7)
recolour("XS_Brain_M", ((0.95, 0.65, 0.7), (1.0, 0.8, 0.82)), rough=0.35, coat=0.4, back=(0.98, 0.78, 0.8))
recolour("XS_Tongue_M", ((0.9, 0.32, 0.4), (1.0, 0.5, 0.55)), rough=0.35, coat=0.4, back=(0.92, 0.38, 0.42))
xs = bpy.data.materials.get("M_XS_Skin")
if xs:
    for n in xs.node_tree.nodes:
        if n.type == "BSDF_PRINCIPLED" and not n.inputs["Base Color"].is_linked:   # the cut face (muscle): clean red-pink
            n.inputs["Base Color"].default_value = (0.88, 0.3, 0.32, 1); n.inputs["Roughness"].default_value = 0.4
        if n.type == "VALTORGB":
            n.color_ramp.elements[0].color = (0.85, 0.28, 0.3, 1); n.color_ramp.elements[1].color = (1.0, 0.45, 0.45, 1)
        if n.type == "BUMP": n.inputs["Strength"].default_value = 0.1
# 6. tunnel: clean glossy pink with soft veins (not a medical photo)
tm = bpy.data.materials.get("M_Tunnel")
if tm:
    for n in tm.node_tree.nodes:
        if n.type == "VALTORGB": n.color_ramp.elements[0].color = (0.85, 0.32, 0.4, 1); n.color_ramp.elements[1].color = (1.0, 0.6, 0.65, 1)
        if n.type == "MIX" and n.data_type == "RGBA": n.inputs[6].default_value = (0.75, 0.22, 0.32, 1)
        if n.type == "BSDF_PRINCIPLED": n.inputs["Emission Strength"].default_value = 0.8; n.inputs["Emission Color"].default_value = (1.0, 0.5, 0.55, 1)
        if n.type == "BUMP": n.inputs["Strength"].default_value = 0.2
for o in bpy.data.objects:
    if o.type == "LIGHT" and o.name.startswith("Tunnel_"): o.data.energy = 1.5
# 7. skin: smooth, no pores (MPFB bump/normal already x0.35 by anim_look; also clamp SSS-driven greyness)
print("ANIM_FIX done")
bpy.ops.wm.save_as_mainfile(filepath=out, compress=True)
