"""Diagram set (mouth + forearm, colour-coded, sky gradient) at X=+40 and hospital ward at X=-40; PatientW duplicate.
blender -b work/or.blend --python 04_sets.py -- work/sets.blend"""
import bpy, sys, bmesh, math
from mathutils import Vector, Matrix
HERE = "/home/user/Muhammed/blender/TongueFromArm_v001/"
out = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene
exec(open(HERE + "scripts/lib.py").read())

# ============================================================ DIAGRAM (mouth) at X=+40
DX = Vector((40, 0, 0))
dcol = bpy.data.collections.new("Diagram"); sc.collection.children.link(dcol)
def imp(path, col):
    before = set(bpy.data.objects); bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    for o in new:
        for c in o.users_collection: c.objects.unlink(o)
        col.objects.link(o)
    return new
# teeth + gums -> real mesh objects in metres, mouth centre at DX, front = -Y
new = imp(HERE + "assets/teeth.glb", dcol)
meshes = [o for o in new if o.type == 'MESH']
for o in meshes:
    mw = o.matrix_world.copy(); o.parent = None; o.matrix_world = mw
    o.data.transform(o.matrix_world); o.matrix_world = Matrix.Identity(4)
for o in new:
    if o.type != 'MESH': bpy.data.objects.remove(o)
S_ = 0.0075   # teeth units -> m (arch ~6.5 cm wide)
C0 = Vector((0, -9.0, 19.1))
for o in meshes:
    o.data.transform(Matrix.Translation(-C0)); o.data.transform(Matrix.Scale(S_, 4))
# split into upper / lower by island centroid
def split_lower(o):
    bm = bmesh.new(); bm.from_mesh(o.data); bm.verts.ensure_lookup_table()
    seen = set(); low = []
    for v in bm.verts:
        if v.index in seen: continue
        isl = []; st = [v]; seen.add(v.index)
        while st:
            x = st.pop(); isl.append(x)
            for e in x.link_edges:
                y = e.other_vert(x)
                if y.index not in seen: seen.add(y.index); st.append(y)
        if sum(p.co.z for p in isl) / len(isl) < 0: low += isl
    lowidx = {v.index for v in low}
    print("SPLIT", o.name, len(lowidx), len(bm.verts))
    if len(lowidx) in (0, len(bm.verts)): lowidx = {v.index for v in bm.verts if v.co.z < 0}
    me2 = o.data.copy(); o2 = bpy.data.objects.new(o.name + "_low", me2); dcol.objects.link(o2)
    bm2 = bmesh.new(); bm2.from_mesh(me2); bm2.verts.ensure_lookup_table()
    bmesh.ops.delete(bm2, geom=[v for v in bm2.verts if v.index not in lowidx], context='VERTS'); bm2.to_mesh(me2); bm2.free()
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.index in lowidx], context='VERTS'); bm.to_mesh(o.data); bm.free()
    return o2
gums = next(o for o in meshes if "Gum" in o.name); teeth = next(o for o in meshes if "Teeth" in o.name)
gums.name = "Gums_up"; teeth.name = "Teeth_up"
def bisect_lower(o):
    me2 = o.data.copy(); o2 = bpy.data.objects.new(o.name + "_low", me2); dcol.objects.link(o2)
    for ob, keep_low in ((o, False), (o2, True)):
        bm = bmesh.new(); bm.from_mesh(ob.data)
        bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=(0, 0, 0), plane_no=(0, 0, 1), clear_outer=keep_low, clear_inner=not keep_low)
        bm.to_mesh(ob.data); bm.free()
    return o2
gl = bisect_lower(gums); gl.name = "Gums_low"; tl = split_lower(teeth); tl.name = "Teeth_low"
for o in (gums, teeth, gl, tl):
    o.data.polygons.foreach_set("use_smooth", [True] * len(o.data.polygons))
