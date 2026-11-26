"""SpeakWithoutSight v007 stage A (from scratch): the parlour, the settee, the girl and her teacher.
blender -b --python 01_build.py -- <polyhaven_dir> <out.blend>

Layout (metres, Z up, the camera side is -Y): a late-1800s parlour. A plum velvet settee stands with its seat front at
y=-0.30 (seat top z=0.44). The GIRL (one MPFB model, ~1.22 m) sits on its right half (x=+0.30) and her TEACHER (one MPFB
model, ~1.65 m) on its left half (x=-0.30), both facing -Y; 02_animate.py seats and turns them. Back wall y=+0.80 with a
tall window (behind the teacher), a framed DA KRAS FILMS sampler above the settee and a grandfather clock (girl side).
An oil lamp on a side table stands beside the girl. The window shows a garden backdrop whose season and sky are keyed
values (02), never the scene clock."""
import bpy, bmesh, sys, math, random, os
from mathutils import Vector, Matrix
HERE = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(HERE, "lib_build.py")).read())
a = sys.argv[sys.argv.index("--") + 1:]
PH, OUT = a[0], a[1]
BRAND = "/home/user/Muhammed/blender/assets/brand/DaKrasFilms_logo_dark.png"
random.seed(19)
for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob, do_unlink=True)
sc = bpy.context.scene
sc.render.fps = 60
sc.frame_start, sc.frame_end = 1, 1645
sc.render.resolution_x, sc.render.resolution_y = 1080, 1920

# ================================================================== the two characters (ONE model each, all film)
G, GB = human("Girl", 0.0, 0.17, {"asian": 0.05, "caucasian": 0.85, "african": 0.10}, "ponytail01/ponytail01.mhclo",
              "young_caucasian_female/young_caucasian_female.mhmat", "eyebrow010/eyebrow010.mhclo",
              height=0.5, weight=0.55, muscle=0.4, clothes=["male_casualsuit03/male_casualsuit03.mhclo", "shoes02/shoes02.mhclo"])
T, TB = human("Teacher", 0.0, 0.42, {"asian": 0.05, "caucasian": 0.35, "african": 0.60}, "afro01/afro01.mhclo",
              "young_african_female/young_african_female.mhmat", "eyebrow010/eyebrow010.mhclo",
              height=0.5, weight=0.55, muscle=0.45, clothes=["male_casualsuit03/male_casualsuit03.mhclo", "shoes01/shoes01.mhclo"])
eye_fix(G); eye_fix(T); eye_group_fix()
_eg = bpy.data.node_groups.get("EnhancedEye")
if _eg: _eg.nodes["Principled BSDF"].inputs["Specular IOR Level"].default_value = 0.1     # no grey sheen over the iris
EG = bpy.data.node_groups.get("EnhancedEye")
for n in (EG.nodes if EG else []):
    if n.type == 'MATH' and abs(n.inputs[1].default_value - 0.92) < 1e-4: n.inputs[1].default_value = 0.96

def iris(rig, major, minor):
    for c in rig.children:
        if c.type == 'MESH' and "high-poly" in c.name:
            for m in c.data.materials:
                for n in m.node_tree.nodes:
                    if n.type == 'GROUP' and "IrisMajorColor" in n.inputs:
                        n.inputs["IrisMajorColor"].default_value = (*major, 1); n.inputs["IrisMinorColor"].default_value = (*minor, 1)
                        n.inputs["Clearcoat"].default_value = 0.0; n.inputs["InnerLayerRoughness"].default_value = 0.6
iris(G, (0.32, 0.42, 0.52), (0.14, 0.20, 0.27))      # pale grey-blue: soft, unfocused (no glowing / dead white)
iris(T, (0.13, 0.06, 0.02), (0.05, 0.025, 0.01))

def recolor(m, target, level=0.75):
    """replace the hue of the garment texture by `target`, keeping its weave/fold shading (luminance normalised)"""
    import numpy as np
    nt = m.node_tree
    tx = [n for n in nt.nodes if n.type == 'TEX_IMAGE' and n.image and "diffuse" in n.image.name.lower()][0]
    px = np.array(tx.image.pixels[:]).reshape(-1, 4)[::7]
    avg = float((0.3 * px[:, 0] + 0.59 * px[:, 1] + 0.11 * px[:, 2]).mean()) or 0.3
    bw = nt.nodes.new("ShaderNodeRGBToBW"); nt.links.new(tx.outputs["Color"], bw.inputs[0])
    g = nt.nodes.new("ShaderNodeMath"); g.operation = 'MULTIPLY'; g.inputs[1].default_value = level / avg; nt.links.new(bw.outputs[0], g.inputs[0])
    pw = nt.nodes.new("ShaderNodeMath"); pw.operation = 'POWER'; pw.inputs[1].default_value = 0.4; nt.links.new(g.outputs[0], pw.inputs[0])
    mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs["Factor"].default_value = 1.0
    mx.inputs["A"].default_value = (*target, 1); nt.links.new(pw.outputs[0], mx.inputs["B"])
    for lk in list(tx.outputs["Color"].links):
        if lk.to_node != bw: nt.links.new(mx.outputs["Result"], lk.to_socket)

