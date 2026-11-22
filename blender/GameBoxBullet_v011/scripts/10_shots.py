"""GameBoxBullet v011: hard-cut shot version built straight to the VO (frames 1-1311, 60 fps).
blender -b ../GameBoxBullet_v001/work/scene.blend --python scripts/10_shots.py -- ../GameBoxBullet_v001/work/v11_anim.blend

Replaces the v001-v010 continuous camera, the old layered see-through box and the street walker with:
- a shooter shot (who fires, the gun, the muzzle flash), a tracked bullet close-up, a static exterior and a static interior wall break
- one solid collector's box model (one mesh family, never swapped) with a real bullet hole and a crack decal fixed at the impact
- a separate cross-section model of the same box (solid cut layers on a sky-blue studio card) for the inside beats
- an animated man holding the box at chest height, palms on its sides, with head, eye, blink and expression changes
- one camera, hard cuts baked into its keys (constant interpolation, no markers)"""
import sys, os, math, random, json, colorsys
import bpy, bmesh
import numpy as np
from mathutils import Vector, Matrix, Quaternion, Euler

OUT = sys.argv[sys.argv.index("--") + 1]
HERE = os.path.dirname(os.path.abspath(__file__)); V11 = os.path.dirname(HERE)
BL = os.path.dirname(V11); V1 = os.path.join(BL, "GameBoxBullet_v001")
exec(open(os.path.join(BL, "pipeline", "anim_lib.py")).read())
exec(open(os.path.join(BL, "pipeline", "hand_poses.py")).read())
def ground_z(x, y): return 0.0   # the shooter stands on the road (z 0)
sc = bpy.context.scene
random.seed(1511)
V = Vector
F_END = 1311
ENV = lambda k, d: float(os.environ.get(k, d))

def kf(o, path, f, idx=-1): o.keyframe_insert(path, frame=f, index=idx)
def coll(name):
    c = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if c.name not in sc.collection.children: sc.collection.children.link(c)
    return c
def mesh_obj(name, bm, c, mat=None):
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); c.objects.link(o)
    if mat: me.materials.append(mat)
    return o
def cube_bm(x0, x1, y0, y1, z0, z1):
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co = V(((x0 + x1) / 2 + v.co.x * (x1 - x0), (y0 + y1) / 2 + v.co.y * (y1 - y0), (z0 + z1) / 2 + v.co.z * (z1 - z0)))
    uvl = bm.loops.layers.uv.new("UVMap")
    for fc_ in bm.faces:
        nx, ny, nz = (abs(x) for x in fc_.normal)
        for lp in fc_.loops:
            co = lp.vert.co
            lp[uvl].uv = (co.y, co.z) if nx >= max(ny, nz) else ((co.x, co.z) if ny >= nz else (co.x, co.y))
    return bm
def box(name, c, x0, x1, y0, y1, z0, z1, mat=None, bevel=0.0):
    o = mesh_obj(name, cube_bm(x0, x1, y0, y1, z0, z1), c, mat)
    if bevel:
        m = o.modifiers.new("bev", "BEVEL"); m.width = bevel; m.segments = 2; m.limit_method = "ANGLE"
    return o
def P(name, col, rough=0.5, metal=0.0, emit=None, ew=0.0, coat=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*col, 1); b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal; b.inputs["Coat Weight"].default_value = coat
    if emit:
        b.inputs["Emission Color"].default_value = (*emit, 1); b.inputs["Emission Strength"].default_value = ew
    return m
def hexc(h):
    h = h.lstrip("#"); c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(((x + 0.055) / 1.055) ** 2.4 if x > 0.04045 else x / 12.92 for x in c)
def fcurves_of(idb):
    ad = idb.animation_data
    if not ad or not ad.action: return []
    act = ad.action
    if hasattr(act, "fcurves") and len(act.fcurves): return list(act.fcurves)
    out = []
    for L in act.layers:
        for st in L.strips:
            for cb in st.channelbags: out += list(cb.fcurves)
    return out
def hide_key(o, frames_vis):
    """frames_vis: [(frame, visible)] -> keyed hide_render + hide_viewport, constant"""
    for f, vis in frames_vis:
        o.hide_render = not vis; o.hide_viewport = not vis
        kf(o, "hide_render", f); kf(o, "hide_viewport", f)
def remove_tree(o):
    for c in list(o.children_recursive): bpy.data.objects.remove(c, do_unlink=True)
    bpy.data.objects.remove(o, do_unlink=True)

C_FX = coll("FX"); C_BOX = coll("Box"); C_SEC = coll("Section"); C_EXT = coll("Exterior"); C_ROOM = coll("Bedroom")

# ================================================================== VO beats (frame = 1 + round(sec * 60))
BEATS = [(1, "A stray bullet"), (51, "ripped through"), (97, "the wall of his house"), (169, "flying straight for his chest"),
         (277, "But he was holding"), (354, "his brand new video game collector's box"), (497, "The bullet slammed into it"),
         (603, "The case cracked"), (675, "the discs shattered"), (755, "and layer by layer"), (831, "they ate up the bullet's energy"),
         (941, "It stopped halfway through"), (1039, "buried inside the box"), (1137, "His game collection"), (1213, "just saved his life")]
F_FIRE = 10      # muzzle flash ("stray" @13)
F_WALL = 99      # nose meets the siding ("wall" @97)
F_DRY = 141      # nose leaves the drywall into the room
F_HIT = 519      # nose meets the box cover ("slammed" @519)
F_STOP = 962     # bullet at rest, halfway ("stopped" @948)

# ================================================================== clean out v001-v010 pieces that v011 replaces
for o in list(C_BOX.objects): bpy.data.objects.remove(o, do_unlink=True)
for n in ("Bullet_trail",):
    if bpy.data.objects.get(n): bpy.data.objects.remove(bpy.data.objects[n], do_unlink=True)
if bpy.data.objects.get("Walker"): remove_tree(bpy.data.objects["Walker"])
for o in [o for o in bpy.data.objects if o.name.startswith("ceiling_fan")]:   # the fan blocked the top of the frame: gone
    bpy.data.objects.remove(o, do_unlink=True)
bpy.data.orphans_purge(do_recursive=True)

# ================================================================== the man and where he stands
man = bpy.data.objects["Gamer"]; body = bpy.data.objects["Gamer.body"]
R = make_human_ctrl(man); H = Human(R)
add_hand_limits(man)
FZ = 0.25
MAN = V((0.0, 3.25, 0.0))
BW, BH, BD = 0.30, 0.26, 0.17          # one box model: 30 x 26 x 17 cm, front face toward the wall (-Y)
HIT_L = V((0.0, -BD / 2, 0.02))        # impact point on the cover (box local)
# chest surface at the box height (rest pose, rig at MAN): the box back face sits on the hoodie
def chest_y(zw):
    me = body.data; Mw = Matrix.Translation(V((MAN.x, MAN.y, FZ - 0.01)))
    ys = [(Mw @ v.co).y for v in me.vertices if abs((Mw @ v.co).z - zw) < 0.03 and abs(v.co.x) < 0.10]
    return min(ys)
BOX_Z = 1.45
CHEST = chest_y(BOX_Z)
BOX_C = V((0.0, CHEST - 0.032 - BD / 2, BOX_Z))
print("BOX_C", BOX_C, "chest", CHEST)

# ------------------------------------------------------------------ box motion (world)
def sm(a, b, f): return smooth((f - a) / float(b - a))
def shove(f):
    if f <= F_HIT: return 0.0
    u = (f - F_HIT) / 60.0
    return 0.045 * (1 - math.exp(-u * 5.0)) * math.exp(-u * 0.35) + 0.012 * (1 - math.exp(-u * 2))
def box_pose(f):
    loc = BOX_C.copy(); rx = 0.0; rz = 0.0; ry = 0.0
    loc.z += 0.003 * math.sin(f / 60 * 2 * math.pi * 0.27)                               # breathing
    adm = 1 - sm(440, 505, f)                                                               # admiring: turns the box in his hands
    rz += math.radians(13) * math.sin(2 * math.pi * (f - 150) / 210.0) * adm
    rx += math.radians(-9) * adm * (0.6 + 0.4 * math.sin(2 * math.pi * f / 260.0))
    loc.z += 0.03 * sm(270, 330, f) * adm                                                   # lifts it a little to look at it
    loc.y -= 0.02 * sm(270, 330, f) * adm
    if f > F_HIT:
        loc.y += shove(f)
        u = (f - F_HIT) / 50.0
        rx += math.radians(-5.0) * (1 - math.exp(-u * 3.0)) * math.exp(-u * 0.4)
        loc.z += -0.012 * (1 - math.exp(-u * 3)) * math.exp(-u * 0.5)
        trem = math.exp(-(f - F_HIT) / 300.0)
        rz += math.radians(1.2) * math.sin(f * 0.21) * trem; loc.x += 0.002 * math.sin(f * 0.17) * trem
    # buried: he tilts the front up toward his eyes and peers at the hole, then brings it back up to his chest
    t = sm(1040, 1080, f) * (1 - sm(1140, 1185, f))
    rx += math.radians(-24) * t; loc.z -= 0.05 * t; loc.y -= 0.06 * t; ry += math.radians(5) * t
    # payoff: lifts it a little toward the camera, front square
    w = sm(1225, 1270, f)
    loc.z += 0.025 * w; loc.y -= 0.03 * w
    return loc, Euler((rx, ry, rz))
def box_M(f):
    l, e = box_pose(f); return Matrix.Translation(l) @ e.to_matrix().to_4x4()

