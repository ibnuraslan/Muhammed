"""Static set: house exterior + layered shot wall + living room + props + tumbler + bullet + the couple (appended).
blender -b --python 02_build_scene.py -- <assets_dir> <humans.blend> <out.blend>"""
import sys, os, math, random
import bpy, bmesh
from mathutils import Vector, Matrix
HERE = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(HERE, "layout.py")).read())
A, HUM, OUT = sys.argv[sys.argv.index("--") + 1:][:3]
random.seed(4)
R_ = math.radians
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = "CYCLES"; sc.cycles.device = "CPU"
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1080, 1920, 100
sc.render.fps, sc.render.fps_base = 60, 1.0
sc.frame_start, sc.frame_end = 1, END
sc.cycles.samples = 48; sc.cycles.use_adaptive_sampling = True; sc.cycles.adaptive_threshold = 0.05
sc.cycles.use_denoising = True; sc.cycles.denoiser = "OPENIMAGEDENOISE"
sc.cycles.max_bounces = 8; sc.cycles.diffuse_bounces = 3; sc.cycles.glossy_bounces = 3
sc.cycles.transmission_bounces = 8; sc.cycles.transparent_max_bounces = 8
sc.cycles.caustics_reflective = sc.cycles.caustics_refractive = False
sc.render.use_persistent_data = True
sc.render.use_motion_blur = True; sc.render.motion_blur_shutter = 0.5
sc.view_settings.view_transform = "AgX"; sc.view_settings.look = "AgX - Medium High Contrast"
sc.render.image_settings.file_format = "PNG"

def col(name, parent=None):
    c = bpy.data.collections.new(name); (parent or sc.collection).children.link(c); return c
C_EXT, C_WALL, C_ROOM, C_PROP, C_CUP, C_FX = [col(n) for n in ("Exterior", "ShotWall", "Room", "Props", "Tumbler", "FX")]

# ------------------------------------------------------------------ materials
def tex_path(asset, kind, res="2k"):
    d = os.path.join(A, asset, "textures")
    for f in os.listdir(d):
        if kind in f: return os.path.join(d, f)
def img(p, non_color=False):
    im = bpy.data.images.load(p, check_existing=True)
    if non_color: im.colorspace_settings.name = "Non-Color"
    return im
def pbr(name, asset, scale=1.0, tint=None, rough_mul=1.0, bump=1.0, rot=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; N = nt.nodes; L = nt.links
    bs = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord"); mp = N.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (scale, scale, scale)
    mp.inputs["Rotation"].default_value[2] = rot
    L.new(tc.outputs["Object"], mp.inputs["Vector"])
    d = N.new("ShaderNodeTexImage"); d.image = img(tex_path(asset, "_diff")); L.new(mp.outputs[0], d.inputs[0]); d.projection = "BOX"; d.projection_blend = 0.15
    if tint:
        mx = N.new("ShaderNodeMix"); mx.data_type = "RGBA"; mx.blend_type = "MULTIPLY"; mx.inputs[0].default_value = 1.0
        L.new(d.outputs[0], mx.inputs[6]); mx.inputs[7].default_value = (*tint, 1); L.new(mx.outputs[2], bs.inputs["Base Color"])
    else:
        L.new(d.outputs[0], bs.inputs["Base Color"])
    rp = tex_path(asset, "_rough")
    if rp:
        r = N.new("ShaderNodeTexImage"); r.image = img(rp, True); L.new(mp.outputs[0], r.inputs[0]); r.projection = "BOX"; r.projection_blend = 0.15
        mt = N.new("ShaderNodeMath"); mt.operation = "MULTIPLY"; mt.inputs[1].default_value = rough_mul
        L.new(r.outputs[0], mt.inputs[0]); L.new(mt.outputs[0], bs.inputs["Roughness"])
    np_ = tex_path(asset, "_nor_gl")
    if np_:
        n = N.new("ShaderNodeTexImage"); n.image = img(np_, True); L.new(mp.outputs[0], n.inputs[0]); n.projection = "BOX"; n.projection_blend = 0.15
        nm = N.new("ShaderNodeNormalMap"); nm.inputs[0].default_value = bump; L.new(n.outputs[0], nm.inputs[1]); L.new(nm.outputs[0], bs.inputs["Normal"])
    return m
def flat(name, color, rough=0.5, metal=0.0, emit=None, estr=0.0, trans=0.0, ior=1.45, alpha=1.0, coat=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1); b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal; b.inputs["Transmission Weight"].default_value = trans; b.inputs["IOR"].default_value = ior
    b.inputs["Alpha"].default_value = alpha; b.inputs["Coat Weight"].default_value = coat
    if emit: b.inputs["Emission Color"].default_value = (*emit, 1); b.inputs["Emission Strength"].default_value = estr
    return m
M_FLOOR = pbr("M_WoodFloor", "wood_floor", 0.5, rough_mul=0.8)
M_PLASTER = pbr("M_Plaster", "painted_plaster_wall", 0.8, tint=(1.0, 0.97, 0.92), bump=0.3)
M_SIDING = pbr("M_Siding", "white_planks_clean", 1.0, tint=(0.62, 0.70, 0.66), rot=R_(90))
M_ROOF = pbr("M_Roof", "grey_roof_tiles_02", 1.0, tint=(0.55, 0.52, 0.5))
M_ASPH = pbr("M_Asphalt", "asphalt_02", 0.3)
M_GRASS = pbr("M_Lawn", "grass_ground", 0.5, tint=(0.75, 0.85, 0.65))
M_CONC = pbr("M_Concrete", "concrete_floor_painted", 0.6, tint=(0.75, 0.74, 0.72))
M_TRIM = flat("M_Trim", (0.86, 0.85, 0.82), 0.4)
M_SHUTTER = flat("M_Shutter", (0.10, 0.17, 0.14), 0.45)
M_GLASS = flat("M_Glass", (0.9, 0.95, 1.0), 0.02, trans=1.0, ior=1.45)
M_OSB = flat("M_OSB", (0.55, 0.40, 0.23), 0.8)
M_STUD = flat("M_Stud", (0.72, 0.58, 0.40), 0.75)
M_GYP = flat("M_Drywall", (0.88, 0.87, 0.84), 0.9)
M_INSUL = flat("M_Insulation", (0.92, 0.62, 0.62), 0.95)
M_WARMWIN = flat("M_WarmWindow", (0.2, 0.15, 0.1), 0.6, emit=(1.0, 0.62, 0.32), estr=2.5)

# ------------------------------------------------------------------ mesh helpers
def box(name, p0, p1, mat, coll, bevel=0.0):
    p0, p1 = Vector(p0), Vector(p1)
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts: v.co = Vector((v.co.x * (p1.x - p0.x), v.co.y * (p1.y - p0.y), v.co.z * (p1.z - p0.z)))
    bmesh.ops.translate(bm, verts=bm.verts, vec=(p0 + p1) / 2)
    uv = bm.loops.layers.uv.new()
    for f in bm.faces:
        n = f.normal
        for l in f.loops:
            c = l.vert.co
            l[uv].uv = (c.y, c.z) if abs(n.x) > 0.5 else ((c.x, c.z) if abs(n.y) > 0.5 else (c.x, c.y))
    bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); coll.objects.link(o); o.data.materials.append(mat)
    if bevel:
        b = o.modifiers.new("bev", "BEVEL"); b.width = bevel; b.segments = 2; b.limit_method = "ANGLE"
    return o
