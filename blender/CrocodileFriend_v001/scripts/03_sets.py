"""Sets: HOME (log house + pond + viewing deck + garden) at (0,0); RIVER bank at (-45,0); HALL interior at (45,0).
blender -b work/people.blend -P 03_sets.py -- work/sets.blend   (appends croc from work/croc.blend)"""
import bpy, sys, os, math, random
import numpy as np
from mathutils import Vector, Matrix
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); A = os.path.join(HERE, "assets")
OUT = sys.argv[-1]; sc = bpy.context.scene; random.seed(7)
def coll(n):
    c = bpy.data.collections.get(n) or bpy.data.collections.new(n)
    if c.name not in sc.collection.children: sc.collection.children.link(c)
    return c
def link(o, c):
    for u in list(o.users_collection): u.objects.unlink(o)
    c.objects.link(o)
def imp(fn, name, c, keep=None):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=os.path.join(A, fn))
    new = [o for o in bpy.data.objects if o not in before]
    bpy.context.view_layer.update()
    ms = [o for o in new if o.type == 'MESH']
    if keep:
        ms2 = [o for o in ms if keep(o)]
        for o in ms:
            if o not in ms2: bpy.data.objects.remove(o)
        ms = ms2
    for o in ms:
        mw = o.matrix_world.copy(); o.parent = None; o.matrix_world = mw
    for o in [o for o in new if o in ms or True]:
        try:
            if o.type != 'MESH': bpy.data.objects.remove(o)
        except ReferenceError: pass
    for o in bpy.context.selected_objects: o.select_set(False)
    for o in ms: o.select_set(True)
    bpy.context.view_layer.objects.active = ms[0]
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    if len(ms) > 1: bpy.ops.object.join()
    o = bpy.context.view_layer.objects.active; o.name = name
    # origin: bottom centre
    vs = np.array([tuple(v.co) for v in o.data.vertices]); mn, mx = vs.min(0), vs.max(0)
    off = Vector(((mn[0]+mx[0])/2, (mn[1]+mx[1])/2, mn[2]))
    o.data.transform(Matrix.Translation(-off)); o.location = (0, 0, 0)
    link(o, c); o["size"] = list(mx - mn)
    return o
def fit(o, height=None, length=None):
    s = o["size"]; f = height / s[2] if height else length / max(s[0], s[1])
    o.scale = (f, f, f); return f
def inst(o, loc, rot=0, scale=None, c=None):
    n = o.copy(); (c or o.users_collection[0]).objects.link(n); n.location = loc; n.rotation_euler = (0, 0, rot)
    if scale: n.scale = tuple(v * scale for v in o.scale)
    return n
def soften(o, sat=1.15, rough=0.45):
    for m in o.data.materials:
        if not m or not m.use_nodes: continue
        for n in m.node_tree.nodes:
            if n.type == 'BSDF_PRINCIPLED':
                n.inputs["Roughness"].default_value = max(rough, n.inputs["Roughness"].default_value)
            if n.type == 'NORMAL_MAP': n.inputs["Strength"].default_value = 0.35
def pbr(name, folder, scale=1.0, tint=None, value=1.0, sat=1.1):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; N = nt.nodes; L = nt.links; b = N["Principled BSDF"]
    D = os.path.join(A, "ph", folder, "textures"); fs = os.listdir(D)
    tc = N.new("ShaderNodeTexCoord"); mp = N.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (scale,)*3
    L.new(tc.outputs["Object"], mp.inputs[0])
    def tex(key, nc=False):
        f = [x for x in fs if key in x][0]; t = N.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(os.path.join(D, f))
        if nc: t.image.colorspace_settings.name = "Non-Color"
        L.new(mp.outputs[0], t.inputs[0]); return t
    d = tex("diff"); hs = N.new("ShaderNodeHueSaturation"); hs.inputs["Saturation"].default_value = sat; hs.inputs["Value"].default_value = value
    L.new(d.outputs[0], hs.inputs["Color"])
    if tint:
        mx = N.new("ShaderNodeMix"); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs[0].default_value = 1
        L.new(hs.outputs[0], mx.inputs[6]); mx.inputs[7].default_value = tint + (1,); L.new(mx.outputs[2], b.inputs["Base Color"])
    else: L.new(hs.outputs[0], b.inputs["Base Color"])
    r = tex("rough", True); L.new(r.outputs[0], b.inputs["Roughness"])
    n = tex("nor_gl", True); nm = N.new("ShaderNodeNormalMap"); nm.inputs["Strength"].default_value = 0.35
    L.new(n.outputs[0], nm.inputs["Color"]); L.new(nm.outputs[0], b.inputs["Normal"])
    return m
