"""5-second cut in the fast short-form style, built on the motion-test animation.

blender -b anim.blend --python 06_cut_5s.py -- <out.blend>

Source action frames 196-495 (reach -> grab -> lift -> rise -> drink) become frames 1-300.
Four camera setups switched by timeline markers (animated camera cuts the farm keeps),
whip-pans between them, and a glowing outline on the bottle as it is grabbed.
"""
import sys, math
import bpy
from mathutils import Vector

OUT = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene
OFF = 195                                   # source frame = clip frame + OFF
arm = bpy.data.objects["Farmer"]
PB = arm.pose.bones
bottle = bpy.data.objects["Bottle"]

# ------------------------------------------------------------------ shift all animation
def fcurves_of(act):
    out = []
    for layer in getattr(act, "layers", []):
        for strip in layer.strips:
            for cb in getattr(strip, "channelbags", []):
                out.extend(cb.fcurves)
    if not out and hasattr(act, "fcurves"):
        out.extend(act.fcurves)
    return out

for old in ("CAM_Main", "CAM_Aim"):
    ob = bpy.data.objects.get(old)
    if ob:
        bpy.data.objects.remove(ob, do_unlink=True)
for act in bpy.data.actions:
    for fc in fcurves_of(act):
        for kp in fc.keyframe_points:
            kp.co.x -= OFF
            kp.handle_left.x -= OFF
            kp.handle_right.x -= OFF
        fc.update()
sc.frame_start, sc.frame_end, sc.frame_step = 1, 300, 1
sc.render.filepath = "//render/Cut5s_v001_"

# ------------------------------------------------------------------ bottle highlight (inverted hull)
prof = [(0.0, 0.0), (2.9, 0.0), (3.25, 0.35), (3.35, 1.2), (3.35, 13.8), (3.2, 15.4),
        (2.6, 17.4), (1.75, 19.0), (1.35, 20.4), (1.3, 22.8), (1.48, 23.1), (1.5, 24.2),
        (1.38, 24.6), (0.0, 24.65)]
OUTL = 0.0032
verts = [((r / 100 + OUTL) if r > 0 else 0.0, 0, z / 100 + (OUTL if z > 24 else (-OUTL if z == 0 else 0)))
         for r, z in prof]
me = bpy.data.meshes.new("Bottle_Highlight")
me.from_pydata(verts, [(i, i + 1) for i in range(len(verts) - 1)], [])
hl = bpy.data.objects.new("Bottle_Highlight", me)
sc.collection.objects.link(hl)
scr = hl.modifiers.new("Lathe", 'SCREW'); scr.axis = 'Z'; scr.steps = 48; scr.render_steps = 48
scr.use_merge_vertices = True; scr.use_normal_calculate = True; scr.use_normal_flip = True
hl.parent = bottle
for attr in ("visible_shadow", "visible_diffuse", "visible_glossy", "visible_transmission",
             "visible_volume_scatter"):
    setattr(hl, attr, False)
mat = bpy.data.materials.new("M_Highlight_Outline")
mat.use_nodes = True
n, l = mat.node_tree.nodes, mat.node_tree.links
n.clear()
o = n.new('ShaderNodeOutputMaterial')
em = n.new('ShaderNodeEmission'); em.inputs['Color'].default_value = (1.0, 0.62, 0.02, 1)
em.inputs['Strength'].default_value = 0.0
tr = n.new('ShaderNodeBsdfTransparent')
geo = n.new('ShaderNodeNewGeometry'); lp = n.new('ShaderNodeLightPath')
inv = n.new('ShaderNodeMath'); inv.operation = 'SUBTRACT'; inv.inputs[0].default_value = 1.0
mx = n.new('ShaderNodeMath'); mx.operation = 'MAXIMUM'
mix = n.new('ShaderNodeMixShader')
l.new(lp.outputs['Is Camera Ray'], inv.inputs[1])
l.new(geo.outputs['Backfacing'], mx.inputs[0]); l.new(inv.outputs[0], mx.inputs[1])
l.new(mx.outputs[0], mix.inputs['Fac'])
l.new(em.outputs['Emission'], mix.inputs[1]); l.new(tr.outputs['BSDF'], mix.inputs[2])
l.new(mix.outputs['Shader'], o.inputs['Surface'])
hl.data.materials.append(mat)
# on as the fingers lock round the bottle, pulse, fade while it lifts
for f, v in ((1, 0.6), (66, 0.6), (71, 3.2), (78, 2.0), (86, 2.9), (104, 2.4), (113, 0.6)):
    em.inputs['Strength'].default_value = v
    em.inputs['Strength'].keyframe_insert("default_value", frame=f)
# fully hidden outside the highlight window (an unlit hull would read as a black rim)
for f, h in ((1, True), (66, False), (114, True)):
    hl.hide_render = h
    hl.keyframe_insert("hide_render", frame=f)
