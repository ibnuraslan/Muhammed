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
sc.render.use_motion_blur = True; sc.render.motion_blur_shutter = 0.5; sc.cycles.samples = 48; sc.cycles.adaptive_threshold = 0.05; sc.cycles.use_denoising = True
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
    # printed-packaging look without text: per-face UV label = coloured band + round badge + fine stripes + print grain,
    # varied per product by the face attribute "rnd"
    uv = N.new("ShaderNodeUVMap"); uv.uv_map = "UVMap"; sep = N.new("ShaderNodeSeparateXYZ"); L.new(uv.outputs["UV"], sep.inputs["Vector"])
    at = N.new("ShaderNodeAttribute"); at.attribute_name = "rnd"; at.attribute_type = 'GEOMETRY'
    c2 = PAL[(i + 3) % len(PAL)]; c3 = PAL[(i + 7) % len(PAL)]
    def mth(op, a_, b_=None, v=None):
        n_ = N.new("ShaderNodeMath"); n_.operation = op
        L.new(a_, n_.inputs[0]) if not isinstance(a_, float) else n_.inputs[0].__setattr__("default_value", a_)
        if b_ is not None: L.new(b_, n_.inputs[1])
        if v is not None: n_.inputs[1].default_value = v
        return n_.outputs[0]
    lo = mth('MULTIPLY_ADD', at.outputs["Fac"], None, 0.25); lo.node.inputs[2].default_value = 0.2   # band start 0.2..0.45
    inband = mth('MULTIPLY', mth('GREATER_THAN', sep.outputs["Y"], lo), mth('LESS_THAN', sep.outputs["Y"], mth('ADD', lo, None, 0.32)))
    cx = mth('SUBTRACT', sep.outputs["X"], None, 0.5); cy = mth('SUBTRACT', sep.outputs["Y"], mth('ADD', lo, None, 0.16))
    rr = mth('SQRT', mth('ADD', mth('MULTIPLY', cx, cx), mth('MULTIPLY', cy, cy)))
    badge = mth('LESS_THAN', rr, None, 0.13)
    stripes = mth('MULTIPLY', mth('GREATER_THAN', sep.outputs["Y"], None, 0.82), mth('GREATER_THAN', mth('SINE', mth('MULTIPLY', sep.outputs["Y"], None, 90.0)), None, 0.3))
    hs = N.new("ShaderNodeHueSaturation"); hs.inputs["Color"].default_value = (*[0.45 * a_ + 0.55 * b_ for a_, b_ in zip(c2, (0.95, 0.93, 0.88))], 1)
    L.new(mth('SUBTRACT', at.outputs["Fac"], None, 0.0), hs.inputs["Hue"])
    m1 = N.new("ShaderNodeMix"); m1.data_type = 'RGBA'; L.new(inband, m1.inputs["Factor"]); m1.inputs["A"].default_value = (*c, 1); L.new(hs.outputs[0], m1.inputs["B"])
    m2 = N.new("ShaderNodeMix"); m2.data_type = 'RGBA'; L.new(badge, m2.inputs["Factor"]); L.new(m1.outputs["Result"], m2.inputs["A"]); m2.inputs["B"].default_value = (*c3, 1)
    m3 = N.new("ShaderNodeMix"); m3.data_type = 'RGBA'; L.new(stripes, m3.inputs["Factor"]); L.new(m2.outputs["Result"], m3.inputs["A"]); m3.inputs["B"].default_value = (0.05, 0.05, 0.05, 1)
    nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 300; L.new(uv.outputs["UV"], nz.inputs["Vector"])
    gr = N.new("ShaderNodeMix"); gr.data_type = 'RGBA'; gr.blend_type = 'MULTIPLY'; gr.inputs["Factor"].default_value = 0.12
    L.new(m3.outputs["Result"], gr.inputs["A"]); L.new(nz.outputs["Color"], gr.inputs["B"]); L.new(gr.outputs["Result"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.3 + 0.3 * random.random()
    pmats.append(m)
canm = [mat("M_can%d" % i, c, 0.25, metal=0.6) for i, c in enumerate([(0.7, 0.1, 0.1), (0.2, 0.4, 0.7), (0.8, 0.75, 0.6), (0.2, 0.5, 0.25)])]
bottm = [mat("M_bottle%d" % i, c, 0.05, transm=0.9) for i, c in enumerate([(0.9, 0.95, 0.9), (0.3, 0.6, 0.3), (0.8, 0.5, 0.2)])]
shelfm = mat("M_shelf", (0.88, 0.88, 0.86), 0.35, metal=0.3)
uprm = mat("M_upright", (0.25, 0.27, 0.3), 0.4, metal=0.8)
stripm = [mat("M_strip%d" % i, c, 0.4) for i, c in enumerate([(0.85, 0.7, 0.1), (0.75, 0.15, 0.1), (0.15, 0.45, 0.7)])]

def gondola(name, side):
    """one long shelf run at y = side*SHELF_Y, products facing the aisle; one mesh, many material slots"""
    bm = bmesh.new()
    tagm = mat("M_tag", (0.92, 0.92, 0.9), 0.5); chromem = mat("M_rail", (0.8, 0.8, 0.82), 0.2, metal=1.0)
    mats = [shelfm, uprm] + stripm + pmats + canm + bottm + [tagm, chromem]
    TAG = len(mats) - 2; RAIL = len(mats) - 1
    uvl = bm.loops.layers.uv.new("UVMap"); rl = bm.faces.layers.float.new("rnd")
    def face_uvs(faces, val):
        for f in faces:
            n_ = f.normal
            ax = Vector((0, 0, 1)) if abs(n_.z) < 0.9 else Vector((0, 1, 0))
            u_ = ax.cross(n_).normalized(); v_ = n_.cross(u_).normalized() if abs(n_.z) < 0.9 else ax
            us = [l.vert.co.dot(u_) for l in f.loops]; vs = [l.vert.co.dot(v_) for l in f.loops]
            for l in f.loops:
                l[uvl].uv = ((l.vert.co.dot(u_) - min(us)) / max(1e-6, max(us) - min(us)), (l.vert.co.dot(v_) - min(vs)) / max(1e-6, max(vs) - min(vs)))
            f[rl] = val
    def add_box(cx, cy, cz, sx, sy, sz, mi, bevel=0.0, rot=0.0, pouch=False):
        if pouch:   # pillow pack: squared-off sphere, pinched top seal
            r = bmesh.ops.create_icosphere(bm, subdivisions=2, radius=0.5); vs = r["verts"]
            for v in vs:
                c = v.co * 2
                q = Vector([math.copysign(abs(a_) ** 0.45, a_) * 0.5 for a_ in c])
                if q.z > 0.38: q.y *= 0.25
                q.y *= 0.8 + 0.2 * (1 - abs(c.z)); v.co = q
        else:
            r = bmesh.ops.create_cube(bm, size=1.0); vs = r["verts"]
            if bevel: ed = list({e for v in vs for e in v.link_edges})
        Rz = Matrix.Rotation(rot, 3, 'Z')
        for v in vs:
            v.co = Rz @ Vector((v.co.x * sx, v.co.y * sy, v.co.z * sz)) + Vector((cx, cy, cz))
        if bevel and not pouch:
            res = bmesh.ops.bevel(bm, geom=ed + list(vs), offset=bevel, segments=1, affect='EDGES', profile=0.5)
            vs = [v for v in res["verts"] if v.is_valid]
        fs = {f for v in vs for f in v.link_faces}
        for f in fs: f.material_index = mi; f.smooth = pouch
        [f.normal_update() for f in fs]; face_uvs(fs, random.random())
    def add_lathe(cx, cy, z0, prof, mi, seg=16):
        rings = []
        for r_, z_ in prof:
            if r_ < 1e-4: rings.append([bm.verts.new((cx, cy, z0 + z_))])
            else: rings.append([bm.verts.new((cx + r_ * math.cos(2 * math.pi * k / seg), cy + r_ * math.sin(2 * math.pi * k / seg), z0 + z_)) for k in range(seg)])
        fs = []
        for a_, b_ in zip(rings, rings[1:]):
            for k in range(seg):
                if len(a_) == 1: q = (a_[0], b_[(k + 1) % seg], b_[k])
                elif len(b_) == 1: q = (a_[k], a_[(k + 1) % seg], b_[0])
                else: q = (a_[k], a_[(k + 1) % seg], b_[(k + 1) % seg], b_[k])
                f = bm.faces.new(q); f.material_index = mi; f.smooth = True; fs.append(f)
        h = max(z_ for _, z_ in prof); val = random.random()
        for f in fs:
            f.normal_update(); f[rl] = val
            for l in f.loops:
                a = math.atan2(l.vert.co.y - cy, l.vert.co.x - cx); l[uvl].uv = ((a / (2 * math.pi)) % 1.0, (l.vert.co.z - z0) / h)
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
        add_box(0, y0 - side * 0.004, z + 0.055, AISLE_X1 - AISLE_X0, 0.005, 0.005, RAIL)          # wire front rail
        for xt in [AISLE_X0 + 0.2 + 0.31 * i + random.uniform(-0.05, 0.05) for i in range(int((AISLE_X1 - AISLE_X0) / 0.31))]:
            add_box(xt, y0 - side * 0.013, z - 0.008, 0.045, 0.003, 0.03, TAG)                     # blank shelf tags
        x = AISLE_X0 + 0.05; kind = random.choice("bcbbo")
        while x < AISLE_X1 - 0.1:
            if random.random() < 0.08: kind = random.choice("bbbcco")
            if kind == "b":
                w = random.choice([0.07, 0.09, 0.12, 0.16]); h = random.choice([0.14, 0.18, 0.22, 0.26]); d = random.choice([0.06, 0.08])
                mi = 5 + random.randrange(len(pmats)); n_deep = 4
                for k in range(n_deep):
                    yy = y0 + side * (0.05 + k * (d + 0.01))
                    if abs(yy) > SHELF_Y + SHELF_D - 0.05: break
                    add_box(x + w / 2, yy + side * random.uniform(-0.004, 0.012), z + 0.0125 + h / 2, w * 0.97, d, h, mi,
                            bevel=0.0025, rot=math.radians(random.gauss(0, 1.6)))
                x += w + 0.005 + (0.03 if random.random() < 0.1 else 0)
            elif kind == "c":
                rad = 0.035; h = 0.12; mi = 5 + len(pmats) + random.randrange(len(canm))
                for k in range(5):
                    yy = y0 + side * (0.05 + k * 0.075)
                    CANP = [(0, 0), (rad * 0.9, 0), (rad * 0.92, 0.004), (rad, 0.011), (rad, h - 0.013), (rad * 0.96, h - 0.006), (rad * 0.98, h - 0.002), (rad * 0.88, h), (0, h - 0.004)]
                    add_lathe(x + rad, yy, z + 0.0125, CANP, mi)
                    if random.random() < 0.5: add_lathe(x + rad, yy, z + 0.0125 + h, CANP, mi)
                x += 2 * rad + 0.005
            elif kind == "o":
                rad = 0.035; h = 0.22; mi = 5 + len(pmats) + len(canm) + random.randrange(len(bottm))
                BOT = [(0, 0), (rad * 0.85, 0), (rad, 0.01), (rad, 0.55 * h), (rad * 0.93, 0.66 * h), (rad * 0.5, 0.8 * h), (rad * 0.34, 0.86 * h),
                       (rad * 0.34, 0.93 * h), (rad * 0.4, 0.935 * h), (rad * 0.4, h), (0, h)]
                for k in range(4):
                    add_lathe(x + rad, y0 + side * (0.05 + k * 0.09), z + 0.0125, BOT, mi, seg=14)
                x += 2 * rad + 0.01
            else:
                w = random.choice([0.12, 0.15, 0.18]); h = random.choice([0.18, 0.24]); mi = 5 + random.randrange(len(pmats))
                for k in range(3):
                    add_box(x + w / 2, y0 + side * (0.05 + k * 0.07), z + 0.0125 + h / 2, w * 0.95, 0.05, h, mi, pouch=True, rot=math.radians(random.gauss(0, 4)))
                x += w + 0.01
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = obj(name, me, REAL, mats=mats)
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
tubem = mat("M_tube", (1, 1, 1), 0.2, emit=(1.0, 0.97, 0.9), estr=3.0)
LIGHTS = []
for x in [-8 + 2.0 * i for i in range(9)]:
    for y in (-0.5, 0.5):
        obj("Tube", box_mesh("Tube", 1.4, 0.18, 0.03), REAL, (x, y, 3.56), [tubem])
for x in [-8 + 4.0 * i for i in range(5)]:
    ld = bpy.data.lights.new("StoreArea", 'AREA'); ld.shape = 'RECTANGLE'; ld.size = 3.0; ld.size_y = 1.4
    ld.energy = 165; ld.color = (1.0, 0.96, 0.9)
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
ZH, YB = 6.0, 3.2           # half height, slab depth behind the cut face (cut face at y=0, slab at y in [-YB, 0])
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
fabric_m = mat("M_fabric_macro", (0.02, 0.065, 0.19), 0.85, noise_amt=0.5, nscale=60, bump=0.4)
skin_epi = mat("M_skin_epi", (0.78, 0.55, 0.42), 0.45, sss=0.3, noise_amt=0.3, nscale=25, bump=0.2)
skin_der = mat("M_dermis", (0.85, 0.45, 0.42), 0.5, sss=0.4, noise_amt=0.4, nscale=12, bump=0.3)
fat_m = mat("M_fat_lobule", (1.0, 0.63, 0.24), 0.3, sss=0.5, coat=0.8, noise_amt=0.22, nscale=9, bump=0.12)
_nt = fat_m.node_tree; _b = _nt.nodes["Principled BSDF"]; _lw = _nt.nodes.new("ShaderNodeLayerWeight"); _lw.inputs["Blend"].default_value = 0.12
_src = _b.inputs["Base Color"].links[0].from_socket
_mx = _nt.nodes.new("ShaderNodeMix"); _mx.data_type = 'RGBA'; _lpw = _nt.nodes.new("ShaderNodeMath"); _lpw.operation = "POWER"; _lpw.inputs[1].default_value = 3.0; _nt.links.new(_lw.outputs["Facing"], _lpw.inputs[0]); _nt.links.new(_lpw.outputs[0], _mx.inputs["Factor"])
_nt.links.new(_src, _mx.inputs["A"]); _mx.inputs["B"].default_value = (0.96, 0.86, 0.66, 1); _nt.links.new(_mx.outputs["Result"], _b.inputs["Base Color"])
_b.inputs["Subsurface Radius"].default_value = (1.1, 0.65, 0.2); _b.inputs["Coat Roughness"].default_value = 0.06
sept_m = mat("M_septa", (0.9, 0.8, 0.62), 0.3, sss=0.4, coat=0.6, noise_amt=0.4, nscale=8)
fascia_m = mat("M_fascia", (0.92, 0.88, 0.85), 0.3, sss=0.2, coat=0.5, noise_amt=0.3, nscale=20)
musc_m = mat("M_muscle", (0.42, 0.03, 0.03), 0.35, sss=0.3, coat=0.7, noise_amt=0.45, nscale=14, bump=0.3)
_nt = musc_m.node_tree; _b = _nt.nodes["Principled BSDF"]
_tc = _nt.nodes.new("ShaderNodeTexCoord"); _wv = _nt.nodes.new("ShaderNodeTexWave"); _wv.bands_direction = 'Z'; _wv.inputs["Scale"].default_value = 60
_wv.inputs["Distortion"].default_value = 2.0; _nt.links.new(_tc.outputs["Object"], _wv.inputs["Vector"])
_bp = _nt.nodes.new("ShaderNodeBump"); _bp.inputs["Strength"].default_value = 0.35; _nt.links.new(_wv.outputs["Fac"], _bp.inputs["Height"]); _nt.links.new(_bp.outputs["Normal"], _b.inputs["Normal"])
_b.inputs["Coat Roughness"].default_value = 0.08
perit_m = mat("M_peritoneum", (0.9, 0.72, 0.7), 0.12, sss=0.3, coat=1.0, transm=0.15)
gut_m = mat("M_intestine", (0.75, 0.32, 0.3), 0.18, sss=0.6, coat=1.0, noise_amt=0.3, nscale=5, bump=0.2)
vessel_r = mat("M_vessel_red", (0.6, 0.04, 0.04), 0.3, sss=0.3, coat=0.5)
vessel_b = mat("M_vessel_blue", (0.15, 0.2, 0.5), 0.3, sss=0.3, coat=0.5)
def add_weave(m_, root_obj, strength, dist=0.0005):
    nt = m_.node_tree; N = nt.nodes; L = nt.links; b = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord"); tc.object = root_obj
    sep = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs["Object"], sep.inputs[0])
    def sinw(sock, k):
        m1 = N.new("ShaderNodeMath"); m1.operation = 'MULTIPLY'; m1.inputs[1].default_value = k; L.new(sock, m1.inputs[0])
        m2 = N.new("ShaderNodeMath"); m2.operation = 'SINE'; L.new(m1.outputs[0], m2.inputs[0]); return m2.outputs[0]
    a_ = sinw(sep.outputs["Y"], 2 * math.pi / 0.04); b2 = sinw(sep.outputs["Z"], 2 * math.pi / 0.04)
    pr = N.new("ShaderNodeMath"); pr.operation = 'MULTIPLY'; L.new(a_, pr.inputs[0]); L.new(b2, pr.inputs[1])
    ab = N.new("ShaderNodeMath"); ab.operation = 'ABSOLUTE'; L.new(pr.outputs[0], ab.inputs[0])
    bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = strength; bp.inputs["Distance"].default_value = dist
    L.new(ab.outputs[0], bp.inputs["Height"])
    old = b.inputs["Normal"].links[0].from_socket if b.inputs["Normal"].links else None
    if old: L.new(old, bp.inputs["Normal"])
    L.new(bp.outputs["Normal"], b.inputs["Normal"])
    cm = N.new("ShaderNodeMix"); cm.data_type = 'RGBA'; cm.blend_type = 'MULTIPLY'; cm.inputs["Factor"].default_value = 0.35
    src = b.inputs["Base Color"].links[0].from_socket if b.inputs["Base Color"].links else None
    if src: L.new(src, cm.inputs["A"])
    else: cm.inputs["A"].default_value = b.inputs["Base Color"].default_value
    mr = N.new("ShaderNodeMapRange"); mr.inputs["To Min"].default_value = 0.75; mr.inputs["To Max"].default_value = 1.1; L.new(ab.outputs[0], mr.inputs["Value"])
    L.new(mr.outputs["Result"], cm.inputs["B"]); L.new(cm.outputs["Result"], b.inputs["Base Color"])
add_weave(fabric_m, root, 0.6)
for m_ in bpy.data.objects["Woman.female_casualsuit01"].data.materials: add_weave(m_, root, 1.0, 0.004)
fabric = grid_slab("M_Fabric", -0.06, 0.0, fabric_m, 48, 40)
epi = grid_slab("M_Epidermis", 0.0, 0.06, skin_epi)
der = grid_slab("M_Dermis", 0.06, 0.32, skin_der)
sept = slab("M_FatBed", 0.32, 4.3, sept_m)
sept.location.y = -YB / 2 - 0.9                 # behind the packed lobule layer
fas = slab("M_Fascia", 4.3, 4.42, fascia_m); fas.location.y = -YB / 2 - 0.27
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
for i in range(9):
    for j in range(4):
        fibre("M_MuscleFib_%d_%d" % (i, j), 4.49 + i * 0.112 + (0.056 if j % 2 else 0), -0.07 - j * 0.1, i * 4 + j)
musc_back = slab("M_MuscleBed", 4.42, 5.5, musc_m); musc_back.location.y = -YB / 2 - 0.3
perit = grid_slab("M_Peritoneum", 5.5, 5.56, perit_m, 24, 24)
# ---- intestines: coiled small-bowel loops behind the peritoneum, touching folds, glossy pink-grey serosa with vessels
def serosa_mat():
    m = bpy.data.materials.new("M_serosa"); m.use_nodes = True; nt = m.node_tree; N = nt.nodes; L = nt.links; b = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord")
    nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 1.6; nz.inputs["Detail"].default_value = 3
    L.new(tc.outputs["Object"], nz.inputs["Vector"])
    vo = N.new("ShaderNodeTexVoronoi"); vo.feature = 'DISTANCE_TO_EDGE'; vo.inputs["Scale"].default_value = 2.2
    mxv = N.new("ShaderNodeMix"); mxv.data_type = 'VECTOR'; mxv.inputs["Factor"].default_value = 0.35
    L.new(tc.outputs["Object"], mxv.inputs["A"]); L.new(nz.outputs["Color"], mxv.inputs["B"]); L.new(mxv.outputs["Result"], vo.inputs["Vector"])
    vr = N.new("ShaderNodeMapRange"); vr.inputs["From Min"].default_value = 0.0; vr.inputs["From Max"].default_value = 0.035
    vr.inputs["To Min"].default_value = 1.0; vr.inputs["To Max"].default_value = 0.0; L.new(vo.outputs["Distance"], vr.inputs["Value"])
    base = N.new("ShaderNodeMix"); base.data_type = 'RGBA'; L.new(nz.outputs["Fac"], base.inputs["Factor"])
    base.inputs["A"].default_value = (0.30, 0.10, 0.11, 1); base.inputs["B"].default_value = (0.46, 0.22, 0.22, 1)
    ves = N.new("ShaderNodeMix"); ves.data_type = 'RGBA'; L.new(vr.outputs["Result"], ves.inputs["Factor"])
    L.new(base.outputs["Result"], ves.inputs["A"]); ves.inputs["B"].default_value = (0.45, 0.03, 0.05, 1)
    L.new(ves.outputs["Result"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.35; b.inputs["Coat Weight"].default_value = 0.8; b.inputs["Coat Roughness"].default_value = 0.1
    b.inputs["Subsurface Weight"].default_value = 0.25; b.inputs["Subsurface Radius"].default_value = (0.6, 0.15, 0.12)
    bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.25; L.new(vr.outputs["Result"], bp.inputs["Height"]); L.new(bp.outputs["Normal"], b.inputs["Normal"])
    return m
serosa = serosa_mat()
R_G = 0.46
def tube(name, pts, rad, m_, cyc=False):
    cu = bpy.data.curves.new(name, 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = rad; cu.bevel_resolution = 5; cu.resolution_u = 10
    sp = cu.splines.new('NURBS'); sp.points.add(len(pts) - 1)
    for p, c in zip(sp.points, pts): p.co = (*c, 1)
    sp.use_endpoint_u = True; sp.order_u = 4
    o = bpy.data.objects.new(name, cu); link(o, MACRO); o.parent = root; cu.materials.append(m_)
    return o
gut_objs = []
# real CC-BY bowel model ("Small and large intestine" by antonia.sundberg), mirrored into the macro frame behind the peritoneum,
# cropped to the cavity (x 5.62..12) and kept behind the cut plane (y < -0.1)
import os as _os
_before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=_os.path.join(_os.path.dirname(_os.path.abspath(out)), "assets/models/guts.glb"))
_new = [o for o in bpy.data.objects if o not in _before]
bpy.context.view_layer.update()
GS = 13.0
bm = bmesh.new()
for o in _new:
    if o.type != 'MESH': continue
    me_ = o.data.copy(); me_.transform(o.matrix_world); bm.from_mesh(me_); bpy.data.meshes.remove(me_)
for o in _new: bpy.data.objects.remove(o, do_unlink=True)
M_ = Matrix.Rotation(math.pi, 4, 'Z') @ Matrix.Diagonal((GS, GS, GS, 1))
bm.transform(M_)
cx_ = sum(v.co.x for v in bm.verts) / len(bm.verts); cz_ = sum(v.co.z for v in bm.verts) / len(bm.verts); ymax = max(v.co.y for v in bm.verts)
for v in bm.verts: v.co += Vector((7.6 - cx_, -0.12 - ymax, -cz_))
bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.x < 5.62 or abs(v.co.z) > ZH + 1.5], context='VERTS')
gme = bpy.data.meshes.new("GutReal"); bm.to_mesh(gme); bm.free()
for p_ in gme.polygons: p_.use_smooth = True
gme.materials.clear(); gme.materials.append(serosa)
gut_objs.append(mobj("M_GutReal", gme, ()))
print("GUT verts", len(gme.vertices))
# mesentery sheet with vessels behind the loops, and a dark body cavity behind that
mes_m = mat("M_mesentery", (0.55, 0.22, 0.2), 0.3, sss=0.4, coat=0.6, noise_amt=0.5, nscale=3, bump=0.3)
mes = slab("M_Mesentery", 5.6, 12.0, mes_m, zh=ZH + 2); mes.location.y = -YB / 2 - 9.0
cav = slab("M_GutBed", 5.6, 13.0, mat("M_cavity", (0.12, 0.03, 0.03), 0.5, sss=0.2, noise_amt=0.5, nscale=2), zh=ZH + 2)
cav.location.y = -YB / 2 - 10.5
for v in range(7):
    z0 = random.uniform(-ZH + 0.5, ZH - 0.5)
    pts = [(5.7 + k * 0.6, mes.location.y + YB / 2 + 0.03, z0 + 0.35 * math.sin(k * 1.4 + v)) for k in range(7)]
    tube("M_MesVessel%d" % v, pts, 0.05, vessel_r)
# ---- capillaries + small vessels over the cut face of the fat (kept off the bullet channel |z| > 0.7)
def capillary(name, p0, direction, n, step, rad, depth=0):
    pts = []; p = Vector(p0); d = Vector(direction).normalized(); ph = random.uniform(0, 6.28)
    for k in range(n):
        pts.append(tuple(p)); w = 0.55 * math.sin(k * 0.9 + ph)
        d = (d + Vector((0, 0, w * 0.9)) + Vector((random.uniform(-0.2, 0.2), 0, random.uniform(-0.45, 0.45)))).normalized()
        d.y = 0.0; d.normalize(); p = p + d * step; p.y = 0.03 + 0.02 * math.sin(k * 1.7 + ph)
        if abs(p.z) < 0.7: p.z = math.copysign(0.7, p.z if p.z != 0 else 1)
        if depth < 1 and k in (n // 3, 2 * n // 3) and random.random() < 0.8:
            capillary(name + "b%d" % k, p, (d.x, 0, d.z + random.choice((-1, 1)) * 0.9), max(4, n // 2), step * 0.8, rad * 0.65, depth + 1)
    if p.x < 4.25 and len(pts) > 3:
        tube(name, [q for q in pts if 0.36 < q[0] < 4.25] or pts, rad, vessel_r if random.random() < 0.8 else vessel_b)
for v in range(10):
    side = random.choice((-1, 1)); z0 = side * random.uniform(0.9, ZH - 0.5)
    capillary("M_Vessel%d" % v, (0.4, 0.03, z0), (1, 0, random.uniform(-0.4, 0.4)), 22, 0.18, random.choice((0.008, 0.011, 0.014)))
# ---- fat: ~8k packed, overlapping lobules (3-11 mm) instanced by geometry nodes, deformation driven live by TipCtl
lob_c = bpy.data.collections.new("LobuleProtos")          # not linked to the scene: only instanced
for k in range(6):
    bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0)
    for v in bm.verts:
        n_ = noise.noise(v.co * 1.4 + Vector((k * 3.1, k, 0)))
        v.co *= 1.0 + 0.22 * n_
        v.co.x *= 0.82
    me = bpy.data.meshes.new("Lobule%d" % k); bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = True
    me.materials.append(fat_m)
    o = bpy.data.objects.new("LobProto%d" % k, me); lob_c.objects.link(o)
pts = []; cell = 0.25; grid = {}
def gkey(c): return (int(c.x // cell), int(c.y // cell), int(c.z // cell))
tries = 0
while len(pts) < 9000 and tries < 220000:
    tries += 1
    r = random.uniform(0.07, 0.22) if random.random() < 0.8 else random.uniform(0.18, 0.26)
    c = Vector((random.uniform(0.34, 4.28), random.uniform(-1.1, 0.06 - r * 0.3), random.uniform(-ZH - 0.2, ZH + 0.2)))
    k0 = gkey(c); ok = True
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for dz in (-1, 0, 1):
                for (q, rq) in grid.get((k0[0] + dx, k0[1] + dy, k0[2] + dz), ()):
                    if (c - q).length < (r + rq) * 0.72: ok = False; break
                if not ok: break
            if not ok: break
        if not ok: break
    if ok:
        pts.append((c, r)); grid.setdefault(k0, []).append((c, r))
me = bpy.data.meshes.new("FatPoints"); me.vertices.add(len(pts)); me.vertices.foreach_set("co", [a for c, r in pts for a in c])
ar = me.attributes.new("r", 'FLOAT', 'POINT'); ar.data.foreach_set("value", [r for c, r in pts])
ap = me.attributes.new("ph", 'FLOAT', 'POINT'); ap.data.foreach_set("value", [random.uniform(0, 6.283) for _ in pts])
av = me.attributes.new("v", 'INT', 'POINT'); av.data.foreach_set("value", [random.randrange(6) for _ in pts])
fatp = mobj("M_FatPoints", me, ())
tipctl = bpy.data.objects.new("TipCtl", None); sc.collection.objects.link(tipctl); tipctl.parent = root   # x = tip depth, y = energy, z = settle wobble
ng = bpy.data.node_groups.new("FatLobulesGN", 'GeometryNodeTree')
ng.interface.new_socket(name="Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
ng.interface.new_socket(name="Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')
GN = ng.nodes; GL = ng.links
gi = GN.new("NodeGroupInput"); go = GN.new("NodeGroupOutput")
def M(op, a, b=None, c=None):
    n = GN.new("ShaderNodeMath"); n.operation = op
    for i, x in enumerate((a, b, c)):
        if x is None: continue
        if isinstance(x, (int, float)): n.inputs[i].default_value = x
        else: GL.new(x, n.inputs[i])
    return n.outputs[0]
def V(op, a, b=None, s=None):
    n = GN.new("ShaderNodeVectorMath"); n.operation = op
    GL.new(a, n.inputs[0])
    if b is not None:
        if isinstance(b, (tuple, list)): n.inputs[1].default_value = b
        else: GL.new(b, n.inputs[1])
    if s is not None:
        if isinstance(s, (int, float)): n.inputs["Scale"].default_value = s
        else: GL.new(s, n.inputs["Scale"])
    return n.outputs["Value" if op in ('LENGTH', 'DOT_PRODUCT', 'DISTANCE') else "Vector"]
def attr(name, typ='FLOAT'):
    n = GN.new("GeometryNodeInputNamedAttribute"); n.data_type = typ; n.inputs["Name"].default_value = name
    return n.outputs["Attribute"]
oi = GN.new("GeometryNodeObjectInfo"); oi.inputs["Object"].default_value = tipctl; oi.transform_space = 'RELATIVE'
tsep = GN.new("ShaderNodeSeparateXYZ"); GL.new(oi.outputs["Location"], tsep.inputs[0])
d_, e_, wob = tsep.outputs[0], tsep.outputs[1], tsep.outputs[2]
st = GN.new("GeometryNodeInputSceneTime"); t_ = st.outputs["Seconds"]
pos = GN.new("GeometryNodeInputPosition").outputs[0]
ps = GN.new("ShaderNodeSeparateXYZ"); GL.new(pos, ps.inputs[0]); cx, cy, cz = ps.outputs
r_ = attr("r"); ph = attr("ph")
radv = GN.new("ShaderNodeCombineXYZ"); GL.new(cy, radv.inputs[1]); GL.new(cz, radv.inputs[2]); radv = radv.outputs[0]
rho = V('LENGTH', radv)
rdir = V('NORMALIZE', V('ADD', radv, (0.0, 1e-4, 1e-4)))
passed = M('DIVIDE', 1.0, M('ADD', 1.0, M('EXPONENT', M('DIVIDE', M('SUBTRACT', cx, M('ADD', d_, 0.25)), 0.18))))
on = M('GREATER_THAN', t_, 3.15)
ah = M('DIVIDE', M('SUBTRACT', cx, M('ADD', d_, 0.3)), 0.4)
ahead = M('MULTIPLY', M('EXPONENT', M('MULTIPLY', M('MULTIPLY', ah, ah), -1.0)), on)
clear = M('ADD', M('MAXIMUM', 0.0, M('SUBTRACT', M('MULTIPLY_ADD', r_, 0.4, 0.42), rho)), M('MULTIPLY', 0.08, M('EXPONENT', M('DIVIDE', M('MULTIPLY', rho, rho), -1.0))))
push = M('MULTIPLY', clear, M('ADD', M('MULTIPLY', passed, 0.95), M('MULTIPLY', ahead, 0.55)))
tipv = GN.new("ShaderNodeCombineXYZ"); GL.new(d_, tipv.inputs[0]); tipv = tipv.outputs[0]
dv = V('SUBTRACT', pos, tipv); dist = V('LENGTH', dv); ddir = V('NORMALIZE', dv)
ph1 = M('MULTIPLY', M('SUBTRACT', M('DIVIDE', dist, 0.7), M('MULTIPLY', t_, 1.6)), 6.2832)
wave = M('MULTIPLY', M('MULTIPLY', M('MULTIPLY', e_, 0.14), M('SINE', ph1)), M('EXPONENT', M('DIVIDE', dist, -2.0)))
wob_t = M('MULTIPLY', M('MULTIPLY', wob, 0.07), M('MULTIPLY', M('SINE', M('ADD', M('MULTIPLY', t_, 13.8), ph)), M('EXPONENT', M('DIVIDE', dist, -2.5))))
wave = M('ADD', wave, wob_t)
hb = M('POWER', M('MAXIMUM', 0.0, M('SINE', M('MULTIPLY', t_, 8.357))), 3.0)
pulse = M('MULTIPLY', hb, 0.02)
newpos = V('ADD', V('ADD', pos, V('SCALE', rdir, s=push)), V('SCALE', ddir, s=wave))
sq = M('ADD', M('MULTIPLY', ahead, 0.42), M('MULTIPLY', M('MULTIPLY', passed, 0.16), M('EXPONENT', M('DIVIDE', rho, -0.8))))
sxv = M('MULTIPLY', r_, M('ADD', M('SUBTRACT', 1.0, sq), wave))
syz = M('MULTIPLY', r_, M('ADD', M('ADD', 1.0, M('MULTIPLY', sq, 0.5)), pulse))
scl = GN.new("ShaderNodeCombineXYZ"); GL.new(sxv, scl.inputs[0]); GL.new(syz, scl.inputs[1]); GL.new(syz, scl.inputs[2])
rot = GN.new("ShaderNodeCombineXYZ"); GL.new(ph, rot.inputs[0])
setp = GN.new("GeometryNodeSetPosition"); GL.new(gi.outputs[0], setp.inputs["Geometry"]); GL.new(newpos, setp.inputs["Position"])
ci = GN.new("GeometryNodeCollectionInfo"); ci.inputs["Collection"].default_value = lob_c; ci.inputs["Separate Children"].default_value = True
ci.inputs["Reset Children"].default_value = True; ci.transform_space = 'ORIGINAL'
iop = GN.new("GeometryNodeInstanceOnPoints")
GL.new(setp.outputs[0], iop.inputs["Points"]); GL.new(ci.outputs[0], iop.inputs["Instance"]); iop.inputs["Pick Instance"].default_value = True
GL.new(attr("v", 'INT'), iop.inputs["Instance Index"]); GL.new(rot.outputs[0], iop.inputs["Rotation"]); GL.new(scl.outputs[0], iop.inputs["Scale"])
GL.new(iop.outputs[0], go.inputs[0])
gm = fatp.modifiers.new("Lobules", 'NODES'); gm.node_group = ng
LOB = pts
# energy rings (emissive tori around the channel, keyed later)
ring_m = bpy.data.materials.new("M_ring"); ring_m.use_nodes = True; nt = ring_m.node_tree; N = nt.nodes; L = nt.links
N.remove(N["Principled BSDF"]); mo = N["Material Output"]; oi = N.new("ShaderNodeObjectInfo")
em = N.new("ShaderNodeEmission"); em.inputs["Color"].default_value = (1.0, 0.72, 0.38, 1)
ms = N.new("ShaderNodeMath"); ms.operation = 'MULTIPLY'; ms.inputs[1].default_value = 6.0; L.new(oi.outputs["Alpha"], ms.inputs[0]); L.new(ms.outputs[0], em.inputs["Strength"])
tr = N.new("ShaderNodeBsdfTransparent"); mxs = N.new("ShaderNodeMixShader")
L.new(oi.outputs["Alpha"], mxs.inputs[0]); L.new(tr.outputs[0], mxs.inputs[1]); L.new(em.outputs[0], mxs.inputs[2]); L.new(mxs.outputs[0], mo.inputs["Surface"])
bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=False, segments=64, radius1=1.0, radius2=1.0, depth=0.06)
for v in bm.verts: v.co = Matrix.Rotation(math.pi / 2, 3, 'Y') @ v.co
rme = bpy.data.meshes.new("Ring"); bm.to_mesh(rme); bm.free(); rme.materials.append(ring_m)
for i in range(12):
    o = mobj("M_Ring%02d" % i, rme, ()); o.scale = (1, 0.01, 0.01); o.color = (1, 1, 1, 0)
    sol = o.modifiers.new("sol", 'SOLIDIFY'); sol.thickness = 0.07
# entry hole decal on fabric + skin (dark ring) — appears after pierce
hole_m = mat("M_hole", (0.07, 0.025, 0.02), 0.7)
bm = bmesh.new(); bmesh.ops.create_circle(bm, cap_ends=True, segments=24, radius=0.2)
for v in bm.verts: v.co = Matrix.Rotation(math.pi / 2, 3, 'Y') @ v.co + Vector((-0.065, 0, 0))
hme = bpy.data.meshes.new("Hole"); bm.to_mesh(hme); bm.free(); hme.materials.append(hole_m)
hole = mobj("M_HoleDecal", hme, ())
th = bpy.data.objects.new("TeeHole", hme); REAL.objects.link(th); th.parent = root      # same hole on the real tee (store side of the swap)
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
cr = N.new("ShaderNodeValToRGB"); cr.color_ramp.elements[0].color = (0.01, 0.16, 0.26, 1); cr.color_ramp.elements[1].color = (0.35, 0.72, 0.85, 1)
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
