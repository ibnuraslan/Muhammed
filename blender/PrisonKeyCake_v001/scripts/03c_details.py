# Detail pass (exec'd at the end of 03_animate.py): face acting, night lantern, dust, glasses, hats, crowd variation, skin pores.
import bmesh
PR_ = Rig(bpy.data.objects["Prisoner"])
def face_keys(rig, keys):
    """keys: [(f, eye_yaw, eye_pitch, jaw)] -> eye + jaw rotations (rest-relative)"""
    for f, ey, ep, jw in keys:
        for s_ in "LR": rig.key_rot("eye." + s_, f, [("Z", ey), ("X", ep)])
        rig.key_rot("jaw", f, [("X", jw)])
face_keys(PR_, [(1, 0, 8, 0), (22, -28, 4, 0), (40, -30, 4, 0), (58, 0, 14, 0), (150, 0, 18, 0), (230, 3, 18, 0), (300, 0, 10, 2),
                (340, -30, 0, 0), (360, -28, 2, 0), (380, 0, 8, 0),
                (894, 0, 14, 0), (930, 2, 16, 0), (938, -30, 26, 0), (952, -26, 24, 0), (960, 0, 14, 0), (990, 0, 10, 4), (1010, 0, 18, 6), (1040, 0, 12, 1),
                (1120, 0, 20, 0), (1200, 0, -20, 3), (1260, 0, 16, 0), (1290, -12, 8, 0),
                (1340, 0, 20, 0), (1372, 0, 6, 0), (1405, 4, 10, 0), (1418, 0, 8, 0), (1428, 0, 4, 9), (1445, 0, 0, 3),
                (1500, 12, 0, 0), (1540, -14, 0, 0), (1580, 10, -2, 0), (1640, -16, 0, 0), (1700, 8, -4, 0), (1780, -10, 0, 0), (1890, 0, 0, 0)])
# --- guard's lantern passing outside the cell door during the jam (light leaks under the door)
gl = bpy.data.lights.new("L_PassingLantern", 'POINT'); gl.color = (1.0, 0.6, 0.28); gl.shadow_soft_size = 0.05
glo = bpy.data.objects.new("L_PassingLantern", gl); sc.collection.objects.link(glo)
for f, x, e in ((1, 8.0, 0), (920, 8.0, 0), (926, 7.2, 60), (944, 2.6, 60), (966, 2.6, 60), (990, 5.5, 60), (1000, 7.5, 0)):
    glo.location = (x, -0.35 + 0.1 * math.sin(f / 4.0), 0.55); glo.keyframe_insert("location", frame=f)
    gl.energy = e; gl.keyframe_insert("energy", frame=f)
for f in range(920, 1001, 3):
    gl.energy = 60 * (0.85 + 0.15 * math.sin(f * 1.3)) if 926 <= f <= 990 else 0; gl.keyframe_insert("energy", frame=f)
# --- soft warm night fill on the door (reads as candle bounce) so the lock macros are legible
df = bpy.data.lights.new("L_DoorFill", 'AREA'); df.size = 0.6; df.color = (1.0, 0.7, 0.45)
dfo = bpy.data.objects.new("L_DoorFill", df); sc.collection.objects.link(dfo); dfo.location = (1.1, 0.9, 1.6)
dfo.rotation_euler = (Vector((2.0, 0.6, 1.1)) - dfo.location).to_track_quat('-Z', 'Y').to_euler()
for f, e in ((1, 0.0), (860, 0.0), (885, 9.0), (1050, 9.0), (1080, 0.0), (1380, 0.0), (1400, 9.0), (1460, 9.0), (1480, 0.0)):
    df.energy = e; df.keyframe_insert("energy", frame=f)
