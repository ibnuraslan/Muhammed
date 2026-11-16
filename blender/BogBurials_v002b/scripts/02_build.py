"""BogBurials: sets, per-shot animation at 1x, one camera per shot with hard-cut markers, look.
blender -b lib.blend --python 02_build.py -- <out.blend>
Shot lengths come from shots.py (Phase 2: VO frames). Every shot is keyed from its own start frame."""
import bpy, sys, math, os, random, bmesh
from mathutils import Vector, Matrix, Euler, Quaternion
argv = sys.argv[sys.argv.index("--") + 1:]
OUT = argv[0]
HERE = "/home/user/Muhammed/blender/BogBurials_v002b/scripts"
BRAND = "/home/user/Muhammed/blender/assets/brand/"
PHD = "/tmp/claude-0/assets/ph/"
P = "/home/user/Muhammed/blender/pipeline/"
exec(open(P + "anim_lib.py").read()); exec(open(P + "hand_poses.py").read())
exec(open(HERE + "/shots.py").read()); exec(open(HERE + "/curl_pose.py").read()); exec(open(HERE + "/skel_bind.py").read())
R_ = math.radians
random.seed(33)
sc = bpy.context.scene
sc.render.fps = 60; sc.render.resolution_x = 1080; sc.render.resolution_y = 1920
lay = layout()
SH = {sid: (st, f0, f1) for sid, st, f0, f1 in lay}
FEND = lay[-1][3]
sc.frame_start = 1; sc.frame_end = FEND

def coll(name):
    c = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if c.name not in sc.collection.children: sc.collection.children.link(c)
    return c
def move_to(o, c):
    for uc in list(o.users_collection): uc.objects.unlink(o)
    c.objects.link(o)

# ------------------------------------------------------------------ materials / shapes
MATS = {}
def mat(name, rgb, rough=0.5, metal=0.0, emit=None, ew=0.0, alpha=1.0):
    if name in MATS: return MATS[name]
    m = bpy.data.materials.new(name); m.use_nodes = True
    p = m.node_tree.nodes["Principled BSDF"]
    p.inputs["Base Color"].default_value = (*rgb, 1); p.inputs["Roughness"].default_value = rough
    p.inputs["Metallic"].default_value = metal
    if emit:
        p.inputs["Emission Color"].default_value = (*emit, 1); p.inputs["Emission Strength"].default_value = ew
    if alpha < 1: p.inputs["Alpha"].default_value = alpha
    MATS[name] = m; return m

def tex_mat(name, tid, scale=1.0, tint=(1, 1, 1), bright=0.0, sat=1.0, rough=None, bump=0.3, box=False):
    """Poly Haven texture set, softened for the animated look (bump low, roughness >= 0.45)"""
    if name in MATS: return MATS[name]
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree
    p = nt.nodes["Principled BSDF"]
    d = PHD + tid + "/textures/"
    tc = nt.nodes.new("ShaderNodeTexCoord"); mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (scale, scale, scale)
    nt.links.new(tc.outputs["Object" if box else "UV"], mp.inputs["Vector"])
    def img(fn, nc=False):
        t = nt.nodes.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(d + fn, check_existing=True)
        if nc: t.image.colorspace_settings.name = "Non-Color"
        if box: t.projection = 'BOX'; t.projection_blend = 0.3
        nt.links.new(mp.outputs["Vector"], t.inputs["Vector"]); return t
    dif = img(f"{tid}_diff_1k.jpg")
    hs = nt.nodes.new("ShaderNodeHueSaturation"); hs.inputs["Saturation"].default_value = sat
    hs.inputs["Value"].default_value = 1.0 + bright
    nt.links.new(dif.outputs["Color"], hs.inputs["Color"])
    mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs["Factor"].default_value = 1.0
    mx.inputs["B"].default_value = (*tint, 1); nt.links.new(hs.outputs["Color"], mx.inputs["A"])
    nt.links.new(mx.outputs["Result"], p.inputs["Base Color"])
    p.inputs["Roughness"].default_value = rough if rough is not None else 0.8
    try:
        nf = [f for f in os.listdir(d) if "_nor_gl_" in f][0]
        nm = img(nf, True); nmn = nt.nodes.new("ShaderNodeNormalMap"); nmn.inputs["Strength"].default_value = bump
        nt.links.new(nm.outputs["Color"], nmn.inputs["Color"]); nt.links.new(nmn.outputs["Normal"], p.inputs["Normal"])
    except Exception as e:
        print("BUILD no normal", tid, e)
    if "Specular IOR Level" in p.inputs: p.inputs["Specular IOR Level"].default_value = 0.3
    MATS[name] = m; return m

def rbox(name, size, loc, m, c, bevel=0.02, rot=(0, 0, 0), seg=3):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    o = bpy.context.active_object; o.name = name; o.scale = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel:
        b = o.modifiers.new("bev", 'BEVEL'); b.width = bevel; b.segments = seg; b.limit_method = 'NONE'
    bpy.ops.object.shade_smooth()
    o.data.materials.append(m); move_to(o, c); return o

def cyl(name, r, depth, loc, m, c, rot=(0, 0, 0), verts=32):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=depth, location=loc, rotation=rot)
    o = bpy.context.active_object; o.name = name; bpy.ops.object.shade_smooth()
    o.data.materials.append(m); move_to(o, c); return o

