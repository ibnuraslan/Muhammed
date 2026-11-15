"""v008 from the director's v007 review (2026-11-14 23:49 UTC): short shots with clean cuts, faces on every beat,
simpler stagings. Runs on the 06_fix_v007 output.  blender -b film_v7k.blend --python 07_v008.py -- out.blend
Beat frames unchanged, no VO, DOF f/11."""
import sys, math, re
import bpy, bmesh
from mathutils import Vector, Matrix, Quaternion
HERE = "/home/user/Muhammed/blender/"
_src = open(HERE + "EscapeArtist_v001/scripts/06_fix_v007.py").read()
exec(_src.split("# ------------------------------------------------------------------ 1. camera")[0])   # libs + hand helpers
O = bpy.data.objects
CAST = ["Prisoner", "PrisonerOld", "Boy", "Father", "Stepmother", "Guard", "Guard2", "Judge", "Protester1", "Protester2"]
H = {n: Human(Rig(O[n])) for n in CAST}
PR = O["Prisoner"]; P_ = H["Prisoner"]; ZP = P_.root_head.z
def L(*a): print("V8", *a, flush=True)

# ================================================================== A. sawing (2186-2440): inside the cell, nothing crosses the bar plane
saw = O["Hacksaw"]; BAR2 = Vector((0.0, -3.2, 0.0)); SZ = 1.56
clear_hand(PR, "R", 2187, 2440); clear_hand(PR, "L", 2187, 2440); clear_tf(saw, 2187, 2441)
sax, sctr, sext = obj_local_axis(saw); Ssc = Matrix.Diagonal(saw.matrix_world.to_scale()).to_4x4()
# saw long axis along -y (handle in the cell, blade through the gap between bars 2 and 3, touching bar 2's side); frame up
sc.frame_set(0); _e0 = saw.matrix_world @ (sctr - sax * max(sext) * 0.5); _e1 = saw.matrix_world @ (sctr + sax * max(sext) * 0.5)
hand_end_neg = True                     # assume the handle is at the -axis end (checked visually); flip below if needed
_order = sorted(range(3), key=lambda i: sext[i]); side_ax = Vector((0, 0, 0)); side_ax[_order[1]] = 1    # the frame's height axis -> world up
SAWX = 0.026                            # blade plane just right of bar 2 (radius 1 cm)
for f in range(2186, 2441, 1):
    sc.frame_set(f)
    st = math.sin((f - 2186) * 2 * math.pi / 30)
    hp = Vector((SAWX, -3.0 + 0.055 * st, SZ))           # handle end point (cell side of the bars)
    R = align(sax, Vector((0, 1, 0)), side_ax, Vector((0, 0, 1)))      # the handle is the +axis end: toward the cell
    hend_local = sctr + sax * max(sext) * 0.5
    key_matrix(saw, f, Matrix.Translation(hp) @ R @ Ssc @ Matrix.Translation(-hend_local + sax * 0.03))
    dR, nR = hand_dirs(0, (0, 0, -1), (1, 0, 0))
    P_.key_hand("R", f, hp + Vector((-0.045, 0.06, 0.07)), dR, nR, Vector((-0.45, -2.45, 1.0)))
    dL, nL = hand_dirs(0, (0, 0, 1), (0, -1, 0))
    P_.key_hand("L", f, Vector((0.0, -3.13, 1.72)), dL, nL, Vector((0.45, -2.5, 1.1)))
pose_fingers(PR, "R", "wrap_grip", range(2186, 2441, 6))
# stand 15 cm further back so both arms work near-straight (the tight bend flipped the IK elbows)
SWR2 = Vector((0.05, -2.47, ZP + 0.03))
for f in range(2186, 2441, 1):
    st = math.sin((f - 2186) * 2 * math.pi / 30)
    root = SWR2 + Vector((0.0, 0.055 * st, 0))      # the body rocks with the stroke: the arm keeps one stable shape
    P_.key_root(f, root, yaw=0, flex=6)
    for s_ in "LR": P_.key_foot(s_, f, P_.foot_xy(s_, SWR2, 0), 0)
for f in range(2186, 2441, 1):
    for s_, px in (("R", -0.55), ("L", 0.55)):
        pb = P_.r.PB["Pole_elbow." + s_]; nme = "Pole_elbow." + s_
        pb.location = P_.r.rest(nme).to_3x3().inverted() @ (Vector((px, -2.75, 1.05)) - P_.r.BN[nme].head_local)
        pb.keyframe_insert("location", frame=f, group=nme)
for f in range(2186, 2441, 1):
    st = math.sin((f - 2186) * 2 * math.pi / 30)
    snap_hand(PR, "R", f, Vector((SAWX - 0.005, -2.97 + 0.055 * st, SZ + 0.005)), fist_point, iters=2)
pose_fingers(PR, "L", "wrap_grip", range(2186, 2441, 12))      # wrapped round the bar (grip_object gave a claw)
for f in range(2186, 2441, 10):
    P_.key_spine(f, flex=4, head=(8, 0 if not 2330 < f < 2380 else 60))
key_obj(saw, 2898, loc=saw.location.copy(), rot=saw.rotation_euler.copy())
L("saw re-staged")

