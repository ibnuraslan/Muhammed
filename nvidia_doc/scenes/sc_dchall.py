"""CH1 SET 2/3/4: a clean modern AI data hall (Iceman look: cool, bright, readable). Two long rows of racks with
perforated doors, server units with handles and small status LEDs, overhead cable trays, white tiled floor.
Animation that plays in any render of the baked file (frame drivers, no scripts):
  - LEDs blink at per-unit random rates
  - an 'activity wave' lights the racks one after another down the aisle (shot B)
Shots:  tray  (A) slow slide along an open server tray: eight accelerator boards with finned heatsinks
        aisle (B) pull back down the aisle as the racks light up in a wave
"""
import math
import numpy as np
import bpy
from mathutils import Vector
from kit import *

EXPOSURE = -0.2
VARIANT_FOR = {"tray": "on", "install": "on", "wake": "one", "ripple": "one", "half_empty": "half"}
DUR = {"tray": 5.0, "aisle": 6.0, "install": 5.0, "wake": 4.0, "ripple": 4.0}   # estimates until the chapter 1 voiceover arrives
ROWS_X = (-1.5, 1.5)                    # rack fronts face the centre aisle (x = 0)
N_RACKS = 14
RACK_W, RACK_D, RACK_H = 0.62, 1.1, 2.15


def frame_driver(socket, expr):
    d = socket.driver_add("default_value").driver; d.type = 'SCRIPTED'; d.expression = expr
    return d


def led_material(name, col, wave=False):
    """Emissive LED: blinks by (frame, object random); with wave=True also gated by the rack's wave delay."""
    m = bpy.data.materials.new(name); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; N.clear()
    out = N.new("ShaderNodeOutputMaterial"); em = N.new("ShaderNodeEmission"); em.inputs['Color'].default_value = (*col, 1)
    t = N.new("ShaderNodeValue"); t.name = "Frame"; frame_driver(t.outputs[0], "frame")
    oi = N.new("ShaderNodeObjectInfo")
    rate = N.new("ShaderNodeMapRange"); rate.inputs['To Min'].default_value = 0.15; rate.inputs['To Max'].default_value = 0.9
    L.new(oi.outputs['Random'], rate.inputs['Value'])
    ph = N.new("ShaderNodeMath"); ph.operation = 'MULTIPLY_ADD'; L.new(t.outputs[0], ph.inputs[0]); L.new(rate.outputs[0], ph.inputs[1])
    r100 = N.new("ShaderNodeMath"); r100.operation = 'MULTIPLY'; r100.inputs[1].default_value = 37.0; L.new(oi.outputs['Random'], r100.inputs[0])
    L.new(r100.outputs[0], ph.inputs[2])
    sn = N.new("ShaderNodeMath"); sn.operation = 'SINE'; L.new(ph.outputs[0], sn.inputs[0])
    on = N.new("ShaderNodeMath"); on.operation = 'GREATER_THAN'; on.inputs[1].default_value = -0.2; L.new(sn.outputs[0], on.inputs[0])
    st = N.new("ShaderNodeMath"); st.operation = 'MULTIPLY'; st.inputs[1].default_value = 14.0; L.new(on.outputs[0], st.inputs[0])
    if wave:   # rack activity: 0 until frame passes this rack's 'wave' attribute, then ramps up over 8 frames
        at = N.new("ShaderNodeAttribute"); at.attribute_type = 'OBJECT'; at.attribute_name = "wave"
        sub = N.new("ShaderNodeMath"); sub.operation = 'SUBTRACT'; L.new(t.outputs[0], sub.inputs[0]); L.new(at.outputs['Fac'], sub.inputs[1])
        rp = N.new("ShaderNodeMapRange"); rp.inputs['From Min'].default_value = 0.0; rp.inputs['From Max'].default_value = 8.0
        L.new(sub.outputs[0], rp.inputs['Value'])
        base = N.new("ShaderNodeMath"); base.operation = 'MULTIPLY_ADD'; base.inputs[1].default_value = 0.85; base.inputs[2].default_value = 0.15
        L.new(rp.outputs[0], base.inputs[0])
        g = N.new("ShaderNodeMath"); g.operation = 'MULTIPLY'; L.new(st.outputs[0], g.inputs[0]); L.new(base.outputs[0], g.inputs[1])
        st = g
    L.new(st.outputs[0], em.inputs['Strength']); L.new(em.outputs[0], out.inputs['Surface'])
    return m


