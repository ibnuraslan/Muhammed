"""Container terminal at dusk (illustration for the Indonesia shipments): container stacks, gantry cranes, quay, water."""
import math
import numpy as np
import bpy
from mathutils import Vector
from kit import *

EXPOSURE = -1.6
L20, W8, H8 = 12.19, 2.44, 2.59     # 40 ft container


def container_material(name, color):
    m = bpy.data.materials.new(name); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; p = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord"); oi = N.new("ShaderNodeObjectInfo")
    # corrugation along the length
    sep = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs['Object'], sep.inputs[0])
    mul = N.new("ShaderNodeMath"); mul.operation = 'MULTIPLY'; mul.inputs[1].default_value = 2 * math.pi / 0.28; L.new(sep.outputs['X'], mul.inputs[0])
    sn = N.new("ShaderNodeMath"); sn.operation = 'SINE'; L.new(mul.outputs[0], sn.inputs[0])
    bp = N.new("ShaderNodeBump"); bp.inputs['Strength'].default_value = 0.5; bp.inputs['Distance'].default_value = 0.03
    L.new(sn.outputs[0], bp.inputs['Height']); L.new(bp.outputs['Normal'], p.inputs['Normal'])
    # per-container colour variation + rust/dirt
    hs = N.new("ShaderNodeHueSaturation"); hs.inputs['Color'].default_value = (*color, 1)
    hv = N.new("ShaderNodeMath"); hv.operation = 'MULTIPLY_ADD'; hv.inputs[1].default_value = 0.12; hv.inputs[2].default_value = 0.44
    L.new(oi.outputs['Random'], hv.inputs[0]); L.new(hv.outputs[0], hs.inputs['Hue'])
    vv = N.new("ShaderNodeMath"); vv.operation = 'MULTIPLY_ADD'; vv.inputs[1].default_value = 0.6; vv.inputs[2].default_value = 0.7
    L.new(oi.outputs['Random'], vv.inputs[0]); L.new(vv.outputs[0], hs.inputs['Value'])
    n = N.new("ShaderNodeTexNoise"); n.inputs['Scale'].default_value = 1.5; n.inputs['Detail'].default_value = 8; L.new(tc.outputs['Object'], n.inputs['Vector'])
    dirt = N.new("ShaderNodeMix"); dirt.data_type = 'RGBA'; dirt.blend_type = 'MULTIPLY'; dirt.inputs['Factor'].default_value = 0.6
    L.new(hs.outputs['Color'], dirt.inputs[6]); L.new(n.outputs['Color'], dirt.inputs[7]); L.new(dirt.outputs[2], p.inputs['Base Color'])
    p.inputs['Roughness'].default_value = 0.55; p.inputs['Metallic'].default_value = 0.35
    return m


def crane(x, y, mat, h=52, boom=70):
    parts = []
    for dx in (-8, 8):
        for dy in (-11, 11):
            parts.append(box("Leg", (x + dx, y + dy, h / 2), (1.4, 1.4, h), mat))
    parts.append(box("Beam", (x, y, h), (18, 24, 2.5), mat))
    parts.append(box("Boom", (x, y - boom / 2 + 10, h + 6), (2.2, boom + 30, 2.2), mat))
    parts.append(box("Mast", (x, y + 4, h + 18), (2.0, 2.0, 24), mat))
    for k in range(6):
        parts.append(box("Brace", (x + (k % 2 * 2 - 1) * 8, y, h * (0.2 + 0.12 * k)), (0.6, 22, 0.6), mat, rot=(math.radians(25 * (1 if k % 2 else -1)), 0, 0)))
    return join(parts, "Crane")


VARIANT_FOR = {"ship_lift": None, "tropical_dock": "tropical", "scan_gate": None, "xray_gate": "xray"}
DUR = {"xray_gate": 9.5, "ship_lift": 5.0, "tropical_dock": 5.0, "scan_gate": 5.0}     # estimates until the chapter 1 voiceover arrives


