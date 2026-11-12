"""Build the AIAsleep set: car interior, seated driver, night highway, city, lights.
blender -b work/driver.blend --python scripts/02_build_scene.py -- work/scene.blend"""
import sys, os, math, bpy
from mathutils import Vector, Matrix
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
A = os.path.join(HERE, "assets"); out = sys.argv[sys.argv.index("--") + 1]
exec(open(os.path.join(HERE, "..", "pipeline", "anim_lib.py")).read())
sc = bpy.context.scene
sc.render.fps = 60; sc.frame_start, sc.frame_end = 1, 2610
sc.render.resolution_x, sc.render.resolution_y = 1080, 1920
sc.render.engine = "CYCLES"; sc.cycles.samples = 48; sc.cycles.adaptive_threshold = 0.05; sc.cycles.use_denoising = True
sc.view_settings.view_transform = "AgX"; sc.view_settings.look = "AgX - Medium High Contrast"
def coll(n):
    c = bpy.data.collections.new(n); sc.collection.children.link(c); return c
def imp(path, c):
    before = set(bpy.data.objects); bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    for o in new:
        for u in list(o.users_collection): u.objects.unlink(o)
        c.objects.link(o)
    return new
# ---------------- car (stationary, faces -Y). Driver rig sits at origin; car is offset so the driver's seat is under him.
CAR_OFF = Vector((-0.37, -0.55, 0.0))
cc = coll("Car")
car = imp(os.path.join(A, "models/saab.glb"), cc)
CarRoot = bpy.data.objects.new("CarRoot", None); cc.objects.link(CarRoot); CarRoot.location = CAR_OFF
for o in car:
    if o.parent is None: o.parent = CarRoot
for o in list(car):
    if o.type == "MESH" and any(k in o.name for k in ("Logo", "Number_Plane")):
        bpy.data.objects.remove(o, do_unlink=True)
car = [o for o in cc.objects]
bpy.context.view_layer.update()
for o in car:   # bring the car's own wheel 6 cm toward the driver (telescoping column)
    if o.name.startswith("Wheel_Steering") and o.type == "MESH":
        mw = o.matrix_world.copy(); mw.translation.y += 0.06; o.matrix_world = mw
WHEEL_C = Vector((0.0, -0.525, 0.92)); WHEEL_TILT = -66   # car's own wheel (Wheel_Steering_*), rim plane tilt
# ---------------- driver
rig = bpy.data.objects["Driver"]
R = make_human_ctrl(rig); H = Human(R)
def seat_pose(f, flex=-14, side=0, twist=0, head=(0, 0), hip=Vector((0, 0.06, 0.62))):
    H.key_root(f, hip, flex=flex, side=side)
    H.key_spine(f, flex=8 + 0.0, twist=twist, side=side * 0.5, head=head)
def feet(f, dx=0.0):
    for s, x in (("L", 0.13), ("R", -0.13)):
        a = H.ankle[s]
        M = Matrix.Translation(Vector((x, -0.80 + dx, 0.37))) @ Matrix.Rotation(math.radians(-22), 4, 'X') @ Matrix.Translation(-a) @ R.rest("IK_foot." + s)
        R.key_world("IK_foot." + s, f, M)
        n = "Pole_knee." + s; pb = R.PB[n]
        pb.location = R.rest(n).to_3x3().inverted() @ (Vector((x * 1.3, -0.9, 0.9)) - R.BN[n].head_local); pb.keyframe_insert("location", frame=f, group=n)
def rim_point(ang, r=0.18):
    """point on the wheel rim at clock angle (deg, 0 = top, + = clockwise seen by the driver)"""
    t = math.radians(WHEEL_TILT); a = math.radians(ang)
    up = Matrix.Rotation(t, 3, 'X') @ Vector((0, -1, 0)); right = Vector((-1, 0, 0))   # driver faces -Y, his right is -X
    return WHEEL_C + up * (r * math.cos(a)) + right * (r * math.sin(a)), up, Matrix.Rotation(t, 3, 'X') @ Vector((0, 0, 1))
def hands(f, angL=-60, angR=60, off=0.0):
    for s, ang in (("L", angL), ("R", angR)):
        p, up, nrm = rim_point(ang)
        rad = (p - WHEEL_C).normalized()
        W = p + rad * 0.03 + nrm * 0.05 + Vector((0, off, 0))
        d = (-rad + up * 0.2).normalized(); n = nrm  # fingers wrap toward the centre, palm faces the rim plane
        H.key_hand(s, f, W, d, n, pole=W + Vector((0.35 if s == "L" else -0.35, 0.4, -0.35)))
