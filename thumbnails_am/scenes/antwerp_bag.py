"""Antwerp thumbnail A1, "the rubbish bag": a black bin bag split open on a sunlit autumn forest floor beside the
motorway. Spilling toward the camera: torn diamond papers (white, blue-lined), loose glittering diamonds, a VHS
security tape with its ribbon unspooled across the leaves, and a half-eaten salami sandwich. No text, no people.
Bag and spill in the right/lower part of the frame; the soft gold forest at upper left stays clean for the title.
    PREVIEW=0.4 SPP=48 blender -b --python antwerp_bag.py"""
import os, sys, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tcommon as T
C = T.use("antwerp")
import bpy, bmesh
import numpy as np
from mathutils import Vector, Matrix
import ph, props as PR, sets as S, sets3 as S3
E = os.environ.get
sc = T.res_setup(int(E("SPP", "256")), noise=0.01)
rng = random.Random(int(E("SEED", "4")))
BAG = Vector((float(E("BX", "0.35")), float(E("BY", "0.45")), 0))

# ---------------------------------------------------------------- ground: autumn leaf litter, gently uneven
import glob
GD = os.path.join(T.ROOTS["antwerp"], "assets", "polyhaven", E("GROUND", "forest_leaves_02"))
ph.texture(E("GROUND", "forest_leaves_02"))                 # make sure the maps are downloaded
leaves = bpy.data.materials.new("leaf_litter"); leaves.use_nodes = True
N = leaves.node_tree.nodes; L = leaves.node_tree.links; pg = N["Principled BSDF"]
uvn = N.new("ShaderNodeUVMap"); mpn = N.new("ShaderNodeMapping"); mpn.inputs['Scale'].default_value = (20, 20, 1)
L.new(uvn.outputs['UV'], mpn.inputs['Vector'])
def _img(pat, col):
    t = N.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(glob.glob(os.path.join(GD, pat))[0], check_existing=True)
    t.image.colorspace_settings.name = 'sRGB' if col else 'Non-Color'; L.new(mpn.outputs[0], t.inputs['Vector']); return t
dif = _img("*diff*", True); hs = N.new("ShaderNodeHueSaturation"); hs.inputs['Saturation'].default_value = float(E("GSAT", "1.2"))
hs.inputs['Value'].default_value = float(E("GVAL", "1.0")); hs.inputs['Hue'].default_value = float(E("GHUE", "0.505"))
L.new(dif.outputs['Color'], hs.inputs['Color']); L.new(hs.outputs['Color'], pg.inputs['Base Color'])
L.new(_img("*rough*", False).outputs['Color'], pg.inputs['Roughness'])
nm = N.new("ShaderNodeNormalMap"); L.new(_img("*nor_gl*", False).outputs['Color'], nm.inputs['Color']); L.new(nm.outputs[0], pg.inputs['Normal'])
bpy.ops.mesh.primitive_plane_add(size=40, location=(0, 10, 0))
gnd = bpy.context.active_object; gnd.name = "ground"
sd = gnd.modifiers.new("sub", "SUBSURF"); sd.subdivision_type = 'SIMPLE'; sd.levels = sd.render_levels = 6
dtx = bpy.data.textures.new("gnd_noise", 'CLOUDS'); dtx.noise_scale = 0.6
dp = gnd.modifiers.new("disp", "DISPLACE"); dp.texture = dtx; dp.strength = 0.012; dp.mid_level = 0.5
gnd.data.materials.append(leaves)
# small heaps of real 3D leaves near camera would cost a lot; the texture's normal map carries the detail



def vmin_z(objs):
    dg = bpy.context.evaluated_depsgraph_get(); z = 1e9; P = []
    for o in objs:
        oe = o.evaluated_get(dg); me = oe.to_mesh()
        P += [o.matrix_world @ v.co for v in me.vertices]; oe.to_mesh_clear()
    import numpy as _np
    A = _np.array([tuple(q) for q in P]); return Vector(A.min(0).tolist()), Vector(A.max(0).tolist())

