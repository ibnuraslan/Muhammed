"""Animated-CG look (STYLE_ANIMATED.md) + hands pass.  blender -b work/film.blend --python scripts/05_look_hands.py -- work/final.blend"""
import sys, os, math, bpy
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_PATH = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene; O = bpy.data.objects
# 1. studio tool (camera sky handled by us: the story is a night drive -> readable blue night, see below)
sys.argv = [sys.argv[0], "--", "--no-sky", "--sat", "1.25", "--bump", "0.35"]
exec(open(os.path.join(HERE, "..", "pipeline", "anim_look.py")).read())
sys.argv = ["x", "--", OUT_PATH]
# 2. readable blue night for camera rays (faces lit, nothing murky)
WN = sc.world.node_tree.nodes
ramp = next(n for n in WN if n.type == "VALTORGB")
ramp.color_ramp.elements[0].color = (0.12, 0.28, 0.75, 1); ramp.color_ramp.elements[0].position = 0.47   # horizon: city-glow blue
ramp.color_ramp.elements[1].color = (0.02, 0.07, 0.38, 1); ramp.color_ramp.elements[1].position = 0.70  # zenith: deep cobalt
WN["WorldBG"].inputs[1].default_value = 0.9
# brighter, cleaner cabin key + fill on the face (blue-tinted night, faces readable)
for n, e in (("Key_Dash", 14.0), ("Fill_Instrument", 5.0), ("Rim_Window", 10.0)):
    O[n].data.energy = e
