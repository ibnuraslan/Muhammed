"""Post anim_look.py hand fixes for EarInArm (client look change, 22:45). blender -b in.blend --python 05_anim_look_fix.py -- out.blend"""
import sys, bpy
out = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene
sc.view_settings.exposure = -1.5
# keyed f-stop: never below 5.6 (macros keep their high values)
cd = bpy.data.cameras["CAM_Film"]
for layer in cd.animation_data.action.layers:
    for strip in layer.strips:
        for cb in strip.channelbags:
            for fc in cb.fcurves:
                if "aperture_fstop" in fc.data_path:
                    for kp in fc.keyframe_points:
                        kp.co.y = max(5.6, kp.co.y); kp.handle_left.y = max(5.6, kp.handle_left.y); kp.handle_right.y = max(5.6, kp.handle_right.y)
# studio backdrop -> sky gradient (bottom near-white, top sky cyan)
for mn in ("SA_Grad", "SB_Grad"):
    m = bpy.data.materials.get(mn)
    if not m: continue
    cr = next(n for n in m.node_tree.nodes if n.type == 'VALTORGB')
    els = sorted(cr.color_ramp.elements, key=lambda e: e.position)
    els[0].color = (0.80, 0.93, 1.0, 1); els[-1].color = (0.08, 0.55, 0.93, 1)
    for e in els[1:-1]: e.color = (0.35, 0.75, 0.97, 1)
    em = next(n for n in m.node_tree.nodes if n.type == 'EMISSION'); em.inputs["Strength"].default_value = 1.0
fl = bpy.data.materials.get("SA_FloorMat")
if fl: fl.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.75, 0.9, 1.0, 1)
# bright clean interior: lighter walls/floor tint, brighter chair teal
def set_tint(mname, col):
    m = bpy.data.materials.get(mname)
    if not m: return
    for n in m.node_tree.nodes:
        if n.type == 'MIX' and n.blend_type == 'MULTIPLY': n.inputs["B"].default_value = (*col, 1)
set_tint("Wall_Plaster", (0.88, 0.95, 1.0)); set_tint("Floor_Tiles", (0.95, 0.97, 1.0)); set_tint("Upholstery", (0.1, 0.55, 0.75))
# cartilage: clean pearly, vessels saturated red; gloves brighter blue
for mn, col in (("Cartilage", (0.93, 0.93, 0.9)), ("SB_Vessel", (0.75, 0.03, 0.05)), ("Vessel", (0.75, 0.03, 0.05)), ("NitrileGlove", (0.15, 0.45, 0.95))):
    m = bpy.data.materials.get(mn)
    if m: m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (*col, 1)
# softer, even key: raise the fill, keep the rim
for ln, e in (("OR_Key2", 160),):
    L = bpy.data.lights.get(ln)
    if L: L.energy = e
# clean painted walls (no plaster grime)
m = bpy.data.materials.get("Wall_Plaster")
if m:
    b = m.node_tree.nodes["Principled BSDF"]
    for l in list(b.inputs["Base Color"].links): m.node_tree.links.remove(l)
    b.inputs["Base Color"].default_value = (0.82, 0.9, 0.95, 1)
    for l in list(b.inputs["Roughness"].links): m.node_tree.links.remove(l)
    b.inputs["Roughness"].default_value = 0.6
print("ANIMFIX_DONE")
bpy.ops.wm.save_as_mainfile(filepath=out, compress=True)