gm = mat("D_Gum", (0.85, 0.36, 0.40), 0.4); tm = mat("D_Tooth", (0.95, 0.94, 0.90), 0.3)
for o, m in ((gums, gm), (gl, gm), (teeth, tm), (tl, tm)): o.data.materials.clear(); o.data.materials.append(m)
for o in (gums, teeth, gl, tl):
    print("DTEETH", o.name, len(o.data.vertices), bbox(o))
# mouth rig: empty at centre; upper jaw opens about a back hinge
mouth = bpy.data.objects.new("Mouth", None); dcol.objects.link(mouth); mouth.location = DX
hinge = bpy.data.objects.new("UpperHinge", None); dcol.objects.link(hinge); hinge.parent = mouth; hinge.location = (0, 0.045, 0.0)
for o in (gums, teeth):
    o.parent = hinge; o.matrix_parent_inverse = Matrix.Translation(-Vector((0, 0.045, 0)))
for o in (gl, tl): o.parent = mouth
bpy.context.view_layer.update()
# tongue: higher-res object, decimated, scaled into the lower arch; tip -Y
new = imp(HERE + "assets/tongue.glb", dcol)
tms = [o for o in new if o.type == 'MESH']
for o in tms:
    mw = o.matrix_world.copy(); o.parent = None; o.matrix_world = mw; o.data.transform(o.matrix_world); o.matrix_world = Matrix.Identity(4)
for o in new:
    if o not in tms: bpy.data.objects.remove(o)
bm = bmesh.new()
for o in tms: bm.from_mesh(o.data)
T = tms[0]; bm.to_mesh(T.data); bm.free()
for o in tms[1:]: bpy.data.objects.remove(o)
bm = bmesh.new(); bm.from_mesh(T.data); bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.05); bm.to_mesh(T.data); bm.free()
dm = T.modifiers.new("Dec", 'DECIMATE'); dm.ratio = 0.15
bpy.context.view_layer.objects.active = T
with bpy.context.temp_override(object=T, active_object=T): bpy.ops.object.modifier_apply(modifier="Dec")
mn, mx = bbox(T, local=True)
ctr = (mn + mx) / 2; L = mx.y - mn.y; W = mx.x - mn.x; H = mx.z - mn.z
s = 0.054 / L
T.data.transform(Matrix.Diagonal((s * 0.95, s, s * 0.9, 1)) @ Matrix.Translation(-ctr))
sm0 = T.modifiers.new("Sm", 'SMOOTH'); sm0.factor = 0.8; sm0.iterations = 6
with bpy.context.temp_override(object=T, active_object=T): bpy.ops.object.modifier_apply(modifier="Sm")
T.name = "Tongue_full"; T.data.polygons.foreach_set("use_smooth", [True] * len(T.data.polygons))
print("TONGUE dims m", round(W * s, 3), round(L * s, 3), round(H * s, 3))
# place: tongue top just below lower incisal edge; centred in arch
T.parent = mouth; T.location = (0, 0.004, -0.003)
bpy.context.view_layer.update()
tmat = mat("D_Tongue", (0.93, 0.48, 0.52), 0.45)
T.data.materials.clear(); T.data.materials.append(tmat)
# split: back stump (10%) and front piece (90%) along Y in tongue-local coords
mn, mx = bbox(T, local=True); ycut = mx.y - 0.17 * (mx.y - mn.y)
def bisect_copy(src, name, keep_front):
    me = src.data.copy(); o = bpy.data.objects.new(name, me); dcol.objects.link(o); o.parent = src.parent; o.matrix_world = src.matrix_world.copy()
    bm = bmesh.new(); bm.from_mesh(me)
    r = bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=(0, ycut, 0), plane_no=(0, 1, 0),
                               clear_outer=keep_front, clear_inner=not keep_front)
    edges = [e for e in r["geom_cut"] if isinstance(e, bmesh.types.BMEdge)]
    try:
        f = bmesh.ops.holes_fill(bm, edges=edges, sides=0)
        for fc in f["faces"]: fc.material_index = 1
        bmesh.ops.triangulate(bm, faces=f["faces"])
    except Exception as ex: print("FILLFAIL", ex)
    bm.to_mesh(me); bm.free()
    return o
