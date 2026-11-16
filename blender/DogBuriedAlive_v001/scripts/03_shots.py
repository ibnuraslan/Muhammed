# DogBuriedAlive: per-shot animation at 1x (each from its own start frame), one camera per shot. exec'd by 02_build.py.
DS = DOG.scale.x                                   # dog object scale (1.25)
RD = Rig(DOG)
RDAD, RMOM, RSON = Rig(DAD), Rig(MOM), Rig(SON)
HDAD, HMOM, HSON = Human(RDAD), Human(RMOM), Human(RSON)
for rg in (DAD, MOM, SON): add_hand_limits(rg)
CHARS = {"dad": (DAD, HDAD), "mom": (MOM, HMOM), "son": (SON, HSON)}
PARK = {"dad": Vector((-50, -40, 0)), "mom": Vector((-52, -40, 0)), "son": Vector((-54, -40, 0)), "dog": Vector((-56, -40, 0))}
PRESENT = {}
def kr(n, step):
    r = list(range(0, n + 1, step))
    if r[-1] != n: r.append(n)
    return r
def ground_z(x, y): return 0.0                   # every walk in this film is on flat ground (lawn, road, deck via offsets)

def walk_arms(rig, H, path, yaw_fn, f0, f1, stride=0.75, swing=0.16, step=2):
    """arms swing opposite to the legs (no mannequin walk): relaxed hands at the hips, forward/back"""
    frames = list(range(f0, f1 + 1)); dist = [0.0]
    for a_, b_ in zip(frames, frames[1:]): dist.append(dist[-1] + (path(b_) - path(a_)).to_2d().length)
    for i, f in enumerate(frames):
        if i % step and i != len(frames) - 1: continue
        ph = 2 * math.pi * (dist[i] / stride)
        c = Matrix.Rotation(R_(yaw_fn(f)), 3, 'Z'); p = path(f)
        for s, sx, sg in (("L", 1, 1), ("R", -1, -1)):
            fw = swing * math.sin(ph) * sg       # left arm forward when the right foot is forward
            pt = p + c @ Vector((0.215 * sx, -fw, 0.0)); pt.z = p.z + 0.86 + 0.03 * abs(math.sin(ph))
            place_hand(rig, s, f, pt, c @ Vector((-sx, 0, 0)), c @ Vector((0, -0.25 * math.copysign(1, fw) * min(1, abs(fw) * 6), -1)).normalized())
            if i == 0: apply_pose(rig, s, "relaxed", f)

def stand(H, rig, f, pos, yaw=0.0, head=(0, 0), flex=0.0, twist=0.0, hands=True, breath=0.0, hand_fwd=0.0):
    c = Matrix.Rotation(R_(yaw), 3, 'Z')
    H.key_root(f, Vector((pos.x, pos.y, pos.z + 0.95 - breath * 0.004)), yaw=yaw, flex=flex * 0.3)
    for s, sx in (("L", 1), ("R", -1)):
        H.key_foot(s, f, (pos + c @ Vector((0.1 * sx, 0, 0))).to_2d(), yaw)
        if hands:
            place_hand(rig, s, f, pos + c @ Vector((0.205 * sx, -hand_fwd, 0.86 + flex * 0.002)), c @ Vector((-sx, 0, 0)), (0, 0, -1))
            apply_pose(rig, s, "relaxed", f)
    H.key_spine(f, flex=flex + breath, twist=twist, head=head)

def kneel(H, rig, f, pos, yaw=0.0, head=(0, 0), flex=10.0):
    """one-knee kneel: left foot planted forward, right knee down; hands rest on the left knee and the right thigh"""
    c = Matrix.Rotation(R_(yaw), 3, 'Z')
    H.key_root(f, Vector((pos.x, pos.y, 0.60)) + c @ Vector((0, 0.05, 0)), yaw=yaw, flex=flex * 0.4)
    H.key_foot("L", f, (pos + c @ Vector((0.13, -0.38, 0))).to_2d(), yaw)
    a = H.ankle["R"]
    fp = pos + c @ Vector((-0.12, 0.42, 0))
    M = Matrix.Translation(Vector((fp.x, fp.y, 0.13))) @ Matrix.Rotation(R_(yaw), 4, 'Z') @ Matrix.Rotation(R_(-55), 4, 'X') @ \
        Matrix.Translation(-a) @ H.r.rest("IK_foot.R")
    H.r.key_world("IK_foot.R", f, M)
    pb = H.r.PB["Pole_knee.R"]; n = "Pole_knee.R"; pole = fp + c @ Vector((0, -0.9, 0.3))
    pb.location = H.r.rest(n).to_3x3().inverted() @ (pole - H.r.BN[n].head_local); pb.keyframe_insert("location", frame=f, group=n)
    H.key_spine(f, flex=flex, head=head)
    sc.frame_set(f)
    kL = rig.matrix_world @ rig.pose.bones["lowerleg01.L"].head
    kR = rig.matrix_world @ rig.pose.bones["lowerleg01.R"].head
    hR = rig.matrix_world @ rig.pose.bones["upperleg01.R"].head
    place_hand(rig, "L", f, kL + Vector((0, 0, 0.065)), (0, 0, -1), c @ Vector((0.15, -1, -0.2)))
    place_hand(rig, "R", f, hR.lerp(kR, 0.6) + Vector((0, 0, 0.075)), (0, 0, -1), c @ Vector((0.0, -1, -0.3)))
    apply_pose(rig, "L", "relaxed", f); apply_pose(rig, "R", "relaxed", f)

