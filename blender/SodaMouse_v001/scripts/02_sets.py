"""Sets + props. Kitchen (origin) and lab (x=30). Reads build/chars.blend, writes build/sets.blend.
blender -b build/chars.blend --python 02_sets.py"""
import bpy, bmesh, math, os, random
from mathutils import Vector, Matrix
exec(open(os.path.dirname(__file__) + "/common.py").read())
R = math.radians
sc = bpy.context.scene

def coll(name):
    c = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if c.name not in sc.collection.children: sc.collection.children.link(c)
    return c

def put(ob, c):
    for u in list(ob.users_collection): u.objects.unlink(ob)
    c.objects.link(ob)

def mat(name, col, rough=0.5, metal=0.0, trans=0.0, ior=1.45, sss=0.0, alpha=1.0, emit=None):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name); m.use_nodes = True
    P = m.node_tree.nodes["Principled BSDF"]
    P.inputs["Base Color"].default_value = (*col, 1); P.inputs["Roughness"].default_value = rough
    P.inputs["Metallic"].default_value = metal; P.inputs["Transmission Weight"].default_value = trans; P.inputs["IOR"].default_value = ior
    if sss: P.inputs["Subsurface Weight"].default_value = sss; P.inputs["Subsurface Radius"].default_value = (0.3, 0.6, 0.2)
    P.inputs["Alpha"].default_value = alpha
    return m

def lathe(name, prof, seg=64, uv=True, cap_top=False, cap_bot=False):
    """prof: list of (r, z) bottom->top; returns mesh object (smooth)"""
    bm = bmesh.new(); rings = []
    for i, (r, z) in enumerate(prof):
        ring = [bm.verts.new((r * math.cos(2 * math.pi * k / seg), r * math.sin(2 * math.pi * k / seg), z)) for k in range(seg)]
        rings.append(ring)
    uvl = bm.loops.layers.uv.new("UVMap")
    zs = [p[1] for p in prof]; z0, z1 = min(zs), max(zs)
    for i in range(len(rings) - 1):
        for k in range(seg):
            a, b = rings[i][k], rings[i][(k + 1) % seg]; c, d = rings[i + 1][(k + 1) % seg], rings[i + 1][k]
            f = bm.faces.new((a, b, c, d))
            for lp, (u, v) in zip(f.loops, ((k, i), (k + 1, i), (k + 1, i + 1), (k, i + 1))):
                lp[uvl].uv = (u / seg, (prof[v][1] - z0) / max(1e-6, z1 - z0))
    if cap_bot: bm.faces.new(list(reversed(rings[0])))
    if cap_top: bm.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = True
    ob = bpy.data.objects.new(name, me); sc.collection.objects.link(ob)
    return ob

def append_blend(path, cname, loc, scale=1.0, rot=0.0, skip=()):
    with bpy.data.libraries.load(path) as (fd, td): td.objects = [n for n in fd.objects if not any(s in n for s in skip)]
    c = coll(cname); obs = []
    for o in td.objects:
        if o is None: continue
        c.objects.link(o); obs.append(o)
    for o in obs:
        if o.parent is None:
            o.location = Vector(loc) + Matrix.Rotation(rot, 3, 'Z') @ (o.location * scale)
            o.rotation_euler.z += rot; o.scale = o.scale * scale
    return obs

def import_glb(path, cname, loc, scale, rot=0.0):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    root = bpy.data.objects.new(cname + "_root", None); coll(cname).objects.link(root)
    for o in new:
        put(o, coll(cname))
        if o.parent is None: o.parent = root
    root.location = loc; root.scale = (scale,) * 3; root.rotation_euler.z = rot
    return root, new

# ===================================================================== KITCHEN (origin)
K = coll("SET_Kitchen")
kroot, knew = import_glb(SCR + "/models/kitchen.glb", "SET_Kitchen", (0, 1.75, 0), 0.0254)
tab = append_blend(SCR + "/ph/dining_table/dining_table_1k.blend", "SET_Kitchen", (0, -0.38, 0), skip=("cloth",))
for o in tab: o.name = "KitchenTable" if o.type == 'MESH' else o.name
TABLE_Z = 0.79
# big floor + side walls so wide shots never see void
bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, 0.0)); fl = bpy.context.active_object; fl.name = "KitchenFloor"
fl.scale = (8, 9, 1); put(fl, K); fl.data.materials.append(mat("KitchenFloorWood", (0.62, 0.45, 0.3), 0.45))
for nm, loc, rot, sz in (("KitchenWallL", (-2.0, 0, 1.5), (R(90), 0, R(90)), (9, 3, 1)), ("KitchenWallR", (2.0, 0, 1.5), (R(90), 0, R(90)), (9, 3, 1)),
                         ("KitchenWallBack", (0, -4.2, 1.5), (R(90), 0, 0), (4.2, 3, 1))):
    bpy.ops.mesh.primitive_plane_add(size=1, location=loc, rotation=rot); w = bpy.context.active_object; w.name = nm; w.scale = sz; put(w, K)
    w.data.materials.append(mat("KitchenWallPaint", (0.93, 0.9, 0.84), 0.8))
