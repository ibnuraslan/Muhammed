"""GameBoxBullet v012 stage A (rebuild from scratch): two MPFB people in real CC0 garments, the street + house + gamer room,
the ONE bullet, the ONE collector's box set (solid slipcase with solid content layers), the pistol, the look.
blender -b --python 01_build.py -- <assets_dir> <logo_white.png> <logo_dark.png> <out.blend>

World: +Y points into the house. The front wall of the house is the slab y = 0 .. 0.15 (outside is y < 0).
He sits on the sofa inside facing -Y (toward the wall, the TV and the window). The shooter stands across the lawn.
MPFB characters face -Y in their rest pose."""
import bpy, bmesh, sys, math, random, os
from mathutils import Vector, Matrix
HERE = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(HERE, "lib.py")).read())

a = sys.argv[sys.argv.index("--") + 1:]
ASSETS, LOGO_W, LOGO_D, OUT = a[0], a[1], a[2], a[3]
random.seed(15)
for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob, do_unlink=True)
sc.render.fps = 60; sc.render.fps_base = 1.0
sc.frame_start, sc.frame_end = 1, 1311
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1080, 1920, 100

# ================================================================== PEOPLE (one model each)
TSHIRT_M = "elvs_crude_t-shirt_male/elvs_crude_t-shirt_male.mhclo"
CARGO = "cortu_cargo_pants/cortu_cargo_pants.mhclo"
SWEATER = "toigo_fisherman_sweater/toigo_fisherman_sweater.mhclo"; PANTS = "toigo_wool_pants/toigo_wool_pants.mhclo"
HERO, HB = human("Hero", 1.0, 0.45, {"asian": 0.10, "caucasian": 0.80, "african": 0.10}, "short02/short02.mhclo",
                 "young_caucasian_male/young_caucasian_male.mhmat", "eyebrow004/eyebrow004.mhclo", height=0.5, muscle=0.35, weight=0.45,
                 shoes="shoes02/shoes02.mhclo", clothes=[TSHIRT_M, CARGO])
SHOOT, SB = human("Shooter", 1.0, 0.45, {"asian": 0.05, "caucasian": 0.25, "african": 0.70}, "short01/short01.mhclo",
                  "middleage_african_male/middleage_african_male.mhmat", "eyebrow001/eyebrow001.mhclo", height=0.55, muscle=0.4, weight=0.5,
                  shoes="shoes02/shoes02.mhclo", clothes=[SWEATER, PANTS])
PEOPLE = ((HERO, HB), (SHOOT, SB))
for r, b in PEOPLE:
    bake_keys(b); eye_fix(r)
# EnhancedEye cornea: refractive transmission -> transparent mix (LESSONS 3), every eye group
for g in [g for g in bpy.data.node_groups if g.name.startswith("EnhancedEye")]:
    P = next((n for n in g.nodes if n.type == "BSDF_PRINCIPLED"), None); OUTN = next((n for n in g.nodes if n.type == "GROUP_OUTPUT"), None)
    if P is None or OUTN is None or "CorneaTransparentMix" in g.nodes: continue
    tl = [l for l in g.links if l.to_node == P and l.to_socket.name == "Transmission Weight"]
    src = tl[0].from_socket if tl else None
    for l in tl: g.links.remove(l)
    P.inputs["Transmission Weight"].default_value = 0.0
    ols = [l for l in g.links if l.from_node == P and l.to_node == OUTN]
    if not ols: continue
    out_sock = ols[0].to_socket; g.links.remove(ols[0])
    tr = g.nodes.new("ShaderNodeBsdfTransparent"); mx = g.nodes.new("ShaderNodeMixShader"); mx.name = "CorneaTransparentMix"
    if src: g.links.new(src, mx.inputs[0])
    else: mx.inputs[0].default_value = 0.0
    g.links.new(P.outputs[0], mx.inputs[1]); g.links.new(tr.outputs[0], mx.inputs[2]); g.links.new(mx.outputs[0], out_sock)
    print("EYEFIX", g.name)
for m in HB.data.materials: tint(m, (1.0, 0.90, 0.82))
for m in SB.data.materials: tint(m, (1.0, 0.93, 0.88))
for r, t in ((HERO, (0.32, 0.18, 0.10)), (SHOOT, (0.25, 0.22, 0.20))):
    for c in r.children:
        if c.type == 'MESH' and any(k in c.name for k in ("short02", "short01", "eyebrow")):
            for m in c.data.materials: tint(m, t)

# ---- wardrobe: REAL garments (MakeHuman community CC0), recoloured; the body is masked only where a garment covers it
def cl(rig, key, newname):
    o = part(rig, key); o.name = newname; return o