# ================================================================== B. fence: elbows bent, body closer with the face turned, crouch on top, bent arms in the drop
FX = 7.0; M_Y = -13.8; LT = 3.1; OY = -14.18; OZ = 3.58
for f in range(1600, 1701, 4):
    u = (f - 1600) / 100.0; rz = ZP + (2.5 - ZP) * u
    ph = (f - 1600) / 20.0; a = (ph % 2) < 1
    hz = min(LT - 0.06, rz + 0.52)
    root = Vector((FX, M_Y + 0.36, rz))
    P_.key_root(f, root, yaw=0, flex=2); P_.key_spine(f, flex=2, head=(-12, 25))
    for s, sx, up in (("L", -1, a), ("R", 1, not a)):
        W = Vector((FX + sx * 0.2, M_Y + 0.1, hz + (0.05 if up else -0.22)))
        dd, nn = hand_dirs(0, (0, 0.1, 1), (0, 1, 0))
        P_.key_hand(s, f, W, dd, nn, root + Vector((sx * 0.45, 0.25, -0.45)))
        F = Vector((FX + sx * 0.16, M_Y + 0.2, rz - 0.82 + (0.18 if up else 0.0)))
        P_.r.key_world("IK_foot." + s, f, Matrix.Translation(F) @ Matrix.Rotation(R_(-30), 4, "X") @ Matrix.Translation(-P_.ankle[s]) @ P_.r.rest("IK_foot." + s))
        sc.frame_set(f); W_ = bw(PR, "wrist." + s)
        gripo(P_, s, f, O["Object_8"], Vector((W_.x, M_Y + 0.012, W_.z + 0.06)), (0, -1, 0), finger_dir=(0, 0, -1))
# crouch on the blanket at the outrigger end (1734-1750), then the drop with bent arms
for f, rt, flex, hh, fz in ((1734, (M_Y - 0.25, 3.84), 20, (M_Y - 0.2, 3.46), None), (1741, (OY + 0.02, 4.12), 35, (OY + 0.1, 3.66), OZ + 0.03),
                            (1748, (OY + 0.0, 4.1), 40, (OY + 0.12, 3.66), OZ + 0.03)):
    root = Vector((FX, rt[0], rt[1]))
    P_.key_root(f, root, yaw=0, flex=flex); P_.key_spine(f, flex=flex * 0.5, head=(-25, 0))
    for s, sx in (("L", -1), ("R", 1)):
        dd, nn = hand_dirs(0, (0, -0.3, -1), (0, 0, -1))
        P_.key_hand(s, f, Vector((FX + sx * 0.24, hh[0], hh[1])), dd, nn, root + Vector((sx * 0.5, 0.1, 0.0)))
        if fz is not None:
            F = Vector((FX + sx * 0.16, OY + 0.05, fz))
            P_.r.key_world("IK_foot." + s, f, Matrix.Translation(F) @ Matrix.Rotation(R_(10), 4, "X") @ Matrix.Translation(-P_.ankle[s]) @ P_.r.rest("IK_foot." + s))
g = 9.8; z0 = 4.1; zl = ground_z(FX, M_Y - 0.6) + ZP - 0.38
T = math.sqrt(2 * (z0 - zl) / g); t0 = max(1750, 1792 - int(round(T * 60)))
clear_keys(PR, t0, 1791)
for f in list(range(t0, 1790, 3)) + [1790]:
    t = (f - t0) / 60.0; z = max(zl, z0 - 0.5 * g * t * t); y = OY - min(1.0, t / T) * 0.42
    root = Vector((FX, y, z)); P_.key_root(f, root, yaw=0, flex=10); P_.key_spine(f, flex=6, head=(-5, 0))
    for s, sx in (("L", -1), ("R", 1)):
        dd, nn = hand_dirs(0, (0, -0.2, 1), (-sx, 0, 0))
        P_.key_hand(s, f, root + Vector((sx * 0.32, -0.15, 0.45)), dd, nn, root + Vector((sx * 0.6, 0.2, 0.1)))
        F = root + Vector((sx * 0.15, -0.08, -0.84))
        P_.r.key_world("IK_foot." + s, f, Matrix.Translation(F) @ Matrix.Translation(-P_.ankle[s]) @ P_.r.rest("IK_foot." + s))
L("fence: elbows bent, crouch on top, drop t0", t0)
# chain-link reads as chain-link at night: lift the wire colour
m8 = O["Object_8"].data.materials[0]
hsv = m8.node_tree.nodes.get("Hue/Saturation/Value")
if hsv: hsv.inputs["Value"].default_value = max(1.6, hsv.inputs["Value"].default_value * 1.8)
# blanket: real cloth (denser mesh, folds, fabric weave, soft hem) over the same profile
bl = O["Blanket"]; me_old = bl.data
prof = [(M_Y + 0.12, 2.95), (M_Y + 0.025, 3.13), (M_Y - 0.1, LT + (0.1 / 0.38) * (OZ - LT) + 0.035), (M_Y - 0.24, LT + (0.24 / 0.38) * (OZ - LT) + 0.035),
        (OY, OZ + 0.04), (OY - 0.06, OZ - 0.06), (OY - 0.09, OZ - 0.2)]
