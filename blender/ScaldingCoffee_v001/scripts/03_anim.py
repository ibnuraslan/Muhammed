"""B09 ScaldingCoffee: characters, animation (each beat a clip in its own window), cameras + markers.
blender -b work/sets.blend --python 03_anim.py -- out.blend [beats=B1,B2,...]"""
import bpy, sys, math, json
from mathutils import Vector, Matrix, Quaternion, Euler
W = "/tmp/claude-0/b09/"; P = "/home/user/Muhammed/blender/pipeline/"
a = sys.argv[sys.argv.index("--") + 1:]; OUT = a[0]
ONLY = set(a[1].split(",")) if len(a) > 1 else None
exec(open(P + "anim_lib.py").read())
exec(open(P + "hand_poses.py").read())
sc = bpy.context.scene; R_ = math.radians
sc.frame_start, sc.frame_end = 1, 2860
FLOORS = []
def ground_z(x, y):
    dg = bpy.context.evaluated_depsgraph_get(); best = 0.0
    for o in FLOORS:
        oe = o.evaluated_get(dg); inv = oe.matrix_world.inverted()
        hit, loc, nrm, idx = oe.ray_cast(inv @ Vector((x, y, 5.0)), (inv.to_3x3() @ Vector((0, 0, -1))).normalized())
        if hit: best = max(best, (oe.matrix_world @ loc).z)
    return best

# ------------------------------------------------------------------ characters
def load_char(cid, new=None):
    with bpy.data.libraries.load(W + "work/ch_%s.blend" % cid, link=False) as (fd, td): td.objects = list(fd.objects)
    new = new or cid; c = bpy.data.collections.new("CH_" + new); sc.collection.children.link(c)
    rig = None
    objs = [o for o in td.objects if o]
    arms = [o for o in objs if o.type == 'ARMATURE']
    rig = max(arms, key=lambda r: sum(1 for ch in r.children if ch.type == 'MESH'))
    for o in objs:
        if o.type == 'ARMATURE' and o != rig: bpy.data.objects.remove(o); continue
        if o.parent is None and o != rig: bpy.data.objects.remove(o); continue
        c.objects.link(o); o.hide_render = False; o.hide_viewport = False
    if new != cid:
        for o in list(c.objects):
            if o.type == 'ARMATURE': o.name = new
            else: o.name = new + "." + o.name.split(".", 1)[1]
    return rig

def eye_fix_all():
    for g in bpy.data.node_groups:
        if not g.name.startswith("EnhancedEye") or g.nodes.get("CorneaTransparentMix"): continue
        Pn = next((n for n in g.nodes if n.type == "BSDF_PRINCIPLED"), None)
        OUTN = next((n for n in g.nodes if n.type == "GROUP_OUTPUT"), None)
        if not Pn or not OUTN: continue
        tl = [l for l in g.links if l.to_node == Pn and l.to_socket.name == "Transmission Weight"]
        src = tl[0].from_socket if tl else None
        for l in tl: g.links.remove(l)
        Pn.inputs["Transmission Weight"].default_value = 0.0
        ol = [l for l in g.links if l.from_node == Pn and l.to_node == OUTN]
        if not ol: continue
        out_sock = ol[0].to_socket; g.links.remove(ol[0])
        tr = g.nodes.new("ShaderNodeBsdfTransparent"); mx = g.nodes.new("ShaderNodeMixShader"); mx.name = "CorneaTransparentMix"
        if src: g.links.new(src, mx.inputs[0])
        else: mx.inputs[0].default_value = 0.0
        g.links.new(Pn.outputs[0], mx.inputs[1]); g.links.new(tr.outputs[0], mx.inputs[2]); g.links.new(mx.outputs[0], out_sock)
        print("EYEFIX", g.name)

def tint(rig, key, rgb, mode='MULTIPLY', fac=1.0):
    for ch in rig.children:
        if ch.type == 'MESH' and key in ch.name:
            for i, m in enumerate(ch.data.materials):
                if not m: continue
                m = m.copy(); ch.data.materials[i] = m; nt = m.node_tree
                done = False
                for nd in list(nt.nodes):
                    if nd.type == 'TEX_IMAGE' and nd.image and "normal" not in nd.image.name.lower() and nd.outputs['Color'].links:
                        for lk in list(nd.outputs['Color'].links):
                            mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = mode
                            mx.inputs['Factor'].default_value = fac; mx.inputs['B'].default_value = (*rgb, 1)
                            nt.links.new(nd.outputs['Color'], mx.inputs['A']); nt.links.new(mx.outputs['Result'], lk.to_socket); done = True
                if not done:
                    for nd in nt.nodes:
                        if nd.type == 'BSDF_PRINCIPLED' and not nd.inputs["Base Color"].links:
                            nd.inputs["Base Color"].default_value = (*rgb, 1)

