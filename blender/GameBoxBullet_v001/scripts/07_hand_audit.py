"""Hand audit (client rule, 23:00 UTC): every 2 frames, BVH overlap of
 each hand vs the other hand, vs its own torso/legs/head (body), vs its own shirt (sleeve cuff excluded), vs the other character.
blender -b film.blend --python 07_hand_audit.py -- hand_audit.txt"""
import sys, bpy
from mathutils.bvhtree import BVHTree
OUT = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene
CH = {"Gamer": ("Gamer.body", "Gamer.male_casualsuit03"), "Walker": ("Walker.body", "Walker.female_casualsuit01")}
def side_of(gname):
    if gname.startswith(("finger", "metacarpal", "wrist")): return gname[-1]
    if gname.startswith(("lowerarm", "upperarm", "shoulder", "clavicle")): return "arm"
    return "body"
def parts(obj, dg):
    oe = obj.evaluated_get(dg); me = oe.to_mesh(preserve_all_data_layers=True, depsgraph=dg); M = obj.matrix_world
    names = [g.name for g in obj.vertex_groups]
    bones = set(b.name for b in obj.parent.data.bones)
    lab = []
    for v in me.vertices:
        best = None; w = 0
        for g in v.groups:
            if g.group < len(names) and g.weight > w and names[g.group] in bones:
                best, w = names[g.group], g.weight
        lab.append(side_of(best) if best else "body")
    co = [M @ v.co for v in me.vertices]
    out = {}
    for key in ("L", "R", "body", "arm"):
        polys = [list(p.vertices) for p in me.polygons if all(lab[i] == key for i in p.vertices)]
        out[key] = BVHTree.FromPolygons(co, polys) if polys else None
    allp = [list(p.vertices) for p in me.polygons]
    out["all"] = BVHTree.FromPolygons(co, allp)
    oe.to_mesh_clear(); return out
hits = []; frames = 0
for f in range(1, sc.frame_end + 1, 2):
    sc.frame_set(f); dg = bpy.context.evaluated_depsgraph_get(); frames += 1
    P = {}
    for ch, (bn, cn) in CH.items():
        P[ch] = (parts(bpy.data.objects[bn], dg), parts(bpy.data.objects[cn], dg))
    boxt = []
    for o in bpy.data.objects:
        if o.type == "MESH" and o.name.startswith(("Box_", "Tray_")) and not o.hide_render:
            oe = o.evaluated_get(dg); me = oe.to_mesh(); co = [o.matrix_world @ v.co for v in me.vertices]
            boxt.append(BVHTree.FromPolygons(co, [list(p.vertices) for p in me.polygons])); oe.to_mesh_clear()
    for bt in boxt:
        for k in ("L", "R"):
            if P["Gamer"][0][k]:
                n = len(P["Gamer"][0][k].overlap(bt))
                if n: hits.append((f, "Gamer", "hand%s-box" % k, n))
    for ch, (b, c) in P.items():
        tests = [("handL-handR", b["L"], b["R"]), ("handL-body", b["L"], b["body"]), ("handR-body", b["R"], b["body"]),
                 ("handL-shirt", b["L"], c["body"]), ("handR-shirt", b["R"], c["body"])]
        oth = [o for o in P if o != ch][0]
        tests += [("hand-other", b["L"], P[oth][0]["all"]), ("hand-other", b["R"], P[oth][0]["all"])]
        for name, A, Bt in tests:
            if A is None or Bt is None: continue
            n = len(A.overlap(Bt))
            if n: hits.append((f, ch, name, n))
rep = ["HAND AUDIT GameBoxBullet: frames 1-%d every 2 frames (%d frames), 2 characters" % (sc.frame_end, frames),
       "flagged frames: %d, overlapping triangle pairs: %d" % (len({(h[0], h[1]) for h in hits}), sum(h[3] for h in hits)), ""]
rep += ["f%4d %-7s %-12s %d" % h for h in hits[:400]]
open(OUT, "w").write("\n".join(rep)); print("\n".join(rep[:30]))
