"""CH5 redo (data hall, Ch1 quality and richer): a contained cold aisle in a modern AI data hall at night.
Two rows of 42U racks (detailed 2U server fronts with perforated bezels, drive caddies, handles, top-of-rack switches
with port LEDs, PDUs), blinking status LEDs (frame drivers, independent per LED), a wake wave that switches racks on
down the aisle, yellow fibre trunking and black ladder trays with cable bundles dropping into the racks, a glass-roofed
cold-aisle containment with sliding doors, perforated raised-floor tiles, cool overhead light strips and a thin
cold-aisle haze. A second pod is visible beyond the glass for depth.

  wake        CH5 6C  (233 f) slow push down the aisle while the racks wake one after another
  half_empty  CH5 7A  (252 f) wide from the aisle end: the near half live, the far half empty frames (no servers)
  ripple      CH5 7C  (236 f) low, close, trucking along one rack row: LEDs, bezels, then craning up to the trays
"""
import math
import numpy as np
import bpy
from mathutils import Vector
from kit import *
from common import area_light, world_flat
from sc_dchall import led_material, frame_driver

EXPOSURE = 0.0
VARIANT_FOR = {"wake": "wake", "half_empty": "half", "ripple": "live"}
FRAMES = {"wake": 233, "half_empty": 252, "ripple": 236}
AISLE = 1.8                      # cold aisle width (between rack fronts)
RW, RD, RH = 0.6, 1.2, 2.2       # rack width (along y), depth, height
N_RACKS = 16
FX = AISLE / 2                   # rack front plane |x|
Y0 = 0.0                         # first rack centre y


