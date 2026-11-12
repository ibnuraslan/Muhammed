"""INTRO SET 2 / THE BANK EXTERIOR, Moscow, August 1995, dusk (dramatization).
A four-storey stucco building on a Moscow street (Poly Haven modular facade kit, retinted ochre), granite steps to the
entrance, lamps coming on. Militia Ladas pull up at the kerb, blue beacons turning (2A). On the steps an officer sits,
unwell; a colleague crouches and hands him a glass of water (2B)."""
import os, math
import numpy as np
import bpy
from mathutils import Vector, Matrix
from kit import *
from human import Human, add_asset, reset_pose, fingers_curl, pose_walk, pose_sit, _world_verts, reach
import ph
from pbkit import soviet_car, masonry_facade, joinm, precip_curtains, leaves
import pbpeople as PP
from sc_bankoffice import person, stand, nod, look, _fwd, retint

EXPOSURE = 0.9
BOUNCES = 6
DUR = {"pullup": 4.8, "steps": 4.8}
FRONT_Y = 0.0                # facade plane; the street is toward -Y
KERB_Y = -5.0                # pavement 5 m deep
ROAD_W = 12.0
DOOR2_X = 15.0               # a door bay of the ochre neighbour (Ch2 9A)
STEP_N, STEP_H, STEP_D = 4, 0.16, 0.36
rng = np.random.default_rng(8)


# ============================================================================ facade from the modular kit
def kit_facade(x0, bays, top_bay="centered_large", door_bays=(), tint=(0.66, 0.68, 0.7)):
    """Assemble ground floor + two floors + top floor + crown, `bays` x 3 m, starting at x0, facing -Y."""
    root, ms = ph.model("modular_urban_apartments_facade")
    by = {}
    for o in ms:
        by.setdefault(o.name.split(".")[0], o)
    for o in ms:                                    # the kit's meshes are shared: tint per object, not per mesh
        for slot in getattr(o, "material_slots", []):
            m = slot.material; slot.link = 'OBJECT'; slot.material = m
    retint(ms, tint)
    out = []

    def put(name, bay_x0_src, z_src, x, z):
        o = by.get(name)
        if o is None:
            return
        n = o.copy(); bpy.context.collection.objects.link(n); n.parent = None
        n.matrix_world = Matrix.Translation((x - bay_x0_src, 0, z - z_src)) @ o.matrix_world
        out.append(n)

    SRC = {"standard": -3.0, "centered_large": 8.0, "centered_small": 12.0, "centered_double": 16.0, "offset_small": 20.0}
    for i in range(bays):
        x = x0 + i * 3.0
        kind = "centered_large" if i in door_bays else top_bay
        sx = SRC[kind]
        # ground floor: tall glazed doors (shopfront-like banking hall), the entrance bay included
        put(f"wall_door_{kind}_01", sx, 0.0, x, 0.0); put(f"door_{kind}_01", sx, 0.0, x, 0.0)
        put("cornice_standard_standard_01", -3.0, 3.4, x, 3.0)
        for f, (zsrc, suf) in enumerate(((4.0, "01"), (8.0, "02"), (8.0, "02"), (12.0, "03"))):
            z = 3.2 + f * 3.0
            put(f"wall_window_{top_bay}_{suf}", SRC[top_bay], zsrc, x, z); put(f"window_{top_bay}_{suf}", SRC[top_bay], zsrc, x, z)
        put("crown_standard_standard_01", -3.0, 4.0, x, 3.2 + 4 * 3.0)
        put("base_standard_01", -3.0, -2.0, x, -0.55)
    for i in range(bays + 1):
        x = x0 + i * 3.0
        for f in range(5):
            put("wall_pier_standard_01", -22.12 - 0.0, 0.0, x - 0.125 + 0.0, f * 3.0 + (0.2 if f else 0.0))
    bpy.data.objects.remove(root, do_unlink=True)
    for o in ms:
        bpy.data.objects.remove(o, do_unlink=True)
    # infill behind the openings (the building has a body)
    box("BankBody", (x0 + bays * 1.5, 6.6, 8.0), (bays * 3.0, 12.0, 16.0), pbr("Interior", (0.05, 0.045, 0.04), 0.9))
    return out