def plane(name, size, loc, m, c, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_plane_add(size=1, location=loc, rotation=rot)
    o = bpy.context.active_object; o.name = name; o.scale = (size[0], size[1], 1)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    o.data.materials.append(m); move_to(o, c); return o

def dup(src, name, loc, rot=(0, 0, 0), scale=1.0, c=None, linked=True):
    o = src.copy()
    if not linked: o.data = src.data.copy()
    o.name = name; o.rotation_mode = 'XYZ'; o.location = loc; o.rotation_euler = rot
    o.scale = (scale, scale, scale) if isinstance(scale, (int, float)) else scale
    o.hide_render = o.hide_viewport = False
    (c or src.users_collection[0]).objects.link(o); return o

def area(name, loc, target, energy, size, c, color=(1, 1, 1)):
    L = bpy.data.lights.new(name, 'AREA'); L.energy = energy; L.size = size; L.color = color
    o = bpy.data.objects.new(name, L); c.objects.link(o); o.location = loc
    o.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler(); return o

def logo_decal(name, loc, rot, width, dark, c, parent=None):
    img = bpy.data.images.load(BRAND + ("DaKrasFilms_logo_dark.png" if dark else "DaKrasFilms_logo_white.png"), check_existing=True)
    m = bpy.data.materials.new(name + "_mat"); m.use_nodes = True; nt = m.node_tree
    pr = nt.nodes["Principled BSDF"]; tx = nt.nodes.new("ShaderNodeTexImage"); tx.image = img
    nt.links.new(tx.outputs["Color"], pr.inputs["Base Color"]); nt.links.new(tx.outputs["Alpha"], pr.inputs["Alpha"])
    pr.inputs["Roughness"].default_value = 0.5
    o = plane(name, (width, width * 414 / 967), loc, m, c, rot)
    if parent:
        mw = o.matrix_world.copy(); o.parent = parent; o.matrix_world = mw
    return o

def grid_terrain(name, size, n, zfun, m, c, origin=(0, 0)):
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    res = n
    vs = {}
    for i in range(res + 1):
        for j in range(res + 1):
            x = -size / 2 + size * i / res; y = -size / 2 + size * j / res
            vs[i, j] = bm.verts.new((x + origin[0], y + origin[1], zfun(x, y)))
    uv_l = bm.loops.layers.uv.new("UVMap")
    for i in range(res):
        for j in range(res):
            f = bm.faces.new((vs[i, j], vs[i + 1, j], vs[i + 1, j + 1], vs[i, j + 1]))
            for lp in f.loops:
                lp[uv_l].uv = (lp.vert.co.x / 2.0, lp.vert.co.y / 2.0)
    bm.to_mesh(me); bm.free()
    for p_ in me.polygons: p_.use_smooth = True
    o = bpy.data.objects.new(name, me); c.objects.link(o); o.data.materials.append(m); return o

def noise2(x, y, s=1.0):
    return (math.sin(x * 1.7 * s + 0.3) * math.cos(y * 1.3 * s + 1.1) * 0.5 + math.sin(x * 3.1 * s + y * 2.3 * s) * 0.25
            + math.sin(x * 7.3 * s - y * 5.9 * s + 2.0) * 0.08)

# ------------------------------------------------------------------ world: sky gradient seen by camera, soft light
w = bpy.data.worlds.new("Sky"); sc.world = w; w.use_nodes = True; nt = w.node_tree; nt.nodes.clear()
o_ = nt.nodes.new("ShaderNodeOutputWorld"); lp = nt.nodes.new("ShaderNodeLightPath")
tc = nt.nodes.new("ShaderNodeTexCoord"); sep = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(tc.outputs["Generated"], sep.inputs[0])
mr = nt.nodes.new("ShaderNodeMapRange"); mr.inputs["From Min"].default_value = -0.05; mr.inputs["From Max"].default_value = 0.5
nt.links.new(sep.outputs["Z"], mr.inputs["Value"])
ramp = nt.nodes.new("ShaderNodeValToRGB"); ramp.color_ramp.elements[0].color = (0.72, 0.90, 1.0, 1); ramp.color_ramp.elements[1].color = (0.10, 0.52, 0.95, 1)
nt.links.new(mr.outputs["Result"], ramp.inputs["Fac"])
# soft clouds
nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 3.0; nz.inputs["Detail"].default_value = 4.0
nt.links.new(tc.outputs["Generated"], nz.inputs["Vector"])
cr = nt.nodes.new("ShaderNodeMapRange"); cr.inputs["From Min"].default_value = 0.55; cr.inputs["From Max"].default_value = 0.72
nt.links.new(nz.outputs["Fac"], cr.inputs["Value"])
hz = nt.nodes.new("ShaderNodeMapRange"); hz.inputs["From Min"].default_value = 0.02; hz.inputs["From Max"].default_value = 0.2
nt.links.new(sep.outputs["Z"], hz.inputs["Value"])
cm = nt.nodes.new("ShaderNodeMath"); cm.operation = 'MULTIPLY'; nt.links.new(cr.outputs["Result"], cm.inputs[0]); nt.links.new(hz.outputs["Result"], cm.inputs[1])
cmix = nt.nodes.new("ShaderNodeMix"); cmix.data_type = 'RGBA'; nt.links.new(cm.outputs[0], cmix.inputs["Factor"])
nt.links.new(ramp.outputs["Color"], cmix.inputs["A"]); cmix.inputs["B"].default_value = (0.97, 0.98, 1.0, 1)
bg_cam = nt.nodes.new("ShaderNodeBackground"); nt.links.new(cmix.outputs["Result"], bg_cam.inputs["Color"]); bg_cam.inputs["Strength"].default_value = 1.0
bg_lit = nt.nodes.new("ShaderNodeBackground"); bg_lit.inputs["Color"].default_value = (0.85, 0.92, 1.0, 1); bg_lit.inputs["Strength"].default_value = 1.2
SUN = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", "SUN")); sc.collection.objects.link(SUN)
SUN.data.energy = 3.0; SUN.data.angle = R_(8); SUN.rotation_euler = (R_(35), R_(10), R_(30))
mix = nt.nodes.new("ShaderNodeMixShader"); nt.links.new(lp.outputs["Is Camera Ray"], mix.inputs["Fac"])
nt.links.new(bg_lit.outputs[0], mix.inputs[1]); nt.links.new(bg_cam.outputs[0], mix.inputs[2]); nt.links.new(mix.outputs[0], o_.inputs[0])

# ------------------------------------------------------------------ library objects
BURA = bpy.data.objects["BurA"]; BURB = bpy.data.objects["BurB"]; DEAD = bpy.data.objects["Dead"]
WORK = bpy.data.objects["Worker"]; ARCH = bpy.data.objects["Arch"]
WOLF = bpy.data.objects["Wolf_rig"]
SKEL = bpy.data.objects["Skeleton"]; BRAIN = bpy.data.objects["Brain"]; EXC = bpy.data.objects["Excavator"]
TRUCK = bpy.data.objects["Pickup"]; BRUSH = bpy.data.objects["Brush"]
PLANTS = {o.name: o for o in bpy.data.collections["PLANTS"].objects}
for o in PLANTS.values(): o.location = (0, 0, -80)
LIBC = bpy.data.collections["PLANTS"]
GRASS = [PLANTS[n] for n in ("PH_grass_medium_01_large_a_LOD0", "PH_grass_medium_01_large_b_LOD0", "PH_grass_medium_01_large_c_LOD0",
                             "PH_grass_medium_01_tall_a_LOD0", "PH_grass_medium_01_tall_b_LOD0", "PH_grass_medium_01_mid_a_LOD0")]
SHRUBS = [PLANTS[n] for n in ("PH_shrub_02_a_LOD1", "PH_shrub_02_b_LOD1", "PH_shrub_02_c_LOD1")]
TREE = PLANTS["PH_island_tree_02_LOD1"]; TREE_PARTS = [o for n, o in PLANTS.items() if n.startswith("PH_island_tree_02_") and n.endswith("LOD1")]
DEADTRUNK = PLANTS["PH_dead_tree_trunk"]; BRANCH = [PLANTS[n] for n in ("PH_dry_branches_medium_01_a", "PH_dry_branches_medium_01_b", "PH_dry_branches_medium_01_c")]
STUMP = PLANTS["PH_tree_stump_01"]

def scatter(srcs, n, c, region, zfun, scale=(0.8, 1.4), avoid=None, name="Sc"):
    out = []
    for k in range(n):
        for _ in range(30):
            x = random.uniform(region[0], region[1]); y = random.uniform(region[2], region[3])
            if avoid and avoid(x, y): continue
            break
        else:
            continue
        s = random.uniform(*scale)
        out.append(dup(random.choice(srcs), f"{name}{k}", (x, y, zfun(x, y) - 0.02), (0, 0, random.uniform(0, 6.28)), s, c))
    return out

def tree_at(name, loc, rot, s, c):
    for part in TREE_PARTS:
        dup(part, name + "_" + part.name[-12:], Vector(loc), (0, 0, rot), s, c)

# ================================================================== SET 1: bog (x=0). Water surface z=0.
CB = coll("SET_bog")
FLOOR = -0.70
def bog_z(x, y):
    r = math.hypot(x, y)
    t = smooth((r - 3.6) / 1.4)
    base = FLOOR + 0.03 * noise2(x, y, 2.0)
    bank = 0.15 + 0.10 * noise2(x, y, 0.6) + 0.03 * noise2(x, y, 3.0)
    return base + (bank - base) * t
bog_mud = tex_mat("BogMud", "brown_mud_02", 1.0, (0.85, 0.70, 0.52), 0.1, 1.1)
bank_m = tex_mat("BankGround", "forest_ground_04", 1.0, (1.0, 1.0, 0.95), 0.1, 1.2)
TERR = grid_terrain("BogTerrain", 44, 176, bog_z, bog_mud, CB)
TERR.data.materials.append(bank_m)
for p_ in TERR.data.polygons:
    if p_.center.z > -0.05: p_.material_index = 1
# water: clear, slightly green, gently waving; casts no shadow so the floor stays lit under it
wm = bpy.data.materials.new("Water"); wm.use_nodes = True; wnt = wm.node_tree; wp = wnt.nodes["Principled BSDF"]
wp.inputs["Base Color"].default_value = (0.70, 0.92, 0.85, 1); wp.inputs["Roughness"].default_value = 0.04
wp.inputs["Transmission Weight"].default_value = 1.0; wp.inputs["IOR"].default_value = 1.33
if "Specular IOR Level" in wp.inputs: wp.inputs["Specular IOR Level"].default_value = 0.35
wn = wnt.nodes.new("ShaderNodeTexNoise"); wn.inputs["Scale"].default_value = 2.5; wn.inputs["Detail"].default_value = 3
wtc = wnt.nodes.new("ShaderNodeTexCoord"); wmp = wnt.nodes.new("ShaderNodeMapping"); wnt.links.new(wtc.outputs["Object"], wmp.inputs["Vector"])
wnt.links.new(wmp.outputs["Vector"], wn.inputs["Vector"])
wb = wnt.nodes.new("ShaderNodeBump"); wb.inputs["Strength"].default_value = 0.12; wnt.links.new(wn.outputs["Fac"], wb.inputs["Height"])
wnt.links.new(wb.outputs["Normal"], wp.inputs["Normal"])
wmp.inputs["Location"].default_value = (0, 0, 0); wmp.inputs["Location"].keyframe_insert("default_value", frame=1)
wmp.inputs["Location"].default_value = (FEND / 600.0, FEND / 900.0, FEND / 300.0); wmp.inputs["Location"].keyframe_insert("default_value", frame=FEND)
for fc in (wnt.animation_data.action.fcurves if hasattr(wnt.animation_data.action, "fcurves") else []):
    for kp in fc.keyframe_points: kp.interpolation = 'LINEAR'
WATER = plane("WaterSurface", (44, 44), (0, 0, 0), wm, CB)
WATER.visible_shadow = False
um = bpy.data.materials.new("WaterUnder"); um.use_nodes = True; unt = um.node_tree; unt.nodes.clear()
uo = unt.nodes.new("ShaderNodeOutputMaterial"); ut = unt.nodes.new("ShaderNodeBsdfTransparent"); ut.inputs[0].default_value = (0.80, 0.97, 0.93, 1)
ug = unt.nodes.new("ShaderNodeBsdfGlossy"); ug.inputs["Roughness"].default_value = 0.15; ug.inputs[0].default_value = (0.75, 0.95, 0.9, 1)
umx = unt.nodes.new("ShaderNodeMixShader"); umx.inputs[0].default_value = 0.12
unt.links.new(ut.outputs[0], umx.inputs[1]); unt.links.new(ug.outputs[0], umx.inputs[2]); unt.links.new(umx.outputs[0], uo.inputs[0])
WUNDER = plane("WaterUnder", (44, 44), (0, 0, 0), um, CB); WUNDER.visible_shadow = False
vm = bpy.data.materials.new("WaterVolume"); vm.use_nodes = True; vnt = vm.node_tree; vnt.nodes.clear()
vo = vnt.nodes.new("ShaderNodeOutputMaterial"); vv = vnt.nodes.new("ShaderNodeVolumePrincipled")
vv.inputs["Color"].default_value = (0.55, 0.85, 0.75, 1); vv.inputs["Density"].default_value = 0.10
vv.inputs["Absorption Color"].default_value = (0.75, 0.95, 0.85, 1)
vnt.links.new(vv.outputs[0], vo.inputs["Volume"])
WVOL = rbox("WaterVolume", (11.0, 11.0, 1.0), (0, 0, -0.505), vm, CB, 0.0)
WVOL.visible_shadow = False
# banks: grass, shrubs, dead trunks, trees; reeds of tall grass right at the waterline
on_bank = lambda x, y: math.hypot(x, y) < 4.6
scatter(GRASS, 650, CB, (-14, 14, -14, 14), bog_z, (1.6, 2.8), on_bank, "BogGrass")
ring = []
for k in range(140):
    a = random.uniform(0, 6.28); r = random.uniform(4.3, 5.0); x, y = r * math.cos(a), r * math.sin(a)
    ring.append(dup(random.choice(GRASS[:4]), f"Reed{k}", (x, y, bog_z(x, y) - 0.03), (0, 0, random.uniform(0, 6.28)), random.uniform(2.6, 3.6), CB))
scatter(SHRUBS, 40, CB, (-16, 16, -16, 16), bog_z, (0.9, 1.5), lambda x, y: math.hypot(x, y) < 6.5, "BogShrub")
for k, (x, y, rz, s) in enumerate(((-7.5, 6.0, 0.4, 1.0), (8.0, 7.5, 2.0, 1.1), (-9.0, -5.0, 4.0, 0.9), (10.5, -3.0, 1.0, 1.2),
                                    (-3.0, 10.5, 5.0, 1.0), (4.0, -10.0, 3.0, 1.1), (12.0, 6.0, 2.5, 1.3), (-12.0, 3.0, 0.8, 1.2))):
    tree_at(f"BogTree{k}", (x, y, bog_z(x, y) - 0.05), rz, s, CB)
dup(DEADTRUNK, "BogDeadTrunk0", (-5.4, 2.6, bog_z(-5.4, 2.6) - 0.05), (0, 0, 1.0), 1.0, CB)
dup(DEADTRUNK, "BogDeadTrunk1", (5.8, -3.6, bog_z(5.8, -3.6) - 0.05), (0, 0, 3.0), 0.9, CB)
for k in range(6):
    x, y = random.uniform(-3, 3), random.uniform(-3, 3)
    if math.hypot(x, y) < 1.4: continue
    pass   # (sunken branches removed: one blocked the lens in S05)
area("BogFill", (-3, -6, 4), (0, 0, -0.3), 300, 6, CB, (0.95, 1.0, 0.95))

# ------------------------------------------------------------------ the deceased: curled pose (constant), and baked copies
for pb in DEAD.pose.bones: pb.rotation_mode = 'QUATERNION'
RDEAD = Rig(DEAD)
curl_off_ik(DEAD); key_curl(RDEAD, 1); curl_hands(RDEAD, 1)
# closed eyes: upper lids down a little (orbicularis03), only rotation keys on the lid bones
for s_ in "LR":
    pbn = "orbicularis03." + s_
    if pbn in RDEAD.PB:
        RDEAD.key_rot(pbn, 1, [("X", 28)])
DEAD_ROT = Euler((0, R_(-90), 0)).to_matrix()
DOFF = {}   # lying on her right side
def dead_place(f, xy, floor_z, yaw=0.0, lift=0.0):
    """key the rig so the curled body lies on its side with its lowest point on floor_z, centred on xy"""
    M = (Matrix.Rotation(R_(yaw), 3, 'Z') @ DEAD_ROT)
    DEAD.rotation_mode = 'XYZ'; DEAD.rotation_euler = M.to_euler()
    if yaw not in DOFF:
        DEAD.location = (0, 0, 0); sc.frame_set(f); DEAD.location = (0, 0, 0); DEAD.rotation_euler = M.to_euler()
        bpy.context.view_layer.update()
        body = bpy.data.objects["Dead.body"]; dg = bpy.context.evaluated_depsgraph_get(); ev_ = body.evaluated_get(dg)
        pts = [body.matrix_world @ v.co for v in ev_.data.vertices]
        mn = Vector([min(p[i] for p in pts) for i in range(3)]); mx = Vector([max(p[i] for p in pts) for i in range(3)])
        DOFF[yaw] = (mn, mx)
    mn, mx = DOFF[yaw]; cen = (mn + mx) / 2
    DEAD.location = Vector((xy[0] - cen.x, xy[1] - cen.y, floor_z - mn.z + 0.005 + lift))
    DEAD.keyframe_insert("location", frame=f); DEAD.keyframe_insert("rotation_euler", frame=f)
    return mn - cen, mx - cen    # half extents (relative)
EXT = dead_place(1, (0, 0), FLOOR)
print("BUILD dead extents", tuple(round(v, 3) for v in EXT[0]), tuple(round(v, 3) for v in EXT[1]))
DEAD_CEN = Vector((0, 0, FLOOR + 0.005 - EXT[0].z))    # body centre at the bog site

def bake_dead(parts=("body", "elegantsuit", "long01", "shoes", "eyebrow", "eyelashes", "high-poly", "Shroud", "LegWool")):
    """static meshes of the posed body in world orientation, centred on the body centre"""
    off = []
    for ch in DEAD.children:
        for m in ch.modifiers:
            if m.type == 'SUBSURF' and m.show_viewport: m.show_viewport = False; off.append(m)
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get(); out = []
    for ch in DEAD.children:
        if ch.type != 'MESH' or not any(p in ch.name for p in parts): continue
        me = bpy.data.meshes.new_from_object(ch.evaluated_get(dg), depsgraph=dg)
        me.transform(Matrix.Translation(-DEAD_CEN) @ ch.matrix_world); me.update()
        out.append((ch.name.split(".", 1)[1], me))
        print("BUILD baked", ch.name, len(me.vertices))
    for m in off: m.show_viewport = True
    return out
exec(open(HERE + "/05_clothes.py").read())
sc.frame_set(1); bpy.context.view_layer.update()
DSM = bake_dead()
def place_static(name, c, loc, yaw=0.0):
    root = bpy.data.objects.new(name, None); c.objects.link(root); root.location = loc; root.rotation_euler = (0, 0, R_(yaw))
    for nm, me in DSM:
        o = bpy.data.objects.new(name + "_" + nm, me); c.objects.link(o); o.parent = root
    return root

# ------------------------------------------------------------------ stakes: crossed pairs over each body, none through it
bark = tex_mat("Bark", "bark_brown_02", 1.0, (0.85, 0.72, 0.58), 0.15, 1.1, bump=0.25)
def stake_mesh(name, length=2.1, r0=0.035, r1=0.022, seed=0):
    rnd = random.Random(seed)
    bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius=1, depth=1, location=(0, 0, 0))
    o = bpy.context.active_object; o.name = name
    me = o.data
    for v in me.vertices:
        t = v.co.z + 0.5                                    # 0 bottom .. 1 top
        r = r0 + (r1 - r0) * t
        if t < 0.06: r *= max(0.25, t / 0.06)               # sharpened point
        bend = 0.04 * math.sin(t * 3.0 + seed) + 0.02 * math.sin(t * 9 + seed * 2)
        v.co.x = v.co.x * r + bend; v.co.y = v.co.y * r + 0.02 * math.sin(t * 5 + seed)
        v.co.z = t * length
    lc = o.modifiers.new("sub", 'SUBSURF'); lc.levels = 1; lc.render_levels = 1
    bpy.ops.object.shade_smooth(); me.materials.append(bark)
    me.uv_layers.new(name="UVMap")
    for poly in me.polygons:
        for li in poly.loop_indices:
            co = me.vertices[me.loops[li].vertex_index].co
            me.uv_layers[0].data[li].uv = (math.atan2(co.y, co.x) / 6.28 * 0.3, co.z * 0.5)
    move_to(o, CSTK); return o
