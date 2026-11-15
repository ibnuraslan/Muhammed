"""v009b (director review of v009), on the VO timeline (1-2436, beats unchanged): camera, exposure and visibility only.
1. 480-570: the tunnel faded to black (stretched exposure ramp). Exposure held at its 480 value to the cut at 570.
2. 1648-1703 injection: low front-left close-up on the boy's face and the medic's hand with the syringe at his arm.
3+7. Mask: the edge boy's reaction runs on to 1820 (the mask's approach is never shown, so no floating mask); from
   1821 a tight close-up of the boy's face with the mask on (the diver's hands are not on the mask in this animation,
   so they are kept out of frame). The coach, the boy and DiverB hold still to the cut at 1885.
4. 1941-2104 tow: the camera keeps the 1940 side offset in the pair's travel frame (no drift into the rock), with a
   hard cut to a shot from ahead on their path, looking back at them, through the squeeze (1984-2026); a follow light, exposure held.
5. 1065-1070: the blurred rock frame takes the 1071 framing.
6. 1591-1647 and 1704-1820 edge-boy reactions: a slow push-in (no still hold).
8. 2100-2140: the flood-front mesh in the lens at the cave mouth is hidden (it is not in shot otherwise).
9. 2240-2300: the reed in front of the waving men is hidden.
10. 871-890: the cross-section push holds its 871 framing (no flat pink plane).
blender -b in.blend --python 24_v009b_fix.py -- out.blend"""
import bpy, sys
from mathutils import Vector as V
OUT = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene; cam = sc.camera; aim = cam.constraints[0].target
def fcs(o, path):
    ad = o.animation_data
    return sorted([fc for lay in ad.action.layers for st in lay.strips for cb in st.channelbags for fc in cb.fcurves if fc.data_path == path], key=lambda f: f.array_index)
CL, AL = fcs(cam, "location"), fcs(aim, "location"); LF = fcs(cam.data, "lens")
def ev(F, f): return V([fc.evaluate(f) for fc in F])
def setk(F, f, vals, interp='LINEAR'):
    for i, fc in enumerate(F):
        v = vals[i]
        ks = [k for k in fc.keyframe_points if int(round(k.co.x)) == f]
        if ks: ks[0].co.y = v; ks[0].handle_left.y = v; ks[0].handle_right.y = v; ks[0].interpolation = interp
        else: fc.keyframe_points.insert(f, v).interpolation = interp
def apply(vals):
    lo, hi = min(vals) - 0.5, max(vals) + 0.5
    for F in (CL, AL, LF):          # drop old keys in the range first (the time warps left fractional-frame keys)
        for fc in F:
            for kp in [k for k in fc.keyframe_points if lo <= k.co.x <= hi]: fc.keyframe_points.remove(kp)
    for f, (c, t, l) in sorted(vals.items()):
        setk(CL, f, c); setk(AL, f, t); setk(LF, f, [l])
    for F in (CL, AL, LF):
        for fc in F: fc.update()
def hold(f0, f1, src):
    c, t, l = ev(CL, src), ev(AL, src), LF[0].evaluate(src)
    apply({f: (c, t, l) for f in range(f0, f1 + 1)})
def push(f0, f1, src, k=0.18):
    c, t, l = ev(CL, src), ev(AL, src), LF[0].evaluate(src)
    apply({f: (c + (t - c) * k * (f - f0) / (f1 - f0), t, l) for f in range(f0, f1 + 1)})
b2 = bpy.data.objects["Boy2"]; db = bpy.data.objects["DiverB"]; syr = bpy.data.objects["Prop_Syringe"]
def face(f):
    sc.frame_set(f); hb = b2.pose.bones["head"]
    return (b2.matrix_world @ hb.head).lerp(b2.matrix_world @ hb.tail, 0.45)
# 10, 5
hold(871, 890, 871); hold(1065, 1070, 1071)
# 6 + 3: reactions (the second runs on to 1820)
push(1591, 1647, 1600); push(1704, 1820, 1720)
# 2: injection close-up
inj = {}
for f in range(1648, 1704):      # the medic's forearm crosses the lens before 1648 and after 1703
    sc.frame_set(f); sp = syr.matrix_world.translation.copy()
    inj[f] = (sp + V((0.15, -0.55, 0.05)) + V((0, 0.06, 0)) * (f - 1648) / 55, sp, 35)
apply(inj)
# 7: mask on the boy's face (from 1811, after it is on): tight, long lens from the low front-right so only face and mask fill the frame
DIR = V((-0.28, -1.57, -0.01)).normalized(); mk = {}
for f in range(1821, 1885):
    p = face(f)
    mk[f] = (p + DIR * (1.5 - 0.12 * (f - 1821) / 63) + V((0, 0, 0.12)), p - V((0, 0, 0.04)), 62)
apply(mk)
# hold the coach, the boy and DiverB still until the cut at 1885 (their next keys are the jump to the tow / parking;
# interpolating toward them made the coach fly off in the reaction shot and the boy slide out of the mask close-up)
for n in ("Coach", "Boy2", "DiverB"):
    r = bpy.data.objects[n]; k = 0
    for lay in r.animation_data.action.layers:
        for st in lay.strips:
            for cb in st.channelbags:
                for fc in cb.fcurves:
                    kps = sorted(fc.keyframe_points, key=lambda q: q.co.x)
                    for i, kp in enumerate(kps[:-1]):
                        if 1700 <= kp.co.x < 1885 and kps[i + 1].co.x >= 1884: kp.interpolation = 'CONSTANT'; k += 1
                    fc.update()
    print("HOLD", n, k)
