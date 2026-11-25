"""BeethovenDeaf v011 stage A (from scratch): the composer (char.py), the music room, the piano with 88 hinged keys,
the brass rod and its clamp, candles, sheet music, the logo frame, the x-ray anatomy, render settings and look.
blender -b --python 01_build.py -- <src_assets.blend> <logo_dark.png> <logo_white.png> <out.blend>

World: the composer sits on the bench at +Y facing -Y (MPFB rest direction). The keyboard front edge is the line y=0,
the keys run back to y=-0.152 (white key tops z=0.8057), the piano body extends to -Y. Bass keys are at +X
(the composer's left). The CC-BY piano/bench/candelabra/skull/ear meshes come from BeethovenDeaf_v010 (extract.py),
rotated 180 degrees about Z into this layout."""
import bpy, bmesh, sys, os, math, random
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
HERE = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(HERE, "lib.py")).read())
a = sys.argv[sys.argv.index("--") + 1:]
SRC, LOGO_D, LOGO_W, OUT = a[0], a[1], a[2], a[3]
random.seed(8)
exec(open(os.path.join(HERE, "char.py")).read())          # clears the scene, builds COMP/CB
sc.render.fps = 60; sc.render.fps_base = 1.0
sc.frame_start, sc.frame_end = 1, 1435
sc.render.resolution_x, sc.render.resolution_y = 1080, 1920; sc.render.resolution_percentage = 100

def coll(name):
    c = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if c.name not in sc.collection.children: sc.collection.children.link(c)
    return c
C_SET, C_PROPS, C_FX, C_XR = coll("Set"), coll("Props"), coll("FX"), coll("XRay")
def to(o, c):
    for u in list(o.users_collection): u.objects.unlink(o)
    c.objects.link(o); return o

ROT = Matrix.Rotation(math.pi, 4, 'Z')
with bpy.data.libraries.load(SRC) as (src, dst):
    dst.objects = [n for n in src.objects if n.startswith("SRC_")]
SRCO = {o.name[4:]: o for o in dst.objects}

# ================================================================== PIANO: drop the model's fused keys + the maker's lettering
pi = SRCO["Piano"]; pi.name = "Piano"; to(pi, C_SET)
bm = bmesh.new(); bm.from_mesh(pi.data); bm.verts.ensure_lookup_table()
seen = set(); kill = []
for v in bm.verts:
    if v.index in seen: continue
    st = [v]; comp = []; seen.add(v.index)
    while st:
        x = st.pop(); comp.append(x)
        for e in x.link_edges:
            y = e.other_vert(x)
            if y.index not in seen: seen.add(y.index); st.append(y)
    cs = [q.co for q in comp]; mn = [min(q[i] for q in cs) for i in range(3)]; mx = [max(q[i] for q in cs) for i in range(3)]
    keys = (mn[0] > -0.668 and mx[0] < 0.668 and mn[1] > -0.012 and mx[1] < 0.178 and mn[2] > 0.70 and mx[2] < 0.84)
    letters = (mn[1] > 0.17 and mx[1] < 0.195 and mn[2] > 0.84 and mx[2] < 0.95 and abs(mn[0]) < 0.35 and abs(mx[0]) < 0.35 and len(comp) < 400)
    if keys or letters: kill.extend(comp)
print("PIANO removed verts", len(kill))
bmesh.ops.delete(bm, geom=list(set(kill)), context='VERTS'); bm.to_mesh(pi.data); bm.free()
pi.matrix_world = ROT @ pi.matrix_world
bpy.context.view_layer.update()
_pd = bpy.context.evaluated_depsgraph_get(); _pe = pi.evaluated_get(_pd); _pm = _pe.to_mesh()
PIANO_BVH = BVHTree.FromPolygons([pi.matrix_world @ v.co for v in _pm.vertices], [tuple(p.vertices) for p in _pm.polygons]); _pe.to_mesh_clear()
def piano_top(x, y, z0=2.0):
    hit = PIANO_BVH.ray_cast(Vector((x, y, z0)), Vector((0, 0, -1)), 5.0)
    return hit[0].z if hit[0] is not None else None
