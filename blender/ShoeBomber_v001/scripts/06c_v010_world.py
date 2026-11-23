"""v010 (director 12-13): blue daytime sky instead of the pink dusk.
Camera rays see a clear blue sky (Preetham, high sun); lighting keeps the existing world but desaturated to neutral, the
sun lamp goes white and the cloud deck goes white/grey. The sky shot gets a cleaner exposure.
blender -b in.blend --python 06c_v010_world.py -- <out.blend>"""
import sys, math, bpy
OUT = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene
w = sc.world; nt = w.node_tree; N = nt.nodes; Lk = nt.links
bg = N["WorldBG"]; mix = N["Mix"]
# lighting branch: the old mix, desaturated
hs = N.new("ShaderNodeHueSaturation"); hs.inputs["Saturation"].default_value = 0.0
Lk.new(mix.outputs["Result"], hs.inputs["Color"])
bg_light = N.new("ShaderNodeBackground"); bg_light.inputs["Strength"].default_value = bg.inputs["Strength"].default_value
Lk.new(hs.outputs["Color"], bg_light.inputs["Color"])
# camera branch: clean blue daytime gradient (horizon pale blue -> deep blue zenith), no pink anywhere
tcw = N.new("ShaderNodeTexCoord"); sepw = N.new("ShaderNodeSeparateXYZ"); mr = N.new("ShaderNodeMapRange")
mr.inputs["From Min"].default_value = 0.0; mr.inputs["From Max"].default_value = 0.55
rp = N.new("ShaderNodeValToRGB")
rp.color_ramp.elements[0].color = (0.50, 0.70, 0.95, 1); rp.color_ramp.elements[1].color = (0.05, 0.22, 0.72, 1)
Lk.new(tcw.outputs["Generated"], sepw.inputs[0]); Lk.new(sepw.outputs["Z"], mr.inputs["Value"]); Lk.new(mr.outputs["Result"], rp.inputs["Fac"])
bg_cam = N.new("ShaderNodeBackground"); bg_cam.inputs["Strength"].default_value = 1.0
Lk.new(rp.outputs["Color"], bg_cam.inputs["Color"])
lp = N.new("ShaderNodeLightPath"); ms = N.new("ShaderNodeMixShader")
Lk.new(lp.outputs["Is Camera Ray"], ms.inputs["Fac"])
Lk.new(bg_light.outputs["Background"], ms.inputs[1]); Lk.new(bg_cam.outputs["Background"], ms.inputs[2])
Lk.new(ms.outputs["Shader"], N["World Output"].inputs["Surface"])
# sun: white daylight
for o in bpy.data.objects:
    if o.type == 'LIGHT' and o.data.type == 'SUN': o.data.color = (1.0, 1.0, 1.0)
# cloud deck: white tops, soft grey shadows (no pink)
cd = bpy.data.materials.get("CloudDeck")
if cd:
    for n in cd.node_tree.nodes:
        if n.type == 'VALTORGB':
            for e in n.color_ramp.elements[1:]:
                v = sum(e.color[:3]) / 3
                e.color = (v * 0.97, v * 0.985, v, e.color[3])
        if n.type == 'BSDF_PRINCIPLED':
            if not n.inputs["Base Color"].is_linked: n.inputs["Base Color"].default_value = (0.92, 0.93, 0.95, 1)
            n.inputs["Subsurface Weight"].default_value = 0.0      # its red-default SSS radius tinted the deck pink-brown
# the floor under the decks (seen through their gaps) was brown-pink: cool blue-grey cloud shadow instead
cf = bpy.data.materials.get("CloudFloorMat")
if cf and cf.use_nodes:
    for n in cf.node_tree.nodes:
        for inp in n.inputs:
            if inp.name in ("Color", "Base Color", "Emission Color") and not inp.is_linked and hasattr(inp.default_value, "__len__"):
                inp.default_value = (0.50, 0.56, 0.66, 1)
            if inp.name == "Subsurface Weight": inp.default_value = 0.0
# any other warm-tinted sky materials (cloud banks, haze) -> neutral
for mname in ("CloudBank", "Haze", "SkyHaze"):
    m = bpy.data.materials.get(mname)
    if m and m.use_nodes:
        for n in m.node_tree.nodes:
            for inp in n.inputs:
                if inp.name in ("Color", "Base Color") and not inp.is_linked and hasattr(inp.default_value, "__len__"):
                    inp.default_value = (0.92, 0.93, 0.95, 1)
# exposure per set (keys replace 06's): cabin + beat-7 shoe +0.9, sky -0.5 (no washed-out deck), airport -0.4
ad = sc.animation_data
if ad and ad.action:
    for layer in ad.action.layers:
        for strip in layer.strips:
            for cb in strip.channelbags:
                for fc in list(cb.fcurves):
                    if fc.data_path == "view_settings.exposure": cb.fcurves.remove(fc)
for f, ex in ((1, 0.9), (1158, 0.9), (1159, -1.0), (1392, -1.0), (1393, -0.4), (sc.frame_end, -0.4)):
    sc.view_settings.exposure = ex; sc.view_settings.keyframe_insert("exposure", frame=f)
ad = sc.animation_data
for layer in ad.action.layers:
    for strip in layer.strips:
        for cb in strip.channelbags:
            for fc in cb.fcurves:
                if fc.data_path == "view_settings.exposure":
                    for kp in fc.keyframe_points: kp.interpolation = 'CONSTANT'
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print("WORLD_V010_SAVED", OUT)
