"""Tool grip pass (client, Nov 13): the pen-shaped tools are HELD, never balanced; the hand drives the tool.
blender -b film_c.blend --python 10_tool_grip.py -- <out.blend> <report.txt>

For each held range:
  1. The fingers are in the hand_poses 'pinch' preset (thumb + index close on the barrel, middle under it, ring/little
     curled) - keyed in 03, with add_hand_limits already on the rig (07), i.e. limits are in place BEFORE this solve.
  2. The pen's place in the hand is measured once from the evaluated pose: barrel through the thumb/index pinch point,
     running back over the web of the hand.
  3. Every frame the wrist is solved so the pen tip stays on the original tip path (the letters / the incision) and the
     barrel leans back over the hand toward the shoulder side, kept >= 20 cm from the head centre (>= 10 cm from face/mask).
  4. The IK hand is keyed every frame, then the pen is baked every frame from the EVALUATED wrist (no gap, no own motion).
     After release it lies still where it was put down."""
import sys, os, math
import bpy
from mathutils import Vector, Matrix
a = sys.argv[sys.argv.index("--") + 1:]
OUT, REP = a[0], a[1]
sc = bpy.context.scene
V = lambda *x: Vector(x)

def ik_remove(r, s, a0, b0):
    for L in r.animation_data.action.layers:
        for st in L.strips:
            for cb in st.channelbags:
                for fc in cb.fcurves:
                    if fc.data_path in ('pose.bones["IK_hand.%s"].location' % s, 'pose.bones["IK_hand.%s"].rotation_quaternion' % s):
                        k = fc.keyframe_points
                        for i in reversed(range(len(k))):
                            if a0 <= k[i].co.x <= b0: k.remove(k[i], fast=True)
                        fc.update()
def obj_clear(ob):
    if ob.animation_data: ob.animation_data_clear()
def seg_dist(p, a_, b_):
    ab = b_ - a_; t = max(0.0, min(1.0, (p - a_).dot(ab) / max(ab.length_squared, 1e-9))); return (p - (a_ + ab * t)).length
def pen_length(pen):
    zs = []
    for c in [pen] + list(pen.children_recursive):
        if c.type == 'MESH':
            M = pen.matrix_world.inverted() @ c.matrix_world
            zs += [(M @ Vector(v)).z for v in c.bound_box]
    return max(zs) if zs else 0.15