seat_pose(1); feet(1); hands(1)
# fingers wrap the rim
def grip(f, s, k=1.0):
    for fi in (2, 3, 4, 5):
        for j, a in ((1, 55), (2, 70), (3, 45)):
            n = "finger%d-%d.%s" % (fi, j, s); pb = R.PB[n]
            pb.rotation_quaternion = Matrix.Rotation(math.radians(a * k), 4, 'X').to_quaternion(); pb.keyframe_insert("rotation_quaternion", frame=f, group=n)
    for j, a in ((1, 10), (2, 25), (3, 25)):
        n = "finger1-%d.%s" % (j, s); pb = R.PB[n]
        pb.rotation_quaternion = Matrix.Rotation(math.radians(a * k), 4, 'X').to_quaternion(); pb.keyframe_insert("rotation_quaternion", frame=f, group=n)
grip(1, "L"); grip(1, "R")

# ---------------- materials
def img(path, cs="sRGB"):
    i = bpy.data.images.load(path, check_existing=True); i.colorspace_settings.name = cs; return i
def texdir(n):
    d = os.path.join(A, "tex", n, "textures"); fs = os.listdir(d)
    g = lambda k: os.path.join(d, next(f for f in fs if k in f)) if any(k in f for f in fs) else None
    return g("diff") or g("albedo"), g("nor_gl"), g("rough")
def pbr(name, tex, scale=4.0, tint=None, rough_mul=1.0, bump=0.3):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; N = nt.nodes; L = nt.links
    bs = N["Principled BSDF"]; d, nrm, r = texdir(tex)
    tc = N.new("ShaderNodeTexCoord"); mp = N.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (scale,) * 3
    L.new(tc.outputs["Object"], mp.inputs[0])
    def t(path, cs):
        n = N.new("ShaderNodeTexImage"); n.image = img(path, cs); n.projection = "BOX"; n.projection_blend = 0.3; L.new(mp.outputs[0], n.inputs[0]); return n
    td = t(d, "sRGB")
    if tint:
        mx = N.new("ShaderNodeMix"); mx.data_type = "RGBA"; mx.blend_type = "MULTIPLY"; mx.inputs[0].default_value = 1.0
        L.new(td.outputs[0], mx.inputs[6]); mx.inputs[7].default_value = (*tint, 1); L.new(mx.outputs[2], bs.inputs["Base Color"])
    else: L.new(td.outputs[0], bs.inputs["Base Color"])
    if r:
        tr = t(r, "Non-Color"); mt = N.new("ShaderNodeMath"); mt.operation = "MULTIPLY"; mt.inputs[1].default_value = rough_mul
        L.new(tr.outputs[0], mt.inputs[0]); L.new(mt.outputs[0], bs.inputs["Roughness"])
    if nrm:
        tn = t(nrm, "Non-Color"); nm = N.new("ShaderNodeNormalMap"); nm.inputs[0].default_value = bump
        L.new(tn.outputs[0], nm.inputs[1]); L.new(nm.outputs[0], bs.inputs["Normal"])
    return m
M_seat = pbr("SeatLeather", "fabric_leather_02", 3.0, tint=(0.16, 0.15, 0.15), bump=0.6)
M_trim = pbr("TrimFabric", "denim_fabric", 6.0, tint=(0.25, 0.24, 0.24), rough_mul=1.2, bump=0.4)
M_dash = pbr("DashLeather", "brown_leather", 5.0, tint=(0.10, 0.10, 0.11), rough_mul=0.9, bump=0.5)
for o in car:
    if o.type != "MESH": continue
    for sl in o.material_slots:
        if not sl.material: continue
        nm = sl.material.name
        if nm.startswith("M_Interrior_Dark"): sl.material = M_seat if "Seat" in o.name else M_dash
        elif nm.startswith("M_Interrior_Gray") or nm.startswith("M_Interrior_Light"): sl.material = M_trim
        elif nm.startswith("M_Rubber"): sl.material = M_dash
