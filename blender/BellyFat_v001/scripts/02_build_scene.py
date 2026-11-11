"""Supermarket set + macro cross-section set + bullet.  blender -b humans.blend --python 02_build_scene.py -- <out.blend>
All procedural (no external textures except the cleaned MPFB tee). Names: REAL collection (store, people), MACRO collection (tissue)."""
import sys, math, random
import bpy, bmesh
from mathutils import Vector, Matrix, noise

out = sys.argv[sys.argv.index("--") + 1]
random.seed(10)
sc = bpy.context.scene
sc.render.fps = 60; sc.render.fps_base = 1.0
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1080, 1920, 100
sc.frame_start, sc.frame_end = 1, 1290
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'
sc.cycles.samples = 48; sc.cycles.adaptive_threshold = 0.05; sc.cycles.use_denoising = True
sc.view_settings.exposure = -0.6; sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Medium High Contrast'

def coll(name):
    c = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if c.name not in sc.collection.children: sc.collection.children.link(c)
    return c
REAL = coll("REAL"); MACRO = coll("MACRO")
# move humans into REAL
for ob in list(sc.collection.objects):
    REAL.objects.link(ob); sc.collection.objects.unlink(ob)

def link(ob, c): c.objects.link(ob); return ob

# ------------------------------------------------------------------ materials
def mat(name, base=(0.8, 0.8, 0.8), rough=0.5, metal=0.0, emit=None, estr=1.0, sss=0.0, coat=0.0, noise_amt=0.0, nscale=40.0, bump=0.0, alpha=None, transm=0.0):
    m = bpy.data.materials.get(name)
    if m: return m
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; N = nt.nodes; L = nt.links
    b = N["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*base, 1); b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if sss: b.inputs["Subsurface Weight"].default_value = sss; b.inputs["Subsurface Radius"].default_value = (0.8, 0.3, 0.2)
    if coat: b.inputs["Coat Weight"].default_value = coat; b.inputs["Coat Roughness"].default_value = 0.08
    if transm: b.inputs["Transmission Weight"].default_value = transm
    if emit: b.inputs["Emission Color"].default_value = (*emit, 1); b.inputs["Emission Strength"].default_value = estr
    if alpha is not None: b.inputs["Alpha"].default_value = alpha
    if noise_amt or bump:
        tc = N.new("ShaderNodeTexCoord"); nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = nscale
        nz.inputs["Detail"].default_value = 6
        L.new(tc.outputs["Object"], nz.inputs["Vector"])
        if noise_amt:
            mx = N.new("ShaderNodeMix"); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'
            mx.inputs["Factor"].default_value = noise_amt; mx.inputs["A"].default_value = (*base, 1)
            ramp = N.new("ShaderNodeMapRange"); L.new(nz.outputs["Fac"], ramp.inputs["Value"])
            ramp.inputs["To Min"].default_value = 0.6; ramp.inputs["To Max"].default_value = 1.3
            L.new(ramp.outputs["Result"], mx.inputs["B"]); L.new(mx.outputs["Result"], b.inputs["Base Color"])
        if bump:
            bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = bump
            L.new(nz.outputs["Fac"], bp.inputs["Height"]); L.new(bp.outputs["Normal"], b.inputs["Normal"])
    return m

def box_mesh(name, sx, sy, sz):
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts: v.co = Vector((v.co.x * sx, v.co.y * sy, v.co.z * sz))
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free(); return me

def obj(name, me, c, loc=(0, 0, 0), mats=()):
    o = bpy.data.objects.new(name, me); link(o, c); o.location = loc
    for m_ in mats: o.data.materials.append(m_)
    return o

# ------------------------------------------------------------------ store
AISLE_X0, AISLE_X1, SHELF_Y, SHELF_D, SHELF_H = -9.0, 9.0, 1.0, 0.55, 1.95
floor_m = bpy.data.materials.new("M_floor"); floor_m.use_nodes = True
nt = floor_m.node_tree; N = nt.nodes; L = nt.links; b = N["Principled BSDF"]
tc = N.new("ShaderNodeTexCoord"); br = N.new("ShaderNodeTexBrick")
br.inputs["Scale"].default_value = 1.0; br.inputs["Mortar Size"].default_value = 0.004; br.offset = 0.0
br.inputs["Brick Width"].default_value = 0.6; br.inputs["Row Height"].default_value = 0.6
br.inputs["Color1"].default_value = (0.78, 0.76, 0.72, 1); br.inputs["Color2"].default_value = (0.70, 0.69, 0.66, 1)
br.inputs["Mortar"].default_value = (0.35, 0.34, 0.32, 1)
L.new(tc.outputs["Object"], br.inputs["Vector"])
nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 6; nz.inputs["Detail"].default_value = 8
L.new(tc.outputs["Object"], nz.inputs["Vector"])
mx = N.new("ShaderNodeMix"); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs["Factor"].default_value = 0.25
L.new(br.outputs["Color"], mx.inputs["A"]); L.new(nz.outputs["Color"], mx.inputs["B"]); L.new(mx.outputs["Result"], b.inputs["Base Color"])
rr = N.new("ShaderNodeMapRange"); rr.inputs["To Min"].default_value = 0.08; rr.inputs["To Max"].default_value = 0.3
L.new(nz.outputs["Fac"], rr.inputs["Value"]); L.new(rr.outputs["Result"], b.inputs["Roughness"])
bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.15; bp.invert = True
L.new(br.outputs["Fac"], bp.inputs["Height"]); L.new(bp.outputs["Normal"], b.inputs["Normal"])
fl = obj("Floor", box_mesh("Floor", 24, 12, 0.02), REAL, (0, 0, -0.01), [floor_m])
ceil = obj("Ceiling", box_mesh("Ceiling", 24, 12, 0.05), REAL, (0, 0, 3.6), [mat("M_ceiling", (0.85, 0.85, 0.83), 0.8, noise_amt=0.3, nscale=3)])
wallm = mat("M_wall", (0.80, 0.78, 0.72), 0.7, noise_amt=0.4, nscale=2, bump=0.05)
obj("WallBack", box_mesh("WallBack", 0.1, 12, 3.6), REAL, (AISLE_X0 - 1.8, 0, 1.8), [wallm])
obj("WallFront", box_mesh("WallFront", 0.1, 12, 3.6), REAL, (AISLE_X1 + 3.0, 0, 1.8), [wallm])
obj("WallL", box_mesh("WallL", 24, 0.1, 3.6), REAL, (0, 5.0, 1.8), [wallm])
obj("WallR", box_mesh("WallR", 24, 0.1, 3.6), REAL, (0, -5.0, 1.8), [wallm])

# product palette: muted real-world packaging colours (plain, no text)
PAL = [(0.45, 0.04, 0.02), (0.7, 0.38, 0.02), (0.03, 0.12, 0.4), (0.75, 0.72, 0.62), (0.05, 0.22, 0.06), (0.35, 0.14, 0.03),
       (0.55, 0.05, 0.12), (0.03, 0.03, 0.035), (0.8, 0.55, 0.05), (0.08, 0.3, 0.45), (0.6, 0.2, 0.03), (0.22, 0.04, 0.2)]
pmats = []
for i, c in enumerate(PAL):
    m = bpy.data.materials.new("M_pack%02d" % i); m.use_nodes = True
    nt = m.node_tree; N = nt.nodes; L = nt.links; b = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord"); sep = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs["Generated"], sep.inputs["Vector"])
    # band label: a lighter stripe across the middle plus a darker cap; reads as printed packaging without any text
    band = N.new("ShaderNodeMapRange"); band.interpolation_type = 'STEPPED'; band.inputs["Steps"].default_value = 1
    L.new(sep.outputs["Z"], band.inputs["Value"])
    m1 = N.new("ShaderNodeMath"); m1.operation = 'PINGPONG'; m1.inputs[1].default_value = 0.5; L.new(sep.outputs["Z"], m1.inputs[0])
    gt = N.new("ShaderNodeMath"); gt.operation = 'GREATER_THAN'; gt.inputs[1].default_value = 0.32; L.new(m1.outputs[0], gt.inputs[0])
    c2 = PAL[(i + 3) % len(PAL)]
    mx = N.new("ShaderNodeMix"); mx.data_type = 'RGBA'; L.new(gt.outputs[0], mx.inputs["Factor"])
    mx.inputs["A"].default_value = (*c, 1); mx.inputs["B"].default_value = (*[0.5 * a + 0.5 * b_ for a, b_ in zip(c2, (0.95, 0.93, 0.88))], 1)
    L.new(mx.outputs["Result"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.35 + 0.3 * random.random()
    pmats.append(m)
canm = [mat("M_can%d" % i, c, 0.25, metal=0.6) for i, c in enumerate([(0.7, 0.1, 0.1), (0.2, 0.4, 0.7), (0.8, 0.75, 0.6), (0.2, 0.5, 0.25)])]
bottm = [mat("M_bottle%d" % i, c, 0.05, transm=0.9) for i, c in enumerate([(0.9, 0.95, 0.9), (0.3, 0.6, 0.3), (0.8, 0.5, 0.2)])]
shelfm = mat("M_shelf", (0.88, 0.88, 0.86), 0.35, metal=0.3)
uprm = mat("M_upright", (0.25, 0.27, 0.3), 0.4, metal=0.8)
stripm = [mat("M_strip%d" % i, c, 0.4) for i, c in enumerate([(0.85, 0.7, 0.1), (0.75, 0.15, 0.1), (0.15, 0.45, 0.7)])]

def gondola(name, side):
    """one long shelf run at y = side*SHELF_Y, products facing the aisle; one mesh, many material slots"""
    bm = bmesh.new()
    mats = [shelfm, uprm] + stripm + pmats + canm + bottm
    def add_box(cx, cy, cz, sx, sy, sz, mi):
        r = bmesh.ops.create_cube(bm, size=1.0)
        for v in r["verts"]:
            v.co = Vector((cx + v.co.x * sx, cy + v.co.y * sy, cz + v.co.z * sz))
        for f in {f for v in r["verts"] for f in v.link_faces}: f.material_index = mi
    def add_cyl(cx, cy, cz, rad, h, mi, seg=12):
        r = bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=rad, radius2=rad, depth=h)
        for v in r["verts"]: v.co += Vector((cx, cy, cz))
        for f in {f for v in r["verts"] for f in v.link_faces}: f.material_index = mi
    y0 = side * SHELF_Y; yb = side * (SHELF_Y + SHELF_D)   # front edge, back edge
    add_box(0, side * (SHELF_Y + SHELF_D + 0.02), SHELF_H / 2, AISLE_X1 - AISLE_X0, 0.04, SHELF_H, 1)    # back panel
    for x in [AISLE_X0 + i * 1.2 for i in range(int((AISLE_X1 - AISLE_X0) / 1.2) + 1)]:
        add_box(x, (y0 + yb) / 2, SHELF_H / 2, 0.04, SHELF_D, SHELF_H, 1)
    levels = [0.12, 0.5, 0.88, 1.26, 1.64]
    for li, z in enumerate(levels):
        add_box(0, (y0 + yb) / 2, z, AISLE_X1 - AISLE_X0, SHELF_D, 0.025, 0)
        add_box(0, y0 - side * 0.005, z - 0.01, AISLE_X1 - AISLE_X0, 0.012, 0.05, 2 + (li % 3))   # price strip (plain colour)
        x = AISLE_X0 + 0.05; kind = random.choice("bcbbo")
        while x < AISLE_X1 - 0.1:
            if random.random() < 0.08: kind = random.choice("bbbcco")
            if kind == "b":
                w = random.choice([0.07, 0.09, 0.12, 0.16]); h = random.choice([0.14, 0.18, 0.22, 0.26]); d = random.choice([0.06, 0.08])
                mi = 5 + random.randrange(len(pmats)); n_deep = 4
                for k in range(n_deep):
                    yy = y0 + side * (0.05 + k * (d + 0.01))
                    if abs(yy) > SHELF_Y + SHELF_D - 0.05: break
                    add_box(x + w / 2, yy, z + 0.0125 + h / 2, w * 0.97, d, h, mi)
                x += w + 0.005 + (0.03 if random.random() < 0.1 else 0)
            elif kind == "c":
                rad = 0.035; h = 0.12; mi = 5 + len(pmats) + random.randrange(len(canm))
                for k in range(5):
                    yy = y0 + side * (0.05 + k * 0.075)
                    add_cyl(x + rad, yy, z + 0.0125 + h / 2, rad, h, mi)
                    if random.random() < 0.5: add_cyl(x + rad, yy, z + 0.0125 + h * 1.5, rad, h, mi)
                x += 2 * rad + 0.005
            else:
                rad = 0.035; h = 0.22; mi = 5 + len(pmats) + len(canm) + random.randrange(len(bottm))
                for k in range(4):
                    add_cyl(x + rad, y0 + side * (0.05 + k * 0.09), z + 0.0125 + h / 2, rad, h, mi, seg=10)
                x += 2 * rad + 0.01
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = obj(name, me, REAL, mats=mats)
    for p in me.polygons: p.use_smooth = False
    return o
gondola("ShelfL", 1); gondola("ShelfR", -1)
# second aisle rows beyond (seen through gaps / at the end) and coolers at the back wall
coolm = mat("M_cooler_glow", (0.9, 0.95, 1.0), 0.1, emit=(0.85, 0.93, 1.0), estr=2.5)
for i in range(8):
    obj("Cooler%d" % i, box_mesh("Cooler%d" % i, 0.1, 1.0, 1.9), REAL, (AISLE_X0 - 1.6, -3.6 + i * 1.05, 1.1), [coolm])
    obj("CoolerFrame%d" % i, box_mesh("CoolerFrame%d" % i, 0.5, 1.04, 2.3), REAL, (AISLE_X0 - 1.45 - 0.3, -3.6 + i * 1.05, 1.15), [uprm])
# hanging aisle signs: plain colour boards, no text
signm = mat("M_sign", (0.12, 0.42, 0.6), 0.5)
for x in (-6.0, 0.0, 6.0):
    obj("Sign%d" % int(x), box_mesh("Sign", 0.02, 1.0, 0.32), REAL, (x, 0, 2.75), [signm])
    for dy in (-0.45, 0.45):
        obj("SignWire", box_mesh("SignWire", 0.004, 0.004, 0.68), REAL, (x, dy, 3.25), [uprm])
# ceiling light troffers (emissive) + area lights
tubem = mat("M_tube", (1, 1, 1), 0.2, emit=(1.0, 0.97, 0.9), estr=4.0)
LIGHTS = []
for x in [-8 + 2.0 * i for i in range(9)]:
    for y in (-0.5, 0.5):
        obj("Tube", box_mesh("Tube", 1.4, 0.18, 0.03), REAL, (x, y, 3.56), [tubem])
for x in [-8 + 4.0 * i for i in range(5)]:
    ld = bpy.data.lights.new("StoreArea", 'AREA'); ld.shape = 'RECTANGLE'; ld.size = 3.0; ld.size_y = 1.4
    ld.energy = 320; ld.color = (1.0, 0.96, 0.9)
    lo = bpy.data.objects.new("StoreArea", ld); link(lo, REAL); lo.location = (x, 0, 3.45); LIGHTS.append(lo)
# store world: soft warm grey (enclosed set; only seen in reflections)
w = bpy.data.worlds.new("W_store"); sc.world = w; w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (0.55, 0.55, 0.52, 1); w.node_tree.nodes["Background"].inputs[1].default_value = 0.25

# shopping cart (procedural wire basket) and woman's hand basket
def cart(name, loc, yaw):
    bm = bmesh.new()
    def rod(a, b_, r=0.008):
        a = Vector(a); b_ = Vector(b_); d = b_ - a
        rr = bmesh.ops.create_cone(bm, cap_ends=False, segments=6, radius1=r, radius2=r, depth=d.length)
        q = d.to_track_quat('Z', 'Y')
        for v in rr["verts"]: v.co = (q.to_matrix() @ v.co) + (a + b_) / 2
    L_, W_, H0, H1 = 0.9, 0.55, 0.45, 0.95
    for i in range(10):
        x = -L_ / 2 + i * L_ / 9; rod((x, -W_ / 2, H0), (x, -W_ / 2, H1)); rod((x, W_ / 2, H0), (x, W_ / 2, H1))
    for j in range(7):
        y = -W_ / 2 + j * W_ / 6; rod((-L_ / 2, y, H0), (-L_ / 2, y, H1)); rod((L_ / 2, y, H0), (L_ / 2, y, H1)); rod((-L_ / 2, y, H0), (L_ / 2, y, H0))
    for z in (H0, (H0 + H1) / 2, H1):
        rod((-L_ / 2, -W_ / 2, z), (L_ / 2, -W_ / 2, z)); rod((-L_ / 2, W_ / 2, z), (L_ / 2, W_ / 2, z))
        rod((-L_ / 2, -W_ / 2, z), (-L_ / 2, W_ / 2, z)); rod((L_ / 2, -W_ / 2, z), (L_ / 2, W_ / 2, z))
    for sx in (-1, 1):
        for sy in (-1, 1):
            rod((sx * L_ * 0.42, sy * W_ * 0.42, 0.08), (sx * L_ * 0.45, sy * W_ * 0.45, H0), 0.012)
    rod((L_ / 2 + 0.12, -W_ / 2, 1.05), (L_ / 2 + 0.12, W_ / 2, 1.05), 0.016)
    rod((L_ / 2, -W_ / 2, H1), (L_ / 2 + 0.12, -W_ / 2, 1.05)); rod((L_ / 2, W_ / 2, H1), (L_ / 2 + 0.12, W_ / 2, 1.05))
    for sx in (-1, 1):
        for sy in (-1, 1):
            rr = bmesh.ops.create_cone(bm, cap_ends=True, segments=10, radius1=0.05, radius2=0.05, depth=0.03)
            for v in rr["verts"]: v.co = Matrix.Rotation(math.pi / 2, 3, 'X') @ v.co + Vector((sx * L_ * 0.42, sy * W_ * 0.42, 0.05))
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = obj(name, me, REAL, loc, [mat("M_chrome", (0.8, 0.8, 0.82), 0.15, metal=1.0)]); o.rotation_euler.z = yaw
    return o
cart("Cart", (-4.0, -0.2, 0), 0)
bk = bpy.data.objects.new("Basket", box_mesh("Basket", 0.42, 0.28, 0.2)); link(bk, REAL)
bk.data.materials.append(mat("M_basket", (0.65, 0.08, 0.06), 0.45))
sol = bk.modifiers.new("shell", 'SOLIDIFY'); sol.thickness = 0.008
bmb = bmesh.new(); bmb.from_mesh(bk.data)
top = [f for f in bmb.faces if f.normal.z > 0.9]; bmesh.ops.delete(bmb, geom=top, context='FACES_ONLY'); bmb.to_mesh(bk.data); bmb.free()
for i, (dx, dy, c) in enumerate([(-0.1, 0.03, 2), (0.08, -0.05, 7), (0.1, 0.07, 9)]):
    it = obj("BasketItem%d" % i, box_mesh("BI%d" % i, 0.12, 0.08, 0.16), REAL, (dx, dy, -0.02), [pmats[c]]); it.parent = bk
# loose items that will fall off the shelf at the impact
for i in range(3):
    bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=True, segments=14, radius1=0.035, radius2=0.035, depth=0.12)
    me = bpy.data.meshes.new("FallCan%d" % i); bm.to_mesh(me); bm.free()
    o = obj("FallCan%d" % i, me, REAL, mats=[canm[i % 4]])
# dust motes in the light (tiny emissive specks drifting)
dustm = mat("M_dust", (1, 1, 1), 0.5, emit=(1.0, 0.97, 0.9), estr=3.0)
bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=1, radius=0.0025); dme = bpy.data.meshes.new("Dust"); bm.to_mesh(dme); bm.free()
dme.materials.append(dustm)
for i in range(90):
    o = obj("Dust%02d" % i, dme, REAL, (random.uniform(-1.0, 4.5), random.uniform(-0.6, 0.95), random.uniform(0.5, 1.9)))