bpy.data.objects["KitchenWallBack"].hide_render = True   # behind the cameras; only for bounce-free safety
bpy.data.objects["KitchenWallBack"].hide_viewport = True

# ===================================================================== LAB (x = 30)
LX = 30.0
L = coll("SET_Lab")
lroot, lnew = import_glb(SCR + "/models/labbench.glb", "SET_Lab", (LX, 1.55, 0.51), 1.0)
bpy.ops.mesh.primitive_plane_add(size=1, location=(LX, 0, 0)); fl = bpy.context.active_object; fl.name = "LabFloor"; fl.scale = (10, 10, 1); put(fl, L)
fl.data.materials.append(mat("LabFloor", (0.78, 0.82, 0.86), 0.35))
tile = mat("LabTile", (0.92, 0.95, 0.97), 0.3)
nt = tile.node_tree; br = nt.nodes.new("ShaderNodeTexBrick"); br.inputs["Scale"].default_value = 9.0
br.inputs["Color1"].default_value = (0.93, 0.96, 0.98, 1); br.inputs["Color2"].default_value = (0.88, 0.93, 0.97, 1)
br.inputs["Mortar"].default_value = (0.75, 0.8, 0.85, 1); br.inputs["Mortar Size"].default_value = 0.012; br.offset = 0.0
tc = nt.nodes.new("ShaderNodeTexCoord"); nt.links.new(tc.outputs["UV"], br.inputs["Vector"])
nt.links.new(br.outputs["Color"], nt.nodes["Principled BSDF"].inputs["Base Color"])
for nm, loc, rot, sz in (("LabWallBack", (LX, 2.1, 1.6), (R(90), 0, 0), (8, 3.2, 1)), ("LabWallL", (LX - 3.2, 0, 1.6), (R(90), 0, R(90)), (8, 3.2, 1)),
                         ("LabWallR", (LX + 3.2, 0, 1.6), (R(90), 0, R(90)), (8, 3.2, 1))):
    bpy.ops.mesh.primitive_plane_add(size=1, location=loc, rotation=rot); w = bpy.context.active_object; w.name = nm; w.scale = sz; put(w, L)
    w.data.materials.append(tile)
# stainless worktable (top 1.6 x 0.8, height 0.92) in front of the scientist
steel = mat("Steel", (0.78, 0.8, 0.83), 0.28, metal=1.0)
LT_Z = 0.92
def box(name, loc, dims, m, bev=0.006):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc); b = bpy.context.active_object; b.name = name; b.scale = dims
    bpy.ops.object.transform_apply(scale=True)
    bv = b.modifiers.new("bev", 'BEVEL'); bv.width = bev; bv.segments = 3; bv.limit_method = 'ANGLE'
    b.data.materials.append(m); put(b, L); return b
box("LabTableTop", (LX, -0.38, LT_Z - 0.02), (1.6, 0.8, 0.04), steel, 0.012)
box("LabTableShelf", (LX, -0.38, 0.18), (1.5, 0.7, 0.025), steel)
for sx in (-0.76, 0.76):
    for sy in (-0.74, -0.02):
        box("LabTableLeg", (LX + sx, sy, (LT_Z - 0.04) / 2), (0.04, 0.04, LT_Z - 0.04), steel, 0.004)
# a few lab props for life on the back bench come with the glb; a wall clock-free poster stays blank

