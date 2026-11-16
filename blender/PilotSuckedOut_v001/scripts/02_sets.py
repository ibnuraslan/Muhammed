"""B17 sets: cockpit (NoPilotPlane set at origin), exterior 737 at (0,-3000,0) heading +X with the captain's front
windscreen pane removed, landing field at (0,-20000,-3000). blender -b base.blend --python 02_sets.py -- out.blend"""
import bpy, sys, math, bmesh, random
from mathutils import Vector, Matrix
OUT = sys.argv[sys.argv.index("--") + 1:][0]
D = bpy.data; sc = bpy.context.scene; R_ = math.radians
def coll(n):
    c = D.collections.get(n) or D.collections.new(n)
    if c.name not in sc.collection.children: sc.collection.children.link(c)
    return c
def mat(name, rgb, rough=0.5, metal=0.0, emit=0.0):
    m = D.materials.get(name) or D.materials.new(name); m.use_nodes = True
    P = m.node_tree.nodes["Principled BSDF"]; P.inputs["Base Color"].default_value = (*rgb, 1)
    P.inputs["Roughness"].default_value = rough; P.inputs["Metallic"].default_value = metal
    if emit: P.inputs["Emission Color"].default_value = (*rgb, 1); P.inputs["Emission Strength"].default_value = emit
    return m
# ---------------------------------------------------------------- world: level, ground 3 km below
er = D.objects["EXT_ROT"]; er.rotation_euler = (0, 0, 0); er.location = (0, 1.5, 1.2)
bpy.context.view_layer.update()
em = D.objects["EXT_MOVE"]; em.matrix_world = Matrix.Translation((0, 0, -3000))
for n in ("SUNSHADE_L", "SUNSHADE_R"):
    o = D.objects.get(n)
    if o: D.objects.remove(o, do_unlink=True)
# ---------------------------------------------------------------- uniform: captain epaulettes off (arms go overhead)
for n in ("EPAULETTE_CAPT_L", "EPAULETTE_CAPT_R"):
    o = D.objects.get(n)
    if o: D.objects.remove(o, do_unlink=True)
# ---------------------------------------------------------------- director P1 notes: deeper sky, sun key, darker ground, FO brown irises
sky = D.objects["SKY_DOME"].data.materials[0].node_tree
for n in sky.nodes:
    if n.type == 'VALTORGB':
        el = n.color_ramp.elements; el[0].color = (0.55, 0.75, 0.95, 1); el[1].color = (0.25, 0.55, 0.92, 1); el[2].color = (0.04, 0.28, 0.78, 1)
    if n.type == 'EMISSION': n.inputs["Strength"].default_value = 1.15
for n in sc.world.node_tree.nodes:
    if n.type == 'BACKGROUND' and not n.inputs[0].is_linked: n.inputs[1].default_value = 0.6
D.objects["SUN"].data.energy = 7.5
gm = D.objects["GROUND"].data.materials[0].node_tree
for n in gm.nodes:
    if n.type == 'HUE_SAT': n.inputs["Value"].default_value = n.inputs["Value"].default_value * 0.7; n.inputs["Saturation"].default_value = 1.25
fo_eye = None
for o in D.objects["FO"].children:
    for m in (o.data.materials if o.type == 'MESH' else []):
        if not m or not m.node_tree: continue
        for n in m.node_tree.nodes:
            if n.type == 'GROUP' and n.node_tree and n.node_tree.name.startswith("EnhancedEye"):
                n.inputs["IrisMajorColor"].default_value = (0.23, 0.12, 0.05, 1); n.inputs["IrisMinorColor"].default_value = (0.07, 0.035, 0.015, 1)
                n.inputs["EyeWhiteColor"].default_value = (0.82, 0.8, 0.78, 1); print("SETS FO iris ->", m.name)
for o in (D.objects["CAPT"], D.objects["Attendant"]):
    for c in o.children:
        for m in (c.data.materials if c.type == 'MESH' else []):
            if m and m.node_tree:
                for n in m.node_tree.nodes:
                    if n.type == 'GROUP' and n.node_tree and n.node_tree.name.startswith("EnhancedEye"):
                        n.inputs["EyeWhiteColor"].default_value = (0.85, 0.83, 0.8, 1)