def flat(name, rgb, rough=0.5, spec=0.3):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = rgb + (1,); b.inputs["Roughness"].default_value = rough; b.inputs["Specular IOR Level"].default_value = spec
    return m
def box(name, size, loc, mat, c, bevel=0.01):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc); o = bpy.context.object; o.name = name; o.scale = size
    bpy.ops.object.transform_apply(scale=True)
    if bevel: bv = o.modifiers.new("b", 'BEVEL'); bv.width = bevel; bv.segments = 2
    o.data.materials.append(mat); link(o, c); return o
# ---------------------------------------------------------------- world / light
w = bpy.data.worlds.new("Sky"); sc.world = w; w.use_nodes = True; nt = w.node_tree
env = nt.nodes.new("ShaderNodeTexEnvironment"); env.image = bpy.data.images.load(os.path.join(A, "ph", "hdri", "kloofendal_48d_partly_cloudy_puresky_1k.hdr"))
nt.links.new(env.outputs[0], nt.nodes["Background"].inputs[0]); nt.nodes["Background"].inputs[1].default_value = 1.0
sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", "SUN")); sc.collection.objects.link(sun)
sun.data.energy = 3.5; sun.data.angle = math.radians(3); sun.rotation_euler = (math.radians(42), 0, math.radians(35)); sun.data.color = (1, 0.96, 0.9)
# ---------------------------------------------------------------- terrain
CH = coll("SET_HOME"); CR = coll("SET_RIVER"); CI = coll("SET_HALL")
grass = pbr("Grass", "aerial_grass_rock", 0.25, (0.75, 1.0, 0.55), 1.15, 1.3)
sand = pbr("Sand", "coast_sand_01", 0.4, (1.0, 0.95, 0.82), 1.2, 1.0)
def sstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1); return t * t * (3 - 2 * t)
def terrain(name, x0, x1, y0, y1, res, hfun, sandfun, c):
    nx, ny = int((x1-x0)/res)+1, int((y1-y0)/res)+1
    X, Y = np.meshgrid(np.linspace(x0, x1, nx), np.linspace(y0, y1, ny)); Z = hfun(X, Y)
    me = bpy.data.meshes.new(name); verts = np.stack([X.ravel(), Y.ravel(), Z.ravel()], 1)
    faces = [(j*nx+i, j*nx+i+1, (j+1)*nx+i+1, (j+1)*nx+i) for j in range(ny-1) for i in range(nx-1)]
    me.from_pydata(verts.tolist(), [], faces); me.update()
    for p in me.polygons: p.use_smooth = True
    o = bpy.data.objects.new(name, me); c.objects.link(o)
    S = sandfun(X, Y, Z).ravel()
    me.materials.append(grass); me.materials.append(sand)
    for p in me.polygons: p.material_index = 1 if np.mean([S[v] for v in p.vertices]) > 0.5 else 0
    return o
