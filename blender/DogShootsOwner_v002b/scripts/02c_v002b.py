# DogShootsOwner v002b shot changes (director's v002 review), exec'd by 02_build.py just before the FUN table.
#  2. shot 04: after the flash a second angle (marker 04b) frames the paw on the trigger and the gun; the dog startles
#  3. 14a/14b and 15a-15d: the clean rigged dog lying on its side (no scan); hand on its back by ray cast on the
#     evaluated dog mesh
#  4. 15a/15d: the man kneels by the dog, left hand on its back, right forearm resting on his thigh, looks down; cameras push in
#  5. 15c: small head turn and breath in the close-up
from mathutils.bvhtree import BVHTree
EXTRA_MARKERS = []          # (sid, frame) extra camera cuts inside a shot
DOGBODY = next(c for c in DOG.children if c.type == 'MESH')
for _o in (SDH, SDF):
    _o.hide_render = _o.hide_viewport = True


def _dog_points(f):
    sc.frame_set(f); bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    e = DOGBODY.evaluated_get(dg); me = e.to_mesh(); mw = e.matrix_world
    pts = [mw @ v.co for v in me.vertices]; me.calc_loop_triangles()
    tris = [tuple(t.vertices) for t in me.loop_triangles]; e.to_mesh_clear()
    return pts, tris


def dog_lie(f, xy, surf_z, yaw, roll=-1, toward=None, reach=None, breath=0.0, head=(0, 0, 0)):
    """the rigged dog asleep on its side. roll=-1: its back faces local -X (before yaw). The legs settle toward the
    ground (the upper legs rest on the lower ones). Placed so its lowest point is on surf_z and, if given, its
    outermost point along `toward` (unit, world) is at the scalar `reach` (= that point . toward)."""
    DOG.rotation_mode = 'XYZ'
    DOG.rotation_euler = (Matrix.Rotation(R_(yaw), 3, 'Z') @ Matrix.Rotation(R_(90 * roll), 3, 'Y')).to_euler()
    down = -1.0 if roll < 0 else 1.0                      # armature-space x toward the ground
    top = "L" if roll < 0 else "R"
    pose = {"spine1": (None, (breath, 0, 5)), "spine2": (None, (0, 0, 4)), "neck1": (None, (8 + head[0], head[1], 10 + head[2])),
            "head": (None, (-2, 0, 5)), "tail1": (None, (-30, 0, -20)), "tail2": (None, (0, 0, -25))}
    # relaxed legs: a little bent, front paws a little forward, hind paws a little back (armature space)
    CURL = {"FL": (0.0, -0.05, 0.06), "FR": (0.0, -0.03, 0.05), "HL": (0.0, 0.07, 0.03), "HR": (0.0, 0.04, 0.05)}
    for pb in DOG.pose.bones:
        l_, r_ = pose.get(pb.name, (None, None))
        k = pb.name.split(".")[-1] if pb.name.startswith("IK_hoof.") else None
        if k:
            v = Vector(CURL[k]); v.x += down * (float(os.environ.get('DSO_LTOP', '0.06')) if k[1] == top else float(os.environ.get('DSO_LBOT', '0.03')))
            pb.location = DOG.data.bones[pb.name].matrix_local.to_3x3().inverted() @ v
        else:
            pb.location = Vector(l_) if l_ else Vector()
        pb.rotation_mode = 'QUATERNION'
        pb.rotation_quaternion = Euler(tuple(R_(v) for v in r_)).to_quaternion() if r_ else Quaternion()
        pb.keyframe_insert("location", frame=f); pb.keyframe_insert("rotation_quaternion", frame=f)
    DOG.location = Vector((xy.x, xy.y, surf_z + 0.155))
    DOG.keyframe_insert("location", frame=f); DOG.keyframe_insert("rotation_euler", frame=f)
    pts, _ = _dog_points(f)
    dz = surf_z + 0.004 - min(p.z for p in pts)
    sh = Vector((0, 0, dz))
    if toward is not None:
        t = Vector(toward).normalized(); sup = max(p.dot(t) for p in pts)
        sh += t * (reach - sup); sh.z = dz
    DOG.location = DOG.location + sh; DOG.keyframe_insert("location", frame=f)
    return f


