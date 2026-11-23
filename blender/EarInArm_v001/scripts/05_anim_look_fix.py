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
# v009i: the cabinet glass mirrored a hard white triangle (a light) top-left in many shots: matte dark panels instead
_cg = bpy.data.materials.new("CabGlass_Matte"); _cg.use_nodes = True; _cb = _cg.node_tree.nodes["Principled BSDF"]
_cb.inputs["Base Color"].default_value = (0.03, 0.035, 0.04, 1); _cb.inputs["Roughness"].default_value = 0.55
for _o in [o for o in bpy.data.objects if o.name.startswith("OR_CabGlass")]:
    for _i in range(len(_o.data.materials)): _o.data.materials[_i] = _cg
# v012: warmer light (the clinic read bare and grey)
for _n, _c in (("OR_Key0", (1.0, 0.88, 0.74)), ("OR_Key1", (1.0, 0.86, 0.7)), ("OR_Key2", (1.0, 0.92, 0.82)), ("OR_Key3", (1.0, 0.9, 0.8)), ("OR_SurgSpot", (1.0, 0.95, 0.86))):
    if _n in bpy.data.objects: bpy.data.objects[_n].data.color = _c
# v012: motivated three-point light (key from the surgical lamp side, softer cool fill, warm rim) and less motion blur
for _n, _e in (("OR_Key0", 1.15), ("OR_Key1", 1.25), ("OR_Key2", 0.6), ("OR_Key3", 1.3)):
    if _n in bpy.data.objects: bpy.data.objects[_n].data.energy *= _e
bpy.context.scene.render.motion_blur_shutter = 0.2; bpy.context.scene.render.use_motion_blur = False   # v013: no motion blur (director: heavy blur everywhere)
print("ANIMFIX_DONE")
# v012b: the vessel web hid the ear's shape in the growth close-ups; show the ear clearly (cartilage shape first),
# then only a few thin vessels once it has turned pink (stage 3)
for o in bpy.data.objects:
    if o.name.startswith("SB_Vessel"):
        if o.animation_data: o.animation_data_clear()
        i = int(o.name[9:] or 0); keep = False   # v012b: none (they read as a red scribble over the ear)
        o.hide_render = True; o.keyframe_insert("hide_render", frame=1)
        if keep:
            o.hide_render = False; o.keyframe_insert("hide_render", frame=990)
            o.hide_render = True; o.keyframe_insert("hide_render", frame=1046)
bpy.ops.wm.save_as_mainfile(filepath=out, compress=True)
