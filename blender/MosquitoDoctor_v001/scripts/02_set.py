"""B22 sets + props. Room (sick boy's bed + the doctor's desk, 1900 clinic, pale-blue walls, window), ward (x=40) with beds and
mosquito nets, mosquito (rigged Sketchfab Aedes), corked glass vial, notebook, pen, organ set, logo crates.
blender -b chars.blend --python 02_set.py -- scene.blend"""
import bpy, sys, os, math, bmesh, glob
from mathutils import Vector, Matrix
OUT = sys.argv[sys.argv.index("--") + 1]
HERE = os.path.dirname(os.path.abspath(__file__)); A = os.path.join(HERE, "..", "assets")
sc = bpy.context.scene; D = bpy.data.objects; V = Vector
def link(o, coll=None): (coll or sc.collection).objects.link(o); return o
def mat(name, rgb, rough=0.5, metal=0.0, alpha=1.0, trans=0.0, emit=None, ior=1.45, coat=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True; P = m.node_tree.nodes["Principled BSDF"]
    P.inputs["Base Color"].default_value = (*rgb, 1); P.inputs["Roughness"].default_value = rough
    P.inputs["Metallic"].default_value = metal; P.inputs["Alpha"].default_value = alpha
    P.inputs["Transmission Weight"].default_value = trans; P.inputs["IOR"].default_value = ior
    P.inputs["Coat Weight"].default_value = coat
    if emit: P.inputs["Emission Color"].default_value = (*emit[0], 1); P.inputs["Emission Strength"].default_value = emit[1]
    return m
def box(name, size, loc, m, bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc); o = bpy.context.object; o.name = name; o.scale = size
    bpy.ops.object.transform_apply(scale=True)
    if bevel:
        b = o.modifiers.new("bev", 'BEVEL'); b.width = bevel; b.segments = 2
    o.data.materials.append(m); return o
def append_ph(asset, want=None):
    p = glob.glob(f"{A}/ph/{asset}/*.blend")[0]
    with bpy.data.libraries.load(p, link=False) as (s, d):
        d.objects = [n for n in s.objects if (want is None or n in want)]
    obs = [o for o in d.objects if o is not None]
    for o in obs: link(o)
    return obs
def append_ph_mat(asset):
    p = glob.glob(f"{A}/ph/{asset}/*.blend")[0]
    with bpy.data.libraries.load(p, link=False) as (s, d): d.materials = list(s.materials)
    return d.materials[0]
def group(obs, name):
    e = bpy.data.objects.new(name, None); link(e)
    for o in obs:
        if o.parent is None: o.parent = e
    return e
def bbox(obs):
    bpy.context.view_layer.update()
    pts = [o.matrix_world @ V(c) for o in obs if o.type == 'MESH' for c in o.bound_box]
    return V([min(p[i] for p in pts) for i in range(3)]), V([max(p[i] for p in pts) for i in range(3)])
def import_glb(name):
    before = set(bpy.data.objects); bpy.ops.import_scene.gltf(filepath=f"{A}/{name}.glb")
    obs = [o for o in bpy.data.objects if o not in before]
    for o in list(obs):
        if o.type in ('CAMERA', 'LIGHT') or o.name.startswith(("Cube", "Icosphere")) and o.type == 'MESH' and len(o.data.vertices) < 100:
            obs.remove(o); bpy.data.objects.remove(o, do_unlink=True)
    return obs
def place(obs, name, size_axis, size, loc, rotz=0.0, floor=True):
    """root-group the imported objects, scale so the bbox extent on size_axis = size, sit on z=loc.z, rotate"""
    roots = [o for o in obs if o.parent is None or o.parent not in obs]
    e = bpy.data.objects.new(name, None); link(e)
    for o in roots: o.parent = e
    lo, hi = bbox(obs); k = size / (hi - lo)[size_axis]; e.scale = (k, k, k); bpy.context.view_layer.update()
    lo, hi = bbox(obs); c = (lo + hi) / 2
    e.location = V((-c.x, -c.y, -lo.z if floor else -c.z)); bpy.context.view_layer.update()
    e2 = bpy.data.objects.new(name + "_pivot", None); link(e2); e.parent = e2
    e2.location = loc; e2.rotation_euler = (0, 0, math.radians(rotz)); bpy.context.view_layer.update()
    lo, hi = bbox(obs); print("SET", name, "bbox", [round(x, 2) for x in lo], [round(x, 2) for x in hi])
    return e2

# ------------------------------------------------------------------ materials
M_WALL = mat("Wall_paleblue", (0.50, 0.70, 0.82), 0.8)
M_TRIM = mat("Trim_white", (0.92, 0.92, 0.90), 0.35)
M_CEIL = mat("Ceiling", (0.93, 0.93, 0.92), 0.9)
M_FLOOR = append_ph_mat("wood_floor_deck"); M_FLOOR.name = "Floor_wood"
for n in M_FLOOR.node_tree.nodes:
    if n.type == 'NORMAL_MAP': n.inputs['Strength'].default_value = 0.3
    if n.type == 'DISPLACEMENT': n.inputs['Scale'].default_value = 0.0
M_SKY = bpy.data.materials.new("WindowSky"); M_SKY.use_nodes = True
nt = M_SKY.node_tree; nt.nodes.clear()
tc = nt.nodes.new("ShaderNodeTexCoord"); sep = nt.nodes.new("ShaderNodeSeparateXYZ"); ramp = nt.nodes.new("ShaderNodeValToRGB")
em = nt.nodes.new("ShaderNodeEmission"); outn = nt.nodes.new("ShaderNodeOutputMaterial")
nt.links.new(tc.outputs["Generated"], sep.inputs[0]); nt.links.new(sep.outputs["Z"], ramp.inputs[0])
ramp.color_ramp.elements[0].color = (0.91, 0.97, 1.0, 1); ramp.color_ramp.elements[1].color = (0.31, 0.76, 0.97, 1)
nt.links.new(ramp.outputs[0], em.inputs[0]); em.inputs[1].default_value = 1.6; nt.links.new(em.outputs[0], outn.inputs[0])

# ------------------------------------------------------------------ ROOM (origin): x -3..3, y -3..3, back wall y=3
RM = []
fl = box("Room_Floor", (7, 7, 0.04), (0, 0, -0.02), M_FLOOR); RM.append(fl)
uv = fl.modifiers.new("uv", 'UV_PROJECT') if False else None
bpy.context.view_layer.objects.active = fl; bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.cube_project(cube_size=2.0); bpy.ops.object.mode_set(mode='OBJECT')
H = 3.2
def wall_with_window(name, axis, pos, length, win=None, center=0.0):
    """wall plane along x (axis='y': wall at y=pos) or along y (axis='x'); win=(c, w, z0, z1) cut-out"""
    obs = []
    th = 0.12
    def seg(n, a0, a1, z0, z1):
        if a1 - a0 < 1e-3 or z1 - z0 < 1e-3: return
        c = (a0 + a1) / 2; z = (z0 + z1) / 2
        if axis == 'y': o = box(n, (a1 - a0, th, z1 - z0), (c, pos, z), M_WALL)
        else: o = box(n, (th, a1 - a0, z1 - z0), (pos, c, z), M_WALL)
        obs.append(o)
    a0, a1 = center - length / 2, center + length / 2
    if win:
        c, w, z0, z1 = win
        seg(name + "_L", a0, c - w / 2, 0, H); seg(name + "_R", c + w / 2, a1, 0, H)
        seg(name + "_B", c - w / 2, c + w / 2, 0, z0); seg(name + "_T", c - w / 2, c + w / 2, z1, H)
    else:
        seg(name, a0, a1, 0, H)
    # skirting + chair rail
    for zc, hh, nm in ((0.08, 0.16, "Skirt"), (0.95, 0.05, "Rail")):
        if axis == 'y': o = box(f"{name}_{nm}", (length, 0.03, hh), (center, pos - 0.075 * (1 if pos > 0 else -1), zc), M_TRIM)
        else: o = box(f"{name}_{nm}", (0.03, length, hh), (pos - 0.075 * (1 if pos > 0 else -1), center, zc), M_TRIM)
        obs.append(o)
    return obs
RM += wall_with_window("Room_Back", 'y', 3.0, 7.0, win=(0.9, 1.3, 0.9, 2.5))
RM += wall_with_window("Room_Left", 'x', -3.0, 7.0, win=(0.0, 1.1, 0.9, 2.4))
RM += wall_with_window("Room_Right", 'x', 3.0, 7.0)
RM.append(box("Room_Ceiling", (7, 7, 0.05), (0, 0, H + 0.02), M_CEIL))
def window(name, axis, pos, c, w, z0, z1, sky_off=1.5):
    obs = []
    t = 0.06
    if axis == 'y':
        for (sx, sz, lx, lz) in ((w, t, c, z0 + t / 2), (w, t, c, z1 - t / 2), (t, z1 - z0, c - w / 2 + t / 2, (z0 + z1) / 2),
                                 (t, z1 - z0, c + w / 2 - t / 2, (z0 + z1) / 2), (t * 0.6, z1 - z0, c, (z0 + z1) / 2),
                                 (w, t * 0.6, c, z0 + (z1 - z0) * 0.55)):
            obs.append(box(name + "_frame", (sx, 0.14 if sx < sz else 0.12, sz), (lx, pos, lz), M_TRIM))
        obs.append(box(name + "_sill", (w + 0.16, 0.22, 0.04), (c, pos - 0.08, z0 - 0.02), M_TRIM))
        sky = box(name + "_sky", (w * 4, 0.02, (z1 - z0) * 3.5), (c, pos + sky_off, (z0 + z1) / 2 + 0.6), M_SKY)
    else:
        for (sy, sz, ly, lz) in ((w, t, c, z0 + t / 2), (w, t, c, z1 - t / 2), (t, z1 - z0, c - w / 2 + t / 2, (z0 + z1) / 2),
                                 (t, z1 - z0, c + w / 2 - t / 2, (z0 + z1) / 2), (t * 0.6, z1 - z0, c, (z0 + z1) / 2),
                                 (w, t * 0.6, c, z0 + (z1 - z0) * 0.55)):
            obs.append(box(name + "_frame", (0.14 if sy < sz else 0.12, sy, sz), (pos, ly, lz), M_TRIM))
        obs.append(box(name + "_sill", (0.22, w + 0.16, 0.04), (pos + 0.08, c, z0 - 0.02), M_TRIM))
        sky = box(name + "_sky", (0.02, w * 4, (z1 - z0) * 3.5), (pos - sky_off, c, (z0 + z1) / 2 + 0.6), M_SKY)
    sky.visible_shadow = False; sky.visible_diffuse = False
    obs.append(sky); return obs
RM += window("Room_WinBack", 'y', 3.0, 0.9, 1.3, 0.9, 2.5)
RM += window("Room_WinLeft", 'x', -3.0, 0.0, 1.1, 0.9, 2.4)

# boy's iron bed against the left wall, head at the back (y+)
bed = import_glb("bed")
BED = place(bed, "BoyBed", 0, 1.95, V((-1.4, 1.0, 0)), rotz=90)
for o in bed:
    if o.type != 'MESH': continue
    for sl in o.material_slots:
        m = sl.material.copy(); sl.material = m; P = m.node_tree.nodes.get("Principled BSDF")
        if not P: continue
        nm = o.name.lower()
        for l in list(P.inputs["Base Color"].links): m.node_tree.links.remove(l)
        for l in list(P.inputs["Roughness"].links): m.node_tree.links.remove(l)
        if "bed_0" in nm: P.inputs["Base Color"].default_value = (0.90, 0.90, 0.88, 1); P.inputs["Roughness"].default_value = 0.35
        elif "lagen" in nm: P.inputs["Base Color"].default_value = (0.85, 0.90, 0.95, 1); P.inputs["Roughness"].default_value = 0.8
        else: P.inputs["Base Color"].default_value = (0.97, 0.97, 0.95, 1); P.inputs["Roughness"].default_value = 0.8
# desk (free-standing, doctor sits behind it facing -y)
desk = import_glb("desk")
DESK = place(desk, "Desk", 0, 1.62, V((1.4, 1.5, 0)), rotz=0)
chair = append_ph("dining_chair_02")
CHAIR = place(chair, "DeskChair", 2, 0.95, V((1.4, 2.25, 0)), rotz=180)
shelf = append_ph("wooden_bookshelf_worn"); SHELF = place(shelf, "Bookshelf", 2, 1.9, V((2.55, 2.75, 0)), rotz=0)
books = append_ph("book_encyclopedia_set_01"); BOOKS = place(books, "Books", 0, 0.62, V((2.55, 2.70, 1.02)), rotz=0)
lamp = append_ph("vintage_oil_lamp"); LAMP = place(lamp, "OilLamp", 2, 0.42, V((0.85, 1.55, 0.0)), rotz=20)
cab = append_ph("vintage_cabinet_01"); CAB = place(cab, "Cabinet", 2, 1.0, V((-0.6, 2.72, 0)), rotz=0)
pic = append_ph("hanging_picture_frame_01"); PIC = place(pic, "Picture", 0, 0.6, V((-2.92, -1.2, 1.55)), rotz=90, floor=False)
bucket = append_ph("wooden_bucket_01"); BUCKET = place(bucket, "Basin", 2, 0.28, V((0.55, 2.35, 0)), rotz=0)
crate = append_ph("wooden_crate_01"); CRATE = place(crate, "CrateRoom", 0, 0.55, V((-1.0, 2.55, 0)), rotz=8)
print("DESKTOP")
lo, hi = bbox(desk); DESK_TOP = hi.z; print("DESK top z", round(DESK_TOP, 3), [round(x, 2) for x in lo], [round(x, 2) for x in hi])
LAMP.location.z = DESK_TOP; LAMP.location.y = 1.3
lo, hi = bbox(bed); print("BED top z", round(hi.z, 3))

# ------------------------------------------------------------------ props
# glass vial: lathe profile (radius, z) in metres, open top with a lip; cork separate
def lathe(name, prof, m, seg=40):
    bm = bmesh.new(); rings = []
    for r, z in prof:
        ring = [bm.verts.new((r * math.cos(2 * math.pi * i / seg), r * math.sin(2 * math.pi * i / seg), z)) for i in range(seg)]
        rings.append(ring)
    for a, b in zip(rings, rings[1:]):
        for i in range(seg):
            bm.faces.new((a[i], a[(i + 1) % seg], b[(i + 1) % seg], b[i]))
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); link(o); me.materials.append(m)
    for p in me.polygons: p.use_smooth = True
    return o
