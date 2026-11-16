"""B36 PaperclipHouse: props library -> <scratch>/build/props.blend
blender -b --factory-startup --python 10_props.py
Every prop is ONE mesh object in collection PROPS, origin at its natural grip point,
up = +Z, front = -Y, custom props grip_w / bottom_z (and body_xyz on the guitar).
No text, brands or logos on any prop."""
import bpy, bmesh, math, random, os, json
from mathutils import Vector, Matrix

SCR = "/tmp/claude-0/-home-user-Muhammed/0b019bde-e3b5-5ca9-9067-8cf46a4c300e/scratchpad"
MOD = SCR + "/models"
OUT = SCR + "/build/props.blend"
R = math.radians
random.seed(36)

for o in list(bpy.data.objects): bpy.data.objects.remove(o)
for c in list(bpy.data.collections): bpy.data.collections.remove(c)
PC = bpy.data.collections.new("PROPS"); bpy.context.scene.collection.children.link(PC)
sc = bpy.context.scene

# ------------------------------------------------------------------ helpers
def mat(name, col, rough=0.4, metal=0.0, img=None, trans=0.0, ior=1.45, coat=0.0, emit=None):
    m = bpy.data.materials.get(name)
    if m: return m
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; p = nt.nodes["Principled BSDF"]
    p.inputs["Base Color"].default_value = (*col, 1)
    p.inputs["Roughness"].default_value = rough
    p.inputs["Metallic"].default_value = metal
    p.inputs["IOR"].default_value = ior
    p.inputs["Transmission Weight"].default_value = trans
    p.inputs["Coat Weight"].default_value = coat
    if img is not None:
        t = nt.nodes.new("ShaderNodeTexImage"); t.image = img; t.interpolation = 'Linear'
        nt.links.new(t.outputs["Color"], p.inputs["Base Color"])
    if trans > 0:
        m.blend_method = 'HASHED' if hasattr(m, "blend_method") else None
    return m

def new_obj(name, bm, mats):
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); PC.objects.link(o)
    for m in mats: me.materials.append(m)
    return o

