"""ShoeBomber v011 stage A: cast (one model per character, real MakeHuman garments, solid bodies), sets, props, look.
blender -b --python 01_build.py -- <out.blend>
Every set hangs under its own root empty so 02_animate.py can place it where the one continuous camera needs it:
  SET_Cabin    economy cabin, aisle along +Y (forward), floor z=0. The bomber's row is y=0, left block, aisle seat.
               An exit-row gap (open floor across the cabin) runs y 0.35..1.75 in front of his row.
  SET_Void     deep teal studio sphere for the cutaway shoe (beat 7)
  SET_Sky      the airliner (DA KRAS FILMS livery) over a cloud deck (beat 8)
  SET_Airport  security lane: roller bed, X-ray tunnel, trays (logo in the tray bottom), walk-through arch (beat 9)"""
import bpy, bmesh, sys, math, random, json
from mathutils import Vector, Matrix
exec(open("/home/user/Muhammed/blender/ShoeBomber_v011/scripts/lib.py").read())
OUT = sys.argv[sys.argv.index("--") + 1:][0]
A = "/opt/assets/sb/"
LOGO_DARK = "/home/user/Muhammed/blender/assets/brand/DaKrasFilms_logo_dark.png"
LOGO_WHITE = "/home/user/Muhammed/blender/assets/brand/DaKrasFilms_logo_white.png"
random.seed(7)
for ob in list(bpy.data.objects): bpy.data.objects.remove(ob, do_unlink=True)
sc = bpy.context.scene
sc.render.fps = 60; sc.frame_start, sc.frame_end = 1, 1469
sc.render.resolution_x, sc.render.resolution_y = 1080, 1920

def coll(name):
    c = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if c.name not in sc.collection.children: sc.collection.children.link(c)
    return c
def to_coll(objs, c):
    for o in objs:
        for u in list(o.users_collection): u.objects.unlink(o)
        c.objects.link(o)
def tree(o):
    out = [o]
    for ch in o.children: out += tree(ch)
    return out

# ================================================================== CAST
SW = "toigo_fisherman_sweater/toigo_fisherman_sweater.mhclo"; WP = "toigo_wool_pants/toigo_wool_pants.mhclo"
POLO = "namuhekam_male_polo_shirt/namuhekam_male_polo_shirt.mhclo"; TM = "elvs_crude_t-shirt_male/elvs_crude_t-shirt_male.mhclo"
TF = "joepal_crude_t-shirt_female/joepal_crude_t-shirt_female.mhclo"; TT = "toigo_basic_tucked_t-shirt/toigo_basic_tucked_t-shirt.mhclo"
FSUIT = "toigo_female_double-breasted_suit/toigo_female_double-breasted_suit.mhclo"
RACE = {"asian": 0.05, "caucasian": 0.85, "african": 0.10}
#            name        g    age  race                                               hair                    skin                                                   brow                         clothes      shoes                    h     wgt  colours (top, trousers)
CAST = [("Bomber",    1.0, 0.42, {"asian": 0.05, "caucasian": 0.55, "african": 0.40}, "short04/short04.mhclo", "young_caucasian_male/young_caucasian_male.mhmat", "eyebrow001/eyebrow001.mhclo", [SW, WP], None, 0.78, 0.45, (0.85, 0.36, 0.02), (0.05, 0.07, 0.20)),
        ("Attendant", 0.0, 0.40, RACE, "ponytail01/ponytail01.mhclo", "young_caucasian_female/young_caucasian_female.mhmat", "eyebrow010/eyebrow010.mhclo", [FSUIT], "shoes01/shoes01.mhclo", 0.5, 0.45, (0.62, 0.02, 0.06), (0.62, 0.02, 0.06)),
        ("Steward",   1.0, 0.50, {"asian": 0.05, "caucasian": 0.10, "african": 0.85}, "afro01/afro01.mhclo", "young_african_male/young_african_male.mhmat", "eyebrow004/eyebrow004.mhclo", [POLO, WP], "shoes02/shoes02.mhclo", 0.55, 0.5, (0.85, 0.85, 0.88), (0.04, 0.06, 0.22)),
        ("PaxA",      1.0, 0.62, RACE, "short01/short01.mhclo", "middleage_caucasian_male/middleage_caucasian_male.mhmat", "eyebrow002/eyebrow002.mhclo", [TM, WP], "shoes03/shoes03.mhclo", 0.6, 0.62, (0.10, 0.62, 0.12), (0.30, 0.17, 0.06)),
        ("PaxW",      0.0, 0.55, {"asian": 0.85, "caucasian": 0.10, "african": 0.05}, "bob02/bob02.mhclo", "middleage_asian_female/middleage_asian_female.mhmat", "eyebrow007/eyebrow007.mhclo", [TF, WP], "shoes01/shoes01.mhclo", 0.45, 0.5, (0.85, 0.05, 0.50), (0.02, 0.30, 0.36)),
        ("Traveller", 1.0, 0.38, {"asian": 0.70, "caucasian": 0.25, "african": 0.05}, "short02/short02.mhclo", "young_asian_male/young_asian_male.mhmat", "eyebrow003/eyebrow003.mhclo", [TT, WP], None, 0.55, 0.45, (0.95, 0.72, 0.02), (0.06, 0.08, 0.30)),
        ("AirWoman",  0.0, 0.42, {"asian": 0.05, "caucasian": 0.15, "african": 0.80}, "braid01/braid01.mhclo", "young_african_female/young_african_female.mhmat", "eyebrow008/eyebrow008.mhclo", [TF, WP], None, 0.5, 0.45, (0.10, 0.55, 0.80), (0.35, 0.05, 0.40))]