# --- dust in the cell light (thin volume, cell interior only)
bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
for v in bm.verts: v.co = Vector((v.co.x * 3.9, v.co.y * 3.9, (v.co.z + 0.5) * 2.95))
me = bpy.data.meshes.new("CellDust"); bm.to_mesh(me); bm.free()
du = bpy.data.objects.new("CellDust", me); sc.collection.objects.link(du)
md = bpy.data.materials.new("M_Dust"); md.use_nodes = True; nt = md.node_tree; nt.nodes.remove(nt.nodes["Principled BSDF"])
vs = nt.nodes.new('ShaderNodeVolumePrincipled'); vs.inputs['Color'].default_value = (0.9, 0.85, 0.75, 1); vs.inputs['Anisotropy'].default_value = 0.45
nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 6.0
mr = nt.nodes.new('ShaderNodeMapRange'); mr.inputs['To Min'].default_value = 0.004; mr.inputs['To Max'].default_value = 0.03
nt.links.new(nz.outputs['Fac'], mr.inputs['Value']); nt.links.new(mr.outputs['Result'], vs.inputs['Density'])
nt.links.new(vs.outputs['Volume'], nt.nodes["Material Output"].inputs['Volume']); me.materials.append(md)
du.visible_shadow = False
key_hide(du, [(1, False), (1460, True)])
# --- glasses on the older man (Child Of the head bone)
def child_of_head(o, arm, bone="head"):
    c = o.constraints.new('CHILD_OF'); c.target = arm; c.subtarget = bone
    c.inverse_matrix = (arm.matrix_world @ arm.data.bones[bone].matrix_local).inverted()
PRo = bpy.data.objects["President"]; bpy.context.view_layer.update()
M_GL = bpy.data.materials.new("M_GlassFrame"); M_GL.use_nodes = True
M_GL.node_tree.nodes["Principled BSDF"].inputs['Base Color'].default_value = (0.03, 0.025, 0.02, 1); M_GL.node_tree.nodes["Principled BSDF"].inputs['Metallic'].default_value = 0.6
M_LENS = bpy.data.materials.new("M_Lens"); M_LENS.use_nodes = True; bl = M_LENS.node_tree.nodes["Principled BSDF"]
bl.inputs['Transmission Weight'].default_value = 1.0; bl.inputs['Roughness'].default_value = 0.02; bl.inputs['IOR'].default_value = 1.5
bm = bmesh.new()
eyes = [PRo.data.bones["eye." + s_].head_local for s_ in "LR"]
for e in eyes:
    c = e + Vector((0, -0.042, 0.002))
    r = bmesh.ops.create_circle(bm, cap_ends=False, segments=20, radius=0.021)
    for v in r['verts']: v.co = Vector((c.x + v.co.x, c.y, c.z + v.co.y * 0.8))
    for i in range(20):
        a0, a1 = r['verts'][i].co, r['verts'][(i + 1) % 20].co
        t = bmesh.ops.create_cone(bm, cap_ends=True, segments=5, radius1=0.0016, radius2=0.0016, depth=(a1 - a0).length * 1.1)
        bmesh.ops.rotate(bm, verts=t['verts'], matrix=Vector((0, 0, 1)).rotation_difference((a1 - a0).normalized()).to_matrix())
        bmesh.ops.translate(bm, verts=t['verts'], vec=(a0 + a1) / 2)
    for v in r['verts']: bm.verts.remove(v)
    side = 1 if e.x > 0 else -1
    t = bmesh.ops.create_cone(bm, cap_ends=True, segments=5, radius1=0.0015, radius2=0.0015, depth=0.07)
    bmesh.ops.rotate(bm, verts=t['verts'], matrix=Matrix.Rotation(R_(90), 3, 'X'))
    bmesh.ops.translate(bm, verts=t['verts'], vec=Vector((c.x + side * 0.036, c.y + 0.036, c.z + 0.006)))
