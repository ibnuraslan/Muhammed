"""THE BOUTIQUE, Chapter Two (December 2008): the same nameless jeweller, now at Christmas dusk.
  xmas     (ch2 1A, title): dusk track down the avenue: soft, sparse warm lights wound round the plane trees, shoppers with bags
  door     (ch2 1B): four figures in long coats and wigs step past a guard who holds the door
  wig      (ch2 2A): upstairs, a wig drops onto the carpet as the camera rises to a man walking away
  floor16  (ch2 2B): wide from the landing: sixteen people sitting on the salon floor, one man standing by the stairs
  suitcase (ch2 3A): medium-wide: a robber loads velvet trays into an open suitcase on the carpet
  panel    (ch2 3B): a wooden wall panel slides open on a concealed compartment of lit stands
  grenade  (ch2 4A): far down the salon a man raises a small dark shape, then turns for the door (seen wide)
  getaway  (ch2 4B): outside on the avenue a dark car pulls away from the kerb into the evening traffic
  after    (ch2 5A): the empty salon after hours: open cases, fallen trays, a slow push through the quiet
"""
import math
import numpy as np
import bpy
from mathutils import Vector
from kit import *
import dd
from dd import person, place, face_to, walk_to, arms_relaxed, pose_floor_sit, zero, ground
from human import reach, fingers_curl, pose_walk
from sc_street import car
import sc_boutique as B0
from sc_boutique import haussmann, street, show_lights, salon_room, vitrine, mats, WARM, arms_relaxed_one

EXPOSURE = 0.2
DUR = {k: 9.0 for k in ("xmas", "door", "wig", "floor16", "suitcase", "panel", "grenade", "getaway", "after")}
VARIANT_FOR = {"xmas": "xmas", "door": "xmas", "getaway": "xmas", "wig": "upstairs", "floor16": "upstairs",
               "suitcase": "upstairs", "panel": "upstairs", "grenade": "upstairs", "after": "after"}


def tree_lights(base, height=6.5, turns=7, n=70, r0=0.22, seed=0):
    """Warm bulbs wound in a loose spiral up a plane-tree trunk and into the first branches: soft and sparse."""
    rng = np.random.default_rng(seed)
    bulb = emissive("XmasBulb", (1.0, 0.72, 0.38), 9.0)
    Bd = dd.Builder("TreeLights%d" % seed)
    for k in range(n):
        u = k / (n - 1)
        a = 2 * math.pi * turns * u + rng.uniform(-0.1, 0.1)
        r = r0 + 0.9 * max(0.0, u - 0.55) ** 1.2 * 2.0
        z = 0.8 + u * height
        Bd.cyl((base.x + r * math.cos(a), base.y + r * math.sin(a), z), 0.018, 0.03, bulb, verts=6)
    return Bd.done()


def shopper(name, seed, rng):
    g = 1.0 if seed % 2 else 0.0
    looks = [("male_casualsuit05", 1.1, (1, 1, 1)), ("male_elegantsuit01", 2.0, (0.6, 0.55, 0.5)), ("male_casualsuit01", 1.2, (1, 1, 1))]
    if g:
        cl, v, tn = looks[seed % 3]
        h = person(name, g, int(rng.integers(25, 65)), cl, ("short02", "short01", "short04")[seed % 3], cval=v, tint=tn, sat=0.6)
    else:
        h = person(name, g, int(rng.integers(25, 60)), "female_elegantsuit01", ("long01", "bob01", "ponytail01")[seed % 3],
                   cval=1.6, tint=((0.7, 0.3, 0.25), (0.85, 0.8, 0.72), (0.35, 0.4, 0.6))[seed % 3], sat=0.3)
    bag = box(name + "Bag", (0, 0, 0), (0.3, 0.1, 0.34), pbr(name + "BagM", ((0.75, 0.68, 0.55), (0.1, 0.1, 0.12), (0.55, 0.08, 0.08))[seed % 3], 0.6))
    return h, bag


