"""CH4 (chat B): a northern German harbour town, 2007-08 (generic: no names, no readable signs).
The man there is unnamed, seen only from behind or at medium distance, at his shop, searched, arrested.
Variants:
  harbour:  overcast quay, brick gabled houses, small boats bobbing, a boat-accessories shop on the corner.
            quay   (A): wide slow pan along the harbour: boats bob, a flag snaps, the shop on the quay
            watch  (A2, surveillance): over two officers' shoulders in a parked car at dusk, the shop across the road
            lock   (B2, surveillance): from behind the car: the man locks the shop door and walks off
  shop:     inside the shop: rope coils, fenders, buoys; the man from behind hangs a coil of rope
            shop   (B)
  house:    his brick house: day (search, recorder carried out) and blue dawn (arrest)
            boxes  (A, day):  officers in gloves carry evidence boxes out past the camera
            steps  (A, day):  an officer carries the reel-to-reel in an open evidence box down the steps to a van
            dawn   (A, dawn): two unmarked cars stop outside, officers walk up the path
            away   (B, dawn): from behind: the man is walked to a car between two officers; the car pulls away
"""
import math, os
import numpy as np
import bpy
from mathutils import Vector
from kit import *
from common import world_flat, ease
from human import reach, fingers_curl
import ph
import b_common as B
import b_props as P

EXPOSURE = 0.2
DUR = {"saliva": 5.0, "quay": 6.0, "watch": 5.5, "lock": 5.5, "shop": 5.0, "boxes": 5.0, "steps": 5.5, "dawn": 6.0, "away": 6.5}
VARIANT_FOR = {"saliva": "kitchen", "quay": "harbour", "watch": "harbour_dusk", "lock": "harbour_dusk", "shop": "shop",
               "boxes": "house_day", "steps": "house_day", "dawn": "house_dawn", "away": "house_dawn"}
SHOP_DOOR = Vector((4.0, 6.0, 0.0))
HOUSE_DOOR = Vector((0.0, 6.0, 0.6))


def water_mat():
    m = bpy.data.materials.new("Harbour"); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; p = N["Principled BSDF"]
    p.inputs['Base Color'].default_value = (0.02, 0.035, 0.04, 1); p.inputs['Roughness'].default_value = 0.08
    tc = N.new("ShaderNodeTexCoord"); nz = N.new("ShaderNodeTexNoise"); nz.noise_dimensions = '4D'
    nz.inputs['Scale'].default_value = 0.6; nz.inputs['Detail'].default_value = 6
    d = nz.inputs['W'].driver_add("default_value").driver; d.type = 'SCRIPTED'; d.expression = "frame / 24 * 0.25"
    L.new(tc.outputs['Object'], nz.inputs['Vector'])
    bp = N.new("ShaderNodeBump"); bp.inputs['Strength'].default_value = 0.25; L.new(nz.outputs['Fac'], bp.inputs['Height'])
    L.new(bp.outputs['Normal'], p.inputs['Normal'])
    return m


