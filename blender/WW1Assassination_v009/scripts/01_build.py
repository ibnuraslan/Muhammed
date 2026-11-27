"""WW1Assassination v009 stage A (from scratch): the cast in real MakeHuman garments, Sarajevo 1914 street set, two touring cars,
props, the DA KRAS FILMS cafe sign and the deep, punchy look.
blender -b --python 01_build.py -- <assets_dir> <logo_dark.png> <out.blend>
assets_dir holds car.glb, pistol.glb (Sketchfab CC-BY) and ph/ (Poly Haven CC0 textures + HDRI); see fetch_assets.sh.

World (metres, Z up):
  Quay road along +X (y -4..4), north pavement y 4..7.5 (kerb 0.15), buildings from y 7.5.
  Side street (wrong turn) runs north (+Y) between x -5..5 from the quay; the cafe is on its east corner (x 7.5.., y 7.5..).
  River side: parapet at y -4.6..-4.0, river below, far-bank houses at y -40."""
import bpy, bmesh, sys, os, math, random
from mathutils import Vector, Matrix
HERE = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(HERE, "lib.py")).read())
a = sys.argv[sys.argv.index("--") + 1:]
ASSETS, LOGO, OUT = os.path.abspath(a[0]), os.path.abspath(a[1]), os.path.abspath(a[2])
PH = os.path.join(ASSETS, "ph")
random.seed(14)
for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob, do_unlink=True)
sc.render.fps = 60
sc.frame_start, sc.frame_end = 1, 1826
sc.render.resolution_x, sc.render.resolution_y = 1080, 1920

def coll(name, parent=None):
    c = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if c.name not in (parent or sc.collection).children: (parent or sc.collection).children.link(c)
    return c
def to_coll(o, c):
    for uc in list(o.users_collection): uc.objects.unlink(o)
    c.objects.link(o)
    for ch in o.children: to_coll(ch, c)

# ================================================================== PEOPLE (MPFB2 + MakeHuman CC0 garments: one model per character)
DBS = "toigo_male_double-breasted_suit/toigo_male_double-breasted_suit.mhclo"; S3 = "toigo_male_suit_3/toigo_male_suit_3.mhclo"
FSU = "toigo_female_suit/toigo_female_suit.mhclo"; FS2 = "toigo_female_suit_2/toigo_female_suit_2.mhclo"
SKL = "toigo_long_full_skirt/toigo_long_full_skirt.mhclo"; TJ = "toigo_male_suit_tie_and_jacket/toigo_male_suit_tie_and_jacket.mhclo"
BOW = "toigo_suit_with_jacket_and_bowtie/toigo_suit_with_jacket_and_bowtie.mhclo"; WORK = "male_worksuit01/male_worksuit01.mhclo"
NEWS = "jujube_newsboy_cap/jujube_newsboy_cap.mhclo"; FED = "fedora01/fedora01.mhclo"; CLO = "aethelraed_unraed_cloche_hat/aethelraed_unraed_cloche_hat.mhclo"
CAU = {"asian": 0.03, "caucasian": 0.94, "african": 0.03}
# name: gender, age, hair, skin, brows, clothes, colours {garment key: rgb}, hair tint, extra
CAST = {
  # the Archduke: pale-blue general's tunic (double-breasted, real loose jacket + trousers), plumed helmet (modelled, on the head bone)
  "Archduke": (1.0, 0.62, "short02/short02.mhclo", "middleage_caucasian_male/middleage_caucasian_male.mhmat", "eyebrow004/eyebrow004.mhclo",
               [DBS], {"double-breasted": (0.42, 0.62, 0.92)}, (0.22, 0.15, 0.10), dict(weight=0.62, muscle=0.45, height=0.55)),
  # the Duchess: white jacket and long full skirt, white cloche hat (real garment asset)
  "Duchess": (0.0, 0.55, "bob02/bob02.mhclo", "middleage_caucasian_female/middleage_caucasian_female.mhmat", "eyebrow010/eyebrow010.mhclo",
              [FSU, SKL, CLO], {"female_suit": (0.93, 0.92, 0.88), "long_full_skirt": (0.95, 0.94, 0.90), "cloche": (0.96, 0.95, 0.92)},
              (0.30, 0.18, 0.10), dict(weight=0.5, cup=0.35, height=0.45)),
  "Driver": (1.0, 0.42, "short01/short01.mhclo", "middleage_caucasian_male2/middleage_caucasian_male.mhmat", "eyebrow001/eyebrow001.mhclo",
             [WORK, NEWS], {"worksuit": (0.10, 0.12, 0.16), "newsboy": (0.08, 0.08, 0.10)}, (0.15, 0.10, 0.07), dict(weight=0.55)),
  "Driver2": (1.0, 0.5, "short03/short03.mhclo", "middleage_caucasian_male/middleage_caucasian_male.mhmat", "eyebrow004/eyebrow004.mhclo",
              [WORK, NEWS], {"worksuit": (0.30, 0.18, 0.08), "newsboy": (0.12, 0.10, 0.08)}, (0.12, 0.09, 0.06), dict(weight=0.6)),
  # the gunman: a 19-year-old in a dark charcoal suit, bare-headed
  "Gunman": (1.0, 0.24, "short04/short04.mhclo", "young_caucasian_male/young_caucasian_male.mhmat", "eyebrow001/eyebrow001.mhclo",
             [S3], {"suit_3": (0.10, 0.11, 0.14)}, (0.10, 0.07, 0.05), dict(weight=0.35, muscle=0.35, height=0.45)),
  # the bomb thrower: brown suit, newsboy cap
  "Bomber": (1.0, 0.27, "short01/short01.mhclo", "young_caucasian_male2/young_caucasian_male.mhmat", "eyebrow007/eyebrow007.mhclo",
             [TJ, NEWS], {"tie_and_jacket": (0.40, 0.20, 0.08), "newsboy": (0.20, 0.16, 0.10)}, (0.14, 0.09, 0.06), dict(weight=0.4)),
  # the two who lost their nerve
  "Nerve1": (1.0, 0.33, "short03/short03.mhclo", "young_caucasian_male/young_caucasian_male.mhmat", "eyebrow004/eyebrow004.mhclo",
             [S3, FED], {"suit_3": (0.04, 0.26, 0.16), "fedora": (0.10, 0.08, 0.06)}, (0.12, 0.08, 0.05), dict(weight=0.45)),
  "Nerve2": (1.0, 0.22, "short02/short02.mhclo", "young_caucasian_male2/young_caucasian_male.mhmat", "eyebrow001/eyebrow001.mhclo",
             [BOW, NEWS], {"bowtie": (0.06, 0.10, 0.36), "newsboy": (0.30, 0.30, 0.32)}, (0.30, 0.16, 0.07), dict(weight=0.35)),
  # crowd on the quay
  "Q1": (0.0, 0.35, "ponytail01/ponytail01.mhclo", "young_caucasian_female/young_caucasian_female.mhmat", "eyebrow010/eyebrow010.mhclo",
         [FS2, SKL, CLO], {"female_suit_2": (0.62, 0.05, 0.18), "long_full_skirt": (0.18, 0.04, 0.30), "cloche": (0.70, 0.08, 0.20)}, (0.35, 0.18, 0.08), dict(cup=0.3)),
  "Q2": (1.0, 0.55, "short02/short02.mhclo", "middleage_caucasian_male/middleage_caucasian_male.mhmat", "eyebrow004/eyebrow004.mhclo",
         [DBS, FED], {"double-breasted": (0.30, 0.14, 0.06), "fedora": (0.06, 0.06, 0.07)}, (0.20, 0.15, 0.12), dict(weight=0.7)),
  "Q3": (0.0, 0.48, "bob01/bob01.mhclo", "middleage_caucasian_female/middleage_caucasian_female.mhmat", "eyebrow010/eyebrow010.mhclo",
         [FSU, SKL], {"female_suit": (0.02, 0.40, 0.42), "long_full_skirt": (0.03, 0.22, 0.30)}, (0.12, 0.08, 0.06), dict(cup=0.35)),
  "Q4": (1.0, 0.75, "short01/short01.mhclo", "old_caucasian_male/old_caucasian_male.mhmat", "eyebrow001/eyebrow001.mhclo",
         [TJ, FED], {"tie_and_jacket": (0.24, 0.24, 0.28), "fedora": (0.20, 0.10, 0.05)}, (0.55, 0.53, 0.50), dict(weight=0.55)),
  "Q5": (0.0, 0.28, "long01/long01.mhclo", "young_caucasian_female2/young_caucasian_female.mhmat", "eyebrow010/eyebrow010.mhclo",
         [FS2, SKL], {"female_suit_2": (0.85, 0.55, 0.05), "long_full_skirt": (0.40, 0.18, 0.05)}, (0.45, 0.25, 0.08), dict(cup=0.3)),
  "Q6": (1.0, 0.4, "short04/short04.mhclo", "middleage_caucasian_male2/middleage_caucasian_male.mhmat", "eyebrow007/eyebrow007.mhclo",
         [BOW, NEWS], {"bowtie": (0.45, 0.05, 0.05), "newsboy": (0.10, 0.10, 0.12)}, (0.10, 0.07, 0.05), dict(weight=0.5)),
  # crowd at the corner by the cafe
  "C1": (0.0, 0.4, "braid01/braid01.mhclo", "young_caucasian_female/young_caucasian_female.mhmat", "eyebrow010/eyebrow010.mhclo",
         [FSU, SKL, CLO], {"female_suit": (0.10, 0.30, 0.70), "long_full_skirt": (0.05, 0.12, 0.40), "cloche": (0.95, 0.85, 0.30)}, (0.25, 0.13, 0.06), dict(cup=0.3)),
  "C2": (1.0, 0.6, "short03/short03.mhclo", "middleage_caucasian_male/middleage_caucasian_male.mhmat", "eyebrow004/eyebrow004.mhclo",
         [S3, FED], {"suit_3": (0.35, 0.28, 0.12), "fedora": (0.08, 0.08, 0.08)}, (0.30, 0.25, 0.20), dict(weight=0.65)),
  "C3": (0.0, 0.62, "bob02/bob02.mhclo", "old_caucasian_female/old_caucasian_female.mhmat", "eyebrow010/eyebrow010.mhclo",
         [FS2, SKL], {"female_suit_2": (0.40, 0.06, 0.40), "long_full_skirt": (0.20, 0.05, 0.22)}, (0.50, 0.48, 0.45), dict(cup=0.4)),
}
SUBDIV = {k: (1 if k in ("Archduke", "Duchess", "Gunman", "Bomber", "Driver", "Nerve1", "Nerve2") else 0) for k in CAST}
PEOPLE = {}
for nm, (g, age, hair, skin, brow, clothes, cols, htint, kw) in CAST.items():
    skin_path = skin.replace("middleage_caucasian_male2/middleage_caucasian_male", "middleage_caucasian_male/middleage_caucasian_male")
    skin_path = skin_path.replace("young_caucasian_male2/young_caucasian_male", "young_caucasian_male2/young_caucasian_male2")
    skin_path = skin_path.replace("young_caucasian_female2/young_caucasian_female", "young_caucasian_female2/young_caucasian_female2")
    rig, body = human(nm, g, age, CAU, hair, skin_path, brow, clothes=clothes, shoes="shoes02/shoes02.mhclo", subdiv=SUBDIV[nm], **kw)
    bake_keys(body); eye_fix(rig)
    PEOPLE[nm] = (rig, body)
    for m in body.data.materials: tint(m, (1.0, 0.90, 0.84))
    for c in rig.children:
        if c.type != 'MESH' or c == body: continue
        for key, rgb in cols.items():
            if key in c.name: colorize(c, rgb); c["garment"] = 1
        if hair.split("/")[0] in c.name or "eyebrow" in c.name:
            for m in c.data.materials: tint(m, htint)
    print("PERSON", nm, [c.name for c in rig.children])
