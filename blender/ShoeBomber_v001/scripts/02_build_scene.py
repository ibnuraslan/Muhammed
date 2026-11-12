"""ShoeBomber sets: cabin (origin), studio (x=200), sky (x=-2000,z=600), airport (x=400). Appends the humans.
blender -b --factory-startup --python 02_build_scene.py -- <humans.blend> <out.blend>"""
import sys, os, math, random
import bpy, bmesh
from mathutils import Vector, Matrix
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sb_lib as L
a = sys.argv[sys.argv.index("--") + 1:]
HUM, OUT = a[0], a[1]
random.seed(7)
sc = bpy.context.scene
for o in list(bpy.data.objects): bpy.data.objects.remove(o)
sc.render.fps = 60; sc.render.fps_base = 1.0; sc.frame_start, sc.frame_end = 1, 1620
sc.render.resolution_x, sc.render.resolution_y = 1080, 1920
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'
V = Vector
TEX = "/opt/assets/sb_tex/"

# ------------------------------------------------------------------ materials
M = {}
M["carpet"] = L.tex_mat("Carpet", "dirty_carpet", 3.0, tint=(0.42, 0.45, 0.62), bump=0.5)
M["wall"] = L.mat("CabinWall", (0.55, 0.54, 0.52), 0.45)
M["bin"] = L.mat("BinPlastic", (0.82, 0.81, 0.78), 0.35)
M["trim"] = L.mat("TrimGrey", (0.32, 0.33, 0.35), 0.4)
M["metal"] = L.mat("BrushedMetal", (0.7, 0.71, 0.72), 0.28, 1.0)
M["glow_blue"] = L.mat("CoveGlow", (0.1, 0.1, 0.1), 0.5, emit=(0.35, 0.5, 1.0), estr=0.5)
M["glow_warm"] = L.mat("ReadingGlow", (0.9, 0.9, 0.9), 0.5, emit=(1.0, 0.82, 0.6), estr=30.0)
M["glow_off"] = L.mat("ReadingOff", (0.6, 0.6, 0.6), 0.3)
M["headrest"] = L.mat("HeadrestCloth", (0.86, 0.86, 0.84), 0.9)
M["seatfab"] = L.mat("SeatFabric", (0.07, 0.09, 0.16), 0.85)
M["blanket"] = L.tex_mat("Blanket", "denim_fabric", 2.0, tint=(0.5, 0.25, 0.25), bump=0.6)
M["dark"] = L.mat("DarkPlastic", (0.05, 0.05, 0.055), 0.4)
M["cup"] = L.mat("PaperCup", (0.92, 0.92, 0.9), 0.6)
M["can"] = L.mat("CanRed", (0.55, 0.08, 0.06), 0.25, 0.8)
M["can2"] = L.mat("CanSilver", (0.7, 0.72, 0.74), 0.2, 1.0)

# ------------------------------------------------------------------ CABIN
C = "Cabin"
Y0, Y1 = -4.0, 9.5
def shell():
    """inner fuselage: ellipse profile x=+-1.82 at z~0.9, ceiling 2.2"""
    bm = bmesh.new()
    prof = []
    for i in range(41):
        t = math.radians(-35 + i * (215 + 35 - (-35) - 215) / 40)  # placeholder, replaced below
    angs = [math.radians(-38 + k * (218 / 40.0)) for k in range(41)]   # -38..180  (right side up and over)
    pts = []
    for an in angs:
        x = 1.85 * math.cos(an); z = 0.95 + 1.32 * math.sin(an)
        pts.append((x, max(0.0, z)))
    # mirror to the left side
    full = [(-x, z) for x, z in reversed(pts)] + pts[1:]
    full = [p for p in full]
    ns = int((Y1 - Y0) / 0.25)
    rows = []
    for j in range(ns + 1):
        y = Y0 + j * (Y1 - Y0) / ns
        rows.append([bm.verts.new((x, y, z)) for x, z in full])
    for j in range(ns):
        for i in range(len(full) - 1):
            bm.faces.new((rows[j][i], rows[j][i + 1], rows[j + 1][i + 1], rows[j + 1][i]))
    me = bpy.data.meshes.new("CabinShell"); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new("CabinShell", me); L.coll(C).objects.link(o); L.set_mat(o, M["wall"])
    for p in me.polygons: p.use_smooth = True
    return o
shell()
fl = L.add_box("CabinFloor", (3.6, Y1 - Y0, 0.05), (0, (Y0 + Y1) / 2, -0.025), M["carpet"], C)
# UVs for carpet: box project via smart UV
bpy.context.view_layer.objects.active = fl
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT'); bpy.ops.uv.cube_project(cube_size=1.0); bpy.ops.object.mode_set(mode='OBJECT')
# bulkheads
L.add_box("BulkheadFwd", (3.8, 0.08, 2.4), (0, Y1, 1.1), M["wall"], C)
L.add_box("BulkheadAft", (3.8, 0.08, 2.4), (0, Y0, 1.1), M["wall"], C)
curtain = L.add_box("GalleyCurtain", (0.9, 0.03, 1.9), (0, Y1 - 0.1, 0.95), L.mat("CurtainBlue", (0.12, 0.16, 0.32), 0.9), C)
L.add_box("GalleyGlow", (0.85, 0.01, 0.06), (0, Y1 - 0.13, 1.93), L.mat("GalleyGlowDim", (0.9, 0.9, 0.9), 0.5, emit=(1.0, 0.82, 0.6), estr=6.0), C)

ROWS = [i * 0.86 for i in range(-3, 11)]          # row y positions (seat cushion centre), 14 rows
SEAT_X = {"A": -1.42, "B": -0.94, "C": -0.46, "D": 0.46, "E": 0.94, "F": 1.42}
BOMBER_ROW = 3                                     # index -> y = 0.0 (row value 0)
seat = L.import_glb("seat2", 1.12, "z", collection="Lib", obname="SeatMaster")
# orient: back is where the tall verts are; turn so the seat faces +Y
vs = [v.co for v in seat.data.vertices]; zt = max(v.z for v in vs)
top = [v for v in vs if v.z > 0.85 * zt]
cy = sum(v.y for v in top) / len(top); cx = sum(v.x for v in top) / len(top)
ang = math.atan2(cx, cy)            # direction of the back from centre
seat.data.transform(Matrix.Rotation(-ang + math.pi, 4, 'Z'))    # back toward -Y
vs = [v.co for v in seat.data.vertices]
w_ = max(v.x for v in vs) - min(v.x for v in vs)
seat.data.transform(Matrix.Scale(0.47 / w_, 4, (1, 0, 0)))
for s in seat.material_slots:
    if s.material and "puffy" in s.material.name: s.material = M["seatfab"]
    elif s.material and "plastic" in s.material.name: s.material = L.mat("SeatShell", (0.42, 0.43, 0.45), 0.4)