t = bmesh.ops.create_cone(bm, cap_ends=True, segments=5, radius1=0.0015, radius2=0.0015, depth=abs(eyes[0].x - eyes[1].x) - 0.04)
bmesh.ops.rotate(bm, verts=t['verts'], matrix=Matrix.Rotation(R_(90), 3, 'Y'))
bmesh.ops.translate(bm, verts=t['verts'], vec=(eyes[0] + eyes[1]) / 2 + Vector((0, -0.044, 0.008)))
me = bpy.data.meshes.new("Glasses"); bm.to_mesh(me); bm.free(); me.materials.append(M_GL)
gls = bpy.data.objects.new("President_Glasses", me); sc.collection.objects.link(gls); gls.matrix_world = PRo.matrix_world.copy()
child_of_head(gls, PRo)
key_hide(gls, [(1, True), (1730, False)])
# --- crowd hats (bowlers and flat caps, Child Of the head; some waved in the hand) + per-person clothing variation
M_HAT = bpy.data.materials.new("M_Hat"); M_HAT.use_nodes = True; nt = M_HAT.node_tree; hb = nt.nodes["Principled BSDF"]
oi = nt.nodes.new('ShaderNodeObjectInfo'); hc = nt.nodes.new('ShaderNodeValToRGB')
hc.color_ramp.elements[0].color = (0.03, 0.03, 0.03, 1); hc.color_ramp.elements[1].color = (0.25, 0.2, 0.15, 1)
nt.links.new(oi.outputs['Random'], hc.inputs['Fac']); nt.links.new(hc.outputs['Color'], hb.inputs['Base Color']); hb.inputs['Roughness'].default_value = 0.7
def hat_mesh(kind):
    bm = bmesh.new()
    if kind == "bowler":
        r = bmesh.ops.create_uvsphere(bm, u_segments=20, v_segments=10, radius=0.1)
        for v in r['verts']:
            v.co.z = max(v.co.z, 0.0) * 0.95
        b = bmesh.ops.create_cone(bm, cap_ends=True, segments=24, radius1=0.15, radius2=0.15, depth=0.008)
    else:
        r = bmesh.ops.create_uvsphere(bm, u_segments=20, v_segments=8, radius=0.105)
        for v in r['verts']: v.co.z = max(v.co.z, 0.0) * 0.35
        b = bmesh.ops.create_cone(bm, cap_ends=True, segments=16, radius1=0.08, radius2=0.08, depth=0.006)
        for v in b['verts']: v.co.y -= 0.07
    me = bpy.data.meshes.new("Hat_" + kind); bm.to_mesh(me); bm.free(); me.materials.append(M_HAT)
    for p in me.polygons: p.use_smooth = True
    return me
HATS = {k: hat_mesh(k) for k in ("bowler", "cap")}
def head_top(arm):
    body = [c for c in bpy.data.objects if c.parent == arm and c.name.split(".")[-1] == "body"] or [c for c in arm.children if "body" in c.name]
    hd = arm.data.bones["head"].head_local
    pts = [v.co for v in body[0].data.vertices if abs(v.co.x - hd.x) < 0.08 and abs(v.co.y - hd.y) < 0.08] if body else []
    return Vector((hd.x, hd.y - 0.005, (max(p.z for p in pts) if pts else hd.z + 0.18)))