# EnhancedEye cornea fix in every eye node group (LESSONS 3)
for g in [g for g in bpy.data.node_groups if g.name.startswith("EnhancedEye")]:
    P = next((n for n in g.nodes if n.type == "BSDF_PRINCIPLED"), None); OUTN = next((n for n in g.nodes if n.type == "GROUP_OUTPUT"), None)
    if P is None or OUTN is None or "CorneaTransparentMix" in g.nodes: continue
    tl = [l for l in g.links if l.to_node == P and l.to_socket.name == "Transmission Weight"]
    src = tl[0].from_socket if tl else None
    for l in tl: g.links.remove(l)
    P.inputs["Transmission Weight"].default_value = 0.0
    ols = [l for l in g.links if l.from_node == P and l.to_node == OUTN]
    if not ols: continue
    out_sock = ols[0].to_socket; g.links.remove(ols[0])
    tr = g.nodes.new("ShaderNodeBsdfTransparent"); mx = g.nodes.new("ShaderNodeMixShader"); mx.name = "CorneaTransparentMix"
    if src: g.links.new(src, mx.inputs[0])
    else: mx.inputs[0].default_value = 0.0
    g.links.new(P.outputs[0], mx.inputs[1]); g.links.new(tr.outputs[0], mx.inputs[2]); g.links.new(mx.outputs[0], out_sock)

# body skin under each garment is masked (solid look, no skin poking through); hats/caps don't mask
for nm, (rig, body) in PEOPLE.items():
    for c in rig.children:
        if c.type == 'MESH' and c.get("garment") and not any(k in c.name for k in ("newsboy", "fedora", "cloche")):
            hide_by_proximity(body, c, "Hide." + c.name, dist=0.02, rings=3)
    # skirt over suit trousers: the trouser legs under the long skirt are masked (no trouser hem below the skirt)
    sk = next((c for c in rig.children if "long_full_skirt" in c.name), None)
    if sk:
        for c in rig.children:
            if c.type == 'MESH' and ("female_suit" in c.name):
                zt = max(v.co.z for v in sk.data.vertices) - 0.06
                vg = c.vertex_groups.new(name="under_skirt"); vg.add([v.index for v in c.data.vertices if v.co.z < zt], 1.0, 'REPLACE')
                mk = c.modifiers.new("under_skirt", 'MASK'); mk.vertex_group = "under_skirt"; mk.invert_vertex_group = True
    # thick, closed cloth: every garment gets a little solidify so no edge reads as a paper shell
    for c in rig.children:
        if c.type == 'MESH' and c.get("garment") and "Solid" not in c.modifiers:
            so = c.modifiers.new("Solid", 'SOLIDIFY'); so.thickness = 0.004; so.offset = -1.0; so.use_rim = True

# the seated Duchess: the long skirt hem below the knees is masked (it would fold through the car door; it is inside the car)
DR_, DB_ = PEOPLE["Duchess"]
skd = next(c for c in DR_.children if "long_full_skirt" in c.name)
kz = DR_.data.bones["lowerleg01.L"].head_local.z + 0.06
vg = skd.vertex_groups.new(name="hem_hide"); vg.add([v.index for v in skd.data.vertices if v.co.z < kz], 1.0, 'REPLACE')
mk = skd.modifiers.new("hem_hide", 'MASK'); mk.vertex_group = "hem_hide"; mk.invert_vertex_group = True
# ---- the Archduke's plumed helmet: dark crown + gold band + peak + emerald-green feather plume, bound to the head bone
AR, AB = PEOPLE["Archduke"]
def head_frame(rig):
    hb = rig.data.bones["head"]; return hb.head_local.copy(), hb.matrix_local.copy()
