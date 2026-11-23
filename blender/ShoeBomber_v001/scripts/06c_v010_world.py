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
hs = N.new("ShaderNodeHueSaturation"); hs.inputs["Saturation"].default_value = 0.25
Lk.new(mix.outputs["Result"], hs.inputs["Color"])
bg_light = N.new("ShaderNodeBackground"); bg_light.inputs["Strength"].default_value = bg.inputs["Strength"].default_value
Lk.new(hs.outputs["Color"], bg_light.inputs["Color"])
# camera branch: blue sky
sky = N.new("ShaderNodeTexSky"); sky.sky_type = 'PREETHAM'; sky.turbidity = 2.2
sky.sun_direction = (0.3, -0.5, 0.81)
bg_cam = N.new("ShaderNodeBackground"); bg_cam.inputs["Strength"].default_value = 0.55
sat = N.new("ShaderNodeHueSaturation"); sat.inputs["Saturation"].default_value = 1.6; sat.inputs["Value"].default_value = 0.9
Lk.new(sky.outputs["Color"], sat.inputs["Color"]); Lk.new(sat.outputs["Color"], bg_cam.inputs["Color"])
lp = N.new("ShaderNodeLightPath"); ms = N.new("ShaderNodeMixShader")
Lk.new(lp.outputs["Is Camera Ray"], ms.inputs["Fac"])
Lk.new(bg_light.outputs["Background"], ms.inputs[1]); Lk.new(bg_cam.outputs["Background"], ms.inputs[2])
Lk.new(ms.outputs["Shader"], N["World Output"].inputs["Surface"])
# sun: white daylight
for o in bpy.data.objects:
    if o.type == 'LIGHT' and o.data.type == 'SUN': o.data.color = (1.0, 0.97, 0.92)
# cloud deck: white tops, soft grey shadows (no pink)
cd = bpy.data.materials.get("CloudDeck")
if cd:
    for n in cd.node_tree.nodes:
        if n.type == 'VALTORGB':
            for e in n.color_ramp.elements:
                v = sum(e.color[:3]) / 3; g = 0.55 + 0.45 * v
                e.color = (g * 0.97, g * 0.98, g, e.color[3])
        if n.type == 'BSDF_PRINCIPLED' and not n.inputs["Base Color"].is_linked:
            n.inputs["Base Color"].default_value = (0.92, 0.93, 0.95, 1)
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
for f, ex in ((1, 0.9), (1158, 0.9), (1159, -0.5), (1392, -0.5), (1393, -0.4), (sc.frame_end, -0.4)):
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