# ===================================================================== PROPS
P = coll("PROPS")
# --- soda can (12 oz: h 0.122, d 0.066), generic green label, no brand
cr = 0.033
prof = [(0.0, 0.0), (0.020, 0.0015), (0.027, 0.006), (0.031, 0.002), (cr, 0.008), (cr, 0.100), (0.029, 0.112), (0.0265, 0.1185), (0.027, 0.1215), (0.0255, 0.122)]
can = lathe("SodaCan", prof)
labelimg = bpy.data.images.load(SCR + "/tex/can_label.png"); labelimg.name = "can_label"
cm = bpy.data.materials.new("CanBody"); cm.use_nodes = True; nt = cm.node_tree; Pn = nt.nodes["Principled BSDF"]
ti = nt.nodes.new("ShaderNodeTexImage"); ti.image = labelimg
# label only on the straight wall (uv.y between 0.07 and 0.82), silver elsewhere
sep = nt.nodes.new("ShaderNodeSeparateXYZ"); tcn = nt.nodes.new("ShaderNodeTexCoord"); nt.links.new(tcn.outputs["UV"], sep.inputs[0])
mp = nt.nodes.new("ShaderNodeMapRange"); nt.links.new(sep.outputs["Y"], mp.inputs[0]); mp.inputs[1].default_value = 0.07; mp.inputs[2].default_value = 0.82
mpv = nt.nodes.new("ShaderNodeCombineXYZ"); nt.links.new(sep.outputs["X"], mpv.inputs[0]); nt.links.new(mp.outputs[0], mpv.inputs[1]); nt.links.new(mpv.outputs[0], ti.inputs[0])
inband = nt.nodes.new("ShaderNodeMath"); inband.operation = 'COMPARE'; inband.inputs[1].default_value = 0.445; inband.inputs[2].default_value = 0.375
nt.links.new(sep.outputs["Y"], inband.inputs[0])
mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = 'RGBA'; mx.inputs["A"].default_value = (0.8, 0.82, 0.84, 1)
nt.links.new(inband.outputs[0], mx.inputs["Factor"]); nt.links.new(ti.outputs["Color"], mx.inputs["B"]); nt.links.new(mx.outputs["Result"], Pn.inputs["Base Color"])
mr = nt.nodes.new("ShaderNodeMapRange"); mr.inputs[3].default_value = 1.0; mr.inputs[4].default_value = 0.35
nt.links.new(inband.outputs[0], mr.inputs[0]); nt.links.new(mr.outputs[0], Pn.inputs["Metallic"])
Pn.inputs["Roughness"].default_value = 0.3; Pn.inputs["Coat Weight"].default_value = 0.4
can.data.materials.append(cm); put(can, P)
# lid with the drinking opening (opened) and a pull tab
bm = bmesh.new()
bmesh.ops.create_circle(bm, cap_ends=True, radius=0.0262, segments=64)
me = bpy.data.meshes.new("CanLid"); bm.to_mesh(me); bm.free()
lid = bpy.data.objects.new("CanLid", me); sc.collection.objects.link(lid); put(lid, P); lid.location = (0, 0, 0.1205)
lid.data.materials.append(mat("CanLidAlu", (0.82, 0.83, 0.85), 0.25, metal=1.0))
# opening: dark recess shape near the rim (+Y side)
bm = bmesh.new(); bmesh.ops.create_circle(bm, cap_ends=True, radius=1.0, segments=32)
for v in bm.verts: v.co.x *= 0.0105; v.co.y = v.co.y * 0.0072
me = bpy.data.meshes.new("CanOpening"); bm.to_mesh(me); bm.free()
op = bpy.data.objects.new("CanOpening", me); sc.collection.objects.link(op); put(op, P); op.parent = can; op.location = (0, 0.0145, 0.1209)
op.data.materials.append(mat("CanOpeningDark", (0.02, 0.05, 0.02), 0.2))
lid.parent = can
bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=0.0085, depth=0.0012, location=(0, -0.004, 0.1218))
tab_ = bpy.context.active_object; tab_.name = "CanTab"; tab_.scale = (0.75, 1.5, 1); put(tab_, P); tab_.parent = can
tab_.data.materials.append(bpy.data.materials["CanLidAlu"])
# green soda just under the opening (visible in the top macro)
bpy.ops.mesh.primitive_circle_add(vertices=32, radius=1, fill_type='NGON', location=(0, 0.0145, 0.1175))
sod = bpy.context.active_object; sod.name = "CanSodaSurface"; sod.scale = (0.0102, 0.007, 1); put(sod, P); sod.parent = can
soda = mat("Soda", (0.45, 0.85, 0.12), 0.05, trans=0.0, ior=1.33)
sod.data.materials.append(soda)
can.location = (0.0, 0.0, 0.0)

