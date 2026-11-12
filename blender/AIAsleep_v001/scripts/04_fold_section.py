"""Epicanthic fold shape key + beat-9 anatomical cross-section of the upper lid / inner corner.
blender -b work/anim.blend --python scripts/04_fold_section.py -- work/film.blend"""
import sys, os, math, bpy, bmesh
from mathutils import Vector, Matrix
from mathutils.kdtree import KDTree
out = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene; O = bpy.data.objects
rig = O["Driver"]; body = O["Driver.body"]
# ---------------- fold: upper-lid skin near the medial canthus droops down and toward the nose over the inner corner
me = body.data
if not me.shape_keys: body.shape_key_add(name="Basis")
sk = body.shape_key_add(name="EpicanthicFold", from_mix=False)
eyeL = rig.data.bones["eye.L"].head_local; eyeR = rig.data.bones["eye.R"].head_local
kb = me.shape_keys.key_blocks; basis = kb[0]
mix = [v.co.copy() for v in me.vertices]
for k in kb[1:]:
    if k.name == "EpicanthicFold" or k.mute or k.value == 0: continue
    rel = k.relative_key
    for i in range(len(mix)): mix[i] += (k.data[i].co - rel.data[i].co) * k.value
n = 0
for c, sx in ((eyeL, -1), (eyeR, 1)):
    can = c + Vector((0.0125 * sx, -0.006, -0.001))       # medial canthus (toward the nose = toward x=0)
    for v in me.vertices:
        p = mix[v.index]; d = p - can
        if p.y > c.y - 0.003: continue                       # only the front of the lid region
        r = math.sqrt((d.x * 1.0) ** 2 + (d.z * 1.4) ** 2 + (d.y * 0.6) ** 2)
        if r > 0.011 or d.z < -0.0025: continue
        w = (1 - r / 0.011) ** 2
        up = max(0.0, min(1.0, (d.z + 0.0025) / 0.004))       # upper lid side carries the fold
        sk.data[v.index].co = basis.data[v.index].co + Vector((0.0009 * sx, -0.0006, -0.0021)) * w * up; n += 1
sk.value = 1.0
print("FOLD verts", n)
# ---------------- section (built from the evaluated head at frame 1800)
sc.frame_set(1800); bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get()
EYE = rig.matrix_world @ rig.pose.bones["eye.R"].head
CUT_X = EYE.x + 0.002                                      # sagittal plane just medial of the pupil, toward the inner corner
secc = bpy.data.collections.new("Section"); sc.collection.children.link(secc)
def mat(name, base, rough=0.45, sss=0.0, wave=None, vor=None, coat=0.0, pore=None):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; N = nt.nodes; L = nt.links
    b = N["Principled BSDF"]; b.inputs["Base Color"].default_value = (*base, 1); b.inputs["Roughness"].default_value = rough
    b.inputs["Subsurface Weight"].default_value = sss; b.inputs["Subsurface Radius"].default_value = (0.003, 0.0012, 0.0008); b.inputs["Subsurface Scale"].default_value = 0.3
    b.inputs["Coat Weight"].default_value = coat
    tc = N.new("ShaderNodeTexCoord"); tex = None
    if wave:
        tex = N.new("ShaderNodeTexWave"); tex.inputs["Scale"].default_value = wave; tex.inputs["Distortion"].default_value = 4; tex.inputs["Detail"].default_value = 6
        tex.bands_direction = "Z"
    elif vor:
        tex = N.new("ShaderNodeTexVoronoi"); tex.inputs["Scale"].default_value = vor
    elif pore:
        tex = N.new("ShaderNodeTexNoise"); tex.inputs["Scale"].default_value = pore; tex.inputs["Detail"].default_value = 8
    if tex:
        L.new(tc.outputs["Object"], tex.inputs[0]); fo = tex.outputs[1] if tex.bl_idname == "ShaderNodeTexWave" else tex.outputs[0]
        if tex.bl_idname == "ShaderNodeTexVoronoi": fo = tex.outputs["Distance"]
        cr = N.new("ShaderNodeMix"); cr.data_type = "RGBA"; cr.inputs[6].default_value = (*base, 1); cr.inputs[7].default_value = (base[0] * 0.6, base[1] * 0.45, base[2] * 0.4, 1)
        L.new(fo, cr.inputs[0]); L.new(cr.outputs[2], b.inputs["Base Color"])
        bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.6; bp.inputs["Distance"].default_value = 0.0002
        L.new(fo, bp.inputs["Height"]); L.new(bp.outputs[0], b.inputs["Normal"])
    return m
