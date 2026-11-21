"""After pipeline/anim_look.py: the approved v009 high-key tweaks (house siding, exposure, room fill, wall colour),
the section studio card stays self-lit, f-stops at least 8 on every shot.
blender -b work/v11_look.blend --python scripts/11_look_fix.py -- work/v11_fix.blend"""
import sys, bpy
out = sys.argv[sys.argv.index("--") + 1]
sid = bpy.data.materials.get("M_siding_blue")
if sid:
    mix = [n for n in sid.node_tree.nodes if n.type == "MIX"][0]; mix.inputs[7].default_value = (1.9, 2.3, 2.9, 1)
bpy.context.scene.view_settings.exposure = 0.35
for ln, k in (("L_fill", 1.6), ("L_window_bounce", 1.5), ("L_monitor", 1.3)):
    l = bpy.data.lights.get(ln)
    if l: l.energy *= k
rw = bpy.data.materials.get("M_room_wall")
if rw:
    mix = [n for n in rw.node_tree.nodes if n.type == "MIX"][0]; mix.inputs[7].default_value = (0.62, 0.72, 0.92, 1)
fk = bpy.data.lights.get("L_face_key")
if fk: fk.energy = min(fk.energy, 10.0)
# anim_look raises light energy x1.25: keep the catchlight and the hole glint tiny
for n, e in (("L_catchlight", 1.5), ("L_face_key", 10.0)):
    l = bpy.data.lights.get(n)
    if l and not (l.animation_data and l.animation_data.action): l.energy = e
cam = bpy.data.cameras["CAM_Film"]
ad = cam.animation_data
fcs = []
if ad and ad.action:
    for L in ad.action.layers:
        for st in L.strips:
            for cb in st.channelbags: fcs += list(cb.fcurves)
for fc in fcs:
    if fc.data_path == "dof.aperture_fstop":
        for k in fc.keyframe_points: k.co.y = max(8.0, k.co.y)
bpy.ops.wm.save_as_mainfile(filepath=out)
print("LOOKFIX_DONE")