# ---------------------------------------------------------------- 737 exterior
ap = D.objects["Airliner"]
OLD = ap.location.copy(); ap.location = (0, -3000, 0)
bm = bmesh.new(); bm.from_mesh(ap.data)
gi = {i for i, m in enumerate(ap.data.materials) if m and m.name.startswith("CockpitGlass")}
dead = []
for f in bm.faces:
    c = f.calc_center_median()
    if 17.45 <= c.x <= 18.25 and 0.04 <= c.y <= 0.84 and 3.9 <= c.z <= 4.32 and f.material_index in gi:
        dead.append(f)
print("SETS glass faces removed", len(dead))
bmesh.ops.delete(bm, geom=dead, context='FACES')
bm.to_mesh(ap.data); bm.free()
# dark cockpit liner inside the nose, seen through the open frame
M_liner = mat("M_nose_liner", (0.13, 0.15, 0.17), 0.7)
M_seat = mat("M_nose_seat", (0.18, 0.18, 0.2), 0.6)
# inner liner: a dark copy of the nose skin, pushed 4 cm inward, so the open frame shows a dark cockpit, not white backfaces
bm = bmesh.new(); bm.from_mesh(ap.data)
def _near_hole(c): return 17.0 <= c.x <= 18.7 and -0.45 <= c.y <= 1.35 and c.z >= 3.55
keep = [f for f in bm.faces if f.calc_center_median().x > 13.5 and f.material_index not in gi and not _near_hole(f.calc_center_median())]
bmesh.ops.delete(bm, geom=[f for f in bm.faces if f not in set(keep)], context='FACES')
for v in bm.verts: v.co -= v.normal * 0.04
bmesh.ops.reverse_faces(bm, faces=bm.faces[:])
lme = D.meshes.new("NOSE_LINER"); bm.to_mesh(lme); bm.free()
ln = D.objects.new("NOSE_LINER", lme); sc.collection.objects.link(ln); lme.materials.clear(); lme.materials.append(M_liner)
for p_ in lme.polygons: p_.material_index = 0
ln.parent = ap; ln.matrix_parent_inverse = Matrix.Identity(4)
bpy.ops.mesh.primitive_cube_add(size=1); st = bpy.context.active_object; st.name = "NOSE_SEAT"
st.scale = (0.12, 0.5, 0.75); st.location = (16.25, 0.45, 3.25); bpy.ops.object.transform_apply(scale=True)
bv = st.modifiers.new("b", 'BEVEL'); bv.width = 0.05; bv.segments = 3
st.data.materials.append(M_seat); st.parent = ap; st.matrix_parent_inverse = Matrix.Identity(4)
for o in (ln, st):
    for c in list(o.users_collection): c.objects.unlink(o)
    coll("PLANE").objects.link(o)
# ---------------------------------------------------------------- cloud puffs near the 737 (white, soft), they drift past in 03
M_cloud = mat("M_cloudpuff", (0.86, 0.89, 0.95), 0.9)
M_cloud.node_tree.nodes["Principled BSDF"].inputs["Subsurface Weight"].default_value = 0.0
CP = coll("CLOUDS_NEAR"); random.seed(17)
def puff(name, loc, size):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=1, location=(0, 0, 0)); o = bpy.context.active_object
    o.name = name
    for v in o.data.vertices:
        n = v.co.normalized(); v.co = n * (1 + 0.18 * math.sin(5 * n.x + 3 * n.y) * math.cos(4 * n.z + 2 * n.x))
    sub = o.modifiers.new("s", 'SUBSURF'); sub.levels = 1; sub.render_levels = 2
    bpy.ops.object.shade_smooth()
    # cluster of 4 lobes
    o.scale = (size * 1.3, size, size * 0.75); o.location = loc
    o.data.materials.append(M_cloud)
    for c in list(o.users_collection): c.objects.unlink(o)
    CP.objects.link(o); return o