NX, NY = 24, 4
pts = []
for j in range(len(prof) - 1):
    for k in range(NY):
        u = k / NY; pts.append(tuple(prof[j][i] * (1 - u) + prof[j + 1][i] * u for i in range(2)))
pts.append(prof[-1])
vs, fs = [], []
for i in range(NX):
    x = FX - 0.5 + 1.0 * i / (NX - 1)
    for j, (y, z) in enumerate(pts):
        edge = 1.0 if j in (0, len(pts) - 1) else 0.3
        fold = 0.018 * math.sin(i * 0.9 + j * 0.35) + 0.01 * math.sin(i * 2.3) + edge * 0.03 * math.sin(i * 1.7 + 1.3)
        vs.append((x + 0.01 * math.sin(j * 1.1), y + fold * 0.4, z + fold))
for i in range(NX - 1):
    for j in range(len(pts) - 1):
        a_ = i * len(pts) + j; fs.append((a_, a_ + 1, a_ + 1 + len(pts), a_ + len(pts)))
me = bpy.data.meshes.new("BlanketCloth"); me.from_pydata(vs, [], fs); me.update()
for p in me.polygons: p.use_smooth = True
wool = bpy.data.materials.new("BlanketWool2"); wool.use_nodes = True; nt = wool.node_tree
bs = nt.nodes["Principled BSDF"]; bs.inputs["Roughness"].default_value = 1.0
try: bs.inputs["Sheen Weight"].default_value = 0.6
except KeyError: pass
wv = nt.nodes.new("ShaderNodeTexWave"); wv.inputs["Scale"].default_value = 60; wv.wave_type = "BANDS"
nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 18
mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = "RGBA"; mx.inputs["Factor"].default_value = 0.35
mx.inputs["A"].default_value = (0.20, 0.13, 0.08, 1); mx.inputs["B"].default_value = (0.32, 0.24, 0.15, 1)
nt.links.new(wv.outputs["Fac"], mx.inputs["Factor"]); nt.links.new(mx.outputs["Result"], bs.inputs["Base Color"])
bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.35
nt.links.new(nz.outputs["Fac"], bp.inputs["Height"]); nt.links.new(bp.outputs["Normal"], bs.inputs["Normal"])
me.materials.append(wool); bl.data = me
sol = bl.modifiers.new("thick", "SOLIDIFY"); sol.thickness = 0.012; sol.offset = 1.0
L("blanket cloth, chain-link lifted")

# ================================================================== C. tally (2898-2990): head up off the arm, scratching at chest height
TR = Vector((-0.78, -1.5, ZP)); TY = -90
nail = O["Nail"]; clear_tf(nail, 2896, 2992)
clear_hand(PR, "R", 2898, 2990)
for f in range(2898, 2991, 3):
    stroke = math.sin(f * 0.9)
    W = Vector((-1.24, -1.35 - 0.04 * (f - 2898) / 92 + 0.012 * stroke, 1.42 - 0.03 * stroke))
    dR, nR = hand_dirs(TY, (0.2, 1, 0.2), (0, 0, -1))
    P_.key_root(f, TR + Vector((0, 0, -0.005 * stroke)), yaw=TY)
    P_.key_spine(f, flex=2, head=(-6, -14))
    P_.key_hand("R", f, W, dR, nR, TR + Vector((0.1, 0.5, 0.15)))
pose_fingers(PR, "R", "pinch", range(2898, 2991, 6))
for f in range(2898, 2991, 3):
    sc.frame_set(f); pp = pinch_point(PR, "R")
    nail.matrix_world = Matrix.Translation(pp + Vector((-0.03, 0, 0))) @ Matrix.Rotation(R_(90), 4, "Y")
    nail.keyframe_insert("location", frame=f); nail.keyframe_insert("rotation_euler", frame=f)
L("tally re-posed")

# ================================================================== D. toolbox: 60 % size, still on the floor until his fist is on it
tbx = O["Toolbox"]; tbx.scale = tbx.scale * 0.8
FAr = O["Father"]; BOr = O["Boy"]
clear_tf(tbx, 943, 1421)
tbx.location = (2.2, 7.6, 0.0); tbx.rotation_euler = (0, 0, R_(-15))
for f in (0, 942, 999): tbx.keyframe_insert("location", frame=f); tbx.keyframe_insert("rotation_euler", frame=f)
tax, tctr, text = obj_local_axis(tbx); TBG = Vector((tctr.x, tctr.y, tctr.z + text.z * 0.5 - 0.01))
sc.frame_set(999); H0 = tbx.matrix_world @ TBG
for f in range(990, 1000, 2): snap_hand(FAr, "R", f, H0, fist_point, iters=2)
for f in range(1036, 1422, 4):           # the boy holds it a little further out from his leg
    sc.frame_set(f)
    hR = bw(BOr, "upperleg01.R"); hL = bw(BOr, "upperleg01.L"); side = (hR - hL).normalized()
    pb = BOr.pose.bones["IK_hand.R"]; Mw = BOr.matrix_world @ pb.matrix
    pb.matrix = BOr.matrix_world.inverted() @ (Matrix.Translation(side * 0.06) @ Mw); pb.keyframe_insert("location", frame=f, group=pb.name)