seat.hide_render = True; seat.hide_viewport = True
SEATS = {}
for ri, ry in enumerate(ROWS):
    for k, sx in SEAT_X.items():
        o = bpy.data.objects.new("Seat_%02d%s" % (ri, k), seat.data); L.coll("Seats").objects.link(o)
        o.location = (sx, ry, 0.0); SEATS[(ri, k)] = o
        hr = L.add_box("Headrest_%02d%s" % (ri, k), (0.34, 0.02, 0.2), (sx, ry - 0.19, 0.98), M["headrest"], "Seats")
print("SEAT_DIMS", tuple(round(v, 3) for v in seat.dimensions))
# overhead bins, cove light, reading light panels, windows
for side in (-1, 1):
    L.add_box("Bin_%d" % side, (0.78, Y1 - Y0 - 0.2, 0.42), (side * 1.25, (Y0 + Y1) / 2, 1.86), M["bin"], C, bevel=0.06)
    L.add_box("BinLip_%d" % side, (0.04, Y1 - Y0 - 0.2, 0.05), (side * 0.85, (Y0 + Y1) / 2, 1.66), M["trim"], C)
    L.add_box("PSU_%d" % side, (0.55, Y1 - Y0 - 0.2, 0.03), (side * 1.3, (Y0 + Y1) / 2, 1.635), M["trim"], C)
    L.add_box("Cove_%d" % side, (0.03, Y1 - Y0 - 0.2, 0.03), (side * 0.82, (Y0 + Y1) / 2, 2.1), M["glow_blue"], C)
    for ry in ROWS:
        L.add_box("BinSeam_%d_%.1f" % (side, ry), (0.8, 0.008, 0.4), (side * 1.25, ry - 0.4, 1.86), M["trim"], C)
        for k in range(3):
            on = (side == -1 and abs(ry) < 0.01 and k == 0) or random.random() < 0.18
            L.add_box("RL_%d_%.1f_%d" % (side, ry, k), (0.06, 0.06, 0.012), (side * (0.98 + 0.25 * k), ry - 0.05, 1.622),
                      M["glow_warm"] if on else M["glow_off"], "Seats")
    # windows: oval emissive night sky + frame
    for ry in ROWS + [ROWS[-1] + 0.86]:
        y = ry + 0.12
        bpy.ops.mesh.primitive_circle_add(vertices=24, radius=0.15, fill_type='NGON', location=(side * 1.745, y, 1.18))
        w = bpy.context.active_object; w.name = "Window_%d_%.1f" % (side, ry)
        w.scale = (1, 0.8, 1.25); w.rotation_euler = (0, math.radians(90 + side * 12), 0)
        L.link(w, L.coll(C)); w["window"] = 1
        bpy.ops.mesh.primitive_torus_add(major_radius=0.17, minor_radius=0.025, location=(side * 1.73, y, 1.18))
        fr = bpy.context.active_object; fr.name = "WinFrame_%d_%.1f" % (side, ry); fr.scale = (1, 0.8, 1.25)
        fr.rotation_euler = (0, math.radians(90 + side * 12), 0); L.set_mat(fr, M["bin"]); L.link(fr, L.coll(C))
# night sky window material: dark gradient + drifting clouds + blinking wing light handled in animate
wm = bpy.data.materials.new("WindowNight"); wm.use_nodes = True; N = wm.node_tree.nodes; Ln = wm.node_tree.links
for n in list(N): N.remove(n)
o_ = N.new("ShaderNodeOutputMaterial"); em = N.new("ShaderNodeEmission"); tc = N.new("ShaderNodeTexCoord"); mp = N.new("ShaderNodeMapping")
mp.name = "CloudDrift"; nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 3.0; nz.inputs["Detail"].default_value = 6
cr = N.new("ShaderNodeValToRGB"); cr.color_ramp.elements[0].position = 0.45; cr.color_ramp.elements[0].color = (0.004, 0.008, 0.03, 1)
cr.color_ramp.elements[1].position = 0.75; cr.color_ramp.elements[1].color = (0.12, 0.15, 0.25, 1)
Ln.new(tc.outputs["Object"], mp.inputs["Vector"]); Ln.new(mp.outputs["Vector"], nz.inputs["Vector"]); Ln.new(nz.outputs["Fac"], cr.inputs["Fac"])
Ln.new(cr.outputs["Color"], em.inputs["Color"]); em.inputs["Strength"].default_value = 1.2; Ln.new(em.outputs[0], o_.inputs["Surface"])
for o in bpy.data.objects:
    if o.get("window"): L.set_mat(o, wm)

# tray tables (folded down at bomber row neighbours), blankets, pillows, bags
def tray(name, loc):
    return L.add_box(name, (0.4, 0.3, 0.02), loc, M["trim"], "Props", bevel=0.01)
TRAY = tray("TrayTable", (SEAT_X["B"], 0.86 - 0.55, 0.72))            # B seat row 3 (in front of PaxA), drops in the tackle
CUP = None
bpy.ops.mesh.primitive_cylinder_add(vertices=20, radius=0.035, depth=0.09, location=(SEAT_X["B"] + 0.08, 0.86 - 0.55, 0.775))
CUP = bpy.context.active_object; CUP.name = "Cup"; L.set_mat(CUP, M["cup"]); L.link(CUP, L.coll("Props"))
for (ri, k) in [(1, "E"), (5, "A"), (6, "F"), (2, "C"), (8, "D")]:
    b = L.add_box("Blanket_%d%s" % (ri, k), (0.44, 0.35, 0.06), (SEAT_X[k], ROWS[ri] + 0.05, 0.52), M["blanket"], "Props", bevel=0.025)
    b.rotation_euler = (math.radians(8), 0, math.radians(random.uniform(-10, 10)))