CSTK = coll("STAKES")
def stake_frame(base, top):
    d = (Vector(top) - Vector(base)); q = d.to_track_quat('Z', 'Y')
    return q.to_euler(), d.length
def place_stake(o, base, top, f=None):
    e, L = stake_frame(base, top)
    o.location = Vector(base); o.rotation_euler = e; o.scale = (1, 1, L / 2.1)
    if f is not None:
        o.keyframe_insert("location", frame=f); o.keyframe_insert("rotation_euler", frame=f)

def stake_cluster(prefix, cen, top_z, yaw=0.0, n_pairs=3, spacing=0.36, half=0.80, seed=0):
    """crossed X pairs along the body: bases buried beside it, shafts crossing 0.2 m above its top"""
    out = []; Rz = Matrix.Rotation(R_(yaw), 3, 'Z')
    for k in range(n_pairs):
        xo = (k - (n_pairs - 1) / 2) * spacing
        for side in (1, -1):
            cross = Vector((xo, 0, top_z + 0.20))
            base = Vector((xo + 0.04 * side, side * half, -0.45 - (top_z + 0.20)))       # base 0.45 m under the floor line
            base = Vector((base.x, base.y, cen.z - 0.30 - 0.20))
            dirv = (cross - base).normalized()
            top = base + dirv * 2.1
            b = Vector(cen.to_2d().to_3d()) + Rz @ Vector((base.x, base.y, 0)); b.z = base.z
            t = Vector(cen.to_2d().to_3d()) + Rz @ Vector((top.x, top.y, 0)); t.z = top.z
            o = stake_mesh(f"{prefix}_{k}{'a' if side > 0 else 'b'}", seed=seed * 10 + k * 2 + (side > 0))
            place_stake(o, b, t); out.append(o)
    return out
TOPZ = DEAD_CEN.z + EXT[1].z
STK_MAIN = stake_cluster("Stake", Vector((0, 0, FLOOR)), TOPZ, 0, seed=1)
# other burials of the pond: baked bodies + their stakes
OTHERS = [((-2.1, 1.3), 35), ((2.4, 1.6), -20), ((1.7, -1.9), 70), ((-1.6, -2.2), 110), ((3.3, 0.2), 15)]
OB = []
for k, ((x, y), yw) in enumerate(OTHERS):
    place_static(f"Burial{k}", CB, (x, y, DEAD_CEN.z + bog_z(x, y) - FLOOR), yw)
    OB += stake_cluster(f"StakeB{k}", Vector((x, y, bog_z(x, y))), TOPZ + bog_z(x, y) - FLOOR, yw, seed=k + 2)

# ================================================================== SET 2: cross-section (x=100)
CC = coll("SET_cut")
CX = Vector((1000, 0, 0))
peat_m = tex_mat("PeatCut", "mud_forest", 1.0, (0.62, 0.42, 0.26), 0.05, 1.1, box=True)
mudc_m = tex_mat("MudCut", "brown_mud_02", 1.0, (0.55, 0.40, 0.30), -0.05, 1.0, box=True)
# lower mud block, upper peat layer (the lid), both cut flat toward the camera (-Y face at y = -0.55)
rbox("CutMud", (4.0, 2.0, 3.0), CX + Vector((0, 0.45, FLOOR - 1.5)), mudc_m, CC, 0.01)
NICHE = 0.12
LID = rbox("CutLid", (4.0, 2.0, 0.55), CX + Vector((0, 0.45, TOPZ + NICHE + 0.275)), peat_m, CC, 0.01)
# niche in front of the body: the body lies on the mud, exposed at the cut face; the lid covers it from above
rbox("CutBack", (4.0, 0.9, TOPZ + NICHE - FLOOR), CX + Vector((0, 1.0, (FLOOR + TOPZ + NICHE) / 2)), peat_m, CC, 0.01)
CUTGRASS = scatter(GRASS, 70, CC, (CX.x - 1.9, CX.x + 1.9, -0.4, 1.4), lambda x, y: TOPZ + NICHE + 0.55, (1.0, 1.6), None, "CutGrass")
for g in CUTGRASS:
    g.parent = LID; g.matrix_parent_inverse = LID.matrix_world.inverted()
CS = place_static("CutBody", CC, CX + Vector((0, 0.05, DEAD_CEN.z)))
CUT_STK = stake_cluster("CutStake", CX + Vector((0, 0.05, FLOOR)), TOPZ, 0, n_pairs=2, spacing=0.5, half=0.45, seed=9)
# backdrop for the cut: sky-blue gradient wall far behind (explainer beat)
bdm = bpy.data.materials.new("CutBackdrop"); bdm.use_nodes = True; bnt = bdm.node_tree
bnt.nodes.remove(bnt.nodes["Principled BSDF"]); em = bnt.nodes.new("ShaderNodeEmission")
btc = bnt.nodes.new("ShaderNodeTexCoord"); bsp = bnt.nodes.new("ShaderNodeSeparateXYZ"); bnt.links.new(btc.outputs["Generated"], bsp.inputs[0])
brp = bnt.nodes.new("ShaderNodeValToRGB"); brp.color_ramp.elements[0].color = (0.91, 0.97, 1.0, 1); brp.color_ramp.elements[1].color = (0.31, 0.76, 0.97, 1)
bnt.links.new(bsp.outputs["Z"], brp.inputs["Fac"]); bnt.links.new(brp.outputs["Color"], em.inputs["Color"]); em.inputs["Strength"].default_value = 1.0
bnt.links.new(em.outputs[0], bnt.nodes["Material Output"].inputs[0])
plane("CutBackdrop", (40, 20), CX + Vector((0, 9, 2)), bdm, CC, (R_(90), 0, 0))
area("CutKey", CX + Vector((-2.0, -3.5, 2.5)), CX + Vector((0, 0, -0.4)), 500, 3, CC)
area("CutFill", CX + Vector((2.5, -3.0, 0.5)), CX + Vector((0, 0, -0.5)), 200, 3, CC, (0.95, 0.97, 1.0))
# air bubbles (light blue, glowing a little), keyed per shot 12
bub_m = mat("Bubble", (0.75, 0.92, 1.0), 0.1, emit=(0.55, 0.85, 1.0), ew=2.0)
wcm = bpy.data.materials.new("CutWater"); wcm.use_nodes = True; wp_ = wcm.node_tree.nodes["Principled BSDF"]
wp_.inputs["Base Color"].default_value = (0.45, 0.78, 0.85, 1); wp_.inputs["Alpha"].default_value = 0.35; wp_.inputs["Roughness"].default_value = 0.1
WATERCUT = rbox("CutWaterLayer", (4.0, 2.0, 0.72), CX + Vector((0, 0.45, TOPZ + NICHE + 0.55 + 0.36)), wcm, CC, 0.0)
WATERCUT.visible_shadow = False
BUBS = []
for k in range(16):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8, radius=random.uniform(0.035, 0.06))
    b = bpy.context.active_object; b.name = f"Bubble{k}"; bpy.ops.object.shade_smooth(); b.data.materials.append(bub_m)
    move_to(b, CC); b.location = CX + Vector((0, 0, -50)); BUBS.append(b)

# ================================================================== SET 3: construction site (x=200), dried bog 8,000 years later
CS3 = coll("SET_site")
SX = Vector((2000, 0, 0))
dirt_m = tex_mat("SiteDirt", "dirt", 0.5, (0.95, 0.85, 0.72), 0.1, 1.1)
def site_z(x, y):
    lx, ly = x, y
    z = 0.04 * noise2(lx, ly, 0.8)
    for (mx_, my_, h, r) in ((-1.0, 1.2, 0.7, 1.6), (4.5, 6.0, 1.1, 2.2), (-6.0, 7.0, 0.8, 2.0)):
        d = math.hypot(lx - mx_, ly - my_); z += h * max(0.0, 1 - (d / r) ** 2) ** 1.5
    d = math.hypot(lx - 2.0, ly - 1.5); z -= 0.45 * max(0.0, 1 - (d / 1.6) ** 2)    # the excavated hole
    return z
SITE = grid_terrain("SiteGround", 60, 150, site_z, dirt_m, CS3, (SX.x, SX.y))
sgz = lambda x, y: site_z(x - SX.x, y - SX.y)
scatter(GRASS, 260, CS3, (SX.x - 28, SX.x + 28, -28, 28), sgz, (1.4, 2.4), lambda x, y: math.hypot(x - SX.x, y) < 13, "SiteGrass")
for k, (x, y) in enumerate(((-16, 12), (14, 16), (-20, -6), (18, -10), (2, 22), (-8, 20))):
    tree_at(f"SiteTree{k}", (SX.x + x, y, sgz(SX.x + x, y)), k * 1.3, 1.1, CS3)