def container_ship(x0, y0, protos, rng, length=220, beam=32):
    """Hull, deck stacks of containers, bridge block at the stern. Built around (x0, y0), bow toward +X."""
    hull_m = pbr("Hull", (0.015, 0.022, 0.04), 0.7, 0.0)
    red = pbr("Antifoul", (0.35, 0.05, 0.04), 0.6)
    white = pbr("ShipWhite", (0.75, 0.75, 0.73), 0.5)
    parts = [box("Hull", (0, 0, 4), (length, beam, 14), hull_m, bevel=1.5),
             box("Boot", (0, 0, -3.2), (length - 2, beam - 0.5, 1.4), red, bevel=0.5)]
    bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=beam * 0.72, depth=34, location=(length / 2 + 14, 0, 4), rotation=(0, math.radians(90), 0))
    bow = bpy.context.active_object; bow.scale = (0.42, 1.0, 1.0); bow.rotation_euler.x = math.radians(45); bow.data.materials.append(hull_m); parts.append(bow)
    parts += [box("Bridge", (-length / 2 + 18, 0, 11 + 9), (14, beam - 4, 18), white, bevel=0.3),
              box("BridgeWing", (-length / 2 + 18, 0, 11 + 18.5), (8, beam + 4, 1.2), white),
              box("Funnel", (-length / 2 + 8, 0, 11 + 16), (6, 6, 14), pbr("Funnel", (0.6, 0.12, 0.08), 0.5))]
    ship = join(parts, "Ship"); ship.location = (x0, y0, 0)
    stacks = []
    for bay in range(14):
        for row in range(11):
            hgt = int(rng.integers(3, 7))
            for lvl in range(hgt):
                o = instance(protos[int(rng.integers(0, len(protos)))], (x0 - length / 2 + 40 + bay * (L20 + 0.6), y0 - beam / 2 + 2.5 + row * (W8 + 0.12), 11 + H8 / 2 + lvl * H8))
                stacks.append(o)
    return ship, stacks


