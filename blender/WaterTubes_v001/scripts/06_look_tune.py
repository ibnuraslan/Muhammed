"""Animated-CG look, hand tuning on top of pipeline/anim_look.py (client look change, Nov 11 22:45 UTC).
blender -b look.blend --python 06_look_tune.py -- <out.blend>
- camera-ray sky: bright stylised storm sky (soft slate-blue with puffy clouds) that clears to the cyan->white sky by beat 8
- lighting: high-key; keyed world/sun strengths rescaled (anim_look's static multipliers are overridden by keys)
- cutaway shell: sky-blue gradient (#4FC3F7 top -> #E8F7FF bottom)
- section water: clean saturated blue with soft caustics; flood water: clean ochre-brown, glossy, simple foam
- clean surfaces: house grime/streaks off (story mud line kept), tube vinyl clean, f-stop >= 5.6 except the cutaway macro"""
import bpy, sys, math
OUT = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene
def F(t): return 1 + round(t * 60)
def srgb(h):
    h = h.lstrip("#"); c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(((x + 0.055) / 1.055) ** 2.4 if x > 0.04045 else x / 12.92 for x in c) + (1.0,)
SKY_TOP, SKY_BOT = srgb("#4FC3F7"), srgb("#E8F7FF")
sc.view_settings.look = "AgX - Punchy"; sc.render.use_motion_blur = False

def fcurves_of(idblock):
    ad = idblock.animation_data
    if not ad or not ad.action: return []
    out = []
    for layer in getattr(ad.action, "layers", []):
        for strip in layer.strips:
            for cb in getattr(strip, "channelbags", []): out += list(cb.fcurves)
    return out or list(getattr(ad.action, "fcurves", []))
def scale_keys(idblock, path_part, mul, add=0.0):
    for fc in fcurves_of(idblock):
        if path_part in fc.data_path:
            for kp in fc.keyframe_points:
                kp.co.y = kp.co.y * mul + add; kp.handle_left.y = kp.handle_left.y * mul + add; kp.handle_right.y = kp.handle_right.y * mul + add
            fc.update()

# ------------------------------------------------------------------ world: lighting brighter, camera sees a stylised sky
w = sc.world; nt = w.node_tree; N, L = nt.nodes, nt.links
scale_keys(w.node_tree, 'nodes["Background"].inputs[1]', 1.7, 0.2)        # HDRI light strength
scale_keys(w.node_tree, 'nodes["StormGrade"].inputs[2]', 0.6, 0.4)         # lift saturation of the light
scale_keys(w.node_tree, 'nodes["StormGrade"].inputs[4]', 0.5, 0.5)         # lift value (brighter storm light)
mix = N.get("anim_look_v1")
skyb = mix.inputs[2].links[0].from_node
for n in list(N):
    if n.type == "VALTORGB" and n.outputs[0].links and n.outputs[0].links[0].to_node == skyb: N.remove(n)
tc = N.new("ShaderNodeTexCoord")
# vertical gradient by view direction (stable as the camera tilts): z of the ray direction
sep = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs["Generated"], sep.inputs[0])
mr = N.new("ShaderNodeMapRange"); mr.inputs["From Min"].default_value = 0.47; mr.inputs["From Max"].default_value = 0.75
L.new(sep.outputs["Z"], mr.inputs["Value"])
clear = N.new("ShaderNodeValToRGB"); clear.color_ramp.elements[0].color = SKY_BOT; clear.color_ramp.elements[1].color = SKY_TOP
L.new(mr.outputs[0], clear.inputs[0])
storm = N.new("ShaderNodeValToRGB"); storm.color_ramp.elements[0].color = (0.62, 0.7, 0.8, 1); storm.color_ramp.elements[1].color = (0.24, 0.36, 0.55, 1)
L.new(mr.outputs[0], storm.inputs[0])
# puffy clouds: noise on the view direction, drifting with the HDRI mapping
mp = N.get("HDRIMap")
nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 3.2; nz.inputs["Detail"].default_value = 4; nz.inputs["Roughness"].default_value = 0.55
L.new(mp.outputs[0], nz.inputs["Vector"])
cr = N.new("ShaderNodeMapRange"); cr.inputs["From Min"].default_value = 0.5; cr.inputs["From Max"].default_value = 0.62; L.new(nz.outputs["Fac"], cr.inputs["Value"])
horizon = N.new("ShaderNodeMath"); horizon.operation = "MULTIPLY"; horizon.use_clamp = True; L.new(cr.outputs[0], horizon.inputs[0]); L.new(mr.outputs[0], horizon.inputs[1])
storm_v = N.new("ShaderNodeValue"); storm_v.name = "StormAmount"
for f, v in ((1, 1.0), (F(24.0), 1.0), (F(26.5), 0.25), (F(29.0), 0.0)):
    storm_v.outputs[0].default_value = v; storm_v.outputs[0].keyframe_insert("default_value", frame=f)
