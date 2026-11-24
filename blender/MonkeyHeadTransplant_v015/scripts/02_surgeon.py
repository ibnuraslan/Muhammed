"""v014 surgeon: ONE fresh MPFB human used for the whole film. Loose scrubs (top + trousers), a cloth bouffant cap and a
surgical mask, all generated from the body mesh itself (offset outward, volume-preserving smoothing, same skin weights),
latex gloves = the body's own hands with a latex material. blender -b base.blend --python 02_surgeon.py -- out.blend"""
import bpy, sys, os, json, math, bmesh
from mathutils import Vector, Matrix
OUT = sys.argv[sys.argv.index("--") + 1]
HERE = os.path.dirname(os.path.abspath(__file__)); PIPE = os.path.join(HERE, "../../pipeline")
from bl_ext.user_default.mpfb.services.humanservice import HumanService
sc = bpy.context.scene
for o in list(bpy.data.objects):
    if o.name == "Surgeon" or o.name.startswith(("Surgeon.", "Surgeon_")): bpy.data.objects.remove(o, do_unlink=True)
bpy.ops.outliner.orphans_purge(do_recursive=True)
_EYE = json.load(open("/root/.config/blender/5.2/extensions/user_default/mpfb/data/settings/eye_settings.default.json"))
info = HumanService._create_default_human_info_dict(); info["name"] = "Surgeon"
info["phenotype"] = {"gender": 1.0, "age": 0.5, "muscle": 0.5, "weight": 0.48, "proportions": 0.65, "height": 0.55,
                     "cupsize": 0.5, "firmness": 0.5, "race": {"asian": 0.15, "caucasian": 0.7, "african": 0.15}}
info["rig"] = "default"
info["eyes"] = "high-poly/high-poly.mhclo"; info["eyebrows"] = "eyebrow001/eyebrow001.mhclo"
info["eyelashes"] = "eyelashes01/eyelashes01.mhclo"; info["teeth"] = "teeth_base/teeth_base.mhclo"; info["tongue"] = "tongue01/tongue01.mhclo"
info["hair"] = ""
es = dict(_EYE); es["IrisMajorColor"] = [0.12, 0.07, 0.03, 1.0]; es["IrisMinorColor"] = [0.05, 0.03, 0.01, 1.0]; info["eyes_material_settings"] = es
info["clothes"] = ["shoes03/shoes03.mhclo"]
info["skin_mhmat"] = "middleage_caucasian_male/middleage_caucasian_male.mhmat"; info["skin_material_type"] = "ENHANCED_SSS"
info["eyes_material_type"] = "PROCEDURAL_EYES"
st = HumanService.get_default_deserialization_settings(); st["subdiv_levels"] = 1
HumanService.deserialize_from_dict(info, st)
rig = bpy.data.objects["Surgeon"]; body = bpy.data.objects["Surgeon.body"]
print("CHILDREN", [c.name for c in rig.children])
_NO_SAVE = True
exec(open(os.path.join(HERE, "eye_fix.py")).read())
exec(open(os.path.join(PIPE, "anim_lib.py")).read())
exec(open(os.path.join(PIPE, "hand_poses.py")).read())
R = make_human_ctrl(rig); add_hand_limits(rig)
for s in "LR":                        # MPFB rest elbow ~46 deg: let the IK straighten a little (mannequin-arm lesson)
    lo = rig.pose.bones["lowerarm01." + s]; lo.ik_min_x = math.radians(-40)
# ---------------------------------------------------------------- region helpers (rest pose, world == armature space)
BN = rig.data.bones
_vis = [(m, m.show_viewport) for m in body.modifiers]
for m, _ in _vis: m.show_viewport = False
_dg = bpy.context.evaluated_depsgraph_get(); _ev = body.evaluated_get(_dg)
me = bpy.data.meshes.new_from_object(_ev); me.name = "SurgeonShapedTmp"
for m, v in _vis: m.show_viewport = v
_orig = body.data
assert len(me.vertices) == len(_orig.vertices)
bone_groups = {g.index: g.name for g in body.vertex_groups if g.name in BN}
dom = []
for v in _orig.vertices:
    best = (0.0, None)
    for g in v.groups:
        n = bone_groups.get(g.group)
        if n and g.weight > best[0]: best = (g.weight, n)
    dom.append(best[1] or "")
