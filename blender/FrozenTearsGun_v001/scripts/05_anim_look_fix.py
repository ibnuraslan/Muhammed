"""Hand fixes after pipeline/anim_look.py for the animated-CG look (client, Nov 11 22:45).
blender -b in.blend --python 05_anim_look_fix.py -- out.blend"""
import sys, bpy
out = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene
def F(t): return 1 + round(t * 60)
def fcurves(idblock):
    ad = idblock.animation_data
    if not ad or not ad.action: return []
    return [fc for l in ad.action.layers for s in l.strips for cb in s.channelbags for fc in cb.fcurves]
def lin(h):
    h = h.lstrip('#'); c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(((x + 0.055) / 1.055) ** 2.4 if x > 0.04045 else x / 12.92 for x in c) + (1.0,)
SKY_TOP, SKY_BOT = (0.02, 0.42, 0.95, 1.0), (0.80, 0.93, 1.0, 1.0)   # #4FC3F7 -> #E8F7FF, pushed for AgX Punchy
# 1) explainer backdrop: sky-blue gradient, cyan at the top -> near-white at the bottom
rmp = next(n for n in bpy.data.materials["M_ExplainerGradient"].node_tree.nodes if n.type == 'VALTORGB')
rmp.color_ramp.elements[0].position = 0.0; rmp.color_ramp.elements[0].color = SKY_BOT
rmp.color_ramp.elements[1].position = 1.0; rmp.color_ramp.elements[1].color = SKY_TOP
next(n for n in bpy.data.materials["M_ExplainerGradient"].node_tree.nodes if n.type == 'EMISSION').inputs["Strength"].default_value = 1.35
# 2) workshop: daytime sky outside the window instead of night, brighter clean interior
p = bpy.data.materials["M_NightOutside"].node_tree.nodes["Principled BSDF"]
p.inputs["Emission Color"].default_value = SKY_TOP; p.inputs["Base Color"].default_value = SKY_TOP
for fc in fcurves(bpy.data.materials["M_NightOutside"].node_tree):
    for kp in fc.keyframe_points: kp.co.y = 2.5; kp.handle_left.y = kp.handle_right.y = 2.5
moon = bpy.data.lights["L_WindowMoon"]
for fc in fcurves(moon):
    if fc.data_path == "energy":
        for kp in fc.keyframe_points: kp.co.y = 120.0; kp.handle_left.y = kp.handle_right.y = 120.0
    if fc.data_path == "color":
        v = (1.0, 0.97, 0.92)[fc.array_index]
        for kp in fc.keyframe_points: kp.co.y = v; kp.handle_left.y = kp.handle_right.y = v
for nm, e in (("L_Bulb", 380.0), ("L_FrontWash", 160.0), ("L_FaceFill", 30.0), ("L_RimBack", 60.0), ("L_DeskLamp", 80.0)):
    bpy.data.lights[nm].energy = e
for n in sc.world.node_tree.nodes:
    if n.type == 'BACKGROUND' and n.inputs[0].is_linked and n.inputs[0].links[0].from_node.type == 'TEX_ENVIRONMENT':
        n.inputs["Strength"].default_value = 0.35
# 3) keyed light energies x1.25 (anim_look only scales static values)
for L in bpy.data.lights:
    if L.name in ("L_WindowMoon",): continue
    for fc in fcurves(L):
        if fc.data_path == "energy":
            for kp in fc.keyframe_points:
                kp.co.y *= 1.25; kp.handle_left.y *= 1.25; kp.handle_right.y *= 1.25
# 4) keyed f-stop: at least 5.6 everywhere (macro beats are already f/8-f/40)
cam = sc.camera.data
for fc in fcurves(cam):
    if fc.data_path == "dof.aperture_fstop":
        for kp in fc.keyframe_points:
            kp.co.y = max(5.6, kp.co.y); kp.handle_left.y = max(5.6, kp.handle_left.y); kp.handle_right.y = max(5.6, kp.handle_right.y)
# 5) exposure: the two memory flashes become short (6-frame peak) and mild, so nothing blows out; office at 0
for fc in fcurves(sc):
    if fc.data_path == "view_settings.exposure":
        sc.animation_data.action  # keep
        while len(fc.keyframe_points): fc.keyframe_points.remove(fc.keyframe_points[0])
for t, e in ((0, 0.0), (18.78, 0.0), (18.88, 1.8), (18.98, 1.8), (19.1, 0.0), (28.2, 0.0), (28.3, 1.8), (28.4, 1.8), (28.52, 0.0)):
    sc.view_settings.exposure = e; sc.view_settings.keyframe_insert("exposure", frame=F(t))
sc.render.use_motion_blur = False
bpy.ops.wm.save_as_mainfile(filepath=out, compress=True)
print("ANIMFIX saved", out)
