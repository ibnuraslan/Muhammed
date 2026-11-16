"""DogShootsOwner: sets, per-shot animation at 1x, one camera per shot with hard-cut markers, look.
blender -b lib.blend --python 02_build.py -- <out.blend> [brand_dir]
Shot lengths come from shots.py (Phase 2: VO frames). Every shot is keyed from its own start frame."""
import bpy, sys, math, os, random, bmesh
from mathutils import Vector, Matrix, Euler, Quaternion
argv = sys.argv[sys.argv.index("--") + 1:]
OUT = argv[0]
HERE = os.path.dirname(os.path.abspath(__file__)) if "__file__" in dir() else "/home/user/Muhammed/blender/DogShootsOwner_v001/scripts"
HERE = "/home/user/Muhammed/blender/DogShootsOwner_v001/scripts"
BRAND = "/home/user/Muhammed/blender/assets/brand/"
P = "/home/user/Muhammed/blender/pipeline/"
exec(open(P + "anim_lib.py").read()); exec(open(P + "hand_poses.py").read())
exec(open(HERE + "/shots.py").read())
R_ = math.radians
random.seed(7)
sc = bpy.context.scene
sc.render.fps = 60; sc.render.resolution_x = 1080; sc.render.resolution_y = 1920
SH = {sid: (st, f0, f1) for sid, st, f0, f1 in layout()}
FEND = max(f1 for _, f1 in [(v[1], v[2]) for v in SH.values()])
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
    (c or src.users_collection[0]).objects.link(o); bpy.context.view_layer.update(); return o

def area(name, loc, target, energy, size, c, color=(1, 1, 1)):
    L = bpy.data.lights.new(name, 'AREA'); L.energy = energy; L.size = size; L.color = color
    o = bpy.data.objects.new(name, L); c.objects.link(o); o.location = loc
    o.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler(); return o

def point(name, loc, energy, c, color=(1, 1, 1), r=0.05):
    L = bpy.data.lights.new(name, 'POINT'); L.energy = energy; L.color = color; L.shadow_soft_size = r
    o = bpy.data.objects.new(name, L); c.objects.link(o); o.location = loc; return o

def logo_decal(name, loc, rot, width, dark, c, parent=None):
    img = bpy.data.images.load(BRAND + ("DaKrasFilms_logo_dark.png" if dark else "DaKrasFilms_logo_white.png"), check_existing=True)
    m = bpy.data.materials.new(name + "_mat"); m.use_nodes = True; nt = m.node_tree
    pr = nt.nodes["Principled BSDF"]; tx = nt.nodes.new("ShaderNodeTexImage"); tx.image = img
    nt.links.new(tx.outputs["Color"], pr.inputs["Base Color"]); nt.links.new(tx.outputs["Alpha"], pr.inputs["Alpha"])
    pr.inputs["Roughness"].default_value = 0.5
    m.blend_method = 'BLEND' if hasattr(m, "blend_method") else None
    o = plane(name, (width, width * 414 / 967), loc, m, c, rot)
    if parent:
        mw = o.matrix_world.copy(); o.parent = parent; o.matrix_world = mw
    return o

# ------------------------------------------------------------------ world: sky gradient seen by camera, soft light
w = bpy.data.worlds.new("Sky"); sc.world = w; w.use_nodes = True; nt = w.node_tree; nt.nodes.clear()
o_ = nt.nodes.new("ShaderNodeOutputWorld"); lp = nt.nodes.new("ShaderNodeLightPath")
tc = nt.nodes.new("ShaderNodeTexCoord"); sep = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(tc.outputs["Generated"], sep.inputs[0])
mr = nt.nodes.new("ShaderNodeMapRange"); mr.inputs["From Min"].default_value = -0.05; mr.inputs["From Max"].default_value = 0.5
nt.links.new(sep.outputs["Z"], mr.inputs["Value"])
ramp = nt.nodes.new("ShaderNodeValToRGB"); ramp.color_ramp.elements[0].color = (0.72, 0.90, 1.0, 1); ramp.color_ramp.elements[1].color = (0.10, 0.52, 0.95, 1)
nt.links.new(mr.outputs["Result"], ramp.inputs["Fac"])
bg_cam = nt.nodes.new("ShaderNodeBackground"); nt.links.new(ramp.outputs["Color"], bg_cam.inputs["Color"]); bg_cam.inputs["Strength"].default_value = 1.0
bg_lit = nt.nodes.new("ShaderNodeBackground"); bg_lit.inputs["Color"].default_value = (0.85, 0.92, 1.0, 1); bg_lit.inputs["Strength"].default_value = 1.2
SUN = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", "SUN")); sc.collection.objects.link(SUN)
SUN.data.energy = 2.5; SUN.data.angle = R_(8); SUN.rotation_euler = (R_(40), R_(10), R_(35))
mix = nt.nodes.new("ShaderNodeMixShader"); nt.links.new(lp.outputs["Is Camera Ray"], mix.inputs["Fac"])
nt.links.new(bg_lit.outputs[0], mix.inputs[1]); nt.links.new(bg_cam.outputs[0], mix.inputs[2]); nt.links.new(mix.outputs[0], o_.inputs[0])

# ------------------------------------------------------------------ library objects
OWNER = bpy.data.objects["Owner"]; MEDA = bpy.data.objects["MedA"]; MEDB = bpy.data.objects["MedB"]
DOG = bpy.data.objects["Dog_rig"]; DOGB = bpy.data.objects["Dog_body"]
GUN = bpy.data.objects["Shotgun"]; PHONE = bpy.data.objects["Phone"]; SEAT = bpy.data.objects["CarSeat"]
CRATE = bpy.data.objects["Crate"]; BED = bpy.data.objects["Bed"]; AMB = bpy.data.objects["Ambulance"]
SKEL = bpy.data.objects["Skeleton"]; LUNGS = bpy.data.objects["Lungs"]
PLANTS = {o.name: o for o in bpy.data.collections["PLANTS"].objects}
keep = {"PH_fir_tree_01_a_LOD2", "PH_fir_tree_01_b_LOD2", "PH_fir_tree_01_c_LOD2", "PH_fir_sapling_medium_a_LOD1",
        "PH_fir_sapling_medium_b_LOD1", "PH_fern_02_b", "PH_fern_02_c", "PH_grass_medium_01_large_a_LOD1",
        "PH_grass_medium_01_large_b_LOD1", "PH_grass_medium_01_mid_a_LOD1", "PH_shrub_02_a_LOD1", "PH_shrub_02_c_LOD1", "PH_tree_stump_01"}
for n, o in list(PLANTS.items()):
    if n not in keep: bpy.data.objects.remove(o, do_unlink=True); PLANTS.pop(n)
for o in PLANTS.values(): o.location = (0, 0, -50)
LIBC = bpy.data.collections["PLANTS"]

# ------------------------------------------------------------------ SET 1: truck cab (x=0). Truck front = -Y. Driver on +X.
CT = coll("SET_truck")
beige = mat("SeatBeige", (0.78, 0.68, 0.52), 0.65); trim = mat("TrimGrey", (0.32, 0.31, 0.30), 0.55)
carpet = mat("Carpet", (0.16, 0.16, 0.17), 0.9); roofm = mat("Headliner", (0.80, 0.77, 0.72), 0.8)
dash = mat("Dash", (0.20, 0.20, 0.21), 0.5); glass = mat("Glass", (0.8, 0.9, 1.0), 0.05, alpha=0.08)
BZ = 0.48                       # rear bench cushion top
DRV = Vector((0.40, -0.30, 0.0))  # driver seat base (centre of cushion, floor level)
rbox("FloorCab", (1.7, 2.6, 0.06), (0, -0.2, -0.03), carpet, CT, 0.01)
rbox("Roof", (1.7, 2.6, 0.05), (0, -0.2, 1.56), roofm, CT, 0.02)
# rear bench: cushion + back with seams (two cushions)
for i, x in enumerate((-0.37, 0.37)):
    rbox(f"BenchCushion{i}", (0.72, 0.56, 0.14), (x, 0.73, BZ - 0.07), beige, CT, 0.05)
    rbox(f"BenchBack{i}", (0.72, 0.14, 0.62), (x, 1.04, BZ + 0.28), beige, CT, 0.05, rot=(R_(-12), 0, 0))
rbox("BenchBase", (1.5, 0.5, BZ - 0.14), (0, 0.75, (BZ - 0.14) / 2), trim, CT, 0.02)
rbox("RearWall", (1.7, 0.06, 1.6), (0, 1.17, 0.8), trim, CT, 0.01)
# front seats (real model, faces +Y in the library; turn it to face -Y)
for nm, x in (("SeatDriver", DRV.x), ("SeatPass", -DRV.x)):
    s = dup(SEAT, nm, (x, DRV.y + 0.06, 0.0), (0, 0, R_(180)), (0.84, 0.80, 0.82), CT, linked=False)
    s.data.materials.clear(); s.data.materials.append(beige)
SDRV = bpy.data.objects["SeatDriver"]; bpy.context.view_layer.update()
_sp = [SDRV.matrix_world @ v.co for v in SDRV.data.vertices]
CUSH_Z = max(p.z for p in _sp if abs(p.x - DRV.x) < 0.1 and DRV.y - 0.30 < p.y < DRV.y + 0.05 and p.z < 0.62)
BACK_FRONT_Y = min(p.y for p in _sp if abs(p.x - DRV.x) < 0.12 and 0.72 < p.z < 0.82)
print("BUILD seat cushion z", round(CUSH_Z, 3), "back front y", round(BACK_FRONT_Y, 3), "zmax", round(max(p.z for p in _sp), 3), "ymin/max", round(min(p.y for p in _sp), 3), round(max(p.y for p in _sp), 3))
SEAT_TOP = Vector((DRV.x, BACK_FRONT_Y - 0.33, CUSH_Z + 0.08))
# side doors with window openings (lower panel + pillars, no glass in the opening)
for sx in (-1, 1):
    rbox(f"DoorLow{sx}", (0.06, 2.4, 0.82), (0.85 * sx, -0.2, 0.41), trim, CT, 0.02)
    rbox(f"DoorArm{sx}", (0.10, 1.9, 0.08), (0.80 * sx, -0.1, 0.70), beige, CT, 0.03)
    for y in (-1.45, 0.15, 1.12):
        rbox(f"Pillar{sx}_{y}", (0.07, 0.10, 0.76), (0.85 * sx, y, 1.19), trim, CT, 0.02)
rbox("Dashboard", (1.7, 0.45, 0.35), (0, -1.32, 0.80), dash, CT, 0.06)
rbox("DashTop", (1.6, 0.30, 0.06), (0, -1.40, 0.99), dash, CT, 0.03)
# steering wheel
bpy.ops.mesh.primitive_torus_add(major_radius=0.19, minor_radius=0.018, location=(DRV.x, -1.02, 1.0), rotation=(R_(65), 0, 0))
wh = bpy.context.active_object; wh.name = "Wheel"; wh.data.materials.append(dash); move_to(wh, CT); bpy.ops.object.shade_smooth()
cyl("WheelHub", 0.05, 0.08, (DRV.x, -1.02, 1.0), dash, CT, rot=(R_(65), 0, 0))
cyl("WheelColumn", 0.035, 0.35, (DRV.x, -1.15, 0.93), dash, CT, rot=(R_(65), 0, 0))
for a in (0, 120, 240):
    sp = rbox(f"Spoke{a}", (0.17, 0.02, 0.012), (DRV.x, -1.02, 1.0), dash, CT, 0.005)
    sp.rotation_euler = Euler((R_(65), 0, 0)) ; sp.rotation_euler.rotate_axis('Z', R_(a))
    sp.data.transform(Matrix.Translation((0.085, 0, 0))); sp.location = (DRV.x, -1.02, 1.0)
