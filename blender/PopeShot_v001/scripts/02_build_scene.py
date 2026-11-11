"""PopeShot sets + assets. blender -b --python 02_build_scene.py -- <humans.blend> <asset_dir> <out.blend>
asset_dir holds glb/*.glb and ph/<id>/textures (Poly Haven) and ph/hdri."""
import sys, os, math, random, bpy, bmesh
from mathutils import Vector, Matrix
a = sys.argv[sys.argv.index("--") + 1:]
HUM, AS, OUT = a
R_ = math.radians
random.seed(31)
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'
sc.render.resolution_x, sc.render.resolution_y = 1080, 1920
sc.render.fps = 60; sc.frame_start, sc.frame_end = 1, 1620
sc.cycles.samples = 48; sc.cycles.adaptive_threshold = 0.05; sc.cycles.use_denoising = True; sc.cycles.denoiser = 'OPENIMAGEDENOISE'
sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Medium High Contrast'
sc.render.use_motion_blur = True; sc.render.motion_blur_shutter = 0.5
sc.cycles.max_bounces = 6; sc.cycles.transparent_max_bounces = 16

def col(name):
    c = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if c.name not in sc.collection.children: sc.collection.children.link(c)
    return c
def link(o, c):
    for x in list(o.users_collection): x.objects.unlink(o)
    col(c).objects.link(o); return o

# ------------------------------------------------------------------ materials
IMG = {}
def img(path, nonc=False):
    if path not in IMG:
        im = bpy.data.images.load(path, check_existing=True)
        if nonc: im.colorspace_settings.name = 'Non-Color'
        IMG[path] = im
    return IMG[path]
def texfile(tid, kind):
    d = os.path.join(AS, "ph", tid, "textures")
    for f in os.listdir(d):
        if "_%s_" % kind in f: return os.path.join(d, f)
def pbr(name, tid, scale=1.0, tint=(1, 1, 1), rough_mul=1.0, bump=0.3, spec=0.5):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; n, l = nt.nodes, nt.links
    bs = n["Principled BSDF"]
    tc = n.new('ShaderNodeTexCoord'); mp = n.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (scale,) * 3
    l.new(tc.outputs['Object'], mp.inputs['Vector'])
    def T(kind, nonc):
        p = texfile(tid, kind)
        if not p: return None
        t = n.new('ShaderNodeTexImage'); t.image = img(p, nonc); t.projection = 'BOX'; t.projection_blend = 0.25
        l.new(mp.outputs['Vector'], t.inputs['Vector']); return t
    d = T("diff", False) or T("col", False); r = T("rough", True); nr = T("nor_gl", True)
    mx = n.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs['Factor'].default_value = 1
    mx.inputs['B'].default_value = tuple(tint) + (1,)
    l.new(d.outputs['Color'], mx.inputs['A']); l.new(mx.outputs['Result'], bs.inputs['Base Color'])
    if r:
        mm = n.new('ShaderNodeMath'); mm.operation = 'MULTIPLY'; mm.inputs[1].default_value = rough_mul
        l.new(r.outputs['Color'], mm.inputs[0]); l.new(mm.outputs[0], bs.inputs['Roughness'])
    if nr:
        nm = n.new('ShaderNodeNormalMap'); nm.inputs['Strength'].default_value = 1.0
        l.new(nr.outputs['Color'], nm.inputs['Color']); l.new(nm.outputs['Normal'], bs.inputs['Normal'])
    bs.inputs['Specular IOR Level'].default_value = spec
    return m
def simple(name, color, rough=0.5, metal=0.0, emit=None, estr=0.0, noise_bump=0.0, nscale=40):
    m = bpy.data.materials.new(name); m.use_nodes = True
    bs = m.node_tree.nodes["Principled BSDF"]; n, l = m.node_tree.nodes, m.node_tree.links
    bs.inputs['Base Color'].default_value = tuple(color) + (1,); bs.inputs['Roughness'].default_value = rough
    bs.inputs['Metallic'].default_value = metal
    if emit: bs.inputs['Emission Color'].default_value = tuple(emit) + (1,); bs.inputs['Emission Strength'].default_value = estr
    if noise_bump:
        nz = n.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = nscale; nz.inputs['Detail'].default_value = 10
        bp = n.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = noise_bump
        l.new(nz.outputs['Fac'], bp.inputs['Height']); l.new(bp.outputs['Normal'], bs.inputs['Normal'])
        # grime variation in colour too
        mr = n.new('ShaderNodeMapRange'); mr.inputs['To Min'].default_value = 0.8; mr.inputs['To Max'].default_value = 1.1
        mx = n.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs['Factor'].default_value = 1
        mx.inputs['A'].default_value = tuple(color) + (1,)
        l.new(nz.outputs['Fac'], mr.inputs['Value']); l.new(mr.outputs['Result'], mx.inputs['B']); l.new(mx.outputs['Result'], bs.inputs['Base Color'])
    return m