def gabled(name, x, y, w, d, h, brick, roof, face_y=-1, lit=(), rng=None):
    """A brick gabled house facing -Y: walls, a pitched roof, white-framed windows (some lit), a door."""
    box(name, (x, y + d / 2, h / 2), (w, d, h), brick)
    bpy.ops.mesh.primitive_cylinder_add(vertices=3, radius=w / 2 / math.cos(math.radians(30)) * 0.98, depth=d + 0.3,
                                        location=(x, y + d / 2, h + w * 0.29), rotation=(math.radians(90), 0, 0))
    r = bpy.context.active_object; r.name = name + "Roof"; r.rotation_euler = (math.radians(90), math.radians(90), 0)
    r.scale = (0.9, 1.0, 1.0); r.data.materials.append(roof)
    fr = pbr("WinWhite", (0.85, 0.85, 0.83), 0.4)
    k = 0
    for fl in range(int(h // 2.8)):
        for j in range(max(1, int(w // 2.0))):
            wx = x - w / 2 + 1.0 + j * 2.0; wz = 1.5 + fl * 2.8
            if wx > x + w / 2 - 0.6:
                continue
            box(name + "WF", (wx, y - 0.01, wz), (0.95, 0.06, 1.25), fr)
            lit_ = k in lit
            box(name + "WP", (wx, y - 0.035, wz), (0.82, 0.01, 1.1), emissive("WinLit", (1.0, 0.7, 0.42), 1.4) if lit_ else pbr("WinDark", (0.006, 0.007, 0.008), 0.15, **{'Coat Weight': 0.35}))
            box(name + "WC", (wx - 0.3, y - 0.04, wz), (0.22, 0.01, 1.05), fabric("NetC", (0.5, 0.48, 0.44), 0.9, 0.2, 200))
            k += 1


def motorboat(name, loc, rz, col):
    """A small harbour motor boat: tapered hull, a white wheelhouse, a short mast (no lettering)."""
    import bmesh
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x *= 6.0; v.co.y *= 2.2; v.co.z *= 1.0
        if v.co.x > 0:                                   # bow: pinch and lift
            v.co.y *= 0.15; v.co.z += 0.25 if v.co.z > 0 else 0.15
        if v.co.z < 0:
            v.co.y *= 0.55
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    hull = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(hull)
    me.materials.append(pbr(name + "Hull", col, 0.35, **{'Coat Weight': 0.5}))
    bv = hull.modifiers.new("bv", 'BEVEL'); bv.width = 0.12; bv.segments = 3
    cab = box(name + "Cab", (-0.6, 0, 0.95), (1.8, 1.4, 1.0), pbr("CabW", (0.85, 0.85, 0.83), 0.4), bevel=0.05)
    win = box(name + "CabWin", (0.31, 0, 1.1), (0.02, 1.2, 0.4), pbr("CabGlass", (0.02, 0.03, 0.035), 0.05, **{'Coat Weight': 1.0}))
    mast = cyl(name + "Mast", (-0.9, 0, 2.2), 0.04, 1.8, pbr("MastM", (0.75, 0.75, 0.75), 0.3, 0.8), verts=8)
    for o in (cab, win, mast):
        o.parent = hull
    hull.location = loc; hull.rotation_euler = (0, 0, rz)
    return hull


def build(variant=None):
    variant = variant or "harbour"
    c = {"variant": variant}
    rng = np.random.default_rng(2007)
    try:
        import rj
        rj.sky({"harbour": "grey", "harbour_dusk": "dusk", "shop": "grey", "house_day": "grey", "house_dawn": "dusk"}[variant])
    except Exception:
        world_flat((0.3, 0.33, 0.36), 1.0)
    brick = B.tex_mat("Brick", "brick_wall_02", scale=0.35, tint=(0.7, 0.5, 0.42))
    brick2 = B.tex_mat("Brick2", "red_brick_03" if False else "brick_wall_08", scale=0.35, tint=(0.6, 0.45, 0.38))
    roof = B.tex_mat("Roof", "grey_roof_tiles", scale=0.4, tint=(0.4, 0.38, 0.38))
    cars = []
    if variant == "kitchen":
        # inside the house: a kitchen table; the man sits with his back to us, an officer hands him a swab tube
        world_flat((0.006, 0.007, 0.01), 1.0)
        box("KFloor", (0, 0, -0.01), (5, 4, 0.02), B.tex_mat("KFl", "floor_tiles_06", scale=0.5, tint=(0.6, 0.6, 0.58)))
        kw = B.plaster("KWall", (0.6, 0.58, 0.52), dirt=0.1)
        box("KWallB", (0, 2.0, 1.3), (5, 0.1, 2.6), kw); box("KWallL", (-2.5, 0, 1.3), (0.1, 4, 2.6), kw); box("KWallR", (2.5, 0, 1.3), (0.1, 4, 2.6), kw)
        box("KWin", (0.0, 1.96, 1.5), (1.2, 0.02, 1.0), emissive("KGrey", (0.75, 0.8, 0.85), 0.35))
        for (bx, bz, sx, sz) in ((0.0, 1.5, 0.05, 1.0), (0.0, 1.5, 1.2, 0.05), (0.0, 2.0, 1.25, 0.06), (0.0, 1.0, 1.25, 0.06), (-0.6, 1.5, 0.06, 1.05), (0.6, 1.5, 0.06, 1.05)):
            box("KMull", (bx, 1.94, bz), (sx, 0.03, sz), pbr("KFrame", (0.8, 0.8, 0.78), 0.5))
        B.key_spot((0.6, 1.85, 2.1), (0, 0.3, 0.8), 700, 70, (0.8, 0.86, 0.95), soft=0.6, name="KWinKey")
        B.fill((-2.0, -1.5, 2.0), (0, 0.5, 1.0), 25, 2.0, (0.5, 0.55, 0.7))
        ph.model("wooden_table_02", loc=(0, 0.5, 0), rot_z=0)
        for x, fz in ((-0.1, math.pi), (0.25, 0.0)):
            ph.model("dining_chair_02", loc=(x, -0.15 if fz == math.pi else 1.15, 0), rot_z=fz + math.pi)
        man = B.person("Searched", 1.0, 58, "male_casualsuit03", "short02", hue=0.6, sat=0.2, val=0.35, hair_val=2.0, hair_sat=0.0)
        B.seat(man, (-0.1, -0.22, 0), math.pi, lean=8)          # faces +Y, back to the camera
        off = B.person("SwabOfficer", 0.0, 36, "female_elegantsuit01", "ponytail01", hue=0.6, sat=0.2, val=0.3, hair_val=0.3)
        B.stand(off, (0.35, 1.25, 0), 0.0)                        # across the table, facing -Y
        B.flat_clothes(off, (0.12, 0.14, 0.18))
        c["man"], c["off"] = man, off
        c["tube"] = cyl("SwabTube", (0, 0, 0), 0.012, 0.14, pbr("TubeClear", (0.9, 0.92, 0.95), 0.1, **{'Transmission Weight': 0.7}), verts=16)
        c["rest"] = B.capture(man); c["rests"] = [B.capture(off)]; c["offs"] = [off]
        B.room_haze((0, 0, 1.3), (4.8, 3.8, 2.6), density=0.012)
        return c
    if variant.startswith("harbour") or variant == "shop":
        # quay along y = 0..6 (water at y < 0), a street y = 1..5, houses from y = 6
        box("Quay", (0, 3.0, -0.25), (80, 6.0, 0.5), B.tex_mat("QuayStone", "cobblestone_02", scale=0.25, tint=(0.55, 0.55, 0.55)))
        box("QuayEdge", (0, 0.05, -0.15), (80, 0.3, 0.3), pbr("Granite", (0.35, 0.35, 0.36), 0.6))
        wat = box("Water", (0, -30, -1.2), (120, 60, 0.02), water_mat())
        for k in range(8):
            x0 = -18 + k * 5.0
            gabled(f"H{k}", x0, 6.0, 4.6, 8, 7.5 + rng.uniform(-1, 1.5), brick if k % 2 else brick2, roof, lit=(1, 3) if variant == "harbour_dusk" else ())
        # the shop on the corner: a ground-floor window display (fenders, buoys) and a door; no lettering
        box("ShopWin", (SHOP_DOOR.x - 1.4, 5.98, 1.2), (1.6, 0.02, 1.4), pbr("ShopGlass", (0.05, 0.06, 0.07), 0.03, **{'Coat Weight': 1.0}))
        box("ShopDisp", (SHOP_DOOR.x - 1.4, 6.3, 1.2), (1.5, 0.02, 1.3), emissive("ShopLit", (1.0, 0.82, 0.6), 1.2 if variant == "harbour_dusk" else 0.4))
        c["shop_door"] = box("ShopDoor", (SHOP_DOOR.x, 5.97, 1.05), (0.95, 0.06, 2.1), pbr("ShopDoorM", (0.1, 0.18, 0.22), 0.4))
        box("Awning", (SHOP_DOOR.x - 0.7, 5.5, 2.5), (3.2, 1.0, 0.06), pbr("AwningBlue", (0.08, 0.14, 0.25), 0.6), rot=(math.radians(-12), 0, 0))
        try:
            ph.model("lifebuoy", loc=(SHOP_DOOR.x + 0.75, 5.93, 1.6), rot_z=0)
        except Exception:
            pass
        # boats bobbing at the quay
        cols = [(0.12, 0.18, 0.3), (0.7, 0.7, 0.68), (0.35, 0.08, 0.06), (0.1, 0.25, 0.2)]
        c["boats"] = [motorboat(f"Boat{k}", (-16 + k * 4.2, -3.6 - (k % 2) * 0.6, -1.0), math.radians(90 + rng.uniform(-5, 5)), cols[k % 4]) for k in range(7)]
        # a flag on a short mast at the quay
        mast = cyl("Mast", (-4.0, 0.8, 2.5), 0.04, 5.0, pbr("MastW", (0.85, 0.85, 0.85), 0.4), verts=12)
        bpy.ops.mesh.primitive_grid_add(x_subdivisions=24, y_subdivisions=16, size=1, location=(-3.55, 0.8, 4.6), rotation=(math.radians(90), 0, 0))
        fl = bpy.context.active_object; fl.scale = (0.9, 0.6, 1); fl.data.materials.append(pbr("FlagCloth", (0.12, 0.2, 0.45), 0.8))
        wv = fl.modifiers.new("wave", 'WAVE'); wv.height = 0.06; wv.width = 0.35; wv.speed = 0.12; wv.use_normal = True
        if variant == "harbour_dusk":
            import vehicles
            car = vehicles.make("sedan_modern", loc=(2.0, -0.6 + 0, 0.0), heading_deg=0, color=(0.15, 0.17, 0.2)) if False else None
            c["car"] = vehicles.make("sedan_modern", loc=(1.0, 2.0, 0.0), heading_deg=0, color=(0.14, 0.16, 0.19), lamps=False)
            o1 = B.person("Obs1", 1.0, 40, "male_casualsuit05", "short02", hue=0.6, sat=0.2, val=0.3, hair_val=0.3)
            o2 = B.person("Obs2", 0.0, 34, "female_elegantsuit01", "ponytail01", hue=0.6, sat=0.2, val=0.3, hair_val=0.25)
            B.seat(o1, (1.0 + 0.05, 2.0 - 0.38, 0.0), -math.pi / 2 + 0.0, lean=-5); B.ground(o1, 0.25)
            B.seat(o2, (1.0 + 0.05, 2.0 + 0.38, 0.0), -math.pi / 2 + 0.0, lean=-5); B.ground(o2, 0.25)
            c["obs"] = (o1, o2)
            ph.model("street_lamp_01", loc=(8.0, 5.3, 0.0), rot_z=math.radians(90))
            B.key_spot((8.0, 4.4, 5.2), (5.0, 5.5, 0.5), 2200, 60, (1.0, 0.65, 0.35), soft=0.2, name="Sodium")
        man = B.person("Seller", 1.0, 58, "male_casualsuit05", "short02", hue=0.6, sat=0.25, val=0.25, hair_val=2.0, hair_sat=0.0)
        c["man"] = man
        B.room_haze((0, 0, 4), (80, 40, 8), density=0.004, color=(0.75, 0.78, 0.82))
        if variant == "shop":                                   # the interior behind the shop front (y 6.0 .. 10)
            for o in list(bpy.data.objects):
                if o.name.startswith(("H2", "H3", "H4")) and o.location.y > 5:
                    o.hide_render = True
            box("ShopFloor", (2.5, 8.0, 0.0), (6, 4, 0.02), B.tex_mat("ShopFl", "old_wooden_floor_02", scale=0.5, tint=(0.55, 0.5, 0.45)))
            sw = B.plaster("ShopWall", (0.55, 0.55, 0.5))
            box("ShopBack", (2.5, 10.0, 1.4), (6, 0.1, 2.8), sw); box("ShopL", (-0.5, 8.0, 1.4), (0.1, 4, 2.8), sw); box("ShopR", (5.5, 8.0, 1.4), (0.1, 4, 2.8), sw)
            box("ShopCeil", (2.5, 8.0, 2.82), (6, 4, 0.04), sw)
            rope = pbr("Rope", (0.6, 0.52, 0.35), 0.85); rope2 = pbr("RopeBlue", (0.1, 0.2, 0.4), 0.85)
            fender_m = [pbr("FenderW", (0.85, 0.85, 0.82), 0.4), pbr("FenderB", (0.08, 0.15, 0.35), 0.4), pbr("FenderO", (0.8, 0.35, 0.05), 0.4)]
            for k in range(7):                                  # coils hanging on wall hooks
                bpy.ops.mesh.primitive_torus_add(major_radius=0.16, minor_radius=0.03, location=(0.3 + k * 0.5, 9.88, 1.7), rotation=(math.radians(90), 0, 0))
                bpy.context.active_object.data.materials.append(rope if k % 2 else rope2)
                cyl("Hook", (0.3 + k * 0.5, 9.93, 1.86), 0.008, 0.1, pbr("HookS", (0.5, 0.5, 0.5), 0.3, 1.0), verts=8, rot=(math.radians(90), 0, 0))
            for k in range(9):                                  # fenders hanging from a rail
                cyl("Fender", (-0.3, 6.6 + k * 0.36, 1.55), 0.09, 0.55, fender_m[k % 3], verts=24)
            box("Rail", (-0.3, 8.0, 1.86), (0.03, 3.4, 0.03), pbr("RailS", (0.5, 0.5, 0.52), 0.3, 1.0))
            ph.model("ocean_buoy", loc=(4.6, 9.4, 0.0), rot_z=0.4, scale=0.5)
            ph.model("life_jacket", loc=(4.9, 8.5, 0.9), rot_z=-1.2) if True else None
            ph.model("WoodenTable_03", loc=(3.0, 7.2, 0.0), rot_z=0.0)
            B.key_spot((SHOP_DOOR.x - 1.4, 4.5, 2.2), (2.0, 9.5, 1.2), 900, 45, (0.82, 0.88, 0.98), soft=0.6, name="ShopWinLight")
            B.practical((2.5, 8.0, 2.6), 40, (1.0, 0.75, 0.48), 0.2, "ShopBulb")
            c["coil"] = None
            bpy.ops.mesh.primitive_torus_add(major_radius=0.16, minor_radius=0.03, location=(0, 0, -30), rotation=(math.radians(90), 0, 0))
            c["coil"] = bpy.context.active_object; c["coil"].data.materials.append(rope)
            B.stand(man, (3.85, 9.3, 0.0), math.pi)        # faces the back wall (+Y)
        c["rest"] = B.capture(man)
    else:
        # the man's house: detached brick gable house behind a short front garden, a pavement and a road (y < 0)
        box("Road", (0, -5.0, 0.0), (80, 7, 0.02), B.tex_mat("Road", "asphalt_02", scale=0.25, tint=(0.45, 0.45, 0.45)))
        box("Pave", (0, 0.5, 0.06), (80, 3.0, 0.12), B.tex_mat("Pave", "concrete_pavers", scale=0.5, tint=(0.55, 0.55, 0.55)))
        box("Garden", (0, 4.0, 0.03), (80, 4.0, 0.06), B.tex_mat("Lawn", "grass_path_2" if False else "leafy_grass", scale=0.3, tint=(0.5, 0.55, 0.45)))
        box("GPath", (0, 4.0, 0.07), (1.2, 4.0, 0.03), B.tex_mat("GPathM", "concrete_pavers", scale=0.6, tint=(0.6, 0.6, 0.6)))
        gabled("House", 0.0, 6.0, 9.0, 9.0, 5.8, brick, roof, lit=(0, 2) if variant == "house_dawn" else ())
        for k in range(3):                                  # front steps up to the door
            box("Step", (0, 5.6 - k * 0.32, 0.1 + k * 0.2 - 0.0), (1.6, 0.36, 0.2 + 0.0), pbr("StepC", (0.5, 0.5, 0.49), 0.7)) if False else box("Step", (0, 5.84 - k * 0.32, (3 - k) * 0.2 / 2), (1.6, 0.34, (3 - k) * 0.2), pbr("StepC", (0.5, 0.5, 0.49), 0.7))
        c["door"] = box("HouseDoor", (0, 5.98, 0.6 + 1.05), (1.0, 0.06, 2.1), pbr("HouseDoorM", (0.25, 0.08, 0.05), 0.4))
        gabled("Neigh1", -11.5, 7.0, 8.0, 8.0, 5.5, brick2, roof, lit=(1,) if variant == "house_dawn" else ())
        gabled("Neigh2", 11.5, 7.5, 8.0, 8.0, 5.5, brick2, roof)
        hedge = B.tex_mat("Hedge", "leafy_grass", scale=0.8, tint=(0.25, 0.32, 0.2))
        for x in (-3.0, 3.0):
            box("Hedge", (x * 1.7, 2.1, 0.5), (4.6, 0.6, 1.0), hedge)
        import vehicles
        if variant == "house_day":
            c["van"] = vehicles.make("van_1990s", loc=(3.5, -2.8, 0.0), heading_deg=180, color=(0.82, 0.82, 0.8))
            c["car1"] = vehicles.make("sedan_modern", loc=(-5.5, -2.8, 0.0), heading_deg=0, color=(0.2, 0.22, 0.25))
            ev = join([box("EvBoxB", (0, 0, 0.11), (0.6, 0.42, 0.02), pbr("Card", (0.6, 0.48, 0.32), 0.85))] +
                      [box("EvBoxS", (sx * 0.29, 0, 0.2), (0.02, 0.42, 0.2), pbr("Card", (0.6, 0.48, 0.32), 0.85)) for sx in (-1, 1)] +
                      [box("EvBoxS2", (0, sy * 0.2, 0.2), (0.6, 0.02, 0.2), pbr("Card", (0.6, 0.48, 0.32), 0.85)) for sy in (-1, 1)], "EvBox")
            rec = P.reel_recorder("Carried", (0, 0, 0.12), rot_z=0.0, spin=0.0, scale=1.0)
            rec["root"].parent = ev; rec["root"].location = (0, 0, 0.12)
            c["evbox"] = ev
            c["boxes"] = [box(f"Carton{k}", (0, 0, -30), (0.5, 0.35, 0.3), pbr("Carton", (0.55, 0.42, 0.28), 0.85), bevel=0.01) for k in range(2)]
            offs = [B.person(f"Off{k}", 1.0 if k != 1 else 0.0, 30 + 8 * k, "male_casualsuit05" if k != 1 else "female_elegantsuit01",
                             "short03" if k != 1 else "ponytail01", hue=0.6, sat=0.2, val=0.3, hair_val=0.3) for k in range(3)]
            c["offs"] = offs
        else:
            c["car1"] = vehicles.make("sedan_modern", loc=(-14.0, -3.0, 0.0), heading_deg=0, color=(0.15, 0.16, 0.18), lamps=True)
            c["car2"] = vehicles.make("sedan_modern", loc=(-22.0, -3.0, 0.0), heading_deg=0, color=(0.25, 0.26, 0.28), lamps=True)
            offs = [B.person(f"Off{k}", 1.0, 32 + 6 * k, "male_casualsuit05", ["short03", "short01", "short04", "short02"][k], hue=0.6, sat=0.2, val=0.3, hair_val=0.3) for k in range(4)]
            c["offs"] = offs
            man = B.person("Arrested", 1.0, 59, "male_casualsuit03", "short02", hue=0.6, sat=0.2, val=0.35, hair_val=2.0, hair_sat=0.0)
            c["man"] = man
            ph.model("street_lamp_01", loc=(6.0, 1.6, 0.12), rot_z=math.radians(90))
            B.key_spot((6.0, 0.7, 5.2), (2.0, -1.0, 0.3), 1800, 60, (1.0, 0.65, 0.35), soft=0.2, name="Sodium")
        c["rests"] = [B.capture(h) for h in offs]
        B.room_haze((0, 0, 3), (60, 30, 6), density=0.006 if variant == "house_dawn" else 0.003, color=(0.7, 0.76, 0.88))
    return c


def drive(car, x0, x1, u):
    car.location.x = x0 + (x1 - x0) * u


def anim(c, t, move):
    sec = t * DUR[move]
    v = c["variant"]
    if v == "kitchen":
        man, off = c["man"], c["off"]
        B.apply_pose(man, c["rest"]); B.apply_pose(off, c["rests"][0])
        u = ease(min(1.0, max(0.0, (sec - 0.8) / 1.6)))
        tube = Vector((0.1, 0.75 - 0.2 * u, 0.95 - 0.05 * u))
        reach(off, "R", tube + Vector((0.0, 0.08, 0.02)), Vector((0.4, 0.5, -0.8)), Vector((0, -1, 0)))
        fingers_curl(off, 40, side=("R",)); B.nod(off, 18)
        c["tube"].location = tube; c["tube"].rotation_euler = (math.radians(90), 0, 0)
        fwd = B.fwd_of(man); side = fwd.cross(Vector((0, 0, 1))).normalized()
        for sd, sg in (("L", -1), ("R", 1)):
            reach(man, sd, man.bone_head("spine01") + fwd * 0.42 + side * (0.15 * sg) + Vector((0, 0, 0.8 - man.bone_head("spine01").z + 0.05)),
                  Vector((sg * side.x, sg * side.y, -0.8)), fwd + Vector((0, 0, -0.4)))
        fingers_curl(man, 30); B.nod(man, 6)
        bpy.context.view_layer.update()
        return
    if v.startswith("harbour"):
        for k, b in enumerate(c["boats"]):
            b.location.z = -1.0 + 0.05 * math.sin(sec * 1.1 + k * 1.3)
            b.rotation_euler = (0.03 * math.sin(sec * 0.9 + k), 0.02 * math.sin(sec * 1.3 + k * 2), b.rotation_euler.z)
        man = c["man"]
        if move == "lock":
            if sec < 2.0:
                B.stand(man, (SHOP_DOOR.x, SHOP_DOOR.y - 0.45, 0.0), math.pi)
                reach(man, "R", Vector((SHOP_DOOR.x + 0.3, 5.9, 1.05)), Vector((0.5, -0.4, -0.8)), Vector((0, 1, 0)))
                fingers_curl(man, 40, side=("R",))
            else:
                u = ease(min(1.0, (sec - 2.0) / 3.5))
                B.walk_to(man, (SHOP_DOOR.x, SHOP_DOOR.y - 0.6, 0), (SHOP_DOOR.x + 6.0, SHOP_DOOR.y - 1.2, 0), u, 5.0 * u + 0.001, stride=22, swing=14)
        else:
            B.stand(man, (0, 0, -40), 0)
        if v == "harbour_dusk":
            for h in c["obs"]:
                h.rot("head", (0, 0, 1), 4 * math.sin(sec * 0.4))
    elif v == "shop":
        man = c["man"]; B.apply_pose(man, c["rest"])
        u = ease(min(1.0, max(0.0, (sec - 0.6) / 2.0)))
        coil = c["coil"]; hook = Vector((3.8, 9.85, 1.7))
        coil.location = Vector((3.8, 9.45, 1.25)).lerp(hook, u)
        for sd, dx in (("L", -0.12), ("R", 0.12)):
            reach(man, sd, coil.location + Vector((dx, -0.08, 0.05)), Vector((dx * 4, -0.4, -0.8)), Vector((0, 1, 0.3)))
        fingers_curl(man, 40)
        if sec > 3.0:
            B.apply_pose(man, c["rest"]); B.arms_down(man)
        B.nod(man, -6)
    else:
        offs = c["offs"]
        for h, P0 in zip(offs, c["rests"]):
            B.apply_pose(h, P0)
        if v == "house_day":
            if move == "boxes":
                for k, (h, bx) in enumerate(zip(offs[:2], c["boxes"])):
                    u = ease(min(1.0, max(0.0, (sec - 0.4 - 1.6 * k) / 3.0)))
                    B.walk_to(h, (0.0 + 0.3 * k, 5.4, 0.0), (0.6 + 0.3 * k, 0.2, 0.0), u, 4.0 * u + 0.001, stride=20, swing=0)
                    fwd = B.fwd_of(h); side = fwd.cross(Vector((0, 0, 1))).normalized()
                    hold = h.bone_head("spine02") + fwd * 0.32 + Vector((0, 0, -0.12))
                    bx.location = hold + Vector((0, 0, 0.02)); bx.rotation_euler = (0, 0, math.atan2(fwd.y, fwd.x))
                    for sd, sg in (("L", -1), ("R", 1)):
                        reach(h, sd, hold + side * (0.2 * sg), Vector((sg * side.x, sg * side.y, -0.6)), fwd)
                    fingers_curl(h, 40)
                B.hide_person(offs[2]); c["evbox"].location = (0, 0, -30)
            else:
                h = offs[2]
                u = ease(min(1.0, sec / (DUR["steps"] * 0.9)))
                path = [Vector((0.0, 5.5, 0.6)), Vector((0.0, 4.6, 0.06)), Vector((1.6, 0.4, 0.12)), Vector((3.0, -1.2, 0.0))]
                seg = min(2, int(u * 3)); su = u * 3 - seg
                p = path[seg].lerp(path[seg + 1], su)
                B.walk_to(h, path[seg], path[seg + 1], su, 1.4 * su + seg * 1.4, stride=18, swing=0)
                B.ground(h, p.z)
                fwd = B.fwd_of(h); side = fwd.cross(Vector((0, 0, 1))).normalized()
                hold = h.bone_head("spine02") + fwd * 0.36 + Vector((0, 0, -0.15))
                ev = c["evbox"]; ev.location = hold + Vector((0, 0, -0.15)); ev.rotation_euler = (0, 0, math.atan2(fwd.y, fwd.x) + math.pi / 2)
                for sd, sg in (("L", -1), ("R", 1)):
                    reach(h, sd, hold + side * (0.3 * sg), Vector((sg * side.x, sg * side.y, -0.6)), fwd)
                fingers_curl(h, 40)
                for o_ in offs[:2]:
                    B.hide_person(o_)
                for bx in c["boxes"]:
                    bx.location = (0, 0, -30)
        else:
            man = c["man"]
            if move == "dawn":
                u = ease(min(1.0, sec / 2.6))
                drive(c["car1"], -14.0, -2.5, u); drive(c["car2"], -22.0, -9.0, u)
                for k, h in enumerate(offs):
                    w = ease(min(1.0, max(0.0, (sec - 2.8 - 0.25 * k) / 3.0)))
                    p0 = Vector((-2.5 + 1.2 * (k % 2) - 4.5 * (k // 2), -1.6, 0)); p1 = Vector((-0.3 + 0.6 * (k % 2) - 0.6 * (k // 2), 3.0 + 0.8 * (k // 2), 0))
                    if w <= 0:
                        B.stand(h, (0, 0, 0), 0, z=-40)
                    else:
                        B.walk_to(h, p0, p1, w, 3.0 * w, stride=22, swing=14); B.ground(h, 0.06)
                B.stand(man, (0, 0, 0), 0, z=-40)
            else:
                c["car1"].location.x = -1.5
                c["car2"].location.x = -9.0
                u = ease(min(1.0, sec / 3.4))
                p0 = Vector((0.0, 4.0, 0)); p1 = Vector((-1.2, -0.6, 0))
                B.walk_to(man, p0, p1, u, 3.0 * u + 0.001, stride=18, swing=0); B.ground(man, 0.06)
                for k, sx in ((0, -0.55), (1, 0.55)):
                    h = offs[k]
                    B.walk_to(h, p0 + Vector((sx, 0.1, 0)), p1 + Vector((sx, 0.1, 0)), u, 3.0 * u + 0.001, stride=18, swing=8); B.ground(h, 0.06)
                for h in offs[2:]:
                    B.stand(h, (-4.0 + 1.0 * offs.index(h), -1.2, 0), math.radians(10)); B.ground(h, 0.06)
                if sec > 3.6:                                  # in the car: he is out of sight, the car pulls away
                    B.stand(man, (0, 0, 0), 0, z=-40)
                    for h in offs[:2]:
                        B.stand(h, (0, 0, 0), 0, z=-40)
                    drive(c["car1"], -1.5, 14.0, ease(min(1.0, (sec - 4.0) / 2.5)) if sec > 4.0 else 0.0)
    bpy.context.view_layer.update()


def cam(a, b, tgt, lens):
    return lambda c, t: (Vector(a).lerp(Vector(b), ease(t)), Vector(tgt), lens)


def cam_quay(c, t):
    e = ease(t)
    return (Vector((-24.0, -19.0, 4.5)), Vector((-8.0 + 8.0 * e, 3.0, 2.5)), 30)


MOVES = {
    "saliva": dict(kind="anim", dof=2.8, cam=cam((-1.5, -2.7, 1.7), (-1.3, -2.4, 1.66), (0.25, 0.9, 1.1), 32),
                   anim=lambda c, t: anim(c, t, "saliva"), focus=lambda c, t: c["off"].bone_head("spine03")),
    "quay": dict(kind="anim", dof=None, cam=cam_quay, anim=lambda c, t: anim(c, t, "quay")),
    "watch": dict(kind="anim", dof=2.0, cam=cam((0.15, 2.0, 1.25), (0.3, 2.0, 1.24), (6.0, 5.0, 1.2), 32),
                  anim=lambda c, t: anim(c, t, "watch"), focus=lambda c, t: Vector((SHOP_DOOR.x, 5.8, 1.2))),
    "lock": dict(kind="anim", dof=3.2, cam=cam((-3.5, 1.2, 1.6), (-3.0, 1.4, 1.58), (SHOP_DOOR.x + 1.0, 5.5, 1.2), 35),
                 anim=lambda c, t: anim(c, t, "lock"), focus=lambda c, t: c["man"].bone_head("spine03")),
    "shop": dict(kind="anim", dof=2.8, cam=cam((0.2, 6.3, 1.7), (0.6, 6.6, 1.65), (3.9, 9.7, 1.35), 28),
                 anim=lambda c, t: anim(c, t, "shop"), focus=lambda c, t: c["man"].bone_head("spine03")),
    "boxes": dict(kind="anim", dof=4.0, cam=cam((2.6, -1.0, 1.5), (2.3, -0.6, 1.48), (0.0, 4.5, 1.4), 30),
                  anim=lambda c, t: anim(c, t, "boxes"), focus=lambda c, t: c["offs"][0].bone_head("spine03")),
    "steps": dict(kind="anim", dof=4.0, cam=cam((-3.2, -1.5, 1.6), (-2.8, -1.1, 1.58), (0.8, 3.0, 1.2), 30),
                  anim=lambda c, t: anim(c, t, "steps"), focus=lambda c, t: c["evbox"].location),
    "dawn": dict(kind="anim", dof=None, cam=cam((8.0, -7.0, 2.6), (7.0, -6.2, 2.5), (-2.0, 2.0, 1.2), 28),
                 anim=lambda c, t: anim(c, t, "dawn")),
    "away": dict(kind="anim", dof=4.0, cam=cam((0.9, 5.45, 2.1), (0.6, 5.1, 2.0), (-1.2, -1.5, 1.1), 30),
                 anim=lambda c, t: anim(c, t, "away"), focus=lambda c, t: c["man"].bone_head("spine03")),
}