def recolor_garment(rig, top_mult, skirt_mult, name):
    """the MPFB elegantsuit has one material for blouse + skirt: split it by the UV island (skirt = lower body verts)
    into two materials and tint each (saturated period colours)."""
    cl = [c for c in rig.children if c.type == 'MESH' and "suit" in c.name][0]
    cl.name = name
    m0 = cl.data.materials[0]
    mt = m0.copy(); mt.name = name + "_top"; ms = m0.copy(); ms.name = name + "_skirt"
    recolor(mt, top_mult); recolor(ms, skirt_mult)
    for mm in (mt, ms):
        for nd in mm.node_tree.nodes:
            if nd.type == 'NORMAL_MAP': nd.inputs["Strength"].default_value = 0.5
            if nd.type == 'BSDF_PRINCIPLED':
                nd.inputs["Sheen Weight"].default_value = 0.25
    cl.data.materials.clear(); cl.data.materials.append(mt); cl.data.materials.append(ms)
    # skirt = the connected mesh part(s) with the low mean height (the blouse and the skirt are separate parts)
    bm = bmesh.new(); bm.from_mesh(cl.data); bm.verts.ensure_lookup_table()
    comp = {}; cid = 0
    for v in bm.verts:
        if v.index in comp: continue
        st = [v]; comp[v.index] = cid
        while st:
            x = st.pop()
            for e in x.link_edges:
                y = e.other_vert(x)
                if y.index not in comp: comp[y.index] = cid; st.append(y)
        cid += 1
    zs = {}
    for v in bm.verts: zs.setdefault(comp[v.index], []).append(v.co.z)
    bm.free()
    zmax = max(v.co.z for v in cl.data.vertices); zmin = min(v.co.z for v in cl.data.vertices)
    skirt_c = {c for c, l in zs.items() if sum(l) / len(l) < zmin + 0.45 * (zmax - zmin)}
    print("GARMENT", name, "parts", cid, "skirt parts", len(skirt_c), [(c, round(sum(l) / len(l), 2), len(l)) for c, l in zs.items()][:8])
    for p in cl.data.polygons:
        p.material_index = 1 if comp[p.vertices[0]] in skirt_c else 0
    # the body under the skirt is hidden (seated thighs must never poke through the fabric)
    hem = min(cl.data.vertices[i].co.z for i in range(len(cl.data.vertices)) if comp[i] in skirt_c)
    body = [c for c in rig.children if c.type == 'MESH' and c.name.endswith(".body")][0]
    bn = {b.name for b in rig.data.bones}
    bi = {g.index: g.name for g in body.vertex_groups if g.name in bn}
    covered = set()
    for v in body.data.vertices:
        best = (0, None)
        for g in v.groups:
            nm = bi.get(g.group)
            if nm and g.weight > best[0]: best = (g.weight, nm)
        if best[1] and best[1].startswith(("upperleg", "pelvis")) and v.co.z > hem + 0.03:
            covered.add(v.index)
    if rig.name == "Teacher":           # (the girl's skirt never shows her thighs; masking hers exposed the skirt's inside)
        hide_under(body, covered, name="hide_skirt", rings=2)
    print("GARMENT", name, "hem z", round(hem, 3), "hidden body verts", len(covered))
    return cl
GCL = recolor_garment(G, (1.0, 0.45, 0.02), (0.02, 0.06, 0.45), "Girl.clothes")       # saffron blouse, navy skirt
TCL = recolor_garment(T, (0.62, 0.03, 0.10), (0.02, 0.10, 0.12), "Teacher.clothes")    # deep raspberry striped blouse, dark teal skirt
for c in G.children:
    if c.type == 'MESH' and any(k in c.name.lower() for k in ("pony", "eyebrow")):
        for m in c.data.materials: tint(m, (0.55, 0.36, 0.20))      # warm chestnut (one hairstyle, the braid, all film)
for c in T.children:
    if c.type == 'MESH' and any(k in c.name.lower() for k in ("afro", "eyebrow")):
        for m in c.data.materials: tint(m, (0.35, 0.22, 0.15))
for m in GB.data.materials: tint(m, (1.0, 0.86, 0.78))
for m in TB.data.materials: tint(m, (1.05, 0.90, 0.82))
for rig in (G, T):
    for c in rig.children:
        if c.type == 'MESH' and "teeth" in c.name:
            for m in c.data.materials: tint(m, (1.4, 1.35, 1.3))
# solid garments (no paper edges), solidify right after the Armature
for rig in (G, T):
    for c in rig.children:
        if c.type == 'MESH' and ("clothes" in c.name or "shoes" in c.name):
            so = c.modifiers.new("solid", 'SOLIDIFY'); so.thickness = 0.003; so.offset = 1.0; so.use_rim = True
            i = c.modifiers.find("solid")
            while i > c.modifiers.find("Armature") + 1:
                c.modifiers.move(i, i - 1); i -= 1

# ================================================================== materials
def plaster(name, c1, c2, scale=40.0, rough=0.85):
    m = mat(name, c1, rough=rough); nt = m.node_tree; p = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord"); nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = scale
    cr = nt.nodes.new("ShaderNodeValToRGB"); cr.color_ramp.elements[0].color = (*c1, 1); cr.color_ramp.elements[1].color = (*c2, 1)
    nt.links.new(tc.outputs["Object"], nz.inputs["Vector"]); nt.links.new(nz.outputs["Fac"], cr.inputs["Fac"]); nt.links.new(cr.outputs["Color"], p.inputs["Base Color"])
    return m

