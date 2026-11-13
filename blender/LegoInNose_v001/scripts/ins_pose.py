"""v008e (director, Nov 13): the brick-insertion pose. Fingertips up to the nostril, fist below and in front of the face.
blender -b in.blend --python ins_pose.py -- out.blend
For each insertion (Brick_Big 120-156, Brick_Small 700-742), in the boy's head frame (fw = out of the face, up, rt):
  brick : from where the carry leaves it (f0) it travels with the head to the nostril ENTRY (12 mm below/in front of the
          nostril) by fe, then slides into the nostril over the last 6 frames (fe..fn); after fn the old keys (stuck) continue.
  hand  : place_hand with the fingers pointing up and back toward the nostril (so the hand sits below and in front of the face),
          the palm normal chosen from candidates for the most face clearance; "pinch" pose; then the IK target is shifted until
          the thumb-index tip midpoint sits on the brick centre (on the entry point while the brick slides in), held to fh.
  check : every frame, the evaluated hand mesh (except the thumb and index tips) against the face/head mesh: min distance."""
import bpy, sys, os
from mathutils import Vector, Matrix, Quaternion
from mathutils.bvhtree import BVHTree
OUT = sys.argv[sys.argv.index("--") + 1]; sc = bpy.context.scene; vl = bpy.context.view_layer
HP = "/home/user/Muhammed/blender/pipeline/hand_poses.py"
exec(open(HP).read())
A = bpy.data.objects["Boy"]; BODY = bpy.data.objects["Boy_Body"]; S = "R"
def smooth(t): t = max(0.0, min(1.0, t)); return t * t * (3 - 2 * t)
def head_M():
    pb = A.pose.bones["head"]; return A.matrix_world @ pb.matrix @ A.data.bones["head"].matrix_local.inverted()
def axes():
    R = head_M().to_3x3().normalized(); return R @ Vector((0, -1, 0)), R @ Vector((0, 0, 1)), R @ Vector((1, 0, 0))
def tips(): return [A.matrix_world @ A.pose.bones["finger%d-3.%s" % (k, S)].tail for k in (1, 2, 3, 4, 5)]
def pinch(): t = tips(); return (t[0] + t[1]) / 2
def fcs(o): return [fc for l in o.animation_data.action.layers for st in l.strips for cb in st.channelbags for fc in cb.fcurves]
gi = {g.index: g.name for g in BODY.vertex_groups if g.name in A.data.bones}
dom = []
for v in BODY.data.vertices:
    g = max((g for g in v.groups if g.group in gi), key=lambda g: g.weight, default=None); dom.append(gi[g.group] if g else "")
FACE = ("head", "jaw", "neck", "eye", "nose", "lip", "oris", "cheek", "brow", "temporal", "tongue", "levator", "risorius", "special", "orbicularis", "ear")
HANDV = [i for i, n in enumerate(dom) if n.endswith("." + S) and n.startswith(("wrist", "metacarpal", "finger")) and n not in ("finger1-3." + S, "finger2-3." + S, "finger1-2." + S, "finger2-2." + S)]
masks = [(m, m.show_viewport) for m in BODY.modifiers if m.type in ("MASK", "SUBSURF", "MULTIRES")]
for m, _ in masks: m.show_viewport = False
def clearance():
    dg = bpy.context.evaluated_depsgraph_get(); e = BODY.evaluated_get(dg); me = e.to_mesh(); mw = e.matrix_world
    V = [mw @ v.co for v in me.vertices]
    polys = [tuple(p.vertices) for p in me.polygons if all(dom[i].lower().startswith(FACE) or any(k in dom[i].lower() for k in FACE) for i in p.vertices)]
    e.to_mesh_clear(); T = BVHTree.FromPolygons(V, polys)
    best = 9.0
    for i in HANDV:
        loc, nr, _, d = T.find_nearest(V[i], 0.2)
        if loc is not None:
            sd = d if (V[i] - loc).dot(nr) >= 0 else -d
            best = min(best, sd)
    return best