# ================================================================== the box (one solid model)
C = (0.03, 0.06, 0.16)
def art_material():
    """front art: deep blue gradient, a gold abstract emblem (rings + chevrons), no text"""
    Hh, Ww = 512, 600
    yy, xx = np.mgrid[0:Hh, 0:Ww]; u = xx / Ww; v = yy / Hh
    img = np.zeros((Hh, Ww, 3))
    base = np.array(hexc("#0B1F5C")); top = np.array(hexc("#2E6CF0"))
    img[:] = base * (1 - v[..., None]) + top * v[..., None]
    cx, cy = 0.5, 0.58; r = np.hypot((u - cx) * Ww / Hh, v - cy)
    gold = np.array(hexc("#F2B233")); cyan = np.array(hexc("#5CE1FF"))
    ring = (np.abs(r - 0.25) < 0.018) | (np.abs(r - 0.18) < 0.008)
    img[ring] = gold
    chev = (np.abs(np.abs((u - cx) * Ww / Hh) - (cy - v) * 0.8 - 0.02) < 0.02) & (v < cy) & (v > cy - 0.2)
    img[chev] = cyan
    star = r < 0.07
    img[star] = img[star] * 0.2 + gold * 0.8
    band = (v < 0.14) | (v > 0.94)
    img[band] = np.array(hexc("#111A33"))
    stripe = (np.abs(v - 0.14) < 0.006)
    img[stripe] = gold
    im = bpy.data.images.new("box_front_art", Ww, Hh); px = np.ones((Hh, Ww, 4)); px[..., :3] = img; im.pixels = px.ravel(); im.pack()
    m = bpy.data.materials.new("M_box_front"); m.use_nodes = True; nt = m.node_tree
    t = nt.nodes.new("ShaderNodeTexImage"); t.image = im; t.extension = "EXTEND"
    tc = nt.nodes.new("ShaderNodeTexCoord"); mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Location"].default_value = (0.5, 0.5, 0); mp.inputs["Scale"].default_value = (1 / BW, 1 / BH, 1)
    sep = nt.nodes.new("ShaderNodeSeparateXYZ"); com = nt.nodes.new("ShaderNodeCombineXYZ")
    nt.links.new(tc.outputs["Object"], sep.inputs[0]); nt.links.new(sep.outputs["X"], com.inputs["X"]); nt.links.new(sep.outputs["Z"], com.inputs["Y"])
    nt.links.new(com.outputs[0], mp.inputs[0]); nt.links.new(mp.outputs[0], t.inputs[0])
    b = nt.nodes["Principled BSDF"]; nt.links.new(t.outputs[0], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.3; b.inputs["Coat Weight"].default_value = 0.6; b.inputs["Coat Roughness"].default_value = 0.08
    return m
M_front = art_material()
M_side = P("M_box_side", hexc("#13235A"), 0.35, coat=0.5)
M_edge = P("M_box_edge", hexc("#F2B233"), 0.3, metal=0.6)
M_torn = P("M_box_torn", (0.16, 0.12, 0.09), 0.9)
broot = bpy.data.objects.new("BoxRoot", None); C_BOX.objects.link(broot)
broot.empty_display_size = 0.1
def to_box(o): o.parent = broot; return o
# rigid front cover (5 mm) with a real hole, body behind it with the bullet's tunnel
CT = 0.005
cover = to_box(box("Box_cover", C_BOX, -BW / 2, BW / 2, -BD / 2, -BD / 2 + CT, -BH / 2, BH / 2, M_side, 0.0015))
cover.data.materials.append(M_front)
for p in cover.data.polygons:
    if p.normal.y < -0.9: p.material_index = 1
bodyb = to_box(box("Box_body", C_BOX, -BW / 2, BW / 2, -BD / 2 + CT, BD / 2, -BH / 2, BH / 2, M_side, 0.002))
# gold trim stripes on the sides (thin raised bands)
for zz in (-BH / 2 + 0.03, BH / 2 - 0.03):
    for sx in (-1, 1):
        to_box(box("Box_trim", C_BOX, sx * BW / 2 - 0.0006, sx * BW / 2 + 0.0006, -BD / 2 + 0.01, BD / 2 - 0.01, zz - 0.003, zz + 0.003, M_edge))
HOLE_R = 0.0072; TUN_D = 0.060
def bore(o, y0, y1, r, mat):
    bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=True, segments=24, radius1=r, radius2=r * 0.85, depth=(y1 - y0))
    rnd = random.Random(7)
    for v in bm.verts:
        k = 1 + 0.12 * (rnd.random() - 0.5); v.co.x *= k; v.co.y *= k
    bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=Matrix.Rotation(math.radians(-90), 3, 'X'))
    bmesh.ops.translate(bm, verts=bm.verts, vec=(HIT_L.x, (y0 + y1) / 2, HIT_L.z))
    cut = mesh_obj(o.name + "_bore", bm, sc.collection, mat)
    m = o.modifiers.new("bore", "BOOLEAN"); m.object = cut; m.operation = "DIFFERENCE"; m.solver = "EXACT"; m.material_mode = "TRANSFER"
    bpy.context.view_layer.objects.active = o
    for s_ in bpy.context.selected_objects: s_.select_set(False)
    o.select_set(True); bpy.ops.object.modifier_apply(modifier="bore")
    bpy.data.objects.remove(cut, do_unlink=True)
bore(cover, -BD / 2 - 0.01, -BD / 2 + CT + 0.002, HOLE_R, M_torn)
bore(bodyb, -BD / 2 + CT - 0.002, -BD / 2 + TUN_D, HOLE_R * 0.95, M_torn)
# intact plug in the hole until the bullet arrives
bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=True, segments=24, radius1=HOLE_R + 0.0004, radius2=HOLE_R + 0.0004, depth=CT * 0.98)
bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=Matrix.Rotation(math.radians(90), 3, 'X'))
bmesh.ops.translate(bm, verts=bm.verts, vec=(HIT_L.x, -BD / 2 + CT / 2, HIT_L.z))
plug = to_box(mesh_obj("Box_plug", bm, C_BOX, M_front))
# crack decal on the cover, centred on the impact: radial cracks generated once, revealed by a growing radius (no tiling)
def crack_image(n=512, seed=5):
    rng = np.random.default_rng(seed); a = np.zeros((n, n))
    def line(x0, y0, x1, y1, w):
        L = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
        for t in np.linspace(0, 1, L * 2):
            x = x0 + (x1 - x0) * t; y = y0 + (y1 - y0) * t
            xi, yi = int(x), int(y)
            a[max(0, yi - w):yi + w + 1, max(0, xi - w):xi + w + 1] = 1.0
    c = n / 2
    def branch(x, y, ang, length, w, depth):
        steps = int(length / 6)
        for _ in range(steps):
            ang += rng.normal(0, 0.18); nx = x + 6 * math.cos(ang); ny = y + 6 * math.sin(ang)
            if not (2 < nx < n - 3 and 2 < ny < n - 3): return
            line(x, y, nx, ny, w); x, y = nx, ny
            if depth < 2 and rng.random() < 0.06:
                branch(x, y, ang + rng.choice([-1, 1]) * rng.uniform(0.4, 0.9), length * 0.4, max(0, w - 1), depth + 1)
    for k in range(11):
        ang = 2 * math.pi * k / 11 + rng.normal(0, 0.15)
        branch(c + 14 * math.cos(ang), c + 14 * math.sin(ang), ang, rng.uniform(140, 240), 1, 0)
    # concentric stress fractures close to the hole
    yy, xx = np.mgrid[0:n, 0:n]; r = np.hypot(xx - c, yy - c); th = np.arctan2(yy - c, xx - c)
    for rr in (30, 52):
        a[(np.abs(r - rr - 3 * np.sin(th * 5)) < 1.0) & (np.sin(th * 7 + rr) > 0.1)] = 1.0
    whit = np.clip(1 - (r - 15) / 16, 0, 1) * (r > 13)
    img = np.zeros((n, n, 4))
    img[..., 0] = 0.92; img[..., 1] = 0.94; img[..., 2] = 1.0
    img[..., 3] = np.clip(a * 0.95 + whit * 0.55, 0, 1) * (r > 13.5)
    im = bpy.data.images.new("crack_decal", n, n, alpha=True); im.pixels = img.ravel(); im.alpha_mode = "STRAIGHT"; im.pack()
    return im
DEC = 0.13
def decal_material():
    m = bpy.data.materials.new("M_crack_decal"); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    tc = nt.nodes.new("ShaderNodeTexCoord"); t = nt.nodes.new("ShaderNodeTexImage"); t.image = crack_image(); t.extension = "CLIP"
    ln = nt.nodes.new("ShaderNodeVectorMath"); ln.operation = "LENGTH"
    sub = nt.nodes.new("ShaderNodeVectorMath"); sub.operation = "SUBTRACT"; sub.inputs[1].default_value = (0.5, 0.5, 0)
    rad = nt.nodes.new("ShaderNodeValue"); rad.name = "crack_radius"; rad.outputs[0].default_value = 0.0
    div = nt.nodes.new("ShaderNodeMath"); div.operation = "DIVIDE"; div.inputs[1].default_value = DEC
    lt = nt.nodes.new("ShaderNodeMath"); lt.operation = "LESS_THAN"
    mul = nt.nodes.new("ShaderNodeMath"); mul.operation = "MULTIPLY"
    b = nt.nodes.new("ShaderNodeBsdfPrincipled"); b.inputs["Base Color"].default_value = (0.85, 0.9, 1.0, 1); b.inputs["Roughness"].default_value = 0.6
    tr = nt.nodes.new("ShaderNodeBsdfTransparent"); mx = nt.nodes.new("ShaderNodeMixShader"); o = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(tc.outputs["UV"], t.inputs[0]); nt.links.new(tc.outputs["UV"], sub.inputs[0]); nt.links.new(sub.outputs[0], ln.inputs[0])
    nt.links.new(rad.outputs[0], div.inputs[0]); nt.links.new(ln.outputs["Value"], lt.inputs[0]); nt.links.new(div.outputs[0], lt.inputs[1])
    nt.links.new(lt.outputs[0], mul.inputs[0]); nt.links.new(t.outputs["Alpha"], mul.inputs[1])
    nt.links.new(mul.outputs[0], mx.inputs[0]); nt.links.new(tr.outputs[0], mx.inputs[1]); nt.links.new(b.outputs[0], mx.inputs[2])
    nt.links.new(mx.outputs[0], o.inputs[0])
    return m, rad
M_decal, CRACK_R = decal_material()
bpy.ops.mesh.primitive_plane_add(size=1.0); dec = bpy.context.active_object; dec.name = "Box_crack_decal"
for c_ in list(dec.users_collection): c_.objects.unlink(dec)
C_BOX.objects.link(dec); dec.data.materials.append(M_decal); to_box(dec)
dec.rotation_euler = (math.radians(90), 0, 0); dec.scale = (DEC, DEC, 1); dec.location = (HIT_L.x, -BD / 2 - 0.0004, HIT_L.z)
for f, r_ in ((1, 0.0), (F_HIT, 0.0), (F_HIT + 4, 0.016), (F_HIT + 40, 0.024), (603, 0.028), (640, 0.044), (674, 0.056), (720, 0.060), (F_END, 0.060)):
    CRACK_R.outputs[0].default_value = r_; CRACK_R.outputs[0].keyframe_insert("default_value", frame=f)
