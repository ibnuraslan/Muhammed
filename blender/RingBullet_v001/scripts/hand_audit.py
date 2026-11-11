"""Hand audit (client rule, Nov 11 23:00): BVH overlap every N frames of
  each hand vs the other hand, each hand vs own torso/head (skin), each hand (fingers) vs own clothes, each hand vs other characters.
blender -b film.blend --python hand_audit.py -- <report.txt> [step=2]
Skin is evaluated without subsurf/mask (index-aligned cage) so vertex groups select hands and torso exactly."""
import sys
import bpy
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index("--") + 1:]; REP = a[0]; STEP = int(a[1]) if len(a) > 1 else 2
F0 = int(a[2]) if len(a) > 2 else None; F1 = int(a[3]) if len(a) > 3 else None
sc = bpy.context.scene; O = bpy.data.objects
CHARS = [n for n in ("Owner", "Robber", "Officer") if n in O]

def groups(body):
    VG = {g.index: g.name for g in body.vertex_groups}
    hand = {"L": set(), "R": set()}; fing = {"L": set(), "R": set()}; torso = set()
    for v in body.data.vertices:
        for g in v.groups:
            n = VG.get(g.group, ""); w = g.weight
            if w < 0.5: continue
            if n.startswith(("finger", "wrist", "metacarpal")) and n[-2:] in (".L", ".R"):
                hand[n[-1]].add(v.index)
                if n.startswith("finger") and not n.startswith("finger1-1"): fing[n[-1]].add(v.index)   # fingers only: the cuff legitimately rests on the back of the hand and the thumb base
            elif n.startswith(("spine", "pelvis", "breast", "neck", "head", "jaw", "clavicle")):
                torso.add(v.index)
    return hand, fing, torso

INFO = {c: groups(O[c + ".body"]) for c in CHARS}
def cage(body):
    mods = [m for m in body.modifiers if m.type in ('SUBSURF', 'MASK')]
    for m in mods: m.show_viewport = False
    dg = bpy.context.evaluated_depsgraph_get(); e = body.evaluated_get(dg); me = e.to_mesh()
    V = [e.matrix_world @ v.co for v in me.vertices]; P = [tuple(p.vertices) for p in me.polygons]
    e.to_mesh_clear()
    for m in mods: m.show_viewport = True
    return V, P
def sub_bvh(V, P, sel):
    ps = [p for p in P if all(i in sel for i in p)]
    return BVHTree.FromPolygons(V, ps) if ps else None
def mesh_bvh(o):
    dg = bpy.context.evaluated_depsgraph_get(); e = o.evaluated_get(dg); me = e.to_mesh()
    V = [e.matrix_world @ v.co for v in me.vertices]; P = [tuple(p.vertices) for p in me.polygons]; e.to_mesh_clear()
    return BVHTree.FromPolygons(V, P)

counts = {}; lines = []; flagged = set()
def flag(kind, f, n):
    counts[kind] = counts.get(kind, 0) + 1; flagged.add(f)
    if counts[kind] <= 400: lines.append("F%4d %-22s %d tri pairs" % (f, kind, n))
for f in range(F0 or sc.frame_start, (F1 or sc.frame_end) + 1, STEP):
    sc.frame_set(f)
    vis = [c for c in CHARS if not O[c + ".body"].hide_render and not O[c].hide_render]
    data = {}
    for c in vis:
        body = O[c + ".body"]; V, P = cage(body); hand, fing, torso = INFO[c]
        data[c] = dict(V=V, P=P, H={s: sub_bvh(V, P, hand[s]) for s in "LR"}, F={s: sub_bvh(V, P, fing[s]) for s in "LR"},
                       T=sub_bvh(V, P, torso))
    for c in vis:
        d = data[c]
        if d["H"]["L"] and d["H"]["R"]:
            ov = d["H"]["L"].overlap(d["H"]["R"])
            if ov: flag("%s hand_vs_hand" % c, f, len(ov))
        for s in "LR":
            if d["H"][s] and d["T"]:
                ov = d["H"][s].overlap(d["T"])
                if ov: flag("%s hand%s_vs_torso" % (c, s), f, len(ov))
        if c == "Owner":
            for cl in [o for o in O if o.name.startswith(c + ".") and any(k in o.name for k in ("suit", "worksuit"))]:
                cb = mesh_bvh(cl)
                for s in "LR":
                    if d["F"][s]:
                        ov = d["F"][s].overlap(cb)
                        if len(ov) > 2: flag("%s fingers%s_vs_clothes" % (c, s), f, len(ov))
        for c2 in vis:
            if c2 == c: continue
            other = BVHTree.FromPolygons(data[c2]["V"], data[c2]["P"])
            for s in "LR":
                if d["H"][s]:
                    ov = d["H"][s].overlap(other)
                    if ov: flag("%s hand%s_vs_%s" % (c, s, c2), f, len(ov))
out = ["Hand audit, step %d, frames %d-%d" % (STEP, sc.frame_start, sc.frame_end),
       "HAND_COUNTS " + (str(counts) if counts else "none"), "FLAGGED_FRAMES %d %s" % (len(flagged), sorted(flagged)[:80])] + lines
open(REP, "w").write("\n".join(out) + "\n"); print("\n".join(out[:3]))
