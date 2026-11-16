# Bind the static skeleton mesh to a copy of the Dead rig (rigid nearest-bone weights with joint blending).
# exec'd by 02_build.py: needs bpy, Vector, Matrix. Returns (skel_rig, skel_obj).
def skel_bind(DEAD, SKEL, name="SkelRig"):
    rig = DEAD.copy(); rig.data = DEAD.data.copy(); rig.name = name
    if rig.animation_data: rig.animation_data_clear()
    DEAD.users_collection[0].objects.link(rig)
    rig.location = (0, 0, 0); rig.rotation_euler = (0, 0, 0)
    for pb in rig.pose.bones:
        pb.rotation_mode = 'QUATERNION'; pb.location = (0, 0, 0); pb.rotation_quaternion = (1, 0, 0, 0)
        for c in pb.constraints:
            for at in ("target", "pole_target"):
                if getattr(c, at, None) is DEAD: setattr(c, at, rig)
    body = next(c for c in DEAD.children if c.name.endswith(".body"))
    Minv = DEAD.matrix_world.inverted(); bpts = [Minv @ body.matrix_world @ v.co for v in body.data.vertices]
    H = max(p.z for p in bpts) - min(p.z for p in bpts)
    sk = SKEL.copy(); sk.data = SKEL.data.copy(); sk.name = name + "_Skeleton"
    DEAD.users_collection[0].objects.link(sk)
    me = sk.data
    pts = [v.co for v in me.vertices]; h0 = max(p.z for p in pts) - min(p.z for p in pts)
    s = (H * 0.985) / h0
    cx = (max(p.x for p in bpts) + min(p.x for p in bpts)) / 2; cy = sum(p.y for p in bpts) / len(bpts)
    me.transform(Matrix.Translation(Vector((cx, cy - 0.005, min(p.z for p in bpts) + 0.01))) @ Matrix.Scale(s, 4))
    me.update()
    # turn the rig's upper arms so its arm bones lie along the skeleton's arms (skeleton hangs its arms closer to the body)
    BN = rig.data.bones
    muted = []
    for pb in rig.pose.bones:
        for c in pb.constraints:
            if c.influence > 0: muted.append((c, c.influence)); c.influence = 0.0
    bpy.context.view_layer.update()
    for sd, sx in (("L", 1), ("R", -1)):
        sh = BN["upperarm01." + sd].head_local; wr = BN["wrist." + sd].head_local
        cand = [v.co for v in me.vertices if v.co.x * sx > abs(sh.x) * 0.9 and wr.z - 0.25 < v.co.z < sh.z - 0.15]
        if not cand: continue
        lowz = sorted(cand, key=lambda p: p.z)[:max(20, len(cand) // 12)]
        hand = sum(lowz, Vector()) / len(lowz)
        tgt = Vector((hand.x, hand.y, hand.z + 0.08))
        el = BN["lowerarm01." + sd].head_local
        lu = (el - sh).length; ll = (wr - el).length
        el_s = sh + (tgt - sh) * (lu / (lu + ll))           # skeleton elbow on its straight arm
        bpy.context.view_layer.update()
        pu = rig.pose.bones["upperarm01." + sd]
        q = (el - sh).rotation_difference(el_s - sh)
        pu.matrix = Matrix.Translation(sh) @ q.to_matrix().to_4x4() @ Matrix.Translation(-sh) @ pu.matrix
        bpy.context.view_layer.update()
        pl = rig.pose.bones["lowerarm01." + sd]
        e_now = pl.head.copy(); w_now = rig.pose.bones["wrist." + sd].head.copy()
        q2 = (w_now - e_now).rotation_difference(tgt - e_now)
        pl.matrix = Matrix.Translation(e_now) @ q2.to_matrix().to_4x4() @ Matrix.Translation(-e_now) @ pl.matrix
        bpy.context.view_layer.update()
        print("SKEL arm", sd, tuple(round(x, 3) for x in hand), round(q.angle * 57.3, 1), round(q2.angle * 57.3, 1),
              tuple(round(x, 3) for x in rig.pose.bones["wrist." + sd].head))
    bpy.context.view_layer.objects.active = rig
    for o in bpy.context.selected_objects: o.select_set(False)
    rig.select_set(True)
    bpy.ops.object.mode_set(mode='POSE'); bpy.ops.pose.armature_apply(selected=False)
    bpy.ops.object.mode_set(mode='EDIT'); eb = rig.data.edit_bones
    for sd in "LR":
        b = eb["IK_hand." + sd]; w = eb["wrist." + sd]; b.head, b.tail, b.roll = w.head.copy(), w.tail.copy(), w.roll
    bpy.ops.object.mode_set(mode='OBJECT')
    for c, inf in muted: c.influence = inf
    for pb in rig.pose.bones: pb.rotation_quaternion = (1, 0, 0, 0)
    # nearest-bone weights over the main deform bones
    MAIN = [b for b in rig.data.bones if b.use_deform and not b.name.startswith(
        ("oris", "tongue", "levator", "special", "orbicularis", "temporalis", "oculi", "risorius", "jaw", "eye", "breast", "toe"))]
    segs = [(b.name, b.head_local.copy(), b.tail_local.copy()) for b in MAIN]
    for n, _, _ in segs: sk.vertex_groups.new(name=n)
    gi = {g.name: g.index for g in sk.vertex_groups}
    def dseg(p, a, b):
        ab = b - a; t = max(0.0, min(1.0, (p - a).dot(ab) / max(ab.length_squared, 1e-9)))
        return (p - (a + ab * t)).length
    for v in me.vertices:
        ds = sorted(((dseg(v.co, a, b), n) for n, a, b in segs))[:2]
        (d0, n0), (d1, n1) = ds
        w0 = 1.0 / (d0 ** 4 + 1e-9); w1 = 1.0 / (d1 ** 4 + 1e-9); t = w0 + w1
        sk.vertex_groups[gi[n0]].add([v.index], w0 / t, 'REPLACE')
        if w1 / t > 0.05: sk.vertex_groups[gi[n1]].add([v.index], w1 / t, 'REPLACE')
    sk.parent = rig; md = sk.modifiers.new("Armature", 'ARMATURE'); md.object = rig
    sk.hide_render = sk.hide_viewport = False
    return rig, sk
