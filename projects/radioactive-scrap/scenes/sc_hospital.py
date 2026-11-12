"""The large Istanbul hospital (January 1999) and the small local clinic (December 1998).

Areas (one set, separate rooms): hospital exterior with front steps and car park; a long corridor with benches,
the nurses' station and the theatre doors; a ward of iron beds with daylight windows; a small lab; a doctor's
office with a film lightbox; an operating theatre; and the local clinic with cots and drips (night).
Real people appear as unnamed figures. No injuries, no hand close-ups: medium shots with the person in frame.
"""
import math
import numpy as np
import bpy
from mathutils import Vector, Euler
from kit import *
from rs_kit import *
from rs_env import sky, periphery, facade_material
from human import reset_pose, pose_walk, reach, fingers_curl, pose_sit
from durs import dur

EXPOSURE = 0.0
BOUNCES = 8
EXT = Vector((0.0, 60.0, 0))          # hospital block centre (front face at y = 52)
COR = Vector((-40.0, 0.0, 0))         # corridor centre (runs along X, 28 m)
WARD = Vector((0.0, 0.0, 0))
LAB = Vector((25.0, 0.0, 0))
OFFICE = Vector((40.0, 0.0, 0))
OR_ = Vector((55.0, 0.0, 0))
CLINIC = Vector((-80.0, 0.0, 0))
BEDS = [Vector((-5.2 + k * 2.6, 2.6, 0)) for k in range(5)]      # bed centres along the ward's north wall (heads north)


def iron_bed(name, ctr, rot_z=0.0):
    """1990s hospital bed: white-painted iron frame, mattress, sheet and a grey wool blanket."""
    iron = painted_steel(name + "Iron", (0.75, 0.75, 0.72), 0.45, 0.35)
    parts = [box("Mattress", (0, 0, 0.6), (0.9, 1.95, 0.16), fabric(name + "Sheet", (0.82, 0.82, 0.78), 0.9, 0.3, 500), bevel=0.04)]
    for sy in (-1, 1):
        parts.append(box("Rail", (0.0, sy * 1.0, 0.75 if sy > 0 else 0.62), (0.95, 0.04, 0.04), iron))
        for sx in (-1, 1):
            parts.append(cyl("Leg", (sx * 0.45, sy * 1.0, 0.45 if sy > 0 else 0.35), 0.02, 0.9 if sy > 0 else 0.7, iron, verts=8))
        for k in range(5):
            parts.append(cyl("Spindle", (-0.36 + k * 0.18, sy * 1.0, 0.75 if sy > 0 else 0.56), 0.008, 0.3 if sy > 0 else 0.16, iron, verts=6))
    parts.append(box("Frame", (0, 0, 0.5), (0.9, 1.95, 0.05), iron))
    o = join(parts, name); o.location = ctr; o.rotation_euler = (0, 0, rot_z)
    return o


def blanket(name, ctr, rot_z=0.0, col=(0.38, 0.38, 0.4), length=1.4, z=0.72, thick=0.12):
    b = box(name, (0, 0, 0), (0.98, length, thick), fabric(name + "W", col, 0.95, 0.5, 300), bevel=min(0.09, thick * 0.45))
    b.location = Vector(ctr) + Vector((0, 0, z)); b.rotation_euler = (0, 0, rot_z)
    return b


def drip_stand(name, loc, bag_col=(0.9, 0.92, 0.9), fill=0.8):
    steel = pbr(name + "Steel", (0.7, 0.7, 0.7), 0.3, 0.9)
    parts = [cyl("DPole", (0, 0, 0.95), 0.012, 1.9, steel, verts=8), box("DHook", (0, 0, 1.9), (0.3, 0.012, 0.012), steel)]
    for k in range(4):
        a = k / 4 * 2 * math.pi; parts.append(box("DFoot", (0.14 * math.cos(a), 0.14 * math.sin(a), 0.02), (0.28, 0.03, 0.02), steel, rot=(0, 0, a)))
    st = join(parts, name); st.location = loc
    bag = box(name + "Bag", (0, 0, 0), (0.12, 0.03, 0.18), pbr(name + "BagM", bag_col, 0.15, 0.0, **{'Transmission Weight': 0.5}), bevel=0.02)
    bag.location = Vector(loc) + Vector((0.12, 0, 1.72))
    line = cyl(name + "Line", Vector(loc) + Vector((0.12, 0, 1.25)), 0.003, 0.8, pbr("Line", (0.9, 0.9, 0.9), 0.1, 0.0, **{'Transmission Weight': 0.8}), verts=6)
    return st, bag


def rotary_phone(loc, rot_z=0.0):
    blk = pbr("Bakelite", (0.03, 0.03, 0.03), 0.25, 0.0, **{'Coat Weight': 0.6})
    base = join([box("PhoneBase", (0, 0, 0.05), (0.2, 0.22, 0.1), blk, bevel=0.03),
                 cyl("Dial", (0, -0.05, 0.105), 0.055, 0.01, pbr("DialFace", (0.8, 0.78, 0.7), 0.4), verts=24)], "Phone")
    base.location = loc; base.rotation_euler = (0, 0, rot_z)
    hs = join([box("HSGrip", (0, 0, 0), (0.2, 0.04, 0.035), blk, bevel=0.012), box("HSEar", (-0.1, 0, -0.02), (0.05, 0.06, 0.05), blk, bevel=0.015),
               box("HSMouth", (0.1, 0, -0.02), (0.05, 0.06, 0.05), blk, bevel=0.015)], "Handset")
    hs.location = Vector(loc) + Vector((0, 0, 0.14)); hs.rotation_euler = (0, 0, rot_z)
    return base, hs


def cloth_blanket(name, ctr, col, rot_z=0.0, w=1.12, l=1.42, foot=-1.0, nx=24, ny=34):
    """A thin wool blanket as a dense grid; drape_blankets() lays it over whatever lies in the bed (ray-cast),
    so the body shape shows through, the sides fall over the mattress edge, with a turned-down sheet at the chest."""
    import bmesh
    bm = bmesh.new(); vs = []
    for j in range(ny + 1):
        row = []
        for i in range(nx + 1):
            row.append(bm.verts.new((-w / 2 + w * i / nx, foot + l * j / ny, 0.0)))
        vs.append(row)
    for j in range(ny):
        for i in range(nx):
            bm.faces.new((vs[j][i], vs[j][i + 1], vs[j + 1][i + 1], vs[j + 1][i]))
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for p_ in me.polygons:
        p_.use_smooth = True
    o = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(o)
    o.location = (ctr[0], ctr[1], 0.0); o.rotation_euler = (0, 0, rot_z)
    me.materials.append(fabric(name + "W", col, 0.95, 0.5, 300))
    o.modifiers.new("Thick", 'SOLIDIFY').thickness = 0.012
    # turned-down white sheet: the top rows of the same cloth carry a second (sheet) material, so it drapes too
    me.materials.append(fabric(name + "SheetW", (0.86, 0.86, 0.82), 0.9, 0.3, 500))
    for p_ in me.polygons:
        if p_.index // nx >= ny - 5:
            p_.material_index = 1
    sheet = None
    return dict(obj=o, sheet=sheet, nx=nx, ny=ny, w=w, l=l, foot=foot)


def drape_blankets(c):
    """Lay every cloth blanket over its bed's contents: ray-cast each vertex straight down, 1.2 cm above the hit;
    beyond the mattress the cloth hangs ~25 cm; two smoothing passes; small folds."""
    dg = bpy.context.evaluated_depsgraph_get(); sc = bpy.context.scene
    for B in c.get("blankets", []):
        o = B["obj"]; home = o.location.copy(); o.location = (0, -400, 0)
        bpy.context.view_layer.update(); dg = bpy.context.evaluated_depsgraph_get()
        M = __import__("mathutils").Matrix.Translation(home) @ __import__("mathutils").Matrix.Rotation(o.rotation_euler.z, 4, 'Z')
        nx, ny = B["nx"], B["ny"]; H = [[0.0] * (nx + 1) for _ in range(ny + 1)]
        for j in range(ny + 1):
            for i in range(nx + 1):
                v = o.data.vertices[j * (nx + 1) + i].co
                wp = M @ Vector((v.x, v.y, 2.2))
                hit, loc, n, idx, ob, _ = sc.ray_cast(dg, wp, Vector((0, 0, -1)))
                z = loc.z + 0.012 if hit else 0.4
                H[j][i] = min(max(z, 0.42), 0.98)      # cap: an upright patient sits out of the blanket at the waist
        for _ in range(2):
            H = [[(H[j][i] * 2 + H[max(0, j - 1)][i] + H[min(ny, j + 1)][i] + H[j][max(0, i - 1)] + H[j][min(nx, i + 1)]) / 6
                  for i in range(nx + 1)] for j in range(ny + 1)]
        for j in range(ny + 1):
            for i in range(nx + 1):
                v = o.data.vertices[j * (nx + 1) + i]
                v.co.z = H[j][i] + 0.006 * math.sin(i * 1.7 + j * 0.9) * math.sin(j * 0.6)
        o.data.update(); o.location = home
    bpy.context.view_layer.update()