# ---------------------------------------------------------------- the bin bag, lying on its side, split
bag_r, bag_ms = ph.model("trashbag", loc=(0, 0, 0), rot_z=0, scale=1.0)
lo, hi = ph.bounds(bag_ms)
bag_r.location = BAG - Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z - 0.01))
bag_r.rotation_euler = (math.radians(float(E("BRX", "-12"))), 0, math.radians(float(E("BRZ", "20"))))
bpy.context.view_layer.update()
lo, hi = vmin_z(bag_ms); bag_r.location.z -= lo.z + 0.01; bag_r.location.x += BAG.x - (lo.x + hi.x) / 2
bag_r.location.y += BAG.y - (lo.y + hi.y) / 2
bpy.context.view_layer.update()
lo, hi = vmin_z(bag_ms)
# the split: a ragged hole torn in the camera side of the bag (boolean with a lumpy blob), plastic given thickness
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=4, radius=float(E("HOLE_R", "0.12")),
                                      location=(BAG.x - 0.06, lo.y + float(E("HOLE_Y", "0.07")), float(E("HOLE_Z", "0.12"))))
cutter = bpy.context.active_object; cutter.name = "tear"; cutter.scale = (1.4, 0.8, 0.8)
ctx = bpy.data.textures.new("tear_noise", 'CLOUDS'); ctx.noise_scale = 0.05
cd = cutter.modifiers.new("d", "DISPLACE"); cd.texture = ctx; cd.strength = 0.06
cutter.hide_render = True; cutter.display_type = 'WIRE'
for o in bag_ms:
    sol = o.modifiers.new("plastic", "SOLIDIFY"); sol.thickness = 0.0015
    bo = o.modifiers.new("tear", "BOOLEAN"); bo.object = cutter; bo.operation = 'DIFFERENCE'; bo.solver = 'EXACT'
    o.modifiers.move(len(o.modifiers) - 1, 0)
blk = bpy.data.materials.new("binbag"); blk.use_nodes = True; p = blk.node_tree.nodes["Principled BSDF"]
p.inputs['Base Color'].default_value = (0.008, 0.008, 0.01, 1); p.inputs['Roughness'].default_value = 0.22
p.inputs['Coat Weight'].default_value = 0.6; p.inputs['Coat Roughness'].default_value = 0.08
for o in bag_ms:
    for m in o.data.materials:
        pm = m.node_tree.nodes.get("Principled BSDF")
        if pm:
            for l in list(pm.inputs['Base Color'].links):
                m.node_tree.links.remove(l)
            pm.inputs['Base Color'].default_value = (0.01, 0.01, 0.012, 1); pm.inputs['Coat Weight'].default_value = 0.6
            pm.inputs['Coat Roughness'].default_value = 0.1
            for l in list(pm.inputs['Roughness'].links):
                m.node_tree.links.remove(l)
            pm.inputs['Roughness'].default_value = 0.3
    ss = o.modifiers.new("smooth", "SUBSURF"); ss.levels = ss.render_levels = 2
    o.modifiers.move(len(o.modifiers) - 1, 0)
    for pl in o.data.polygons:
        pl.use_smooth = True
print("BAG", lo, hi)
mouth = Vector((BAG.x - 0.06, lo.y + 0.05, 0.0))          # where the spill leaves the hole


def shred(c, w, h, rz, seed):
    """A torn-off strip of black bag plastic lying on the leaves."""
    r = random.Random(seed)
    bm = bmesh.new(); n = 12; pts = []
    for k in range(n):
        a = 2 * math.pi * k / n
        pts.append((math.cos(a) * w / 2 * r.uniform(0.6, 1.0), math.sin(a) * h / 2 * r.uniform(0.5, 1.0), 0))
    f = bm.faces.new([bm.verts.new(q) for q in pts]); bmesh.ops.triangulate(bm, faces=[f])
    bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=3, use_grid_fill=True)
    for v in bm.verts:
        v.co.z = 0.006 + 0.012 * math.sin(v.co.x * 40 + seed) * math.cos(v.co.y * 30)
    me = bpy.data.meshes.new("shred"); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new("shred", me); sc.collection.objects.link(o)
    o.location = c; o.rotation_euler.z = rz
    so = o.modifiers.new("t", "SOLIDIFY"); so.thickness = 0.0008
    ss = o.modifiers.new("s", "SUBSURF"); ss.levels = ss.render_levels = 2
    for pl in me.polygons:
        pl.use_smooth = True
    me.materials.append(blk)
    return o


shred(mouth + Vector((-0.1, -0.12, 0)), 0.2, 0.1, math.radians(-25), 1)
shred(mouth + Vector((0.18, -0.08, 0)), 0.16, 0.08, math.radians(30), 2)


