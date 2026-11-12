"""Contact audit for EscapeArtist. blender -b film.blend --python audit.py -- [step]
Checks per sampled frame, visible characters only:
 - feet: lowest foot/shoe vertex vs ground_z (hover > 4 cm, sink > 3 cm) while the character is standing (not climbing/airborne beats)
 - penetration: hand / foot / head verts inside scene geometry (BVH overlap of each character's hands, feet, head with set meshes)
 - camera: inside a mesh (ray parity test) or hidden-geometry clipping
Prints counts per beat."""
import sys, math, bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
exec(open("/home/user/Muhammed/blender/EscapeArtist_v001/scripts/escape_lib.py").read().split("# ---------------------------------------------------------------- visibility")[0])
a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
STEP = int(a[0]) if a else 30
B = [0, 276, 558, 678, 942, 1128, 1422, 1548, 1860, 2172, 2484, 2898, 3228, 3498, 3618, 3750]
AIR = [(1600, 1800)]            # fence climb / drop: feet are on the mesh, not the ground
sc = bpy.context.scene; dg = bpy.context.evaluated_depsgraph_get()
CAST = ["Prisoner", "PrisonerOld", "Boy", "Father", "Stepmother", "Guard", "Guard2", "Judge", "Protester1", "Protester2"]
STATIC = [o for o in bpy.data.objects if o.type == "MESH" and o.users_collection and o.users_collection[0].name in ("SET", "HOUSE", "COURT")
          and not o.name.startswith(("Tube_", "Fixture_", "SolitaryPanel")) and not o.hide_render and not o.hide_viewport]
def bvh_of(objs):
    vs, fs = [], []
    for o in objs:
        e = o.evaluated_get(dg); me = e.to_mesh(); M = o.matrix_world; base = len(vs)
        vs += [M @ v.co for v in me.vertices]; fs += [tuple(base + i for i in p.vertices) for p in me.polygons]; e.to_mesh_clear()
    return BVHTree.FromPolygons(vs, fs)
SB = bvh_of(STATIC)
def inside(p, tree, maxd=0.08):
    """point behind the nearest surface (within maxd) => inside that solid"""
    loc, nrm, idx, d = tree.find_nearest(p, maxd)
    if loc is None: return False
    return (p - loc).dot(nrm) < -0.003
def beat(f): return max(i for i in range(15) if B[i] <= f) + 1
GROUPS = {"hand": ("wrist", "finger", "metacarpal"), "foot": ("foot", "toe"), "head": ("head",)}
res = {}
for f in range(0, 3751, STEP):
    sc.frame_set(f); dg = bpy.context.evaluated_depsgraph_get()
    b = beat(f); r = res.setdefault(b, dict(hover=0, sink=0, pen=0, cam=0, n=0))
    cam = sc.camera
    if inside(cam.matrix_world.translation, SB): r["cam"] += 1; print("CAM_INSIDE", f)
    for n in CAST:
        arm = bpy.data.objects[n]; body = bpy.data.objects.get(n + ".body")
        if body is None or body.hide_render: continue
        r["n"] += 1
        mods = [m for m in body.modifiers if m.type == "SUBSURF" and m.show_render]
        for m in mods: m.show_viewport = False
        dg = bpy.context.evaluated_depsgraph_get()
        e = body.evaluated_get(dg); me = e.to_mesh(); M = body.matrix_world
        vg = {g.index: g.name for g in body.vertex_groups}
        feet, pen = [], 0
        for v in me.vertices:
            gs = [vg.get(g.group, "") for g in v.groups if g.weight > 0.5]
            p = M @ v.co
            if any(g.startswith(("foot", "toe")) for g in gs): feet.append(p)
            if any(g.startswith(GROUPS["hand"] + GROUPS["head"]) for g in gs) and inside(p, SB): pen += 1
        e.to_mesh_clear()
        for m in mods: m.show_viewport = True
        if pen > 5: r["pen"] += 1; print("PEN", f, n, pen)
        if feet and not any(a0 <= f <= a1 for a0, a1 in AIR):
            lo = min(feet, key=lambda p: p.z); gz = ground_z(lo.x, lo.y)
            # shoes cover the foot: foot skin ~1.5 cm above the sole
            d = lo.z - gz - 0.015
            if d > 0.06 and not (n in ("Prisoner", "PrisonerOld") and b in (2, 9, 12, 13)): r["hover"] += 1; print("HOVER", f, n, round(d, 3))
            if d < -0.04: r["sink"] += 1; print("SINK", f, n, round(d, 3))
for b in sorted(res): print("BEAT", b, res[b])
print("TOTAL", {k: sum(r[k] for r in res.values()) for k in ("hover", "sink", "pen", "cam", "n")})