# car paint: deep graphite instead of the blue
for m in bpy.data.materials:
    if m.name.startswith("M_Body") and m.node_tree:
        bs = m.node_tree.nodes.get("Principled BSDF")
        if bs: bs.inputs["Coat Weight"].default_value = 0.8; bs.inputs["Roughness"].default_value = 0.25
# patch out the MakeHuman watermark print on the shirt texture (corner text)
for i in bpy.data.images:
    if "casualsuit01_diffuse" in i.name:
        w, h = i.size; px = list(i.pixels)
        def fill(x0, y0, x1, y1, src):
            c = px[(src[1] * w + src[0]) * 4:(src[1] * w + src[0]) * 4 + 4]
            for y in range(int(y0 * h), int(y1 * h)):
                for x in range(int(x0 * w), int(x1 * w)): px[(y * w + x) * 4:(y * w + x) * 4 + 4] = c
        fill(0.0, 0.94, 0.14, 1.0, (int(0.16 * w), int(0.96 * h))); fill(0.84, 0.0, 1.0, 0.05, (int(0.82 * w), int(0.03 * h)))
        i.pixels[:] = px; i.pack()

# ---------------- dash screen (centre console) + dash camera (on the steering column, facing the driver)
uc = coll("CabinFX")
bpy.ops.mesh.primitive_plane_add(size=1); scr = bpy.context.object; scr.name = "DashScreen"
scr.scale = (0.19, 0.12, 1); scr.location = (-0.37, -0.68, 0.98); scr.rotation_euler = (math.radians(-70), 0, 0)
for u in list(scr.users_collection): u.objects.unlink(scr)
uc.objects.link(scr)
bpy.ops.object.modifier_add(type="BEVEL") if False else None
ms = bpy.data.materials.new("ScreenUI"); ms.use_nodes = True; N = ms.node_tree.nodes; L = ms.node_tree.links
bs = N["Principled BSDF"]; bs.inputs["Base Color"].default_value = (0.01, 0.01, 0.012, 1); bs.inputs["Roughness"].default_value = 0.08
uv = N.new("ShaderNodeTexCoord"); mpp = N.new("ShaderNodeMapping"); mpp.inputs["Scale"].default_value = (-1.58, -1, 1); mpp.inputs["Location"].default_value = (1.29, 1, 0)
L.new(uv.outputs["UV"], mpp.inputs[0])
tr = N.new("ShaderNodeTexImage"); tr.image = img(os.path.join(A, "ui/icon_closed_red.png")); tr.extension = "CLIP"
tg = N.new("ShaderNodeTexImage"); tg.image = img(os.path.join(A, "ui/icon_open_green.png")); tg.extension = "CLIP"
L.new(mpp.outputs[0], tr.inputs[0]); L.new(mpp.outputs[0], tg.inputs[0])
mx = N.new("ShaderNodeMix"); mx.data_type = "RGBA"; mx.name = "UI_GREEN"; L.new(tr.outputs[0], mx.inputs[6]); L.new(tg.outputs[0], mx.inputs[7])
L.new(mx.outputs[2], bs.inputs["Emission Color"]); bs.inputs["Emission Strength"].default_value = 6.0
scr.data.materials.append(ms)
# bezel
bpy.ops.mesh.primitive_cube_add(size=1); bz = bpy.context.object; bz.name = "DashScreenBezel"
for u in list(bz.users_collection): u.objects.unlink(bz)
uc.objects.link(bz); bz.parent = scr; bz.scale = (1.06, 1.08, 0.12); bz.location = (0, 0, -0.07)
bz.modifiers.new("b", "BEVEL").width = 0.004; bz.data.materials.append(M_dash)
# dash camera unit: housing + lens
def prim(kind, name, parent=None, **kw):
    getattr(bpy.ops.mesh, "primitive_%s_add" % kind)(**kw); o = bpy.context.object; o.name = name
    for u in list(o.users_collection): u.objects.unlink(o)
    uc.objects.link(o); o.parent = parent; return o