def perforated(name, col):
    m = pbr(name, col, 0.45, 0.7)
    N = m.node_tree.nodes; L = m.node_tree.links; tc = N.new("ShaderNodeTexCoord")
    mp = N.new("ShaderNodeMapping"); mp.inputs['Scale'].default_value = (180, 180, 180); L.new(tc.outputs['Object'], mp.inputs['Vector'])
    vo = N.new("ShaderNodeTexVoronoi"); vo.feature = 'F1'; vo.inputs['Randomness'].default_value = 0.0; L.new(mp.outputs[0], vo.inputs['Vector'])
    hole = N.new("ShaderNodeMath"); hole.operation = 'LESS_THAN'; hole.inputs[1].default_value = 0.32; L.new(vo.outputs['Distance'], hole.inputs[0])
    dark = N.new("ShaderNodeMix"); dark.data_type = 'RGBA'; L.new(hole.outputs[0], dark.inputs['Factor'])
    dark.inputs[6].default_value = (*col, 1); dark.inputs[7].default_value = (0.005, 0.005, 0.006, 1)
    L.new(dark.outputs[2], N["Principled BSDF"].inputs['Base Color'])
    return m


def server_unit(name, frame_m, face_m, handle_m, led_a, led_b):
    """A 2U server front: face plate, two handles, a row of drive bays, two status LEDs."""
    parts = [box("Face", (0, 0, 0), (0.48, 0.02, 0.085), face_m, bevel=0.002)]
    for sx in (-0.225, 0.225):
        parts.append(box("Handle", (sx, -0.02, 0), (0.012, 0.018, 0.07), handle_m, bevel=0.003))
    for k in range(8):
        parts.append(box("Bay", (-0.17 + k * 0.043, -0.011, 0.0), (0.038, 0.004, 0.06), frame_m))
    o = join(parts, name)
    leds = [box("LedA", (0.19, -0.012, 0.028), (0.012, 0.004, 0.008), led_a), box("LedB", (0.205, -0.012, 0.028), (0.012, 0.004, 0.008), led_b)]
    return o, leds