RIGS = {}
for (n, g, a, race, hair, skin, brow, cl, sh, h, wgt, ctop, cbot) in CAST:
    r, b = human(n, g, a, race, hair, skin, brow, height=h, weight=wgt, shoes=sh, clothes=cl, cup=0.35)
    bake_keys(b)
    if g > 0.5: flatten_chest(r, b)
    flatten_crotch(r, b)
    RIGS[n] = (r, b)
    tops = [c for c in r.children if c.type == 'MESH' and any(k in c.name for k in ("sweater", "shirt", "suit"))]
    bots = [c for c in r.children if c.type == 'MESH' and "pants" in c.name]
    for t in tops: colorize(t, ctop, gain=1.5); t.name = n + ".top"
    for t in bots: colorize(t, cbot, gain=1.5); t.name = n + ".trousers"
    # trousers under a top: the waistband the top covers is masked (no waistband poking through the knit)
    for t in bots:
        for tp in tops:
            zmin = min(v.co.z for v in tp.data.vertices)
            rise = 0.11 if n == "Bomber" else 0.02      # the bomber lies prone: his waistband must stay under the sweater hem
            vg = t.vertex_groups.new(name="under_top"); vg.add([v.index for v in t.data.vertices if v.co.z > zmin + rise], 1.0, 'REPLACE')
            mk = t.modifiers.new("under_top", 'MASK'); mk.vertex_group = "under_top"; mk.invert_vertex_group = True
    # client lesson: SOLID bodies. Drop MPFB's delete-group masks; keep all skin and pull it in a few mm under cloth.
    for m in list(b.modifiers):
        if m.type == 'MASK' and m.name.startswith("Delete.") and "shoes" not in m.name: b.modifiers.remove(m)
    solid_under(b, tops + bots)
    if sh is None: socks(r, b, (0.012, 0.015, 0.05) if n == "Bomber" else (0.75, 0.04, 0.06), n)
    eye_fix(r)
    for m in b.data.materials: tint(m, (1.0, 0.90, 0.82))
HAIRT = {"Bomber": (0.42, 0.26, 0.15), "Attendant": (0.55, 0.25, 0.10), "Steward": (0.25, 0.20, 0.17), "PaxA": (0.60, 0.55, 0.50),
         "PaxW": (0.22, 0.17, 0.15), "Traveller": (0.22, 0.17, 0.15), "AirWoman": (0.20, 0.14, 0.12)}
for n, col in HAIRT.items():
    r = RIGS[n][0]
    for c in r.children:
        if c.type == 'MESH' and any(k in c.name.lower() for k in ("short", "pony", "bob", "braid", "afro", "eyebrow")):
            for m in c.data.materials: tint(m, col)
    for c in r.children:
        if c.type == 'MESH' and "teeth" in c.name:
            for m in c.data.materials: tint(m, (1.5, 1.45, 1.4))
# EnhancedEye cornea fix on every eye group (LESSONS 3)
for g in [g for g in bpy.data.node_groups if g.name.startswith("EnhancedEye")]:
    P = next((n_ for n_ in g.nodes if n_.type == "BSDF_PRINCIPLED"), None); OUTN = next((n_ for n_ in g.nodes if n_.type == "GROUP_OUTPUT"), None)
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
C_PEOPLE = coll("People")
for n, (r, b) in RIGS.items(): to_coll(tree(r), C_PEOPLE)

# ================================================================== CABIN (root SET_Cabin at the world origin)
C_CAB = coll("Cabin")
def root(name, c):
    e = bpy.data.objects.new(name, None); c.objects.link(e); e.empty_display_size = 0.3; return e
CAB = root("SET_Cabin", C_CAB)
def own(o, parent, c):
    o.parent = parent; to_coll([o], c); return o
Y0, Y1 = -6.0, 6.2
m_carpet = mat("M_Carpet", (0.16, 0.05, 0.42), rough=0.9)
nt = m_carpet.node_tree; p_ = nt.nodes["Principled BSDF"]
tc = nt.nodes.new("ShaderNodeTexCoord"); vo = nt.nodes.new("ShaderNodeTexVoronoi"); vo.inputs["Scale"].default_value = 22
cr = nt.nodes.new("ShaderNodeValToRGB"); cr.color_ramp.elements[0].color = (0.10, 0.03, 0.30, 1); cr.color_ramp.elements[1].color = (0.30, 0.10, 0.62, 1)
nt.links.new(tc.outputs["Object"], vo.inputs["Vector"]); nt.links.new(vo.outputs["Distance"], cr.inputs["Fac"]); nt.links.new(cr.outputs["Color"], p_.inputs["Base Color"])
floor = own(box("Cab_Floor", (3.9, Y1 - Y0, 0.04), (0, (Y0 + Y1) / 2, -0.02), m_carpet, bevel=0), CAB, C_CAB)

# shell: profile (half width, z) swept along Y, windows cut by boolean
m_wall = mat("M_CabWall", (0.80, 0.86, 0.90), rough=0.45, coat=0.2)
m_wall.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.62, 0.86, 0.92, 1)
prof = [(1.86, -0.02), (1.90, 0.45), (1.96, 0.95), (1.93, 1.45), (1.80, 1.80), (1.30, 2.18), (0.70, 2.34), (0.0, 2.38)]
bm = bmesh.new(); ny = 64
rows = []
for j in range(ny + 1):
    y = Y0 + (Y1 - Y0) * j / ny; row = []
    for (hx, z) in prof[::-1] + [(-p[0], p[1]) for p in prof[1:]]:
        pass
    pts = [(-p[0], p[1]) for p in prof] + [(p[0], p[1]) for p in prof[::-1][1:]]
    row = [bm.verts.new((x, y, z)) for (x, z) in pts]; rows.append(row)
for j in range(ny):
    for i in range(len(rows[0]) - 1):
        bm.faces.new((rows[j][i], rows[j][i + 1], rows[j + 1][i + 1], rows[j + 1][i]))
me = bpy.data.meshes.new("Cab_Shell"); bm.to_mesh(me); bm.free()
shell = bpy.data.objects.new("Cab_Shell", me); C_CAB.objects.link(shell); shell.parent = CAB
me.materials.append(m_wall)
for p in me.polygons: p.use_smooth = True
so = shell.modifiers.new("solid", 'SOLIDIFY'); so.thickness = 0.06; so.offset = 1.0
# window cutters (rounded) every 0.85 m both sides
cutters = []
WIN_Y = [y for y in [Y0 + 0.5 + 0.85 * k for k in range(14)] if y < Y1 - 0.4]
for sx in (1, -1):
    for y in WIN_Y:
        if 0.55 < y < 1.5: continue      # exit door instead
        bpy.ops.mesh.primitive_cylinder_add(radius=0.15, depth=0.6, location=(sx * 1.95, y, 1.05), rotation=(0, math.radians(90), 0), vertices=24)
        c = bpy.context.active_object; c.scale = (1.0, 0.75, 1.0); c.name = "cut"; cutters.append(c)