# ============================================================================ build
def build(variant=None):
    variant = variant or "dusk"
    c = {"variant": variant}
    if variant == "dusk":
        world_sky(sun_elev_deg=-4.0, sun_rot_deg=250, strength=2.6, tint=(0.62, 0.74, 1.0))      # blue hour, just after sunset
        bpy.context.scene.view_settings.exposure = 1.6                                          # lifted: readable blue hour
    elif variant == "summer":
        world_sky(sun_elev_deg=38, sun_rot_deg=150, strength=0.5, tint=(0.85, 0.9, 1.0)); sun(38, 150, 2.2, (1.0, 0.94, 0.85), 1.5)
        bpy.context.scene.view_settings.exposure = -1.0
    elif variant == "autumn":
        world_flat((0.42, 0.45, 0.5), 0.95)
    else:                                                                                       # winter / seasons: soft overcast
        world_flat((0.6, 0.63, 0.68), 0.85)
    # ground: pavement, kerb, road
    pave = ph.texture("concrete_pavers", scale=0.8)
    road = ph.texture("asphalt_02", scale=0.25)
    box("Pavement", (0, KERB_Y / 2, -0.01), (220, -KERB_Y, 0.16), pave)
    box("Kerb", (0, KERB_Y, 0.0), (220, 0.25, 0.18), pbr("Granite", (0.32, 0.31, 0.3), 0.55))
    box("Road", (0, KERB_Y - ROAD_W / 2, -0.12), (220, ROAD_W, 0.1), road)
    box("FarPave", (0, KERB_Y - ROAD_W - 3, -0.01), (220, 6, 0.16), pave)
    # the bank: 7 bays, entrance in the middle bay (x = 0)
    kit_facade(-10.5, 7, door_bays=(3,))
    # granite steps up to the entrance, with a low parapet each side
    gran = ph.texture("granite_tile", scale=1.0)
    for k in range(STEP_N):
        d = STEP_D * (STEP_N - k)
        box("Step", (0, -d / 2 - 0.05, STEP_H * (k + 0.5)), (4.2, d, STEP_H), gran)
    for sx in (-2.25, 2.25):
        box("Parapet", (sx, -STEP_D * STEP_N / 2 - 0.05, 0.42), (0.3, STEP_D * STEP_N, 0.84), gran)
    c["step_top"] = STEP_H * STEP_N
    # brass plate beside the door, plain lettering
    plate = pbr("PlateBrass", (0.55, 0.42, 0.2), 0.3, 1.0)
    box("BankPlate", (1.4, -0.12, 2.0), (0.7, 0.02, 0.45), plate, bevel=0.005)
    text_obj("BankPlateText", "БАНК", (1.4, -0.135, 2.03), 0.12, pbr("PlateInk", (0.05, 0.04, 0.03), 0.4), rot=(math.radians(90), 0, 0), extrude=0.001)
    # neighbours (CG stucco, punched windows) to close the street
    kit_facade(-22.5, 4, tint=(0.78, 0.82, 0.86), top_bay="centered_small")          # left: warm grey stone
    kit_facade(10.5, 5, tint=(1.05, 0.82, 0.38), top_bay="centered_large")          # right: ochre
    kit_facade(25.5, 4, tint=(0.62, 0.72, 0.82), top_bay="centered_double")        # further along: pale blue-grey, then sage
    kit_facade(37.5, 5, tint=(0.72, 0.84, 0.62), top_bay="offset_small")
    kit_facade(-34.5, 4, tint=(1.0, 0.9, 0.62), top_bay="centered_double")         # and the other way: cream
    for x, w, h, col in ((66.0, 27.0, 17.0, (0.42, 0.33, 0.24)), (94.0, 28.0, 20.0, (0.36, 0.38, 0.4)),
                         (-48.5, 28.0, 18.0, (0.4, 0.36, 0.32)), (-76.5, 28.0, 21.0, (0.46, 0.4, 0.3)), (-96.0, 10.0, 16.0, (0.5, 0.46, 0.4))):
        box("Neighbour", (x, 6.0, h / 2), (w, 12.0, h), masonry_facade(f"N{x}", col, 3.2, 2.6, 1.2, 1.7, 0.1, lit_col=(1.0, 0.72, 0.45), lit_strength=0.25))
    if variant == "dusk":                                                           # soft warm rooms behind some windows
        for k in range(10):
            x = float(rng.uniform(-22, 25)); z = float(rng.choice([4.3, 7.3, 10.3]))
            l = area_light((x, 0.9, z), (math.radians(90), 0, 0), 1.2, 12, (1.0, 0.75, 0.45)); l.visible_camera = False
    for sx in (-1, 1):                                                               # buildings closing both ends of the street
        box("StreetEnd", (sx * 108, -12, 11), (4, 60, 22), masonry_facade(f"End{sx}", (0.56, 0.52, 0.46), 3.2, 2.6, 1.2, 1.7, 0.1, lit_col=(1.0, 0.72, 0.45), lit_strength=0.25))
    box("OppositeRow", (0, KERB_Y - ROAD_W - 12, 10), (220, 12, 20), masonry_facade("Opp", (0.55, 0.5, 0.42), 3.2, 2.6, 1.2, 1.7, 0.12, lit_col=(1.0, 0.72, 0.45), lit_strength=0.3))
    # street lamps (scanned) along the kerb, lit; linden-like small trees
    for x in (-16.0, -4.0, 8.0, 20.0):
        r, lm = ph.model("street_lamp_01", loc=(x, KERB_Y + 0.5, 0), rot_z=math.radians(180))
        if variant == "dusk":
            l = bpy.data.lights.new("StreetLamp", 'POINT'); l.energy = 160; l.color = (1.0, 0.8, 0.6); l.shadow_soft_size = 0.15
            lo = bpy.data.objects.new("StreetLamp", l); bpy.context.collection.objects.link(lo); lo.location = (x, KERB_Y + 0.5, 3.75)
    if variant in ("dusk", "summer", "autumn"):
        for x in (-12.5, 12.0, 24.0):
            r, tm = ph.model("tree_small_02", loc=(x, KERB_Y + 1.1, 0), rot_z=rng.uniform(0, 6.28), scale=1.25)
            if variant == "autumn":
                retint(tm, (1.4, 0.75, 0.3))
    # warm light inside the banking hall
    for x in (-7.5, -1.5, 4.5):
        l = area_light((x, 1.5, 2.8), (0, 0, 0), 3.0, 140 if variant == "dusk" else 40, (1.0, 0.82, 0.6)); l.visible_camera = False
    # the entrance doors, hinged so they can open (the kit's own door in the centre bay is removed)
    for o in list(bpy.data.objects):
        if o.name.startswith("door_centered_large_01") and o.type == 'MESH':
            lo_, hi_ = ph.bounds([o])
            if abs((lo_.x + hi_.x) / 2) < 0.5 and lo_.z < 1.0:
                bpy.data.objects.remove(o, do_unlink=True)
    dm = pbr("BankDoorWood", (0.12, 0.07, 0.04), 0.4, 0.0, **{'Coat Weight': 0.4})
    c["doors"] = []
    for sx in (-1, 1):
        lf = joinm([box("BDLeaf", (-sx * 0.42, 0, 1.3), (0.84, 0.06, 2.6), dm, bevel=0.01),
                    box("BDGlass", (-sx * 0.42, -0.035, 1.75), (0.55, 0.01, 1.0), glass("BDGlassM", (0.75, 0.7, 0.6), 0.1)),
                    cyl("BDHandle", (-sx * 0.75, -0.08, 1.15), 0.015, 0.4, pbr("BDBrass", (0.6, 0.45, 0.2), 0.3, 1.0), verts=12)], "BankDoor")
        lf.location = (sx * 0.86, -0.12, STEP_H * STEP_N - 0.64 + 0.64); c["doors"].append(lf)
    box("BankLobbyBack", (0, 3.0, 1.9), (3.0, 0.1, 3.8), pbr("LobbyWood", (0.25, 0.15, 0.08), 0.5))      # a real hall behind the doors
    box("BankLobbyFloor", (0, 1.5, 0.63), (3.0, 3.0, 0.02), pbr("LobbyStone", (0.45, 0.42, 0.38), 0.3))
    ll = area_light((0, 1.6, 3.4), (0, 0, 0), 1.5, 60 if variant == "dusk" else 20, (1.0, 0.82, 0.58)); ll.visible_camera = False
    # weather and season dressing
    if variant == "autumn":
        c["rain"] = precip_curtains("rain", x_range=(-9, 9), ys=(-5.5, -3.0, -1.0))          # short curtains: seen along the street they stack into a white wall
        c["leaves"] = leaves(160, (-14, 14, KERB_Y - 1.0, -0.2))
        for nm in ("Road", "Pavement", "FarPave"):
            o = bpy.data.objects.get(nm)
            if o:
                o.data.materials[0].node_tree.nodes["Principled BSDF"].inputs['Coat Weight'].default_value = 0.8
    if variant in ("winter", "seasons"):
        snow_m = pbr("SnowCover", (0.85, 0.87, 0.9), 0.6, 0.0, **{'Subsurface Weight': 0.3})
        cover = [box("SnowPave", (0, KERB_Y / 2, 0.075), (220, -KERB_Y, 0.03), snow_m), box("SnowFar", (0, KERB_Y - ROAD_W - 3, 0.075), (220, 6, 0.03), snow_m),
                 box("SnowRoadEdge", (0, KERB_Y - 0.8, -0.05), (220, 1.4, 0.03), snow_m)]
        for k in range(STEP_N):
            d = STEP_D * (STEP_N - k)
            cover.append(box("SnowStep", (0, -d / 2 - 0.05, STEP_H * (k + 1) + 0.012), (4.0, d - 0.04, 0.025), snow_m))
        c["snow_cover"] = cover
        c["snow"] = precip_curtains("snow")
    if variant == "seasons":
        c["leaves"] = leaves(160, (-14, 14, KERB_Y - 1.0, -0.2))
        c["rain"] = precip_curtains("rain")
        # one shot, three seasons: snow, autumn leaves, rain, a third of the shot each (PB_SHOT_FRAMES = the cut, at bake time)
        nf = int(os.environ.get("PB_SHOT_FRAMES", 150)); F1, F2 = nf // 3, 2 * nf // 3
        for o in c["snow_cover"] + c["snow"]:
            d = o.driver_add("hide_render").driver; d.type = 'SCRIPTED'; d.expression = f"frame >= {F1}"
        for o in c["leaves"]:
            d = o.driver_add("hide_render").driver; d.type = 'SCRIPTED'; d.expression = f"frame < {F1} or frame >= {F2}"
        for o in c["rain"]:
            d = o.driver_add("hide_render").driver; d.type = 'SCRIPTED'; d.expression = f"frame < {F2}"
        bg = bpy.context.scene.world.node_tree.nodes["Background"]
        d = bg.inputs['Color'].driver_add("default_value", 0).driver; d.type = 'SCRIPTED'; d.expression = f"0.6 if frame < {F1} else (0.55 if frame < {F2} else 0.4)"
        d = bg.inputs['Color'].driver_add("default_value", 1).driver; d.type = 'SCRIPTED'; d.expression = f"0.63 if frame < {F1} else (0.5 if frame < {F2} else 0.44)"
        d = bg.inputs['Color'].driver_add("default_value", 2).driver; d.type = 'SCRIPTED'; d.expression = f"0.68 if frame < {F1} else (0.42 if frame < {F2} else 0.5)"
        # autumn: trees in yellow leaf (visible only in the autumn third), leaves falling through the air
        from pbkit import ph_instances
        trees = ph_instances("tree_small_02", [((x, KERB_Y + 1.1, 0), float(rng.uniform(0, 6.28)), 1.3) for x in (-12.5, -2.0, 9.0, 20.0)])
        for t_ in trees:
            for o in [t_] + list(t_.children):
                d = o.driver_add("hide_render").driver; d.type = 'SCRIPTED'; d.expression = f"frame < {F1} or frame >= {F2}"
                for ms in getattr(o, "material_slots", []):
                    if ms.material and not ms.material.name.startswith("Autumn"):
                        m2 = ms.material.copy(); m2.name = "Autumn" + m2.name
                        pb = m2.node_tree.nodes.get("Principled BSDF")
                        if pb and pb.inputs['Base Color'].is_linked:
                            src = pb.inputs['Base Color'].links[0].from_socket
                            mx = m2.node_tree.nodes.new("ShaderNodeMix"); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs['Factor'].default_value = 1.0
                            m2.node_tree.links.new(src, mx.inputs[6]); mx.inputs[7].default_value = (1.6, 0.8, 0.25, 1)
                            m2.node_tree.links.new(mx.outputs[2], pb.inputs['Base Color'])
                        ms.material = m2
        c["air_leaves"] = leaves(80, (-14, 14, KERB_Y - 3.0, -0.5), seed=9)
        for o in c["air_leaves"]:
            d = o.driver_add("hide_render").driver; d.type = 'SCRIPTED'; d.expression = f"frame < {F1} or frame >= {F2}"
        # rain: the road and pavement turn wet and glossy
        for nm in ("Road", "Pavement", "FarPave"):
            o = bpy.data.objects.get(nm)
            if o:
                pb = o.data.materials[0].node_tree.nodes["Principled BSDF"]
                d = pb.inputs['Coat Weight'].driver_add("default_value").driver; d.type = 'SCRIPTED'; d.expression = f"0.9 if frame >= {F2} else 0.0"
    CAST[variant](c)
    animate(c, 0.0, {"dusk": "pullup", "summer": "traffic", "autumn": "detain", "winter": "doorbell", "seasons": "seasons"}[variant])
    return c


