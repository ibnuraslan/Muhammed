"""Milgram: characters + sets + props in one file.
blender -b --factory-startup --python 01_build.py -- <repo_blender_dir> <assets_dir> <out.blend>
Cast (generic, re-used MPFB2 rigs from our own packages, re-dressed):
  Stranger (bald, salmon-pink tee, khaki trousers)  <- EarInArm_v011 'Patient' (has expression shape keys)
  Subject  (grey hair, light-blue shirt, grey trousers) <- ElectricianPolice_v010 'Man' (vest + gloves removed)
  Doc      (dark hair, white lab coat, shirt + tie, dark trousers) <- TitanicIceberg_v014 'ExpertA'
Sets: LAB A (origin) the subject's room with the shock generator | LAB B (x=20) the stranger's room | HOME (x=40) 1960s living room."""
import sys, os, math, random
import bpy, bmesh
from mathutils import Vector, Matrix, Euler
a = sys.argv[sys.argv.index("--") + 1:]; ROOT, AS, OUT = a[0], a[1], a[2]
HERE = os.path.dirname(os.path.abspath(__file__)); PKG = os.path.dirname(HERE)
V = Vector; R_ = math.radians
for ob in list(bpy.data.objects): bpy.data.objects.remove(ob, do_unlink=True)
sc = bpy.context.scene
random.seed(25)
XB, XH = 20.0, 40.0
sc["XB"] = XB; sc["XH"] = XH

# =============================================================== characters
SRC = [("EarInArm_v011", "Patient", "Stranger"), ("ElectricianPolice_v010", "Man", "Subject"), ("TitanicIceberg_v014", "ExpertA", "Doc")]
RIGS = {}
for f, src, new in SRC:
    path = os.path.join(ROOT, f, f + "_60fps.blend")
    with bpy.data.libraries.load(path, link=False) as (df, dt):
        dt.objects = [n for n in df.objects if n == src or n.startswith(src + ".")]
    objs = [o for o in dt.objects if o is not None]
    rig = next(o for o in objs if o.type == 'ARMATURE')
    kids = [o for o in objs if o.parent == rig and o.type == 'MESH' and not any(k in o.name for k in (".vest", ".gloves"))]
    for o in [rig] + kids:
        sc.collection.objects.link(o)
        o.animation_data_clear()
        if o.type == 'MESH' and o.data.shape_keys: o.data.shape_keys.animation_data_clear()
        o.hide_render = o.hide_viewport = False
    for o in objs:
        if o is not rig and o not in kids: bpy.data.objects.remove(o, do_unlink=True)
    rig.parent = None
    rig.name = new; rig.data.name = new
    for k in kids:
        k.name = new + "." + k.name.split(".", 1)[1]; k.data.name = k.name
        for m in k.modifiers:
            if m.type == 'ARMATURE': m.object = rig
            if m.type == 'MASK': m.show_viewport = m.show_render = True
    rig.location = (0, 0, 0); rig.rotation_euler = (0, 0, 0); rig.scale = (1, 1, 1)
    for pb in rig.pose.bones:
        pb.location = (0, 0, 0); pb.rotation_mode = 'QUATERNION'; pb.rotation_quaternion = (1, 0, 0, 0); pb.scale = (1, 1, 1)
        for c in list(pb.constraints):
            if c.type in ('CHILD_OF',): pb.constraints.remove(c)
    RIGS[new] = rig
    print("CHAR", new, "from", src, [k.name for k in kids], "IK" , "IK_hand.L" in rig.data.bones)
bpy.ops.outliner.orphans_purge(do_recursive=True)
for n, r in RIGS.items():
    for k in r.children:
        if k.type != 'MESH': continue
        for i, m in enumerate(k.data.materials):
            if m and m.users > 1: k.data.materials[i] = m.copy()
# shape keys: the stranger's EarGone off, expressions to 0 (keyed per shot later)
for k in RIGS["Stranger"].children:
    if k.type == 'MESH' and k.data.shape_keys:
        for kb in k.data.shape_keys.key_blocks:
            if kb.name == "EarGone" or kb.name.startswith("X_"): kb.value = 0.0

def P_of(m):
    return m.node_tree, next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')