M_skin = mat("Sec_Skin", (0.62, 0.34, 0.24), 0.38, sss=0.7, coat=0.35, pore=4000)
M_musc = mat("Sec_Orbicularis", (0.38, 0.035, 0.03), 0.32, sss=0.35, wave=2500, coat=0.5)
M_fat = mat("Sec_OrbitalFat", (0.85, 0.52, 0.06), 0.22, sss=0.6, vor=900, coat=0.6)
M_tars = mat("Sec_Tarsus", (0.88, 0.80, 0.72), 0.35, sss=0.5, pore=3000, coat=0.4)
M_bone = mat("Sec_Bone", (0.66, 0.58, 0.44), 0.7, sss=0.1, vor=1800)
M_scl = mat("Sec_Sclera", (0.93, 0.90, 0.86), 0.18, sss=0.4, coat=0.9, pore=2500)
M_vit = mat("Sec_Vitreous", (0.16, 0.24, 0.30), 0.05, sss=0.9, coat=1.0)
M_lens = mat("Sec_Lens", (0.85, 0.72, 0.45), 0.04, sss=0.8, coat=1.0)
M_iris = mat("Sec_Iris", (0.16, 0.07, 0.03), 0.4, wave=6000)
def catmull_pts(pts, n=6):
    out_ = []
    P = [pts[0]] + pts + [pts[-1]]
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = [Vector(x) for x in P[i - 1:i + 3]]
        for k in range(n):
            t = k / n
            out_.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    out_.append(Vector(pts[-1])); return out_
def slab(name, poly2d, m, x0=-0.013, smooth_n=6, disp=0.0):
    """closed (y,z) profile relative to the eye centre, extruded from EYE.x+x0 to the cut plane"""
    pts = catmull_pts(poly2d + [poly2d[0]], smooth_n)[:-1]
    bm = bmesh.new()
    vs = [bm.verts.new((EYE.x + x0, EYE.y + p.x, EYE.z + p.y)) for p in pts]
    f = bm.faces.new(vs); bmesh.ops.triangulate(bm, faces=[f]) if False else None
    ex = bmesh.ops.extrude_face_region(bm, geom=[f]); nv = [g for g in ex["geom"] if isinstance(g, bmesh.types.BMVert)]
    for v in nv: v.co.x = CUT_X
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    me_ = bpy.data.meshes.new(name); bm.to_mesh(me_); bm.free()
    o = O.new(name, me_); secc.objects.link(o); me_.materials.append(m)
    bv = o.modifiers.new("bev", "BEVEL"); bv.width = 0.0003; bv.segments = 2; bv.limit_method = "ANGLE"
    rm = o.modifiers.new("rem", "REMESH"); rm.mode = "SMOOTH"; rm.octree_depth = 7; rm.use_smooth_shade = True; rm.use_remove_disconnected = False
    if disp:
        t = bpy.data.textures.new(name + "_t", "CLOUDS"); t.noise_scale = 0.0018
        d = o.modifiers.new("disp", "DISPLACE"); d.texture = t; d.strength = disp; d.texture_coords = "GLOBAL"
    sm = o.modifiers.new("sm", "SMOOTH"); sm.factor = 0.5; sm.iterations = 2
    return o
def band(name, centre, thick, m, **kw):
    """thick band along a centre polyline (offset toward +y = into the head)"""
    c = catmull_pts(centre, 4); left = []; right = []
    for i, p in enumerate(c):
        a_ = c[max(i - 1, 0)]; b_ = c[min(i + 1, len(c) - 1)]; t = (b_ - a_).normalized(); n_ = Vector((t.y, -t.x))
        if n_.x < 0: n_ = -n_
        left.append(p); right.append(p + n_ * thick)
    return slab(name, [tuple(v) for v in left + right[::-1]], m, smooth_n=1, **kw)