# --- mouse tail tip (pink curve) curling out of the opening (S03)
cu = bpy.data.curves.new("TailTip", 'CURVE'); cu.dimensions = '3D'; sp = cu.splines.new('BEZIER'); pts = [(0, 0.0145, 0.112), (0.001, 0.016, 0.125), (0.006, 0.022, 0.131), (0.011, 0.027, 0.126)]
sp.bezier_points.add(len(pts) - 1)
for bp, p in zip(sp.bezier_points, pts): bp.co = p; bp.handle_left_type = bp.handle_right_type = 'AUTO'
cu.bevel_depth = 0.0017; cu.bevel_resolution = 3; cu.use_fill_caps = True
tp = cu.splines[0].bezier_points
for i, bp in enumerate(tp): bp.radius = 1.0 - 0.6 * i / (len(tp) - 1)
tail = bpy.data.objects.new("MouseTailTip", cu); sc.collection.objects.link(tail); put(tail, P); tail.parent = can
tail.data.materials.append(mat("MouseTailPink", (0.9, 0.5, 0.55), 0.5, sss=0.2))
tail.hide_render = tail.hide_viewport = True     # only shown in the can-opening macro

# --- mouse (Sketchfab "Rat (Test) Free", CC-BY), ~0.085 m body, lying on its side (dead)
before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=SCR + "/models/mouse.glb")
mnew = [o for o in bpy.data.objects if o not in before]
src = next(o for o in mnew if o.type == 'MESH' and any(m.type == 'ARMATURE' for m in o.modifiers))
dg = bpy.context.evaluated_depsgraph_get()
me = bpy.data.meshes.new_from_object(src.evaluated_get(dg)); me.transform(src.matrix_world)
for o in mnew: bpy.data.objects.remove(o, do_unlink=True)
mouse = bpy.data.objects.new("Mouse", me); sc.collection.objects.link(mouse)
dd = [max(v.co[i] for v in me.vertices) - min(v.co[i] for v in me.vertices) for i in range(3)]
print("MOUSE raw dims", [round(x, 3) for x in dd])
ax = dd.index(max(dd))
if ax == 0: me.transform(Matrix.Rotation(R(90), 4, 'Z'))
elif ax == 2: me.transform(Matrix.Rotation(R(-90), 4, 'X'))
bb = [Vector(c) for c in mouse.bound_box]; lo = Vector([min(v[i] for v in bb) for i in range(3)]); hi = Vector([max(v[i] for v in bb) for i in range(3)])
L_ = max(hi - lo); mouse.data.transform(Matrix.Translation(-(lo + hi) / 2)); s = 0.15 / L_
mouse.data.transform(Matrix.Scale(s, 4)); mouse.data.update(); put(mouse, P)
print("MOUSE dims", [round(d, 3) for d in mouse.dimensions])
for m_ in mouse.data.materials:
    if m_ and m_.use_nodes:
        Pn = m_.node_tree.nodes.get("Principled BSDF")
        if Pn: Pn.inputs["Roughness"].default_value = max(0.45, Pn.inputs["Roughness"].default_value)

# --- plate (kitchen)
plate = lathe("Plate", [(0.0, 0.0), (0.07, 0.0), (0.075, 0.004), (0.1, 0.012), (0.125, 0.022), (0.128, 0.024), (0.124, 0.025), (0.098, 0.016), (0.07, 0.010), (0.0, 0.010)])
plate.data.materials.append(mat("Ceramic", (0.95, 0.95, 0.93), 0.2)); put(plate, P)
# --- green puddle (spilt soda on the plate)
bpy.ops.mesh.primitive_circle_add(vertices=48, radius=1, fill_type='NGON'); pud = bpy.context.active_object; pud.name = "SodaPuddle"
for v in pud.data.vertices:
    a = math.atan2(v.co.y, v.co.x); rr = 1 + 0.12 * math.sin(3 * a) + 0.07 * math.sin(5 * a + 1)
    v.co.x *= rr; v.co.y *= rr * 0.8
pud.scale = (0.075, 0.075, 1); put(pud, P); pud.data.materials.append(soda)