sky_mix = N.new("ShaderNodeMix"); sky_mix.data_type = "RGBA"; L.new(storm_v.outputs[0], sky_mix.inputs["Factor"])
L.new(clear.outputs[0], sky_mix.inputs["A"]); L.new(storm.outputs[0], sky_mix.inputs["B"])
cloud_col = N.new("ShaderNodeMix"); cloud_col.data_type = "RGBA"; L.new(storm_v.outputs[0], cloud_col.inputs["Factor"])
cloud_col.inputs["A"].default_value = (0.97, 0.98, 1.0, 1); cloud_col.inputs["B"].default_value = (0.72, 0.76, 0.84, 1)
cm = N.new("ShaderNodeMix"); cm.data_type = "RGBA"; L.new(horizon.outputs[0], cm.inputs["Factor"])
L.new(sky_mix.outputs["Result"], cm.inputs["A"]); L.new(cloud_col.outputs["Result"], cm.inputs["B"])
L.new(cm.outputs["Result"], skyb.inputs["Color"])
skyb.inputs["Strength"].default_value = 1.0

# sun: stronger, warmer; keys rescaled
sun = bpy.data.objects["Sun"]
scale_keys(sun.data, "energy", 1.0, 2.2)
sun.data.angle = math.radians(10)

# ------------------------------------------------------------------ cutaway shell: sky-blue gradient
msh = bpy.data.materials["CutBackdrop"]; nt = msh.node_tree
ramp = next(n for n in nt.nodes if n.type == "VALTORGB")
while len(ramp.color_ramp.elements) > 2: ramp.color_ramp.elements.remove(ramp.color_ramp.elements[1])
ramp.color_ramp.elements[0].color = SKY_BOT; ramp.color_ramp.elements[0].position = 0.25
ramp.color_ramp.elements[1].color = SKY_TOP; ramp.color_ramp.elements[1].position = 0.8
for n in nt.nodes:
    if n.type == "EMISSION": n.inputs["Strength"].default_value = 1.0
# cutaway key light: brighter, softer
for n in ("CutKey", "CutRim"):
    bpy.data.objects[n].data.energy *= 2.0; bpy.data.objects[n].data.size *= 2.0

# ------------------------------------------------------------------ section water: clean saturated blue, soft caustics
mwt = bpy.data.materials["TubeWater"]; nt = mwt.node_tree
b = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
for l in list(b.inputs["Base Color"].links): nt.links.remove(l)
b.inputs["Base Color"].default_value = (0.0, 0.1, 0.55, 1); b.inputs["Subsurface Weight"].default_value = 0.3
b.inputs["Roughness"].default_value = 0.08; b.inputs["Coat Weight"].default_value = 1.0; b.inputs["Coat Roughness"].default_value = 0.02
vor = next(n for n in nt.nodes if n.type == "TEX_VORONOI")
cr2 = nt.nodes.new("ShaderNodeMapRange"); cr2.inputs["From Min"].default_value = 0.0; cr2.inputs["From Max"].default_value = 0.12
cr2.inputs["To Min"].default_value = 1.0; cr2.inputs["To Max"].default_value = 0.0; nt.links.new(vor.outputs["Distance"], cr2.inputs["Value"])
pw = nt.nodes.new("ShaderNodeMath"); pw.operation = "POWER"; pw.inputs[1].default_value = 3.0; nt.links.new(cr2.outputs[0], pw.inputs[0])
em = nt.nodes.new("ShaderNodeMath"); em.operation = "MULTIPLY_ADD"; em.inputs[1].default_value = 0.9; em.inputs[2].default_value = 0.15
nt.links.new(pw.outputs[0], em.inputs[0]); nt.links.new(em.outputs[0], b.inputs["Emission Strength"])
b.inputs["Emission Color"].default_value = (0.25, 0.7, 1.0, 1)
# animate the caustics (W drift)
vor.voronoi_dimensions = "4D"
for f, wv in ((1, 0.0), (2010, 8.0)):
    vor.inputs["W"].default_value = wv; vor.inputs["W"].keyframe_insert("default_value", frame=f)
