"""v007: exhaled bubbles only underwater. They were shown from 2370 in the air chamber, rising through the boy's and the
medic's heads (limb_check PROPHEAD). Now shown 2425-2580 only (under water), render and viewport keyed together.
blender -b in.blend --python 19_v007_bubbles.py -- out.blend"""
import bpy, sys
OUT = sys.argv[sys.argv.index("--") + 1]
n = 0
for o in bpy.data.objects:
    if not o.name.startswith("FX_Bubble_"): continue
    ad = o.animation_data
    if ad and ad.action:
        for lay in ad.action.layers:
            for st in lay.strips:
                for cb in st.channelbags:
                    for fc in list(cb.fcurves):
                        if fc.data_path in ("hide_render", "hide_viewport"): cb.fcurves.remove(fc)
    for f, h in ((1, True), (2424, True), (2425, False), (2705, True)):
        o.hide_render = h; o.hide_viewport = h
        o.keyframe_insert("hide_render", frame=f); o.keyframe_insert("hide_viewport", frame=f)
    n += 1
print("BUBBLES_UNDERWATER", n)
bpy.ops.wm.save_as_mainfile(filepath=OUT)