cut_m = mat("D_CutMuscle", (0.80, 0.22, 0.25), 0.4)
front = bisect_copy(T, "Tongue_front", True); stump = bisect_copy(T, "Tongue_stump", False)
for o in (front, stump):
    o.data.materials.append(cut_m)
T.hide_render = True; T.hide_viewport = True
# floor of the mouth under the tongue (closes the view through the lower arch)
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.03, segments=48, ring_count=24)
fl_ = bpy.context.active_object; fl_.name = "MouthFloor"; move_to(fl_, dcol); fl_.parent = mouth
fl_.location = (0, 0.008, -0.0135); fl_.scale = (0.85, 1.25, 0.16); fl_.data.materials.append(gm)
fl_.data.polygons.foreach_set("use_smooth", [True] * len(fl_.data.polygons))
# tumour: purple bumpy blob on the front piece's right side, parented to it
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.007, segments=32, ring_count=16)
tu = bpy.context.active_object; tu.name = "Tumour"; move_to(tu, dcol)
tu.scale = (1.0, 1.25, 0.45)
dsp = tu.modifiers.new("Bumps", 'DISPLACE'); tx = bpy.data.textures.new("TumBumps", 'CLOUDS'); tx.noise_scale = 0.003; dsp.texture = tx; dsp.strength = 0.0025
tu.data.materials.append(mat("D_Tumour", (0.42, 0.12, 0.40), 0.35))
fm, fx = bbox(front)
tu.location = Vector(((fm.x + fx.x) / 2 + 0.010, fm.y + 0.55 * (fx.y - fm.y), fx.z - 0.0045))
tu.parent = front; tu.matrix_parent_inverse = front.matrix_world.inverted()
# FLAP = copy of the front piece (same topology) with a 'Slab' shape key (flat oval muscle slab); muscle -> tongue colour blend
flap = bpy.data.objects.new("Flap", front.data.copy()); dcol.objects.link(flap); flap.parent = mouth; flap.matrix_world = front.matrix_world.copy()
flap.shape_key_add(name="Basis", from_mix=False); sk = flap.shape_key_add(name="Slab", from_mix=False)
mn, mx = bbox(flap, local=True); c = (mn + mx) / 2
for i, v in enumerate(flap.data.vertices):
    p = v.co - c
    sk.data[i].co = c + Vector((p.x * 0.85, p.y * 0.95, p.z * 0.38))
fl = bpy.data.materials.new("D_Flap"); fl.use_nodes = True; nt = fl.node_tree; P = nt.nodes["Principled BSDF"]
mixc = nt.nodes.new("ShaderNodeMix"); mixc.data_type = 'RGBA'; mixc.name = "Pinkify"
wv = nt.nodes.new("ShaderNodeTexWave"); wv.wave_type = 'BANDS'; wv.bands_direction = 'Y'; wv.inputs["Scale"].default_value = 180; wv.inputs["Distortion"].default_value = 2
tcn = nt.nodes.new("ShaderNodeTexCoord"); nt.links.new(tcn.outputs["Object"], wv.inputs["Vector"])
mus = nt.nodes.new("ShaderNodeMix"); mus.data_type = 'RGBA'; mus.inputs[6].default_value = (0.72, 0.13, 0.16, 1); mus.inputs[7].default_value = (0.90, 0.30, 0.32, 1)
fac = nt.nodes.new("ShaderNodeMath"); fac.operation = 'MULTIPLY'; fac.inputs[1].default_value = 0.6
nt.links.new(wv.outputs["Fac"], fac.inputs[0]); nt.links.new(fac.outputs[0], mus.inputs[0])
nt.links.new(mus.outputs[2], mixc.inputs[6]); mixc.inputs[7].default_value = (0.90, 0.47, 0.50, 1); mixc.inputs[0].default_value = 0.0
nt.links.new(mixc.outputs[2], P.inputs["Base Color"]); P.inputs["Roughness"].default_value = 0.4
flap.data.materials.clear(); flap.data.materials.append(fl); flap.data.materials.append(fl)
# neck vessels + nerve coming up behind the stump (stubs that the flap's vessels connect to)
sm, sx = bbox(stump)
back = Vector((0, sx.y + 0.002, (sm.z + sx.z) / 2))
if back.x < 1: back += DX
VES = {}
for nm, col_, dx, r in (("Artery", (0.85, 0.08, 0.10), 0.010, 0.0016), ("Vein", (0.12, 0.25, 0.85), -0.010, 0.0019), ("Nerve", (0.98, 0.82, 0.15), 0.0, 0.0010)):
    m_ = mat("D_" + nm, col_, 0.3)
    pts = [back + Vector((dx, 0.004, -0.004)), back + Vector((dx * 1.4, 0.012, -0.016)), back + Vector((dx * 1.6, 0.018, -0.040))]
    VES["Neck" + nm] = tube("Neck" + nm, [p for p in pts], r, m_, dcol)