print("PIANO tops", [(y, round(piano_top(0.0, y) or -1, 4)) for y in (-0.2, -0.25, -0.3, -0.34, -0.4, -0.5, -0.8)])
for m in pi.data.materials:
    if m and m.use_nodes:
        for p in [n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED']:
            p.inputs["Coat Weight"].default_value = 0.5; p.inputs["Coat Roughness"].default_value = 0.08
            p.inputs["Roughness"].default_value = max(0.3, p.inputs["Roughness"].default_value)
        sat_boost_mat = m
for m in pi.data.materials:
    nt = m.node_tree
    for p in [n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED']:
        bc = p.inputs["Base Color"]
        if bc.is_linked:
            src_ = bc.links[0].from_socket
            hs = nt.nodes.new("ShaderNodeHueSaturation"); hs.inputs["Saturation"].default_value = 1.45; hs.inputs["Value"].default_value = 1.5
            nt.links.new(src_, hs.inputs["Color"]); nt.links.new(hs.outputs["Color"], bc)
        else:
            bc.default_value = (0.20, 0.045, 0.02, 1)
# keybed under the keys (felt red) and a plain fallboard face over the old lettering area
felt = fabric("M_Felt", (0.45, 0.02, 0.04), scale=600)
to(box("KeyBed", (1.354, 0.17, 0.02), (0, -0.085, 0.773), felt, bevel=0.0), C_SET)

# ================================================================== 88 hinged keys (bevelled ivory / ebony), origin at the hinge
ivory = mat("M_Ivory", (0.93, 0.89, 0.78), rough=0.25, coat=0.4)
ebony = mat("M_Ebony", (0.015, 0.012, 0.012), rough=0.22, coat=0.6)
WP = 0.025865; WX0 = 0.659; HINGE_Y = -0.152; HINGE_Z = 0.790
KEY_TOP_W = 0.8057; KEY_TOP_B = 0.8177; BLACK_Y0 = -0.055
NOTES = "ABCDEFG"
KEYS = {}      # name -> dict(obj, x, top, y0, y1, black)
def key_obj(name, w, y0, y1, z0, z1, x, material, bev):
    me = bpy.data.meshes.new(name); o = bpy.data.objects.new(name, me); C_SET.objects.link(o)
    bm = bmesh.new()
    r = bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x = v.co.x * w; v.co.y = (y0 + y1) / 2 - HINGE_Y + v.co.y * (y1 - y0); v.co.z = (z0 + z1) / 2 - HINGE_Z + v.co.z * (z1 - z0)
    bm.to_mesh(me); bm.free()
    b = o.modifiers.new("bev", 'BEVEL'); b.width = bev; b.segments = 2; b.limit_method = 'ANGLE'
    me.materials.append(material)
    for p in me.polygons: p.use_smooth = True
    o.location = (x, HINGE_Y, HINGE_Z); o.rotation_mode = 'XYZ'
    return o
for i in range(52):
    x = WX0 - i * WP
    o = key_obj("KeyW%02d" % i, WP - 0.0012, 0.0, HINGE_Y, 0.7837, KEY_TOP_W, x, ivory, 0.0012)
    KEYS[o.name] = dict(obj=o, x=x, top=KEY_TOP_W, black=False, note=NOTES[i % 7])
    if NOTES[i % 7] in "ACDFG" and i < 51:
        xb = x - WP / 2
        ob = key_obj("KeyB%02d" % i, 0.0124, BLACK_Y0, HINGE_Y, KEY_TOP_W - 0.004, KEY_TOP_B, xb, ebony, 0.0018)
        KEYS[ob.name] = dict(obj=ob, x=xb, top=KEY_TOP_B, black=True, note=NOTES[i % 7] + "#")
print("KEYS", len(KEYS))
# key slip (front rail) under the key fronts and cheek blocks: the model keeps its own cheeks

# ================================================================== bench (raised so the forearms run level to the keys), candelabra
be = SRCO["Bench"]; be.name = "Bench"; to(be, C_SET)
be.matrix_world = ROT @ be.matrix_world
vs = [be.matrix_world @ v.co for v in be.data.vertices]; top0 = max(v.z for v in vs)
BENCH_TOP = 0.525
be.scale.z = BENCH_TOP / top0
be.location = (0.0, 0.60, 0.0)
bpy.context.view_layer.update()
vs = [be.matrix_world @ v.co for v in be.data.vertices]
BENCH_C = Vector(((min(v.x for v in vs) + max(v.x for v in vs)) / 2, (min(v.y for v in vs) + max(v.y for v in vs)) / 2, max(v.z for v in vs)))
print("BENCH", [round(x, 3) for x in BENCH_C], "y", round(min(v.y for v in vs), 3), round(max(v.y for v in vs), 3))
cd = SRCO["Candelabra_A"]; cd.name = "Candelabra_A"; to(cd, C_PROPS)
cd.matrix_world = ROT @ cd.matrix_world
bpy.context.view_layer.update()
_cv = [cd.matrix_world @ v.co for v in cd.data.vertices]
cd.location += Vector((-0.42, -0.62, 0)) - Vector(((min(v.x for v in _cv) + max(v.x for v in _cv)) / 2, (min(v.y for v in _cv) + max(v.y for v in _cv)) / 2, 0))
cd.location.z += piano_top(-0.42, -0.62) - min(v.z for v in _cv)
for m in cd.data.materials: tint(m, (1.0, 0.85, 0.5))

# ================================================================== room (deep teal panelled walls, warm parquet, crimson rug, night window)
wall_m = mat("M_Wall", (0.015, 0.20, 0.22), rough=0.55)
nt = wall_m.node_tree; p = nt.nodes["Principled BSDF"]
tc = nt.nodes.new("ShaderNodeTexCoord"); nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 3.0
cr = nt.nodes.new("ShaderNodeValToRGB"); cr.color_ramp.elements[0].color = (0.010, 0.15, 0.17, 1); cr.color_ramp.elements[1].color = (0.03, 0.27, 0.28, 1)
nt.links.new(tc.outputs["Object"], nz.inputs["Vector"]); nt.links.new(nz.outputs["Fac"], cr.inputs["Fac"]); nt.links.new(cr.outputs["Color"], p.inputs["Base Color"])
panel_m = mat("M_Panel", (0.012, 0.12, 0.14), rough=0.4, coat=0.2)
gold = mat("M_Gold", (0.85, 0.55, 0.16), rough=0.28, metal=1.0)
floor_m = wood("M_Parquet", (0.20, 0.06, 0.02), (0.38, 0.13, 0.04), scale=6.0, rough=0.35)
rug_m = mat("M_Rug", (0.42, 0.02, 0.05), rough=0.85)
nt = rug_m.node_tree; p = nt.nodes["Principled BSDF"]
tc = nt.nodes.new("ShaderNodeTexCoord"); wv = nt.nodes.new("ShaderNodeTexWave"); wv.wave_type = 'RINGS'; wv.inputs["Scale"].default_value = 2.2; wv.inputs["Distortion"].default_value = 4.0
cr = nt.nodes.new("ShaderNodeValToRGB"); cr.color_ramp.interpolation = 'CONSTANT'
cr.color_ramp.elements[0].color = (0.40, 0.015, 0.045, 1); cr.color_ramp.elements[1].position = 0.78; cr.color_ramp.elements[1].color = (0.75, 0.42, 0.06, 1)
nt.links.new(tc.outputs["Object"], wv.inputs["Vector"]); nt.links.new(wv.outputs["Fac"], cr.inputs["Fac"]); nt.links.new(cr.outputs["Color"], p.inputs["Base Color"])
RX0, RX1, RY0, RY1, RH = -3.0, 3.0, -3.4, 2.3, 3.6
for o in (box("Floor", (RX1 - RX0, RY1 - RY0, 0.04), ((RX0 + RX1) / 2, (RY0 + RY1) / 2, -0.02), floor_m, bevel=0),
          box("Ceiling", (RX1 - RX0, RY1 - RY0, 0.04), ((RX0 + RX1) / 2, (RY0 + RY1) / 2, RH + 0.02), panel_m, bevel=0),
          box("Rug", (2.6, 3.4, 0.008), (0.0, -0.55, 0.004), rug_m, bevel=0.003),
          box("Wall_Back", (RX1 - RX0, 0.1, RH), ((RX0 + RX1) / 2, RY1 + 0.05, RH / 2), wall_m, bevel=0),
          box("Wall_Front", (RX1 - RX0, 0.1, RH), ((RX0 + RX1) / 2, RY0 - 0.05, RH / 2), wall_m, bevel=0),
          box("Wall_Left", (0.1, RY1 - RY0, RH), (RX1 + 0.05, (RY0 + RY1) / 2, RH / 2), wall_m, bevel=0),
          box("Wall_Right", (0.1, RY1 - RY0, RH), (RX0 - 0.05, (RY0 + RY1) / 2, RH / 2), wall_m, bevel=0)):
    to(o, C_SET)
def frame4(name, w, h, center, normal_axis, t=0.04, d=0.03, material=None, parent=None):
    """a moulded rectangular frame of four bevelled bars in the plane normal to normal_axis ('X' or 'Y')"""
    material = material or gold; out = []
    for (dx, dz, sw, sh) in ((0, h / 2, w + t, t), (0, -h / 2, w + t, t), (w / 2, 0, t, h + t), (-w / 2, 0, t, h + t)):
        if normal_axis == 'Y': loc = Vector(center) + Vector((dx, 0, dz)); size = (sw, d, sh)
        else: loc = Vector(center) + Vector((0, dx, dz)); size = (d, sw, sh)
        o = box(name, size, loc, material, bevel=min(t, d) * 0.3); to(o, C_SET); out.append(o)
        if parent is not None:
            mw = o.matrix_world.copy(); o.parent = parent; o.matrix_world = mw
    return out
# wainscot panels with gilt mouldings on every wall
def panels_along(axis, fixed, a0, a1, inward, n):
    L = (a1 - a0) / n
    for k in range(n):
        c = a0 + (k + 0.5) * L
        if axis == 'X':
            loc = Vector((c, fixed + inward * 0.012, 0.55)); size = (L - 0.16, 0.02, 0.72)
            fr = Vector((c, fixed + inward * 0.024, 0.55)); fs_ = (L - 0.10, 0.012, 0.78)
        else:
            loc = Vector((fixed + inward * 0.012, c, 0.55)); size = (0.02, L - 0.16, 0.72)
            fr = Vector((fixed + inward * 0.024, c, 0.55)); fs_ = (0.012, L - 0.10, 0.78)
        to(box("Panel", size, loc, panel_m, bevel=0.008), C_SET)
        frame4("PanelFrame", (L - 0.12), 0.74, fr, 'Y' if axis == 'X' else 'X', t=0.025, d=0.018)
panels_along('X', RY1, RX0, RX1, -1, 5); panels_along('Y', RX1, RY0, RY1, -1, 5); panels_along('Y', RX0, RY0, RY1, 1, 5)
for (nm, size, loc) in (("DadoRail_B", (RX1 - RX0, 0.05, 0.05), (0, RY1 - 0.025, 1.0)), ("DadoRail_L", (0.05, RY1 - RY0, 0.05), (RX1 - 0.025, (RY0 + RY1) / 2, 1.0)),
                        ("DadoRail_R", (0.05, RY1 - RY0, 0.05), (RX0 + 0.025, (RY0 + RY1) / 2, 1.0)),
                        ("Cornice_B", (RX1 - RX0, 0.12, 0.12), (0, RY1 - 0.06, RH - 0.06)), ("Cornice_L", (0.12, RY1 - RY0, 0.12), (RX1 - 0.06, (RY0 + RY1) / 2, RH - 0.06)),
                        ("Cornice_R", (0.12, RY1 - RY0, 0.12), (RX0 + 0.06, (RY0 + RY1) / 2, RH - 0.06))):
    to(box(nm, size, loc, gold, bevel=0.01), C_SET)
# night window on the left wall (+X) behind the piano, purple-blue sky with a moon glow
sky = gradient_emit("M_NightSky", (0.10, 0.10, 0.55), (0.30, 0.06, 0.40), strength=1.4)
win = box("Window_Night", (0.02, 1.3, 2.0), (RX1 - 0.01, -1.6, 1.85), sky, bevel=0); to(win, C_SET)
moon = mat("M_Moon", (1, 0.95, 0.8), emit=((1.0, 0.92, 0.75), 6.0))
mo = sphere("Moon", 0.09, (RX1 - 0.03, -1.35, 2.45), moon); mo.scale.x = 0.2; to(mo, C_SET)
for (nm, size, loc) in (("Mullion_V", (0.05, 0.05, 2.0), (RX1 - 0.04, -1.6, 1.85)), ("Mullion_H", (0.05, 1.3, 0.05), (RX1 - 0.04, -1.6, 2.2)),
                        ("WinFrame_T", (0.08, 1.42, 0.08), (RX1 - 0.04, -1.6, 2.88)), ("WinFrame_B", (0.12, 1.42, 0.08), (RX1 - 0.06, -1.6, 0.82))):
    to(box(nm, size, loc, gold, bevel=0.01), C_SET)
curt_m = fabric("M_Curtain", (0.36, 0.03, 0.30), scale=300, bump=0.3)
for k, yy in enumerate((-2.45, -0.75)):
    bpy.ops.mesh.primitive_plane_add(size=1, location=(RX1 - 0.12, yy, 1.78))
    cu = bpy.context.active_object; cu.name = "Curtain_%d" % k; cu.scale = (1, 0.5, 3.4); cu.rotation_euler = (0, math.radians(90), 0)
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    sd = cu.modifiers.new("sd", 'SUBSURF'); sd.levels = 4; sd.render_levels = 4; sd.subdivision_type = 'SIMPLE'
    tx = bpy.data.textures.new("CurtWave_%d" % k, 'WOOD'); tx.wood_type = 'BANDNOISE'; tx.noise_scale = 0.06; tx.turbulence = 1.0
    dp = cu.modifiers.new("folds", 'DISPLACE'); dp.texture = tx; dp.strength = 0.07; dp.texture_coords = 'GLOBAL'; dp.direction = 'X'
    so = cu.modifiers.new("th", 'SOLIDIFY'); so.thickness = 0.01
    cu.data.materials.append(curt_m); bpy.ops.object.shade_smooth(); to(cu, C_SET)
# paintings: abstract colour fields (no imagery, no text) in gilt frames on the right wall
def painting(name, loc, size, cols, rot_z):
    m = mat("M_" + name, cols[0], rough=0.6)
    nt = m.node_tree; p = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord"); nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 2.5; nz.inputs["Detail"].default_value = 6
    cr = nt.nodes.new("ShaderNodeValToRGB"); cr.color_ramp.elements[0].color = (*cols[0], 1); cr.color_ramp.elements[1].color = (*cols[1], 1)
    e3 = cr.color_ramp.elements.new(0.5); e3.color = (*cols[2], 1)
    nt.links.new(tc.outputs["Generated"], nz.inputs["Vector"]); nt.links.new(nz.outputs["Fac"], cr.inputs["Fac"]); nt.links.new(cr.outputs["Color"], p.inputs["Base Color"])
    cv = box(name, (0.02, size[0], size[1]), loc, m, bevel=0); to(cv, C_SET)
    frame4(name + "_Frame", size[0] + 0.03, size[1] + 0.03, Vector(loc) + Vector((0.012 if loc[0] < 0 else -0.012, 0, 0)), 'X', t=0.07, d=0.04)
    return cv
painting("Painting_A", (RX0 + 0.05, -0.6, 2.1), (1.1, 0.8), ((0.05, 0.15, 0.40), (0.85, 0.55, 0.10), (0.55, 0.05, 0.15)), math.radians(-90))
painting("Painting_B", (RX0 + 0.05, 1.3, 2.15), (0.7, 0.95), ((0.40, 0.10, 0.02), (0.10, 0.45, 0.40), (0.85, 0.70, 0.30)), math.radians(-90))
# the DA KRAS FILMS logo: a framed, glazed print on the back wall behind the composer (dark ground, white logo)
lg = bpy.data.images.load(LOGO_W); lg.pack()
lm = bpy.data.materials.new("M_LogoPrint"); lm.use_nodes = True; nt = lm.node_tree; p = nt.nodes["Principled BSDF"]
tx = nt.nodes.new("ShaderNodeTexImage"); tx.image = lg; tx.extension = 'CLIP'
bgc = nt.nodes.new("ShaderNodeMix"); bgc.data_type = 'RGBA'; bgc.inputs["A"].default_value = (0.05, 0.03, 0.10, 1)
nt.links.new(tx.outputs["Alpha"], bgc.inputs["Factor"]); nt.links.new(tx.outputs["Color"], bgc.inputs["B"])
nt.links.new(bgc.outputs["Result"], p.inputs["Base Color"]); nt.links.new(bgc.outputs["Result"], p.inputs["Emission Color"])
p.inputs["Emission Strength"].default_value = 0.35; p.inputs["Roughness"].default_value = 0.45
LOGO_W_M, LOGO_H_M = 0.95, 0.95 * 414 / 967
lo = bpy.data.objects.new("LogoPrint", bpy.data.meshes.new("LogoPrint")); C_SET.objects.link(lo)
bm = bmesh.new()
for (x, z) in ((-0.5, -0.5), (0.5, -0.5), (0.5, 0.5), (-0.5, 0.5)): bm.verts.new((x * (LOGO_W_M + 0.16), 0, z * (LOGO_H_M + 0.16)))
bm.faces.new(bm.verts); bm.to_mesh(lo.data); bm.free()
uv = lo.data.uv_layers.new()
k = 0.16 / LOGO_W_M; kz = 0.16 / LOGO_H_M
for li, l in enumerate(lo.data.loops):
    co = lo.data.vertices[l.vertex_index].co
    uv.data[li].uv = (0.5 + co.x / LOGO_W_M, 0.5 + co.z / LOGO_H_M)
lo.data.materials.append(lm)
LOGO_LOC = Vector((0.75, RY1 - 0.03, 1.95))
lo.location = LOGO_LOC
frame4("LogoFrame", LOGO_W_M + 0.20, LOGO_H_M + 0.20, LOGO_LOC + Vector((0, -0.01, 0)), 'Y', t=0.06, d=0.04)
lb = box("LogoBack", (LOGO_W_M + 0.2, 0.01, LOGO_H_M + 0.2), LOGO_LOC + Vector((0, 0.02, 0)), mat("M_LogoBack", (0.05, 0.03, 0.10), rough=0.5), bevel=0); to(lb, C_SET)

# ================================================================== sheet music (generated staves + note heads; no text)
def sheet_image(name, seed, w=512, h=704):
    import numpy as np
    rng = random.Random(seed)
    A = np.ones((h, w, 4), dtype=np.float32); A[..., 0] = 0.96; A[..., 1] = 0.92; A[..., 2] = 0.80
    ink = (0.05, 0.04, 0.06)
    y = 70
    while y < h - 60:
        for l in range(5):
            yy = y + l * 9; A[h - 1 - yy, 30:w - 30, :3] = ink
        x = 50
        while x < w - 50:
            nl = rng.randint(-2, 10); cy = y + nl * 4.5
            for dy in range(-4, 5):
                for dx in range(-6, 7):
                    if (dx / 6.0) ** 2 + (dy / 4.0) ** 2 <= 1.0:
                        py = int(cy + dy); px = x + dx
                        if 0 <= py < h: A[h - 1 - py, px, :3] = ink
            st = -1 if nl > 4 else 1
            for k in range(26):
                py = int(cy - st * k)
                if 0 <= py < h: A[h - 1 - py, x + 5 * st, :3] = ink
            if rng.random() < 0.35: x += 16
            x += rng.randint(22, 34)
            if rng.random() < 0.12:
                A[h - 1 - (y + 36): h - 1 - y, x - 8:x - 6, :3] = ink
        y += 78
    img = bpy.data.images.new(name, w, h, alpha=True); img.pixels.foreach_set(A.ravel()); img.pack(); return img
SHEETS = [sheet_image("Sheet%d" % i, 11 + i) for i in range(3)]
def page(name, img, size, loc, rot, parent_coll=C_PROPS):
    m = bpy.data.materials.new("M_" + name); m.use_nodes = True; nt = m.node_tree; p = nt.nodes["Principled BSDF"]
    tx = nt.nodes.new("ShaderNodeTexImage"); tx.image = img; nt.links.new(tx.outputs["Color"], p.inputs["Base Color"])
    p.inputs["Roughness"].default_value = 0.7
    bpy.ops.mesh.primitive_plane_add(size=1, location=loc, rotation=rot)
    o = bpy.context.active_object; o.name = name; o.scale = (size[0], size[1], 1); bpy.ops.object.transform_apply(scale=True)
    so = o.modifiers.new("th", 'SOLIDIFY'); so.thickness = 0.0008
    o.data.materials.append(m); to(o, parent_coll); return o
# music desk: a carved walnut stand on the piano case, leaning back, two open manuscript pages
desk_w = wood("M_DeskWood", (0.06, 0.014, 0.006), (0.16, 0.045, 0.015), scale=9)
DESK_TILT = math.radians(14)
DZ = piano_top(0.0, -0.33)
desk = box("MusicDesk", (0.62, 0.018, 0.24), (0.0, -0.335 - 0.12 * math.sin(DESK_TILT), DZ + 0.022 + 0.12 * math.cos(DESK_TILT)), desk_w, bevel=0.006, rot=(-DESK_TILT, 0, 0)); to(desk, C_PROPS)
to(box("MusicDesk_Ledge", (0.66, 0.05, 0.022), (0.0, -0.315, DZ + 0.011), desk_w, bevel=0.005), C_PROPS)
nrm = Vector((0, math.cos(DESK_TILT), math.sin(DESK_TILT)))
for k, img in ((-1, SHEETS[0]), (1, SHEETS[1])):
    page("DeskPage%d" % (k + 1), img, (0.19, 0.225), desk.location + Vector((k * 0.112, 0, 0.01)) + nrm * 0.011, (math.radians(90) - DESK_TILT, 0, 0))
# manuscript pages lying on the closed lid and on the side table (fixed props, never move)
LID_Z = piano_top(0.1, -0.95)
for i, (x, y, r) in enumerate(((0.30, -0.75, 12), (0.05, -0.95, -20), (-0.35, -1.25, 35), (0.42, -1.15, -8))):
    page("LidPage%d" % i, SHEETS[i % 3], (0.215, 0.29), (x, y, LID_Z + 0.002 + 0.0012 * i), (0, 0, math.radians(r)))

# ================================================================== side table with candles, inkwell and a quill (to the composer's right, +y side)
tw = wood("M_TableWood", (0.06, 0.015, 0.006), (0.15, 0.04, 0.012), scale=7)
ST = Vector((-1.15, 0.55, 0.0))
to(box("SideTable_Top", (0.62, 0.46, 0.035), ST + Vector((0, 0, 0.74)), tw, bevel=0.01), C_PROPS)
for dx in (-0.27, 0.27):
    for dy in (-0.19, 0.19):
        to(cyl("SideTable_Leg", 0.018, 0.72, ST + Vector((dx, dy, 0.36)), tw, verts=12), C_PROPS)
ink_m = mat("M_InkGlass", (0.02, 0.05, 0.12), rough=0.1, coat=0.8)
to(cyl("Inkwell", 0.03, 0.05, ST + Vector((0.14, 0.08, 0.783)), ink_m, verts=24, bevel=0.006), C_PROPS)
quill_m = mat("M_Quill", (0.95, 0.93, 0.88), rough=0.6)
q = cyl("Quill", 0.0035, 0.26, ST + Vector((0.10, 0.06, 0.80)), quill_m, rot=(math.radians(-62), 0, math.radians(25)), verts=8); to(q, C_PROPS)
for i in range(4):
    page("TablePage%d" % i, SHEETS[(i + 2) % 3], (0.215, 0.29), ST + Vector((-0.09 + 0.01 * i, -0.02 - 0.008 * i, 0.758 + 0.0012 * i)), (0, 0, math.radians(-10 + 7 * i)))
# candles (wax + emissive flame + small warm light) on the candelabra and the side table
wax = mat("M_Wax", (0.95, 0.90, 0.78), rough=0.5, sss=0.3)
flame_m = mat("M_Flame", (1, 0.7, 0.3), emit=((1.0, 0.62, 0.22), 18.0))
CANDLES = []
def candle(loc, h=0.14):
    c = cyl("Candle", 0.012, h, Vector(loc) + Vector((0, 0, h / 2)), wax, verts=16); to(c, C_PROPS)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.008, location=Vector(loc) + Vector((0, 0, h + 0.016)), segments=12, ring_count=8)
    f = bpy.context.active_object; f.name = "Flame"; f.scale = (1, 1, 2.3); f.data.materials.append(flame_m); to(f, C_FX)
    L = bpy.data.lights.new("CandleLight", 'POINT'); L.energy = 6.0; L.color = (1.0, 0.62, 0.28); L.shadow_soft_size = 0.02
    lo_ = bpy.data.objects.new("CandleLight", L); lo_.location = Vector(loc) + Vector((0, 0, h + 0.05)); C_FX.objects.link(lo_)
    CANDLES.append((f, lo_))
bpy.context.view_layer.update()
cvs = [cd.matrix_world @ v.co for v in cd.data.vertices]
cmn = Vector([min(v[i] for v in cvs) for i in range(3)]); cmx = Vector([max(v[i] for v in cvs) for i in range(3)])
cc = (cmn + cmx) / 2; cw = (cmx - cmn)
for dx, dz in ((-0.5, 0.75), (0.0, 1.0), (0.5, 0.75)):
    candle((cc.x + dx * cw.x * 0.92, cc.y, cmn.z + dz * cw.z + 0.004), 0.12)
for d in ((-0.12, -0.12), (0.18, 0.12)):
    candle(ST + Vector((d[0], d[1], 0.7575)), 0.18)
to(cyl("CandleDish", 0.04, 0.008, ST + Vector((-0.12, -0.12, 0.761)), gold, verts=24), C_PROPS)
to(cyl("CandleDish", 0.04, 0.008, ST + Vector((0.18, 0.12, 0.761)), gold, verts=24), C_PROPS)

# ================================================================== the brass rod and its clamp on the piano case
brass = mat("M_Brass", (0.95, 0.62, 0.20), rough=0.22, metal=1.0)
ROD_R = 0.0028; ROD_LEN = 0.92
rod = cyl("Rod", ROD_R, ROD_LEN, (0, 0, ROD_LEN / 2), brass, verts=20, bevel=0.0012)
bpy.ops.object.select_all(action='DESELECT'); rod.select_set(True); bpy.context.view_layer.objects.active = rod
sc.cursor.location = (0, 0, 0); bpy.ops.object.origin_set(type='ORIGIN_CURSOR'); to(rod, C_PROPS)
CT = piano_top(0.0, -0.215)
CLAMP_P = Vector((0.0, -0.205, CT + 0.04))     # where the rod passes through the collar (front edge of the case top)
post = cyl("RodClamp_Post", 0.006, 0.03, Vector((0, -0.205, CT + 0.019)), brass, verts=16, bevel=0.002); to(post, C_PROPS)
foot = box("RodClamp_Foot", (0.07, 0.04, 0.008), Vector((0, -0.215, CT + 0.004)), brass, bevel=0.003); to(foot, C_PROPS)
bpy.ops.mesh.primitive_torus_add(major_radius=0.0085, minor_radius=0.0035, location=CLAMP_P)
col_ = bpy.context.active_object; col_.name = "RodClamp_Collar"; col_.data.materials.append(brass); bpy.ops.object.shade_smooth(); to(col_, C_PROPS)
for sx in (-1, 1):
    to(cyl("RodClamp_Screw", 0.0028, 0.005, Vector((sx * 0.026, -0.215, CT + 0.0095)), brass, verts=10), C_PROPS)
ce = empty("RodClamp_Point", CLAMP_P, size=0.02); to(ce, C_PROPS)

# ================================================================== rings: cyan glow rings that travel along the rod (driven in stage B)
ring_m = mat("M_RingGlow", (0.3, 0.95, 1.0), emit=((0.25, 0.92, 1.0), 9.0))
for i in range(10):
    bpy.ops.mesh.primitive_torus_add(major_radius=0.0105, minor_radius=0.0018, location=(0, 0, 0), major_segments=40, minor_segments=8)
    r_ = bpy.context.active_object; r_.name = "RodRing%02d" % i; r_.data.materials.append(ring_m); bpy.ops.object.shade_smooth(); to(r_, C_FX)

# ================================================================== look and render settings (PRODUCTION_RULES: fast + zero error)
sc.render.engine = 'CYCLES'; cy = sc.cycles
cy.device = 'CPU'; cy.samples = 64; cy.use_adaptive_sampling = True; cy.adaptive_threshold = 0.04
cy.use_denoising = True; cy.denoiser = 'OPENIMAGEDENOISE'
cy.max_bounces = 6; cy.diffuse_bounces = 3; cy.glossy_bounces = 3; cy.transmission_bounces = 6; cy.transparent_max_bounces = 16
cy.caustics_reflective = False; cy.caustics_refractive = False
sc.render.use_persistent_data = True; sc.render.use_simplify = True; sc.cycles.texture_limit_render = '2048'
sc.render.use_motion_blur = False
sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Punchy'; sc.view_settings.exposure = 0.35
w = bpy.data.worlds.new("World"); sc.world = w; w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (0.02, 0.04, 0.10, 1); w.node_tree.nodes["Background"].inputs[1].default_value = 0.6
def area(name, loc, target, power, size, col):
    L = bpy.data.lights.new(name, 'AREA'); L.energy = power; L.size = size; L.color = col
    o = bpy.data.objects.new(name, L); C_FX.objects.link(o); o.location = loc
    t = bpy.data.objects.new(name + "_T", None); C_FX.objects.link(t); t.location = target
    c = o.constraints.new('TRACK_TO'); c.target = t; c.track_axis = 'TRACK_NEGATIVE_Z'; c.up_axis = 'UP_Y'
    return o
area("Key_Warm", (-1.0, -0.9, 2.3), (0, 0.45, 1.2), 260, 1.2, (1.0, 0.72, 0.45))
area("Fill_Cool", (1.6, -0.2, 1.7), (0, 0.4, 1.1), 110, 1.6, (0.55, 0.70, 1.0))
area("Rim_Back", (0.4, 2.0, 2.6), (0, 0.45, 1.3), 180, 1.0, (0.75, 0.85, 1.0))
area("Room_Top", (0, -0.6, 3.4), (0, -0.6, 0), 260, 3.0, (1.0, 0.82, 0.62))
sc.render.filepath = "//render/BeethovenDeaf_v011_####.png"; sc.render.image_settings.file_format = 'PNG'
sc.render.image_settings.color_mode = 'RGB'
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("BUILD_OK", OUT)
