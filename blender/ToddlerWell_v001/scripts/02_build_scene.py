"""ToddlerWell set: field, 15 m well shaft with clean cross-section, pit, tripod, tape, excavator, trees, props, sky.
blender -b work/cast.blend --python scripts/02_build_scene.py -- work/scene.blend
Run from blender/ToddlerWell_v001/."""
import sys, os, math, random
import bpy, bmesh
from mathutils import Vector, Matrix

OUT = sys.argv[sys.argv.index("--") + 1]
HERE = os.path.abspath(".")
A = os.path.join(HERE, "assets")
R_ = math.radians
random.seed(17)
sc = bpy.context.scene
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1080, 1920, 100
sc.render.fps, sc.render.fps_base = 60, 1.0
sc.frame_start, sc.frame_end = 1, 1950
sc.render.engine = "CYCLES"; sc.cycles.device = "CPU"
sc.cycles.samples = 48; sc.cycles.adaptive_threshold = 0.05; sc.cycles.use_denoising = True; sc.cycles.denoiser = "OPENIMAGEDENOISE"
sc.render.use_motion_blur = True; sc.render.motion_blur_shutter = 0.5
sc.view_settings.view_transform = "AgX"; sc.view_settings.look = "AgX - Medium High Contrast"
sc.cycles.max_bounces = 8; sc.cycles.transparent_max_bounces = 16

SHAFT_R = 0.29
DEPTH = 15.24          # 50 ft
PIT_C = Vector((1.75, 0.35)); PIT_R = 1.05

def coll(name):
    c = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if c.name not in sc.collection.children: sc.collection.children.link(c)
    return c
C_SET = coll("SET"); C_PROPS = coll("PROPS"); C_VEG = coll("VEG"); C_FX = coll("FX")
C_CAST = coll("CAST")
for o in list(sc.collection.objects):
    sc.collection.objects.unlink(o); C_CAST.objects.link(o)

def link(o, c):
    for cc in o.users_collection: cc.objects.unlink(o)
    c.objects.link(o); return o

def tex(path, cs="sRGB"):
    im = bpy.data.images.load(path, check_existing=True)
    if cs != "sRGB": im.colorspace_settings.name = "Non-Color"
    return im

def ph(asset, kind):
    d = os.path.join(A, "ph", asset, "textures")
    for f in sorted(os.listdir(d)):
        if kind in f: return os.path.join(d, f)

def new_mat(name):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    return m, nt, out

def cutaway(nt, shader_out, out):
    """back faces transparent: from inside the earth (cross-section camera) the near soil disappears"""
    geo = nt.nodes.new("ShaderNodeNewGeometry"); tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    mx = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(geo.outputs["Backfacing"], mx.inputs[0]); nt.links.new(shader_out, mx.inputs[1]); nt.links.new(tr.outputs[0], mx.inputs[2])
    nt.links.new(mx.outputs[0], out.inputs["Surface"])

def pbr(nt, asset, scale, coord="UV", tint=None, rough_mul=1.0, bump=0.6, disp_bump=True, extra_col=None):
    """returns principled node, wired with diffuse/rough/normal of a Poly Haven texture set"""
    tc = nt.nodes.new("ShaderNodeTexCoord"); mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (scale, scale, scale)
    nt.links.new(tc.outputs[coord], mp.inputs["Vector"])
    bs = nt.nodes.new("ShaderNodeBsdfPrincipled")
    def img(kind, cs):
        p = ph(asset, kind)
        if not p: return None
        n = nt.nodes.new("ShaderNodeTexImage"); n.image = tex(p, cs)
        if coord == "Object": n.projection = "BOX"; n.projection_blend = 0.3
        nt.links.new(mp.outputs[0], n.inputs[0]); return n
    d = img("diff", "sRGB"); r = img("rough", "nc"); nm = img("nor_gl", "nc")
    col = d.outputs["Color"]
    if tint is not None:
        mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = "RGBA"; mx.blend_type = "MULTIPLY"; mx.inputs["Factor"].default_value = 1
        nt.links.new(col, mx.inputs["A"]); mx.inputs["B"].default_value = (*tint, 1); col = mx.outputs["Result"]
    if extra_col: col = extra_col(col)
    nt.links.new(col, bs.inputs["Base Color"])
    if r: nt.links.new(r.outputs["Color"], bs.inputs["Roughness"])
    if nm and coord == "UV":
        nmap = nt.nodes.new("ShaderNodeNormalMap"); nmap.inputs["Strength"].default_value = bump
        nt.links.new(nm.outputs["Color"], nmap.inputs["Color"]); nt.links.new(nmap.outputs[0], bs.inputs["Normal"])
    elif coord == "Object":
        b = nt.nodes.new("ShaderNodeBump"); b.inputs["Strength"].default_value = 0.35 * bump; b.inputs["Distance"].default_value = 0.02
        nt.links.new(d.outputs["Color"], b.inputs["Height"]); nt.links.new(b.outputs[0], bs.inputs["Normal"])
    return bs

# ------------------------------------------------------------------ materials
def ground_mat():
    m, nt, out = new_mat("M_Ground")
    def depthmix(col):
        # deeper than 8 cm (inside the dug pit) -> moist soil colour
        tc = nt.nodes.new("ShaderNodeTexCoord"); sep = nt.nodes.new("ShaderNodeSeparateXYZ")
        nt.links.new(tc.outputs["Object"], sep.inputs[0])
        mr = nt.nodes.new("ShaderNodeMapRange"); mr.inputs[1].default_value = -0.05; mr.inputs[2].default_value = -0.4
        nt.links.new(sep.outputs["Z"], mr.inputs[0])
        mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = "RGBA"; mx.blend_type = "MULTIPLY"
        nt.links.new(mr.outputs[0], mx.inputs["Factor"]); nt.links.new(col, mx.inputs["A"]); mx.inputs["B"].default_value = (0.45, 0.33, 0.24, 1)
        # large-scale colour variation so the field is not a repeating tile
        nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 0.08; nt.links.new(tc.outputs["Object"], nz.inputs[0])
        mx2 = nt.nodes.new("ShaderNodeMix"); mx2.data_type = "RGBA"; mx2.blend_type = "OVERLAY"; mx2.inputs["Factor"].default_value = 0.35
        nt.links.new(mx.outputs["Result"], mx2.inputs["A"]); nt.links.new(nz.outputs["Color"], mx2.inputs["B"])
        return mx2.outputs["Result"]
    bs = pbr(nt, "dry_ground_01", 0.33, coord="UV", tint=(0.66, 0.55, 0.42), extra_col=depthmix)
    cutaway(nt, bs.outputs[0], out); return m

def soil_mat(name, tint):
    m, nt, out = new_mat(name)
    def strata(col):
        tc = nt.nodes.new("ShaderNodeTexCoord"); sep = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(tc.outputs["Object"], sep.inputs[0])
        # strata bands: wave texture along Z, distorted
        wv = nt.nodes.new("ShaderNodeTexWave"); wv.wave_type = "BANDS"; wv.bands_direction = "Z"
        wv.inputs["Scale"].default_value = 0.11; wv.inputs["Distortion"].default_value = 3.5; wv.inputs["Detail"].default_value = 4; wv.inputs["Detail Scale"].default_value = 1.5
        nt.links.new(tc.outputs["Object"], wv.inputs[0])
        cr = nt.nodes.new("ShaderNodeValToRGB"); cr.color_ramp.elements[0].color = (0.5, 0.36, 0.25, 1); cr.color_ramp.elements[1].color = (1.1, 0.98, 0.8, 1)
        e = cr.color_ramp.elements.new(0.5); e.color = (0.75, 0.55, 0.38, 1)
        nt.links.new(wv.outputs["Fac"], cr.inputs[0])
        mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = "RGBA"; mx.blend_type = "MULTIPLY"; mx.inputs["Factor"].default_value = 1
        nt.links.new(col, mx.inputs["A"]); nt.links.new(cr.outputs[0], mx.inputs["B"])
        # darker and damper with depth
        mr = nt.nodes.new("ShaderNodeMapRange"); mr.inputs[1].default_value = 0; mr.inputs[2].default_value = -16
        mr.inputs[3].default_value = 1.0; mr.inputs[4].default_value = 0.55; nt.links.new(sep.outputs["Z"], mr.inputs[0])
        mx2 = nt.nodes.new("ShaderNodeMix"); mx2.data_type = "RGBA"; mx2.blend_type = "MULTIPLY"; mx2.inputs["Factor"].default_value = 1
        cv = nt.nodes.new("ShaderNodeCombineColor"); [nt.links.new(mr.outputs[0], cv.inputs[i]) for i in range(3)]
        nt.links.new(mx.outputs["Result"], mx2.inputs["A"]); nt.links.new(cv.outputs[0], mx2.inputs["B"])
        return mx2.outputs["Result"]
    bs = pbr(nt, "excavated_soil_wall", 0.5, coord="Object", tint=tint, extra_col=strata, bump=1.2)
    cutaway(nt, bs.outputs[0], out); return m