def horrified(H, rig, f, pos, yaw, amt, head=(0, 0), back=0.0):
    """step back, both hands come up in front of the chest (palms out, 20+ cm off the body), head pulls back"""
    c = Matrix.Rotation(R_(yaw), 3, 'Z')
    p = pos + c @ Vector((0, back * amt, 0))
    H.key_root(f, Vector((p.x, p.y, 0.95 - 0.02 * amt)), yaw=yaw, flex=-4 * amt)
    for s, sx in (("L", 1), ("R", -1)):
        H.key_foot(s, f, (p + c @ Vector((0.11 * sx, 0.06 * amt * (1 if s == "R" else 0), 0))).to_2d(), yaw)
        hz = rig.data.bones["neck01"].head_local.z          # chest height of this character
        rel = Vector((0.205 * sx, 0, 0.86 * hz / 1.50)).lerp(Vector((0.11 * sx, -0.24, hz - 0.12)), amt)
        nrm = (c @ Vector((-sx, 0, 0))).lerp(c @ Vector((0, -1, 0)), amt).normalized()
        fd = Vector((0, 0, -1)).lerp(c @ Vector((0.25 * sx, -0.05, 1)), amt).normalized()
        place_hand(rig, s, f, p + c @ rel, nrm, fd)
        apply_pose(rig, s, "open_alarm" if amt > 0.5 else "relaxed", f, amount=1.0)
        # elbows stay down and in front of the ribs (no wing pose)
        pn = "Pole_elbow." + s; pb = rig.pose.bones[pn]
        el = Vector((0.20 * sx, 0.30, hz - 0.55)).lerp(Vector((0.30 * sx, 0.25, hz - 0.75)), 0.0)
        pole = p + c @ el
        pb.location = rig.data.bones[pn].matrix_local.to_3x3().inverted() @ (pole - rig.data.bones[pn].head_local)
        pb.keyframe_insert("location", frame=f, group=pn)
    H.key_spine(f, flex=-5 * amt, head=(head[0] - 8 * amt, head[1]))
    jaw = rig.pose.bones.get("jaw")
    if jaw:
        jaw.rotation_mode = 'XYZ'; jaw.rotation_euler = (R_(9 * amt), 0, 0); jaw.keyframe_insert("rotation_euler", frame=f)

def park(key, f):
    if key == "dog":
        DOG.location = PARK["dog"]; DOG.keyframe_insert("location", frame=f); return
    rig, H = CHARS[key]; stand(H, rig, f, PARK[key])

# ------------------------------------------------------------------ dog
def dog_key(f, loc, rot, pose):
    """rot: (rx, ry, rz) degrees, applied as Rz @ Ry @ Rx (yaw last)"""
    DOG.location = loc; DOG.rotation_mode = 'XYZ'
    DOG.rotation_euler = (Matrix.Rotation(R_(rot[2]), 3, 'Z') @ Matrix.Rotation(R_(rot[1]), 3, 'Y') @ Matrix.Rotation(R_(rot[0]), 3, 'X')).to_euler()
    DOG.keyframe_insert("location", frame=f); DOG.keyframe_insert("rotation_euler", frame=f)
    for pb in DOG.pose.bones:
        l_, r_ = pose.get(pb.name, (None, None))
        if pb.name.startswith("IK_hoof") and l_ is not None:
            pb.location = DOG.data.bones[pb.name].matrix_local.to_3x3().inverted() @ Vector(l_)
        else:
            pb.location = Vector(l_) if l_ else Vector()
        pb.rotation_mode = 'QUATERNION'
        pb.rotation_quaternion = Euler(tuple(R_(v) for v in r_)).to_quaternion() if r_ else Quaternion()
        pb.keyframe_insert("location", frame=f); pb.keyframe_insert("rotation_quaternion", frame=f)

CURL = {"IK_hoof.FL": (0.03, 0.13, 0.16), "IK_hoof.FR": (0.0, 0.10, 0.13), "IK_hoof.HL": (0.03, -0.16, 0.14), "IK_hoof.HR": (0.0, -0.13, 0.11)}
def side_pose(head=(0, 0, 0), breath=0.0, tail=0.0, curl=1.0):
    p = {"spine1": (None, (breath, 0, 5)), "spine2": (None, (0, 0, 4)), "neck1": (None, (8 + head[0], head[1], 10 + head[2])),
         "head": (None, (-2, 0, 5)), "tail1": (None, (-30, 0, -20 + tail)), "tail2": (None, (0, 0, -25))}
    for k, v in CURL.items(): p[k] = (tuple(x * curl for x in v), None)
    return p
TORSO0 = DOG.data.bones["torso"].head_local.copy()
def dog_side(f, loc, yaw, roll=-90, **kw):
    """lying on its side (asleep / unconscious), rolled about its long axis; `loc` = where the torso centre goes"""
    R = Matrix.Rotation(R_(yaw), 3, 'Z') @ Matrix.Rotation(R_(roll), 3, 'Y')
    org = loc - R @ (TORSO0 * DS)
    dog_key(f, org, (0, roll, yaw), side_pose(**kw))

def stand_pose(head=(0, 0, 0), tail=0.0, pant=0.0, ext=None):
    p = {"neck1": (None, (head[0], head[1], head[2] * 0.5)), "head": (None, (pant, 0, head[2] * 0.5)), "tail1": (None, (tail, 0, 0)),
         "tail2": (None, (tail * 0.5, 0, 0))}
    if ext: p.update(ext)
    return p