clear_tf(tbx, 1000, 1421)
def hang_from_fist(o, rig, s, f0, f1, grip_local, step=2):
    """carried by the handle: the handle point in the fist, the object upright (world up), its long axis along the knuckle line"""
    ax, ctr, ext = obj_local_axis(o); Sm = Matrix.Diagonal(o.matrix_world.to_scale()).to_4x4()
    for f in list(range(f0, f1 + 1, step)) + [f1]:
        sc.frame_set(f); c = fist_point(rig, s); _, n, d, a = hand_frame(rig, s)
        a.z = 0
        if a.length < 1e-4: a = Vector((1, 0, 0))
        R = align(ax, a.normalized(), Vector((0, 0, 1)), Vector((0, 0, 1)))
        key_matrix(o, f, Matrix.Translation(c) @ R @ Sm @ Matrix.Translation(-grip_local))
# the boy's free arm hangs relaxed (it was locked out sideways)
BO_ = H["Boy"]; clear_hand(BOr, "L", 1048, 1421)
for f in range(1048, 1422, 6):
    sc.frame_set(f); hR = bw(BOr, "upperleg01.R"); hL = bw(BOr, "upperleg01.L"); side = (hL - hR).normalized()
    fw = Vector((0, 0, 1)).cross(hR - hL).normalized()
    W = hL + side * 0.1 + fw * 0.05 + Vector((0, 0, 0.0))
    BO_.key_hand("L", f, W, Vector((0, 0, -1)), -side, W + side * 0.2 + Vector((0, 0, 0.35)) - fw * 0.25)
pose_fingers(BOr, "L", "relaxed", range(1048, 1422, 24))
hang_from_fist(tbx, FAr, "R", 1000, 1047, TBG)
hang_from_fist(tbx, BOr, "R", 1048, 1421, TBG)
L("toolbox")

# ================================================================== E. stepmother: a phone at her ear (the desk phone stays on the table)
SMr = O["Stepmother"]; SM_ = H["Stepmother"]
ph = O["Phone_Phone_0"]
while ph.parent: ph = ph.parent
clear_tf(ph, 1, 3750); ph.location = (6.9, 7.8, 0.55); ph.rotation_euler = (0, 0, R_(200))
for f in (0, 3750): ph.keyframe_insert("location", frame=f); ph.keyframe_insert("rotation_euler", frame=f)
bpy.ops.mesh.primitive_cube_add(size=1); mob = bpy.context.object; mob.name = "MobilePhone"
mob.scale = (0.072, 0.145, 0.009); bpy.ops.object.transform_apply(scale=True)
bv = mob.modifiers.new("b", "BEVEL"); bv.width = 0.006; bv.segments = 3
mm = bpy.data.materials.new("PhoneBlack"); mm.use_nodes = True
mm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.02, 0.02, 0.025, 1); mm.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.25
mob.data.materials.append(mm)
clear_hand(SMr, "R", 1128, 1421)
for f in range(1128, 1422, 4):
    sc.frame_set(f)
    hd = bw(SMr, "head"); hR = bw(SMr, "upperleg01.R"); hL = bw(SMr, "upperleg01.L"); side = (hR - hL).normalized()
    fw = Vector((0, 0, 1)).cross(hR - hL).normalized()
    W = hd + side * 0.13 + fw * 0.02 + Vector((0, 0, -0.1))
    SM_.key_hand("R", f, W, Vector((0, 0, 1)), -side, hd + side * 0.35 + Vector((0, 0, -0.45)) - fw * 0.2)
pose_fingers(SMr, "R", "wrap_grip", range(1128, 1422, 8))
bake_in_fist(mob, SMr, "R", 1128, 1421, step=4, grip_frac=0.35)
vis_key([mob], [(1128, 1421)])
SR = Vector((7.2, 8.3, SM_.root_head.z)); SYw = -35
for f in range(1140, 1422, 4):
    t = (f - 1140) / 60; pt = 0.5 + 0.5 * math.sin(t * 5)
    dL, nL = hand_dirs(SYw, (-0.4, 1, 0.3), (0, 0, -1))
    SM_.key_hand("L", f, rel(SR, SYw, (-0.24, 0.27 + 0.04 * pt, 0.3)), dL, nL, rel(SR, SYw, (-0.5, -0.3, -0.1)))
L("stepmother phone at ear, elbow bent")

# ================================================================== F. judge: smaller gavel
gav = O["Gavel"]; gav.scale = gav.scale * 0.65
JUr = O["Judge"]; clear_tf(gav, 1380, 1547)
gax, _, _ = obj_local_axis(gav)
GHEAD = Vector((0, 1, 0)) if abs(gax.x) > 0.5 else Vector((1, 0, 0))
bake_in_fist(gav, JUr, "R", 1380, 1547, grip_frac=0.12, handle_ref=(0, Vector((10.2, 7.48, 1.2))), up_axis=GHEAD)
L("gavel smaller")

# ================================================================== G. old man (beat 13): one clear gesture, he lifts his head to the window light
PO_ = H["PrisonerOld"]
for f, hd in ((3228, (28, 4)), (3330, (30, 0)), (3370, (22, 6)), (3392, (-18, 22)), (3430, (-20, 26)), (3446, (-10, 10))):
    PO_.key_spine(f, flex=24 if f < 3392 else 12, head=hd)
L("old man gesture")