M_GLASS = bpy.data.materials.new("VialGlass"); M_GLASS.use_nodes = True
nt = M_GLASS.node_tree; nt.nodes.clear()
lw = nt.nodes.new("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.25
tr = nt.nodes.new("ShaderNodeBsdfTransparent"); tr.inputs[0].default_value = (0.90, 0.96, 1.0, 1)
gl = nt.nodes.new("ShaderNodeBsdfPrincipled"); gl.inputs["Base Color"].default_value = (0.85, 0.93, 1.0, 1); gl.inputs["Roughness"].default_value = 0.08
gl.inputs["Coat Weight"].default_value = 1.0
mxg = nt.nodes.new("ShaderNodeMixShader"); om = nt.nodes.new("ShaderNodeOutputMaterial")
ad = nt.nodes.new("ShaderNodeMath"); ad.operation = 'ADD'; ad.inputs[1].default_value = 0.12; ad.use_clamp = True
nt.links.new(lw.outputs["Facing"], ad.inputs[0]); nt.links.new(ad.outputs[0], mxg.inputs[0])
nt.links.new(tr.outputs[0], mxg.inputs[1]); nt.links.new(gl.outputs[0], mxg.inputs[2]); nt.links.new(mxg.outputs[0], om.inputs[0])
VR, VL = 0.011, 0.075        # outer radius, length
prof = [(0.0001, 0.0), (VR * 0.6, 0.0015), (VR * 0.92, 0.005), (VR, 0.011), (VR, VL - 0.006), (VR * 1.12, VL - 0.004), (VR * 1.12, VL),
        (VR * 0.86, VL), (VR * 0.86, VL - 0.006), (VR * 0.86, 0.012), (VR * 0.8, 0.0055), (VR * 0.5, 0.0028), (0.0001, 0.002)]
VIAL = lathe("Vial", prof, M_GLASS)
M_CORK = mat("Cork", (0.62, 0.42, 0.24), 0.75)
CORK = lathe("Cork", [(0.0001, VL - 0.012), (VR * 0.86, VL - 0.012), (VR * 0.9, VL + 0.002), (VR * 1.0, VL + 0.010), (0.0001, VL + 0.010)], M_CORK)
CORK.parent = VIAL
# notebook: open, two slightly curved page blocks on a cover
M_PAPER = bpy.data.materials.new("Paper"); M_PAPER.use_nodes = True
nt = M_PAPER.node_tree; P = nt.nodes["Principled BSDF"]; P.inputs["Roughness"].default_value = 0.85
tc = nt.nodes.new("ShaderNodeTexCoord"); wv = nt.nodes.new("ShaderNodeTexWave"); wv.wave_type = 'BANDS'; wv.bands_direction = 'Y'
wv.inputs["Scale"].default_value = 28; wv.inputs["Distortion"].default_value = 0
cr = nt.nodes.new("ShaderNodeValToRGB"); cr.color_ramp.elements[0].position = 0.93; cr.color_ramp.elements[0].color = (0.96, 0.94, 0.88, 1)
cr.color_ramp.elements[1].position = 0.97; cr.color_ramp.elements[1].color = (0.62, 0.70, 0.85, 1)
nt.links.new(tc.outputs["Generated"], wv.inputs["Vector"]); nt.links.new(wv.outputs["Fac"], cr.inputs[0]); nt.links.new(cr.outputs[0], P.inputs["Base Color"])
M_COVER = mat("BookCover", (0.35, 0.12, 0.08), 0.5)
def page(name, side):
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=12, y_subdivisions=2, size=1); o = bpy.context.object; o.name = name
    for v in o.data.vertices:
        x = (v.co.x + 0.5) * 0.15; v.co = V((side * x, v.co.y * 0.21, 0.004 + 0.010 * math.sin(math.pi * min(1, x / 0.15) * 0.5) * (1 - x / 0.15) + 0.006 * (x / 0.15)))
    o.data.materials.append(M_PAPER); s = o.modifiers.new("s", 'SOLIDIFY'); s.thickness = 0.004; return o