hide_key(plug, [(1, True), (F_HIT, False)])
for f in range(1, F_END + 1, 2):
    l, e = box_pose(f); broot.location = l; broot.rotation_euler = e
    kf(broot, "location", f); kf(broot, "rotation_euler", f)
for fc in fcurves_of(broot):
    for k in fc.keyframe_points: k.interpolation = "LINEAR"

# ================================================================== man: stance, body, head, face, eyes, hands
bpy.context.view_layer.objects.active = man; bpy.ops.object.mode_set(mode='POSE')
for s, dx in (("L", 0.115), ("R", -0.115)):
    xy = V((MAN.x + dx, MAN.y + (0.0 if s == "L" else 0.035)))
    a = H.ankle[s]; z = FZ + a.z + 0.0165
    for f in (1, F_END):
        M = Matrix.Translation(V((xy.x, xy.y, z))) @ Matrix.Rotation(math.radians(7 if s == "L" else -7), 4, 'Z') @ Matrix.Translation(-a) @ R.rest("IK_foot." + s)
        R.key_world("IK_foot." + s, f, M)
        pole = V((xy.x + dx * 0.5, xy.y - 0.7, z + 0.45)); n = "Pole_knee." + s; pb = R.PB[n]
        pb.location = R.rest(n).to_3x3().inverted() @ (pole - R.BN[n].head_local); pb.keyframe_insert("location", frame=f)
def man_state(f):
    dy = 0.0; dz = 0.0; flex = 4.0; twist = 0.0; side = 0.0; hp = 20.0; hy = 0.0; wx = 0.0
    br = math.sin(f / 60 * 2 * math.pi * 0.27); dz += 0.004 * br; flex += 0.8 * br
    adm = 1 - sm(440, 505, f)
    hy += 9 * math.sin(2 * math.pi * (f - 150) / 210.0 + 0.5) * adm                       # head follows the box he is turning
    twist += 5 * math.sin(2 * math.pi * (f - 150) / 210.0 + 0.2) * adm
    side += 3 * math.sin(2 * math.pi * f / 300.0) * adm; wx += 0.012 * math.sin(2 * math.pi * f / 300.0) * adm
    hp += 4 * math.sin(2 * math.pi * f / 95.0) * adm                                        # little happy nods
    # he hears the wall crack, looks up from the box toward the noise
    up = sm(395, 430, f) * (1 - sm(F_HIT + 40, F_HIT + 90, f)); hp -= 20 * up; hy -= 6 * up
    if f > F_HIT:   # impact: pushed back, head snaps back then forward
        v = (f - F_HIT) / 60.0
        dy += shove(f); dz -= 0.015 * (1 - math.exp(-v * 3)) * math.exp(-v * 0.5); flex -= 6 * (1 - math.exp(-v * 4)) * math.exp(-v * 0.6)
        hp -= 10 * math.exp(-v * 2.5) * (1 - math.exp(-v * 12))
    # stares down at the cracking box, small shakes of disbelief, heavy breaths
    dn = sm(600, 640, f) * (1 - sm(1140, 1175, f)); hp += 14 * dn
    hy += 5 * math.sin(2 * math.pi * f / 70.0) * dn * (sm(830, 860, f) - sm(930, 960, f))
    dz += 0.006 * math.sin(2 * math.pi * f / 50.0) * dn * sm(560, 620, f)
    # peers into the hole (head tilts to the side, leans in)
    pe = sm(1040, 1080, f) * (1 - sm(1140, 1185, f)); hp += 10 * pe; side -= 6 * pe; flex += 5 * pe
    # looks up at the hole in the wall, then back at the box
    lw = sm(1150, 1172, f) * (1 - sm(1196, 1218, f)); hp -= 24 * lw; hy += 4 * lw
    # relief: big exhale, shoulders drop, head lifts with a smile
    rl = sm(1222, 1262, f); dz -= 0.012 * rl; hp -= 12 * rl; flex -= 2 * rl; hy -= 4 * rl
    hp += 1.5 * math.sin(f * 0.05) + 0.8 * math.sin(f * 0.13)
    hy += 1.5 * math.sin(f * 0.031 + 1.0)
    return dy, dz, flex, twist, side, hp, hy, wx
for f in list(range(1, F_END + 1, 3)) + [F_END]:
    dy, dz, flex, twist, side, hp, hy, wx = man_state(f)
    H.key_root(f, V((MAN.x + wx, MAN.y + H.root_head.y + dy, FZ + H.root_head.z - 0.006 + dz)), yaw=0.0, flex=flex * 0.3, side=side * 0.5)
    H.key_spine(f, flex=flex, twist=twist, side=side, head=(hp, hy))
# eyes: aim at the box / the noise / the hole / the camera, with small saccades
SACC = {}
rng = random.Random(3)
for f in range(1, F_END + 1, 22): SACC[f] = (rng.uniform(-3, 3), rng.uniform(-4, 4))
def eye_state(f):
    p, y = 6.0, 0.0
    up = sm(395, 415, f) * (1 - sm(F_HIT + 30, F_HIT + 60, f)); p -= 10 * up
    lw = sm(1150, 1160, f) * (1 - sm(1196, 1206, f)); p -= 12 * lw
    rl = sm(1250, 1275, f); p -= 6 * rl; y += 2 * rl
    k = max(kk for kk in SACC if kk <= f); sp, sy = SACC[k]
    return p + sp, y + sy
for f in range(1, F_END + 1, 2):
    p, y = eye_state(f)
    for s in "LR":
        R.key_rot("eye." + s, f, [("X", p), ("Z", y)])
# step-shaped saccades: hold each eye direction, jump over 2 frames
for fc in fcurves_of(man):
    if fc.data_path.startswith('pose.bones["eye.'):
        for kp in fc.keyframe_points: kp.interpolation = "LINEAR"
# face: smile / wide eyes / brows / jaw (never a gaping mouth)
SM = 1.0; LID = -1.0
def key_face(f, smile, wide, brow, jaw):
    for sd, sx in (("L", 1), ("R", -1)):
        for n, d in (("oris03.", V((sx * 0.003, 0.004, 0.006))), ("oris07.", V((sx * 0.003, 0.004, 0.004))),
                     ("risorius03.", V((sx * 0.002, 0.003, 0.005))), ("levator05.", V((0, 0.001, 0.002))),
                     ("orbicularis04.", V((0, 0, 0.002)))):
            nm = n + sd; pb = R.PB[nm]
            pb.location = R.rest(nm).to_3x3().inverted() @ (d * smile * SM); pb.keyframe_insert("location", frame=f)
        for nm, a in (("orbicularis03." + sd, -16 * wide * LID), ("orbicularis04." + sd, 8 * wide * LID)):
            pb = R.PB[nm]; pb.rotation_quaternion = Quaternion(V((1, 0, 0)), math.radians(a)); pb.keyframe_insert("rotation_quaternion", frame=f)
        for nm in ("oculi01." + sd, "oculi02." + sd):
            pb = R.PB[nm]; pb.location = R.rest(nm).to_3x3().inverted() @ V((0, 0, 0.004 * brow)); pb.keyframe_insert("location", frame=f)
    pb = R.PB["jaw"]; pb.rotation_quaternion = Quaternion(V((1, 0, 0)), math.radians(jaw)); pb.keyframe_insert("rotation_quaternion", frame=f)
FACE = [(1, 0.7, 0.0, 0.0, 0.0), (180, 1.0, 0.0, 0.2, 1.0), (260, 0.8, 0.0, 0.0, 0.0), (300, 1.0, 0.0, 0.3, 2.0), (380, 0.9, 0.0, 0.1, 0.5),
        (410, 0.2, 0.3, 0.6, 1.0), (470, 0.0, 0.5, 0.8, 2.0), (F_HIT, 0.0, 0.5, 0.8, 2.0), (F_HIT + 8, -0.3, 1.0, 1.0, 6.0),
        (580, -0.2, 0.9, 1.0, 5.0), (640, -0.1, 0.7, 0.8, 3.0), (700, -0.2, 0.8, 0.9, 4.5), (780, -0.1, 0.6, 0.7, 2.0),
        (860, -0.2, 0.85, 1.0, 5.0), (930, -0.1, 0.6, 0.6, 2.5), (1060, 0.0, 0.5, 0.7, 1.5), (1120, 0.1, 0.6, 0.9, 3.0),
        (1160, 0.0, 0.9, 1.0, 4.0), (1210, 0.1, 0.6, 0.5, 2.0), (1240, 0.5, 0.3, 0.3, 3.0), (1275, 1.0, 0.1, 0.4, 1.5), (F_END, 1.0, 0.1, 0.3, 1.0)]
for f, a, b, c, d in FACE: key_face(f, a, b, c, d)
BLINKS = [70, 190, 300, 372, 452, 527, 640, 720, 800, 872, 960, 1050, 1112, 1178, 1233, 1290]
def blink_keys():
    for sd in "LR":
        nm = "orbicularis03." + sd; pb = R.PB[nm]
        for fb in BLINKS:
            qs = []
            for ff in (fb - 3, fb + 4):
                sc.frame_set(ff); qs.append((ff, pb.rotation_quaternion.copy()))
            for ff, q in qs:
                pb.rotation_quaternion = q; pb.keyframe_insert("rotation_quaternion", frame=ff)
            pb.rotation_quaternion = Quaternion(V((1, 0, 0)), math.radians(22 * LID)); pb.keyframe_insert("rotation_quaternion", frame=fb)
