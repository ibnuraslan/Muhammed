"""Fixes from the director's moving preview of v010 (= v008c synced), applied to the packed v008c film.
blender -b SurgeonBrandsLivers_v008c_60fps.blend --python 13_preview_fixes.py -- <out.blend>

1. Black frames at the calendar wall (my 638-640): the snap put the camera inside the calendar paper, then right behind
   the home picture frame hung on the other side of the same wall. The home picture moves 0.8 m along the wall and the
   camera's near face is now in front of the calendar (04_camera.py ZONES).
2. Studio liver beat (1040-1200): the arm-less glove hands are cut; the liver is shown alone, still (no prop moving by itself).
3. Smoke puffs over the liver (translucent discs) removed.
4. Camera keys re-baked from 04_camera.py's K list (same spline + wall/dive snapping) onto the existing CAM_Film and
   CAM_Film_Aim: pulled back at 240 and 330-365, studio exit in front of the liver, whip past the anaesthetist.
   The look pass's depth-of-field keys are left as they are."""
import sys, os, math
import bpy
from mathutils import Vector, Quaternion, Matrix
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene
V = lambda *a: Vector(a)
def ev(f): sc.frame_set(f)

# 1. home picture off the crossing line
for o in bpy.data.objects:
    if o.name.startswith(("HOME_Frame", "HOME_Art")) and o.matrix_world.translation.y < 0:
        o.location.y -= 0.8

# 2. liver alone in the light: hide the glove hands from 1036 on, hold the liver still at its mid-lift pose
GH = bpy.data.objects["GloveHands"]
for o in [GH] + list(GH.children_recursive):          # visible only for the studio writing (100-310), hidden after
    ad_ = o.animation_data
    if ad_ and ad_.action:
        for L in ad_.action.layers:
            for st in L.strips:
                for cb in st.channelbags:
                    for fcu in cb.fcurves:
                        if fcu.data_path == "hide_render":
                            k = fcu.keyframe_points
                            for i in reversed(range(len(k))):
                                if k[i].co.x > 312: k.remove(k[i], fast=True)
                            fcu.update()
# studio (v008e): no glove hands and no pen at all - the S and B burn themselves into the liver (sparks + hot trail),
# like the accepted liver-alone shot. No hand ever appears without an arm.
def hide_all(ob):
    for o in [ob] + list(ob.children_recursive):
        ad_ = o.animation_data
        if ad_ and ad_.action:
            for L in ad_.action.layers:
                for st in L.strips:
                    for cb in st.channelbags:
                        for fcu in list(cb.fcurves):
                            if fcu.data_path == "hide_render": cb.fcurves.remove(fcu)
        o.hide_render = True
hide_all(GH); hide_all(bpy.data.objects["ArgonPen_Studio"])
liver = bpy.data.objects["Liver"]
ev(1120); L_hold, R_hold = liver.location.copy(), liver.rotation_euler.copy()
ad = liver.animation_data
for L in ad.action.layers:
    for st in L.strips:
        for cb in st.channelbags:
            for fcu in cb.fcurves:
                if fcu.data_path in ("location", "rotation_euler"):
                    k = fcu.keyframe_points
                    for i in reversed(range(len(k))):
                        if k[i].co.x > 1040: k.remove(k[i], fast=True)
                    fcu.update()
for f in (1041, 1710):
    liver.location = L_hold; liver.rotation_euler = R_hold
    liver.keyframe_insert("location", frame=f); liver.keyframe_insert("rotation_euler", frame=f)

# 2b. on the OR table her hidden body (under the drape, masked to the head) sits 7 cm lower so the surgeons' forearms
# stay above it (clip_scan unmasks it); 0 at home and on the bed
for nm in ("Patient", "AnaesthesiaMask", "NeckTowel", "AnaesTube"):   # her face mask, towel and tube go down with her
    PTR = bpy.data.objects[nm]
    for f, z in ((1, -0.07), (600, -0.07), (601, 0.0), (1060, 0.0), (1061, -0.07), (1710, -0.07)):
        PTR.delta_location = (0, 0, z); PTR.keyframe_insert("delta_location", index=2, frame=f)
    for L in PTR.animation_data.action.layers:
        for st in L.strips:
            for cb in st.channelbags:
                for fcu in cb.fcurves:
                    if fcu.data_path == "delta_location":
                        for k in fcu.keyframe_points: k.interpolation = 'CONSTANT'
