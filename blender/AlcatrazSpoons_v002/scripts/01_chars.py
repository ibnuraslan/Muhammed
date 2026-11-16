"""AlcatrazSpoons characters: re-use MPFB2 rigs from our own packages (the MakeHuman asset server is down), re-dress them.
blender -b --factory-startup --python 01_chars.py -- <repo_blender_dir> <out.blend>
P1/P2/P3 = prisoners (white uniform with black stripes, white knit cap, hair hidden), Guard = 1960s grey-blue uniform."""
import sys, os, math
import bpy, bmesh
from mathutils import Vector, Matrix
a = sys.argv[sys.argv.index("--") + 1:]; ROOT, OUT = a[0], a[1]
for ob in list(bpy.data.objects): bpy.data.objects.remove(ob, do_unlink=True)
sc = bpy.context.scene

SRC = [(os.path.join(ROOT, "PrisonKeyCake_v010/PrisonKeyCake_v010_60fps.blend"), "Prisoner", "P1"),
       (os.path.join(ROOT, "PrisonKeyCake_v010/PrisonKeyCake_v010_60fps.blend"), "YardP1", "P2"),
       (os.path.join(ROOT, "PrisonKeyCake_v010/PrisonKeyCake_v010_60fps.blend"), "YardP2", "P3"),
       (os.path.join(ROOT, "EscapeArtist_v010/EscapeArtist_v010_60fps.blend"), "Guard", "Guard")]
RIGS = {}
for path, src, new in SRC:
    with bpy.data.libraries.load(path, link=False) as (df, dt):
        names = [n for n in df.objects if n == src or n.startswith(src + ".")]
        dt.objects = names
    objs = [o for o in dt.objects if o is not None]
    rig = next(o for o in objs if o.type == 'ARMATURE')
    kids = [o for o in objs if o.parent == rig]
    for o in [rig] + kids:
        sc.collection.objects.link(o)
        o.animation_data_clear()
        if o.type == 'MESH' and o.data.shape_keys: o.data.shape_keys.animation_data_clear()
        o.hide_render = o.hide_viewport = False; o.hide_set(False)
    for o in [o for o in objs if o not in kids and o is not rig]:
        bpy.data.objects.remove(o, do_unlink=True)
    rig.name = new; rig.data.name = new
    for k in kids:
        k.name = new + "." + k.name.split(".", 1)[1]
        k.data.name = k.name
    rig.location = (0, 0, 0); rig.rotation_euler = (0, 0, 0); rig.scale = (1, 1, 1)
    for pb in rig.pose.bones:
        pb.location = (0, 0, 0); pb.rotation_mode = 'QUATERNION'; pb.rotation_quaternion = (1, 0, 0, 0); pb.scale = (1, 1, 1)
    RIGS[new] = rig
    print("CHAR", new, "from", src, [k.name for k in kids])
bpy.ops.outliner.orphans_purge(do_recursive=True)

# ---- make every material single-user per character (the donors share some) and drop old tints
def own_mats(rig):
    for k in rig.children:
        if k.type != 'MESH': continue
        for i, m in enumerate(k.data.materials):
            if m and m.users > 1:
                k.data.materials[i] = m.copy()
for r in RIGS.values(): own_mats(r)