def wall_with_holes(name, axis, a0, a1, y0, y1, z0, z1, holes, mat, coll, bevel=0.0):
    """box slab spanning y0..y1, z0..z1 (axis 'x': thickness along x from a0..a1; axis 'y': thickness along y) with rectangular holes [(u0,u1,z0,z1)]"""
    us = sorted({y0, y1} | {h[0] for h in holes} | {h[1] for h in holes})
    out = []
    for ua, ub in zip(us, us[1:]):
        zs = [(z0, z1)]
        for h in holes:
            if h[0] <= ua and ub <= h[1]:
                zs = [(z0, h[2]), (h[3], z1)]
        for za, zb in zs:
            if zb - za < 1e-4: continue
            if axis == "x": out.append(box(name, (a0, ua, za), (a1, ub, zb), mat, coll, bevel))
            else: out.append(box(name, (ua, a0, za), (ub, a1, zb), mat, coll, bevel))
    return out
def lathe(name, prof, n=64, mat=None, coll=None, close_bottom=True, close_top=False, smooth=True):
    """prof: [(r, z), ...] bottom->top; revolve around Z"""
    me = bpy.data.meshes.new(name); verts = []; faces = []
    for i in range(n):
        a = 2 * math.pi * i / n
        for r, z in prof: verts.append((r * math.cos(a), r * math.sin(a), z))
    m = len(prof)
    for i in range(n):
        j = (i + 1) % n
        for k in range(m - 1):
            faces.append((i * m + k, j * m + k, j * m + k + 1, i * m + k + 1))
    if close_bottom:
        verts.append((0, 0, prof[0][1])); c = len(verts) - 1
        for i in range(n): faces.append((c, ((i + 1) % n) * m, i * m))
    if close_top:
        verts.append((0, 0, prof[-1][1])); c = len(verts) - 1
        for i in range(n): faces.append((c, i * m + m - 1, ((i + 1) % n) * m + m - 1))
    me.from_pydata(verts, [], faces); me.update()
    if smooth: me.shade_smooth()
    o = bpy.data.objects.new(name, me); (coll or sc.collection).objects.link(o)
    if mat: me.materials.append(mat)
    return o
def append_asset(asset, coll, loc, rot_z=0.0, scale=1.0, keep=None, res="1k"):
    f = os.path.join(A, asset, "%s_%s.blend" % (asset, res))
    with bpy.data.libraries.load(f) as (src, dst): dst.objects = list(src.objects)
    root = bpy.data.objects.new(asset + "_root", None); coll.objects.link(root)
    root.location = loc; root.rotation_euler = (0, 0, rot_z); root.scale = (scale,) * 3
    obs = []
    for o in dst.objects:
        if o is None or o.type not in ("MESH",): continue
        if keep and not keep(o.name): continue
        coll.objects.link(o); o.parent = root; obs.append(o)
    return root, obs
def instance(root, coll, loc, rot_z=0.0, scale=1.0, name=None):
    new = bpy.data.objects.new(name or root.name + "_i", None); coll.objects.link(new)
    new.location = loc; new.rotation_euler = (0, 0, rot_z); new.scale = (scale,) * 3
    for ch in root.children:
        c = ch.copy(); coll.objects.link(c); c.parent = new
    return new

# ------------------------------------------------------------------ world (dusk)
wo = bpy.data.worlds.new("World"); sc.world = wo; wo.use_nodes = True
WN = wo.node_tree.nodes; WL = wo.node_tree.links
env = WN.new("ShaderNodeTexEnvironment"); env.image = img(os.path.join(A, "hdri", "belfast_sunset_puresky_2k.hdr"))
mpw = WN.new("ShaderNodeMapping"); tcw = WN.new("ShaderNodeTexCoord"); WL.new(tcw.outputs["Generated"], mpw.inputs[0]); WL.new(mpw.outputs[0], env.inputs[0])
mpw.inputs["Rotation"].default_value[2] = R_(200)
WL.new(env.outputs[0], WN["Background"].inputs[0]); WN["Background"].inputs[1].default_value = 0.55

# ------------------------------------------------------------------ house shell
r = ROOM; H = r["h"]
HX1 = 9.4; HY0 = r["y0"] - 0.15; HY1 = 6.6            # house footprint (outside of the siding planes)
# interior floor slab + ceiling
fl = box("RoomFloor", (r["x0"], r["y0"], -0.05), (r["x1"], r["y1"], 0.0), M_FLOOR, C_ROOM)
box("Ceiling", (r["x0"], r["y0"], H), (r["x1"], r["y1"], H + 0.05), M_PLASTER, C_ROOM)
# interior walls (back, sides); window in back wall for depth
wall_with_holes("BackWall", "x", r["x1"], r["x1"] + 0.15, r["y0"] - 0.15, r["y1"] + 0.15, 0, H, [(-1.4, -0.2, 0.0, 2.1)], M_PLASTER, C_ROOM)  # doorway to hall
wall_with_holes("SideWallS", "y", r["y0"] - 0.15, r["y0"], r["x0"] - 0.17, r["x1"] + 0.15, 0, H, [], M_PLASTER, C_ROOM)
wall_with_holes("SideWallN", "y", r["y1"], r["y1"] + 0.15, r["x0"] - 0.17, r["x1"] + 0.15, 0, H, [(3.6, 5.2, 0.0, 2.2)], M_PLASTER, C_ROOM)  # opening to kitchen
box("HallBack", (r["x1"] + 1.6, r["y0"], 0), (r["x1"] + 1.75, r["y1"], H), M_PLASTER, C_ROOM)
box("HallFloor", (r["x1"], r["y0"], -0.05), (r["x1"] + 1.75, r["y1"], 0), M_FLOOR, C_ROOM)
box("KitchenFloor", (r["x0"], r["y1"], -0.05), (r["x1"], r["y1"] + 3.0, 0), M_FLOOR, C_ROOM)
box("KitchenWall", (r["x0"], r["y1"] + 3.0, 0), (r["x1"], r["y1"] + 3.15, H), M_PLASTER, C_ROOM)
box("KitchenCounter", (r["x0"] + 1.2, r["y1"] + 2.4, 0), (r["x1"] - 0.6, r["y1"] + 3.0, 0.9), flat("M_Cabinet", (0.25, 0.3, 0.33), 0.5), C_ROOM, 0.005)
box("KitchenTop", (r["x0"] + 1.18, r["y1"] + 2.38, 0.9), (r["x1"] - 0.58, r["y1"] + 3.0, 0.94), flat("M_Stone", (0.82, 0.8, 0.76), 0.25), C_ROOM, 0.004)
box("Baseboard", (r["x1"] - 0.02, r["y0"], 0), (r["x1"], r["y1"], 0.1), M_TRIM, C_ROOM)
box("BaseboardS", (r["x0"], r["y0"], 0), (r["x1"], r["y0"] + 0.02, 0.1), M_TRIM, C_ROOM)

# shot wall: real layers with real windows (y ranges); hole cut by boolean in 03
WIN = [(-1.75, -0.7, 0.85, 2.15), (1.4, 2.5, 0.85, 2.15)]      # two windows in the dining room façade
WIN_EXT = WIN + [(3.9, 4.9, 0.0, 2.15), (5.5, 6.3, 0.85, 2.15)]  # + front door + hall window (beyond the room)
x_sid0, x_sid1 = WALL_OUT, WALL_OUT + 0.02
x_osb0, x_osb1 = x_sid1, x_sid1 + 0.012
x_cav0, x_cav1 = x_osb1, WALL_IN - 0.0125
x_gyp0 = x_cav1
HOLE_LAYERS = []
HOLE_LAYERS += wall_with_holes("Drywall", "x", x_gyp0, WALL_IN, r["y0"], r["y1"], 0, H, WIN, M_GYP, C_WALL)
# inner face paint (plaster look) is the drywall itself; give it the plaster material
for o in HOLE_LAYERS: o.data.materials[0] = M_PLASTER
osb = wall_with_holes("Sheathing", "x", x_osb0, x_osb1, HY0, HY1, -0.4, H + 0.35, WIN_EXT, M_OSB, C_WALL)
HOLE_LAYERS += osb
# studs every 0.406 m, skipping window openings (headers/sills added)
y = r["y0"]
while y < r["y1"]:
    inwin = [w for w in WIN if w[0] - 0.05 < y < w[1] + 0.05]
    if not inwin:
        box("Stud", (x_cav0, y, 0), (x_cav1, y + 0.038, H), M_STUD, C_WALL)
    y += 0.406