# flap vessels: from the flap's back-underside forward under the stump to the neck stubs (grow with bevel_factor_end)
fm2, fx2 = bbox(front)
for nm, dx, r in (("Artery", 0.010, 0.0016), ("Vein", -0.010, 0.0019), ("Nerve", 0.0, 0.0010)):
    a0 = Vector(((fm2.x + fx2.x) / 2 + dx * 0.6, fx2.y - 0.004, fm2.z + 0.003))
    pts = [a0, a0 + Vector((0, 0.006, -0.004)), back + Vector((dx, -0.002, -0.006)) + Vector((0, 0, 0)), back + Vector((dx, 0.004, -0.004))]
    o = tube("Join" + nm, [p for p in pts], r, bpy.data.materials["D_" + nm], dcol)
    o.data.bevel_factor_end = 1.0
# stitch rings at the three junctions
for i, (nm, dx) in enumerate((("Artery", 0.010), ("Vein", -0.010), ("Nerve", 0.0))):
    bpy.ops.mesh.primitive_torus_add(major_radius=0.0024 if nm != "Nerve" else 0.0015, minor_radius=0.00035, major_segments=24, minor_segments=8)
    t = bpy.context.active_object; t.name = "Stitch" + nm; move_to(t, dcol)
    t.location = back + Vector((dx, 0.004, -0.004)); t.rotation_euler = (math.radians(90), 0, 0)
    t.data.materials.append(mat("D_Stitch", (0.15, 0.20, 0.55), 0.3))
# ============================================================ DIAGRAM (forearm) at X=+40, Y=+3 (separate framing)
AX = Vector((40, 3.0, 0))
rig = bpy.data.objects["Patient"]; B = bpy.data.objects["Patient.body"]
dg = bpy.context.evaluated_depsgraph_get()
# rest-pose skin copy of the right forearm + hand
me = B.data.copy(); fa = bpy.data.objects.new("D_Forearm", me); dcol.objects.link(fa)
for kb in (me.shape_keys.key_blocks if me.shape_keys else []): pass
if me.shape_keys:
    fa.active_shape_key_index = 0
    keys = list(me.shape_keys.key_blocks)
    for kb in keys[::-1]: fa.shape_key_remove(kb)
bones = {b.name for b in rig.data.bones}; gi = {g.index: g.name for g in B.vertex_groups}
bm = bmesh.new(); bm.from_mesh(me); dl = bm.verts.layers.deform.active; kill = []
for v in bm.verts:
    ws = {gi[k]: w for k, w in v[dl].items()}
    if any(ws.get(h, 0) > 0 for h in ("HelperGeometry", "JointCubes")) or "body" not in ws: kill.append(v); continue
    bw = {k: w for k, w in ws.items() if k in bones}
    if not bw: kill.append(v); continue
    d = max(bw, key=bw.get)
    if not (d.endswith(".R") and d.startswith(("lowerarm", "wrist", "finger", "metacarpal"))): kill.append(v)