# hands: palms flat on the box sides, fingers forward along the sides, thumbs over the top edge
GY = ENV("GY", "0.052"); GZ = ENV("GZ", "-0.020"); FD_UP = ENV("FDUP", "0.12"); SKIN = ENV("SKIN", "0.050")
HANDP = {"L": (-0.3, -0.6, 0.03, 0.060), "R": (0.2, -0.6, 0.03, 0.045)}
HAND_FR = list(range(1, F_END + 1, 2)) + [F_END]
SKINF = {(s, f): HANDP[s][3] for s in "LR" for f in HAND_FR}
def key_hands(f, only=None):
    M = box_M(f); Rb = M.to_3x3()
    for s, sx in (("L", 1), ("R", -1)):
        if only and s != only: continue
        out, up, gy, _ = HANDP[s]
        pp = M @ V((sx * BW / 2, gy, GZ)); nrm = Rb @ V((-sx, 0, 0)); fd = Rb @ V((sx * out, -1.0, up))
        place_hand(man, s, f, pp, nrm, fd, skin=SKINF[(s, f)])
        pole = M @ V((sx * 0.75, 0.30, -0.30))
        pb = R.PB["Pole_elbow." + s]; nme = "Pole_elbow." + s
        pb.location = R.rest(nme).to_3x3().inverted() @ (pole - R.BN[nme].head_local); pb.keyframe_insert("location", frame=f)
for f in HAND_FR:
    key_hands(f)
# contact pass: measure the hand skin against the box side at every keyed frame, re-place until it sits 1-3 mm off
GI = {g.index: g.name for g in body.vertex_groups}
HANDV = {s: [v.index for v in body.data.vertices if any(g.weight > 0.3 and GI.get(g.group, "").endswith("." + s) and GI[g.group].startswith(("finger", "metacarpal", "wrist")) for g in v.groups)] for s in "LR"}
def hand_contact(f, s):
    sc.frame_set(f); dg = bpy.context.evaluated_depsgraph_get(); Bi = box_M(f).inverted(); sx = 1 if s == "L" else -1
    e = body.evaluated_get(dg); me = e.to_mesh(); M = Bi @ e.matrix_world; pen = 0.0; gap = 9.0
    if len(me.vertices) == len(body.data.vertices):
        for i in HANDV[s]:
            l = M @ me.vertices[i].co
            if abs(l.y) < BD / 2 and abs(l.z) < BH / 2:
                d = sx * l.x - BW / 2
                if d < 0: pen = max(pen, -d)
                else: gap = min(gap, d)
    e.to_mesh_clear(); return pen, gap
for mm in body.modifiers:
    if mm.type in ("SUBSURF", "MASK"): mm.show_viewport = False
CONTACT = {}
for it in range(4):
    nfix = 0
    for f in HAND_FR:
        for s in "LR":
            pen, gap = hand_contact(f, s)
            CONTACT[(s, f)] = (pen, gap)
            if pen > 0.0005 or gap > 0.004:
                SKINF[(s, f)] += (pen + 0.0015) if pen > 0.0005 else -(gap - 0.0015)
                key_hands(f, only=s); nfix += 1
    print("CONTACT pass", it, "fixed", nfix, flush=True)
    if not nfix: break
for mm in body.modifiers:
    if mm.type in ("SUBSURF", "MASK"): mm.show_viewport = True
print("CONTACT worst pen mm", round(max(v[0] for v in CONTACT.values()) * 1000, 1), "worst gap mm", round(max(v[1] for v in CONTACT.values() if v[1] < 9) * 1000, 1))
blink_keys()
for f in (1, F_END):
    for s in "LR":
        apply_pose(man, s, "flat_palm", f)
bpy.ops.object.mode_set(mode='OBJECT')

# ================================================================== shooter (who fires): generic man across the street
with bpy.data.libraries.load(os.path.join(V1, "work", "shooter.blend"), link=False) as (s_, d_):
    d_.objects = [n for n in s_.objects]
for o in d_.objects:
    if o: C_EXT.objects.link(o)
shooter = bpy.data.objects["Shooter"]
M_eye = bpy.data.materials.get("M_eye")
for o in shooter.children:
    if o.name.endswith(".high-poly") and M_eye:
        for i in range(len(o.data.materials)): o.data.materials[i] = M_eye
RS = make_human_ctrl(shooter); HS = Human(RS); add_hand_limits(shooter)
MUZ = V((0.0, -30.3, 1.47))           # muzzle: on the bullet line (wall hole at x 0, z 1.47)
M_gun = P("M_gun", (0.025, 0.025, 0.028), 0.45, metal=0.3)
gun = bpy.data.objects.new("Gun", None); C_EXT.objects.link(gun)
# plain toy-like silhouette only: a slide block, a grip block, a guard loop. No mechanism detail.
parts = [((-0.012, 0.012, -0.17, 0.0, -0.016, 0.016)), ((-0.011, 0.011, -0.165, -0.115, -0.11, -0.016))]
for i, (x0, x1, y0, y1, z0, z1) in enumerate(parts):
    o = box("Gun_part%d" % i, C_EXT, x0, x1, y0, y1, z0, z1, M_gun, 0.003); o.parent = gun
    if i == 1: o.rotation_euler.x = math.radians(-14)
bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=False, segments=16, radius1=0.022, radius2=0.022, depth=0.006)
gd = mesh_obj("Gun_guard", bm, C_EXT, M_gun); gd.parent = gun; gd.rotation_euler = (0, math.radians(90), 0); gd.location = (0, -0.095, -0.03); gd.scale = (1, 1.0, 1.0)
GRIP_L = V((0.0, -0.14, -0.05))       # grip centre (gun local; muzzle at origin, barrel along +Y)
def gun_M(f):
    t = max(0.0, f - F_FIRE)
    kick = (1 - math.exp(-t / 1.5)) * math.exp(-t / 9.0) if f >= F_FIRE else 0.0
    rec = Matrix.Translation(GRIP_L) @ Matrix.Rotation(math.radians(16 * kick), 4, 'X') @ Matrix.Translation(-GRIP_L)
    aim = Matrix.Rotation(math.radians(0.6 * math.sin(f * 0.15)), 4, 'Z') if f < F_FIRE else Matrix.Identity(4)
    return Matrix.Translation(MUZ + V((0, -0.025 * kick, 0))) @ aim @ rec
for f in range(1, 80):
    gun.matrix_world = gun_M(f); kf(gun, "location", f); kf(gun, "rotation_euler", f)
SH_ROOT = V((-0.13, -30.3 - 0.68, 0.0))     # body behind the outstretched right arm; faces +Y
bpy.context.view_layer.objects.active = shooter; bpy.ops.object.mode_set(mode='POSE')
for f in (1, F_END):
    HS.key_root(f, V((SH_ROOT.x, SH_ROOT.y, HS.root_head.z - 0.01)), yaw=180.0, flex=0.0, side=0.0)
    for s, dx in (("L", -0.13), ("R", 0.13)):
        xy = V((SH_ROOT.x + dx, SH_ROOT.y + (0.12 if s == "L" else -0.10)))
        HS.key_foot(s, f, xy, 180.0 + (8 if s == "L" else -12))
for f in range(1, 80, 2):
    k = max(0.0, f - F_FIRE); jolt = (1 - math.exp(-k / 2.0)) * math.exp(-k / 12.0) if f >= F_FIRE else 0.0
    HS.key_spine(f, flex=-2 - 3 * jolt, twist=-5, side=0.0, head=(4 - 4 * jolt, -8))
HS.key_spine(F_END, flex=-2, twist=-5, side=0.0, head=(4, -8))
for f in list(range(1, 80, 3)) + [80]:
    G = gun_M(f); Rg = G.to_3x3()
    pb = RS.PB["Pole_elbow.R"]; pole = G @ V((0.25, -0.40, -0.45))
    pb.location = RS.rest("Pole_elbow.R").to_3x3().inverted() @ (pole - RS.BN["Pole_elbow.R"].head_local); pb.keyframe_insert("location", frame=f)
    grip_object(shooter, "R", f, bpy.data.objects["Gun_part1"], G @ V((0.011, -0.146, -0.046)), Rg @ V((-1, 0, 0)), finger_dir=Rg @ V((0, 1, 0)))
for c in RS.PB["lowerarm02.L"].constraints:
    if c.type == "IK": c.mute = True
for c in RS.PB["wrist.L"].constraints:
    if c.type == "COPY_ROTATION": c.mute = True
for f in (1, F_END):
    RS.key_rot("upperarm01.L", f, [("Y", 40), ("X", 5)])
    apply_pose(shooter, "L", "relaxed", f)
bpy.ops.object.mode_set(mode='OBJECT')
# muzzle flash: a short star of light for 3 frames, then a small smoke puff
M_flash = bpy.data.materials.new("M_flash"); M_flash.use_nodes = True; nt = M_flash.node_tree; nt.nodes.clear()
e_ = nt.nodes.new("ShaderNodeEmission"); e_.inputs["Color"].default_value = (1.0, 0.75, 0.35, 1); e_.inputs["Strength"].default_value = 40
o_ = nt.nodes.new("ShaderNodeOutputMaterial"); nt.links.new(e_.outputs[0], o_.inputs[0])
bm = bmesh.new()
for k in range(7):
    a = 2 * math.pi * k / 7; L_ = 0.11 if k % 2 else 0.07
    tip = V((math.cos(a) * 0.5 * L_, 0.04, math.sin(a) * 0.5 * L_)) + V((0, 0.05, 0))
    v0 = bm.verts.new((0, 0.0, 0)); v1 = bm.verts.new(tip + V((0.004, 0, 0.004))); v2 = bm.verts.new(tip - V((0.004, 0, 0.004)))
    bm.faces.new((v0, v1, v2))
cone = bmesh.ops.create_cone(bm, cap_ends=True, segments=10, radius1=0.018, radius2=0.002, depth=0.12)
bmesh.ops.rotate(bm, verts=cone["verts"], cent=(0, 0, 0), matrix=Matrix.Rotation(math.radians(-90), 3, 'X'))
bmesh.ops.translate(bm, verts=cone["verts"], vec=(0, 0.06, 0))
flash = mesh_obj("Muzzle_flash", bm, C_FX, M_flash); flash.location = MUZ
hide_key(flash, [(1, False), (F_FIRE, True), (F_FIRE + 3, False)])
for f, s_ in ((F_FIRE, 0.6), (F_FIRE + 1, 1.0), (F_FIRE + 2, 0.7)):
    flash.scale = (s_, s_, s_); kf(flash, "scale", f)
fl = bpy.data.lights.new("L_flash", "POINT"); fl.color = (1.0, 0.75, 0.4); fl.shadow_soft_size = 0.05
flo = bpy.data.objects.new("L_flash", fl); C_FX.objects.link(flo); flo.location = MUZ + V((0, 0.08, 0))
for f, e in ((1, 0), (F_FIRE - 1, 0), (F_FIRE, 600), (F_FIRE + 2, 300), (F_FIRE + 4, 0)):
    fl.energy = e; fl.keyframe_insert("energy", frame=f)

