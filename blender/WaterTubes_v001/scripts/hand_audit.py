"""BVH hand audit (client rule, Nov 11 23:00). blender -b film.blend --python hand_audit.py -- <report.txt> [step=2] [f0] [f1]
Every <step> frames, for each character:
 - hand vs other hand (palm+finger faces of the body mesh)
 - hand vs own torso/head (body faces weighted to spine/neck/head/breast/pelvis) and vs own shirt torso panel (rest |x| < 0.16)
 - hand vs other characters' bodies (only when the rigs are within 2.5 m)
Prints each hit (frame, character, pair) and the total."""
import bpy, sys
from mathutils import Vector
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index("--") + 1:]
OUT = a[0]; STEP = int(a[1]) if len(a) > 1 else 2
sc = bpy.context.scene
F0 = int(a[2]) if len(a) > 2 else sc.frame_start; F1 = int(a[3]) if len(a) > 3 else sc.frame_end
CH = [o for o in bpy.data.objects if o.type == "ARMATURE" and o.name in ("Hero", "NeighbourA", "NeighbourB")]
HAND_KEYS = ("finger", "metacarpal")
TORSO_KEYS = ("spine", "neck", "head", "breast", "pelvis", "clavicle", "jaw", "special", "oris", "levator", "orbicularis", "oculi", "temporalis", "risorius", "eye", "tongue")
info = {}
for rig in CH:
    body = next(c for c in rig.children if c.name.endswith(".body"))
    gi = {g.index: g.name for g in body.vertex_groups}
    bones = set(rig.data.bones.keys())
    hid = {i for i, nm in gi.items() if nm in ("HelperGeometry", "JointCubes")}
    side = {}; torso = set()
    for v in body.data.vertices:
        gs = [g for g in v.groups if gi[g.group] in bones]
        if not gs or any(g.group in hid for g in v.groups): continue
        g = max(gs, key=lambda x: x.weight); n = gi[g.group]
        if any(k in n for k in HAND_KEYS) or n.startswith("wrist") and g.weight > 0.9:
            side.setdefault(n[-1], set()).add(v.index)
        elif any(n.startswith(k) for k in TORSO_KEYS):
            torso.add(v.index)
    shirt = next((c for c in rig.children if "suit" in c.name), None)
    sh_faces = []
    if shirt:
        co = [v.co for v in shirt.data.vertices]
        sh_faces = [tuple(p.vertices) for p in shirt.data.polygons if all(abs(co[i].x) < 0.16 and 0.95 < co[i].z < 1.55 for i in p.vertices)]
    info[rig.name] = dict(rig=rig, body=body, L=side.get("L", set()), R=side.get("R", set()), torso=torso, shirt=shirt, sh_faces=sh_faces)
    print("HANDSETS", rig.name, len(side.get("L", ())), len(side.get("R", ())), len(torso), len(sh_faces))

def faces_in(me, vset):
    return [tuple(p.vertices) for p in me.polygons if all(i in vset for i in p.vertices)]
def bvh(pts, faces): return BVHTree.FromPolygons(pts, faces) if faces else None
hits = []
for f in range(F0, F1 + 1, STEP):
    sc.frame_set(f); dg = bpy.context.evaluated_depsgraph_get()
    T = {}
    for n, d in info.items():
        M = d["body"].matrix_world
        mods = [m for m in d["body"].modifiers if m.type != "ARMATURE" and m.show_viewport]
        for m in mods: m.show_viewport = False
        dg.update(); e = d["body"].evaluated_get(dg); me = e.to_mesh(); pts = [M @ v.co for v in me.vertices]
        for m in mods: m.show_viewport = True
        assert len(pts) == len(d["body"].data.vertices)
        if "fL" not in d:
            d["fL"] = faces_in(me, d["L"]); d["fR"] = faces_in(me, d["R"]); d["fT"] = faces_in(me, d["torso"])
            d["fAll"] = [tuple(p.vertices) for p in me.polygons if not any(i in d["L"] or i in d["R"] for i in p.vertices)]
        T[n] = dict(L=bvh(pts, d["fL"]), R=bvh(pts, d["fR"]), T=bvh(pts, d["fT"]), ALL=bvh(pts, d["fAll"]), root=d["rig"].matrix_world @ d["rig"].pose.bones["root"].head)
        e.to_mesh_clear()
        if d["shirt"] and d["sh_faces"]:
            es = d["shirt"].evaluated_get(dg); ms = es.to_mesh(); Ms = d["shirt"].matrix_world
            T[n]["S"] = bvh([Ms @ v.co for v in ms.vertices], d["sh_faces"]); es.to_mesh_clear()
    for n, t in T.items():
        if t["L"] and t["R"] and t["L"].overlap(t["R"]): hits.append((f, n, "handL-handR"))
        for s in "LR":
            if not t[s]: continue
            if t["T"] and t[s].overlap(t["T"]): hits.append((f, n, f"hand{s}-torso/head"))
            if t.get("S") and t[s].overlap(t["S"]): hits.append((f, n, f"hand{s}-shirt"))
            for m, u in T.items():
                if m != n and (t["root"] - u["root"]).length < 2.5 and u["ALL"] and t[s].overlap(u["ALL"]): hits.append((f, n, f"hand{s}-{m}"))
txt = "\n".join("HIT f%d %s %s" % h for h in hits) + "\nHAND_AUDIT total hits: %d (frames %d-%d step %d)\n" % (len(hits), F0, F1, STEP)
print(txt); open(OUT, "w").write(txt)