def cast_dusk(c):
    blue = (0.05, 0.12, 0.42)
    c["cars"] = [soviet_car(f"Militia{k}", None, kind="lada", beacon=True, lamps=True) for k in range(2)]
    parked = soviet_car("ParkedVolga", (0.16, 0.18, 0.2), kind="volga"); parked.location = (14.0, KERB_Y - 1.1, 0.0)
    c["people"] = {"sit": PP.militia("OffSit", 44), "help": PP.militia("OffHelp", 31), "walk": PP.militia("OffWalk", 38)}


def cast_summer(c):
    cols = [(0.15, 0.17, 0.2), (0.62, 0.6, 0.55), (0.35, 0.08, 0.06), (0.22, 0.3, 0.24), (0.7, 0.66, 0.5)]
    c["traffic"] = [soviet_car(f"Traffic{k}", cols[k], kind="volga" if k % 2 == 0 else "lada") for k in range(5)]
    from pbkit import kit_vehicle
    c["trolley"] = kit_vehicle("bus_city", "CityBus", (0.75, 0.68, 0.45))
    c["banker"] = person("Banker", 1.0, 52, "male_elegantsuit01", "short04", cval=0.1, hv=0.45, sat=0.2)
    c["doorman"] = person("Doorman", 1.0, 58, "male_elegantsuit01", "short04", cval=0.25, hv=0.6, hue=0.6, sat=0.6)
    c["walkers"] = [person("Passer1", 0.0, 40, "female_elegantsuit01", "bob01", cval=0.4, hv=0.3), person("Passer2", 1.0, 30, "male_casualsuit02", "short01", cval=0.5)]
    c["briefcase"] = joinm([box("BCase", (0, 0, 0), (0.42, 0.1, 0.3), pbr("BCaseL", (0.08, 0.045, 0.025), 0.45), bevel=0.02)], "BankerCase")
    # street life: shop signs (generic Cyrillic) over the neighbours' ground floors, a news kiosk, lime trees, pedestrians
    for k, (x, word, bg) in enumerate(((-19.5, "ПРОДУКТЫ", (0.12, 0.3, 0.55)), (-13.5, "АПТЕКА", (0.15, 0.42, 0.25)), (13.5, "ХЛЕБ", (0.55, 0.22, 0.1)),
                                       (19.5, "ОПТИКА", (0.2, 0.22, 0.25)), (24.0, "ОБУВЬ", (0.45, 0.12, 0.12)))):
        box(f"ShopSign{k}", (x, -0.5, 3.7), (2.4, 0.08, 0.55), pbr(f"SignBoard{k}", bg, 0.5), bevel=0.01)
        text_obj(f"ShopWord{k}", word, (x, -0.55, 3.59), 0.3, pbr(f"SignInk{k}", (0.92, 0.9, 0.82), 0.4), extrude=0.004)
    kiosk_m = pbr("KioskBody", (0.62, 0.7, 0.72), 0.45, 0.2)
    kx, ky = 7.5, KERB_Y + 1.6
    box("Kiosk", (kx, ky, 1.15), (2.2, 1.6, 2.3), kiosk_m, bevel=0.03)
    box("KioskRoof", (kx, ky, 2.38), (2.5, 1.9, 0.12), pbr("KioskRoofM", (0.25, 0.3, 0.32), 0.5))
    box("KioskGlass", (kx, ky - 0.81, 1.45), (1.9, 0.02, 0.9), glass("KioskGlassM", (0.8, 0.85, 0.85), 0.05))
    from pbkit import image_plane
    import paper_tex
    pgs = paper_tex.make_all()["pages"]
    for j in range(4):                                                              # papers and magazines behind the glass
        image_plane(f"KioskPaper{j}", pgs[j % len(pgs)], (kx - 0.7 + j * 0.45, ky - 0.7, 1.4 + 0.12 * (j % 2)), (0.3, 0.4), (math.radians(80), 0, 0), rough=0.8)
    box("KioskSign", (kx, ky - 0.86, 2.1), (1.9, 0.04, 0.3), pbr("KioskSignM", (0.6, 0.12, 0.08), 0.5))
    text_obj("KioskWord", "ГАЗЕТЫ", (kx, -0.04 + ky - 0.84, 2.02), 0.2, pbr("KioskInk", (0.95, 0.92, 0.85), 0.4), extrude=0.003)
    from pbkit import ph_instances
    ph_instances("tree_small_02", [((x, KERB_Y + 1.1, 0), float(rng.uniform(0, 6.28)), 1.2) for x in (-24.0, -6.0, 3.0, 18.0, 33.0)])
    ph_instances("tree_small_02", [((x, FAR_KERB + 1.2, 0), float(rng.uniform(0, 6.28)), 1.15) for x in (-20.0, -8.0, 4.0, 16.0, 28.0)])
    c["near_walkers"] = [person("Passer3", 0.0, 62, "female_casualsuit01", "bob02", cval=0.35, hv=0.4),
                         person("Passer4", 1.0, 24, "male_casualsuit03", "short02", cval=0.55, hv=0.2),
                         person("Passer5", 0.0, 33, "female_elegantsuit01", "long01", cval=0.3, hv=0.25)]
    # overhead trolleybus wires along the street
    for y in (KERB_Y - 2.5, KERB_Y - 3.3):
        cyl("Wire", (0, y, 6.2), 0.008, 90, pbr("WireM", (0.05, 0.05, 0.05), 0.5), verts=6, rot=(0, math.radians(90), 0))