def base_link(m):
    nt = m.node_tree; P = next((n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'), None)
    return nt, P

def stripe_suit(m, n_stripes=16.0, duty=0.30, white=(0.93, 0.93, 0.9), black=(0.035, 0.035, 0.04)):
    """horizontal black bands on a white uniform, in the mesh's own (rest) Generated coordinates so they follow the body"""
    nt, P = base_link(m)
    for l in list(P.inputs['Base Color'].links): nt.links.remove(l)
    tc = nt.nodes.new('ShaderNodeTexCoord'); sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    mul = nt.nodes.new('ShaderNodeMath'); mul.operation = 'MULTIPLY'; mul.inputs[1].default_value = n_stripes
    fr = nt.nodes.new('ShaderNodeMath'); fr.operation = 'FRACT'
    lt = nt.nodes.new('ShaderNodeMath'); lt.operation = 'LESS_THAN'; lt.inputs[1].default_value = duty
    mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'
    mx.inputs['A'].default_value = (*white, 1); mx.inputs['B'].default_value = (*black, 1)
    nt.links.new(tc.outputs['Generated'], sep.inputs[0]); nt.links.new(sep.outputs['Z'], mul.inputs[0])
    nt.links.new(mul.outputs[0], fr.inputs[0]); nt.links.new(fr.outputs[0], lt.inputs[0]); nt.links.new(lt.outputs[0], mx.inputs['Factor'])
    nt.links.new(mx.outputs['Result'], P.inputs['Base Color'])
    P.inputs['Roughness'].default_value = 0.7
    for l in list(P.inputs['Roughness'].links): nt.links.remove(l)
    m["stripes"] = 1

def flat_colour(m, rgb, rough=0.6):
    nt, P = base_link(m)
    for l in list(P.inputs['Base Color'].links): nt.links.remove(l)
    P.inputs['Base Color'].default_value = (*rgb, 1); P.inputs['Roughness'].default_value = rough

SUITS = {"P1": "male_casualsuit01", "P2": "male_casualsuit01", "P3": "male_casualsuit03", "Guard": "male_casualsuit01"}
for n, r in RIGS.items():
    for k in r.children:
        if k.type != 'MESH': continue
        if SUITS[n] in k.name:
            for m in k.data.materials:
                if n == "Guard": flat_colour(m, (0.07, 0.10, 0.17), 0.55)          # dark grey-blue uniform
                else: stripe_suit(m, n_stripes=15.0 if n != "P3" else 17.0)
        if "shoes" in k.name:
            for m in k.data.materials: flat_colour(m, (0.05, 0.045, 0.04), 0.45)

# ---- eye fix (EnhancedEye cornea -> transparent mix), if the procedural eye group is present and not fixed yet
g = bpy.data.node_groups.get("EnhancedEye")
if g and not any(nd.name.startswith("CorneaTransparentMix") for nd in g.nodes):
    _NO_SAVE = True
    exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "eye_fix.py")).read())
for n, r in RIGS.items():
    eye = next(k for k in r.children if k.name.endswith("high-poly"))
    print("EYEMAT", n, [m.name for m in eye.data.materials], [nd.type for m in eye.data.materials for nd in m.node_tree.nodes][:12])

# ---- brows and lashes: the PrisonKeyCake donors lost their card alpha (black bands, LESSONS s3). EscapeArtist's prisoner
# uses the same eyebrow001 / eyelashes01 assets with intact alpha: take those materials.
EA = os.path.join(ROOT, "EscapeArtist_v010/EscapeArtist_v010_60fps.blend")
with bpy.data.libraries.load(EA, link=False) as (df, dt):
    dt.materials = ["Prisoner.eyebrow001", "Prisoner.eyelashes01"]
MB, ML = dt.materials
for mm in (MB, ML):
    im = next(nd.image for nd in mm.node_tree.nodes if nd.type == 'TEX_IMAGE')
    al = im.pixels[3::4]; print("CARD", mm.name, im.name, "alpha min", min(al))
    assert min(al) < 0.5, "donor card has no alpha"
for n in ("P1", "P2", "P3"):
    for k in RIGS[n].children:
        if k.name.endswith("eyebrow001"): k.data.materials[0] = MB
        if k.name.endswith("eyelashes01"): k.data.materials[0] = ML

# ---- open the elbow IK limit (MPFB rest elbow is ~46 deg bent: min 0 kept arms in an A-pose)
for r in RIGS.values():
    for s in "LR":
        lo = r.pose.bones["lowerarm01." + s]
        lo.use_ik_limit_x = True; lo.ik_min_x = math.radians(-40); lo.ik_max_x = math.radians(100)