NB = bpy.data.objects.new("Notebook", None); link(NB)
for nm, sd in (("NB_PageL", -1), ("NB_PageR", 1)): page(nm, sd).parent = NB
cov = box("NB_Cover", (0.31, 0.22, 0.003), (0, 0, 0.0015), M_COVER); cov.parent = NB
NB.location = V((1.38, 1.18, DESK_TOP)); NB.rotation_euler = (0, 0, math.radians(180))
# a mosquito sketch on the right page: thin dark strokes (no text)
M_INK = mat("Ink", (0.05, 0.05, 0.08), 0.6)
bpy.ops.curve.primitive_bezier_circle_add(radius=0.022, location=(0, 0, 0)); sk = bpy.context.object; sk.name = "NB_Sketch"
sk.data.bevel_depth = 0.0006; sk.scale = (1.0, 0.45, 1); sk.data.materials.append(M_INK)
sk.parent = NB; sk.location = (-0.07, 0.03, 0.0175)
for i, (a, l) in enumerate(((30, 0.05), (90, 0.05), (150, 0.05), (210, 0.05), (270, 0.05), (330, 0.05))):
    bpy.ops.curve.primitive_bezier_curve_add(location=(0, 0, 0)); c = bpy.context.object; c.name = f"NB_Leg{i}"
    sp = c.data.splines[0]; ra = math.radians(a)
    sp.bezier_points[0].co = V((0.02 * math.cos(ra), 0.009 * math.sin(ra), 0)); sp.bezier_points[1].co = V((l * math.cos(ra), l * 0.7 * math.sin(ra), 0))
    for bp in sp.bezier_points: bp.handle_left_type = bp.handle_right_type = 'VECTOR'
    c.data.bevel_depth = 0.0004; c.data.materials.append(M_INK); c.parent = NB; c.location = (-0.07, 0.03, 0.0175)