def curtain(name, x, y0, y1, col=(0.62, 0.72, 0.7)):
    """Ward cubicle curtain: a rail at 2.15 m and a gathered fabric panel hanging from it (partly drawn)."""
    import bmesh
    L = abs(y1 - y0); n = max(8, int(L * 14)); bm = bmesh.new(); rows = []
    for j in range(2):
        z = 0.3 + 1.82 * j
        rows.append([bm.verts.new((0.05 * math.sin(i / n * L * 18.0), i / n * L, z)) for i in range(n + 1)])
    for i in range(n):
        bm.faces.new((rows[0][i], rows[0][i + 1], rows[1][i + 1], rows[1][i]))
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for p in me.polygons:
        p.use_smooth = True
    o = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(o)
    o.location = (x, min(y0, y1), 0); me.materials.append(fabric(name + "M", col, 0.95, 0.4, 500))
    o.modifiers.new("Thick", 'SOLIDIFY').thickness = 0.006
    cyl(name + "Rail", (x, max(y0, y1) - 1.25, 2.15), 0.012, 2.5, pbr("CurtRail", (0.7, 0.7, 0.7), 0.3, 0.9), verts=8, rot=(math.radians(90), 0, 0))
    return o


def facade_windows(name, origin, width, floors, floor_h=3.4, bay=3.0, sill0=1.0, normal_y=-1):
    """Real window units on a concrete facade: aluminium frames, mullion, sill, reflective glass with a dim
    interior behind (some with curtains), repeated with array modifiers. origin = bottom-left of the face."""
    frame_m = pbr(name + "Frame", (0.62, 0.63, 0.62), 0.35, 0.7)
    glass_m = pbr(name + "Glass", (0.05, 0.07, 0.08), 0.04, 0.0, **{'Specular IOR Level': 0.8, 'Coat Weight': 0.6})
    inner_m = noisy(name + "Inner", (0.16, 0.15, 0.13), 0.9, dirt=0.6, scale=1.2, dark=0.4)
    w, h_ = 1.9, 1.5; t = 0.06
    parts = [box("WGlass", (0, 0, 0), (w, 0.02, h_), glass_m), box("WInner", (0, -normal_y * 0.6, 0), (w, 0.02, h_), inner_m),
             box("WTop", (0, normal_y * 0.02, h_ / 2), (w + 0.1, 0.1, t), frame_m), box("WBot", (0, normal_y * 0.02, -h_ / 2), (w + 0.1, 0.1, t), frame_m),
             box("WL", (-w / 2, normal_y * 0.02, 0), (t, 0.1, h_), frame_m), box("WR", (w / 2, normal_y * 0.02, 0), (t, 0.1, h_), frame_m),
             box("WMul", (0, normal_y * 0.02, 0), (0.05, 0.08, h_), frame_m), box("WSill", (0, normal_y * 0.1, -h_ / 2 - 0.05), (w + 0.25, 0.22, 0.05), pbr(name + "Sill", (0.55, 0.55, 0.52), 0.6))]
    u = join(parts, name + "Unit")
    u.location = Vector(origin) + Vector((bay / 2, normal_y * 0.035, sill0 + h_ / 2))
    a1 = u.modifiers.new("ArrX", 'ARRAY'); a1.use_relative_offset = False; a1.use_constant_offset = True; a1.constant_offset_displace = (bay, 0, 0); a1.count = int(width // bay)
    a2 = u.modifiers.new("ArrZ", 'ARRAY'); a2.use_relative_offset = False; a2.use_constant_offset = True; a2.constant_offset_displace = (0, 0, floor_h); a2.count = floors
    band_m = ph_mat("rough_concrete", 1.2, (0.55, 0.54, 0.5), name=name + "Band", tint=(0.75, 0.74, 0.7))
    for f in range(floors + 1):                      # concrete floor bands proud of the wall
        box(name + "BandZ", Vector(origin) + Vector((width / 2, normal_y * 0.12, f * floor_h - 0.15)), (width, 0.24, 0.3), band_m)
    return u


def tree(name, loc, kind="pine", seed=0):
    r = np.random.default_rng(seed); bark = pbr(name + "Bark", (0.12, 0.09, 0.07), 0.9)
    if kind == "pine":
        hgt = float(r.uniform(6, 9)); needles = noisy(name + "Needle", (0.06, 0.12, 0.07), 0.9, dirt=0.5, scale=8, dark=0.5)
        cyl(name + "Trunk", Vector(loc) + Vector((0, 0, hgt * 0.3)), 0.14, hgt * 0.6, bark, verts=10)
        for k in range(4):
            bpy.ops.mesh.primitive_cone_add(vertices=14, radius1=1.9 - 0.4 * k, depth=2.4, location=Vector(loc) + Vector((0, 0, hgt * 0.35 + k * 1.3)))
            o = bpy.context.active_object; o.data.materials.append(needles)
            d = o.modifiers.new("D", 'DISPLACE'); tx = bpy.data.textures.new(name + "T", 'CLOUDS'); tx.noise_scale = 0.4; d.texture = tx; d.strength = 0.35
    else:   # bare winter plane tree
        hgt = float(r.uniform(6, 9)); cyl(name + "Trunk", Vector(loc) + Vector((0, 0, hgt * 0.35)), 0.18, hgt * 0.7, bark, verts=10)
        for k in range(9):
            a = r.uniform(0, 2 * math.pi); el = r.uniform(0.5, 1.1); L = r.uniform(2.0, 3.5); z0 = hgt * r.uniform(0.45, 0.7)
            dvec = Vector((math.cos(a) * math.cos(el), math.sin(a) * math.cos(el), math.sin(el)))
            ctr = Vector(loc) + Vector((0, 0, z0)) + dvec * L / 2
            b = cyl(name + "Branch", ctr, 0.05, L, bark, verts=6); b.rotation_mode = 'QUATERNION'; b.rotation_quaternion = dvec.to_track_quat('Z', 'Y')


def window_view(ctr, side, seed=0, dmin=14, n_blocks=5):
    """What a window looks out on: plastered apartment blocks 14-40 m out with real window units, so glass never
    reads as a white card or flat grey squares."""
    n = {"N": Vector((0, 1, 0)), "S": Vector((0, -1, 0)), "E": Vector((1, 0, 0)), "W": Vector((-1, 0, 0))}[side]
    t = Vector((-n.y, n.x, 0)); r = np.random.default_rng(seed)
    for k in range(n_blocks):
        d = float(r.uniform(dmin, dmin + 26)); lat = float(r.uniform(-18, 18)); floors = int(r.integers(4, 9)); hgt = floors * 2.9 + 0.6
        w = float(r.choice([12.0, 15.0, 18.0]))
        p = Vector(ctr) + n * d + t * lat; p.z = hgt / 2 - 1.0
        tint = [(0.86, 0.8, 0.68), (0.9, 0.86, 0.78), (0.76, 0.74, 0.7), (0.84, 0.72, 0.62)][k % 4]
        pl = ph_mat("plastered_wall_04", 0.3, (0.7, 0.68, 0.62), name=f"ViewPlaster{seed}_{k}", tint=tint)
        box("ViewBlock", p, (abs(t.x) * w + abs(n.x) * 10 + 0.01, abs(t.y) * w + abs(n.y) * 10 + 0.01, hgt), pl)
        if side in ("N", "S"):                       # windows on the face that looks back at us
            face_y = p.y - n.y * 5.0
            facade_windows(f"ViewWin{seed}_{k}", Vector((p.x - w / 2, face_y, -1.0)), w, floors, floor_h=2.9, bay=3.0, sill0=0.9, normal_y=-int(n.y))
    box("ViewGround", Vector((ctr[0], ctr[1], -0.06)) + n * 31, (60, 60, 0.1), pbr("ViewGround", (0.25, 0.24, 0.22), 0.9))


def build(variant=None):
    c = {}
    v = variant or "day"
    rng = np.random.default_rng(4)
    w_, sun_ = sky({"day": "afternoon", "morning": "morning", "night": "dusk"}[v])
    if v == "night":
        w_.node_tree.nodes["Background"].inputs['Strength'].default_value = 0.2; sun_.data.energy = 0.0
        bpy.context.scene.view_settings.exposure = 0.8
    box("Ground", (0, 0, -0.06), (600, 600, 0.1), ph_mat("asphalt_02", 0.15, (0.2, 0.2, 0.2), name="Asphalt"))
    periphery(rng, center=(0, 20), r_min=150, r_max=520, n_blocks=360, hill_h=40, minarets=2, smokes=1)
    haze((0, 300, 30), (1200, 500, 90), density=0.0012, color=(0.86, 0.88, 0.92), anis=0.3)   # outdoors only (rooms sit at y=0)
    # ---------------- exterior: the hospital block, entrance canopy, steps, car park
    plaster = ph_mat("plastered_wall_04", 0.25, (0.7, 0.68, 0.62), name="HospPlaster", tint=(0.86, 0.84, 0.78))
    box("HospBlock", EXT + Vector((0, 0, 10)), (60, 16, 20), plaster)
    box("HospWing", EXT + Vector((-38, -4, 7)), (16, 24, 14), plaster)
    facade_windows("HospFront", EXT + Vector((-30, -8.0, 0)), 24.0, 5)          # left of the entrance
    facade_windows("HospFrontR", EXT + Vector((6, -8.0, 0)), 24.0, 5)
    facade_windows("HospFrontU", EXT + Vector((-6, -8.0, 3.4)), 12.0, 4)        # above the canopy
    facade_windows("HospWingF", EXT + Vector((-46, -16.0, 0)), 15.0, 4)
    box("RoofParapet", EXT + Vector((0, -7.9, 20.2)), (60, 0.3, 0.5), pbr("Parapet", (0.5, 0.5, 0.48), 0.7))
    # ambulances (kit vans in white with a red band and plain AMBULANS lettering), trees, a few people
    from rs_vehicles import van as _van
    for j, (pos, hd) in enumerate(((EXT + Vector((-7.5, -13.5, 0)), math.radians(90)), (EXT + Vector((-11.0, -14.5, 0)), math.radians(80)))):
        r_, _w = _van(f"Ambulance{j}", (0.9, 0.9, 0.88)); r_.location = pos; r_.rotation_euler = (0, 0, hd)
        band = box(f"AmbBand{j}", (0, 0, 0), (4.6, 2.02, 0.16), pbr("AmbRed", (0.6, 0.04, 0.03), 0.4)); band.parent = r_; band.location = (0, 0, 1.0)
        for sgn in (-1, 1):
            tx = text_obj(f"AmbText{j}", "AMBULANS", (0, 0, 0), 0.22, pbr("AmbTextM", (0.6, 0.04, 0.03), 0.4), font_path="/usr/share/fonts/opentype/inter/Inter-Bold.otf")
            tx.parent = r_; tx.location = (0.2, sgn * 1.03, 1.35); tx.rotation_euler = (math.radians(90), 0, 0 if sgn < 0 else math.pi)
    for j, (dx, dy, kd) in enumerate(((-24, -20, "pine"), (-17, -24, "bare"), (14, -23, "bare"), (24, -21, "pine"), (30, -26, "pine"), (-30, -26, "bare"))):
        tree(f"Tree{j}", EXT + Vector((dx, dy, 0)), kd, seed=j)
    box("Canopy", EXT + Vector((0, -10.0, 3.6)), (9, 4, 0.3), pbr("Canopy", (0.6, 0.6, 0.58), 0.6))
    for sx in (-4.2, 4.2):
        cyl("CanopyCol", EXT + Vector((sx, -11.6, 1.8)), 0.15, 3.6, pbr("Col", (0.65, 0.64, 0.6), 0.6), verts=12)
    box("Doors", EXT + Vector((0, -8.02, 1.4)), (3.2, 0.06, 2.8), glass("DoorGlass", (0.6, 0.65, 0.65), 0.05))
    step_m = ph_mat("concrete_floor_worn_001", 0.5, (0.5, 0.5, 0.48), name="Steps")
    for k in range(6):
        box("Step", EXT + Vector((0, -8.3 - 4.2 + k * 0.35 + 2.1, 0.08 + k * 0.15)), (8.0, 4.2 - k * 0.7, 0.16 + k * 0.3), step_m)
    c["steps_top"] = EXT + Vector((0, -8.6, 0.9))
    sign = text_obj("HospSign", "DEVLET HASTANESİ", EXT + Vector((0, -8.1, 4.4)), 0.55, pbr("SignLetters", (0.15, 0.25, 0.45), 0.5),
                    font_path="/usr/share/fonts/opentype/inter/Inter-Bold.otf", extrude=0.03)
    from rs_vehicles import car
    c["car"] = car("FamilyCar", (0.55, 0.12, 0.08)); c["car"].location = EXT + Vector((11.0, -19.0, 0)); c["car"].rotation_euler = (0, 0, 0)
    car("ParkedA", (0.7, 0.7, 0.68)).location = EXT + Vector((-17.0, -19.5, 0))
    car("ParkedB", (0.15, 0.2, 0.3)).location = EXT + Vector((17.0, -19.0, 0))
    # ---------------- corridor
    floor_m = ph_mat("large_grey_tiles", 0.5, (0.5, 0.5, 0.48), name="CorFloor")
    wall_m = two_tone("CorWall")
    cr = room("Cor", COR, 28, 3.0, 3.0, floor_m, wall_m, windows=[("S", -12 + 4 * k, 1.0, 1.6, 1.5) for k in range(7)],
              doors=[("E", 0.0, 0.0, 1.8, 2.3)])
    for kind, ctr, side in cr["openings"]:
        if kind == "win":
            daylight_window(ctr, side, (1.6, 1.5), energy=260 if v != "night" else 0)
            window_view(ctr, side, seed=int(ctr.x * 7) % 997, n_blocks=2)
    for k in range(6):
        tube_light(COR + Vector((-12 + 5 * k, 0, 2.95)), energy=55)
    bench_m = noisy("BenchWood", (0.35, 0.24, 0.14), 0.7, dirt=0.4)
    c["benches"] = []
    for k, bx in enumerate((-8.0, -3.0, 4.0)):
        b = join([box("BenchSeat", (0, 0, 0.45), (1.8, 0.42, 0.05), bench_m), box("BenchBack", (0, 0.2, 0.75), (1.8, 0.04, 0.4), bench_m),
                  box("BenchLeg", (-0.8, 0, 0.22), (0.05, 0.4, 0.45), pbr("BenchIron", (0.1, 0.1, 0.1), 0.5, 0.6)),
                  box("BenchLeg", (0.8, 0, 0.22), (0.05, 0.4, 0.45), pbr("BenchIron", (0.1, 0.1, 0.1), 0.5, 0.6))], "Bench")
        b.location = COR + Vector((bx, 1.22, 0)); c["benches"].append(b.location.copy())
    for k in range(5):
        box("DoorPanel", COR + Vector((-11 + 5.5 * k, 1.49, 1.05)), (0.95, 0.04, 2.1), pbr("WardDoor", (0.55, 0.62, 0.58), 0.5))
    # nurses' station (a counter on the corridor's south side near the middle)
    ns = COR + Vector((1.0, -0.95, 0))
    box("Counter", ns + Vector((0, 0, 0.55)), (2.2, 0.6, 1.1), noisy("CounterWood", (0.42, 0.3, 0.18), 0.6, dirt=0.4))
    box("CounterTop", ns + Vector((0, 0, 1.12)), (2.3, 0.7, 0.04), pbr("Formica", (0.75, 0.72, 0.65), 0.4))
    c["phone"], c["handset"] = rotary_phone(ns + Vector((0.4, 0.05, 1.14)), math.pi)
    c["ns"] = ns
    ph_model("binder_notebook", loc=ns + Vector((-0.5, 0.05, 1.14)), rot_z=0.3)
    # theatre doors at the corridor's east end (two leaves on hinges)
    c["leaves"] = []
    for sy in (-1, 1):
        hinge = bpy.data.objects.new("LeafHinge", None); bpy.context.collection.objects.link(hinge)
        hinge.location = COR + Vector((14.0 + 0.05, sy * 0.9, 0))
        lf = box("Leaf", (0, 0, 0), (0.05, 0.88, 2.25), pbr("LeafM", (0.62, 0.68, 0.66), 0.45), bevel=0.01); lf.parent = hinge; lf.location = (0, -sy * 0.45, 1.13)
        port = cyl("Porthole", (0, 0, 0), 0.14, 0.06, glass("PortGlass", (0.8, 0.85, 0.85), 0.05), verts=20, rot=(0, math.radians(90), 0)); port.parent = hinge; port.location = (0, -sy * 0.45, 1.55)
        c["leaves"].append((hinge, sy))
    box("TheatreBeyond", COR + Vector((16.5, 0, 1.5)), (4.0, 3.0, 3.0), pbr("TheatreWall", (0.55, 0.65, 0.62), 0.6))
    tube_light(COR + Vector((16.0, 0, 2.9)), energy=60)
    # ---------------- ward
    wf = ph_mat("large_grey_tiles", 0.6, (0.5, 0.5, 0.48), name="WardFloor")
    wr = room("Ward", WARD, 14, 8, 3.2, wf, two_tone("WardWall", (0.45, 0.55, 0.5), (0.82, 0.8, 0.72)),
              windows=[("S", -4.5, 0.9, 2.0, 1.8), ("S", 0.0, 0.9, 2.0, 1.8), ("S", 4.5, 0.9, 2.0, 1.8)], doors=[("W", 2.5, 0, 1.2, 2.2)])
    c["ward_windows"] = []
    for kind, ctr, side in wr["openings"]:
        if kind == "win":
            daylight_window(ctr, side, (2.0, 1.8), energy={"day": 420, "morning": 650, "night": 0}[v], color=(1.0, 0.9, 0.78) if v == "morning" else (0.86, 0.9, 1.0))
            window_view(ctr, side, seed=len(c["ward_windows"]) + 10)
            c["ward_windows"].append(ctr)
    for k in range(3):
        tube_light(WARD + Vector((-4.5 + 4.5 * k, 0.5, 3.15)), energy=40 if v != "night" else 80)
    c["beds"] = []
    for k, b in enumerate(BEDS):
        iron_bed(f"Bed{k}", b)
        cab = box(f"Cabinet{k}", b + Vector((0.75, 0.75, 0.4)), (0.42, 0.4, 0.8), painted_steel(f"Cab{k}", (0.78, 0.78, 0.74), 0.4, 0.3), bevel=0.01)
        c["beds"].append(b)
    for k in (0, 2, 3):
        drip_stand(f"Drip{k}", BEDS[k] + Vector((-0.65, 0.6, 0)))
    c["drip3"], c["platelet"] = drip_stand("DripP", BEDS[1] + Vector((-0.65, 0.6, 0)), bag_col=(0.95, 0.8, 0.35))
    c["blankets"] = []
    for k, b in enumerate(BEDS):            # thin wool blankets, draped over whoever lies there (drape_blankets per shot)
        c["blankets"].append(cloth_blanket(f"Blanket{k}", b, [(0.22, 0.24, 0.3), (0.32, 0.22, 0.18), (0.24, 0.28, 0.24)][k % 3]))
        box(f"Pillow{k}", b + Vector((0, 0.8, 0.72)), (0.6, 0.32, 0.09), fabric(f"Pillow{k}", (0.86, 0.86, 0.82), 0.9, 0.3, 400), bevel=0.05)
    for k in range(4):                     # cubicle curtains between beds, partly drawn back to the wall
        curtain(f"Curtain{k}", BEDS[k].x + 1.3, 3.75, 3.75 - (1.2 + 0.5 * (k % 2)))
    ph_model("industrial_storage_cart", loc=BEDS[3] + Vector((1.3, -2.2, 0)), rot_z=0.2)       # nurses' trolley
    ph_model("SchoolChair_01", loc=BEDS[0] + Vector((0.9, -0.4, 0)), rot_z=math.radians(80))
    for k, x in enumerate((-2.25, 2.25)):        # two more beds along the window wall, heads to the wall, lockers and a drip
        sb = WARD + Vector((x, -2.75, 0)); iron_bed(f"SBed{k}", sb, rot_z=math.pi)
        c["blankets"].append(cloth_blanket(f"SBlanket{k}", sb, (0.3, 0.3, 0.34), rot_z=math.pi))
        box(f"SLocker{k}", sb + Vector((0.75, -0.75, 0.4)), (0.42, 0.4, 0.8), painted_steel(f"SCab{k}", (0.78, 0.78, 0.74), 0.4, 0.3), bevel=0.01)
        drip_stand(f"SDrip{k}", sb + Vector((-0.65, -0.6, 0)))
    chart = box("Chart", BEDS[2] + Vector((0, -1.03, 0.68)), (0.24, 0.015, 0.32), pbr("ChartBoard", (0.45, 0.35, 0.2), 0.5))
    c["chart"] = chart
    c["visitor_chair"] = ph_model("SchoolChair_01", loc=BEDS[2] + Vector((-0.9, -0.3, 0)), rot_z=math.radians(-90))
    # ---------------- lab
    lr = room("Lab", LAB, 6, 5, 3.0, wf, two_tone("LabWall", (0.75, 0.75, 0.72), (0.88, 0.87, 0.83)), windows=[("S", 0.0, 1.0, 2.4, 1.5)])
    for kind, ctr, side in lr["openings"]:
        daylight_window(ctr, side, (2.4, 1.5), energy=380 if v != "night" else 0)
        window_view(ctr, side, seed=21)
    box("LabBench", LAB + Vector((0, -1.9, 0.45)), (4.0, 0.7, 0.9), painted_steel("LabBench", (0.8, 0.8, 0.78), 0.5, 0.3))
    box("LabTop", LAB + Vector((0, -1.9, 0.92)), (4.1, 0.75, 0.04), pbr("LabTopM", (0.15, 0.15, 0.15), 0.4))
    mic, _ = ph_model("vintage_microscope", loc=LAB + Vector((0.3, -2.0, 0.94)), rot_z=math.pi)
    c["mic"] = LAB + Vector((0.3, -2.0, 1.25))
    for k in range(6):
        cyl("RackTube", LAB + Vector((-1.4 + k * 0.05, -1.95, 1.0)), 0.007, 0.1, pbr("Blood", (0.35, 0.02, 0.02), 0.2), verts=8)
    tube_light(LAB + Vector((0, 0, 2.95)), energy=45)
    c["tube"] = cyl("SampleTube", (0, -150, 0), 0.008, 0.1, glass("TubeGlass", (0.95, 0.95, 0.95), 0.02), verts=10)
    c["tube_blood"] = cyl("TubeBlood", (0, -150, 0), 0.0072, 0.07, pbr("Blood2", (0.4, 0.02, 0.02), 0.2), verts=10)
    ph_model("metal_stool_01", loc=LAB + Vector((0.3, -1.25, 0)))
    # ---------------- office with lightbox
    orr = room("Office", OFFICE, 5, 4, 2.9, ph_mat("herringbone_parquet", 0.8, (0.4, 0.28, 0.18), name="OfficeFloor"), two_tone("OffWall", (0.6, 0.55, 0.45), (0.82, 0.78, 0.68)),
               windows=[("E", 0.0, 1.0, 1.4, 1.4)])
    for kind, ctr, side in orr["openings"]:
        daylight_window(ctr, side, (1.4, 1.4), energy=160 if v != "night" else 0)
        window_view(ctr, side, seed=31, dmin=24)
    lb_frame = box("LightboxFrame", OFFICE + Vector((0, 1.93, 1.6)), (1.0, 0.1, 0.62), painted_steel("LBFrame", (0.75, 0.75, 0.72), 0.4, 0.3), bevel=0.01)
    lb = bpy.data.materials.new("LightboxPanel"); lb.use_nodes = True
    lp = lb.node_tree.nodes["Principled BSDF"]; lp.inputs['Base Color'].default_value = (0.9, 0.92, 0.95, 1); lp.inputs['Emission Color'].default_value = (0.9, 0.95, 1.0, 1)
    vnode = lb.node_tree.nodes.new("ShaderNodeValue"); d = vnode.outputs[0].driver_add("default_value").driver; d.type = 'SCRIPTED'
    d.expression = "0.7 * (1 if frame < 60 else 0.0)" if v != "lightbox_off" else "0.7"
    lb.node_tree.links.new(vnode.outputs[0], lp.inputs['Emission Strength'])
    box("LightboxPanel", OFFICE + Vector((0, 1.875, 1.6)), (0.9, 0.01, 0.52), lb)
    lbl = bpy.data.lights.new("LBGlow", 'AREA'); lbl.size = 0.9; lbl.size_y = 0.5
    dl = lbl.driver_add("energy").driver; dl.type = 'SCRIPTED'; dl.expression = "8 * (1 if frame < 60 else 0.0)"
    lo = bpy.data.objects.new("LBGlow", lbl); bpy.context.collection.objects.link(lo); lo.location = OFFICE + Vector((0, 1.82, 1.6)); lo.rotation_euler = (math.radians(90), 0, 0)
    film = bpy.data.materials.new("Film"); film.use_nodes = True
    fn = film.node_tree.nodes; fp = fn["Principled BSDF"]; tcn = fn.new("ShaderNodeTexCoord"); nn = fn.new("ShaderNodeTexNoise"); nn.inputs['Scale'].default_value = 3
    film.node_tree.links.new(tcn.outputs['Object'], nn.inputs['Vector']); cr_ = fn.new("ShaderNodeValToRGB")
    cr_.color_ramp.elements[0].color = (0.02, 0.025, 0.03, 1); cr_.color_ramp.elements[1].color = (0.3, 0.32, 0.35, 1)
    film.node_tree.links.new(nn.outputs['Fac'], cr_.inputs['Fac']); film.node_tree.links.new(cr_.outputs['Color'], fp.inputs['Base Color'])
    fp.inputs["Transmission Weight"].default_value = 0.2; fp.inputs["Roughness"].default_value = 0.3
    c["film"] = box("ScanFilm", (0, -150, 0), (0.35, 0.004, 0.43), film)
    c["lightbox"] = OFFICE + Vector((0, 1.86, 1.6))
    desk, _ = ph_model("metal_office_desk", loc=OFFICE + Vector((-0.8, -0.6, 0)), rot_z=0.0)
    tube_light(OFFICE + Vector((0, 0, 2.85)), energy=30)
    # ---------------- operating theatre
    orm = room("Theatre", OR_, 6, 6, 3.2, ph_mat("large_grey_tiles", 0.8, (0.5, 0.55, 0.52), name="ORFloor"), two_tone("ORWall", (0.5, 0.62, 0.6), (0.62, 0.72, 0.7), split=2.0))
    steel = pbr("ORSteel", (0.7, 0.7, 0.72), 0.25, 0.9)
    box("ORTable", OR_ + Vector((0, 0, 0.85)), (0.6, 2.0, 0.08), pbr("ORPad", (0.12, 0.2, 0.2), 0.6), bevel=0.02)
    cyl("ORPillar", OR_ + Vector((0, 0, 0.42)), 0.12, 0.84, steel, verts=16)
    cyl("LampArm", OR_ + Vector((0, 0, 2.75)), 0.04, 0.9, steel, verts=10)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, radius=0.45, location=OR_ + Vector((0, 0, 2.3)))
    dome = bpy.context.active_object; dome.scale = (1, 1, 0.35); dome.data.materials.append(painted_steel("LampDome", (0.82, 0.83, 0.8), 0.35, 0.2))
    bulbm = bpy.data.materials.new("ORBulb"); bulbm.use_nodes = True
    bp = bulbm.node_tree.nodes["Principled BSDF"]; bp.inputs['Base Color'].default_value = (0.8, 0.8, 0.8, 1); bp.inputs['Emission Color'].default_value = (1.0, 0.97, 0.9, 1)
    vb = bulbm.node_tree.nodes.new("ShaderNodeValue"); db = vb.outputs[0].driver_add("default_value").driver; db.type = 'SCRIPTED'; db.expression = "12 * min(1, max(0, (frame - 14) / 3))"
    bulbm.node_tree.links.new(vb.outputs[0], bp.inputs['Emission Strength'])
    for k in range(6):
        a = k / 6 * 2 * math.pi
        cyl("ORBulbDisc", OR_ + Vector((0.22 * math.cos(a), 0.22 * math.sin(a), 2.15)), 0.07, 0.01, bulbm, verts=16)
    sl = bpy.data.lights.new("ORLamp", 'SPOT'); sl.spot_size = math.radians(45); sl.spot_blend = 0.4; sl.shadow_soft_size = 0.3; sl.color = (1.0, 0.97, 0.92)
    ds = sl.driver_add("energy").driver; ds.type = 'SCRIPTED'; ds.expression = "1500 * min(1, max(0, (frame - 14) / 3))"
    so = bpy.data.objects.new("ORLamp", sl); bpy.context.collection.objects.link(so); so.location = OR_ + Vector((0, 0, 2.1))
    tube_light(OR_ + Vector((1.8, 1.8, 3.15)), energy=70); tube_light(OR_ + Vector((-1.8, -1.8, 3.15)), energy=70)
    tube_light(OR_ + Vector((1.8, -1.8, 3.15)), energy=50)
    ph_model("industrial_storage_cart", loc=OR_ + Vector((-2.0, 1.6, 0)), rot_z=0.4)
    # ---------------- local clinic (December, evening)
    cf = ph_mat("worn_brick_floor", 0.6, (0.4, 0.3, 0.25), name="ClinicFloor")
    cl = room("Clinic", CLINIC, 7, 5, 2.8, cf, two_tone("ClinicWall", (0.4, 0.5, 0.55), (0.8, 0.78, 0.7)), doors=[("S", 2.4, 0, 1.0, 2.1)],
              windows=[("S", -1.5, 1.0, 1.4, 1.2)])
    for k in range(2):
        tube_light(CLINIC + Vector((-1.5 + 3 * k, 0, 2.75)), energy=55)
    c["cots"] = []
    for k in range(3):
        cc = CLINIC + Vector((-2.4 + k * 2.0, 1.3, 0))
        iron_bed(f"Cot{k}", cc)
        drip_stand(f"CDrip{k}", cc + Vector((-0.6, 0.7, 0)), fill=0.6)
        c["blankets"].append(cloth_blanket(f"CBlanket{k}", cc, [(0.32, 0.22, 0.18), (0.22, 0.24, 0.3), (0.3, 0.28, 0.2)][k]))
        box(f"CPillow{k}", cc + Vector((0, 0.8, 0.72)), (0.6, 0.32, 0.09), fabric(f"CPillow{k}", (0.86, 0.86, 0.82), 0.9, 0.3, 400), bevel=0.05)
        c["cots"].append(cc)
    # small 1998 clinic: a glass-fronted cabinet, a sink with a mirror, a chair, a calendar, a window onto the dark street
    mc = painted_steel("MedCab", (0.86, 0.86, 0.83), 0.35, 0.2)          # white steel medicine cabinet with glass doors
    box("MedCabinet", CLINIC + Vector((3.2, 1.6, 0.9)), (0.4, 0.9, 1.8), mc, bevel=0.01)
    box("MedCabGlass", CLINIC + Vector((2.995, 1.6, 1.3)), (0.01, 0.82, 0.9), glass("MedGlass", (0.85, 0.9, 0.9), 0.05))
    for k in range(3):
        box("MedShelf", CLINIC + Vector((3.15, 1.6, 0.95 + 0.3 * k)), (0.3, 0.84, 0.015), mc)
        for j in range(5):
            cyl("MedBottle", CLINIC + Vector((3.15, 1.3 + 0.14 * j, 1.02 + 0.3 * k)), 0.03, 0.12, glass(f"Bottle{(j + k) % 3}", [(0.5, 0.3, 0.1), (0.85, 0.9, 0.9), (0.3, 0.45, 0.6)][(j + k) % 3], 0.1), verts=10)
    porcelain = pbr("Porcelain", (0.88, 0.88, 0.85), 0.15, 0.0, **{'Coat Weight': 0.5})
    box("Sink", CLINIC + Vector((3.2, -0.9, 0.85)), (0.4, 0.55, 0.18), porcelain, bevel=0.04)
    cyl("SinkPedestal", CLINIC + Vector((3.25, -0.9, 0.4)), 0.09, 0.8, porcelain, verts=14)
    cyl("Tap", CLINIC + Vector((3.4, -0.9, 1.02)), 0.012, 0.14, pbr("Chrome", (0.8, 0.8, 0.8), 0.1, 1.0), verts=8)
    box("Mirror", CLINIC + Vector((3.48, -0.9, 1.5)), (0.02, 0.45, 0.55), pbr("MirrorM", (0.9, 0.9, 0.9), 0.02, 1.0))
    ph_model("plastic_monobloc_chair_01", loc=CLINIC + Vector((1.6, 0.4, 0)), rot_z=2.4)
    box("Calendar", CLINIC + Vector((-3.48, 0.5, 1.6)), (0.02, 0.35, 0.5), pbr("CalendarM", (0.85, 0.82, 0.75), 0.7))
    window_view(CLINIC + Vector((-1.5, -2.5, 1.6)), "S", seed=41, dmin=14, n_blocks=3)
    # night street outside the clinic door
    box("ClinicFacade", CLINIC + Vector((0, -2.62, 1.4)), (12, 0.02, 2.8), ph_mat("plastered_wall_04", 0.4, (0.6, 0.55, 0.47), name="ClinicPlaster", tint=(0.9, 0.85, 0.75))).hide_render = True
    lamp = bpy.data.lights.new("ClinicStreetLamp", 'SPOT'); lamp.energy = 700; lamp.color = (1.0, 0.68, 0.38); lamp.spot_size = math.radians(100)
    lo = bpy.data.objects.new("ClinicStreetLamp", lamp); bpy.context.collection.objects.link(lo); lo.location = CLINIC + Vector((5.5, -6.0, 5.5))
    cyl("ClinicLampPole", CLINIC + Vector((5.5, -5.6, 2.8)), 0.07, 5.6, pbr("PoleIron", (0.05, 0.05, 0.05), 0.5, 0.6), verts=10)
    # ---------------- people
    P = {}
    P["m1"] = person("ManA", 1.0, 38, "wool_brown", "short02", moustache=True)
    P["m2"] = person("ManB", 1.0, 45, "charcoal", "short02", hat="flat", hat_col=(0.24, 0.2, 0.15), moustache=True)
    P["doc"] = person("Doctor", 1.0, 46, "doctor", "short03", hv=0.4)
    P["nurse"] = person("Nurse", 0.0, 32, "nurse", "ponytail01", hv=0.1, hat="nurse", hat_col=(0.92, 0.92, 0.9))
    P["son"] = person("Son", 1.0, 19, "navy", "short04")
    P["pat1"] = person("Patient1", 1.0, 50, "wool_grey", "short02", moustache=True)
    P["pat2"] = person("Patient2", 1.0, 34, "camel", "short03")
    P["tech"] = person("Tech", 0.0, 40, "nurse", "ponytail01", hv=0.2, hat="nurse", hat_col=(0.92, 0.92, 0.9))
    P["wife"] = person("Wife", 0.0, 44, "woman_coat", "bob02", hv=0.12)
    P["ext1"] = person("Visitor1", 0.0, 60, "woman_coat", "bob01", hv=0.5)
    P["ext2"] = person("Visitor2", 1.0, 66, "camel", "short02", hv=0.7, hat="flat", hat_col=(0.2, 0.18, 0.15))
    c["people"] = P
    for h in P.values():
        place(h, (0, -150, 0), 0)
    c["variant"] = v
    import rs_env as _rs_env
    _rs_env.cinematic(c, __name__)        # house cinematic look (look.py)
    return c


