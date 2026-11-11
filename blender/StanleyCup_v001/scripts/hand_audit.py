"""Hand audit (BVH overlap), STYLE_ANIMATED.md "Hands". blender -b film.blend --python hand_audit.py -- [step] [f0] [f1]
Pairs checked each frame: hand vs other hand; hand vs own torso/head (body) and own clothes (minus that arm's sleeve);
hand vs the other character (body + clothes). Hand = finger + metacarpal + palm (wrist) polygons of the body mesh."""
import sys, bpy
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
STEP = int(a[0]) if a else 2
sc = bpy.context.scene
F0 = int(a[1]) if len(a) > 1 else sc.frame_start; F1 = int(a[2]) if len(a) > 2 else sc.frame_end
CH = {"Woman": ("Woman.body", "Woman.female_elegantsuit01"), "Fiance": ("Fiance.body", "Fiance.male_casualsuit05")}
HAND_KEYS = ("finger", "metacarpal", "wrist")
TORSO_KEYS = ("spine", "neck", "head", "jaw", "clavicle", "breast", "pelvis", "root", "special", "oris", "levator", "orbicularis", "oculi", "temporalis", "risorius", "eye", "tongue")
def groups(ob, keys, side=None):
    out = set()
    for g in ob.vertex_groups:
        n = g.name
        if any(n.startswith(k) for k in keys) and (side is None or n.endswith("." + side) or "." not in n or not n[-2:] in (".L", ".R")):
            if side is not None and not n.endswith("." + side): continue
            out.add(g.index)
    return out
def vsets(ob, gidx, thr=0.4):
    """vertices of the visible body only (MPFB 'body' group; not helpers, not skin hidden under clothes)"""
    keep = ob.vertex_groups.get("body"); hide = {g.index for g in ob.vertex_groups if g.name.startswith("Delete.")}
    out = set()
    for v in ob.data.vertices:
        gs = {g.group: g.weight for g in v.groups}
        if keep is not None and gs.get(keep.index, 0) < 0.5: continue
        if any(gs.get(h, 0) > 0.5 for h in hide): continue
        if any(gs.get(g, 0) > thr for g in gidx): out.add(v.index)
    return out
HANDV = {}
def tree(ob, mask, dg, keep_verts=None):
    e = ob.evaluated_get(dg); me = e.to_mesh(); M = ob.matrix_world
    vs = [M @ v.co for v in me.vertices]
    n = len(ob.data.vertices)
    polys = [p.vertices[:] for p in me.polygons if (mask is None or all(i < n and i in mask for i in p.vertices))]
    if keep_verts is not None: HANDV[keep_verts] = [vs[i] for i in mask]
    e.to_mesh_clear()
    return BVHTree.FromPolygons(vs, polys) if polys else None
DEPTH = 0.006   # a hand resting on skin/cloth touches it; > 6 mm inside counts as penetration
def pen_depth(key, t):
    """deepest hand vertex behind the target surface (signed distance along the surface normal)"""
    d = 0.0
    for v in HANDV[key]:
        loc, nrm, idx, dist = t.find_nearest(v, 0.05)
        if loc is not None and (v - loc).dot(nrm) < 0: d = max(d, dist)
    return d
# masks (computed on the base mesh; evaluated meshes keep vertex order because subdiv is off in the viewport for the audit)
for o in bpy.data.objects:
    for m in o.modifiers:
        if m.type in ("SUBSURF", "MASK"): m.show_viewport = False     # keep vertex indices = base mesh
MASK = {}
for c, (body, cloth) in CH.items():
    b = bpy.data.objects[body]; cl = bpy.data.objects[cloth]
    for s in "LR":
        MASK[(c, "hand", s)] = vsets(b, {g.index for g in b.vertex_groups if g.name.endswith("." + s) and g.name.startswith(HAND_KEYS)})
        # clothes minus this arm (sleeve) so the cuff around the wrist is not a hit
        arm = {g.index for g in cl.vertex_groups if g.name.endswith("." + s) and g.name.startswith(("upperarm", "lowerarm", "wrist", "shoulder", "clavicle", "finger", "metacarpal"))}
        MASK[(c, "cloth_no", s)] = {v.index for v in cl.data.vertices if not any(g.group in arm and g.weight > 0.05 for g in v.groups)}
    MASK[(c, "torso")] = vsets(b, {g.index for g in b.vertex_groups if g.name.startswith(TORSO_KEYS)})
    MASK[(c, "visible")] = vsets(b, {g.index for g in b.vertex_groups}, 0.0)
hits = []; touches = []
for f in range(F0, F1 + 1, STEP):
    sc.frame_set(f); dg = bpy.context.evaluated_depsgraph_get()
    T = {}
    for c, (body, cloth) in CH.items():
        b = bpy.data.objects[body]; cl = bpy.data.objects[cloth]
        for s in "LR":
            T[(c, "hand", s)] = tree(b, MASK[(c, "hand", s)], dg, keep_verts=(c, s))
            T[(c, "cloth_no", s)] = tree(cl, MASK[(c, "cloth_no", s)], dg)
        T[(c, "torso")] = tree(b, MASK[(c, "torso")], dg)
        T[(c, "all")] = [tree(b, MASK[(c, "visible")], dg), tree(cl, None, dg)]
    for c in CH:
        other = "Fiance" if c == "Woman" else "Woman"
        hL, hR = T[(c, "hand", "L")], T[(c, "hand", "R")]
        if hL and hR and hL.overlap(hR): hits.append((f, c, "hand-vs-hand"))
        for s in "LR":
            h = T[(c, "hand", s)]
            if not h: continue
            if T[(c, "torso")] and h.overlap(T[(c, "torso")]):
                dd = pen_depth((c, s), T[(c, "torso")]); touches.append(f)
                if dd > DEPTH: hits.append((f, c, s, "hand-into-own-torso/head", round(dd, 3)))
            if T[(c, "cloth_no", s)] and h.overlap(T[(c, "cloth_no", s)]):
                dd = pen_depth((c, s), T[(c, "cloth_no", s)]); touches.append(f)
                if dd > DEPTH: hits.append((f, c, s, "hand-into-own-clothes", round(dd, 3)))
            for t in T[(other, "all")]:
                if t and h.overlap(t):
                    dd = pen_depth((c, s), t); touches.append(f)
                    if dd > DEPTH: hits.append((f, c, s, "hand-into-" + other, round(dd, 3)))
                    break
print("HAND_AUDIT frames %d-%d step %d: %d hits" % (F0, F1, STEP, len(hits)))
print("HAND_AUDIT_CONTACTS (touch, <= 6 mm)", len(touches))
from collections import Counter
print("HAND_AUDIT_BY_KIND", Counter((h[1], h[3] if len(h) > 4 else h[-1]) for h in hits))
print("HAND_AUDIT_HITS", hits[:200])