# dip pen + inkwell
PEN = lathe("Pen", [(0.0001, 0.0), (0.0012, 0.004), (0.0030, 0.02), (0.0038, 0.05), (0.0040, 0.15), (0.0001, 0.152)], mat("PenBlack", (0.04, 0.04, 0.05), 0.3))
PEN.location = V((1.62, 1.2, DESK_TOP + 0.005)); PEN.rotation_euler = (0, math.radians(90), math.radians(20))
INKW = lathe("Inkwell", [(0.0001, 0), (0.028, 0), (0.03, 0.03), (0.012, 0.045), (0.012, 0.055), (0.0001, 0.055)], mat("InkwellGlass", (0.1, 0.12, 0.2), 0.1))
INKW.location = V((1.80, 1.25, DESK_TOP))
# floor stain (black sludge, mild): flattened glossy blob by the basin
bpy.ops.mesh.primitive_circle_add(vertices=48, radius=0.10, fill_type='NGON', location=(0.70, 2.24, 0.002)); st = bpy.context.object; st.name = "FloorStain"
for i, v in enumerate(st.data.vertices):
    if v.co.length > 1e-4: v.co *= 1 + 0.10 * math.sin(i * 2 * math.pi / 48 * 3) + 0.06 * math.cos(i * 2 * math.pi / 48 * 5)