# ============================================================================ helpers
def hide(c, keep=()):
    for k, h in c["people"].items():
        if k not in keep:
            h.arm.location = (0, -150, 0)


def walk_to(h, a, b, sec, speed=1.1, stride=1.25, z=None):
    a = Vector(a); b = Vector(b); d = b - a; L_ = d.length; s = min(L_, max(0.0, speed * sec))
    h.arm.rotation_euler = (0, 0, 0); h.arm.location = (0, 0, 0); reset_pose(h)
    moving = 0 < s < L_
    ph_ = (s / stride) % 1.0 if moving else 0.0
    pose_walk(h, ph_, stride=24 if moving else 0, arm_swing=0); arms_relaxed(h, ph_, 14 if moving else 0)
    p = a + d.normalized() * s
    place(h, (p.x, p.y, a.z if z is None else z(p)), face_angle(a, b))
    return p


def stand_at(h, loc, look, **kw):
    stand_pose(h, **kw); place(h, loc, face_angle(loc, look))


def sit_at(h, loc, look, lean=10):
    h.arm.rotation_euler = (0, 0, 0); h.arm.location = (0, 0, 0); reset_pose(h); pose_sit(h, lean=lean)
    place(h, Vector((loc[0], loc[1], 0.0)), face_angle(loc, look))


