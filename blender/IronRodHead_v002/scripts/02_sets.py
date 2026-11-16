"""Sets for B12 IronRodHead: an 1848 railroad cutting (track along Y, rock walls both sides) and the skull / brain
diagram floating above the track (the cutting is its real background).
blender -b chars.blend --python 02_sets.py -- <out.blend>"""
import sys, os, math, random
import bpy, bmesh
from mathutils import Vector, Matrix
HERE = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(HERE, "00_lib.py")).read())
exec(open(os.path.join(HERE, "_b04_sets_helpers.txt")).read().split('OUT = sys.argv')[0].split('exec(open')[0])
OUT = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene
BRAND = os.path.join(HERE, "..", "..", "assets", "brand")
exec("\n".join(l for l in open(os.path.join(HERE, "_b04_sets_helpers.txt")).read().split("\n")
               if not l.startswith(("import", "from", "HERE", "exec", "OUT", "sc =", "BRAND", '"""', "blender -b"))).split("Sets for B04")[-1])
CS = coll("Set"); CD = coll("Diagram")
rnd = random.Random(12)

# ------------------------------------------------------------------ ground, ballast, track
bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=60, y_segments=60, size=80)
for v in bm.verts:     # gentle undulation away from the track bed, rising toward the rock walls
    x, y = v.co.x, v.co.y; ax = abs(x)
    v.co.z = (0.0 if ax < 6 else min(2.5, (ax - 6) * 0.35)) + 0.06 * math.sin(x * 0.7) * math.cos(y * 0.5) * (ax > 6.5)
ground = mesh_obj("Ground", bm, [pbr("Dirt", "rocky_trail", scale=0.45, tint=(1.05, 0.95, 0.82), bump=0.3, coord="Object")], CS)
shade_smooth(ground)
bm = bmesh.new()
prof = [(-2.1, 0.0), (-1.55, 0.16), (1.55, 0.16), (2.1, 0.0)]
for k, y in enumerate((-45, 45)):
    pass
vs = [[bm.verts.new((x, y, z)) for x, z in prof] for y in (-45, 45)]
for i in range(3): bm.faces.new((vs[0][i], vs[0][i + 1], vs[1][i + 1], vs[1][i]))
ballast = mesh_obj("Ballast", bm, [pbr("BallastMat", "coast_sand_rocks_02", scale=0.9, tint=(0.95, 0.9, 0.85), bump=0.35)], CS)
track = glb_asset("track", CS)
track.data.transform(Matrix.Rotation(R_(90), 4, 'Z'))
seg = max(v.co.y for v in track.data.vertices) - min(v.co.y for v in track.data.vertices)
n = int(88 / seg)
track.location = (0, -44 + seg / 2, 0.16)
arr = track.modifiers.new("Array", 'ARRAY'); arr.count = n; arr.relative_offset_displace = (0, 1, 0)
for m in track.data.materials:
    bs = next((x for x in m.node_tree.nodes if x.type == 'BSDF_PRINCIPLED'), None)
    if bs: bs.inputs['Roughness'].default_value = max(0.4, bs.inputs['Roughness'].default_value)

# ------------------------------------------------------------------ rock walls of the cutting (scanned cliff, softened)
cliff = glb_asset("cliff", CS)
for m in cliff.data.materials:
    nt = m.node_tree; bs = next((x for x in nt.nodes if x.type == 'BSDF_PRINCIPLED'), None)
    if bs:
        bs.inputs['Roughness'].default_value = 0.6
        if bs.inputs['Base Color'].links:
            src = bs.inputs['Base Color'].links[0].from_socket
            mxn = nt.nodes.new('ShaderNodeMix'); mxn.data_type = 'RGBA'; mxn.blend_type = 'MULTIPLY'; mxn.inputs['Factor'].default_value = 1
            mxn.inputs['B'].default_value = (0.62, 0.52, 0.42, 1); nt.links.new(src, mxn.inputs['A']); nt.links.new(mxn.outputs['Result'], bs.inputs['Base Color'])
        for l in list(bs.inputs['Roughness'].links): nt.links.remove(l)
        if bs.inputs['Normal'].links:
            nm = bs.inputs['Normal'].links[0].from_node
            if nm.type == 'NORMAL_MAP': nm.inputs['Strength'].default_value = 0.35