def simple_mat(name, rgb, rough=0.6, metal=0.0, emit=None, emit_s=0.0):
    m, nt, out = new_mat(name); bs = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bs.inputs["Base Color"].default_value = (*rgb, 1); bs.inputs["Roughness"].default_value = rough; bs.inputs["Metallic"].default_value = metal
    if emit: bs.inputs["Emission Color"].default_value = (*emit, 1); bs.inputs["Emission Strength"].default_value = emit_s
    nt.links.new(bs.outputs[0], out.inputs["Surface"]); return m

M_GROUND = ground_mat()
def strata_mat(name, ref_obj_name=None):
    """real soil profile: topsoil, dry clay, gravel bands, red laterite clay, sandy layers; wavy boundaries, moisture low down"""
    m, nt, out = new_mat(name)
    tc = nt.nodes.new("ShaderNodeTexCoord"); sep = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(tc.outputs["Object"], sep.inputs[0])
    nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 0.6; nz.inputs["Detail"].default_value = 6
    nt.links.new(tc.outputs["Object"], nz.inputs[0])
    mz = nt.nodes.new("ShaderNodeMath"); mz.operation = "MULTIPLY_ADD"; mz.inputs[1].default_value = 0.45; mz.inputs[2].default_value = -0.22
    nt.links.new(nz.outputs["Fac"], mz.inputs[0])
    zn = nt.nodes.new("ShaderNodeMath"); zn.operation = "ADD"; nt.links.new(sep.outputs["Z"], zn.inputs[0]); nt.links.new(mz.outputs[0], zn.inputs[1])
    def texset(asset, scale, tint=(1, 1, 1)):
        mp = nt.nodes.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (scale,) * 3; nt.links.new(tc.outputs["Object"], mp.inputs[0])
        out_ = {}
        for kind, cs in (("diff", "sRGB"), ("rough", "nc"), ("disp", "nc")):
            pth = ph(asset, kind)
            if not pth: continue
            n = nt.nodes.new("ShaderNodeTexImage"); n.image = tex(pth, cs); n.projection = "BOX"; n.projection_blend = 0.35
            nt.links.new(mp.outputs[0], n.inputs[0]); out_[kind] = n.outputs["Color"]
        if tint != (1, 1, 1):
            mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = "RGBA"; mx.blend_type = "MULTIPLY"; mx.inputs["Factor"].default_value = 1
            nt.links.new(out_["diff"], mx.inputs["A"]); mx.inputs["B"].default_value = (*tint, 1); out_["diff"] = mx.outputs["Result"]
        return out_
    L = [  # (top of band z, asset, scale, tint)
        (0.5, "forrest_ground_01", 0.9, (0.55, 0.45, 0.38)),      # dark topsoil with roots
        (-0.4, "excavated_soil_wall", 0.6, (1.0, 0.9, 0.75)),     # dry clay
        (-2.6, "gravelly_sand", 1.2, (0.85, 0.8, 0.72)),          # gravel band
        (-3.3, "red_laterite_soil_stones", 0.7, (1.0, 0.85, 0.75)),  # reddish clay
        (-7.2, "gravelly_sand", 0.9, (1.15, 1.05, 0.85)),         # sandy layer
        (-8.4, "excavated_soil_wall", 0.6, (0.8, 0.68, 0.55)),    # clay, darker
        (-11.6, "gravelly_sand", 1.3, (0.7, 0.65, 0.58)),         # gravel band
        (-12.4, "red_laterite_soil_stones", 0.7, (0.75, 0.6, 0.5)),  # wet laterite
    ]
    sets = [texset(a, sc_, t) for _, a, sc_, t in L]
    col = sets[0]["diff"]; rgh = sets[0].get("rough"); hgt = sets[0].get("disp")
    for (ztop, *_), st in zip(L[1:], sets[1:]):
        lt = nt.nodes.new("ShaderNodeMath"); lt.operation = "LESS_THAN"; lt.inputs[1].default_value = ztop; nt.links.new(zn.outputs[0], lt.inputs[0])
        for key in ("diff", "rough", "disp"):
            cur = {"diff": col, "rough": rgh, "disp": hgt}[key]
            if cur is None or key not in st: continue
            mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = "RGBA"; nt.links.new(lt.outputs[0], mx.inputs["Factor"])
            nt.links.new(cur, mx.inputs["A"]); nt.links.new(st[key], mx.inputs["B"])
            if key == "diff": col = mx.outputs["Result"]
            elif key == "rough": rgh = mx.outputs["Result"]
            else: hgt = mx.outputs["Result"]
    # moisture: darker and glossier deeper down
    mr = nt.nodes.new("ShaderNodeMapRange"); mr.inputs[1].default_value = -5; mr.inputs[2].default_value = -15; nt.links.new(sep.outputs["Z"], mr.inputs[0])
    dark = nt.nodes.new("ShaderNodeMix"); dark.data_type = "RGBA"; dark.blend_type = "MULTIPLY"; nt.links.new(mr.outputs[0], dark.inputs["Factor"])
    nt.links.new(col, dark.inputs["A"]); dark.inputs["B"].default_value = (0.55, 0.5, 0.45, 1)
    bs = nt.nodes.new("ShaderNodeBsdfPrincipled"); nt.links.new(dark.outputs["Result"], bs.inputs["Base Color"])
    if rgh is not None:
        rmul = nt.nodes.new("ShaderNodeMath"); rmul.operation = "MULTIPLY_ADD"; rmul.inputs[1].default_value = 1.0; rmul.inputs[2].default_value = 0.0
        nt.links.new(rgh, rmul.inputs[0]); nt.links.new(rmul.outputs[0], bs.inputs["Roughness"])
    bump = nt.nodes.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = 0.9; bump.inputs["Distance"].default_value = 0.04
    nt.links.new(hgt if hgt is not None else col, bump.inputs["Height"]); nt.links.new(bump.outputs[0], bs.inputs["Normal"])
    if ref_obj_name: tc.object = bpy.data.objects.get(ref_obj_name)
    cutaway(nt, bs.outputs[0], out); return m

M_SOIL = strata_mat("M_Soil")
M_SHAFT = strata_mat("M_ShaftWall")
M_SAND = bpy.data.materials.new("M_Sand"); M_SAND.use_nodes = True
_nt = M_SAND.node_tree; _nt.nodes.clear(); _o = _nt.nodes.new("ShaderNodeOutputMaterial")
_nt.links.new(pbr(_nt, "gravelly_sand", 3.0, coord="UV", tint=(0.6, 0.52, 0.42)).outputs[0], _o.inputs["Surface"])

# ------------------------------------------------------------------ earth blocks (cross-section ready)
def axis(lo, hi, dense_lo, dense_hi, fine, coarse):
    v = []; x = lo
    while x < hi - 1e-6:
        v.append(round(x, 4)); x += fine if dense_lo - 1e-6 <= x < dense_hi - 1e-6 else coarse
        if x > dense_lo and v[-1] < dense_lo: x = dense_lo
    v.append(hi); return sorted(set(v))

XS = axis(-40, 40, -4.0, 4.0, 0.05, 2.0)
def pit_bowl(x, y):
    d = math.hypot(x - PIT_C.x, y - PIT_C.y) / PIT_R
    if d >= 1 or y < 0: return 0.0
    return (1 - d * d) ** 0.7
def in_hole(x, y): return math.hypot(x, y) < SHAFT_R + 0.035

def earth_back():
    """top grid y in [0, 40] + front cut face at y=0 (with the slot for the shaft) ; shape key 'Pit' dents the top"""
    ys = axis(0, 40, 0.0, 4.0, 0.05, 2.0)
    zs = [0.0] + [-round(0.05 * i, 3) for i in range(1, 31)] + [-1.5 - 0.5 * i for i in range(1, 38)]
    zs = sorted(set(z for z in zs if z >= -20.0), reverse=True)
    bm = bmesh.new(); uv = bm.loops.layers.uv.new("UVMap")
    top = {}
    for j, y in enumerate(ys):
        for i, x in enumerate(XS):
            top[i, j] = bm.verts.new((x, y, 0.0))
    for j in range(len(ys) - 1):
        for i in range(len(XS) - 1):
            cx, cy = (XS[i] + XS[i + 1]) / 2, (ys[j] + ys[j + 1]) / 2
            if in_hole(cx, cy): continue
            f = bm.faces.new((top[i, j], top[i + 1, j], top[i + 1, j + 1], top[i, j + 1])); f.material_index = 0
    front = {}
    for k, z in enumerate(zs):
        for i, x in enumerate(XS):
            front[i, k] = top[i, 0] if k == 0 else bm.verts.new((x, 0.0, z))
    for k in range(len(zs) - 1):
        for i in range(len(XS) - 1):
            cx, cz = (XS[i] + XS[i + 1]) / 2, (zs[k] + zs[k + 1]) / 2
            if abs(cx) < SHAFT_R and cz > -DEPTH: continue      # slot shows the far half of the pipe
            f = bm.faces.new((front[i, k + 1], front[i + 1, k + 1], front[i + 1, k], front[i, k])); f.material_index = 1
    for f in bm.faces:
        for l in f.loops: l[uv].uv = (l.vert.co.x, l.vert.co.y if f.material_index == 0 else l.vert.co.z)
    me = bpy.data.meshes.new("EarthBack"); bm.to_mesh(me); bm.free()
    for f in me.polygons: f.use_smooth = False
    ob = bpy.data.objects.new("EarthBack", me); C_SET.objects.link(ob)
    me.materials.append(M_GROUND); me.materials.append(M_SOIL)
    # Pit shape key (fully dug = 0.95 m deep); front face top edge follows the dent
    ob.shape_key_add(name="Basis"); sk = ob.shape_key_add(name="Pit")
    for v in me.vertices:
        x, y, z = v.co
        dz = -0.95 * pit_bowl(x, max(0.0, y) if y < 0.01 else y) if y > -1e-6 else 0.0
        if abs(y) < 1e-6 and z < 0:     # front face: lerp between the dented top and the bottom
            top_z = -0.95 * pit_bowl(x, 0.0001)
            dz = top_z * (1 - z / -20.0)
        sk.data[v.index].co.z = z + dz
    return ob