def split_outfit(k, z_split, top, bottom, rough=(0.65, 0.6), keep_tex=0.0, tie=None):
    """one MPFB outfit mesh = shirt + trousers: colour by rest-pose height (object coords, follow the body)"""
    zs = [v.co.z for v in k.data.vertices]
    xs_ = [v.co.x for v in k.data.vertices]; ys_ = [v.co.y for v in k.data.vertices]
    def gn(val, arr): return (val - min(arr)) / (max(arr) - min(arr))
    z_split = gn(z_split, zs)
    if tie is not None:
        cx, w, ymax, zlo = tie
        tie = (gn(cx, xs_), w / (max(xs_) - min(xs_)), gn(ymax, ys_), gn(zlo, zs))
    for m in k.data.materials:
        nt, P = P_of(m)
        old = P.inputs['Base Color'].links[0].from_socket if P.inputs['Base Color'].links else None
        for l in list(P.inputs['Base Color'].links): nt.links.remove(l)
        tc = nt.nodes.new('ShaderNodeTexCoord'); sep = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(tc.outputs['Generated'], sep.inputs[0])
        gt = nt.nodes.new('ShaderNodeMath'); gt.operation = 'GREATER_THAN'; gt.inputs[1].default_value = z_split
        nt.links.new(sep.outputs['Z'], gt.inputs[0])
        mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'
        mx.inputs['A'].default_value = (*bottom, 1); mx.inputs['B'].default_value = (*top, 1)
        fac = gt.outputs[0]
        if tie is not None and old is not None:    # keep the original texture (shirt + tie) in a narrow front strip
            cx, w, ymax, zlo = tie
            ax = nt.nodes.new('ShaderNodeMath'); ax.operation = 'SUBTRACT'; ax.inputs[1].default_value = cx; nt.links.new(sep.outputs['X'], ax.inputs[0])
            ab = nt.nodes.new('ShaderNodeMath'); ab.operation = 'ABSOLUTE'; nt.links.new(ax.outputs[0], ab.inputs[0])
            lt = nt.nodes.new('ShaderNodeMath'); lt.operation = 'LESS_THAN'; lt.inputs[1].default_value = w; nt.links.new(ab.outputs[0], lt.inputs[0])
            fy = nt.nodes.new('ShaderNodeMath'); fy.operation = 'LESS_THAN'; fy.inputs[1].default_value = ymax; nt.links.new(sep.outputs['Y'], fy.inputs[0])
            fz = nt.nodes.new('ShaderNodeMath'); fz.operation = 'GREATER_THAN'; fz.inputs[1].default_value = zlo; nt.links.new(sep.outputs['Z'], fz.inputs[0])
            m1 = nt.nodes.new('ShaderNodeMath'); m1.operation = 'MULTIPLY'; nt.links.new(lt.outputs[0], m1.inputs[0]); nt.links.new(fy.outputs[0], m1.inputs[1])
            m2 = nt.nodes.new('ShaderNodeMath'); m2.operation = 'MULTIPLY'; nt.links.new(m1.outputs[0], m2.inputs[0]); nt.links.new(fz.outputs[0], m2.inputs[1])
            mx2 = nt.nodes.new('ShaderNodeMix'); mx2.data_type = 'RGBA'
            nt.links.new(mx.outputs['Result'], mx2.inputs['A']); nt.links.new(old, mx2.inputs['B']); nt.links.new(m2.outputs[0], mx2.inputs['Factor'])
            nt.links.new(fac, mx.inputs['Factor']); nt.links.new(mx2.outputs['Result'], P.inputs['Base Color'])
        else:
            nt.links.new(fac, mx.inputs['Factor']); nt.links.new(mx.outputs['Result'], P.inputs['Base Color'])
        for l in list(P.inputs['Roughness'].links): nt.links.remove(l)
        P.inputs['Roughness'].default_value = rough[0]
    print("OUTFIT", k.name, "z range", round(min(zs), 3), round(max(zs), 3), "split", z_split)

def flat_colour(m, rgb, rough=0.6):
    nt, P = P_of(m)
    for l in list(P.inputs['Base Color'].links): nt.links.remove(l)
    P.inputs['Base Color'].default_value = (*rgb, 1); P.inputs['Roughness'].default_value = rough

def tint_hair(m, sat, val):
    nt, P = P_of(m)
    if not P.inputs['Base Color'].links: return
    src = P.inputs['Base Color'].links[0].from_socket
    hs = nt.nodes.new('ShaderNodeHueSaturation'); hs.inputs['Saturation'].default_value = sat; hs.inputs['Value'].default_value = val
    nt.links.new(src, hs.inputs['Color']); nt.links.new(hs.outputs[0], P.inputs['Base Color'])

def kid(n, suffix):
    return next(k for k in RIGS[n].children if k.name.endswith(suffix))

hip = {n: RIGS[n].data.bones["upperleg01.L"].head_local.z for n in RIGS}
# Stranger: salmon-pink tee over khaki trousers
split_outfit(kid("Stranger", "casualsuit06"), hip["Stranger"] + 0.07, (0.80, 0.33, 0.34), (0.42, 0.37, 0.27))
# Subject: light-blue shirt, mid-grey trousers, grey hair
split_outfit(kid("Subject", "casualsuit01"), hip["Subject"] + 0.07, (0.36, 0.55, 0.78), (0.20, 0.21, 0.23))
for m in kid("Subject", "short02").data.materials: tint_hair(m, 0.08, 1.9)
# Doc: white lab coat (jacket) over the shirt + tie strip, dark trousers below the coat hem
dsuit = kid("Doc", "elegantsuit01")
neck = RIGS["Doc"].data.bones["neck01"].head_local
ys = [v.co.y for v in dsuit.data.vertices if abs(v.co.z - (neck.z - 0.15)) < 0.02]
split_outfit(dsuit, hip["Doc"] - 0.02, (0.86, 0.87, 0.88), (0.06, 0.065, 0.08), tie=(neck.x, 0.03, min(ys) + 0.035, hip["Doc"] + 0.05))
hair = kid("Doc", "short03"); rb = RIGS["Doc"].data.bones
ez = (rb["eye.L"].head_local.z + rb["eye.R"].head_local.z) / 2; ey = rb["eye.L"].head_local.y; hy = rb["head"].head_local.y
bm = bmesh.new(); bm.from_mesh(hair.data)
cut = [v for v in bm.verts if v.co.z < ez + 0.045 and v.co.y < hy - 0.02]
bmesh.ops.delete(bm, geom=cut, context='VERTS'); bm.to_mesh(hair.data); bm.free()
print("FRINGE cut", len(cut), "verts below", round(ez + 0.045, 3))
for n in RIGS:
    for k in RIGS[n].children:
        if "shoes" in k.name:
            for m in k.data.materials: flat_colour(m, (0.05, 0.04, 0.035), 0.45)