bpy.ops.object.select_all(action='DESELECT')
for c in cutters: c.select_set(True)
bpy.context.view_layer.objects.active = cutters[0]; bpy.ops.object.join(); cut = bpy.context.active_object
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
bo = shell.modifiers.new("win", 'BOOLEAN'); bo.object = cut; bo.operation = 'DIFFERENCE'; bo.solver = 'EXACT'
bpy.context.view_layer.objects.active = shell
for mname in ("solid", "win"): bpy.ops.object.modifier_apply(modifier=mname)
bpy.data.objects.remove(cut, do_unlink=True)
# window panes: bright sky glass seen through the holes (emission gradient, outside the shell)
m_sky_win = bpy.data.materials.new("M_WinSky"); m_sky_win.use_nodes = True
nt = m_sky_win.node_tree; nt.nodes.clear()
o_ = nt.nodes.new("ShaderNodeOutputMaterial"); em = nt.nodes.new("ShaderNodeEmission"); tc = nt.nodes.new("ShaderNodeTexCoord")
se = nt.nodes.new("ShaderNodeSeparateXYZ"); cr = nt.nodes.new("ShaderNodeValToRGB")
cr.color_ramp.elements[0].color = (0.75, 0.92, 1.0, 1); cr.color_ramp.elements[1].color = (0.05, 0.45, 0.95, 1)
nt.links.new(tc.outputs["Object"], se.inputs[0]); mr = nt.nodes.new("ShaderNodeMapRange"); mr.inputs["From Min"].default_value = 0.6; mr.inputs["From Max"].default_value = 1.5
nt.links.new(se.outputs["Z"], mr.inputs["Value"]); nt.links.new(mr.outputs["Result"], cr.inputs["Fac"])
nt.links.new(cr.outputs["Color"], em.inputs["Color"]); em.inputs["Strength"].default_value = 2.2; nt.links.new(em.outputs[0], o_.inputs["Surface"])
for sx in (1, -1):
    pl = own(box("Cab_WinSky_%d" % sx, (0.02, Y1 - Y0, 1.4), (sx * 2.12, (Y0 + Y1) / 2, 1.05), m_sky_win, bevel=0), CAB, C_CAB)
# window bezels (cream rings) and shades
m_bezel = mat("M_Bezel", (0.95, 0.93, 0.86), rough=0.4, coat=0.3)
for sx in (1, -1):
    for y in WIN_Y:
        if 0.55 < y < 1.5: continue
        bpy.ops.mesh.primitive_torus_add(major_radius=0.165, minor_radius=0.022, location=(sx * 1.90, y, 1.05), rotation=(0, math.radians(90), 0))
        t = bpy.context.active_object; t.scale = (1, 0.75, 1); t.name = "Cab_Bezel"; t.data.materials.append(m_bezel); bpy.ops.object.shade_smooth()
        own(t, CAB, C_CAB)
# exit doors at y ~1.05 (outline + handle), both sides
m_door = mat("M_ExitDoor", (0.80, 0.90, 0.95), rough=0.4, coat=0.3); m_red = mat("M_ExitRed", (0.85, 0.03, 0.03), rough=0.35, coat=0.4)
for sx in (1, -1):
    own(box("Cab_ExitDoor_%d" % sx, (0.05, 0.80, 1.35), (sx * 1.90, 1.05, 0.95), m_door, bevel=0.03), CAB, C_CAB)
    own(box("Cab_ExitHandle_%d" % sx, (0.06, 0.30, 0.05), (sx * 1.86, 1.05, 1.15), m_red, bevel=0.015), CAB, C_CAB)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.13, depth=0.03, location=(sx * 1.86, 1.05, 1.45), rotation=(0, math.radians(90), 0)); w_ = bpy.context.active_object
    w_.name = "Cab_ExitWin_%d" % sx; w_.data.materials.append(m_sky_win); own(w_, CAB, C_CAB)
# overhead bins (saturated teal doors with a seam) + ceiling light strips
m_bin = mat("M_Bin", (0.02, 0.42, 0.50), rough=0.55, coat=0.0)
m_light = mat("M_CeilLight", (1, 1, 1), emit=((1.0, 0.94, 0.85), 6.0))
for sx in (1, -1):
    for k in range(int((Y1 - Y0) / 1.25)):
        y = Y0 + 0.65 + k * 1.25
        b_ = own(box("Cab_Bin", (0.80, 1.20, 0.40), (sx * 1.38, y, 2.02), m_bin, bevel=0.05), CAB, C_CAB)
        b_.rotation_euler.y = math.radians(-14 * sx)
    own(box("Cab_LightStrip_%d" % sx, (0.06, Y1 - Y0 - 0.4, 0.02), (sx * 0.92, (Y0 + Y1) / 2, 2.24), m_light, bevel=0), CAB, C_CAB)
own(box("Cab_LightMid", (0.30, Y1 - Y0 - 0.4, 0.02), (0, (Y0 + Y1) / 2, 2.35), mat("M_CeilPanel", (0.85, 0.95, 1.0), emit=((0.85, 0.95, 1.0), 1.2)), bevel=0), CAB, C_CAB)
# front bulkhead with the airline's name (DA KRAS FILMS logo) and a curtain gap to the galley
m_bulk = mat("M_Bulkhead", (0.05, 0.20, 0.55), rough=0.35, coat=0.3)
for sx in (1, -1):
    own(box("Cab_Bulkhead_%d" % sx, (1.35, 0.06, 2.3), (sx * 1.20, Y1 - 0.2, 1.15), m_bulk, bevel=0.02), CAB, C_CAB)