for w in WIN:
    box("Header", (x_cav0, w[0] - 0.04, w[3]), (x_cav1, w[1] + 0.04, w[3] + 0.2), M_STUD, C_WALL)
    box("Sill", (x_cav0, w[0] - 0.04, w[2] - 0.04), (x_cav1, w[1] + 0.04, w[2]), M_STUD, C_WALL)
    for yy in (w[0] - 0.078, w[1] + 0.04): box("JackStud", (x_cav0, yy, 0), (x_cav1, yy + 0.038, H), M_STUD, C_WALL)
box("BottomPlate", (x_cav0, r["y0"], 0), (x_cav1, r["y1"], 0.038), M_STUD, C_WALL)
box("TopPlate", (x_cav0, r["y0"], H - 0.076), (x_cav1, r["y1"], H), M_STUD, C_WALL)
# insulation batts in each stud bay (fluffy displaced boxes)
ins_tex = bpy.data.textures.new("InsulNoise", "CLOUDS"); ins_tex.noise_scale = 0.03
y = r["y0"] + 0.038
INSUL = []
while y < r["y1"] - 0.1:
    yb = min(y + 0.368, r["y1"])
    if not [w for w in WIN if w[0] - 0.1 < (y + yb) / 2 < w[1] + 0.1] and not (y - 0.02 < -2.37 < yb + 0.02):
        o = box("Insulation", (x_cav0 + 0.004, y + 0.004, 0.04), (x_cav1 - 0.03, yb - 0.004, H - 0.08), M_INSUL, C_WALL)
        sd = o.modifiers.new("sub", "SUBSURF"); sd.levels = sd.render_levels = 3; sd.subdivision_type = "SIMPLE"
        dp = o.modifiers.new("fluff", "DISPLACE"); dp.texture = ins_tex; dp.strength = 0.012
        INSUL.append(o)
    y += 0.406
# lap siding boards (each board tilted so the lower edge sits proud), corner boards, trim
def siding_face(name, plane, u0, u1, z0, z1, holes, normal_sign):
    """plane: ('x', x_out) boards along Y; ('y', y_out) boards along X. normal_sign: +1/-1 outward along the axis"""
    exp = 0.152; z = z0; out = []
    while z < z1 - 0.01:
        zb = min(z + exp + 0.025, z1)
        segs = [(u0, u1)]
        for h in holes:
            if h[2] - 0.02 < z + exp / 2 < h[3] + 0.02:
                segs = [(a, min(b, h[0])) if a < h[0] else (max(a, h[1]), b) for a, b in segs for _ in [0]]
                segs = [s for s in [(a, b) for a, b in [(u0, h[0]), (h[1], u1)]] if s[1] > s[0]] if len(holes) == 1 else segs
        # robust split for several holes
        segs = [(u0, u1)]
        for h in sorted(holes):
            if h[2] - 0.02 < z + exp / 2 < h[3] + 0.02:
                nsegs = []
                for a, b in segs:
                    if h[1] <= a or h[0] >= b: nsegs.append((a, b))
                    else:
                        if h[0] > a: nsegs.append((a, h[0]))
                        if h[1] < b: nsegs.append((h[1], b))
                segs = nsegs
        for a, b in segs:
            if b - a < 0.02: continue
            if plane[0] == "x":
                xo = plane[1]
                o = box(name, (xo - 0.004 * normal_sign if normal_sign > 0 else xo, a, z), (xo + (0.0 if normal_sign > 0 else 0.004), b, zb), M_SIDING, C_EXT)
                me = o.data
                for v in me.vertices:
                    if v.co.z < z + 0.001: v.co.x += -0.016 if normal_sign < 0 else 0.016
            else:
                yo = plane[1]
                o = box(name, (a, yo, z), (b, yo + 0.004 * (1 if normal_sign > 0 else -1), zb), M_SIDING, C_EXT)
                for v in o.data.vertices:
                    if v.co.z < z + 0.001: v.co.y += 0.016 * normal_sign
            out.append(o)
        z += exp
    return out
SIDING_SHOT = siding_face("Siding", ("x", WALL_OUT + 0.016), HY0, HY1, 0.0, H + 0.3, WIN_EXT, -1)
HOLE_LAYERS += SIDING_SHOT
siding_face("SidingS", ("y", HY0), WALL_OUT, HX1, 0.0, H + 0.3, [(1.0, 2.2, 0.9, 2.1), (5.0, 6.2, 0.9, 2.1)], -1)
siding_face("SidingN", ("y", HY1), WALL_OUT, HX1, 0.0, H + 0.3, [(2.0, 3.2, 0.9, 2.1)], 1)
box("SideSheathS", (WALL_OUT + 0.02, HY0 + 0.004, -0.4), (HX1, HY0 + 0.1, H + 0.35), M_OSB, C_EXT)
box("SideSheathN", (WALL_OUT + 0.02, HY1 - 0.1, -0.4), (HX1, HY1 - 0.004, H + 0.35), M_OSB, C_EXT)
box("RearWall", (HX1 - 0.15, HY0, -0.4), (HX1, HY1, H + 0.35), M_SIDING, C_EXT)
for yy in (HY0 - 0.03, HY1 - 0.09):
    box("CornerBoard", (WALL_OUT - 0.03, yy, -0.05), (WALL_OUT + 0.1, yy + 0.12, H + 0.35), M_TRIM, C_EXT, 0.004)
for (a0, b0, a1, b1) in ((WALL_OUT - 0.02, HY0 - 0.03, WALL_OUT + 0.2, HY1 + 0.03), (HX1 - 0.2, HY0 - 0.03, HX1, HY1 + 0.03),
                         (WALL_OUT - 0.02, HY0 - 0.03, HX1, HY0 + 0.17), (WALL_OUT - 0.02, HY1 - 0.17, HX1, HY1 + 0.03)):
    box("Foundation", (a0, b0, GROUND_Z - 0.1), (a1, b1, -0.06 if a1 - a0 > 1 and b1 - b0 > 1 else -0.06), M_CONC, C_EXT)