# eye fix on every EnhancedEye group; every character uses a procedural (fixed) eye
for g in [g for g in bpy.data.node_groups if g.name.startswith("EnhancedEye")]:
    if any(nd.name.startswith("CorneaTransparentMix") for nd in g.nodes): continue
    src = open(os.path.join(HERE, "eye_fix.py")).read().replace('bpy.data.node_groups["EnhancedEye"]', 'bpy.data.node_groups["%s"]' % g.name)
    _NO_SAVE = True; exec(src)
for n in RIGS:
    eye = kid(n, "high-poly")
    print("EYE", n, [m.name for m in eye.data.materials], [nd.node_tree.name for m in eye.data.materials for nd in m.node_tree.nodes if nd.type == 'GROUP'])
# brow / lash cards must keep alpha
for n in RIGS:
    for suf in ("eyebrow001", "eyelashes01"):
        for m in kid(n, suf).data.materials:
            for nd in m.node_tree.nodes:
                if nd.type == 'TEX_IMAGE' and nd.image:
                    al = nd.image.pixels[3::4]; print("CARD", n, suf, nd.image.name, "alpha min", round(min(al), 3))

# every limb IK on (the EarInArm donor had its leg IK at influence 0: the legs stayed straight through the chair)
for r in RIGS.values():
    for pb in r.pose.bones:
        for c in pb.constraints:
            if c.type in ('IK', 'COPY_ROTATION'): c.influence = 1.0; c.mute = False
# elbow IK limit opened (MPFB rest elbow ~46 deg)
for r in RIGS.values():
    for s in "LR":
        lo = r.pose.bones["lowerarm01." + s]; lo.use_ik_limit_x = True; lo.ik_min_x = R_(-40); lo.ik_max_x = R_(100)

# =============================================================== materials
def mat(name, rgb, rough=0.5, metal=0.0, emit=None, estr=0.0, alpha=1.0):
    m = bpy.data.materials.new(name); m.use_nodes = True; P = m.node_tree.nodes["Principled BSDF"]
    P.inputs['Base Color'].default_value = (*rgb, 1); P.inputs['Roughness'].default_value = rough; P.inputs['Metallic'].default_value = metal
    if emit: P.inputs['Emission Color'].default_value = (*emit, 1); P.inputs['Emission Strength'].default_value = estr
    return m

def paint(name, rgb, var=0.05, scale=3.0, bump=0.06, rough=0.65):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; P = nt.nodes["Principled BSDF"]
    nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = scale; nz.inputs['Detail'].default_value = 6.0
    tc = nt.nodes.new('ShaderNodeTexCoord'); nt.links.new(tc.outputs['Object'], nz.inputs['Vector'])
    mr = nt.nodes.new('ShaderNodeMapRange'); mr.inputs['To Min'].default_value = 1 - var; mr.inputs['To Max'].default_value = 1 + var
    nt.links.new(nz.outputs['Fac'], mr.inputs['Value'])
    mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs['Factor'].default_value = 1.0
    mx.inputs['A'].default_value = (*rgb, 1); nt.links.new(mr.outputs[0], mx.inputs['B']); nt.links.new(mx.outputs['Result'], P.inputs['Base Color'])
    bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = bump; nt.links.new(nz.outputs['Fac'], bp.inputs['Height']); nt.links.new(bp.outputs['Normal'], P.inputs['Normal'])
    P.inputs['Roughness'].default_value = rough
    return m

def wallpaper(name, base, motif):
    """1960s damask-like wallpaper: soft yellow with a repeating paler motif (Voronoi + wave), no text"""
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; P = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new('ShaderNodeTexCoord'); mp = nt.nodes.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (4.0, 4.0, 4.0)
    nt.links.new(tc.outputs['Object'], mp.inputs['Vector'])
    vo = nt.nodes.new('ShaderNodeTexVoronoi'); vo.feature = 'DISTANCE_TO_EDGE'; vo.inputs['Scale'].default_value = 2.0; vo.inputs['Randomness'].default_value = 0.0
    nt.links.new(mp.outputs[0], vo.inputs['Vector'])
    cr = nt.nodes.new('ShaderNodeValToRGB'); cr.color_ramp.elements[0].position = 0.06; cr.color_ramp.elements[0].color = (*motif, 1)
    cr.color_ramp.elements[1].position = 0.12; cr.color_ramp.elements[1].color = (*base, 1)
    nt.links.new(vo.outputs['Distance'], cr.inputs['Fac']); nt.links.new(cr.outputs['Color'], P.inputs['Base Color'])
    P.inputs['Roughness'].default_value = 0.7
    return m