# ---------------------------------------------------------------- spill: opened diamond papers ("briefkes")
def dpaper(name, w, h, blue, seed):
    """An opened, torn diamond paper: white outer paper, the inside lined in blue with a white margin, the
    fold creases (thirds both ways) still standing. No print."""
    m = bpy.data.materials.new(name); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links
    p = N["Principled BSDF"]; p.inputs['Roughness'].default_value = 0.6
    tc = N.new("ShaderNodeTexCoord"); sep = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs['Object'], sep.inputs[0])
    def inside(sock, half):
        ab = N.new("ShaderNodeMath"); ab.operation = 'ABSOLUTE'; L.new(sock, ab.inputs[0])
        lt = N.new("ShaderNodeMath"); lt.operation = 'LESS_THAN'; lt.inputs[1].default_value = half; L.new(ab.outputs[0], lt.inputs[0])
        return lt.outputs[0]
    mm = N.new("ShaderNodeMath"); mm.operation = 'MULTIPLY'
    L.new(inside(sep.outputs['X'], w / 2 - 0.012), mm.inputs[0]); L.new(inside(sep.outputs['Y'], h / 2 - 0.012), mm.inputs[1])
    geo = N.new("ShaderNodeNewGeometry")
    nb = N.new("ShaderNodeMath"); nb.operation = 'SUBTRACT'; nb.inputs[0].default_value = 1.0; L.new(geo.outputs['Backfacing'], nb.inputs[1])
    m2 = N.new("ShaderNodeMath"); m2.operation = 'MULTIPLY'; L.new(mm.outputs[0], m2.inputs[0]); L.new(nb.outputs[0], m2.inputs[1])
    mx = N.new("ShaderNodeMix"); mx.data_type = 'RGBA'; L.new(m2.outputs[0], mx.inputs['Factor'])
    mx.inputs[6].default_value = (0.92, 0.92, 0.9, 1); mx.inputs[7].default_value = (*blue, 1)
    L.new(mx.outputs[2], p.inputs['Base Color'])
    r = random.Random(seed)
    nx, ny = 12, 9
    bm = bmesh.new()
    vs = [[bm.verts.new((-w / 2 + w * i / nx, -h / 2 + h * j / ny, 0)) for i in range(nx + 1)] for j in range(ny + 1)]
    for j in range(ny):
        for i in range(nx):
            bm.faces.new((vs[j][i], vs[j][i + 1], vs[j + 1][i + 1], vs[j + 1][i]))
    # a torn corner: drop the faces beyond a ragged diagonal
    cut = r.choice((1, -1)); kill = []
    for f in bm.faces:
        c = f.calc_center_median()
        if (cut * c.x / w + c.y / h) > 0.32 + r.uniform(-0.06, 0.06):
            kill.append(f)
    if r.random() < 0.6:
        bmesh.ops.delete(bm, geom=kill, context='FACES')
    for v in bm.verts:
        z = 0.0
        z += 0.006 * max(0, 1 - abs(v.co.x) / (w / 3)) ** 2 + 0.004 * max(0, 1 - abs(v.co.y) / (h / 3)) ** 2
        v.co.z = z + 0.008
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); sc.collection.objects.link(o); me.materials.append(m)
    so = o.modifiers.new("t", "SOLIDIFY"); so.thickness = 0.0005
    for pl in me.polygons:
        pl.use_smooth = True
    return o


BLUES = [(0.12, 0.38, 0.95), (0.2, 0.55, 1.0), (0.08, 0.3, 0.85)]
paper_spots = []
for i in range(int(E("NPAPER", "8"))):
    t = i / 7.0
    p_ = mouth + Vector((rng.uniform(-0.32, 0.12) * (0.5 + t) - 0.05, -0.08 - 0.45 * t, 0))
    o = dpaper(f"dpaper{i}", rng.uniform(0.14, 0.18), rng.uniform(0.1, 0.13), BLUES[i % 3], i)
    o.location = p_; o.rotation_euler = (rng.uniform(-0.1, 0.1), rng.uniform(-0.1, 0.1), rng.uniform(0, 6.28))
    paper_spots.append(p_)

