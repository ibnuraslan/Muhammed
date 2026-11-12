"""Hand pass: Limit Rotation (local space) on every finger, thumb and wrist bone of every MPFB character, chosen from the
bend direction the animation actually uses (so no backward bends, little side spread); IK elbows get a no-hyperextension
limit on the lower arm.  Also writes float attributes handL/handR/forearm on each body for hands_audit.py.
blender -b film.blend --python 04_hand_limits.py -- <out.blend>"""
import bpy, sys, math
from mathutils import Quaternion
OUT = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene
R_ = math.radians
RIGS = [o for o in bpy.data.objects if o.type == 'ARMATURE' and o.name in ("Diver", "Keeper", "SpecA", "SpecB", "SpecC", "SpecD", "SpecE", "SpecF", "SpecG")]
SAMPLE = list(range(1, sc.frame_end + 1, 40))
n_con = 0
import os
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "pipeline", "hand_poses.py")).read())
for rig in RIGS:
    add_hand_limits(rig); n_con += 1
    names = []      # shared library limits replace the per-animation limits below [b.name for b in rig.pose.bones if b.name.startswith(("finger", "wrist."))]
    # local rotation the animation uses, per bone, sampled over the film
    used = {n: [] for n in names}
    for f in SAMPLE:
        sc.frame_set(f)
        for n in names:
            pb = rig.pose.bones[n]
            q = pb.rotation_quaternion if pb.rotation_mode == 'QUATERNION' else pb.rotation_euler.to_quaternion()
            used[n].append(q.to_euler('XYZ'))
    for n in names:
        pb = rig.pose.bones[n]
        e = used[n]
        lo = [min(v[i] for v in e) for i in range(3)]; hi = [max(v[i] for v in e) for i in range(3)]
        c = pb.constraints.new('LIMIT_ROTATION'); c.owner_space = 'LOCAL'; c.name = "HandLimit"
        c.use_limit_x = c.use_limit_y = c.use_limit_z = True
        if n.startswith("wrist."):
            c.min_x, c.max_x = R_(-60), R_(60); c.min_y, c.max_y = R_(-40), R_(40); c.min_z, c.max_z = R_(-25), R_(25)
            for i, ax in enumerate("xyz"):          # never clip what the animation already does
                setattr(c, "min_" + ax, min(getattr(c, "min_" + ax), lo[i])); setattr(c, "max_" + ax, max(getattr(c, "max_" + ax), hi[i]))
        else:
            # dominant bend axis = the one the animation rotates most; allow 0..90 deg in that direction only
            span = [max(abs(lo[i]), abs(hi[i])) for i in range(3)]
            k = max(range(3), key=lambda i: span[i]); sgn = 1 if abs(hi[k]) >= abs(lo[k]) else -1
            thumb = n.startswith("finger1")
            for i, ax in enumerate("xyz"):
                if i == k:
                    a, b = (0.0, R_(90)) if sgn > 0 else (R_(-90), 0.0)
                    a = min(a, lo[i]); b = max(b, hi[i])
                else:
                    side = R_(30 if thumb else 10)
                    a, b = min(-side, lo[i]), max(side, hi[i])
                setattr(c, "min_" + ax, a); setattr(c, "max_" + ax, b)
        n_con += 1
    # elbows: the IK chain may not hyper-extend
    for s in "LR":
        pb = rig.pose.bones.get("lowerarm01." + s)
        if pb:
            pb.use_ik_limit_x = True; pb.ik_min_x = R_(-145); pb.ik_max_x = R_(145)
    # attributes for the hand audit
    body = next((ch for ch in rig.children if ch.type == 'MESH' and ch.name.endswith(".body")), None)
    if body:
        gn = {g.index: g.name for g in body.vertex_groups}
        hl, hr, fa = [], [], []
        for v in body.data.vertices:
            gs = [(gn[g.group], g.weight) for g in v.groups if gn[g.group] in rig.data.bones]
            nm = max(gs, key=lambda x: x[1])[0] if gs else ""
            hand = nm.startswith(("wrist", "finger", "metacarpal"))
            hl.append(1.0 if hand and nm.endswith(".L") else 0.0); hr.append(1.0 if hand and nm.endswith(".R") else 0.0)
            fa.append(1.0 if nm.startswith(("lowerarm", "upperarm02")) else 0.0)
        for nm, vals in (("handL", hl), ("handR", hr), ("forearm", fa)):
            a = body.data.attributes.get(nm) or body.data.attributes.new(nm, 'FLOAT', 'POINT'); a.data.foreach_set("value", vals)
print("HAND_LIMITS constraints", n_con, "on", len(RIGS), "rigs")
bpy.ops.wm.save_as_mainfile(filepath=OUT)