def build(variant=None):
    tropical = variant == "tropical"
    if tropical:
        bpy.context.scene.view_settings.exposure = -2.0
        world_sky(sun_elev_deg=40, sun_rot_deg=200, strength=0.3, tint=(1.0, 0.98, 0.95), aerosol=1.2)
        sun(40, 200, energy=2.0, color=(1.0, 0.95, 0.88), angle_deg=1.0)
    else:
        world_sky(sun_elev_deg=2.5, sun_rot_deg=70, strength=0.5, tint=(1.0, 0.85, 0.75), aerosol=3.0)
        sun(2.5, 160, energy=2.5, color=(1.0, 0.55, 0.32), angle_deg=1.5)
    r = np.random.default_rng(21)
    colors = [(0.45, 0.07, 0.05), (0.05, 0.16, 0.32), (0.08, 0.22, 0.12), (0.55, 0.35, 0.08), (0.35, 0.36, 0.38), (0.6, 0.6, 0.58)]
    mats = [container_material(f"Cont{k}", c) for k, c in enumerate(colors)]
    protos = [box(f"ContP{k}", (0, 0, -50), (L20, W8, H8), m, bevel=0.06) for k, m in enumerate(mats)]
    yard = []
    for row in range(16):
        for bay in range(9):
            x0 = -60 + bay * (L20 + 1.8); y0 = 20 + row * (W8 * 6 + 6)
            for lane in range(6):
                height = int(r.integers(1, 6)) if r.random() > 0.08 else 0
                for lvl in range(height):
                    yard.append(instance(protos[int(r.integers(0, len(protos)))], (x0, y0 + lane * (W8 + 0.15), H8 / 2 + lvl * H8)))
    steel = pbr("CraneSteel", (0.05, 0.065, 0.085), 0.75, 0.0)   # matte painted steel
    for k in range(4):
        crane(-40 + k * 38, -6, steel)
    box("Quay", (0, 190, -1), (900, 420, 2), pbr("Concrete", (0.12, 0.115, 0.11), 0.85))   # quay edge at y = -20
    water = box("Sea", (0, -300, -2.5), (3000, 600, 1), pbr("Sea", (0.01, 0.018, 0.025), 0.08))
    nt = water.data.materials[0].node_tree; N = nt.nodes; L = nt.links; tc = N.new("ShaderNodeTexCoord")
    n = N.new("ShaderNodeTexNoise"); n.inputs['Scale'].default_value = 0.08; n.inputs['Detail'].default_value = 10; L.new(tc.outputs['Object'], n.inputs['Vector'])
    b = N.new("ShaderNodeBump"); b.inputs['Strength'].default_value = 0.3; L.new(n.outputs['Fac'], b.inputs['Height']); L.new(b.outputs['Normal'], N["Principled BSDF"].inputs['Normal'])
    # quay lights coming on
    lamp = emissive("Sodium", (1.0, 0.62, 0.3), 60)
    for k in range(14):
        box("Pole", (-80 + k * 14, 8, 15), (0.4, 0.4, 30), steel)
        box("Lamp", (-80 + k * 14, 8, 30.2), (1.6, 1.0, 0.4), lamp)
    if not tropical:
      haze((0, 160, 40), (900, 400, 80), density=0.00025, color=(1.0, 0.85, 0.75) if not tropical else (0.85, 0.9, 1.0), anis=0.5)
    ctx = dict(stack=Vector((-4, 40, 6)))
    # the moored ship along the quay, and one crane's spreader lifting a container off it
    ship, stacks = container_ship(-10.0, -40.0, protos, r)
    ctx.update(ship=ship, stacks=stacks, ship_x0=ship.location.x)
    cable = pbr("Cable", (0.03, 0.03, 0.03), 0.5)
    spreader = box("Spreader", (0, 0, 0), (L20 + 0.4, W8 + 0.3, 0.8), pbr("Spreader", (0.6, 0.45, 0.05), 0.5, 0.3))
    lifted = instance(protos[0], (0, 0, 0)); lifted.name = "Lifted"
    cables = [cyl("HoistCable", (0, 0, 0), 0.05, 1.0, cable, verts=6) for _ in range(4)]
    ctx.update(spreader=spreader, lifted=lifted, cables=cables, crane_x=-2.0)
    # the scanner portal on the gate road (y = 150) and a truck with a container that drives through it
    if variant == "xray":
        # CH5 9A: a container X-ray portal: open steel gantry (lattice posts + cross-beam), a ribbed detector arm,
        # an equipment hut, amber warning beacons that flash (frame drivers). No glowing slab.
        steel = pbr("GantrySteel", (0.55, 0.56, 0.58), 0.35, 0.85)
        yellow = pbr("GantryYellow", (0.72, 0.52, 0.08), 0.45, 0.2)
        for sx in (-3.4, 3.4):
            for dy in (-0.7, 0.7):
                box("PostLeg", (-120 + sx, 150 + dy, 3.4), (0.28, 0.28, 6.8), yellow, bevel=0.02)
            for k in range(6):                                           # lattice bracing between the leg pairs
                box("Brace", (-120 + sx, 150, 0.6 + k * 1.1), (0.12, 1.4, 0.12), steel, rot=(math.radians(35 if k % 2 else -35), 0, 0))
            box("DetectorArm", (-120 + sx * 0.82, 150, 3.2), (0.35, 0.5, 5.2), pbr("Detector", (0.18, 0.19, 0.2), 0.45, 0.4), bevel=0.04)
        box("CrossBeam", (-120, 150, 7.0), (7.6, 1.8, 0.6), yellow, bevel=0.03)
        box("SourceHead", (-120, 150, 6.45), (1.2, 1.2, 0.6), pbr("SourceHead", (0.25, 0.26, 0.27), 0.4, 0.6), bevel=0.05)
        box("Hut", (-128.5, 146, 1.4), (3.0, 2.5, 2.8), pbr("Hut", (0.6, 0.6, 0.58), 0.6), bevel=0.05)
        box("HutWin", (-127.0, 146, 1.7), (0.02, 1.4, 0.8), emissive("HutWin", (1.0, 0.85, 0.6), 1.5))
        for k, (sx, ph_) in enumerate(((-3.4, 0), (3.4, 12))):
            bm = bpy.data.materials.new(f"Beacon{k}"); bm.use_nodes = True
            Nn = bm.node_tree.nodes; Ll = bm.node_tree.links; Nn.clear()
            o_ = Nn.new("ShaderNodeOutputMaterial"); em = Nn.new("ShaderNodeEmission"); em.inputs['Color'].default_value = (1.0, 0.55, 0.08, 1)
            v = Nn.new("ShaderNodeValue"); dd = v.outputs[0].driver_add("default_value").driver; dd.type = 'SCRIPTED'
            dd.expression = f"30 * (1 if ((frame + {ph_}) % 24) < 10 else 0.03)"
            Ll.new(v.outputs[0], em.inputs['Strength']); Ll.new(em.outputs[0], o_.inputs['Surface'])
            cyl("Beacon", (-120 + sx, 150, 7.45), 0.16, 0.3, bm, verts=16)
            bl = bpy.data.lights.new(f"BeaconL{k}", 'POINT'); bl.color = (1.0, 0.55, 0.1); bl.shadow_soft_size = 0.1
            dl = bl.driver_add("energy").driver; dl.type = 'SCRIPTED'; dl.expression = f"900 * (1 if ((frame + {ph_}) % 24) < 10 else 0.03)"
            bo = bpy.data.objects.new(f"BeaconL{k}", bl); bpy.context.collection.objects.link(bo); bo.location = (-120 + sx, 149.4, 7.6)
        for sx in (-4.2, 4.2):                                           # road barriers + painted stop line
            box("Barrier", (-120 + sx, 140, 0.5), (0.4, 1.6, 1.0), pbr("Barrier", (0.8, 0.8, 0.78), 0.5), bevel=0.05)
        box("StopLine", (-120, 143, 0.03), (6.5, 0.3, 0.02), pbr("Paint", (0.85, 0.85, 0.8), 0.6))
        area_light((-112, 140, 9), (0, 0, 0), 6, 1200, (1.0, 0.92, 0.82))
    else:
        gate_m = pbr("Gate", (0.75, 0.75, 0.73), 0.4, 0.2)
        for sx in (-3.2, 3.2):
            box("GatePost", (-120 + sx, 150, 3.0), (0.8, 2.0, 6.0), gate_m, bevel=0.05)
        box("GateTop", (-120, 150, 6.3), (7.2, 2.0, 0.8), gate_m, bevel=0.05)
        sm = bpy.data.materials.new("ScanBeam"); sm.use_nodes = True
        Nn = sm.node_tree.nodes; Ll = sm.node_tree.links; Nn.clear()
        o_ = Nn.new("ShaderNodeOutputMaterial"); em = Nn.new("ShaderNodeEmission"); em.inputs['Color'].default_value = (1.0, 0.1, 0.06, 1)
        v = Nn.new("ShaderNodeValue"); dd = v.outputs[0].driver_add("default_value").driver; dd.type = 'SCRIPTED'; dd.expression = "0.12 + 0.06 * sin(frame * 0.8)"
        tr = Nn.new("ShaderNodeBsdfTransparent"); mxs = Nn.new("ShaderNodeMixShader"); em.inputs['Strength'].default_value = 6.0
        Ll.new(v.outputs[0], mxs.inputs[0]); Ll.new(tr.outputs[0], mxs.inputs[1]); Ll.new(em.outputs[0], mxs.inputs[2]); Ll.new(mxs.outputs[0], o_.inputs['Surface'])
        for sx in (-2.75, 2.75):                       # bright red scan bars on the inner faces of the posts
            box("ScanBar", (-120 + sx, 150, 3.0), (0.05, 0.08, 5.6), emissive("ScanBar", (1.0, 0.12, 0.06), 25))
        box("Beam", (-120, 150, 3.0), (6.0, 0.03, 5.8), sm).visible_shadow = False
    box("GateRoad", (-120, 150, -0.48), (14, 300, 1), pbr("Asphalt", (0.05, 0.05, 0.055), 0.6))
    cab_m = pbr("Cab", (0.08, 0.22, 0.4), 0.35, 0.3)
    truck = join([box("Cab", (0, 5.6, 1.6), (2.5, 2.2, 2.6), cab_m, bevel=0.15),
                  box("Chassis", (0, -1.0, 0.8), (2.4, 12.0, 0.5), pbr("Chassis", (0.03, 0.03, 0.03), 0.6))], "Truck")
    tc_ = instance(protos[2], (0, -1.0, 1.05 + H8 / 2)); tc_.rotation_euler = (0, 0, math.radians(90)); tc_.parent = truck
    truck.location = (-120, 120, 0); ctx["truck"] = truck
    if tropical:                                   # palms along the quay edge (scanned tree), ship arriving
        import ph
        root, ms = ph.model("island_tree_02", loc=(0, 0, -300))
        for k in range(10):
            instance(ms[0], (-160 + k * 34 + r.uniform(-4, 4), -14, 0.0), rot=(0, 0, r.uniform(0, 6.28)), scale=(2.6, 2.6, 2.6))
    return ctx


