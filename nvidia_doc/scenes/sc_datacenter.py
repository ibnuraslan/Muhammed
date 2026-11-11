"""AI data-center aisle: two rows of racks, blinking status LEDs, fibre trays with travelling light pulses,
raised perforated floor, haze. Variant 'build' = a half-built hall (the 2025 data-center pitch)."""
import math
import numpy as np
import bpy
from mathutils import Vector
from kit import *

VARIANT_FOR = {}
BOUNCES = 6
AISLE_L = 22.0
RACK_W, RACK_D, RACK_H = 0.6, 1.2, 2.25
ROW_X = 1.1          # aisle half-width to rack fronts


def faceplate(name):
    """Server fronts: 1U seams, dark bezels, handle highlights."""
    m = bpy.data.materials.new(name); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; p = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord")
    sep = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs['Object'], sep.inputs[0])
    cmb = N.new("ShaderNodeCombineXYZ"); L.new(sep.outputs['Y'], cmb.inputs[0]); L.new(sep.outputs['Z'], cmb.inputs[1])
    br = N.new("ShaderNodeTexBrick"); br.inputs['Scale'].default_value = 1.0
    br.inputs['Brick Width'].default_value = RACK_W * 0.98; br.inputs['Row Height'].default_value = 0.0889   # 2U servers
    br.inputs['Mortar Size'].default_value = 0.003; br.offset = 0.0
    br.inputs['Color1'].default_value = (0.07, 0.075, 0.08, 1); br.inputs['Color2'].default_value = (0.10, 0.105, 0.11, 1)
    br.inputs['Mortar'].default_value = (0.004, 0.004, 0.005, 1)
    L.new(cmb.outputs[0], br.inputs['Vector']); L.new(br.outputs['Color'], p.inputs['Base Color'])
    n = N.new("ShaderNodeTexNoise"); n.inputs['Scale'].default_value = 300; L.new(tc.outputs['Object'], n.inputs['Vector'])
    rr = N.new("ShaderNodeMapRange"); rr.inputs['To Min'].default_value = 0.25; rr.inputs['To Max'].default_value = 0.45
    L.new(n.outputs['Fac'], rr.inputs['Value']); L.new(rr.outputs[0], p.inputs['Roughness'])
    p.inputs['Metallic'].default_value = 0.8
    bp = N.new("ShaderNodeBump"); bp.inputs['Strength'].default_value = 0.4; L.new(br.outputs['Fac'], bp.inputs['Height']); L.new(bp.outputs['Normal'], p.inputs['Normal'])
    return m


def fiber_pulses(name, color=(0.25, 0.85, 1.0), strength=20.0):
    """Travelling light pulses along +Y (set node 'Offset' input each frame via m['offset_node'])."""
    m = bpy.data.materials.new(name); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; p = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord"); sep = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs['Object'], sep.inputs[0])
    off = N.new("ShaderNodeMath"); off.operation = 'ADD'; L.new(sep.outputs['Y'], off.inputs[0]); off.inputs[1].default_value = 0.0
    sc = N.new("ShaderNodeMath"); sc.operation = 'MULTIPLY'; sc.inputs[1].default_value = 0.35; L.new(off.outputs[0], sc.inputs[0])
    fr = N.new("ShaderNodeMath"); fr.operation = 'FRACT'; L.new(sc.outputs[0], fr.inputs[0])
    pw = N.new("ShaderNodeMath"); pw.operation = 'POWER'; pw.inputs[1].default_value = 18.0; L.new(fr.outputs[0], pw.inputs[0])
    st = N.new("ShaderNodeMath"); st.operation = 'MULTIPLY_ADD'; st.inputs[1].default_value = strength; st.inputs[2].default_value = 0.15
    L.new(pw.outputs[0], st.inputs[0])
    p.inputs['Base Color'].default_value = (0.02, 0.05, 0.06, 1)
    p.inputs['Emission Color'].default_value = (*color, 1); L.new(st.outputs[0], p.inputs['Emission Strength'])
    m["offset_node"] = off.name
    return m