bmesh.ops.delete(bm, geom=kill, context='VERTS'); bm.to_mesh(me); bm.free()
fa.vertex_groups.clear()
fa.data.materials.clear(); fa.data.materials.append(B.data.materials[0])
fa.modifiers.new("Sub", 'SUBSURF').levels = 1
# orient: forearm axis (elbow->wrist) along +X, palm up, centred at AX
el = rig.data.bones["lowerarm01.R"].head_local; wr = rig.data.bones["wrist.R"].head_local
ax = (wr - el).normalized()
Rm = ax.to_track_quat('X', 'Z').to_matrix().to_4x4()
fa.data.transform(Matrix.Translation(-(el + wr) / 2)); fa.data.transform(Rm.inverted())
fa.location = AX
bpy.context.view_layer.update()
print("FOREARM", bbox(fa))
sm_ = fa.modifiers["Sub"]; sm_.levels = 2
with bpy.context.temp_override(object=fa, active_object=fa): bpy.ops.object.modifier_apply(modifier="Sub")
fa.modifiers.new("Sub", 'SUBSURF').levels = 1
# window on the up-facing middle of the forearm: oval patch -> cup (muscle bed) + ArmFlap (red muscle slab that lifts out)
me = fa.data; bm = bmesh.new(); bm.from_mesh(me); bm.normal_update()
xs = [v.co.x for v in bm.verts]; zs = [v.co.z for v in bm.verts]
x0 = -0.03; RX, RY = 0.045, 0.016
cy = sum(v.co.y for v in bm.verts if abs(v.co.x - x0) < 0.02) / max(1, len([v for v in bm.verts if abs(v.co.x - x0) < 0.02]))
sel = [f for f in bm.faces if f.normal.z > 0.35 and ((f.calc_center_median().x - x0) / RX) ** 2 + ((f.calc_center_median().y - cy) / RY) ** 2 < 1]
print("WINDOW faces", len(sel))
patch = bm.copy(); 
selidx = {f.index for f in sel}
bmesh.ops.delete(patch, geom=[f for f in patch.faces if f.index not in selidx], context='FACES')
bmesh.ops.delete(bm, geom=sel, context='FACES_ONLY') if False else bmesh.ops.delete(bm, geom=sel, context='FACES')
bm.to_mesh(me); bm.free()
fa.data.materials.append(mat("D_Bed", (0.62, 0.12, 0.15), 0.45))
# cup: patch extruded down 9 mm, top removed
cm = bpy.data.meshes.new("D_ArmCup"); patch.to_mesh(cm)
cup = bpy.data.objects.new("D_ArmCup", cm); dcol.objects.link(cup); cup.location = fa.location
b2 = bmesh.new(); b2.from_mesh(cm)
top = b2.faces[:]
r = bmesh.ops.extrude_face_region(b2, geom=top)
nv = [e for e in r["geom"] if isinstance(e, bmesh.types.BMVert)]
for v in nv: v.co.z -= 0.009
bmesh.ops.delete(b2, geom=top, context='FACES')
bmesh.ops.reverse_faces(b2, faces=b2.faces[:])
b2.to_mesh(cm); b2.free(); cm.materials.append(mat("D_Bed", (0.62, 0.12, 0.15), 0.45))
# arm flap: patch solidified 8 mm downward, muscle with fibres
fm_ = bpy.data.meshes.new("ArmFlap"); patch.to_mesh(fm_); patch.free()
af = bpy.data.objects.new("ArmFlap", fm_); dcol.objects.link(af); af.location = fa.location
so = af.modifiers.new("Thick", 'SOLIDIFY'); so.thickness = 0.008; so.offset = -1; so.use_even_offset = True
af.modifiers.new("Sub", 'SUBSURF').levels = 2
fm_.materials.append(bpy.data.materials["D_Flap"])
for o in (cup, af): o.data.polygons.foreach_set("use_smooth", [True] * len(o.data.polygons))
fa["window_c"] = (x0, cy)
# flap vessels: three short strands from the flap underside into the bed (hooked in the animation)
for nm, dy, r in (("Artery", 0.006, 0.0018), ("Vein", -0.006, 0.0021), ("Nerve", 0.0, 0.0012)):
    p0 = fa.location + Vector((x0 + RX * 0.85, cy + dy, -0.004)); p1 = p0 + Vector((0.03, 0, -0.004))
    tube("ArmVes" + nm, [p0, (p0 + p1) / 2, p1], r, bpy.data.materials["D_" + nm], dcol)