# --- beaker (lab, 1 L, wide mouth so the mouse fits): glass shell + liquid
bk = [(0.0, 0.0), (0.05, 0.0), (0.054, 0.003), (0.055, 0.17), (0.058, 0.176), (0.0545, 0.176), (0.0515, 0.17), (0.0515, 0.004), (0.0, 0.004)]
beaker = lathe("Beaker", bk, seg=64)
beaker.data.materials.append(mat("LabGlass", (0.95, 0.98, 1.0), 0.02, trans=1.0, ior=1.45)); put(beaker, P)
liq = lathe("BeakerLiquid", [(0.0, 0.0045), (0.0508, 0.0045), (0.0508, 0.11), (0.0, 0.11)], seg=48, cap_top=False)
bmh = bmesh.new(); bmh.from_mesh(liq.data); bmesh.ops.contextual_create(bmh, geom=[v for v in bmh.verts if abs(v.co.z - 0.11) < 1e-5]); bmh.to_mesh(liq.data); bmh.free()
liq.data.materials.append(mat("SodaLiquid", (0.42, 0.88, 0.1), 0.05, trans=0.85, ior=1.33)); put(liq, P); liq.parent = beaker

# --- jelly blob (dissolved mouse), soft green, subsurface
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=5, radius=1); jel = bpy.context.active_object; jel.name = "Jelly"
random.seed(4)
for v in jel.data.vertices:
    n = v.co.normalized(); d = 1 + 0.10 * math.sin(3 * n.x + 1) * math.sin(4 * n.y) + 0.06 * math.sin(6 * n.z + 2)
    v.co = n * d
    if v.co.z < -0.25: v.co.z = -0.25 - (v.co.z + 0.25) * 0.15
for p in jel.data.polygons: p.use_smooth = True
jel.scale = (0.055, 0.045, 0.026); put(jel, P)
bpy.context.view_layer.objects.active = jel; bpy.ops.object.select_all(action='DESELECT'); jel.select_set(True); bpy.ops.object.transform_apply(scale=True)
jel.data.materials.append(mat("JellyGreen", (0.35, 0.82, 0.12), 0.12, trans=0.35, ior=1.36, sss=0.35))

# --- steel tray (lab), lab spatula (flat blade, long handle)
tray = lathe("Tray", [(0.0, 0.0), (0.16, 0.0), (0.17, 0.018), (0.175, 0.02), (0.166, 0.02), (0.157, 0.004), (0.0, 0.004)], seg=64)
tray.scale = (1.0, 0.7, 1.0); tray.data.materials.append(steel); put(tray, P)
bm = bmesh.new()
blade = bmesh.ops.create_cube(bm, size=1)["verts"]
for v in blade: v.co.x *= 0.11; v.co.y *= 0.045; v.co.z *= 0.002; v.co.x += 0.055 + 0.0
hd = bmesh.ops.create_cone(bm, cap_ends=True, segments=16, radius1=0.006, radius2=0.006, depth=0.2)["verts"]
for v in hd: v.co = Matrix.Rotation(R(90), 3, 'Y') @ v.co; v.co.x -= 0.1
me = bpy.data.meshes.new("Spatula"); bm.to_mesh(me); bm.free()
spat = bpy.data.objects.new("Spatula", me); sc.collection.objects.link(spat); put(spat, P)
spat.data.materials.append(steel)
bv = spat.modifiers.new("bev", 'BEVEL'); bv.width = 0.0015; bv.segments = 2

# --- fizz bubbles (keyed later): a handful of tiny spheres parented to the beaker
bub = mat("Bubble", (0.9, 1.0, 0.85), 0.02, trans=1.0, ior=1.1)
for i in range(14):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=10, ring_count=6, radius=0.0022 + 0.0016 * random.random())
    b = bpy.context.active_object; b.name = "Bubble.%02d" % i; put(b, P); b.parent = beaker
    b.location = (random.uniform(-0.035, 0.035), random.uniform(-0.035, 0.035), random.uniform(0.01, 0.1)); b.data.materials.append(bub)

# --- pour stream (can -> beaker): bezier with bevel, grows with bevel_factor_end
cu = bpy.data.curves.new("PourStream", 'CURVE'); cu.dimensions = '3D'; sp = cu.splines.new('BEZIER'); sp.bezier_points.add(2)
cu.bevel_depth = 0.0045; cu.bevel_resolution = 4; cu.use_fill_caps = True
st = bpy.data.objects.new("PourStream", cu); sc.collection.objects.link(st); put(st, P); st.data.materials.append(bpy.data.materials["SodaLiquid"])

# park props off-set until animation places them
for o in (can, plate, pud, beaker, jel, tray, spat, mouse, st):
    o.location = (0, -20, 0)
sc["TABLE_Z"] = TABLE_Z; sc["LAB_Z"] = LT_Z; sc["LX"] = LX
bpy.ops.wm.save_as_mainfile(filepath=BUILD + "/sets.blend")
print("SETS saved")