for (ri, k) in [(4, "C"), (2, "D"), (7, "B")]:
    L.add_box("Bag_%d%s" % (ri, k), (0.32, 0.18, 0.24), (SEAT_X[k] + 0.0, ROWS[ri] - 0.55, 0.12), L.mat("BagBlack", (0.03, 0.03, 0.035), 0.6), "Props", bevel=0.03)

# drink trolley
TR = L.add_box("Trolley", (0.3, 0.75, 1.0), (0, 6.5, 0.52), L.mat("TrolleyMetal", (0.55, 0.56, 0.58), 0.35, 0.4), "Props", bevel=0.02)
for k in range(4):
    L.add_box("TrolleyDrawerLine_%d" % k, (0.305, 0.72, 0.006), (0, 0, -0.35 + k * 0.22), M["trim"], "Props").parent = TR
top = L.add_box("TrolleyTop", (0.32, 0.77, 0.03), (0, 0, 0.515), M["dark"], "Props"); top.parent = TR
for i in range(6):
    bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=0.033, depth=0.12, location=(random.uniform(-0.1, 0.1), -0.3 + i * 0.12, 0.59))
    c = bpy.context.active_object; c.name = "TrolleyCan_%d" % i; L.set_mat(c, M["can"] if i % 2 else M["can2"]); L.link(c, L.coll("Props")); c.parent = TR
for i in range(4):
    bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=0.035, depth=0.09, location=(0.08, -0.25 + i * 0.07, 0.575))
    c = bpy.context.active_object; c.name = "TrolleyCup_%d" % i; L.set_mat(c, M["cup"]); L.link(c, L.coll("Props")); c.parent = TR

# sneakers (pair): split loose parts, clean texture, one per shoe
sn = L.import_glb("sneakerA", 0.30, "y", collection="Lib", obname="SneakerPair")
for s in sn.material_slots:
    if s.material:
        for nd in s.material.node_tree.nodes:
            if nd.type == 'TEX_IMAGE' and nd.image:
                key = nd.image.name.split(".")[0]
                p = TEX + "snA_%s.png" % key
                if os.path.exists(p):
                    nd.image = bpy.data.images.load(p, check_existing=True)
                    if key != "Image_0": nd.image.colorspace_settings.name = "Non-Color"
bpy.context.view_layer.objects.active = sn
for o in bpy.context.selected_objects: o.select_set(False)
sn.select_set(True)
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT'); bpy.ops.mesh.separate(type='LOOSE'); bpy.ops.object.mode_set(mode='OBJECT')
parts = [o for o in bpy.data.objects if o.name.startswith("SneakerPair")]
# group loose parts into the two shoes by x of their centre
def cen(o): vs = [v.co for v in o.data.vertices]; return sum((v for v in vs), Vector()) / len(vs)
CX = {p.name: cen(p).x for p in parts}; xs = sorted(CX.values()); mid = (xs[0] + xs[-1]) / 2
groups = [[p for p in parts if (CX[p.name] > mid) == bool(side)] for side in (0, 1)]
shoes = []
for side in (0, 1):
    grp = groups[side]
    with bpy.context.temp_override(active_object=grp[0], selected_editable_objects=grp, object=grp[0]):
        bpy.ops.object.join()
    o = grp[0]; o.name = "Shoe_%s" % ("R" if side else "L")
    vs = [v.co for v in o.data.vertices]
    mn = Vector([min(v[i] for v in vs) for i in range(3)]); mx = Vector([max(v[i] for v in vs) for i in range(3)])
    # origin at heel-bottom centre, toe toward -Y (character forward)
    o.data.transform(Matrix.Translation(-V(((mn.x + mx.x) / 2, (mn.y + mx.y) / 2, mn.z))))
    shoes.append(o)
print("SHOES", [(s.name, tuple(round(d, 3) for d in s.dimensions)) for s in shoes])
# which way is the toe? toe is the lower, longer end; the collar (tall) is the heel side
for o in shoes:
    vs = [v.co for v in o.data.vertices]; tall = [v for v in vs if v.z > 0.8 * max(v.z for v in vs)]
    if sum(v.y for v in tall) / len(tall) < 0:    # heel collar toward -Y -> rotate so toe -> -Y
        o.data.transform(Matrix.Rotation(math.pi, 4, 'Z'))
    L.link(o, L.coll("Props"))
# copies for the studio cutaway and the airport traveller
for o in shoes:
    for tag in ("Studio", "Trav"):
        c = o.copy(); c.data = o.data.copy() if tag == "Studio" else o.data; c.name = o.name + "_" + tag
        L.coll("Props" if tag == "Trav" else "Studio").objects.link(c)