# ================================================================== bullet: one straight path, one size
bullet = bpy.data.objects["Bullet"]
HITW = box_M(F_HIT) @ HIT_L
print("HIT world", HITW)
def line_pt(y):   # straight line from the muzzle to the impact point
    t = (y - MUZ.y) / (HITW.y - MUZ.y); return MUZ.lerp(HITW, t)
pre = pchip([(F_FIRE, MUZ.y + 0.02), (F_FIRE + 6, -29.2), (54, -24.0), (56, -22.6), (96, -1.9), (F_WALL, 0.0), (120, 0.08), (F_DRY, 0.16),
             (168, 0.42), (222, 0.86), (276, 1.27), (350, 1.80), (420, 2.30), (496, 2.80), (F_HIT, HITW.y)])
depth = pchip([(F_HIT, 0.0), (560, 0.003), (602, 0.005), (675, 0.008), (700, 0.013), (735, 0.029), (754, 0.037), (790, 0.050), (830, 0.063),
               (860, 0.070), (891, 0.0755), (940, 0.0835), (F_STOP, 0.085), (F_END, 0.085)])
def nose_world(f):
    if f <= F_HIT: return line_pt(pre(f))
    return box_M(f) @ (HIT_L + V((0, depth(f), 0)))
bullet.rotation_mode = "QUATERNION"
DIRW = (HITW - MUZ).normalized()
for f in range(1, F_END + 1):
    bullet.location = nose_world(f)
    d = DIRW if f <= F_HIT else (box_M(f).to_3x3() @ V((0, 1, 0))).normalized()
    spin = f * 0.5 if f < F_HIT else F_HIT * 0.5 + 0.5 * 40 * (1 - math.exp(-(f - F_HIT) / 40))
    bullet.rotation_quaternion = V((0, 1, 0)).rotation_difference(d) @ Quaternion(V((0, 1, 0)), spin)
    kf(bullet, "location", f); kf(bullet, "rotation_quaternion", f)
hide_key(bullet, [(1, False), (F_FIRE, True)])
mk = bullet.data.shape_keys.key_blocks["mushroom"]
for f, v in ((1, 0.0), (F_HIT, 0.0), (F_HIT + 50, 0.45), (700, 0.6), (850, 0.8), (F_STOP, 0.9)):
    mk.value = v; mk.keyframe_insert("value", frame=f)
# a faint heat shimmer streak behind the bullet outside (constant length, follows it)
bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=False, segments=12, radius1=0.0016, radius2=0.0003, depth=0.16)
bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=Matrix.Rotation(math.radians(90), 3, 'X')); bmesh.ops.translate(bm, verts=bm.verts, vec=(0, -0.11, 0))
mst = bpy.data.materials.new("M_streak"); mst.use_nodes = True; nt_ = mst.node_tree; nt_.nodes.clear()
e_ = nt_.nodes.new("ShaderNodeEmission"); e_.inputs["Color"].default_value = (1.0, 0.85, 0.6, 1); e_.inputs["Strength"].default_value = 3
t_ = nt_.nodes.new("ShaderNodeBsdfTransparent"); m_ = nt_.nodes.new("ShaderNodeMixShader"); m_.inputs[0].default_value = 0.7
o_ = nt_.nodes.new("ShaderNodeOutputMaterial"); nt_.links.new(e_.outputs[0], m_.inputs[1]); nt_.links.new(t_.outputs[0], m_.inputs[2]); nt_.links.new(m_.outputs[0], o_.inputs[0])
stk = mesh_obj("Bullet_streak", bm, C_FX, mst); stk.parent = bullet
hide_key(stk, [(1, False), (F_FIRE + 1, True), (F_WALL, False)])

# ================================================================== wall break: plugs, splinters, dust
for n_, fh in (("Plug_siding", F_WALL), ("Plug_osb", F_WALL + 3), ("Plug_drywall", F_DRY)):
    o = bpy.data.objects[n_]; hide_key(o, [(1, True), (fh, False)])
def mat_dust(name, col, dens):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt_ = m.node_tree; nt_.nodes.clear()
    vol = nt_.nodes.new("ShaderNodeVolumePrincipled"); vol.inputs["Color"].default_value = (*col, 1)
    nz = nt_.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 6; nz.inputs["Detail"].default_value = 4
    gr = nt_.nodes.new("ShaderNodeTexGradient"); gr.gradient_type = "SPHERICAL"; tc_ = nt_.nodes.new("ShaderNodeTexCoord")
    mm = nt_.nodes.new("ShaderNodeMath"); mm.operation = "MULTIPLY"; m2 = nt_.nodes.new("ShaderNodeMath"); m2.operation = "MULTIPLY"
    oi_ = nt_.nodes.new("ShaderNodeObjectInfo"); m3 = nt_.nodes.new("ShaderNodeMath"); m3.operation = "MULTIPLY"; m3.inputs[1].default_value = dens
    nt_.links.new(tc_.outputs["Object"], gr.inputs[0]); nt_.links.new(gr.outputs[0], mm.inputs[0]); nt_.links.new(nz.outputs[0], mm.inputs[1])
    nt_.links.new(mm.outputs[0], m2.inputs[0]); nt_.links.new(oi_.outputs["Alpha"], m2.inputs[1]); nt_.links.new(m2.outputs[0], m3.inputs[0])
    nt_.links.new(m3.outputs[0], vol.inputs["Density"])
    o_ = nt_.nodes.new("ShaderNodeOutputMaterial"); nt_.links.new(vol.outputs[0], o_.inputs["Volume"])
    return m
M_dust = mat_dust("M_dust", (0.85, 0.82, 0.76), 5.0)
M_drydust = mat_dust("M_drywall_dust", (0.95, 0.95, 0.93), 4.0)
M_splinter = bpy.data.materials["M_stud"]; M_chip = bpy.data.materials["M_siding_blue"]; M_dw = bpy.data.materials["M_drywall"]
M_fluff = bpy.data.materials["M_insulation"]
def piece(name, dims, mat, c=C_FX):
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co = V((v.co.x * dims[0], v.co.y * dims[1], v.co.z * dims[2])) + V([random.uniform(-0.15, 0.15) * d for d in dims])
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free(); me.materials.append(mat)
    o = bpy.data.objects.new(name, me); c.objects.link(o); return o
def ballistic(o, p0, v0, f0, f1, grav=0.4, drag=0.8, spin=6.0, floor=None, step=3, parent=None):
    ax = V((random.uniform(-1, 1), random.uniform(-1, 1), random.uniform(-1, 1))).normalized(); o.rotation_mode = "QUATERNION"
    hide_key(o, [(1, False), (f0, True)])
    if parent: o.parent = parent
    o.location = p0; kf(o, "location", f0 - 1)
    p = p0.copy(); v = v0.copy(); landed = False
    for f in range(f0, f1 + 1, step):
        dt = step / 60.0
        if not landed:
            v = v * math.exp(-drag * dt) + V((0, 0, -grav * dt)); p = p + v * dt
            if floor is not None and p.z < floor: p.z = floor; landed = True
        o.location = p; o.rotation_quaternion = Quaternion(ax, spin * (1 - math.exp(-(f - f0) / 90.0)) * (0.3 if landed else 1))
        kf(o, "location", f); kf(o, "rotation_quaternion", f)
        if landed or f - f0 > 520: break
HOLE = V((0, 0, 1.47))
for i in range(80):    # outside: siding splinters and paint chips kick back out of the entry hole
    o = piece("Splinter_out_%02d" % i, (random.uniform(0.006, 0.02), random.uniform(0.002, 0.005), random.uniform(0.015, 0.06)), random.choice([M_chip, M_chip, M_splinter]))
    a = random.uniform(0, 6.28); r = random.uniform(0.01, 0.06)
    p0 = HOLE + V((r * math.cos(a), -0.03, r * math.sin(a)))
    v0 = V((math.cos(a) * random.uniform(0.3, 1.2), -random.uniform(0.6, 1.8), math.sin(a) * random.uniform(0.3, 1.2) + 0.3))
    ballistic(o, p0, v0, F_WALL + random.randint(0, 3), 160, grav=1.2, drag=1.6, spin=10)
for i in range(4):
    pass
for i in range(70):    # inside: drywall chunks, splinters and insulation fluff burst into the room
    kind = random.random()
    if kind < 0.5: o = piece("Drywall_chunk_%02d" % i, [random.uniform(0.006, 0.018)] * 2 + [random.uniform(0.004, 0.012)], M_dw)
    elif kind < 0.8: o = piece("Splinter_in_%02d" % i, (random.uniform(0.003, 0.008), random.uniform(0.02, 0.07), random.uniform(0.003, 0.008)), M_splinter)
    else: o = piece("Fluff_%02d" % i, [random.uniform(0.008, 0.02)] * 3, M_fluff)
    a = random.uniform(0, 6.28); r = random.uniform(0.02, 0.09)
    p0 = HOLE + V((r * math.cos(a), 0.17, r * math.sin(a)))
    cone = random.uniform(0.5, 0.9)
    v0 = V((math.cos(a) * cone * 1.6, random.uniform(0.1, 0.4), math.sin(a) * cone + 0.1))
    ballistic(o, p0, v0, F_DRY + random.randint(0, 4), F_END, grav=1.6, drag=1.6, floor=FZ + 0.005)
def puff(name, p0, drift, f0, r0, r1, mat, dur=240):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=1.0, location=p0); o = bpy.context.active_object; o.name = name
    for c in list(o.users_collection): c.objects.unlink(o)
    C_FX.objects.link(o); o.data.materials.append(mat)
    hide_key(o, [(1, False), (f0, True), (f0 + dur, False)])
    for f, u in ((f0, 0.0), (f0 + dur * 0.25, 0.45), (f0 + dur * 0.6, 0.8), (f0 + dur, 1.0)):
        s_ = r0 + (r1 - r0) * u; o.scale = (s_, s_ * 0.8, s_); o.location = p0 + drift * u
        o.color = (1, 1, 1, (1 - u) ** 1.5); kf(o, "scale", int(f)); kf(o, "location", int(f)); kf(o, "color", int(f))
    return o