cliff.hide_render = True; cliff.hide_viewport = True
walls = []
for side in (1, -1):
    for k in range(9):
        o = cliff.copy(); CS.objects.link(o); o.hide_render = False; o.hide_viewport = False
        s = 1.25 + 0.25 * rnd.random()
        o.scale = (s, s, s * (1.5 + 0.3 * rnd.random()))
        o.rotation_euler = (0, 0, R_(180 * (side < 0)) + R_(rnd.uniform(-5, 5)))
        o.location = (side * (8.6 + rnd.uniform(0, 0.6)), -40 + k * 10 + rnd.uniform(-1.5, 1.5), -0.2)
        o.name = "Wall%s%d" % ("R" if side > 0 else "L", k); walls.append(o)

# ------------------------------------------------------------------ crates (plank boxes with corner battens), logo decal
def crate(name, w, d, h, c=CS):
    bm = bmesh.new(); add_box(bm, Vector((-w / 2, -d / 2, 0)), Vector((w / 2, d / 2, h)))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = mesh_obj(name, bm, [pbr("CratePlanks", "brown_planks_05", scale=1.6, tint=(1.25, 1.1, 0.9), bump=0.0, coord="Generated")], c)
    m = o.modifiers.new("Bevel", 'BEVEL'); m.width = 0.012; m.segments = 2
    bt = 0.045
    for sx in (-1, 1):
        for sy in (-1, 1):
            bm = bmesh.new(); add_box(bm, Vector((sx * w / 2 - bt / 2 - 0.004, sy * d / 2 - bt / 2 - 0.004, 0)),
                                     Vector((sx * w / 2 + bt / 2 + 0.004, sy * d / 2 + bt / 2 + 0.004, h)))
            bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
            b = mesh_obj(name + "_Batten", bm, [pbr("CrateBatten", "brown_planks_05", scale=2.0, tint=(0.8, 0.62, 0.45), bump=0.0, coord="Generated")], c)
            b.parent = o
    for z in (-0.002, h - bt + 0.004):
        bm = bmesh.new(); add_box(bm, Vector((-w / 2 - 0.006, -d / 2 - 0.006, z)), Vector((w / 2 + 0.006, d / 2 + 0.006, z + bt)))
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        b = mesh_obj(name + "_Band", bm, [bpy.data.materials["CrateBatten"]], c); b.parent = o
    return o
LOGO_DARK = logo_mat("LogoDark", "dark")
def logo_on(o, w, d, h, face=-1, width=None):
    lw = width or (w * 0.86); lh = lw * 414 / 967
    p = decal(o.name + "_Logo", lw, lh, LOGO_DARK, CS); p.parent = o
    p.location = (0, face * (d / 2 + 0.0105), h * 0.5); p.rotation_euler = (0, 0, 0 if face < 0 else math.pi)
    return p
STACK = []
def stack(prefix, base, yaw, sizes, logo_idx=None):
    out = []
    z = 0.0
    for i, (w, d, h, dx) in enumerate(sizes):
        o = crate("%s%d" % (prefix, i), w, d, h)
        R = Matrix.Rotation(R_(yaw), 3, 'Z')
        o.location = Vector(base) + R @ Vector((dx, 0, 0)) + Vector((0, 0, z if dx == 0 or i >= 2 else 0))
        o.rotation_euler = (0, 0, R_(yaw + rnd.uniform(-3, 3)))
        if i == logo_idx: logo_on(o, w, d, h)
        out.append(o)
        if i == 1: z = h
    return out
# supply stack by the track (logo): two side by side + one on top
# beside Gage's work spot, logo face toward the track (-x): two side by side + one on top
SUP = stack("CrateSup", (3.75, 2.6, 0), -90, [(1.2, 0.8, 0.75, -0.65), (1.0, 0.8, 0.75, 0.62), (1.1, 0.8, 0.7, 0.0)], logo_idx=0)
SUP[2].location = (3.8, 2.6, 0.75)
sc["SUP"] = [o.name for o in SUP]
# stack that Gage kicks over at the end (no logo: it's the action prop)
KICK = []
for i, (w, h, p) in enumerate(((0.75, 0.6, (-3.0, -8.0, 0.0)), (0.7, 0.55, (-3.02, -8.02, 0.6)), (0.62, 0.5, (-2.98, -7.98, 1.15)))):
    o = crate("CrateKick%d" % i, w, 0.6, h); o.location = p; o.rotation_euler = (0, 0, R_(rnd.uniform(-4, 4))); KICK.append(o)
sc["KICK"] = [o.name for o in KICK]