st.scale = (1.25, 0.85, 1); st.data.materials.append(mat("Sludge", (0.03, 0.025, 0.02), 0.15))
st.hide_render = True; st.hide_viewport = True

# ------------------------------------------------------------------ mosquito (rigged Aedes, Sketchfab CC-BY)
mq = import_glb("aedes")
MQA = next(o for o in mq if o.type == 'ARMATURE'); MQA.name = "MosqRig"
MQA.animation_data_clear()
for o in mq:
    if o.type == 'MESH' and o.parent and o.parent.type == 'ARMATURE': pass
top = [o for o in mq if o.parent is None][0]
MQ = bpy.data.objects.new("Mosquito", None); link(MQ); top.parent = MQ
S_MQ = 0.0018; top.scale = (S_MQ, S_MQ, S_MQ)
for o in mq:
    if o.type == 'EMPTY' and o not in (top,) and not any(c.type in ('MESH', 'ARMATURE') for c in o.children_recursive): o.hide_render = True
names = {"AntenaEsquerda_0": "MQ_Body", "AntenaEsquerda_4": "MQ_Bristles", "AntenaEsquerda_1": "MQ_Wings", "AntenaEsquerda_2": "MQ_Head",
         "AntenaEsquerda.002_0": "MQ_Proboscis", "AntenaEsquerda_3": "MQ_Gut"}