# matches + matchbox + fuse cords + syringe
MB = L.add_box("Matchbox", (0.036, 0.052, 0.014), (0, 0, 0), L.mat("MatchboxCard", (0.55, 0.12, 0.08), 0.7), "Props", bevel=0.002)
def match(name):
    bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=0.0015, depth=0.045, location=(0, 0, 0.0225))
    st = bpy.context.active_object; st.name = name; L.set_mat(st, L.mat("MatchWood", (0.75, 0.6, 0.4), 0.8)); L.link(st, L.coll("Props"))
    bpy.ops.mesh.primitive_uv_sphere_add(segments=10, ring_count=6, radius=0.0028, location=(0, 0, 0.046))
    hd = bpy.context.active_object; hd.name = name + "_Head"; hd.scale = (1, 1, 1.5); L.set_mat(hd, L.mat("MatchHead", (0.25, 0.04, 0.03), 0.6)); L.link(hd, L.coll("Props")); hd.parent = st
    bpy.ops.mesh.primitive_uv_sphere_add(segments=12, ring_count=8, radius=0.008, location=(0, 0, 0.06))
    fl_ = bpy.context.active_object; fl_.name = name + "_Flame"; fl_.scale = (0.8, 0.8, 2.2); L.link(fl_, L.coll("Props")); fl_.parent = st
    fm = bpy.data.materials.new("Flame_" + name); fm.use_nodes = True; nn = fm.node_tree.nodes
    for n in list(nn): nn.remove(n)
    out = nn.new("ShaderNodeOutputMaterial"); e = nn.new("ShaderNodeEmission"); e.inputs["Color"].default_value = (1.0, 0.55, 0.15, 1)
    e.inputs["Strength"].default_value = 25; tr = nn.new("ShaderNodeBsdfTransparent"); mx = nn.new("ShaderNodeMixShader"); mx.name = "FlameMix"
    lw = nn.new("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.6
    fm.node_tree.links.new(lw.outputs["Facing"], mx.inputs["Fac"]); fm.node_tree.links.new(e.outputs[0], mx.inputs[1]); fm.node_tree.links.new(tr.outputs[0], mx.inputs[2])
    fm.node_tree.links.new(mx.outputs[0], out.inputs["Surface"]); L.set_mat(fl_, fm)
    lt = bpy.data.lights.new(name + "_Light", 'POINT'); lt.energy = 0.0; lt.color = (1.0, 0.6, 0.25); lt.shadow_soft_size = 0.01
    lo = bpy.data.objects.new(name + "_Light", lt); L.coll("Props").objects.link(lo); lo.parent = st; lo.location = (0, 0, 0.07)
    return st
MATCH = match("Match")
# fuse cords: a short curve poking out of each shoe's inner sole near the heel
for s in shoes:
    cu = bpy.data.curves.new("Fuse_" + s.name, 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = 0.004; cu.bevel_resolution = 3
    sp = cu.splines.new('BEZIER'); sp.bezier_points.add(2)
    for i, p in enumerate([V((0, -0.07, 0.03)), V((0.004, -0.075, -0.025)), V((0.018, -0.09, -0.075))]):   # out through the heel sole
        sp.bezier_points[i].co = p; sp.bezier_points[i].handle_left_type = sp.bezier_points[i].handle_right_type = 'AUTO'
    fo = bpy.data.objects.new("Fuse_" + s.name, cu); L.coll("Props").objects.link(fo); fo.parent = s
    fo.data.materials.append(L.mat("FuseCord", (0.75, 0.62, 0.42), 0.85))
sy = L.import_glb("syringe", 0.15, "max", collection="Props", obname="Syringe")

# ------------------------------------------------------------------ STUDIO (x=200)
SX = V((200, 0, 0))
S = "Studio"
bm = bmesh.new()
prof = [(y, 0.0) for y in [-6, -2, 0, 1.5]] + [(1.5 + 1.2 * math.sin(math.radians(a)), 1.2 - 1.2 * math.cos(math.radians(a))) for a in range(10, 91, 10)] + [(2.7, 4.0), (2.7, 8.0)]
rows = []
for xx in (-8, 8):
    rows.append([bm.verts.new((SX.x + xx, y, z)) for y, z in prof])
for i in range(len(prof) - 1):
    bm.faces.new((rows[0][i], rows[0][i + 1], rows[1][i + 1], rows[1][i]))
me = bpy.data.meshes.new("Cyc"); bm.to_mesh(me); bm.free()
cyc = bpy.data.objects.new("StudioCyc", me); L.coll(S).objects.link(cyc)
for p in me.polygons: p.use_smooth = True
cm = bpy.data.materials.new("CycGradient"); cm.use_nodes = True; N = cm.node_tree.nodes; Ln = cm.node_tree.links
b = N["Principled BSDF"]; tc = N.new("ShaderNodeTexCoord"); sep = N.new("ShaderNodeSeparateXYZ"); rp = N.new("ShaderNodeValToRGB")
Ln.new(tc.outputs["Generated"], sep.inputs[0]); Ln.new(sep.outputs["Z"], rp.inputs["Fac"])
rp.color_ramp.elements[0].position = 0.0; rp.color_ramp.elements[0].color = (0.25, 0.75, 0.85, 1)
rp.color_ramp.elements[1].position = 0.55; rp.color_ramp.elements[1].color = (0.008, 0.03, 0.09, 1)
e_ = rp.color_ramp.elements.new(0.22); e_.color = (0.03, 0.32, 0.48, 1)
Ln.new(rp.outputs["Color"], b.inputs["Base Color"]); b.inputs["Roughness"].default_value = 0.8
Ln.new(rp.outputs["Color"], b.inputs["Emission Color"]); b.inputs["Emission Strength"].default_value = 0.2
L.set_mat(cyc, cm)
for nm, loc, en, sz in (("StudioKey", (SX.x - 2.0, -2.5, 3.2), 900, 2.5), ("StudioRim", (SX.x + 2.5, 1.8, 2.5), 600, 1.5), ("StudioFill", (SX.x + 2.5, -3.0, 1.2), 200, 3.0)):
    ld = bpy.data.lights.new(nm, 'AREA'); ld.energy = en; ld.size = sz
    lo = bpy.data.objects.new(nm, ld); L.coll(S).objects.link(lo); lo.location = loc
    lo.rotation_euler = (V((SX.x, 0, 1.2)) - V(loc)).to_track_quat('-Z', 'Y').to_euler()
# putty slab (abstract grey block) per studio shoe, with an outline shell for the highlight
pm = bpy.data.materials.new("Putty"); pm.use_nodes = True; N = pm.node_tree.nodes; b = N["Principled BSDF"]
nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 60; bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.25
pm.node_tree.links.new(nz.outputs["Fac"], bp.inputs["Height"]); pm.node_tree.links.new(bp.outputs["Normal"], b.inputs["Normal"])
b.inputs["Base Color"].default_value = (0.11, 0.11, 0.105, 1); b.inputs["Roughness"].default_value = 0.85
om = L.mat("SlabOutline", (0, 0, 0), 0.5, emit=(1.0, 0.75, 0.1), estr=0.0); om.use_backface_culling = True
for s in shoes:
    st = bpy.data.objects[s.name + "_Studio"]
    sl = L.add_box("Slab_" + s.name, (0.075, 0.2, 0.022), (0, 0, 0), pm, S, bevel=0.008)
    ol = L.add_box("SlabOutline_" + s.name, (0.075, 0.2, 0.022), (0, 0, 0), om, S, bevel=0.008)
    ol.modifiers.clear(); ol.scale = (1.04, 1.03, 1.12)
    wf = ol.modifiers.new("wire", 'WIREFRAME'); wf.thickness = 0.0025
    sl.parent = st; ol.parent = st; sl.location = ol.location = (0, 0.0, 0.03)

# ------------------------------------------------------------------ SKY (x=-2000, z=600)
K = "Sky"
KX = V((-2000, 0, 600))
pl = L.import_glb("plane", 39.5, "x", collection=K, obname="Airliner")
# retract the landing gear: delete gear geometry
import bmesh as _bm
_b = _bm.new(); _b.from_mesh(pl.data)
_gi = {i for i, m in enumerate(pl.data.materials) if m and "gear" in m.name.lower()}
_bm.ops.delete(_b, geom=[f for f in _b.faces if f.material_index in _gi], context='FACES')
_b.to_mesh(pl.data); _b.free()
vs = [v.co for v in pl.data.vertices]
print("PLANE_EXT", [round(max(v[i] for v in vs) - min(v[i] for v in vs), 2) for i in range(3)])
paint = L.mat("AirlinerPaint", (0.86, 0.87, 0.88), 0.25)
belly = L.mat("AirlinerBelly", (0.5, 0.52, 0.55), 0.3)
glass = L.mat("CockpitGlass", (0.02, 0.025, 0.03), 0.05)
navR = L.mat("NavRed", (0.3, 0, 0), 0.4, emit=(1, 0.05, 0.02), estr=40); navG = L.mat("NavGreen", (0, 0.3, 0), 0.4, emit=(0.05, 1, 0.1), estr=40)
for s in pl.material_slots:
    if not s.material: continue
    n = s.material.name.lower()
    if "strobe1" in n: s.material = navR
    elif "strobe3" in n: s.material = navG
    elif "wingbodylights" in n or "wiper" in n: s.material = glass
    elif "strobe" in n: s.material = L.mat("StrobeWhite", (1, 1, 1), 0.3, emit=(1, 1, 1), estr=5)
    elif "light" in n: s.material = glass
    elif "engine" in n or "gear" in n or "blade" in n: s.material = belly
    else: s.material = paint
pl.location = KX
# cabin-window light strip on both sides of the fuselage (warm, reads as "people inside")
# cloud deck: displaced, noise-alpha planes below; big puffs around
cdm = bpy.data.materials.new("CloudDeck"); cdm.use_nodes = True; N = cdm.node_tree.nodes; Ln = cdm.node_tree.links
for n in list(N): N.remove(n)
o_ = N.new("ShaderNodeOutputMaterial"); pr = N.new("ShaderNodeBsdfPrincipled"); tr = N.new("ShaderNodeBsdfTransparent"); mx = N.new("ShaderNodeMixShader")
tc = N.new("ShaderNodeTexCoord"); nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 0.012; nz.inputs["Detail"].default_value = 10; nz.inputs["Roughness"].default_value = 0.6
cr = N.new("ShaderNodeValToRGB"); cr.color_ramp.elements[0].position = 0.42; cr.color_ramp.elements[1].position = 0.62
pr.inputs["Base Color"].default_value = (1.0, 0.86, 0.78, 1); pr.inputs["Roughness"].default_value = 1.0
pr.inputs["Subsurface Weight"].default_value = 0.3
Ln.new(tc.outputs["Object"], nz.inputs["Vector"]); Ln.new(nz.outputs["Fac"], cr.inputs["Fac"]); Ln.new(cr.outputs["Color"], mx.inputs["Fac"])
Ln.new(tr.outputs[0], mx.inputs[1]); Ln.new(pr.outputs[0], mx.inputs[2]); Ln.new(mx.outputs[0], o_.inputs["Surface"])
for k, dz in enumerate((-70, -78, -86)):
    bpy.ops.mesh.primitive_plane_add(size=6000, location=(KX.x, KX.y, KX.z + dz))
    d = bpy.context.active_object; d.name = "CloudDeck_%d" % k; L.set_mat(d, cdm); L.link(d, L.coll(K))
    d.rotation_euler.z = k * 1.3
bpy.ops.mesh.primitive_plane_add(size=6000, location=(KX.x, KX.y, KX.z - 95))
d = bpy.context.active_object; d.name = "CloudFloor"; L.set_mat(d, L.mat("CloudFloorMat", (0.9, 0.78, 0.72), 1.0)); L.link(d, L.coll(K))
puff = L.mat("CloudPuff", (1.0, 0.9, 0.84), 1.0)
puff.node_tree.nodes["Principled BSDF"].inputs["Subsurface Weight"].default_value = 0.6
puff.node_tree.nodes["Principled BSDF"].inputs["Subsurface Radius"].default_value = (5, 5, 5)
tx = bpy.data.textures.new("PuffNoise", 'CLOUDS'); tx.noise_scale = 0.35; tx.noise_depth = 4
for i in range(70):
    r = random.uniform(12, 38)
    an = random.uniform(0, 2 * math.pi); dist = random.uniform(220, 900)
    p = KX + V((math.cos(an) * dist, math.sin(an) * dist + 300, random.uniform(-82, -70)))
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=5, radius=r, location=p)
    c = bpy.context.active_object; c.name = "Puff_%02d" % i; c.scale = (1.6, 1.3, 0.5)
    dm = c.modifiers.new("d", 'DISPLACE'); dm.texture = tx; dm.strength = r * 0.22
    L.set_mat(c, puff); L.link(c, L.coll(K))
    for f_ in c.data.polygons: f_.use_smooth = True

# ------------------------------------------------------------------ AIRPORT (x=400)
AX = V((400, 0, 0))
A = "Airport"
fl = L.add_box("TerminalFloor", (40, 40, 0.05), AX + V((0, 0, -0.025)), L.tex_mat("TerminalTiles", "large_grey_tiles", 8.0, tint=(0.55, 0.55, 0.57), rough_mul=0.6), A)
bpy.context.view_layer.objects.active = fl
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT'); bpy.ops.uv.cube_project(cube_size=1.0); bpy.ops.object.mode_set(mode='OBJECT')
ceil = L.add_box("TerminalCeiling", (40, 40, 0.1), AX + V((0, 0, 7.0)), L.mat("CeilingWhite", (0.55, 0.55, 0.56), 0.6), A)
# skylight opening: emissive day-sky panels in the ceiling (the camera descends through the middle one)
for i in range(-3, 4):
    L.add_box("Skylight_%d" % i, (2.0, 6.0, 0.12), AX + V((i * 3.2, 0, 6.99)), L.mat("SkylightSky", (0.6, 0.75, 0.9), 0.3, emit=(0.75, 0.85, 1.0), estr=3.0), A)
glassm = L.mat("TerminalGlass", (0.8, 0.9, 0.95), 0.02, trans=1.0)
L.add_box("GlassWall", (40, 0.05, 7.0), AX + V((0, 9.0, 3.5)), glassm, A)
for i in range(-6, 7):
    L.add_box("Mullion_%d" % i, (0.12, 0.15, 7.0), AX + V((i * 3.0, 8.95, 3.5)), M["trim"], A)
    L.add_box("Column_%d" % i, (0.5, 0.5, 7.0), AX + V((i * 6.0, -6.0, 3.5)), L.mat("ColumnWhite", (0.88, 0.88, 0.86), 0.4), A)
# security lane: belt (conveyor model repeated), X-ray tunnel, curtains, detector, trays, stanchions
BELT_Y = 0.0
cv = L.import_glb("conveyor", 0.75, "z", collection=A, obname="Conveyor_0")
cv.rotation_euler.z = math.radians(90); cv.location = AX + V((-1.0, BELT_Y, 0))
for k in range(1, 4):
    c = cv.copy(); c.name = "Conveyor_%d" % k; L.coll(A).objects.link(c); c.location = AX + V((-1.0 + 2.0 * k, BELT_Y, 0))
BELT_TOP = 0.75
xm = L.mat("XrayBody", (0.78, 0.8, 0.82), 0.35)
L.add_box("XrayTunnelL", (2.4, 0.15, 1.2), AX + V((4.0, BELT_Y - 0.55, 1.3)), xm, A, bevel=0.05)
L.add_box("XrayTunnelR", (2.4, 0.15, 1.2), AX + V((4.0, BELT_Y + 0.55, 1.3)), xm, A, bevel=0.05)
L.add_box("XrayTunnelTop", (2.4, 1.25, 0.25), AX + V((4.0, BELT_Y, 1.82)), xm, A, bevel=0.05)
L.add_box("XrayBase", (2.4, 1.25, 0.7), AX + V((4.0, BELT_Y, 0.35)), xm, A, bevel=0.05)
cm_ = L.mat("LeadCurtain", (0.15, 0.17, 0.2), 0.7)
for k in range(10):
    L.add_box("Curtain_%d" % k, (0.01, 0.095, 0.75), AX + V((2.8, BELT_Y - 0.45 + k * 0.1, 1.15)), cm_, A)
L.add_box("XrayDesk", (1.0, 0.7, 0.8), AX + V((4.5, BELT_Y + 1.6, 0.4)), xm, A)
L.add_box("XrayMonitor", (0.55, 0.05, 0.38), AX + V((4.5, BELT_Y + 1.4, 1.15)), L.mat("MonitorGlow", (0.02, 0.02, 0.02), 0.2, emit=(0.25, 0.45, 0.6), estr=3.0), A)
dt = L.import_glb("detector", 2.3, "z", collection=A, obname="WalkDetector")
dt.location = AX + V((1.0, BELT_Y + 1.6, 0)); dt.rotation_euler.z = math.radians(90)
tm = L.mat("TrayGrey", (0.22, 0.23, 0.25), 0.55)
def mk_tray(name, loc):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    t = bpy.context.active_object; t.name = name; t.scale = (0.55, 0.38, 0.1); bpy.ops.object.transform_apply(scale=True)
    bm = bmesh.from_edit_mesh(t.data) if False else None
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='DESELECT'); bpy.ops.object.mode_set(mode='OBJECT')
    for f_ in t.data.polygons: f_.select = f_.normal.z > 0.9
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.delete(type='FACE'); bpy.ops.object.mode_set(mode='OBJECT')
    so = t.modifiers.new("s", 'SOLIDIFY'); so.thickness = 0.012; bv = t.modifiers.new("b", 'BEVEL'); bv.width = 0.01; bv.segments = 2
    L.set_mat(t, tm); L.link(t, L.coll(A)); return t
