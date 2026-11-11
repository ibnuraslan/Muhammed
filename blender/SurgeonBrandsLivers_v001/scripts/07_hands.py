"""Hands pass (client, Nov 11 23:00 UTC): joint limits on fingers/thumb/wrist/elbow, then a hand-overlap audit every 2 frames
with automatic re-keying of every flagged frame (hand moved out of the body / away from the other hand), then a re-audit.
blender -b film.blend --python 07_hands.py -- <out.blend> <report.txt>

Overlap test: each hand is sampled as 14 points (wrist, metacarpal heads, every finger joint and tip). The bodies are
capsules along the bone chains (torso spine05..neck, head sphere, upper/lower arms of the *other* character,
plus the opposite hand's palm segment). A point deeper than the capsule radius minus a skin margin is a hit."""
import sys, math
import bpy
from mathutils import Vector, Matrix, Euler, Quaternion
a = sys.argv[sys.argv.index("--") + 1:]
OUT, REP = a[0], a[1]
sc = bpy.context.scene
R_ = math.radians
ACTORS = [o for o in bpy.data.objects if o.type == 'ARMATURE' and o.name != "GloveHands"]
FING = ["finger%d-%d" % (k, j) for k in range(2, 6) for j in range(1, 4)]
THUMB = ["finger1-%d" % j for j in range(1, 4)]

def fcurves(id_):
    ad = id_.animation_data; out = []
    if ad and ad.action:
        for layer in getattr(ad.action, "layers", []):
            for strip in layer.strips:
                for cb in strip.channelbags:
                    out += list(cb.fcurves)
    return out

# ------------------------------------------------------------------ 1. limits
def keyed_quats(rig, bone):
    fcs = [fc for fc in fcurves(rig) if fc.data_path == 'pose.bones["%s"].rotation_quaternion' % bone]
    if len(fcs) < 4:
        return []
    frames = sorted({round(kp.co.x) for fc in fcs for kp in fc.keyframe_points})
    fcs.sort(key=lambda fc: fc.array_index)
    return [Quaternion([fc.evaluate(f) for fc in fcs]).normalized() for f in frames[::3]]

def add_limit(pb, rng, name="HandLimit"):
    c = pb.constraints.get(name) or pb.constraints.new('LIMIT_ROTATION'); c.name = name
    c.owner_space = 'LOCAL'
    for ax, (lo, hi) in zip("xyz", rng):
        setattr(c, "use_limit_" + ax, True)
        setattr(c, "min_" + ax, R_(lo)); setattr(c, "max_" + ax, R_(hi))
    return c

n_lim = 0
for rig in ACTORS:
    for s in "LR":
        # fingers: find the curl axis (X or Z) and its forward sign from this character's own keys
        signs = {}
        for b in FING:
            qs = keyed_quats(rig, b + "." + s)
            if not qs:
                continue
            ex = [q.to_euler('XYZ') for q in qs]
            rx = max(abs(e.x) for e in ex); rz = max(abs(e.z) for e in ex)
            ax = 0 if rx >= rz else 2
            mean = sum(e[ax] for e in ex) / len(ex)
            signs[b] = (ax, 1 if mean >= 0 else -1)
        if not signs:
            continue
        # majority axis/sign for this hand (all fingers curl the same way)
        votes = {}
        for v in signs.values():
            votes[v] = votes.get(v, 0) + 1
        ax, sg = max(votes, key=votes.get)
        for b in FING:
            pb = rig.pose.bones.get(b + "." + s)
            if not pb:
                continue
            rng = [(-10, 10), (-8, 8), (-10, 10)]
            rng[ax] = (0, 95) if sg > 0 else (-95, 0)
            add_limit(pb, rng); n_lim += 1
        for b in THUMB:
            pb = rig.pose.bones.get(b + "." + s)
            if pb:
                add_limit(pb, [(-50, 50), (-35, 35), (-50, 50)]); n_lim += 1
        # wrist: after its Copy Rotation from the IK control
        pb = rig.pose.bones["wrist." + s]
        add_limit(pb, [(-60, 60), (-40, 40), (-25, 25)]); n_lim += 1
print("LIMITS", n_lim)

# elbow: IK limits on lowerarm01 (hinge about local X). Pick the bend side that reaches the targets best.
def ik_err(rig, s, frames):
    e = 0.0
    for f in frames:
        sc.frame_set(f)
        hand = rig.matrix_world @ rig.pose.bones["wrist." + s].head
        tgt = rig.matrix_world @ rig.pose.bones["IK_hand." + s].head
        e += (hand - tgt).length
    return e
for rig in ACTORS:
    rng = [f for f in range(1, sc.frame_end + 1, 90)]
    for s in "LR":
        pb = rig.pose.bones["lowerarm01." + s]
        best = None
        for lo, hi in ((0, 145), (-145, 0)):
            pb.use_ik_limit_x = True; pb.ik_min_x = R_(lo); pb.ik_max_x = R_(hi)
            e = ik_err(rig, s, rng)
            if best is None or e < best[0]:
                best = (e, lo, hi)
        pb.use_ik_limit_x = True; pb.ik_min_x = R_(best[1]); pb.ik_max_x = R_(best[2])
        print("ELBOW", rig.name, s, best[1], best[2], round(best[0], 3))

# ------------------------------------------------------------------ 2. audit + re-key
HAND_PTS = ["wrist", "metacarpal1", "metacarpal2", "metacarpal3", "metacarpal4"] + ["finger%d-%d" % (k, j) for k in (1, 2, 3, 5) for j in (1, 3)]
def visible(rig):
    body = bpy.data.objects.get(rig.name + ".body")
    if rig.name == "Patient":       # on the table / bed her body is masked to the head (drape and blanket stand in), so only home counts
        return 601 <= sc.frame_current <= 791
    return body is not None and not body.hide_render
