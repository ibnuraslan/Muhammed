"""BVH hand audit (client rule, Nov 11 23:00).  blender -b film.blend --python hands_audit.py -- <report.txt> [step_diver=2] [step_others=4]
For every MPFB character, every <step> frames:
  HAND_HAND    left-hand points inside the right hand (and vice versa)          > 4 mm deep
  HAND_TORSO   hand points inside its own torso / head (body minus hands and forearms)  > 4 mm
  HAND_CLOTH   hand points inside its own clothes                                > 4 mm
  HAND_OTHER   diver hands inside the beluga or its jaw; keeper hands inside the buoy  > 4 mm
Uses the handL/handR/forearm point attributes written by 04_hand_limits.py (they survive mask + subdivision)."""
import sys, bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index("--") + 1:]; OUT = a[0]
STEP_D = int(a[1]) if len(a) > 1 else 2; STEP_O = int(a[2]) if len(a) > 2 else 4
sc = bpy.context.scene
RIGS = [o for o in bpy.data.objects if o.type == 'ARMATURE' and o.name in ("Diver", "Keeper", "SpecA", "SpecB", "SpecC", "SpecD", "SpecE", "SpecF", "SpecG")]
EPS = 0.004
hits = {}; frames = {}
def flag(kind, who, f, n):
    hits[(kind, who)] = hits.get((kind, who), 0) + n
    frames.setdefault((kind, who), []).append(f)
def world_bvh(o, dg, keep=None):
    e = o.evaluated_get(dg); me = e.to_mesh(); M = o.matrix_world
    vs = [M @ v.co for v in me.vertices]
    polys = [list(p.vertices) for p in me.polygons if keep is None or keep(p)]
    e.to_mesh_clear()
    return BVHTree.FromPolygons(vs, polys) if polys else None
def inside(t, p):
    if t is None: return False
    loc, nrm, i, d = t.find_nearest(p, 0.04)        # open shells: only near-surface penetration is meaningful
    return loc is not None and (p - loc).dot(nrm) < -EPS
for f in range(sc.frame_start, sc.frame_end + 1, 1):
    who_now = [r for r in RIGS if (f - 1) % (STEP_D if r.name == "Diver" else STEP_O) == 0]
    if not who_now: continue
    sc.frame_set(f); dg = bpy.context.evaluated_depsgraph_get()
    for rig in who_now:
        if rig.name != "Diver" and all(ch.hide_render for ch in rig.children if ch.type == 'MESH'): continue
        body = next(ch for ch in rig.children if ch.type == 'MESH' and ch.name.endswith(".body"))
        e = body.evaluated_get(dg); me = e.to_mesh(); M = body.matrix_world
        HL = me.attributes.get("handL"); HR = me.attributes.get("handR"); FA = me.attributes.get("forearm")
        if HL is None: e.to_mesh_clear(); continue
        hl = [0.0] * len(me.vertices); hr = hl[:]; fa = hl[:]
        HL.data.foreach_get("value", hl); HR.data.foreach_get("value", hr); FA.data.foreach_get("value", fa)
        vs = [M @ v.co for v in me.vertices]
        Lp = [vs[i] for i in range(len(vs)) if hl[i] > 0.9][::2]; Rp = [vs[i] for i in range(len(vs)) if hr[i] > 0.9][::2]
        tor = [list(p.vertices) for p in me.polygons if all(hl[i] < 0.1 and hr[i] < 0.1 and fa[i] < 0.1 for i in p.vertices)]
        lpoly = [list(p.vertices) for p in me.polygons if all(hl[i] > 0.5 for i in p.vertices)]
        rpoly = [list(p.vertices) for p in me.polygons if all(hr[i] > 0.5 for i in p.vertices)]
        e.to_mesh_clear()
        T = BVHTree.FromPolygons(vs, tor); TL = BVHTree.FromPolygons(vs, lpoly) if lpoly else None; TR = BVHTree.FromPolygons(vs, rpoly) if rpoly else None
        n = sum(1 for p in Lp if inside(TR, p)) + sum(1 for p in Rp if inside(TL, p))
        if n: flag("HAND_HAND", rig.name, f, n)
        n = sum(1 for p in Lp + Rp if inside(T, p))
        if n: flag("HAND_TORSO", rig.name, f, n)
        for ch in rig.children:
            if ch.type == 'MESH' and any(k in ch.name for k in ("suit", "casual", "elegant", "worksuit")) and not ch.hide_render:
                wr_ = [rig.matrix_world @ rig.pose.bones["wrist." + s_].head for s_ in "LR"]
                hp = [p for p in Lp + Rp if min((p - w).length for w in wr_) > 0.05]       # the wrist under a sleeve cuff is fine
                tc = world_bvh(ch, dg); n = sum(1 for p in hp if inside(tc, p) and (tc.find_nearest(p, 0.04)[3] or 0) > 0.01)
                if n: flag("HAND_CLOTH", rig.name, f, n)
        others = []
        if rig.name == "Diver": others = [bpy.data.objects["Beluga"], bpy.data.objects["Beluga_Jaw"]]
        if rig.name == "SpecF" and "RingBuoy" in bpy.data.objects: others = [bpy.data.objects["RingBuoy"]]
        for o in others:
            to = world_bvh(o, dg); n = sum(1 for p in Lp + Rp if inside(to, p))
            if n: flag("HAND_OTHER", rig.name + "/" + o.name, f, n)
lines = ["HAND AUDIT (diver every %d frames, others every %d; depth > %.0f mm)" % (STEP_D, STEP_O, EPS * 1000)]
total = 0
for (k, w), n in sorted(hits.items()):
    fr = frames[(k, w)]; total += n
    lines.append("%-11s %-22s %5d samples in %4d frames, frames %d-%d" % (k, w, n, len(fr), fr[0], fr[-1]))
lines.append("HAND AUDIT TOTAL: %d samples in %d flagged frame-checks" % (total, sum(len(v) for v in frames.values())))
open(OUT, "w").write("\n".join(lines) + "\n"); print("\n".join(lines))