def prim(kind, name, m, loc=(0, 0, 0), rot=(0, 0, 0), scl=(1, 1, 1), **kw):
    bm = bmesh.new()
    if kind == "box":
        bmesh.ops.create_cube(bm, size=1.0)
    elif kind == "cyl":
        bmesh.ops.create_cone(bm, cap_ends=True, segments=kw.get("seg", 32), radius1=1, radius2=1, depth=1)
    elif kind == "cone":
        bmesh.ops.create_cone(bm, cap_ends=True, segments=kw.get("seg", 32), radius1=1, radius2=kw.get("r2", 0.0), depth=1)
    elif kind == "sph":
        bmesh.ops.create_uvsphere(bm, u_segments=kw.get("seg", 32), v_segments=kw.get("seg", 32) // 2, radius=1)
    elif kind == "ico":
        bmesh.ops.create_icosphere(bm, subdivisions=1, radius=1)
    elif kind == "torus":
        R1, r1 = kw["R"], kw["r"]; nu, nv = kw.get("nu", 48), kw.get("nv", 12)
        vs = [[bm.verts.new(((R1 + r1 * math.cos(b)) * math.cos(a), (R1 + r1 * math.cos(b)) * math.sin(a), r1 * math.sin(b)))
               for b in [2 * math.pi * j / nv for j in range(nv)]] for a in [2 * math.pi * i / nu for i in range(nu)]]
        for i in range(nu):
            for j in range(nv):
                bm.faces.new((vs[i][j], vs[(i + 1) % nu][j], vs[(i + 1) % nu][(j + 1) % nv], vs[i][(j + 1) % nv]))
    M = Matrix.Translation(loc) @ Matrix.Rotation(rot[2], 4, 'Z') @ Matrix.Rotation(rot[1], 4, 'Y') @ Matrix.Rotation(rot[0], 4, 'X') @ Matrix.Diagonal((*scl, 1))
    bm.transform(M)
    for f in bm.faces: f.smooth = kind in ("cyl", "sph", "torus", "cone", "lathe")
    return new_obj(name, bm, [m])

def lathe(name, m, prof, axis="Z", seg=48, cap=True):
    """prof = [(r, t)] along axis; t increasing"""
    bm = bmesh.new(); rings = []
    for r, t in prof:
        ring = []
        for i in range(seg):
            a = 2 * math.pi * i / seg; c, s = r * math.cos(a), r * math.sin(a)
            p = (c, s, t) if axis == "Z" else (c, t, s) if axis == "Y" else (t, c, s)
            ring.append(bm.verts.new(p))
        rings.append(ring)
    for a, b in zip(rings, rings[1:]):
        for i in range(seg):
            j = (i + 1) % seg
            try: bm.faces.new((a[i], a[j], b[j], b[i]))
            except ValueError: pass
    if cap:
        for ring in (rings[0], rings[-1]):
            if prof[0][0] > 1e-6 or ring is rings[-1]:
                try: bm.faces.new(ring)
                except ValueError: pass
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    for f in bm.faces: f.smooth = True
    return new_obj(name, bm, [m])

def join(objs, name):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs:
        if o.name not in PC.objects: PC.objects.link(o)
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    o = bpy.context.view_layer.objects.active
    o.name = name; o.data.name = name
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    return o

def bbox(o):
    vs = [o.matrix_world @ v.co for v in o.data.vertices]
    lo = Vector([min(v[i] for v in vs) for i in range(3)]); hi = Vector([max(v[i] for v in vs) for i in range(3)])
    return lo, hi

def finish(o, name, grip, grip_w):
    """set origin at world point grip, store grip_w / bottom_z"""
    o.name = name; o.data.name = name
    o.data.transform(Matrix.Translation(-Vector(grip))); o.location = (0, 0, 0)
    lo, hi = bbox(o)
    o["grip_w"] = float(grip_w); o["bottom_z"] = float(-lo.z)
    if len(o.data.polygons) > 60000:
        d = o.modifiers.new("dec", 'DECIMATE'); d.ratio = 60000 / len(o.data.polygons)
        bpy.context.view_layer.objects.active = o; bpy.ops.object.modifier_apply(modifier="dec")
    for c in list(o.users_collection):
        if c != PC: c.objects.unlink(o)
    if o.name not in PC.objects: PC.objects.link(o)
    print("PROP", name, "dims", tuple(round(x, 3) for x in (hi - lo)), "faces", len(o.data.polygons), "bottom_z", round(-lo.z, 3))
    return o

def imp(path):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    ms = [o for o in new if o.type == 'MESH']
    for o in ms:
        mw = o.matrix_world.copy(); o.parent = None; o.matrix_world = mw
    for o in new:
        if o.type != 'MESH': bpy.data.objects.remove(o)
    bpy.ops.object.select_all(action='DESELECT')
    for o in ms: o.select_set(True)
    bpy.context.view_layer.objects.active = ms[0]
    if len(ms) > 1: bpy.ops.object.join()
    o = bpy.context.view_layer.objects.active
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    return o

def xform(o, M):
    o.data.transform(M); o.data.update()

def make_img(name, w, h, draw):
    """draw(px, w, h) fills a flat RGBA float list; returns packed image"""
    img = bpy.data.images.new(name, w, h, alpha=False)
    px = [1.0] * (w * h * 4)
    draw(px, w, h)
    img.pixels.foreach_set(px); img.pack()
    return img

def rect(px, w, h, x0, y0, x1, y1, col):
    for y in range(max(0, y0), min(h, y1)):
        for x in range(max(0, x0), min(w, x1)):
            i = (y * w + x) * 4; px[i:i + 3] = col

def planar_uv(o, ax_u, ax_v):
    """UV from bbox along two world axes (0=x,1=y,2=z)"""
    lo, hi = bbox(o); me = o.data
    uv = me.uv_layers.new(name="UVMap") if not me.uv_layers else me.uv_layers[0]
    for poly in me.polygons:
        for li in poly.loop_indices:
            co = me.vertices[me.loops[li].vertex_index].co
            uv.data[li].uv = ((co[ax_u] - lo[ax_u]) / max(1e-6, hi[ax_u] - lo[ax_u]), (co[ax_v] - lo[ax_v]) / max(1e-6, hi[ax_v] - lo[ax_v]))

def retint(o, fn):
    """fn(material) -> rebuild each slot material for the clean look"""
    for i, m in enumerate(o.data.materials):
        o.data.materials[i] = fn(m)

def tex_of(m):
    if not m or not m.use_nodes: return None
    for n in m.node_tree.nodes:
        if n.type == 'TEX_IMAGE' and n.image: return n.image
    return None

def tinted(name, img, tint=(1, 1, 1), hue=0.5, sat=1.0, rough=0.4, metal=0.0, val=1.0):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; p = nt.nodes["Principled BSDF"]
    p.inputs["Roughness"].default_value = rough; p.inputs["Metallic"].default_value = metal
    t = nt.nodes.new("ShaderNodeTexImage"); t.image = img
    hs = nt.nodes.new("ShaderNodeHueSaturation"); hs.inputs["Hue"].default_value = hue; hs.inputs["Saturation"].default_value = sat
    hs.inputs["Value"].default_value = val
    mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs["Factor"].default_value = 1.0
    mx.inputs[7].default_value = (*tint, 1)
    nt.links.new(t.outputs["Color"], hs.inputs["Color"]); nt.links.new(hs.outputs["Color"], mx.inputs[6])
    nt.links.new(mx.outputs[2], p.inputs["Base Color"])
    return m

# ------------------------------------------------------------------ materials
RED = mat("M_ClipRed", (0.85, 0.03, 0.03), 0.35, coat=0.6)
FISHG = mat("M_FishGreen", (0.05, 0.65, 0.45), 0.4, coat=0.5)
FISHB = mat("M_FishBlue", (0.05, 0.35, 0.9), 0.4)
WHITE = mat("M_White", (0.92, 0.92, 0.92), 0.45)
BLACK = mat("M_Black", (0.02, 0.02, 0.025), 0.4)
STEEL = mat("M_Steel", (0.62, 0.63, 0.66), 0.35, 1.0)
DSTEEL = mat("M_DarkSteel", (0.18, 0.18, 0.2), 0.4, 1.0)
BRASS = mat("M_Brass", (0.85, 0.62, 0.25), 0.35, 1.0)
GOLD = mat("M_Gold", (0.95, 0.72, 0.3), 0.35, 1.0)
CAMPG = mat("M_CampGreen", (0.1, 0.45, 0.18), 0.45, 0.3)
MBLACK = mat("M_MatteBlack", (0.03, 0.03, 0.035), 0.55)
MGREY = mat("M_MatteGrey", (0.25, 0.26, 0.28), 0.5)
WOODBLK = mat("M_BlackWood", (0.035, 0.025, 0.02), 0.4, coat=0.5)
SNOW = mat("M_Snow", (0.95, 0.97, 1.0), 0.6)
GLASS = mat("M_Glass", (1, 1, 1), 0.02, trans=1.0, ior=1.45)
SKIN = mat("M_FigSkin", (0.85, 0.6, 0.48), 0.5)
FIGBLK = mat("M_FigBlack", (0.03, 0.03, 0.04), 0.45)
BLUETAG = mat("M_BlueTag", (0.05, 0.3, 0.85), 0.4)
SILVER = mat("M_Silver", (0.85, 0.86, 0.88), 0.35, 1.0)
LBLUE = mat("M_PhotoBlue", (0.45, 0.72, 0.95), 0.5)

PROPS = []

# ------------------------------------------------------------------ P_Paperclip (long axis Y, flat on XY)
def paperclip():
    def arc(cx, cy, r, a0, a1, n=16):
        return [(cx + r * math.cos(a0 + (a1 - a0) * i / n), cy + r * math.sin(a0 + (a1 - a0) * i / n)) for i in range(n + 1)]
    pts = [(2.0, 10.0)] + arc(0, 40, 2.0, 0, math.pi) + arc(1.25, 6, 3.25, math.pi, 2 * math.pi) + arc(0, 44, 4.5, 0, math.pi) + [(-4.5, 14.0)]
    cu = bpy.data.curves.new("clip", 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = 0.6; cu.bevel_resolution = 3; cu.use_fill_caps = True
    sp = cu.splines.new('POLY'); sp.points.add(len(pts) - 1)
    for p, (x, y) in zip(sp.points, pts): p.co = (x, y, 0, 1)
    o = bpy.data.objects.new("clip", cu); PC.objects.link(o)
    bpy.context.view_layer.objects.active = o; bpy.ops.object.select_all(action='DESELECT'); o.select_set(True)
    bpy.ops.object.convert(target='MESH'); o = bpy.context.view_layer.objects.active
    lo, hi = bbox(o); s = 0.05 / (hi.y - lo.y)        # 50 mm, wire 1.2 mm -> 0.6*s*2
    xform(o, Matrix.Diagonal((s, s, s, 1)) @ Matrix.Translation(-(lo + hi) / 2))
    o.data.materials.clear(); o.data.materials.append(RED)
    for f in o.data.polygons: f.use_smooth = True
    # grip: pinched at the lower third
    return finish(o, "P_Paperclip", (0, -0.012, 0), 0.01)

# ------------------------------------------------------------------ P_FishPen (long axis Y, nib at -Y)
def fishpen():
    prof = [(0.0003, -0.070), (0.0008, -0.068), (0.0028, -0.060), (0.0045, -0.056), (0.0072, -0.045), (0.0088, -0.030),
            (0.0090, -0.015), (0.0082, 0.005), (0.0066, 0.025), (0.0048, 0.040), (0.0036, 0.050), (0.0032, 0.054)]
    body = lathe("fb", FISHG, prof, axis="Y", seg=40)
    nib = lathe("nib", STEEL, [(0.0002, -0.0715), (0.0006, -0.0705), (0.0016, -0.064), (0.0018, -0.062)], axis="Y", seg=20)
    # body slightly flattened sideways (fish shape)
    xform(body, Matrix.Diagonal((0.8, 1, 1, 1)))
    # tail fin: vertical V in YZ plane
    bm = bmesh.new()
    v = [bm.verts.new(p) for p in [(-0.0007, 0.050, 0.0), (-0.0007, 0.072, 0.014), (-0.0007, 0.066, 0.0), (-0.0007, 0.072, -0.014),
                                   (0.0007, 0.050, 0.0), (0.0007, 0.072, 0.014), (0.0007, 0.066, 0.0), (0.0007, 0.072, -0.014)]]
    bm.faces.new(v[0:4][::-1]); bm.faces.new(v[4:8])
    for i in range(4): bm.faces.new((v[i], v[(i + 1) % 4], v[4 + (i + 1) % 4], v[4 + i]))
    tail = new_obj("tail", bm, [FISHB])
    bm = bmesh.new()
    v = [bm.verts.new(p) for p in [(-0.0006, -0.025, 0.0080), (-0.0006, -0.002, 0.0145), (-0.0006, 0.012, 0.0072),
                                   (0.0006, -0.025, 0.0080), (0.0006, -0.002, 0.0145), (0.0006, 0.012, 0.0072)]]
    bm.faces.new(v[0:3][::-1]); bm.faces.new(v[3:6])
    for i in range(3): bm.faces.new((v[i], v[(i + 1) % 3], v[3 + (i + 1) % 3], v[3 + i]))
    dorsal = new_obj("dorsal", bm, [FISHB])
    parts = [body, nib, tail, dorsal]
    for sx in (-1, 1):
        parts.append(prim("sph", "eyeW", WHITE, (sx * 0.0058, -0.047, 0.0025), scl=(0.0018,) * 3, seg=16))
        parts.append(prim("sph", "eyeB", BLACK, (sx * 0.0068, -0.0475, 0.0026), scl=(0.0010,) * 3, seg=12))
    # small fins (pectoral)
    for sx in (-1, 1):
        parts.append(prim("sph", "pec", FISHB, (sx * 0.0072, -0.030, -0.004), scl=(0.0012, 0.006, 0.003), seg=12))
    o = join(parts, "P_FishPen")
    return finish(o, "P_FishPen", (0, -0.015, 0), 0.016)

# ------------------------------------------------------------------ P_Doorknob
def doorknob():
    o = imp(MOD + "/doorknob.glb")
    lo, hi = bbox(o); c = (lo + hi) / 2
    # long axis is Y (knob + rosette). measure radius per end to find the knob ball
    vs = [v.co - c for v in o.data.vertices]
    L = hi.y - lo.y
    def rmax(sel): return max(((v.x ** 2 + v.z ** 2) ** 0.5 for v in vs if sel(v)), default=0)
    rA = rmax(lambda v: v.y > L * 0.3); rB = rmax(lambda v: v.y < -L * 0.3)
    print("KNOB ends radius", rA, rB, "L", L)
    xform(o, Matrix.Translation(-c))
    # orient knob ball toward -Y (front), rosette at +Y
    knob_pos = rA < rB   # assume the end with the smaller max radius is the rosette? decide by vertex mass
    nA = sum(1 for v in vs if v.y > L * 0.3); nB = sum(1 for v in vs if v.y < -L * 0.3)
    print("KNOB ends verts", nA, nB)
    o["_rA"] = rA; o["_rB"] = rB
    o.data.materials.clear(); o.data.materials.append(BRASS)
    for f in o.data.polygons: f.use_smooth = True
    return o

# ------------------------------------------------------------------ P_CampStove
def campstove():
    W, D, H = 0.45, 0.28, 0.10
    parts = [prim("box", "case", CAMPG, (0, 0, 0), scl=(W, D, H))]
    bv = parts[0].modifiers.new("bv", 'BEVEL'); bv.width = 0.008; bv.segments = 3
    bpy.context.view_layer.objects.active = parts[0]; bpy.ops.object.modifier_apply(modifier="bv")
    # top deck (dark steel tray)
    parts.append(prim("box", "deck", DSTEEL, (0, -0.005, H / 2 + 0.002), scl=(W - 0.03, D - 0.05, 0.004)))
    # lid open upright at back
    parts.append(prim("box", "lid", CAMPG, (0, D / 2 + 0.006, H / 2 + 0.135), scl=(W, 0.012, 0.27)))
    # side wind flaps
    for sx in (-1, 1):
        parts.append(prim("box", "flap", CAMPG, (sx * (W / 2 - 0.004), 0.02, H / 2 + 0.06), scl=(0.008, D - 0.06, 0.12)))
    for bx in (-0.11, 0.11):
        parts.append(prim("torus", "burner", BLACK, (bx, -0.005, H / 2 + 0.012), R=0.045, r=0.006))
        parts.append(prim("cyl", "cap", DSTEEL, (bx, -0.005, H / 2 + 0.01), scl=(0.03, 0.03, 0.012)))
        for a in (0, 60, 120):
            parts.append(prim("box", "grate", BLACK, (bx, -0.005, H / 2 + 0.03), rot=(0, 0, R(a)), scl=(0.13, 0.006, 0.006)))
    for bx in (-0.11, 0.11):
        parts.append(prim("cyl", "knob", BLACK, (bx, -D / 2 - 0.012, 0.0), rot=(R(90), 0, 0), scl=(0.016, 0.016, 0.024)))
    # carry latches
    for sx in (-1, 1):
        parts.append(prim("box", "latch", DSTEEL, (sx * 0.17, -D / 2 - 0.004, 0.02), scl=(0.03, 0.008, 0.02)))
    o = join(parts, "P_CampStove")
    return finish(o, "P_CampStove", (0, 0, 0), W)

# ------------------------------------------------------------------ P_Generator
def generator():
    o = imp(MOD + "/generator.glb")
    lo, hi = bbox(o); s = 0.55 / (hi.x - lo.x)
    xform(o, Matrix.Diagonal((s, s, s, 1)) @ Matrix.Translation(Vector((-(lo.x + hi.x) / 2, -(lo.y + hi.y) / 2, -lo.z))))
    img = None
    for m in o.data.materials:
        img = img or tex_of(m)
    o.data.materials.clear()
    if img:
        o.data.materials.append(tinted("M_Generator", img, (1, 1, 1), hue=0.5, sat=1.15, rough=0.4, val=1.05))
    else:
        o.data.materials.append(mat("M_GenRed", (0.8, 0.05, 0.03), 0.4))
    lo, hi = bbox(o)
    # top handle bar: highest verts centre
    top = [v.co for v in o.data.vertices if v.co.z > hi.z - 0.015]
    g = sum(top, Vector()) / len(top)
    return finish(o, "P_Generator", (g.x, g.y, hi.z - 0.012), 0.25)

# ------------------------------------------------------------------ P_Keg
def keg():
    prof = [(0.0, 0.0), (0.17, 0.0), (0.19, 0.005), (0.19, 0.035), (0.183, 0.04), (0.2, 0.05), (0.2, 0.105), (0.207, 0.112),
            (0.207, 0.128), (0.2, 0.135), (0.202, 0.205), (0.2, 0.275), (0.207, 0.282), (0.207, 0.298), (0.2, 0.305),
            (0.2, 0.36), (0.183, 0.37), (0.19, 0.375), (0.19, 0.41), (0.182, 0.41), (0.182, 0.38), (0.12, 0.372), (0.0, 0.37)]
    body = lathe("keg", STEEL, prof, seg=64, cap=False)
    parts = [body]
    # hand holes in the top chime: dark slots on the outer chime wall, front and back
    for a in (90, 270):
        x, y = 0.191 * math.cos(R(a)), 0.191 * math.sin(R(a))
        parts.append(prim("box", "hole", MBLACK, (x, y, 0.393), rot=(0, 0, R(a)), scl=(0.004, 0.11, 0.022)))
    # spear / valve
    parts.append(prim("cyl", "valve", DSTEEL, (0, 0, 0.385), scl=(0.035, 0.035, 0.03)))
    parts.append(prim("cyl", "valvetop", STEEL, (0, 0, 0.402), scl=(0.022, 0.022, 0.01)))
    o = join(parts, "P_Keg")
    return finish(o, "P_Keg", (0, 0, 0.405), 0.30)

# ------------------------------------------------------------------ P_Snowmobile
def snowmobile():
    o = imp(MOD + "/snowmobile.glb")
    lo, hi = bbox(o)
    s = 3.0 / (hi.y - lo.y)
    xform(o, Matrix.Diagonal((s, s, s, 1)) @ Matrix.Translation(Vector((-(lo.x + hi.x) / 2, -(lo.y + hi.y) / 2, -lo.z))))
    # recolour: hue-shift the orange body to blue; keep black / glass
    new = []
    for m in o.data.materials:
        img = tex_of(m)
        if m and "Glass" in m.name:
            new.append(mat("M_SnowGlass", (0.25, 0.35, 0.45), 0.1, trans=0.6))
        elif img:
            new.append(tinted("M_Snowmobile_" + m.name, img, (1, 1, 1), hue=0.08, sat=1.2, rough=0.4))
        else:
            new.append(mat("M_SnowBlue", (0.03, 0.25, 0.9), 0.4, coat=0.4))
    o.data.materials.clear()
    for m in new: o.data.materials.append(m)
    return o

# ------------------------------------------------------------------ P_Van (vanB = Vito panel van)
def van():
    o = imp(MOD + "/vanB.glb")
    lo, hi = bbox(o); s = 5.0 / (hi.x - lo.x)
    # long axis X, front at +X -> rotate -90 deg so front = -Y
    xform(o, Matrix.Rotation(R(-90), 4, 'Z') @ Matrix.Diagonal((s, s, s, 1)) @
          Matrix.Translation(Vector((-(lo.x + hi.x) / 2, -(lo.y + hi.y) / 2, -lo.z))))
    img = tex_of(o.data.materials[0])
    if img:
        W_, H_ = img.size; px = list(img.pixels)
        def samp(x, y):
            i = ((H_ - 1 - y) * W_ + x) * 4; return px[i:i + 3]
        def paint(x0, y0, x1, y1, col):
            for y in range(y0, y1):
                for x in range(x0, x1):
                    i = ((H_ - 1 - y) * W_ + x) * 4; px[i:i + 3] = col
        paint(188, 408, 248, 468, samp(150, 440))      # grille badge -> grille colour
        paint(585, 458, 695, 480, samp(620, 520))      # rear maker name
        paint(445, 482, 490, 500, samp(470, 530))      # rear model text L
        paint(645, 482, 705, 500, samp(670, 530))      # rear model text R
        paint(822, 396, 864, 434, samp(842, 385))      # wheel cap centre badge
        img.pixels.foreach_set(px); img.pack()
    body = tinted("M_VanBody", img, (0.12, 0.42, 0.95), hue=0.5, sat=1.0, rough=0.38) if img else mat("M_VanBody", (0.4, 0.7, 1.0), 0.38)
    side = body.copy(); side.name = "VanSide"
    o.data.materials.clear(); o.data.materials.append(body); o.data.materials.append(side)
    lo, hi = bbox(o)
    # side panel faces: normals +-X, between wheel arches height and window line, rear 2/3 (cargo)
    for p in o.data.polygons:
        c = p.center
        if abs(p.normal.x) > 0.85 and 0.55 < c.z < 1.35 and c.y > lo.y + 1.6 and c.y < hi.y - 0.35:
            p.material_index = 1
    print("VAN side faces", sum(1 for p in o.data.polygons if p.material_index == 1), "img", img.name if img else None,
          img.size[:] if img else None)
    return finish(o, "P_Van", (0, 0, 0), 0)

# ------------------------------------------------------------------ paper textures
def contract_img():
    def d(px, w, h):
        g = [0.62, 0.63, 0.66]
        rect(px, w, h, 60, h - 80, 300, h - 64, [0.35, 0.36, 0.4])     # title bar
        y = h - 120
        for k in range(16):
            ln = w - 120 - (random.randint(0, 120) if k % 5 == 4 else 0)
            rect(px, w, h, 60, y, ln, y + 7, g); y -= 22
            if k % 5 == 4: y -= 14
        rect(px, w, h, 60, 90, 220, 93, [0.4, 0.4, 0.45])               # signature line
        rect(px, w, h, 260, 90, 380, 93, [0.4, 0.4, 0.45])
        for t in range(160):                                              # blue squiggle
            x = 70 + t; yy = int(105 + 10 * math.sin(t * 0.18) + 4 * math.sin(t * 0.5))
            rect(px, w, h, x, yy, x + 3, yy + 3, [0.05, 0.15, 0.7])
    return make_img("T_Contract", 420, 594, d)

def contract():
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=8, y_segments=12, size=0.5)
    bm.transform(Matrix.Diagonal((0.21, 0.297, 1, 1)))
    for v in bm.verts: v.co.z = 0.006 * (2 * v.co.x / 0.21) ** 2       # slight curl
    o = new_obj("contract", bm, [mat("M_Contract", (1, 1, 1), 0.6, img=contract_img())])
    planar_uv(o, 0, 1)
    sol = o.modifiers.new("s", 'SOLIDIFY'); sol.thickness = 0.001
    bpy.context.view_layer.objects.active = o; bpy.ops.object.modifier_apply(modifier="s")
    return finish(o, "P_Contract", (0.085, -0.125, 0.004), 0.004)

def pen2():
    parts = [prim("cyl", "b", BLACK, (0, 0, 0), rot=(R(90), 0, 0), scl=(0.0045, 0.0045, 0.13), seg=24),
             prim("cone", "t", STEEL, (0, -0.072, 0), rot=(R(90), 0, 0), scl=(0.0045, 0.0045, 0.014), seg=24, r2=0.0)]
    # cone points along +Z before rotation; rotation X+90 maps +Z -> -Y (tip forward)
    parts.append(prim("box", "clip", STEEL, (0, 0.04, 0.005), scl=(0.002, 0.04, 0.002)))
    o = join(parts, "P_Pen2")
    return finish(o, "P_Pen2", (0, -0.03, 0), 0.009)

def condokeys():
    k = imp(MOD + "/key.glb")
    lo, hi = bbox(k); s = 0.06 / (hi.x - lo.x)
    # key flat in XZ? dims (8.9, 0.15, 3.8) -> long X, flat Y thin. put bow (ring hole end) at origin, blade pointing -Z
    xform(k, Matrix.Diagonal((s, s, s, 1)) @ Matrix.Translation(-(lo + hi) / 2))
    lo, hi = bbox(k)
    # which end is the bow? the wider end along Z
    def width(sel): return max((v.co.z for v in k.data.vertices if sel(v.co)), default=0) - min((v.co.z for v in k.data.vertices if sel(v.co)), default=0)
    wl = width(lambda c: c.x < lo.x + 0.01); wh = width(lambda c: c.x > hi.x - 0.01)
    bow_x = lo.x if wl > wh else hi.x
    # rotate so bow is up (+Z), blade down
    ang = R(90) if bow_x > 0 else R(-90)
    xform(k, Matrix.Rotation(ang, 4, 'Y'))
    lo, hi = bbox(k)
    xform(k, Matrix.Translation(Vector((0, 0, -hi.z - 0.012))))     # bow top just under the ring bottom-ish
    k.data.materials.clear(); k.data.materials.append(SILVER)
    k2 = k.copy(); k2.data = k.data.copy(); PC.objects.link(k2)
    xform(k, Matrix.Rotation(R(14), 4, 'Y')); xform(k2, Matrix.Rotation(R(-22), 4, 'Y') @ Matrix.Translation((0, 0.003, 0)))
    ring = prim("torus", "ring", STEEL, (0, 0, -0.004), rot=(R(90), 0, 0), R=0.015, r=0.0012)
    tag = prim("box", "tag", BLUETAG, (0.0, 0.002, -0.045), rot=(0, R(-40), 0), scl=(0.02, 0.003, 0.034))
    tl = prim("box", "tagl", STEEL, (0.012, 0.002, -0.026), rot=(0, R(-40), 0), scl=(0.002, 0.002, 0.012))
    o = join([ring, k, k2, tag, tl], "P_CondoKeys")
    return finish(o, "P_CondoKeys", (0, 0, 0.011), 0.01)

def guitar():
    o = imp(MOD + "/guitar.glb")
    lo, hi = bbox(o); s = 1.0 / (hi.z - lo.z); c = (lo + hi) / 2
    xform(o, Matrix.Diagonal((s, s, s, 1)) @ Matrix.Translation(Vector((-c.x, -c.y, -lo.z))))
    # front (sound hole / strings) should face -Y: test which side the strings are on (max |y| side of neck verts)
    neck_idx = [i for i, m in enumerate(o.data.materials) if m and "neck" in m.name.lower()]
    body_idx = [i for i, m in enumerate(o.data.materials) if m and "body" in m.name.lower()]
    nv = set(); bv = set()
    for p in o.data.polygons:
        (nv if p.material_index in neck_idx else bv).update(p.vertices)
    V = o.data.vertices
    bz = [V[i].co for i in bv]; blo = Vector([min(v[k] for v in bz) for k in range(3)]); bhi = Vector([max(v[k] for v in bz) for k in range(3)])
    lo, hi = bbox(o)
    neck_mid = Vector((0, 0, (bhi.z + hi.z) / 2))
    # neck centre y at that height
    near = [V[i].co for i in nv if abs(V[i].co.z - neck_mid.z) < 0.03]
    if near: neck_mid.x = sum(v.x for v in near) / len(near); neck_mid.y = sum(v.y for v in near) / len(near)
    body_c = (blo + bhi) / 2
    new = []
    for i, m in enumerate(o.data.materials):
        if i in body_idx: new.append(mat("M_GuitarBlack", (0.015, 0.015, 0.02), 0.35, coat=1.0))
        else:
            img = tex_of(m)
            new.append(tinted("M_GuitarNeck", img, (1, 1, 1), hue=0.5, sat=0.5, val=0.4, rough=0.4) if img else mat("M_GuitarNeckS", (0.35, 0.2, 0.1), 0.45))
    o.data.materials.clear()
    for m in new: o.data.materials.append(m)
    o = finish(o, "P_Guitar", neck_mid, 0.05)
    o["body_xyz"] = list(body_c - neck_mid)
    return o

def snowglobe():
    parts = [lathe("base", WOODBLK, [(0.0, 0.0), (0.05, 0.0), (0.05, 0.004), (0.047, 0.012), (0.044, 0.03), (0.036, 0.032), (0.0, 0.032)], seg=48)]
    parts.append(prim("torus", "band", GOLD, (0, 0, 0.022), R=0.0455, r=0.0025))
    parts.append(prim("sph", "glass", GLASS, (0, 0, 0.073), scl=(0.045,) * 3, seg=48))
    parts.append(prim("sph", "mound", SNOW, (0, 0, 0.036), scl=(0.036, 0.036, 0.012), seg=32))
    for k, sx in enumerate((-1, 1)):
        x = sx * 0.012; z0 = 0.044
        for lx in (-0.0025, 0.0025):
            parts.append(prim("cyl", "leg", FIGBLK, (x + lx, 0, z0 + 0.006), scl=(0.0018, 0.0018, 0.012), seg=12))
        parts.append(prim("box", "torso", FIGBLK, (x, 0, z0 + 0.0165), scl=(0.009, 0.005, 0.011)))
        for ax in (-1, 1):
            parts.append(prim("cyl", "arm", FIGBLK, (x + ax * 0.0058, -0.001, z0 + 0.016), rot=(0, ax * R(15), 0), scl=(0.0014, 0.0014, 0.01), seg=10))
        parts.append(prim("sph", "head", SKIN, (x, 0, z0 + 0.0265), scl=(0.0035,) * 3, seg=16))
        parts.append(prim("sph", "hair", FIGBLK, (x, 0.0007, z0 + 0.0282), scl=(0.0039, 0.0037, 0.0028), seg=16))
        if k == 1:
            parts.append(prim("sph", "gbody", RED, (x - 0.002, -0.004, z0 + 0.014), rot=(0, R(55), 0), scl=(0.0045, 0.0012, 0.0055), seg=12))
            parts.append(prim("box", "gneck", FIGBLK, (x - 0.008, -0.004, z0 + 0.019), rot=(0, R(55), 0), scl=(0.0012, 0.0008, 0.012)))
    for i in range(40):
        while True:
            p = Vector((random.uniform(-1, 1), random.uniform(-1, 1), random.uniform(-1, 1)))
            if p.length < 1: break
        p = p * 0.036 + Vector((0, 0, 0.076))
        if p.z < 0.05: p.z += 0.03
        parts.append(prim("ico", "flake", SNOW, tuple(p), scl=(0.0011,) * 3))
    o = join(parts, "P_SnowGlobe")
    return finish(o, "P_SnowGlobe", (0, 0, 0), 0.1)

def moviecamera():
    parts = []
    head = Vector((0, 0, 1.30))
    for a in (90, 210, 330):
        foot = Vector((0.42 * math.cos(R(a)), 0.42 * math.sin(R(a)), 0.0))
        d = head - foot; L = d.length
        rot = d.to_track_quat('Z', 'Y').to_euler()
        parts.append(prim("cyl", "leg", MGREY, tuple((head + foot) / 2), rot=tuple(rot), scl=(0.016, 0.016, L), seg=12))
        parts.append(prim("sph", "foot", MBLACK, tuple(foot + Vector((0, 0, 0.012))), scl=(0.022, 0.022, 0.012), seg=12))
    parts.append(prim("cyl", "hub", MBLACK, tuple(head), scl=(0.06, 0.06, 0.06)))
    parts.append(prim("box", "plate", MGREY, (0, 0, 1.345), scl=(0.16, 0.24, 0.03)))
    parts.append(prim("box", "body", MBLACK, (0, 0, 1.47), scl=(0.16, 0.32, 0.22)))
    bv = parts[-1].modifiers.new("bv", 'BEVEL'); bv.width = 0.01; bv.segments = 2
    bpy.context.view_layer.objects.active = parts[-1]; bpy.ops.object.modifier_apply(modifier="bv")
    for y in (-0.09, 0.11):
        parts.append(prim("cyl", "reel", MGREY, (0, y, 1.68), rot=(0, R(90), 0), scl=(0.12, 0.12, 0.03), seg=40))
        parts.append(prim("cyl", "reelhub", STEEL, (0, y, 1.68), rot=(0, R(90), 0), scl=(0.025, 0.025, 0.05), seg=20))
    parts.append(prim("box", "mag", MBLACK, (0, 0.01, 1.6), scl=(0.05, 0.2, 0.05)))
    parts.append(prim("cyl", "lens", MBLACK, (0, -0.22, 1.47), rot=(R(90), 0, 0), scl=(0.05, 0.05, 0.13), seg=32))
    parts.append(prim("cyl", "lensring", STEEL, (0, -0.24, 1.47), rot=(R(90), 0, 0), scl=(0.054, 0.054, 0.012), seg=32))
    parts.append(prim("cyl", "glass", mat("M_LensGlass", (0.05, 0.08, 0.15), 0.1, 0.5), (0, -0.287, 1.47), rot=(R(90), 0, 0), scl=(0.043, 0.043, 0.004), seg=32))
    parts.append(prim("box", "hood", MBLACK, (0, -0.32, 1.47), scl=(0.15, 0.04, 0.12)))
    parts.append(prim("cyl", "vf", MBLACK, (0.1, 0.15, 1.5), rot=(R(90), 0, 0), scl=(0.022, 0.022, 0.12), seg=16))
    parts.append(prim("cyl", "handle", MGREY, (0, 0.25, 1.33), rot=(R(-70), 0, 0), scl=(0.012, 0.012, 0.35), seg=12))
    o = join(parts, "P_MovieCamera")
    return finish(o, "P_MovieCamera", (0, 0, 0), 0.05)

def clapper():
    def stick(name, z):
        parts = [prim("box", name, MBLACK, (0, 0, z), scl=(0.28, 0.008, 0.03))]
        for k in range(6):
            x = -0.115 + k * 0.046
            parts.append(prim("box", name + "w", WHITE, (x, -0.0045, z), rot=(0, R(-40), 0), scl=(0.016, 0.001, 0.036)))
        o = join(parts, name)
        # trim stripe overhang: clamp verts to the stick height
        for v in o.data.vertices:
            if v.co.y < -0.004: v.co.z = max(z - 0.015, min(z + 0.015, v.co.z)); v.co.x = max(-0.14, min(0.14, v.co.x))
        return o
    slate = prim("box", "slate", MBLACK, (0, 0, 0.10), scl=(0.28, 0.006, 0.20))
    lines = [prim("box", "ln", WHITE, (0, -0.0035, z), scl=(0.26, 0.001, 0.003)) for z in (0.13, 0.07)]
    lines.append(prim("box", "lnv", WHITE, (0.0, -0.0035, 0.10), scl=(0.003, 0.001, 0.06)))
    lower = stick("lower", 0.215)
    upper = stick("upper", 0.0)
    xform(upper, Matrix.Translation((-0.14, 0, 0.245)) @ Matrix.Rotation(R(-18), 4, 'Y') @ Matrix.Translation((0.14, 0, 0.0)))
    hinge = prim("cyl", "hinge", STEEL, (-0.135, 0, 0.233), rot=(R(90), 0, 0), scl=(0.008, 0.008, 0.02), seg=12)
    o = join([slate, lower, upper, hinge] + lines, "P_Clapper")
    return finish(o, "P_Clapper", (0.12, 0, 0.015), 0.01)

def newspaper():
    def d(px, w, h):
        rect(px, w, h, 0, 0, w, h, [0.93, 0.92, 0.88])
        rect(px, w, h, 20, h - 50, w - 20, h - 22, [0.3, 0.3, 0.32])    # masthead block
        cols = 3; cw = (w - 40) // cols
        for c in range(cols):
            x0 = 20 + c * cw + 4; y = h - 80
            while y > 30:
                if c == 1 and h - 260 < y < h - 90:
                    rect(px, w, h, x0, h - 250, x0 + cw - 8, h - 95, [0.5, 0.75, 0.95]); y = h - 270; continue
                rect(px, w, h, x0, y, x0 + cw - 8 - (30 if random.random() < 0.15 else 0), y + 5, [0.6, 0.6, 0.62]); y -= 14
    img = make_img("T_Newspaper", 300, 450, d)
    NM = mat("M_Newspaper", (1, 1, 1), 0.7, img=img)
    pages = []
    for side in (-1, 1):
        bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=6, y_segments=8, size=0.5)
        bm.transform(Matrix.Diagonal((0.225, 0.30, 1, 1)))
        p = new_obj("page", bm, [NM]); planar_uv(p, 0, 1)
        sol = p.modifiers.new("s", 'SOLIDIFY'); sol.thickness = 0.002
        bpy.context.view_layer.objects.active = p; bpy.ops.object.modifier_apply(modifier="s")
        # stand up: XY grid -> XZ (normal -Y)
        xform(p, Matrix.Rotation(R(90), 4, 'X'))
        xform(p, Matrix.Translation((side * 0.1125, 0, 0)))
        xform(p, Matrix.Rotation(R(side * -12), 4, 'Z'))   # V fold toward reader
        pages.append(p)
    o = join(pages, "P_Newspaper")
    lo, hi = bbox(o)
    return finish(o, "P_Newspaper", (lo.x + 0.005, (lo.y + hi.y) / 2, 0), 0.01)