# ------------------------------------------------------------------ bullet (generic slug only)
bm = bmesh.new()
prof = []
for i in range(17):
    t = i / 16; x = 0.6 * t                      # 0 = base, 0.6 = tip  (macro units; scaled by MACRO root 0.025 -> 15 mm)
    r = 0.18 if t < 0.55 else 0.18 * math.sqrt(max(0.0, 1 - ((t - 0.55) / 0.45) ** 2)) ** 0.9
    prof.append((x, max(r, 0.012 if i < 16 else 0.0)))
segs = 24
rings = []
for x, r in prof:
    rings.append([bm.verts.new((x, r * math.cos(2 * math.pi * k / segs), r * math.sin(2 * math.pi * k / segs))) for k in range(segs)])
for a, b_ in zip(rings, rings[1:]):
    for k in range(segs):
        bm.faces.new((a[k], a[(k + 1) % segs], b_[(k + 1) % segs], b_[k]))
bm.faces.new(list(reversed(rings[0])))
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)
bme = bpy.data.meshes.new("Bullet"); bm.to_mesh(bme); bm.free()
for p in bme.polygons: p.use_smooth = True
bullet = bpy.data.objects.new("Bullet", bme); sc.collection.objects.link(bullet)   # in both worlds -> master collection
bme.materials.append(mat("M_copper", (0.85, 0.45, 0.25), 0.22, metal=1.0, noise_amt=0.25, nscale=30, bump=0.05))
bullet.modifiers.new("sub", 'SUBSURF').levels = 1
# heat-shimmer / speed trail behind the bullet in the store (thin emissive cone, fades)
bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=False, segments=16, radius1=0.0, radius2=0.16, depth=6.0)
for v in bm.verts: v.co = Matrix.Rotation(math.pi / 2, 3, 'Y') @ v.co + Vector((-3.0, 0, 0))
tme = bpy.data.meshes.new("Trail"); bm.to_mesh(tme); bm.free()
trm = bpy.data.materials.new("M_trail"); trm.use_nodes = True; nt = trm.node_tree; N = nt.nodes; L = nt.links
N.remove(N["Principled BSDF"]); mo = N["Material Output"]
tc = N.new("ShaderNodeTexCoord"); sep = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs["Generated"], sep.inputs["Vector"])
oi = N.new("ShaderNodeObjectInfo")
pw = N.new("ShaderNodeMath"); pw.operation = 'POWER'; pw.inputs[1].default_value = 3.0; L.new(sep.outputs["X"], pw.inputs[0])
mul = N.new("ShaderNodeMath"); mul.operation = 'MULTIPLY'; L.new(pw.outputs[0], mul.inputs[0]); L.new(oi.outputs["Alpha"], mul.inputs[1])
mul2 = N.new("ShaderNodeMath"); mul2.operation = 'MULTIPLY'; mul2.inputs[1].default_value = 0.35; L.new(mul.outputs[0], mul2.inputs[0])
em = N.new("ShaderNodeEmission"); em.inputs["Color"].default_value = (1.0, 0.85, 0.65, 1); em.inputs["Strength"].default_value = 1.5
tr = N.new("ShaderNodeBsdfTransparent"); mxs = N.new("ShaderNodeMixShader")
L.new(mul2.outputs[0], mxs.inputs[0]); L.new(tr.outputs[0], mxs.inputs[1]); L.new(em.outputs[0], mxs.inputs[2]); L.new(mxs.outputs[0], mo.inputs["Surface"])
tme.materials.append(trm)
trail = bpy.data.objects.new("Trail", tme); link(trail, REAL); trail.parent = bullet
trail.scale = (1, 0.5, 0.5); trail.location = (-0.0, 0, 0)