def earth_front():
    ys = axis(-40, 0, -4.0, 0.0, 0.05, 2.0); ys[-1] = -0.004     # offset from EarthBack's cut face (no coincident faces)
    zs = [0.0, -0.25, -0.5, -0.75, -1.0, -1.5, -3, -6, -10, -20]
    bm = bmesh.new(); uv = bm.loops.layers.uv.new("UVMap"); top = {}
    for j, y in enumerate(ys):
        for i, x in enumerate(XS): top[i, j] = bm.verts.new((x, y, 0.0))
    for j in range(len(ys) - 1):
        for i in range(len(XS) - 1):
            cx, cy = (XS[i] + XS[i + 1]) / 2, (ys[j] + ys[j + 1]) / 2
            if in_hole(cx, cy): continue
            f = bm.faces.new((top[i, j], top[i + 1, j], top[i + 1, j + 1], top[i, j + 1])); f.material_index = 0
    jl = len(ys) - 1; back = {}
    for k, z in enumerate(zs):
        for i, x in enumerate(XS): back[i, k] = top[i, jl] if k == 0 else bm.verts.new((x, -0.004, z))
    for k in range(len(zs) - 1):          # +y face (pit's front wall), normal +y
        for i in range(len(XS) - 1):
            cx = (XS[i] + XS[i + 1]) / 2
            if abs(cx) < SHAFT_R + 0.04: continue
            f = bm.faces.new((back[i, k], back[i + 1, k], back[i + 1, k + 1], back[i, k + 1])); f.material_index = 1
    bm.normal_update()
    for f in bm.faces:
        if f.material_index == 1 and f.normal.y < 0: f.normal_flip()
        if f.material_index == 0 and f.normal.z < 0: f.normal_flip()
        for l in f.loops: l[uv].uv = (l.vert.co.x, l.vert.co.y if f.material_index == 0 else l.vert.co.z)
    me = bpy.data.meshes.new("EarthFront"); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new("EarthFront", me); C_SET.objects.link(ob)
    me.materials.append(M_GROUND); me.materials.append(M_SOIL); return ob

EB = earth_back(); EF = earth_front()
# fix normals of EarthBack: top up, front face -y
bm = bmesh.new(); bm.from_mesh(EB.data); bm.normal_update()
for f in bm.faces:
    if f.material_index == 0 and f.normal.z < 0: f.normal_flip()
    if f.material_index == 1 and f.normal.y > 0: f.normal_flip()
bm.to_mesh(EB.data); bm.free()

# the earth surfaces are see-through from below, so they cast no shadows; a shadow-only slab + sleeve keeps the
# sun out of the underground (except down the shaft), and lets the cross-section fill light reach the cut face
for o in (EB, EF): o.visible_shadow = False
M_BLOCK = simple_mat("M_ShadowBlock", (0.1, 0.08, 0.06), 1.0)
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, -1.3)); BLK = link(bpy.context.object, C_SET); BLK.name = "ShadowSlab"; BLK.scale = (90, 90, 0.1)
bpy.ops.object.transform_apply(scale=True)
bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=SHAFT_R + 0.05, depth=2, location=(0, 0, -1.3)); cyl = bpy.context.object
md = BLK.modifiers.new("hole", "BOOLEAN"); md.object = cyl; bpy.context.view_layer.objects.active = BLK; bpy.ops.object.modifier_apply(modifier="hole"); bpy.data.objects.remove(cyl)
bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=SHAFT_R + 0.07, depth=1.3, end_fill_type="NOTHING", location=(0, 0, -0.66)); SLV = link(bpy.context.object, C_SET); SLV.name = "ShadowSleeve"
for o in (BLK, SLV):
    o.data.materials.append(M_BLOCK); o.visible_camera = False; o.visible_diffuse = False; o.visible_glossy = False; o.visible_transmission = False; o.visible_volume_scatter = False

# outer field beyond the earth blocks
bpy.ops.mesh.primitive_plane_add(size=900, location=(0, 0, -0.03)); FIELD = link(bpy.context.object, C_SET); FIELD.name = "FieldFar"
FIELD.data.materials.append(M_GROUND); FIELD.visible_shadow = False
for p in FIELD.data.polygons: pass
for l in FIELD.data.uv_layers[0].data: l.uv = (l.uv[0] * 900, l.uv[1] * 900)

# shaft tube (inward normals), sandy bottom, casing ring + flange
bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=SHAFT_R, depth=DEPTH, end_fill_type="NOTHING", location=(0, 0, -DEPTH / 2))
TUBE = link(bpy.context.object, C_SET); TUBE.name = "ShaftTube"
bpy.ops.object.mode_set(mode="EDIT"); bpy.ops.mesh.select_all(action="SELECT"); bpy.ops.mesh.subdivide(number_cuts=36)
bpy.ops.mesh.flip_normals(); bpy.ops.object.mode_set(mode="OBJECT")
for v in TUBE.data.vertices:      # irregular hand-bored wall
    a = math.atan2(v.co.y, v.co.x); z = v.co.z
    rr = 1 + 0.025 * math.sin(3 * a + z * 1.3) + 0.015 * math.sin(7 * a - z * 2.1) + 0.012 * math.sin(z * 5.0)
    rr = min(rr, 1.0) if z > -0.9 else rr
    v.co.x *= rr; v.co.y *= rr
TUBE.data.materials.append(M_SHAFT); TUBE.visible_shadow = False
for nd in M_SHAFT.node_tree.nodes:
    if nd.type == "TEX_COORD": nd.object = EB   # the shadow slab + sleeve do its shadowing
uvl = TUBE.data.uv_layers[0]
for p in TUBE.data.polygons:
    p.use_smooth = True
    for li in p.loop_indices:
        co = TUBE.data.vertices[TUBE.data.loops[li].vertex_index].co
        uvl.data[li].uv = (math.atan2(co.y, co.x) * SHAFT_R, co.z)
bpy.ops.mesh.primitive_circle_add(vertices=64, radius=SHAFT_R * 1.05, fill_type="NGON", location=(0, 0, -DEPTH + 0.01))
FLOOR = link(bpy.context.object, C_SET); FLOOR.name = "ShaftFloor"; FLOOR.data.materials.append(M_SAND)
bpy.ops.object.mode_set(mode="EDIT"); bpy.ops.mesh.subdivide(number_cuts=6); bpy.ops.object.mode_set(mode="OBJECT")
for v in FLOOR.data.vertices: v.co.z += 0.06 * max(0, 1 - (v.co.xy.length / SHAFT_R) ** 2) + 0.01 * math.sin(v.co.x * 40)

M_RUST = bpy.data.materials.new("M_Casing"); M_RUST.use_nodes = True
nt = M_RUST.node_tree; nt.nodes.clear(); out = nt.nodes.new("ShaderNodeOutputMaterial")
bsr = nt.nodes.new("ShaderNodeBsdfPrincipled"); bsr.inputs["Base Color"].default_value = (0.28, 0.16, 0.09, 1); bsr.inputs["Metallic"].default_value = 0.5; bsr.inputs["Roughness"].default_value = 0.7
nt.links.new(bsr.outputs[0], out.inputs["Surface"])
bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=SHAFT_R + 0.025, depth=0.95, location=(0, 0, 0.12 - 0.475))
CAS = link(bpy.context.object, C_SET); CAS.name = "Casing"
md = CAS.modifiers.new("hollow", "BOOLEAN")
bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=SHAFT_R - 0.005, depth=3, location=(0, 0, 0)); cut = bpy.context.object
md.object = cut; bpy.context.view_layer.objects.active = CAS; bpy.ops.object.modifier_apply(modifier="hollow"); bpy.data.objects.remove(cut)
CAS.data.materials.clear(); CAS.data.materials.append(M_RUST)
bpy.ops.mesh.primitive_torus_add(major_radius=SHAFT_R + 0.03, minor_radius=0.018, location=(0, 0, 0.12)); lip = link(bpy.context.object, C_SET); lip.name = "CasingLip"; lip.data.materials.append(M_RUST)
# concrete-ish collar / packed dirt mound hiding the stepped grid hole
bpy.ops.mesh.primitive_circle_add(vertices=64, radius=0.62, fill_type="NOTHING", location=(0, 0, 0)); col_ = link(bpy.context.object, C_SET); col_.name = "DirtCollar"
bm = bmesh.new(); bm.from_mesh(col_.data)
outer = list(bm.verts); inner = [bm.verts.new((v.co.x * (SHAFT_R + 0.026) / 0.62, v.co.y * (SHAFT_R + 0.026) / 0.62, 0.05)) for v in outer]
mid = [bm.verts.new((v.co.x * 0.42 / 0.62, v.co.y * 0.42 / 0.62, 0.035)) for v in outer]
for i in range(len(outer)):
    j = (i + 1) % len(outer)
    bm.faces.new((outer[i], outer[j], mid[j], mid[i])); bm.faces.new((mid[i], mid[j], inner[j], inner[i]))
