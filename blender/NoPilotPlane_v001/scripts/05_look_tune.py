"""Hand-tune after pipeline/anim_look.py (client LOOK CHANGE 22:45 UTC: bright, clean 3D animation, not a film).
blender -b work/anim_look.blend --python 05_look_tune.py -- out.blend
- sky dome: clean cyan (#4FC3F7-ish) zenith to near-white horizon; ground haze lighter and thinner
- cockpit: light Boeing grey-blue panels, wear/scuff contrast cut to 25 %, brighter soft fill
- pilots' suits: clean navy uniform colour instead of near-black
- exposure +0.3, no motion blur, farm settings kept"""
import sys, bpy
out = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene; M = bpy.data.materials
def lerp(a, b, t): return tuple(a[i] + (b[i] - a[i]) * t for i in range(len(a)))
# sky dome
rp = [n for n in M["M_sky"].node_tree.nodes if n.type == 'VALTORGB'][0].color_ramp
for el in rp.elements:
    el.color = (0.80, 0.93, 1.0, 1) if el.position < 0.03 else ((0.55, 0.82, 1.0, 1) if el.position < 0.3 else (0.08, 0.50, 0.93, 1))
em = [n for n in M["M_sky"].node_tree.nodes if n.type == 'EMISSION'][0]; em.inputs["Strength"].default_value = 1.8
# ground: less haze, lighter haze colour, a touch more saturated fields
g = M["M_ground"].node_tree
for n in g.nodes:
    if n.type == 'MATH' and n.operation == 'MINIMUM': n.inputs[1].default_value = 0.55
    if n.type == 'MIX' and n.data_type == 'RGBA' and tuple(round(c, 2) for c in n.inputs["B"].default_value[:3]) == (0.55, 0.62, 0.72):
        n.inputs["B"].default_value = (0.78, 0.88, 0.97, 1)
# cockpit palette: light grey-blue, clean
for name, col in (("M_panel", (0.20, 0.25, 0.32)), ("M_cockpit_dark", (0.10, 0.12, 0.15)), ("M_glareshield_fabric", (0.07, 0.08, 0.10))):
    m = M.get(name)
    if m:
        p = m.node_tree.nodes["Principled BSDF"]
        for n in m.node_tree.nodes:
            if n.type == 'MIX' and n.data_type == 'RGBA' and not n.inputs["A"].is_linked: n.inputs["A"].default_value = (*col, 1)
        if not p.inputs["Base Color"].is_linked: p.inputs["Base Color"].default_value = (*col, 1)
for m in M:   # worn/scuffed materials: cut the wear contrast to 25 %, raise the base where it is the pedestal
    if not m.use_nodes or not any(k in m.name for k in ("worn", "leather", "M_screw", "throttle_knob")): continue
    for n in m.node_tree.nodes:
        if n.type == 'MIX' and n.data_type == 'RGBA' and not n.inputs["A"].is_linked and not n.inputs["B"].is_linked:
            if "pedestal" in m.name: n.inputs["A"].default_value = (0.20, 0.25, 0.32, 1)
            n.inputs["B"].default_value = lerp(n.inputs["A"].default_value, n.inputs["B"].default_value, 0.25)
cs = M["M_cockpit_shell"].node_tree
for n in cs.nodes:
    if n.type == 'TEX_BRICK':
        n.inputs["Color1"].default_value = (0.42, 0.47, 0.53, 1); n.inputs["Color2"].default_value = (0.39, 0.44, 0.5, 1); n.inputs["Mortar"].default_value = (0.3, 0.34, 0.38, 1)
# pilots' suits: clean navy uniform
for m in M:
    if "elegantsuit" in m.name and m.use_nodes:
        hs = [n for n in m.node_tree.nodes if n.type == 'HUE_SAT']
        for n in hs: n.inputs["Value"].default_value = 2.2; n.inputs["Saturation"].default_value = 1.6
        p = m.node_tree.nodes.get("Principled BSDF")
        if p and hs:
            mx = m.node_tree.nodes.new("ShaderNodeMix"); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs["Factor"].default_value = 0.85
            m.node_tree.links.new(hs[0].outputs["Color"], mx.inputs["A"]); mx.inputs["B"].default_value = (0.35, 0.5, 1.0, 1)
            m.node_tree.links.new(mx.outputs["Result"], p.inputs["Base Color"])
# light: high-key soft fill in the cockpit and cabin
O = bpy.data.objects
for nm, k in (("L_cockpit", 3.0), ("L_door_fill", 2.0), ("L_panel_glow", 2.5)):
    if nm in O: O[nm].data.energy *= k
for o in O:
    if o.name.startswith("L_cabin_"): o.data.energy *= 1.3
ld = bpy.data.lights.new("L_cockpit_softbox", 'AREA'); ld.shape = 'RECTANGLE'; ld.size, ld.size_y = 1.8, 1.4; ld.energy = 260; ld.color = (1, 0.98, 0.95)
lo = bpy.data.objects.new("L_cockpit_softbox", ld); lo.location = (0, 1.25, 2.12); sc.collection.objects.link(lo)
ld2 = bpy.data.lights.new("L_face_fill", 'AREA'); ld2.size = 0.8; ld2.energy = 60; ld2.color = (1, 0.97, 0.94)
lo2 = bpy.data.objects.new("L_face_fill", ld2); lo2.location = (0.52, 2.05, 1.35); lo2.rotation_euler = (-1.5708, 0, 0); sc.collection.objects.link(lo2)
# keep the original eye/teeth/lash shaders: the generic look pass (roughness floor, saturation) turns the procedural eyes black
import os
SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "work", "anim.blend")
keep = [m.name for m in M if any(k in m.name for k in ("high-poly", "teeth_base", "eyelashes01", "eyebrow001"))]
with bpy.data.libraries.load(SRC, link=False) as (src, dst):
    dst.materials = [n for n in src.materials if n in keep]
for o in bpy.data.objects:
    if o.type != 'MESH': continue
    for slot in o.material_slots:
        if slot.material and slot.material.name in keep:
            new = [m for m in dst.materials if m and m.name.startswith(slot.material.name + ".")]
            if new: slot.material = new[0]
O["L_face_fill"].data.energy = 25
# galley fill on the door (kills YOU's head shadow) and a lighter cockpit floor mat
ld3 = bpy.data.lights.new("L_galley_door_fill", 'AREA'); ld3.size = 0.7; ld3.energy = 70; ld3.color = (1, 0.97, 0.94)
lo3 = bpy.data.objects.new("L_galley_door_fill", ld3); lo3.location = (0.35, -0.95, 1.95); lo3.rotation_euler = (0.9, 0, 0.5); sc.collection.objects.link(lo3)
fl = M.get("M_floor_rubber")
if fl: fl.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.13, 0.15, 0.18, 1)
sc.view_settings.exposure = 0.3
sc.render.use_motion_blur = False
sc.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=out, compress=True)
print("LOOKTUNE saved", out)
