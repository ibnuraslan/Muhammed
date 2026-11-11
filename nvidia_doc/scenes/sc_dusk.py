"""SET 3 / STREET AT DUSK (dramatization). A wide city street, blue dusk, shopfronts lit warm, streetlights coming on.
A: long lens from across the road: a bus passes in the near lane and reveals Alice walking toward us in slow motion.
B: tracking alongside her on the far sidewalk; pedestrians and cars cross the foreground; she glances once to the side.

Timing from the voiceover: A 14.60-17.85 (3.25 s) "The woman at the center of the allegation is Alice Huang."
                           B 17.85-20.50 (2.65 s) "She comes from the other side of Nvidia's business."
Everything runs at ~45% speed (slow motion): cars, pedestrians and her walk cycle together.
"""
import math
import numpy as np
import bpy
from mathutils import Vector
from kit import *
from human import Human, add_asset, pose_walk, reset_pose, fingers_curl, _world_verts
from people import woman
from sc_home import facade, haze_mix
import ph

EXPOSURE = -0.4
DUR = {"reveal": 3.25, "track": 2.65}
SLOW = 0.45
ROAD_Y = (-7.0, 7.0)          # kerb to kerb, the road runs along X
FAR_WALK_Y = 9.2              # where she walks (far sidewalk), toward -X
FACADE_Y = 12.0
HAZE = (0.33, 0.4, 0.55)
rng = np.random.default_rng(7)


# ============================================================================ vehicles
def car(name, col, length=4.5, width=1.85, height=1.45, kind="sedan"):
    body = pbr(name + "Paint", col, 0.22, 0.6, **{'Coat Weight': 1.0, 'Coat Roughness': 0.05})
    glass_m = pbr("CarGlass", (0.02, 0.025, 0.03), 0.05, 0.0, **{'Coat Weight': 1.0})
    tyre = pbr("Tyre", (0.02, 0.02, 0.02), 0.8)
    rim = pbr("Rim", (0.5, 0.5, 0.52), 0.3, 1.0)
    head = emissive("Headlamp", (1.0, 0.92, 0.8), 40); tail = emissive("Taillamp", (1.0, 0.04, 0.02), 18)
    L_, W_, H_ = length, width, height
    parts = [box("Body", (0, 0, 0.55), (L_, W_, 0.62), body, bevel=0.12)]
    if kind == "bus":
        parts = [box("Body", (0, 0, 1.75), (L_, W_, 2.9), body, bevel=0.08),
                 box("WinBand", (0, 0, 2.2), (L_ - 0.6, W_ + 0.01, 1.1), glass_m, bevel=0.02),
                 box("Windscreen", (L_ / 2 - 0.02, 0, 1.9), (0.04, W_ - 0.25, 1.6), glass_m),
                 box("RouteSign", (L_ / 2 - 0.01, 0, 3.0), (0.03, W_ - 0.5, 0.25), emissive("Route", (1.0, 0.6, 0.15), 6)),
                 box("Livery", (0, 0, 1.15), (L_ - 0.2, W_ + 0.012, 0.28), pbr("Livery", (0.12, 0.35, 0.22), 0.3, 0.3)),
                 box("Skirt", (0, 0, 0.42), (L_ - 0.4, W_ + 0.01, 0.12), pbr("Skirt", (0.08, 0.08, 0.09), 0.6))]
        for k in range(5):
            parts.append(box("DoorSeam", (-L_ / 2 + 1.5 + k * 2.3, 0, 1.6), (0.02, W_ + 0.014, 2.4), pbr("Seam", (0.1, 0.1, 0.11), 0.5)))
    else:
        parts.append(box("Cabin", (-0.15, 0, 1.08), (L_ * 0.52, W_ - 0.16, 0.5), glass_m, bevel=0.14))
    for sx in (-1, 1):
        for sy in (-1, 1):
            wx = sx * (L_ / 2 - (0.75 if kind != "bus" else 1.6))
            parts.append(cyl("Tyre", (wx, sy * (W_ / 2 - 0.12), 0.33 if kind != "bus" else 0.5), 0.33 if kind != "bus" else 0.5, 0.24, tyre, verts=24, rot=(math.radians(90), 0, 0)))
            parts.append(cyl("Rim", (wx, sy * (W_ / 2 - 0.0), 0.33 if kind != "bus" else 0.5), 0.2, 0.02, rim, verts=16, rot=(math.radians(90), 0, 0)))
    hz = 0.65 if kind != "bus" else 0.6
    for sy in (-1, 1):
        parts.append(box("Head", (L_ / 2 + 0.01, sy * (W_ / 2 - 0.3), hz), (0.04, 0.35, 0.1), head))
        parts.append(box("Tail", (-L_ / 2 - 0.01, sy * (W_ / 2 - 0.25), hz + 0.05), (0.04, 0.3, 0.1), tail))
    o = join(parts, name)
    return o