def colorize_lift(obj, rgb, lo=0.55):
    """recolour a garment: its texture's light/dark (folds, seams) is kept as value, lifted to lo..1 so dark textures stay saturated"""
    for m in obj.data.materials:
        if not m or not m.use_nodes: continue
        nt = m.node_tree
        for p in [n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED']:
            bc = p.inputs["Base Color"]
            if bc.is_linked:
                src = bc.links[0].from_socket
                bw = nt.nodes.new("ShaderNodeRGBToBW"); nt.links.new(src, bw.inputs[0])
                mr = nt.nodes.new("ShaderNodeMapRange"); mr.inputs["To Min"].default_value = lo; mr.inputs["To Max"].default_value = 1.0
                mr.inputs["From Max"].default_value = 0.6; nt.links.new(bw.outputs[0], mr.inputs["Value"])
                mul = nt.nodes.new("ShaderNodeMix"); mul.data_type = 'RGBA'; mul.blend_type = 'MULTIPLY'; mul.inputs["Factor"].default_value = 1.0
                mul.inputs["A"].default_value = (*rgb, 1); nt.links.new(mr.outputs[0], mul.inputs["B"])
                nt.links.new(mul.outputs["Result"], bc)
            else:
                bc.default_value = (*rgb, 1)
            p.inputs["Roughness"].default_value = max(0.6, p.inputs["Roughness"].default_value)
colorize = colorize_lift
H_TOP = cl(HERO, "crude_t-shirt_male", "Hero.top"); H_TRS = cl(HERO, "cargo_pants", "Hero.trousers")
colorize(H_TOP, (0.80, 0.03, 0.03)); colorize(H_TRS, (0.03, 0.09, 0.40))
S_TOP = cl(SHOOT, "fisherman_sweater", "Shooter.top"); S_TRS = cl(SHOOT, "wool_pants", "Shooter.trousers")
colorize(S_TOP, (0.05, 0.38, 0.12)); colorize(S_TRS, (0.10, 0.10, 0.14))
def under_top(trs, top):
    zmin = min(v.co.z for v in top.data.vertices)
    vg = trs.vertex_groups.new(name="under_top"); vg.add([v.index for v in trs.data.vertices if v.co.z > zmin + 0.015], 1.0, 'REPLACE')
    mk = trs.modifiers.new("under_top", 'MASK'); mk.vertex_group = "under_top"; mk.invert_vertex_group = True
under_top(H_TRS, H_TOP); under_top(S_TRS, S_TOP)
# no see-through rips or alpha holes in any garment: the cloth is opaque everywhere
for gar in (H_TOP, H_TRS, S_TOP, S_TRS):
    for m in gar.data.materials:
        if not m or not m.use_nodes: continue
        for p in [n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED']:
            for lk in list(p.inputs["Alpha"].links): m.node_tree.links.remove(lk)
            p.inputs["Alpha"].default_value = 1.0
        try: m.blend_method = 'OPAQUE'
        except Exception: pass
# solid garments: give every garment real thickness (no paper-thin hollow shells) and smooth shading
for gar in (H_TOP, H_TRS, S_TOP, S_TRS):
    so = gar.modifiers.new("solid", 'SOLIDIFY'); so.thickness = 0.004; so.offset = 1.0; so.use_rim = True
    for p in gar.data.polygons: p.use_smooth = True
# body hidden only where it is right under the cloth (dist 1.6 cm, eroded 3 rings): skin stays at hems and inside the crotch,
# so the figure is solid everywhere the cloth stands off it (no hollow sleeves, no hole at the crotch)
for body, gar in ((HB, H_TOP), (HB, H_TRS), (SB, S_TOP), (SB, S_TRS)):
    hide_by_proximity(body, gar, "Hide." + gar.name, dist=0.016)
# skin under the trousers' crotch takes the trouser colour, so any gap reads as cloth, never skin
crotch_m = fabric("M_HeroCrotchCloth", (0.03, 0.07, 0.30), scale=600, bump=0.2)
def crotch_cloth(body, rig, m):
    body.data.materials.append(m); mi = len(body.data.materials) - 1
    hipL = bl(rig, "upperleg01.L"); hipR = bl(rig, "upperleg01.R"); pz = bl(rig, "pelvis.L").z
    for p in body.data.polygons:
        c = p.center
        ank = bl(rig, "foot.L").z + 0.06
        legs = c.z < pz + 0.06 and c.z > ank and abs(c.x) < 0.25 and not any(k in n for n in [] for k in ())
        if (abs(c.x) < 0.11 and hipL.z - 0.20 < c.z < pz + 0.06) or (ank < c.z < hipL.z - 0.05): p.material_index = mi
crotch_cloth(HB, HERO, crotch_m); crotch_cloth(SB, SHOOT, fabric("M_ShooterCrotchCloth", (0.06, 0.06, 0.08), scale=600, bump=0.2))

# ================================================================== MATERIALS
M = {}
M["lawn"] = fabric("M_Lawn", (0.10, 0.48, 0.06), scale=260, bump=0.35, rough=0.85)
M["walk"] = tiles("M_Sidewalk", (0.78, 0.74, 0.68), (0.72, 0.68, 0.62), (0.55, 0.52, 0.48), scale=1.2, rough=0.6, coat=0.0)
M["road"] = mat("M_Road", (0.10, 0.10, 0.12), rough=0.8)
M["siding"] = mat("M_Siding", (0.95, 0.80, 0.25), rough=0.55)
M["trim"] = mat("M_Trim", (0.97, 0.97, 0.95), rough=0.4)
M["roof"] = mat("M_Roof", (0.55, 0.10, 0.08), rough=0.6)
M["wallin"] = mat("M_WallTeal", (0.02, 0.42, 0.46), rough=0.7)
M["wallback"] = mat("M_WallPurple", (0.30, 0.08, 0.45), rough=0.7)
M["drywall"] = mat("M_DrywallCore", (0.93, 0.92, 0.88), rough=0.9)
M["floor"] = wood("M_Floor", (0.42, 0.22, 0.10), (0.30, 0.15, 0.07), scale=2.0)
M["rug"] = fabric("M_Rug", (0.10, 0.20, 0.70), scale=500, bump=0.5)
M["tvbody"] = mat("M_TVBody", (0.02, 0.02, 0.025), rough=0.3)
M["shelf"] = mat("M_Shelf", (0.95, 0.95, 0.95), rough=0.4)
M["frame"] = mat("M_Frame", (0.05, 0.05, 0.06), rough=0.35)
M["gun"] = mat("M_Gun", (0.04, 0.04, 0.045), rough=0.35, metal=0.6)
M["bullet"] = mat("M_Bullet", (0.95, 0.52, 0.20), rough=0.22, metal=1.0)
M["bullet_core"] = mat("M_BulletBase", (0.80, 0.62, 0.25), rough=0.25, metal=1.0)

# ================================================================== EXTERIOR: lawn, sidewalk, road, the house front
def plane(name, sx, sy, loc, material, rot=(0, 0, 0), cuts=0):
    bpy.ops.mesh.primitive_plane_add(size=1, location=loc, rotation=rot)
    o = bpy.context.active_object; o.name = name; o.scale = (sx, sy, 1); bpy.ops.object.transform_apply(scale=True)
    if cuts:
        bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.subdivide(number_cuts=cuts); bpy.ops.object.mode_set(mode='OBJECT')
    o.data.materials.append(material); return o
plane("Lawn", 30, 9.6, (0, -4.9, -0.002), M["lawn"])
plane("Sidewalk", 30, 1.6, (0, -10.5, 0.0), M["walk"])
plane("Road", 30, 7.0, (0, -14.8, -0.01), M["road"])
plane("LawnFar", 30, 8.0, (0, -22.3, -0.002), M["lawn"])
plane("Floor_in", 8.0, 4.2, (0, 2.25, 0.001), M["floor"])

# house front wall: one solid slab with a real window opening; siding boards (raised strips) on the outside face
WALL_T = 0.15
WIN = dict(x0=0.62, x1=1.52, z0=0.80, z1=2.05)
bm = bmesh.new()
def slab(x0, x1, z0, z1, y0, y1):
    bmesh.ops.create_cube(bm, size=1.0, matrix=Matrix.Translation(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2)) @ Matrix.Diagonal((x1 - x0, y1 - y0, z1 - z0, 1)))
XW0, XW1, ZW1 = -4.0, 4.0, 3.0
slab(XW0, WIN["x0"], 0, ZW1, 0, WALL_T); slab(WIN["x1"], XW1, 0, ZW1, 0, WALL_T)
slab(WIN["x0"], WIN["x1"], 0, WIN["z0"], 0, WALL_T); slab(WIN["x0"], WIN["x1"], WIN["z1"], ZW1, 0, WALL_T)
me = bpy.data.meshes.new("HouseWall"); bm.to_mesh(me); bm.free()
WALL = bpy.data.objects.new("HouseWall", me); sc.collection.objects.link(WALL)
me.materials.append(M["siding"]); me.materials.append(M["wallin"])
for p in me.polygons:
    p.material_index = 0 if p.normal.y < -0.5 else 1
# siding boards outside (y < 0): 12 cm boards with a lap shadow, cut around the window
for i in range(int(ZW1 / 0.12)):
    z = i * 0.12 + 0.06
    spans = [(XW0, XW1)] if not (WIN["z0"] - 0.06 < z < WIN["z1"] + 0.06) else [(XW0, WIN["x0"] - 0.07), (WIN["x1"] + 0.07, XW1)]
    for k, (xa, xb) in enumerate(spans):
        bd = box("Siding_%02d_%d" % (i, k), (xb - xa, 0.016, 0.115), ((xa + xb) / 2, -0.008, z), M["siding"], bevel=0.004, segs=2, rot=(R_(-4), 0, 0))
        bd.parent = WALL
# window trim (white casing outside and inside), sill; the window is OPEN (the sash is raised above the opening, no glass in the path)
for nm, sz, lc in (("Trim_L", (0.07, 0.04, WIN["z1"] - WIN["z0"] + 0.14), (WIN["x0"] - 0.035, -0.02, (WIN["z0"] + WIN["z1"]) / 2)),
                   ("Trim_R", (0.07, 0.04, WIN["z1"] - WIN["z0"] + 0.14), (WIN["x1"] + 0.035, -0.02, (WIN["z0"] + WIN["z1"]) / 2)),
                   ("Trim_T", (WIN["x1"] - WIN["x0"] + 0.14, 0.05, 0.08), ((WIN["x0"] + WIN["x1"]) / 2, -0.025, WIN["z1"] + 0.04)),
                   ("Sill", (WIN["x1"] - WIN["x0"] + 0.16, 0.24, 0.04), ((WIN["x0"] + WIN["x1"]) / 2, 0.04, WIN["z0"] - 0.02)),
                   ("TrimIn_L", (0.06, 0.03, WIN["z1"] - WIN["z0"] + 0.12), (WIN["x0"] - 0.03, WALL_T + 0.015, (WIN["z0"] + WIN["z1"]) / 2)),
                   ("TrimIn_R", (0.06, 0.03, WIN["z1"] - WIN["z0"] + 0.12), (WIN["x1"] + 0.03, WALL_T + 0.015, (WIN["z0"] + WIN["z1"]) / 2)),
                   ("TrimIn_T", (WIN["x1"] - WIN["x0"] + 0.12, 0.03, 0.06), ((WIN["x0"] + WIN["x1"]) / 2, WALL_T + 0.015, WIN["z1"] + 0.03))):
    box(nm, sz, lc, M["trim"], bevel=0.006).parent = WALL
# raised sash (frame + pane) sits ABOVE the opening, inside the wall top region
sash = box("Sash", (WIN["x1"] - WIN["x0"] - 0.02, 0.04, 0.05), ((WIN["x0"] + WIN["x1"]) / 2, WALL_T / 2, WIN["z1"] - 0.03), M["trim"], bevel=0.005)
sash.parent = WALL
# roof eave above the wall
eave = box("Eave", (8.6, 0.7, 0.12), (0, -0.2, ZW1 + 0.05), M["roof"], bevel=0.01, rot=(R_(-18), 0, 0))
# side walls + back wall of the room (inside)
box("RoomWall_L", (0.12, 4.0, 2.9), (-2.6, 2.15, 1.45), M["wallin"], bevel=0.0)
box("RoomWall_R", (0.12, 4.0, 2.9), (2.6, 2.15, 1.45), M["wallin"], bevel=0.0)
box("RoomWall_B", (5.3, 0.12, 2.9), (0, 4.0, 1.45), M["wallback"], bevel=0.0)
box("Ceiling", (5.3, 4.0, 0.06), (0, 2.1, 2.92), mat("M_Ceil", (0.95, 0.94, 0.92), rough=0.8), bevel=0.0)
box("Baseboard_B", (5.2, 0.02, 0.10), (0, 3.93, 0.05), M["trim"], bevel=0.003)
box("Baseboard_F", (5.2, 0.02, 0.10), (0, WALL_T + 0.01, 0.05), M["trim"], bevel=0.003)
rug = box("Rug", (2.2, 1.5, 0.012), (0.0, 1.9, 0.006), M["rug"], bevel=0.004)

# ---- TV on the inside front wall (left of the window), abstract colourful game image (no text)
TVX = -1.15
tv = box("TV", (1.20, 0.06, 0.70), (TVX, WALL_T + 0.05, 1.55), M["tvbody"], bevel=0.012)
scr_m = bpy.data.materials.new("M_TVScreen"); scr_m.use_nodes = True; nt = scr_m.node_tree; nt.nodes.clear()
o_ = nt.nodes.new("ShaderNodeOutputMaterial"); em = nt.nodes.new("ShaderNodeEmission"); tc = nt.nodes.new("ShaderNodeTexCoord")
wv = nt.nodes.new("ShaderNodeTexWave"); wv.inputs["Scale"].default_value = 2.0; wv.inputs["Distortion"].default_value = 6.0
cr = nt.nodes.new("ShaderNodeValToRGB")
cr.color_ramp.elements[0].color = (0.05, 0.25, 0.95, 1); cr.color_ramp.elements[1].color = (0.95, 0.15, 0.55, 1)
e3 = cr.color_ramp.elements.new(0.5); e3.color = (0.10, 0.85, 0.65, 1)
nt.links.new(tc.outputs["Generated"], wv.inputs["Vector"]); nt.links.new(wv.outputs["Fac"], cr.inputs["Fac"])
nt.links.new(cr.outputs["Color"], em.inputs["Color"]); em.inputs["Strength"].default_value = 2.2
nt.links.new(em.outputs[0], o_.inputs["Surface"])
scr = box("TVScreen", (1.12, 0.004, 0.62), (TVX, WALL_T + 0.082, 1.55), scr_m, bevel=0.0)
cab = box("TVCabinet", (1.6, 0.42, 0.45), (TVX, WALL_T + 0.21, 0.225), mat("M_Cabinet", (0.95, 0.60, 0.05), rough=0.45), bevel=0.015)
console = box("Console", (0.30, 0.20, 0.06), (TVX + 0.35, WALL_T + 0.22, 0.48), mat("M_ConsoleBody", (0.95, 0.95, 0.97), rough=0.3), bevel=0.012)

# ================================================================== Poly Haven: sofa (recoloured), plants, shrubs
def append_blend(path, names=None):
    with bpy.data.libraries.load(path, link=False) as (src, dst):
        dst.objects = [n for n in src.objects if names is None or n in names]
    out = []
    for o in dst.objects:
        if o is None: continue
        sc.collection.objects.link(o); out.append(o)
    return out
sofa = append_blend(os.path.join(ASSETS, "sofa_02", "sofa_02_1k.blend"))
for o in sofa:
    for m in o.data.materials:
        if m: colorize_obj = None
    o.parent = None
# sofa: find which side its backrest is on, rotate so the seat faces -Y (toward the wall), place it
base = [o for o in sofa if o.name.endswith("Base")][0]; seat = [o for o in sofa if o.name.endswith("Seat")][0]
vs = [base.matrix_world @ v.co for v in base.data.vertices]
hi = [v for v in vs if v.z > 0.55]; back_y = sum(v.y for v in hi) / max(1, len(hi))
yaw = 0.0 if back_y > base.matrix_world.translation.y else math.pi
SOFA_Y = 2.75
for o in sofa:
    o.matrix_world = Matrix.Translation((0, SOFA_Y, 0)) @ Matrix.Rotation(yaw, 4, 'Z') @ Matrix.Translation(-Vector((0, -0.031, 0))) @ o.matrix_world
    for m in o.data.materials:
        if not m or not m.use_nodes: continue
        nt = m.node_tree
        for p in [n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED']:
            bc = p.inputs["Base Color"]
            if bc.is_linked:
                src = bc.links[0].from_socket; bw = nt.nodes.new("ShaderNodeRGBToBW"); nt.links.new(src, bw.inputs[0])
                mul = nt.nodes.new("ShaderNodeMix"); mul.data_type = 'RGBA'; mul.blend_type = 'MULTIPLY'; mul.inputs["Factor"].default_value = 1.0
                mr = nt.nodes.new("ShaderNodeMapRange"); mr.inputs["To Min"].default_value = 0.6; mr.inputs["From Max"].default_value = 0.35
                nt.links.new(bw.outputs[0], mr.inputs["Value"])
                nt.links.new(mr.outputs[0], mul.inputs["A"]); mul.inputs["B"].default_value = (0.95, 0.55, 0.03, 1)
                nt.links.new(mul.outputs["Result"], bc)
            else:
                bc.default_value = (0.95, 0.62, 0.04, 1)
bpy.context.view_layer.update()
sv = [seat.matrix_world @ v.co for v in seat.data.vertices]
mid = [v for v in sv if abs(v.x) < 0.45]
SEAT_TOP = max(v.z for v in mid if abs(v.y - SOFA_Y) < 0.15) if mid else max(v.z for v in sv)
SEAT_FRONT_Y = min(v.y for v in sv)
print("SOFA yaw", round(math.degrees(yaw)), "seat top", round(SEAT_TOP, 3), "seat front y", round(SEAT_FRONT_Y, 3))
sc["SEAT_TOP"] = SEAT_TOP; sc["SEAT_FRONT_Y"] = SEAT_FRONT_Y; sc["SOFA_Y"] = SOFA_Y
plants = append_blend(os.path.join(ASSETS, "potted_plant_01", "potted_plant_01_1k.blend"))
for o in plants:
    if o.parent is None: o.location = (2.15, 3.55, 0.0); o.scale = (1.3, 1.3, 1.3)
for i, (x, y, s) in enumerate(((-3.0, -0.55, 1.2), (-1.7, -0.6, 1.0), (2.4, -0.55, 1.1), (3.4, -0.6, 1.3))):
    sh = append_blend(os.path.join(ASSETS, "shrub_01", "shrub_01_1k.blend"))
    for o in sh:
        if o.parent is None: o.location = (x, y, 0); o.scale = (s, s, s); o.name = "Shrub_%d_%s" % (i, o.name)
for o in list(plants) + [o for o in sc.objects if o.name.startswith("Shrub_")]:
    if o.type == 'MESH': soften(o, rough_min=0.4)

# ---- back wall: shelves with coloured game cases (no text) and the DA KRAS FILMS poster above the sofa
for row, z in enumerate((1.15, 1.55)):
    sh = box("Shelf_%d" % row, (0.9, 0.22, 0.025), (1.65, 3.82, z), M["shelf"], bevel=0.004)
    xs = 1.25
    for k in range(9):
        col = [(0.9, 0.1, 0.1), (0.1, 0.35, 0.95), (0.1, 0.75, 0.25), (0.98, 0.8, 0.05), (0.6, 0.1, 0.8)][(k + row) % 5]
        w_ = 0.016
        box("Case_%d_%d" % (row, k), (w_, 0.135, 0.17), (xs, 3.80, z + 0.0125 + 0.085), mat("M_Case_%d_%d" % (row, k), col, rough=0.35), bevel=0.002)
        xs += w_ + 0.006 + (0.05 if k == 5 else 0)
# poster with the logo, framed
logo_img = bpy.data.images.load(os.path.abspath(LOGO_W)); logo_img.name = "DaKrasFilms_logo_white"; logo_img.pack()
logo_dark = bpy.data.images.load(os.path.abspath(LOGO_D)); logo_dark.name = "DaKrasFilms_logo_dark"; logo_dark.pack()
def poster_mat(name, img, bg):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree
    p = nt.nodes["Principled BSDF"]; p.inputs["Roughness"].default_value = 0.45
    tx = nt.nodes.new("ShaderNodeTexImage"); tx.image = img; tx.extension = 'CLIP'
    tc = nt.nodes.new("ShaderNodeTexCoord"); mp = nt.nodes.new("ShaderNodeMapping")
    mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = 'RGBA'; mx.inputs["A"].default_value = (*bg, 1)
    nt.links.new(tc.outputs["UV"], mp.inputs["Vector"]); nt.links.new(mp.outputs["Vector"], tx.inputs["Vector"])
    nt.links.new(tx.outputs["Alpha"], mx.inputs["Factor"]); nt.links.new(tx.outputs["Color"], mx.inputs["B"])
    nt.links.new(mx.outputs["Result"], p.inputs["Base Color"])
    return m, mp
aspect = logo_img.size[0] / max(1, logo_img.size[1])
PW = 0.95; PH = PW / aspect * 1.35
pm, pmap = poster_mat("M_Poster", logo_img, (0.05, 0.10, 0.55))
pmap.inputs["Scale"].default_value = (1.12, 1.12 * 1.35, 1); pmap.inputs["Location"].default_value = (-0.06, -0.06 * 1.35 - 0.175, 0)
bpy.ops.mesh.primitive_plane_add(size=1, location=(-0.35, 3.935, 1.62), rotation=(R_(90), 0, 0))
POSTER = bpy.context.active_object; POSTER.name = "LogoPoster"; POSTER.scale = (PW, PH, 1); bpy.ops.object.transform_apply(scale=True)
POSTER.data.materials.append(pm)
for nm, sz, lc in (("PF_T", (PW + 0.05, 0.03, 0.025), (-0.35, 3.925, 1.62 + PH / 2)), ("PF_B", (PW + 0.05, 0.03, 0.025), (-0.35, 3.925, 1.62 - PH / 2)),
                   ("PF_L", (0.025, 0.03, PH + 0.05), (-0.35 - PW / 2, 3.925, 1.62)), ("PF_R", (0.025, 0.03, PH + 0.05), (-0.35 + PW / 2, 3.925, 1.62))):
    box(nm, sz, lc, M["frame"], bevel=0.003)

# ================================================================== THE BULLET (one object, constant size, round-nose 9 mm slug)
def lathe(name, prof, material, segs=40):
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    rings = []
    for (r, z) in prof:
        ring = []
        for k in range(segs):
            t = 2 * math.pi * k / segs
            ring.append(bm.verts.new((r * math.cos(t), r * math.sin(t), z)))
        rings.append(ring)
    for a_, b_ in zip(rings, rings[1:]):
        for k in range(segs):
            bm.faces.new((a_[k], a_[(k + 1) % segs], b_[(k + 1) % segs], b_[k]))
    bm.faces.new(rings[0][::-1])
    tip = bm.verts.new((0, 0, prof[-1][1] + 0.0004))
    for k in range(segs):
        bm.faces.new((rings[-1][k], rings[-1][(k + 1) % segs], tip))
    bm.normal_update(); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); sc.collection.objects.link(o); me.materials.append(material)
    for p in me.polygons: p.use_smooth = True
    return o
R0 = 0.0045
prof = [(R0 * 0.92, 0.0), (R0, 0.0006), (R0, 0.0075)]
for k in range(1, 9):
    t = k / 8 * math.pi / 2
    prof.append((R0 * math.cos(t) * 0.98 + 0.0001, 0.0075 + 0.0085 * math.sin(t)))
BUL = lathe("Bullet", prof, M["bullet"])   # local +Z = flight direction (nose at +Z), length 16.4 mm
BUL.data.materials.append(M["bullet_core"])
for p in BUL.data.polygons:
    if p.center.z < 0.0003: p.material_index = 1

# ================================================================== THE PISTOL (generic, no markings), muzzle at local +Y, grip origin at 0
gun_parts = []
gun_parts.append(box("G_slide", (0.028, 0.185, 0.034), (0, 0.065, 0.055), M["gun"], bevel=0.003))
gun_parts.append(box("G_frame", (0.026, 0.150, 0.020), (0, 0.055, 0.030), M["gun"], bevel=0.003))
g = box("G_grip", (0.030, 0.050, 0.115), (0, -0.005, -0.025), M["gun"], bevel=0.006, rot=(R_(-14), 0, 0)); gun_parts.append(g)
bpy.ops.mesh.primitive_torus_add(major_radius=0.022, minor_radius=0.003, location=(0, 0.035, 0.012), rotation=(0, R_(90), 0))
tg = bpy.context.active_object; tg.name = "G_guard"; tg.data.materials.append(M["gun"]); tg.scale = (1, 1, 0.75); gun_parts.append(tg)
gun_parts.append(cyl("G_muzzle", 0.0055, 0.01, (0, 0.158, 0.060), M["gun"], rot=(R_(90), 0, 0)))
bpy.ops.object.select_all(action='DESELECT')
for o in gun_parts: o.select_set(True)
bpy.context.view_layer.objects.active = gun_parts[0]
for o in gun_parts:
    for md in list(o.modifiers):
        bpy.context.view_layer.objects.active = o; bpy.ops.object.modifier_apply(modifier=md.name)
bpy.context.view_layer.objects.active = gun_parts[0]; bpy.ops.object.join()
GUN = bpy.context.active_object; GUN.name = "Pistol"
GUN["muzzle"] = (0.0, 0.165, 0.060)
# muzzle flash: a bright stylised star, keyed in 02 (scale 0 -> 1 -> 0 inside 4 frames)
fl_m = mat("M_Flash", (1.0, 0.5, 0.05), emit=((1.0, 0.45, 0.05), 5.0))
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=0.03, location=(0, 0, 0))
FLASH = bpy.context.active_object; FLASH.name = "MuzzleFlash"; FLASH.data.materials.append(fl_m)
for v in FLASH.data.vertices:
    v.co *= (1.0 + 1.6 * random.random() ** 3)