def set_brick(o, f, M):
    o.matrix_world = M; vl.update(); o.keyframe_insert("location", frame=f)
    o.keyframe_insert("rotation_quaternion" if o.rotation_mode == "QUATERNION" else "rotation_euler", frame=f)
def pose_hand(f, target, d, n):
    sc.frame_set(f)
    place_hand(A, S, f, target - d * 0.07, n, d)        # first guess: palm 7 cm back along the fingers
    apply_pose(A, S, "pinch", f); sc.frame_set(f)
    for it in range(8):                                   # shift the IK target until the pinch is on the target point
        e = target - pinch()
        if e.length < 0.002: break
        pb = A.pose.bones["IK_hand." + S]; m = pb.matrix.copy(); m.translation = m.translation + A.matrix_world.inverted().to_3x3() @ (e * 0.8)
        pb.matrix = m; vl.update(); pb.keyframe_insert("location", frame=f, group=pb.name); sc.frame_set(f)
    return (target - pinch()).length
import math
TILT, ROLL, ENT, FWK, CLEAR = 0, 250, 0.028, 1.0, 0.015     # from a grid search (tilt 0-45, roll 180-290, entry 12-28 mm) for face clearance
def hand_axes():
    fw, up, rt = axes(); t = math.radians(TILT); d = (up * math.cos(t) - fw * math.sin(t)).normalized()
    a = math.radians(ROLL); b1 = (fw - d * fw.dot(d)).normalized(); b2 = d.cross(b1); return d, b1 * math.cos(a) + b2 * math.sin(a)
def lerpM(Ma, Mb, t):
    la, ra, _ = Ma.decompose(); lb, rb, _ = Mb.decompose(); return Matrix.Translation(la.lerp(lb, t)) @ ra.slerp(rb, t).to_matrix().to_4x4()
def run(pn, f0, fe, fn, fh):
    o = bpy.data.objects[pn]
    sc.frame_set(f0); Bstart = head_M().inverted() @ o.matrix_world.copy()
    sc.frame_set(fn); Hn = head_M(); Bn = Hn.inverted() @ o.matrix_world.copy(); fw, up, rt = axes()
    out_h = Hn.to_3x3().inverted() @ (-up * 0.8 + fw * FWK).normalized()                 # out of the nostril, head space
    Bent = Matrix.Translation(Bn.translation + out_h * ENT) @ Bn.to_3x3().to_4x4()
    rim = Bn.translation + out_h * 0.006
    worst, errs, last = (9, 0), [], None
    for f in range(f0, fh + 1):
        sc.frame_set(f); H = head_M()
        if f <= fe: BM = H @ lerpM(Bstart, Bent, smooth((f - f0) / (fe - f0)))
        elif f <= fn: BM = H @ lerpM(Bent, Bn, (f - fe) / (fn - fe))
        else: BM = None
        if BM is not None: set_brick(o, f, BM)
        d, n = hand_axes()
        if f <= fe: cands = [BM.translation]
        else:                                   # follow the brick up toward the rim as far as the face clearance allows
            k = min(1.0, (f - fe) / (fn - fe)); cands = [H @ (Bent.translation.lerp(rim, k * u)) for u in (1.0, 0.75, 0.5, 0.25, 0.0)]
        for j, tgt in enumerate(cands):
            e = pose_hand(f, tgt, d, n); sc.frame_set(f); c = clearance()
            if c >= CLEAR or j == len(cands) - 1: break
        errs.append(e)
        if c < worst[0]: worst = (c, f)
    print("INS", pn, f0, fh, "pinch error max %.1f mm" % (max(errs) * 1000), "min hand-face clearance %.1f mm at f%d" % (worst[0] * 1000, worst[1]))
run("Brick_Big", 120, 144, 150, 156)
run("Brick_Small", 700, 730, 736, 742)
for m, v in masks: m.show_viewport = v
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True); print("INS saved", OUT)
