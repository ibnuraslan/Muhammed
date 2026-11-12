"""CH3 (chat B): 1981 domestic sets (generic, unnamed people; no act of any crime is shown).
  evening:  a living room at night, a generic map board game (no brand) on the coffee table under a warm lamp.
            game   (A): low over the board: four figures around it (cropped, soft), one rolls the dice
  nextday:  the same room in flat grey morning light: two detectives search it.
            search (B): one lifts the sofa cushions, the other opens the sideboard; they find nothing and leave
  flat:     a plain 1970s rented block at dusk; a moped with a spade strapped to its side idles at the kerb.
            moped  (A): low push past the moped, exhaust drifting
            curtain(B): the landlord behind a lace curtain upstairs watches; slow push toward the window
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

EXPOSURE = 0.2
DUR = {"game": 5.0, "search": 6.0, "moped": 5.0, "curtain": 5.5}
VARIANT_FOR = {"game": "evening", "search": "nextday", "moped": "flat", "curtain": "flat"}
CT = Vector((0.0, 0.0, 0.0))        # coffee table centre


def board_image(path, W=1400, H=1000):
    """A generic map board game: an invented continent map of coloured territories (no text, no brand)."""
    if os.path.exists(path):
        return path
    import skia
    rng = np.random.default_rng(3)
    s = skia.Surface(W, H); cv = s.getCanvas(); cv.clear(skia.Color4f(0.12, 0.22, 0.32, 1))
    p = skia.Paint(AntiAlias=True)
    cols = [(0.55, 0.42, 0.2), (0.35, 0.45, 0.22), (0.6, 0.35, 0.25), (0.45, 0.4, 0.3), (0.3, 0.38, 0.3), (0.62, 0.55, 0.3)]
    for k in range(26):                                   # territories: irregular blobs
        cx, cy = rng.uniform(150, W - 150), rng.uniform(120, H - 120)
        path_ = skia.Path(); n = 9
        for j in range(n):
            a = j / n * 2 * math.pi; r = rng.uniform(60, 130)
            x, y = cx + r * math.cos(a), cy + r * 0.8 * math.sin(a)
            path_.moveTo(x, y) if j == 0 else path_.lineTo(x, y)
        path_.close()
        p.setStyle(skia.Paint.kFill_Style); p.setColor4f(skia.Color4f(*cols[k % len(cols)], 1)); cv.drawPath(path_, p)
        p.setStyle(skia.Paint.kStroke_Style); p.setStrokeWidth(3); p.setColor4f(skia.Color4f(0.15, 0.12, 0.08, 1)); cv.drawPath(path_, p)
    p.setStyle(skia.Paint.kStroke_Style); p.setStrokeWidth(14); p.setColor4f(skia.Color4f(0.45, 0.32, 0.15, 1))
    cv.drawRect(skia.Rect.MakeXYWH(7, 7, W - 14, H - 14), p)
    s.makeImageSnapshot().save(path, skia.kPNG)
    return path


def moped(name, loc, rot_z):
    """A small 1970s moped (two spoked wheels, tube frame, tank, saddle) with a spade strapped along its side."""
    tube = pbr("MopedRed", (0.35, 0.05, 0.04), 0.35, 0.3, **{'Coat Weight': 0.6})
    chrome = pbr("MChrome", (0.8, 0.8, 0.82), 0.15, 1.0); rub = pbr("MRubber", (0.02, 0.02, 0.02), 0.7)
    parts = [box("Tank", (0.12, 0, 0.72), (0.32, 0.18, 0.16), tube, bevel=0.05)]     # unrotated first: join keeps its transform
    for x in (-0.55, 0.55):                                # wheels (along local X), axle along Y
        bpy.ops.mesh.primitive_torus_add(major_radius=0.25, minor_radius=0.055, location=(x, 0, 0.31), rotation=(math.radians(90), 0, 0))
        t = bpy.context.active_object; t.data.materials.append(rub); parts.append(t)
        parts.append(cyl("Rim", (x, 0, 0.31), 0.2, 0.02, chrome, verts=32, rot=(math.radians(90), 0, 0)))
        parts.append(cyl("Hub", (x, 0, 0.31), 0.05, 0.08, chrome, verts=16, rot=(math.radians(90), 0, 0)))
    def bar(a, b, r, m):
        a = Vector(a); b = Vector(b); d = b - a
        o = cyl("Bar", (a + b) / 2, r, d.length, m, verts=12)
        o.rotation_mode = 'QUATERNION'; o.rotation_quaternion = d.to_track_quat('Z', 'Y'); return o
    parts += [bar((0.55, 0, 0.31), (0.42, 0, 0.95), 0.02, chrome),       # fork
              bar((0.42, 0, 0.92), (-0.1, 0, 0.55), 0.03, tube),          # down tube
              bar((-0.1, 0, 0.55), (-0.55, 0, 0.31), 0.022, tube),        # chain stay
              bar((-0.1, 0, 0.55), (-0.25, 0, 0.78), 0.022, tube),        # seat post
              bar((0.38, -0.3, 1.02), (0.38, 0.3, 1.02), 0.012, chrome)]  # handlebar
    parts.append(box("Engine", (0.0, 0, 0.4), (0.25, 0.16, 0.2), pbr("Engine", (0.18, 0.18, 0.19), 0.5, 0.6), bevel=0.02))
    parts.append(box("Saddle", (-0.28, 0, 0.82), (0.32, 0.17, 0.07), pbr("Saddle", (0.03, 0.03, 0.03), 0.5), bevel=0.03))
    parts.append(box("Carrier", (-0.52, 0, 0.72), (0.3, 0.2, 0.02), chrome))
    parts.append(bar((-0.35, 0.08, 0.35), (-0.75, 0.08, 0.42), 0.02, chrome))  # exhaust
    parts.append(cyl("Lamp", (0.47, 0, 1.0), 0.07, 0.08, chrome, verts=24, rot=(0, math.radians(90), 0)))
    o = join(parts, name)
    # the spade, strapped along the left side, blade down by the rear wheel, a strap round the carrier
    try:
        sp, ms = ph.model("rusted_spade_01", loc=(0, 0, 0))
        sp.parent = o; sp.location = (-0.2, -0.19, 0.62); sp.rotation_euler = (0, math.radians(68), 0); sp.scale = (0.95, 0.95, 0.95)
    except Exception as e:
        print("[home81] spade:", e)
    box("Strap", (-0.48, -0.14, 0.74), (0.04, 0.12, 0.03), pbr("Strap", (0.05, 0.04, 0.03), 0.8)).parent = o
    o.location = loc; o.rotation_euler = (0, 0, rot_z)
    return o


def facade(c, night_windows):
    """A plain three-storey 1970s rented block: rendered wall, rows of windows with frames, a front door."""
    wall = B.tex_mat("BlockWall", "grey_plaster_02", scale=0.4, tint=(0.75, 0.72, 0.65))
    W = 22.0; Hh = 9.0; y0 = 4.0
    hx0, hx1, hz0, hz1 = -1.85, -0.55, 3.5, 4.9                     # the landlord's window opening
    box("BlockWallL", ((-W / 2 + hx0) / 2, y0 + 0.2, Hh / 2), (hx0 + W / 2, 0.4, Hh), wall)
    box("BlockWallR", ((W / 2 + hx1) / 2, y0 + 0.2, Hh / 2), (W / 2 - hx1, 0.4, Hh), wall)
    box("BlockWallB", ((hx0 + hx1) / 2, y0 + 0.2, hz0 / 2), (hx1 - hx0, 0.4, hz0), wall)
    box("BlockWallT", ((hx0 + hx1) / 2, y0 + 0.2, (Hh + hz1) / 2), (hx1 - hx0, 0.4, Hh - hz1), wall)
    rw = B.plaster("LLRoom", (0.4, 0.33, 0.25)) if False else pbr("LLRoom", (0.35, 0.28, 0.2), 0.8)
    box("LLBack", (-1.2, y0 + 3.0, 4.2), (4, 0.1, 2.8), rw); box("LLSideL", (-3.2, y0 + 1.7, 4.2), (0.1, 2.6, 2.8), rw)
    box("LLSideR", (0.8, y0 + 1.7, 4.2), (0.1, 2.6, 2.8), rw); box("LLCeil", (-1.2, y0 + 1.7, 5.62), (4, 2.6, 0.05), rw)
    fr = pbr("WinFrameW", (0.75, 0.73, 0.68), 0.5)
    try:
        import rj
        wg = rj.window_glass(); lace = rj.net_curtain()
    except Exception:
        wg = glass("WG", (0.9, 0.9, 0.9), 0.05); lace = pbr("Lace", (0.85, 0.84, 0.8), 0.8, **{'Transmission Weight': 0.5})
    c["windows"] = []
    for fl in range(3):
        for k in range(8):
            x = -9.0 + k * 2.6; z = 1.4 + fl * 2.8
            if abs(x + 1.2) < 0.1 and fl == 1:               # the landlord's real window: a hollow frame only
                for (dx, dz, sx, sz) in ((0, 0.68, 1.3, 0.06), (0, -0.68, 1.3, 0.06), (0.62, 0, 0.06, 1.4), (-0.62, 0, 0.06, 1.4)):
                    box("FrameRing", (x + dx, y0 - 0.005, z + dz), (sx, 0.06, sz), fr)
                continue
            box("Frame", (x, y0 - 0.005, z), (1.3, 0.06, 1.4), fr)
            if abs(x + 1.2) < 0.1 and fl == 1:
                continue                                      # the real window (opening) is built separately
            lit_ = (k * 3 + fl) % 5 in night_windows
            box("Pane", (x, y0 - 0.035, z), (1.18, 0.01, 1.28),
                emissive("RoomLit", (1.0, 0.66, 0.38), 1.1) if lit_ else pbr("DarkPane", (0.004, 0.0045, 0.005), 0.3))
            box("Curt", (x - 0.4, y0 - 0.04, z), (0.3, 0.01, 1.22), fabric("CurtF", (0.3, 0.26, 0.2) if not lit_ else (0.55, 0.38, 0.2), 0.9, 0.3, 200))
            c["windows"].append((x, z))
    # the landlord's window (first floor, left of the door) gets a lace curtain
    x, z = -1.2, 1.4 + 2.8
    lace = pbr("LaceB", (0.85, 0.83, 0.78), 0.8, **{'Alpha': 0.45, 'Transmission Weight': 0.3})
    cur = box("Lace", (x, y0 + 0.1, z), (1.15, 0.01, 1.25), lace)
    c["lace"] = cur; c["lwin"] = Vector((x, y0, z))
    box("Door", (1.4, y0 - 0.02, 1.1), (1.1, 0.06, 2.2), pbr("BlockDoor", (0.2, 0.15, 0.1), 0.5))
    box("Canopy", (1.4, y0 - 0.5, 2.35), (1.6, 1.0, 0.08), pbr("Canopy", (0.3, 0.3, 0.3), 0.6))
    box("Pavement", (0, y0 - 2.0, 0.06), (W + 10, 4.0, 0.12), B.tex_mat("Pav", "concrete_pavers", scale=0.5, tint=(0.55, 0.55, 0.55)))
    box("Kerb", (0, y0 - 4.05, 0.07), (W + 10, 0.15, 0.14), pbr("Kerb", (0.45, 0.45, 0.44), 0.7))
    box("Street", (0, y0 - 9.0, 0.0), (W + 40, 10, 0.02), B.tex_mat("Str", "asphalt_02", scale=0.25, tint=(0.45, 0.45, 0.45)))


def build(variant=None):
    variant = variant or "evening"
    c = {"variant": variant}
    rng = np.random.default_rng(9)
    if variant in ("evening", "nextday"):
        world_flat((0.006, 0.007, 0.01), 1.0)
        box("Floor", (0, 0, -0.01), (6, 5, 0.02), B.tex_mat("Carpet81", "dirty_carpet", scale=0.5, tint=(0.55, 0.42, 0.3)))
        try:
            import rj
            paper = rj.wallpaper("Wall81", (0.42, 0.36, 0.26), (0.36, 0.3, 0.2))
        except Exception:
            paper = B.plaster("Wall81", (0.42, 0.36, 0.26))
        for (loc, size) in (((0, 2.5, 1.3), (6, 0.1, 2.6)), ((-3, 0, 1.3), (0.1, 5, 2.6)), ((3, 0, 1.3), (0.1, 5, 2.6)), ((0, -2.5, 1.3), (6, 0.1, 2.6))):
            box("W81", loc, size, paper)
        box("Ceil81", (0, 0, 2.62), (6, 5, 0.04), B.plaster("C81", (0.55, 0.52, 0.46)))
        ph.model("Sofa_01", loc=(0, 1.15, 0), rot_z=0)                      # faces -Y, the table
        ph.model("ArmChair_01", loc=(-1.25, 0.0, 0), rot_z=math.radians(-90))
        ph.model("ArmChair_01", loc=(1.25, 0.0, 0), rot_z=math.radians(90))
        tbl, _ = ph.model("CoffeeTable_01", loc=(0, 0, 0), rot_z=0, scale=0.7)
        top = 0.53 * 0.7
        c["top"] = top
        img = board_image(os.path.join(B.GEN, "b_board.png"))
        c["board"] = B.sheet("Board", (0, 0.0, top + 0.005), (0.72, 0.52), B.img_mat("BoardM", img, 0.6))
        cols = [(0.6, 0.05, 0.04), (0.05, 0.1, 0.5), (0.85, 0.75, 0.1), (0.1, 0.35, 0.1)]
        for k in range(46):
            x, y = rng.uniform(-0.32, 0.32), rng.uniform(-0.22, 0.22)
            box("Piece", (x, y, top + 0.012), (0.012, 0.012, 0.012), pbr(f"Piece{k % 4}", cols[k % 4], 0.4))
        c["dice"] = [box(f"Die{k}", (0, 0, -30), (0.016, 0.016, 0.016), pbr("Die", (0.9, 0.88, 0.82), 0.3), bevel=0.003) for k in range(3)]
        ph.model("painted_wooden_cabinet", loc=(2.3, 2.15, 0), rot_z=0)        # the sideboard
        ph.model("Television_01", loc=(-2.3, 2.1, 0.0), rot_z=0.3)
        if variant == "evening":
            ph.model("desk_lamp_arm_01", loc=(1.7, 1.2, 0), rot_z=2.6, scale=1.0)
            B.key_spot((0.4, 0.2, 1.8), (0.0, 0.0, top), 260, 55, (1.0, 0.68, 0.38), soft=0.15, name="GameLamp")
            B.fill((-2.5, -2.0, 2.0), (0, 0, 0.6), 10, 1.5, (0.4, 0.5, 0.75))
            seats = [((-0.35, 1.0), math.radians(10)), ((0.35, 1.0), math.radians(-10)), ((-1.15, 0.0), math.radians(-90)), ((1.15, 0.0), math.radians(90))]
            looks = [(1.0, 41, "male_casualsuit05", "short02"), (0.0, 38, "female_elegantsuit01", "long01"),
                     (1.0, 45, "male_casualsuit03", "short04"), (0.0, 43, "female_elegantsuit01", "bob02")]
            c["players"] = []
            for (xy, fz), (g, yrs, cl, hr) in zip(seats, looks):
                h = B.person(f"Player{len(c['players'])}", g, yrs, cl, hr, hue=0.08 + 0.05 * len(c["players"]), sat=0.4, val=0.38, hair_val=0.35)
                B.seat(h, (xy[0], xy[1], 0), fz, lean=22)
                B.ground(h, 0.08)
                c["players"].append(h)
            c["rest"] = [B.capture(h) for h in c["players"]]
        else:
            sky = box("Win81", (-2.95, 0.0, 1.4), (0.02, 1.6, 1.3), emissive("GreyDay", (0.75, 0.8, 0.86), 1.5)); sky.visible_shadow = False
            B.key_spot((-2.8, 0.0, 1.6), (0.5, 0.5, 0.5), 1400, 70, (0.82, 0.88, 0.98), soft=0.8, name="WinKey")
            B.fill((2.5, -2.0, 2.0), (0, 0, 0.6), 15, 1.5, (0.5, 0.55, 0.7))
            c["cushion"] = box("Cushion", (-0.35, 1.05, 0.48), (0.6, 0.55, 0.12), fabric("CushF", (0.35, 0.25, 0.15), 0.9, 0.5, 300), bevel=0.04)
            d1 = B.person("Det1", 1.0, 46, "male_casualsuit05", "short02", hue=0.08, sat=0.35, val=0.45, hair_val=0.5)
            d2 = B.person("Det2", 1.0, 36, "male_elegantsuit01", "short04", hue=0.08, sat=0.25, val=0.35, hair_val=0.3)
            B.stand(d1, (-0.35, 0.45, 0), math.pi); B.stand(d2, (2.3, 1.45, 0), math.pi)
            c["d1"], c["d2"] = d1, d2
            c["rest"] = [B.capture(d1), B.capture(d2)]
        B.room_haze((0, 0, 1.3), (5.8, 4.8, 2.6), density=0.015)
    else:
        try:
            import rj
            rj.sky("dusk")
        except Exception:
            world_flat((0.05, 0.06, 0.1), 1.0)
        bpy.context.scene.view_settings.exposure += 0.7       # dusk exterior: open up
        facade(c, night_windows=(0, 2))
        c["moped"] = moped("Moped", (-1.0, 1.0, 0.12), math.radians(8))
        c["exhaust"] = B.smoke((-1.8, 1.08, 0.5), density=0.25, size=(0.5, 0.5, 1.0))
        ph.model("street_lamp_01", loc=(-6.0, 0.4, 0.12), rot_z=math.radians(-90))
        B.key_spot((-6.0, -0.6, 5.0), (-1.0, 1.0, 0.5), 2500, 50, (1.0, 0.65, 0.35), soft=0.2, name="Sodium")
        B.fill((4, -10, 4), (0, 3, 2), 1500, 8, (0.4, 0.5, 0.85))
        lw = c["lwin"]
        land = B.person("Landlord", 1.0, 63, "male_casualsuit05", "short02", hue=0.1, sat=0.2, val=0.4, hair_val=1.6, hair_sat=0.1)
        B.stand(land, (lw.x + 0.15, lw.y + 0.75, 0), 0.0, z=2.8 + 0.0)
        c["landlord"] = land
        box("UpFloor", (lw.x, lw.y + 1.0, 2.79), (3, 2, 0.02), pbr("UpF", (0.2, 0.15, 0.1), 0.8))
        B.practical((lw.x + 0.4, lw.y + 2.2, 4.9), 160, (1.0, 0.68, 0.38), 0.3, "LandlordLamp")
        B.room_haze((0, -2, 3), (30, 14, 6), density=0.004, color=(0.75, 0.78, 0.9))
    if variant in ("evening", "nextday"):
        B.finish_interior(lift=0.0)
    else:
        B.preview_cap()
    return c


def anim(c, t, move):
    sec = t * DUR[move]
    v = c["variant"]
    if v == "evening":
        for h, P0 in zip(c["players"], c["rest"]):
            B.apply_pose(h, P0)
        top = c["top"]
        for k, h in enumerate(c["players"]):
            fwd = B.fwd_of(h); side = fwd.cross(Vector((0, 0, 1))).normalized()
            for sd, sg in (("L", -1), ("R", 1)):
                k_ = h.bone_tail(f"upperleg02.{sd}")
                reach(h, sd, k_ + Vector((0, 0, 0.06)) + fwd * 0.08, Vector((sg * side.x, sg * side.y, -0.6)), fwd + Vector((0, 0, -0.7)))
            fingers_curl(h, 30)
            B.nod(h, 22 + 3 * math.sin(sec * 0.5 + k))
        # dice: thrown at 1.0 s from the near edge, tumble across the board, settle
        for k, d in enumerate(c["dice"]):
            u = min(1.0, max(0.0, (sec - 1.0 - 0.05 * k) / 1.1))
            p0 = Vector((-0.28 + 0.03 * k, -0.3, top + 0.12)); p1 = Vector((0.05 + 0.06 * k, 0.02 - 0.04 * k, top + 0.013))
            p = p0.lerp(p1, ease(u)); p.z += 0.06 * abs(math.sin(u * math.pi * 2.5)) * (1 - u)
            d.location = p if sec > 0.9 else Vector((0, 0, -30))
            d.rotation_euler = (u * 9 + k, u * 7, u * 5 + k)
    elif v == "nextday":
        d1, d2 = c["d1"], c["d2"]
        for h, P0 in zip((d1, d2), c["rest"]):
            B.apply_pose(h, P0)
        u = ease(min(1.0, max(0.0, (sec - 0.6) / 1.2))) * (1 - ease(min(1.0, max(0.0, (sec - 3.4) / 1.0))))
        cu = c["cushion"]; cu.location = Vector((-0.35, 1.05, 0.48)) + Vector((0, -0.25 * u, 0.35 * u)); cu.rotation_euler = (math.radians(-55 * u), 0, 0)
        for sd, dx in (("L", -0.25), ("R", 0.25)):
            reach(d1, sd, cu.location + Vector((dx, -0.25, 0.0)), Vector((dx * 3, -0.5, -0.8)), Vector((0, 1, -0.3)))
        fingers_curl(d1, 40); B.nod(d1, 18 * (0.4 + 0.6 * u), "spine03"); B.nod(d1, 20)
        reach(d2, "R", Vector((2.45, 1.85, 0.9)), Vector((0.5, -0.6, -0.6)), Vector((0, 1, 0)))
        reach(d2, "L", Vector((2.1, 1.85, 0.95)), Vector((-0.5, -0.6, -0.6)), Vector((0, 1, 0)))
        fingers_curl(d2, 35); B.nod(d2, 15)
    else:
        mo = c["moped"]
        mo.location.z = 0.12 + 0.002 * math.sin(sec * 40)              # idling engine shiver
        land = c["landlord"]
        land.rot("head", (0, 0, 1), 6 * math.sin(sec * 0.4)); B.nod(land, 12)
        lc = c["lace"]; op = ease(min(1.0, max(0.0, (sec - 1.0) / 1.5)))
        lc.location.x = c["lwin"].x - 0.38 * op
        lc.scale.x = 1.0 - 0.62 * op
    bpy.context.view_layer.update()


def cam(a, b, tgt, lens):
    return lambda c, t: (Vector(a).lerp(Vector(b), ease(t)), Vector(tgt), lens)


MOVES = {
    "game": dict(kind="anim", dof=2.0, cam=cam((0.25, -0.75, 1.25), (0.15, -0.55, 1.08), (0.0, 0.02, 0.38), 35),
                 anim=lambda c, t: anim(c, t, "game"), focus=lambda c, t: Vector((0.05, 0.0, 0.4))),
    "search": dict(kind="anim", dof=4.0, cam=cam((-2.4, -2.1, 1.65), (-2.1, -1.7, 1.6), (0.6, 1.0, 0.8), 28),
                   anim=lambda c, t: anim(c, t, "search"), focus=lambda c, t: c["d1"].bone_head("spine03")),
    "moped": dict(kind="anim", dof=2.8, cam=cam((1.6, -2.0, 0.65), (0.9, -1.5, 0.6), (-1.0, 1.0, 0.6), 32),
                  anim=lambda c, t: anim(c, t, "moped"), focus=lambda c, t: c["moped"].location + Vector((0, 0, 0.5))),
    "curtain": dict(kind="anim", dof=4.0, cam=cam((-0.2, -6.0, 1.6), (-0.6, -3.8, 2.2), (-1.2, 4.0, 4.1), 35),
                    anim=lambda c, t: anim(c, t, "curtain"), focus=lambda c, t: c["lwin"]),
}