helper = set()
for g in body.vertex_groups:
    if g.name in ("HelperGeometry", "JointCubes"):
        for v in _orig.vertices:
            for gg in v.groups:
                if gg.group == g.index and gg.weight > 0.5: helper.add(v.index)
H = lambda n: BN[n].head_local
neck_z = H("neck01").z; hip_z = H("pelvis.L").z; head_c = H("head")
wristL, wristR = H("wrist.L"), H("wrist.R"); ankle = (H("foot.L").z + H("foot.R").z) / 2
TOP_B = ("spine", "breast", "clavicle", "shoulder01", "upperarm", "lowerarm", "pelvis", "root", "neck01", "upperleg01")
LEG_B = ("pelvis", "upperleg", "lowerleg", "root")
HAND_B = ("wrist", "finger", "metacarpal")
def near_wrist(co, d):
    return min((co - wristL).length, (co - wristR).length) < d
def body_cy(z): return 0.0
cy = sum(v.co.y for v in me.vertices if abs(v.co.z - (neck_z - 0.25)) < 0.03) / max(1, sum(1 for v in me.vertices if abs(v.co.z - (neck_z - 0.25)) < 0.03))
def in_top(i, co):
    d = dom[i]
    if not d.startswith(TOP_B) or i in helper: return False
    if co.z < hip_z - 0.03: return False
    if d.startswith("lowerarm") and near_wrist(co, 0.035): return False
    if d == "neck01" and co.z > neck_z - 0.005: return False
    if co.z > neck_z - 0.11 + 1.3 * abs(co.x) and co.y < cy and abs(co.x) < 0.085: return False      # V-neck
    if co.z > neck_z + 0.01: return False
    return True
def in_trousers(i, co):
    d = dom[i]
    if i in helper or d.startswith(("upperarm", "lowerarm", "wrist", "finger", "metacarpal", "foot", "toe")): return False
    if co.z > hip_z + 0.06: return False
    if co.z < ankle + 0.05: return False
    return True
HEAD_SKIP = ("neck",)
brow_z = H("head").z + 0.105     # tuned below from the eyebrow mesh
eb = bpy.data.objects.get("Surgeon.eyebrow001")
eye_z = BN["eye.L"].head_local.z if "eye.L" in BN else H("head").z + 0.06
brow_z = eye_z + 0.032
yf = min(v.co.y for v in me.vertices if dom[v.index] == "head"); yb = max(v.co.y for v in me.vertices if dom[v.index] == "head")
def in_cap(i, co):
    if i in helper: return False
    d = dom[i]
    if d.startswith(("neck02", "neck03")) is False and not d.startswith(("head", "temporalis", "levator", "special", "oculi", "orbicularis", "eye", "jaw", "oris")): 
        if not d.startswith("neck"): return False
    u = (co.y - yf) / (yb - yf)
    zc = brow_z - 0.085 * max(0.0, min(1.0, (u - 0.25) / 0.6))
    return co.z > zc
nose_tip = min((v for v in me.vertices if abs(v.co.x) < 0.006 and v.co.z > neck_z + 0.05 and v.index not in helper), key=lambda v: v.co.y).co
print("HEADINFO top", round(max(v.co.z for v in me.vertices if v.index not in helper), 3), "head bone", tuple(round(x, 3) for x in head_c),
      "brow", round(brow_z, 3), "eye", round(eye_z, 3), "doms", sorted(set(dom[v.index] for v in me.vertices if v.co.z > neck_z + 0.12 and v.index not in helper))[:60])
def in_mask(i, co):
    if i in helper: return False
    if co.y > head_c.y - 0.02: return False
    if abs(co.x) > 0.072: return False
    if dom[i].startswith(("neck", "spine", "clavicle", "breast")): return False
    top = nose_tip.z + 0.022; bot = nose_tip.z - 0.085
    return bot < co.z < top