def cast_autumn(c):
    c["car"] = soviet_car("MilitiaVolga", (0.42, 0.48, 0.55), kind="volga", stripe=(0.05, 0.12, 0.42), beacon=True)
    c["offA"] = PP.militia("DetA", 40); c["offB"] = PP.militia("DetB", 33)
    c["man"] = person("Detained", 1.0, 42, "male_elegantsuit01", "short01", cval=0.2, hv=0.15, hue=0.62, sat=0.5)
    c["umbrella"] = None


def cast_winter(c):
    c["inv"] = person("InvWinter", 1.0, 46, "male_casualsuit05", "short02", cval=0.14, hv=0.3, sat=0.2)
    # rings at an ordinary entrance of the ochre neighbour (a kit facade door); a buzzer panel beside it
    box("Buzzer", (DOOR2_X + 0.95, -0.12, 1.35), (0.1, 0.03, 0.16), pbr("BuzzerM", (0.3, 0.3, 0.3), 0.4, 0.8))


def cast_seasons(c):
    c["traffic"] = [soviet_car(f"Season{k}", ((0.15, 0.17, 0.2), (0.6, 0.58, 0.52), (0.3, 0.08, 0.06))[k], kind="lada" if k else "volga") for k in range(3)]


CAST = {"dusk": cast_dusk, "summer": cast_summer, "autumn": cast_autumn, "winter": cast_winter, "seasons": cast_seasons}