EXCV = dup(EXC, "SiteExcavator", SX + Vector((5.6, 2.6, sgz(SX.x + 5.6, 2.6))), (0, 0, R_(160)), 1.0, CS3)
TRK = dup(TRUCK, "SitePickup", SX + Vector((-4.2, 3.8, sgz(SX.x - 4.2, 3.8) + 0.0)), (0, 0, R_(8)), 1.0, CS3, linked=False)
# pickup paint recoloured clean white (no brand), texture kept for windows/tyres/lights
for m in TRK.data.materials:
    nt_ = m.node_tree; t0 = next((n for n in nt_.nodes if n.type == 'TEX_IMAGE'), None)
    if t0 and not any(n.type == 'BSDF_PRINCIPLED' for n in nt_.nodes):
        outn = next(n for n in nt_.nodes if n.type == 'OUTPUT_MATERIAL'); pr = nt_.nodes.new("ShaderNodeBsdfPrincipled")
        nt_.links.new(t0.outputs["Color"], pr.inputs["Base Color"]); nt_.links.new(pr.outputs[0], outn.inputs["Surface"])
    Pn = next((n for n in nt_.nodes if n.type == 'BSDF_PRINCIPLED'), None)
    if Pn is None: continue
    t_ = next((n for n in nt_.nodes if n.type == 'TEX_IMAGE'), None)
    print("BUILD truck mat", m.name, bool(t_), tuple(round(v, 2) for v in Pn.inputs["Base Color"].default_value))
    if not t_:
        c_ = Pn.inputs["Base Color"].default_value
        if c_[0] > 1.6 * max(c_[1], c_[2]): Pn.inputs["Base Color"].default_value = (0.92, 0.92, 0.9, 1)
    if t_:
        hs = nt_.nodes.new("ShaderNodeHueSaturation"); hs.inputs["Saturation"].default_value = 0.0; hs.inputs["Value"].default_value = 1.6
        nt_.links.new(t_.outputs["Color"], hs.inputs["Color"]); nt_.links.new(hs.outputs["Color"], Pn.inputs["Base Color"])
    Pn.inputs["Roughness"].default_value = 0.35
# logo on the driver door (pickup faces -Y in the library: its left side is +X; driver side = +X after an 8 deg yaw)
bpy.context.view_layer.update()
LOGO1 = logo_decal("Logo_PickupDoor", Vector((0, 0, 0)), (0, 0, 0), 0.50, True, CS3)
glass = mat("TruckGlass", (0.03, 0.04, 0.05), 0.08, 0.0)
paint = mat("TruckPaint", (0.86, 0.86, 0.84), 0.35, 0.0)
TRK.data.materials.append(glass); _gi = len(TRK.data.materials) - 1
TRK.data.materials.append(paint); _pi = len(TRK.data.materials) - 1
_vs = TRK.data.vertices
_roof = [v.co for v in _vs if v.co.z > 1.60]
_ry0, _ry1 = min(p.y for p in _roof), max(p.y for p in _roof); _rz = min(p.z for p in _roof)
_ng = _np = 0
for _p in TRK.data.polygons:
    c_ = _p.center
    # cab glass band: below the roof, from the windshield foot to the rear window
    if 1.12 < c_.z < 1.60 and _ry0 - 0.55 < c_.y < _ry1 + 0.08 and abs(c_.x) < 0.80:
        _p.material_index = _gi; _ng += 1
    # no brand or number text: tailgate lettering and both licence plates painted plain
    elif (abs(c_.y) > 2.05 and abs(c_.x) < 0.55 and 0.18 < c_.z < 0.76) or (c_.y > 2.05 and abs(c_.x) < 0.62 and 0.70 < c_.z < 1.02):
        _p.material_index = _pi; _np += 1
print("BUILD glass faces", _ng, "plain faces", _np, "roof y", round(_ry0, 2), round(_ry1, 2))
# fence posts with orange safety mesh at the edge of the dig
fm = mat("SafetyOrange", (1.0, 0.35, 0.05), 0.6); pm_ = mat("PostGrey", (0.35, 0.35, 0.36), 0.5, 0.6)
for k in range(0):
    a = R_(200 + k * 18); x, y = SX.x + 2.0 + 3.0 * math.cos(a), 1.5 + 3.0 * math.sin(a)
    cyl(f"FencePost{k}", 0.025, 1.1, (x, y, sgz(x, y) + 0.5), pm_, CS3)
# the skull in the excavated earth (separate copy of the skeleton's skull)
def make_skull():
    me = SKEL.data.copy(); o = bpy.data.objects.new("SkullFound", me); CS3.objects.link(o)
    bm = bmesh.new(); bm.from_mesh(me)
    zmax = max(v.co.z for v in bm.verts)
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z < zmax - 0.235], context='VERTS')
    bm.to_mesh(me); bm.free()
    pts = [v.co for v in me.vertices]; c = sum(pts, Vector()) / len(pts); mnz = min(p.z for p in pts)
    me.transform(Matrix.Translation(Vector((-c.x, -c.y, -mnz)))); me.update()
    return o
SKULL = make_skull()
SKULL.location = SX + Vector((0.6, 0.3, sgz(SX.x + 0.6, 0.3) - 0.025)); SKULL.rotation_euler = (R_(-6), 0, R_(27))
skull_m = mat("BoneOld", (0.78, 0.66, 0.48), 0.6)
SKULL.data.materials.clear(); SKULL.data.materials.append(skull_m)
area("SiteFill", SX + Vector((-3, -6, 4)), SX + Vector((1, 1, 0.5)), 300, 6, CS3)

# ================================================================== SET 4: dig (x=300) + field of burials
CD = coll("SET_dig")
DX = Vector((3000, 0, 0))
peat2 = tex_mat("DigPeat", "mud_forest", 0.6, (0.80, 0.62, 0.46), 0.35, 1.1)
PITS = [(0.0, 0.0)]
for i in range(-5, 6):
    for j in range(-6, 7):
        if (i, j) == (0, 0): continue
        if random.random() < 0.62:
            PITS.append((i * 2.4 + random.uniform(-0.5, 0.5), j * 2.2 + random.uniform(-0.5, 0.5)))
def dig_z(x, y):
    z = 0.03 * noise2(x, y, 1.0)
    for (px, py) in PITS:
        dx, dy = (x - px) / 0.85, (y - py) / 0.62
        d = dx * dx + dy * dy
        if d < 1.6: z -= 0.32 * max(0.0, 1 - d) ** 0.6 if d < 1 else 0.0
    return z
DIG = grid_terrain("DigGround", 34, 340, dig_z, peat2, CD, (DX.x, DX.y))
dgz = lambda x, y: dig_z(x - DX.x, y - DX.y)
scatter(GRASS, 160, CD, (DX.x - 30, DX.x + 30, -30, 30), dgz, (1.4, 2.4), lambda x, y: abs(x - DX.x) < 15 and abs(y) < 16, "DigGrass")
# pin flags at every burial
flag_m = mat("FlagOrange", (1.0, 0.45, 0.05), 0.5); wire_m = mat("FlagWire", (0.3, 0.3, 0.3), 0.4, 0.6)
for k, (px, py) in enumerate(PITS):
    if k == 0: continue
    x, y = DX.x + px + 0.75, py + 0.45
    cyl(f"FlagWire{k}", 0.004, 0.45, (x, y, dgz(x, y) + 0.2), wire_m, CD, verts=6)
    rbox(f"FlagCloth{k}", (0.12, 0.004, 0.08), (x + 0.06, y, dgz(x, y) + 0.38), flag_m, CD, 0.0)
# grid strings around the main pit
for k, (a, b) in enumerate((((-1.0, -0.75), (1.0, -0.75)), ((1.0, -0.75), (1.0, 0.75)), ((1.0, 0.75), (-1.0, 0.75)), ((-1.0, 0.75), (-1.0, -0.75)))):
    A = DX + Vector((a[0], a[1], 0)); Bp = DX + Vector((b[0], b[1], 0))
    A.z = dgz(A.x, A.y) + 0.12; Bp.z = dgz(Bp.x, Bp.y) + 0.12
    mid = (A + Bp) / 2; L = (Bp - A).length
    o = cyl(f"GridString{k}", 0.003, L, mid, mat("String", (0.95, 0.9, 0.75), 0.6), CD, verts=6)
    o.rotation_euler = (Bp - A).to_track_quat('Z', 'Y').to_euler()
    cyl(f"GridPeg{k}", 0.012, 0.3, (A.x, A.y, A.z - 0.05), mat("PegWood", (0.6, 0.45, 0.28), 0.7), CD, verts=8)
# skeleton bound to a copy of the Dead rig (same curled pose); lies in the main pit
SKR, SKO = skel_bind(DEAD, SKEL)
for c_ in list(SKR.users_collection): c_.objects.unlink(SKR)
for c_ in list(SKO.users_collection): c_.objects.unlink(SKO)
CD.objects.link(SKR); CD.objects.link(SKO)
bone_m = mat("BoneClean", (0.86, 0.76, 0.58), 0.55)
SKO.data.materials.clear(); SKO.data.materials.append(bone_m)
RSK = Rig(SKR); curl_off_ik(SKR); key_curl(RSK, 1)
curl_hands(RSK, 1)
pit_floor = dgz(DX.x, DX.y)
SKR.rotation_mode = 'XYZ'; SKR.rotation_euler = DEAD_ROT.to_euler()
sc.frame_set(1); bpy.context.view_layer.update()
def place_rig_lowest(rig, mesh, xy, floor_z, f=1):
    rig.location = (0, 0, 0); bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get(); ev_ = mesh.evaluated_get(dg)
    pts = [mesh.matrix_world @ v.co for v in ev_.data.vertices]
    mn = Vector([min(p[i] for p in pts) for i in range(3)]); mx = Vector([max(p[i] for p in pts) for i in range(3)])
    cen = (mn + mx) / 2
    rig.location = Vector((xy[0] - cen.x, xy[1] - cen.y, floor_z - mn.z + 0.01))
    rig.keyframe_insert("location", frame=f); rig.keyframe_insert("rotation_euler", frame=f)
    return mn - cen, mx - cen
SKEXT = place_rig_lowest(SKR, SKO, (DX.x, DX.y), pit_floor)
SK_CEN = Vector((DX.x, DX.y, pit_floor + 0.01 - SKEXT[0].z))
# baked skeletons in the other pits near the centre (168 burials)
dg = bpy.context.evaluated_depsgraph_get()
SKBAKE = bpy.data.meshes.new_from_object(SKO.evaluated_get(dg), depsgraph=dg)
SKB_MW = SKO.matrix_world.copy()
for k, (px, py) in enumerate(PITS[1:]):
    if k == 0: continue          # pit 1 holds the opened skull alone
    o = bpy.data.objects.new(f"SkelBaked{k}", SKBAKE); CD.objects.link(o)
    o.matrix_world = Matrix.Translation(Vector((px, py, dgz(DX.x + px, py) - pit_floor))) @ \
        Matrix.Translation(SK_CEN) @ Matrix.Rotation(random.uniform(-0.6, 0.6), 4, 'Z') @ Matrix.Translation(-SK_CEN) @ SKB_MW