# ---------------------------------------------------------------- materials
def mat(name, rgb, rough=0.7, sheen=0.3, bump=0.0, scale=400.0):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; p = nt.nodes["Principled BSDF"]
    p.inputs["Base Color"].default_value = (*rgb, 1); p.inputs["Roughness"].default_value = rough
    p.inputs["Sheen Weight"].default_value = sheen * 0.25
    if bump:
        tc = nt.nodes.new("ShaderNodeTexCoord"); wv = nt.nodes.new("ShaderNodeTexWave"); wv.inputs["Scale"].default_value = scale
        wv.inputs["Distortion"].default_value = 2.0; bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = bump
        nt.links.new(tc.outputs["Object"], wv.inputs["Vector"]); nt.links.new(wv.outputs["Fac"], bp.inputs["Height"]); nt.links.new(bp.outputs["Normal"], p.inputs["Normal"])
    return m
M_SCRUB = mat("M_ScrubTop", (0.05, 0.30, 0.36), 0.78, 0.4, 0.08)
M_PANTS = mat("M_ScrubPants", (0.035, 0.22, 0.27), 0.8, 0.4, 0.08)
M_CAP = mat("M_ScrubCap", (0.07, 0.36, 0.42), 0.8, 0.4, 0.1, 250)
M_MASK = mat("M_SurgMask", (0.80, 0.88, 0.92), 0.85, 0.2, 0.12, 300)
M_GLOVE = bpy.data.materials.new("M_Latex"); M_GLOVE.use_nodes = True
pg = M_GLOVE.node_tree.nodes["Principled BSDF"]; pg.inputs["Base Color"].default_value = (0.62, 0.66, 0.86, 1)
pg.inputs["Roughness"].default_value = 0.38; pg.inputs["Subsurface Weight"].default_value = 0.15
# ---------------------------------------------------------------- garment builder
tex = bpy.data.textures.new("ClothFolds", "CLOUDS"); tex.noise_scale = 0.09; tex.noise_depth = 1
tex2 = bpy.data.textures.new("CapCrinkle", "CLOUDS"); tex2.noise_scale = 0.03; tex2.noise_depth = 2
def garment(name, sel, offs, m, smooth=8, thick=0.004, disp=(tex, 0.006), subsurf=1, bsmooth=25):
    bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
    keep = {v.index for v in bm.verts if sel(v.index, v.co)}
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.index not in keep], context='VERTS')
    # drop dangling verts / faces with a boundary on 2+ sides (stair-step teeth), then straighten every boundary loop
    for _ in range(3):
        bad = [f for f in bm.faces if sum(1 for e in f.edges if e.is_boundary) >= 2]
        if not bad: break
        bmesh.ops.delete(bm, geom=bad, context='FACES')
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
    for _ in range(bsmooth):
        new = {}
        for v in bm.verts:
            if not v.is_boundary: continue
            nb = [e.other_vert(v) for e in v.link_edges if e.is_boundary]
            if len(nb) == 2: new[v] = v.co * 0.5 + (nb[0].co + nb[1].co) * 0.25
        for v, c in new.items(): v.co = c
        bmesh.ops.smooth_vert(bm, verts=[v for v in bm.verts if not v.is_boundary and any(w.is_boundary for e in v.link_edges for w in e.verts)], factor=0.5, use_axis_x=True, use_axis_y=True, use_axis_z=True)
    bm.normal_update()
    for v in bm.verts: v.co = v.co + v.normal * offs(v.co)
    bmesh.ops.smooth_laplacian_vert(bm, verts=bm.verts[:], lambda_factor=0.6, lambda_border=0.0, use_x=True, use_y=True, use_z=True, preserve_volume=True) if smooth else None
    for _ in range(smooth):
        bmesh.ops.smooth_vert(bm, verts=[v for v in bm.verts if not v.is_boundary], factor=0.5, use_axis_x=True, use_axis_y=True, use_axis_z=True)
    nm = bpy.data.meshes.new(name); bm.to_mesh(nm); bm.free()
    for p in nm.polygons: p.use_smooth = True
    nm.materials.clear(); nm.materials.append(m)
    o = bpy.data.objects.new(name, nm); body.users_collection[0].objects.link(o)
    o.parent = rig; o.matrix_world = body.matrix_world.copy()
    for g in body.vertex_groups: o.vertex_groups.new(name=g.name)
    # copy weights by nearest source vertex (topology was a subset, indices changed)
    from mathutils.kdtree import KDTree
    kd = KDTree(len(me.vertices))
    for v in me.vertices: kd.insert(v.co, v.index)
    kd.balance()
    for v in nm.vertices:
        co, idx, dd = kd.find(v.co - v.normal * offs(v.co))
        for g in _orig.vertices[idx].groups:
            o.vertex_groups[g.group].add([v.index], g.weight, 'REPLACE')
    if disp:
        d = o.modifiers.new("Folds", "DISPLACE"); d.texture = disp[0]; d.strength = disp[1]; d.mid_level = 0.5; d.texture_coords = 'LOCAL'
    a = o.modifiers.new("Armature", "ARMATURE"); a.object = rig
    cs = o.modifiers.new("CorrSmooth", "CORRECTIVE_SMOOTH"); cs.iterations = 6; cs.use_only_smooth = False
    so = o.modifiers.new("Solidify", "SOLIDIFY"); so.thickness = thick; so.offset = 1.0; so.use_rim = True
    if subsurf: sb = o.modifiers.new("Subsurf", "SUBSURF"); sb.levels = 1; sb.render_levels = 1
    return o, keep