# outside: grass + firs seen through the windows
grass = mat("GrassGround", (0.30, 0.52, 0.18), 0.9)
plane("TruckGround", (60, 60), (0, 0, -0.45), grass, CT)
for i in range(14):
    a = i / 14 * 2 * math.pi; r = 9 + random.random() * 6
    src = PLANTS[random.choice(["PH_fir_tree_01_a_LOD2", "PH_fir_tree_01_b_LOD2", "PH_fir_tree_01_c_LOD2"])]
    dup(src, f"TruckFir{i}", (math.cos(a) * r, math.sin(a) * r, -0.45), (0, 0, random.random() * 6), 0.8 + random.random() * 0.3, CT)
area("TruckKey", (1.6, -1.6, 2.4), (0, 0.4, 0.7), 260, 1.5, CT)
area("TruckFill", (-1.4, 0.6, 1.9), (0.2, 0.3, 0.8), 90, 1.5, CT, (0.95, 0.97, 1.0))
_sf = area("SeatBackFill", (0.2, 0.6, 1.0), (0.35, 0.0, 0.6), 40, 0.6, CT); _sf.visible_camera = False
area("TruckRoofLight", (0, 0.2, 1.50), (0, 0.2, 0.0), 60, 1.0, CT)
# the shotgun lies on its side on the bench, stock at the back, barrel toward the driver's seat back
G = dup(GUN, "Gun", (0, 0, 0), (0, 0, 0), 0.88, CT, linked=False)
G.rotation_mode = 'XYZ'
BUTT = Vector((0.30, 0.98, BZ + 0.03)); MUZ = Vector((0.33, 0.10, BZ + 0.075))
dvec = (MUZ - BUTT); G.rotation_euler = Euler((R_(90), 0, 0))
G.rotation_euler = (Matrix.Rotation(math.atan2(dvec.y, dvec.x), 3, 'Z') @ Matrix.Rotation(-math.asin(dvec.z / dvec.length), 3, 'Y') @ Matrix.Rotation(R_(90), 3, 'X')).to_euler()
G.location = BUTT + dvec.normalized() * 0.44 + Vector((0, 0, 0.0))
TRIG = BUTT + dvec.normalized() * 0.30 + Vector((0, 0, 0.03))      # trigger/grip area (paw target)
# muzzle flash: emissive star + light, keyed per shot
fl_m = mat("Flash", (1, 0.7, 0.2), 0.5, emit=(1.0, 0.62, 0.15), ew=0.0)
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=0.05, location=MUZ + dvec.normalized() * 0.03)
FLASH = bpy.context.active_object; FLASH.name = "MuzzleFlash"; FLASH.data.materials.append(fl_m); move_to(FLASH, CT)
for v in FLASH.data.vertices:
    v.co *= 1.0 + 1.6 * abs(math.sin(7 * v.co.x / 0.05) * math.cos(5 * v.co.z / 0.05))
FLASH.scale = (0.01, 0.01, 0.01)
FL_L = point("FlashLight", MUZ + dvec.normalized() * 0.05, 0, CT, (1.0, 0.65, 0.25), 0.03)
# seat-back hole (a solid dark hole with torn fabric lip; hidden until the shot)
_hz = MUZ.z + 0.02
def _ray_y(x, z, y0=1.0):
    inv = SDRV.matrix_world.inverted()
    ok_, loc_, n_, i_ = SDRV.ray_cast(inv @ Vector((x, y0, z)), inv.to_3x3() @ Vector((0, -1, 0)))
    return (SDRV.matrix_world @ loc_).y if ok_ else None
SEATBACK_Y = _ray_y(MUZ.x, _hz) + 0.004
print("BUILD seatback y at hole", round(SEATBACK_Y, 3), "muzzle y", round(MUZ.y, 3))
HOLE_P = Vector((MUZ.x, SEATBACK_Y + 0.0, MUZ.z + 0.02))
hm = mat("HoleDark", (0.05, 0.035, 0.03), 0.9); lip = mat("HoleLip", (0.42, 0.36, 0.28), 0.9)
bpy.ops.mesh.primitive_circle_add(vertices=24, radius=0.028, fill_type='NGON', location=(0, 0, 0))
HOLE = bpy.context.active_object; HOLE.name = "SeatHole"; HOLE.data.materials.append(hm); move_to(HOLE, CT)
for i, v in enumerate(HOLE.data.vertices):
    if v.co.length > 0.001: v.co *= 1.0 + 0.25 * math.sin(i * 2.7)
foam_m = mat("SeatFoam", (0.95, 0.85, 0.55), 0.85)
bmL = bmesh.new()
rnd = random.Random(11)
for i in range(22):
    a_ = i / 22 * 2 * math.pi + rnd.uniform(-0.1, 0.1); r_ = 0.031 + rnd.uniform(-0.004, 0.006)
    m_ = Matrix.Translation((math.cos(a_) * r_, math.sin(a_) * r_, -0.002 - rnd.uniform(0, 0.004)))
    g_ = bmesh.ops.create_icosphere(bmL, subdivisions=1, radius=rnd.uniform(0.004, 0.008), matrix=m_)
for i in range(7):               # torn fabric flaps curling outward
    a_ = i / 7 * 2 * math.pi + 0.3
    c_, s_ = math.cos(a_), math.sin(a_)
    v1 = bmL.verts.new((c_ * 0.026 - s_ * 0.010, s_ * 0.026 + c_ * 0.010, 0.0))
    v2 = bmL.verts.new((c_ * 0.026 + s_ * 0.010, s_ * 0.026 - c_ * 0.010, 0.0))
    v3 = bmL.verts.new((c_ * 0.050, s_ * 0.050, -0.010))
    f_ = bmL.faces.new((v1, v2, v3)); f_.material_index = 1
me_ = bpy.data.meshes.new("SeatHoleLip"); bmL.to_mesh(me_); bmL.free()
LIP = bpy.data.objects.new("SeatHoleLip", me_); CT.objects.link(LIP)
LIP.data.materials.append(foam_m); LIP.data.materials.append(beige)
sol_ = LIP.modifiers.new("solid", 'SOLIDIFY'); sol_.thickness = 0.002
for o in (HOLE, LIP):
    o.rotation_euler = (R_(90), 0, 0); o.location = HOLE_P; o.scale = (0.001, 0.001, 0.001)
SMOKE_M = mat("Smoke", (0.85, 0.85, 0.85), 0.9, alpha=0.35)
smokes = []
for i in range(5):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=0.02, location=HOLE_P)
    s_ = bpy.context.active_object; s_.name = f"Smoke{i}"; s_.data.materials.append(SMOKE_M); move_to(s_, CT); s_.scale = (0.001,) * 3
    smokes.append(s_)

# ------------------------------------------------------------------ SET 2: anatomy (x=100)
CA = coll("SET_anat"); AX = Vector((100, 0, 0))
bone_m = mat("Bone", (0.93, 0.86, 0.70), 0.35); lung_m = mat("LungPink", (0.90, 0.38, 0.40), 0.3)
SK = dup(SKEL, "AnatSkeleton", AX + Vector((0, 0, -1.0)), (0, 0, R_(180)), 1.0, CA, linked=False)
SK.data.materials.clear(); SK.data.materials.append(bone_m)
# keep only the thorax: delete vertices outside the ribcage box
bm = bmesh.new(); bm.from_mesh(SK.data)
bmesh.ops.delete(bm, geom=[v for v in bm.verts if not (1.07 < v.co.z < 1.47 and abs(v.co.x) < 0.15)], context='VERTS')
bm.to_mesh(SK.data); bm.free()
LG = dup(LUNGS, "AnatLungs", AX + Vector((0, -0.01, 0.12)), (0, 0, 0), 1.05, CA, linked=False)
LG.scale = (0.95, 3.2, 1.05)
for m in LG.data.materials: pass
LG.data.materials.clear(); LG.data.materials.append(lung_m)
bul_m = mat("Bullet", (0.75, 0.45, 0.20), 0.25, metal=1.0)
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.006, location=AX); BUL = bpy.context.active_object; BUL.name = "Bullet"
BUL.scale = (1, 2.2, 1); BUL.data.materials.append(bul_m); move_to(BUL, CA)
trail_m = mat("Trail", (1, 0.85, 0.4), 0.5, emit=(1, 0.75, 0.3), ew=6.0)
bpy.ops.mesh.primitive_cone_add(vertices=16, radius1=0.005, radius2=0.0005, depth=0.12, location=AX)
TRAIL = bpy.context.active_object; TRAIL.name = "BulletTrail"; TRAIL.data.materials.append(trail_m); move_to(TRAIL, CA)
TRAIL.parent = BUL; TRAIL.location = (0, 0.065 / 2.2, 0); TRAIL.rotation_euler = (R_(-90), 0, 0); TRAIL.scale = (1, 1 / 2.2, 1)
glint_m = mat("Glint", (1, 0.9, 0.4), 0.5, emit=(1, 0.85, 0.3), ew=0.0)
hit_m = mat("LungHit", (0.75, 0.05, 0.08), 0.4, emit=(0.9, 0.1, 0.1), ew=0.0)
# backdrop: sky-blue gradient card behind the thorax (camera sees the world gradient too)
bd_m = bpy.data.materials.new("AnatBackdrop"); bd_m.use_nodes = True; nt2 = bd_m.node_tree; nt2.nodes.clear()
_o = nt2.nodes.new("ShaderNodeOutputMaterial"); _e = nt2.nodes.new("ShaderNodeEmission"); _tc = nt2.nodes.new("ShaderNodeTexCoord")
_sp = nt2.nodes.new("ShaderNodeSeparateXYZ"); _rp = nt2.nodes.new("ShaderNodeValToRGB")
_rp.color_ramp.elements[0].color = (0.80, 0.94, 1.0, 1); _rp.color_ramp.elements[1].color = (0.08, 0.55, 0.92, 1)
nt2.links.new(_tc.outputs["Generated"], _sp.inputs[0]); nt2.links.new(_sp.outputs["Y"], _rp.inputs["Fac"])
nt2.links.new(_rp.outputs["Color"], _e.inputs["Color"]); _e.inputs["Strength"].default_value = 1.4; nt2.links.new(_e.outputs[0], _o.inputs[0])
plane("AnatBackdrop", (6, 6), AX + Vector((0, -1.6, 0.2)), bd_m, CA, rot=(R_(90), 0, 0))
area("AnatKey", AX + Vector((0.8, 1.2, 1.4)), AX + Vector((0, 0, 0.25)), 120, 1.2, CA)
area("AnatFill", AX + Vector((-1.0, 1.0, 0.6)), AX + Vector((0, 0, 0.25)), 60, 1.5, CA, (0.9, 0.95, 1.0))
area("AnatRim", AX + Vector((0, -1.2, 1.0)), AX + Vector((0, 0, 0.25)), 50, 1.0, CA)