def build_xmas(c):
    world_sky(sun_elev_deg=-4, sun_rot_deg=240, strength=1.4, tint=(0.55, 0.65, 1.0))
    blk, info = haussmann(-11, 11, seed=1, boutique=True, lit_frac=0.5)
    for a, b, sd in ((-34, -11, 2), (11, 33, 3), (33, 55, 4), (-56, -34, 5)):
        haussmann(a, b, seed=sd, lit_frac=0.45)
    show_lights(info); c["info"] = info
    street(c)
    for k in range(-5, 6):
        l = bpy.data.lights.new("StreetL", 'POINT'); l.energy = 250; l.color = (1.0, 0.72, 0.42)
        o = bpy.data.objects.new("StreetL", l); bpy.context.collection.objects.link(o); o.location = (k * 11.0 + 3.0, -5.4, 4.4)
    rng = np.random.default_rng(12)
    for k in range(-4, 5):
        x = k * 9.0 - 1.5
        tree_lights(Vector((x, -4.6, 0)), seed=k + 10)
    # a single garland of bulbs along the awnings
    bulb = emissive("Garland", (1.0, 0.78, 0.45), 7.0)
    G = dd.Builder("Garland")
    for i in range(140):
        x = -10.5 + 21.0 * i / 139
        sag = 0.25 * math.sin(math.pi * ((x + 10.5) % 7.0) / 7.0)
        G.cyl((x, -1.55, 4.55 - sag), 0.02, 0.035, bulb, verts=6)
    G.done()
    # shoppers walking both ways along the pavement
    c["shoppers"] = []
    for k in range(7):
        h, bag = shopper(f"Shop{k}", k, rng)
        dirx = 1 if k % 2 else -1
        y = -3.3 + rng.uniform(-1.2, 1.2)
        start = Vector((-dirx * (6 + 3.5 * k), y, 0.06))
        c["shoppers"].append((h, bag, start, Vector((dirx * 30, y, 0.06)), rng.uniform(0.8, 1.15)))
    # the guard at the door, and the four disguised figures (long coats, wigs) for the door shot
    g = dd.guard("DoorGuard", 44, "short02"); c["guard"] = g
    c["disguised"] = []
    for k in range(4):
        wig = ("long01", "bob02", "long01", "bob01")[k]
        h = person(f"Disg{k}", 1.0, 30 + 6 * k, "female_elegantsuit01", wig, cval=1.4, sat=0.4,
                   tint=((0.5, 0.42, 0.36), (0.25, 0.25, 0.3), (0.6, 0.55, 0.48), (0.3, 0.32, 0.4))[k], hv=(0.5, 0.25, 0.7, 0.3)[k])
        c["disguised"].append(h)
    # door leaf that the guard holds open
    D = dd.Builder("FrontDoorLeaf"); D.box((0.55, 0, 1.6), (1.1, 0.05, 3.15), mats()["glass"])
    D.box((0.02, 0, 1.6), (0.06, 0.07, 3.2), mats()["lacquer"]).box((1.08, 0, 1.6), (0.06, 0.07, 3.2), mats()["lacquer"])
    D.box((0.95, -0.06, 1.2), (0.03, 0.03, 0.9), mats()["bronze"])
    c["leaf"] = D.done(info["door"] + Vector((-1.1, -0.06, 0)))
    gc = dd.sedan("Getaway", (0.03, 0.035, 0.04)); c["getaway"] = gc
    c["traffic"] = []
    for k, col in enumerate(((0.5, 0.5, 0.52), (0.1, 0.12, 0.2), (0.6, 0.58, 0.5))):
        cr = dd.sedan(f"Traffic{k}", col); c["traffic"].append((cr, -40 - 18 * k, -10.0 if k % 2 == 0 else -17.0, 1 if k % 2 == 0 else -1))