# 3. smoke puffs
for o in bpy.data.objects:
    if o.name.startswith("Smoke_"):
        if o.animation_data: o.animation_data_clear()
        o.hide_render = True; o.hide_viewport = True

# 5. hands re-placed with pipeline/hand_poses.py place_hand (home woman, clerk), gavel baked from the judge's hand
exec(open(os.path.join(HERE, "..", "..", "pipeline", "hand_poses.py")).read())
def ik_clear(r, s, a0, b0):
    for L in r.animation_data.action.layers:
        for st in L.strips:
            for cb in st.channelbags:
                for fcu in cb.fcurves:
                    if fcu.data_path in ('pose.bones["IK_hand.%s"].location' % s, 'pose.bones["IK_hand.%s"].rotation_quaternion' % s):
                        k = fcu.keyframe_points
                        for i in reversed(range(len(k))):
                            if a0 <= k[i].co.x <= b0: k.remove(k[i], fast=True)
                        fcu.update()
def Wb(r, b, tail=False):
    pb = r.pose.bones[b]; return r.matrix_world @ (pb.tail if tail else pb.head)
def axes(r):
    up = (Wb(r, "neck01") - Wb(r, "spine05")).normalized()
    right = (Wb(r, "upperarm01.R") - Wb(r, "upperarm01.L")); right = (right - up * right.dot(up)).normalized()
    fwd = up.cross(right).normalized()
    if (Wb(r, "jaw", True) - Wb(r, "head")).dot(fwd) < 0: fwd = -fwd
    return up, right, fwd
# 5a. the woman at home: mug held in front of her chest (elbow down), then one palm pressed on her right side under the
#     ribs (the liver) and the other on her left thigh above the knee. No raised elbow, no hand at the groin.
PT = bpy.data.objects["Patient"]; MUG = bpy.data.objects["Mug"]
plan = {}
for f in range(601, 776, 3):
    ev(f); up, right, fwd = axes(PT)
    sp = Wb(PT, "spine03"); thigh = Wb(PT, "upperleg01.L").lerp(Wb(PT, "lowerleg01.L"), 0.70)
    if f <= 684 or f >= 756:                                                           # v008f: no mug; arm hangs relaxed
        c_ = (Wb(PT, "upperarm01.L") + Wb(PT, "upperarm01.R")) / 2          # mirror her hanging right hand onto the left
        if f <= 643:                                                   # both arms still hang here
            pr = Wb(PT, "finger3-1.R").lerp(Wb(PT, "wrist.R"), 0.4)
            pl = pr - right * 2 * (pr - c_).dot(right)
            HANG = ((pl - c_).dot(right), (pl - c_).dot(up), (pl - c_).dot(fwd))
        pl = c_ + right * HANG[0] + up * HANG[1] + fwd * HANG[2]              # then it keeps hanging (no raised elbow)
        L = (pl, right, -up)
    else:
        tax = (Wb(PT, "lowerleg01.L") - Wb(PT, "upperleg01.L")).normalized()
        front = (fwd - tax * fwd.dot(tax)).normalized()                                   # the thigh's own front
        L = (thigh + front * 0.05 - right * 0.085, (right * 0.7 - front * 0.3).normalized(), tax)   # palm on the OUTSIDE of her left thigh
    R = None
    if f >= 756:                                                                     # both arms hang as she turns away
        R = (c_ - right * HANG[0] + up * HANG[1] + fwd * HANG[2], -right, -up)
    elif f >= 662:
        R = (sp + right * 0.15 + fwd * 0.04 + up * 0.04, -right, (fwd * 0.7 - up * 0.3))  # palm pressed on her right side
    plan[f] = (L, R)