camU = prim("cube", "DashCamHousing", size=1); camU.scale = (0.07, 0.035, 0.032); camU.location = (0.0, -0.80, 1.075)
camU.modifiers.new("b", "BEVEL").width = 0.006; camU.modifiers["b"].segments = 3; camU.data.materials.append(M_dash)
lens = prim("cylinder", "DashCamLens", vertices=48, radius=0.011, depth=0.012); lens.location = (0.0, -0.78, 1.077); lens.rotation_euler = (math.radians(90), 0, 0)
ml = bpy.data.materials.new("LensGlass"); ml.use_nodes = True; b2 = ml.node_tree.nodes["Principled BSDF"]
b2.inputs["Base Color"].default_value = (0.01, 0.015, 0.03, 1); b2.inputs["Roughness"].default_value = 0.02; b2.inputs["Metallic"].default_value = 0.6
b2.inputs["Emission Color"].default_value = (0.2, 0.9, 1.0, 1); b2.inputs["Emission Strength"].default_value = 0.0
lens.data.materials.append(ml)
irled = []
for k in (-1, 1):
    e = prim("uv_sphere", "IR_LED_%d" % k, segments=12, ring_count=8, radius=0.003); e.location = (0.025 * k, -0.783, 1.077)
    mi = bpy.data.materials.new("IRLed"); mi.use_nodes = True; bb = mi.node_tree.nodes["Principled BSDF"]
    bb.inputs["Emission Color"].default_value = (1, 0.15, 0.1, 1); bb.inputs["Emission Strength"].default_value = 2; e.data.materials.append(mi)

# ---------------- world: night city HDRI
w = bpy.data.worlds.new("Night"); sc.world = w; w.use_nodes = True; N = w.node_tree.nodes; L = w.node_tree.links
env = N.new("ShaderNodeTexEnvironment"); env.image = img(os.path.join(A, "tex/hdri/shanghai_bund_2k.hdr"), "Linear Rec.709")
tcw = N.new("ShaderNodeTexCoord"); mpw = N.new("ShaderNodeMapping"); mpw.name = "WorldRot"; L.new(tcw.outputs["Generated"], mpw.inputs[0]); L.new(mpw.outputs[0], env.inputs[0])
L.new(env.outputs[0], N["Background"].inputs[0]); N["Background"].inputs[1].default_value = 0.35; N["Background"].name = "WorldBG"

# ---------------- highway: everything outside moves +Y past the stationary car (WorldMover)
hc = coll("Highway")
Mover = bpy.data.objects.new("WorldMover", None); hc.objects.link(Mover)
ROAD_LEN = 2600.0
bpy.ops.mesh.primitive_plane_add(size=1); rd = bpy.context.object; rd.name = "Road"
for u in list(rd.users_collection): u.objects.unlink(rd)
hc.objects.link(rd); rd.parent = Mover; rd.scale = (16, ROAD_LEN, 1); rd.location = (-2.0, -ROAD_LEN / 2 + 200, 0.0)
M_asph = pbr("Asphalt", "asphalt_02", 0.35, rough_mul=1.0, bump=0.8)
rd.data.materials.append(M_asph)
# lane dashes + edge lines (thin painted strips, emissive-free retro-reflective white)
mpaint = bpy.data.materials.new("LanePaint"); mpaint.use_nodes = True; pb_ = mpaint.node_tree.nodes["Principled BSDF"]
pb_.inputs["Base Color"].default_value = (0.75, 0.72, 0.62, 1); pb_.inputs["Roughness"].default_value = 0.5
def strip(name, x, length, gap, width=0.15):
    bpy.ops.mesh.primitive_plane_add(size=1); o = bpy.context.object; o.name = name
    for u in list(o.users_collection): u.objects.unlink(o)
    hc.objects.link(o); o.parent = Mover; o.scale = (width, length, 1); o.location = (x, 200, 0.004)
    a = o.modifiers.new("arr", "ARRAY"); a.use_relative_offset = False; a.use_constant_offset = True
    a.constant_offset_displace = (0, -(length + gap) / length * 1.0 * length / o.scale[1] if False else -(length + gap), 0)
    a.count = int(ROAD_LEN / (length + gap)); o.data.materials.append(mpaint); return o
# array offsets are in local space -> divide by scale
for nm, x, ln, gp in (("LaneDash_L", 1.85, 3.0, 9.0), ("LaneDash_R", -1.85, 3.0, 9.0), ("EdgeLine_L", 5.4, 40.0, 0.0), ("EdgeLine_R", -9.2, 40.0, 0.0)):
    o = strip(nm, x, ln, gp); o.modifiers["arr"].use_constant_offset = False; o.modifiers["arr"].use_relative_offset = True
    o.modifiers["arr"].relative_offset_displace = (0, -(ln + gp) / ln, 0)
