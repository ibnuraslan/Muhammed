"""FRANKFURT STAGING HANGAR and AIRFIELD, May 1984 (dramatization). A steel-truss hangar open to the apron, burlap and
crates, a forklift, box trailers, a four-engine military transport with its ramp down. Variants: day / night (floodlit).

Ch1 6A   wrap     two workers wrap a crate in burlap as a forklift passes behind
Ch1 6B   seal     a worker staples the burlap down, then crimps a lead seal on the strap (medium shot)
Ch1 7A   sensor   inside a trailer: the door opens, daylight floods in and a small sensor's lamp comes on
Ch1 7B   apron    sealed trailers on the apron, the transport plane beyond, a tug crossing
Ch1 12A  load     night: crates roll up the ramp into the plane's hold under floodlights
Ch1 12B  slats    night: push in on one slatted crate; through the slats, a typewriter
"""
import math
import numpy as np
import bpy, bmesh
from mathutils import Vector, Matrix
from kit import *
import ph
import twp
import machines as MC
import tw_vehicles as V
import typewriter as T

EXPOSURE = 0.0
DUR = {"wrap": 5.0, "seal": 4.5, "sensor": 4.5, "apron": 5.0, "load": 5.0, "slats": 5.0,
       "customs_torch": 5.0, "customs_clock": 4.5, "dock_xray": 5.0, "dock_seal": 4.5}
VARIANT_FOR = {"load": "night", "slats": "night", "customs_torch": "customs", "customs_clock": "customs", "dock_xray": "dock", "dock_seal": "dock"}
CUSTOMS = Vector((-6.0, 3.0, 0.0))
DOCK = Vector((2.0, -4.0, 0.0))
HX, HY, HZ = 18.0, 14.0, 11.0          # hangar half-length (x), half-depth (y), eave height; doors open on -Y
PLANE = Vector((26.0, -100.0, 0.0))          # far out on the apron: a soft silhouette until the kit has a cargo plane
WORK = Vector((-4.0, 2.0, 0.0))         # the wrapping station
TRAILER = Vector((12.0, -HY - 5.0, 0.0))      # parked on the apron just outside the doors


def forklift(name):
    """The kit's forklift (mast tilts, forks lift via vehicles.part)."""
    import vehicles as _K
    r = _K.make("forklift", color=(0.55, 0.42, 0.12), dirt=0.3); r.name = name
    return r, [r]


def transport(name):
    """Four-engine high-wing military transport, generic: fuselage, T-tail, rear ramp down, engines with props."""
    grey = pbr("PlaneGrey", (0.32, 0.34, 0.33), 0.55, 0.3)
    dark = pbr("PlaneDark", (0.05, 0.05, 0.06), 0.5)
    r = bpy.data.objects.new(name, None); bpy.context.collection.objects.link(r)
    def P(o):
        o.parent = r; return o
    L = 30.0; R = 2.4
    P(cyl("Fuselage", (0, 0, 3.0), R, L, grey, verts=48, rot=(math.radians(90), 0, 0)))
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, radius=R, location=(0, L / 2, 3.0))
    nose = bpy.context.active_object; nose.scale = (1, 1.4, 0.95); nose.data.materials.append(grey); P(nose)
    P(box("Cockpit", (0, L / 2 + 1.8, 4.2), (2.6, 1.0, 0.6), dark, rot=(math.radians(-25), 0, 0)))
    tail = P(box("TailBoom", (0, -L / 2 - 2.5, 4.4), (2.4, 6.0, 1.6), grey, bevel=0.4, rot=(math.radians(-14), 0, 0)))
    P(box("Fin", (0, -L / 2 - 4.5, 8.5), (0.4, 4.0, 7.0), grey, rot=(math.radians(-20), 0, 0)))
    P(box("Stab", (0, -L / 2 - 6.0, 11.8), (13.0, 3.0, 0.3), grey))
    P(box("Wing", (0, 2.0, 5.6), (48.0, 5.0, 0.5), grey, bevel=0.12))
    props = []
    for x in (-15.0, -8.0, 8.0, 15.0):
        P(cyl("Nacelle", (x, 4.0, 4.9), 0.75, 5.0, grey, verts=24, rot=(math.radians(90), 0, 0)))
        hub = bpy.data.objects.new("PropHub", None); bpy.context.collection.objects.link(hub); hub.parent = r; hub.location = (x, 6.6, 4.9)
        for k in range(4):
            b = box("Blade", (0, 0, 1.0), (0.3, 0.06, 2.0), dark, rot=(0, k * math.pi / 2, 0)); b.parent = hub
            b.location = (math.sin(k * math.pi / 2) * 1.0, 0, math.cos(k * math.pi / 2) * 1.0)
        props.append(hub)
    ramp = bpy.data.objects.new("RampHinge", None); bpy.context.collection.objects.link(ramp); ramp.parent = r; ramp.location = (0, -L / 2, 0.9)
    rp = box("Ramp", (0, -2.5, 0), (3.8, 5.0, 0.15), pbr("RampFloor", (0.2, 0.21, 0.2), 0.6, 0.6)); rp.parent = ramp
    ramp.rotation_euler = (math.radians(-11), 0, 0)
    P(box("Hold", (0, -L / 2 + 4, 2.4), (3.9, 9.0, 3.4), pbr("HoldInside", (0.12, 0.13, 0.12), 0.7)))
    P(box("HoldLight", (0, -L / 2 + 6, 4.0), (1.0, 6.0, 0.05), pbr("HoldLamp", (0.9, 0.9, 0.85), 0.3, 0.0, **{'Emission Color': (1, 0.9, 0.75, 1), 'Emission Strength': 0.15})))
    for x in (-2.4, 2.4):
        P(box("GearPod", (x, 1.0, 1.4), (1.2, 7.0, 1.6), grey, bevel=0.3))
        for y in (-1.5, 2.5):
            P(cyl("Wheel", (x, y, 0.6), 0.6, 0.5, V._mats()["tyre"], verts=24, rot=(0, math.radians(90), 0)))
    P(cyl("NoseWheel", (0, L / 2 - 1.0, 0.45), 0.45, 0.4, V._mats()["tyre"], verts=24, rot=(0, math.radians(90), 0)))
    return r, props