box("FoundationFace", (WALL_OUT - 0.02, HY0 - 0.03, GROUND_Z - 0.1), (WALL_OUT - 0.0, HY1 + 0.03, 0.0), M_CONC, C_EXT)
# windows: trim, sash, glass, shutters (exterior); interior casing + sill + curtains
M_CURT = flat("M_Curtain", (0.78, 0.72, 0.62), 0.9)
for i, (u0, u1, z0, z1) in enumerate(WIN_EXT):
    door = z0 < 0.1
    xo = WALL_OUT - 0.002
    for (a, b, c, d) in [(u0 - 0.1, u0, z0, z1 + 0.1), (u1, u1 + 0.1, z0, z1 + 0.1), (u0 - 0.1, u1 + 0.1, z1, z1 + 0.14)] + ([] if door else [(u0 - 0.12, u1 + 0.12, z0 - 0.06, z0)]):
        box("WinTrim", (xo - 0.03, a, c), (xo + 0.02, b, d), M_TRIM, C_EXT, 0.004)
    if door:
        box("FrontDoor", (WALL_OUT + 0.02, u0, 0.0), (WALL_OUT + 0.07, u1, z1), flat("M_Door", (0.35, 0.08, 0.07), 0.35), C_EXT, 0.006)
        box("DoorKnob", (WALL_OUT - 0.0, u1 - 0.14, 1.0), (WALL_OUT + 0.02, u1 - 0.1, 1.04), flat("M_Brass", (0.8, 0.6, 0.3), 0.25, 1.0), C_EXT)
        continue
    xm = WALL_OUT + 0.06
    box("Glass", (xm - 0.003, u0, z0), (xm + 0.003, u1, z1), M_GLASS, C_EXT)
    for zz in (z0, (z0 + z1) / 2 - 0.02, z1 - 0.045): box("Sash", (xm - 0.02, u0, zz), (xm + 0.02, u1, zz + 0.045), M_TRIM, C_EXT)
    for uu in (u0, (u0 + u1) / 2 - 0.015, u1 - 0.04): box("Mullion", (xm - 0.02, uu, z0), (xm + 0.02, uu + 0.03 if uu != u0 and uu != u1 - 0.04 else uu + 0.04, z1), M_TRIM, C_EXT)
    for (a, b) in ((u0 - 0.55, u0 - 0.12), (u1 + 0.12, u1 + 0.55)):
        sh = box("Shutter", (xo - 0.05, a, z0), (xo - 0.02, b, z1), M_SHUTTER, C_EXT, 0.004)
    if u1 < r["y1"]:  # interior side of dining-room windows
        box("InSill", (WALL_IN - 0.01, u0 - 0.1, z0 - 0.04), (WALL_IN + 0.06, u1 + 0.1, z0), M_TRIM, C_ROOM, 0.004)
        for (a, b) in ((u0 - 0.45, u0 - 0.05), (u1 + 0.05, u1 + 0.45)):
            c = box("Curtain", (WALL_IN + 0.06, a, 0.05), (WALL_IN + 0.09, b, H - 0.15), M_CURT, C_ROOM)
            sd = c.modifiers.new("sub", "SUBSURF"); sd.levels = sd.render_levels = 2
            wv = c.modifiers.new("folds", "WAVE"); wv.use_x = False; wv.use_y = True; wv.use_normal = False
            wv.height = 0.025; wv.width = 0.12; wv.narrowness = 1.0; wv.speed = 0.0
        # glow behind the hall window/door (beyond the room) reads as lived-in
for (u0, u1, z0, z1) in WIN_EXT[3:]:
    box("HallGlow", (WALL_OUT + 0.4, u0, z0), (WALL_OUT + 0.42, u1, z1), M_WARMWIN, C_EXT)
# roof: gable, ridge along Y
ov = 0.45; rise = 2.2; xm = (WALL_OUT + HX1) / 2; hw = (HX1 - WALL_OUT) / 2 + ov
def roof_plane(name, sgn):
    me = bpy.data.meshes.new(name)
    zE = H + 0.25; x_e = xm + sgn * hw; x_r = xm
    vs = [(x_e, HY0 - ov, zE - 0.05), (x_e, HY1 + ov, zE - 0.05), (x_r, HY1 + ov, zE + rise), (x_r, HY0 - ov, zE + rise)]
    me.from_pydata(vs, [], [(0, 1, 2, 3)] if sgn < 0 else [(3, 2, 1, 0)]); me.update()
    uvl = me.uv_layers.new()
    for li, l in enumerate(me.loops):
        v = me.vertices[l.vertex_index].co; uvl.data[li].uv = (v.y, math.hypot(v.x - x_r, v.z - zE - rise))
    o = bpy.data.objects.new(name, me); C_EXT.objects.link(o); me.materials.append(M_ROOF)
    so = o.modifiers.new("thick", "SOLIDIFY"); so.thickness = 0.06
    return o
roof_plane("RoofW", -1); roof_plane("RoofE", 1)
box("Fascia", (WALL_OUT - ov - 0.02, HY0 - ov, H + 0.05), (WALL_OUT - ov + 0.03, HY1 + ov, H + 0.22), M_TRIM, C_EXT)
box("Soffit", (WALL_OUT - ov, HY0 - ov, H + 0.18), (WALL_OUT, HY1 + ov, H + 0.2), M_TRIM, C_EXT)
# gable end triangles
for yy, nm in ((HY0 - 0.01, "GableS"), (HY1 + 0.01, "GableN")):
    me = bpy.data.meshes.new(nm); me.from_pydata([(WALL_OUT, yy, H + 0.25), (HX1, yy, H + 0.25), (xm, yy, H + 0.25 + rise - 0.3)], [], [(0, 1, 2)])
    o = bpy.data.objects.new(nm, me); C_EXT.objects.link(o); me.materials.append(M_SIDING)
    me.uv_layers.new()
# porch at the front door
DOOR = WIN_EXT[2]
box("PorchDeck", (WALL_OUT - 1.8, DOOR[0] - 0.9, GROUND_Z), (WALL_OUT, DOOR[1] + 0.9, -0.03), flat("M_Deck", (0.42, 0.33, 0.25), 0.7), C_EXT, 0.01)
for k in range(2): box("Step", (WALL_OUT - 1.8 - 0.3 * (k + 1), DOOR[0] - 0.2, GROUND_Z), (WALL_OUT - 1.8 - 0.3 * k, DOOR[1] + 0.2, -0.03 - 0.17 * (k + 1)), M_CONC, C_EXT, 0.01)
for yy in (DOOR[0] - 0.85, DOOR[1] + 0.75):
    box("PorchPost", (WALL_OUT - 1.75, yy, -0.03), (WALL_OUT - 1.65, yy + 0.1, H + 0.15), M_TRIM, C_EXT, 0.005)
box("PorchRail", (WALL_OUT - 1.75, DOOR[0] - 0.85, 0.85), (WALL_OUT - 1.68, DOOR[0] - 0.1, 0.9), M_TRIM, C_EXT)
for k in range(9):
    yy = DOOR[0] - 0.8 + k * 0.08
    box("Baluster", (WALL_OUT - 1.73, yy, -0.03), (WALL_OUT - 1.7, yy + 0.03, 0.85), M_TRIM, C_EXT)
box("PorchRoof", (WALL_OUT - 1.95, DOOR[0] - 1.05, H + 0.15), (WALL_OUT, DOOR[1] + 1.05, H + 0.25), M_TRIM, C_EXT)
pl = box("PorchLampGlass", (WALL_OUT - 0.12, DOOR[1] + 0.18, 1.75), (WALL_OUT - 0.02, DOOR[1] + 0.3, 1.95), flat("M_LampGlass", (1, 0.8, 0.5), 0.3, emit=(1.0, 0.7, 0.4), estr=20), C_EXT)
lp = bpy.data.lights.new("PorchLight", "POINT"); lp.energy = 60; lp.color = (1.0, 0.72, 0.45); lp.shadow_soft_size = 0.05
o = bpy.data.objects.new("PorchLight", lp); o.location = (WALL_OUT - 0.25, DOOR[1] + 0.24, 1.85); C_EXT.objects.link(o)