# ------------------------------------------------------------------ SET 3: ambulance interior (x=200), faces: rear door at +Y
CI = coll("SET_ambi"); IX = Vector((200, 0, 0))
white = mat("AmbWhite", (0.92, 0.94, 0.95), 0.45); cab_m = mat("AmbCab", (0.75, 0.80, 0.84), 0.4)
floor_m = mat("AmbFloor", (0.45, 0.50, 0.55), 0.6); mattress = mat("Mattress", (0.20, 0.45, 0.70), 0.5)
steel = mat("Steel", (0.75, 0.76, 0.78), 0.3, metal=0.8)
rbox("AmbFloor", (2.0, 3.6, 0.06), IX + Vector((0, 0, -0.03)), floor_m, CI, 0.01)
rbox("AmbRoof", (2.0, 3.6, 0.06), IX + Vector((0, 0, 1.92)), white, CI, 0.01)
for sx in (-1, 1):
    rbox(f"AmbWall{sx}", (0.06, 3.6, 1.95), IX + Vector((0.98 * sx, 0, 0.96)), white, CI, 0.01)
    for k in range(3):
        rbox(f"AmbCab{sx}_{k}", (0.30, 0.9, 0.35), IX + Vector((0.80 * sx, -1.1 + k * 0.95, 1.55)), cab_m, CI, 0.02)
rbox("AmbFront", (2.0, 0.06, 1.95), IX + Vector((0, -1.8, 0.96)), white, CI, 0.01)
rbox("AmbBench", (0.40, 1.6, 0.42), IX + Vector((-0.75, -0.2, 0.21)), cab_m, CI, 0.03)
# stretcher
STR_Z = 0.62
rbox("StretcherMat", (0.58, 1.9, 0.10), IX + Vector((0.30, 0.0, STR_Z - 0.05)), mattress, CI, 0.04)
rbox("StretcherFrame", (0.60, 1.95, 0.04), IX + Vector((0.30, 0.0, STR_Z - 0.12)), steel, CI, 0.01)
for yy in (-0.8, 0.8):
    for xx in (0.05, 0.55):
        cyl(f"StrLeg{xx}{yy}", 0.018, STR_Z - 0.14, IX + Vector((xx, yy, (STR_Z - 0.14) / 2)), steel, CI)
# rear door frame (opening at y=+1.8) + open doors swung out
for sx in (-1, 1):
    rbox(f"AmbDoorPost{sx}", (0.18, 0.08, 1.95), IX + Vector((0.92 * sx, 1.8, 0.96)), white, CI, 0.01)
    d_ = rbox(f"AmbDoorOpen{sx}", (0.04, 0.85, 1.75), IX + Vector((1.02 * sx, 2.25, 0.95)), white, CI, 0.01)
rbox("AmbRearTop", (2.0, 0.08, 0.20), IX + Vector((0, 1.8, 1.85)), white, CI, 0.01)
rbox("AmbStep", (1.6, 0.30, 0.05), IX + Vector((0, 1.98, -0.25)), steel, CI, 0.01)
plane("AmbOutGround", (30, 30), IX + Vector((0, 10, -0.5)), mat("Asphalt", (0.30, 0.31, 0.33), 0.8), CI)
area("AmbiCeil", IX + Vector((0, -0.3, 1.85)), IX + Vector((0, -0.3, 0)), 220, 1.8, CI)
area("AmbiFront", IX + Vector((0.5, 3.2, 1.6)), IX + Vector((0, 0, 1.0)), 280, 2.0, CI)
# medical details: oxygen bottle, monitor on wall
cyl("O2", 0.07, 0.55, IX + Vector((-0.85, -1.55, 0.7)), mat("O2Green", (0.2, 0.6, 0.35), 0.35), CI)
rbox("Monitor", (0.05, 0.38, 0.28), IX + Vector((-0.93, -0.6, 1.22)), dash, CI, 0.01)
rbox("MonitorScreen", (0.01, 0.32, 0.22), IX + Vector((-0.905, -0.6, 1.22)), mat("ScreenGreen", (0.05, 0.25, 0.2), 0.3, emit=(0.1, 0.8, 0.5), ew=1.5), CI, 0.0)

# ------------------------------------------------------------------ SET 4: forest road + clearing (x=300)
CR = coll("SET_road"); RX = Vector((300, 0, 0))
plane("RoadGround", (120, 160), RX + Vector((0, 0, -0.01)), grass, CR)
asph = mat("Road", (0.30, 0.31, 0.33), 0.75); line_m = mat("RoadLine", (0.95, 0.95, 0.9), 0.5)
plane("Road", (6.0, 160), RX + Vector((0, 0, 0.005)), asph, CR)
for k in range(-30, 30):
    plane(f"RoadDash{k}", (0.12, 1.5), RX + Vector((0, k * 3.0, 0.008)), line_m, CR)
for i in range(70):
    side = 1 if i % 2 else -1
    x = side * (5 + random.random() * 22); y = -70 + i * 2.1 + random.random()
    if side < 0 and -8 < y < 14 and x > -18: x -= 12    # keep the clearing (x~-9, y~0..6) open
    src = PLANTS[random.choice(["PH_fir_tree_01_a_LOD2", "PH_fir_tree_01_b_LOD2", "PH_fir_tree_01_c_LOD2"])]
    dup(src, f"RoadFir{i}", RX + Vector((x, y, 0)), (0, 0, random.random() * 6), 0.7 + random.random() * 0.35, CR)
for i in range(40):
    side = 1 if i % 2 else -1
    src = PLANTS[random.choice(["PH_shrub_02_a_LOD1", "PH_shrub_02_c_LOD1", "PH_fern_02_b", "PH_fern_02_c"])]
    dup(src, f"RoadShrub{i}", RX + Vector((side * (3.6 + random.random() * 3), -60 + i * 3 + random.random() * 2, 0)), (0, 0, random.random() * 6), 0.8 + random.random() * 0.5, CR)
AM = dup(AMB, "Amb", RX + Vector((1.5, 0, 0)), (0, 0, 0), 1.0, CR, linked=False)
logo_decal("Logo_Amb", AM.matrix_world @ Vector((0, -2.83, float(os.environ.get("DSO_LZ", "0.73")))), (R_(90), 0, 0), float(os.environ.get("DSO_LW", "0.56")), True, CR, parent=AM)
# ambulance light bar flashers (keyed blink)
red_m = mat("FlashRed", (1, 0.1, 0.1), 0.3, emit=(1, 0.05, 0.05), ew=0.0); blue_m = mat("FlashBlue", (0.2, 0.3, 1), 0.3, emit=(0.15, 0.3, 1.0), ew=0.0)
area("RoadSun", RX + Vector((8, -6, 14)), RX + Vector((0, 0, 0)), 3000, 8.0, CR, (1.0, 0.97, 0.9))
# clearing (for beat 15): grass clumps + ferns around the spot where the dog lies
CLR = RX + Vector((-11.0, 2.0, 0))
for i in range(260):
    a = random.random() * 2 * math.pi; r = 0.4 + random.random() * 4.5
    src = PLANTS[random.choice(["PH_grass_medium_01_large_a_LOD1", "PH_grass_medium_01_large_b_LOD1", "PH_grass_medium_01_mid_a_LOD1"])]
    p_ = CLR + Vector((math.cos(a) * r, math.sin(a) * r, 0))
    if (p_ - (CLR + Vector((0.2, -0.4, 0)))).length < 0.95: continue
    if (p_ - (CLR + Vector((-0.6, -1.45, 0)))).length < 0.8: continue      # 15b camera spot: no blades in the lens      # keep the dog's spot clear of clumps
    dup(src, f"ClrGrass{i}", p_, (0, 0, random.random() * 6), 1.3 + random.random() * 0.8, CR)
for i in range(16):
    a = random.random() * 2 * math.pi; r = 3 + random.random() * 3
    src = PLANTS[random.choice(["PH_fern_02_b", "PH_fern_02_c", "PH_shrub_02_a_LOD1"])]
    dup(src, f"ClrFern{i}", CLR + Vector((math.cos(a) * r, math.sin(a) * r, 0)), (0, 0, random.random() * 6), 1.0 + random.random() * 0.4, CR)
for i in range(18):
    a = i / 18 * 2 * math.pi + random.random() * 0.2; r = 7 + random.random() * 4
    p_ = CLR + Vector((math.cos(a) * r, math.sin(a) * r, 0))
    if p_.x > RX.x - 4: continue
    src = PLANTS[random.choice(["PH_fir_tree_01_a_LOD2", "PH_fir_tree_01_b_LOD2", "PH_fir_sapling_medium_a_LOD1"])]
    dup(src, f"ClrFir{i}", p_, (0, 0, random.random() * 6), 0.7 + random.random() * 0.3, CR)

# ------------------------------------------------------------------ SET 5: kennel (x=400)
CK = coll("SET_kennel"); KX = Vector((400, 0, 0))
wall_k = mat("KennelWall", (0.86, 0.88, 0.86), 0.6); fl_k = mat("KennelFloor", (0.55, 0.58, 0.60), 0.6)
plane("KFloor", (8, 8), KX, fl_k, CK)
rbox("KWall", (8, 0.1, 3.5), KX + Vector((0, 1.6, 1.75)), wall_k, CK, 0.0)
rbox("KTable", (2.0, 0.9, 0.05), KX + Vector((0.2, 0.2, 0.76)), steel, CK, 0.01)
for xx in (-0.7, 0.7):
    for yy in (-0.2, 0.6):
        cyl(f"KTLeg{xx}{yy}", 0.025, 0.74, KX + Vector((xx, yy, 0.37)), steel, CK)
CR8 = dup(CRATE, "DogCrate", KX + Vector((0, 0.25, 0.785)), (0, 0, R_(180)), 1.27, CK, linked=False)
crate_m = mat("CrateWhite", (0.92, 0.93, 0.93), 0.4)
CR8.data.materials.clear(); CR8.data.materials.append(crate_m)
# crate door: a separate barred door that swings (rbox frame + bars), hinged at the crate's -X front edge
DOOR = bpy.data.objects.new("CrateDoor", None); CK.objects.link(DOOR)
cpts = [CR8.matrix_world @ v.co for v in CR8.data.vertices]
_inv = CR8.matrix_world.inverted()
_ok, _loc, _n, _i = CR8.ray_cast(_inv @ Vector((KX.x, 0.25, 1.4)), _inv.to_3x3() @ Vector((0, 0, -1)))
CRATE_FLOOR = (CR8.matrix_world @ _loc).z if _ok else 0.80
print("BUILD crate floor", round(CRATE_FLOOR, 3))
cminy = min(p.y for p in cpts); cmaxy = max(p.y for p in cpts); cminx = min(p.x for p in cpts); cmaxx = max(p.x for p in cpts); ctop = max(p.z for p in cpts)
print("BUILD crate front y", round(cminy, 3), "x", round(cminx, 3), round(cmaxx, 3), "top", round(ctop, 3))
# logo plate on the crate top front edge
box_m = mat("Cardboard", (0.72, 0.52, 0.30), 0.8)

area("KennelKey", KX + Vector((1.5, -2.0, 2.4)), KX + Vector((0, 0.2, 1.0)), 450, 2.0, CK)
area("KennelFill", KX + Vector((-1.8, -1.2, 1.6)), KX + Vector((0, 0.2, 1.0)), 180, 2.0, CK, (0.92, 0.96, 1.0))