def wood(name, rgb, scale=6.0):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; P = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new('ShaderNodeTexCoord'); w = nt.nodes.new('ShaderNodeTexWave'); w.wave_type = 'RINGS'; w.inputs['Scale'].default_value = scale
    w.inputs['Distortion'].default_value = 6.0; w.inputs['Detail'].default_value = 3.0
    nt.links.new(tc.outputs['Object'], w.inputs['Vector'])
    cr = nt.nodes.new('ShaderNodeValToRGB'); cr.color_ramp.elements[0].color = (*[c * 0.8 for c in rgb], 1); cr.color_ramp.elements[1].color = (*rgb, 1)
    nt.links.new(w.outputs['Fac'], cr.inputs['Fac']); nt.links.new(cr.outputs['Color'], P.inputs['Base Color'])
    P.inputs['Roughness'].default_value = 0.45
    return m

M_WALL = paint("M_LabWall", (0.20, 0.27, 0.62), var=0.03)        # the reference's periwinkle-blue painted walls
M_CEIL = paint("M_Ceiling", (0.85, 0.86, 0.88), var=0.02)
M_CARPET = paint("M_Carpet", (0.17, 0.18, 0.20), var=0.18, scale=180.0, bump=0.2, rough=0.95)
M_SKIRT = mat("M_Skirting", (0.85, 0.86, 0.88), 0.4)
M_GEN = mat("M_GenBody", (0.80, 0.81, 0.82), 0.35)
M_GENDARK = mat("M_GenDark", (0.06, 0.065, 0.07), 0.4)
M_PLATE = mat("M_SwitchPlate", (0.55, 0.56, 0.58), 0.3, 0.8)
M_LEVER = mat("M_Lever", (0.08, 0.08, 0.09), 0.3, 0.6)
M_RED = mat("M_DangerBand", (0.55, 0.04, 0.04), 0.4)
BANDS = [(0.75, 0.78, 0.80), (0.82, 0.82, 0.70), (0.86, 0.78, 0.45), (0.86, 0.62, 0.30), (0.80, 0.42, 0.22), (0.70, 0.18, 0.12), (0.55, 0.04, 0.04), (0.20, 0.02, 0.02)]
M_CABLE = mat("M_Cable", (0.03, 0.03, 0.035), 0.45)
M_PLUG = mat("M_Plug", (0.08, 0.08, 0.09), 0.35)
M_PRONG = mat("M_Prong", (0.85, 0.75, 0.45), 0.25, 1.0)
M_SOCKET = mat("M_Socket", (0.90, 0.90, 0.88), 0.35)
M_STRAP = mat("M_Strap", (0.12, 0.10, 0.09), 0.5)
M_ELEC = mat("M_Electrode", (0.75, 0.75, 0.78), 0.25, 1.0)
M_FLOORWOOD = wood("M_FloorWood", (0.42, 0.24, 0.12), 2.0)
M_RUG = paint("M_Rug", (0.38, 0.03, 0.03), var=0.25, scale=40.0, bump=0.1, rough=0.9)
M_PAPER = mat("M_Paper", (0.93, 0.93, 0.90), 0.8)
M_INK = mat("M_InkLine", (0.55, 0.56, 0.6), 0.8)
M_WP = wallpaper("M_Wallpaper", (0.86, 0.74, 0.38), (0.95, 0.90, 0.70))
M_FRAME = mat("M_Frame", (0.12, 0.08, 0.05), 0.5)
M_ARC = mat("M_Arc", (1.0, 0.95, 0.7), 0.5, emit=(1.0, 0.85, 0.45), estr=25.0)

COLS = {}
def col(name):
    if name not in COLS:
        c = bpy.data.collections.new(name); sc.collection.children.link(c); COLS[name] = c
    return COLS[name]
def link(o, cname):
    for c in list(o.users_collection): c.objects.unlink(o)
    col(cname).objects.link(o); return o
def box(name, cname, size, loc, m, rot=(0, 0, 0), bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=loc, rotation=rot)
    o = bpy.context.active_object; o.name = name; o.scale = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel > 0:
        b = o.modifiers.new("Bev", 'BEVEL'); b.width = bevel; b.segments = 3
    o.data.materials.append(m); return link(o, cname)
def plane(name, cname, size, loc, rot, m):
    bpy.ops.mesh.primitive_plane_add(size=1.0, location=loc, rotation=rot)
    o = bpy.context.active_object; o.name = name; o.scale = (size[0], size[1], 1)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    o.data.materials.append(m); return link(o, cname)
def cyl(name, cname, r, depth, loc, rot, m, verts=24):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=depth, location=loc, rotation=rot)
    o = bpy.context.active_object; o.name = name; o.data.materials.append(m)
    for p in o.data.polygons: p.use_smooth = True
    return link(o, cname)
