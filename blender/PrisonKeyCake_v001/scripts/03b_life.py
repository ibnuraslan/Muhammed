# Background life (exec'd inside 03_animate.py, before the guard is baked): yard prisoners, patrol guard with lantern, pigeons.
# ---- two prisoners walking the exercise loop (day, beats 3-5)
def loop_pts(cx, cy, rx, ry, a0, turns, n=24):
    return [(cx + rx * math.cos(a0 + 2 * math.pi * turns * i / n), cy + ry * math.sin(a0 + 2 * math.pi * turns * i / n)) for i in range(n + 1)]
for nm, a0, ph in (("YardP1", 0.4, 0), ("YardP2", 2.6, 20)):
    Y = Actor(nm)
    pts = loop_pts(-4.5, 9.5, 3.4, 4.0, a0, 0.5)
    p0 = Vector((pts[0][0], pts[0][1], 0.0))
    pth, yfn = Y.walk(300 + ph, 880, pts, stride=0.7, lean=4)
    y0 = yfn(300 + ph)
    Y.stand(1, Vector((pts[0][0], pts[0][1], 0.99)), y0)
    Y.k(1, root=Vector((pts[0][0], pts[0][1], 0.99)), yaw=y0, hL=HANG["L"], hR=HANG["R"], sp_flex=8, h_pitch=12)
    arm_swing(Y, 300 + ph, 880, pth, amp=0.07)
    end_walk(Y, 880, pth, yfn)
    Y.k(880, root=pth(880) + Vector((0, 0, 0.99)), yaw=yfn(880))
    Y.k(500 + ph, h_yaw=25); Y.k(620 + ph, h_yaw=-10); Y.k(760, h_yaw=15)
    Y.bake(1, 900)
    key_hide(Y.o, [(1, False), (900, True)])
# ---- second guard: walks the north wall by day, patrols the night yard with a lantern (beats 9-10)
G2 = Actor("Guard2")
G2.stand(1, Vector((-7.0, 14.2, 0.99)), 90)
G2.k(1, root=Vector((-7.0, 14.2, 0.99)), yaw=90, hL=HANG["L"], hR=HANG["R"], h_pitch=5)
pd, yd = G2.walk(280, 900, [(-7.0, 14.2), (-1.0, 14.1), (5.0, 14.2), (7.8, 12.8)], stride=0.72)
arm_swing(G2, 280, 900, pd, amp=0.06)
end_walk(G2, 900, pd, yd)
G2.k(900, root=pd(900) + Vector((0, 0, 0.99)), yaw=yd(900))
# night: lantern patrol from the gate towards the cell block, he stops and lifts the lantern towards the corridor exit
LANT = [o for o in bpy.data.objects if o.name.startswith("Lantern_01") and o.name.endswith("_Y2")]
lant_src = bpy.data.objects["Lantern_01_Y0"]
hl = lant_src.copy(); hl.name = "Lantern_Patrol"; sc.collection.objects.link(hl)
hlg = bpy.data.objects["Lantern_01_glass_Y0"].copy(); hlg.name = "Lantern_Patrol_glass"; sc.collection.objects.link(hlg); hlg.parent = hl; hlg.matrix_parent_inverse = hl.matrix_world.inverted()
pl = bpy.data.lights.new("L_PatrolLantern", 'POINT'); pl.energy = 30; pl.color = (1.0, 0.6, 0.28); pl.shadow_soft_size = 0.05
plo = bpy.data.objects.new("L_PatrolLantern", pl); sc.collection.objects.link(plo); plo.parent = hl; plo.location = (0, 0, 0.15)
G2.k(1520, root=Vector((7.8, 10.0, 0.99)), yaw=195)
G2.stand(1521, Vector((7.8, 10.0, 0.99)), 195)
pn, yn = G2.walk(1560, 1760, [(7.8, 10.0), (7.2, 7.4), (5.8, 4.8), (4.6, 3.8)], stride=0.7)
end_walk(G2, 1760, pn, yn)
G2.k(1760, root=pn(1760) + Vector((0, 0, 0.99)), yaw=yn(1760))
G2.k(1800, yaw=260, h_yaw=10, h_pitch=-5)
for i, s_ in enumerate("LR"):
    G2.plant(s_, 1766 + i * 10, 1782 + i * 10, G2.h.foot_xy(s_, pn(1760), 260), 260)
arm_swing(G2, 1560, 1760, pn, amp=0.05)
def lantern_m(f):
    p, yw = G2.root_at(f); Rz = Matrix.Rotation(R_(yw), 3, 'Z')
    sw = 0.03 * math.sin(f / 6.0)
    lift = 0.0 if f < 1790 else 0.35 * smooth((f - 1790) / 25.0)
    return Matrix.Translation(p + Rz @ Vector((-0.27, -0.12 - lift * 0.5, -0.4 + lift + sw))) @ Matrix.Rotation(R_(yw), 4, 'Z')
