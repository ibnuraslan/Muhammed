"""HeadsetBullet v004 look fixes after pipeline/anim_look.py (client look change, 22:45 UTC: bright clean 3D animation).
blender -b looked.blend --python 06_anim_look_fixes.py -- <out.blend>"""
import sys, bpy, math
out = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene
def fcurves(idb):
    ad = idb.animation_data
    if not ad or not ad.action: return []
    return [fc for l in ad.action.layers for s in l.strips for cb in s.channelbags for fc in cb.fcurves]
# 1. f-stop is animated: clamp keys >= 5.6, except the true macro moments (bullet at the ear cup, impact) >= 4
for cam in bpy.data.cameras:
    for fc in fcurves(cam):
        if fc.data_path == "dof.aperture_fstop":
            for kp in fc.keyframe_points:
                lo = 4.0 if 600 <= kp.co.x <= 960 else 5.6
                if kp.co.y < lo: kp.co.y = lo; kp.handle_left.y = kp.handle_right.y = lo
            fc.update()
# 2. bright, clean room: lighter walls and ceiling, more even fill, softer coloured washes
def tint(name, rgb):
    m = bpy.data.materials.get(name)
    if not m: return
    for n in m.node_tree.nodes:
        if n.type == 'MIX' and n.data_type == 'RGBA' and n.blend_type == 'MULTIPLY':
            n.inputs[7].default_value = (*rgb, 1)
tint("IntPaint", (0.62, 0.78, 0.95))         # light sky-blue walls
tint("Laminate", (0.75, 0.52, 0.32))          # warm honey floor
for nm, e in (("Room_Bounce", 140), ("Win_Fill", 160), ("Sun_Beam", 520), ("RGB_Wash_Back", 30), ("RGB_Wash_Right", 22), ("RGB_Wash_Left", 16)):
    L = bpy.data.lights.get(nm)
    if L: L.energy = e
ceil = bpy.data.materials.get("Ceiling")
# 3. hit: spark + crack only (already no injury); make the crack a clean bright-edged stylised crack, sparks warm yellow
sp = bpy.data.materials.get("Spark")
if sp:
    b = sp.node_tree.nodes["Principled BSDF"]; b.inputs["Emission Color"].default_value = (1.0, 0.8, 0.3, 1)
# 4. no grain/vignette/haze in the scene; keep exposure, check blowout in the sheet
sc.view_settings.exposure = 0.15
print("FIXES done")
bpy.ops.wm.save_as_mainfile(filepath=out, compress=True)