def wallpaper(name, base, motif, stripe):
    """deep teal damask: vertical stripes + a repeating diamond-flower motif (procedural, no text)"""
    m = mat(name, base, rough=0.7, sheen=0.2); nt = m.node_tree; p = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord"); sep = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(tc.outputs["Object"], sep.inputs[0])
    # horizontal coordinate along the wall = x + y (works for back and side walls)
    hz = nt.nodes.new("ShaderNodeMath"); hz.operation = 'ADD'; nt.links.new(sep.outputs["X"], hz.inputs[0]); nt.links.new(sep.outputs["Y"], hz.inputs[1])
    cxy = nt.nodes.new("ShaderNodeCombineXYZ"); nt.links.new(hz.outputs[0], cxy.inputs[0]); nt.links.new(sep.outputs["Z"], cxy.inputs[1])
    def mth(op, a_, b_=None):
        n_ = nt.nodes.new("ShaderNodeMath"); n_.operation = op
        for i_, x in enumerate((a_, b_)):
            if x is None: continue
            if isinstance(x, (int, float)): n_.inputs[i_].default_value = float(x)
            else: nt.links.new(x, n_.inputs[i_])
        return n_.outputs[0]
    su = mth('SINE', mth('MULTIPLY', hz.outputs[0], 22.0)); sv = mth('SINE', mth('MULTIPLY', sep.outputs["Z"], 16.0))
    sw = mth('SINE', mth('MULTIPLY', mth('ADD', hz.outputs[0], mth('MULTIPLY', sep.outputs["Z"], 0.7)), 44.0))
    mot = mth("ADD", mth("MULTIPLY", su, sv), mth("MULTIPLY", sw, 0.18))
    mr = nt.nodes.new("ShaderNodeMapRange"); mr.inputs["From Min"].default_value = 0.62; mr.inputs["From Max"].default_value = 0.52
    nt.links.new(mot, mr.inputs["Value"])
    wv = nt.nodes.new("ShaderNodeTexWave"); wv.wave_type = 'BANDS'; wv.bands_direction = 'X'; wv.inputs["Scale"].default_value = 3.5
    nt.links.new(cxy.outputs[0], wv.inputs["Vector"])
    st = nt.nodes.new("ShaderNodeMath"); st.operation = 'GREATER_THAN'; st.inputs[1].default_value = 0.985; nt.links.new(wv.outputs["Fac"], st.inputs[0])
    c1 = nt.nodes.new("ShaderNodeMix"); c1.data_type = 'RGBA'; c1.inputs["A"].default_value = (*motif, 1); c1.inputs["B"].default_value = (*base, 1)
    nt.links.new(mr.outputs[0], c1.inputs["Factor"])
    c2 = nt.nodes.new("ShaderNodeMix"); c2.data_type = 'RGBA'; c2.inputs["B"].default_value = (*stripe, 1)
    nt.links.new(c1.outputs["Result"], c2.inputs["A"]); nt.links.new(st.outputs[0], c2.inputs["Factor"])
    nt.links.new(c2.outputs["Result"], p.inputs["Base Color"])
    return m

def wood(name, c1, c2, scale=3.0, rough=0.4, planks=False):
    m = mat(name, c1, rough=rough, coat=0.25); nt = m.node_tree; p = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord"); mp = nt.nodes.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (1, 10, 1)
    wv = nt.nodes.new("ShaderNodeTexWave"); wv.inputs["Scale"].default_value = scale; wv.inputs["Distortion"].default_value = 6.0; wv.inputs["Detail"].default_value = 3.0
    cr = nt.nodes.new("ShaderNodeValToRGB"); cr.color_ramp.elements[0].color = (*c1, 1); cr.color_ramp.elements[1].color = (*c2, 1)
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"]); nt.links.new(mp.outputs["Vector"], wv.inputs["Vector"])
    nt.links.new(wv.outputs["Fac"], cr.inputs["Fac"])
    if planks:
        br = nt.nodes.new("ShaderNodeTexBrick"); br.inputs["Scale"].default_value = 1.0; br.offset = 0.5
        br.inputs["Brick Width"].default_value = 1.6; br.inputs["Row Height"].default_value = 0.16; br.inputs["Mortar Size"].default_value = 0.004
        br.inputs["Color1"].default_value = (1, 1, 1, 1); br.inputs["Color2"].default_value = (0.8, 0.8, 0.8, 1); br.inputs["Mortar"].default_value = (0.15, 0.15, 0.15, 1)
        nt.links.new(tc.outputs["Object"], br.inputs["Vector"])
        mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs["Factor"].default_value = 1.0
        nt.links.new(cr.outputs["Color"], mx.inputs["A"]); nt.links.new(br.outputs["Color"], mx.inputs["B"]); nt.links.new(mx.outputs["Result"], p.inputs["Base Color"])
    else:
        nt.links.new(cr.outputs["Color"], p.inputs["Base Color"])
    return m

def velvet(name, col, sheen_tint=(1, 0.8, 1)):
    m = mat(name, col, rough=0.7, sheen=0.35); p = m.node_tree.nodes["Principled BSDF"]
    p.inputs["Sheen Tint"].default_value = (*sheen_tint, 1); p.inputs["Sheen Roughness"].default_value = 0.35
    nt = m.node_tree; tc = nt.nodes.new("ShaderNodeTexCoord"); nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 60
    bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.08
    nt.links.new(tc.outputs["Object"], nz.inputs["Vector"]); nt.links.new(nz.outputs["Fac"], bp.inputs["Height"]); nt.links.new(bp.outputs["Normal"], p.inputs["Normal"])
    return m