hh, HM = head_frame(AR)
eye_z = AR.data.bones["eye.L"].head_local.z
crown_m = mat("M_HelmetCrown", (0.03, 0.035, 0.04), rough=0.3, coat=0.6)
band_m = mat("M_HelmetGold", (0.95, 0.62, 0.12), rough=0.25, metal=0.9)
plume_m = mat("M_Plume", (0.02, 0.55, 0.16), rough=0.55, sheen=0.6)
# fit the crown on the skull: raycast the head mesh for the circumference at brow height
skull = [AB.matrix_world @ v.co for v in AB.data.vertices if v.co.z > eye_z + 0.035]
cx = sum(p.x for p in skull) / len(skull); cy = sum(p.y for p in skull) / len(skull)
zb = eye_z + 0.045
ring_pts = [p for p in skull if abs(p.z - zb) < 0.012]
rx = max(abs(p.x - cx) for p in ring_pts) + 0.007; ry = max(abs(p.y - cy) for p in ring_pts) + 0.007
bm = bmesh.new()
segs = 40; rows = [(zb - 0.004, 1.00), (zb + 0.03, 1.0), (zb + 0.06, 0.96), (zb + 0.08, 0.86)]
rings = []
for z, k in rows:
    rings.append([bm.verts.new((cx + rx * k * math.cos(2 * math.pi * i / segs), cy + ry * k * math.sin(2 * math.pi * i / segs), z)) for i in range(segs)])
for r0, r1 in zip(rings, rings[1:]):
    for i in range(segs):
        bm.faces.new((r0[i], r0[(i + 1) % segs], r1[(i + 1) % segs], r1[i]))
top = bm.faces.new(rings[-1]); bmesh.ops.triangulate(bm, faces=[top])
me = bpy.data.meshes.new("Helmet"); bm.to_mesh(me); bm.free()
HELM = bpy.data.objects.new("Archduke.helmet", me); sc.collection.objects.link(HELM); me.materials.append(crown_m)
so = HELM.modifiers.new("solid", 'SOLIDIFY'); so.thickness = 0.006; so.offset = 1.0
sd = HELM.modifiers.new("sub", 'SUBSURF'); sd.levels = 1; sd.render_levels = 2
for p in me.polygons: p.use_smooth = True
band = cyl("Archduke.helmetBand", 1.0, 0.018, (cx, cy, zb + 0.01), band_m, verts=40)
band.scale = (rx * 1.035, ry * 1.035, 1.0)
peak = sphere("Archduke.helmetPeak", 1.0, (cx, cy - ry * 0.95, zb - 0.002), crown_m)
peak.scale = (rx * 0.75, 0.05, 0.006)
# plume: ~70 drooping feather strands from a gold rosette on top
plume_objs = [HELM, band, peak]
rng = random.Random(3)
for i in range(48):     # a cascade of long feathers falling from the crown top over the sides and back (never over the face)
    ang = rng.uniform(-0.15 * math.pi, 1.15 * math.pi); L = rng.uniform(0.12, 0.17); r0 = rng.uniform(0.0, 0.015)
    out = Vector((math.cos(ang) * rx / ry, math.sin(ang), 0)).normalized()
    base = Vector((cx + r0 * out.x, cy + r0 * out.y, zb + 0.085))
    pts = [base, base + out * 0.05 + Vector((0, 0, 0.035)), base + out * (rx * 0.9 + 0.02) + Vector((0, 0, 0.01)),
           base + out * (rx * 1.05 + 0.03) + Vector((0, 0, -L * 0.55)), base + out * (rx * 1.1 + 0.035) + Vector((0, 0, -L * 0.75))]
    plume_objs.append(curve_tube("Archduke.plume%02d" % i, [tuple(p) for p in pts], 0.0032, plume_m, res=4))
ros = sphere("Archduke.rosette", 0.018, (cx, cy, zb + 0.085), band_m); plume_objs.append(ros)
for o in plume_objs:
    mw = o.matrix_world.copy(); o.parent = AR; o.parent_type = 'BONE'; o.parent_bone = "head"
    bpy.context.view_layer.update(); o.matrix_world = mw
# hair: cut every hair card above the helmet band so nothing pokes through the crown
hair_ar = part(AR, "short02")
cut_p0 = Vector((0, 0, zb + 0.004)); cut_n = Vector((0, 0, 1))
bm = bmesh.new(); bm.from_mesh(hair_ar.data)
kill = [v for v in bm.verts if (hair_ar.matrix_world @ v.co).z > zb + 0.004]
bmesh.ops.delete(bm, geom=kill, context='VERTS'); bm.to_mesh(hair_ar.data); bm.free()

# ================================================================== CARS (CC-BY touring car, roof off, folded hood added, repainted)
SC_CAR = 0.0058
def build_car(name, paint, pennant=None):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=os.path.join(ASSETS, "car.glb"))
    new = [o for o in bpy.data.objects if o not in before]
    bpy.context.view_layer.update()
    root = bpy.data.objects.new(name, None); sc.collection.objects.link(root); root.empty_display_size = 1.5
    sway = bpy.data.objects.new(name + "_Body", None); sc.collection.objects.link(sway); sway.parent = root
    T = Matrix.Rotation(math.radians(90), 4, 'Z') @ Matrix.Translation((0, 0, 198 * SC_CAR)) @ Matrix.Scale(SC_CAR, 4)
    groups = {}
    for o in new:
        if o.type != 'MESH' or o.name.startswith("roof"): continue
        me = o.data.copy(); me.transform(T @ o.matrix_world)
        key = "Body"
        for w in ("wheel front.001", "wheel front", "wheel back.001", "wheel back"):
            if o.name.startswith(w + "_"): key = w; break
        groups.setdefault(key, []).append(me)
    for o in new: bpy.data.objects.remove(o)
    parts = {}
    for key, mes in groups.items():
        bm = bmesh.new(); mats = []
        for me in mes:
            off = len(mats); mats += list(me.materials)
            tmp = bmesh.new(); tmp.from_mesh(me)
            for f in tmp.faces: f.material_index += off
            tm = bpy.data.meshes.new("tmp"); tmp.to_mesh(tm); tmp.free(); bm.from_mesh(tm); bpy.data.meshes.remove(tm)
        me2 = bpy.data.meshes.new(name + "_" + key); bm.to_mesh(me2); bm.free()
        for m in mats: me2.materials.append(m)
        o = bpy.data.objects.new(name + "_" + key.replace(" ", "_").replace(".", ""), me2); sc.collection.objects.link(o)
        for p in me2.polygons: p.use_smooth = True
        if key != "Body":
            cen = sum((v.co for v in me2.vertices), Vector()) / len(me2.vertices)
            me2.transform(Matrix.Translation(-cen)); o.location = cen; o.parent = root; o.rotation_mode = 'XYZ'
        else:
            o.parent = sway
        parts[key] = o
    body = parts["Body"]
    for i, m in enumerate(body.data.materials):
        if m is None: continue
        m2 = m.copy(); m2.name = name + "_" + m.name
        bs = next((x for x in m2.node_tree.nodes if x.type == 'BSDF_PRINCIPLED'), None)
        if bs and m.name in ("body", "body_matte"):
            for lk in list(bs.inputs['Base Color'].links): m2.node_tree.links.remove(lk)
            bs.inputs['Base Color'].default_value = (*(paint if m.name == "body" else (0.02, 0.02, 0.02)), 1)
            bs.inputs['Roughness'].default_value = 0.2 if m.name == "body" else 0.5
            bs.inputs['Metallic'].default_value = 0.0; bs.inputs['Coat Weight'].default_value = 0.7 if m.name == "body" else 0.0
        if bs and m.name == "leather":
            for lk in list(bs.inputs['Base Color'].links): m2.node_tree.links.remove(lk)
            bs.inputs['Base Color'].default_value = (0.32, 0.05, 0.03, 1); bs.inputs['Roughness'].default_value = 0.45
        body.data.materials[i] = m2
    for k, o in parts.items():
        if k == "Body": continue
        for i, m in enumerate(o.data.materials):
            if m and (name + "_" + m.name) in bpy.data.materials: o.data.materials[i] = bpy.data.materials[name + "_" + m.name]
    # folded hood behind the rear seat: a leather roll over three bows (the bomb bounces off it)
    hood_m = mat(name + "_Hood", (0.06, 0.045, 0.035), rough=0.5, coat=0.2)
    xr = -(262 * SC_CAR) - 0.10; zr = (113 + 198) * SC_CAR + 0.02
    roll = cyl(name + "_HoodRoll", 0.15, 1.30, (xr, 0, zr), hood_m, rot=(math.radians(90), 0, 0), verts=32, bevel=0.03)
    roll.scale = (1.0, 0.75, 1.0)
    sd = roll.modifiers.new("sub", 'SUBSURF'); sd.levels = 1; sd.render_levels = 2
    tex = bpy.data.textures.new(name + "_hoodfold", 'CLOUDS'); tex.noise_scale = 0.06
    dp = roll.modifiers.new("folds", 'DISPLACE'); dp.texture = tex; dp.strength = 0.015
    roll.parent = sway
    for dx in (-0.06, 0.06):
        bow = curve_tube(name + "_HoodBow", [(xr + dx, -0.62, zr - 0.25), (xr + dx, -0.66, zr + 0.05), (xr + dx, 0.66, zr + 0.05), (xr + dx, 0.62, zr - 0.25)], 0.012, mat("M_Chrome", (0.8, 0.8, 0.82), rough=0.15, metal=1.0))
        bow.parent = sway
    if pennant:
        for sy in (-1, 1):
            fx, fy, fz = 1.85, sy * 0.62, (60 + 198) * SC_CAR
            pole = cyl(name + "_PennantPole", 0.006, 0.42, (fx, fy, fz + 0.21), mat("M_Chrome", (0.8, 0.8, 0.82), rough=0.15, metal=1.0))
            pole.parent = sway
            pm = bpy.data.meshes.new(name + "_Pennant"); bmp = bmesh.new()
            v0 = bmp.verts.new((fx, fy, fz + 0.40)); v1 = bmp.verts.new((fx, fy, fz + 0.24)); v2 = bmp.verts.new((fx - 0.30, fy, fz + 0.32))
            bmp.faces.new((v0, v1, v2)); bmp.to_mesh(pm); bmp.free()
            po = bpy.data.objects.new(name + "_Pennant", pm); sc.collection.objects.link(po); po.parent = sway
            pm.materials.append(pennant)
            s = po.modifiers.new("solid", 'SOLIDIFY'); s.thickness = 0.004
    root["wheel_r"] = parts["wheel front"].dimensions.z / 2
    return root, sway, parts