M = dict(
    cobble=pbr("Cobble", "cobblestone_floor_08", 0.35, (0.95, 0.9, 0.82)),
    trav=pbr("Travertine", "rough_plaster_03", 1.4, (1.0, 0.93, 0.8)),
    plaster=pbr("Plaster", "plastered_wall_04", 0.5, (0.95, 0.88, 0.75)),
    brick=pbr("Brick", "castle_brick_07", 0.4, (1, 0.95, 0.9)),
    whitepl=pbr("WhitePlaster", "white_plaster_02", 0.6, (0.95, 0.95, 0.93)),
    marble=pbr("Marble", "marble_01", 1.2, (1, 0.98, 0.95), 0.4, spec=0.6),
    concrete=pbr("Concrete", "concrete_wall_008", 0.6, (0.75, 0.72, 0.68)),
    tiles=pbr("Tiles", "floor_tiles_06", 0.8, (0.85, 0.95, 0.95)),
    wood=pbr("Wood", "wood_floor_deck", 1.0, (0.7, 0.5, 0.35)),
    linen=pbr("WhiteWool", "rough_linen", 6.0, (1.25, 1.22, 1.15), 1.0, spec=0.3),
    drape=pbr("SurgDrape", "cotton_jersey", 5.0, (0.25, 0.5, 0.48), 1.0, spec=0.3),
    fabric=pbr("Banner", "fabric_pattern_07", 3.0, (0.8, 0.75, 0.6)),
    rust=pbr("RustMetal", "rusty_metal_02", 2.0, (0.6, 0.6, 0.6)),
    plate=pbr("MetalPlate", "metal_plate", 2.0, (0.8, 0.82, 0.85)),
    shutter=pbr("PaintedMetal", "painted_metal_shutter", 1.0, (0.9, 0.9, 0.9)),
)
M["plate"].node_tree.nodes["Principled BSDF"].inputs['Metallic'].default_value = 0.8
M["gold"] = simple("Gold", (1.0, 0.72, 0.32), 0.25, 1.0, noise_bump=0.08, nscale=120)
M["brass"] = simple("Brass", (0.8, 0.58, 0.3), 0.35, 1.0, noise_bump=0.1)
M["bullet"] = simple("BulletLead", (0.55, 0.52, 0.48), 0.35, 1.0, noise_bump=0.15, nscale=200)

# ------------------------------------------------------------------ geometry helpers
def box(name, size, loc, mat, c="Set", bevel=0.0, rot=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=(0, 0, rot)); o = bpy.context.object; o.name = name
    o.scale = size; bpy.ops.object.transform_apply(scale=True)
    o.data.materials.append(mat)
    if bevel:
        b = o.modifiers.new("bev", 'BEVEL'); b.width = bevel; b.segments = 2
    return link(o, c)
def room(name, x0, x1, y0, y1, z0, z1, mat, floor=None, ceil=None, drop=(), c="Set"):
    """inward-facing room shell with thickness; drop = faces to remove: 'ymin','ymax','xmin','xmax','zmin','zmax'"""
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co = Vector(((x0 if v.co.x < 0 else x1), (y0 if v.co.y < 0 else y1), (z0 if v.co.z < 0 else z1)))
    bm.normal_update()
    for f in list(bm.faces):
        nrm = f.normal; key = ("x" if abs(nrm.x) > 0.5 else "y" if abs(nrm.y) > 0.5 else "z") + ("max" if (nrm.x + nrm.y + nrm.z) > 0 else "min")
        f.material_index = 1 if key == "zmin" else 2 if key == "zmax" else 0
        if key in drop: bm.faces.remove(f)
    bmesh.ops.reverse_faces(bm, faces=bm.faces[:])
    bm.to_mesh(me); o = bpy.data.objects.new(name, me)
    for mm in (mat, floor or mat, ceil or mat): me.materials.append(mm)
    s = o.modifiers.new("thick", 'SOLIDIFY'); s.thickness = 0.25; s.offset = -1
    return link(o, c)