# burial cloth: the garment, baked in the same pose, as worn decayed linen around the bones (shot 22 on)
linen = tex_mat("BurialLinen", "rough_linen", 3.0, (0.85, 0.70, 0.48), 0.1, 0.0, bump=0.2)
lnt = linen.node_tree; lp_ = lnt.nodes["Principled BSDF"]
hn = lnt.nodes.new("ShaderNodeTexNoise"); hn.inputs["Scale"].default_value = 9.0; hn.inputs["Detail"].default_value = 6
hr = lnt.nodes.new("ShaderNodeMapRange"); hr.inputs["From Min"].default_value = 0.40; hr.inputs["From Max"].default_value = 0.44
lnt.links.new(hn.outputs["Fac"], hr.inputs["Value"]); lnt.links.new(hr.outputs["Result"], lp_.inputs["Alpha"])
sc.frame_set(1); dg = bpy.context.evaluated_depsgraph_get()
cloth_src = bpy.data.objects["Dead.female_elegantsuit01"]
CLOTH_ME = bpy.data.meshes.new_from_object(cloth_src.evaluated_get(dg), depsgraph=dg)
CLOTH = bpy.data.objects.new("BurialCloth", CLOTH_ME); CD.objects.link(CLOTH)
CLOTH.data.materials.clear(); CLOTH.data.materials.append(linen)
# move it from the bog body pose to the skeleton: same pose, different placement (rig transforms differ only by location)
CLOTH.matrix_world = Matrix.Translation(SKR.matrix_world.translation - DEAD.matrix_world.translation) @ cloth_src.matrix_world
sol = CLOTH.modifiers.new("shrink", 'DISPLACE'); sol.strength = -0.012
# stomach contents: seeds and plant fibres inside the abdomen (between ribs and pelvis)
sc.frame_set(1); bpy.context.view_layer.update()
ABD = (SKR.matrix_world @ SKR.pose.bones["spine03"].head).lerp(SKR.matrix_world @ SKR.pose.bones["lowerleg01.R"].head, 0.45)
ABD = ABD + (SKR.matrix_world.to_3x3() @ Vector((0, -1, 0))).normalized() * 0.10
ABD.z = pit_floor + 0.06
seed_m = mat("Seeds", (0.60, 0.32, 0.10), 0.45, emit=(1.0, 0.62, 0.12), ew=0.0)
fib_m = mat("Fibres", (0.40, 0.28, 0.14), 0.8)
SEEDS = []
fwd_abd = (SKR.matrix_world.to_3x3() @ Vector((0, -1, 0))).normalized()

for k in range(80):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=10, ring_count=6, radius=0.012)
    s_ = bpy.context.active_object; s_.name = f"Seed{k}"; s_.scale = (1, 0.7, 0.7); bpy.ops.object.shade_smooth()
    s_.data.materials.append(seed_m); move_to(s_, CD)
    d_ = Vector((random.gauss(0, 1), random.gauss(0, 1), random.gauss(0, 1) * 0.5)).normalized() * random.uniform(0, 0.065)
    s_.location = ABD + d_; s_.rotation_euler = (random.uniform(0, 3), random.uniform(0, 3), random.uniform(0, 3)); SEEDS.append(s_)
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=0.055, location=ABD)
FIB = bpy.context.active_object; FIB.name = "StomachMass"; FIB.scale = (1.0, 0.8, 0.75)
dsp = FIB.modifiers.new("d", 'DISPLACE'); tx_ = bpy.data.textures.new("fibtex", 'CLOUDS'); tx_.noise_scale = 0.03; dsp.texture = tx_; dsp.strength = 0.02
bpy.ops.object.shade_smooth(); FIB.data.materials.append(fib_m); move_to(FIB, CD)
# an opened skull with the preserved brain, in the next pit (archaeologists lifted its cap)
SK2 = make_skull(); SK2.name = "SkullOpen"; move_to(SK2, CD)
SK2.data.materials.clear(); SK2.data.materials.append(bone_m)
bm = bmesh.new(); bm.from_mesh(SK2.data)
zt = max(v.co.z for v in bm.verts)
res_ = bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=(0, 0, zt - 0.055), plane_no=(0, 0.25, 1), clear_outer=True)
bm.to_mesh(SK2.data); bm.free()
sol2 = SK2.modifiers.new("thick", 'SOLIDIFY'); sol2.thickness = 0.006
P2 = PITS[1]
SK2.location = DX + Vector((P2[0] + 0.1, P2[1] - 0.05, dgz(DX.x + P2[0] + 0.1, P2[1] - 0.05) + 0.0)); SK2.rotation_euler = (R_(-8), 0, R_(25))
BR = dup(BRAIN, "BrainOld", (0, 0, 0), (0, 0, 0), 0.75, CD, linked=False)
brn_m = mat("BrainOld", (0.50, 0.33, 0.20), 0.5)
BR.data.materials.clear(); BR.data.materials.append(brn_m)
bpy.context.view_layer.update()
skp = [SK2.matrix_world @ v.co for v in SK2.data.vertices]
skmn = Vector([min(p[i] for p in skp) for i in range(3)]); skmx = Vector([max(p[i] for p in skp) for i in range(3)])
crown = [p for p in skp if p.z > skmx.z - 0.03]          # the cut rim: the brain sits centred under it
rc = sum(crown, Vector()) / len(crown)
BR.location = Vector((rc.x, rc.y, skmx.z - 0.098)); BR.rotation_euler = SK2.rotation_euler.copy()
area("DigFill", DX + Vector((-2, -4, 3.5)), DX + Vector((0, 0, 0)), 650, 6, CD)
area("SkullFill", SK2.location + Vector((-0.4, -0.6, 0.7)), SK2.location, 25, 0.5, CD)

# logo on the pickup door: placed on the body side facing the site camera
bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get(); ev_ = TRK.evaluated_get(dg); inv = TRK.matrix_world.inverted()
side_dir = TRK.matrix_world.to_3x3() @ Vector((1, 0, 0))
probe = TRK.matrix_world @ Vector((0, -0.75, 0.88))
ok, loc, nrm, idx = ev_.ray_cast(inv @ (probe + side_dir * 2.0), inv.to_3x3() @ (-side_dir))
if ok:
    hit = TRK.matrix_world @ loc; nw = side_dir.normalized()      # the truck's own side axis (the scanned door's normals are noisy)
    LOGO1.location = hit + nw * 0.006
    LOGO1.rotation_euler = nw.to_track_quat('Z', 'Y').to_euler()
    print("BUILD logo door", tuple(round(v, 3) for v in hit), tuple(round(v, 2) for v in nw))
LOGO1.parent = None
# a flat white door sign (magnetic company sign) carries the logo, so every letter sits on one flat face
_n = LOGO1.rotation_euler.to_matrix() @ Vector((0, 0, 1))
SIGN = rbox("DoorSign", (0.58, 0.30, 0.008), LOGO1.location + _n * 0.022, mat("SignWhite", (0.95, 0.95, 0.94), 0.4), CS3, 0.004,
            rot=LOGO1.rotation_euler.copy())
LOGO1.location = LOGO1.location + _n * 0.0275
bpy.context.view_layer.update()
# push the sign out until no part of it is inside the door
for _k in range(12):
    _d = SIGN.evaluated_get(bpy.context.evaluated_depsgraph_get())
    _inside = 0
    for _v in SIGN.data.vertices:
        _w = SIGN.matrix_world @ _v.co; _ok, _l, _nn, _i = TRK.closest_point_on_mesh(TRK.matrix_world.inverted() @ _w)
        if _ok and (_w - TRK.matrix_world @ _l).dot(TRK.matrix_world.to_3x3() @ _nn) < 0: _inside += 1
    if not _inside: break
    SIGN.location += _n * 0.01; LOGO1.location += _n * 0.01; bpy.context.view_layer.update()
print("BUILD sign pushed", _k)
LOGO_N = LOGO1.rotation_euler.to_matrix() @ Vector((0, 0, 1)); LOGO_N.z = 0; LOGO_N.normalize()
LOGO_T = Vector((0, 0, 1)).cross(LOGO_N).normalized()        # along the truck body
# ================================================================== rigs and helpers
def ensure_leg_ik(obj):
    if "IK_foot.L" in obj.data.bones: return
    bpy.context.view_layer.objects.active = obj
    for o in bpy.context.selected_objects: o.select_set(False)
    obj.select_set(True); bpy.ops.object.mode_set(mode='EDIT'); eb = obj.data.edit_bones
    for s in "LR":
        b = eb.new("IK_foot." + s); b.head, b.tail, b.roll = eb["foot." + s].head.copy(), eb["foot." + s].tail.copy(), eb["foot." + s].roll
        b.use_deform = False; b.parent = None
        kn = eb["lowerleg01." + s].head.copy(); p = eb.new("Pole_knee." + s)
        p.head = kn + Vector((0, -0.6, 0)); p.tail = p.head + Vector((0, 0, 0.08)); p.use_deform = False
    bpy.ops.object.mode_set(mode='POSE')
    for s in "LR":
        pb = obj.pose.bones["lowerleg02." + s]
        for c in list(pb.constraints):
            if c.type == 'IK': pb.constraints.remove(c)
        c = pb.constraints.new('IK'); c.target, c.subtarget = obj, "IK_foot." + s
        c.pole_target, c.pole_subtarget = obj, "Pole_knee." + s; c.chain_count = 4; c.iterations = 300
        for tb in ("upperleg02.", "lowerleg02."):
            q = obj.pose.bones[tb + s]; q.lock_ik_x = q.lock_ik_y = q.lock_ik_z = True
        obj.pose.bones["lowerleg01." + s].lock_ik_y = obj.pose.bones["lowerleg01." + s].lock_ik_z = True
        cr = obj.pose.bones["foot." + s].constraints.new('COPY_ROTATION'); cr.target, cr.subtarget = obj, "IK_foot." + s
        for pbn in ("IK_foot." + s, "Pole_knee." + s): obj.pose.bones[pbn].rotation_mode = 'QUATERNION'
        ref = obj.data.bones["lowerleg01." + s].head_local.copy(); best = (0, 9)
        for d in range(-180, 180, 2):
            c.pole_angle = R_(d); bpy.context.view_layer.update(); e = (obj.pose.bones["lowerleg01." + s].head - ref).length
            if e < best[1]: best = (d, e)
        c.pole_angle = R_(best[0]); print("BUILD legIK", obj.name, s, best)
    bpy.ops.object.mode_set(mode='OBJECT')
for rg in (BURA, BURB, WORK, ARCH):
    ensure_leg_ik(rg)
    for pb in rg.pose.bones: pb.rotation_mode = 'QUATERNION'
    add_hand_limits(rg)
RA, RB, RW, RAR = Rig(BURA), Rig(BURB), Rig(WORK), Rig(ARCH)
# hard hat on the worker's head: sits on the hair, Child Of the head bone
HAT = dup(bpy.data.objects["HardHat"], "Worker_HardHat", (0, 0, 0), (0, 0, 0), 1.0, bpy.data.collections["CHAR_Worker"], linked=False)
bpy.context.view_layer.update()
_hair = next(c for c in WORK.children if "short" in c.name)
_hp = [_hair.matrix_world @ v.co for v in _hair.data.vertices]
_top = max(p.z for p in _hp); _up = [p for p in _hp if p.z > _top - 0.10]
_cx = (max(p.x for p in _up) + min(p.x for p in _up)) / 2; _cy = (max(p.y for p in _up) + min(p.y for p in _up)) / 2
_w = max(p.x for p in _up) - min(p.x for p in _up)
_hd = HAT.dimensions.copy(); _s = (_w + 0.05) / _hd.x
HAT.scale = (_s, _s, _s); HAT.location = (_cx, _cy + 0.01, _top - 0.085 * _s / 1.0)
bpy.context.view_layer.update()
_c = HAT.constraints.new('CHILD_OF'); _c.target = WORK; _c.subtarget = "head"
_c.inverse_matrix = (WORK.matrix_world @ WORK.pose.bones["head"].matrix).inverted()
print("BUILD hat", round(_w, 3), round(_s, 3), tuple(round(v, 3) for v in HAT.dimensions))
HA, HB, HW, HAR = Human(RA), Human(RB), Human(RW), Human(RAR)
CHARS = {"bA": (BURA, HA), "bB": (BURB, HB), "wk": (WORK, HW), "ar": (ARCH, HAR)}
PARK = {"bA": Vector((0, -500, 0)), "bB": Vector((2, -500, 0)), "wk": Vector((4, -500, 0)), "ar": Vector((6, -500, 0)), "wolf": Vector((8, -500, 0))}
GZ = {"fn": lambda x, y: 0.0}
def ground_z(x, y): return GZ["fn"](x, y)
def any_z(x, y):
    if x < 500: return bog_z(x, y)
    if x < 1500: return 0.0
    if x < 2500: return sgz(x, y)
    return dgz(x, y)