def rug_mat(name):
    """a Persian-style rug: crimson field, navy border bands, gold medallion lattice (procedural, no text)"""
    m = mat(name, (0.25, 0.006, 0.012), rough=0.9, sheen=0.4); nt = m.node_tree; p = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord"); sep = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(tc.outputs["Generated"], sep.inputs[0])
    def mth(op, a_, b_=None):
        n_ = nt.nodes.new("ShaderNodeMath"); n_.operation = op
        for i_, x in enumerate((a_, b_)):
            if x is None: continue
            if isinstance(x, (int, float)): n_.inputs[i_].default_value = float(x)
            else: nt.links.new(x, n_.inputs[i_])
        return n_.outputs[0]
    # distance to the nearest edge in generated coords (0..0.5)
    ex = mth('MINIMUM', sep.outputs["X"], mth('SUBTRACT', 1.0, sep.outputs["X"]))
    ey = mth('MINIMUM', sep.outputs["Y"], mth('SUBTRACT', 1.0, sep.outputs["Y"]))
    e = mth('MINIMUM', ex, ey)
    border = mth('LESS_THAN', e, 0.09); inner = mth('LESS_THAN', mth('ABSOLUTE', mth('SUBTRACT', e, 0.105)), 0.008)
    # diamond lattice (gold lines on crimson) + a central medallion
    u = mth('SUBTRACT', sep.outputs["X"], 0.5); v = mth('SUBTRACT', sep.outputs["Y"], 0.5)
    d1 = mth('ABSOLUTE', mth('SINE', mth('MULTIPLY', mth('ADD', u, v), 30.0)))
    d2 = mth('ABSOLUTE', mth('SINE', mth('MULTIPLY', mth('SUBTRACT', u, v), 30.0)))
    lat = mth('LESS_THAN', mth('MINIMUM', d1, d2), 0.06)
    rr = mth('SQRT', mth('ADD', mth('MULTIPLY', u, u), mth('MULTIPLY', v, v)))
    med = mth('LESS_THAN', rr, 0.09); medring = mth('LESS_THAN', mth('ABSOLUTE', mth('SUBTRACT', rr, 0.105)), 0.008)
    wv = nt.nodes.new("ShaderNodeTexWave"); wv.inputs["Scale"].default_value = 60; wv.wave_type = 'RINGS'; nt.links.new(tc.outputs["Generated"], wv.inputs["Vector"])
    c0 = nt.nodes.new("ShaderNodeMix"); c0.data_type = 'RGBA'; c0.inputs["A"].default_value = (0.20, 0.004, 0.010, 1); c0.inputs["B"].default_value = (0.75, 0.42, 0.05, 1)
    nt.links.new(lat, c0.inputs["Factor"])
    cm_ = nt.nodes.new("ShaderNodeMix"); cm_.data_type = 'RGBA'; cm_.inputs["B"].default_value = (0.03, 0.06, 0.30, 1)
    nt.links.new(c0.outputs["Result"], cm_.inputs["A"]); nt.links.new(med, cm_.inputs["Factor"])
    c = nt.nodes.new("ShaderNodeMix"); c.data_type = 'RGBA'; c.inputs["B"].default_value = (0.75, 0.42, 0.05, 1)
    nt.links.new(cm_.outputs["Result"], c.inputs["A"]); nt.links.new(medring, c.inputs["Factor"])
    c2 = nt.nodes.new("ShaderNodeMix"); c2.data_type = 'RGBA'; c2.inputs["B"].default_value = (0.02, 0.05, 0.25, 1)
    nt.links.new(c.outputs["Result"], c2.inputs["A"]); nt.links.new(border, c2.inputs["Factor"])
    c3 = nt.nodes.new("ShaderNodeMix"); c3.data_type = 'RGBA'; c3.inputs["B"].default_value = (0.85, 0.55, 0.08, 1)
    nt.links.new(c2.outputs["Result"], c3.inputs["A"]); nt.links.new(inner, c3.inputs["Factor"])
    nt.links.new(c3.outputs["Result"], p.inputs["Base Color"])
    bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.25; nt.links.new(wv.outputs["Fac"], bp.inputs["Height"]); nt.links.new(bp.outputs["Normal"], p.inputs["Normal"])
    return m

M_WALL = wallpaper("M_Wallpaper", (0.012, 0.20, 0.22), (0.05, 0.36, 0.34), (0.55, 0.38, 0.06))
M_WAIN = wood("M_Wainscot", (0.09, 0.025, 0.010), (0.16, 0.05, 0.02), scale=2.0, rough=0.35)
M_FLOOR = wood("M_Floor", (0.22, 0.07, 0.02), (0.36, 0.13, 0.04), scale=2.0, planks=True)
M_CEIL = plaster("M_Ceiling", (0.80, 0.74, 0.62), (0.86, 0.80, 0.68))
M_TRIM = mat("M_Trim", (0.85, 0.80, 0.68), rough=0.4, coat=0.2)
M_MAHOG = wood("M_Mahogany", (0.10, 0.025, 0.012), (0.20, 0.06, 0.025), scale=4.0, rough=0.3)
M_VELVET = velvet("M_Velvet", (0.13, 0.012, 0.20))
M_RUG = rug_mat("M_Rug")
M_CURTAIN = velvet("M_Curtain", (0.40, 0.012, 0.02), (1, 0.6, 0.6))
M_BRASS = mat("M_Brass", (0.95, 0.62, 0.20), rough=0.25, metal=1.0)
M_GOLD = mat("M_GoldTassel", (0.9, 0.6, 0.1), rough=0.5, sheen=0.5)

# ================================================================== room shell
BACK_Y = 0.80
def slab(name, size, loc, m, bev=0.0):
    return box(name, size, loc, m, bevel=bev)
FLOOR = slab("PL_Floor", (7.0, 7.0, 0.05), (0, -1.5, -0.025), M_FLOOR)
CEIL = slab("PL_Ceiling", (7.0, 7.0, 0.05), (0, -1.5, 2.85), M_CEIL)
WIN_X = (-1.75, -0.85); WIN_Z = (0.80, 2.30)
def wall_with_hole(name, y0, y1, xr, zr, hx, hz, m):
    parts = []
    for nm, x0, x1, z0, z1 in (("L", xr[0], hx[0], zr[0], zr[1]), ("R", hx[1], xr[1], zr[0], zr[1]),
                               ("T", hx[0], hx[1], hz[1], zr[1]), ("B", hx[0], hx[1], zr[0], hz[0])):
        if x1 - x0 > 1e-4 and z1 - z0 > 1e-4:
            parts.append(slab(name + nm, (x1 - x0, y1 - y0, z1 - z0), ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), m))
    bpy.ops.object.select_all(action='DESELECT')
    for p in parts: p.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]; bpy.ops.object.join(); o = bpy.context.active_object; o.name = name; return o