# ------------------------------------------------------------------ yard, street, neighbours
box("Lawn", (-9.0, -16, GROUND_Z - 0.05), (HX1 + 4, 18, GROUND_Z), M_GRASS, C_EXT)
box("Sidewalk", (-10.6, -40, GROUND_Z - 0.04), (-9.0, 40, GROUND_Z + 0.03), M_CONC, C_EXT)
box("Curb", (-10.8, -40, GROUND_Z - 0.15), (-10.6, 40, GROUND_Z + 0.02), M_CONC, C_EXT)
box("Street", (-19.0, -40, GROUND_Z - 0.18), (-10.8, 40, GROUND_Z - 0.12), M_ASPH, C_EXT)
box("Walkway", (-9.0, DOOR[0] - 0.1, GROUND_Z - 0.03), (WALL_OUT - 2.4, DOOR[1] + 0.1, GROUND_Z + 0.015), M_CONC, C_EXT)
box("Driveway", (-9.0, -9.0, GROUND_Z - 0.03), (WALL_OUT, -6.0, GROUND_Z + 0.01), M_CONC, C_EXT)
# lawn grass (hair particles: no cache needed)
lawn_g = box("LawnGrass", (-8.9, -5.8, GROUND_Z - 0.01), (WALL_OUT - 0.25, 12.0, GROUND_Z), M_GRASS, C_EXT)
me = lawn_g.data
ps = lawn_g.modifiers.new("grass", "PARTICLE_SYSTEM").particle_system; pset = ps.settings
pset.type = "HAIR"; pset.count = 60000; pset.hair_length = 0.07; pset.use_advanced_hair = True
pset.render_type = "PATH"; pset.child_type = "NONE"
pset.root_radius = 0.004; pset.tip_radius = 0.0; pset.radius_scale = 1.0
pset.brownian_factor = 0.05; pset.factor_random = 0.3; pset.length_random = 0.6
lawn_g.data.materials.append(flat("M_GrassBlade", (0.10, 0.17, 0.05), 0.6))
pset.material = 2
# picket fence along the sidewalk
M_FENCE = flat("M_Fence", (0.88, 0.87, 0.84), 0.5)
for k in range(int((26.0) / 0.14)):
    yy = -14 + k * 0.14
    if DOOR[0] - 0.4 < yy < DOOR[1] + 0.4 or -9.2 < yy < -5.8: continue
    box("Picket", (-8.95, yy, GROUND_Z), (-8.92, yy + 0.08, GROUND_Z + 0.95), M_FENCE, C_EXT)
for zz in (0.25, 0.7): box("FenceRail", (-8.92, -14, GROUND_Z + zz), (-8.88, 12, GROUND_Z + zz + 0.07), M_FENCE, C_EXT)
# street lamp post (procedural)
M_POLE = flat("M_Pole", (0.12, 0.12, 0.12), 0.4, 0.8)
for yy in (-9.5, 12.0):
    box("LampPole", (-10.45, yy, GROUND_Z), (-10.35, yy + 0.1, GROUND_Z + 4.2), M_POLE, C_EXT)
    box("LampArm", (-11.3, yy, GROUND_Z + 4.1), (-10.35, yy + 0.1, GROUND_Z + 4.2), M_POLE, C_EXT)
    box("LampHead", (-11.45, yy - 0.08, GROUND_Z + 3.98), (-11.05, yy + 0.18, GROUND_Z + 4.1),
        flat("M_StreetGlow", (1, 0.85, 0.6), 0.3, emit=(1.0, 0.78, 0.5), estr=12), C_EXT)
    ls = bpy.data.lights.new("StreetLamp", "SPOT"); ls.energy = 900; ls.color = (1.0, 0.75, 0.45); ls.spot_size = R_(110); ls.shadow_soft_size = 0.2
    o = bpy.data.objects.new("StreetLamp", ls); o.location = (-11.25, yy + 0.05, GROUND_Z + 3.95); C_EXT.objects.link(o)
# neighbour houses (simplified, lit windows) beside and across the street
M_SID2 = pbr("M_Siding2", "white_planks_clean", 1.0, tint=(0.80, 0.74, 0.62), rot=R_(90))
M_SID3 = pbr("M_Siding3", "white_planks_clean", 1.0, tint=(0.55, 0.60, 0.72), rot=R_(90))
def neighbour(x0, y0, w, d, h, face_sign, mat):
    box("NbHouse", (x0, y0, GROUND_Z), (x0 + d, y0 + w, GROUND_Z + h), mat, C_EXT)
    xf = x0 if face_sign < 0 else x0 + d
    for k in range(3):
        yy = y0 + 0.8 + k * (w - 1.6) / 2.0
        box("NbWin", (xf - 0.03, yy, GROUND_Z + 1.2), (xf + 0.03, yy + 0.9, GROUND_Z + 2.4), M_WARMWIN if (k + int(x0)) % 2 == 0 else M_GLASS, C_EXT)
        box("NbTrim", (xf - 0.05, yy - 0.08, GROUND_Z + 1.12), (xf + 0.05, yy + 0.98, GROUND_Z + 1.2), M_TRIM, C_EXT)
    me = bpy.data.meshes.new("NbRoof"); zz = GROUND_Z + h
    me.from_pydata([(x0 - 0.4, y0 - 0.4, zz), (x0 + d + 0.4, y0 - 0.4, zz), (x0 + d + 0.4, y0 + w + 0.4, zz), (x0 - 0.4, y0 + w + 0.4, zz),
                    (x0 + d / 2, y0 - 0.4, zz + 2.0), (x0 + d / 2, y0 + w + 0.4, zz + 2.0)], [],
                   [(0, 4, 5, 3), (1, 2, 5, 4), (0, 1, 4), (3, 5, 2)])
    me.uv_layers.new(); o = bpy.data.objects.new("NbRoof", me); C_EXT.objects.link(o); me.materials.append(M_ROOF)
neighbour(-0.5, -22.0, 10, 9, 3.4, -1, M_SID2)
neighbour(-0.5, 13.0, 9, 9, 3.4, -1, M_SID3)
neighbour(-30.0, -12.0, 10, 9, 3.4, 1, M_SID3)
neighbour(-30.0, 2.0, 11, 9, 3.4, 1, M_SID2)
neighbour(-30.0, 17.0, 10, 9, 3.4, 1, M_SID2)
# shrubs along the façade and yard
sh_root, _ = append_asset("shrub_02", C_EXT, (WALL_OUT - 0.7, -3.0, GROUND_Z), 0, 0.9, keep=lambda n: n.endswith("LOD1"))
sh_root.name = "Shrub_src"
for (xx, yy, rz, s) in [(WALL_OUT - 0.7, -0.9, 1.2, 0.8), (WALL_OUT - 0.7, 0.9, 2.0, 0.85), (WALL_OUT - 0.7, 3.0, 0.4, 0.95),
                        (WALL_OUT - 0.8, 6.2, 2.6, 0.9), (-8.2, -12, 0.7, 1.2), (-8.3, 9.0, 1.8, 1.1), (-6.0, -14.0, 0.2, 1.4)]:
    instance(sh_root, C_EXT, (xx, yy, GROUND_Z), rz, s)

# ------------------------------------------------------------------ living room furniture + props
tb_root, tb_obs = append_asset("dining_table", C_ROOM, TABLE_C, 0.0); tb_root.scale = (1.0, TABLE_SY, 1.0)
for (asset, loc, rz, s) in [("Sofa_01", (5.6, 2.2, 0), R_(90), 1.15), ("coffee_table_round_01", (4.5, 2.2, 0), 0, 0.75),
                            ("Shelf_01", (6.59, -2.2, 0), R_(-90), 1.0), ("potted_plant_01", (6.2, -2.8, 0), 0, 1.0),
                            ("potted_plant_01", (0.45, 0.35, 0), 1.3, 0.9), ("modern_ceiling_lamp_01", (3.4, 0.0, H - 1.17), 0, 1.0),
                            ("hanging_picture_frame_02", (6.58, -1.0, 1.65), R_(90), 1.2), ("hanging_picture_frame_02", (1.6, 3.19, 1.6), R_(180), 0.9),
                            ("ceramic_vase_02", (6.45, -2.5, 1.14), 0, 0.6), ("potted_plant_04", (4.5, 2.2, 0.37), 0, 1.0)]:
    append_asset(asset, C_ROOM if "plant" in asset or "Sofa" in asset or "Shelf" in asset else C_PROP, loc, rz, s)