ik_clear(PT, "L", 601, 775); ik_clear(PT, "R", 662, 775)
for f, (L, R) in sorted(plan.items()):
    place_hand(PT, "L", f, L[0], L[1], L[2])
    ev(f); up_, right_, fwd_ = axes(PT)                      # left elbow points down and slightly out (no raised wing)
    pn = "Pole_elbow.L"; pbp = PT.pose.bones[pn]; bn_ = PT.data.bones[pn]
    pole_w = Wb(PT, "upperarm01.L") - up_ * 0.55 - right_ * 0.12 - fwd_ * 0.10
    pbp.location = bn_.matrix_local.to_3x3().inverted() @ (PT.matrix_world.inverted() @ pole_w - bn_.head_local)
    pbp.keyframe_insert("location", frame=f, group=pn)
    if R: place_hand(PT, "R", f, R[0], R[1], R[2])
    if f >= 756:
        pn = "Pole_elbow.R"; pbp = PT.pose.bones[pn]; bn_ = PT.data.bones[pn]
        pole_w = Wb(PT, "upperarm01.R") - up_ * 0.55 + right_ * 0.12 - fwd_ * 0.10
        pbp.location = bn_.matrix_local.to_3x3().inverted() @ (PT.matrix_world.inverted() @ pole_w - bn_.head_local)
        pbp.keyframe_insert("location", frame=f, group=pn)
# v008f: the mug is removed (it read as an object at her groin); her left hand is relaxed until it goes to the thigh
MUG.animation_data_clear(); MUG.hide_render = True; MUG.hide_viewport = True
for f in range(600, 686, 6):
    apply_pose(PT, "L", "relaxed", f)
# 5a2. Surgeon2 after the glove snap: elbows bent, both hands on the drape edge in front of him (no arms spread wide)
S2_ = bpy.data.objects["Surgeon2"]
for s_ in "LR":
    ik_clear(S2_, s_, 1018, 1048)
for f in (1022, 1030, 1038, 1046):
    place_hand(S2_, "L", f, Vector((-0.14, 0.27, 1.20)), Vector((0, 0, -1)), Vector((0.1, -1, 0)))
    place_hand(S2_, "R", f, Vector((-0.46, 0.27, 1.20)), Vector((0, 0, -1)), Vector((-0.1, -1, 0)))
    apply_pose(S2_, "L", "flat_palm", f); apply_pose(S2_, "R", "flat_palm", f)
# 5a3. the glowing x-ray liver sits INSIDE her torso: right upper abdomen under the ribs, 60% size, riding spine03
XL = bpy.data.objects["XRayLiver_Home"]
if XL.animation_data and XL.animation_data.action:
    for Lr in XL.animation_data.action.layers:
        for st in Lr.strips:
            for cb in st.channelbags:
                for fcu in list(cb.fcurves):
                    if fcu.data_path in ("location", "scale", "rotation_euler"): cb.fcurves.remove(fcu)
ev(700); up, right, fwd = axes(PT)
XL.scale = XL.scale * 0.6; bpy.context.view_layer.update()
bb = [XL.matrix_world @ Vector(c) for c in XL.bound_box]; B = sum(bb, Vector()) / 8
C = Wb(PT, "spine03") + right * 0.06 + fwd * 0.15 + up * 0.06      # on her right belly, inside her silhouette
XL.matrix_world = Matrix.Translation(C - B) @ XL.matrix_world
# 5b. the judge: from the pick-up on, the gavel's handle grip point sits in his evaluated palm on every frame (the designed
#     raise / strike rotation is kept), so it never floats free of his fist
PA = bpy.data.objects["PanelA"]; GAV = bpy.data.objects["Gavel"]
stick = [c for c in GAV.children if c.name.startswith("Gavel_src") and len(c.data.vertices) and (max(v.co.y for v in c.data.vertices) - min(v.co.y for v in c.data.vertices)) > 0.2][0]
GST = -min(v.co.y for v in stick.data.vertices)
mats = {}
for f in range(1484, sc.frame_end + 1):
    ev(f)
    pw = PA.matrix_world @ PA.pose.bones["wrist.R"].head; pm = PA.matrix_world @ PA.pose.bones["finger3-1.R"].head
    palm = pw.lerp(pm, 0.75)
    G = GAV.matrix_world @ Vector((0, -(GST - 0.075), 0))
    mats[f] = Matrix.Translation(palm - G) @ GAV.matrix_world
