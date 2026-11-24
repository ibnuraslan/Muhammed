"""v014 layout (static): both monkeys sit upright on padded primate seats on the OR table, facing the camera side;
instrument towel + needle holder, heart-monitor cart beside the table, x-ray anatomy, new light rig.
blender -b surg.blend --python 03_layout.py -- layout.blend"""
import bpy, sys, math, bmesh, json, os
from mathutils import Vector, Matrix, Euler
OUT = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene; D = bpy.data
def kill(names):
    for n in names:
        o = D.objects.get(n)
        if o: D.objects.remove(o, do_unlink=True)
kill(["T1_BodyDrape", "T2_BodyDrape", "T1_HeadRest", "T2_HeadRest", "T1_Drape", "T2_Drape", "MarkerLine", "MarkerPen", "MarkerPenTip",
      "NeckRef", "Seam", "NeckBandage", "Collar_Head", "Collar_BodyB", "XR_CordBody", "XR_CordHead", "XR_Spine", "XR_GapGlowBody",
      "XR_GapGlowHead", "XR_Pulse", "XR_Void", "XR_Key", "NeedleHolder", "NeedleHolderRing1", "NeedleHolderRing-1",
      "Lamp2Sat_Pivot", "LampSat_Arm", "LampSat_Dome", "LampSat_Lens", "LampSat_Spot", "Lamp2_Base", "Lamp2_Pole", "Lamp2_Shade", "Lamp2_Light"])
col = D.collections.get("V14") or D.collections.new("V14")
if col.name not in sc.collection.children: sc.collection.children.link(col)
def mat(name, rgb, rough=0.5, metal=0.0, emit=None, estr=0.0, alpha=None):
    m = D.materials.get(name)
    if m: return m
    m = D.materials.new(name); m.use_nodes = True; p = m.node_tree.nodes["Principled BSDF"]
    p.inputs["Base Color"].default_value = (*rgb, 1); p.inputs["Roughness"].default_value = rough; p.inputs["Metallic"].default_value = metal
    if emit: p.inputs["Emission Color"].default_value = (*emit, 1); p.inputs["Emission Strength"].default_value = estr
    return m
def link(o):
    for c in o.users_collection: c.objects.unlink(o)
    col.objects.link(o); return o
def ray_down(objs, x, y, z0=3.0):
    best = None
    dg = bpy.context.evaluated_depsgraph_get()
    for o in objs:
        oe = o.evaluated_get(dg); inv = o.matrix_world.inverted()
        ok, loc, nrm, idx = oe.ray_cast(inv @ Vector((x, y, z0)), (inv.to_3x3() @ Vector((0, 0, -1))).normalized())
        if ok:
            w = o.matrix_world @ loc
            if best is None or w.z > best: best = w.z
    return best