# ------------------------------------------------------------------ SET 6: hospital room (x=500)
CH = coll("SET_hosp"); HX = Vector((500, 0, 0))
wall_h = mat("HospWall", (0.80, 0.90, 0.92), 0.6); fl_h = mat("HospFloor", (0.72, 0.74, 0.76), 0.5)
blanket = mat("Blanket", (0.55, 0.75, 0.88), 0.8); pillow = mat("Pillow", (0.95, 0.96, 0.97), 0.8)
plane("HFloor", (8, 8), HX, fl_h, CH)
rbox("HWallBack", (8, 0.1, 3.0), HX + Vector((0, 1.6, 1.5)), wall_h, CH, 0.0)
rbox("HWallSide", (0.1, 8, 3.0), HX + Vector((-1.6, 0, 1.5)), wall_h, CH, 0.0)
rbox("HWindow", (0.02, 1.2, 1.0), HX + Vector((-1.54, 0.2, 1.6)), mat("WinSky", (0.6, 0.85, 1.0), 0.2, emit=(0.6, 0.85, 1.0), ew=1.2), CH, 0.0)
BD = dup(BED, "HospBed", HX + Vector((0, 0.3, 0)), (0, 0, R_(180)), 1.0, CH, linked=False)
bpts = [BD.matrix_world @ v.co for v in BD.data.vertices]
print("BUILD bed bbox", [round(min(p[i] for p in bpts), 2) for i in range(3)], [round(max(p[i] for p in bpts), 2) for i in range(3)])
MAT_Z = 0.62    # mattress top (checked in stills)
rbox("BedPillow", (0.62, 0.35, 0.12), HX + Vector((-0.1, 1.24, MAT_Z + 0.44)), pillow, CH, 0.05, rot=(R_(-58), 0, 0))
cyl("IVPole", 0.015, 1.9, HX + Vector((0.75, 1.0, 0.95)), steel, CH)
cyl("IVBase", 0.22, 0.04, HX + Vector((0.75, 1.0, 0.02)), steel, CH)
rbox("IVBag", (0.12, 0.04, 0.2), HX + Vector((0.75, 1.0, 1.75)), mat("IVBag", (0.9, 0.95, 1.0), 0.2, alpha=0.6), CH, 0.02)
area("HospKey", HX + Vector((1.6, -1.8, 2.5)), HX + Vector((0, 0.3, 0.9)), 420, 2.0, CH)
area("HospFill", HX + Vector((-1.4, -1.0, 1.8)), HX + Vector((0, 0.3, 0.9)), 160, 2.0, CH, (0.9, 0.95, 1.0))

exec(open(HERE + "/02b_dress.py").read())

# ================================================================== animation helpers
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
for rg in (OWNER, MEDA, MEDB): ensure_leg_ik(rg)
ROWN, RMA, RMB = Rig(OWNER), Rig(MEDA), Rig(MEDB)
HOWN, HMA, HMB = Human(ROWN), Human(RMA), Human(RMB)
for rg in (OWNER, MEDA, MEDB): add_hand_limits(rg)
CHARS = {"own": (OWNER, HOWN), "ma": (MEDA, HMA), "mb": (MEDB, HMB)}
PARK = {"own": Vector((-50, 0, 0)), "ma": Vector((-52, 0, 0)), "mb": (Vector((-54, 0, 0))), "dog": Vector((-56, 0, 0))}

def stand(H, rig, f, pos, yaw=0.0, head=(0, 0), flex=0.0, twist=0.0, hands=True, breath=0.0):
    c = Matrix.Rotation(R_(yaw), 3, 'Z')
    H.key_root(f, Vector((pos.x, pos.y, pos.z + 0.95 - breath * 0.004)), yaw=yaw, flex=flex * 0.3)
    for s, sx in (("L", 1), ("R", -1)):
        H.key_foot(s, f, (pos + c @ Vector((0.1 * sx, 0, 0))).to_2d(), yaw)
        if hands:
            place_hand(rig, s, f, pos + c @ Vector((0.205 * sx, 0.0, 0.86 + flex * 0.002)), c @ Vector((-sx, 0, 0)), (0, 0, -1))
            apply_pose(rig, s, "relaxed", f)
    H.key_spine(f, flex=flex + breath, twist=twist, head=head)

def feet_at(H, f, pos, yaw, z):
    pass

def seated(H, rig, f, pos, yaw=0.0, lean=-8.0, flex=6.0, head=(0, 0), twist=0.0, knee_fwd=0.58, foot_z=0.0, legs_out=False):
    """pos = seat-cushion top centre under the hips (world)."""
    c = Matrix.Rotation(R_(yaw), 3, 'Z')
    H.key_root(f, Vector((pos.x, pos.y, pos.z + 0.10)), yaw=yaw, flex=lean)
    for s, sx in (("L", 1), ("R", -1)):
        if legs_out:
            fp = pos + c @ Vector((0.11 * sx, -0.92, 0.0))
            a = H.ankle[s]
            M = Matrix.Translation(Vector((fp.x, fp.y, pos.z + 0.07))) @ Matrix.Rotation(R_(yaw), 4, 'Z') @ Matrix.Rotation(R_(-70), 4, 'X') @ \
                Matrix.Translation(-a) @ H.r.rest("IK_foot." + s)
            H.r.key_world("IK_foot." + s, f, M)
            pole = fp + Vector((0, 0, 0.8)); pb = H.r.PB["Pole_knee." + s]; n = "Pole_knee." + s
            pb.location = H.r.rest(n).to_3x3().inverted() @ (pole - H.r.BN[n].head_local); pb.keyframe_insert("location", frame=f, group=n)
        else:
            fp = pos + c @ Vector((0.13 * sx, -knee_fwd, 0))
            a = H.ankle[s]
            M = Matrix.Translation(Vector((fp.x, fp.y, foot_z + a.z))) @ Matrix.Rotation(R_(yaw), 4, 'Z') @ Matrix.Translation(-a) @ H.r.rest("IK_foot." + s)
            H.r.key_world("IK_foot." + s, f, M)
            pole = fp + c @ Vector((0, -0.7, 0.45)); pb = H.r.PB["Pole_knee." + s]; n = "Pole_knee." + s
            pb.location = H.r.rest(n).to_3x3().inverted() @ (pole - H.r.BN[n].head_local); pb.keyframe_insert("location", frame=f, group=n)
    H.key_spine(f, flex=flex, twist=twist, head=head)

def hands_lap(rig, f, pos, yaw=0.0, legs_out=False):
    c = Matrix.Rotation(R_(yaw), 3, 'Z')
    for s, sx in (("L", 1), ("R", -1)):
        place_hand(rig, s, f, pos + c @ Vector((0.12 * sx, -0.26, 0.17 if not legs_out else 0.15)), (0, 0, -1), c @ Vector((0, -1, 0)))
        apply_pose(rig, s, "relaxed", f)

def dog_key(f, loc, yaw, pose):
    DOG.location = loc; DOG.rotation_euler = (0, 0, R_(yaw))
    DOG.keyframe_insert("location", frame=f); DOG.keyframe_insert("rotation_euler", frame=f)
    for pb in DOG.pose.bones:
        l_, r_ = pose.get(pb.name, (None, None))
        pb.location = Vector(l_) if l_ else Vector(); pb.rotation_mode = 'QUATERNION'
        pb.rotation_quaternion = Euler(tuple(R_(v) for v in r_)).to_quaternion() if r_ else Quaternion()
        pb.keyframe_insert("location", frame=f); pb.keyframe_insert("rotation_quaternion", frame=f)

def dog_side(f, loc, yaw, head=(0, 0, 0), tail=0.0, breath=0.0, roll_sign=1):
    """dog lying on its side, asleep (legs relaxed, slightly bent); rotation about its own long axis"""
    DOG.location = loc + Vector((0, 0, 0.155)); DOG.rotation_mode = 'XYZ'
    DOG.rotation_euler = (Matrix.Rotation(R_(yaw), 3, 'Z') @ Matrix.Rotation(R_(90 * roll_sign), 3, 'Y')).to_euler()
    DOG.keyframe_insert("location", frame=f); DOG.keyframe_insert("rotation_euler", frame=f)
    pose = {"IK_hoof.FL": ((0, -0.05, 0.07), None), "IK_hoof.FR": ((0, -0.02, 0.05), None),
            "IK_hoof.HL": ((0, 0.05, 0.07), None), "IK_hoof.HR": ((0, 0.02, 0.05), None),
            "neck1": (None, (8 + head[0], head[1], head[2])), "head": (None, (-6, 0, 0)), "tail1": (None, (-35 + tail, 0, 0)),
            "spine1": (None, (breath, 0, 0))}
    pose.update({"spine1": (None, (breath, 0, 5)), "spine2": (None, (0, 0, 4)), "neck1": (None, (8 + head[0], head[1], 10 + head[2])),
                 "head": (None, (-2, 0, 5)), "tail1": (None, (-30, 0, -20)), "tail2": (None, (0, 0, -25))})
    CURL = {"IK_hoof.FL": (0.03, 0.13, 0.16), "IK_hoof.FR": (0.0, 0.10, 0.13), "IK_hoof.HL": (0.03, -0.16, 0.14), "IK_hoof.HR": (0.0, -0.13, 0.11)}
    for pb in DOG.pose.bones:
        l_, r_ = pose.get(pb.name, (None, None))
        if pb.name in CURL:
            pb.location = DOG.data.bones[pb.name].matrix_local.to_3x3().inverted() @ Vector(CURL[pb.name])
        else:
            pb.location = Vector(l_) if l_ else Vector()
        pb.rotation_mode = 'QUATERNION'
        pb.rotation_quaternion = Euler(tuple(R_(v) for v in r_)).to_quaternion() if r_ else Quaternion()
        pb.keyframe_insert("location", frame=f); pb.keyframe_insert("rotation_quaternion", frame=f)

def dog_pose_stand(head=(0, 0, 0), tail=0.0, pant=0.0, ext=None):
    p = {"neck1": (None, (head[0], head[1], head[2] * 0.5)), "head": (None, (pant, 0, head[2] * 0.5)), "tail1": (None, (tail, 0, 0)),
         "tail2": (None, (tail * 0.5, 0, 0))}
    if ext: p.update(ext)
    return p

def keyobj(o, f, loc=None, rot=None, scale=None):
    if loc is not None: o.location = loc; o.keyframe_insert("location", frame=f)
    if rot is not None: o.rotation_euler = rot; o.keyframe_insert("rotation_euler", frame=f)
    if scale is not None: o.scale = scale if not isinstance(scale, (int, float)) else (scale,) * 3; o.keyframe_insert("scale", frame=f)

def emit_key(m, f, v):
    p = m.node_tree.nodes["Principled BSDF"]; p.inputs["Emission Strength"].default_value = v
    p.inputs["Emission Strength"].keyframe_insert("default_value", frame=f)

def light_key(o, f, e):
    o.data.energy = e; o.data.keyframe_insert("energy", frame=f)

# cameras
CAMC = coll("CAMERAS")
CAMS = {}
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

def lerp(a, b, t): return a + (b - a) * t
def ease(t): return t * t * (3 - 2 * t)

PRESENT = {}   # sid -> set of chars present (others are parked)

# ================================================================== shots
def shot_truck_common(f0, f1, man_head=(0, 0), man_twist=0.0, flex=6.0, wheel=True):
    seat_top = SEAT_TOP.copy()
    seated(HOWN, OWNER, f0, seat_top, yaw=0, lean=-8, flex=flex, head=man_head, twist=man_twist)
    if wheel:
        for s, sx in (("L", 1), ("R", -1)):
            place_hand(OWNER, s, f0, (DRV.x + 0.15 * sx, -0.950, 1.0 + 0.04), (0, -0.7, 0.4), (-sx * 0.35, 0, 1)); apply_pose(OWNER, s, "relaxed", f0)
    return seat_top