def sit_up_in_bed(h, bed, k=1.0):
    """Patient sitting up against the pillows: legs straight along the mattress, torso raised (k 0 low .. 1 upright)."""
    h.arm.rotation_euler = (0, 0, 0); h.arm.location = (0, 0, 0); reset_pose(h)
    for sd in ("L", "R"):
        for b_ in ("upperleg01", "upperleg02", "lowerleg01", "lowerleg02"):
            h.aim(f"{b_}.{sd}", (0, -1, -0.02))
        h.aim(f"foot.{sd}", (0, -0.4, 1))
    back = 35 + 25 * (1 - k)                               # lean back against the raised pillows
    h.rot("spine05", (1, 0, 0), -back * 0.5); h.rot("spine03", (1, 0, 0), -back * 0.5)
    h.rot("head", (1, 0, 0), back * 0.45)
    for sd, sg in (("L", 1), ("R", -1)):
        h.aim(f"upperarm01.{sd}", (sg * 0.25, 0.1, -1)); h.aim(f"upperarm02.{sd}", (sg * 0.25, 0.1, -1))
        h.aim(f"lowerarm01.{sd}", (sg * 0.1, -1, -0.35)); h.aim(f"lowerarm02.{sd}", (sg * 0.1, -1, -0.35))
    place(h, bed + Vector((0, 0.35, 0.62)), 0.0)

