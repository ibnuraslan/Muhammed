"""Contact audit for TitanicIceberg.  blender -b film.blend --python audit.py -- <report.txt>
Checks (every 6 frames inside each actor's on-screen window):
  feet:   lowest shoe vertex vs. the floor it stands on (hover > 2 cm, sink > 2 cm)
  hands:  hand/finger vertices vs. the prop they hold: min gap (float > 3 cm) and verts inside the prop (penetration, BVH parity)
  heads:  hat vertices vs. scalp (gap / poke-through count)
  camera: camera position inside any camera-visible, render-visible closed mesh."""
import sys, bpy, bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree
OUT = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene; O = bpy.data.objects
L = []
def P(*a): L.append(" ".join(str(x) for x in a)); print(*a)

def ev_mesh(ob):
    dg = bpy.context.evaluated_depsgraph_get(); e = ob.evaluated_get(dg); me = e.to_mesh()
    vs = [e.matrix_world @ v.co for v in me.vertices]; fs = [tuple(p.vertices) for p in me.polygons]
    groups = {g.index: g.name for g in ob.vertex_groups}
    wts = [{groups.get(g.group, ""): g.weight for g in v.groups} for v in me.vertices]
    e.to_mesh_clear(); return vs, fs, wts
def bvh(ob):
    vs, fs, _ = ev_mesh(ob); return BVHTree.FromPolygons(vs, fs), vs
def inside(tree, p):
    n = 0; o = p.copy(); d = Vector((0.0123, 0.0071, 1.0)).normalized()
    for _ in range(40):
        h = tree.ray_cast(o, d)
        if h[0] is None: break
        n += 1; o = h[0] + d * 1e-4
    return n % 2 == 1

ACT = {  # actor: (frames, floor object or z, held props {side: prop})
    "Steward": (range(0, 361, 6), "Deck_Planks", {"L": "bcamera", "R": "bcamera"}),
    "Deckhand": (range(0, 361, 12), "Deck_Planks", {}),
    "Tech": (range(1084, 1200, 6), "Darkroom_Floor", {"R": "Tongs"}),
    "ExpertA": (range(1200, 1330, 6), "Office_Floor", {"R": "magnifier"}),
    "ExpertB": (range(1200, 1330, 6), "Office_Floor", {"L": "Print_Office", "R": "Print_Office"}),
}
tot = dict(hover=0, sink=0, float=0, pen=0, cam=0)
for name, (frames, floor, props) in ACT.items():
    rig = O[name]; body = O[name + ".body"]
    shoes = [c for c in rig.children if c.name.split(".")[-1].startswith("shoes")]
    for f in frames:
        sc.frame_set(f)
        ft, _ = bvh(O[floor]); fz = None
        for sh in shoes:
            vs, _, _ = ev_mesh(sh)
            for s, sel in (("L", lambda v: v.x), ("R", lambda v: -v.x)):
                pass
            low = min(vs, key=lambda v: v.z)
            h = ft.ray_cast(low + Vector((0, 0, 1.0)), Vector((0, 0, -1)))
            if h[0] is not None:
                gap = low.z - h[0].z
                if gap > 0.02: tot["hover"] += 1; P("HOVER", name, f, round(gap, 3))
                if gap < -0.02: tot["sink"] += 1; P("SINK", name, f, round(gap, 3))
        if props:
            vs, _, wts = ev_mesh(body)
            for s, pn in props.items():
                hv = [v for v, w in zip(vs, wts) if any(k.startswith(("finger", "wrist", "metacarpal")) and k.endswith("." + s) and val > 0.5 for k, val in w.items())]
                if not hv: continue
                pt, _ = bvh(O[pn])
                dmin = min((pt.find_nearest(v)[3] for v in hv), default=9)
                pen = sum(1 for v in hv[::3] if inside(pt, v))
                if dmin > 0.03: tot["float"] += 1; P("HAND_FLOAT", name, s, pn, f, round(dmin, 3))
                if pen > 10: tot["pen"] += 1; P("HAND_PEN", name, s, pn, f, pen)
# hands: every 2 frames, hand vs other hand (closest verts < 6 mm) and hand verts inside own suit/clothes (BVH parity)
tot["hand_hand"] = 0; tot["hand_body"] = 0
for name, (frames, floor, props) in ACT.items():
    rig = O[name]; body = O[name + ".body"]
    suit = [c for c in rig.children if c.name.split(".")[-1].startswith(("male_", "female_"))]
    f0, f1 = frames[0], frames[-1]
    for f in range(f0, f1 + 1, 2):
        sc.frame_set(f)
        vs, _, wts = ev_mesh(body)
        H = {s: [v for v, w in zip(vs, wts) if any(k.startswith(("finger", "wrist", "metacarpal")) and k.endswith("." + s) and val > 0.5 for k, val in w.items())] for s in "LR"}
        if H["L"] and H["R"]:
            tL = BVHTree.FromPolygons(H["L"], [])  # point set
            from mathutils.kdtree import KDTree
            kd = KDTree(len(H["L"]))
            for i, v in enumerate(H["L"]): kd.insert(v, i)
            kd.balance()
            dmin = min(kd.find(v)[2] for v in H["R"][::2])
            if dmin < 0.006: tot["hand_hand"] += 1; P("HAND_HAND", name, f, round(dmin, 4))
        for sm in suit:
            st_, _ = bvh(sm)
            for s in "LR":
                FV = [v for v, w in zip(vs, wts) if any(k.startswith("finger") and k.endswith("." + s) and val > 0.5 for k, val in w.items())]
                n_in = sum(1 for v in FV[::3] if inside(st_, v))
                if n_in > 3: tot["hand_body"] += 1; P("HAND_IN_CLOTHES", name, s, f, n_in)
# head items: steward's hat
sc.frame_set(100)
hat = O.get("Steward.fedora01")
if hat:
    ht, _ = bvh(O["Steward.body"]); vs, _, _ = ev_mesh(hat)
    poke = sum(1 for v in vs[::4] if inside(ht, v)); P("HAT_POKE_THROUGH_VERTS", poke)
# camera inside geometry
cam = sc.camera
meshes = [o for o in O if o.type == 'MESH' and o.name not in ("Fog_Volume", "Mist_Bank", "Funnel_Smoke", "Explainer_Cyc", "Ocean_Far")]
for f in range(0, sc.frame_end + 1, 6):
    sc.frame_set(f); p = cam.matrix_world.translation
    for o in meshes:
        if o.hide_render or not o.visible_camera: continue
        if (o.matrix_world.translation - p).length > max(o.dimensions) + 2: continue
        if o.name.startswith(("liner", "Liner")): continue      # ghost (transparent) by design
        t, _ = bvh(o)
        if inside(t, p): tot["cam"] += 1; P("CAMERA_INSIDE", f, o.name)
P("TOTALS", tot)
open(OUT, "w").write("\n".join(L) + "\n")