TABLES = [D.objects["T1_Pad"], D.objects["T2_Pad"]]
VINYL = mat("V_SeatVinyl", (0.10, 0.32, 0.30), 0.42)
STEEL = mat("V_Steel", (0.50, 0.52, 0.55), 0.32, 0.9)
TOWEL = mat("V_Towel", (0.30, 0.55, 0.52), 0.85)
# ---------------------------------------------------------------- monkeys: upright, reclined 8 deg against a padded backrest
REC = -0.14
L = {}
for tag, x in (("A", -0.27), ("B", 0.27)):
    root = D.objects["MonkeyRoot" + tag]; bodyo = D.objects["MK_Body" + tag]
    root.rotation_mode = 'XYZ'; root.rotation_euler = (REC, 0.0, 0.0); root.location = (0, 0, 0)
    bpy.context.view_layer.update()
    vs = [bodyo.matrix_world @ v.co for v in bodyo.data.vertices]
    zmin = min(v.z for v in vs); ymax = max(v.y for v in vs)
    low = [v for v in vs if v.z < zmin + 0.03]
    cx = sum(v.x for v in low) / len(low); cy = sum(v.y for v in low) / len(low)
    tz = ray_down(TABLES, x, 0.25)
    seat_top = tz + 0.05
    back_y = 0.415                                      # monkey's back plane
    root.location = (x - cx * 0, back_y - ymax, seat_top - zmin - 0.003)
    bpy.context.view_layer.update()
    vs = [bodyo.matrix_world @ v.co for v in bodyo.data.vertices]
    low = [v for v in vs if v.z < seat_top + 0.03]
    sx0, sx1 = min(v.x for v in low), max(v.x for v in low); sy0, sy1 = min(v.y for v in low), max(v.y for v in low)
    # seat cushion
    bpy.ops.mesh.primitive_cube_add(size=1, location=((sx0 + sx1) / 2, (sy0 + sy1) / 2 + 0.01, tz + 0.025))
    cu = link(bpy.context.active_object); cu.name = "Seat_" + tag; cu.scale = (sx1 - sx0 + 0.08, sy1 - sy0 + 0.08, 0.05)
    bv = cu.modifiers.new("bev", "BEVEL"); bv.width = 0.015; bv.segments = 4; cu.data.materials.append(VINYL)
    for p in cu.data.polygons: p.use_smooth = True
    # backrest: a padded board behind the back, 8 mm clear of the fur at its closest point
    bx0, bx1 = root.location.x - 0.13, root.location.x + 0.13; bz0, bz1 = seat_top + 0.06, seat_top + 0.36
    back_pts = [v for v in vs if bx0 < v.x < bx1 and bz0 < v.z < bz1]
    by = max(v.y for v in back_pts) + 0.008
    bpy.ops.mesh.primitive_cube_add(size=1, location=(root.location.x, by + 0.025, (bz0 + bz1) / 2))
    br = link(bpy.context.active_object); br.name = "Backrest_" + tag; br.scale = (0.28, 0.05, bz1 - bz0)
    bv = br.modifiers.new("bev", "BEVEL"); bv.width = 0.018; bv.segments = 4; br.data.materials.append(VINYL)
    for p in br.data.polygons: p.use_smooth = True
    for sxp in (-0.1, 0.1):
        bpy.ops.mesh.primitive_cylinder_add(radius=0.009, depth=bz1 - tz + 0.02, location=(root.location.x + sxp, by + 0.06, (tz + bz1) / 2))
        po = link(bpy.context.active_object); po.name = "BackPost_%s%d" % (tag, 0 if sxp < 0 else 1); po.data.materials.append(STEEL)
        for p in po.data.polygons: p.use_smooth = True
    L[tag] = dict(root=tuple(root.location), seat_top=seat_top, table_z=tz, back_y=by, back_top=bz1)
    print("MONKEY", tag, "root", tuple(round(v, 3) for v in root.location), "seat", round(seat_top, 3), "backrest y", round(by, 3))
# the donor head starts on body A (same mesh family: head-local == identity on its body root)
head = D.objects["MK_Head"]; head.parent = None
head.matrix_world = D.objects["MonkeyRootA"].matrix_world.copy()
# body A gets its own materials (it can be faded out separately during the x-ray void)
bA = D.objects["MK_BodyA"]
for i, m in enumerate(bA.data.materials):
    bA.data.materials[i] = m.copy(); bA.data.materials[i].name = m.name + "_A"
for n in ("Collar_BodyA",):
    o = D.objects.get(n)
    if o: o.hide_render = o.hide_viewport = True
