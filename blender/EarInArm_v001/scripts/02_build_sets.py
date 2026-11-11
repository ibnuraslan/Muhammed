"""Sets and props. blender -b work/humans.blend --python 02_build_sets.py -- work/sets.blend
OR set at the origin; studio A (rib cage) at x=+40; studio B (forearm tissue slice) at x=+60."""
import sys, os, math, random
import bpy, bmesh
from mathutils import Vector, Matrix, Euler
out = sys.argv[sys.argv.index("--") + 1]
HERE = os.path.dirname(os.path.abspath(__file__)); AS = os.path.join(HERE, "..", "assets")
sc = bpy.context.scene
random.seed(7)
R_ = math.radians

def coll(name):
    c = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if c.name not in sc.collection.children: sc.collection.children.link(c)
    return c
C_OR, C_SA, C_SB, C_PROP = coll("OR_Set"), coll("Studio_Ribs"), coll("Studio_Tissue"), coll("Props")

def link(o, c):
    for u in list(o.users_collection): u.objects.unlink(o)
    c.objects.link(o); return o

# ------------------------------------------------------------------ materials
def mat(name, col, rough=0.5, metal=0.0, sss=0.0, emit=None, alpha=1.0, trans=0.0, coat=0.0):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*col, 1); b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if sss: b.inputs["Subsurface Weight"].default_value = sss; b.inputs["Subsurface Radius"].default_value = (1.0, 0.35, 0.2); b.inputs["Subsurface Scale"].default_value = 0.01
    if emit: b.inputs["Emission Color"].default_value = (*emit[0], 1); b.inputs["Emission Strength"].default_value = emit[1]
    if alpha < 1: b.inputs["Alpha"].default_value = alpha
    if trans: b.inputs["Transmission Weight"].default_value = trans
    if coat: b.inputs["Coat Weight"].default_value = coat
    return m

def tex_mat(name, folder, scale=1.0, tint=None):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; b = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord"); mp = nt.nodes.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (scale,) * 3
    nt.links.new(tc.outputs["UV"], mp.inputs["Vector"])
    fs = os.listdir(os.path.join(AS, folder))
    def img(key, cs):
        f = [x for x in fs if key in x.lower()]
        if not f: return None
        t = nt.nodes.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(os.path.join(AS, folder, f[0])); t.image.colorspace_settings.name = cs
        nt.links.new(mp.outputs["Vector"], t.inputs["Vector"]); return t
    d = img("diff", "sRGB")
    if d:
        if tint:
            mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs["Factor"].default_value = 1
            mx.inputs["B"].default_value = (*tint, 1); nt.links.new(d.outputs["Color"], mx.inputs["A"]); nt.links.new(mx.outputs["Result"], b.inputs["Base Color"])
        else: nt.links.new(d.outputs["Color"], b.inputs["Base Color"])
    r = img("rough", "Non-Color")
    if r: nt.links.new(r.outputs["Color"], b.inputs["Roughness"])
    n = img("nor_gl", "Non-Color")
    if n:
        nm = nt.nodes.new("ShaderNodeNormalMap"); nt.links.new(n.outputs["Color"], nm.inputs["Color"]); nt.links.new(nm.outputs["Normal"], b.inputs["Normal"])
    return m

def box(name, size, loc, m, c, bevel=0.0, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1); o = bpy.context.object; o.name = name
    o.scale = size; bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    o.location = loc; o.rotation_euler = rot
    if bevel:
        bv = o.modifiers.new("bev", 'BEVEL'); bv.width = bevel; bv.segments = 3
    o.data.materials.append(m); return link(o, c)

def cyl(name, r, h, loc, m, c, rot=(0, 0, 0), verts=24):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=h, location=loc, rotation=rot, vertices=verts); o = bpy.context.object; o.name = name
    o.data.materials.append(m); bpy.ops.object.shade_smooth(); return link(o, c)

def sph(name, r, loc, m, c, scale=(1, 1, 1)):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, location=loc, segments=24, ring_count=12); o = bpy.context.object; o.name = name
    o.scale = scale; bpy.ops.object.shade_smooth(); o.data.materials.append(m); return link(o, c)

