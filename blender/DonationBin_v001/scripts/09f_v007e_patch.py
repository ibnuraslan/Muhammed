"""DonationBin v007e patch, applied to the v007d package (director review of 971ada3).
blender -b DonationBin_v007d_60fps.blend --python 09f_v007e_patch.py -- out.blend
1. Black-hole eye: the MPFB EnhancedEye shader (glass cornea over the eyeball) renders black/pink in Cycles here. Every
   character's eye gets a simple opaque eye: white, brown iris, dark pupil, glossy coat. The iris is painted from each
   eyeball's own forward direction (a per-vertex attribute), so it follows the gaze bones. A tiny catchlight rides with
   the camera (not visible to the camera).
2. 1561-1860: four shots (~1.5 s) at three-quarter angles (both eyes read), camera rolled with her head, with a head
   turn up to the grate; the camera keeps 28 cm clear of everything (no blurred tarp/bag slabs at the lens).
3. 1897-1935: the push on the passer-by stops; a steady front-left shot keeps his whole head in frame.
4. (dropped) moving her back from the grate."""
import sys, math
import bpy
from mathutils import Vector, Matrix, Quaternion
OUT = sys.argv[sys.argv.index("--") + 1]
_src = open("/home/user/Muhammed/blender/DonationBin_v001/scripts/09e_v007d_roll.py").read()
_helpers = _src[:_src.index("\nA1 = (0, 20, -20")]
_helpers = _helpers.replace("OUT = sys.argv[sys.argv.index(\"--\") + 1]", "")
exec(_helpers)
# ---- 1. eyes
import bpy
from mathutils import Vector
def eye_attr(o):
    me = o.data
    if "irisdot" in me.color_attributes: me.color_attributes.remove(me.color_attributes["irisdot"])
    ca = me.color_attributes.new("irisdot", 'FLOAT_COLOR', 'POINT')
    for s in (1, -1):
        idx = [v.index for v in me.vertices if v.co.x * s > 0]
        c = sum((me.vertices[i].co for i in idx), Vector()) / len(idx)
        for i in idx:
            d = (me.vertices[i].co - c).normalized().dot(Vector((0, -1, 0)))
            ca.data[i].color = (max(0.0, d), 0, 0, 1)
def simple_eye(m):
    nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial"); bs = nt.nodes.new("ShaderNodeBsdfPrincipled")
    at = nt.nodes.new("ShaderNodeAttribute"); at.attribute_name = "irisdot"; at.attribute_type = 'GEOMETRY'
    sep = nt.nodes.new("ShaderNodeSeparateColor")
    ramp = nt.nodes.new("ShaderNodeValToRGB"); cr = ramp.color_ramp; cr.interpolation = 'LINEAR'
    cr.elements[0].position = 0.0; cr.elements[0].color = (0.85, 0.83, 0.80, 1)
    cr.elements[1].position = 1.0; cr.elements[1].color = (0.01, 0.01, 0.01, 1)
    for pos, col in ((0.78, (0.85, 0.83, 0.80, 1)), (0.80, (0.30, 0.19, 0.09, 1)), (0.935, (0.22, 0.13, 0.06, 1)), (0.95, (0.02, 0.015, 0.01, 1))):
        e = cr.elements.new(pos); e.color = col
    nt.links.new(at.outputs["Color"], sep.inputs[0]); nt.links.new(sep.outputs[0], ramp.inputs[0])
    nt.links.new(ramp.outputs[0], bs.inputs["Base Color"])
    bs.inputs["Roughness"].default_value = 0.35
    bs.inputs["Coat Weight"].default_value = 1.0; bs.inputs["Coat Roughness"].default_value = 0.02
    nt.links.new(bs.outputs[0], out.inputs[0])
    m.surface_render_method = 'DITHERED'
def fix_all_eyes():
    n = 0
    for o in bpy.data.objects:
        if o.type == 'MESH' and o.name.endswith(".high-poly"):
            eye_attr(o)
            for m in o.data.materials:
                if m and m.use_nodes and m.node_tree.nodes.get("EnhancedEye"): simple_eye(m); n += 1
    return n

ne = fix_all_eyes()
print("EYES_FIXED", ne)
cl = bpy.data.lights.new("CamCatch", 'POINT'); cl.energy = 1.5; cl.shadow_soft_size = 0.01; cl.color = (1.0, 0.96, 0.9)
clo = bpy.data.objects.new("CamCatch", cl); sc.collection.objects.link(clo)
clo.parent = cam; clo.location = (0.05, 0.06, 0.0); clo.visible_camera = False
print("CATCHLIGHT")
# (4. pulling her back from the grate was dropped: rigid key shifts interleaved with the dense existing keys and made her jitter)
# ---- 2. head turn up to the grate (1660-1730) on top of the breathing
for f in (1652, 1738):
    sc.frame_set(f); WO.pose.bones["head"].keyframe_insert("rotation_quaternion", frame=f, group="head")
for f, deg in ((1675, -14), (1700, -22), (1720, -12)):
    sc.frame_set(f); pb = WO.pose.bones["head"]
    pb.rotation_quaternion = pb.rotation_quaternion @ Quaternion(Vector((1, 0, 0)), math.radians(deg))
    pb.keyframe_insert("rotation_quaternion", frame=f, group="head")
print("HEAD_TURN")
_air = air
def air(c, r=0.28): return _air(c, r)
cuts = [1561, 1651, 1741, 1801, 1861]
for i, (a_, b_) in enumerate(zip(cuts, cuts[1:])):
    angs = (35, 30, 40, 25, 45, 20, 50) if i % 2 == 0 else (-35, -30, -40, -25, -45, -20, -50)
    ok = face_shot(a_, b_ - 1, angs, (0.62, 0.56, 0.50, 0.45), ups=(0.0, 0.06, 0.12, -0.04, 0.20), lens=34, push=0.04,
                   roll=True, aim=Vector(), name="days34_%d" % i)
    if not ok:
        face_shot(a_, b_ - 1, tuple(-x for x in angs) + (0, 10, -10), (0.62, 0.56, 0.50, 0.45), ups=(0.0, 0.06, 0.12, -0.04, 0.20),
                  lens=34, push=0.04, roll=True, aim=Vector(), name="days34b_%d" % i)
# ---- 3. 1897-1935: steady front-left on the passer-by
PB = bpy.data.objects["Passerby"]
tp = smooth_face(PB, 1897, 1935)
fixed_shot(1897, 1935, (-0.45, -2.45, 1.62), (0.5, -1.1, 1.5), lens=30, track=lambda f: tp[f] + Vector((0, 0, -0.08)), name="passerby steady")
for f, (p, q, ln) in sorted(NEW.items()):
    cam.location = p; cam.keyframe_insert("location", frame=f)
    cam.rotation_mode = 'QUATERNION'
    q0 = cam.rotation_quaternion.copy()
    cam.rotation_quaternion = q if q.dot(q0) >= 0 else -q; cam.keyframe_insert("rotation_quaternion", frame=f)
    cd.lens = ln; cd.keyframe_insert("lens", frame=f)
sc["director_fix"] = "v007e: eyes (clear cornea + catchlight), 1.5 s three-quarter shots in the three days, steady passer-by, back from the grate"
sc.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print("V007E_DONE", len(NEW))
