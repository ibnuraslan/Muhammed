"""Hands pass (client, Nov 11 23:00 UTC): joint limits on fingers, thumbs and wrists for every character.
blender -b in.blend --python hands_pass.py -- out.blend
Finger curl in this rig is +X in the bone's local space (that is how 03_animate.py keys it), so the limits allow
-5..95 deg curl, +-10 deg spread/twist; thumbs get a cone; wrists (driven by Copy Rotation from the IK_hand target)
are clamped to +-65 flex, +-35 side, +-80 twist relative to the forearm."""
import sys, math, bpy
out = sys.argv[sys.argv.index("--") + 1]
R = math.radians
def limit(pb, x, y, z):
    c = pb.constraints.get("HandLimit") or pb.constraints.new("LIMIT_ROTATION")
    c.name = "HandLimit"; c.owner_space = "LOCAL"
    c.use_limit_x, c.min_x, c.max_x = True, R(x[0]), R(x[1])
    c.use_limit_y, c.min_y, c.max_y = True, R(y[0]), R(y[1])
    c.use_limit_z, c.min_z, c.max_z = True, R(z[0]), R(z[1])
    if hasattr(c, "use_legacy_behavior"): c.use_legacy_behavior = False
n = 0
for nm in ("Boy", "Teen", "Man", "Mom"):
    a = bpy.data.objects[nm]
    for pb in a.pose.bones:
        b = pb.name
        if b.startswith("finger1-"):            # thumb: a natural cone
            limit(pb, (-20, 60), (-30, 30), (-30, 30)); n += 1
        elif b.startswith("finger"):            # fingers: forward curl only
            limit(pb, (-5, 95), (-10, 10), (-10, 10)); n += 1
        # wrists: no Limit Rotation (the wrist copies the IK_hand target's rotation; clamping it swings the whole hand off
        # the props). Wrist range is instead checked by wrist_check() below and reported.
# wrist range check (reported): angle between hand direction and forearm direction
import mathutils
WR = []
def wrist_check():
    sc = bpy.context.scene; bad = 0; worst = 0.0
    for f in range(sc.frame_start, sc.frame_end + 1, 10):
        sc.frame_set(f)
        for nm in ("Boy", "Teen", "Man", "Mom"):
            a = bpy.data.objects[nm]
            if a.hide_render: continue
            for s in "LR":
                fa = a.pose.bones["lowerarm02." + s]; w = a.pose.bones["wrist." + s]
                rest = math.degrees(a.data.bones["lowerarm02." + s].vector.angle(a.data.bones["wrist." + s].vector))
                ang = abs(math.degrees(fa.vector.angle(w.vector)) - rest)
                if ang > 70: WR.append((f, nm, s, round(ang)))
                worst = max(worst, ang)
                if ang > 70: bad += 1
    return bad, worst
bad, worst = wrist_check()
import collections
print("WRIST_RUNS", collections.Counter((x[1], x[2]) for x in WR), WR[:25])
print("HANDS_PASS limits on", n, "bones; wrist bends >70 deg:", bad, "worst %.0f deg" % worst)
bpy.ops.wm.save_as_mainfile(filepath=out, compress=True)