def ward_patients(c, sec, upright=None):
    lie_in_bed(c["people"]["pat2"], BEDS[3] + Vector((0, 0.9, 0)), (0, -1), 0.69)
    if upright is None:
        lie_in_bed(c["people"]["pat1"], BEDS[2] + Vector((0, 0.9, 0)), (0, -1), 0.69)
    else:
        sit_up_in_bed(c["people"]["pat1"], BEDS[2], upright)
    drape_blankets(c)


def S(name, t):
    sec = t * dur(name)
    bpy.context.scene.frame_current = int(round(sec * 24)) + 1
    return sec


def C(p0, p1, tgt, lens, tgt1=None):
    def f(c, t):
        e = ease(t); tg = Vector(tgt) if tgt1 is None else Vector(tgt).lerp(Vector(tgt1), e)
        return (Vector(p0).lerp(Vector(p1), e), tg, lens)
    return f


def leaves(c, k):
    for hinge, sy in c["leaves"]:
        hinge.rotation_euler = (0, 0, sy * math.radians(70) * (1 - k))


# ============================================================================ shots
def c2_1a(c, t):
    sec = S("ch2_1a", t); hide(c, ("m1", "m2")); leaves(c, 1)
    def zf(p):
        y = p.y - (EXT.y - 12.5)
        return max(0.0, min(0.9, y * 0.9 / 4.2))
    walk_to(c["people"]["m1"], EXT + Vector((-1.0, -17.0, 0)), EXT + Vector((-0.6, -8.8, 0)), sec, speed=0.75, z=zf)
    walk_to(c["people"]["m2"], EXT + Vector((0.4, -17.8, 0)), EXT + Vector((0.6, -8.8, 0)), sec - 0.5, speed=0.7, z=zf)
    c["focus"] = c["people"]["m1"].arm.location + Vector((0, 0, 1.3))