# ---- knit caps for the prisoners (hair hidden under them), a peaked cap for the guard
def head_metrics(r):
    body = next(k for k in r.children if k.name.endswith(".body"))
    gi = body.vertex_groups["head"].index
    pts = [v.co.copy() for v in body.data.vertices if any(gg.group == gi and gg.weight > 0.5 for gg in v.groups)]
    xs = [p.x for p in pts]; ys = [p.y for p in pts]; zs = [p.z for p in pts]
    eye_z = (r.data.bones["eye.L"].head_local.z + r.data.bones["eye.R"].head_local.z) / 2
    return Vector(((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, 0)), max(xs) - min(xs), max(ys) - min(ys), max(zs), eye_z

def knit_mat(name, rgb):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; P = nt.nodes["Principled BSDF"]
    P.inputs['Base Color'].default_value = (*rgb, 1); P.inputs['Roughness'].default_value = 0.85
    tc = nt.nodes.new('ShaderNodeTexCoord'); w = nt.nodes.new('ShaderNodeTexWave'); w.wave_type = 'BANDS'; w.bands_direction = 'X'
    w.inputs['Scale'].default_value = 40.0; bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = 0.3
    nt.links.new(tc.outputs['Object'], w.inputs['Vector']); nt.links.new(w.outputs['Fac'], bp.inputs['Height']); nt.links.new(bp.outputs['Normal'], P.inputs['Normal'])
    return m

def parent_to_bone(o, r, bone):
    Mw = o.matrix_world.copy(); o.parent = r; o.parent_type = 'BONE'; o.parent_bone = bone
    bpy.context.view_layer.update(); o.matrix_world = Mw

def make_cap(n, mat, rim_off, hide_hair=True, brim=True):
    r = RIGS[n]
    if hide_hair:
        for k in r.children:
            if k.type == 'MESH' and any(h in k.name for h in ("short0", "bob", "ponytail", "afro")):
                k.hide_render = True; k.hide_viewport = True
    body = next(k for k in r.children if k.name.endswith(".body"))
    c, wx, wy, top, eye_z = head_metrics(r)
    rim = eye_z + rim_off
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=48, v_segments=32, radius=1.0)
    rx, ry, rz = wx / 2 * 1.15, wy / 2 * 1.15, (top - rim) * 1.3
    for v in bm.verts: v.co = Vector((v.co.x * rx, v.co.y * ry, v.co.z * rz))
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z < -0.002], context='VERTS')
    me = bpy.data.meshes.new(n + ".cap"); bm.to_mesh(me); bm.free()
    cap = bpy.data.objects.new(n + ".cap", me); sc.collection.objects.link(cap)
    cap.location = (c.x, c.y, rim); me.materials.append(mat)
    for p_ in me.polygons: p_.use_smooth = True
    sw = cap.modifiers.new("Fit", 'SHRINKWRAP'); sw.target = body; sw.wrap_method = 'NEAREST_SURFACEPOINT'; sw.offset = 0.007
    if brim:   # the folded brim: lowest 3.5 cm sits a little proud
        vg = cap.vertex_groups.new(name="brim")
        for v in me.vertices:
            if v.co.z < 0.035: vg.add([v.index], 1.0, 'REPLACE')
        dp = cap.modifiers.new("Brim", 'DISPLACE'); dp.vertex_group = "brim"; dp.direction = 'NORMAL'; dp.strength = 0.006; dp.mid_level = 0.0
    sol = cap.modifiers.new("Solid", 'SOLIDIFY'); sol.thickness = 0.006; sol.offset = -1.0
    cap.modifiers.new("Sub", 'SUBSURF').levels = 1
    bpy.context.view_layer.update(); parent_to_bone(cap, r, "head")
    print("CAP", n, "rim z", round(rim, 3), "top", round(top, 3))
    return cap, c, wx, wy, rim