def slatted_crate(name, with_tw=True):
    """Open-slat wooden crate (the typewriter inside shows between the slats)."""
    wood = bpy.data.materials.get("SlatWood") or ph.texture("brown_planks_03", scale=2.0, name="SlatWood", tint=(0.9, 0.82, 0.7))
    r = bpy.data.objects.new(name, None); bpy.context.collection.objects.link(r)
    W_, D_, H_ = 0.62, 0.62, 0.42
    for k in range(4):
        z = 0.05 + k * 0.11
        for sy in (-1, 1):
            box("SlatF", (0, sy * D_ / 2, z), (W_, 0.02, 0.06), wood).parent = r
            box("SlatS", (sy * W_ / 2, 0, z), (0.02, D_, 0.06), wood).parent = r
    for sx in (-1, 1):
        for sy in (-1, 1):
            box("Corner", (sx * (W_ / 2 - 0.02), sy * (D_ / 2 - 0.02), H_ / 2), (0.05, 0.05, H_), wood).parent = r
    box("Bottom", (0, 0, 0.01), (W_, D_, 0.02), wood).parent = r
    for k in range(5):
        box("TopSlat", (-W_ / 2 + 0.06 + k * 0.125, 0, H_), (0.08, D_, 0.02), wood).parent = r
    tw = None
    if with_tw:
        tw = T.make(name + "_TW", loc=(0, 0, 0.03), color=(0.2, 0.25, 0.3), mechanism=False, glyphs=True, legends=True, text=" ")
        tw["root"].parent = r
        tw["paper"].hide_render = True
    return r, tw