def trolleybus():
    body = pbr("TrolleyCream", (0.72, 0.66, 0.48), 0.4, 0.1, **{'Coat Weight': 0.5})
    band = pbr("TrolleyRed", (0.5, 0.1, 0.06), 0.4)
    glass_m = pbr("TrolleyGlass", (0.03, 0.035, 0.04), 0.05, 0.0, **{'Coat Weight': 1.0})
    tyre = pbr("TrolleyTyre", (0.02, 0.02, 0.02), 0.85)
    parts = [box("TBody", (0, 0, 1.65), (11.5, 2.5, 2.6), body, bevel=0.35),
             box("TBand", (0, 0, 0.75), (11.52, 2.52, 0.3), band),
             box("TWin", (0.2, 0, 2.0), (10.0, 2.52, 1.0), glass_m),
             box("TWind", (5.76, 0, 1.9), (0.04, 2.2, 1.3), glass_m)]
    for k in range(6):
        parts.append(box("TPillar", (-4.5 + k * 1.8, 0, 2.0), (0.12, 2.54, 1.02), body))
    for sx in (-3.6, 3.8):
        for sy in (-1, 1):
            parts.append(cyl("TTyre", (sx, sy * 1.05, 0.5), 0.5, 0.3, tyre, verts=24, rot=(math.radians(90), 0, 0)))
    for sy in (-0.25, 0.25):
        parts.append(box("TPole", (-1.2, sy, 4.6), (6.2, 0.05, 0.05), pbr("PoleBlack", (0.05, 0.05, 0.05), 0.5), rot=(0, math.radians(-14), 0)))
    return joinm(parts, "Trolleybus")


def seat_on_steps(h, x, k_seat):
    """Sit on step k_seat, feet two steps down, facing the street (-Y)."""
    reset_pose(h); h.arm.rotation_euler = (0, 0, 0); h.arm.location = (0, 0, 0); bpy.context.view_layer.update()
    pose_sit(h, lean=22)
    y_front = -STEP_D * (STEP_N - k_seat) - 0.05                 # front edge of the seat step
    h.arm.location = (x, y_front + 0.12, 0); bpy.context.view_layer.update()
    pelvis = h.bone_head("pelvis") if "pelvis" in h.arm.pose.bones else h.bone_head("spine05")
    seat_z = STEP_H * (k_seat + 1)
    w = np.concatenate([_world_verts(o) for o in h.parts if o.type == 'MESH'])
    # rest the body's lowest point behind the knees on the step: put the pelvis ~0.1 m above the seat
    h.arm.location.z += seat_z + 0.1 - pelvis.z
    bpy.context.view_layer.update()


# ============================================================================ animation
def car_x(sec, x_stop, arrive=2.8, v0=11.0, start=-26.0):
    """Decelerate uniformly from v0 so the car stops exactly at x_stop at time `arrive`."""
    d = x_stop - start
    v0 = 2 * d / arrive
    if sec >= arrive:
        return x_stop, 0.0
    return start + v0 * sec - 0.5 * (v0 / arrive) * sec * sec, v0 * (1 - sec / arrive)


def animate(c, sec, shot):
    if shot in ("pullup", "steps"):
        return animate_dusk(c, sec, shot)
    fn = ANIM.get(shot)
    if fn:
        fn(c, sec)
    bpy.context.view_layer.update()