def asset(aid, name, cname, loc, rot_z=0.0, scale=(1, 1, 1)):
    p = os.path.join(AS, aid, aid + "_1k.blend")
    with bpy.data.libraries.load(p, link=False) as (df, dt): dt.objects = list(df.objects)
    obs = [o for o in dt.objects if o and o.type == 'MESH']
    main = obs[0]
    for o in obs:
        col(cname).objects.link(o)
    for o in obs[1:]:
        if o.parent is None: o.parent = main
    main.name = name; main.location = loc; main.rotation_euler = (0, 0, R_(rot_z)); main.scale = scale
    for o in obs:
        for m in o.data.materials:     # STYLE: clean surfaces (bump low, roughness >= 0.35)
            for nd in m.node_tree.nodes:
                if nd.type == 'NORMAL_MAP': nd.inputs['Strength'].default_value = min(nd.inputs['Strength'].default_value, 0.35)
                if nd.type == 'BUMP': nd.inputs['Strength'].default_value = min(nd.inputs['Strength'].default_value, 0.3)
    return main

def room(cname, cx, cy, w, d, h, wall_m, floor_m, open_front=False):
    """four walls + floor + ceiling, the inside visible. cx,cy centre; w along x, d along y"""
    plane(cname + "_Floor", cname, (w, d), (cx, cy, 0), (0, 0, 0), floor_m)
    plane(cname + "_Ceil", cname, (w, d), (cx, cy, h), (math.pi, 0, 0), M_CEIL)
    box(cname + "_WallBack", cname, (w, 0.1, h), (cx, cy + d / 2 + 0.05, h / 2), wall_m)
    box(cname + "_WallFront", cname, (w, 0.1, h), (cx, cy - d / 2 - 0.05, h / 2), wall_m)
    box(cname + "_WallL", cname, (0.1, d, h), (cx - w / 2 - 0.05, cy, h / 2), wall_m)
    box(cname + "_WallR", cname, (0.1, d, h), (cx + w / 2 + 0.05, cy, h / 2), wall_m)
    for nm, sz, lc in (("SkB", (w, 0.02, 0.1), (cx, cy + d / 2 - 0.01, 0.05)), ("SkF", (w, 0.02, 0.1), (cx, cy - d / 2 + 0.01, 0.05)),
                       ("SkL", (0.02, d, 0.1), (cx - w / 2 + 0.01, cy, 0.05)), ("SkR", (0.02, d, 0.1), (cx + w / 2 - 0.01, cy, 0.05))):
        box(cname + "_" + nm, cname, sz, lc, M_SKIRT)

def area_light(name, cname, loc, size, energy, rot=(0, 0, 0), color=(1, 1, 1)):
    L = bpy.data.lights.new(name, 'AREA'); L.size = size; L.energy = energy; L.color = color
    o = bpy.data.objects.new(name, L); o.location = loc; o.rotation_euler = rot; col(cname).objects.link(o); return o

def ray_top(o, x, y):
    """z of the first surface hit straight down at (x, y)"""
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    hit, loc, *_ = sc.ray_cast(dg, V((x, y, 3.0)), V((0, 0, -1)))
    return loc.z if hit else None

# =============================================================== LAB A: the subject's room (origin)
room("LabA", 0.0, -0.6, 5.0, 6.0, 2.8, M_WALL, M_CARPET)
area_light("LabA_Key", "LabA", (0.0, -0.8, 2.7), 3.0, 450)
area_light("LabA_Fill", "LabA", (-1.5, -2.5, 2.2), 2.0, 110, rot=(R_(50), 0, R_(-30)))
TA = asset("WoodenTable_01", "LabA_Table", "LabA", (0, 0.06, 0), 0.0, (0.92, 1.2, 1.37))
TABLE_Z = 0.549 * 1.37
sc["TABLE_Z"] = TABLE_Z
CH_A = asset("SchoolChair_01", "LabA_Chair", "LabA", (0.0, -0.72, 0), 180.0)

# --- the shock generator: a light-grey console with 30 lever switches, a lamp over each, colour bands (no text)
GX0, GX1 = -0.52, 0.52; GY0, GY1 = -0.12, 0.30; GZ0, GZ1 = TABLE_Z, TABLE_Z + 0.30
sc["GEN"] = (GX0, GX1, GY0, GY1, GZ0, GZ1)
box("Gen_Body", "LabA", (GX1 - GX0, GY1 - GY0, GZ1 - GZ0), ((GX0 + GX1) / 2, (GY0 + GY1) / 2, (GZ0 + GZ1) / 2), M_GEN, bevel=0.008)
box("Gen_Top", "LabA", (GX1 - GX0 + 0.01, GY1 - GY0 + 0.01, 0.02), ((GX0 + GX1) / 2, (GY0 + GY1) / 2, GZ1 + 0.005), M_GENDARK, bevel=0.004)
box("Gen_Base", "LabA", (GX1 - GX0 + 0.01, GY1 - GY0 + 0.01, 0.025), ((GX0 + GX1) / 2, (GY0 + GY1) / 2, GZ0 + 0.0125), M_GENDARK, bevel=0.004)
NSW = 30; SWZ = GZ0 + 0.105; LAMPZ = GZ0 + 0.19; BANDZ = GZ0 + 0.145
SWX = [GX0 + 0.06 + i * (GX1 - GX0 - 0.12) / (NSW - 1) for i in range(NSW)]
sc["SWX"] = SWX; sc["SWZ"] = SWZ; sc["LAMPZ"] = LAMPZ
for g in range(8):     # colour bands across groups of 4 switches (the last two are the danger zone)
    i0 = g * 4; i1 = min(NSW - 1, i0 + 3)
    x0 = SWX[i0] - 0.014; x1 = SWX[i1] + 0.014
    box("Gen_Band%d" % g, "LabA", (x1 - x0, 0.004, 0.022), ((x0 + x1) / 2, GY0 - 0.002, BANDZ), mat("M_Band%d" % g, BANDS[g], 0.4))