# guard: his hair mesh covered his eyes (client: no hair over the face); short-cropped look instead
_gh = O["Guard.short03"]
for fc in [f for f in fcurves_of(_gh) if f.data_path in ("hide_render", "hide_viewport")]:
    for k in list(fc.keyframe_points)[::-1]: fc.keyframe_points.remove(k)
_gh.hide_render = True; _gh.hide_viewport = True
# ================================================================== V9. director's v008 review
# blanket hidden once he is over (it read as a floating block above the fence)
vis_key([O["Blanket"]], [(1548, 1760)])
# soft slot light (its hard edge drew a pale "mask" patch across the face)
_sl = O["SlotLight"].data; _sl.spot_blend = 1.0; _sl.shadow_soft_size = 0.35
# no police strobe in the courtroom: steady light from 1422
for nm in ("PoliceRed", "PoliceBlue"):
    Ld = O[nm].data
    for fc in fcurves_of(Ld):
        if fc.data_path == "energy":
            for k in [k for k in fc.keyframe_points if k.co.x >= 1422][::-1]: fc.keyframe_points.remove(k)
    Ld.energy = 0; Ld.keyframe_insert("energy", frame=1422)
    for fc in fcurves_of(Ld):
        for k in fc.keyframe_points: k.interpolation = "CONSTANT"
# boy at the workbench: elbows bent, hands on the coins
BOr = O["Boy"]; BO_ = H["Boy"]; BR = Vector((0.45, 8.05, BO_.root_head.z))
clear_hand(BOr, "L", 680, 941); clear_hand(BOr, "R", 680, 941)
for f in range(680, 942, 6):
    t = (f - 680) / 60.0; jit = 0.012 * math.sin(t * 9); jit2 = 0.01 * math.cos(t * 7)
    dL, nL = hand_dirs(180, (0.3, 1, -0.6), (0.2, 0, -1)); dR, nR = hand_dirs(180, (-0.3, 1, -0.6), (-0.2, 0, -1))
    BO_.key_hand("L", f, Vector((0.33 + jit, 8.4, 0.75)), dL, nL, Vector((0.05, 8.05, 0.45)))
    BO_.key_hand("R", f, Vector((0.57, 8.39 + jit2, 0.76 + abs(jit))), dR, nR, Vector((0.85, 8.05, 0.45)))
pose_fingers(BOr, "L", "pinch", range(680, 942, 30)); pose_fingers(BOr, "R", "pinch", range(680, 942, 30))
# boy reacting to the stepmother (no frozen hold): looks down at the box, flinches when she shouts, looks up at her
for bn in ('bones["spine', 'bones["neck', 'bones["head"]'):
    clear_keys(BOr, 1136, 1421, bn)
for f, fl, hd in ((1136, 4, (22, 0)), (1180, 6, (28, 12)), (1222, 4, (20, 8)), (1230, -10, (-8, 28)), (1250, -4, (0, 30)),
                  (1295, 4, (18, -12)), (1340, 2, (6, 18)), (1380, 6, (24, 4)), (1421, 4, (16, 0))):
    BO_.key_spine(f, flex=fl, head=hd)
# judge: bent-elbow strike onto the block, other hand flat on the desk
JUr = O["Judge"]; JU_ = H["Judge"]
clear_hand(JUr, "R", 1380, 1547); clear_hand(JUr, "L", 1380, 1547)
strike = [(1380, 0.0), (1415, -0.9), (1432, -1.1), (1440, 0.03), (1446, -0.12), (1452, 0.0), (1470, -0.7), (1478, 0.02), (1500, 0.0)]
SPk = catmull([(f, a) for f, a in strike])
for f in range(1380, 1548, 2):
    a = max(0.0, -SPk(f))
    W = Vector((10.1, 7.52 + 0.03 * a, 1.17 + 0.2 * a))
    dR, nR = hand_dirs(0, (0, -1, -0.2 + 0.6 * a), (1, 0, 0))
    JU_.key_hand("R", f, W, dR, nR, Vector((9.85, 8.0, 0.95)))
    dL, nL = hand_dirs(0, (0, -1, 0), (0, 0, -1))
    JU_.key_hand("L", f, Vector((10.58, 7.6, 1.15)), dL, nL, Vector((10.95, 8.0, 0.95)))
pose_fingers(JUr, "R", "wrap_grip", range(1380, 1548, 8)); pose_fingers(JUr, "L", "flat_palm", range(1380, 1548, 24))
# corridor run: arms bent and pumping (no A-pose), tube stays in the right fist
tube = O["ToothpasteTube"]
clear_hand(PR, "L", 2696, 2898); clear_hand(PR, "R", 2696, 2898)
for f in range(2696, 2899, 2):
    sc.frame_set(f); r = bw(PR, "root"); yw = 90
    ph = (f - 2696) * 2 * math.pi / 25.0
    for s_, sg in (("L", -1), ("R", 1)):
        sw = math.sin(ph + (0 if s_ == "L" else math.pi))
        W = rel(r, yw, (sg * 0.2, 0.26 * sw, 0.12 + 0.12 * max(0.0, sw)))
        d_, n_ = hand_dirs(yw, (0, 0.6, 0.8), (-sg, 0, 0))
        P_.key_hand(s_, f, W, d_, n_, rel(r, yw, (sg * 0.35, -0.45, -0.05)))