bk_root, bk_obs = append_asset("book_encyclopedia_set_01", C_PROP, (6.45, -2.0, 0.73), R_(-90), 0.9, keep=lambda n: "book" in n)
ch_root, _ = append_asset("dining_chair_02", C_ROOM, WOMAN_SEAT, R_(90))          # chair faces -X (towards the wall)
ch_root.name = "Chair_Woman"
ch2 = instance(ch_root, C_ROOM, FIANCE_SEAT, 0.0, name="Chair_Fiance")
instance(ch_root, C_ROOM, (2.3, 0.75, 0), R_(180), name="Chair_Empty1")
instance(ch_root, C_ROOM, (3.1, 0.75, 0), R_(182), name="Chair_Empty2")
instance(ch_root, C_ROOM, (3.9, 0.76, 0), R_(178), name="Chair_Empty3")
instance(ch_root, C_ROOM, (1.75, 0.0, 0), R_(-90), name="Chair_Empty4")
# rug under the sofa area
box("Rug", (3.8, 1.0, 0.0), (6.3, 3.0, 0.008), flat("M_Rug", (0.45, 0.34, 0.27), 0.95), C_ROOM)
# TV on the back wall area (dark, with a soft blue glow)
box("TVStand", (6.25, 1.3, 0.0), (6.55, 3.0, 0.5), flat("M_Walnut", (0.25, 0.15, 0.09), 0.5), C_ROOM, 0.006)
box("TV", (6.5, 1.55, 0.75), (6.56, 2.75, 1.45), flat("M_TVScreen", (0.01, 0.01, 0.012), 0.15, emit=(0.35, 0.5, 0.9), estr=0.6), C_ROOM, 0.004)

# measure the table top
dg = bpy.context.evaluated_depsgraph_get(); bpy.context.view_layer.update()
top = 0.0
for o in tb_obs:
    for v in o.data.vertices:
        w = o.matrix_world @ v.co
        if abs(w.x - TABLE_C.x) < 0.3 and abs(w.y - TABLE_C.y) < 0.3: top = max(top, w.z)
print("TABLE_TOP", round(top, 4), [o.name for o in tb_obs])
TOP = top
sc["table_top"] = TOP
# seat height of the chair
seat = 0.0
for o in ch_root.children:
    for v in o.data.vertices:
        w = o.matrix_world @ v.co
        if (w.to_2d() - WOMAN_SEAT.to_2d()).length < 0.12: seat = max(seat, w.z)
print("SEAT_TOP", round(seat, 4)); sc["seat_top"] = seat

# table setting: plates, cutlery, candle, her glass, bread board
M_PLATE = flat("M_Plate", (0.93, 0.92, 0.9), 0.15, coat=0.6)
M_STEELF = flat("M_Cutlery", (0.8, 0.8, 0.8), 0.2, 1.0)
for (px, py) in ((4.36, 0.12), (4.0, -0.2)):
    p = lathe("Plate", [(0.0, 0), (0.09, 0), (0.105, 0.012), (0.13, 0.02), (0.128, 0.022), (0.1, 0.014), (0.0, 0.01)], 48, M_PLATE, C_PROP, False)
    p.location = (px, py, TOP)
    food = lathe("Food", [(0.0, 0.0), (0.06, 0.0), (0.055, 0.025), (0.02, 0.035), (0.0, 0.036)], 32, flat("M_Pasta", (0.75, 0.45, 0.2), 0.6), C_PROP, False)
    food.location = (px, py, TOP + 0.011)
    tx = bpy.data.textures.new("FoodN", "CLOUDS"); tx.noise_scale = 0.008
    s_ = food.modifiers.new("s", "SUBSURF"); s_.levels = s_.render_levels = 2
    d_ = food.modifiers.new("d", "DISPLACE"); d_.texture = tx; d_.strength = 0.006
    for k, dy in enumerate((-0.16, 0.16)):
        box("Fork" if k == 0 else "Knife", (px - 0.09, py + dy - 0.008, TOP), (px + 0.09, py + dy + 0.008, TOP + 0.004), M_STEELF, C_PROP, 0.001)
cnd = lathe("CandleHolder", [(0.0, 0), (0.04, 0), (0.035, 0.01), (0.012, 0.02), (0.012, 0.08), (0.025, 0.09), (0.0, 0.09)], 32, flat("M_Brass2", (0.8, 0.62, 0.33), 0.3, 1.0), C_PROP, False)
cnd.location = (3.25, 0.18, TOP)
cdl = lathe("Candle", [(0.0, 0), (0.011, 0), (0.011, 0.14), (0.009, 0.145), (0.0, 0.146)], 24, flat("M_Wax", (0.95, 0.93, 0.86), 0.5), C_PROP, False)
cdl.location = (3.25, 0.18, TOP + 0.09)
fl_ = lathe("CandleFlame", [(0.0, 0), (0.004, 0.004), (0.005, 0.012), (0.003, 0.022), (0.0, 0.03)], 16, flat("M_Flame", (1, 0.6, 0.2), 0.5, emit=(1.0, 0.55, 0.18), estr=30), C_FX, True)
fl_.location = (3.25, 0.18, TOP + 0.09 + 0.148)
lc = bpy.data.lights.new("CandleLight", "POINT"); lc.energy = 4; lc.color = (1.0, 0.6, 0.3); lc.shadow_soft_size = 0.01
o = bpy.data.objects.new("CandleLight", lc); o.location = fl_.location + Vector((0, 0, 0.015)); C_FX.objects.link(o)
wg = lathe("WineGlass", [(0.0, 0.0), (0.035, 0.0), (0.033, 0.004), (0.004, 0.008), (0.004, 0.09), (0.03, 0.11), (0.042, 0.16), (0.038, 0.21),
                         (0.036, 0.21), (0.040, 0.16), (0.028, 0.112), (0.0, 0.1)], 40, M_GLASS, C_PROP, False)
wg.location = (3.68, -0.3, TOP); wg.name = "HisGlass"
wg2 = wg.copy(); wg2.data = wg.data; C_PROP.objects.link(wg2); wg2.location = (4.5, 0.3, TOP); wg2.name = "HerGlass"
box("BreadBoard", (3.4, -0.05, TOP), (3.75, 0.2, TOP + 0.018), flat("M_BoardWood", (0.55, 0.36, 0.2), 0.6), C_PROP, 0.004)
bread = lathe("Bread", [(0.0, 0), (0.07, 0), (0.08, 0.03), (0.06, 0.06), (0.0, 0.07)], 32, flat("M_Bread", (0.6, 0.36, 0.15), 0.7), C_PROP, False)
bread.location = (3.57, 0.07, TOP + 0.018); bread.scale = (1.5, 1.0, 0.9)
nap = box("Napkin", (4.4, -0.05, TOP), (4.55, 0.08, TOP + 0.006), flat("M_Napkin", (0.7, 0.25, 0.2), 0.9), C_PROP, 0.002)

