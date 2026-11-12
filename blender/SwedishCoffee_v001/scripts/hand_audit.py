"""Hand audit (STYLE_ANIMATED.md "Hands" rule).
blender -b film.blend --python hand_audit.py -- <report.txt> [step=2]
For every sampled frame and every rendered character whose hands are inside the camera view:
  HAND_HAND    finger/wrist points of the left and right hand closer than 2.5 cm (hands merging)
  HAND_TORSO   hand points inside / within 8 mm of the character's own torso, head or torso clothing
  HAND_OTHER   hand points inside another character's body
  JOINT_BACK   a finger bone bent backwards (final local Z rotation > +2 deg; forward curl is negative Z on the MPFB rig)
Hand points are bone heads/tails of wrist and finger bones (they sit ~1 cm inside the skin).
Subdivision is switched off for speed (the base mesh is within ~3 mm of the subdivided one)."""
import sys, bpy, math
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from bpy_extras.object_utils import world_to_camera_view
a = sys.argv[sys.argv.index("--") + 1:]; OUT = a[0]; STEP = int(a[1]) if len(a) > 1 else 2
sc = bpy.context.scene; cam = sc.camera
for o in bpy.data.objects:
    for m in o.modifiers:
        if m.type == 'SUBSURF': m.show_viewport = False
arms = [o for o in bpy.data.objects if o.type == 'ARMATURE' and o.users_collection[0].name.startswith("S")]
TORSO = ("spine", "neck", "head", "pelvis", "clavicle", "breast", "root", "jaw", "special", "oris", "levator", "orbicularis", "oculi", "temporalis", "risorius", "eye")
issues = {}
def flag(k, f, m): issues.setdefault(k, []).append((f, m))
def hand_pts(arm, s):
    P = arm.pose.bones; M = arm.matrix_world
    return [M @ P[n].tail for n in P.keys() if n.endswith("." + s) and n.startswith(("finger", "wrist"))] + \
           [M @ P[n].head for n in P.keys() if n.endswith("." + s) and n.startswith("finger")]
def bvh_region(objs, dg, keys=None):
    vs, fs = [], []
    for o in objs:
        ev = o.evaluated_get(dg); me = ev.to_mesh(); mw = o.matrix_world
        keep = None
        if keys is not None:
            gi = {g.index for g in o.vertex_groups if g.name.startswith(keys)}
            keep = [any(g.group in gi and g.weight > 0.4 for g in v.groups) for v in me.vertices]
        base = len(vs); idx = {}
        for i, v in enumerate(me.vertices):
            if keep is None or keep[i]: idx[i] = len(vs); vs.append(mw @ v.co)
        for p in me.polygons:
            if all(i in idx for i in p.vertices): fs.append([idx[i] for i in p.vertices])
        ev.to_mesh_clear()
    return BVHTree.FromPolygons(vs, fs) if fs else None
def inside(t, p, tol):
    loc, nrm, i, d = t.find_nearest(p, 0.2)
    if loc is None: return False
    return (p - loc).dot(nrm) < tol
nframes = 0
for f in range(sc.frame_start, sc.frame_end + 1, STEP):
    sc.frame_set(f); dg = bpy.context.evaluated_depsgraph_get(); nframes += 1
    vis = [o for o in arms if not o.hide_render and any(not c.hide_render for c in o.children)]
    inview = []
    for arm in vis:
        pts = hand_pts(arm, "L") + hand_pts(arm, "R")
        if any(0 <= v.x <= 1 and 0 <= v.y <= 1 and v.z > 0 for v in (world_to_camera_view(sc, cam, p) for p in pts[::4])): inview.append(arm)
    full = {}
    for arm in inview:
        L, R = hand_pts(arm, "L"), hand_pts(arm, "R")
        dmin = min((p - q).length for p in L[::2] for q in R[::2])
        if dmin < 0.025: flag("HAND_HAND", f, "%s hands %.1f cm apart" % (arm.name, dmin * 100))
        meshes = [c for c in arm.children if c.type == 'MESH' and not c.hide_render and c.name.split(".")[-1] not in ("high-poly", "eyelashes01", "eyebrow001", "eyebrow002", "eyebrow003", "eyebrow004", "eyebrow005", "teeth_base", "tongue01")]
        meshes = [m for m in meshes if not m.name.split(".")[-1].startswith(("shoes", "short", "bob", "ponytail"))]
        t = bvh_region(meshes, dg, TORSO)
        if t:
            n = sum(1 for p in L + R if inside(t, p, 0.008))
            if n >= 2: flag("HAND_TORSO", f, "%s %d hand points in torso/head/clothes" % (arm.name, n))
        for other in vis:
            if other is arm: continue
            # cheap reject: hands far from the other character's root
            if min((p - other.matrix_world @ other.pose.bones["root"].head).length for p in L + R) > 1.3: continue
            if other.name not in full:
                full[other.name] = bvh_region([c for c in other.children if c.type == 'MESH' and c.name.endswith((".body",))], dg)
            t2 = full[other.name]
            if t2 and sum(1 for p in L + R if inside(t2, p, 0.0)) >= 2: flag("HAND_OTHER", f, "%s hand inside %s" % (arm.name, other.name))
        for pb in arm.pose.bones:
            if pb.name.startswith("finger") and not pb.name.startswith("finger1"):
                rest = pb.parent.matrix @ (pb.parent.bone.matrix_local.inverted() @ pb.bone.matrix_local)
                mb = (rest.inverted() @ pb.matrix).to_euler()
                if math.degrees(mb.z) > 2: flag("JOINT_BACK", f, "%s %s %.0f deg" % (arm.name, pb.name, math.degrees(mb.z)))
lines = ["SwedishCoffee hand audit: every %d frames (%d frames sampled), characters with a hand in camera view" % (STEP, nframes)]
for k in ("HAND_HAND", "HAND_TORSO", "HAND_OTHER", "JOINT_BACK"):
    v = issues.get(k, []); lines.append("%-11s %4d" % (k, len(v)))
    for fr, m in v[:4000]: lines.append("    f%04d %s" % (fr, m))
open(OUT, "w").write("\n".join(lines) + "\n"); print("\n".join(lines))