def build_upstairs(c, after=False):
    world_sky(sun_elev_deg=-4, sun_rot_deg=240, strength=1.2, tint=(0.55, 0.65, 1.0))
    salon_room(c, w=14.0, d=10.0, hgt=4.0)
    carpet = fabric("UpCarpet", (0.32, 0.22, 0.18), 0.95, 0.5, 500)
    box("UpFloor", (0, 5, 0.002), (13.9, 9.9, 0.004), carpet)
    haussmann(-30, 30, seed=30, rot_z=math.pi, origin=(0, -14, -5.0), lit_frac=0.45)
    rng = np.random.default_rng(31)
    # the stairs opening at the back right, with a banister
    box("StairOpen", (5.4, 8.4, 0.003), (2.2, 2.6, 0.006), pbr("StairDark", (0.03, 0.025, 0.02), 0.8))
    for k in range(10):
        cyl("Baluster", (4.3, 7.2 + k * 0.26, 0.45), 0.02, 0.9, pbr("BalW", (0.2, 0.12, 0.07), 0.4), verts=8)
    box("Banister", (4.3, 8.4, 0.92), (0.08, 2.6, 0.06), pbr("BalW2", (0.2, 0.12, 0.07), 0.35))
    c["cases"] = []
    for k, (x, y) in enumerate(((-3.0, 3.0), (0.4, 3.4), (3.4, 3.0))):
        cs, jew = vitrine(f"UVit{k}", (x, y, 0), rng=rng, lit=True); c["cases"].append((cs, jew))
    # the concealed compartment: a shallow built-in cabinet in the panelled left wall, lined in velvet, lit inside;
    # its front is a moulded panel that slides aside
    pm = pbr("PanelM", (0.72, 0.68, 0.6), 0.55)
    vel = dd.tex_mat("velour_velvet", 2.0, tint=(0.22, 0.28, 0.62), name="NicheVel", sat=0.5)
    N_ = dd.Builder("Niche")
    N_.box((-6.98, 6.0, 1.5), (0.02, 1.5, 1.3), vel)                          # back
    for z in (0.85, 2.15):
        N_.box((-6.85, 6.0, z), (0.28, 1.6, 0.04), pm)                        # bottom / top
    for y in (5.22, 6.78):
        N_.box((-6.85, y, 1.5), (0.28, 0.04, 1.34), pm)                       # sides
    N_.box((-6.85, 6.0, 1.45), (0.24, 1.5, 0.02), vel)                        # a velvet shelf
    N_.done()
    stand = pbr("NicheStand", (0.88, 0.86, 0.82), 0.45)
    for k in range(4):
        for row, z in enumerate((0.9, 1.48)):
            y = 5.5 + k * 0.33
            cyl("NStand", (-6.86, y, z + 0.05), 0.03, 0.1, stand, verts=16)
            dd.ring(f"NicheRing{k}{row}", (-6.86, y, z + 0.13), stone_r=0.005 + 0.001 * ((k + row) % 2),
                    band="plat" if (k + row) % 2 else "gold", stone=("diamond", "sapphire", "diamond", "ruby")[k])
    nl = bpy.data.lights.new("NicheL", 'AREA'); nl.shape = 'RECTANGLE'; nl.size = 1.4; nl.size_y = 0.2; nl.energy = 30; nl.color = WARM
    no = bpy.data.objects.new("NicheL", nl); bpy.context.collection.objects.link(no); no.location = (-6.82, 6.0, 2.1)
    nl2 = bpy.data.lights.new("NicheL2", 'AREA'); nl2.shape = 'RECTANGLE'; nl2.size = 1.4; nl2.size_y = 0.15; nl2.energy = 20; nl2.color = WARM
    no2 = bpy.data.objects.new("NicheL2", nl2); bpy.context.collection.objects.link(no2); no2.location = (-6.82, 6.0, 1.42)
    pnl = dd.Builder("SlidingPanel"); pnl.box((0, 0, 0), (0.04, 1.62, 1.36), pm)
    pnl.box((0.025, 0, 0), (0.01, 1.4, 1.14), pbr("PanelMould", (0.8, 0.77, 0.7), 0.5))
    c["panel"] = pnl.done((-6.7, 6.0, 1.5))
    if after:
        for cs, jew in c["cases"]:                    # emptied cases: jewels gone, a tray fallen on the carpet
            for j in jew:
                j.location.z -= 50
        for k in range(4):
            box("FallenTray", (-2.0 + k * 1.4 + rng.uniform(-0.3, 0.3), 4.6 + rng.uniform(-0.5, 0.6), 0.015), (0.4, 0.3, 0.025),
                dd.tex_mat("velour_velvet", 2.0, tint=(0.25, 0.32, 0.7), name="FallenVel", sat=0.4), rot=(0, 0, rng.uniform(0, 3)))
        c["panel"].location.y = 7.6
        for o in bpy.data.objects:                   # after hours: the big lights off, only the cases and the window glow
            if o.type == 'LIGHT' and (o.name.startswith("Chand") or o.name.startswith("CeilFill")):
                o.data.energy = 0.0
        return
    # sixteen people on the floor along the walls (staff, a customer), seen wide; robbers standing
    c["floor"] = []
    spots = [(-6.2, 1.2 + k * 0.62) for k in range(8)] + [(-4.6 + k * 0.62, 9.3) for k in range(8)]
    for k, (x, y) in enumerate(spots):
        g = 1.0 if k % 3 else 0.0
        h = dd.staff(f"Up{k}", g, 25 + (k * 7) % 35, ("short02", "bob01", "short04", "ponytail01", "short01", "bob02")[k % 6], seed=k)
        pose_floor_sit(h, hunch=14)
        tgt = (x + 2.0, y) if x < -6 else (x, y - 2.0)
        place(h, (x, y, 0), face_to((x, y), tgt))
        c["floor"].append(h)
    c["robbers"] = []
    for k in range(3):
        h = person(f"Rob{k}", 1.0, 30 + 7 * k, ("male_casualsuit05", "male_casualsuit01", "male_casualsuit03")[k], ("short02", "short04", "short01")[k],
                   cval=1.0)
        c["robbers"].append(h)
    w = person("WigMan", 1.0, 35, "female_elegantsuit01", "long01", cval=1.3, tint=(0.5, 0.42, 0.36), hv=0.5, sat=0.4)
    c["wigman"] = w
    # a loose wig on the carpet (a hair cap shell) for the drop
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.12, location=(0, 0, 0))
    wg = bpy.context.active_object; wg.name = "Wig"; wg.scale = (1.0, 1.15, 0.45)
    wg.data.materials.append(fabric("WigHair", (0.16, 0.09, 0.05), 0.8, 0.9, 900)); c["wig_obj"] = wg
    disp = wg.modifiers.new("hair", 'DISPLACE'); tx = bpy.data.textures.new("WigN", 'CLOUDS'); tx.noise_scale = 0.03; disp.texture = tx; disp.strength = 0.03
    sc = dd.model_h("vintage_suitcase", (-1.0, 5.6, 0), 0.45, rot_z=0.3); c["suitcase"] = sc
    c["trays"] = [box(f"Tray{k}", (0, 0, -40), (0.38, 0.28, 0.025), dd.tex_mat("velour_velvet", 2.0, tint=(0.25, 0.32, 0.7), name="TrayV", sat=0.4))
                  for k in range(4)]
    c["grenade"] = cyl("Grenade", (0, 0, -40), 0.03, 0.08, pbr("GrenadeM", (0.06, 0.07, 0.05), 0.6), verts=12)