chest_z = neck_z - 0.18
def top_off(co):
    base = 0.016
    if co.z < chest_z: base += 0.028 * min(1.0, (chest_z - co.z) / 0.35)      # loose drape over the belly to the hem
    if abs(co.x) > 0.2: base = 0.014 + 0.012 * min(1.0, (abs(co.x) - 0.2) / 0.4)  # sleeves widen toward the cuff
    return base
top, k_top = garment("Surgeon_ScrubTop", in_top, top_off, M_SCRUB, smooth=10, thick=0.004)
pants, k_p = garment("Surgeon_ScrubPants", in_trousers, lambda co: 0.012 + 0.01 * min(1.0, max(0.0, (hip_z - 0.3 - co.z) / 0.5)), M_PANTS, smooth=6, thick=0.004)
cap, k_c = garment("Surgeon_Cap", in_cap, lambda co: 0.007 + 0.012 * max(0.0, min(1.0, (co.z - brow_z) / 0.08)), M_CAP, smooth=4, thick=0.003, disp=(tex2, 0.004))
# ---- mask: a parametric sheet, cylindrically projected onto the face, relaxed taut (tents over nose and lips)
from mathutils.bvhtree import BVHTree
_bv = BVHTree.FromPolygons([v.co for v in me.vertices], [p.vertices[:] for p in me.polygons if not any(i in helper for i in p.vertices)])
ax_c = Vector((0.0, head_c.y + 0.03, 0.0)); NU, NV = 28, 18
z_top0 = nose_tip.z + 0.016; z_bot = nose_tip.z - 0.088
def mpt(u, v):            # u: -1..1 around the face, v: 0 top .. 1 bottom
    th = math.radians(78) * u
    zt = z_top0 - 0.022 * abs(u) ** 1.5
    z = zt + (z_bot + 0.012 * abs(u) - zt) * v
    d = Vector((math.sin(th), -math.cos(th), 0.0))
    o = Vector((ax_c.x, ax_c.y, z)) + d * 0.3
    hit = _bv.ray_cast(o, -d, 0.35)
    if hit[0] is None: return None
    return hit[0] + hit[1].normalized() * 0.008
verts = []; grid = {}
for j in range(NV + 1):
    for i in range(NU + 1):
        q = mpt(-1 + 2 * i / NU, j / NV)
        if q is None: continue
        grid[(i, j)] = len(verts); verts.append(q)
faces = [(grid[(i, j)], grid[(i + 1, j)], grid[(i + 1, j + 1)], grid[(i, j + 1)]) for j in range(NV) for i in range(NU)
         if all(k in grid for k in ((i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1)))]