BACK = wall_with_hole("PL_BackWall", BACK_Y, BACK_Y + 0.12, (-3.5, 3.5), (0, 2.85), WIN_X, WIN_Z, M_WALL)
SIDE_L = slab("PL_SideL", (0.12, 7.0, 2.85), (-3.2, -1.5, 1.425), M_WALL)
SIDE_R = slab("PL_SideR", (0.12, 7.0, 2.85), (3.2, -1.5, 1.425), M_WALL)
# wainscot panels + dado rail on the back wall (left and right of the window), skirting, cornice
for nm, x0, x1 in (("A", -3.4, WIN_X[0]), ("B", WIN_X[0], WIN_X[1]), ("C", WIN_X[1], 3.4)):
    zt = 0.78 if nm == "B" else 0.88
    slab("PL_Wainscot" + nm, (x1 - x0, 0.02, zt), ((x0 + x1) / 2, BACK_Y - 0.01, zt / 2), M_WAIN)
    slab("PL_Dado" + nm, (x1 - x0, 0.04, 0.035), ((x0 + x1) / 2, BACK_Y - 0.025, zt + 0.015), M_MAHOG, bev=0.006)
slab("PL_Cornice", (7.0, 0.08, 0.10), (0, BACK_Y - 0.04, 2.80), M_TRIM, bev=0.01)
for sx in (-1, 1):
    slab("PL_WainSide%d" % sx, (0.02, 7.0, 0.88), (sx * 3.13, -1.5, 0.44), M_WAIN)
# the rug in front of the settee
RUG = slab("PL_Rug", (2.6, 1.9, 0.008), (0.0, -0.75, 0.004), M_RUG, bev=0.003)

# ---- the window: sash frame with 6 panes, curtains, and the garden backdrop outside
M_GLASS = bpy.data.materials.new("M_WinGlass"); M_GLASS.use_nodes = True
nt = M_GLASS.node_tree
for n in list(nt.nodes):
    if n.type != 'OUTPUT_MATERIAL': nt.nodes.remove(n)
tr = nt.nodes.new("ShaderNodeBsdfTransparent"); gl = nt.nodes.new("ShaderNodeBsdfGlossy"); gl.inputs["Roughness"].default_value = 0.03
fr = nt.nodes.new("ShaderNodeFresnel"); mxs = nt.nodes.new("ShaderNodeMixShader")
nt.links.new(fr.outputs[0], mxs.inputs[0]); nt.links.new(tr.outputs[0], mxs.inputs[1]); nt.links.new(gl.outputs[0], mxs.inputs[2])
nt.links.new(mxs.outputs[0], nt.nodes["Material Output"].inputs["Surface"])
wx0, wx1 = WIN_X; wz0, wz1 = WIN_Z; wy = BACK_Y + 0.06
parts = []
for nm, sz, lc in (("l", (0.07, 0.08, wz1 - wz0), (wx0 + 0.035, wy, (wz0 + wz1) / 2)), ("r", (0.07, 0.08, wz1 - wz0), (wx1 - 0.035, wy, (wz0 + wz1) / 2)),
                   ("t", (wx1 - wx0, 0.08, 0.07), ((wx0 + wx1) / 2, wy, wz1 - 0.035)), ("b", (wx1 - wx0, 0.08, 0.07), ((wx0 + wx1) / 2, wy, wz0 + 0.035)),
                   ("m", (wx1 - wx0, 0.06, 0.05), ((wx0 + wx1) / 2, wy, (wz0 + wz1) / 2)),
                   ("v", (0.03, 0.04, wz1 - wz0), ((wx0 + wx1) / 2, wy, (wz0 + wz1) / 2)),
                   ("h1", (wx1 - wx0, 0.04, 0.03), ((wx0 + wx1) / 2, wy, wz0 + (wz1 - wz0) * 0.25)),
                   ("h2", (wx1 - wx0, 0.04, 0.03), ((wx0 + wx1) / 2, wy, wz0 + (wz1 - wz0) * 0.75))):
    parts.append(slab("PL_Sash_" + nm, sz, lc, M_TRIM, bev=0.004))
bpy.ops.object.select_all(action='DESELECT')
for p in parts: p.select_set(True)
bpy.context.view_layer.objects.active = parts[0]; bpy.ops.object.join(); bpy.context.active_object.name = "PL_Sash"
bpy.ops.mesh.primitive_plane_add(size=1, location=((wx0 + wx1) / 2, wy + 0.01, (wz0 + wz1) / 2), rotation=(math.radians(90), 0, 0))
g_ = bpy.context.active_object; g_.name = "PL_WinGlass"; g_.scale = (wx1 - wx0, wz1 - wz0, 1); g_.data.materials.append(M_GLASS)
slab("PL_Sill", (wx1 - wx0 + 0.16, 0.16, 0.04), ((wx0 + wx1) / 2, BACK_Y - 0.03, wz0 - 0.02), M_TRIM, bev=0.006)
# curtains: gathered velvet panels (wavy planes, solidified) tied back either side of the window
def curtain(name, x_c, width, flip):
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=48, y_subdivisions=12, size=1)
    o = bpy.context.active_object; o.name = name
    for v in o.data.vertices:
        u = v.co.x + 0.5; h = v.co.y + 0.5          # u across, h up (0 bottom .. 1 top)
        pinch = 1.0 - 0.55 * math.exp(-((h - 0.42) / 0.10) ** 2)      # tie-back at 42 % height
        x = x_c + flip * (u - 0.5) * width * pinch
        y = BACK_Y - 0.10 + 0.035 * math.sin(u * math.pi * 9) * (0.5 + 0.5 * pinch)
        z = 0.02 + h * 2.62
        v.co = Vector((x, y, z))
    o.data.materials.append(M_CURTAIN)
    for p in o.data.polygons: p.use_smooth = True
    so = o.modifiers.new("solid", 'SOLIDIFY'); so.thickness = 0.012
    sd = o.modifiers.new("subd", 'SUBSURF'); sd.levels = 1; sd.render_levels = 1
    return o