def S01(f0, f1):
    PRESENT["01"] = {"own", "dog"}
    shot_truck_common(f0, f1)
    D0 = Vector((0.13 - 0.17 - 0.03, 0.70, BZ + 0.008)); n = f1 - f0
    for k in range(0, n + 1, 10):
        t = k / n
        dog_key(f0 + k, D0, 90, dog_pose_stand(head=(8 * math.sin(t * 6), 0, -35 * ease(min(1, t * 1.6))), tail=25 * math.sin(k * 0.45), pant=4 * math.sin(k * 0.9)))
    c = camera("01", 24)
    sc.frame_set(f1); hd = DOG.matrix_world @ DOG.pose.bones["neck2"].tail
    tg = hd.lerp(D0 + Vector((0.0, 0, 0.3)), 0.45)
    cam_key(c, f0, (0.0, -0.40, 1.30), tg, lens=22)
    cam_key(c, f1, (0.0, -0.22, 1.26), tg, lens=22)

def S02(f0, f1):
    PRESENT["02"] = {"own", "dog"}
    shot_truck_common(f0, f1)
    D0 = Vector((0.13 - 0.17 - 0.03, 0.70, BZ + 0.008)); n = f1 - f0
    # front-right paw (nearest the bench edge) lifts at 35% and lands on the grip/trigger area at 65%
    for k in list(range(0, n + 1, 6)) + [n]:
        t = k / n; u = ease(max(0.0, min(1.0, (t - 0.30) / 0.35)))
        uh = ease(min(1.0, u / 0.7))                      # sideways travel done by 70%, then straight down
        uh = ease(max(0.0, min(1.0, (u - 0.15) / 0.55)))   # lift first, then travel
        lift = 0.10 * (math.sin(math.pi * 0.5 * min(1.0, u / 0.15)) if u < 0.7 else (1.0 - (u - 0.7) / 0.3))
        ext = {"__FR": ("trig", uh, lift), "torso": ((0, 0, -0.01 * u), (0, 3 * u, 0))}
        dog_key(f0 + k, D0, 90, dog_pose_stand(head=(-14 * u, 0, -10), tail=20 * math.sin(k * 0.4), pant=3 * math.sin(k * 0.9), ext=ext))
    c = camera("02", 40)
    tgt = Vector((TRIG.x - 0.04, TRIG.y + 0.02, TRIG.z + 0.08))
    cam_key(c, f0, Vector((TRIG.x + 0.12, 0.36, TRIG.z + 0.34)), tgt, lens=30)
    cam_key(c, f1, Vector((TRIG.x + 0.10, 0.40, TRIG.z + 0.28)), tgt, lens=30)

def S03(f0, f1):
    PRESENT["03"] = {"own", "dog"}
    shot_truck_common(f0, f1)
    D0 = Vector((0.13 - 0.17 - 0.03, 0.70, BZ + 0.008))
    for k in (0, f1 - f0):
        dog_key(f0 + k, D0, 90, dog_pose_stand(head=(-14, 0, -10), tail=10, ext={"__FR": "trig"}))
    c = camera("03", 30)
    a = MUZ + Vector((-0.16, 0.50, 0.17)); b = MUZ + Vector((-0.12, 0.40, 0.14))
    cam_key(c, f0, (-0.58, 0.08, 1.30), (0.18, 0.62, 0.80), lens=18); cam_key(c, f1, (-0.52, 0.10, 1.26), (0.19, 0.62, 0.80), lens=18)

def S04(f0, f1):
    PRESENT["04"] = {"own", "dog"}
    shot_truck_common(f0, f1)
    D0 = Vector((0.13 - 0.17 - 0.03, 0.70, BZ + 0.008))
    for k in (0, f1 - f0):
        dog_key(f0 + k, D0, 90, dog_pose_stand(head=(-14, 0, -10), tail=10, ext={"__FR": "trig"}))
    fb = f0 + 40
    keyobj(FLASH, f0, scale=0.01); keyobj(FLASH, fb - 1, scale=0.01); keyobj(FLASH, fb, scale=1.8); keyobj(FLASH, fb + 5, scale=1.2); keyobj(FLASH, fb + 12, scale=0.01)
    emit_key(fl_m, f0, 0); emit_key(fl_m, fb - 1, 0); emit_key(fl_m, fb, 40); emit_key(fl_m, fb + 12, 0)
    light_key(FL_L, f0, 0); light_key(FL_L, fb - 1, 0); light_key(FL_L, fb, 80); light_key(FL_L, fb + 14, 0)
    g0 = G.location.copy(); keyobj(G, f0, loc=g0); keyobj(G, fb, loc=g0); keyobj(G, fb + 3, loc=g0 - dvec.normalized() * 0.02); keyobj(G, fb + 14, loc=g0)
    c = camera("04", 32)
    side = Vector((0.45, 0, 0))
    cam_key(c, f0, (0.76, 0.52, 0.86), MUZ + Vector((-0.02, 0.02, 0.0)), lens=22)
    cam_key(c, f1, (0.74, 0.46, 0.82), MUZ + Vector((-0.02, 0.0, 0.0)), lens=22)

def S05(f0, f1):
    PRESENT["05"] = {"own", "dog"}
    fh = f0 + 30
    shot_truck_common(f0, f1)
    seat_top = SEAT_TOP.copy()
    seated(HOWN, OWNER, fh, seat_top, lean=-8, flex=6)
    seated(HOWN, OWNER, fh + 6, seat_top, lean=-2, flex=-4, head=(-10, 0))            # jolt
    seated(HOWN, OWNER, fh + 30, seat_top, lean=-5, flex=10, head=(-6, -35), twist=-25)   # turns to look back over his left shoulder
    seated(HOWN, OWNER, f1, seat_top, lean=-5, flex=8, head=(-8, -45), twist=-32)
    for fr in (fh, fh + 6, fh + 30, f1):
        place_hand(OWNER, "R", fr, (DRV.x - 0.15, -0.950, 1.04), (0, -0.7, 0.4), (0.35, 0, 1)); apply_pose(OWNER, "R", "relaxed", fr)
    place_hand(OWNER, "L", fh, (DRV.x + 0.15, -0.950, 1.04), (0, -0.7, 0.4), (-0.35, 0, 1)); apply_pose(OWNER, "L", "relaxed", fh)
    for fr in (fh + 18, fh + 30, f1):      # left hand goes to the hurt side (flank), palm on the jumper
        sc.frame_set(fr)
        place_hand(OWNER, "L", fr, SEAT_TOP + Vector((0.20, 0.02, 0.32)), (-1, 0.2, 0), (0, 0.1, -1)); apply_pose(OWNER, "L", "relaxed", fr)
    D0 = Vector((0.13 - 0.17 - 0.03, 0.70, BZ + 0.008))
    for k in (0, fh - f0, fh - f0 + 8, f1 - f0):
        dog_key(f0 + k, D0, 90, dog_pose_stand(head=(-10 if k < 30 else 10, 0, -10 if k < 30 else 20), tail=10))
    keyobj(HOLE, f0, scale=0.001); keyobj(HOLE, fh - 1, scale=0.001); keyobj(HOLE, fh, scale=1.0)
    keyobj(LIP, f0, scale=0.001); keyobj(LIP, fh - 1, scale=0.001); keyobj(LIP, fh, scale=1.0)
    for i, s_ in enumerate(smokes):
        keyobj(s_, f0, loc=HOLE_P, scale=0.001); keyobj(s_, fh, loc=HOLE_P, scale=0.001)
        keyobj(s_, fh + 4, loc=HOLE_P + Vector((0.01 * i - 0.02, -0.02, 0.01)), scale=1.0)
        keyobj(s_, f1, loc=HOLE_P + Vector((0.03 * i - 0.06, -0.10 - 0.02 * i, 0.12 + 0.03 * i)), scale=2.5 + i * 0.4)
    emit_key(fl_m, fh - 1, 0)
    c = camera("05", 26)
    cam_key(c, f0, (0.02, 0.36, 1.10), (DRV.x + 0.02, SEATBACK_Y - 0.20, 0.98), lens=18)
    cam_key(c, f1, (0.03, 0.33, 1.10), (DRV.x + 0.02, SEATBACK_Y - 0.20, 1.00), lens=18)

def S06(f0, f1):
    PRESENT["06"] = {"own", "dog"}
    seat_top = SEAT_TOP.copy()
    seated(HOWN, OWNER, f0, seat_top, lean=-5, flex=8, head=(-8, -45), twist=-32)
    place_hand(OWNER, "L", f0, SEAT_TOP + Vector((0.20, 0.02, 0.32)), (-1, 0.2, 0), (0, 0.1, -1)); apply_pose(OWNER, "L", "relaxed", f0)
    place_hand(OWNER, "R", f0, (DRV.x - 0.15, -0.950, 1.04), (0, -0.7, 0.4), (0.35, 0, 1)); apply_pose(OWNER, "R", "relaxed", f0)
    D0 = Vector((0.13 - 0.17 - 0.03, 0.70, BZ + 0.008))
    dog_key(f0, D0, 90, dog_pose_stand(head=(10, 0, 20), tail=10)); dog_key(f1, D0, 90, dog_pose_stand(head=(14, 0, 25), tail=15))
    for i, s_ in enumerate(smokes):
        keyobj(s_, f0, loc=HOLE_P + Vector((0.01 * i - 0.02, -0.03, 0.02)), scale=1.2)
        keyobj(s_, f1, loc=HOLE_P + Vector((0.03 * i - 0.06, -0.12 - 0.02 * i, 0.14 + 0.03 * i)), scale=2.8 + i * 0.4)
    c = camera("06", 20)
    cam_key(c, f0, Vector((0.62, 0.40, 0.72)), Vector((HOLE_P.x - 0.02, SEATBACK_Y, 0.82)), lens=18)
    cam_key(c, f1, Vector((0.60, 0.36, 0.70)), Vector((HOLE_P.x - 0.02, SEATBACK_Y, 0.80)), lens=18)

# anatomy: bullet path from behind (+Y side is the man's back after the skeleton is turned)
def anat_points():
    pts = [v.co for v in SK.data.vertices]
    ymax = max(p.y for p in pts)
    return ymax
def S07a(f0, f1):
    PRESENT["07a"] = set()
    ymax = anat_points()
    entry = AX + Vector((0.07, 0.5, 0.18)); rib = AX + Vector((0.07, SK.location.y + ymax - 0.01, 0.18))
    n = f1 - f0; fh = f0 + int(n * 0.55)
    keyobj(BUL, f0, loc=entry + Vector((0, 0.6, 0.03)), rot=(0, 0, 0)); keyobj(BUL, fh, loc=rib)
    keyobj(BUL, f1, loc=rib + Vector((0, -0.02, 0)))
    c = camera("07a", 40)
    cam_key(c, f0, AX + Vector((0.55, 1.15, 0.45)), AX + Vector((0.03, 0, 0.2)))
    cam_key(c, f1, AX + Vector((0.35, 0.95, 0.35)), AX + Vector((0.05, 0, 0.19)))