pen_m = mat("M_PennantYellow", (0.98, 0.72, 0.02), rough=0.6)
CAR1, CAR1B, CAR1P = build_car("Car1", (0.02, 0.38, 0.14), pennant=pen_m)
CAR2, CAR2B, CAR2P = build_car("Car2", (0.03, 0.06, 0.25))
print("CAR wheel_r", CAR1["wheel_r"])
# seat geometry (car-local): rear cushion top, front cushion top, floor
SEAT_REAR_Z = (32.4 + 198) * SC_CAR; SEAT_FRONT_Z = (23.6 + 198) * SC_CAR; FLOOR_Z = (-37.6 + 198) * SC_CAR
CAR1["seat_rear_z"] = SEAT_REAR_Z; CAR1["seat_front_z"] = SEAT_FRONT_Z; CAR1["floor_z"] = FLOOR_Z
CAR2["seat_rear_z"] = SEAT_REAR_Z; CAR2["seat_front_z"] = SEAT_FRONT_Z; CAR2["floor_z"] = FLOOR_Z

# ================================================================== PROPS
# pistol (Browning 1910, CC-BY): spare magazine dropped, one plain blued-steel material (no maker's monogram)
before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=os.path.join(ASSETS, "pistol.glb"))
new = [o for o in bpy.data.objects if o not in before and o.type == 'MESH']
for o in [o for o in bpy.data.objects if o not in before and o.type != 'MESH']:
    for c in o.children:
        mw = c.matrix_world.copy(); c.parent = None; c.matrix_world = mw
    bpy.data.objects.remove(o)
gun_m = mat("M_Gun", (0.035, 0.038, 0.045), rough=0.32, metal=0.85)
grip_m = mat("M_GunGrip", (0.05, 0.03, 0.02), rough=0.5)
keep = []
for o in new:
    bb = [o.matrix_world @ Vector(c) for c in o.bound_box]
    if min(p.x for p in bb) > 5.0: bpy.data.objects.remove(o); continue
    keep.append(o)
for o in keep:
    o.data.materials.clear(); o.data.materials.append(gun_m)
bpy.ops.object.select_all(action='DESELECT')
for o in keep: o.select_set(True)
bpy.context.view_layer.objects.active = keep[0]; bpy.ops.object.join()
GUN = bpy.context.active_object; GUN.name = "Pistol"
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
# scale: real length 153 mm; model spans x -4.65..4.71 (muzzle at -x, grip down to -z)
s = 0.153 / 9.36
GUN.data.transform(Matrix.Scale(s, 4))
# origin at the grip centre (where the palm closes): grip x 1.2..4.7 z -3.1..1.0 in model units
gc = Vector((3.0, 0.0, -1.0)) * s
GUN.data.transform(Matrix.Translation(-gc))
GUN["muzzle"] = tuple(Vector((-4.65, 0, 2.45)) * s - gc)
for p in GUN.data.polygons: p.use_smooth = True
GUN.location = (0, 0, -50)
# the thrown bomb: a small dark iron grenade with a fuse cap (one object for the whole film)
bomb_m = mat("M_Bomb", (0.05, 0.05, 0.055), rough=0.45, metal=0.6)
BOMB = sphere("Bomb", 0.045, (0, 0, -50), bomb_m, segs=32)
BOMB.scale = (1.0, 1.0, 0.82)
cap = cyl("BombCap", 0.012, 0.03, (0, 0, -50 + 0.045), mat("M_BombCap", (0.55, 0.42, 0.20), rough=0.35, metal=0.9), verts=16)
cap.parent = BOMB; cap.location = (0, 0, 0.045 / 0.82)
tex = bpy.data.textures.new("bomb_ribs", 'WOOD'); tex.wood_type = 'RINGS'; tex.noise_scale = 0.02
d = BOMB.modifiers.new("ribs", 'DISPLACE'); d.texture = tex; d.strength = 0.002

# ================================================================== SET
def ph_mat(name, pid, tint_rgb, scale=0.5, rough=0.8, bump=0.35):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; N = nt.nodes; L = nt.links
    p = N["Principled BSDF"]; p.inputs["Roughness"].default_value = rough
    tc = N.new("ShaderNodeTexCoord"); mp = N.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (scale, scale, scale)
    tx = N.new("ShaderNodeTexImage"); tx.projection = 'BOX'; tx.projection_blend = 0.3
    tx.image = bpy.data.images.load(os.path.join(PH, pid, "textures", pid + "_diff_1k.jpg"))
    L.new(tc.outputs["Object"], mp.inputs["Vector"]); L.new(mp.outputs["Vector"], tx.inputs["Vector"])
    bw = N.new("ShaderNodeRGBToBW"); L.new(tx.outputs["Color"], bw.inputs[0])
    mx = N.new("ShaderNodeMix"); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs["Factor"].default_value = 1.0
    L.new(tx.outputs["Color"], mx.inputs["A"]); mx.inputs["B"].default_value = (*tint_rgb, 1)
    L.new(mx.outputs["Result"], p.inputs["Base Color"])
    bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = bump; bp.inputs["Distance"].default_value = 0.01
    L.new(bw.outputs[0], bp.inputs["Height"]); L.new(bp.outputs["Normal"], p.inputs["Normal"])
    return m