box("Gen_StripDark", "LabA", (GX1 - GX0 - 0.04, 0.004, 0.03), ((GX0 + GX1) / 2, GY0 - 0.002, GZ0 + 0.255), M_GENDARK)
LEVERS = []
for i, x in enumerate(SWX):
    box("Gen_Plate%02d" % i, "LabA", (0.024, 0.006, 0.034), (x, GY0 - 0.003, SWZ), M_PLATE, bevel=0.002)
    piv = bpy.data.objects.new("Gen_LeverPivot%02d" % i, None); piv.location = (x, GY0 - 0.006, SWZ); col("LabA").objects.link(piv)
    lv = cyl("Gen_Lever%02d" % i, "LabA", 0.0035, 0.028, (x, GY0 - 0.006 - 0.014, SWZ), (R_(90), 0, 0), M_LEVER, 12)
    tipb = cyl("Gen_LeverTip%02d" % i, "LabA", 0.006, 0.008, (x, GY0 - 0.006 - 0.028, SWZ), (R_(90), 0, 0), M_LEVER, 16)
    for o in (lv, tipb):
        o.parent = piv; o.matrix_parent_inverse = piv.matrix_world.inverted()
    piv.rotation_euler = (R_(25), 0, 0)      # lever up (off); keyed down (-25) when pressed
    LEVERS.append(piv)
    lm = mat("M_Lamp%02d" % i, (0.35, 0.05, 0.04), 0.3, emit=(1.0, 0.08, 0.04), estr=0.0)
    lamp = cyl("Gen_Lamp%02d" % i, "LabA", 0.0075, 0.012, (x, GY0 - 0.004, LAMPZ), (R_(90), 0, 0), lm, 16)
    bev = lamp.modifiers.new("Bev", 'BEVEL'); bev.width = 0.004; bev.segments = 3