curtain("PL_CurtainL", wx0 - 0.22, 0.48, 1); curtain("PL_CurtainR", wx1 + 0.22, 0.48, -1)
cyl("PL_CurtainRod", 0.018, (wx1 - wx0) + 1.1, ((wx0 + wx1) / 2, BACK_Y - 0.12, 2.66), M_BRASS, rot=(0, math.radians(90), 0))
for sx in (wx0 - 0.22, wx1 + 0.22):
    bpy.ops.mesh.primitive_torus_add(major_radius=0.06, minor_radius=0.012, location=(sx, BACK_Y - 0.10, 1.12), rotation=(math.radians(90), 0, 0))
    bpy.context.active_object.name = "PL_TieBack"; bpy.context.active_object.data.materials.append(M_GOLD)

# garden backdrop outside the window: sky gradient + trees + lawn, its season / daylight are 3 keyed values
def garden_mat():
    m = bpy.data.materials.new("M_Garden"); m.use_nodes = True; nt = m.node_tree
    for n in list(nt.nodes):
        if n.type != 'OUTPUT_MATERIAL': nt.nodes.remove(n)
    tc = nt.nodes.new("ShaderNodeTexCoord"); sep = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(tc.outputs["Generated"], sep.inputs[0])
    vS = nt.nodes.new("ShaderNodeValue"); vS.name = "Season"      # 0 summer green, 1 autumn orange, 2 winter snow, 3 spring green
    vD = nt.nodes.new("ShaderNodeValue"); vD.name = "Daylight"    # 1 day, 0 night
    # sky
    sky = nt.nodes.new("ShaderNodeValToRGB"); sky.color_ramp.elements[0].color = (0.25, 0.55, 0.95, 1); sky.color_ramp.elements[1].color = (0.65, 0.85, 1.0, 1)
    inv = nt.nodes.new("ShaderNodeMath"); inv.operation = 'SUBTRACT'; inv.inputs[0].default_value = 1.0; nt.links.new(sep.outputs["Y"], inv.inputs[1])
    nt.links.new(inv.outputs[0], sky.inputs["Fac"])
    # tree crowns: noise blobs above a lawn line
    nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 5.0; nz.inputs["Detail"].default_value = 8.0; nt.links.new(tc.outputs["Generated"], nz.inputs["Vector"])
    hl = nt.nodes.new("ShaderNodeMath"); hl.operation = 'MULTIPLY_ADD'; nt.links.new(nz.outputs["Fac"], hl.inputs[0]); hl.inputs[1].default_value = 0.55; hl.inputs[2].default_value = 0.20
    tree = nt.nodes.new("ShaderNodeMath"); tree.operation = 'LESS_THAN'; nt.links.new(sep.outputs["Y"], tree.inputs[0]); nt.links.new(hl.outputs[0], tree.inputs[1])
    lawn = nt.nodes.new("ShaderNodeMath"); lawn.operation = 'LESS_THAN'; lawn.inputs[1].default_value = 0.22; nt.links.new(sep.outputs["Y"], lawn.inputs[0])
    # season colours for leaves and lawn: ramp over Season/3
    s3 = nt.nodes.new("ShaderNodeMath"); s3.operation = 'DIVIDE'; s3.inputs[1].default_value = 3.0; nt.links.new(vS.outputs[0], s3.inputs[0])
    leaf = nt.nodes.new("ShaderNodeValToRGB"); cr = leaf.color_ramp
    cr.elements[0].position = 0.0; cr.elements[0].color = (0.05, 0.40, 0.04, 1)
    cr.elements[1].position = 1.0; cr.elements[1].color = (0.18, 0.60, 0.10, 1)
    for pos, c in ((0.333, (0.95, 0.35, 0.02, 1)), (0.667, (0.92, 0.95, 1.0, 1))): e = cr.elements.new(pos); e.color = c
    nt.links.new(s3.outputs[0], leaf.inputs["Fac"])
    shade = nt.nodes.new("ShaderNodeMix"); shade.data_type = 'RGBA'; shade.blend_type = 'MULTIPLY'
    nt.links.new(nz.outputs["Fac"], shade.inputs["Factor"]); nt.links.new(leaf.outputs["Color"], shade.inputs["A"]); shade.inputs["B"].default_value = (0.55, 0.55, 0.55, 1)
    m1 = nt.nodes.new("ShaderNodeMix"); m1.data_type = 'RGBA'; nt.links.new(tree.outputs[0], m1.inputs["Factor"])
    nt.links.new(sky.outputs["Color"], m1.inputs["A"]); nt.links.new(shade.outputs["Result"], m1.inputs["B"])
    m2 = nt.nodes.new("ShaderNodeMix"); m2.data_type = 'RGBA'; nt.links.new(lawn.outputs[0], m2.inputs["Factor"])
    nt.links.new(m1.outputs["Result"], m2.inputs["A"]); nt.links.new(leaf.outputs["Color"], m2.inputs["B"])
    # night: deep blue-purple, moonlit
    nite = nt.nodes.new("ShaderNodeMix"); nite.data_type = 'RGBA'; nite.blend_type = 'MULTIPLY'
    nt.links.new(m2.outputs["Result"], nite.inputs["A"]); nite.inputs["B"].default_value = (0.10, 0.10, 0.35, 1)
    one_m = nt.nodes.new("ShaderNodeMath"); one_m.operation = 'SUBTRACT'; one_m.inputs[0].default_value = 1.0; nt.links.new(vD.outputs[0], one_m.inputs[1])
    nt.links.new(one_m.outputs[0], nite.inputs["Factor"])
    em = nt.nodes.new("ShaderNodeEmission"); nt.links.new(nite.outputs["Result"], em.inputs["Color"])
    st = nt.nodes.new("ShaderNodeMath"); st.operation = 'MULTIPLY_ADD'; nt.links.new(vD.outputs[0], st.inputs[0]); st.inputs[1].default_value = 1.6; st.inputs[2].default_value = 0.6
    nt.links.new(st.outputs[0], em.inputs["Strength"])
    nt.links.new(em.outputs[0], nt.nodes["Material Output"].inputs["Surface"])
    vS.outputs[0].default_value = 0.0; vD.outputs[0].default_value = 1.0
    return m
