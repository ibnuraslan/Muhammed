"""v008c: Mom's LEFT arm never passes through her own body (director, f944-955: forearm through chest/belly while walking in).
blender -b in.blend --python mom_arm.py -- out.blend
1. The walk-in (870-962) had no left-hand keys: the IK target held the 965 chin-reach offset, across her chest.
   Now: hand low at her left side, slightly in front, small walk swing, elbow pole out to the side.
2. Test every frame 870-1145: forearm/wrist/hand vertices against her own torso (spine/pelvis/breast/neck);
   any vertex > 0.5 cm inside -> the hand target is pushed out to her left (and forward) by depth + 2 cm, repeated."""
import bpy, sys, math
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
OUT = sys.argv[sys.argv.index("--") + 1]; sc = bpy.context.scene; vl = bpy.context.view_layer
A = bpy.data.objects["Mom"]; BODY = bpy.data.objects["Mom_Body"]
IK, POLE = A.pose.bones["IK_hand.L"], A.pose.bones["Pole_elbow.L"]
def bw(n, tail=False): pb = A.pose.bones[n]; return A.matrix_world @ (pb.tail if tail else pb.head)
def set_world(pb, p, f):
    m = pb.matrix.copy(); m.translation = A.matrix_world.inverted() @ p; pb.matrix = m; vl.update()
    pb.keyframe_insert("location", frame=f, group=pb.name)
def frame_axes():
    shL, shR = bw("upperarm01.L"), bw("upperarm01.R"); left = (shL - shR); left.z = 0; left.normalize()
    up = Vector((0, 0, 1)); fwd = left.cross(up).normalized(); return shL, left, fwd, up
# 1. walk-in keys
for f in range(870, 963, 4):
    sc.frame_set(f); shL, left, fwd, up = frame_axes()
    sw = 0.07 * math.sin((f - 870) / 47.0 * 2 * math.pi * 2.2)
    set_world(IK, shL + left * 0.13 + fwd * (0.12 + sw) - up * 0.40, f)
    set_world(POLE, shL + left * 0.5 - fwd * 0.25 - up * 0.15, f)
# pole out to the side on every existing hand key too (elbow never folds inward)
for f in (965, 978, 990, 1015, 1040, 1058, 1075, 1100, 1140):
    sc.frame_set(f); shL, left, fwd, up = frame_axes(); set_world(POLE, shL + left * 0.55 - fwd * 0.1 - up * 0.2, f)
# 2. test + push
gi = {g.index: g.name for g in BODY.vertex_groups if g.name in A.data.bones}
dom = []
for v in BODY.data.vertices:
    g = max((g for g in v.groups if g.group in gi), key=lambda g: g.weight, default=None); dom.append(gi[g.group] if g else "")
ARM = ("lowerarm01.L", "lowerarm02.L", "wrist.L", "metacarpal", "finger")
TOR = ("spine", "pelvis", "breast", "neck", "clavicle")
probe = [i for i, n in enumerate(dom) if n.startswith(ARM) and n.endswith(".L")]
masks = [(m, m.show_viewport) for m in BODY.modifiers if m.type in ("MASK", "SUBSURF", "MULTIRES")]
for m, _ in masks: m.show_viewport = False
def hits(f):
    sc.frame_set(f); dg = bpy.context.evaluated_depsgraph_get(); e = BODY.evaluated_get(dg); me = e.to_mesh(); mw = e.matrix_world
    V = [mw @ v.co for v in me.vertices]
    polys = [tuple(p.vertices) for p in me.polygons if all(dom[i].startswith(TOR) for i in p.vertices)]
    e.to_mesh_clear(); T = BVHTree.FromPolygons(V, polys); deep = 0.0
    for i in probe:
        loc, nr, _, d = T.find_nearest(V[i], 0.3)
        if loc is not None and d > 0.005 and (V[i] - loc).dot(nr) < 0: deep = max(deep, d)
    return deep
for rnd in range(6):
    bad = [(f, d) for f in range(870, 1146) for d in [hits(f)] if d > 0]
    print("MOMARM round", rnd, "frames inside", len(bad), "max %.1f cm" % (max([d for _, d in bad], default=0) * 100), [f for f, _ in bad][:30])
    if not bad: break
    for f, d in bad:
        sc.frame_set(f); shL, left, fwd, up = frame_axes(); p = bw("wrist.L")
        set_world(IK, (A.matrix_world @ IK.matrix.translation) + left * (d + 0.02) + fwd * 0.01, f)
for m, v in masks: m.show_viewport = v
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True); print("MOMARM saved", OUT)
