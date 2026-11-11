"""Hands pass (client, Nov 11 23:00): joint limits on fingers, thumbs, wrists and elbows; relaxed minimum curl.
blender -b in.blend --python 06_hands_pass.py -- out.blend"""
import sys, math, bpy
out = sys.argv[sys.argv.index("--") + 1]
R_ = math.radians
def limit(pb, x=None, y=None, z=None, name="HandLimit"):
    c = pb.constraints.get(name) or pb.constraints.new('LIMIT_ROTATION'); c.name = name
    c.owner_space = 'LOCAL'; c.use_transform_limit = True
    for ax, rng in (("x", x), ("y", y), ("z", z)):
        on = rng is not None
        setattr(c, "use_limit_" + ax, on)
        if on: setattr(c, "min_" + ax, R_(rng[0])); setattr(c, "max_" + ax, R_(rng[1]))
    return c
n = 0
for rig in ("Inventor", "Mentor"):
    o = bpy.data.objects[rig]
    for s in "LR":
        sx = 1 if s == "L" else -1
        # elbow: IK may only bend it forward (no hyper-extension)
        for nm in ("lowerarm01." + s,):
            pb = o.pose.bones[nm]; pb.use_ik_limit_x = True; pb.ik_min_x = R_(0); pb.ik_max_x = R_(145); pb.lock_ik_y = pb.lock_ik_z = True
        # fingers: bend forward 0..90 (MPFB local +X), no backward bend, small spread/twist; relaxed floor of 6 deg
        for k in range(2, 6):
            for j in range(1, 4):
                pb = o.pose.bones["finger%d-%d.%s" % (k, j, s)]
                limit(pb, x=(6, 90), y=(-15, 15) if j == 1 else (-8, 8), z=(-12, 12)); n += 1
        # thumb: natural cone around its rest
        for j in range(1, 4):
            pb = o.pose.bones["finger1-%d.%s" % (j, s)]
            limit(pb, x=(-35, 25), y=(-40, 40), z=(-45, 45)); n += 1
        # wrist (after the IK copy-rotation): flex +-60, side +-25, twist +-45
        pb = o.pose.bones["wrist." + s]
        limit(pb, x=(-70, 70), y=(-90, 90), z=(-30, 30)); n += 1   # y = pronation proxy (forearm twist is locked in the IK)
print("HANDLIMITS", n)
bpy.ops.wm.save_as_mainfile(filepath=out, compress=True)