SETC = coll("Set")
cobble_m = ph_mat("M_Cobble", "cobblestone_floor_08", (1.25, 1.05, 0.85), scale=0.35, rough=0.75, bump=0.6)
paving_m = ph_mat("M_Paving", "castle_brick_07", (1.1, 0.95, 0.8), scale=0.6, rough=0.8, bump=0.4)
kerb_m = mat("M_Kerb", (0.55, 0.50, 0.44), rough=0.7)
PLASTERS = [ph_mat("M_PlasterYellow", "yellow_plaster_02", (1.6, 1.15, 0.25)),
            ph_mat("M_PlasterTerracotta", "red_plaster_weathered", (1.5, 0.55, 0.30)),
            ph_mat("M_PlasterTeal", "white_stucco", (0.25, 0.85, 0.85)),
            ph_mat("M_PlasterCream", "white_stucco", (1.25, 1.05, 0.75)),
            ph_mat("M_PlasterRose", "white_stucco", (1.3, 0.55, 0.60)),
            ph_mat("M_PlasterOchre", "yellow_plaster_02", (1.4, 0.75, 0.25)),
            ph_mat("M_PlasterBlue", "white_stucco", (0.45, 0.60, 1.25))]
stone_m = ph_mat("M_StoneParapet", "plaster_stone_wall_01", (1.0, 0.92, 0.80), scale=0.5)
trim_m = mat("M_Trim", (0.92, 0.88, 0.80), rough=0.55)
glass_m = mat("M_WindowGlass", (0.03, 0.06, 0.09), rough=0.08, spec=0.8)
frame_m = mat("M_WindowFrame", (0.95, 0.94, 0.90), rough=0.4)
shut_ms = [mat("M_ShutterGreen", (0.02, 0.30, 0.12), rough=0.5), mat("M_ShutterBlue", (0.02, 0.12, 0.40), rough=0.5),
           mat("M_ShutterRed", (0.45, 0.04, 0.03), rough=0.5)]
door_m = wood("M_DoorWood", (0.18, 0.08, 0.03), (0.32, 0.15, 0.06))
roof_m = ph_mat("M_RoofTiles", "castle_brick_07", (1.5, 0.45, 0.22), scale=1.2, rough=0.7, bump=0.5)

def add_box(bm, c, s, mi):
    """axis-aligned box into a bmesh (centre c, size s, material index mi)"""
    r = bmesh.ops.create_cube(bm, size=1.0, matrix=Matrix.Translation(c) @ Matrix.Diagonal((*s, 1.0)))
    for f in {f for v in r["verts"] for f in v.link_faces}: f.material_index = mi

def ground():
    # quay road + side street (cobbles), pavements with kerbs, river parapet, river, far bank quay
    box("Road", (140, 8.0, 0.2), (-35, 0, -0.1), cobble_m, bevel=0)
    box("SideStreet", (10.0, 70, 0.2), (0, 39, -0.1), cobble_m, bevel=0)
    for nm, sz, c in (("PaveNorthA", (88.5 - 5.0, 3.5, 0.15), (-50.0 + (-7.5 + 95) / 2 - 43.75 + 0.0, 5.75, 0.075)),):
        pass
    box("PaveNorthA", (95 - 5.0, 3.5, 0.15), (-50.0, 5.75, 0.075), paving_m, bevel=0.02, segs=2)        # x -95..-5
    box("PaveNorthB", (25.0, 3.5, 0.15), (17.5, 5.75, 0.075), paving_m, bevel=0.02, segs=2)            # x 5..30
    box("PaveSideW", (2.5, 62.5, 0.15), (-6.25, 38.75, 0.075), paving_m, bevel=0.02, segs=2)           # x -7.5..-5, y 7.5..70
    box("PaveSideE", (2.5, 62.5, 0.15), (6.25, 38.75, 0.075), paving_m, bevel=0.02, segs=2)
    box("Parapet", (140, 0.5, 0.95), (-35, -4.35, 0.475), stone_m, bevel=0.03, segs=2)
    box("ParapetCap", (140, 0.62, 0.08), (-35, -4.35, 0.98), kerb_m, bevel=0.02, segs=2)
    water_m = mat("M_River", (0.02, 0.25, 0.30), rough=0.12, spec=0.03)
    w = box("River", (160, 36, 0.1), (-35, -22.6, -2.6), water_m, bevel=0)
    tex = bpy.data.textures.new("ripple", 'CLOUDS'); tex.noise_scale = 0.8
    box("RiverWallN", (140, 0.6, 3.0), (-35, -4.9, -1.2), stone_m, bevel=0)
    box("FarQuay", (160, 12, 0.3), (-35, -46.6, 0.0), paving_m, bevel=0)
    box("FarWall", (160, 0.6, 3.0), (-35, -40.5, -1.2), stone_m, bevel=0)
ground()

def building(name, x0, x1, y0, depth, h, floors, pm, face="S", shop=False, roof=True, shutters=None):
    """one house: plaster mass + cornice + string courses + recessed windows with frames, sills and shutters, door/shop front,
    hipped tile roof. face: S = front at y0 facing -y; W = front at x0 facing -x; N = front at y0 facing +y."""
    bm = bmesh.new(); mats = [pm, trim_m, glass_m, frame_m, shutters or random.choice(shut_ms), door_m]
    W_ = x1 - x0
    # mass
    if face in ("S", "N"):
        yc = y0 + depth / 2 if face == "S" else y0 - depth / 2
        add_box(bm, Vector(((x0 + x1) / 2, yc, h / 2)), (W_, depth, h), 0)
    else:
        add_box(bm, Vector((x0 + depth / 2, (y0 + x1) / 2, h / 2)), (depth, x1 - y0, h), 0)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); SETC.objects.link(o)
    for m in mats: me.materials.append(m)
    return o