wb = glb_asset("wheelbarrow", CS, target_size=1.45, axis=1); wb.location = (-3.8, 3.5, 0); wb.rotation_euler = (0, 0, R_(70))
pk = glb_asset("pickaxe", CS, target_size=0.9, axis=2); pk.rotation_euler = (R_(90), 0, R_(25)); pk.location = (4.4, -1.6, 0.05)
# loose rocks along the cutting floor (small copies of the cliff scan)
for k in range(14):
    o = cliff.copy(); CS.objects.link(o); o.hide_render = False; o.hide_viewport = False; s = rnd.uniform(0.06, 0.14)
    o.scale = (s, s, s * 1.4); o.rotation_euler = (0, 0, rnd.uniform(0, 6.28))
    x = rnd.choice((-1, 1)) * rnd.uniform(4.2, 6.2); o.location = (x, rnd.uniform(-30, 30), -0.05); o.name = "Rock%d" % k

# the drill hole in the rock floor where Gage tamps (dark hole with a ring of grey rock dust)
HOLE = Vector((2.9, 0.2, 0.0))
bm = bmesh.new(); bmesh.ops.create_circle(bm, cap_ends=True, segments=24, radius=0.03)
hole = mesh_obj("DrillHole", bm, [flat("HoleMat", (0.03, 0.025, 0.02), rough=0.9)], CS); hole.location = HOLE + Vector((0, 0, 0.012))
bm = bmesh.new(); bmesh.ops.create_circle(bm, cap_ends=True, segments=32, radius=0.10)
for v in bm.verts:
    r = v.co.length; v.co.z = 0.01
bm.free()
sc["HOLE"] = tuple(HOLE)

# ------------------------------------------------------------------ diagram: skull + brain, 4x life size, above the track
DG = Vector((0.0, 14.0, 2.3)); SCALE = 4.0
sk = glb_asset("skull", CD)
def vbox(o):
    vs = [v.co for v in o.data.vertices]
    return Vector([min(v[i] for v in vs) for i in range(3)]), Vector([max(v[i] for v in vs) for i in range(3)])
mn, mx = vbox(sk); hgt = mx.z - mn.z
sk.data.transform(Matrix.Scale(0.215 * SCALE / hgt, 4))
mn, mx = vbox(sk); ctr = (mn + mx) / 2
sk.data.transform(Matrix.Translation(-ctr)); sk.location = DG
skm = flat("BoneCream", (0.93, 0.87, 0.74), rough=0.45)
sk.data.materials.clear(); sk.data.materials.append(skm)
sk.name = "Skull"
br = glb_asset("brain", CD)
mn, mx = vbox(br); ctr = (mn + mx) / 2
br.data.transform(Matrix.Translation(-ctr)); br.data.transform(Matrix.Rotation(R_(-90), 4, 'Z'))
ys = [v.co.y for v in br.data.vertices]; L = max(ys) - min(ys)
br.data.transform(Matrix.Scale(0.15 * SCALE / L, 4)); br.location = DG + Vector((0, 0.018 * SCALE, 0.03 * SCALE))
br.name = "Brain"
# cutaway window in the skull's left side (person's left = +x; the skull faces -y): delete the faces in a box
bm = bmesh.new(); bm.from_mesh(sk.data)
cut = [f for f in bm.faces if all(v.co.x > 0.10 and -0.30 < v.co.y < 0.10 and -0.02 < v.co.z < 0.30 for v in f.verts)]
bmesh.ops.delete(bm, geom=cut, context='FACES'); bm.to_mesh(sk.data); bm.free()
print("WINDOW faces cut", len(cut))
sc["DIAG"] = tuple(DG); sc["DSCALE"] = SCALE
print("SKULL dims", tuple(round(x, 3) for x in sk.dimensions), "BRAIN dims", tuple(round(x, 3) for x in br.dimensions))

# ------------------------------------------------------------------ sky + sun
w = bpy.data.worlds.new("B12Sky"); sc.world = w; w.use_nodes = True
nt = w.node_tree; bg = nt.nodes['Background']
sky = nt.nodes.new('ShaderNodeTexSky')
try: sky.sky_type = 'NISHITA'
except Exception: pass
try:
    sky.sun_elevation = R_(45); sky.sun_rotation = R_(200); sky.altitude = 300
except Exception: pass
nt.links.new(sky.outputs[0], bg.inputs[0]); bg.inputs[1].default_value = 0.35
sun = bpy.data.lights.new("Sun", 'SUN'); sun.energy = 3.2; sun.angle = R_(4); sun.color = (1.0, 0.96, 0.9)
so = bpy.data.objects.new("Sun", sun); CS.objects.link(so); so.rotation_euler = (R_(42), R_(10), R_(200))
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("SETS_DONE")