# 4: tow
def pair(f):
    sc.frame_set(f)
    return ((db.matrix_world @ db.pose.bones["root"].head) + (b2.matrix_world @ b2.pose.bones["root"].head)) / 2
PP = {f: pair(f) for f in range(1925, 2115)}
def frame_at(f):      # travel frame of the pair (forward, side, up), smoothed over +-10 frames
    fw = PP[min(f + 10, 2114)] - PP[max(f - 10, 1925)]; fw.z = 0; fw.normalize()
    return fw, V((0, 0, 1)).cross(fw).normalized(), V((0, 0, 1))
fw0, sd0, up0 = frame_at(1940); d0 = ev(CL, 1940) - PP[1940]; t0 = ev(AL, 1940) - PP[1940]; rl = LF[0].evaluate(1940)
loc = lambda v, fw, sd, up: (v.dot(fw), v.dot(sd), v.dot(up))
dc = loc(d0, fw0, sd0, up0); dt = loc(t0, fw0, sd0, up0)
tw = {}
for f in range(1941, 2105):
    fw, sd, up = frame_at(f); p = PP[f]
    c = p + fw * dc[0] * 0.8 + sd * dc[1] * 0.8 + up * dc[2]; t = p + fw * dt[0] + sd * dt[1] + up * dt[2]
    e = min(1.0, (f - 1940) / 12.0)
    tw[f] = (ev(CL, 1940).lerp(c, e), t, rl)
    if 1984 <= f <= 2026:      # the passage squeezes: hard cut to a camera on their own path 0.75 s ahead (inside the tube)
        tw[f] = (PP[min(2114, f + 45)] + V((0, 0, 0.25)), p + V((0, 0, 0.1)), 26)    # ahead on their path, looking back at them
apply(tw)
# exposure holds (1, 4)
def exp_hold(f0, f1):
    sc.frame_set(f0); v = sc.view_settings.exposure
    for f in (f0, f1):
        sc.view_settings.exposure = v; sc.view_settings.keyframe_insert("exposure", frame=f)
    ad = sc.animation_data
    for lay in ad.action.layers:
        for st in lay.strips:
            for cb in st.channelbags:
                for fc in cb.fcurves:
                    if fc.data_path == "view_settings.exposure":
                        for kp in list(fc.keyframe_points):
                            if f0 < kp.co.x < f1: fc.keyframe_points.remove(kp)
                        fc.update()
    return v
print("EXP_HOLD", round(exp_hold(480, 570), 2), round(exp_hold(1940, 2104), 2))
sc.view_settings.exposure = 1.7; sc.view_settings.keyframe_insert("exposure", frame=570)    # the flooding tunnel stays readable to the cut
sc.view_settings.exposure = 2.2; sc.view_settings.keyframe_insert("exposure", frame=1960); sc.view_settings.keyframe_insert("exposure", frame=2104)
# follow light on the tow pair (lights only; never seen)
L = bpy.data.objects.new("TowFollow", bpy.data.lights.new("TowFollow", 'POINT')); sc.collection.objects.link(L)
L.data.shadow_soft_size = 0.5; L.visible_camera = False; L.visible_glossy = False; L.visible_volume_scatter = False
sv = bpy.data.materials["M_Silt"].node_tree.nodes["SiltAmount"].outputs[0]      # thin silt through the tow so the pair read
for f, v in ((1925, sv.default_value), (1935, 0.25), (2100, 0.25)):
    if f == 1925:
        bpy.context.scene.frame_set(1925); v = sv.default_value
    sv.default_value = v; sv.keyframe_insert("default_value", frame=f)
for f in range(1930, 2106, 2):
    L.location = tw[f][0] + V((0, 0, 0.25)) if f in tw else PP[f] + V((0.6, 0.4, 0.7)); L.keyframe_insert("location", frame=f)   # a lamp on the camera
for f, e in ((1, 0), (1929, 0), (1930, 450), (2104, 450), (2105, 0)):
    L.data.energy = e; L.data.keyframe_insert("energy", frame=f)
# 8, 9: visibility
for nm, f0, f1 in (("S2_SurgeFront", 2100, 2140), ("S1_Plant_1095", 2240, 2300)):
    o = bpy.data.objects.get(nm)
    if not o: print("MISSING", nm); continue
    for f, h in ((f0 - 1, o.hide_render), (f0, True), (f1, True), (f1 + 1, o.hide_render)):
        o.hide_render = h; o.hide_viewport = h; o.keyframe_insert("hide_render", frame=f); o.keyframe_insert("hide_viewport", frame=f)
    o.hide_render = False; o.hide_viewport = False
for o in bpy.data.objects:          # no bubble right in front of the lens in the shot from ahead
    if o.name.startswith("FX_Bubble_"):
        for f, h in ((1967, False), (1968, True), (2026, True), (2027, False)):
            o.hide_render = h; o.hide_viewport = h; o.keyframe_insert("hide_render", frame=f); o.keyframe_insert("hide_viewport", frame=f)
for nm in ("DiverB_TorchLight", "Boy2_TorchLight"):     # underwater the torch beam lit the murk into a white blob in front of the lens
    o = bpy.data.objects.get(nm)
    if o: o.visible_volume_scatter = False
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("V009B_OK")