# ---------------------------------------------------------------- loose diamonds (big enough to read: 1-2 cm)
fire = PR.fire_glass("fire")
# brighter, whiter stones: the dispersive glass plus a mirror-like surface reflection (reads as glitter at small size)
_N = fire.node_tree.nodes; _L = fire.node_tree.links; _out = _N["Material Output"]
_src = _out.inputs['Surface'].links[0].from_socket
_gl = _N.new("ShaderNodeBsdfGlossy"); _gl.inputs['Roughness'].default_value = 0.0; _gl.inputs['Color'].default_value = (1, 1, 1, 1)
_fr = _N.new("ShaderNodeFresnel"); _fr.inputs['IOR'].default_value = 2.42
_mx = _N.new("ShaderNodeMixShader"); _L.new(_fr.outputs[0], _mx.inputs[0]); _L.new(_src, _mx.inputs[1]); _L.new(_gl.outputs[0], _mx.inputs[2])
_ad = _N.new("ShaderNodeAddShader"); _L.new(_mx.outputs[0], _ad.inputs[0])
_g2 = _N.new("ShaderNodeBsdfGlossy"); _g2.inputs['Roughness'].default_value = 0.02
_g2.inputs['Color'].default_value = (float(E("GEMSPEC", "0.35")),) * 3 + (1,); _L.new(_g2.outputs[0], _ad.inputs[1])
_L.new(_ad.outputs[0], _out.inputs['Surface'])
gems = bpy.data.collections.new("gems"); sc.collection.children.link(gems)
spots = [(q, 0.009) for q in paper_spots[:6]] + [(mouth + Vector((-0.1, -0.12, 0)), 0.008), (mouth + Vector((0.18, -0.08, 0)), 0.008)]
for i in range(int(E("NGEM", "18"))):
    d = rng.uniform(0.024, 0.038) * float(E("GEMS", "1.0"))
    o = PR.brilliant(f"gem{i}", d, fire)
    for c_ in list(o.users_collection):
        c_.objects.unlink(o)
    gems.objects.link(o)
    if i < 12:
        q, z0 = spots[i % len(spots)]
        base = q + Vector((rng.uniform(-0.04, 0.04), rng.uniform(-0.03, 0.03), z0))
    else:
        base = mouth + Vector((rng.uniform(-0.3, 0.3), rng.uniform(-0.55, -0.05), 0.0))
    o.location = (base.x, base.y, base.z + d * 0.43)
    o.rotation_euler = (rng.uniform(-0.2, 0.2), rng.uniform(-0.2, 0.2), rng.uniform(0, 6.28))

# ---------------------------------------------------------------- the VHS security tape and its loose ribbon
def vhs(loc, rz):
    shell = S.flat("vhs_shell", (0.012, 0.012, 0.014), 0.35)
    win = bpy.data.materials.new("vhs_window"); win.use_nodes = True; pw = win.node_tree.nodes["Principled BSDF"]
    pw.inputs['Base Color'].default_value = (0.03, 0.03, 0.035, 1); pw.inputs['Roughness'].default_value = 0.05
    pw.inputs['Coat Weight'].default_value = 1.0
    label = S.flat("vhs_label", (0.92, 0.9, 0.84), 0.7)                     # blank white spine label
    root = bpy.data.objects.new("vhs", None); sc.collection.objects.link(root)
    parts = [S.box("vhs_body", (0, 0, 0.0125), (0.187, 0.103, 0.025), shell, bevel=0.002),
             S.box("vhs_win", (0, 0.005, 0.0252), (0.09, 0.045, 0.001), win),
             S.box("vhs_label", (0, -0.0517, 0.0125), (0.15, 0.001, 0.016), label),
             S.box("vhs_toplabel", (0, -0.035, 0.0252), (0.12, 0.022, 0.0008), label)]
    for o in parts:
        o.parent = root
    root.location = loc; root.rotation_euler = (math.radians(4), 0, rz)
    return root


TAPE = mouth + Vector((float(E("TX", "-0.38")), float(E("TY", "-0.2")), 0.012))
vhs(TAPE, math.radians(float(E("TRZ", "35"))))
tape_m = bpy.data.materials.new("tape_ribbon"); tape_m.use_nodes = True; pt = tape_m.node_tree.nodes["Principled BSDF"]
pt.inputs['Base Color'].default_value = (0.05, 0.03, 0.02, 1); pt.inputs['Roughness'].default_value = 0.12
pt.inputs['Metallic'].default_value = 0.6
cu = bpy.data.curves.new("ribbon", 'CURVE'); cu.dimensions = '3D'; cu.extrude = float(E("RIBW", "0.011")); cu.twist_mode = 'Z_UP'
sp = cu.splines.new('BEZIER')
# loops of ribbon: from the cassette mouth toward the camera and back, lifting off the leaves in places
pts = []
r2 = random.Random(7)
start = TAPE + Vector((0.05, -0.04, 0.02))
cur = start.copy(); ang = math.radians(-70)
for k in range(int(E("NLOOP", "22"))):
    ang += r2.uniform(-1.1, 1.3)
    step = r2.uniform(0.06, 0.11)
    cur = cur + Vector((math.cos(ang) * step, math.sin(ang) * step, 0))
    cur.x = max(TAPE.x - 0.45, min(TAPE.x + 0.55, cur.x)); cur.y = max(TAPE.y - 0.55, min(TAPE.y + 0.05, cur.y))
    pts.append(Vector((cur.x, cur.y, 0.012 + (0.05 if k % 5 == 2 else 0.0) + r2.uniform(0, 0.012))))