rng = np.random.default_rng(3)
def noise(X, Y, a=0.04): return a * (np.sin(X*0.9+1.3)*np.cos(Y*0.7) + 0.5*np.sin(X*2.1+Y*1.7))
POND = (0.0, 10.0, 8.0, 5.5)
def pond_d(X, Y): return np.sqrt(((X-POND[0])/POND[2])**2 + ((Y-POND[1])/POND[3])**2)
def h_home(X, Y): return noise(X, Y) - 1.0 * sstep(1.12, 0.72, pond_d(X, Y))
def s_home(X, Y, Z): return (pond_d(X, Y) < 1.08).astype(float)
terrain("Ground_Home", -30, 30, -22, 30, 0.35, h_home, s_home, CH)
RX = -45.0
def h_riv(X, Y): return noise(X, Y, 0.03) + 0.12*(X-RX) * (X > RX) - 1.3 * sstep(RX-2, RX-6, X)
def s_riv(X, Y, Z): return (X < RX + 9).astype(float)
terrain("Ground_River", RX-14, RX+14, -20, 22, 0.35, h_riv, s_riv, CR)
WATER_Z = -0.22
wat = bpy.data.materials.new("Water"); wat.use_nodes = True; N = wat.node_tree.nodes; Lk = wat.node_tree.links; b = N["Principled BSDF"]
b.inputs["Base Color"].default_value = (0.045, 0.085, 0.05, 1); b.inputs["Roughness"].default_value = 0.04
b.inputs["Specular IOR Level"].default_value = 0.35; b.inputs["Alpha"].default_value = 0.92
nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 3.0; bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.08
Lk.new(nz.outputs["Fac"], bp.inputs["Height"]); Lk.new(bp.outputs[0], b.inputs["Normal"])
for nm, loc, size, c in (("Water_Pond", (0, 10, WATER_Z), (18, 13), CH), ("Water_River", (RX-8, 0, WATER_Z), (14, 44), CR)):
    bpy.ops.mesh.primitive_plane_add(size=1, location=loc); o = bpy.context.object; o.name = nm; o.scale = (size[0], size[1], 1)
    bpy.ops.object.transform_apply(scale=True); o.data.materials.append(wat); link(o, c)
# ---------------------------------------------------------------- house
def keep_house(o):
    if o.name.startswith(("Box311", "Box571")): return False
    bb = [o.matrix_world @ Vector(cc) for cc in o.bound_box]; cx = sum(p.x for p in bb)/8; cy = sum(p.y for p in bb)/8
    return abs(cx) < 2.2 and -3.0 < cy < 2.3
house = imp("house2.glb", "House", CH, keep_house); soften(house)
fit(house, height=5.6); house.location = (0, -4.5, 0.02)
HS = house.scale[0]
# ---------------------------------------------------------------- vegetation
palms = [imp(f, n, CH) for f, n in (("palm1.glb", "Palm1"), ("palm2.glb", "Palm2"), ("palm3.glb", "Palm3"))]
fit(palms[0], height=7); fit(palms[1], height=8); fit(palms[2], height=3.5)
plants = [imp(f, n, CH) for f, n in (("plant1.glb", "Plant1"), ("plant2.glb", "Plant2"))]
fit(plants[0], height=1.2); fit(plants[1], height=1.0)
for o in palms + plants: soften(o)
for p, loc, r in ((palms[0], (-10, 2, 0), 0.3), (palms[1], (11, 3, 0), 1.0), (palms[0], (-12, 16, 0), 2.0), (palms[1], (10, 18, 0), 0.5),
                  (palms[2], (-6, -1, 0), 0.2), (palms[2], (7, 0, 0), 1.2), (palms[0], (-18, -8, 0), 0.7), (palms[1], (16, -6, 0), 2.4),
                  (palms[0], (4, 23, 0), 1.1), (palms[1], (-4, 25, 0), 0.4)):
    inst(p, loc, r)
for i in range(40):
    ang = random.uniform(0, 2*math.pi); rr = random.uniform(1.25, 1.7)
    x = POND[0] + POND[2]*rr*math.cos(ang); y = POND[1] + POND[3]*rr*math.sin(ang)
    if -6 < x < 6 and y < 6: continue           # keep the house side / walking strip open
    if -5 < x < 5 and y > 15: continue         # deck
    inst(random.choice(plants), (x, y, 0), random.uniform(0, 6), random.uniform(0.8, 1.5))
for o in palms + plants: o.hide_render = o.hide_viewport = True; o.location.z = -50   # masters hidden
# ---------------------------------------------------------------- viewing deck (north shore) + railing
wood = pbr("DeckWood", "wood_floor_deck", 0.5, (1.0, 0.9, 0.8), 1.1)
for i in range(14):
    box("DeckPlank%02d" % i, (8.0, 0.24, 0.05), (0, 15.6 + i*0.26, 0.45), wood, CH, 0.004)