for o in ("Flap",): bpy.data.objects[o].hide_render = True; bpy.data.objects[o].hide_viewport = True

# ============================================================ WARD at X=-40
W0 = Vector((-40, 0, 0))
wcol = bpy.data.collections.new("Ward"); sc.collection.children.link(wcol)
def box(name, loc, dims, m, col=wcol):
    bpy.ops.mesh.primitive_cube_add(size=1); o = bpy.context.active_object; o.name = name; move_to(o, col)
    o.location = W0 + Vector(loc); o.scale = dims; o.data.materials.append(m)
    bv = o.modifiers.new("Bev", 'BEVEL'); bv.width = min(0.01, min(dims) * 0.3); bv.segments = 2
    return o
wall = mat("W_Wall", (0.78, 0.88, 0.95), 0.8); wall2 = mat("W_WallAccent", (0.36, 0.62, 0.86), 0.7)
floor = mat("W_Floor", (0.80, 0.80, 0.78), 0.5); white = mat("W_White", (0.92, 0.93, 0.94), 0.4); wood = mat("W_Wood", (0.62, 0.45, 0.30), 0.5)
box("W_Floor", (-0.8, 0, -0.05), (7.6, 7, 0.1), floor); box("W_Ceil", (0, 0, 2.85), (6, 7, 0.1), white)
box("W_WallBack", (0, 1.55, 1.4), (6, 0.1, 2.9), wall); box("W_WallAccent", (0, 1.49, 0.55), (6, 0.02, 1.1), wall2)
box("W_WallFront", (0, -3.3, 1.4), (6, 0.1, 2.9), wall)
box("W_WallRight", (2.6, 0, 1.4), (0.1, 7, 2.9), wall)
# left wall with door opening (y -2.4..-1.4) 
box("W_WallL1", (-2.3, 0.45, 1.4), (0.1, 2.3, 2.9), wall); box("W_WallL2", (-2.3, -2.85, 1.4), (0.1, 0.9, 2.9), wall)
box("W_WallL3", (-2.3, -1.9, 2.45), (0.1, 1.0, 0.8), wall)
box("W_DoorFrameA", (-2.27, -1.38, 1.0), (0.14, 0.06, 2.1), white); box("W_DoorFrameB", (-2.27, -2.42, 1.0), (0.14, 0.06, 2.1), white)
box("W_Corridor", (-3.6, -1.9, 1.4), (0.1, 3, 2.9), wall); 
# window on the right wall: frame + bright sky panel behind (no black void)
box("W_WinFrame", (2.54, 0.2, 1.55), (0.06, 1.5, 1.2), white)
box("W_WinSky", (2.5, 0.2, 1.55), (0.02, 1.36, 1.06), mat("W_Sky", (0.55, 0.80, 0.98), 0.5, emit=1.2))
box("W_WinBar", (2.47, 0.2, 1.55), (0.03, 0.04, 1.06), white)
# bed (CC-BY model), head against the back wall
before = set(bpy.data.objects); bpy.ops.import_scene.gltf(filepath=HERE + "assets/bed.glb")
bed_objs = [o for o in bpy.data.objects if o not in before]
root = bpy.data.objects.new("W_Bed", None); wcol.objects.link(root)
for o in bed_objs:
    move_to(o, wcol)
    if o.parent is None: o.parent = root
bpy.context.view_layer.update()
bb = [o.matrix_world @ Vector(c) for o in bed_objs if o.type == 'MESH' for c in o.bound_box]
mn = Vector([min(v[i] for v in bb) for i in range(3)]); mx = Vector([max(v[i] for v in bb) for i in range(3)])
print("BED raw", mn, mx)
L = mx.y - mn.y; sB = 2.15 / L
root.scale = (sB, sB, sB); root.location = W0 + Vector((0, 1.45 - 2.15 / 2, 0)) - Vector(((mn.x + mx.x) / 2, (mn.y + mx.y) / 2, mn.z)) * sB
bpy.context.view_layer.update()
bm_ = mat("W_BedFrame", (0.90, 0.91, 0.93), 0.35); sheet = mat("W_Sheet", (0.96, 0.97, 0.98), 0.8)
for o in bed_objs:
    if o.type == 'MESH':
        o.data.materials.clear(); o.data.materials.append(bm_)