for o in mq:
    if o.name in names: o.name = names[o.name]
def setmat(o, m):
    o.data.materials.clear(); o.data.materials.append(m)
M_MQ = bpy.data.materials.new("MQ_BodyMat"); M_MQ.use_nodes = True
nt = M_MQ.node_tree; P = nt.nodes["Principled BSDF"]; P.inputs["Roughness"].default_value = 0.4; P.inputs["Coat Weight"].default_value = 0.3
tc = nt.nodes.new("ShaderNodeTexCoord"); sep = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(tc.outputs["Generated"], sep.inputs[0])
# white bands along the legs and abdomen (Aedes): bands in generated Y
wv = nt.nodes.new("ShaderNodeTexWave"); wv.wave_type = 'BANDS'; wv.bands_direction = 'Y'; wv.inputs["Scale"].default_value = 9; wv.inputs["Distortion"].default_value = 0
nt.links.new(tc.outputs["Generated"], wv.inputs["Vector"])
cr = nt.nodes.new("ShaderNodeValToRGB"); cr.color_ramp.elements[0].position = 0.8; cr.color_ramp.elements[0].color = (0.035, 0.035, 0.04, 1)
cr.color_ramp.elements[1].position = 0.86; cr.color_ramp.elements[1].color = (0.85, 0.85, 0.85, 1)
nt.links.new(wv.outputs["Fac"], cr.inputs[0])
# abdomen mask (generated x 0.39-0.61, y 0.33-0.63) -> blood-red tint driven by the 'Feed' value (keyed)
fv = nt.nodes.new("ShaderNodeValue"); fv.name = "Feed"; fv.outputs[0].default_value = 0.0
mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = 'RGBA'; nt.links.new(cr.outputs[0], mx.inputs[6]); mx.inputs[7].default_value = (0.75, 0.04, 0.03, 1)
def rng(sock, lo, hi):
    a = nt.nodes.new("ShaderNodeMath"); a.operation = 'GREATER_THAN'; nt.links.new(sock, a.inputs[0]); a.inputs[1].default_value = lo
    b = nt.nodes.new("ShaderNodeMath"); b.operation = 'LESS_THAN'; nt.links.new(sock, b.inputs[0]); b.inputs[1].default_value = hi
    c = nt.nodes.new("ShaderNodeMath"); c.operation = 'MULTIPLY'; nt.links.new(a.outputs[0], c.inputs[0]); nt.links.new(b.outputs[0], c.inputs[1]); return c.outputs[0]
