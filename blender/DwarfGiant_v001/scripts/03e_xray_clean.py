"""v003b: clean x-ray cutaway.  blender -b film_l.blend --python 03e_xray_clean.py -- <out.blend>
While the camera-attached card is fully opaque (1091-1231), only the x-ray figure, its spine and the card render.
The card sits behind the hero, so the office floor/walls/desk crossed it and showed a straight-edged slab.
The room comes back at 1232 for the 8-frame fade-out (card 1232->1240, normal hero from 1241)."""
import bpy, sys
out = sys.argv[sys.argv.index("--") + 1]
OB = bpy.data.objects; sc = bpy.context.scene
F0, F1 = 1091, 1231
keep = {"Hero_Xray"} | {o.name for o in OB["Spine"].children_recursive} | {o.name for o in sc.camera.children_recursive}
def fcs(o):
    ad = o.animation_data
    if not ad or not ad.action: return []
    return [fc for l in ad.action.layers for st in l.strips for cb in st.channelbags for fc in cb.fcurves if fc.data_path == "hide_render"]
n = 0
for o in OB:
    if o.type in ("EMPTY", "LIGHT", "CAMERA", "ARMATURE", "LIGHT_PROBE") or o.name in keep or o.name.startswith("Hormone"): continue
    fc = fcs(o)
    after = bool(fc[0].evaluate(F1 + 1)) if fc else o.hide_render
    before = bool(fc[0].evaluate(1)) if fc else o.hide_render
    if fc:
        for kp in [k for k in fc[0].keyframe_points if F0 <= k.co.x <= F1 + 1]: fc[0].keyframe_points.remove(kp)
    else:
        o.hide_render = before; o.keyframe_insert("hide_render", frame=1)
    o.hide_render = True; o.keyframe_insert("hide_render", frame=F0)
    o.hide_render = after; o.keyframe_insert("hide_render", frame=F1 + 1)
    for f in fcs(o):
        for kp in f.keyframe_points: kp.interpolation = "CONSTANT"
    n += 1
print("XRAYCLEAN hidden", n, "objects for", F0, F1)
bpy.ops.wm.save_as_mainfile(filepath=out)