for v in outer: v.co.z = -0.005
bm.normal_update()
for f in bm.faces:
    if f.normal.z < 0: f.normal_flip()
bm.to_mesh(col_.data); bm.free(); col_.data.materials.append(M_GROUND)
for p in col_.data.polygons: p.use_smooth = True
col_.data.uv_layers.new(); [setattr(l, "uv", (col_.data.vertices[col_.data.loops[i].vertex_index].co.x, col_.data.vertices[col_.data.loops[i].vertex_index].co.y)) for i, l in enumerate(col_.data.uv_layers[0].data)]

# roots poking out of the shaft wall + trickling sand ribbons
M_ROOT = simple_mat("M_Root", (0.32, 0.22, 0.14), 0.8)
for i in range(22):
    z = -random.uniform(0.6, DEPTH - 1.0); a = random.uniform(0, 2 * math.pi)
    cu = bpy.data.curves.new("root", "CURVE"); cu.dimensions = "3D"; cu.bevel_depth = random.uniform(0.004, 0.012); cu.bevel_resolution = 2
    sp = cu.splines.new("BEZIER"); sp.bezier_points.add(2)
    L = random.uniform(0.06, 0.16)
    for k, t in enumerate((0.0, 0.5, 1.0)):
        r = SHAFT_R + 0.02 - L * t
        aa = a + 0.4 * t * random.uniform(-1, 1)
        p = sp.bezier_points[k]; p.co = (r * math.cos(aa), r * math.sin(aa), z - 0.06 * t * t + random.uniform(-0.02, 0.02)); p.handle_left_type = p.handle_right_type = "AUTO"
    sp.bezier_points[2].radius = 0.2
    ob = bpy.data.objects.new("Root%02d" % i, cu); C_SET.objects.link(ob); cu.materials.append(M_ROOT)

# ---- scanned stones embedded in the cut face and the shaft wall, roots near the top of the cut face
before = set(bpy.data.objects); bpy.ops.import_scene.gltf(filepath=os.path.join(A, "models/rocks.glb"))
rk = [o for o in bpy.data.objects if o not in before and o.type == "MESH"]
for o in [o for o in bpy.data.objects if o not in before]:
    if o.type == "MESH": mw = o.matrix_world.copy(); o.parent = None; o.matrix_world = mw
for o in [o for o in bpy.data.objects if o not in before and o.type != "MESH"]: bpy.data.objects.remove(o)
ROCKS = []
for o in rk:
    bpy.ops.object.select_all(action="DESELECT"); o.select_set(True); bpy.context.view_layer.objects.active = o
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    vs = [v.co for v in o.data.vertices]; c = sum(vs, Vector()) / len(vs); r = max((v - c).length for v in vs)
    for v in o.data.vertices: v.co = (v.co - c) / r
    o.name = "RockSrc"; link(o, C_SET); o.hide_render = True; o.hide_viewport = True; ROCKS.append(o)
    for m_ in o.data.materials:       # scans are pale grey: tint to the local soil
        if not m_ or m_.get("tinted"): continue
        m_["tinted"] = 1; bsd = [n for n in m_.node_tree.nodes if n.type == "BSDF_PRINCIPLED"][0]
        if bsd.inputs["Base Color"].is_linked:
            src_ = bsd.inputs["Base Color"].links[0].from_socket
            mx = m_.node_tree.nodes.new("ShaderNodeMix"); mx.data_type = "RGBA"; mx.blend_type = "MULTIPLY"; mx.inputs["Factor"].default_value = 1
            mx.inputs["B"].default_value = (0.55, 0.45, 0.36, 1); m_.node_tree.links.new(src_, mx.inputs["A"]); m_.node_tree.links.new(mx.outputs["Result"], bsd.inputs["Base Color"])
n = 0
while n < 90 and ROCKS:
    z = -random.uniform(0.15, 15.0) ** 1.0; x = random.uniform(-7, 7)
    if abs(x) < SHAFT_R + 0.15: continue
    s_ = random.uniform(0.04, 0.22) * (1.4 if z < -2.5 and random.random() < 0.3 else 1.0)
    o = bpy.data.objects.new("CutStone%02d" % n, random.choice(ROCKS).data); C_SET.objects.link(o)
    o.location = (x, -s_ * random.uniform(0.15, 0.45), z); o.scale = (s_, s_ * random.uniform(0.6, 1.0), s_ * random.uniform(0.5, 0.9))
    o.rotation_euler = (random.uniform(0, 6.3), random.uniform(0, 6.3), random.uniform(0, 6.3)); n += 1
for i in range(40):     # stones in the shaft wall, poking in
    a_ = random.uniform(0, 2 * math.pi); z = -random.uniform(0.9, 15.0); s_ = random.uniform(0.02, 0.04)
    o = bpy.data.objects.new("WallStone%02d" % i, random.choice(ROCKS).data); C_SET.objects.link(o)
    o.location = ((SHAFT_R + s_ * 0.75) * math.cos(a_), (SHAFT_R + s_ * 0.75) * math.sin(a_), z); o.scale = (s_,) * 3; o.rotation_euler = (a_, a_ * 2, a_ * 3)
for i in range(12):     # pebbles on the shaft floor
    a_ = random.uniform(0, 2 * math.pi); r_ = random.uniform(0, SHAFT_R - 0.05); s_ = random.uniform(0.012, 0.03)
    o = bpy.data.objects.new("FloorPebble%02d" % i, random.choice(ROCKS).data); C_SET.objects.link(o)
    o.location = (r_ * math.cos(a_), r_ * math.sin(a_), -DEPTH + 0.03); o.scale = (s_,) * 3
for i in range(34):     # roots on the cut face (top 1.4 m)
    x0 = random.uniform(-6, 6)
    if abs(x0) < SHAFT_R + 0.1: continue
    cu = bpy.data.curves.new("croot", "CURVE"); cu.dimensions = "3D"; cu.bevel_depth = random.uniform(0.003, 0.012); cu.bevel_resolution = 2
    sp = cu.splines.new("BEZIER"); k_ = random.randint(3, 5); sp.bezier_points.add(k_ - 1)
    z0 = -random.uniform(0.02, 0.4); x_ = x0
    for j in range(k_):
        bp = sp.bezier_points[j]; x_ += random.uniform(-0.15, 0.15)
        bp.co = (x_, -random.uniform(0.003, 0.02), z0 - j * random.uniform(0.15, 0.32)); bp.handle_left_type = bp.handle_right_type = "AUTO"; bp.radius = 1.0 - j / k_
    ob = bpy.data.objects.new("CutRoot%02d" % i, cu); C_SET.objects.link(ob); cu.materials.append(M_ROOT)

# sand trickle material: streaks moving down (mapping offset keyed in the animate step)
m, nt, out = new_mat("M_SandTrickle")
tc = nt.nodes.new("ShaderNodeTexCoord"); mp = nt.nodes.new("ShaderNodeMapping"); mp.name = "TrickleMap"
mp.inputs["Scale"].default_value = (40, 1, 4); nt.links.new(tc.outputs["UV"], mp.inputs[0])
nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 3; nz.inputs["Detail"].default_value = 4; nt.links.new(mp.outputs[0], nz.inputs[0])
ramp = nt.nodes.new("ShaderNodeValToRGB"); ramp.color_ramp.elements[0].position = 0.52; ramp.color_ramp.elements[1].position = 0.62; nt.links.new(nz.outputs["Fac"], ramp.inputs[0])
gr = nt.nodes.new("ShaderNodeTexGradient"); gr.gradient_type = "LINEAR"; nt.links.new(tc.outputs["UV"], gr.inputs[0])
mulw = nt.nodes.new("ShaderNodeMath"); mulw.operation = "MULTIPLY"
# fade across the ribbon width (u) with a sine bump
sepuv = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(tc.outputs["UV"], sepuv.inputs[0])
sn = nt.nodes.new("ShaderNodeMath"); sn.operation = "SINE"; mpi = nt.nodes.new("ShaderNodeMath"); mpi.operation = "MULTIPLY"; mpi.inputs[1].default_value = math.pi
nt.links.new(sepuv.outputs["X"], mpi.inputs[0]); nt.links.new(mpi.outputs[0], sn.inputs[0])
nt.links.new(ramp.outputs[0], mulw.inputs[0]); nt.links.new(sn.outputs[0], mulw.inputs[1])
bs = nt.nodes.new("ShaderNodeBsdfPrincipled"); bs.inputs["Base Color"].default_value = (0.6, 0.48, 0.34, 1); bs.inputs["Roughness"].default_value = 1
tr = nt.nodes.new("ShaderNodeBsdfTransparent"); mx = nt.nodes.new("ShaderNodeMixShader")
nt.links.new(mulw.outputs[0], mx.inputs[0]); nt.links.new(tr.outputs[0], mx.inputs[1]); nt.links.new(bs.outputs[0], mx.inputs[2]); nt.links.new(mx.outputs[0], out.inputs["Surface"])
M_TRICKLE = m
for i, (a, z0, z1) in enumerate(((0.6, -1.2, -6.0), (2.4, -4.0, -11.0), (4.1, -7.5, -DEPTH + 0.1), (5.3, -0.4, -3.5))):
    bpy.ops.mesh.primitive_plane_add(size=1); ob = link(bpy.context.object, C_SET); ob.name = "SandTrickle%d" % i
    r = SHAFT_R * 0.93
    ob.scale = (0.025, 1, (z0 - z1)); ob.location = (r * math.cos(a), r * math.sin(a), (z0 + z1) / 2)
    ob.rotation_euler = (R_(90), 0, a + R_(90)); ob.data.materials.append(M_TRICKLE)
    ob.visible_shadow = False