bpy.ops.mesh.primitive_plane_add(size=1, location=((wx0 + wx1) / 2, BACK_Y + 2.4, 1.55), rotation=(math.radians(90), 0, 0))
GARD = bpy.context.active_object; GARD.name = "PL_Garden"; GARD.scale = (6.0, 4.0, 1); bpy.ops.object.transform_apply(scale=True)
GARD.data.materials.append(garden_mat())
GARD.visible_diffuse = False; GARD.visible_glossy = False; GARD.visible_shadow = False

# ================================================================== the settee (procedural Victorian camel-back, exact seat surface)
SEAT_Z = 0.44; SEAT_FRONT = -0.30; SEAT_BACK = 0.24; SW = 1.62
st_parts = []
st_parts.append(slab("PL_SetteeSeat", (SW - 0.20, SEAT_BACK - SEAT_FRONT, 0.13), (0, (SEAT_FRONT + SEAT_BACK) / 2, SEAT_Z - 0.065), M_VELVET, bev=0.035))
st_parts.append(slab("PL_SetteeBack", (SW - 0.10, 0.16, 0.52), (0, SEAT_BACK + 0.06, SEAT_Z + 0.24), M_VELVET, bev=0.05))
for sx in (-1, 1):
    st_parts.append(slab("PL_SetteeArm%d" % sx, (0.13, SEAT_BACK - SEAT_FRONT + 0.08, 0.24), (sx * (SW / 2 - 0.065), (SEAT_FRONT + SEAT_BACK) / 2 + 0.02, SEAT_Z + 0.07), M_VELVET, bev=0.04))
for o in st_parts:
    pass
SET_RAIL = slab("PL_SetteeRail", (SW, SEAT_BACK - SEAT_FRONT + 0.02, 0.10), (0, (SEAT_FRONT + SEAT_BACK) / 2 + 0.07, SEAT_Z - 0.18), M_MAHOG, bev=0.015)   # set back under the seat (calves clear)
SET_CREST = slab("PL_SetteeCrest", (SW - 0.05, 0.06, 0.05), (0, SEAT_BACK + 0.11, SEAT_Z + 0.52), M_MAHOG, bev=0.015)
for i, (sx, sy) in enumerate(((-1, -1), (1, -1), (-1, 1), (1, 1))):
    x = sx * (SW / 2 - 0.07); y = (SEAT_FRONT + 0.05) if sy < 0 else (SEAT_BACK + 0.10)
    bpy.ops.mesh.primitive_cone_add(vertices=24, radius1=0.022, radius2=0.035, depth=0.21, location=(x, y, 0.105))
    o = bpy.context.active_object; o.name = "PL_SetteeLeg%d" % i; o.data.materials.append(M_MAHOG); bpy.ops.object.shade_smooth()
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.03, location=(x, y, 0.03)); o2 = bpy.context.active_object; o2.name = "PL_SetteeFoot%d" % i
    o2.data.materials.append(M_BRASS); bpy.ops.object.shade_smooth()
# tufting buttons on the back cushion
for i in range(7):
    for j in range(2):
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.011, location=(-0.66 + i * 0.22 + (0.11 if j else 0), SEAT_BACK - 0.02 - 0.0, SEAT_Z + 0.18 + j * 0.16))
        o = bpy.context.active_object; o.name = "PL_Tuft"; o.data.materials.append(M_VELVET); o.scale = (1, 0.5, 1)

# ================================================================== Poly Haven dressing (CC0)
def append_ph(asset, name, loc, rot_z=0.0, scale=1.0, keep=None):
    d = os.path.join(PH, asset); blend = [f for f in os.listdir(d) if f.endswith(".blend")][0]
    with bpy.data.libraries.load(os.path.join(d, blend), link=False) as (src, dst):
        dst.objects = list(src.objects)
    objs = [o for o in dst.objects if o is not None and o.type == 'MESH' and (keep is None or keep(o.name))]
    root = bpy.data.objects.new(name, None); sc.collection.objects.link(root)
    for o in objs:
        sc.collection.objects.link(o)
        if o.parent is None or o.parent not in objs: o.parent = root
    root.location = loc; root.rotation_euler.z = rot_z; root.scale = (scale,) * 3
    for o in objs:
        for m in o.data.materials:
            if not m or not m.use_nodes: continue
            for n in m.node_tree.nodes:
                if n.type == 'BSDF_PRINCIPLED' and not n.inputs["Roughness"].is_linked:
                    n.inputs["Roughness"].default_value = max(0.3, n.inputs["Roughness"].default_value)
                if n.type == 'NORMAL_MAP': n.inputs["Strength"].default_value = 0.5
    return root, objs