pose_fingers(PR, "L", "wrap_grip", range(2696, 2899, 12)); pose_fingers(PR, "R", "wrap_grip", range(2696, 2899, 12))
clear_tf(tube, 2694, 2898)
bake_in_fist(tube, PR, "R", 2694, 2898, grip_frac=0.3)
# ending: the old man stands at the cell-front bars, both hands on the bars, face in a gap between bars
POr = O["PrisonerOld"]; PO_ = H["PrisonerOld"]
clear_keys(POr, 3676, 3750)
GAPX = 0.4025; ER = Vector((GAPX, -0.48, PO_.root_head.z))
for f in range(3676, 3751, 4):
    b = 0.006 * math.sin(f / 12)
    dd, nn_ = hand_dirs(180, (0, 0.3, 1), (0, 1, 0))
    pose(PO_, f, ER + Vector((0, 0, b)), yaw=180, spine=(3, 0, 0), head=(-2, 2 * math.sin(f / 30)),
         hands={"L": (Vector((0.23, -0.07, 1.24)), dd, nn_, ER + Vector((-0.5, 0.0, -0.3))), "R": (Vector((0.575, -0.07, 1.24)), dd, nn_, ER + Vector((0.5, 0.0, -0.3)))},
         fingers={"L": 0.85, "R": 0.85})
    face(PO_, f, brow=0.3, lid=0.15)
    if (f - 3676) % 8 == 0:
        for s_, bx in (("L", 0.23), ("R", 0.575)):
            gripo(PO_, s_, f, O["CellFront_0"], (bx, -0.017, 1.24), (0, 1, 0), finger_dir=(0, 0, -1))
gav = O["Gavel"]; clear_tf(gav, 1380, 1547)
gax2, gctr2, gext2 = obj_local_axis(gav); GL = max(gext2)
sc.frame_set(0)
e0 = gctr2 - gax2 * GL * 0.5; e1 = gctr2 + gax2 * GL * 0.5
gp0 = Vector((10.2, 7.48, 1.2))
hend, headend = (e0, e1) if (gav.matrix_world @ e0 - gp0).length < (gav.matrix_world @ e1 - gp0).length else (e1, e0)
hdir = (headend - hend).normalized(); gside = Vector((1, 0, 0)) if abs(hdir.x) < 0.7 else Vector((0, 1, 0))
GSm = Matrix.Diagonal(gav.matrix_world.to_scale()).to_4x4()
for f in list(range(1380, 1548, 2)):
    a = max(0.0, -SPk(f)); th = 0.6 - a
    Hd = Vector((0, -math.cos(th), -math.sin(th)))
    sc.frame_set(f); c = fist_point(JUr, "R")
    R = align(hdir, Hd, gside, Vector((1, 0, 0)))
    key_matrix(gav, f, Matrix.Translation(c) @ R @ GSm @ Matrix.Translation(-(hend + (headend - hend) * 0.12)))
L("v009 re-stages")
# ================================================================== H. camera: short shots with clean cuts, following the acting face
cam = sc.camera
for c in list(cam.constraints): cam.constraints.remove(c)
cam.animation_data_clear(); cam.data.animation_data_clear()
for nm in ("Corridor_FarWall", "CellFront_0"):
    o = O[nm]
    for fc in fcurves_of(o):
        if fc.data_path in ("hide_render", "hide_viewport"):
            for k in list(fc.keyframe_points)[::-1]: fc.keyframe_points.remove(k)
    o.hide_render = False; o.hide_viewport = False