mk = nt.nodes.new("ShaderNodeMath"); mk.operation = 'MULTIPLY'; nt.links.new(rng(sep.outputs["X"], 0.40, 0.60), mk.inputs[0]); nt.links.new(rng(sep.outputs["Y"], 0.33, 0.62), mk.inputs[1])
mk2 = nt.nodes.new("ShaderNodeMath"); mk2.operation = 'MULTIPLY'; nt.links.new(mk.outputs[0], mk2.inputs[0]); nt.links.new(fv.outputs[0], mk2.inputs[1])
nt.links.new(mk2.outputs[0], mx.inputs[0]); nt.links.new(mx.outputs[2], P.inputs["Base Color"])
setmat(D["MQ_Body"], M_MQ); setmat(D["MQ_Bristles"], mat("MQ_BristleMat", (0.05, 0.05, 0.05), 0.5))
setmat(D["MQ_Head"], mat("MQ_HeadMat", (0.06, 0.06, 0.07), 0.3, coat=0.5)); setmat(D["MQ_Proboscis"], mat("MQ_ProbMat", (0.05, 0.05, 0.05), 0.4))
setmat(D["MQ_Gut"], mat("MQ_GutMat", (0.6, 0.05, 0.04), 0.4)); D["MQ_Gut"].hide_render = True; D["MQ_Gut"].hide_viewport = True
mw = mat("MQ_WingMat", (0.85, 0.9, 0.95), 0.15, alpha=0.35); setmat(D["MQ_Wings"], mw)
# a second mosquito for the vial (same rig, copied)
MQ.location = V((30, 0, 0))

# ------------------------------------------------------------------ organs: Sketchfab 'Human Organs' + lungs/heart from RooseveltSpeech
org = import_glb("organs"); ORG = place(org, "Organs", 2, 0.42, V((60, 0, 1.0)), floor=False)
# ------------------------------------------------------------------ ward at x=40: 7 m wide, 16 m long, beds both sides with nets
WX = 40.0
WD = []
wf = box("Ward_Floor", (8, 18, 0.04), (WX, 0, -0.02), M_FLOOR); WD.append(wf)
bpy.context.view_layer.objects.active = wf; bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.cube_project(cube_size=2.0); bpy.ops.object.mode_set(mode='OBJECT')
M_WARDWALL = mat("WardWall", (0.62, 0.85, 0.86), 0.8)
for side in (-1, 1):
    x = WX + side * 3.6
    segs = []
    for k in range(-4, 5):
        y = k * 2.0
        segs.append(box("Ward_Wall", (0.12, 1.0, H), (x, y - 0.5, H / 2), M_WARDWALL))
        segs.append(box("Ward_WallLow", (0.12, 1.0, 1.0), (x, y + 0.5, 0.5), M_WARDWALL))
        segs.append(box("Ward_WallHi", (0.12, 1.0, 0.6), (x, y + 0.5, H - 0.3), M_WARDWALL))
        sky = box("Ward_Sky", (0.02, 1.0, 1.7), (x + side * 0.4, y + 0.5, 1.85), M_SKY); sky.visible_shadow = False; sky.visible_diffuse = False
        segs.append(box("Ward_WinFrame", (0.12, 1.0, 0.05), (x, y + 0.5, 1.0), M_TRIM))
        segs.append(box("Ward_WinFrame", (0.14, 0.05, 1.6), (x, y + 0.5, 1.8), M_TRIM))
    WD += segs
WD.append(box("Ward_End", (8, 0.12, H), (WX, 9.0, H / 2), M_WARDWALL)); WD.append(box("Ward_Ceiling", (8, 18, 0.05), (WX, 0, H + 0.02), M_CEIL))
M_NET = mat("Net", (0.90, 0.92, 0.92), 1.0, alpha=0.10)
M_NET.node_tree.nodes["Principled BSDF"].inputs["Specular IOR Level"].default_value = 0.0
WARD_BEDS = []
# one bed template in its own collection (not in the view layer), instanced 14 times: keeps the file small
TPL = bpy.data.collections.new("WardBedTpl"); sc.collection.children.link(TPL)
bo = import_glb("bed")
for o in bo:
    for c in list(o.users_collection): c.objects.unlink(o)
    TPL.objects.link(o)
    if o.type == 'MESH':
        for sl in o.material_slots:
            m = sl.material.copy(); sl.material = m; P = m.node_tree.nodes.get("Principled BSDF")
            for l in list(P.inputs["Base Color"].links): m.node_tree.links.remove(l)
            for l in list(P.inputs["Roughness"].links): m.node_tree.links.remove(l)
            nm = o.name.lower()
            P.inputs["Base Color"].default_value = (0.90, 0.90, 0.88, 1) if "bed_0" in nm else (0.97, 0.97, 0.95, 1)
            P.inputs["Roughness"].default_value = 0.35 if "bed_0" in nm else 0.8