# a round meter (blank face, a needle) and a pilot lamp on the left of the top strip
cyl("Gen_MeterRim", "LabA", 0.045, 0.012, (GX0 + 0.10, GY0 - 0.004, GZ0 + 0.245), (R_(90), 0, 0), M_GENDARK, 32)
cyl("Gen_MeterFace", "LabA", 0.038, 0.004, (GX0 + 0.10, GY0 - 0.011, GZ0 + 0.245), (R_(90), 0, 0), mat("M_MeterFace", (0.95, 0.94, 0.88), 0.4), 32)
ndl = box("Gen_Needle", "LabA", (0.002, 0.002, 0.032), (GX0 + 0.10, GY0 - 0.015, GZ0 + 0.245 + 0.014), M_RED)
box("Gen_Dial", "LabA", (0.05, 0.02, 0.05), (GX1 - 0.10, GY0 - 0.01, GZ0 + 0.245), M_GENDARK, bevel=0.01)
# red "wrong answer" lamp on the back wall above the generator
M_WRONG = mat("M_WrongLamp", (0.5, 0.03, 0.02), 0.3, emit=(1.0, 0.05, 0.03), estr=0.0)
cyl("LabA_WrongBase", "LabA", 0.09, 0.03, (0.0, 2.38, 1.75), (R_(90), 0, 0), M_GENDARK, 32)
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.075, location=(0.0, 2.36, 1.75), segments=32, ring_count=16)
dome = bpy.context.active_object; dome.name = "LabA_WrongDome"; dome.scale = (1, 0.6, 1); dome.data.materials.append(M_WRONG); link(dome, "LabA")
for p in dome.data.polygons: p.use_smooth = True
L = bpy.data.lights.new("LabA_WrongGlow", 'POINT'); L.color = (1.0, 0.1, 0.05); L.energy = 0.0; L.shadow_soft_size = 0.1
lo = bpy.data.objects.new("LabA_WrongGlow", L); lo.location = (0.0, 2.2, 1.75); col("LabA").objects.link(lo)
# cable from the back of the generator, down the table, along the floor to the wall socket: the plug lies UNPLUGGED
def curve_tube(name, cname, pts, r, m):
    cu = bpy.data.curves.new(name, 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = r; cu.bevel_resolution = 4
    sp = cu.splines.new('BEZIER'); sp.bezier_points.add(len(pts) - 1)
    for bp_, p in zip(sp.bezier_points, pts):
        bp_.co = p; bp_.handle_left_type = bp_.handle_right_type = 'AUTO'
    o = bpy.data.objects.new(name, cu); cu.materials.append(m); col(cname).objects.link(o); return o
PLUG = V((1.55, 2.05, 0.012))
curve_tube("LabA_Cable", "LabA", [V((0.35, 0.28, GZ0 + 0.06)), V((0.55, 0.40, GZ0 + 0.01)), V((0.62, 0.55, GZ0 - 0.15)), V((0.66, 0.62, 0.30)),
                                   V((0.75, 0.80, 0.012)), V((1.1, 1.4, 0.012)), V((1.4, 1.85, 0.012)), PLUG - V((0.03, 0.06, 0))], 0.006, M_CABLE)
pl = box("LabA_Plug", "LabA", (0.035, 0.05, 0.022), PLUG + V((0, 0, 0.011)), M_PLUG, bevel=0.005)
pl.rotation_euler = (0, 0, R_(-30))
for dx in (-0.008, 0.008):
    pr = box("LabA_Prong", "LabA", (0.003, 0.018, 0.008), PLUG + V((dx, 0.032, 0.011)), M_PRONG)
    pr.parent = pl; pr.matrix_parent_inverse = pl.matrix_world.inverted()
sock = box("LabA_Socket", "LabA", (0.08, 0.015, 0.12), (1.85, 2.385, 0.32), M_SOCKET, bevel=0.006)
for dx in (-0.012, 0.012): box("LabA_SocketHole", "LabA", (0.004, 0.004, 0.014), (1.85 + dx, 2.376, 0.33), M_GENDARK)
# the DA KRAS FILMS poster on the back wall (right of the generator), dark logo on white paper in a thin frame
LOGO_D = bpy.data.images.load(os.path.join(ROOT, "assets/brand/DaKrasFilms_logo_dark.png")); LOGO_W = bpy.data.images.load(os.path.join(ROOT, "assets/brand/DaKrasFilms_logo_white.png"))
def logo_mat(name, img, bg=None):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; P = nt.nodes["Principled BSDF"]
    t = nt.nodes.new('ShaderNodeTexImage'); t.image = img; t.extension = 'CLIP'
    if bg is None:
        nt.links.new(t.outputs['Color'], P.inputs['Base Color']); nt.links.new(t.outputs['Alpha'], P.inputs['Alpha'])
    else:
        mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.inputs['A'].default_value = (*bg, 1)
        nt.links.new(t.outputs['Color'], mx.inputs['B']); nt.links.new(t.outputs['Alpha'], mx.inputs['Factor']); nt.links.new(mx.outputs['Result'], P.inputs['Base Color'])
    P.inputs['Roughness'].default_value = 0.6
    return m
PW, PH = 0.95, 0.62
box("LabA_PosterFrame", "LabA", (PW + 0.04, 0.02, PH + 0.04), (1.35, 2.39, 1.55), M_FRAME)
box("LabA_Poster", "LabA", (PW, 0.004, PH), (1.35, 2.378, 1.55), M_PAPER)
lp = plane("LabA_PosterLogo", "LabA", (PW * 0.86, PW * 0.86 * 414 / 967), (1.35, 2.374, 1.55), (R_(90), 0, 0), logo_mat("M_LogoPoster", LOGO_D))
# a coat rack and a filing cabinet so the room is not empty
box("LabA_Cabinet", "LabA", (0.5, 0.6, 1.3), (-1.95, 1.9, 0.65), mat("M_CabinetGrey", (0.45, 0.47, 0.5), 0.35, 0.5), bevel=0.01)
for k in range(3): box("LabA_CabinetDrawer%d" % k, "LabA", (0.44, 0.01, 0.34), (-1.95, 1.595, 0.25 + k * 0.4), mat("M_DrawerFace", (0.52, 0.54, 0.57), 0.35, 0.5), bevel=0.005)
# a clipboard on the table (photo of the subject; the photo image is set in 02 from review/portrait if present)
CB = asset("clipboard", "Clipboard_Table", "LabA", (-0.68, -0.02, TABLE_Z + 0.003), 10.0)
CB2 = asset("clipboard", "Clipboard_Doc", "Props", (30.0, 0, 0), 0.0)

# =============================================================== LAB B: the stranger's room (x = XB)
room("LabB", XB, -0.6, 4.5, 5.0, 2.8, M_WALL, M_CARPET)
area_light("LabB_Key", "LabB", (XB, -0.8, 2.7), 3.0, 450)
area_light("LabB_Fill", "LabB", (XB + 1.0, -2.6, 2.0), 2.0, 110, rot=(R_(55), 0, R_(25)))
TB = asset("WoodenTable_01", "LabB_Table", "LabB", (XB, -0.45, 0), 0.0, (0.72, 1.2, 1.37))
CH_B = asset("SchoolChair_01", "LabB_Chair", "LabB", (XB, 0.44, 0), 0.0)
# a speaker box on the wall (the stranger hears the questions); a small table lamp for depth
box("LabB_Speaker", "LabB", (0.3, 0.12, 0.4), (XB - 1.6, 1.84, 1.9), mat("M_Speaker", (0.35, 0.25, 0.18), 0.5), bevel=0.01)
box("LabB_SpeakerCloth", "LabB", (0.24, 0.005, 0.32), (XB - 1.6, 1.778, 1.9), mat("M_SpeakerCloth", (0.75, 0.68, 0.55), 0.9))
# electrode cuff for the stranger's right wrist (placed and bound in 02) + its cable
bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=0.054, depth=0.05)
cuff = bpy.context.active_object; cuff.name = "Cuff"; cuff.data.materials.append(M_STRAP); link(cuff, "Props")
bm = bmesh.new(); bm.from_mesh(cuff.data)
bmesh.ops.delete(bm, geom=[f for f in bm.faces if abs(f.normal.z) > 0.9], context='FACES_ONLY'); bm.to_mesh(cuff.data); bm.free()
cuff.modifiers.new("Solid", 'SOLIDIFY').thickness = 0.006
for p in cuff.data.polygons: p.use_smooth = True
el = cyl("CuffElectrode", "Props", 0.012, 0.01, (0, 0, 0), (0, 0, 0), M_ELEC, 20)