for fc in fcurves_of(hl.animation_data.action):
    for kp in fc.keyframe_points:
        kp.interpolation = 'CONSTANT'


# ------------------------------------------------------------------ subjects
def bottle_pt(h=0.11):
    return bottle.matrix_world @ Vector((0, 0, h))
def bone_pt(name, tail=False):
    pb = PB[name]
    return (pb.tail if tail else pb.head).copy()
def mouth_pt():
    return bottle.matrix_world @ Vector((0, 0, 0.24))

def smooth(x):
    return x * x * (3 - 2 * x)

# shot definitions: frames, lens, f-stop, camera(f, t) -> position, aim(f, t) -> point
def shotA(t):
    tgt = bottle_pt(0.12).lerp(bone_pt("head"), 0.35)
    cam = bottle_pt(0.0) + Vector((-0.95, -0.80, 0.30)) * (1.0 - 0.18 * smooth(t))
    return cam, tgt
def shotB(t):
    tgt = bottle_pt(0.11)
    a = math.radians(-24 + 10 * t)
    base = Vector((0.43 * math.sin(a), -0.43 * math.cos(a), 0.05))
    b0 = bpy.data.objects["Bottle"].matrix_world.translation
    cam = Vector((b0.x, b0.y, B_START.z + 0.11 + (tgt.z - B_START.z - 0.11) * 0.75)) + base
    return cam, tgt
def shotC(t):
    tgt = bone_pt("spine01").lerp(bottle_pt(0.12), 0.25)
    root = bone_pt("root")
    cam = Vector((root.x - 1.25, root.y - 1.45, 0.28 + 0.45 * smooth(t)))
    return cam, tgt
def shotD(t):
    head = bone_pt("head", tail=False)
    tgt = head.lerp(bottle_pt(0.15), 0.5)
    a = math.radians(-62)
    d = 1.35 - 0.25 * smooth(t)
    cam = head + Vector((d * math.sin(a), -d * math.cos(a), -0.02))
    return cam, tgt

SHOTS = [("CAM_A_Reach", 1, 45, 32, 4.0, shotA),
         ("CAM_B_Grab", 46, 120, 55, 2.8, shotB),
         ("CAM_C_Rise", 121, 200, 26, 5.6, shotC),
         ("CAM_D_Drink", 201, 300, 50, 2.8, shotD)]
WHIP = 6                 # frames of whip at each side of a cut
WHIP_DEG = 38

sc.frame_set(1)
B_START = bottle.matrix_world.translation.copy()
for m in list(sc.timeline_markers):
    sc.timeline_markers.remove(m)

for idx, (name, f0, f1, lens, fstop, fn) in enumerate(SHOTS):
    cd = bpy.data.cameras.new(name)
    cd.lens = lens; cd.sensor_fit = 'AUTO'; cd.sensor_width = 36; cd.clip_start = 0.02
    cd.dof.use_dof = True; cd.dof.aperture_fstop = fstop
    cam = bpy.data.objects.new(name, cd)
    sc.collection.objects.link(cam)
    aim = bpy.data.objects.new(name + "_Aim", None)
    aim.empty_display_size = 0.05
    sc.collection.objects.link(aim)
    tt = cam.constraints.new('TRACK_TO'); tt.target = aim
    tt.track_axis = 'TRACK_NEGATIVE_Z'; tt.up_axis = 'UP_Y'
    foc = bpy.data.objects.new(name + "_Focus", None)
    foc.empty_display_size = 0.03
    sc.collection.objects.link(foc)
    cd.dof.focus_object = foc
    mk = sc.timeline_markers.new(name, frame=f0)
    mk.camera = cam
    frames = sorted(set(list(range(f0, f1 + 1, 2)) + [f1]))
    for f in frames:
        sc.frame_set(f)
        t = (f - f0) / max(1, (f1 - f0))
        cpos, apos = fn(t)
        foc.location = apos
        foc.keyframe_insert("location", frame=f)
        # whip-pan: rotate the aim around the camera, out at the end, in at the start
        ang = 0.0
        if idx < len(SHOTS) - 1 and f > f1 - WHIP:
            ang = WHIP_DEG * smooth((f - (f1 - WHIP)) / WHIP)
        if idx > 0 and f < f0 + WHIP:
            ang = -WHIP_DEG * (1 - smooth((f - f0) / WHIP))
        if ang:
            v = apos - cpos
            v = v.copy()
            from mathutils import Matrix
            v = Matrix.Rotation(math.radians(-ang), 3, 'Z') @ v
            apos = cpos + v
        cam.location = cpos
        cam.keyframe_insert("location", frame=f)
        aim.location = apos
        aim.keyframe_insert("location", frame=f)
    print("SHOT", name, f0, f1)

sc.camera = bpy.data.objects[SHOTS[0][0]]
sc.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("CUT_OK")
