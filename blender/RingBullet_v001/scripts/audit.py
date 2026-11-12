"""RingBullet contact / safety audit.
blender -b film.blend --python audit.py -- <report.txt> [step]
Checks per sampled frame: foot hover/sink, ring fit (gap/penetration on the finger), body vs props penetration (BVH overlap),
bandage/plaster gap, camera inside geometry, gun pointed at camera, robber face visible to camera."""
import sys, math
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index("--") + 1:]
REP = a[0]; STEP = int(a[1]) if len(a) > 1 else 5
sc = bpy.context.scene; O = bpy.data.objects; cam = sc.camera
lines = []; counts = {}
def flag(kind, f, msg):
    counts[kind] = counts.get(kind, 0) + 1
    if counts[kind] <= 12: lines.append("F%4d %-14s %s" % (f, kind, msg))

def ev_mesh(o, dg):
    e = o.evaluated_get(dg); me = e.to_mesh()
    v = [e.matrix_world @ x.co for x in me.vertices]; p = [tuple(x.vertices) for x in me.polygons]
    e.to_mesh_clear(); return v, p
def bvh(o, dg):
    v, p = ev_mesh(o, dg); return BVHTree.FromPolygons(v, p), v

STATIC = [o for o in O if o.type == 'MESH' and o.visible_get() and not o.animation_data and o.parent is None and not o.name.startswith(("Owner", "Robber"))
          and o.users_collection and o.users_collection[0].name in ("Set", "Props") and o.name not in ("Rug",)]
dg = bpy.context.evaluated_depsgraph_get()
SB = {o.name: bvh(o, dg)[0] for o in STATIC}
PROP_NEAR = [n for n in SB if n.startswith(("Desk", "Lamp", "Paper", "Ledger", "Book", "book", "Wall", "Door", "wooden", "Pen"))]
body = O["Owner.body"]; ring = O["WeddingRing"]
HANDV = None
for f in range(sc.frame_start, sc.frame_end + 1, STEP):
    sc.frame_set(f); dg = bpy.context.evaluated_depsgraph_get()
    hid = lambda o: o.hide_render
    # feet (owner shoes lowest vertex near each foot vs floor z=0)
    sv, _ = ev_mesh(O["Owner.shoes02"], dg)
    for s, sx in (("L", 1), ("R", -1)):
        fx = (O["Owner"].matrix_world @ O["Owner"].pose.bones["foot." + s].head)
        pts = [v for v in sv if (v - fx).to_2d().length < 0.2]
        if pts:
            zmin = min(v.z for v in pts)
            planted = O["Owner"].pose.bones["foot." + s].head.z < 0.12
            if zmin < -0.012: flag("foot_sink", f, "%s %.3f" % (s, zmin))
            if planted and zmin > 0.02 and not (1249 <= f): flag("foot_hover", f, "%s %.3f" % (s, zmin))
    # body vs props
    bb, bv = bvh(body, dg)
    for n in PROP_NEAR:
        ov = bb.overlap(SB[n])
        if ov: flag("body_vs_prop", f, "%s %d tris" % (n, len(ov)))
    # ring fit
    if not ring.hide_render:
        rv, rp = ev_mesh(ring, dg); rb = BVHTree.FromPolygons(rv, rp)
        ov = rb.overlap(bb)
        c = ring.matrix_world.translation; ax = (ring.matrix_world.to_3x3() @ Vector((0, 0, 1))).normalized()
        inner = [v for v in rv if ((v - c) - ax * (v - c).dot(ax)).length < 0.0095 * ring.matrix_world.to_scale().x * 1.03]
        gaps = [bb.find_nearest(v)[3] for v in inner[::6]]
        g = min(gaps) if gaps else 0
        depth = 0.0
        for v in rv[::3]:
            loc, nrm, _, d = bb.find_nearest(v)
            if loc is not None and (v - loc).dot(nrm) < 0: depth = max(depth, d)
        if depth > 0.0015: flag("ring_pen", f, "%d tris overlap, depth %.4f m" % (len(ov), depth))
        if g > 0.0025: flag("ring_gap", f, "min gap %.4f m" % g)
    for nm in ("FingerBandage", "NeckPlaster"):
        o = O[nm]
        if not o.hide_render:
            v, _ = ev_mesh(o, dg); d = min(bb.find_nearest(x)[3] for x in v[::5])
            if d > 0.003: flag("dressing_gap", f, "%s %.4f" % (nm, d))
    # camera inside geometry: nearest-surface distance and an odd-hit ray test against static meshes
    cp = cam.matrix_world.translation
    def parity(t, d):
        hits = 0; p = cp.copy(); d = d.normalized()
        for _ in range(8):
            h = t.ray_cast(p, d)
            if h[0] is None: break
            hits += 1; p = h[0] + d * 1e-4
        return hits % 2
    for n, t in SB.items():
        # inside only if two independent ray directions both see an odd number of crossings (a grazing ray on a bevel can't fake it)
        if parity(t, Vector((0.01, 0.02, 1))) and parity(t, Vector((0.7, -0.3, 0.2))) and not n.startswith(("Floor", "Ceiling", "Street", "Yard", "Sidewalk", "Night", "Facade")):
            flag("cam_inside", f, n)
    nb = bb.find_nearest(cp)
    if nb[3] is not None and nb[3] < 0.004: flag("cam_in_body", f, "%.4f" % nb[3])
    # gun at camera / robber face
    G = O["Gun"]
    if not G.hide_render:
        mz = G.matrix_world @ Vector((0.19, 0, 0)); gx = (G.matrix_world.to_3x3() @ Vector((1, 0, 0))).normalized()
        ang = math.degrees(gx.angle((cp - mz).normalized()))
        from bpy_extras.object_utils import world_to_camera_view as w2c
        def inview(p):
            v = w2c(sc, cam, p); return 0 <= v.x <= 1 and 0 <= v.y <= 1 and v.z > 0
        if ang < 60 and inview(mz): flag("gun_at_cam", f, "%.0f deg" % ang)
        RA = O["Robber"]; hb = RA.pose.bones["head"]; hp = RA.matrix_world @ hb.head
        Rd = (hb.matrix @ RA.data.bones["head"].matrix_local.inverted()).to_3x3()
        fwd = (RA.matrix_world.to_3x3() @ Rd @ Vector((0, -1, 0))).normalized()   # MPFB faces -Y at rest
        if fwd.dot((cp - hp).normalized()) > 0.1 and inview(hp): flag("robber_face", f, "camera in front of robber")
out = ["RingBullet audit, step %d, frames %d-%d" % (STEP, sc.frame_start, sc.frame_end), "COUNTS " + (str(counts) if counts else "none")] + lines
open(REP, "w").write("\n".join(out) + "\n"); print("\n".join(out))