for i in range(3):
    puff("Dust_out_%d" % i, HOLE + V((random.uniform(-0.04, 0.04), -0.06, random.uniform(-0.04, 0.04))), V((random.uniform(-0.2, 0.2), -0.35, 0.12)), F_WALL + i * 2, 0.02, 0.22, M_dust, 120)
for i in range(4):
    sx_ = 1 if i % 2 else -1
    puff("Dust_in_%d" % i, HOLE + V((sx_ * random.uniform(0.06, 0.14), 0.22 + 0.04 * i, random.uniform(-0.08, 0.08))), V((sx_ * random.uniform(0.1, 0.2), 0.12 + 0.04 * i, random.uniform(-0.05, 0.12))), F_DRY + 2 * i, 0.03, 0.18, M_drydust, 200)
puff("Dust_smoke_gun", MUZ + V((0, 0.06, 0.01)), V((0.05, 0.25, 0.12)), F_FIRE + 1, 0.01, 0.14, M_dust, 60)
# impact at the cover: flakes + a puff (box local, they ride with the box)
for i in range(24):
    o = piece("Cover_flake_%02d" % i, [random.uniform(0.002, 0.005)] * 2 + [0.0008], random.choice([M_front, M_side]))
    a = random.uniform(0, 6.28); p0 = HIT_L + V((0.005 * math.cos(a), -0.002, 0.005 * math.sin(a)))
    v0 = V((math.cos(a) * random.uniform(0.04, 0.12), -random.uniform(0.05, 0.16), math.sin(a) * random.uniform(0.04, 0.12)))
    ballistic(o, p0, v0, F_HIT + random.randint(0, 4), 700, grav=0.12, drag=2.2, step=3, parent=broot)
pb_ = puff("Dust_box", HIT_L + V((0, -0.02, 0)), V((0, -0.05, 0.03)), F_HIT + 1, 0.008, 0.07, M_drydust, 150); pb_.parent = broot

# ================================================================== the same box cut in half: studio cross-section
SEC0 = V((40.0, 40.0, 10.0))
sroot = bpy.data.objects.new("SectionRoot", None); C_SEC.objects.link(sroot); sroot.location = SEC0
def sec(o): o.parent = sroot; return o
LAY = [  # name, thickness (m), material, has disc
    ("cover", 0.005, P("M_sec_cover", hexc("#13235A"), 0.35, coat=0.4), None),
    ("tray1", 0.016, P("M_sec_tray", (0.03, 0.03, 0.035), 0.5), "Disc_1"),
    ("tray2", 0.016, bpy.data.materials["M_sec_tray"], "Disc_2"),
    ("divider", 0.004, P("M_sec_card_red", hexc("#C8322E"), 0.7), None),
    ("manual", 0.030, None, None),
    ("sleeve", 0.010, P("M_sec_sleeve", hexc("#F4F1EA"), 0.6), "Disc_3"),
    ("insert", 0.020, P("M_sec_card", hexc("#B07A45"), 0.85), None),
    ("artbook", 0.064, None, None),
    ("back", 0.005, bpy.data.materials["M_sec_cover"], None)]
def page_material(name, base, line, period):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree
    tc = nt.nodes.new("ShaderNodeTexCoord"); sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    wv = nt.nodes.new("ShaderNodeTexWave"); wv.wave_type = "BANDS"; wv.bands_direction = "X"; wv.inputs["Scale"].default_value = 1.0
    mul = nt.nodes.new("ShaderNodeVectorMath"); mul.operation = "SCALE"; mul.inputs["Scale"].default_value = 1.0 / period
    com = nt.nodes.new("ShaderNodeCombineXYZ")
    cr = nt.nodes.new("ShaderNodeValToRGB"); cr.color_ramp.elements[0].color = (*line, 1); cr.color_ramp.elements[1].color = (*base, 1); cr.color_ramp.elements[0].position = 0.15
    nt.links.new(tc.outputs["Object"], sep.inputs[0]); nt.links.new(sep.outputs["Y"], com.inputs["X"]); nt.links.new(com.outputs[0], mul.inputs[0])
    nt.links.new(mul.outputs[0], wv.inputs["Vector"]); nt.links.new(wv.outputs["Fac"], cr.inputs[0])
    b = nt.nodes["Principled BSDF"]; nt.links.new(cr.outputs[0], b.inputs["Base Color"]); b.inputs["Roughness"].default_value = 0.8
    return m
M_pages = page_material("M_sec_pages", hexc("#FBF6E6"), hexc("#B9AE92"), 0.0016)
M_artpages = page_material("M_sec_artpages", hexc("#FFF8EC"), hexc("#C9B9A0"), 0.0022)
M_bookcover = P("M_sec_bookcover", hexc("#2BB3A3"), 0.5)
M_disc = P("M_sec_disc", (0.80, 0.90, 1.0), 0.15, metal=0.0, emit=(0.55, 0.8, 1.0), ew=1.2)
M_shell = P("M_sec_shell", hexc("#0E1A45"), 0.35, coat=0.4)
SHELL = 0.004
y = -BD / 2; LAYY = {}
for nm, th, mat, disc in LAY:
    y0, y1 = y, y + th; LAYY[nm] = (y0, y1)
    zlo, zhi = (-BH / 2, BH / 2) if nm in ("cover", "back") else (-BH / 2 + SHELL, BH / 2 - SHELL)
    if nm == "manual":
        sec(box("Sec_" + nm, C_SEC, -BW / 2, 0, y0, y1, zlo + 0.01, zhi - 0.01, M_pages))
        sec(box("Sec_manual_gap", C_SEC, -BW / 2, -0.0002, y0, y1, zlo, zhi, P("M_sec_foam", (0.02, 0.02, 0.025), 0.9)))
    elif nm == "artbook":
        sec(box("Sec_artbook_cf", C_SEC, -BW / 2, 0, y0 + 0.001, y0 + 0.004, zlo + 0.006, zhi - 0.006, M_bookcover))
        sec(box("Sec_artbook_cb", C_SEC, -BW / 2, 0, y1 - 0.004, y1 - 0.001, zlo + 0.006, zhi - 0.006, M_bookcover))
        sec(box("Sec_artbook_pages", C_SEC, -BW / 2, 0, y0 + 0.004, y1 - 0.004, zlo + 0.010, zhi - 0.010, M_artpages))
        sec(box("Sec_artbook_spine", C_SEC, -BW / 2, -0.0002, y0 + 0.001, y1 - 0.001, zlo, zhi, bpy.data.materials["M_sec_foam"]))
    else:
        sec(box("Sec_" + nm, C_SEC, -BW / 2, 0, y0, y1, zlo, zhi, mat))
    y = y1
print("SECTION depth", y + BD / 2, LAYY)
for zz in (-BH / 2, BH / 2 - SHELL):
    sec(box("Sec_shell", C_SEC, -BW / 2, 0, -BD / 2 + 0.005, BD / 2 - 0.005, zz, zz + SHELL, M_shell))
# discs on the cut face: bright lines across the trays; each breaks around the bullet when the nose reaches it
DISC_R = 0.06
def disc_y(nm): y0, y1 = LAYY[nm]; return (y0 + y1) / 2
DISCS = {"Disc_1": disc_y("tray1"), "Disc_2": disc_y("tray2"), "Disc_3": disc_y("sleeve")}
def cross(yl):
    return min(f for f in range(F_HIT, F_STOP + 1) if (-BD / 2 + depth(f)) >= yl)
GAP = 0.013
for dn, dy_ in DISCS.items():
    fh = cross(dy_)
    whole = sec(box("Sec_" + dn, C_SEC, -BW / 2, 0.0004, dy_ - 0.0012, dy_ + 0.0012, HIT_L.z - DISC_R, HIT_L.z + DISC_R, M_disc))
    lo = sec(box("Sec_" + dn + "_lo", C_SEC, -BW / 2, 0.0004, dy_ - 0.0012, dy_ + 0.0012, HIT_L.z - DISC_R, HIT_L.z - GAP, M_disc))
    hi = sec(box("Sec_" + dn + "_hi", C_SEC, -BW / 2, 0.0004, dy_ - 0.0012, dy_ + 0.0012, HIT_L.z + GAP, HIT_L.z + DISC_R, M_disc))
    hide_key(whole, [(1, True), (fh, False)]); hide_key(lo, [(1, False), (fh, True)]); hide_key(hi, [(1, False), (fh, True)])
    for i in range(14):   # shards blow out of the gap (toward the camera side and up/down), spinning, in slow motion
        bm = bmesh.new(); s_ = random.uniform(0.0015, 0.004)
        vs = [bm.verts.new((random.uniform(-0.6, 0.6) * s_, random.uniform(-0.15, 0.15) * s_, random.uniform(-1, 1) * s_)) for _ in range(3)]
        bm.faces.new(vs); bmesh.ops.solidify(bm, geom=bm.faces[:], thickness=0.0006)
        o = mesh_obj("Sec_shard_%s_%02d" % (dn, i), bm, C_SEC, M_disc); o.parent = sroot
        zz = HIT_L.z + random.choice([-1, 1]) * random.uniform(0.002, GAP)
        p0 = V((0.002, dy_, zz))
        v0 = V((random.uniform(0.01, 0.05), random.uniform(-0.004, 0.012), (zz - HIT_L.z) * random.uniform(1.5, 4.0)))
        ballistic(o, p0, v0, fh, min(F_END, fh + 260), grav=0.0, drag=1.4, spin=4.0, step=2, parent=sroot)
        o.location = p0
# the torn channel behind the bullet (dark strip on the cut face)
bm = cube_bm(0.0, 0.0006, 0.0, 1.0, -0.0065, 0.0065)
chan = mesh_obj("Sec_channel", bm, C_SEC, M_torn); chan.parent = sroot
bul2 = bpy.data.objects.new("Bullet_section", bullet.data); C_SEC.objects.link(bul2); bul2.parent = sroot
bul2.rotation_mode = "QUATERNION"; bul2.modifiers.new("sub", "SUBSURF").levels = 1
BUL_L = 0.028
for f in range(F_HIT - 1, F_END + 1):
    dpt = depth(f); nose = V((0.0, -BD / 2 + dpt, HIT_L.z))
    bul2.location = nose; bul2.rotation_quaternion = Quaternion(V((0, 1, 0)), F_HIT * 0.5 + 0.5 * 40 * (1 - math.exp(-(f - F_HIT) / 40)))
    kf(bul2, "location", f); kf(bul2, "rotation_quaternion", f)
    ln = max(0.0005, dpt - BUL_L * 0.6)
    chan.location = (0.0, -BD / 2 - 0.0005, HIT_L.z); chan.scale = (1, ln + 0.0005, 1); kf(chan, "location", f); kf(chan, "scale", f)