own(box("Cab_BulkTop", (1.1, 0.06, 0.35), (0, Y1 - 0.2, 2.15), m_bulk, bevel=0.02), CAB, C_CAB)
m_curt = fabric("M_Curtain", (0.62, 0.02, 0.06), scale=200, bump=0.4)
cu = own(box("Cab_Curtain", (1.05, 0.03, 1.95), (0, Y1 - 0.12, 0.98), m_curt, bevel=0.01), CAB, C_CAB)
tx = bpy.data.textures.new("curt", 'WOOD'); tx.wood_type = 'BANDNOISE'; tx.noise_scale = 0.1
sd = cu.modifiers.new("sd", 'SUBSURF'); sd.levels = 3; sd.subdivision_type = 'SIMPLE'
dp = cu.modifiers.new("folds", 'DISPLACE'); dp.texture = tx; dp.strength = 0.05; dp.texture_coords = 'LOCAL'
def logo_plane(name, path, w, loc, rot, parent, c, emit=0.0):
    img = bpy.data.images.load(path); asp = img.size[1] / img.size[0]
    bpy.ops.mesh.primitive_plane_add(size=1, location=loc, rotation=rot)
    o = bpy.context.active_object; o.name = name; o.scale = (w, w * asp, 1); bpy.ops.object.transform_apply(scale=True)
    m = bpy.data.materials.new("M_" + name); m.use_nodes = True; nt_ = m.node_tree; p = nt_.nodes["Principled BSDF"]
    ti = nt_.nodes.new("ShaderNodeTexImage"); ti.image = img
    nt_.links.new(ti.outputs["Color"], p.inputs["Base Color"]); nt_.links.new(ti.outputs["Alpha"], p.inputs["Alpha"])
    p.inputs["Roughness"].default_value = 0.45
    if emit:
        nt_.links.new(ti.outputs["Color"], p.inputs["Emission Color"]); p.inputs["Emission Strength"].default_value = emit
    m.blend_method = 'HASHED' if hasattr(m, "blend_method") else None
    o.data.materials.append(m); own(o, parent, c); return o
LOGO_CAB = logo_plane("Logo_Bulkhead", LOGO_WHITE, 1.0, (-1.20, Y1 - 0.24, 1.70), (math.radians(90), 0, 0), CAB, C_CAB, emit=0.6)

# seats: real airline seat (CC-BY), recoloured royal blue with magenta headrest covers
SEAT = imp(A + "glb2/aseat.glb", "SeatSrc", target_dim=1.12, axis=2)
for m in SEAT.data.materials: colorize(SEAT, (0.04, 0.16, 0.75), gain=1.8)
SEAT.data.transform(Matrix.Scale(0.50 / max(0.01, (max(v.co.x for v in SEAT.data.vertices) - min(v.co.x for v in SEAT.data.vertices))), 4, Vector((1, 0, 0))))
SY = [v.co.y for v in SEAT.data.vertices]
print("SEAT dims", round(max(v.co.x for v in SEAT.data.vertices) - min(v.co.x for v in SEAT.data.vertices), 3), round(max(SY) - min(SY), 3))
to_coll([SEAT], C_CAB); SEAT.hide_render = True; SEAT.hide_viewport = True
m_head = fabric("M_Headrest", (0.85, 0.05, 0.45), scale=300, bump=0.2)
SEAT_FACE = -1     # set by 02 after a check: model front along -Y -> rows face +Y via rotation 180
ROW_Y = [-3.4, -2.55, -1.70, -0.85, 0.0, 2.10, 2.95, 3.80, 4.65]
SEAT_X = {"L": [-0.63, -1.13, -1.63], "R": [0.63, 1.13, 1.63]}
SEATS = {}
for ry in ROW_Y:
    for side, xs in SEAT_X.items():
        for k, x in enumerate(xs):
            s = bpy.data.objects.new("Seat_%s%d_%.2f" % (side, k, ry), SEAT.data); C_CAB.objects.link(s); s.parent = CAB
            s.location = (x, ry, 0.0); s.rotation_euler.z = math.radians(180)
            SEATS[(side, k, ry)] = s
            hr = own(box("Headrest_%s%d_%.2f" % (side, k, ry), (0.40, 0.03, 0.20), (x, ry + 0.0, 1.0), m_head, bevel=0.012), CAB, C_CAB)
            hr["headrest"] = 1
sc["SEAT_ROWS"] = ROW_Y

# ================================================================== PROPS (cabin)
C_PROP = coll("Props")
# sneakers: the real high-top pair (CC-BY), split into left/right, recoloured true red with white soles
pair = imp(A + "glb2/redsneaker.glb", "SneakerPair", target_dim=0.37, axis=None)
bpy.context.view_layer.objects.active = pair; bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.separate(type='LOOSE'); bpy.ops.object.mode_set(mode='OBJECT')
parts = [o for o in bpy.data.objects if o.name.startswith("SneakerPair")]
xs = sorted(parts, key=lambda o: sum((o.matrix_world @ v.co).x for v in o.data.vertices) / len(o.data.vertices))
half = len(xs) // 2
def join(objs, name):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs: o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    if len(objs) > 1: bpy.ops.object.join()
    o = bpy.context.active_object; o.name = name; return o
# separate by loose parts may give many pieces: group by centroid x sign
cx = lambda o: sum((o.matrix_world @ v.co).x for v in o.data.vertices) / max(1, len(o.data.vertices))
CX = {o.name: cx(o) for o in parts}
mid = (min(CX.values()) + max(CX.values())) / 2
LEFTS = [o for o in parts if CX[o.name] < mid]; RIGHTS = [o for o in parts if CX[o.name] >= mid]
SHOE_L = join(LEFTS, "ShoeL"); SHOE_R = join(RIGHTS, "ShoeR")
for o in (SHOE_L, SHOE_R):
    bpy.context.view_layer.objects.active = o; bpy.ops.object.select_all(action='DESELECT'); o.select_set(True)
    bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
    mn = min(v.co.z for v in o.data.vertices); o.data.transform(Matrix.Translation((0, 0, -mn))); o.location.z += mn
    for m in o.data.materials:
        nt_ = m.node_tree
        for p in [n_ for n_ in nt_.nodes if n_.type == 'BSDF_PRINCIPLED']:
            p.inputs["Roughness"].default_value = 0.45
            p.inputs["Coat Weight"].default_value = 0.25
        for n_ in nt_.nodes:
            if n_.type == 'NORMAL_MAP': n_.inputs["Strength"].default_value = 0.4
    to_coll([o], C_PROP)