def photoframe():
    W, H, b = 0.25, 0.30, 0.025
    parts = [prim("box", "t", SILVER, (0, 0, H - b / 2), scl=(W, 0.02, b)), prim("box", "bt", SILVER, (0, 0, b / 2), scl=(W, 0.02, b)),
             prim("box", "l", SILVER, (-W / 2 + b / 2, 0, H / 2), scl=(b, 0.0199, H - 2 * b - 0.0004)), prim("box", "r", SILVER, (W / 2 - b / 2, 0, H / 2), scl=(b, 0.0199, H - 2 * b - 0.0004)),
             prim("box", "pic", LBLUE, (0, 0.002, H / 2), scl=(W - 2 * b + 0.002, 0.004, H - 2 * b + 0.002)),
             prim("box", "back", MGREY, (0, 0.009, H / 2), scl=(W - 0.01, 0.003, H - 0.01))]
    o = join(parts, "P_PhotoFrame")
    return finish(o, "P_PhotoFrame", (0, 0, 0), 0.02)

def ticket():
    def d(px, w, h):
        rect(px, w, h, 0, 0, w, h, [0.8, 0.05, 0.05])
        rect(px, w, h, 0, 30, w, 42, [0.97, 0.97, 0.97])
        rect(px, w, h, 108, 0, 110, h, [0.6, 0.03, 0.03])
    img = make_img("T_Ticket", 150, 70, d)
    o = prim("box", "ticket", mat("M_Ticket", (1, 1, 1), 0.45, img=img), (0, 0, 0), scl=(0.15, 0.07, 0.0006))
    planar_uv(o, 0, 1)
    return finish(o, "P_TicketCard", (-0.065, 0, 0), 0.003)