# ------------------------------------------------------------------ MACRO cross-section (macro units; root scaled 0.025)
root = bpy.data.objects.new("MacroRoot", None); sc.collection.objects.link(root); root.empty_display_size = 2
def mobj(name, me, mats=(), loc=(0, 0, 0)):
    o = bpy.data.objects.new(name, me); link(o, MACRO); o.parent = root; o.location = loc
    for m_ in mats: o.data.materials.append(m_)
    return o
ZH, YB = 3.6, 3.2           # half height, slab depth behind the cut face (cut face at y=0, slab at y in [-YB, 0])
def slab(name, x0, x1, m_, sub=0, zh=ZH):
    me = box_mesh(name, x1 - x0, YB, 2 * zh)
    o = mobj(name, me, [m_], ((x0 + x1) / 2, -YB / 2, 0))
    if sub:
        o.modifiers.new("sub", 'SUBSURF').levels = sub
    return o
def grid_slab(name, x0, x1, m_, nz=72, ny=64):
    """a thin layer with a dense grid so it can dimple (Warp modifier) — x0..x1 thickness"""
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=ny, y_segments=nz, size=1.0)
    for v in bm.verts: v.co = Vector((0.0, (v.co.x + 1) / 2 * -YB, v.co.y * ZH))
    bmesh.ops.solidify(bm, geom=bm.faces[:], thickness=-(x1 - x0))
    for v in bm.verts: v.co.x += x0
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = True
    return mobj(name, me, [m_])