# ---------------------------------------------------------------- neck seam geometry (B): ring where head meets body
bpy.context.view_layer.update()
hB = D.objects["MonkeyRootB"].matrix_world
headB = hB.copy()   # head world matrix when seated on B
bB = D.objects["MK_BodyB"]
capf = [p for p in bB.data.polygons if bB.data.materials[p.material_index].name.startswith("M_NeckCap")]
cpts = [bB.matrix_world @ p.center for p in capf]
cc = sum(cpts, Vector()) / len(cpts)
nrm = sum((bB.matrix_world.to_3x3() @ p.normal for p in capf), Vector()).normalized()
if nrm.z < 0: nrm = -nrm
L["neck_c"] = tuple(cc); L["neck_n"] = tuple(nrm)
print("NECK", tuple(round(v, 3) for v in cc), tuple(round(v, 3) for v in nrm), len(capf))
# ---------------------------------------------------------------- instrument towel + needle holder (procedural, detailed)
tz = ray_down(TABLES, 0.55, 0.36)
tz = ray_down(TABLES, 0.66, 0.30)
bpy.ops.mesh.primitive_cube_add(size=1, location=(0.67, 0.33, tz + 0.025))
tw = link(bpy.context.active_object); tw.name = "InstrTowel"; tw.scale = (0.30, 0.22, 0.05); tw.data.materials.append(TOWEL)
bv = tw.modifiers.new("bev", "BEVEL"); bv.width = 0.012; bv.segments = 4
for p in tw.data.polygons: p.use_smooth = True
tz = tz + 0.038   # folded towel stack: the holder lies on top, fingers can pinch it from above
def needle_holder():
    """Mayo-Hegar style needle holder built along local +Y (rings at -Y, jaw tip at +Y), lying flat in XY."""
    parts = []
    # two shanks: tapered bars from ring to the box joint, crossing to the jaws
    for sgn in (-1, 1):
        bm = bmesh.new()
        prof = [(-0.075, 0.016 * sgn, 0.0035), (-0.02, 0.006 * sgn, 0.003), (0.0, 0.0, 0.0028), (0.025, -0.0012 * sgn, 0.0022), (0.04, -0.0006 * sgn, 0.0014)]
        rings = []
        for (y, x, r) in prof:
            ring = [bm.verts.new((x + r * math.cos(t), y, 0.0016 * sgn * 0 + r * 0.6 * math.sin(t))) for t in [k * math.pi / 4 for k in range(8)]]
            rings.append(ring)
        for a_, b_ in zip(rings, rings[1:]):
            for k in range(8):
                bm.faces.new((a_[k], a_[(k + 1) % 8], b_[(k + 1) % 8], b_[k]))
        bm.faces.new(rings[0][::-1]); bm.faces.new(rings[-1])
        me = D.meshes.new("NH_Shank"); bm.to_mesh(me); bm.free()
        o = D.objects.new("NH_Shank%d" % (0 if sgn < 0 else 1), me); col.objects.link(o); parts.append(o)
        for p in me.polygons: p.use_smooth = True
        bpy.ops.mesh.primitive_torus_add(major_radius=0.011, minor_radius=0.0022, location=(0.017 * sgn, -0.086, 0.0))
        t_ = link(bpy.context.active_object); t_.name = "NH_Ring%d" % (0 if sgn < 0 else 1); parts.append(t_)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.0035, depth=0.004, location=(0, 0, 0))
    j = link(bpy.context.active_object); j.name = "NH_Joint"; parts.append(j)
    # curved needle (half circle) held in the jaw tip + a short dark thread tail
    bm = bmesh.new(); pts = []
    for k in range(13):
        t = math.pi * k / 12
        pts.append(Vector((0.006 * math.cos(t), 0.041, -0.006 * math.sin(t) * 0.0 - 0.006 * math.sin(t))))
    cu = D.curves.new("NH_Needle", "CURVE"); cu.dimensions = '3D'; cu.bevel_depth = 0.0005; sp = cu.splines.new('POLY'); sp.points.add(len(pts) - 1)
    for k, q in enumerate(pts): sp.points[k].co = (*q, 1)
    nd = D.objects.new("NH_Needle", cu); col.objects.link(nd); parts.append(nd)
    for o in parts:
        if o.type in ('MESH', 'CURVE'):
            o.data.materials.clear(); o.data.materials.append(STEEL)
    root = D.objects.new("NeedleHolder", None); col.objects.link(root); root.empty_display_size = 0.03
    for o in parts:
        mw = o.matrix_world.copy(); o.parent = root; o.matrix_world = mw
    return root
nh = needle_holder()
for k, yy in enumerate((-0.072, 0.03)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0))
    rb = link(bpy.context.active_object); rb.name = "NH_Rest%d" % k; rb.data.materials.append(STEEL); rb["local_y"] = yy
nh.matrix_world = Matrix.Translation((0.64, 0.35, tz + 0.012 + 0.03 + 0.0035)) @ Matrix.Rotation(math.radians(160), 4, 'Z')
for k in (0, 1):
    rb = D.objects["NH_Rest%d" % k]
    rb.matrix_world = nh.matrix_world @ Matrix.Translation((0, rb["local_y"], -0.0035 - 0.015))
    rb.scale = (0.05, 0.012, 0.03)
L["nh_rest"] = [list(r) for r in nh.matrix_world]
L["towel_z"] = tz + 0.012
# ---------------------------------------------------------------- heart monitor cart beside the table (front-right of B)
dx, dy = -2.25, -0.10
for o in D.objects:
    if o.name.startswith(("MonCart_", "Monitor", "ECG_Trace", "Beep_Lamp", "Scope_LabelPlate")) and o.parent is None:
        o.location.x += dx; o.location.y += dy