CLOCK, CLOCK_P = append_ph("vintage_grandfather_clock_01", "PL_Clock", (1.55, BACK_Y - 0.48, 0.0), rot_z=0.0, keep=lambda n: not n.startswith("wdg"))
TABLE, _ = append_ph("side_table_01", "PL_SideTable", (1.12, -0.02, 0.0))
LAMP, LAMP_P = append_ph("vintage_oil_lamp", "PL_OilLamp", (1.12, -0.02, 0.548), scale=0.75)
PLANT, _ = append_ph("potted_plant_02", "PL_Plant", (-2.35, BACK_Y - 0.45, 0.1), scale=1.3)
CAB, _ = append_ph("vintage_cabinet_01", "PL_Cabinet", (2.35, BACK_Y - 0.33, 0.341), rot_z=0.0, scale=0.85)
FRAME, FRAME_P = append_ph("fancy_picture_frame_01", "PL_Sampler", (0.15, BACK_Y - 0.003, 1.62), rot_z=0.0, scale=1.0)
log_lines = []
for o in CLOCK_P: log_lines.append("clock part " + o.name)
# the framed sampler: the DA KRAS FILMS logo on cream linen (the brand, readable, sits naturally in the room)
canvas = [o for o in FRAME_P if "canvas" in o.name][0]
im = bpy.data.images.load(BRAND); im.name = "DaKrasFilms_logo_dark"
cm = bpy.data.materials.new("M_SamplerLogo"); cm.use_nodes = True; nt = cm.node_tree; p = nt.nodes["Principled BSDF"]
ti = nt.nodes.new("ShaderNodeTexImage"); ti.image = im; ti.extension = 'CLIP'
uv = nt.nodes.new("ShaderNodeTexCoord"); mp = nt.nodes.new("ShaderNodeMapping")
nt.links.new(uv.outputs["UV"], mp.inputs["Vector"]); nt.links.new(mp.outputs["Vector"], ti.inputs["Vector"])
mp.inputs["Scale"].default_value = (1.176, 2.128, 1); mp.inputs["Location"].default_value = (-0.088, -0.564, 0)
mix = nt.nodes.new("ShaderNodeMix"); mix.data_type = 'RGBA'; mix.inputs["A"].default_value = (0.86, 0.78, 0.60, 1)
nt.links.new(ti.outputs["Alpha"], mix.inputs["Factor"]); nt.links.new(ti.outputs["Color"], mix.inputs["B"])
nt.links.new(mix.outputs["Result"], p.inputs["Base Color"]); p.inputs["Roughness"].default_value = 0.85; p.inputs["Sheen Weight"].default_value = 0.4
canvas.data.materials.clear(); canvas.data.materials.append(cm)
print("LOGO image size", im.size[:], "canvas uv layers", [u.name for u in canvas.data.uv_layers])

# oil-lamp flame light (keyed in 02) + its flame glow
for o in LAMP_P:
    if "flame" in o.name:
        for m in o.data.materials:
            pr = [n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED']
            if pr:
                pr[0].inputs["Emission Color"].default_value = (1.0, 0.55, 0.15, 1); pr[0].inputs["Emission Strength"].default_value = 8.0
LL = bpy.data.lights.new("LampLight", 'POINT'); LL.energy = 0.0; LL.color = (1.0, 0.62, 0.28); LL.shadow_soft_size = 0.05
LLO = bpy.data.objects.new("LampLight", LL); sc.collection.objects.link(LLO); LLO.location = (1.12, -0.02, 0.548 + 0.45)

# ================================================================== lights (all keyed in 02: the dim 'trapped' beat, the time-lapse)
def area(name, loc, rot, size, energy, color):
    L = bpy.data.lights.new(name, 'AREA'); L.size = size; L.energy = energy; L.color = color
    o = bpy.data.objects.new(name, L); sc.collection.objects.link(o); o.location = loc; o.rotation_euler = [math.radians(r) for r in rot]
    o.visible_camera = False; return o
SUNL = bpy.data.lights.new("Sun", 'SUN'); SUNL.energy = 2.2; SUNL.color = (1.0, 0.88, 0.70); SUNL.angle = math.radians(3)
SUN = bpy.data.objects.new("Sun", SUNL); sc.collection.objects.link(SUN); SUN.rotation_euler = (math.radians(58), 0, math.radians(200))
area("WinFill", ((wx0 + wx1) / 2, BACK_Y - 0.2, 1.6), (-90, 0, 0), 1.2, 50.0, (0.80, 0.90, 1.0))
area("Key", (0.9, -1.9, 2.1), (55, 0, 28), 1.4, 110.0, (1.0, 0.90, 0.80))
area("Fill", (-1.8, -1.6, 1.4), (70, 0, -50), 1.6, 35.0, (0.85, 0.85, 1.0))
area("Rim", (0.4, 0.55, 2.4), (-35, 0, 180), 1.0, 35.0, (1.0, 0.85, 0.7))
w = bpy.data.worlds.new("World"); sc.world = w; w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (0.35, 0.30, 0.26, 1); w.node_tree.nodes["Background"].inputs[1].default_value = 0.35

# ================================================================== render settings (look)
sc.render.engine = 'CYCLES'
sc.cycles.samples = 64; sc.cycles.use_adaptive_sampling = True; sc.cycles.adaptive_threshold = 0.04
sc.cycles.use_denoising = True; sc.cycles.denoiser = 'OPENIMAGEDENOISE'
sc.cycles.max_bounces = 6; sc.cycles.diffuse_bounces = 3; sc.cycles.glossy_bounces = 3; sc.cycles.transmission_bounces = 6
sc.cycles.transparent_max_bounces = 16; sc.cycles.caustics_reflective = False; sc.cycles.caustics_refractive = False
sc.render.use_persistent_data = True
sc.view_settings.view_transform = 'AgX'
try: sc.view_settings.look = 'AgX - Punchy'
except Exception: pass
sc.render.use_simplify = True; sc.render.simplify_subdivision_render = 2

print("\n".join(log_lines))
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("BUILD_DONE", OUT)