fabric_m = mat("M_fabric_macro", (0.03, 0.10, 0.28), 0.85, noise_amt=0.5, nscale=60, bump=0.4)
skin_epi = mat("M_skin_epi", (0.78, 0.55, 0.42), 0.45, sss=0.3, noise_amt=0.3, nscale=25, bump=0.2)
skin_der = mat("M_dermis", (0.85, 0.45, 0.42), 0.5, sss=0.4, noise_amt=0.4, nscale=12, bump=0.3)
fat_m = mat("M_fat_lobule", (1.0, 0.62, 0.08), 0.3, sss=0.25, coat=0.5, noise_amt=0.3, nscale=6, bump=0.15)
sept_m = mat("M_septa", (0.7, 0.38, 0.25), 0.4, sss=0.3, noise_amt=0.4, nscale=8)
fascia_m = mat("M_fascia", (0.92, 0.88, 0.85), 0.3, sss=0.2, coat=0.5, noise_amt=0.3, nscale=20)
musc_m = mat("M_muscle", (0.42, 0.03, 0.03), 0.4, sss=0.25, coat=0.35, noise_amt=0.45, nscale=14, bump=0.5)
perit_m = mat("M_peritoneum", (0.95, 0.8, 0.78), 0.1, sss=0.2, coat=1.0, transm=0.5)
gut_m = mat("M_intestine", (0.75, 0.32, 0.3), 0.18, sss=0.6, coat=1.0, noise_amt=0.3, nscale=5, bump=0.2)
vessel_r = mat("M_vessel_red", (0.6, 0.04, 0.04), 0.3, sss=0.3, coat=0.5)
vessel_b = mat("M_vessel_blue", (0.15, 0.2, 0.5), 0.3, sss=0.3, coat=0.5)
fabric = grid_slab("M_Fabric", -0.06, 0.0, fabric_m, 48, 40)
epi = grid_slab("M_Epidermis", 0.0, 0.06, skin_epi)
der = grid_slab("M_Dermis", 0.06, 0.32, skin_der)
sept = slab("M_FatBed", 0.32, 4.3, sept_m)
sept.location.y = -YB / 2 - 0.25                # recessed so lobules bulge from the face
fas = slab("M_Fascia", 4.3, 4.42, fascia_m)
# muscle: fibre bundles (long rounded boxes along Z, stacked), striated look via bump noise
fib_me = []
for k in range(3):
    bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=True, segments=10, radius1=0.062, radius2=0.062, depth=2 * ZH * 0.99, )
    me = bpy.data.meshes.new("Fib%d" % k); bm.to_mesh(me); bm.free()
    fib_me.append(me)
