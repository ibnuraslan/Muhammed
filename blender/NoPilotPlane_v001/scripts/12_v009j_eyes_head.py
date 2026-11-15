"""v009j (director): (1) black-hole eyes in close-ups: the MPFB EnhancedEye cornea used refractive transmission; it is now a
Transparent BSDF mixed in by the same transmission value (Principled transmission 0), the LegoInNose eye fix
(blender/LegoInNose_v001/scripts/eye_fix.py on claude/connect03-lego-in-nose, a44130b), applied to every EnhancedEye group.
Plus a small catchlight that rides with the camera. (2) top-of-head close-ups: in the face shots his head lifts toward the
windscreen (a keyed Damped Track on the head and neck), so both eyes read.
blender -b film.blend --python 12_v009j_eyes_head.py -- out.blend"""
import bpy, sys
from mathutils import Vector
out = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene
# 1. eye fix on every EnhancedEye group
for g in [g for g in bpy.data.node_groups if g.name.startswith("EnhancedEye")]:
    if "CorneaTransparentMix" in g.nodes: continue
    P = next(n for n in g.nodes if n.type == "BSDF_PRINCIPLED"); OUTN = next(n for n in g.nodes if n.type == "GROUP_OUTPUT")
    tl = [l for l in g.links if l.to_node == P and l.to_socket.name == "Transmission Weight"]
    src = tl[0].from_socket if tl else None
    tv = P.inputs["Transmission Weight"].default_value
    for l in tl: g.links.remove(l)
    P.inputs["Transmission Weight"].default_value = 0.0
    ol = [l for l in g.links if l.from_node == P and l.to_node == OUTN][0]; out_sock = ol.to_socket; g.links.remove(ol)
    tr = g.nodes.new("ShaderNodeBsdfTransparent"); mx = g.nodes.new("ShaderNodeMixShader"); mx.name = "CorneaTransparentMix"
    if src: g.links.new(src, mx.inputs[0])
    else: mx.inputs[0].default_value = tv
    g.links.new(P.outputs[0], mx.inputs[1]); g.links.new(tr.outputs[0], mx.inputs[2]); g.links.new(mx.outputs[0], out_sock)
    print("EYEFIX", g.name, "transmission source", src.node.name if src else tv)
# catchlight: a small, weak point light just above the lens
CAM = sc.camera
ld = bpy.data.lights.new("L_catch", "POINT"); ld.energy = 1.5; ld.shadow_soft_size = 0.015; ld.use_shadow = False
L = bpy.data.objects.new("L_catch", ld); sc.collection.objects.link(L)
L.parent = CAM; L.location = (0.0, 0.06, 0.0)
L.visible_camera = False
# 2. head lift in the face close-ups (film frames, target point)
YOU = bpy.data.objects["YOU"]
LIFT = [(546, 620, (0.0, 1.30, 1.60)), (951, 990, (0.15, 2.60, 1.60)), (1153, 1224, (0.15, 2.60, 1.60)), (2959, 3018, (-0.30, 2.60, 1.35))]
B = YOU.data.bones["head"]; R = (YOU.matrix_world.to_3x3() @ B.matrix_local.to_3x3())
fwd = Vector((0, -1, 0))                                  # MPFB rest pose faces -Y
axes = {"TRACK_X": Vector((1, 0, 0)), "TRACK_NEGATIVE_X": Vector((-1, 0, 0)), "TRACK_Y": Vector((0, 1, 0)),
        "TRACK_NEGATIVE_Y": Vector((0, -1, 0)), "TRACK_Z": Vector((0, 0, 1)), "TRACK_NEGATIVE_Z": Vector((0, 0, -1))}
ax = max(axes, key=lambda k: (R @ axes[k]).normalized().dot(fwd))
print("HEADLIFT track axis", ax)
for (a, b, tgt) in LIFT:
    e = bpy.data.objects.new("LOOK_%d" % a, None); e.location = tgt; sc.collection.objects.link(e)
    for bone, w in (("head", 0.8), ("neck02", 0.35)):
        c = YOU.pose.bones[bone].constraints.new("DAMPED_TRACK"); c.name = "lift_%d" % a
        c.target = e; c.track_axis = ax
        for f, v in ((a - 10, 0.0), (a, w), (b, w), (b + 10, 0.0)):
            c.influence = v; c.keyframe_insert("influence", frame=f)
        c.influence = 0.0; c.keyframe_insert("influence", frame=1)
bpy.ops.wm.save_as_mainfile(filepath=out, compress=True)
print("V9J saved", out)