report = []
def hold(rig_name, s, pen_name, f0, f1, put=None, lean=V(0.75, -0.45, 0.85), away=V(1, 0, 0), head_clear=0.20):
    """put = (frame_release, tip_loc, axis) to carry the pen to a rest place and let go"""
    r = bpy.data.objects[rig_name]; pen = bpy.data.objects[pen_name]; PB = r.pose.bones; BN = r.data.bones
    Lp = pen_length(pen)
    # original tip path
    tipw = {}; Rorig = {}
    for f in range(f0, (put[0] if put else f1) + 1):
        sc.frame_set(f); tipw[f] = pen.matrix_world.translation.copy()
        Rorig[f] = (r.matrix_world.to_3x3() @ PB["wrist." + s].matrix.to_3x3()).normalized()   # feasible hand orientation
    # grip geometry from the evaluated pinch pose, in wrist space
    sc.frame_set(f0 + 30)
    Wp = PB["wrist." + s].matrix.copy(); Wi = Wp.inverted()
    loc = lambda b, tail=False: Wi @ (PB[b].tail if tail else PB[b].head)
    c = (loc("finger1-3." + s, True) + loc("finger2-3." + s, True)) / 2
    web = (loc("finger2-1." + s) + loc("finger1-2." + s)) / 2
    u = (web - c).normalized()
    palm_n = (loc("finger3-1." + s) - loc("wrist." + s)).cross(loc("finger2-1." + s) - loc("finger5-1." + s)).normalized()
    if s == "R": palm_n = -palm_n
    tipL = c - u * 0.045                                       # grip 4.5 cm up the barrel from the tip
    X = palm_n.cross(u).normalized(); Y = u.cross(X)
    T = Matrix((X, Y, u)).transposed().to_4x4(); T.translation = tipL     # pen in wrist space (pen +Z = tip -> back end)
    bl = (-palm_n - u * (-palm_n).dot(u)).normalized()
    A = Matrix((u, bl, u.cross(bl))).transposed()
    W0, I0 = BN["wrist." + s].matrix_local, BN["IK_hand." + s].matrix_local
    end = put[0] if put else f1
    ik_remove(r, s, f0, end)
    worst = 9.0
    for f in range(f0, end + 1):
        sc.frame_set(f)
        hd = r.matrix_world @ (PB["head"].head + (PB["head"].tail - PB["head"].head) * 0.5)
        ff = min(f, f1)
        Ro = Rorig[ff]; Uo = (Ro @ u).normalized()                # where the barrel points with the original hand
        U = Uo.copy(); P0 = tipw[ff]
        for _ in range(16):                                         # swing it away from the head only as far as needed
            if seg_dist(hd, P0, P0 + U * Lp) >= head_clear: break
            U = (U + away * 0.12 + V(0, 0, 0.04)).normalized()
        Rq = Uo.rotation_difference(U).to_matrix() @ Ro             # world wrist rotation, small change from a feasible one
        if f <= f1:
            P = P0
        else:
            k = (f - f1) / max(1, end - f1); k = k * k * (3 - 2 * k); P = tipw[f1].lerp(put[1], k)
        Rw = r.matrix_world.to_3x3().inverted() @ Rq
        Hw = Rw.to_4x4()
        Pa = r.matrix_world.inverted() @ P
        Hw.translation = Pa - Rw @ tipL
        pb = PB["IK_hand." + s]
        M_ = (Hw @ W0.inverted()) @ I0; M_.translation = Hw.translation    # the IK solve puts the wrist head ON the control's head
        pb.matrix = M_
        pb.keyframe_insert("location", frame=f, group=pb.name); pb.keyframe_insert("rotation_quaternion", frame=f, group=pb.name)
    # bake the pen from the evaluated wrist
    obj_clear(pen); pen.rotation_mode = 'QUATERNION'
    gap = 0.0
    for f in range(f0, end + 1):
        sc.frame_set(f)
        M = r.matrix_world @ PB["wrist." + s].matrix @ T
        pen.matrix_world = M
        pen.keyframe_insert("location", frame=f); pen.keyframe_insert("rotation_quaternion", frame=f)
        hd = r.matrix_world @ (PB["head"].head + (PB["head"].tail - PB["head"].head) * 0.5)
        tip = M.translation; back = M @ V(0, 0, Lp)
        worst = min(worst, seg_dist(hd, tip, back))
        if f <= f1: gap = max(gap, (tip - tipw[f]).length)
    for f in (end + 1, sc.frame_end):                          # lies still once put down
        pen.keyframe_insert("location", frame=f); pen.keyframe_insert("rotation_quaternion", frame=f)
    report.append("%s.%s holds %s %d-%d%s: pen %.0f mm long, tip off its path max %.1f cm, barrel to head centre min %.1f cm"
                  % (rig_name, s, pen_name, f0, f1, (", carries it to rest by %d" % end) if put else "", Lp * 1000, gap * 100, worst * 100))
    print(report[-1])

# Surgeon 1, OR pen over the incision: back end over his right hand toward his right shoulder side (+X), away from the face;
# then he lays it on the instrument tray before taking the needle driver
hold("Surgeon1", "R", "ArgonPen_OR", 1, 300, put=(312, V(0.33, -1.0, 1.04), V(1, 0.3, 0.05)), lean=V(0.75, -0.45, 0.85), away=V(1, 0, 0))
# studio: gloved hand writes S and B; the pen leans back over the hand
hold("GloveHands", "R", "ArgonPen_Studio", 1, 300, lean=V(0.45, -0.35, 0.85), away=V(1, 0, 0), head_clear=0.0)
with open(REP, "w") as fh:
    fh.write("Tool grip pass (pinch preset, limits on before solve, pen baked from the evaluated wrist every frame)\n" + "\n".join(report) + "\n")
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("TOOLGRIP_DONE", OUT)
