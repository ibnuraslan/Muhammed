"""THE BOUTIQUE (hero set): a nameless luxury jeweller on a Paris avenue. A limestone Haussmann building, dark awnings,
a doorman; NO name, logo or sign anywhere. Interiors: the lit salon with display cases, the safe room.
Variants: dawn (avenue, October 2007), lane (side street with the service door), salon (ground-floor salon), safe.
  facade   (intro 3A): dawn crane up the facade while the doorman sweeps the step
  painters (intro 3B): four men in white overalls carry paint tins down the side lane toward the service door, wide
  grille   (ch1 1A, title): dawn track along the avenue as a staff member raises the front grille
  floor    (ch1 2A): wide from the doorway, staff sitting on the salon floor, a painter standing over them
  safe     (ch1 2B): the manager at the alarm panel, its LED turning green, the vault door swinging open
"""
import math
import numpy as np
import bpy
from mathutils import Vector
from kit import *
import ph
import dd
from dd import person, place, face_to, walk_to, arms_relaxed, pose_floor_sit, zero, ground
from human import reach, fingers_curl
from sc_street import car

EXPOSURE = 0.0
BOUNCES = 8
LEAD = 2.5
DUR = {"facade": 4.5, "painters": 4.5, "grille": 5.0, "floor": 4.5, "safe": 5.0}
VARIANT_FOR = {"facade": "dawn", "painters": "lane", "grille": "dawn", "floor": "salon", "safe": "safe"}
WARM = (1.0, 0.78, 0.5)


# ============================================================================ materials
_M = {}


def mats():
    if not _M:
        _M["stone"] = dd.tex_mat("white_sandstone_blocks_02", 0.32, tint=(0.98, 0.93, 0.85), name="Limestone", sat=0.7)
        _M["stone_plain"] = dd.tex_mat("white_sandstone_bricks", 0.6, tint=(0.95, 0.9, 0.83), name="LimestoneP", sat=0.6)
        _M["slate"] = dd.tex_mat("roof_slates_02", 0.5, tint=(0.55, 0.6, 0.66), name="Slate", sat=0.5)
        _M["glass"] = pbr("WinGlass", (0.02, 0.025, 0.03), 0.03, 0.2, **{'Coat Weight': 1.0})
        _M["frame"] = pbr("WinFrame", (0.78, 0.76, 0.72), 0.5)
        _M["iron"] = pbr("Iron", (0.025, 0.027, 0.03), 0.45, 0.7)
        _M["bronze"] = pbr("Bronze", (0.16, 0.11, 0.06), 0.3, 0.9)
        _M["awning"] = fabric("Awning", (0.018, 0.02, 0.026), 0.85, 0.4, 600)
        _M["lit"] = emissive("ShopGlow", WARM, 2.5)
        _M["curtain_lit"] = emissive("RoomGlow", (1.0, 0.82, 0.6), 0.8)
    return _M