for x in (-3.9, -1.3, 1.3, 3.9):
    for y in (15.6, 19.0): box("DeckPost", (0.14, 0.14, 1.6), (x, y, -0.15), wood, CH, 0.01)
for x in (-3.9, -2.6, -1.3, 0, 1.3, 2.6, 3.9): box("RailPost", (0.09, 0.09, 1.0), (x, 15.55, 0.95), wood, CH, 0.008)
box("RailTop", (8.0, 0.1, 0.07), (0, 15.55, 1.45), wood, CH, 0.01)
box("RailMid", (8.0, 0.05, 0.06), (0, 15.55, 1.0), wood, CH, 0.008)
# logo sign on the deck rail (placement 2)
def logo_mat(name, png):
    m = bpy.data.materials.new(name); m.use_nodes = True; N = m.node_tree.nodes; Lk = m.node_tree.links; b = N["Principled BSDF"]
    t = N.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(os.path.join(HERE, "..", "assets", "brand", png)); t.extension = 'CLIP'
    bg = N.new("ShaderNodeMix"); bg.data_type = 'RGBA'; bg.inputs[6].default_value = (0.93, 0.85, 0.62, 1)
    Lk.new(t.outputs["Alpha"], bg.inputs[0]); Lk.new(t.outputs["Color"], bg.inputs[7]); Lk.new(bg.outputs[2], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.6; return m
sign = box("LogoSign_Board", (1.6, 0.04, 0.72), (2.0, 15.5, 1.12), wood, CH, 0.01)
bpy.ops.mesh.primitive_plane_add(size=1, location=(2.0, 15.475, 1.12), rotation=(math.radians(90), 0, 0)); lg = bpy.context.object
lg.name = "LogoSign_Face"; lg.scale = (1.45, 1.45 * 414 / 967, 1); bpy.ops.object.transform_apply(scale=True)
lg.data.materials.append(logo_mat("LogoSign", "DaKrasFilms_logo_dark.png")); link(lg, CH)
# ---------------------------------------------------------------- porch props: crate with logo (placement 1), bucket, meat
crate = imp("crate.glb", "Crate", CH); soften(crate); fit(crate, height=0.5)
bucket = imp("bucket.glb", "Bucket", CH, lambda o: "Icosphere" not in o.name); soften(bucket); fit(bucket, height=0.42)
meat = imp("meat.glb", "Meat", CH); soften(meat); fit(meat, length=0.2)
meat2 = inst(meat, (0, 0, 0)); meat2.name = "MeatInBucket"
# ---------------------------------------------------------------- RIVER bank dressing
for p, loc, r in ((palms[0], (RX+6, 6, 0.7), 0.4), (palms[1], (RX+9, -5, 1.0), 2.0), (palms[0], (RX+12, 12, 1.4), 1.0),
                  (palms[2], (RX+4, -9, 0.4), 0.3), (palms[1], (RX+7, 16, 0.8), 1.7), (palms[2], (RX+3, 12, 0.3), 2.2)):
    o = inst(p, loc, r, c=CR); o.hide_render = o.hide_viewport = False
for i in range(18):
    o = inst(random.choice(plants), (RX + random.uniform(5, 13), random.uniform(-18, 20), 0), random.uniform(0, 6), random.uniform(0.9, 1.6), c=CR)
    o.location.z = 0.12*(o.location.x-RX) - 0.05; o.hide_render = o.hide_viewport = False
for o in CH.objects:
    if o.name.startswith(("Palm", "Plant")) and "." in o.name: o.hide_render = o.hide_viewport = False
# ---------------------------------------------------------------- HALL interior (45, 0): 10 x 9 m room
HX = 45.0
floorm = pbr("HallFloor", "wood_floor_deck", 0.6, (1.0, 0.85, 0.7), 1.05)
wallm = pbr("HallWall", "plastered_wall_02", 0.5, (0.85, 0.95, 0.9), 1.1)
box("Hall_Floor", (10, 9, 0.1), (HX, 0, -0.05), floorm, CI, 0)
box("Hall_WallBack", (10, 0.2, 4), (HX, 4.5, 2), wallm, CI, 0)
box("Hall_WallL", (0.2, 9, 4), (HX-5, 0, 2), wallm, CI, 0)
box("Hall_WallR", (0.2, 9, 4), (HX+5, 0, 2), wallm, CI, 0)
box("Hall_WallFront", (10, 0.2, 4), (HX, -4.5, 2), wallm, CI, 0)
box("Hall_Ceiling", (10, 9, 0.1), (HX, 0, 4.05), flat("Ceil", (0.9, 0.88, 0.82)), CI, 0)
trim = flat("Trim", (0.15, 0.42, 0.38), 0.4)
glassm = flat("WindowView", (0.55, 0.8, 0.6), 0.3); glassm.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].default_value = 1.2
glassm.node_tree.nodes["Principled BSDF"].inputs["Emission Color"].default_value = (0.6, 0.85, 0.65, 1)
for x in (HX-3, HX+3):
    box("Hall_Window", (1.8, 0.05, 1.6), (x, 4.38, 2.1), glassm, CI, 0)
    box("Hall_WinFrameT", (2.0, 0.12, 0.1), (x, 4.36, 2.95), trim, CI, 0.01); box("Hall_WinFrameB", (2.0, 0.12, 0.1), (x, 4.36, 1.25), trim, CI, 0.01)
    box("Hall_WinFrameL", (0.1, 0.12, 1.8), (x-0.95, 4.36, 2.1), trim, CI, 0.01); box("Hall_WinFrameR", (0.1, 0.12, 1.8), (x+0.95, 4.36, 2.1), trim, CI, 0.01)
    box("Hall_WinMull", (0.06, 0.1, 1.6), (x, 4.34, 2.1), trim, CI, 0.005)
