# curled (fetal) burial pose, FK on the MPFB default rig. exec'd; needs Rig from anim_lib and R_.
CURL = {
    # bone: [(axis, deg), ...] in armature rest axes (character faces -Y, X = its left)
    "spine05": [("X", 8)], "spine04": [("X", 10)], "spine03": [("X", 12)], "spine02": [("X", 10)], "spine01": [("X", 8)],
    "neck01": [("X", 4)], "neck02": [("X", 4)], "head": [("X", 2)],
    "upperleg01.L": [("X", -105), ("Z", -16)], "upperleg01.R": [("X", -105), ("Z", 16)],
    "lowerleg01.L": [("X", 125)], "lowerleg01.R": [("X", 125)],
    "foot.L": [("X", 25)], "foot.R": [("X", 25)],
}
def curl_off_ik(obj):
    """legs FK (IK off), arms stay on IK so the hands can rest on the shins"""
    for s in "LR":
        for bn in ("lowerleg02." + s, "foot." + s):
            for c in obj.pose.bones[bn].constraints:
                if c.type in ('IK', 'COPY_ROTATION'): c.influence = 0.0
def key_curl(R, f, amount=1.0, extra=None):
    d = dict(CURL)
    if extra: d.update(extra)
    for n, seq in d.items():
        if n in R.PB:
            R.key_rot(n, f, [(ax, v * amount) for ax, v in seq])

def curl_hands(R, f, hug=1.0):
    """hands rest on the front of the shins just below the knees (arms tucked in)"""
    obj = R.o; bpy.context.scene.frame_set(int(f)); bpy.context.view_layer.update()
    Mw = obj.matrix_world
    for s, sx in (("L", 1), ("R", -1)):
        kn = Mw @ obj.pose.bones["lowerleg01." + s].head
        an = Mw @ obj.pose.bones["foot." + s].head
        shin = kn.lerp(an, 0.22 + 0.10 * (1 - hug))
        down = (an - kn).normalized()
        fwd = (Mw.to_3x3() @ Vector((0, -1, 0))).normalized()   # body front
        side = (Mw.to_3x3() @ Vector((sx, 0, 0))).normalized()
        pp = shin + fwd * 0.075 + side * 0.02
        place_hand(obj, s, f, pp, -fwd, (down * 0.7 - side * 0.7).normalized(), skin=0.0)
        apply_pose(obj, s, "relaxed", f)
        pn = "Pole_elbow." + s; pb = obj.pose.bones[pn]
        el = Mw.inverted() @ (kn + side * 0.5 + Mw.to_3x3() @ Vector((0, 0.2, 0.25)))
        pb.location = obj.data.bones[pn].matrix_local.to_3x3().inverted() @ (el - obj.data.bones[pn].head_local)
        pb.keyframe_insert("location", frame=f, group=pn)