def build(variant=None):
    c = {}
    v = variant or "xmas"
    {"xmas": build_xmas, "upstairs": build_upstairs, "after": lambda c: build_upstairs(c, True)}[v](c)
    return c


# ============================================================================ animation
def anim_street(c, sec):
    for h, bag, a, b, sp in c["shoppers"]:
        walk_to(h, a, b, sec, speed=sp)
        bag.location = h.bone_tail("lowerarm02.R") - Vector((0, 0, 0.22)); bag.rotation_euler = (0, 0, h.arm.rotation_euler.z)
    for cr, x0, y, d in c["traffic"]:
        cr.location = (d * (x0 + 9.0 * sec), y, 0); cr.rotation_euler = (0, 0, 0 if d > 0 else math.pi)


def hide_people(c, keep=()):
    for h in [c["guard"]] + c["disguised"]:
        if h not in keep:
            h.arm.location = (0, 0, -60)


def anim_xmas(c, t):
    sec = t * DUR["xmas"]
    anim_street(c, sec)
    hide_people(c)
    c["getaway"].location = (-30, -7.2, 0)
    c["leaf"].rotation_euler = (0, 0, 0)


def anim_door(c, t):
    sec = t * DUR["door"]
    anim_street(c, sec)
    d = c["info"]["door"]
    c["leaf"].rotation_euler = (0, 0, math.radians(-80))
    g = c["guard"]; zero(g); pose_walk(g, 0.0, stride=0.0, arm_swing=0.0)
    gp = d + Vector((-1.3, -0.55, 0.12)); place(g, gp, face_to(gp, gp + Vector((1, -0.4, 0))), z=0.12)
    M = g.arm.matrix_world.to_3x3()
    reach(g, "L", d + Vector((-1.05, -1.0, 1.15)), M @ Vector((1, 0.3, -0.5))); arms_relaxed_one(g, "R")
    for k, h in enumerate(c["disguised"]):
        a = d + Vector((-4.5 - 1.1 * k, -3.0 + 0.3 * k, 0.06)); b = d + Vector((-0.2, 1.5, 0.06))
        walk_to(h, a, b, sec + 1.5 - 0.9 * k, speed=1.0)
        ground(h, 0.06 if h.arm.location.y < -0.9 else 0.12)
    c["getaway"].location = (-30, -7.2, 0)