def dog_walk(path, f0, f1, stride, gait, origin, wag=25.0, head=(0, 0, 0)):
    """quadruped locomotion in armature space: the dog object sits at `origin` (no rotation, scale DS); path is world xy"""
    DOG.location = origin; DOG.rotation_euler = (0, 0, 0)
    DOG.keyframe_insert("location", frame=f0); DOG.keyframe_insert("rotation_euler", frame=f0)
    DOG.keyframe_insert("location", frame=f1); DOG.keyframe_insert("rotation_euler", frame=f1)
    for pb in DOG.pose.bones:
        pb.rotation_mode = 'QUATERNION'
        if not pb.name.startswith(("IK_hoof", "torso")):
            pb.location = Vector(); pb.rotation_quaternion = Quaternion()
            pb.keyframe_insert("location", frame=f0); pb.keyframe_insert("rotation_quaternion", frame=f0)
    lp = lambda f: (path(f) - origin) / DS
    quad_move(RD, lp, f0, f1, stride / DS, gait=gait, body_bob=0.012 if gait == "walk" else 0.025)
    for f in sorted(set(range(f0, f1 + 1, 4)) | {f1}):
        RD.key_rot("tail1", f, [("X", 10), ("Z", wag * math.sin((f - f0) * 0.55))])
        RD.key_rot("tail2", f, [("Z", wag * 0.6 * math.sin((f - f0) * 0.55 - 0.6))])
        RD.key_rot("neck1", f, [("X", head[0]), ("Z", head[2])])

# eyelids (fur-coloured caps over the eyes; scale 1 = closed, 0 = open), bone-parented to the head
LID_M = mat("DogLid", (0.80, 0.50, 0.24), 0.65)
LIDS = []
for sx in (1, -1):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=12, radius=1.0, location=(0.0495 * sx, -0.4265, 0.6155))
    l = bpy.context.active_object; l.name = "DogLid" + ("L" if sx > 0 else "R"); l.scale = (0.0105, 0.0175, 0.0145)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True); bpy.ops.object.shade_smooth()
    l.data.materials.append(LID_M); move_to(l, bpy.data.collections["CHAR_Dog"])
    DOG.location = (0, 0, 0); DOG.rotation_euler = (0, 0, 0)
    for pb in DOG.pose.bones: pb.location = Vector(); pb.rotation_quaternion = Quaternion()
    bpy.context.view_layer.update()
    mw = l.matrix_world.copy(); l.parent = DOG; l.parent_type = 'BONE'; l.parent_bone = "head"; bpy.context.view_layer.update()
    l.matrix_world = mw
    LIDS.append(l)
def lids(f, closed):
    for l in LIDS:
        s = 1.0 if closed else 0.001
        l.scale = (s, s, s); l.keyframe_insert("scale", frame=f)
        l.hide_render = not closed; l.keyframe_insert("hide_render", frame=f)

# ------------------------------------------------------------------ cars
def car_rig(src, name, c):
    o = dup(src, name, (0, 0, -80), c=c)
    ws = []
    for w_ in src.children:
        wo = dup(w_, name + "_" + w_.name.split("_")[-1], w_.location, c=c); wo.parent = o; wo.rotation_mode = 'XYZ'; ws.append(wo)
    return o, ws
def car_drive(o, ws, f0, f1, path, step=2, rev=False):
    """path(t in 0..1) -> world xy ; heading from the tangent (model front = -Y); wheels spin with distance"""
    frames = list(range(f0, f1 + 1)); dist = 0.0; prev = None
    for i, f in enumerate(frames):
        t = (f - f0) / max(1, f1 - f0)
        p = path(t); a = path(max(0, t - 0.01)); b = path(min(1, t + 0.01)); d = (b - a)
        if rev: d = -d
        h = math.atan2(d.x, -d.y) if d.length > 1e-6 else (o.rotation_euler.z)
        if prev is not None: dist += (p - prev).length * (-1 if rev else 1)
        prev = p
        if i % step and i != len(frames) - 1: continue
        o.location = Vector((p.x, p.y, 0)); o.rotation_euler = (0, 0, h)
        o.keyframe_insert("location", frame=f); o.keyframe_insert("rotation_euler", frame=f)
        for w_ in ws:
            w_.rotation_euler = (-dist / 0.38, 0, 0); w_.keyframe_insert("rotation_euler", frame=f)
def bez(p0, p1, p2, p3):
    return lambda t: (1 - t) ** 3 * p0 + 3 * (1 - t) ** 2 * t * p1 + 3 * (1 - t) * t ** 2 * p2 + t ** 3 * p3
def eased(fn, a=0.0, b=1.0, ein=True, eout=True):
    def g(t):
        u = t
        if ein and eout: u = ease(t)
        elif eout: u = math.sin(t * math.pi / 2)
        elif ein: u = 1 - math.cos(t * math.pi / 2)
        return fn(a + (b - a) * u)
    return g