def anim_lift(c, t):
    """Spreader comes down onto a deck container, locks, and lifts it toward the boom (the cables shorten)."""
    x = c["crane_x"]; y_deck = -40.0; top = 58.0
    z_deck = 11 + 5 * H8 + 0.4
    if t < 0.3:
        z = top - (top - z_deck - 2) * ease(t / 0.3); carry = False
    else:
        z = z_deck + (top - 8 - z_deck) * ease(min(1.0, (t - 0.35) / 0.65)) if t > 0.35 else z_deck; carry = t > 0.33
    sp = c["spreader"]; sp.location = (x, y_deck, z + 0.6)
    c["lifted"].location = (x, y_deck, z - H8 / 2 if carry else -60)
    for k, cb in enumerate(c["cables"]):
        dx = (k % 2 - 0.5) * (L20 - 1); dy = (k // 2 - 0.5) * 1.6
        length = max(0.5, top - (z + 1.0)); cb.location = (x + dx, y_deck + dy, z + 1.0 + length / 2); cb.scale = (1, 1, length)


def anim_dock(c, t):
    e = 1 - (1 - t) ** 2
    dx = 70 * (1 - e)                               # the ship glides the last 70 m into its berth
    c["ship"].location.x = c["ship_x0"] + dx
    for o in c["stacks"]:
        if "x0" not in o:
            o["x0"] = o.location.x
        o.location.x = o["x0"] + dx
    anim_lift(c, 0.0)


def anim_scan(c, t):
    c["truck"].location = (-120, 128 + 9.0 * t * DUR["scan_gate"] / 2.0, 0)
    anim_lift(c, 0.0)


def _xray(c, t):
    c["truck"].location = (-120, 128 + 26.0 * t, 0)          # ~2.7 m/s: the container clears the portal by the end
    anim_lift(c, 0.0)


def cam_lift(c, t):
    e = ease(t)
    return (Vector((-75, -135, 6)).lerp(Vector((-68, -128, 7)), e), Vector((-2, -40, 28 + 4 * e)), 45)       # from the water: ship, crane, the lift


def cam_dock(c, t):
    e = ease(t)
    return (Vector((70, -175, 12)).lerp(Vector((62, -168, 13)), e), Vector((-10, -40, 14)), 35)                # across the water


MOVES = {
    "scan_gate": dict(kind="anim", far=1200.0, anim=anim_scan,
                      cam=lambda c, t: (Vector((-104, 132, 2.2)).lerp(Vector((-105, 135, 2.4)), ease(t)), Vector((-120, 150, 3.0)), 35)),
    # CH5 9A: the truck rolls its container slowly through the X-ray portal, amber beacons flashing
    "xray_gate": dict(kind="anim", far=1200.0, anim=lambda c, t: _xray(c, t),
                      cam=lambda c, t: (Vector((-106, 129, 2.4)).lerp(Vector((-107.5, 132, 2.6)), ease(t)), Vector((-120, 150, 3.4)), 32)),
    "ship_lift": dict(kind="anim", far=1200.0, cam=cam_lift, anim=anim_lift),
    "tropical_dock": dict(kind="anim", far=1200.0, cam=cam_dock, anim=anim_dock),
    "crane_rise": dict(kind="anim", far=1200.0, cam=lambda c, t: ((95, -175, 5 + 6 * t), (-5, 10, 24), 32)),
    "container_push": dict(kind="plate", dof=4.0, far=600.0, cam=lambda c, t: ((14, 4, 3.2), (-10, 28, 5), 40), focus=lambda c, t: (-2, 23, 4)),
}