# guard rails / barrier (concrete median) as long boxes with concrete texture
M_conc = pbr("Concrete", "asphalt_02", 0.8, tint=(0.55, 0.55, 0.52), bump=0.5)
for nm, x in (("Median", 6.2), ("Barrier_R", -9.8)):
    bpy.ops.mesh.primitive_cube_add(size=1); o = bpy.context.object; o.name = nm
    for u in list(o.users_collection): u.objects.unlink(o)
    hc.objects.link(o); o.parent = Mover; o.scale = (0.5, ROAD_LEN, 0.85); o.location = (x, -ROAD_LEN / 2 + 200, 0.42)
    o.modifiers.new("b", "BEVEL").width = 0.08; o.data.materials.append(M_conc)
# street lights: imported model + warm sodium/LED point light, every 38 m on the median
sl = imp(os.path.join(A, "models/streetlight.glb"), hc)
slm = [o for o in sl if o.type == "MESH"]; sl_names = [o.name for o in sl]
bpy.context.view_layer.update()
for o in slm:
    mw = o.matrix_world.copy(); o.parent = None; o.matrix_world = mw
bpy.ops.object.select_all(action="DESELECT")
for o in slm: o.select_set(True)
bpy.context.view_layer.objects.active = slm[0]
if len(slm) > 1: bpy.ops.object.join()
SL = bpy.context.view_layer.objects.active; SL.name = "StreetLightSrc"
for n in sl_names:
    o = bpy.data.objects.get(n)
    if o is not None and o.type == "EMPTY": bpy.data.objects.remove(o, do_unlink=True)
bpy.context.view_layer.update()
dims = SL.dimensions; s_ = 10.0 / max(dims); SL.scale = (s_,) * 3; SL.location = (0, 0, 0); SL.rotation_euler = (0, 0, 0)
bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
bpy.context.view_layer.update()
SL.hide_render = True; SL.hide_viewport = True
lamp_light = bpy.data.lights.new("StreetLamp", "POINT"); lamp_light.energy = 9000; lamp_light.color = (1.0, 0.72, 0.42); lamp_light.shadow_soft_size = 0.4
for k in range(int(ROAD_LEN / 38)):
    y = 200 - k * 38
    for side, x, rz in ((0, 6.2, 0), (1, -9.8, 180)):
        if side == 1 and k % 2: continue
        o = bpy.data.objects.new("SLamp_%d_%d" % (k, side), SL.data); hc.objects.link(o); o.parent = Mover
        o.location = (x, y, 0.85 if side == 0 else 0.85); o.rotation_euler = (0, 0, math.radians(rz + 90))
        if k < 70:   # real lights only along the stretch the camera sees
            l = bpy.data.objects.new("SLampLight_%d_%d" % (k, side), lamp_light); hc.objects.link(l); l.parent = Mover
            l.location = (x - 2.6 if side == 0 else x + 2.6, y, 10.0)
# city skyline: imported city blocks set back on both sides, scaled up; parallax-moved at a fraction of road speed
cityc = coll("City")
cobjs = imp(os.path.join(A, "models/city.glb"), cityc)
CityRoot = bpy.data.objects.new("CityRoot", None); cityc.objects.link(CityRoot)
for o in cobjs:
    if o.parent is None: o.parent = CityRoot
bpy.context.view_layer.update()
CityRoot.scale = (3.0, 3.0, 3.0); CityRoot.location = (-260, -150, -2)
City2 = bpy.data.objects.new("CityRoot2", None); cityc.objects.link(City2)
for o in cobjs:
    if o.parent == CityRoot and o.type in ("MESH", "EMPTY"):
        pass