def facade_details(o, along, n_out, p0, length, h, floors, shop=False, door_at=None):
    """windows etc. on a facade: along = unit vector along the facade, n_out = outward normal, p0 = facade start at ground"""
    bm = bmesh.new(); bm.from_mesh(o.data)
    al = Vector(along); no = Vector(n_out); P0 = Vector(p0)
    def bx(u, z, w, hh, d, out, mi):
        c = P0 + al * u + no * out + Vector((0, 0, z))
        sx = abs(al.x) * w + abs(no.x) * d; sy = abs(al.y) * w + abs(no.y) * d
        add_box(bm, c, (max(sx, 0.001), max(sy, 0.001), hh), mi)
    fh = (h - 0.8) / floors
    bays = max(2, int(length / 2.6))
    bw = length / bays
    # string courses + cornice
    for k in range(1, floors):
        bx(length / 2, fh * k, length, 0.14, 0.12, 0.06, 1)
    bx(length / 2, h - 0.25, length + 0.3, 0.42, 0.45, 0.2, 1)
    bx(length / 2, 0.35, length, 0.7, 0.10, 0.05, 1)          # plinth
    for k in range(floors):
        zc = fh * k + fh * 0.55
        for b in range(bays):
            u = bw * (b + 0.5)
            if k == 0:
                if shop:
                    bx(u, 1.55, bw * 0.78, 2.5, 0.06, 0.012, 2)       # shop window glass (recessed)
                    bx(u, 2.86, bw * 0.84, 0.12, 0.14, 0.02, 3)        # frame top
                    bx(u - bw * 0.40, 1.5, 0.10, 2.8, 0.14, 0.02, 3); bx(u + bw * 0.40, 1.5, 0.10, 2.8, 0.14, 0.02, 3)
                elif door_at is not None and b == door_at:
                    bx(u, 1.25, 1.2, 2.5, 0.06, 0.012, 5)
                    bx(u, 2.6, 1.45, 0.25, 0.16, 0.03, 1)
                else:
                    bx(u, 1.7, 0.9, 1.4, 0.05, 0.012, 2); bx(u, 1.0, 1.05, 0.08, 0.12, 0.04, 1)
                continue
            ww, wh = 1.0, min(1.8, fh * 0.62)
            bx(u, zc, ww, wh, 0.05, 0.012, 2)                         # glass pane on the wall, framed
            bx(u, zc + wh / 2 + 0.04, ww + 0.16, 0.08, 0.10, 0.02, 3)  # frame
            bx(u, zc - wh / 2 - 0.04, ww + 0.16, 0.08, 0.10, 0.02, 3)
            bx(u - ww / 2 - 0.04, zc, 0.08, wh, 0.10, 0.02, 3); bx(u + ww / 2 + 0.04, zc, 0.08, wh, 0.10, 0.02, 3)
            bx(u, zc, 0.05, wh, 0.06, 0.03, 3)                       # mullion
            bx(u, zc - wh / 2 - 0.11, ww + 0.3, 0.07, 0.22, 0.08, 1)  # sill
            bx(u, zc + wh / 2 + 0.22, ww + 0.4, 0.16, 0.16, 0.05, 1)  # pediment lintel
            for sgn in (-1, 1):                                        # open shutters
                bx(u + sgn * (ww / 2 + 0.34), zc, 0.48, wh, 0.04, 0.05, 4)
            if k == 1 and b % 3 == 1:                                  # small balcony with railing
                bx(u, zc - wh / 2 - 0.18, ww + 0.8, 0.12, 0.7, 0.35, 1)
                for t in range(9):
                    bx(u - (ww + 0.7) / 2 + t * (ww + 0.7) / 8, zc - wh / 2 + 0.25, 0.025, 0.75, 0.025, 0.66, 3)
                bx(u, zc - wh / 2 + 0.62, ww + 0.8, 0.04, 0.05, 0.66, 3)
    bm.to_mesh(o.data); bm.free()

def roof_on(name, x0, x1, y0, y1, z, rise=2.2, mat_=None):
    bm = bmesh.new(); ov = 0.35
    v = [bm.verts.new(p) for p in ((x0 - ov, y0 - ov, z), (x1 + ov, y0 - ov, z), (x1 + ov, y1 + ov, z), (x0 - ov, y1 + ov, z))]
    if (x1 - x0) >= (y1 - y0):
        r = [bm.verts.new(((x0 + x1) / 2 - (x1 - x0) / 2 + (y1 - y0) / 2, (y0 + y1) / 2, z + rise)), bm.verts.new(((x0 + x1) / 2 + (x1 - x0) / 2 - (y1 - y0) / 2, (y0 + y1) / 2, z + rise))]
        faces = [(v[0], v[1], r[1], r[0]), (v[1], v[2], r[1]), (v[2], v[3], r[0], r[1]), (v[3], v[0], r[0])]
    else:
        r = [bm.verts.new(((x0 + x1) / 2, (y0 + y1) / 2 - (y1 - y0) / 2 + (x1 - x0) / 2, z + rise)), bm.verts.new(((x0 + x1) / 2, (y0 + y1) / 2 + (y1 - y0) / 2 - (x1 - x0) / 2, z + rise))]
        faces = [(v[0], v[1], r[0]), (v[1], v[2], r[1], r[0]), (v[2], v[3], r[1]), (v[3], v[0], r[0], r[1])]
    for f in faces: bm.faces.new(f)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); SETC.objects.link(o); me.materials.append(mat_ or roof_m)
    s = o.modifiers.new("solid", 'SOLIDIFY'); s.thickness = 0.12
    return o

# north row on the quay (block A, x -95..-7.5) and block B east of the side street (cafe on the corner, x 7.5..30)
DEPTH = 10.0
xs = [-95.0]
while xs[-1] < -7.5 - 7:
    xs.append(xs[-1] + random.choice((9.0, 10.5, 12.0)))
xs[-1] = -7.5
k = 0
for x0, x1 in zip(xs, xs[1:]):
    h = random.choice((13.0, 14.5, 16.0)); fl = 4 if h > 14 else 3
    pm = PLASTERS[k % len(PLASTERS)]; k += 1
    o = building("House_%02d" % k, x0, x1, 7.5, DEPTH, h, fl, pm, shop=(k % 3 == 0))
    facade_details(o, (1, 0, 0), (0, -1, 0), (x0, 7.5, 0), x1 - x0, h, fl, shop=(k % 3 == 0), door_at=(1 if k % 3 else None))
    roof_on("Roof_%02d" % k, x0, x1, 7.5, 7.5 + DEPTH, h)
    if x1 == -7.5:      # the corner house also fronts the side street
        facade_details(o, (0, 1, 0), (1, 0, 0), (-7.5, 7.5, 0), DEPTH, h, fl, door_at=1)
# side street west facades (y 17.5..70) and east facades (y 20..70)
for side, xf, n in (("W", -7.5, (1, 0, 0)), ("E", 7.5, (-1, 0, 0))):
    ys = [17.5 if side == "W" else 20.0]
    while ys[-1] < 62: ys.append(ys[-1] + random.choice((9.0, 11.0)))
    for j, (y0, y1) in enumerate(zip(ys, ys[1:])):
        h = random.choice((13.0, 14.5)); pm = PLASTERS[(k + j) % len(PLASTERS)]
        x0b = xf - DEPTH if side == "W" else xf
        bm = bmesh.new(); add_box(bm, Vector((x0b + DEPTH / 2, (y0 + y1) / 2, h / 2)), (DEPTH, y1 - y0, h), 0)
        me = bpy.data.meshes.new("SideHouse_%s%02d" % (side, j)); bm.to_mesh(me); bm.free()
        o = bpy.data.objects.new(me.name, me); SETC.objects.link(o)
        for m in (pm, trim_m, glass_m, frame_m, random.choice(shut_ms), door_m): me.materials.append(m)
        p0 = (xf, y0, 0) if side == "E" else (xf, y1, 0)
        facade_details(o, (0, 1, 0) if side == "E" else (0, -1, 0), n, p0, y1 - y0, h, 3 if h < 14 else 4, door_at=1)
        roof_on("SideRoof_%s%02d" % (side, j), x0b, x0b + DEPTH, y0, y1, h)
# block B: the cafe house on the corner (x 7.5..19.5, y 7.5..20) + two more houses to x 30
CAFE_H = 13.0
o = building("CafeHouse", 7.5, 19.5, 7.5, 12.5, CAFE_H, 3, PLASTERS[0])
facade_details(o, (1, 0, 0), (0, -1, 0), (7.5, 7.5, 0), 12.0, CAFE_H, 3, shop=True)
facade_details(o, (0, 1, 0), (-1, 0, 0), (7.5, 7.5, 0), 12.5, CAFE_H, 3, shop=True)
roof_on("CafeRoof", 7.5, 19.5, 7.5, 20.0, CAFE_H)
for j, (x0, x1) in enumerate(((19.5, 30.0), (30.0, 41.0))):
    o = building("HouseB_%d" % j, x0, x1, 7.5, DEPTH, 14.5, 4, PLASTERS[(j + 3) % len(PLASTERS)])
    facade_details(o, (1, 0, 0), (0, -1, 0), (x0, 7.5, 0), x1 - x0, 14.5, 4, door_at=1)
    roof_on("RoofB_%d" % j, x0, x1, 7.5, 7.5 + DEPTH, 14.5)