def animate_dusk(c, sec, shot):
    y_lane = KERB_Y - 1.2
    for k, car in enumerate(c["cars"]):
        if shot == "pullup":
            x, v = car_x(max(0.0, sec - 0.9 * k), -3.5 - 5.2 * k, arrive=3.2, start=-34.0 - 6 * k)
        else:
            x, v = -8.0 - 5.2 * k, 0.0                                   # parked further down for the steps shot
        car.location = (x, y_lane, 0.0); car.rotation_euler = (0, 0, 0)
    a, b, w = c["people"]["sit"], c["people"]["help"], c["people"]["walk"]
    # walker: an officer climbing toward the door (2A); out of the way in 2B
    if shot == "pullup":
        ph_ = (sec * 0.9) % 1.0
        pose_walk_at(w, ph_, Vector((2.6, -4.4 + 1.2 * min(sec, 3.2), 0.0)), math.pi)
    else:
        PP.hide(w, True)                                                 # cap included
    # seated officer and the colleague with the glass (2B); in 2A they are already there, small in the background
    seat_on_steps(a, -0.8, 1)
    nod(a, "spine04", 10); nod(a, "neck01", 10); nod(a, "head", 14)
    fwd = _fwd(a)
    knees = (a.bone_tail("upperleg02.L") + a.bone_tail("upperleg02.R")) / 2
    hand_out = ease(min(1.0, max(0.0, (sec - 1.0) / 1.4))) if shot == "steps" else 0.0
    glass_pos = None
    # helper crouches on the step below, to the seated man's left, holding out a glass
    stand(b, (-0.05, -STEP_D * STEP_N - 0.35, 0), math.radians(-50))       # on the pavement, angled toward him
    nod(b, "spine04", 26); nod(b, "spine03", 14); nod(b, "head", 6)
    bpy.context.view_layer.update()
    gp0 = b.bone_head("spine03") + _fwd(b) * 0.2 + Vector((0, 0, -0.35))
    gp1 = knees + fwd * 0.22 + Vector((0.1, 0, 0.05))
    glass_pos = gp0.lerp(gp1, hand_out)
    # the wrist is only aimed while the glass is held out; resting, it follows the forearm (no folded-back hand)
    reach(b, "R", glass_pos + Vector((0, 0, -0.03)), Vector((0.5, 0.3, -0.7)), Vector((0, 0, 1)) if hand_out > 0.3 else None)
    fingers_curl(b, 45, side=("R",), thumb=25)
    look(b, a.bone_head("head"), 1.0)
    # seated man's right hand comes up to take it at the end
    take = ease(min(1.0, max(0.0, (sec - 2.6) / 1.2))) if shot == "steps" else 0.0
    rest = knees + Vector((0.0, 0, 0.05))
    reach(a, "R", rest.lerp(glass_pos + Vector((0.03, 0.02, 0.0)), take), Vector((-0.5, -0.5, -0.6)), Vector((0, 0.5, -0.8)))
    reach(a, "L", knees + Vector((0.12, 0.05, 0.04)), Vector((0.5, -0.5, -0.6)), Vector((0, -0.5, -0.8)))
    if "glass" not in c:
        gm = glass("WaterGlass", (0.95, 0.97, 0.98), 0.02)
        g = cyl("Glass", (0, 0, 0.05), 0.035, 0.1, gm, verts=24)
        water = cyl("Water", (0, 0, 0.035), 0.032, 0.07, pbr("Water", (0.8, 0.85, 0.9), 0.0, 0.0, **{'Transmission Weight': 1.0}), verts=24)
        water.parent = g
        c["glass"] = g
    c["glass"].location = glass_pos + Vector((0, 0, -0.05))
    bpy.context.view_layer.update()


def pose_walk_at(h, phase, loc, face_z):
    h.arm.rotation_euler = (0, 0, 0); h.arm.location = (0, 0, 0); bpy.context.view_layer.update()
    bob = pose_walk(h, phase, stride=24, arm_swing=16)
    PP.relax_arms(h, 16, phase)
    h.arm.rotation_euler = (0, 0, face_z)
    # stairs: lift the walker with the step under him
    step_k = max(0, min(STEP_N, int((loc.y + STEP_D * STEP_N + 0.05) / STEP_D) + 1)) if loc.y > -STEP_D * STEP_N - 0.05 else 0
    h.arm.location = (loc.x, loc.y, STEP_H * step_k + bob); bpy.context.view_layer.update()


def anim_pullup(c, t):
    animate(c, t * DUR["pullup"], "pullup")


def anim_steps(c, t):
    animate(c, t * DUR["steps"], "steps")


# ============================================================================ cameras
def cam_pullup(c, t):
    e = ease(t)
    loc = Vector((-12.0, KERB_Y - ROAD_W + 1.5, 1.5)).lerp(Vector((-10.8, KERB_Y - ROAD_W + 1.8, 1.55)), e)
    tgt = Vector((-6.0, -2.0, 2.6)).lerp(Vector((-2.0, -1.5, 2.4)), e)
    return (loc, tgt, 28)


def cam_steps(c, t):
    e = ease(t)
    a = c["people"]["sit"]
    tgt = Vector((-0.55, -1.0, 0.85))
    return (tgt + Vector((-2.4, -5.6, 0.8)).lerp(Vector((-2.1, -5.0, 0.75)), e), tgt + Vector((0.3, 0, 0.25)), 30)


MOVES = {
    "pullup": dict(kind="anim", dof=5.6, far=60.0, cam=cam_pullup, anim=anim_pullup, focus=lambda c, t: c["cars"][0].location + Vector((0, 0, 1.0))),
    "steps": dict(kind="anim", dof=2.8, far=30.0, cam=cam_steps, anim=anim_steps, focus=lambda c, t: Vector((-0.55, -1.0, 0.85))),
}