# ============================================================================ the street
def shopfront_sign(text, loc, mat_bg, mat_txt, width):
    box("SignBoard", loc, (width, 0.08, 0.5), mat_bg, bevel=0.01)
    text_obj("SignText", text, (loc[0], loc[1] - 0.05, loc[2] - 0.12), 0.26, mat_txt,
             rot=(math.radians(90), 0, 0), font_path="/usr/share/fonts/opentype/inter/Inter-SemiBold.otf", spacing=1.1)


def build_street(c):
    asphalt = pbr("Asphalt", (0.035, 0.036, 0.04), 0.55)
    N = asphalt.node_tree.nodes; L = asphalt.node_tree.links; tc = N.new("ShaderNodeTexCoord")
    nz = N.new("ShaderNodeTexNoise"); nz.inputs['Scale'].default_value = 90; nz.inputs['Detail'].default_value = 8; L.new(tc.outputs['Object'], nz.inputs['Vector'])
    rr = N.new("ShaderNodeMapRange"); rr.inputs['To Min'].default_value = 0.35; rr.inputs['To Max'].default_value = 0.65; L.new(nz.outputs['Fac'], rr.inputs['Value'])
    L.new(rr.outputs[0], N["Principled BSDF"].inputs['Roughness'])
    box("Road", (0, 0, -0.05), (400, ROAD_Y[1] - ROAD_Y[0], 0.1), asphalt)
    paint = pbr("LinePaint", (0.75, 0.75, 0.72), 0.6)
    for k in range(-60, 60):
        box("Dash", (k * 6.0, 0, 0.002), (3.0, 0.15, 0.005), paint)
        box("Dash2", (k * 6.0, -3.5, 0.002), (3.0, 0.12, 0.005), paint); box("Dash3", (k * 6.0, 3.5, 0.002), (3.0, 0.12, 0.005), paint)
    pave = pbr("Paving", (0.3, 0.29, 0.27), 0.75)
    N = pave.node_tree.nodes; L = pave.node_tree.links; tc = N.new("ShaderNodeTexCoord")
    br = N.new("ShaderNodeTexBrick"); br.inputs['Scale'].default_value = 1.6; br.inputs['Mortar Size'].default_value = 0.01
    br.inputs['Color1'].default_value = (0.32, 0.31, 0.29, 1); br.inputs['Color2'].default_value = (0.27, 0.26, 0.25, 1); br.inputs['Mortar'].default_value = (0.18, 0.18, 0.17, 1)
    L.new(tc.outputs['Object'], br.inputs['Vector']); L.new(br.outputs['Color'], N["Principled BSDF"].inputs['Base Color'])
    kerb = pbr("Kerb", (0.45, 0.44, 0.42), 0.7)
    for y0, y1 in ((ROAD_Y[1], FACADE_Y), (-FACADE_Y, ROAD_Y[0])):
        box("Sidewalk", (0, (y0 + y1) / 2, 0.08), (400, y1 - y0, 0.16), pave)
        box("Kerb", (0, y0 if y0 > 0 else y1, 0.08), (400, 0.25, 0.17), kerb)
    # far side: a continuous row of 5-9 storey buildings, shopfronts at street level
    shop_glow = [emissive(f"ShopGlow{k}", col, 0.32) for k, col in enumerate(((1.0, 0.72, 0.45), (1.0, 0.8, 0.6), (0.95, 0.76, 0.55)))]
    shelf_m = pbr("ShopShelf", (0.06, 0.05, 0.04), 0.7)
    sign_bg = [pbr("SignDark", (0.03, 0.03, 0.035), 0.5), pbr("SignLight", (0.8, 0.79, 0.75), 0.5)]
    sign_txt = [emissive("SignTxtW", (1.0, 0.97, 0.9), 5), emissive("SignTxtA", (1.0, 0.75, 0.4), 5)]
    names = ["PHARMACY", "BOOKS", "NOODLE HOUSE", "BAKERY", "OPTICAL", "CAFE", "TAILOR", "MARKET", "FLORIST", "KOPI", "HARDWARE", "DIM SUM"]
    upper = [facade("Up1", (0.06, 0.07, 0.08), (0.5, 0.48, 0.45), floor=3.6, bay=1.8, lit_frac=0.25, refl=0.2),
             facade("Up2", (0.05, 0.06, 0.07), (0.62, 0.6, 0.56), floor=3.4, bay=1.5, lit_frac=0.3, refl=0.15),
             facade("Up3", (0.04, 0.05, 0.06), (0.3, 0.31, 0.32), floor=3.8, bay=2.0, lit_frac=0.2, refl=0.3)]
    x = -120.0; k = 0
    while x < 120:
        w = rng.uniform(9, 18); floors = rng.integers(5, 10)
        hgt = 4.5 + floors * 3.6
        box("Bldg", (x + w / 2, FACADE_Y + 6, 4.5 + (hgt - 4.5) / 2), (w - 0.1, 12, hgt - 4.5), upper[k % 3])
        box("ShopGlass", (x + w / 2, FACADE_Y + 0.05, 2.0), (w - 0.8, 0.05, 3.2), glass("ShopWin", (0.85, 0.88, 0.9), 0.02))
        box("ShopInside", (x + w / 2, FACADE_Y + 2.5, 2.0), (w - 0.8, 0.05, 3.2), shop_glow[k % 3])
        for j in range(int(w // 2.2)):          # shelves / counters inside, seen as silhouettes against the glow
            box("Shelf", (x + 1.0 + j * 2.2 + rng.uniform(-0.3, 0.3), FACADE_Y + rng.uniform(1.0, 2.2), rng.uniform(0.6, 1.0)),
                (rng.uniform(0.8, 1.6), 0.4, rng.uniform(1.2, 2.0)), shelf_m)
        l = bpy.data.lights.new("ShopLight", 'AREA'); l.energy = 60; l.size = max(1.0, w - 2); l.color = (1.0, 0.78, 0.55)
        lo = bpy.data.objects.new("ShopLight", l); bpy.context.collection.objects.link(lo); lo.location = (x + w / 2, FACADE_Y + 1.2, 3.4)
        box("Pier", (x + 0.2, FACADE_Y, 2.25), (0.4, 0.6, 4.5), pbr("PierStone", (0.38, 0.36, 0.33), 0.7))
        shopfront_sign(names[k % len(names)], (x + w / 2, FACADE_Y - 0.06, 4.0), sign_bg[k % 2], sign_txt[k % 2], min(w - 1.5, 6.5))
        box("Canopy", (x + w / 2, FACADE_Y - 0.9, 3.45), (w - 0.3, 1.8, 0.08), pbr("Canopy", (0.12, 0.12, 0.13), 0.5, 0.6))
        x += w; k += 1
    # street trees and streetlights along the far kerb
    crown_m = pbr("RainTree", (0.03, 0.05, 0.03), 0.85)
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=1.0, location=(0, 0, 0)); crown = bpy.context.active_object
    tx = bpy.data.textures.new("Crown", 'CLOUDS'); tx.noise_scale = 0.45
    dm = crown.modifiers.new("d", 'DISPLACE'); dm.texture = tx; dm.strength = 0.3; bpy.ops.object.modifier_apply(modifier=dm.name)
    crown.data.materials.append(crown_m); crown.location = (0, 0, -100)
    bark = pbr("Bark", (0.06, 0.05, 0.04), 0.9)
    lamps = []
    pole_m = pbr("Pole", (0.2, 0.21, 0.22), 0.5, 0.7)
    for k in range(-14, 15):
        tx_ = k * 9.0 + rng.uniform(-1.5, 1.5)
        cyl("Trunk", (tx_, ROAD_Y[1] + 1.4, 2.2), 0.16, 4.4, bark, verts=12)
        instance(crown, (tx_, ROAD_Y[1] + 1.4, 5.6), scale=(3.4, 3.0, 1.8))
        lx = k * 18.0 + 4.5
        cyl("LampPole", (lx, ROAD_Y[1] + 0.6, 4.0), 0.07, 8.0, pole_m, verts=12)
        box("LampArm", (lx, ROAD_Y[1] - 0.4, 7.9), (0.08, 2.0, 0.08), pole_m)
        head = box("LampHead", (lx, ROAD_Y[1] - 1.3, 7.85), (0.5, 0.25, 0.08), pbr("LampHeadM", (0.2, 0.2, 0.2), 0.5))
        l = bpy.data.lights.new("StreetLamp", 'SPOT'); l.energy = 0.0; l.spot_size = math.radians(110); l.spot_blend = 0.6; l.color = (1.0, 0.75, 0.45)
        lo = bpy.data.objects.new("StreetLamp", l); bpy.context.collection.objects.link(lo); lo.location = (lx, ROAD_Y[1] - 1.3, 7.75)
        lamps.append(l)
    c["lamps"] = lamps
    # near side: a low wall and planters (only seen out of focus in the foreground)
    box("NearWall", (0, -FACADE_Y, 1.5), (400, 0.3, 3.0), pbr("NearWall", (0.25, 0.25, 0.26), 0.8))


def build_traffic(c):
    cols = [(0.6, 0.62, 0.64), (0.04, 0.04, 0.045), (0.75, 0.75, 0.74), (0.35, 0.06, 0.05), (0.12, 0.18, 0.28), (0.45, 0.45, 0.47)]
    veh = []
    lanes = [(-5.25, 1), (-1.75, 1), (1.75, -1), (5.25, -1)]       # (y, direction along X)
    for k in range(14):
        y, d = lanes[k % 4]
        o = car(f"Car{k}", cols[k % len(cols)])
        o.rotation_euler = (0, 0, 0 if d > 0 else math.pi)
        veh.append(dict(o=o, y=y, d=d, x0=rng.uniform(-90, 90), v=rng.uniform(9, 13)))
    bus = car("Bus", (0.85, 0.85, 0.82), length=12.0, width=2.5, height=3.2, kind="bus")
    bus.rotation_euler = (0, 0, 0)
    veh.append(dict(o=bus, y=-5.25, d=1, x0=-3.0, v=9.0, bus=True))      # covers her at frame 1, clears by ~1 s
    c["traffic"] = veh


def build_people(c):
    alice = woman("Alice"); c["alice"] = alice
    peds = []
    specs = [(1.0, 40, "male_casualsuit01", "short02", 10.0, 1), (0.0, 28, "female_casualsuit02", "ponytail01", 10.6, -1),
             (1.0, 55, "male_casualsuit04", "short04", 11.2, -1), (0.0, 45, "female_sportsuit01", "bob01", 8.6, 1),
             (1.0, 33, "male_casualsuit06", "short03", 11.0, 1)]
    for k, (g, yrs, cl, hr, y, d) in enumerate(specs):
        h = Human(f"Ped{k}", gender=g, years=yrs, muscle=0.5, weight=0.45, height=0.5, eyelashes=None)
        add_asset(h, "clothes", cl, val=0.35, rough=0.7); add_asset(h, "clothes", "shoes02", val=0.25)
        add_asset(h, "hair", hr, val=0.3)
        peds.append(dict(h=h, y=y, d=d, x0=rng.uniform(-12, 14), v=rng.uniform(1.1, 1.4), ph=rng.uniform(0, 1)))
    c["peds"] = peds


def arms_down(h, phase, swing):
    """Replace MakeHuman's A-pose arms: hang them at the sides, swinging opposite to the legs."""
    M = h.arm.matrix_world.to_3x3(); fwd = (M @ Vector((0, -1, 0))).normalized(); left = (M @ Vector((1, 0, 0))).normalized()
    for sd, sg in (("L", 1), ("R", -1)):
        a = math.radians(swing) * math.sin(2 * math.pi * phase + (math.pi if sd == "L" else 0.0))
        up = (Vector((0, 0, -1)) * math.cos(a) + fwd * math.sin(a) + left * (0.12 * sg)).normalized()
        lo = (up + fwd * (0.25 + 0.15 * max(0.0, math.sin(a)))).normalized()
        h.aim(f"upperarm01.{sd}", up); h.aim(f"upperarm02.{sd}", up)
        h.aim(f"lowerarm01.{sd}", lo); h.aim(f"lowerarm02.{sd}", lo)
        h.aim(f"wrist.{sd}", lo + left * (0.1 * sg))


def place_walker(h, x, y, d, phase, stride=26, swing=16):
    bob = pose_walk(h, phase % 1.0, stride=stride, arm_swing=swing)
    h.arm.rotation_euler = (0, 0, math.radians(90) if d > 0 else math.radians(-90))     # rest faces -Y -> along +/-X
    h.arm.location = (x, y, 0.16 + bob)
    bpy.context.view_layer.update()
    arms_down(h, phase % 1.0, swing)


def build(variant=None):
    c = {}
    world_sky(sun_elev_deg=-1.5, sun_rot_deg=200, strength=1.6, tint=(0.62, 0.72, 1.0), air=1.5, aerosol=2.0)
    build_street(c); build_traffic(c); build_people(c)
    # soft blue skylight fill from above the street (dusk), very low
    f = area_light((0, 0, 30), (0, 0, 0), 60, 900, (0.55, 0.65, 1.0)); f.visible_camera = False
    animate(c, 0.0)
    # Alice's feet on the pavement (her rig's lowest vertex at the pavement top)
    return c


def animate(c, sec):
    """sec = time since the start of Set 3 (on-screen seconds; the world runs at SLOW)."""
    w = sec * SLOW                                  # world time
    for v in c["traffic"]:
        x = v["x0"] + v["d"] * v["v"] * w
        if not v.get("bus"):
            x = ((x + 100) % 200) - 100
        v["o"].location = (x, v["y"], 0.0)
    a = c["alice"]
    ax = 6.0 - 1.15 * w                              # she walks toward -X along the far sidewalk
    place_walker(a, ax, FAR_WALK_Y, -1, (1.15 * w) / 1.35 + 0.1, stride=24, swing=14)
    if sec > DUR["reveal"] + 1.6:                    # B: one glance to her side (toward the road)
        g = math.sin(math.pi * min(1.0, (sec - DUR["reveal"] - 1.6) / 0.9))
        a.rot("neck01", (0, 0, 1), 10 * g); a.rot("head", (0, 0, 1), 14 * g)
    for p in c["peds"]:
        x = p["x0"] + p["d"] * p["v"] * w
        place_walker(p["h"], x, p["y"], p["d"], p["ph"] + p["v"] * w / 1.35)
    on = ease(min(1.0, max(0.0, (sec - 0.8) / 4.0)))  # streetlights warming up through the set
    for l in c["lamps"]:
        l.energy = 900 * on
    c["alice_pos"] = Vector((ax, FAR_WALK_Y, 1.0))
    bpy.context.view_layer.update()


def anim_reveal(c, t):
    animate(c, t * DUR["reveal"])


def anim_track(c, t):
    animate(c, DUR["reveal"] + t * DUR["track"])


def cam_reveal(c, t):
    e = ease(t)
    loc = Vector((-9.0, -10.5, 1.55)).lerp(Vector((-10.5, -10.3, 1.6)), e)    # across the road, long lens, slow drift
    return (loc, c["alice_pos"] + Vector((0, 0, 0.45)), 85)


def cam_track(c, t):
    p = c["alice_pos"]
    loc = Vector((p.x - 1.5, ROAD_Y[1] - 1.2, 1.45))                           # on the road edge, moving with her
    return (loc, p + Vector((0.6, 0, 0.5)), 50)


MOVES = {
    "reveal": dict(kind="anim", dof=2.0, far=80.0, cam=cam_reveal, focus=lambda c, t: c["alice_pos"], anim=anim_reveal),
    "track": dict(kind="anim", dof=1.8, far=40.0, cam=cam_track, focus=lambda c, t: c["alice_pos"], anim=anim_track),
}