ev(1483); M0 = GAV.matrix_world.copy()
GAV.animation_data_clear(); GAV.rotation_mode = 'QUATERNION'
for f in (1, 1483):
    GAV.matrix_world = M0; GAV.keyframe_insert("location", frame=f); GAV.keyframe_insert("rotation_quaternion", frame=f)
for f, M in mats.items():
    GAV.matrix_world = M; GAV.keyframe_insert("location", frame=f); GAV.keyframe_insert("rotation_quaternion", frame=f)
print("GAVEL head z at strike", round(mats[1538].translation.z, 3), "grip shift at 1538", round((mats[1538].translation - Vector((-9.85, -0.1, 1.317))).length, 3))
# 5c. the clerk: left hand rests flat on the desk beside the licence (arm bent), head up so her face reads
PB_ = bpy.data.objects["PanelB"]
ik_clear(PB_, "L", 1556, 1710)
for f in range(1556, 1711, 6):
    place_hand(PB_, "L", f, Vector((-10.22, -0.93, 1.197)), Vector((0, 0, -1)), Vector((1, 0.25, 0)))
    ev(f)                                   # elbow down and back beside her body (no raised "wing")
    pn = "Pole_elbow.L"; pbp = PB_.pose.bones[pn]; bn_ = PB_.data.bones[pn]
    pole_w = (PB_.matrix_world @ PB_.pose.bones["upperarm01.L"].head) + Vector((-0.15, 0.06, -0.45))
    pole_a = PB_.matrix_world.inverted() @ pole_w
    pbp.location = bn_.matrix_local.to_3x3().inverted() @ (pole_a - bn_.head_local)
    pbp.keyframe_insert("location", frame=f, group=pn)
for bn, deg in (("head", -24), ("neck01", -8)):
    pb = PB_.pose.bones[bn]
    for Lr in PB_.animation_data.action.layers:
        for st in Lr.strips:
            for cb in st.channelbags:
                fcs = sorted([fc for fc in cb.fcurves if fc.data_path == 'pose.bones["%s"].rotation_quaternion' % bn], key=lambda c: c.array_index)
                if len(fcs) != 4: continue
                frames = sorted({round(k.co.x) for k in fcs[0].keyframe_points if k.co.x >= 1480})
                for f in frames:
                    q = Quaternion([fc.evaluate(f) for fc in fcs]) @ Quaternion((1, 0, 0), math.radians(deg))
                    for i, fc in enumerate(fcs): fc.keyframe_points.insert(f, q[i])
# 4. camera re-bake from 04_camera.py
src = open(os.path.join(HERE, "04_camera.py")).read()
exec(open(os.path.join(HERE, "lib.py")).read())
exec(open(os.path.join(HERE, "..", "..", "pipeline", "anim_lib.py")).read())
part_a = src[src.index("def head(name, f, dz=0.0):"):src.index("cam_d = bpy.data.cameras.new")]
part_b = src[src.index("def pvec(keys):"):src.index("PS = {}")]
sc.frame_set(1)       # LZ and the other set positions are read from the frame-1 liver (before its held pose)
exec(part_a); exec(part_b)
cam = bpy.data.objects["CAM_Film"]; aim = bpy.data.objects["CAM_Film_Aim"]
for ob, paths in ((cam, ("location",)), (aim, ("location",)), (cam.data, ("lens",))):
    if not ob.animation_data or not ob.animation_data.action: continue
    for L in ob.animation_data.action.layers:
        for st in L.strips:
            for cb in st.channelbags:
                for fcu in list(cb.fcurves):
                    if fcu.data_path in paths: cb.fcurves.remove(fcu)
PS = {}
for f in range(1, sc.frame_end + 1):
    cam.location = snap(f, fc(f), PS); cam.keyframe_insert("location", frame=f)
    aim.location = fa(f); aim.keyframe_insert("location", frame=f)
    if f % 2 or f == sc.frame_end:
        cam.data.lens = fl(f); cam.data.keyframe_insert("lens", frame=f)
sc["camera_keys"] = [k[0] for k in K]
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print("PREVIEW_FIXES_DONE", len(K))
