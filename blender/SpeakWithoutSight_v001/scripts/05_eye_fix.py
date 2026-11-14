"""Copied from LegoInNose_v001 (Connect03, a44130b) per LESSONS_LEARNED section 3.
v008f: eyes rendered as black holes in dim/close shots. MPFB's EnhancedEye cornea uses refractive transmission over the iris;
with refractive caustics off (the Cycles default) almost no light reaches the iris through it. The cornea is now a straight
Transparent BSDF mixed in by the same transmission value (Principled transmission 0), so light reaches the iris and sclera.
blender -b in.blend --python eye_fix.py -- out.blend   (also exec-able: set _NO_SAVE = True)"""
import bpy, sys
g = bpy.data.node_groups["EnhancedEye"]; nt = g
P = next(n for n in g.nodes if n.type == "BSDF_PRINCIPLED"); OUTN = next(n for n in g.nodes if n.type == "GROUP_OUTPUT")
tl = [l for l in g.links if l.to_node == P and l.to_socket.name == "Transmission Weight"]
src = tl[0].from_socket if tl else None
for l in tl: g.links.remove(l)
P.inputs["Transmission Weight"].default_value = 0.0
ol = [l for l in g.links if l.from_node == P and l.to_node == OUTN][0]; out_sock = ol.to_socket; g.links.remove(ol)
tr = g.nodes.new("ShaderNodeBsdfTransparent"); mx = g.nodes.new("ShaderNodeMixShader"); mx.name = "CorneaTransparentMix"
if src: g.links.new(src, mx.inputs[0])
else: mx.inputs[0].default_value = 0.0
g.links.new(P.outputs[0], mx.inputs[1]); g.links.new(tr.outputs[0], mx.inputs[2]); g.links.new(mx.outputs[0], out_sock)
print("EYEFIX done, transmission source:", src.node.name if src else None)
if not globals().get("_NO_SAVE"):
    bpy.ops.wm.save_as_mainfile(filepath=sys.argv[sys.argv.index("--") + 1], compress=True)
