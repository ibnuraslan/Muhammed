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

# v008: his face lit by the phone screen while he posts
_scr = bpy.data.objects.get("ManPhone_screenB") or bpy.data.objects.get("ManPhone_screen")
if _scr:
    L = bpy.data.lights.new("PhoneGlow", 'POINT'); L.energy = 0; L.color = (0.75, 0.85, 1.0); L.shadow_soft_size = 0.03
    lo = bpy.data.objects.new("PhoneGlow", L); sc.collection.objects.link(lo); lo.parent = _scr; lo.location = (0, 0, 0.06)
    lo.visible_camera = False
    for f, e in ((1, 0), (FF(30.4), 0), (FF(30.7), 4.0), (FF(33.4), 4.0), (FF(33.45), 0)):
        L.energy = e; L.keyframe_insert("energy", frame=f)
# v008: phone-screen insert (33.4-34.6 s): a blank social post with a photo of her at the glass and pulsing share icons, no text
import os, math
INS = Vector((-300.0, -200.0, 1.0)); C_INS = bpy.data.collections.new("INSERT"); sc.collection.children.link(C_INS)
def _em(name, rgb, strength=1.0, img=None):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    o = nt.nodes.new("ShaderNodeOutputMaterial"); e = nt.nodes.new("ShaderNodeEmission"); e.inputs["Strength"].default_value = strength
    if img:
        t = nt.nodes.new("ShaderNodeTexImage"); t.image = img; nt.links.new(t.outputs[0], e.inputs[0])
    else: e.inputs[0].default_value = (*rgb, 1)
    nt.links.new(e.outputs[0], o.inputs[0]); return m
def _card(name, w, h, x, z, m, y=0.0, circle=False):
    if circle: bpy.ops.mesh.primitive_circle_add(vertices=32, radius=w / 2, fill_type='NGON')
    else: bpy.ops.mesh.primitive_plane_add(size=1); bpy.context.object.scale = (w, h, 1)
    o = bpy.context.object; o.name = name
    for c in list(o.users_collection): c.objects.unlink(o)
    C_INS.objects.link(o); o.rotation_euler = (math.radians(90), 0, 0); o.location = INS + Vector((x, y, z)); o.data.materials.append(m); return o
_card("InsBezel", 0.66, 1.17, 0, 0, _em("InsBezel", (0.02, 0.02, 0.025)), y=0.004)
_card("InsBG", 0.60, 1.07, 0, 0, _em("InsBG", (0.96, 0.96, 0.97)))
_card("InsHeader", 0.60, 0.07, 0, 0.50, _em("InsHeader", (0.20, 0.42, 0.85)), y=-0.001)
_card("InsAvatar", 0.08, 0.08, -0.22, 0.38, _em("InsAvatar", (0.45, 0.60, 0.80)), y=-0.001, circle=True)
for i_, (w_, z_) in enumerate(((0.30, 0.395), (0.22, 0.355), (0.48, 0.30), (0.40, 0.265))):
    _card(f"InsLine{i_}", w_, 0.018, -0.24 + w_ / 2 + (0.06 if i_ < 2 else -0.02), z_, _em(f"InsLine{i_}", (0.72, 0.73, 0.76)), y=-0.001)
_img = bpy.data.images.load(os.path.join(D, "..", "assets_thumb_glass.jpg"))
_card("InsPhoto", 0.52, 0.52, 0, -0.02, _em("InsPhoto", None, 1.0, _img), y=-0.001)
for i_, (x_, col) in enumerate(((-0.17, (0.90, 0.20, 0.30)), (0.0, (0.25, 0.50, 0.95)), (0.17, (0.30, 0.75, 0.40)))):
    ic = _card(f"InsIcon{i_}", 0.07, 0.07, x_, -0.36, _em(f"InsIcon{i_}", col, 1.2), y=-0.002, circle=True)
    for k_ in range(0, 9):
        t_ = 33.4 + 0.15 * k_ + 0.05 * i_; s_ = 1.0 + 0.35 * (k_ % 2)
        ic.scale = (s_, s_, s_); ic.keyframe_insert("scale", frame=FF(t_))
# share bar that fills as the story spreads
bar = _card("InsShareBar", 0.48, 0.02, 0, -0.44, _em("InsShareBar", (0.25, 0.50, 0.95)), y=-0.002)
_card("InsShareTrack", 0.48, 0.02, 0, -0.44, _em("InsShareTrack", (0.85, 0.86, 0.88)), y=-0.001)
for f, sx in ((FF(33.4), 0.05), (FF(34.6), 1.0)):
    bar.scale = (0.48 * sx, 0.02, 1); bar.location.x = INS.x - 0.24 + 0.24 * sx; bar.keyframe_insert("scale", frame=f); bar.keyframe_insert("location", frame=f)
print("INSERT_OK")