def cut(o, cutter_size, cutter_loc):
    bpy.ops.mesh.primitive_cube_add(size=1, location=cutter_loc); k = bpy.context.object; k.scale = cutter_size
    bm_ = o.modifiers.new("cut", 'BOOLEAN'); bm_.object = k; bm_.operation = 'DIFFERENCE'; bm_.solver = 'EXACT'
    bpy.context.view_layer.objects.active = o
    for md in list(o.modifiers):
        bpy.ops.object.modifier_apply(modifier=md.name)
    bpy.data.objects.remove(k, do_unlink=True)
def lathe(name, prof, mat, seg=32, loc=(0, 0, 0), flutes=0, fdepth=0.0, c="Set"):
    """prof = [(r, z)...] bottom->top; flutes = vertical fluting count"""
    me = bpy.data.meshes.new(name); bm = bmesh.new(); rings = []
    for (r, z) in prof:
        ring = []
        for i in range(seg):
            t = 2 * math.pi * i / seg
            rr = r * (1 - fdepth * (0.5 + 0.5 * math.cos(flutes * t))) if flutes else r
            ring.append(bm.verts.new((rr * math.cos(t), rr * math.sin(t), z)))
        rings.append(ring)
    for r0, r1 in zip(rings, rings[1:]):
        for i in range(seg): bm.faces.new((r0[i], r0[(i + 1) % seg], r1[(i + 1) % seg], r1[i]))
    bm.faces.new(rings[-1]); bm.faces.new(list(reversed(rings[0])))
    bm.to_mesh(me); o = bpy.data.objects.new(name, me); o.location = loc; me.materials.append(mat)
    for p in me.polygons: p.use_smooth = True
    return link(o, c)
def inst(src, name, loc, rot=0.0, scale=1.0, c="Set"):
    o = src.copy(); o.name = name; o.location = loc; o.rotation_euler = (0, 0, rot); o.scale = (scale,) * 3
    return link(o, c)

def imp(name, target, loc=(0, 0, 0), rot=0.0, axis="z", c="Props", decimate=None):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=os.path.join(AS, "glb", name + ".glb"))
    new = [o for o in bpy.data.objects if o not in before]
    newn = [o.name for o in new]
    meshes = [o for o in new if o.type == 'MESH']
    bpy.ops.object.select_all(action='DESELECT')
    for o in meshes:
        o.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
    if len(meshes) > 1: bpy.ops.object.join()
    o = bpy.context.view_layer.objects.active
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    for xn in newn:
        x = bpy.data.objects.get(xn)
        if x and x != o: bpy.data.objects.remove(x, do_unlink=True)
    o.name = name
    vs = [v.co for v in o.data.vertices]
    mn = Vector([min(v[i] for v in vs) for i in range(3)]); mx = Vector([max(v[i] for v in vs) for i in range(3)])
    d = mx - mn
    ref = d.z if axis == "z" else max(d)
    s = target / ref
    o.data.transform(Matrix.Scale(s, 4) @ Matrix.Translation(-Vector(((mn.x + mx.x) / 2, (mn.y + mx.y) / 2, mn.z))))
    o.location = loc; o.rotation_euler = (0, 0, rot)
    if decimate:
        dm = o.modifiers.new("dec", 'DECIMATE'); dm.ratio = decimate
    print("IMP", name, tuple(round(x * s, 3) for x in d), len(o.data.polygons))
    return link(o, c)

# ------------------------------------------------------------------ world
wd = bpy.data.worlds.new("Sky"); sc.world = wd; wd.use_nodes = True
wn, wl = wd.node_tree.nodes, wd.node_tree.links
env = wn.new('ShaderNodeTexEnvironment'); env.image = bpy.data.images.load(os.path.join(AS, "ph", "hdri", "kloppenheim_06_puresky_2k.hdr"))
wmap = wn.new('ShaderNodeMapping'); wtc = wn.new('ShaderNodeTexCoord'); wmap.inputs['Rotation'].default_value = (0, 0, R_(140))
wl.new(wtc.outputs['Generated'], wmap.inputs['Vector']); wl.new(wmap.outputs['Vector'], env.inputs['Vector'])
wl.new(env.outputs['Color'], wn["Background"].inputs['Color']); wn["Background"].inputs['Strength'].default_value = 0.9
sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", 'SUN')); link(sun, "Lights")
sun.data.energy = 4.5; sun.data.angle = R_(1.2); sun.data.color = (1.0, 0.95, 0.86)
sun.rotation_euler = (R_(48), 0, R_(-35))