def c2_1b(c, t):
    sec = S("ch2_1b", t); hide(c, ("m1", "m2", "nurse")); leaves(c, 1)
    b = c["benches"][0]
    sit_at(c["people"]["m1"], b + Vector((-0.4, -0.08, 0.43)), b + Vector((-0.4, -2, 0)), lean=8)
    sit_at(c["people"]["m2"], b + Vector((0.45, -0.08, 0.43)), b + Vector((0.45, -2, 0)), lean=18)
    walk_to(c["people"]["nurse"], COR + Vector((6.0, -0.5, 0)), COR + Vector((-13.0, -0.5, 0)), sec, speed=1.2)
    c["focus"] = b + Vector((0, 0, 1.1))


def c2_2a(c, t):
    sec = S("ch2_2a", t); hide(c, ("m1", "m2")); leaves(c, 1)
    b = c["benches"][0]; h = c["people"]["m2"]
    sit_at(h, b + Vector((0.45, -0.08, 0.43)), b + Vector((0.45, -2, 0)), lean=-6)
    sd = forward(h).cross(Vector((0, 0, 1)))
    h.rot("neck01", sd, 12); h.rot("head", sd, 16 + 2 * math.sin(sec * 0.8))       # head back against the wall
    sit_at(c["people"]["m1"], b + Vector((-0.4, -0.08, 0.43)), b + Vector((-0.4, -2, 0)), lean=14)
    c["focus"] = h.bone_head("head")


def c2_2b(c, t):          # a passing nurse stops, looks at him, hurries off to fetch a doctor
    sec = S("ch2_2b", t); hide(c, ("m1", "m2", "nurse")); leaves(c, 1)
    b = c["benches"][0]; h = c["people"]["m2"]
    sit_at(h, b + Vector((0.45, -0.08, 0.43)), b + Vector((0.45, -2, 0)), lean=-6)
    sd = forward(h).cross(Vector((0, 0, 1))); h.rot("neck01", sd, 12); h.rot("head", sd, 16)
    sit_at(c["people"]["m1"], b + Vector((-0.4, -0.08, 0.43)), b + Vector((-0.4, -2, 0)), lean=14)
    n = c["people"]["nurse"]; stop = b + Vector((1.0, -1.2, 0))
    if sec < 1.3:
        walk_to(n, b + Vector((-3.5, -1.2, 0)), stop, sec, speed=(stop - (b + Vector((-3.5, -1.2, 0)))).length / 1.3)
    elif sec < 2.4:
        stand_at(n, stop, b + Vector((0.45, 0, 0.9)))
        n.rot("head", forward(n).cross(Vector((0, 0, 1))), -8)
    else:
        walk_to(n, stop, stop + Vector((8.0, 0.2, 0)), sec - 2.4, speed=1.9, stride=1.35)
    c["focus"] = n.bone_head("head")


def c2_3a(c, t):
    sec = S("ch2_3a", t); hide(c, ("doc", "pat1", "pat2", "son"))
    ward_patients(c, sec, upright=0.8)
    h = c["people"]["doc"]; seat = BEDS[2] + Vector((-0.9, -0.3, 0.45))
    sit_at(h, seat, BEDS[2] + Vector((0, 0.3, 0)), lean=16 + 6 * ease(min(1.0, sec / 2.0)))
    c["focus"] = h.bone_head("head")


def c2_3b(c, t):
    sec = S("ch2_3b", t); hide(c, ("doc", "pat1", "pat2", "son"))
    ward_patients(c, sec, upright=0.85)
    p = c["people"]["pat1"]; p.rot("head", (0, 0, 1), 8 * math.sin(sec * 1.1))
    sit_at(c["people"]["doc"], BEDS[2] + Vector((-0.9, -0.3, 0.45)), BEDS[2] + Vector((0, 0.3, 0)), lean=20)
    stand_at(c["people"]["son"], BEDS[2] + Vector((0.95, -0.6, 0)), BEDS[2] + Vector((0, 0.4, 0.6)), hands_pockets=True)
    c["focus"] = p.bone_head("head")


def c2_4a(c, t):
    sec = S("ch2_4a", t); hide(c, ("doc", "pat1", "pat2"))
    ward_patients(c, sec)
    win = c["ward_windows"][1]; h = c["people"]["doc"]
    stand_at(h, Vector((win.x + 0.2, win.y + 0.75, 0)), Vector((win.x - 0.2, win.y - 3, 0)), crossed=True)
    h.rot("head", (0, 0, 1), 3 * math.sin(sec * 0.4))
    c["focus"] = h.bone_head("head")


def c2_4b(c, t):
    sec = S("ch2_4b", t); hide(c, ("doc", "pat1", "pat2"))
    ward_patients(c, sec)
    win = c["ward_windows"][1]; h = c["people"]["doc"]
    k = ease(min(1.0, max(0.0, (sec - 0.8) / 1.6)))
    loc = Vector((win.x + 0.2, win.y + 0.75, 0))
    stand_pose(h, crossed=k < 0.5); place(h, loc, face_angle(loc, Vector((win.x - 0.2, win.y - 3, 0))) + math.pi * k)
    c["focus"] = h.bone_head("head")


def c2_5a(c, t):
    sec = S("ch2_5a", t); hide(c, ("doc", "pat1", "pat2", "son"))
    ward_patients(c, sec, upright=0.8)
    h = c["people"]["son"]; loc = BEDS[2] + Vector((0.95, -0.7, 0))
    stand_at(h, loc, BEDS[2] + Vector((-1.2, -0.6, 0)))
    from human import reach as rch
    sd = forward(h).cross(Vector((0, 0, 1)))
    rch(h, "R", h.bone_head("spine02") + forward(h) * 0.3 + Vector((0, 0, 0.05 + 0.04 * math.sin(sec * 3))), Vector((sd.x, sd.y, -0.8)), forward(h))
    stand_at(c["people"]["doc"], BEDS[2] + Vector((-1.2, -0.7, 0)), loc, crossed=True)
    c["focus"] = h.bone_head("head")


def c2_6a(c, t):          # medium: the doctor lifts the receiver to his ear, his other hand resting on the counter
    sec = S("ch2_6a", t); hide(c, ("doc",)); leaves(c, 1)
    ns = c["ns"]; h = c["people"]["doc"]; loc = ns + Vector((0.3, 0.55, 0))
    stand_at(h, loc, ns + Vector((0.3, 0, 0)))
    sd = forward(h).cross(Vector((0, 0, 1))).normalized()
    k = ease(min(1.0, sec / 0.9))
    ear = h.bone_head("head") - sd * 0.1 + Vector((0, 0, -0.05)) + forward(h) * 0.03      # his LEFT ear (sd points right)
    rest = ns + Vector((0.4, 0.05, 1.18))
    hs_at = rest.lerp(ear + Vector((0, 0, -0.06)), k)
    reach(h, "L", hs_at, Vector((-sd.x, -sd.y, -1.0)), Vector((0, 0, 1)))
    reach(h, "R", ns + Vector((0.05, 0.22, 1.15)), Vector((sd.x, sd.y, -1.0)), forward(h))
    fingers_curl(h, 55, thumb=40)
    hs = c["handset"]; hs.location = hs_at; hs.rotation_euler = (math.radians(80 * k), 0, math.atan2(sd.y, sd.x))
    h.rot("head", sd, -6)
    c["focus"] = h.bone_head("head")