# far bank (backdrop across the river)
xf0 = -100.0; j = 0
while xf0 < 40:
    w_ = random.choice((10.0, 12.0, 14.0)); h = random.choice((11.0, 13.0, 15.0))
    o = building("FarHouse_%02d" % j, xf0, xf0 + w_, -42.0, DEPTH, h, 3, PLASTERS[(j + 2) % len(PLASTERS)])
    o.location.y -= DEPTH
    facade_details(o, (-1, 0, 0), (0, 1, 0), (xf0 + w_, -42.0, 0), w_, h, 3, door_at=1)
    roof_on("FarRoof_%02d" % j, xf0, xf0 + w_, -52.0, -42.0, h)
    xf0 += w_; j += 1
# minaret + dome silhouettes far behind the far bank (Sarajevo skyline)
dome_m = mat("M_Dome", (0.10, 0.35, 0.30), rough=0.35, coat=0.4); minar_m = mat("M_Minaret", (0.95, 0.93, 0.86), rough=0.6)
for (mx_, my_) in ((-60, -70), (-15, -75), (25, -68)):
    cyl("Minaret", 1.0, 28, (mx_, my_, 14), minar_m, verts=16); c_ = bpy.data.objects.new("x", None)
    bpy.ops.mesh.primitive_cone_add(radius1=1.3, depth=5, location=(mx_, my_, 30.5)); cn = bpy.context.active_object; cn.data.materials.append(dome_m)
    sphere("Dome", 7.0, (mx_ + 12, my_ - 6, 10), dome_m)
# the cafe awnings (striped canvas, sloped) on both cafe fronts + the DA KRAS FILMS shop sign
def stripes(name, c1, c2, n=10.0):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; N = nt.nodes; L = nt.links
    p = N["Principled BSDF"]; p.inputs["Roughness"].default_value = 0.7; p.inputs["Sheen Weight"].default_value = 0.3
    tc = N.new("ShaderNodeTexCoord"); wv = N.new("ShaderNodeTexWave"); wv.bands_direction = 'X'; wv.inputs["Scale"].default_value = n
    wv.wave_profile = 'SAW'
    cr = N.new("ShaderNodeValToRGB"); cr.color_ramp.interpolation = 'CONSTANT'
    cr.color_ramp.elements[0].color = (*c1, 1); cr.color_ramp.elements[1].position = 0.5; cr.color_ramp.elements[1].color = (*c2, 1)
    L.new(tc.outputs["UV"], wv.inputs["Vector"]); L.new(wv.outputs["Fac"], cr.inputs["Fac"]); L.new(cr.outputs["Color"], p.inputs["Base Color"])
    return m
awn_m = stripes("M_Awning", (0.75, 0.03, 0.05), (0.98, 0.95, 0.88), n=1.4)
def awning(name, p_wall, along, n_out, length, z=3.2, proj=1.6, drop=0.7):
    al = Vector(along); no = Vector(n_out); P = Vector(p_wall)
    bm = bmesh.new(); uv = bm.loops.layers.uv.new("UVMap")
    a0 = P + Vector((0, 0, z)); a1 = a0 + al * length
    b0 = a0 + no * proj - Vector((0, 0, drop)); b1 = b0 + al * length
    c0 = b0 - Vector((0, 0, 0.30)); c1 = b1 - Vector((0, 0, 0.30))
    vs = [bm.verts.new(p) for p in (a0, a1, b1, b0, c0, c1)]
    f1 = bm.faces.new((vs[0], vs[3], vs[2], vs[1])); f2 = bm.faces.new((vs[3], vs[4], vs[5], vs[2]))
    for f in (f1, f2):
        for l in f.loops:
            l[uv].uv = ((l.vert.co - a0).dot(al) / 1.0, 0.0)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); SETC.objects.link(o); me.materials.append(awn_m)
    s = o.modifiers.new("solid", 'SOLIDIFY'); s.thickness = 0.02
    for t in range(int(length / 1.5) + 1):        # iron awning arms
        q0 = a0 + al * (t * length / int(length / 1.5)); q1 = q0 + no * proj - Vector((0, 0, drop))
        curve_tube(name + "_arm", [tuple(q0), tuple(q1)], 0.012, mat("M_Iron", (0.03, 0.03, 0.03), rough=0.4, metal=0.8))
    return o
awning("CafeAwningS", (8.0, 7.5, 0), (1, 0, 0), (0, -1, 0), 11.0)
awning("CafeAwningW", (7.5, 8.2, 0), (0, 1, 0), (-1, 0, 0), 10.5)
# shop sign: deep-green enamel board with the white logo, on the side-street front (above the awning) and on the quay front
logo_w = image_mat("M_LogoSign", LOGO.replace("_dark", "_white"), emit=0.25, rough=0.45, alpha=True)
sign_bg = mat("M_SignBoard", (0.01, 0.18, 0.10), rough=0.35, coat=0.6)
gold_m = mat("M_SignGold", (0.95, 0.65, 0.15), rough=0.25, metal=0.9)
LOGO_SIGNS = []
for nm, c, rot, al in (("SignW", Vector((7.40, 13.4, 4.75)), (math.radians(90), 0, math.radians(-90)), (0, 1, 0)),
                       ("SignS", Vector((13.5, 7.40, 4.75)), (math.radians(90), 0, 0), (1, 0, 0))):
    brd = box(nm + "_Board", (3.6 if al[0] else 0.10, 0.10 if al[0] else 3.6, 1.62), c, sign_bg, bevel=0.03)
    fr = box(nm + "_Frame", (3.8 if al[0] else 0.08, 0.08 if al[0] else 3.8, 1.82), c + Vector((0.03, 0.03, 0)) * 0, gold_m, bevel=0.02)
    fr.location += (Vector((0, 0.03, 0)) if al[0] else Vector((0.03, 0, 0)))
    bpy.ops.mesh.primitive_plane_add(size=1.0, location=c, rotation=rot)
    lp = bpy.context.active_object; lp.name = nm + "_Logo"; lp.scale = (3.2, 3.2 * 414 / 967, 1)
    off = Vector((0, -0.06, 0)) if al[0] else Vector((-0.06, 0, 0))
    lp.location = c + off
    lp.data.materials.append(logo_w); LOGO_SIGNS.append(lp)
    for o_ in (brd, fr, lp): to_coll(o_, SETC)
# cafe tables and chairs under the awning (simple bentwood set) on the quay front, clear of the people
cafe_wood = wood("M_CafeWood", (0.25, 0.10, 0.04), (0.40, 0.18, 0.07))
for i, (tx_, ty_) in enumerate(((10.5, 6.6), (13.5, 6.6), (16.5, 6.6))):
    cyl("CafeTableTop", 0.35, 0.03, (tx_, ty_, 0.15 + 0.74), cafe_wood, verts=32, bevel=0.01)
    cyl("CafeTableLeg", 0.03, 0.72, (tx_, ty_, 0.15 + 0.37), mat("M_Iron", (0.03, 0.03, 0.03), rough=0.4, metal=0.8))
    cyl("CafeTableFoot", 0.22, 0.03, (tx_, ty_, 0.15 + 0.015), mat("M_Iron", (0.03, 0.03, 0.03), rough=0.4, metal=0.8))
    cup_ = cyl("CafeCup", 0.04, 0.07, (tx_ + 0.1, ty_, 0.15 + 0.79), mat("M_Porcelain", (0.96, 0.95, 0.92), rough=0.2), verts=24)