lab = D.objects.get("Scope_LabelPlate")
if lab: lab.hide_render = lab.hide_viewport = True          # no labels or text anywhere
mon_o = D.objects["Monitor"]
for sl in mon_o.material_slots:
    m_ = sl.material
    if not (m_ and m_.node_tree): continue
    for n in list(m_.node_tree.nodes):
        if n.type == 'TEX_IMAGE' and n.image and n.outputs[0].links:
            px = n.image.pixels[:]; k_ = max(1, len(px) // 4 // 4000)
            avg = [sum(px[i * 4 * k_ + c] for i in range(len(px) // 4 // k_)) / (len(px) // 4 // k_) for c in range(3)]
            for l in list(n.outputs[0].links):
                to = l.to_socket; m_.node_tree.links.remove(l)
                if to.type == 'RGBA': to.default_value = (*avg, 1)
dm = D.materials.get("basedecal")                              # the scope's printed decal text -> plain dark enamel
if dm and dm.node_tree:
    for n in list(dm.node_tree.nodes):
        if n.type == 'TEX_IMAGE':
            for l in list(n.outputs[0].links): dm.node_tree.links.remove(l)
    pb = next((n for n in dm.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)
    if pb: pb.inputs["Base Color"].default_value = (0.05, 0.05, 0.055, 1); pb.inputs["Alpha"].default_value = 1.0
mon = D.objects["Monitor"]; bpy.context.view_layer.update()
mb = [mon.matrix_world @ Vector(c) for c in mon.bound_box]
mx0, mx1 = min(v.x for v in mb), max(v.x for v in mb); my0 = min(v.y for v in mb); mz1 = max(v.z for v in mb)
for nm_, zc, hz in (("ScopeTextCover_T", mz1 - 0.022, 0.04), ("ScopeTextCover_B", mz1 - 0.37, 0.03)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=((mx0 + mx1) / 2, my0 - 0.002, zc))
    cv = link(bpy.context.active_object); cv.name = nm_; cv.scale = (mx1 - mx0 - 0.01, 0.003, hz)
    cv.data.materials.append(mat("V_ScopeEnamel", (0.06, 0.065, 0.07), 0.4))
# move the IV pole out of the camera's working space (back-right corner)
for o in D.objects:
    if o.name.startswith("IV_") and o.parent is None: o.location.x += 0.55; o.location.y += 0.55
for n in ("Mayo_Instruments", "Instruments"):
    o = D.objects.get(n)
    if o: o.hide_render = o.hide_viewport = True
lr = D.objects.get("Lamp_Root")
if lr: lr.location.z += 0.4                          # dome lamp higher: out of the top of frame
# ---------------------------------------------------------------- x-ray anatomy (hidden until the x-ray beat)
XR = col
brain = D.objects["XR_Brain"]; brain.parent = None
hd = D.objects["MK_Head"]
hv = [hd.matrix_world @ v.co for v in hd.data.vertices]
L["head_bb"] = [[min(v[i] for v in hv) for i in range(3)], [max(v[i] for v in hv) for i in range(3)]]
print("HEAD_A bb", L["head_bb"])
json.dump(L, open(os.path.join(os.path.dirname(OUT), "layout.json"), "w"), indent=1)
# ---------------------------------------------------------------- light rig: warm OR key from the dome lamp, cool rim, soft fill
for n, e in (("Fill_Front", 160.0), ("Fill_Right", 110.0), ("Key_WarmCorner", 90.0), ("Key_WarmOR", 220.0), ("Rim_Back", 260.0), ("Rim_Cool", 80.0)):
    o = D.objects.get(n)
    if o: o.data.energy = e
ls = D.objects.get("Lamp_Spot")
if ls: ls.data.energy = 420.0; ls.data.color = (1.0, 0.93, 0.82)
def area(name, loc, tgt, size, energy, color):
    ld = D.lights.new(name, "AREA"); ld.size = size; ld.energy = energy; ld.color = color
    o = D.objects.new(name, ld); col.objects.link(o); o.location = loc
    o.rotation_mode = "QUATERNION"; o.rotation_quaternion = (Vector(tgt) - Vector(loc)).to_track_quat("-Z", "Y"); return o
area("V14_Key", (-0.9, -1.1, 2.3), (0.1, 0.25, 1.4), 1.0, 160.0, (1.0, 0.88, 0.74))     # warm key, front-left high
area("V14_Rim", (0.9, 1.6, 2.2), (0.15, 0.3, 1.5), 0.6, 140.0, (0.70, 0.86, 1.0))      # cool rim, back-right
area("V14_FaceFill", (0.9, -1.2, 1.6), (0.1, 0.4, 1.5), 1.4, 45.0, (0.92, 0.96, 1.0))    # soft fill, low right
sc.view_settings.look = "AgX - Punchy"; sc.view_settings.exposure = -0.25
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print("LAYOUT SAVED")