RIGS = {}; HUM = {}; CUR_WIN = None
def setup(cid, new=None):
    rig = load_char(cid, new); name = new or cid
    R = make_human_ctrl(rig); add_hand_limits(rig)
    for s in "LR":   # MPFB rest elbow ~46 deg: open the IK limit so arms can straighten (LESSONS 8)
        lo = rig.pose.bones["lowerarm01." + s]; lo.use_ik_limit_x = True; lo.ik_min_x = R_(-40); lo.ik_max_x = R_(110)
    H = Human(R); RIGS[name] = rig; HUM[name] = H
    if CUR_WIN:
        f0, f1 = CUR_WIN
        for ob in [rig] + list(rig.children):
            for f, show in ((1, f0 <= 1), (f0, True), (f1 + 1, False)):
                if f < 1: continue
                ob.hide_render = not show; ob.hide_viewport = not show
                ob.keyframe_insert("hide_render", frame=f); ob.keyframe_insert("hide_viewport", frame=f)
    rig["char"] = name
    return rig, R, H

def catchlight(rig, cam, f_on, f_off):
    """small camera-only point light near the lens for an eye catchlight (LESSONS 8)"""
    l = bpy.data.lights.new("Catch_" + cam.name, 'POINT'); l.energy = 0.6; l.shadow_soft_size = 0.02
    o = bpy.data.objects.new("Catch_" + cam.name, l); sc.collection.objects.link(o); o.parent = cam; o.location = (0.05, 0.06, 0)
    o.visible_diffuse = o.visible_glossy = True
    return o

# ------------------------------------------------------------------ cameras, markers, visibility
CAMS = []
def cam_shot(name, f0, f1, keys, lens=35, fstop=8.0, focus=None):
    """keys: list of (frame, loc, target); smooth Bezier between; horizon level (track-quat with world up)"""
    c = bpy.data.objects.new(name, bpy.data.cameras.new(name)); sc.collection.objects.link(c)
    c.data.lens = lens; c.data.clip_start = 0.01; c.data.sensor_fit = 'AUTO'
    c.data.dof.use_dof = True; c.data.dof.aperture_fstop = fstop
    for f, loc, tgt in keys:
        c.location = loc; d = Vector(tgt) - Vector(loc)
        c.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
        c.keyframe_insert("location", frame=f); c.keyframe_insert("rotation_euler", frame=f)
        c.data.dof.focus_distance = d.length if focus is None else focus; c.data.dof.keyframe_insert("focus_distance", frame=f)
    m = sc.timeline_markers.new(name, frame=f0); m.camera = c
    CAMS.append((name, f0, f1, c))
    return c

def vis(o, f, show):
    for ob in [o] + list(o.children_recursive):
        ob.hide_render = not show; ob.hide_viewport = not show
        ob.keyframe_insert("hide_render", frame=f); ob.keyframe_insert("hide_viewport", frame=f)

def keyconst(fc_owner):
    pass

def set_interp(obj, kind='CONSTANT', path=None):
    ad = obj.animation_data
    if not ad or not ad.action: return
    for fc in _fcurves(ad.action):
        if path is None or fc.data_path == path:
            for k in fc.keyframe_points: k.interpolation = kind

def _fcurves(act):
    if hasattr(act, "fcurves") and len(getattr(act, "fcurves", [])):
        return list(act.fcurves)
    out = []
    for layer in getattr(act, "layers", []):
        for strip in layer.strips:
            for cb in getattr(strip, "channelbags", []): out += list(cb.fcurves)
    return out

def breathe(H, f0, f1, base_flex=0.0, twist=0.0, head=(0.0, 0.0), amp=1.6, period=200, extra=None, step=20):
    """slow breathing + small head drift so no hold is frozen (keys every `step` frames)"""
    for f in range(f0, f1 + 1, step):
        ph = math.sin(2 * math.pi * (f - f0) / period)
        hx, hz = head(f) if callable(head) else head
        H.key_spine(f, flex=base_flex + amp * ph, twist=twist, head=(hx + 0.5 * ph, hz))

