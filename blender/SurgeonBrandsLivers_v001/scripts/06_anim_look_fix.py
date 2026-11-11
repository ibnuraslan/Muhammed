"""Hand fixes after pipeline/anim_look.py (client look change, Nov 11 22:45 UTC: bright clean 3D animation, not a film).
blender -b look.blend --python 06_anim_look_fix.py -- <out.blend>"""
import sys, colorsys
import bpy
OUT = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene
SKY_TOP = (0.08, 0.55, 0.93, 1)      # #4FC3F7 in linear
SKY_BOT = (0.80, 0.93, 1.0, 1)       # #E8F7FF in linear

def fcurves(id_):
    ad = id_.animation_data; out = []
    if ad and ad.action:
        for layer in getattr(ad.action, "layers", []):
            for strip in layer.strips:
                for cb in strip.channelbags:
                    out += list(cb.fcurves)
    return out

# 1. studio dome: bright sky gradient, cyan top -> near-white bottom
d = bpy.data.materials["StudioGradient"]
ramp = [n for n in d.node_tree.nodes if n.type == 'VALTORGB'][0]
els = ramp.color_ramp.elements
while len(els) > 2:
    els.remove(els[1])
els[0].position = 0.0; els[0].color = (0.50, 0.82, 1.0, 1)   # near-white cyan; pure #E8F7FF reads grey under AgX
els[1].position = 1.0; els[1].color = SKY_TOP
em = [n for n in d.node_tree.nodes if n.type == 'EMISSION'][0]; em.inputs['Strength'].default_value = 1.15
mr = [n for n in d.node_tree.nodes if n.type == 'MAP_RANGE'][0]
mr.inputs['From Min'].default_value = -2.2; mr.inputs['From Max'].default_value = 1.6    # liver height sits in clear light cyan
els.new(0.45).color = (0.30, 0.74, 0.98, 1)
# window backplates: clear bright sky
for name in ("Outside", "Outside2"):
    m = bpy.data.materials.get(name)
    if m:
        e = [n for n in m.node_tree.nodes if n.type == 'EMISSION'][0]
        e.inputs['Color'].default_value = (0.35, 0.72, 1.0, 1); e.inputs['Strength'].default_value = 1.6
for m in bpy.data.materials:
    if m.name.startswith("TreeSil"):
        e = [n for n in m.node_tree.nodes if n.type == 'EMISSION'][0]; e.inputs['Color'].default_value = (0.25, 0.65, 0.3, 1)

# 2. liver: clean glossy red-brown organ; the initials become a soft warm glow line (no char, no wound look)
lm = bpy.data.objects["Liver"].data.materials[0]; nt = lm.node_tree
for n in nt.nodes:
    if n.type == 'MIX' and n.data_type == 'RGBA' and tuple(round(c, 3) for c in n.inputs['B'].default_value[:3]) == (0.012, 0.006, 0.004):
        n.inputs['B'].default_value = (0.55, 0.12, 0.05, 1)          # warm glowing line colour instead of black char
    if n.type == 'MIX' and n.data_type == 'RGBA' and tuple(round(c, 2) for c in n.inputs['B'].default_value[:3]) == (0.48, 0.15, 0.11):
        n.inputs['B'].default_value = (0.62, 0.20, 0.13, 1)          # cleaner red-brown
pr = nt.nodes["Principled BSDF"]
pr.inputs['Coat Weight'].default_value = 0.6; pr.inputs['Coat Roughness'].default_value = 0.15
pr.inputs['Subsurface Weight'].default_value = 0.08
pr.inputs['Emission Color'].default_value = (1.0, 0.55, 0.2, 1)
# the ember term (sear^2 * k) becomes a steady soft glow
for n in nt.nodes:
    if n.type == 'MATH' and n.operation == 'MULTIPLY' and abs(n.inputs[1].default_value - 0.04) < 1e-6:
        n.inputs[1].default_value = 2.2
for n in nt.nodes:
    if n.type == 'BUMP':
        n.inputs['Strength'].default_value = 0.15
# ghost/x-ray livers keep their glow (already clean)

# 3. skin: no pores, smooth CG skin
for ob in [o for o in bpy.data.objects if o.name.endswith(".body")]:
    for m in ob.data.materials:
        if m and m.get("pores"):
            for n in m.node_tree.nodes:
                if n.type == 'TEX_NOISE' and n.inputs['Scale'].default_value > 1000:
                    for lk in list(n.outputs['Fac'].links):
                        if lk.to_node.type == 'BUMP':
                            lk.to_node.inputs['Strength'].default_value = 0.0
# abdomen window: clean peach skin, thin neat incision line
sk = bpy.data.materials.get("Skin_Abdomen")
if sk: sk.node_tree.nodes["Principled BSDF"].inputs['Base Color'].default_value = (0.95, 0.62, 0.48, 1)
inc = bpy.data.materials.get("Incision")
if inc: inc.node_tree.nodes["Principled BSDF"].inputs['Base Color'].default_value = (0.85, 0.25, 0.25, 1)

# 4. brighter interiors: lift the dark hearing-room panelling and the brown ceilings
for name, val in (("Hearing_Wall", 1.9), ("Ceiling", 1.3), ("Home_Wall", 1.15)):
    m = bpy.data.materials.get(name)
    if not m: continue
    for n in m.node_tree.nodes:
        if n.type == 'HUE_SAT':
            n.inputs['Value'].default_value = val
for L in bpy.data.lights:
    if L.name.startswith(("HEAR_Ceil", "HOME_Ceil")):
        L.energy *= 1.8
    if L.name.startswith("SurgLampSpot"):
        L.energy *= 0.7          # the abdomen window was blowing out

# 5. depth of field: keyed f-stops raised to >= 5.6 (macro studio stays at 8)
cam = bpy.data.cameras["CAM_Film"]
for fc in fcurves(cam):
    if "aperture_fstop" in fc.data_path:
        for kp in fc.keyframe_points:
            v = max(5.6, kp.co.y); d_ = v - kp.co.y
            kp.co.y = v; kp.handle_left.y += d_; kp.handle_right.y += d_
sc.render.use_motion_blur = False
print("ANIM_FIX_DONE")
bpy.ops.wm.save_as_mainfile(filepath=OUT)