def anim_getaway(c, t):
    sec = t * DUR["getaway"]
    anim_street(c, sec)
    hide_people(c)
    u = max(0.0, sec - 1.0)
    x = c["info"]["door"].x + 3.0 + 0.5 * 2.2 * u * u if u < 3 else c["info"]["door"].x + 3.0 + 9.9 + 6.6 * (u - 3)
    c["getaway"].location = (x, -7.2 - min(1.0, u * 0.4) * 2.0, 0)


def anim_wig(c, t):
    sec = t * DUR["wig"]
    hide_floor(c, keep_wigman=True)
    w = c["wigman"]
    walk_to(w, Vector((-1.5, 6.4, 0)), Vector((1.8, 8.6, 0)), sec * 0.9 + 1.0, speed=0.8)
    u = min(1.0, sec / 0.7)
    wg = c["wig_obj"]; wg.location = Vector((-1.0, 6.1, 0.05 + 1.5 * (1 - u) ** 2)); wg.rotation_euler = (0.3 * (1 - u), 0.5 * (1 - u), 0.4)


def hide_floor(c, keep_wigman=False):
    for h in c.get("robbers", []):
        h.arm.location = (0, 0, -60)
    if not keep_wigman and "wigman" in c:
        c["wigman"].arm.location = (0, 0, -60)
    for k, tr in enumerate(c.get("trays", [])):
        tr.location = (0, 0, -40)
    if "grenade" in c:
        c["grenade"].location = (0, 0, -40)


def anim_floor16(c, t):
    sec = t * DUR["floor16"]
    hide_floor(c)
    r = c["robbers"][0]; zero(r); pose_walk(r, 0.0, stride=0.0, arm_swing=0.0)
    place(r, (3.9, 7.4, 0), face_to((3.9, 7.4), (-4, 5))); arms_relaxed(r)
    r.rot("head", (0, 0, 1), 20 * math.sin(sec * 0.5))
    c["wig_obj"].location = (-1.0, 6.1, 0.05)


def anim_suitcase(c, t):
    sec = t * DUR["suitcase"]
    hide_floor(c)
    r = c["robbers"][1]
    from dd import pose_crouch
    sp = Vector((-1.0, 5.0, 0)); pose_crouch(r, lean=34); r.arm.rotation_euler = (0, 0, face_to(sp, (-1.0, 5.6))); r.arm.location = sp; ground(r)
    case = Vector((-1.0, 5.6, 0.12))
    for k, tr in enumerate(c["trays"]):
        u = min(1.0, max(0.0, (sec - 1.2 * k) / 1.2))
        src = Vector((-0.4, 4.7, 0.7)); dst = case + Vector((0, 0, 0.03 * k))
        tr.location = src.lerp(dst, ease(u)) if u > 0 else Vector((0, 0, -40)); tr.rotation_euler = (0, 0, 0.3)
        if 0 < u < 1:
            reach(r, "R", tr.location + Vector((0.12, -0.1, 0.03)), Vector((0.5, -0.5, -0.5)))
            reach(r, "L", tr.location + Vector((-0.12, -0.1, 0.03)), Vector((-0.5, -0.5, -0.5)))
    c["wig_obj"].location = (-3.0, 7.5, 0.05)


def anim_panel(c, t):
    sec = t * DUR["panel"]
    hide_floor(c)
    u = ease(min(1.0, max(0.0, (sec - 1.0) / 3.5)))
    c["panel"].location = (-6.7, 6.0 + 1.65 * u, 1.5)


def anim_grenade(c, t):
    sec = t * DUR["grenade"]
    hide_floor(c, keep_wigman=False)
    r = c["robbers"][2]; zero(r); pose_walk(r, 0.0, stride=0.0, arm_swing=0.0)
    rp = Vector((4.2, 8.2, 0)); place(r, rp, face_to(rp, (-4, 4))); arms_relaxed(r)
    up = min(1.0, max(0.0, (sec - 1.0) / 1.0)) * (1.0 - min(1.0, max(0.0, (sec - 4.0) / 1.0)))
    M = r.arm.matrix_world.to_3x3(); sh = r.bone_head("upperarm01.R")
    if up > 0:
        reach(r, "R", sh + M @ Vector((-0.1, -0.35 - 0.15 * up, -0.35 + 0.55 * up)), M @ Vector((-1, 0, -0.5)))
        c["grenade"].location = r.bone_tail("wrist.R") + Vector((0, 0, 0.03))
    if sec > 5.0:
        walk_to(r, rp, Vector((5.4, 9.4, 0)), sec - 5.0, speed=0.8)