TRAYS = []
for k in range(5):
    TRAYS.append(mk_tray("Tray_%d" % k, AX + V((-1.6 + k * 0.75, BELT_Y, BELT_TOP + 0.05))))
for k in range(6):
    mk_tray("TrayStack_%d" % k, AX + V((-2.8, BELT_Y + 0.9, 0.05 + k * 0.08)))
for k in range(8):
    bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=0.03, depth=1.0, location=AX + V((-3.5 + k * 1.1, BELT_Y - 1.6, 0.5)))
    p = bpy.context.active_object; p.name = "Stanchion_%d" % k; L.set_mat(p, M["metal"]); L.link(p, L.coll(A))
    if k < 7: L.add_box("Tape_%d" % k, (1.1, 0.01, 0.05), AX + V((-2.95 + k * 1.1, BELT_Y - 1.6, 0.95)), L.mat("TapeBlue", (0.08, 0.12, 0.35), 0.5), A)
# bags in other trays
for k, col in ((0, (0.05, 0.05, 0.06)), (2, (0.35, 0.15, 0.1)), (3, (0.15, 0.3, 0.2))):
    L.add_box("TrayBag_%d" % k, (0.35, 0.25, 0.15), TRAYS[k].location + V((0, 0, 0.08)), L.mat("Bag%d" % k, col, 0.6), A, bevel=0.03).parent = None