# energy rings where the nose meets each layer (emissive, expanding, fading)
ringmat = bpy.data.materials.new("M_energy_ring"); ringmat.use_nodes = True
nt = ringmat.node_tree; nt.nodes.clear()
oi = nt.nodes.new("ShaderNodeObjectInfo"); em = nt.nodes.new("ShaderNodeEmission"); tr = nt.nodes.new("ShaderNodeBsdfTransparent")
ad = nt.nodes.new("ShaderNodeAddShader"); mo = nt.nodes.new("ShaderNodeOutputMaterial")
mul = nt.nodes.new("ShaderNodeMath"); mul.operation = "MULTIPLY"; mul.inputs[1].default_value = 25.0
nt.links.new(oi.outputs["Color"], em.inputs["Color"]); nt.links.new(oi.outputs["Alpha"], mul.inputs[0]); nt.links.new(mul.outputs[0], em.inputs["Strength"])
nt.links.new(em.outputs[0], ad.inputs[0]); nt.links.new(tr.outputs[0], ad.inputs[1]); nt.links.new(ad.outputs[0], mo.inputs[0])
RINGS = [(cross(DISCS["Disc_1"]), (0.3, 0.8, 1.0)), (cross(DISCS["Disc_2"]), (0.3, 0.8, 1.0)), (cross(LAYY["divider"][0]), (1.0, 0.6, 0.25)),
         (cross(LAYY["manual"][0] + 0.010), (1.0, 0.8, 0.45)), (cross(LAYY["manual"][0] + 0.022), (1.0, 0.8, 0.45)),
         (cross(DISCS["Disc_3"]), (0.3, 0.8, 1.0)), (cross(LAYY["insert"][0] + 0.002), (1.0, 0.55, 0.2))]
for i, (fr, col) in enumerate(RINGS):
    bpy.ops.mesh.primitive_torus_add(major_radius=1.0, minor_radius=0.04, major_segments=48, minor_segments=8)
    o = bpy.context.active_object; o.name = "Sec_ring_%02d" % i
    for c_ in list(o.users_collection): c_.objects.unlink(o)
    C_SEC.objects.link(o); o.data.materials.append(ringmat); o.parent = sroot
    o.rotation_euler = (math.radians(90), 0, 0); o.location = (0.0, -BD / 2 + depth(fr) - 0.002, HIT_L.z)
    for f, s_, a in ((fr - 1, 0.003, 0.0), (fr, 0.005, 1.0), (fr + 24, 0.016, 0.5), (fr + 60, 0.024, 0.0)):
        o.scale = (s_, s_, s_); o.color = (*col, a); kf(o, "scale", f); kf(o, "color", f)
    hide_key(o, [(1, False), (fr - 1, True), (fr + 62, False)])
# studio card behind the section (the approved sky-blue gradient) + soft key and fill
mbd = bpy.data.materials.new("M_sec_backdrop"); mbd.use_nodes = True; nt_ = mbd.node_tree; nt_.nodes.clear()
tc_ = nt_.nodes.new("ShaderNodeTexCoord"); gr_ = nt_.nodes.new("ShaderNodeTexGradient"); gr_.gradient_type = "LINEAR"
sx_ = nt_.nodes.new("ShaderNodeSeparateXYZ"); cr_ = nt_.nodes.new("ShaderNodeValToRGB")
cr_.color_ramp.elements[0].color = (*hexc("#E8F7FF"), 1); cr_.color_ramp.elements[1].color = (*hexc("#4FC3F7"), 1)
em_ = nt_.nodes.new("ShaderNodeEmission"); em_.inputs["Strength"].default_value = 1.6; o_ = nt_.nodes.new("ShaderNodeOutputMaterial")
nt_.links.new(tc_.outputs["Generated"], sx_.inputs[0]); nt_.links.new(sx_.outputs["Y"], cr_.inputs[0])
nt_.links.new(cr_.outputs[0], em_.inputs[0]); nt_.links.new(em_.outputs[0], o_.inputs[0])
bd_ = box("Sec_backdrop", C_SEC, -0.02, 0.0, -1.6, 1.6, -1.6, 1.6, mbd); bd_.parent = sroot; bd_.location = (-0.55, 0, 0)
for nm_, loc_, e_, sz_ in (("L_sec_key", (0.45, -0.35, 0.40), 9.0, 0.35), ("L_sec_fill", (0.50, 0.40, -0.10), 4.0, 0.5)):
    ld = bpy.data.lights.new(nm_, "AREA"); ld.size = sz_; ld.energy = e_; ld.color = (1.0, 0.97, 0.93)
    lo_ = bpy.data.objects.new(nm_, ld); C_SEC.objects.link(lo_); lo_.parent = sroot; lo_.location = loc_
    lo_.rotation_mode = "QUATERNION"; lo_.rotation_quaternion = (V((0, 0, 0)) - V(loc_)).to_track_quat('-Z', 'Y')

# ================================================================== room dressing: logo poster, lights
LOGO = os.path.join(BL, "assets", "brand", "DaKrasFilms_logo_dark.png")
ml = bpy.data.materials.new("M_logo_poster"); ml.use_nodes = True; nt = ml.node_tree
ti = nt.nodes.new("ShaderNodeTexImage"); ti.image = bpy.data.images.load(LOGO); ti.image.pack(); ti.extension = "CLIP"
mx = nt.nodes.new("ShaderNodeMixRGB"); mx.inputs[1].default_value = (0.97, 0.96, 0.92, 1)
tcl = nt.nodes.new("ShaderNodeTexCoord"); mpl = nt.nodes.new("ShaderNodeMapping")
mpl.inputs["Location"].default_value = (-0.125, -0.409, 0); mpl.inputs["Scale"].default_value = (1.25, 1.818, 1)
nt.links.new(tcl.outputs["UV"], mpl.inputs[0]); nt.links.new(mpl.outputs[0], ti.inputs[0])
nt.links.new(ti.outputs["Alpha"], mx.inputs[0]); nt.links.new(ti.outputs["Color"], mx.inputs[2])
bl_ = nt.nodes["Principled BSDF"]; nt.links.new(mx.outputs[0], bl_.inputs["Base Color"]); bl_.inputs["Roughness"].default_value = 0.5
LOGO_X, LOGO_Z, LOGO_W = ENV("LOGOX", "1.02"), ENV("LOGOZ", "2.02"), 0.62
bpy.ops.mesh.primitive_plane_add(size=1.0); lp = bpy.context.active_object; lp.name = "Logo_poster"
for c_ in list(lp.users_collection): c_.objects.unlink(lp)
C_ROOM.objects.link(lp); lp.data.materials.append(ml)
lp.rotation_euler = (math.radians(90), 0, 0); lp.scale = (LOGO_W, LOGO_W * 0.62, 1); lp.location = (LOGO_X, 4.6 - 0.012, LOGO_Z)
fr_ = box("Logo_frame", C_ROOM, LOGO_X - LOGO_W / 2 - 0.02, LOGO_X + LOGO_W / 2 + 0.02, 4.6 - 0.010, 4.6, LOGO_Z - LOGO_W * 0.31 - 0.02, LOGO_Z + LOGO_W * 0.31 + 0.02, P("M_logo_frame", (0.05, 0.05, 0.06), 0.4))
for pn in ("Poster1",):   # the old poster behind his head would fight with the logo poster: moved left
    po = bpy.data.objects.get(pn)
    if po: po.location.x = -0.85
fk = bpy.data.lights.new("L_face_key", "AREA"); fk.size = 0.6; fk.color = (1.0, 0.93, 0.86); fk.energy = 10.0
fko = bpy.data.objects.new("L_face_key", fk); C_ROOM.objects.link(fko)
fko.location = (0.9, 2.1, 1.95); fko.rotation_mode = "QUATERNION"; fko.rotation_quaternion = (V((0, 3.2, 1.75)) - V((0.9, 2.1, 1.95))).to_track_quat('-Z', 'Y')
hl = bpy.data.lights.new("L_hole_glint", "POINT"); hl.shadow_soft_size = 0.003; hl.color = (1.0, 0.9, 0.75); hl.energy = 0.0
hlo = bpy.data.objects.new("L_hole_glint", hl); C_BOX.objects.link(hlo); hlo.parent = broot; hlo.location = HIT_L + V((0.002, 0.012, 0.003))
for f, e in ((1, 0.0), (1038, 0.0), (1039, 2.0), (1136, 2.0), (1137, 0.0), (1213, 0.0), (1214, 0.8), (F_END, 0.04)):
    hl.energy = e; hl.keyframe_insert("energy", frame=f)
cl = bpy.data.lights.new("L_cavity", "POINT"); cl.shadow_soft_size = 0.02; cl.color = (1.0, 0.9, 0.75)
clo = bpy.data.objects.new("L_cavity", cl); bpy.data.collections["Wall"].objects.link(clo); clo.location = (0.0, 0.08, 1.59)
cl.energy = 0.0
# room life: LED strip colour drift
led = bpy.data.materials["M_led"].node_tree.nodes["Principled BSDF"]
for f in range(1, F_END + 1, 24):
    led.inputs["Emission Color"].default_value = (*colorsys.hsv_to_rgb((f / 600.0) % 1.0, 0.8, 1.0), 1)
    led.inputs["Emission Color"].keyframe_insert("default_value", frame=f)

# ================================================================== camera: one camera, hard cuts at the shot boundaries
cam_d = bpy.data.cameras.new("CAM_Film"); cam_d.sensor_fit = "AUTO"; cam_d.clip_start = 0.01; cam_d.clip_end = 300
cam = bpy.data.objects.new("CAM_Film", cam_d); sc.collection.objects.link(cam); sc.camera = cam
cam_d.dof.use_dof = True
def lerp(a, b, t): return a + (b - a) * t
def bul(f): return nose_world(f)
def head_pt(f):
    sc.frame_set(f); return man.matrix_world @ man.pose.bones["head"].head
