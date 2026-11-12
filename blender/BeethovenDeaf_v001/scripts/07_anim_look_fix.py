"""After pipeline/anim_look.py: hand-tune BeethovenDeaf to the bright animated look (client, Nov 11 22:45).
blender -b looked.blend --python 07_anim_look_fix.py -- <out.blend>"""
import sys, bpy
from mathutils import Vector
OUT = sys.argv[sys.argv.index("--") + 1]; sc = bpy.context.scene
# 1. X-ray backdrop -> sky gradient: cyan #4FC3F7 at the top to near-white #E8F7FF at the bottom
m = bpy.data.materials["M_StudioBackdrop"]; nt = m.node_tree
cr = next(n for n in nt.nodes if n.type == 'VALTORGB'); e = cr.color_ramp.elements
while len(e) > 2: e.remove(e[-1])
cr.color_ramp.interpolation = 'LINEAR'
e[0].position = 0.2; e[0].color = (0.22, 0.66, 1.0, 1); e[1].position = 0.68; e[1].color = (0.0, 0.36, 1.0, 1)   # #4FC3F7 -> #E8F7FF, pre-compensated for AgX desaturation
next(n for n in nt.nodes if n.type == 'EMISSION').inputs['Strength'].default_value = 1.0
# the fully ghosted body stacks >16 transparent layers and greys the backdrop: hide it while it is invisible anyway (f640-1125)
C = bpy.data.objects["Composer"]
for o in [o for o in bpy.data.objects if o.parent == C and o.type == 'MESH']:
    for f, v in ((1, False), (640, True), (1150, False)): o.hide_render = v; o.keyframe_insert("hide_render", frame=f)
# rings + pulses: saturated so they read on the light backdrop
for nm, col, st in (("M_RingCyan", (0.0, 0.5, 1.0), 2.5), ("M_PulseRed", (1.0, 0.05, 0.03), 10.0)):
    em = bpy.data.materials[nm].node_tree.nodes["Emit"]; em.inputs['Color'].default_value = (*col, 1); em.inputs['Strength'].default_value = st
# skull veil over the ear macros: nearly clear there (was 0.86)
sk = bpy.data.materials[bpy.data.objects["XRay_Skull"].data.materials[0].name].node_tree
for fc in sk.animation_data.action.layers[0].strips[0].channelbags[0].fcurves:
    if 'SkullAlpha' in fc.data_path:
        for kp in fc.keyframe_points:
            if abs(kp.co.y - 0.86) < 1e-3: kp.co.y = 0.97; kp.handle_left.y = 0.97; kp.handle_right.y = 0.97
        fc.update()
# 2. warm but bright, readable room (high key, lifted shadows)
sc.view_settings.exposure = 0.25; sc.cycles.transparent_max_bounces = 32
L = bpy.data.objects["Warm_Fill"].data; L.energy = 420; L.size = 4.5
bpy.data.objects["Rim_Back"].data.energy = 160
bpy.data.objects["Moon_Window"].data.energy = 300
for o in bpy.data.objects:
    if o.type == 'LIGHT' and o.name.startswith("CandleLight") and o.data.animation_data and o.data.animation_data.action:
        for fc in o.data.animation_data.action.layers[0].strips[0].channelbags[0].fcurves:
            for kp in fc.keyframe_points: kp.co.y *= 1.6; kp.handle_left.y *= 1.6; kp.handle_right.y *= 1.6
ld = bpy.data.lights.new("Room_Fill_HighKey", 'AREA'); ld.energy = 520; ld.size = 5.0; ld.color = (1.0, 0.9, 0.78)
F = bpy.data.objects.new("Room_Fill_HighKey", ld); sc.collection.objects.link(F); F.location = (-1.2, -1.6, 3.6)
F.rotation_euler = (Vector((0, 0.2, 0.9)) - F.location).to_track_quat('-Z', 'Y').to_euler()
F.visible_camera = False
bpy.data.objects["Face_Fill"].data.energy = 6.0
w = sc.world.node_tree.nodes.get("RoomBG")
if w: w.inputs['Strength'].default_value = max(w.inputs['Strength'].default_value, 0.25)
# the fill light must not light the inside of the studio sphere: off while the x-ray backdrop is up (it is outside the sphere anyway)
# 3. animated f-stop: never below 5.6 (macro keys at 8-11 stay)
cd = sc.camera.data
for fc in cd.animation_data.action.layers[0].strips[0].channelbags[0].fcurves:
    if "aperture_fstop" in fc.data_path:
        for kp in fc.keyframe_points:
            kp.co.y = max(kp.co.y, 5.6); kp.handle_left.y = max(kp.handle_left.y, 5.6); kp.handle_right.y = max(kp.handle_right.y, 5.6)
# 4. skin: smooth, clean (lower the skin normal/bump further), slightly warmer peach
for mat in bpy.data.materials:
    if mat.name.startswith("Composer.body") and mat.node_tree:
        for n in mat.node_tree.nodes:
            if n.type in ('NORMAL_MAP', 'BUMP'): n.inputs['Strength'].default_value *= 0.5
# 5. anatomy colour coding: cream bone, colour-coded clean parts
P = next(n for n in bpy.data.materials["M_EardrumTorn"].node_tree.nodes if n.type == 'BSDF_PRINCIPLED'); P.inputs['Roughness'].default_value = 0.45
# 6. eyes: MPFB's procedural eye group renders black with this light-path setup -> clean animated eye shader
#    (sclera / brown iris / pupil from a baked 'faces forward' attribute on the rest-pose eyeballs; glossy coat for life)
eye = bpy.data.objects["Composer.high-poly"]; me = eye.data
cent = {}
for side in (1, -1):
    vs = [v.co for v in me.vertices if v.co.x * side > 0]; cent[side] = sum(vs, Vector()) / len(vs)
at = me.attributes.get("EyeFront") or me.attributes.new("EyeFront", 'FLOAT', 'POINT')
for v in me.vertices:
    c = cent[1 if v.co.x > 0 else -1]; at.data[v.index].value = (v.co - c).normalized().dot(Vector((0, -1, 0)))
em = me.materials[0]; nt = em.node_tree; outn = next(n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL')
mix = outn.inputs['Surface'].links[0].from_node      # x-ray ghost mix: replace its 'opaque' input
an = nt.nodes.new('ShaderNodeAttribute'); an.attribute_name = "EyeFront"
cr = nt.nodes.new('ShaderNodeValToRGB'); e = cr.color_ramp.elements
e[0].position = 0.80; e[0].color = (0.80, 0.77, 0.72, 1); e[1].position = 0.975; e[1].color = (0.01, 0.008, 0.006, 1)
e.new(0.83).color = (0.26, 0.14, 0.06, 1); e.new(0.955).color = (0.12, 0.06, 0.025, 1)
nt.links.new(an.outputs['Fac'], cr.inputs['Fac'])
pb = nt.nodes.new('ShaderNodeBsdfPrincipled'); pb.inputs['Roughness'].default_value = 0.35; pb.inputs['Coat Weight'].default_value = 1.0; pb.inputs['Coat Roughness'].default_value = 0.03
nt.links.new(cr.outputs['Color'], pb.inputs['Base Color'])
nt.links.new(pb.outputs[0], mix.inputs[1])
eye.visible_shadow = False
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True); print("LOOKFIX_DONE")
