"""v012 (client: 'empty blurry pink frame'): the four nostril-tunnel passes become HARD CUTS between the face and the cutaway
(batch-2 staging allows cuts). For each range the camera (CAM_Film location + constraint influences, CAM_Film_Aim, camera data:
lens, f-stop...) is re-timed: frames [a, b] play the camera of [c, b] (a cut at a, then a slower ease) - only the camera, never
the characters. The tunnel meshes never render, and the visible_camera keys that hid the room/characters inside the tunnels are
cleared inside those windows. blender -b in.blend --python cut_tunnels.py -- out.blend"""
import bpy, sys
OUT = sys.argv[sys.argv.index("--") + 1]; sc = bpy.context.scene
CUTS = [(578, 700, 626), (729, 800, 760), (944, 1010, 972), (1151, 1230, 1190)]      # (a, b, c): frames a..b show camera c..b
TUN_WIN = [(598, 626), (726, 754), (944, 973), (1148, 1176)]
def fcs(idb):
    ad = getattr(idb, "animation_data", None)
    return [fc for l in ad.action.layers for st in l.strips for cb in st.channelbags for fc in cb.fcurves] if ad and ad.action else []
cam = bpy.data.objects["CAM_Film"]; aim = bpy.data.objects["CAM_Film_Aim"]
curves = fcs(cam) + fcs(aim) + fcs(cam.data)
for a, b, c in CUTS:
    for fc in curves:
        if fc.data_path in ("hide_render", "hide_viewport"): continue
        vals = {f: fc.evaluate(c + (f - a) * (b - c) / (b - a)) for f in range(a, b + 1)}
        for kp in [k for k in fc.keyframe_points if a <= k.co.x <= b][::-1]: fc.keyframe_points.remove(kp)
        for f, v in vals.items(): fc.keyframe_points.insert(f, v, options={"FAST"})
        prev = [k for k in fc.keyframe_points if k.co.x == a - 1]
        if not prev: fc.keyframe_points.insert(a - 1, fc.evaluate(a - 1), options={"FAST"})
        for k in fc.keyframe_points:
            if a - 1 <= k.co.x <= a: k.interpolation = "CONSTANT"        # the cut: no blend between a-1 and a
        fc.update()
nt = 0
for o in bpy.data.objects:
    if o.name.startswith("Tunnel_"):
        if o.animation_data: o.animation_data_clear()
        o.hide_render = True; o.hide_viewport = True; nt += 1
nv = 0
for o in bpy.data.objects:
    for fc in fcs(o):
        if fc.data_path != "visible_camera": continue
        for w0, w1 in TUN_WIN:
            ks = [k for k in fc.keyframe_points if w0 - 2 <= k.co.x <= w1 + 2 and k.co.y < 0.5]
            for k in ks: k.co.y = 1.0; nv += 1
        fc.update()
print("CUTS done; tunnels hidden", nt, "visible_camera keys restored", nv)
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