def import_glb(name, path, c, size, axis=None):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    newnames = [o.name for o in new]
    meshes = [o for o in new if o.type == 'MESH']
    for o in new:
        if o.type != 'MESH': continue
        M = o.matrix_world.copy(); o.parent = None; o.matrix_world = M
    bpy.ops.object.select_all(action='DESELECT')
    for o in meshes: o.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    if len(meshes) > 1: bpy.ops.object.join()
    o = bpy.context.object; o.name = name + "_tmpjoin"
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    for xn in newnames:
        x = bpy.data.objects.get(xn)
        if x is not None and x != o: bpy.data.objects.remove(x, do_unlink=True)
    o.name = name
    pts = [Vector(v.co) for v in o.data.vertices]
    mn = Vector([min(p[i] for p in pts) for i in range(3)]); mx = Vector([max(p[i] for p in pts) for i in range(3)])
    ctr = (mn + mx) / 2; dims = mx - mn
    s = size / (dims[axis] if axis is not None else max(dims))
    o.data.transform(Matrix.Scale(s, 4) @ Matrix.Translation(-ctr)); o.data.update()
    print("IMPORT", name, [round(d * s, 3) for d in dims])
    return link(o, c)

M_TILE = tex_mat("Floor_Tiles", "floor_tiles_02", 2.0, tint=(0.75, 0.8, 0.82))
M_WALL = tex_mat("Wall_Plaster", "grey_plaster", 1.0, tint=(0.72, 0.84, 0.86))
M_STEEL = mat("Steel", (0.8, 0.8, 0.82), 0.25, 1.0)
M_BSTEEL = mat("BrushedSteel", (0.6, 0.62, 0.64), 0.4, 1.0)
M_UPH = mat("Upholstery", (0.08, 0.22, 0.3), 0.55, coat=0.3)
M_WHITE = mat("WhitePaint", (0.85, 0.87, 0.88), 0.35)
M_DARK = mat("DarkPlastic", (0.03, 0.035, 0.04), 0.4)
M_GAUZE = mat("Gauze", (0.92, 0.92, 0.9), 0.9, sss=0.1)
M_CART = mat("Cartilage", (0.86, 0.88, 0.9), 0.3, sss=0.35, coat=0.4)
M_CART.node_tree.nodes["Principled BSDF"].inputs["Subsurface Radius"].default_value = (0.6, 0.65, 0.9)
M_DRAPE = mat("Drape", (0.15, 0.42, 0.5), 0.8)
M_GLASS = mat("Glass", (0.9, 0.95, 1.0), 0.05, trans=1.0)
M_SCREEN = mat("Screen", (0.0, 0.0, 0.0), 0.2, emit=((0.02, 0.05, 0.06), 1.0))
M_TRACE = mat("Trace", (0.1, 1.0, 0.4), 0.5, emit=((0.2, 1.0, 0.45), 6.0))
M_IVBAG = mat("IVBag", (0.9, 0.95, 1.0), 0.1, alpha=0.4, trans=0.6)

# ================================================================== OR SET (origin)
box("OR_Floor", (8, 8, 0.02), (0, 0, -0.01), M_TILE, C_OR)
bpy.ops.object.select_all(action='DESELECT')
for nm, size, loc in (("OR_WallBack", (8, 0.1, 3.2), (0, 2.6, 1.6)), ("OR_WallLeft", (0.1, 8, 3.2), (-2.6, 0, 1.6)),
                      ("OR_WallRight", (0.1, 8, 3.2), (3.0, 0, 1.6)), ("OR_WallFront", (8, 0.1, 3.2), (0, -3.6, 1.6))):
    o = box(nm, size, loc, M_WALL, C_OR)
    bpy.context.view_layer.objects.active = o; bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.uv.cube_project(cube_size=2.0); bpy.ops.object.mode_set(mode='OBJECT')
o = bpy.data.objects["OR_Floor"]; bpy.context.view_layer.objects.active = o; bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.uv.cube_project(cube_size=2.0); bpy.ops.object.mode_set(mode='OBJECT')
box("OR_Ceiling", (8, 8, 0.05), (0, 0, 3.0), M_WHITE, C_OR)
for i, x in enumerate((-1.2, 1.2)):  # ceiling light panels
    box("OR_CeilLight%d" % i, (0.6, 1.2, 0.02), (x, 0.3, 2.97), mat("Panel", (1, 1, 1), 0.5, emit=((1, 0.98, 0.95), 6.0)), C_OR)
