"""After pipeline/anim_look.py: make the animated parts of the look follow it.
- the camera sky gradient dims to a readable blue night when the sun is down (day->night->day in beat 5, rewind in beat 3)
- keyed sun energy x1.25 (anim_look scales only un-keyed values)
blender -b look.blend --python 03b_look.py -- <out.blend>"""
import sys
import bpy
OUT = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene
nt = sc.world.node_tree
mix = nt.nodes["anim_look_v1"]
skyb = mix.inputs[2].links[0].from_node
ramp = skyb.inputs["Color"].links[0].from_node
night = nt.nodes["SkyNight"].inputs["Factor"]
def fcurves(idb):
    ad = idb.animation_data; out = []
    if ad and ad.action:
        for ly in ad.action.layers:
            for st in ly.strips:
                for cb in st.channelbags: out += list(cb.fcurves)
    return out
for fc in fcurves(bpy.data.lights["Sun"]):
    if fc.data_path == "energy":
        for kp in fc.keyframe_points: kp.co.y *= 1.25; kp.handle_left.y *= 1.25; kp.handle_right.y *= 1.25
DAY_TOP, DAY_BOT = (0.08, 0.55, 0.93, 1), (0.80, 0.93, 1.0, 1)
NIGHT_TOP, NIGHT_BOT = (0.01, 0.04, 0.16, 1), (0.08, 0.16, 0.36, 1)
e0, e1 = ramp.color_ramp.elements[0], ramp.color_ramp.elements[1]
for f in range(sc.frame_start, sc.frame_end + 1, 4):
    sc.frame_set(f); k = night.default_value      # 0 day .. 1 night
    lerp = lambda a, b: tuple(a[i] + (b[i] - a[i]) * k for i in range(4))
    e0.color = lerp(DAY_BOT, NIGHT_BOT); e1.color = lerp(DAY_TOP, NIGHT_TOP)
    e0.keyframe_insert("color", frame=f); e1.keyframe_insert("color", frame=f)
print("LOOK2 done")
bpy.ops.wm.save_as_mainfile(filepath=OUT)