def build(variant=None):
    c = {"variant": variant}
    night = variant in ("night", "customs")
    customs = variant == "customs"
    rng = np.random.default_rng(12)
    if night:
        world_flat((0.012, 0.016, 0.026), 1.0)
    else:
        w = world_sky(sun_elev_deg=22, sun_rot_deg=200, strength=0.6, tint=(0.82, 0.86, 0.92), air=1.5, aerosol=3.0)
        w.node_tree.nodes["Sky Texture"].sun_disc = False
        sn = bpy.data.lights.new("Sun", 'SUN'); sn.energy = 1.4; sn.angle = math.radians(8); sn.color = (0.95, 0.93, 0.9)      # overcast
        so = bpy.data.objects.new("Sun", sn); bpy.context.collection.objects.link(so); so.rotation_euler = (math.radians(55), 0, math.radians(200))
    # ---------------------------------------------------------------- hangar shell
    floor = ph.texture("hangar_concrete_floor", scale=0.12, name="HangarFloor")
    box("HangarFloor", (0, 0, -0.05), (2 * HX, 2 * HY, 0.1), floor)
    box("Apron", (0, -HY - 40, -0.06), (160, 80, 0.1), ph.texture("concrete_pavement", scale=0.08, name="ApronConc", tint=(0.8, 0.8, 0.78)))
    for k in range(8):
        box("ApronLine", (-30 + k * 9, -HY - 12, 0.0), (5.0, 0.15, 0.01), pbr("Paint", (0.6, 0.52, 0.2), 0.6))
    iron = ph.texture("corrugated_iron_02", scale=0.4, name="Corrugated", tint=(0.75, 0.78, 0.76))
    box("BackWall", (0, HY, HZ / 2), (2 * HX, 0.2, HZ), iron)
    for sx in (-1, 1):
        box("SideWall", (sx * HX, 0, HZ / 2), (0.2, 2 * HY, HZ), iron)
    box("FrontHeader", (0, -HY, HZ + 1.2), (2 * HX, 0.3, 2.4), iron)
    steel = pbr("Truss", (0.3, 0.32, 0.31), 0.5, 0.7)
    for k in range(7):
        x = -HX + 3 + k * 5.0
        for sx in (-1, 1):
            pass
        box("TrussTop", (x, 0, HZ + 1.6), (0.2, 2 * HY, 0.25), steel)
        box("TrussBot", (x, 0, HZ), (0.2, 2 * HY, 0.2), steel)
        for j in range(10):
            yy = -HY + 1.4 + j * 2.8
            box("Web", (x, yy, HZ + 0.8), (0.08, 0.08, 1.9), steel, rot=(math.radians(35 if j % 2 else -35), 0, 0))
        for yy in (-HY + 0.2, HY - 0.2):
            box("Column", (x, yy, HZ / 2), (0.35, 0.35, HZ), steel)
    box("Roof", (0, 0, HZ + 1.8), (2 * HX, 2 * HY, 0.15), iron)
    for k in range(5):
        box("Skylight", (-HX + 5 + k * 7.0, 0, HZ + 1.86), (2.0, 2 * HY - 2, 0.02), glass("SkyGlass", (0.85, 0.88, 0.9), 0.2))
        if not night:
            sk = area_light((-HX + 5 + k * 7.0, 0, HZ + 1.7), (0, 0, 0), 2.0, 900, (0.88, 0.92, 1.0)); sk.data.shape = 'RECTANGLE'
            sk.data.size = 2.0; sk.data.size_y = 2 * HY - 2; sk.visible_camera = False
    for x in np.arange(-HX + 4, HX, 6.0):
        for y in (-6.0, 4.0):
            ph.model("hanging_industrial_lamp", loc=(x, y, HZ - 0.1))
            if customs and not (x < -6 and y > 0):
                continue                                # a Soviet customs shed at night: one lamp left burning
            pl = bpy.data.lights.new("HangLamp", 'SPOT'); pl.energy = (250 if customs else 1200) if night else 1400; pl.spot_size = math.radians(110); pl.spot_blend = 0.8
            pl.color = (1.0, 0.85, 0.65)
            po = bpy.data.objects.new("HangLamp", pl); bpy.context.collection.objects.link(po); po.location = (x, y, HZ - 1.4)
    if not night:
        pt = bpy.data.lights.new("DoorPortal", 'AREA'); pt.shape = 'RECTANGLE'; pt.size = 2 * HX; pt.size_y = HZ; pt.cycles.is_portal = True
        po = bpy.data.objects.new("DoorPortal", pt); bpy.context.collection.objects.link(po); po.location = (0, -HY, HZ / 2); po.rotation_euler = (math.radians(-90), 0, 0)
    haze((0, 0, HZ / 2), (2 * HX, 2 * HY, HZ), density=0.006 if not night else 0.01, color=(0.8, 0.83, 0.88), anis=0.5)
    # ---------------------------------------------------------------- stock: shelving, crates, burlap rolls, pallets
    for k in range(5):
        ph.model("steel_frame_shelves_02", loc=(-HX + 2 + k * 0.62, HY - 0.6, 0), rot_z=math.pi, scale=1.0)
    for k in range(14):
        x = -14 + (k % 7) * 1.1; y = 9.0 + (k // 7) * 1.0
        o = MC.burlap_crate(f"Stock{k}"); o.location = (x + rng.uniform(-0.1, 0.1), y, 0.43); o.rotation_euler = (0, 0, rng.uniform(-0.08, 0.08))
        if k % 3 == 0:
            o2 = MC.burlap_crate(f"StockT{k}"); o2.location = (x, y, 1.29)
    for k in range(6):
        ph.model("wooden_crate_02" if k % 2 else "wooden_crate_01", loc=(6 + (k % 3) * 1.0, 10 + (k // 3) * 0.9, 0), rot_z=rng.uniform(-0.2, 0.2))
    hes = bpy.data.materials.get("Burlap") or ph.texture("hessian_230", scale=2.0, name="Burlap", tint=(0.78, 0.66, 0.5))
    for k in range(3):
        cyl("BurlapRoll", (WORK.x - 2.2, WORK.y + 0.8 + k * 0.42, 0.2), 0.2, 1.4, hes, verts=24, rot=(0, math.radians(90), 0))
    ph.model("metal_tool_chest", loc=(WORK.x + 1.8, WORK.y + 1.0, 0), rot_z=math.pi)
    ph.model("clipboard", loc=(WORK.x + 1.75, WORK.y + 0.95, 0.66))
    # ---------------------------------------------------------------- the wrapping station: one crate being wrapped and sealed
    wood = ph.texture("brown_planks_03", scale=1.5, name="CrateWood")
    crate = box("WrapCrate", (WORK.x, WORK.y, 0.48), (1.0, 0.8, 0.9), wood, bevel=0.01)
    hes = bpy.data.materials.get("BurlapBig") or ph.texture("hessian_230", scale=0.9, name="BurlapBig", tint=(0.8, 0.68, 0.5))
    wrap = box("Wrapping", (0, 0, 0), (1.03, 0.83, 0.93), hes, bevel=0.03)
    sub = wrap.modifiers.new("sub", 'SUBSURF'); sub.levels = 3; sub.render_levels = 3; sub.subdivision_type = 'SIMPLE'
    dsp = wrap.modifiers.new("folds", 'DISPLACE'); tx = bpy.data.textures.new("Folds", 'CLOUDS'); tx.noise_scale = 0.18
    dsp.texture = tx; dsp.strength = 0.012; dsp.mid_level = 0.5
    wrap.data.transform(Matrix.Translation((0, 0, 0.465)))                         # origin at the bottom: scale z = how far it is wrapped
    wrap.location = (WORK.x, WORK.y, 0.015)
    c["wrap"] = wrap
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=24, y_subdivisions=24, size=1)
    sheet = bpy.context.active_object; sheet.name = "BurlapSheet"; sheet.scale = (1.1, 1.0, 1); bpy.ops.object.transform_apply(scale=True)
    sheet.rotation_mode = 'XYZ'; sheet.data.materials.append(hes)
    sw = sheet.modifiers.new("drape", 'WAVE'); sw.use_x = True; sw.use_y = True; sw.height = 0.03; sw.width = 0.25; sw.speed = 0.01
    c["sheet"] = sheet
    strap_m = pbr("StrapW", (0.32, 0.27, 0.2), 0.8)
    rope = bpy.data.materials.get("Rope") or ph.texture("hessian_380", scale=6.0, name="Rope", tint=(0.55, 0.45, 0.32))
    strap = cyl("WrapTwine", (WORK.x, WORK.y - 0.43, 0.48), 0.008, 0.95, rope, verts=8); c["strap"] = strap
    cyl("WrapTwineTop", (WORK.x, WORK.y, 0.955), 0.008, 0.86, rope, verts=8, rot=(math.radians(90), 0, 0))
    seal = join([cyl("SealWireH", (0, 0, 0), 0.002, 0.1, pbr("SealWireMH", (0.6, 0.6, 0.62), 0.3, 1.0), verts=6),
                 cyl("SealLeadH", (0, 0, -0.06), 0.013, 0.012, pbr("LeadH", (0.42, 0.43, 0.45), 0.5, 0.8), verts=16, rot=(math.radians(90), 0, 0))], "SealH")
    c["seal"] = seal
    st, _ = ph.model("vintage_stapler"); c["stapler"] = st
    sm = pbr("StapleH", (0.7, 0.7, 0.72), 0.25, 1.0)
    c["staples"] = [box("StapleH", (0, 0, 0), (0.014, 0.002, 0.002), sm) for k in range(8)]
    # forklift, trailers, tug
    fk, fw = forklift("Forklift"); c["fork"] = fk; c["fork_w"] = fw
    pal = box("ForkLoad", (0, 0, 0), (1.0, 0.8, 0.9), hes, bevel=0.03); c["fork_load"] = pal
    c["trailers"] = []
    for k, (p, rz) in enumerate(((TRAILER, math.pi / 2), (Vector((-10, -HY - 10, 0)), 0.2), (Vector((-2, -HY - 13, 0)), 0.1), (Vector((6, -HY - 11, 0)), -0.05))):
        if k > 0 and night:
            continue                                   # the apron trailers are a daytime set-up
        tr, wh, doors = V.truck(f"Trailer{k}", cab_color=(0.25, 0.3, 0.26), trailer_color=(0.62, 0.62, 0.6), boxy=(k == 0))
        tr.location = p; tr.rotation_euler = (0, 0, rz)
        c["trailers"].append((tr, doors))
    c["sensor_tr"] = c["trailers"][0]
    # the light sensor inside trailer 0 (local coords): a small grey box with a lamp, wired to the wall
    tr0 = c["trailers"][0][0]
    sens = box("Sensor", (-4.3, -1.15, 3.2), (0.1, 0.05, 0.08), pbr("SensorGrey", (0.4, 0.42, 0.4), 0.4), bevel=0.005); sens.parent = tr0
    lamp = pbr("SensorLamp", (0.3, 0.04, 0.03), 0.3, 0.0, **{'Emission Color': (1.0, 0.15, 0.05, 1), 'Emission Strength': 0.0})
    sl = cyl("SensorLED", (-4.3, -1.12, 3.2), 0.008, 0.008, lamp, verts=12, rot=(math.radians(90), 0, 0)); sl.parent = tr0
    d = lamp.node_tree.nodes["Principled BSDF"].inputs['Emission Strength'].driver_add("default_value").driver
    d.type = 'SCRIPTED'; d.expression = "12 * (1 if frame > 40 and (frame // 8) % 2 == 0 else 0)"
    cyl("SensorWire", (-3.0, -1.17, 3.2), 0.004, 2.6, pbr("WireB", (0.05, 0.05, 0.05), 0.5), verts=6, rot=(0, math.radians(90), 0)).parent = tr0
    for k in range(4):
        o = MC.burlap_crate(f"TrLoad{k}", tag=False); o.parent = tr0; o.location = (-2.0 + (k // 2) * 1.0, -0.55 + (k % 2) * 1.1, 1.38)
    if not night:
        haze((0, -HY - 50, 10), (160, 90, 20), density=0.0025, color=(0.82, 0.86, 0.92), anis=0.3)
    pl, props = transport("Transport"); pl.location = PLANE; pl.rotation_euler = (0, 0, math.pi); c["plane"] = pl; c["props"] = props
    # night: floodlight masts on the apron, crates on a roller conveyor into the hold
    c["roll_crates"] = []
    if night:
        for x in (-14.0, 22.0):
            cyl("FloodMast", (x, PLANE.y + 22, 7.0), 0.15, 14, steel, verts=12)
            fl = bpy.data.lights.new("Flood", 'SPOT'); fl.energy = 25000; fl.spot_size = math.radians(55); fl.spot_blend = 0.4; fl.color = (1.0, 0.82, 0.6)
            fo = bpy.data.objects.new("Flood", fl); bpy.context.collection.objects.link(fo); fo.location = (x, PLANE.y + 21.2, 13.2); point_at(fo, (PLANE.x, PLANE.y + 16, 0.5))
            box("FloodHead", (x, PLANE.y + 22, 14.1), (1.2, 0.4, 0.8), pbr("FloodHousing", (0.1, 0.1, 0.1), 0.4))
        haze((PLANE.x, PLANE.y + 15, 6), (60, 50, 12), density=0.004, color=(0.8, 0.85, 0.95), anis=0.6)
        ramp_end = PLANE + Vector((0, 15 + 5, 0))
        for k in range(10):
            cyl("Roller", (PLANE.x, PLANE.y + 22 - k * 0.5, 0.42), 0.04, 0.9, steel, verts=12, rot=(0, math.radians(90), 0))
        box("ConveyorRail", (PLANE.x - 0.47, PLANE.y + 19.8, 0.4), (0.04, 5.2, 0.12), steel); box("ConveyorRail", (PLANE.x + 0.47, PLANE.y + 19.8, 0.4), (0.04, 5.2, 0.12), steel)
        for k in range(4):
            o = MC.burlap_crate(f"Roll{k}", size=(0.8, 0.7, 0.7), tag=False); c["roll_crates"].append(o)
        sc, stw = slatted_crate("SlatCrate"); sc.location = (PLANE.x - 2.4, PLANE.y + 23.5, 0.0); sc.rotation_euler = (0, 0, 0.2)
        c["slat"] = sc
        ss = bpy.data.lights.new("SlatSun", 'SPOT'); ss.energy = 350; ss.spot_size = math.radians(30); ss.spot_blend = 0.2; ss.shadow_soft_size = 0.02
        ss.color = (1.0, 0.82, 0.6)
        so_ = bpy.data.objects.new("SlatSun", ss); bpy.context.collection.objects.link(so_)
        so_.location = Vector(sc.location) + Vector((-0.9, 0.6, 1.8)); point_at(so_, Vector(sc.location) + Vector((0, 0, 0.12)))   # light raking through the slats
        for k in range(5):
            o = MC.burlap_crate(f"Wait{k}", tag=False); o.location = (PLANE.x - 3.6 + (k % 3) * 1.05, PLANE.y + 25 + (k // 3) * 0.9, 0.43)
    if customs:
        sc, stw = slatted_crate("CustomsCrate"); sc.location = CUSTOMS; sc.rotation_euler = (0, 0, 0.3); c["ccrate"] = sc
        lid = [o for o in sc.children if o.name.startswith("TopSlat")]
        piv = bpy.data.objects.new("LidHinge", None); bpy.context.collection.objects.link(piv); piv.parent = sc; piv.location = (0, 0.31, 0.42)
        for o in lid:
            mw = o.matrix_world.copy(); o.parent = piv; o.matrix_world = mw
        c["clid"] = piv
        box("CustomsTable", (CUSTOMS.x - 1.6, CUSTOMS.y + 0.6, 0.4), (1.4, 0.7, 0.05), ph.texture("dark_wood", scale=1.0, name="CTable"))
        ph.model("clipboard", loc=(CUSTOMS.x - 1.7, CUSTOMS.y + 0.6, 0.43))
        # a wall clock on the back wall above the crate: the hands are separate objects that turn (frame-driven by bake)
        ck, _ = ph.model("wall_clock", loc=(CUSTOMS.x + 0.5, HY - 0.12, 3.0), rot_z=math.pi, scale=2.2)
        hm = pbr("ClockHand", (0.02, 0.02, 0.02), 0.4)
        c["hands"] = []
        for k, (L_, w_) in enumerate(((0.22, 0.016), (0.3, 0.01))):
            hp = bpy.data.objects.new("HandPivot", None); bpy.context.collection.objects.link(hp); hp.location = (CUSTOMS.x + 0.5, HY - 0.25, 3.0)
            hb = box("Hand", (0, 0, L_ / 2), (w_, 0.004, L_), hm); hb.parent = hp
            c["hands"].append(hp)
        for k in range(6):
            o = MC.burlap_crate(f"CStock{k}", tag=False); o.location = (CUSTOMS.x + 2.0 + (k % 3) * 1.0, CUSTOMS.y + 1.5 + (k // 3) * 0.9, 0.43)
        torch, _ = ph.model("vintage_flashlight"); c["torch"] = torch
        sp = bpy.data.lights.new("TorchC", 'SPOT'); sp.energy = 600; sp.spot_size = math.radians(26); sp.spot_blend = 0.3; sp.color = (1.0, 0.9, 0.75)
        so = bpy.data.objects.new("TorchC", sp); bpy.context.collection.objects.link(so); c["beam"] = so
    if variant == "dock":
        # an X-ray inspection tunnel: steel housing, lead-strip curtains, a roller bed, an operator console with a monitor
        st_m = pbr("TunnelSteel", (0.55, 0.58, 0.56), 0.4, 0.5)
        box("Tunnel", (DOCK.x, DOCK.y, 1.15), (2.2, 1.4, 1.5), st_m, bevel=0.03)
        box("TunnelHole", (DOCK.x, DOCK.y, 0.95), (2.25, 1.0, 0.9), pbr("TunnelDark", (0.02, 0.02, 0.02), 0.6))
        warn = pbr("XLamp", (0.4, 0.15, 0.02), 0.3, 0.0, **{'Emission Color': (1.0, 0.55, 0.1, 1), 'Emission Strength': 0.0})
        d = warn.node_tree.nodes["Principled BSDF"].inputs['Emission Strength'].driver_add("default_value").driver
        d.type = 'SCRIPTED'; d.expression = "15 * (1 if (frame % 30) < 15 else 0.1)"
        cyl("XWarn", (DOCK.x + 0.8, DOCK.y, 1.95), 0.07, 0.12, warn, verts=16)
        for sx in (-1, 1):
            for k in range(8):
                box("LeadStrip", (DOCK.x + sx * 1.12, DOCK.y - 0.44 + k * 0.125, 0.95), (0.01, 0.11, 0.88), pbr("Lead", (0.2, 0.2, 0.21), 0.6, 0.3))
        for k in range(18):
            cyl("BedRoller", (DOCK.x - 4.5 + k * 0.5, DOCK.y, 0.48), 0.04, 1.0, st_m, verts=12, rot=(math.radians(90), 0, 0))
        for sy in (-1, 1):
            box("BedRail", (DOCK.x, DOCK.y + sy * 0.52, 0.45), (9.0, 0.05, 0.12), st_m)
        import machines as _MC
        _MC.terminal("XrayConsole", (DOCK.x + 0.4, DOCK.y - 1.5, 0.75), math.pi)
        box("ConsoleDesk", (DOCK.x + 0.4, DOCK.y - 1.55, 0.37), (1.0, 0.6, 0.74), st_m)
        c["dock_crates"] = [MC.burlap_crate(f"DockCrate{k}", size=(0.8, 0.7, 0.6)) for k in range(4)]
    # people
    P = {}
    P["wA"] = twp.person("HWorkA", 1.0, 33, "male_worksuit01", "short01", hv=0.25, cval=0.5, hue=0.58, sat=0.2)
    P["wB"] = twp.person("HWorkB", 1.0, 50, "male_worksuit01", "short04", hv=0.45, cval=0.45, hue=0.1, sat=0.2)
    P["driver"] = twp.person("Driver", 1.0, 40, "male_worksuit01", "short02", hv=0.3, cval=0.42, hue=0.58, sat=0.15)
    P["load1"] = twp.person("Loader1", 1.0, 26, "male_worksuit01", "short03", hv=0.2, cval=0.5, hue=0.3, sat=0.15)
    P["insp"] = twp.person("Inspector", 1.0, 46, "male_casualsuit03", "short02", hv=0.4, cval=0.55, hue=0.1, sat=0.2)
    P["guard"] = twp.person("Guard", 1.0, 35, "male_worksuit01", "short01", hv=0.25, cval=0.45, hue=0.3, sat=0.25)
    c["P"] = P
    animate(c, 0.0, {"customs": "customs_torch", "dock": "dock_xray"}.get(variant, "wrap"))
    return c


# ============================================================================ animation
def animate(c, sec, shot):
    from human import reach, fingers_curl
    P = c["P"]
    used = {"wrap": ["wA", "wB", "driver"], "seal": ["wA"], "sensor": ["wB"], "apron": ["driver"], "load": ["load1", "wA"], "slats": [],
            "customs_torch": ["guard"], "customs_clock": [], "dock_xray": ["insp", "wA"], "dock_seal": ["insp"]}[shot]
    for k, h in P.items():
        twp.hide(twp.person_objs(h), k not in used)
    if shot.startswith("customs"):
        for k, hp in enumerate(c["hands"]):                 # hour hand from 2:55, minute hand sweeping (time-lapse feel)
            mins = 55 + sec * 6.0
            hp.rotation_euler = (0, math.radians(-(mins * 6 if k else (2 + mins / 60) * 30)), 0)
        c["clid"].rotation_euler = (math.radians(-8 * ease(min(1.0, sec / 3.0))) if shot == "customs_clock" else math.radians(-8), 0, 0)
        g = P["guard"]
        twp.walk(g, (CUSTOMS.x + 4.0, CUSTOMS.y - 4.0), (CUSTOMS.x + 1.0, CUSTOMS.y - 1.0), sec, speed=0.7)
        aim = c["ccrate"].location + Vector((0, 0, 0.3))
        sh = g.bone_head("upperarm01.R")
        hand_p = sh + (aim - sh).normalized() * 0.5 + Vector((0, 0, -0.05))
        reach(g, "R", hand_p, Vector((0.6, -0.4, -0.6)), aim - sh)
        fingers_curl(g, 60, thumb=30)
        dd = (aim - hand_p).normalized()
        c["torch"].location = hand_p + dd * 0.05; c["torch"].rotation_mode = 'QUATERNION'; c["torch"].rotation_quaternion = dd.to_track_quat('Y', 'Z')
        c["beam"].location = hand_p + dd * 0.18; c["beam"].rotation_mode = 'QUATERNION'; c["beam"].rotation_quaternion = (-dd).to_track_quat('Z', 'Y')
        c["beam"].data.energy = 600 if shot == "customs_torch" else 0
        twp.hide(twp.person_objs(g) + [c["torch"]] + list(c["torch"].children_recursive), shot != "customs_torch")
    if shot.startswith("dock"):
        for k, o in enumerate(c["dock_crates"]):
            x = DOCK.x - 4.2 + ((sec * 0.35 + k * 2.2) % 8.4)
            o.location = (x, DOCK.y, 0.82)
        ins = P["insp"]
        if shot == "dock_xray":
            twp.stand(ins, (DOCK.x + 0.4, DOCK.y - 2.15, 0), math.pi)
            ins.rot("head", (1, 0, 0), 12)
            twp.stand(P["wA"], (DOCK.x - 3.2, DOCK.y - 0.95, 0), math.pi)
            reach(P["wA"], "R", Vector((DOCK.x - 3.2, DOCK.y - 0.45, 1.05)), Vector((0.5, -0.4, -0.7)), Vector((0, 1, 0)))
        else:
            cr = c["dock_crates"][0]; cr.location = (DOCK.x + 3.0, DOCK.y, 0.82)
            twp.stand(ins, (DOCK.x + 3.0, DOCK.y - 0.95, 0), math.pi)
            tag = Vector((DOCK.x + 3.0, DOCK.y - 0.36, 0.95))
            reach(ins, "R", tag + Vector((0.05, -0.08, 0.02)), Vector((-0.5, -0.4, -0.7)), Vector((0, 1, 0)))
            reach(ins, "L", tag + Vector((-0.25, -0.2, -0.05 + 0.03 * math.sin(sec))), Vector((0.5, -0.4, -0.7)), Vector((0, 1, 0.3)))
            ins.rot("head", (1, 0, 0), 16)
        fingers_curl(ins, 40, thumb=20)
    for hub in c["props"]:
        hub.rotation_euler = (0, sec * (14.0 if shot in ("apron", "load") else 0.0), 0)
    wrap, sheet = c["wrap"], c["sheet"]
    fk = c["fork"]
    st = c["stapler"]; twp.hide([st] + list(st.children_recursive), shot != "seal")
    # forklift: crosses behind the station (wrap), or carries a crate down the apron (apron)
    if shot == "wrap":
        x = -14.0 + 2.2 * sec
        fk.location = (x, 7.0, 0); fk.rotation_euler = (0, 0, 0); V.roll(c["fork_w"], 2.2 * sec, 0.3)
        c["fork_load"].location = Vector((x + 1.4, 7.0, 0.6)); twp.hide([c["fork_load"]], False)
        twp.stand(P["driver"], (x - 0.25, 7.0, 0.85), math.pi / 2)
        from human import pose_sit
    elif shot == "apron":
        x = -20.0 + 2.6 * sec
        fk.location = (x, -HY - 6.0, 0); fk.rotation_euler = (0, 0, 0); V.roll(c["fork_w"], 2.6 * sec, 0.3)
        c["fork_load"].location = Vector((x + 1.4, -HY - 6.0, 0.6)); twp.hide([c["fork_load"]], False)
        twp.stand(P["driver"], (x - 0.25, -HY - 6.0, 0.85), math.pi / 2)
    else:
        fk.location = (30, 30, -20); twp.hide([c["fork_load"]], True)
    # wrapping station
    if shot == "wrap":
        k = ease(min(1.0, sec / 4.2))
        wrap.scale = (1, 1, max(0.02, 0.35 + 0.65 * k))
        a, b = P["wA"], P["wB"]
        twp.stand(a, (WORK.x - 0.2, WORK.y - 0.98, 0), math.pi)
        twp.stand(b, (WORK.x + 0.95, WORK.y + 0.05, 0), math.pi / 2 + math.pi)       # faces -X, the crate side
        top = 0.015 + 0.93 * wrap.scale.z
        sheet.location = (WORK.x, WORK.y - 0.46, top + 0.3); sheet.rotation_euler = (math.radians(75), 0, 0)
        for sd, dx in (("L", 0.35), ("R", -0.35)):
            reach(a, sd, Vector((WORK.x + dx, WORK.y - 0.5, top + 0.25)), Vector((dx, -0.6, -0.6)), Vector((0, 1, 0)))
        reach(b, "R", Vector((WORK.x + 0.55, WORK.y - 0.2, top - 0.05)), Vector((0.3, -0.6, -0.6)), Vector((-1, 0, 0)))
        reach(b, "L", Vector((WORK.x + 0.55, WORK.y + 0.25, top - 0.05)), Vector((0.3, 0.6, -0.6)), Vector((-1, 0, 0)))
        fingers_curl(a, 50, thumb=25); fingers_curl(b, 40, thumb=20)
        for s_ in c["staples"]:
            s_.hide_render = True
        c["seal"].location = (0, 0, -30)
    else:
        wrap.scale = (1, 1, 1); sheet.location = (0, 0, -30)
    if shot == "seal":
        a = P["wA"]
        twp.stand(a, (WORK.x - 0.15, WORK.y - 0.95, 0), math.pi)
        n = int(sec / 0.5)
        for i, s_ in enumerate(c["staples"]):
            s_.location = (WORK.x - 0.4 + i * 0.11, WORK.y - 0.428, 0.88); s_.hide_render = i >= min(n, 6)
        if sec < 3.0:
            xs = WORK.x - 0.4 + min(n, 5) * 0.11
            lift = 0.04 * max(0.0, math.sin(math.pi * ((sec % 0.5) / 0.5)))
            sp = Vector((xs, WORK.y - 0.5, 0.88 + lift))
            st.location = sp; st.rotation_euler = (math.radians(90), 0, math.pi / 2)
            reach(a, "R", sp + Vector((0.0, -0.08, 0.02)), Vector((-0.8, -0.3, -0.6)), Vector((0, 1, 0)))
            reach(a, "L", Vector((xs - 0.25, WORK.y - 0.45, 0.82)), Vector((0.8, -0.3, -0.6)), Vector((0, 1, 0)))
            c["seal"].location = (0, 0, -30)
        else:
            st.location = (WORK.x + 0.5, WORK.y - 0.2, 0.93); st.rotation_euler = (0, 0, 0.4)
            crimp = max(0.0, math.sin(math.pi * min(1.0, (sec - 3.3) / 0.6))) if sec > 3.3 else 0.0
            sp = Vector((WORK.x, WORK.y - 0.45, 0.66))                       # the lead seal hangs off the twine
            c["seal"].location = sp
            reach(a, "R", sp + Vector((0.07, -0.08, 0.02 - 0.015 * crimp)), Vector((-0.8, -0.3, -0.6)), Vector((-0.3, 1, 0)))
            reach(a, "L", sp + Vector((-0.08, -0.08, 0.02)), Vector((0.8, -0.3, -0.6)), Vector((0.3, 1, 0)))
        fingers_curl(a, 50, thumb=25)
        a.rot("head", (1, 0, 0), -10)
    # the trailer: doors swing open for the sensor shot, closed otherwise
    tr0, doors = c["sensor_tr"]
    op = ease(min(1.0, max(0.0, (sec - 1.0) / 1.3))) if shot == "sensor" else 0.0
    for d_, sy in zip(doors, (-1, 1)):
        d_.rotation_euler = (0, 0, -sy * math.radians(110) * op)
    if shot == "sensor":
        b = P["wB"]
        tw_ = tr0.matrix_world
        door_pt = tw_ @ Vector((-4.77 - 0.9, -0.6, 0.0))
        twp.stand(b, (door_pt.x, door_pt.y, 0.0), tr0.rotation_euler.z - math.pi / 2)
    # night loading: crates roll up the conveyor and the ramp into the hold
    if shot == "load":
        for k, o in enumerate(c["roll_crates"]):
            s_ = (sec * 0.22 + k * 0.25) % 1.0
            y = PLANE.y + 23.0 - 9.0 * s_
            z = 0.8 if y > PLANE.y + 17.5 else 0.8 + (PLANE.y + 17.5 - y) * 0.19
            o.location = (PLANE.x, y, min(z, 1.6))
        a, b = P["load1"], P["wA"]
        twp.stand(a, (PLANE.x + 0.9, PLANE.y + 21.0 - 0.3 * sec, 0), math.radians(160))
        twp.stand(b, (PLANE.x - 1.0, PLANE.y + 19.5, 0), math.radians(-150))
        reach(a, "L", c["roll_crates"][1].location + Vector((0.45, 0.0, 0.1)), Vector((0.6, 0, -0.7)), Vector((-1, 0, 0)))
    bpy.context.view_layer.update()


def anim(shot):
    return lambda c, t: animate(c, t * DUR[shot], shot)


def cam_wrap(c, t):
    e = ease(t)
    return (WORK + Vector((-3.2, -3.4, 1.8)).lerp(Vector((-2.8, -3.0, 1.75)), e), WORK + Vector((0.2, 0.3, 0.9)), 28)


def cam_seal(c, t):
    e = ease(t)
    return (WORK + Vector((2.6, -3.3, 1.8)).lerp(Vector((2.35, -3.0, 1.75)), e), WORK + Vector((-0.2, -0.55, 1.0)), 28)


def cam_sensor(c, t):
    tr0 = c["sensor_tr"][0]; M = tr0.matrix_world; e = ease(t)
    return ((M @ Vector((2.2, 0.55, 2.5))).lerp(M @ Vector((1.6, 0.5, 2.45)), e), M @ Vector((-4.7, -0.35, 2.4)), 22)


def cam_apron(c, t):
    e = ease(t)
    return (Vector((-24.0, -HY - 2.0, 2.0)).lerp(Vector((-22.0, -HY - 2.6, 2.1)), e), Vector((0.0, -HY - 18.0, 1.6)), 30)


def cam_load(c, t):
    e = ease(t)
    return (Vector((PLANE.x + 2.2, PLANE.y + 24.5, 1.05)).lerp(Vector((PLANE.x + 1.8, PLANE.y + 23.2, 1.0)), e), Vector((PLANE.x - 0.1, PLANE.y + 15.8, 1.5)), 32)


def cam_slats(c, t):
    e = ease(t); s = c["slat"].location
    return (s + Vector((0.6, -1.6, 1.2)).lerp(Vector((0.18, -0.6, 0.66)), e), s + Vector((0.0, -0.03, 0.14)), 45)


def cam_customs_torch(c, t):
    e = ease(t)
    return (CUSTOMS + Vector((-3.5, -4.2, 1.6)).lerp(Vector((-3.0, -3.7, 1.55)), e), CUSTOMS + Vector((1.0, 0.0, 0.6)), 28)


def cam_customs_clock(c, t):
    e = ease(t)
    return (CUSTOMS + Vector((-0.6, -2.8, 0.9)).lerp(Vector((-0.4, -2.3, 1.1)), e), CUSTOMS + Vector((0.3, 3.0, 2.1)), 26)


def cam_dock_xray(c, t):
    e = ease(t)
    return (DOCK + Vector((-4.2, -4.0, 2.0)).lerp(Vector((-3.6, -3.4, 1.9)), e), DOCK + Vector((-0.5, 0.0, 0.9)), 30)


def cam_dock_seal(c, t):
    e = ease(t); p = DOCK + Vector((3.0, -0.4, 0.95))
    return (p + Vector((1.4, -1.6, 0.6)).lerp(Vector((1.15, -1.3, 0.5)), e), p, 35)


MOVES = {
    "customs_torch": dict(kind="anim", dof=None, cam=cam_customs_torch, anim=anim("customs_torch")),
    "customs_clock": dict(kind="anim", dof=3.0, cam=cam_customs_clock, focus=lambda c, t: CUSTOMS + Vector((0, 0, 0.4)), anim=anim("customs_clock")),
    "dock_xray": dict(kind="anim", dof=None, cam=cam_dock_xray, anim=anim("dock_xray")),
    "dock_seal": dict(kind="anim", dof=2.0, cam=cam_dock_seal, focus=lambda c, t: DOCK + Vector((3.0, -0.38, 0.95)), anim=anim("dock_seal")),
    "wrap": dict(kind="anim", dof=3.5, cam=cam_wrap, focus=lambda c, t: WORK + Vector((0, -0.4, 0.9)), anim=anim("wrap")),
    "seal": dict(kind="anim", dof=2.6, cam=cam_seal, focus=lambda c, t: WORK + Vector((0, -0.45, 0.8)), anim=anim("seal")),
    "sensor": dict(kind="anim", dof=None, cam=cam_sensor, anim=anim("sensor")),
    "apron": dict(kind="anim", dof=None, cam=cam_apron, anim=anim("apron")),
    "load": dict(kind="anim", dof=None, cam=cam_load, anim=anim("load")),
    "slats": dict(kind="anim", dof=1.6, cam=cam_slats, focus=lambda c, t: c["slat"].location + Vector((0, 0, 0.15)), anim=anim("slats")),
}
