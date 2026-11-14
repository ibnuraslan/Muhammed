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
from mathutils import Vector
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
# the writing hand gets its forearm (nitrile up to the elbow), entering from the frame edge - no arm-less glove
gb = bpy.data.objects["GloveHands.body"]
keep = gb.vertex_groups["keep_hands"]
fa_ = gb.vertex_groups.get("keep_forearms") or gb.vertex_groups.new(name="keep_forearms")
gi = {g.name: g.index for g in gb.vertex_groups}
arm = {gi[n] for n in ("lowerarm01.L", "lowerarm02.L", "lowerarm01.R", "lowerarm02.R", "wrist.L", "wrist.R") if n in gi}
ids = [v.index for v in gb.data.vertices if any((g.group == keep.index and g.weight > 0.5) or (g.group in arm and g.weight > 0.35) for g in v.groups)]
fa_.add(ids, 1.0, 'REPLACE')
gb.modifiers["hands_only"].vertex_group = "keep_forearms"
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
PTR = bpy.data.objects["Patient"]
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
