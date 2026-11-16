# exec'd by 03_anim.py: basement S16, backyard S17, water tower S18
M_tox = bpy.data.materials["Toxic"]; M_toxd = bpy.data.materials["ToxicDim"]
def ooze(name, c, radius, center, fa, grow, flat=0.004, rz=0.0, sx=1.0, sy=1.0):
    """an irregular green film that spreads from a point (keyed scale)"""
    bpy.ops.mesh.primitive_circle_add(vertices=64, radius=radius, fill_type='NGON', location=center)
    o = bpy.context.active_object; o.name = name; link(o, c)
    me = o.data; random.seed(hash(name) % 1000)
    ph = [random.uniform(0, 6.28) for _ in range(4)]
    for v in me.vertices:
        a = math.atan2(v.co.y, v.co.x)
        k = 1 + 0.18 * math.sin(3 * a + ph[0]) + 0.1 * math.sin(5 * a + ph[1]) + 0.06 * math.sin(9 * a + ph[2])
        v.co.x *= k * sx; v.co.y *= k * sy
    so = o.modifiers.new("thick", 'SOLIDIFY'); so.thickness = flat; so.offset = 1
    o.modifiers.new("sub", 'SUBSURF').levels = 2
    o.data.materials.append(M_tox)
    o.rotation_euler = (0, 0, R_(rz))
    o.scale = (0.02, 0.02, 1); o.keyframe_insert("scale", frame=0); o.keyframe_insert("scale", frame=fa)
    o.scale = (1, 1, 1); o.keyframe_insert("scale", frame=fa + grow)
    return o

# ================================================================== S16: basement: green liquid seeps out at the wall base and spreads
BX = Vector((1200, 0, 0)); fa = f0("S16"); fe = fx("S16")
BAS = OB["B_floor"].users_collection[0]
P1 = ooze("Seep_floor", BAS, 1.0, BX + Vector((0.2, 2.5, 0.002)), fa - 25, 150, sy=0.8)
P2 = ooze("Seep_floor2", BAS, 0.6, BX + Vector((-1.3, 2.5, 0.002)), fa + 40, 110, sy=0.7)
for i, (x, h) in enumerate(((-1.6, 0.42), (-0.9, 0.3), (-0.1, 0.55), (0.6, 0.36), (1.4, 0.48), (2.0, 0.25))):     # streaks out of the block joints
    bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=4, y_segments=10, size=0.5)
    w_ = 0.16 + 0.05 * (i % 2)
    for v in bm.verts:
        u = v.co.y + 0.5
        v.co = Vector((v.co.x * w_ * (1.0 - 0.45 * u) + 0.02 * math.sin(u * 9 + i), 0.0, u * h))
    me = bpy.data.meshes.new("Seep_streak.%d" % i); bm.to_mesh(me); bm.free()
    s_ = bpy.data.objects.new("Seep_streak.%d" % i, me); BAS.objects.link(s_); s_.data.materials.append(M_toxd)
    s_.location = BX + Vector((x, 2.488, 0.0))
    st = fa - 30 + i * 9
    s_.scale = (1, 1, 0.02); s_.keyframe_insert("scale", frame=0); s_.keyframe_insert("scale", frame=st)
    s_.scale = (1, 1, 1); s_.keyframe_insert("scale", frame=st + 70)
camshot("S16", [(0.0, (1200.35, -1.7, 1.2), (1200.0, 2.5, 0.35), 24), (1.0, (1200.15, 0.2, 0.8), (1200.0, 2.5, 0.3), 24)])

# ================================================================== S17: backyard: a green puddle spreads up through the lawn
YX = Vector((1500, 0, 0)); fa = f0("S17"); fe = fx("S17")
YRD = OB["Y_lawn"].users_collection[0]
ooze("Yard_puddle", YRD, 1.6, YX + Vector((0.2, -2.5, 0.005)), fa, 90, sx=1.3)
ooze("Yard_puddle2", YRD, 0.7, YX + Vector((-1.8, -1.2, 0.005)), fa + 25, 80)
camshot("S17", [(0.0, (1500.9, -10.8, 0.6), (1500.0, -1.5, 0.2), 24), (1.0, (1500.7, -9.3, 0.55), (1500.0, -1.5, 0.15), 24)])

# ================================================================== S18: water tower: green drips run down the tank
TX = Vector((1800, 0, 0)); fa = f0("S18"); fe = fx("S18")
TWR = OB["WaterTower"]; TC = TWR.users_collection[0]
def radius_at(z, ang=-90):
    d = Vector((math.cos(R_(ang)), math.sin(R_(ang)), 0))
    hit = sc.ray_cast(bpy.context.evaluated_depsgraph_get(), TX + d * 30 + Vector((0, 0, z)), -d, distance=40)
    return (30 - hit[1].__sub__(TX + d * 30 + Vector((0, 0, z))).length) if hit[0] and hit[4] == TWR else 0.0
ev(1)
prof = [(z / 4, radius_at(z / 4)) for z in range(0, 96)]
tank = [(z, r) for z, r in prof if r > 1.6]
zt0, zt1 = (min(z for z, r in tank), max(z for z, r in tank)) if tank else (12.0, 18.0)
print("TANK z", zt0, zt1, max(r for z, r in prof))
random.seed(4)
for i in range(14):
    ang = -90 + random.uniform(-55, 55); st = fa + i * 9 + random.randint(0, 6)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.1, segments=12, ring_count=8); dp = bpy.context.active_object; dp.name = "Drip.%d" % i
    dp.scale = (1, 1, 2.4); dp.data.materials.append(M_tox); link(dp, TC); bpy.ops.object.shade_smooth()
    ztop = zt1 - 0.4 - random.uniform(0, 0.8)
    for f in range(st, st + 130, 3):
        u = (f - st) / 130.0; z = ztop - (ztop - zt0 + 0.2) * (u ** 1.4)
        r = radius_at(z, ang) or radius_at(zt0 + 0.5, ang)
        d = Vector((math.cos(R_(ang)), math.sin(R_(ang)), 0))
        dp.location = TX + d * (r + 0.06) + Vector((0, 0, z)); dp.keyframe_insert("location", frame=f)
    key_vis(dp, [(0, False), (st, True)])
    # a thin streak left behind on the tank
    sk = plane("DripTrail.%d" % i, (0.07, 1.0), (0, 0, 0), M_toxd, TC)
    sk.data.transform(Matrix.Translation((0, -0.5, 0))); sk.rotation_euler = (R_(90), 0, R_(ang + 90))
    d = Vector((math.cos(R_(ang)), math.sin(R_(ang)), 0)); r0 = radius_at(ztop - 0.3, ang) or 2.0
    sk.location = TX + d * (r0 + 0.03) + Vector((0, 0, ztop))
    sk.scale = (1, 0.01, 1); sk.keyframe_insert("scale", frame=0); sk.keyframe_insert("scale", frame=st)
    sk.scale = (1, min(ztop - zt0, 6.0), 1); sk.keyframe_insert("scale", frame=st + 130)
camshot("S18", [(0.0, (1803.0, -24.0, 1.6), (1800.0, 0.0, (zt0 + zt1) / 2 - 3.0), 30), (1.0, (1802.6, -22.5, 1.7), (1800.0, 0.0, (zt0 + zt1) / 2), 30)])