for i in range(26):
    ang = random.uniform(0, 2 * math.pi); r = random.uniform(160, 460)
    base = Vector((random.uniform(-500, 700), -3000 + r * math.cos(ang), r * math.sin(ang) * 0.3 + random.uniform(-70, 30)))
    S = random.uniform(10, 22)
    for k in range(7):
        off = Vector((random.uniform(-2.2, 2.2) * S, random.uniform(-1.0, 1.0) * S, random.uniform(-0.2, 0.8) * S * (1 if k else 0)))
        puff("PUFF_%02d_%d" % (i, k), base + off, S * random.uniform(0.6, 1.1))
# ---------------------------------------------------------------- landing field (on the ground 3 km down)
L0 = Vector((0, -20000, -3000))
LC = coll("LANDING")
M_asph = mat("M_runway", (0.16, 0.165, 0.17), 0.75)
M_paint = mat("M_runway_paint", (0.92, 0.92, 0.9), 0.5)
M_grass = D.materials.new("M_grass_field"); M_grass.use_nodes = True
nt = M_grass.node_tree; P = nt.nodes["Principled BSDF"]
nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 0.02; nz.inputs["Detail"].default_value = 6
cr = nt.nodes.new("ShaderNodeValToRGB"); cr.color_ramp.elements[0].color = (0.16, 0.36, 0.08, 1); cr.color_ramp.elements[1].color = (0.33, 0.52, 0.14, 1)
nt.links.new(nz.outputs["Fac"], cr.inputs["Fac"]); nt.links.new(cr.outputs["Color"], P.inputs["Base Color"]); P.inputs["Roughness"].default_value = 0.85
M_hill = D.materials.new("M_hills"); M_hill.use_nodes = True
nt = M_hill.node_tree; P = nt.nodes["Principled BSDF"]
nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 0.004; nz.inputs["Detail"].default_value = 4
cr = nt.nodes.new("ShaderNodeValToRGB"); cr.color_ramp.elements[0].color = (0.2, 0.33, 0.12, 1); cr.color_ramp.elements[1].color = (0.42, 0.45, 0.26, 1)
nt.links.new(nz.outputs["Fac"], cr.inputs["Fac"]); nt.links.new(cr.outputs["Color"], P.inputs["Base Color"]); P.inputs["Roughness"].default_value = 0.9
def box(name, c, s, m, coll_=LC):
    bpy.ops.mesh.primitive_cube_add(size=1, location=c); o = bpy.context.active_object; o.name = name; o.scale = s
    bpy.ops.object.transform_apply(scale=True); o.data.materials.append(m)
    for cc in list(o.users_collection): cc.objects.unlink(o)
    coll_.objects.link(o); return o
box("RUNWAY", L0 + Vector((0, 0, 0.05)), (2400, 45, 0.1), M_asph)
pm = bmesh.new()
for i in range(-38, 38):   # centre-line dashes
    bmesh.ops.create_cube(pm, size=1, matrix=Matrix.Translation((i * 30, 0, 0.11)) @ Matrix.Diagonal((18, 0.9, 0.02, 1)))
for s in (-1, 1):          # edge lines
    bmesh.ops.create_cube(pm, size=1, matrix=Matrix.Translation((0, s * 21.5, 0.11)) @ Matrix.Diagonal((2380, 0.9, 0.02, 1)))
for k in range(8):         # threshold bars (no numbers, no text)
    for s in (-1, 1):
        bmesh.ops.create_cube(pm, size=1, matrix=Matrix.Translation((-1150, s * (3 + k * 2.2), 0.11)) @ Matrix.Diagonal((30, 1.4, 0.02, 1)))
for i in range(-20, 21):   # touchdown zone bars
    if abs(i) < 3: continue
for x in (-900, -750, -600):
    for s in (-1, 1):
        bmesh.ops.create_cube(pm, size=1, matrix=Matrix.Translation((x, s * 9, 0.11)) @ Matrix.Diagonal((22, 3, 0.02, 1)))