def c2_6b(c, t):
    sec = S("ch2_6b", t); hide(c, ("doc", "nurse")); leaves(c, 1)
    ns = c["ns"]; h = c["people"]["doc"]; loc = ns + Vector((0.4, 0.75, 0))
    stand_at(h, loc, ns + Vector((2.0, 0.6, 0)))
    sd = forward(h).cross(Vector((0, 0, 1)))
    ear = h.bone_head("head") - sd * 0.09 + Vector((0, 0, -0.04))
    reach(h, "R", ear + Vector((0, 0, -0.08)), Vector((sd.x, sd.y, -0.7)), Vector((0, 0, 1)))
    c["handset"].location = ear + Vector((0, 0, -0.08)); c["handset"].rotation_euler = (math.radians(80), 0, math.atan2(sd.y, sd.x))
    n = c["people"]["nurse"]
    p0 = ns + Vector((-5.0, 0.6, 0)); p1 = ns + Vector((-0.9, 0.7, 0))
    walk_to(n, p0, p1, sec, speed=(p1 - p0).length / max(1.0, dur("ch2_6b") * 0.7) * 0.75)
    c["focus"] = h.bone_head("head")


def c4_1a(c, t):
    sec = S("ch4_1a", t); hide(c, ("pat1", "pat2", "m1", "m2"))
    ward_patients(c, sec)
    lie_in_bed(c["people"]["m1"], BEDS[0] + Vector((0, 0.9, 0)), (0, -1), 0.69)
    lie_in_bed(c["people"]["m2"], BEDS[4] + Vector((0, 0.9, 0)), (0, -1), 0.69)
    drape_blankets(c)
    c["focus"] = BEDS[2] + Vector((0, 0, 0.8))


def c4_1b(c, t):
    sec = S("ch4_1b", t); hide(c, ("pat1", "pat2", "doc", "m1"))
    ward_patients(c, sec)
    lie_in_bed(c["people"]["m1"], BEDS[0] + Vector((0, 0.9, 0)), (0, -1), 0.69)
    h = c["people"]["doc"]; loc = BEDS[2] + Vector((0.1, -1.6, 0))
    stand_at(h, loc, BEDS[2])
    sd = forward(h).cross(Vector((0, 0, 1)))
    board = h.bone_head("spine02") + forward(h) * 0.3 + Vector((0, 0, -0.1))
    reach(h, "L", board - sd * 0.08, Vector((-sd.x, -sd.y, -0.7)), forward(h))
    reach(h, "R", board + sd * (0.04 + 0.03 * math.sin(sec * 5)) + Vector((0, 0, 0.02)), Vector((sd.x, sd.y, -0.7)), forward(h))
    c["chart"].location = board + forward(h) * 0.03; c["chart"].rotation_euler = (math.radians(-50), 0, math.atan2(-forward(h).x, forward(h).y))
    h.rot("head", sd, -14)
    drape_blankets(c)
    c["focus"] = h.bone_head("head")


def c4_2a(c, t):          # the technician holds a sample tube up to the window light, close to her face (medium)
    sec = S("ch4_2a", t); hide(c, ("tech",))
    h = c["people"]["tech"]; win = LAB + Vector((0, -2.6, 1.75))
    loc = LAB + Vector((-0.9, -1.3, 0)); stand_at(h, loc, win)
    sd = forward(h).cross(Vector((0, 0, 1)))
    k = ease(min(1.0, sec / 1.4))
    tube = h.bone_head("head") + forward(h) * 0.24 + sd * 0.06 + Vector((0, 0, -0.42 + 0.16 * k))      # lifts only to chin height
    reach(h, "R", tube, Vector((sd.x * 0.3, sd.y * 0.3, -1.0)), forward(h) + Vector((0, 0, 0.4)))
    fingers_curl(h, 70, thumb=50)
    c["tube"].location = tube + Vector((0, 0, 0.06)); c["tube_blood"].location = tube + Vector((0, 0, 0.045))
    c["focus"] = h.bone_head("head")


def c4_2b(c, t):          # the technician bends to the microscope (person in frame)
    sec = S("ch4_2b", t); hide(c, ("tech",))
    h = c["people"]["tech"]; mic = c["mic"]
    sit_at(h, LAB + Vector((0.3, -1.25, 0.62)), mic, lean=22 + 3 * math.sin(sec * 0.6))
    sd = forward(h).cross(Vector((0, 0, 1)))
    reach(h, "R", mic + sd * 0.14 + Vector((0, 0, -0.18)), Vector((sd.x, sd.y, -0.7)), forward(h))
    reach(h, "L", mic - sd * 0.16 + Vector((0, 0, -0.25)), Vector((-sd.x, -sd.y, -0.7)), forward(h))
    c["focus"] = h.bone_head("head")


def c4_3a(c, t):          # a nurse hangs the pale yellow platelet bag, both hands at shoulder height (medium-wide)
    sec = S("ch4_3a", t); hide(c, ("nurse", "pat1", "pat2"))
    ward_patients(c, sec)
    h = c["people"]["nurse"]; pole = BEDS[1] + Vector((-0.65, 0.6, 0)); loc = pole + Vector((-0.15, -0.5, 0))
    stand_at(h, loc, pole + Vector((0.12, 0, 0)))
    sd = forward(h).cross(Vector((0, 0, 1)))
    k = ease(min(1.0, sec / 1.8))
    sh = h.bone_head("upperarm01.R").z
    hold = pole + Vector((0.12, -0.08, sh - 0.02))
    bag = (h.bone_head("spine02") + forward(h) * 0.28).lerp(hold, k)
    reach(h, "R", bag + sd * 0.05 + Vector((0, 0, 0.08)), Vector((sd.x, sd.y, -1.0)), forward(h))
    reach(h, "L", bag - sd * 0.05 + Vector((0, 0, -0.04)), Vector((-sd.x, -sd.y, -1.0)), forward(h))
    fingers_curl(h, 60, thumb=40)
    c["platelet"].location = bag
    c["focus"] = h.bone_head("head")


def c4_3b(c, t):
    sec = S("ch4_3b", t); hide(c, ("pat1", "pat2"))
    ward_patients(c, sec, upright=ease(min(1.0, sec / dur("ch4_3b"))))
    c["focus"] = c["people"]["pat1"].bone_head("head")


def c4_11a(c, t):
    sec = S("ch4_11a", t); hide(c, ("m2", "ext1", "ext2")); leaves(c, 1)
    bpy.context.scene.view_settings.exposure = 1.0        # the facade faces away from the low morning sun
    walk_to(c["people"]["ext1"], EXT + Vector((-9.0, -16.0, 0)), EXT + Vector((-2.0, -13.2, 0)), sec, speed=0.6)
    stand_at(c["people"]["ext2"], EXT + Vector((5.2, -13.0, 0)), EXT + Vector((0, -10, 0)), hands_pockets=True)
    def zf(p):
        y = p.y - (EXT.y - 12.5)
        return max(0.0, min(0.9, y * 0.9 / 4.2))
    walk_to(c["people"]["m2"], EXT + Vector((0.0, -8.4, 0)), EXT + Vector((0.4, -17.0, 0)), sec, speed=0.8, z=zf)
    c["focus"] = c["people"]["m2"].arm.location + Vector((0, 0, 1.3))


def c4_11b(c, t):
    sec = S("ch4_11b", t); hide(c, ("m2", "wife", "son", "ext1"))
    bpy.context.scene.view_settings.exposure = 1.0
    walk_to(c["people"]["ext1"], EXT + Vector((2.0, -14.0, 0)), EXT + Vector((8.0, -17.0, 0)), sec, speed=0.6)
    car_ = c["car"]
    stand_at(c["people"]["wife"], car_.location + Vector((-0.6, -1.4, 0)), car_.location + Vector((-2, -6, 0)))
    son = c["people"]["son"]; loc = car_.location + Vector((0.3, -1.25, 0))
    stand_at(son, loc, car_.location + Vector((0.3, 0, 0)))
    walk_to(c["people"]["m2"], car_.location + Vector((-3.5, -6.5, 0)), car_.location + Vector((-1.0, -1.9, 0)), sec, speed=0.8)
    c["focus"] = c["people"]["wife"].bone_head("head")


def c4_12a(c, t):         # the doctor clips the film to the lightbox, then steps back to look (medium, from the side)
    sec = S("ch4_12a", t); hide(c, ("doc",))
    h = c["people"]["doc"]; lb = c["lightbox"]; floor_lb = lb + Vector((0, 0, -lb.z))
    clip = lb + Vector((0.0, -0.02, 0.0))
    if sec < 1.1:                       # clipping: close to the wall, hands at the film at face height
        loc = floor_lb + Vector((0.15, -0.42, 0)); stand_at(h, loc, floor_lb)
        sd = forward(h).cross(Vector((0, 0, 1))); k = ease(min(1.0, sec / 0.7))
        f_ = (h.bone_head("spine02") + forward(h) * 0.25).lerp(clip, k)
        reach(h, "R", f_ + sd * 0.15, Vector((sd.x, sd.y, -1.0)), forward(h)); reach(h, "L", f_ - sd * 0.15, Vector((-sd.x, -sd.y, -1.0)), forward(h))
        fingers_curl(h, 50, thumb=40)
        c["film"].location = f_
    else:                               # steps back, arms down, studying it
        k = ease(min(1.0, (sec - 1.1) / 0.9))
        loc = floor_lb + Vector((0.15, -0.42 - 0.5 * k, 0)); stand_at(h, loc, floor_lb)
        arms_relaxed(h); h.rot("head", forward(h).cross(Vector((0, 0, 1))), 4)
        c["film"].location = clip
    c["film"].rotation_euler = (0, 0, 0)
    c["focus"] = h.bone_head("head")