mm = bpy.data.meshes.new("Surgeon_Mask"); mm.from_pydata(verts, [], faces)
bnd_m = {grid[k] for k in grid if k[0] in (0, NU) or k[1] in (0, NV)}
nbr = {i: [] for i in range(len(verts))}
for e in mm.edges: x_, y_ = e.vertices; nbr[x_].append(y_); nbr[y_].append(x_)
for it in range(120):
    co = [v.co.copy() for v in mm.vertices]
    for v in mm.vertices:
        if v.index in bnd_m or not nbr[v.index]: continue
        v.co = co[v.index] * 0.3 + sum((co[k] for k in nbr[v.index]), Vector()) * (0.7 / len(nbr[v.index]))
        loc, nrm, idx, dist = _bv.find_nearest(v.co)
        if loc is not None and (v.co - loc).dot(nrm) < 0.008: v.co = loc + nrm * 0.008
for p in mm.polygons: p.use_smooth = True
mm.materials.append(M_MASK)
mask = bpy.data.objects.new("Surgeon_Mask", mm); body.users_collection[0].objects.link(mask); mask.parent = rig
mask.matrix_world = body.matrix_world.copy()
vg = mask.vertex_groups.new(name="head"); vg.add(list(range(len(verts))), 1.0, 'REPLACE')
wv = bpy.data.textures.new("MaskPleats", "WOOD"); wv.wood_type = 'BANDS'; wv.noise_basis_2 = 'SIN'; wv.turbulence = 0.0
pl = mask.modifiers.new("Pleats", "DISPLACE"); pl.texture = wv; pl.strength = 0.0018; pl.texture_coords = 'LOCAL'
am = mask.modifiers.new("Armature", "ARMATURE"); am.object = rig
so = mask.modifiers.new("Solidify", "SOLIDIFY"); so.thickness = 0.0015; so.offset = 1.0
sb = mask.modifiers.new("Subsurf", "SUBSURF"); sb.levels = 1; sb.render_levels = 1
k_m = set()
# ---------------------------------------------------------------- hide body skin under garments (keep a 1.5 cm margin)
hid = body.vertex_groups.new(name="HiddenUnderClothes")
from mathutils.kdtree import KDTree
def interior(keep, margin):
    # vertices of `keep` farther than margin from any vertex not in keep (boundary)
    bnd = [v.co for v in me.vertices if v.index not in keep and v.index not in helper]
    kd = KDTree(len(bnd))
    for i, c in enumerate(bnd): kd.insert(c, i)
    kd.balance()
    return [i for i in keep if kd.find(me.vertices[i].co)[2] > margin]
ids = [i for i in interior(k_top, 0.045) if me.vertices[i].co.z < neck_z - 0.15] + interior(k_p, 0.04) + interior(k_c, 0.025)
hid.add(ids, 1.0, 'REPLACE')
mk = body.modifiers.new("HideUnderClothes", "MASK"); mk.vertex_group = hid.name; mk.invert_vertex_group = True
while body.modifiers.find(mk.name) > 1: bpy.ops.object.modifier_move_up({"object": body}, modifier=mk.name) if False else body.modifiers.move(body.modifiers.find(mk.name), body.modifiers.find(mk.name) - 1)
# ---------------------------------------------------------------- gloves: the body's own hands get the latex material
body.data.materials.append(M_GLOVE); gi = len(body.data.materials) - 1
for p in _orig.polygons:
    vs = [me.vertices[i] for i in p.vertices]
    if all(dom[v.index].startswith(HAND_B) or (dom[v.index].startswith("lowerarm") and near_wrist(v.co, 0.07)) for v in vs):
        _orig.polygons[p.index].material_index = gi
print("GARMENTS", len(top.data.vertices), len(pants.data.vertices), len(cap.data.vertices), len(mask.data.vertices), "hidden", len(ids))
print("REST", "neck_z", round(neck_z, 3), "hip_z", round(hip_z, 3), "brow_z", round(brow_z, 3), "nose", tuple(round(x, 3) for x in nose_tip))
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
