"""CH5 (chat B): after the verdict (generic buildings: no names, no crests, no readable text).
  fedcourt:  a long modern stone court building, overcast; flags moving.
             fedwide (A): wide, slow push: people on the steps, flags moving
             press   (B): a lawyer in a coat walks down the steps past press cameras
  corridor:  a long court corridor, 2013.
             walk    (A): Michael walks down the corridor carrying a folder
             wait    (B): he sits on a bench outside a courtroom door and waits; slow push
  physicist: a retired physicist's home workbench (basement window).
             listen  (A): an older man in headphones at the bench, the borrowed recorder's reels turning
             year    (B): calendar pages fall away as the window light swings across the bench (time passing)
  school:    an old boarding-school building beyond the woods; fog drifts past it (no figure: an unproven lead).
             fog     (A)
  prison:    a prison wall and a sliding steel gate at dawn, 2023.
             gate    (A): the gate slides open; a man walks out, seen from behind
             wall    (B): wide: he walks away along the long wall into the haze
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
DUR = {"fedwide": 5.5, "press": 5.5, "walk": 6.0, "wait": 5.5, "listen": 5.5, "year": 7.0, "fog": 6.0, "gate": 6.5, "wall": 6.5}
VARIANT_FOR = {"fedwide": "fedcourt", "press": "fedcourt", "walk": "corridor", "wait": "corridor", "listen": "physicist",
               "year": "physicist", "fog": "school", "gate": "prison", "wall": "prison"}


def sky(kind):
    try:
        import rj
        rj.sky(kind)
    except Exception:
        world_flat((0.3, 0.33, 0.36), 1.0)


def press_camera(name, loc, rot_z):
    dark = pbr(name + "M", (0.04, 0.04, 0.045), 0.4)
    parts = [box("TV", (0, 0, 1.55), (0.14, 0.42, 0.22), dark, bevel=0.02), cyl("TVLens", (0, -0.27, 1.55), 0.05, 0.14, dark, verts=20, rot=(math.radians(90), 0, 0))]
    for k in range(3):
        a = k * 2 * math.pi / 3
        b_ = cyl("Leg", (0.25 * math.cos(a), 0.25 * math.sin(a), 0.72), 0.012, 1.5, pbr("LegM", (0.2, 0.2, 0.2), 0.4, 0.8), verts=8)
        b_.rotation_euler = (math.radians(9) * math.sin(a), -math.radians(9) * math.cos(a), 0)
        parts.append(b_)
    o = join(parts, name); o.location = loc; o.rotation_euler = (0, 0, rot_z)
    return o


def build(variant=None):
    variant = variant or "fedcourt"
    c = {"variant": variant}
    rng = np.random.default_rng(55)
    if variant == "fedcourt":
        sky("grey")
        bpy.context.scene.view_settings.exposure += 0.6
        stone = B.tex_mat("Stone", "concrete_wall_006", scale=0.25, tint=(1.15, 1.08, 0.95))
        box("Plaza", (0, -6, -0.05), (80, 30, 0.1), B.tex_mat("PlazaM", "granite_tile", scale=0.3, tint=(0.6, 0.6, 0.6)))
        for k in range(8):                                   # broad steps up to the entrance
            box("Step", (0, 1.0 + k * 0.4, 0.08 + k * 0.16), (24, 0.4 + (7 - k) * 0.0, 0.16), stone)
        box("Building", (0, 12.0, 6.5), (44, 16, 13), stone)
        for k in range(15):                                  # tall window bays (dark glass) between stone piers
            x = -19.6 + k * 2.8
            box("Bay", (x, 3.98, 6.9), (1.6, 0.06, 10.0), pbr("BayGlass", (0.02, 0.025, 0.03), 0.06, **{'Coat Weight': 1.0}))
        box("Canopy", (0, 3.0, 4.5), (12, 2.5, 0.3), stone)
        # depth: stone piers proud of the glass bays, floor bands, a cornice, canopy columns and a glazed entrance
        for k in range(16):
            box("Pier", (-21.0 + k * 2.8, 3.62, 6.5), (1.0, 0.75, 13.0), stone)
        for z in (4.25, 7.6, 10.9):
            box("Band", (0, 3.72, z), (44.2, 0.55, 0.45), stone)
        box("Cornice", (0, 3.5, 13.2), (45.0, 1.1, 0.55), stone)
        metal = pbr("DoorMetal", (0.1, 0.1, 0.11), 0.35, 0.9)
        try:
            import rj
            eg = rj.window_glass()
        except Exception:
            eg = pbr("EntGlass", (0.02, 0.025, 0.03), 0.04, **{'Coat Weight': 1.0})
        box("EntGlass", (0, 3.92, 2.8), (6.0, 0.04, 2.9), eg)
        for x in (-3.0, -1.5, 0.0, 1.5, 3.0):
            box("EntMull", (x, 3.88, 2.8), (0.08, 0.1, 2.9), metal)
        box("EntHead", (0, 3.88, 4.2), (6.1, 0.12, 0.12), metal)
        for x in (-5.5, -2.0, 2.0, 5.5):
            cyl("CanCol", (x, 2.0, 2.85), 0.16, 3.2, stone, verts=20)
        for k in range(2):                                    # low planters either side of the steps
            box("Planter", ((-1 if k else 1) * 13.5, 0.2, 0.4), (3.0, 1.6, 0.8), stone)
        try:
            import rj
            rj.low_instances("birch", [((sx * (12.5 + 4.2 * j), -5.0 - 2.5 * (j % 2), 0), 0.7 * j + sx, 1.0 + 0.1 * j) for sx in (-1, 1) for j in range(3)])
        except Exception as e:
            print("[fedcourt] trees", e)
        c["flags"] = []
        for x in (-8, -6, 6, 8):
            cyl("Pole", (x, -1.5, 4.5), 0.05, 9.0, pbr("PoleS", (0.8, 0.8, 0.82), 0.25, 1.0), verts=12)
            bpy.ops.mesh.primitive_grid_add(x_subdivisions=30, y_subdivisions=20, size=1, location=(x + 0.8, -1.5, 8.0), rotation=(math.radians(90), 0, 0))
            f = bpy.context.active_object; f.scale = (1.5, 1.0, 1); f.data.materials.append(fabric("FlagCloth" + str(x), (0.22, 0.05, 0.04) if x < 0 else (0.05, 0.08, 0.2), 0.9, 0.4, 260))
            f["base"] = [tuple(v.co) for v in f.data.vertices]
            c["flags"].append(f)
        B.key_sun(18, 200, 3.0, color=(1.0, 0.85, 0.7), angle=3.0)
        people = []
        for k in range(6):
            h = B.person(f"Step{k}", 1.0 if k % 2 else 0.0, 30 + 6 * k, "male_elegantsuit01" if k % 2 else "female_elegantsuit01", ["short02", "bob01", "short04", "long01", "short01", "ponytail01"][k],
                         hue=0.6, sat=0.2, val=0.3, hair_val=0.35)
            people.append(h)
        c["people"] = people
        law = B.person("Lawyer", 1.0, 52, "male_elegantsuit01", "short04", hue=0.6, sat=0.2, val=0.2, hair_val=1.0, hair_sat=0.2)
        c["lawyer"] = law
        c["presscams"] = [press_camera(f"Press{k}", (-3.5 + k * 1.6, -2.6 - 0.4 * (k % 2), 0), math.radians(180 + (k - 2) * 8)) for k in range(5)]
        crew = []
        for k in range(3):
            h = B.person(f"Crew{k}", 1.0 if k != 1 else 0.0, 28 + 5 * k, "male_casualsuit05" if k != 1 else "female_elegantsuit01", ["short03", "ponytail01", "short01"][k],
                         hue=0.55, sat=0.25, val=0.35, hair_val=0.3)
            B.stand(h, (-2.7 + k * 3.2, -3.3, 0), math.pi + 0.1 * (k - 1)); crew.append(h)
        c["crew"] = crew
        B.room_haze((0, 0, 5), (60, 40, 10), density=0.003, color=(0.8, 0.82, 0.85))
    elif variant == "corridor":
        world_flat((0.006, 0.007, 0.01), 1.0)
        box("CFloor", (0, 0, -0.01), (3.2, 30, 0.02), B.tex_mat("CorFl", "marble_tiles" if False else "granite_tile_02", scale=0.4, tint=(0.55, 0.55, 0.55)))
        wall = B.plaster("CorW", (0.62, 0.6, 0.55), dirt=0.08)
        box("CWallL", (-1.6, 0, 1.75), (0.1, 30, 3.5), wall); box("CCeil", (0, 0, 3.52), (3.2, 30, 0.05), wall)
        # right wall: tall windows with low winter sun raking across the floor
        for k in range(10):
            y = -13 + k * 3.0
            box("CPier", (1.6, y, 1.75), (0.1, 1.6, 3.5), wall)
        box("CWinLo", (1.6, 0, 0.45), (0.1, 30, 0.9), wall); box("CWinHi", (1.6, 0, 3.3), (0.1, 30, 0.4), wall)
        sk = box("COut", (5, 0, 2), (0.05, 40, 5), emissive("COutM", (0.85, 0.82, 0.75), 0.8)); sk.visible_shadow = False
        B.key_sun(16, -10, 9.0, color=(1.0, 0.75, 0.5), angle=0.6)
        oak = B.tex_mat("COak", "oak_veneer_01", scale=0.8, tint=(0.7, 0.55, 0.4))
        for k in range(4):
            y = -9 + k * 6.0
            box("CDoor", (-1.56, y, 1.2), (0.06, 1.3, 2.4), oak)
            box("CDoorFrame", (-1.55, y, 2.45), (0.08, 1.45, 0.1), oak)
        for y in (-7.0, -1.0, 5.0):
            box("Bench", (-1.3, y, 0.23), (0.45, 1.8, 0.06), oak); box("BenchLeg", (-1.3, y, 0.11), (0.4, 1.7, 0.2), pbr("BLeg", (0.2, 0.2, 0.2), 0.4, 0.8))
        mic = B.michael("Michael13", 51)
        c["m"] = mic
        c["folder"] = box("Folder", (0, 0, -30), (0.03, 0.24, 0.32), pbr("FolderBlue", (0.08, 0.12, 0.25), 0.6))
        B.room_haze((0, 0, 1.75), (3.0, 29, 3.4), density=0.02, color=(0.95, 0.92, 0.88))
    elif variant == "physicist":
        world_flat((0.005, 0.006, 0.008), 1.0)
        box("PFloor", (0, 0, -0.01), (5, 4, 0.02), B.tex_mat("PFl", "concrete_floor_02", scale=0.5, tint=(0.5, 0.5, 0.48)))
        wall = B.plaster("PWall", (0.5, 0.48, 0.44), dirt=0.3)
        box("PWallB", (0, 1.8, 1.25), (5, 0.1, 2.5), wall); box("PWallL", (-2.5, 0, 1.25), (0.1, 4, 2.5), wall); box("PWallR", (2.5, 0, 1.25), (0.1, 4, 2.5), wall)
        box("PCeil", (0, 0, 2.52), (5, 4, 0.04), wall)
        # high basement window in the back wall (left of the bench)
        box("PWinHole", (-1.2, 1.82, 2.1), (0.9, 0.12, 0.45), emissive("PWin", (0.85, 0.85, 0.8), 0.8))
        ph.model("WoodenTable_03", loc=(0.3, 1.35, 0), rot_z=0)
        c["rec"] = P.reel_recorder("Borrowed", (0.15, 1.38, 0.83), rot_z=0.05, spin=0.35)
        ph.model("retro_multimeter", loc=(0.75, 1.45, 0.83), rot_z=-0.4)
        ph.model("classic_laptop", loc=(-0.3, 1.3, 0.83), rot_z=0.3, scale=0.55)
        for k in range(4):
            B.sheet("Note", (0.55 + 0.05 * k, 1.15 + 0.02 * k, 0.832 + 0.001 * k), (0.21, 0.297), B.paper_mat("PNote", (0.88, 0.87, 0.82)), rot=(0, 0, 0.2 * k))
        # the wall calendar: a stack of 12 month pages (blank grids, no text) that fall away one by one (frame drivers)
        cal_m = B.paper_mat("CalPage", (0.9, 0.89, 0.85), lines=True)
        c["pages"] = []
        for k in range(12):
            pg = B.sheet(f"Cal{k}", (0, 0, 0), (0.3, 0.42), cal_m)
            pv = bpy.data.objects.new(f"CalHinge{k}", None); bpy.context.collection.objects.link(pv)
            pv.location = (1.4, 1.74 - 0.001 * k, 1.85); pg.parent = pv; pg.location = (0, 0, -0.21); pg.rotation_euler = (math.radians(90), 0, 0)
            t0 = 14 + k * 12
            d = pv.driver_add("rotation_euler", 0).driver; d.type = 'SCRIPTED'
            d.expression = f"-min(1, max(0, (frame - {t0}) / 6)) * 2.9"
            d2 = pv.driver_add("location", 2).driver; d2.type = 'SCRIPTED'
            d2.expression = f"1.85 - 3.0 * min(1, max(0, (frame - {t0} - 6) / 10))"
            c["pages"].append(pv)
        # the window light swings from summer (high, warm) to winter (low, cold) over the shot (frame-driven sun)
        sd = bpy.data.lights.new("SeasonSun", 'SUN'); sd.energy = 6.0; sd.angle = math.radians(1.0)
        so = bpy.data.objects.new("SeasonSun", sd); bpy.context.collection.objects.link(so)
        so.rotation_euler = (math.radians(40), 0, math.radians(200))
        d = so.driver_add("rotation_euler", 2).driver; d.type = 'SCRIPTED'; d.expression = "radians(200) - 0.9 * min(1, frame / 160)"
        d = so.driver_add("rotation_euler", 0).driver; d.type = 'SCRIPTED'; d.expression = "radians(40) + 0.35 * min(1, frame / 160)"
        for i, ex in enumerate(("1.0", "0.8 - 0.1 * min(1, frame / 160)", "0.6 + 0.3 * min(1, frame / 160)")):
            dd = sd.driver_add("color", i).driver; dd.type = 'SCRIPTED'; dd.expression = ex
        B.practical((0.7, 1.1, 1.5), 30, (1.0, 0.75, 0.5), 0.1, "BenchLamp")
        ph.model("desk_lamp_arm_01", loc=(0.75, 1.5, 0.83), rot_z=math.radians(-150))
        old = B.person("Physicist", 1.0, 70, "male_casualsuit05", "short02", hue=0.08, sat=0.3, val=0.4, hair_val=2.4, hair_sat=0.0)
        B.seat(old, (0.15, 0.7, 0), math.pi, lean=14)
        ph.model("dining_chair_02", loc=(0.15, 0.62, 0), rot_z=math.pi)
        c["old"] = old; c["phones"] = P.headphones(old); c["rest"] = B.capture(old)
        B.room_haze((0, 0, 1.25), (4.8, 3.8, 2.5), density=0.02)
    elif variant == "school":
        sky("mist")
        box("Ground", (0, 0, -0.05), (200, 200, 0.1), B.tex_mat("Meadow", "leafy_grass", scale=0.15, tint=(0.4, 0.45, 0.38)))
        box("Drive", (0, -10, 0.0), (3.5, 60, 0.03), B.tex_mat("DriveG", "gravel_road", scale=0.2, tint=(0.55, 0.53, 0.5)))
        plaster = B.tex_mat("SchoolPl", "grey_plaster_02", scale=0.3, tint=(0.8, 0.77, 0.7))
        roof = B.tex_mat("SchoolRoof", "grey_roof_tiles", scale=0.3, tint=(0.35, 0.33, 0.33))
        box("SchoolMain", (0, 30, 6), (34, 12, 12), plaster)
        bpy.ops.mesh.primitive_cylinder_add(vertices=3, radius=8.0, depth=34.4, location=(0, 30, 15), rotation=(0, math.radians(90), 0))
        r = bpy.context.active_object; r.rotation_euler = (math.radians(30), math.radians(90), 0); r.scale = (0.7, 1, 1); r.data.materials.append(roof)
        box("Tower", (0, 23.5, 10), (5, 3, 20), plaster)
        fr = pbr("SWin", (0.03, 0.035, 0.04), 0.1, **{'Coat Weight': 1.0})
        for fl in range(3):
            for k in range(12):
                box("SWinB", (-15 + k * 2.7, 23.95, 2.5 + fl * 3.3), (1.1, 0.05, 1.8), fr)
        B.ph_instances("fir_tree_01", [((sx * (6 + 9 * k) + rng.uniform(-2, 2), -6 + rng.uniform(-8, 14), 0), rng.uniform(0, 6), 0.6) for sx in (-1, 1) for k in range(4)])
        c["fogbank"] = B.room_haze((0, 18, 4), (60, 12, 8), density=0.05, color=(0.85, 0.87, 0.9))   # a drifting bank of fog
        B.room_haze((0, 10, 6), (120, 90, 14), density=0.03, color=(0.82, 0.85, 0.88))
    else:   # prison
        sky("mist")
        box("Ground", (0, 0, -0.05), (200, 200, 0.1), B.tex_mat("Tarmac", "asphalt_02", scale=0.2, tint=(0.45, 0.45, 0.45)))
        box("Verge", (0, -40.0, 0.0), (200, 64, 0.04), B.tex_mat("VergeG", "leafy_grass", scale=0.2, tint=(0.4, 0.45, 0.38)))
        concrete = B.tex_mat("WallConc", "concrete_wall_008", scale=0.2, tint=(0.62, 0.62, 0.6))
        box("PWallA", (-26.0, 4.0, 3.0), (48, 0.6, 6.0), concrete); box("PWallB", (26.0, 4.0, 3.0), (48, 0.6, 6.0), concrete)
        box("GatePier", (-2.4, 4.0, 3.4), (0.8, 1.0, 6.8), concrete); box("GatePier2", (2.4, 4.0, 3.4), (0.8, 1.0, 6.8), concrete)
        box("CopingA", (-26.0, 4.0, 6.1), (48.2, 0.95, 0.22), concrete); box("CopingB", (26.0, 4.0, 6.1), (48.2, 0.95, 0.22), concrete)
        razor = pbr("Razor", (0.55, 0.56, 0.58), 0.25, 1.0)
        brk = pbr("Bracket", (0.2, 0.21, 0.22), 0.5, 0.8)
        for (x0, x1) in ((-50.0, -2.0), (2.0, 50.0)):
            for x in np.arange(x0, x1, 3.0):                  # cranked steel brackets carrying the coil
                box("Brk", (x, 4.0, 6.55), (0.05, 0.05, 0.7), brk)
            cu = bpy.data.curves.new("RazorC", 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = 0.006; cu.bevel_resolution = 1
            sp = cu.splines.new('POLY'); n = int((x1 - x0) / 0.12) * 10
            sp.points.add(n - 1)
            for i in range(n):
                a_ = i / 10 * 2 * math.pi; xx = x0 + i / 10 * 0.12
                sp.points[i].co = (xx, 4.0 + 0.32 * math.cos(a_), 6.62 + 0.32 * math.sin(a_), 1)
            ob = bpy.data.objects.new("RazorWire", cu); bpy.context.collection.objects.link(ob); ob.data.materials.append(razor)
        # a watchtower on the wall line, a lamp post by the road, the road with its markings, verge, distant trees
        box("TowerShaft", (-16.0, 4.6, 5.0), (2.4, 2.4, 10.0), concrete)
        box("TowerCab", (-16.0, 4.6, 11.2), (3.6, 3.6, 2.4), concrete)
        box("TowerGlass", (-16.0, 4.6, 11.4), (3.65, 3.65, 1.1), pbr("TowerG", (0.03, 0.035, 0.04), 0.05, **{'Coat Weight': 1.0}))
        box("TowerRoof", (-16.0, 4.6, 12.55), (4.4, 4.4, 0.3), pbr("TowerRoofM", (0.2, 0.2, 0.21), 0.6))
        cyl("TowerLight", (-14.0, 2.8, 12.0), 0.18, 0.3, pbr("TL", (0.3, 0.3, 0.3), 0.3, 0.9), verts=16, rot=(math.radians(90), 0, 0))
        try:
            B.ph_instances("street_lamp_01", [((7.0, -1.6, 0.0), math.radians(90), 1.0), ((-9.0, -1.6, 0.0), math.radians(90), 1.0)])
        except Exception as e:
            print("[prison] lamp", e)
        white = pbr("RoadLine", (0.75, 0.75, 0.72), 0.6)
        for x in np.arange(-60, 60, 6.0):
            box("Dash", (x, -4.5, 0.002), (3.0, 0.12, 0.004), white)
        box("EdgeLine", (0, -7.6, 0.002), (200, 0.12, 0.004), white)
        box("KerbP", (0, 2.6, 0.07), (200, 0.2, 0.14), pbr("KerbPM", (0.45, 0.45, 0.44), 0.7))
        box("WallVerge", (0, 3.2, 0.03), (200, 1.0, 0.04), B.tex_mat("VergeW", "leafy_grass", scale=0.2, tint=(0.42, 0.48, 0.38)))
        try:
            import rj
            rj.low_instances("fir_a", [((x, 26.0 + 5 * ((k * 7) % 3), 0), k * 0.9, 1.4 + 0.2 * (k % 3)) for k, x in enumerate(np.arange(-60, 60, 7.0))])
            rj.low_instances("fir_a", [((x + 2.0 * (j % 2), -62.0 - 6.0 * j, 0), k * 1.3 + j, 1.3 + 0.15 * ((k + j) % 3)) for k, x in enumerate(np.arange(-70, 70, 5.0)) for j in range(2)])
        except Exception as e:
            print("[prison] trees", e)
        steel = pbr("GateSteel", (0.22, 0.24, 0.26), 0.45, 0.8)
        gate = join([box("GateLeaf", (0, 0, 2.6), (4.0, 0.12, 5.2), steel)] + [box("GateRib", (-1.8 + k * 0.45, -0.07, 2.6), (0.06, 0.04, 5.2), steel) for k in range(9)], "Gate")
        gate.location = (0, 3.55, 0); c["gate"] = gate
        box("YardWallL", (-3.0, 8.0, 3.0), (0.4, 8.0, 6.0), concrete); box("YardWallR", (3.0, 8.0, 3.0), (0.4, 8.0, 6.0), concrete)
        ph.model("security_light", loc=(2.4, 3.45, 5.6), rot_z=math.pi) if True else None
        B.key_sun(4, 75, 4.0, color=(1.0, 0.62, 0.35), angle=1.5)             # low dawn sun along the wall
        man = B.mazurek("Released", 2023)
        yl = area_light((0.0, 8.0, 5.5), (0, 0, 0), 4.0, 120, (0.75, 0.8, 0.9)); yl.visible_camera = False   # soft yard skylight
        c["man"] = man
        c["bag"] = box("Holdall", (0, 0, -30), (0.5, 0.25, 0.28), pbr("Holdall", (0.08, 0.08, 0.09), 0.6), bevel=0.06)
        B.room_haze((0, 0, 4), (120, 60, 8), density=0.01, color=(0.85, 0.82, 0.8))
    if variant in ("fedcourt",):
        B.finish_exterior(azim=323, elev=18, sun_energy=8.0, exposure=0.4)
    elif variant == "prison":
        B.finish_exterior(azim=72, elev=4, sun_energy=6.0, exposure=0.6,
                          sky=dict(horizon=(0.62, 0.48, 0.38), zenith=(0.03, 0.07, 0.22), ground=(0.05, 0.05, 0.05), mid=(0.14, 0.18, 0.34)))   # dawn: warm horizon, blue above                 # low warm dawn sun along the wall
    elif variant in ("corridor", "physicist"):
        B.finish_interior(lift=0.0)
    else:
        B.preview_cap()
    return c


def carry_bag(c, h):
    side = B.fwd_of(h).cross(Vector((0, 0, 1))).normalized()
    hand = h.bone_head("upperarm01.R") + Vector((0, 0, -0.62)) + side * 0.06
    c["bag"].location = hand + Vector((0, 0, -0.17))
    c["bag"].rotation_euler = (0, 0, math.atan2(B.fwd_of(h).y, B.fwd_of(h).x))


def anim(c, t, move):
    sec = t * DUR[move]
    v = c["variant"]
    if v == "fedcourt":
        for k, f in enumerate(c["flags"]):                    # cloth: travelling ripples that grow away from the pole, a slight droop
            for vt, (bx, by, bz) in zip(f.data.vertices, f["base"]):
                d = bx + 0.5                                  # 0 at the pole edge .. 1 at the fly end
                vt.co = (bx - 0.03 * d * d, by - 0.06 * d * d, 0.16 * d * math.sin(7.0 * d - 3.2 * sec - k) + 0.05 * d * math.sin(15.0 * d + 0.9 * by * 6 - 5.0 * sec))
            f.data.update()
        for k, h in enumerate(c["people"]):
            u = ((sec * 0.18 + k * 0.17) % 1.0)
            x0 = -9 + k * 3.2; up = k % 2 == 0
            p0 = Vector((x0, 1.0 if up else 3.6, 0)); p1 = Vector((x0 + 0.6, 3.6 if up else 1.0, 0))
            B.walk_to(h, p0, p1, u, 3.0 * u, stride=16, swing=10)
            y = h.arm.location.y; B.ground(h, max(0.0, min(8, int((y - 0.8) / 0.4) + 1)) * 0.16)
        law = c["lawyer"]
        u = ease(min(1.0, sec / DUR[move]))
        B.walk_to(law, (1.0, 3.6, 0), (0.0, -1.5, 0), u, 4.5 * u + 0.001, stride=22, swing=12)
        y = law.arm.location.y; B.ground(law, max(0.0, min(8, int((y - 0.8) / 0.4) + 1)) * 0.16)
        for k, h in enumerate(c["crew"]):
            h.rot("head", (0, 0, 1), 8 * math.sin(sec * 0.5 + k))
    elif v == "corridor":
        m = c["m"]
        if move == "walk":
            u = sec / DUR[move]
            B.walk_to(m, (0.1, -12.0, 0), (-0.1, 0.5, 0), u, 7.5 * u, stride=22, swing=6)
        else:
            B.seat(m, (-1.15, -1.0, 0), math.pi / 2, lean=10); B.ground(m, 0.0)
            B.nod(m, 10 + 3 * math.sin(sec * 0.4))
        fwd = B.fwd_of(m); side = fwd.cross(Vector((0, 0, 1))).normalized()
        hand = m.bone_head("upperarm01.L") + Vector((0, 0, -0.55)) - side * 0.12 + fwd * 0.05
        reach(m, "L", hand, Vector((0, 0, -1)), fwd)
        fingers_curl(m, 45, side=("L",))
        f = c["folder"]; f.location = m.bone_tail("wrist.L") + Vector((0, 0, -0.05)) - side * 0.03
        f.rotation_euler = (0, 0, math.atan2(fwd.y, fwd.x) - math.pi / 2)
        if move == "wait":
            f.location = m.arm.location + Vector((0.0, 0.0, 0.0)) + Vector((-0.05, 0.35, 0.3)); f.rotation_euler = (math.radians(90), 0, 0)
    elif v == "physicist":
        old = c["old"]; B.apply_pose(old, c["rest"])
        fwd = B.fwd_of(old); side = fwd.cross(Vector((0, 0, 1))).normalized()
        knob = Vector((0.15, 1.2, 0.98))
        reach(old, "R", knob + Vector((0.05, -0.05, 0.03)), Vector((0.6, -0.4, -0.6)), fwd + Vector((0, 0, -0.5)))
        reach(old, "L", Vector((-0.2, 1.1, 0.88)), Vector((-0.6, -0.4, -0.6)), fwd + Vector((0, 0, -0.5)))
        fingers_curl(old, 30); B.nod(old, 16 + 3 * math.sin(sec * 0.5))
    elif v == "school":
        u = sec / DUR[move]
        c["fogbank"].location.x = -12.0 + 24.0 * u                 # fog drifts past the building; no one on the drive
    else:
        man = c["man"]
        op = ease(min(1.0, sec / 2.2)) if move == "gate" else 1.0
        c["gate"].location.x = 0.7 + 3.5 * op          # ajar at the start: dawn light already in the gap
        if move == "gate":
            u = min(1.0, max(0.0, (sec - 1.4) / (DUR[move] - 1.4)))
            B.walk_to(man, (0.0, 6.6, 0), (0.6, -3.5, 0), u, 6.0 * u + 0.001, stride=20, swing=10)
        else:
            u = sec / DUR[move]
            B.walk_to(man, (1.5, 3.0, 0), (-14.0, 3.0, 0), u, 9.0 * u, stride=20, swing=10)
        carry_bag(c, man)
    bpy.context.view_layer.update()


def cam(a, b, tgt, lens):
    return lambda c, t: (Vector(a).lerp(Vector(b), ease(t)), Vector(tgt), lens)


MOVES = {
    "fedwide": dict(kind="anim", dof=None, cam=cam((-7.0, -24.0, 1.8), (-6.0, -21.0, 2.0), (0.0, 6.0, 6.0), 26), anim=lambda c, t: anim(c, t, "fedwide")),
    "press": dict(kind="anim", dof=4.0, cam=cam((5.0, -6.5, 1.7), (4.4, -5.9, 1.65), (0.0, 1.0, 1.4), 35),
                  anim=lambda c, t: anim(c, t, "press"), focus=lambda c, t: c["lawyer"].bone_head("spine03")),
    "walk": dict(kind="anim", dof=4.0, cam=cam((0.3, 3.5, 1.6), (0.2, 2.6, 1.6), (0.0, -8.0, 1.3), 35),
                 anim=lambda c, t: anim(c, t, "walk"), focus=lambda c, t: c["m"].bone_head("spine03")),
    "wait": dict(kind="anim", dof=2.8, cam=cam((1.1, 2.2, 1.45), (0.9, 1.2, 1.4), (-1.2, -1.0, 1.0), 35),
                 anim=lambda c, t: anim(c, t, "wait"), focus=lambda c, t: c["m"].bone_head("head")),
    "listen": dict(kind="anim", dof=2.8, cam=cam((1.6, -0.9, 1.55), (1.3, -0.6, 1.5), (0.1, 1.2, 1.15), 32),
                   anim=lambda c, t: anim(c, t, "listen"), focus=lambda c, t: c["old"].bone_head("head")),
    "year": dict(kind="anim", dof=2.8, cam=cam((-1.4, -1.2, 1.7), (-1.1, -0.9, 1.68), (1.0, 1.6, 1.35), 30),
                 anim=lambda c, t: anim(c, t, "year"), focus=lambda c, t: Vector((1.2, 1.7, 1.5))),
    "fog": dict(kind="anim", dof=None, cam=cam((1.8, -16.0, 1.7), (1.4, -13.5, 1.75), (0.0, 25.0, 6.0), 32), anim=lambda c, t: anim(c, t, "fog")),
    "gate": dict(kind="anim", dof=4.0, cam=cam((0.5, 10.5, 1.7), (0.4, 9.6, 1.68), (0.0, -6.0, 1.5), 32),
                 anim=lambda c, t: anim(c, t, "gate"), focus=lambda c, t: c["man"].bone_head("spine03")),
    "wall": dict(kind="anim", dof=None, cam=cam((10.0, -12.0, 1.8), (9.0, -11.6, 1.8), (-14.0, 2.0, 4.2), 30), anim=lambda c, t: anim(c, t, "wall")),
}