# SUV: blue paint, plates blank, logo on both front doors
SUVB, SUVW = car_rig(SUV, "SUVcar", CY)
for i, m in enumerate(SUVB.data.materials):
    if m and m.name.startswith("Body"):
        nm = m.copy(); SUVB.data.materials[i] = nm
        Pn = next(n for n in nm.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
        for l in list(Pn.inputs["Base Color"].links): nm.node_tree.links.remove(l)
        Pn.inputs["Base Color"].default_value = (0.05, 0.42, 0.85, 1); Pn.inputs["Roughness"].default_value = 0.3
        if "Coat Weight" in Pn.inputs: Pn.inputs["Coat Weight"].default_value = 0.5
    if m and m.name.startswith("Shadow"):
        nm = mat("NoShadow", (0, 0, 0)); nm.blend_method = 'CLIP' if hasattr(nm, "blend_method") else None
        nm.node_tree.nodes["Principled BSDF"].inputs["Alpha"].default_value = 0.0; SUVB.data.materials[i] = nm
    if m and m.name.startswith("Glass"):
        nm = m.copy(); SUVB.data.materials[i] = nm
        Pn = next((n for n in nm.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)
        if Pn:
            for l in list(Pn.inputs["Base Color"].links): nm.node_tree.links.remove(l)
            Pn.inputs["Base Color"].default_value = (0.03, 0.05, 0.07, 1); Pn.inputs["Roughness"].default_value = 0.05
            for k in ("Transmission Weight", "Alpha"):
                if k in Pn.inputs:
                    for l in list(Pn.inputs[k].links): nm.node_tree.links.remove(l)
            if "Transmission Weight" in Pn.inputs: Pn.inputs["Transmission Weight"].default_value = 0.0
            Pn.inputs["Alpha"].default_value = 1.0
M_PLATE = mat("BlankPlate", (0.93, 0.93, 0.90), 0.5)
def ray_local(obj, o, d):
    ok, loc, nrm, idx = obj.ray_cast(Vector(o), Vector(d).normalized())
    return loc if ok else None
for y0, dy, nm_, z_ in ((-4.0, 1, "Front", 0.48), (4.0, -1, "Rear", 0.62)):
    hit = ray_local(SUV, (0, y0, z_), (0, dy, 0))
    yy = (hit.y - dy * 0.012) if hit else y0 * 0.6
    pl = rbox("SUVPlate" + nm_, (0.54, 0.02, 0.13), (0, yy, z_), M_PLATE, CY, bevel=0.005); pl.parent = SUVB
    print("BUILD plate", nm_, round(yy, 3))
for sx in (1, -1):
    hit = ray_local(SUV, (2.5 * sx, -0.30, 0.80), (-sx, 0, 0))
    xx = (hit.x + 0.006 * sx) if hit else 1.0 * sx
    lg = logo_decal("SUVLogo" + ("L" if sx > 0 else "R"), (xx, -0.30, 0.80), (R_(90), 0, R_(90 * sx)), 0.80, False, CY)
    lg.parent = SUVB
    print("BUILD logo x", round(xx, 3))
PKB, PKW = car_rig(PICKUP, "PickupCar", CR)

# ------------------------------------------------------------------ dirt clumps
CLUMPS = [dup(ROCK, f"Clump{i}", (0, 0, -70), (0, 0, 0), 2.2, CG) for i in range(26)]
for cl in CLUMPS:
    cl.data = ROCK.data.copy(); cl.data.materials.clear(); cl.data.materials.append(CLUMP_M)
    for ms in cl.material_slots: ms.link = 'OBJECT'; ms.material = CLUMP_M
def clump_fall(cl, f0, f1, p0, p1, spin=3.0, arc=0.0):
    n = f1 - f0
    for k in kr(n, 3):
        t = k / n
        p = p0.lerp(p1, t); p.z = p0.z + (p1.z - p0.z) * t * t + arc * 4 * t * (1 - t)
        keyobj(cl, f0 + k, loc=p, rot=(spin * t, spin * 0.7 * t, 0))
def clump_park(cl, f): keyobj(cl, f, loc=Vector((0, 0, -70)))

# ================================================================== GRAVE shots
DOG_G = Vector((-0.12, 0.42, -0.86))
YAW_G = 50                                     # diagonal in the pocket: head toward the open face (camera), clear of every wall         # torso of the lying dog in the pocket (head to +x, back to camera)
def grave_people(f0, f1, heads=(28, 0), turn_at=None):
    pass
def fill_key(f, h):
    FILL.scale = (1, 1, h); FILL.keyframe_insert("scale", frame=f)
def g_dog(f0, f1, breath_amp=2.0, closed=True, head=(0, 0, 0)):
    for k in kr(f1 - f0, 6):
        dog_side(f0 + k, DOG_G, YAW_G, roll=90, breath=breath_amp * math.sin(k * 0.10), head=head)
    lids(f0, closed); lids(f1, closed)

def SG01(f0, f1):
    PRESENT["G01"] = {"dad", "mom", "son", "dog"}
    g_dog(f0, f1)
    fill_key(f0, 0.62); fill_key(f1, 0.96)
    keyobj(MOUND_G, f0, scale=(0.62, 0.62, 0.001)); keyobj(MOUND_G, f1, scale=(0.62, 0.62, 0.06))
    for (rig, H), x, y, yw in ((CHARS["dad"], -0.55, 1.55, 8), (CHARS["mom"], 0.15, 1.75, -4), (CHARS["son"], 0.75, 1.55, -15)):
        for k in (0, 40, 80, f1 - f0):
            stand(H, rig, f0 + k, Vector((x, y, 0)), yw, head=(30 + 3 * math.sin(k * 0.05), 0), flex=6, breath=math.sin(k * 0.08))
    random.seed(5)
    for i, cl in enumerate(CLUMPS[:14]):
        a = f0 + i * 7; b = a + 26
        if b > f1: clump_park(cl, f0); continue
        x = random.uniform(-0.45, 0.45)
        clump_fall(cl, a, b, Vector((x, random.uniform(0.15, 0.9), 0.55)), Vector((x * 0.9, random.uniform(0.2, 0.9), -0.35 + 0.33 * (i / 14))))
        clump_park(cl, a - 1); keyobj(cl, f1, loc=cl.location.copy())
    c = camera("G01", 40)
    cam_key(c, f0, (0.25, -4.6, -0.35), (0, 0.6, 0.15)); cam_key(c, f1, (0.15, -4.1, -0.30), (0, 0.6, 0.12))

def SG02(f0, f1):
    PRESENT["G02"] = {"dog"}
    g_dog(f0, f1, breath_amp=3.0)
    fill_key(f0, 0.96); fill_key(f1, 0.97)
    random.seed(9)
    for i, cl in enumerate(CLUMPS[:8]):
        a = f0 + i * 9; b = a + 22
        x = random.uniform(-0.4, 0.4)
        clump_fall(cl, a, b, Vector((x, 0.5, 0.2)), Vector((x, 0.5, -0.05)))
        clump_park(cl, a - 1)
    c = camera("G02", 32)
    cam_key(c, f0, (0.35, -1.75, -0.55), (0.05, 0.2, -0.85)); cam_key(c, f1, (0.25, -1.45, -0.60), (0.05, 0.2, -0.85))

def SG03(f0, f1):
    PRESENT["G03"] = {"dad", "mom", "son", "dog"}
    g_dog(f0, f1, breath_amp=3.5)
    fill_key(f0, 1.0); keyobj(MOUND_G, f0, scale=(0.62, 0.62, 0.12))
    n = f1 - f0; tw = f0 + 40
    for key, x, y, yw, dl in (("dad", -0.55, 1.55, 8, 0), ("mom", 0.15, 1.75, -4, 10), ("son", 0.75, 1.55, -15, 18)):
        rig, H = CHARS[key]
        stand(H, rig, f0, Vector((x, y, 0)), yw, head=(30, 0), flex=6)
        t0 = tw + dl
        stand(H, rig, t0, Vector((x, y, 0)), yw, head=(10, 0), flex=2)
        st = Vector((x, y, 0)); en = Vector((x + 0.3 * (1 if x > 0 else -1), y + 5.5 - dl * 0.04, 0))
        pth = lambda f, st=st, en=en, t0=t0: st.lerp(en, max(0.0, min(1.0, (f - t0) / (f1 - t0))))
        yfn = lambda f, t0=t0, yw=yw: yw + (180 - yw) * ease(max(0.0, min(1.0, (f - t0) / 30.0)))
        H.walk(pth, yfn, t0 + 1, f1, stride=0.72)
        walk_arms(rig, H, pth, yfn, t0 + 1, f1, stride=0.72 * 2)
        for f in sorted(set(range(t0 + 1, f1 + 1, 6)) | {f1}): H.key_spine(f, flex=4, head=(0, 0))
    random.seed(4)
    c = camera("G03", 40)
    cam_key(c, f0, (0.0, -4.4, -0.45), (0, 0.6, 0.05)); cam_key(c, f1, (0.0, -4.8, -0.20), (0, 1.2, 0.35))

# ================================================================== ROAD shots
def SR04(f0, f1):
    PRESENT["R04"] = {"dog"}
    n = f1 - f0
    pth = lambda f: RX + Vector((1.6, 9.0 - 6.6 * (f - f0) / n, 0))
    dog_walk(pth, f0, f1, 1.05, "trot", RX + Vector((1.6, 0, 0)), wag=12, head=(-6, 0, 0))
    car_drive(PKB, PKW, f0, f1, lambda t: (RX + Vector((1.6, 15.5 - 6.6 * t, 0))).to_2d())
    c = camera("R04", 32)
    cam_key(c, f0, RX + Vector((2.6, 4.6, 0.40)), RX + Vector((1.5, 10.0, 0.6)), lens=40); cam_key(c, f1, RX + Vector((2.6, 1.0, 0.40)), RX + Vector((1.5, 6.5, 0.55)), lens=40)

def SR05(f0, f1):
    PRESENT["R05"] = {"dog"}
    D = RX + Vector((2.35, 1.6, 0.0))
    for k in kr(f1 - f0, 10): dog_side(f0 + k, D + Vector((0, 0, 0.16)), 180, roll=90, breath=0.0)
    lids(f0, True); lids(f1, True)
    keyobj(PKB, f0, loc=RX + Vector((1.2, 6.2, 0)), rot=(0, 0, R_(4))); keyobj(PKB, f1, loc=RX + Vector((1.2, 6.2, 0)), rot=(0, 0, R_(4)))
    for w_ in PKW: keyobj(w_, f0, rot=(0, 0, 0)); keyobj(w_, f1, rot=(0, 0, 0))
    c = camera("R05", 30)
    cam_key(c, f0, RX + Vector((3.4, -0.6, 2.6)), RX + Vector((2.1, 2.9, 0.2))); cam_key(c, f1, RX + Vector((3.2, 0.0, 2.1)), RX + Vector((2.1, 2.8, 0.2)))

# ================================================================== YARD shots
DOG_LAWN = YX + Vector((-1.8, 0.6, 0))
def SY06(f0, f1):
    PRESENT["Y06"] = {"dad", "mom", "son", "dog"}
    for k in kr(f1 - f0, 10): dog_side(f0 + k, DOG_LAWN + Vector((0, 0, 0.16)), 90, roll=90)
    lids(f0, True); lids(f1, True)
    for k in (0, 50, f1 - f0):
        stand(HDAD, DAD, f0 + k, DOG_LAWN + Vector((0.15, 0.95, 0)), 0, head=(34 + 4 * math.sin(k * 0.04), 0), flex=12, breath=math.sin(k * 0.06 + 2))
        stand(HMOM, MOM, f0 + k, DOG_LAWN + Vector((-1.0, 1.9, 0)), 18, head=(26, -8), flex=4, breath=math.sin(k * 0.06))
        stand(HSON, SON, f0 + k, DOG_LAWN + Vector((1.05, 1.75, 0)), -20, head=(28, 6), flex=4, breath=math.sin(k * 0.06 + 1))
    c = camera("Y06", 30)
    cam_key(c, f0, DOG_LAWN + Vector((0.5, -3.6, 0.8)), DOG_LAWN + Vector((0.0, 1.2, 0.75)))
    cam_key(c, f1, DOG_LAWN + Vector((0.3, -3.1, 0.75)), DOG_LAWN + Vector((0.0, 1.2, 0.75)))

def SY07(f0, f1):
    PRESENT["Y07"] = {"dad", "mom", "son"}
    for k in (0, 55, f1 - f0):
        stand(HDAD, DAD, f0 + k, YMOUND + Vector((-0.2, 1.25, 0)), 5, head=(30, 0), flex=6, breath=math.sin(k * 0.05))
        stand(HMOM, MOM, f0 + k, YMOUND + Vector((-1.05, 0.95, 0)), 30, head=(28, -6), flex=5, breath=math.sin(k * 0.05 + 1))
        stand(HSON, SON, f0 + k, YMOUND + Vector((0.75, 1.05, 0)), -25, head=(30, 6), flex=5, breath=math.sin(k * 0.05 + 2))
        c = camera("Y07", 32)
    cam_key(c, f0, YMOUND + Vector((0.4, -3.4, 0.55)), YMOUND + Vector((0, 0.8, 0.75)))
    cam_key(c, f1, YMOUND + Vector((0.2, -2.8, 0.50)), YMOUND + Vector((0, 0.8, 0.75)))

DRV = YX + Vector((6.0, 1.0, 0))
def SY08(f0, f1):
    PRESENT["Y08"] = set()
    car_drive(SUVB, SUVW, f0, f1, eased(bez((DRV + Vector((0, 2.5, 0))).to_2d(), (DRV + Vector((0, -2, 0))).to_2d(),
                                            (DRV + Vector((0, -6, 0))).to_2d(), (DRV + Vector((-0.8, -7.8, 0))).to_2d())), rev=True)
    c = camera("Y08", 30)
    cam_key(c, f0, YX + Vector((1.2, -0.5, 1.2)), DRV + Vector((0, 2.0, 0.8))); cam_key(c, f1, YX + Vector((0.8, -1.5, 1.3)), DRV + Vector((-0.5, -6.5, 0.8)))

def SY09(f0, f1):
    PRESENT["Y09"] = set()
    car_drive(SUVB, SUVW, f0, f1, eased(lambda t: (YX + Vector((3.5 + 16 * t, -9.2, 0))).to_2d(), ein=True, eout=False))
    c = camera("Y09", 28)
    cam_key(c, f0, YX + Vector((4.0, -2.2, 1.1)), YX + Vector((4.5, -9.2, 0.9))); cam_key(c, f1, YX + Vector((10.0, -2.6, 1.3)), YX + Vector((15.5, -9.2, 0.9)))

# ================================================================== UNDERGROUND shots (grave set)
def SU10(f0, f1):
    PRESENT["U10"] = {"dog"}
    g_dog(f0, f1, breath_amp=3.0); fill_key(f0, 1.0)
    keyobj(MOUND_G, f0, scale=(0.62, 0.62, 0.12))
    sc.frame_set(f0); hd = DOG.matrix_world @ DOG.pose.bones["head"].head
    c = camera("U10", 40, fstop=9)
    cam_key(c, f0, hd + Vector((-0.16, -1.00, 0.10)), hd + Vector((-0.05, 0, -0.02))); cam_key(c, f1, hd + Vector((-0.13, -0.90, 0.09)), hd + Vector((-0.05, 0, -0.02)))

def SU11(f0, f1):
    PRESENT["U11"] = {"dog"}
    fill_key(f0, 1.0); keyobj(MOUND_G, f0, scale=(0.62, 0.62, 0.12))
    for k in kr(f1 - f0, 6):
        t = k / (f1 - f0)
        dog_side(f0 + k, DOG_G, YAW_G, roll=90, breath=4 * math.sin(k * 0.16), head=(-6 * ease(min(1, t * 2)), 0, 4 * math.sin(k * 0.2)))
    lids(f0, True); lids(f0 + 30, True); lids(f0 + 34, False); lids(f1, False)
    sc.frame_set(f0); hd = DOG.matrix_world @ DOG.pose.bones["head"].head
    c = camera("U11", 45, fstop=9)
    cam_key(c, f0, hd + Vector((-0.12, -0.92, 0.09)), hd + Vector((-0.03, 0, -0.01))); cam_key(c, f1, hd + Vector((-0.10, -0.84, 0.08)), hd + Vector((-0.03, 0, -0.01)))

def SU12(f0, f1):
    PRESENT["U12"] = {"dog"}
    fill_key(f0, 1.0); keyobj(MOUND_G, f0, scale=(0.62, 0.62, 0.12)); lids(f0, False); lids(f1, False)
    for k in kr(f1 - f0, 6):
        t = ease(min(1, k / (f1 - f0) * 1.4))
        dog_side(f0 + k, DOG_G, YAW_G, roll=90, breath=5 * math.sin(k * 0.2), head=(-14 * t, 0, 18 * t + 3 * math.sin(k * 0.25)), curl=1.0 - 0.3 * t)
    c = camera("U12", 32)
    cam_key(c, f0, (0.45, -1.6, -0.65), (0.15, 0.2, -0.82)); cam_key(c, f1, (0.40, -1.4, -0.55), (0.15, 0.2, -0.75))

def SU13(f0, f1):
    PRESENT["U13"] = {"dog"}
    fill_key(f0, 1.0); keyobj(MOUND_G, f0, scale=(0.62, 0.62, 0.12)); lids(f0, False)
    n = f1 - f0
    for k in kr(n, 4):
        t = k / n; up = ease(t)
        loc = Vector((-0.05, 0.24, -0.95 + 0.36 * up))
        pitch = -48
        pf = 0.5 + 0.5 * math.sin(k * 0.42); pr = 0.5 + 0.5 * math.sin(k * 0.42 + math.pi)
        pose = stand_pose(head=(-12, 0, 0), tail=8 * math.sin(k * 0.3))
        pose["IK_hoof.FL"] = ((0.02, -0.10 - 0.10 * pf, 0.10 + 0.16 * pf), None)
        pose["IK_hoof.FR"] = ((-0.02, -0.10 - 0.10 * pr, 0.10 + 0.16 * pr), None)
        pose["IK_hoof.HL"] = ((0.0, 0.02, 0.03 + 0.04 * pr), None); pose["IK_hoof.HR"] = ((0.0, 0.02, 0.03 + 0.04 * pf), None)
        dog_key(f0 + k, loc, (pitch, 0, 90), pose)
        # tunnel cutter rides with the dog (union with the pocket keeps the whole path open)
        keyobj(TUNNEL, f0 + k, loc=loc + Vector((0.12, 0, 0.18)), rot=(0, R_(-48), 0), scale=(0.62, 0.44, 0.40))
    keyobj(TUNNEL, f0 - 1, loc=Vector((0, 0.18, -60))); keyobj(TUNNEL, f1 + 1, loc=Vector((0, 0.18, -60)))
    random.seed(13)
    for i, cl in enumerate(CLUMPS):
        a = f0 + 4 + i * 7; b = a + 30
        if b > f1: clump_park(cl, f0); continue
        sc.frame_set(a); paw = DOG.matrix_world @ DOG.pose.bones["hoof.FL" if i % 2 else "hoof.FR"].head
        clump_fall(cl, a, b, paw + Vector((random.uniform(-0.05, 0.05), -0.16, 0.05)), paw + Vector((random.uniform(-0.3, 0.3), -0.18, -0.9)), arc=0.05)
        clump_park(cl, a - 1); clump_park(cl, b + 1)
    c = camera("U13", 32)
    cam_key(c, f0, (0.35, -1.9, -0.60), (0.1, 0.2, -0.62)); cam_key(c, f1, (0.30, -1.9, -0.35), (0.1, 0.2, -0.38))

YEXIT = YMOUND
def SY14(f0, f1):
    PRESENT["Y14"] = {"dog"}
    n = f1 - f0
    keyobj(HOLE, f0, loc=YEXIT + Vector((0, 0.0, 0))); keyobj(HOLE, f1, loc=YEXIT + Vector((0, 0.0, 0)))
    keyobj(HOLE, f0 - 1, loc=YEXIT + Vector((0, 0, -60))); keyobj(HOLE, f1 + 1, loc=YEXIT + Vector((0, 0, -60)))
    for k in kr(n, 4):
        t = k / n; up = ease(min(1, t * 1.25))
        pf = 0.5 + 0.5 * math.sin(k * 0.45); pr = 0.5 + 0.5 * math.sin(k * 0.45 + math.pi)
        pose = stand_pose(head=(-18 + 10 * up, 0, 6 * math.sin(k * 0.12)), tail=0)
        pose["IK_hoof.FL"] = ((0.02, -0.06 - 0.08 * pf * (1 - up), 0.12 + 0.10 * pf * (1 - up)), None)
        pose["IK_hoof.FR"] = ((-0.02, -0.06 - 0.08 * pr * (1 - up), 0.12 + 0.10 * pr * (1 - up)), None)
        dog_key(f0 + k, YEXIT + Vector((0, 0.42, -1.05 + 0.82 * up)), (-58 + 18 * up, 0, 0), pose)
    random.seed(17)
    for i, cl in enumerate(CLUMPS[:16]):
        a = f0 + i * 6; b = a + 28
        if b > f1: clump_park(cl, f0); continue
        ang = random.uniform(0, 6.28)
        clump_fall(cl, a, b, YEXIT + Vector((0.12 * math.cos(ang), 0.1 * math.sin(ang), 0.15)),
                   YEXIT + Vector((0.75 * math.cos(ang), 0.6 * math.sin(ang), 0.04)), arc=0.30)
        clump_park(cl, a - 1)
    c = camera("Y14", 30)
    cam_key(c, f0, YEXIT + Vector((0.45, -1.7, 0.40)), YEXIT + Vector((0, 0.2, 0.30))); cam_key(c, f1, YEXIT + Vector((0.3, -1.4, 0.45)), YEXIT + Vector((0, 0.2, 0.40)))

def SY15(f0, f1):
    PRESENT["Y15"] = set()
    car_drive(SUVB, SUVW, f0, f1, eased(bez((YX + Vector((-6.0, -9.0, 0))).to_2d(), (YX + Vector((3.0, -9.0, 0))).to_2d(),
                                            (DRV + Vector((0, -6.0, 0))).to_2d(), (DRV + Vector((0, 0.5, 0))).to_2d()), ein=False, eout=True))
    c = camera("Y15", 26)
    cam_key(c, f0, YX + Vector((0.5, 3.5, 1.1)), YX + Vector((-1.0, -9.0, 0.9))); cam_key(c, f1, YX + Vector((1.0, 5.0, 1.2)), DRV + Vector((0, -1.0, 0.8)))

PORCH_SPOT = YX + Vector((2.1, 6.0, 0))
def SY16(f0, f1):
    PRESENT["Y16"] = {"dog"}
    car_drive(SUVB, SUVW, f0, f1, eased(lambda t: (DRV + Vector((0, -2.2 + 2.7 * t, 0))).to_2d(), ein=False, eout=True))
    for k in kr(f1 - f0, 4):
        dog_key(f0 + k, PORCH_SPOT, (0, 0, 120), stand_pose(head=(-4, 0, 10 * math.sin(k * 0.05)), tail=0,
                ext={"tail1": (None, (15, 0, 35 * math.sin(k * 0.7))), "tail2": (None, (0, 0, 25 * math.sin(k * 0.7 - 0.6)))}))
    c = camera("Y16", 28)
    cam_key(c, f0, PORCH_SPOT + Vector((-1.1, 1.6, 0.75)), DRV + Vector((-0.5, -1.0, 0.7))); cam_key(c, f1, PORCH_SPOT + Vector((-0.9, 1.4, 0.70)), DRV + Vector((-0.5, -0.5, 0.7)))

# ================================================================== PORCH shots
DOG_P = PX + Vector((0.0, 0.25, DECK_Z))
def porch_dog(f0, f1, head_fn, wag=38, pant=4):
    for k in kr(f1 - f0, 3):
        h = head_fn(k)
        dog_key(f0 + k, DOG_P, (0, 0, 0), stand_pose(head=h, pant=pant * math.sin(k * 0.9),
                ext={"tail1": (None, (20, 0, wag * math.sin(k * 0.75))), "tail2": (None, (0, 0, wag * 0.7 * math.sin(k * 0.75 - 0.7))),
                     "spine2": (None, (0, 0, 3 * math.sin(k * 0.75)))}))
def SP17(f0, f1):
    PRESENT["P17"] = {"dog"}
    porch_dog(f0, f1, lambda k: (-3, 0, 8 * math.sin(k * 0.04)))
    c = camera("P17", 26)
    cam_key(c, f0, PX + Vector((0.25, -1.75, 0.80)), PX + Vector((0, 0.6, 1.05)), lens=30); cam_key(c, f1, PX + Vector((0.15, -1.45, 0.78)), PX + Vector((0, 0.6, 1.0)), lens=30)
def SP18(f0, f1):
    PRESENT["P18"] = {"dog"}
    porch_dog(f0, f1, lambda k: (-5, 0, -15 + 6 * math.sin(k * 0.05)), wag=45)
    c = camera("P18", 30)
    cam_key(c, f0, PX + Vector((1.55, -0.6, 0.85)), PX + Vector((0, 0.45, 0.85))); cam_key(c, f1, PX + Vector((1.35, -0.8, 0.82)), PX + Vector((0, 0.45, 0.85)))
def SP19(f0, f1):
    PRESENT["P19"] = {"dog"}
    porch_dog(f0, f1, lambda k: (-8 + 4 * math.sin(k * 0.06), 12 * math.sin(k * 0.035), 0), wag=40, pant=6)
    sc.frame_set(f0); hd = DOG.matrix_world @ DOG.pose.bones["head"].head
    c = camera("P19", 40, fstop=9)
    cam_key(c, f0, hd + Vector((0.05, -0.95, 0.02)), hd + Vector((0, 0, 0.0))); cam_key(c, f1, hd + Vector((0.03, -0.75, 0.01)), hd + Vector((0, 0, 0.0)))

# ================================================================== reaction
FAM = {"dad": (YX + Vector((4.35, 0.6, 0)), -100), "mom": (YX + Vector((4.0, -0.35, 0)), -80), "son": (YX + Vector((4.75, -1.1, 0)), -70)}
def park_suv(f0, f1):
    for f in (f0, f1):
        keyobj(SUVB, f, loc=DRV + Vector((0.6, 0.5, 0)), rot=(0, 0, R_(180)))
        for w_ in SUVW: keyobj(w_, f, rot=(0, 0, 0))
def SY20(f0, f1):
    PRESENT["Y20"] = {"dad", "mom", "son", "dog"}
    park_suv(f0, f1); n = f1 - f0
    for key, (p, yw) in FAM.items():
        rig, H = CHARS[key]
        for k in (0, 30):
            stand(H, rig, f0 + k, p, yw, head=(0, 0), breath=math.sin(k * 0.1))
        for k, a in ((55, 0.6), (75, 1.0), (n, 1.0)):
            horrified(H, rig, f0 + k, p, yw, a, back=0.30 if key != "son" else 0.15)
    pth = lambda f: YX + Vector((1.5, 2.0, 0)).lerp(Vector((3.0, 0.7, 0)), (f - f0) / n)
    dog_walk(pth, f0, f1, 0.95, "trot", YX + Vector((1.5, 1.5, 0)), wag=40, head=(-8, 0, 0))
    c = camera("Y20", 28)
    cam_key(c, f0, YX + Vector((-0.2, 3.0, 1.05)), YX + Vector((3.6, 0.3, 0.75)), lens=26); cam_key(c, f1, YX + Vector((0.3, 2.7, 1.05)), YX + Vector((3.8, 0.2, 0.85)), lens=26)
def SY21(f0, f1):
    PRESENT["Y21"] = {"dad", "mom", "son"}
    park_suv(f0, f1)
    for key, (p, yw) in FAM.items():
        rig, H = CHARS[key]
        for k in kr(f1 - f0, 30):
            horrified(H, rig, f0 + k, p, yw, 1.0, head=(3 * math.sin(k * 0.05), 4 * math.sin(k * 0.04)), back=0.30 if key != "son" else 0.15)
    c = camera("Y21", 35)
    cam_key(c, f0, YX + Vector((1.2, 0.9, 1.35)), YX + Vector((4.2, 0.1, 1.45))); cam_key(c, f1, YX + Vector((1.5, 0.75, 1.40)), YX + Vector((4.2, 0.1, 1.48)))

FUN = {"G01": SG01, "G02": SG02, "G03": SG03, "R04": SR04, "R05": SR05, "Y06": SY06, "Y07": SY07, "Y08": SY08, "Y09": SY09,
       "U10": SU10, "U11": SU11, "U12": SU12, "U13": SU13, "Y14": SY14, "Y15": SY15, "Y16": SY16, "P17": SP17, "P18": SP18,
       "P19": SP19, "Y20": SY20, "Y21": SY21}