# ============================================================================ chapter shots on the street
DUR.update({"traffic": 6.5, "arrive_bank": 6.0, "detain": 5.5, "release": 5.5, "doorbell": 6.0, "seasons": 7.0})
VARIANT_FOR = {"pullup": "dusk", "steps": "dusk", "traffic": "summer", "arrive_bank": "summer", "detain": "autumn", "release": "autumn",
               "doorbell": "winter", "seasons": "seasons"}
LANE_NEAR, LANE_FAR = KERB_Y - 1.8, KERB_Y - ROAD_W + 2.2
FAR_KERB = KERB_Y - ROAD_W - 6.0


def drive(car, x0, v, sec, y, d=1):
    car.location = (x0 + d * v * sec, y, 0.0); car.rotation_euler = (0, 0, 0 if d > 0 else math.pi)


def open_doors(c, k):
    for sx, lf in zip((-1, 1), c["doors"]):
        lf.rotation_euler = (0, 0, math.radians(sx * 75 * k))


def a_traffic(c, sec):
    """Summer 1995: Volgas, a Lada and a trolleybus pass the bank; two people walk the far pavement."""
    tr = c["traffic"]
    specs = [(-40, 11, LANE_NEAR, 1), (-60, 12, LANE_NEAR, 1), (40, 10, LANE_FAR, -1), (70, 12, LANE_FAR, -1), (-80, 13, LANE_NEAR, 1)]
    for car, (x0, v, y, d) in zip(tr, specs):
        drive(car, x0, v, sec, y, d)
    drive(c["trolley"], 30, 6.5, sec, KERB_Y - 2.9, -1)
    for k, w in enumerate(c["walkers"]):
        PP.walk_at(w, sec * 0.9 + k * 0.4, (-6 + k * 9 + (1.3 if k == 0 else -1.3) * sec, KERB_Y - ROAD_W - 1.5, 0), math.radians(90 if k == 0 else -90), stride=22, swing=14)
    for k, w in enumerate(c.get("near_walkers", [])):                              # the near pavement
        d = 1 if k % 2 == 0 else -1
        PP.walk_at(w, sec * 0.85 + k * 0.33, (-8 + k * 7 + d * 1.2 * sec, KERB_Y + 1.2 + 1.3 * (k % 2), 0), math.radians(90 * d), stride=20, swing=12)
    for h in (c["banker"], c["doorman"]):
        PP.hide(h, True)
    c["briefcase"].hide_render = True
    open_doors(c, 0.0)


def a_arrive_bank(c, sec):
    """The banker (from behind) walks up the steps; the doorman opens the door for him."""
    for car in c["traffic"]:
        car.location = (60, 0, -10)
    drive(c["traffic"][0], -30, 10, sec, LANE_FAR + 2, 1)
    c["trolley"].location = (60, 0, -10)
    for w in c["walkers"] + c.get("near_walkers", []):
        PP.hide(w, True)
    b = c["banker"]; PP.hide(b, False); PP.hide(c["doorman"], False); c["briefcase"].hide_render = False
    y = KERB_Y + 1.0 + 0.85 * sec
    y = min(y, -0.35)
    pose_walk_at(b, (sec * 0.9) % 1.0, Vector((-0.3, y, 0.0)), math.pi)          # walks +Y, toward the door
    c["briefcase"].location = b.bone_tail("wrist.R") + Vector((0, 0, -0.2)); c["briefcase"].rotation_euler = (0, 0, math.radians(90))
    dm = c["doorman"]
    k = ease(min(1.0, max(0.0, (sec - 2.2) / 1.5)))
    PP.stand(dm, (0.95, -0.42, STEP_H * STEP_N), math.radians(-90 + 40 * 0))      # by the right leaf, facing -X... then the door
    PP.nod(dm, "head", 6)
    open_doors(c, 0.0)
    c["doors"][1].rotation_euler = (0, 0, math.radians(75 * k))
    PP.hand_to(dm, "R", c["doors"][1].matrix_world @ Vector((-0.75, -0.08, 1.15)), curl=50)
    PP.look(dm, b.bone_head("head"), 1.0)


def a_detain(c, sec):
    """Autumn rain: two plain-clothes officers walk a man from the building to the militia Volga at the kerb."""
    car = c["car"]; car.location = (2.5, KERB_Y - 1.1, 0); car.rotation_euler = (0, 0, 0)
    y = -1.6 - 0.75 * sec
    face = 0.0                                                                       # walking toward -Y (the street)
    PP.walk_at(c["man"], sec * 0.8, (0.3, y, 0), face, stride=18, swing=4)
    PP.nod(c["man"], "head", 16)
    PP.walk_at(c["offA"], sec * 0.8 + 0.5, (-0.25, y + 0.1, 0), face, stride=18, swing=6)
    PP.walk_at(c["offB"], sec * 0.8 + 0.25, (0.85, y + 0.1, 0), face, stride=18, swing=6)
    PP.hand_to(c["offA"], "L", c["man"].bone_head("upperarm01.R") + Vector((0, 0, -0.2)), curl=50)
    PP.hand_to(c["offB"], "R", c["man"].bone_head("upperarm01.L") + Vector((0, 0, -0.2)), curl=50)
    for h in (c["offA"], c["offB"], c["man"]):
        PP.hide(h, False)
    for lf in c.get("leaves", []):
        pass