# ------------------------------------------------------------------ SQUARE (origin)
g = bpy.data.meshes.new("Ground"); bm = bmesh.new()
bmesh.ops.create_grid(bm, x_segments=60, y_segments=60, size=80); bm.to_mesh(g)
gro = bpy.data.objects.new("Ground", g); g.materials.append(M["cobble"]); link(gro, "Square")
# fluted Doric column (real proportions), linked copies in 4-deep curved rows like a basilica colonnade
colm = lathe("ColumnSrc", [(0.9, 0), (0.9, 0.35), (0.78, 0.42), (0.72, 0.5), (0.7, 1.0), (0.66, 6.0), (0.6, 10.6), (0.68, 10.75), (0.85, 10.95), (0.95, 11.0), (0.95, 11.35)],
             M["trav"], seg=48, flutes=20, fdepth=0.06, c="Hidden")
cols = []
for side in (-1, 1):
    for ring in range(3):
        R = 34 + ring * 3.2
        for k in range(14):
            t = R_(-62 + k * 7.0)
            x = side * (R * math.cos(t) - 14); y = R * math.sin(t) + 2
            if abs(x) < 12: continue
            cols.append(inst(colm, "Col", (x, y, 0), c="Square"))
    # entablature + balustrade on top of each wing (segments following the arc)
    for k in range(13):
        t0 = R_(-62 + k * 7.0 + 3.5); R = 37.2
        x = side * (R * math.cos(t0) - 14); y = R * math.sin(t0) + 2
        if abs(x) < 12: continue
        box("Entab", (8.6, 5.0, 1.6), (x, y, 12.15), M["trav"], "Square", rot=side * -(math.pi / 2 - t0) if side > 0 else (math.pi / 2 - t0))
        box("Attic", (8.6, 4.4, 1.0), (x, y, 13.4), M["trav"], "Square", rot=side * -(math.pi / 2 - t0) if side > 0 else (math.pi / 2 - t0))
# facade (back, y=36): wall with openings for the theatre window, balcony door and side windows
fac = box("Facade", (70, 1.5, 30), (0, 36, 15), M["trav"], "Square")
cut(fac, (2.2, 3, 2.4), (-8, 36, 9.3))          # theatre window
cut(fac, (2.0, 3, 3.2), (0, 36, 8.6))            # balcony door
for x in (-22, -16, 8, 16, 22):
    cut(fac, (2.0, 3, 2.6), (x, 36, 9.3))
for x in (-22, -16, -8, 0, 8, 16, 22):
    cut(fac, (2.0, 3, 2.6), (x, 36, 17.0))
pil = lathe("PilasterSrc", [(0.8, 0), (0.8, 0.4), (0.62, 0.55), (0.6, 22.0), (0.75, 22.3), (0.85, 22.6)], M["trav"], seg=40, flutes=24, fdepth=0.05, c="Hidden")
for x in (-26, -19, -12, -4, 4, 12, 19, 26):
    inst(pil, "Pilaster", (x, 35.0, 0), c="Square")
box("Cornice", (72, 3.0, 1.4), (0, 35.4, 23.2), M["trav"], "Square", bevel=0.2)
box("CorniceLow", (72, 2.2, 0.6), (0, 35.1, 6.6), M["trav"], "Square", bevel=0.1)
box("Attic2", (60, 1.8, 4.0), (0, 36.0, 26.0), M["trav"], "Square")
box("Steps", (40, 6, 0.6), (0, 32.5, 0.3), M["trav"], "Square"); box("Steps2", (36, 4, 0.6), (0, 33.5, 0.9), M["trav"], "Square")
# window frames / glass in the side windows (dark interiors behind)
glassm = simple("WindowGlass", (0.05, 0.06, 0.07), 0.05, 0.0)
for x in (-22, -16, 8, 16, 22):
    box("Glass", (2.0, 0.05, 2.6), (x, 36.4, 9.3), glassm, "Square")