# dust volume inside the shaft (makes the head-torch beam visible)
bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=SHAFT_R * 0.97, depth=DEPTH - 0.3, location=(0, 0, -DEPTH / 2 - 0.1))
DV = link(bpy.context.object, C_FX); DV.name = "ShaftDust"
m, nt, out = new_mat("M_ShaftDust"); pv = nt.nodes.new("ShaderNodeVolumePrincipled"); pv.inputs["Density"].default_value = 0.06
pv.inputs["Color"].default_value = (0.9, 0.8, 0.65, 1); nt.links.new(pv.outputs[0], out.inputs["Volume"]); DV.data.materials.append(m)
DV.visible_shadow = False

# ------------------------------------------------------------------ rescue tripod with pulley
def pbr_mat(name, asset, scale, coord="UV", tint=None, metal=0.0):
    m, nt, out = new_mat(name); b = pbr(nt, asset, scale, coord=coord, tint=tint); b.inputs["Metallic"].default_value = metal
    nt.links.new(b.outputs[0], out.inputs["Surface"]); return m
M_WOOD = pbr_mat("M_TripodWood", "bark_brown_02", 1.0, coord="Object", tint=(0.9, 0.8, 0.7))
M_STEEL = pbr_mat("M_Steel", "rusty_metal_02", 3.0, coord="Object", metal=0.7)
M_CONCRETE = pbr_mat("M_Concrete", "concrete_wall_008", 1.5, coord="Object", tint=(0.5, 0.47, 0.43))
bpy.data.objects["DirtCollar"].data.materials[0] = M_CONCRETE
M_ROPE = bpy.data.materials.new("M_Rope"); M_ROPE.use_nodes = True
_nt = M_ROPE.node_tree; _bs = _nt.nodes["Principled BSDF"]; _bs.inputs["Base Color"].default_value = (0.74, 0.6, 0.36, 1); _bs.inputs["Roughness"].default_value = 0.85
_w = _nt.nodes.new("ShaderNodeTexWave"); _w.wave_type = "BANDS"; _w.bands_direction = "DIAGONAL"; _w.inputs["Scale"].default_value = 60; _tc = _nt.nodes.new("ShaderNodeTexCoord")
_nt.links.new(_tc.outputs["Object"], _w.inputs[0]); _bp = _nt.nodes.new("ShaderNodeBump"); _bp.inputs["Strength"].default_value = 0.6
_nt.links.new(_w.outputs["Fac"], _bp.inputs["Height"]); _nt.links.new(_bp.outputs[0], _bs.inputs["Normal"])
TOP = Vector((0, 0.05, 3.4))
TRI = bpy.data.objects.new("Tripod", None); C_PROPS.objects.link(TRI)
for k, ang in enumerate((R_(60), R_(180), R_(300))):
    foot = Vector((1.6 * math.cos(ang), 1.6 * math.sin(ang), 0.0))
    v = TOP - foot; L = v.length
    bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius=0.04, depth=L + 0.15)
    leg = link(bpy.context.object, C_PROPS); leg.name = "TripodLeg%d" % k
    leg.location = (foot + TOP) / 2 + v.normalized() * 0.075; leg.rotation_mode = "QUATERNION"
    leg.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(v.normalized()); leg.data.materials.append(M_WOOD); leg.parent = TRI
bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=0.11, depth=0.05, location=TOP + Vector((0, 0, -0.18)), rotation=(0, R_(90), 0))
PUL = link(bpy.context.object, C_PROPS); PUL.name = "Pulley"; PUL.data.materials.append(M_STEEL); PUL.parent = TRI
bpy.ops.mesh.primitive_cube_add(size=1, location=TOP + Vector((0, 0, -0.06))); hd = link(bpy.context.object, C_PROPS); hd.scale = (0.16, 0.24, 0.1); hd.name = "TripodHead"; hd.data.materials.append(M_STEEL); hd.parent = TRI
bv = hd.modifiers.new("bevel", "BEVEL"); bv.width = 0.015; bv.segments = 2
# hand winch on the +x+y leg: drum + crank + frame plates
lf = Vector((1.6 * math.cos(R_(60)), 1.6 * math.sin(R_(60)), 0)); wpos = lf.lerp(TOP, 0.33)
bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=0.075, depth=0.2, location=wpos + Vector((0.06, -0.05, 0)), rotation=(0, R_(90), R_(60)))
dr = link(bpy.context.object, C_PROPS); dr.name = "TripodWinchDrum"; dr.data.materials.append(M_ROPE); dr.parent = TRI
for k in (-1, 1):
    bpy.ops.mesh.primitive_cube_add(size=1, location=wpos + Vector((0.06, -0.05, 0)) + Matrix.Rotation(R_(60), 3, "Z") @ Vector((0.11 * k, 0, 0)))
    pl = link(bpy.context.object, C_PROPS); pl.name = "TripodWinchPlate%d" % k; pl.scale = (0.012, 0.2, 0.22); pl.rotation_euler = (0, 0, R_(60)); pl.data.materials.append(M_STEEL); pl.parent = TRI
bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius=0.012, depth=0.2, location=wpos + Vector((0.2, 0.08, 0.06)), rotation=(R_(90), 0, R_(60)))
ck = link(bpy.context.object, C_PROPS); ck.name = "TripodWinchCrank"; ck.data.materials.append(M_STEEL); ck.parent = TRI
for k_ in range(8):     # chain links hanging from the head
    bpy.ops.mesh.primitive_torus_add(major_radius=0.02, minor_radius=0.005, location=TOP + Vector((0.07, 0, -0.14 - 0.032 * k_)), rotation=(R_(90) * (k_ % 2), 0, 0))
    cl_ = link(bpy.context.object, C_PROPS); cl_.name = "TripodChain%d" % k_; cl_.data.materials.append(M_STEEL); cl_.parent = TRI

# ------------------------------------------------------------------ barrier tape on stakes
m, nt, out = new_mat("M_Tape"); tc = nt.nodes.new("ShaderNodeTexCoord"); wv = nt.nodes.new("ShaderNodeTexWave")
wv.wave_profile = "SAW"; wv.inputs["Scale"].default_value = 6; wv.inputs["Distortion"].default_value = 0; nt.links.new(tc.outputs["UV"], wv.inputs[0])
cr = nt.nodes.new("ShaderNodeValToRGB"); cr.color_ramp.interpolation = "CONSTANT"; cr.color_ramp.elements[0].color = (0.8, 0.05, 0.03, 1)
cr.color_ramp.elements[1].position = 0.5; cr.color_ramp.elements[1].color = (0.9, 0.9, 0.88, 1); nt.links.new(wv.outputs["Fac"], cr.inputs[0])
bs = nt.nodes.new("ShaderNodeBsdfPrincipled"); bs.inputs["Roughness"].default_value = 0.4; nt.links.new(cr.outputs[0], bs.inputs["Base Color"]); nt.links.new(bs.outputs[0], out.inputs["Surface"])
M_TAPE = m
STAKES = [Vector((-7.0 + 1.75 * i, 5.4 + 0.35 * math.cos(i * 0.9), 0)) for i in range(9)]
for i, s in enumerate(STAKES):
    bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=0.025, depth=1.05, location=s + Vector((0, 0, 0.48)))
    st = link(bpy.context.object, C_PROPS); st.name = "Stake%d" % i; st.data.materials.append(M_WOOD); st.rotation_euler = (random.uniform(-0.05, 0.05), random.uniform(-0.05, 0.05), 0)
cu = bpy.data.curves.new("Tape", "CURVE"); cu.dimensions = "3D"; cu.extrude = 0.035; cu.twist_mode = "Z_UP"
sp = cu.splines.new("POLY"); pts = []
for i in range(len(STAKES) - 1):
    a, b = STAKES[i], STAKES[i + 1]
    for t in (0, 0.25, 0.5, 0.75):
        p = a.lerp(b, t); p.z = 0.92 - 0.06 * math.sin(math.pi * t); pts.append(p)