def dog_hit(f, x, y):
    """top surface of the dog under (x, y) at frame f: (point, normal) or (None, None)"""
    pts, tris = _dog_points(f)
    bvh = BVHTree.FromPolygons(pts, tris)
    loc, n, i, d = bvh.ray_cast(Vector((x, y, 5.0)), Vector((0, 0, -1)))
    if loc is None: return None, None
    if n.z < 0: n = -n
    return loc, n


def hand_on_dog(f, x, y, fdir=(0.35, -1.0, 0), skin=0.016, side="L", pose_="flat_palm", step=(0.02, 0.0), ex=None):
    """palm on the dog's surface: starts at (x, y) and steps by `step` (toward the dog) until the ray hits it,
    then a further 3 cm onto the flank so the palm is not on the curved edge"""
    h = None
    for k in range(20):
        h, n = dog_hit(f, x + step[0] * k, y + step[1] * k)
        if h is not None:
            ex = ex if ex is not None else float(os.environ.get("DSO_HEX", "0.5"))
            h2, n2_ = dog_hit(f, x + step[0] * (k + ex), y + step[1] * (k + ex))
            if h2 is not None: h, n = h2, n2_
            break
    if h is None:
        print("BUILD WARN no dog under hand", f, x, y); return None
    n2 = (n + Vector((0, 0, 1.5))).normalized()
    fd = Vector(fdir); fd = (fd - n2 * fd.dot(n2)).normalized()
    place_hand(OWNER, side, f, h, -n2, fd, skin=skin); apply_pose(OWNER, side, pose_, f)
    sc.frame_set(f); sh_ = OWNER.matrix_world @ OWNER.pose.bones["upperarm01." + side].head
    wr_ = OWNER.matrix_world @ OWNER.pose.bones["wrist." + side].head
    print("BUILD hand_on_dog", f, "target", tuple(round(v, 3) for v in h), "shoulder dist", round((h - sh_).length, 3), "wrist-target", round((wr_ - h).length, 3))
    return h


_HAND_VS = {}
def _hand_inside_dog(f, side, bvh):
    body = bpy.data.objects["Owner.body"]
    if side not in _HAND_VS:
        gi = {g.index: g.name for g in body.vertex_groups}; ids = []; bones = {b.name for b in OWNER.data.bones}
        for v in body.data.vertices:
            gs = [g for g in v.groups if gi.get(g.group) in bones]
            if not gs: continue
            g = max(gs, key=lambda x: x.weight); nm = gi.get(g.group, "")
            if nm.endswith("." + side) and nm.startswith(("finger", "metacarpal", "wrist", "lowerarm")): ids.append(v.index)
        _HAND_VS[side] = ids
    mods = [m for m in body.modifiers if m.type in ('MASK', 'SUBSURF') and m.show_viewport]
    for m in mods: m.show_viewport = False
    sc.frame_set(f); dg = bpy.context.evaluated_depsgraph_get()
    e = body.evaluated_get(dg); me = e.to_mesh(); mw = body.matrix_world; bad = 0
    for i in _HAND_VS[side]:
        p = mw @ me.vertices[i].co; loc, nn, _, d = bvh.find_nearest(p, 0.08)
        if loc is not None and (p - loc).dot(nn) < 0.003: bad += 1
    e.to_mesh_clear()
    for m in mods: m.show_viewport = True
    return bad


def hand_on_dog_side(f, origin, direction, fdir=(0, -0.3, -1), skin=None, side="L", pose_="relaxed", angles=(0, -30, 30, -60, 60)):
    skin = skin if skin is not None else float(os.environ.get("DSO_SKN", "0.016"))
    """palm on the side of the dog that faces him (its back): a horizontal ray from `origin` along `direction`
    finds the surface; the palm faces into it and the fingers point down along the fur (wrist stays neutral)"""
    pts, tris = _dog_points(f)
    bvh = BVHTree.FromPolygons(pts, tris)
    loc, n, i, d = bvh.ray_cast(Vector(origin), Vector(direction).normalized())
    if loc is None:
        print("BUILD WARN no dog side hit", f, origin); return None
    if n.dot(Vector(direction)) > 0: n = -n
    fd = Vector(fdir); fd = (fd - n * fd.dot(n)).normalized()
    # finger direction turned about the palm normal (thumb away from the fur) and the palm lifted in 5 mm steps,
    # until every hand vertex is at least 3 mm outside the dog; the smallest lift wins
    best = None
    for ang in angles:
        fa = Matrix.Rotation(R_(ang), 3, n) @ fd
        for k in range(16):
            sk = skin + 0.005 * k
            if best and sk >= best[0]: break
            place_hand(OWNER, side, f, loc, -n, fa, skin=sk); apply_pose(OWNER, side, pose_, f)
            if _hand_inside_dog(f, side, bvh) == 0:
                best = (sk, ang, fa.copy()); break
    if best is None: best = (skin + 0.075, 0, fd)
    sk, ang, fa = best
    place_hand(OWNER, side, f, loc, -n, fa, skin=sk); apply_pose(OWNER, side, pose_, f)
    bad = _hand_inside_dog(f, side, bvh)
    print("BUILD hand lift", side, f, "skin", round(sk, 3), "angle", ang, "inside", bad)
    sc.frame_set(f); sh_ = OWNER.matrix_world @ OWNER.pose.bones["upperarm01." + side].head
    wr_ = OWNER.matrix_world @ OWNER.pose.bones["wrist." + side].head
    print("BUILD hand_side", side, f, "target", tuple(round(v, 3) for v in loc), "n", tuple(round(v, 2) for v in n),
          "shoulder dist", round((loc - sh_).length, 3), "wrist-target", round((wr_ - loc).length, 3))
    return loc