for o in (SHOE_L, SHOE_R):
    d = [o.matrix_world @ v.co for v in o.data.vertices]
    print("SHOE", o.name, [round(max(q[i] for q in d) - min(q[i] for q in d), 3) for i in range(3)])
# fuse cords: a short braided cord out of each shoe's tongue (positions set in 02 on the shoe's own axes)
m_fuse = mat("M_Fuse", (0.95, 0.62, 0.05), rough=0.6, sheen=0.3)
m_fuse_tip = mat("M_FuseTip", (0.05, 0.04, 0.03), rough=0.8)
def fuse(name):
    pts = [(0, 0, 0), (0.002, -0.006, 0.018), (0.007, -0.013, 0.036), (0.015, -0.018, 0.052), (0.026, -0.020, 0.066)]
    cu_ = bpy.data.curves.new(name, 'CURVE'); cu_.dimensions = '3D'; cu_.bevel_depth = 0.0026; cu_.bevel_resolution = 3; cu_.use_fill_caps = True
    sp = cu_.splines.new('POLY'); sp.points.add(len(pts) - 1)
    for pt_, p in zip(sp.points, pts): pt_.co = (*p, 1)
    o = bpy.data.objects.new(name, cu_); sc.collection.objects.link(o); cu_.materials.append(m_fuse); to_coll([o], C_PROP); return o