def fibre(name, x, y, k):
    bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=True, segments=10, radius1=0.062, radius2=0.062, depth=2 * ZH * 0.99)
    bmesh.ops.subdivide_edges(bm, edges=[e for e in bm.edges if abs(e.verts[0].co.z - e.verts[1].co.z) > 1], cuts=60)
    for v in bm.verts:
        v.co.x += 0.012 * math.sin(v.co.z * 3.1 + k); v.co.y += 0.012 * math.cos(v.co.z * 2.3 + k * 1.7)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = True
    return mobj(name, me, [musc_m], (x, y, 0))
for i in range(8):
    for j in range(4):
        fibre("M_MuscleFib_%d_%d" % (i, j), 4.5 + i * 0.118 + (0.059 if j % 2 else 0), -0.07 - j * 0.11, i * 4 + j)
musc_back = slab("M_MuscleBed", 4.42, 5.5, musc_m); musc_back.location.y = -YB / 2 - 0.1
perit = grid_slab("M_Peritoneum", 5.5, 5.56, perit_m, 24, 24)
# intestines: tubes coiling behind the peritoneum (curves with bevel)
gut_objs = []
for g in range(5):
    cu = bpy.data.curves.new("Gut%d" % g, 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = 0.42; cu.bevel_resolution = 4
    sp = cu.splines.new('NURBS'); pts = []
    z = -ZH + 0.5 + g * 1.45; y = -0.6 - 0.4 * (g % 2)
    for k in range(14):
        pts.append((6.1 + 0.6 * math.sin(k * 1.3 + g), y - 0.25 * math.cos(k * 0.9 + g) - k * 0.12, z + 0.5 * math.sin(k * 0.7 + g * 2)))
    sp.points.add(len(pts) - 1)
    for p, c in zip(sp.points, pts): p.co = (*c, 1)
    sp.use_endpoint_u = True; sp.order_u = 4
    o = bpy.data.objects.new("M_Gut%d" % g, cu); link(o, MACRO); o.parent = root; cu.materials.append(gut_m)
    gut_objs.append(o)
dg = bpy.context.evaluated_depsgraph_get()
for i, o in enumerate(list(gut_objs)):
    me = bpy.data.meshes.new_from_object(o.evaluated_get(dg)); nm = o.name
    bpy.data.objects.remove(o, do_unlink=True)
    for p in me.polygons: p.use_smooth = True
    gut_objs[i] = mobj(nm, me, ())
gut_bed = slab("M_GutBed", 5.6, 8.4, mat("M_mesentery", (0.8, 0.5, 0.42), 0.3, sss=0.4, coat=0.5, noise_amt=0.4, nscale=5))
gut_bed.location.y = -YB / 2 - 1.6
# blood vessels threading through the fat (thin tubes, clean)
for v in range(6):
    cu = bpy.data.curves.new("Vessel%d" % v, 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = 0.05 if v % 2 == 0 else 0.035
    sp = cu.splines.new('BEZIER'); n = 6; sp.bezier_points.add(n - 1)
    z0 = random.uniform(-3, 3); y0 = random.uniform(-2.6, -0.5)
    for k, bp_ in enumerate(sp.bezier_points):
        bp_.co = (0.5 + k * 0.75, y0 + random.uniform(-0.3, 0.3), z0 + random.uniform(-0.6, 0.6)); bp_.handle_left_type = bp_.handle_right_type = 'AUTO'
    o = bpy.data.objects.new("M_Vessel%d" % v, cu); link(o, MACRO); o.parent = root; cu.materials.append(vessel_r if v % 2 == 0 else vessel_b)
# fat lobules: packed, slightly flattened blobs; some bulge out of the cut face
lob_me = []
for k in range(6):
    bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=3, radius=1.0)
    for v in bm.verts:
        n_ = noise.noise(v.co * 1.7 + Vector((k * 3.1, k, 0)))
        v.co *= 1.0 + 0.18 * n_
    me = bpy.data.meshes.new("Lobule%d" % k); bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = True
    me.materials.append(fat_m); lob_me.append(me)
LOB = []
pts = []
tries = 0
while len(pts) < 420 and tries < 40000:
    tries += 1
    r = random.uniform(0.26, 0.44)
    c = Vector((random.uniform(0.32 + r * 0.8, 4.3 - r * 0.8), random.uniform(-YB + r, 0.12), random.uniform(-ZH + r * 0.7, ZH - r * 0.7)))
    if all((c - p).length > (r + q) * 0.86 for p, q in pts):
        pts.append((c, r))
for i, (c, r) in enumerate(pts):
    o = mobj("M_Lob%03d" % i, lob_me[i % 6], (), tuple(c))
    o.scale = (r * 0.9, r, r * 1.05); o.rotation_euler = (random.uniform(0, 6), random.uniform(0, 6), random.uniform(0, 6))
    o["rest"] = tuple(c); o["r"] = r; LOB.append(o)
# energy rings (emissive tori around the channel, keyed later)
ring_m = bpy.data.materials.new("M_ring"); ring_m.use_nodes = True; nt = ring_m.node_tree; N = nt.nodes; L = nt.links
N.remove(N["Principled BSDF"]); mo = N["Material Output"]; oi = N.new("ShaderNodeObjectInfo")
em = N.new("ShaderNodeEmission"); em.inputs["Color"].default_value = (1.0, 0.92, 0.7, 1)
ms = N.new("ShaderNodeMath"); ms.operation = 'MULTIPLY'; ms.inputs[1].default_value = 12.0; L.new(oi.outputs["Alpha"], ms.inputs[0]); L.new(ms.outputs[0], em.inputs["Strength"])
tr = N.new("ShaderNodeBsdfTransparent"); mxs = N.new("ShaderNodeMixShader")
L.new(oi.outputs["Alpha"], mxs.inputs[0]); L.new(tr.outputs[0], mxs.inputs[1]); L.new(em.outputs[0], mxs.inputs[2]); L.new(mxs.outputs[0], mo.inputs["Surface"])
bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=False, segments=64, radius1=1.0, radius2=1.0, depth=0.06)
for v in bm.verts: v.co = Matrix.Rotation(math.pi / 2, 3, 'Y') @ v.co
rme = bpy.data.meshes.new("Ring"); bm.to_mesh(rme); bm.free(); rme.materials.append(ring_m)
for i in range(12):
    o = mobj("M_Ring%02d" % i, rme, ()); o.scale = (1, 0.01, 0.01); o.color = (1, 1, 1, 0)
    sol = o.modifiers.new("sol", 'SOLIDIFY'); sol.thickness = 0.07