pts.append(STAKES[-1] + Vector((0, 0, 0.92)))
sp.points.add(len(pts) - 1)
for p, q in zip(sp.points, pts): p.co = (*q, 1)
pass
TAPE = bpy.data.objects.new("Tape", cu); C_PROPS.objects.link(TAPE); cu.materials.append(M_TAPE)

# ------------------------------------------------------------------ rope coil, buckets, shovels, water bottles, cones
def import_unit(path, name, size, axis="z"):
    """import a GLB, join its meshes into one object with the base at z=0, scaled so its largest (or z) extent = size"""
    before = set(bpy.data.objects); bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    for o in new: o.animation_data_clear()
    meshes = [o for o in new if o.type == "MESH"]
    for o in meshes:
        mw = o.matrix_world.copy(); o.parent = None; o.matrix_world = mw
    for o in new:
        if o.type != "MESH": bpy.data.objects.remove(o)
    bpy.ops.object.select_all(action="DESELECT")
    for o in meshes: o.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    if len(meshes) > 1: bpy.ops.object.join()
    ob = bpy.context.object; bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    vs = [v.co for v in ob.data.vertices]
    mn = Vector((min(v.x for v in vs), min(v.y for v in vs), min(v.z for v in vs))); mx = Vector((max(v.x for v in vs), max(v.y for v in vs), max(v.z for v in vs)))
    ext = (mx - mn).z if axis == "z" else max(mx - mn)
    c = Vector(((mn.x + mx.x) / 2, (mn.y + mx.y) / 2, mn.z))
    for v in ob.data.vertices: v.co = (v.co - c) * (size / ext)
    ob.name = name; link(ob, LIB_SRC); return ob
LIB_SRC = bpy.data.collections.new("PropSources"); sc.collection.children.link(LIB_SRC); LIB_SRC.hide_render = True; LIB_SRC.hide_viewport = True
CONE_SRC = import_unit(os.path.join(A, "models/cone.glb"), "ConeSrc", 0.5)
COIL_SRC = import_unit(os.path.join(A, "models/ropecoil.glb"), "RopeCoilSrc", 0.5, axis="max")
for i, p in enumerate(((-4.6, 1.6), (3.6, 2.8), (-3.4, 3.2), (4.2, -2.2), (-5.5, -2.5), (6.8, -2.9))):
    o = bpy.data.objects.new("Cone%d" % i, CONE_SRC.data); C_PROPS.objects.link(o); o.location = (p[0], p[1], 0); o.rotation_euler.z = random.uniform(0, 6.3)
for i, p in enumerate(((-1.75, 1.25), (2.9, -1.4))):
    o = bpy.data.objects.new("RopeCoil%d" % i, COIL_SRC.data); C_PROPS.objects.link(o); o.location = (p[0], p[1], 0); o.rotation_euler.z = random.uniform(0, 6.3)
with bpy.data.libraries.load(os.path.join(A, "ph/wooden_bucket_01/wooden_bucket_01_1k.blend")) as (s, d): d.objects = s.objects
for o in d.objects:
    C_PROPS.objects.link(o); o.location = (-2.4, 1.6, 0) if "handle" not in o.name else o.location + Vector((-2.4, 1.6, 0))

# ------------------------------------------------------------------ excavator (CC-BY tori1243)
before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=os.path.join(A, "models/excavator.glb"))
new = [o for o in bpy.data.objects if o not in before]
for o in new: link(o, C_PROPS)
for a in list(bpy.data.actions):
    if a.name.startswith("Take"): bpy.data.actions.remove(a)
for o in new:
    o.animation_data_clear()
for n in ("left", "bottom", "back", "Object_5", "Object_7", "Object_9"):
    o = bpy.data.objects.get(n)
    if o:
        for ch in o.children_recursive: bpy.data.objects.remove(ch)
        bpy.data.objects.remove(o)
root = bpy.data.objects["Sketchfab_model"]; root.name = "ExcavatorRoot"
bpy.data.objects["Excavator"].name = "ExcavatorNode"
bpy.context.view_layer.update()
mn = Vector((1e9,) * 3); mx_ = Vector((-1e9,) * 3)
for o in root.children_recursive:
    if o.type == "MESH":
        for c in o.bound_box:
            w = o.matrix_world @ Vector(c); mn = Vector(map(min, mn, w)); mx_ = Vector(map(max, mx_, w))
print("EXC bbox", mn, mx_)
EXS = 2.1
ctrl = bpy.data.objects.new("Excavator", None); C_PROPS.objects.link(ctrl)
root.parent = ctrl; root.matrix_parent_inverse = Matrix.Translation(-Vector(((mn.x + mx_.x) / 2, (mn.y + mx_.y) / 2, mn.z)))
ctrl.scale = (EXS,) * 3; ctrl.location = (7.0, 1.0, 0); ctrl.rotation_euler = (0, 0, R_(90))
for nm in ("Body_GEO", "arm_01_GEO1", "Arm_2_GEO", "shovel_GEO", "claw_GEO", "Tread_GEO"):
    o = bpy.data.objects[nm]; o.rotation_mode = "XYZ"; print("EXCPART", nm, tuple(o.rotation_euler), tuple(o.location))

# ------------------------------------------------------------------ pickup in the background (CC-BY alban)
before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=os.path.join(A, "models/pickup.glb"))
new = [o for o in bpy.data.objects if o not in before]
for o in new: link(o, C_PROPS); o.animation_data_clear()
pr = [o for o in new if o.parent is None][0]; pr.name = "PickupRoot"
bpy.context.view_layer.update()
mn = Vector((1e9,) * 3); mx_ = Vector((-1e9,) * 3)
for o in new:
    if o.type == "MESH":
        for c in o.bound_box:
            w = o.matrix_world @ Vector(c); mn = Vector(map(min, mn, w)); mx_ = Vector(map(max, mx_, w))
L = max(mx_.x - mn.x, mx_.y - mn.y)
pk = bpy.data.objects.new("Pickup", None); C_PROPS.objects.link(pk)
pr.parent = pk; pr.matrix_parent_inverse = Matrix.Translation(-Vector(((mn.x + mx_.x) / 2, (mn.y + mx_.y) / 2, mn.z)))
pk.scale = (5.2 / L,) * 3; pk.location = (-8.5, 9.5, 0); pk.rotation_euler = (0, 0, R_(35))
print("PICKUP L", L)

# ------------------------------------------------------------------ vegetation (Poly Haven CC0)
def lib_objs(path, pred):
    with bpy.data.libraries.load(path) as (s, d): d.objects = [n for n in s.objects if pred(n)]
    return [o for o in d.objects if o]
def as_coll(name, objs):
    c = bpy.data.collections.new(name)
    for o in objs: c.objects.link(o)
    return c
tree_a = as_coll("TreeA", lib_objs(os.path.join(A, "ph/tree_small_02/tree_small_02_1k.blend"), lambda n: n.endswith("LOD1")))
tree_b = as_coll("TreeB", lib_objs(os.path.join(A, "ph/island_tree_02/island_tree_02_1k.blend"), lambda n: n.endswith("LOD1") and "island_tree_02" in n))
shrub = as_coll("Shrub", lib_objs(os.path.join(A, "ph/shrub_02/shrub_02_1k.blend"), lambda n: n.endswith("LOD1")))
grass_objs = lib_objs(os.path.join(A, "ph/grass_medium_01/grass_medium_01_1k.blend"), lambda n: n.endswith("LOD1"))
grass = [as_coll("Grass%d" % i, [o]) for i, o in enumerate(grass_objs[:8])]
for c in [tree_a, tree_b, shrub] + grass:
    for o in c.objects: o.location = (0, 0, 0) if o.parent is None else o.location
for c in (tree_a, tree_b):     # background trees (16-60 m away): decimate to keep the package small
    for o in c.objects:
        if o.type == "MESH" and len(o.data.vertices) > 20000:
            o.data = o.data.copy(); dm = o.modifiers.new("dec", "DECIMATE"); dm.ratio = 0.12
            sc.collection.objects.link(o); bpy.context.view_layer.update()
            dg = bpy.context.evaluated_depsgraph_get(); me = bpy.data.meshes.new_from_object(o.evaluated_get(dg))
            o.modifiers.clear(); o.data = me; sc.collection.objects.unlink(o)
LIB = bpy.data.collections.new("LIB"); sc.collection.children.link(LIB); LIB.hide_render = True; LIB.hide_viewport = True
for c in [tree_a, tree_b, shrub] + grass: LIB.children.link(c)
def inst(c, loc, rot, s, parent_coll):
    e = bpy.data.objects.new("i_" + c.name, None); e.instance_type = "COLLECTION"; e.instance_collection = c
    e.location = loc; e.rotation_euler = (0, 0, rot); e.scale = (s, s, s); parent_coll.objects.link(e); return e