FLASH.scale = (0.001, 0.001, 0.001)

# ================================================================== THE COLLECTOR'S BOX SET (one prop)
# Solid slipcase (front, back, sides, bottom; open top) holding 7 solid content layers that stand upright inside.
# Box local frame: x = width (his left/right), y = depth (front at -y faces the wall, back at +y faces his chest), z = up, origin at the bottom centre.
BW, BH, BD = 0.30, 0.22, 0.12
T = 0.006
BOX = bpy.data.objects.new("GameBoxSet", None); sc.collection.objects.link(BOX); BOX.empty_display_size = 0.1
art_m = bpy.data.materials.new("M_BoxArt"); art_m.use_nodes = True; nt = art_m.node_tree
p = nt.nodes["Principled BSDF"]; p.inputs["Roughness"].default_value = 0.35; p.inputs["Coat Weight"].default_value = 0.4
tc = nt.nodes.new("ShaderNodeTexCoord"); sep = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(tc.outputs["Object"], sep.inputs[0])
# deep purple -> blue gradient with a gold emblem ring (abstract, no text)
gr = nt.nodes.new("ShaderNodeValToRGB"); gr.color_ramp.elements[0].color = (0.10, 0.02, 0.35, 1); gr.color_ramp.elements[1].color = (0.02, 0.20, 0.75, 1)
mz = nt.nodes.new("ShaderNodeMath"); mz.operation = 'MULTIPLY_ADD'; mz.inputs[1].default_value = 1 / BH; mz.inputs[2].default_value = 0.0
nt.links.new(sep.outputs["Z"], mz.inputs[0]); nt.links.new(mz.outputs[0], gr.inputs["Fac"])
# emblem: ring centred at (0.07, 0.13) on the face
cx = nt.nodes.new("ShaderNodeCombineXYZ"); nt.links.new(sep.outputs["X"], cx.inputs["X"]); nt.links.new(sep.outputs["Z"], cx.inputs["Y"])
dst = nt.nodes.new("ShaderNodeVectorMath"); dst.operation = 'DISTANCE'; dst.inputs[1].default_value = (0.075, 0.125, 0)
nt.links.new(cx.outputs[0], dst.inputs[0])
ring = nt.nodes.new("ShaderNodeMapRange"); ring.inputs["From Min"].default_value = 0.035; ring.inputs["From Max"].default_value = 0.05
nt.links.new(dst.outputs["Value"], ring.inputs["Value"])
ring2 = nt.nodes.new("ShaderNodeMath"); ring2.operation = 'PINGPONG'; ring2.inputs[1].default_value = 0.5
nt.links.new(ring.outputs[0], ring2.inputs[0])
ringm = nt.nodes.new("ShaderNodeMath"); ringm.operation = 'GREATER_THAN'; ringm.inputs[1].default_value = 0.3
nt.links.new(ring2.outputs[0], ringm.inputs[0])
gold = nt.nodes.new("ShaderNodeMix"); gold.data_type = 'RGBA'; gold.inputs["B"].default_value = (1.0, 0.72, 0.08, 1)
nt.links.new(gr.outputs["Color"], gold.inputs["A"]); nt.links.new(ringm.outputs[0], gold.inputs["Factor"])
# the logo (white) on the lower-left of the front face, mapped from object coords
lt = nt.nodes.new("ShaderNodeTexImage"); lt.image = logo_img; lt.extension = 'CLIP'
lmap = nt.nodes.new("ShaderNodeMapping")
LOGO_W_M = 0.16; LOGO_X0 = -0.105; LOGO_Z0 = 0.016
lmap.inputs["Location"].default_value = (-LOGO_X0 / LOGO_W_M, -LOGO_Z0 / (LOGO_W_M / aspect), 0)
lmap.inputs["Scale"].default_value = (1 / LOGO_W_M, 1 / (LOGO_W_M / aspect), 1)
nt.links.new(cx.outputs[0], lmap.inputs["Vector"]); nt.links.new(lmap.outputs[0], lt.inputs["Vector"])
lmix = nt.nodes.new("ShaderNodeMix"); lmix.data_type = 'RGBA'
nt.links.new(gold.outputs["Result"], lmix.inputs["A"]); nt.links.new(lt.outputs["Color"], lmix.inputs["B"]); nt.links.new(lt.outputs["Alpha"], lmix.inputs["Factor"])
# CRACKS: voronoi edges inside a keyed radius around the impact point; HOLE: a dark disc (keyed radius). Both start at 0.
IMP_LOCAL = Vector((0.0, -BD / 2, BH - 0.020))       # impact point on the front face (box local)
sep2 = nt.nodes.new("ShaderNodeVectorMath"); sep2.operation = 'DISTANCE'; sep2.inputs[1].default_value = (IMP_LOCAL.x, IMP_LOCAL.z, 0)
nt.links.new(cx.outputs[0], sep2.inputs[0])
vor = nt.nodes.new("ShaderNodeTexVoronoi"); vor.feature = 'DISTANCE_TO_EDGE'; vor.inputs["Scale"].default_value = 45.0
nt.links.new(tc.outputs["Object"], vor.inputs["Vector"])
edge = nt.nodes.new("ShaderNodeMath"); edge.operation = 'LESS_THAN'; edge.inputs[1].default_value = 0.035
nt.links.new(vor.outputs["Distance"], edge.inputs[0])
# radial spokes: angle bands
ang = nt.nodes.new("ShaderNodeVectorMath"); ang.operation = 'SUBTRACT'; ang.inputs[1].default_value = (IMP_LOCAL.x, IMP_LOCAL.z, 0)
nt.links.new(cx.outputs[0], ang.inputs[0])
sp = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(ang.outputs[0], sp.inputs[0])
at = nt.nodes.new("ShaderNodeMath"); at.operation = 'ARCTAN2'; nt.links.new(sp.outputs["Y"], at.inputs[0]); nt.links.new(sp.outputs["X"], at.inputs[1])
spn = nt.nodes.new("ShaderNodeTexNoise"); spn.inputs["Scale"].default_value = 3.0; spn.noise_dimensions = '1D'
nt.links.new(at.outputs[0], spn.inputs["W"])
spm = nt.nodes.new("ShaderNodeMath"); spm.operation = 'MULTIPLY'; spm.inputs[1].default_value = 9.0
nt.links.new(spn.outputs["Fac"], spm.inputs[0])
spf = nt.nodes.new("ShaderNodeMath"); spf.operation = 'FRACT'; nt.links.new(spm.outputs[0], spf.inputs[0])
spk = nt.nodes.new("ShaderNodeMath"); spk.operation = 'LESS_THAN'; spk.inputs[1].default_value = 0.07; nt.links.new(spf.outputs[0], spk.inputs[0])
cmax = nt.nodes.new("ShaderNodeMath"); cmax.operation = 'MAXIMUM'; nt.links.new(edge.outputs[0], cmax.inputs[0]); nt.links.new(spk.outputs[0], cmax.inputs[1])
CR = nt.nodes.new("ShaderNodeValue"); CR.name = "CrackRadius"; CR.outputs[0].default_value = 0.0
inr = nt.nodes.new("ShaderNodeMath"); inr.operation = 'LESS_THAN'; nt.links.new(sep2.outputs["Value"], inr.inputs[0]); nt.links.new(CR.outputs[0], inr.inputs[1])
crk = nt.nodes.new("ShaderNodeMath"); crk.operation = 'MULTIPLY'; nt.links.new(cmax.outputs[0], crk.inputs[0]); nt.links.new(inr.outputs[0], crk.inputs[1])
HR = nt.nodes.new("ShaderNodeValue"); HR.name = "HoleRadius"; HR.outputs[0].default_value = 0.0
hol = nt.nodes.new("ShaderNodeMath"); hol.operation = 'LESS_THAN'; nt.links.new(sep2.outputs["Value"], hol.inputs[0]); nt.links.new(HR.outputs[0], hol.inputs[1])
cm = nt.nodes.new("ShaderNodeMix"); cm.data_type = 'RGBA'; cm.inputs["B"].default_value = (0.92, 0.92, 1.0, 1)
nt.links.new(lmix.outputs["Result"], cm.inputs["A"]); nt.links.new(crk.outputs[0], cm.inputs["Factor"])
hm = nt.nodes.new("ShaderNodeMix"); hm.data_type = 'RGBA'; hm.inputs["B"].default_value = (0.015, 0.01, 0.01, 1)
nt.links.new(cm.outputs["Result"], hm.inputs["A"]); nt.links.new(hol.outputs[0], hm.inputs["Factor"])
nt.links.new(hm.outputs["Result"], p.inputs["Base Color"])
# the cracks are raised a little (bump)
bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.6; bp.inputs["Distance"].default_value = 0.001
nt.links.new(crk.outputs[0], bp.inputs["Height"]); nt.links.new(bp.outputs["Normal"], p.inputs["Normal"])
shell_m = mat("M_BoxShell", (0.08, 0.02, 0.30), rough=0.35, coat=0.4)
inner_m = mat("M_BoxInner", (0.02, 0.02, 0.05), rough=0.6)