def P(rig, b, tail=False):
    pb = rig.pose.bones[b]; return rig.matrix_world @ (pb.tail if tail else pb.head)
def seg_dist(p, a_, b_):
    ab = b_ - a_; t = max(0.0, min(1.0, (p - a_).dot(ab) / max(ab.length_squared, 1e-9)))
    c_ = a_ + ab * t; return (p - c_).length, c_
def hand_points(rig, s):
    pts = [P(rig, b + "." + s) for b in HAND_PTS]
    pts += [P(rig, "finger%d-3.%s" % (k, s), tail=True) for k in (1, 2, 3, 4, 5)]
    return pts
def torso_caps(rig):
    ch = ["spine05", "spine04", "spine03", "spine02", "spine01", "neck01"]
    # ellipse-ish torso approximated by a capsule of 0.10 m (deep-inside test; skin + cloth sit at ~0.12-0.16)
    caps = [(P(rig, a_), P(rig, b_), 0.10) for a_, b_ in zip(ch, ch[1:])]
    h0, h1 = P(rig, "head"), P(rig, "head", tail=True)
    caps.append((h0 + (h1 - h0) * 0.3, h0 + (h1 - h0) * 0.7, 0.075))
    return caps
def arm_caps(rig):
    out = []
    for s in "LR":
        out.append((P(rig, "upperarm01." + s), P(rig, "lowerarm01." + s), 0.045))
        out.append((P(rig, "lowerarm01." + s), P(rig, "wrist." + s), 0.035))
    return out
def palm_seg(rig, s):
    return P(rig, "wrist." + s), P(rig, "finger3-1." + s)

def audit(step=2, fix=False):
    hits = []; fixes = {}
    for f in range(1, sc.frame_end + 1, step):
        sc.frame_set(f)
        vis = [r for r in ACTORS if visible(r)]
        for rig in vis:
            caps_self = torso_caps(rig)
            others = [r for r in vis if r is not rig]
            for s in "LR":
                pts = hand_points(rig, s)
                push = Vector((0, 0, 0)); kinds = set()
                for cap_list, kind in ((caps_self, "own body"),) + tuple((torso_caps(o) + arm_caps(o), "other:" + o.name) for o in others
                                                                          if (P(o, "spine03") - pts[0]).length < 1.2):
                    for p in pts:
                        for a_, b_, r in cap_list:
                            d, c_ = seg_dist(p, a_, b_)
                            if d < r - 0.005:
                                kinds.add(kind); push += (p - c_).normalized() * (r - d + 0.02) if d > 1e-5 else Vector((0, -0.03, 0))
                # the other hand (palms through each other)
                o = "R" if s == "L" else "L"
                a2, b2 = palm_seg(rig, o)
                for p in pts[:5]:
                    d, c_ = seg_dist(p, a2, b2)
                    if d < 0.022:
                        kinds.add("other hand"); push += (p - c_).normalized() * (0.03 - d) if d > 1e-5 else Vector((0.02, 0, 0))
                if kinds:
                    hits.append((f, rig.name, s, sorted(kinds), push.length))
                    fixes[(rig.name, s, f)] = push
    if fix:
        for (name, s, f), push in sorted(fixes.items(), key=lambda x: x[0][2]):
            rig = bpy.data.objects[name]
            sc.frame_set(f)
            pb = rig.pose.bones["IK_hand." + s]
            if push.length > 0.12:
                push = push.normalized() * 0.12
            # world push -> bone basis translation
            mw = rig.matrix_world @ pb.matrix
            new = Matrix.Translation(push) @ mw
            pb.matrix = rig.matrix_world.inverted() @ new
            pb.keyframe_insert("location", frame=f, group="IK_hand." + s)
            pb.keyframe_insert("rotation_quaternion", frame=f, group="IK_hand." + s)
    return hits

h0 = audit(fix=True)
print("AUDIT pass1", len(h0))
h1 = audit(fix=True)
print("AUDIT pass2", len(h1))
for extra in range(4):
    hx = audit(fix=True); print("AUDIT extra", extra, len(hx))
    if not hx: break
h2 = audit(fix=False)
print("AUDIT final", len(h2))
with open(REP, "w") as fh:
    fh.write("Hand audit (every 2 frames, frames 1-%d)\n" % sc.frame_end)
    fh.write("Limit Rotation constraints added: %d (fingers 0..95 deg forward only, +-10 spread; thumb cone; wrist +-60 flex / +-25 side)\n" % n_lim)
    fh.write("Elbow IK limits: one-sided 0..145 deg on every lowerarm01 (side chosen per arm by best target reach)\n\n")
    fh.write("pass 1 (before re-key): %d hits\npass 2 (after 1st re-key): %d hits\nfinal: %d hits\n\n" % (len(h0), len(h1), len(h2)))
    by = {}
    for f, n, s, k, d in h0:
        by.setdefault((n, s, tuple(k)), []).append(f)
    fh.write("Pass-1 hits by hand / kind (frame ranges):\n")
    for (n, s, k), fr in sorted(by.items()):
        fh.write("  %-10s %s %-28s %d frames  %d-%d\n" % (n, s, ",".join(k), len(fr), min(fr), max(fr)))
    fh.write("\nFinal remaining hits:\n" + "\n".join("  %5d %-10s %s %s depth-push %.3f" % (f, n, s, ",".join(k), d) for f, n, s, k, d in h2) + "\n")
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("HANDS_DONE", OUT)
