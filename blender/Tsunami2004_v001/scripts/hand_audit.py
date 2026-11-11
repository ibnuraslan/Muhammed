"""Hand audit (client rule, 23:00 UTC).  blender -b film.blend --python hand_audit.py -- <report.txt> [step=2]
For every person in view, every <step> frames, BVH overlap of:
  HAND_HAND    left hand vs right hand
  HAND_TORSO   hand vs own torso / hips / legs
  HAND_HEAD    hand vs own head / neck
  HAND_CLOTHES hand vs own clothes (sleeve and cuff faces that are weighted to the forearm/hand are excluded)
  HAND_OTHER   hand vs another person's body
"""
import sys
import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from bpy_extras.object_utils import world_to_camera_view
argv = sys.argv[sys.argv.index("--") + 1:]
OUT = argv[0]; STEP = int(argv[1]) if len(argv) > 1 else 2
sc = bpy.context.scene; cam = sc.camera
rigs = [o for o in bpy.data.objects if o.type == 'ARMATURE' and any(c.name.endswith(".body") for c in o.children)]
def body_of(r): return next(c for c in r.children if c.name.endswith(".body"))
def clothes_of(r): return [c for c in r.children if c.type == 'MESH' and "suit" in c.name]
def mask(ob, keys, thr=0.4):
    names = {g.index: g.name for g in ob.vertex_groups}
    m = np.zeros(len(ob.data.vertices), bool)
    for v in ob.data.vertices:
        w = sum(g.weight for g in v.groups if any(k in names[g.group] for k in keys))
        m[v.index] = w > thr
    return m
HAND = ("wrist", "finger", "metacarpal")
M = {}
for r in rigs:
    b = body_of(r)
    hl = mask(b, tuple(k + "" for k in HAND)) & mask(b, (".L",), 0.01) if False else None
    names = {g.index: g.name for g in b.vertex_groups}
    L = np.zeros(len(b.data.vertices), bool); Rr = np.zeros(len(b.data.vertices), bool)
    for v in b.data.vertices:
        wl = sum(g.weight for g in v.groups if any(k in names[g.group] for k in HAND) and names[g.group].endswith(".L"))
        wr = sum(g.weight for g in v.groups if any(k in names[g.group] for k in HAND) and names[g.group].endswith(".R"))
        L[v.index] = wl > 0.5; Rr[v.index] = wr > 0.5
    torso = mask(b, ("spine", "pelvis", "upperleg", "breast", "root"))
    head = mask(b, ("head", "neck", "jaw"))
    cl = [(c, ~mask(c, ("lowerarm", "wrist", "finger", "metacarpal"), 0.2)) for c in clothes_of(r)]
    M[r.name] = (L, Rr, torso, head, cl)
def world(ob, dg):
    ev = ob.evaluated_get(dg); me = ev.to_mesh()
    co = np.zeros(len(me.vertices) * 3); me.vertices.foreach_get("co", co); co = co.reshape(-1, 3)
    Mw = np.array(ob.matrix_world); co = co @ Mw[:3, :3].T + Mw[:3, 3]
    tris = [tuple(p.vertices) for p in me.polygons]; ev.to_mesh_clear(); return co, tris
def sub(co, tris, m):
    k = [t for t in tris if all(m[i] for i in t)]
    return BVHTree.FromPolygons([tuple(c) for c in co], k) if k else None
def in_view(p):
    v = world_to_camera_view(sc, cam, p); return 0 <= v.x <= 1 and -0.1 <= v.y <= 1.1 and 0 < v.z < 60
hits = {}
def flag(k, f, msg): hits.setdefault(k, []).append((f, msg))
for f in range(sc.frame_start, sc.frame_end + 1, STEP):
    sc.frame_set(f); dg = bpy.context.evaluated_depsgraph_get()
    live = [r for r in rigs if not body_of(r).hide_render and in_view(r.matrix_world @ r.pose.bones["root"].head)]
    if not live: continue
    data = {}
    for r in live:
        co, tris = world(body_of(r), dg); data[r.name] = (co, tris)
    for r in live:
        co, tris = data[r.name]; L, Rr, torso, head, cl = M[r.name]
        hL, hR = sub(co, tris, L), sub(co, tris, Rr)
        if hL and hR and len(hL.overlap(hR)) > 0: flag("HAND_HAND", f, r.name)
        for nm, hb in (("L", hL), ("R", hR)):
            if not hb: continue
            for key, mk in (("HAND_TORSO", torso), ("HAND_HEAD", head)):
                tb = sub(co, tris, mk)
                if tb and len(hb.overlap(tb)) > 0: flag(key, f, "%s %s" % (r.name, nm))
            for c, cm in cl:
                cco, ctr = world(c, dg); cb = sub(cco, ctr, cm)
                if cb and len(hb.overlap(cb)) > 0: flag("HAND_CLOTHES", f, "%s %s %s" % (r.name, nm, c.name))
            root = r.matrix_world @ r.pose.bones["root"].head
            for r2 in live:
                if r2 is r or (r2.matrix_world @ r2.pose.bones["root"].head - root).length > 2.0: continue
                co2, tr2 = data[r2.name]
                if len(hb.overlap(BVHTree.FromPolygons([tuple(c) for c in co2], tr2))) > 0: flag("HAND_OTHER", f, "%s %s x %s" % (r.name, nm, r2.name))
with open(OUT, "w") as fh:
    fh.write("Tsunami2004 hand audit, every %d frames, people in view\n" % STEP); tot = 0
    for k in ("HAND_HAND", "HAND_TORSO", "HAND_HEAD", "HAND_CLOTHES", "HAND_OTHER"):
        v = hits.get(k, []); tot += len(v); fh.write("%-14s %4d\n" % (k, len(v)))
        for f, m in v[:40]: fh.write("    f%4d (%.2fs) %s\n" % (f, (f - 1) / 60, m))
    fh.write("TOTAL %d\n" % tot)
print(open(OUT).read())