# ------------------------------------------------------------------ v002 detail pass
# cabin: window shades pulled down (moonlight sliver at the bottom), seat-back screens glowing (no text)
shade_m = L.mat("WindowShade", (0.72, 0.7, 0.66), 0.6)
for o in [o for o in bpy.data.objects if o.get("window")]:
    sh = o.copy(); sh.data = o.data; sh.name = "Shade_" + o.name; L.coll(C).objects.link(sh)
    side = 1 if o.location.x > 0 else -1
    sh.location = o.location + V((-side * 0.012, 0, 0.045)); sh.scale = (o.scale.x * 1.02, o.scale.y * 1.02, o.scale.z * 0.92)
    sh.data = o.data.copy(); sh.data.materials.clear(); sh.data.materials.append(shade_m)
wmn = bpy.data.materials["WindowNight"]
wmn.node_tree.nodes["Emission"].inputs["Strength"].default_value = 3.0
scr_cols = [(0.15, 0.35, 0.8), (0.1, 0.5, 0.6), (0.4, 0.3, 0.7), (0.2, 0.25, 0.35)]
for (ri, k), so in SEATS.items():
    if random.random() < 0.55:
        col = random.choice(scr_cols)
        sm = L.mat("Screen_%d_%d_%d" % tuple(int(c * 10) for c in col), (0.01, 0.01, 0.01), 0.15, emit=col, estr=random.choice((1.5, 2.5, 3.5)))
        L.add_box("SeatScreen_%02d%s" % (ri, k), (0.2, 0.006, 0.13), so.location + V((0, -0.358, 0.86)), sm, "Seats")
    else:
        L.add_box("SeatScreen_%02d%s" % (ri, k), (0.2, 0.006, 0.13), so.location + V((0, -0.358, 0.86)), M["dark"], "Seats")
