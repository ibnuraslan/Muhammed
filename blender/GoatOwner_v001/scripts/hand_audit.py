"""Hand audit (client rule, Nov 11 23:00): BVH overlap every <step> frames of
  each hand vs the other hand, each hand vs its own torso/head/clothes, each hand vs other characters and the goat.
blender -b anim.blend --python hand_audit.py -- <report.txt> [step]"""
import sys
import bpy
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index("--") + 1:]; OUT = a[0]; STEP = int(a[1]) if len(a) > 1 else 2
sc = bpy.context.scene
HUM = [bpy.data.objects[n] for n in ("Owner", "Passer", "OffA", "OffB", "Rescuer")]
GOAT = [c for c in bpy.data.objects["Goat_rig"].children if c.type == 'MESH']
def is_hand(n): return n.startswith(("finger", "metacarpal"))        # palm + fingers (wrist ring sits under the sleeve cuff)
def is_arm(n): return n.startswith(("lowerarm", "upperarm", "shoulder", "clavicle")) or is_hand(n)
HAND_TOL, BODY_TOL, OTHER_TOL = 0, 6, 12     # polygon pairs; light contact (palm on own belly, palm on the goat) is allowed up to the tolerance
def split(rig, dg):
    """returns {'L': hand tree, 'R': hand tree, 'body': torso/head/legs tree, 'clothes': tree}"""
    out = {}
    for o in rig.children:
        if o.type != 'MESH' or o.hide_render: continue
        e = o.evaluated_get(dg); me = e.to_mesh(); mw = o.matrix_world
        vs = [mw @ v.co for v in me.vertices]
        if o.name.endswith(".body"):
            bones = set(rig.data.bones.keys())
            gn = {g.index: g.name for g in o.vertex_groups if g.name in bones}
            side = {}
            for v in me.vertices:
                best = max((g for g in v.groups if g.group in gn), key=lambda g: g.weight, default=None)
                nm = gn.get(best.group, "") if best else ""
                side[v.index] = ("L" if nm.endswith(".L") else "R") if is_hand(nm) else ("arm" if is_arm(nm) else "body")
            parts = {"L": [], "R": [], "body": []}
            for p in me.polygons:
                tags = [side[i] for i in p.vertices]
                t = max(set(tags), key=tags.count)
                if t in parts: parts[t].append(list(p.vertices))
            for k, ps in parts.items():
                if ps: out[k] = BVHTree.FromPolygons(vs, ps)
        elif not any(x in o.name for x in ("eyebrow", "eyelash", "teeth", "tongue", "high-poly")):
            out.setdefault("clothes_list", []).append(BVHTree.FromPolygons(vs, [list(p.vertices) for p in me.polygons]))
        e.to_mesh_clear()
    return out
flags = []; total = {}
FR = [int(x) for x in a[2].split(",")] if len(a) > 2 else range(sc.frame_start, sc.frame_end + 1, STEP)
for f in FR:
    sc.frame_set(f); dg = bpy.context.evaluated_depsgraph_get()
    vis = [r for r in HUM if not r.hide_render]
    T = {r.name: split(r, dg) for r in vis}
    gt = []
    for o in GOAT:
        e = o.evaluated_get(dg); me = e.to_mesh(); mw = o.matrix_world
        gt.append(BVHTree.FromPolygons([mw @ v.co for v in me.vertices], [list(p.vertices) for p in me.polygons])); e.to_mesh_clear()
    for r in vis:
        t = T[r.name]
        for s in "LR":
            h = t.get(s)
            if not h: continue
            o_ = "R" if s == "L" else "L"
            checks = [("other hand", t.get(o_), HAND_TOL), ("own body", t.get("body"), BODY_TOL)]
            checks += [("own clothes", c, BODY_TOL) for c in t.get("clothes_list", [])]
            for r2 in vis:
                if r2 is r: continue
                for k in ("L", "R", "body"):
                    if T[r2.name].get(k): checks.append(("%s %s" % (r2.name, k), T[r2.name][k], OTHER_TOL))
            checks += [("goat", g, OTHER_TOL) for g in gt]
            for what, tr, tol in checks:
                if tr is None: continue
                n = len(h.overlap(tr)); key = "%s %s hand vs %s" % (r.name, s, what)
                if n: total[key] = total.get(key, 0) + 1
                if n > tol: flags.append((f, key, n))
L = ["HAND AUDIT GoatOwner (every %d frames)" % STEP, "flagged samples (over tolerance): %d" % len(flags)]
L += ["  f%d (%.2fs) %s: %d polygon pairs" % (f, (f - 1) / 60, k, n) for f, k, n in flags[:60]]
L.append("contacts within tolerance (samples): " + ", ".join("%s %d" % kv for kv in sorted(total.items())))
open(OUT, "w").write("\n".join(L) + "\n"); print("\n".join(L[:40]))