def build(variant=None):
    c = {}
    world_flat((0.02, 0.025, 0.03), 1.0)
    rng = np.random.default_rng(5)
    floor = pbr("FloorTile", (0.62, 0.63, 0.64), 0.35)
    N = floor.node_tree.nodes; L = floor.node_tree.links; tc = N.new("ShaderNodeTexCoord")
    br = N.new("ShaderNodeTexBrick"); br.inputs['Scale'].default_value = 1.667; br.offset = 0.0; br.inputs['Mortar Size'].default_value = 0.004
    br.inputs['Brick Width'].default_value = 1.0; br.inputs['Row Height'].default_value = 1.0
    br.inputs['Color1'].default_value = (0.62, 0.63, 0.64, 1); br.inputs['Color2'].default_value = (0.58, 0.59, 0.6, 1); br.inputs['Mortar'].default_value = (0.2, 0.21, 0.22, 1)
    L.new(tc.outputs['Object'], br.inputs['Vector']); L.new(br.outputs['Color'], N["Principled BSDF"].inputs['Base Color'])
    box("Floor", (0, 6, -0.01), (12, 30, 0.02), floor)
    box("Ceiling", (0, 6, 3.6), (12, 30, 0.04), pbr("Ceil", (0.75, 0.76, 0.77), 0.8))
    wall = pbr("Wall", (0.55, 0.56, 0.58), 0.8)
    box("WallEnd", (0, 21, 1.8), (12, 0.1, 3.6), wall); box("WallBack", (0, -4, 1.8), (12, 0.1, 3.6), wall)
    for x in (-5.5, 5.5):
        box("WallSide", (x, 6, 1.8), (0.1, 30, 3.6), wall)
    # light strips down the aisle (cool) + soft area lights under them
    for y in np.arange(-2, 20, 2.4):
        box("LightStrip", (0, y, 3.56), (0.18, 1.8, 0.03), emissive("Strip", (0.92, 0.96, 1.0), 6.0))
        l = area_light((0, y, 3.5), (0, 0, 0), 1.6, 70, (0.92, 0.96, 1.0)); l.visible_camera = False
    # racks
    frame_m = pbr("RackFrame", (0.03, 0.03, 0.035), 0.4, 0.6)
    door_m = perforated("RackDoor", (0.06, 0.065, 0.07))
    face_m = pbr("ServerFace", (0.16, 0.17, 0.18), 0.35, 0.8)
    handle_m = pbr("Handle", (0.55, 0.56, 0.58), 0.25, 1.0)
    led_g = led_material("LedGreen", (0.25, 1.0, 0.45), wave=True); led_b = led_material("LedBlue", (0.3, 0.6, 1.0), wave=True)
    racks = []
    # one server front + two LEDs as templates, then linked copies (fast to build, light file)
    srv_t, (la_t, lb_t) = server_unit("SrvT", frame_m, face_m, handle_m, led_g, led_b)
    for o in (srv_t, la_t, lb_t):
        o.location = (0, 0, -50)
    la_off, lb_off = Vector((0.19, -0.012, 0.028)), Vector((0.205, -0.012, 0.028))
    door_t = box("DoorT", (0, 0, -60), (0.02, RACK_W - 0.02, RACK_H - 0.1), door_m)
    body_t = box("RackBodyT", (0, 0, -70), (RACK_D, RACK_W, RACK_H), frame_m, bevel=0.005)
    for side, x in ((-1, ROWS_X[0]), (1, ROWS_X[1])):
        rz = -math.radians(90) * side           # server fronts face the centre aisle
        for k in range(N_RACKS):
            y = k * (RACK_W + 0.02)
            instance(body_t, (x + side * RACK_D / 2, y, RACK_H / 2))
            filled = 19 if variant != "half" else (19 if (k + (side > 0)) % 3 == 0 else (6 if k % 2 else 0))
            for u in range(filled):
                z = 0.18 + u * 0.1
                instance(srv_t, (x, y, z), rot=(0, 0, rz))
                for tmpl, off in ((la_t, la_off), (lb_t, lb_off)):
                    # LED offset rotated into the rack's facing
                    ox = off.x * math.cos(rz) - off.y * math.sin(rz); oy = off.x * math.sin(rz) + off.y * math.cos(rz)
                    ld = instance(tmpl, (x + ox, y + oy, z + off.z), rot=(0, 0, rz))
                    racks.append((ld, side, k))
            if k % 3 != 1 and variant != "half":
                instance(door_t, (x - side * 0.03, y, RACK_H / 2))
    c["leds"] = racks
    # overhead cable trays with bundled cables, over each row
    tray_m = pbr("Tray", (0.45, 0.46, 0.48), 0.4, 0.9)
    cable_cols = [pbr(f"Cable{k}", col, 0.5) for k, col in enumerate(((0.9, 0.75, 0.1), (0.15, 0.35, 0.8), (0.08, 0.08, 0.09)))]
    for x in ROWS_X:
        xx = x + math.copysign(0.4, x)
        box("TrayBase", (xx, 4, 2.75), (0.4, 18, 0.01), tray_m)
        for s_ in (-0.2, 0.2):
            box("TrayLip", (xx + s_, 4, 2.79), (0.01, 18, 0.08), tray_m)
        for k in range(10):
            cyl("Cable", (xx - 0.15 + k * 0.033, 4, 2.775 + (k % 2) * 0.02), 0.012, 18, cable_cols[k % 3], verts=8, rot=(math.radians(90), 0, 0))
        for y in np.arange(-1, 13, 2.0):
            cyl("Hanger", (xx, y, 3.18), 0.008, 0.8, tray_m, verts=6)
    # the open server tray at the front of the right row (shot A): eight accelerator boards with finned heatsinks
    pcb = pbr("PCB", (0.02, 0.05, 0.03), 0.35, 0.0, **{'Coat Weight': 0.6})
    alu = pbr("FinAlu", (0.8, 0.81, 0.83), 0.28, 1.0)
    gold = pbr("Gold", (1.0, 0.75, 0.35), 0.2, 1.0)
    tx, ty, tz = ROWS_X[1] - 0.35, 1.3, 1.12
    tray_objs_start = set(bpy.data.objects)
    box("TrayPan", (tx, ty, tz), (0.75, 0.48, 0.01), pbr("TrayPan", (0.6, 0.61, 0.63), 0.35, 0.9))
    for k in range(8):
        bx = tx - 0.3 + (k % 4) * 0.2; by = ty - 0.11 + (k // 4) * 0.22
        box("Board", (bx, by, tz + 0.012), (0.17, 0.19, 0.004), pcb)
        box("Contacts", (bx, by - 0.096, tz + 0.012), (0.16, 0.004, 0.003), gold)
        for f in range(22):
            box("Fin", (bx - 0.075 + f * 0.0072, by, tz + 0.045), (0.0012, 0.17, 0.06), alu)
        box("SinkBase", (bx, by, tz + 0.017), (0.16, 0.18, 0.006), alu)
    for k in range(6):
        cyl("Fan", (tx + 0.36, ty - 0.2 + k * 0.08, tz + 0.04), 0.035, 0.04, pbr("FanBlack", (0.02, 0.02, 0.02), 0.5), verts=24, rot=(0, math.radians(90), 0))
    c["tray"] = Vector((tx, ty, tz + 0.04))
    if variant in ("one", "half"):               # the open tray only exists in the busy-hall shots
        for o in set(bpy.data.objects) - tray_objs_start:
            o.hide_render = True; o.hide_viewport = True
    # wave timing: racks light up from the far end toward the camera in shot B (frame numbers within the shot)
    for ld, side, k in racks:
        if variant == "on":
            ld["wave"] = -100.0
        elif variant == "one":                 # every rack dark except one, which wakes at frame 30 (+ a ripple up the units)
            ld["wave"] = 30.0 + (ld.location.z - 0.18) * 14 if (side > 0 and k == 6) else 1e6
        else:
            ld["wave"] = 10 + (N_RACKS - 1 - k) * 6 + (3 if side > 0 else 0)
    # two technicians and a server chassis being slid into the open rack (shot 3A)
    if variant == "on":
        from human import Human, add_asset, pose_walk, _world_verts, reach, fingers_curl
        techs = []
        for k, (g, cl, hr) in enumerate(((1.0, "male_worksuit01", "short02"), (0.0, "female_casualsuit01", "ponytail01"))):
            h = Human(f"Tech{k}", gender=g, years=30 + 8 * k, muscle=0.5, weight=0.45, height=0.5, eyelashes=None)
            add_asset(h, "clothes", cl, val=0.3, rough=0.7); add_asset(h, "clothes", "shoes02", val=0.2); add_asset(h, "hair", hr, val=0.25)
            pose_walk(h, 0.0, stride=0.0, arm_swing=0.0)
            h.arm.rotation_euler = (0, 0, math.radians(-90)); h.arm.location = (ROWS_X[0] + 0.9, 2.3 + k * 0.6, 0); bpy.context.view_layer.update()   # face -X, the rack
            w = np.concatenate([_world_verts(o) for o in h.parts if o.type == 'MESH'])
            h.arm.location.z -= w[:, 2].min(); bpy.context.view_layer.update()
            techs.append(h)
        chassis = box("Chassis", (0, 0, 0), (0.75, 0.48, 0.088), face_m, bevel=0.004)
        c["techs"] = techs; c["chassis"] = chassis
    return c


def anim_install(c, t):
    """The chassis slides from the technicians' hands into the empty slot (rack k=4, unit 9, left row)."""
    from human import reach, fingers_curl
    s_ = ease(min(1.0, max(0.0, (t - 0.15) / 0.7)))
    y = 4 * (RACK_W + 0.02); slot = Vector((ROWS_X[0] - 0.35, y, 0.18 + 9 * 0.1))
    out = slot + Vector((0.75, 0, 0.0))
    p = out.lerp(slot, s_)
    ch = c["chassis"]; ch.location = p; ch.rotation_euler = (0, 0, math.radians(90))
    for k, h in enumerate(c["techs"]):
        side = -0.2 if k == 0 else 0.2
        grip = p + Vector((0.38, side, 0.0))
        for sd, dz in (("L", 0.0), ("R", 0.0)):
            reach(h, sd, grip + Vector((0.05, 0.05 if sd == "L" else -0.05, 0.02)), Vector((0.5, 0, -1)), Vector((-1, 0, -0.2)))
        fingers_curl(h, 45, thumb=20)
        h.arm.location.x = ROWS_X[0] + 1.0 + 0.55 * (1 - s_) - 0.25 * s_
        h.arm.location.y = 4 * (RACK_W + 0.02) + (-0.3 if k == 0 else 0.3)
    bpy.context.view_layer.update()


def cam_install(c, t):
    e = ease(t)
    y = 4 * (RACK_W + 0.02)
    return (Vector((1.2, y - 2.6, 1.55)).lerp(Vector((1.0, y - 2.2, 1.5)), e), Vector((ROWS_X[0] + 0.3, y + 0.2, 1.1)), 30)


def cam_wake(c, t):
    e = ease(t)
    y = 6 * (RACK_W + 0.02)
    return (Vector((-0.6, y - 5.0, 1.5)).lerp(Vector((-0.4, y - 3.8, 1.45)), e), Vector((ROWS_X[1], y, 1.1)), 32)


def cam_ripple(c, t):
    e = ease(t)
    y = 6 * (RACK_W + 0.02)
    return (Vector((0.35, y - 1.3, 1.1)).lerp(Vector((0.45, y - 1.0, 1.25)), e), Vector((ROWS_X[1], y + 0.05, 1.15)), 45)


def cam_tray(c, t):
    e = ease(t)
    p = c["tray"]
    loc = p + Vector((-0.55, -0.45 + 0.5 * e, 0.28 - 0.05 * e))     # slide along the boards
    return (loc, p + Vector((0.05, -0.05 + 0.45 * e, -0.02)), 50)


def cam_aisle(c, t):
    e = ease(t)
    loc = Vector((0.15, 7.5, 1.4)).lerp(Vector((0.0, -2.5, 1.65)), e)        # pull back down the aisle
    return (loc, Vector((0.0, 16.0, 1.25)), 28)


MOVES = {
    "half_empty": dict(kind="anim", dof=4.0, far=30.0, cam=lambda c, t: (Vector((0.1, -1.5 + 1.5 * ease(t), 1.5)), Vector((0.0, 12.0, 1.2)), 28),
                       focus=lambda c, t: Vector((0.0, 6.0, 1.2))),
    "install": dict(kind="anim", dof=4.0, far=20.0, cam=cam_install, focus=lambda c, t: c["chassis"].location, anim=anim_install),
    "wake": dict(kind="anim", dof=4.0, far=20.0, cam=cam_wake, focus=lambda c, t: Vector((ROWS_X[1], 6 * (RACK_W + 0.02), 1.1))),
    "ripple": dict(kind="anim", dof=2.8, far=10.0, cam=cam_ripple, focus=lambda c, t: Vector((ROWS_X[1], 6 * (RACK_W + 0.02), 1.15))),
    "tray": dict(kind="anim", dof=5.6, far=4.0, cam=cam_tray, focus=lambda c, t: c["tray"] + Vector((0.05, -0.05 + 0.45 * ease(t), 0.0))),
    "aisle": dict(kind="anim", dof=4.0, far=30.0, cam=cam_aisle, focus=lambda c, t: Vector((0.0, 9.0, 1.3))),
}
