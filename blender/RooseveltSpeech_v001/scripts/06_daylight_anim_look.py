"""Hand fixes after pipeline/anim_look.py (client look change, Nov 11 22:45): bright daytime street, bright hall,
sky-gradient studio dome, clean glossy (not wet) anatomy, softer scans.  blender -b in.blend --python 06_daylight_anim_look.py -- out.blend"""
import sys, bpy
out = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene
def obj(n): return bpy.data.objects.get(n)
# ---- daytime sun + sky light (street and hall share the world; hall is indoors so the sun is street-only)
sun = obj("MoonFill"); sun.data.energy = 5.5; sun.data.color = (1.0, 0.95, 0.86); sun.data.angle = 0.03
sun.rotation_euler = (0.42, 0.0, 0.5)
for nm in ("HeroKey", "HeroRim"): obj(nm).data.energy *= 1.4; obj(nm).data.color = (1, 0.97, 0.92)
# world lighting: fcurve-keyed strength (street 0.05 / hall 0.3) -> bright daytime fill everywhere
w = sc.world; bg = next(n for n in w.node_tree.nodes if n.type == "BACKGROUND" and n.inputs["Color"].is_linked)
ad = w.animation_data
if ad and ad.action:
    for lay in getattr(ad.action, "layers", []):
        for st in lay.strips:
            for cb in st.channelbags:
                for fc in list(cb.fcurves):
                    if "Strength" in fc.data_path or "inputs[1]" in fc.data_path: cb.fcurves.remove(fc)
bg.inputs["Strength"].default_value = 1.4
# lamps by day: gas/lantern/headlamp lights much lower, lit windows dimmer (rooms still read warm)
for L in bpy.data.lights:
    if L.name.startswith(("GasLight", "LanternLight")): L.energy *= 0.25
    if L.name.startswith("HeadLamp"): L.energy *= 0.3
    if L.name.startswith(("ChandLight", "StageKey", "StageRim", "Footlights")): L.energy *= 1.6
for m in bpy.data.materials:
    if m.name.startswith("WindowLit"):
        for n in m.node_tree.nodes:
            if n.type == "MATH" and n.operation == "MULTIPLY" and abs(n.inputs[1].default_value - 2.2) < 1e-3: n.inputs[1].default_value = 0.9
    if m.name.startswith(("GasGlow", "CarLampGlow")):
        b = m.node_tree.nodes.get("Principled BSDF")
        if b: b.inputs["Emission Strength"].default_value *= 0.25
# ---- studio dome: sky-blue gradient, cyan #4FC3F7 top -> #E8F7FF bottom
dm = bpy.data.materials["StudioDome"]
rp = next(n for n in dm.node_tree.nodes if n.type == "VALTORGB")
rp.color_ramp.elements[0].color = (0.55, 0.84, 1.0, 1); rp.color_ramp.elements[1].color = (0.03, 0.42, 0.95, 1)
# ghost body reads on the light backdrop: slightly deeper cyan rim
for m in bpy.data.materials:
    if not m.node_tree: continue
    for n in m.node_tree.nodes:
        if n.type == "EMISSION" and tuple(round(c, 2) for c in n.inputs["Color"].default_value[:3]) == (0.35, 0.75, 1.0):
            n.inputs["Color"].default_value = (0.1, 0.45, 0.85, 1); n.inputs["Strength"].default_value = 0.7
# ---- anatomy: clean glossy colour-coded, not wet
mu = bpy.data.materials["ChestMuscle"]; mb = mu.node_tree.nodes["Principled BSDF"]
mb.inputs["Coat Weight"].default_value = 0.25; mb.inputs["Coat Roughness"].default_value = 0.3
for n in mu.node_tree.nodes:
    if n.type == "MIX" and n.data_type == "RGBA": n.inputs["A"].default_value = (0.75, 0.12, 0.16, 1); n.inputs["B"].default_value = (0.95, 0.35, 0.38, 1)
bo = bpy.data.materials["BonePorous"]
for n in bo.node_tree.nodes:
    if n.type == "MIX" and n.data_type == "RGBA": n.inputs["A"].default_value = (0.92, 0.86, 0.7, 1); n.inputs["B"].default_value = (0.98, 0.95, 0.85, 1)
for m in bpy.data.materials:
    if m.name.startswith("Lung"):
        b = m.node_tree.nodes.get("Principled BSDF")
        if b: b.inputs["Coat Weight"].default_value = 0.25; b.inputs["Coat Roughness"].default_value = 0.3
# wound: small clean dark-red mark, no gore
for m in bpy.data.materials:
    if not m.node_tree: continue
    for n in m.node_tree.nodes:
        if n.type == "BSDF_PRINCIPLED" and tuple(round(c, 3) for c in n.inputs["Base Color"].default_value[:3]) == (0.035, 0.012, 0.01):
            n.inputs["Base Color"].default_value = (0.35, 0.02, 0.03, 1)
        if n.type == "MAP_RANGE" and abs(n.inputs["From Max"].default_value - 0.028) < 1e-4: n.inputs["From Max"].default_value = 0.016
# breath vapour reads as murky by day: hide
for o in bpy.data.objects:
    if o.name.startswith("Breath"): o.hide_render = True
    if o.animation_data and o.name.startswith("Breath"): o.animation_data_clear(); o.hide_render = True
sc.view_settings.exposure = 0.45
for n in dm.node_tree.nodes:
    if n.type == "EMISSION": n.inputs["Strength"].default_value = 1.15
for m in bpy.data.materials:
    if m.name.startswith("InteriorDark"): m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.25, 0.18, 0.12, 1)
bpy.ops.wm.save_as_mainfile(filepath=out, compress=True)
print("DAYLIGHT OK")