# ------------------------------------------------------------------ 2. shot 04: second angle after the flash
_S04_orig = S04
def S04(f0, f1):
    _S04_orig(f0, f1)
    fb = f0 + 5
    D0 = Vector((0.13 - 0.17 - 0.03, 0.70, BZ + 0.008))
    # the dog startles at the bang: head jerks up and back, then stays alert (the paw stays on the trigger area)
    for fr, hd, tl in ((fb, (-14, 0, -10), 10), (fb + 3, (14, 0, -28), -20), (fb + 10, (10, 0, -22), -25), (f1, (6, 0, -18), -20)):
        dog_key(fr, D0, 90, dog_pose_stand(head=hd, tail=tl, ext={"__FR": "trig"}))
    c = camera("04b", 30)
    tgt = Vector((TRIG.x - 0.06, TRIG.y + 0.02, TRIG.z + 0.12))
    fb2 = fb + 14
    cam_key(c, fb2, Vector((TRIG.x + 0.28, TRIG.y - 0.42, TRIG.z + 0.46)), tgt, lens=26)
    cam_key(c, f1, Vector((TRIG.x + 0.24, TRIG.y - 0.36, TRIG.z + 0.42)), tgt, lens=26)
    EXTRA_MARKERS.append(("04b", fb2))


# ------------------------------------------------------------------ 3. hospital: rigged dog on its side beside his legs
def hosp_dog(f, breath=0.0):
    # back toward the man (-X), legs away from him, head toward the foot of the bed (-Y), back 7 cm from his hip
    dog_lie(f, Vector((HX.x + 0.45, 0.66)), BED_TOP, 0, roll=-1, toward=(-1, 0, 0), reach=-(HX.x + float(os.environ.get('DSO_HDX', '-0.02'))), breath=breath)


def hosp_man(f, smile_head=(18, -20), stroke=0.0):
    st = HX + Vector((-0.235, 0.78, BED_TOP + 0.02))
    seated(HOWN, OWNER, f, st, yaw=0, lean=-26, flex=14, head=smile_head, legs_out=True)
    hand_on_dog_side(f, (HX.x - 0.20, float(os.environ.get("DSO_HY", "0.80")) - 0.05 * stroke, BED_TOP + float(os.environ.get("DSO_HZ", "0.32"))),
                     (1, 0, 0), fdir=(0.0, -0.35, -1))
    place_hand(OWNER, "R", f, st + Vector((-0.18, -0.25, 0.10)), (-0.3, 0, -1), (0, -1, 0)); apply_pose(OWNER, "R", "relaxed", f)