me = D.meshes.new("RUNWAY_PAINT"); pm.to_mesh(me); pm.free()
po = D.objects.new("RUNWAY_PAINT", me); po.location = L0; po.data.materials.append(M_paint); LC.objects.link(po)
g = box("GRASS", L0, (6000, 3000, 0.02), M_grass)
# rolling hills: subdivided grid displaced by noise, kept away from the runway
bpy.ops.mesh.primitive_grid_add(x_subdivisions=160, y_subdivisions=160, size=1, location=(0, 0, 0)); h = bpy.context.active_object
h.name = "HILLS"; h.scale = (9000, 9000, 1); bpy.ops.object.transform_apply(scale=True)
random.seed(3)
cent = [(random.uniform(-4000, 4000), random.uniform(-4000, 4000), random.uniform(80, 320), random.uniform(300, 900)) for _ in range(40)]
cent += [(-200, 1500, 420, 700), (900, 1700, 300, 600), (-1500, -1800, 260, 700), (1800, -1600, 360, 800), (2600, 600, 250, 600)]
for v in h.data.vertices:
    x, y = v.co.x, v.co.y; z = 0.0
    for cx, cy, hh, rr in cent:
        d2 = ((x - cx) ** 2 + (y - cy) ** 2) / rr ** 2
        if d2 < 9: z += hh * math.exp(-d2)
    fade = min(1.0, max(0.0, (abs(y) - 250) / 500.0))    # flat near the runway strip
    v.co.z = z * fade - 0.5
h.location = L0; h.data.materials.append(M_hill)
bpy.ops.object.shade_smooth()
for cc in list(h.users_collection): cc.objects.unlink(h)
LC.objects.link(h)
# dress the landing field: Poly Haven trees and shrubs (CC0) in lines and clumps, runway edge lights
PH = "/home/user/work17/ph"
TP = coll("LAND_PROTO"); TP.hide_render = False
protos = []
for pid in ("island_tree_01", "shrub_01"):
    with bpy.data.libraries.load(f"{PH}/{pid}/{pid}_1k.blend") as (src, dst):
        dst.objects = list(src.objects)
    pc = D.collections.new("PROTO_" + pid)
    for o in dst.objects:
        if not o or o.type != 'MESH': continue
        if "LOD" in o.name and not o.name.endswith("LOD1"): continue
        pc.objects.link(o); o.location = (0, 0, 0)
        if len(o.data.vertices) > 120000:
            sc.collection.objects.link(o)
            dm = o.modifiers.new("dec", 'DECIMATE'); dm.ratio = 50000 / len(o.data.vertices)
            bpy.context.view_layer.update()
            nm = bpy.data.meshes.new_from_object(o.evaluated_get(bpy.context.evaluated_depsgraph_get()))
            o.modifiers.clear(); o.data = nm; sc.collection.objects.unlink(o)
    print("SETS proto", pid, [(o.name, len(o.data.vertices)) for o in pc.objects])
    protos.append((pid, pc))
for im in D.images:
    if im.name.startswith(("island_tree", "shrub_01")) and im.size[0] > 512: im.scale(512, 512)
bpy.ops.file.pack_all()
random.seed(11)
def inst(pc, loc, scale, rotz):
    e = D.objects.new("I_" + pc.name, None); e.instance_type = 'COLLECTION'; e.instance_collection = pc
    e.location = loc; e.scale = (scale,) * 3; e.rotation_euler = (0, 0, rotz); LC.objects.link(e)
tree_pc, shrub_pc = protos[0][1], protos[1][1]
def hz(x, y):
    z = 0.0
    for cx, cy, hh, rr in cent:
        d2 = ((x - cx) ** 2 + (y - cy) ** 2) / rr ** 2
        if d2 < 9: z += hh * math.exp(-d2)
    return z * min(1.0, max(0.0, (abs(y) - 250) / 500.0)) - 0.5