# arcs: stylised jagged emissive bolts (each its own object, keyed on/off in 02)
def bolt(name, start, end, n=7, jit=0.02, r=0.0025):
    pts = [V(start).lerp(V(end), i / n) + (V((random.uniform(-jit, jit), random.uniform(-jit, jit), random.uniform(-jit, jit))) if 0 < i < n else V()) for i in range(n + 1)]
    cu = bpy.data.curves.new(name, 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = r
    sp = cu.splines.new('POLY'); sp.points.add(len(pts) - 1)
    for p_, q in zip(sp.points, pts): p_.co = (*q, 1)
    o = bpy.data.objects.new(name, cu); cu.materials.append(M_ARC); col("Props").objects.link(o); return o
for i in range(10):
    ang = i * 36
    d = V((math.cos(R_(ang)), math.sin(R_(ang)), random.uniform(-0.4, 0.6))).normalized()
    bolt("ArcW%02d" % i, (0, 0, 0), d * random.uniform(0.07, 0.12), n=6, jit=0.012, r=0.0016)    # wrist sparks (parented in 02)
for i in range(14):
    ang = i * 360 / 14
    d = V((math.cos(R_(ang)), math.sin(R_(ang)) * 0.6, random.uniform(-0.3, 0.9))).normalized()
    bolt("ArcB%02d" % i, d * 0.25, d * random.uniform(0.55, 0.8), n=8, jit=0.05, r=0.003)          # body arcs round the collapse

# =============================================================== HOME: 1960s living room (x = XH)
room("Home", XH, 0.0, 4.5, 4.5, 2.6, M_WP, M_FLOORWOOD)
plane("Home_Rug", "Home", (2.4, 1.7), (XH, 0.2, 0.004), (0, 0, 0), M_RUG)
area_light("Home_Key", "Home", (XH, -0.5, 2.5), 2.5, 350, color=(1.0, 0.93, 0.82))
area_light("Home_Fill", "Home", (XH - 1.2, -1.8, 1.8), 1.5, 150, rot=(R_(60), 0, R_(-30)), color=(1.0, 0.95, 0.88))
TT = asset("WoodenTable_01", "Home_TVTable", "Home", (XH, 1.75, 0), 0.0, (0.55, 0.9, 1.0))
TV = asset("Television_01", "Home_TV", "Home", (XH, 1.75, 0.549), 0.0, (1.25, 1.25, 1.25))
AC = asset("ArmChair_01", "Home_Armchair", "Home", (XH - 1.1, -0.6, 0), 200.0)
# a standard lamp + a framed picture (plain landscape colours) so the room reads as a home
cyl("Home_LampPole", "Home", 0.012, 1.5, (XH + 1.6, 1.6, 0.75), (0, 0, 0), M_FRAME, 12)
cyl("Home_LampBase", "Home", 0.15, 0.03, (XH + 1.6, 1.6, 0.015), (0, 0, 0), M_FRAME, 24)
bpy.ops.mesh.primitive_cone_add(vertices=32, radius1=0.25, radius2=0.15, depth=0.3, location=(XH + 1.6, 1.6, 1.55))
sh = bpy.context.active_object; sh.name = "Home_LampShade"; sh.data.materials.append(mat("M_Shade", (0.95, 0.88, 0.7), 0.7, emit=(1.0, 0.85, 0.6), estr=1.5)); link(sh, "Home")
box("Home_PicFrame", "Home", (0.7, 0.03, 0.5), (XH - 1.2, 2.23, 1.6), M_FRAME)
box("Home_Pic", "Home", (0.62, 0.005, 0.42), (XH - 1.2, 2.21, 1.6), mat("M_Pic", (0.35, 0.55, 0.45), 0.6))
# TV screen: an emissive picture of the subject (portrait image set in 02), placed over the TV's own screen
scr = plane("Home_TVScreen", "Home", (0.40, 0.30), (XH - 0.07, 1.75 - 0.27, 0.549 + 0.31), (R_(90), 0, 0), mat("M_TVScreen", (0.05, 0.05, 0.05), 0.2))

# =============================================================== render settings / look
w = bpy.data.worlds.new("World"); sc.world = w; w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (0.75, 0.82, 0.95, 1); w.node_tree.nodes["Background"].inputs[1].default_value = 0.12
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = 48; sc.cycles.adaptive_threshold = 0.05; sc.cycles.use_denoising = True
sc.render.resolution_x, sc.render.resolution_y = 1080, 1920; sc.render.fps = 60
sc.view_settings.view_transform = 'AgX'
try: sc.view_settings.look = 'AgX - Punchy'
except Exception as e: print("LOOK", e)
sc.render.use_motion_blur = False
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print("BUILD_OK")
