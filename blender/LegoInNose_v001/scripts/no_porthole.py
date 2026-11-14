"""v008f: the x-ray porthole over the boy's nose (2.0-2.75 s synced) read as a glitch -> removed: the skin-shader radius is 0 on
every key and the porthole interior (XRay_Inside + children) never renders. blender -b in.blend --python no_porthole.py -- out.blend"""
import bpy, sys
n = 0
for m in bpy.data.materials:
    if not m.node_tree: continue
    for nd in m.node_tree.nodes:
        if nd.name == "PortRadius":
            nd.outputs[0].default_value = 0.0
            ad = m.node_tree.animation_data
            if ad and ad.action:
                for l in ad.action.layers:
                    for st in l.strips:
                        for cb in st.channelbags:
                            for fc in cb.fcurves:
                                if "PortRadius" in fc.data_path:
                                    for k in fc.keyframe_points: k.co.y = 0.0; k.handle_left.y = 0.0; k.handle_right.y = 0.0
                                    fc.update(); n += 1
for root in ("XRay_Inside",):
    o = bpy.data.objects.get(root)
    if not o: continue
    for x in [o] + list(o.children_recursive):
        if x.animation_data: x.animation_data_clear()
        x.hide_render = True; x.hide_viewport = True
        if x.type == "LIGHT": x.data.energy = 0.0
print("NOPORT fcurves zeroed", n)
bpy.ops.wm.save_as_mainfile(filepath=sys.argv[sys.argv.index("--") + 1], compress=True)