def anim_after(c, t):
    pass


# ============================================================================ cameras
def cam_xmas(c, t):
    e = ease(t); d = c["info"]["door"]
    return Vector((d.x - 18.0 + 6.0 * e, -11.5, 2.2)), Vector((d.x - 6.0 + 6.0 * e, 0.0, 3.2)), 30


def cam_door(c, t):
    e = ease(t); d = c["info"]["door"]
    return Vector((d.x - 6.0, -8.6, 1.75)).lerp(Vector((d.x - 5.0, -8.0, 1.72)), e), d + Vector((-0.8, -0.6, 1.4)), 26


def cam_getaway(c, t):
    e = ease(t); d = c["info"]["door"]
    return Vector((d.x - 6.0, -14.5, 1.6)).lerp(Vector((d.x - 4.5, -14.0, 1.55)), e), Vector((d.x + 6.0, -7.0, 0.9)), 30


MOVES = {
    "xmas": dict(kind="anim", dof=None, anim=anim_xmas, cam=cam_xmas, title=("Chapter Two", "The Front Door", 24, 4.5 * 24)),
    "door": dict(kind="anim", dof=5.6, anim=anim_door, cam=cam_door, focus=lambda c, t: c["info"]["door"] + Vector((-1.0, -0.8, 1.4))),
    "getaway": dict(kind="anim", dof=5.6, anim=anim_getaway, cam=cam_getaway, focus=lambda c, t: c["getaway"].location + Vector((0, 0, 0.8))),
    "wig": dict(kind="anim", dof=2.8, anim=anim_wig,
                cam=lambda c, t: (Vector((-1.6, 5.0, 0.35)).lerp(Vector((-1.4, 4.9, 1.3)), ease(t)), Vector((-0.6, 6.4, 0.2)).lerp(Vector((0.6, 7.6, 1.2)), ease(t)), 32),
                focus=lambda c, t: Vector((-1.0, 6.1, 0.1)).lerp(Vector((0.8, 7.8, 1.2)), ease(t))),
    "floor16": dict(kind="anim", dof=5.6, anim=anim_floor16,
                    cam=lambda c, t: (Vector((5.2, 1.0, 2.4)).lerp(Vector((4.8, 1.6, 2.3)), ease(t)), Vector((-3.0, 6.5, 0.5)), 22),
                    focus=lambda c, t: Vector((-4.0, 6.0, 0.6))),
    "suitcase": dict(kind="anim", dof=4.0, anim=anim_suitcase,
                     cam=lambda c, t: (Vector((1.4, 3.4, 1.7)).lerp(Vector((1.1, 3.7, 1.65)), ease(t)), Vector((-1.0, 5.4, 0.4)), 30),
                     focus=lambda c, t: Vector((-1.0, 5.4, 0.4))),
    "panel": dict(kind="anim", dof=4.0, anim=anim_panel,
                  cam=lambda c, t: (Vector((-3.4, 3.6, 1.65)).lerp(Vector((-3.8, 4.0, 1.6)), ease(t)), Vector((-6.9, 6.4, 1.45)), 30),
                  focus=lambda c, t: Vector((-7.0, 6.0, 1.4))),
    "grenade": dict(kind="anim", dof=5.6, anim=anim_grenade,
                    cam=lambda c, t: (Vector((-5.0, 1.0, 1.7)).lerp(Vector((-4.6, 1.3, 1.65)), ease(t)), Vector((4.0, 8.2, 1.3)), 32),
                    focus=lambda c, t: Vector((4.2, 8.2, 1.4))),
    "after": dict(kind="anim", dof=4.0, anim=anim_after,
                  cam=lambda c, t: (Vector((0.5, 0.8, 1.6)).lerp(Vector((0.3, 3.0, 1.5)), ease(t)), Vector((-1.5, 8.0, 0.8)), 26),
                  focus=lambda c, t: Vector((-0.5, 4.8, 0.8))),
}