GLINTS = []
def S07b(f0, f1):
    PRESENT["07b"] = set()
    ymax = anat_points(); yb = SK.location.y + ymax
    rib = AX + Vector((0.07, yb - 0.01, 0.18)); inside = AX + Vector((0.075, yb - 0.08, 0.17))
    keyobj(BUL, f0, loc=rib); keyobj(BUL, f0 + 30, loc=rib + Vector((0, -0.03, 0))); keyobj(BUL, f1, loc=inside)
    inv = SK.matrix_world.inverted()
    for i, (dx, dz) in enumerate([(0.07, 0.18), (0.085, 0.14), (0.06, 0.22), (0.095, 0.10)]):
        ok_, cp, nn, ii = SK.closest_point_on_mesh(inv @ (AX + Vector((dx, yb + 0.03, dz))))
        gp = SK.matrix_world @ cp
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=0.0035, location=gp)
        g = bpy.context.active_object; g.name = f"Glint{i}"; g.data.materials.append(glint_m); move_to(g, CA); GLINTS.append(g)
        keyobj(g, 1, scale=0.001); keyobj(g, f0 + 20 + i * 18, scale=0.001); keyobj(g, f0 + 24 + i * 18, scale=1.6); keyobj(g, f0 + 34 + i * 18, scale=1.0)
    emit_key(glint_m, 1, 0); emit_key(glint_m, f0 + 19, 0); emit_key(glint_m, f0 + 24, 12)
    c = camera("07b", 50)
    cam_key(c, f0, AX + Vector((0.32, 0.62, 0.30)), AX + Vector((0.07, 0.0, 0.17)))
    cam_key(c, f1, AX + Vector((0.26, 0.52, 0.26)), AX + Vector((0.07, 0.0, 0.16)))
def S07c(f0, f1):
    PRESENT["07c"] = set()
    ymax = anat_points(); yb = SK.location.y + ymax
    inside = AX + Vector((0.075, yb - 0.08, 0.17))
    lpts = [LG.matrix_world @ v.co for v in LG.data.vertices]
    near = min(lpts, key=lambda p: (Vector((p.x, 0, p.z)) - Vector((inside.x, 0, inside.z))).length + (0 if p.y > LG.location.y else 1))
    hitp = Vector((inside.x, max(p.y for p in lpts if abs(p.x - inside.x) < 0.02 and abs(p.z - inside.z) < 0.02) if any(abs(p.x - inside.x) < 0.02 and abs(p.z - inside.z) < 0.02 for p in lpts) else LG.location.y + 0.03, inside.z))
    keyobj(BUL, f0, loc=inside); keyobj(BUL, f0 + 25, loc=hitp + Vector((0, -0.01, 0))); keyobj(BUL, f0 + 26, loc=hitp + Vector((0, -0.01, 0)), scale=1.0)
    keyobj(BUL, f0 + 27, scale=0.001)
    bpy.ops.mesh.primitive_circle_add(vertices=24, radius=0.018, fill_type='NGON', location=hitp + Vector((0, 0.003, 0)), rotation=(R_(-90), 0, 0))
    hr = bpy.context.active_object; hr.name = "LungHitRing"; hr.data.materials.append(hit_m); move_to(hr, CA)
    keyobj(hr, 1, scale=0.001); keyobj(hr, f0 + 25, scale=0.001); keyobj(hr, f0 + 30, scale=1.0); keyobj(hr, f1, scale=1.25)
    emit_key(hit_m, 1, 0); emit_key(hit_m, f0 + 25, 0); emit_key(hit_m, f0 + 30, 6.0); emit_key(hit_m, f1, 3.0)
    s0 = LG.scale.copy(); keyobj(LG, f0, scale=s0); keyobj(LG, f0 + 30, scale=s0); keyobj(LG, f1, scale=(s0.x * 0.97, s0.y * 0.97, s0.z * 0.96))
    c = camera("07c", 50)
    cam_key(c, f0, hitp + Vector((0.20, 0.42, 0.10)), hitp); cam_key(c, f1, hitp + Vector((0.12, 0.28, 0.06)), hitp)

PHONE_CURL = float(os.environ.get('DSO_CURL', '0.6'))
def phone_pose(f, raise_=0.0, look=(22, 0), mouth=0):
    seat_top = SEAT_TOP.copy()
    seated(HOWN, OWNER, f, seat_top, lean=-4, flex=10, head=look)
    hp = Vector((DRV.x - 0.06, DRV.y - 0.33, seat_top.z + 0.55 + raise_))
    place_hand(OWNER, "R", f, hp, (0.25, 0.85, -0.35), (0.25, -0.25, 0.95)); apply_pose(OWNER, "R", "cup_hold", f, amount=PHONE_CURL)
    place_hand(OWNER, "L", f, seat_top + Vector((0.12, -0.27, 0.17)), (0, 0, -1), (0, -1, 0)); apply_pose(OWNER, "L", "relaxed", f)
    return hp
PH = dup(PHONE, "PhoneHeld", (0, 0, 0), (0, 0, 0), 1.0, CT, linked=False)
PH.data.transform(Matrix.Diagonal((1.0, 0.82, 1.0, 1.0)))
scr = mat("PhoneScreen", (0.05, 0.15, 0.12), 0.2, emit=(0.25, 0.75, 0.55), ew=1.2)
def attach_phone(f):
    sc.frame_set(f)
    pbw = OWNER.pose.bones["wrist.R"]; Mw = OWNER.matrix_world
    wh = Mw @ pbw.head; fm = Mw @ OWNER.pose.bones["finger3-1.R"].head
    i2 = Mw @ OWNER.pose.bones["finger2-1.R"].head; i5 = Mw @ OWNER.pose.bones["finger5-1.R"].head
    d = (fm - wh).normalized(); acr = (i2 - i5).normalized()
    n = d.cross(acr).normalized()
    face = (Mw @ OWNER.pose.bones["head"].head) - wh
    if n.dot(face) < 0: n = -n                      # phone on the palm side that faces his face
    ctr = wh + d * 0.090 + n * float(os.environ.get('DSO_OFF', '0.034')) + n.cross(d).normalized() * float(os.environ.get('DSO_LAT', '0.0'))
    y_ = n.cross(d).normalized()
    R3 = Matrix((n, y_, d)).transposed()
    PH.matrix_world = Matrix.Translation(ctr) @ R3.to_4x4()
    bpy.context.view_layer.update()
    c = PH.constraints.new('CHILD_OF'); c.target = OWNER; c.subtarget = "wrist.R"
    c.inverse_matrix = (Mw @ pbw.matrix).inverted() @ Matrix.Identity(4)
    c.set_inverse_pending = False
    # the constraint maps the current world matrix; store the offset in matrix_basis
    PH.matrix_basis = (Mw @ pbw.matrix).inverted() @ Matrix.Translation(ctr) @ R3.to_4x4()
    c.inverse_matrix = Matrix.Identity(4)
    print("BUILD phone at", tuple(round(v, 3) for v in ctr))
def attach_to_hand(prop, rig, side, f, along=0.085, off=0.022, toward=None, axes="x"):
    """place prop in the hand at frame f and bind it (Child Of wrist). axes 'x': prop local X = palm normal, Z = fingers
    (phone); 'z': prop local Z = palm normal, Y = fingers (flat board)."""
    sc.frame_set(f)
    pbw = rig.pose.bones["wrist." + side]; Mw = rig.matrix_world
    wh = Mw @ pbw.head; fm = Mw @ rig.pose.bones["finger3-1." + side].head
    i2 = Mw @ rig.pose.bones["finger2-1." + side].head; i5 = Mw @ rig.pose.bones["finger5-1." + side].head
    d = (fm - wh).normalized(); n = d.cross((i2 - i5).normalized()).normalized()
    face = (Mw @ rig.pose.bones["head"].head) - wh if toward is None else (Vector(toward) - wh)
    if n.dot(face) < 0: n = -n
    ctr = wh + d * along + n * off
    if axes == "x":
        R3 = Matrix((n, n.cross(d).normalized(), d)).transposed()
    elif axes == "zx":
        R3 = Matrix((d, n.cross(d).normalized(), n)).transposed()
    else:
        R3 = Matrix((d.cross(n).normalized(), d, n)).transposed()
    c = prop.constraints.new('CHILD_OF'); c.target = rig; c.subtarget = "wrist." + side
    c.inverse_matrix = Matrix.Identity(4)
    prop.matrix_basis = (Mw @ pbw.matrix).inverted() @ Matrix.Translation(ctr) @ R3.to_4x4()
    print("BUILD attach", prop.name, tuple(round(v, 3) for v in ctr))

def phone_grip_shot(keys):
    """phone fixed in front of his chest (screen toward his face); grip_object closes the right hand on it at every key,
    then the phone is bound to the wrist (Child Of, world kept)."""
    seat_top = SEAT_TOP.copy()
    for fr, lk in keys:
        seated(HOWN, OWNER, fr, seat_top, lean=-4, flex=10, head=lk)
        place_hand(OWNER, "L", fr, seat_top + Vector((0.12, -0.27, 0.17)), (0, 0, -1), (0, -1, 0)); apply_pose(OWNER, "L", "relaxed", fr)
    sc.frame_set(keys[0][0])
    C = Vector((DRV.x - 0.08, seat_top.y - 0.34, seat_top.z + 0.47))
    face = OWNER.matrix_world @ OWNER.pose.bones["head"].head
    n = (face - C).normalized(); up = Vector((0, 0, 1)); L = (up - n * up.dot(n)).normalized(); y_ = L.cross(n).normalized()
    PH.constraints.clear(); PH.matrix_world = Matrix.Translation(C) @ Matrix((n, y_, L)).transposed().to_4x4()
    bpy.context.view_layer.update()
    for fr, lk in keys:
        rep_ = grip_object(OWNER, "R", fr, PH, C - n * 0.0045, n, grip="wrap")
        print("BUILD phone grip", fr, rep_)
    sc.frame_set(keys[0][0])
    Mw = OWNER.matrix_world; pbw = OWNER.pose.bones["wrist.R"]
    world = PH.matrix_world.copy()
    c_ = PH.constraints.new('CHILD_OF'); c_.target = OWNER; c_.subtarget = "wrist.R"
    c_.inverse_matrix = (Mw @ pbw.matrix).inverted(); PH.matrix_basis = world

# phone in a dash mount by the centre vent, screen toward the driver; he taps it with his index finger
MOUNT_C = Vector((0.16, -1.02, 1.00))
def mount_phone():
    face = Vector((DRV.x, SEAT_TOP.y - 0.05, SEAT_TOP.z + 0.78))
    n = (face - MOUNT_C); n.z = 0; n.normalize()           # screen normal, horizontal toward him
    up = Vector((0, 0, 1)); y_ = up.cross(n).normalized()
    PH.constraints.clear(); PH.matrix_world = Matrix.Translation(MOUNT_C) @ Matrix((n, y_, up)).transposed().to_4x4()
    # phone local X is its thin axis -> make sure the lit screen faces him: X along n
    rbox("PhoneCradle", (0.012, 0.080, 0.120), MOUNT_C - n * 0.010, blackp_m, CT, 0.004).rotation_euler = (0, 0, math.atan2(n.y, n.x))
    for k in (-1, 1):
        cl = rbox(f"PhoneClamp{k}", (0.018, 0.008, 0.050), MOUNT_C + y_ * (0.037 * k) - n * 0.002, blackp_m, CT, 0.002)
        cl.rotation_euler = (0, 0, math.atan2(n.y, n.x))
    rbox("PhoneMountArm", (0.015, 0.015, 0.07), MOUNT_C - n * 0.02 + Vector((0, 0, -0.08)), blackp_m, CT, 0.004)
    return n