# ------------------------------------------------------------------ build
PROPS += [paperclip(), fishpen()]
dk = doorknob()
PROPS += [campstove(), generator(), keg()]
sm = snowmobile()
PROPS += [van(), contract(), pen2(), condokeys(), guitar(), snowglobe(), moviecamera(), clapper(), newspaper(), photoframe(), ticket()]

# doorknob orientation + origin (decided from the end radii)
lo, hi = bbox(dk)
rA, rB = dk["_rA"], dk["_rB"]; del dk["_rA"]; del dk["_rB"]
L = hi.y - lo.y
# scale: knob ball diameter 6 cm. the ball is the end whose cross-section stays wide over a long span: use the end
# with fewer extreme-radius verts as rosette (thin plate).  Fallback: ball = end with larger radius.
def span(sign):
    vs = [v.co for v in dk.data.vertices if sign * v.co.y > L * 0.15]
    return max((v.x ** 2 + v.z ** 2) ** 0.5 for v in vs)
ball_sign = 1 if os.environ.get("KNOB_BALL", "") == "+" else -1 if os.environ.get("KNOB_BALL", "") == "-" else (1 if rA <= rB else -1)
rball = span(ball_sign)
s = 0.03 / rball
xform(dk, Matrix.Diagonal((s, s, s, 1)))
if ball_sign > 0: xform(dk, Matrix.Rotation(R(180), 4, 'Z'))   # ball toward -Y
lo, hi = bbox(dk)
ball = [v.co for v in dk.data.vertices if v.co.y < lo.y + 0.035]
bc = sum(ball, Vector()) / len(ball)
PROPS.insert(2, finish(dk, "P_Doorknob", (0, bc.y, 0), 0.06))