roots = [o for o in bo if o.parent is None]
te = bpy.data.objects.new("WardBedTplRoot", None); TPL.objects.link(te)
for o in roots: o.parent = te
lo, hi = bbox(bo); k_ = 1.95 / (hi - lo).x; te.scale = (k_,) * 3; bpy.context.view_layer.update()
lo, hi = bbox(bo); c_ = (lo + hi) / 2; te.location = V((-c_.x, -c_.y, -lo.z)); bpy.context.view_layer.update()
lo, hi = bbox(bo); print("WARD bed tpl", [round(x, 2) for x in lo], [round(x, 2) for x in hi])
sc.view_layers[0].layer_collection.children["WardBedTpl"].exclude = True
for side in (-1, 1):
    for k in range(-3, 4):
        y = k * 2.0 + 0.5
        inst = bpy.data.objects.new(f"WardBed_{side}_{k}", None); link(inst)
        inst.instance_type = 'COLLECTION'; inst.instance_collection = TPL; inst.location = V((WX + side * 2.5, y, 0))
        if side > 0: inst.rotation_euler = (0, 0, math.pi)     # pillows at the wall on both sides
        net = box(f"Net_{side}_{k}", (hi.x - lo.x + 0.1, hi.y - lo.y + 0.1, 2.05 - 0.45), (WX + side * 2.5, y, 0.45 + (2.05 - 0.45) / 2), M_NET)
        net.visible_shadow = False
        bpy.context.view_layer.objects.active = net; bpy.ops.object.mode_set(mode='EDIT'); bm = bmesh.from_edit_mesh(net.data)
        for f in [f for f in bm.faces if f.normal.z < -0.5]: bm.faces.remove(f)
        bmesh.update_edit_mesh(net.data); bpy.ops.object.mode_set(mode='OBJECT')
        WARD_BEDS.append((inst, net))
cr2 = append_ph("wooden_crate_01"); CRATE2 = place(cr2, "CrateWard", 0, 0.6, V((WX + 0.9, 7.6, 0)), rotz=-5)
# logo decals (dark logo on the light crate sides): thin planes parented to the crates
for crn, loc, rz in (("CrateRoom", None, 8), ("CrateWard", None, -5)):
    pass
# ------------------------------------------------------------------ lighting: high-key, soft
w = bpy.data.worlds.new("World"); sc.world = w; w.use_nodes = True
bg = w.node_tree.nodes["Background"]; bg.inputs[0].default_value = (0.75, 0.86, 1.0, 1); bg.inputs[1].default_value = 0.7
sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", 'SUN')); link(sun)
sun.data.energy = 3.0; sun.data.angle = math.radians(8); sun.data.color = (1.0, 0.96, 0.9)
sun.rotation_euler = (math.radians(50), 0, math.radians(200))
for nm, loc, sz, en in (("RoomCeilLight", (0, 0.2, 3.1), 4.0, 600), ("WardCeilLightA", (WX, -4, 3.1), 6.0, 700), ("WardCeilLightB", (WX, 4, 3.1), 6.0, 700)):
    L = bpy.data.objects.new(nm, bpy.data.lights.new(nm, 'AREA')); link(L); L.location = loc
    L.data.shape = 'SQUARE'; L.data.size = sz; L.data.energy = en; L.data.color = (1.0, 0.98, 0.95)
# window light: area lights just outside the windows pointing in
for nm, loc, rot, en in (("WinBackLight", (0.9, 3.4, 1.7), (math.radians(-90), 0, 0), 300), ("WinLeftLight", (-3.4, 0, 1.65), (0, math.radians(-90), 0), 250)):
    L = bpy.data.objects.new(nm, bpy.data.lights.new(nm, 'AREA')); link(L); L.location = loc; L.rotation_euler = rot
    L.data.size = 1.4; L.data.energy = en
print("SET done")
sc.render.engine = 'CYCLES'; sc.render.resolution_x, sc.render.resolution_y = 1080, 1920; sc.render.fps = 60
sc.view_settings.view_transform = 'AgX'
try: sc.view_settings.look = 'AgX - Punchy'
except Exception as e: print("look", e)
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