M_CAP = knit_mat("M_KnitCap", (0.9, 0.9, 0.87))
for n in ("P1", "P2", "P3"): make_cap(n, M_CAP, 0.045)

# guard: navy patrol cap (fitted crown + stiff visor), hair hidden so no fringe falls over an eye
mc = bpy.data.materials.new("M_GuardCap"); mc.use_nodes = True; P_ = mc.node_tree.nodes["Principled BSDF"]
P_.inputs['Base Color'].default_value = (0.03, 0.045, 0.09, 1); P_.inputs['Roughness'].default_value = 0.6
cap, c, wx, wy, rim = make_cap("Guard", mc, 0.035, brim=False)
mv = bpy.data.materials.new("M_GuardVisor"); mv.use_nodes = True; Pv = mv.node_tree.nodes["Principled BSDF"]
Pv.inputs['Base Color'].default_value = (0.015, 0.015, 0.02, 1); Pv.inputs['Roughness'].default_value = 0.3
bm = bmesh.new()                                   # half-disc visor in front of the forehead, curved down at the sides
R_front = wy / 2 * 1.02 + 0.007; segs = 24; ring_o, ring_i = [], []
for i in range(segs + 1):
    t = math.pi * (0.12 + 0.76 * i / segs)         # front half only
    ox, oy = math.cos(t) * wx / 2 * 1.08, -math.sin(t) * R_front
    dx, dy = math.cos(t), -math.sin(t)
    depth = 0.055 * math.sin(t) ** 1.5             # deepest at the middle
    zi = -0.004 * (1 - math.sin(t))
    ring_i.append(bm.verts.new((ox, oy, zi))); ring_o.append(bm.verts.new((ox + dx * depth * 0.4, oy + dy * depth, zi - 0.012 * math.sin(t) - 0.006)))
for i in range(segs): bm.faces.new((ring_i[i], ring_i[i + 1], ring_o[i + 1], ring_o[i]))
me = bpy.data.meshes.new("Guard.visor"); bm.to_mesh(me); bm.free()
vi = bpy.data.objects.new("Guard.visor", me); sc.collection.objects.link(vi); me.materials.append(mv)
vi.location = (c.x, c.y, rim + 0.002); vi.modifiers.new("Solid", 'SOLIDIFY').thickness = 0.005
for p_ in me.polygons: p_.use_smooth = True
bpy.context.view_layer.update(); parent_to_bone(vi, RIGS["Guard"], "head")
# a cap badge plate (plain metal, no text) on the crown front
bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=0.014, depth=0.004)
bd = bpy.context.active_object; bd.name = "Guard.badge"; bd.rotation_euler = (math.radians(90), 0, 0)
bd.location = (c.x, c.y - wy / 2 * 1.02 - 0.012, rim + 0.035)
mbd = bpy.data.materials.new("M_Badge"); mbd.use_nodes = True; Pb = mbd.node_tree.nodes["Principled BSDF"]
Pb.inputs['Base Color'].default_value = (0.8, 0.6, 0.25, 1); Pb.inputs['Metallic'].default_value = 1.0; Pb.inputs['Roughness'].default_value = 0.35
bd.data.materials.append(mbd); bpy.context.view_layer.update(); parent_to_bone(bd, RIGS["Guard"], "head")

# ---- eyes: the PrisonKeyCake image eyes read dark at film size; use the guard's procedural (fixed) EnhancedEye material
GE = next(k for k in RIGS["Guard"].children if k.name.endswith("high-poly")).data.materials[0]
for n in ("P1", "P2", "P3"):
    eye = next(k for k in RIGS[n].children if k.name.endswith("high-poly"))
    eye.data.materials[0] = GE

# ---- the prop characters: a hero flashlight for the guard is built in 02_sets; nothing else here
for n, r in RIGS.items():
    print("RIG", n, tuple(round(d, 2) for d in r.dimensions), "head z", round(r.data.bones["head"].head_local.z, 3))
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print("CHARS_OK")