GZ["fn"] = any_z

def stand(H, rig, f, pos, yaw=0.0, head=(0, 0), flex=0.0, twist=0.0, hands=True, breath=0.0, crouch=0.0, root_flex=None):
    c = Matrix.Rotation(R_(yaw), 3, 'Z')
    gz = any_z(pos.x, pos.y)
    H.key_root(f, Vector((pos.x, pos.y, gz + 0.95 - breath * 0.004 - crouch)), yaw=yaw, flex=(flex * 0.3 if root_flex is None else root_flex))
    for s, sx in (("L", 1), ("R", -1)):
        H.key_foot(s, f, (pos + c @ Vector((0.1 * sx, 0.02 if crouch else 0, 0))).to_2d(), yaw)
        if hands:
            place_hand(rig, s, f, Vector((pos.x, pos.y, gz)) + c @ Vector((0.235 * sx, -0.02, 0.80 - crouch + flex * 0.002)), c @ Vector((-sx, 0, 0)), (0, 0, -1))
            apply_pose(rig, s, "relaxed", f)
    H.key_spine(f, flex=flex + breath, twist=twist, head=head)

def walk_swing(H, rig, path, yaw_fn, f0, f1, stride=0.72, step=3):
    """walk plus bent arm swing (no mannequin arms)"""
    H.walk(path, yaw_fn, f0, f1, stride=stride, step=2)
    dist = 0.0; prev = path(f0)
    for f in range(f0, f1 + 1):
        p = path(f); dist += (p - prev).to_2d().length; prev = p
        if (f - f0) % step and f != f1: continue
        ph = 2 * math.pi * dist / stride
        yw = yaw_fn(f); c = Matrix.Rotation(R_(yw), 3, 'Z'); gz = any_z(p.x, p.y)
        for s, sx, sg in (("L", 1, -1), ("R", -1, 1)):
            sw = 0.18 * math.sin(ph) * sg
            pp = Vector((p.x, p.y, gz)) + c @ Vector((0.24 * sx, -sw, 0.80 + abs(sw) * 0.3))
            place_hand(rig, s, f, pp, c @ Vector((-sx, 0, 0)), c @ Vector((0, -0.25, -1)))
            if f == f0 or (f - f0) % (step * 4) == 0: apply_pose(rig, s, "relaxed", f)

def keyobj(o, f, loc=None, rot=None, scale=None):
    if loc is not None: o.location = loc; o.keyframe_insert("location", frame=f)
    if rot is not None: o.rotation_euler = rot; o.keyframe_insert("rotation_euler", frame=f)
    if scale is not None: o.scale = scale if not isinstance(scale, (int, float)) else (scale,) * 3; o.keyframe_insert("scale", frame=f)
def emit_key(m, f, v):
    p = m.node_tree.nodes["Principled BSDF"]; p.inputs["Emission Strength"].default_value = v
    p.inputs["Emission Strength"].keyframe_insert("default_value", frame=f)
def vis(o, frames_on):
    """frames_on: list of (a, b) ranges where o renders; keyed hide_render + hide_viewport together"""
    o.hide_render = o.hide_viewport = True; o.keyframe_insert("hide_render", frame=1); o.keyframe_insert("hide_viewport", frame=1)
    for a_, b_ in frames_on:
        for fr, h in ((a_, False), (b_ + 1, True)):
            o.hide_render = o.hide_viewport = h; o.keyframe_insert("hide_render", frame=fr); o.keyframe_insert("hide_viewport", frame=fr)

CAMC = coll("CAMERAS"); CAMS = {}
def camera(sid, lens=35, fstop=8.0):
    cd = bpy.data.cameras.new("CAM_" + sid); cd.lens = lens; cd.clip_start = 0.02
    cd.dof.use_dof = True; cd.dof.aperture_fstop = fstop
    o = bpy.data.objects.new("CAM_" + sid, cd); CAMC.objects.link(o); CAMS[sid] = o
    return o