for fc in fcurves_of(nt):
    for kp in fc.keyframe_points: kp.interpolation = "LINEAR"
for n in nt.nodes:
    if n.type == "OUTPUT_MATERIAL":
        for l in list(n.inputs["Volume"].links): nt.links.remove(l)

# ------------------------------------------------------------------ flood water: clean ochre-brown, glossy; simple foam
mw = bpy.data.materials["FloodWater"]; nt = mw.node_tree
for n in nt.nodes:
    if n.type == "MIX" and n.data_type == "RGBA" and not n.inputs["A"].links:
        n.inputs["A"].default_value = (0.2, 0.125, 0.06, 1); n.inputs["B"].default_value = (0.6, 0.48, 0.33, 1)
    if n.type == "BUMP": n.inputs["Strength"].default_value = 0.08
b = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED"); b.inputs["Coat Weight"].default_value = 0.6; b.inputs["Coat Roughness"].default_value = 0.05
fg = bpy.data.node_groups["FloodSurface"]
scale_keys(fg, 'nodes["Chop"]', 0.7)
msec = bpy.data.materials["FloodSection"]; bb = next(n for n in msec.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
bb.inputs["Base Color"].default_value = (0.45, 0.26, 0.09, 1); bb.inputs["Subsurface Radius"].default_value = (0.8, 0.45, 0.15)
bpy.data.materials["SprayMat"].node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.95, 0.92, 0.85, 1)

# ------------------------------------------------------------------ clean surfaces
for m in bpy.data.materials:
    if not m.node_tree: continue
    for n in m.node_tree.nodes:
        # house grime (near-ground darkening and weathering streak multiplies) -> off; keep story mud line
        if n.type == "MIX" and n.data_type == "RGBA" and n.blend_type == "MULTIPLY":
            bi = n.inputs["B"]
            if not bi.links and tuple(round(x, 2) for x in bi.default_value[:3]) == (0.35, 0.3, 0.25):
                for l in list(n.inputs["Factor"].links): m.node_tree.links.remove(l)
                n.inputs["Factor"].default_value = 0.0
            elif bi.links and bi.links[0].from_node.type == "TEX_NOISE" and not n.inputs["Factor"].links and n.inputs["Factor"].default_value == 0.3:
                n.inputs["Factor"].default_value = 0.06
# tube vinyl: clean deep blue-black, glossy, no mud spatter
mt = bpy.data.materials["TubeVinyl"]; nt = mt.node_tree
for n in nt.nodes:
    if n.type == "VALTORGB" and len(n.color_ramp.elements) == 2 and n.color_ramp.elements[0].color[0] < 0.03:
        n.color_ramp.elements[0].color = (0.035, 0.04, 0.038, 1); n.color_ramp.elements[1].color = (0.07, 0.078, 0.072, 1)
    if n.type == "MIX" and n.data_type == "RGBA" and not n.inputs["B"].links:
        n.inputs["B"].default_value = (0.045, 0.05, 0.047, 1)
    if n.type == "MATH" and n.operation == "MULTIPLY" and n.inputs[1].default_value == 1.8: n.inputs[1].default_value = 0.5
# lawn: brighter, cleaner green
for gname in ("Lawn_G",):
    g = bpy.data.node_groups.get(gname)
    if g:
        for n in g.nodes:
            if n.type == "MIX" and n.blend_type == "MULTIPLY": n.inputs["B"].default_value = (0.55, 1.0, 0.35, 1)
            if n.type == "NORMAL_MAP": n.inputs["Strength"].default_value = 0.3
for nm, col in (("ArrowFlood", (1.0, 0.33, 0.02)), ("ArrowWeight", (0.15, 0.75, 1.0))):
    ab = bpy.data.materials[nm].node_tree.nodes["Principled BSDF"]
    ab.inputs["Base Color"].default_value = (*col, 1); ab.inputs["Emission Color"].default_value = (*col, 1); ab.inputs["Emission Strength"].default_value = 1.2
    ab.inputs["Roughness"].default_value = 0.3; ab.inputs["Coat Weight"].default_value = 0.15
# DOF: >= 5.6 everywhere (anim_look), keep f/4 only on the cutaway macro
cam = sc.camera
cam.data.dof.aperture_fstop = 6.0
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("SAVED", OUT)