# ============================================================================ the Haussmann block
def haussmann(x0, x1, seed=0, boutique=False, depth=14.0, gf=5.0, floors=5, fh=3.25, lit_frac=0.12, rot_z=0.0, origin=(0, 0, 0)):
    """A limestone apartment block with its front face on y=0 (street at -y). Returns the joined object + info."""
    M = mats(); rng = np.random.default_rng(seed)
    w = x1 - x0; cx = (x0 + x1) / 2
    H = gf + floors * fh
    B = dd.Builder("Block%d" % seed)
    B.box((cx, depth / 2, (gf + H) / 2), (w, depth, H - gf), M["stone"])
    B.box((cx, depth / 2 + 0.6, gf / 2), (w, depth - 1.2, gf), pbr("ShopInterior", (0.05, 0.045, 0.04), 0.7))
    nb = max(3, int(round(w / 2.7)))
    bay = w / nb
    lit = []
    for f in range(floors):
        z0 = gf + f * fh
        B.box((cx, -0.06, z0 + 0.05), (w, 0.14, 0.22), M["stone_plain"])
        for b in range(nb):
            x = x0 + bay * (b + 0.5)
            wh = 2.2 if f < 3 else 1.9
            zc = z0 + 0.45 + wh / 2
            B.box((x, 0.04, zc), (1.25, 0.06, wh), M["glass"])
            B.box((x, -0.03, zc + wh / 2 + 0.12), (1.6, 0.1, 0.24), M["stone_plain"])
            for sx in (-1, 1):
                B.box((x + sx * 0.7, -0.02, zc), (0.16, 0.08, wh + 0.1), M["stone_plain"])
            B.box((x, 0.0, zc), (0.05, 0.04, wh), M["frame"])
            B.box((x, 0.0, zc + wh * 0.25), (1.25, 0.04, 0.04), M["frame"])
            if rng.random() < lit_frac:
                B.box((x, 0.12, zc), (1.2, 0.02, wh * 0.95), M["curtain_lit"])
            if f not in (0, 3):           # individual balconettes (continuous balconies on floors 1 and 4)
                B.box((x, -0.18, z0 + 0.95), (1.3, 0.02, 0.05), M["iron"])
                for k in range(9):
                    B.box((x - 0.6 + k * 0.15, -0.18, z0 + 0.7), (0.012, 0.012, 0.5), M["iron"])
        if f in (0, 3):                   # continuous balcony
            B.box((cx, -0.45, z0 + 0.05), (w - 0.2, 0.9, 0.16), M["stone_plain"])
            B.box((cx, -0.86, z0 + 1.08), (w - 0.2, 0.03, 0.05), M["iron"])
            n = int((w - 0.3) / 0.13)
            for k in range(n):
                B.box((x0 + 0.2 + k * 0.13, -0.86, z0 + 0.6), (0.014, 0.014, 0.95), M["iron"])
            for k in range(nb * 3):
                B.box((x0 + bay * (k / 3 + 0.17), -0.4, z0 - 0.15), (0.12, 0.7, 0.28), M["stone_plain"])
    # cornice + mansard roof with dormers
    B.box((cx, -0.25, H + 0.1), (w + 0.1, 0.6, 0.35), M["stone_plain"])
    pitch = math.radians(68); mh = 3.0; run = mh / math.tan(pitch)
    B.box((cx, run / 2 + 0.2, H + 0.25 + mh / 2), (w, mh / math.sin(pitch), 0.12), M["slate"], rot=(pitch - math.pi / 2, 0, 0))
    B.box((cx, depth / 2, H + 0.25 + mh), (w, depth - 2 * run, 0.1), M["slate"])
    for b in range(nb):
        x = x0 + bay * (b + 0.5)
        B.box((x, run / 2 - 0.05, H + 1.5), (1.0, 0.8, 1.6), M["stone_plain"])
        B.box((x, run / 2 - 0.46, H + 1.45), (0.65, 0.02, 1.1), M["glass"])
        B.box((x, run / 2 - 0.05, H + 2.35), (1.15, 0.95, 0.12), M["slate"])
    for k in range(int(w // 6) + 1):
        B.box((x0 + 2 + k * 6, depth / 2 + 1, H + 0.25 + mh + 0.8), (0.8, 2.2, 1.6), M["stone_plain"])
    # ground floor
    info = dict(H=H, gf=gf, x0=x0, x1=x1)
    if boutique:
        opens = shop_front(B, x0, x1, gf, info)
    else:
        gfn = max(2, int(round(w / 4.5))); opens = []
        for b in range(gfn):
            x = x0 + w / gfn * (b + 0.5); ww = w / gfn - 1.0
            B.box((x, 0.06, 2.0), (ww, 0.05, 3.6), M["glass"])
            B.box((x, 0.0, 3.85), (ww, 0.12, 0.12), M["iron"])
            opens.append((x, ww))
    # stone piers between the ground-floor openings, the openings themselves recessed 1.2 m
    edges = [x0] + [e for x, ww in sorted(opens) for e in (x - ww / 2, x + ww / 2)] + [x1]
    for a_, b_ in zip(edges[0::2], edges[1::2]):
        if b_ - a_ > 0.01:
            B.box(((a_ + b_) / 2, 0.6, gf / 2), (b_ - a_, 1.2, gf), M["stone"])
    for x, ww in opens:
        B.box((x, 0.6, 4.4), (ww, 1.2, gf - 4.0 if gf > 4.4 else 0.2), M["stone"])
    B.box((cx, -0.08, gf - 0.1), (w + 0.04, 0.2, 0.3), M["stone_plain"])
    o = B.done(origin, rot_z)
    return o, info


def shop_front(B, x0, x1, gf, info):
    """Three tall display windows with bronze frames and dark awnings, a central door. No name, no logo."""
    M = mats(); cx = (x0 + x1) / 2
    xs = [cx - 6.0, cx, cx + 6.0]
    doors = []
    for i, x in enumerate(xs):
        isdoor = (i == 1)
        ww = 2.4 if isdoor else 3.6
        for sx in (-1, 1):
            B.box((x + sx * (ww / 2 + 0.07), 0.0, 2.0), (0.14, 0.14, 4.0), M["bronze"])
        B.box((x, 0.0, 4.0), (ww + 0.3, 0.14, 0.14), M["bronze"])
        if isdoor:
            B.box((x, 0.03, 1.6), (ww - 0.2, 0.04, 3.2), M["glass"])
            B.box((x, 0.0, 1.6), (0.06, 0.06, 3.2), M["bronze"])
            B.box((x, -0.45, 0.06), (ww + 0.8, 0.9, 0.12), M["stone_plain"])
            doors.append(Vector((x, 0, 0)))
        else:
            B.box((x, 0.03, 2.0), (ww - 0.15, 0.04, 3.8), M["glass"])
            # the lit display behind the glass: a warm backdrop and three small plinths
            B.box((x, 0.9, 2.0), (ww - 0.2, 0.05, 3.6), pbr("ShowBackM", (0.35, 0.3, 0.24), 0.6))
            for k in range(3):
                B.box((x - 1.0 + k * 1.0, 0.5, 0.75 + 0.15 * (k % 2)), (0.4, 0.4, 1.5 + 0.3 * (k % 2)), pbr("PlinthM", (0.06, 0.05, 0.045), 0.4))
        # awning: a dark slanted fabric canopy over each opening
        B.box((x, -0.75, 4.3), (ww + 0.6, 1.6, 0.04), M["awning"], rot=(math.radians(-24), 0, 0))
        B.box((x, -1.48, 3.98), (ww + 0.6, 0.02, 0.28), M["awning"])
    # a blank bronze plaque by the door (no text) and two carriage lamps
    B.box((cx + 1.6, -0.03, 1.7), (0.4, 0.03, 0.55), M["bronze"])
    info["door"] = doors[0]; info["shows"] = [Vector((x, 0, 0)) for x in (xs[0], xs[2])]
    return [(x, (2.4 if i == 1 else 3.6) + 0.3) for i, x in enumerate(xs)]


def show_lights(info):
    for p in info["shows"]:
        for k in range(3):
            l = bpy.data.lights.new("ShowL", 'SPOT'); l.energy = 60; l.color = WARM; l.spot_size = math.radians(50); l.shadow_soft_size = 0.2
            o = bpy.data.objects.new("ShowL", l); bpy.context.collection.objects.link(o)
            o.location = p + Vector((-1.0 + k * 1.0, 0.3, 3.6)); point_at(o, p + Vector((-1.0 + k * 1.0, 0.5, 1.4)))
        a = bpy.data.lights.new("ShowFill", 'AREA'); a.energy = 120; a.size = 3.0; a.color = WARM
        ao = bpy.data.objects.new("ShowFill", a); bpy.context.collection.objects.link(ao); ao.location = p + Vector((0, 0.6, 3.8))
        ao.visible_camera = False


def street(c, y_kerb=-6.0, length=140, opposite=True):
    road = dd.wet(dd.tex_mat("asphalt_02", 0.35, tint=(0.5, 0.5, 0.52), name="Road", sat=0.4), 0.35, 0.25, ripples=False)
    box("Road", (0, y_kerb - 8, -0.06), (length, 16, 0.1), road)
    pave = dd.tex_mat("concrete_floor_02", 0.5, tint=(0.62, 0.61, 0.59), name="Pavement", sat=0.3)
    box("Pavement", (0, y_kerb / 2, 0.0), (length, -y_kerb, 0.12), pave)
    box("Kerb", (0, y_kerb, 0.0), (length, 0.25, 0.13), pbr("Granite", (0.32, 0.32, 0.33), 0.5))
    if opposite:
        for k, (a, b) in enumerate(((-60, -30), (-30, -8), (-8, 14), (14, 40), (40, 66))):
            haussmann(a, b, seed=20 + k, rot_z=math.pi, origin=(0, y_kerb - 16 - 6, 0), lit_frac=0.1)
            # rotated by pi about the origin: x flips, so the row still spans the street
        box("PaveOpp", (0, y_kerb - 19, 0.0), (length, 6, 0.12), pave)
    # lamp posts and a few parked cars along the kerb
    for k in range(-5, 6):
        x = k * 11.0 + 3.0
        cyl("LampPost", (x, y_kerb + 0.6, 2.4), 0.07, 4.8, mats()["iron"], verts=12)
        box("LampHead", (x, y_kerb + 0.6, 5.0), (0.35, 0.35, 0.5), pbr("LampGlass", (0.8, 0.78, 0.7), 0.3))
    cars = []
    for k, (x, col) in enumerate(((-14, (0.05, 0.05, 0.06)), (-8.5, (0.4, 0.41, 0.43)), (9, (0.12, 0.14, 0.18)), (15, (0.6, 0.6, 0.6)))):
        cr = car(f"Parked{k}", col); cr.location = (x, y_kerb - 1.2, 0); cars.append(cr)
    c["cars"] = cars


def doorman(c, loc):
    h = person("Doorman", 1.0, 52, "male_elegantsuit01", "short04", cval=0.12, hv=0.6, sat=0.3)
    broom = dd.model_h("wooden_broom", (0, 0, 0), 1.35) or cyl("Broom", (0, 0, 0.65), 0.012, 1.3, pbr("BroomW", (0.3, 0.2, 0.1), 0.6))
    c["doorman"] = h; c["broom"] = broom; c["doorman_at"] = Vector(loc)


def anim_doorman(c, sec):
    h = c["doorman"]; base = c["doorman_at"]
    zero(h); from human import pose_walk
    pose_walk(h, 0.0, stride=0.0, arm_swing=0.0)
    h.rot("spine03", (1, 0, 0), 12); h.rot("head", (1, 0, 0), 16)
    face = math.radians(-60)
    h.arm.rotation_euler = (0, 0, face); h.arm.location = base; ground(h, 0.12)
    M = h.arm.matrix_world.to_3x3()
    sw = 0.28 * math.sin(sec * 2.2)
    foot = base + M @ Vector((sw, -0.75, 0)) + Vector((0, 0, 0.12))
    top = base + M @ Vector((0.05 + 0.1 * sw, -0.22, 1.1))
    b = c["broom"]; b.location = foot
    d = (top - foot).normalized(); b.rotation_euler = d.to_track_quat('Z', 'Y').to_euler()
    reach(h, "L", top, M @ Vector((1, 0, -0.5)))
    reach(h, "R", foot.lerp(top, 0.55), M @ Vector((-1, -0.3, -0.5)))
    fingers_curl(h, 60, thumb=30)


def painter(name, years, seed):
    h = person(name, 1.0, years, "male_worksuit01", ("short02", "short01", "short03", "short04")[seed % 4], cval=1.05, sat=0.0,
               hv=0.2 + 0.15 * (seed % 2), height=0.45 + 0.05 * (seed % 3), weight=0.5)
    return h


def paint_tin(name):
    tin = pbr("TinWhite", (0.85, 0.85, 0.83), 0.35, 0.3)
    parts = [cyl(name, (0, 0, 0.13), 0.13, 0.26, tin, verts=24),
             cyl(name + "Rim", (0, 0, 0.265), 0.132, 0.012, pbr("TinRim", (0.6, 0.6, 0.62), 0.3, 1.0), verts=24)]
    return join(parts, name)


# ============================================================================ variants
def build_dawn(c):
    world_sky(sun_elev_deg=3, sun_rot_deg=95, strength=0.35, tint=(0.88, 0.92, 1.0))
    sun(3, 95, energy=1.4, color=(1.0, 0.72, 0.5), angle_deg=1.5)
    blk, info = haussmann(-11, 11, seed=1, boutique=True, lit_frac=0.08)
    haussmann(-34, -11, seed=2, lit_frac=0.12); haussmann(11, 33, seed=3, lit_frac=0.1)
    haussmann(33, 55, seed=4, lit_frac=0.1); haussmann(-56, -34, seed=5, lit_frac=0.1)
    show_lights(info); c["info"] = info
    street(c)
    doorman(c, info["door"] + Vector((1.1, -0.9, 0)))
    # the front grille over the door: an iron lattice that rolls up
    gr = [box("GrilleBar", (0, 0, 1.6), (2.5, 0.03, 0.03), mats()["iron"])]
    for k in range(18):
        gr.append(box("GrilleV", (-1.2 + k * 0.14, 0, 1.6), (0.015, 0.02, 3.2), mats()["iron"]))
    for k in range(12):
        gr.append(box("GrilleH", (0, 0, 0.1 + k * 0.28), (2.5, 0.02, 0.02), mats()["iron"]))
    c["grille"] = join(gr, "Grille"); c["grille"].location = info["door"] + Vector((0, -0.1, 0))
    st = person("Staff", 0.0, 34, "female_elegantsuit01", "bob01", cval=0.15, hv=0.25)
    c["staff"] = st
    haze = dd.frame_value  # (unused placeholder to keep imports explicit)


def build_lane(c):
    world_sky(sun_elev_deg=4, sun_rot_deg=95, strength=0.3, tint=(0.88, 0.92, 1.0))
    sun(4, 95, energy=0.9, color=(1.0, 0.75, 0.55), angle_deg=1.5)
    # a narrow rue running along +Y: the boutique block's side on the right (x>0), another block on the left
    haussmann(-30, 30, seed=7, rot_z=math.radians(-90), origin=(4.0, 0, 0), lit_frac=0.06, gf=5.0)
    haussmann(-30, 30, seed=8, rot_z=math.radians(90), origin=(-4.0, 0, 0), lit_frac=0.06, gf=5.0)
    road = dd.wet(dd.tex_mat("cobblestone_floor_04", 0.6, tint=(0.55, 0.55, 0.56), name="Cobbles", sat=0.4), 0.4, 0.4, ripples=False)
    box("Lane", (0, 0, -0.05), (8, 70, 0.1), road)
    for sx in (-1, 1):
        box("LanePave", (sx * 3.3, 0, 0.02), (1.4, 70, 0.14), dd.tex_mat("concrete_floor_02", 0.5, tint=(0.6, 0.6, 0.58), name="LP", sat=0.3))
    # the service door on the right wall: plain dark steel, a small caged lamp above
    door = box("ServiceDoor", (3.97, 9.0, 1.15), (0.06, 1.1, 2.3), pbr("SteelDoor", (0.08, 0.085, 0.09), 0.45, 0.6))
    box("ServiceFrame", (3.98, 9.0, 1.2), (0.05, 1.3, 2.45), pbr("DoorFrameM", (0.3, 0.3, 0.3), 0.5, 0.5))
    lamp = bpy.data.lights.new("DoorLamp", 'POINT'); lamp.energy = 25; lamp.color = WARM; lamp.shadow_soft_size = 0.05
    lo = bpy.data.objects.new("DoorLamp", lamp); bpy.context.collection.objects.link(lo); lo.location = (3.7, 9.0, 2.8)
    box("DoorLampBox", (3.85, 9.0, 2.8), (0.15, 0.15, 0.2), emissive("DoorLampGlow", WARM, 6))
    c["door_at"] = Vector((3.4, 9.0, 0))
    v = car("Van", (0.8, 0.8, 0.79), length=5.0, width=2.0); v.location = (-2.2, 2.0, 0); v.rotation_euler = (0, 0, math.pi / 2)
    c["painters"] = []
    for k in range(4):
        h = painter(f"Painter{k}", 30 + 6 * k, k)
        tin = paint_tin(f"Tin{k}")
        c["painters"].append((h, tin, Vector((0.3 + 0.55 * (k % 2) - 0.2 * (k // 2), -3.5 - 1.3 * k, 0)), 0.25 * k))


def salon_room(c, w=14.0, d=10.0, hgt=4.6, carpet=False):
    M = mats()
    floor = dd.tex_mat("marble_01", 0.35, tint=(0.92, 0.9, 0.86), name="Marble", sat=0.6)
    floor.node_tree.nodes["Principled BSDF"].inputs['Coat Weight'].default_value = 0.6
    box("Floor", (0, d / 2, -0.05), (w, d, 0.1), floor)
    if carpet:
        box("Rug", (0, d / 2 + 0.5, 0.004), (6.5, 4.5, 0.008), fabric("Rug", (0.32, 0.27, 0.22), 0.95, 0.4, 400))
    panel = pbr("Boiserie", (0.72, 0.68, 0.6), 0.55)
    mould = pbr("Moulding", (0.8, 0.77, 0.7), 0.5)
    box("WallBack", (0, d + 0.1, hgt / 2), (w, 0.2, hgt), panel)
    box("WallL", (-w / 2 - 0.1, d / 2, hgt / 2), (0.2, d, hgt), panel)
    box("WallR", (w / 2 + 0.1, d / 2, hgt / 2), (0.2, d, hgt), panel)
    box("Ceiling", (0, d / 2, hgt + 0.1), (w, d, 0.2), pbr("Ceil", (0.85, 0.83, 0.8), 0.8))
    # moulded panels on the side and back walls
    for (ax, pos, rng_) in (("x", d - 0.01, np.arange(-w / 2 + 1.2, w / 2 - 1.0, 2.2)),):
        for x in rng_:
            for z0, hz in ((0.45, 0.6), (1.4, 2.3)):
                for (dx, dz, sx, sz) in ((0, 0, 1.8, 0.04), (0, hz, 1.8, 0.04), (-0.9, hz / 2, 0.04, hz), (0.9, hz / 2, 0.04, hz)):
                    box("Mould", (x + dx + 0.9, pos, z0 + dz), (sx, 0.03, sz), mould)
    for sx in (-1, 1):
        for y in np.arange(1.2, d - 1.0, 2.2):
            for z0, hz in ((0.45, 0.6), (1.4, 2.3)):
                for (dy, dz, sy, sz) in ((0, 0, 1.8, 0.04), (0, hz, 1.8, 0.04), (-0.9, hz / 2, 0.04, hz), (0.9, hz / 2, 0.04, hz)):
                    box("Mould", (sx * (w / 2 - 0.01), y + dy + 0.9, z0 + dz), (0.03, sy, sz), mould)
    box("Cornice", (0, d - 0.05, hgt - 0.12), (w, 0.15, 0.24), mould)
    # front wall with the tall windows onto the avenue (daylight from outside)
    for x in (-5.0, 0.0, 5.0):
        box("FrontGlass", (x, -0.02, 2.0), (3.4, 0.03, 3.8), glass("FrontGlass", (0.92, 0.95, 0.96), 0.03))
    for x in (-7.0, -2.5, 2.5, 7.0):
        box("FrontPier", (x, 0.0, hgt / 2), (1.4 if abs(x) < 7 else 0.6, 0.3, hgt), panel)
    box("FrontHead", (0, 0.0, 4.3), (w, 0.3, 0.6), panel)
    pt = bpy.data.lights.new("Portal", 'AREA'); pt.shape = 'RECTANGLE'; pt.size = w; pt.size_y = 4.0; pt.cycles.is_portal = True
    po = bpy.data.objects.new("Portal", pt); bpy.context.collection.objects.link(po); po.location = (0, -0.1, 2.0); po.rotation_euler = (math.radians(-90), 0, 0)
    # chandeliers + warm ceiling wash
    for x in (-3.5, 3.5):
        dd.model_h("Chandelier_01", (x, d / 2, hgt - 1.0), 0.95)
        l = bpy.data.lights.new("Chand", 'POINT'); l.energy = 140; l.color = WARM; l.shadow_soft_size = 0.4
        o = bpy.data.objects.new("Chand", l); bpy.context.collection.objects.link(o); o.location = (x, d / 2, hgt - 0.6)
    return panel


def vitrine(name, loc, size=(1.4, 0.6), rot_z=0.0, rng=None, lit=True):
    """A display case: dark wood base, glass top, a warm light strip inside and jewels on small stands."""
    rng = rng or np.random.default_rng(3)
    M = mats(); W, D = size
    wood_ = wood(name + "Wood", (0.05, 0.03, 0.02), (0.12, 0.07, 0.04), scale=(0.3, 6, 6), rough=0.3, coat=0.5)
    parts = [box(name + "Base", (0, 0, 0.45), (W, D, 0.9), wood_, bevel=0.01),
             box(name + "Bed", (0, 0, 0.91), (W - 0.06, D - 0.06, 0.02), fabric(name + "Velvet", (0.05, 0.06, 0.08), 0.9, 0.7, 300))]
    case = join(parts, name)
    gl = box(name + "Glass", (0, 0, 1.13), (W, D, 0.42), glass(name + "G", (0.95, 0.97, 0.98), 0.0))
    gl.parent = case
    if lit:
        st = box(name + "Strip", (0, D / 2 - 0.04, 1.32), (W - 0.1, 0.02, 0.01), emissive(name + "StripE", WARM, 25)); st.parent = case
        l = bpy.data.lights.new(name + "L", 'AREA'); l.size = W * 0.8; l.energy = 12; l.color = WARM
        lo = bpy.data.objects.new(name + "L", l); bpy.context.collection.objects.link(lo); lo.parent = case; lo.location = (0, 0, 1.3)
    jew = []
    for k in range(int(W / 0.25)):
        x = -W / 2 + 0.15 + k * 0.25
        stand_m = pbr(name + "Stand", (0.82, 0.8, 0.76), 0.5)
        s = cyl(name + "Stand", (x, 0.0, 0.94), 0.025, 0.05, stand_m, verts=16); s.parent = case
        r = dd.ring(f"{name}R{k}", (x, 0.0, 0.98), stone_r=rng.uniform(0.003, 0.006), band="plat" if k % 2 else "gold",
                    stone=("diamond", "ruby", "diamond", "sapphire", "emerald")[k % 5])
        r.parent = case; jew.append(r)
    case.location = loc; case.rotation_euler = (0, 0, rot_z)
    return case, jew


def build_salon(c):
    world_sky(sun_elev_deg=4, sun_rot_deg=95, strength=0.5, tint=(0.85, 0.9, 1.0))
    sun(4, 95, energy=1.0, color=(1.0, 0.75, 0.55), angle_deg=1.5)
    salon_room(c)
    rng = np.random.default_rng(9)
    c["cases"] = []
    for k, (x, y) in enumerate(((-3.5, 3.2), (0.0, 3.6), (3.5, 3.2), (-3.5, 6.4), (3.5, 6.4))):
        cs, _ = vitrine(f"Vit{k}", (x, y, 0), rng=rng); c["cases"].append(cs)
    for x in (-5.8, 5.8):
        dd.model_h("ArmChair_01", (x, 8.5, 0), 0.95, rot_z=math.pi if x < 0 else math.pi)
    # outside the windows: the avenue at dawn (a facade across the street)
    haussmann(-30, 30, seed=30, rot_z=math.pi, origin=(0, -14, 0), lit_frac=0.12)
    box("StreetOut", (0, -7, -0.06), (80, 14, 0.1), pbr("AsphaltOut", (0.08, 0.08, 0.085), 0.6))
    # staff sitting on the floor against the left wall; one painter standing over them
    c["seated"] = []
    spots = [(-6.0, 4.4), (-5.95, 5.3), (-6.05, 6.2), (-5.9, 7.1)]
    who = [("Staff0", 0.0, 32, "female_elegantsuit01", "bob02"), ("Staff1", 1.0, 45, "male_elegantsuit01", "short02"),
           ("Staff2", 0.0, 51, "female_elegantsuit01", "ponytail01"), ("Staff3", 1.0, 29, "male_elegantsuit01", "short04")]
    for (x, y), (nm, g, yr, cl, hr) in zip(spots, who):
        h = person(nm, g, yr, cl, hr, cval=0.12, hv=0.3)
        pose_floor_sit(h, hunch=16)
        place(h, (x, y, 0), face_to((x, y), (0.0, y)))
        c["seated"].append(h)
    p = painter("PainterG", 38, 1); c["guard_painter"] = p
    c["pistol"] = dd.model_h("service_pistol", (0, 0, 0), 0.13)


def build_safe(c):
    world_flat((0.02, 0.02, 0.025), 1.0)
    steel = pbr("SafeSteel", (0.45, 0.46, 0.47), 0.32, 0.9)
    wall = pbr("SafeWall", (0.55, 0.55, 0.53), 0.7)
    box("Floor", (0, 2, -0.05), (6, 6, 0.1), dd.tex_mat("concrete_floor_painted", 0.6, tint=(0.6, 0.6, 0.6), name="SafeFloor", sat=0.4))
    box("Back", (0, 4.6, 1.5), (6, 0.2, 3.0), wall); box("L", (-3.0, 2, 1.5), (0.2, 6, 3.0), wall); box("R", (3.0, 2, 1.5), (0.2, 6, 3.0), wall)
    box("Ceil", (0, 2, 3.0), (6, 6, 0.1), wall)
    # safe deposit wall on the left
    br = brushed_metal("Deposit", (0.6, 0.6, 0.6))
    for i in range(10):
        for j in range(7):
            box("Box", (-2.88, 1.0 + i * 0.32, 0.4 + j * 0.3), (0.05, 0.3, 0.28), br, bevel=0.004)
            cyl("Lock", (-2.85, 1.0 + i * 0.32, 0.45 + j * 0.3), 0.012, 0.02, mats()["bronze"], verts=10, rot=(0, math.radians(90), 0))
    # the vault door in the back wall: a thick round door hinged on its left edge
    box("VaultFrame", (0.8, 4.48, 1.15), (2.2, 0.1, 2.2), steel)
    box("VaultDark", (0.8, 4.52, 1.15), (1.6, 0.05, 1.6), pbr("VaultIn", (0.05, 0.05, 0.05), 0.6))
    vd = [cyl("Door", (0.85, 0, 0), 0.82, 0.3, steel, verts=64, rot=(math.radians(90), 0, 0))]
    for k in range(6):
        a = k * math.pi / 3
        vd.append(cyl("Spoke", (0.85 + 0.18 * math.cos(a), -0.2, 0.18 * math.sin(a)), 0.02, 0.36, mats()["bronze"], verts=8,
                      rot=(0, math.pi / 2 - a, 0)))
    vd.append(cyl("Hub", (0.85, -0.2, 0), 0.07, 0.08, mats()["bronze"], verts=24, rot=(math.radians(90), 0, 0)))
    door = join(vd, "VaultDoor"); door.location = (0.8 - 0.85, 4.25, 1.15); c["vault"] = door
    # alarm keypad with a status LED (red, then green: frame driver)
    box("Keypad", (2.88, 2.6, 1.45), (0.04, 0.22, 0.3), pbr("KeypadM", (0.85, 0.85, 0.82), 0.4))
    for i in range(3):
        for j in range(4):
            box("Key", (2.855, 2.53 + i * 0.07, 1.36 + j * 0.055), (0.01, 0.05, 0.04), pbr("KeyM", (0.3, 0.3, 0.32), 0.4))
    led = bpy.data.materials.new("LED"); led.use_nodes = True
    N = led.node_tree.nodes; L = led.node_tree.links; N.clear()
    out = N.new("ShaderNodeOutputMaterial"); em = N.new("ShaderNodeEmission"); em.inputs['Strength'].default_value = 30
    g = dd.frame_value(N, "1 if frame > 46 else 0", "Green")
    mx = N.new("ShaderNodeMix"); mx.data_type = 'RGBA'; mx.inputs[6].default_value = (1, 0.05, 0.02, 1); mx.inputs[7].default_value = (0.1, 1, 0.2, 1)
    L.new(g.outputs[0], mx.inputs['Factor']); L.new(mx.outputs[2], em.inputs['Color']); L.new(em.outputs[0], out.inputs['Surface'])
    box("LED", (2.85, 2.6, 1.58), (0.01, 0.03, 0.02), led)
    for x in (-1.2, 1.2):
        box("Tube", (x, 2.0, 2.94), (0.12, 2.4, 0.04), emissive("Tube", (0.9, 0.95, 1.0), 6))
        a = bpy.data.lights.new("TubeL", 'AREA'); a.shape = 'RECTANGLE'; a.size = 0.2; a.size_y = 2.4; a.energy = 150; a.color = (0.9, 0.95, 1.0)
        o = bpy.data.objects.new("TubeL", a); bpy.context.collection.objects.link(o); o.location = (x, 2.0, 2.9)
    mg = person("Manager", 0.0, 46, "female_elegantsuit01", "bob01", cval=0.1, hv=0.25); c["manager"] = mg
    pt = painter("PainterS", 34, 2); c["safe_painter"] = pt


def build(variant=None):
    c = {"variant": variant}
    v = variant or "dawn"
    {"dawn": build_dawn, "lane": build_lane, "salon": build_salon, "safe": build_safe}[v](c)
    return c


# ============================================================================ animation + cameras
def anim_facade(c, t):
    anim_doorman(c, t * DUR["facade"])
    c["staff"].arm.location = (0, 0, -50)
    c["grille"].location.z = 3.2


def cam_facade(c, t):
    e = ease(t)
    d = c["info"]["door"]
    loc = Vector((d.x - 9.0, -17.0, 1.7)).lerp(Vector((d.x - 7.0, -16.0, 6.5)), e)
    tgt = Vector((d.x, 0, 3.0)).lerp(Vector((d.x, 0, 11.0)), e)
    return loc, tgt, 26


def anim_grille(c, t):
    sec = t * DUR["grille"]
    anim_doorman(c, sec + 3.0)
    d = c["info"]["door"]
    u = ease(min(1.0, max(0.0, (sec - 0.8) / 3.4)))
    c["grille"].location = d + Vector((0, -0.1, 3.0 * u))
    st = c["staff"]; zero(st); from human import pose_walk
    pose_walk(st, 0.0, stride=0.0, arm_swing=0.0)
    place(st, d + Vector((-0.6, -0.65, 0.12)), face_to(d + Vector((-0.6, -0.65, 0)), d + Vector((-0.6, 0, 0))), z=0.12)
    M = st.arm.matrix_world.to_3x3()
    hz = 1.15 + 0.5 * u
    reach(st, "R", d + Vector((-0.45, -0.25, hz)), M @ Vector((-1, 0.3, -0.5)))
    arms_relaxed_one(st, "L")


def arms_relaxed_one(h, sd):
    M = h.arm.matrix_world.to_3x3(); fwd = (M @ Vector((0, -1, 0))).normalized(); left = (M @ Vector((1, 0, 0))).normalized()
    sg = 1 if sd == "L" else -1
    up = (Vector((0, 0, -1)) + left * (0.12 * sg)).normalized(); lo = (up + fwd * 0.25).normalized()
    h.aim(f"upperarm01.{sd}", up); h.aim(f"upperarm02.{sd}", up); h.aim(f"lowerarm01.{sd}", lo); h.aim(f"lowerarm02.{sd}", lo)


def cam_grille(c, t):
    e = ease(t)
    d = c["info"]["door"]
    loc = Vector((d.x - 11.0, -10.5, 1.9)).lerp(Vector((d.x - 6.5, -9.0, 1.85)), e)
    return loc, d + Vector((0.0, 0, 2.0)), 32


def anim_painters(c, t):
    sec = t * DUR["painters"]
    for h, tin, start, delay in c["painters"]:
        end = c["door_at"] + Vector((-0.6 - 0.25 * (start.x), -0.5 + 0.1 * start.y, 0))
        walk_to(h, start, start + Vector((0.4, 12.0, 0)), max(0.0, sec - delay) + 0.5, speed=1.15)
        tip = h.bone_tail("wrist.R") if "wrist.R" in h.arm.pose.bones else h.bone_tail("lowerarm02.R")
        tin.location = tip - Vector((0, 0, 0.3))


def cam_painters(c, t):
    e = ease(t)
    loc = Vector((-1.5, -9.5, 2.4)).lerp(Vector((-1.2, -7.8, 2.2)), e)
    return loc, Vector((1.2, 9.0, 1.4)), 30


def anim_floor(c, t):
    sec = t * DUR["floor"]
    p = c["guard_painter"]
    x = -4.4 + 0.5 * math.sin(sec * 0.6)
    walk_to(p, Vector((-4.2, 3.8, 0)), Vector((-4.6, 7.6, 0)), sec, speed=0.55, cadence=1.2)
    pp = c["pistol"]
    if pp is not None:
        tip = p.bone_tail("wrist.R") if "wrist.R" in p.arm.pose.bones else p.bone_tail("lowerarm02.R")
        pp.location = tip + Vector((0, 0, -0.1)); pp.rotation_euler = (math.radians(90), 0, p.arm.rotation_euler.z)
    for k, h in enumerate(c["seated"]):
        h.rot("head", (0, 0, 1), 0)


def cam_floor(c, t):
    e = ease(t)
    loc = Vector((2.5, 9.2, 1.7)).lerp(Vector((1.6, 9.0, 1.65)), e)
    return loc, Vector((-5.0, 5.2, 0.7)), 26


def anim_safe(c, t):
    sec = t * DUR["safe"]
    mg = c["manager"]; zero(mg); from human import pose_walk
    pose_walk(mg, 0.0, stride=0.0, arm_swing=0.0)
    place(mg, (2.35, 2.55, 0), math.radians(-90))
    M = mg.arm.matrix_world.to_3x3()
    press = 0.015 * max(0.0, math.sin(sec * 7.0)) if sec < 1.9 else 0.0
    reach(mg, "L", Vector((2.8 - press, 2.62, 1.42)), M @ Vector((0.6, 0.2, -0.8)))
    arms_relaxed_one(mg, "R")
    mg.rot("head", (0, 1, 0), -6)
    p = c["safe_painter"]; place(p, (0.6, 1.0, 0), face_to((0.6, 1.0), (2.3, 2.6))); arms_relaxed(p)
    u = ease(min(1.0, max(0.0, (sec - 2.2) / 2.6)))
    c["vault"].rotation_euler = (0, 0, math.radians(-95 * u))


def cam_safe(c, t):
    e = ease(t)
    loc = Vector((-2.2, -0.6, 1.75)).lerp(Vector((-1.8, -0.2, 1.7)), e)
    return loc, Vector((1.4, 3.6, 1.2)), 24


MOVES = {
    "facade": dict(kind="anim", dof=8.0, cam=cam_facade, anim=anim_facade, focus=lambda c, t: c["info"]["door"]),
    "grille": dict(kind="anim", dof=5.6, cam=cam_grille, anim=anim_grille, focus=lambda c, t: c["info"]["door"] + Vector((0, -0.6, 1.5)),
                   title=("Chapter One", "The Service Door", 24, 4.0 * 24)),
    "painters": dict(kind="anim", dof=8.0, cam=cam_painters, anim=anim_painters, focus=lambda c, t: Vector((0.5, 2.0, 1.2))),
    "floor": dict(kind="anim", dof=5.6, cam=cam_floor, anim=anim_floor, focus=lambda c, t: Vector((-5.2, 5.6, 0.8))),
    "safe": dict(kind="anim", dof=5.6, cam=cam_safe, anim=anim_safe, focus=lambda c, t: Vector((2.3, 2.6, 1.4))),
}
for _k in ("grille",):
    MOVES[_k]["dof"] = None        # DOF off on the title shot