# upper lid skin with the fold: full upper lid that hangs down and overlaps the lid crease near the inner corner
SKIN_U = [(-0.0085, 0.030), (-0.0118, 0.022), (-0.0142, 0.0140), (-0.0151, 0.0075), (-0.0149, 0.0042), (-0.0141, 0.0030), (-0.0136, 0.0036), (-0.0137, 0.0012)]
band("Sec_SkinUpper", SKIN_U, 0.0011, M_skin, disp=0.00012)
band("Sec_MuscleUpper", [(-0.0076, 0.029), (-0.0107, 0.0215), (-0.0130, 0.0138), (-0.0139, 0.0080), (-0.0136, 0.0052)], 0.0011, M_musc)
slab("Sec_FatUpper", [(-0.0098, 0.0245), (-0.0118, 0.0150), (-0.0127, 0.0085), (-0.0118, 0.0060), (-0.0085, 0.0098), (-0.0030, 0.0128), (0.0040, 0.0136), (0.0060, 0.0180), (-0.0020, 0.0230)], M_fat, disp=0.0004)
slab("Sec_Tarsus", [(-0.0130, 0.0016), (-0.0128, 0.0058), (-0.0121, 0.0058), (-0.0122, 0.0016)], M_tars)
band("Sec_SkinLower", [(-0.0136, -0.0010), (-0.0134, -0.0060), (-0.0122, -0.0130), (-0.0095, -0.0220)], 0.0013, M_skin, disp=0.0001)
band("Sec_MuscleLower", [(-0.0122, -0.0035), (-0.0118, -0.0080), (-0.0105, -0.0135), (-0.0080, -0.0215)], 0.0011, M_musc)
slab("Sec_FatLower", [(-0.0108, -0.0090), (-0.0092, -0.0200), (-0.0030, -0.0215), (0.0020, -0.0165), (-0.0060, -0.0110)], M_fat, disp=0.0003)
slab("Sec_OrbitalRim", [(-0.0070, 0.0225), (-0.0040, 0.0320), (0.0110, 0.0330), (0.0140, 0.0240), (0.0040, 0.0195)], M_bone, disp=0.0003)
slab("Sec_OrbitalFloor", [(-0.0060, -0.0230), (0.0120, -0.0215), (0.0140, -0.0290), (-0.0040, -0.0300)], M_bone, disp=0.0003)
# eyeball: sclera shell + vitreous + lens + iris, cut by the same plane
def ball(name, r, m, centre=Vector((0, 0, 0)), scale=(1, 1, 1)):
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=64, v_segments=40, radius=r)
    for v in bm.verts: v.co = Vector((v.co.x * scale[0], v.co.y * scale[1], v.co.z * scale[2])) + EYE + centre
    res = bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=Vector((CUT_X, 0, 0)), plane_no=Vector((1, 0, 0)), clear_outer=True)
    edges = [e for e in bm.edges if e.is_boundary]
    if edges: bmesh.ops.edgeloop_fill(bm, edges=edges)
    me_ = bpy.data.meshes.new(name); bm.to_mesh(me_); bm.free()
    for p_ in me_.polygons: p_.use_smooth = True
    o = O.new(name, me_); secc.objects.link(o); me_.materials.append(m); return o
ball("Sec_Sclera", 0.0120, M_scl)
ball("Sec_Vitreous", 0.0112, M_vit, centre=Vector((CUT_X - EYE.x + 0.00005, 0, 0)) * 0)
ball("Sec_Cornea", 0.0078, M_vit, centre=Vector((0, -0.0058, 0)))
ball("Sec_Lens", 0.0046, M_lens, centre=Vector((0, -0.0072, 0)), scale=(1, 0.42, 1))
ball("Sec_Iris", 0.0062, M_iris, centre=Vector((0, -0.0093, 0)), scale=(1, 0.06, 1))
for o in secc.objects:
    if o.name in ("Sec_Vitreous", "Sec_Cornea"): o.location.x += 0.00004
skin = O["Sec_SkinUpper"]
# teal-to-navy studio backdrop + studio key/rim (only during the section)
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.12, segments=48, ring_count=24); bg = bpy.context.object; bg.name = "Sec_Backdrop"
for u in list(bg.users_collection): u.objects.unlink(bg)
secc.objects.link(bg); bg.location = EYE
mb = bpy.data.materials.new("Sec_BackdropGrad"); mb.use_nodes = True; N = mb.node_tree.nodes; L = mb.node_tree.links
for x in list(N):
    if x.type != "OUTPUT_MATERIAL": N.remove(x)
tc = N.new("ShaderNodeTexCoord"); sep = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs["Generated"], sep.inputs[0])
cr = N.new("ShaderNodeValToRGB"); cr.color_ramp.elements[0].color = (0.004, 0.012, 0.045, 1); cr.color_ramp.elements[1].color = (0.01, 0.20, 0.24, 1)
cr.color_ramp.elements[0].position = 0.25; cr.color_ramp.elements[1].position = 0.85
L.new(sep.outputs["Z"], cr.inputs[0]); em = N.new("ShaderNodeEmission"); L.new(cr.outputs[0], em.inputs[0]); em.inputs[1].default_value = 0.55
L.new(em.outputs[0], N["Material Output"].inputs[0]); bg.data.materials.append(mb)
lights = []
for nm, off, e, col in (("Sec_Key", (0.06, -0.05, 0.05), 0.4, (1.0, 0.93, 0.85)), ("Sec_Rim", (-0.02, 0.06, 0.06), 0.4, (0.4, 0.85, 1.0)), ("Sec_Fill", (0.06, -0.03, -0.05), 0.08, (0.7, 0.85, 1.0))):
    l = bpy.data.lights.new(nm, "AREA"); l.size = 0.08; l.color = col; lo = O.new(nm, l); secc.objects.link(lo)
    lo.location = EYE + Vector(off); lo.rotation_euler = (EYE - lo.location).to_track_quat("-Z", "Y").to_euler(); lights.append((l, e))