def a_release(c, sec):
    """Thirty days later: he walks out alone along the wet pavement, collar up, leaves blowing past."""
    PP.hide(c["offA"], True); PP.hide(c["offB"], True)
    c["car"].location = (60, 0, -10)
    for o in c.get("rain", []):
        o.hide_render = True
    m = c["man"]
    PP.walk_at(m, sec * 0.85, (-6.0 + 1.1 * sec, KERB_Y + 1.6, 0), math.radians(90), stride=22, swing=8)
    PP.nod(m, "neck01", 6); PP.nod(m, "head", 10)
    r = np.random.default_rng(3)
    for k, lf in enumerate(c["leaves"][:60]):                                       # gusts carry some leaves along the pavement
        x0 = r.uniform(-14, 6); y0 = r.uniform(KERB_Y + 0.3, -0.5); v = r.uniform(0.6, 1.6)
        lf.location = (x0 + v * sec, y0 + 0.2 * math.sin(sec * 1.3 + k), 0.012 + max(0.0, 0.25 * math.sin(sec * 2.0 + k)))
        lf.rotation_euler = (sec * 2.0 + k, sec * 1.3, k)


def a_doorbell(c, sec):
    """Winter, snow falling: an investigator rings at an apartment entrance; no answer. He steps back and looks up."""
    inv = c["inv"]
    back = ease(min(1.0, max(0.0, (sec - 3.5) / 1.5)))
    PP.stand(inv, (DOOR2_X + 0.4, -0.8 - 0.6 * back, 0.08), 0.0 + math.pi)                   # faces +Y (the door)
    if sec < 3.0:
        PP.hand_to(inv, "R", Vector((DOOR2_X + 0.95, -0.15, 1.35)) + Vector((0, -0.03 * (1 if (sec % 1.2) < 0.4 else 0), 0)), curl=60)
    PP.nod(inv, "head", -14 * back)


def a_seasons(c, sec):
    """Same street, same move: snow, then autumn leaves, then rain; cars pass in each season."""
    bpy.context.scene.frame_set(int(sec * 24) + 1)              # the season switches are frame drivers: evaluate them
    r = np.random.default_rng(12)
    for k, lf in enumerate(c.get("air_leaves", [])):            # leaves drifting down through the frame
        x0 = r.uniform(-14, 14); y0 = r.uniform(KERB_Y - 3.0, -0.5); z0 = r.uniform(0.5, 7.0); v = r.uniform(0.5, 1.0)
        z = (z0 - v * sec) % 7.0 + 0.05
        lf.location = (x0 + 0.6 * math.sin(sec * 1.1 + k), y0, z); lf.rotation_euler = (sec * 2.3 + k, sec * 1.7, k)
    for k, car in enumerate(c["traffic"]):
        drive(car, -40 + k * 25, 11, (sec + k * 2.0) % 7.0, LANE_NEAR if k % 2 == 0 else LANE_FAR, 1 if k % 2 == 0 else -1)


ANIM = {"traffic": a_traffic, "arrive_bank": a_arrive_bank, "detain": a_detain, "release": a_release, "doorbell": a_doorbell, "seasons": a_seasons}


def _anim(move):
    return lambda c, t: animate(c, t * DUR[move], move)


def _push(a, b, ta, tb, lens):
    return lambda c, t: (Vector(a).lerp(Vector(b), ease(t)), Vector(ta).lerp(Vector(tb), ease(t)), lens)


FAR = KERB_Y - ROAD_W
MOVES.update({
    "traffic": dict(kind="anim", dof=11.0, far=80.0, anim=_anim("traffic"), cam=_push((-16.0, FAR - 2.0, 2.3), (-14.5, FAR - 1.9, 2.35), (8.0, -1.0, 3.2), (10.0, -1.0, 3.0), 26),
                    focus=lambda c, t: Vector((0.0, KERB_Y, 2.0)), title=("CHAPTER 1", "TWO HOSPITALS", 12, 120)),
    "arrive_bank": dict(kind="anim", dof=4.0, far=40.0, anim=_anim("arrive_bank"), cam=_push((-4.5, KERB_Y - 2.4, 1.6), (-4.0, KERB_Y - 2.0, 1.62), (0.0, -1.2, 1.6), (0.1, -0.8, 1.7), 30),
                        focus=lambda c, t: c["banker"].bone_head("spine03")),
    "detain": dict(kind="anim", dof=4.0, far=40.0, anim=_anim("detain"), cam=_push((-5.5, KERB_Y - 2.5, 1.5), (-5.0, KERB_Y - 2.2, 1.52), (1.0, -3.0, 1.3), (1.5, -4.2, 1.2), 30),
                   focus=lambda c, t: c["man"].bone_head("spine03")),
    "release": dict(kind="anim", dof=4.0, far=40.0, anim=_anim("release"), cam=_push((-1.0, KERB_Y - 3.0, 1.5), (0.0, KERB_Y - 3.0, 1.5), (-4.0, KERB_Y + 1.6, 1.2), (-0.5, KERB_Y + 1.6, 1.2), 30),
                    focus=lambda c, t: c["man"].bone_head("spine03")),
    "doorbell": dict(kind="anim", dof=4.0, far=40.0, anim=_anim("doorbell"), cam=_push((DOOR2_X - 3.0, KERB_Y + 0.2, 1.6), (DOOR2_X - 2.5, KERB_Y + 0.4, 1.6), (DOOR2_X + 0.2, -0.5, 1.5), (DOOR2_X + 0.3, -0.4, 1.7), 32),
                     focus=lambda c, t: c["inv"].bone_head("head")),
    "seasons": dict(kind="anim", dof=8.0, far=80.0, anim=_anim("seasons"), cam=_push((-9.0, FAR - 1.5, 1.7), (-6.0, FAR - 1.6, 1.75), (-3.0, 0.0, 4.0), (0.0, 0.0, 3.8), 26),
                    focus=lambda c, t: Vector((0, -0.2, 3.0))),
})


_build_set = build


def build(variant=None):
    c = _build_set(variant)
    from pbkit import finish_scene
    import pblook
    pblook.apply("sc_bank", variant)                 # the house cinematic light (HOUSE_LOOK=plain for the old)
    finish_scene()
    return c