for x in (-22, -16, -8, 0, 8, 16, 22):
    box("Glass", (2.0, 0.05, 2.6), (x, 36.4, 17.0), glassm, "Square")
# balcony on the facade
box("BalconySlab", (5.0, 2.2, 0.35), (0, 34.2, 6.85), M["trav"], "Square", bevel=0.05)
bal = lathe("BalusterSrc", [(0.07, 0), (0.07, 0.06), (0.05, 0.12), (0.1, 0.35), (0.05, 0.6), (0.06, 0.7), (0.07, 0.76)], M["trav"], seg=16, c="Hidden")
for i in range(15):
    inst(bal, "Baluster", (-2.3 + i * 4.6 / 14, 33.25, 7.02))
for i in range(5):
    inst(bal, "Baluster", (-2.35, 33.4 + i * 0.3, 7.02)); inst(bal, "Baluster", (2.35, 33.4 + i * 0.3, 7.02))
box("Rail", (5.0, 0.22, 0.12), (0, 33.25, 7.84), M["trav"], "Square", bevel=0.03)
# crimson drape hanging from the balcony rail (plain, no emblem)
dr = bpy.data.meshes.new("BalconyDrape"); bm = bmesh.new()
bmesh.ops.create_grid(bm, x_segments=40, y_segments=20, size=1); bm.to_mesh(dr)
dro = bpy.data.objects.new("BalconyDrape", dr); dro.scale = (2.0, 0.8, 1); dro.rotation_euler = (R_(90), 0, 0); dro.location = (0, 33.1, 7.0)
dmat = pbr("Crimson", "fabric_pattern_07", 3.0, (0.55, 0.05, 0.06)); dr.materials.append(dmat); link(dro, "Square")
tx = bpy.data.textures.new("DrapeFold", 'WOOD'); tx.wood_type = 'BANDNOISE'; tx.noise_scale = 0.12; tx.turbulence = 3
dm = dro.modifiers.new("fold", 'DISPLACE'); dm.texture = tx; dm.strength = 0.08
# barriers along the lane (wooden sawhorse barriers), y -18..14, both sides
for side in (-1, 1):
    for k in range(9):
        y = -18 + k * 3.6
        box("BarrierRail", (0.08, 3.4, 0.12), (side * 2.9, y, 0.95), M["wood"], "Square", bevel=0.01)
        box("BarrierRail2", (0.08, 3.4, 0.1), (side * 2.9, y, 0.55), M["wood"], "Square", bevel=0.01)
        for dy in (-1.5, 1.5):
            for dx in (-0.15, 0.15):
                o = box("BarrierLeg", (0.06, 0.07, 1.05), (side * 2.9 + dx, y + dy, 0.5), M["wood"], "Square")
                o.rotation_euler = (0, R_(-9 if dx < 0 else 9), 0)
# flagpoles with plain flags (no emblems) behind the crowd
flagcols = [(0.9, 0.8, 0.2), (0.92, 0.9, 0.85), (0.15, 0.25, 0.6), (0.7, 0.1, 0.1), (0.9, 0.8, 0.2), (0.92, 0.9, 0.85)]
for i, (x, y) in enumerate(((-6.5, -9), (6.8, -4), (-7.2, 2), (7.4, 7), (-6.0, 9), (6.2, -13))):
    lathe("FlagPole", [(0.02, 0), (0.02, 3.6), (0.035, 3.65)], M["wood"], seg=12, loc=(x, y, 0), c="Square")
    fm = bpy.data.meshes.new("Flag"); bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=30, y_segments=18, size=0.5); bm.to_mesh(fm)
    for v in fm.vertices: v.co.x += 0.5
    f = bpy.data.objects.new("Flag%d" % i, fm); f.rotation_euler = (R_(90), 0, R_(random.uniform(0, 360))); f.location = (x, y, 3.1); f.scale = (1.2, 0.8, 1)
    fmat = pbr("FlagCloth%d" % i, "cotton_jersey", 8.0, flagcols[i]); fm.materials.append(fmat); link(f, "Square")
    wv = f.modifiers.new("wave", 'WAVE'); wv.use_normal = True; wv.use_x = False; wv.use_y = False
    wv.height = 0.09; wv.width = 0.5; wv.speed = 0.03 + 0.01 * i; wv.start_position_x = 0.0; wv.falloff_radius = 0
    f.modifiers.new("sub", 'SUBSURF').levels = 1