cam.data.dof.use_dof = True; cam.data.dof.aperture_fstop = 11.0
cam.rotation_mode = "QUATERNION"
# (frame, subject, bone, offset0 (fwd, right, up), offset1, lens0, lens1, target z offset, fixed (cam_pos, target_pos) or None)
S = [
    (0, "Guard", "head", (2.4, 0.7, 0.3), (2.0, 0.6, 0.25), 26, 28, -0.45, None),
    (60, "Guard", "upperleg01.R", (1.7, 0.55, 0.35), (1.55, 0.5, 0.33), 30, 32, 0.15, None),     # the key ring on his hip
    (100, "Prisoner", "head", (1.1, -0.2, 0.0), (0.8, -0.1, 0.0), 32, 40, 0.0, None),
    (200, "Prisoner", "head", None, None, 50, 50, 0.0, ((0.4025, 0.2, 1.66), None)),
    (236, "Prisoner", "head", (1.6, 0.5, 0.3), (1.5, 0.5, 0.3), 24, 24, -0.2, None),
    (300, "Prisoner", "spine03", (0.95, -0.4, 0.3), (0.9, -0.4, 0.3), 34, 34, 0.08, None),
    (541, "Prisoner", "head", (1.5, 0.3, 0.2), (1.5, 0.3, 0.2), 26, 26, -0.15, None),
    (600, None, None, None, None, 30, 32, 0.0, ((0.45, 0.85, 1.3), (-0.12, -0.12, 1.15))),
    (626, "Prisoner", "head", (1.4, 0.9, 0.25), (1.6, 0.8, 0.3), 26, 26, -0.2, None),       # the door swings toward the lock camera: cut
    (652, "Prisoner", "head", None, None, 30, 30, -0.15, ((0.95, 1.35, 1.65), None)),     # corridor, on the side away from the open door (the door panel stays behind him)
    (678, "Boy", "head", (0.45, -0.75, 0.12), (0.42, -0.72, 0.12), 40, 42, -0.2, None),
    (790, "Father", "head", (1.6, 0.2, 0.05), (1.5, 0.2, 0.05), 32, 32, -0.1, None),
    (860, "Boy", "head", (0.5, -0.75, 0.15), (0.48, -0.72, 0.15), 40, 42, -0.2, None),
    (942, "Father", "head", (2.4, 0.9, 0.35), (2.2, 0.9, 0.3), 26, 26, -0.5, None),
    (1046, "Boy", "head", (1.3, 0.5, 0.15), (1.2, 0.5, 0.15), 30, 30, -0.2, None),
    (1115, "Stepmother", "head", (1.45, -0.5, 0.05), (1.3, -0.45, 0.05), 34, 36, -0.12, None),
    (1218, "Boy", "head", (1.2, 0.4, 0.05), (1.1, 0.4, 0.05), 32, 32, -0.15, None),
    (1340, "Boy", "head", (1.6, -0.6, 0.2), (1.5, -0.6, 0.2), 28, 28, -0.2, None),
    (1422, "Judge", "head", (1.7, 0.35, 0.0), (1.6, 0.35, 0.0), 44, 44, -0.32, None),
    (1472, "Guard", "head", None, None, 30, 32, -0.35, ((4.3, 1.25, 1.8), None)),
    (1548, "Prisoner", "head", (1.8, 1.5, 0.4), (1.6, 1.4, 0.4), 28, 28, -0.2, None),
    (1588, "Prisoner", "head", (2.0, -0.6, 0.1), (2.0, -0.6, 0.1), 34, 34, -0.25, None),      # outside the fence, his face through the wire
    (1712, "Prisoner", "head", None, None, 26, 26, -0.3, ((8.2, -15.5, 3.1), None)),
    (1756, "Prisoner", "head", (2.6, 0.5, -0.1), (2.6, 0.5, 0.0), 26, 26, -0.2, None),
    (1860, None, None, None, None, 24, 24, 0.0, ((0.95, -2.6, 1.75), (-0.3, -0.5, 1.45))),     # the solitary door as he is brought in
    (1866, "Prisoner", "head", None, None, 24, 24, -0.2, ((0.95, -2.6, 1.75), None)),
    (1946, "Prisoner", "head", (1.1, 0.35, -0.25), (1.05, 0.35, -0.25), 32, 32, 0.0, None),
    (2040, "Prisoner", "head", None, None, 30, 30, -0.15, ((-0.6, -1.45, 1.45), None)),
    (2140, "Prisoner", "head", None, None, 26, 26, -0.2, ((-0.95, -0.9, 1.75), None)),
    (2186, None, None, None, None, 28, 28, 0.0, ((-0.75, -2.5, 1.95), (-0.02, -3.03, 1.56))),   # his fist on the saw handle, blade through the gap, left hand on the bar
    (2310, "Prisoner", "head", None, None, 26, 26, -0.15, ((0.85, -2.8, 1.72), None)),
    (2440, "Prisoner", "head", (1.5, 0.4, 0.3), (1.5, 0.4, 0.3), 26, 26, -0.2, None),
    (2508, "Prisoner", "head", None, None, 26, 26, -0.25, ((1.2, 1.35, 1.7), None)),
    (2590, "Prisoner", "head", (0.6, 1.0, 0.25), (0.6, 1.0, 0.25), 24, 24, -0.25, None),
    (2700, "Prisoner", "head", None, None, 28, 30, -0.25, ((8.6, 1.6, 1.75), None)),
    (2790, "Prisoner", "head", (1.2, -1.15, 0.2), (1.2, -1.15, 0.2), 26, 26, -0.2, None),
    (2898, "Prisoner", "head", (1.2, 0.95, 0.1), (1.15, 0.9, 0.1), 26, 26, -0.05, None),
    (2992, "Prisoner", "head", None, None, 26, 26, -0.2, ((1.1, -1.0, 1.7), None)),
    (3052, "Prisoner", "head", (1.1, 0.35, -0.2), (1.05, 0.35, -0.2), 32, 32, 0.0, None),     # seated: face, not his back
    (3166, "PrisonerOld", "head", (1.3, 0.4, 0.05), (1.25, 0.4, 0.05), 30, 30, -0.1, None),
    (3228, "PrisonerOld", "head", (1.4, -0.5, -0.1), (1.35, -0.5, -0.1), 30, 30, -0.1, None),
    (3360, "PrisonerOld", "head", (0.9, 0.3, -0.15), (0.85, 0.3, -0.12), 40, 40, 0.0, None),
    (3446, "PrisonerOld", "head", None, None, 26, 26, -0.2, ((-0.85, -1.4, 1.75), None)),
    (3498, "PrisonerOld", "head", None, None, 28, 28, -0.1, ((0.9, -2.35, 1.75), None)),
    (3530, "Protester1", "head", (3.0, -0.9, 0.2), (2.8, -0.9, 0.2), 28, 28, -0.25, None),
    (3618, "Protester2", "head", (1.6, -0.5, 0.05), (1.5, -0.5, 0.05), 32, 32, -0.15, None),
    (3680, None, None, None, None, 24, 26, 0.0, ((0.4025, 0.55, 1.56), (0.4025, -0.6, 1.4), (0.4025, 0.3, 1.6))),
    (3751, None, None, None, None, 0, 0, 0, None),
]
SKIP = tuple(CAST) + ("WinBar", "CellFront", "Hacksaw", "hacksaw", "Toolbox", "Gavel", "Phone", "Mobile", "Nail", "Tube", "ScrapKey", "File_", "Placard", "Candle", "Blanket", "Spark", "Filing", "KeyRing", "GuardKey", "Crumpled", "Object_8", "Razor")
def cast_free(dg, a, b):
    """from target a toward camera b: return the first blocking point (ignoring characters, props, bars), or None"""
    d = b - a; dist = d.length; d.normalize(); p = a.copy(); travelled = 0.0
    for _ in range(12):
        hit, loc, n, i, ob, _m = sc.ray_cast(dg, p, d, distance=dist - travelled)
        if not hit: return None
        if not ob.name.startswith(SKIP) and not (ob.parent and ob.parent.name.startswith(SKIP)):
            return loc
        travelled += (loc - p).length + 0.002; p = loc + d * 0.002
        if travelled >= dist: return None
    return None