for i in range(44):
    a = random.uniform(R_(10), R_(170)) if i < 18 else random.uniform(0, 2 * math.pi)
    r = random.uniform(16, 60)
    inst(tree_a if i % 2 else tree_b, (r * math.cos(a), r * math.sin(a), 0), random.uniform(0, 6.3), random.uniform(0.8, 1.3), C_VEG)
for i in range(30):
    a = random.uniform(0, 2 * math.pi); r = random.uniform(9, 30)
    inst(shrub, (r * math.cos(a), r * math.sin(a), 0), random.uniform(0, 6.3), random.uniform(0.6, 1.2), C_VEG)
def clear_zone(x, y):
    if math.hypot(x, y) < 3.2: return False
    if math.hypot(x - 4.8, y - 1.0) < 3.5: return False            # excavator
    if -9 < x < 9 and 4.6 < y < 9.5: return False                    # tape + crowd
    if -6 < x < 0 and -5 < y < 0 and abs((y + 0.0) - (x * 0.55)) < 1.0: return False   # toddler's walk line
    return True
n = 0
while n < 260:
    a = random.uniform(0, 2 * math.pi); r = 2.8 + random.expovariate(1 / 7.0)
    x, y = r * math.cos(a), r * math.sin(a)
    if r > 40 or not clear_zone(x, y): continue
    inst(random.choice(grass), (x, y, 0), random.uniform(0, 6.3), random.uniform(0.5, 1.1), C_VEG); n += 1

# ------------------------------------------------------------------ sky, sun, clouds, underground fill
w = bpy.data.worlds.new("World"); sc.world = w; w.use_nodes = True; nt = w.node_tree; nt.nodes.clear()
sky = nt.nodes.new("ShaderNodeTexSky"); sky.name = "Sky"; sky.sky_type = "MULTIPLE_SCATTERING"; sky.sun_disc = False
sky.sun_elevation = R_(55); sky.sun_rotation = R_(150); sky.altitude = 200; sky.air_density = 1.2
bg = nt.nodes.new("ShaderNodeBackground"); bg.inputs["Strength"].default_value = 0.35
wo = nt.nodes.new("ShaderNodeOutputWorld"); nt.links.new(sky.outputs[0], bg.inputs[0]); nt.links.new(bg.outputs[0], wo.inputs[0])
sd = bpy.data.lights.new("Sun", "SUN"); sd.energy = 3.0; sd.angle = R_(1.5); sd.color = (1.0, 0.95, 0.88)
SUN = bpy.data.objects.new("Sun", sd); C_SET.objects.link(SUN)
SUN.rotation_euler = (R_(90 - 55), 0, R_(150 - 90))
ld = bpy.data.lights.new("XsecFill", "AREA"); ld.shape = "RECTANGLE"; ld.size = 24; ld.size_y = 22; ld.energy = 0.0; ld.color = (1.0, 0.92, 0.82)
XL = bpy.data.objects.new("XsecFill", ld); C_SET.objects.link(XL); XL.location = (0, -9, -8.5); XL.rotation_euler = (R_(90), 0, 0)
XL.visible_camera = False; XL.visible_glossy = False
ld = bpy.data.lights.new("ShaftFill", "POINT"); ld.energy = 0.0; ld.shadow_soft_size = 0.1; ld.color = (1.0, 0.85, 0.65)
SF = bpy.data.objects.new("ShaftFill", ld); C_SET.objects.link(SF); SF.location = (0, 0, -DEPTH + 2.6); SF.visible_camera = False
SF2 = bpy.data.objects.new("ShaftFillMid", ld); C_SET.objects.link(SF2); SF2.location = (0.05, 0.05, -6.0); SF2.visible_camera = False
# clouds
bpy.ops.mesh.primitive_plane_add(size=6000, location=(0, 0, 900)); CL = link(bpy.context.object, C_SET); CL.name = "Clouds"
m, nt, out = new_mat("M_Clouds"); tc = nt.nodes.new("ShaderNodeTexCoord"); mp = nt.nodes.new("ShaderNodeMapping"); mp.name = "CloudMap"
nt.links.new(tc.outputs["Object"], mp.inputs[0]); mp.inputs["Scale"].default_value = (0.0012, 0.0012, 0.0012)
nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 3.0; nz.inputs["Detail"].default_value = 8; nz.inputs["Roughness"].default_value = 0.6
nt.links.new(mp.outputs[0], nz.inputs[0])
cr = nt.nodes.new("ShaderNodeValToRGB"); cr.color_ramp.elements[0].position = 0.55; cr.color_ramp.elements[1].position = 0.75; nt.links.new(nz.outputs["Fac"], cr.inputs[0])
tr = nt.nodes.new("ShaderNodeBsdfTransparent"); em = nt.nodes.new("ShaderNodeEmission"); em.name = "CloudEmit"; em.inputs["Strength"].default_value = 1.6
em.inputs["Color"].default_value = (1, 0.98, 0.95, 1)
mx = nt.nodes.new("ShaderNodeMixShader"); nt.links.new(cr.outputs[0], mx.inputs[0]); nt.links.new(tr.outputs[0], mx.inputs[1]); nt.links.new(em.outputs[0], mx.inputs[2])
nt.links.new(mx.outputs[0], out.inputs["Surface"]); CL.data.materials.append(m)
CL.visible_shadow = False; CL.visible_diffuse = False; CL.visible_glossy = False

# ------------------------------------------------------------------ head-worn items + hi-vis vests
def eval_co(ob):
    """vertex positions with shape keys applied (modifiers off -> same topology)"""
    st = [(m, m.show_viewport) for m in ob.modifiers]
    for m, _ in st: m.show_viewport = False
    bpy.context.view_layer.update(); dg = bpy.context.evaluated_depsgraph_get()
    me = ob.evaluated_get(dg).to_mesh(); co = [ob.matrix_world @ v.co for v in me.vertices]
    ob.evaluated_get(dg).to_mesh_clear()
    for m, v in st: m.show_viewport = v
    return co
def head_info(rig):
    body = [c for c in rig.children if c.name.endswith(".body")][0]
    hb = rig.data.bones["head"]
    vs = [c for c in eval_co(body) if c.z > (rig.matrix_world @ hb.head_local).z + 0.02]
    mn = Vector(map(min, *vs)) if False else Vector((min(v.x for v in vs), min(v.y for v in vs), min(v.z for v in vs)))
    mx = Vector((max(v.x for v in vs), max(v.y for v in vs), max(v.z for v in vs)))
    return mn, mx
def parent_bone(o, rig, bone):
    """Parent to the head bone, keeping its rest-pose placement (moves with the head)"""
    bpy.context.view_layer.update()
    mw = o.matrix_world.copy()
    o.parent = rig; o.parent_type = "BONE"; o.parent_bone = bone     # a real child of the head bone: worn, not a loose prop
    bpy.context.view_layer.update(); o.matrix_world = mw
HAT_SRC = None
before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=os.path.join(A, "models/hardhat.glb"))
hnew = [o for o in bpy.data.objects if o not in before and o.type == "MESH"]
bpy.ops.object.select_all(action="DESELECT")
for o in hnew: o.select_set(True)
bpy.context.view_layer.objects.active = hnew[0]
if len(hnew) > 1: bpy.ops.object.join()
HAT_SRC = bpy.context.object
mw_ = HAT_SRC.matrix_world.copy(); HAT_SRC.parent = None; HAT_SRC.matrix_world = mw_
for o in [o for o in bpy.data.objects if o not in before and o.type != "MESH"]:
    bpy.data.objects.remove(o)
HAT_SRC.parent = None; bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
hb_ = [Vector(c) for c in HAT_SRC.bound_box]; hmn = Vector((min(v.x for v in hb_), min(v.y for v in hb_), min(v.z for v in hb_))); hmx = Vector((max(v.x for v in hb_), max(v.y for v in hb_), max(v.z for v in hb_)))
print("HAT bbox", hmn, hmx)
HAT_C = Vector(((hmn.x + hmx.x) / 2, (hmn.y + hmx.y) / 2, hmn.z))
for v in HAT_SRC.data.vertices: v.co -= HAT_C
HAT_W = max(hmx.x - hmn.x, hmx.y - hmn.y); HAT_H = hmx.z - hmn.z
link(HAT_SRC, LIB) if False else None

M_VEST = bpy.data.materials.new("M_HiVis"); M_VEST.use_nodes = True
nt = M_VEST.node_tree; nt.nodes.clear(); out = nt.nodes.new("ShaderNodeOutputMaterial")
at = nt.nodes.new("ShaderNodeAttribute"); at.attribute_name = "band"
bs = nt.nodes.new("ShaderNodeBsdfPrincipled"); bs.inputs["Roughness"].default_value = 0.75
mixc = nt.nodes.new("ShaderNodeMix"); mixc.data_type = "RGBA"; mixc.inputs["A"].default_value = (0.75, 0.95, 0.05, 1); mixc.inputs["B"].default_value = (0.75, 0.76, 0.78, 1)
nt.links.new(at.outputs["Fac"], mixc.inputs["Factor"]); nt.links.new(mixc.outputs["Result"], bs.inputs["Base Color"])
mixm = nt.nodes.new("ShaderNodeMath"); mixm.operation = "MULTIPLY"; mixm.inputs[1].default_value = 0.7; nt.links.new(at.outputs["Fac"], mixm.inputs[0]); nt.links.new(mixm.outputs[0], bs.inputs["Metallic"])
bs.inputs["Emission Color"].default_value = (0.6, 0.85, 0.02, 1); bs.inputs["Emission Strength"].default_value = 0.08
nt.links.new(bs.outputs[0], out.inputs["Surface"])
M_VEST_OR = M_VEST.copy(); M_VEST_OR.name = "M_HiVisOrange"
M_VEST_OR.node_tree.nodes["Mix"].inputs["A"].default_value = (1.0, 0.35, 0.02, 1)
M_VEST_OR.node_tree.nodes["Principled BSDF"].inputs["Emission Color"].default_value = (1.0, 0.3, 0.0, 1)