# fasten-seatbelt sign glow panels (pictogram only) under the bins
belt_m = L.mat("BeltSignGlow", (0.02, 0.02, 0.02), 0.3, emit=(1.0, 0.75, 0.35), estr=4.0)
for ry in ROWS[::2]:
    for side in (-1, 1):
        L.add_box("BeltSign_%d_%.1f" % (side, ry), (0.05, 0.03, 0.012), (side * 1.12, ry + 0.2, 1.618), belt_m, "Seats")
# blankets read as cloth: subdivide + displace
cloth_tx = bpy.data.textures.new("ClothNoise", 'CLOUDS'); cloth_tx.noise_scale = 0.08
for o in [o for o in bpy.data.objects if o.name.startswith("Blanket_")]:
    o.modifiers.clear(); sd = o.modifiers.new("sd", 'SUBSURF'); sd.levels = sd.render_levels = 3; sd.subdivision_type = 'SIMPLE'
    dp = o.modifiers.new("dp", 'DISPLACE'); dp.texture = cloth_tx; dp.strength = 0.03
    sm2 = o.modifiers.new("sm", 'SMOOTH'); sm2.iterations = 6
    o.scale = (1.0, 1.0, 1.0)
# studio: cyan rim light behind the shoes (also the slab edge light)
ld = bpy.data.lights.new("StudioCyanRim", 'AREA'); ld.energy = 900; ld.size = 1.2; ld.color = (0.35, 0.9, 1.0)
lo = bpy.data.objects.new("StudioCyanRim", ld); L.coll(S).objects.link(lo); lo.location = (SX.x, 1.4, 1.9)
lo.rotation_euler = (V((SX.x, 0, 1.15)) - lo.location).to_track_quat('-Z', 'Y').to_euler()
# putty slab: kneaded, finger-pressed surface (displaced, not a clean block)
putty_tx = bpy.data.textures.new("PuttyNoise", 'CLOUDS'); putty_tx.noise_scale = 0.01
for o in [o for o in bpy.data.objects if o.name.startswith("Slab_")]:
    o.modifiers.clear(); sd = o.modifiers.new("sd", 'SUBSURF'); sd.levels = sd.render_levels = 4
    dp = o.modifiers.new("dp", 'DISPLACE'); dp.texture = putty_tx; dp.strength = 0.004
for o in [o for o in bpy.data.objects if o.name.startswith("SlabOutline_")]:
    bpy.data.objects.remove(o)
# volumetric cloud banks for the two crossings and volumetric cumulus puffs
def cloud_vol(name, dens=6.0, scale=3.0, col=(1.0, 0.92, 0.88)):
    m = bpy.data.materials.new(name); m.use_nodes = True; N = m.node_tree.nodes; Ln = m.node_tree.links
    for n in list(N): N.remove(n)
    out = N.new("ShaderNodeOutputMaterial"); pv = N.new("ShaderNodeVolumePrincipled"); tc = N.new("ShaderNodeTexCoord")
    nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = scale; nz.inputs["Detail"].default_value = 8; nz.inputs["Roughness"].default_value = 0.6
    cr = N.new("ShaderNodeMapRange"); cr.inputs["From Min"].default_value = 0.45; cr.inputs["From Max"].default_value = 0.7
    cr.inputs["To Max"].default_value = dens
    Ln.new(tc.outputs["Object"], nz.inputs["Vector"]); Ln.new(nz.outputs["Fac"], cr.inputs["Value"]); Ln.new(cr.outputs["Result"], pv.inputs["Density"])
    pv.inputs["Color"].default_value = (*col, 1); pv.inputs["Anisotropy"].default_value = 0.4
    pv.inputs["Emission Color"].default_value = (*col, 1)
    Ln.new(cr.outputs["Result"], pv.inputs["Emission Strength"])      # self-lit wisps: bright where dense
    Ln.new(pv.outputs[0], out.inputs["Volume"]); return m
cm_near = cloud_vol("CloudBankNear", 3.0, 2.5)
def bank(name, loc, size):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=1.0, location=loc)
    o = bpy.context.active_object; o.name = name; o.scale = size; L.set_mat(o, cm_near); L.link(o, L.coll(K if name.startswith("Sky") else S)); return o
bank("StudioCloudBank", SX + V((0.0, -4.4, 1.45)), (2.5, 1.6, 1.6))
bank("SkyCloudEntry", KX + V((11.2, 5.0, 1.6)), (1.6, 1.0, 1.0))
bank("SkyCloudExit", KX + V((-60.0, 84.0, -6.0)), (14.0, 14.0, 8.0))
# puffs stay surface clouds (volume puffs cost ~140 s per preview still); soft translucent SSS with a noise-bumped surface
pz = bpy.data.materials["CloudPuff"]; nt = pz.node_tree; bsdf = nt.nodes["Principled BSDF"]
bsdf.inputs["Base Color"].default_value = (1.0, 0.88, 0.82, 1); bsdf.inputs["Roughness"].default_value = 1.0
bsdf.inputs["Subsurface Weight"].default_value = 1.0; bsdf.inputs["Subsurface Radius"].default_value = (8, 8, 8); bsdf.inputs["Subsurface Scale"].default_value = 3.0
nz_ = nt.nodes.new("ShaderNodeTexNoise"); nz_.inputs["Scale"].default_value = 0.15; nz_.inputs["Detail"].default_value = 10
bp_ = nt.nodes.new("ShaderNodeBump"); bp_.inputs["Strength"].default_value = 0.6
nt.links.new(nz_.outputs["Fac"], bp_.inputs["Height"]); nt.links.new(bp_.outputs["Normal"], bsdf.inputs["Normal"])
# engine exhaust glow at the back of each engine nacelle
pl = bpy.data.objects["Airliner"]
ei = {i for i, m in enumerate(pl.data.materials) if m and "engine" in m.name.lower()}
pts = {1: [], -1: []}
for poly in pl.data.polygons:
    if poly.material_index in ei:
        c = poly.center; pts[1 if c.y > 0 else -1].append(c)