sp.bezier_points.add(len(pts))
for bp, q in zip(sp.bezier_points, [start] + pts):
    bp.co = q; bp.handle_left_type = bp.handle_right_type = 'AUTO'
for bp in sp.bezier_points:
    bp.tilt = math.pi / 2 + r2.uniform(-0.5, 0.5)
ro = bpy.data.objects.new("ribbon", cu); sc.collection.objects.link(ro); cu.materials.append(tape_m)
cu.resolution_u = 16
ro.rotation_euler.x = 0

# ---------------------------------------------------------------- the half-eaten salami sandwich
SW = mouth + Vector((float(E("SWX", "-0.05")), float(E("SWY", "-0.42")), 0.0))
S3.sandwich(loc=(SW.x, SW.y, 0.008), rz=math.radians(float(E("SWR", "-30"))), length=float(E("SWL", "0.2")))

# ---------------------------------------------------------------- light: low autumn sun through the trees
HDRI = E("HDRI", "autumn_forest_04")
SUN_AZ = float(E("SUN_AZ", "60"))
ph.world_hdri(HDRI, strength=float(E("SKY_K", "1.0")), rot_z=T.hdri_sun_rot(HDRI, SUN_AZ), res="4k")
T.sun(SUN_AZ, float(E("SUN_EL", "22")), energy=float(E("SUN_E", "4.0")), color=(1.0, 0.85, 0.62), angle=1.0)
T.area("fill", (-0.6, -1.6, 0.9), (BAG.x, 0.0, 0.05), 2.0, float(E("FILL", "120")), color=(0.85, 0.92, 1.0))

for i, (gx, gz) in enumerate(((-0.6, 0.9), (0.2, 1.1), (0.9, 0.7))):
    gl = bpy.data.lights.new(f"glint{i}", 'POINT'); gl.energy = float(E("GLINT_E", "600")); gl.shadow_soft_size = 0.01
    go = bpy.data.objects.new(f"glint{i}", gl); sc.collection.objects.link(go); go.location = (gx, -1.4, gz)
    go.visible_diffuse = False; go.visible_volume_scatter = False
    go.light_linking.receiver_collection = gems
for i in range(int(E("NPLANT", "14"))):
    aid = ("shrub_02", "fern_02", "dry_branches_medium_01", "nettle_plant")[i % 4]
    x = -4.5 + 9.0 * i / 13 + rng.uniform(-0.4, 0.4); y = rng.uniform(3.5, 6.0)
    try:
        ph.model(aid, loc=(x, y, 0), rot_z=rng.uniform(0, 6.28), scale=rng.uniform(0.9, 1.4))
    except Exception as e:
        print("plant", aid, e)
for (x, y, rz) in ((-1.8, 4.2, 0.3), (2.6, 5.0, 2.0)):
    try:
        ph.model("dead_tree_trunk", loc=(x, y, 0), rot_z=rz)
    except Exception as e:
        print("trunk", e)

# ---------------------------------------------------------------- camera: low, looking up the spill to the bag
cam = Vector((float(E("CAMX", "-0.15")), float(E("CAMY", "-0.95")), float(E("CAMZ", "0.32"))))
tgt = Vector((float(E("AX", "0.02")), float(E("AY", "0.25")), float(E("AZ", "0.16"))))
C.camera(cam, tgt, lens=float(E("LENS", "28")), fstop=float(E("FSTOP", "2.8")),
         focus=(mouth + Vector((-0.05, float(E("FOCY", "-0.25")), 0.02)) - cam).length)

if E("CLIP"):
    import clipcheck
    clipcheck.check("antwerp_bag", limit=40); sys.exit(0)
T.grade(sc, sat=float(E("SAT", "1.3")), con=float(E("CON", "1.1")), expo=float(E("EXPO", "0.0")), vig=float(E("VIG", "0.2")))
T.glints(sc, thr=float(E("GLT", "0.8")), strength=float(E("GLS", "0.6")))
T.render(sc, "antwerp_a1")