def pole(R, s, f, W):
    n = "Pole_elbow." + s; pb = R.PB[n]
    pb.location = R.rest(n).to_3x3().inverted() @ (Vector(W) - R.BN[n].head_local); pb.keyframe_insert("location", frame=f, group=n)

def knee_pole(R, s, f, W):
    n = "Pole_knee." + s; pb = R.PB[n]
    pb.location = R.rest(n).to_3x3().inverted() @ (Vector(W) - R.BN[n].head_local); pb.keyframe_insert("location", frame=f, group=n)

def foot_at(R, H, s, f, W, yaw=0.0, pitch=0.0):
    a_ = H.ankle[s]
    M = Matrix.Translation(Vector(W)) @ Matrix.Rotation(R_(yaw), 4, 'Z') @ Matrix.Rotation(R_(pitch), 4, 'X') @ Matrix.Translation(-a_) @ R.rest("IK_foot." + s)
    R.key_world("IK_foot." + s, f, M)

def child_of_hand(obj, rig, side, f_on, f_off=None):
    """Child Of the hand bone from f_on (grip), off at f_off (release); keyed influence"""
    c = obj.constraints.new('CHILD_OF'); c.target = rig; c.subtarget = "wrist." + side; c.name = "Grip_" + side
    sc.frame_set(f_on); bpy.context.view_layer.update()
    c.inverse_matrix = (rig.matrix_world @ rig.pose.bones["wrist." + side].matrix).inverted()
    c.influence = 0.0; c.keyframe_insert("influence", frame=f_on - 1)
    c.influence = 1.0; c.keyframe_insert("influence", frame=f_on)
    if f_off:
        c.influence = 1.0; c.keyframe_insert("influence", frame=f_off - 1); c.influence = 0.0; c.keyframe_insert("influence", frame=f_off)
    return c

ALL_BEATS = ["B1", "B2", "B3", "B4", "B5", "B6"]
def want(b): return ONLY is None or b in ONLY

# ================================================================== B1 spill (1..420)
exec(open(W + "scripts/lib_props.py").read())

def bone_w(rig, n, tail=False):
    pb = rig.pose.bones[n]; return rig.matrix_world @ (pb.tail if tail else pb.head)

def hand_delta(R, s, f_src, f_dst, delta, rot=None):
    """key IK_hand.<s> at f_dst = its pose at f_src moved by world delta (and optional world rotation about the wrist)"""
    sc.frame_set(f_src); pb = R.PB["IK_hand." + s]; M = pb.matrix.copy()
    if rot is not None:
        t = M.translation.copy(); M = Matrix.Translation(t) @ rot.to_4x4() @ Matrix.Translation(-t) @ M
    M = Matrix.Translation(Vector(delta)) @ M
    R.key_world("IK_hand." + s, f_dst, M)

def hold_fingers(rig, s, f_src, f_dst):
    sc.frame_set(f_src)
    for k in (1, 2, 3, 4, 5):
        for j in (1, 2, 3):
            pb = rig.pose.bones["finger%d-%d.%s" % (k, j, s)]; pb.keyframe_insert("rotation_quaternion", frame=f_dst, group=pb.name)

