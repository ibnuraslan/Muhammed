"""Hand fixes after pipeline/anim_look.py (animated-CG look, client 22:45 UTC).
blender -b work/film_anim.blend --python scripts/06_anim_fix.py -- work/film_anim2.blend"""
import sys, bpy
out = sys.argv[sys.argv.index("--") + 1]
def hexc(h):
    h = h.lstrip("#"); c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(((x + 0.055) / 1.055) ** 2.4 if x > 0.04045 else x / 12.92 for x in c) + (1.0,)
# cross-section card: bright sky-blue gradient (cyan top -> near-white bottom), self-lit so it stays clean
m = bpy.data.materials["M_backdrop"]; nt = m.node_tree
cr = [n for n in nt.nodes if n.type == "VALTORGB"][0]; gr = [n for n in nt.nodes if n.type == "TEX_GRADIENT"][0]
mp = [n for n in nt.nodes if n.type == "MAPPING"][0]; tc = [n for n in nt.nodes if n.type == "TEX_COORD"][0]
gr.gradient_type = "LINEAR"; mp.inputs["Scale"].default_value = (1, 1, 1)
for l in list(mp.inputs[0].links): nt.links.remove(l)
nt.links.new(tc.outputs["Generated"], mp.inputs[0])
cr.color_ramp.elements[0].color = hexc("#4FC3F7"); cr.color_ramp.elements[1].color = hexc("#E8F7FF")
for l in list(cr.inputs[0].links): nt.links.remove(l)
nt.links.new(gr.outputs[0], cr.inputs[0])
df = [n for n in nt.nodes if n.type == "BSDF_DIFFUSE"][0]; mx = nt.nodes["fade"]
em = nt.nodes.new("ShaderNodeEmission"); em.inputs["Strength"].default_value = 2.6
nt.links.new(cr.outputs[0], em.inputs[0]); nt.links.new(em.outputs[0], mx.inputs[1])
# cleaner, brighter booklet/artbook pages; brighter studio key on the section
for mn, col in (("M_manual_page", (0.88, 0.84, 0.74)), ("M_artbook_pages", (0.86, 0.82, 0.72)), ("M_manual_page_print", (0.35, 0.62, 0.95))):
    for nm in (mn, mn + "_xp"):
        mm = bpy.data.materials.get(nm)
        if mm:
            b = [n for n in mm.node_tree.nodes if n.type == "BSDF_PRINCIPLED"][0]; b.inputs["Base Color"].default_value = col + (1,)
kl = bpy.data.lights["L_cutaway_key"]
for fc in kl.animation_data.action.layers[0].strips[0].channelbags[0].fcurves if kl.animation_data else []:
    for kp in fc.keyframe_points:
        if kp.co.y > 0: kp.co.y = 14.0
# our house: clean light-blue painted siding instead of the dark weathered look
sid = bpy.data.materials.get("M_siding_blue")
if sid:
    mix = [n for n in sid.node_tree.nodes if n.type == "MIX"][0]; mix.inputs[7].default_value = (1.9, 2.3, 2.9, 1)
# high-key: a little more exposure overall, brighter bedroom fill and walls
bpy.context.scene.view_settings.exposure = 0.35
for ln, k in (("L_fill", 1.6), ("L_window_bounce", 1.5), ("L_monitor", 1.3)):
    l = bpy.data.lights.get(ln)
    if l: l.energy *= k
rw = bpy.data.materials.get("M_room_wall")
if rw:
    mix = [n for n in rw.node_tree.nodes if n.type == "MIX"][0]; mix.inputs[7].default_value = (0.62, 0.72, 0.92, 1)
bpy.ops.wm.save_as_mainfile(filepath=out)
print("ANIMFIX_DONE")