def build(variant=None):
    c = {}
    world_flat((0.004, 0.005, 0.007), 1.0)
    # -------- room: raised floor (light grey tiles, darker grout), dark walls and ceiling
    tile = pbr("FloorTile", (0.42, 0.43, 0.44), 0.35, 0.0)
    N = tile.node_tree.nodes; L = tile.node_tree.links; tc = N.new("ShaderNodeTexCoord")
    br = N.new("ShaderNodeTexBrick"); br.offset = 0.0; br.inputs['Scale'].default_value = 1.0
    br.inputs['Brick Width'].default_value = 0.6; br.inputs['Row Height'].default_value = 0.6; br.inputs['Mortar Size'].default_value = 0.006
    br.inputs['Color1'].default_value = (0.40, 0.41, 0.42, 1); br.inputs['Color2'].default_value = (0.36, 0.37, 0.38, 1)
    br.inputs['Mortar'].default_value = (0.05, 0.05, 0.055, 1)
    L.new(tc.outputs['Object'], br.inputs['Vector']); L.new(br.outputs['Color'], N["Principled BSDF"].inputs['Base Color'])
    box("Floor", (0, 12, -0.02), (30, 60, 0.04), tile)
    perf = perforated("PerfTile", (0.32, 0.33, 0.34), pitch=0.02, hole=0.45, metal=0.6, rough=0.4)
    for k in range(int(N_RACKS * RW / 0.6) + 2):                       # perforated tiles down the cold aisle
        box("PerfTile", (0, Y0 - 0.3 + k * 0.6, 0.002), (0.58, 0.58, 0.004), perf)
    box("Under", (0, 12, -0.3), (30, 60, 0.02), emissive("Plenum", (0.25, 0.35, 0.5), 0.15))
    dark = pbr("Wall", (0.05, 0.055, 0.06), 0.8)
    box("Ceiling", (0, 12, 4.6), (30, 60, 0.1), pbr("Ceil", (0.025, 0.027, 0.03), 0.9))
    box("WallFar", (0, 40, 2.3), (30, 0.2, 4.6), dark); box("WallBack", (0, -8, 2.3), (30, 0.2, 4.6), dark)
    box("WallL", (-9, 12, 2.3), (0.2, 60, 4.6), dark); box("WallR", (9, 12, 2.3), (0.2, 60, 4.6), dark)

    # -------- one rack prototype (front faces +X at x = RD/2), server units as one mesh
    frame_m = pbr("RackFrame", (0.018, 0.019, 0.021), 0.4, 0.6)
    bezel_m = perforated("Bezel", (0.07, 0.075, 0.08), pitch=0.0045, hole=0.55, metal=0.7, rough=0.35)
    caddy_m = pbr("Caddy", (0.11, 0.115, 0.12), 0.35, 0.8)
    handle_m = pbr("Handle", (0.55, 0.56, 0.58), 0.25, 1.0)
    label_m = pbr("Label", (0.75, 0.75, 0.72), 0.6)
    sw_m = pbr("Switch", (0.03, 0.032, 0.035), 0.5, 0.4)
    port_m = pbr("Port", (0.005, 0.005, 0.006), 0.6)
    fx = RD / 2
    shell = [box("RackSideL", (0, -RW / 2 + 0.01, RH / 2), (RD, 0.02, RH), frame_m),
             box("RackSideR", (0, RW / 2 - 0.01, RH / 2), (RD, 0.02, RH), frame_m),
             box("RackTop", (0, 0, RH - 0.01), (RD, RW, 0.02), frame_m),
             box("RackBase", (0, 0, 0.05), (RD, RW, 0.1), frame_m),
             box("RailL", (fx - 0.03, -0.24, RH / 2), (0.03, 0.025, RH - 0.2), handle_m),
             box("RailR", (fx - 0.03, 0.24, RH / 2), (0.03, 0.025, RH - 0.2), handle_m),
             box("Back", (-fx + 0.01, 0, RH / 2), (0.02, RW - 0.04, RH - 0.1), frame_m)]
    rack_empty = join(shell, "RackEmpty")
    parts = []
    z = 0.16; units = []
    while z < RH - 0.32:
        u = 0.0889                                              # 2U server
        parts.append(box("Srv", (fx - 0.04, 0, z + u / 2), (0.06, 0.445, u - 0.004), bezel_m))
        for j in range(6):                                      # drive caddies on the left half
            parts.append(box("Caddy", (fx - 0.005, -0.2 + j * 0.034, z + u / 2), (0.012, 0.03, u - 0.016), caddy_m))
        parts.append(box("HandleL", (fx + 0.012, -0.215, z + u / 2), (0.016, 0.01, 0.05), handle_m))
        parts.append(box("HandleR", (fx + 0.012, 0.215, z + u / 2), (0.016, 0.01, 0.05), handle_m))
        parts.append(box("Lbl", (fx + 0.001, 0.12, z + u * 0.72), (0.002, 0.06, 0.012), label_m))
        units.append(z + u / 2)
        z += u
    for k in range(2):                                          # two top-of-rack switches with port rows
        zz = RH - 0.27 + k * 0.05
        parts.append(box("ToR", (fx - 0.04, 0, zz), (0.06, 0.445, 0.042), sw_m))
        for j in range(24):
            parts.append(box("PortHole", (fx - 0.008, -0.19 + j * 0.0165, zz), (0.006, 0.012, 0.012), port_m))
    servers = join(parts, "RackServers")
    led_g = led_material("LedGreen", (0.25, 1.0, 0.45), wave=variant == "wake")
    led_b = led_material("LedBlue", (0.25, 0.65, 1.0), wave=variant == "wake")
    led_a = led_material("LedAmber", (1.0, 0.55, 0.12), wave=variant == "wake")
    leds = []
    for zc in units:                                            # per server: two status LEDs + a link LED
        leds.append(box("L", (fx + 0.012, 0.155, zc + 0.012), (0.004, 0.006, 0.006), led_g))
        leds.append(box("L", (fx + 0.012, 0.172, zc + 0.012), (0.004, 0.006, 0.006), led_b))
        leds.append(box("L", (fx + 0.012, 0.19, zc - 0.012), (0.004, 0.004, 0.004), led_a if (int(zc * 100) % 3 == 0) else led_g))
    for k in range(2):
        zz = RH - 0.27 + k * 0.05
        for j in range(24):
            leds.append(box("L", (fx + 0.0, -0.19 + j * 0.0165, zz + 0.011), (0.003, 0.004, 0.003), led_g))
    # LED objects stay separate per rack row position: one joined cluster per rack (object random / wave per rack)
    led_proto = join(leds, "RackLeds")
    for m in (led_g, led_b, led_a):
        pass

    def place_rack(loc, rz, live, wave_frame):
        r = instance(rack_empty, loc, (0, 0, rz))
        if live:
            instance(servers, loc, (0, 0, rz))
            o = instance(led_proto, loc, (0, 0, rz)); o["wave"] = float(wave_frame)
        return r

    # -------- the pod: two rows facing the cold aisle (row A at -x faces +x, row B at +x faces -x) + a far pod
    for pod_y in (0.0, 16 * RW + 4.0):
        for side, rz in ((-1, 0.0), (1, math.pi)):
            x = side * (FX + RD / 2)
            for k in range(N_RACKS):
                y = pod_y + Y0 + k * RW
                live = True
                if variant == "half" and pod_y == 0.0 and k >= N_RACKS // 2:
                    live = False
                wave = 10 + k * 9 + (4 if side > 0 else 0)
                place_rack((x, y, 0), rz, live, wave if pod_y == 0.0 else 0)
    rack_empty.hide_render = servers.hide_render = led_proto.hide_render = True
    rack_empty.location = servers.location = led_proto.location = (0, 0, -50)
    if variant == "half":                                     # unpacked boxes waiting by the empty racks
        card = pbr("Carton", (0.55, 0.42, 0.26), 0.85)
        for k, (x, y) in enumerate(((0.35, 6.4), (-0.4, 7.2), (0.2, 8.1), (0.45, 8.9))):
            box("Carton", (x, y, 0.22), (0.62, 0.48, 0.44), card, bevel=0.01, rot=(0, 0, 0.1 * k))
    # -------- containment: glass roof over the aisle, sliding doors at the near end, end panels
    glass_r = glass("ContGlass", (0.85, 0.92, 0.95), 0.08)
    cont_len = N_RACKS * RW
    box("ContRoof", (0, Y0 - RW / 2 + cont_len / 2, RH + 0.12), (AISLE + 0.2, cont_len, 0.01), glass_r)
    alu = pbr("ContFrame", (0.5, 0.52, 0.55), 0.3, 0.9)
    for k in range(N_RACKS + 1):
        box("RoofBar", (0, Y0 - RW / 2 + k * RW, RH + 0.13), (AISLE + 0.2, 0.03, 0.04), alu)
    for sx in (-1, 1):                                       # far end sliding doors (glass with frame)
        box("DoorGlass", (sx * AISLE / 4, Y0 - RW / 2 + cont_len + 0.02, RH / 2), (AISLE / 2 - 0.04, 0.01, RH), glass_r)
        box("DoorFrame", (sx * AISLE / 4, Y0 - RW / 2 + cont_len + 0.02, RH - 0.03), (AISLE / 2, 0.04, 0.06), alu)
    box("DoorSign", (0, Y0 - RW / 2 + cont_len + 0.04, RH + 0.05), (0.5, 0.01, 0.1), emissive("DoorSign", (0.4, 0.9, 1.0), 2.0))
    # -------- overhead: yellow fibre trunking + black ladder trays with cable bundles and drops into racks
    yellow = pbr("FibreDuct", (0.85, 0.62, 0.05), 0.45)
    black = pbr("Tray", (0.02, 0.02, 0.022), 0.5, 0.6)
    cable_m = pbr("Cable", (0.03, 0.035, 0.05), 0.55)
    cable_b = pbr("CableBlue", (0.05, 0.12, 0.35), 0.5)
    for side in (-1, 1):
        x = side * (FX + RD / 2)
        L_ = 2 * (N_RACKS * RW + 4.0) + 4
        box("Fibre", (x - side * 0.2, 12, RH + 0.55), (0.3, L_, 0.1), yellow, bevel=0.01)
        box("FibreIn", (x - side * 0.2, 12, RH + 0.6), (0.24, L_, 0.03), pbr("FibreIn", (0.4, 0.3, 0.03), 0.6))
        for rail in (-0.25, 0.25):
            box("TrayRail", (x + side * 0.15 + rail, 12, RH + 0.95), (0.03, L_, 0.06), black)
        rung = box("Rung", (0, 0, -40), (0.5, 0.025, 0.02), black)
        for k in range(int(L_ / 0.3)):
            instance(rung, (x + side * 0.15, -8 + k * 0.3, RH + 0.92))
        for j in range(5):                                    # cable bundle in the ladder tray
            cyl("Bundle", (x + side * 0.15 - 0.16 + j * 0.08, 12, RH + 0.97), 0.03, L_, cable_b if j % 2 else cable_m, verts=10, rot=(math.radians(90), 0, 0))
        for k in range(0, N_RACKS, 2):                        # drops from the trunk into every other rack top
            cyl("Drop", (x - side * 0.2, Y0 + k * RW, RH + 0.27), 0.04, 0.5, yellow, verts=12)
        box("Hanger", (x, 12, RH + 1.6), (0.02, 0.02, 1.4), black)
    # -------- light: cool LED strips over the aisle (visible), soft fill, thin cold-aisle haze
    strip = emissive("Strip", (0.82, 0.9, 1.0), 6.0)
    for k in range(6):
        y = Y0 + 0.5 + k * 1.7
        box("Strip", (0, y, 3.4), (0.08, 1.2, 0.03), strip)
        area_light((0, y, 3.35), (0, 0, 0), 1.2, 70, (0.82, 0.9, 1.0)).visible_camera = False
    for k in range(4):                                        # dimmer strips over the far pod and the hot aisles
        for x in (-3.6, 3.6):
            l = area_light((x, Y0 + k * 3.5, 3.6), (0, 0, 0), 1.0, 25, (0.7, 0.8, 1.0)); l.visible_camera = False
        area_light((0, 16 * RW + 5 + k * 3, 3.4), (0, 0, 0), 1.0, 45, (0.82, 0.9, 1.0)).visible_camera = False
    haze((0, Y0 + cont_len / 2, 1.15), (AISLE, cont_len + 2, 2.3), density=0.012, color=(0.75, 0.85, 1.0), anis=0.35)
    haze((0, 20, 2.3), (16, 50, 4.6), density=0.004, color=(0.7, 0.8, 1.0), anis=0.3)
    c["aisle_end"] = Vector((0, Y0 + cont_len, 1.2))
    return c


def _push(c, t):
    e = ease(t)
    return (Vector((0.15, -2.6, 1.5)).lerp(Vector((-0.05, 2.6, 1.42)), e), Vector((0.0, 14.0, 1.15)), 26)


def _half(c, t):
    e = ease(t)
    return (Vector((-0.55, -1.9, 2.05)).lerp(Vector((0.35, -1.4, 1.95)), e), Vector((0.1, 9.5, 0.8)), 24)


def _ripple(c, t):
    e = ease(t)
    y = 1.4 + 3.2 * e
    z = 0.75 + 1.15 * e * e                                   # truck along the faces, then crane up toward the trays
    return (Vector((0.25, y - 1.1, z)), Vector((-FX - 0.02, y + 0.9, 0.95 + 1.55 * e * e)), 32)


MOVES = {
    "wake": dict(kind="anim", far=60.0, cam=_push),
    "half_empty": dict(kind="anim", far=60.0, cam=_half),
    "ripple": dict(kind="anim", dof=2.4, far=20.0, cam=_ripple,
                   focus=lambda c, t: Vector((-FX, 1.4 + 3.2 * ease(t) + 0.1, 0.95 + 1.55 * ease(t) ** 2))),
}