for side in (-1, 1):                     # tree lines along the field edges and clumps on the near hills
    for i in range(70):
        x = random.uniform(-1500, 1500); y = side * random.uniform(75, 260)
        if side > 0 and -320 < x < 160 and y < 175: continue          # hangar and tower apron
        inst(tree_pc, L0 + Vector((x, y, hz(x, y))), random.uniform(2.6, 4.0), random.uniform(0, 6.28))
    for i in range(90):
        x = random.uniform(-1200, 1200); y = side * random.uniform(45, 200)
        if side > 0 and -320 < x < 160 and y < 175: continue
        if side < 0 and 240 < x < 290 and y > -75: continue          # keep the van and its logo clear
        inst(shrub_pc, L0 + Vector((x, y, hz(x, y))), random.uniform(2.5, 4.5), random.uniform(0, 6.28))
for x, y in ((243, -52), (249, -46), (278, -50), (284, -44), (-310, -60), (-285, -66), (215, -40), (205, -34)):
    inst(shrub_pc, L0 + Vector((x, y, 0)), random.uniform(2.5, 3.5), random.uniform(0, 6.28))
for i in range(120):
    x = random.uniform(-3000, 3000); y = random.choice((-1, 1)) * random.uniform(500, 2500)
    inst(tree_pc, L0 + Vector((x, y, hz(x, y))), random.uniform(3.5, 6.0), random.uniform(0, 6.28))
for k in range(2):                       # keep protos out of the scene centre
    pass
M_post = mat("M_light_post", (0.85, 0.75, 0.2), 0.4); M_lamp = mat("M_light_lamp", (1.0, 0.95, 0.8), 0.2, emit=3.0)
lm_ = bmesh.new()
for x in range(-1180, 1181, 60):
    for sd in (-1, 1):
        bmesh.ops.create_cone(lm_, cap_ends=True, segments=10, radius1=0.09, radius2=0.09, depth=0.35, matrix=Matrix.Translation((x, sd * 24.5, 0.18)))
me = D.meshes.new("EDGE_LIGHTS"); lm_.to_mesh(me); lm_.free()
el = D.objects.new("EDGE_LIGHTS", me); el.location = L0; me.materials.append(M_post); LC.objects.link(el)
lm_ = bmesh.new()
for x in range(-1180, 1181, 60):
    for sd in (-1, 1):
        bmesh.ops.create_uvsphere(lm_, u_segments=10, v_segments=6, radius=0.11, matrix=Matrix.Translation((x, sd * 24.5, 0.4)))
me = D.meshes.new("EDGE_LAMPS"); lm_.to_mesh(me); lm_.free()
ek = D.objects.new("EDGE_LAMPS", me); ek.location = L0; me.materials.append(M_lamp); LC.objects.link(ek)
# airport: hangars (CC-BY ElectricL), control tower (CC-BY alecbeauregard), perimeter fence, more edge lights
def glb(name, path, size_ax, size):
    before = set(D.objects); bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in D.objects if o not in before]; ms = [o for o in new if o.type == 'MESH']
    for o in ms:
        mw = o.matrix_world.copy(); o.parent = None; o.matrix_world = mw
    for o in new:
        if o.type != 'MESH': D.objects.remove(o, do_unlink=True)
    bpy.ops.object.select_all(action='DESELECT')
    for o in ms: o.select_set(True)
    bpy.context.view_layer.objects.active = ms[0]; bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    if len(ms) > 1: bpy.ops.object.join()
    ob = bpy.context.view_layer.objects.active; ob.name = name
    pts = [v.co for v in ob.data.vertices]; mn = Vector([min(p[i] for p in pts) for i in range(3)]); mx = Vector([max(p[i] for p in pts) for i in range(3)])
    sc_ = size / (mx - mn)["xyz".index(size_ax)]
    ob.data.transform(Matrix.Scale(sc_, 4) @ Matrix.Translation(-Vector(((mn.x + mx.x) / 2, (mn.y + mx.y) / 2, mn.z))))
    for cc in list(ob.users_collection): cc.objects.unlink(ob)
    LC.objects.link(ob)
    pts = [v.co for v in ob.data.vertices]; print("SETS", name, [round(max(p[i] for p in pts) - min(p[i] for p in pts), 1) for i in range(3)])
    return ob