def build(variant=None):
    s = bpy.context.scene
    world_flat((0.003, 0.004, 0.006), 1.0)
    build_hall = variant == "build"
    floor = box("Floor", (0, AISLE_L / 2 - 2, -0.025), (8, AISLE_L + 8, 0.05), None)
    fm = brushed_metal("FloorTile", (0.2, 0.21, 0.23), (0.25, 0.45), 0.2, axis=(1, 1, 1), bump=0.05)
    nt = fm.node_tree; N = nt.nodes; L = nt.links; tc = N.new("ShaderNodeTexCoord")
    tile = N.new("ShaderNodeTexBrick"); tile.inputs['Scale'].default_value = 1 / 0.6; tile.offset = 0.0
    tile.inputs['Brick Width'].default_value = 1.0; tile.inputs['Row Height'].default_value = 1.0; tile.inputs['Mortar Size'].default_value = 0.004
    tile.inputs['Color1'].default_value = (0.16, 0.17, 0.19, 1); tile.inputs['Color2'].default_value = (0.11, 0.12, 0.13, 1)
    L.new(tc.outputs['Object'], tile.inputs['Vector']); L.new(tile.outputs['Color'], N["Principled BSDF"].inputs['Base Color'])
    N["Principled BSDF"].inputs['Metallic'].default_value = 0.3
    floor.data.materials.append(fm)
    ceil_m = pbr("Ceiling", (0.02, 0.022, 0.025), 0.8)
    box("Ceiling", (0, AISLE_L / 2 - 2, 3.4), (8, AISLE_L + 8, 0.05), ceil_m)
    body = pbr("RackBody", (0.012, 0.012, 0.014), 0.4, 0.7)
    fp = faceplate("Faceplate")
    leds = blinking_leds("LED", (0.3, 0.9, 1.0), 18.0)
    led_proto = box("LEDp", (0, 0, -5), (0.004, 0.004, 0.004), leds)
    rack_proto = box("RackP", (0, 0, -10), (RACK_D, RACK_W, RACK_H), body, bevel=0.004)
    front_proto = box("FrontP", (0, 0, -10), (0.01, RACK_W * 0.96, RACK_H * 0.94), fp)
    frame_m = brushed_metal("Frame", (0.25, 0.26, 0.28), (0.3, 0.45), 0.4)
    r = np.random.default_rng(7)
    n_racks = int(AISLE_L / RACK_W)
    racks = []
    for side in (-1, 1):
        for k in range(n_racks):
            y = -1.0 + k * RACK_W + RACK_W / 2
            x = side * (ROW_X + RACK_D / 2)
            if build_hall and (r.random() < 0.45 or k > n_racks * 0.6):
                # empty open frame (rack under construction)
                for dx in (-1, 1):
                    for dy in (-1, 1):
                        box("Post", (x + dx * RACK_D * 0.48, y + dy * RACK_W * 0.46, RACK_H / 2), (0.03, 0.03, RACK_H), frame_m)
                continue
            racks.append(instance(rack_proto, (x, y, RACK_H / 2)))
            instance(front_proto, (side * (ROW_X + 0.005), y, RACK_H / 2))
            n_srv = int(RACK_H * 0.94 / 0.0889)
            for j in range(n_srv):
                if r.random() < 0.15:
                    continue
                z = 0.07 + j * 0.0889 + 0.044
                for q in range(int(r.integers(1, 4))):
                    yy = y - RACK_W * 0.4 + q * 0.02 + (RACK_W * 0.6 if r.random() < 0.3 else 0)
                    instance(led_proto, (side * (ROW_X - 0.002), yy, z))
    # overhead: fibre trays (with light pulses) and ladder racks
    pulses = fiber_pulses("Fiber")
    for side in (-1, 1):
        box("FiberTray", (side * 0.55, AISLE_L / 2 - 1, 2.75), (0.18, AISLE_L + 2, 0.06), pulses)
        box("Ladder", (side * (ROW_X + RACK_D / 2), AISLE_L / 2 - 1, 2.55), (0.5, AISLE_L + 2, 0.04), pbr("Ladder", (0.03, 0.03, 0.035), 0.5, 0.8))
    strip = emissive("Strip", (0.85, 0.92, 1.0), 14.0 if not build_hall else 3.0)
    for k in range(9):
        box("LightStrip", (0, -0.5 + k * 2.4, 3.36), (0.12, 1.8, 0.02), strip)
    # end of aisle: containment door, glowing
    glow = emissive("EndGlow", (0.7, 0.85, 1.0), 6.0)
    box("EndDoor", (0, AISLE_L - 0.6, 1.25), (ROW_X * 2 - 0.05, 0.02, 2.5), glow)
    box("DoorFrame", (0, AISLE_L - 0.62, 1.25), (ROW_X * 2 + 0.1, 0.04, 2.6), frame_m)
    if build_hall:
        work = bpy.data.lights.new("Work", 'SPOT'); work.energy = 900; work.color = (1.0, 0.82, 0.6); work.spot_size = math.radians(70)
        o = bpy.data.objects.new("Work", work); bpy.context.collection.objects.link(o); o.location = (0.4, 8, 3.0); point_at(o, (0, 9, 0))
        for k in range(4):
            cyl("Spool", (r.uniform(-0.6, 0.6), 4 + k * 3.1, 0.3), 0.3, 0.25, pbr("Spool", (0.25, 0.2, 0.12), 0.7), rot=(0, math.radians(90), 0))
    haze(((0, AISLE_L / 2 - 1, 1.7)), (ROW_X * 2, AISLE_L + 2, 3.4), density=0.035, color=(0.75, 0.85, 1.0), anis=0.4)
    return dict(leds=leds, pulses=pulses, end=Vector((0, AISLE_L - 0.6, 1.3)))


def _tick(c, t, seconds=6.0):
    set_led_time(c["leds"], t * seconds * 0.8)
    c["pulses"].node_tree.nodes[c["pulses"]["offset_node"]].inputs[1].default_value = -t * seconds * 2.2


MOVES = {
    "silhouette_aisle": dict(kind="plate", far=30.0, cam=lambda c, t: ((0.0, -0.8, 1.15), (0.0, 12, 1.35), 30), anim=_tick),
    "rack_lights": dict(kind="plate", dof=2.0, far=10.0,
                        cam=lambda c, t: ((0.55, 1.2, 1.25), (ROW_X, 3.2, 1.1), 50), focus=lambda c, t: (ROW_X, 2.6, 1.15), anim=_tick),
    "dolly_aisle": dict(kind="anim", far=30.0, cam=lambda c, t: ((0.15, -1.0 + 4.0 * ease(t), 1.35), (0.0, 14 + 4 * t, 1.5), 28), anim=_tick),
    "locked_rack": dict(kind="plate", dof=4.0, far=10.0,
                        cam=lambda c, t: ((-0.1, 5.0, 1.15), (ROW_X, 5.7, 1.12), 32), focus=lambda c, t: (ROW_X, 5.7, 1.12), anim=_tick),
    "slow_push": dict(kind="plate", far=30.0, cam=lambda c, t: ((0.35, -0.5, 1.6), (-0.1, 10, 1.2), 30), anim=_tick),
}