def facing(rig):
    hR = bw(rig, "upperleg01.R"); hL = bw(rig, "upperleg01.L")
    v = Vector((0, 0, 1)).cross(hR - hL); v.z = 0
    return v.normalized() if v.length > 1e-6 else Vector((0, -1, 0))
cuts = []
for si in range(len(S) - 1):
    f0, sub, bone, o0, o1, l0, l1, tz, fixed = S[si]; f1 = S[si + 1][0] - 1
    cuts.append(f0)
    if fixed is not None and fixed != "SAW":
        cp0 = Vector(fixed[0]); tp0 = Vector(fixed[1]) if fixed[1] is not None else None
        cp1 = Vector(fixed[2]) if len(fixed) > 2 else cp0
    if sub:
        rig = O[sub]
        tr = {}; fa = Vector()
        for f in range(f0, f1 + 1):
            sc.frame_set(f); tr[f] = bw(rig, bone) + Vector((0, 0, tz)); fa += facing(rig)
        fa.z = 0; fa.normalize(); rt = fa.cross(Vector((0, 0, 1)))
    rows = []
    for f in range(f0, f1 + 1):
        u = (f - f0) / max(1, f1 - f0); u = u * u * (3 - 2 * u)
        lens = l0 + (l1 - l0) * u
        if sub and fixed is not None and fixed != "SAW":
            w = [tr[k] for k in range(max(f0, f - 8), min(f1, f + 8) + 1)]
            T_ = sum(w, Vector()) / len(w); C = cp0
        elif sub:
            w = [tr[k] for k in range(max(f0, f - 8), min(f1, f + 8) + 1)]
            T_ = sum(w, Vector()) / len(w)
            off = Vector(o0).lerp(Vector(o1), u)
            C = T_ + fa * off.x + rt * off.y + Vector((0, 0, off.z))
            if fixed == "SAW":
                T_ = T_.lerp(Vector((0.03, -3.12, 1.58)), 0.75)
        else:
            C, T_ = cp0.lerp(cp1, u), tp0
        sc.frame_set(f); dg = bpy.context.evaluated_depsgraph_get()
        blk = cast_free(dg, T_, C) if (fixed is None or fixed == "SAW") else None     # fixed cameras were placed clear: never pulled in
        k = 1.0
        if blk is not None:
            dvec = (C - T_); L0 = dvec.length; dvec.normalize()
            Ln = max(0.3, (blk - T_).length - 0.12); k = Ln / max(L0, 1e-6)
        rows.append((f, C, T_, lens, k))
    # pull-in smoothed: the closest needed distance over +-14 frames, then eased (no camera pops inside a shot)
    ks = [r[4] for r in rows]; n = len(ks)
    km = [min(ks[max(0, i - 14):i + 15]) for i in range(n)]
    ksm = [sum(km[max(0, i - 7):i + 8]) / len(km[max(0, i - 7):i + 8]) for i in range(n)]
    for (f, C, T_, lens, _), kk in zip(rows, ksm):
        C = T_ + (C - T_) * min(1.0, kk)
        q = (T_ - C).to_track_quat("-Z", "Y")
        cam.location = C; cam.keyframe_insert("location", frame=f)
        cam.rotation_quaternion = q; cam.keyframe_insert("rotation_quaternion", frame=f)
        cam.data.lens = lens; cam.data.keyframe_insert("lens", frame=f)
        cam.data.dof.focus_distance = (T_ - C).length; cam.data.dof.keyframe_insert("focus_distance", frame=f)
    L("shot", f0, f1, sub)
for fc in fcurves_of(cam) + fcurves_of(cam.data):
    for k in fc.keyframe_points: k.interpolation = "LINEAR"
import json
json.dump({"cuts": cuts}, open(OUT.replace(".blend", "_cuts.json"), "w"))
sc.frame_set(0)
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
L("SAVED", OUT)