# entry hole decal on fabric + skin (dark ring) — appears after pierce
hole_m = mat("M_hole", (0.05, 0.03, 0.03), 0.6)
bm = bmesh.new(); bmesh.ops.create_circle(bm, cap_ends=True, segments=24, radius=0.2)
for v in bm.verts: v.co = Matrix.Rotation(math.pi / 2, 3, 'Y') @ v.co + Vector((-0.065, 0, 0))
hme = bpy.data.meshes.new("Hole"); bm.to_mesh(hme); bm.free(); hme.materials.append(hole_m)
hole = mobj("M_HoleDecal", hme, ())
# studio backdrop dome: cyan -> white gradient (emission), seen only from inside
bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=48, v_segments=24, radius=30.0)
bmesh.ops.reverse_faces(bm, faces=bm.faces[:])
dme2 = bpy.data.meshes.new("Dome"); bm.to_mesh(dme2); bm.free()
for p in dme2.polygons: p.use_smooth = True
dm = bpy.data.materials.new("M_dome"); dm.use_nodes = True; nt = dm.node_tree; N = nt.nodes; L = nt.links
N.remove(N["Principled BSDF"]); mo = N["Material Output"]
tc = N.new("ShaderNodeTexCoord"); sep = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs["Object"], sep.inputs["Vector"])
mr = N.new("ShaderNodeMapRange"); mr.inputs["From Min"].default_value = -20; mr.inputs["From Max"].default_value = 24
L.new(sep.outputs["Z"], mr.inputs["Value"])
cr = N.new("ShaderNodeValToRGB"); cr.color_ramp.elements[0].color = (0.12, 0.55, 0.72, 1); cr.color_ramp.elements[1].color = (0.92, 0.97, 1.0, 1)
cr.color_ramp.elements[0].position = 0.15; cr.color_ramp.elements[1].position = 0.85
L.new(mr.outputs["Result"], cr.inputs["Fac"])
em = N.new("ShaderNodeEmission"); em.inputs["Strength"].default_value = 0.45; L.new(cr.outputs["Color"], em.inputs["Color"])
L.new(em.outputs[0], mo.inputs["Surface"])
dme2.materials.append(dm)
dome = mobj("M_Dome", dme2, (), (3.0, 0, 0))
# macro studio lights (power scaled for the 0.025 root: radiance ~ P / size^2, so P * 0.025^2)
S2_ = 0.025 ** 2
for nm, loc, rot, P, size, col in (("M_Key", (-2, 9, 8), (math.radians(-50), 0, math.radians(180 + 15)), 9000, 8, (1, 0.97, 0.93)),
                                   ("M_Fill", (8, 10, -2), (math.radians(-100), 0, math.radians(150)), 2500, 10, (0.8, 0.92, 1.0)),
                                   ("M_Rim", (3, -4, 10), (math.radians(20), 0, 0), 3000, 6, (0.85, 0.95, 1.0))):
    ld = bpy.data.lights.new(nm, 'AREA'); ld.size = size; ld.energy = 0.4 * P * S2_; ld.color = col
    lo = bpy.data.objects.new(nm, ld); link(lo, MACRO); lo.parent = root; lo.location = loc
    tgt = Vector((2.5, 0, 0)) - Vector(loc); lo.rotation_euler = tgt.to_track_quat('-Z', 'Y').to_euler()

# ------------------------------------------------------------------ camera
cd = bpy.data.cameras.new("CAM_Film"); cam = bpy.data.objects.new("CAM_Film", cd); sc.collection.objects.link(cam); sc.camera = cam
cd.lens = 30; cd.sensor_fit = 'AUTO'; cd.sensor_width = 36; cd.clip_start = 0.01; cd.clip_end = 200
print("LOBULES", len(LOB))
bpy.ops.wm.save_as_mainfile(filepath=out)