hg = glb("HANGAR", "/home/user/work17/models/hangar.glb", "z", 16.0)
for i, x in enumerate((-260, -170, -80, 10)):
    h_ = hg if i == 0 else hg.copy()
    if i: LC.objects.link(h_)
    h_.location = L0 + Vector((x, 120, 0)); h_.rotation_euler = (0, 0, R_(0))
tw = glb("TOWER", "/home/user/work17/models/tower.glb", "z", 34.0); tw.location = L0 + Vector((120, 110, 0))
M_fpost = mat("M_fence_post", (0.55, 0.57, 0.6), 0.4, 0.5)
M_mesh = D.materials.new("M_fence_mesh"); M_mesh.use_nodes = True; nt = M_mesh.node_tree; P = nt.nodes["Principled BSDF"]
tco = nt.nodes.new("ShaderNodeTexCoord"); br = nt.nodes.new("ShaderNodeTexBrick"); br.inputs["Scale"].default_value = 3.0; br.inputs["Mortar Size"].default_value = 0.012
nt.links.new(tco.outputs["Object"], br.inputs["Vector"])
br.offset = 0.0; br.squash = 1.0
inv = nt.nodes.new("ShaderNodeMath"); inv.operation = 'SUBTRACT'; inv.inputs[0].default_value = 1.0
nt.links.new(br.outputs["Fac"], inv.inputs[1]); nt.links.new(br.outputs["Fac"], P.inputs["Alpha"])
P.inputs["Base Color"].default_value = (0.6, 0.62, 0.64, 1); P.inputs["Metallic"].default_value = 0.6; P.inputs["Roughness"].default_value = 0.4
fb = bmesh.new(); pnl = bmesh.new()
for side, y in ((1, 62.0),):
    for x in range(-900, 901, 4):
        bmesh.ops.create_cone(fb, cap_ends=True, segments=8, radius1=0.04, radius2=0.04, depth=2.2, matrix=Matrix.Translation((x, y, 1.1)))
    bmesh.ops.create_cube(fb, size=1, matrix=Matrix.Translation((0, y, 2.18)) @ Matrix.Diagonal((1800, 0.05, 0.05, 1)))
    bmesh.ops.create_cube(pnl, size=1, matrix=Matrix.Translation((0, y, 1.1)) @ Matrix.Diagonal((1800, 0.01, 2.1, 1)))
me = D.meshes.new("FENCE_POSTS"); fb.to_mesh(me); fb.free(); fo_ = D.objects.new("FENCE_POSTS", me); fo_.location = L0; me.materials.append(M_fpost); LC.objects.link(fo_)
me = D.meshes.new("FENCE_MESH"); pnl.to_mesh(me); pnl.free(); fm_ = D.objects.new("FENCE_MESH", me); fm_.location = L0; me.materials.append(M_mesh); LC.objects.link(fm_)
# landing copy of the 737 (shares the mesh; landing shots look at its right side)
al = ap.copy(); al.name = "Airliner_LAND"; al.data = ap.data; coll("LANDING").objects.link(al)
al.location = L0 + Vector((0, 0, 0))
# simple main + nose gear (struts and twin tyres), parented to the landing copy
M_tyre = mat("M_tyre", (0.05, 0.05, 0.055), 0.8); M_strut = mat("M_strut", (0.75, 0.76, 0.78), 0.35, 0.6)
def gear(name, base_local, n_wheels=2, r=0.56, w=0.36, strut=1.9, sep=0.95):
    objs = []
    bpy.ops.mesh.primitive_cylinder_add(vertices=20, radius=0.11, depth=strut, location=(0, 0, 0)); s = bpy.context.active_object
    s.name = name + "_STRUT"; s.location = base_local + Vector((0, 0, -strut / 2)); s.data.materials.append(M_strut); objs.append(s)
    for k in range(n_wheels):
        bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=r, depth=w, location=(0, 0, 0)); t = bpy.context.active_object
        t.name = name + "_TYRE%d" % k; t.rotation_euler = (R_(90), 0, 0)
        t.location = base_local + Vector((0, (k - (n_wheels - 1) / 2) * sep, -strut))
        bv = t.modifiers.new("b", 'BEVEL'); bv.width = 0.12; bv.segments = 4
        t.data.materials.append(M_tyre); objs.append(t)
        bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=r * 0.55, depth=w + 0.02, location=(0, 0, 0)); hb = bpy.context.active_object
        hb.name = name + "_HUB%d" % k; hb.rotation_euler = (R_(90), 0, 0); hb.location = t.location; hb.data.materials.append(M_strut); objs.append(hb)
    for o in objs:
        bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); bpy.context.view_layer.objects.active = o; bpy.ops.object.shade_smooth()
        o.parent = al; o.matrix_parent_inverse = Matrix.Identity(4)
        for cc in list(o.users_collection): cc.objects.unlink(o)
        LC.objects.link(o)
    return objs