def S14a(f0, f1):
    PRESENT["14a"] = {"own", "dog"}
    for fr, t in ((f0, 0.0), ((f0 + f1) // 2, 0.5), (f1, 1.0)):
        hosp_dog(fr, breath=2.0 * t); hosp_man(fr, smile_head=(26 + 4 * t, 10 + 4 * t), stroke=0.3 * t)
    c = camera("14a", 30)
    tgt = HX + Vector((0.05, 0.50, BED_TOP + 0.40))
    cam_key(c, f0, tgt + Vector((1.55, -0.75, 0.55)), tgt); cam_key(c, f1, tgt + Vector((1.35, -0.62, 0.50)), tgt)


def S14b(f0, f1):
    PRESENT["14b"] = {"own", "dog"}
    for fr, t in ((f0, 0.0), ((f0 + f1) // 2, 1.0), (f1, 0.0)):
        hosp_dog(fr, breath=2.0 * t); hosp_man(fr, smile_head=(28, 12), stroke=t)
    c = camera("14b", 40)
    # higher and centred on his face, hand and the dog's shoulders (not the hind quarter)
    tgt = HX + Vector((-0.02, 0.62, BED_TOP + 0.50))
    cam_key(c, f0, tgt + Vector((0.95, -0.80, 0.75)), tgt, lens=32); cam_key(c, f1, tgt + Vector((0.82, -0.70, 0.66)), tgt, lens=32)


# ------------------------------------------------------------------ 4/5. field: dog asleep on its side, the man kneels by it
FDOG_XY = DOGSPOT.to_2d()
KNEEL = DOGSPOT + Vector((0.10, 0.62, 0))       # where he kneels (behind the dog's back, facing -Y toward the camera)


def field_dog(f, breath=0.0):
    # yaw -90 with roll -1: back toward +Y (the man), head toward -X, legs toward the camera (-Y)
    dog_lie(f, FDOG_XY, 0.0, -90, roll=-1, toward=(0, 1, 0), reach=KNEEL.y - float(os.environ.get('DSO_FRCH', '0.28')), breath=breath)


def kneel(f, pos, yaw=0.0, flex=float(os.environ.get('DSO_KFL', '46')), head=(30, 0), twist=0.0, hip_z=0.50, hip_back=-0.10, breath=0.0):
    """both knees on the ground, toes tucked, hips between knees and heels; torso leans forward over the dog"""
    c = Matrix.Rotation(R_(yaw), 3, 'Z')
    HOWN.key_root(f, pos + c @ Vector((0, hip_back, hip_z - breath * 0.003)), yaw=yaw, flex=flex * 0.35)
    for s, sx in (("L", 1), ("R", -1)):
        fp = pos + c @ Vector((0.12 * sx, 0.14, 0))
        a = HOWN.ankle[s]
        M = Matrix.Translation(Vector((fp.x, fp.y, pos.z + 0.13))) @ Matrix.Rotation(R_(yaw), 4, 'Z') @ Matrix.Rotation(R_(80), 4, 'X') @ \
            Matrix.Translation(-a) @ HOWN.r.rest("IK_foot." + s)
        HOWN.r.key_world("IK_foot." + s, f, M)
        pole = pos + c @ Vector((0.14 * sx, -0.9, 0.05)); pb = HOWN.r.PB["Pole_knee." + s]; n = "Pole_knee." + s
        pb.location = HOWN.r.rest(n).to_3x3().inverted() @ (pole - HOWN.r.BN[n].head_local); pb.keyframe_insert("location", frame=f, group=n)
    HOWN.key_spine(f, flex=flex + breath, twist=twist, head=head)


def field_man(f, head=(32, 0), on_dog=True, dx=0.0, breath=0.0, twist=0.0):
    kneel(f, KNEEL, yaw=0, head=head, breath=breath, twist=twist, hip_back=float(os.environ.get("DSO_HB", "0.0")))
    hz = float(os.environ.get("DSO_FHZ", "0.24"))
    if on_dog:
        hand_on_dog_side(f, (KNEEL.x + 0.14 + dx, KNEEL.y, hz), (0, -1, 0), fdir=(0.25, 0.0, -1), side="L", angles=(60,))
        hand_on_dog_side(f, (KNEEL.x - 0.22, KNEEL.y, hz + 0.02), (0, -1, 0), fdir=(-0.25, 0.0, -1), side="R", angles=(0,))
    else:
        for s_, sx in (("L", 1), ("R", -1)):     # arms hang relaxed beside his thighs, elbows a little bent
            place_hand(OWNER, s_, f, KNEEL + Vector((0.27 * sx, -0.16, 0.46)), (-sx, 0, 0), (0, -0.35, -1)); apply_pose(OWNER, s_, "relaxed", f)


def S15a(f0, f1):
    PRESENT["15a"] = {"own", "dog"}
    # the ambulance parked on the road set is in view of the clearing: hidden for the field shots
    for fr, hid in ((f0 - 1, False), (f0, True)):
        AM.hide_render = AM.hide_viewport = hid; AM.keyframe_insert("hide_render", frame=fr); AM.keyframe_insert("hide_viewport", frame=fr)
        for ch in AM.children_recursive:
            ch.hide_render = ch.hide_viewport = hid; ch.keyframe_insert("hide_render", frame=fr); ch.keyframe_insert("hide_viewport", frame=fr)
    # the kennel and hospital sets lie along +X behind the clearing (seen in 15b): hidden too
    for cn in ("SET_kennel", "SET_hosp"):
        cc = bpy.data.collections.get(cn)
        if not cc: continue
        for ob in list(cc.all_objects):
            if ob.type not in ('MESH', 'CURVE', 'EMPTY'): continue
            if ob in (DOG, DOGBODY, OWNER) or ob.parent in (OWNER, DOG): continue
            for fr, hid in ((f0 - 1, False), (f0, True)):
                ob.hide_render = hid; ob.keyframe_insert("hide_render", frame=fr)
    n = f1 - f0
    for k, t in ((0, 0.0), (int(n * 0.30), 0.0), (int(n * 0.62), 1.0), (n, 1.0)):
        fr = f0 + k
        field_dog(fr, breath=0.0)
        field_man(fr, head=(30 + 6 * t, 4 - 4 * t), on_dog=t > 0.5)
    c = camera("15a", 30)
    tgt = KNEEL.lerp(DOGSPOT, 0.55) + Vector((0, 0, 0.45))
    cam_key(c, f0, tgt + Vector((0.55, -3.1, 0.55)), tgt, lens=30); cam_key(c, f1, tgt + Vector((0.42, -2.4, 0.45)), tgt, lens=30)


def S15b(f0, f1):
    PRESENT["15b"] = {"own", "dog"}          # the man is just out of frame; his hand rests on the dog's back
    for fr in (f0, f1):
        field_dog(fr); field_man(fr, head=(36, 0))
    sc.frame_set(f0)
    hp_ = DOG.matrix_world @ DOG.pose.bones["head"].head
    body = DOG.matrix_world @ DOG.pose.bones["spine2"].head
    tgt = hp_.lerp(body, 0.35)
    c = camera("15b", 40)
    # from the head end, a little to the man's side: face in front, body behind it; he stays out of frame
    cam_key(c, f0, tgt + Vector((-0.98, 0.12, 0.16)), tgt, lens=40); cam_key(c, f1, tgt + Vector((-0.84, 0.10, 0.14)), tgt, lens=40)


def S15c(f0, f1):
    PRESENT["15c"] = {"own", "dog"}
    n = f1 - f0
    # close-up: a slow breath and a small head turn toward the dog
    for k, hd, br, tw in ((0, (8, 0), 0, 0), (int(n * 0.45), (12, -8), 3, -3), (n, (14, -12), 1, -4)):
        fr = f0 + k
        field_dog(fr); field_man(fr, head=hd, breath=br, twist=tw)
    sc.frame_set(f0)
    hd_ = OWNER.matrix_world @ OWNER.pose.bones["head"].head
    tgt = hd_ + Vector((0, -0.04, 0.02))
    c = camera("15c", 45)
    # low, looking up into his bowed face
    cam_key(c, f0, tgt + Vector((0.28, -0.95, -0.62)), tgt); cam_key(c, f1, tgt + Vector((0.24, -0.82, -0.55)), tgt)


def S15d(f0, f1):
    PRESENT["15d"] = {"own", "dog"}
    n = f1 - f0
    # final shot: slow push-in on him kneeling, hand on the dog's back moving a little, breath, head low
    ks = sorted(set(list(range(0, n, 12)) + [n]))
    for k in ks:
        u = k / n; t = math.sin(math.pi * min(1.0, u / 0.7) * 0.5) if u <= 0.7 else 1.0 - 0.3 * (u - 0.7) / 0.3
        fr = f0 + k
        field_dog(fr); field_man(fr, head=(38 + 4 * t, -6 + 4 * t), dx=0.0, breath=2.0 * t)
    c = camera("15d", 32)
    tgt = KNEEL.lerp(DOGSPOT, 0.45) + Vector((0, 0, 0.42))
    cam_key(c, f0, tgt + Vector((0.95, -2.5, 0.70)), tgt, lens=32); cam_key(c, f1, tgt + Vector((0.62, -1.65, 0.45)), tgt, lens=32)
