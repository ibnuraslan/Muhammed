"""v003b: clean x-ray cutaway.  blender -b film_l.blend --python 03e_xray_clean.py -- <out.blend>
While the camera-attached card is fully opaque (1091-1231), only the x-ray figure, its spine and the card render.
The card sits behind the hero, so the office floor/walls/desk crossed it and showed a straight-edged slab.
The room comes back at 1232 for the 8-frame fade-out (card 1232->1240, normal hero from 1241)."""
import bpy, sys
out = sys.argv[sys.argv.index("--") + 1]
OB = bpy.data.objects; sc = bpy.context.scene
RANGES = [(151, 240)]   # v005: only the brain inset is on the card
keep = {"Hero_Xray", "Brain"} | {o.name for o in OB["Brain"].children_recursive} | {o.name for o in OB["Spine"].children_recursive} | {o.name for o in sc.camera.children_recursive}
def fcs(o):
    ad = o.animation_data
    if not ad or not ad.action: return []
    return [fc for l in ad.action.layers for st in l.strips for cb in st.channelbags for fc in cb.fcurves if fc.data_path == "hide_render"]
n = 0
for o in OB:
    if o.type in ("EMPTY", "LIGHT", "CAMERA", "ARMATURE", "LIGHT_PROBE") or o.name in keep or o.name.startswith("Hormone"): continue
    for F0, F1 in RANGES:
        fc = fcs(o)
        after = bool(fc[0].evaluate(F1 + 1)) if fc else o.hide_render
        before = bool(fc[0].evaluate(1)) if fc else o.hide_render
        if fc:
            while True:
                idx = [i for i, k in enumerate(fc[0].keyframe_points) if F0 <= k.co.x <= F1 + 1]
                if not idx: break
                fc[0].keyframe_points.remove(fc[0].keyframe_points[idx[0]])
        else:
            o.hide_render = before; o.keyframe_insert("hide_render", frame=1)
        o.hide_render = True; o.keyframe_insert("hide_render", frame=F0)
        o.hide_render = after; o.keyframe_insert("hide_render", frame=F1 + 1)
    for f in fcs(o):
        for kp in f.keyframe_points: kp.interpolation = "CONSTANT"
    n += 1
print("XRAYCLEAN hidden", n, "objects for", RANGES)
# vNEXT: MPFB tongue meshes poke out of the mouth when the head turns (hero f836-891). Never needed on screen: off for render.
for o in [o for o in OB if ".tongue" in o.name]:
    ad = o.animation_data
    if ad and ad.action:
        for l in ad.action.layers:
            for st in l.strips:
                for cb in st.channelbags:
                    for fc in [fc for fc in cb.fcurves if fc.data_path == "hide_render"]: cb.fcurves.remove(fc)
    o.hide_render = True; print("TONGUE off", o.name)
# vNEXT: the bend deformer throws the upper-spine pieces out of the body (f1101-1236) and they render as a black neck column: off
for o in [o for o in OB["Spine"].children_recursive if o.name in ("Object_8", "Object_10")]:
    ad = o.animation_data
    if ad and ad.action:
        for l in ad.action.layers:
            for st in l.strips:
                for cb in st.channelbags:
                    for fc in [fc for fc in cb.fcurves if fc.data_path == "hide_render"]: cb.fcurves.remove(fc)
    o.hide_render = True; print("SPINEPART off", o.name)
# v006: dust specks read as white blobs floating in the air: off
for o in [o for o in OB if o.name.startswith("Dust")]:
    ad = o.animation_data
    if ad and ad.action:
        for l in ad.action.layers:
            for st in l.strips:
                for cb in st.channelbags:
                    for fc in [fc for fc in cb.fcurves if fc.data_path == "hide_render"]: cb.fcurves.remove(fc)
    o.hide_render = True
print("DUST off")
# director's eye fix (LESSONS_LEARNED 3): cornea as Transparent mix instead of refraction, so irises are lit
import os
if "EnhancedEye" in bpy.data.node_groups:
    _NO_SAVE = True
    exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "eye_fix.py")).read())
else:
    print("EYEFIX skipped: no EnhancedEye group")
bpy.ops.wm.save_as_mainfile(filepath=out)