def make_vest(rig, mat):
    cl = [c for c in rig.children if c.name.endswith(".body")][0]     # smooth closed torso -> clean vest
    B = rig.data.bones; M = rig.matrix_world
    z_lo = (M @ B["spine04"].head_local).z - 0.04; z_hi = (M @ B["neck01"].head_local).z - 0.02
    x_lim = abs((M @ B["upperarm01.L"].head_local).x - M.translation.x) * 0.8
    v = cl.copy(); v.data = cl.data.copy(); v.name = rig.name + ".vest"; C_CAST.objects.link(v)
    for m_ in list(v.modifiers):
        if m_.type != "ARMATURE": v.modifiers.remove(m_)
    co = eval_co(cl); Mi = v.matrix_world.inverted()
    if v.data.shape_keys:
        v.shape_key_clear()
    for vv in v.data.vertices: vv.co = Mi @ co[vv.index]
    bm = bmesh.new(); bm.from_mesh(v.data); cx = M.translation.x
    kill = [vv for vv in bm.verts if not (z_lo < (v.matrix_world @ vv.co).z < z_hi and abs((v.matrix_world @ vv.co).x - cx) < x_lim)]
    # (body mesh: also drop anything that is not torso - arms are outside x_lim, neck above z_hi)
    bmesh.ops.delete(bm, geom=kill, context="VERTS"); bm.to_mesh(v.data); bm.free()
    band = v.data.attributes.new("band", "FLOAT", "POINT")
    h = z_hi - z_lo
    for vv in v.data.vertices:
        t = ((v.matrix_world @ vv.co).z - z_lo) / h
        band.data[vv.index].value = 1.0 if (0.18 < t < 0.27 or 0.45 < t < 0.54) else 0.0
    v.data.materials.clear(); v.data.materials.append(mat)
    d = v.modifiers.new("vest_offset", "DISPLACE"); d.strength = 0.045; d.mid_level = 0.0
    bpy.context.view_layer.objects.active = v
    while v.modifiers[0].name != "vest_offset": bpy.ops.object.modifier_move_up(modifier="vest_offset")
    sm = v.modifiers.new("vest_smooth", "SMOOTH"); sm.factor = 0.9; sm.iterations = 12
    bpy.context.view_layer.objects.active = v
    while v.modifiers[1].name != "vest_smooth": bpy.ops.object.modifier_move_up(modifier="vest_smooth")
    s = v.modifiers.new("vest_thick", "SOLIDIFY"); s.thickness = 0.006
    ss = v.modifiers.new("vest_subd", "SUBSURF"); ss.levels = 1; ss.render_levels = 1
    return v

def make_hat(rig, color):
    mn, mx = head_info(rig)
    hw = max(mx.x - mn.x, mx.y - mn.y)
    s = hw * 1.22 / HAT_W
    h = HAT_SRC.copy(); h.data = HAT_SRC.data.copy(); h.name = rig.name + ".hardhat"; C_CAST.objects.link(h)
    h.scale = (s, s, s)
    h.location = Vector(((mn.x + mx.x) / 2, (mn.y + mx.y) / 2 + 0.005, mx.z + 0.025 - HAT_H * s))
    for m_ in h.data.materials:
        if m_ and m_.node_tree:
            for nd in m_.node_tree.nodes:
                if nd.type == "BSDF_PRINCIPLED" and not nd.inputs["Base Color"].is_linked: nd.inputs["Base Color"].default_value = (*color, 1)
    parent_bone(h, rig, "head"); return h

for nm, mat, hc in (("ResA", M_VEST, (1, 0.85, 0.1)), ("ResB", M_VEST_OR, (0.95, 0.95, 0.92)), ("ResC", M_VEST, (1, 0.5, 0.05))):
    rig = bpy.data.objects[nm]; make_vest(rig, mat); make_hat(rig, hc)
bpy.data.objects.remove(HAT_SRC)

# head torch on the teen: elastic strap + lamp + spot light, parented to the head bone
teen = bpy.data.objects["Teen"]; mn, mx = head_info(teen)
hc = Vector(((mn.x + mx.x) / 2, (mn.y + mx.y) / 2, 0)); hz = mn.z + (mx.z - mn.z) * 0.6
rx, ry = (mx.x - mn.x) / 2 * 1.04, (mx.y - mn.y) / 2 * 1.04
bpy.ops.mesh.primitive_torus_add(major_radius=1.0, minor_radius=0.012, major_segments=48, minor_segments=6, location=(0, 0, 0))
strap = link(bpy.context.object, C_CAST); strap.location = (hc.x, hc.y, hz); strap.name = "Teen.torch_strap"; strap.scale = (rx, ry, 1.0); strap.rotation_euler = (R_(-8), 0, 0)
strap.scale = (rx, ry, 1.0); bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
for v in strap.data.vertices: v.co.z = v.co.z * 1.0 + 0.0
for v in strap.data.vertices:       # flatten into a band
    v.co.z = (v.co.z) * 1.0
strap.data.materials.append(simple_mat("M_Strap", (0.05, 0.05, 0.06), 0.7))
bpy.ops.mesh.primitive_cylinder_add(vertices=20, radius=0.016, depth=0.024, location=(hc.x, mn.y - 0.004, hz + 0.005), rotation=(R_(90), 0, 0))
lamp = link(bpy.context.object, C_CAST); lamp.name = "Teen.torch_lamp"; lamp.data.materials.append(simple_mat("M_TorchBody", (0.1, 0.1, 0.11), 0.3, 0.5))
bpy.ops.mesh.primitive_circle_add(vertices=20, radius=0.012, fill_type="NGON", location=(hc.x, mn.y - 0.0165, hz + 0.005), rotation=(R_(90), 0, 0))
lens = link(bpy.context.object, C_CAST); lens.name = "Teen.torch_lens"
lens.data.materials.append(simple_mat("M_TorchLens", (1, 1, 1), 0.1, 0, (1, 0.95, 0.85), 0.0))
sl = bpy.data.lights.new("HeadTorch", "SPOT"); sl.energy = 0.0; sl.spot_size = R_(38); sl.spot_blend = 0.35; sl.shadow_soft_size = 0.01; sl.color = (1, 0.95, 0.85)
SL = bpy.data.objects.new("HeadTorch", sl); C_CAST.objects.link(SL); SL.location = (hc.x, mn.y - 0.022, hz + 0.005); SL.rotation_euler = (R_(-90 - 12), 0, 0)
for o in (strap, lamp, lens, SL): parent_bone(o, teen, "head")

# ------------------------------------------------------------------ ropes (curves, points keyed in the animate step)
def rope(name, n, radius=0.011):
    cu = bpy.data.curves.new(name, "CURVE"); cu.dimensions = "3D"; cu.bevel_depth = radius; cu.bevel_resolution = 2
    sp = cu.splines.new("POLY"); sp.points.add(n - 1)
    o = bpy.data.objects.new(name, cu); C_PROPS.objects.link(o); cu.materials.append(M_ROPE); return o
rope("RopeLoop", 40, 0.009)       # beat 2: lowered loop
rope("RopeMain", 60, 0.012)       # beats 6-11: haul line (haulers -> pulley -> teen's waist)
rope("RopeWaist", 24, 0.012)      # loop around the teen's waist

# camera
cd = bpy.data.cameras.new("Cam"); cd.lens = 24; cd.sensor_width = 36; cd.clip_start = 0.02; cd.clip_end = 3000
cd.dof.use_dof = True; cd.dof.aperture_fstop = 4.0
CAM = bpy.data.objects.new("Cam", cd); sc.collection.objects.link(CAM); sc.camera = CAM
TGT = bpy.data.objects.new("CamTarget", None); sc.collection.objects.link(TGT)
tc_ = CAM.constraints.new("TRACK_TO"); tc_.target = TGT; tc_.track_axis = "TRACK_NEGATIVE_Z"; tc_.up_axis = "UP_Y"
cd.dof.focus_object = TGT

# place cast off-stage for now
for i, nm in enumerate(("Toddler", "Teen", "ResA", "ResB", "ResC", "Mother", "Crowd1", "Crowd2", "Crowd3", "Crowd4")):
    bpy.data.objects[nm].location = (0, 0, 0)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, OUT))
print("SCENE SAVED", OUT)