# mattress top by ray cast
dg = bpy.context.evaluated_depsgraph_get()
hit, loc, nrm, idx, ob, M = sc.ray_cast(dg, W0 + Vector((0, 0.2, 2.0)), Vector((0, 0, -1)))
MZ = loc.z if hit else 0.6
print("MATTRESS", MZ, ob.name if hit else None)
# sheet over mattress, pillow wedge, blanket over the legs
box("W_MattressSheet", (0, 0.35, MZ - W0.z + 0.0), (0.92, 2.0, 0.02), sheet)
pw = box("W_Pillow", (0, 1.15, MZ + 0.28), (0.7, 0.22, 0.55), sheet); pw.rotation_euler = (math.radians(-20), 0, 0)
pw.modifiers["Bev"].width = 0.08; pw.modifiers["Bev"].segments = 4
bl = box("W_Blanket", (0, -0.2, MZ + 0.14), (0.98, 1.35, 0.26), mat("W_BlanketM", (0.55, 0.75, 0.92), 0.8))
bl.modifiers["Bev"].width = 0.06; bl.modifiers["Bev"].segments = 4
# bedside table + cup, monitor on a stand, IV pole
box("W_Table", (0.85, 0.95, 0.35), (0.45, 0.45, 0.7), wood); box("W_TableTop", (0.85, 0.95, 0.71), (0.5, 0.5, 0.03), white)
box("W_MonStand", (1.55, 1.25, 0.6), (0.06, 0.06, 1.2), white); box("W_Mon", (1.55, 1.18, 1.35), (0.45, 0.06, 0.32), mat("W_MonBody", (0.25, 0.28, 0.32), 0.4))
box("W_MonScreen", (1.55, 1.145, 1.35), (0.40, 0.01, 0.26), mat("W_MonScr", (0.05, 0.25, 0.20), 0.3, emit=0.8))
# logo poster on the back wall (flat-on, dark logo on a white board)
pb_ = box("W_Poster", (1.05, 1.47, 1.75), (0.95, 0.03, 0.55), white)
img = bpy.data.images.load("/home/user/Muhammed/blender/assets/brand/DaKrasFilms_logo_dark.png"); img.pack()
lm = bpy.data.materials.new("W_Logo"); lm.use_nodes = True; nt = lm.node_tree; P = nt.nodes["Principled BSDF"]
ti = nt.nodes.new("ShaderNodeTexImage"); ti.image = img; ti.extension = 'CLIP'
nt.links.new(ti.outputs["Color"], P.inputs["Base Color"]); nt.links.new(ti.outputs["Alpha"], P.inputs["Alpha"]); P.inputs["Roughness"].default_value = 0.6
lm.blend_method = 'BLEND' if hasattr(lm, "blend_method") else None
bpy.ops.mesh.primitive_plane_add(size=1); lg = bpy.context.active_object; lg.name = "W_LogoDecal"; move_to(lg, wcol)
lg.scale = (0.85, 0.85 * 414 / 967, 1); lg.rotation_euler = (math.radians(90), 0, 0); lg.location = W0 + Vector((1.05, 1.453, 1.75))
lg.data.materials.append(lm)
# ceiling light panel
box("W_CeilLight", (0, 0, 2.79), (1.2, 0.6, 0.02), mat("W_Panel", (1, 1, 1), 0.5, emit=3.0))
for o in wcol.objects:
    if o.type == 'MESH': o.data.polygons.foreach_set("use_smooth", [False] * len(o.data.polygons))
sc["MZ"] = MZ
bpy.ops.wm.save_as_mainfile(filepath=out, compress=True)