# ------------------------------------------------------------------ tumbler (generic insulated steel tumbler, no logo)
M_POWDER = bpy.data.materials.new("M_Powdercoat"); M_POWDER.use_nodes = True
N = M_POWDER.node_tree.nodes; L = M_POWDER.node_tree.links; b = N["Principled BSDF"]
b.inputs["Base Color"].default_value = (0.42, 0.55, 0.58, 1); b.inputs["Roughness"].default_value = 0.42; b.inputs["Metallic"].default_value = 0.15
b.inputs["Coat Weight"].default_value = 0.25; b.inputs["Coat Roughness"].default_value = 0.2
nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 900; bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.08
L.new(nz.outputs[0], bp.inputs["Height"]); L.new(bp.outputs[0], b.inputs["Normal"])
# x-ray mix (keyed in 03): mix the powder coat with a cyan fresnel ghost
ghost = N.new("ShaderNodeBsdfTransparent"); fres = N.new("ShaderNodeLayerWeight"); fres.inputs[0].default_value = 0.3
em = N.new("ShaderNodeEmission"); em.inputs[0].default_value = (0.35, 0.85, 1.0, 1); em.inputs[1].default_value = 1.5
mixg = N.new("ShaderNodeMixShader"); L.new(fres.outputs["Facing"], mixg.inputs[0]); L.new(ghost.outputs[0], mixg.inputs[1]); L.new(em.outputs[0], mixg.inputs[2])
mixx = N.new("ShaderNodeMixShader"); mixx.name = "XRAY"; mixx.inputs[0].default_value = 0.0
L.new(b.outputs[0], mixx.inputs[1]); L.new(mixg.outputs[0], mixx.inputs[2]); L.new(mixx.outputs[0], N["Material Output"].inputs[0])
M_STEEL = flat("M_Steel", (0.78, 0.78, 0.78), 0.18, 1.0)
M_LID = flat("M_LidPlastic", (0.82, 0.86, 0.85), 0.35)
M_STRAW = flat("M_Straw", (0.42, 0.55, 0.58), 0.3, alpha=1.0)
M_WATER = flat("M_Water", (0.9, 0.97, 1.0), 0.0, trans=1.0, ior=1.33)
M_ICE = flat("M_Ice", (0.88, 0.95, 1.0), 0.12, trans=1.0, ior=1.31)
M_DROP = flat("M_Drop", (1, 1, 1), 0.0, trans=1.0, ior=1.12, coat=1.0)
def r_out(z):
    """outer radius profile of the body (narrow base that flares to the top)"""
    pts = [(0.0, 0.039), (0.008, 0.0405), (0.06, 0.0405), (0.075, 0.0425), (0.235, 0.0505), (0.25, 0.051)]
    for (z0, r0), (z1, r1) in zip(pts, pts[1:]):
        if z <= z1: return r0 + (r1 - r0) * (z - z0) / (z1 - z0)
    return pts[-1][1]
Z_TOP = 0.25
prof = [(0.0, 0.0), (0.033, 0.0), (0.0385, 0.002)] + [(r_out(z), z) for z in [i * 0.0025 for i in range(1, 101)]]
body = lathe("Tumbler_Body", prof, 128, M_POWDER, C_CUP, False)
# inner wall (thin steel showing at the rim), lip
inner = lathe("Tumbler_Inner", [(0.0, 0.014), (0.036, 0.014)] + [(r_out(z) - 0.0035, z) for z in [0.03 + i * 0.01 for i in range(23)]] + [(r_out(0.249) - 0.0035, 0.249)], 96, M_STEEL, C_CUP, False)
lip = lathe("Tumbler_Lip", [(r_out(0.236) - 0.0006, 0.236), (r_out(0.236) + 0.0004, 0.2365), (r_out(0.25) + 0.0005, 0.2495), (r_out(0.25) - 0.0035, 0.2505)], 128, M_STEEL, C_CUP, False)
lid = lathe("Tumbler_Lid", [(0.0, 0.262), (0.046, 0.262), (0.052, 0.258), (0.0525, 0.249), (0.051, 0.244), (0.047, 0.244)], 96, M_LID, C_CUP, False)
for nme, prof2 in (("Tumbler_LidTop", [(0.0, 0.265), (0.043, 0.265), (0.046, 0.262), (0.0, 0.262)]),):
    lathe(nme, prof2, 96, M_LID, C_CUP, False)