def prism(name, outline, y0, y1, material, parent, mats_side=None):
    """solid extrusion of a 2D outline (x, z) between y0 and y1 (closed mesh)"""
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    f0 = [bm.verts.new((x, y0, z)) for x, z in outline]
    f1 = [bm.verts.new((x, y1, z)) for x, z in outline]
    bm.faces.new(f0[::-1]); bm.faces.new(f1)
    n = len(outline)
    for k in range(n):
        bm.faces.new((f0[k], f0[(k + 1) % n], f1[(k + 1) % n], f1[k]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); sc.collection.objects.link(o); o.parent = parent
    me.materials.append(material)
    bv = o.modifiers.new("bev", 'BEVEL'); bv.width = 0.0008; bv.segments = 2; bv.limit_method = 'ANGLE'
    return o
def rect(x0, x1, z0, z1): return [(x0, z0), (x1, z0), (x1, z1), (x0, z1)]
# slipcase walls (solid)
FRONT = prism("Box_Front", rect(-BW / 2, BW / 2, 0, BH), -BD / 2, -BD / 2 + T, shell_m, BOX)
FRONT.data.materials.append(art_m)
for p in FRONT.data.polygons:
    if p.normal.y < -0.9: p.material_index = 1
FRONT.data.uv_layers.new()
BACK = prism("Box_Back", rect(-BW / 2, BW / 2, 0, BH), BD / 2 - T, BD / 2, shell_m, BOX)
prism("Box_SideL", rect(BW / 2 - T, BW / 2, 0, BH), -BD / 2 + T, BD / 2 - T, shell_m, BOX)
prism("Box_SideR", rect(-BW / 2, -BW / 2 + T, 0, BH), -BD / 2 + T, BD / 2 - T, shell_m, BOX)
prism("Box_Bottom", rect(-BW / 2 + T, BW / 2 - T, 0, T), -BD / 2 + T, BD / 2 - T, shell_m, BOX)
# content layers: front (y small) to back; each SOLID, with a notch chunk above the bullet path that bursts out when the bullet passes
LAYERS = [("ArtBook", (0.90, 0.08, 0.06), 0.016), ("DiscCase1", (0.05, 0.25, 0.95), 0.014), ("Manual", (0.97, 0.95, 0.88), 0.014),
          ("DiscCase2", (0.06, 0.72, 0.20), 0.014), ("Steelbook", (0.75, 0.78, 0.82), 0.014), ("DiscCase3", (0.98, 0.78, 0.04), 0.014),
          ("PosterFolio", (0.95, 0.35, 0.05), 0.016)]
gap = (BD - 2 * T - sum(t for *_, t in LAYERS)) / (len(LAYERS) + 1)
NW, ND = 0.030, 0.030                  # notch width and depth from the top edge
xi, zi0, zi1 = BW / 2 - T - 0.002, T, BH - 0.002
y = -BD / 2 + T + gap
sc["LAYERS"] = []
lay_info = []
for i, (nm, col, th) in enumerate(LAYERS):
    m = mat("M_" + nm, col, rough=0.3 if "Case" in nm or "Steel" in nm else 0.55, metal=0.6 if "Steel" in nm else 0.0, coat=0.3)
    outline = [(-xi, zi0), (xi, zi0), (xi, zi1), (NW / 2, zi1), (NW / 2, zi1 - ND), (-NW / 2, zi1 - ND), (-NW / 2, zi1), (-xi, zi1)]
    L = prism("Layer_%d_%s" % (i, nm), outline, y, y + th, m, BOX)
    # the notch chunk (two halves) fills the gap flush; same material
    halves = []
    for side, (xa, xb) in (("L", (0.0, NW / 2)), ("R", (-NW / 2, 0.0))):
        c = prism("Chunk_%d_%s" % (i, side), rect(xa + 0.0002 * (1 if side == "L" else -1) * 0, xb, zi1 - ND, zi1), y, y + th, m, BOX)
        halves.append(c.name)
    lay_info.append({"name": L.name, "y0": y, "y1": y + th, "chunks": halves, "disc": "Disc" in nm or "Steel" in nm})
    # disc inside every disc case: a thin iridescent ring between the case walls (seen in the burst shards and at the notch)
    y += th + gap
import json as _json
sc["LAYER_INFO"] = _json.dumps(lay_info)
sc["BOX_DIMS"] = [BW, BH, BD]; sc["IMP_LOCAL"] = list(IMP_LOCAL); sc["NOTCH"] = [NW, ND, zi1]
# disc shards (glitter) and card flakes: small triangles that start INSIDE each notch chunk (hidden by it), burst out in 02
shard_m = mat("M_DiscShard", (0.85, 0.88, 0.95), rough=0.08, metal=1.0, coat=1.0)
flake_m = mat("M_Flake", (0.95, 0.90, 0.80), rough=0.6)
for li in lay_info:
    for k in range(10):
        me = bpy.data.meshes.new("Shard"); bm = bmesh.new()
        s = random.uniform(0.004, 0.008)
        vv = [bm.verts.new((random.uniform(-s, s), random.uniform(-0.001, 0.001), random.uniform(-s, s))) for _ in range(3)]
        bm.faces.new(vv); bm.to_mesh(me); bm.free()
        o = bpy.data.objects.new("Shard_%s_%d" % (li["name"].split("_")[1], k), me); sc.collection.objects.link(o); o.parent = BOX
        me.materials.append(shard_m if li["disc"] else flake_m)
        so = o.modifiers.new("solid", 'SOLIDIFY'); so.thickness = 0.0008
        o.location = (random.uniform(-NW / 2 + 0.006, NW / 2 - 0.006), (li["y0"] + li["y1"]) / 2, zi1 - random.uniform(0.006, ND - 0.008))
# energy ring (emissive torus), keyed in 02
ring_m = mat("M_EnergyRing", (0.3, 0.8, 1.0), emit=((0.35, 0.85, 1.0), 12.0))
bpy.ops.mesh.primitive_torus_add(major_radius=0.02, minor_radius=0.0015, location=(0, 0, 0))
RING = bpy.context.active_object; RING.name = "EnergyRing"; RING.data.materials.append(ring_m); RING.scale = (0.001, 0.001, 0.001)
# wall damage: entry hole decal outside, exit hole inside, and splinters/dust chips (keyed in 02)
hole_m = mat("M_WallHole", (0.02, 0.015, 0.01), rough=0.9)
for nm in ("WallHole_out", "WallHole_in"):
    bpy.ops.mesh.primitive_circle_add(vertices=24, radius=0.009, fill_type='NGON', location=(0, 0, 0))
    h = bpy.context.active_object; h.name = nm; h.data.materials.append(hole_m); h.scale = (0.001, 0.001, 0.001)
chip_m = [mat("M_ChipSiding", (0.95, 0.80, 0.25), rough=0.6), mat("M_ChipDry", (0.93, 0.92, 0.88), rough=0.9)]
for side in (0, 1):
    for k in range(14):
        me = bpy.data.meshes.new("Chip"); bm = bmesh.new()
        s = random.uniform(0.006, 0.016)
        vv = [bm.verts.new((random.uniform(-s, s), random.uniform(-s, s) * 0.3, random.uniform(-s, s))) for _ in range(4)]
        bm.faces.new(vv[:3]); bm.faces.new((vv[0], vv[2], vv[3])); bm.to_mesh(me); bm.free()
        o = bpy.data.objects.new("Chip_%d_%02d" % (side, k), me); sc.collection.objects.link(o); me.materials.append(chip_m[side])
        so = o.modifiers.new("solid", 'SOLIDIFY'); so.thickness = 0.002
        o.scale = (0.001, 0.001, 0.001)

# ================================================================== LOOK: deep rich colour, fast clean render
sc.view_settings.view_transform = 'AgX'
try: sc.view_settings.look = 'AgX - Punchy'
except Exception: pass
sc.view_settings.exposure = -0.3
sc.render.engine = 'CYCLES'
sc.cycles.samples = 64; sc.cycles.adaptive_threshold = 0.04; sc.cycles.use_adaptive_sampling = True; sc.cycles.use_denoising = True
sc.cycles.denoiser = 'OPENIMAGEDENOISE'
try:
    vl = sc.view_layers[0]; vl.cycles.denoising_store_passes = False
    sc.cycles.denoising_input_passes = 'RGB_ALBEDO_NORMAL'
except Exception: pass
sc.cycles.max_bounces = 6; sc.cycles.diffuse_bounces = 3; sc.cycles.glossy_bounces = 3; sc.cycles.transmission_bounces = 6
sc.cycles.transparent_max_bounces = 16; sc.cycles.caustics_reflective = sc.cycles.caustics_refractive = False
sc.render.use_persistent_data = True
sc.render.use_simplify = True; sc.render.simplify_subdivision_render = 2; sc.cycles.texture_limit_render = '2048'
sc.render.use_motion_blur = False
# sky: clear saturated blue (Nishita-free gradient so it stays bright and clean)
w = bpy.data.worlds.new("World"); sc.world = w; w.use_nodes = True; nt = w.node_tree
bg = nt.nodes["Background"]; tc = nt.nodes.new("ShaderNodeNewGeometry"); sp = nt.nodes.new("ShaderNodeSeparateXYZ")
neg = nt.nodes.new("ShaderNodeVectorMath"); neg.operation = 'SCALE'; neg.inputs["Scale"].default_value = -1.0
nt.links.new(tc.outputs["Incoming"], neg.inputs[0]); nt.links.new(neg.outputs[0], sp.inputs[0])
crw = nt.nodes.new("ShaderNodeValToRGB"); crw.color_ramp.elements[0].position = 0.0; crw.color_ramp.elements[0].color = (0.30, 0.65, 1.0, 1)
crw.color_ramp.elements[1].position = 0.45; crw.color_ramp.elements[1].color = (0.02, 0.22, 0.95, 1)
nt.links.new(sp.outputs["Z"], crw.inputs["Fac"]); bg.inputs["Strength"].default_value = 1.0
# the camera sees a clear saturated blue sky; light from the sky stays soft and pale
lp = nt.nodes.new("ShaderNodeLightPath"); skym = nt.nodes.new("ShaderNodeMix"); skym.data_type = 'RGBA'
skym.inputs["A"].default_value = (0.70, 0.85, 1.0, 1); nt.links.new(crw.outputs["Color"], skym.inputs["B"])
nt.links.new(lp.outputs["Is Camera Ray"], skym.inputs["Factor"]); nt.links.new(skym.outputs["Result"], bg.inputs["Color"])
sun_d = bpy.data.lights.new("Sun", 'SUN'); sun_d.energy = 4.0; sun_d.angle = R_(3); sun_d.color = (1.0, 0.95, 0.86)
SUN = bpy.data.objects.new("Sun", sun_d); sc.collection.objects.link(SUN); SUN.rotation_euler = (R_(50), 0, R_(-30))
def area(name, loc, target, power, size, col):
    ld = bpy.data.lights.new(name, 'AREA'); ld.energy = power; ld.size = size; ld.color = col; ld.shape = 'DISK'
    o = bpy.data.objects.new(name, ld); sc.collection.objects.link(o); o.location = loc
    d = Vector(target) - Vector(loc); o.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    return o
area("Room_Key", (-0.9, 0.9, 2.5), (0.0, 2.6, 1.0), 260, 1.4, (1.0, 0.93, 0.85))
area("Room_Fill", (1.3, 1.2, 1.7), (0.0, 2.6, 1.1), 110, 1.8, (0.85, 0.92, 1.0))
area("Room_Rim", (0.9, 3.7, 2.4), (0.0, 2.7, 1.3), 140, 1.0, (1.0, 0.85, 0.7))
area("Room_Ceil", (0.0, 2.0, 2.85), (0.0, 2.0, 0.0), 160, 2.2, (1.0, 0.97, 0.92))
area("Room_Back", (0.0, 1.0, 2.6), (0.0, 3.9, 1.5), 120, 1.6, (1.0, 0.95, 0.9))
area("TV_Glow", (TVX, WALL_T + 0.25, 1.55), (TVX, 2.5, 1.2), 25, 0.9, (0.45, 0.55, 1.0))

sc["WALL_T"] = WALL_T; sc["WIN"] = [WIN["x0"], WIN["x1"], WIN["z0"], WIN["z1"]]
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("BUILD_OK", OUT)
for r in (HERO, SHOOT):
    print("BONES", r.name, {n: tuple(round(x, 3) for x in r.data.bones[n].head_local) for n in ("head", "neck01", "spine03", "upperarm01.R", "wrist.R", "pelvis.L", "upperleg01.L", "lowerleg01.L", "foot.L")})