# second skyline copy via collection instance on the other side
cityc_inst = bpy.data.objects.new("CityInst", None); cityc_inst.instance_type = "COLLECTION"; cityc_inst.instance_collection = cityc
sc.collection.objects.link(cityc_inst); cityc_inst.location = (520, -600, 0); cityc_inst.rotation_euler = (0, 0, math.radians(180))
# building windows glow: boost emission-ish by raising the city material brightness slightly at night
# traffic: two other cars (linked copies of the sedan body parts) in neighbouring lanes with head/tail lights
tc_ = coll("Traffic")
def traffic_car(name, x, col):
    root = bpy.data.objects.new(name, None); tc_.objects.link(root)
    for o in car:
        if o.type == "MESH" and o.name in bpy.data.objects:
            d = bpy.data.objects.new(name + "_" + o.name[:20], o.data); tc_.objects.link(d); d.parent = root; d.matrix_parent_inverse = Matrix.Identity(4)
            d.matrix_world = Matrix.Translation(-CAR_OFF) @ o.matrix_world if False else o.matrix_world.copy()
    for k in (-1, 1):
        t = bpy.data.lights.new(name + "_tail%d" % k, "POINT"); t.energy = 25; t.color = (1, 0.05, 0.02); t.shadow_soft_size = 0.1
        to = bpy.data.objects.new(name + "_tail%d" % k, t); tc_.objects.link(to); to.parent = root; to.location = (CAR_OFF.x + 0.65 * k, CAR_OFF.y + 2.9, 0.75)
        hl = bpy.data.lights.new(name + "_head%d" % k, "SPOT"); hl.energy = 400; hl.spot_size = math.radians(50); hl.color = (1, 0.95, 0.85)
        ho = bpy.data.objects.new(name + "_head%d" % k, hl); tc_.objects.link(ho); ho.parent = root; ho.location = (CAR_OFF.x + 0.6 * k, CAR_OFF.y - 2.0, 0.7)
        ho.rotation_euler = (math.radians(95), 0, 0)
    root.location = (x, 0, 0); return root
bpy.context.view_layer.update()
T1 = traffic_car("TrafficA", -3.7, None); T2 = traffic_car("TrafficB", 3.7, None)
# our own head/tail lights
for k in (-1, 1):
    hl = bpy.data.lights.new("OurHead%d" % k, "SPOT"); hl.energy = 600; hl.spot_size = math.radians(45); hl.color = (1, 0.96, 0.9)
    ho = bpy.data.objects.new("OurHead%d" % k, hl); cc.objects.link(ho); ho.location = (CAR_OFF.x + 0.6 * k, CAR_OFF.y - 2.05, 0.7); ho.rotation_euler = (math.radians(98), 0, 0)
    t = bpy.data.lights.new("OurTail%d" % k, "POINT"); t.energy = 20; t.color = (1, 0.05, 0.02)
    to = bpy.data.objects.new("OurTail%d" % k, t); cc.objects.link(to); to.location = (CAR_OFF.x + 0.65 * k, CAR_OFF.y + 2.9, 0.78)
# ---------------- cabin lights: dash ambient, alarm (red), calm (cyan), key on the face from the screen side, rim from the window
def area(name, loc, rot, size, e, col, c=uc):
    l = bpy.data.lights.new(name, "AREA"); l.energy = e; l.size = size; l.color = col
    o = bpy.data.objects.new(name, l); c.objects.link(o); o.location = loc; o.rotation_euler = rot; return o
area("Key_Dash", (-0.20, -0.62, 1.0), (math.radians(-80), 0, math.radians(200)), 0.25, 4.0, (0.55, 0.75, 1.0))
area("Fill_Instrument", (0.0, -0.66, 0.98), (math.radians(-75), 0, math.radians(180)), 0.2, 1.5, (0.9, 0.85, 0.8))
area("Rim_Window", (0.55, 0.25, 1.15), (math.radians(80), 0, math.radians(120)), 0.5, 6.0, (0.6, 0.7, 1.0))
area("Alarm_Red", (-0.35, -0.68, 1.02), (math.radians(-85), 0, math.radians(190)), 0.35, 0.0, (1.0, 0.03, 0.02))
area("Calm_Green", (-0.35, -0.68, 1.02), (math.radians(-85), 0, math.radians(190)), 0.35, 0.0, (0.1, 1.0, 0.45))
# scan beam: narrow cyan spot from the dash camera, swept by keyframed rotation
sb = bpy.data.lights.new("ScanBeam", "SPOT"); sb.energy = 0.0; sb.color = (0.2, 0.95, 1.0); sb.spot_size = math.radians(40); sb.spot_blend = 0.05; sb.shadow_soft_size = 0.001
sbo = bpy.data.objects.new("ScanBeam", sb); uc.objects.link(sbo); sbo.location = (0.0, -0.77, 1.077)
sbo.scale = (1.0, 0.04, 1.0)   # squashed cone -> thin horizontal slit
bpy.ops.wm.save_as_mainfile(filepath=out)
print("SAVED", out)