# distant city behind the colonnades (rooftops so the skyline is not empty)
for i in range(18):
    side = -1 if i % 2 else 1; y = -40 + (i // 2) * 9
    h = random.uniform(14, 22)
    b = box("Building", (random.uniform(8, 12), random.uniform(7, 9), h), (side * random.uniform(52, 58), y, h / 2), random.choice([M["plaster"], M["brick"], M["whitepl"]]), "Square")
dome = lathe("Dome", [(9.0, 0), (9.0, 6), (8.8, 7), (8.0, 10), (6.5, 13), (4.5, 15), (2.0, 16.3), (0.8, 16.6), (0.8, 19), (0.3, 19.5)], M["trav"], seg=64, flutes=16, fdepth=0.02, loc=(0, 52, 26), c="Square")
lathe("DomeDrum", [(10.5, 0), (10.5, 6)], M["trav"], seg=64, flutes=32, fdepth=0.03, loc=(0, 52, 20), c="Square")

# ------------------------------------------------------------------ THEATRE (behind the left window, floor z=7)
room("Theatre", -13, -3, 36.75, 45, 7, 11, M["tiles"], floor=M["concrete"], ceil=M["whitepl"], drop=("ymin",), c="Theatre")
# ------------------------------------------------------------------ CORRIDOR + CELL (behind the balcony door)
room("Corridor", -1.4, 1.4, 36.75, 38.2, 7, 10.4, M["concrete"], drop=("ymin", "ymax"), c="Cell")
cell = room("Cell", -2.5, 2.5, 38.2, 43.0, 7, 10.2, M["plaster"], floor=M["concrete"], ceil=M["concrete"], c="Cell")
cut(cell, (1.2, 1.2, 0.9), (0, 43.0, 9.0))
cut(cell, (1.3, 1.0, 2.3), (0, 38.2, 8.15))      # door opening (the barred door sits in it)
# ------------------------------------------------------------------ SHRINE (behind the cell window)
shr = room("Shrine", -6, 6, 43.3, 56, 7, 16, M["trav"], floor=M["marble"], ceil=M["plaster"], c="Shrine")
cut(shr, (1.2, 1.2, 0.9), (0, 43.3, 9.0))
# apse niche + pedestal for the statue
lathe("Pedestal", [(0.75, 0), (0.75, 0.15), (0.6, 0.25), (0.55, 1.1), (0.68, 1.2), (0.72, 1.3)], M["marble"], seg=48, flutes=12, fdepth=0.04, loc=(0, 53.6, 7), c="Shrine")
for x in (-2.6, 2.6):
    inst(pil, "ShrinePil", (x, 55.6, 7), scale=0.36, c="Shrine")
box("ShrineArch", (6.2, 0.6, 0.8), (0, 55.6, 15.2), M["trav"], "Shrine", bevel=0.1)
box("Altar", (2.4, 0.9, 1.0), (0, 52.0, 7.5), M["marble"], "Shrine", bevel=0.03)
for x in (-3.5, 3.5):
    box("Pew", (2.6, 0.45, 0.45), (x * 0.6, 46.5, 7.45), M["wood"], "Shrine", bevel=0.02)
    box("PewBack", (2.6, 0.06, 0.9), (x * 0.6, 46.25, 7.9), M["wood"], "Shrine", bevel=0.01)

# ------------------------------------------------------------------ ASSETS
jeep = imp("jeep", 1.75, (0, -14, 0), c="Square")
pig = imp("pigeon", 0.28, (0, 0, -50), c="Hidden")
pistol = imp("pistol", 0.19, (0, 0, -50), axis="max", c="Props")
mary = imp("mary", 1.75, (0, 53.6, 8.3), rot=0.0, c="Shrine")
crown = imp("crown", 0.2, (0, 0, -50), axis="max", c="Shrine")
candles = imp("candles", 0.4, (0, 0, -50), axis="max", c="Hidden")
aorta = imp("aorta", 0.42, (0, 0, -50), c="XRay")
spine = imp("spine", 0.62, (0, 0, -50), c="XRay")
skel = imp("skeleton", 1.70, (0, 0, -50), c="XRay", decimate=0.5)
guts = imp("guts", 0.30, (0, 0, -50), c="XRay", decimate=0.6)
hand = imp("handbones", 0.21, (0, 0, -50), axis="max", c="XRay", decimate=0.6)
mon = imp("monitor", 2.0, (-5.0, 43.2, 7), rot=R_(180), c="Theatre")
orl = imp("orlamp", 1.4, (-8, 40.5, 9.6), c="Theatre")
optab = imp("optable", 2.3, (-8.0, 40.5, 7), c="Theatre")
chair = imp("chair", 0.95, (0, 0, -50), c="Hidden")
door = imp("celldoor", 2.2, (0, 38.3, 7), c="Cell")
bars = imp("bars", 1.0, (0, 43.05, 8.55), axis="max", c="Cell")
altar = imp("altar", 1.2, (0, 0, -50), c="Hidden")
# candle racks in the shrine: rows of candle-pack instances on brass stands
for side in (-1, 1):
    for r in range(2):
        st = box("CandleStand", (1.6, 0.5, 0.06), (side * 1.9, 52.2 - r * 0.7, 7.9 + r * 0.15), M["brass"], "Shrine", bevel=0.01)
        box("CandleStandLeg", (0.05, 0.05, 0.9), (side * 1.9, 52.2 - r * 0.7, 7.45), M["brass"], "Shrine")
        for k in range(3):
            inst(candles, "CandleSet", (side * 1.9 - 0.5 + k * 0.5, 52.2 - r * 0.7, 7.93 + r * 0.15), rot=random.uniform(0, 6), c="Shrine")
for o in (chair,):
    pass
c1 = inst(chair, "ChairPope", (-0.45, 40.6, 7), rot=R_(-90), c="Cell"); c2 = inst(chair, "ChairPrisoner", (0.45, 40.6, 7), rot=R_(90), c="Cell")
box("Cot", (0.85, 1.9, 0.08), (-1.9, 41.8, 7.45), M["rust"], "Cell")
box("CotMattress", (0.8, 1.85, 0.12), (-1.9, 41.8, 7.55), M["drape"], "Cell")
for dx in (-0.38, 0.38):
    for dy in (-0.9, 0.9):
        box("CotLeg", (0.04, 0.04, 0.45), (-1.9 + dx, 41.8 + dy, 7.22), M["rust"], "Cell")
lathe("Bucket", [(0.12, 0), (0.14, 0.02), (0.16, 0.3), (0.165, 0.31)], M["rust"], seg=24, loc=(1.9, 42.4, 7), c="Cell")
bpy.data.collections["Hidden"].hide_render = True; bpy.data.collections["Hidden"].hide_viewport = True

# white paint on the jeep (keeps the texture's dirt/wear, removes insignia colour)
for m in jeep.data.materials:
    if not m or not m.node_tree: continue
    nt = m.node_tree; bs = next((x for x in nt.nodes if x.type == 'BSDF_PRINCIPLED'), None)
    if not bs: continue
    src = bs.inputs['Base Color'].links[0].from_socket if bs.inputs['Base Color'].links else None
    if src is None: bs.inputs['Base Color'].default_value = (0.85, 0.85, 0.83, 1); continue
    rgb = nt.nodes.new('ShaderNodeRGBToBW'); nt.links.new(src, rgb.inputs['Color'])
    mr = nt.nodes.new('ShaderNodeMapRange'); mr.inputs['From Min'].default_value = 0.02; mr.inputs['From Max'].default_value = 0.09
    nt.links.new(rgb.outputs['Val'], mr.inputs['Value'])
    mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; nt.links.new(mr.outputs['Result'], mx.inputs['Factor'])
    mx.inputs['A'].default_value = (0.03, 0.03, 0.03, 1); mx.inputs['B'].default_value = (0.82, 0.82, 0.8, 1)
    nt.links.new(mx.outputs['Result'], bs.inputs['Base Color'])

# ------------------------------------------------------------------ HUMANS (append)
with bpy.data.libraries.load(HUM, link=False) as (src, dst):
    dst.collections = [n for n in src.collections if n.startswith("CH_")]
for c in dst.collections:
    sc.collection.children.link(c)
for o in bpy.data.objects:
    if o.type == 'ARMATURE' and o.name in [c.name[3:] for c in dst.collections]:
        o.location = (0, 0, -100 - len(o.name))
sc["asset_dir"] = AS
for m in bpy.data.materials: m.use_fake_user = True
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("SAVED", OUT)