straw = lathe("Tumbler_Straw", [(0.0035, 0.02), (0.0035, 0.33), (0.0045, 0.331), (0.0045, 0.02)], 24, M_STRAW, C_CUP, False)
straw.location = (0.012, 0.0, 0.0); straw.rotation_euler = (0, R_(-4), 0)
water = lathe("Tumbler_Water", [(0.0, 0.0145), (0.0355, 0.0145)] + [(r_out(z) - 0.0038, z) for z in [0.03 + i * 0.01 for i in range(19)]] + [(0.0, 0.21)], 96, M_WATER, C_CUP, False, True)
# ripple surface (separate plane, displaced in 03)
ws = bpy.data.meshes.new("Tumbler_WaterSurf"); bm = bmesh.new()
bmesh.ops.create_circle(bm, cap_ends=True, segments=96, radius=r_out(0.21) - 0.0039)
bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=6, use_grid_fill=True)
bm.to_mesh(ws); bm.free()
wso = bpy.data.objects.new("Tumbler_WaterSurf", ws); C_CUP.objects.link(wso); wso.location.z = 0.2101; ws.materials.append(M_WATER)
ICE = []
for k in range(6):
    me = bpy.data.meshes.new("Ice"); bm = bmesh.new(); bmesh.ops.create_cube(bm, size=0.024); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new("Tumbler_Ice%d" % k, me); C_CUP.objects.link(o); me.materials.append(M_ICE)
    bv = o.modifiers.new("bev", "BEVEL"); bv.width = 0.004; bv.segments = 3
    a = k * 2.4; rr = 0.018 if k < 5 else 0.0
    o.location = (rr * math.cos(a), rr * math.sin(a), 0.2 - 0.012 * (k % 2) - 0.03 * (k // 3)); o.rotation_euler = (a, a * 0.7, a * 1.3)
    ICE.append(o)
# handle: C-shaped bevelled curve with a rubber grip
hc = bpy.data.curves.new("Tumbler_Handle", "CURVE"); hc.dimensions = "3D"; hc.bevel_depth = 0.0075; hc.bevel_resolution = 4
sp = hc.splines.new("BEZIER"); pts = [(0.039, 0, 0.215), (0.072, 0, 0.205), (0.082, 0, 0.14), (0.074, 0, 0.075), (0.042, 0, 0.068)]
sp.bezier_points.add(len(pts) - 1)
for bp_, p in zip(sp.bezier_points, pts): bp_.co = p; bp_.handle_left_type = bp_.handle_right_type = "AUTO"
handle = bpy.data.objects.new("Tumbler_Handle", hc); C_CUP.objects.link(handle); hc.materials.append(M_POWDER)
for zz in (0.215, 0.068):
    rg = lathe("Tumbler_HandleRing", [(r_out(zz) - 0.001, zz - 0.006), (r_out(zz) + 0.003, zz - 0.005), (r_out(zz) + 0.003, zz + 0.005), (r_out(zz) - 0.001, zz + 0.006)], 96, M_POWDER, C_CUP, False)
# condensation beads on the body (water drops), plus a few running streaks
DROPS = []
random.seed(11)
for k in range(170):
    z = random.uniform(0.02, 0.235); a = random.uniform(0, 2 * math.pi)
    if abs(math.atan2(math.sin(a), math.cos(a))) < 0.35 and 0.06 < z < 0.22: continue   # keep the handle side clean
    s = random.uniform(0.0006, 0.0015) * (1.6 if random.random() < 0.08 else 1.0)
    me = bpy.data.meshes.new("Drop"); bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=10, v_segments=6, radius=1.0)
    for v in bm.verts:
        if v.co.x < 0: v.co.x *= 0.15
    bm.to_mesh(me); bm.free(); me.shade_smooth()
    o = bpy.data.objects.new("Drop", me); C_CUP.objects.link(o); me.materials.append(M_DROP)
    ro = r_out(z) + 0.0001
    o.location = (ro * math.cos(a), ro * math.sin(a), z); o.rotation_euler = (0, 0, a); o.scale = (s * 0.7, s, s * 1.2)
    DROPS.append(o)
cup_root = bpy.data.objects.new("Tumbler", None); C_CUP.objects.link(cup_root)
for o in C_CUP.objects:
    if o is not cup_root and o.parent is None: o.parent = cup_root
cup_root.location = (CUP_C.x, CUP_C.y, TOP)
cup_root.rotation_euler = (0, 0, R_(70))     # handle toward her right hand (+X,+Y)
# dent shape key on the body: pushed in around the impact direction (bullet comes from -X)
bpy.context.view_layer.update()
body.shape_key_add(name="Basis"); dk = body.shape_key_add(name="Dent"); dk.interpolation = "KEY_LINEAR"
imp_z = IMPACT_Z - TOP
sc["impact_local_z"] = imp_z
inv = cup_root.matrix_world.inverted().to_3x3()
dirl = inv @ Vector((-1, -SHOT_SLOPE, 0)).normalized()          # local direction the bullet comes from
ang0 = math.atan2(dirl.y, dirl.x); sc["impact_local_angle"] = ang0
for v in body.data.vertices:
    a = math.atan2(v.co.y, v.co.x); da = math.atan2(math.sin(a - ang0), math.cos(a - ang0))
    dz = v.co.z - imp_z; rr = math.hypot(v.co.x, v.co.y)
    w = math.exp(-((rr * da) ** 2 + dz ** 2) / (2 * 0.011 ** 2))
    ring = 0.0009 * math.exp(-(((rr * da) ** 2 + dz ** 2) ** 0.5 - 0.016) ** 2 / (2 * 0.004 ** 2))
    push = 0.0026 * w - ring * 0.5
    dk.data[v.index].co = v.co - Vector((v.co.x, v.co.y, 0)).normalized() * push if rr > 1e-5 else v.co
sd = body.modifiers.new("sub", "SUBSURF"); sd.levels = 1; sd.render_levels = 2

# ------------------------------------------------------------------ bullet (jacketed round nose, ~9 mm) with a mushroom shape key
M_COPPER = flat("M_Copper", (0.85, 0.45, 0.28), 0.22, 1.0)
bprof = [(0.0, 0.0), (0.0045, 0.0), (0.0046, 0.0004), (0.0046, 0.0085)] + [(0.0046 * math.cos(t * math.pi / 2) ** 0.7, 0.0085 + 0.0065 * math.sin(t * math.pi / 2)) for t in [i / 10 for i in range(1, 11)]]
bul = lathe("Bullet", bprof, 48, M_COPPER, C_FX, True)
for v in bul.data.vertices:   # lathe is along Z; bullet axis -> +X
    v.co = Vector((v.co.z - 0.0075, v.co.y, -v.co.x))
bul.data.update()
bul.shape_key_add(name="Basis"); mk = bul.shape_key_add(name="Mushroom")
random.seed(5)
for v in bul.data.vertices:
    x = v.co.x; rr = math.hypot(v.co.y, v.co.z)
    if x > -0.002:
        t = (x + 0.002) / 0.0095
        nx = -0.002 + (x + 0.002) * 0.35
        k = 1.0 + 0.9 * t ** 1.5 * (1 + 0.25 * math.sin(7 * math.atan2(v.co.z, v.co.y)))
        mk.data[v.index].co = Vector((nx, v.co.y * k, v.co.z * k))
bul.location = (-14.0, 0.0, SHOT_Z0)
# shimmer wake (refractive cone) parented to the bullet
wake = lathe("BulletWake", [(0.0, 0.0), (0.0040, 0.004), (0.0042, 0.03), (0.0025, 0.12), (0.0, 0.2)], 24, flat("M_Shimmer", (1, 1, 1), 0.0, trans=1.0, ior=1.01), C_FX, False)
for v in wake.data.vertices: v.co = Vector((-v.co.z - 0.006, v.co.y, -v.co.x))
wake.data.update(); wake.parent = bul

# ------------------------------------------------------------------ the couple
with bpy.data.libraries.load(HUM) as (src, dst): dst.collections = [c for c in src.collections if c in ("Woman", "Fiance")]
for c in dst.collections: sc.collection.children.link(c)

# ------------------------------------------------------------------ lights (room)
def area(name, loc, rot, size, energy, color, coll=C_ROOM, shape="RECTANGLE", sy=None):
    l = bpy.data.lights.new(name, "AREA"); l.shape = shape; l.size = size; l.size_y = sy or size; l.energy = energy; l.color = color
    o = bpy.data.objects.new(name, l); o.location = loc; o.rotation_euler = rot; coll.objects.link(o); return o
pend = bpy.data.lights.new("PendantLight", "POINT"); pend.energy = 260; pend.color = (1.0, 0.78, 0.55); pend.shadow_soft_size = 0.12
o = bpy.data.objects.new("PendantLight", pend); o.location = (TABLE_C.x, TABLE_C.y, H - 1.0); C_ROOM.objects.link(o)
area("CeilingFill", (3.4, 0.0, H - 0.05), (0, 0, 0), 3.5, 420, (1.0, 0.88, 0.76))
area("SofaLamp", (5.8, -2.6, 1.6), (R_(70), 0, R_(150)), 0.6, 120, (1.0, 0.75, 0.5))
area("WallWash", (4.5, -2.6, 2.4), (R_(-40), 0, 0), 1.2, 120, (1.0, 0.85, 0.7))
area("KeyFace", (3.2, -1.8, 1.9), (R_(60), 0, R_(-60)), 1.0, 160, (1.0, 0.9, 0.8))
area("WindowDusk1", (0.1, -1.22, 1.5), (0, R_(90), 0), 1.0, 60, (0.55, 0.65, 1.0), sy=1.3)
area("WindowDusk2", (0.1, 1.95, 1.5), (0, R_(90), 0), 1.0, 60, (0.55, 0.65, 1.0), sy=1.3)
area("KitchenGlow", (3.0, r["y1"] + 1.5, H - 0.05), (0, 0, 0), 1.5, 150, (1.0, 0.85, 0.65))
area("HallGlowL", (r["x1"] + 0.8, 0.0, H - 0.05), (0, 0, 0), 1.0, 60, (1.0, 0.8, 0.6))
sun = bpy.data.lights.new("SunDusk", "SUN"); sun.energy = 1.2; sun.color = (1.0, 0.55, 0.3); sun.angle = R_(3)
o = bpy.data.objects.new("SunDusk", sun); o.rotation_euler = (R_(82), 0, R_(-120)); C_EXT.objects.link(o)
for o in bpy.data.objects:
    if o.type == "MESH" and o.data.materials and o.data.materials[0] and o.data.materials[0].name in ("M_Glass", "M_Drop", "M_Shimmer", "M_Water", "M_Ice", "M_LampGlass", "M_Flame", "M_StreetGlow"):
        o.visible_shadow = False
print("BUILT", len(bpy.data.objects), "objects; HOLE_LAYERS", len(HOLE_LAYERS))
sc["hole_layers"] = [o.name for o in HOLE_LAYERS if True]
bpy.ops.wm.save_as_mainfile(filepath=OUT)