blackp_m = mat("MountBlack", (0.04, 0.04, 0.045), 0.45)
def tap_pose(f, reach, look=(18, -20)):
    """reach 0 = right hand on his thigh, 1 = index fingertip 4 mm off the screen"""
    seat_top = SEAT_TOP.copy()
    seated(HOWN, OWNER, f, seat_top, lean=-4, flex=10 + 6 * reach, head=look)
    place_hand(OWNER, "L", f, seat_top + Vector((0.12, -0.27, 0.17)), (0, 0, -1), (0, -1, 0)); apply_pose(OWNER, "L", "relaxed", f)
    if reach <= 0:
        place_hand(OWNER, "R", f, seat_top + Vector((-0.12, -0.27, 0.17)), (0, 0, -1), (0, -1, 0)); apply_pose(OWNER, "R", "relaxed", f)
        return
    tip = MOUNT_C + PH_N * 0.010 + Vector((0, 0, -0.015))
    fdir = (tip - (seat_top + Vector((-0.10, -0.2, 0.45)))).normalized()
    palm = tip - fdir * 0.095
    rest = seat_top + Vector((-0.12, -0.27, 0.17))
    p_ = rest.lerp(palm, reach)
    place_hand(OWNER, "R", f, p_, (0, 0, -1), fdir); apply_pose(OWNER, "R", "point", f)
    if reach >= 0.99:          # correct so the measured index tip sits 4 mm in front of the screen
        for _ in range(3):
            sc.frame_set(f); tipw = OWNER.matrix_world @ OWNER.pose.bones["finger2-3.R"].tail
            p_ = p_ + (tip - tipw)
            place_hand(OWNER, "R", f, p_, (0, 0, -1), fdir); apply_pose(OWNER, "R", "point", f)
        sc.frame_set(f); print("BUILD tap tip err mm", round(((OWNER.matrix_world @ OWNER.pose.bones["finger2-3.R"].tail) - tip).length * 1000, 1))

PH_N = None
def S08a(f0, f1):
    PRESENT["08a"] = {"own"}
    global PH_N
    PH_N = mount_phone()
    for fr, r_ in ((f0, 0.0), (f0 + 25, 0.6), (f0 + 45, 1.0), (f0 + 75, 1.0), (f1, 0.75)):
        tap_pose(fr, r_)
    c = camera("08a", 45)
    sc.frame_set(f0); Hh = OWNER.matrix_world @ OWNER.pose.bones["head"].head
    cp = Vector((-0.30, -1.15, 1.20)); d1 = (MOUNT_C - cp).normalized(); d2 = (Hh - cp).normalized()
    tgt = cp + (d1 + d2).normalized()
    cam_key(c, f0, cp, tgt, lens=22); cam_key(c, f1, cp + Vector((0.03, 0.03, 0)), tgt, lens=22)
def S08b(f0, f1):
    PRESENT["08b"] = {"own"}
    for fr, r_, lk in ((f0, 0.75, (14, -18)), (f0 + 35, 0.3, (6, -10)), (f1, 0.0, (4, -6))):
        tap_pose(fr, r_, lk)
    c = camera("08b", 50)
    sc.frame_set(f0); hz = (OWNER.matrix_world @ OWNER.pose.bones["head"].head)
    tgt = hz + Vector((0, 0, 0.04))
    cam_key(c, f0, tgt + Vector((-0.42, -0.62, 0.06)), tgt, lens=50); cam_key(c, f1, tgt + Vector((-0.36, -0.54, 0.05)), tgt, lens=50)

