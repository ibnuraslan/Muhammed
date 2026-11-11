"""Contact audit for WaterTubes. blender -b film.blend --python audit.py -- <report.txt>
Checks (every 5th frame while each character is in frame range):
 - feet: lowest shoe vertex vs surface under it (hover > 4 cm, sink > 3 cm)
 - shoe / hand mesh penetration into static scene meshes (BVH overlap count)
 - hero hands vs hose nozzle during beat 1 (grip gap)
 - camera inside geometry (ray parity against houses, tubes, ground)"""
import bpy, sys, math
from mathutils import Vector
from mathutils.bvhtree import BVHTree
OUT = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene
log = []
def P(*a): s = " ".join(str(x) for x in a); print(s); log.append(s)

_G = bpy.data.objects["Ground"]; _H = bpy.data.objects["HeroHouse"]
def surf_z(x, y):
    best = None
    for ob in (_G, _H, *[o for o in bpy.data.objects if o.name.startswith("Sidewalk_") and abs(o.location.x - x) < 2 and abs(o.location.y - y) < 2]):
        mi = ob.matrix_world.inverted()
        hit, loc, n, i = ob.ray_cast(mi @ Vector((x, y, 1.6)), (mi.to_3x3() @ Vector((0, 0, -1))).normalized())
        if hit:
            z = (ob.matrix_world @ loc).z
            if z < 1.45 and (best is None or z > best): best = z
    return best if best is not None else 0.0

def bvh_world(ob, dg):
    e = ob.evaluated_get(dg); me = e.to_mesh()
    M = ob.matrix_world
    bvh = BVHTree.FromPolygons([M @ v.co for v in me.vertices], [tuple(p.vertices) for p in me.polygons])
    e.to_mesh_clear(); return bvh

ACTIVE = {"Hero": [(1, 2010)], "NeighbourA": [(1, 2010)], "NeighbourB": [(1, 2010)]}
STATIC = [o for o in bpy.data.objects if o.type == "MESH" and (o.name.startswith(("Tube_", "Valve_", "HeroHouse", "Ground", "WetSofa", "Bin_", "Fence_")))]
hover = sink = pen_feet = pen_hands = 0; worst = []
dg = bpy.context.evaluated_depsgraph_get()
for f in range(1, 2011, 5):
    sc.frame_set(f); dg = bpy.context.evaluated_depsgraph_get()
    for name in ACTIVE:
        rig = bpy.data.objects[name]
        shoes = next(c for c in rig.children if "shoes" in c.name)
        e = shoes.evaluated_get(dg); me = e.to_mesh(); M = shoes.matrix_world
        pts = [M @ v.co for v in me.vertices]; e.to_mesh_clear()
        for s in "LR":
            fb = rig.matrix_world @ rig.pose.bones["foot." + s].head
            side = [p for p in pts if (p.xy - fb.xy).length < 0.2]
            if not side: continue
            low = min(side, key=lambda p: p.z)
            gz = surf_z(low.x, low.y); d = low.z - gz
            if d > 0.04: hover += 1; worst.append((d, f, name, s, "hover"))
            if d < -0.03: sink += 1; worst.append((-d, f, name, s, "sink"))
    if f % 25 == 1:
        bv_static = [(o.name, bvh_world(o, dg)) for o in STATIC if not o.hide_render]
        for name in ACTIVE:
            rig = bpy.data.objects[name]
            shoes = next(c for c in rig.children if "shoes" in c.name)
            bs = bvh_world(shoes, dg)
            for on, b in bv_static:
                if on in ("Ground",): continue
                ov = bs.overlap(b)
                if ov: pen_feet += 1; worst.append((len(ov) / 100, f, name, on, "shoe-overlap"))
P("FEET hover>4cm:", hover, " sink>3cm:", sink, " shoe/scene overlaps:", pen_feet)
# hands vs nozzle during beat 1
gaps = []
hero = bpy.data.objects["Hero"]
for f in range(1, 151, 10):
    sc.frame_set(f); noz = bpy.data.objects["Nozzle"].matrix_world.translation
    for s in "LR":
        tip = hero.matrix_world @ hero.pose.bones["finger3-3." + s].tail if "finger3-3." + s in hero.pose.bones else hero.matrix_world @ hero.pose.bones["wrist." + s].tail
        gaps.append(((tip - noz).length, f, s))
P("GRIP nozzle: max fingertip-to-nozzle %.3f m, mean %.3f m" % (max(g[0] for g in gaps), sum(g[0] for g in gaps) / len(gaps)))
# camera inside geometry
cam = sc.camera; inside = []
CANDS = [o for o in bpy.data.objects if o.type == "MESH" and not o.hide_render and o.name.startswith(("Tube_", "house", "HeroHouse", "hero_house", "CutTube", "CutWater", "FloodWall", "Tree_", "Lamp_"))]
for f in range(1, 2011, 10):
    sc.frame_set(f); dg = bpy.context.evaluated_depsgraph_get(); c = cam.matrix_world.translation
    for o in CANDS:
        if o.hide_render: continue
        mi = o.matrix_world.inverted(); oc = mi @ c; e = o.evaluated_get(dg)
        bb = [Vector(b) for b in o.bound_box]
        if not all(min(b[i] for b in bb) - 0.01 <= oc[i] <= max(b[i] for b in bb) + 0.01 for i in range(3)): continue
        hits = 0; p = oc.copy(); dvec = Vector((0.0123, 0.0071, 1)).normalized()
        for _ in range(40):
            hit, loc, n, i = e.ray_cast(p, dvec)
            if not hit: break
            hits += 1; p = loc + dvec * 1e-4
        if hits % 2 == 1: inside.append((f, o.name))
P("CAMERA inside geometry frames:", len(inside), inside[:20])
# camera below water / ground
under = []
fn = bpy.data.node_groups["FloodSurface"].nodes
for f in range(1, 2011, 10):
    sc.frame_set(f); c = cam.matrix_world.translation
    if c.z < surf_z(c.x, c.y) + 0.05: under.append(f)
P("CAMERA below ground frames:", under)
worst.sort(reverse=True)
P("WORST:", [(round(a, 3), f, n, s, k) for a, f, n, s, k in worst[:25]])
open(OUT, "w").write("\n".join(log) + "\n")