gear("GEAR_N", Vector((15.6, 0, 1.25)), r=0.38, w=0.25, strut=1.45, sep=0.6)
gear("GEAR_ML", Vector((-1.6, 2.9, 1.2)), strut=1.55, sep=0.95)
gear("GEAR_MR", Vector((-1.6, -2.9, 1.2)), strut=1.55, sep=0.95)
# white service van by the runway, our logo on its side (shot 23)
before = set(D.objects); bpy.ops.import_scene.gltf(filepath="/home/user/work17/models/van.glb")
new = [o for o in D.objects if o not in before]; ms = [o for o in new if o.type == 'MESH']
for o in ms:
    mw = o.matrix_world.copy(); o.parent = None; o.matrix_world = mw
for o in new:
    if o.type != 'MESH': D.objects.remove(o, do_unlink=True)
bpy.ops.object.select_all(action='DESELECT')
for o in ms: o.select_set(True)
bpy.context.view_layer.objects.active = ms[0]; bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
if len(ms) > 1: bpy.ops.object.join()
van = bpy.context.view_layer.objects.active; van.name = "VAN"
pts = [v.co for v in van.data.vertices]; mn = Vector([min(p[i] for p in pts) for i in range(3)]); mx = Vector([max(p[i] for p in pts) for i in range(3)])
dd = mx - mn; ax = 0 if dd.x > dd.y else 1; s_ = 5.3 / dd[ax]
van.data.transform(Matrix.Scale(s_, 4) @ Matrix.Translation(-Vector(((mn.x + mx.x) / 2, (mn.y + mx.y) / 2, mn.z))))
if ax == 1: van.data.transform(Matrix.Rotation(R_(90), 4, 'Z'))       # long axis along X
for cc in list(van.users_collection): cc.objects.unlink(van)
LC.objects.link(van); van.location = L0 + Vector((260, -48, 0.1))
pts = [v.co for v in van.data.vertices]; print("SETS van dims", [round(max(p[i] for p in pts) - min(p[i] for p in pts), 2) for i in range(3)])
ymin = min(p.y for p in pts); zc = (max(p.z for p in pts) + min(p.z for p in pts)) / 2
img = D.images.load("/home/user/Muhammed/blender/assets/brand/DaKrasFilms_logo_dark.png"); img.pack()
lm = D.materials.new("M_logo_van"); lm.use_nodes = True; lm.blend_method = 'BLEND' if hasattr(lm, "blend_method") else None
nt = lm.node_tree; P = nt.nodes["Principled BSDF"]; tx = nt.nodes.new("ShaderNodeTexImage"); tx.image = img
nt.links.new(tx.outputs["Color"], P.inputs["Base Color"]); nt.links.new(tx.outputs["Alpha"], P.inputs["Alpha"]); P.inputs["Roughness"].default_value = 0.4
bpy.ops.mesh.primitive_plane_add(size=1); lg = bpy.context.active_object; lg.name = "LOGO_VAN"
lg.scale = (2.0, 2.0 * 414 / 967, 1); bpy.ops.object.transform_apply(scale=True)
lg.rotation_euler = (R_(90), 0, 0); lg.location = (-0.35, ymin - 0.012, zc - 0.22)
lg.data.materials.append(lm); lg.parent = van; lg.matrix_parent_inverse = Matrix.Identity(4)
for cc in list(lg.users_collection): cc.objects.unlink(lg)
LC.objects.link(lg)
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print("SETS_OK")