def beat_B1():
    FLOORS[:] = [bpy.data.objects["CarFloor"]]
    cC = bpy.data.collections["SetCar"]
    rig, R, H = setup("GranH", "GranC")
    tint(rig, "ponytail", (1.35, 1.35, 1.4))
    tint(rig, "elegantsuit", (0.80, 0.74, 0.95), "MIX", 0.62)     # light lavender outfit: the coffee stain must read
    sx = -0.42; hip = Vector((sx, -0.06, 0.70))
    knee = {"L": Vector((sx + 0.11, -0.52, 0.70)), "R": Vector((sx - 0.11, -0.52, 0.70))}
    lean = {1: -8, 250: -8, 268: -17, 300: -15, 340: -12, 420: -12}
    for f, l in lean.items(): H.key_root(f, hip, flex=l)
    for f in (1, 420):
        for s in "LR":
            foot_at(R, H, s, f, Vector((knee[s].x, -0.60, 0.33 + H.ankle[s].z)))
            knee_pole(R, s, f, knee[s] + Vector((0, -0.6, 0.15)))
    # spine/head: look down at the cup while opening it, recoil at the spill, then look down at her lap
    def headf(f):
        if f < 250: return (22.0, 0.0)
        if f < 270: return (22.0 - 30 * (f - 250) / 20, 4.0 * (f - 250) / 20)
        if f < 330: return (-8.0 + 6 * (f - 270) / 60, 4.0)
        return (-2.0 + 14 * min(1, (f - 330) / 50), 4.0 - 4 * min(1, (f - 330) / 50))
    for f in range(1, 421, 10):
        ph = math.sin(2 * math.pi * f / 180); hx, hz = headf(f)
        H.key_spine(f, flex=(10 if f < 250 else 4) + 1.4 * ph, head=(hx + 0.4 * ph, hz))
    for s in "LR":
        pole(R, s, 1, Vector((sx + (0.5 if s == "L" else -0.5), 0.25, 0.75))); pole(R, s, 420, Vector((sx + (0.5 if s == "L" else -0.5), 0.25, 0.75)))
    sc.frame_set(1); bpy.context.view_layer.update()
    kL = bone_w(rig, "lowerleg01.L"); kR = bone_w(rig, "lowerleg01.R"); hL = bone_w(rig, "upperleg01.L"); hR = bone_w(rig, "upperleg01.R")
    print("B1 knees", kL, kR, "hips", hL, hR)
    # cup wedged between the thighs near the knees
    cpos = (kL + kR) / 2 * 0.72 + (hL + hR) / 2 * 0.28; cpos.z = min(kL.z, kR.z) - 0.035
    cup = paper_cup("SpillCup", cC, tuple(cpos)); cup.rotation_mode = 'XYZ'
    lidO = lid("SpillLid", cC, (cpos.x, cpos.y, cpos.z + CUP_H))
    st = steam("SpillSteam", cC, (cpos.x, cpos.y, cpos.z + CUP_H), h=0.32, r=0.05, dens=0.55); st.parent = cup
    st.matrix_parent_inverse = cup.matrix_world.inverted()
    key_steam(st, 1, 420)
    for f, ang in ((1, 0), (205, 0), (222, -24), (240, -30), (420, -30)):
        cup.rotation_euler.x = R_(ang); cup.keyframe_insert("rotation_euler", frame=f)
    # hands: left resting on the left thigh; right on the right thigh, then pinches the lid and peels it up and away
    def thigh_pt(s, u=0.55):
        h = hL if s == "L" else hR; k = kL if s == "L" else kR; p = h.lerp(k, u); return p + Vector((0.03 if s == "L" else -0.03, 0, 0.075))
    for s in "LR":
        place_hand(rig, s, 1, thigh_pt(s), Vector((0, 0, -1)), Vector((0.15 if s == "L" else -0.15, -1, -0.2)))
        apply_pose(rig, s, "relaxed", 1)
    place_hand(rig, "L", 250, thigh_pt("L"), Vector((0, 0, -1)), Vector((0.15, -1, -0.2))); apply_pose(rig, "L", "relaxed", 250)
    place_hand(rig, "R", 120, thigh_pt("R", 0.5), Vector((0, 0, -1)), Vector((-0.15, -1, -0.2))); apply_pose(rig, "R", "relaxed", 120)
    edge = Vector((cpos.x - 0.012, cpos.y + CUP_R1 + 0.002, cpos.z + CUP_H + 0.003))
    rep = grip_object(rig, "R", 150, lidO, edge, Vector((0.1, -1.0, -0.35)), grip="pinch")
    for it in range(6):     # land the thumb-index midpoint on the lid edge (grip_object's pinch moved only twice)
        sc.frame_set(150); bpy.context.view_layer.update(); M = rig.matrix_world
        mid = M @ ((rig.pose.bones["finger2-3.R"].tail + rig.pose.bones["finger1-3.R"].tail) / 2)
        err = edge - mid
        if err.length < 0.004: break
        hand_delta(R, "R", 150, 150, err)
    print("B1 lid grip", rep, "pinch err", round(err.length, 4))
    hold_fingers(rig, "R", 150, 165)
    hand_delta(R, "R", 150, 165, (0, 0, 0))
    hand_delta(R, "R", 150, 190, (-0.01, 0.02, 0.05), Matrix.Rotation(R_(-15), 3, 'Y'))
    hand_delta(R, "R", 150, 215, (-0.08, 0.06, 0.15), Matrix.Rotation(R_(-35), 3, 'Y'))
    child_of_hand(lidO, rig, "R", 165)
    # spill: lid off at ~205, cup tips toward her lap 205..240; coffee pours onto the skirt and spreads
    skirt = next(o for o in rig.children if "elegantsuit" in o.name)
    pool_c = (cpos + (hL + hR) / 2) / 2; pool_c.z = max(hL.z, kL.z) + 0.09
    bm = bmesh.new(); bmesh.ops.create_circle(bm, cap_ends=True, segments=40, radius=0.09)
    for v in bm.verts:
        ang = math.atan2(v.co.y, v.co.x); v.co *= 1.0 + 0.22 * math.sin(3 * ang) + 0.12 * math.sin(7 * ang + 1)
    bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=3, use_grid_fill=True)
    me = bpy.data.meshes.new("SpillPool"); bm.to_mesh(me); bm.free()
    pool = bpy.data.objects.new("SpillPool", me); cC.objects.link(pool); pool.location = pool_c; pool.scale = (0.9, 1.4, 1)
    me.materials.append(mat("CoffeeWet", (0.13, 0.06, 0.025), 0.12))
    sw = pool.modifiers.new("Wrap", 'SHRINKWRAP'); sw.target = skirt; sw.wrap_method = 'PROJECT'; sw.use_project_z = True
    sw.use_negative_direction = True; sw.use_positive_direction = True; sw.offset = 0.004
    for f, sc_ in ((1, 0.02), (214, 0.02), (232, 0.55), (270, 1.0), (420, 1.12)):
        pool.scale = (0.9 * sc_, 1.4 * sc_, 1); pool.keyframe_insert("scale", frame=f)
    vis(pool, 1, False); vis(pool, 214, True)
    st2 = steam("SpillSteam2", cC, tuple(pool_c), h=0.30, r=0.08, dens=0.0)
    am = st2.active_material.node_tree.nodes["SteamAmount"].outputs[0]
    for f, v in ((1, 0.0), (220, 0.0), (250, 0.7), (420, 0.45)):
        am.default_value = v; am.keyframe_insert("default_value", frame=f)
    key_steam(st2, 1, 420, rate=1.1)
    # flinch: both hands lift up and out (open_alarm), right hand still holding the lid
    place_hand(rig, "L", 266, thigh_pt("L", 0.35) + Vector((0.12, 0.05, 0.28)), Vector((0.3, -1, 0.2)), Vector((0.2, -0.3, 1)))
    apply_pose(rig, "L", "open_alarm", 266)
    place_hand(rig, "L", 330, thigh_pt("L", 0.35) + Vector((0.10, 0.04, 0.22)), Vector((0.3, -1, 0.2)), Vector((0.2, -0.3, 1)))
    apply_pose(rig, "L", "open_alarm", 330, amount=0.7)
    place_hand(rig, "L", 400, thigh_pt("L", 0.3) + Vector((0.10, 0.03, 0.18)), Vector((0.3, -1, 0.0)), Vector((0.2, -0.5, 1)))
    hand_delta(R, "R", 215, 250, (0, 0, 0)); hand_delta(R, "R", 215, 268, (-0.06, 0.02, 0.06)); hand_delta(R, "R", 215, 400, (-0.05, 0.03, 0.03))
    for f in (250, 268, 400): hold_fingers(rig, "R", 150, f)
    # cameras: 1a outside through the open door, 1b lap from the driver side, 1c her face from the door opening
    face = Vector((sx, -0.02, 1.16))
    c1 = cam_shot("Cam1a", 1, 110, [(1, (-2.35, 0.15, 1.22), (-0.42, -0.28, 0.88)), (110, (-2.05, 0.02, 1.16), (-0.42, -0.28, 0.86))], lens=32)
    c2 = cam_shot("Cam1b", 111, 300, [(111, (-1.30, -0.74, 1.24), (-0.42, -0.24, 0.94)), (300, (-1.18, -0.68, 1.22), (-0.42, -0.22, 0.95))], lens=24)
    c3 = cam_shot("Cam1c", 301, 420, [(301, (-1.20, -0.80, 1.18), face), (420, (-1.10, -0.74, 1.17), face)], lens=40)
    for c, f0, f1 in ((c2, 111, 300), (c3, 301, 420)): catchlight(rig, c, f0, f1)
    return rig

if want("B1"):
    CUR_WIN = (1, 420); beat_B1()

exec(open(W + "scripts/b2_b6.py").read())

eye_fix_all()
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print("ANIM_OK", OUT)