fl = bpy.data.lights.new("FaceFill_Soft", "AREA"); fl.energy = 9.0; fl.size = 0.6; fl.color = (0.75, 0.85, 1.0)
fo = O.new("FaceFill_Soft", fl); bpy.data.collections["CabinFX"].objects.link(fo); fo.location = (-0.35, -0.75, 1.35)
fo.rotation_euler = (Vector((0, -0.13, 1.28)) - fo.location).to_track_quat("-Z", "Y").to_euler()
# extra soft fills: over-the-shoulder cabin fill and the HUD/console area (director, 00:41)
for nm, loc, aim, e, sz, col in (("CabinFill_Rear", (-0.45, 0.55, 1.30), (0.0, -0.3, 1.05), 18.0, 0.8, (0.85, 0.9, 1.0)),
                                 ("HUD_Fill", (-0.20, -0.40, 1.28), (-0.37, -0.68, 0.95), 7.0, 0.4, (0.9, 0.92, 1.0))):
    L_ = bpy.data.lights.new(nm, "AREA"); L_.energy = e; L_.size = sz; L_.color = col
    o_ = O.new(nm, L_); bpy.data.collections["CabinFX"].objects.link(o_); o_.location = loc
    o_.rotation_euler = (Vector(aim) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
# 3. cutaway on the bright sky-blue gradient (cyan #4FC3F7 top -> #E8F7FF bottom)
bgm = bpy.data.materials["Sec_BackdropGrad"]; cr = next(n for n in bgm.node_tree.nodes if n.type == "VALTORGB")
cr.color_ramp.elements[0].color = (0.80, 0.93, 1.0, 1); cr.color_ramp.elements[0].position = 0.30
cr.color_ramp.elements[1].color = (0.08, 0.55, 0.93, 1); cr.color_ramp.elements[1].position = 0.55
next(n for n in bgm.node_tree.nodes if n.type == "EMISSION").inputs[1].default_value = 1.0
for nm, col in (("Sec_Skin", (0.95, 0.62, 0.48)), ("Sec_Orbicularis", (0.85, 0.16, 0.20)), ("Sec_OrbitalFat", (1.0, 0.68, 0.12)),
                ("Sec_Bone", (0.95, 0.90, 0.76)), ("Sec_Tarsus", (0.98, 0.86, 0.80)), ("Sec_Sclera", (0.97, 0.96, 0.94)),
                ("Sec_Vitreous", (0.55, 0.78, 0.92)), ("Sec_Lens", (0.95, 0.85, 0.55))):
    b = bpy.data.materials[nm].node_tree.nodes["Principled BSDF"]; b.inputs["Base Color"].default_value = (*col, 1)
    b.inputs["Coat Weight"].default_value = 0.6; b.inputs["Roughness"].default_value = 0.35
    for n in bpy.data.materials[nm].node_tree.nodes:
        if n.type == "MIX" and n.data_type == "RGBA" and not n.inputs[6].is_linked:
            n.inputs[6].default_value = (*col, 1); n.inputs[7].default_value = (col[0] * 0.75, col[1] * 0.6, col[2] * 0.6, 1)
for n, e in (("Sec_Key", 1.2), ("Sec_Rim", 0.8), ("Sec_Fill", 0.6)):
    L = O[n].data
    if L.animation_data and L.animation_data.action:
        act = L.animation_data.action
        try: fcs = list(act.fcurves)
        except AttributeError: fcs = [fc for ly in act.layers for s in ly.strips for cb in s.channelbags for fc in cb.fcurves]
        for fc in fcs:
            for kp in fc.keyframe_points:
                if kp.co.y > 0: kp.co.y = e
# 4. clean CG skin (no pores), neutral grey-blue shirt
sg = next(n for n in bpy.data.materials["Driver.body"].node_tree.nodes if n.type == "GROUP")
sg.inputs["Pore strength"].default_value = 0.0; sg.inputs["Roughness"].default_value = 0.5
sm = bpy.data.materials["Driver.male_casualsuit01"]; bs = next((n for n in sm.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
if bs and bs.inputs["Base Color"].is_linked:
    src = bs.inputs["Base Color"].links[0].from_socket
    mx = sm.node_tree.nodes.new("ShaderNodeMix"); mx.data_type = "RGBA"; mx.blend_type = "COLOR"; mx.inputs[0].default_value = 0.85
    mx.inputs[7].default_value = (0.32, 0.38, 0.46, 1); sm.node_tree.links.new(src, mx.inputs[6]); sm.node_tree.links.new(mx.outputs[2], bs.inputs["Base Color"])
# 5. depth of field: f/5.6 everywhere, f/8-11 macros (re-key; anim_look only clamps the static value)
camd = O["FilmCam"].data
act = camd.animation_data.action
try: fcs = list(act.fcurves)
except AttributeError: fcs = [fc for ly in act.layers for s in ly.strips for cb in s.channelbags for fc in cb.fcurves]
for fc in fcs:
    if "fstop" in fc.data_path:
        for kp in fc.keyframe_points: kp.co.y = max(kp.co.y, 5.6)
# 6. hands: Limit Rotation (local) on fingers, thumb and wrist
rig = O["Driver"]
def limit(pb, x=(0, 90), y=(-10, 10), z=(-10, 10)):
    c = pb.constraints.new("LIMIT_ROTATION"); c.owner_space = "LOCAL"
    c.use_limit_x = c.use_limit_y = c.use_limit_z = True
    c.min_x, c.max_x = map(math.radians, x); c.min_y, c.max_y = map(math.radians, y); c.min_z, c.max_z = map(math.radians, z)
for pb in rig.pose.bones:
    n = pb.name
    if n.startswith("finger1-"): limit(pb, (-20, 60), (-35, 35), (-35, 35))          # thumb: natural cone
    elif n.startswith("finger"): limit(pb, (0, 90))
    elif n.startswith("wrist."): limit(pb, (-60, 60), (-30, 30), (-25, 25))
for s in "LR":   # elbow: IK limits, no hyper-extension
    pb = rig.pose.bones["lowerarm01." + s]
    for ax in ("x", "y", "z"): setattr(pb, "lock_ik_" + ax, False)
for o in O:
    if o.type == 'LIGHT': o.visible_camera = False   # light panels never show up in frame
sc.render.use_motion_blur = False
sc.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=OUT_PATH, compress=True); print("SAVED", OUT_PATH)