CLIP = dup(bpy.data.objects["Clipboard"], "ClipHeld", (0, 0, 0), (0, 0, 0), 1.0, CI, linked=False)
bpy.ops.mesh.primitive_cube_add(size=1); GAUZE = bpy.context.active_object; GAUZE.name = "GauzePad"
GAUZE.scale = (0.07, 0.07, 0.008); bpy.ops.object.transform_apply(scale=True)
_gb = GAUZE.modifiers.new("bev", 'BEVEL'); _gb.width = 0.003; _gb.segments = 2
GAUZE.data.materials.append(mat("Gauze", (0.97, 0.97, 0.96), 0.8)); move_to(GAUZE, CI)
def S09(f0, f1):
    PRESENT["09"] = {"own", "ma"}
    st = IX + Vector((0.40, 0.15, STR_Z + 0.13))
    seated(HOWN, OWNER, f0, st, yaw=90, lean=-6, flex=8, head=(10, 15), knee_fwd=0.58, foot_z=0.30)
    seated(HOWN, OWNER, f1, st, yaw=90, lean=-6, flex=9, head=(12, 25), knee_fwd=0.58, foot_z=0.30)
    hands_lap(OWNER, f0, st, yaw=90); hands_lap(OWNER, f1, st, yaw=90)
    # medic A stands behind him (he faces +X), left hand flat on his upper back, right arm bent, hand at his own waist
    pa = IX + Vector((-0.30, 0.22, 0))
    for fr, hd, dz in ((f0, (22, 0), 0.0), ((f0 + f1) // 2, (25, 5), -0.03), (f1, (24, 2), -0.05)):
        stand(HMA, MEDA, fr, pa, yaw=90, head=hd, flex=14, hands=False)
        place_hand(MEDA, "L", fr, IX + Vector((0.155, 0.27, STR_Z + 0.50 + dz)), (1, 0, 0), (0, 0.15, 1)); apply_pose(MEDA, "L", "flat_palm", fr)
        place_hand(MEDA, "R", fr, pa + Vector((0.10, -0.24, 1.02)), (0, 1, 0), (1, 0.3, -0.4)); apply_pose(MEDA, "R", "relaxed", fr)
    attach_to_hand(GAUZE, MEDA, "L", f0, along=0.095, off=0.036, toward=IX + Vector((0.4, 0.27, STR_Z + 0.5)), axes="z")
    c = camera("09", 24)
    cam_key(c, f0, IX + Vector((0.55, -1.55, 1.55)), IX + Vector((0.0, 0.2, 1.0))); cam_key(c, f1, IX + Vector((0.45, -1.35, 1.52)), IX + Vector((0.0, 0.25, 1.0)))

def S10(f0, f1):
    PRESENT["10"] = {"own", "mb"}
    st = IX + Vector((0.30, -0.25, STR_Z + 0.06))
    seated(HOWN, OWNER, f0, st, yaw=180, lean=-6, flex=8, head=(10, 0), legs_out=True)
    seated(HOWN, OWNER, f1, st, yaw=180, lean=-6, flex=8, head=(8, 8), legs_out=True)
    hands_lap(OWNER, f0, st, yaw=180, legs_out=True); hands_lap(OWNER, f1, st, yaw=180, legs_out=True)
    RZ = STR_Z + 0.10
    for H_, rg, x, yaw_, rx, hd in ():
        for fr, h2, dy in ((f0, hd, 0.0), (f1, (hd[0] + 4, -8 if x < 0 else 8), 0.02)):
            pos = IX + Vector((x, 0.62, 0))
            stand(H_, rg, fr, pos, yaw=yaw_, head=h2, flex=18, hands=False)
            # both hands on the stretcher's side rail, palms down, elbows bent
            for s, sy in (("L", 1), ("R", -1)):
                sgn = 1 if yaw_ < 0 else -1
                place_hand(rg, s, fr, IX + Vector((rx, 0.62 + sy * sgn * 0.17 + dy, RZ + 0.012)), (0, 0, -1), (sgn * 1, 0, -0.25))
                apply_pose(rg, s, "wrap_grip", fr, amount=0.6)
    pb_ = IX + Vector((-0.50, 1.30, 0))
    for fr, hd in ((f0, (30, 0)), (f1, (32, -6))):
        stand(HMB, MEDB, fr, pb_, yaw=160, head=hd, flex=6, hands=False)
        c3 = Matrix.Rotation(R_(160), 3, 'Z')
        place_hand(MEDB, "L", fr, pb_ + c3 @ Vector((0.06, -0.40, 1.10)), c3 @ Vector((0, 0.45, -1)), c3 @ Vector((-1, 0, 0.1))); apply_pose(MEDB, "L", "hold_flat_object", fr)
        place_hand(MEDB, "R", fr, pb_ + c3 @ Vector((-0.22, -0.36, 1.05)), c3 @ Vector((1, 0, 0)), c3 @ Vector((0, -0.4, 0.9))); apply_pose(MEDB, "R", "relaxed", fr)
    attach_to_hand(CLIP, MEDB, "L", f0, along=0.15, off=0.035, axes="zx")
    c = camera("10", 24)
    cam_key(c, f0, IX + Vector((0.25, 3.9, 1.15)), IX + Vector((0.3, 0.4, 0.95))); cam_key(c, f1, IX + Vector((0.25, 3.6, 1.15)), IX + Vector((0.3, 0.4, 0.95)))

def amb_lights(f0, f1):
    for k, f in enumerate(range(f0, f1 + 1, 8)):
        emit_key(red_m, f, 30 if k % 2 == 0 else 2); emit_key(blue_m, f, 2 if k % 2 == 0 else 30)
def S11(f0, f1):
    PRESENT["11"] = set()
    keyobj(AM, f0, loc=RX + Vector((1.5, -24, 0)), rot=(0, 0, 0)); keyobj(AM, f1, loc=RX + Vector((1.5, 2, 0)), rot=(0, 0, 0))
    for fc in []: pass
    c = camera("11", 32)
    cam_key(c, f0, RX + Vector((-1.6, 8.0, 0.7)), RX + Vector((1.5, -14, 1.5))); cam_key(c, f1, RX + Vector((-1.9, 8.4, 0.8)), RX + Vector((1.5, 2, 1.4)))
def S12(f0, f1):
    PRESENT["12"] = set()
    keyobj(AM, f0, loc=RX + Vector((1.5, 6, 0)), rot=(0, 0, R_(180))); keyobj(AM, f1, loc=RX + Vector((1.5, -6, 0)), rot=(0, 0, R_(180)))
    c = camera("12", 35)
    cam_key(c, f0, RX + Vector((1.4, 11.5, 1.3)), RX + Vector((1.5, 6, 1.2)), lens=35); cam_key(c, f1, RX + Vector((1.45, 1.5, 1.25)), RX + Vector((1.5, -6, 1.15)), lens=35)

def S13a(f0, f1):
    PRESENT["13a"] = {"dog"}
    D0 = Vector((KX.x + 0.02, (cminy + cmaxy) / 2 + 0.02, CRATE_FLOOR + 0.005)); n = f1 - f0
    for k in range(0, n + 1, 10):
        t = k / n
        dog_key(f0 + k, D0, -90, dog_pose_stand(head=(6 * math.sin(t * 4), 0, 32 + 8 * math.sin(t * 3.0)), tail=20 * math.sin(k * 0.5), pant=4 * math.sin(k * 0.9)))
    c = camera("13a", 35)
    sc.frame_set(f0); tgt = DOG.matrix_world @ DOG.pose.bones["head"].head
    cam_key(c, f0, tgt + Vector((0.25, -1.4, 0.05)), tgt); cam_key(c, f1, tgt + Vector((0.18, -1.15, 0.03)), tgt)
def S13b(f0, f1):
    PRESENT["13b"] = {"dog"}
    D0 = Vector((KX.x + 0.02, (cminy + cmaxy) / 2 + 0.02, CRATE_FLOOR + 0.005)); n = f1 - f0
    for k in range(0, n + 1, 10):
        dog_key(f0 + k, D0, -90, dog_pose_stand(head=(-5, 0, 30 + 8 * math.sin(k * 0.05)), tail=15 * math.sin(k * 0.4), pant=3 * math.sin(k * 0.9)))
    c = camera("13b", 32)
    tgt = Vector((KX.x + 0.25, 0.1, 1.12))
    cam_key(c, f0, tgt + Vector((0.15, -2.4, 0.22)), tgt); cam_key(c, f1, tgt + Vector((0.10, -2.15, 0.18)), tgt)

# hospital: the real curled sleeping-dog scan lies on the bed against his legs, head toward his lap;
# his left hand rests flat on its back, right arm by his side
SDH = dup(bpy.data.objects["SleepDog"], "SleepDogHosp", (0, 0, 0), (0, 0, 0), 0.85, CH, linked=True)
SDH.hide_render = SDH.hide_viewport = False
def _ray_down(obj, x, y, z0=3.0):
    inv = obj.matrix_world.inverted()
    ok, loc, n, i = obj.ray_cast(inv @ Vector((x, y, z0)), inv.to_3x3() @ Vector((0, 0, -1)))
    return (obj.matrix_world @ loc) if ok else None
_bt = _ray_down(BD, HX.x + 0.20, 0.52)
BED_TOP = _bt.z if _bt else MAT_Z
SDH.location = Vector((HX.x + 0.21, 0.52, BED_TOP + 0.002)); bpy.context.view_layer.update()
_bk = _ray_down(SDH, HX.x + 0.06, 0.62)
DOG_BACK = _bk if _bk else Vector((HX.x + 0.07, 0.28, BED_TOP + 0.22))
print("BUILD hosp bed top", round(BED_TOP, 3), "dog back", tuple(round(v, 3) for v in DOG_BACK))
def hosp_man(f, smile_head=(18, -20), stroke=0.0):
    st = HX + Vector((-0.22, 0.78, BED_TOP + 0.02))
    seated(HOWN, OWNER, f, st, yaw=0, lean=-34, flex=12, head=smile_head, legs_out=True)
    sc.frame_set(f)
    hp = DOG_BACK + Vector((0.0, -0.05 * stroke, 0.0))
    _h = _ray_down(SDH, hp.x, hp.y) or hp
    place_hand(OWNER, "L", f, _h, (0.15, 0, -1), (0.35, -1, 0)); apply_pose(OWNER, "L", "relaxed", f)
    place_hand(OWNER, "R", f, st + Vector((-0.18, -0.25, 0.10)), (-0.3, 0, -1), (0, -1, 0)); apply_pose(OWNER, "R", "relaxed", f)
def S14a(f0, f1):
    PRESENT["14a"] = {"own"}
    for fr, t in ((f0, 0.0), ((f0 + f1) // 2, 0.5), (f1, 1.0)):
        hosp_man(fr, smile_head=(26 + 4 * t, 10 + 4 * t), stroke=0.3 * t)
    c = camera("14a", 30)
    tgt = HX + Vector((0.0, 0.50, BED_TOP + 0.40))
    cam_key(c, f0, tgt + Vector((1.55, -0.55, 0.45)), tgt); cam_key(c, f1, tgt + Vector((1.35, -0.45, 0.40)), tgt)
def S14b(f0, f1):
    PRESENT["14b"] = {"own"}
    for fr, t in ((f0, 0.0), ((f0 + f1) // 2, 1.0), (f1, 0.0)):
        hosp_man(fr, smile_head=(28, 12), stroke=t)
    c = camera("14b", 40)
    tgt = HX + Vector((0.0, 0.62, BED_TOP + 0.45))
    cam_key(c, f0, tgt + Vector((1.00, -0.45, 0.35)), tgt, lens=32); cam_key(c, f1, tgt + Vector((0.86, -0.38, 0.30)), tgt, lens=32)

# field: the same scan, curled asleep in the grass, back toward the cameras (-Y), head on its front paws
DOGSPOT = CLR + Vector((0.2, -0.4, 0)); MANSPOT = CLR + Vector((0.4, 0.75, 0))
SDF = dup(bpy.data.objects["SleepDog"], "SleepDogField", DOGSPOT + Vector((0, 0, 0.0)), (0, 0, R_(90)), 1.0, CR, linked=True)
SDF.hide_render = SDF.hide_viewport = False
def clear_man(f, head=(30, 0), breath=0.0, back=0.0):
    stand(HOWN, OWNER, f, MANSPOT + Vector((0, back, 0)), yaw=8, head=head, flex=6, breath=breath)
def clear_dog(f, breath=0.0):
    pass
def S15a(f0, f1):
    PRESENT["15a"] = {"own"}
    for fr, hd in ((f0, (20, 5)), ((f0 + f1) // 2, (30, 0)), (f1, (34, -3))):
        clear_man(fr, head=hd)
    c = camera("15a", 28)
    tgt = MANSPOT.lerp(DOGSPOT, 0.5) + Vector((0, 0, 0.75))
    cam_key(c, f0, tgt + Vector((0.6, -4.6, 0.0)), tgt, lens=26); cam_key(c, f1, tgt + Vector((0.5, -4.2, 0.05)), tgt, lens=26)
def S15b(f0, f1):
    PRESENT["15b"] = set()          # the dog alone; the man is out of this shot
    c = camera("15b", 35)
    # low 3/4 side view at the dog's head height: closed eyes and the side-lying body read clearly
    bpy.context.view_layer.update()
    hp_ = SDF.matrix_world @ Vector((0.0, 0.38, 0.12))       # scan head end (+Y local)
    tgt = hp_.lerp(SDF.matrix_world.translation + Vector((0, 0, 0.12)), 0.35)
    cam_key(c, f0, tgt + Vector((-0.55, -1.05, 0.10)), tgt, lens=40); cam_key(c, f1, tgt + Vector((-0.46, -0.90, 0.08)), tgt, lens=40)
def S15c(f0, f1):
    PRESENT["15c"] = {"own"}
    for fr, hd, br in ((f0, (34, -3), 0), ((f0 + f1) // 2, (38, -4), 3), (f1, (36, -2), 0)):
        clear_man(fr, head=hd, breath=br); clear_dog(fr)
    c = camera("15c", 45)
    tgt = MANSPOT + Vector((0, 0, 1.55))
    cam_key(c, f0, tgt + Vector((0.35, -1.45, -0.25)), tgt); cam_key(c, f1, tgt + Vector((0.30, -1.20, -0.22)), tgt)
def S15d(f0, f1):
    PRESENT["15d"] = {"own"}
    for fr in (f0, f1): clear_man(fr, head=(36, -2)); clear_dog(fr)
    c = camera("15d", 28)
    tgt = (MANSPOT + DOGSPOT) / 2 + Vector((0, 0, 0.5))
    cam_key(c, f0, tgt + Vector((1.2, -3.0, 0.6)), tgt); cam_key(c, f1, tgt + Vector((2.2, -5.5, 4.0)), tgt)

FUN = {"01": S01, "02": S02, "03": S03, "04": S04, "05": S05, "06": S06, "07a": S07a, "07b": S07b, "07c": S07c,
       "08a": S08a, "08b": S08b, "09": S09, "10": S10, "11": S11, "12": S12, "13a": S13a, "13b": S13b,
       "14a": S14a, "14b": S14b, "15a": S15a, "15b": S15b, "15c": S15c, "15d": S15d}

# dog paw override: "__FR" in a pose = armature-space offset of the front-right paw target
_dog_key_orig = dog_key
def dog_key(f, loc, yaw, pose):
    fr = pose.pop("__FR", None)
    _dog_key_orig(f, loc, yaw, pose)
    if fr is not None:
        sc.frame_set(f)
        pb = DOG.pose.bones["IK_hoof.FR"]
        if isinstance(fr, str) or (isinstance(fr, tuple) and fr and fr[0] == "trig"):
            u, lift = (1.0, 0.0) if isinstance(fr, str) else (fr[1], fr[2])
            tw = TRIG + Vector((0, 0.03, 0.022))
            restw = DOG.matrix_world @ DOG.data.bones["IK_hoof.FR"].head_local
            off_w = (tw - restw) * u + Vector((0, 0, lift)); off_a = DOG.matrix_world.inverted().to_3x3() @ off_w
        else:
            off_a = Vector(fr)
        Mrest = DOG.data.bones["IK_hoof.FR"].matrix_local
        pb.location = Mrest.to_3x3().inverted() @ off_a
        pb.keyframe_insert("location", frame=f)

# park all characters far away before the first shot that uses them
def park(key, f):
    if key == "dog":
        DOG.location = PARK["dog"]; DOG.keyframe_insert("location", frame=f); return
    rig, H = CHARS[key]
    stand(H, rig, f, PARK[key])

lay = layout()
for sid, st, f0, f1 in lay:
    FUN[sid](f0, f1)
    pres = PRESENT[sid]
    for key in ("own", "ma", "mb", "dog"):
        if key not in pres:
            park(key, f0); park(key, f1)
    print("BUILD shot", sid, st, f0, f1, sorted(pres))

f08 = SH["08a"][1]; f08e = SH["08b"][2]
for fr, hid in ((1, True), (f08 - 1, True), (f08, False), (f08e, False), (f08e + 1, True)):
    PH.hide_render = PH.hide_viewport = hid; PH.keyframe_insert("hide_render", frame=fr); PH.keyframe_insert("hide_viewport", frame=fr)
f9, f9e = SH["09"][1], SH["09"][2]
f10, f10e = SH["10"][1], SH["10"][2]
for ob_, (a_, b_) in ((CLIP, (f10, f10e)), (GAUZE, (f9, f9e))):
    for fr, hid in ((1, True), (a_ - 1, True), (a_, False), (b_, False), (b_ + 1, True)):
        ob_.hide_render = ob_.hide_viewport = hid; ob_.keyframe_insert("hide_render", frame=fr); ob_.keyframe_insert("hide_viewport", frame=fr)
# hard cuts: boundary keys get vector handles, the last key of every shot is constant (no inbetween across a cut)
BOUND = set()
for sid, st, f0, f1 in lay: BOUND |= {f0, f1}
def fix_curves(idblock):
    ad = idblock.animation_data
    if not ad or not ad.action: return
    for fc in ad.action.fcurves if hasattr(ad.action, "fcurves") else []:
        for kp in fc.keyframe_points:
            fr = int(round(kp.co.x))
            if fr in BOUND:
                kp.handle_left_type = 'VECTOR'; kp.handle_right_type = 'VECTOR'
            if any(fr == f1 for _, _, _, f1 in lay): kp.interpolation = 'CONSTANT'
        fc.update()
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
            if any(fr == f1 for _, _, _, f1 in lay): kp.interpolation = 'CONSTANT'
        fc.update()
for m in (fl_m, glint_m, hit_m, red_m, blue_m):
    if m.node_tree.animation_data and m.node_tree.animation_data.action:
        for fc in all_fcurves(m.node_tree.animation_data.action):
            for kp in fc.keyframe_points: kp.interpolation = 'LINEAR' if m is not red_m and m is not blue_m else 'CONSTANT'

# camera markers (hard cuts)
for sid, st, f0, f1 in lay:
    mk = sc.timeline_markers.new("S" + sid, frame=f0); mk.camera = CAMS[sid]
sc.camera = CAMS[lay[0][0]]

# look
sc.render.engine = 'CYCLES'; sc.cycles.samples = 48; sc.cycles.use_denoising = True
sc.view_settings.view_transform = 'AgX'
try: sc.view_settings.look = 'AgX - Punchy'
except Exception: pass
sc.render.use_motion_blur = False
# hide the library originals
for o in bpy.data.collections["PROPS"].objects: o.hide_render = o.hide_viewport = True
for o in LIBC.objects: o.hide_render = o.hide_viewport = True
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("BUILD_OK", OUT, "frames", sc.frame_start, sc.frame_end)