# wall cabinets and a scrub sink area on the back wall (background detail)
for i in range(4):
    box("OR_Cabinet%d" % i, (0.58, 0.45, 0.9), (-1.6 + i * 0.6, 2.3, 0.45), M_WHITE, C_OR, bevel=0.01)
    box("OR_CabHandle%d" % i, (0.15, 0.02, 0.02), (-1.6 + i * 0.6, 2.06, 0.8), M_STEEL, C_OR)
    box("OR_CabGlass%d" % i, (0.56, 0.35, 0.7), (-1.6 + i * 0.6, 2.38, 1.75), M_GLASS, C_OR)
    for j in range(3):
        box("OR_Supply%d_%d" % (i, j), (0.12, 0.1, 0.18), (-1.75 + i * 0.6 + j * 0.15, 2.4, 1.55), mat("Supply%d" % j, [(0.3, 0.5, 0.7), (0.9, 0.9, 0.85), (0.6, 0.3, 0.3)][j], 0.6), C_OR)
box("OR_Counter", (2.4, 0.5, 0.04), (-0.7, 2.3, 0.92), M_BSTEEL, C_OR)

# procedure chair: base, seat, hinged back (pivot) and footrest
CH = Vector((0, 0, 0))
box("Chair_Base", (0.5, 0.6, 0.08), (0, 0.0, 0.04), M_DARK, C_OR, bevel=0.02)
cyl("Chair_Column", 0.08, 0.36, (0, 0.0, 0.26), M_STEEL, C_OR)
box("Chair_Seat", (0.56, 0.55, 0.12), (0, -0.05, 0.49), M_UPH, C_OR, bevel=0.04)
box("Chair_LegRest", (0.5, 0.5, 0.1), (0, -0.55, 0.42), M_UPH, C_OR, bevel=0.04, rot=(R_(-35), 0, 0))
piv = bpy.data.objects.new("Chair_BackPivot", None); C_OR.objects.link(piv); piv.location = (0, 0.18, 0.55)
bk = box("Chair_Back", (0.54, 0.12, 0.8), (0, 0.27, 0.98), M_UPH, C_OR, bevel=0.04)
hr = box("Chair_Headrest", (0.3, 0.12, 0.2), (0, 0.27, 1.47), M_UPH, C_OR, bevel=0.04)
for o in (bk, hr):
    o.parent = piv; o.matrix_parent_inverse = piv.matrix_world.inverted()
for s in (-1, 1):
    box("Chair_Arm%d" % (s > 0), (0.08, 0.45, 0.05), (s * 0.32, 0.0, 0.7), M_UPH, C_OR, bevel=0.02)
    cyl("Chair_ArmPost%d" % (s > 0), 0.02, 0.2, (s * 0.32, 0.1, 0.6), M_STEEL, C_OR)
# arm board for the left arm (+X), height matches the shoulder of the reclined patient
box("ArmBoard", (0.6, 0.16, 0.04), (0.62, 0.15, 0.86), M_UPH, C_OR, bevel=0.015)
cyl("ArmBoard_Post", 0.02, 0.84, (0.62, 0.15, 0.42), M_STEEL, C_OR)
box("ArmBoard_Foot", (0.3, 0.3, 0.03), (0.62, 0.15, 0.015), M_DARK, C_OR)
box("ArmBoard_Drape", (0.62, 0.2, 0.006), (0.62, 0.15, 0.883), M_DRAPE, C_OR)

# instrument trolley (surgeon's carving station)
TR = Vector((1.05, -0.75, 0.0))
box("Trolley_Top", (0.7, 0.45, 0.03), TR + Vector((0, 0, 0.9)), M_BSTEEL, C_OR)
box("Trolley_Shelf", (0.7, 0.45, 0.02), TR + Vector((0, 0, 0.3)), M_BSTEEL, C_OR)
for dx in (-0.33, 0.33):
    for dy in (-0.2, 0.2):
        cyl("Trolley_Leg", 0.012, 0.88, TR + Vector((dx, dy, 0.46)), M_STEEL, C_OR, verts=12)
        sph("Trolley_Wheel", 0.03, TR + Vector((dx, dy, 0.03)), M_DARK, C_OR)