G2.hand_fn["R"].append((1500, 1890, lambda f: grip_hand(lantern_m(f) @ Vector((0, 0, 0.3)), Vector((0, 0, -1)) if True else None, Matrix.Rotation(R_(G2.root_at(f)[1]), 3, 'Z') @ Vector((1, 0, 0)))))
G2.compile()
bake_obj(hl, 1500, 1890, lantern_m)
key_hide(hl, [(1, True), (1524, False)])
G2.bake()
key_hide(G2.o, [(1, False), (905, True), (1524, False)])
# ---- pigeons: a few circling the yard by day, a flock bursting off the government steps at the reveal
M_BIRD = bpy.data.materials.new("M_Pigeon"); M_BIRD.use_nodes = True
M_BIRD.node_tree.nodes["Principled BSDF"].inputs['Base Color'].default_value = (0.32, 0.33, 0.36, 1)
M_BIRD.node_tree.nodes["Principled BSDF"].inputs['Roughness'].default_value = 0.8
def make_bird(name):
    import bmesh
    me = bpy.data.meshes.new(name); bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=10, v_segments=6, radius=0.06)
    for v in bm.verts: v.co.y *= 2.0; v.co.z *= 0.9
    r = bmesh.ops.create_uvsphere(bm, u_segments=8, v_segments=5, radius=0.035)
    for v in r['verts']: v.co += Vector((0, -0.13, 0.04))
    bm.to_mesh(me); bm.free(); me.materials.append(M_BIRD)
    b = bpy.data.objects.new(name, me); sc.collection.objects.link(b)
    wings = []
    for sg in (1, -1):
        wm = bpy.data.meshes.new(name + "_w"); wb = bmesh.new()
        vs = [wb.verts.new(v) for v in ((0, -0.05, 0), (0, 0.06, 0), (sg * 0.24, 0.05, 0), (sg * 0.2, -0.02, 0))]
        wb.faces.new(vs if sg > 0 else vs[::-1]); wb.to_mesh(wm); wb.free(); wm.materials.append(M_BIRD)
        w = bpy.data.objects.new(name + ("_wL" if sg > 0 else "_wR"), wm); sc.collection.objects.link(w); w.parent = b; w.location = (sg * 0.03, 0, 0.02)
        wings.append((w, sg))
    return b, wings
random.seed(12)
BIRDS = []
for i in range(14):
    b, wings = make_bird("Pigeon%02d" % i)
    if i < 5:   # circling the yard (day) 1-900
        cx, cy, r, h, sp = random.uniform(-3, 3), random.uniform(7, 11), random.uniform(3, 6), random.uniform(6, 10), random.choice((1, -1)) * random.uniform(0.25, 0.4)
        f0, f1 = 1, 900; ph = random.uniform(0, 6.28)
        def pos(f, cx=cx, cy=cy, r=r, h=h, sp=sp, ph=ph): a = ph + sp * f / 60.0; return Vector((cx + r * math.cos(a), cy + r * math.sin(a), h + 0.4 * math.sin(f / 50.0)))
    else:       # burst off the steps 1785-1890
        x0, y0 = random.uniform(-4, 4), GY + random.uniform(0.3, 2.0); z0 = TOPZ * random.uniform(0.2, 0.9)
        dv = Vector((random.uniform(-3, 3), random.uniform(-5, -2), random.uniform(3, 5)))
        f0, f1 = 1600, 1890; t0 = random.randint(1785, 1805)
        def pos(f, x0=x0, y0=y0, z0=z0, dv=dv, t0=t0):
            t = max(0.0, (f - t0) / 60.0); return Vector((x0, y0, z0 + 0.06)) + dv * t + Vector((0, 0, -0.6 * t * t))
    def bm_(f, pos=pos):
        p = pos(f); d = pos(f + 2) - pos(f - 2)
        if d.length < 1e-5: d = Vector((0, -1, 0))
        return Matrix.Translation(p) @ (Vector((0, -1, 0)).rotation_difference(d.normalized())).to_matrix().to_4x4()
    bake_obj(b, f0, f1, bm_, step=3)
    for w, sg in wings:
        for f in range(f0, f1 + 1, 3):
            moving = i < 5 or f >= 1785
            w.rotation_euler = (0, sg * R_(35 * math.sin(f * 0.9 + i) if moving else -70 * sg * sg), 0); w.keyframe_insert("rotation_euler", frame=f)
    key_hide(b, [(1, i >= 5), (900 if i < 5 else 1, i < 5)] if i < 5 else [(1, True), (1730, False)])