box("Hall_Skirting", (10, 0.06, 0.15), (HX, 4.38, 0.075), trim, CI, 0.005)
# easel + portrait painting (plain picture, no text) + flowers
easel = imp("easel.glb", "Easel", CI); soften(easel); fit(easel, height=1.85); easel.location = (HX+1.2, 3.2, 0); easel.rotation_euler = (0, 0, math.radians(90))
frame = imp("frame.glb", "PortraitFrame", CI); fit(frame, height=1.15)
flowers = imp("flowers.glb", "Flowers", CI); soften(flowers); fit(flowers, height=0.7)
vase = imp("vase.glb", "Vase", CI); soften(vase); fit(vase, height=0.8)
for o, loc in ((flowers, (HX+0.3, 3.4, 0)), (flowers, (HX+2.1, 3.4, 0)), (vase, (HX-0.4, 3.6, 0)), (vase, (HX+2.8, 3.6, 0)), (flowers, (HX+1.2, 2.6, 0))):
    inst(o, loc, random.uniform(0, 6))
flowers.location.z = -50; vase.location.z = -50; flowers.hide_render = vase.hide_render = True
bench = imp("bench.glb", "Bench", CI); soften(bench); fit(bench, length=1.8)
for i, (x, y) in enumerate(((HX-1.8, -0.2), (HX+1.0, -0.2), (HX-1.8, -1.6), (HX+1.0, -1.6))):
    inst(bench, (x, y, 0), math.radians(180))
bench.location.z = -50; bench.hide_render = True
lamp = bpy.data.objects.new("HallLight", bpy.data.lights.new("HallLight", "AREA")); CI.objects.link(lamp)
lamp.data.energy = 900; lamp.data.size = 6; lamp.location = (HX, 0, 3.9); lamp.data.color = (1, 0.95, 0.85)
# croc + porch logo crate
with bpy.data.libraries.load(os.path.join(HERE, "work", "croc.blend")) as (src, dst): dst.objects = ["Croc", "Croc_body"]
CC = coll("CROC")
for o in dst.objects: CC.objects.link(o)
for o in bpy.data.objects:
    if o.type == 'ARMATURE' and o.name != "Croc":
        link(o, coll("PEOPLE"))
        for ch in o.children: link(ch, coll("PEOPLE"))
crate.location = (-2.2, -6.4, 0.75 + 0.02)  # on the porch (porch deck height checked in 04)
for o in list(bpy.data.objects):
    if o.name.startswith("Icosphere"): print("REMOVE stray", o.name); bpy.data.objects.remove(o)
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("HOUSE scale", HS, "dims", house.dimensions[:])