def cam_key(o, f, loc, tgt, lens=None, focus=None):
    o.location = loc; o.rotation_euler = (Vector(tgt) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    o.keyframe_insert("location", frame=f); o.keyframe_insert("rotation_euler", frame=f)
    if lens: o.data.lens = lens; o.data.keyframe_insert("lens", frame=f)
    o.data.dof.focus_distance = focus if focus else (Vector(tgt) - Vector(loc)).length
    o.data.dof.keyframe_insert("focus_distance", frame=f)
def cam_move(sid, f0, f1, a, b, lens=35, fstop=8.0, lens1=None, mid=None):
    o = camera(sid, lens, fstop); cam_key(o, f0, Vector(a[0]), Vector(a[1]), lens)
    if mid: cam_key(o, (f0 + f1) // 2, Vector(mid[0]), Vector(mid[1]), (lens + (lens1 or lens)) / 2)
    cam_key(o, f1, Vector(b[0]), Vector(b[1]), lens1 or lens)
    return o
def lerp(a, b, t): return a + (b - a) * t
def ease(t): return t * t * (3 - 2 * t)
PRESENT = {}

def top_point(obj_list, x, y, z0=3.0):
    """highest surface point of the evaluated meshes under (x, y)"""
    dg = bpy.context.evaluated_depsgraph_get(); best = None
    for o in obj_list:
        ev_ = o.evaluated_get(dg); inv = o.matrix_world.inverted()
        ok, loc, nrm, idx = ev_.ray_cast(inv @ Vector((x, y, z0)), inv.to_3x3() @ Vector((0, 0, -1)))
        if ok:
            w_ = o.matrix_world @ loc
            if best is None or w_.z > best.z: best = w_
    return best
DEADMESH = [c for c in DEAD.children if c.type == 'MESH' and any(k in c.name for k in ("body", "elegantsuit", "long01"))]

# ================================================================== shots
def bur_hold(f, lower, breath=0.0):
    """BurA and BurB stand in the water on both sides of the body, palms resting on its upper side (shoulder / hip)"""
    dead_place(f, (0, 0), FLOOR, lift=0.22 * (1 - lower))
    sc.frame_set(f); bpy.context.view_layer.update()
    cen = DEAD_CEN + Vector((0, 0, 0.22 * (1 - lower)))
    for H, rig, side in ((HA, BURA, 1), (HB, BURB, -1)):
        pos = Vector((0.0, side * 0.62, 0)); yaw = 180 if side > 0 else 0
        stand(H, rig, f, pos, yaw=yaw, flex=34 + breath, head=(4, 0), hands=False, crouch=0.10 + 0.08 * lower, root_flex=22)
        for s, sx in (("L", 1), ("R", -1)):
            c = Matrix.Rotation(R_(yaw), 3, 'Z')
            hx = (c @ Vector((0.17 * sx, 0, 0))).x
            tp = top_point(DEADMESH, hx, side * 0.12)
            tp = tp if tp else cen + Vector((hx, side * 0.12, 0.2))
            place_hand(rig, s, f, tp + Vector((0, 0, 0.004)), (0, 0, -1), c @ Vector((0, -1, -0.3)), skin=0.012)
            apply_pose(rig, s, "relaxed", f)

def S01(f0, f1):
    PRESENT["01"] = {"bA", "bB"}
    for k, f in enumerate((f0, f0 + (f1 - f0) // 3, f0 + 2 * (f1 - f0) // 3, f1)):
        bur_hold(f, k / 3.0, breath=1.5 * math.sin(k))
    cam_move("01", f0, f1, ((-4.6, -1.3, 1.35), (0, 0, 0.1)), ((-4.0, -1.1, 1.2), (0, 0, 0.05)), 32)

def under_cam(sid, f0, f1, a, b, lens=30, fstop=8.0, mid=None):
    return cam_move(sid, f0, f1, a, b, lens, fstop, mid=mid)

def bur_stand_by(f, d=1.3, yawA=180, yawB=0, head=(12, 0), breath=0.0):
    stand(HA, BURA, f, Vector((-0.8, d + 0.4, 0)), yaw=200, flex=6 + breath, head=head)
    stand(HB, BURB, f, Vector((1.0, d + 0.3, 0)), yaw=160, flex=6 - breath, head=head)

def S02(f0, f1):
    PRESENT["02"] = {"bA", "bB"}
    dead_place(f0, (0, 0), FLOOR); dead_place(f1, (0, 0), FLOOR); bur_stand_by(f0); bur_stand_by(f1, breath=2)
    c = DEAD_CEN
    under_cam("02", f0, f1, (c + Vector((-0.55, -1.05, 0.05)), c + Vector((0, 0, 0))), (c + Vector((0.25, -1.0, 0.12)), c + Vector((0.05, 0, 0.0))), 32)

def S03(f0, f1):
    PRESENT["03"] = {"bA", "bB"}
    dead_place(f0, (0, 0), FLOOR); dead_place(f1, (0, 0), FLOOR); bur_stand_by(f0); bur_stand_by(f1, breath=2)
    c = DEAD_CEN
    under_cam("03", f0, f1, (c + Vector((0.95, -0.75, 0.25)), c + Vector((0.1, 0, -0.05))), (c + Vector((0.75, -0.55, 0.18)), c + Vector((0.15, 0, -0.05))), 32)

STAKE_PUSH = None
def S04(f0, f1):
    # simplest safe staging (the hand-on-stake versions clipped five times): the stakes stand driven around her,
    # both men stand behind in the water, the camera tracks low along the stakes underwater
    PRESENT["04"] = {"bA", "bB"}
    dead_place(f0, (0, 0), FLOOR); dead_place(f1, (0, 0), FLOOR)
    bur_stand_by(f0, d=1.6, head=(14, 6)); bur_stand_by(f1, d=1.6, breath=2, head=(18, -6))
    c = DEAD_CEN
    under_cam("04", f0, f1, (c + Vector((1.35, -1.25, 0.05)), c + Vector((0.1, 0, 0.12))), (c + Vector((0.75, -1.55, 0.08)), c + Vector((-0.05, 0, 0.12))), 26)

def S05(f0, f1):
    PRESENT["05"] = {"bA", "bB"}
    dead_place(f0, (0, 0), FLOOR); dead_place(f1, (0, 0), FLOOR); bur_stand_by(f0, d=1.6); bur_stand_by(f1, d=1.6, breath=2, head=(16, -8))
    c = DEAD_CEN
    under_cam("05", f0, f1, (c + Vector((-1.9, -1.5, 0.15)), c + Vector((0, 0, 0.1))), (c + Vector((-1.2, -1.9, 0.2)), c + Vector((0, 0, 0.1))), 26)

def S06(f0, f1):
    PRESENT["06"] = {"bA", "bB"}
    dead_place(f0, (0, 0), FLOOR); dead_place(f1, (0, 0), FLOOR); bur_stand_by(f0, d=1.6); bur_stand_by(f1, d=1.6, breath=2)
    c = DEAD_CEN
    under_cam("06", f0, f1, (c + Vector((1.5, -0.25, -0.12)), c + Vector((0, 0, 0.12))), (c + Vector((1.3, 0.35, -0.10)), c + Vector((0, 0, 0.15))), 24)

def S07(f0, f1):
    PRESENT["07"] = {"bA", "bB"}
    # the body tries to rise 3 cm, the crossed stakes keep it down (2 slow swells)
    for k in range(5):
        f = f0 + k * (f1 - f0) // 4
        dead_place(f, (0, 0), FLOOR, lift=0.03 if k % 2 else 0.0)
    bur_stand_by(f0, d=1.6); bur_stand_by(f1, d=1.6, breath=2)
    c = DEAD_CEN
    under_cam("07", f0, f1, (c + Vector((-0.2, -1.25, -0.08)), c + Vector((0, 0, 0.25))), (c + Vector((0.2, -1.1, -0.1)), c + Vector((0, 0, 0.45))), 22)

# wolf at the bank, sniffing toward the stakes of burial 4 (3.3, 0.2)
def wolf_pose(head=(0, 0, 0), tail=0.0):
    return {"neck1": (None, (head[0], head[1], head[2] * 0.5)), "head": (None, (0, 0, head[2] * 0.5)), "tail1": (None, (tail, 0, 0)), "tail2": (None, (tail * 0.5, 0, 0))}
RWOLF = Rig(WOLF)
for pb in WOLF.pose.bones: pb.rotation_mode = 'QUATERNION'
WP0 = Vector((7.6, 1.8, 0)); WP1 = Vector((4.95, 0.75, 0))
WHEAD = math.atan2((WP1 - WP0).x, -(WP1 - WP0).y)
def wolf_head(f, neck=(0, 0, 0), tail=0.0):
    for n, r in (("neck1", (-neck[0] * 0.6, neck[1], neck[2] * 0.5)), ("head", (-neck[0] * 0.4, 0, neck[2] * 0.5)),
                 ("tail1", (tail, 0, 0)), ("tail2", (tail * 0.5, 0, 0))):
        if n in RWOLF.PB:
            RWOLF.PB[n].rotation_quaternion = Euler(tuple(R_(v) for v in r)).to_quaternion()
            RWOLF.PB[n].keyframe_insert("rotation_quaternion", frame=f, group=n)
def S08(f0, f1):
    PRESENT["08"] = {"wolf"}
    WOLF.location = (0, 0, 0); WOLF.keyframe_insert("location", frame=f0); WOLF.keyframe_insert("location", frame=f1)
    path = lambda f: WP0.lerp(WP1, ease(min(1.0, max(0.0, (f - f0) / (f1 - f0 - 30)))))
    quad_move(RWOLF, path, f0, f1, 0.55, gait="walk", heading_fn=lambda f: WHEAD)
    for f, nk, tl in ((f0, (5, 0, 0), 10), ((f0 + f1) // 2, (-5, 0, 6), 14), (f1 - 20, (-20, 0, 0), 12), (f1, (-28, 0, 0), 10)):
        wolf_head(f, nk, tl)
    cam_move("08", f0, f1, ((7.4, -2.3, 1.25), (5.9, 1.2, 0.35)), ((7.0, -1.9, 1.15), (5.2, 0.9, 0.3)), 30)

def S09(f0, f1):
    PRESENT["09"] = {"wolf"}
    WOLF.location = (0, 0, 0); WOLF.keyframe_insert("location", frame=f0); WOLF.keyframe_insert("location", frame=f1)
    quad_move(RWOLF, lambda f: WP1.copy(), f0, f1, 0.55, gait="walk", heading_fn=lambda f: WHEAD)
    for f, nk, tl in ((f0, (-28, 0, 0), 10), (f0 + 40, (-40, 0, 8), 12), (f0 + 75, (-32, 0, -10), 14), (f0 + 100, (-8, 0, 30), 16), (f1, (2, 0, 40), 22)):
        wolf_head(f, nk, tl)
    cam_move("09", f0, f1, ((3.5, -1.3, 0.95), (4.95, 0.75, 0.45)), ((3.7, -1.05, 0.9), (4.95, 0.75, 0.42)), 40)

LEAVES = []
def S10(f0, f1):
    PRESENT["10"] = {"bA", "bB"}
    dead_place(f0, (0, 0), FLOOR); dead_place(f1, (0, 0), FLOOR); bur_stand_by(f0, d=1.8); bur_stand_by(f1, d=1.8, breath=2)
    leaf_m = mat("DeadLeaf", (0.45, 0.30, 0.12), 0.7)
    for k in range(45):
        bpy.ops.mesh.primitive_circle_add(vertices=12, radius=0.035, fill_type='NGON')
        l_ = bpy.context.active_object; l_.name = f"Leaf{k}"; l_.scale = (0.45, 1.0, 1.0); l_.data.materials.append(leaf_m)
        sb = l_.modifiers.new("b", 'SIMPLE_DEFORM'); sb.deform_method = 'BEND'; sb.angle = R_(40); sb.deform_axis = 'X'
        move_to(l_, CB); LEAVES.append(l_)
        x, y = random.uniform(-1.4, 1.4), random.uniform(-1.0, 1.0)
        while abs(x) < 0.55 and abs(y) < 0.40:          # never through the body
            x, y = random.uniform(-1.4, 1.4), random.uniform(-1.0, 1.0)
        d0 = f0 + random.randint(0, 90); dur = random.randint(70, 110)
        z1 = bog_z(x, y) + 0.02
        for f, z in ((f0, -0.05), (d0, -0.05), (d0 + dur, z1), (f1, z1)):
            l_.location = (x, y, z); l_.keyframe_insert("location", frame=f)
            l_.rotation_euler = (0.3 * math.sin(f * 0.05 + k), 0.3 * math.cos(f * 0.04 + k), k + f * 0.01); l_.keyframe_insert("rotation_euler", frame=f)
        vis(l_, [(f0, f1)])
    # peat layer rises from the floor and closes over the body
    pl = grid_terrain("PeatRise", 5.0, 50, lambda x, y: 0.02 * noise2(x * 3, y * 3), bog_mud, CB)
    for f, z in ((f0, FLOOR - 0.06), (f0 + 40, FLOOR - 0.06), (f1 - 10, TOPZ + 0.02), (f1, TOPZ + 0.02)):
        pl.location = (0, 0, z); pl.keyframe_insert("location", frame=f)
    vis(pl, [(f0, f1)])
    c = DEAD_CEN
    under_cam("10", f0, f1, (c + Vector((-0.4, -1.7, 0.30)), c + Vector((0, 0, 0.0))), (c + Vector((-0.2, -1.5, 0.42)), c + Vector((0, 0, 0.0))), 26, 22.0)   # f/22: the near peat stays sharp

def S11(f0, f1):
    PRESENT["11"] = set()
    z_end = LID.location.z
    for f, dz in ((f0, 0.9), (f0 + 8, 0.9), (f0 + min(62, f1 - f0 - 12), 0.0), (f1, 0.0)):
        LID.location.z = z_end + dz; LID.keyframe_insert("location", frame=f)
    cam_move("11", f0, f1, (CX + Vector((0.7, -2.8, 0.3)), CX + Vector((0, 0, -0.32))), (CX + Vector((0.3, -2.0, -0.05)), CX + Vector((0, 0, -0.42))), 30)

def S12(f0, f1):
    PRESENT["12"] = set()
    LID.keyframe_insert("location", frame=f0)
    top = TOPZ + NICHE + 0.55
    vis(WATERCUT, [(f0, f1)])
    for k, b in enumerate(BUBS):
        x = random.uniform(-1.3, 1.3); y = random.uniform(-0.45, -0.25)
        d0 = f0 + random.randint(0, 14); fall = random.randint(20, 30)
        p0 = CX + Vector((x, y, top + 0.62)); p1 = CX + Vector((x + 0.05, y, top + 0.07)); p2 = CX + Vector((x + 0.2, y, top + 0.45))
        for f, p in ((f0, p0), (d0, p0), (d0 + fall, p1), (d0 + fall + 22, p2), (max(f1, d0 + fall + 23), p2 + Vector((0.05, 0, 0.12)))):
            b.location = p; b.keyframe_insert("location", frame=f)
        b.scale = (1, 1, 1); b.keyframe_insert("scale", frame=d0 + fall - 4)
        b.scale = (1.25, 1.25, 0.7); b.keyframe_insert("scale", frame=d0 + fall + 2)
        b.scale = (1, 1, 1); b.keyframe_insert("scale", frame=d0 + fall + 10)
        vis(b, [(f0, f1)])
    cam_move("12", f0, f1, (CX + Vector((-0.5, -3.0, 0.7)), CX + Vector((0, 0, -0.05))), (CX + Vector((-0.2, -2.6, 0.6)), CX + Vector((0, 0, -0.1))), 30)

def S13(f0, f1):
    PRESENT["13"] = {"bA", "bB"}
    dead_place(f0, (0, 0), FLOOR); dead_place(f1, (0, 0), FLOOR); bur_stand_by(f0, d=1.8); bur_stand_by(f1, d=1.8, breath=2)
    c = DEAD_CEN
    under_cam("13", f0, f1, (c + Vector((0.80, -0.72, 0.14)), c + Vector((0.02, -0.22, 0.02))), (c + Vector((0.55, -0.55, 0.09)), c + Vector((0.02, -0.24, 0.02))), 32)

def S14(f0, f1):
    PRESENT["14"] = {"wk"}
    a = SX + Vector((1.2, -1.2, 0)); b_ = SX + Vector((-0.5, -3.1, 0))
    path = lambda f: a.lerp(b_, (f - f0) / (f1 - f0))
    yw = math.degrees(math.atan2((b_ - a).x, -(b_ - a).y))
    walk_swing(HW, WORK, path, lambda f: yw, f0, f1)
    cam_move("14", f0, f1, (SX + Vector((-4.2, -7.0, 3.6)), SX + Vector((1.8, 1.4, 0.9))), (SX + Vector((-3.0, -5.6, 2.6)), SX + Vector((1.6, 1.2, 0.9))), 32)

def S15(f0, f1):
    PRESENT["15"] = {"wk"}
    L = LOGO1.location.copy(); L.z = 0
    sgn = 1 if LOGO_T.dot(TRK.matrix_world.to_3x3() @ Vector((0, -1, 0))) > 0 else -1     # +: toward the truck's nose
    a = L + LOGO_N * 0.75 + LOGO_T * sgn * 1.30; b_ = L + LOGO_N * 0.75 + LOGO_T * sgn * 0.78
    path = lambda f: a.lerp(b_, min(1.0, (f - f0) / (f1 - f0 - 20)))
    d = b_ - a; yw = math.degrees(math.atan2(d.x, -d.y))
    walk_swing(HW, WORK, path, lambda f: yw, f0, f1)
    Lw = LOGO1.location
    print("BUILD S15 cam", tuple(round(v, 2) for v in Lw + LOGO_N * 3.0), tuple(round(v, 2) for v in LOGO_N), sgn)
    cam_move("15", f0, f1, (Lw + LOGO_N * 2.9 + LOGO_T * sgn * 0.35 + Vector((0, 0, 0.25)), Lw + LOGO_T * sgn * 0.22 + Vector((0, 0, 0.05))),
             (Lw + LOGO_N * 2.5 + LOGO_T * sgn * 0.3 + Vector((0, 0, 0.22)), Lw + LOGO_T * sgn * 0.2 + Vector((0, 0, 0.05))), 28)

def S16(f0, f1):
    PRESENT["16"] = {"wk"}
    pos = SX + Vector((0.55, 1.05, 0)); yw = 0
    stand(HW, WORK, f0, pos, yaw=yw, flex=10, head=(20, 0))
    stand(HW, WORK, f0 + 50, pos, yaw=yw, flex=28, head=(28, 0), crouch=0.05)
    stand(HW, WORK, f1, pos, yaw=yw, flex=30, head=(30, -6), crouch=0.06)
    sk = SKULL.location
    cam_move("16", f0, f1, (sk + Vector((0.75, -1.45, 0.5)), sk + Vector((0, 0.45, 0.62))), (sk + Vector((0.6, -1.25, 0.42)), sk + Vector((0, 0.4, 0.55))), 24)

def arch_kneel(f, pos, yaw, reach=0.0, head=(30, 0), brush=False):
    """archaeologist kneels at the pit edge: knees and shins on the ground, upper body leaning in"""
    c = Matrix.Rotation(R_(yaw), 3, 'Z'); gz = dgz(pos.x, pos.y)
    HAR.key_root(f, Vector((pos.x, pos.y, gz + 0.59)) + c @ Vector((0, 0.10, 0)), yaw=yaw, flex=18)
    for s, sx in (("L", 1), ("R", -1)):
        fp = pos + c @ Vector((0.12 * sx, 0.55, 0)); a_ = HAR.ankle[s]
        M = Matrix.Translation(Vector((fp.x, fp.y, dgz(fp.x, fp.y) + 0.10))) @ Matrix.Rotation(R_(yaw), 4, 'Z') @ Matrix.Rotation(R_(-80), 4, 'X') @ \
            Matrix.Translation(-a_) @ RAR.rest("IK_foot." + s)
        RAR.key_world("IK_foot." + s, f, M)
        pole = pos + c @ Vector((0.12 * sx, -0.6, 0.3)); pbn = "Pole_knee." + s; pb = RAR.PB[pbn]
        pb.location = RAR.rest(pbn).to_3x3().inverted() @ (pole - RAR.BN[pbn].head_local); pb.keyframe_insert("location", frame=f, group=pbn)
    HAR.key_spine(f, flex=24 + reach * 10, head=head)
    # left hand on the left thigh; right hand per shot
    place_hand(ARCH, "L", f, Vector((pos.x, pos.y, gz)) + c @ Vector((0.14, -0.12, 0.52)), (0, 0, -1), c @ Vector((0, -1, -0.2)))
    apply_pose(ARCH, "L", "relaxed", f)

def arch_rhand(f, pos, yaw):
    c = Matrix.Rotation(R_(yaw), 3, 'Z'); gz = dgz(pos.x, pos.y)
    place_hand(ARCH, "R", f, Vector((pos.x, pos.y, gz)) + c @ Vector((-0.14, -0.12, 0.52)), (0, 0, -1), c @ Vector((0, -1, -0.2)))
    apply_pose(ARCH, "R", "relaxed", f)

def S17(f0, f1):
    PRESENT["17"] = {"ar"}
    pos = DX + Vector((0.0, -1.05, 0)); yaw = 180
    for f, r in ((f0, 0.0), ((f0 + f1) // 2, 0.5), (f1, 1.0)):
        arch_kneel(f, pos, yaw, r, head=(10, 6 * r))
        arch_rhand(f, pos, yaw)
    cam_move("17", f0, f1, (DX + Vector((1.3, 1.9, 1.35)), DX + Vector((0, -0.45, 0.25))), (DX + Vector((1.0, 1.6, 1.15)), DX + Vector((0, -0.5, 0.25))), 30)

def S18(f0, f1):
    PRESENT["18"] = {"ar"}
    pos = DX + Vector((0.0, -1.05, 0))
    arch_kneel(f0, pos, 180, 0.5); arch_kneel(f1, pos, 180, 0.6); arch_rhand(f0, pos, 180); arch_rhand(f1, pos, 180)
    o = camera("18", 26, 8)
    cam_key(o, f0, DX + Vector((0.3, -2.0, 6.0)), DX + Vector((0, 0, 0)), 26)
    cam_key(o, f1, DX + Vector((0.8, -3.5, 19.0)), DX + Vector((0, 0.5, 0)), 26)

BRUSH_OBJ = None
def S19(f0, f1):
    PRESENT["19"] = {"ar"}
    pos = DX + Vector((0.05, -0.95, 0)); yaw = 180
    # she sweeps the loose soil 0.36 m from the bones with her flat right hand (no tool, nothing touches the bones)
    tgt = SK_CEN + Vector((0.05, -0.36, 0.0))
    for k, f in enumerate(list(range(f0, f1, 15)) + [f1]):
        arch_kneel(f, pos, yaw, 0.8, head=(22, 4))
        hp = tgt + Vector((0.06 * math.sin(k * 1.3), -0.03 * math.cos(k * 1.3), 0)); hp.z = dgz(hp.x, hp.y)
        place_hand(ARCH, "R", f, hp, (0, 0, -1), (0, 1, 0), skin=0.014)
        apply_pose(ARCH, "R", "relaxed", f)
    cam_move("19", f0, f1, (DX + Vector((1.2, 1.6, 1.3)), SK_CEN + Vector((0, -0.5, 0.25))), (DX + Vector((1.0, 1.35, 1.15)), SK_CEN + Vector((0, -0.5, 0.2))), 32)

def S20(f0, f1):
    PRESENT["20"] = set()
    for k, s_ in enumerate(SEEDS[:1]):
        pass
    for f, v in ((f0, 0.5), (f0 + 30, 0.5), (f0 + 65, 6.0), (f1 - 30, 4.5), (f1, 4.5)):
        emit_key(seed_m, f, v)
    a = ABD
    fw = fwd_abd
    side = Vector((0, 0, 1)).cross(fw).normalized()
    cam_move("20", f0, f1, (a + fw * 0.42 + side * 0.06 + Vector((0, 0, 0.40)), a + Vector((0, 0, 0.01))), (a + fw * 0.32 + side * 0.04 + Vector((0, 0, 0.30)), a + Vector((0, 0, 0.01))), 45, 11)

def S21(f0, f1):
    PRESENT["21"] = set()
    c = BR.location
    cam_move("21", f0, f1, (c + Vector((0.2, -0.32, 0.30)), c + Vector((0, 0, 0.02))), (c + Vector((-0.08, -0.30, 0.27)), c + Vector((0, 0, 0.02))), 35, 11)

def S22(f0, f1):
    PRESENT["22"] = set()
    c = SK_CEN
    cam_move("22", f0, f1, (c + Vector((1.1, -0.9, 0.9)), c + Vector((0, 0, -0.05))), (c + Vector((0.45, -0.85, 0.55)), c + Vector((0, 0, -0.05))), 30, 9)

def S23(f0, f1):
    PRESENT["23"] = set()
    c = SK_CEN; o = camera("23", 30, 9)
    for k, f in enumerate((f0, (f0 + f1) // 2, f1)):
        a_ = R_(-90 + 22 * k)
        cam_key(o, f, c + Vector((0.12 * math.cos(a_), 0.12 * math.sin(a_), 1.75 - 0.08 * k)), c + Vector((0, 0.001, 0)), 30)

def S24(f0, f1):
    PRESENT["24"] = set()
    # the same curled body, as she was laid down: placed in the pit exactly where the skeleton lies
    dead_place(f0, (SK_CEN.x, SK_CEN.y), pit_floor); dead_place(f1, (SK_CEN.x, SK_CEN.y), pit_floor)
    c = SK_CEN; o = camera("24", 30, 9)
    for k, f in enumerate((f0, (f0 + f1) // 2, f1)):
        a_ = R_(-46 + 22 * k)
        cam_key(o, f, c + Vector((0.12 * math.cos(a_), 0.12 * math.sin(a_), 1.55 - 0.1 * k)), c + Vector((0, 0.001, 0)), 30)

FUN = {sid: globals()["S" + sid] for sid, _, _, _ in lay}

def park(key, f):
    if key == "wolf":
        WOLF.location = PARK["wolf"]; WOLF.keyframe_insert("location", frame=f); return
    rig, H = CHARS[key]
    stand(H, rig, f, PARK[key])

for sid, st, f0, f1 in lay:
    FUN[sid](f0, f1)
    pres = PRESENT[sid]
    for key in ("bA", "bB", "wk", "ar", "wolf"):
        if key not in pres:
            park(key, f0); park(key, f1)
    print("BUILD shot", sid, st, f0, f1, sorted(pres))

# visibility by shot
def rng(*sids): return [(SH[s][1], SH[s][2]) for s in sids if s in SH]
for o in STK_MAIN + OB: vis(o, rng("04", "05", "06", "07", "08", "09", "10"))
for o in list(SKO.children) + [SKO]: pass
vis(SKO, rng("17", "18", "19", "20", "21", "22", "23"))
vis(WATER, rng("01", "08", "09")); vis(WUNDER, rng("02", "03", "04", "05", "06", "07", "10", "13")); vis(WVOL, rng("02", "03", "04", "05", "06", "07", "10", "13"))
vis(CLOTH, rng("22", "23"))
for s_ in SEEDS + [FIB]: vis(s_, rng("19", "20", "21"))
# the Dead rig only renders in the bog shots and the last shot
for ch in DEAD.children: vis(ch, rng("01", "02", "03", "04", "05", "06", "07", "10", "13", "24"))


# hard cuts: the last key of every shot is constant (no inbetween across a cut)
BOUND = set()
for sid, st, f0, f1 in lay: BOUND |= {f0, f1}
LASTS = {f1 for _, _, _, f1 in lay}
def all_fcurves(action):
    try:
        return list(action.fcurves)
    except Exception:
        out = []
        for layer in action.layers:
            for strip in layer.strips:
                for cb in strip.channelbags: out += list(cb.fcurves)
        return out
for idb in list(bpy.data.objects) + list(bpy.data.materials) + list(bpy.data.lights) + list(bpy.data.cameras):
    ad = getattr(idb, "animation_data", None)
    if not ad or not ad.action: continue
    for fc in all_fcurves(ad.action):
        for kp in fc.keyframe_points:
            fr = int(round(kp.co.x))
            if fr in BOUND: kp.handle_left_type = 'VECTOR'; kp.handle_right_type = 'VECTOR'
            if fr in LASTS: kp.interpolation = 'CONSTANT'
        fc.update()
nta = seed_m.node_tree.animation_data
if nta and nta.action:
    for fc in all_fcurves(nta.action):
        for kp in fc.keyframe_points: kp.interpolation = 'LINEAR'

for sid, st, f0, f1 in lay:
    mk = sc.timeline_markers.new("S" + sid, frame=f0); mk.camera = CAMS[sid]
# the client VO, from frame 1
VO = "/home/user/Muhammed/blender/BogBurials_v002b/BogBurials_v002b_VO.mp3"
se = sc.sequence_editor_create()
coll_ = se.strips if hasattr(se, "strips") else se.sequences
snd = coll_.new_sound("VO", VO, channel=1, frame_start=1)
print("BUILD VO strip", snd.frame_final_start, snd.frame_final_end)
sc.camera = CAMS[lay[0][0]]

# camera-only catchlights for the faces
for nm, rig in (("CatchW", WORK), ("CatchR", ARCH)):
    L = bpy.data.lights.new(nm, 'POINT'); L.energy = 4; L.shadow_soft_size = 0.02
    o = bpy.data.objects.new(nm, L); sc.collection.objects.link(o)
    o.parent = rig; o.location = (0.1, -0.6, 1.75)
    o.visible_diffuse = False; o.visible_glossy = True; o.visible_transmission = False; o.visible_volume_scatter = False
# look
sc.render.engine = 'CYCLES'; sc.cycles.samples = 48; sc.cycles.use_denoising = True
sc.cycles.max_bounces = 8; sc.cycles.transmission_bounces = 8; sc.cycles.transparent_max_bounces = 16
sc.view_settings.view_transform = 'AgX'
try: sc.view_settings.look = 'AgX - Punchy'
except Exception: pass
sc.render.use_motion_blur = False
for o in bpy.data.collections["PROPS"].objects: o.hide_render = o.hide_viewport = True
for o in LIBC.objects: o.hide_render = o.hide_viewport = True

bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("BUILD_OK", OUT, "frames", sc.frame_start, sc.frame_end)