random.seed(31)
sc.frame_set(1730); dg_ = bpy.context.evaluated_depsgraph_get()
for i, a in enumerate(CROWD):
    kind = "bowler" if i % 4 in (1,) else "cap"
    if i % 2 == 0 and i % 3 != 0: continue      # bob-haired figures: no hat on the head (only waved in the hand)
    h = bpy.data.objects.new("CrowdHat%02d" % i, HATS["bowler" if i % 3 == 0 else kind]); sc.collection.objects.link(h)
    if i % 3 == 0:     # waved in the raised hand
        pbw = a.pose.bones["wrist.R"]; Mw = a.matrix_world @ pbw.matrix
        h.matrix_world = Mw @ Matrix.Translation(Vector((0.0, 0.08, 0.03))) @ Matrix.Rotation(R_(80), 4, 'X')
        c = h.constraints.new('CHILD_OF'); c.target = a; c.subtarget = "wrist.R"; c.inverse_matrix = Mw.inverted()
    else:
        body = next(ch for ch in a.children if ch.name.split(".")[1] == "body") if any(len(ch.name.split(".")) > 1 and ch.name.split(".")[1] == "body" for ch in a.children) else next(ch for ch in a.children if "body" in ch.name)
        hair = [ch for ch in a.children if any(k in ch.name for k in ("bob02", "short03"))]
        pbh = a.pose.bones["head"]; Mh = a.matrix_world @ pbh.matrix; hp = Mh.translation
        topz = -9.0
        for ob_ in [body] + hair:
            e = ob_.evaluated_get(dg_); me = e.to_mesh()
            for v in me.vertices:
                w = e.matrix_world @ v.co
                if (w.xy - hp.xy).length < 0.11 and w.z > topz: topz = w.z
            e.to_mesh_clear()
        sink = 0.006 if kind == "bowler" else 0.012
        up = (Mh.to_3x3() @ Vector((0, 1, 0))).normalized()
        h.matrix_world = Matrix.Translation(Vector((hp.x, hp.y, topz - sink))) @ Matrix.Rotation(a.matrix_world.to_euler().z, 4, 'Z') @ Matrix.Scale(1.25 if kind == "bowler" else 1.32, 4)
        c = h.constraints.new('CHILD_OF'); c.target = a; c.subtarget = "head"; c.inverse_matrix = Mh.inverted()
    key_hide(h, [(1, True), (1730, False)])
for src in crowd_src:
    for ch in src.children:
        if ch.type != 'MESH' or ch.name.split(".")[-1] in ("body", "high-poly", "eyebrow001", "eyelashes01", "teeth_base", "tongue01"): continue
        for m in ch.data.materials:
            bs_ = next((n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)
            if not bs_ or not bs_.inputs['Base Color'].links: continue
            s0 = bs_.inputs['Base Color'].links[0].from_socket
            oi = m.node_tree.nodes.new('ShaderNodeObjectInfo'); hs = m.node_tree.nodes.new('ShaderNodeHueSaturation')
            mh = m.node_tree.nodes.new('ShaderNodeMapRange'); mh.inputs['To Min'].default_value = 0.42; mh.inputs['To Max'].default_value = 0.58
            mv = m.node_tree.nodes.new('ShaderNodeMapRange'); mv.inputs['To Min'].default_value = 0.6; mv.inputs['To Max'].default_value = 1.3
            m.node_tree.links.new(oi.outputs['Random'], mh.inputs['Value']); m.node_tree.links.new(oi.outputs['Random'], mv.inputs['Value'])
            m.node_tree.links.new(mh.outputs['Result'], hs.inputs['Hue']); m.node_tree.links.new(mv.outputs['Result'], hs.inputs['Value'])
            m.node_tree.links.new(s0, hs.inputs['Color']); m.node_tree.links.new(hs.outputs['Color'], bs_.inputs['Base Color'])
# --- skin pores / knuckle detail on the prisoner (hero close-ups)
for ch in bpy.data.objects["Prisoner"].children:
    if ch.name.endswith(".body"):
        for m in ch.data.materials:
            for bs_ in [n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED']:
                nzp = m.node_tree.nodes.new('ShaderNodeTexNoise'); nzp.inputs['Scale'].default_value = 450; nzp.inputs['Detail'].default_value = 3
                bp_ = m.node_tree.nodes.new('ShaderNodeBump'); bp_.inputs['Strength'].default_value = 0.12; bp_.inputs['Distance'].default_value = 0.0005
                if bs_.inputs['Normal'].links: m.node_tree.links.new(bs_.inputs['Normal'].links[0].from_socket, bp_.inputs['Normal'])
                m.node_tree.links.new(nzp.outputs['Fac'], bp_.inputs['Height']); m.node_tree.links.new(bp_.outputs['Normal'], bs_.inputs['Normal'])
                bs_.inputs['Roughness'].default_value = max(0.45, bs_.inputs['Roughness'].default_value)
print("DETAILS done")