lo, hi = bbox(sm)
# front of snowmobile = skis end. skis are lowest geometry; their centre-y decides the front
low = [v.co for v in sm.data.vertices if v.co.z < lo.z + 0.05]
ly = sum(v.y for v in low) / len(low)
front_sign = 1 if os.environ.get("SNOW_FRONT", "") == "+" else -1 if os.environ.get("SNOW_FRONT", "") == "-" else (1 if ly > 0 else -1)
if front_sign > 0: xform(sm, Matrix.Rotation(R(180), 4, 'Z'))
PROPS.insert(6, finish(sm, "P_Snowmobile", (0, 0, 0), 0))

# lay them out in a row (not used by the film: shots place them)
x = 0
for o in PROPS:
    lo, hi = bbox(o); w = hi.x - lo.x
    o.location = (x - lo.x, 30.0, 0)
    x += w + 0.5
bpy.ops.file.pack_all()
bpy.ops.outliner.orphans_purge(do_recursive=True)
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print("SAVED", OUT, [o.name for o in PROPS])

# credits
cr = json.load(open(MOD + "/credits.json"))
used = {"P_Doorknob": "doorknob", "P_Generator": "generator", "P_Snowmobile": "snowmobile", "P_Van": "vanB", "P_CondoKeys": "key", "P_Guitar": "guitar"}
out = {o.name: (cr[used[o.name]] if o.name in used else "procedural (built in 10_props.py)") for o in PROPS}
json.dump(out, open(os.path.dirname(os.path.abspath(__file__)) + "/props_credits.json", "w"), indent=1)
