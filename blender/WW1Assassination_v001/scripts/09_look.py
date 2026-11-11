"""Animated-CG look (client, Nov 11 22:45): run pipeline/anim_look.py first (--no-sky; our sky texture is already a clear
blue sky), then fix what that tool cannot reach because it is keyframed here: f-stop keys (>= 5.6), sun energy keys (x1.25),
exposure keys (brighter, high-key), plus stylised bright blast smoke.
blender -b film_v3.blend --python ../pipeline/anim_look.py -- look.blend --no-sky --sat 1.3 --bump 0.35
blender -b look.blend --python 09_look.py -- <out.blend>"""
import sys
import bpy
OUT = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene
def fcurves(idb):
    ad = idb.animation_data
    if not ad or not ad.action: return []
    return [fc for l in ad.action.layers for st in l.strips for cb in st.channelbags for fc in cb.fcurves]
cam = sc.camera.data
for fc in fcurves(cam):
    if "aperture_fstop" in fc.data_path:
        for kp in fc.keyframe_points:
            kp.co[1] = max(5.6, kp.co[1]); kp.handle_left[1] = max(5.6, kp.handle_left[1]); kp.handle_right[1] = max(5.6, kp.handle_right[1])
        fc.update()
sun = bpy.data.objects["Key_Sun"].data
for fc in fcurves(sun):
    if fc.data_path == "energy":
        for kp in fc.keyframe_points:
            kp.co[1] *= 1.25; kp.handle_left[1] *= 1.25; kp.handle_right[1] *= 1.25
        fc.update()
for fc in fcurves(sc):
    if fc.data_path == "view_settings.exposure":
        for kp in fc.keyframe_points:
            kp.co[1] += 0.35; kp.handle_left[1] += 0.35; kp.handle_right[1] += 0.35
        fc.update()
m = bpy.data.materials.get("BlastSmoke")
if m:
    for n in m.node_tree.nodes:
        if n.type == "VOLUME_PRINCIPLED": n.inputs["Color"].default_value = (0.45, 0.43, 0.42, 1)
sc.render.use_motion_blur = False
# soft fill so shadows stay readable (high-key)
if not bpy.data.objects.get("Fill_Sun"):
    L = bpy.data.lights.new("Fill_Sun", 'SUN'); L.energy = 0.9; L.angle = 0.6; L.color = (0.85, 0.92, 1.0)
    o = bpy.data.objects.new("Fill_Sun", L); sc.collection.objects.link(o); o.rotation_euler = (0.9, 0.0, -0.6)
    o.data.use_shadow = False
print("LOOK_DONE")
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