# visibility timeline: dive in at 1806, back out at 2210
D0, D1 = 1806, 2210
def vis(o, f, show):
    o.hide_render = not show; o.keyframe_insert("hide_render", frame=f)
for o in secc.objects:
    pass
    vis(o, 1, False); vis(o, D0, True); vis(o, D1, False)
for o in O:
    if o.parent == rig or o.name in ("FaceMeshOverlay",):
        if o.name.startswith("Sec_"): continue
        vis(o, 1, True); vis(o, D0, False); vis(o, D1, True)
for l, e in lights:
    l.energy = 0; l.keyframe_insert("energy", frame=D0 - 1); l.energy = e; l.keyframe_insert("energy", frame=D0); l.keyframe_insert("energy", frame=D1 - 1); l.energy = 0; l.keyframe_insert("energy", frame=D1)
for ad in [o.animation_data for o in O if o.animation_data] + [l.animation_data for l, _ in lights if l.animation_data]:
    act = ad.action
    if not act: continue
    try: fcs = list(act.fcurves)
    except AttributeError: fcs = [fc for ly in act.layers for s in ly.strips for cb in s.channelbags for fc in cb.fcurves]
    for fc in fcs:
        if fc.data_path in ("hide_render", "energy") and (fc.data_path == "hide_render" or fc.id_data in [l for l, _ in lights] if False else fc.data_path == "hide_render"):
            for kp in fc.keyframe_points: kp.interpolation = "CONSTANT"
# camera: replace the beat-9 keys with the dive + section orbit (camera on the medial, cut side)
cam = O["FilmCam"]; aim = O["CamAim"]; camd = cam.data
def fcurves(idb):
    act = idb.animation_data.action
    try: return list(act.fcurves)
    except AttributeError: return [fc for ly in act.layers for s in ly.strips for cb in s.channelbags for fc in cb.fcurves]
for idb in (cam, aim, camd):
    for fc in fcurves(idb):
        for kp in [k for k in fc.keyframe_points if 1795 < k.co.x < 2250][::-1]: fc.keyframe_points.remove(kp)
CUTC = Vector((CUT_X, EYE.y - 0.004, EYE.z + 0.002))
V = Vector
KEYS = [(1803, EYE + V((0.006, -0.026, 0.004)), EYE + V((0.009, -0.01, 0.003)), 40),     # into the skin at the inner corner (<=6 frames)
        (1830, CUTC + V((0.055, -0.035, 0.006)), CUTC, 30),
        (1900, CUTC + V((0.060, -0.010, 0.020)), CUTC + V((0, -0.003, 0.002)), 30),
        (1980, CUTC + V((0.050, -0.030, 0.030)), CUTC + V((0, -0.006, 0.005)), 34),
        (2060, CUTC + V((0.058, -0.018, -0.016)), CUTC + V((0, -0.006, 0.004)), 34),
        (2140, CUTC + V((0.040, -0.048, 0.012)), CUTC + V((0, -0.008, 0.004)), 32),
        (2200, EYE + V((0.008, -0.075, 0.004)), EYE + V((0.004, 0, 0)), 40)]
for f, p, a, l in KEYS:
    cam.location = p; cam.keyframe_insert("location", frame=f); aim.location = a; aim.keyframe_insert("location", frame=f); camd.lens = l; camd.keyframe_insert("lens", frame=f)
for idb in (cam, aim, camd):
    for fc in fcurves(idb):
        for kp in fc.keyframe_points: kp.handle_left_type = kp.handle_right_type = "AUTO"
        fc.update()
for fc in fcurves(camd):
    if "fstop" in fc.data_path:
        for kp in fc.keyframe_points: kp.interpolation = "LINEAR"
bpy.ops.wm.save_as_mainfile(filepath=out); print("SAVED", out, "CUT_X", CUT_X, "EYE", EYE)