def c4_12b(c, t):         # studies it, then switches the lightbox off (driver at frame 60)
    sec = S("ch4_12b", t); hide(c, ("doc",))
    h = c["people"]["doc"]; lb = c["lightbox"]; loc = lb + Vector((0.4, -0.55, -lb.z))
    c["film"].location = lb + Vector((0, -0.02, 0.0))
    stand_at(h, loc, lb + Vector((0, 0, -lb.z)), crossed=sec < 2.0)
    if sec >= 2.0:
        sd = forward(h).cross(Vector((0, 0, 1)))
        reach(h, "R", lb + Vector((0.55, -0.08, -0.25)), Vector((sd.x, sd.y, -1.0)), forward(h))
    c["focus"] = h.bone_head("head")


def c4_13a(c, t):
    S("ch4_13a", t); hide(c, ())
    c["focus"] = OR_ + Vector((0, 0, 0.9))


def c4_13b(c, t):
    sec = S("ch4_13b", t); hide(c, ())
    leaves(c, ease(min(1.0, sec / dur("ch4_13b"))))
    c["focus"] = COR + Vector((14.0, 0, 1.3))


def c1_11a(c, t):         # local clinic, evening: a nurse adjusts the drip line at shoulder height beside the beds (medium)
    sec = S("ch1_11a", t); hide(c, ("nurse", "m1", "m2", "pat2"))
    for nm, cc in (("m1", c["cots"][0]), ("m2", c["cots"][1]), ("pat2", c["cots"][2])):
        lie_in_bed(c["people"][nm], cc + Vector((0, 0.9, 0)), (0, -1), 0.69)
    h = c["people"]["nurse"]; pole = c["cots"][1] + Vector((-0.6, 0.7, 0)); loc = pole + Vector((-0.25, -0.5, 0))
    stand_at(h, loc, pole + Vector((0.12, 0, 0)))
    sd = forward(h).cross(Vector((0, 0, 1)))
    sh = h.bone_head("upperarm01.R").z
    reach(h, "R", pole + Vector((0.12, -0.04, sh - 0.05 + 0.02 * math.sin(sec * 2))), Vector((sd.x, sd.y, -1.0)), forward(h))
    fingers_curl(h, 60, thumb=40)
    h.rot("head", sd, -4)
    drape_blankets(c)
    c["focus"] = h.bone_head("head")


def c1_11b(c, t):         # the men walk out of the clinic door into the dark street
    sec = S("ch1_11b", t); hide(c, ("m1", "m2"))
    door = CLINIC + Vector((2.4, -2.5, 0))
    walk_to(c["people"]["m1"], door + Vector((0, 1.2, 0)), door + Vector((3.5, -4.0, 0)), sec, speed=0.8)
    walk_to(c["people"]["m2"], door + Vector((0, 2.0, 0)), door + Vector((2.5, -4.4, 0)), sec - 0.6, speed=0.75)
    c["focus"] = c["people"]["m1"].arm.location + Vector((0, 0, 1.3))


SHOTS = {
    "ch1_11a": ("night", c1_11a, C(CLINIC + Vector((1.6, -1.8, 1.6)), CLINIC + Vector((1.3, -1.6, 1.55)), CLINIC + Vector((-0.5, 1.4, 1.1)), 28), 4.0),
    "ch1_11b": ("night", c1_11b, C(CLINIC + Vector((7.5, -9.0, 1.5)), CLINIC + Vector((7.0, -8.6, 1.5)), CLINIC + Vector((3.0, -3.5, 1.2)), 32), 4.0),
    "ch2_1a": ("day", c2_1a, C(EXT + Vector((7.0, -24.0, 1.0)), EXT + Vector((6.2, -23.0, 1.3)), EXT + Vector((0, -10.0, 2.5)), 28), None),
    "ch2_1b": ("day", c2_1b, C(COR + Vector((-4.5, -1.1, 1.5)), COR + Vector((-4.8, -1.0, 1.45)), COR + Vector((-8.0, 1.2, 1.0)), 30), 4.0),
    "ch2_2a": ("day", c2_2a, C(COR + Vector((-6.6, -1.1, 1.3)), COR + Vector((-6.8, -1.0, 1.3)), COR + Vector((-7.6, 1.2, 1.1)), 40), 2.8),
    "ch2_2b": ("day", c2_2b, C(COR + Vector((-10.8, -1.2, 1.5)), COR + Vector((-10.5, -1.1, 1.5)), COR + Vector((-7.0, 0.2, 1.2)), 30), 4.0),
    "ch2_3a": ("day", c2_3a, C(WARD + Vector((-2.6, -1.4, 1.4)), WARD + Vector((-2.3, -1.2, 1.35)), BEDS[2] + Vector((-0.4, 0.2, 0.9)), 35), 2.8),
    "ch2_3b": ("day", c2_3b, C(BEDS[2] + Vector((-1.6, -1.5, 1.45)), BEDS[2] + Vector((-1.45, -1.3, 1.45)), BEDS[2] + Vector((0.3, 0.4, 1.0)), 38), 2.8),
    "ch2_4a": ("day", c2_4a, C(WARD + Vector((1.3, 0.4, 1.5)), WARD + Vector((1.1, 0.2, 1.5)), WARD + Vector((0.2, -3.2, 1.45)), 32), 4.0),
    "ch2_4b": ("day", c2_4b, C(WARD + Vector((-1.8, 1.8, 1.6)), WARD + Vector((-1.2, 0.8, 1.6)), WARD + Vector((0.2, -3.2, 1.55)), 40), 2.8),
    "ch2_5a": ("day", c2_5a, C(BEDS[2] + Vector((-2.2, -2.4, 1.5)), BEDS[2] + Vector((-2.0, -2.2, 1.5)), BEDS[2] + Vector((0.9, -0.6, 1.5)), 38), 2.8),
    "ch2_6a": ("day", c2_6a, C(COR + Vector((4.2, -0.9, 1.55)), COR + Vector((4.0, -0.8, 1.55)), COR + Vector((1.4, -0.25, 1.4)), 32), 2.8),
    "ch2_6b": ("day", c2_6b, C(COR + Vector((-2.8, 0.9, 1.55)), COR + Vector((-2.6, 0.8, 1.55)), COR + Vector((1.4, -0.2, 1.4)), 35), 4.0),
    "ch4_1a": ("day", c4_1a, C(WARD + Vector((-6.0, -2.6, 1.7)), WARD + Vector((5.0, -2.6, 1.7)), WARD + Vector((-4.0, 2.2, 0.8)), 28, WARD + Vector((5.0, 2.2, 0.8))), 4.0),
    "ch4_1b": ("day", c4_1b, C(BEDS[2] + Vector((1.6, -3.4, 1.5)), BEDS[2] + Vector((1.4, -3.1, 1.5)), BEDS[2] + Vector((0.1, -1.5, 1.3)), 35), 2.8),
    "ch4_2a": ("day", c4_2a, C(LAB + Vector((1.2, 0.6, 1.5)), LAB + Vector((1.0, 0.4, 1.5)), LAB + Vector((-0.9, -1.6, 1.55)), 35), 2.8),
    "ch4_2b": ("day", c4_2b, C(LAB + Vector((1.9, 0.2, 1.4)), LAB + Vector((1.7, 0.0, 1.4)), LAB + Vector((0.3, -1.6, 1.1)), 35), 2.8),
    "ch4_3a": ("day", c4_3a, C(BEDS[1] + Vector((1.8, -3.3, 1.5)), BEDS[1] + Vector((1.6, -3.1, 1.5)), BEDS[1] + Vector((-0.7, 0.0, 1.25)), 30), 2.8),
    "ch4_3b": ("morning", c4_3b, C(WARD + Vector((-4.5, -2.8, 1.4)), WARD + Vector((-4.0, -2.6, 1.4)), BEDS[2] + Vector((0, 0.5, 1.0)), 32), 4.0),
    "ch4_11a": ("morning", c4_11a, C(EXT + Vector((-12.0, -27.0, 1.6)), EXT + Vector((-11.0, -26.0, 1.6)), EXT + Vector((-2.0, -9.0, 4.0)), 24), 5.6),
    "ch4_11b": ("morning", c4_11b, C(EXT + Vector((5.0, -26.0, 1.5)), EXT + Vector((5.6, -25.5, 1.5)), EXT + Vector((10.6, -20.0, 1.2)), 32), 4.0),
    "ch4_12a": ("day", c4_12a, C(OFFICE + Vector((-1.5, -0.4, 1.6)), OFFICE + Vector((-1.3, -0.2, 1.6)), OFFICE + Vector((0.1, 1.5, 1.5)), 32), 2.8),
    "ch4_12b": ("day", c4_12b, C(OFFICE + Vector((1.6, -0.8, 1.6)), OFFICE + Vector((1.4, -0.6, 1.6)), OFFICE + Vector((0.1, 1.5, 1.5)), 32), 2.8),
    "ch4_13a": ("day", c4_13a, C(OR_ + Vector((2.3, -2.5, 1.75)), OR_ + Vector((2.0, -2.2, 1.75)), OR_ + Vector((0, 0, 1.45)), 24), None),
    "ch4_13b": ("day", c4_13b, C(COR + Vector((2.0, 0.0, 1.6)), COR + Vector((8.0, 0.0, 1.6)), COR + Vector((15.0, 0.0, 1.4)), 30), 5.6),
}
VARIANT_FOR = {k: v[0] for k, v in SHOTS.items()}
DUR = {k: dur(k) for k in SHOTS}


def _focus(c, t):
    return c.get("focus", WARD + Vector((0, 0, 1)))


from durs import title_for
MOVES = {k: {**dict(kind="anim", far=200.0, anim=v[1], cam=v[2], dof=v[3], focus=_focus), **({'title': title_for(k), 'dof': None} if title_for(k) else {})} for k, v in SHOTS.items()}