box("Trolley_Drape", (0.66, 0.42, 0.004), TR + Vector((0, 0, 0.917)), M_DRAPE, C_OR)
tray = import_glb("Tray", os.path.join(AS, "tray.glb"), C_OR, 0.34)
tray.location = TR + Vector((0.1, 0.0, 0.92)); tray.rotation_euler = (0, 0, R_(90))
# instruments laid on the drape
for i in range(5):
    cyl("Trolley_Instr%d" % i, 0.004, 0.14, TR + Vector((-0.25 + i * 0.03, 0.08, 0.924)), M_STEEL, C_OR, rot=(R_(90), 0, 0), verts=8)
box("Trolley_GauzeStack", (0.1, 0.1, 0.03), TR + Vector((-0.2, -0.12, 0.935)), M_GAUZE, C_OR, bevel=0.005)
# kidney dish held by the nurse later
bpy.ops.mesh.primitive_torus_add(major_radius=0.07, minor_radius=0.018, location=(0, 0, 0)); kd = bpy.context.object; kd.name = "KidneyDish"
kd.scale = (1.4, 0.8, 0.6); bpy.ops.object.transform_apply(scale=True); kd.data.materials.append(M_STEEL); bpy.ops.object.shade_smooth(); link(kd, C_PROP)

# IV stand and bag
IV = Vector((-0.55, 0.45, 0))
cyl("IV_Pole", 0.012, 1.9, IV + Vector((0, 0, 0.95)), M_STEEL, C_OR, verts=12)
for a in range(5):
    cyl("IV_FootSpoke", 0.01, 0.3, IV + Vector((0.15 * math.cos(a * 1.256), 0.15 * math.sin(a * 1.256), 0.05)), M_STEEL, C_OR, rot=(0, R_(90), a * 1.256), verts=8)
sph("IV_Bag", 0.07, IV + Vector((0.08, 0, 1.75)), M_IVBAG, C_OR, scale=(1, 0.4, 1.5))
drip = sph("IV_Drip", 0.006, IV + Vector((0.08, 0, 1.55)), mat("Drip", (0.9, 0.95, 1), 0.05, trans=1.0), C_OR)
for f in range(1, 1771, 40):  # a drip falling every 40 frames
    drip.location.z = IV.z + 1.58; drip.keyframe_insert("location", index=2, frame=f)
    drip.location.z = IV.z + 1.45; drip.keyframe_insert("location", index=2, frame=f + 12)
for fc in drip.animation_data.action.layers[0].strips[0].channelbags[0].fcurves:
    for kp in fc.keyframe_points: kp.interpolation = 'CONSTANT' if int(kp.co.x - 1) % 40 == 12 else 'QUAD'
# heart monitor on an arm with an animated trace (no text)
MON = Vector((-0.75, -0.1, 1.55))
cyl("Mon_Pole", 0.02, 1.5, Vector((MON.x - 0.05, MON.y + 0.12, 0.75)), M_STEEL, C_OR)
box("Mon_Body", (0.42, 0.06, 0.3), MON, M_DARK, C_OR, bevel=0.01, rot=(0, 0, R_(40)))
scr = box("Mon_Screen", (0.38, 0.005, 0.26), MON + Vector((-0.019, -0.023, 0)), M_SCREEN, C_OR, rot=(0, 0, R_(40)))
# trace: a curve with a moving ECG bump made of 3 polylines whose x offset scrolls
def ecg(t):
    t = t % 1.0
    return 0.03 * math.exp(-((t - 0.3) / 0.015) ** 2) - 0.012 * math.exp(-((t - 0.34) / 0.01) ** 2) + 0.01 * math.exp(-((t - 0.55) / 0.04) ** 2)