FUSE_L = fuse("FuseL"); FUSE_R = fuse("FuseR")
# match: wooden stick + red head, flame = emission teardrop + small point light
m_wood = mat("M_MatchWood", (0.85, 0.62, 0.32), rough=0.6); m_mhead = mat("M_MatchHead", (0.75, 0.04, 0.03), rough=0.5)
MATCH = cyl("Match", 0.0019, 0.058, (0, 0, 0.029), m_wood, verts=10); to_coll([MATCH], C_PROP)
mh = sphere("MatchHead", 0.0034, (0, 0, 0.059), m_mhead, segs=12); mh.scale = (1, 1, 1.4); mh.parent = MATCH; to_coll([mh], C_PROP)
m_flame = bpy.data.materials.new("M_Flame"); m_flame.use_nodes = True
nt = m_flame.node_tree; nt.nodes.clear(); o_ = nt.nodes.new("ShaderNodeOutputMaterial"); em = nt.nodes.new("ShaderNodeEmission")
lw = nt.nodes.new("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.35
cr = nt.nodes.new("ShaderNodeValToRGB"); cr.color_ramp.elements[0].color = (1.0, 0.55, 0.08, 1); cr.color_ramp.elements[1].color = (1.0, 0.18, 0.0, 1)
nt.links.new(lw.outputs["Facing"], cr.inputs["Fac"]); nt.links.new(cr.outputs["Color"], em.inputs["Color"]); em.inputs["Strength"].default_value = 5
nt.links.new(em.outputs[0], o_.inputs["Surface"])
FLAME = sphere("Flame", 0.0100, (0, 0, 0.074), m_flame, segs=16); FLAME.scale = (1, 1, 2.2); FLAME.parent = MATCH; to_coll([FLAME], C_PROP)
fl = bpy.data.objects.new("FlameLight", bpy.data.lights.new("FlameLight", 'POINT')); fl.data.energy = 3.0; fl.data.color = (1.0, 0.6, 0.2)
fl.data.shadow_soft_size = 0.01; fl.parent = MATCH; fl.location = (0, 0, 0.075); C_PROP.objects.link(fl)
# spent matches + matchbox on the armrest tray area (set in 02)
MBOX = box("Matchbox", (0.052, 0.036, 0.014), (0, 0, 0.007), mat("M_Matchbox", (0.95, 0.80, 0.05), rough=0.5), bevel=0.002); to_coll([MBOX], C_PROP)
# syringe (CC-BY), scaled to 14 cm
SYR = imp(A + "glb/syringe.glb", "Syringe", target_dim=0.14, axis=None); to_coll([SYR], C_PROP)
# flex-cuff restraint: one black strap loop per wrist joined by a bridge (bound to the wrists in 02)
m_cuff = mat("M_Cuff", (0.02, 0.02, 0.025), rough=0.45, coat=0.2)
# smoke wisp
m_smoke = mat("M_Smoke", (0.85, 0.85, 0.88), rough=1.0, alpha=0.35)

# ================================================================== VOID (cutaway studio, beat 7)
C_VOID = coll("Void")
VOID = root("SET_Void", C_VOID)
m_void = bpy.data.materials.new("M_Void"); m_void.use_nodes = True
nt = m_void.node_tree; nt.nodes.clear(); o_ = nt.nodes.new("ShaderNodeOutputMaterial"); em = nt.nodes.new("ShaderNodeEmission")
tc = nt.nodes.new("ShaderNodeTexCoord"); se = nt.nodes.new("ShaderNodeSeparateXYZ"); cr = nt.nodes.new("ShaderNodeValToRGB")
mr = nt.nodes.new("ShaderNodeMapRange"); mr.inputs["From Min"].default_value = -6; mr.inputs["From Max"].default_value = 6
cr.color_ramp.elements[0].color = (0.00, 0.10, 0.22, 1); cr.color_ramp.elements[1].color = (0.00, 0.55, 0.65, 1)
nt.links.new(tc.outputs["Object"], se.inputs[0]); nt.links.new(se.outputs["Z"], mr.inputs["Value"]); nt.links.new(mr.outputs["Result"], cr.inputs["Fac"])
nt.links.new(cr.outputs["Color"], em.inputs["Color"]); em.inputs["Strength"].default_value = 1.0; nt.links.new(em.outputs[0], o_.inputs["Surface"])
bpy.ops.mesh.primitive_uv_sphere_add(radius=6.0, segments=48, ring_count=24); vs = bpy.context.active_object; vs.name = "Void_Sphere"
vs.data.materials.append(m_void); bpy.ops.object.shade_smooth(); own(vs, VOID, C_VOID)
for k, (loc, en) in enumerate((((2.0, -2.0, 2.5), 300), ((-2.5, -1.0, 1.0), 150), ((0.5, 2.5, 3.0), 200))):
    L = bpy.data.objects.new("Void_Light%d" % k, bpy.data.lights.new("Void_Light%d" % k, 'AREA')); L.data.energy = en; L.data.size = 1.5
    L.location = loc; L.rotation_euler = (Vector((0, 0, 0)) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler(); C_VOID.objects.link(L); L.parent = VOID
# cutaway shoe: a copy of the right shoe cut lengthwise; the cavity in the sole holds the charge (putty slab), fuse into it.
CUT = SHOE_R.copy(); CUT.data = SHOE_R.data.copy(); CUT.name = "CutShoe"; C_VOID.objects.link(CUT)
for c_ in list(CUT.users_collection):
    if c_ != C_VOID: c_.objects.unlink(CUT)
CUT.parent = None; CUT.location = (0, 0, 0)
bpy.context.view_layer.objects.active = CUT; bpy.ops.object.select_all(action='DESELECT'); CUT.select_set(True)
dims = [max(v.co[i] for v in CUT.data.vertices) - min(v.co[i] for v in CUT.data.vertices) for i in range(3)]
LONG = 0 if dims[0] > dims[1] else 1
sc["SHOE_LONG_AXIS"] = LONG
# split into upper half (lifts away) and sole half by a horizontal cut through the midsole
zc = 0.028
bm = bmesh.new(); bm.from_mesh(CUT.data)
res = bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=(0, 0, zc), plane_no=(0, 0, 1), clear_inner=False, clear_outer=False)
bm.to_mesh(CUT.data); bm.free()
CUT_UP = CUT.copy(); CUT_UP.data = CUT.data.copy(); CUT_UP.name = "CutShoe_Upper"; C_VOID.objects.link(CUT_UP)
def keep(o, above):
    bm = bmesh.new(); bm.from_mesh(o.data)
    kill = [v for v in bm.verts if (v.co.z < zc - 1e-5) == above]
    bmesh.ops.delete(bm, geom=kill, context='VERTS'); bm.to_mesh(o.data); bm.free()
keep(CUT_UP, True); keep(CUT, False); CUT.name = "CutShoe_Sole"
for o in (CUT, CUT_UP):
    sol = o.modifiers.new("cap", 'SOLIDIFY'); sol.thickness = 0.003
# charge: a soft putty slab sunk into the sole (rounded, displaced, ochre), and the fuse running into it
m_putty = mat("M_Putty", (0.36, 0.38, 0.30), rough=0.6, coat=0.05)
L_ = dims[LONG]; W_ = dims[1 - LONG]
sz = (L_ * 0.62, W_ * 0.48, 0.016) if LONG == 0 else (W_ * 0.48, L_ * 0.62, 0.016)
PUTTY = box("CutShoe_Charge", sz, (0, 0, zc - 0.006), m_putty, bevel=0.006, segs=4); to_coll([PUTTY], C_VOID)
tx = bpy.data.textures.new("putty", 'CLOUDS'); tx.noise_scale = 0.01
sdv = PUTTY.modifiers.new("sd", 'SUBSURF'); sdv.levels = 3; sdv.render_levels = 3
dpv = PUTTY.modifiers.new("lumps", 'DISPLACE'); dpv.texture = tx; dpv.strength = 0.002
m_cav = mat("M_Cavity", (0.95, 0.95, 0.92), rough=0.7)
cav = box("CutShoe_Cavity", (sz[0] + 0.01, sz[1] + 0.01, 0.004), (0, 0, zc - 0.0145), m_cav, bevel=0.002); to_coll([cav], C_VOID)
for o in (CUT, CUT_UP, PUTTY, cav):
    o.parent = VOID

# ================================================================== SKY (beat 8)
C_SKY = coll("Sky")
SKY = root("SET_Sky", C_SKY)
PLANE = imp(A + "glb/plane.glb", "Airliner", target_dim=38.0, axis=None)
pd = [max(v.co[i] for v in PLANE.data.vertices) - min(v.co[i] for v in PLANE.data.vertices) for i in range(3)]
print("PLANE dims", [round(x, 2) for x in pd])
to_coll([PLANE], C_SKY); PLANE.parent = SKY
# livery: plain white body (no airline marks) with a deep red cheatline; logo decal placed in 02 once the fuselage axis is known
for m in PLANE.data.materials:
    if not m or not m.use_nodes: continue
    for p in [n_ for n_ in m.node_tree.nodes if n_.type == 'BSDF_PRINCIPLED']:
        if not p.inputs["Base Color"].is_linked:
            c = p.inputs["Base Color"].default_value
        p.inputs["Roughness"].default_value = max(0.3, p.inputs["Roughness"].default_value)
LOGO_PLANE_IMG = LOGO_DARK
# cloud deck: displaced, bright white with blue shadows, far below
bpy.ops.mesh.primitive_plane_add(size=600, location=(0, 0, -60)); cd_ = bpy.context.active_object; cd_.name = "Sky_Clouds"
sdc = cd_.modifiers.new("sd", 'SUBSURF'); sdc.levels = 8; sdc.render_levels = 8; sdc.subdivision_type = 'SIMPLE'
txc = bpy.data.textures.new("clouds", 'CLOUDS'); txc.noise_scale = 14; txc.noise_depth = 4
dpc = cd_.modifiers.new("puff", 'DISPLACE'); dpc.texture = txc; dpc.strength = 26; dpc.texture_coords = 'GLOBAL'
cd_.data.materials.append(mat("M_Cloud", (0.92, 0.95, 1.0), rough=1.0, sss=0.0, emit=((0.55, 0.70, 0.95), 0.10)))
own(cd_, SKY, C_SKY)
sun = bpy.data.objects.new("Sky_Sun", bpy.data.lights.new("Sky_Sun", 'SUN')); sun.data.energy = 2.6; sun.rotation_euler = (math.radians(40), math.radians(10), math.radians(30))
C_SKY.objects.link(sun); sun.parent = SKY
# sky dome (camera sees it only while the sky set is visible)
m_dome = bpy.data.materials.new("M_SkyDome"); m_dome.use_nodes = True
nt = m_dome.node_tree; nt.nodes.clear(); o_ = nt.nodes.new("ShaderNodeOutputMaterial"); em = nt.nodes.new("ShaderNodeEmission")
tc = nt.nodes.new("ShaderNodeTexCoord"); se = nt.nodes.new("ShaderNodeSeparateXYZ"); cr = nt.nodes.new("ShaderNodeValToRGB")
mr = nt.nodes.new("ShaderNodeMapRange"); mr.inputs["From Min"].default_value = -0.1; mr.inputs["From Max"].default_value = 0.8
cr.color_ramp.elements[0].color = (0.25, 0.62, 0.95, 1); cr.color_ramp.elements[1].color = (0.0, 0.10, 0.55, 1)
nrm = nt.nodes.new("ShaderNodeVectorMath"); nrm.operation = 'NORMALIZE'
nt.links.new(tc.outputs["Object"], nrm.inputs[0]); nt.links.new(nrm.outputs[0], se.inputs[0]); nt.links.new(se.outputs["Z"], mr.inputs["Value"])
nt.links.new(mr.outputs["Result"], cr.inputs["Fac"]); nt.links.new(cr.outputs["Color"], em.inputs["Color"]); em.inputs["Strength"].default_value = 1.0
nt.links.new(em.outputs[0], o_.inputs["Surface"])
bpy.ops.mesh.primitive_uv_sphere_add(radius=400, segments=48, ring_count=24); dome = bpy.context.active_object; dome.name = "Sky_Dome"
dome.data.materials.append(m_dome); bpy.ops.object.shade_smooth(); own(dome, SKY, C_SKY)
dome.visible_shadow = False; dome.visible_diffuse = False; dome.visible_glossy = True

# ================================================================== AIRPORT (beat 9)
C_AIR = coll("Airport")
AIR = root("SET_Airport", C_AIR)
m_afloor = tiles("M_AirFloor", (0.02, 0.38, 0.42), (0.03, 0.45, 0.50), (0.01, 0.25, 0.28), scale=1.0, w=0.6, h=0.6, rough=0.3, coat=0.3)
own(box("Air_Floor", (14, 14, 0.04), (0, 0, -0.02), m_afloor, bevel=0), AIR, C_AIR)
m_awall = mat("M_AirWall", (0.38, 0.10, 0.62), rough=0.5)
own(box("Air_WallBack", (14, 0.1, 4.0), (0, 4.0, 2.0), m_awall, bevel=0), AIR, C_AIR)
own(box("Air_WallLeft", (0.1, 14, 4.0), (-5.0, 0, 2.0), m_awall, bevel=0), AIR, C_AIR)
own(box("Air_Ceiling", (14, 14, 0.1), (0, 0, 3.6), mat("M_AirCeil", (0.9, 0.95, 1.0), emit=((0.9, 0.95, 1.0), 0.8)), bevel=0), AIR, C_AIR)
for k in range(5):
    own(box("Air_Light%d" % k, (2.4, 0.25, 0.03), (-2 + k * 1.2 - 1, 0.5 + (k % 2) * 1.5, 3.54), m_light, bevel=0), AIR, C_AIR)
# window band on the back wall: runway daylight
own(box("Air_Windows", (9, 0.05, 1.6), (0, 3.93, 2.1), m_sky_win, bevel=0), AIR, C_AIR)
for k in range(10):
    own(box("Air_Mullion%d" % k, (0.08, 0.10, 1.7), (-4.5 + k, 3.90, 2.1), mat("M_Mullion", (0.9, 0.9, 0.92), rough=0.3, metal=0.6), bevel=0.005), AIR, C_AIR)
# roller bed (real conveyor, CC-BY) along +X, X-ray tunnel over its far end
CONV = imp(A + "glb/conveyor.glb", "Air_Conveyor", target_dim=0.78, axis=2)
cdim = [max(v.co[i] for v in CONV.data.vertices) - min(v.co[i] for v in CONV.data.vertices) for i in range(3)]
CONV.rotation_euler.z = math.radians(90) if cdim[1] > cdim[0] else 0.0
CONV.scale = (1.4, 1.0, 1.0) if cdim[1] > cdim[0] else (1.0, 1.4, 1.0)
colorize(CONV, (0.10, 0.10, 0.12), gain=1.2)
own(CONV, AIR, C_AIR); CONV.location = (0, 0, 0)
sc["CONV_DIM"] = [round(x, 3) for x in cdim]
m_scan = mat("M_Scanner", (0.92, 0.92, 0.95), rough=0.35, coat=0.4); m_curtain = mat("M_LeadCurtain", (0.05, 0.05, 0.06), rough=0.6)
own(box("Air_XrayBody", (1.3, 1.05, 1.0), (1.7, 0, 1.15), m_scan, bevel=0.06), AIR, C_AIR)
own(box("Air_XrayHole", (1.32, 0.72, 0.42), (1.7, 0, 0.98), m_curtain, bevel=0.01), AIR, C_AIR)
for k in range(8):
    own(box("Air_Flap%d" % k, (0.02, 0.085, 0.40), (1.04, -0.31 + k * 0.088, 0.98), m_curtain, bevel=0.004), AIR, C_AIR)
own(box("Air_XrayStripe", (1.32, 1.06, 0.08), (1.7, 0, 1.55), mat("M_ScanStripe", (0.0, 0.45, 0.85), rough=0.3, coat=0.4), bevel=0.01), AIR, C_AIR)
# trays: soft grey plastic tub with the DA KRAS FILMS logo printed in the bottom (as real airport trays carry ads)
m_tray = mat("M_Tray", (0.30, 0.34, 0.40), rough=0.45, coat=0.1)
def tray(name):
    bm = bmesh.new(); w, l, h, t = 0.42, 0.56, 0.10, 0.008
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts: v.co = Vector((v.co.x * w, v.co.y * l, (v.co.z + 0.5) * h))
    top = [f for f in bm.faces if f.normal.z > 0.9]
    bmesh.ops.delete(bm, geom=top, context='FACES_ONLY')
    me_ = bpy.data.meshes.new(name); bm.to_mesh(me_); bm.free()
    o = bpy.data.objects.new(name, me_); C_AIR.objects.link(o)
    s_ = o.modifiers.new("t", 'SOLIDIFY'); s_.thickness = t; s_.offset = -1
    b_ = o.modifiers.new("b", 'BEVEL'); b_.width = 0.012; b_.segments = 3
    me_.materials.append(m_tray)
    for p in me_.polygons: p.use_smooth = True
    lg = logo_plane(name + "_Logo", LOGO_DARK, 0.34, (0, 0, 0.0105), (0, 0, math.radians(-90)), o, C_AIR)
    return o
TRAYS = [tray("Tray%d" % k) for k in range(4)]
for t in TRAYS: t.parent = AIR
# the traveller's own sneakers (white/blue, a recoloured copy of the hero pair so it reads as a different pair)
TSH_L = SHOE_L.copy(); TSH_L.data = SHOE_L.data.copy(); TSH_L.name = "TravShoeL"; C_AIR.objects.link(TSH_L)
TSH_R = SHOE_R.copy(); TSH_R.data = SHOE_R.data.copy(); TSH_R.name = "TravShoeR"; C_AIR.objects.link(TSH_R)
for o in (TSH_L, TSH_R):
    for c_ in list(o.users_collection):
        if c_ != C_AIR: c_.objects.unlink(o)
    mm = o.data.materials[0].copy(); o.data.materials[0] = mm; o.data.materials[0].name = "M_TravShoe"
for o in (TSH_L, TSH_R): colorize(o, (0.05, 0.30, 0.95), gain=1.6)
OSH = [SHOE_L.copy() for _ in range(2)]
for k, o in enumerate(OSH):
    o.data = SHOE_L.data.copy(); o.name = "WomanShoe%d" % k; C_AIR.objects.link(o)
    for c_ in list(o.users_collection):
        if c_ != C_AIR: c_.objects.unlink(o)
    mm = o.data.materials[0].copy(); o.data.materials[0] = mm; colorize(o, (0.95, 0.85, 0.05), gain=1.6)
# walk-through metal detector arch (CC-BY)
DET = imp(A + "glb/detector.glb", "Air_Detector", target_dim=2.15, axis=2); own(DET, AIR, C_AIR); DET.location = (0.2, 1.6, 0)
colorize(DET, (0.85, 0.85, 0.9), gain=1.2)
# stanchions (posts with a teal belt)
m_post = mat("M_Post", (0.8, 0.8, 0.85), rough=0.25, metal=0.9); m_belt = mat("M_Belt", (0.0, 0.55, 0.60), rough=0.5)
for k in range(4):
    x = -3.2 + k * 0.9
    own(cyl("Air_Post%d" % k, 0.03, 0.95, (x, -1.3, 0.475), m_post), AIR, C_AIR)
    own(cyl("Air_PostBase%d" % k, 0.16, 0.03, (x, -1.3, 0.015), m_post), AIR, C_AIR)
    if k < 3: own(box("Air_Belt%d" % k, (0.88, 0.008, 0.05), (x + 0.45, -1.3, 0.88), m_belt, bevel=0), AIR, C_AIR)
# fill lights
for k, (loc, en) in enumerate((((-1.5, -3.0, 2.8), 500), ((2.5, -2.5, 2.5), 300), ((-1.0, 2.0, 3.0), 200))):
    L = bpy.data.objects.new("Air_Fill%d" % k, bpy.data.lights.new("Air_Fill%d" % k, 'AREA')); L.data.energy = en; L.data.size = 2.0
    L.location = loc; L.rotation_euler = (Vector((0, 0, 1.0)) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler(); C_AIR.objects.link(L); L.parent = AIR
# cabin fill lights
for k, (loc, en) in enumerate((((0.0, -1.5, 2.1), 160), ((0.0, 2.5, 2.1), 160), ((-1.0, 0.8, 1.9), 90), ((0.0, 4.8, 2.0), 120))):
    L = bpy.data.objects.new("Cab_Fill%d" % k, bpy.data.lights.new("Cab_Fill%d" % k, 'AREA')); L.data.energy = en; L.data.size = 1.2
    L.location = loc; L.rotation_euler = (0, 0, 0); C_CAB.objects.link(L); L.parent = CAB

# ================================================================== world + look (deep, rich: Filmic High Contrast, as LegoInNose v013)
w = bpy.data.worlds.new("World"); sc.world = w; w.use_nodes = True
bg = w.node_tree.nodes["Background"]; bg.inputs[0].default_value = (0.35, 0.55, 0.75, 1); bg.inputs[1].default_value = 0.35
sc.render.engine = 'CYCLES'; sc.cycles.samples = 64; sc.cycles.use_adaptive_sampling = True; sc.cycles.adaptive_threshold = 0.04
sc.cycles.use_denoising = True; sc.cycles.denoiser = 'OPENIMAGEDENOISE'
sc.cycles.max_bounces = 6; sc.cycles.diffuse_bounces = 3; sc.cycles.glossy_bounces = 3; sc.cycles.transmission_bounces = 6
sc.cycles.transparent_max_bounces = 16; sc.cycles.caustics_reflective = False; sc.cycles.caustics_refractive = False
sc.render.use_persistent_data = True; sc.render.use_simplify = True; sc.render.simplify_subdivision_render = 2
sc.cycles.texture_limit_render = '2048'
sc.view_settings.view_transform = 'Filmic'; sc.view_settings.look = 'High Contrast'
sc.render.use_motion_blur = False
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print("BUILD_OK", OUT)
