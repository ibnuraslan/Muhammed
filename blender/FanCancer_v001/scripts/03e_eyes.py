"""v007: MPFB EnhancedEye cornea uses refractive transmission -> eyes read as black holes (LESSONS §3).
The cornea becomes a Transparent BSDF mixed in by the old transmission value (after eye_fix.py, LegoInNose a44130b)."""
import bpy
for g in [g for g in bpy.data.node_groups if g.name.startswith("EnhancedEye")]:
    if "CorneaTransparentMix" in g.nodes: continue
    P = next((n for n in g.nodes if n.type == "BSDF_PRINCIPLED"), None); OUTN = next((n for n in g.nodes if n.type == "GROUP_OUTPUT"), None)
    if P is None or OUTN is None: continue
    tl = [l for l in g.links if l.to_node == P and l.to_socket.name == "Transmission Weight"]
    src = tl[0].from_socket if tl else None
    for l in tl: g.links.remove(l)
    P.inputs["Transmission Weight"].default_value = 0.0
    ol = [l for l in g.links if l.from_node == P and l.to_node == OUTN]
    if not ol: continue
    out_sock = ol[0].to_socket; g.links.remove(ol[0])
    tr = g.nodes.new("ShaderNodeBsdfTransparent"); mx = g.nodes.new("ShaderNodeMixShader"); mx.name = "CorneaTransparentMix"
    if src: g.links.new(src, mx.inputs[0])
    else: mx.inputs[0].default_value = 0.0
    g.links.new(P.outputs[0], mx.inputs[1]); g.links.new(tr.outputs[0], mx.inputs[2]); g.links.new(mx.outputs[0], out_sock)
    print("EYEFIX", g.name, src.node.name if src else None)

# v007: fill light on her face and torso at the glass (16-18 s); she was a dark silhouette behind the glass
from mathutils import Vector
sc = bpy.context.scene; FF = lambda t: 1 + round(60 * t)
L = bpy.data.lights.new("FanGlassFill", 'AREA'); L.energy = 0; L.size = 0.8; L.color = (1.0, 0.95, 0.9)
lo = bpy.data.objects.new("FanGlassFill", L); lo.location = (0.55, 0.12, 1.85)
lo.rotation_euler = (Vector((0.0, 0.45, 1.35)) - lo.location).to_track_quat('-Z', 'Y').to_euler()
lo.visible_camera = False; lo.visible_glossy = False; lo.visible_transmission = False; sc.collection.objects.link(lo)
for f, e in ((1, 0), (FF(15.7), 0), (FF(15.8), 60), (FF(18.2), 60), (FF(18.3), 0)):
    L.energy = e; L.keyframe_insert("energy", frame=f)
for fc in L.animation_data.action.fcurves if hasattr(L.animation_data.action, "fcurves") else []:
    for kp in fc.keyframe_points: kp.interpolation = 'CONSTANT'
# stray orange desk-lamp head in the clinic
for o in bpy.data.objects:
    if (o.name.startswith("geo_lamp") or any(sl.material and sl.material.name.startswith("desk_lamp_arm") for sl in o.material_slots)) and -40 < o.matrix_world.translation.x < -20:
        o.hide_render = True; o.hide_viewport = True; print("HIDE", o.name)
# the stool leaves the clinic frame while he posts (no blob at the bottom edge)
st = bpy.data.objects.get("metal_stool_01")
if st:
    for f, v in ((FF(29.3), False), (FF(29.35), True)):
        st.hide_render = v; st.keyframe_insert("hide_render", frame=f)