# lamp posts along the kerb (cast iron) every 16 m, with bunting strung between them and across the street
iron_m = mat("M_Iron", (0.03, 0.03, 0.03), rough=0.4, metal=0.8)
lamp_glass = mat("M_LampGlass", (0.95, 0.9, 0.7), rough=0.1, emit=((1.0, 0.85, 0.5), 0.3))
LAMPS = []
for x_ in list(range(-90, -8, 16)) + [11, 27]:
    for y_ in (4.45, -3.7):
        if y_ < 0 and x_ > -10: pass
        cyl("LampPost", 0.07, 4.2, (x_, y_, 2.1 + (0.15 if y_ > 0 else 0.9)), iron_m, verts=12)
        cyl("LampBase", 0.16, 0.6, (x_, y_, 0.3 + (0.15 if y_ > 0 else 0.9)), iron_m, verts=12, bevel=0.03)
        bpy.ops.mesh.primitive_cone_add(radius1=0.22, radius2=0.12, depth=0.45, location=(x_, y_, 4.55 + (0.15 if y_ > 0 else 0.9)))
        lg = bpy.context.active_object; lg.name = "LampHead"; lg.data.materials.append(lamp_glass)
        LAMPS.append(Vector((x_, y_, 4.8 + (0.15 if y_ > 0 else 0.9))))
flag_ms = [mat("M_FlagRed", (0.80, 0.02, 0.03), rough=0.6), mat("M_FlagYellow", (0.98, 0.70, 0.02), rough=0.6),
           mat("M_FlagWhite", (0.95, 0.94, 0.90), rough=0.6), mat("M_FlagBlack", (0.03, 0.03, 0.03), rough=0.6),
           mat("M_FlagGreen", (0.02, 0.45, 0.15), rough=0.6)]
rope_m = mat("M_Rope", (0.55, 0.45, 0.30), rough=0.8)
def bunting(name, p0, p1, sag=0.9, every=0.55, cols=(0, 1, 2)):
    p0 = Vector(p0); p1 = Vector(p1); L = (p1 - p0).length; n = max(2, int(L / every))
    pts = [p0.lerp(p1, t / 12.0) - Vector((0, 0, sag * 4 * (t / 12.0) * (1 - t / 12.0))) for t in range(13)]
    curve_tube(name + "_rope", [tuple(p) for p in pts], 0.008, rope_m, res=4)
    bm = bmesh.new()
    for i in range(1, n):
        t = i / n; p = p0.lerp(p1, t) - Vector((0, 0, sag * 4 * t * (1 - t)))
        d = (p1 - p0).normalized()
        v0 = bm.verts.new(p - d * 0.14); v1 = bm.verts.new(p + d * 0.14); v2 = bm.verts.new(p - Vector((0, 0, 0.34)) + Vector((random.uniform(-0.03, 0.03), random.uniform(-0.03, 0.03), 0)))
        f = bm.faces.new((v0, v1, v2)); f.material_index = cols[i % len(cols)]
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); SETC.objects.link(o)
    for c in cols: me.materials.append(flag_ms[c])
    for f in me.polygons: f.material_index = f.material_index
    s = o.modifiers.new("solid", 'SOLIDIFY'); s.thickness = 0.004
    return o
for i in range(len(LAMPS) - 2):
    a_, b_ = LAMPS[i], LAMPS[i + 2]
    if abs(a_.y - b_.y) < 0.1 and abs(a_.x - b_.x) < 20:
        bunting("BuntingKerb%02d" % i, a_ - Vector((0, 0, 0.6)), b_ - Vector((0, 0, 0.6)), sag=0.8, cols=(1, 3) if i % 4 == 0 else (0, 2))
# bunting across the quay, high (well above every camera path), and flags hanging from the facades
for x_ in range(-88, -8, 12):
    bunting("BuntingCross%03d" % (x_ + 100), (x_, 7.4, 9.5), (x_ + 4, -4.0, 7.0), sag=1.0, cols=(0, 2, 1))
for x_ in range(-90, -10, 7):
    zf = 8.5
    pole = curve_tube("FlagPole", [(x_, 7.5, zf), (x_, 6.4, zf + 0.9)], 0.02, iron_m)
    bm = bmesh.new(); cols = (0, 2) if x_ % 2 else (1, 3)
    for k_, ci in enumerate(cols):
        v = [bm.verts.new(p) for p in ((x_, 6.6 + 0.0, zf + 0.75 - k_ * 0.7), (x_, 6.6, zf + 0.05 - k_ * 0.7), (x_, 6.6 - 0.0, zf + 0.05 - k_ * 0.7), (x_, 6.6, zf + 0.75 - k_ * 0.7))]
    bm.free()
    for k_, ci in enumerate(cols):
        bpy.ops.mesh.primitive_plane_add(size=1, location=(x_ - 0.0, 6.55, zf - 0.55 - k_ * 0.75), rotation=(math.radians(90), 0, math.radians(90)))
        fl = bpy.context.active_object; fl.name = "HangFlag"; fl.scale = (1.0, 0.75, 1); fl.data.materials.append(flag_ms[ci])
        so = fl.modifiers.new("solid", 'SOLIDIFY'); so.thickness = 0.005
# put every loose set object into the Set collection
for o in list(sc.collection.objects):
    if o.type in ('MESH', 'CURVE') and not o.parent and o not in (GUN, BOMB) and not o.name.startswith(("Car", "Archduke")):
        to_coll(o, SETC)

# ================================================================== LOOK: AgX Punchy, sunny sky, fast-render settings (PRODUCTION_RULES)
sc.view_settings.view_transform = 'AgX'
try: sc.view_settings.look = 'AgX - Punchy'
except Exception: pass
sc.view_settings.exposure = 0.0
sc.render.engine = 'CYCLES'
sc.cycles.samples = 64; sc.cycles.adaptive_threshold = 0.04; sc.cycles.use_adaptive_sampling = True; sc.cycles.use_denoising = True
sc.cycles.denoiser = 'OPENIMAGEDENOISE'
sc.cycles.max_bounces = 6; sc.cycles.diffuse_bounces = 3; sc.cycles.glossy_bounces = 3; sc.cycles.transmission_bounces = 6
sc.cycles.transparent_max_bounces = 16; sc.cycles.caustics_reflective = sc.cycles.caustics_refractive = False
sc.render.use_persistent_data = True
sc.render.use_simplify = True; sc.render.simplify_subdivision_render = 2; sc.cycles.texture_limit_render = '2048'
sc.render.use_motion_blur = False
w = bpy.data.worlds.new("World"); sc.world = w; w.use_nodes = True; nt = w.node_tree
env = nt.nodes.new("ShaderNodeTexEnvironment"); env.image = bpy.data.images.load(os.path.join(PH, "hdri", "kloofendal_48d_partly_cloudy_puresky_1k.hdr"))
mp = nt.nodes.new("ShaderNodeMapping"); tc = nt.nodes.new("ShaderNodeTexCoord"); mp.inputs["Rotation"].default_value = (0, 0, math.radians(200))
nt.links.new(tc.outputs["Generated"], mp.inputs["Vector"]); nt.links.new(mp.outputs["Vector"], env.inputs["Vector"])
hs = nt.nodes.new("ShaderNodeHueSaturation"); hs.inputs["Saturation"].default_value = 1.5
nt.links.new(env.outputs["Color"], hs.inputs["Color"]); nt.links.new(hs.outputs["Color"], nt.nodes["Background"].inputs["Color"])
nt.nodes["Background"].inputs["Strength"].default_value = 1.0
sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", 'SUN')); sc.collection.objects.link(sun)
sun.data.energy = 4.2; sun.data.angle = math.radians(2.5); sun.data.color = (1.0, 0.92, 0.80)
sun.rotation_euler = (math.radians(42), 0, math.radians(-35))
sc["logo_signs"] = [o.name for o in LOGO_SIGNS]
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("BUILD_DONE", OUT, len(bpy.data.objects), "objects")