def box_pt(f, p=V((0, 0, 0))): return box_M(f) @ p
def secw(p): return SEC0 + p
def shot_static(c, a, lens, fs=8.0):
    return lambda f, t: (c, a, lens, fs, (a - c).length)
SHOTS = []   # (first frame, last frame, fn(f, t) -> (cam pos, aim, lens, fstop, focus distance))
# S1 who fires: side medium on the shooter, gun + flash, bullet leaves screen right (+Y = screen right in every side shot)
SHOTS.append((1, 54, lambda f, t: (V((2.05, -30.75, 1.30)) + V((0, 0.10 * t, 0.02 * t)), V((0.0, -30.62, 1.30)), 38, 8.0, 2.1)))
# S2a tracked close-up of the bullet over the lawn (rear 3/4, house ahead)
def s2a(f, t):
    b = bul(f); c = b + V((0.20, -0.17, 0.035)); a = b + V((0.0, 0.03, 0.0)); return c, a, 55, 16.0, (b - c).length
SHOTS.append((55, 96, s2a))
# S2b outside the wall: static, the bullet punches the siding, splinters and dust kick back
SHOTS.append((97, 140, shot_static(V((1.55, -2.55, 1.42)), V((-0.02, 0.0, 1.47)), 70, 8.0)))
# S2c inside the room: static, the drywall bursts and the bullet comes through
SHOTS.append((141, 168, shot_static(V((1.45, 1.85, 1.50)), V((0.05, 0.30, 1.46)), 40, 8.0)))
# S3a bullet POV: behind and beside the bullet, the man ahead holding his box (approach path)
def s3a(f, t):
    b = bul(f); c = b + V((0.05, -0.25, 0.045)); a = b + V((0.0, 0.6, 0.0)); return c, a, 28, 11.0, (b - c).length
SHOTS.append((169, 222, s3a))
# S3b medium on him: chest and face, smiling at the box he is turning (logo poster behind)
SHOTS.append((223, 276, lambda f, t: (V((-0.42, 2.02, 1.78)) + V((0.06 * t, 0.04 * t, 0)), V((0.02, 3.10, 1.64)), 36, 8.0, 1.25)))
# S4a his hands on the new box, he lifts and tilts it (close, both hands with their forearms)
def s4a(f, t):
    bc = box_pt(f); c = bc + V((0.30, -0.78, 0.16)) + V((-0.10 * t, 0.04 * t, 0)); return c, bc + V((0, 0, 0.03)), 38, 8.0, (bc - c).length
SHOTS.append((277, 353, s4a))
# S4b face medium close: happy, then he hears something and looks up from the box
def s4b(f, t):
    hd = head_pt(f); c = V((0.42, 2.20, 1.80)) + V((-0.05 * t, 0.03 * t, 0)); return c, hd + V((0, 0, -0.17)), 40, 8.0, (hd - c).length
SHOTS.append((354, 432, s4b))
# S4c bullet close-up again: tracked from the side, the box and his hands ahead (screen right)
def s4c(f, t):
    b = bul(f); c = b + V((0.29, -0.06, 0.05)); a = b + V((0.0, 0.05, 0.0)); return c, a, 34, 11.0, (b - c).length
SHOTS.append((433, 496, s4c))
# S5a side profile: the bullet flies in from screen left and slams into the box in his hands
SHOTS.append((497, 551, shot_static(V((1.02, 2.80, 1.60)), V((0.0, 3.00, 1.60)), 36, 8.0)))
# S5b his reaction (face + top of the box with the hole)
SHOTS.append((552, 602, lambda f, t: (V((0.30, 2.18, 1.74)) + V((0.0, 0.03 * t, 0)), V((0.0, 3.05, 1.62)), 38, 8.0, 0.95)))
# S6 the case cracks: front close on the box, hands at both sides
def s6(f, t):
    c = box_pt(f, V((0.10, -0.88, -0.02))) + V((0, 0.05 * t, 0)); a = box_pt(f, V((0.0, -BD / 2, 0.15))); return c, a, 35, 11.0, (a - c).length
SHOTS.append((603, 674, s6))
# S7 cross-section: the discs shatter
def s_sec(dist, lens, track, zoff=0.0, yoff=0.0):
    def fn(f, t):
        nose_y = -BD / 2 + depth(f)
        ty = lerp(-BD / 2 + 0.02, nose_y, track) + yoff
        a = secw(V((0.0, ty, HIT_L.z + zoff))); c = a + V((dist * 0.87, -dist * 0.48, 0.03)); return c, a, lens, 11.0, dist
    return fn
SHOTS.append((675, 754, s_sec(0.34, 50, 1.0, 0.0, -0.005)))
# S8a cross-section: layer by layer (pages), energy rings
SHOTS.append((755, 830, s_sec(0.40, 50, 1.0, 0.0, -0.010)))
# S8b his face: staring down at the box, breathing hard
def s8b(f, t):
    hd = head_pt(f); c = V((-0.38, 2.25, 1.76)) + V((0.08 * t, 0, 0)); return c, hd + V((0.0, 0.0, -0.20)), 38, 8.0, (hd - c).length
SHOTS.append((831, 890, s8b))
# S8c cross-section: the bullet slowing in the card insert
SHOTS.append((891, 940, s_sec(0.36, 50, 1.0, 0.0, -0.012)))
# S9 cross-section: it stops halfway; slow push in on the whole section
def s9(f, t):
    a = secw(V((0.0, 0.0, 0.0))); a = a.lerp(secw(V((0.0, -BD / 2 + depth(F_STOP) - 0.01, HIT_L.z))), 0.5 * t)
    d = lerp(0.46, 0.34, smooth(t)); c = a + V((d * 0.87, -d * 0.48, 0.05)); return c, a, 50, 11.0, d
SHOTS.append((941, 1038, s9))
# S10a buried: macro into the hole, the bullet's base deep inside, cracks round it
def s10a(f, t):
    c = box_pt(f, HIT_L + V((0.02, -0.30 + 0.06 * t, 0.015))); a = box_pt(f, HIT_L + V((0.0, 0.02, 0.0))); return c, a, 60, 16.0, (a - c).length
SHOTS.append((1039, 1092, s10a))
# S10b he tilts the box up and peers into the hole
def s10b(f, t):
    hd = head_pt(f); bc = box_pt(f); a = hd.lerp(bc, 0.55); c = a + V((0.55, -0.72, 0.06)); return c, a, 36, 8.0, (a - c).length
SHOTS.append((1093, 1136, s10b))
# S11a he looks up at the hole in the wall, alive (face + box)
SHOTS.append((1137, 1212, lambda f, t: (V((0.48, 2.05, 1.70)) + V((-0.06 * t, 0.04 * t, 0.01 * t)), V((0.0, 3.08, 1.62)), 36, 8.0, 1.25)))
# S11b payoff: relief, the box with the bullet still in it held up at his chest, logo poster behind
SHOTS.append((1213, F_END, lambda f, t: (V((-0.30, 2.12, 1.66)) + V((0.04 * t, 0.08 * t, 0.0)), V((0.08, 3.04, 1.62)), 34, 8.0, 1.05)))
CAMLOG = []
cam.rotation_mode = "QUATERNION"
for f0, f1, fn in SHOTS:
    for f in range(f0, f1 + 1):
        t = (f - f0) / max(1, f1 - f0)
        c, a, lens, fs, fd = fn(f, t)
        cam.location = c; cam.rotation_quaternion = (a - c).normalized().to_track_quat('-Z', 'Y')
        cam_d.lens = lens; cam_d.dof.aperture_fstop = fs; cam_d.dof.focus_distance = max(0.05, fd)
        kf(cam, "location", f); kf(cam, "rotation_quaternion", f); cam_d.keyframe_insert("lens", frame=f)
        cam_d.dof.keyframe_insert("aperture_fstop", frame=f); cam_d.dof.keyframe_insert("focus_distance", frame=f)
        CAMLOG.append((f, tuple(round(x, 4) for x in c), tuple(round(x, 4) for x in a), lens))
for idb in (cam, cam_d):
    for fc in fcurves_of(idb):
        for k in fc.keyframe_points: k.interpolation = "CONSTANT"
# debris never near the lens: any wall piece passing within 0.6 m of the camera is hidden for that whole shot
DEB = [o for o in bpy.data.objects if o.name.startswith(("Drywall_chunk", "Splinter_in", "Fluff", "Splinter_out"))]
for f0, f1, fn in SHOTS:
    if f1 < F_WALL: continue
    near = set()
    for f in range(f0, f1 + 1, 2):
        sc.frame_set(f); c = cam.matrix_world.translation
        for o in DEB:
            if not o.hide_render and (o.matrix_world.translation - c).length < 0.6: near.add(o)
    for o in near:
        sc.frame_set(f0 - 1); was = not o.hide_render
        hide_key(o, [(f0 - 1, was), (f0, False), (f1 + 1, was)])
    print("DEBRIS_HIDDEN shot", f0, len(near))
# catchlight: a tiny light riding with the camera, seen only in reflections (eyes), no diffuse light on the face
ctl = bpy.data.lights.new("L_catchlight", "AREA"); ctl.size = 0.06; ctl.energy = 1.5; ctl.color = (1, 1, 1)
cto = bpy.data.objects.new("L_catchlight", ctl); sc.collection.objects.link(cto); cto.parent = cam; cto.location = (0.12, 0.16, 0.0)
cto.visible_diffuse = False; cto.visible_transmission = False; cto.visible_volume_scatter = False; cto.visible_camera = False
json.dump(CAMLOG[::10], open(os.path.join(V11, "camera_path.json"), "w"))
json.dump([{"beat": i + 1, "frame": f, "first_words": w} for i, (f, w) in enumerate(BEATS)], open(os.path.join(V11, "beats.json"), "w"), indent=1)
json.dump([{"shot": i + 1, "first": a, "last": b} for i, (a, b, _) in enumerate(SHOTS)], open(os.path.join(V11, "shots.json"), "w"), indent=1)
sc.cycles.transparent_max_bounces = 64
sc.frame_start, sc.frame_end = 1, F_END
sc.frame_set(1)
print("SHOTS_DONE", len(SHOTS))
bpy.ops.wm.save_as_mainfile(filepath=OUT)
