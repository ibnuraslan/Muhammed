"""Client look change (animated CG) + hands rule, applied on top of the animation.
blender -b anim.blend --python 06_finish.py -- <repo_root> <out.blend>"""
import sys, os, math, bpy
from mathutils import Quaternion
a = sys.argv[sys.argv.index("--") + 1:]; ROOT, OUT = a[0], a[1]
sc = bpy.context.scene
R_ = math.radians
# 1. studio look pass (sky gradient for camera rays, AgX Punchy, saturation, softer bump, f/5.6+, no motion blur)
sys.argv = [sys.argv[0], "--", "--sat", "1.25", "--bump", "0.4"]
exec(open(os.path.join(ROOT, "blender", "pipeline", "anim_look.py")).read())
# 2. cross-section on the bright sky-blue gradient: studio dome cyan (top) -> near white (bottom), light floor
dm = bpy.data.materials["M_StudioDome"]; rp = next(n for n in dm.node_tree.nodes if n.type == 'VALTORGB')
rp.color_ramp.elements[0].color = (0.80, 0.93, 1.0, 1); rp.color_ramp.elements[1].color = (0.08, 0.55, 0.93, 1)
next(n for n in dm.node_tree.nodes if n.type == 'EMISSION').inputs['Strength'].default_value = 1.0
fl = bpy.data.materials["M_StudioFloor"].node_tree.nodes["Principled BSDF"]; fl.inputs['Base Color'].default_value = (0.75, 0.88, 0.97, 1)
for nm in ("S3_Key", "S3_Rim"): bpy.data.objects[nm].data.energy *= 1.6
bpy.data.materials["M_SumpWater"].node_tree.nodes["Principled BSDF"].inputs['Base Color'].default_value = (0.02, 0.25, 0.75, 1)
# 3. caves lit like animation: head torches + a soft blue fill so faces and rock read
f4 = bpy.data.objects["S4_Fill"]; f4.data.color = (0.62, 0.78, 1.0); f4.data.size = 9
ad = f4.data.animation_data
for fc in ad.action.layers[0].strips[0].channelbags[0].fcurves:
    for kp in fc.keyframe_points: kp.co.y *= 3.5; kp.handle_left.y *= 3.5; kp.handle_right.y *= 3.5
for o in bpy.data.objects:
    if o.name.startswith("S5_Ambient_"): o.data.energy = 45; o.data.color = (0.5, 0.75, 1.0)
cf = bpy.data.objects["CAM_Fill"]; cf.data.color = (0.65, 0.8, 1.0)
for fc in cf.data.animation_data.action.layers[0].strips[0].channelbags[0].fcurves:
    for kp in fc.keyframe_points: kp.co.y *= 3.0; kp.handle_left.y *= 3.0; kp.handle_right.y *= 3.0
TUN = [tuple(p) for p in sc["TUN"]]
for i, p in enumerate(TUN[1:6]):
    L = bpy.data.objects.new("S2_BlueFill_%d" % i, bpy.data.lights.new("S2_BlueFill_%d" % i, 'POINT'))
    L.data.energy = 60; L.data.color = (0.55, 0.72, 1.0); L.data.shadow_soft_size = 1.2; L.location = (p[0], p[1], p[2] + 2.6)
    L.visible_volume_scatter = False; sc.collection.objects.link(L)
if sc.animation_data: sc.animation_data_clear()
for f, e in ((1, 0.0), (300, 0.0), (330, 1.3), (580, 1.3), (583, 0.0), (1008, 0.0), (1009, 1.4), (1212, 1.4), (1240, 1.6), (1700, 1.6), (1840, 1.4),
             (2430, 1.4), (2470, 1.6), (2565, 1.6), (2566, 0.0), (2726, 0.0), (2727, 1.0), (2800, 0.0), (3090, 0.0)):
    sc.view_settings.exposure = e; sc.view_settings.keyframe_insert("exposure", frame=f)
# 4. divers in black neoprene (worksuit recoloured to smooth rubber), no grime
for o in bpy.data.objects:
    if o.type == 'MESH' and o.name.split(".")[-1] == "male_worksuit01":
        for m in o.data.materials:
            p = m.node_tree.nodes.get("Principled BSDF") or next((n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)
            if p:
                for lk in list(p.inputs['Base Color'].links): m.node_tree.links.remove(lk)
                p.inputs['Base Color'].default_value = (0.012, 0.014, 0.018, 1); p.inputs['Roughness'].default_value = 0.38
                if 'Coat Weight' in p.inputs: p.inputs['Coat Weight'].default_value = 0.3
bpy.data.materials["M_Tank"].node_tree.nodes["Principled BSDF"].inputs['Base Color'].default_value = (0.85, 0.65, 0.05, 1)
# 5. hands: Limit Rotation (local) on fingers, thumb and wrist; relaxed curl where a rig has no finger keys
for r in [o for o in bpy.data.objects if o.type == 'ARMATURE']:
    keyed = r.animation_data and r.animation_data.action and any(
        '"finger' in fc.data_path for fc in r.animation_data.action.layers[0].strips[0].channelbags[0].fcurves)
    for pb in r.pose.bones:
        n = pb.name
        if n.startswith("finger") and any(c_.name == "HandLimit" for c_ in pb.constraints):
            continue                       # shared hand_poses limits already on this rig
        if n.startswith("wrist.") and any(c_.name == "HandLimit" for c_ in pb.constraints):
            continue
        if n.startswith("finger"):
            thumb = n.startswith("finger1")
            c = pb.constraints.new('LIMIT_ROTATION'); c.owner_space = 'LOCAL'
            c.use_limit_x = c.use_limit_y = c.use_limit_z = True
            c.min_x, c.max_x = (R_(-15), R_(60)) if thumb else (R_(0), R_(90))
            c.min_y, c.max_y = R_(-20 if thumb else -5), R_(20 if thumb else 5)
            c.min_z, c.max_z = R_(-25 if thumb else -10), R_(25 if thumb else 10)
            if not keyed:
                pb.rotation_mode = 'QUATERNION'; pb.rotation_quaternion = Quaternion((1, 0, 0), R_(25 * (0.4 if thumb else 1.0)))
        elif n.startswith("wrist."):
            c = pb.constraints.new('LIMIT_ROTATION'); c.owner_space = 'LOCAL'
            c.use_limit_x = c.use_limit_z = True; c.min_x, c.max_x = R_(-60), R_(60); c.min_z, c.max_z = R_(-25), R_(25)
# 6. rock blackouts: at most 4 black frames, rock texture on the way in and out
wv = bpy.data.materials["M_RockWipe"].node_tree.nodes["Wipe"].outputs[0]
wv_fc = None
mw = bpy.data.materials["M_RockWipe"]
if mw.node_tree.animation_data: mw.node_tree.animation_data_clear()
wv.default_value = 0.0; wv.keyframe_insert("default_value", frame=1)
for J in (582, 1008, 2565, 2726):
    for f, v in ((J - 7, 0.0), (J - 1, 1.0), (J + 2, 1.0), (J + 8, 0.0)):
        wv.default_value = v; wv.keyframe_insert("default_value", frame=f)
sc["finish"] = "anim_look + cave fill + wetsuits + hand limits + 4-frame wipes"
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("FINISH_OK")