glow = L.mat("EngineGlow", (0.0, 0.0, 0.0), 0.5, emit=(1.0, 0.45, 0.15), estr=25)
for sd_, P in pts.items():
    if not P: continue
    xmin = min(p.x for p in P); ys = sum(p.y for p in P) / len(P); zs = sum(p.z for p in P) / len(P)
    bpy.ops.mesh.primitive_circle_add(vertices=24, radius=0.45, fill_type='NGON', location=pl.matrix_world @ V((xmin - 0.05, ys, zs)))
    g = bpy.context.active_object; g.name = "EngineGlow_%d" % sd_; g.rotation_euler = (0, math.radians(90), 0); L.set_mat(g, glow); L.link(g, L.coll(K))
# airport: hanging lane signs with pictograms only (generated images: shoe + arrow, bag)
def icon(path, kind):
    if os.path.exists(path): return     # made by make_icons.py (system python + PIL)
    from PIL import Image as _I, ImageDraw as _D
    im = _I.new("RGB", (256, 128), (20, 40, 70)); d = _D.Draw(im)
    if kind == "shoe":
        d.polygon([(40, 90), (40, 50), (70, 45), (95, 70), (140, 75), (150, 90)], fill=(240, 240, 240))
        d.line([(170, 70), (220, 70)], fill=(255, 200, 60), width=10); d.polygon([(220, 55), (245, 70), (220, 85)], fill=(255, 200, 60))
    else:
        d.rectangle((60, 50, 140, 100), fill=(240, 240, 240)); d.rectangle((85, 35, 115, 50), outline=(240, 240, 240), width=6)
        d.line([(170, 70), (220, 70)], fill=(255, 200, 60), width=10); d.polygon([(220, 55), (245, 70), (220, 85)], fill=(255, 200, 60))
    im.save(path)
for k, (kind, x) in enumerate((("shoe", -1.0), ("bag", 3.0), ("shoe", 7.0))):
    pth = "/opt/assets/sb_tex/sign_%s.png" % kind; icon(pth, kind)
    sm = bpy.data.materials.new("Sign_%d" % k); sm.use_nodes = True; N = sm.node_tree.nodes
    t = N.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(pth, check_existing=True)
    b_ = N["Principled BSDF"]; sm.node_tree.links.new(t.outputs["Color"], b_.inputs["Base Color"]); sm.node_tree.links.new(t.outputs["Color"], b_.inputs["Emission Color"])
    b_.inputs["Emission Strength"].default_value = 1.5
    bpy.ops.mesh.primitive_plane_add(size=1, location=AX + V((x, -1.2, 3.2)))
    sg = bpy.context.active_object; sg.name = "LaneSign_%d" % k; sg.scale = (1.2, 0.6, 1); sg.rotation_euler = (math.radians(90), 0, 0)
    L.set_mat(sg, sm); L.link(sg, L.coll(A))
    L.add_box("LaneSignFrame_%d" % k, (1.25, 0.06, 0.64), AX + V((x, -1.17, 3.2)), M["trim"], A)
    for dx in (-0.5, 0.5):
        L.add_box("LaneSignRod_%d_%d" % (k, dx * 10), (0.02, 0.02, 3.8), AX + V((x + dx, -1.17, 5.1)), M["metal"], A)
# ------------------------------------------------------------------ world: dusk HDRI for the sky set (mix to a day sky for the airport)
w = bpy.data.worlds.new("World"); sc.world = w; w.use_nodes = True; N = w.node_tree.nodes; Ln = w.node_tree.links
for n in list(N): N.remove(n)
out = N.new("ShaderNodeOutputWorld"); env = N.new("ShaderNodeTexEnvironment"); env.image = bpy.data.images.load(L.PH + "hdri/qwantani_dusk_2_puresky_2k.hdr")
bg = N.new("ShaderNodeBackground"); bg.name = "WorldBG"; bg.inputs["Strength"].default_value = 1.0
gtc = N.new("ShaderNodeTexCoord"); gsep = N.new("ShaderNodeSeparateXYZ"); gr = N.new("ShaderNodeValToRGB")
Ln.new(gtc.outputs["Generated"], gsep.inputs[0]); Ln.new(gsep.outputs["Z"], gr.inputs["Fac"])
gr.color_ramp.elements[0].position = 0.0; gr.color_ramp.elements[0].color = (1.0, 0.55, 0.3, 1)
gr.color_ramp.elements[1].position = 0.45; gr.color_ramp.elements[1].color = (0.35, 0.25, 0.6, 1)
gm = N.new("ShaderNodeMix"); gm.data_type = 'RGBA'; gm.blend_type = 'MULTIPLY'; gm.inputs["Factor"].default_value = 0.85
Ln.new(env.outputs["Color"], gm.inputs["A"]); Ln.new(gr.outputs["Color"], gm.inputs["B"])
Ln.new(gm.outputs["Result"], bg.inputs["Color"]); Ln.new(bg.outputs[0], out.inputs["Surface"])
env.image.scale(1024, 512)

# ------------------------------------------------------------------ humans
with bpy.data.libraries.load(HUM, link=False) as (src, dst):
    dst.objects = list(src.objects)
H = L.coll("Humans")
for o in dst.objects:
    if o: H.objects.link(o)
# patched (logo-free) shirt textures
for im in bpy.data.images:
    nm = os.path.basename(im.filepath)
    if nm in ("male_casualsuit04_diffuse.png", "female_casualsuit02_diffuse.png") and os.path.exists(TEX + nm):
        im.filepath = TEX + nm; im.reload()
for o in bpy.data.objects:
    if o.type == 'ARMATURE': o.location = (0, -30 - len(o.name), 0)
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("SCENE_SAVED", OUT)