for row, (col, z) in enumerate((((0.2, 1.0, 0.45), 0.06), ((1.0, 0.85, 0.2), -0.02), ((0.3, 0.8, 1.0), -0.08))):
    cu = bpy.data.curves.new("Trace%d" % row, 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = 0.0018
    sp = cu.splines.new('POLY'); N = 60; sp.points.add(N - 1)
    for i in range(N):
        u = i / (N - 1); y = ecg(u * 2.0) if row == 0 else (0.012 * math.sin(u * 25) if row == 1 else 0.01 * math.sin(u * 12 + 1))
        sp.points[i].co = (-0.17 + 0.34 * u, 0, z + y, 1)
    to = bpy.data.objects.new("Mon_Trace%d" % row, cu); C_OR.objects.link(to)
    cu.materials.append(mat("Trace%d" % row, col, 0.5, emit=(col, 5.0)))
    to.parent = scr; to.location = (0, -0.004, 0)
    cu.bevel_factor_mapping_start = cu.bevel_factor_mapping_end = 'SPLINE'
    for f in range(1, 1771, 60):  # sweep: trace draws on, once per second (heartbeat)
        cu.bevel_factor_end = 0.02; cu.keyframe_insert("bevel_factor_end", frame=f)
        cu.bevel_factor_end = 1.0; cu.keyframe_insert("bevel_factor_end", frame=f + 57)
# ceiling surgical lamps (CC-BY)
lamps = import_glb("OR_Lamps", os.path.join(AS, "or_lamps.glb"), C_OR, 1.8)
lamps.location = (0.3, 0.2, 2.45); lamps.rotation_euler = (R_(90), 0, 0)
# floor kick plate, a wall clock-free poster-free wall. Door at the right wall
box("OR_Door", (0.05, 1.2, 2.2), (2.95, -1.2, 1.1), mat("DoorPanel", (0.5, 0.62, 0.66), 0.4), C_OR, bevel=0.01)
box("OR_DoorWindow", (0.06, 0.4, 0.5), (2.95, -1.2, 1.5), M_GLASS, C_OR)
box("OR_Kick", (8, 0.02, 0.12), (0, 2.54, 0.06), M_BSTEEL, C_OR)
# back-table with a sterile bowl
box("OR_BackTable", (1.0, 0.55, 0.03), (1.9, 1.4, 0.9), M_BSTEEL, C_OR)
for dx in (-0.45, 0.45):
    for dy in (-0.24, 0.24):
        cyl("OR_BackTableLeg", 0.012, 0.88, (1.9 + dx, 1.4 + dy, 0.45), M_STEEL, C_OR, verts=12)
sph("OR_Bowl", 0.11, (1.75, 1.4, 0.98), M_STEEL, C_OR, scale=(1, 1, 0.4))

# ================================================================== STUDIO A: rib-cage cross-section (x=+40)
SA = Vector((40, 0, 1.2))
def studio(name, ctr, c, R=2.6):
    # cyclorama sphere with cyan-to-white gradient by height (inside view)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=R, location=ctr, segments=48, ring_count=24); o = bpy.context.object; o.name = name + "_Cyc"
    bpy.ops.object.shade_smooth()
    m = bpy.data.materials.new(name + "_Grad"); m.use_nodes = True; nt = m.node_tree; nt.nodes.remove(nt.nodes["Principled BSDF"])
    tc = nt.nodes.new("ShaderNodeTexCoord"); sep = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(tc.outputs["Object"], sep.inputs[0])
    mr = nt.nodes.new("ShaderNodeMapRange"); mr.inputs["From Min"].default_value = -R * 0.8; mr.inputs["From Max"].default_value = R * 0.9
    nt.links.new(sep.outputs["Z"], mr.inputs["Value"])
    cr = nt.nodes.new("ShaderNodeValToRGB"); cr.color_ramp.elements[0].color = (0.92, 0.97, 1.0, 1); cr.color_ramp.elements[1].color = (0.05, 0.42, 0.62, 1)
    e = cr.color_ramp.elements.new(0.45); e.color = (0.35, 0.75, 0.88, 1)
    nt.links.new(mr.outputs["Result"], cr.inputs["Fac"])
    em = nt.nodes.new("ShaderNodeEmission"); em.inputs["Strength"].default_value = 0.75; nt.links.new(cr.outputs["Color"], em.inputs["Color"])
    nt.links.new(em.outputs[0], nt.nodes["Material Output"].inputs["Surface"])
    o.data.materials.append(m); link(o, c)
    o.visible_shadow = False
    # soft studio lights
    for i, (off, en, sz, col) in enumerate(((Vector((-1.2, -1.4, 1.2)), 120, 1.2, (1, 0.97, 0.92)), (Vector((1.5, -0.6, 0.4)), 50, 1.0, (0.8, 0.92, 1.0)),
                                             (Vector((0.2, 1.4, 1.0)), 90, 0.6, (0.85, 0.95, 1.0)))):
        ld = bpy.data.lights.new("%s_L%d" % (name, i), 'AREA'); ld.energy = en; ld.size = sz; ld.color = col
        lo = bpy.data.objects.new(ld.name, ld); c.objects.link(lo); lo.location = ctr + off
        lo.rotation_euler = (ctr - lo.location).to_track_quat('-Z', 'Y').to_euler()
    return o
studio("SA", SA, C_SA)
thor = import_glb("SA_Thorax", os.path.join(AS, "thorax.glb"), C_SA, 0.62)
thor.data.transform(Matrix.Rotation(R_(-90), 4, 'Z'))
bm = bmesh.new(); bm.from_mesh(thor.data); bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0005)
bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(thor.data); bm.free()
for a in list(thor.data.color_attributes): thor.data.color_attributes.remove(a)
thor.location = SA
M_BONE = mat("Bone", (0.88, 0.82, 0.7), 0.45, sss=0.15)
thor.data.materials.clear(); thor.data.materials.append(M_BONE)
# soft-tissue cross-section slab (translucent pink) behind the ribs reads as "inside the chest"
slab = box("SA_TissueSlab", (0.5, 0.06, 0.55), SA + Vector((0, 0.16, 0)), mat("TissueGlass", (0.95, 0.55, 0.55), 0.3, sss=0.3, alpha=0.35), C_SA, bevel=0.02)
# the pale costal cartilage block that gets lifted out (front, lower right ribs)
CB_POS = SA + Vector((0.07, -0.14, -0.1))
cblock = box("SA_CartBlock", (0.06, 0.03, 0.07), CB_POS, M_CART, C_SA, bevel=0.008)
cblock.modifiers.new("sub", 'SUBSURF').levels = 1
# glowing cut outline around the block
cu = bpy.data.curves.new("SA_CutLine", 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = 0.0012
sp = cu.splines.new('POLY'); sp.points.add(31); sp.use_cyclic_u = True
for i in range(32):
    a = i / 32 * 2 * math.pi; sp.points[i].co = (0.036 * math.cos(a), -0.017, 0.042 * math.sin(a), 1)
cut = bpy.data.objects.new("SA_CutLine", cu); C_SA.objects.link(cut); cut.location = CB_POS
cu.materials.append(mat("CutGlow", (1, 0.9, 0.5), 0.5, emit=((1.0, 0.85, 0.4), 8.0)))
cu.bevel_factor_end = 0.0
# floating membrane the camera comes through (matches the white tee / skin)
mem = box("SA_Membrane", (0.9, 0.004, 1.2), SA + Vector((0, -0.575, 0)), mat("MembraneSkin", (0.95, 0.93, 0.9), 0.6, sss=0.2, alpha=0.55), C_SA)
# floating particles for depth (foreground/background life)
for i in range(40):
    p = sph("SA_Mote%d" % i, random.uniform(0.003, 0.008), SA + Vector((random.uniform(-0.8, 0.8), random.uniform(-0.6, 0.9), random.uniform(-0.6, 0.7))),
            mat("Mote", (0.9, 0.97, 1), 0.3, emit=((0.8, 0.95, 1), 1.5)), C_SA)
    p.keyframe_insert("location", frame=1); p.location += Vector((random.uniform(-0.1, 0.1), random.uniform(-0.1, 0.1), random.uniform(0.05, 0.2))); p.keyframe_insert("location", frame=1770)

# ================================================================== STUDIO B: forearm tissue slice (x=+60)
SB = Vector((60, 0, 1.2))
studio("SB", SB, C_SB, R=1.4)
M_SKIN_SL = mat("SliceSkin", (0.78, 0.55, 0.45), 0.45, sss=0.4)
M_FAT = mat("SliceFat", (0.95, 0.82, 0.5), 0.4, sss=0.3)
M_MUSC = mat("SliceMuscle", (0.6, 0.12, 0.12), 0.35, sss=0.3)
# layered tissue block 0.5 x 0.35, the ear sits in the fat layer just under the skin. The skin layer is glassy (x-ray) here.
box("SB_Muscle", (0.5, 0.35, 0.12), SB + Vector((0, 0, -0.11)), M_MUSC, C_SB, bevel=0.01)
box("SB_Fat", (0.5, 0.35, 0.06), SB + Vector((0, 0, -0.02)), M_FAT, C_SB, bevel=0.005)
sk = box("SB_SkinXray", (0.5, 0.35, 0.012), SB + Vector((0, 0, 0.034)), mat("XraySkin", (0.95, 0.75, 0.65), 0.15, alpha=0.25, trans=0.3, coat=1.0), C_SB, bevel=0.004)
for o in C_SB.objects:
    if o.type == 'MESH' and o.name.startswith("SB_") and "Cyc" not in o.name:
        o.modifiers.new("sub", 'SUBSURF').levels = 1
# muscle fibre stripes for texture
for i in range(14):
    cyl("SB_Fibre%d" % i, 0.008, 0.48, SB + Vector((0, -0.16 + i * 0.024, -0.12 + random.uniform(-0.03, 0.03))), M_MUSC, C_SB, rot=(0, R_(90), 0), verts=10)
# membrane matching the forearm skin (camera dives through it)
box("SB_Membrane", (0.9, 1.2, 0.004), SB + Vector((0, 0, 0.42)), mat("MembraneArm", (0.8, 0.62, 0.55), 0.6, emit=((0.9, 0.75, 0.68), 0.5)), C_SB)
for i in range(30):
    p = sph("SB_Cell%d" % i, random.uniform(0.004, 0.012), SB + Vector((random.uniform(-0.5, 0.5), random.uniform(-0.4, 0.4), random.uniform(0.06, 0.4))),
            mat("Cell", (1.0, 0.5, 0.5), 0.3, emit=((1, 0.4, 0.4), 0.8), alpha=0.7), C_SB)
    p.keyframe_insert("location", frame=1); p.location += Vector((random.uniform(-0.08, 0.08), random.uniform(-0.08, 0.08), random.uniform(-0.05, 0.05))); p.keyframe_insert("location", frame=1770)

# ================================================================== PROPS
ear = import_glb("Ear_Src", os.path.join(AS, "ear.glb"), C_PROP, 0.065, axis=None)
ear.data.materials.clear(); ear.data.materials.append(M_CART)
scal = import_glb("Scalpel", os.path.join(AS, "scalpel.glb"), C_PROP, 0.15)
# forceps: two thin blades joined at the back (procedural)
def forceps(name):
    bm = bmesh.new()
    for s in (-1, 1):
        g = bmesh.ops.create_cube(bm, size=1.0)["verts"]
        for v in g:
            v.co = Vector((v.co.x * 0.006, v.co.y * 0.13 + 0.065, v.co.z * 0.003))
            v.co.x += s * (0.0025 + 0.006 * (v.co.y / 0.13))  # tips spread
    me = bpy.data.meshes.new(name); bm.to_mesh(me); o = bpy.data.objects.new(name, me); C_PROP.objects.link(o)
    o.data.materials.append(M_STEEL); o.modifiers.new("bev", 'BEVEL').width = 0.001
    return o
forc = forceps("Forceps"); forc2 = forceps("Forceps_Nurse")
# needle holder + curved needle + thread
nh = cyl("NeedleHolder", 0.003, 0.15, (0, 0, 0), M_STEEL, C_PROP, rot=(R_(90), 0, 0), verts=8)
for s in (-1, 1):
    bpy.ops.mesh.primitive_torus_add(major_radius=0.008, minor_radius=0.0015, location=(s * 0.008, 0.07, 0)); r = bpy.context.object; r.name = "NH_Ring"; r.data.materials.append(M_STEEL); link(r, C_PROP); r.parent = nh
bpy.ops.mesh.primitive_torus_add(major_radius=0.006, minor_radius=0.0004, major_segments=24, minor_segments=6, location=(0, -0.078, 0)); nd = bpy.context.object; nd.name = "Needle"
bm = bmesh.from_edit_mesh(nd.data) if False else None
nd.data.materials.append(M_STEEL); link(nd, C_PROP)
nd.parent = nh
M_THREAD = mat("Suture", (0.1, 0.12, 0.35), 0.5)
print("SETS_DONE", len(bpy.data.objects))
bpy.ops.wm.save_as_mainfile(filepath=out)
