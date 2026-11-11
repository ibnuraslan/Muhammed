"""Contact audit for PrisonKeyCake: feet hover/sink, IK reach (hand/foot target vs actual), hidden-state aware.
blender -b film.blend --python audit_contacts.py -- [step]"""
import sys, bpy
from mathutils import Vector
a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
STEP = int(a[0]) if a else 4
sc = bpy.context.scene
ACT = ["Prisoner", "Visitor", "Guard", "CrowdB", "YardP1", "YardP2", "Guard2"]
FLOOR = lambda x, y: 0.004 if (-2.0 <= x <= 2.0 and -2.0 <= y <= 2.0) or (2.35 <= x <= 8.2 and -0.9 <= y <= 0.9) or (13.0 <= x <= 21 and 2 <= y <= 10) else 0.0
issues = {}
def add(k, f, msg):
    issues.setdefault(k, []).append((f, msg))
shoes = {n: [c for c in bpy.data.objects[n].children if "shoes" in c.name][0] for n in ACT}
for f in range(1, 1891, STEP):
    sc.frame_set(f); dg = bpy.context.evaluated_depsgraph_get()
    for n in ACT:
        rig = bpy.data.objects[n]
        if rig.hide_render: continue
        sh = shoes[n].evaluated_get(dg); me = sh.to_mesh(); M = sh.matrix_world
        pts = [M @ v.co for v in me.vertices]; sh.to_mesh_clear()
        # split shoes by side of the armature root (x in rig local after yaw): use the two foot bones
        for s in "LR":
            fb = rig.pose.bones["foot." + s]; c = rig.matrix_world @ fb.head
            near = [p for p in pts if (p.xy - c.xy).length < 0.16]
            if not near: continue
            lo = min(p.z for p in near); g = FLOOR(c.x, c.y)
            if lo - g < -0.02: add(n, f, "%s foot sinks %.3f" % (s, lo - g))
            sb = rig.pose.bones["foot." + s]
        lows = []
        for s in "LR":
            c = rig.matrix_world @ rig.pose.bones["foot." + s].head
            near = [p for p in pts if (p.xy - c.xy).length < 0.16]
            if near: lows.append(min(p.z for p in near) - FLOOR(c.x, c.y))
        if lows and min(lows) > 0.03: add(n, f, "both feet off the ground %.3f" % min(lows))
        for s in "LR":
            for tgt, bone in (("IK_hand." + s, "wrist." + s), ("IK_foot." + s, "foot." + s)):
                if tgt not in rig.pose.bones: continue
                d = (rig.pose.bones[tgt].head - rig.pose.bones[bone].head).length
                if d > 0.03: add(n, f, "%s unreachable by %.3f" % (tgt, d))
for n, L in issues.items():
    print("CONTACT", n, len(L), "issues")
    by = {}
    for f, m in L:
        key = m.split(" by ")[0].split(" sinks")[0].split(" off")[0]
        by.setdefault(key, []).append((f, float(m.split()[-1])))
    for key, v in by.items():
        runs = []
        for f, val in v:
            if runs and f - runs[-1][1] <= STEP: runs[-1][1] = f; runs[-1][2] = max(runs[-1][2], abs(val))
            else: runs.append([f, f, abs(val)])
        print("   ", key, " ".join("%d-%d(%.2f)" % tuple(r) for r in runs))
print("CONTACT done")
